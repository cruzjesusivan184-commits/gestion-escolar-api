"""
views/maestros.py
----------------------------------------------------------
Vistas para la gestión de maestros: CRUD completo.

Particularidad de materias_array:
    Las materias que imparte un maestro se almacenan como un array JSON
    serializado en un TextField de la BD (json.dumps al guardar, json.loads al leer).
    En MaestrosAll.get() se deserializa materias_array de string a lista Python
    antes de enviar la respuesta, para que el frontend reciba un array real y no
    un string con corchetes.

Mismos patrones que alumnos.py:
    - MaestrosAll: GET /lista-maestros/ (lista paginada para MaestrosScreen)
    - MaestrosView: GET/POST/PUT/DELETE /maestros/ (CRUD de un maestro)
    - @transaction.atomic en POST y PUT para atomicidad BD.
    - request.query_params para DELETE (id en URL), request.data para PUT (id en body).
"""
from django.db.models import *
from django.db import transaction
from gestion_escolar_api.models import Administradores, Maestros
from gestion_escolar_api.serializers import UserSerializer
from gestion_escolar_api.serializers import *
from gestion_escolar_api.models import *
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import Group
import json


class MaestrosAll(generics.CreateAPIView):
    """
    Endpoint: GET /lista-maestros/
    Método HTTP: GET
    Autenticación: Requerida (IsAuthenticated)
    Modelo BD: Maestros

    Retorna: lista JSON de maestros activos con materias_array deserializado.
    Consumido por: MaestrosScreen.obtenerMaestros() en el frontend Angular.
    """
    #Obtener todos los maestros
    # Necesita permisos de autenticación de usuario para poder acceder a la petición
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        maestros = Maestros.objects.filter(user__is_active=1).order_by("id")
        lista = MaestrosSerializer(maestros, many=True).data
        for maestro in lista:
            if isinstance(maestro, dict) and "materias_array" in maestro:
                try:
                    maestro["materias_array"] = json.loads(maestro["materias_array"])
                except Exception:
                    maestro["materias_array"] = []
        return Response(lista, 200)

class MaestrosView(generics.CreateAPIView):
    """
    Endpoint: /maestros/
    Métodos HTTP: GET (?id=X), POST (crear), PUT (actualizar), DELETE (?id=X)
    Autenticación: Requerida para GET, PUT, DELETE. POST es público.
    Modelo BD: Maestros (+ User via ForeignKey)
    """
    # Permisos por método (sobrescribe el comportamiento default)
    # Verifica que el usuario esté autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación

    #Eliminar un maestro específico por su ID
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        maestro = Maestros.objects.filter(id=request.query_params.get("id"), user__is_active=1).first()
        if not maestro:
            return Response({"message": "Maestro no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        user = maestro.user
        maestro.delete()
        user.delete()
        return Response({"message": "Maestro eliminado correctamente"}, status=status.HTTP_200_OK)
    
   #Obtener un maestro específico por su ID
    def get(self, request, *args, **kwargs):
        maestro = Maestros.objects.filter(id=request.GET.get("id"), user__is_active=1).first()
        if not maestro:
            return Response({"message": "Maestro no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        serializer = MaestrosSerializer(maestro)
        return Response(serializer.data, status=status.HTTP_200_OK)

   # Actualizar datos del maestro
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        maestro = Maestros.objects.filter(id=request.data["id"], user__is_active=1).first()
        if not maestro:
            return Response({"message": "Maestro no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        user = maestro.user
        user.first_name = request.data["first_name"]
        user.last_name = request.data["last_name"]
        user.save()
        maestro.id_trabajador = request.data["id_trabajador"]
        maestro.fecha_nacimiento = request.data["fecha_nacimiento"]
        maestro.telefono = request.data["telefono"]
        maestro.rfc = request.data["rfc"].upper()
        maestro.cubiculo = request.data["cubiculo"]
        maestro.area_investigacion = request.data["area_investigacion"]
        maestro.campus = request.data["campus"]
        maestro.sueldo_estimado = request.data["sueldo_estimado"]
        maestro.materias_array = json.dumps(request.data["materias_array"])
        maestro.save()
        return Response({"message": "Maestro actualizado correctamente"}, status=status.HTTP_200_OK)

    #Registrar nuevo usuario maestro
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)
        if user.is_valid():
            role = request.data['rol']
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            email = request.data['email']
            password = request.data['password']
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                return Response({"message":"Username "+email+", is already taken"},400)
            user = User.objects.create( username = email,
                                        email = email,
                                        first_name = first_name,
                                        last_name = last_name,
                                        is_active = 1)
            user.save()
            user.set_password(password)
            user.save()
            
            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)
            user.save()
            #Create a profile for the user
            maestro = Maestros.objects.create(user=user,
                                            id_trabajador= request.data["id_trabajador"],
                                            fecha_nacimiento= request.data["fecha_nacimiento"],
                                            telefono= request.data["telefono"],
                                            rfc= request.data["rfc"].upper(),
                                            cubiculo= request.data["cubiculo"],
                                            area_investigacion= request.data["area_investigacion"],
                                            materias_array = json.dumps(request.data["materias_array"]),
                                            campus= request.data["campus"],
                                            sueldo_estimado= request.data["sueldo_estimado"])
            maestro.save()
            return Response({"Maestro creado con ID= ": maestro.id }, 201)
        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
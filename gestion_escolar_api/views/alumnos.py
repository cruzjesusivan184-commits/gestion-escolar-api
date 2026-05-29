"""
views/alumnos.py
----------------------------------------------------------
Vistas para la gestión de alumnos: CRUD completo.

Separación de responsabilidades:
    AlumnosView: maneja operaciones sobre UN alumno específico (GET/POST/PUT/DELETE).
    AlumnosAll: maneja la operación de listar TODOS los alumnos (GET lista).

request.query_params vs request.data:
    - request.query_params.get("id"): parámetro de URL (?id=5). Usado en DELETE y GET.
    - request.data["id"]: cuerpo JSON del request. Usado en PUT.
    Esta diferencia es importante: si el profesor pregunta "¿cómo reciben el id?",
    la respuesta depende del método HTTP.

@transaction.atomic en POST:
    Crea el User y el perfil Alumnos en una sola transacción. Si falla cualquier
    paso, ambos se deshacen. Sin esto, podría crearse un User sin perfil Alumnos.
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
from django.shortcuts import get_object_or_404
import json


class AlumnosView(generics.CreateAPIView):
    """
    Endpoint: /alumnos/
    Métodos HTTP: GET (?id=X), POST (crear), PUT (actualizar), DELETE (?id=X)
    Autenticación: Requerida para GET, PUT, DELETE. POST es público.
    Modelo BD: Alumnos (+ User via ForeignKey)
    """
    # Permisos por método (sobrescribe el comportamiento default)
    # Verifica que el usuario esté autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación

    # DELETE /alumnos/?id=X — Eliminación FÍSICA del alumno y su User asociado.
    # Se elimina primero el perfil y luego el User para respetar integridad referencial.
    # request.query_params.get("id"): el id viene como parámetro en la URL, no en el body.
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        alumno = Alumnos.objects.filter(id=request.query_params.get("id"), user__is_active=1).first()
        if not alumno:
            return Response({"message": "Alumno no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        user = alumno.user
        alumno.delete()
        user.delete()
        return Response({"message": "Alumno eliminado correctamente"}, status=status.HTTP_200_OK)
  
    #Obtener un alumno específico por su ID
    def get(self, request, *args, **kwargs):
        alumno = Alumnos.objects.filter(id=request.GET.get("id"), user__is_active=1).first()
        if not alumno:
            return Response({"message": "Alumno no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        serializer = AlumnoSerializer(alumno)
        return Response(serializer.data, status=status.HTTP_200_OK)
  
    # Actualizar datos del alumno
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        alumno = Alumnos.objects.filter(id=request.data["id"], user__is_active=1).first()
        if not alumno:
            return Response({"message": "Alumno no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        user = alumno.user
        user.first_name = request.data["first_name"]
        user.last_name = request.data["last_name"]
        user.save()
        alumno.matricula = request.data["matricula"]
        alumno.curp = request.data["curp"].upper()
        alumno.rfc = request.data["rfc"].upper()
        alumno.fecha_nacimiento = request.data["fecha_nacimiento"]
        alumno.edad = request.data["edad"]
        alumno.telefono = request.data["telefono"]
        alumno.ocupacion = request.data["ocupacion"]
        alumno.direccion = request.data["direccion"]
        alumno.sexo = request.data["sexo"]
        alumno.save()
        return Response({"message": "Alumno actualizado correctamente"}, status=status.HTTP_200_OK)

    #Registrar nuevo usuario
    @transaction.atomic
    def post(self, request, *args, **kwargs):

        user = UserSerializer(data=request.data)
        if user.is_valid():
            #Grab user data
            role = request.data['rol']
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            email = request.data['email']
            password = request.data['password']
            #Valida si existe el usuario o bien el email registrado
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
            alumno = Alumnos.objects.create(user=user,
                                            matricula= request.data["matricula"],
                                            curp= request.data["curp"].upper(),
                                            rfc= request.data["rfc"].upper(),
                                            fecha_nacimiento= request.data["fecha_nacimiento"],
                                            edad= request.data["edad"],
                                            telefono= request.data["telefono"],
                                            ocupacion= request.data["ocupacion"],
                                            direccion= request.data["direccion"],
                                            sexo= request.data["sexo"])
            alumno.save()

            return Response({"Alumno creado con ID= ": alumno.id }, 201)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)

class AlumnosAll(generics.CreateAPIView):
    """
    Endpoint: GET /lista-alumnos/
    Método HTTP: GET
    Autenticación: Requerida (IsAuthenticated)
    Modelo BD: Alumnos

    Retorna: lista JSON de todos los alumnos activos, ordenados por id.
    Consumido por: AlumnosScreen.obtenerAlumnos() en el frontend Angular.
    """
    # permission_classes = (permissions.IsAuthenticated,):
    # Solo usuarios autenticados (con token válido) pueden ver la lista de alumnos.
    # Si no hay token o es inválido, DRF retorna 401 Unauthorized automáticamente.
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        alumnos = Alumnos.objects.filter(user__is_active=1).order_by("id")
        lista = AlumnoSerializer(alumnos, many=True).data
        return Response(lista, 200)

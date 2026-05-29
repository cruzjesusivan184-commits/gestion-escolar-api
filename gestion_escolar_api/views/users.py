"""
views/users.py
----------------------------------------------------------
Vistas para la gestión de administradores y totales de usuarios.

Conceptos clave:
    request.query_params vs request.data:
        - request.query_params: parámetros de la URL (?id=5). Se usa en GET y DELETE.
        - request.data: cuerpo del request (JSON). Se usa en POST, PUT, PATCH.

    filter() vs get() en el ORM de Django:
        - filter(): retorna un QuerySet (lista) aunque haya 0 o 1 resultados.
          Nunca lanza excepción si no encuentra nada.
        - get(): retorna un objeto único. Lanza DoesNotExist si no encuentra nada
          y MultipleObjectsReturned si hay más de uno.
        En estas vistas se usa filter(...).first() para obtener el primer resultado
        o None si no existe, evitando excepciones inesperadas.

    @transaction.atomic:
        Garantiza que las operaciones de BD (crear User + crear perfil) sean
        atómicas: si falla alguna, se deshacen todas. Esencial para evitar
        usuarios "fantasma" (User sin perfil o perfil sin User).
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


class AdminAll(generics.CreateAPIView):
    """
    Endpoint: GET /lista-admins/
    Método HTTP: GET
    Autenticación: Requerida (IsAuthenticated)
    Modelo BD: Administradores

    Retorna: lista JSON de todos los administradores con is_active=True,
             ordenados por id, usando AdminSerializer.

    user__is_active=1: filtro por campo relacionado (double underscore en Django ORM).
    Equivale a un JOIN con auth_user WHERE is_active=1. Solo retorna admins activos
    (los desactivados con PATCH no aparecen en esta lista).
    """
    #Esta función es esencial para todo donde se requiera autorización de inicio de sesión (token)
    permission_classes = (permissions.IsAuthenticated,)
    # Invocamos la petición GET para obtener todos los administradores
    def get(self, request, *args, **kwargs):
        admin = Administradores.objects.filter(user__is_active = 1).order_by("id")
        lista = AdminSerializer(admin, many=True).data
        return Response(lista, 200)
    
class AdminView(generics.CreateAPIView):
    """
    Endpoint: /admin/
    Métodos HTTP: GET (obtener por id), POST (crear), PUT (actualizar), DELETE (eliminar físico), PATCH (desactivar)

    get_permissions():
        Permite el registro (POST) sin autenticación para que nuevos usuarios
        puedan registrarse desde la pantalla pública. Para el resto de operaciones
        (GET, PUT, DELETE, PATCH) requiere token válido.
    """
    # Permisos por método (sobrescribe el comportamiento default)
    # Verifica que el usuario esté autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación
    
    # GET /admin/?id=X — Obtiene los datos de un administrador por su id.
    # Usa request.GET.get("id") porque el id viaja como query param en la URL.
    # AdminSerializer serializa el objeto a JSON incluyendo el User anidado.
    def get(self, request, *args, **kwargs):
        admin = Administradores.objects.filter(id=request.GET.get("id"), user__is_active=1).first()
        if not admin:
            return Response({"message": "Administrador no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminSerializer(admin)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # POST /admin/ — Registra un nuevo administrador.
    # @transaction.atomic garantiza que si falla la creación del perfil,
    # el User también se deshace (no quedan usuarios "fantasma").
    # user.set_password() cifra la contraseña antes de guardarla en BD.
    # Group.objects.get_or_create(name=role) asigna el rol al usuario en la tabla auth_group.
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        
        # Serializamos los datos del administrador para volverlo de nuevo JSON
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
                return Response({"message":"Nombre de usuario "+email+", ya existe"},400)

            user = User.objects.create( username = email,
                                        email = email,
                                        first_name = first_name,
                                        last_name = last_name,
                                        is_active = 1)


            user.save()
            #Cifrar la contraseña
            user.set_password(password)
            user.save()

            #Asignar el rol al usuario a la tabla de grupos
            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)
            user.save()

            #Almacenar los datos adicionales del administrador en la tabla de administradores
            admin = Administradores.objects.create(
                user=user,
                clave_admin= request.data.get("clave_admin"),
                telefono= request.data.get("telefono"),
                rfc= request.data.get("rfc", "").upper(),
                edad= request.data.get("edad"),
                ocupacion= request.data.get("ocupacion"),
                categoria= request.data.get("categoria"),
                grado_academico= request.data.get("grado_academico")
            )
            
            admin.save()

            return Response({"Administrador creado ID": admin.id }, 201)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # PUT /admin/ — Actualiza los datos de un administrador existente.
    # request.data contiene el cuerpo JSON del request (campos a actualizar).
    # Se actualiza el User (first_name, last_name) y el perfil Administradores por separado.
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        admin = Administradores.objects.filter(id=request.data["id"], user__is_active=1).first()
        if not admin:
            return Response({"message": "Administrador no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        user = admin.user
        # Actualizar campos del usuario
        user.first_name = request.data["first_name"]
        user.last_name = request.data["last_name"]
        #Guardamos los cambios del usuario no es necesario actualizar la contraseña
        user.save()

        # Actualizar campos del administrador
        admin.clave_admin = request.data.get("clave_admin")
        admin.telefono = request.data.get("telefono")
        admin.rfc = request.data.get("rfc", "").upper()
        admin.edad = request.data.get("edad")
        admin.ocupacion = request.data.get("ocupacion")
        admin.categoria = request.data.get("categoria")
        admin.grado_academico = request.data.get("grado_academico")
        
        admin.save()

        return Response({"message": "Administrador actualizado correctamente"}, status=status.HTTP_200_OK)
    
    # DELETE /admin/?id=X — Eliminación FÍSICA: borra el User y en cascada el perfil.
    # Usar con cuidado; en la app el frontend usa PATCH (eliminación lógica) en su lugar.
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        admin = Administradores.objects.filter(id=request.GET.get("id"), user__is_active=1).first()
        if not admin:
            return Response({"message": "Administrador no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        try:
            admin.user.delete()
            return Response({"details":"Administrador eliminado"},200)
        except Exception as e:
            return Response({"details":"Error al eliminar administrador"},400)
        
    # PATCH /admin/ — Eliminación LÓGICA: pone is_active=False en el User.
    # El administrador ya no puede iniciar sesión y no aparece en las listas,
    # pero su registro permanece en la BD (útil para auditorías).
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        admin = Administradores.objects.filter(id=request.data["id"], user__is_active=1).first()
        if not admin:
            return Response({"message": "Administrador no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        try:
            admin.user.is_active = False
            admin.user.save()
            return Response({"details":"Administrador desactivado"},200)
        except Exception as e:
            return Response({"details":"Error al desactivar administrador"},400)

class TotalUsuarios(generics.CreateAPIView):
    """
    Endpoint: GET /total-usuarios/
    Método HTTP: GET
    Autenticación: Requerida (IsAuthenticated)
    Modelo BD: Administradores, Maestros, Alumnos

    Retorna: { total_admins, total_maestros, total_alumnos }
    Consumido por: GraficosScreen para construir las gráficas de pastel, línea y dona.

    .count() es más eficiente que len(queryset): ejecuta SELECT COUNT(*) en SQL
    en lugar de traer todos los registros a Python solo para contarlos.
    """
    #Primero verificamos que el usuario esté autenticado para acceder a esta vista
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        total_admins = Administradores.objects.filter(user__is_active=1).count()
        total_maestros = Maestros.objects.filter(user__is_active=1).count()
        total_alumnos = Alumnos.objects.filter(user__is_active=1).count()
        #En caso de error, se puede manejar con un bloque try-except para capturar cualquier excepción que pueda ocurrir durante la consulta a la base de datos y devolver una respuesta adecuada.
        try:
            return Response({
                "total_admins": total_admins,
                "total_maestros": total_maestros,
                "total_alumnos": total_alumnos
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"details":"Error al obtener el total de usuarios"},400)
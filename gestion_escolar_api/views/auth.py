"""
views/auth.py
----------------------------------------------------------
Vistas de autenticación: login y logout del sistema.

¿Qué es un serializer y por qué se necesita?
    ObtainAuthToken (clase base de DRF) usa self.serializer_class para validar
    las credenciales (username y password) recibidas en request.data. El serializer
    se encarga de buscar el usuario en la BD y verificar la contraseña.
    Sin serializer, habría que hacer esa lógica manualmente con User.objects.get().

¿Qué hace @transaction.atomic?
    Envuelve la operación en una transacción de BD: si algún paso falla, se
    revierten TODOS los cambios anteriores. Es crucial en operaciones que
    crean múltiples registros (User + perfil) para evitar datos incompletos.
    Ejemplo: si se crea el User pero falla al crear el perfil Administradores,
    @transaction.atomic deshace la creación del User automáticamente.

¿Cómo viaja el token JWT?
    Tras un login exitoso, el backend genera un Token DRF (Token.objects.get_or_create)
    y lo incluye en la respuesta JSON. El frontend lo guarda en cookies y lo
    envía en cada petición subsiguiente en el header:
        Authorization: Bearer <token>
"""
from django.db.models import *
from gestion_escolar_api.models import *
from gestion_escolar_api.serializers import *
from gestion_escolar_api.models import *
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response


class CustomAuthToken(ObtainAuthToken):
    """
    Endpoint: POST /login/
    Método HTTP: POST
    Autenticación: No requiere (pública)
    Modelo BD: User, Alumnos, Maestros, Administradores, Token

    Recibe: { username: email, password: contraseña }
    Retorna: datos del perfil + token JWT + rol del usuario.

    Flujo:
        1. Valida credenciales con self.serializer_class (busca usuario y verifica pwd).
        2. Obtiene el grupo (rol) del usuario.
        3. Genera o recupera el token (Token.objects.get_or_create).
        4. Según el rol, serializa el perfil correspondiente y añade token + rol.
        5. Retorna la respuesta JSON con código 200.
    """

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                        context={'request': request})

        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if user.is_active:
            # Obtener perfil y roles del usuario
            roles = user.groups.all()
            role_names = []
            # Verifico si el usuario tiene un perfil asociado
            for role in roles:
                role_names.append(role.name)

            #Si solo es un rol especifico asignamos el elemento 0
            role_names = role_names[0]
            
            #Esta función genera la clave dinámica (token) para iniciar sesión
            token, created = Token.objects.get_or_create(user=user)
            
            #Verificar que tipo de usuario quiere iniciar sesión
            
            if role_names == 'alumno':
                alumno = Alumnos.objects.filter(user=user).first()
                alumno = AlumnoSerializer(alumno).data
                alumno["token"] = token.key
                alumno["rol"] = "alumno"
                return Response(alumno,200)
            if role_names == 'maestro':
                maestro = Maestros.objects.filter(user=user).first()
                maestro = MaestrosSerializer(maestro).data
                maestro["token"] = token.key
                maestro["rol"] = "maestro"
                return Response(maestro,200)
            if role_names == 'administrador':
                user = UserSerializer(user, many=False).data
                user['token'] = token.key
                user["rol"] = "administrador"
                return Response(user,200)
            else:
                return Response({"details":"Forbidden"},403)
                pass
            
        return Response({}, status=status.HTTP_403_FORBIDDEN)


class Logout(generics.GenericAPIView):
    """
    Endpoint: GET /logout/
    Método HTTP: GET
    Autenticación: Requerida (permission_classes = IsAuthenticated)
    Modelo BD: Token

    Recibe: token en el header Authorization: Bearer <token>
    Retorna: { 'logout': True } si el token se eliminó correctamente.

    permission_classes = (permissions.IsAuthenticated,):
        Obliga a que el request incluya un token válido. Si no lo incluye,
        DRF devuelve automáticamente 401 Unauthorized sin ejecutar el método.
        Así se protege el endpoint para que solo usuarios autenticados puedan cerrar sesión.

    Al eliminar el token (token.delete()), queda inválido: cualquier petición
    futura con ese token recibirá 401, forzando al usuario a volver a hacer login.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):

        print("logout")
        user = request.user
        print(str(user))
        if user.is_active:
            token = Token.objects.get(user=user)
            token.delete()

            return Response({'logout':True})


        return Response({'logout': False})

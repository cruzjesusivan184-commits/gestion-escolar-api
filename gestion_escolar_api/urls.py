"""
urls.py
----------------------------------------------------------
Define todas las rutas (endpoints) de la API REST del sistema escolar.

¿Qué es CORS y por qué está configurado en Django?
    CORS (Cross-Origin Resource Sharing) es una política de seguridad del
    navegador que bloquea peticiones entre dominios diferentes por defecto.
    El frontend Angular (localhost:4200) y el backend Django (localhost:8000)
    están en puertos distintos, por lo que son "orígenes diferentes".
    django-cors-headers añade los headers CORS en las respuestas para
    permitir que el navegador acepte las respuestas del backend.

Convención de rutas:
    - Los endpoints de lista (GET todos) usan nombres como lista-admins/.
    - Los endpoints de detalle/CRUD usan el nombre del recurso: admin/, maestros/, etc.
    - El mismo path maneja múltiples métodos HTTP (GET, POST, PUT, DELETE, PATCH)
      según la vista que esté asociada.

El token JWT viaja en cada petición autenticada en el header:
    Authorization: Bearer <token>
    El backend verifica este token con BearerTokenAuthentication (models.py)
    antes de ejecutar cualquier vista con permission_classes = IsAuthenticated.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views.bootstrap import VersionView
from gestion_escolar_api.views import alumnos, maestros, users, auth

urlpatterns = [
    #Agregamos las endpoints de usuarios
    #Create Admin
        path('admin/', users.AdminView.as_view()),
    #Lista de administradores
        path('lista-admins/', users.AdminAll.as_view()),
    #Edit Admin
        #path('admins-edit/', users.AdminsViewEdit.as_view())
    #Total de usuarios
        path('total-usuarios/', users.TotalUsuarios.as_view()),
    #Create Maestro
        path('maestros/', maestros.MaestrosView.as_view()),
    #Lista de maestros
        path('lista-maestros/', maestros.MaestrosAll.as_view()),
    #Create Alumno
        path('alumnos/', alumnos.AlumnosView.as_view()),
    #Lista de alumnos
        path('lista-alumnos/', alumnos.AlumnosAll.as_view()),
    #Login
        path('login/', auth.CustomAuthToken.as_view()),
    #Logout
        path('logout/', auth.Logout.as_view())
]
    
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

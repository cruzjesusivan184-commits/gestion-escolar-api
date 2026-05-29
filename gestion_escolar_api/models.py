"""
models.py
----------------------------------------------------------
Define los modelos (tablas) de la base de datos del sistema escolar.

¿Qué es un modelo en Django?
    Un modelo es una clase Python que hereda de models.Model y representa
    una tabla en la base de datos. Cada atributo de la clase es una columna.
    Django genera automáticamente las migraciones SQL cuando se ejecuta
    `makemigrations` y `migrate`.

Relación con el modelo User de Django:
    Se usa ForeignKey al modelo User incorporado de Django para almacenar
    las credenciales (username, email, password cifrada). Cada perfil
    (Administradores, Maestros, Alumnos) tiene un campo `user = ForeignKey(User)`
    que crea una relación uno-a-uno con la tabla auth_user.
    on_delete=models.CASCADE significa que si el User se elimina, el perfil
    también se elimina automáticamente.

BearerTokenAuthentication:
    Sobrescribe el prefijo del token de DRF de "Token" a "Bearer",
    para que el frontend Angular pueda enviar:
        Authorization: Bearer <token>
    en lugar de "Token <token>".
"""
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import AbstractUser, User
from django.conf import settings

from django.db import models
from django.contrib.auth.models import User

from rest_framework.authentication import TokenAuthentication

# BearerTokenAuthentication: adapta el esquema de autenticación de DRF
# para aceptar el prefijo "Bearer" en lugar del predeterminado "Token".
# Esto es necesario para compatibilidad con el frontend Angular que usa JWT.
class BearerTokenAuthentication(TokenAuthentication):
    keyword = "Bearer"


# ──────────────────────────────────────────────────────────────
# Modelo Administradores
# Tabla que almacena los datos adicionales de los usuarios administradores.
# Se vincula a la tabla auth_user de Django via ForeignKey.
# Los campos de autenticación (email, password) están en auth_user;
# los campos de perfil (clave_admin, rfc, etc.) están en esta tabla.
# ──────────────────────────────────────────────────────────────
class Administradores(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, default=None)
    clave_admin = models.CharField(max_length=255,null=True, blank=True)
    telefono = models.CharField(max_length=255, null=True, blank=True)
    rfc = models.CharField(max_length=255,null=True, blank=True)
    edad = models.IntegerField(null=True, blank=True)
    ocupacion = models.CharField(max_length=255,null=True, blank=True)
    categoria = models.CharField(max_length=255, null=True, blank=True)
    grado_academico = models.CharField(max_length=255, null=True, blank=True)
    creation = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "Perfil del admin "+self.user.first_name+" "+self.user.last_name
    
# ──────────────────────────────────────────────────────────────
# Modelo Maestros
# Tabla de perfil para usuarios con rol "maestro".
# materias_array se almacena como TextField con JSON serializado
# (json.dumps/json.loads en las vistas) porque SQLite no tiene campo JSON nativo.
# ──────────────────────────────────────────────────────────────
class Maestros(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, default=None)
    id_trabajador = models.CharField(max_length=255,null=True, blank=True)
    fecha_nacimiento = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    telefono = models.CharField(max_length=255, null=True, blank=True)
    rfc = models.CharField(max_length=255,null=True, blank=True)
    cubiculo = models.CharField(max_length=255,null=True, blank=True)
    edad = models.IntegerField(null=True, blank=True)
    area_investigacion = models.CharField(max_length=255,null=True, blank=True)
    materias_array = models.TextField(null=True, blank=True)
    campus = models.CharField(max_length=255, null=True, blank=True)
    sueldo_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    creation = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "Perfil del maestro "+self.user.first_name+" "+self.user.last_name
    
# ──────────────────────────────────────────────────────────────
# Modelo Alumnos
# Tabla de perfil para usuarios con rol "alumno".
# ──────────────────────────────────────────────────────────────
class Alumnos(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, default=None)
    matricula = models.CharField(max_length=255,null=True, blank=True)
    curp = models.CharField(max_length=255,null=True, blank=True)
    rfc = models.CharField(max_length=255,null=True, blank=True)
    fecha_nacimiento = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    edad = models.IntegerField(null=True, blank=True)
    telefono = models.CharField(max_length=255, null=True, blank=True)
    ocupacion = models.CharField(max_length=255,null=True, blank=True)
    direccion = models.CharField(max_length=500, null=True, blank=True)
    sexo = models.CharField(max_length=255, null=True, blank=True)
    creation = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    update = models.DateTimeField(null=True, blank=True)
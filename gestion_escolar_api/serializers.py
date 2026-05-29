"""
serializers.py
----------------------------------------------------------
Define los serializadores de Django REST Framework (DRF) para los modelos.

¿Qué es un serializador?
    Un serializador convierte objetos Python (instancias de modelos Django)
    en tipos de datos simples que pueden renderizarse como JSON para las
    respuestas HTTP, y también valida/deserializa datos entrantes (JSON)
    para crear o actualizar objetos de base de datos.

    Sin serializador habría que convertir cada campo manualmente a un dict.
    Con serializers.ModelSerializer, DRF infiere los campos del modelo
    automáticamente según Meta.fields.

    fields = '__all__': incluye todos los campos del modelo en el JSON de respuesta.

UserSerializer (anidado):
    AdminSerializer, MaestrosSerializer y AlumnoSerializer incluyen
    user = UserSerializer(read_only=True). Esto serializa el objeto User
    relacionado como un sub-objeto JSON { "id": 1, "first_name": "...", ... }
    en lugar de mostrar solo el id del ForeignKey.
    read_only=True evita que el API acepte modificar el User directamente
    a través de estos serializadores (se modifica via los endpoints de User).
"""
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Administradores, Maestros
from .models import Administradores, Alumnos


# UserSerializer: serializa solo los campos de identificación del User de Django.
# Se anida en AdminSerializer, MaestrosSerializer y AlumnoSerializer para que
# la respuesta JSON incluya los datos del usuario en lugar del id del ForeignKey.
class UserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('id','first_name','last_name', 'email')
        
# AdminSerializer: serializa el modelo Administradores con datos del usuario anidado.
# El campo user=UserSerializer(read_only=True) expande el ForeignKey como sub-objeto.
class AdminSerializer(serializers.ModelSerializer):
    user=UserSerializer(read_only=True)
    class Meta:
        model = Administradores
        fields = '__all__'

# MaestrosSerializer: serializa el modelo Maestros con datos del usuario anidado.
class MaestrosSerializer(serializers.ModelSerializer):
    user=UserSerializer(read_only=True)
    class Meta:
        model = Maestros
        fields = '__all__'

# AlumnoSerializer: serializa el modelo Alumnos con datos del usuario anidado.
class AlumnoSerializer(serializers.ModelSerializer):
    user=UserSerializer(read_only=True)
    class Meta:
        model = Alumnos
        fields = "__all__"

"""
views/bootstrap.py
----------------------------------------------------------
Vista utilitaria de información del sistema. Expone la versión actual
de la aplicación para health checks y monitoreo.

VersionView:
    Endpoint: GET /version/ (o la ruta que esté configurada en urls.py)
    Autenticación: No requiere (AllowAny + authentication_classes vacío)
    Retorna: { "version": "1.0.0" }

    Lee la versión de settings.APP_VERSION o de la variable de entorno APP_VERSION.
    Si ninguna está definida, retorna el default "1.0.0".
"""
import os
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions


class VersionView(APIView):
    """
    Vista pública que retorna la versión actual de la aplicación.
    authentication_classes = [] desactiva la autenticación para este endpoint.
    permissions.AllowAny permite el acceso a cualquier cliente, sin token.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        # Obtiene la versión desde settings o variable de entorno; default "1.0.0"
        version = getattr(settings, "APP_VERSION", os.getenv("APP_VERSION", "1.0.0"))
        return Response({"version": version})

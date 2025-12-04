"""
URLs para monitoreo y salud del sistema.
"""

from django.urls import path
from apps.core.views import health_check, metrics

urlpatterns = [
    path("", health_check, name="health-check"),
    path("metrics/", metrics, name="metrics"),
]


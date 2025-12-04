# apps/notifications/admin.py
"""
Configuración del admin para notificaciones.
"""

from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Notification.
    """
    list_display = ["titulo", "usuario", "tipo", "estado", "creada_en"]
    list_filter = ["tipo", "estado", "creada_en"]
    search_fields = ["titulo", "mensaje", "usuario__username"]
    readonly_fields = ["id", "creada_en", "leida_en"]
    ordering = ["-creada_en"]


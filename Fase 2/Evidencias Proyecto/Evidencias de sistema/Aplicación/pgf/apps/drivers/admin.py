# apps/drivers/admin.py
from django.contrib import admin
from .models import Chofer, HistorialAsignacionVehiculo


@admin.register(Chofer)
class ChoferAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "rut", "zona", "vehiculo_asignado", "activo", "fecha_ingreso")
    list_filter = ("activo", "zona", "sucursal")
    search_fields = ("nombre_completo", "rut", "telefono", "email")
    ordering = ("nombre_completo",)


@admin.register(HistorialAsignacionVehiculo)
class HistorialAsignacionVehiculoAdmin(admin.ModelAdmin):
    list_display = ("chofer", "vehiculo", "fecha_asignacion", "fecha_fin", "activa")
    list_filter = ("activa", "fecha_asignacion")
    search_fields = ("chofer__nombre_completo", "vehiculo__patente")
    ordering = ("-fecha_asignacion",)


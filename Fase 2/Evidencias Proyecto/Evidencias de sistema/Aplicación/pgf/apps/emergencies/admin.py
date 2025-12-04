# apps/emergencies/admin.py
from django.contrib import admin
from .models import EmergenciaRuta


@admin.register(EmergenciaRuta)
class EmergenciaRutaAdmin(admin.ModelAdmin):
    list_display = (
        "vehiculo", "estado", "prioridad", "solicitante",
        "aprobador", "mecanico_asignado", "fecha_solicitud", "zona"
    )
    list_filter = ("estado", "prioridad", "zona", "fecha_solicitud")
    search_fields = ("vehiculo__patente", "descripcion", "ubicacion")
    ordering = ("-fecha_solicitud",)
    date_hierarchy = "fecha_solicitud"
    readonly_fields = (
        "fecha_solicitud", "fecha_aprobacion", "fecha_asignacion",
        "fecha_resolucion", "fecha_cierre"
    )


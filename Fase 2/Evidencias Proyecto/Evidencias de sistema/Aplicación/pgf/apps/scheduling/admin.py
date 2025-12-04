# apps/scheduling/admin.py
from django.contrib import admin
from .models import Agenda, CupoDiario


@admin.register(Agenda)
class AgendaAdmin(admin.ModelAdmin):
    list_display = ("vehiculo", "fecha_programada", "tipo_mantenimiento", "estado", "coordinador", "zona")
    list_filter = ("estado", "tipo_mantenimiento", "zona", "fecha_programada")
    search_fields = ("vehiculo__patente", "motivo", "coordinador__username")
    ordering = ("-fecha_programada",)
    date_hierarchy = "fecha_programada"


@admin.register(CupoDiario)
class CupoDiarioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "cupos_disponibles", "cupos_totales", "cupos_ocupados", "zona")
    list_filter = ("fecha", "zona")
    ordering = ("-fecha",)
    date_hierarchy = "fecha"


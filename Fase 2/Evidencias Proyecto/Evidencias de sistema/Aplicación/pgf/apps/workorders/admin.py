from django.contrib import admin
from .models import (
    OrdenTrabajo, ItemOT, Presupuesto, DetallePresup,
    Aprobacion, Pausa, Checklist, Evidencia, Auditoria
)

@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = ("id", "vehiculo", "estado", "responsable", "apertura", "cierre")
    list_filter = ("estado", "apertura")
    search_fields = ("id", "vehiculo__patente", "motivo")

@admin.register(ItemOT)
class ItemOTAdmin(admin.ModelAdmin):
    list_display = ("id", "ot", "tipo", "descripcion", "cantidad", "costo_unitario")
    list_filter = ("tipo",)
    search_fields = ("descripcion", "ot__id")

@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = ("id", "ot", "total", "requiere_aprobacion", "creado_en")
    list_filter = ("requiere_aprobacion",)

@admin.register(DetallePresup)
class DetallePresupAdmin(admin.ModelAdmin):
    list_display = ("id", "presupuesto", "concepto", "cantidad", "precio")
    search_fields = ("concepto",)

@admin.register(Aprobacion)
class AprobacionAdmin(admin.ModelAdmin):
    list_display = ("id", "presupuesto", "sponsor", "estado", "fecha")
    list_filter = ("estado",)

@admin.register(Pausa)
class PausaAdmin(admin.ModelAdmin):
    list_display = ("id", "ot", "usuario", "motivo", "inicio", "fin")
    search_fields = ("motivo",)

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ("id", "ot", "verificador", "resultado", "fecha")
    list_filter = ("resultado",)

@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ("id", "ot", "tipo", "url", "subido_en")
    list_filter = ("tipo",)

@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ("ts", "accion", "objeto_tipo", "objeto_id", "usuario")
    list_filter = ("accion", "objeto_tipo", "ts")
    search_fields = ("objeto_id", "usuario__username")

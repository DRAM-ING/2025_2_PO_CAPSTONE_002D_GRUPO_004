from django.contrib import admin
from .models import Repuesto, Stock, MovimientoStock, SolicitudRepuesto, HistorialRepuestoVehiculo


@admin.register(Repuesto)
class RepuestoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "marca", "categoria", "activo", "created_at")
    list_filter = ("categoria", "activo", "marca")
    search_fields = ("codigo", "nombre", "marca", "descripcion")
    ordering = ("nombre",)


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("repuesto", "cantidad_actual", "cantidad_minima", "necesita_reorden", "updated_at")
    list_filter = ("cantidad_actual",)
    search_fields = ("repuesto__codigo", "repuesto__nombre", "ubicacion")
    ordering = ("-updated_at",)


@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ("repuesto", "tipo", "cantidad", "usuario", "fecha", "ot")
    list_filter = ("tipo", "fecha")
    search_fields = ("repuesto__codigo", "repuesto__nombre", "motivo")
    ordering = ("-fecha",)
    readonly_fields = ("fecha",)


@admin.register(SolicitudRepuesto)
class SolicitudRepuestoAdmin(admin.ModelAdmin):
    list_display = ("repuesto", "ot", "cantidad_solicitada", "estado", "fecha_solicitud")
    list_filter = ("estado", "fecha_solicitud")
    search_fields = ("repuesto__codigo", "repuesto__nombre", "ot__id")
    ordering = ("-fecha_solicitud",)
    readonly_fields = ("fecha_solicitud", "fecha_aprobacion", "fecha_entrega")


@admin.register(HistorialRepuestoVehiculo)
class HistorialRepuestoVehiculoAdmin(admin.ModelAdmin):
    list_display = ("vehiculo", "repuesto", "cantidad", "fecha_uso", "ot")
    list_filter = ("fecha_uso",)
    search_fields = ("vehiculo__patente", "repuesto__codigo", "repuesto__nombre")
    ordering = ("-fecha_uso",)
    readonly_fields = ("fecha_uso",)


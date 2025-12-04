# apps/inventory/models.py
from django.db import models
from django.conf import settings
from apps.vehicles.models import Vehiculo
from apps.workorders.models import OrdenTrabajo, ItemOT
import uuid


class Repuesto(models.Model):
    """Catálogo de repuestos disponibles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=64, unique=True, db_index=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    marca = models.CharField(max_length=128, blank=True)
    categoria = models.CharField(max_length=128, blank=True)  # ej: "Frenos", "Motor", "Transmisión"
    precio_referencia = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    unidad_medida = models.CharField(max_length=32, default="UNIDAD")  # UNIDAD, LITRO, KILO, etc.
    activo = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["categoria", "activo"]),
        ]
        ordering = ["nombre"]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Stock(models.Model):
    """Stock actual de repuestos en bodega"""
    repuesto = models.OneToOneField(Repuesto, on_delete=models.CASCADE, related_name="stock")
    cantidad_actual = models.PositiveIntegerField(default=0)
    cantidad_minima = models.PositiveIntegerField(default=0)  # Nivel de reorden
    ubicacion = models.CharField(max_length=128, blank=True)  # Ubicación física en bodega
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["cantidad_actual"]),
        ]
    
    def __str__(self):
        return f"{self.repuesto.codigo}: {self.cantidad_actual} unidades"
    
    @property
    def necesita_reorden(self):
        """Indica si el stock está por debajo del mínimo"""
        return self.cantidad_actual <= self.cantidad_minima


class MovimientoStock(models.Model):
    """Registro de movimientos de stock (entradas y salidas)"""
    class TipoMovimiento(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SALIDA = "SALIDA", "Salida"
        AJUSTE = "AJUSTE", "Ajuste"
        DEVOLUCION = "DEVOLUCION", "Devolución"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT, related_name="movimientos")
    tipo = models.CharField(max_length=20, choices=TipoMovimiento.choices)
    cantidad = models.PositiveIntegerField()
    cantidad_anterior = models.PositiveIntegerField()
    cantidad_nueva = models.PositiveIntegerField()
    motivo = models.TextField(blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimientos_stock")
    fecha = models.DateTimeField(auto_now_add=True)
    
    # Relaciones opcionales
    ot = models.ForeignKey(OrdenTrabajo, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimientos_stock")
    item_ot = models.ForeignKey(ItemOT, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimientos_stock")
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimientos_stock")
    
    class Meta:
        indexes = [
            models.Index(fields=["fecha"]),
            models.Index(fields=["repuesto", "fecha"]),
            models.Index(fields=["tipo", "fecha"]),
            models.Index(fields=["ot", "vehiculo"]),
        ]
        ordering = ["-fecha"]
    
    def __str__(self):
        return f"{self.tipo} {self.cantidad} {self.repuesto.codigo} - {self.fecha}"


class SolicitudRepuesto(models.Model):
    """Solicitudes de repuestos desde OT"""
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADA = "APROBADA", "Aprobada"
        RECHAZADA = "RECHAZADA", "Rechazada"
        ENTREGADA = "ENTREGADA", "Entregada"
        CANCELADA = "CANCELADA", "Cancelada"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ot = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE, related_name="solicitudes_repuestos")
    item_ot = models.ForeignKey(ItemOT, on_delete=models.CASCADE, related_name="solicitudes", null=True, blank=True)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT, related_name="solicitudes")
    cantidad_solicitada = models.PositiveIntegerField()
    cantidad_entregada = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    motivo = models.TextField(blank=True)
    
    # Usuarios involucrados
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="solicitudes_realizadas",
        null=True
    )
    aprobador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_aprobadas"
    )
    entregador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_entregadas"
    )
    
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["estado", "fecha_solicitud"]),
            models.Index(fields=["ot", "estado"]),
            models.Index(fields=["repuesto", "estado"]),
        ]
        ordering = ["-fecha_solicitud"]
    
    def __str__(self):
        return f"Solicitud {self.repuesto.codigo} x{self.cantidad_solicitada} - OT {self.ot.id}"


class HistorialRepuestoVehiculo(models.Model):
    """Histórico de repuestos utilizados por vehículo"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name="historial_repuestos")
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT, related_name="historial_vehiculos")
    cantidad = models.PositiveIntegerField()
    fecha_uso = models.DateTimeField(auto_now_add=True)
    ot = models.ForeignKey(OrdenTrabajo, on_delete=models.SET_NULL, null=True, blank=True, related_name="historial_repuestos")
    item_ot = models.ForeignKey(ItemOT, on_delete=models.SET_NULL, null=True, blank=True, related_name="historial_repuestos")
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["vehiculo", "fecha_uso"]),
            models.Index(fields=["repuesto", "fecha_uso"]),
            models.Index(fields=["ot"]),
        ]
        ordering = ["-fecha_uso"]
    
    def __str__(self):
        return f"{self.vehiculo.patente} - {self.repuesto.codigo} x{self.cantidad} - {self.fecha_uso}"


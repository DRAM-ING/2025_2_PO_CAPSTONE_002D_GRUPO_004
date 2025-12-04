# apps/drivers/models.py
from django.db import models
from apps.vehicles.models import Vehiculo
import uuid


class Chofer(models.Model):
    """Modelo para choferes de la flota"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre_completo = models.CharField(max_length=255)
    rut = models.CharField(max_length=12, unique=True, db_index=True, help_text="RUT sin puntos ni guión")
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    zona = models.CharField(max_length=100, blank=True, help_text="Zona o sucursal asignada")
    sucursal = models.CharField(max_length=100, blank=True, help_text="Sucursal específica")
    vehiculo_asignado = models.ForeignKey(
        Vehiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="choferes",
        help_text="Vehículo actualmente asignado"
    )
    km_mensual_promedio = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Kilometraje promedio mensual"
    )
    activo = models.BooleanField(default=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["rut"]),
            models.Index(fields=["zona", "activo"]),
            models.Index(fields=["vehiculo_asignado"]),
        ]
        ordering = ["nombre_completo"]
        verbose_name = "Chofer"
        verbose_name_plural = "Choferes"
    
    def __str__(self):
        return f"{self.nombre_completo} ({self.rut})"


class HistorialAsignacionVehiculo(models.Model):
    """Historial de asignaciones de vehículos a choferes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chofer = models.ForeignKey(Chofer, on_delete=models.CASCADE, related_name="historial_asignaciones")
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="historial_choferes")
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    motivo_fin = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["chofer", "activa"]),
            models.Index(fields=["vehiculo", "activa"]),
            models.Index(fields=["fecha_asignacion"]),
        ]
        ordering = ["-fecha_asignacion"]
    
    def __str__(self):
        return f"{self.chofer.nombre_completo} - {self.vehiculo.patente} ({self.fecha_asignacion})"


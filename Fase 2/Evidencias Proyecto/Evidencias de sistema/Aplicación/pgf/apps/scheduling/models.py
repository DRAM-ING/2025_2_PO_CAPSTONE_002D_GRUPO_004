# apps/scheduling/models.py
from django.db import models
from django.conf import settings
from apps.vehicles.models import Vehiculo
from apps.workorders.models import OrdenTrabajo
import uuid


class Agenda(models.Model):
    """Agenda de programación de mantenimientos"""
    ESTADOS = (
        ("PROGRAMADA", "Programada"),
        ("CONFIRMADA", "Confirmada"),
        ("EN_PROCESO", "En Proceso"),
        ("COMPLETADA", "Completada"),
        ("CANCELADA", "Cancelada"),
        ("REPROGRAMADA", "Reprogramada"),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="agendas")
    coordinador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="agendas_creadas",
        limit_choices_to={"rol": "COORDINADOR_ZONA"}
    )
    fecha_programada = models.DateTimeField(help_text="Fecha y hora programada para el mantenimiento")
    motivo = models.TextField(help_text="Motivo de la programación")
    tipo_mantenimiento = models.CharField(
        max_length=50,
        choices=[
            ("PREVENTIVO", "Preventivo"),
            ("CORRECTIVO", "Correctivo"),
            # ("EMERGENCIA", "Emergencia"),  # Opción removida
        ],
        default="PREVENTIVO"
    )
    zona = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="PROGRAMADA")
    observaciones = models.TextField(blank=True)
    
    # Relación con OT (se crea cuando el vehículo ingresa)
    ot_asociada = models.OneToOneField(
        OrdenTrabajo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agenda_origen"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["fecha_programada"]),
            models.Index(fields=["estado", "fecha_programada"]),
            models.Index(fields=["vehiculo", "estado"]),
            models.Index(fields=["zona", "fecha_programada"]),
        ]
        ordering = ["fecha_programada"]
        constraints = [
            models.UniqueConstraint(
                fields=["vehiculo", "fecha_programada"],
                condition=models.Q(estado__in=["PROGRAMADA", "CONFIRMADA", "EN_PROCESO"]),
                name="unique_vehiculo_fecha_activa"
            )
        ]
    
    def __str__(self):
        return f"{self.vehiculo.patente} - {self.fecha_programada.strftime('%Y-%m-%d %H:%M')}"


class CupoDiario(models.Model):
    """Cupos disponibles por día para programación"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fecha = models.DateField(unique=True, db_index=True)
    cupos_totales = models.PositiveIntegerField(default=10, help_text="Cupos totales del día")
    cupos_ocupados = models.PositiveIntegerField(default=0)
    zona = models.CharField(max_length=100, blank=True, help_text="Zona específica (opcional)")
    
    class Meta:
        indexes = [
            models.Index(fields=["fecha", "zona"]),
        ]
        ordering = ["fecha"]
    
    @property
    def cupos_disponibles(self):
        return self.cupos_totales - self.cupos_ocupados
    
    def __str__(self):
        return f"{self.fecha} - {self.cupos_disponibles}/{self.cupos_totales} disponibles"


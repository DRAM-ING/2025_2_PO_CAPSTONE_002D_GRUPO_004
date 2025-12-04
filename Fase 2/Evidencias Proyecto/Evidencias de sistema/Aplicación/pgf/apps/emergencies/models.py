# apps/emergencies/models.py
from django.db import models
from django.conf import settings
from apps.vehicles.models import Vehiculo
from apps.workorders.models import OrdenTrabajo
import uuid


class EmergenciaRuta(models.Model):
    """Emergencias en ruta que requieren atención especial"""
    ESTADOS = (
        ("SOLICITADA", "Solicitada"),
        ("APROBADA", "Aprobada"),
        ("ASIGNADA", "Asignada"),
        ("EN_CAMINO", "En Camino"),
        ("EN_REPARACION", "En Reparación"),
        ("RESUELTA", "Resuelta"),
        ("CERRADA", "Cerrada"),
        ("RECHAZADA", "Rechazada"),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="emergencias")
    
    # Usuarios involucrados
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="emergencias_solicitadas",
        help_text="Coordinador o Supervisor que solicita"
    )
    aprobador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emergencias_aprobadas",
        help_text="Jefe de Taller o Subgerencia que aprueba"
    )
    supervisor_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emergencias_supervisadas",
        limit_choices_to={"rol__in": ["SUPERVISOR", "COORDINADOR_ZONA"]}
    )
    mecanico_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emergencias_atendidas",
        limit_choices_to={"rol": "MECANICO"}
    )
    
    # Datos de la emergencia
    descripcion = models.TextField(help_text="Descripción de la emergencia")
    ubicacion = models.CharField(max_length=255, help_text="Ubicación donde ocurrió la emergencia")
    zona = models.CharField(max_length=100, blank=True)
    prioridad = models.CharField(
        max_length=20,
        choices=[
            ("CRITICA", "Crítica"),
            ("ALTA", "Alta"),
            ("MEDIA", "Media"),
        ],
        default="ALTA"
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default="SOLICITADA")
    
    # Fechas
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_asignacion = models.DateTimeField(null=True, blank=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    
    # Relación con OT (se crea cuando se asigna mecánico)
    ot_asociada = models.OneToOneField(
        OrdenTrabajo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emergencia_origen"
    )
    
    observaciones = models.TextField(blank=True)
    
    class Meta:
        app_label = "emergencies"
        indexes = [
            models.Index(fields=["estado", "fecha_solicitud"]),
            models.Index(fields=["vehiculo", "estado"]),
            models.Index(fields=["zona", "estado"]),
            models.Index(fields=["mecanico_asignado", "estado"]),
        ]
        ordering = ["-fecha_solicitud"]
    
    def __str__(self):
        return f"Emergencia {self.vehiculo.patente} - {self.estado} ({self.fecha_solicitud})"


# apps/notifications/models.py
"""
Modelos para el sistema de notificaciones.

Este módulo define:
- Notification: Notificaciones del sistema para usuarios

Relaciones:
- Notification -> User (ForeignKey) - Usuario destinatario
- Notification -> OrdenTrabajo (ForeignKey opcional) - OT relacionada
- Notification -> Evidencia (ForeignKey opcional) - Evidencia relacionada
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Notification(models.Model):
    """
    Notificación del sistema para un usuario.
    
    Representa una notificación que se muestra al usuario en el frontend.
    Puede estar relacionada con una OT, evidencia, o ser general.
    
    Tipos:
    - EVIDENCIA_SUBIDA: Se subió una evidencia importante
    - OT_CREADA: Se creó una nueva OT
    - OT_CERRADA: Se cerró una OT
    - OT_ASIGNADA: Se asignó una OT al usuario
    - OT_EN_PAUSA: Una OT entró en pausa
    - OT_EN_QA: Una OT entró en QA
    - OT_RETRABAJO: Una OT fue marcada como retrabajo
    - OT_APROBADA: Una OT fue aprobada
    - OT_RECHAZADA: Una OT fue rechazada
    - GENERAL: Notificación general
    
    Estados:
    - NO_LEIDA: Notificación no leída (default)
    - LEIDA: Notificación leída
    - ARCHIVADA: Notificación archivada
    """
    
    class TipoNotificacion(models.TextChoices):
        """
        Tipos de notificaciones disponibles.
        """
        EVIDENCIA_SUBIDA = "EVIDENCIA_SUBIDA", "Evidencia Subida"
        OT_CREADA = "OT_CREADA", "OT Creada"
        OT_CERRADA = "OT_CERRADA", "OT Cerrada"
        OT_ASIGNADA = "OT_ASIGNADA", "OT Asignada"
        OT_EN_PAUSA = "OT_EN_PAUSA", "OT en Pausa"
        OT_EN_QA = "OT_EN_QA", "OT en QA"
        OT_RETRABAJO = "OT_RETRABAJO", "OT Retrabajo"
        OT_APROBADA = "OT_APROBADA", "OT Aprobada"
        OT_RECHAZADA = "OT_RECHAZADA", "OT Rechazada"
        GENERAL = "GENERAL", "General"
    
    class EstadoNotificacion(models.TextChoices):
        """
        Estados de las notificaciones.
        """
        NO_LEIDA = "NO_LEIDA", "No Leída"
        LEIDA = "LEIDA", "Leída"
        ARCHIVADA = "ARCHIVADA", "Archivada"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Usuario destinatario de la notificación
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notificaciones"
    )
    
    # Tipo de notificación
    tipo = models.CharField(
        max_length=20,
        choices=TipoNotificacion.choices,
        default="GENERAL"
    )
    
    # Título de la notificación
    titulo = models.CharField(max_length=200)
    
    # Mensaje de la notificación
    mensaje = models.TextField()
    
    # Estado de la notificación
    estado = models.CharField(
        max_length=15,
        choices=EstadoNotificacion.choices,
        default="NO_LEIDA"
    )
    
    # Relaciones opcionales
    # OT relacionada (si aplica)
    ot = models.ForeignKey(
        "workorders.OrdenTrabajo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notificaciones"
    )
    
    # Evidencia relacionada (si aplica)
    evidencia = models.ForeignKey(
        "workorders.Evidencia",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notificaciones"
    )
    
    # Fecha de creación
    creada_en = models.DateTimeField(auto_now_add=True)
    
    # Fecha de lectura (cuando el usuario marca como leída)
    leida_en = models.DateTimeField(null=True, blank=True)
    
    # Datos adicionales en formato JSON
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        """
        Configuración del modelo.
        """
        ordering = ["-creada_en"]  # Más recientes primero
        indexes = [
            models.Index(fields=["usuario", "estado"]),  # Búsquedas por usuario y estado
            models.Index(fields=["creada_en"]),  # Ordenamiento por fecha
        ]
    
    def __str__(self):
        """
        Representación en string de la notificación.
        """
        return f"{self.titulo} - {self.usuario.username}"
    
    def marcar_como_leida(self):
        """
        Marca la notificación como leída.
        
        Actualiza el estado y la fecha de lectura.
        """
        if self.estado == "NO_LEIDA":
            self.estado = "LEIDA"
            self.leida_en = timezone.now()
            self.save(update_fields=["estado", "leida_en"])
    
    def archivar(self):
        """
        Archiva la notificación.
        
        Cambia el estado a ARCHIVADA.
        """
        self.estado = "ARCHIVADA"
        self.save(update_fields=["estado"])


# apps/notifications/serializers.py
"""
Serializers para el sistema de notificaciones.

Este módulo define:
- NotificationSerializer: Serializer para el modelo Notification
"""

from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Notification.
    
    Serializa todas las notificaciones del sistema, incluyendo
    información relacionada de OT y evidencias.
    """
    
    # Campos calculados
    ot_id = serializers.UUIDField(source="ot.id", read_only=True, allow_null=True)
    ot_patente = serializers.SerializerMethodField()
    evidencia_id = serializers.UUIDField(source="evidencia.id", read_only=True, allow_null=True)
    evidencia_tipo = serializers.CharField(source="evidencia.tipo", read_only=True, allow_null=True)
    
    def get_ot_patente(self, obj):
        """Obtiene la patente del vehículo de la OT si existe."""
        if obj.ot and obj.ot.vehiculo:
            return obj.ot.vehiculo.patente
        return None
    
    class Meta:
        model = Notification
        fields = [
            "id",
            "tipo",
            "titulo",
            "mensaje",
            "estado",
            "ot_id",
            "ot_patente",
            "evidencia_id",
            "evidencia_tipo",
            "creada_en",
            "leida_en",
            "metadata",
        ]
        read_only_fields = ["id", "creada_en", "leida_en"]


# apps/emergencies/serializers.py
from rest_framework import serializers
from .models import EmergenciaRuta
from apps.vehicles.serializers import VehiculoListSerializer


class EmergenciaRutaSerializer(serializers.ModelSerializer):
    vehiculo_info = VehiculoListSerializer(source="vehiculo", read_only=True)
    solicitante_nombre = serializers.SerializerMethodField()
    aprobador_nombre = serializers.SerializerMethodField()
    supervisor_nombre = serializers.SerializerMethodField()
    mecanico_nombre = serializers.SerializerMethodField()
    
    def get_solicitante_nombre(self, obj):
        """Retorna el nombre completo del solicitante o None si no existe."""
        return obj.solicitante.get_full_name() if obj.solicitante else None
    
    def get_aprobador_nombre(self, obj):
        """Retorna el nombre completo del aprobador o None si no existe."""
        return obj.aprobador.get_full_name() if obj.aprobador else None
    
    def get_supervisor_nombre(self, obj):
        """Retorna el nombre completo del supervisor o None si no existe."""
        return obj.supervisor_asignado.get_full_name() if obj.supervisor_asignado else None
    
    def get_mecanico_nombre(self, obj):
        """Retorna el nombre completo del mecánico o None si no existe."""
        return obj.mecanico_asignado.get_full_name() if obj.mecanico_asignado else None
    
    class Meta:
        model = EmergenciaRuta
        fields = [
            "id", "vehiculo", "vehiculo_info", "solicitante", "solicitante_nombre",
            "aprobador", "aprobador_nombre", "supervisor_asignado", "supervisor_nombre",
            "mecanico_asignado", "mecanico_nombre", "descripcion", "ubicacion",
            "zona", "prioridad", "estado", "fecha_solicitud", "fecha_aprobacion",
            "fecha_asignacion", "fecha_resolucion", "fecha_cierre", "ot_asociada",
            "observaciones"
        ]
        read_only_fields = [
            "id", "fecha_solicitud", "fecha_aprobacion", "fecha_asignacion",
            "fecha_resolucion", "fecha_cierre", "ot_asociada"
        ]


class EmergenciaRutaListSerializer(serializers.ModelSerializer):
    vehiculo_patente = serializers.CharField(source="vehiculo.patente", read_only=True)
    
    class Meta:
        model = EmergenciaRuta
        fields = [
            "id", "vehiculo_patente", "descripcion", "ubicacion", "prioridad",
            "estado", "fecha_solicitud", "zona"
        ]


class EmergenciaRutaCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear emergencia (solo requiere datos básicos)"""
    class Meta:
        model = EmergenciaRuta
        fields = [
            "vehiculo", "descripcion", "ubicacion", "zona", "prioridad", "observaciones"
        ]


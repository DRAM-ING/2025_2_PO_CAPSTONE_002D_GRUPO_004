# apps/scheduling/serializers.py
from rest_framework import serializers
from .models import Agenda, CupoDiario
from apps.vehicles.serializers import VehiculoListSerializer


class AgendaSerializer(serializers.ModelSerializer):
    vehiculo_info = VehiculoListSerializer(source="vehiculo", read_only=True)
    coordinador_nombre = serializers.CharField(source="coordinador.get_full_name", read_only=True)
    
    class Meta:
        model = Agenda
        fields = [
            "id", "vehiculo", "vehiculo_info", "coordinador", "coordinador_nombre",
            "fecha_programada", "motivo", "tipo_mantenimiento", "zona",
            "estado", "observaciones", "ot_asociada", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at", "ot_asociada", "coordinador"]


class AgendaListSerializer(serializers.ModelSerializer):
    vehiculo_patente = serializers.CharField(source="vehiculo.patente", read_only=True)
    
    class Meta:
        model = Agenda
        fields = [
            "id", "vehiculo_patente", "fecha_programada", "tipo_mantenimiento",
            "estado", "zona"
        ]


class CupoDiarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CupoDiario
        fields = [
            "id", "fecha", "cupos_totales", "cupos_ocupados", "cupos_disponibles", "zona"
        ]
        read_only_fields = ["id", "cupos_disponibles"]


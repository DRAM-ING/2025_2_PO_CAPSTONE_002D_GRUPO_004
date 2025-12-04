# apps/scheduling/tests/test_serializers.py
"""
Tests para serializers de scheduling.
"""

import pytest
from apps.scheduling.serializers import AgendaSerializer, CupoDiarioSerializer
from apps.scheduling.models import Agenda, CupoDiario


class TestAgendaSerializer:
    """Tests para AgendaSerializer"""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_agenda_serializer_valid(self, agenda):
        """Test serializar agenda válida"""
        serializer = AgendaSerializer(agenda)
        data = serializer.data
        
        assert data["tipo_mantenimiento"] == agenda.tipo_mantenimiento
        assert data["estado"] == agenda.estado
        assert "vehiculo" in data
        assert "coordinador" in data  # El serializer usa coordinador, no supervisor
        assert "vehiculo_info" in data
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_agenda_serializer_create(self, vehiculo, coordinador_user):
        """Test crear agenda desde serializer"""
        from django.utils import timezone
        from datetime import timedelta
        
        data = {
            "vehiculo": vehiculo.id,
            # coordinador se asigna automáticamente en perform_create, no se incluye aquí
            "fecha_programada": (timezone.now() + timedelta(days=7)).isoformat(),
            "motivo": "Mantenimiento preventivo de prueba",  # Campo requerido
            "tipo_mantenimiento": "PREVENTIVO",
            "estado": "PROGRAMADA",
            "observaciones": "Nueva programación"
        }
        serializer = AgendaSerializer(data=data)
        assert serializer.is_valid(), f"Errores del serializer: {serializer.errors}"
        
        # El coordinador se asigna en perform_create del ViewSet, pero aquí lo asignamos manualmente
        agenda = serializer.save(coordinador=coordinador_user)
        assert agenda.tipo_mantenimiento == "PREVENTIVO"
        assert agenda.estado == "PROGRAMADA"
        assert agenda.coordinador == coordinador_user


class TestCupoDiarioSerializer:
    """Tests para CupoDiarioSerializer"""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_cupo_serializer_valid(self, cupo_diario):
        """Test serializar cupo válido"""
        serializer = CupoDiarioSerializer(cupo_diario)
        data = serializer.data
        
        assert data["zona"] == cupo_diario.zona
        assert data["cupos_disponibles"] == cupo_diario.cupos_disponibles
        assert data["cupos_ocupados"] == cupo_diario.cupos_ocupados  # El modelo usa cupos_ocupados, no cupos_reservados
        assert data["cupos_totales"] == cupo_diario.cupos_totales


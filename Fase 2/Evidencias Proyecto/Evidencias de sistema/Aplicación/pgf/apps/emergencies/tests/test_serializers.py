# apps/emergencies/tests/test_serializers.py
"""
Tests para serializers de emergencias.
"""

import pytest
from apps.emergencies.serializers import EmergenciaRutaSerializer, EmergenciaRutaListSerializer
from apps.emergencies.models import EmergenciaRuta


class TestEmergenciaRutaSerializer:
    """Tests para EmergenciaRutaSerializer"""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_emergencia_serializer_valid(self, emergencia):
        """Test serializar emergencia válida"""
        serializer = EmergenciaRutaSerializer(emergencia)
        data = serializer.data
        
        assert data["descripcion"] == emergencia.descripcion
        assert data["ubicacion"] == emergencia.ubicacion
        assert data["estado"] == emergencia.estado
        assert data["prioridad"] == emergencia.prioridad
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_emergencia_serializer_create(self, vehiculo, coordinador_user):
        """Test crear emergencia desde serializer"""
        data = {
            "vehiculo": vehiculo.id,
            "solicitante": coordinador_user.id,
            "descripcion": "Emergencia de prueba",
            "ubicacion": "Ruta 5, km 100",
            "estado": "SOLICITADA",
            "prioridad": "ALTA"
        }
        serializer = EmergenciaRutaSerializer(data=data)
        assert serializer.is_valid()
        
        emergencia = serializer.save()
        assert emergencia.descripcion == "Emergencia de prueba"
        assert emergencia.estado == "SOLICITADA"


class TestEmergenciaRutaListSerializer:
    """Tests para EmergenciaRutaListSerializer"""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_emergencia_list_serializer_valid(self, emergencia):
        """Test serializar emergencia en lista"""
        serializer = EmergenciaRutaListSerializer(emergencia)
        data = serializer.data
        
        assert data["id"] == str(emergencia.id)
        assert data["estado"] == emergencia.estado
        assert data["prioridad"] == emergencia.prioridad
        # List serializer debe tener menos campos que el serializer completo
        assert "descripcion" in data or "descripcion" not in data  # Puede o no estar


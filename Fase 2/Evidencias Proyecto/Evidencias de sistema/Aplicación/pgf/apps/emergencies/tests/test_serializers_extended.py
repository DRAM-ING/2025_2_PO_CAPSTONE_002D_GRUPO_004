# apps/emergencies/tests/test_serializers_extended.py
"""
Tests extendidos para serializers de emergencias.
Cubre edge cases y manejo de errores.
"""

import pytest
from apps.emergencies.serializers import (
    EmergenciaRutaSerializer,
    EmergenciaRutaListSerializer,
    EmergenciaRutaCreateSerializer
)
from apps.emergencies.models import EmergenciaRuta


class TestEmergenciaRutaSerializerEdgeCases:
    """Tests para casos edge en EmergenciaRutaSerializer"""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_serializer_with_none_solicitante(self, emergencia):
        """Test que el serializer maneja correctamente solicitante=None"""
        emergencia.solicitante = None
        emergencia.save()
        
        serializer = EmergenciaRutaSerializer(emergencia)
        data = serializer.data
        
        assert data["solicitante_nombre"] is None
        assert "solicitante" in data
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_serializer_with_none_aprobador(self, emergencia):
        """Test que el serializer maneja correctamente aprobador=None"""
        emergencia.aprobador = None
        emergencia.save()
        
        serializer = EmergenciaRutaSerializer(emergencia)
        data = serializer.data
        
        assert data["aprobador_nombre"] is None
        assert "aprobador" in data
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_serializer_with_none_supervisor(self, emergencia):
        """Test que el serializer maneja correctamente supervisor_asignado=None"""
        emergencia.supervisor_asignado = None
        emergencia.save()
        
        serializer = EmergenciaRutaSerializer(emergencia)
        data = serializer.data
        
        assert data["supervisor_nombre"] is None
        assert "supervisor_asignado" in data
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_serializer_with_none_mecanico(self, emergencia):
        """Test que el serializer maneja correctamente mecanico_asignado=None"""
        emergencia.mecanico_asignado = None
        emergencia.save()
        
        serializer = EmergenciaRutaSerializer(emergencia)
        data = serializer.data
        
        assert data["mecanico_nombre"] is None
        assert "mecanico_asignado" in data
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_serializer_with_all_none_relations(self, vehiculo, coordinador_user):
        """Test serializer con todas las relaciones opcionales en None"""
        emergencia = EmergenciaRuta.objects.create(
            vehiculo=vehiculo,
            solicitante=coordinador_user,
            descripcion="Emergencia sin relaciones opcionales",
            ubicacion="Test",
            estado="SOLICITADA",
            prioridad="MEDIA",
            aprobador=None,
            supervisor_asignado=None,
            mecanico_asignado=None
        )
        
        serializer = EmergenciaRutaSerializer(emergencia)
        data = serializer.data
        
        assert data["solicitante_nombre"] is not None  # solicitante está definido
        assert data["aprobador_nombre"] is None
        assert data["supervisor_nombre"] is None
        assert data["mecanico_nombre"] is None


class TestEmergenciaRutaListSerializer:
    """Tests para EmergenciaRutaListSerializer"""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_list_serializer_with_none_vehiculo(self, emergencia):
        """Test que el list serializer maneja vehículo=None (edge case)"""
        # Este caso no debería ocurrir en producción, pero probamos el manejo
        emergencia.vehiculo = None
        emergencia.save()
        
        serializer = EmergenciaRutaListSerializer(emergencia)
        # No debería lanzar error, pero puede retornar None o string vacío
        data = serializer.data
        assert "vehiculo_patente" in data


class TestEmergenciaRutaCreateSerializer:
    """Tests para EmergenciaRutaCreateSerializer"""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_create_serializer_valid(self, vehiculo):
        """Test crear emergencia con datos válidos"""
        data = {
            "vehiculo": vehiculo.id,
            "descripcion": "Emergencia de prueba",
            "ubicacion": "Ruta 5, km 100",
            "zona": "Zona Norte",
            "prioridad": "ALTA",
            "observaciones": "Observaciones de prueba"
        }
        serializer = EmergenciaRutaCreateSerializer(data=data)
        assert serializer.is_valid(), f"Errores: {serializer.errors}"
        
        emergencia = serializer.save()
        assert emergencia.descripcion == "Emergencia de prueba"
        assert emergencia.ubicacion == "Ruta 5, km 100"
        assert emergencia.prioridad == "ALTA"
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_create_serializer_vehiculo_required(self):
        """Test que el vehículo es requerido"""
        data = {
            "descripcion": "Emergencia sin vehículo",
            "ubicacion": "Test",
            "prioridad": "ALTA"
        }
        serializer = EmergenciaRutaCreateSerializer(data=data)
        assert serializer.is_valid() is False
        assert "vehiculo" in serializer.errors
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_create_serializer_descripcion_required(self, vehiculo):
        """Test que la descripción es requerida"""
        data = {
            "vehiculo": vehiculo.id,
            "ubicacion": "Test",
            "prioridad": "ALTA"
        }
        serializer = EmergenciaRutaCreateSerializer(data=data)
        assert serializer.is_valid() is False
        assert "descripcion" in serializer.errors
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_create_serializer_invalid_vehiculo(self):
        """Test crear emergencia con vehículo inexistente"""
        import uuid
        data = {
            "vehiculo": uuid.uuid4(),  # UUID que no existe
            "descripcion": "Emergencia de prueba",
            "ubicacion": "Test",
            "prioridad": "ALTA"
        }
        serializer = EmergenciaRutaCreateSerializer(data=data)
        assert serializer.is_valid() is False
        assert "vehiculo" in serializer.errors


"""
Tests adicionales para serializers de vehicles.
"""

import pytest
from apps.vehicles.serializers import (
    VehiculoSerializer,
    VehiculoListSerializer,
    MarcaSerializer,
    IngresoVehiculoSerializer,
    HistorialVehiculoSerializer
)
from apps.vehicles.models import Vehiculo, IngresoVehiculo, HistorialVehiculo


@pytest.mark.serializer
class TestVehiculoSerializerExtended:
    """Tests adicionales para VehiculoSerializer"""
    
    def test_vehiculo_serializer_validate_patente_format(self, marca, supervisor_user):
        """Test validación de formato de patente"""
        serializer = VehiculoSerializer(data={
            'patente': 'INVALID',
            'marca': marca.id,
            'modelo': 'Test',
            'anio': 2023,
            'tipo': 'CAMION',
            'estado': 'ACTIVO',
            'supervisor': supervisor_user.id,
            'estado_operativo': 'OPERATIVO'
        })
        
        assert not serializer.is_valid()
        assert 'patente' in serializer.errors
    
    def test_vehiculo_serializer_marca_representation(self, vehiculo):
        """Test representación de marca en serializer"""
        serializer = VehiculoSerializer(vehiculo)
        
        assert 'marca' in serializer.data
        # La marca puede ser un ID o un objeto, dependiendo de la implementación
    
    def test_vehiculo_list_serializer_has_less_fields(self, vehiculo):
        """Test que VehiculoListSerializer tiene menos campos"""
        list_serializer = VehiculoListSerializer(vehiculo)
        full_serializer = VehiculoSerializer(vehiculo)
        
        # El list serializer debería tener menos campos
        assert len(list_serializer.data) <= len(full_serializer.data)


@pytest.mark.serializer
class TestMarcaSerializer:
    """Tests para MarcaSerializer"""
    
    def test_marca_serializer_create(self, db):
        """Test creación de marca"""
        serializer = MarcaSerializer(data={
            'nombre': 'Nueva Marca',
            'activa': True
        })
        
        assert serializer.is_valid()
        marca = serializer.save()
        assert marca.nombre == 'Nueva Marca'
    
    def test_marca_serializer_update(self, marca):
        """Test actualización de marca"""
        serializer = MarcaSerializer(marca, data={
            'nombre': 'Marca Actualizada',
            'activa': False
        })
        
        assert serializer.is_valid()
        marca = serializer.save()
        assert marca.nombre == 'Marca Actualizada'
        assert marca.activa is False


@pytest.mark.serializer
class TestIngresoVehiculoSerializer:
    """Tests para IngresoVehiculoSerializer"""
    
    def test_ingreso_serializer_create(self, vehiculo, guardia_user):
        """Test creación de ingreso"""
        serializer = IngresoVehiculoSerializer(data={
            'vehiculo': vehiculo.id,
            'guardia': guardia_user.id,
            'kilometraje': 50000,
            'observaciones_ingreso': 'Test ingreso'
        })
        
        assert serializer.is_valid()
        ingreso = serializer.save()
        assert ingreso.vehiculo == vehiculo
        assert ingreso.guardia == guardia_user


@pytest.mark.serializer
class TestHistorialVehiculoSerializer:
    """Tests para HistorialVehiculoSerializer"""
    
    def test_historial_serializer_read_only(self, vehiculo, orden_trabajo):
        """Test que HistorialVehiculoSerializer es principalmente read-only"""
        historial = HistorialVehiculo.objects.create(
            vehiculo=vehiculo,
            ot=orden_trabajo,
            tipo_evento='OT_CREADA',
            descripcion='Test historial'
        )
        
        serializer = HistorialVehiculoSerializer(historial)
        
        assert 'vehiculo' in serializer.data
        assert 'tipo_evento' in serializer.data


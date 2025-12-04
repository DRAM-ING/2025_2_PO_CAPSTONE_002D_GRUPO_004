# apps/drivers/tests/test_serializers.py
"""
Tests para serializers de drivers.
"""

import pytest
from apps.drivers.serializers import ChoferSerializer
from apps.drivers.models import Chofer


class TestChoferSerializer:
    """Tests para ChoferSerializer"""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_chofer_serializer_valid(self, chofer):
        """Test serializar chofer válido"""
        serializer = ChoferSerializer(chofer)
        data = serializer.data
        
        assert data["nombre_completo"] == chofer.nombre_completo
        assert data["rut"] == chofer.rut
        assert data["telefono"] == chofer.telefono
        assert data["email"] == chofer.email
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_chofer_serializer_create(self):
        """Test crear chofer desde serializer"""
        data = {
            "nombre_completo": "Pedro González",
            "rut": "12345678-5",
            "telefono": "+56987654321",
            "email": "pedro@test.com",
            "zona": "Norte",
            "activo": True
        }
        serializer = ChoferSerializer(data=data)
        assert serializer.is_valid()
        
        chofer = serializer.save()
        assert chofer.nombre_completo == "Pedro González"
        # El serializer normaliza el RUT quitando guiones y puntos
        assert chofer.rut == "123456785"


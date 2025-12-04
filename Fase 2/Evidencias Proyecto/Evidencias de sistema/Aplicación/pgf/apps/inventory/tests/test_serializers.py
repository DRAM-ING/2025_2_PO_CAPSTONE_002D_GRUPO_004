# apps/inventory/tests/test_serializers.py
"""
Tests para serializers de inventario.
"""

import pytest
from apps.inventory.serializers import RepuestoSerializer, StockSerializer, SolicitudRepuestoSerializer
from apps.inventory.models import Repuesto, Stock, SolicitudRepuesto


class TestRepuestoSerializer:
    """Tests para RepuestoSerializer"""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_repuesto_serializer_valid(self, repuesto):
        """Test serializar repuesto válido"""
        serializer = RepuestoSerializer(repuesto)
        data = serializer.data
        
        assert data["codigo"] == repuesto.codigo
        assert data["nombre"] == repuesto.nombre
        assert data["marca"] == repuesto.marca
        assert data["categoria"] == repuesto.categoria
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_repuesto_serializer_create(self):
        """Test crear repuesto desde serializer"""
        data = {
            "codigo": "REP003",
            "nombre": "Repuesto Nuevo",
            "marca": "Marca Test",
            "categoria": "MOTOR",
            "precio_referencia": 200.00,
            "activo": True
        }
        serializer = RepuestoSerializer(data=data)
        assert serializer.is_valid()
        
        repuesto = serializer.save()
        assert repuesto.codigo == "REP003"
        assert repuesto.nombre == "Repuesto Nuevo"


class TestStockSerializer:
    """Tests para StockSerializer"""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_stock_serializer_valid(self, stock):
        """Test serializar stock válido"""
        serializer = StockSerializer(stock)
        data = serializer.data
        
        assert data["cantidad_actual"] == stock.cantidad_actual
        assert data["cantidad_minima"] == stock.cantidad_minima
        assert "repuesto" in data


class TestSolicitudRepuestoSerializer:
    """Tests para SolicitudRepuestoSerializer"""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_solicitud_serializer_valid(self, solicitud_repuesto):
        """Test serializar solicitud válida"""
        serializer = SolicitudRepuestoSerializer(solicitud_repuesto)
        data = serializer.data
        
        assert data["cantidad_solicitada"] == solicitud_repuesto.cantidad_solicitada
        assert data["estado"] == solicitud_repuesto.estado
        assert "ot" in data
        assert "repuesto" in data


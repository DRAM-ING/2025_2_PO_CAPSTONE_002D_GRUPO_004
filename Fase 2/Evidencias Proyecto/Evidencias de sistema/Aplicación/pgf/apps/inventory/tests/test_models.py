# apps/inventory/tests/test_models.py
"""
Tests para modelos de inventario.
"""

import pytest
from apps.inventory.models import Repuesto, Stock, MovimientoStock, SolicitudRepuesto


class TestRepuestoModel:
    """Tests para modelo Repuesto"""
    
    @pytest.mark.model
    @pytest.mark.django_db
    def test_repuesto_str(self, repuesto):
        """Test método __str__ de Repuesto"""
        assert str(repuesto) == f"{repuesto.codigo} - {repuesto.nombre}"
    
    @pytest.mark.model
    @pytest.mark.django_db
    def test_repuesto_creates_stock_signal(self):
        """Test que crear repuesto permite crear stock manualmente"""
        repuesto = Repuesto.objects.create(
            codigo="REP004",
            nombre="Repuesto con Stock",
            marca="Marca Test",
            categoria="MOTOR",
            precio_referencia=150.00,
            activo=True
        )
        
        # Crear stock manualmente (no hay señal automática)
        stock = Stock.objects.create(
            repuesto=repuesto,
            cantidad_actual=0,
            cantidad_minima=10
        )
        
        # Verificar que se creó el stock
        assert stock is not None
        assert stock.cantidad_actual == 0
        assert stock.repuesto == repuesto


class TestStockModel:
    """Tests para modelo Stock"""
    
    @pytest.mark.model
    @pytest.mark.django_db
    def test_stock_str(self, stock):
        """Test método __str__ de Stock"""
        # El __str__ del modelo retorna: "{codigo}: {cantidad_actual} unidades"
        assert str(stock) == f"{stock.repuesto.codigo}: {stock.cantidad_actual} unidades"
    
    @pytest.mark.model
    @pytest.mark.django_db
    def test_stock_necesita_reorden(self, stock):
        """Test que stock detecta cuando necesita reorden"""
        stock.cantidad_actual = 5
        stock.cantidad_minima = 10
        stock.save()
        
        # Verificar propiedad necesita_reorden
        assert stock.necesita_reorden is True
        assert stock.cantidad_actual <= stock.cantidad_minima
        
        # Verificar que cuando hay suficiente stock, no necesita reorden
        stock.cantidad_actual = 15
        stock.save()
        assert stock.necesita_reorden is False


class TestMovimientoStockModel:
    """Tests para modelo MovimientoStock"""
    
    @pytest.mark.model
    @pytest.mark.django_db
    def test_movimiento_stock_str(self, stock, bodega_user):
        """Test método __str__ de MovimientoStock"""
        movimiento = MovimientoStock.objects.create(
            repuesto=stock.repuesto,
            tipo=MovimientoStock.TipoMovimiento.ENTRADA,
            cantidad=10,
            cantidad_anterior=stock.cantidad_actual,
            cantidad_nueva=stock.cantidad_actual + 10,
            motivo="Test",
            usuario=bodega_user
        )
        
        assert str(movimiento) is not None


class TestSolicitudRepuestoModel:
    """Tests para modelo SolicitudRepuesto"""
    
    @pytest.mark.model
    @pytest.mark.django_db
    def test_solicitud_str(self, solicitud_repuesto):
        """Test método __str__ de SolicitudRepuesto"""
        assert str(solicitud_repuesto) is not None
    
    @pytest.mark.model
    @pytest.mark.django_db
    def test_solicitud_estados(self):
        """Test estados válidos de solicitud"""
        estados = [choice[0] for choice in SolicitudRepuesto.Estado.choices]
        assert "PENDIENTE" in estados
        assert "APROBADA" in estados
        assert "RECHAZADA" in estados
        assert "ENTREGADA" in estados


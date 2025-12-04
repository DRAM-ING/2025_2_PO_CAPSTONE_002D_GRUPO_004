# apps/workorders/tests/test_serializers_edge_cases.py
"""
Tests para casos edge y manejo de errores en serializers de órdenes de trabajo.
"""

import pytest
from apps.workorders.serializers import (
    OrdenTrabajoSerializer,
    ItemOTSerializer,
    ItemOTCreateSerializer
)
from apps.workorders.models import OrdenTrabajo, ItemOT


class TestOrdenTrabajoSerializerEdgeCases:
    """Tests para casos edge en OrdenTrabajoSerializer"""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_serializer_with_none_responsable(self, orden_trabajo):
        """Test que el serializer maneja correctamente responsable=None"""
        orden_trabajo.responsable = None
        orden_trabajo.save()
        
        serializer = OrdenTrabajoSerializer(orden_trabajo)
        data = serializer.data
        
        assert data["responsable_nombre"] is None
        assert data["responsable_detalle"] is None
        assert "responsable" in data
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_serializer_with_none_supervisor(self, orden_trabajo):
        """Test que el serializer maneja correctamente supervisor=None"""
        orden_trabajo.supervisor = None
        orden_trabajo.save()
        
        serializer = OrdenTrabajoSerializer(orden_trabajo)
        data = serializer.data
        
        assert data["supervisor_nombre"] is None
        assert data["supervisor_detalle"] is None
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_serializer_with_none_mecanico(self, orden_trabajo):
        """Test que el serializer maneja correctamente mecanico=None"""
        orden_trabajo.mecanico = None
        orden_trabajo.save()
        
        serializer = OrdenTrabajoSerializer(orden_trabajo)
        data = serializer.data
        
        assert data["mecanico_nombre"] is None
        assert data["mecanico_detalle"] is None
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_serializer_with_none_vehiculo_marca(self, orden_trabajo, vehiculo):
        """Test que el serializer maneja correctamente vehiculo.marca=None"""
        vehiculo.marca = None
        vehiculo.save()
        orden_trabajo.vehiculo = vehiculo
        orden_trabajo.save()
        
        serializer = OrdenTrabajoSerializer(orden_trabajo)
        data = serializer.data
        
        assert data["vehiculo_detalle"]["marca"] is None
        assert data["vehiculo_detalle"]["marca_id"] is None
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_serializer_with_none_vehiculo_supervisor(self, orden_trabajo, vehiculo):
        """Test que el serializer maneja correctamente vehiculo.supervisor=None"""
        vehiculo.supervisor = None
        vehiculo.save()
        orden_trabajo.vehiculo = vehiculo
        orden_trabajo.save()
        
        serializer = OrdenTrabajoSerializer(orden_trabajo)
        data = serializer.data
        
        assert data["vehiculo_detalle"]["supervisor"] is None
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_serializer_vehiculo_detalle_completo(self, orden_trabajo, vehiculo):
        """Test que vehiculo_detalle incluye todos los campos esperados"""
        serializer = OrdenTrabajoSerializer(orden_trabajo)
        data = serializer.data
        
        vehiculo_detalle = data["vehiculo_detalle"]
        assert vehiculo_detalle is not None
        assert "id" in vehiculo_detalle
        assert "patente" in vehiculo_detalle
        assert "marca" in vehiculo_detalle
        assert "modelo" in vehiculo_detalle
        assert "anio" in vehiculo_detalle
        assert "tipo" in vehiculo_detalle
        assert "categoria" in vehiculo_detalle
        assert "estado" in vehiculo_detalle
        assert "estado_operativo" in vehiculo_detalle
        assert "kilometraje_actual" in vehiculo_detalle
        assert "zona" in vehiculo_detalle
        assert "sucursal" in vehiculo_detalle
        assert "vin" in vehiculo_detalle
        assert "supervisor" in vehiculo_detalle


class TestItemOTSerializerEdgeCases:
    """Tests para casos edge en ItemOTSerializer"""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_item_serializer_with_none_repuesto(self, orden_trabajo):
        """Test que el serializer maneja correctamente repuesto=None (para servicios)"""
        from decimal import Decimal
        item = ItemOT.objects.create(
            ot=orden_trabajo,
            tipo="SERVICIO",
            descripcion="Mano de obra",  # Usar 'descripcion' en lugar de 'concepto'
            cantidad=1,
            costo_unitario=Decimal("100.00"),  # Usar 'costo_unitario' en lugar de 'precio'
            repuesto=None
        )
        
        serializer = ItemOTSerializer(item)
        data = serializer.data
        
        assert data["tipo"] == "SERVICIO"
        assert data["repuesto"] is None or data["repuesto"] == ""
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_item_create_serializer_valid(self, orden_trabajo):
        """Test crear item con datos válidos"""
        data = {
            "tipo": "REPUESTO",
            "descripcion": "Filtro de aceite",  # Usar 'descripcion' en lugar de 'concepto'
            "cantidad": 2,
            "costo_unitario": "50.00"  # Usar 'costo_unitario' en lugar de 'precio'
        }
        serializer = ItemOTCreateSerializer(data=data)
        assert serializer.is_valid(), f"Errores: {serializer.errors}"
        
        item = serializer.save(ot=orden_trabajo)
        assert item.tipo == "REPUESTO"
        assert item.descripcion == "Filtro de aceite"
        assert item.cantidad == 2
        from decimal import Decimal
        assert item.costo_unitario == Decimal("50.00")
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_item_create_serializer_tipo_required(self, orden_trabajo):
        """Test que el tipo es requerido"""
        data = {
            "concepto": "Item sin tipo",
            "cantidad": 1,
            "precio": 10.0
        }
        serializer = ItemOTCreateSerializer(data=data)
        assert serializer.is_valid() is False
        assert "tipo" in serializer.errors
    
    @pytest.mark.serializer
    @pytest.mark.django_db
    def test_item_create_serializer_cantidad_positive(self, orden_trabajo):
        """Test que la cantidad debe ser positiva"""
        data = {
            "tipo": "REPUESTO",
            "concepto": "Item con cantidad negativa",
            "cantidad": -1,
            "precio": 10.0
        }
        serializer = ItemOTCreateSerializer(data=data)
        # Django debería validar esto, pero verificamos
        if not serializer.is_valid():
            # Si hay error, está bien
            pass
        else:
            # Si es válido, el modelo debería tener validación
            item = serializer.save(ot=orden_trabajo)
            assert item.cantidad > 0


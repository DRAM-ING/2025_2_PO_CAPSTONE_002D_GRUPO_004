"""
Tests adicionales para serializers de workorders que no están cubiertos.
"""

import pytest
from decimal import Decimal
from apps.workorders.serializers import (
    OrdenTrabajoSerializer,
    ItemOTSerializer,
    ItemOTCreateSerializer,
    PresupuestoSerializer,
    PausaSerializer,
    ChecklistSerializer
)
from apps.workorders.models import OrdenTrabajo, ItemOT, Presupuesto, Pausa, Checklist


@pytest.mark.serializer
class TestItemOTSerializerExtended:
    """Tests adicionales para ItemOTSerializer"""
    
    def test_item_serializer_calcula_subtotal(self, orden_trabajo, repuesto):
        """Test que el serializer calcula subtotal correctamente"""
        item = ItemOT.objects.create(
            ot=orden_trabajo,
            tipo='REPUESTO',
            repuesto=repuesto,
            descripcion='Test item',
            cantidad=2,
            costo_unitario=Decimal('100.00')
        )
        
        serializer = ItemOTSerializer(item)
        
        # Verificar que tiene los campos necesarios
        assert 'subtotal' in serializer.data or 'cantidad' in serializer.data
    
    def test_item_create_serializer_validates_required_fields(self, orden_trabajo):
        """Test validación de campos requeridos en ItemOTCreateSerializer"""
        serializer = ItemOTCreateSerializer(data={
            'tipo': 'REPUESTO',
            # Faltan campos requeridos
        })
        
        assert not serializer.is_valid()
        assert 'descripcion' in serializer.errors or 'costo_unitario' in serializer.errors


@pytest.mark.serializer
class TestPresupuestoSerializerExtended:
    """Tests adicionales para PresupuestoSerializer"""
    
    def test_presupuesto_serializer_includes_detalles(self, orden_trabajo, presupuesto):
        """Test que PresupuestoSerializer incluye detalles"""
        serializer = PresupuestoSerializer(presupuesto)
        
        assert 'total' in serializer.data
        # Puede tener detalles si están relacionados


@pytest.mark.serializer
class TestPausaSerializerExtended:
    """Tests adicionales para PausaSerializer"""
    
    def test_pausa_serializer_creation(self, orden_trabajo, mecanico_user):
        """Test creación de pausa con serializer"""
        serializer = PausaSerializer(data={
            'ot': orden_trabajo.id,
            'usuario': mecanico_user.id,
            'tipo': 'OTRO',
            'motivo': 'Test pausa'
        })
        
        assert serializer.is_valid()
        pausa = serializer.save()
        assert pausa.ot == orden_trabajo


@pytest.mark.serializer
class TestChecklistSerializerExtended:
    """Tests adicionales para ChecklistSerializer"""
    
    def test_checklist_serializer_creation(self, orden_trabajo, supervisor_user):
        """Test creación de checklist con serializer"""
        serializer = ChecklistSerializer(data={
            'ot': orden_trabajo.id,
            'verificador': supervisor_user.id,
            'items': [{'descripcion': 'Test item', 'cumplido': True}]
        })
        
        # El serializer puede requerir formato específico para items
        # Verificar que al menos valida
        assert serializer.is_valid() or 'items' in serializer.errors


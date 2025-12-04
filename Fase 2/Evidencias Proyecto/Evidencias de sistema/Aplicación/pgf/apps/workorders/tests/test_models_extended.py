# apps/workorders/tests/test_models_extended.py
"""
Tests extendidos para modelos de workorders.
Este archivo contiene tests para aumentar la cobertura al 100%.
"""

import pytest
from decimal import Decimal
from django.utils import timezone
from apps.workorders.models import (
    ItemOT, Presupuesto, DetallePresup, Aprobacion,
    Checklist, Evidencia, Auditoria
)


class TestItemOTModel:
    """Tests para el modelo ItemOT"""
    
    @pytest.mark.model
    def test_itemot_creation(self, db, orden_trabajo):
        """Test creación de ItemOT"""
        item = ItemOT.objects.create(
            ot=orden_trabajo,
            tipo="REPUESTO",
            descripcion="Repuesto de prueba",
            cantidad=2,
            costo_unitario=Decimal("100.00")
        )
        assert item.tipo == "REPUESTO"
        assert item.cantidad == 2
        assert item.costo_unitario == Decimal("100.00")
    
    @pytest.mark.model
    def test_itemot_str_representation(self, db, orden_trabajo):
        """Test representación string de ItemOT"""
        item = ItemOT.objects.create(
            ot=orden_trabajo,
            tipo="SERVICIO",
            descripcion="Servicio de prueba",
            cantidad=1,
            costo_unitario=Decimal("50.00")
        )
        assert str(item) is not None
        assert len(str(item)) > 0


class TestPresupuestoModel:
    """Tests para el modelo Presupuesto"""
    
    @pytest.mark.model
    def test_presupuesto_creation(self, db, orden_trabajo):
        """Test creación de Presupuesto"""
        presupuesto = Presupuesto.objects.create(
            ot=orden_trabajo,
            total=Decimal("500.00"),
            requiere_aprobacion=False,
            umbral=Decimal("1000.00")
        )
        assert presupuesto.total == Decimal("500.00")
        assert presupuesto.requiere_aprobacion is False
        assert presupuesto.ot == orden_trabajo
    
    @pytest.mark.model
    def test_presupuesto_str_representation(self, db, orden_trabajo):
        """Test representación string de Presupuesto"""
        presupuesto = Presupuesto.objects.create(
            ot=orden_trabajo,
            total=Decimal("500.00")
        )
        assert str(presupuesto) is not None


class TestDetallePresupModel:
    """Tests para el modelo DetallePresup"""
    
    @pytest.mark.model
    def test_detallepresup_creation(self, db, orden_trabajo):
        """Test creación de DetallePresup"""
        presupuesto = Presupuesto.objects.create(
            ot=orden_trabajo,
            total=Decimal("100.00")
        )
        detalle = DetallePresup.objects.create(
            presupuesto=presupuesto,
            concepto="Repuesto A",
            cantidad=2,
            precio=Decimal("50.00")
        )
        assert detalle.concepto == "Repuesto A"
        assert detalle.cantidad == 2
        assert detalle.precio == Decimal("50.00")
    
    @pytest.mark.model
    def test_detallepresup_str_representation(self, db, orden_trabajo):
        """Test representación string de DetallePresup"""
        presupuesto = Presupuesto.objects.create(
            ot=orden_trabajo,
            total=Decimal("100.00")
        )
        detalle = DetallePresup.objects.create(
            presupuesto=presupuesto,
            concepto="Test",
            cantidad=1,
            precio=Decimal("100.00")
        )
        assert str(detalle) is not None


class TestAprobacionModel:
    """Tests para el modelo Aprobacion"""
    
    @pytest.mark.model
    def test_aprobacion_creation(self, db, orden_trabajo, supervisor_user):
        """Test creación de Aprobacion"""
        presupuesto = Presupuesto.objects.create(
            ot=orden_trabajo,
            total=Decimal("1500.00"),
            requiere_aprobacion=True
        )
        aprobacion = Aprobacion.objects.create(
            presupuesto=presupuesto,
            sponsor=supervisor_user,
            estado="PENDIENTE",
            comentario="Esperando aprobación"
        )
        assert aprobacion.estado == "PENDIENTE"
        assert aprobacion.sponsor == supervisor_user
    
    @pytest.mark.model
    def test_aprobacion_str_representation(self, db, orden_trabajo, supervisor_user):
        """Test representación string de Aprobacion"""
        presupuesto = Presupuesto.objects.create(
            ot=orden_trabajo,
            total=Decimal("1500.00")
        )
        aprobacion = Aprobacion.objects.create(
            presupuesto=presupuesto,
            sponsor=supervisor_user,
            estado="PENDIENTE"
        )
        assert str(aprobacion) is not None


class TestChecklistModel:
    """Tests para el modelo Checklist"""
    
    @pytest.mark.model
    def test_checklist_creation(self, db, orden_trabajo, supervisor_user):
        """Test creación de Checklist"""
        checklist = Checklist.objects.create(
            ot=orden_trabajo,
            resultado="OK",
            observaciones="Checklist de prueba",
            verificador=supervisor_user
        )
        assert checklist.resultado == "OK"
        assert checklist.verificador == supervisor_user
    
    @pytest.mark.model
    def test_checklist_str_representation(self, db, orden_trabajo, supervisor_user):
        """Test representación string de Checklist"""
        checklist = Checklist.objects.create(
            ot=orden_trabajo,
            resultado="OK",
            verificador=supervisor_user
        )
        assert str(checklist) is not None


class TestEvidenciaModel:
    """Tests para el modelo Evidencia"""
    
    @pytest.mark.model
    def test_evidencia_creation(self, db, orden_trabajo):
        """Test creación de Evidencia"""
        evidencia = Evidencia.objects.create(
            ot=orden_trabajo,
            url="https://s3.example.com/evidencia.jpg",
            tipo="FOTO",
            descripcion="Evidencia de prueba"
        )
        assert evidencia.tipo == "FOTO"
        assert evidencia.url == "https://s3.example.com/evidencia.jpg"
    
    @pytest.mark.model
    def test_evidencia_without_ot(self, db):
        """Test creación de Evidencia sin OT (evidencia general)"""
        evidencia = Evidencia.objects.create(
            url="https://s3.example.com/general.jpg",
            tipo="FOTO",
            descripcion="Evidencia general"
        )
        assert evidencia.ot is None
        assert evidencia.tipo == "FOTO"


class TestAuditoriaModel:
    """Tests para el modelo Auditoria"""
    
    @pytest.mark.model
    def test_auditoria_creation(self, db, supervisor_user):
        """Test creación de Auditoria"""
        auditoria = Auditoria.objects.create(
            usuario=supervisor_user,
            accion="TEST_ACTION",
            objeto_tipo="TestObject",
            objeto_id="123",
            payload={"test": "data"}
        )
        assert auditoria.accion == "TEST_ACTION"
        assert auditoria.usuario == supervisor_user
    
    @pytest.mark.model
    def test_auditoria_without_usuario(self, db):
        """Test creación de Auditoria sin usuario (acción del sistema)"""
        auditoria = Auditoria.objects.create(
            accion="SYSTEM_ACTION",
            objeto_tipo="SystemObject",
            objeto_id="456"
        )
        assert auditoria.usuario is None
        assert auditoria.accion == "SYSTEM_ACTION"


# apps/workorders/tests/test_models.py
"""
Tests para los modelos de órdenes de trabajo.
"""

import pytest
from datetime import datetime, timedelta
from apps.workorders.models import OrdenTrabajo, Pausa, Evidencia
from apps.vehicles.models import Vehiculo


class TestOrdenTrabajoModel:
    """Tests para el modelo OrdenTrabajo"""
    
    @pytest.mark.model
    def test_orden_trabajo_creation(self, orden_trabajo):
        """Test creación básica de orden de trabajo"""
        assert orden_trabajo.estado == OrdenTrabajo.ESTADOS[0][0]  # ABIERTA
        assert orden_trabajo.motivo == "Prueba de OT"
    
    @pytest.mark.model
    def test_orden_trabajo_estado_transitions(self, orden_trabajo):
        """Test transiciones de estado"""
        assert orden_trabajo.estado == "ABIERTA"
        
        orden_trabajo.estado = "EN_DIAGNOSTICO"
        orden_trabajo.save()
        assert orden_trabajo.estado == "EN_DIAGNOSTICO"
    
    @pytest.mark.model
    def test_orden_trabajo_str_representation(self, orden_trabajo):
        """Test representación string de la OT"""
        # El __str__ puede usar id o algún otro campo
        str_repr = str(orden_trabajo)
        assert str_repr is not None
        assert len(str_repr) > 0


class TestPausaModel:
    """Tests para el modelo Pausa"""
    
    @pytest.mark.model
    def test_pausa_creation(self, db, orden_trabajo, supervisor_user):
        """Test creación básica de pausa"""
        from apps.workorders.models import Pausa
        orden_trabajo.estado = "EN_EJECUCION"
        orden_trabajo.save()
        
        pausa = Pausa.objects.create(
            ot=orden_trabajo,
            motivo="Prueba de pausa",
            usuario=supervisor_user
        )
        assert pausa.ot == orden_trabajo
        assert pausa.motivo == "Prueba de pausa"
        assert pausa.inicio is not None
    
    @pytest.mark.model
    def test_pausa_str_representation(self, db, orden_trabajo, supervisor_user):
        """Test representación string de pausa"""
        from apps.workorders.models import Pausa
        orden_trabajo.estado = "EN_EJECUCION"
        orden_trabajo.save()
        
        pausa = Pausa.objects.create(
            ot=orden_trabajo,
            motivo="Prueba",
            usuario=supervisor_user
        )
        # Verificar que tiene representación string
        str_repr = str(pausa)
        assert str_repr is not None
        assert len(str_repr) > 0


class TestEvidenciaModel:
    """Tests para el modelo Evidencia"""
    
    @pytest.mark.model
    def test_evidencia_creation(self, db, orden_trabajo):
        """Test creación básica de evidencia"""
        from apps.workorders.models import Evidencia
        evidencia = Evidencia.objects.create(
            ot=orden_trabajo,
            url="https://s3.example.com/evidencia.jpg",
            tipo="FOTO",
            descripcion="Foto de prueba"
        )
        assert evidencia.ot == orden_trabajo
        assert evidencia.url == "https://s3.example.com/evidencia.jpg"
        assert evidencia.tipo == "FOTO"
    
    @pytest.mark.model
    def test_evidencia_without_ot(self, db):
        """Test creación de evidencia sin OT (evidencia general)"""
        from apps.workorders.models import Evidencia
        evidencia = Evidencia.objects.create(
            url="https://s3.example.com/evidencia.jpg",
            tipo="FOTO",
            descripcion="Evidencia general"
        )
        assert evidencia.ot is None
        assert evidencia.url == "https://s3.example.com/evidencia.jpg"
    
    @pytest.mark.model
    def test_evidencia_str_representation(self, db, orden_trabajo):
        """Test representación string de evidencia"""
        from apps.workorders.models import Evidencia
        evidencia = Evidencia.objects.create(
            ot=orden_trabajo,
            url="https://s3.example.com/evidencia.jpg",
            tipo="FOTO",
            descripcion="Foto de prueba"
        )
        assert str(evidencia) is not None


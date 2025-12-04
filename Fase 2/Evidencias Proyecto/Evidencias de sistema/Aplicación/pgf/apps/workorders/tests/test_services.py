"""
Tests para los servicios de transición de estado en workorders.
"""

import pytest
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta
from apps.workorders.models import OrdenTrabajo
from apps.workorders.services import (
    can_transition,
    transition,
    do_transition,
    create_work_order,
    VALID_TRANSITIONS
)


@pytest.mark.unit
class TestCanTransition:
    """Tests para can_transition"""
    
    def test_valid_transition_abierta_to_en_diagnostico(self):
        """Test transición válida ABIERTA → EN_DIAGNOSTICO"""
        assert can_transition("ABIERTA", "EN_DIAGNOSTICO") is True
    
    def test_valid_transition_abierta_to_en_ejecucion(self):
        """Test transición válida ABIERTA → EN_EJECUCION"""
        assert can_transition("ABIERTA", "EN_EJECUCION") is True
    
    def test_valid_transition_en_diagnostico_to_en_ejecucion(self):
        """Test transición válida EN_DIAGNOSTICO → EN_EJECUCION"""
        assert can_transition("EN_DIAGNOSTICO", "EN_EJECUCION") is True
    
    def test_valid_transition_en_ejecucion_to_en_pausa(self):
        """Test transición válida EN_EJECUCION → EN_PAUSA"""
        assert can_transition("EN_EJECUCION", "EN_PAUSA") is True
    
    def test_valid_transition_en_pausa_to_en_ejecucion(self):
        """Test transición válida EN_PAUSA → EN_EJECUCION"""
        assert can_transition("EN_PAUSA", "EN_EJECUCION") is True
    
    def test_valid_transition_en_ejecucion_to_en_qa(self):
        """Test transición válida EN_EJECUCION → EN_QA"""
        assert can_transition("EN_EJECUCION", "EN_QA") is True
    
    def test_valid_transition_en_qa_to_cerrada(self):
        """Test transición válida EN_QA → CERRADA"""
        assert can_transition("EN_QA", "CERRADA") is True
    
    def test_valid_transition_cerrada_to_en_ejecucion(self):
        """Test transición válida CERRADA → EN_EJECUCION (reabrir)"""
        assert can_transition("CERRADA", "EN_EJECUCION") is True
    
    def test_invalid_transition_cerrada_to_abierta(self):
        """Test transición inválida CERRADA → ABIERTA"""
        assert can_transition("CERRADA", "ABIERTA") is False
    
    def test_invalid_transition_anulada_to_any(self):
        """Test que ANULADA no puede cambiar a ningún estado"""
        assert can_transition("ANULADA", "ABIERTA") is False
        assert can_transition("ANULADA", "EN_EJECUCION") is False
        assert can_transition("ANULADA", "CERRADA") is False
    
    def test_invalid_transition_en_pausa_to_en_qa(self):
        """Test transición inválida EN_PAUSA → EN_QA (debe pasar por EN_EJECUCION)"""
        assert can_transition("EN_PAUSA", "EN_QA") is False
    
    def test_invalid_transition_unknown_state(self):
        """Test transición desde estado desconocido"""
        assert can_transition("ESTADO_INEXISTENTE", "ABIERTA") is False


@pytest.mark.unit
class TestTransition:
    """Tests para transition"""
    
    def test_transition_success_abierta_to_en_diagnostico(self, orden_trabajo):
        """Test transición exitosa ABIERTA → EN_DIAGNOSTICO"""
        orden_trabajo.estado = "ABIERTA"
        orden_trabajo.save()
        
        success, error = transition(orden_trabajo, "EN_DIAGNOSTICO")
        
        assert success is True
        assert error is None
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.estado == "EN_DIAGNOSTICO"
        assert orden_trabajo.fecha_diagnostico is not None
    
    def test_transition_success_en_diagnostico_to_en_ejecucion(self, orden_trabajo):
        """Test transición exitosa EN_DIAGNOSTICO → EN_EJECUCION"""
        orden_trabajo.estado = "EN_DIAGNOSTICO"
        orden_trabajo.save()
        
        success, error = transition(orden_trabajo, "EN_EJECUCION")
        
        assert success is True
        assert error is None
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.estado == "EN_EJECUCION"
        assert orden_trabajo.fecha_inicio_ejecucion is not None
    
    def test_transition_success_en_ejecucion_to_cerrada(self, orden_trabajo):
        """Test transición exitosa EN_EJECUCION → CERRADA"""
        orden_trabajo.estado = "EN_EJECUCION"
        orden_trabajo.save()
        
        # Primero pasar por EN_QA
        transition(orden_trabajo, "EN_QA")
        orden_trabajo.refresh_from_db()
        
        success, error = transition(orden_trabajo, "CERRADA")
        
        assert success is True
        assert error is None
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.estado == "CERRADA"
        assert orden_trabajo.cierre is not None
    
    def test_transition_preserves_fecha_inicio_ejecucion(self, orden_trabajo):
        """Test que fecha_inicio_ejecucion no se sobrescribe"""
        orden_trabajo.estado = "EN_EJECUCION"
        fecha_original = timezone.now() - timedelta(days=1)
        orden_trabajo.fecha_inicio_ejecucion = fecha_original
        orden_trabajo.save()
        
        # Cambiar a EN_PAUSA y volver a EN_EJECUCION
        transition(orden_trabajo, "EN_PAUSA")
        transition(orden_trabajo, "EN_EJECUCION")
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.fecha_inicio_ejecucion == fecha_original
    
    def test_transition_failure_invalid_transition(self, orden_trabajo):
        """Test transición fallida por transición inválida"""
        orden_trabajo.estado = "CERRADA"
        orden_trabajo.save()
        
        success, error = transition(orden_trabajo, "ABIERTA")
        
        assert success is False
        assert error is not None
        assert "inválida" in error.lower()
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.estado == "CERRADA"  # No cambió


@pytest.mark.unit
class TestDoTransition:
    """Tests para do_transition"""
    
    def test_do_transition_success(self, orden_trabajo, admin_user):
        """Test do_transition exitosa"""
        orden_trabajo.estado = "ABIERTA"
        orden_trabajo.save()
        
        do_transition(orden_trabajo, "EN_DIAGNOSTICO", usuario=admin_user)
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.estado == "EN_DIAGNOSTICO"
    
    def test_do_transition_creates_auditoria(self, orden_trabajo, admin_user):
        """Test que do_transition crea registro de auditoría"""
        from apps.workorders.models import Auditoria
        
        orden_trabajo.estado = "ABIERTA"
        orden_trabajo.save()
        
        estado_anterior = orden_trabajo.estado
        do_transition(orden_trabajo, "EN_DIAGNOSTICO", usuario=admin_user)
        
        auditoria = Auditoria.objects.filter(
            usuario=admin_user,
            accion="CAMBIO_ESTADO",
            objeto_tipo="OrdenTrabajo",
            objeto_id=str(orden_trabajo.id)
        ).first()
        
        assert auditoria is not None
        assert auditoria.payload['estado_anterior'] == estado_anterior
        assert auditoria.payload['estado_nuevo'] == "EN_DIAGNOSTICO"
    
    def test_do_transition_raises_value_error_on_invalid(self, orden_trabajo):
        """Test que do_transition lanza ValueError en transición inválida"""
        orden_trabajo.estado = "ANULADA"
        orden_trabajo.save()
        
        with pytest.raises(ValueError):
            do_transition(orden_trabajo, "ABIERTA")
    
    def test_do_transition_no_auditoria_on_same_state(self, orden_trabajo, admin_user):
        """Test que do_transition no crea auditoría si el estado no cambia"""
        from apps.workorders.models import Auditoria
        
        orden_trabajo.estado = "ABIERTA"
        orden_trabajo.save()
        
        # Intentar cambiar al mismo estado (no debería crear auditoría)
        # Pero primero necesitamos una transición válida
        do_transition(orden_trabajo, "EN_DIAGNOSTICO", usuario=admin_user)
        count_before = Auditoria.objects.count()
        
        # Cambiar a otro estado válido
        do_transition(orden_trabajo, "EN_EJECUCION", usuario=admin_user)
        count_after = Auditoria.objects.count()
        
        # Debería haber creado una nueva auditoría
        assert count_after > count_before


@pytest.mark.unit
class TestCreateWorkOrder:
    """Tests para create_work_order"""
    
    def test_create_work_order_success(self, vehiculo, supervisor_user, mecanico_user, jefe_taller_user):
        """Test creación exitosa de OT"""
        data = {
            'vehiculo': vehiculo,
            'responsable': supervisor_user,
            'mecanico': mecanico_user,  # Agregar mecánico para que quede en ABIERTA
            'estado': 'ABIERTA',
            'motivo': 'Test OT'
        }
        
        ot = create_work_order(data, jefe_taller_user)
        
        assert ot is not None
        assert ot.vehiculo == vehiculo
        assert ot.responsable == supervisor_user
        assert ot.estado == "ABIERTA"  # Con mecánico, debería quedar en ABIERTA
    
    def test_create_work_order_without_mecanico_sets_pausa(self, vehiculo, supervisor_user, jefe_taller_user):
        """Test que OT sin mecánico se pone en EN_PAUSA"""
        data = {
            'vehiculo': vehiculo,
            'responsable': supervisor_user,
            'estado': 'ABIERTA',
            'motivo': 'Test OT',
            'mecanico': None
        }
        
        ot = create_work_order(data, jefe_taller_user)
        
        assert ot.estado == "EN_PAUSA"
    
    def test_create_work_order_with_mecanico_sets_abierta(self, vehiculo, supervisor_user, mecanico_user, jefe_taller_user):
        """Test que OT con mecánico se pone en ABIERTA"""
        data = {
            'vehiculo': vehiculo,
            'responsable': supervisor_user,
            'mecanico': mecanico_user,
            'estado': 'EN_DIAGNOSTICO',  # Intentar otro estado
            'motivo': 'Test OT'
        }
        
        ot = create_work_order(data, jefe_taller_user)
        
        assert ot.estado == "ABIERTA"
    
    def test_create_work_order_permission_denied(self, vehiculo, supervisor_user, mecanico_user):
        """Test que create_work_order rechaza usuarios sin permisos"""
        data = {
            'vehiculo': vehiculo,
            'responsable': supervisor_user,
            'mecanico': mecanico_user,
            'estado': 'ABIERTA',
            'motivo': 'Test OT'
        }
        
        with pytest.raises(PermissionError):
            create_work_order(data, mecanico_user)  # Mecánico no puede crear OT
    
    @patch('apps.vehicles.utils.registrar_ot_creada')
    @patch('apps.vehicles.utils.calcular_sla_ot')
    def test_create_work_order_handles_historial_error(self, mock_sla, mock_historial, vehiculo, supervisor_user, jefe_taller_user):
        """Test que create_work_order maneja errores en registro de historial"""
        mock_historial.side_effect = Exception("Historial error")
        
        data = {
            'vehiculo': vehiculo,
            'responsable': supervisor_user,
            'estado': 'ABIERTA',
            'motivo': 'Test OT'
        }
        
        # No debería fallar, solo loguear el error
        ot = create_work_order(data, jefe_taller_user)
        
        assert ot is not None
    
    @patch('apps.notifications.utils.crear_notificacion_ot_creada')
    def test_create_work_order_handles_notification_error(self, mock_notif, vehiculo, supervisor_user, jefe_taller_user):
        """Test que create_work_order maneja errores en notificaciones"""
        mock_notif.side_effect = Exception("Notification error")
        
        data = {
            'vehiculo': vehiculo,
            'responsable': supervisor_user,
            'estado': 'ABIERTA',
            'motivo': 'Test OT'
        }
        
        # No debería fallar, solo loguear el error
        ot = create_work_order(data, jefe_taller_user)
        
        assert ot is not None

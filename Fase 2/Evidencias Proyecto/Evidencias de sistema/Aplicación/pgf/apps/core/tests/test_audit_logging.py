# apps/core/tests/test_audit_logging.py
"""
Tests para utilidades de logging de auditoría.
"""

import pytest
from apps.core.audit_logging import log_audit, log_security_event
from apps.workorders.models import Auditoria


class TestAuditLogging:
    """Tests para funciones de logging de auditoría"""
    
    @pytest.mark.unit
    @pytest.mark.django_db
    def test_log_audit_creates_record(self, admin_user):
        """Test que log_audit crea registro en base de datos"""
        auditoria = log_audit(
            usuario=admin_user,
            accion="TEST_ACTION",
            objeto_tipo="TestObject",
            objeto_id="123",
            payload={"test": "data"}
        )
        
        assert auditoria is not None
        assert auditoria.usuario == admin_user
        assert auditoria.accion == "TEST_ACTION"
        assert auditoria.objeto_tipo == "TestObject"
        assert auditoria.objeto_id == "123"
        assert auditoria.payload == {"test": "data"}
        
        # Verificar que se guardó en BD
        assert Auditoria.objects.filter(id=auditoria.id).exists()
    
    @pytest.mark.unit
    @pytest.mark.django_db
    def test_log_audit_without_payload(self, admin_user):
        """Test log_audit sin payload"""
        auditoria = log_audit(
            usuario=admin_user,
            accion="TEST_ACTION",
            objeto_tipo="TestObject"
        )
        
        assert auditoria is not None
        assert auditoria.payload == {}
    
    @pytest.mark.unit
    @pytest.mark.django_db
    def test_log_security_event(self, admin_user):
        """Test log_security_event"""
        auditoria = log_security_event(
            usuario=admin_user,
            evento="LOGIN_FAILED",
            detalles={"ip": "192.168.1.1"},
            ip_address="192.168.1.1"
        )
        
        assert auditoria is not None
        assert auditoria.accion == "SECURITY_LOGIN_FAILED"
        assert auditoria.objeto_tipo == "SecurityEvent"
        assert "ip_address" in auditoria.payload
        assert auditoria.payload["ip_address"] == "192.168.1.1"


# apps/workorders/tests/test_permissions.py
"""
Tests para los permisos de órdenes de trabajo según nueva especificación.
"""

import pytest
from rest_framework import status
from apps.workorders.permissions import (
    WorkOrderPermission, 
    ALLOWED_ROLES_READ, 
    ALLOWED_ROLES_CREATE,
    ALLOWED_ROLES_UPDATE,
    ALLOWED_ROLES_CLOSE
)
from apps.workorders.models import OrdenTrabajo


class TestWorkOrderPermission:
    """Tests para WorkOrderPermission según nueva especificación"""
    
    @pytest.mark.permission
    def test_unauthenticated_user_denied(self, api_client):
        """Test que usuario no autenticado es denegado"""
        permission = WorkOrderPermission()
        request = type('Request', (), {'user': None, 'method': 'GET'})()
        assert permission.has_permission(request, None) is False
    
    @pytest.mark.permission
    def test_admin_can_read(self, admin_user):
        """Test que ADMIN puede leer"""
        permission = WorkOrderPermission()
        request = type('Request', (), {'user': admin_user, 'method': 'GET'})()
        assert permission.has_permission(request, None) is True
    
    @pytest.mark.permission
    def test_admin_can_create(self, admin_user):
        """Test que ADMIN puede crear OT"""
        permission = WorkOrderPermission()
        view = type('View', (), {'action': 'create'})()
        request = type('Request', (), {'user': admin_user, 'method': 'POST'})()
        assert permission.has_permission(request, view) is True
    
    @pytest.mark.permission
    def test_supervisor_can_read(self, supervisor_user):
        """Test que SUPERVISOR puede leer"""
        permission = WorkOrderPermission()
        request = type('Request', (), {'user': supervisor_user, 'method': 'GET'})()
        assert permission.has_permission(request, None) is True
    
    @pytest.mark.permission
    def test_supervisor_cannot_create(self, supervisor_user):
        """Test que SUPERVISOR NO puede crear OT (solo JEFE_TALLER)"""
        permission = WorkOrderPermission()
        view = type('View', (), {'action': 'create'})()
        request = type('Request', (), {'user': supervisor_user, 'method': 'POST'})()
        assert permission.has_permission(request, view) is False
    
    @pytest.mark.permission
    def test_mecanico_can_read(self, mecanico_user):
        """Test que MECANICO puede leer"""
        permission = WorkOrderPermission()
        request = type('Request', (), {'user': mecanico_user, 'method': 'GET'})()
        assert permission.has_permission(request, None) is True
    
    @pytest.mark.permission
    def test_mecanico_cannot_create(self, mecanico_user):
        """Test que MECANICO NO puede crear OT"""
        permission = WorkOrderPermission()
        view = type('View', (), {'action': 'create'})()
        request = type('Request', (), {'user': mecanico_user, 'method': 'POST'})()
        assert permission.has_permission(request, view) is False
    
    @pytest.mark.permission
    def test_guardia_can_read(self, db):
        """Test que GUARDIA puede leer (solo lectura)"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        guardia = User.objects.create_user(
            username="guardia_test",
            email="guardia@test.com",
            password="testpass123",
            rol=User.Rol.GUARDIA,
            is_active=True
        )
        permission = WorkOrderPermission()
        request = type('Request', (), {'user': guardia, 'method': 'GET'})()
        assert permission.has_permission(request, None) is True
    
    @pytest.mark.permission
    def test_guardia_cannot_create(self, db):
        """Test que GUARDIA NO puede crear OT (solo lectura)"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        guardia = User.objects.create_user(
            username="guardia_test",
            email="guardia@test.com",
            password="testpass123",
            rol=User.Rol.GUARDIA,
            is_active=True
        )
        permission = WorkOrderPermission()
        view = type('View', (), {'action': 'create'})()
        request = type('Request', (), {'user': guardia, 'method': 'POST'})()
        assert permission.has_permission(request, view) is False
    
    @pytest.mark.permission
    def test_jefe_taller_can_create(self, db):
        """Test que JEFE_TALLER puede crear OT"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        jefe_taller = User.objects.create_user(
            username="jefe_taller_test",
            email="jefe_taller@test.com",
            password="testpass123",
            rol=User.Rol.JEFE_TALLER,
            is_active=True
        )
        permission = WorkOrderPermission()
        view = type('View', (), {'action': 'create'})()
        request = type('Request', (), {'user': jefe_taller, 'method': 'POST'})()
        assert permission.has_permission(request, view) is True
    
    @pytest.mark.permission
    def test_safe_methods_allowed_for_read_roles(self, supervisor_user):
        """Test que métodos seguros (GET, HEAD, OPTIONS) están permitidos para roles de lectura"""
        permission = WorkOrderPermission()
        for method in ['GET', 'HEAD', 'OPTIONS']:
            request = type('Request', (), {'user': supervisor_user, 'method': method})()
            assert permission.has_permission(request, None) is True
    
    @pytest.mark.permission
    def test_unsafe_methods_require_write_role(self, db):
        """Test que métodos no seguros requieren rol de escritura apropiado"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        guardia = User.objects.create_user(
            username="guardia_test",
            email="guardia@test.com",
            password="testpass123",
            rol=User.Rol.GUARDIA,
            is_active=True
        )
        permission = WorkOrderPermission()
        # POST con action='create' NO está permitido para GUARDIA
        view_create = type('View', (), {'action': 'create'})()
        request_post = type('Request', (), {'user': guardia, 'method': 'POST'})()
        assert permission.has_permission(request_post, view_create) is False
        
        # Otros métodos no seguros no están permitidos para GUARDIA
        view_other = type('View', (), {'action': 'update'})()
        for method in ['PUT', 'PATCH', 'DELETE']:
            request = type('Request', (), {'user': guardia, 'method': method})()
            assert permission.has_permission(request, view_other) is False

    @pytest.mark.permission
    def test_coordinador_zona_can_read(self, db):
        """Test que COORDINADOR_ZONA puede leer"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        coordinador = User.objects.create_user(
            username="coordinador_test",
            email="coordinador@test.com",
            password="testpass123",
            rol=User.Rol.COORDINADOR_ZONA,
            is_active=True
        )
        permission = WorkOrderPermission()
        request = type('Request', (), {'user': coordinador, 'method': 'GET'})()
        assert permission.has_permission(request, None) is True

    @pytest.mark.permission
    def test_coordinador_zona_can_update(self, db, orden_trabajo):
        """Test que COORDINADOR_ZONA puede actualizar OT"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        coordinador = User.objects.create_user(
            username="coordinador_test",
            email="coordinador@test.com",
            password="testpass123",
            rol=User.Rol.COORDINADOR_ZONA,
            is_active=True
        )
        permission = WorkOrderPermission()
        view = type('View', (), {'action': 'update'})()
        request = type('Request', (), {'user': coordinador, 'method': 'PUT'})()
        assert permission.has_permission(request, view) is True
        
        # Verificar también has_object_permission
        assert permission.has_object_permission(request, view, orden_trabajo) is True

    @pytest.mark.permission
    def test_coordinador_zona_cannot_create(self, db):
        """Test que COORDINADOR_ZONA NO puede crear OT"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        coordinador = User.objects.create_user(
            username="coordinador_test",
            email="coordinador@test.com",
            password="testpass123",
            rol=User.Rol.COORDINADOR_ZONA,
            is_active=True
        )
        permission = WorkOrderPermission()
        view = type('View', (), {'action': 'create'})()
        request = type('Request', (), {'user': coordinador, 'method': 'POST'})()
        assert permission.has_permission(request, view) is False

    @pytest.mark.permission
    def test_allowed_roles_update_includes_coordinador_zona(self):
        """Test que ALLOWED_ROLES_UPDATE incluye COORDINADOR_ZONA"""
        assert "COORDINADOR_ZONA" in ALLOWED_ROLES_UPDATE

    @pytest.mark.permission
    def test_allowed_roles_read_includes_coordinador_zona(self):
        """Test que ALLOWED_ROLES_READ incluye COORDINADOR_ZONA"""
        assert "COORDINADOR_ZONA" in ALLOWED_ROLES_READ
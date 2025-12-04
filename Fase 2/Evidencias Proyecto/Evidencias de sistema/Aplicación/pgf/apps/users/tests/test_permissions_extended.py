"""
Tests adicionales para permisos de usuarios.
"""

import pytest
from unittest.mock import Mock
from apps.users.permissions import UserPermission
from apps.users.models import User


@pytest.mark.permission
class TestUserPermission:
    """Tests para UserPermission"""
    
    def test_create_action_allowed_public(self):
        """Test que create está permitido públicamente"""
        permission = UserPermission()
        request = Mock()
        request.user = None
        
        view = Mock()
        view.action = 'create'
        
        assert permission.has_permission(request, view) is True
    
    def test_me_action_requires_auth(self, admin_user):
        """Test que me requiere autenticación"""
        permission = UserPermission()
        request = Mock()
        request.user = admin_user
        # is_authenticated es una propiedad, no necesita ser establecida
        
        view = Mock()
        view.action = 'me'
        
        assert permission.has_permission(request, view) is True
    
    def test_me_action_denied_unauthenticated(self):
        """Test que me es denegado sin autenticación"""
        permission = UserPermission()
        request = Mock()
        request.user = None
        
        view = Mock()
        view.action = 'me'
        
        assert permission.has_permission(request, view) is False
    
    def test_list_allowed_for_admin(self, admin_user):
        """Test que list está permitido para ADMIN"""
        permission = UserPermission()
        request = Mock()
        request.user = admin_user
        # is_authenticated es una propiedad
        request.user.rol = "ADMIN"
        
        view = Mock()
        view.action = 'list'
        
        assert permission.has_permission(request, view) is True
    
    def test_list_allowed_for_supervisor(self, supervisor_user):
        """Test que list está permitido para SUPERVISOR"""
        permission = UserPermission()
        request = Mock()
        request.user = supervisor_user
        # is_authenticated es una propiedad
        request.user.rol = "SUPERVISOR"
        
        view = Mock()
        view.action = 'list'
        
        assert permission.has_permission(request, view) is True
    
    def test_list_denied_for_mecanico(self, mecanico_user):
        """Test que list es denegado para MECANICO"""
        permission = UserPermission()
        request = Mock()
        request.user = mecanico_user
        # is_authenticated es una propiedad
        request.user.rol = "MECANICO"
        
        view = Mock()
        view.action = 'list'
        
        assert permission.has_permission(request, view) is False
    
    def test_other_actions_require_auth(self, admin_user):
        """Test que otras acciones requieren autenticación"""
        permission = UserPermission()
        request = Mock()
        request.user = admin_user
        # is_authenticated es una propiedad
        
        view = Mock()
        view.action = 'retrieve'
        
        assert permission.has_permission(request, view) is True
    
    def test_has_object_permission_admin_user(self, admin_user, db):
        """Test que admin puede ver/editar usuario admin"""
        permission = UserPermission()
        admin_obj = User.objects.create_user(
            username="admin",
            password="TestPass123!",
            rol="ADMIN"
        )
        
        request = Mock()
        request.user = admin_user
        # is_authenticated es una propiedad
        request.user.username = "admin"
        request.user.rol = "ADMIN"
        
        view = Mock()
        view.action = 'retrieve'
        
        assert permission.has_object_permission(request, view, admin_obj) is True
    
    def test_has_object_permission_denied_admin_user(self, mecanico_user, db):
        """Test que usuario normal no puede ver/editar admin"""
        permission = UserPermission()
        admin_obj = User.objects.create_user(
            username="admin",
            password="TestPass123!",
            rol="ADMIN"
        )
        
        request = Mock()
        request.user = mecanico_user
        # is_authenticated es una propiedad
        request.user.rol = "MECANICO"
        
        view = Mock()
        view.action = 'retrieve'
        
        assert permission.has_object_permission(request, view, admin_obj) is False
    
    def test_has_object_permission_permanent_user_cannot_delete(self, admin_user, db):
        """Test que usuario permanente no puede ser eliminado"""
        permission = UserPermission()
        permanent_user = User.objects.create_user(
            username="permanent",
            password="TestPass123!",
            rol="ADMIN",
            is_permanent=True
        )
        
        request = Mock()
        request.user = admin_user
        # is_authenticated es una propiedad
        request.user.rol = "ADMIN"
        
        view = Mock()
        view.action = 'destroy'
        
        assert permission.has_object_permission(request, view, permanent_user) is False
    
    def test_has_object_permission_user_can_view_self(self, mecanico_user):
        """Test que usuario puede ver su propio perfil"""
        permission = UserPermission()
        
        request = Mock()
        request.user = mecanico_user
        # is_authenticated es una propiedad
        
        view = Mock()
        view.action = 'retrieve'
        
        assert permission.has_object_permission(request, view, mecanico_user) is True
    
    def test_has_object_permission_user_can_edit_self(self, mecanico_user):
        """Test que usuario puede editar su propio perfil"""
        permission = UserPermission()
        
        request = Mock()
        request.user = mecanico_user
        # is_authenticated es una propiedad
        
        view = Mock()
        view.action = 'update'
        
        assert permission.has_object_permission(request, view, mecanico_user) is True
    
    def test_has_object_permission_user_cannot_view_others(self, mecanico_user, supervisor_user):
        """Test que usuario no puede ver otros usuarios"""
        permission = UserPermission()
        
        request = Mock()
        request.user = mecanico_user
        # is_authenticated es una propiedad
        request.user.rol = "MECANICO"
        
        view = Mock()
        view.action = 'retrieve'
        
        assert permission.has_object_permission(request, view, supervisor_user) is False
    
    def test_has_object_permission_supervisor_can_view_any(self, supervisor_user, mecanico_user):
        """Test que supervisor puede ver cualquier usuario"""
        permission = UserPermission()
        
        request = Mock()
        request.user = supervisor_user
        # is_authenticated es una propiedad
        request.user.rol = "SUPERVISOR"
        
        view = Mock()
        view.action = 'retrieve'
        
        assert permission.has_object_permission(request, view, mecanico_user) is True


"""
Tests para el sistema de permisos de usuarios.
"""
import pytest
from django.contrib.auth import get_user_model
from apps.users.permissions import UserPermission
from rest_framework.test import APIRequestFactory
from unittest.mock import Mock

User = get_user_model()


class MockView:
    """Mock view para tests de permisos"""
    action = 'list'


class MockViewRetrieve:
    """Mock view para tests de permisos con retrieve"""
    action = 'retrieve'


class TestUserPermission:
    """Tests para UserPermission"""

    @pytest.mark.django_db
    def test_admin_puede_ver_todos_los_usuarios(self):
        """Test que admin puede ver todos los usuarios"""
        factory = APIRequestFactory()
        request = factory.get('/api/v1/users/')
        
        # Crear usuario admin
        admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='test123',
            rol='ADMIN'
        )
        request.user = admin_user
        
        permission = UserPermission()
        view = MockView()
        assert permission.has_permission(request, view) is True

    @pytest.mark.django_db
    def test_supervisor_puede_ver_usuarios(self):
        """Test que supervisor puede ver usuarios"""
        factory = APIRequestFactory()
        request = factory.get('/api/v1/users/')
        
        supervisor = User.objects.create_user(
            username='supervisor_test',
            email='supervisor@test.com',
            password='test123',
            rol='SUPERVISOR'
        )
        request.user = supervisor
        
        permission = UserPermission()
        view = MockView()
        assert permission.has_permission(request, view) is True

    @pytest.mark.django_db
    def test_usuario_normal_no_puede_ver_lista_usuarios(self):
        """Test que usuario normal no puede ver lista de usuarios"""
        factory = APIRequestFactory()
        request = factory.get('/api/v1/users/')
        
        normal_user = User.objects.create_user(
            username='normal_test',
            email='normal@test.com',
            password='test123',
            rol='MECANICO'
        )
        request.user = normal_user
        
        permission = UserPermission()
        view = MockView()
        assert permission.has_permission(request, view) is False

    @pytest.mark.django_db
    def test_usuario_puede_ver_su_propio_perfil(self):
        """Test que usuario puede ver su propio perfil"""
        factory = APIRequestFactory()
        
        user = User.objects.create_user(
            username='self_test',
            email='self@test.com',
            password='test123',
            rol='MECANICO'
        )
        
        request = factory.get(f'/api/v1/users/{user.id}/')
        request.user = user
        
        permission = UserPermission()
        view = MockViewRetrieve()
        assert permission.has_object_permission(request, view, user) is True

    @pytest.mark.django_db
    def test_admin_no_puede_ver_usuario_admin(self):
        """Test que admin no puede ver el usuario 'admin' principal"""
        factory = APIRequestFactory()
        
        # Crear usuario admin (no el principal)
        admin_user = User.objects.create_user(
            username='admin_other',
            email='admin_other@test.com',
            password='test123',
            rol='ADMIN'
        )
        
        # Crear usuario 'admin' principal
        main_admin = User.objects.create_user(
            username='admin',
            email='main@test.com',
            password='test123',
            rol='ADMIN'
        )
        
        request = factory.get(f'/api/v1/users/{main_admin.id}/')
        request.user = admin_user
        
        permission = UserPermission()
        view = MockViewRetrieve()
        # admin_other no puede ver al usuario 'admin' principal
        assert permission.has_object_permission(request, view, main_admin) is False

    @pytest.mark.django_db
    def test_solo_admin_principal_puede_ver_admin(self):
        """Test que solo el usuario 'admin' puede verse a sí mismo"""
        factory = APIRequestFactory()
        
        main_admin = User.objects.create_user(
            username='admin',
            email='main@test.com',
            password='test123',
            rol='ADMIN'
        )
        
        request = factory.get(f'/api/v1/users/{main_admin.id}/')
        request.user = main_admin
        
        permission = UserPermission()
        view = MockViewRetrieve()
        assert permission.has_object_permission(request, view, main_admin) is True


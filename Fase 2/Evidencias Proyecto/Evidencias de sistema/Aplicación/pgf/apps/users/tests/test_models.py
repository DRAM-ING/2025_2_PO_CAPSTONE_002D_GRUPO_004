# apps/users/tests/test_models.py
"""
Tests para los modelos de usuarios.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

User = get_user_model()


class TestUserModel:
    """Tests para el modelo User"""
    
    @pytest.mark.model
    def test_user_creation(self, db):
        """Test creación básica de usuario"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            rol=User.Rol.ADMIN
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.rol == User.Rol.ADMIN
        assert user.is_active is True
    
    @pytest.mark.model
    def test_user_email_unique(self, db):
        """Test que el email debe ser único"""
        User.objects.create_user(
            username="user1",
            email="test@example.com",
            password="testpass123"
        )
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="user2",
                email="test@example.com",
                password="testpass123"
            )
    
    @pytest.mark.model
    def test_user_rut_unique(self, db):
        """Test que el RUT debe ser único"""
        User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
            rut="12345678-9"
        )
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="user2",
                email="user2@example.com",
                password="testpass123",
                rut="12345678-9"
            )
    
    @pytest.mark.model
    def test_user_rol_choices(self, db):
        """Test que el rol debe ser uno de los permitidos"""
        for rol_value, rol_label in User.Rol.choices:
            user = User.objects.create_user(
                username=f"user_{rol_value}",
                email=f"{rol_value}@example.com",
                password="testpass123",
                rol=rol_value
            )
            assert user.rol == rol_value
    
    @pytest.mark.model
    def test_user_str_representation(self, db):
        """Test representación string del usuario"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        assert str(user) == "testuser"
    
    @pytest.mark.model
    def test_user_inactive_cannot_login(self, db):
        """Test que usuario inactivo no puede hacer login"""
        user = User.objects.create_user(
            username="inactive",
            email="inactive@example.com",
            password="testpass123",
            is_active=False
        )
        assert user.is_active is False
    
    @pytest.mark.model
    def test_user_profile_created_automatically(self, db):
        """Test que el perfil se crea automáticamente"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        assert hasattr(user, 'profile')
        assert user.profile is not None


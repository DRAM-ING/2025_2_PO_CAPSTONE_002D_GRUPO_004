# apps/users/tests/test_serializers.py
"""
Tests para los serializers de usuarios.
"""

import pytest
from django.contrib.auth import get_user_model
from apps.users.serializers import UserSerializer
from apps.core.validators import validar_rut_chileno, validar_formato_correo, validar_rol

User = get_user_model()


class TestUserSerializer:
    """Tests para UserSerializer"""
    
    @pytest.mark.serializer
    def test_user_serializer_creation(self, db):
        """Test creación de usuario a través del serializer"""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",  # Contraseña que cumple requisitos: mayúscula, minúscula, número y carácter especial
            "rol": "ADMIN",
            "rut": "12345678-5"  # RUT válido
        }
        serializer = UserSerializer(data=data)
        assert serializer.is_valid() is True
        
        user = serializer.save()
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.rol == "ADMIN"
    
    @pytest.mark.serializer
    def test_user_serializer_email_validation(self, db):
        """Test validación de email único"""
        # Crear usuario existente
        User.objects.create_user(
            username="existing",
            email="existing@example.com",
            password="testpass123"
        )
        
        # Intentar crear otro con mismo email
        data = {
            "username": "newuser",
            "email": "existing@example.com",
            "password": "testpass123",
            "rol": "ADMIN"
        }
        serializer = UserSerializer(data=data)
        assert serializer.is_valid() is False
        assert "email" in serializer.errors
    
    @pytest.mark.serializer
    def test_user_serializer_rut_validation(self, db):
        """Test validación de RUT"""
        # RUT inválido
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "rol": "ADMIN",
            "rut": "12345678-0"  # Dígito verificador incorrecto
        }
        serializer = UserSerializer(data=data)
        assert serializer.is_valid() is False
        assert "rut" in serializer.errors
    
    @pytest.mark.serializer
    def test_user_serializer_rut_unique(self, db):
        """Test que el RUT debe ser único"""
        User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
            rut="12345678-5"  # RUT válido
        )
        
        data = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "testpass123",
            "rol": "ADMIN",
            "rut": "12345678-5"  # RUT duplicado
        }
        serializer = UserSerializer(data=data)
        assert serializer.is_valid() is False
        assert "rut" in serializer.errors
    
    @pytest.mark.serializer
    def test_user_serializer_rol_validation(self, db):
        """Test validación de rol"""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "rol": "ROL_INEXISTENTE"
        }
        serializer = UserSerializer(data=data)
        assert serializer.is_valid() is False
        assert "rol" in serializer.errors
    
    @pytest.mark.serializer
    def test_user_serializer_update(self, db, admin_user):
        """Test actualización de usuario"""
        data = {
            "email": "updated@example.com",
            "rol": "SUPERVISOR"
        }
        serializer = UserSerializer(admin_user, data=data, partial=True)
        assert serializer.is_valid() is True
        
        updated_user = serializer.save()
        assert updated_user.email == "updated@example.com"
        assert updated_user.rol == "SUPERVISOR"


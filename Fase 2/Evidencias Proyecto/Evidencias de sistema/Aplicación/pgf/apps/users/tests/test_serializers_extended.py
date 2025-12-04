"""
Tests adicionales para serializers de users.
"""

import pytest
from apps.users.serializers import UserSerializer, UsuarioListSerializer
from apps.users.models import User


@pytest.mark.serializer
class TestUserSerializerExtended:
    """Tests adicionales para UserSerializer"""
    
    def test_user_serializer_password_validation(self, db):
        """Test validación de complejidad de contraseña"""
        serializer = UserSerializer(data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'weak',  # Contraseña débil
            'rol': 'MECANICO'
        })
        
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
    
    def test_user_serializer_password_hashing(self, db):
        """Test que la contraseña se hashea al crear"""
        serializer = UserSerializer(data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'rol': 'MECANICO'
        })
        
        assert serializer.is_valid()
        user = serializer.save()
        assert user.password != 'TestPass123!'  # Debe estar hasheada
        assert user.check_password('TestPass123!')  # Pero debe verificar correctamente
    
    def test_user_list_serializer_excludes_password(self, admin_user):
        """Test que UsuarioListSerializer no incluye password"""
        serializer = UsuarioListSerializer(admin_user)
        
        assert 'password' not in serializer.data
    
    def test_user_serializer_update_password(self, admin_user):
        """Test actualización de contraseña"""
        serializer = UserSerializer(admin_user, data={
            'username': admin_user.username,
            'email': admin_user.email,
            'password': 'NewPass123!',
            'rol': admin_user.rol
        }, partial=True)
        
        assert serializer.is_valid()
        user = serializer.save()
        assert user.check_password('NewPass123!')


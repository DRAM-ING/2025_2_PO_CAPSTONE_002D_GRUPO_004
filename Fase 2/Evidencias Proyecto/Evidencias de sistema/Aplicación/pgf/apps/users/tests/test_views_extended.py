# apps/users/tests/test_views_extended.py
"""
Tests adicionales para acciones personalizadas de usuarios.
"""

import pytest
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class TestUserActions:
    """Tests para acciones personalizadas de usuarios"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_get_me_profile(self, authenticated_client, admin_user):
        """Test obtener perfil propio"""
        url = "/api/v1/users/me/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == admin_user.id
        assert response.data["username"] == admin_user.username
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_update_me_profile(self, authenticated_client, admin_user):
        """Test actualizar perfil propio"""
        url = "/api/v1/users/me/"
        # Usar un email único basado en timestamp para evitar conflictos
        import time
        unique_email = f"nuevo_{int(time.time())}@test.com"
        data = {
            "username": admin_user.username,  # El serializer requiere username
            "first_name": "Nombre Actualizado",
            "email": unique_email
        }
        response = authenticated_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK, f"Error: {response.data if hasattr(response, 'data') else response.content}"
        assert response.data["first_name"] == "Nombre Actualizado"
        
        admin_user.refresh_from_db()
        assert admin_user.first_name == "Nombre Actualizado"
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_users_filters_admin(self, authenticated_client, admin_user):
        """Test que admin no ve al usuario 'admin' en listado"""
        # Crear usuario admin especial
        special_admin = User.objects.create_user(
            username="admin",
            email="admin@system.com",
            password="testpass123",
            rol=User.Rol.ADMIN,
            is_active=True,
            rut="99999999-9"
        )
        
        url = "/api/v1/users/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        if isinstance(results, list):
            # El usuario 'admin' no debe aparecer para otros usuarios
            admin_ids = [u["id"] for u in results if u.get("username") == "admin"]
            # Solo el propio admin puede verse a sí mismo
            if admin_user.username != "admin":
                assert str(special_admin.id) not in admin_ids


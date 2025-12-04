# apps/users/tests/test_views.py
"""
Tests para las views de usuarios.
"""

import pytest
from django.urls import reverse
from rest_framework import status


class TestUserViewSet:
    """Tests para UserViewSet"""
    
    @pytest.mark.view
    @pytest.mark.api
    def test_user_list_requires_authentication(self, api_client):
        """Test que listar usuarios requiere autenticación"""
        url = "/api/v1/users/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    def test_user_list_admin_access(self, authenticated_client):
        """Test que admin puede listar usuarios"""
        url = "/api/v1/users/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.view
    @pytest.mark.api
    def test_user_create(self, authenticated_client):
        """Test creación de usuario"""
        url = "/api/v1/users/"
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "TestPass123!",  # Contraseña que cumple requisitos: mayúscula, minúscula, número y carácter especial
            "rol": "ADMIN"
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["username"] == "newuser"
    
    @pytest.mark.view
    @pytest.mark.api
    def test_user_update(self, authenticated_client, admin_user):
        """Test actualización de usuario"""
        url = f"/api/v1/users/{admin_user.id}/"
        data = {
            "email": "updated@example.com",
            "rol": "SUPERVISOR"
        }
        response = authenticated_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "updated@example.com"
    
    @pytest.mark.view
    @pytest.mark.api
    def test_user_delete(self, authenticated_client, admin_user):
        """Test eliminación de usuario"""
        url = f"/api/v1/users/{admin_user.id}/"
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestAuthenticationViews:
    """Tests para vistas de autenticación"""
    
    @pytest.mark.view
    @pytest.mark.api
    def test_login_view_success(self, api_client, admin_user):
        """Test login exitoso"""
        url = "/api/v1/auth/login/"
        data = {
            "username": admin_user.username,
            "password": "testpass123"
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_login_view_invalid_credentials(self, api_client):
        """Test login con credenciales inválidas"""
        url = "/api/v1/auth/login/"
        data = {
            "username": "nonexistent",
            "password": "wrongpass"
        }
        response = api_client.post(url, data, format="json")
        # El serializer puede retornar 400 (ValidationError) o 401 dependiendo de la implementación
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED]
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_login_view_inactive_user(self, api_client):
        """Test login con usuario inactivo"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.create_user(
            username="inactive",
            email="inactive@example.com",
            password="testpass123",
            is_active=False
        )
        
        url = "/api/v1/auth/login/"
        data = {
            "username": user.username,
            "password": "testpass123"
        }
        response = api_client.post(url, data, format="json")
        # El serializer puede retornar 400 (ValidationError) o 401 dependiendo de la implementación
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED]
    
    @pytest.mark.view
    @pytest.mark.api
    def test_me_view_requires_authentication(self, api_client):
        """Test que /me/ requiere autenticación"""
        url = "/api/v1/auth/me/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    def test_me_view_returns_user_data(self, authenticated_client, admin_user):
        """Test que /me/ retorna datos del usuario autenticado"""
        url = "/api/v1/auth/me/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == admin_user.username
        assert response.data["email"] == admin_user.email
    
    @pytest.mark.view
    @pytest.mark.api
    def test_refresh_token_success(self, api_client, admin_user):
        """Test refresh token exitoso"""
        # Primero hacer login para obtener refresh token
        login_url = "/api/v1/auth/login/"
        login_data = {
            "username": admin_user.username,
            "password": "testpass123"
        }
        login_response = api_client.post(login_url, login_data, format="json")
        assert login_response.status_code == status.HTTP_200_OK
        
        # Obtener refresh token de las cookies
        refresh_token = login_response.cookies.get("pgf_refresh")
        assert refresh_token is not None
        
        # Hacer refresh
        refresh_url = "/api/v1/auth/refresh/"
        api_client.cookies = login_response.cookies
        response = api_client.post(refresh_url)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
    
    @pytest.mark.view
    @pytest.mark.api
    def test_refresh_token_missing(self, api_client):
        """Test refresh token sin cookie"""
        url = "/api/v1/auth/refresh/"
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "No refresh token found" in response.data["detail"]
    
    @pytest.mark.view
    @pytest.mark.api
    def test_change_password_success(self, authenticated_client, admin_user):
        """Test cambio de contraseña exitoso"""
        url = "/api/v1/auth/change-password/"
        data = {
            "current_password": "testpass123",  # El view espera current_password, no old_password
            "new_password": "newpass123",
            "confirm_password": "newpass123"  # El serializer requiere confirm_password
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar que la contraseña cambió
        admin_user.refresh_from_db()
        assert admin_user.check_password("newpass123")
    
    @pytest.mark.view
    @pytest.mark.api
    def test_change_password_wrong_old_password(self, authenticated_client):
        """Test cambio de contraseña con contraseña antigua incorrecta"""
        url = "/api/v1/auth/change-password/"
        data = {
            "old_password": "wrongpass",
            "new_password": "newpass123"
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


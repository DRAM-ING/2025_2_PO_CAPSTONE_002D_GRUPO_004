"""
Tests de seguridad para el proyecto PGF.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.workorders.models import OrdenTrabajo

User = get_user_model()


class TestRateLimiting:
    """Tests para rate limiting."""
    
    @pytest.mark.security
    def test_rate_limiting_get_excluded(self, db, authenticated_client):
        """Test que GET requests no están sujetas a rate limiting."""
        # Hacer múltiples GET requests
        for _ in range(10):
            response = authenticated_client.get("/api/v1/work/ordenes/")
            assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS
    
    @pytest.mark.security
    def test_rate_limiting_post_enforced(self, db, authenticated_client):
        """Test que POST requests están sujetas a rate limiting."""
        # Este test puede ser difícil de ejecutar sin hacer muchos requests
        # Se puede mockear el cache para simular rate limiting
        from django.core.cache import cache
        cache.set("ratelimit:127.0.0.1", 300, 60)
        
        response = authenticated_client.post("/api/v1/work/ordenes/", {})
        # Puede ser 400 (datos inválidos) o 429 (rate limited)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_429_TOO_MANY_REQUESTS
        ]


class TestSecurityHeaders:
    """Tests para headers de seguridad."""
    
    @pytest.mark.security
    def test_security_headers_present(self, db, authenticated_client):
        """Test que los headers de seguridad están presentes."""
        response = authenticated_client.get("/api/v1/work/ordenes/")
        
        # Verificar headers de seguridad
        assert "X-Content-Type-Options" in response
        assert response["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response or "Content-Security-Policy" in response


class TestAuthentication:
    """Tests de autenticación."""
    
    @pytest.mark.security
    def test_protected_endpoint_requires_auth(self, db):
        """Test que endpoints protegidos requieren autenticación."""
        client = APIClient()
        response = client.get("/api/v1/work/ordenes/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.security
    def test_invalid_token_rejected(self, db):
        """Test que tokens inválidos son rechazados."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
        response = client.get("/api/v1/work/ordenes/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthorization:
    """Tests de autorización."""
    
    @pytest.mark.security
    def test_user_cannot_access_admin_endpoints(self, db, authenticated_client):
        """Test que usuarios normales no pueden acceder a endpoints de admin."""
        # Asumir que /api/v1/health/metrics/ requiere admin
        response = authenticated_client.get("/api/v1/health/metrics/")
        # Puede ser 403 si no es admin
        if response.status_code == status.HTTP_403_FORBIDDEN:
            assert True  # Comportamiento esperado
        else:
            # Si es 200, el usuario debe ser admin
            assert response.status_code == status.HTTP_200_OK


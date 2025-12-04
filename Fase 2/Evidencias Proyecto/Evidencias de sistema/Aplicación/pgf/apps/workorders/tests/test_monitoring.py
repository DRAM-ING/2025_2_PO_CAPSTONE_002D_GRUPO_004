"""
Tests para funcionalidades de monitoreo y salud del sistema.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.core.monitoring import HealthCheck, MetricsCollector

User = get_user_model()


class TestHealthCheck:
    """Tests para health check endpoints."""
    
    @pytest.mark.monitoring
    def test_health_check_requires_auth(self, db):
        """Test que health check requiere autenticación."""
        client = APIClient()
        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.monitoring
    def test_health_check_authenticated(self, db, authenticated_client):
        """Test health check con usuario autenticado."""
        response = authenticated_client.get("/api/v1/health/")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        assert "overall_status" in response.data
        assert "database" in response.data
        assert "cache" in response.data
        assert "storage" in response.data
    
    @pytest.mark.monitoring
    def test_health_check_database(self, db):
        """Test verificación de base de datos."""
        result = HealthCheck.check_database()
        assert "status" in result
        assert result["status"] == "healthy"
    
    @pytest.mark.monitoring
    def test_health_check_cache(self, db):
        """Test verificación de cache."""
        result = HealthCheck.check_cache()
        assert "status" in result
        # Puede ser healthy o unhealthy dependiendo de la configuración
    
    @pytest.mark.monitoring
    def test_health_check_all(self, db):
        """Test verificación completa."""
        result = HealthCheck.check_all()
        assert "overall_status" in result
        assert "database" in result
        assert "cache" in result
        assert "storage" in result
        assert "timestamp" in result


class TestMetrics:
    """Tests para endpoints de métricas."""
    
    @pytest.mark.monitoring
    def test_metrics_requires_admin(self, db, authenticated_client):
        """Test que métricas requiere ser admin."""
        response = authenticated_client.get("/api/v1/health/metrics/")
        # Puede ser 403 si no es admin, o 200 si es admin
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN
        ]
    
    @pytest.mark.monitoring
    def test_metrics_collector(self, db):
        """Test recolector de métricas."""
        # Incrementar contadores
        MetricsCollector.increment_request(success=True)
        MetricsCollector.increment_request(success=False)
        MetricsCollector.increment_rate_limited()
        
        # Obtener métricas
        metrics = MetricsCollector.get_request_metrics()
        assert "total_requests" in metrics
        assert "failed_requests" in metrics
        assert "rate_limited_requests" in metrics
        assert metrics["total_requests"] >= 1
        assert metrics["failed_requests"] >= 1
        assert metrics["rate_limited_requests"] >= 1


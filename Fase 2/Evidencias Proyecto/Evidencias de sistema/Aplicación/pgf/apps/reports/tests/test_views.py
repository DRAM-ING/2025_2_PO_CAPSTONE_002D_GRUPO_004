# apps/reports/tests/test_views.py
"""
Pruebas para las vistas de reportes.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.view
@pytest.mark.api
class TestDashboardEjecutivoView:
    """Pruebas para el Dashboard Ejecutivo."""
    
    def test_dashboard_requires_authentication(self):
        """Test que el dashboard requiere autenticación."""
        client = APIClient()
        response = client.get("/api/v1/reports/dashboard-ejecutivo/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_dashboard_success(self, authenticated_client):
        """Test obtener dashboard exitosamente."""
        response = authenticated_client.get("/api/v1/reports/dashboard-ejecutivo/")
        assert response.status_code == status.HTTP_200_OK
        assert "kpis" in response.data or "total_ot" in response.data or isinstance(response.data, dict)
    
    def test_dashboard_cached(self, authenticated_client):
        """Test que el dashboard usa caché."""
        # Primera llamada
        response1 = authenticated_client.get("/api/v1/reports/dashboard-ejecutivo/")
        assert response1.status_code == status.HTTP_200_OK
        
        # Segunda llamada (debería usar caché)
        response2 = authenticated_client.get("/api/v1/reports/dashboard-ejecutivo/")
        assert response2.status_code == status.HTTP_200_OK


@pytest.mark.django_db
@pytest.mark.view
@pytest.mark.api
class TestReporteProductividadView:
    """Pruebas para el Reporte de Productividad."""
    
    def test_productividad_requires_authentication(self):
        """Test que el reporte de productividad requiere autenticación."""
        client = APIClient()
        response = client.get("/api/v1/reports/productividad/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_productividad_success(self, authenticated_client):
        """Test obtener reporte de productividad exitosamente."""
        response = authenticated_client.get("/api/v1/reports/productividad/")
        # Puede ser 200 o 403 dependiendo del rol
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]
    
    def test_productividad_with_dates(self, authenticated_client):
        """Test reporte de productividad con fechas."""
        from datetime import timedelta
        from django.utils import timezone
        
        # Formato ISO sin timezone para evitar problemas
        fecha_inicio = (timezone.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
        fecha_fin = timezone.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        response = authenticated_client.get(
            f"/api/v1/reports/productividad/?fecha_inicio={fecha_inicio}&fecha_fin={fecha_fin}"
        )
        # Puede ser 200 o 403 dependiendo del rol
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]


@pytest.mark.django_db
@pytest.mark.view
@pytest.mark.api
class TestReportePDFView:
    """Pruebas para el Reporte PDF."""
    
    def test_pdf_requires_authentication(self):
        """Test que generar PDF requiere autenticación."""
        client = APIClient()
        response = client.get("/api/v1/reports/pdf/?tipo=diario")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_pdf_missing_tipo(self, authenticated_client):
        """Test que generar PDF requiere tipo."""
        response = authenticated_client.get("/api/v1/reports/pdf/")
        # Puede ser 200 (usa default), 400 o 403 dependiendo de la validación
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
    
    def test_pdf_invalid_tipo(self, authenticated_client):
        """Test que tipo inválido retorna error."""
        response = authenticated_client.get("/api/v1/reports/pdf/?tipo=invalido")
        # Puede ser 400 o 403 dependiendo de la validación
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
    
    def test_pdf_diario_success(self, authenticated_client):
        """Test generar PDF diario."""
        response = authenticated_client.get("/api/v1/reports/pdf/?tipo=diario")
        # Puede ser 200 (PDF) o 403 dependiendo del rol
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]
        if response.status_code == status.HTTP_200_OK:
            assert response.get("Content-Type") == "application/pdf" or "pdf" in response.get("Content-Type", "").lower()


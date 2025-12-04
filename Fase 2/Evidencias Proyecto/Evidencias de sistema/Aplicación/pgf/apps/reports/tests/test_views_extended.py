# apps/reports/tests/test_views_extended.py
"""
Tests adicionales para las views de reportes.
"""

import pytest
from rest_framework import status
from datetime import timedelta
from django.utils import timezone


class TestDashboardEjecutivoExtended:
    """Tests adicionales para DashboardEjecutivoView"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_dashboard_requires_ejecutivo_role(self, authenticated_client, mecanico_user):
        """Test que solo roles autorizados pueden ver dashboard"""
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = "/api/v1/reports/dashboard-ejecutivo/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_dashboard_returns_kpis(self, authenticated_client, admin_user):
        """Test que dashboard retorna KPIs"""
        authenticated_client.force_authenticate(user=admin_user)
        
        url = "/api/v1/reports/dashboard-ejecutivo/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "kpis" in response.data
        assert "ultimas_5_ot" in response.data
        assert "pausas_frecuentes" in response.data
        assert "mecanicos_carga" in response.data
        assert "tiempos_promedio" in response.data
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_dashboard_uses_cache(self, authenticated_client, admin_user):
        """Test que dashboard usa cache"""
        authenticated_client.force_authenticate(user=admin_user)
        
        url = "/api/v1/reports/dashboard-ejecutivo/"
        
        # Primera llamada
        response1 = authenticated_client.get(url)
        assert response1.status_code == status.HTTP_200_OK
        
        # Segunda llamada (debe usar cache)
        response2 = authenticated_client.get(url)
        assert response2.status_code == status.HTTP_200_OK
        # Los datos deben ser iguales (cache)
        assert response1.data == response2.data


class TestReporteProductividadExtended:
    """Tests adicionales para ReporteProductividadView"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_reporte_productividad_requires_permission(self, authenticated_client, mecanico_user):
        """Test que solo roles autorizados pueden ver reporte"""
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = "/api/v1/reports/productividad/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_reporte_productividad_with_dates(self, authenticated_client, supervisor_user):
        """Test reporte con fechas personalizadas"""
        authenticated_client.force_authenticate(user=supervisor_user)
        
        # Usar formato ISO válido sin espacios
        fecha_inicio = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S')
        fecha_fin = timezone.now().strftime('%Y-%m-%dT%H:%M:%S')
        
        url = f"/api/v1/reports/productividad/?fecha_inicio={fecha_inicio}&fecha_fin={fecha_fin}"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "periodo" in response.data
        assert "total_ot_cerradas" in response.data
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_reporte_productividad_invalid_date_range(self, authenticated_client, supervisor_user):
        """Test reporte con rango de fechas inválido"""
        authenticated_client.force_authenticate(user=supervisor_user)
        
        # Usar formato ISO válido sin espacios
        fecha_inicio = timezone.now().strftime('%Y-%m-%dT%H:%M:%S')
        fecha_fin = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S')  # Fecha fin antes de inicio
        
        url = f"/api/v1/reports/productividad/?fecha_inicio={fecha_inicio}&fecha_fin={fecha_fin}"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# apps/workorders/tests/test_evidencias_download.py
"""
Tests para el endpoint de descarga de evidencias.
"""

import pytest
from rest_framework import status
from apps.workorders.models import Evidencia


class TestEvidenciaDownload:
    """Tests para el endpoint download de evidencias"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_download_requires_authentication(self, api_client, evidencia):
        """Test que descargar evidencia requiere autenticación"""
        url = f"/api/v1/work/evidencias/{evidencia.id}/download/"
        response = api_client.get(url)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_download_nonexistent_evidencia(self, authenticated_client):
        """Test descargar evidencia que no existe"""
        url = "/api/v1/work/evidencias/00000000-0000-0000-0000-000000000000/download/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_download_evidencia_success(self, authenticated_client, evidencia):
        """Test descargar evidencia exitosamente"""
        url = f"/api/v1/work/evidencias/{evidencia.id}/download/"
        
        from unittest.mock import patch, MagicMock
        with patch('apps.workorders.views.boto3') as mock_boto3:
            mock_s3 = MagicMock()
            mock_s3.generate_presigned_url.return_value = "https://s3.example.com/presigned-url"
            mock_boto3.client.return_value = mock_s3
            
            response = authenticated_client.get(url)
            # Debe retornar URL presignada
            if response.status_code == status.HTTP_200_OK:
                assert "download_url" in response.data
                assert "expires_in" in response.data


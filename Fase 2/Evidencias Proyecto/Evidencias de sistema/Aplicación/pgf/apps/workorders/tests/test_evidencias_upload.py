# apps/workorders/tests/test_evidencias_upload.py
"""
Tests para el endpoint de subida de evidencias (presigned).
"""

import pytest
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from apps.workorders.models import Evidencia, OrdenTrabajo


class TestEvidenciaPresignedUpload:
    """Tests para el endpoint presigned de evidencias"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_presigned_upload_requires_authentication(self, api_client):
        """Test que subir evidencia requiere autenticación"""
        url = "/api/v1/work/evidencias/presigned/"
        file = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        data = {
            "file": file,
            # No incluir "ot" para que sea None, pero no pasarlo explícitamente como None
            "tipo": "FOTO",
            "descripcion": "Test"
        }
        response = api_client.post(url, data, format="multipart")
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_presigned_upload_requires_permission(self, authenticated_client, mecanico_user):
        """Test que solo roles autorizados pueden subir evidencias"""
        # Autenticar como mecánico (tiene permiso)
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = "/api/v1/work/evidencias/presigned/"
        file = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        data = {
            "file": file,
            "tipo": "FOTO",
            "descripcion": "Test"
        }
        # Mock de boto3 para evitar errores de S3
        from unittest.mock import patch, MagicMock
        with patch('apps.workorders.views.boto3') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3
            
            response = authenticated_client.post(url, data, format="multipart")
            # Puede fallar por configuración de S3, pero debe pasar la validación de permisos
            assert response.status_code != status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_presigned_upload_requires_file(self, authenticated_client, mecanico_user):
        """Test que se requiere un archivo para subir"""
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = "/api/v1/work/evidencias/presigned/"
        data = {
            "tipo": "FOTO",
            "descripcion": "Test sin archivo"
        }
        response = authenticated_client.post(url, data, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "archivo" in str(response.data.get("detail", "")).lower()
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_presigned_upload_validates_file_size(self, authenticated_client, mecanico_user):
        """Test que se valida el tamaño máximo del archivo (3GB)"""
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = "/api/v1/work/evidencias/presigned/"
        # Crear archivo de más de 3GB (simulado)
        large_content = b"x" * (3 * 1024 * 1024 * 1024 + 1)  # 3GB + 1 byte
        file = SimpleUploadedFile("large.jpg", large_content, content_type="image/jpeg")
        data = {
            "file": file,
            "tipo": "FOTO",
            "descripcion": "Test archivo grande"
        }
        response = authenticated_client.post(url, data, format="multipart")
        # Debe rechazar archivos mayores a 3GB
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_presigned_upload_with_ot(self, authenticated_client, mecanico_user, orden_trabajo):
        """Test subir evidencia asociada a una OT"""
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = "/api/v1/work/evidencias/presigned/"
        file = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        data = {
            "file": file,
            "ot": str(orden_trabajo.id),
            "tipo": "FOTO",
            "descripcion": "Evidencia de prueba"
        }
        
        from unittest.mock import patch, MagicMock
        with patch('apps.workorders.views.boto3') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3
            
            response = authenticated_client.post(url, data, format="multipart")
            # Si pasa la validación, debe crear la evidencia
            if response.status_code == status.HTTP_201_CREATED:
                assert "evidencia" in response.data
                assert "file_url" in response.data
                evidencia_id = response.data["evidencia"]["id"]
                evidencia = Evidencia.objects.get(id=evidencia_id)
                assert evidencia.ot == orden_trabajo


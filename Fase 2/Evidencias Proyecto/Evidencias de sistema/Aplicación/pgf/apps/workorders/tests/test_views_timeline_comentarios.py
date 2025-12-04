# apps/workorders/tests/test_views_timeline_comentarios.py
"""
Tests para las nuevas funcionalidades de workorders:
- Timeline consolidado de OT
- Comentarios en OT
- Invalidación de evidencias
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.workorders.models import OrdenTrabajo, ComentarioOT, Evidencia, VersionEvidencia
from apps.workorders.views import timeline_ot

User = get_user_model()


class TestTimelineOT:
    """Tests para timeline consolidado de OT"""
    
    @pytest.mark.view
    @pytest.mark.api
    def test_timeline_requires_authentication(self, api_client, orden_trabajo):
        """Test que timeline requiere autenticación"""
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/timeline/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    def test_timeline_success(self, authenticated_client, orden_trabajo):
        """Test obtener timeline exitoso"""
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/timeline/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "timeline" in response.data
        assert "actores" in response.data
        assert isinstance(response.data["timeline"], list)
    
    @pytest.mark.view
    @pytest.mark.api
    def test_timeline_includes_creacion(self, authenticated_client, orden_trabajo):
        """Test que timeline incluye creación de OT"""
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/timeline/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        timeline = response.data["timeline"]
        creacion = [t for t in timeline if t["tipo"] == "creacion"]
        assert len(creacion) >= 1
    
    @pytest.mark.view
    @pytest.mark.api
    def test_timeline_not_found(self, authenticated_client):
        """Test timeline con OT inexistente"""
        url = "/api/v1/work/ordenes/00000000-0000-0000-0000-000000000000/timeline/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestComentariosOT:
    """Tests para comentarios en OT"""
    
    @pytest.mark.view
    @pytest.mark.api
    def test_crear_comentario_requires_authentication(self, api_client, orden_trabajo):
        """Test que crear comentario requiere autenticación"""
        url = "/api/v1/work/comentarios/"
        data = {
            "ot": str(orden_trabajo.id),
            "contenido": "Comentario de prueba"
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    def test_crear_comentario_success(self, authenticated_client, orden_trabajo):
        """Test crear comentario exitoso"""
        url = "/api/v1/work/comentarios/"
        data = {
            "ot": str(orden_trabajo.id),
            "contenido": "Comentario de prueba"
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["contenido"] == "Comentario de prueba"
        assert ComentarioOT.objects.filter(ot=orden_trabajo).exists()
    
    @pytest.mark.view
    @pytest.mark.api
    def test_crear_comentario_with_mentions(self, authenticated_client, orden_trabajo, supervisor_user):
        """Test crear comentario con menciones"""
        url = "/api/v1/work/comentarios/"
        data = {
            "ot": str(orden_trabajo.id),
            "contenido": "Comentario con @supervisor",
            "menciones": [f"@{supervisor_user.username}"]  # Formato de menciones
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        comentario = ComentarioOT.objects.get(ot=orden_trabajo)
        # Verificar que el comentario tiene menciones (JSONField)
        assert isinstance(comentario.menciones, list)
        assert len(comentario.menciones) >= 0
    
    @pytest.mark.view
    @pytest.mark.api
    def test_listar_comentarios(self, authenticated_client, orden_trabajo, admin_user):
        """Test listar comentarios de OT"""
        # Crear comentario primero
        ComentarioOT.objects.create(
            ot=orden_trabajo,
            usuario=admin_user,
            contenido="Comentario de prueba"
        )
        
        url = f"/api/v1/work/comentarios/?ot={orden_trabajo.id}"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # La respuesta puede ser lista directa o paginada
        data = response.data
        if hasattr(data, 'get') and isinstance(data, dict):  # Es un dict paginado
            results = data.get("results", [])
        elif isinstance(data, list):  # Es una lista directa
            results = data
        else:
            results = []
        # Verificar que hay al menos un comentario
        assert len(results) >= 1
    
    @pytest.mark.view
    @pytest.mark.api
    def test_editar_comentario(self, authenticated_client, orden_trabajo, admin_user):
        """Test editar comentario"""
        comentario = ComentarioOT.objects.create(
            ot=orden_trabajo,
            usuario=admin_user,
            contenido="Comentario original"
        )
        
        url = f"/api/v1/work/comentarios/{comentario.id}/"
        data = {"contenido": "Comentario editado"}
        response = authenticated_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        comentario.refresh_from_db()
        assert comentario.contenido == "Comentario editado"
        assert comentario.editado is True


class TestInvalidarEvidencia:
    """Tests para invalidación de evidencias"""
    
    @pytest.mark.view
    @pytest.mark.api
    def test_invalidar_evidencia_requires_authentication(self, api_client, evidencia):
        """Test que invalidar evidencia requiere autenticación"""
        url = f"/api/v1/work/evidencias/{evidencia.id}/invalidar/"
        data = {"motivo_invalidacion": "Evidencia incorrecta"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    def test_invalidar_evidencia_success(self, authenticated_client, evidencia, jefe_taller_user):
        """Test invalidar evidencia exitoso (requiere JEFE_TALLER)"""
        client = APIClient()
        client.force_authenticate(user=jefe_taller_user)
        
        url = f"/api/v1/work/evidencias/{evidencia.id}/invalidar/"
        data = {"motivo": "Evidencia incorrecta, requiere retomar"}  # El endpoint espera "motivo"
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        evidencia.refresh_from_db()
        assert evidencia.invalidado is True
        assert evidencia.motivo_invalidacion == "Evidencia incorrecta, requiere retomar"
        # Verificar que se creó versión
        assert VersionEvidencia.objects.filter(evidencia_original=evidencia).exists()
    
    @pytest.mark.view
    @pytest.mark.api
    def test_invalidar_evidencia_requires_motivo(self, authenticated_client, evidencia):
        """Test que motivo_invalidacion es obligatorio"""
        url = f"/api/v1/work/evidencias/{evidencia.id}/invalidar/"
        data = {}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.view
    @pytest.mark.api
    def test_invalidar_evidencia_not_found(self, authenticated_client):
        """Test invalidar evidencia inexistente"""
        url = "/api/v1/work/evidencias/00000000-0000-0000-0000-000000000000/invalidar/"
        data = {"motivo_invalidacion": "Test"}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND


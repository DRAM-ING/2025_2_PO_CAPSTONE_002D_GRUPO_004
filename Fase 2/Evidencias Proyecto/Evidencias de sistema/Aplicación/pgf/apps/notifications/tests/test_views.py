# apps/notifications/tests/test_views.py
"""
Tests para las views de notificaciones.
"""

import pytest
from rest_framework import status
from apps.notifications.models import Notification


@pytest.fixture
def notificacion(db, admin_user):
    """Crea una notificación de prueba"""
    return Notification.objects.create(
        usuario=admin_user,
        titulo="Test Notification",
        mensaje="Mensaje de prueba",
        tipo="OT_CREADA",
        estado="NO_LEIDA"
    )


class TestNotificationViewSet:
    """Tests para NotificationViewSet"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_notifications_requires_authentication(self, api_client):
        """Test que listar notificaciones requiere autenticación"""
        url = "/api/v1/notifications/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_notifications_success(self, authenticated_client, notificacion):
        """Test listar notificaciones exitosamente"""
        url = "/api/v1/notifications/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_marcar_leida_success(self, authenticated_client, notificacion):
        """Test marcar notificación como leída"""
        url = f"/api/v1/notifications/{notificacion.id}/marcar-leida/"
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        notificacion.refresh_from_db()
        assert notificacion.estado == "LEIDA"
        assert notificacion.leida_en is not None
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_marcar_todas_leidas_success(self, authenticated_client, admin_user):
        """Test marcar todas las notificaciones como leídas"""
        # Crear múltiples notificaciones no leídas
        for i in range(3):
            Notification.objects.create(
                usuario=admin_user,
                titulo=f"Notification {i}",
                mensaje=f"Mensaje {i}",
                tipo="OT_CREADA",
                estado="NO_LEIDA"
            )
        
        url = "/api/v1/notifications/marcar-todas-leidas/"
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["marcadas"] == 3
        
        # Verificar que todas están marcadas como leídas
        no_leidas = Notification.objects.filter(usuario=admin_user, estado="NO_LEIDA").count()
        assert no_leidas == 0
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_contador_no_leidas(self, authenticated_client, admin_user):
        """Test obtener contador de notificaciones no leídas"""
        # Crear notificaciones no leídas
        Notification.objects.create(
            usuario=admin_user,
            titulo="Test",
            mensaje="Test",
            tipo="OT_CREADA",
            estado="NO_LEIDA"
        )
        
        url = "/api/v1/notifications/contador/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "no_leidas" in response.data
        assert response.data["no_leidas"] >= 1


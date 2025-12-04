# apps/workorders/tests/test_views_actions.py
"""
Tests para acciones personalizadas de OrdenTrabajoViewSet.
"""

import pytest
from rest_framework import status
from apps.workorders.models import OrdenTrabajo, Checklist, Pausa


class TestOrdenTrabajoActions:
    """Tests para acciones personalizadas de OT"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_diagnostico_requires_jefe_taller(self, authenticated_client, orden_trabajo, mecanico_user):
        """Test que solo JEFE_TALLER puede realizar diagnóstico"""
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/diagnostico/"
        data = {"diagnostico": "Diagnóstico de prueba"}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_diagnostico_success(self, authenticated_client, orden_trabajo, jefe_taller_user):
        """Test realizar diagnóstico exitosamente"""
        authenticated_client.force_authenticate(user=jefe_taller_user)
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/diagnostico/"
        data = {"diagnostico": "Diagnóstico de prueba"}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.estado == "EN_DIAGNOSTICO"
        # Verificar que el diagnóstico se guardó correctamente
        assert orden_trabajo.diagnostico == "Diagnóstico de prueba", f"Diagnóstico actual: '{orden_trabajo.diagnostico}'"
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_aprobar_asignacion_requires_supervisor(self, authenticated_client, orden_trabajo, mecanico_user, supervisor_user):
        """Test que solo SUPERVISOR puede aprobar asignación"""
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/aprobar-asignacion/"
        data = {"mecanico": mecanico_user.id}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_aprobar_asignacion_success(self, authenticated_client, orden_trabajo, jefe_taller_user, mecanico_user):
        """Test aprobar asignación exitosamente"""
        # El endpoint solo permite JEFE_TALLER o ADMIN
        authenticated_client.force_authenticate(user=jefe_taller_user)
        
        # Asegurar que la OT esté en un estado válido
        orden_trabajo.estado = "EN_DIAGNOSTICO"
        orden_trabajo.save()
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/aprobar-asignacion/"
        data = {"mecanico_id": str(mecanico_user.id)}  # El endpoint espera mecanico_id
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK, f"Error: {response.data}"
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.mecanico == mecanico_user
        assert orden_trabajo.estado in ["EN_EJECUCION", "ABIERTA"]
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_en_qa_requires_mecanico(self, authenticated_client, orden_trabajo, supervisor_user):
        """Test que solo MECANICO puede enviar a QA"""
        # Cambiar estado a EN_EJECUCION primero
        orden_trabajo.estado = "EN_EJECUCION"
        orden_trabajo.save()
        
        authenticated_client.force_authenticate(user=supervisor_user)
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/en-qa/"
        response = authenticated_client.post(url, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_en_qa_success(self, authenticated_client, orden_trabajo, mecanico_user):
        """Test enviar a QA exitosamente"""
        # Cambiar estado a EN_EJECUCION primero
        orden_trabajo.estado = "EN_EJECUCION"
        orden_trabajo.mecanico = mecanico_user
        orden_trabajo.save()
        
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/en-qa/"
        response = authenticated_client.post(url, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.estado == "EN_QA"
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_rechazar_qa_requires_supervisor(self, authenticated_client, orden_trabajo, mecanico_user):
        """Test que solo SUPERVISOR/JEFE_TALLER puede rechazar QA"""
        orden_trabajo.estado = "EN_QA"
        orden_trabajo.save()
        
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/rechazar-qa/"
        data = {"observaciones": "Rechazado"}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_rechazar_qa_success(self, authenticated_client, orden_trabajo, supervisor_user):
        """Test rechazar QA exitosamente"""
        orden_trabajo.estado = "EN_QA"
        orden_trabajo.save()
        
        authenticated_client.force_authenticate(user=supervisor_user)
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/rechazar-qa/"
        data = {"observaciones": "Rechazado por calidad"}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.estado == "EN_EJECUCION"
        
        # Verificar que se creó checklist
        checklist = Checklist.objects.filter(ot=orden_trabajo).first()
        assert checklist is not None
        assert checklist.resultado == "NO_OK"
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_cerrar_ot_requires_jefe_taller(self, authenticated_client, orden_trabajo, mecanico_user):
        """Test que solo JEFE_TALLER puede cerrar OT"""
        orden_trabajo.estado = "EN_QA"
        orden_trabajo.save()
        
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/cerrar/"
        data = {
            "diagnostico_final": "Diagnóstico final",
            "fecha_cierre": "2025-01-30T12:00:00Z"
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_cerrar_ot_success(self, authenticated_client, orden_trabajo, jefe_taller_user):
        """Test cerrar OT exitosamente"""
        orden_trabajo.estado = "EN_QA"
        orden_trabajo.save()
        
        authenticated_client.force_authenticate(user=jefe_taller_user)
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/cerrar/"
        data = {
            "diagnostico_final": "Diagnóstico final",
            "fecha_cierre": "2025-01-30T12:00:00Z"
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.estado == "CERRADA"
        # El modelo usa 'diagnostico', no 'diagnostico_final'
        assert orden_trabajo.diagnostico == "Diagnóstico final"
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_en_pausa_requires_mecanico(self, authenticated_client, orden_trabajo, supervisor_user):
        """Test que solo MECANICO puede pausar OT"""
        orden_trabajo.estado = "EN_EJECUCION"
        orden_trabajo.save()
        
        authenticated_client.force_authenticate(user=supervisor_user)
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/en-pausa/"
        data = {"motivo": "Pausa de prueba"}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_en_pausa_success(self, authenticated_client, orden_trabajo, mecanico_user):
        """Test pausar OT exitosamente"""
        orden_trabajo.estado = "EN_EJECUCION"
        orden_trabajo.mecanico = mecanico_user
        orden_trabajo.save()
        
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/en-pausa/"
        # El endpoint en_pausa no acepta data, solo cambia el estado
        response = authenticated_client.post(url, format="json")
        assert response.status_code == status.HTTP_200_OK, f"Error: {response.data}"
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.estado == "EN_PAUSA"
        
        # El endpoint en_pausa solo cambia el estado, no crea una pausa automáticamente
        # Para crear una pausa con motivo, se debe usar el endpoint POST /api/v1/work/pausas/
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_timeline_ot(self, authenticated_client, orden_trabajo):
        """Test obtener timeline de OT"""
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/timeline/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "timeline" in response.data
        assert isinstance(response.data["timeline"], list)
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_ping_endpoint(self, authenticated_client):
        """Test endpoint ping"""
        url = "/api/v1/work/ping/"
        response = authenticated_client.post(url, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["ok"] is True


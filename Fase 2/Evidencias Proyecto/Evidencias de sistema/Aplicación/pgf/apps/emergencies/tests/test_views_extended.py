# apps/emergencies/tests/test_views_extended.py
"""
Tests adicionales para acciones personalizadas de emergencias.
"""

import pytest
from rest_framework import status
from apps.emergencies.models import EmergenciaRuta


class TestEmergenciaActions:
    """Tests para acciones personalizadas de emergencias"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_aprobar_emergencia_requires_permission(self, authenticated_client, emergencia, mecanico_user):
        """Test que solo roles autorizados pueden aprobar"""
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = f"/api/v1/emergencies/{emergencia.id}/aprobar/"
        response = authenticated_client.post(url, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_aprobar_emergencia_success(self, authenticated_client, emergencia, jefe_taller_user):
        """Test aprobar emergencia exitosamente"""
        authenticated_client.force_authenticate(user=jefe_taller_user)
        
        url = f"/api/v1/emergencies/{emergencia.id}/aprobar/"
        response = authenticated_client.post(url, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        emergencia.refresh_from_db()
        assert emergencia.estado == "APROBADA"
        assert emergencia.aprobador == jefe_taller_user
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_asignar_supervisor_success(self, authenticated_client, emergencia, supervisor_user, jefe_taller_user):
        """Test asignar supervisor exitosamente"""
        emergencia.estado = "APROBADA"
        emergencia.aprobador = jefe_taller_user
        emergencia.save()
        
        authenticated_client.force_authenticate(user=supervisor_user)
        
        url = f"/api/v1/emergencies/{emergencia.id}/asignar-supervisor/"
        data = {"supervisor_id": supervisor_user.id}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        emergencia.refresh_from_db()
        assert emergencia.supervisor_asignado == supervisor_user
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_asignar_mecanico_success(self, authenticated_client, emergencia, supervisor_user, mecanico_user):
        """Test asignar mecánico exitosamente"""
        emergencia.estado = "APROBADA"
        emergencia.supervisor_asignado = supervisor_user
        emergencia.save()
        
        authenticated_client.force_authenticate(user=supervisor_user)
        
        url = f"/api/v1/emergencies/{emergencia.id}/asignar-mecanico/"
        data = {"mecanico_id": mecanico_user.id}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        emergencia.refresh_from_db()
        assert emergencia.mecanico_asignado == mecanico_user
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_resolver_emergencia_success(self, authenticated_client, emergencia, mecanico_user):
        """Test resolver emergencia exitosamente"""
        emergencia.estado = "EN_PROCESO"
        emergencia.mecanico_asignado = mecanico_user
        emergencia.save()
        
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = f"/api/v1/emergencies/{emergencia.id}/resolver/"
        data = {"observaciones": "Emergencia resuelta"}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        emergencia.refresh_from_db()
        assert emergencia.estado == "RESUELTA"
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_cerrar_emergencia_success(self, authenticated_client, emergencia, supervisor_user):
        """Test cerrar emergencia exitosamente"""
        emergencia.estado = "RESUELTA"
        emergencia.save()
        
        authenticated_client.force_authenticate(user=supervisor_user)
        
        url = f"/api/v1/emergencies/{emergencia.id}/cerrar/"
        response = authenticated_client.post(url, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        emergencia.refresh_from_db()
        assert emergencia.estado == "CERRADA"
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_rechazar_emergencia_success(self, authenticated_client, emergencia, jefe_taller_user):
        """Test rechazar emergencia exitosamente"""
        authenticated_client.force_authenticate(user=jefe_taller_user)
        
        url = f"/api/v1/emergencies/{emergencia.id}/rechazar/"
        data = {"motivo": "No es emergencia"}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        emergencia.refresh_from_db()
        assert emergencia.estado == "RECHAZADA"


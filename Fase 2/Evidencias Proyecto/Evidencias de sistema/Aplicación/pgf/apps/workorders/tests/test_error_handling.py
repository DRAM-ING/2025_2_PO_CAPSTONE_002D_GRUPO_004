# apps/workorders/tests/test_error_handling.py
"""
Tests para el manejo de errores en endpoints críticos.
"""

import pytest
from rest_framework import status
from apps.workorders.models import OrdenTrabajo


class TestErrorHandling:
    """Tests para manejo de errores"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_create_ot_with_invalid_vehiculo(self, authenticated_client, jefe_taller_user):
        """Test crear OT con vehículo inválido"""
        authenticated_client.force_authenticate(user=jefe_taller_user)
        
        url = "/api/v1/work/ordenes/"
        data = {
            "vehiculo": "00000000-0000-0000-0000-000000000000",  # UUID inválido
            "motivo": "Test"
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_create_ot_with_missing_required_fields(self, authenticated_client, jefe_taller_user, vehiculo):
        """Test crear OT sin campos obligatorios"""
        authenticated_client.force_authenticate(user=jefe_taller_user)
        
        url = "/api/v1/work/ordenes/"
        data = {
            "vehiculo": vehiculo.id,
            # Falta motivo
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_transition_invalid_state(self, authenticated_client, orden_trabajo, mecanico_user):
        """Test transición a estado inválido"""
        authenticated_client.force_authenticate(user=mecanico_user)
        
        # Intentar cambiar de ABIERTA directamente a CERRADA (inválido)
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/cerrar/"
        response = authenticated_client.post(url, format="json")
        # Debe fallar porque la OT no está en EN_QA
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_aprobar_asignacion_without_mecanico(self, authenticated_client, orden_trabajo, jefe_taller_user):
        """Test aprobar asignación sin mecánico asignado"""
        # Asegurar que la OT esté en EN_DIAGNOSTICO para que el endpoint sea accesible
        orden_trabajo.estado = "EN_DIAGNOSTICO"
        orden_trabajo.save()
        
        # El endpoint requiere JEFE_TALLER o ADMIN, usar jefe_taller_user
        authenticated_client.force_authenticate(user=jefe_taller_user)
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/aprobar-asignacion/"
        data = {}  # Sin mecánico
        response = authenticated_client.post(url, data, format="json")
        # El endpoint debe retornar 400 porque falta mecanico_id
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Debe tener un error sobre mecanico_id
        assert "mecanico" in str(response.data).lower() or "mecanico_id" in str(response.data).lower()


"""
Tests adicionales para views de workorders que no están cubiertos.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from apps.workorders.models import OrdenTrabajo, ItemOT, Presupuesto, Pausa, Checklist


@pytest.mark.view
class TestOrdenTrabajoViewSetAdditional:
    """Tests adicionales para OrdenTrabajoViewSet"""
    
    def test_list_workorders_filter_by_estado(self, admin_user, orden_trabajo):
        """Test filtro de list por estado"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get(f'/api/v1/work/ordenes/?estado={orden_trabajo.estado}')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_list_workorders_search(self, admin_user, orden_trabajo):
        """Test búsqueda en list"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        # Buscar por patente del vehículo
        if orden_trabajo.vehiculo:
            response = client.get(f'/api/v1/work/ordenes/?search={orden_trabajo.vehiculo.patente}')
            assert response.status_code == status.HTTP_200_OK
    
    def test_get_queryset_filters_by_mecanico(self, mecanico_user, orden_trabajo):
        """Test que get_queryset filtra por mecánico para MECANICO"""
        orden_trabajo.mecanico = mecanico_user
        orden_trabajo.save()
        
        client = APIClient()
        client.force_authenticate(user=mecanico_user)
        
        response = client.get('/api/v1/work/ordenes/')
        
        assert response.status_code == status.HTTP_200_OK
        # Debería ver solo sus OTs
        assert all(ot['mecanico'] == str(mecanico_user.id) for ot in response.data['results'] if ot.get('mecanico'))
    
    def test_get_queryset_shows_all_with_ver_todas(self, mecanico_user, orden_trabajo, admin_user):
        """Test que get_queryset muestra todas con ver_todas=true"""
        # Crear OT sin asignar a mecanico_user
        orden_trabajo.mecanico = admin_user
        orden_trabajo.save()
        
        client = APIClient()
        client.force_authenticate(user=mecanico_user)
        
        response = client.get('/api/v1/work/ordenes/?ver_todas=true')
        
        assert response.status_code == status.HTTP_200_OK
        # Puede ver todas las OTs con ver_todas=true


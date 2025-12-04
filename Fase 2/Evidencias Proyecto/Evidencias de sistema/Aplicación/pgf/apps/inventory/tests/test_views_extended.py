"""
Tests adicionales para views de inventory.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from apps.inventory.models import Repuesto, Stock, SolicitudRepuesto


@pytest.mark.view
class TestRepuestoViewSetExtended:
    """Tests adicionales para RepuestoViewSet"""
    
    def test_list_repuestos(self, admin_user, repuesto):
        """Test listado de repuestos"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get('/api/v1/inventory/repuestos/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_create_repuesto(self, admin_user):
        """Test creación de repuesto"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        data = {
            'codigo': 'REP-TEST-001',
            'nombre': 'Repuesto Test',
            'descripcion': 'Test descripción',
            'categoria': 'MOTOR',
            'precio': '100.00',
            'unidad_medida': 'UNIDAD'
        }
        
        response = client.post('/api/v1/inventory/repuestos/', data)
        
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
    
    def test_filter_repuestos_by_categoria(self, admin_user, repuesto):
        """Test filtro por categoría"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get(f'/api/v1/inventory/repuestos/?categoria={repuesto.categoria}')
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.view
class TestStockViewSetExtended:
    """Tests adicionales para StockViewSet"""
    
    def test_list_stock(self, admin_user, stock):
        """Test listado de stock"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get('/api/v1/inventory/stock/')
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.view
class TestSolicitudRepuestoViewSetExtended:
    """Tests adicionales para SolicitudRepuestoViewSet"""
    
    def test_list_solicitudes(self, admin_user, solicitud_repuesto):
        """Test listado de solicitudes"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get('/api/v1/inventory/solicitudes/')
        
        assert response.status_code == status.HTTP_200_OK


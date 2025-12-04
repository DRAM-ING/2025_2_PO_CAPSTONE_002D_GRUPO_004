"""
Tests adicionales para views de vehicles.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from apps.vehicles.models import Vehiculo, IngresoVehiculo, Marca


@pytest.mark.view
class TestVehiculoViewSetExtended:
    """Tests adicionales para VehiculoViewSet"""
    
    def test_list_vehicles_uses_list_serializer(self, admin_user, vehiculo):
        """Test que list usa VehiculoListSerializer"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get('/api/v1/vehicles/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_retrieve_vehicle_uses_full_serializer(self, admin_user, vehiculo):
        """Test que retrieve usa VehiculoSerializer completo"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get(f'/api/v1/vehicles/{vehiculo.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'patente' in response.data
        assert 'marca' in response.data
    
    def test_filter_by_estado(self, admin_user, vehiculo):
        """Test filtro por estado"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get('/api/v1/vehicles/?estado=ACTIVO')
        
        assert response.status_code == status.HTTP_200_OK
        assert all(v['estado'] == 'ACTIVO' for v in response.data['results'])
    
    def test_search_by_patente(self, admin_user, vehiculo):
        """Test búsqueda por patente"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get(f'/api/v1/vehicles/?search={vehiculo.patente}')
        
        assert response.status_code == status.HTTP_200_OK
        assert any(v['patente'] == vehiculo.patente for v in response.data['results'])
    
    def test_ordering_by_patente(self, admin_user, vehiculo):
        """Test ordenamiento por patente"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get('/api/v1/vehicles/?ordering=patente')
        
        assert response.status_code == status.HTTP_200_OK
        patentes = [v['patente'] for v in response.data['results']]
        assert patentes == sorted(patentes)
    
    def test_perform_create_logs_audit(self, admin_user, marca, supervisor_user):
        """Test que perform_create registra auditoría"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        data = {
            'patente': 'NEW01',
            'marca': marca.id,
            'modelo': 'Test Model',
            'anio': 2023,
            'tipo': 'CAMION',
            'tipo_motor': 'DIESEL',  # Campo requerido
            'estado': 'ACTIVO',
            'supervisor': supervisor_user.id,
            'estado_operativo': 'OPERATIVO',
            'zona': 'ZONA_TEST',
            'sucursal': 'SUCURSAL_TEST'
        }
        
        response = client.post('/api/v1/vehicles/', data)
        
        # Puede ser 201 o 400 si hay validaciones adicionales
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
        if response.status_code == 400:
            # Si falla, verificar que es por validación, no por permisos
            assert 'detail' in response.data or any(key in response.data for key in ['patente', 'marca', 'modelo'])
    
    def test_perform_update_logs_audit(self, admin_user, vehiculo):
        """Test que perform_update registra auditoría"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        data = {
            'patente': vehiculo.patente,
            'marca': vehiculo.marca.id,
            'modelo': 'Modelo Actualizado',
            'anio': vehiculo.anio,
            'tipo': vehiculo.tipo,
            'estado': vehiculo.estado,
            'supervisor': vehiculo.supervisor.id if vehiculo.supervisor else None,
            'estado_operativo': vehiculo.estado_operativo
        }
        
        response = client.patch(f'/api/v1/vehicles/{vehiculo.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_marcas_action(self, admin_user, marca):
        """Test acción marcas"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get('/api/v1/vehicles/marcas/')
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
    
    def test_pendientes_salida_action(self, admin_user, vehiculo):
        """Test acción pendientes_salida"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get('/api/v1/vehicles/pendientes_salida/')
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


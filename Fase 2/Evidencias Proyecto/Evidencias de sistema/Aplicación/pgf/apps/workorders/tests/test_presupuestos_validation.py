# apps/workorders/tests/test_presupuestos_validation.py
"""
Tests para validaciones de presupuestos.
"""

import pytest
from decimal import Decimal
from rest_framework import status
from apps.workorders.models import Presupuesto, DetallePresup, OrdenTrabajo


class TestPresupuestoValidation:
    """Tests para validaciones de presupuestos"""
    
    @pytest.mark.django_db
    def test_presupuesto_detalles_data_must_be_list(self, orden_trabajo, authenticated_client):
        """Test que detalles_data debe ser una lista"""
        url = '/api/v1/work/presupuestos/'
        data = {
            'ot': str(orden_trabajo.id),
            'detalles_data': 'not_a_list',  # Debe ser lista
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detalles_data' in response.data
    
    @pytest.mark.django_db
    def test_presupuesto_detalles_data_must_not_be_empty(self, orden_trabajo, authenticated_client):
        """Test que detalles_data no puede estar vacío"""
        url = '/api/v1/work/presupuestos/'
        data = {
            'ot': str(orden_trabajo.id),
            'detalles_data': [],  # Lista vacía
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detalles_data' in response.data
    
    @pytest.mark.django_db
    def test_presupuesto_detalle_must_be_dict(self, orden_trabajo, authenticated_client):
        """Test que cada detalle debe ser un diccionario"""
        url = '/api/v1/work/presupuestos/'
        data = {
            'ot': str(orden_trabajo.id),
            'detalles_data': ['not_a_dict'],  # Debe ser diccionario
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detalles_data' in response.data
    
    @pytest.mark.django_db
    def test_presupuesto_detalle_requires_cantidad_and_precio(self, orden_trabajo, authenticated_client):
        """Test que cada detalle debe incluir cantidad y precio"""
        url = '/api/v1/work/presupuestos/'
        data = {
            'ot': str(orden_trabajo.id),
            'detalles_data': [
                {'concepto': 'Repuesto X'}  # Falta cantidad y precio
            ],
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detalles_data' in response.data
    
    @pytest.mark.django_db
    def test_presupuesto_cantidad_must_be_positive(self, orden_trabajo, authenticated_client):
        """Test que cantidad debe ser mayor a 0"""
        url = '/api/v1/work/presupuestos/'
        data = {
            'ot': str(orden_trabajo.id),
            'detalles_data': [
                {
                    'concepto': 'Repuesto X',
                    'cantidad': 0,  # Debe ser > 0
                    'precio': 100.00
                }
            ],
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detalles_data' in response.data
    
    @pytest.mark.django_db
    def test_presupuesto_precio_must_be_non_negative(self, orden_trabajo, authenticated_client):
        """Test que precio debe ser >= 0"""
        url = '/api/v1/work/presupuestos/'
        data = {
            'ot': str(orden_trabajo.id),
            'detalles_data': [
                {
                    'concepto': 'Repuesto X',
                    'cantidad': 2,
                    'precio': -10.00  # Debe ser >= 0
                }
            ],
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detalles_data' in response.data
    
    @pytest.mark.django_db
    def test_presupuesto_invalid_cantidad_type(self, orden_trabajo, authenticated_client):
        """Test que cantidad debe ser un número válido"""
        url = '/api/v1/work/presupuestos/'
        data = {
            'ot': str(orden_trabajo.id),
            'detalles_data': [
                {
                    'concepto': 'Repuesto X',
                    'cantidad': 'not_a_number',  # Debe ser número
                    'precio': 100.00
                }
            ],
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detalles_data' in response.data
    
    @pytest.mark.django_db
    def test_presupuesto_invalid_precio_type(self, orden_trabajo, authenticated_client):
        """Test que precio debe ser un número válido"""
        url = '/api/v1/work/presupuestos/'
        data = {
            'ot': str(orden_trabajo.id),
            'detalles_data': [
                {
                    'concepto': 'Repuesto X',
                    'cantidad': 2,
                    'precio': 'not_a_number'  # Debe ser número
                }
            ],
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detalles_data' in response.data
    
    @pytest.mark.django_db
    def test_presupuesto_valid_data(self, orden_trabajo, authenticated_client):
        """Test que presupuesto válido se crea correctamente"""
        url = '/api/v1/work/presupuestos/'
        data = {
            'ot': str(orden_trabajo.id),
            'detalles_data': [
                {
                    'concepto': 'Repuesto X',
                    'cantidad': 2,
                    'precio': 100.00
                },
                {
                    'concepto': 'Servicio Y',
                    'cantidad': 1,
                    'precio': 50.00
                }
            ],
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        # El serializer puede devolver total como string o Decimal
        total = response.data.get('total')
        if isinstance(total, str):
            total = Decimal(total)
        else:
            total = Decimal(str(total))
        assert total == Decimal('250.00')
        assert len(response.data.get('detalles', [])) == 2


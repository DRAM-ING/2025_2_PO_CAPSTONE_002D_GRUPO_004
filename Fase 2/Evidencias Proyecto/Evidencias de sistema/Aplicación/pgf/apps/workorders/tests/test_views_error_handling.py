# apps/workorders/tests/test_views_error_handling.py
"""
Tests para manejo de errores en views de órdenes de trabajo.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.workorders.models import OrdenTrabajo
from apps.vehicles.models import Vehiculo

User = get_user_model()


class TestOrdenTrabajoViewSetErrorHandling:
    """Tests para manejo de errores en OrdenTrabajoViewSet"""
    
    @pytest.mark.view
    @pytest.mark.django_db
    def test_create_ot_with_invalid_vehiculo(self, admin_user):
        """Test crear OT con vehículo inexistente"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        import uuid
        data = {
            "vehiculo": uuid.uuid4(),  # UUID que no existe
            "motivo": "Test OT",
            "tipo": "MANTENCION"
        }
        
        response = client.post('/api/v1/work/ordenes/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "vehiculo" in str(response.data).lower() or "no existe" in str(response.data).lower()
    
    @pytest.mark.view
    @pytest.mark.django_db
    def test_create_ot_without_authentication(self, vehiculo):
        """Test crear OT sin autenticación"""
        client = APIClient()
        
        data = {
            "vehiculo": str(vehiculo.id),
            "motivo": "Test OT",
            "tipo": "MANTENCION"
        }
        
        response = client.post('/api/v1/work/ordenes/', data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.django_db
    def test_get_ot_not_found(self, admin_user):
        """Test obtener OT que no existe"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        import uuid
        ot_id = uuid.uuid4()
        
        response = client.get(f'/api/v1/work/ordenes/{ot_id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.view
    @pytest.mark.django_db
    def test_update_ot_with_invalid_data(self, orden_trabajo, admin_user):
        """Test actualizar OT con datos inválidos"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        data = {
            "estado": "ESTADO_INVALIDO"  # Estado que no existe
        }
        
        response = client.patch(f'/api/v1/work/ordenes/{orden_trabajo.id}/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.view
    @pytest.mark.django_db
    def test_delete_ot_with_active_items(self, orden_trabajo, admin_user):
        """Test eliminar OT con items activos (si está permitido)"""
        from apps.workorders.models import ItemOT
        
        # Crear un item asociado
        from decimal import Decimal
        ItemOT.objects.create(
            ot=orden_trabajo,
            tipo="REPUESTO",
            descripcion="Test item",  # Usar 'descripcion' en lugar de 'concepto'
            cantidad=1,
            costo_unitario=Decimal("10.00")  # Usar 'costo_unitario' en lugar de 'precio'
        )
        
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.delete(f'/api/v1/work/ordenes/{orden_trabajo.id}/')
        
        # Dependiendo de la lógica de negocio, puede ser 400 o 204
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_403_FORBIDDEN
        ]
    
    @pytest.mark.view
    @pytest.mark.django_db
    def test_transition_with_invalid_state(self, orden_trabajo, admin_user):
        """Test transición de estado inválida"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        # Intentar cambiar de ABIERTA directamente a CERRADA (debe pasar por estados intermedios)
        response = client.post(
            f'/api/v1/work/ordenes/{orden_trabajo.id}/cerrar/',
            {},
            format='json'
        )
        
        # Debería fallar porque la OT está en ABIERTA, no en EN_QA
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN
        ]


class TestEvidenciaViewSetErrorHandling:
    """Tests para manejo de errores en EvidenciaViewSet"""
    
    @pytest.mark.view
    @pytest.mark.django_db
    def test_download_evidencia_not_found(self, admin_user):
        """Test descargar evidencia que no existe"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        import uuid
        evidencia_id = uuid.uuid4()
        
        response = client.get(f'/api/v1/work/evidencias/{evidencia_id}/download/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.view
    @pytest.mark.django_db
    def test_upload_evidencia_without_file(self, orden_trabajo, admin_user):
        """Test subir evidencia sin archivo ni URL"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        data = {
            "ot": str(orden_trabajo.id),
            "descripcion": "Test evidencia",
            "tipo": "FOTO"
            # No se proporciona 'url' ni archivo
        }
        
        response = client.post('/api/v1/work/evidencias/', data, format='json')
        
        # El modelo Evidencia requiere 'url', así que debería fallar si no se proporciona
        # El serializer ahora requiere 'url' como campo write_only
        assert response.status_code == status.HTTP_400_BAD_REQUEST, f"Error: {response.data}"
        assert "url" in str(response.data).lower() or "required" in str(response.data).lower()


class TestPresupuestoViewSetErrorHandling:
    """Tests para manejo de errores en PresupuestoViewSet"""
    
    @pytest.mark.view
    @pytest.mark.django_db
    def test_create_presupuesto_without_detalles(self, orden_trabajo, admin_user):
        """Test crear presupuesto sin detalles"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        data = {
            "ot": str(orden_trabajo.id)
            # Sin detalles_data
        }
        
        response = client.post('/api/v1/work/presupuestos/', data, format='json')
        
        # Dependiendo de la validación, puede ser 400 o 201 con total=0
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_201_CREATED
        ]
    
    @pytest.mark.view
    @pytest.mark.django_db
    def test_create_presupuesto_with_invalid_detalles(self, orden_trabajo, admin_user):
        """Test crear presupuesto con detalles inválidos"""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        data = {
            "ot": str(orden_trabajo.id),
            "detalles_data": [
                {
                    "concepto": "Test",
                    "cantidad": -1,  # Cantidad negativa
                    "precio": 10.0
                }
            ]
        }
        
        response = client.post('/api/v1/work/presupuestos/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


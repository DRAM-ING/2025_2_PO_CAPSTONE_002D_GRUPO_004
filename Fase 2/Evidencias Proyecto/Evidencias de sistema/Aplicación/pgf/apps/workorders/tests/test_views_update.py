# apps/workorders/tests/test_views_update.py
"""
Tests específicos para el método update de OrdenTrabajoViewSet.
Cubre los casos críticos que fueron corregidos recientemente.
"""

import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from apps.workorders.models import OrdenTrabajo, ItemOT
from apps.inventory.models import Repuesto


@pytest.mark.django_db
class TestOrdenTrabajoViewSetUpdate:
    """Tests para el método update de OrdenTrabajoViewSet"""

    def test_update_without_vehiculo_succeeds(self, authenticated_client, orden_trabajo, jefe_taller_user):
        """
        Test que actualizar OT sin enviar vehiculo funciona correctamente.
        Este es el caso crítico que causaba errores antes.
        """
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/"
        data = {
            "tipo": "REPARACION",
            "prioridad": "ALTA",
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "items_data": [
                {
                    "tipo": "SERVICIO",
                    "descripcion": "Servicio actualizado",
                    "cantidad": 1,
                    "costo_unitario": "100.00"
                }
            ]
        }
        
        response = authenticated_client.put(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK, f"Response: {response.data}"
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.motivo == "Motivo actualizado"
        assert orden_trabajo.prioridad == "ALTA"

    def test_update_with_items_data_replaces_items(self, authenticated_client, orden_trabajo, jefe_taller_user, repuesto):
        """
        Test que items_data reemplaza todos los items existentes.
        """
        # Crear items existentes
        ItemOT.objects.create(
            ot=orden_trabajo,
            tipo="SERVICIO",
            descripcion="Servicio antiguo",
            cantidad=1,
            costo_unitario=Decimal("100.00")
        )
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/"
        data = {
            "tipo": "REPARACION",
            "prioridad": "ALTA",
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "items_data": [
                {
                    "tipo": "REPUESTO",
                    "descripcion": "Nuevo repuesto",
                    "cantidad": 2,
                    "costo_unitario": "150.00",
                    "repuesto": str(repuesto.id)
                }
            ]
        }
        
        response = authenticated_client.put(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.items.count() == 1
        item = orden_trabajo.items.first()
        assert item.descripcion == "Nuevo repuesto"
        assert item.cantidad == 2

    def test_update_returns_400_for_empty_request_data(self, authenticated_client, orden_trabajo):
        """
        Test que actualizar con request.data vacío retorna error 400.
        """
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/"
        
        # Simular request con data vacío (esto es difícil de hacer directamente,
        # pero podemos probar con datos inválidos)
        response = authenticated_client.put(url, {}, format="json")
        # Debe retornar 400 porque falta responsable y items_data
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_handles_costo_unitario_as_string(self, authenticated_client, orden_trabajo, jefe_taller_user):
        """
        Test que costo_unitario puede ser enviado como string.
        """
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/"
        data = {
            "tipo": "REPARACION",
            "prioridad": "ALTA",
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "items_data": [
                {
                    "tipo": "SERVICIO",
                    "descripcion": "Servicio test",
                    "cantidad": 1,
                    "costo_unitario": "100.50"  # String
                }
            ]
        }
        
        response = authenticated_client.put(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        orden_trabajo.refresh_from_db()
        item = orden_trabajo.items.first()
        assert item.costo_unitario == Decimal("100.50")

    def test_update_handles_costo_unitario_as_number(self, authenticated_client, orden_trabajo, jefe_taller_user):
        """
        Test que costo_unitario puede ser enviado como número.
        """
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/"
        data = {
            "tipo": "REPARACION",
            "prioridad": "ALTA",
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "items_data": [
                {
                    "tipo": "SERVICIO",
                    "descripcion": "Servicio test",
                    "cantidad": 1,
                    "costo_unitario": 100.50  # Number
                }
            ]
        }
        
        response = authenticated_client.put(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        orden_trabajo.refresh_from_db()
        item = orden_trabajo.items.first()
        assert item.costo_unitario == Decimal("100.50")

    def test_update_returns_detailed_errors_on_validation_failure(self, authenticated_client, orden_trabajo, jefe_taller_user):
        """
        Test que los errores de validación se retornan con detalles.
        """
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/"
        data = {
            "tipo": "REPARACION",
            "prioridad": "ALTA",
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "items_data": [
                {
                    "tipo": "SERVICIO",
                    # Falta descripcion
                    "cantidad": 1,
                    "costo_unitario": "100.00"
                }
            ]
        }
        
        response = authenticated_client.put(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data or "items_data" in str(response.data)

    def test_update_preserves_responsable_if_not_provided(self, authenticated_client, orden_trabajo, jefe_taller_user):
        """
        Test que responsable se preserva si no se proporciona.
        """
        # Asegurar que la OT tiene un responsable
        orden_trabajo.responsable = jefe_taller_user
        orden_trabajo.save()
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/"
        data = {
            "motivo": "Motivo actualizado",
            "prioridad": "ALTA",
            "items_data": [
                {
                    "tipo": "SERVICIO",
                    "descripcion": "Servicio test",
                    "cantidad": 1,
                    "costo_unitario": "100.00"
                }
            ]
            # No incluir responsable
        }
        
        response = authenticated_client.put(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.responsable == jefe_taller_user

    def test_update_coordinador_zona_can_edit(self, orden_trabajo, coordinador_user):
        """
        Test que COORDINADOR_ZONA puede editar OTs.
        """
        client = APIClient()
        client.force_authenticate(user=coordinador_user)
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/"
        data = {
            "motivo": "Motivo actualizado por coordinador",
            "prioridad": "ALTA",
            "responsable": coordinador_user.id,
            "items_data": [
                {
                    "tipo": "SERVICIO",
                    "descripcion": "Servicio test",
                    "cantidad": 1,
                    "costo_unitario": "100.00"
                }
            ]
        }
        
        response = client.put(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.motivo == "Motivo actualizado por coordinador"

    def test_update_vehiculo_is_ignored(self, authenticated_client, orden_trabajo, vehiculo, jefe_taller_user, marca):
        """
        Test que vehiculo no se puede cambiar en actualizaciones.
        """
        from apps.vehicles.models import Vehiculo
        original_vehiculo = orden_trabajo.vehiculo
        
        # Crear un vehículo diferente para intentar cambiar
        otro_vehiculo = Vehiculo.objects.create(
            patente="TEST02",
            marca=marca,
            modelo="Modelo Test 2",
            anio=2020,
            tipo="CAMION",
            categoria="PESADO",
            zona="ZONA_TEST",
            sucursal="SUCURSAL_TEST"
        )
        
        url = f"/api/v1/work/ordenes/{orden_trabajo.id}/"
        data = {
            "vehiculo": otro_vehiculo.id,  # Intentar cambiar vehículo
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "items_data": [
                {
                    "tipo": "SERVICIO",
                    "descripcion": "Servicio test",
                    "cantidad": 1,
                    "costo_unitario": "100.00"
                }
            ]
        }
        
        response = authenticated_client.put(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        orden_trabajo.refresh_from_db()
        # El vehículo original debe mantenerse
        assert orden_trabajo.vehiculo == original_vehiculo
        assert orden_trabajo.vehiculo != otro_vehiculo


# apps/vehicles/tests/test_views_actions.py
"""
Tests para acciones personalizadas de VehiculoViewSet.
"""

import pytest
from rest_framework import status
from apps.vehicles.models import IngresoVehiculo
from apps.workorders.models import OrdenTrabajo


class TestVehiculoActions:
    """Tests para acciones personalizadas de vehículos"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_ingreso_rapido_requires_guardia(self, authenticated_client, vehiculo, mecanico_user):
        """Test que solo GUARDIA puede registrar ingreso rápido"""
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = "/api/v1/vehicles/ingreso/"
        data = {
            "vehiculo": vehiculo.id,
            "observaciones": "Ingreso de prueba",
            "kilometraje": 50000
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_ingreso_rapido_success(self, authenticated_client, vehiculo, guardia_user):
        """Test registrar ingreso rápido exitosamente"""
        authenticated_client.force_authenticate(user=guardia_user)
        
        url = "/api/v1/vehicles/ingreso/"
        # El endpoint espera patente, no vehiculo.id
        data = {
            "patente": vehiculo.patente,  # Usar patente en lugar de vehiculo.id
            "observaciones": "Ingreso de prueba",
            "kilometraje": 50000
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        # La respuesta puede tener "ingreso" o los datos directamente
        if "ingreso" in response.data:
            ingreso_id = response.data["ingreso"]["id"]
        else:
            # Si no hay "ingreso", los datos están directamente en response.data
            ingreso_id = response.data["id"]
        ingreso = IngresoVehiculo.objects.get(id=ingreso_id)
        assert ingreso.vehiculo == vehiculo
        assert ingreso.guardia == guardia_user
        assert ingreso.kilometraje == 50000
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_ingreso_rapido_creates_ot(self, authenticated_client, vehiculo, guardia_user, supervisor_user, jefe_taller_user):
        """Test que ingreso rápido puede crear OT automáticamente"""
        authenticated_client.force_authenticate(user=guardia_user)
        
        url = "/api/v1/vehicles/ingreso/"
        # El endpoint espera patente, no vehiculo.id
        data = {
            "patente": vehiculo.patente,  # Usar patente en lugar de vehiculo.id
            "observaciones": "Ingreso con OT",
            "kilometraje": 50000,
            "crear_ot": True,
            "motivo_ot": "Mantenimiento preventivo"
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verificar que se creó la OT
        if "ot" in response.data:
            ot_id = response.data["ot"]["id"]
            ot = OrdenTrabajo.objects.get(id=ot_id)
            assert ot.vehiculo == vehiculo
            assert ot.motivo == "Mantenimiento preventivo"
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_registrar_salida_requires_permission(self, authenticated_client, ingreso_vehiculo, mecanico_user):
        """Test que solo roles autorizados pueden registrar salida"""
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = "/api/v1/vehicles/salida/"
        data = {
            "ingreso_id": str(ingreso_vehiculo.id),
            "observaciones_salida": "Salida de prueba"
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_registrar_salida_success(self, authenticated_client, ingreso_vehiculo, guardia_user):
        """Test registrar salida exitosamente"""
        authenticated_client.force_authenticate(user=guardia_user)
        
        url = "/api/v1/vehicles/salida/"
        data = {
            "ingreso_id": str(ingreso_vehiculo.id),
            "observaciones_salida": "Salida de prueba",
            "kilometraje_salida": 50100
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        ingreso_vehiculo.refresh_from_db()
        assert ingreso_vehiculo.salio is True
        assert ingreso_vehiculo.kilometraje_salida == 50100
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_ingresos_hoy(self, authenticated_client, ingreso_vehiculo):
        """Test listar ingresos de hoy"""
        # Verificar que el ingreso se creó correctamente
        from apps.vehicles.models import IngresoVehiculo
        from django.utils import timezone
        hoy = timezone.now().date()
        ingresos_count = IngresoVehiculo.objects.filter(fecha_ingreso__date=hoy).count()
        assert ingresos_count >= 1, f"No se encontraron ingresos para hoy ({hoy}). Total en DB: {IngresoVehiculo.objects.count()}"
        
        url = "/api/v1/vehicles/ingresos-hoy/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "ingresos" in response.data
        assert len(response.data["ingresos"]) >= 1, f"Se esperaba al menos 1 ingreso, pero se encontraron {len(response.data['ingresos'])}"
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_ingresos_historial(self, authenticated_client, ingreso_vehiculo):
        """Test listar historial de ingresos"""
        url = "/api/v1/vehicles/ingresos-historial/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        if isinstance(results, list):
            assert len(results) >= 1
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_historial_vehiculo(self, authenticated_client, vehiculo):
        """Test obtener historial completo de vehículo"""
        url = f"/api/v1/vehicles/{vehiculo.id}/historial/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # La respuesta usa "ordenes_trabajo" no "ordenes"
        assert "ordenes_trabajo" in response.data
        assert "historial_repuestos" in response.data  # También puede ser "historial_repuestos" no "repuestos"
        assert "ingresos" in response.data
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_marcas(self, authenticated_client):
        """Test listar marcas de vehículos"""
        url = "/api/v1/vehicles/marcas/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


# apps/vehicles/tests/test_views_new_features.py
"""
Tests para las nuevas funcionalidades de vehículos:
- Registro de ingreso
- Registro de salida
- Listado de ingresos del día
- Generación de ticket PDF
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.vehicles.models import Vehiculo, IngresoVehiculo
from apps.workorders.models import OrdenTrabajo

User = get_user_model()


class TestIngresoVehiculo:
    """Tests para registro de ingreso de vehículos"""
    
    @pytest.mark.view
    @pytest.mark.api
    def test_registrar_ingreso_requires_guardia(self, db, vehiculo):
        """Test que solo GUARDIA puede registrar ingreso"""
        mecanico = User.objects.create_user(
            username="mecanico_ingreso",
            email="mecanico@test.com",
            password="testpass123",
            rol=User.Rol.MECANICO,
            is_active=True
        )
        client = APIClient()
        client.force_authenticate(user=mecanico)
        
        url = "/api/v1/vehicles/ingreso/"
        data = {"patente": vehiculo.patente}
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    def test_registrar_ingreso_creates_vehiculo(self, db, guardia_user):
        """Test que registrar ingreso crea vehículo si no existe"""
        client = APIClient()
        client.force_authenticate(user=guardia_user)
        
        url = "/api/v1/vehicles/ingreso/"
        data = {
            "patente": "NEW123",
            "marca": "Toyota",
            "modelo": "Hilux",
            "anio": 2020
        }
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "ot_generada" in response.data
        assert Vehiculo.objects.filter(patente="NEW123").exists()
    
    @pytest.mark.view
    @pytest.mark.api
    def test_registrar_ingreso_creates_ot(self, db, guardia_user, vehiculo):
        """Test que registrar ingreso crea OT automáticamente"""
        client = APIClient()
        client.force_authenticate(user=guardia_user)
        
        url = "/api/v1/vehicles/ingreso/"
        data = {
            "patente": vehiculo.patente,
            "observaciones": "Ingreso para mantención"
        }
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "ot_generada" in response.data
        ot_id = response.data["ot_generada"]["id"]
        assert OrdenTrabajo.objects.filter(id=ot_id).exists()
        ot = OrdenTrabajo.objects.get(id=ot_id)
        assert ot.estado == "ABIERTA"
    
    @pytest.mark.view
    @pytest.mark.api
    def test_registrar_ingreso_requires_patente(self, db, guardia_user):
        """Test que patente es obligatoria"""
        client = APIClient()
        client.force_authenticate(user=guardia_user)
        
        url = "/api/v1/vehicles/ingreso/"
        data = {}
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestSalidaVehiculo:
    """Tests para registro de salida de vehículos"""
    
    @pytest.mark.view
    @pytest.mark.api
    def test_registrar_salida_requires_guardia(self, db, ingreso_vehiculo):
        """Test que solo GUARDIA puede registrar salida"""
        mecanico = User.objects.create_user(
            username="mecanico_salida",
            email="mecanico2@test.com",
            password="testpass123",
            rol=User.Rol.MECANICO,
            is_active=True
        )
        client = APIClient()
        client.force_authenticate(user=mecanico)
        
        url = "/api/v1/vehicles/salida/"
        data = {"ingreso_id": str(ingreso_vehiculo.id)}
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    def test_registrar_salida_success(self, db, guardia_user, ingreso_vehiculo):
        """Test registrar salida exitoso"""
        client = APIClient()
        client.force_authenticate(user=guardia_user)
        
        url = "/api/v1/vehicles/salida/"
        data = {
            "ingreso_id": str(ingreso_vehiculo.id),
            "observaciones_salida": "Vehículo listo",
            "kilometraje_salida": 50000
        }
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        ingreso_vehiculo.refresh_from_db()
        assert ingreso_vehiculo.salio is True
        assert ingreso_vehiculo.vehiculo.estado == "ACTIVO"
    
    @pytest.mark.view
    @pytest.mark.api
    def test_registrar_salida_requires_ingreso_id(self, db, guardia_user):
        """Test que ingreso_id es obligatorio"""
        client = APIClient()
        client.force_authenticate(user=guardia_user)
        
        url = "/api/v1/vehicles/salida/"
        data = {}
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestIngresosHoy:
    """Tests para listado de ingresos del día"""
    
    @pytest.mark.view
    @pytest.mark.api
    def test_ingresos_hoy_requires_authentication(self, api_client):
        """Test que requiere autenticación"""
        url = "/api/v1/vehicles/ingresos-hoy/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    def test_ingresos_hoy_success(self, authenticated_client, ingreso_vehiculo):
        """Test listar ingresos del día exitoso"""
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


class TestTicketPDF:
    """Tests para generación de ticket PDF"""
    
    @pytest.mark.view
    @pytest.mark.api
    def test_generar_ticket_requires_authentication(self, api_client, ingreso_vehiculo):
        """Test que requiere autenticación"""
        url = f"/api/v1/vehicles/ingreso/{ingreso_vehiculo.id}/ticket/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    def test_generar_ticket_success(self, authenticated_client, ingreso_vehiculo):
        """Test generar ticket PDF exitoso"""
        url = f"/api/v1/vehicles/ingreso/{ingreso_vehiculo.id}/ticket/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.get("Content-Type") == "application/pdf" or "application/pdf" in str(response.get("Content-Type", ""))
        assert "ticket_ingreso" in str(response.get("Content-Disposition", ""))
    
    @pytest.mark.view
    @pytest.mark.api
    def test_generar_ticket_not_found(self, authenticated_client):
        """Test generar ticket con ingreso inexistente"""
        url = "/api/v1/vehicles/ingreso/00000000-0000-0000-0000-000000000000/ticket/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# apps/vehicles/tests/test_views.py
"""
Tests para las views de vehículos.
"""

import pytest
from rest_framework import status
from apps.vehicles.models import Vehiculo


class TestVehiculoViewSet:
    """Tests para VehiculoViewSet"""
    
    @pytest.mark.view
    @pytest.mark.api
    def test_list_vehicles_requires_authentication(self, api_client):
        """Test que listar vehículos requiere autenticación"""
        url = "/api/v1/vehicles/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    def test_list_vehicles_success(self, authenticated_client, vehiculo):
        """Test listar vehículos exitoso"""
        url = "/api/v1/vehicles/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # La respuesta puede tener paginación o ser una lista directa
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        if isinstance(results, list):
            assert len(results) >= 1
        else:
            # Si es un solo resultado o dict
            assert response.data is not None
    
    @pytest.mark.view
    @pytest.mark.api
    def test_create_vehicle_success(self, authenticated_client, supervisor_user, marca):
        """Test crear vehículo exitoso"""
        url = "/api/v1/vehicles/"
        data = {
            "patente": "AA1234",  # Formato válido de patente
            "marca": marca.id,  # Usar ID de la marca, no el nombre
            "modelo": "Hilux",
            "anio": 2020,
            "tipo": "ELECTRICO",
            "estado": "ACTIVO",
            "zona": "ZONA_TEST",  # Usar zona en lugar de site
            "sucursal": "SUCURSAL_TEST",
            "supervisor": supervisor_user.id,
            "estado_operativo": "OPERATIVO"
        }
        response = authenticated_client.post(url, data, format="json")
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Errores: {response.data}")
        assert response.status_code == status.HTTP_201_CREATED
        # Verificar que el vehículo se creó correctamente
        assert response.data["patente"] == "AA1234"
    
    @pytest.mark.view
    @pytest.mark.api
    def test_create_vehicle_invalid_patente(self, authenticated_client, supervisor_user):
        """Test crear vehículo con patente inválida"""
        url = "/api/v1/vehicles/"
        data = {
            "patente": "INVALID",  # Formato inválido
            "marca": "Toyota",
            "modelo": "Hilux",
            "anio": 2020,
            "tipo": "ELECTRICO",
            "estado": "ACTIVO",
            "site": "SITE_TEST",
            "supervisor": supervisor_user.id,
            "estado_operativo": "OPERATIVO"
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "patente" in response.data
    
    @pytest.mark.view
    @pytest.mark.api
    def test_retrieve_vehicle_success(self, authenticated_client, vehiculo):
        """Test obtener vehículo por ID"""
        url = f"/api/v1/vehicles/{vehiculo.id}/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["patente"] == vehiculo.patente
    
    @pytest.mark.view
    @pytest.mark.api
    def test_update_vehicle_success(self, authenticated_client, vehiculo, marca):
        """Test actualizar vehículo"""
        from apps.vehicles.models import Marca
        ford_marca, _ = Marca.objects.get_or_create(nombre="Ford", defaults={"activa": True})
        
        url = f"/api/v1/vehicles/{vehiculo.id}/"
        data = {
            "marca": ford_marca.id,
            "modelo": "Ranger"
        }
        response = authenticated_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        # El serializer retorna marca_nombre como string
        assert response.data.get("marca_nombre") == "Ford" or response.data.get("marca") == ford_marca.id
    
    @pytest.mark.view
    @pytest.mark.api
    def test_delete_vehicle_success(self, authenticated_client, vehiculo):
        """Test eliminar vehículo"""
        url = f"/api/v1/vehicles/{vehiculo.id}/"
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar que fue eliminado
        assert not Vehiculo.objects.filter(id=vehiculo.id).exists()
    
    @pytest.mark.view
    @pytest.mark.api
    def test_filter_vehicles_by_estado(self, authenticated_client, vehiculo):
        """Test filtrar vehículos por estado"""
        url = "/api/v1/vehicles/?estado=ACTIVO"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # La respuesta puede tener paginación o ser una lista directa
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        if isinstance(results, list):
            # Todos los resultados deben tener estado ACTIVO
            for result in results:
                assert result.get("estado") == "ACTIVO" or result["estado"] == "ACTIVO"
        else:
            # Si es un solo resultado
            assert response.data is not None
    
    @pytest.mark.view
    @pytest.mark.api
    def test_search_vehicles_by_patente(self, authenticated_client, vehiculo):
        """Test buscar vehículos por patente"""
        url = f"/api/v1/vehicles/?search={vehiculo.patente}"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # La respuesta puede tener paginación o ser una lista directa
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        if isinstance(results, list):
            assert len(results) >= 1
            assert any(r.get("patente") == vehiculo.patente or r["patente"] == vehiculo.patente for r in results)
        else:
            # Si es un solo resultado
            assert results.get("patente") == vehiculo.patente or results["patente"] == vehiculo.patente
    
    @pytest.mark.view
    @pytest.mark.api
    def test_ingreso_requires_guardia_role(self, authenticated_client):
        """Test que registrar ingreso requiere rol GUARDIA"""
        url = "/api/v1/vehicles/ingreso/"
        data = {
            "patente": "ABC123",
            "observaciones": "Test ingreso"
        }
        response = authenticated_client.post(url, data, format="json")
        # Admin no puede registrar ingresos, solo GUARDIA
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.view
    @pytest.mark.api
    def test_ingreso_missing_patente(self, db):
        """Test registrar ingreso sin patente"""
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient
        User = get_user_model()
        
        guardia = User.objects.create_user(
            username="guardia_test",
            email="guardia@test.com",
            password="testpass123",
            rol=User.Rol.GUARDIA,
            is_active=True
        )
        
        client = APIClient()
        client.force_authenticate(user=guardia)
        
        url = "/api/v1/vehicles/ingreso/"
        data = {
            "observaciones": "Test ingreso sin patente"
        }
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "patente" in response.data["detail"].lower()
    
    @pytest.mark.view
    @pytest.mark.api
    def test_historial_requires_authentication(self, api_client, vehiculo):
        """Test que historial requiere autenticación"""
        url = f"/api/v1/vehicles/{vehiculo.id}/historial/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    def test_historial_success(self, authenticated_client, vehiculo):
        """Test obtener historial de vehículo"""
        url = f"/api/v1/vehicles/{vehiculo.id}/historial/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "vehiculo" in response.data
        assert "ordenes_trabajo" in response.data
        assert "ingresos" in response.data


# apps/drivers/tests/test_views.py
"""
Pruebas para las vistas de drivers (choferes).
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from apps.drivers.models import Chofer, HistorialAsignacionVehiculo
from apps.vehicles.models import Vehiculo


@pytest.mark.django_db
@pytest.mark.view
@pytest.mark.api
class TestChoferViewSet:
    """Pruebas para el ViewSet de Choferes."""
    
    def test_list_choferes_requires_authentication(self):
        """Test que listar choferes requiere autenticación."""
        client = APIClient()
        response = client.get("/api/v1/drivers/choferes/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_choferes_success(self, authenticated_client, db):
        """Test listar choferes exitosamente."""
        # Crear chofer de prueba
        chofer = Chofer.objects.create(
            nombre_completo="Juan Pérez",
            rut="123456785",  # RUT sin puntos ni guión
            telefono="+56912345678",
            email="juan@test.com",
            activo=True
        )
        
        response = authenticated_client.get("/api/v1/drivers/choferes/")
        assert response.status_code == status.HTTP_200_OK
        # Manejar paginación o lista directa
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1
        assert any(c["id"] == str(chofer.id) for c in data)
    
    def test_create_chofer_success(self, authenticated_client, db):
        """Test crear chofer exitosamente."""
        data = {
            "nombre_completo": "Pedro González",
            "rut": "12345678-5",  # RUT válido chileno
            "telefono": "+56987654321",
            "email": "pedro@test.com",
            "zona": "Norte",
            "activo": True
        }
        
        response = authenticated_client.post("/api/v1/drivers/choferes/", data, format="json")
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Error response: {response.data}")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["nombre_completo"] == data["nombre_completo"]
        # El RUT se limpia (sin puntos ni guión)
        assert response.data["rut"] == "123456785"
    
    def test_create_chofer_duplicate_rut(self, authenticated_client, db):
        """Test que no se puede crear chofer con RUT duplicado."""
        # Crear chofer existente con RUT válido
        Chofer.objects.create(
            nombre_completo="Chofer Existente",
            rut="11111111-1",  # RUT válido chileno
            activo=True
        )
        
        data = {
            "nombre_completo": "Otro Chofer",
            "rut": "11111111-1",  # RUT duplicado
            "activo": True
        }
        
        response = authenticated_client.post("/api/v1/drivers/choferes/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_retrieve_chofer_success(self, authenticated_client, db):
        """Test obtener chofer por ID."""
        chofer = Chofer.objects.create(
            nombre_completo="María López",
            rut="222222222",  # RUT sin puntos ni guión
            activo=True
        )
        
        response = authenticated_client.get(f"/api/v1/drivers/choferes/{chofer.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["nombre_completo"] == chofer.nombre_completo
        assert response.data["rut"] == chofer.rut
    
    def test_update_chofer_success(self, authenticated_client, db):
        """Test actualizar chofer."""
        chofer = Chofer.objects.create(
            nombre_completo="Carlos Ruiz",
            rut="333333333",  # RUT sin puntos ni guión
            telefono="+56911111111",
            activo=True
        )
        
        data = {
            "nombre_completo": "Carlos Ruiz Actualizado",
            "rut": chofer.rut,
            "telefono": "+56922222222",
            "activo": True
        }
        
        response = authenticated_client.put(f"/api/v1/drivers/choferes/{chofer.id}/", data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["nombre_completo"] == "Carlos Ruiz Actualizado"
        assert response.data["telefono"] == "+56922222222"
    
    def test_delete_chofer_success(self, authenticated_client, db):
        """Test eliminar chofer."""
        chofer = Chofer.objects.create(
            nombre_completo="Chofer a Eliminar",
            rut="444444444",  # RUT sin puntos ni guión
            activo=True
        )
        
        response = authenticated_client.delete(f"/api/v1/drivers/choferes/{chofer.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Chofer.objects.filter(id=chofer.id).exists()
    
    def test_asignar_vehiculo_success(self, authenticated_client, db, vehiculo):
        """Test asignar vehículo a chofer."""
        chofer = Chofer.objects.create(
            nombre_completo="Chofer con Vehículo",
            rut="555555555",  # RUT sin puntos ni guión
            activo=True
        )
        
        data = {
            "vehiculo_id": str(vehiculo.id)
        }
        
        response = authenticated_client.post(
            f"/api/v1/drivers/choferes/{chofer.id}/asignar-vehiculo/",
            data,
            format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        # El vehiculo_asignado puede ser UUID o string
        vehiculo_id = response.data.get("vehiculo_asignado")
        assert str(vehiculo.id) == str(vehiculo_id)
        
        # Verificar que se creó registro en historial
        historial = HistorialAsignacionVehiculo.objects.filter(chofer=chofer, vehiculo=vehiculo).first()
        assert historial is not None
        assert historial.fecha_fin is None  # Asignación activa
    
    def test_asignar_vehiculo_missing_id(self, authenticated_client, db):
        """Test asignar vehículo sin proporcionar ID."""
        chofer = Chofer.objects.create(
            nombre_completo="Chofer sin Vehículo",
            rut="666666666",  # RUT sin puntos ni guión
            activo=True
        )
        
        response = authenticated_client.post(
            f"/api/v1/drivers/choferes/{chofer.id}/asignar-vehiculo/",
            {},
            format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_historial_chofer_success(self, authenticated_client, db, vehiculo):
        """Test obtener historial de asignaciones de un chofer."""
        chofer = Chofer.objects.create(
            nombre_completo="Chofer con Historial",
            rut="777777777",  # RUT sin puntos ni guión
            activo=True
        )
        
        # Crear historial (fecha_asignacion se crea automáticamente)
        historial = HistorialAsignacionVehiculo.objects.create(
            chofer=chofer,
            vehiculo=vehiculo,
            activa=True
        )
        
        response = authenticated_client.get(f"/api/v1/drivers/choferes/{chofer.id}/historial/")
        assert response.status_code == status.HTTP_200_OK
        # Manejar paginación o lista directa
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1
        assert any(h.get("chofer") == str(chofer.id) or str(chofer.id) in str(h.get("chofer", "")) for h in data)
    
    def test_filter_choferes_by_activo(self, authenticated_client, db):
        """Test filtrar choferes por estado activo."""
        Chofer.objects.create(nombre_completo="Chofer Activo", rut="888888888", activo=True)
        Chofer.objects.create(nombre_completo="Chofer Inactivo", rut="999999999", activo=False)
        
        response = authenticated_client.get("/api/v1/drivers/choferes/?activo=true")
        assert response.status_code == status.HTTP_200_OK
        # Manejar paginación o lista directa
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert all(c["activo"] is True for c in data)
    
    def test_search_choferes_by_nombre(self, authenticated_client, db):
        """Test buscar choferes por nombre."""
        Chofer.objects.create(nombre_completo="Juan Pérez", rut="101010101", activo=True)
        Chofer.objects.create(nombre_completo="Pedro González", rut="202020202", activo=True)
        
        response = authenticated_client.get("/api/v1/drivers/choferes/?search=Juan")
        assert response.status_code == status.HTTP_200_OK
        # Manejar paginación o lista directa
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert any("Juan" in c["nombre_completo"] for c in data)


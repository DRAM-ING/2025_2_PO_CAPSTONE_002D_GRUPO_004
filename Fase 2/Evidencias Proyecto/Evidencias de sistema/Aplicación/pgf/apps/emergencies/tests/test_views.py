# apps/emergencies/tests/test_views.py
"""
Pruebas para las vistas de emergencias.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from apps.emergencies.models import EmergenciaRuta
from apps.vehicles.models import Vehiculo
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.view
@pytest.mark.api
class TestEmergenciaRutaViewSet:
    """Pruebas para el ViewSet de Emergencias."""
    
    @pytest.fixture
    def coordinador_user(self, db):
        """Crea un usuario coordinador para pruebas."""
        return User.objects.create_user(
            username="coordinador_test",
            email="coordinador@test.com",
            password="testpass123",
            rol=User.Rol.COORDINADOR_ZONA,
            is_active=True,
            rut="11111111-1"
        )
    
    @pytest.fixture
    def emergencia(self, db, vehiculo, coordinador_user):
        """Crea una emergencia de prueba."""
        return EmergenciaRuta.objects.create(
            vehiculo=vehiculo,
            solicitante=coordinador_user,
            descripcion="Emergencia de prueba",
            ubicacion="Ruta 5, km 100",
            estado="SOLICITADA",
            prioridad="ALTA"
        )
    
    def test_list_emergencias_requires_authentication(self):
        """Test que listar emergencias requiere autenticación."""
        client = APIClient()
        response = client.get("/api/v1/emergencies/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_emergencias_success(self, authenticated_client, emergencia):
        """Test listar emergencias exitosamente."""
        response = authenticated_client.get("/api/v1/emergencies/")
        assert response.status_code == status.HTTP_200_OK
        # Manejar paginación o lista directa
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1
    
    def test_create_emergencia_success(self, db, vehiculo, coordinador_user):
        """Test crear emergencia exitosamente."""
        from rest_framework.test import APIClient
        
        # Usar cliente autenticado con coordinador
        client = APIClient()
        client.force_authenticate(user=coordinador_user)
        
        data = {
            "vehiculo": str(vehiculo.id),
            "descripcion": "Nueva emergencia",
            "ubicacion": "Ruta 5, km 200",
            "prioridad": "ALTA"
            # No incluir solicitante ni estado, se asignan automáticamente
        }
        
        response = client.post("/api/v1/emergencies/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data.get("descripcion") == data["descripcion"] or "descripcion" in str(response.data)
        
        # Verificar que se creó correctamente en la base de datos
        emergencia_creada = EmergenciaRuta.objects.filter(
            vehiculo=vehiculo,
            solicitante=coordinador_user,
            descripcion=data["descripcion"]
        ).first()
        assert emergencia_creada is not None
        assert emergencia_creada.estado == "SOLICITADA"
        assert emergencia_creada.solicitante == coordinador_user
    
    def test_retrieve_emergencia_success(self, authenticated_client, emergencia):
        """Test obtener emergencia por ID."""
        response = authenticated_client.get(f"/api/v1/emergencies/{emergencia.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(emergencia.id)
        assert response.data["descripcion"] == emergencia.descripcion
    
    def test_update_emergencia_success(self, authenticated_client, emergencia):
        """Test actualizar emergencia."""
        data = {
            "vehiculo": str(emergencia.vehiculo.id),
            "solicitante": str(emergencia.solicitante.id),
            "descripcion": "Emergencia actualizada",
            "ubicacion": emergencia.ubicacion,
            "estado": emergencia.estado,
            "prioridad": "CRITICA"
        }
        
        response = authenticated_client.put(f"/api/v1/emergencies/{emergencia.id}/", data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["descripcion"] == "Emergencia actualizada"
        assert response.data["prioridad"] == "CRITICA"
    
    def test_filter_emergencias_by_estado(self, authenticated_client, emergencia):
        """Test filtrar emergencias por estado."""
        response = authenticated_client.get("/api/v1/emergencies/?estado=SOLICITADA")
        assert response.status_code == status.HTTP_200_OK
        # Manejar paginación o lista directa
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert all(e["estado"] == "SOLICITADA" for e in data)
    
    def test_search_emergencias_by_patente(self, authenticated_client, emergencia):
        """Test buscar emergencias por patente del vehículo."""
        response = authenticated_client.get(f"/api/v1/emergencies/?search={emergencia.vehiculo.patente}")
        assert response.status_code == status.HTTP_200_OK
        # Manejar paginación o lista directa
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1
    
    def test_mecanico_sees_only_assigned(self, db, vehiculo, coordinador_user):
        """Test que mecánico solo ve emergencias asignadas a él."""
        from rest_framework.test import APIClient
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        mecanico = User.objects.create_user(
            username="mecanico_test",
            email="mecanico@test.com",
            password="testpass123",
            rol=User.Rol.MECANICO,
            is_active=True,
            rut="22222222-2"
        )
        
        # Crear emergencia asignada al mecánico
        emergencia_asignada = EmergenciaRuta.objects.create(
            vehiculo=vehiculo,
            solicitante=coordinador_user,
            mecanico_asignado=mecanico,
            descripcion="Emergencia asignada",
            ubicacion="Ruta 5",
            estado="ASIGNADA"
        )
        
        # Crear emergencia no asignada
        EmergenciaRuta.objects.create(
            vehiculo=vehiculo,
            solicitante=coordinador_user,
            descripcion="Emergencia no asignada",
            ubicacion="Ruta 5",
            estado="SOLICITADA"
        )
        
        client = APIClient()
        client.force_authenticate(user=mecanico)
        
        response = client.get("/api/v1/emergencies/")
        assert response.status_code == status.HTTP_200_OK
        # Manejar paginación o lista directa
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) == 1
        assert data[0]["id"] == str(emergencia_asignada.id)


# apps/scheduling/tests/test_views.py
"""
Tests para las views de scheduling (agenda y programación).
"""

import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import status
from apps.scheduling.models import Agenda, CupoDiario


@pytest.fixture
def agenda(db, vehiculo, coordinador_user):
    """Crea una agenda de prueba"""
    return Agenda.objects.create(
        vehiculo=vehiculo,
        coordinador=coordinador_user,  # El modelo usa coordinador, no supervisor
        fecha_programada=timezone.now() + timedelta(days=7),
        motivo="Mantenimiento preventivo de prueba",  # Campo requerido
        tipo_mantenimiento="PREVENTIVO",
        estado="PROGRAMADA",  # El modelo usa string, no enum
        observaciones="Mantenimiento programado",
        zona="ZONA_TEST"
    )


@pytest.fixture
def cupo_diario(db):
    """Crea un cupo diario de prueba"""
    fecha = timezone.now().date() + timedelta(days=1)
    return CupoDiario.objects.create(
        fecha=fecha,
        zona="Norte",
        cupos_totales=10,  # El modelo usa cupos_totales y cupos_ocupados
        cupos_ocupados=3  # cupos_disponibles es una propiedad calculada
    )


class TestAgendaViewSet:
    """Tests para AgendaViewSet"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_agenda_requires_authentication(self, api_client):
        """Test que listar agenda requiere autenticación"""
        # La URL correcta es /agendas/ (plural) según el router
        url = "/api/v1/scheduling/agendas/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_agenda_success(self, authenticated_client, agenda):
        """Test listar agenda exitosamente"""
        url = "/api/v1/scheduling/agendas/"  # URL correcta con plural
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        if isinstance(results, list):
            assert len(results) >= 1
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_create_agenda_success(self, authenticated_client, vehiculo, coordinador_user):
        """Test crear agenda exitosamente"""
        # El usuario debe ser coordinador para crear agendas
        authenticated_client.force_authenticate(user=coordinador_user)
        url = "/api/v1/scheduling/agendas/"  # URL correcta con plural
        data = {
            "vehiculo": vehiculo.id,
            # coordinador se asigna automáticamente desde el usuario autenticado
            "fecha_programada": (timezone.now() + timedelta(days=7)).isoformat(),
            "motivo": "Mantenimiento preventivo de prueba",  # Campo requerido
            "tipo_mantenimiento": "PREVENTIVO",
            "estado": "PROGRAMADA",
            "observaciones": "Nueva programación"
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["tipo_mantenimiento"] == "PREVENTIVO"
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_update_agenda_estado(self, authenticated_client, agenda):
        """Test actualizar estado de agenda"""
        url = f"/api/v1/scheduling/agendas/{agenda.id}/"  # URL correcta con plural
        data = {"estado": "CONFIRMADA"}
        response = authenticated_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["estado"] == "CONFIRMADA"
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_filter_agenda_by_estado(self, authenticated_client, agenda):
        """Test filtrar agenda por estado"""
        url = "/api/v1/scheduling/agendas/?estado=PROGRAMADA"  # URL correcta con plural
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        if isinstance(results, list):
            assert all(item["estado"] == "PROGRAMADA" for item in results)


class TestCupoDiarioViewSet:
    """Tests para CupoDiarioViewSet"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_cupos_requires_authentication(self, api_client):
        """Test que listar cupos requiere autenticación"""
        url = "/api/v1/scheduling/cupos/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_cupos_success(self, authenticated_client, cupo_diario):
        """Test listar cupos exitosamente"""
        url = "/api/v1/scheduling/cupos/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        if isinstance(results, list):
            assert len(results) >= 1
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_filter_cupos_by_zona(self, authenticated_client, cupo_diario):
        """Test filtrar cupos por zona"""
        url = "/api/v1/scheduling/cupos/?zona=Norte"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        if isinstance(results, list):
            assert all(item["zona"] == "Norte" for item in results)


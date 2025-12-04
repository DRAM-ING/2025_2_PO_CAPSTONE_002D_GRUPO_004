# apps/drivers/tests/test_views_extended.py
"""
Tests adicionales para acciones personalizadas de drivers.
"""

import pytest
from rest_framework import status
from django.utils import timezone
from apps.drivers.models import Chofer, HistorialAsignacionVehiculo


@pytest.fixture
def chofer(db):
    """Crea un chofer de prueba"""
    return Chofer.objects.create(
        nombre_completo="Juan Pérez",
        rut="123456785",
        telefono="+56912345678",
        email="juan@test.com",
        activo=True
    )


class TestChoferActions:
    """Tests para acciones personalizadas de choferes"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_asignar_vehiculo_success(self, authenticated_client, chofer, vehiculo, supervisor_user):
        """Test asignar vehículo a chofer exitosamente"""
        authenticated_client.force_authenticate(user=supervisor_user)
        
        url = f"/api/v1/drivers/choferes/{chofer.id}/asignar-vehiculo/"
        data = {"vehiculo_id": vehiculo.id}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        chofer.refresh_from_db()
        assert chofer.vehiculo_asignado == vehiculo
        
        # Verificar que se creó historial
        historial = HistorialAsignacionVehiculo.objects.filter(chofer=chofer).latest('fecha_asignacion')
        assert historial.vehiculo == vehiculo
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_historial_asignaciones(self, authenticated_client, chofer, vehiculo):
        """Test obtener historial de asignaciones"""
        # Crear asignación previa
        HistorialAsignacionVehiculo.objects.create(
            chofer=chofer,
            vehiculo=vehiculo,
            fecha_asignacion=timezone.now()
        )
        
        url = f"/api/v1/drivers/choferes/{chofer.id}/historial/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


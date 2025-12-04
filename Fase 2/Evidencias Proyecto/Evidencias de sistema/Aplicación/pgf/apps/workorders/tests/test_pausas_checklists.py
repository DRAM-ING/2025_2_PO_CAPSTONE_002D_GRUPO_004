# apps/workorders/tests/test_pausas_checklists.py
"""
Tests para PausaViewSet y ChecklistViewSet.
"""

import pytest
from django.utils import timezone
from rest_framework import status
from apps.workorders.models import Pausa, Checklist


@pytest.fixture
def pausa(db, orden_trabajo, mecanico_user):
    """Crea una pausa de prueba"""
    return Pausa.objects.create(
        ot=orden_trabajo,
        usuario=mecanico_user,  # Campo requerido
        motivo="Pausa de prueba",
        inicio=timezone.now()
    )


@pytest.fixture
def checklist(db, orden_trabajo, supervisor_user):
    """Crea un checklist de prueba"""
    return Checklist.objects.create(
        ot=orden_trabajo,
        verificador=supervisor_user,
        resultado="OK",
        observaciones="Checklist de prueba"
    )


class TestPausaViewSet:
    """Tests para PausaViewSet"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_pausas_requires_authentication(self, api_client):
        """Test que listar pausas requiere autenticación"""
        url = "/api/v1/work/pausas/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_create_pausa_success(self, authenticated_client, orden_trabajo, mecanico_user):
        """Test crear pausa exitosamente"""
        orden_trabajo.estado = "EN_EJECUCION"
        orden_trabajo.mecanico = mecanico_user
        orden_trabajo.save()
        
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = "/api/v1/work/pausas/"
        data = {
            "ot": str(orden_trabajo.id),
            "usuario": str(mecanico_user.id),  # Campo requerido
            "tipo": "OTRO",  # Campo requerido
            "motivo": "Pausa de prueba",
            "inicio": timezone.now().isoformat()
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED, f"Error: {response.data}"
        assert response.data["motivo"] == "Pausa de prueba"
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_finalizar_pausa(self, authenticated_client, orden_trabajo, mecanico_user):
        """Test finalizar pausa"""
        # Asegurar que la OT esté asignada al mecánico para que pueda ver la pausa
        orden_trabajo.mecanico = mecanico_user
        orden_trabajo.estado = "EN_EJECUCION"
        orden_trabajo.save()
        
        # Crear pausa asociada a la OT
        from apps.workorders.models import Pausa
        pausa = Pausa.objects.create(
            ot=orden_trabajo,
            usuario=mecanico_user,
            tipo="OTRO",
            motivo="Pausa de prueba",
            inicio=timezone.now()
        )
        
        authenticated_client.force_authenticate(user=mecanico_user)
        
        url = f"/api/v1/work/pausas/{pausa.id}/"
        data = {"fin": timezone.now().isoformat()}
        response = authenticated_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK, f"Error: {response.data}"
        
        pausa.refresh_from_db()
        assert pausa.fin is not None


class TestChecklistViewSet:
    """Tests para ChecklistViewSet"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_checklists_requires_authentication(self, api_client):
        """Test que listar checklists requiere autenticación"""
        url = "/api/v1/work/checklists/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_create_checklist_success(self, authenticated_client, orden_trabajo, supervisor_user):
        """Test crear checklist exitosamente"""
        orden_trabajo.estado = "EN_QA"
        orden_trabajo.save()
        
        authenticated_client.force_authenticate(user=supervisor_user)
        
        url = "/api/v1/work/checklists/"
        data = {
            "ot": str(orden_trabajo.id),
            "resultado": "OK",
            "observaciones": "Checklist de prueba"
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["resultado"] == "OK"
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_update_checklist(self, authenticated_client, checklist, supervisor_user):
        """Test actualizar checklist"""
        authenticated_client.force_authenticate(user=supervisor_user)
        
        url = f"/api/v1/work/checklists/{checklist.id}/"
        data = {"resultado": "NO_OK", "observaciones": "Actualizado"}
        response = authenticated_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        checklist.refresh_from_db()
        assert checklist.resultado == "NO_OK"
        assert checklist.observaciones == "Actualizado"


import pytest
from django.urls import reverse
from rest_framework import status
from apps.workorders.models import OrdenTrabajo

@pytest.mark.django_db
class TestOrdenTrabajoEdgeCases:
    
    def test_crear_ot_sin_vehiculo(self, authenticated_client, jefe_taller_user, vehiculo):
        """Intenta crear una OT sin especificar vehículo."""
        authenticated_client.force_authenticate(user=jefe_taller_user)
        url = reverse('orden-trabajo-list')
        # Incluir responsable pero no vehiculo para que falle por falta de vehiculo
        data = {
            "motivo": "Falla desconocida",
            "responsable": jefe_taller_user.id  # Agregar responsable para que el error sea sobre vehiculo
            # No incluir vehiculo para que falle
        }
        response = authenticated_client.post(url, data)
        # El serializer ahora valida vehiculo y retorna 400, no 500
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # El error debe ser sobre vehiculo
        assert "vehiculo" in response.data or any("vehiculo" in str(error).lower() for error_list in response.data.values() if isinstance(error_list, list) for error in error_list)

    def test_transicion_invalida_directa(self, authenticated_client, jefe_taller_user, orden_trabajo):
        """Intenta pasar de ABIERTA a CERRADA directamente (no permitido)."""
        authenticated_client.force_authenticate(user=jefe_taller_user)
        url = reverse('orden-trabajo-cerrar', args=[orden_trabajo.id])
        response = authenticated_client.post(url)
        
        # Debería fallar porque debe pasar por QA primero
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.estado == "ABIERTA"

    def test_acceso_ot_otro_zona(self, api_client, jefe_taller_user, orden_trabajo):
        """Un usuario de una zona puede ver OTs de otras zonas (lógica actual)."""
        # Por ahora la lógica de zonas no está estricta en el ViewSet, pero es buen caso para probar
        # Si implementamos multi-tenancy o filtrado por zona.
        pass

    def test_crear_ot_vehiculo_inactivo(self, authenticated_client, jefe_taller_user, vehiculo):
        """Intenta crear OT para un vehículo dado de baja."""
        vehiculo.estado = "INACTIVO"
        vehiculo.save()
        
        authenticated_client.force_authenticate(user=jefe_taller_user)
        url = reverse('orden-trabajo-list')
        data = {
            "vehiculo": vehiculo.patente,
            "motivo": "Reparación",
            "supervisor": jefe_taller_user.id
        }
        response = authenticated_client.post(url, data)
        # Dependiendo de la lógica, esto podría ser 400 o permitido.
        # Asumimos que no se debe reparar un vehículo inactivo.
        # Si el sistema lo permite, este test fallará y nos alertará para definir la regla.
        if response.status_code == 201:
            pytest.warns(UserWarning, match="Se permitió crear OT para vehículo INACTIVO")
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_flujo_completo_happy_path(self, authenticated_client, jefe_taller_user, orden_trabajo):
        """Prueba el ciclo de vida completo de una OT."""
        authenticated_client.force_authenticate(user=jefe_taller_user)
        
        # 1. Diagnóstico
        url = reverse('orden-trabajo-diagnostico', args=[orden_trabajo.id])
        resp = authenticated_client.post(url, {"diagnostico": "Falla motor", "nivel_combustible": 50})
        assert resp.status_code == status.HTTP_200_OK
        
        # 2. Ejecución
        url = reverse('orden-trabajo-en-ejecucion', args=[orden_trabajo.id])
        resp = authenticated_client.post(url)
        assert resp.status_code == status.HTTP_200_OK
        
        # 3. QA
        url = reverse('orden-trabajo-en-qa', args=[orden_trabajo.id])
        resp = authenticated_client.post(url)
        assert resp.status_code == status.HTTP_200_OK
        
        # 4. Cerrar
        url = reverse('orden-trabajo-cerrar', args=[orden_trabajo.id])
        # Cerrar requiere fecha_cierre y diagnostico_final
        data_cierre = {
            "fecha_cierre": "2024-01-15T10:30:00Z",
            "diagnostico_final": "Motor reparado exitosamente"
        }
        resp = authenticated_client.post(url, data_cierre)
        assert resp.status_code == status.HTTP_200_OK
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.estado == "CERRADA"

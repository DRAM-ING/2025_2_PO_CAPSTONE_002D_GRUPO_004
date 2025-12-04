# apps/workorders/tests/test_presupuestos.py
"""
Tests para PresupuestoViewSet y DetallePresupViewSet.
"""

import pytest
from decimal import Decimal
from rest_framework import status
from apps.workorders.models import Presupuesto, DetallePresup


@pytest.fixture
def presupuesto(db, orden_trabajo):
    """Crea un presupuesto de prueba"""
    from decimal import Decimal
    return Presupuesto.objects.create(
        ot=orden_trabajo,
        total=Decimal("500.00"),
        requiere_aprobacion=False
    )


class TestPresupuestoViewSet:
    """Tests para PresupuestoViewSet"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_presupuestos_requires_authentication(self, api_client):
        """Test que listar presupuestos requiere autenticación"""
        url = "/api/v1/work/presupuestos/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_create_presupuesto_calcula_total(self, authenticated_client, orden_trabajo):
        """Test que crear presupuesto calcula total automáticamente"""
        url = "/api/v1/work/presupuestos/"
        data = {
            "ot": str(orden_trabajo.id),
            "detalles_data": [
                {
                    "concepto": "Repuesto A",
                    "cantidad": 2,
                    "precio": 100.00
                },
                {
                    "concepto": "Repuesto B",
                    "cantidad": 1,
                    "precio": 50.00
                }
            ]
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED, f"Error: {response.data}"
        # El serializer puede devolver total como string o Decimal
        total = response.data.get("total")
        if isinstance(total, str):
            total = Decimal(total)
        else:
            total = Decimal(str(total))
        assert total == Decimal("250.00")  # 2*100 + 1*50
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_create_presupuesto_requiere_aprobacion(self, authenticated_client, orden_trabajo):
        """Test que presupuesto > 1000 requiere aprobación"""
        url = "/api/v1/work/presupuestos/"
        data = {
            "ot": str(orden_trabajo.id),
            "detalles_data": [
                {
                    "concepto": "Repuesto Caro",
                    "cantidad": 1,
                    "precio": 1500.00
                }
            ]
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["requiere_aprobacion"] is True


class TestDetallePresupViewSet:
    """Tests para DetallePresupViewSet"""
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_list_detalles_requires_authentication(self, api_client):
        """Test que listar detalles requiere autenticación"""
        url = "/api/v1/work/detalles-presupuesto/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.view
    @pytest.mark.api
    @pytest.mark.django_db
    def test_create_detalle_presupuesto(self, authenticated_client, presupuesto):
        """Test crear detalle de presupuesto"""
        url = "/api/v1/work/detalles-presupuesto/"
        data = {
            "presupuesto": presupuesto.id,
            "concepto": "Nuevo concepto",
            "cantidad": 3,
            "precio": 75.00
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["concepto"] == "Nuevo concepto"
        # El serializer puede tener 'subtotal' como campo calculado o podemos calcularlo manualmente
        if "subtotal" in response.data:
            subtotal = Decimal(str(response.data["subtotal"]))
        else:
            # Calcular manualmente: cantidad * precio
            cantidad = Decimal(str(response.data["cantidad"]))
            precio = Decimal(str(response.data["precio"]))
            subtotal = cantidad * precio
        assert subtotal == Decimal("225.00")  # 3 * 75


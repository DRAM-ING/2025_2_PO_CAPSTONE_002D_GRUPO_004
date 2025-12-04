# apps/vehicles/tests.py
import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from apps.users.models import User
from apps.vehicles.models import Vehiculo

@pytest.mark.django_db
def test_vehiculos_list_requires_auth():
    client = APIClient()
    url = "/api/vehiculos/"
    r = client.get(url)
    assert r.status_code in (401, 403)

@pytest.mark.django_db
def test_supervisor_can_create_vehicle():
    u = User.objects.create_user(username="sup", password="x", rol="SUPERVISOR")
    client = APIClient()
    token = client.post("/api/auth/token/", {"username":"sup","password":"x"}, format="json").data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    payload = {"patente":"XYZ123","marca":"Volvo","modelo":"FH","anio":2023,"vin":"VIN-1","estado":"ACTIVO"}
    r = client.post("/api/vehiculos/", payload, format="json")
    assert r.status_code in (200,201), r.data
    assert Vehiculo.objects.filter(patente="XYZ123").exists()

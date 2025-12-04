# conftest.py
"""
Configuración global de pytest para el proyecto PGF.

Este archivo contiene fixtures compartidas que pueden ser usadas
en todos los tests del proyecto.
"""

import pytest
from django.contrib.auth import get_user_model
from apps.vehicles.models import Vehiculo, IngresoVehiculo
from apps.workorders.models import OrdenTrabajo, Evidencia
from datetime import datetime, timedelta
import uuid

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Crea un usuario administrador para pruebas."""
    return User.objects.create_user(
        username="admin_test",
        email="admin@test.com",
        password="testpass123",
        rol=User.Rol.ADMIN,
        is_active=True,
        rut="12345678-5"  # RUT válido
    )


@pytest.fixture
def supervisor_user(db):
    """Crea un usuario supervisor para pruebas."""
    return User.objects.create_user(
        username="supervisor_test",
        email="supervisor@test.com",
        password="testpass123",
        rol=User.Rol.SUPERVISOR,
        is_active=True,
        rut="87654321-0"
    )


@pytest.fixture
def jefe_taller_user(db):
    """Crea un usuario jefe de taller para pruebas."""
    return User.objects.create_user(
        username="jefe_taller_test",
        email="jefe@test.com",
        password="testpass123",
        rol=User.Rol.JEFE_TALLER,
        is_active=True,
        rut="11111111-1"
    )


@pytest.fixture
def mecanico_user(db):
    """Crea un usuario mecánico para pruebas."""
    return User.objects.create_user(
        username="mecanico_test",
        email="mecanico@test.com",
        password="testpass123",
        rol=User.Rol.MECANICO,
        is_active=True,
        rut="22222222-2"
    )


@pytest.fixture
def guardia_user(db):
    """Crea un usuario guardia para pruebas."""
    return User.objects.create_user(
        username="guardia_test",
        email="guardia@test.com",
        password="testpass123",
        rol=User.Rol.GUARDIA,
        is_active=True,
        rut="33333333-3"
    )


@pytest.fixture
def marca(db):
    """Crea una marca de vehículo de prueba."""
    from apps.vehicles.models import Marca
    marca, _ = Marca.objects.get_or_create(
        nombre="Toyota",
        defaults={"activa": True}
    )
    return marca


@pytest.fixture
def vehiculo(db, supervisor_user, marca):
    """Crea un vehículo de prueba."""
    return Vehiculo.objects.create(
        patente="TEST01",
        marca=marca,
        modelo="Hilux",
        anio=2020,
        tipo=Vehiculo.TIPOS[0][0],  # ELECTRICO
        estado=Vehiculo.ESTADOS[0][0],  # ACTIVO
        zona="ZONA_TEST",
        sucursal="SUCURSAL_TEST",
        supervisor=supervisor_user,
        estado_operativo="OPERATIVO"
    )


@pytest.fixture
def orden_trabajo(db, vehiculo, supervisor_user, jefe_taller_user):
    """Crea una orden de trabajo de prueba."""
    return OrdenTrabajo.objects.create(
        vehiculo=vehiculo,
        supervisor=supervisor_user,
        jefe_taller=jefe_taller_user,
        responsable=supervisor_user,  # Campo requerido
        motivo="Prueba de OT",
        estado=OrdenTrabajo.ESTADOS[0][0],  # ABIERTA
        zona="ZONA_TEST",
        apertura=datetime.now()
    )


@pytest.fixture
def api_client():
    """Cliente API de Django REST Framework."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Cliente API autenticado como admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def ingreso_vehiculo(db, vehiculo, guardia_user):
    """Crea un ingreso de vehículo de prueba."""
    from django.utils import timezone
    from datetime import datetime, time as dt_time
    # Asegurar que la fecha sea exactamente de hoy
    # El filtro usa fecha_ingreso__date=hoy, así que necesitamos que la fecha del datetime sea de hoy
    ahora = timezone.now()
    # Usar la fecha de hoy con una hora específica (12:00)
    fecha_ingreso = timezone.make_aware(datetime.combine(ahora.date(), dt_time(12, 0)))
    
    # Crear el ingreso (fecha_ingreso tiene auto_now_add=True, así que se establecerá automáticamente)
    ingreso = IngresoVehiculo.objects.create(
        vehiculo=vehiculo,
        guardia=guardia_user,
        observaciones="Ingreso de prueba",
        kilometraje=45000
    )
    
    # Actualizar la fecha manualmente después de crear (auto_now_add solo se aplica en create)
    # Usar update() para evitar que auto_now_add se active de nuevo
    IngresoVehiculo.objects.filter(id=ingreso.id).update(fecha_ingreso=fecha_ingreso)
    
    # Refrescar el objeto desde la DB para obtener la fecha actualizada
    ingreso.refresh_from_db()
    
    return ingreso


@pytest.fixture
def evidencia(db, orden_trabajo):
    """Crea una evidencia de prueba."""
    return Evidencia.objects.create(
        ot=orden_trabajo,
        url="https://s3.example.com/test.jpg",
        tipo=Evidencia.TipoEvidencia.FOTO,
        descripcion="Evidencia de prueba"
    )


@pytest.fixture
def bodega_user(db):
    """Crea un usuario BODEGA para pruebas."""
    return User.objects.create_user(
        username="bodega_test",
        email="bodega@test.com",
        password="testpass123",
        rol=User.Rol.BODEGA,
        is_active=True,
        rut="44444444-4"
    )


@pytest.fixture
def chofer_user(db):
    """Crea un usuario chofer para pruebas."""
    return User.objects.create_user(
        username="chofer_test",
        email="chofer@test.com",
        password="testpass123",
        rol=User.Rol.CHOFER,
        is_active=True,
        rut="44444444-4"
    )


@pytest.fixture
def chofer(db):
    """Crea un chofer de prueba."""
    from apps.drivers.models import Chofer
    return Chofer.objects.create(
        nombre_completo="Juan Pérez",
        rut="123456785",
        telefono="+56912345678",
        email="juan@test.com",
        activo=True
    )


@pytest.fixture
def coordinador_user(db):
    """Crea un usuario COORDINADOR_ZONA para pruebas."""
    return User.objects.create_user(
        username="coordinador_test",
        email="coordinador@test.com",
        password="testpass123",
        rol=User.Rol.COORDINADOR_ZONA,
        is_active=True,
        rut="55555555-5"
    )


@pytest.fixture
def repuesto(db):
    """Crea un repuesto de prueba."""
    from apps.inventory.models import Repuesto, Stock
    from decimal import Decimal
    repuesto = Repuesto.objects.create(
        codigo="REP001",
        nombre="Repuesto de Prueba",
        marca="Marca Test",
        categoria="MOTOR",
        precio_referencia=Decimal("100.00"),
        activo=True
    )
    # Crear stock asociado si no existe
    Stock.objects.get_or_create(
        repuesto=repuesto,
        defaults={
            "cantidad_actual": 0,
            "cantidad_minima": 10
        }
    )
    return repuesto


@pytest.fixture
def stock(db, repuesto):
    """Crea un stock de prueba."""
    from apps.inventory.models import Stock
    stock, _ = Stock.objects.get_or_create(
        repuesto=repuesto,
        defaults={
            "cantidad_actual": 50,
            "cantidad_minima": 10,
            "ubicacion": "A1-B2"
        }
    )
    return stock


@pytest.fixture
def solicitud_repuesto(db, orden_trabajo, repuesto, mecanico_user):
    """Crea una solicitud de repuesto de prueba."""
    from apps.inventory.models import SolicitudRepuesto
    return SolicitudRepuesto.objects.create(
        ot=orden_trabajo,
        repuesto=repuesto,
        cantidad_solicitada=5,
        estado=SolicitudRepuesto.Estado.PENDIENTE,
        solicitante=mecanico_user,
        motivo="Solicitud de prueba"
    )


# Fixture emergencia comentado porque la app emergencies está deshabilitada
# @pytest.fixture
# def emergencia(db, vehiculo, coordinador_user):
#     """Crea una emergencia de prueba."""
#     from apps.emergencies.models import EmergenciaRuta
#     return EmergenciaRuta.objects.create(
#         vehiculo=vehiculo,
#         solicitante=coordinador_user,
#         descripcion="Emergencia de prueba",
#         ubicacion="Ruta 5, km 100",
#         estado="SOLICITADA",
#         prioridad="ALTA"
#     )


@pytest.fixture
def agenda(db, vehiculo, coordinador_user):
    """Crea una agenda de prueba."""
    from apps.scheduling.models import Agenda
    from django.utils import timezone
    from datetime import timedelta
    return Agenda.objects.create(
        vehiculo=vehiculo,
        coordinador=coordinador_user,
        fecha_programada=timezone.now() + timedelta(days=7),
        motivo="Mantenimiento preventivo de prueba",
        tipo_mantenimiento="PREVENTIVO",
        estado="PROGRAMADA",
        zona="ZONA_TEST"
    )


@pytest.fixture
def cupo_diario(db):
    """Crea un cupo diario de prueba."""
    from apps.scheduling.models import CupoDiario
    from django.utils import timezone
    from datetime import timedelta
    fecha = (timezone.now() + timedelta(days=7)).date()
    cupo, _ = CupoDiario.objects.get_or_create(
        fecha=fecha,
        defaults={
            "cupos_totales": 10,
            "cupos_ocupados": 3,
            "zona": "ZONA_TEST"
        }
    )
    return cupo


@pytest.fixture
def presupuesto(db, orden_trabajo):
    """Crea un presupuesto de prueba."""
    from apps.workorders.models import Presupuesto
    from decimal import Decimal
    return Presupuesto.objects.create(
        ot=orden_trabajo,
        total=Decimal("0.00"),
        requiere_aprobacion=False
    )


@pytest.fixture
def notification(db, admin_user, orden_trabajo):
    """Crea una notificación de prueba."""
    from apps.notifications.models import Notification
    return Notification.objects.create(
        usuario=admin_user,
        tipo="GENERAL",
        titulo="Test Notification",
        mensaje="Test message",
        ot=orden_trabajo,
        estado="NO_LEIDA"
    )


@pytest.fixture
def checklist(db, orden_trabajo, supervisor_user):
    """Crea un checklist de prueba."""
    from apps.workorders.models import Checklist
    return Checklist.objects.create(
        ot=orden_trabajo,
        verificador=supervisor_user,
        resultado="OK",
        observaciones="Checklist de prueba"
    )
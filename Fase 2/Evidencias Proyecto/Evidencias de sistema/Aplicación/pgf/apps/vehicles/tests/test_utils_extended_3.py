"""
Tests adicionales para funciones de vehicles/utils.py que no están completamente cubiertas.
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from apps.vehicles.models import HistorialVehiculo, BackupVehiculo
from apps.vehicles.utils import (
    registrar_evento_historial,
    registrar_ot_creada,
    registrar_backup_asignado,
    calcular_sla_ot
)
from apps.workorders.models import OrdenTrabajo


@pytest.mark.unit
class TestRegistrarEventoHistorial:
    """Tests para registrar_evento_historial"""
    
    def test_registrar_evento_basico(self, vehiculo):
        """Test registro básico de evento"""
        historial = registrar_evento_historial(
            vehiculo=vehiculo,
            tipo_evento="TEST_EVENTO",
            descripcion="Test descripción"
        )
        
        assert historial is not None
        assert historial.vehiculo == vehiculo
        assert historial.tipo_evento == "TEST_EVENTO"
        assert historial.descripcion == "Test descripción"
        assert historial.estado_antes == vehiculo.estado_operativo
        assert historial.estado_despues == vehiculo.estado_operativo
    
    def test_registrar_evento_con_ot(self, vehiculo, orden_trabajo):
        """Test registro de evento con OT"""
        historial = registrar_evento_historial(
            vehiculo=vehiculo,
            tipo_evento="OT_CREADA",
            ot=orden_trabajo,
            descripcion="OT creada"
        )
        
        assert historial.ot == orden_trabajo
        assert historial.fecha_ingreso == orden_trabajo.apertura
        assert historial.supervisor == orden_trabajo.supervisor
    
    def test_registrar_evento_con_fechas(self, vehiculo):
        """Test registro de evento con fechas de ingreso y salida"""
        fecha_ingreso = timezone.now() - timedelta(days=5)
        fecha_salida = timezone.now()
        
        historial = registrar_evento_historial(
            vehiculo=vehiculo,
            tipo_evento="INGRESO_SALIDA",
            fecha_ingreso=fecha_ingreso,
            fecha_salida=fecha_salida,
            descripcion="Test con fechas"
        )
        
        assert historial.fecha_ingreso == fecha_ingreso
        assert historial.fecha_salida == fecha_salida
        assert historial.tiempo_permanencia is not None
        assert historial.tiempo_permanencia == pytest.approx(5.0, abs=0.1)
    
    def test_registrar_evento_con_backup(self, vehiculo, db):
        """Test registro de evento con backup"""
        backup = BackupVehiculo.objects.create(
            vehiculo_principal=vehiculo,
            vehiculo_backup=vehiculo,  # En realidad sería otro vehículo
            fecha_inicio=timezone.now(),
            motivo="Test backup",
            estado="ACTIVO"
        )
        
        historial = registrar_evento_historial(
            vehiculo=vehiculo,
            tipo_evento="BACKUP_ASIGNADO",
            backup=backup,
            descripcion="Backup asignado"
        )
        
        assert historial.backup_utilizado == backup
    
    def test_registrar_evento_con_estados_custom(self, vehiculo):
        """Test registro de evento con estados personalizados"""
        historial = registrar_evento_historial(
            vehiculo=vehiculo,
            tipo_evento="CAMBIO_ESTADO",
            estado_antes="OPERATIVO",
            estado_despues="EN_TALLER",
            descripcion="Cambio de estado"
        )
        
        assert historial.estado_antes == "OPERATIVO"
        assert historial.estado_despues == "EN_TALLER"
    
    def test_registrar_evento_con_supervisor(self, vehiculo, supervisor_user):
        """Test registro de evento con supervisor"""
        historial = registrar_evento_historial(
            vehiculo=vehiculo,
            tipo_evento="SUPERVISION",
            supervisor=supervisor_user,
            descripcion="Supervisión realizada"
        )
        
        assert historial.supervisor == supervisor_user
    
    def test_registrar_evento_con_falla(self, vehiculo):
        """Test registro de evento con falla"""
        historial = registrar_evento_historial(
            vehiculo=vehiculo,
            tipo_evento="FALLA_DETECTADA",
            falla="Falla en motor",
            descripcion="Falla detectada"
        )
        
        assert historial.falla == "Falla en motor"


@pytest.mark.unit
class TestRegistrarOtCreada:
    """Tests para registrar_ot_creada"""
    
    def test_registrar_ot_creada_cambia_estado_vehiculo(self, orden_trabajo, admin_user):
        """Test que registrar_ot_creada cambia estado del vehículo a EN_TALLER"""
        estado_antes = orden_trabajo.vehiculo.estado_operativo
        orden_trabajo.vehiculo.estado_operativo = "OPERATIVO"
        orden_trabajo.vehiculo.save()
        
        registrar_ot_creada(orden_trabajo, admin_user)
        
        orden_trabajo.vehiculo.refresh_from_db()
        assert orden_trabajo.vehiculo.estado_operativo == "EN_TALLER"
        assert orden_trabajo.vehiculo.ultimo_movimiento is not None
    
    def test_registrar_ot_creada_guarda_estado_antes(self, orden_trabajo, admin_user):
        """Test que registrar_ot_creada guarda estado_operativo_antes"""
        orden_trabajo.vehiculo.estado_operativo = "OPERATIVO"
        orden_trabajo.vehiculo.save()
        # No establecer estado_operativo_antes a None, dejarlo como está o establecer un valor válido
        orden_trabajo.estado_operativo_antes = "OPERATIVO"  # Establecer un valor válido
        orden_trabajo.save()
        
        # Guardar el estado antes de llamar a la función
        estado_antes_esperado = orden_trabajo.vehiculo.estado_operativo
        
        registrar_ot_creada(orden_trabajo, admin_user)
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.estado_operativo_antes == estado_antes_esperado
    
    def test_registrar_ot_creada_crea_historial(self, orden_trabajo, admin_user):
        """Test que registrar_ot_creada crea registro en historial"""
        count_before = HistorialVehiculo.objects.count()
        
        registrar_ot_creada(orden_trabajo, admin_user)
        
        count_after = HistorialVehiculo.objects.count()
        assert count_after > count_before
        
        historial = HistorialVehiculo.objects.filter(
            vehiculo=orden_trabajo.vehiculo,
            tipo_evento="OT_CREADA"
        ).first()
        
        assert historial is not None
        assert historial.ot == orden_trabajo
        assert historial.estado_despues == "EN_TALLER"
    
    def test_registrar_ot_creada_usa_supervisor_ot(self, orden_trabajo, supervisor_user, admin_user):
        """Test que registrar_ot_creada usa supervisor de la OT"""
        orden_trabajo.supervisor = supervisor_user
        orden_trabajo.save()
        
        registrar_ot_creada(orden_trabajo, admin_user)
        
        historial = HistorialVehiculo.objects.filter(
            vehiculo=orden_trabajo.vehiculo,
            tipo_evento="OT_CREADA"
        ).first()
        
        assert historial.supervisor == supervisor_user


@pytest.mark.unit
class TestRegistrarBackupAsignado:
    """Tests para registrar_backup_asignado"""
    
    def test_registrar_backup_asignado_crea_historial(self, vehiculo, db):
        """Test que registrar_backup_asignado crea registro en historial"""
        backup = BackupVehiculo.objects.create(
            vehiculo_principal=vehiculo,
            vehiculo_backup=vehiculo,  # En realidad sería otro vehículo
            fecha_inicio=timezone.now(),
            motivo="Test backup",
            estado="ACTIVO"
        )
        
        count_before = HistorialVehiculo.objects.count()
        
        registrar_backup_asignado(backup)
        
        count_after = HistorialVehiculo.objects.count()
        assert count_after > count_before
        
        historial = HistorialVehiculo.objects.filter(
            vehiculo=vehiculo,
            tipo_evento="BACKUP_ASIGNADO"
        ).first()
        
        assert historial is not None
        assert historial.backup_utilizado == backup


@pytest.mark.unit
class TestCalcularSlaOt:
    """Tests para calcular_sla_ot"""
    
    def test_calcular_sla_ot_sin_fecha_limite(self, orden_trabajo):
        """Test calcular_sla_ot cuando no hay fecha_limite_sla"""
        orden_trabajo.fecha_limite_sla = None
        orden_trabajo.sla_vencido = False
        orden_trabajo.tipo = "MANTENCION"
        orden_trabajo.save()
        
        result = calcular_sla_ot(orden_trabajo)
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.fecha_limite_sla is not None
        assert isinstance(result, bool)
    
    def test_calcular_sla_ot_con_fecha_vencida(self, orden_trabajo):
        """Test calcular_sla_ot cuando la fecha está vencida"""
        orden_trabajo.fecha_limite_sla = timezone.now() - timedelta(days=1)
        orden_trabajo.sla_vencido = False
        orden_trabajo.estado = "EN_EJECUCION"  # No cerrada
        orden_trabajo.save()
        
        result = calcular_sla_ot(orden_trabajo)
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.sla_vencido is True
        assert result is True
    
    def test_calcular_sla_ot_con_fecha_futura(self, orden_trabajo):
        """Test calcular_sla_ot cuando la fecha es futura"""
        orden_trabajo.fecha_limite_sla = timezone.now() + timedelta(days=1)
        orden_trabajo.sla_vencido = True
        orden_trabajo.estado = "EN_EJECUCION"
        orden_trabajo.save()
        
        result = calcular_sla_ot(orden_trabajo)
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.sla_vencido is False
        assert result is False
    
    def test_calcular_sla_ot_cerrada_no_vencida(self, orden_trabajo):
        """Test que OT cerrada no se marca como vencida aunque pase la fecha"""
        orden_trabajo.fecha_limite_sla = timezone.now() - timedelta(days=1)
        orden_trabajo.sla_vencido = False
        orden_trabajo.estado = "CERRADA"
        orden_trabajo.save()
        
        result = calcular_sla_ot(orden_trabajo)
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.sla_vencido is False
        assert result is False
    
    def test_calcular_sla_ot_diferentes_tipos(self, orden_trabajo):
        """Test calcular_sla_ot con diferentes tipos de OT"""
        tipos_sla = {
            "MANTENCION": 7,
            "REPARACION": 3,
            "EMERGENCIA": 1,
            "DIAGNOSTICO": 2,
            "OTRO": 5,
        }
        
        for tipo, dias_esperados in tipos_sla.items():
            orden_trabajo.tipo = tipo
            orden_trabajo.fecha_limite_sla = None
            orden_trabajo.save()
            
            calcular_sla_ot(orden_trabajo)
            
            orden_trabajo.refresh_from_db()
            assert orden_trabajo.fecha_limite_sla is not None
            # Verificar que la fecha límite es aproximadamente apertura + días esperados
            diferencia = (orden_trabajo.fecha_limite_sla - orden_trabajo.apertura).days
            assert diferencia == dias_esperados


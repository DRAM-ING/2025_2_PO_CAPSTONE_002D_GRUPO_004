# apps/vehicles/tests/test_utils.py
"""
Tests para utilidades de vehículos.
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from apps.vehicles.utils import (
    registrar_evento_historial,
    registrar_ot_creada,
    registrar_ot_cerrada,
    registrar_backup_asignado,
    calcular_sla_ot
)
from apps.vehicles.models import HistorialVehiculo, BackupVehiculo
from apps.workorders.models import OrdenTrabajo


class TestRegistrarEventoHistorial:
    """Tests para registrar_evento_historial"""
    
    @pytest.mark.unit
    def test_registrar_evento_basico(self, db, vehiculo, supervisor_user):
        """Test registrar evento básico en historial"""
        historial = registrar_evento_historial(
            vehiculo=vehiculo,
            tipo_evento="OT_CREADA",
            supervisor=supervisor_user,
            descripcion="Evento de prueba"
        )
        assert historial.vehiculo == vehiculo
        assert historial.tipo_evento == "OT_CREADA"
        assert historial.supervisor == supervisor_user
    
    @pytest.mark.unit
    def test_registrar_evento_con_ot(self, db, vehiculo, orden_trabajo, supervisor_user):
        """Test registrar evento con OT"""
        historial = registrar_evento_historial(
            vehiculo=vehiculo,
            tipo_evento="OT_CERRADA",
            ot=orden_trabajo,
            supervisor=supervisor_user,
            descripcion="OT cerrada"
        )
        assert historial.ot == orden_trabajo
        assert historial.tipo_evento == "OT_CERRADA"
    
    @pytest.mark.unit
    def test_registrar_evento_con_fechas(self, db, vehiculo, supervisor_user):
        """Test registrar evento con fechas de ingreso y salida"""
        fecha_ingreso = timezone.now()
        fecha_salida = fecha_ingreso + timedelta(days=2)
        
        historial = registrar_evento_historial(
            vehiculo=vehiculo,
            tipo_evento="OT_CERRADA",
            supervisor=supervisor_user,
            fecha_ingreso=fecha_ingreso,
            fecha_salida=fecha_salida,
            descripcion="Evento con fechas"
        )
        assert historial.fecha_ingreso == fecha_ingreso
        assert historial.fecha_salida == fecha_salida
        assert historial.tiempo_permanencia is not None
        assert historial.tiempo_permanencia == 2.0  # 2 días


class TestRegistrarOtCreada:
    """Tests para registrar_ot_creada"""
    
    @pytest.mark.unit
    def test_registrar_ot_creada(self, db, orden_trabajo, supervisor_user):
        """Test registrar OT creada en historial"""
        orden_trabajo.vehiculo.estado_operativo = "OPERATIVO"
        orden_trabajo.vehiculo.save()
        
        registrar_ot_creada(orden_trabajo, supervisor_user)
        
        # Verificar que el estado operativo cambió
        orden_trabajo.vehiculo.refresh_from_db()
        assert orden_trabajo.vehiculo.estado_operativo == "EN_TALLER"
        
        # Verificar que se creó el historial
        historial = HistorialVehiculo.objects.filter(
            vehiculo=orden_trabajo.vehiculo,
            tipo_evento="OT_CREADA"
        ).first()
        assert historial is not None
        assert historial.ot == orden_trabajo


class TestRegistrarOtCerrada:
    """Tests para registrar_ot_cerrada"""
    
    @pytest.mark.unit
    def test_registrar_ot_cerrada(self, db, orden_trabajo, supervisor_user):
        """Test registrar OT cerrada en historial"""
        from datetime import timedelta
        
        orden_trabajo.estado = "CERRADA"
        orden_trabajo.apertura = timezone.now() - timedelta(days=3)
        orden_trabajo.cierre = timezone.now()
        orden_trabajo.fecha_inicio_ejecucion = timezone.now() - timedelta(days=2)
        orden_trabajo.estado_operativo_antes = "OPERATIVO"
        orden_trabajo.vehiculo.estado_operativo = "EN_TALLER"
        orden_trabajo.vehiculo.save()
        orden_trabajo.save()
        
        registrar_ot_cerrada(orden_trabajo, supervisor_user)
        
        # Verificar que se actualizaron los tiempos
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.tiempo_total_reparacion is not None
        assert orden_trabajo.tiempo_total_reparacion > 0
        
        # Verificar que se creó el historial
        historial = HistorialVehiculo.objects.filter(
            vehiculo=orden_trabajo.vehiculo,
            tipo_evento="OT_CERRADA"
        ).first()
        assert historial is not None


class TestRegistrarBackupAsignado:
    """Tests para registrar_backup_asignado"""
    
    @pytest.mark.unit
    def test_registrar_backup_asignado(self, db, vehiculo, supervisor_user, marca):
        """Test registrar backup asignado en historial"""
        from apps.vehicles.models import Vehiculo
        
        vehiculo_backup = Vehiculo.objects.create(
            patente="BACKUP02",
            marca=marca,
            modelo="Hilux",
            anio=2020,
            tipo=Vehiculo.TIPOS[0][0],
            estado=Vehiculo.ESTADOS[0][0],
            supervisor=supervisor_user,
            estado_operativo="OPERATIVO"
        )
        
        backup = BackupVehiculo.objects.create(
            vehiculo_principal=vehiculo,
            vehiculo_backup=vehiculo_backup,
            motivo="Backup de prueba",
            supervisor=supervisor_user,
            fecha_inicio=timezone.now()
        )
        
        registrar_backup_asignado(backup)
        
        # Verificar que se creó el historial
        historial = HistorialVehiculo.objects.filter(
            vehiculo=vehiculo,
            tipo_evento="BACKUP_ASIGNADO"
        ).first()
        assert historial is not None
        assert historial.backup_utilizado == backup


class TestCalcularSlaOt:
    """Tests para calcular_sla_ot"""
    
    @pytest.mark.unit
    def test_calcular_sla_mantencion(self, db, orden_trabajo):
        """Test calcular SLA para mantención"""
        orden_trabajo.tipo = "MANTENCION"
        orden_trabajo.apertura = timezone.now()
        orden_trabajo.save()
        
        sla_vencido = calcular_sla_ot(orden_trabajo)
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.fecha_limite_sla is not None
        assert sla_vencido is False  # Recién creada, no debería estar vencida
    
    @pytest.mark.unit
    def test_calcular_sla_reparacion(self, db, orden_trabajo):
        """Test calcular SLA para reparación"""
        orden_trabajo.tipo = "REPARACION"
        orden_trabajo.apertura = timezone.now()
        orden_trabajo.save()
        
        sla_vencido = calcular_sla_ot(orden_trabajo)
        
        orden_trabajo.refresh_from_db()
        assert orden_trabajo.fecha_limite_sla is not None
        assert sla_vencido is False
    
    @pytest.mark.unit
    def test_calcular_sla_vencido(self, db, orden_trabajo):
        """Test calcular SLA vencido"""
        from datetime import timedelta
        
        orden_trabajo.tipo = "REPARACION"
        orden_trabajo.apertura = timezone.now() - timedelta(days=5)  # 5 días atrás (SLA es 3 días)
        orden_trabajo.estado = "EN_EJECUCION"
        orden_trabajo.save()
        
        sla_vencido = calcular_sla_ot(orden_trabajo)
        
        orden_trabajo.refresh_from_db()
        assert sla_vencido is True
        assert orden_trabajo.sla_vencido is True
    
    @pytest.mark.unit
    def test_calcular_sla_cerrada_no_vencido(self, db, orden_trabajo):
        """Test que OT cerrada no se marca como SLA vencido"""
        from datetime import timedelta
        
        orden_trabajo.tipo = "REPARACION"
        orden_trabajo.apertura = timezone.now() - timedelta(days=5)
        orden_trabajo.estado = "CERRADA"
        orden_trabajo.cierre = timezone.now()
        orden_trabajo.save()
        
        sla_vencido = calcular_sla_ot(orden_trabajo)
        
        orden_trabajo.refresh_from_db()
        # Aunque pasó el SLA, como está cerrada, no debería estar vencida
        assert orden_trabajo.sla_vencido is False


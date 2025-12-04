# apps/vehicles/utils.py
"""
Utilidades para gestión de vehículos, historial y backups.

Este módulo proporciona funciones helper para:
- Registrar eventos en el historial de vehículos
- Calcular tiempos de permanencia
- Gestionar backups automáticamente
"""

from django.utils import timezone
from .models import HistorialVehiculo, BackupVehiculo, Vehiculo
from apps.workorders.models import OrdenTrabajo


def registrar_evento_historial(
    vehiculo,
    tipo_evento,
    ot=None,
    supervisor=None,
    descripcion="",
    falla="",
    fecha_ingreso=None,
    fecha_salida=None,
    backup=None,
    estado_antes=None,
    estado_despues=None
):
    """
    Registra un evento en el historial de un vehículo.
    
    Parámetros:
    - vehiculo: Instancia de Vehiculo
    - tipo_evento: Tipo de evento (OT_CREADA, OT_CERRADA, etc.)
    - ot: Instancia de OrdenTrabajo (opcional)
    - supervisor: Usuario supervisor (opcional)
    - descripcion: Descripción del evento
    - falla: Falla registrada (opcional)
    - fecha_ingreso: Fecha de ingreso (opcional)
    - fecha_salida: Fecha de salida (opcional)
    - backup: Instancia de BackupVehiculo (opcional)
    - estado_antes: Estado operativo antes del evento (opcional)
    - estado_despues: Estado operativo después del evento (opcional)
    
    Retorna:
    - Instancia de HistorialVehiculo creada
    """
    # Calcular tiempo de permanencia si hay fechas
    tiempo_permanencia = None
    if fecha_ingreso and fecha_salida:
        delta = fecha_salida - fecha_ingreso
        tiempo_permanencia = delta.total_seconds() / 86400  # Convertir a días
    
    # Obtener estado operativo del vehículo si no se proporciona
    if not estado_antes:
        estado_antes = vehiculo.estado_operativo
    if not estado_despues:
        estado_despues = vehiculo.estado_operativo
    
    # Crear registro de historial
    historial = HistorialVehiculo.objects.create(
        vehiculo=vehiculo,
        ot=ot,
        tipo_evento=tipo_evento,
        fecha_ingreso=fecha_ingreso or (ot.apertura if ot else None),
        fecha_salida=fecha_salida or (ot.cierre if ot and ot.cierre else None),
        tiempo_permanencia=tiempo_permanencia,
        descripcion=descripcion,
        falla=falla,
        supervisor=supervisor or (ot.supervisor if ot else None),
        estado_antes=estado_antes,
        estado_despues=estado_despues,
        backup_utilizado=backup or (ot.backup if ot else None),
    )
    
    return historial


def registrar_ot_creada(ot, usuario_creo):
    """
    Registra en el historial cuando se crea una OT.
    
    Parámetros:
    - ot: Instancia de OrdenTrabajo
    - usuario_creo: Usuario que creó la OT
    """
    # Obtener estado operativo antes
    estado_antes = ot.vehiculo.estado_operativo
    
    # Cambiar estado operativo del vehículo a EN_TALLER
    ot.vehiculo.estado_operativo = "EN_TALLER"
    ot.vehiculo.ultimo_movimiento = timezone.now()
    ot.vehiculo.save(update_fields=["estado_operativo", "ultimo_movimiento"])
    
    # Guardar estado operativo antes en la OT
    ot.estado_operativo_antes = estado_antes
    ot.save(update_fields=["estado_operativo_antes"])
    
    # Registrar en historial
    registrar_evento_historial(
        vehiculo=ot.vehiculo,
        tipo_evento="OT_CREADA",
        ot=ot,
        supervisor=ot.supervisor or usuario_creo,
        descripcion=f"OT creada por {usuario_creo.get_full_name() or usuario_creo.username}. Motivo: {ot.motivo[:100]}",
        fecha_ingreso=ot.apertura,
        estado_antes=estado_antes,
        estado_despues="EN_TALLER",
    )


def registrar_ot_cerrada(ot, usuario_cerro):
    """
    Registra en el historial cuando se cierra una OT.
    
    Parámetros:
    - ot: Instancia de OrdenTrabajo
    - usuario_cerro: Usuario que cerró la OT
    """
    from datetime import timedelta
    
    # Calcular tiempos
    if ot.cierre and ot.apertura:
        delta_total = ot.cierre - ot.apertura
        tiempo_total_dias = delta_total.total_seconds() / 86400
        
        # Actualizar tiempos en la OT
        ot.tiempo_total_reparacion = tiempo_total_dias
        
        # Calcular tiempo en espera (desde apertura hasta inicio de ejecución)
        if ot.fecha_inicio_ejecucion:
            delta_espera = ot.fecha_inicio_ejecucion - ot.apertura
            ot.tiempo_espera = delta_espera.total_seconds() / 3600  # En horas
        else:
            ot.tiempo_espera = 0
        
        # Calcular tiempo en ejecución (desde inicio hasta cierre, restando pausas)
        if ot.fecha_inicio_ejecucion:
            from apps.workorders.models import Pausa
            # Filtrar solo pausas que están dentro del período de ejecución
            # (que se solapan con el período entre fecha_inicio_ejecucion y cierre) y que tienen fin
            # Una pausa se solapa si: inicio < cierre AND fin > fecha_inicio_ejecucion
            pausas = Pausa.objects.filter(
                ot=ot,
                fin__isnull=False
            )
            # Calcular tiempo de pausas que se solapan con el período de ejecución
            tiempo_pausas = 0
            for p in pausas:
                # Calcular el solapamiento entre la pausa y el período de ejecución
                # Una pausa se solapa si: inicio < cierre AND fin > fecha_inicio_ejecucion
                if p.inicio < ot.cierre and p.fin > ot.fecha_inicio_ejecucion:
                    inicio_solapamiento = max(p.inicio, ot.fecha_inicio_ejecucion)
                    fin_solapamiento = min(p.fin, ot.cierre)
                    if inicio_solapamiento < fin_solapamiento:
                        tiempo_pausas += (fin_solapamiento - inicio_solapamiento).total_seconds() / 3600
            
            delta_ejecucion = ot.cierre - ot.fecha_inicio_ejecucion
            tiempo_ejecucion_horas = (delta_ejecucion.total_seconds() / 3600) - tiempo_pausas
            # Redondear a 2 decimales para coincidir con el DecimalField
            from decimal import Decimal
            ot.tiempo_ejecucion = Decimal(str(max(0, round(tiempo_ejecucion_horas, 2))))  # No negativo, redondeado a 2 decimales
        else:
            ot.tiempo_ejecucion = 0
        
        ot.save(update_fields=[
            "tiempo_total_reparacion",
            "tiempo_espera",
            "tiempo_ejecucion"
        ])
    
    # Determinar nuevo estado operativo del vehículo
    # Si hay backup activo, el vehículo sigue EN_TALLER hasta devolver backup
    backup_activo = BackupVehiculo.objects.filter(
        vehiculo_principal=ot.vehiculo,
        estado="ACTIVO"
    ).exists()
    
    if backup_activo:
        estado_despues = "EN_TALLER"  # Sigue en taller hasta devolver backup
    else:
        estado_despues = "OPERATIVO"  # Vuelve a operativo
    
    # Actualizar estado operativo del vehículo
    ot.vehiculo.estado_operativo = estado_despues
    ot.vehiculo.ultimo_movimiento = timezone.now()
    ot.vehiculo.save(update_fields=["estado_operativo", "ultimo_movimiento"])
    
    # Guardar estado operativo después en la OT
    ot.estado_operativo_despues = estado_despues
    ot.causa_salida = ot.diagnostico or "OT cerrada exitosamente"
    ot.save(update_fields=["estado_operativo_despues", "causa_salida"])
    
    # Registrar en historial
    registrar_evento_historial(
        vehiculo=ot.vehiculo,
        tipo_evento="OT_CERRADA",
        ot=ot,
        supervisor=ot.supervisor or usuario_cerro,
        descripcion=f"OT cerrada por {usuario_cerro.get_full_name() or usuario_cerro.username}. Diagnóstico: {ot.diagnostico[:100] if ot.diagnostico else 'N/A'}",
        fecha_ingreso=ot.apertura,
        fecha_salida=ot.cierre,
        estado_antes=ot.estado_operativo_antes or "EN_TALLER",
        estado_despues=estado_despues,
    )
    
    # Si hay backup activo, no hacer nada más (se devolverá después)
    # Si no hay backup, el vehículo vuelve a operativo


def registrar_backup_asignado(backup):
    """
    Registra en el historial cuando se asigna un backup.
    
    Parámetros:
    - backup: Instancia de BackupVehiculo
    """
    # Registrar en historial del vehículo principal
    registrar_evento_historial(
        vehiculo=backup.vehiculo_principal,
        tipo_evento="BACKUP_ASIGNADO",
        ot=backup.ot,
        supervisor=backup.supervisor,
        descripcion=f"Backup {backup.vehiculo_backup.patente} asignado. Motivo: {backup.motivo[:100]}",
        fecha_ingreso=backup.fecha_inicio,
        backup=backup,
        estado_antes=backup.vehiculo_principal.estado_operativo,
        estado_despues="EN_TALLER",  # Sigue en taller con backup
    )


def calcular_sla_ot(ot):
    """
    Calcula si una OT excedió el SLA y actualiza el campo sla_vencido.
    
    Parámetros:
    - ot: Instancia de OrdenTrabajo
    
    Retorna:
    - True si el SLA está vencido, False en caso contrario
    """
    # SLA por defecto: 7 días para mantención, 3 días para reparación, 1 día para emergencia
    sla_dias = {
        "MANTENCION": 7,
        "REPARACION": 3,
        "EMERGENCIA": 1,
        "DIAGNOSTICO": 2,
        "OTRO": 5,
    }
    
    dias_sla = sla_dias.get(ot.tipo, 5)  # Default 5 días
    
    # Calcular fecha límite
    if not ot.fecha_limite_sla:
        ot.fecha_limite_sla = ot.apertura + timezone.timedelta(days=dias_sla)
        ot.save(update_fields=["fecha_limite_sla"])
    
    # Verificar si está vencido
    ahora = timezone.now()
    if ahora > ot.fecha_limite_sla and ot.estado != "CERRADA":
        ot.sla_vencido = True
        ot.save(update_fields=["sla_vencido"])
        return True
    else:
        ot.sla_vencido = False
        ot.save(update_fields=["sla_vencido"])
        return False


# apps/core/audit_logging.py
"""
Utilidades mejoradas para logging de auditoría y trazabilidad.

Este módulo proporciona funciones centralizadas para registrar todas las acciones
del sistema, mejorando la trazabilidad y calidad del software.

Funciones principales:
- log_audit: Registra acciones generales del sistema
- log_security_event: Registra eventos de seguridad
- log_data_change: Registra cambios en datos con before/after
- log_performance: Registra métricas de rendimiento
"""

import logging
import time
from typing import Optional, Dict, Any
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.workorders.models import Auditoria

User = get_user_model()

logger = logging.getLogger('apps.core.audit')
performance_logger = logging.getLogger('apps.core.performance')


def get_client_ip(request) -> Optional[str]:
    """
    Obtiene la dirección IP del cliente desde el request.
    
    Intenta obtener la IP real del cliente considerando proxies y load balancers.
    Revisa los headers HTTP_X_FORWARDED_FOR y REMOTE_ADDR.
    
    Args:
        request: Objeto HttpRequest de Django
    
    Returns:
        Dirección IP del cliente como string, o None si no se puede determinar
    
    Ejemplo:
        >>> ip = get_client_ip(request)
        >>> log_audit(..., ip_address=ip)
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # HTTP_X_FORWARDED_FOR puede contener múltiples IPs separadas por coma
        # La primera es generalmente la IP real del cliente
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_audit(
    usuario,
    accion: str,
    objeto_tipo: str,
    objeto_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    nivel: str = 'INFO',
    ip_address: Optional[str] = None
):
    """
    Registra una acción de auditoría en la base de datos y en logs.
    
    Esta función es el punto central para registrar todas las acciones del sistema,
    mejorando la trazabilidad y cumplimiento normativo.
    
    Args:
        usuario: Usuario que realiza la acción (puede ser None para acciones del sistema)
        accion: Nombre de la acción (ej: 'CREAR_OT', 'ACTUALIZAR_VEHICULO')
        objeto_tipo: Tipo de objeto afectado (ej: 'OrdenTrabajo', 'Vehiculo')
        objeto_id: ID del objeto afectado (opcional)
        payload: Datos adicionales en formato dict (opcional)
        nivel: Nivel de log ('INFO', 'WARNING', 'ERROR')
        ip_address: Dirección IP del cliente (opcional)
    
    Returns:
        Instancia de Auditoria creada o None si falla
    
    Ejemplo:
        >>> log_audit(
        ...     usuario=request.user,
        ...     accion="CREAR_VEHICULO",
        ...     objeto_tipo="Vehiculo",
        ...     objeto_id=str(vehiculo.id),
        ...     payload={"patente": "ABC123", "marca": "Toyota"}
        ... )
    """
    try:
        # Preparar payload con información adicional
        audit_payload = payload or {}
        if ip_address:
            audit_payload['ip_address'] = ip_address
        
        # Crear registro de auditoría
        auditoria = Auditoria.objects.create(
            usuario=usuario,
            accion=accion,
            objeto_tipo=objeto_tipo,
            objeto_id=str(objeto_id) if objeto_id else '',
            payload=audit_payload
        )
        
        # Log también en archivo para análisis
        usuario_info = f"{usuario.username} ({usuario.rol})" if usuario else "Sistema"
        log_message = (
            f"AUDIT [{accion}] Usuario: {usuario_info} | "
            f"Objeto: {objeto_tipo} | ID: {objeto_id} | Payload: {audit_payload}"
        )
        
        if nivel == 'ERROR':
            logger.error(log_message)
        elif nivel == 'WARNING':
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        return auditoria
    except Exception as e:
        # No fallar la operación principal si falla el logging
        logger.error(f"Error al registrar auditoría: {e}", exc_info=True)
        return None


def log_data_change(
    usuario,
    accion: str,
    objeto_tipo: str,
    objeto_id: str,
    cambios: Dict[str, Dict[str, Any]],
    ip_address: Optional[str] = None
):
    """
    Registra un cambio en datos con información de antes y después.
    
    Útil para rastrear modificaciones específicas en campos.
    
    Args:
        usuario: Usuario que realiza el cambio
        accion: Nombre de la acción (ej: 'ACTUALIZAR_VEHICULO')
        objeto_tipo: Tipo de objeto afectado
        objeto_id: ID del objeto afectado
        cambios: Dict con formato {campo: {"antes": valor_anterior, "despues": valor_nuevo}}
        ip_address: Dirección IP del cliente (opcional)
    
    Ejemplo:
        >>> log_data_change(
        ...     usuario=request.user,
        ...     accion="ACTUALIZAR_VEHICULO",
        ...     objeto_tipo="Vehiculo",
        ...     objeto_id=str(vehiculo.id),
        ...     cambios={
        ...         "estado": {"antes": "ACTIVO", "despues": "EN_MANTENIMIENTO"},
        ...         "kilometraje": {"antes": 50000, "despues": 51000}
        ...     }
        ... )
    """
    payload = {
        "cambios": cambios,
        "total_campos_modificados": len(cambios)
    }
    if ip_address:
        payload['ip_address'] = ip_address
    
    return log_audit(
        usuario=usuario,
        accion=accion,
        objeto_tipo=objeto_tipo,
        objeto_id=objeto_id,
        payload=payload,
        nivel='INFO',
        ip_address=ip_address
    )


def log_performance(
    operacion: str,
    tiempo_ejecucion: float,
    detalles: Optional[Dict[str, Any]] = None
):
    """
    Registra métricas de rendimiento para análisis.
    
    Args:
        operacion: Nombre de la operación (ej: 'LISTAR_OT', 'CREAR_VEHICULO')
        tiempo_ejecucion: Tiempo de ejecución en segundos
        detalles: Información adicional (número de registros, tamaño de respuesta, etc.)
    """
    try:
        log_message = f"PERFORMANCE [{operacion}] Tiempo: {tiempo_ejecucion:.3f}s"
        if detalles:
            log_message += f" | Detalles: {detalles}"
        
        # Solo loggear operaciones lentas (>1s) como WARNING
        if tiempo_ejecucion > 1.0:
            performance_logger.warning(log_message)
        else:
            performance_logger.info(log_message)
    except Exception as e:
        logger.error(f"Error al registrar métrica de rendimiento: {e}")


def performance_monitor(operacion: str):
    """
    Decorador/context manager para medir tiempo de ejecución.
    
    Uso como context manager:
        >>> with performance_monitor("LISTAR_OT"):
        ...     # código a medir
        ...     pass
    """
    class PerformanceMonitor:
        def __init__(self, op: str):
            self.operacion = op
            self.inicio = None
        
        def __enter__(self):
            self.inicio = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            tiempo = time.time() - self.inicio
            log_performance(self.operacion, tiempo)
    
    return PerformanceMonitor(operacion)


def log_security_event(
    usuario,
    evento: str,
    detalles: dict = None,
    ip_address: str = None
):
    """
    Registra un evento de seguridad.
    
    Args:
        usuario: Usuario relacionado (puede ser None para eventos anónimos)
        evento: Tipo de evento de seguridad
        detalles: Detalles adicionales
        ip_address: Dirección IP del cliente
    
    Returns:
        Instancia de Auditoria creada o None si falla
    """
    try:
        payload = detalles or {}
        if ip_address:
            payload['ip_address'] = ip_address
        
        return log_audit(
            usuario=usuario,
            accion=f"SECURITY_{evento}",
            objeto_tipo="SecurityEvent",
            payload=payload,
            nivel='WARNING',
            ip_address=ip_address
        )
    except Exception as e:
        logger.error(f"Error al registrar evento de seguridad: {e}")
        return None


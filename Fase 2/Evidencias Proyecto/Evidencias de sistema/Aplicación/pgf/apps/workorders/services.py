"""
Servicios para gestión de transiciones de estado en Órdenes de Trabajo.

Este módulo define la lógica de negocio para cambiar el estado de las OT,
asegurando que solo se permitan transiciones válidas según el flujo de trabajo.

Flujo de estados:
ABIERTA → EN_DIAGNOSTICO → EN_EJECUCION → EN_PAUSA → EN_EJECUCION → EN_QA → CERRADA
                                                      ↓
                                                  RETRABAJO → EN_EJECUCION

Relaciones:
- Importado por: apps/workorders/views.py (OrdenTrabajoViewSet)
- Usado en: apps/workorders/tasks_colacion.py (para pausas automáticas)
"""

from django.utils import timezone  # Para obtener la fecha/hora actual con timezone
from .models import OrdenTrabajo  # Modelo de Orden de Trabajo


# ==================== DEFINICIÓN DE TRANSICIONES VÁLIDAS ====================
"""
Diccionario que define las transiciones válidas entre estados.

Estructura: {estado_actual: {estados_destino_permitidos}}

Reglas de negocio:
- ABIERTA: puede ir a diagnóstico, ejecución directa, o anularse
- EN_DIAGNOSTICO: puede volver a ABIERTA (si hay error) o ir a ejecución
- EN_EJECUCION: puede pausarse, ir a QA, anularse, o marcarse como retrabajo
- EN_PAUSA: solo puede volver a ejecución o anularse
- EN_QA: puede cerrarse, volver a ejecución, o marcarse como retrabajo
- RETRABAJO: puede volver a ejecución, ir a QA, o anularse
- CERRADA: estado final, no puede cambiar
- ANULADA: estado final, no puede cambiar
"""

VALID_TRANSITIONS = {
    "ABIERTA": {"EN_DIAGNOSTICO", "EN_EJECUCION", "ANULADA"},
    # Permite diagnóstico previo o ejecución directa
    # También permite anular si es necesario
    
    "EN_DIAGNOSTICO": {"ABIERTA", "EN_EJECUCION", "ANULADA"},
    # Puede volver a ABIERTA si hay error en el diagnóstico
    # O ir directamente a ejecución si no requiere diagnóstico completo
    
    "EN_EJECUCION": {"EN_PAUSA", "EN_QA", "ANULADA", "RETRABAJO"},
    # Puede pausarse (manual o automática por colación)
    # Puede enviarse a QA cuando está lista
    # Puede anularse si es necesario
    # Puede marcarse como retrabajo desde QA (aunque normalmente viene de EN_QA)
    
    "EN_PAUSA": {"EN_EJECUCION", "ANULADA"},
    # Solo puede reanudar ejecución o anularse
    # No puede saltar directamente a QA sin reanudar
    
    "EN_QA": {"CERRADA", "EN_EJECUCION", "RETRABAJO"},
    # Puede cerrarse si pasa QA
    # Puede volver a ejecución si necesita ajustes menores
    # Puede marcarse como retrabajo si requiere trabajo significativo
    
    "RETRABAJO": {"EN_EJECUCION", "EN_QA", "ANULADA"},
    # Retrabajo puede volver a ejecución para corregir
    # O ir directamente a QA si se corrigió rápidamente
    # Puede anularse si no es viable
    
    "CERRADA": {"EN_EJECUCION"},  # Permite reabrir OT cerrada para jefe de taller
    "ANULADA": set(),  # Estado final, conjunto vacío = no puede cambiar
}


def can_transition(current: str, target: str) -> bool:
    """
    Verifica si una transición de estado es válida.
    
    Esta función valida que el cambio de estado cumpla con las reglas de negocio
    definidas en VALID_TRANSITIONS.
    
    Parámetros:
    - current: Estado actual de la OT (str)
    - target: Estado destino deseado (str)
    
    Retorna:
    - True si la transición es válida
    - False si la transición no está permitida
    
    Ejemplo:
    >>> can_transition("ABIERTA", "EN_DIAGNOSTICO")
    True
    >>> can_transition("CERRADA", "ABIERTA")
    False
    
    Uso:
    - Llamado desde transition() antes de cambiar el estado
    - Puede usarse en frontend para habilitar/deshabilitar botones
    """
    # Obtener el conjunto de estados destino permitidos para el estado actual
    # Si current no existe en VALID_TRANSITIONS, retorna set() (conjunto vacío)
    allowed_targets = VALID_TRANSITIONS.get(current, set())
    
    # Verificar si el estado destino está en el conjunto de permitidos
    return target in allowed_targets


def transition(ot, target: str):
    """
    Realiza una transición de estado en una Orden de Trabajo.
    
    Esta función:
    1. Valida que la transición sea permitida
    2. Actualiza el estado de la OT
    3. Actualiza fechas relevantes según el estado destino
    4. Guarda los cambios en la base de datos
    
    Parámetros:
    - ot: Instancia de OrdenTrabajo a modificar
    - target: Estado destino (str)
    
    Retorna:
    - Tupla (success: bool, error: str | None)
      - success=True, error=None si la transición fue exitosa
      - success=False, error="mensaje" si la transición no es válida
    
    Actualiza campos:
    - estado: siempre se actualiza
    - fecha_diagnostico: si target == "EN_DIAGNOSTICO"
    - fecha_inicio_ejecucion: si target == "EN_EJECUCION" (solo la primera vez)
    - cierre: si target == "CERRADA"
    
    Uso:
    - Llamado desde apps/workorders/views.py en acciones de OrdenTrabajoViewSet
    - Llamado desde apps/workorders/tasks_colacion.py para pausas automáticas
    """
    # Validar transición antes de proceder
    if not can_transition(ot.estado, target):
        error_msg = f"Transición inválida: {ot.estado} → {target}"
        return False, error_msg
    
    # Actualizar el estado
    ot.estado = target
    
    # Actualizar fechas según el estado destino
    # Esto permite rastrear cuándo ocurrió cada cambio de estado importante
    
    if target == "EN_DIAGNOSTICO":
        # Registrar cuándo se inició el diagnóstico
        ot.fecha_diagnostico = timezone.now()
    
    elif target == "EN_EJECUCION":
        # Solo registrar la primera vez que se inicia ejecución
        # Si ya existe, no sobrescribir (permite rastrear la fecha original)
        if not ot.fecha_inicio_ejecucion:
            ot.fecha_inicio_ejecucion = timezone.now()
    
    elif target == "CERRADA":
        # Registrar cuándo se cerró la OT
        ot.cierre = timezone.now()
    
    # Determinar qué campos actualizar en la base de datos
    # Usar update_fields para optimizar la consulta SQL
    update_fields = ["estado"]  # Siempre actualizar el estado
    
    # Agregar campos de fecha según corresponda
    if target == "EN_DIAGNOSTICO":
        update_fields.append("fecha_diagnostico")
    elif target == "EN_EJECUCION":
        update_fields.append("fecha_inicio_ejecucion")
    elif target == "CERRADA":
        update_fields.append("cierre")
    
    # Guardar solo los campos especificados (optimización)
    # Esto evita actualizar campos que no cambiaron
    ot.save(update_fields=update_fields)
    
    # Retornar éxito
    return True, None


def do_transition(ot, target: str, usuario=None):
    """
    Versión que lanza excepción en lugar de retornar tupla.
    
    Esta función es un wrapper de transition() que lanza una excepción
    si la transición falla, en lugar de retornar una tupla.
    También registra auditoría automáticamente si se proporciona un usuario.
    
    Útil cuando se quiere usar en contextos donde las excepciones
    son más apropiadas que valores de retorno.
    
    Parámetros:
    - ot: Instancia de OrdenTrabajo
    - target: Estado destino (str)
    - usuario: Usuario que realiza la transición (opcional, para auditoría)
    
    Lanza:
    - ValueError: Si la transición no es válida
    
    Uso:
    - Llamado desde código que prefiere manejar excepciones
    - Útil en transacciones atómicas donde un error debe revertir todo
    """
    # Obtener estado anterior antes de la transición
    estado_anterior = ot.estado
    
    # Intentar la transición
    ok, err = transition(ot, target)
    
    # Si falló, lanzar excepción con el mensaje de error
    if not ok:
        raise ValueError(err)
    
    # Si fue exitosa y se proporcionó usuario, registrar auditoría
    if usuario and estado_anterior != target:
        try:
            from .models import Auditoria
            Auditoria.objects.create(
                usuario=usuario,
                accion="CAMBIO_ESTADO",
                objeto_tipo="OrdenTrabajo",
                objeto_id=str(ot.id),
                payload={
                    "estado_anterior": estado_anterior,
                    "estado_nuevo": target
                }
            )
        except Exception as e:
            # No fallar la transición si falla la auditoría
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al registrar auditoría de transición para OT {ot.id}: {e}")
    
    # Si fue exitosa, no retorna nada (None implícito)


def create_work_order(data, user):
    """
    Crea una nueva Orden de Trabajo encapsulando toda la lógica de negocio.
    
    Responsabilidades:
    1. Validar permisos (JEFE_TALLER, ADMIN, GUARDIA)
    2. Crear la instancia de OT
    3. Asegurar estado inicial ABIERTA
    4. Registrar historial (SLA, creación)
    5. Enviar notificaciones
    
    Parámetros:
    - data: Diccionario con datos validados del serializer
    - user: Usuario que crea la OT
    
    Retorna:
    - Instancia de OrdenTrabajo creada
    
    Lanza:
    - PermissionError: Si el usuario no tiene permisos
    - Exception: Si falla alguna operación crítica
    """
    # 1. Validar permisos
    if user.rol not in ("JEFE_TALLER", "ADMIN", "GUARDIA"):
        raise PermissionError("Solo JEFE_TALLER, ADMIN o GUARDIA pueden crear OT.")
    
    # 2. Crear instancia (usando el diccionario de datos)
    ot = OrdenTrabajo.objects.create(**data)
    
    # 3. Asegurar estado inicial
    # Si no tiene mecánico asignado, poner en pausa automáticamente
    if not ot.mecanico:
        if ot.estado != "EN_PAUSA":
            ot.estado = "EN_PAUSA"
            ot.save(update_fields=["estado"])
    else:
        if ot.estado != "ABIERTA":
            ot.estado = "ABIERTA"
            ot.save(update_fields=["estado"])
    
    # 4. Registrar historial y SLA
    try:
        from apps.vehicles.utils import registrar_ot_creada, calcular_sla_ot
        registrar_ot_creada(ot, user)
        calcular_sla_ot(ot)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al registrar historial para OT {ot.id}: {e}")
    
    # 5. Enviar notificaciones
    try:
        from apps.notifications.utils import crear_notificacion_ot_creada
        crear_notificacion_ot_creada(ot, user)
    except Exception as e:
        # No fallar la creación si las notificaciones fallan
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al crear notificaciones para OT {ot.id}: {e}")
        
    return ot

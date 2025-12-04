# apps/workorders/tasks_colacion.py
"""
Tareas Celery para manejo automático de colación (12:30-13:15)
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import datetime, time
from .models import OrdenTrabajo, Pausa
from django.db.models import Q

logger = logging.getLogger(__name__)


@shared_task
def iniciar_colacion_automatica():
    """
    Tarea que se ejecuta a las 12:30 para iniciar colación automática
    en todas las OT que estén en EN_EJECUCION
    """
    ahora = timezone.now()
    
    # Obtener todas las OT en ejecución
    ots_en_ejecucion = OrdenTrabajo.objects.filter(
        estado="EN_EJECUCION",
        mecanico__isnull=False
    )
    
    pausas_creadas = []
    for ot in ots_en_ejecucion:
        # Verificar que no tenga una pausa activa
        pausa_activa = Pausa.objects.filter(
            ot=ot,
            fin__isnull=True,
            tipo="COLACION"
        ).exists()
        
        if not pausa_activa:
            # Crear pausa de colación automática
            pausa = Pausa.objects.create(
                ot=ot,
                usuario=ot.mecanico,
                tipo="COLACION",
                motivo="Colación automática (12:30-13:15)",
                es_automatica=True,
                inicio=ahora  # Establecer inicio explícitamente
            )
            
            # Cambiar estado de OT a EN_PAUSA
            from .services import do_transition
            try:
                do_transition(ot, "EN_PAUSA")
            except (ValueError, Exception) as e:
                # Si no puede cambiar, registrar error pero continuar
                logger.warning(f"No se pudo cambiar estado de OT {ot.id} a EN_PAUSA: {e}")
            
            pausas_creadas.append(str(pausa.id))
    
    return {
        "pausas_creadas": len(pausas_creadas),
        "pausas_ids": pausas_creadas,
        "timestamp": ahora.isoformat()
    }


@shared_task
def finalizar_colacion_automatica():
    """
    Tarea que se ejecuta a las 13:15 para finalizar colación automática
    y reanudar todas las OT
    """
    ahora = timezone.now()
    
    # Obtener todas las pausas de colación activas
    pausas_colacion = Pausa.objects.filter(
        tipo="COLACION",
        es_automatica=True,
        fin__isnull=True
    )
    
    pausas_finalizadas = []
    for pausa in pausas_colacion:
        pausa.fin = ahora
        pausa.save(update_fields=["fin"])
        
        # Reanudar OT
        ot = pausa.ot
        if ot.estado == "EN_PAUSA":
            from .services import do_transition
            try:
                do_transition(ot, "EN_EJECUCION")
            except (ValueError, Exception) as e:
                # Si no puede cambiar, registrar error pero continuar
                logger.warning(f"No se pudo cambiar estado de OT {ot.id} a EN_EJECUCION: {e}")
        
        pausas_finalizadas.append(str(pausa.id))
    
    return {
        "pausas_finalizadas": len(pausas_finalizadas),
        "pausas_ids": pausas_finalizadas,
        "timestamp": ahora.isoformat()
    }


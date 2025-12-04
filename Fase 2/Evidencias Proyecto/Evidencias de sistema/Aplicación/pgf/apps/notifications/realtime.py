# apps/notifications/realtime.py
"""
Utilidades para enviar actualizaciones en tiempo real por WebSocket.

Este módulo proporciona funciones para enviar actualizaciones de datos
(OTs, vehículos, asignaciones, etc.) en tiempo real a los usuarios conectados.
"""

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


def enviar_actualizacion_ot(ot, action="updated", usuarios=None):
    """
    Envía una actualización de OT en tiempo real por WebSocket.
    
    Parámetros:
    - ot: Instancia de OrdenTrabajo
    - action: Acción realizada ("updated", "created", "deleted", "assigned", etc.)
    - usuarios: Lista de usuarios a notificar (si None, notifica a todos los relacionados)
    
    Notifica a:
    - Mecánico asignado (si existe)
    - Supervisor
    - Jefe de Taller
    - Responsable
    - ADMIN
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        # Determinar usuarios a notificar
        if usuarios is None:
            usuarios = []
            
            # Agregar mecánico si existe
            if ot.mecanico:
                usuarios.append(ot.mecanico)
            
            # Agregar supervisor si existe
            if ot.supervisor:
                usuarios.append(ot.supervisor)
            
            # Agregar jefe de taller si existe
            if ot.jefe_taller:
                usuarios.append(ot.jefe_taller)
            
            # Agregar responsable si existe
            if ot.responsable:
                usuarios.append(ot.responsable)
            
            # Agregar ADMIN
            admins = User.objects.filter(rol="ADMIN", is_active=True)
            usuarios.extend(admins)
            
            # Eliminar duplicados
            usuarios = list(set(usuarios))
        
        # Serializar datos básicos de la OT
        ot_data = {
            "id": str(ot.id),
            "estado": ot.estado,
            "tipo": ot.tipo,
            "prioridad": ot.prioridad,
            "motivo": ot.motivo,
            "vehiculo_id": str(ot.vehiculo.id) if ot.vehiculo else None,
            "vehiculo_patente": ot.vehiculo.patente if ot.vehiculo else None,
            "mecanico_id": str(ot.mecanico.id) if ot.mecanico else None,
            "supervisor_id": str(ot.supervisor.id) if ot.supervisor else None,
            "responsable_id": str(ot.responsable.id) if ot.responsable else None,
            "chofer_id": str(ot.chofer.id) if ot.chofer else None,
            "apertura": ot.apertura.isoformat() if ot.apertura else None,
            "cierre": ot.cierre.isoformat() if ot.cierre else None,
        }
        
        # Enviar a cada usuario
        for usuario in usuarios:
            if not usuario or not usuario.is_active:
                continue
                
            group_name = f"notifications_{usuario.id}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "data_update",
                    "entity_type": "workorder",
                    "entity_id": str(ot.id),
                    "action": action,
                    "data": ot_data
                }
            )
    except Exception as e:
        logger.error(f"Error al enviar actualización de OT {ot.id} por WebSocket: {e}")


def enviar_actualizacion_vehiculo(vehiculo, action="updated", usuarios=None):
    """
    Envía una actualización de vehículo en tiempo real por WebSocket.
    
    Parámetros:
    - vehiculo: Instancia de Vehiculo
    - action: Acción realizada ("updated", "created", "deleted", etc.)
    - usuarios: Lista de usuarios a notificar (si None, notifica a todos los relacionados)
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        # Determinar usuarios a notificar
        if usuarios is None:
            usuarios = []
            
            # Agregar supervisor si existe
            if vehiculo.supervisor:
                usuarios.append(vehiculo.supervisor)
            
            # Agregar ADMIN
            admins = User.objects.filter(rol="ADMIN", is_active=True)
            usuarios.extend(admins)
            
            # Eliminar duplicados
            usuarios = list(set(usuarios))
        
        # Serializar datos básicos del vehículo
        vehiculo_data = {
            "id": str(vehiculo.id),
            "patente": vehiculo.patente,
            "marca": vehiculo.marca.nombre if vehiculo.marca else None,
            "modelo": vehiculo.modelo,
            "anio": vehiculo.anio,
            "estado": vehiculo.estado,
            "supervisor_id": str(vehiculo.supervisor.id) if vehiculo.supervisor else None,
        }
        
        # Enviar a cada usuario
        for usuario in usuarios:
            if not usuario or not usuario.is_active:
                continue
                
            group_name = f"notifications_{usuario.id}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "data_update",
                    "entity_type": "vehicle",
                    "entity_id": str(vehiculo.id),
                    "action": action,
                    "data": vehiculo_data
                }
            )
    except Exception as e:
        logger.error(f"Error al enviar actualización de vehículo {vehiculo.id} por WebSocket: {e}")


def enviar_actualizacion_asignacion(ot, mecanico, action="assigned"):
    """
    Envía una actualización de asignación en tiempo real por WebSocket.
    
    Parámetros:
    - ot: Instancia de OrdenTrabajo
    - mecanico: Instancia de User (mecánico asignado)
    - action: Acción realizada ("assigned", "unassigned", "reassigned")
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        # Usuarios a notificar: mecánico, supervisor, jefe de taller, admin
        usuarios = []
        
        if mecanico:
            usuarios.append(mecanico)
        
        if ot.supervisor:
            usuarios.append(ot.supervisor)
        
        if ot.jefe_taller:
            usuarios.append(ot.jefe_taller)
        
        admins = User.objects.filter(rol="ADMIN", is_active=True)
        usuarios.extend(admins)
        
        # Eliminar duplicados
        usuarios = list(set(usuarios))
        
        # Datos de la asignación
        asignacion_data = {
            "ot_id": str(ot.id),
            "mecanico_id": str(mecanico.id) if mecanico else None,
            "mecanico_nombre": mecanico.get_full_name() if mecanico else None,
            "estado": ot.estado,
            "vehiculo_patente": ot.vehiculo.patente if ot.vehiculo else None,
        }
        
        # Enviar a cada usuario
        for usuario in usuarios:
            if not usuario or not usuario.is_active:
                continue
                
            group_name = f"notifications_{usuario.id}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "data_update",
                    "entity_type": "assignment",
                    "entity_id": str(ot.id),
                    "action": action,
                    "data": asignacion_data
                }
            )
    except Exception as e:
        logger.error(f"Error al enviar actualización de asignación OT {ot.id} por WebSocket: {e}")


def enviar_actualizacion_evidencia(evidencia, action="created", usuarios=None):
    """
    Envía una actualización de evidencia en tiempo real por WebSocket.
    
    Parámetros:
    - evidencia: Instancia de Evidencia
    - action: Acción realizada ("created", "deleted", "updated")
    - usuarios: Lista de usuarios a notificar (si None, notifica a todos los relacionados con la OT)
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        # Si no hay OT asociada, no enviar actualización
        if not evidencia.ot:
            return
        
        # Determinar usuarios a notificar
        if usuarios is None:
            usuarios = []
            ot = evidencia.ot
            
            # Agregar mecánico si existe
            if ot.mecanico:
                usuarios.append(ot.mecanico)
            
            # Agregar supervisor si existe
            if ot.supervisor:
                usuarios.append(ot.supervisor)
            
            # Agregar jefe de taller si existe
            if ot.jefe_taller:
                usuarios.append(ot.jefe_taller)
            
            # Agregar responsable si existe
            if ot.responsable:
                usuarios.append(ot.responsable)
            
            # Agregar usuario que subió la evidencia
            if evidencia.subido_por:
                usuarios.append(evidencia.subido_por)
            
            # Agregar ADMIN
            admins = User.objects.filter(rol="ADMIN", is_active=True)
            usuarios.extend(admins)
            
            # Eliminar duplicados
            usuarios = list(set(usuarios))
        
        # Serializar datos básicos de la evidencia
        evidencia_data = {
            "id": str(evidencia.id),
            "tipo": evidencia.tipo,
            "descripcion": evidencia.descripcion,
            "ot_id": str(evidencia.ot.id) if evidencia.ot else None,
            "subido_por_id": str(evidencia.subido_por.id) if evidencia.subido_por else None,
            "subido_en": evidencia.subido_en.isoformat() if evidencia.subido_en else None,
        }
        
        # Enviar a cada usuario
        for usuario in usuarios:
            if not usuario or not usuario.is_active:
                continue
                
            group_name = f"notifications_{usuario.id}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "data_update",
                    "entity_type": "evidence",
                    "entity_id": str(evidencia.id),
                    "action": action,
                    "data": evidencia_data
                }
            )
    except Exception as e:
        logger.error(f"Error al enviar actualización de evidencia {evidencia.id} por WebSocket: {e}")


def enviar_actualizacion_comentario(comentario, action="created", usuarios=None):
    """
    Envía una actualización de comentario en tiempo real por WebSocket.
    
    Parámetros:
    - comentario: Instancia de ComentarioOT
    - action: Acción realizada ("created", "updated", "deleted")
    - usuarios: Lista de usuarios a notificar (si None, notifica a todos los relacionados con la OT)
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        # Determinar usuarios a notificar
        if usuarios is None:
            usuarios = []
            ot = comentario.ot
            
            # Agregar mecánico si existe
            if ot.mecanico:
                usuarios.append(ot.mecanico)
            
            # Agregar supervisor si existe
            if ot.supervisor:
                usuarios.append(ot.supervisor)
            
            # Agregar jefe de taller si existe
            if ot.jefe_taller:
                usuarios.append(ot.jefe_taller)
            
            # Agregar responsable si existe
            if ot.responsable:
                usuarios.append(ot.responsable)
            
            # Agregar usuario que creó el comentario
            if comentario.usuario:
                usuarios.append(comentario.usuario)
            
            # Agregar usuarios mencionados
            if comentario.menciones:
                for mencion_id in comentario.menciones:
                    try:
                        mencion_user = User.objects.get(id=mencion_id)
                        usuarios.append(mencion_user)
                    except User.DoesNotExist:
                        pass
            
            # Agregar ADMIN
            admins = User.objects.filter(rol="ADMIN", is_active=True)
            usuarios.extend(admins)
            
            # Eliminar duplicados
            usuarios = list(set(usuarios))
        
        # Serializar datos básicos del comentario
        comentario_data = {
            "id": str(comentario.id),
            "texto": comentario.texto,
            "ot_id": str(comentario.ot.id) if comentario.ot else None,
            "usuario_id": str(comentario.usuario.id) if comentario.usuario else None,
            "usuario_nombre": comentario.usuario.get_full_name() if comentario.usuario else None,
            "menciones": comentario.menciones or [],
            "creado_en": comentario.creado_en.isoformat() if comentario.creado_en else None,
        }
        
        # Enviar a cada usuario
        for usuario in usuarios:
            if not usuario or not usuario.is_active:
                continue
                
            group_name = f"notifications_{usuario.id}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "data_update",
                    "entity_type": "comment",
                    "entity_id": str(comentario.id),
                    "action": action,
                    "data": comentario_data
                }
            )
    except Exception as e:
        logger.error(f"Error al enviar actualización de comentario {comentario.id} por WebSocket: {e}")


def enviar_actualizacion_item(item, action="created", usuarios=None):
    """
    Envía una actualización de item de OT en tiempo real por WebSocket.
    
    Parámetros:
    - item: Instancia de ItemOT
    - action: Acción realizada ("created", "updated", "deleted")
    - usuarios: Lista de usuarios a notificar (si None, notifica a todos los relacionados con la OT)
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        # Determinar usuarios a notificar
        if usuarios is None:
            usuarios = []
            ot = item.ot
            
            # Agregar mecánico si existe
            if ot.mecanico:
                usuarios.append(ot.mecanico)
            
            # Agregar supervisor si existe
            if ot.supervisor:
                usuarios.append(ot.supervisor)
            
            # Agregar jefe de taller si existe
            if ot.jefe_taller:
                usuarios.append(ot.jefe_taller)
            
            # Agregar responsable si existe
            if ot.responsable:
                usuarios.append(ot.responsable)
            
            # Agregar ADMIN
            admins = User.objects.filter(rol="ADMIN", is_active=True)
            usuarios.extend(admins)
            
            # Eliminar duplicados
            usuarios = list(set(usuarios))
        
        # Serializar datos básicos del item
        item_data = {
            "id": str(item.id),
            "tipo": item.tipo,
            "descripcion": item.descripcion,
            "cantidad": item.cantidad,
            "costo_unitario": str(item.costo_unitario),
            "ot_id": str(item.ot.id) if item.ot else None,
            "repuesto_id": str(item.repuesto.id) if item.repuesto else None,
        }
        
        # Enviar a cada usuario
        for usuario in usuarios:
            if not usuario or not usuario.is_active:
                continue
                
            group_name = f"notifications_{usuario.id}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "data_update",
                    "entity_type": "item",
                    "entity_id": str(item.id),
                    "action": action,
                    "data": item_data
                }
            )
    except Exception as e:
        logger.error(f"Error al enviar actualización de item {item.id} por WebSocket: {e}")


# apps/notifications/utils.py
"""
Utilidades para crear notificaciones.

Este módulo proporciona funciones helper para crear notificaciones
automáticamente cuando ocurren eventos importantes en el sistema.
"""

from .models import Notification
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import NotificationSerializer

User = get_user_model()


def enviar_notificacion_websocket(notificacion):
    """
    Envía una notificación por WebSocket en tiempo real.
    
    Parámetros:
    - notificacion: Instancia de Notification
    
    Envía la notificación al grupo del usuario destinatario
    para que se muestre en tiempo real en el frontend.
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return  # Si no hay channel layer configurado, no hacer nada
        
        # Serializar notificación
        serializer = NotificationSerializer(notificacion)
        notification_data = serializer.data
        
        # Enviar al grupo del usuario
        group_name = f"notifications_{notificacion.usuario.id}"
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "notification_message",
                "notification": notification_data
            }
        )
    except Exception as e:
        # No fallar si hay error de WebSocket
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al enviar notificación por WebSocket {notificacion.id}: {e}")


def enviar_notificacion_email(notificacion):
    """
    Envía una notificación por email (opcional).
    
    Parámetros:
    - notificacion: Instancia de Notification
    
    Solo envía email si:
    - El usuario tiene email configurado
    - La configuración de email está habilitada
    - La notificación es importante (EVIDENCIA_SUBIDA, OT_CERRADA, etc.)
    """
    # Solo enviar email para notificaciones importantes
    tipos_importantes = [
        "EVIDENCIA_SUBIDA",
        "OT_CERRADA",
        "OT_APROBADA",
        "OT_RECHAZADA",
        "OT_RETRABAJO",
    ]
    
    if notificacion.tipo not in tipos_importantes:
        return
    
    if not notificacion.usuario.email:
        return
    
    try:
        # Obtener patente si existe OT
        patente = "N/A"
        if notificacion.ot and notificacion.ot.vehiculo:
            patente = notificacion.ot.vehiculo.patente
        
        # Crear mensaje HTML
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #003DA5;">{notificacion.titulo}</h2>
                <p>{notificacion.mensaje}</p>
                <p><strong>Vehículo:</strong> {patente}</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">Sistema PGF - Plataforma de Gestión de Flota</p>
            </div>
        </body>
        </html>
        """
        
        # Enviar email
        send_mail(
            subject=f"PGF: {notificacion.titulo}",
            message=strip_tags(html_message),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notificacion.usuario.email],
            html_message=html_message,
            fail_silently=True,  # No fallar si hay error de email
        )
    except Exception as e:
        # Registrar error pero no fallar
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al enviar email de notificación {notificacion.id}: {e}")


def crear_notificacion_evidencia(evidencia, usuario_subio):
    """
    Crea notificaciones cuando se sube una evidencia importante.
    
    Parámetros:
    - evidencia: Instancia de Evidencia
    - usuario_subio: Usuario que subió la evidencia
    
    Notifica a:
    - Supervisor de la OT (si existe)
    - Responsable de la OT (si existe)
    - ADMIN (si la evidencia es grande o importante)
    """
    ot = evidencia.ot
    usuarios_a_notificar = []
    
    # Agregar supervisor si existe
    if ot.supervisor:
        usuarios_a_notificar.append(ot.supervisor)
    
    # Agregar responsable si existe
    if ot.responsable:
        usuarios_a_notificar.append(ot.responsable)
    
    # Agregar ADMIN si la evidencia es grande (>100MB) o es un PDF/documento importante
    es_importante = (
        evidencia.tipo in ["PDF", "DOCUMENTO", "HOJA_CALCULO"] or
        (hasattr(evidencia, 'url') and 'evidencias' in evidencia.url)
    )
    
    if es_importante:
        admins = User.objects.filter(rol="ADMIN", is_active=True)
        usuarios_a_notificar.extend(admins)
    
    # Eliminar duplicados y no notificar al usuario que subió
    usuarios_a_notificar = list(set(usuarios_a_notificar))
    if usuario_subio in usuarios_a_notificar:
        usuarios_a_notificar.remove(usuario_subio)
    
    # Crear notificaciones
    notificaciones = []
    for usuario in usuarios_a_notificar:
        tipo_evidencia_display = dict(evidencia.TipoEvidencia.choices).get(evidencia.tipo, evidencia.tipo)
        
        notificacion = Notification.objects.create(
            usuario=usuario,
            tipo="EVIDENCIA_SUBIDA",
            titulo=f"Nueva evidencia en OT #{str(ot.id)[:8]}",
            mensaje=f"{usuario_subio.get_full_name() or usuario_subio.username} subió una {tipo_evidencia_display.lower()} a la OT del vehículo {ot.vehiculo.patente if ot.vehiculo else 'N/A'}. {evidencia.descripcion or ''}",
            ot=ot,
            evidencia=evidencia,
            metadata={
                "usuario_subio": usuario_subio.username,
                "tipo_evidencia": evidencia.tipo,
                "patente": ot.vehiculo.patente if ot.vehiculo else None,
            }
        )
        notificaciones.append(notificacion)
        
        # Enviar email si está configurado
        try:
            enviar_notificacion_email(notificacion)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar email para notificación {notificacion.id}: {e}")
        
        # Enviar notificación por WebSocket en tiempo real
        try:
            enviar_notificacion_websocket(notificacion)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar notificación por WebSocket {notificacion.id}: {e}")
    
    return notificaciones


def crear_notificacion_ot_creada(ot, usuario_creo):
    """
    Crea notificaciones cuando se crea una nueva OT.
    
    Notifica a:
    - Supervisor (si existe)
    - ADMIN
    - JEFE_TALLER
    """
    usuarios_a_notificar = []
    
    # Agregar supervisor si existe
    if ot.supervisor:
        usuarios_a_notificar.append(ot.supervisor)
    
    # Agregar ADMIN y JEFE_TALLER
    admins = User.objects.filter(rol__in=["ADMIN", "JEFE_TALLER"], is_active=True)
    usuarios_a_notificar.extend(admins)
    
    # Eliminar duplicados
    usuarios_a_notificar = list(set(usuarios_a_notificar))
    if usuario_creo in usuarios_a_notificar:
        usuarios_a_notificar.remove(usuario_creo)
    
    notificaciones = []
    for usuario in usuarios_a_notificar:
        notificacion = Notification.objects.create(
            usuario=usuario,
            tipo="OT_CREADA",
            titulo=f"Nueva OT creada - {ot.vehiculo.patente if ot.vehiculo else 'N/A'}",
            mensaje=f"{usuario_creo.get_full_name() or usuario_creo.username} creó una nueva OT para el vehículo {ot.vehiculo.patente if ot.vehiculo else 'N/A'}. Motivo: {ot.motivo[:100]}",
            ot=ot,
            metadata={
                "usuario_creo": usuario_creo.username,
                "patente": ot.vehiculo.patente if ot.vehiculo else None,
                "tipo": ot.tipo if hasattr(ot, 'tipo') else None,
            }
        )
        notificaciones.append(notificacion)
        enviar_notificacion_email(notificacion)
        enviar_notificacion_websocket(notificacion)
    
    return notificaciones


def crear_notificacion_ot_comentario(comentario, menciones):
    """
    Crea notificaciones cuando se agrega un comentario con menciones.
    
    Notifica a los usuarios mencionados en el comentario.
    """
    notificaciones = []
    
    for mencion in menciones:
        # Extraer ID de usuario de la mención (formato: @username o @id)
        # Por ahora, asumimos que las menciones son IDs de usuario
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Intentar obtener usuario por ID o username
            if mencion.startswith("@"):
                mencion = mencion[1:]  # Remover @
            
            usuario = None
            try:
                # Intentar por ID primero
                usuario = User.objects.get(id=mencion)
            except (User.DoesNotExist, ValueError):
                try:
                    # Intentar por username
                    usuario = User.objects.get(username=mencion)
                except User.DoesNotExist:
                    pass
            
            if usuario and usuario != comentario.usuario:
                notificacion = Notification.objects.create(
                    usuario=usuario,
                    tipo="GENERAL",
                    titulo=f"Nueva mención en OT {comentario.ot.id}",
                    mensaje=f"{comentario.usuario.get_full_name() if comentario.usuario else 'Usuario'} te mencionó en un comentario: {comentario.contenido[:100]}",
                    ot=comentario.ot,
                    metadata={
                        "comentario_id": str(comentario.id),
                        "usuario_comentario": comentario.usuario.username if comentario.usuario else None,
                    }
                )
                notificaciones.append(notificacion)
                enviar_notificacion_websocket(notificacion)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al crear notificación de mención {mencion}: {e}")
    
    return notificaciones


def crear_notificacion_ot_cerrada(ot, usuario_cerro):
    """
    Crea notificaciones cuando se cierra una OT.
    
    Notifica a:
    - Supervisor de la OT
    - ADMIN
    - SPONSOR
    - EJECUTIVO
    """
    usuarios_a_notificar = []
    
    if ot.supervisor:
        usuarios_a_notificar.append(ot.supervisor)
    
    ejecutivos = User.objects.filter(rol__in=["ADMIN", "SPONSOR", "EJECUTIVO"], is_active=True)
    usuarios_a_notificar.extend(ejecutivos)
    
    usuarios_a_notificar = list(set(usuarios_a_notificar))
    if usuario_cerro in usuarios_a_notificar:
        usuarios_a_notificar.remove(usuario_cerro)
    
    notificaciones = []
    for usuario in usuarios_a_notificar:
        notificacion = Notification.objects.create(
            usuario=usuario,
            tipo="OT_CERRADA",
            titulo=f"OT cerrada - {ot.vehiculo.patente if ot.vehiculo else 'N/A'}",
            mensaje=f"La OT del vehículo {ot.vehiculo.patente if ot.vehiculo else 'N/A'} fue cerrada por {usuario_cerro.get_full_name() or usuario_cerro.username}.",
            ot=ot,
            metadata={
                "usuario_cerro": usuario_cerro.username,
                "patente": ot.vehiculo.patente if ot.vehiculo else None,
            }
        )
        notificaciones.append(notificacion)
        enviar_notificacion_email(notificacion)
        enviar_notificacion_websocket(notificacion)
    
    return notificaciones


def crear_notificacion_ot_asignada(ot, usuario_asignado):
    """
    Crea notificaciones cuando se asigna una OT a un mecánico.
    
    Notifica al mecánico asignado.
    """
    if not usuario_asignado or usuario_asignado.rol != "MECANICO":
        return []
    
    notificacion = Notification.objects.create(
        usuario=usuario_asignado,
        tipo="OT_ASIGNADA",
        titulo=f"OT asignada - {ot.vehiculo.patente if ot.vehiculo else 'N/A'}",
        mensaje=f"Se te asignó una nueva OT para el vehículo {ot.vehiculo.patente if ot.vehiculo else 'N/A'}. Motivo: {ot.motivo[:100]}",
        ot=ot,
        metadata={
            "patente": ot.vehiculo.patente if ot.vehiculo else None,
        }
    )
    
    enviar_notificacion_websocket(notificacion)
    return [notificacion]


def crear_notificacion_ot_aprobada(ot, usuario_aprobo):
    """
    Crea notificaciones cuando se aprueba una OT.
    
    Notifica al responsable de la OT.
    """
    if not ot.responsable:
        return []
    
    notificacion = Notification.objects.create(
        usuario=ot.responsable,
        tipo="OT_APROBADA",
        titulo=f"OT aprobada - {ot.vehiculo.patente if ot.vehiculo else 'N/A'}",
        mensaje=f"La OT del vehículo {ot.vehiculo.patente if ot.vehiculo else 'N/A'} fue aprobada por {usuario_aprobo.get_full_name() or usuario_aprobo.username}.",
        ot=ot,
        metadata={
            "usuario_aprobo": usuario_aprobo.username,
            "patente": ot.vehiculo.patente if ot.vehiculo else None,
        }
    )
    
    enviar_notificacion_email(notificacion)
    enviar_notificacion_websocket(notificacion)
    return [notificacion]


def crear_notificacion_ot_rechazada(ot, usuario_rechazo):
    """
    Crea notificaciones cuando se rechaza una OT.
    
    Notifica al responsable de la OT.
    """
    if not ot.responsable:
        return []
    
    notificacion = Notification.objects.create(
        usuario=ot.responsable,
        tipo="OT_RECHAZADA",
        titulo=f"OT rechazada - {ot.vehiculo.patente if ot.vehiculo else 'N/A'}",
        mensaje=f"La OT del vehículo {ot.vehiculo.patente if ot.vehiculo else 'N/A'} fue rechazada por {usuario_rechazo.get_full_name() or usuario_rechazo.username}. Revisa los comentarios.",
        ot=ot,
        metadata={
            "usuario_rechazo": usuario_rechazo.username,
            "patente": ot.vehiculo.patente if ot.vehiculo else None,
        }
    )
    
    enviar_notificacion_email(notificacion)
    enviar_notificacion_websocket(notificacion)
    return [notificacion]


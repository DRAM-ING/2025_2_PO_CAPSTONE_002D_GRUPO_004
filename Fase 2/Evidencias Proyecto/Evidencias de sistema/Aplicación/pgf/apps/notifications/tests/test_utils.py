"""
Tests para utilidades de notificaciones.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.utils import timezone
from apps.notifications.models import Notification
from apps.notifications.utils import (
    enviar_notificacion_websocket,
    enviar_notificacion_email,
    crear_notificacion_ot_creada,
    crear_notificacion_ot_cerrada,
    crear_notificacion_ot_asignada,
    crear_notificacion_ot_aprobada,
    crear_notificacion_ot_rechazada
)


@pytest.mark.unit
class TestEnviarNotificacionWebSocket:
    """Tests para enviar_notificacion_websocket"""
    
    @patch('apps.notifications.utils.get_channel_layer')
    @patch('apps.notifications.utils.async_to_sync')
    def test_enviar_notificacion_websocket_success(self, mock_async, mock_get_layer, notification):
        """Test envío exitoso de notificación por WebSocket"""
        mock_channel_layer = MagicMock()
        mock_get_layer.return_value = mock_channel_layer
        
        enviar_notificacion_websocket(notification)
        
        mock_async.assert_called_once()
        mock_get_layer.assert_called_once()
    
    @patch('apps.notifications.utils.get_channel_layer')
    @patch('apps.notifications.utils.logger')
    def test_enviar_notificacion_websocket_no_channel_layer(self, mock_logger, mock_get_layer, notification):
        """Test que no falla si no hay channel layer"""
        mock_get_layer.return_value = None
        
        # No debería fallar
        enviar_notificacion_websocket(notification)
    
    @patch('apps.notifications.utils.get_channel_layer')
    @patch('apps.notifications.utils.async_to_sync')
    @patch('apps.notifications.utils.logger')
    def test_enviar_notificacion_websocket_error(self, mock_logger, mock_async, mock_get_layer, notification):
        """Test manejo de error en WebSocket"""
        mock_channel_layer = MagicMock()
        mock_get_layer.return_value = mock_channel_layer
        mock_async.side_effect = Exception("WebSocket error")
        
        # No debería fallar
        enviar_notificacion_websocket(notification)
        
        mock_logger.error.assert_called_once()


@pytest.mark.unit
class TestEnviarNotificacionEmail:
    """Tests para enviar_notificacion_email"""
    
    @patch('apps.notifications.utils.send_mail')
    @patch('logging.getLogger')
    def test_enviar_notificacion_email_tipo_importante(self, mock_get_logger, mock_send_mail, notification):
        """Test envío de email para tipo importante"""
        notification.tipo = "OT_CERRADA"
        notification.usuario.email = "test@example.com"
        notification.ot = Mock()
        notification.ot.vehiculo = Mock()
        notification.ot.vehiculo.patente = "TEST01"
        
        enviar_notificacion_email(notification)
        
        mock_send_mail.assert_called_once()
    
    def test_enviar_notificacion_email_tipo_no_importante(self, notification):
        """Test que no envía email para tipo no importante"""
        notification.tipo = "GENERAL"
        
        with patch('apps.notifications.utils.send_mail') as mock_send_mail:
            enviar_notificacion_email(notification)
            mock_send_mail.assert_not_called()
    
    def test_enviar_notificacion_email_sin_email(self, notification):
        """Test que no envía email si usuario no tiene email"""
        notification.tipo = "OT_CERRADA"
        notification.usuario.email = ""
        
        with patch('apps.notifications.utils.send_mail') as mock_send_mail:
            enviar_notificacion_email(notification)
            mock_send_mail.assert_not_called()
    
    @patch('apps.notifications.utils.send_mail')
    @patch('logging.getLogger')
    def test_enviar_notificacion_email_error(self, mock_get_logger, mock_send_mail, notification):
        """Test manejo de error al enviar email"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        notification.tipo = "OT_CERRADA"
        notification.usuario.email = "test@example.com"
        notification.ot = Mock()
        notification.ot.vehiculo = Mock()
        notification.ot.vehiculo.patente = "TEST01"
        mock_send_mail.side_effect = Exception("SMTP error")
        
        # No debería fallar
        enviar_notificacion_email(notification)
        
        mock_logger.error.assert_called_once()


@pytest.mark.unit
class TestCrearNotificacionOtCreada:
    """Tests para crear_notificacion_ot_creada"""
    
    def test_crear_notificacion_ot_creada_crea_notificaciones(self, orden_trabajo, admin_user, supervisor_user):
        """Test que crea notificaciones para usuarios relevantes"""
        orden_trabajo.supervisor = supervisor_user
        orden_trabajo.save()
        
        with patch('apps.notifications.utils.enviar_notificacion_email'), \
             patch('apps.notifications.utils.enviar_notificacion_websocket'):
            notificaciones = crear_notificacion_ot_creada(orden_trabajo, admin_user)
        
        assert len(notificaciones) > 0
        assert all(n.tipo == "OT_CREADA" for n in notificaciones)
    
    def test_crear_notificacion_ot_creada_no_notifica_creador(self, orden_trabajo, admin_user):
        """Test que no notifica al usuario que creó la OT"""
        orden_trabajo.supervisor = admin_user
        orden_trabajo.save()
        
        with patch('apps.notifications.utils.enviar_notificacion_email'), \
             patch('apps.notifications.utils.enviar_notificacion_websocket'):
            notificaciones = crear_notificacion_ot_creada(orden_trabajo, admin_user)
        
        # No debería notificar al creador
        assert all(n.usuario != admin_user for n in notificaciones)


@pytest.mark.unit
class TestCrearNotificacionOtCerrada:
    """Tests para crear_notificacion_ot_cerrada"""
    
    def test_crear_notificacion_ot_cerrada_crea_notificaciones(self, orden_trabajo, admin_user):
        """Test que crea notificaciones al cerrar OT"""
        orden_trabajo.estado = "CERRADA"
        orden_trabajo.cierre = timezone.now()
        orden_trabajo.save()
        
        with patch('apps.notifications.utils.enviar_notificacion_email'), \
             patch('apps.notifications.utils.enviar_notificacion_websocket'):
            notificaciones = crear_notificacion_ot_cerrada(orden_trabajo, admin_user)
        
        assert len(notificaciones) > 0
        assert all(n.tipo == "OT_CERRADA" for n in notificaciones)


@pytest.mark.unit
class TestCrearNotificacionOtAsignada:
    """Tests para crear_notificacion_ot_asignada"""
    
    def test_crear_notificacion_ot_asignada_crea_notificacion(self, orden_trabajo, mecanico_user):
        """Test que crea notificación al asignar OT a mecánico"""
        orden_trabajo.mecanico = mecanico_user
        orden_trabajo.save()
        
        with patch('apps.notifications.utils.enviar_notificacion_websocket'):
            notificaciones = crear_notificacion_ot_asignada(orden_trabajo, mecanico_user)
        
        assert len(notificaciones) == 1
        assert notificaciones[0].tipo == "OT_ASIGNADA"
        assert notificaciones[0].usuario == mecanico_user
    
    def test_crear_notificacion_ot_asignada_no_mecanico(self, orden_trabajo, supervisor_user):
        """Test que no crea notificación si no es mecánico"""
        notificaciones = crear_notificacion_ot_asignada(orden_trabajo, supervisor_user)
        
        assert len(notificaciones) == 0


@pytest.mark.unit
class TestCrearNotificacionOtAprobada:
    """Tests para crear_notificacion_ot_aprobada"""
    
    def test_crear_notificacion_ot_aprobada_crea_notificacion(self, orden_trabajo, admin_user, supervisor_user):
        """Test que crea notificación al aprobar OT"""
        orden_trabajo.responsable = supervisor_user
        orden_trabajo.save()
        
        with patch('apps.notifications.utils.enviar_notificacion_email'), \
             patch('apps.notifications.utils.enviar_notificacion_websocket'):
            notificaciones = crear_notificacion_ot_aprobada(orden_trabajo, admin_user)
        
        assert len(notificaciones) == 1
        assert notificaciones[0].tipo == "OT_APROBADA"
        assert notificaciones[0].usuario == supervisor_user
    
    def test_crear_notificacion_ot_aprobada_sin_responsable(self, orden_trabajo, admin_user):
        """Test que no crea notificación si no hay responsable"""
        orden_trabajo.responsable = None
        orden_trabajo.save()
        
        notificaciones = crear_notificacion_ot_aprobada(orden_trabajo, admin_user)
        
        assert len(notificaciones) == 0


@pytest.mark.unit
class TestCrearNotificacionOtRechazada:
    """Tests para crear_notificacion_ot_rechazada"""
    
    def test_crear_notificacion_ot_rechazada_crea_notificacion(self, orden_trabajo, admin_user, supervisor_user):
        """Test que crea notificación al rechazar OT"""
        orden_trabajo.responsable = supervisor_user
        orden_trabajo.save()
        
        with patch('apps.notifications.utils.enviar_notificacion_email'), \
             patch('apps.notifications.utils.enviar_notificacion_websocket'):
            notificaciones = crear_notificacion_ot_rechazada(orden_trabajo, admin_user)
        
        assert len(notificaciones) == 1
        assert notificaciones[0].tipo == "OT_RECHAZADA"
        assert notificaciones[0].usuario == supervisor_user
    
    def test_crear_notificacion_ot_rechazada_sin_responsable(self, orden_trabajo, admin_user):
        """Test que no crea notificación si no hay responsable"""
        orden_trabajo.responsable = None
        orden_trabajo.save()
        
        notificaciones = crear_notificacion_ot_rechazada(orden_trabajo, admin_user)
        
        assert len(notificaciones) == 0

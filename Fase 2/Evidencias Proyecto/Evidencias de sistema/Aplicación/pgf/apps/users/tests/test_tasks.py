"""
Tests para tareas asíncronas de usuarios.
"""

import pytest
from unittest.mock import patch, Mock
from django.core import mail
from apps.users.tasks import send_password_reset_email


@pytest.mark.celery
class TestSendPasswordResetEmail:
    """Tests para send_password_reset_email"""
    
    @patch('apps.users.tasks.send_mail')
    @patch('apps.users.tasks.render_to_string')
    @patch('apps.users.tasks.logger')
    def test_send_password_reset_email_success(self, mock_logger, mock_render, mock_send_mail):
        """Test envío exitoso de email de recuperación"""
        mock_render.return_value = '<html>Reset link</html>'
        mock_send_mail.return_value = True
        
        result = send_password_reset_email("test@example.com", "http://example.com/reset")
        
        assert result is True
        mock_send_mail.assert_called_once()
        mock_logger.info.assert_called_once()
    
    @patch('apps.users.tasks.send_mail')
    @patch('apps.users.tasks.render_to_string')
    @patch('apps.users.tasks.logger')
    def test_send_password_reset_email_failure(self, mock_logger, mock_render, mock_send_mail):
        """Test manejo de error al enviar email"""
        mock_render.return_value = '<html>Reset link</html>'
        mock_send_mail.side_effect = Exception("SMTP error")
        
        result = send_password_reset_email("test@example.com", "http://example.com/reset")
        
        assert result is False
        mock_logger.error.assert_called_once()
    
    @patch('apps.users.tasks.send_mail')
    @patch('apps.users.tasks.render_to_string')
    def test_send_password_reset_email_renders_template(self, mock_render, mock_send_mail):
        """Test que renderiza el template correcto"""
        mock_render.return_value = '<html>Reset link</html>'
        mock_send_mail.return_value = True
        
        send_password_reset_email("test@example.com", "http://example.com/reset?token=abc123")
        
        mock_render.assert_called_once_with(
            'users/emails/password_reset_email.html',
            {'reset_url': 'http://example.com/reset?token=abc123'}
        )
    
    @patch('apps.users.tasks.send_mail')
    @patch('apps.users.tasks.render_to_string')
    def test_send_password_reset_email_calls_send_mail(self, mock_render, mock_send_mail):
        """Test que llama a send_mail con parámetros correctos"""
        from django.conf import settings
        
        mock_render.return_value = '<html>Reset link</html>'
        mock_send_mail.return_value = True
        
        send_password_reset_email("test@example.com", "http://example.com/reset")
        
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        
        assert call_args[1]['subject'] == "Recuperación de Contraseña - PGF"
        assert call_args[1]['recipient_list'] == ["test@example.com"]
        assert call_args[1]['from_email'] == settings.DEFAULT_FROM_EMAIL
        assert 'html_message' in call_args[1]
        assert 'message' in call_args[1]


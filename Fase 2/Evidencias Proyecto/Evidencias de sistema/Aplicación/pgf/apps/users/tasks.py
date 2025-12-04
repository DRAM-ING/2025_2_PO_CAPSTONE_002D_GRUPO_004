from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_password_reset_email(email, reset_url):
    """
    Tarea asíncrona para enviar email de recuperación de contraseña.
    """
    try:
        subject = "Recuperación de Contraseña - PGF"
        html_message = render_to_string(
            'users/emails/password_reset_email.html', 
            {'reset_url': reset_url}
        )
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email de recuperación enviado a {email}")
        return True
    except Exception as e:
        logger.error(f"Error enviando email a {email}: {e}")
        return False

"""
Middleware para monitoreo y logging de requests.
"""

import time
import logging
from django.utils.deprecation import MiddlewareMixin
from apps.core.monitoring import MetricsCollector

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware para registrar todos los requests."""
    
    def process_request(self, request):
        """Registra el inicio del request."""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Registra el final del request con métricas."""
        if hasattr(request, '_start_time'):
            duration = (time.time() - request._start_time) * 1000
            
            # Registrar request
            logger.info(
                f"{request.method} {request.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.2f}ms - "
                f"IP: {self.get_client_ip(request)}"
            )
            
            # Actualizar métricas
            MetricsCollector.increment_request(success=response.status_code < 400)
            
            # Registrar errores
            if response.status_code >= 400:
                logger.warning(
                    f"Error {response.status_code} on {request.method} {request.path} - "
                    f"IP: {self.get_client_ip(request)}"
                )
        
        return response
    
    def get_client_ip(self, request):
        """Obtiene la IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware para agregar headers de seguridad."""
    
    def process_response(self, request, response):
        """Agrega headers de seguridad a la respuesta."""
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:;"
        )
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options (ya está en otro middleware, pero lo reforzamos)
        if 'X-Frame-Options' not in response:
            response['X-Frame-Options'] = 'DENY'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=()"
        )
        
        return response


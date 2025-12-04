"""
Tests para el middleware de core.
"""

import pytest
from unittest.mock import Mock, patch
from django.test import RequestFactory
from django.http import HttpResponse
from apps.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware


@pytest.mark.unit
class TestRequestLoggingMiddleware:
    """Tests para RequestLoggingMiddleware"""
    
    def test_process_request_sets_start_time(self):
        """Test que process_request establece _start_time"""
        middleware = RequestLoggingMiddleware(get_response=lambda r: HttpResponse())
        request = RequestFactory().get('/test/')
        
        result = middleware.process_request(request)
        
        assert result is None
        assert hasattr(request, '_start_time')
        assert isinstance(request._start_time, float)
    
    @patch('apps.core.middleware.logger')
    @patch('apps.core.middleware.MetricsCollector')
    def test_process_response_logs_request(self, mock_metrics, mock_logger):
        """Test que process_response registra el request"""
        middleware = RequestLoggingMiddleware(get_response=lambda r: HttpResponse())
        request = RequestFactory().get('/test/')
        request._start_time = 1000.0
        response = HttpResponse(status=200)
        
        with patch('time.time', return_value=1001.0):
            result = middleware.process_response(request, response)
        
        assert result == response
        mock_logger.info.assert_called_once()
        mock_metrics.increment_request.assert_called_once_with(success=True)
    
    @patch('apps.core.middleware.logger')
    @patch('apps.core.middleware.MetricsCollector')
    def test_process_response_logs_error(self, mock_metrics, mock_logger):
        """Test que process_response registra errores"""
        middleware = RequestLoggingMiddleware(get_response=lambda r: HttpResponse())
        request = RequestFactory().get('/test/')
        request._start_time = 1000.0
        response = HttpResponse(status=404)
        
        with patch('time.time', return_value=1001.0):
            result = middleware.process_response(request, response)
        
        assert result == response
        mock_logger.warning.assert_called_once()
        mock_metrics.increment_request.assert_called_once_with(success=False)
    
    def test_process_response_without_start_time(self):
        """Test que process_response funciona sin _start_time"""
        middleware = RequestLoggingMiddleware(get_response=lambda r: HttpResponse())
        request = RequestFactory().get('/test/')
        response = HttpResponse()
        
        result = middleware.process_response(request, response)
        
        assert result == response
    
    def test_get_client_ip_from_x_forwarded_for(self):
        """Test que get_client_ip obtiene IP de X-Forwarded-For"""
        middleware = RequestLoggingMiddleware(get_response=lambda r: HttpResponse())
        request = RequestFactory().get('/test/')
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.1, 10.0.0.1'
        
        ip = middleware.get_client_ip(request)
        
        assert ip == '192.168.1.1'
    
    def test_get_client_ip_from_remote_addr(self):
        """Test que get_client_ip obtiene IP de REMOTE_ADDR"""
        middleware = RequestLoggingMiddleware(get_response=lambda r: HttpResponse())
        request = RequestFactory().get('/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.2'
        
        ip = middleware.get_client_ip(request)
        
        assert ip == '192.168.1.2'


@pytest.mark.unit
class TestSecurityHeadersMiddleware:
    """Tests para SecurityHeadersMiddleware"""
    
    def test_process_response_adds_security_headers(self):
        """Test que process_response agrega headers de seguridad"""
        middleware = SecurityHeadersMiddleware(get_response=lambda r: HttpResponse())
        request = RequestFactory().get('/test/')
        response = HttpResponse()
        
        result = middleware.process_response(request, response)
        
        assert result == response
        assert 'Content-Security-Policy' in response
        assert 'X-Content-Type-Options' in response
        assert response['X-Content-Type-Options'] == 'nosniff'
        assert 'X-Frame-Options' in response
        assert response['X-Frame-Options'] == 'DENY'
        assert 'Referrer-Policy' in response
        assert 'Permissions-Policy' in response
    
    def test_process_response_preserves_existing_x_frame_options(self):
        """Test que process_response preserva X-Frame-Options existente"""
        middleware = SecurityHeadersMiddleware(get_response=lambda r: HttpResponse())
        request = RequestFactory().get('/test/')
        response = HttpResponse()
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        result = middleware.process_response(request, response)
        
        assert result == response
        assert response['X-Frame-Options'] == 'SAMEORIGIN'  # No se sobrescribe


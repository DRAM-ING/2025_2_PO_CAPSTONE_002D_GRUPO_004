"""
Vistas para monitoreo y salud del sistema.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from apps.core.monitoring import HealthCheck, MetricsCollector


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    """
    Endpoint de health check básico.
    
    Permite verificar el estado de salud del sistema.
    Accesible para usuarios autenticados.
    """
    checks = HealthCheck.check_all()
    
    if checks["overall_status"] == "healthy":
        return Response(checks, status=status.HTTP_200_OK)
    else:
        return Response(checks, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def metrics(request):
    """
    Endpoint para obtener métricas del sistema.
    
    Solo accesible para administradores.
    """
    metrics_data = {
        "requests": MetricsCollector.get_request_metrics(),
        "health": HealthCheck.check_all(),
        "timestamp": HealthCheck.check_all()["timestamp"],
    }
    
    return Response(metrics_data, status=status.HTTP_200_OK)


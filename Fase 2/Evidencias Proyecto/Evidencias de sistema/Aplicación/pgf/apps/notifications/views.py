# apps/notifications/views.py
"""
Vistas para el sistema de notificaciones.

Este módulo define:
- NotificationViewSet: ViewSet para gestionar notificaciones
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Notificaciones.
    
    Endpoints:
    - GET /api/v1/notifications/ → Listar notificaciones del usuario
    - GET /api/v1/notifications/{id}/ → Ver notificación
    - PATCH /api/v1/notifications/{id}/ → Actualizar notificación
    - DELETE /api/v1/notifications/{id}/ → Eliminar notificación
    
    Acciones personalizadas:
    - GET /api/v1/notifications/no-leidas/ → Obtener notificaciones no leídas
    - POST /api/v1/notifications/{id}/marcar-leida/ → Marcar como leída
    - POST /api/v1/notifications/{id}/archivar/ → Archivar notificación
    - POST /api/v1/notifications/marcar-todas-leidas/ → Marcar todas como leídas
    
    Permisos:
    - Solo usuarios autenticados pueden ver sus propias notificaciones
    
    Filtros:
    - Por estado (NO_LEIDA, LEIDA, ARCHIVADA)
    - Por tipo
    - Ordenamiento por fecha (más recientes primero)
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Retorna solo las notificaciones del usuario autenticado.
        
        Filtros opcionales:
        - estado: Filtrar por estado (NO_LEIDA, LEIDA, ARCHIVADA)
        - tipo: Filtrar por tipo de notificación
        """
        queryset = Notification.objects.filter(usuario=self.request.user)
        
        # Filtro por estado
        estado = self.request.query_params.get("estado")
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtro por tipo
        tipo = self.request.query_params.get("tipo")
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        return queryset.order_by("-creada_en")
    
    @action(detail=False, methods=["get"], url_path="no-leidas")
    def no_leidas(self, request):
        """
        Obtiene todas las notificaciones no leídas del usuario.
        
        Endpoint: GET /api/v1/notifications/no-leidas/
        
        Retorna:
        - 200: Lista de notificaciones no leídas
        """
        notificaciones = self.get_queryset().filter(estado="NO_LEIDA")
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"], url_path="marcar-leida")
    def marcar_leida(self, request, pk=None):
        """
        Marca una notificación como leída.
        
        Endpoint: POST /api/v1/notifications/{id}/marcar-leida/
        
        Retorna:
        - 200: Notificación marcada como leída
        - 404: Notificación no encontrada
        """
        notificacion = self.get_object()
        notificacion.marcar_como_leida()
        serializer = self.get_serializer(notificacion)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"], url_path="archivar")
    def archivar(self, request, pk=None):
        """
        Archiva una notificación.
        
        Endpoint: POST /api/v1/notifications/{id}/archivar/
        
        Retorna:
        - 200: Notificación archivada
        - 404: Notificación no encontrada
        """
        notificacion = self.get_object()
        notificacion.archivar()
        serializer = self.get_serializer(notificacion)
        return Response(serializer.data)
    
    @action(detail=False, methods=["post"], url_path="marcar-todas-leidas")
    def marcar_todas_leidas(self, request):
        """
        Marca todas las notificaciones no leídas del usuario como leídas.
        
        Endpoint: POST /api/v1/notifications/marcar-todas-leidas/
        
        Retorna:
        - 200: { "marcadas": cantidad de notificaciones marcadas }
        """
        notificaciones = self.get_queryset().filter(estado="NO_LEIDA")
        cantidad = notificaciones.count()
        
        for notificacion in notificaciones:
            notificacion.marcar_como_leida()
        
        return Response({"marcadas": cantidad})
    
    @action(detail=False, methods=["get"], url_path="contador")
    def contador(self, request):
        """
        Obtiene el contador de notificaciones no leídas.
        
        Endpoint: GET /api/v1/notifications/contador/
        
        Retorna:
        - 200: { "no_leidas": cantidad }
        """
        cantidad = self.get_queryset().filter(estado="NO_LEIDA").count()
        return Response({"no_leidas": cantidad})


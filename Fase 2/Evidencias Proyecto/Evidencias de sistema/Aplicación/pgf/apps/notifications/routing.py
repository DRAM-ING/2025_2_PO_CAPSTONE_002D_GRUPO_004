"""
Routing para WebSockets de notificaciones.

Define las rutas WebSocket para el sistema de notificaciones en tiempo real.
"""

from django.urls import path
from .consumers import NotificationConsumer

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]


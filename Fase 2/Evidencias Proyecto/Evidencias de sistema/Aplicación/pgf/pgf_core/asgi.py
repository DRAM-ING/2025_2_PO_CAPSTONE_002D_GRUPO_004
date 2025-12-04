"""
ASGI config for pgf_core project.

Configurado para soportar WebSockets con Django Channels.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pgf_core.settings')

# Inicializar Django ASGI application
django_asgi_app = get_asgi_application()

# Importar routing de WebSockets después de inicializar Django
from apps.notifications.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # HTTP/HTTPS requests -> Django ASGI application
    "http": django_asgi_app,
    
    # WebSocket requests -> Channels routing
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

"""
Consumers de WebSocket para notificaciones en tiempo real.

Este módulo define el consumer que maneja las conexiones WebSocket
para enviar notificaciones en tiempo real a los usuarios.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings
import jwt

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer de WebSocket para notificaciones en tiempo real.
    
    Maneja:
    - Conexión y autenticación de usuarios
    - Suscripción a notificaciones del usuario
    - Envío de notificaciones en tiempo real
    - Desconexión y limpieza
    """
    
    async def connect(self):
        """
        Maneja la conexión WebSocket.
        
        Autentica al usuario usando JWT token y lo suscribe
        a un grupo de notificaciones específico para su usuario.
        """
        # Obtener token de los query params
        token = self.scope.get("query_string", b"").decode().split("token=")[-1].split("&")[0]
        
        if not token:
            await self.close()
            return
        
        # Autenticar usuario
        user = await self.authenticate_user(token)
        if not user:
            await self.close()
            return
        
        # Guardar usuario en scope
        self.scope["user"] = user
        self.user_id = user.id
        
        # Nombre del grupo para este usuario
        self.group_name = f"notifications_{self.user_id}"
        
        # Unirse al grupo
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # Aceptar conexión
        await self.accept()
        
        # Enviar mensaje de confirmación
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "Conectado a notificaciones en tiempo real"
        }))
    
    async def disconnect(self, close_code):
        """
        Maneja la desconexión WebSocket.
        
        Remueve al usuario del grupo de notificaciones.
        """
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Maneja mensajes recibidos del cliente.
        
        Por ahora solo responde a pings para mantener la conexión viva.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get("type")
            
            if message_type == "ping":
                await self.send(text_data=json.dumps({
                    "type": "pong",
                    "message": "pong"
                }))
        except json.JSONDecodeError:
            pass
    
    async def notification_message(self, event):
        """
        Maneja el envío de notificaciones al cliente.
        
        Este método es llamado cuando se envía un mensaje al grupo
        del usuario a través de channel_layer.group_send().
        
        Parámetros:
        - event: Diccionario con los datos de la notificación
        """
        await self.send(text_data=json.dumps({
            "type": "notification",
            "notification": event["notification"]
        }))
    
    async def data_update(self, event):
        """
        Maneja el envío de actualizaciones de datos en tiempo real.
        
        Este método es llamado cuando se envía una actualización de datos
        (OT, vehículo, asignación, etc.) al grupo del usuario.
        
        Parámetros:
        - event: Diccionario con los datos de la actualización
        """
        await self.send(text_data=json.dumps({
            "type": "data_update",
            "entity_type": event.get("entity_type"),  # "workorder", "vehicle", "assignment", etc.
            "entity_id": event.get("entity_id"),
            "action": event.get("action"),  # "updated", "created", "deleted", "assigned", etc.
            "data": event.get("data")
        }))
    
    @database_sync_to_async
    def authenticate_user(self, token):
        """
        Autentica al usuario usando JWT token.
        
        Parámetros:
        - token: Token JWT como string
        
        Retorna:
        - User object si el token es válido, None en caso contrario
        """
        try:
            # Validar token
            UntypedToken(token)
            
            # Decodificar token para obtener user_id
            decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_data.get("user_id")
            
            if not user_id:
                return None
            
            # Obtener usuario
            try:
                user = User.objects.get(id=user_id, is_active=True)
                return user
            except User.DoesNotExist:
                return None
                
        except (InvalidToken, TokenError, jwt.DecodeError, jwt.InvalidTokenError):
            return None


# apps/drivers/views.py
"""
Vistas y ViewSets para gestión de choferes.

Este módulo define todos los endpoints de la API relacionados con:
- Choferes: CRUD de choferes (conductores de vehículos)
- Historial de asignaciones: Registro de asignaciones de vehículos a choferes

Relaciones:
- Usa: apps/drivers/models.py (Chofer, HistorialAsignacionVehiculo)
- Usa: apps/drivers/serializers.py (serializers para validación)
- Usa: apps/vehicles/models.py (Vehiculo)
- Conectado a: apps/drivers/urls.py

Endpoints principales:
- /api/v1/drivers/choferes/ → CRUD de choferes
- /api/v1/drivers/choferes/{id}/asignar-vehiculo/ → Asignar vehículo a chofer
- /api/v1/drivers/choferes/{id}/historial/ → Historial de asignaciones
- /api/v1/drivers/historial/ → Listar historial de asignaciones
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from .models import Chofer, HistorialAsignacionVehiculo
from .serializers import (
    ChoferSerializer, ChoferListSerializer,
    HistorialAsignacionVehiculoSerializer
)


class ChoferViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de choferes.
    
    Proporciona endpoints CRUD completos y acciones personalizadas:
    - GET /api/v1/drivers/choferes/ → Listar choferes (serializer simplificado)
    - POST /api/v1/drivers/choferes/ → Crear chofer
    - GET /api/v1/drivers/choferes/{id}/ → Ver chofer (serializer completo)
    - PUT/PATCH /api/v1/drivers/choferes/{id}/ → Editar chofer
    - DELETE /api/v1/drivers/choferes/{id}/ → Eliminar chofer
    
    Acciones personalizadas:
    - POST /api/v1/drivers/choferes/{id}/asignar-vehiculo/ → Asignar vehículo
    - GET /api/v1/drivers/choferes/{id}/historial/ → Historial de asignaciones
    
    Permisos:
    - Requiere autenticación
    
    Filtros:
    - Por activo, zona, sucursal
    - Búsqueda por nombre_completo, rut, telefono
    - Ordenamiento por nombre, fecha_ingreso, created_at
    """
    # QuerySet con optimización (select_related reduce queries)
    queryset = Chofer.objects.select_related("vehiculo_asignado").all()
    serializer_class = ChoferSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # Configuración de filtros
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["activo", "zona", "sucursal"]
    search_fields = ["nombre_completo", "rut", "telefono"]
    ordering_fields = ["nombre_completo", "fecha_ingreso", "created_at"]
    ordering = ["nombre_completo"]  # Orden por defecto
    
    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.
        
        - list: Usa ChoferListSerializer (menos campos, más rápido)
        - create/update/retrieve: Usa ChoferSerializer (todos los campos)
        """
        if self.action == "list":
            return ChoferListSerializer
        return ChoferSerializer
    
    def perform_create(self, serializer):
        """
        Crea un chofer y automáticamente crea un usuario asociado con rol CHOFER.
        
        Proceso:
        1. Guarda el chofer
        2. Crea un usuario con rol CHOFER usando el RUT y email del chofer
        3. Genera un username único basado en el RUT
        4. Crea una contraseña temporal (el admin puede cambiarla después)
        """
        from django.contrib.auth import get_user_model
        from django.db import transaction
        import secrets
        import string
        
        User = get_user_model()
        
        # Guardar el chofer primero
        chofer = serializer.save()
        
        # Crear usuario asociado si no existe
        with transaction.atomic():
            # Generar username único basado en RUT (sin guión)
            username_base = chofer.rut.replace("-", "").replace(".", "").lower()
            username = username_base
            
            # Si el username ya existe, agregar sufijo
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{username_base}{counter}"
                counter += 1
            
            # Generar contraseña temporal aleatoria
            password_chars = string.ascii_letters + string.digits + "!@#$%^&*"
            temp_password = ''.join(secrets.choice(password_chars) for _ in range(12))
            
            # Extraer nombre y apellido del nombre_completo
            nombre_parts = chofer.nombre_completo.strip().split(maxsplit=1)
            first_name = nombre_parts[0] if nombre_parts else ""
            last_name = nombre_parts[1] if len(nombre_parts) > 1 else ""
            
            # Crear o actualizar usuario
            user, created = User.objects.get_or_create(
                rut=chofer.rut,
                defaults={
                    "username": username,
                    "email": chofer.email or f"{username}@chofer.local",
                    "first_name": first_name,
                    "last_name": last_name,
                    "rol": "CHOFER",
                    "is_active": chofer.activo,
                }
            )
            
            # Si el usuario ya existía, actualizar datos
            if not created:
                user.email = chofer.email or user.email
                user.first_name = first_name or user.first_name
                user.last_name = last_name or user.last_name
                user.is_active = chofer.activo
                user.save()
            else:
                # Solo establecer contraseña si es un usuario nuevo
                user.set_password(temp_password)
                user.save()
            
            # Crear perfil si no existe
            from apps.users.models import Profile
            Profile.objects.get_or_create(
                user=user,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "notificaciones_email": True,
                    "notificaciones_sonido": True,
                }
            )
    
    @action(detail=True, methods=["post"], url_path="asignar-vehiculo")
    def asignar_vehiculo(self, request, pk=None):
        """
        Asigna un vehículo a un chofer.
        
        Endpoint: POST /api/v1/drivers/choferes/{id}/asignar-vehiculo/
        
        Permisos:
        - Requiere autenticación
        
        Proceso:
        1. Obtiene el chofer
        2. Valida que se proporcione vehiculo_id
        3. Busca el vehículo
        4. Finaliza asignación anterior (si existe)
        5. Asigna nuevo vehículo
        6. Crea registro en historial
        
        Body JSON:
        {
            "vehiculo_id": "uuid-del-vehiculo"
        }
        
        Retorna:
        - 200: Chofer serializado con vehículo asignado
        - 400: Si falta vehiculo_id
        - 404: Si el vehículo no existe
        """
        try:
            chofer = self.get_object()
            vehiculo_id = request.data.get("vehiculo_id")
            
            if not vehiculo_id:
                return Response(
                    {"detail": "Se requiere vehiculo_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Buscar vehículo
            from apps.vehicles.models import Vehiculo
            try:
                vehiculo = Vehiculo.objects.get(id=vehiculo_id)
            except Vehiculo.DoesNotExist:
                return Response(
                    {"detail": "Vehículo no encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {"detail": f"Error al buscar vehículo: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar si el vehículo ya tiene otro chofer asignado
            choferes_existentes = Chofer.objects.filter(
                vehiculo_asignado=vehiculo,
                activo=True
            ).exclude(id=chofer.id)
            
            if choferes_existentes.exists():
                # Finalizar asignaciones anteriores de otros choferes
                for chofer_existente in choferes_existentes:
                    HistorialAsignacionVehiculo.objects.filter(
                        chofer=chofer_existente,
                        vehiculo=vehiculo,
                        activa=True
                    ).update(activa=False, motivo_fin="Reasignación a otro chofer")
                    chofer_existente.vehiculo_asignado = None
                    chofer_existente.save()
            
            # Finalizar asignación anterior del chofer actual si existe
            if chofer.vehiculo_asignado:
                HistorialAsignacionVehiculo.objects.filter(
                    chofer=chofer,
                    vehiculo=chofer.vehiculo_asignado,
                    activa=True
                ).update(activa=False, motivo_fin="Reasignación")
            
            # Asignar nuevo vehículo
            chofer.vehiculo_asignado = vehiculo
            chofer.save()
            
            # Actualizar OTs abiertas del vehículo con el chofer asignado
            from apps.workorders.models import OrdenTrabajo
            from django.utils import timezone
            ots_actualizadas = OrdenTrabajo.objects.filter(
                vehiculo=vehiculo,
                estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA"]
            )
            ots_actualizadas.update(chofer=chofer)
            
            # Enviar actualizaciones en tiempo real para las OTs actualizadas
            try:
                from apps.notifications.realtime import enviar_actualizacion_ot
                for ot in ots_actualizadas:
                    enviar_actualizacion_ot(ot, action="updated")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al enviar actualización en tiempo real para OTs del vehículo {vehiculo.id}: {e}")
            
            # Enviar actualización del vehículo
            try:
                from apps.notifications.realtime import enviar_actualizacion_vehiculo
                enviar_actualizacion_vehiculo(vehiculo, action="updated")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al enviar actualización en tiempo real para vehículo {vehiculo.id}: {e}")
            
            # Crear registro en historial
            HistorialAsignacionVehiculo.objects.create(
                chofer=chofer,
                vehiculo=vehiculo,
                activa=True
            )
            
            # Serializar y retornar
            serializer = ChoferSerializer(chofer)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Capturar cualquier error inesperado y retornar JSON
            import traceback
            error_detail = str(e)
            if hasattr(e, '__traceback__'):
                error_detail = f"{str(e)}\n{traceback.format_exc()}"
            
            return Response(
                {"detail": f"Error al asignar vehículo: {error_detail}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_update(self, serializer):
        """
        Actualiza un chofer y también actualiza el usuario asociado si existe.
        Si no existe usuario, crea uno nuevo.
        """
        from django.contrib.auth import get_user_model
        import secrets
        import string
        
        User = get_user_model()
        chofer = serializer.save()
        
        # Extraer nombre y apellido del nombre_completo
        nombre_parts = chofer.nombre_completo.strip().split(maxsplit=1)
        first_name = nombre_parts[0] if nombre_parts else ""
        last_name = nombre_parts[1] if len(nombre_parts) > 1 else ""
        
        # Buscar o crear usuario asociado
        user, created = User.objects.get_or_create(
            rut=chofer.rut,
            defaults={
                "username": chofer.rut.replace("-", "").replace(".", "").lower(),
                "email": chofer.email or f"{chofer.rut.replace('-', '').replace('.', '')}@chofer.local",
                "first_name": first_name,
                "last_name": last_name,
                "rol": "CHOFER",
                "is_active": chofer.activo,
            }
        )
        
        # Si el usuario ya existía, actualizar datos
        if not created:
            user.email = chofer.email or user.email
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            user.is_active = chofer.activo
            user.save()
        else:
            # Solo establecer contraseña si es un usuario nuevo
            password_chars = string.ascii_letters + string.digits + "!@#$%^&*"
            temp_password = ''.join(secrets.choice(password_chars) for _ in range(12))
            user.set_password(temp_password)
            user.save()
        
        # Crear o actualizar perfil
        from apps.users.models import Profile
        profile, _ = Profile.objects.get_or_create(
            user=user,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "notificaciones_email": True,
                "notificaciones_sonido": True,
            }
        )
        # Actualizar perfil si ya existía
        if not _:
            profile.first_name = first_name or profile.first_name
            profile.last_name = last_name or profile.last_name
            profile.save()
    
    @action(detail=True, methods=["get"])
    def historial(self, request, pk=None):
        """
        Obtiene el historial de asignaciones de un chofer.
        
        Endpoint: GET /api/v1/drivers/choferes/{id}/historial/
        
        Permisos:
        - Requiere autenticación
        
        Retorna:
        - 200: Array de asignaciones serializadas (más recientes primero)
        
        Incluye:
        - Todas las asignaciones del chofer (activas e inactivas)
        - Información del vehículo asignado
        - Fechas de asignación y fin
        - Motivo de fin (si aplica)
        """
        chofer = self.get_object()
        
        # Obtener historial con optimización
        historial = HistorialAsignacionVehiculo.objects.filter(
            chofer=chofer
        ).select_related("vehiculo").order_by("-fecha_asignacion")
        
        serializer = HistorialAsignacionVehiculoSerializer(historial, many=True)
        return Response(serializer.data)


class HistorialAsignacionVehiculoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para historial de asignaciones.
    
    Endpoints:
    - GET /api/v1/drivers/historial/ → Listar todas las asignaciones
    - GET /api/v1/drivers/historial/{id}/ → Ver asignación específica
    
    Permisos:
    - Requiere autenticación
    
    Filtros:
    - Por chofer, vehiculo, activa
    - Ordenamiento por fecha_asignacion (más recientes primero)
    
    Nota:
    - Solo lectura (no permite crear/editar/eliminar)
    - Las asignaciones se crean automáticamente al asignar vehículo
    """
    queryset = HistorialAsignacionVehiculo.objects.select_related(
        "chofer", "vehiculo"
    ).all()
    serializer_class = HistorialAsignacionVehiculoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["chofer", "vehiculo", "activa"]
    ordering = ["-fecha_asignacion"]  # Más recientes primero

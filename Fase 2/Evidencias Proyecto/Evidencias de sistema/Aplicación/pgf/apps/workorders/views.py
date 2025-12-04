# apps/workorders/views.py
"""
Vistas y ViewSets para gestión de Órdenes de Trabajo.

Este módulo define todos los endpoints de la API relacionados con:
- Órdenes de Trabajo (OT): CRUD y transiciones de estado
- Items de OT: Repuestos y servicios
- Presupuestos: Gestión de presupuestos y aprobaciones
- Pausas: Gestión de pausas durante ejecución (incluye colación automática)
- Checklists: Control de calidad (QA)
- Evidencias: Subida de fotos/documentos a S3

Relaciones:
- Usa: apps/workorders/models.py (todos los modelos)
- Usa: apps/workorders/serializers.py (serializers para validación)
- Usa: apps/workorders/services.py (transiciones de estado)
- Usa: apps/workorders/permissions.py (WorkOrderPermission)
- Usa: apps/workorders/filters.py (OrdenTrabajoFilter)
- Conectado a: apps/workorders/urls.py

Endpoints principales:
- /api/v1/work/ordenes/ → CRUD de OT
- /api/v1/work/ordenes/{id}/diagnostico/ → Diagnóstico por Jefe de Taller
- /api/v1/work/ordenes/{id}/aprobar-asignacion/ → Aprobación de asignación
- /api/v1/work/items/ → CRUD de items
- /api/v1/work/presupuestos/ → CRUD de presupuestos
- /api/v1/work/pausas/ → CRUD de pausas
- /api/v1/work/checklists/ → CRUD de checklists
- /api/v1/work/evidencias/ → CRUD de evidencias
"""

import os  # Para variables de entorno
import uuid  # Para generar IDs únicos
import mimetypes  # Para detectar tipos MIME de archivos
import re  # Para expresiones regulares
from decimal import Decimal  # Para cálculos precisos de dinero
from urllib.parse import urlparse, urlunparse  # Para manipular URLs

import boto3  # Cliente AWS S3
from botocore.config import Config  # Configuración de boto3

from django.db import transaction  # Para transacciones atómicas
from django.db.models import Q  # Para consultas complejas con OR
from django.utils import timezone  # Para timestamps

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.views import APIView

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from drf_spectacular.utils import extend_schema  # Para documentación OpenAPI

from apps.core.serializers import EmptySerializer
from .filters import OrdenTrabajoFilter
from .permissions import WorkOrderPermission
from .services import transition, do_transition
from .serializers import OrdenTrabajoListSerializer

from .models import (
    OrdenTrabajo, ItemOT, Presupuesto, DetallePresup,
    Aprobacion, Pausa, Checklist, Evidencia, Auditoria,
    ComentarioOT, BloqueoVehiculo, VersionEvidencia
)
from .serializers import (
    OrdenTrabajoSerializer, ItemOTSerializer,
    PresupuestoSerializer, DetallePresupSerializer,
    AprobacionSerializer, PausaSerializer,
    ChecklistSerializer, EvidenciaSerializer,
    ComentarioOTSerializer, BloqueoVehiculoSerializer, VersionEvidenciaSerializer,
    AuditoriaSerializer
)


class PingView(APIView):
    """
    Vista simple para verificar que el servidor está funcionando.
    
    Endpoint: POST /api/v1/work/ping/
    
    Permisos:
    - Requiere autenticación (IsAuthenticated)
    
    Uso:
    - Healthcheck del sistema
    - Verificar que el token JWT es válido
    - Testing de conectividad
    
    Retorna:
    - 200: {"ok": True} si el servidor está funcionando
    - 401: Si no hay token o es inválido
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmptySerializer
    http_method_names = ["post"]  # Solo acepta POST

    @extend_schema(
        request=EmptySerializer,
        responses={200: None},
        description="Ping de salud autenticado"
    )
    def post(self, request, *args, **kwargs):
        """
        Retorna OK si el servidor está funcionando y el usuario está autenticado.
        
        Parámetros:
        - request: HttpRequest con usuario autenticado
        
        Retorna:
        - Response con {"ok": True}
        """
        return Response({"ok": True})


# ============== ORDENES DE TRABAJO =================
class OrdenTrabajoViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal para gestión de Órdenes de Trabajo.
    
    Proporciona endpoints CRUD completos y acciones personalizadas:
    - GET /api/v1/work/ordenes/ → Listar OT
    - POST /api/v1/work/ordenes/ → Crear OT
    - GET /api/v1/work/ordenes/{id}/ → Ver OT
    - PUT/PATCH /api/v1/work/ordenes/{id}/ → Editar OT
    - DELETE /api/v1/work/ordenes/{id}/ → Eliminar OT
    
    Acciones personalizadas:
    - POST /api/v1/work/ordenes/{id}/en-ejecucion/ → Cambiar a EN_EJECUCION
    - POST /api/v1/work/ordenes/{id}/en-qa/ → Cambiar a EN_QA
    - POST /api/v1/work/ordenes/{id}/en-pausa/ → Cambiar a EN_PAUSA
    - POST /api/v1/work/ordenes/{id}/cerrar/ → Cerrar OT
    - POST /api/v1/work/ordenes/{id}/anular/ → Anular OT
    - POST /api/v1/work/ordenes/{id}/diagnostico/ → Realizar diagnóstico
    - POST /api/v1/work/ordenes/{id}/aprobar-asignacion/ → Aprobar asignación
    - POST /api/v1/work/ordenes/{id}/retrabajo/ → Marcar como retrabajo
    
    Permisos:
    - Usa WorkOrderPermission (permisos personalizados por rol)
    
    Filtros:
    - Por estado, vehículo, supervisor, mecánico, etc.
    - Búsqueda por patente de vehículo
    - Ordenamiento por fecha, estado, etc.
    """
    # QuerySet base con optimización (select_related reduce queries)
    # select_related: para ForeignKey (una sola query)
    # prefetch_related: para relaciones reversas (ManyToMany, reverse ForeignKey)
    queryset = OrdenTrabajo.objects.select_related(
        "vehiculo", 
        "vehiculo__marca", 
        "vehiculo__supervisor",
        "responsable", 
        "mecanico", 
        "supervisor", 
        "jefe_taller", 
        "chofer"
    ).prefetch_related(
        "items",
        "evidencias",
        "comentarios",
        "pausas",
        "checklists"
    ).all().order_by("-apertura")
    serializer_class = OrdenTrabajoSerializer

    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.
        
        - list: Usa OrdenTrabajoListSerializer (optimizado para listados)
        - create/update/retrieve: Usa OrdenTrabajoSerializer (completo)
        """
        if self.action == 'list':
            return OrdenTrabajoListSerializer
        return OrdenTrabajoSerializer

    # Configuración de filtros
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = OrdenTrabajoFilter  # Usar el filtro personalizado
    ordering_fields = ["id", "apertura", "cierre", "estado"]  # Campos ordenables
    search_fields = ["vehiculo__patente"]  # Búsqueda por patente

    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario.
        
        - MECANICO: Solo OTs asignadas a él (mecanico=user)
        - CHOFER: Solo OTs de su vehículo asignado
        - ADMINISTRATIVO_TALLER: Todas las OTs del taller
        - BODEGA: OTs que requieren repuestos
        - Otros roles: Sin filtrado adicional (se aplican permisos en has_permission)
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        rol = getattr(user, "rol", None)
        
        # MECANICO: Solo OTs asignadas a él, a menos que se pida ver todas
        # NOTA: Para acciones de detalle (retrieve), se permite acceso si la OT está asignada
        # (se valida en get_object)
        if rol == "MECANICO":
            # Si se pasa el parámetro ver_todas=true, mostrar todas las OTs
            ver_todas = self.request.query_params.get('ver_todas', 'false').lower() == 'true'
            if not ver_todas:
                # Para listado, filtrar solo OTs asignadas
                # Para detalle (retrieve), el filtro se aplica pero get_object permite acceso
                return queryset.filter(mecanico=user)
            # Si ver_todas=true, no filtrar (mostrar todas)
        
        # CHOFER: Solo OTs de su vehículo asignado
        if rol == "CHOFER":
            try:
                from apps.drivers.models import Chofer
                # Buscar chofer asociado al usuario por RUT
                chofer = Chofer.objects.filter(rut=user.rut).first()
                if chofer and chofer.vehiculo_asignado:
                    # Filtrar OTs del vehículo asignado al chofer
                    return queryset.filter(vehiculo=chofer.vehiculo_asignado)
                else:
                    # Si no tiene vehículo asignado, no ver ninguna OT
                    return queryset.none()
            except Exception:
                # Si hay error, retornar queryset vacío
                return queryset.none()
        
        # ADMINISTRATIVO_TALLER: Todas las OTs del taller
        if rol == "ADMINISTRATIVO_TALLER":
            return queryset
        
        # BODEGA: OTs que requieren repuestos o tienen items de repuestos
        if rol == "BODEGA":
            # Filtrar OTs que tienen items de tipo REPUESTO o solicitudes de repuestos
            try:
                from apps.inventory.models import SolicitudRepuesto
                from apps.workorders.models import ItemOT
                
                # OTs con items de repuestos
                ot_ids_con_items_repuestos = ItemOT.objects.filter(
                    tipo="REPUESTO"
                ).values_list("ot_id", flat=True).distinct()
                
                # OTs con solicitudes de repuestos pendientes
                ot_ids_con_solicitudes = SolicitudRepuesto.objects.filter(
                    estado__in=["PENDIENTE", "APROBADA", "EN_PREPARACION"]
                ).values_list("ot_id", flat=True).distinct()
                
                # Combinar ambas listas
                ot_ids = set(ot_ids_con_items_repuestos) | set(ot_ids_con_solicitudes)
                
                if ot_ids:
                    return queryset.filter(id__in=ot_ids)
                else:
                    # Si no hay OTs con repuestos, mostrar todas (para que bodega pueda ver el estado general)
                    return queryset
            except Exception:
                # Si hay error, retornar todas las OTs
                return queryset
        
        # Otros roles: sin filtrado adicional
        return queryset
    
    def get_object(self):
        """
        Obtiene un objeto específico, permitiendo acceso a MECANICO para OTs asignadas.
        
        Para MECANICO: Si la OT no está en el queryset filtrado pero está asignada a él,
        se permite el acceso.
        """
        # Obtener el objeto usando el método base
        try:
            obj = super().get_object()
            return obj
        except OrdenTrabajo.DoesNotExist:
            # Si no se encuentra en el queryset filtrado, verificar si es MECANICO
            # y si la OT está asignada a él
            user = self.request.user
            rol = getattr(user, "rol", None)
            
            if rol == "MECANICO":
                # Intentar obtener la OT directamente si está asignada al mecánico
                pk = self.kwargs.get('pk')
                if pk:
                    try:
                        ot = OrdenTrabajo.objects.select_related(
                            "vehiculo", 
                            "vehiculo__marca", 
                            "vehiculo__supervisor",
                            "responsable", 
                            "mecanico", 
                            "supervisor", 
                            "jefe_taller", 
                            "chofer"
                        ).prefetch_related(
                            "items",
                            "evidencias",
                            "comentarios",
                            "pausas",
                            "checklists"
                        ).get(pk=pk, mecanico=user)
                        return ot
                    except OrdenTrabajo.DoesNotExist:
                        pass
            
            # Si no se encuentra, lanzar la excepción original
            from rest_framework.exceptions import NotFound
            raise NotFound("No OrdenTrabajo matches the given query.")

    def create(self, request, *args, **kwargs):
        """
        Crea una nueva OT y envía notificaciones a usuarios relevantes.
        
        Sobrescribe el método create del ModelViewSet para agregar
        lógica de notificaciones y registro de historial cuando se crea una nueva OT.
        
        Flujo según rol:
        - GUARDIA: Crea OT cuando el vehículo llega al taller, estado ABIERTA
        - JEFE_TALLER/ADMIN: Pueden crear OT, pero si ya existe una OT activa para el vehículo,
          se sugiere editar la existente en lugar de crear una nueva
        """
        # Validar permisos primero
        if request.user.rol not in ("JEFE_TALLER", "ADMIN", "GUARDIA"):
            return Response(
                {"detail": "Solo JEFE_TALLER, ADMIN o GUARDIA pueden crear OT."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar datos con el serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verificar si ya existe una OT activa para el vehículo (solo si se proporciona vehículo)
        # NOTA: JEFE_TALLER y ADMIN pueden crear OT incluso si hay una activa, pero se mostrará una advertencia
        vehiculo_id = request.data.get("vehiculo")
        ot_activa_info = None
        if vehiculo_id:
            # Buscar OTs activas para este vehículo
            ots_activas = OrdenTrabajo.objects.filter(
                vehiculo_id=vehiculo_id,
                estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA", "EN_QA"]
            ).exclude(estado="CERRADA").exclude(estado="ANULADA")
            
            if ots_activas.exists():
                ot_activa = ots_activas.first()
                ot_activa_info = {
                    "ot_id": str(ot_activa.id),
                    "ot_estado": ot_activa.estado,
                    "ot_motivo": ot_activa.motivo,
                }
                
                # Solo para GUARDIA: bloquear si ya hay OT activa (el guardia no debe crear múltiples OTs)
                # JEFE_TALLER y ADMIN pueden crear OT incluso si hay una activa (útil para casos especiales)
                if request.user.rol == "GUARDIA":
                    return Response(
                        {
                            "detail": f"Este vehículo ya cuenta con una OT activa (ID: {str(ot_activa.id)[:8]}). Por favor, edita la OT existente en lugar de crear una nueva.",
                            **ot_activa_info,
                            "sugerencia": "editar_existente"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        try:
            # Preparar datos para el serializer
            serializer_data = request.data.copy()
            
            # Si no se proporciona responsable, asignar automáticamente:
            # 1. Supervisor del vehículo si existe
            # 2. Usuario que crea la OT como fallback
            if not serializer_data.get("responsable"):
                vehiculo_id = serializer_data.get("vehiculo")
                if vehiculo_id:
                    try:
                        from apps.vehicles.models import Vehiculo
                        vehiculo = Vehiculo.objects.select_related("supervisor").get(id=vehiculo_id)
                        if vehiculo.supervisor:
                            # Usar el supervisor del vehículo como responsable
                            serializer_data["responsable"] = str(vehiculo.supervisor.id)
                        else:
                            # Si no tiene supervisor, usar el usuario que crea
                            serializer_data["responsable"] = str(request.user.id)
                    except Vehiculo.DoesNotExist:
                        # Si no se encuentra el vehículo, usar el usuario que crea
                        serializer_data["responsable"] = str(request.user.id)
                else:
                    # Si no hay vehículo, usar el usuario que crea
                    serializer_data["responsable"] = str(request.user.id)
            
            # Validar con el serializer (incluye validación de responsable obligatorio)
            serializer = self.get_serializer(data=serializer_data)
            serializer.is_valid(raise_exception=True)
            
            # Usar el método create del serializer que maneja items_data correctamente
            ot = serializer.save()
            
            # Registrar auditoría de creación
            try:
                Auditoria.objects.create(
                    usuario=request.user,
                    accion="CREAR_OT",
                    objeto_tipo="OrdenTrabajo",
                    objeto_id=str(ot.id),
                    payload={
                        "vehiculo_id": str(ot.vehiculo.id) if ot.vehiculo else None,
                        "vehiculo_patente": ot.vehiculo.patente if ot.vehiculo else None,
                        "tipo": ot.tipo,
                        "prioridad": ot.prioridad,
                        "estado": ot.estado,
                        "motivo": ot.motivo[:200] if ot.motivo else None,
                    }
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al registrar auditoría para OT {ot.id}: {e}")
            
            # Registrar historial y SLA
            try:
                from apps.vehicles.utils import registrar_ot_creada, calcular_sla_ot
                registrar_ot_creada(ot, request.user)
                calcular_sla_ot(ot)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al registrar historial para OT {ot.id}: {e}")
            
            # Enviar notificaciones
            try:
                from apps.notifications.utils import crear_notificacion_ot_creada
                crear_notificacion_ot_creada(ot, request.user)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al crear notificaciones para OT {ot.id}: {e}")
            
            # Enviar actualización en tiempo real
            try:
                from apps.notifications.realtime import enviar_actualizacion_ot
                enviar_actualizacion_ot(ot, action="created")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al enviar actualización en tiempo real para OT {ot.id}: {e}")
            
            # Retornar respuesta con la OT creada
            headers = self.get_success_headers(serializer.data)
            response_data = serializer.data
            
            # Si hay OT activa previa, incluir advertencia en la respuesta
            if ot_activa_info:
                response_data["advertencia"] = {
                    "mensaje": f"Se creó la OT, pero este vehículo ya tiene una OT activa (ID: {ot_activa_info['ot_id'][:8]}).",
                    "ot_activa": ot_activa_info,
                    "sugerencia": "Considera editar la OT existente si es para el mismo trabajo."
                }
            
            return Response(
                response_data, 
                status=status.HTTP_201_CREATED, 
                headers=headers
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creando OT: {e}", exc_info=True)
            return Response(
                {"detail": f"Error interno al crear la OT: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_update(self, serializer):
        """
        Actualiza una OT y registra auditoría.
        """
        # Obtener instancia antes de actualizar
        instance = serializer.instance
        
        # Guardar datos antiguos para comparar cambios
        old_data = {
            "estado": instance.estado,
            "prioridad": instance.prioridad,
            "motivo": instance.motivo,
        }
        
        # Guardar cambios
        ot = serializer.save()
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_ot
            enviar_actualizacion_ot(ot, action="updated")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para OT {ot.id}: {e}")
        
        # Registrar auditoría de actualización
        try:
            cambios = {}
            if old_data["estado"] != ot.estado:
                cambios["estado_anterior"] = old_data["estado"]
                cambios["estado_nuevo"] = ot.estado
            if old_data["prioridad"] != ot.prioridad:
                cambios["prioridad_anterior"] = old_data["prioridad"]
                cambios["prioridad_nuevo"] = ot.prioridad
            if old_data["motivo"] != ot.motivo:
                cambios["motivo_cambiado"] = True
            
            if cambios:
                Auditoria.objects.create(
                    usuario=self.request.user,
                    accion="ACTUALIZAR_OT",
                    objeto_tipo="OrdenTrabajo",
                    objeto_id=str(ot.id),
                    payload=cambios
                )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al registrar auditoría de actualización para OT {ot.id}: {e}")

    def update(self, request, *args, **kwargs):
        """
        Actualiza una OT con restricciones según el rol.
        
        ADMINISTRATIVO_TALLER solo puede actualizar campos administrativos:
        - fechas (apertura, cierre, fecha_compromiso)
        - costos (costo_estimado, costo_real)
        - tiempos (tiempo_estimado, tiempo_real)
        - observaciones administrativas
        
        NO puede actualizar:
        - estado (debe usar transiciones)
        - mecánico, supervisor, jefe_taller
        - diagnóstico técnico
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Logging para debugging
        import logging
        logger = logging.getLogger(__name__)
        
        # Verificar que request.data no sea Empty
        from rest_framework.request import Empty
        if isinstance(request.data, Empty):
            logger.error(f"Error: request.data es Empty para OT {instance.id}. Content-Type: {request.content_type}, Body length: {len(request.body) if hasattr(request, 'body') else 'N/A'}")
            return Response(
                {'detail': 'No se recibieron datos en la solicitud. Asegúrate de enviar JSON válido con Content-Type: application/json'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que request.data no esté vacío (dict vacío)
        if isinstance(request.data, dict) and len(request.data) == 0:
            return Response(
                {'detail': 'No se recibieron datos para actualizar. Debe proporcionar al menos un campo.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si es ADMINISTRATIVO_TALLER, restringir campos actualizables
        if request.user.rol == "ADMINISTRATIVO_TALLER":
            # Campos permitidos para ADMINISTRATIVO_TALLER
            campos_permitidos = {
                'apertura', 'cierre', 'fecha_compromiso',
                'costo_estimado', 'costo_real',
                'tiempo_estimado', 'tiempo_real',
                'observaciones', 'motivo'
            }
            
            # Filtrar datos para solo incluir campos permitidos
            data_permitida = {k: v for k, v in request.data.items() if k in campos_permitidos}
            
            # Crear nuevo request con datos filtrados
            from django.http import QueryDict
            if isinstance(request.data, QueryDict):
                request._full_data = QueryDict('', mutable=True)
                request._full_data.update(data_permitida)
            else:
                # Si es un dict normal, crear uno nuevo
                request._full_data = data_permitida.copy() if hasattr(data_permitida, 'copy') else data_permitida
        
        # Usar request._full_data si fue modificado (para ADMINISTRATIVO_TALLER), 
        # de lo contrario usar request.data
        data_to_use = getattr(request, '_full_data', None) or request.data
        
        logger.info(f"Actualizando OT {instance.id} con datos: {data_to_use}")
        
        serializer = self.get_serializer(instance, data=data_to_use, partial=partial)
        
        # Validar y capturar errores detallados
        if not serializer.is_valid():
            # Convertir received_data a algo serializable
            received_data_serializable = None
            try:
                if hasattr(data_to_use, 'items'):
                    received_data_serializable = dict(data_to_use)
                elif isinstance(data_to_use, (dict, list, str, int, float, bool, type(None))):
                    received_data_serializable = data_to_use
                else:
                    # Si no es serializable, convertir a string
                    received_data_serializable = str(type(data_to_use).__name__)
            except Exception as e:
                received_data_serializable = f"Error al serializar datos: {str(e)}"
            
            error_details = {
                'detail': 'Error de validación al actualizar la orden de trabajo',
                'errors': serializer.errors,
                'received_data': received_data_serializable
            }
            logger.error(f"Errores de validación al actualizar OT {instance.id}: {serializer.errors}")
            logger.error(f"Datos recibidos: {data_to_use}")
            return Response(error_details, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.perform_update(serializer)
        except Exception as e:
            logger.error(f"Error al actualizar OT {instance.id}: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Error al actualizar la orden de trabajo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Recargar la instancia desde la base de datos para asegurar datos actualizados
        instance.refresh_from_db()
        
        # Usar el serializer con la instancia actualizada
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        """
        Eliminar OT de forma segura.
        
        Este método se ejecuta antes de eliminar una OT.
        Limpia relaciones con módulos que pueden no estar migrados
        (inventory) para evitar errores de ForeignKey.
        
        Parámetros:
        - instance: Instancia de OrdenTrabajo a eliminar
        
        Proceso:
        1. Intenta eliminar SolicitudRepuesto relacionadas (si existe la tabla)
        2. Intenta limpiar MovimientoStock relacionados (si existe la tabla)
        3. Elimina la OT (esto elimina automáticamente items, pausas, evidencias, etc.)
        
        Nota: Usa try/except para que si las tablas no existen,
        la eliminación continúe sin errores.
        """
        try:
            # Intentar eliminar solicitudes de repuestos relacionadas
            from apps.inventory.models import SolicitudRepuesto
            SolicitudRepuesto.objects.filter(ot=instance).delete()
        except Exception:
            # Si la tabla no existe o hay error, continuar
            pass
        
        try:
            # Intentar limpiar movimientos de stock relacionados
            from apps.inventory.models import MovimientoStock
            MovimientoStock.objects.filter(ot=instance).update(ot=None)
        except Exception:
            # Si la tabla no existe o hay error, continuar
            pass
        
        # Eliminar la OT
        # Django automáticamente eliminará:
        # - Items (CASCADE)
        # - Pausas (CASCADE)
        # - Evidencias (CASCADE)
        # - Checklists (CASCADE)
        instance.delete()

    @extend_schema(request=EmptySerializer, responses={200: None})
    @action(detail=True, methods=['post'], url_path='en-ejecucion')
    def en_ejecucion(self, request, pk=None):
        """
        Cambia el estado de la OT a EN_EJECUCION.
        
        Endpoint: POST /api/v1/work/ordenes/{id}/en-ejecucion/
        
        Permisos:
        - Solo MECANICO o JEFE_TALLER
        - JEFE_TALLER puede reabrir OTs cerradas
        
        Flujo:
        1. Verifica permisos
        2. Obtiene la OT
        3. Ejecuta transición de estado (valida que sea válida)
        4. Retorna nuevo estado
        
        Retorna:
        - 200: {"estado": "EN_EJECUCION"}
        - 403: Si no tiene permisos
        - 400: Si la transición no es válida
        """
        ot = self.get_object()
        
        # Si la OT está cerrada, solo JEFE_TALLER puede reabrirla
        if ot.estado == "CERRADA":
            if request.user.rol not in ("JEFE_TALLER", "ADMIN"):
                return Response(
                    {"detail": "Solo JEFE_TALLER puede reabrir una OT cerrada."},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            # Para otros estados, MECANICO y JEFE_TALLER pueden cambiar a EN_EJECUCION
            if request.user.rol not in ("MECANICO", "JEFE_TALLER", "ADMIN"):
                return Response(
                    {"detail": "Solo MECANICO o JEFE_TALLER pueden iniciar la ejecución."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        do_transition(ot, "EN_EJECUCION", usuario=request.user)  # Valida y ejecuta transición
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_ot
            enviar_actualizacion_ot(ot, action="state_changed")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para OT {ot.id}: {e}")
        
        return Response({"estado": ot.estado})

    @extend_schema(request=EmptySerializer, responses={200: None})
    @action(detail=True, methods=['post'], url_path='en-qa')
    def en_qa(self, request, pk=None):
        """
        Cambia el estado de la OT a EN_QA (Control de Calidad).
        
        Endpoint: POST /api/v1/work/ordenes/{id}/en-qa/
        
        Permisos:
        - Solo SUPERVISOR o ADMIN
        
        Uso:
        - Cuando el mecánico termina el trabajo y necesita revisión de calidad
        
        Retorna:
        - 200: {"estado": "EN_QA"}
        - 403: Si no tiene permisos
        """
        # Solo MECANICO y JEFE_TALLER pueden mover a QA
        if request.user.rol not in ("MECANICO", "JEFE_TALLER"):
            return Response(
                {"detail": "Solo MECANICO o JEFE_TALLER pueden mover a QA."},
                status=status.HTTP_403_FORBIDDEN
            )
        ot = self.get_object()
        try:
            do_transition(ot, "EN_QA", usuario=request.user)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al cambiar estado a EN_QA para OT {ot.id}: {e}")
            return Response(
                {"detail": f"Error al cambiar estado: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_ot
            enviar_actualizacion_ot(ot, action="state_changed")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para OT {ot.id}: {e}")
        
        return Response({"estado": ot.estado})

    @extend_schema(request=EmptySerializer, responses={200: None})
    @action(detail=True, methods=['post'], url_path='en-pausa')
    @transaction.atomic
    def en_pausa(self, request, pk=None):
        """
        Cambia el estado de la OT a EN_PAUSA.
        
        Endpoint: POST /api/v1/work/ordenes/{id}/en-pausa/
        
        Permisos:
        - MECANICO, SUPERVISOR, ADMIN, JEFE_TALLER
        
        Nota:
        - Alternativa a crear una Pausa explícita
        - Útil para pausas rápidas sin necesidad de registrar motivo
        
        Retorna:
        - 200: {"estado": "EN_PAUSA"}
        - 403: Si no tiene permisos
        """
        # Solo MECANICO y JEFE_TALLER pueden pausar
        if request.user.rol not in ("MECANICO", "JEFE_TALLER"):
            return Response(
                {"detail": "Solo MECANICO o JEFE_TALLER pueden pausar OT."},
                status=status.HTTP_403_FORBIDDEN
            )
        ot = self.get_object()
        do_transition(ot, "EN_PAUSA", usuario=request.user)
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_ot
            enviar_actualizacion_ot(ot, action="state_changed")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para OT {ot.id}: {e}")
        
        return Response({"estado": ot.estado})

    @extend_schema(request=EmptySerializer, responses={200: None})
    @action(detail=True, methods=['post'], url_path='esperando-repuestos')
    @transaction.atomic
    def esperando_repuestos(self, request, pk=None):
        """
        Marca la OT como esperando repuestos (pausa por falta de repuestos).
        
        Endpoint: POST /api/v1/work/ordenes/{id}/esperando-repuestos/
        
        Permisos:
        - Solo MECANICO o JEFE_TALLER
        
        Flujo:
        1. Verifica permisos
        2. Obtiene la OT
        3. Cambia estado a EN_PAUSA (si no está ya en pausa)
        4. Retorna nuevo estado
        
        Retorna:
        - 200: {"estado": "EN_PAUSA", "mensaje": "OT pausada esperando repuestos"}
        - 403: Si no tiene permisos
        """
        # Solo MECANICO y JEFE_TALLER pueden marcar como esperando repuestos
        if request.user.rol not in ("MECANICO", "JEFE_TALLER", "ADMIN"):
            return Response(
                {"detail": "Solo MECANICO o JEFE_TALLER pueden marcar OT como esperando repuestos."},
                status=status.HTTP_403_FORBIDDEN
            )
        ot = self.get_object()
        
        # Si no está en pausa, cambiar a EN_PAUSA
        if ot.estado != "EN_PAUSA":
            do_transition(ot, "EN_PAUSA", usuario=request.user)
        
        # Registrar auditoría
        try:
            Auditoria.objects.create(
                usuario=request.user,
                accion="OT_ESPERANDO_REPUESTOS",
                objeto_tipo="OrdenTrabajo",
                objeto_id=str(ot.id),
                payload={"motivo": "Esperando repuestos"}
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al registrar auditoría de espera de repuestos para OT {ot.id}: {e}")
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_ot
            enviar_actualizacion_ot(ot, action="state_changed")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para OT {ot.id}: {e}")
        
        return Response({
            "estado": ot.estado,
            "mensaje": "OT pausada esperando repuestos"
        })

    @extend_schema(request=EmptySerializer, responses={200: None})
    @action(detail=True, methods=['post'], url_path='cerrar')
    @transaction.atomic
    def cerrar(self, request, pk=None):
        """
        Cierra la OT definitivamente.
        
        Endpoint: POST /api/v1/work/ordenes/{id}/cerrar/
        
        Permisos:
        - Solo SUPERVISOR, ADMIN o JEFE_TALLER
        
        Requisitos:
        - La OT debe estar en EN_QA o CERRADA
        - Debe incluir fecha_cierre, diagnostico_final y estado_final = CERRADA
        
        Proceso:
        1. Valida estado
        2. Valida campos obligatorios (fecha_cierre, diagnostico_final)
        3. Ejecuta transición a CERRADA
        4. Genera PDF de cierre (tarea Celery asíncrona)
        5. Registra auditoría
        
        Retorna:
        - 200: {"estado": "CERRADA", "cierre": "2024-01-15T10:30:00Z"}
        - 403: Si no tiene permisos
        - 400: Si el estado no permite cerrar o faltan campos obligatorios
        """
        # Solo JEFE_TALLER puede cerrar OT
        if request.user.rol != "JEFE_TALLER":
            return Response(
                {"detail": "Solo JEFE_TALLER puede cerrar la OT."},
                status=status.HTTP_403_FORBIDDEN
            )
        ot = self.get_object()
        
        # Validar que el estado permita cerrar
        if ot.estado not in ("EN_QA", "CERRADA"):
            return Response(
                {"detail": f"No se puede cerrar una OT en estado {ot.estado}. Debe estar en EN_QA."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar campos obligatorios para el cierre
        diagnostico_final = request.data.get('diagnostico_final') or request.data.get('diagnostico')
        fecha_cierre = request.data.get('fecha_cierre') or request.data.get('cierre')
        
        if not diagnostico_final:
            return Response(
                {"detail": "El campo diagnostico_final es obligatorio para cerrar la OT."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not fecha_cierre:
            return Response(
                {"detail": "El campo fecha_cierre es obligatorio para cerrar la OT."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar diagnóstico y fecha de cierre
        ot.diagnostico = diagnostico_final
        if fecha_cierre:
            from django.utils.dateparse import parse_datetime
            fecha_parsed = parse_datetime(fecha_cierre)
            if fecha_parsed:
                ot.cierre = fecha_parsed
            else:
                return Response(
                    {"detail": "El formato de fecha_cierre es inválido. Use formato ISO 8601."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Guardar diagnóstico y cierre antes de la transición
        ot.save(update_fields=["diagnostico", "cierre"])
        
        # Ejecutar transición (actualiza estado y fecha de cierre)
        do_transition(ot, "CERRADA", usuario=request.user)
        
        # Registrar en historial del vehículo y calcular tiempos
        try:
            from apps.vehicles.utils import registrar_ot_cerrada
            registrar_ot_cerrada(ot, request.user)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al registrar historial para OT {ot.id}: {e}")
        
        # Generar PDF de cierre automáticamente (tarea asíncrona)
        try:
            from .tasks import generar_pdf_cierre
            generar_pdf_cierre.delay(str(ot.id), request.user.id)
        except Exception:
            # Si no existe la tarea, continuar sin error
            pass
        
        # Registrar auditoría
        Auditoria.objects.create(
            usuario=request.user,
            accion="CERRAR_OT",
            objeto_tipo="OrdenTrabajo",
            objeto_id=str(ot.id),
            payload={}
        )
        
        # Crear notificaciones
        try:
            from apps.notifications.utils import crear_notificacion_ot_cerrada
            crear_notificacion_ot_cerrada(ot, request.user)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al crear notificaciones para OT cerrada {ot.id}: {e}")
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_ot
            enviar_actualizacion_ot(ot, action="closed")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para OT {ot.id}: {e}")
        
        return Response({"estado": ot.estado, "cierre": ot.cierre})

    @extend_schema(request=EmptySerializer, responses={200: None})
    @action(detail=True, methods=['post'], url_path='anular')
    def anular(self, request, pk=None):
        """
        Anula la OT (cancela antes de completarse).
        
        Endpoint: POST /api/v1/work/ordenes/{id}/anular/
        
        Permisos:
        - Solo SUPERVISOR o ADMIN
        
        Uso:
        - Cuando se detecta que la OT fue creada por error
        - Cuando el vehículo ya no necesita reparación
        
        Retorna:
        - 200: {"estado": "ANULADA"}
        - 403: Si no tiene permisos
        """
        # Solo JEFE_TALLER puede anular OT
        if request.user.rol != "JEFE_TALLER":
            return Response(
                {"detail": "Solo JEFE_TALLER puede anular la OT."},
                status=status.HTTP_403_FORBIDDEN
            )
        ot = self.get_object()
        do_transition(ot, "ANULADA", usuario=request.user)
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_ot
            enviar_actualizacion_ot(ot, action="state_changed")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para OT {ot.id}: {e}")
        
        return Response({"estado": ot.estado})
    
    @extend_schema(
        request={"type": "object", "properties": {
            "resultado": {"type": "string"},
            "observaciones": {"type": "string"}
        }},
        responses={200: None}
    )
    @action(detail=True, methods=['post'], url_path='aprobar-qa')
    @transaction.atomic
    def aprobar_qa(self, request, pk=None):
        """
        Aprueba QA y cierra la OT desde el ID de la OT.
        
        Endpoint: POST /api/v1/work/ordenes/{id}/aprobar-qa/
        
        Permisos:
        - Solo SUPERVISOR, ADMIN o JEFE_TALLER
        
        Requisitos:
        - La OT debe estar en EN_QA
        
        Body JSON:
        {
            "resultado": "OK",  // Opcional, por defecto "OK"
            "observaciones": "Observaciones del QA"  // Opcional
        }
        
        Retorna:
        - 200: {"estado": "CERRADA", "mensaje": "QA aprobada y OT cerrada"}
        - 403: Si no tiene permisos
        - 400: Si el estado no permite aprobar QA
        """
        if request.user.rol not in ("SUPERVISOR", "ADMIN", "JEFE_TALLER"):
            return Response(
                {"detail": "Solo SUPERVISOR/ADMIN/JEFE_TALLER pueden aprobar QA."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        ot = self.get_object()
        
        # Validar estado
        if ot.estado != "EN_QA":
            return Response(
                {"detail": f"La OT no está en estado EN_QA. Estado actual: {ot.estado}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar o crear checklist
        checklist, created = Checklist.objects.get_or_create(
            ot=ot,
            defaults={
                "verificador": request.user,
                "resultado": "OK",
                "observaciones": request.data.get("observaciones", "")
            }
        )
        
        # Actualizar checklist si ya existía
        if not created:
            checklist.resultado = "OK"
            if request.data.get("observaciones"):
                checklist.observaciones = request.data.get("observaciones")
            checklist.verificador = request.user
            checklist.save()
        
        # Cerrar la OT
        do_transition(ot, "CERRADA")
        
        # Registrar auditoría
        Auditoria.objects.create(
            usuario=request.user,
            accion="APROBAR_QA",
            objeto_tipo="Checklist",
            objeto_id=str(checklist.id),
            payload={"ot_id": str(ot.id)}
        )
        
        # Crear notificaciones
        try:
            from apps.notifications.utils import crear_notificacion_ot_cerrada, crear_notificacion_ot_aprobada
            crear_notificacion_ot_cerrada(ot, request.user)
            crear_notificacion_ot_aprobada(ot, request.user)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al crear notificaciones para OT aprobada {ot.id}: {e}")
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_ot
            enviar_actualizacion_ot(ot, action="closed")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para OT {ot.id}: {e}")
        
        return Response({
            "estado": ot.estado,
            "mensaje": "QA aprobada y OT cerrada"
        })
    
    @extend_schema(
        request={"type": "object", "properties": {
            "observaciones": {"type": "string"}
        }},
        responses={200: None}
    )
    @action(detail=True, methods=['post'], url_path='rechazar-qa')
    @transaction.atomic
    def rechazar_qa(self, request, pk=None):
        """
        Rechaza QA y devuelve la OT a EN_EJECUCION desde el ID de la OT.
        
        Endpoint: POST /api/v1/work/ordenes/{id}/rechazar-qa/
        
        Permisos:
        - Solo SUPERVISOR, ADMIN o JEFE_TALLER
        
        Requisitos:
        - La OT debe estar en EN_QA
        
        Body JSON:
        {
            "observaciones": "Motivo del rechazo"  // Opcional
        }
        
        Retorna:
        - 200: {"estado": "EN_EJECUCION", "mensaje": "QA rechazada. OT devuelta a EN_EJECUCION para corrección"}
        - 403: Si no tiene permisos
        - 400: Si el estado no permite rechazar QA
        """
        if request.user.rol not in ("SUPERVISOR", "ADMIN", "JEFE_TALLER"):
            return Response(
                {"detail": "Solo SUPERVISOR/ADMIN/JEFE_TALLER pueden rechazar QA."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        ot = self.get_object()
        
        # Validar estado
        if ot.estado != "EN_QA":
            return Response(
                {"detail": f"La OT no está en estado EN_QA. Estado actual: {ot.estado}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar o crear checklist
        checklist, created = Checklist.objects.get_or_create(
            ot=ot,
            defaults={
                "verificador": request.user,
                "resultado": "NO_OK",
                "observaciones": request.data.get("observaciones", "QA rechazada - requiere corrección")
            }
        )
        
        # Actualizar checklist si ya existía
        if not created:
            checklist.resultado = "NO_OK"
            checklist.observaciones = request.data.get("observaciones", checklist.observaciones)
            if not checklist.observaciones:
                checklist.observaciones = "QA rechazada - requiere corrección"
            checklist.verificador = request.user
            checklist.save()
        
        # Devolver OT a EN_EJECUCION
        do_transition(ot, "EN_EJECUCION", usuario=request.user)
        
        # Registrar auditoría
        Auditoria.objects.create(
            usuario=request.user,
            accion="RECHAZAR_QA",
            objeto_tipo="Checklist",
            objeto_id=str(checklist.id),
            payload={
                "ot_id": str(ot.id),
                "observaciones": checklist.observaciones
            }
        )
        
        # Crear notificaciones
        try:
            from apps.notifications.utils import crear_notificacion_ot_rechazada
            crear_notificacion_ot_rechazada(ot, request.user)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al crear notificaciones para OT rechazada {ot.id}: {e}")
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_ot
            enviar_actualizacion_ot(ot, action="state_changed")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para OT {ot.id}: {e}")
        
        return Response({
            "estado": ot.estado,
            "mensaje": "QA rechazada. OT devuelta a EN_EJECUCION para corrección"
        })
    
    @extend_schema(
        request={"type": "object", "properties": {"diagnostico": {"type": "string"}}},
        responses={200: None}
    )
    @action(detail=True, methods=['post'], url_path='diagnostico')
    @transaction.atomic
    def diagnostico(self, request, pk=None):
        """
        Jefe de Taller realiza diagnóstico de la OT.
        
        Endpoint: POST /api/v1/work/ordenes/{id}/diagnostico/
        
        Permisos:
        - Solo JEFE_TALLER o ADMIN
        
        Requisitos:
        - La OT debe estar en ABIERTA o EN_DIAGNOSTICO
        - Se debe proporcionar el texto del diagnóstico
        
        Proceso:
        1. Valida permisos y estado
        2. Guarda diagnóstico y asigna jefe_taller
        3. Establece fecha_diagnostico
        4. Cambia estado a EN_DIAGNOSTICO
        5. Registra auditoría
        
        Body JSON:
        {
            "diagnostico": "Texto del diagnóstico técnico"
        }
        
        Retorna:
        - 200: {"estado": "EN_DIAGNOSTICO", "diagnostico": "..."}
        - 403: Si no tiene permisos
        - 400: Si falta diagnóstico o estado inválido
        """
        if request.user.rol not in ("JEFE_TALLER", "ADMIN"):
            return Response(
                {"detail": "Solo JEFE_TALLER puede realizar diagnóstico."},
                status=status.HTTP_403_FORBIDDEN
            )
        ot = self.get_object()
        
        # Validar estado
        if ot.estado not in ("ABIERTA", "EN_DIAGNOSTICO"):
            return Response(
                {"detail": f"La OT debe estar en ABIERTA o EN_DIAGNOSTICO para realizar diagnóstico."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener diagnóstico del body
        diagnostico_texto = request.data.get("diagnostico", "")
        if not diagnostico_texto:
            return Response(
                {"detail": "El diagnóstico es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Guardar diagnóstico y asignar jefe de taller
        ot.diagnostico = diagnostico_texto
        ot.jefe_taller = request.user
        ot.fecha_diagnostico = timezone.now()
        
        # Guardar diagnóstico y jefe_taller antes de la transición
        ot.save(update_fields=["diagnostico", "jefe_taller", "fecha_diagnostico"])
        
        # Cambiar estado (actualiza fecha_diagnostico automáticamente)
        do_transition(ot, "EN_DIAGNOSTICO", usuario=request.user)
        
        # Registrar auditoría
        Auditoria.objects.create(
            usuario=request.user,
            accion="DIAGNOSTICO_OT",
            objeto_tipo="OrdenTrabajo",
            objeto_id=str(ot.id),
            payload={"diagnostico": diagnostico_texto}
        )
        
        return Response({"estado": ot.estado, "diagnostico": ot.diagnostico})
    
    @extend_schema(
        request={"type": "object", "properties": {
            "prioridad": {"type": "string", "enum": ["BAJA", "MEDIA", "ALTA", "CRITICA"]}
        }},
        responses={200: None}
    )
    @action(detail=True, methods=['post'], url_path='cambiar-prioridad')
    @transaction.atomic
    def cambiar_prioridad(self, request, pk=None):
        """
        Cambia la prioridad de una OT.
        
        Endpoint: POST /api/v1/work/ordenes/{id}/cambiar-prioridad/
        
        Permisos:
        - Solo COORDINADOR_ZONA, JEFE_TALLER o ADMIN
        
        Body JSON:
        {
            "prioridad": "ALTA"  // BAJA, MEDIA, ALTA, CRITICA
        }
        
        Retorna:
        - 200: {"prioridad": "ALTA", "mensaje": "Prioridad actualizada"}
        - 403: Si no tiene permisos
        - 400: Si la prioridad no es válida
        """
        # Solo COORDINADOR_ZONA, JEFE_TALLER o ADMIN pueden cambiar prioridad
        if request.user.rol not in ["COORDINADOR_ZONA", "JEFE_TALLER", "ADMIN"]:
            return Response(
                {"detail": "Solo COORDINADOR_ZONA, JEFE_TALLER o ADMIN pueden cambiar la prioridad."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        ot = self.get_object()
        nueva_prioridad = request.data.get("prioridad")
        
        if not nueva_prioridad:
            return Response(
                {"detail": "Se requiere el campo 'prioridad'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que la prioridad sea válida
        prioridades_validas = ["BAJA", "MEDIA", "ALTA", "CRITICA"]
        if nueva_prioridad not in prioridades_validas:
            return Response(
                {"detail": f"Prioridad inválida. Debe ser una de: {', '.join(prioridades_validas)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar prioridad
        prioridad_anterior = ot.prioridad
        ot.prioridad = nueva_prioridad
        ot.save(update_fields=["prioridad"])
        
        # Registrar auditoría
        try:
            Auditoria.objects.create(
                usuario=request.user,
                accion="CAMBIAR_PRIORIDAD",
                objeto_tipo="OrdenTrabajo",
                objeto_id=str(ot.id),
                payload={
                    "prioridad_anterior": prioridad_anterior,
                    "prioridad_nueva": nueva_prioridad
                }
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al registrar auditoría de cambio de prioridad para OT {ot.id}: {e}")
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_ot
            enviar_actualizacion_ot(ot, action="updated")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para OT {ot.id}: {e}")
        
        return Response({
            "prioridad": ot.prioridad,
            "mensaje": f"Prioridad actualizada de {prioridad_anterior} a {nueva_prioridad}"
        })
    
    @extend_schema(
        request={"type": "object", "properties": {
            "mecanico_id": {"type": "string"},
            "prioridad": {"type": "string"}
        }},
        responses={200: None}
    )
    @action(detail=True, methods=['post'], url_path='aprobar-asignacion')
    @transaction.atomic
    def aprobar_asignacion(self, request, pk=None):
        """
        Supervisor aprueba la asignación de un mecánico a la OT.
        
        Endpoint: POST /api/v1/work/ordenes/{id}/aprobar-asignacion/
        
        Permisos:
        - Solo SUPERVISOR, ADMIN o COORDINADOR_ZONA
        
        Requisitos:
        - La OT debe estar en EN_DIAGNOSTICO
        - Se debe proporcionar mecanico_id
        
        Proceso:
        1. Valida permisos y estado
        2. Busca el mecánico (debe tener rol MECANICO)
        3. Asigna mecánico y supervisor
        4. Establece fechas de aprobación y asignación
        5. Ajusta prioridad si se proporciona
        6. Cambia estado a EN_EJECUCION
        7. Registra auditoría
        
        Body JSON:
        {
            "mecanico_id": "uuid-del-mecanico",
            "prioridad": "ALTA"  // Opcional
        }
        
        Retorna:
        - 200: {"estado": "EN_EJECUCION", "mecanico": "...", "supervisor": "..."}
        - 403: Si no tiene permisos
        - 400: Si falta mecanico_id o estado inválido
        - 404: Si el mecánico no existe
        """
        # JEFE_TALLER y ADMIN pueden asignar mecánicos
        if request.user.rol not in ["JEFE_TALLER", "ADMIN"]:
            return Response(
                {"detail": "Solo JEFE_TALLER o ADMIN pueden asignar mecánicos."},
                status=status.HTTP_403_FORBIDDEN
            )
        ot = self.get_object()
        
        # Validar estado - permitir asignar/reasignar desde cualquier estado excepto CERRADA
        if ot.estado == "CERRADA":
            return Response(
                {"detail": f"No se puede asignar o reasignar mecánico a una OT cerrada. Estado actual: {ot.estado}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener ID del mecánico
        mecanico_id = request.data.get("mecanico_id")
        if not mecanico_id:
            return Response(
                {"detail": "Se requiere mecanico_id."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar mecánico (debe tener rol MECANICO)
        from apps.users.models import User
        try:
            mecanico = User.objects.get(id=mecanico_id, rol="MECANICO")
        except User.DoesNotExist:
            return Response(
                {"detail": "Mecánico no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Guardar el mecánico anterior para saber si estaba en pausa por falta de mecánico
        # y para notificar si se está reasignando
        mecanico_anterior = ot.mecanico
        es_reasignacion = mecanico_anterior is not None and mecanico_anterior.id != mecanico.id
        
        # Asignar mecánico
        ot.mecanico = mecanico
        
        # Si no tiene supervisor, asignar el usuario actual si es supervisor
        if not ot.supervisor and request.user.rol in ["SUPERVISOR", "COORDINADOR_ZONA", "ADMIN"]:
            ot.supervisor = request.user
            ot.fecha_aprobacion_supervisor = timezone.now()
        elif ot.supervisor:
            # Si ya tiene supervisor, actualizar fecha de aprobación
            ot.fecha_aprobacion_supervisor = timezone.now()
        
        ot.fecha_asignacion_mecanico = timezone.now()
        
        # Ajustar prioridad si se proporciona
        nueva_prioridad = request.data.get("prioridad")
        if nueva_prioridad:
            ot.prioridad = nueva_prioridad
        
        # Si estaba en EN_PAUSA y no tenía mecánico anterior, cambiar a ABIERTA primero
        if ot.estado == "EN_PAUSA" and not mecanico_anterior:
            # Cambiar a ABIERTA si estaba en pausa sin mecánico
            do_transition(ot, "ABIERTA", usuario=request.user)
        
        # Cambiar estado a EN_EJECUCION si está en ABIERTA o EN_DIAGNOSTICO
        if ot.estado in ("ABIERTA", "EN_DIAGNOSTICO"):
            do_transition(ot, "EN_EJECUCION", usuario=request.user)
            # IMPORTANTE: Después de la transición, guardar también el mecánico y fecha de asignación
            # porque do_transition solo guarda estado y fecha_inicio_ejecucion
            campos_actualizar = ["mecanico", "fecha_asignacion_mecanico"]
            if ot.supervisor:
                campos_actualizar.append("supervisor")
                campos_actualizar.append("fecha_aprobacion_supervisor")
            if nueva_prioridad:
                campos_actualizar.append("prioridad")
            ot.save(update_fields=campos_actualizar)
        else:
            # Si ya está en otro estado, solo guardar la asignación
            # Guardar todos los campos relacionados con la asignación
            campos_actualizar = ["mecanico", "fecha_asignacion_mecanico"]
            if ot.supervisor:
                campos_actualizar.append("supervisor")
                campos_actualizar.append("fecha_aprobacion_supervisor")
            if nueva_prioridad:
                campos_actualizar.append("prioridad")
            ot.save(update_fields=campos_actualizar)
        
        # Registrar auditoría
        accion_auditoria = "REASIGNAR_MECANICO_OT" if es_reasignacion else "APROBAR_ASIGNACION_OT"
        payload_auditoria = {
            "mecanico_id": str(mecanico.id),
            "mecanico": mecanico.username
        }
        if es_reasignacion and mecanico_anterior:
            payload_auditoria["mecanico_anterior_id"] = str(mecanico_anterior.id)
            payload_auditoria["mecanico_anterior"] = mecanico_anterior.username
        
        Auditoria.objects.create(
            usuario=request.user,
            accion=accion_auditoria,
            objeto_tipo="OrdenTrabajo",
            objeto_id=str(ot.id),
            payload=payload_auditoria
        )
        
        # Crear notificaciones
        try:
            from apps.notifications.utils import crear_notificacion_ot_asignada
            crear_notificacion_ot_asignada(ot, mecanico)
            
            # Si es reasignación, notificar también al mecánico anterior
            if es_reasignacion and mecanico_anterior:
                try:
                    from apps.notifications.models import Notificacion
                    Notificacion.objects.create(
                        usuario=mecanico_anterior,
                        tipo="OT_REASIGNADA",
                        titulo=f"OT #{str(ot.id)[:8]} reasignada",
                        mensaje=f"La OT #{str(ot.id)[:8]} ha sido reasignada a otro mecánico.",
                        relacionado_tipo="OrdenTrabajo",
                        relacionado_id=str(ot.id)
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error al crear notificación de reasignación para mecánico anterior {mecanico_anterior.id}: {e}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al crear notificaciones para OT asignada {ot.id}: {e}")
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_ot, enviar_actualizacion_asignacion
            action_type = "reassigned" if es_reasignacion else "assigned"
            enviar_actualizacion_ot(ot, action="updated")
            enviar_actualizacion_asignacion(ot, mecanico, action=action_type)
            # Si es reasignación, notificar también al mecánico anterior
            if es_reasignacion and mecanico_anterior:
                enviar_actualizacion_asignacion(ot, mecanico_anterior, action="unassigned")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para OT {ot.id}: {e}")
        
        # Recargar la OT desde la base de datos para asegurar datos actualizados
        ot.refresh_from_db()
        
        # Retornar la OT completa serializada
        serializer = self.get_serializer(ot)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='retrabajo')
    @transaction.atomic
    def retrabajo(self, request, pk=None):
        """
        Marca la OT como retrabajo (requiere corrección después de QA).
        
        Endpoint: POST /api/v1/work/ordenes/{id}/retrabajo/
        
        Permisos:
        - Solo SUPERVISOR, ADMIN o JEFE_TALLER
        
        Requisitos:
        - La OT debe estar en EN_QA
        
        Proceso:
        1. Valida permisos y estado
        2. Cambia estado a RETRABAJO
        3. Registra auditoría con motivo
        
        Body JSON:
        {
            "motivo": "Retrabajo por calidad"  // Opcional
        }
        
        Retorna:
        - 200: {"estado": "RETRABAJO", "motivo": "..."}
        - 403: Si no tiene permisos
        - 400: Si el estado no permite retrabajo
        """
        # Solo JEFE_TALLER puede aprobar QA y marcar retrabajo
        if request.user.rol != "JEFE_TALLER":
            return Response(
                {"detail": "Solo JEFE_TALLER puede marcar como retrabajo."},
                status=status.HTTP_403_FORBIDDEN
            )
        ot = self.get_object()
        
        # Validar estado
        if ot.estado != "EN_QA":
            return Response(
                {"detail": "Solo se puede marcar como retrabajo desde EN_QA."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener motivo (opcional)
        motivo = request.data.get("motivo", "Retrabajo por calidad")
        
        # Cambiar estado
        try:
            do_transition(ot, "RETRABAJO", usuario=request.user)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al cambiar estado a RETRABAJO para OT {ot.id}: {e}")
            return Response(
                {"detail": f"Error al cambiar estado: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Registrar auditoría
        try:
            Auditoria.objects.create(
                usuario=request.user,
                accion="RETRABAJO_OT",
                objeto_tipo="OrdenTrabajo",
                objeto_id=str(ot.id),
                payload={"motivo": motivo}
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al registrar auditoría de retrabajo para OT {ot.id}: {e}")
            # No fallar la operación si falla la auditoría
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_ot
            enviar_actualizacion_ot(ot, action="state_changed")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para OT {ot.id}: {e}")
        
        return Response({"estado": ot.estado, "motivo": motivo})


# ============== ITEMS =================
class ItemOTViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Items de OT (repuestos y servicios).
    
    Endpoints:
    - GET /api/v1/work/items/ → Listar items
    - POST /api/v1/work/items/ → Crear item
    - GET /api/v1/work/items/{id}/ → Ver item
    - PUT/PATCH /api/v1/work/items/{id}/ → Editar item
    - DELETE /api/v1/work/items/{id}/ → Eliminar item
    
    Permisos:
    - Usa WorkOrderPermission
    
    Filtros:
    - Por tipo (REPUESTO/SERVICIO)
    - Por OT
    - Búsqueda por descripción
    - Ordenamiento por costo, cantidad
    """
    queryset = ItemOT.objects.select_related("ot")  # Optimización: reduce queries
    serializer_class = ItemOTSerializer
    permission_classes = [WorkOrderPermission]

    # Configuración de filtros
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["tipo", "ot"]  # Filtros por tipo y OT
    search_fields = ["descripcion"]  # Búsqueda por descripción
    ordering_fields = ["costo_unitario", "cantidad"]  # Campos ordenables
    ordering = ["-id"]  # Orden por defecto: más recientes primero
    
    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario.
        
        - MECANICO: Solo items de OTs asignadas a él
        - Otros roles: Sin filtrado adicional
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        rol = getattr(user, "rol", None)
        
        # MECANICO: Solo items de OTs asignadas a él
        if rol == "MECANICO":
            return queryset.filter(ot__mecanico=user)
        
        return queryset
    
    def perform_create(self, serializer):
        """Crea un item y envía actualización en tiempo real."""
        item = serializer.save()
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_item, enviar_actualizacion_ot
            enviar_actualizacion_item(item, action="created")
            # También actualizar la OT para que se refresque la lista de items
            if item.ot:
                enviar_actualizacion_ot(item.ot, action="updated")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para item {item.id}: {e}")
    
    def perform_update(self, serializer):
        """Actualiza un item y envía actualización en tiempo real."""
        item = serializer.save()
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_item, enviar_actualizacion_ot
            enviar_actualizacion_item(item, action="updated")
            # También actualizar la OT
            if item.ot:
                enviar_actualizacion_ot(item.ot, action="updated")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para item {item.id}: {e}")
    
    def perform_destroy(self, instance):
        """Elimina un item y envía actualización en tiempo real."""
        ot = instance.ot
        instance.delete()
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_ot
            # Enviar actualización de eliminación (aunque el item ya no existe, enviamos su ID)
            if ot:
                enviar_actualizacion_ot(ot, action="updated")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real al eliminar item: {e}")


# ============== PRESUPUESTO =================
class PresupuestoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Presupuestos.
    
    Endpoints:
    - GET /api/v1/work/presupuestos/ → Listar presupuestos
    - POST /api/v1/work/presupuestos/ → Crear presupuesto (con detalles)
    - GET /api/v1/work/presupuestos/{id}/ → Ver presupuesto
    - PUT/PATCH /api/v1/work/presupuestos/{id}/ → Editar presupuesto
    - DELETE /api/v1/work/presupuestos/{id}/ → Eliminar presupuesto
    
    Permisos:
    - Usa WorkOrderPermission
    
    Filtros:
    - Por requiere_aprobacion
    - Por OT
    - Ordenamiento por total, fecha
    
    Nota:
    - Al crear, se calcula el total automáticamente
    - Si total > umbral (1000), requiere_aprobacion = True
    """
    queryset = Presupuesto.objects.select_related("ot")
    serializer_class = PresupuestoSerializer
    permission_classes = [WorkOrderPermission]

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["requiere_aprobacion", "ot"]
    ordering_fields = ["total", "creado_en"]
    
    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario.
        
        - MECANICO: Solo presupuestos de OTs asignadas a él
        - Otros roles: Sin filtrado adicional
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        rol = getattr(user, "rol", None)
        
        # MECANICO: Solo presupuestos de OTs asignadas a él
        if rol == "MECANICO":
            return queryset.filter(ot__mecanico=user)
        
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        """
        Crea un presupuesto con sus detalles.
        
        Este método se ejecuta al crear un presupuesto.
        Calcula el total sumando todos los detalles y determina
        si requiere aprobación según el umbral.
        
        Body JSON esperado:
        {
            "ot": "uuid-de-ot",
            "detalles_data": [
                {
                    "concepto": "Repuesto X",
                    "cantidad": 2,
                    "precio": 150.00
                },
                ...
            ]
        }
        
        Proceso:
        1. Calcula total sumando cantidad * precio de cada detalle
        2. Determina si requiere aprobación (total > umbral)
        3. Crea el presupuesto
        4. Crea los detalles asociados
        
        Umbral:
        - Por defecto: $1000.00
        - Si total > umbral → requiere_aprobacion = True
        """
        # Obtener detalles del body
        detalles_data = self.request.data.get('detalles_data', [])
        
        # Validar que detalles_data sea una lista
        if not isinstance(detalles_data, list):
            from rest_framework import serializers
            raise serializers.ValidationError({"detalles_data": "Debe ser una lista de detalles."})
        
        # Validar que haya al menos un detalle
        if len(detalles_data) == 0:
            from rest_framework import serializers
            raise serializers.ValidationError({"detalles_data": "Debe incluir al menos un detalle."})
        
        total = Decimal('0')  # Usar Decimal para precisión en dinero
        normalizados = []
        
        # Calcular total y normalizar datos
        for idx, d in enumerate(detalles_data):
            # Validar que cada detalle sea un diccionario
            if not isinstance(d, dict):
                from rest_framework import serializers
                raise serializers.ValidationError({
                    "detalles_data": f"El detalle en la posición {idx} debe ser un objeto."
                })
            
            # Validar campos requeridos
            if 'cantidad' not in d or 'precio' not in d:
                from rest_framework import serializers
                raise serializers.ValidationError({
                    "detalles_data": f"El detalle en la posición {idx} debe incluir 'cantidad' y 'precio'."
                })
            
            try:
                cantidad = Decimal(str(d.get('cantidad', '0')))
                precio = Decimal(str(d.get('precio', '0')))
            except (ValueError, TypeError):
                from rest_framework import serializers
                raise serializers.ValidationError({
                    "detalles_data": f"El detalle en la posición {idx} tiene valores inválidos para cantidad o precio."
                })
            
            # Validar que cantidad y precio sean positivos
            if cantidad <= 0:
                from rest_framework import serializers
                raise serializers.ValidationError({
                    "detalles_data": f"El detalle en la posición {idx} debe tener una cantidad mayor a 0."
                })
            if precio < 0:
                from rest_framework import serializers
                raise serializers.ValidationError({
                    "detalles_data": f"El detalle en la posición {idx} debe tener un precio mayor o igual a 0."
                })
            
            total += cantidad * precio  # Sumar al total
            
            # Normalizar para crear detalles
            normalizados.append({
                "concepto": d.get("concepto", ""),
                "cantidad": int(cantidad),
                "precio": precio
            })

        # Umbral para requerir aprobación
        UMBRAL = Decimal('1000.00')
        
        # Crear presupuesto con total calculado
        presupuesto = serializer.save(
            total=total,
            requiere_aprobacion=(total > UMBRAL),  # Requiere aprobación si supera umbral
            umbral=UMBRAL
        )
        
        # Crear detalles asociados
        for nd in normalizados:
            DetallePresup.objects.create(presupuesto=presupuesto, **nd)


# ============== DETALLES PRESUP =================
class DetallePresupViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Detalles de Presupuesto.
    
    Endpoints:
    - GET /api/v1/work/detalles-presup/ → Listar detalles
    - POST /api/v1/work/detalles-presup/ → Crear detalle
    - GET /api/v1/work/detalles-presup/{id}/ → Ver detalle
    - PUT/PATCH /api/v1/work/detalles-presup/{id}/ → Editar detalle
    - DELETE /api/v1/work/detalles-presup/{id}/ → Eliminar detalle
    
    Permisos:
    - Requiere autenticación
    
    Filtros:
    - Por presupuesto
    - Búsqueda por concepto
    - Ordenamiento por precio, cantidad
    """
    queryset = DetallePresup.objects.select_related("presupuesto", "presupuesto__ot").all()
    serializer_class = DetallePresupSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    
    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario.
        
        - MECANICO: Solo detalles de presupuestos de OTs asignadas a él
        - Otros roles: Sin filtrado adicional
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        rol = getattr(user, "rol", None)
        
        # MECANICO: Solo detalles de presupuestos de OTs asignadas a él
        if rol == "MECANICO":
            return queryset.filter(presupuesto__ot__mecanico=user)
        
        return queryset
    filterset_fields = ["presupuesto"]
    search_fields = ["concepto"]
    ordering_fields = ["precio", "cantidad", "id"]
    ordering = ["-id"]


# ============== APROBACIONES (SPONSOR) =================
class AprobacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Aprobaciones de Presupuesto por Sponsor.
    
    Endpoints:
    - GET /api/v1/work/aprobaciones/ → Listar aprobaciones
    - POST /api/v1/work/aprobaciones/ → Crear aprobación
    - GET /api/v1/work/aprobaciones/{id}/ → Ver aprobación
    - PUT/PATCH /api/v1/work/aprobaciones/{id}/ → Editar aprobación
    - DELETE /api/v1/work/aprobaciones/{id}/ → Eliminar aprobación
    
    Acciones personalizadas:
    - POST /api/v1/work/aprobaciones/{id}/aprobar/ → Aprobar presupuesto
    - POST /api/v1/work/aprobaciones/{id}/rechazar/ → Rechazar presupuesto
    
    Permisos:
    - Usa WorkOrderPermission
    - Solo SPONSOR/ADMIN pueden aprobar/rechazar
    
    Filtros:
    - Por estado (PENDIENTE/APROBADO/RECHAZADO)
    - Por sponsor
    - Por presupuesto
    - Ordenamiento por fecha
    """
    queryset = Aprobacion.objects.select_related("presupuesto", "presupuesto__ot", "sponsor")
    serializer_class = AprobacionSerializer
    permission_classes = [WorkOrderPermission]

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["estado", "sponsor", "presupuesto"]
    ordering_fields = ["fecha"]
    
    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario.
        
        - MECANICO: Solo aprobaciones de presupuestos de OTs asignadas a él
        - Otros roles: Sin filtrado adicional
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        rol = getattr(user, "rol", None)
        
        # MECANICO: Solo aprobaciones de presupuestos de OTs asignadas a él
        if rol == "MECANICO":
            return queryset.filter(presupuesto__ot__mecanico=user)
        
        return queryset

    @extend_schema(request=EmptySerializer, responses={200: None})
    @action(detail=True, methods=['post'], url_path='aprobar')
    @transaction.atomic
    def aprobar(self, request, pk=None):
        """
        Aprueba un presupuesto.
        
        Endpoint: POST /api/v1/work/aprobaciones/{id}/aprobar/
        
        Permisos:
        - Solo SPONSOR o ADMIN
        
        Proceso:
        1. Valida permisos
        2. Cambia estado a APROBADO
        3. Registra auditoría
        
        Retorna:
        - 200: {"estado": "APROBADO"}
        - 403: Si no tiene permisos
        """
        if request.user.rol not in ("SPONSOR", "ADMIN"):
            return Response(
                {"detail": "Solo SPONSOR/ADMIN pueden aprobar."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        ap = self.get_object()
        ap.estado = "APROBADO"
        ap.save(update_fields=["estado"])
        
        # Registrar auditoría
        Auditoria.objects.create(
            usuario=request.user,
            accion="APROBAR_PRESUPUESTO",
            objeto_tipo="Aprobacion",
            objeto_id=str(ap.id),
            payload={"presupuesto": str(ap.presupuesto_id)}
        )
        return Response({"estado": ap.estado})

    @extend_schema(request=EmptySerializer, responses={200: None})
    @action(detail=True, methods=['post'], url_path='rechazar')
    @transaction.atomic
    def rechazar(self, request, pk=None):
        """
        Rechaza un presupuesto.
        
        Endpoint: POST /api/v1/work/aprobaciones/{id}/rechazar/
        
        Permisos:
        - Solo SPONSOR o ADMIN
        
        Proceso:
        1. Valida permisos
        2. Cambia estado a RECHAZADO
        3. Registra auditoría
        
        Retorna:
        - 200: {"estado": "RECHAZADO"}
        - 403: Si no tiene permisos
        """
        if request.user.rol not in ("SPONSOR", "ADMIN"):
            return Response(
                {"detail": "Solo SPONSOR/ADMIN pueden rechazar."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        ap = self.get_object()
        ap.estado = "RECHAZADO"
        ap.save(update_fields=["estado"])
        
        # Registrar auditoría
        Auditoria.objects.create(
            usuario=request.user,
            accion="RECHAZAR_PRESUPUESTO",
            objeto_tipo="Aprobacion",
            objeto_id=str(ap.id),
            payload={"presupuesto": str(ap.presupuesto_id)}
        )
        return Response({"estado": ap.estado})


# ============== PAUSAS =================
class PausaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Pausas durante la ejecución de OT.
    
    Endpoints:
    - GET /api/v1/work/pausas/ → Listar pausas
    - POST /api/v1/work/pausas/ → Crear pausa
    - GET /api/v1/work/pausas/{id}/ → Ver pausa
    - PUT/PATCH /api/v1/work/pausas/{id}/ → Editar pausa
    - DELETE /api/v1/work/pausas/{id}/ → Eliminar pausa
    
    Acciones personalizadas:
    - POST /api/v1/work/pausas/{id}/reanudar/ → Reanudar pausa
    
    Características especiales:
    - Detección automática de colación (12:30-13:15)
    - Cambio automático de estado de OT a EN_PAUSA al crear
    - Cambio automático de estado de OT a EN_EJECUCION al reanudar
    
    Permisos:
    - Usa WorkOrderPermission
    
    Filtros:
    - Por OT
    - Por usuario
    - Ordenamiento por inicio, fin
    """
    queryset = Pausa.objects.select_related("ot", "usuario")
    serializer_class = PausaSerializer
    permission_classes = [WorkOrderPermission]

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["ot", "usuario"]
    ordering_fields = ["inicio", "fin"]
    
    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario.
        
        - MECANICO: Solo pausas de OTs asignadas a él
        - Otros roles: Sin filtrado adicional
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        rol = getattr(user, "rol", None)
        
        # MECANICO: Solo pausas de OTs asignadas a él
        if rol == "MECANICO":
            return queryset.filter(ot__mecanico=user)
        
        return queryset

    @extend_schema(request=EmptySerializer, responses={200: None})
    @action(detail=True, methods=['post'], url_path='reanudar')
    @transaction.atomic
    def reanudar(self, request, pk=None):
        """
        Reanuda una pausa activa.
        
        Endpoint: POST /api/v1/work/pausas/{id}/reanudar/
        
        Permisos:
        - MECANICO, SUPERVISOR, ADMIN, JEFE_TALLER
        
        Proceso:
        1. Valida que la pausa esté activa (fin es None)
        2. Establece fecha de fin
        3. Si la OT está en EN_PAUSA, cambia a EN_EJECUCION
        4. Registra auditoría
        
        Retorna:
        - 200: {"pausa": {...}, "ot_estado": "EN_EJECUCION"}
        - 403: Si no tiene permisos
        - 400: Si la pausa ya fue reanudada
        """
        if request.user.rol not in ("MECANICO", "SUPERVISOR", "ADMIN", "JEFE_TALLER"):
            return Response(
                {"detail": "No autorizado para reanudar pausas."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pausa = self.get_object()
        
        # Validar que la pausa esté activa
        if pausa.fin is not None:
            return Response(
                {"detail": "Esta pausa ya fue reanudada."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Establecer fecha de fin
        pausa.fin = timezone.now()
        pausa.save(update_fields=["fin"])
        
        # Cambiar estado de OT a EN_EJECUCION si estaba en EN_PAUSA
        ot = pausa.ot
        if ot.estado == "EN_PAUSA":
            do_transition(ot, "EN_EJECUCION", usuario=request.user)
        
        # Registrar auditoría
        Auditoria.objects.create(
            usuario=request.user,
            accion="REANUDAR_PAUSA",
            objeto_tipo="Pausa",
            objeto_id=str(pausa.id),
            payload={"ot_id": str(ot.id)}
        )
        
        return Response({
            "pausa": PausaSerializer(pausa).data,
            "ot_estado": ot.estado
        })

    def perform_create(self, serializer):
        """
        Crea una pausa y cambia el estado de la OT automáticamente.
        
        Este método se ejecuta al crear una pausa.
        
        Características:
        - Detecta automáticamente si es horario de colación (12:30-13:15)
        - Si es colación y no se especifica tipo, asigna tipo COLACION automáticamente
        - Cambia el estado de la OT a EN_PAUSA si está en EN_EJECUCION
        - Registra auditoría
        
        Body JSON esperado:
        {
            "ot": "uuid-de-ot",
            "tipo": "COLACION",  // Opcional, se detecta automáticamente
            "motivo": "Pausa para colación"
        }
        """
        # Detectar si es colación automática (12:30-13:15)
        ahora = timezone.now()
        hora_actual = ahora.hour * 60 + ahora.minute  # Convertir a minutos
        hora_colacion_inicio = 12 * 60 + 30  # 12:30 = 750 minutos
        hora_colacion_fin = 13 * 60 + 15     # 13:15 = 795 minutos
        
        es_colacion = hora_actual >= hora_colacion_inicio and hora_actual <= hora_colacion_fin
        
        # Si no se especifica tipo y es horario de colación, asignar automáticamente
        tipo_pausa = serializer.validated_data.get("tipo", "OTRO")
        if es_colacion and tipo_pausa == "OTRO":
            tipo_pausa = "COLACION"
            serializer.validated_data["tipo"] = "COLACION"
            serializer.validated_data["es_automatica"] = True
        
        # Crear pausa (asignar usuario automáticamente)
        pausa = serializer.save(usuario=self.request.user)
        ot = pausa.ot
        
        # Solo cambiar a EN_PAUSA si está en EN_EJECUCION
        if ot.estado == "EN_EJECUCION":
            do_transition(ot, "EN_PAUSA", usuario=self.request.user)
        
        # Registrar auditoría
        Auditoria.objects.create(
            usuario=self.request.user,
            accion="CREAR_PAUSA",
            objeto_tipo="Pausa",
            objeto_id=str(pausa.id),
            payload={
                "ot_id": str(ot.id),
                "motivo": pausa.motivo,
                "tipo": pausa.tipo,
                "es_automatica": pausa.es_automatica
            }
        )


# ============== CHECKLIST =================
class ChecklistViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Checklists de Calidad (QA).
    
    Endpoints:
    - GET /api/v1/work/checklists/ → Listar checklists
    - POST /api/v1/work/checklists/ → Crear checklist
    - GET /api/v1/work/checklists/{id}/ → Ver checklist
    - PUT/PATCH /api/v1/work/checklists/{id}/ → Editar checklist
    - DELETE /api/v1/work/checklists/{id}/ → Eliminar checklist
    
    Acciones personalizadas:
    - POST /api/v1/work/checklists/{id}/aprobar-qa/ → Aprobar QA y cerrar OT
    - POST /api/v1/work/checklists/{id}/rechazar-qa/ → Rechazar QA y devolver a EN_EJECUCION
    
    Permisos:
    - Usa WorkOrderPermission
    - Solo SUPERVISOR/ADMIN/JEFE_TALLER pueden aprobar/rechazar QA
    
    Filtros:
    - Por resultado (OK/NO_OK)
    - Por OT
    - Búsqueda por observaciones
    - Ordenamiento por fecha
    """
    queryset = Checklist.objects.select_related("ot", "verificador")
    serializer_class = ChecklistSerializer
    permission_classes = [WorkOrderPermission]

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["resultado", "ot"]
    ordering_fields = ["fecha"]
    search_fields = ["observaciones"]
    
    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario.
        
        - MECANICO: Solo checklists de OTs asignadas a él
        - Otros roles: Sin filtrado adicional
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        rol = getattr(user, "rol", None)
        
        # MECANICO: Solo checklists de OTs asignadas a él
        if rol == "MECANICO":
            return queryset.filter(ot__mecanico=user)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Crea un checklist y asigna el verificador automáticamente.
        
        Este método se ejecuta al crear un checklist.
        Asigna el usuario actual como verificador.
        
        Body JSON esperado:
        {
            "ot": "uuid-de-ot",
            "resultado": "OK",  // o "NO_OK"
            "observaciones": "Checklist completado"
        }
        """
        # Crear checklist (asignar verificador automáticamente)
        checklist = serializer.save(verificador=self.request.user)
        
        # Registrar auditoría
        Auditoria.objects.create(
            usuario=self.request.user,
            accion="CREAR_CHECKLIST_QA",
            objeto_tipo="Checklist",
            objeto_id=str(checklist.id),
            payload={"ot_id": str(checklist.ot.id), "resultado": checklist.resultado}
        )
    
    @extend_schema(request=EmptySerializer, responses={200: None})
    @action(detail=True, methods=['post'], url_path='aprobar-qa')
    @transaction.atomic
    def aprobar_qa(self, request, pk=None):
        """
        Aprueba QA y cierra la OT.
        
        Endpoint: POST /api/v1/work/checklists/{id}/aprobar-qa/
        
        Permisos:
        - Solo SUPERVISOR, ADMIN o JEFE_TALLER
        
        Requisitos:
        - La OT debe estar en EN_QA
        
        Proceso:
        1. Valida permisos y estado
        2. Actualiza checklist a resultado OK (si no lo está)
        3. Cierra la OT (cambia a CERRADA)
        4. Registra auditoría
        
        Retorna:
        - 200: {"checklist": {...}, "ot_estado": "CERRADA", "mensaje": "..."}
        - 403: Si no tiene permisos
        - 400: Si el estado no permite aprobar QA
        """
        if request.user.rol not in ("SUPERVISOR", "ADMIN", "JEFE_TALLER"):
            return Response(
                {"detail": "Solo SUPERVISOR/ADMIN/JEFE_TALLER pueden aprobar QA."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        checklist = self.get_object()
        ot = checklist.ot
        
        # Validar estado
        if ot.estado != "EN_QA":
            return Response(
                {"detail": f"La OT no está en estado EN_QA. Estado actual: {ot.estado}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar checklist si no tiene resultado OK
        if checklist.resultado != "OK":
            checklist.resultado = "OK"
            checklist.observaciones = request.data.get("observaciones", checklist.observaciones)
            checklist.save()
        
        # Cerrar la OT
        do_transition(ot, "CERRADA")
        
        # Registrar auditoría
        Auditoria.objects.create(
            usuario=request.user,
            accion="APROBAR_QA",
            objeto_tipo="Checklist",
            objeto_id=str(checklist.id),
            payload={"ot_id": str(ot.id)}
        )
        
        # Crear notificaciones (la OT fue cerrada y aprobada)
        try:
            from apps.notifications.utils import crear_notificacion_ot_cerrada, crear_notificacion_ot_aprobada
            crear_notificacion_ot_cerrada(ot, request.user)
            crear_notificacion_ot_aprobada(ot, request.user)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al crear notificaciones para OT aprobada {ot.id}: {e}")
        
        return Response({
            "checklist": ChecklistSerializer(checklist).data,
            "ot_estado": ot.estado,
            "mensaje": "QA aprobada y OT cerrada"
        })
    
    @extend_schema(request=EmptySerializer, responses={200: None})
    @action(detail=True, methods=['post'], url_path='rechazar-qa')
    @transaction.atomic
    def rechazar_qa(self, request, pk=None):
        """
        Rechaza QA y devuelve la OT a EN_EJECUCION para corrección.
        
        Endpoint: POST /api/v1/work/checklists/{id}/rechazar-qa/
        
        Permisos:
        - Solo SUPERVISOR, ADMIN o JEFE_TALLER
        
        Requisitos:
        - La OT debe estar en EN_QA
        
        Proceso:
        1. Valida permisos y estado
        2. Actualiza checklist a resultado NO_OK
        3. Agrega observaciones (si se proporcionan)
        4. Devuelve OT a EN_EJECUCION
        5. Registra auditoría
        
        Body JSON:
        {
            "observaciones": "Motivo del rechazo"  // Opcional
        }
        
        Retorna:
        - 200: {"checklist": {...}, "ot_estado": "EN_EJECUCION", "mensaje": "..."}
        - 403: Si no tiene permisos
        - 400: Si el estado no permite rechazar QA
        """
        if request.user.rol not in ("SUPERVISOR", "ADMIN", "JEFE_TALLER"):
            return Response(
                {"detail": "Solo SUPERVISOR/ADMIN/JEFE_TALLER pueden rechazar QA."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        checklist = self.get_object()
        ot = checklist.ot
        
        # Validar estado
        if ot.estado != "EN_QA":
            return Response(
                {"detail": f"La OT no está en estado EN_QA. Estado actual: {ot.estado}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar checklist con resultado NO_OK y observaciones
        checklist.resultado = "NO_OK"
        checklist.observaciones = request.data.get("observaciones", checklist.observaciones)
        if not checklist.observaciones:
            checklist.observaciones = "QA rechazada - requiere corrección"
        checklist.save()
        
        # Devolver OT a EN_EJECUCION
        do_transition(ot, "EN_EJECUCION", usuario=request.user)
        
        # Registrar auditoría
        Auditoria.objects.create(
            usuario=request.user,
            accion="RECHAZAR_QA",
            objeto_tipo="Checklist",
            objeto_id=str(checklist.id),
            payload={
                "ot_id": str(ot.id),
                "observaciones": checklist.observaciones
            }
        )
        
        # Crear notificaciones
        try:
            from apps.notifications.utils import crear_notificacion_ot_rechazada
            crear_notificacion_ot_rechazada(ot, request.user)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al crear notificaciones para OT rechazada {ot.id}: {e}")
        
        return Response({
            "checklist": ChecklistSerializer(checklist).data,
            "ot_estado": ot.estado,
            "mensaje": "QA rechazada. OT devuelta a EN_EJECUCION para corrección"
        })


# ============== EVIDENCIAS (incluye presigned S3) =================
class EvidenciaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Evidencias (fotos/documentos).
    
    Endpoints:
    - GET /api/v1/work/evidencias/ → Listar evidencias
    - POST /api/v1/work/evidencias/ → Crear evidencia (después de subir a S3)
    - GET /api/v1/work/evidencias/{id}/ → Ver evidencia
    - PUT/PATCH /api/v1/work/evidencias/{id}/ → Editar evidencia
    - DELETE /api/v1/work/evidencias/{id}/ → Eliminar evidencia
    
    Acciones personalizadas:
    - POST /api/v1/work/evidencias/presigned/ → Obtener URL presigned para subir archivo
    
    Permisos:
    - Usa WorkOrderPermission
    - Solo MECANICO, SUPERVISOR, ADMIN, GUARDIA pueden subir evidencias
    
    Filtros:
    - Por tipo (FOTO/PDF/OTRO)
    - Por OT
    - Ordenamiento por fecha de subida
    
    Flujo de subida:
    1. Frontend llama a /presigned/ para obtener URL
    2. Frontend sube archivo directamente a S3 usando URL presigned
    3. Frontend llama a POST /evidencias/ con la URL del archivo
    """
    queryset = Evidencia.objects.select_related("ot", "ot__vehiculo", "subido_por")
    serializer_class = EvidenciaSerializer
    permission_classes = [WorkOrderPermission]

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["tipo", "ot"]
    ordering_fields = ["subido_en"]
    
    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario.
        
        - JEFE_TALLER: todas las evidencias
        - SUPERVISOR: todas las evidencias
        - ADMIN: todas las evidencias
        - COORDINADOR_ZONA: todas las evidencias
        - ADMINISTRATIVO_TALLER: todas las evidencias
        - EJECUTIVO: todas las evidencias
        - MECANICO: evidencias que él subió o de la OT en la que trabaja
        - GUARDIA: evidencias que él subió
        - BODEGA: evidencias de OTs con solicitudes de repuestos
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        rol = getattr(user, "rol", None)
        
        # Jefe de Taller: todas las evidencias
        if rol == "JEFE_TALLER":
            return queryset
        
        # Supervisor Zonal: todas las evidencias
        if rol == "SUPERVISOR":
            return queryset
        
        # Administrador: todas las evidencias
        if rol == "ADMIN":
            return queryset
        
        # Mecánico: evidencias que él subió o de la OT en la que trabaja
        if rol == "MECANICO":
            # Usar Q objects para combinar condiciones (más eficiente que union)
            return queryset.filter(Q(subido_por=user) | Q(ot__mecanico=user))
        
        # Guardia: NO puede ver evidencias de OTs (solo evidencias de ingreso que se manejan en otro modelo)
        if rol == "GUARDIA":
            return queryset.none()  # Guardia no ve evidencias de OTs
        
        # Coordinador de Zona: todas las evidencias
        if rol == "COORDINADOR_ZONA":
            return queryset
        
        # Administrativo de Taller: todas las evidencias
        if rol == "ADMINISTRATIVO_TALLER":
            return queryset
        
        # Bodega: evidencias relacionadas con repuestos
        if rol == "BODEGA":
            # Filtrar evidencias de OTs que tienen solicitudes de repuestos
            try:
                from apps.inventory.models import SolicitudRepuesto
                ots_con_repuestos = SolicitudRepuesto.objects.values_list('ot_id', flat=True).distinct()
                return queryset.filter(ot_id__in=ots_con_repuestos)
            except Exception:
                return queryset.none()
        
        # Ejecutivo: todas las evidencias
        if rol == "EJECUTIVO":
            return queryset
        
        # Otros roles: sin acceso
        return queryset.none()
    
    def create(self, request, *args, **kwargs):
        """
        Crea una nueva evidencia y envía notificaciones a usuarios relevantes.
        
        Sobrescribe el método create del ModelViewSet para agregar
        lógica de notificaciones cuando se sube una evidencia importante.
        También asigna automáticamente el usuario que sube la evidencia.
        """
        # Asignar automáticamente el usuario que sube la evidencia
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Asignar subido_por antes de guardar
        evidencia = serializer.save(subido_por=request.user)
        
        # Crear notificaciones para usuarios relevantes
        try:
            from apps.notifications.utils import crear_notificacion_evidencia
            crear_notificacion_evidencia(evidencia, request.user)
        except Exception as e:
            # Si falla la creación de notificaciones, no fallar la creación de evidencia
            # Solo registrar el error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al crear notificaciones para evidencia {evidencia.id}: {e}")
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_evidencia, enviar_actualizacion_ot
            enviar_actualizacion_evidencia(evidencia, action="created")
            # También actualizar la OT para que se refresque la lista de evidencias
            if evidencia.ot:
                enviar_actualizacion_ot(evidencia.ot, action="updated")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para evidencia {evidencia.id}: {e}")
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(request=EmptySerializer, responses={200: None})
    @action(detail=False, methods=['post'], url_path='presigned')
    def presigned(self, request):
        """
        Sube un archivo directamente al backend, que lo guarda en S3 y crea el registro de evidencia.
        
        Endpoint: POST /api/v1/work/evidencias/presigned/
        
        Permisos:
        - Solo MECANICO, SUPERVISOR, ADMIN, GUARDIA, JEFE_TALLER
        
        Body (multipart/form-data):
        - file: Archivo a subir (requerido)
        - ot: UUID de la OT (opcional)
        - tipo: Tipo de evidencia (opcional, default: FOTO)
        - descripcion: Descripción (opcional)
        
        Validaciones:
        - Tamaño máximo: 3GB
        - Tipos permitidos: Imágenes, PDFs, documentos, etc.
        
        Retorna:
        - 201: {
            "evidencia": {...},
            "file_url": "http://localhost:4566/..."
          }
        - 403: Si no tiene permisos
        - 400: Si el archivo no es válido
        - 500: Si falta configuración de S3
        """
        # Verificar permisos
        if request.user.rol not in ("MECANICO", "SUPERVISOR", "ADMIN", "GUARDIA", "JEFE_TALLER"):
            return Response(
                {"detail": "No autorizado para subir evidencias."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar si hay un archivo en la petición
        if 'file' not in request.FILES:
            return Response(
                {"detail": "No se proporcionó archivo"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        ot_id = request.data.get("ot")
        tipo = request.data.get("tipo", "FOTO")
        descripcion = request.data.get("descripcion", "")
        
        # Validar archivo
        from .middleware import validate_file_upload
        validation = validate_file_upload(file, max_size_mb=3072)
        
        if not validation['valid']:
            return Response(
                {"detail": "; ".join(validation['errors'])},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener configuración de S3
        bucket = os.getenv("AWS_STORAGE_BUCKET_NAME", "pgf-evidencias-dev")
        s3_endpoint_internal = os.getenv("AWS_S3_ENDPOINT_URL", "http://localstack:4566")
        
        # URL pública para acceder a LocalStack desde el navegador
        # En producción con Cloudflare Tunnel, debe ser la URL del túnel que expone LocalStack
        # Si no está configurado AWS_PUBLIC_URL_PREFIX, intentar construir desde CLOUDFLARE_TUNNEL_URL
        # IMPORTANTE: En producción, LocalStack debe estar expuesto a través de un túnel separado
        # o el backend debe servir los archivos directamente (proxy)
        s3_endpoint_public = os.getenv("AWS_PUBLIC_URL_PREFIX")
        
        if not s3_endpoint_public:
            # Si hay URL del túnel de Cloudflare, intentar construir URL para LocalStack
            cloudflare_url = os.getenv("CLOUDFLARE_TUNNEL_URL", "").rstrip("/")
            if cloudflare_url:
                # Opción 1: LocalStack expuesto en subdominio o ruta del túnel
                # Ejemplo: https://random-name-localstack.trycloudflare.com
                # O: https://random-name.trycloudflare.com/localstack
                # Por defecto, asumimos que LocalStack está en un túnel separado con el mismo dominio base
                # Si el túnel del frontend es: https://random-name.trycloudflare.com
                # El túnel de LocalStack podría ser: https://random-name-localstack.trycloudflare.com
                # O usar el mismo túnel con ruta: https://random-name.trycloudflare.com/localstack
                # Por ahora, usamos el mismo dominio con ruta /localstack
                s3_endpoint_public = f"{cloudflare_url}/localstack"
            else:
                # Desarrollo local: usar localhost
                s3_endpoint_public = "http://localhost:4566"
        
        s3 = boto3.client(
            "s3",
            endpoint_url=s3_endpoint_internal,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
            region_name=os.getenv("AWS_S3_REGION_NAME", "us-east-1"),
        )
        
        # Generar key único para el archivo
        if ot_id:
            key = f"evidencias/ot_{ot_id}/{uuid.uuid4()}_{file.name}"
        else:
            key = f"evidencias/generales/{uuid.uuid4()}_{file.name}"
        
        try:
            # Subir archivo a S3
            s3.upload_fileobj(
                file,
                bucket,
                key,
                ExtraArgs={'ContentType': file.content_type or 'application/octet-stream'}
            )
            
            # Generar URL pública
            file_url = f"{s3_endpoint_public}/{bucket}/{key}"
            
            # Crear registro de evidencia
            ot = None
            if ot_id:
                try:
                    ot = OrdenTrabajo.objects.get(id=ot_id)
                except OrdenTrabajo.DoesNotExist:
                    pass
            
            evidencia = Evidencia.objects.create(
                ot=ot,
                url=file_url,
                tipo=tipo,
                descripcion=descripcion,
                subido_por=request.user
            )
            
            # Crear notificaciones
            try:
                from apps.notifications.utils import crear_notificacion_evidencia
                crear_notificacion_evidencia(evidencia, request.user)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al crear notificaciones para evidencia {evidencia.id}: {e}")
            
            from apps.workorders.serializers import EvidenciaSerializer
            return Response({
                "evidencia": EvidenciaSerializer(evidencia).data,
                "file_url": file_url
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al subir archivo a S3: {e}")
            return Response(
                {"detail": f"Error al subir archivo: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_destroy(self, instance):
        """
        Elimina una evidencia y su archivo asociado en S3.
        
        Permisos:
        - ADMIN, JEFE_TALLER: pueden eliminar cualquier evidencia
        - MECANICO, GUARDIA: solo pueden eliminar sus propias evidencias
        """
        user = self.request.user
        rol = getattr(user, "rol", None)
        
        # Verificar permisos
        if rol not in ("ADMIN", "JEFE_TALLER"):
            # MECANICO y GUARDIA solo pueden eliminar sus propias evidencias
            if rol in ("MECANICO", "GUARDIA"):
                if instance.subido_por != user:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Solo puedes eliminar tus propias evidencias.")
            else:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("No tienes permisos para eliminar evidencias.")
        
        # Intentar eliminar el archivo de S3
        try:
            url = instance.url
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # Determinar bucket y key
            bucket = os.getenv("AWS_STORAGE_BUCKET_NAME", "pgf-evidencias-dev")
            if parsed.netloc in ['localhost:4566', 'localstack:4566', '127.0.0.1:4566'] or 'localstack' in parsed.netloc.lower():
                path_parts = parsed.path.lstrip('/').split('/', 1)
                if len(path_parts) >= 2:
                    bucket = path_parts[0]
                    key = path_parts[1]
                else:
                    key = parsed.path.lstrip('/')
            else:
                key = parsed.path.lstrip('/').split('/', 1)[-1] if '/' in parsed.path.lstrip('/') else parsed.path.lstrip('/')
            
            # Crear cliente S3
            s3_endpoint_internal = os.getenv("AWS_S3_ENDPOINT_URL", "http://localstack:4566")
            use_local = s3_endpoint_internal and ("localstack" in s3_endpoint_internal.lower() or "localhost:4566" in s3_endpoint_internal.lower())
            
            s3 = boto3.client(
                "s3",
                endpoint_url=s3_endpoint_internal if use_local else None,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
                region_name=os.getenv("AWS_S3_REGION_NAME", "us-east-1"),
            )
            
            # Eliminar archivo de S3
            try:
                s3.delete_object(Bucket=bucket, Key=key)
            except Exception as e:
                # Si falla la eliminación del archivo, registrar pero continuar
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"No se pudo eliminar el archivo de S3 para evidencia {instance.id}: {e}")
        except Exception as e:
            # Si hay error al procesar la URL, registrar pero continuar con la eliminación del registro
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error al procesar URL de evidencia {instance.id} para eliminación: {e}")
        
        # Registrar auditoría
        try:
            Auditoria.objects.create(
                usuario=user,
                accion="ELIMINAR_EVIDENCIA",
                objeto_tipo="Evidencia",
                objeto_id=str(instance.id),
                payload={
                    "ot_id": str(instance.ot.id) if instance.ot else None,
                    "tipo": instance.tipo,
                    "descripcion": instance.descripcion
                }
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al registrar auditoría de eliminación de evidencia {instance.id}: {e}")
        
        # Guardar referencia a la OT antes de eliminar
        ot = instance.ot
        
        # Eliminar el registro de la base de datos
        instance.delete()
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_evidencia, enviar_actualizacion_ot
            # Enviar actualización de eliminación
            if ot:
                enviar_actualizacion_ot(ot, action="updated")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real al eliminar evidencia: {e}")

    @extend_schema(request=EmptySerializer, responses={200: None})
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """
        Genera una URL presignada para descargar/ver una evidencia.
        
        Endpoint: GET /api/v1/work/evidencias/{id}/download/
        
        Permisos:
        - Usa los mismos permisos que get_queryset() (basado en rol)
        
        Retorna:
        - 200: {
            "download_url": "https://s3...?signature=...",
            "expires_in": 3600
          }
        - 403: Si no tiene permisos para ver esta evidencia
        - 404: Si la evidencia no existe
        - 500: Si hay error al generar la URL presignada
        """
        evidencia = self.get_object()
        
        # Verificar permisos (get_object ya valida permisos básicos, pero verificamos acceso específico)
        user = request.user
        if not user or not user.is_authenticated:
            return Response(
                {"detail": "No autenticado."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Extraer la key de S3 de la URL almacenada
        url = evidencia.url
        
        # Parsear la URL para extraer bucket y key
        # Formatos esperados:
        # - http://localhost:4566/bucket/key (LocalStack)
        # - http://localstack:4566/bucket/key (LocalStack interno)
        # - https://bucket.s3.region.amazonaws.com/key (AWS real)
        # - https://s3.amazonaws.com/bucket/key (AWS formato antiguo - incorrecto pero puede existir)
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        # Determinar bucket y key según el formato de URL
        if parsed.netloc in ['localhost:4566', 'localstack:4566', '127.0.0.1:4566'] or 'localstack' in parsed.netloc.lower():
            # Formato LocalStack: http://localhost:4566/bucket/key
            path_parts = parsed.path.lstrip('/').split('/', 1)
            if len(path_parts) < 2:
                return Response(
                    {"detail": "URL de evidencia inválida (formato LocalStack incorrecto)."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            bucket = path_parts[0]
            key = path_parts[1]
        elif parsed.netloc == 's3.amazonaws.com' or 's3.amazonaws.com' in parsed.netloc:
            # Formato AWS antiguo: https://s3.amazonaws.com/bucket/key
            # Este formato es incorrecto pero puede existir en datos antiguos
            # Si el bucket es "bucket" (literal), usar el bucket configurado
            path_parts = parsed.path.lstrip('/').split('/', 1)
            if len(path_parts) < 2:
                return Response(
                    {"detail": "URL de evidencia inválida (formato AWS antiguo incorrecto)."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            stored_bucket = path_parts[0]
            key = path_parts[1]
            # Si el bucket almacenado es "bucket" (literal), usar el bucket configurado
            if stored_bucket == "bucket":
                bucket = os.getenv("AWS_STORAGE_BUCKET_NAME", "pgf-evidencias-dev")
            else:
                bucket = stored_bucket
        elif '.s3.' in parsed.netloc or '.s3-' in parsed.netloc:
            # Formato AWS moderno: https://bucket.s3.region.amazonaws.com/key
            bucket = parsed.netloc.split('.')[0]
            key = parsed.path.lstrip('/')
        else:
            # Intentar parsear como path-based (último recurso)
            path_parts = parsed.path.lstrip('/').split('/', 1)
            if len(path_parts) >= 2:
                bucket = path_parts[0]
                key = path_parts[1]
            else:
                return Response(
                    {"detail": f"URL de evidencia inválida. No se pudo parsear: {url}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Obtener configuración de S3
        region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        endpoint_url_internal = os.getenv("AWS_ENDPOINT_URL") or os.getenv("AWS_S3_ENDPOINT_URL") or "http://localstack:4566"
        use_local = endpoint_url_internal is not None and ("localstack" in endpoint_url_internal.lower() or "localhost:4566" in endpoint_url_internal.lower())
        
        # Crear cliente S3
        s3 = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url_internal if use_local else None,
            config=Config(s3={"addressing_style": "path"}) if use_local else None
        )
        
        try:
            # Verificar que el archivo existe antes de generar la URL presignada
            from botocore.exceptions import ClientError
            try:
                s3.head_object(Bucket=bucket, Key=key)
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == '404' or error_code == 'NoSuchKey':
                    return Response(
                        {"detail": f"El archivo de evidencia no existe en S3. Key: {key}. La evidencia puede haber sido eliminada o nunca se subió correctamente."},
                        status=status.HTTP_404_NOT_FOUND
                    )
                elif error_code == '403' or error_code == 'AccessDenied':
                    return Response(
                        {"detail": "No se tiene acceso al archivo de evidencia."},
                        status=status.HTTP_403_FORBIDDEN
                    )
                else:
                    raise
            
            # Si estamos usando LocalStack, servir el archivo directamente desde el backend
            # Esto evita problemas de Mixed Content (HTTPS -> HTTP) y CORS
            if use_local:
                try:
                    # Descargar el archivo desde LocalStack
                    from botocore.response import StreamingBody
                    response = s3.get_object(Bucket=bucket, Key=key)
                    
                    # Obtener el contenido del archivo
                    file_content = response['Body'].read()
                    content_type = response.get('ContentType', 'application/octet-stream')
                    
                    # Servir el archivo directamente desde el backend
                    from django.http import HttpResponse
                    http_response = HttpResponse(file_content, content_type=content_type)
                    http_response['Content-Disposition'] = f'inline; filename="{key.split("/")[-1]}"'
                    http_response['Cache-Control'] = 'public, max-age=3600'
                    return http_response
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error al servir archivo directamente desde LocalStack: {e}")
                    # Si falla, intentar con URL presignada como fallback
                    download_url = s3.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket, 'Key': key},
                        ExpiresIn=3600
                    )
                    return Response({
                        "download_url": download_url,
                        "expires_in": 3600,
                        "direct_url": download_url,
                        "use_proxy": True
                    })
            
            # Para AWS real, devolver URL presignada
            download_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=3600
            )
            
            return Response({
                "download_url": download_url,
                "expires_in": 3600
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al generar URL presignada para evidencia {evidencia.id}: {e}")
            return Response(
                {"detail": f"Error al generar URL de descarga: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============== COMENTARIOS EN OT =================
class ComentarioOTViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de comentarios en OT.
    
    Endpoints:
    - GET /api/v1/work/comentarios/ → Listar comentarios
    - POST /api/v1/work/comentarios/ → Crear comentario
    - GET /api/v1/work/comentarios/{id}/ → Ver comentario
    - PUT/PATCH /api/v1/work/comentarios/{id}/ → Editar comentario
    - DELETE /api/v1/work/comentarios/{id}/ → Eliminar comentario
    """
    queryset = ComentarioOT.objects.select_related("usuario", "ot").all().order_by("creado_en")
    serializer_class = ComentarioOTSerializer
    permission_classes = [WorkOrderPermission]
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["ot", "usuario"]
    ordering_fields = ["creado_en"]
    
    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario.
        
        - MECANICO: Solo comentarios de OTs asignadas a él
        - Otros roles: Sin filtrado adicional
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        rol = getattr(user, "rol", None)
        
        # MECANICO: Solo comentarios de OTs asignadas a él
        if rol == "MECANICO":
            return queryset.filter(ot__mecanico=user)
        
        return queryset
    
    def perform_create(self, serializer):
        """Asignar usuario automáticamente al crear comentario."""
        comentario = serializer.save(usuario=self.request.user)
        
        # Notificar a usuarios mencionados
        menciones = comentario.menciones or []
        
        if menciones:
            try:
                from apps.notifications.utils import crear_notificacion_ot_comentario
                crear_notificacion_ot_comentario(comentario, menciones)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al crear notificaciones de comentario {comentario.id}: {e}")
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_comentario, enviar_actualizacion_ot
            enviar_actualizacion_comentario(comentario, action="created")
            # También actualizar la OT para que se refresque la lista de comentarios
            if comentario.ot:
                enviar_actualizacion_ot(comentario.ot, action="updated")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para comentario {comentario.id}: {e}")
    
    def perform_update(self, serializer):
        """Marcar comentario como editado."""
        comentario = serializer.save(editado=True, editado_en=timezone.now())
        
        # Enviar actualización en tiempo real
        try:
            from apps.notifications.realtime import enviar_actualizacion_comentario, enviar_actualizacion_ot
            enviar_actualizacion_comentario(comentario, action="updated")
            # También actualizar la OT
            if comentario.ot:
                enviar_actualizacion_ot(comentario.ot, action="updated")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar actualización en tiempo real para comentario {comentario.id}: {e}")


# ============== TIMELINE DE OT =================
@extend_schema(
    description="Obtiene el timeline consolidado de una OT",
    responses={200: None}
)
@api_view(['GET'])
@permission_classes([WorkOrderPermission])
def timeline_ot(request, ot_id):
    """
    Endpoint para obtener el timeline consolidado de una OT.
    
    Retorna:
    - Cambios de estado (de Auditoria)
    - Comentarios
    - Evidencias
    - Pausas
    - Checklists
    - Actores (usuarios involucrados)
    
    Endpoint: GET /api/v1/work/ordenes/{ot_id}/timeline/
    """
    try:
        ot = OrdenTrabajo.objects.get(id=ot_id)
    except OrdenTrabajo.DoesNotExist:
        return Response(
            {"detail": "OT no encontrada."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Obtener TODAS las acciones de auditoría (no solo cambios de estado)
    todas_auditorias = Auditoria.objects.filter(
        objeto_tipo="OrdenTrabajo",
        objeto_id=str(ot_id)
    ).select_related('usuario').order_by("ts")
    
    # Obtener cambios de estado desde Auditoria (para compatibilidad)
    cambios_estado = Auditoria.objects.filter(
        objeto_tipo="OrdenTrabajo",
        objeto_id=str(ot_id),
        accion__in=["CAMBIO_ESTADO", "TRANSICION_ESTADO", "EN_EJECUCION", "EN_QA", "CERRAR_OT", 
                   "DIAGNOSTICO_OT", "APROBAR_ASIGNACION_OT", "RETRABAJO_OT", "OT_ESPERANDO_REPUESTOS"]
    ).select_related('usuario').order_by("ts")
    
    # Obtener comentarios
    comentarios = ComentarioOT.objects.filter(ot=ot).order_by("creado_en")
    
    # Obtener evidencias
    evidencias = Evidencia.objects.filter(ot=ot).order_by("subido_en")
    
    # Obtener pausas
    pausas = Pausa.objects.filter(ot=ot).order_by("inicio")
    
    # Obtener checklists
    checklists = Checklist.objects.filter(ot=ot).order_by("fecha")
    
    # Construir timeline
    timeline = []
    
    # Agregar creación de OT
    timeline.append({
        "tipo": "creacion",
        "fecha": ot.apertura.isoformat() if hasattr(ot.apertura, 'isoformat') else str(ot.apertura),
        "usuario": None,
        "accion": "OT creada",
        "detalle": {
            "estado": ot.estado,
            "motivo": ot.motivo or ""
        }
    })
    
    # Agregar cambios de estado
    for cambio in cambios_estado:
        timeline.append({
            "tipo": "cambio_estado",
            "fecha": cambio.ts.isoformat() if hasattr(cambio.ts, 'isoformat') else str(cambio.ts),
            "usuario": {
                "id": str(cambio.usuario.id) if cambio.usuario else None,
                "nombre": cambio.usuario.get_full_name() if cambio.usuario else "Sistema",
                "rol": cambio.usuario.rol if cambio.usuario else None
            },
            "accion": cambio.accion,
            "detalle": cambio.payload
        })
    
    # Agregar comentarios
    for comentario in comentarios:
        timeline.append({
            "tipo": "comentario",
            "fecha": comentario.creado_en.isoformat() if hasattr(comentario.creado_en, 'isoformat') else str(comentario.creado_en),
            "usuario": {
                "id": str(comentario.usuario.id) if comentario.usuario else None,
                "nombre": comentario.usuario.get_full_name() if comentario.usuario else "Sistema",
                "rol": comentario.usuario.rol if comentario.usuario else None
            },
            "accion": "Comentario agregado",
            "detalle": {
                "contenido": comentario.contenido or "",
                "menciones": comentario.menciones or [],
                "editado": comentario.editado if hasattr(comentario, 'editado') else False
            }
        })
    
    # Agregar evidencias
    for evidencia in evidencias:
        timeline.append({
            "tipo": "evidencia",
            "fecha": evidencia.subido_en.isoformat() if hasattr(evidencia.subido_en, 'isoformat') else str(evidencia.subido_en),
            "usuario": {
                "id": str(evidencia.subido_por.id) if evidencia.subido_por else None,
                "nombre": evidencia.subido_por.get_full_name() if evidencia.subido_por else "Sistema",
                "rol": evidencia.subido_por.rol if evidencia.subido_por else None
            },
            "accion": "Evidencia subida",
            "detalle": {
                "tipo": evidencia.tipo,
                "descripcion": evidencia.descripcion,
                "url": evidencia.url,
                "invalidado": evidencia.invalidado,
                "invalidado_por": evidencia.invalidado_por.get_full_name() if evidencia.invalidado_por else None,
                "invalidado_en": evidencia.invalidado_en.isoformat() if evidencia.invalidado_en and hasattr(evidencia.invalidado_en, 'isoformat') else (str(evidencia.invalidado_en) if evidencia.invalidado_en else None),
                "motivo_invalidacion": evidencia.motivo_invalidacion
            }
        })
    
    # Agregar pausas
    for pausa in pausas:
        timeline.append({
            "tipo": "pausa",
            "fecha": pausa.inicio.isoformat() if hasattr(pausa.inicio, 'isoformat') else str(pausa.inicio),
            "usuario": {
                "id": str(pausa.usuario.id) if pausa.usuario else None,
                "nombre": pausa.usuario.get_full_name() if pausa.usuario else "Sistema",
                "rol": pausa.usuario.rol if pausa.usuario else None
            },
            "accion": f"Pausa: {pausa.tipo}",
            "detalle": {
                "motivo": pausa.motivo or "",
                "duracion_minutos": pausa.duracion_minutos if hasattr(pausa, 'duracion_minutos') else None,
                "es_automatica": pausa.es_automatica if hasattr(pausa, 'es_automatica') else False
            }
        })
    
    # Agregar checklists
    for checklist in checklists:
        timeline.append({
            "tipo": "checklist",
            "fecha": checklist.fecha.isoformat() if hasattr(checklist.fecha, 'isoformat') else str(checklist.fecha),
            "usuario": {
                "id": str(checklist.verificador.id) if checklist.verificador else None,
                "nombre": checklist.verificador.get_full_name() if checklist.verificador else "Sistema",
                "rol": checklist.verificador.rol if checklist.verificador else None
            },
            "accion": f"Checklist: {checklist.resultado}",
            "detalle": {
                "resultado": checklist.resultado,
                "observaciones": checklist.observaciones,
                "fecha": checklist.fecha.isoformat() if hasattr(checklist.fecha, 'isoformat') else str(checklist.fecha)
            }
        })
    
    # Ordenar por fecha
    timeline.sort(key=lambda x: x["fecha"])
    
    # Obtener actores (usuarios involucrados) - incluir también usuarios de auditoría
    actores = set()
    if ot.supervisor:
        actores.add((str(ot.supervisor.id), ot.supervisor.get_full_name(), ot.supervisor.rol))
    if ot.jefe_taller:
        actores.add((str(ot.jefe_taller.id), ot.jefe_taller.get_full_name(), ot.jefe_taller.rol))
    if ot.mecanico:
        actores.add((str(ot.mecanico.id), ot.mecanico.get_full_name(), ot.mecanico.rol))
    if ot.responsable:
        actores.add((str(ot.responsable.id), ot.responsable.get_full_name(), ot.responsable.rol))
    
    # Agregar usuarios de auditoría
    for auditoria in todas_auditorias:
        if auditoria.usuario:
            actores.add((str(auditoria.usuario.id), auditoria.usuario.get_full_name(), auditoria.usuario.rol))
    
    # Agregar usuarios de evidencias
    for evidencia in evidencias:
        if evidencia.subido_por:
            actores.add((str(evidencia.subido_por.id), evidencia.subido_por.get_full_name(), evidencia.subido_por.rol))
    
    return Response({
        "ot_id": str(ot.id),
        "timeline": timeline,
        "actores": [
            {"id": a[0], "nombre": a[1], "rol": a[2]} for a in actores
        ]
    })


# ============== INVALIDAR EVIDENCIA =================
@extend_schema(
    description="Invalida una evidencia y crea una versión en el historial",
    request=EmptySerializer,
    responses={200: None}
)
@api_view(['POST'])
@permission_classes([WorkOrderPermission])
@transaction.atomic
def invalidar_evidencia(request, evidencia_id):
    """
    Invalida una evidencia y crea un registro en el historial de versiones.
    
    Solo roles permitidos pueden invalidar evidencias:
    - JEFE_TALLER
    - ADMIN
    - SUPERVISOR
    
    Endpoint: POST /api/v1/work/evidencias/{evidencia_id}/invalidar/
    """
    # Verificar permisos
    if request.user.rol not in ["JEFE_TALLER", "ADMIN", "SUPERVISOR"]:
        return Response(
            {"detail": "No tiene permisos para invalidar evidencias."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        evidencia = Evidencia.objects.get(id=evidencia_id)
    except Evidencia.DoesNotExist:
        return Response(
            {"detail": "Evidencia no encontrada."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validar que no esté ya invalidada
    if evidencia.invalidado:
        return Response(
            {"detail": "La evidencia ya está invalidada."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Obtener motivo de invalidación
    motivo = request.data.get("motivo", "")
    if not motivo:
        return Response(
            {"detail": "El motivo de invalidación es obligatorio."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Guardar URL anterior antes de invalidar
    url_anterior = evidencia.url
    
    # Invalidar evidencia
    evidencia.invalidado = True
    evidencia.invalidado_por = request.user
    evidencia.invalidado_en = timezone.now()
    evidencia.motivo_invalidacion = motivo
    evidencia.save()
    
    # Crear versión en el historial
    VersionEvidencia.objects.create(
        evidencia_original=evidencia,
        url_anterior=url_anterior,
        invalidado_por=request.user,
        motivo=motivo
    )
    
    # Registrar auditoría
    Auditoria.objects.create(
        usuario=request.user,
        accion="INVALIDAR_EVIDENCIA",
        objeto_tipo="Evidencia",
        objeto_id=str(evidencia.id),
        payload={
            "ot_id": str(evidencia.ot.id) if evidencia.ot else None,
            "motivo": motivo
        }
    )
    
    return Response({
        "detail": "Evidencia invalidada correctamente.",
        "evidencia": EvidenciaSerializer(evidencia).data
    })


# ============== AUDITORÍA =================
class AuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar registros de auditoría.
    
    Endpoints:
    - GET /api/v1/work/auditoria/ → Listar registros de auditoría
    - GET /api/v1/work/auditoria/{id}/ → Ver registro específico
    
    Permisos:
    - Solo ADMIN puede acceder
    
    Filtros:
    - Por acción, objeto_tipo, usuario
    - Búsqueda por objeto_id
    - Ordenamiento por ts (timestamp)
    """
    queryset = Auditoria.objects.select_related("usuario").all().order_by("-ts")
    serializer_class = AuditoriaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["accion", "objeto_tipo", "usuario"]
    search_fields = ["objeto_id", "accion", "objeto_tipo"]
    ordering_fields = ["ts", "accion"]
    ordering = ["-ts"]  # Más recientes primero
    
    def get_queryset(self):
        """Solo ADMIN puede ver auditoría."""
        if self.request.user.rol != "ADMIN":
            return Auditoria.objects.none()
        return super().get_queryset()
    
    @extend_schema(
        description="Obtiene cambios críticos recientes del sistema",
        responses={200: None}
    )
    @action(detail=False, methods=['get'], url_path='cambios-criticos')
    def cambios_criticos(self, request):
        """
        Retorna los últimos cambios críticos del sistema.
        
        Cambios críticos incluyen:
        - Cambios de estado de OT (CERRAR_OT, ANULAR_OT, etc.)
        - Invalidación de evidencias
        - Cambios de prioridad
        - Aprobaciones/rechazos de presupuestos
        - Cambios de usuario/permisos
        """
        if request.user.rol != "ADMIN":
            return Response(
                {"detail": "No autorizado."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Acciones críticas
        acciones_criticas = [
            "CERRAR_OT", "ANULAR_OT", "INVALIDAR_EVIDENCIA",
            "CAMBIAR_PRIORIDAD", "APROBAR_PRESUPUESTO", "RECHAZAR_PRESUPUESTO",
            "CREAR_USUARIO", "ELIMINAR_USUARIO", "CAMBIAR_ROL"
        ]
        
        cambios = Auditoria.objects.filter(
            accion__in=acciones_criticas
        ).select_related("usuario").order_by("-ts")[:50]  # Últimos 50 cambios
        
        serializer = self.get_serializer(cambios, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Obtiene resumen de actividad por usuario",
        responses={200: None}
    )
    @action(detail=False, methods=['get'], url_path='actividad-usuario')
    def actividad_usuario(self, request):
        """
        Retorna un resumen de actividad por usuario.
        
        Agrupa las acciones por usuario y cuenta cuántas acciones
        realizó cada uno en los últimos 30 días.
        """
        if request.user.rol != "ADMIN":
            return Response(
                {"detail": "No autorizado."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.db.models import Count
        from datetime import timedelta
        
        # Últimos 30 días
        fecha_limite = timezone.now() - timedelta(days=30)
        
        # Agrupar por usuario y contar acciones
        actividad = Auditoria.objects.filter(
            ts__gte=fecha_limite,
            usuario__isnull=False
        ).values(
            'usuario__id',
            'usuario__username',
            'usuario__first_name',
            'usuario__last_name',
            'usuario__rol'
        ).annotate(
            total_acciones=Count('id')
        ).order_by('-total_acciones')[:20]  # Top 20 usuarios más activos
        
        # Formatear respuesta
        resultado = []
        for item in actividad:
            resultado.append({
                "usuario_id": str(item['usuario__id']),
                "username": item['usuario__username'],
                "nombre_completo": f"{item['usuario__first_name']} {item['usuario__last_name']}".strip() or item['usuario__username'],
                "rol": item['usuario__rol'],
                "total_acciones": item['total_acciones']
            })
        
        return Response(resultado)
    
    @extend_schema(
        description="Obtiene evidencias marcadas como inválidas",
        responses={200: None}
    )
    @action(detail=False, methods=['get'], url_path='evidencias-invalidadas')
    def evidencias_invalidadas(self, request):
        """
        Retorna todas las evidencias que han sido invalidadas.
        """
        if request.user.rol != "ADMIN":
            return Response(
                {"detail": "No autorizado."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        evidencias = Evidencia.objects.filter(
            invalidado=True
        ).select_related(
            "ot", "invalidado_por", "subido_por"
        ).order_by("-invalidado_en")
        
        # Usar el serializer de evidencias
        from .serializers import EvidenciaSerializer
        serializer = EvidenciaSerializer(evidencias, many=True)
        return Response(serializer.data)

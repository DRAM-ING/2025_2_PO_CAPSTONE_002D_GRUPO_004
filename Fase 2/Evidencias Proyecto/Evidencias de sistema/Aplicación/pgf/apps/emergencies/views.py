# apps/emergencies/views.py
"""
Vistas y ViewSets para gestión de emergencias en ruta.

Este módulo define todos los endpoints de la API relacionados con:
- Emergencias en Ruta: Gestión de emergencias de vehículos en carretera

Relaciones:
- Usa: apps/emergencies/models.py (EmergenciaRuta)
- Usa: apps/emergencies/serializers.py (serializers para validación)
- Usa: apps/vehicles/models.py (Vehiculo)
- Usa: apps/users/models.py (User)
- Usa: apps/workorders/models.py (OrdenTrabajo)
- Conectado a: apps/emergencies/urls.py

Endpoints principales:
- /api/v1/emergencies/ → CRUD de emergencias
- /api/v1/emergencies/{id}/aprobar/ → Aprobar emergencia
- /api/v1/emergencies/{id}/asignar-supervisor/ → Asignar supervisor
- /api/v1/emergencies/{id}/asignar-mecanico/ → Asignar mecánico
- /api/v1/emergencies/{id}/resolver/ → Marcar como resuelta
- /api/v1/emergencies/{id}/cerrar/ → Cerrar emergencia
- /api/v1/emergencies/{id}/rechazar/ → Rechazar emergencia

Flujo de estados:
SOLICITADA -> APROBADA -> ASIGNADA -> EN_CAMINO -> EN_SITIO -> RESUELTA -> CERRADA
                ↓
            RECHAZADA
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Q
from .models import EmergenciaRuta
from .serializers import (
    EmergenciaRutaSerializer,
    EmergenciaRutaListSerializer,
    EmergenciaRutaCreateSerializer
)
from apps.workorders.models import OrdenTrabajo


class EmergenciaRutaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de emergencias en ruta.
    
    Proporciona endpoints CRUD completos y acciones personalizadas:
    - GET /api/v1/emergencies/ → Listar emergencias (serializer simplificado)
    - POST /api/v1/emergencies/ → Crear emergencia
    - GET /api/v1/emergencies/{id}/ → Ver emergencia (serializer completo)
    - PUT/PATCH /api/v1/emergencies/{id}/ → Editar emergencia
    - DELETE /api/v1/emergencies/{id}/ → Eliminar emergencia
    
    Acciones personalizadas:
    - POST /api/v1/emergencies/{id}/aprobar/ → Aprobar emergencia
    - POST /api/v1/emergencies/{id}/asignar-supervisor/ → Asignar supervisor
    - POST /api/v1/emergencies/{id}/asignar-mecanico/ → Asignar mecánico
    - POST /api/v1/emergencies/{id}/resolver/ → Marcar como resuelta
    - POST /api/v1/emergencies/{id}/cerrar/ → Cerrar emergencia
    - POST /api/v1/emergencies/{id}/rechazar/ → Rechazar emergencia
    
    Permisos:
    - Requiere autenticación
    - Filtrado por rol (cada rol ve solo sus emergencias)
    
    Filtros:
    - Por estado, prioridad, zona
    - Búsqueda por patente, descripción, ubicación
    - Ordenamiento por fecha_solicitud, prioridad
    """
    queryset = EmergenciaRuta.objects.select_related(
        "vehiculo", "solicitante", "aprobador",
        "supervisor_asignado", "mecanico_asignado"
    ).all()
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "prioridad", "zona"]
    search_fields = ["vehiculo__patente", "descripcion", "ubicacion"]
    ordering_fields = ["fecha_solicitud", "prioridad"]
    ordering = ["-fecha_solicitud"]  # Más recientes primero
    
    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.
        
        - create: Usa EmergenciaRutaCreateSerializer (validaciones especiales)
        - list: Usa EmergenciaRutaListSerializer (menos campos)
        - retrieve/update: Usa EmergenciaRutaSerializer (todos los campos)
        """
        if self.action == "create":
            return EmergenciaRutaCreateSerializer
        if self.action == "list":
            return EmergenciaRutaListSerializer
        return EmergenciaRutaSerializer
    
    def get_queryset(self):
        """
        Filtrar emergencias según rol del usuario.
        
        Lógica:
        - MECANICO: Ve solo sus emergencias asignadas
        - SUPERVISOR: Ve emergencias asignadas a él
        - COORDINADOR_ZONA: Ve emergencias que solicitó
        - JEFE_TALLER/ADMIN: Ven todas
        
        Retorna:
        - QuerySet filtrado según permisos
        """
        user = self.request.user
        
        # Verificar que el usuario tenga rol
        if not hasattr(user, 'rol') or not user.rol:
            return EmergenciaRuta.objects.none()
        
        queryset = super().get_queryset()
        
        # Mecánico ve solo sus emergencias asignadas
        if user.rol == "MECANICO":
            return queryset.filter(mecanico_asignado=user)
        
        # Supervisor ve emergencias asignadas a él
        if user.rol == "SUPERVISOR":
            return queryset.filter(supervisor_asignado=user)
        
        # Coordinador ve emergencias que solicitó
        if user.rol == "COORDINADOR_ZONA":
            return queryset.filter(solicitante=user)
        
        # Jefe de Taller, Admin, Ejecutivo, Sponsor ven todas
        if user.rol in ["JEFE_TALLER", "ADMIN", "EJECUTIVO", "SPONSOR"]:
            return queryset
        
        # Por defecto, no mostrar nada si el rol no está contemplado
        return queryset.none()
    
    def perform_create(self, serializer):
        """
        Crea una emergencia y asigna el solicitante automáticamente.
        
        Este método se ejecuta al crear una emergencia.
        
        Validaciones:
        - Solo SUPERVISOR o COORDINADOR_ZONA pueden solicitar
        
        Proceso:
        1. Valida permisos
        2. Asigna solicitante automáticamente
        3. Establece estado inicial a SOLICITADA
        """
        user = self.request.user
        
        # Solo Supervisor, Coordinador o Admin pueden solicitar
        if user.rol not in ["SUPERVISOR", "COORDINADOR_ZONA", "ADMIN"]:
            raise PermissionDenied(
                "Solo Supervisores, Coordinadores o Administradores pueden solicitar emergencias"
            )
        
        serializer.save(solicitante=user, estado="SOLICITADA")
    
    @action(detail=True, methods=["post"])
    def aprobar(self, request, pk=None):
        """
        Aprueba una emergencia.
        
        Endpoint: POST /api/v1/emergencies/{id}/aprobar/
        
        Permisos:
        - Solo JEFE_TALLER, ADMIN, EJECUTIVO o SPONSOR
        
        Requisitos:
        - La emergencia debe estar en SOLICITADA
        
        Proceso:
        1. Valida permisos y estado
        2. Cambia estado a APROBADA
        3. Asigna aprobador
        4. Establece fecha_aprobacion
        
        Retorna:
        - 200: Emergencia serializada
        - 403: Si no tiene permisos
        - 400: Si el estado no permite aprobar
        """
        emergencia = self.get_object()
        user = request.user
        
        # Solo Jefe de Taller, Admin o roles superiores pueden aprobar
        if user.rol not in ["JEFE_TALLER", "ADMIN", "EJECUTIVO", "SPONSOR"]:
            return Response(
                {"detail": "No tienes permisos para aprobar emergencias"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if emergencia.estado != "SOLICITADA":
            return Response(
                {"detail": f"La emergencia está en estado {emergencia.estado}, no se puede aprobar"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        emergencia.estado = "APROBADA"
        emergencia.aprobador = user
        emergencia.fecha_aprobacion = timezone.now()
        emergencia.save()
        
        return Response(EmergenciaRutaSerializer(emergencia).data)
    
    @action(detail=True, methods=["post"])
    def asignar_supervisor(self, request, pk=None):
        """
        Asigna un supervisor a la emergencia.
        
        Endpoint: POST /api/v1/emergencies/{id}/asignar-supervisor/
        
        Permisos:
        - Solo COORDINADOR_ZONA, SUPERVISOR o ADMIN
        
        Body JSON:
        {
            "supervisor_id": "uuid-del-supervisor"
        }
        
        Proceso:
        1. Valida permisos
        2. Busca supervisor (debe tener rol SUPERVISOR o COORDINADOR_ZONA)
        3. Asigna supervisor
        4. Si está APROBADA, cambia a ASIGNADA
        
        Retorna:
        - 200: Emergencia serializada
        - 403: Si no tiene permisos
        - 400: Si falta supervisor_id
        - 404: Si el supervisor no existe
        """
        emergencia = self.get_object()
        user = request.user
        supervisor_id = request.data.get("supervisor_id")
        
        # Solo Coordinador o Supervisor pueden asignar
        if user.rol not in ["COORDINADOR_ZONA", "SUPERVISOR", "ADMIN"]:
            return Response(
                {"detail": "No tienes permisos para asignar supervisor"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not supervisor_id:
            return Response(
                {"detail": "Se requiere supervisor_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.users.models import User
        try:
            supervisor = User.objects.get(id=supervisor_id, rol__in=["SUPERVISOR", "COORDINADOR_ZONA"])
        except User.DoesNotExist:
            return Response(
                {"detail": "Supervisor no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        emergencia.supervisor_asignado = supervisor
        if emergencia.estado == "APROBADA":
            emergencia.estado = "ASIGNADA"
            emergencia.fecha_asignacion = timezone.now()
        emergencia.save()
        
        return Response(EmergenciaRutaSerializer(emergencia).data)
    
    @action(detail=True, methods=["post"])
    def asignar_mecanico(self, request, pk=None):
        """
        Asigna un mecánico a la emergencia y crea OT automáticamente.
        
        Endpoint: POST /api/v1/emergencies/{id}/asignar-mecanico/
        
        Permisos:
        - Solo SUPERVISOR o ADMIN
        
        Body JSON:
        {
            "mecanico_id": "uuid-del-mecanico"
        }
        
        Proceso:
        1. Valida permisos
        2. Busca mecánico (debe tener rol MECANICO)
        3. Asigna mecánico
        4. Cambia estado a ASIGNADA
        5. Crea OT automáticamente con tipo EMERGENCIA
        6. Vincula OT con emergencia
        
        Retorna:
        - 200: Emergencia serializada
        - 403: Si no tiene permisos
        - 400: Si falta mecanico_id
        - 404: Si el mecánico no existe
        """
        emergencia = self.get_object()
        user = request.user
        mecanico_id = request.data.get("mecanico_id")
        
        # Solo Supervisor puede asignar mecánico
        if user.rol not in ["SUPERVISOR", "ADMIN"]:
            return Response(
                {"detail": "Solo Supervisores pueden asignar mecánicos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not mecanico_id:
            return Response(
                {"detail": "Se requiere mecanico_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.users.models import User
        try:
            mecanico = User.objects.get(id=mecanico_id, rol="MECANICO")
        except User.DoesNotExist:
            return Response(
                {"detail": "Mecánico no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        emergencia.mecanico_asignado = mecanico
        emergencia.estado = "ASIGNADA"
        emergencia.fecha_asignacion = timezone.now()
        emergencia.save()
        
        # Crear OT asociada automáticamente
        ot = OrdenTrabajo.objects.create(
            vehiculo=emergencia.vehiculo,
            supervisor=emergencia.supervisor_asignado,
            mecanico=mecanico,
            estado="EN_EJECUCION",  # Emergencias van directo a ejecución
            tipo="EMERGENCIA",
            prioridad=emergencia.prioridad,
            motivo=f"Emergencia en ruta: {emergencia.descripcion}",
            zona=emergencia.zona
        )
        
        emergencia.ot_asociada = ot
        emergencia.save()
        
        return Response(EmergenciaRutaSerializer(emergencia).data)
    
    @action(detail=True, methods=["post"])
    def resolver(self, request, pk=None):
        """
        Marca la emergencia como resuelta.
        
        Endpoint: POST /api/v1/emergencies/{id}/resolver/
        
        Permisos:
        - Solo el mecánico asignado puede resolver
        
        Proceso:
        1. Valida que el usuario sea el mecánico asignado
        2. Cambia estado a RESUELTA
        3. Establece fecha_resolucion
        
        Retorna:
        - 200: Emergencia serializada
        - 403: Si no es el mecánico asignado
        """
        emergencia = self.get_object()
        user = request.user
        
        # Solo el mecánico asignado puede resolver
        if emergencia.mecanico_asignado != user:
            return Response(
                {"detail": "Solo el mecánico asignado puede resolver la emergencia"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        emergencia.estado = "RESUELTA"
        emergencia.fecha_resolucion = timezone.now()
        emergencia.save()
        
        return Response(EmergenciaRutaSerializer(emergencia).data)
    
    @action(detail=True, methods=["post"])
    def cerrar(self, request, pk=None):
        """
        Cierra la emergencia.
        
        Endpoint: POST /api/v1/emergencies/{id}/cerrar/
        
        Permisos:
        - Solo SUPERVISOR o ADMIN
        
        Requisitos:
        - La emergencia debe estar en RESUELTA
        
        Proceso:
        1. Valida permisos y estado
        2. Cambia estado a CERRADA
        3. Establece fecha_cierre
        4. Cierra OT asociada (si existe)
        
        Retorna:
        - 200: Emergencia serializada
        - 403: Si no tiene permisos
        - 400: Si el estado no permite cerrar
        """
        emergencia = self.get_object()
        user = request.user
        
        # Solo Supervisor puede cerrar
        if user.rol not in ["SUPERVISOR", "ADMIN"]:
            return Response(
                {"detail": "Solo Supervisores pueden cerrar emergencias"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if emergencia.estado != "RESUELTA":
            return Response(
                {"detail": "La emergencia debe estar resuelta para cerrarse"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        emergencia.estado = "CERRADA"
        emergencia.fecha_cierre = timezone.now()
        emergencia.save()
        
        # Cerrar OT asociada si existe
        if emergencia.ot_asociada:
            emergencia.ot_asociada.estado = "CERRADA"
            emergencia.ot_asociada.cierre = timezone.now()
            emergencia.ot_asociada.save()
        
        return Response(EmergenciaRutaSerializer(emergencia).data)
    
    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        """
        Rechaza una emergencia.
        
        Endpoint: POST /api/v1/emergencies/{id}/rechazar/
        
        Permisos:
        - Solo JEFE_TALLER, ADMIN, EJECUTIVO o SPONSOR
        
        Body JSON:
        {
            "motivo": "Motivo del rechazo"  // Opcional
        }
        
        Proceso:
        1. Valida permisos
        2. Cambia estado a RECHAZADA
        3. Agrega motivo a observaciones
        
        Retorna:
        - 200: Emergencia serializada
        - 403: Si no tiene permisos
        """
        emergencia = self.get_object()
        user = request.user
        
        # Solo quien puede aprobar puede rechazar
        if user.rol not in ["JEFE_TALLER", "ADMIN", "EJECUTIVO", "SPONSOR"]:
            return Response(
                {"detail": "No tienes permisos para rechazar emergencias"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        motivo = request.data.get("motivo", "")
        emergencia.estado = "RECHAZADA"
        emergencia.observaciones = f"Rechazada: {motivo}"
        emergencia.save()
        
        return Response(EmergenciaRutaSerializer(emergencia).data)

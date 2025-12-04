# apps/scheduling/views.py
"""
Vistas y ViewSets para gestión de agenda y programación.

Este módulo define todos los endpoints de la API relacionados con:
- Agenda: Programación de mantenimientos y reparaciones
- Cupos Diarios: Control de disponibilidad de cupos en el taller

Relaciones:
- Usa: apps/scheduling/models.py (Agenda, CupoDiario)
- Usa: apps/scheduling/serializers.py (serializers para validación)
- Usa: apps/vehicles/models.py (Vehiculo)
- Usa: apps/workorders/models.py (OrdenTrabajo)
- Conectado a: apps/scheduling/urls.py

Endpoints principales:
- /api/v1/scheduling/agendas/ → CRUD de agendas
- /api/v1/scheduling/agendas/{id}/reprogramar/ → Reprogramar agenda
- /api/v1/scheduling/agendas/{id}/cancelar/ → Cancelar agenda
- /api/v1/scheduling/agendas/disponibilidad/ → Verificar disponibilidad
- /api/v1/scheduling/cupos/ → Listar cupos diarios
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Q
from .models import Agenda, CupoDiario
from .serializers import AgendaSerializer, AgendaListSerializer, CupoDiarioSerializer
from apps.workorders.models import OrdenTrabajo
from apps.core.audit_logging import log_audit, log_data_change, get_client_ip


class AgendaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de agenda y programación.
    
    Proporciona endpoints CRUD completos y acciones personalizadas:
    - GET /api/v1/scheduling/agendas/ → Listar agendas (serializer simplificado)
    - POST /api/v1/scheduling/agendas/ → Crear agenda
    - GET /api/v1/scheduling/agendas/{id}/ → Ver agenda (serializer completo)
    - PUT/PATCH /api/v1/scheduling/agendas/{id}/ → Editar agenda
    - DELETE /api/v1/scheduling/agendas/{id}/ → Eliminar agenda
    
    Acciones personalizadas:
    - POST /api/v1/scheduling/agendas/{id}/reprogramar/ → Reprogramar
    - POST /api/v1/scheduling/agendas/{id}/cancelar/ → Cancelar
    - GET /api/v1/scheduling/agendas/disponibilidad/ → Verificar disponibilidad
    
    Permisos:
    - Requiere autenticación
    - Solo COORDINADOR_ZONA puede crear agendas
    - Filtrado por rol (cada rol ve solo sus agendas)
    
    Filtros:
    - Por estado, tipo_mantenimiento, zona
    - Búsqueda por patente, motivo
    - Ordenamiento por fecha_programada, created_at
    """
    queryset = Agenda.objects.select_related("vehiculo", "coordinador").all()
    serializer_class = AgendaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "tipo_mantenimiento", "zona"]
    search_fields = ["vehiculo__patente", "motivo"]
    ordering_fields = ["fecha_programada", "created_at"]
    ordering = ["fecha_programada"]  # Orden por defecto: más próximas primero
    
    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.
        
        - list: Usa AgendaListSerializer (menos campos)
        - create/update/retrieve: Usa AgendaSerializer (todos los campos)
        """
        if self.action == "list":
            return AgendaListSerializer
        return AgendaSerializer
    
    def perform_update(self, serializer):
        """Registra auditoría al actualizar una agenda."""
        instance = serializer.instance
        old_data = {
            "estado": instance.estado,
            "fecha_programada": instance.fecha_programada.isoformat() if instance.fecha_programada else None,
            "tipo_mantenimiento": instance.tipo_mantenimiento
        }
        agenda = serializer.save()
        new_data = {
            "estado": agenda.estado,
            "fecha_programada": agenda.fecha_programada.isoformat() if agenda.fecha_programada else None,
            "tipo_mantenimiento": agenda.tipo_mantenimiento
        }
        
        # Detectar cambios
        cambios = {}
        for campo, valor_anterior in old_data.items():
            valor_nuevo = new_data.get(campo)
            if valor_anterior != valor_nuevo:
                cambios[campo] = {"antes": valor_anterior, "despues": valor_nuevo}
        
        ip = get_client_ip(self.request)
        if cambios:
            log_data_change(
                usuario=self.request.user,
                accion="ACTUALIZAR_AGENDA",
                objeto_tipo="Agenda",
                objeto_id=str(agenda.id),
                cambios=cambios,
                ip_address=ip
            )
        else:
            log_audit(
                usuario=self.request.user,
                accion="ACTUALIZAR_AGENDA",
                objeto_tipo="Agenda",
                objeto_id=str(agenda.id),
                payload={"vehiculo_id": str(agenda.vehiculo.id) if agenda.vehiculo else None},
                ip_address=ip
            )
    
    def perform_destroy(self, instance):
        """Registra auditoría al eliminar una agenda."""
        agenda_id = str(instance.id)
        vehiculo_id = str(instance.vehiculo.id) if instance.vehiculo else None
        fecha = instance.fecha_programada.isoformat() if instance.fecha_programada else None
        instance.delete()
        ip = get_client_ip(self.request)
        log_audit(
            usuario=self.request.user,
            accion="ELIMINAR_AGENDA",
            objeto_tipo="Agenda",
            objeto_id=agenda_id,
            payload={
                "vehiculo_id": vehiculo_id,
                "fecha_programada": fecha
            },
            nivel='WARNING',
            ip_address=ip
        )
    
    def get_queryset(self):
        """
        Filtrar agendas según rol del usuario.
        
        Lógica:
        - COORDINADOR_ZONA: Ve solo sus agendas
        - SUPERVISOR/ADMIN/JEFE_TALLER: Ven todas
        - Otros roles: No ven ninguna
        
        Retorna:
        - QuerySet filtrado según permisos
        """
        user = self.request.user
        queryset = super().get_queryset()
        
        # Coordinador ve todas las agendas de su zona
        if user.rol == "COORDINADOR_ZONA":
            return queryset.filter(coordinador=user)
        
        # Supervisor ve todas las agendas
        if user.rol in ["SUPERVISOR", "ADMIN", "JEFE_TALLER"]:
            return queryset
        
        # Otros roles ven solo agendas relacionadas
        return queryset.none()
    
    def perform_create(self, serializer):
        """
        Crea una agenda verificando disponibilidad y cupos.
        
        Este método se ejecuta al crear una agenda.
        
        Validaciones:
        1. Solo COORDINADOR_ZONA puede crear
        2. Verifica que no haya solapamiento (mismo vehículo, misma fecha)
        3. Verifica cupos disponibles
        4. Incrementa cupos ocupados
        
        Proceso:
        1. Valida permisos
        2. Verifica solapamiento
        3. Obtiene o crea CupoDiario para la fecha
        4. Verifica cupos disponibles
        5. Incrementa cupos ocupados
        6. Asigna coordinador automáticamente
        """
        user = self.request.user
        
        # Solo coordinadores pueden crear agendas
        if user.rol != "COORDINADOR_ZONA":
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Solo los coordinadores de zona pueden agendar citas al taller. "
                "Si necesita agendar una cita, contacte a un coordinador de zona."
            )
        
        fecha_programada = serializer.validated_data.get("fecha_programada")
        vehiculo = serializer.validated_data.get("vehiculo")
        zona = serializer.validated_data.get("zona", "")
        
        # Verificar que no haya solapamiento
        solapamiento = Agenda.objects.filter(
            vehiculo=vehiculo,
            fecha_programada__date=fecha_programada.date(),
            estado__in=["PROGRAMADA", "CONFIRMADA", "EN_PROCESO"]
        ).exists()
        
        if solapamiento:
            from rest_framework import serializers
            raise serializers.ValidationError(
                "Ya existe una agenda activa para este vehículo en esta fecha"
            )
        
        # Verificar cupos disponibles
        fecha = fecha_programada.date()
        cupo, _ = CupoDiario.objects.get_or_create(
            fecha=fecha,
            defaults={"cupos_totales": 10, "zona": zona}
        )
        
        if cupo.cupos_disponibles <= 0:
            from rest_framework import serializers
            raise serializers.ValidationError(
                "No hay cupos disponibles para esta fecha"
            )
        
        # Incrementar cupos ocupados
        cupo.cupos_ocupados += 1
        cupo.save()
        
        # Guardar agenda (asignar coordinador automáticamente)
        agenda = serializer.save(coordinador=user)
        
        # Registrar auditoría
        ip = get_client_ip(self.request)
        log_audit(
            usuario=user,
            accion="CREAR_AGENDA",
            objeto_tipo="Agenda",
            objeto_id=str(agenda.id),
            payload={
                "vehiculo_id": str(agenda.vehiculo.id) if agenda.vehiculo else None,
                "fecha_programada": agenda.fecha_programada.isoformat() if agenda.fecha_programada else None,
                "tipo_mantenimiento": agenda.tipo_mantenimiento,
                "estado": agenda.estado
            },
            ip_address=ip
        )
    
    @action(detail=True, methods=["post"])
    def reprogramar(self, request, pk=None):
        """
        Reprograma una agenda a una nueva fecha.
        
        Endpoint: POST /api/v1/scheduling/agendas/{id}/reprogramar/
        
        Permisos:
        - Requiere autenticación
        
        Body JSON:
        {
            "fecha_programada": "2024-01-15T10:00:00Z"
        }
        
        Proceso:
        1. Valida nueva fecha
        2. Verifica disponibilidad (similar a perform_create)
        3. Libera cupo de fecha anterior
        4. Reserva cupo de nueva fecha
        5. Cambia estado a REPROGRAMADA
        
        Retorna:
        - 200: Agenda serializada
        - 400: Si falta fecha o no hay disponibilidad
        """
        agenda = self.get_object()
        nueva_fecha = request.data.get("fecha_programada")
        
        if not nueva_fecha:
            return Response(
                {"detail": "Se requiere fecha_programada"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Verificar disponibilidad (lógica similar a perform_create)
        # - Verificar solapamiento
        # - Verificar cupos disponibles
        # - Liberar cupo anterior
        # - Reservar cupo nuevo
        
        agenda.fecha_programada = nueva_fecha
        agenda.estado = "REPROGRAMADA"
        agenda.save()
        
        return Response(AgendaSerializer(agenda).data)
    
    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        """
        Cancela una agenda.
        
        Endpoint: POST /api/v1/scheduling/agendas/{id}/cancelar/
        
        Permisos:
        - Requiere autenticación
        
        Proceso:
        1. Cambia estado a CANCELADA
        2. Libera cupo (decrementa cupos_ocupados)
        
        Retorna:
        - 200: Agenda serializada
        """
        agenda = self.get_object()
        agenda.estado = "CANCELADA"
        agenda.save()
        
        # Liberar cupo
        fecha = agenda.fecha_programada.date()
        try:
            cupo = CupoDiario.objects.get(fecha=fecha)
            if cupo.cupos_ocupados > 0:
                cupo.cupos_ocupados -= 1
                cupo.save()
        except CupoDiario.DoesNotExist:
            pass
        
        return Response(AgendaSerializer(agenda).data)
    
    @action(detail=False, methods=["get"])
    def disponibilidad(self, request):
        """
        Verifica disponibilidad de cupos para una fecha.
        
        Endpoint: GET /api/v1/scheduling/agendas/disponibilidad/?fecha=2024-01-15
        
        Permisos:
        - Requiere autenticación
        
        Parámetros:
        - fecha: Fecha en formato YYYY-MM-DD (query parameter)
        
        Retorna:
        - 200: {
            "fecha": "2024-01-15",
            "cupos_disponibles": 5,
            "cupos_totales": 10,
            "cupos_ocupados": 5
          }
        - 400: Si falta fecha o formato inválido
        """
        fecha_str = request.query_params.get("fecha")
        if not fecha_str:
            return Response(
                {"detail": "Se requiere parámetro 'fecha' (YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from datetime import datetime
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"detail": "Formato de fecha inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener o crear cupo para la fecha
        cupo, _ = CupoDiario.objects.get_or_create(
            fecha=fecha,
            defaults={"cupos_totales": 10}
        )
        
        return Response({
            "fecha": fecha,
            "cupos_disponibles": cupo.cupos_disponibles,
            "cupos_totales": cupo.cupos_totales,
            "cupos_ocupados": cupo.cupos_ocupados
        })


class CupoDiarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para cupos diarios.
    
    Endpoints:
    - GET /api/v1/scheduling/cupos/ → Listar cupos
    - GET /api/v1/scheduling/cupos/{id}/ → Ver cupo específico
    
    Permisos:
    - Requiere autenticación
    
    Filtros:
    - Por fecha, zona
    - Ordenamiento por fecha
    
    Nota:
    - Solo lectura (no permite crear/editar/eliminar)
    - Los cupos se crean automáticamente al crear agendas
    """
    queryset = CupoDiario.objects.all()
    serializer_class = CupoDiarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["fecha", "zona"]
    ordering = ["fecha"]  # Orden por fecha ascendente

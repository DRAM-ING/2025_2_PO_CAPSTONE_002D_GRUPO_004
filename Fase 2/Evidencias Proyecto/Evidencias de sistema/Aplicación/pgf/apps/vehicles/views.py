# apps/vehicles/views.py
"""
Vistas y ViewSets para gestión de vehículos.

Este módulo define todos los endpoints de la API relacionados con:
- Vehículos: CRUD de vehículos de la flota
- Ingresos: Registro de ingreso de vehículos al taller
- Evidencias de ingreso: Fotos/documentos del ingreso
- Historial: Historial completo del vehículo (OT, repuestos, ingresos)

Relaciones:
- Usa: apps/vehicles/models.py (Vehiculo, IngresoVehiculo, EvidenciaIngreso)
- Usa: apps/vehicles/serializers.py (serializers para validación)
- Usa: apps/vehicles/permissions.py (VehiclePermission)
- Usa: apps/workorders/models.py (OrdenTrabajo, Auditoria)
- Usa: apps/scheduling/models.py (Agenda)
- Conectado a: apps/vehicles/urls.py

Endpoints principales:
- /api/v1/vehicles/ → CRUD de vehículos
- /api/v1/vehicles/ingreso/ → Registrar ingreso rápido (Guardia)
- /api/v1/vehicles/{id}/ingreso/evidencias/ → Agregar evidencias al ingreso
- /api/v1/vehicles/{id}/historial/ → Historial completo del vehículo
"""

from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction  # Para transacciones atómicas
from django.utils import timezone  # Para timestamps
from drf_spectacular.utils import extend_schema  # Para documentación OpenAPI

from .models import Vehiculo, IngresoVehiculo, EvidenciaIngreso, HistorialVehiculo, BackupVehiculo, Marca
from apps.workorders.models import BloqueoVehiculo
from apps.workorders.serializers import BloqueoVehiculoSerializer
from .serializers import (
    VehiculoSerializer, VehiculoListSerializer,
    IngresoVehiculoSerializer, EvidenciaIngresoSerializer,
    HistorialVehiculoSerializer, BackupVehiculoSerializer,
    MarcaSerializer
)
from .permissions import VehiclePermission
from apps.workorders.models import Auditoria
from apps.core.serializers import EmptySerializer
from apps.core.audit_logging import log_audit, log_data_change, get_client_ip


class VehiculoViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal para gestión de vehículos.
    
    Proporciona endpoints CRUD completos y acciones personalizadas:
    - GET /api/v1/vehicles/ → Listar vehículos (serializer simplificado)
    - POST /api/v1/vehicles/ → Crear vehículo
    - GET /api/v1/vehicles/{id}/ → Ver vehículo (serializer completo)
    - PUT/PATCH /api/v1/vehicles/{id}/ → Editar vehículo
    - DELETE /api/v1/vehicles/{id}/ → Eliminar vehículo
    
    Acciones personalizadas:
    - POST /api/v1/vehicles/ingreso/ → Registrar ingreso rápido (Guardia)
    - POST /api/v1/vehicles/{id}/ingreso/evidencias/ → Agregar evidencias
    - GET /api/v1/vehicles/{id}/historial/ → Historial completo
    
    Permisos:
    - Usa VehiclePermission (permisos personalizados por rol)
    - Requiere autenticación
    
    Filtros:
    - Por estado (ACTIVO, EN_ESPERA, EN_MANTENIMIENTO, BAJA)
    - Por marca, año
    - Búsqueda por patente, marca, modelo, VIN
    - Ordenamiento por patente, año, marca
    """
    # QuerySet base con optimización (select_related reduce queries N+1)
    queryset = Vehiculo.objects.select_related(
        "marca", "supervisor"
    ).all().order_by("-created_at")
    serializer_class = VehiculoSerializer
    permission_classes = [permissions.IsAuthenticated, VehiclePermission]

    # Configuración de filtros
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Filtros exactos
    filterset_fields = ["estado", "marca__nombre", "anio"]
    
    # Búsqueda por texto (busca en múltiples campos)
    search_fields = ["patente", "marca__nombre", "modelo", "vin"]
    
    # Campos ordenables
    ordering_fields = ["patente", "anio", "marca"]

    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.
        
        - list: Usa VehiculoListSerializer (menos campos, más rápido)
        - create/update/retrieve: Usa VehiculoSerializer (todos los campos)
        
        Esto optimiza el rendimiento en listados grandes.
        """
        if self.action == 'list':
            return VehiculoListSerializer  # Serializer simplificado para listado
        return VehiculoSerializer  # Serializer completo para detalle/edición
    
    def perform_create(self, serializer):
        """Registra auditoría al crear un vehículo."""
        vehiculo = serializer.save()
        ip = get_client_ip(self.request)
        log_audit(
            usuario=self.request.user,
            accion="CREAR_VEHICULO",
            objeto_tipo="Vehiculo",
            objeto_id=str(vehiculo.id),
            payload={
                "patente": vehiculo.patente,
                "marca": vehiculo.marca.nombre if vehiculo.marca else None,
                "modelo": vehiculo.modelo,
                "anio": vehiculo.anio
            },
            ip_address=ip
        )
    
    def perform_update(self, serializer):
        """Registra auditoría al actualizar un vehículo."""
        instance = serializer.instance
        old_data = {
            "patente": instance.patente,
            "estado": instance.estado,
            "marca": instance.marca.nombre if instance.marca else None,
            "modelo": instance.modelo,
            "anio": instance.anio
        }
        vehiculo = serializer.save()
        new_data = {
            "patente": vehiculo.patente,
            "estado": vehiculo.estado,
            "marca": vehiculo.marca.nombre if vehiculo.marca else None,
            "modelo": vehiculo.modelo,
            "anio": vehiculo.anio
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
                accion="ACTUALIZAR_VEHICULO",
                objeto_tipo="Vehiculo",
                objeto_id=str(vehiculo.id),
                cambios=cambios,
                ip_address=ip
            )
        else:
            log_audit(
                usuario=self.request.user,
                accion="ACTUALIZAR_VEHICULO",
                objeto_tipo="Vehiculo",
                objeto_id=str(vehiculo.id),
                payload={"patente": vehiculo.patente},
                ip_address=ip
            )
    
    def perform_destroy(self, instance):
        """Registra auditoría al eliminar un vehículo."""
        patente = instance.patente
        vehiculo_id = str(instance.id)
        instance.delete()
        ip = get_client_ip(self.request)
        log_audit(
            usuario=self.request.user,
            accion="ELIMINAR_VEHICULO",
            objeto_tipo="Vehiculo",
            objeto_id=vehiculo_id,
            payload={"patente": patente},
            nivel='WARNING',
            ip_address=ip
        )

    @extend_schema(
        request=IngresoVehiculoSerializer,
        responses={201: IngresoVehiculoSerializer},
        description="Registra el ingreso rápido de un vehículo al taller (Guardia)"
    )
    @action(detail=False, methods=['post'], url_path='ingreso', permission_classes=[permissions.IsAuthenticated])
    @transaction.atomic
    def ingreso(self, request):
        """
        Registra el ingreso rápido de un vehículo al taller.
        
        Endpoint: POST /api/v1/vehicles/ingreso/
        
        Permisos:
        - Solo GUARDIA puede registrar ingresos
        
        Proceso:
        1. Valida que el usuario sea GUARDIA
        2. Busca o crea el vehículo por patente
        3. Cambia estado del vehículo a EN_ESPERA
        4. Crea registro de IngresoVehiculo
        5. Busca Agenda programada para el día
        6. Genera OT automáticamente (vinculada con Agenda si existe)
        7. Registra auditoría
        
        Body JSON:
        {
            "patente": "ABC123",
            "marca": "Toyota",  // Opcional si el vehículo ya existe
            "modelo": "Hilux",  // Opcional
            "anio": 2020,  // Opcional
            "vin": "123456789",  // Opcional
            "observaciones": "Vehículo con daños en parachoques",
            "kilometraje": 50000,  // Opcional
            "qr_code": "QR123",  // Opcional
            "motivo": "Reparación de parachoques",  // Opcional
            "prioridad": "ALTA",  // Opcional, default: MEDIA
            "zona": "Zona Norte"  // Opcional
        }
        
        Retorna:
        - 201: {
            "id": "...",
            "vehiculo": {...},
            "guardia": {...},
            "fecha_ingreso": "...",
            "ot_generada": {
                "id": "...",
                "estado": "ABIERTA",
                "motivo": "..."
            }
          }
        - 403: Si no es GUARDIA
        - 400: Si falta patente
        
        Características especiales:
        - Si el vehículo no existe, se crea automáticamente
        - Si hay una Agenda programada para hoy, se vincula con la OT
        - La OT se crea automáticamente con estado ABIERTA
        """
        # Verificar permisos: Solo GUARDIA puede registrar ingresos
        if request.user.rol != "GUARDIA":
            return Response(
                {"detail": "Solo el Guardia puede registrar ingresos."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Obtener y normalizar patente (mayúsculas, sin espacios)
        patente = request.data.get("patente", "").strip().upper()
        if not patente:
            return Response(
                {"detail": "La patente es requerida."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar o crear vehículo
        # Si viene marca como ID, buscar la instancia de Marca
        marca_id = request.data.get("marca")
        marca_obj = None
        if marca_id:
            try:
                marca_obj = Marca.objects.get(id=marca_id, activa=True)
            except (Marca.DoesNotExist, ValueError, TypeError):
                # Si no se encuentra o no es un ID válido, ignorar
                pass
        
        # get_or_create retorna (objeto, created) donde created es True si se creó
        vehiculo, created = Vehiculo.objects.get_or_create(
            patente=patente,
            defaults={
                "marca": marca_obj,
                "modelo": request.data.get("modelo", ""),
                "anio": request.data.get("anio"),
                "vin": request.data.get("vin", ""),
            }
        )
        
        # Si el vehículo ya existía pero se proporcionó marca, actualizarla
        if not created and marca_obj and not vehiculo.marca:
            vehiculo.marca = marca_obj
            vehiculo.save(update_fields=["marca"])

        # Cambiar estado a EN_ESPERA (vehículo ingresado, esperando atención)
        vehiculo.estado = "EN_ESPERA"
        vehiculo.save(update_fields=["estado"])

        # Crear registro de ingreso
        ingreso = IngresoVehiculo.objects.create(
            vehiculo=vehiculo,
            guardia=request.user,
            observaciones=request.data.get("observaciones", ""),
            kilometraje=request.data.get("kilometraje"),
            qr_code=request.data.get("qr_code", ""),
        )

        # Generar OT automáticamente
        from apps.workorders.models import OrdenTrabajo
        from apps.scheduling.models import Agenda
        
        # Buscar si hay una agenda programada para este vehículo hoy
        agenda = Agenda.objects.filter(
            vehiculo=vehiculo,
            estado__in=["PROGRAMADA", "CONFIRMADA"],  # Estados válidos
            fecha_programada__date=timezone.now().date()  # Solo del día actual
        ).first()
        
        # Obtener motivo del ingreso
        motivo = request.data.get("motivo", "")
        
        # Si hay agenda, usar su información
        if agenda:
            # Combinar motivo de agenda con motivo del ingreso
            motivo = f"{agenda.motivo}. {motivo}".strip()
            tipo_mantenimiento = agenda.tipo_mantenimiento
            # Cambiar estado de agenda a EN_PROCESO
            agenda.estado = "EN_PROCESO"
            agenda.ot_asociada = None  # Se asignará después de crear la OT
            agenda.save()
        else:
            # Si no hay agenda, determinar tipo según motivo
            # Si hay motivo → MANTENCION, si no → CORRECTIVO
            tipo_mantenimiento = "CORRECTIVO" if not motivo else "MANTENCION"
        
        # Buscar o crear chofer si se proporciona información
        chofer = None
        chofer_rut = request.data.get("chofer_rut", "").strip()
        chofer_nombre = request.data.get("chofer_nombre", "").strip()
        
        if chofer_rut or chofer_nombre:
            from apps.drivers.models import Chofer
            from apps.core.validators import validar_rut_chileno
            
            # Si se proporciona RUT, validarlo y buscar/crear chofer
            if chofer_rut:
                es_valido, rut_formateado = validar_rut_chileno(chofer_rut)
                if es_valido:
                    # Limpiar RUT (sin puntos ni guión)
                    rut_limpio = rut_formateado.replace("-", "").replace(".", "")
                    chofer, created = Chofer.objects.get_or_create(
                        rut=rut_limpio,
                        defaults={
                            "nombre_completo": chofer_nombre or "Chofer sin nombre",
                            "activo": True,
                        }
                    )
                    # Si el chofer ya existía, actualizar nombre si se proporcionó
                    if not created and chofer_nombre:
                        chofer.nombre_completo = chofer_nombre
                        chofer.save(update_fields=["nombre_completo"])
                # Si el RUT no es válido, simplemente no crear chofer (no es obligatorio)
                # El usuario puede registrar el ingreso sin chofer
        
        # Determinar responsable: usar supervisor del vehículo si existe, sino el usuario que crea
        responsable = vehiculo.supervisor if vehiculo.supervisor else request.user
        
        # Crear OT automáticamente
        ot = OrdenTrabajo.objects.create(
            vehiculo=vehiculo,
            estado="ABIERTA",  # Estado inicial
            tipo=tipo_mantenimiento,
            motivo=motivo or "Ingreso al taller",
            prioridad=request.data.get("prioridad", "MEDIA"),
            causa_ingreso=request.data.get("observaciones", ""),
            chofer=chofer,  # Asociar chofer si se proporcionó
            responsable=responsable,  # Asignar responsable automáticamente
        )
        
        # Registrar en historial y calcular SLA
        try:
            from apps.vehicles.utils import registrar_ot_creada, calcular_sla_ot
            registrar_ot_creada(ot, request.user)
            calcular_sla_ot(ot)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al registrar historial para OT {ot.id}: {e}")
        
        # Vincular OT con agenda si existe
        if agenda:
            agenda.ot_asociada = ot
            agenda.save()
        
        # Registrar auditoría mejorada
        ip = get_client_ip(request)
        log_audit(
            usuario=request.user,
            accion="REGISTRAR_INGRESO_VEHICULO",
            objeto_tipo="IngresoVehiculo",
            objeto_id=str(ingreso.id),
            payload={
                "vehiculo_id": str(vehiculo.id),
                "patente": patente,
                "vehiculo_creado": created,  # True si se creó el vehículo
                "ot_generada": str(ot.id)
            },
            ip_address=ip
        )

        # TODO: Notificar al supervisor (implementar con Celery o signals)
        # from apps.workorders.tasks import notificar_ingreso_vehiculo
        # notificar_ingreso_vehiculo.delay(str(ingreso.id))

        # Retornar respuesta con información del ingreso y OT generada
        serializer = IngresoVehiculoSerializer(ingreso)
        return Response({
            **serializer.data,
            "ot_generada": {
                "id": str(ot.id),
                "estado": ot.estado,
                "motivo": ot.motivo
            }
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        responses={200: None},
        description="Genera un PDF del ticket de ingreso de un vehículo"
    )
    @action(detail=False, methods=['get'], url_path='ingreso/(?P<ingreso_id>[^/.]+)/ticket', permission_classes=[permissions.IsAuthenticated])
    def generar_ticket_ingreso(self, request, ingreso_id=None):
        """
        Genera un PDF del ticket de ingreso de un vehículo.
        
        Endpoint: GET /api/v1/vehicles/ingreso/{ingreso_id}/ticket/
        
        Permisos:
        - GUARDIA, ADMIN, SUPERVISOR, JEFE_TALLER
        
        Retorna:
        - PDF del ticket de ingreso
        """
        from apps.reports.pdf_generator import generar_ticket_ingreso_pdf
        from django.http import HttpResponse
        
        # Verificar permisos
        if request.user.rol not in ["GUARDIA", "ADMIN", "SUPERVISOR", "JEFE_TALLER"]:
            return Response(
                {"detail": "No tiene permiso para generar tickets de ingreso."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Generar PDF (la función busca el ingreso internamente)
            pdf_buffer = generar_ticket_ingreso_pdf(str(ingreso_id))
            
            # Crear respuesta HTTP con el PDF
            response = HttpResponse(
                pdf_buffer.getvalue(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'inline; filename="ticket_ingreso_{str(ingreso_id)[:8]}.pdf"'
            return response
        except (IngresoVehiculo.DoesNotExist, ValueError) as e:
            # ValueError se lanza cuando generar_ticket_ingreso_pdf no encuentra el ingreso
            if "no encontrado" in str(e).lower() or isinstance(e, IngresoVehiculo.DoesNotExist):
                return Response(
                    {"detail": "Ingreso no encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )
            raise
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al generar ticket de ingreso: {e}", exc_info=True)
            return Response(
                {"detail": f"Error al generar el ticket de ingreso: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        request=EmptySerializer,
        responses={200: None},
        description="Registra la salida de un vehículo del taller"
    )
    @action(detail=False, methods=['post'], url_path='salida', permission_classes=[permissions.IsAuthenticated])
    @transaction.atomic
    def registrar_salida(self, request):
        """
        Registra la salida de un vehículo del taller.
        
        Endpoint: POST /api/v1/vehicles/salida/
        
        Permisos:
        - GUARDIA, ADMIN, JEFE_TALLER pueden registrar salidas
        
        Body JSON:
        {
            "ingreso_id": "uuid-del-ingreso",
            "observaciones_salida": "Observaciones opcionales",
            "kilometraje_salida": 50000  // Opcional
        }
        """
        # Verificar permisos: GUARDIA, ADMIN, JEFE_TALLER pueden registrar salidas
        if request.user.rol not in ["GUARDIA", "ADMIN", "JEFE_TALLER"]:
            return Response(
                {"detail": "No tiene permiso para registrar salidas. Solo Guardia, Admin o Jefe de Taller pueden hacerlo."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        ingreso_id = request.data.get("ingreso_id")
        if not ingreso_id:
            return Response(
                {"detail": "El ID del ingreso es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convertir a string si es UUID
        if hasattr(ingreso_id, '__str__'):
            ingreso_id = str(ingreso_id)
        
        try:
            ingreso = IngresoVehiculo.objects.select_related('vehiculo').get(id=ingreso_id)
        except IngresoVehiculo.DoesNotExist:
            return Response(
                {"detail": "Ingreso no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validar que el vehículo no haya salido ya
        if ingreso.salio:
            return Response(
                {"detail": "Este vehículo ya salió del taller."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que todas las OTs estén cerradas o anuladas
        from apps.workorders.models import OrdenTrabajo
        ots_activas = OrdenTrabajo.objects.filter(
            vehiculo=ingreso.vehiculo
        ).exclude(
            estado__in=["CERRADA", "ANULADA"]
        ).exists()
        
        if ots_activas:
            # Obtener detalles de las OTs activas para el mensaje
            ots_activas_list = OrdenTrabajo.objects.filter(
                vehiculo=ingreso.vehiculo
            ).exclude(
                estado__in=["CERRADA", "ANULADA"]
            ).values_list('id', 'estado')
            
            estados_activos = [f"OT {str(ot_id)[:8]} ({estado})" for ot_id, estado in ots_activas_list]
            return Response(
                {
                    "detail": f"El vehículo tiene OTs activas. Debe cerrarlas antes de registrar la salida.",
                    "ots_activas": list(ots_activas_list),
                    "detalle": f"OTs activas: {', '.join(estados_activos)}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Registrar salida
        ingreso.fecha_salida = timezone.now()
        ingreso.guardia_salida = request.user
        ingreso.observaciones_salida = request.data.get("observaciones_salida", "") or ""
        
        # Manejar kilometraje_salida: puede ser None, string vacío, o número
        kilometraje_salida = request.data.get("kilometraje_salida")
        if kilometraje_salida is not None and kilometraje_salida != "":
            try:
                ingreso.kilometraje_salida = int(kilometraje_salida)
            except (ValueError, TypeError):
                ingreso.kilometraje_salida = None
        else:
            ingreso.kilometraje_salida = None
        
        ingreso.salio = True
        ingreso.save()
        
        # Cambiar estado del vehículo
        ingreso.vehiculo.estado = "ACTIVO"
        ingreso.vehiculo.save(update_fields=["estado"])
        
        # Registrar auditoría mejorada
        ip = get_client_ip(request)
        log_audit(
            usuario=request.user,
            accion="REGISTRAR_SALIDA_VEHICULO",
            objeto_tipo="IngresoVehiculo",
            objeto_id=str(ingreso.id),
            payload={
                "vehiculo_id": str(ingreso.vehiculo.id),
                "patente": ingreso.vehiculo.patente,
                "fecha_salida": ingreso.fecha_salida.isoformat()
            },
            ip_address=ip
        )
        
        # Registrar en historial
        try:
            from apps.vehicles.utils import registrar_evento_historial
            registrar_evento_historial(
                vehiculo=ingreso.vehiculo,
                tipo_evento="SALIDA_TALLER",
                fecha_salida=ingreso.fecha_salida,
                fecha_ingreso=ingreso.fecha_ingreso,
                descripcion=f"Salida registrada por {request.user.get_full_name()}"
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al registrar historial de salida {ingreso.id}: {e}")
        
        serializer = IngresoVehiculoSerializer(ingreso)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Obtiene la lista de ingresos del día",
        responses={200: None}
    )
    @action(detail=False, methods=['get'], url_path='ingresos-hoy', permission_classes=[permissions.IsAuthenticated])
    def ingresos_hoy(self, request):
        """
        Obtiene la lista de ingresos del día actual.
        
        Endpoint: GET /api/v1/vehicles/ingresos-hoy/
        
        Permisos:
        - GUARDIA, ADMIN, SUPERVISOR
        
        Query params:
        - patente: Filtrar por patente (opcional)
        
        Retorna:
        - 200: Lista de ingresos del día con información completa
        """
        # Verificar permisos
        if request.user.rol not in ["GUARDIA", "ADMIN", "SUPERVISOR"]:
            return Response(
                {"detail": "No tiene permisos para ver ingresos."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Obtener fecha de hoy
        hoy = timezone.now().date()
        
        # Filtrar ingresos del día (mostrar todos, tanto los que han salido como los que no)
        # Mostrar todos los ingresos del día, independientemente de si tienen OTs activas o si han salido
        ingresos = IngresoVehiculo.objects.filter(
            fecha_ingreso__date=hoy
        ).select_related(
            "vehiculo", 
            "vehiculo__marca",
            "vehiculo__supervisor",
            "guardia", 
            "guardia_salida"
        ).order_by("-fecha_ingreso")
        
        # Filtrar por patente si se proporciona
        patente = request.query_params.get("patente", "").strip().upper()
        if patente:
            ingresos = ingresos.filter(vehiculo__patente__icontains=patente)
        
        # Serializar
        serializer = IngresoVehiculoSerializer(ingresos, many=True)
        
        return Response({
            "fecha": hoy.isoformat(),
            "total": ingresos.count(),
            "ingresos": serializer.data
        })

    @extend_schema(
        description="Obtiene vehículos pendientes de salida (con todas las OTs cerradas)",
        responses={200: None}
    )
    @action(detail=False, methods=['get'], url_path='pendientes-salida', permission_classes=[permissions.IsAuthenticated])
    def pendientes_salida(self, request):
        """
        Obtiene la lista de vehículos pendientes de salida.
        
        Un vehículo está pendiente de salida si:
        - Tiene un ingreso registrado que no ha salido (salio=False)
        - Todas sus OTs están cerradas o anuladas
        
        Endpoint: GET /api/v1/vehicles/pendientes-salida/
        
        Permisos:
        - GUARDIA, ADMIN, JEFE_TALLER
        
        Query params:
        - patente: Filtrar por patente (opcional)
        
        Retorna:
        - 200: Lista de ingresos pendientes de salida con información completa
        """
        # Verificar permisos
        if request.user.rol not in ["GUARDIA", "ADMIN", "JEFE_TALLER"]:
            return Response(
                {"detail": "No tiene permisos para ver vehículos pendientes de salida."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from apps.workorders.models import OrdenTrabajo
        from django.db.models import Q, Exists, OuterRef, Count, Prefetch
        
        # Obtener todos los ingresos que no han salido
        ingresos_pendientes = IngresoVehiculo.objects.filter(
            salio=False
        ).select_related("vehiculo", "vehiculo__marca", "guardia", "guardia_salida").order_by("-fecha_ingreso")
        
        # Filtrar por patente si se proporciona
        patente = request.query_params.get("patente", "").strip().upper()
        if patente:
            ingresos_pendientes = ingresos_pendientes.filter(vehiculo__patente__icontains=patente)
        
        # Filtrar solo los que tienen todas las OTs cerradas o anuladas
        # Usar una subconsulta con Exists para verificar si hay OTs activas
        # El related_name en OrdenTrabajo es "ordenes"
        ots_activas_subquery = OrdenTrabajo.objects.filter(
            vehiculo=OuterRef('vehiculo')
        ).exclude(
            estado__in=["CERRADA", "ANULADA"]
        )
        
        # Anotar cada ingreso con si tiene OTs activas
        ingresos_pendientes = ingresos_pendientes.annotate(
            tiene_ots_activas=Exists(ots_activas_subquery)
        )
        
        # Filtrar solo los que NO tienen OTs activas (todas están cerradas o anuladas)
        ingresos_validos = ingresos_pendientes.filter(tiene_ots_activas=False)
        
        # Log para debugging
        import logging
        logger = logging.getLogger(__name__)
        total_pendientes = ingresos_pendientes.count()
        total_validos = ingresos_validos.count()
        logger.info(f"Total ingresos pendientes: {total_pendientes}, Con OTs cerradas: {total_validos}")
        
        # Serializar
        serializer = IngresoVehiculoSerializer(ingresos_validos, many=True)
        
        return Response({
            "total": ingresos_validos.count(),
            "ingresos": serializer.data
        })

    @extend_schema(
        description="Obtiene el historial completo de ingresos con filtros de fecha",
        responses={200: None}
    )
    @action(detail=False, methods=['get'], url_path='ingresos-historial', permission_classes=[permissions.IsAuthenticated])
    def ingresos_historial(self, request):
        """
        Obtiene el historial completo de ingresos con filtros de fecha.
        
        Endpoint: GET /api/v1/vehicles/ingresos-historial/
        
        Permisos:
        - GUARDIA, ADMIN, SUPERVISOR, JEFE_TALLER
        
        Query params:
        - patente: Filtrar por patente (opcional)
        - fecha_desde: Fecha de inicio (YYYY-MM-DD) (opcional, por defecto: últimos 30 días)
        - fecha_hasta: Fecha de fin (YYYY-MM-DD) (opcional, por defecto: hoy)
        - salio: Filtrar por estado de salida (true/false) (opcional)
        - page: Número de página (opcional, por defecto: 1)
        - page_size: Tamaño de página (opcional, por defecto: 50)
        
        Retorna:
        - 200: Lista paginada de ingresos con información completa
        """
        # Verificar permisos
        if request.user.rol not in ["GUARDIA", "ADMIN", "SUPERVISOR", "JEFE_TALLER"]:
            return Response(
                {"detail": "No tiene permisos para ver historial de ingresos."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Obtener parámetros de filtro
        patente = request.query_params.get("patente", "").strip().upper()
        fecha_desde = request.query_params.get("fecha_desde", "")
        fecha_hasta = request.query_params.get("fecha_hasta", "")
        salio_param = request.query_params.get("salio", "")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
        
        # Construir queryset base con optimización de consultas
        # select_related para relaciones ForeignKey (una consulta por relación)
        ingresos = IngresoVehiculo.objects.select_related(
            "vehiculo", 
            "vehiculo__marca",
            "vehiculo__supervisor",
            "guardia", 
            "guardia_salida"
        ).order_by("-fecha_ingreso")
        
        # Filtrar por patente si se proporciona
        if patente:
            ingresos = ingresos.filter(vehiculo__patente__icontains=patente)
        
        # Filtrar por fecha desde
        if fecha_desde:
            try:
                from datetime import datetime
                fecha_desde_obj = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
                ingresos = ingresos.filter(fecha_ingreso__date__gte=fecha_desde_obj)
            except ValueError:
                pass  # Ignorar fecha inválida
        
        # Filtrar por fecha hasta
        if fecha_hasta:
            try:
                from datetime import datetime
                fecha_hasta_obj = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
                ingresos = ingresos.filter(fecha_ingreso__date__lte=fecha_hasta_obj)
            except ValueError:
                pass  # Ignorar fecha inválida
        
        # Si no se proporcionaron fechas, usar últimos 30 días por defecto
        if not fecha_desde and not fecha_hasta:
            from datetime import timedelta
            fecha_desde_default = timezone.now().date() - timedelta(days=30)
            ingresos = ingresos.filter(fecha_ingreso__date__gte=fecha_desde_default)
        
        # Filtrar por estado de salida
        if salio_param.lower() == "true":
            ingresos = ingresos.filter(salio=True)
        elif salio_param.lower() == "false":
            ingresos = ingresos.filter(salio=False)
        
        # Paginación
        total = ingresos.count()
        start = (page - 1) * page_size
        end = start + page_size
        ingresos_paginados = ingresos[start:end]
        
        # Serializar
        serializer = IngresoVehiculoSerializer(ingresos_paginados, many=True)
        
        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "results": serializer.data
        })

    @extend_schema(
        request=EvidenciaIngresoSerializer,
        responses={201: EvidenciaIngresoSerializer},
        description="Agrega evidencia fotográfica al ingreso de un vehículo"
    )
    @action(detail=True, methods=['post'], url_path='ingreso/evidencias', permission_classes=[permissions.IsAuthenticated])
    @extend_schema(
        request={"type": "object", "properties": {
            "file": {"type": "string", "format": "binary"},
            "tipo": {"type": "string"},
            "descripcion": {"type": "string"}
        }},
        responses={201: EvidenciaIngresoSerializer}
    )
    def agregar_evidencia_ingreso(self, request, pk=None):
        """
        Agrega evidencia fotográfica al último ingreso de un vehículo.
        
        Endpoint: POST /api/v1/vehicles/{id}/ingreso/evidencias/
        
        Permisos:
        - GUARDIA, SUPERVISOR, ADMIN
        
        Proceso:
        1. Valida permisos
        2. Obtiene el vehículo
        3. Busca el último ingreso del vehículo
        4. Sube archivo a S3 (si se proporciona)
        5. Crea registro de EvidenciaIngreso
        
        Body (multipart/form-data):
        - file: Archivo a subir (requerido si no se proporciona url)
        - url: URL del archivo en S3 (opcional, si el archivo ya está subido)
        - tipo: Tipo de evidencia (opcional, default: FOTO_INGRESO)
        - descripcion: Descripción (opcional)
        
        Retorna:
        - 201: EvidenciaIngreso serializada
        - 403: Si no tiene permisos
        - 404: Si no hay registro de ingreso
        - 400: Si falta archivo o URL
        """
        import os
        import uuid
        import boto3
        
        # Verificar permisos
        if request.user.rol not in ("GUARDIA", "SUPERVISOR", "ADMIN"):
            return Response(
                {"detail": "No autorizado para agregar evidencias de ingreso."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Obtener vehículo
        vehiculo = self.get_object()
        
        # Buscar el último ingreso del vehículo (más reciente)
        ultimo_ingreso = IngresoVehiculo.objects.filter(vehiculo=vehiculo).order_by('-fecha_ingreso').first()
        
        if not ultimo_ingreso:
            return Response(
                {"detail": "No hay registro de ingreso para este vehículo."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener URL o subir archivo
        file_url = request.data.get("url")
        file = request.FILES.get("file")
        
        if not file_url and not file:
            return Response(
                {"detail": "Se debe proporcionar un archivo o una URL."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si se proporciona un archivo, subirlo a S3
        if file:
            # Validar archivo
            from apps.workorders.middleware import validate_file_upload
            validation = validate_file_upload(file, max_size_mb=3072)
            
            if not validation['valid']:
                return Response(
                    {"detail": "; ".join(validation['errors'])},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Configurar S3
            bucket = os.getenv("AWS_STORAGE_BUCKET_NAME", "pgf-evidencias-dev")
            s3_endpoint_internal = os.getenv("AWS_S3_ENDPOINT_URL", "http://localstack:4566")
            s3_endpoint_public = os.getenv("AWS_PUBLIC_URL_PREFIX")
            
            if not s3_endpoint_public:
                cloudflare_url = os.getenv("CLOUDFLARE_TUNNEL_URL", "").rstrip("/")
                if cloudflare_url:
                    s3_endpoint_public = f"{cloudflare_url}/localstack"
                else:
                    s3_endpoint_public = "http://localhost:4566"
            
            s3 = boto3.client(
                "s3",
                endpoint_url=s3_endpoint_internal,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
                region_name=os.getenv("AWS_S3_REGION_NAME", "us-east-1"),
            )
            
            # Generar key único para el archivo
            key = f"evidencias/ingreso_{ultimo_ingreso.id}/{uuid.uuid4()}_{file.name}"
            
            try:
                # Asegurar que el bucket existe
                try:
                    s3.head_bucket(Bucket=bucket)
                except:
                    s3.create_bucket(Bucket=bucket)
                
                # Subir archivo a S3
                s3.upload_fileobj(
                    file,
                    bucket,
                    key,
                    ExtraArgs={'ContentType': file.content_type or 'application/octet-stream'}
                )
                
                # Generar URL pública
                file_url = f"{s3_endpoint_public}/{bucket}/{key}"
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al subir archivo a S3: {e}")
                return Response(
                    {"detail": f"Error al subir archivo: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Crear evidencia de ingreso
        evidencia = EvidenciaIngreso.objects.create(
            ingreso=ultimo_ingreso,
            url=file_url,
            tipo=request.data.get("tipo", EvidenciaIngreso.TipoEvidencia.FOTO_INGRESO),
            descripcion=request.data.get("descripcion", ""),
        )

        # Vincular evidencia a la OT asociada al ingreso
        # Buscar la OT más reciente del vehículo que se creó en el mismo momento del ingreso
        # o la OT más reciente del vehículo si no hay una coincidencia exacta
        from apps.workorders.models import OrdenTrabajo, Evidencia as EvidenciaOT
        
        # Buscar OT asociada al ingreso (la OT más reciente del vehículo creada cerca del momento del ingreso)
        # Usar una ventana de tiempo de 10 minutos para considerar OTs creadas al mismo tiempo
        # (la OT se crea automáticamente al registrar el ingreso, así que debería estar muy cerca en el tiempo)
        from datetime import timedelta
        ventana_tiempo = timedelta(minutes=10)
        tiempo_ingreso = ultimo_ingreso.fecha_ingreso
        
        # Primero buscar OTs creadas en la ventana de tiempo alrededor del ingreso
        ot_asociada = OrdenTrabajo.objects.filter(
            vehiculo=vehiculo,
            apertura__gte=tiempo_ingreso - ventana_tiempo,
            apertura__lte=tiempo_ingreso + ventana_tiempo
        ).order_by('-apertura').first()
        
        # Si no se encuentra una OT en la ventana de tiempo, buscar la OT más reciente del vehículo
        # que aún no esté cerrada o anulada (para asegurar que es la OT activa del ingreso)
        if not ot_asociada:
            ot_asociada = OrdenTrabajo.objects.filter(
                vehiculo=vehiculo,
                estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA", "EN_QA", "RETRABAJO"]
            ).order_by('-apertura').first()
        
        # Si aún no se encuentra, buscar cualquier OT del vehículo (última opción)
        if not ot_asociada:
            ot_asociada = OrdenTrabajo.objects.filter(
                vehiculo=vehiculo
            ).order_by('-apertura').first()
        
        # Si se encuentra una OT, crear evidencia en la OT
        if ot_asociada:
            # Mapear tipo de evidencia de ingreso a tipo de evidencia de OT
            tipo_evidencia_ot = "FOTO"  # Por defecto FOTO
            tipo_ingreso = request.data.get("tipo", EvidenciaIngreso.TipoEvidencia.FOTO_INGRESO)
            
            # Mapear tipos
            tipo_mapping = {
                EvidenciaIngreso.TipoEvidencia.FOTO_INGRESO: "FOTO",
                EvidenciaIngreso.TipoEvidencia.FOTO_DANOS: "FOTO",
                EvidenciaIngreso.TipoEvidencia.FOTO_DOCUMENTOS: "PDF",
                EvidenciaIngreso.TipoEvidencia.OTRO: "OTRO",
            }
            tipo_evidencia_ot = tipo_mapping.get(tipo_ingreso, "FOTO")
            
            # Crear evidencia en la OT
            try:
                evidencia_ot = EvidenciaOT.objects.create(
                    ot=ot_asociada,
                    url=file_url,
                    tipo=tipo_evidencia_ot,
                    descripcion=request.data.get("descripcion", "") or f"Evidencia de ingreso: {evidencia.descripcion or 'Sin descripción'}",
                    subido_por=request.user,
                )
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Evidencia de ingreso {evidencia.id} vinculada a OT {ot_asociada.id} como evidencia {evidencia_ot.id}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al vincular evidencia de ingreso a OT: {e}", exc_info=True)
                # No fallar si no se puede vincular, solo loguear el error

        # Retornar evidencia serializada
        serializer = EvidenciaIngresoSerializer(evidencia)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        description="Obtiene la lista de marcas disponibles",
        responses={200: MarcaSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='marcas', permission_classes=[permissions.IsAuthenticated])
    def marcas(self, request):
        """
        Retorna la lista de marcas activas disponibles.
        
        Endpoint: GET /api/v1/vehicles/marcas/
        
        Permisos:
        - Requiere autenticación
        
        Retorna:
        - 200: Lista de marcas activas [{id, nombre, activa}, ...]
        """
        marcas = Marca.objects.filter(activa=True).order_by('nombre')
        serializer = MarcaSerializer(marcas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Obtiene el historial completo del vehículo (OT, repuestos, ingresos)",
        responses={200: None}
    )
    @action(detail=True, methods=['get'], url_path='historial')
    def historial(self, request, pk=None):
        """
        Retorna el historial completo del vehículo.
        
        Endpoint: GET /api/v1/vehicles/{id}/historial/
        
        Permisos:
        - Requiere autenticación
        
        Retorna:
        - 200: {
            "vehiculo": {...},
            "ordenes_trabajo": [...],
            "historial_repuestos": [...],
            "ingresos": [...],
            "total_ordenes": 10,
            "total_repuestos": 5,
            "total_ingresos": 8
          }
        
        Incluye:
        - Información del vehículo
        - Todas las OT asociadas (con items)
        - Historial de repuestos usados (si existe módulo de inventario)
        - Todos los ingresos al taller (con evidencias)
        
        Optimizaciones:
        - Usa select_related para reducir queries
        - Usa prefetch_related para items y evidencias
        """
        # Obtener vehículo
        vehiculo = self.get_object()
        
        # ==================== HISTORIAL DE OT ====================
        from apps.workorders.models import OrdenTrabajo, ItemOT
        
        # Obtener todas las OT del vehículo con optimizaciones
        ordenes = OrdenTrabajo.objects.filter(vehiculo=vehiculo).select_related(
            'responsable'  # Reducir queries para responsable
        ).prefetch_related('items').order_by('-apertura')  # Más recientes primero
        
        # Serializar OT con sus items
        ordenes_data = []
        for ot in ordenes:
            ordenes_data.append({
                "id": str(ot.id),
                "estado": ot.estado,
                "tipo": ot.tipo,
                "prioridad": ot.prioridad,
                "motivo": ot.motivo,
                "responsable": f"{ot.responsable.first_name} {ot.responsable.last_name}" if ot.responsable else None,
                "apertura": ot.apertura.isoformat(),
                "cierre": ot.cierre.isoformat() if ot.cierre else None,
                "items": [{
                    "tipo": item.tipo,
                    "descripcion": item.descripcion,
                    "cantidad": item.cantidad,
                    "costo_unitario": str(item.costo_unitario),
                } for item in ot.items.all()],
            })
        
        # ==================== HISTORIAL DE REPUESTOS ====================
        historial_repuestos = []
        try:
            # Intentar obtener historial de repuestos (si existe módulo de inventario)
            from apps.inventory.models import HistorialRepuestoVehiculo
            repuestos = HistorialRepuestoVehiculo.objects.filter(
                vehiculo=vehiculo
            ).select_related('repuesto', 'ot').order_by('-fecha_uso')
            
            historial_repuestos = [{
                "repuesto_codigo": h.repuesto.codigo,
                "repuesto_nombre": h.repuesto.nombre,
                "cantidad": h.cantidad,
                "fecha_uso": h.fecha_uso.isoformat(),
                "ot_id": str(h.ot.id) if h.ot else None,
                "costo_unitario": str(h.costo_unitario) if h.costo_unitario else None,
            } for h in repuestos]
        except ImportError:
            # Si el módulo de inventario no existe, continuar sin errores
            pass
        
        # ==================== HISTORIAL DE INGRESOS ====================
        # Obtener todos los ingresos con optimizaciones
        ingresos = IngresoVehiculo.objects.filter(
            vehiculo=vehiculo
        ).select_related('guardia').prefetch_related('evidencias').order_by('-fecha_ingreso')
        
        # Obtener OTs asociadas a los ingresos (buscar por fecha de ingreso y vehículo)
        from django.db.models import Q
        from datetime import timedelta
        
        # Serializar ingresos con evidencias y OT asociada
        ingresos_data = []
        for ing in ingresos:
            # Buscar OT creada en el mismo día del ingreso para este vehículo
            ot_asociada = None
            try:
                # Buscar OT que se creó el mismo día del ingreso
                fecha_ingreso = ing.fecha_ingreso.date()
                ot_asociada = OrdenTrabajo.objects.filter(
                    vehiculo=vehiculo,
                    apertura__date=fecha_ingreso
                ).order_by('-apertura').first()
            except Exception:
                pass
            
            ingresos_data.append({
                "id": str(ing.id),
                "fecha_ingreso": ing.fecha_ingreso.isoformat(),
                "guardia": f"{ing.guardia.first_name} {ing.guardia.last_name}",
                "kilometraje": ing.kilometraje,
                "observaciones": ing.observaciones,
                "ot_id": str(ot_asociada.id) if ot_asociada else None,
                "ot_estado": ot_asociada.estado if ot_asociada else None,
                "evidencias": [{
                    "tipo": ev.tipo,
                    "url": ev.url,
                    "descripcion": ev.descripcion,
                } for ev in ing.evidencias.all()],
            })
        
        # ==================== HISTORIAL DE EVENTOS (HistorialVehiculo) ====================
        # Obtener todos los eventos del historial del vehículo
        eventos_historial = HistorialVehiculo.objects.filter(
            vehiculo=vehiculo
        ).select_related('ot', 'supervisor', 'backup_utilizado__vehiculo_backup').order_by('-creado_en')
        
        # Serializar eventos de historial
        eventos_data = []
        for evento in eventos_historial:
            eventos_data.append({
                "id": str(evento.id),
                "tipo_evento": evento.tipo_evento,
                "descripcion": evento.descripcion,
                "fecha_ingreso": evento.fecha_ingreso.isoformat() if evento.fecha_ingreso else None,
                "fecha_salida": evento.fecha_salida.isoformat() if evento.fecha_salida else None,
                "tiempo_permanencia": str(evento.tiempo_permanencia) if evento.tiempo_permanencia else None,
                "falla": evento.falla,
                "estado_antes": evento.estado_antes,
                "estado_despues": evento.estado_despues,
                "supervisor": f"{evento.supervisor.first_name} {evento.supervisor.last_name}" if evento.supervisor else None,
                "ot": {
                    "id": str(evento.ot.id),
                    "estado": evento.ot.estado,
                    "motivo": evento.ot.motivo,
                } if evento.ot else None,
                "backup_patente": evento.backup_utilizado.vehiculo_backup.patente if evento.backup_utilizado and evento.backup_utilizado.vehiculo_backup else None,
                "creado_en": evento.creado_en.isoformat() if evento.creado_en else None,
            })
        
        # Retornar historial completo
        return Response({
            "vehiculo": {
                "id": str(vehiculo.id),
                "patente": vehiculo.patente,
                "marca": vehiculo.marca.nombre if vehiculo.marca else None,
                "marca_id": vehiculo.marca.id if vehiculo.marca else None,
                "modelo": vehiculo.modelo,
                "anio": vehiculo.anio,
                "estado": vehiculo.estado,
            },
            "ordenes_trabajo": ordenes_data,
            "historial_repuestos": historial_repuestos,
            "ingresos": ingresos_data,
            "eventos": eventos_data,  # Agregar eventos del historial
            "total_ordenes": len(ordenes_data),
            "total_repuestos": len(historial_repuestos),
            "total_ingresos": len(ingresos_data),
            "total_eventos": len(eventos_data),
        })


class HistorialVehiculoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar historial de vehículos.
    
    Solo lectura (ReadOnly) porque el historial se crea automáticamente
    cuando ocurren eventos (OT creada, OT cerrada, backup asignado, etc.)
    
    Endpoints:
    - GET /api/v1/vehicles/historial/ → Listar todos los eventos de historial
    - GET /api/v1/vehicles/historial/{id}/ → Ver evento específico
    - GET /api/v1/vehicles/historial/?vehiculo={id} → Filtrar por vehículo
    - GET /api/v1/vehicles/historial/?tipo_evento=OT_CREADA → Filtrar por tipo
    """
    queryset = HistorialVehiculo.objects.all().select_related(
        'vehiculo', 'ot', 'supervisor', 'backup_utilizado'
    ).order_by('-creado_en')
    serializer_class = HistorialVehiculoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vehiculo', 'tipo_evento']
    search_fields = ['descripcion', 'falla']
    ordering_fields = ['creado_en', 'fecha_ingreso', 'fecha_salida']


class BackupVehiculoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar backups de vehículos.
    
    Endpoints:
    - GET /api/v1/vehicles/backups/ → Listar todos los backups
    - POST /api/v1/vehicles/backups/ → Crear nuevo backup
    - GET /api/v1/vehicles/backups/{id}/ → Ver backup específico
    - PUT/PATCH /api/v1/vehicles/backups/{id}/ → Actualizar backup
    - DELETE /api/v1/vehicles/backups/{id}/ → Eliminar backup
    
    Acciones personalizadas:
    - POST /api/v1/vehicles/backups/{id}/devolver/ → Devolver backup
    """
    queryset = BackupVehiculo.objects.all().select_related(
        'vehiculo_principal', 'vehiculo_backup', 'ot', 'supervisor'
    ).order_by('-fecha_inicio')
    serializer_class = BackupVehiculoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vehiculo_principal', 'vehiculo_backup', 'estado']
    search_fields = ['motivo', 'observaciones']
    ordering_fields = ['fecha_inicio', 'fecha_devolucion', 'duracion_dias']
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo backup y registra en historial.
        """
        response = super().create(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_201_CREATED:
            backup = BackupVehiculo.objects.get(id=response.data['id'])
            
            # Registrar en historial
            try:
                from apps.vehicles.utils import registrar_backup_asignado
                registrar_backup_asignado(backup)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al registrar historial para backup {backup.id}: {e}")
        
        return response
    
    @extend_schema(
        description="Marca un backup como devuelto y calcula la duración",
        responses={200: BackupVehiculoSerializer}
    )
    @action(detail=True, methods=['post'], url_path='devolver')
    @transaction.atomic
    def devolver(self, request, pk=None):
        """
        Marca un backup como devuelto.
        
        Endpoint: POST /api/v1/vehicles/backups/{id}/devolver/
        
        Proceso:
        1. Valida que el backup esté activo
        2. Establece fecha_devolucion = ahora
        3. Cambia estado a DEVUELTO
        4. Calcula duración automáticamente
        5. Crea evento en historial del vehículo principal
        """
        backup = self.get_object()
        
        if backup.estado != "ACTIVO":
            return Response(
                {"detail": "Solo se pueden devolver backups activos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Marcar como devuelto
        backup.fecha_devolucion = timezone.now()
        backup.estado = "DEVUELTO"
        backup.calcular_duracion()
        backup.save()
        
        # Crear evento en historial
        from apps.vehicles.utils import registrar_evento_historial
        registrar_evento_historial(
            vehiculo=backup.vehiculo_principal,
            tipo_evento="BACKUP_DEVUELTO",
            ot=backup.ot,
            supervisor=request.user,
            descripcion=f"Backup {backup.vehiculo_backup.patente} devuelto. Duración: {backup.duracion_dias:.2f} días",
            fecha_salida=backup.fecha_devolucion,
            backup=backup,
        )
        
        # Si el vehículo principal no tiene más backups activos, cambiar estado a OPERATIVO
        backups_activos = BackupVehiculo.objects.filter(
            vehiculo_principal=backup.vehiculo_principal,
            estado="ACTIVO"
        ).exists()
        
        if not backups_activos:
            # Verificar si hay OTs abiertas
            from apps.workorders.models import OrdenTrabajo
            ots_abiertas = OrdenTrabajo.objects.filter(
                vehiculo=backup.vehiculo_principal,
                estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA", "EN_QA"]
            ).exists()
            
            if not ots_abiertas:
                backup.vehiculo_principal.estado_operativo = "OPERATIVO"
                backup.vehiculo_principal.save(update_fields=["estado_operativo"])
        
        serializer = self.get_serializer(backup)
        return Response(serializer.data)




# ============== BLOQUEOS DE VEHÍCULOS =================
class BloqueoVehiculoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de bloqueos de vehículos.
    
    Endpoints:
    - GET /api/v1/vehicles/bloqueos/ → Listar bloqueos
    - POST /api/v1/vehicles/bloqueos/ → Crear bloqueo
    - GET /api/v1/vehicles/bloqueos/{id}/ → Ver bloqueo
    - PUT/PATCH /api/v1/vehicles/bloqueos/{id}/ → Editar bloqueo
    - DELETE /api/v1/vehicles/bloqueos/{id}/ → Eliminar bloqueo
    - POST /api/v1/vehicles/bloqueos/{id}/resolver/ → Resolver bloqueo
    """
    queryset = BloqueoVehiculo.objects.select_related("vehiculo", "creado_por", "resuelto_por").all().order_by("-creado_en")
    serializer_class = BloqueoVehiculoSerializer
    permission_classes = [VehiclePermission]
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["vehiculo", "tipo", "estado"]
    ordering_fields = ["creado_en"]
    
    def perform_create(self, serializer):
        """Asignar usuario automáticamente al crear bloqueo."""
        serializer.save(creado_por=self.request.user)
        
        # Registrar auditoría mejorada
        bloqueo = serializer.instance
        ip = get_client_ip(self.request)
        log_audit(
            usuario=self.request.user,
            accion="CREAR_BLOQUEO_VEHICULO",
            objeto_tipo="BloqueoVehiculo",
            objeto_id=str(bloqueo.id),
            payload={
                "vehiculo_id": str(bloqueo.vehiculo.id),
                "patente": bloqueo.vehiculo.patente,
                "tipo": bloqueo.tipo
            },
            ip_address=ip
        )
    
    @extend_schema(
        request=EmptySerializer,
        responses={200: None},
        description="Resuelve un bloqueo de vehículo"
    )
    @action(detail=True, methods=['post'], url_path='resolver')
    @transaction.atomic
    def resolver(self, request, pk=None):
        """
        Resuelve un bloqueo de vehículo.
        
        Endpoint: POST /api/v1/vehicles/bloqueos/{id}/resolver/
        
        Permisos:
        - ADMIN, SUPERVISOR, JEFE_TALLER
        
        Body JSON:
        {
            "motivo_resolucion": "Motivo opcional"  // Opcional
        }
        """
        bloqueo = self.get_object()
        
        if bloqueo.estado != "ACTIVO":
            return Response(
                {"detail": "El bloqueo ya está resuelto o cancelado."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bloqueo.estado = "RESUELTO"
        bloqueo.resuelto_por = request.user
        bloqueo.resuelto_en = timezone.now()
        bloqueo.save()
        
        # Registrar auditoría
        Auditoria.objects.create(
            usuario=request.user,
            accion="RESOLVER_BLOQUEO_VEHICULO",
            objeto_tipo="BloqueoVehiculo",
            objeto_id=str(bloqueo.id),
            payload={
                "vehiculo_id": str(bloqueo.vehiculo.id),
                "patente": bloqueo.vehiculo.patente
            }
        )
        
        return Response({
            "detail": "Bloqueo resuelto correctamente.",
            "bloqueo": BloqueoVehiculoSerializer(bloqueo).data
        })



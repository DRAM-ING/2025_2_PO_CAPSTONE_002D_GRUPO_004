# apps/reports/views.py
"""
Vistas para generación de reportes y dashboards.

Este módulo define todos los endpoints de la API relacionados con:
- Dashboard Ejecutivo: KPIs y métricas para ejecutivos
- Reportes de Productividad: Estadísticas de productividad del taller
- Reportes PDF: Generación de reportes en formato PDF
- Reportes de Pausas: Análisis de pausas en las OT

Relaciones:
- Usa: apps/workorders/models.py (OrdenTrabajo, Pausa)
- Usa: apps/vehicles/models.py (Vehiculo)
- Usa: apps/users/models.py (User)
- Usa: apps/inventory/models.py (SolicitudRepuesto, MovimientoStock)
- Usa: apps/reports/pdf_generator.py (generación de PDFs)
- Conectado a: apps/reports/urls.py

Endpoints principales:
- /api/v1/reports/dashboard-ejecutivo/ → KPIs del dashboard ejecutivo
- /api/v1/reports/productividad/ → Reporte de productividad
- /api/v1/reports/pdf/ → Generar reporte PDF
- /api/v1/reports/pausas/ → Reporte de pausas

Características:
- Caché de KPIs (2 minutos) para optimizar rendimiento
- Generación de PDFs con ReportLab
- Agregaciones complejas con Django ORM
"""

from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum, Q, F  # Funciones de agregación
from django.utils import timezone
from django.core.cache import cache  # Sistema de caché
from datetime import timedelta
from drf_spectacular.utils import extend_schema

from apps.workorders.models import OrdenTrabajo, Pausa
from apps.vehicles.models import Vehiculo
from apps.users.models import User
from apps.inventory.models import SolicitudRepuesto, MovimientoStock


class DashboardEjecutivoView(views.APIView):
    """
    Dashboard con KPIs para el ejecutivo y jefe de taller.
    
    Endpoint: GET /api/v1/reports/dashboard-ejecutivo/
    
    Permisos:
    - EJECUTIVO, ADMIN, SPONSOR, JEFE_TALLER, SUPERVISOR, COORDINADOR_ZONA
    
    Características:
    - Caché de 2 minutos para optimizar rendimiento
    - KPIs en tiempo real
    - Últimas 5 OT
    - Pausas más frecuentes
    - Mecánicos con más carga
    - Tiempos promedio por estado
    - Cumplimiento SLA (últimos 30 días)
    
    Nota: Este dashboard muestra datos del taller Santa Marta (única sucursal).
    
    Retorna:
    - 200: {
        "kpis": {
            "ot_abiertas": 10,
            "ot_en_diagnostico": 2,
            "ot_en_ejecucion": 5,
            "ot_en_pausa": 1,
            "ot_en_qa": 3,
            "ot_retrabajo": 0,
            "ot_cerradas_hoy": 8,
            "vehiculos_en_taller": 12,
            "productividad_7_dias": 45
        },
        "ultimas_5_ot": [...],
        "pausas_frecuentes": [...],
        "mecanicos_carga": [...],
        "tiempos_promedio": {...}
      }
    - 403: Si no tiene permisos
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Obtiene todos los KPIs del dashboard ejecutivo",
        responses={200: None}
    )
    def get(self, request):
        """
        Retorna todos los KPIs requeridos para el dashboard ejecutivo.
        
        Proceso:
        1. Verifica permisos
        2. Intenta obtener del caché (válido 2 minutos)
        3. Si no está en caché, calcula todos los KPIs
        4. Guarda en caché
        5. Retorna datos
        
        Optimizaciones:
        - Caché de 2 minutos reduce carga en la base de datos
        - select_related para reducir queries
        - Agregaciones eficientes con Django ORM
        """
        # Verificar que el usuario tenga rol EJECUTIVO, ADMIN, SPONSOR, JEFE_TALLER, SUPERVISOR o COORDINADOR_ZONA
        if request.user.rol not in ("EJECUTIVO", "ADMIN", "SPONSOR", "JEFE_TALLER", "SUPERVISOR", "COORDINADOR_ZONA"):
            return Response(
                {"detail": "No autorizado para ver el dashboard ejecutivo."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar si se solicita refrescar (invalidar caché)
        refresh = request.query_params.get('refresh', '').lower() == 'true'
        
        # Intentar obtener del cache (válido por 2 minutos)
        # Esto reduce la carga en la base de datos para consultas frecuentes
        from apps.core.caching import get_or_set_cache
        cache_key = "dashboard_ejecutivo_kpis"
        
        # Si se solicita refrescar, invalidar el caché primero
        if refresh:
            cache.delete(cache_key)
        
        def calculate_kpis():
            """Calcula todos los KPIs del dashboard"""
            # Fecha actual para cálculos
            hoy = timezone.now().date()
            inicio_dia = timezone.make_aware(timezone.datetime.combine(hoy, timezone.datetime.min.time()))
            
            # ==================== KPIs DE OT ====================
            # Contar OT por estado
            ot_abiertas = OrdenTrabajo.objects.filter(estado="ABIERTA").count()
            ot_en_diagnostico = OrdenTrabajo.objects.filter(estado="EN_DIAGNOSTICO").count()
            ot_en_ejecucion = OrdenTrabajo.objects.filter(estado="EN_EJECUCION").count()
            ot_en_pausa = OrdenTrabajo.objects.filter(estado="EN_PAUSA").count()
            ot_en_qa = OrdenTrabajo.objects.filter(estado="EN_QA").count()
            ot_retrabajo = OrdenTrabajo.objects.filter(estado="RETRABAJO").count()
            
            # OT cerradas hoy
            ot_cerradas_hoy = OrdenTrabajo.objects.filter(
                estado="CERRADA",
                cierre__date=hoy
            ).count()
            
            # ==================== OTs ATRASADAS ====================
            # OTs que tienen fecha_limite_sla vencida y aún no están cerradas
            ot_atrasadas = OrdenTrabajo.objects.filter(
                fecha_limite_sla__lt=timezone.now(),
                estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA", "EN_QA"]
            ).count()
            
            # ==================== ÚLTIMAS 5 OT ====================
            # Obtener las 5 OT más recientes con optimización
            ultimas_5_ot = OrdenTrabajo.objects.select_related(
                'vehiculo', 'responsable', 'chofer'
            ).order_by('-apertura')[:5]
            
            # Serializar datos de las últimas 5 OT
            ultimas_5_ot_data = [{
                "id": str(ot.id),
                "patente": ot.vehiculo.patente if ot.vehiculo else "N/A",
                "estado": ot.estado,
                "responsable": f"{ot.responsable.first_name} {ot.responsable.last_name}" if ot.responsable else "Sin responsable",
                "apertura": ot.apertura.isoformat(),
                "tipo": ot.tipo if hasattr(ot, 'tipo') else None,
            } for ot in ultimas_5_ot]
            
            # ==================== VEHÍCULOS EN TALLER ====================
            # Total vehículos en taller (EN_ESPERA o EN_MANTENIMIENTO)
            vehiculos_en_taller = Vehiculo.objects.filter(
                estado__in=["EN_ESPERA", "EN_MANTENIMIENTO"]
            ).count()
            
            # ==================== INFORMACIÓN DE GUARDIAS ====================
            # Ingresos registrados hoy por guardia
            from apps.vehicles.models import IngresoVehiculo
            ingresos_hoy_por_guardia = User.objects.filter(
                rol="GUARDIA"
            ).annotate(
                ingresos_hoy=Count('ingresos_registrados', filter=Q(
                    ingresos_registrados__fecha_ingreso__date=hoy
                ), distinct=True)
            ).filter(ingresos_hoy__gt=0).order_by('-ingresos_hoy')
            
            guardias_data = [{
                "id": str(g.id),
                "nombre": f"{g.first_name} {g.last_name}",
                "username": g.username,
                "ingresos_hoy": g.ingresos_hoy
            } for g in ingresos_hoy_por_guardia]
            
            # ==================== PRODUCTIVIDAD ====================
            # Productividad del taller (OT cerradas en los últimos 7 días)
            hace_7_dias = hoy - timedelta(days=7)
            ot_cerradas_7_dias = OrdenTrabajo.objects.filter(
                estado="CERRADA",
                cierre__date__gte=hace_7_dias
            ).count()
            
            # ==================== DATOS PARA GRÁFICOS ====================
            # OT cerradas por día (últimos 7 días) para gráfico de línea
            ot_cerradas_por_dia = []
            for i in range(7):
                fecha = hoy - timedelta(days=6-i)
                cantidad = OrdenTrabajo.objects.filter(
                    estado="CERRADA",
                    cierre__date=fecha
                ).count()
                ot_cerradas_por_dia.append({
                    "fecha": fecha.isoformat(),
                    "cantidad": cantidad,
                    "dia": fecha.strftime("%d/%m")
                })
            
            # OT por estado para gráfico de barras
            ot_por_estado = [
                {"estado": "Abiertas", "cantidad": ot_abiertas},
                {"estado": "En Diagnóstico", "cantidad": ot_en_diagnostico},
                {"estado": "En Ejecución", "cantidad": ot_en_ejecucion},
                {"estado": "En Pausa", "cantidad": ot_en_pausa},
                {"estado": "En QA", "cantidad": ot_en_qa},
                {"estado": "Retrabajo", "cantidad": ot_retrabajo},
            ]
            
            # Productividad por mecánico (últimos 7 días) para gráfico de barras
            # Usar ots_asignadas (relación desde OrdenTrabajo.mecanico)
            mecanicos_productividad = User.objects.filter(
                rol="MECANICO"
            ).annotate(
                ot_cerradas=Count('ots_asignadas', filter=Q(
                    ots_asignadas__estado="CERRADA",
                    ots_asignadas__cierre__date__gte=hace_7_dias
                ), distinct=True)
            ).filter(ot_cerradas__gt=0).order_by('-ot_cerradas')[:10]
            
            mecanicos_productividad_data = [{
                "nombre": f"{m.first_name} {m.last_name}",
                "ot_cerradas": m.ot_cerradas
            } for m in mecanicos_productividad]
            
            # ==================== PAUSAS MÁS FRECUENTES ====================
            # Agrupar pausas por motivo y contar
            pausas_frecuentes = Pausa.objects.values('motivo').annotate(
                cantidad=Count('id')
            ).order_by('-cantidad')[:5]  # Top 5
            
            # ==================== MECÁNICOS CON MÁS CARGA ====================
            # Mecánicos con más carga de trabajo (OT activas)
            mecanicos_carga = User.objects.filter(
                rol="MECANICO",
                ots_responsable__estado__in=["ABIERTA", "EN_EJECUCION", "EN_PAUSA"]
            ).annotate(
                total_ots=Count('ots_responsable')
            ).order_by('-total_ots')[:5]  # Top 5
            
            # Serializar datos de mecánicos
            mecanicos_carga_data = [{
                "id": m.id,
                "nombre": f"{m.first_name} {m.last_name}",
                "total_ots": m.total_ots
            } for m in mecanicos_carga]
            
            # ==================== TIEMPOS PROMEDIO ====================
            # Calcular tiempos promedio por estado
            tiempos_promedio = {}
            estados = ["ABIERTA", "EN_EJECUCION", "EN_PAUSA", "EN_QA"]
            
            for estado in estados:
                ots = OrdenTrabajo.objects.filter(estado=estado)
                if estado == "CERRADA":
                    # Para cerradas, calcular tiempo desde apertura hasta cierre
                    tiempos = ots.filter(cierre__isnull=False).annotate(
                        tiempo_total=F('cierre') - F('apertura')
                    ).aggregate(
                        promedio=Avg('tiempo_total')
                    )
                else:
                    # Para otros estados, calcular tiempo desde apertura hasta ahora
                    tiempos = ots.annotate(
                        tiempo_actual=timezone.now() - F('apertura')
                    ).aggregate(
                        promedio=Avg('tiempo_actual')
                    )
                
                if tiempos['promedio']:
                    tiempos_promedio[estado] = str(tiempos['promedio'])
                else:
                    tiempos_promedio[estado] = None
            
            # ==================== CUMPLIMIENTO SLA ====================
            # Calcular cumplimiento SLA (OT cerradas dentro del plazo / Total OT cerradas)
            # Solo considerar OT cerradas en los últimos 30 días para tener una muestra representativa
            hace_30_dias = hoy - timedelta(days=30)
            ot_cerradas_30_dias = OrdenTrabajo.objects.filter(
                estado="CERRADA",
                cierre__date__gte=hace_30_dias,
                fecha_limite_sla__isnull=False
            )
            
            total_ot_cerradas_con_sla = ot_cerradas_30_dias.count()
            ot_cumplieron_sla = ot_cerradas_30_dias.filter(
                cierre__lte=F('fecha_limite_sla')
            ).count()
            
            # Calcular porcentaje de cumplimiento
            if total_ot_cerradas_con_sla > 0:
                sla_cumplimiento = round((ot_cumplieron_sla / total_ot_cerradas_con_sla) * 100, 1)
            else:
                sla_cumplimiento = 0.0
            
            # Datos para gráfico de cumplimiento SLA (últimos 7 días)
            cumplimiento_sla_por_dia = []
            for i in range(7):
                fecha = hoy - timedelta(days=6-i)
                ot_dia = OrdenTrabajo.objects.filter(
                    estado="CERRADA",
                    cierre__date=fecha,
                    fecha_limite_sla__isnull=False
                )
                total_dia = ot_dia.count()
                cumplieron_dia = ot_dia.filter(cierre__lte=F('fecha_limite_sla')).count()
                porcentaje_dia = round((cumplieron_dia / total_dia * 100), 1) if total_dia > 0 else 0
                cumplimiento_sla_por_dia.append({
                    "fecha": fecha.isoformat(),
                    "dia": fecha.strftime("%d/%m"),
                    "cumplimiento": porcentaje_dia,
                    "total": total_dia,
                    "cumplieron": cumplieron_dia
                })
            
            # ==================== CONSTRUIR RESPUESTA ====================
            response_data = {
                "kpis": {
                    "ot_abiertas": ot_abiertas,
                    "ot_en_diagnostico": ot_en_diagnostico,
                    "ot_en_ejecucion": ot_en_ejecucion,
                    "ot_en_pausa": ot_en_pausa,
                    "ot_en_qa": ot_en_qa,
                    "ot_retrabajo": ot_retrabajo,
                    "ot_cerradas_hoy": ot_cerradas_hoy,
                    "ot_atrasadas": ot_atrasadas,
                    "vehiculos_en_taller": vehiculos_en_taller,
                    "productividad_7_dias": ot_cerradas_7_dias,
                    "sla_cumplimiento": sla_cumplimiento,
                },
                "guardias": guardias_data,
                "ultimas_5_ot": ultimas_5_ot_data,
                "pausas_frecuentes": list(pausas_frecuentes),
                "mecanicos_carga": mecanicos_carga_data,
                "tiempos_promedio": tiempos_promedio,
                # Datos para gráficos
                "graficos": {
                    "ot_cerradas_por_dia": ot_cerradas_por_dia,
                    "ot_por_estado": ot_por_estado,
                    "mecanicos_productividad": mecanicos_productividad_data,
                    "cumplimiento_sla_por_dia": cumplimiento_sla_por_dia,
                }
            }
            return response_data

        # Obtener del cache o calcular
        response_data = get_or_set_cache(cache_key, calculate_kpis, timeout=120)
        return Response(response_data)


class ReporteProductividadView(views.APIView):
    """
    Reporte de productividad del taller Santa Marta.
    
    Endpoint: GET /api/v1/reports/productividad/
    
    Permisos:
    - EJECUTIVO, ADMIN, JEFE_TALLER, SUPERVISOR
    
    Parámetros (query):
    - fecha_inicio: Fecha de inicio (ISO format, opcional, default: 30 días atrás)
    - fecha_fin: Fecha de fin (ISO format, opcional, default: ahora)
    
    Retorna:
    - 200: {
        "periodo": {
            "inicio": "...",
            "fin": "..."
        },
        "total_ot_cerradas": 45,
        "estadisticas_mecanicos": [...]
      }
    - 403: Si no tiene permisos
    
    Nota: Este reporte muestra datos del taller Santa Marta (única sucursal).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Genera reporte de productividad",
        responses={200: None}
    )
    def get(self, request):
        """
        Genera reporte de productividad del taller.
        
        Calcula:
        - Total de OT cerradas en el período
        - Estadísticas por mecánico (total de OT cerradas)
        
        Parámetros:
        - fecha_inicio: Fecha de inicio del período
        - fecha_fin: Fecha de fin del período
        """
        if request.user.rol not in ("EJECUTIVO", "ADMIN", "JEFE_TALLER", "SUPERVISOR"):
            return Response(
                {"detail": "No autorizado."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Obtener parámetros de fecha
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        # Parsear fechas o usar defaults
        if fecha_inicio:
            try:
                # Intentar parsear como ISO format
                fecha_inicio_str = fecha_inicio.replace('Z', '+00:00')
                # Si tiene espacio en lugar de T, reemplazarlo
                fecha_inicio_str = fecha_inicio_str.replace(' ', 'T')
                fecha_inicio = timezone.datetime.fromisoformat(fecha_inicio_str)
            except (ValueError, AttributeError):
                # Si falla, intentar parsear con make_aware
                from django.utils.dateparse import parse_datetime
                fecha_inicio_parsed = parse_datetime(fecha_inicio)
                if fecha_inicio_parsed:
                    fecha_inicio = timezone.make_aware(fecha_inicio_parsed)
                else:
                    return Response(
                        {"error": "Formato de fecha_inicio inválido. Use formato ISO 8601."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        else:
            fecha_inicio = timezone.now() - timedelta(days=30)  # Default: 30 días atrás
        
        if fecha_fin:
            try:
                # Intentar parsear como ISO format
                fecha_fin_str = fecha_fin.replace('Z', '+00:00')
                # Si tiene espacio en lugar de T, reemplazarlo
                fecha_fin_str = fecha_fin_str.replace(' ', 'T')
                fecha_fin = timezone.datetime.fromisoformat(fecha_fin_str)
            except (ValueError, AttributeError):
                # Si falla, intentar parsear con make_aware
                from django.utils.dateparse import parse_datetime
                fecha_fin_parsed = parse_datetime(fecha_fin)
                if fecha_fin_parsed:
                    fecha_fin = timezone.make_aware(fecha_fin_parsed)
                else:
                    return Response(
                        {"error": "Formato de fecha_fin inválido. Use formato ISO 8601."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        else:
            fecha_fin = timezone.now()  # Default: ahora
        
        # Validar rango de fechas
        from apps.core.validators import validar_rango_fechas
        es_valido, mensaje = validar_rango_fechas(fecha_inicio, fecha_fin)
        if not es_valido:
            return Response(
                {"detail": mensaje},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # OT cerradas en el período
        ot_cerradas = OrdenTrabajo.objects.filter(
            estado="CERRADA",
            cierre__gte=fecha_inicio,
            cierre__lte=fecha_fin
        )
        
        # Estadísticas por mecánico
        from django.db.models import DurationField, ExpressionWrapper
        estadisticas_mecanicos = User.objects.filter(
            rol="MECANICO",
            ots_responsable__in=ot_cerradas
        ).annotate(
            total_cerradas=Count('ots_responsable', filter=Q(ots_responsable__estado="CERRADA"))
        )
        
        return Response({
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat(),
            },
            "total_ot_cerradas": ot_cerradas.count(),
            "estadisticas_mecanicos": [{
                "mecanico": f"{m.first_name} {m.last_name}",
                "total_cerradas": m.total_cerradas,
            } for m in estadisticas_mecanicos],
        })


class ReportePDFView(views.APIView):
    """
    Genera reportes en PDF (diario, semanal, mensual).
    
    Endpoint: GET /api/v1/reports/pdf/
    
    Permisos:
    - EJECUTIVO, ADMIN, JEFE_TALLER, SUPERVISOR, COORDINADOR_ZONA
    
    Parámetros (query):
    - tipo: Tipo de reporte ("diario", "semanal", "mensual")
    - fecha_inicio: Fecha de inicio (YYYY-MM-DD, opcional)
    - fecha_fin: Fecha de fin (YYYY-MM-DD, opcional)
    
    Retorna:
    - 200: Archivo PDF descargable
    - 400: Si el tipo es inválido
    - 403: Si no tiene permisos
    
    Tipos de reporte:
    - diario: Reporte del día (usa fecha_inicio o hoy)
    - semanal: Reporte de 7 días (usa fecha_inicio/fin o últimos 7 días)
    - mensual: Reporte de 30 días (usa fecha_inicio/fin o últimos 30 días)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Genera reporte PDF según tipo (diario, semanal, mensual)",
        parameters=[
            {
                "name": "tipo",
                "in": "query",
                "required": True,
                "schema": {"type": "string", "enum": ["diario", "semanal", "mensual"]}
            },
            {
                "name": "fecha_inicio",
                "in": "query",
                "required": False,
                "schema": {"type": "string", "format": "date"}
            },
            {
                "name": "fecha_fin",
                "in": "query",
                "required": False,
                "schema": {"type": "string", "format": "date"}
            }
        ],
        responses={200: {"content": {"application/pdf": {}}}}
    )
    def get(self, request):
        """
        Genera y retorna un reporte PDF.
        
        Proceso:
        1. Valida permisos
        2. Obtiene tipo de reporte y fechas
        3. Llama al generador de PDF apropiado
        4. Retorna PDF como descarga
        
        Tipos soportados:
        - diario: Reporte de un día
        - semanal: Reporte de 7 días
        - mensual: Reporte de 30 días
        """
        if request.user.rol not in ("EJECUTIVO", "ADMIN", "JEFE_TALLER", "SUPERVISOR", "COORDINADOR_ZONA"):
            return Response(
                {"detail": "No autorizado."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        tipo = request.query_params.get("tipo", "semanal")
        fecha_inicio_str = request.query_params.get("fecha_inicio")
        fecha_fin_str = request.query_params.get("fecha_fin")
        
        from .pdf_generator import generar_reporte_semanal_pdf, generar_reporte_diario_pdf
        from .pdf_generator_completo import (
            generar_reporte_estado_flota,
            generar_reporte_ordenes_trabajo,
        )
        from datetime import datetime, timedelta
        
        # Parsear fechas
        fecha_inicio = None
        fecha_fin = None
        if fecha_inicio_str:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"detail": "Formato de fecha_inicio inválido. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        if fecha_fin_str:
            try:
                fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"detail": "Formato de fecha_fin inválido. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validar rango de fechas
        if fecha_inicio and fecha_fin:
            from apps.core.validators import validar_rango_fechas
            es_valido, mensaje = validar_rango_fechas(fecha_inicio, fecha_fin)
            if not es_valido:
                return Response(
                    {"detail": mensaje},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validar permisos por rol
        # Supervisores ven todos los datos
        # Guardias no pueden acceder a reportes
        # Mecánicos solo ven OT asignadas
        if request.user.rol == "GUARDIA":
            return Response(
                {"detail": "Los guardias no pueden acceder a reportes."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Supervisores pueden ver todos los reportes
        
        # Tipos de reporte completos
        tipo_reporte = request.query_params.get("tipo_reporte")  # Nuevo parámetro para reportes completos
        
        if tipo_reporte:
            # Reportes completos
            if tipo_reporte == "estado_flota":
                supervisor = request.query_params.get("supervisor")
                tipo_vehiculo = request.query_params.get("tipo_vehiculo")
                estado_operativo = request.query_params.get("estado_operativo")
                pdf_bytes = generar_reporte_estado_flota(
                    fecha=fecha_inicio or timezone.now().date(),
                    supervisor=supervisor,
                    tipo_vehiculo=tipo_vehiculo,
                    estado_operativo=estado_operativo
                )
            elif tipo_reporte == "ordenes_trabajo":
                if not fecha_inicio:
                    fecha_fin = timezone.now().date()
                    fecha_inicio = fecha_fin - timedelta(days=30)
                if not fecha_fin:
                    fecha_fin = timezone.now().date()
                pdf_bytes = generar_reporte_ordenes_trabajo(
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin
                )
            elif tipo_reporte == "uso_vehiculo":
                # Función no implementada aún - usar reporte de órdenes de trabajo como alternativa
                return Response(
                    {"detail": "Reporte de uso de vehículo no está disponible aún. Use 'ordenes_trabajo'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif tipo_reporte == "mantenimientos":
                # Función no implementada aún
                return Response(
                    {"detail": "Reporte de mantenimientos recurrentes no está disponible aún."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif tipo_reporte == "por_site":
                # Usar reporte de órdenes de trabajo
                if not fecha_inicio:
                    fecha_fin = timezone.now().date()
                    fecha_inicio = fecha_fin - timedelta(days=30)
                if not fecha_fin:
                    fecha_fin = timezone.now().date()
                pdf_bytes = generar_reporte_ordenes_trabajo(
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin
                )
            elif tipo_reporte == "cumplimiento":
                # Función no implementada aún
                return Response(
                    {"detail": "Reporte de cumplimiento y política no está disponible aún."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif tipo_reporte == "inventario":
                # Función no implementada aún
                return Response(
                    {"detail": "Reporte de inventario no está disponible aún."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {"detail": f"Tipo de reporte '{tipo_reporte}' no válido."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Retornar PDF
            from django.http import HttpResponse
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            fecha_str = (fecha_inicio or timezone.now().date()).strftime('%Y-%m-%d')
            response['Content-Disposition'] = f'attachment; filename="reporte_{tipo_reporte}_{fecha_str}.pdf"'
            return response
        
        # Reportes originales (diario, semanal, mensual)
        if tipo == "diario":
            # Reporte diario
            fecha = None
            if fecha_inicio_str:
                fecha = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            pdf_bytes = generar_reporte_diario_pdf(fecha)
            filename = f"reporte_diario_{fecha or timezone.now().date()}.pdf"
        
        elif tipo == "semanal":
            # Reporte semanal (7 días)
            fecha_inicio = None
            fecha_fin = None
            if fecha_inicio_str:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            if fecha_fin_str:
                fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            if not fecha_inicio:
                # Default: últimos 7 días
                fecha_fin = timezone.now().date()
                fecha_inicio = fecha_fin - timedelta(days=7)
            pdf_bytes = generar_reporte_semanal_pdf(fecha_inicio, fecha_fin)
            filename = f"reporte_semanal_{fecha_inicio}_al_{fecha_fin}.pdf"
        
        elif tipo == "mensual":
            # Reporte mensual (30 días)
            fecha_inicio = None
            fecha_fin = None
            if fecha_inicio_str:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            if fecha_fin_str:
                fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            if not fecha_inicio:
                # Default: últimos 30 días
                fecha_fin = timezone.now().date()
                fecha_inicio = fecha_fin - timedelta(days=30)
            pdf_bytes = generar_reporte_semanal_pdf(fecha_inicio, fecha_fin)  # Usa generador semanal con 30 días
            filename = f"reporte_mensual_{fecha_inicio}_al_{fecha_fin}.pdf"
        
        else:
            return Response(
                {"detail": "Tipo de reporte inválido. Use: diario, semanal o mensual"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Retornar PDF como descarga
        from django.http import HttpResponse
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ReportePausasView(views.APIView):
    """
    Reporte de pausas por OT y mecánico.
    
    Endpoint: GET /api/v1/reports/pausas/
    
    Permisos:
    - EJECUTIVO, ADMIN, JEFE_TALLER, SUPERVISOR
    
    Retorna:
    - 200: {
        "pausas_activas": [...],
        "pausas_por_motivo": [...],
        "total_pausas_activas": 5
      }
    - 403: Si no tiene permisos
    
    Incluye:
    - Pausas activas (sin fecha de fin)
    - Pausas completadas con duración
    - Agrupación por motivo con duración promedio
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Genera reporte de pausas",
        responses={200: None}
    )
    def get(self, request):
        """
        Genera reporte de pausas.
        
        Calcula:
        - Pausas activas (sin fecha de fin)
        - Pausas completadas con duración
        - Agrupación por motivo con estadísticas
        
        Retorna:
        - Array de pausas activas
        - Estadísticas por motivo
        - Total de pausas activas
        """
        if request.user.rol not in ("EJECUTIVO", "ADMIN", "JEFE_TALLER", "SUPERVISOR"):
            return Response(
                {"detail": "No autorizado."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Pausas activas (sin fin)
        pausas_activas = Pausa.objects.filter(fin__isnull=True).select_related('ot', 'usuario')
        
        # Pausas completadas con duración
        pausas_completadas = Pausa.objects.filter(
            fin__isnull=False
        ).annotate(
            duracion=F('fin') - F('inicio')
        ).select_related('ot', 'usuario')
        
        # Agrupar por motivo
        pausas_por_motivo = Pausa.objects.values('motivo').annotate(
            total=Count('id'),
            duracion_promedio=Avg(F('fin') - F('inicio'), filter=Q(fin__isnull=False))
        )
        
        return Response({
            "pausas_activas": [{
                "id": str(p.id),
                "ot_id": str(p.ot.id),
                "usuario": f"{p.usuario.first_name} {p.usuario.last_name}",
                "motivo": p.motivo,
                "inicio": p.inicio.isoformat(),
            } for p in pausas_activas],
            "pausas_por_motivo": list(pausas_por_motivo),
            "total_pausas_activas": pausas_activas.count(),
        })


class DashboardJefeTallerView(views.APIView):
    """
    Dashboard específico para Jefe de Taller.
    
    Endpoint: GET /api/v1/reports/dashboard-jefe-taller/
    
    Permisos:
    - JEFE_TALLER, ADMIN
    
    Muestra:
    - OTs por estado
    - OTs atrasadas
    - Historial de OTs por vehículo/mecánico
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Obtiene reportes específicos para Jefe de Taller",
        responses={200: None}
    )
    def get(self, request):
        if request.user.rol not in ("JEFE_TALLER", "ADMIN"):
            return Response(
                {"detail": "No autorizado."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        refresh = request.query_params.get('refresh', '').lower() == 'true'
        from apps.core.caching import get_or_set_cache
        cache_key = "dashboard_jefe_taller"
        
        if refresh:
            cache.delete(cache_key)
        
        def calculate_report():
            hoy = timezone.now().date()
            
            # OTs por estado
            ot_por_estado = OrdenTrabajo.objects.values('estado').annotate(
                cantidad=Count('id')
            ).order_by('estado')
            
            # OTs atrasadas (con fecha_limite_sla vencida)
            ot_atrasadas = OrdenTrabajo.objects.filter(
                fecha_limite_sla__lt=timezone.now(),
                estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA", "EN_QA"]
            ).select_related('vehiculo', 'mecanico', 'responsable').order_by('fecha_limite_sla')
            
            ot_atrasadas_data = [{
                "id": str(ot.id),
                "patente": ot.vehiculo.patente if ot.vehiculo else "N/A",
                "estado": ot.estado,
                "mecanico": f"{ot.mecanico.first_name} {ot.mecanico.last_name}" if ot.mecanico else "Sin asignar",
                "fecha_limite_sla": ot.fecha_limite_sla.isoformat() if ot.fecha_limite_sla else None,
                "dias_atraso": (timezone.now() - ot.fecha_limite_sla).days if ot.fecha_limite_sla else 0,
            } for ot in ot_atrasadas]
            
            # Historial de OTs por vehículo (últimos 30 días)
            hace_30_dias = hoy - timedelta(days=30)
            historial_por_vehiculo = Vehiculo.objects.filter(
                ordenes__apertura__date__gte=hace_30_dias
            ).annotate(
                total_ots=Count('ordenes', distinct=True),
                ot_cerradas=Count('ordenes', filter=Q(ordenes__estado="CERRADA"), distinct=True),
                ot_activas=Count('ordenes', filter=Q(ordenes__estado__in=["ABIERTA", "EN_EJECUCION", "EN_PAUSA"]), distinct=True)
            ).filter(total_ots__gt=0).order_by('-total_ots')[:20]
            
            historial_vehiculos_data = [{
                "patente": v.patente,
                "marca": v.marca.nombre if v.marca else "N/A",
                "modelo": v.modelo,
                "total_ots": v.total_ots,
                "ot_cerradas": v.ot_cerradas,
                "ot_activas": v.ot_activas,
            } for v in historial_por_vehiculo]
            
            # Historial de OTs por mecánico (últimos 30 días)
            historial_por_mecanico = User.objects.filter(
                rol="MECANICO",
                ots_asignadas__apertura__date__gte=hace_30_dias
            ).annotate(
                total_ots=Count('ots_asignadas', distinct=True),
                ot_cerradas=Count('ots_asignadas', filter=Q(ots_asignadas__estado="CERRADA"), distinct=True),
                ot_activas=Count('ots_asignadas', filter=Q(ots_asignadas__estado__in=["ABIERTA", "EN_EJECUCION", "EN_PAUSA"]), distinct=True)
            ).filter(total_ots__gt=0).order_by('-total_ots')
            
            historial_mecanicos_data = [{
                "id": str(m.id),
                "nombre": f"{m.first_name} {m.last_name}",
                "total_ots": m.total_ots,
                "ot_cerradas": m.ot_cerradas,
                "ot_activas": m.ot_activas,
            } for m in historial_por_mecanico]
            
            return {
                "ot_por_estado": list(ot_por_estado),
                "ot_atrasadas": ot_atrasadas_data,
                "total_atrasadas": len(ot_atrasadas_data),
                "historial_por_vehiculo": historial_vehiculos_data,
                "historial_por_mecanico": historial_mecanicos_data,
            }
        
        response_data = get_or_set_cache(cache_key, calculate_report, timeout=120)
        return Response(response_data)


class DashboardSupervisorView(views.APIView):
    """
    Dashboard específico para Supervisor Zonal.
    
    Endpoint: GET /api/v1/reports/dashboard-supervisor/
    
    Permisos:
    - SUPERVISOR, ADMIN
    
    Muestra:
    - Comparación entre talleres (solo Santa Marta por ahora)
    - Carga de trabajo
    - Tiempos promedio
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Obtiene reportes específicos para Supervisor Zonal",
        responses={200: None}
    )
    def get(self, request):
        if request.user.rol not in ("SUPERVISOR", "ADMIN"):
            return Response(
                {"detail": "No autorizado."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        refresh = request.query_params.get('refresh', '').lower() == 'true'
        from apps.core.caching import get_or_set_cache
        cache_key = "dashboard_supervisor"
        
        if refresh:
            cache.delete(cache_key)
        
        def calculate_report():
            hoy = timezone.now().date()
            hace_30_dias = hoy - timedelta(days=30)
            
            # Carga de trabajo (OT activas por estado)
            carga_trabajo = OrdenTrabajo.objects.filter(
                estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA", "EN_QA"]
            ).values('estado').annotate(
                cantidad=Count('id')
            ).order_by('estado')
            
            # Tiempos promedio por estado (últimos 30 días)
            tiempos_promedio = {}
            estados = ["ABIERTA", "EN_EJECUCION", "EN_PAUSA", "EN_QA", "CERRADA"]
            
            for estado in estados:
                ots = OrdenTrabajo.objects.filter(
                    estado=estado,
                    apertura__date__gte=hace_30_dias
                )
                
                if estado == "CERRADA":
                    tiempos = ots.filter(cierre__isnull=False).annotate(
                        tiempo_total=F('cierre') - F('apertura')
                    ).aggregate(promedio=Avg('tiempo_total'))
                else:
                    tiempos = ots.annotate(
                        tiempo_actual=timezone.now() - F('apertura')
                    ).aggregate(promedio=Avg('tiempo_actual'))
                
                if tiempos['promedio'] and tiempos['promedio'] is not None:
                    try:
                        # Convertir a horas
                        if hasattr(tiempos['promedio'], 'total_seconds'):
                            total_seconds = tiempos['promedio'].total_seconds()
                        else:
                            # Si es un timedelta, usar directamente
                            total_seconds = tiempos['promedio'].total_seconds() if hasattr(tiempos['promedio'], 'total_seconds') else 0
                        horas = total_seconds / 3600
                        tiempos_promedio[estado] = round(horas, 2)
                    except (AttributeError, TypeError) as e:
                        # Si hay error al calcular, usar None
                        tiempos_promedio[estado] = None
                else:
                    tiempos_promedio[estado] = None
            
            # Comparación entre talleres (solo Santa Marta por ahora, pero estructura lista para múltiples)
            # Calcular SLA cumplimiento
            ot_cerradas = OrdenTrabajo.objects.filter(
                estado="CERRADA",
                cierre__date__gte=hace_30_dias,
                fecha_limite_sla__isnull=False
            )
            total_sla = ot_cerradas.count()
            cumplieron_sla = ot_cerradas.filter(cierre__lte=F('fecha_limite_sla')).count()
            sla_cumplimiento = round((cumplieron_sla / total_sla * 100), 1) if total_sla > 0 else 0
            
            talleres_data = [{
                "nombre": "Santa Marta",
                "ot_activas": OrdenTrabajo.objects.filter(
                    estado__in=["ABIERTA", "EN_EJECUCION", "EN_PAUSA"]
                ).count(),
                "ot_cerradas_mes": OrdenTrabajo.objects.filter(
                    estado="CERRADA",
                    cierre__date__gte=hace_30_dias
                ).count(),
                "sla_cumplimiento": sla_cumplimiento,
            }]
            
            return {
                "carga_trabajo": list(carga_trabajo),
                "tiempos_promedio": tiempos_promedio,
                "comparacion_talleres": talleres_data,
            }
        
        response_data = get_or_set_cache(cache_key, calculate_report, timeout=120)
        return Response(response_data)


class DashboardCoordinadorView(views.APIView):
    """
    Dashboard específico para Coordinador de Zona.
    
    Endpoint: GET /api/v1/reports/dashboard-coordinador/
    
    Permisos:
    - COORDINADOR_ZONA, ADMIN
    
    Muestra:
    - Backlog de OTs por taller
    - Vehículos críticos
    - Emergencias
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Obtiene reportes específicos para Coordinador de Zona",
        responses={200: None}
    )
    def get(self, request):
        if request.user.rol not in ("COORDINADOR_ZONA", "ADMIN"):
            return Response(
                {"detail": "No autorizado."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        refresh = request.query_params.get('refresh', '').lower() == 'true'
        from apps.core.caching import get_or_set_cache
        cache_key = "dashboard_coordinador"
        
        if refresh:
            cache.delete(cache_key)
        
        def calculate_report():
            hoy = timezone.now().date()
            
            # Backlog de OTs por taller (solo Santa Marta por ahora)
            backlog_talleres = [{
                "taller": "Santa Marta",
                "ot_pendientes": OrdenTrabajo.objects.filter(
                    estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA"]
                ).count(),
                "ot_atrasadas": OrdenTrabajo.objects.filter(
                    fecha_limite_sla__lt=timezone.now(),
                    estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA"]
                ).count(),
            }]
            
            # Vehículos críticos (con múltiples OTs activas o con OT atrasada)
            vehiculos_criticos = Vehiculo.objects.filter(
                ordenes__estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA"]
            ).annotate(
                ot_activas=Count('ordenes', filter=Q(
                    ordenes__estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA"]
                ), distinct=True),
                tiene_ot_atrasada=Count('ordenes', filter=Q(
                    ordenes__fecha_limite_sla__lt=timezone.now(),
                    ordenes__estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA"]
                ), distinct=True)
            ).filter(
                Q(ot_activas__gte=2) | Q(tiene_ot_atrasada__gt=0)
            ).distinct()[:20]
            
            vehiculos_criticos_data = [{
                "patente": v.patente,
                "marca": v.marca.nombre if v.marca else "N/A",
                "modelo": v.modelo,
                "ot_activas": v.ot_activas,
                "tiene_ot_atrasada": v.tiene_ot_atrasada > 0,
            } for v in vehiculos_criticos]
            
            # Emergencias (OTs con prioridad ALTA y estado activo)
            emergencias = OrdenTrabajo.objects.filter(
                prioridad="ALTA",
                estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA"]
            ).select_related('vehiculo', 'mecanico').order_by('-apertura')[:10]
            
            emergencias_data = [{
                "id": str(ot.id),
                "patente": ot.vehiculo.patente if ot.vehiculo else "N/A",
                "estado": ot.estado,
                "mecanico": f"{ot.mecanico.first_name} {ot.mecanico.last_name}" if ot.mecanico else "Sin asignar",
                "apertura": ot.apertura.isoformat(),
            } for ot in emergencias]
            
            return {
                "backlog_talleres": backlog_talleres,
                "vehiculos_criticos": vehiculos_criticos_data,
                "emergencias": emergencias_data,
            }
        
        response_data = get_or_set_cache(cache_key, calculate_report, timeout=120)
        return Response(response_data)


class DashboardSubgerenteView(views.APIView):
    """
    Dashboard específico para Subgerente de Flota (Alexis).
    
    Endpoint: GET /api/v1/reports/dashboard-subgerente/
    
    Permisos:
    - SUBGERENTE_NACIONAL, EJECUTIVO, ADMIN
    
    Muestra:
    - KPIs globales (OTs mensuales, tiempos de reparación, disponibilidad estimada)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Obtiene reportes ejecutivos nacionales para Subgerente de Flota",
        responses={200: None}
    )
    def get(self, request):
        if request.user.rol not in ("SUBGERENTE_NACIONAL", "EJECUTIVO", "ADMIN"):
            return Response(
                {"detail": "No autorizado."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        refresh = request.query_params.get('refresh', '').lower() == 'true'
        from apps.core.caching import get_or_set_cache
        cache_key = "dashboard_subgerente"
        
        if refresh:
            cache.delete(cache_key)
        
        def calculate_report():
            hoy = timezone.now().date()
            inicio_mes = hoy.replace(day=1)
            hace_30_dias = hoy - timedelta(days=30)
            
            # OTs mensuales
            ot_mensuales = OrdenTrabajo.objects.filter(
                apertura__date__gte=inicio_mes
            ).count()
            
            ot_cerradas_mes = OrdenTrabajo.objects.filter(
                estado="CERRADA",
                cierre__date__gte=inicio_mes
            ).count()
            
            # Tiempos de reparación promedio (últimos 30 días)
            ot_cerradas_30_dias = OrdenTrabajo.objects.filter(
                estado="CERRADA",
                cierre__date__gte=hace_30_dias,
                cierre__isnull=False
            ).annotate(
                tiempo_reparacion=F('cierre') - F('apertura')
            ).aggregate(
                promedio=Avg('tiempo_reparacion')
            )
            
            tiempo_promedio_horas = None
            if ot_cerradas_30_dias['promedio']:
                total_seconds = ot_cerradas_30_dias['promedio'].total_seconds()
                tiempo_promedio_horas = round(total_seconds / 3600, 2)
            
            # Disponibilidad estimada de flota
            total_vehiculos = Vehiculo.objects.filter(estado__in=["ACTIVO", "EN_ESPERA", "EN_MANTENIMIENTO"]).count()
            vehiculos_operativos = Vehiculo.objects.filter(estado="ACTIVO").count()
            disponibilidad = round((vehiculos_operativos / total_vehiculos * 100), 1) if total_vehiculos > 0 else 0
            
            # Tendencias (OTs por semana en el último mes)
            tendencias_semanales = []
            for i in range(4):
                semana_inicio = inicio_mes + timedelta(weeks=i)
                semana_fin = semana_inicio + timedelta(days=6)
                if semana_fin > hoy:
                    semana_fin = hoy
                
                ot_semana = OrdenTrabajo.objects.filter(
                    apertura__date__gte=semana_inicio,
                    apertura__date__lte=semana_fin
                ).count()
                
                ot_cerradas_semana = OrdenTrabajo.objects.filter(
                    estado="CERRADA",
                    cierre__date__gte=semana_inicio,
                    cierre__date__lte=semana_fin
                ).count()
                
                tendencias_semanales.append({
                    "semana": f"Semana {i+1}",
                    "fecha_inicio": semana_inicio.isoformat(),
                    "fecha_fin": semana_fin.isoformat(),
                    "ot_creadas": ot_semana,
                    "ot_cerradas": ot_cerradas_semana,
                })
            
            return {
                "kpis": {
                    "ot_mensuales": ot_mensuales,
                    "ot_cerradas_mes": ot_cerradas_mes,
                    "tiempo_reparacion_promedio_horas": tiempo_promedio_horas,
                    "disponibilidad_flota": disponibilidad,
                    "vehiculos_operativos": vehiculos_operativos,
                    "total_vehiculos": total_vehiculos,
                },
                "tendencias_semanales": tendencias_semanales,
            }
        
        response_data = get_or_set_cache(cache_key, calculate_report, timeout=120)
        return Response(response_data)

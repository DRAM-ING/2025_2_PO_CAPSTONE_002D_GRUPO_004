# apps/reports/pdf_generator_completo.py
"""
Generador completo de reportes PDF con toda la información requerida.

Este módulo contiene funciones para generar los 7 tipos de reportes principales:
1. Reporte de Estado de la Flota (General)
2. Reporte de Órdenes de Trabajo (OT)
3. Reporte de Uso del Vehículo / Comportamiento Operacional
4. Reporte de Mantenimientos Recurrentes
5. Reporte por Zona / Supervisor
6. Reporte de Cumplimiento y Política
7. Reporte de Inventario / Características Vehiculares
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Sum, Q, F, Max, Min
from django.db.models.functions import Extract


def _get_styles():
    """Retorna estilos reutilizables para los PDFs."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003DA5'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#003DA5'),
        spaceAfter=12,
        spaceBefore=12
    )
    return styles, title_style, heading_style


def _create_table(data, col_widths=None):
    """Crea una tabla con estilo PepsiCo."""
    if col_widths is None:
        col_widths = [4*inch] * (len(data[0]) - 1) + [2*inch]
    
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003DA5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    return table


def generar_reporte_estado_flota(fecha=None, supervisor=None, tipo_vehiculo=None, estado_operativo=None):
    """
    ✅ 1. Reporte de Estado de la Flota (General)
    
    Incluye:
    - Resumen General (total vehículos, operativos, en taller, bloqueados, fuera de política, revisión vencida)
    - Indicadores clave (KPIs): % flota operativa, % flota con OT abiertas, tiempo promedio en taller, OT por semana/mes, vehículos sin movimiento
    - Filtros: Supervisor, Tipo de vehículo, Estado operativo
    """
    if not fecha:
        fecha = timezone.now().date()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles, title_style, heading_style = _get_styles()
    
    # Título
    elements.append(Paragraph("REPORTE DE ESTADO DE LA FLOTA", title_style))
    elements.append(Paragraph(f"PepsiCo Chile - Sistema PGF", styles['Normal']))
    elements.append(Paragraph(f"Fecha: {fecha}", styles['Normal']))
    if supervisor:
        elements.append(Paragraph(f"Supervisor: {supervisor}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Importar modelos
    from apps.vehicles.models import Vehiculo
    from apps.workorders.models import OrdenTrabajo
    
    # Filtros
    filtros = {}
    if supervisor:
        filtros['supervisor__username'] = supervisor
    if tipo_vehiculo:
        filtros['tipo'] = tipo_vehiculo
    if estado_operativo:
        filtros['estado_operativo'] = estado_operativo
    
    vehiculos = Vehiculo.objects.filter(**filtros)
    
    # Resumen General
    total_vehiculos = vehiculos.count()
    vehiculos_operativos = vehiculos.filter(estado_operativo="OPERATIVO").count()
    vehiculos_en_taller = vehiculos.filter(estado_operativo="EN_TALLER").count()
    vehiculos_bloqueados = vehiculos.filter(tct=True).count()
    vehiculos_fuera_politica = vehiculos.filter(cumplimiento="FUERA_POLITICA").count()
    
    # Vehículos con revisión vencida
    hoy = timezone.now().date()
    vehiculos_revision_vencida = vehiculos.filter(
        proxima_revision__lt=hoy
    ).count()
    
    # KPIs
    porcentaje_operativo = (vehiculos_operativos / total_vehiculos * 100) if total_vehiculos > 0 else 0
    
    # Vehículos con OT abiertas
    vehiculos_con_ot = vehiculos.filter(
        ordenes__estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA", "EN_QA"]
    ).distinct().count()
    porcentaje_con_ot = (vehiculos_con_ot / total_vehiculos * 100) if total_vehiculos > 0 else 0
    
    # Tiempo promedio de permanencia en taller
    from apps.vehicles.models import HistorialVehiculo
    tiempos_taller = HistorialVehiculo.objects.filter(
        tipo_evento="OT_CERRADA",
        vehiculo__in=vehiculos,
        tiempo_permanencia__isnull=False
    ).aggregate(promedio=Avg('tiempo_permanencia'))
    tiempo_promedio_taller = tiempos_taller['promedio'] or 0
    
    # OT por semana (últimos 7 días)
    fecha_semana = fecha - timedelta(days=7)
    ot_semana = OrdenTrabajo.objects.filter(
        apertura__date__gte=fecha_semana,
        apertura__date__lte=fecha,
        vehiculo__in=vehiculos
    ).count()
    
    # OT por mes (últimos 30 días)
    fecha_mes = fecha - timedelta(days=30)
    ot_mes = OrdenTrabajo.objects.filter(
        apertura__date__gte=fecha_mes,
        apertura__date__lte=fecha,
        vehiculo__in=vehiculos
    ).count()
    
    # Vehículos sin movimiento (más de X días, default 7)
    fecha_sin_movimiento = fecha - timedelta(days=7)
    vehiculos_sin_movimiento = vehiculos.filter(
        ultimo_movimiento__lt=timezone.make_aware(
            timezone.datetime.combine(fecha_sin_movimiento, timezone.datetime.min.time())
        )
    ).count()
    
    # Tabla de Resumen General
    resumen_data = [
        ['Indicador', 'Valor'],
        ['Total de Vehículos', str(total_vehiculos)],
        ['Vehículos Operativos', str(vehiculos_operativos)],
        ['Vehículos en Taller', str(vehiculos_en_taller)],
        ['Vehículos Bloqueados/TCT', str(vehiculos_bloqueados)],
        ['Vehículos Fuera de Política', str(vehiculos_fuera_politica)],
        ['Vehículos con Revisión Vencida', str(vehiculos_revision_vencida)],
    ]
    
    elements.append(Paragraph("Resumen General", heading_style))
    elements.append(_create_table(resumen_data))
    elements.append(Spacer(1, 0.3*inch))
    
    # Tabla de KPIs
    kpi_data = [
        ['KPI', 'Valor'],
        ['% Flota Operativa', f"{porcentaje_operativo:.2f}%"],
        ['% Flota con OT Abiertas', f"{porcentaje_con_ot:.2f}%"],
        ['Tiempo Promedio en Taller (días)', f"{tiempo_promedio_taller:.2f}"],
        ['OT por Semana', str(ot_semana)],
        ['OT por Mes', str(ot_mes)],
        ['Vehículos Sin Movimiento (>7 días)', str(vehiculos_sin_movimiento)],
    ]
    
    elements.append(Paragraph("Indicadores Clave (KPIs)", heading_style))
    elements.append(_create_table(kpi_data))
    elements.append(Spacer(1, 0.3*inch))
    
    # Pie de página
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Generado el {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph("Sistema PGF - PepsiCo Chile", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generar_reporte_ordenes_trabajo(fecha_inicio=None, fecha_fin=None):
    """
    ✅ 2. Reporte de Órdenes de Trabajo (OT)
    
    Incluye:
    - Open Dashboard: OT abiertas, en ejecución, en QA, cerradas, rechazadas
    - Información por OT: número, vehículo, estado, tiempos de proceso, causa de ingreso/salida
    - Alertas: OT con SLA vencido, OT sin actividad, pausas prolongadas
    """
    if not fecha_inicio:
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles, title_style, heading_style = _get_styles()
    
    # Título
    elements.append(Paragraph("REPORTE DE ÓRDENES DE TRABAJO", title_style))
    elements.append(Paragraph(f"PepsiCo Chile - Sistema PGF", styles['Normal']))
    elements.append(Paragraph(f"Período: {fecha_inicio} al {fecha_fin}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Importar modelos
    from apps.workorders.models import OrdenTrabajo, Pausa
    
    # Filtros
    filtros = {}
    
    # Open Dashboard
    ot_abiertas = OrdenTrabajo.objects.filter(estado="ABIERTA", **filtros).count()
    ot_en_ejecucion = OrdenTrabajo.objects.filter(estado="EN_EJECUCION", **filtros).count()
    ot_en_qa = OrdenTrabajo.objects.filter(estado="EN_QA", **filtros).count()
    ot_cerradas = OrdenTrabajo.objects.filter(
        estado="CERRADA",
        cierre__date__gte=fecha_inicio,
        cierre__date__lte=fecha_fin,
        **filtros
    ).count()
    ot_rechazadas = OrdenTrabajo.objects.filter(
        estado="RETRABAJO",
        apertura__date__gte=fecha_inicio,
        apertura__date__lte=fecha_fin,
        **filtros
    ).count()
    
    dashboard_data = [
        ['Estado', 'Cantidad'],
        ['OT Abiertas', str(ot_abiertas)],
        ['OT en Ejecución', str(ot_en_ejecucion)],
        ['OT en QA', str(ot_en_qa)],
        ['OT Cerradas', str(ot_cerradas)],
        ['OT Rechazadas', str(ot_rechazadas)],
    ]
    
    elements.append(Paragraph("Open Dashboard", heading_style))
    elements.append(_create_table(dashboard_data))
    elements.append(Spacer(1, 0.3*inch))
    
    # Información por OT
    ot_list = OrdenTrabajo.objects.filter(
        apertura__date__gte=fecha_inicio,
        apertura__date__lte=fecha_fin,
        **filtros
    ).select_related('vehiculo', 'supervisor', 'mecanico').order_by('-apertura')[:50]  # Limitar a 50 para el PDF
    
    if ot_list:
        ot_data = [['OT', 'Vehículo', 'Estado', 'Tiempo Total (días)', 'Causa Ingreso']]
        for ot in ot_list:
            tiempo_total = ot.tiempo_total_reparacion or 0
            causa_ingreso = (ot.causa_ingreso or ot.motivo or "")[:50]
            ot_data.append([
                str(ot.id)[:8],
                ot.vehiculo.patente if ot.vehiculo else "N/A",
                ot.estado,
                f"{tiempo_total:.2f}",
                causa_ingreso
            ])
        
        elements.append(Paragraph("Información por OT (primeras 50)", heading_style))
        elements.append(_create_table(ot_data, col_widths=[1*inch, 1*inch, 1.5*inch, 1*inch, 2.5*inch]))
        elements.append(Spacer(1, 0.3*inch))
    
    # Alertas
    ahora = timezone.now()
    ot_sla_vencido = OrdenTrabajo.objects.filter(
        sla_vencido=True,
        estado__in=["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA", "EN_QA"],
        **filtros
    ).count()
    
    # OT sin actividad por más de X horas (default 24)
    fecha_sin_actividad = ahora - timedelta(hours=24)
    ot_sin_actividad = OrdenTrabajo.objects.filter(
        estado__in=["EN_EJECUCION", "EN_PAUSA"],
        updated_at__lt=fecha_sin_actividad,
        **filtros
    ).count()
    
    # Pausas prolongadas (más de 4 horas)
    pausas_prolongadas = Pausa.objects.filter(
        fin__isnull=True,
        inicio__lt=ahora - timedelta(hours=4),
        ot__in=OrdenTrabajo.objects.filter(**filtros)
    ).count()
    
    alertas_data = [
        ['Alerta', 'Cantidad'],
        ['OT con SLA Vencido', str(ot_sla_vencido)],
        ['OT Sin Actividad (>24h)', str(ot_sin_actividad)],
        ['Pausas Prolongadas (>4h)', str(pausas_prolongadas)],
    ]
    
    elements.append(Paragraph("Alertas", heading_style))
    elements.append(_create_table(alertas_data))
    elements.append(Spacer(1, 0.3*inch))
    
    # Pie de página
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Generado el {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph("Sistema PGF - PepsiCo Chile", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


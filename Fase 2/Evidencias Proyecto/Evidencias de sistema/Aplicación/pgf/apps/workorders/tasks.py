import io
from celery import shared_task
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.core.files.storage import default_storage
from django.utils import timezone


from .models import OrdenTrabajo, Evidencia, Auditoria
from django.contrib.auth import get_user_model



User = get_user_model()

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generar_pdf_cierre(self, ot_id: str, user_id: int | None):
    """
    Genera PDF de cierre de OT con manejo robusto de errores.
    
    Args:
        self: Instancia de la tarea (para retry)
        ot_id: ID de la orden de trabajo
        user_id: ID del usuario que solicita el PDF
    
    Returns:
        URL del PDF generado
    
    Raises:
        Retry: Si hay error temporal, reintenta hasta 3 veces
    """
    import logging
    logger = logging.getLogger('apps.workorders.tasks')
    
    try:
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        
        # Obtener OT con manejo de errores
        try:
            ot = (OrdenTrabajo.objects
                .select_related("vehiculo", "responsable")
                .prefetch_related("items", "evidencias", "pausas")
                .get(id=ot_id))
        except OrdenTrabajo.DoesNotExist:
            # Si la OT no existe, probablemente fue eliminada después de encolar la tarea
            # No reintentar, simplemente registrar y retornar None
            logger.warning(f"OT {ot_id} no encontrada para generar PDF. La OT probablemente fue eliminada.")
            return None
        
        usuario = User.objects.filter(id=user_id).first() if user_id else None

        # Crear PDF profesional
        buff = io.BytesIO()
        doc = SimpleDocTemplate(buff, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#374151'),
            spaceAfter=12
        )
        
        # Título
        story.append(Paragraph("ORDEN DE TRABAJO", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Información principal
        info_data = [
            ['<b>ID:</b>', str(ot.id)[:8]],
            ['<b>Estado:</b>', ot.estado],
            ['<b>Vehículo:</b>', f"{ot.vehiculo.patente} - {ot.vehiculo.marca} {ot.vehiculo.modelo}" if ot.vehiculo else "N/A"],
            ['<b>Responsable:</b>', f"{ot.responsable.first_name} {ot.responsable.last_name}" if ot.responsable else "Sin responsable"],
            ['<b>Tipo:</b>', ot.tipo or "MANTENCION"],
            ['<b>Prioridad:</b>', ot.prioridad or "MEDIA"],
            ['<b>Apertura:</b>', ot.apertura.strftime("%d/%m/%Y %H:%M")],
            ['<b>Cierre:</b>', ot.cierre.strftime("%d/%m/%Y %H:%M") if ot.cierre else "Pendiente"],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Motivo
        if ot.motivo:
            story.append(Paragraph("<b>Motivo:</b>", heading_style))
            story.append(Paragraph(ot.motivo, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # Items
        items = ot.items.all()
        if items:
            story.append(Paragraph("<b>Items de Trabajo:</b>", heading_style))
            items_data = [['Tipo', 'Descripción', 'Cantidad', 'Costo Unit.', 'Total']]
            total_general = 0
            for item in items:
                total_item = float(item.cantidad * item.costo_unitario)
                total_general += total_item
                items_data.append([
                    item.tipo,
                    item.descripcion[:50],
                    str(item.cantidad),
                    f"${item.costo_unitario:,.2f}",
                    f"${total_item:,.2f}"
                ])
            items_data.append(['', '', '', '<b>TOTAL:</b>', f'<b>${total_general:,.2f}</b>'])
            
            items_table = Table(items_data, colWidths=[1*inch, 2.5*inch, 0.8*inch, 1*inch, 1*inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -2), 1, colors.grey),
                ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            story.append(items_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Pausas
        pausas = ot.pausas.filter(fin__isnull=False)
        if pausas.exists():
            story.append(Paragraph("<b>Pausas Registradas:</b>", heading_style))
            pausas_data = [['Motivo', 'Inicio', 'Fin', 'Duración']]
            for pausa in pausas:
                duracion = pausa.fin - pausa.inicio
                horas = int(duracion.total_seconds() / 3600)
                minutos = int((duracion.total_seconds() % 3600) / 60)
                pausas_data.append([
                    pausa.motivo[:40],
                    pausa.inicio.strftime("%d/%m/%Y %H:%M"),
                    pausa.fin.strftime("%d/%m/%Y %H:%M"),
                    f"{horas}h {minutos}m"
                ])
            
            pausas_table = Table(pausas_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1*inch])
            pausas_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(pausas_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Evidencias
        evidencias = ot.evidencias.all()
        if evidencias.exists():
            story.append(Paragraph("<b>Evidencias:</b>", heading_style))
            evidencias_list = []
            for ev in evidencias:
                evidencias_list.append(f"• {ev.tipo}: {ev.descripcion or 'Sin descripción'}")
            story.append(Paragraph("<br/>".join(evidencias_list), styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # Pie de página
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"<i>Documento generado el {timezone.now().strftime('%d/%m/%Y %H:%M')} - Sistema PGF</i>",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
        ))
        
        # Construir PDF
        doc.build(story)
        buff.seek(0)

        # Guardar archivo en S3/LocalStack usando boto3 directamente
        import boto3
        import os
        from botocore.config import Config
        from django.conf import settings
        
        bucket = os.getenv("AWS_STORAGE_BUCKET_NAME", "pgf-evidencias-dev")
        s3_endpoint_internal = os.getenv("AWS_S3_ENDPOINT_URL", "http://localstack:4566")
        s3_endpoint_public = getattr(settings, 'AWS_PUBLIC_URL_PREFIX', os.getenv("AWS_PUBLIC_URL_PREFIX", "http://localhost:4566"))
        
        # Crear cliente S3
        use_local = "localstack" in s3_endpoint_internal.lower() or "localhost:4566" in s3_endpoint_internal.lower()
        s3 = boto3.client(
            "s3",
            endpoint_url=s3_endpoint_internal if use_local else None,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
            region_name=os.getenv("AWS_S3_REGION_NAME", "us-east-1"),
            config=Config(s3={"addressing_style": "path"}) if use_local else None
        )
        
        # Subir PDF a S3
        key = f"cierres/ot-{ot.id}-{timezone.now().strftime('%Y%m%d-%H%M%S')}.pdf"
        buff.seek(0)
        s3.upload_fileobj(buff, bucket, key, ExtraArgs={'ContentType': 'application/pdf'})
        
        # Construir URL pública
        url = f"{s3_endpoint_public}/{bucket}/{key}"

        # Registrar evidencia
        Evidencia.objects.create(ot=ot, tipo="PDF", url=url, descripcion="Informe de cierre de OT")

        # Auditoría
        Auditoria.objects.create(
            usuario=usuario,
            accion="GENERAR_PDF_CIERRE",
            objeto_tipo="OrdenTrabajo",
            objeto_id=str(ot.id),
            payload={"evidencia": url}
        )
        
        return url
    except Exception as e:
        logger.error(f"Error al generar PDF de cierre para OT {ot_id}: {e}", exc_info=True)
        # No reintentar si la OT no existe (ya se maneja arriba)
        # Solo reintentar para errores temporales (conexión, S3, etc.)
        if "no encontrada" in str(e).lower() or "does not exist" in str(e).lower():
            logger.warning(f"No se reintentará la generación de PDF para OT {ot_id} (no existe)")
            return None
        # Reintentar si es un error temporal
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        raise


# apps/workorders/tasks.py


@shared_task
def ping_task():
    return "pong"

# Importar tareas de colación para que Celery las descubra
from . import tasks_colacion  # noqa

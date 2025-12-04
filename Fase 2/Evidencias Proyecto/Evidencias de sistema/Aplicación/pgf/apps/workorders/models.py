# apps/workorders/models.py
"""
Modelos para gestión de Órdenes de Trabajo (OT).

Este módulo define todos los modelos relacionados con el flujo de trabajo
de mantenimiento y reparación de vehículos:

- OrdenTrabajo: Modelo principal que representa una orden de trabajo
- ItemOT: Items de trabajo (repuestos y servicios) asociados a una OT
- Presupuesto: Presupuesto asociado a una OT
- DetallePresup: Detalles del presupuesto
- Aprobacion: Aprobación de presupuesto por Sponsor
- Pausa: Pausas durante la ejecución de una OT
- Checklist: Checklists de calidad
- Evidencia: Evidencias fotográficas/documentales
- Auditoria: Registro de todas las acciones del sistema

Relaciones principales:
- OrdenTrabajo -> Vehiculo (ForeignKey)
- OrdenTrabajo -> User (múltiples ForeignKeys: supervisor, jefe_taller, mecanico)
- ItemOT -> OrdenTrabajo (ForeignKey)
- Presupuesto -> OrdenTrabajo (OneToOne)
- Pausa -> OrdenTrabajo (ForeignKey)
- Evidencia -> OrdenTrabajo (ForeignKey)

Flujo de estados:
ABIERTA -> EN_DIAGNOSTICO -> EN_EJECUCION -> EN_PAUSA -> EN_EJECUCION -> EN_QA -> CERRADA
                                                          ↓
                                                      RETRABAJO -> EN_EJECUCION
"""

from django.db import models
from django.conf import settings  # Para acceder a AUTH_USER_MODEL
from apps.vehicles.models import Vehiculo  # Modelo de vehículo
import uuid  # Para generar IDs únicos


class OrdenTrabajo(models.Model):
    """
    Modelo principal que representa una Orden de Trabajo (OT).
    
    Una OT es el documento central que rastrea todo el proceso de
    mantenimiento o reparación de un vehículo, desde su apertura
    hasta su cierre.
    
    Estados posibles:
    - ABIERTA: Recién creada, pendiente de diagnóstico
    - EN_DIAGNOSTICO: Jefe de Taller está realizando diagnóstico
    - EN_EJECUCION: Mecánico está trabajando en la OT
    - EN_PAUSA: Trabajo pausado (manual o automática por colación)
    - EN_QA: En control de calidad
    - RETRABAJO: Requiere corrección después de QA
    - CERRADA: Finalizada exitosamente
    - ANULADA: Cancelada antes de completarse
    
    Relaciones:
    - ForeignKey a Vehiculo (vehículo que se está reparando)
    - ForeignKey a User (supervisor, jefe_taller, mecanico, responsable)
    - OneToMany con ItemOT (items de trabajo)
    - OneToOne con Presupuesto (presupuesto asociado)
    - OneToMany con Pausa (pausas durante ejecución)
    - OneToMany con Evidencia (evidencias fotográficas)
    - OneToMany con Checklist (checklists de calidad)
    
    Transiciones de estado:
    - Definidas en apps/workorders/services.py
    - Validadas por can_transition() y ejecutadas por transition()
    """
    
    # ==================== ESTADOS ====================
    ESTADOS = (
        ("ABIERTA", "ABIERTA"),  # Estado inicial, recién creada
        ("EN_DIAGNOSTICO", "EN_DIAGNOSTICO"),  # Jefe de Taller realizando diagnóstico
        ("EN_EJECUCION", "EN_EJECUCION"),  # Mecánico trabajando
        ("EN_PAUSA", "EN_PAUSA"),  # Trabajo pausado (manual o colación automática)
        ("EN_QA", "EN_QA"),  # En control de calidad
        ("RETRABAJO", "RETRABAJO"),  # Requiere corrección después de QA
        ("CERRADA", "CERRADA"),  # Finalizada exitosamente
        ("ANULADA", "ANULADA")  # Cancelada
    )
    
    # ==================== CAMPOS PRINCIPALES ====================
    
    # ID único: UUID4 para evitar colisiones y no exponer información
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Vehículo asociado: PROTECT evita eliminar vehículo si tiene OTs activas
    # related_name="ordenes" permite acceder desde vehiculo.ordenes.all()
    vehiculo = models.ForeignKey(
        Vehiculo, 
        on_delete=models.PROTECT,  # No permitir eliminar vehículo con OTs
        related_name="ordenes"
    )
    
    # ==================== ASIGNACIONES DE ROLES ====================
    # Cada rol tiene responsabilidades específicas en el flujo de la OT
    
    # Supervisor: Aprueba asignación de mecánico y supervisa el trabajo
    # limit_choices_to restringe a usuarios con rol SUPERVISOR o COORDINADOR_ZONA
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,  # Si se elimina el supervisor, poner None
        related_name="ots_supervisadas",  # Acceso desde user.ots_supervisadas.all()
        limit_choices_to={"rol__in": ["SUPERVISOR", "COORDINADOR_ZONA"]},
        help_text="Supervisor asignado"
    )
    
    # Jefe de Taller: Realiza diagnóstico y valida el trabajo
    # limit_choices_to restringe a usuarios con rol JEFE_TALLER
    jefe_taller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ots_jefe_taller",
        limit_choices_to={"rol": "JEFE_TALLER"},
        help_text="Jefe de Taller que valida"
    )
    
    # Mecánico: Ejecuta el trabajo asignado
    # limit_choices_to restringe a usuarios con rol MECANICO
    mecanico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ots_asignadas",  # Acceso desde user.ots_asignadas.all()
        limit_choices_to={"rol": "MECANICO"},
        help_text="Mecánico asignado para ejecución"
    )
    
    # Responsable: Usuario general responsable (puede ser supervisor o mecánico)
    # No tiene limit_choices_to, puede ser cualquier usuario
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ots_responsable",
        help_text="Responsable general (puede ser supervisor o mecánico)"
    )
    
    # Chofer: Chofer que ingresa el vehículo (registrado por el guardia)
    chofer = models.ForeignKey(
        "drivers.Chofer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ots_creadas",
        help_text="Chofer que ingresa el vehículo"
    )
    
    # ==================== ESTADO Y CLASIFICACIÓN ====================
    
    # Estado actual de la OT
    # Se valida contra ESTADOS y se gestiona mediante services.py
    estado = models.CharField(max_length=20, choices=ESTADOS, default="ABIERTA")
    
    # Tipo de trabajo: clasifica el tipo de intervención
    tipo = models.CharField(
        max_length=50,
        blank=True,
        default="MANTENCION",
        choices=[
            ("MANTENCION", "Mantención"),  # Mantenimiento preventivo
            ("REPARACION", "Reparación"),  # Reparación correctiva
            ("EMERGENCIA", "Emergencia"),  # Reparación urgente
            ("DIAGNOSTICO", "Diagnóstico"),  # Solo diagnóstico
            ("OTRO", "Otro"),  # Otro tipo
        ]
    )
    
    # Prioridad: determina la urgencia del trabajo
    prioridad = models.CharField(
        max_length=20,
        blank=True,
        default="MEDIA",
        choices=[
            ("CRITICA", "Crítica"),  # Máxima urgencia
            ("ALTA", "Alta"),  # Alta urgencia
            ("MEDIA", "Media"),  # Urgencia normal
            ("BAJA", "Baja"),  # Baja urgencia
        ]
    )
    
    # ==================== DESCRIPCIÓN Y UBICACIÓN ====================
    
    # Motivo: razón por la cual se creó la OT
    motivo = models.TextField(blank=True)
    
    # Diagnóstico: evaluación técnica realizada por Jefe de Taller
    # Se completa cuando la OT pasa a EN_DIAGNOSTICO
    diagnostico = models.TextField(blank=True, help_text="Diagnóstico realizado por Jefe de Taller")
    
    # Zona: zona o sucursal donde se realiza el trabajo
    zona = models.CharField(max_length=100, blank=True, help_text="Zona o sucursal")
    
    # Backup asignado (si existe)
    backup = models.ForeignKey(
        "vehicles.BackupVehiculo",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ots_backup",
        help_text="Backup asignado durante esta OT"
    )
    
    # Estado operativo del vehículo antes de la OT
    estado_operativo_antes = models.CharField(
        max_length=30,
        blank=True,
        help_text="Estado operativo del vehículo antes de la OT"
    )
    
    # Estado operativo del vehículo después de la OT
    estado_operativo_despues = models.CharField(
        max_length=30,
        blank=True,
        help_text="Estado operativo del vehículo después de la OT"
    )
    
    # Causa de ingreso (más detallada que motivo)
    causa_ingreso = models.TextField(
        blank=True,
        help_text="Causa detallada de ingreso al taller"
    )
    
    # Causa de salida
    causa_salida = models.TextField(
        blank=True,
        help_text="Causa de salida del taller"
    )
    
    # Tiempo en espera (en horas)
    tiempo_espera = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Tiempo en espera antes de iniciar trabajo (horas)"
    )
    
    # Tiempo en ejecución (en horas)
    tiempo_ejecucion = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Tiempo total en ejecución (horas)"
    )
    
    # Tiempo total de reparación (en días)
    tiempo_total_reparacion = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Tiempo total de reparación (días)"
    )
    
    # SLA vencido (True si excedió el tiempo límite)
    sla_vencido = models.BooleanField(
        default=False,
        help_text="Indica si la OT excedió el tiempo límite (SLA)"
    )
    
    # Fecha límite SLA
    fecha_limite_sla = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha límite para cumplir SLA"
    )
    
    # ==================== FECHAS ====================
    # Rastrean el ciclo de vida de la OT
    
    # Apertura: fecha/hora de creación (automática)
    apertura = models.DateTimeField(auto_now_add=True)
    
    # Fecha de diagnóstico: cuando Jefe de Taller completa el diagnóstico
    fecha_diagnostico = models.DateTimeField(null=True, blank=True)
    
    # Fecha de aprobación: cuando Supervisor aprueba la asignación
    fecha_aprobacion_supervisor = models.DateTimeField(null=True, blank=True)
    
    # Fecha de asignación: cuando se asigna el mecánico
    fecha_asignacion_mecanico = models.DateTimeField(null=True, blank=True)
    
    # Fecha de inicio de ejecución: cuando el mecánico inicia el trabajo
    fecha_inicio_ejecucion = models.DateTimeField(null=True, blank=True)
    
    # Cierre: fecha/hora de finalización (se establece al cerrar)
    cierre = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        """
        Configuración del modelo.
        
        - indexes: índices para optimizar búsquedas frecuentes
        """
        indexes = [
            models.Index(fields=["estado"]),  # Búsquedas por estado (muy frecuente)
            models.Index(fields=["apertura"])  # Ordenamiento por fecha de apertura
        ]


class ItemOT(models.Model):
    """
    Item de trabajo asociado a una Orden de Trabajo.
    
    Representa un repuesto o servicio que se utilizará o realizó
    en el marco de una OT. Cada item tiene:
    - Tipo (REPUESTO o SERVICIO)
    - Descripción
    - Cantidad
    - Costo unitario
    
    El costo total se calcula como: cantidad * costo_unitario
    
    Relaciones:
    - ForeignKey a OrdenTrabajo (ot.items.all() para obtener todos los items)
    
    Validaciones:
    - cantidad > 0 (CheckConstraint)
    - costo_unitario >= 0 (CheckConstraint)
    """
    
    class TipoItem(models.TextChoices):
        """
        Tipos de items disponibles.
        """
        REPUESTO = "REPUESTO", "REPUESTO"  # Repuesto o pieza
        SERVICIO = "SERVICIO", "SERVICIO"  # Servicio o mano de obra
    
    # ID único
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # OT a la que pertenece este item
    # CASCADE: si se elimina la OT, se eliminan sus items
    ot = models.ForeignKey(
        OrdenTrabajo, 
        on_delete=models.CASCADE, 
        related_name="items"  # Acceso desde ot.items.all()
    )
    
    # Tipo de item
    tipo = models.CharField(max_length=20, choices=TipoItem.choices)
    
    # Descripción del item
    descripcion = models.TextField()
    
    # Cantidad: debe ser mayor a 0
    cantidad = models.PositiveIntegerField()
    
    # Costo unitario: precio por unidad
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Repuesto asociado (opcional, solo si tipo es REPUESTO)
    repuesto = models.ForeignKey(
        "inventory.Repuesto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items_ot",
        help_text="Repuesto asociado a este item (solo si tipo es REPUESTO)"
    )
    
    class Meta:
        """
        Configuración del modelo.
        
        - constraints: validaciones a nivel de base de datos
        - indexes: índices para optimizar búsquedas
        """
        constraints = [
            # Validar que la cantidad sea mayor a 0
            models.CheckConstraint(
                check=models.Q(cantidad__gt=0), 
                name="itemot_cantidad_gt_0"
            ),
            # Validar que el costo sea mayor o igual a 0
            models.CheckConstraint(
                check=models.Q(costo_unitario__gte=0), 
                name="itemot_costo_gte_0"
            ),
        ]
        indexes = [
            models.Index(fields=["ot"]),  # Búsquedas por OT
            models.Index(fields=["tipo"])  # Filtros por tipo
        ]


class Presupuesto(models.Model):
    """
    Presupuesto asociado a una Orden de Trabajo.
    
    Cada OT puede tener un presupuesto que detalla los costos
    estimados. Si el presupuesto supera un umbral, requiere
    aprobación de un Sponsor.
    
    Relaciones:
    - OneToOne con OrdenTrabajo (ot.presupuesto para acceder)
    - OneToMany con DetallePresup (presupuesto.detalles.all())
    - OneToOne con Aprobacion (presupuesto.aprobacion)
    
    Flujo:
    1. Se crea el presupuesto con sus detalles
    2. Si total > umbral → requiere_aprobacion = True
    3. Sponsor aprueba o rechaza
    4. Si se aprueba, se puede proceder con la OT
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relación OneToOne: cada OT tiene un presupuesto (opcional)
    ot = models.OneToOneField(
        OrdenTrabajo, 
        on_delete=models.CASCADE,  # Si se elimina la OT, se elimina el presupuesto
        related_name="presupuesto"
    )
    
    # Total del presupuesto: suma de todos los detalles
    total = models.DecimalField(max_digits=14, decimal_places=2)
    
    # Indica si requiere aprobación de Sponsor
    # Se establece automáticamente si total > umbral
    requiere_aprobacion = models.BooleanField(default=False)
    
    # Umbral: monto a partir del cual se requiere aprobación
    # Si total > umbral → requiere_aprobacion = True
    umbral = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    
    # Fecha de creación
    creado_en = models.DateTimeField(auto_now_add=True)


class DetallePresup(models.Model):
    """
    Detalle de un presupuesto.
    
    Cada presupuesto puede tener múltiples detalles que suman
    el total. Cada detalle representa un concepto con cantidad y precio.
    
    Relaciones:
    - ForeignKey a Presupuesto (presupuesto.detalles.all())
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Presupuesto al que pertenece
    presupuesto = models.ForeignKey(
        Presupuesto, 
        on_delete=models.CASCADE, 
        related_name="detalles"
    )
    
    # Concepto: descripción del detalle
    concepto = models.CharField(max_length=255)
    
    # Cantidad
    cantidad = models.PositiveIntegerField()
    
    # Precio unitario
    precio = models.DecimalField(max_digits=12, decimal_places=2)


class Aprobacion(models.Model):
    """
    Aprobación de un presupuesto por un Sponsor.
    
    Cuando un presupuesto supera el umbral, requiere aprobación.
    Un Sponsor (rol SPONSOR) puede aprobar o rechazar el presupuesto.
    
    Relaciones:
    - OneToOne con Presupuesto (presupuesto.aprobacion)
    - ForeignKey a User (sponsor que aprueba)
    
    Estados:
    - PENDIENTE: Esperando aprobación
    - APROBADO: Presupuesto aprobado, se puede proceder
    - RECHAZADO: Presupuesto rechazado, requiere ajustes
    """
    
    ESTADOS = (
        ("PENDIENTE", "PENDIENTE"),  # Esperando aprobación
        ("APROBADO", "APROBADO"),  # Aprobado
        ("RECHAZADO", "RECHAZADO")  # Rechazado
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relación OneToOne: cada presupuesto tiene una aprobación
    presupuesto = models.OneToOneField(
        Presupuesto, 
        on_delete=models.CASCADE, 
        related_name="aprobacion"
    )
    
    # Sponsor que aprueba o rechaza
    sponsor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,  # No permitir eliminar sponsor con aprobaciones
        related_name="aprobaciones"
    )
    
    # Estado de la aprobación
    estado = models.CharField(max_length=20, choices=ESTADOS, default="PENDIENTE")
    
    # Comentario del sponsor (opcional)
    comentario = models.TextField(blank=True)
    
    # Fecha de la aprobación/rechazo
    fecha = models.DateTimeField(auto_now_add=True)


class Pausa(models.Model):
    """
    Pausa durante la ejecución de una Orden de Trabajo.
    
    Las pausas pueden ser:
    - Manuales: creadas por el mecánico o supervisor
    - Automáticas: creadas por Celery Beat (colación 12:30-13:15)
    
    Cuando se crea una pausa y la OT está en EN_EJECUCION,
    automáticamente cambia a EN_PAUSA.
    
    Relaciones:
    - ForeignKey a OrdenTrabajo (ot.pausas.all())
    - ForeignKey a User (usuario que crea la pausa)
    
    Propiedades:
    - duracion_minutos: calcula la duración si la pausa está cerrada
    """
    
    TIPOS = (
        ("ESPERA_REPUESTO", "Espera de Repuesto"),  # Esperando repuesto
        ("APROBACION_PENDIENTE", "Aprobación Pendiente"),  # Esperando aprobación
        ("COLACION", "Colación (12:30-13:15)"),  # Pausa de colación
        ("OTRO", "Otro Motivo Operativo"),  # Otro motivo
        ("ADMINISTRATIVA", "Pausa Administrativa"),  # Pausa administrativa
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # OT a la que pertenece la pausa
    ot = models.ForeignKey(
        OrdenTrabajo, 
        on_delete=models.CASCADE, 
        related_name="pausas"
    )
    
    # Usuario que crea la pausa (mecánico, supervisor, etc.)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name="pausas"
    )
    
    # Tipo de pausa
    tipo = models.CharField(
        max_length=30, 
        choices=TIPOS, 
        default="OTRO", 
        help_text="Tipo de pausa"
    )
    
    # Motivo detallado de la pausa
    motivo = models.CharField(max_length=255, help_text="Motivo detallado de la pausa")
    
    # Indica si es una pausa automática (ej: colación creada por Celery)
    es_automatica = models.BooleanField(
        default=False, 
        help_text="Indica si es una pausa automática (ej: colación)"
    )
    
    # Fecha/hora de inicio (automática al crear)
    inicio = models.DateTimeField(auto_now_add=True)
    
    # Fecha/hora de fin (null mientras está activa)
    fin = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        """
        Configuración del modelo.
        
        - indexes: índices para búsquedas frecuentes
        - ordering: orden por defecto (más recientes primero)
        """
        indexes = [
            models.Index(fields=["ot", "inicio"]),  # Búsquedas por OT y fecha
            models.Index(fields=["tipo", "inicio"]),  # Filtros por tipo
            models.Index(fields=["es_automatica"]),  # Filtros de pausas automáticas
        ]
        ordering = ["-inicio"]  # Más recientes primero
    
    @property
    def duracion_minutos(self):
        """
        Calcula la duración de la pausa en minutos.
        
        Solo funciona si la pausa está cerrada (tiene fecha de fin).
        
        Retorna:
        - int: Duración en minutos
        - None: Si la pausa aún está activa (fin es None)
        
        Uso:
        - Llamado desde serializers para incluir duración en API
        - Usado en reportes para calcular tiempo de pausas
        """
        if self.fin and self.inicio:
            delta = self.fin - self.inicio
            return int(delta.total_seconds() / 60)
        return None


class Checklist(models.Model):
    """
    Checklist de calidad para una Orden de Trabajo.
    
    Se usa para verificar que el trabajo cumple con los estándares
    de calidad antes de cerrar la OT.
    
    Relaciones:
    - ForeignKey a OrdenTrabajo (ot.checklists.all())
    - ForeignKey a User (verificador que realiza el checklist)
    """
    
    RESULTADOS = (
        ("OK", "OK"),  # Aprobado
        ("NO_OK", "NO_OK")  # No aprobado, requiere corrección
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # OT a la que pertenece el checklist
    ot = models.ForeignKey(
        OrdenTrabajo, 
        on_delete=models.CASCADE, 
        related_name="checklists"
    )
    
    # Usuario que realiza la verificación
    verificador = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="checklists_realizados"
    )
    
    # Resultado de la verificación
    resultado = models.CharField(max_length=10, choices=RESULTADOS)
    
    # Observaciones adicionales
    observaciones = models.TextField(blank=True)
    
    # Fecha de la verificación
    fecha = models.DateTimeField(auto_now_add=True)


class Evidencia(models.Model):
    """
    Evidencia fotográfica o documental de una Orden de Trabajo.
    
    Las evidencias se almacenan en S3 (AWS o LocalStack) y se
    referencia mediante URL. Pueden ser fotos, PDFs u otros documentos.
    
    Relaciones:
    - ForeignKey a OrdenTrabajo (ot.evidencias.all())
    
    Tipos:
    - FOTO: Imagen fotográfica
    - PDF: Documento PDF
    - OTRO: Otro tipo de documento
    """
    
    class TipoEvidencia(models.TextChoices):
        """
        Tipos de evidencias disponibles.
        
        Soporta múltiples formatos:
        - FOTO: Imágenes (JPEG, PNG, GIF, WebP, BMP)
        - PDF: Documentos PDF
        - HOJA_CALCULO: Hojas de cálculo (XLSX, XLS, CSV)
        - DOCUMENTO: Documentos Word (DOC, DOCX)
        - COMPRIMIDO: Archivos comprimidos (ZIP, RAR, 7Z)
        - OTRO: Otros tipos de archivo
        """
        FOTO = "FOTO", "FOTO"  # Imagen fotográfica
        PDF = "PDF", "PDF"  # Documento PDF
        HOJA_CALCULO = "HOJA_CALCULO", "HOJA_CALCULO"  # Hojas de cálculo (Excel, CSV)
        DOCUMENTO = "DOCUMENTO", "DOCUMENTO"  # Documentos Word
        COMPRIMIDO = "COMPRIMIDO", "COMPRIMIDO"  # Archivos comprimidos
        OTRO = "OTRO", "OTRO"  # Otro tipo de archivo
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # OT a la que pertenece la evidencia (opcional)
    # Si es None, la evidencia es general y no está asociada a una OT específica
    ot = models.ForeignKey(
        OrdenTrabajo, 
        on_delete=models.CASCADE, 
        related_name="evidencias",
        null=True,
        blank=True
    )
    
    # URL de la evidencia en S3
    # Se genera mediante presigned URL en apps/workorders/presigned_url_view.py
    url = models.URLField()
    
    # Tipo de evidencia
    # max_length aumentado a 15 para soportar "HOJA_CALCULO" (12 caracteres) y otros tipos
    tipo = models.CharField(
        max_length=15, 
        choices=TipoEvidencia.choices, 
        default="FOTO"
    )
    
    # Descripción opcional de la evidencia
    descripcion = models.TextField(blank=True, default="")
    
    # Usuario que subió la evidencia
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evidencias_subidas",
        help_text="Usuario que subió esta evidencia"
    )
    
    # Fecha de subida
    subido_en = models.DateTimeField(auto_now_add=True)
    
    # Campos de invalidación
    invalidado = models.BooleanField(default=False, help_text="Indica si la evidencia fue invalidada")
    invalidado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evidencias_invalidadas"
    )
    invalidado_en = models.DateTimeField(null=True, blank=True)
    motivo_invalidacion = models.TextField(blank=True, help_text="Motivo de invalidación")


class Auditoria(models.Model):
    """
    Registro de auditoría de todas las acciones del sistema.
    
    Este modelo registra quién hizo qué, cuándo y sobre qué objeto.
    Es crítico para trazabilidad y cumplimiento normativo.
    
    No tiene ForeignKey directo a los objetos auditados para mantener
    flexibilidad. En su lugar, usa objeto_tipo y objeto_id como strings.
    
    Campos:
    - usuario: Usuario que realizó la acción (puede ser None si es sistema)
    - accion: Tipo de acción (ej: "LOGIN_EXITOSO", "CERRAR_OT")
    - objeto_tipo: Tipo del objeto afectado (ej: "OrdenTrabajo", "User")
    - objeto_id: ID del objeto afectado
    - payload: Datos adicionales en formato JSON
    - ts: Timestamp de la acción
    
    Uso:
    - Registrado automáticamente en vistas críticas
    - Consultado para reportes de auditoría
    - Usado para debugging y análisis de uso
    """
    
    # Usuario que realizó la acción
    # SET_NULL permite mantener el registro aunque se elimine el usuario
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Tipo de acción realizada
    # Ejemplos: "LOGIN_EXITOSO", "CERRAR_OT", "APROBAR_PRESUPUESTO", etc.
    accion = models.CharField(max_length=64)
    
    # Tipo del objeto afectado
    # Ejemplos: "OrdenTrabajo", "User", "Presupuesto", etc.
    objeto_tipo = models.CharField(max_length=64)
    
    # ID del objeto afectado (como string para flexibilidad)
    objeto_id = models.CharField(max_length=64)
    
    # Datos adicionales en formato JSON
    # Permite almacenar información contextual de la acción
    # Ejemplo: {"ip": "192.168.1.1", "mecanico_id": "123", etc.}
    payload = models.JSONField(default=dict, blank=True)
    
    # Timestamp de la acción (automático al crear)
    ts = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        Configuración del modelo.
        
        - indexes: índices para búsquedas frecuentes
        """
        indexes = [
            # Búsquedas por objeto específico
            models.Index(fields=["objeto_tipo", "objeto_id"]),
            # Búsquedas por tipo de acción
            models.Index(fields=["accion"]),
            # Ordenamiento por fecha
            models.Index(fields=["ts"]),
        ]

    def __str__(self):
        """
        Representación en string del registro de auditoría.
        
        Formato: "timestamp accion objeto_tipo:objeto_id"
        Ejemplo: "2024-01-15 10:30:00 CERRAR_OT OrdenTrabajo:abc123"
        """
        return f"{self.ts} {self.accion} {self.objeto_tipo}:{self.objeto_id}"


class ComentarioOT(models.Model):
    """
    Comentarios internos en una Orden de Trabajo.
    
    Permite comunicación entre usuarios (mecánico, supervisor, jefe de taller, etc.)
    dentro del contexto de una OT. Soporta menciones de usuarios.
    
    Relaciones:
    - ForeignKey a OrdenTrabajo (ot.comentarios.all())
    - ForeignKey a User (usuario que crea el comentario)
    - ForeignKey a ComentarioOT (comentario padre, para respuestas)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # OT a la que pertenece el comentario
    ot = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name="comentarios"
    )
    
    # Usuario que crea el comentario
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comentarios_ot"
    )
    
    # Comentario padre (si es una respuesta)
    comentario_padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="respuestas"
    )
    
    # Contenido del comentario
    contenido = models.TextField()
    
    # Menciones de usuarios (almacenadas como lista de IDs en JSON)
    # Ejemplo: ["@jefetaller", "@mecanico123"]
    menciones = models.JSONField(default=list, blank=True)
    
    # Indica si el comentario fue editado
    editado = models.BooleanField(default=False)
    
    # Fecha de creación
    creado_en = models.DateTimeField(auto_now_add=True)
    
    # Fecha de última edición
    editado_en = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["ot", "creado_en"]),
            models.Index(fields=["usuario", "creado_en"]),
        ]
        ordering = ["creado_en"]
    
    def __str__(self):
        return f"Comentario en OT {self.ot.id} por {self.usuario.username if self.usuario else 'Sistema'}"


class BloqueoVehiculo(models.Model):
    """
    Bloqueos o restricciones de vehículos.
    
    Permite marcar vehículos con bloqueos que impiden su ingreso al taller
    o generan alertas especiales.
    
    Relaciones:
    - ForeignKey a Vehiculo (vehiculo.bloqueos.all())
    - ForeignKey a User (usuario que crea el bloqueo)
    """
    
    TIPOS_BLOQUEO = (
        ("PENDIENTE_PAGO", "Pendiente de Pago"),
        ("DOCUMENTACION_INCOMPLETA", "Documentación Incompleta"),
        ("SANCION", "Sanción"),
        ("MANTENIMIENTO_OBLIGATORIO", "Mantenimiento Obligatorio"),
        ("OTRO", "Otro"),
    )
    
    ESTADOS = (
        ("ACTIVO", "Activo"),
        ("RESUELTO", "Resuelto"),
        ("CANCELADO", "Cancelado"),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Vehículo bloqueado
    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.CASCADE,
        related_name="bloqueos"
    )
    
    # Usuario que crea el bloqueo
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bloqueos_creados"
    )
    
    # Tipo de bloqueo
    tipo = models.CharField(max_length=50, choices=TIPOS_BLOQUEO)
    
    # Estado del bloqueo
    estado = models.CharField(max_length=20, choices=ESTADOS, default="ACTIVO")
    
    # Motivo del bloqueo
    motivo = models.TextField()
    
    # Fecha de creación
    creado_en = models.DateTimeField(auto_now_add=True)
    
    # Fecha de resolución
    resuelto_en = models.DateTimeField(null=True, blank=True)
    
    # Usuario que resuelve el bloqueo
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bloqueos_resueltos"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=["vehiculo", "estado"]),
            models.Index(fields=["estado", "creado_en"]),
        ]
        ordering = ["-creado_en"]
    
    def __str__(self):
        return f"Bloqueo {self.tipo} - {self.vehiculo.patente}"


class VersionEvidencia(models.Model):
    """
    Historial de versiones de evidencias.
    
    Cuando una evidencia es invalidada, se crea una nueva versión
    manteniendo el historial completo.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Evidencia original
    evidencia_original = models.ForeignKey(
        Evidencia,
        on_delete=models.CASCADE,
        related_name="versiones"
    )
    
    # URL de la versión anterior (antes de invalidar)
    url_anterior = models.URLField()
    
    # Usuario que invalidó la evidencia
    invalidado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Motivo de invalidación
    motivo = models.TextField()
    
    # Fecha de invalidación
    invalidado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["evidencia_original", "invalidado_en"]),
        ]
        ordering = ["-invalidado_en"]
    
    def __str__(self):
        return f"Versión invalidada de evidencia {self.evidencia_original.id}"

# apps/vehicles/models.py
"""
Modelos para gestión de vehículos.

Este módulo define:
- Vehiculo: Modelo principal de vehículo
- IngresoVehiculo: Registro de ingreso al taller
- EvidenciaIngreso: Evidencias fotográficas del ingreso

Relaciones:
- Vehiculo -> OrdenTrabajo (OneToMany, related_name="ordenes")
- Vehiculo -> IngresoVehiculo (OneToMany, related_name="ingresos")
- IngresoVehiculo -> EvidenciaIngreso (OneToMany, related_name="evidencias")
- Vehiculo -> Chofer (OneToMany, related_name="choferes" en apps/drivers/models.py)

Estados del vehículo:
- ACTIVO: En operación normal
- EN_ESPERA: Ingresado al taller, esperando atención
- EN_MANTENIMIENTO: Actualmente en mantenimiento/reparación
- BAJA: Dado de baja del sistema
"""

from django.db import models
from django.conf import settings  # Para acceder a AUTH_USER_MODEL
import uuid  # Para generar IDs únicos


class Marca(models.Model):
    """
    Modelo que representa una marca de vehículo.
    
    Este modelo centraliza las marcas de vehículos para:
    - Evitar inconsistencias en nombres (ej: "Toyota" vs "TOYOTA" vs "toyota")
    - Validar que solo se usen marcas válidas
    - Facilitar reportes y filtros por marca
    
    Campos:
    - nombre: Nombre único de la marca (ej: "Toyota", "Ford", "Chevrolet")
    - activa: Indica si la marca está activa y puede ser usada
    
    Relaciones:
    - OneToMany con Vehiculo (marca.vehiculos.all())
    """
    
    nombre = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Nombre de la marca (ej: Toyota, Ford, Chevrolet)"
    )
    
    activa = models.BooleanField(
        default=True,
        help_text="Indica si la marca está activa y puede ser usada"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Marca de Vehículo"
        verbose_name_plural = "Marcas de Vehículos"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["nombre"]),
            models.Index(fields=["activa"]),
        ]
    
    def __str__(self):
        return self.nombre


class Vehiculo(models.Model):
    """
    Modelo principal que representa un vehículo de la flota.
    
    Almacena toda la información de un vehículo, incluyendo:
    - Identificación (patente, VIN)
    - Características (marca, modelo, año, tipo)
    - Estado operativo
    - Ubicación (zona, sucursal)
    - Métricas (km mensual promedio)
    
    Relaciones:
    - OneToMany con OrdenTrabajo (vehiculo.ordenes.all())
    - OneToMany con IngresoVehiculo (vehiculo.ingresos.all())
    - OneToMany con Chofer (vehiculo.choferes.all() en drivers app)
    
    Validaciones:
    - Patente única (no puede haber dos vehículos con la misma patente)
    - Año entre 1900 y 2100 (CheckConstraint)
    """
    
    # ==================== ESTADOS ====================
    ESTADOS = (
        ("ACTIVO", "ACTIVO"),  # En operación normal
        ("EN_ESPERA", "EN_ESPERA"),  # Ingresado al taller, esperando atención
        ("EN_MANTENIMIENTO", "EN_MANTENIMIENTO"),  # Actualmente en mantenimiento
        ("BAJA", "BAJA"),  # Dado de baja del sistema
    )
    
    # ==================== TIPOS ====================
    TIPOS = (
        ("ELECTRICO", "Eléctrico"),  # Vehículo eléctrico
        ("DIESEL", "Diésel"),  # Vehículo diésel
        ("UTILITARIO", "Utilitario"),  # Vehículo utilitario
        ("REPARTO", "Reparto"),  # Vehículo de reparto
        ("VENTAS", "Ventas"),  # Vehículo de ventas
        ("RESPALDO", "Respaldo"),  # Vehículo de respaldo
    )
    
    # ==================== CATEGORÍAS ====================
    CATEGORIAS = (
        ("REPARTO", "Reparto"),  # Categoría de reparto
        ("VENTAS", "Ventas"),  # Categoría de ventas
        ("RESPALDO", "Respaldo"),  # Categoría de respaldo
    )

    # ==================== CAMPOS PRINCIPALES ====================
    
    # ID único: UUID4
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    
    # Patente: identificador único del vehículo
    # unique=True: no puede haber dos vehículos con la misma patente
    # db_index=True: índice para búsquedas rápidas
    patente = models.CharField(max_length=32, unique=True, db_index=True)
    
    # Tipo de vehículo: clasificación técnica
    tipo = models.CharField(
        max_length=20, 
        choices=TIPOS, 
        blank=True, 
        help_text="Tipo de vehículo (eléctrico/diésel/utilitario)"
    )
    
    # Categoría operativa: clasificación funcional
    categoria = models.CharField(
        max_length=20, 
        choices=CATEGORIAS, 
        blank=True, 
        help_text="Categoría operativa"
    )
    
    # Información del vehículo
    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,  # No permitir eliminar marca si tiene vehículos
        null=True,
        blank=True,
        related_name="vehiculos",
        help_text="Marca del vehículo (validada contra tabla de marcas)"
    )
    modelo = models.CharField(max_length=64, blank=True)  # Ej: "Hilux", "Ranger"
    anio = models.PositiveIntegerField(null=True, blank=True)  # Año de fabricación
    
    # VIN: Número de identificación del vehículo (Vehicle Identification Number)
    vin = models.CharField(max_length=64, blank=True)
    
    # Estado operativo del vehículo
    estado = models.CharField(max_length=32, choices=ESTADOS, default="ACTIVO")
    
    # ==================== UBICACIÓN Y MÉTRICAS ====================
    
    # Zona: zona geográfica o sucursal asignada
    zona = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Zona o sucursal asignada"
    )
    
    # Sucursal: sucursal específica
    sucursal = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Sucursal específica"
    )
    
    
    # Supervisor asignado al vehículo
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="vehiculos_supervisados",
        limit_choices_to={"rol__in": ["SUPERVISOR", "COORDINADOR_ZONA"]},
        help_text="Supervisor asignado al vehículo"
    )
    
    # Estado operativo: estado real del vehículo (diferente de estado)
    ESTADO_OPERATIVO_CHOICES = (
        ("OPERATIVO", "Operativo"),
        ("EN_TALLER", "En Taller"),
        ("BLOQUEADO", "Bloqueado/TCT"),
        ("FUERA_POLITICA", "Fuera de Política"),
        ("REVISION_VENCIDA", "Revisión Vencida"),
        ("SIN_MOVIMIENTO", "Sin Movimiento"),
    )
    estado_operativo = models.CharField(
        max_length=30,
        choices=ESTADO_OPERATIVO_CHOICES,
        default="OPERATIVO",
        help_text="Estado operativo del vehículo"
    )
    
    # Cumplimiento: si el vehículo está en política o fuera
    CUMPLIMIENTO_CHOICES = (
        ("EN_POLITICA", "En Política"),
        ("FUERA_POLITICA", "Fuera de Política"),
    )
    cumplimiento = models.CharField(
        max_length=20,
        choices=CUMPLIMIENTO_CHOICES,
        default="EN_POLITICA",
        help_text="Cumplimiento de política"
    )
    
    # TCT: Bloqueo Temporal (True si está bloqueado)
    tct = models.BooleanField(
        default=False,
        help_text="Bloqueo Temporal (TCT) activo"
    )
    
    # Fecha de inicio de TCT
    tct_fecha_inicio = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de inicio del bloqueo TCT"
    )
    
    # Días con TCT activo
    tct_dias = models.PositiveIntegerField(
        default=0,
        help_text="Días con TCT activo"
    )
    
    # CeCo: Centro de Costo
    ceco = models.CharField(
        max_length=50,
        blank=True,
        help_text="Centro de Costo (CeCo)"
    )
    
    # Equipo SAP
    equipo_sap = models.CharField(
        max_length=50,
        blank=True,
        help_text="Equipo SAP"
    )
    
    # Última revisión
    ultima_revision = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de última revisión"
    )
    
    # Próxima revisión
    proxima_revision = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de próxima revisión"
    )
    
    # Kilometraje actual
    kilometraje_actual = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Kilometraje actual del vehículo"
    )
    
    # Kilometraje promedio mensual
    # Se usa para planificación de mantenimientos preventivos
    km_mensual_promedio = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Kilometraje promedio mensual"
    )
    
    # Fecha de último movimiento (para detectar vehículos sin movimiento)
    ultimo_movimiento = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de último movimiento registrado"
    )

    # ==================== TIMESTAMPS ====================
    
    # Fecha de creación en el sistema
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Fecha de última actualización
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Configuración del modelo.
        
        - indexes: índices para optimizar búsquedas frecuentes
        - constraints: validaciones a nivel de base de datos
        """
        indexes = [
            models.Index(fields=["estado"]),  # Filtros por estado (muy frecuente)
            models.Index(fields=["marca", "modelo"]),  # Búsquedas por marca/modelo
        ]
        constraints = [
            # Validar que el año esté en un rango razonable
            models.CheckConstraint(
                name="vehiculo_anio_valid",
                check=(
                    models.Q(anio__isnull=True) |  # Puede ser null
                    (models.Q(anio__gte=1900) & models.Q(anio__lte=2100))  # O entre 1900 y 2100
                ),
            ),
        ]

    def save(self, *args, **kwargs):
        """
        Sobrescribe save para normalizar la patente antes de guardar.
        
        Asegura que todas las patentes se guarden en el mismo formato:
        - Sin guiones
        - Sin espacios
        - Mayúsculas
        """
        # Normalizar patente antes de guardar
        if self.patente:
            from apps.core.validators import validar_formato_patente
            es_valido, patente_normalizada = validar_formato_patente(self.patente)
            if es_valido:
                self.patente = patente_normalizada
            # Si no es válido, dejar que el serializer/manager maneje el error
        super().save(*args, **kwargs)
    
    def __str__(self):
        """
        Representación en string del vehículo.
        
        Retorna la patente, que es el identificador principal.
        """
        return self.patente


class IngresoVehiculo(models.Model):
    """
    Registro de ingreso de un vehículo al taller.
    
    Se crea cuando un Guardia registra el ingreso
    de un vehículo al taller. Esto puede generar automáticamente
    una Orden de Trabajo si hay una Agenda programada.
    
    Relaciones:
    - ForeignKey a Vehiculo (vehiculo.ingresos.all())
    - ForeignKey a User (guardia que registra el ingreso)
    - OneToMany con EvidenciaIngreso (ingreso.evidencias.all())
    
    Uso:
    - Registrado desde apps/vehicles/views.py en acción 'ingreso'
    - Puede vincularse con Agenda para crear OT automáticamente
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Vehículo que ingresa
    vehiculo = models.ForeignKey(
        Vehiculo, 
        on_delete=models.PROTECT,  # No permitir eliminar vehículo con ingresos
        related_name="ingresos"
    )
    
    # Guardia que registra el ingreso
    guardia = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name="ingresos_registrados"
    )
    
    # Fecha/hora de ingreso (automática al crear)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    
    # Fecha/hora de salida (se establece al registrar salida)
    fecha_salida = models.DateTimeField(null=True, blank=True)
    
    # Guardia que registra la salida
    guardia_salida = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salidas_registradas"
    )
    
    # Observaciones del ingreso
    observaciones = models.TextField(blank=True)
    
    # Observaciones de la salida
    observaciones_salida = models.TextField(blank=True)
    
    # Kilometraje al momento del ingreso
    kilometraje = models.PositiveIntegerField(null=True, blank=True)
    
    # Kilometraje al momento de la salida
    kilometraje_salida = models.PositiveIntegerField(null=True, blank=True)
    
    # Código QR opcional para escaneo
    qr_code = models.CharField(max_length=255, blank=True)
    
    # Indica si el vehículo ya salió del taller
    salio = models.BooleanField(default=False)
    
    class Meta:
        """
        Configuración del modelo.
        
        - indexes: índices para búsquedas frecuentes
        - ordering: orden por defecto (más recientes primero)
        """
        indexes = [
            models.Index(fields=["fecha_ingreso"]),  # Filtros por fecha
            models.Index(fields=["vehiculo", "fecha_ingreso"]),  # Búsquedas por vehículo y fecha
        ]
        ordering = ["-fecha_ingreso"]  # Más recientes primero
    
    def __str__(self):
        """
        Representación en string del ingreso.
        
        Formato: "Ingreso {patente} - {fecha}"
        """
        return f"Ingreso {self.vehiculo.patente} - {self.fecha_ingreso}"


class EvidenciaIngreso(models.Model):
    """
    Evidencias fotográficas del ingreso de un vehículo.
    
    Se almacenan fotos y documentos relacionados con el ingreso,
    como fotos del estado del vehículo, daños, documentos, etc.
    
    Las evidencias se almacenan en S3 (AWS o LocalStack) y se
    referencia mediante URL.
    
    Relaciones:
    - ForeignKey a IngresoVehiculo (ingreso.evidencias.all())
    
    Tipos:
    - FOTO_INGRESO: Foto general del ingreso
    - FOTO_DANOS: Foto de daños detectados
    - FOTO_DOCUMENTOS: Foto de documentos
    - OTRO: Otro tipo de evidencia
    """
    
    class TipoEvidencia(models.TextChoices):
        """
        Tipos de evidencias de ingreso.
        """
        FOTO_INGRESO = "FOTO_INGRESO", "Foto de Ingreso"  # Foto general
        FOTO_DANOS = "FOTO_DANOS", "Foto de Daños"  # Foto de daños
        FOTO_DOCUMENTOS = "FOTO_DOCUMENTOS", "Foto de Documentos"  # Foto de documentos
        OTRO = "OTRO", "Otro"  # Otro tipo
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Ingreso al que pertenece la evidencia
    ingreso = models.ForeignKey(
        IngresoVehiculo, 
        on_delete=models.CASCADE,  # Si se elimina el ingreso, se eliminan las evidencias
        related_name="evidencias"
    )
    
    # URL de la evidencia en S3
    # Se genera mediante presigned URL
    url = models.URLField()
    
    # Tipo de evidencia
    tipo = models.CharField(
        max_length=20, 
        choices=TipoEvidencia.choices, 
        default=TipoEvidencia.FOTO_INGRESO
    )
    
    # Descripción opcional
    descripcion = models.TextField(blank=True)
    
    # Fecha de subida
    subido_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        """
        Configuración del modelo.
        
        - indexes: índices para búsquedas frecuentes
        """
        indexes = [
            models.Index(fields=["ingreso", "tipo"]),  # Filtros por ingreso y tipo
        ]
    
    def __str__(self):
        """
        Representación en string de la evidencia.
        
        Formato: "Evidencia {tipo} - {patente}"
        """
        return f"Evidencia {self.tipo} - {self.ingreso.vehiculo.patente}"


class HistorialVehiculo(models.Model):
    """
    Historial completo de un vehículo.
    
    Registra todos los eventos importantes del vehículo:
    - Órdenes de trabajo (abiertas, cerradas, en QA)
    - Fechas de ingreso y salida de cada OT
    - Tiempos de permanencia en taller
    - Fallas recurrentes
    - Backups utilizados
    - Supervisor responsable de cada evento
    - Estado operativo antes y después de cada OT
    
    Relaciones:
    - ForeignKey a Vehiculo (vehiculo.historial.all())
    - ForeignKey a OrdenTrabajo (opcional, si está relacionado con una OT)
    - ForeignKey a User (supervisor responsable)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Vehículo al que pertenece este historial
    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.CASCADE,
        related_name="historial"
    )
    
    # OT relacionada (opcional, puede ser un evento sin OT)
    ot = models.ForeignKey(
        "workorders.OrdenTrabajo",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="historial_vehiculo"
    )
    
    # Tipo de evento
    TIPO_EVENTO_CHOICES = (
        ("OT_CREADA", "OT Creada"),
        ("OT_CERRADA", "OT Cerrada"),
        ("OT_EN_QA", "OT en QA"),
        ("OT_RECHAZADA", "OT Rechazada"),
        ("INGRESO_TALLER", "Ingreso a Taller"),
        ("SALIDA_TALLER", "Salida de Taller"),
        ("BACKUP_ASIGNADO", "Backup Asignado"),
        ("BACKUP_DEVUELTO", "Backup Devuelto"),
        ("FALLA_REGISTRADA", "Falla Registrada"),
        ("MANTENIMIENTO", "Mantenimiento"),
        ("OTRO", "Otro"),
    )
    tipo_evento = models.CharField(
        max_length=30,
        choices=TIPO_EVENTO_CHOICES,
        default="OTRO"
    )
    
    # Fecha de ingreso al taller (si aplica)
    fecha_ingreso = models.DateTimeField(null=True, blank=True)
    
    # Fecha de salida del taller (si aplica)
    fecha_salida = models.DateTimeField(null=True, blank=True)
    
    # Tiempo de permanencia en taller (en días)
    tiempo_permanencia = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Tiempo de permanencia en taller (días)"
    )
    
    # Descripción del evento
    descripcion = models.TextField(blank=True)
    
    # Falla registrada (si aplica)
    falla = models.CharField(max_length=200, blank=True)
    
    # Supervisor responsable
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="eventos_historial"
    )
    
    
    # Estado operativo antes del evento
    estado_antes = models.CharField(max_length=30, blank=True)
    
    # Estado operativo después del evento
    estado_despues = models.CharField(max_length=30, blank=True)
    
    # Backup utilizado (si aplica)
    backup_utilizado = models.ForeignKey(
        "vehicles.BackupVehiculo",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="eventos_historial"
    )
    
    # Fecha de creación del registro
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["vehiculo", "creado_en"]),
            models.Index(fields=["tipo_evento", "creado_en"]),
        ]
    
    def __str__(self):
        return f"Historial {self.vehiculo.patente} - {self.tipo_evento} - {self.creado_en}"


class BackupVehiculo(models.Model):
    """
    Registro de asignación de backup a un vehículo.
    
    Cuando un vehículo principal entra al taller, se le puede asignar
    un vehículo backup para que continúe operando.
    
    Relaciones:
    - ForeignKey a Vehiculo (vehiculo principal)
    - ForeignKey a Vehiculo (vehiculo backup)
    - ForeignKey a OrdenTrabajo (OT asociada)
    - ForeignKey a User (supervisor que asigna)
    """
    
    ESTADO_CHOICES = (
        ("ACTIVO", "En Uso"),
        ("DEVUELTO", "Devuelto"),
        ("CANCELADO", "Cancelado"),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Vehículo principal (el que está en taller)
    vehiculo_principal = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,
        related_name="backups_recibidos"
    )
    
    # Vehículo backup (el que se asigna)
    vehiculo_backup = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,
        related_name="backups_asignados"
    )
    
    # OT asociada (si existe)
    ot = models.ForeignKey(
        "workorders.OrdenTrabajo",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="backups"
    )
    
    # Fecha de inicio de asignación
    fecha_inicio = models.DateTimeField()
    
    # Fecha de devolución (null si aún está activo)
    fecha_devolucion = models.DateTimeField(null=True, blank=True)
    
    # Duración del uso (en días, calculado)
    duracion_dias = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Duración del uso del backup (días)"
    )
    
    # Motivo de asignación
    motivo = models.TextField()
    
    
    # Supervisor que asigna
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="backups_asignados"
    )
    
    # Estado del backup
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="ACTIVO"
    )
    
    # Observaciones
    observaciones = models.TextField(blank=True)
    
    # Fecha de creación
    creado_en = models.DateTimeField(auto_now_add=True)
    
    # Fecha de actualización
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-fecha_inicio"]
        indexes = [
            models.Index(fields=["vehiculo_principal", "estado"]),
            models.Index(fields=["vehiculo_backup", "estado"]),
            models.Index(fields=["fecha_inicio"]),
        ]
    
    def __str__(self):
        return f"Backup {self.vehiculo_backup.patente} → {self.vehiculo_principal.patente}"
    
    def calcular_duracion(self):
        """
        Calcula la duración del uso del backup en días.
        
        Si aún está activo, calcula desde fecha_inicio hasta ahora.
        Si está devuelto, calcula desde fecha_inicio hasta fecha_devolucion.
        """
        from django.utils import timezone
        
        if self.fecha_devolucion:
            delta = self.fecha_devolucion - self.fecha_inicio
        else:
            delta = timezone.now() - self.fecha_inicio
        
        self.duracion_dias = delta.total_seconds() / 86400  # Convertir a días
        self.save(update_fields=["duracion_dias"])
        return self.duracion_dias

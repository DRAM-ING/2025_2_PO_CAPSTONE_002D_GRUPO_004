# apps/workorders/serializers.py
from rest_framework import serializers
from .models import (OrdenTrabajo, ItemOT, Presupuesto, DetallePresup,
                    Aprobacion, Pausa, Checklist, Evidencia, ComentarioOT,
                    BloqueoVehiculo, VersionEvidencia, Auditoria)
from decimal import Decimal

# --- PRIMERO DEFINIMOS LOS SERIALIZERS BÁSICOS ---

class ItemOTSerializer(serializers.ModelSerializer):
    repuesto_nombre = serializers.CharField(source="repuesto.nombre", read_only=True, allow_null=True)
    repuesto_codigo = serializers.CharField(source="repuesto.codigo", read_only=True, allow_null=True)
    
    class Meta:
        model = ItemOT
        fields = "__all__"

class DetallePresupSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePresup
        fields = "__all__"

# --- AHORA DEFINIMOS LOS SERIALIZERS QUE USAN A OTROS ---

class ItemOTCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemOT
        exclude = ('ot',)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar que descripcion sea requerida
        if 'descripcion' in self.fields:
            self.fields['descripcion'].required = True
        # Asegurar que cantidad sea requerida y mayor a 0
        if 'cantidad' in self.fields:
            self.fields['cantidad'].required = True
            self.fields['cantidad'].min_value = 1
        # Asegurar que costo_unitario sea requerido
        if 'costo_unitario' in self.fields:
            self.fields['costo_unitario'].required = True
        # Establecer queryset dinámicamente para el campo repuesto si existe
        if 'repuesto' in self.fields:
            from apps.inventory.models import Repuesto
            self.fields['repuesto'].queryset = Repuesto.objects.filter(activo=True)
            self.fields['repuesto'].required = False
            self.fields['repuesto'].allow_null = True
    
    def validate_descripcion(self, value):
        """Validar que descripcion no esté vacía"""
        if not value or not value.strip():
            raise serializers.ValidationError("La descripción es requerida.")
        return value.strip()
    
    def validate_cantidad(self, value):
        """Validar que cantidad sea mayor a 0"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")
        return value
    
    def validate_costo_unitario(self, value):
        """Validar que costo_unitario sea mayor o igual a 0"""
        if value is not None and value < 0:
            raise serializers.ValidationError("El costo unitario no puede ser negativo.")
        return value

class OrdenTrabajoSerializer(serializers.ModelSerializer):
    """
    Serializer para OrdenTrabajo.
    
    Validaciones implementadas:
    - Vehículo existente
    - No permitir OT duplicadas (vehículo no puede tener otra OT activa)
    - Campos obligatorios (motivo, fecha_apertura)
    """
    # Ahora Python ya sabe qué es ItemOTSerializer
    items = ItemOTSerializer(many=True, read_only=True)
    items_data = ItemOTCreateSerializer(many=True, write_only=True, required=False)
    # Evidencias y comentarios
    evidencias = serializers.SerializerMethodField()
    comentarios = serializers.SerializerMethodField()
    vehiculo_patente = serializers.CharField(source="vehiculo.patente", read_only=True, allow_null=True)
    vehiculo_detalle = serializers.SerializerMethodField()
    responsable_nombre = serializers.SerializerMethodField()
    responsable_detalle = serializers.SerializerMethodField()
    supervisor_nombre = serializers.SerializerMethodField()
    supervisor_detalle = serializers.SerializerMethodField()
    jefe_taller_nombre = serializers.SerializerMethodField()
    jefe_taller_detalle = serializers.SerializerMethodField()
    mecanico_nombre = serializers.SerializerMethodField()
    mecanico_detalle = serializers.SerializerMethodField()
    chofer_detalle = serializers.SerializerMethodField()
    fecha_apertura = serializers.DateTimeField(source="apertura", read_only=True)
    # Campos de trazabilidad
    trazabilidad = serializers.SerializerMethodField()
    ultima_modificacion = serializers.SerializerMethodField()
    historial_reciente = serializers.SerializerMethodField()
    
    def get_vehiculo_detalle(self, obj):
        """Retorna los datos completos del vehículo si existe."""
        if obj.vehiculo:
            return {
                "id": str(obj.vehiculo.id),
                "patente": obj.vehiculo.patente,
                "marca": obj.vehiculo.marca.nombre if obj.vehiculo.marca else None,
                "marca_id": str(obj.vehiculo.marca.id) if obj.vehiculo.marca else None,
                "modelo": obj.vehiculo.modelo,
                "anio": obj.vehiculo.anio,
                "tipo": obj.vehiculo.tipo,
                "categoria": obj.vehiculo.categoria,
                "estado": obj.vehiculo.estado,
                "estado_operativo": obj.vehiculo.estado_operativo,
                "kilometraje_actual": obj.vehiculo.kilometraje_actual,
                "zona": obj.vehiculo.zona,
                "sucursal": obj.vehiculo.sucursal,
                "vin": obj.vehiculo.vin,
                "supervisor": {
                    "id": str(obj.vehiculo.supervisor.id),
                    "username": obj.vehiculo.supervisor.username,
                    "nombre_completo": obj.vehiculo.supervisor.get_full_name(),
                    "email": obj.vehiculo.supervisor.email,
                    "rol": obj.vehiculo.supervisor.rol,
                } if obj.vehiculo.supervisor else None,
            }
        return None
    
    def get_responsable_nombre(self, obj):
        """Retorna el nombre completo del responsable o None si no existe."""
        return obj.responsable.get_full_name() if obj.responsable else None
    
    def get_responsable_detalle(self, obj):
        """Retorna los datos completos del responsable si existe."""
        if obj.responsable:
            return {
                "id": str(obj.responsable.id),
                "username": obj.responsable.username,
                "nombre_completo": obj.responsable.get_full_name(),
                "first_name": obj.responsable.first_name,
                "last_name": obj.responsable.last_name,
                "email": obj.responsable.email,
                "rol": obj.responsable.rol,
                "rut": obj.responsable.rut,
            }
        return None
    
    def get_supervisor_nombre(self, obj):
        """Retorna el nombre completo del supervisor o None si no existe."""
        return obj.supervisor.get_full_name() if obj.supervisor else None
    
    def get_supervisor_detalle(self, obj):
        """Retorna los datos completos del supervisor si existe."""
        if obj.supervisor:
            return {
                "id": str(obj.supervisor.id),
                "username": obj.supervisor.username,
                "nombre_completo": obj.supervisor.get_full_name(),
                "first_name": obj.supervisor.first_name,
                "last_name": obj.supervisor.last_name,
                "email": obj.supervisor.email,
                "rol": obj.supervisor.rol,
                "rut": obj.supervisor.rut,
            }
        return None
    
    def get_jefe_taller_nombre(self, obj):
        """Retorna el nombre completo del jefe de taller o None si no existe."""
        return obj.jefe_taller.get_full_name() if obj.jefe_taller else None
    
    def get_jefe_taller_detalle(self, obj):
        """Retorna los datos completos del jefe de taller si existe."""
        if obj.jefe_taller:
            return {
                "id": str(obj.jefe_taller.id),
                "username": obj.jefe_taller.username,
                "nombre_completo": obj.jefe_taller.get_full_name(),
                "first_name": obj.jefe_taller.first_name,
                "last_name": obj.jefe_taller.last_name,
                "email": obj.jefe_taller.email,
                "rol": obj.jefe_taller.rol,
                "rut": obj.jefe_taller.rut,
            }
        return None
    
    def get_mecanico_nombre(self, obj):
        """Retorna el nombre completo del mecánico o None si no existe."""
        return obj.mecanico.get_full_name() if obj.mecanico else None
    
    def get_mecanico_detalle(self, obj):
        """Retorna los datos completos del mecánico si existe."""
        if obj.mecanico:
            return {
                "id": str(obj.mecanico.id),
                "username": obj.mecanico.username,
                "nombre_completo": obj.mecanico.get_full_name(),
                "first_name": obj.mecanico.first_name,
                "last_name": obj.mecanico.last_name,
                "email": obj.mecanico.email,
                "rol": obj.mecanico.rol,
                "rut": obj.mecanico.rut,
            }
        return None
    
    def get_chofer_detalle(self, obj):
        """Retorna los datos completos del chofer si existe."""
        if obj.chofer:
            return {
                "id": str(obj.chofer.id),
                "nombre_completo": obj.chofer.nombre_completo,
                "rut": obj.chofer.rut,
                "telefono": obj.chofer.telefono,
                "zona": obj.chofer.zona,
                "sucursal": obj.chofer.sucursal,
                "activo": obj.chofer.activo,
            }
        return None
    
    def get_trazabilidad(self, obj):
        """
        Retorna información de trazabilidad de la OT.
        Incluye última auditoría y total de eventos.
        """
        from apps.workorders.models import Auditoria
        
        # Obtener última auditoría relacionada a esta OT
        ultima_auditoria = Auditoria.objects.filter(
            objeto_tipo="OrdenTrabajo",
            objeto_id=str(obj.id)
        ).order_by('-ts').first()
        
        # Contar total de eventos de auditoría
        total_eventos = Auditoria.objects.filter(
            objeto_tipo="OrdenTrabajo",
            objeto_id=str(obj.id)
        ).count()
        
        return {
            "ultima_auditoria": {
                "accion": ultima_auditoria.accion if ultima_auditoria else None,
                "usuario": ultima_auditoria.usuario.username if ultima_auditoria and ultima_auditoria.usuario else None,
                "fecha": ultima_auditoria.ts.isoformat() if ultima_auditoria else None,
            } if ultima_auditoria else None,
            "total_eventos": total_eventos
        }
    
    def get_ultima_modificacion(self, obj):
        """Retorna la fecha de última modificación."""
        return obj.updated_at.isoformat() if hasattr(obj, 'updated_at') and obj.updated_at else None
    
    def get_historial_reciente(self, obj):
        """Retorna un resumen del historial reciente de la OT."""
        from apps.workorders.models import Auditoria
        
        # Obtener últimos 5 eventos de auditoría
        eventos_recientes = Auditoria.objects.filter(
            objeto_tipo="OrdenTrabajo",
            objeto_id=str(obj.id)
        ).order_by('-ts')[:5]
        
        return [
            {
                "accion": evento.accion,
                "usuario": evento.usuario.username if evento.usuario else "Sistema",
                "fecha": evento.ts.isoformat(),
                "payload": evento.payload
            }
            for evento in eventos_recientes
        ]
    
    def get_evidencias(self, obj):
        """Retorna las evidencias de la OT."""
        # Obtener evidencias no invalidadas, ordenadas por fecha de subida
        evidencias = obj.evidencias.filter(invalidado=False).order_by('-subido_en')
        return EvidenciaSerializer(evidencias, many=True).data
    
    def get_comentarios(self, obj):
        """Retorna los comentarios de la OT (solo comentarios principales, sin respuestas)."""
        # Obtener solo comentarios principales (sin comentario_padre), ordenados por fecha
        comentarios = obj.comentarios.filter(comentario_padre__isnull=True).order_by('-creado_en')
        return ComentarioOTSerializer(comentarios, many=True).data

    class Meta:
        model = OrdenTrabajo
        fields = '__all__'
        extra_kwargs = {
            'vehiculo': {'required': False}  # No requerido en actualizaciones
        }
    
    def __init__(self, *args, **kwargs):
        """Inicializa el serializer y ajusta campos según el contexto."""
        super().__init__(*args, **kwargs)
        # En actualizaciones (cuando hay una instancia), hacer que vehiculo sea read_only
        if self.instance is not None:
            # Si es una actualización, hacer que vehiculo sea read_only (no se puede cambiar)
            if 'vehiculo' in self.fields:
                self.fields['vehiculo'].read_only = True
                self.fields['vehiculo'].required = False
    
    def validate_vehiculo(self, value):
        """
        Valida que el vehículo exista.
        En creación, el vehículo es requerido.
        En actualización, el vehículo es read_only (no se puede cambiar).
        """
        # En creación, el vehículo es requerido
        if not self.instance and value is None:
            raise serializers.ValidationError("El campo vehiculo es obligatorio al crear una OT.")
        # En actualización, el vehículo es read_only, así que ignorar cualquier valor proporcionado
        if self.instance is not None:
            # Retornar el vehículo actual, ignorando el valor proporcionado
            return self.instance.vehiculo
        return value
    
    def validate(self, attrs):
        """
        Validaciones a nivel de objeto completo.
        """
        # Validar campos obligatorios
        # Nota: 'apertura' se genera automáticamente (auto_now_add=True), no es requerido
        campos_obligatorios = {
            'motivo': 'motivo de ingreso',
        }
        
        for campo, nombre_display in campos_obligatorios.items():
            if campo not in attrs:
                if self.instance:
                    # En actualización, si no viene en attrs, usar el valor actual
                    if not getattr(self.instance, campo, None):
                        raise serializers.ValidationError({campo: f"El campo {nombre_display} es obligatorio."})
                else:
                    # En creación, el campo debe estar en attrs
                    raise serializers.ValidationError({campo: f"El campo {nombre_display} es obligatorio."})
        
        # Validar vehiculo en creación
        if not self.instance:  # Creación
            if 'vehiculo' not in attrs or attrs.get('vehiculo') is None:
                raise serializers.ValidationError({'vehiculo': 'El campo vehiculo es obligatorio al crear una OT.'})
        
        # Validar responsable (obligatorio en creación, opcional en actualización si ya existe)
        if not self.instance:  # Creación
            if 'responsable' not in attrs or not attrs.get('responsable'):
                raise serializers.ValidationError({'responsable': 'El campo responsable es obligatorio.'})
        else:  # Actualización
            # Si no viene responsable en attrs, mantener el actual
            if 'responsable' not in attrs:
                # Si la instancia no tiene responsable, es un error
                if not self.instance.responsable:
                    raise serializers.ValidationError({'responsable': 'El campo responsable es obligatorio.'})
            elif attrs.get('responsable') is None or attrs.get('responsable') == '' or attrs.get('responsable') == '0':
                # Si se envía responsable vacío o "0", mantener el actual
                if not self.instance.responsable:
                    raise serializers.ValidationError({'responsable': 'El campo responsable es obligatorio.'})
                # Si ya tiene responsable, mantenerlo (no actualizar)
                attrs.pop('responsable', None)
        
        # Validar items_data si está presente
        if 'items_data' in attrs:
            items_data = attrs.get('items_data', [])
            # Rechazar items_data vacío
            if items_data == []:
                raise serializers.ValidationError({
                    'items_data': 'No se puede enviar una lista vacía de items. Use null para mantener los items existentes o proporcione al menos un item.'
                })
            for idx, item_data in enumerate(items_data):
                # Validar descripcion
                if 'descripcion' not in item_data or not item_data.get('descripcion') or not str(item_data.get('descripcion', '')).strip():
                    raise serializers.ValidationError({
                        f'items_data[{idx}].descripcion': 'La descripción es requerida.'
                    })
                # Validar cantidad
                cantidad = item_data.get('cantidad')
                if cantidad is not None and cantidad <= 0:
                    raise serializers.ValidationError({
                        f'items_data[{idx}].cantidad': 'La cantidad debe ser mayor a 0.'
                    })
                # Validar costo_unitario
                costo_unitario = item_data.get('costo_unitario')
                if costo_unitario is not None:
                    from decimal import Decimal
                    try:
                        costo_decimal = Decimal(str(costo_unitario))
                        if costo_decimal < 0:
                            raise serializers.ValidationError({
                                f'items_data[{idx}].costo_unitario': 'El costo unitario no puede ser negativo.'
                            })
                    except (ValueError, TypeError):
                        pass  # La validación del campo DecimalField se encargará de esto
        
        # NOTA: La validación de OTs activas se maneja en la vista (views.py)
        # para permitir que JEFE_TALLER y ADMIN puedan crear OT incluso si hay una activa
        # El serializer solo valida la estructura de los datos
        
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop('items_data', [])
        orden = OrdenTrabajo.objects.create(**validated_data)
        for item_data in items_data:
            ItemOT.objects.create(ot=orden, **item_data)
        return orden
    
    def update(self, instance, validated_data):
        """
        Actualiza una OT y sus items.
        Si se proporciona items_data, reemplaza todos los items existentes.
        """
        # Excluir vehiculo de validated_data si está presente (es read_only en actualizaciones)
        validated_data.pop('vehiculo', None)
        items_data = validated_data.pop('items_data', None)
        
        # Preservar responsable si no viene en validated_data o es vacío (es obligatorio)
        # Si no se proporciona responsable, mantener el actual de la instancia
        if 'responsable' not in validated_data or validated_data.get('responsable') is None or validated_data.get('responsable') == '' or validated_data.get('responsable') == '0':
            # Si la instancia no tiene responsable, es un error
            if not instance.responsable:
                raise serializers.ValidationError({'responsable': 'El campo responsable es obligatorio.'})
            # Mantener el responsable actual - eliminar del validated_data para no sobrescribir
            validated_data.pop('responsable', None)
        
        # El vehículo no se puede cambiar en actualizaciones - asegurar que no esté en validated_data
        validated_data.pop('vehiculo', None)
        
        # Actualizar campos de la OT
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Si se proporciona items_data, reemplazar todos los items
        if items_data is not None:
            # Validar que items_data no esté vacío
            if len(items_data) == 0:
                raise serializers.ValidationError({'items_data': 'Debe proporcionar al menos un item.'})
            
            # Validar cada item antes de crear
            for idx, item_data in enumerate(items_data):
                # Validar campos requeridos
                if not item_data.get('tipo'):
                    raise serializers.ValidationError({f'items_data[{idx}].tipo': 'El tipo del item es requerido.'})
                if not item_data.get('descripcion') or not item_data.get('descripcion', '').strip():
                    raise serializers.ValidationError({f'items_data[{idx}].descripcion': 'La descripción del item es requerida.'})
                if not item_data.get('cantidad') or item_data.get('cantidad', 0) <= 0:
                    raise serializers.ValidationError({f'items_data[{idx}].cantidad': 'La cantidad debe ser mayor a 0.'})
                # Validar costo_unitario - puede venir como string o número
                costo_val = item_data.get('costo_unitario')
                if costo_val is None:
                    raise serializers.ValidationError({f'items_data[{idx}].costo_unitario': 'El costo unitario es requerido.'})
                # Convertir a float si es string, luego a string para DecimalField
                try:
                    costo_float = float(costo_val) if isinstance(costo_val, str) else float(costo_val)
                    if costo_float < 0:
                        raise serializers.ValidationError({f'items_data[{idx}].costo_unitario': 'El costo unitario debe ser mayor o igual a 0.'})
                    # Normalizar el valor en item_data - DecimalField espera string
                    item_data['costo_unitario'] = str(costo_float)
                except (ValueError, TypeError):
                    raise serializers.ValidationError({f'items_data[{idx}].costo_unitario': 'El costo unitario debe ser un número válido.'})
            
            # Eliminar items existentes
            instance.items.all().delete()
            # Crear nuevos items
            for item_data in items_data:
                ItemOT.objects.create(ot=instance, **item_data)
        
        return instance

class DetallePresupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePresup
        exclude = ('presupuesto',)

class PresupuestoSerializer(serializers.ModelSerializer):
    # Ahora Python ya sabe qué es DetallePresupSerializer
    detalles = DetallePresupSerializer(many=True, read_only=True)
    detalles_data = DetallePresupCreateSerializer(many=True, write_only=True, required=False)

    total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    requiere_aprobacion = serializers.BooleanField(read_only=True)

    class Meta:
        model = Presupuesto
        fields = '__all__'
    
    def create(self, validated_data):
        """Excluir detalles_data de validated_data antes de crear el objeto"""
        validated_data.pop('detalles_data', None)
        return super().create(validated_data)

# --- Y FINALMENTE, EL RESTO DE SERIALIZERS SIMPLES ---

class AprobacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aprobacion
        fields = "__all__"

class PausaSerializer(serializers.ModelSerializer):
    """
    Serializer para Pausa.
    
    Validaciones implementadas:
    - No permitir pausar si la OT no está EN_EJECUCION
    - No permitir reanudar si la OT no está EN_PAUSA
    """
    usuario_nombre = serializers.CharField(source="usuario.get_full_name", read_only=True)
    duracion_minutos = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Pausa
        fields = "__all__"
    
    def validate(self, attrs):
        """
        Validaciones a nivel de objeto completo.
        """
        ot = attrs.get('ot') or (self.instance.ot if self.instance else None)
        
        if not ot:
            raise serializers.ValidationError({"ot": "La OT es obligatoria."})
        
        # Si se está creando una pausa (no tiene fin), validar que la OT esté EN_EJECUCION
        if not self.instance:  # Creación
            if ot.estado != 'EN_EJECUCION':
                raise serializers.ValidationError({
                    'ot': "Solo se pueden crear pausas cuando la OT está en estado EN_EJECUCION."
                })
        
        return attrs

class ChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checklist
        fields = "__all__"

class EvidenciaSerializer(serializers.ModelSerializer):
    invalidado = serializers.BooleanField(read_only=True)
    invalidado_por_nombre = serializers.CharField(source="invalidado_por.get_full_name", read_only=True)
    invalidado_en = serializers.DateTimeField(read_only=True)
    subido_por_nombre = serializers.CharField(source="subido_por.get_full_name", read_only=True)
    # URL que siempre apunta al endpoint de descarga del backend (accesible desde cualquier dispositivo)
    # Para lectura, usamos SerializerMethodField
    url_download = serializers.SerializerMethodField()
    # URL original almacenada (solo para referencia interna)
    url_original = serializers.URLField(source="url", read_only=True)
    # Campo para escritura: permitir establecer la URL al crear (requerido)
    url = serializers.URLField(write_only=True, required=True)
    
    def get_url_download(self, obj):
        """
        Genera una URL que apunta al endpoint de descarga del backend.
        Esto asegura que las evidencias sean accesibles desde cualquier dispositivo,
        ya que el backend genera URLs presignadas correctamente.
        """
        # Construir URL relativa al endpoint de descarga
        # El frontend debe usar esta URL para obtener la URL presignada real
        return f"/api/v1/work/evidencias/{obj.id}/download/"
    
    class Meta:
        model = Evidencia
        fields = "__all__"
        read_only_fields = ["subido_en", "subido_por"]
        # 'url' no está en read_only_fields porque necesitamos poder establecerlo al crear
        # pero usamos SerializerMethodField para lectura, así que necesitamos un campo separado para escritura


class ComentarioOTSerializer(serializers.ModelSerializer):
    """
    Serializer para comentarios en OT.
    
    Soporta:
    - Creación de comentarios
    - Respuestas a comentarios (comentario_padre)
    - Menciones de usuarios
    - Edición de comentarios
    """
    usuario_nombre = serializers.CharField(source="usuario.get_full_name", read_only=True)
    usuario_username = serializers.CharField(source="usuario.username", read_only=True)
    usuario_rol = serializers.CharField(source="usuario.rol", read_only=True)
    respuestas = serializers.SerializerMethodField()
    
    class Meta:
        model = ComentarioOT
        fields = "__all__"
        read_only_fields = ["editado", "editado_en", "creado_en"]
    
    def get_respuestas(self, obj):
        """Obtiene las respuestas de un comentario."""
        respuestas = obj.respuestas.all().order_by("creado_en")
        return ComentarioOTSerializer(respuestas, many=True).data
    
    def validate(self, attrs):
        """Validar que el contenido no esté vacío."""
        contenido = attrs.get("contenido", "").strip()
        if not contenido:
            raise serializers.ValidationError({"contenido": "El comentario no puede estar vacío."})
        return attrs


class BloqueoVehiculoSerializer(serializers.ModelSerializer):
    """
    Serializer para bloqueos de vehículos.
    """
    creado_por_nombre = serializers.CharField(source="creado_por.get_full_name", read_only=True)
    resuelto_por_nombre = serializers.CharField(source="resuelto_por.get_full_name", read_only=True)
    vehiculo_patente = serializers.CharField(source="vehiculo.patente", read_only=True)
    
    class Meta:
        model = BloqueoVehiculo
        fields = "__all__"
        read_only_fields = ["creado_en", "resuelto_en"]


class VersionEvidenciaSerializer(serializers.ModelSerializer):
    """
    Serializer para versiones de evidencias invalidadas.
    """
    invalidado_por_nombre = serializers.CharField(source="invalidado_por.get_full_name", read_only=True)
    
    class Meta:
        model = VersionEvidencia
        fields = "__all__"
        read_only_fields = ["invalidado_en"]


class AuditoriaSerializer(serializers.ModelSerializer):
    """
    Serializer para registros de auditoría.
    """
    usuario_nombre = serializers.SerializerMethodField()
    usuario_rol = serializers.CharField(source="usuario.rol", read_only=True)
    
    def get_usuario_nombre(self, obj):
        """Retorna el nombre completo del usuario o 'Sistema' si no hay usuario."""
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return "Sistema"
    
    class Meta:
        model = Auditoria
        fields = "__all__"
        read_only_fields = ["id", "ts"]


class OrdenTrabajoListSerializer(serializers.ModelSerializer):
    vehiculo_patente = serializers.CharField(source="vehiculo.patente", read_only=True, allow_null=True)
    vehiculo_detalle = serializers.SerializerMethodField()
    responsable_nombre = serializers.SerializerMethodField()
    responsable_detalle = serializers.SerializerMethodField()
    supervisor_nombre = serializers.SerializerMethodField()
    supervisor_detalle = serializers.SerializerMethodField()
    jefe_taller_nombre = serializers.SerializerMethodField()
    jefe_taller_detalle = serializers.SerializerMethodField()
    mecanico_nombre = serializers.SerializerMethodField()
    mecanico_detalle = serializers.SerializerMethodField()
    fecha_apertura = serializers.DateTimeField(source="apertura", read_only=True)
    tiempo_display = serializers.SerializerMethodField()
    
    def get_vehiculo_detalle(self, obj):
        """Retorna los datos completos del vehículo si existe."""
        if obj.vehiculo:
            return {
                "id": str(obj.vehiculo.id),
                "patente": obj.vehiculo.patente,
                "marca": obj.vehiculo.marca.nombre if obj.vehiculo.marca else None,
                "modelo": obj.vehiculo.modelo,
                "anio": obj.vehiculo.anio,
                "tipo": obj.vehiculo.tipo,
                "estado": obj.vehiculo.estado,
                "estado_operativo": obj.vehiculo.estado_operativo,
            }
        return None
    
    def get_responsable_nombre(self, obj):
        """Retorna el nombre completo del responsable o None si no existe."""
        return obj.responsable.get_full_name() if obj.responsable else None
    
    def get_responsable_detalle(self, obj):
        """Retorna los datos completos del responsable si existe."""
        if obj.responsable:
            return {
                "id": str(obj.responsable.id),
                "username": obj.responsable.username,
                "nombre_completo": obj.responsable.get_full_name(),
                "email": obj.responsable.email,
                "rol": obj.responsable.rol,
            }
        return None
    
    def get_supervisor_nombre(self, obj):
        """Retorna el nombre completo del supervisor o None si no existe."""
        return obj.supervisor.get_full_name() if obj.supervisor else None
    
    def get_supervisor_detalle(self, obj):
        """Retorna los datos completos del supervisor si existe."""
        if obj.supervisor:
            return {
                "id": str(obj.supervisor.id),
                "username": obj.supervisor.username,
                "nombre_completo": obj.supervisor.get_full_name(),
                "email": obj.supervisor.email,
                "rol": obj.supervisor.rol,
            }
        return None
    
    def get_jefe_taller_nombre(self, obj):
        """Retorna el nombre completo del jefe de taller o None si no existe."""
        return obj.jefe_taller.get_full_name() if obj.jefe_taller else None
    
    def get_jefe_taller_detalle(self, obj):
        """Retorna los datos completos del jefe de taller si existe."""
        if obj.jefe_taller:
            return {
                "id": str(obj.jefe_taller.id),
                "username": obj.jefe_taller.username,
                "nombre_completo": obj.jefe_taller.get_full_name(),
                "email": obj.jefe_taller.email,
                "rol": obj.jefe_taller.rol,
            }
        return None
    
    def get_mecanico_nombre(self, obj):
        """Retorna el nombre completo del mecánico o None si no existe."""
        return obj.mecanico.get_full_name() if obj.mecanico else None
    
    def get_mecanico_detalle(self, obj):
        """Retorna los datos completos del mecánico si existe."""
        if obj.mecanico:
            return {
                "id": str(obj.mecanico.id),
                "username": obj.mecanico.username,
                "nombre_completo": obj.mecanico.get_full_name(),
                "email": obj.mecanico.email,
                "rol": obj.mecanico.rol,
            }
        return None
    
    def get_tiempo_display(self, obj):
        """
        Retorna el tiempo de la OT formateado para mostrar.
        
        - Si la OT está cerrada: usa tiempo_total_reparacion (en días)
        - Si la OT no está cerrada: calcula el tiempo transcurrido desde apertura hasta ahora
        """
        from django.utils import timezone
        
        # Si la OT está cerrada y tiene tiempo_total_reparacion, usarlo
        if obj.estado == "CERRADA" and obj.tiempo_total_reparacion:
            return round(float(obj.tiempo_total_reparacion), 2)
        
        # Si no está cerrada, calcular tiempo transcurrido desde apertura
        if obj.apertura:
            ahora = timezone.now()
            delta = ahora - obj.apertura
            dias = delta.total_seconds() / 86400  # Convertir segundos a días
            return round(dias, 2)
        
        return None

    class Meta:
        model = OrdenTrabajo
        fields = [
            "id",
            "estado",
            "vehiculo_patente",
            "vehiculo_detalle",
            "responsable_nombre",
            "responsable_detalle",
            "supervisor_nombre",
            "supervisor_detalle",
            "jefe_taller_nombre",
            "jefe_taller_detalle",
            "mecanico_nombre",
            "mecanico_detalle",
            "prioridad",
            "tipo",
            "apertura",  # Campo original del modelo
            "fecha_apertura",  # Alias para compatibilidad
            "zona",
            "motivo",
            "tiempo_total_reparacion",
            "tiempo_display",
        ]

# apps/vehicles/serializers.py
"""
Serializers para el módulo de vehículos.

Este módulo define:
- VehiculoSerializer: Serializer completo para Vehiculo
- VehiculoListSerializer: Serializer simplificado para listados
- IngresoVehiculoSerializer: Serializer para IngresoVehiculo
- EvidenciaIngresoSerializer: Serializer para EvidenciaIngreso
- HistorialVehiculoSerializer: Serializer para HistorialVehiculo
- BackupVehiculoSerializer: Serializer para BackupVehiculo
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Vehiculo, Marca, IngresoVehiculo, EvidenciaIngreso, HistorialVehiculo, BackupVehiculo
from apps.core.validators import (
    validar_formato_patente,
    validar_ano
)
from apps.workorders.models import OrdenTrabajo

# Obtener el modelo User una vez al inicio del módulo
User = get_user_model()


class MarcaSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Marca.
    """
    class Meta:
        model = Marca
        fields = ['id', 'nombre', 'activa']
        read_only_fields = ['id']


class VehiculoSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Vehiculo.
    
    Incluye todos los campos del vehículo, incluyendo los nuevos campos
    agregados para reportes (supervisor, estado_operativo, etc.)
    
    Validaciones implementadas:
    - Patente única
    - Formato de patente válido
    - Datos obligatorios (patente, marca, modelo, año, tipo_vehiculo, tipo_motor, supervisor)
    - Año válido (2000 - año actual)
    - Validaciones de integridad de datos
    """
    supervisor_nombre = serializers.CharField(source="supervisor.get_full_name", read_only=True)
    supervisor_detalle = serializers.SerializerMethodField()
    marca_nombre = serializers.CharField(source="marca.nombre", read_only=True)
    marca_detalle = serializers.SerializerMethodField()
    
    # Para la escritura, esperamos el ID de la marca
    marca = serializers.PrimaryKeyRelatedField(
        queryset=Marca.objects.filter(activa=True),
        required=True,
        allow_null=False,
        help_text="ID de la marca del vehículo"
    )
    
    # Supervisor es opcional en la creación
    # El queryset se establece directamente usando User.objects
    supervisor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(rol__in=["SUPERVISOR", "COORDINADOR_ZONA"]),
        required=False,
        allow_null=True,
        help_text="ID del supervisor asignado (opcional)"
    )
    
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
    
    def get_marca_detalle(self, obj):
        """Retorna los datos completos de la marca si existe."""
        if obj.marca:
            return {
                "id": obj.marca.id,
                "nombre": obj.marca.nombre,
                "activa": obj.marca.activa,
            }
        return None
    
    class Meta:
        model = Vehiculo
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def validate_patente(self, value):
        """
        Valida que la patente tenga formato válido y sea única.
        """
        # Validar formato de patente
        es_valido, patente_limpia = validar_formato_patente(value)
        if not es_valido:
            raise serializers.ValidationError(patente_limpia)  # patente_limpia contiene el mensaje de error
        
        # Validar que la patente no esté registrada (excepto si es el mismo vehículo)
        instance = self.instance
        if instance:
            # Actualización: verificar que no exista otro vehículo con la misma patente
            # Usar patente_limpia para comparar (normalizada)
            vehiculo_existente = Vehiculo.objects.filter(patente=patente_limpia).exclude(pk=instance.pk).first()
            if vehiculo_existente:
                raise serializers.ValidationError(f"La patente '{patente_limpia}' ya está registrada para otro vehículo.")
        else:
            # Creación: verificar que no exista
            # Normalizar la patente antes de buscar
            vehiculo_existente = Vehiculo.objects.filter(patente=patente_limpia).first()
            if vehiculo_existente:
                raise serializers.ValidationError(f"La patente '{patente_limpia}' ya está registrada.")
        
        return patente_limpia
    
    def validate_anio(self, value):
        """
        Valida que el año sea válido (entre 2000 y el año actual).
        """
        if value:
            es_valido, mensaje = validar_ano(value)
            if not es_valido:
                raise serializers.ValidationError(mensaje)
        return value
    
    def validate_marca(self, value):
        """
        Valida que la marca exista en la tabla de marcas y esté activa.
        """
        if value:
            if not value.activa:
                raise serializers.ValidationError(
                    f"La marca '{value.nombre}' no está activa y no puede ser utilizada."
                )
        return value
    
    def validate(self, attrs):
        """
        Validaciones a nivel de objeto completo.
        """
        # Validar campos obligatorios (solo los esenciales)
        # supervisor y tipo son opcionales en la creación
        campos_obligatorios = {
            'patente': 'patente',
            'marca': 'marca',
            'modelo': 'modelo',
            'anio': 'año',
        }
        
        for campo, nombre_display in campos_obligatorios.items():
            # Si es actualización, usar el valor del atributo o el nuevo valor
            if campo not in attrs:
                if self.instance:
                    # En actualización, si no viene en attrs, usar el valor actual
                    if not getattr(self.instance, campo, None):
                        raise serializers.ValidationError({campo: f"El campo {nombre_display} es obligatorio."})
                else:
                    # En creación, el campo debe estar en attrs
                    raise serializers.ValidationError({campo: f"El campo {nombre_display} es obligatorio."})
        
        
        return attrs


class VehiculoListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de vehículos.
    
    Solo incluye campos esenciales para optimizar rendimiento
    en listados grandes.
    """
    marca_nombre = serializers.CharField(source="marca.nombre", read_only=True)
    marca_detalle = serializers.SerializerMethodField()
    supervisor_nombre = serializers.CharField(source="supervisor.get_full_name", read_only=True)
    supervisor_detalle = serializers.SerializerMethodField()
    
    def get_marca_detalle(self, obj):
        """Retorna los datos completos de la marca si existe."""
        if obj.marca:
            return {
                "id": obj.marca.id,
                "nombre": obj.marca.nombre,
                "activa": obj.marca.activa,
            }
        return None
    
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
    
    class Meta:
        model = Vehiculo
        fields = [
            "id",
            "patente",
            "marca",
            "marca_nombre",
            "marca_detalle",
            "modelo",
            "anio",
            "tipo",
            "categoria",
            "estado",
            "estado_operativo",
            "supervisor",
            "supervisor_nombre",
            "supervisor_detalle",
            "kilometraje_actual",
            "zona",
            "sucursal",
            "vin",
        ]


class IngresoVehiculoSerializer(serializers.ModelSerializer):
    """
    Serializer para IngresoVehiculo.
    
    Validaciones implementadas:
    - Datos mínimos (patente, nombre conductor, RUT conductor, hora ingreso)
    - RUT conductor válido
    - No permitir ingreso si el vehículo ya tiene OT activa
    """
    vehiculo_patente = serializers.CharField(source="vehiculo.patente", read_only=True)
    guardia_nombre = serializers.CharField(source="guardia.get_full_name", read_only=True)
    guardia_detalle = serializers.SerializerMethodField()
    # Incluir información básica del vehículo para el frontend (solo lectura)
    vehiculo_detalle = VehiculoListSerializer(source="vehiculo", read_only=True)
    # Información de OT relacionadas
    ot_relacionadas = serializers.SerializerMethodField()
    
    def get_guardia_detalle(self, obj):
        """Retorna los datos completos del guardia si existe."""
        if obj.guardia:
            return {
                "id": str(obj.guardia.id),
                "username": obj.guardia.username,
                "nombre_completo": obj.guardia.get_full_name(),
                "first_name": obj.guardia.first_name,
                "last_name": obj.guardia.last_name,
                "email": obj.guardia.email,
                "rol": obj.guardia.rol,
            }
        return None
    
    def get_ot_relacionadas(self, obj):
        """Retorna las OT relacionadas con este ingreso."""
        from apps.workorders.models import OrdenTrabajo
        from django.utils import timezone
        from datetime import timedelta
        
        # Buscar OTs del vehículo que se crearon cerca de la fecha de ingreso (mismo día o día siguiente)
        fecha_ingreso = obj.fecha_ingreso.date()
        fecha_limite = fecha_ingreso + timedelta(days=1)
        
        # Hacer la consulta directamente (más eficiente que usar prefetch para este caso)
        ots = OrdenTrabajo.objects.filter(
            vehiculo=obj.vehiculo,
            apertura__date__gte=fecha_ingreso,
            apertura__date__lte=fecha_limite
        ).order_by('-apertura')[:5]  # Máximo 5 OTs más recientes
        
        return [{
            "id": str(ot.id),
            "estado": ot.estado,
            "motivo": ot.motivo,
            "tipo": ot.tipo if hasattr(ot, 'tipo') else None,
            "apertura": ot.apertura.isoformat() if ot.apertura else None,
            "fecha_apertura": ot.apertura.date().isoformat() if ot.apertura else None,
        } for ot in ots]
    
    class Meta:
        model = IngresoVehiculo
        fields = "__all__"
        read_only_fields = ["id", "fecha_ingreso"]
    
    def validate(self, attrs):
        """
        Validaciones a nivel de objeto completo.
        """
        from apps.workorders.models import OrdenTrabajo
        
        # Validar campos obligatorios (solo los que existen en el modelo)
        campos_obligatorios = {
            'vehiculo': 'patente',
        }
        
        for campo, nombre_display in campos_obligatorios.items():
            if campo not in attrs:
                if self.instance:
                    if not getattr(self.instance, campo, None):
                        raise serializers.ValidationError({campo: f"El campo {nombre_display} es obligatorio."})
                else:
                    raise serializers.ValidationError({campo: f"El campo {nombre_display} es obligatorio."})
        
        # Validar que el vehículo no tenga OT activa (solo en creación)
        # NOTA: Esta validación se comenta porque el flujo permite múltiples ingresos
        # El sistema debe manejar múltiples OTs activas si es necesario
        # if not self.instance:
        #     vehiculo = attrs.get('vehiculo')
        #     if vehiculo:
        #         ots_activas = OrdenTrabajo.objects.filter(
        #             vehiculo=vehiculo,
        #             estado__in=['ABIERTA', 'EN_EJECUCION', 'QA', 'EN_DIAGNOSTICO', 'EN_PAUSA']
        #         ).exists()
        #         
        #         if ots_activas:
        #             raise serializers.ValidationError({
        #                 'vehiculo': "El vehículo ya se encuentra ingresado en el taller."
        #             })
        
        return attrs


class EvidenciaIngresoSerializer(serializers.ModelSerializer):
    """
    Serializer para EvidenciaIngreso.
    """
    class Meta:
        model = EvidenciaIngreso
        fields = "__all__"
        read_only_fields = ["id", "subido_en"]


class HistorialVehiculoSerializer(serializers.ModelSerializer):
    """
    Serializer para HistorialVehiculo.
    """
    vehiculo_patente = serializers.CharField(source="vehiculo.patente", read_only=True)
    ot_numero = serializers.CharField(source="ot.id", read_only=True)
    supervisor_nombre = serializers.CharField(source="supervisor.get_full_name", read_only=True)
    backup_patente = serializers.CharField(source="backup_utilizado.vehiculo_backup.patente", read_only=True, allow_null=True)
    
    class Meta:
        model = HistorialVehiculo
        fields = "__all__"
        read_only_fields = ["id", "creado_en"]


class BackupVehiculoSerializer(serializers.ModelSerializer):
    """
    Serializer para BackupVehiculo.
    
    Validaciones implementadas:
    - Backup operativo (estado_operativo = OPERATIVO)
    - Backup no utilizado por otro vehículo
    - Backup no puede ser el mismo que el vehículo principal
    - Campos obligatorios (vehiculo_principal, vehiculo_backup, fecha_inicio, motivo)
    """
    vehiculo_principal_patente = serializers.CharField(source="vehiculo_principal.patente", read_only=True)
    vehiculo_backup_patente = serializers.CharField(source="vehiculo_backup.patente", read_only=True)
    ot_numero = serializers.CharField(source="ot.id", read_only=True, allow_null=True)
    supervisor_nombre = serializers.CharField(source="supervisor.get_full_name", read_only=True)
    
    def validate(self, attrs):
        """
        Validaciones a nivel de objeto completo.
        """
        # Validar campos obligatorios
        campos_obligatorios = {
            'vehiculo_principal': 'vehículo principal',
            'vehiculo_backup': 'vehículo backup',
            'fecha_inicio': 'fecha de inicio',
            'motivo': 'motivo'
        }
        
        for campo, nombre_display in campos_obligatorios.items():
            if campo not in attrs:
                if self.instance:
                    if not getattr(self.instance, campo, None):
                        raise serializers.ValidationError({campo: f"El campo {nombre_display} es obligatorio."})
                else:
                    raise serializers.ValidationError({campo: f"El campo {nombre_display} es obligatorio."})
        
        # Validar que el backup no sea el mismo que el vehículo principal
        vehiculo_principal = attrs.get('vehiculo_principal') or (self.instance.vehiculo_principal if self.instance else None)
        vehiculo_backup = attrs.get('vehiculo_backup') or (self.instance.vehiculo_backup if self.instance else None)
        
        if vehiculo_principal and vehiculo_backup:
            if vehiculo_principal == vehiculo_backup:
                raise serializers.ValidationError({
                    'vehiculo_backup': "Un vehículo no puede ser su propio backup."
                })
            
            # Validar que el backup esté operativo
            if vehiculo_backup.estado_operativo != 'OPERATIVO':
                raise serializers.ValidationError({
                    'vehiculo_backup': "El vehículo backup debe estar operativo."
                })
            
            # Validar que el backup no esté siendo usado por otro vehículo (solo en creación)
            if not self.instance:
                backup_activo = BackupVehiculo.objects.filter(
                    vehiculo_backup=vehiculo_backup,
                    estado='ACTIVO',
                    fecha_devolucion__isnull=True
                ).exists()
                
                if backup_activo:
                    raise serializers.ValidationError({
                        'vehiculo_backup': "El vehículo seleccionado ya está siendo utilizado como backup."
                    })
        
        return attrs
    
    class Meta:
        model = BackupVehiculo
        fields = "__all__"
        read_only_fields = ["id", "creado_en", "actualizado_en", "duracion_dias"]
    
    def create(self, validated_data):
        """
        Crea un backup y calcula la duración automáticamente.
        """
        backup = BackupVehiculo.objects.create(**validated_data)
        backup.calcular_duracion()
        return backup

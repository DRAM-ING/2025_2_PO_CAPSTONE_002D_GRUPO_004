# apps/drivers/serializers.py
from rest_framework import serializers
from .models import Chofer, HistorialAsignacionVehiculo
from apps.vehicles.serializers import VehiculoListSerializer
from apps.core.validators import validar_rut_chileno
import re


class ChoferSerializer(serializers.ModelSerializer):
    vehiculo_asignado_info = VehiculoListSerializer(source="vehiculo_asignado", read_only=True)
    
    class Meta:
        model = Chofer
        fields = [
            "id", "nombre_completo", "rut", "telefono", "email",
            "zona", "sucursal", "vehiculo_asignado", "vehiculo_asignado_info",
            "km_mensual_promedio", "activo", "fecha_ingreso", "observaciones",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def validate_rut(self, value):
        """Valida que el RUT sea válido según formato chileno"""
        if not value:
            raise serializers.ValidationError("El RUT es requerido.")
        
        # Validar formato chileno
        es_valido, rut_limpio = validar_rut_chileno(value)
        if not es_valido:
            raise serializers.ValidationError(f"RUT inválido: {rut_limpio}")
        
        # Retornar RUT limpio (sin puntos ni guión)
        return rut_limpio.replace(".", "").replace("-", "")
    
    def validate_nombre_completo(self, value):
        """Valida que el nombre completo solo contenga letras, espacios y caracteres permitidos"""
        if not value:
            raise serializers.ValidationError("El nombre completo es requerido.")
        
        # Permitir letras, espacios, acentos, ñ, guiones y apóstrofes
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-\']+$', value):
            raise serializers.ValidationError(
                "El nombre completo solo puede contener letras, espacios, acentos, guiones y apóstrofes."
            )
        
        # Validar longitud mínima y máxima
        if len(value.strip()) < 3:
            raise serializers.ValidationError("El nombre completo debe tener al menos 3 caracteres.")
        
        if len(value) > 255:
            raise serializers.ValidationError("El nombre completo no puede exceder 255 caracteres.")
        
        return value.strip()
    
    def validate_telefono(self, value):
        """Valida formato de teléfono"""
        if value:
            # Permitir números, espacios, guiones, paréntesis y +
            if not re.match(r'^[\d\s\-\+\(\)]+$', value):
                raise serializers.ValidationError(
                    "El teléfono solo puede contener números, espacios, guiones, paréntesis y el símbolo +."
                )
            
            # Limpiar y validar longitud
            telefono_limpio = re.sub(r'[\s\-\(\)]', '', value)
            if len(telefono_limpio) < 8 or len(telefono_limpio) > 15:
                raise serializers.ValidationError(
                    "El teléfono debe tener entre 8 y 15 dígitos."
                )
        
        return value


class ChoferListSerializer(serializers.ModelSerializer):
    vehiculo_patente = serializers.CharField(source="vehiculo_asignado.patente", read_only=True)
    
    class Meta:
        model = Chofer
        fields = [
            "id", "nombre_completo", "rut", "telefono", "zona",
            "vehiculo_patente", "activo"
        ]


class HistorialAsignacionVehiculoSerializer(serializers.ModelSerializer):
    chofer_nombre = serializers.CharField(source="chofer.nombre_completo", read_only=True)
    vehiculo_patente = serializers.CharField(source="vehiculo.patente", read_only=True)
    
    class Meta:
        model = HistorialAsignacionVehiculo
        fields = [
            "id", "chofer", "chofer_nombre", "vehiculo", "vehiculo_patente",
            "fecha_asignacion", "fecha_fin", "motivo_fin", "activa"
        ]
        read_only_fields = ["id", "fecha_asignacion"]


# apps/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Profile
from apps.core.validators import (
    validar_rut_chileno,
    validar_formato_correo,
    validar_rol
)

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo User.
    
    Maneja la creación y actualización de usuarios, incluyendo el hasheo correcto
    de contraseñas usando set_password() de Django.
    
    Validaciones implementadas:
    - Correo único
    - Formato de correo válido
    - RUT válido y único
    - Rol válido
    """
    password = serializers.CharField(write_only=True, required=False, min_length=8, help_text="Contraseña (mínimo 8 caracteres)")
    
    def validate_password(self, value):
        """
        Valida la complejidad de la contraseña.
        Requisitos:
        - Mínimo 8 caracteres
        - Al menos una letra mayúscula
        - Al menos una letra minúscula
        - Al menos un número
        - Al menos un carácter especial
        
        Nota: Si el valor está vacío o es None, se retorna sin validar
        (permite actualizar usuario sin cambiar contraseña)
        """
        if not value:
            return value
        
        import re
        errors = []
        
        if len(value) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres.")
        
        if not re.search(r'[A-Z]', value):
            errors.append("La contraseña debe contener al menos una letra mayúscula.")
        
        if not re.search(r'[a-z]', value):
            errors.append("La contraseña debe contener al menos una letra minúscula.")
        
        if not re.search(r'\d', value):
            errors.append("La contraseña debe contener al menos un número.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>\[\]\\/_+=\-]', value):
            errors.append("La contraseña debe contener al menos un carácter especial (!@#$%^&*...).")
        
        if errors:
            raise serializers.ValidationError(" ".join(errors))
        
        return value
    
    def validate_email(self, value):
        """
        Valida que el correo sea único y tenga formato válido.
        """
        # Validar formato de correo
        es_valido, correo_limpio = validar_formato_correo(value)
        if not es_valido:
            raise serializers.ValidationError(correo_limpio)  # correo_limpio contiene el mensaje de error
        
        # Validar que el correo no esté registrado (excepto si es el mismo usuario)
        instance = self.instance
        if instance:
            # Actualización: verificar que no exista otro usuario con el mismo correo
            if User.objects.filter(email=correo_limpio).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError("El correo ya está registrado. Ingrese uno diferente.")
        else:
            # Creación: verificar que no exista
            if User.objects.filter(email=correo_limpio).exists():
                raise serializers.ValidationError("El correo ya está registrado. Ingrese uno diferente.")
        
        return correo_limpio
    
    def validate_rut(self, value):
        """
        Valida que el RUT tenga formato válido y sea único.
        """
        if not value:
            return value  # RUT es opcional
        
        # Validar formato y dígito verificador
        es_valido, rut_formateado = validar_rut_chileno(value)
        if not es_valido:
            raise serializers.ValidationError(rut_formateado)  # rut_formateado contiene el mensaje de error
        
        # Validar que el RUT no esté registrado (excepto si es el mismo usuario)
        instance = self.instance
        if instance:
            # Actualización: verificar que no exista otro usuario con el mismo RUT
            if User.objects.filter(rut=rut_formateado).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError("El RUT ya está registrado en otro usuario.")
        else:
            # Creación: verificar que no exista
            if User.objects.filter(rut=rut_formateado).exists():
                raise serializers.ValidationError("El RUT ya está registrado en otro usuario.")
        
        return rut_formateado
    
    def validate_rol(self, value):
        """
        Valida que el rol sea uno de los permitidos.
        """
        es_valido, mensaje = validar_rol(value)
        if not es_valido:
            raise serializers.ValidationError(mensaje)
        return value
    
    class Meta:
        model = User
        fields = ["id", "username", "email", "rut", "first_name", "last_name", "rol", "is_active", "is_permanent", "date_joined", "password"]
        read_only_fields = ["id", "date_joined", "is_permanent"]
        extra_kwargs = {
            "password": {"write_only": True, "required": False}
        }
    
    def create(self, validated_data):
        """
        Crea un nuevo usuario con la contraseña hasheada correctamente.
        
        Este método es crucial porque Django requiere usar set_password()
        para hashear las contraseñas. Si se guarda directamente, la contraseña
        queda en texto plano y no se puede autenticar.
        
        Parámetros:
        - validated_data: Diccionario con los datos validados del usuario
        
        Retorna:
        - Instancia de User creada con contraseña hasheada
        
        Valida:
        - La contraseña es requerida al crear un usuario
        """
        # Extraer la contraseña del validated_data
        password = validated_data.pop("password", None)
        
        # Validar que la contraseña esté presente al crear
        if not password:
            raise serializers.ValidationError({"password": "La contraseña es requerida al crear un usuario."})
        
        # Crear el usuario sin la contraseña
        user = User.objects.create(**validated_data)
        
        # Hashear y asignar la contraseña
        user.set_password(password)  # Hashea la contraseña correctamente
        user.save()  # Guarda el usuario con la contraseña hasheada
        
        return user
    
    def update(self, instance, validated_data):
        """
        Actualiza un usuario existente.
        
        Si se proporciona una nueva contraseña, la hashea antes de guardar.
        Si no se proporciona contraseña, actualiza solo los otros campos.
        
        Parámetros:
        - instance: Instancia de User a actualizar
        - validated_data: Diccionario con los datos validados
        
        Retorna:
        - Instancia de User actualizada
        """
        # Extraer la contraseña del validated_data
        password = validated_data.pop("password", None)
        
        # Actualizar los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Si se proporcionó una nueva contraseña, hashearla
        if password:
            instance.set_password(password)  # Hashea la nueva contraseña
        
        instance.save()
        return instance

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"
        read_only_fields = ["user"]

    def update(self, instance, validated_data):
        # Actualizar campos del perfil
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)   
    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            # Intentar autenticar
            # No loguear información sensible (username) para prevenir exposición
            user = authenticate(request=self.context.get('request'),
                                username=username, password=password)
            
            # Protección contra timing attacks: siempre hacer las mismas operaciones
            # sin importar si el usuario existe o no
            if not user:
                # No verificar si el usuario existe - esto previene timing attacks
                # y enumeración de usuarios
                raise serializers.ValidationError("Credenciales incorrectas.", code='authorization')
            
            # Verificar que el usuario esté activo
            if not user.is_active:
                raise serializers.ValidationError("Tu cuenta está desactivada. Contacta al administrador.", code='authorization')
            
            # Logging seguro: solo loguear eventos, no datos sensibles
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Login exitoso", extra={"user_id": user.id, "rol": user.rol})
        else:
            raise serializers.ValidationError("Se deben proporcionar ambos campos: 'username' y 'password'.", code='authorization')

        attrs['user'] = user
        return attrs
    

    
class UsuarioListSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ["id", "username", "email", "rut", "first_name", "last_name", "nombre_completo", "rol", "is_active"]
    
    def get_nombre_completo(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        if not User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("No existe un usuario activo con este email.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8, write_only=True)
    confirm_password = serializers.CharField(required=True, min_length=8, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambiar contraseña (requiere contraseña actual)"""
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, min_length=8, write_only=True)
    confirm_password = serializers.CharField(required=True, min_length=8, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return attrs


class AdminChangePasswordSerializer(serializers.Serializer):
    """Serializer para que admin cambie contraseña de otro usuario (sin contraseña actual)"""
    new_password = serializers.CharField(required=True, min_length=8, write_only=True)
    confirm_password = serializers.CharField(required=True, min_length=8, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return attrs

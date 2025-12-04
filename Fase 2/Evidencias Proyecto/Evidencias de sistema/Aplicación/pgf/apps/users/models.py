# apps/users/models.py
"""
Modelos relacionados con usuarios y autenticación.

Este módulo define:
- User: Modelo de usuario extendido con roles y RUT
- Profile: Perfil adicional del usuario
- PasswordResetToken: Tokens para recuperación de contraseña

Relaciones:
- User -> Profile (OneToOne)
- User -> PasswordResetToken (OneToMany)
- User -> OrdenTrabajo (ForeignKey en múltiples campos)
- User -> EmergenciaRuta (ForeignKey en múltiples campos)
"""

from django.db import models
from django.contrib.auth.models import AbstractUser  # Extiende el modelo de usuario base de Django
from django.conf import settings
from django.db.models.signals import post_save  # Señal que se dispara después de guardar
from django.dispatch import receiver  # Decorador para conectar señales
import uuid  # Para generar IDs únicos
import secrets  # Para generar tokens seguros
from django.utils import timezone  # Para manejar fechas con timezone
from datetime import timedelta  # Para calcular fechas futuras


class User(AbstractUser):
    """
    Modelo de Usuario extendido de AbstractUser de Django.
    
    Extiende el modelo base de Django agregando:
    - Sistema de roles para control de acceso
    - RUT chileno como identificador único
    - Email como campo obligatorio y único
    
    Relaciones:
    - OneToOne con Profile (a través de related_name='profile')
    - ForeignKey en OrdenTrabajo (supervisor, jefe_taller, mecanico, responsable)
    - ForeignKey en EmergenciaRuta (solicitante, aprobador, supervisor_asignado, mecanico_asignado)
    - ForeignKey en Agenda (coordinador)
    """
    
    class Rol(models.TextChoices):
        """
        Enum de roles disponibles en el sistema.
        
        Cada rol tiene permisos específicos definidos en:
        - apps/users/permissions.py
        - frontend/src/lib/constants.ts (ROLE_ACCESS)
        """
        GUARDIA = "GUARDIA", "Guardia"  # Control de ingreso/salida de vehículos
        MECANICO = "MECANICO", "Mecánico"  # Ejecuta órdenes de trabajo
        SUPERVISOR = "SUPERVISOR", "Supervisor Zonal"  # Supervisa y aprueba asignaciones
        COORDINADOR_ZONA = "COORDINADOR_ZONA", "Coordinador de Zona"  # Coordina programaciones
        JEFE_TALLER = "JEFE_TALLER", "Jefe de Taller"  # Realiza diagnósticos y aprueba emergencias
        EJECUTIVO = "EJECUTIVO", "Ejecutivo"  # Acceso a dashboard ejecutivo y reportes
        SPONSOR = "SPONSOR", "Sponsor"  # Acceso de solo lectura a dashboards
        ADMIN = "ADMIN", "Administrador"  # Acceso completo al sistema
        CHOFER = "CHOFER", "Chofer"  # Rol pasivo, solo visualización de vehículos asignados
        ADMINISTRATIVO_TALLER = "ADMINISTRATIVO_TALLER", "Administrativo de Taller"  # Gestión administrativa de OTs
        BODEGA = "BODEGA", "Bodega / Encargado de Repuestos"  # Gestión de repuestos e inventario

    # Campo de rol: almacena el rol del usuario, por defecto ADMIN
    # Se valida contra las opciones definidas en Rol.choices
    # max_length=25 para soportar ADMINISTRATIVO_TALLER (21 caracteres)
    rol = models.CharField(max_length=25, choices=Rol.choices, default=Rol.ADMIN)
    
    # Email obligatorio y único: usado para autenticación y recuperación de contraseña
    email = models.EmailField(unique=True, blank=False, null=False)
    
    # RUT chileno: identificador único opcional, sin puntos ni guión
    # Ejemplo: "123456789" o "12345678K"
    # Validado en frontend y backend
    rut = models.CharField(
        max_length=12, 
        unique=True, 
        blank=True, 
        null=True, 
        help_text="RUT sin puntos ni guión (ej: 123456789)"
    )
    
    # Usuario permanente: no se puede eliminar, solo editar y ver
    # Útil para super usuarios del sistema que deben estar siempre disponibles
    is_permanent = models.BooleanField(
        default=False,
        help_text="Si está marcado, este usuario no se puede eliminar, solo editar y ver"
    )
    
    # REQUIRED_FIELDS: le dice a Django que el email es obligatorio al crear superusuario
    # Además de username (que ya es requerido por AbstractUser)
    REQUIRED_FIELDS = ['email']


class Profile(models.Model):
    """
    Perfil extendido del usuario.
    
    Almacena información adicional que no está en el modelo User base.
    Se crea automáticamente cuando se crea un User (ver señales abajo).
    
    Relaciones:
    - OneToOne con User (a través de AUTH_USER_MODEL)
    """
    
    # Relación OneToOne: cada usuario tiene un perfil y viceversa
    # on_delete=CASCADE: si se elimina el usuario, se elimina el perfil
    # related_name='profile': permite acceder al perfil desde user.profile
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Usa el modelo de usuario configurado en settings
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    
    # Nombres: se sincronizan con User.first_name y User.last_name
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    
    # Teléfono: información de contacto adicional
    phone_number = models.CharField(max_length=32, blank=True)
    
    # Preferencias de notificaciones
    notificaciones_email = models.BooleanField(
        default=True,
        help_text="Recibir notificaciones por email"
    )
    notificaciones_sonido = models.BooleanField(
        default=True,
        help_text="Reproducir sonido al recibir notificaciones"
    )
    notificaciones_push = models.BooleanField(
        default=False,
        help_text="Recibir notificaciones push del navegador"
    )

    def __str__(self):
        """
        Representación en string del perfil.
        Usado en admin de Django y en logs.
        """
        return self.user.username


# ==================== SEÑALES (SIGNALS) ====================
# Las señales permiten ejecutar código automáticamente cuando ocurren eventos en los modelos

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Señal que se dispara después de guardar un User.
    
    Crea un Profile automáticamente cuando se crea un nuevo User.
    
    Parámetros:
    - sender: El modelo que envió la señal (User)
    - instance: La instancia del User que se guardó
    - created: True si es un nuevo registro, False si es una actualización
    - **kwargs: Argumentos adicionales
    """
    if created:  # Solo crear perfil si es un usuario nuevo
        Profile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """
    Señal que se dispara después de guardar un User.
    
    Guarda el Profile automáticamente cuando se guarda el User.
    Esto asegura que los cambios en el perfil se persistan.
    """
    # Verificar que el perfil existe antes de guardarlo
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    """
    Señal adicional para asegurar que el perfil existe.
    
    Esta función es idempotente: si el perfil ya existe, no lo crea de nuevo.
    También sincroniza los nombres del User con el Profile.
    
    Se ejecuta después de create_user_profile para garantizar consistencia.
    """
    # get_or_create: obtiene el perfil si existe, o lo crea si no existe
    # defaults: valores por defecto si se crea
    Profile.objects.get_or_create(
        user=instance,
        defaults={
            "first_name": instance.first_name or "",
            "last_name": instance.last_name or "",
        }
    )
    
    # Sincronizar nombres cada vez que cambien en User
    # Esto asegura que Profile.first_name y Profile.last_name siempre coincidan con User
    Profile.objects.filter(user=instance).update(
        first_name=instance.first_name or "",
        last_name=instance.last_name or "",
    )


class PasswordResetToken(models.Model):
    """
    Tokens para recuperación de contraseña.
    
    Almacena tokens únicos y seguros que permiten a los usuarios
    restablecer su contraseña sin necesidad de estar autenticados.
    
    Cada token:
    - Es único y seguro (generado con secrets.token_urlsafe)
    - Expira después de 24 horas
    - Solo puede usarse una vez
    - Se invalida automáticamente cuando se genera uno nuevo
    
    Relaciones:
    - ForeignKey con User (un usuario puede tener múltiples tokens, pero solo uno activo)
    """
    
    # ID único: UUID4 para evitar colisiones y exponer información
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Usuario al que pertenece el token
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,  # Si se elimina el usuario, se eliminan sus tokens
        related_name="password_reset_tokens"
    )
    
    # Token único: string aleatorio seguro, indexado para búsquedas rápidas
    token = models.CharField(max_length=64, unique=True, db_index=True)
    
    # Fecha de creación: se establece automáticamente al crear
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Fecha de expiración: se calcula al crear (created_at + 24 horas)
    expires_at = models.DateTimeField()
    
    # Indica si el token ya fue usado
    used = models.BooleanField(default=False)
    
    class Meta:
        """
        Configuración del modelo.
        
        - indexes: índices para optimizar búsquedas frecuentes
        - ordering: orden por defecto al consultar
        """
        indexes = [
            # Índice compuesto para búsquedas por token y estado de uso
            models.Index(fields=["token", "used"]),
            # Índice para limpiar tokens expirados
            models.Index(fields=["expires_at"]),
        ]
        ordering = ["-created_at"]  # Más recientes primero
    
    def __str__(self):
        """
        Representación en string del token.
        Muestra el email del usuario y la fecha de creación.
        """
        return f"Token para {self.user.email} - {self.created_at}"
    
    @classmethod
    def generate_token(cls, user):
        """
        Genera un nuevo token de reset para el usuario.
        
        Este método:
        1. Invalida todos los tokens anteriores no usados del usuario
        2. Genera un nuevo token seguro
        3. Establece expiración a 24 horas
        4. Crea y retorna el nuevo token
        
        Parámetros:
        - user: Instancia de User para el cual generar el token
        
        Retorna:
        - Instancia de PasswordResetToken
        
        Uso:
        - Llamado desde apps/users/views.py en PasswordResetRequestView
        """
        # Invalidar tokens anteriores no usados y no expirados
        # Esto asegura que solo haya un token activo por usuario
        cls.objects.filter(
            user=user, 
            used=False, 
            expires_at__gt=timezone.now()  # Solo los que aún no han expirado
        ).update(used=True)
        
        # Generar token seguro: 32 bytes codificados en URL-safe base64
        # Resultado: string de ~43 caracteres, único y seguro
        token = secrets.token_urlsafe(32)
        
        # Calcular fecha de expiración: 24 horas desde ahora
        expires_at = timezone.now() + timedelta(hours=24)
        
        # Crear y retornar el nuevo token
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
    
    def is_valid(self):
        """
        Verifica si el token es válido.
        
        Un token es válido si:
        - No ha sido usado (used=False)
        - No ha expirado (expires_at > ahora)
        
        Retorna:
        - True si el token es válido
        - False si el token fue usado o expiró
        
        Uso:
        - Llamado desde apps/users/views.py en PasswordResetConfirmView
        """
        return not self.used and timezone.now() < self.expires_at

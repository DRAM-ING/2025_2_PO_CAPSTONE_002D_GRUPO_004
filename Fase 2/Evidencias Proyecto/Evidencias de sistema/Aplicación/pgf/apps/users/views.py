# apps/users/views.py
"""
Vistas y ViewSets para gestión de usuarios y autenticación.

Este módulo define:
- UserViewSet: CRUD de usuarios con permisos personalizados
- ProfileViewSet: Gestión de perfiles de usuario
- LoginView: Autenticación JWT con cookies
- RefreshCookieView: Renovación de tokens
- PasswordResetRequestView: Solicitud de recuperación de contraseña
- PasswordResetConfirmView: Confirmación y cambio de contraseña
- ChangePasswordView: Cambio de contraseña del usuario logueado
- AdminChangePasswordView: Cambio de contraseña por admin

Relaciones:
- Usa: apps/users/models.py (User, Profile, PasswordResetToken)
- Usa: apps/users/serializers.py (serializers para validación)
- Usa: apps/users/permissions.py (UserPermission)
- Usa: apps/workorders/models.py (Auditoria para logs)
- Conectado a: apps/users/urls.py y apps/users/auth_urls.py
"""

from django.shortcuts import render

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import User, Profile
from .serializers import UserSerializer, ProfileSerializer
from .permissions import UserPermission
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer , LoginSerializer, ProfileSerializer, UsuarioListSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.audit_logging import log_audit, log_data_change, get_client_ip


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Usuarios.
    
    Proporciona endpoints CRUD completos:
    - GET /api/v1/users/ → Listar usuarios
    - POST /api/v1/users/ → Crear usuario (público)
    - GET /api/v1/users/{id}/ → Ver usuario
    - PUT/PATCH /api/v1/users/{id}/ → Editar usuario
    - DELETE /api/v1/users/{id}/ → Eliminar usuario
    - GET /api/v1/users/me/ → Ver perfil propio
    - PUT/PATCH /api/v1/users/me/ → Editar perfil propio
    
    Permisos:
    - Crear: Público (cualquiera puede registrarse)
    - Listar: Solo ADMIN y SUPERVISOR
    - Ver/Editar/Eliminar: ADMIN, SUPERVISOR, o el propio usuario
    - /me/: Cualquier usuario autenticado puede ver/editar su propio perfil
    
    Relaciones:
    - Usa UserPermission para control de acceso
    - Al eliminar, limpia relaciones con inventory (si existen)
    """
    queryset = User.objects.all().order_by('id')  # QuerySet base: todos los usuarios ordenados por ID
    serializer_class = UserSerializer  # Serializer por defecto
    permission_classes = [UserPermission]  # Permisos personalizados
    
    # Configuración de filtros
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['rol', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'rut']
    ordering_fields = ['username', 'email', 'date_joined']
    ordering = ['username']

    def get_queryset(self):
        """
        Filtra el queryset para ocultar el usuario 'admin' a todos excepto al propio admin.
        También aplica filtros de query params (rol, is_active, etc.)
        
        Reglas:
        - Solo el usuario con username 'admin' puede ver al usuario 'admin' en las listas
        - Todos los demás usuarios (incluso otros ADMIN) no verán al usuario 'admin'
        - Filtra por rol si se proporciona ?rol=MECANICO
        
        Retorna:
        - QuerySet filtrado según el usuario autenticado y query params
        """
        queryset = super().get_queryset()
        
        # Solo el usuario con username 'admin' puede ver al usuario 'admin'
        # Esto es más estricto que solo verificar el rol, ya que podría haber múltiples usuarios con rol ADMIN
        if self.request.user.is_authenticated and self.request.user.username != "admin":
            queryset = queryset.exclude(username="admin")
        
        # Aplicar filtro de rol si se proporciona
        rol = self.request.query_params.get('rol')
        if rol:
            queryset = queryset.filter(rol=rol)
        
        return queryset
    
    def perform_create(self, serializer):
        """Registra auditoría al crear un usuario."""
        user = serializer.save()
        ip = get_client_ip(self.request)
        log_audit(
            usuario=self.request.user if self.request.user.is_authenticated else None,
            accion="CREAR_USUARIO",
            objeto_tipo="User",
            objeto_id=str(user.id),
            payload={
                "username": user.username,
                "email": user.email,
                "rol": user.rol,
                "is_active": user.is_active
            },
            ip_address=ip
        )
    
    def perform_update(self, serializer):
        """Registra auditoría al actualizar un usuario."""
        instance = serializer.instance
        old_data = {
            "username": instance.username,
            "email": instance.email,
            "rol": instance.rol,
            "is_active": instance.is_active
        }
        user = serializer.save()
        new_data = {
            "username": user.username,
            "email": user.email,
            "rol": user.rol,
            "is_active": user.is_active
        }
        
        # Detectar cambios
        cambios = {}
        for campo, valor_anterior in old_data.items():
            valor_nuevo = new_data.get(campo)
            if valor_anterior != valor_nuevo:
                cambios[campo] = {"antes": valor_anterior, "despues": valor_nuevo}
        
        ip = get_client_ip(self.request)
        if cambios:
            log_data_change(
                usuario=self.request.user,
                accion="ACTUALIZAR_USUARIO",
                objeto_tipo="User",
                objeto_id=str(user.id),
                cambios=cambios,
                ip_address=ip
            )
        else:
            log_audit(
                usuario=self.request.user,
                accion="ACTUALIZAR_USUARIO",
                objeto_tipo="User",
                objeto_id=str(user.id),
                payload={"username": user.username},
                ip_address=ip
            )

    def destroy(self, request, *args, **kwargs):
        """
        Eliminar usuario con manejo de errores mejorado.
        
        Captura excepciones y siempre retorna JSON en lugar de HTML.
        """
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            # Capturar cualquier excepción y retornar JSON
            from rest_framework.exceptions import ValidationError, PermissionDenied
            from django.db.models.deletion import ProtectedError
            from rest_framework import status
            
            if isinstance(e, (ValidationError, PermissionDenied)):
                # Re-lanzar excepciones de DRF (ya están en formato JSON)
                raise
            
            if isinstance(e, ProtectedError):
                # ProtectedError de Django
                objetos_protegidos = []
                for obj in e.protected_objects[:5]:  # Limitar a 5 para no hacer el mensaje muy largo
                    objetos_protegidos.append(f"{obj._meta.verbose_name} (ID: {obj.pk})")
                
                mensaje = f"No se puede eliminar el usuario porque está relacionado con: {', '.join(objetos_protegidos)}"
                if len(e.protected_objects) > 5:
                    mensaje += f" y {len(e.protected_objects) - 5} más."
                mensaje += " Primero debe eliminar o modificar estas relaciones."
                
                return Response(
                    {"detail": mensaje},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Cualquier otro error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al eliminar usuario: {str(e)}", exc_info=True)
            
            return Response(
                {"detail": f"Error al eliminar el usuario: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_destroy(self, instance):
        """
        Eliminar usuario de forma segura.
        
        Este método se ejecuta antes de eliminar un usuario.
        Limpia relaciones con módulos que pueden no estar migrados
        (inventory) para evitar errores de ForeignKey.
        
        Parámetros:
        - instance: Instancia de User a eliminar
        
        Proceso:
        1. Verifica que el usuario no sea permanente
        2. Verifica relaciones PROTECT antes de intentar eliminar
        3. Intenta limpiar relaciones SET_NULL (si existen)
        4. Elimina el usuario
        
        Nota: Usa try/except para que si las tablas no existen,
        la eliminación continúe sin errores.
        """
        # Prevenir eliminación de usuarios permanentes
        if instance.is_permanent:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                detail="No se puede eliminar un usuario permanente. Solo se puede editar y ver."
            )
        
        # Registrar auditoría antes de eliminar
        username = instance.username
        user_id = str(instance.id)
        ip = get_client_ip(self.request)
        
        # Verificar relaciones PROTECT antes de intentar eliminar
        relaciones_protegidas = []
        
        # Verificar MovimientoStock (PROTECT)
        try:
            from apps.inventory.models import MovimientoStock
            count = MovimientoStock.objects.filter(usuario=instance).count()
            if count > 0:
                relaciones_protegidas.append(f"{count} movimiento(s) de stock")
        except Exception:
            pass
        
        # Verificar SolicitudRepuesto.solicitante (PROTECT)
        try:
            from apps.inventory.models import SolicitudRepuesto
            count = SolicitudRepuesto.objects.filter(solicitante=instance).count()
            if count > 0:
                relaciones_protegidas.append(f"{count} solicitud(es) de repuestos")
        except Exception:
            pass
        
        # Verificar Pausa (PROTECT)
        try:
            from apps.workorders.models import Pausa
            count = Pausa.objects.filter(usuario=instance).count()
            if count > 0:
                relaciones_protegidas.append(f"{count} pausa(s) de órdenes de trabajo")
        except Exception:
            pass
        
        # Verificar Aprobacion.sponsor (PROTECT)
        try:
            from apps.workorders.models import Aprobacion
            count = Aprobacion.objects.filter(sponsor=instance).count()
            if count > 0:
                relaciones_protegidas.append(f"{count} aprobación(es)")
        except Exception:
            pass
        
        # Verificar IngresoVehiculo.guardia (PROTECT)
        try:
            from apps.vehicles.models import IngresoVehiculo
            count = IngresoVehiculo.objects.filter(guardia=instance).count()
            if count > 0:
                relaciones_protegidas.append(f"{count} ingreso(s) de vehículos registrado(s)")
        except Exception:
            pass
        
        # Verificar Agenda.coordinador (PROTECT)
        try:
            from apps.scheduling.models import Agenda
            count = Agenda.objects.filter(coordinador=instance).count()
            if count > 0:
                relaciones_protegidas.append(f"{count} agenda(s) creada(s)")
        except Exception:
            pass
        
        # Verificar EmergenciaRuta.solicitante (PROTECT) - App deshabilitada
        # try:
        #     from apps.emergencies.models import EmergenciaRuta
        #     count = EmergenciaRuta.objects.filter(solicitante=instance).count()
        #     if count > 0:
        #         relaciones_protegidas.append(f"{count} emergencia(s) solicitada(s)")
        # except Exception:
        #     pass
        
        # Si hay relaciones protegidas, retornar error claro
        if relaciones_protegidas:
            from rest_framework.exceptions import ValidationError
            mensaje = f"No se puede eliminar el usuario porque tiene relaciones protegidas: {', '.join(relaciones_protegidas)}. "
            mensaje += "Primero debe eliminar o modificar estas relaciones."
            raise ValidationError({"detail": mensaje})
        
        # Limpiar relaciones SET_NULL (si existen)
        try:
            # SolicitudRepuesto.aprobador y entregador (SET_NULL)
            from apps.inventory.models import SolicitudRepuesto
            SolicitudRepuesto.objects.filter(aprobador=instance).update(aprobador=None)
            SolicitudRepuesto.objects.filter(entregador=instance).update(entregador=None)
        except Exception:
            pass
        
        # Registrar auditoría antes de eliminar
        log_audit(
            usuario=self.request.user,
            accion="ELIMINAR_USUARIO",
            objeto_tipo="User",
            objeto_id=user_id,
            payload={"username": username},
            nivel='WARNING',
            ip_address=ip
        )
        
        # Intentar eliminar el usuario
        # Django automáticamente eliminará:
        # - Profile (OneToOne con CASCADE)
        # - PasswordResetToken (ForeignKey con CASCADE)
        try:
            instance.delete()
        except Exception as e:
            # Capturar cualquier otro error (incluyendo ProtectedError de Django)
            from django.db.models.deletion import ProtectedError
            if isinstance(e, ProtectedError):
                # ProtectedError tiene información sobre los objetos relacionados
                objetos_protegidos = []
                for obj in e.protected_objects:
                    objetos_protegidos.append(f"{obj._meta.verbose_name} (ID: {obj.pk})")
                
                from rest_framework.exceptions import ValidationError
                mensaje = f"No se puede eliminar el usuario porque está relacionado con: {', '.join(objetos_protegidos[:5])}"
                if len(objetos_protegidos) > 5:
                    mensaje += f" y {len(objetos_protegidos) - 5} más."
                mensaje += " Primero debe eliminar o modificar estas relaciones."
                raise ValidationError({"detail": mensaje})
            else:
                # Otro tipo de error
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"detail": f"Error al eliminar el usuario: {str(e)}"})

    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request, *args, **kwargs):
        """
        Endpoint para obtener/editar el perfil del usuario logueado.
        
        URL: /api/v1/users/me/
        
        Métodos:
        - GET: Retorna información del usuario actual
        - PUT/PATCH: Actualiza información del usuario actual
        
        Permisos:
        - Requiere autenticación (cualquier usuario logueado)
        
        Funcionamiento:
        - Establece self.kwargs['pk'] = request.user.pk
        - Delega a retrieve() o update() según el método
        - Esto permite reutilizar la lógica de esos métodos
        
        Uso:
        - Frontend llama a /api/v1/users/me/ para obtener datos del usuario
        - Frontend llama a PUT /api/v1/users/me/ para actualizar perfil
        """
        # Establecer el ID del usuario actual como el ID a consultar
        # Esto permite usar los métodos retrieve() y update() existentes
        self.kwargs['pk'] = request.user.pk
        
        if request.method == 'GET':
            # Obtener información del usuario
            return self.retrieve(request, *args, **kwargs)
        elif request.method in ['PUT', 'PATCH']:
            # Actualizar información del usuario
            return self.update(request, *args, **kwargs)

class ProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet para perfiles de usuario.
    
    Generalmente se accede a través del endpoint /users/me/,
    pero este ViewSet permite gestión directa de perfiles si es necesario.
    
    Permisos:
    - Requiere autenticación
    - Usuario solo ve su propio perfil (a menos que sea staff/admin)
    
    Relaciones:
    - OneToOne con User (a través de AUTH_USER_MODEL)
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtrar queryset según permisos.
        
        - Staff/Admin: Ven todos los perfiles
        - Usuario regular: Solo ve su propio perfil
        
        Retorna:
        - QuerySet filtrado según el usuario
        """
        if self.request.user.is_staff:
            return Profile.objects.all()
        return Profile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """
        Crea un perfil asignando automáticamente el usuario actual.
        
        Si el usuario ya tiene un perfil, no se crea otro.
        """
        # Verificar si el usuario ya tiene un perfil
        if hasattr(self.request.user, 'profile'):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": "El usuario ya tiene un perfil."})
        
        # Asignar el usuario actual al perfil
        serializer.save(user=self.request.user)
    
class MeAPIView(APIView):
    """
    Vista alternativa para /me/.
    
    Endpoint simple que retorna información del usuario actual.
    Más simple que usar UserViewSet.me, pero con menos funcionalidades.
    
    URL: /api/v1/users/me/ (si está configurado en urls.py)
    
    Permisos:
    - Requiere autenticación
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retorna información del usuario actual incluyendo perfil con preferencias.
        
        Retorna:
        - JSON con datos del usuario serializados y perfil
        """
        serializer = UserSerializer(request.user)
        data = serializer.data
        
        # Incluir perfil con preferencias si existe
        if hasattr(request.user, 'profile'):
            profile_serializer = ProfileSerializer(request.user.profile)
            data['profile'] = profile_serializer.data
        
        return Response(data)
    

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

from .serializers import LoginSerializer, UserSerializer, ProfileSerializer, UsuarioListSerializer


class LoginView(APIView):
    """
    Vista de autenticación (login).
    
    Endpoint: POST /api/v1/auth/login/
    
    Permisos:
    - Público (AllowAny) - cualquiera puede intentar hacer login
    
    Funcionalidad:
    1. Valida credenciales (username/password)
    2. Verifica que el usuario esté activo
    3. Genera tokens JWT (access y refresh)
    4. Establece cookies con los tokens
    5. Registra auditoría de login exitoso
    6. Retorna información del usuario y tokens
    
    Cookies:
    - pgf_access: Token de acceso (expira en 1 hora)
    - pgf_refresh: Token de refresh (expira en 7 días)
    
    Relaciones:
    - Usa LoginSerializer para validar credenciales
    - Usa apps/workorders/models.py (Auditoria) para logs
    """
    permission_classes = [AllowAny]  # Público - cualquiera puede intentar login
    throttle_classes = [AnonRateThrottle]  # Rate limiting: 5 intentos/minuto por IP

    def post(self, request):
        """
        Procesa el login.
        
        Parámetros (body JSON):
        - username: Nombre de usuario
        - password: Contraseña
        
        Retorna:
        - 200: Login exitoso
          {
            "user": {...},
            "access": "token...",
            "refresh": "token..."
          }
        - 400: Credenciales inválidas o usuario inactivo
        - 401: Error de autenticación
        """
        try:
            # Validar datos de entrada
            serializer = LoginSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            
            # Obtener usuario validado del serializer
            # LoginSerializer.validate() ya verificó credenciales y que esté activo
            user = serializer.validated_data["user"]
        except serializers.ValidationError as e:
            # Si es un error de validación (credenciales incorrectas), retornarlo directamente
            error_message = "Credenciales incorrectas"
            if hasattr(e, 'detail'):
                if isinstance(e.detail, list) and len(e.detail) > 0:
                    error_message = str(e.detail[0])
                elif isinstance(e.detail, dict):
                    error_message = str(e.detail.get('non_field_errors', [error_message])[0])
                else:
                    error_message = str(e.detail)
            return Response(
                {"detail": error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Capturar cualquier otro error y retornar un mensaje claro
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en login: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Error al procesar el login. Por favor intenta nuevamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            # Logging seguro: no exponer información sensible
            import logging
            logger = logging.getLogger(__name__)
            # Solo loguear eventos, no datos personales
            logger.info("Login exitoso", extra={"user_id": user.id, "rol": user.rol})

            # Generar tokens JWT
            # RefreshToken.for_user() crea un par de tokens (refresh + access)
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token  # Token de acceso (corto plazo)

            # Registrar auditoría de acceso exitoso
            # Esto permite rastrear quién y cuándo accedió al sistema
            from apps.workorders.models import Auditoria
            from django.utils import timezone
            try:
                Auditoria.objects.create(
                    usuario=user,
                    accion="LOGIN_EXITOSO",
                    objeto_tipo="User",
                    objeto_id=str(user.id),
                    payload={
                        "ip": self.get_client_ip(request),  # IP del cliente
                        "user_agent": request.META.get('HTTP_USER_AGENT', ''),  # Navegador
                        "timestamp": timezone.now().isoformat(),  # Fecha/hora
                        "rol": user.rol  # Agregar rol para debugging
                    }
                )
            except Exception as e:
                # Si falla la auditoría, no bloquear el login
                # Solo loguear el error para debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error al registrar auditoría de login: {e}")

            # Preparar respuesta con datos del usuario y tokens
            res = Response({
                "user": UserSerializer(user).data,  # Datos del usuario serializados
                "access": str(access),              # Token de acceso (también en cookie)
                "refresh": str(refresh),            # Token de refresh (también en cookie)
            })

            # Configurar cookies con los tokens
            # secure: True solo en producción (HTTPS), False en desarrollo (HTTP)
            secure = not settings.DEBUG

            # Cookie con token de acceso
            res.set_cookie(
                "pgf_access",
                str(access),
                httponly=True,      # No accesible desde JavaScript (protección XSS)
                samesite="Lax",     # Protección CSRF
                secure=secure,      # Solo enviar por HTTPS en producción
                path="/",           # Disponible en todo el sitio
                max_age=3600,       # Expira en 1 hora (3600 segundos)
            )

            # Cookie con token de refresh
            res.set_cookie(
                "pgf_refresh",
                str(refresh),
                httponly=True,
                samesite="Lax",
                secure=secure,
                path="/",
                max_age=3600 * 24 * 7,  # Expira en 7 días
            )

            return res
        except Exception as e:
            # Capturar errores en la generación de tokens o cookies
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generando tokens o cookies: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Error al generar tokens de autenticación. Por favor intenta nuevamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_client_ip(self, request):
        """
        Obtiene la IP real del cliente.
        
        Considera proxies y load balancers que pueden agregar
        headers como X-Forwarded-For.
        
        Parámetros:
        - request: Objeto HttpRequest de Django
        
        Retorna:
        - str: IP del cliente
        
        Uso:
        - Llamado desde post() para registrar en auditoría
        """
        # Verificar header X-Forwarded-For (usado por proxies)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # X-Forwarded-For puede tener múltiples IPs separadas por coma
            # La primera es la IP original del cliente
            ip = x_forwarded_for.split(',')[0]
        else:
            # Si no hay X-Forwarded-For, usar REMOTE_ADDR
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RefreshCookieView(APIView):
    """
    Vista para renovar el token de acceso usando el refresh token.
    
    Endpoint: POST /api/v1/auth/refresh/
    
    Permisos:
    - Público (AllowAny) - pero requiere refresh token válido en cookie
    
    Funcionalidad:
    1. Lee el refresh token de las cookies
    2. Valida el token
    3. Genera un nuevo access token
    4. Establece cookie con el nuevo access token
    5. Retorna el nuevo access token
    
    Uso:
    - Llamado automáticamente cuando el access token expira
    - Permite mantener la sesión activa sin requerir login nuevamente
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Renueva el token de acceso.
        
        Retorna:
        - 200: Token renovado
          {
            "access": "nuevo_token..."
          }
        - 401: Refresh token inválido o no encontrado
        """
        # Obtener refresh token de las cookies
        refresh_token = request.COOKIES.get("pgf_refresh")

        if not refresh_token:
            return Response({"detail": "No refresh token found"}, status=401)

        try:
            # Validar y generar nuevo access token
            refresh = RefreshToken(refresh_token)
            access = refresh.access_token  # Nuevo token de acceso
        except Exception:
            # Si el token es inválido o expiró
            return Response({"detail": "Invalid refresh token"}, status=401)

        # Preparar respuesta con nuevo token
        res = Response({"access": str(access)})

        # Configurar cookie con nuevo access token
        secure = not settings.DEBUG

        res.set_cookie(
            "pgf_access",
            str(access),
            httponly=True,
            samesite="Lax",
            secure=secure,
            path="/",
            max_age=3600,  # 1 hora
        )

        return res



class UsuarioListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para listar usuarios.
    
    Útil cuando solo se necesita listar usuarios sin permitir
    crear, editar o eliminar.
    
    Endpoints:
    - GET /api/v1/users/ → Lista usuarios (serializer simplificado)
    - GET /api/v1/users/{id}/ → Ver usuario
    
    Permisos:
    - Requiere autenticación
    """
    queryset = User.objects.all().order_by('id')
    serializer_class = UsuarioListSerializer  # Serializer simplificado (menos campos)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtra el queryset para ocultar el usuario 'admin' a todos excepto al propio admin.
        
        Reglas:
        - Solo el usuario con username 'admin' puede ver al usuario 'admin' en las listas
        - Todos los demás usuarios (incluso otros ADMIN) no verán al usuario 'admin'
        
        Retorna:
        - QuerySet filtrado según el usuario autenticado
        """
        queryset = super().get_queryset()
        
        # Solo el usuario con username 'admin' puede ver al usuario 'admin'
        # Esto es más estricto que solo verificar el rol, ya que podría haber múltiples usuarios con rol ADMIN
        if self.request.user.is_authenticated and self.request.user.username != "admin":
            queryset = queryset.exclude(username="admin")
        
        return queryset


class PasswordResetRequestView(APIView):
    """
    Vista para solicitar recuperación de contraseña.
    
    Endpoint: POST /api/v1/auth/password-reset/
    
    Permisos:
    - Público (AllowAny) - cualquiera puede solicitar reset
    
    Funcionalidad:
    1. Valida que el email existe y el usuario está activo
    2. Genera un token de reset único
    3. Envía email con link de recuperación
    4. Retorna éxito (sin exponer si el email existe o no)
    
    Seguridad:
    - Siempre retorna 200 para no revelar si un email existe
    - Token expira en 24 horas
    - Solo un token activo por usuario (invalida anteriores)
    
    Relaciones:
    - Usa PasswordResetToken.generate_token() para crear token
    - Envía email usando Django send_mail
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Procesa la solicitud de reset de contraseña.
        
        Parámetros (body JSON):
        - email: Email del usuario
        
        Retorna:
        - 200: Siempre (por seguridad, no revela si el email existe)
        - 400: Error de validación (email inválido)
        """
        from .serializers import PasswordResetRequestSerializer
        from .models import PasswordResetToken
        from django.core.mail import send_mail
        from django.conf import settings
        
        # Validar email
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        # Logging para auditoría
        import logging
        logger = logging.getLogger(__name__)
        
        # Obtener IP del cliente para logging
        client_ip = self.get_client_ip(request)
        
        try:
            # Buscar usuario activo con ese email
            user = User.objects.get(email=email, is_active=True)
            
            # Log exitoso (sin exponer email completo por seguridad)
            logger.info(
                f"Password reset solicitado para usuario ID {user.id} desde IP {client_ip}",
                extra={
                    'action': 'password_reset_request',
                    'user_id': str(user.id),
                    'email_prefix': email.split('@')[0] if '@' in email else 'unknown',
                    'client_ip': client_ip,
                    'success': True
                }
            )
            
        except User.DoesNotExist:
            # Log intento fallido (sin revelar si el email existe)
            logger.warning(
                f"Intento de password reset para email no encontrado o inactivo desde IP {client_ip}",
                extra={
                    'action': 'password_reset_request',
                    'email_prefix': email.split('@')[0] if '@' in email else 'unknown',
                    'client_ip': client_ip,
                    'success': False,
                    'reason': 'user_not_found_or_inactive'
                }
            )
            
            # Por seguridad, siempre retornar 200 aunque el email no exista
            # Esto previene enumeración de usuarios
            return Response(
                {"detail": "Si el email existe, se enviará un enlace de recuperación."},
                status=status.HTTP_200_OK
            )
        except User.MultipleObjectsReturned:
            # Log error crítico (múltiples usuarios con mismo email)
            logger.error(
                f"Error crítico: Múltiples usuarios con email {email.split('@')[0] if '@' in email else 'unknown'} desde IP {client_ip}",
                extra={
                    'action': 'password_reset_request',
                    'email_prefix': email.split('@')[0] if '@' in email else 'unknown',
                    'client_ip': client_ip,
                    'success': False,
                    'reason': 'multiple_users_same_email'
                }
            )
            
            # Si hay múltiples usuarios con el mismo email (error de datos)
            return Response(
                {"detail": "Error en el sistema. Contacte al administrador."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            # Generar token de reset
            # Esto invalida automáticamente tokens anteriores
            reset_token = PasswordResetToken.generate_token(user)
            
            # Construir URL de reset
            # El frontend debe tener una página en /auth/reset-password
            frontend_url = settings.FRONTEND_URL or 'http://localhost:3000'
            reset_url = f"{frontend_url}/auth/reset-password?token={reset_token.token}"
            
            try:
                # Enviar email con el link de reset usando Celery
                from .tasks import send_password_reset_email
                send_password_reset_email.delay(email, reset_url)
                
                # Log envío de email exitoso
                logger.info(
                    f"Email de password reset enviado para usuario ID {user.id}",
                    extra={
                        'action': 'password_reset_email_sent',
                        'user_id': str(user.id),
                        'email_prefix': email.split('@')[0] if '@' in email else 'unknown',
                        'client_ip': client_ip,
                        'success': True
                    }
                )
                
            except Exception as e:
                # Log error al enviar email
                logger.error(
                    f"Error enviando email de password reset para usuario ID {user.id}: {str(e)}",
                    extra={
                        'action': 'password_reset_email_error',
                        'user_id': str(user.id),
                        'email_prefix': email.split('@')[0] if '@' in email else 'unknown',
                        'client_ip': client_ip,
                        'error': str(e)
                    },
                    exc_info=True
                )
                # Si falla el envío de email, registrar error pero no fallar la request
                # Esto evita revelar si el email existe
        
        except Exception as e:
            # Log error general
            logger.error(
                f"Error generando token de password reset para usuario ID {user.id}: {str(e)}",
                extra={
                    'action': 'password_reset_token_error',
                    'user_id': str(user.id),
                    'email_prefix': email.split('@')[0] if '@' in email else 'unknown',
                    'client_ip': client_ip,
                    'error': str(e)
                },
                exc_info=True
            )
        
        # Siempre retornar éxito (por seguridad)
        # No revelar si el email existe o no en el sistema
        return Response({
            "message": "Si el email existe, se envió un enlace de recuperación."
        }, status=200)


class PasswordResetConfirmView(APIView):
    """
    Vista para confirmar y cambiar la contraseña con token.
    
    Endpoint: POST /api/v1/auth/password-reset/confirm/
    
    Permisos:
    - Público (AllowAny) - pero requiere token válido
    
    Funcionalidad:
    1. Valida el token de reset
    2. Verifica que el token no haya expirado ni sido usado
    3. Valida la nueva contraseña
    4. Cambia la contraseña del usuario
    5. Marca el token como usado
    6. Retorna éxito
    
    Relaciones:
    - Usa PasswordResetToken para validar token
    - Usa User.set_password() para cambiar contraseña
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Confirma el reset de contraseña.
        
        Parámetros (body JSON):
        - token: Token de reset obtenido del email
        - new_password: Nueva contraseña
        - confirm_password: Confirmación de nueva contraseña
        
        Retorna:
        - 200: Contraseña cambiada exitosamente
        - 400: Token inválido, expirado, o contraseñas no coinciden
        """
        from .serializers import PasswordResetConfirmSerializer
        from .models import PasswordResetToken
        from django.utils import timezone
        
        # Validar datos
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token_str = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            # Buscar token
            reset_token = PasswordResetToken.objects.get(
                token=token_str,
                used=False
            )
            
            # Verificar que no haya expirado
            if not reset_token.is_valid():
                return Response(
                    {"detail": "El token ha expirado o ya fue usado."},
                    status=400
                )
            
            # Cambiar contraseña
            user = reset_token.user
            user.set_password(new_password)  # Hashea la contraseña automáticamente
            user.save()
            
            # Marcar token como usado
            reset_token.used = True
            reset_token.save()
            
            # Registrar auditoría
            from apps.workorders.models import Auditoria
            Auditoria.objects.create(
                usuario=user,
                accion="PASSWORD_RESET",
                objeto_tipo="User",
                objeto_id=str(user.id),
                payload={}
            )
            
            return Response({"message": "Contraseña actualizada correctamente."})
        
        except PasswordResetToken.DoesNotExist:
            return Response(
                {"detail": "Token inválido."},
                status=400
            )


class ChangePasswordView(APIView):
    """
    Vista para que un usuario cambie su propia contraseña.
    
    Endpoint: POST /api/v1/auth/change-password/
    
    Permisos:
    - Requiere autenticación (IsAuthenticated)
    
    Funcionalidad:
    1. Verifica la contraseña actual
    2. Valida la nueva contraseña
    3. Cambia la contraseña
    4. Actualiza la sesión para evitar logout
    5. Registra auditoría
    
    Uso:
    - Llamado desde /profile/change-password en el frontend
    - Permite a usuarios cambiar su contraseña sin recuperación
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Cambia la contraseña del usuario logueado.
        
        Parámetros (body JSON):
        - current_password: Contraseña actual (para verificar)
        - new_password: Nueva contraseña
        - confirm_password: Confirmación de nueva contraseña
        
        Retorna:
        - 200: Contraseña cambiada exitosamente
        - 400: Contraseña actual incorrecta o validación falla
        """
        from .serializers import ChangePasswordSerializer
        from django.contrib.auth import update_session_auth_hash
        from rest_framework import status
        
        # Validar datos
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Verificar contraseña actual
        if not user.check_password(serializer.validated_data['current_password']):
            return Response(
                {"detail": "La contraseña actual es incorrecta."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cambiar contraseña
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Actualizar sesión para evitar logout
        # Esto mantiene al usuario autenticado después del cambio
        update_session_auth_hash(request, user)
        
        # Registrar auditoría
        from apps.workorders.models import Auditoria
        Auditoria.objects.create(
            usuario=user,
            accion="CAMBIAR_PASSWORD",
            objeto_tipo="User",
            objeto_id=str(user.id),
            payload={}
        )
        
        return Response({"message": "Contraseña actualizada correctamente."})


class AdminChangePasswordView(APIView):
    """
    Vista para que un admin cambie la contraseña de otro usuario.
    
    Endpoint: POST /api/v1/users/{user_id}/change-password/
    
    Permisos:
    - Requiere autenticación
    - Solo ADMIN o SUPERVISOR pueden cambiar contraseñas de otros
    
    Funcionalidad:
    1. Verifica que el usuario sea ADMIN o SUPERVISOR
    2. Busca el usuario objetivo
    3. Valida la nueva contraseña
    4. Cambia la contraseña
    5. Registra auditoría
    
    Uso:
    - Llamado desde /users/{id}/change-password en el frontend
    - Permite a admins resetear contraseñas sin conocer la actual
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id=None):
        """
        Cambia la contraseña de otro usuario.
        
        Parámetros:
        - user_id: ID del usuario cuya contraseña se cambiará (path parameter)
        
        Body JSON:
        - new_password: Nueva contraseña
        - confirm_password: Confirmación de nueva contraseña
        
        Retorna:
        - 200: Contraseña cambiada exitosamente
        - 403: Usuario no tiene permisos
        - 404: Usuario objetivo no encontrado
        - 400: Error de validación
        """
        from .serializers import AdminChangePasswordSerializer
        from rest_framework import status
        
        # Verificar que el usuario sea ADMIN o SUPERVISOR
        if request.user.rol not in ("ADMIN", "SUPERVISOR"):
            return Response(
                {"detail": "No tienes permisos para cambiar contraseñas de otros usuarios."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar datos
        serializer = AdminChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Buscar usuario objetivo
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Cambiar contraseña
        target_user.set_password(serializer.validated_data['new_password'])
        target_user.save()
        
        # Registrar auditoría
        from apps.workorders.models import Auditoria
        Auditoria.objects.create(
            usuario=request.user,  # Quien hizo el cambio
            accion="ADMIN_CAMBIAR_PASSWORD",
            objeto_tipo="User",
            objeto_id=str(target_user.id),
            payload={"target_user": target_user.username}  # Usuario afectado
        )
        
        return Response({"message": f"Contraseña de {target_user.username} actualizada correctamente."})

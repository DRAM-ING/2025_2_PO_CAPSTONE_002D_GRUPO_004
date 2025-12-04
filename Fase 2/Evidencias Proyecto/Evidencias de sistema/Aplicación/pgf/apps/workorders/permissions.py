from rest_framework.permissions import BasePermission, SAFE_METHODS

"""
Permisos para órdenes de trabajo según especificación de roles:

1. GUARDIA: Puede crear OT a través del flujo de ingreso de vehículos (es el primer actor del proceso)
2. CHOFER: Solo lectura de su vehículo/OT
3. MECANICO: Puede cambiar estados pero NO cerrar OT
4. JEFE_TALLER: Puede crear/editar/cerrar OT
5. SUPERVISOR: Solo lectura de OT de su zona (NO crear/cerrar)
6. COORDINADOR_ZONA: Puede ver OT de su zona (NO cerrar)
7. SPONSOR: Solo lectura completa (NO editar/cerrar)
8. ADMIN: Gestión técnica (NO operativa - no crear/editar OT)
"""

# Roles que pueden leer OT
ALLOWED_ROLES_READ = {
    "ADMIN", "SUPERVISOR", "MECANICO", "GUARDIA", "JEFE_TALLER", 
    "COORDINADOR_ZONA", "SPONSOR", "CHOFER", "EJECUTIVO",
    "ADMINISTRATIVO_TALLER", "BODEGA"
}

# Roles que pueden crear OT directamente (solo Jefe de Taller)
# NOTA: GUARDIA puede crear OT a través del flujo de ingreso de vehículos (automático)
# pero NO puede crear OTs manualmente
# ADMIN puede crear OTs para gestión técnica/soporte
ALLOWED_ROLES_CREATE = {"JEFE_TALLER", "ADMIN"}

# Roles que pueden editar OT (Jefe de Taller, Admin, Administrativo de Taller - campos limitados, Coordinador de Zona)
ALLOWED_ROLES_UPDATE = {"JEFE_TALLER", "ADMIN", "ADMINISTRATIVO_TALLER", "COORDINADOR_ZONA"}

# Roles que pueden cerrar OT (solo Jefe de Taller)
ALLOWED_ROLES_CLOSE = {"JEFE_TALLER"}

# Roles que pueden cambiar estados (Mecánico y Jefe de Taller)
ALLOWED_ROLES_CHANGE_STATE = {"MECANICO", "JEFE_TALLER"}

# Roles que pueden asignar mecánicos (solo Jefe de Taller)
ALLOWED_ROLES_ASSIGN = {"JEFE_TALLER"}

# Roles que pueden crear evidencias (Mecánico, Guardia, Jefe de Taller, Admin)
# NOTA: Guardia solo puede subir evidencias de ingreso, no de OTs
ALLOWED_ROLES_CREATE_EVIDENCIA = {"MECANICO", "ADMIN", "GUARDIA", "JEFE_TALLER"}

# Roles que pueden ver/listar/descargar evidencias
# Jefe de Taller: todas las evidencias
# Supervisor Zonal: todas las evidencias (solo lectura)
# Administrador: todas las evidencias
# Mecánico: evidencias que él subió o de la OT en la que trabaja
# Guardia: evidencias iniciales que registró
# Administrativo: todas las evidencias del taller (solo lectura)
# Bodega: evidencias relacionadas con repuestos (solo lectura)
# Coordinador: todas las evidencias (solo lectura)
# Ejecutivo: todas las evidencias (solo lectura)
ALLOWED_ROLES_VIEW_EVIDENCIA = {
    "JEFE_TALLER", "SUPERVISOR", "ADMIN", "MECANICO",
    "ADMINISTRATIVO_TALLER", "BODEGA", "COORDINADOR_ZONA", "EJECUTIVO", "SPONSOR"
}

# Roles que pueden crear comentarios (Mecánico, Supervisor, Admin, Jefe de Taller)
ALLOWED_ROLES_CREATE_COMENTARIO = {"MECANICO", "SUPERVISOR", "ADMIN", "JEFE_TALLER", "GUARDIA", "COORDINADOR_ZONA"}


class WorkOrderPermission(BasePermission):
    """
    Permisos para órdenes de trabajo según especificación detallada de roles.
    """
    message = "Permisos insuficientes."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        rol = getattr(user, "rol", None)

        # Métodos de lectura: todos los roles autorizados pueden leer
        if request.method in SAFE_METHODS:
            # Para evidencias, usar permisos específicos
            is_evidencia_view = False
            if view:
                serializer_class = getattr(view, 'serializer_class', None)
                if serializer_class:
                    serializer_name = serializer_class.__name__ if hasattr(serializer_class, '__name__') else ""
                    is_evidencia_view = "Evidencia" in serializer_name
                
                if not is_evidencia_view:
                    view_class_name = view.__class__.__name__ if hasattr(view, '__class__') else ""
                    is_evidencia_view = "Evidencia" in view_class_name
                
                if not is_evidencia_view:
                    queryset = getattr(view, 'queryset', None)
                    if queryset and hasattr(queryset, 'model'):
                        model_name = queryset.model.__name__ if hasattr(queryset.model, '__name__') else ""
                        is_evidencia_view = "Evidencia" in model_name
            
            if not is_evidencia_view and hasattr(request, 'path'):
                is_evidencia_view = "/evidencias/" in request.path or "/evidencia/" in request.path
            
            if is_evidencia_view:
                # ADMIN siempre tiene acceso total a evidencias
                if rol == "ADMIN":
                    return True
                return rol in ALLOWED_ROLES_VIEW_EVIDENCIA
            
            return rol in ALLOWED_ROLES_READ

        # Métodos de escritura: según el rol específico
        action = getattr(view, 'action', None) if view else None
        
        # Detectar si es EvidenciaViewSet, PausaViewSet, ChecklistViewSet, ComentarioViewSet
        # Método más confiable: verificar el serializer_class o el queryset
        is_evidencia_view = False
        is_comentario_view = False
        is_pausa_view = False
        is_checklist_view = False
        if view:
            # Método 1: Por serializer_class (más confiable)
            serializer_class = getattr(view, 'serializer_class', None)
            if serializer_class:
                serializer_name = serializer_class.__name__ if hasattr(serializer_class, '__name__') else ""
                is_evidencia_view = "Evidencia" in serializer_name
                is_comentario_view = "Comentario" in serializer_name
                is_pausa_view = "Pausa" in serializer_name
                is_checklist_view = "Checklist" in serializer_name
            
            # Método 2: Por nombre de clase
            if not is_evidencia_view and not is_comentario_view and not is_pausa_view and not is_checklist_view:
                view_class_name = view.__class__.__name__ if hasattr(view, '__class__') else ""
                is_evidencia_view = "Evidencia" in view_class_name
                is_comentario_view = "Comentario" in view_class_name
                is_pausa_view = "Pausa" in view_class_name
                is_checklist_view = "Checklist" in view_class_name
            
            # Método 3: Por queryset model
            if not is_evidencia_view and not is_comentario_view and not is_pausa_view and not is_checklist_view:
                queryset = getattr(view, 'queryset', None)
                if queryset and hasattr(queryset, 'model'):
                    model_name = queryset.model.__name__ if hasattr(queryset.model, '__name__') else ""
                    is_evidencia_view = "Evidencia" in model_name
                    is_comentario_view = "Comentario" in model_name
                    is_pausa_view = "Pausa" in model_name
                    is_checklist_view = "Checklist" in model_name
        
        # Método 4: Por path de la URL (fallback)
        if not is_evidencia_view and not is_comentario_view and not is_pausa_view and not is_checklist_view and hasattr(request, 'path'):
            is_evidencia_view = "/evidencias/" in request.path or "/evidencia/" in request.path
            is_comentario_view = "/comentarios/" in request.path or "/comentario/" in request.path
            is_pausa_view = "/pausas/" in request.path or "/pausa/" in request.path
            is_checklist_view = "/checklists/" in request.path or "/checklist/" in request.path
        
        # Crear evidencia: Mecánico, Supervisor, Admin, Guardia, Jefe de Taller
        if request.method == "POST" and action == "create" and is_evidencia_view:
            # ADMIN siempre puede crear evidencias
            if rol == "ADMIN":
                return True
            return rol in ALLOWED_ROLES_CREATE_EVIDENCIA
        
        # Crear comentario: Mecánico, Supervisor, Admin, Jefe de Taller, Guardia, Coordinador
        if request.method == "POST" and action == "create" and is_comentario_view:
            return rol in ALLOWED_ROLES_CREATE_COMENTARIO
        
        # Crear pausa: Mecánico, Supervisor, Admin, Jefe de Taller
        if request.method == "POST" and action == "create" and is_pausa_view:
            return rol in {"MECANICO", "SUPERVISOR", "ADMIN", "JEFE_TALLER"}
        
        # Crear checklist: Supervisor, Admin, Jefe de Taller
        if request.method == "POST" and action == "create" and is_checklist_view:
            return rol in {"SUPERVISOR", "ADMIN", "JEFE_TALLER"}
        
        # Actualizar pausa: Mecánico (su propia pausa), Supervisor, Admin, Jefe de Taller
        if request.method in ("PUT", "PATCH") and action in ("update", "partial_update", None) and is_pausa_view:
            return rol in {"MECANICO", "SUPERVISOR", "ADMIN", "JEFE_TALLER"}
        
        # Actualizar checklist: Supervisor, Admin, Jefe de Taller
        if request.method in ("PUT", "PATCH") and action in ("update", "partial_update", None) and is_checklist_view:
            return rol in {"SUPERVISOR", "ADMIN", "JEFE_TALLER"}
        
        # Crear OT: solo Jefe de Taller y Admin
        if request.method == "POST" and action == "create":
            return rol in ALLOWED_ROLES_CREATE
        
        # Actualizar OT: Jefe de Taller, Admin y Administrativo de Taller (solo campos administrativos)
        if request.method in ("PUT", "PATCH") and action in ("update", "partial_update", None):
            # None se usa cuando action no está definido (puede pasar en algunos casos)
            if rol == "ADMINISTRATIVO_TALLER":
                # Administrativo puede actualizar campos administrativos (fechas, costos, tiempos)
                # pero no puede cambiar estado, mecánico, etc.
                return True
            return rol in ALLOWED_ROLES_UPDATE
        
        # Eliminar evidencias: ADMIN, JEFE_TALLER, MECANICO (sus propias), GUARDIA (sus propias)
        # La validación específica se hace en has_object_permission
        if request.method == "DELETE" and is_evidencia_view:
            # ADMIN siempre puede eliminar evidencias
            if rol == "ADMIN":
                return True
            # JEFE_TALLER puede eliminar evidencias
            if rol == "JEFE_TALLER":
                return True
            # MECANICO y GUARDIA pueden eliminar (se valida en has_object_permission si son suyas)
            if rol in ("MECANICO", "GUARDIA"):
                return True
            return False
        
        # Eliminar OT: solo Admin (gestión técnica)
        if request.method == "DELETE":
            return rol == "ADMIN"
        
        # Acciones personalizadas se validan en has_object_permission
        # Permitir POST para acciones personalizadas (se validan en la view)
        if request.method == "POST" and action not in ("create",):
            # ADMIN siempre tiene acceso
            if rol == "ADMIN":
                return True
            return rol in ALLOWED_ROLES_READ  # Permitir acceso, validación en view
        
        # ADMIN siempre tiene acceso para otros métodos (PUT, PATCH, DELETE en evidencias)
        if rol == "ADMIN" and is_evidencia_view:
            return True
        
        return False

    def has_object_permission(self, request, view, obj):
        """
        Valida permisos a nivel de objeto para acciones específicas.
        """
        if not request.user or not request.user.is_authenticated:
            return False

        rol = getattr(request.user, "rol", None)
        action = getattr(view, 'action', None) if view else None
        
        # Validar permisos específicos para evidencias
        from .models import Evidencia
        if isinstance(obj, Evidencia):
            # Jefe de Taller: puede ver todas las evidencias
            if rol == "JEFE_TALLER":
                # Jefe de Taller: acceso a todas las evidencias
                return True
            
            # Supervisor Zonal: acceso a todas las evidencias (solo lectura)
            if rol == "SUPERVISOR":
                # Solo lectura (GET), no puede editar ni eliminar
                if request.method in SAFE_METHODS:
                    return True
                return False
            
            # Administrador: acceso total (siempre permitir)
            if rol == "ADMIN":
                return True
            
            # Mecánico: solo evidencias que él subió o de la OT en la que trabaja
            if rol == "MECANICO":
                # Puede ver si él la subió
                if obj.subido_por == request.user:
                    # Puede ver, editar y eliminar sus propias evidencias
                    return True
                # Puede ver si es de una OT asignada a él
                if obj.ot and obj.ot.mecanico == request.user:
                    # Solo lectura para evidencias de OTs asignadas (no las puede eliminar)
                    if request.method in SAFE_METHODS:
                        return True
                    return False
                return False
            
            # Guardia: solo evidencias de ingreso que registró (no puede ver/editar evidencias de OTs)
            if rol == "GUARDIA":
                # Guardia solo puede ver evidencias de ingreso, no de OTs
                # Las evidencias de ingreso se manejan en otro modelo (EvidenciaIngreso)
                # Por lo tanto, no puede ver ni editar evidencias de OTs
                return False
            
            # Administrativo de Taller: puede ver todas las evidencias (solo lectura)
            if rol == "ADMINISTRATIVO_TALLER":
                if request.method in SAFE_METHODS:
                    return True
                # No puede editar ni eliminar evidencias
                return False
            
            # Bodega: puede ver evidencias relacionadas con repuestos (solo lectura)
            if rol == "BODEGA":
                if request.method in SAFE_METHODS:
                    # Verificar si la evidencia está relacionada con una OT que tiene repuestos
                    try:
                        from apps.inventory.models import SolicitudRepuesto
                        if obj.ot:
                            tiene_repuestos = SolicitudRepuesto.objects.filter(ot=obj.ot).exists()
                            return tiene_repuestos
                        return False
                    except Exception:
                        return False
                # No puede editar ni eliminar evidencias
                return False
            
            # Coordinador de Zona: puede ver todas las evidencias (solo lectura)
            if rol == "COORDINADOR_ZONA":
                if request.method in SAFE_METHODS:
                    return True
                # No puede editar ni eliminar evidencias
                return False
            
            # Ejecutivo: puede ver todas las evidencias (solo lectura)
            if rol == "EJECUTIVO":
                if request.method in SAFE_METHODS:
                    return True
                # No puede editar ni eliminar evidencias
                return False
            
            # Sponsor: puede ver todas las evidencias (solo lectura)
            if rol == "SPONSOR":
                if request.method in SAFE_METHODS:
                    return True
                # No puede editar ni eliminar evidencias
                return False
        
        # CHOFER solo puede ver OT de su vehículo asignado (solo lectura)
        if rol == "CHOFER":
            if request.method not in SAFE_METHODS:
                return False  # CHOFER no puede crear, editar ni eliminar OTs
            try:
                from apps.drivers.models import Chofer
                from .models import OrdenTrabajo
                
                # Buscar chofer asociado al usuario por RUT
                chofer = Chofer.objects.filter(rut=request.user.rut, activo=True).first()
                if chofer and chofer.vehiculo_asignado:
                    # Verificar que la OT sea del vehículo asignado al chofer
                    if isinstance(obj, OrdenTrabajo):
                        return obj.vehiculo == chofer.vehiculo_asignado
                # Si no tiene vehículo asignado, no puede ver ninguna OT
                return False
            except Exception:
                return False
        
        # Para actualizaciones de OT, validar permisos específicos
        from .models import OrdenTrabajo
        if isinstance(obj, OrdenTrabajo):
            # Si es una actualización (PUT/PATCH), validar permisos
            if request.method in ("PUT", "PATCH"):
                # ADMINISTRATIVO_TALLER puede actualizar campos administrativos
                if rol == "ADMINISTRATIVO_TALLER":
                    return True
                # JEFE_TALLER y ADMIN pueden actualizar
                if rol in ALLOWED_ROLES_UPDATE:
                    return True
                return False
        
        # Para otros roles y operaciones, usar has_permission
        return True

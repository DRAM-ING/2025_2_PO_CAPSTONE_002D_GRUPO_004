from rest_framework.permissions import BasePermission

class UserPermission(BasePermission):
    def has_permission(self, request, view):
        # Registro público
        if view.action == 'create':
            return True

        # /me requiere autenticación (la view ya lo valida, pero por si acaso)
        if getattr(view, 'action', None) == 'me':
            return request.user and request.user.is_authenticated

        # Listar todos: admin, supervisor, jefe de taller, coordinador (necesitan ver mecánicos para asignar/coordinar)
        if view.action == 'list':
            return request.user and request.user.is_authenticated and request.user.rol in ["ADMIN", "SUPERVISOR", "JEFE_TALLER", "COORDINADOR_ZONA"]

        # Resto: autenticado
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Restricción especial: ningún usuario puede ver/editar el usuario 'admin' excepto el propio admin
        # Esta verificación debe ir ANTES de cualquier otra para tener prioridad
        if obj.username == "admin":
            # Solo el propio admin puede ver/editar el usuario admin
            return request.user.rol == "ADMIN" and request.user.username == "admin"

        # Prevenir eliminación de usuarios permanentes
        # Los usuarios permanentes solo se pueden ver y editar, nunca eliminar
        if view.action == 'destroy' and obj.is_permanent:
            return False

        # Si no es el usuario admin, aplicar permisos normales
        if request.user.rol in ["ADMIN", "SUPERVISOR", "JEFE_TALLER", "COORDINADOR_ZONA"]:
            return True

        # Un usuario puede ver/editar su propio objeto
        if view.action in ['retrieve', 'update', 'partial_update', 'me', 'destroy']:
            return obj == request.user

        return False
# Nota: destroy solo admin/supervisor, no lo permitimos a usuarios normales
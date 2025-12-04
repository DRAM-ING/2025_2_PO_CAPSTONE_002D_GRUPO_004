# apps/workorders/filters.py
import django_filters as filters
from django.db.models import Q
from .models import OrdenTrabajo

class OrdenTrabajoFilter(filters.FilterSet):
    estado = filters.CharFilter(field_name="estado", lookup_expr="iexact")
    apertura_from = filters.DateFilter(field_name="apertura", lookup_expr="date__gte")
    apertura_to   = filters.DateFilter(field_name="apertura", lookup_expr="date__lte")
    patente = filters.CharFilter(label="Patente", method="filter_patente")
    mecanico = filters.CharFilter(label="Mecánico", method="filter_mecanico")

    def filter_patente(self, queryset, name, value):
        return queryset.filter(Q(vehiculo__patente__icontains=value))
    
    def filter_mecanico(self, queryset, name, value):
        """
        Filtra por mecánico usando el ID (UUID).
        Maneja errores de formato UUID de forma más flexible.
        
        Si el usuario autenticado es MECANICO y se envía su propio ID,
        el filtro funciona correctamente con el filtrado automático de get_queryset.
        """
        if not value:
            return queryset
        
        try:
            import uuid
            # Limpiar el valor (quitar espacios, guiones, etc.)
            value_clean = str(value).strip()
            # Intentar convertir a UUID
            mecanico_uuid = uuid.UUID(value_clean)
            # Filtrar por mecanico_id (el campo ForeignKey)
            # Usar select_related para optimizar la consulta
            return queryset.filter(mecanico_id=mecanico_uuid).select_related('mecanico')
        except (ValueError, TypeError, AttributeError) as e:
            # Si no es un UUID válido, intentar buscar por username o nombre
            # Esto es útil para búsquedas más flexibles
            try:
                return queryset.filter(
                    Q(mecanico__username__icontains=str(value)) |
                    Q(mecanico__first_name__icontains=str(value)) |
                    Q(mecanico__last_name__icontains=str(value))
                ).select_related('mecanico')
            except Exception:
                # Si todo falla, retornar queryset sin filtrar (evitar error 400)
                # Pero loguear el error para debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error al filtrar por mecánico con valor '{value}': {e}")
                return queryset

    class Meta:
        model = OrdenTrabajo
        fields = ["id", "estado", "vehiculo", "mecanico"]
        order_by = filters.OrderingFilter(
            fields=(
                ('apertura', 'apertura'),
                ('estado', 'estado'),
            )
        )
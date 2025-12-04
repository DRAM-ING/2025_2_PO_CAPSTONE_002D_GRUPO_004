from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    OrdenTrabajoViewSet, ItemOTViewSet, PresupuestoViewSet, DetallePresupViewSet,
    AprobacionViewSet, PausaViewSet, ChecklistViewSet, EvidenciaViewSet,
    ComentarioOTViewSet, AuditoriaViewSet, PingView, timeline_ot, invalidar_evidencia
)

router = DefaultRouter()

# 🔥 PREFIJO CORRECTO PARA QUE EL FRONT FUNCIONE
router.register(r'ordenes', OrdenTrabajoViewSet, basename='orden-trabajo')
router.register(r'items', ItemOTViewSet, basename='item-ot')
router.register(r'presupuestos', PresupuestoViewSet, basename='presupuesto')
router.register(r'detalles-presupuesto', DetallePresupViewSet, basename='detalle-presupuesto')
router.register(r'aprobaciones', AprobacionViewSet, basename='aprobacion')
router.register(r'pausas', PausaViewSet, basename='pausa')
router.register(r'checklists', ChecklistViewSet, basename='checklist')
router.register(r'evidencias', EvidenciaViewSet, basename='evidencia')
router.register(r'comentarios', ComentarioOTViewSet, basename='comentario-ot')
router.register(r'auditoria', AuditoriaViewSet, basename='auditoria')

urlpatterns = router.urls + [
    path('ping/', PingView.as_view(), name='ping'),
    path('ordenes/<uuid:ot_id>/timeline/', timeline_ot, name='timeline-ot'),
    path('evidencias/<uuid:evidencia_id>/invalidar/', invalidar_evidencia, name='invalidar-evidencia'),
]

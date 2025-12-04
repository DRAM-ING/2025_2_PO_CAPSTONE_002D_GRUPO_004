# apps/inventory/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    RepuestoViewSet, StockViewSet, MovimientoStockViewSet,
    SolicitudRepuestoViewSet, HistorialRepuestoVehiculoViewSet
)

router = DefaultRouter()
router.register(r'repuestos', RepuestoViewSet, basename='repuesto')
router.register(r'stock', StockViewSet, basename='stock')
router.register(r'movimientos', MovimientoStockViewSet, basename='movimiento-stock')
router.register(r'solicitudes', SolicitudRepuestoViewSet, basename='solicitud-repuesto')
router.register(r'historial', HistorialRepuestoVehiculoViewSet, basename='historial-repuesto')

urlpatterns = router.urls


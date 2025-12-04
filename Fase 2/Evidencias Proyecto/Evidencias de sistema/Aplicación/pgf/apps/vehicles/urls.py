# apps/vehicles/urls.py

from rest_framework.routers import DefaultRouter
from apps.vehicles.views import (
    VehiculoViewSet,
    HistorialVehiculoViewSet,
    BackupVehiculoViewSet,
    BloqueoVehiculoViewSet
)

router = DefaultRouter()
router.register(r'', VehiculoViewSet, basename='vehicles')   # /api/v1/vehicles/
router.register(r'historial', HistorialVehiculoViewSet, basename='historial')  # /api/v1/vehicles/historial/
router.register(r'backups', BackupVehiculoViewSet, basename='backups')  # /api/v1/vehicles/backups/
router.register(r'bloqueos', BloqueoVehiculoViewSet, basename='bloqueos')  # /api/v1/vehicles/bloqueos/

urlpatterns = router.urls
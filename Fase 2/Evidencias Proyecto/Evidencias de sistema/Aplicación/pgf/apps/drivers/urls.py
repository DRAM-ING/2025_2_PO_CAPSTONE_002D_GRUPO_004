# apps/drivers/urls.py
from rest_framework.routers import DefaultRouter
from .views import ChoferViewSet, HistorialAsignacionVehiculoViewSet

router = DefaultRouter()
router.register(r'choferes', ChoferViewSet, basename='chofer')
router.register(r'historial', HistorialAsignacionVehiculoViewSet, basename='historial-asignacion')

urlpatterns = router.urls


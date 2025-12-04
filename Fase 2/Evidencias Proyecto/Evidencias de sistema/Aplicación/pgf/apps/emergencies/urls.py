# apps/emergencies/urls.py
from rest_framework.routers import DefaultRouter
from .views import EmergenciaRutaViewSet

router = DefaultRouter()
router.register(r'', EmergenciaRutaViewSet, basename='emergencia')

urlpatterns = router.urls


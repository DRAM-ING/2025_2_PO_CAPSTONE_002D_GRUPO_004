# apps/scheduling/urls.py
from rest_framework.routers import DefaultRouter
from .views import AgendaViewSet, CupoDiarioViewSet

router = DefaultRouter()
router.register(r'agendas', AgendaViewSet, basename='agenda')
router.register(r'cupos', CupoDiarioViewSet, basename='cupo')

urlpatterns = router.urls


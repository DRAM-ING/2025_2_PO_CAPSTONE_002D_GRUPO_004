# pgf_core/urls.py

from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf.urls.static import static
from rest_framework import routers

from apps.users.views import UserViewSet, ProfileViewSet
from apps.vehicles.views import VehiculoViewSet
from apps.workorders.views import  OrdenTrabajoViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'profiles', ProfileViewSet, basename='profiles')
router.register(r'vehicles', VehiculoViewSet, basename='vehicles')
router.register(r'work/ordenes',  OrdenTrabajoViewSet, basename='workorders')

urlpatterns = [

    # ----------------------------
    # ADMIN + DOCUMENTACIÓN
    # ----------------------------
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # DRF browsable API login/logout
    path("api-auth/", include("rest_framework.urls")),

    # ----------------------------
    # AUTH
    # ----------------------------
    path("api/v1/auth/", include("apps.users.auth_urls")),

    # ----------------------------
    # USERS
    # ----------------------------
    path("api/v1/users/", include("apps.users.urls")),

    # ----------------------------
    # VEHICLES
    # ----------------------------
    path("api/v1/vehicles/", include("apps.vehicles.urls")),

    # ----------------------------
    # WORKORDERS
    # ----------------------------
    path("api/v1/work/", include("apps.workorders.urls")),
    
    # ----------------------------
    # INVENTORY
    # ----------------------------
    path("api/v1/inventory/", include("apps.inventory.urls")),
    
    # ----------------------------
    # REPORTS
    # ----------------------------
    path("api/v1/reports/", include("apps.reports.urls")),
    
    # ----------------------------
    # DRIVERS (CHOFERES)
    # ----------------------------
    path("api/v1/drivers/", include("apps.drivers.urls")),
    
    # ----------------------------
    # SCHEDULING (AGENDA)
    # ----------------------------
    path("api/v1/scheduling/", include("apps.scheduling.urls")),
    
    # ----------------------------
    # EMERGENCIES (Deshabilitado)
    # ----------------------------
    # path("api/v1/emergencies/", include("apps.emergencies.urls")),
    
    # ----------------------------
    # NOTIFICATIONS
    # ----------------------------
    path("api/v1/", include("apps.notifications.urls")),
    
    # ----------------------------
    # MONITORING & HEALTH
    # ----------------------------
    path("api/v1/health/", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
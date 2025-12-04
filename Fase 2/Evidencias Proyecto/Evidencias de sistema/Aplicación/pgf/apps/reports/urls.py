# apps/reports/urls.py
from django.urls import path
from .views import (
    DashboardEjecutivoView,
    DashboardJefeTallerView,
    DashboardSupervisorView,
    DashboardCoordinadorView,
    DashboardSubgerenteView,
    ReporteProductividadView,
    ReportePausasView,
    ReportePDFView
)

urlpatterns = [
    path('dashboard-ejecutivo/', DashboardEjecutivoView.as_view(), name='dashboard-ejecutivo'),
    path('dashboard-jefe-taller/', DashboardJefeTallerView.as_view(), name='dashboard-jefe-taller'),
    path('dashboard-supervisor/', DashboardSupervisorView.as_view(), name='dashboard-supervisor'),
    path('dashboard-coordinador/', DashboardCoordinadorView.as_view(), name='dashboard-coordinador'),
    path('dashboard-subgerente/', DashboardSubgerenteView.as_view(), name='dashboard-subgerente'),
    path('productividad/', ReporteProductividadView.as_view(), name='reporte-productividad'),
    path('pausas/', ReportePausasView.as_view(), name='reporte-pausas'),
    path('pdf/', ReportePDFView.as_view(), name='reporte-pdf'),
]


from django.urls import path
from . import views

app_name = "sba"

urlpatterns = [
    path(
        "reporte/ingreso/<int:pk>/pdf/",
        views.pdf_reporte_ingreso,
        name="pdf_reporte_ingreso"
    ),

    path(
        "pdf/<int:pk>/",
        views.pdf_reporte_egreso,
        name="pdf_reporte_egreso"
    ),

    path(
        "pdf/<int:pk>/",
        views.pdf_reporte_financiero,
        name="pdf_reporte_financiero"
    ),

    path('reporte/movimiento/<int:pk>/pdf/', views.pdf_reporte_movimiento, name='pdf_reporte_movimiento'),

    path("manual-usuario/", views.manual_usuario_view, name="admin_manual_usuario"),

]





from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("cotista/<int:cotista_id>/extrato/", views.extrato_cotista_html, name="extrato_cotista_html"),
    path("relatorio/geral/pdf/", views.relatorio_geral_pdf, name="relatorio_geral_pdf"),
    path("relatorio/cotista/<int:cotista_id>/pdf/", views.extrato_cotista_pdf, name="extrato_cotista_pdf"),
]

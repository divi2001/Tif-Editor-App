from django.urls import path
from . import views

app_name = 'mainadmin'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('upload/', views.upload_pdf, name='upload_pdf'),
    path('edit/<int:pdf_id>/', views.edit_pdf, name='edit_pdf'),
    path('delete/<int:pdf_id>/', views.delete_pdf, name='delete_pdf'),
    path('download/<int:pdf_id>/', views.download_pdf, name='download_pdf'),
    path('pdf/<int:pdf_id>/toggle-like/', views.toggle_like, name='toggle_like'),
    path('pdfs/', views.pdf_list, name='pdf_list'),
    path('pdf/<int:pdf_id>/toggle-like/', views.toggle_like, name='toggle_like'),
]
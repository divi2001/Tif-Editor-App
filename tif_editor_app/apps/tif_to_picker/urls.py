# myapp/urls.py

from django.urls import path
from .views import upload_tiff,single_layer_color_picker,export_tiff,process_svg_upload,analyze_color,apply_color
from . import views

urlpatterns = [
    path('', upload_tiff, name='upload_tiff'),
    path('color-picker/', single_layer_color_picker, name='single_layer_color_picker'),
    path('export_tiff/', export_tiff, name='export_tiff'),
    path('upload-svg/', process_svg_upload, name='process_svg_upload'),
    path('analyze-color/', analyze_color, name='analyze-color'),
    path('apply-color/',apply_color,name='apply-color'),     
    path('inspiration-pdfs/', views.inspiration_view, name='inspiration_pdfs'),
]

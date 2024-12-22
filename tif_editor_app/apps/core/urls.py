from django.urls import path
from apps.core.views import contact_form_submission
from django.views.generic import TemplateView

urlpatterns = [
    path('contact/', contact_form_submission, name='contact'),
    path('contact/success/', TemplateView.as_view(template_name='pages/contact_success.html'), name='contact_success')
]
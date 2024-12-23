from django.urls import path
from apps.core.views import contact_form_submission
from django.views.generic import TemplateView

urlpatterns = [
    path('contact-form-submission/', contact_form_submission, name='contact-form-submission'),
]
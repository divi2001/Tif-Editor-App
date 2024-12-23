# apps/core/urls.py

from django.urls import path
from apps.core.views import contact_form_submission, create_new_project, project_list, rename_project, delete_project
from django.views.generic import TemplateView

urlpatterns = [
    path('contact-form-submission/', contact_form_submission, name='contact-form-submission'),
    path('create-new-project/', create_new_project, name='create-new-project'),
    path('projects/', project_list, name='project-list'),
    path('projects/<int:project_id>/rename/', rename_project, name='rename_project'),
    path('projects/<int:project_id>/delete/', delete_project, name='delete_project'),
]
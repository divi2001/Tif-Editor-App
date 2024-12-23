from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from .models import Contact, Project
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import get_object_or_404

User = get_user_model()

@require_http_methods(["GET", "POST"])
@login_required
def contact_form_submission(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        phone_number = request.POST.get('phone_number', '')

        if email != request.user.email:
            return JsonResponse({'status': 'error', 'message': "The email address must match your account email."})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': "User with this email does not exist."})

        try:
            contact = Contact(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                subject=subject,
                message=message,
                phone_number=phone_number
            )
            contact.full_clean()
            contact.save()
            return JsonResponse({'status': 'success', 'message': "Your message has been sent successfully!"})
        except ValidationError as e:
            errors = [f"{field}: {error}" for field, errors in e.message_dict.items() for error in errors]
            return JsonResponse({'status': 'error', 'message': errors})

    return render(request, 'pages/contact.html')


@login_required
@require_http_methods(["POST"])
def create_new_project(request):
    try:
        data = json.loads(request.body)
        new_project_name = Project.get_next_untitled_name(request.user)
        new_project = Project.objects.create(
            user=request.user,
            name=new_project_name,
            status='drafts',
            created_at=timezone.now()
        )
        return JsonResponse({
            'status': 'success',
            'message': 'New project created successfully',
            'project_id': new_project.id,
            'project_name': new_project.name
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
def project_list(request):
    projects = Project.objects.filter(user=request.user).exclude(status='deleted').order_by('-created_at')
    return render(request, 'projects/project_list.html', {'projects': projects})

@csrf_exempt
@login_required
@require_http_methods(["PUT"])
def rename_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    data = json.loads(request.body)
    new_name = data.get('name')
    
    if not new_name:
        return JsonResponse({'error': 'New name is required'}, status=400)
    
    project.name = new_name
    project.save()
    
    return JsonResponse({'message': 'Project renamed successfully', 'project': {'id': project.id, 'name': project.name}})

@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    project.delete()
    
    return JsonResponse({'message': 'Project deleted successfully'})
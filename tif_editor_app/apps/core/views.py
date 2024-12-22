import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Contact
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)

@login_required
def contact_form_submission(request):
    if request.method == 'POST':
        logger.debug(f"Received POST data: {request.POST}")
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        phone_number = request.POST.get('phone_number', '')

        logger.debug(f"Processed form data: {first_name}, {last_name}, {email}, {subject}, {message}, {phone_number}")

        if email != request.user.email:
            logger.warning(f"Email mismatch: form email {email}, user email {request.user.email}")
            messages.error(request, "The email address must match your account email.")
            return redirect('contact')

        try:
            user = User.objects.get(email=email)
            logger.debug(f"Found user: {user}")
        except User.DoesNotExist:
            logger.warning(f"User with email {email} does not exist")
            messages.error(request, "User with this email does not exist.")
            return redirect('contact')

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
            logger.info(f"Contact created: {contact}")
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact_success')
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('contact')

    return render(request, 'pages/contact.html')
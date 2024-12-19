# apps/api/views.py
from django.shortcuts import render

def home_view(request):
    return render(request, 'pages/home.html')

def about_view(request):
    return render(request, 'pages/about.html')

def plans_view(request):
    return render(request, 'pages/plans.html')

def contact_view(request):
    return render(request, 'pages/contact.html')

def privacy_policy_view(request):
    return render(request, 'pages/privacy_policy.html')

def terms_of_service_view(request):
    return render(request, 'pages/terms_of_service.html')
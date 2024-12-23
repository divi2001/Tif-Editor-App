from django.shortcuts import render, redirect
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import SubscriptionPlan, UserSubscription
from datetime import timedelta
import stripe
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from paypal.standard.forms import PayPalPaymentsForm


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from .models import Color

@require_POST
@staff_member_required
def update_color(request):
    color_id = request.POST.get('color_id')
    red = request.POST.get('red')
    green = request.POST.get('green')
    blue = request.POST.get('blue')

    try:
        color = Color.objects.get(id=color_id)
        color.red = int(red)
        color.green = int(green)
        color.blue = int(blue)
        color.save()
        return JsonResponse({'success': True})
    except Color.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Color not found'})
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid color values'})
    
    
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_free_trial(user):
    basic_plan = SubscriptionPlan.objects.get(name='Basic')
    UserSubscription.objects.create(
        user=user,
        plan=basic_plan,
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=7),  # 7-day free trial
        active=True
    )

@login_required
def subscribe_user(request, plan_id):
    plan = SubscriptionPlan.objects.get(id=plan_id)
    if request.method == 'POST':
        token = request.POST['stripeToken']
        email = request.POST['stripeEmail']

        customer = stripe.Customer.create(email=email, source=token)
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': plan.price}],
        )

        # Save subscription data
        UserSubscription.objects.create(
            user=request.user,
            plan=plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=plan.duration_in_days),
            active=True
        )
        return redirect('subscription_success')

    return render(request, 'subscribe.html', {'plan': plan})

def subscription_success(request):
    return render(request, 'success.html')

@login_required
def premium_feature(request):
    subscription = UserSubscription.objects.get(user=request.user)
    if subscription.is_active() and subscription.plan.name == 'Premium':
        return render(request, 'premium_feature.html')
    return redirect('subscribe')




def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            create_free_trial(user)
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})
@login_required
def access_premium_content(request):
    subscription = UserSubscription.objects.get(user=request.user)
    if subscription.is_active() and subscription.plan.name == 'Premium':
        return render(request, 'premium_content.html')
    return redirect('subscribe')


def paypal_view(request, plan_id):
    plan = SubscriptionPlan.objects.get(id=plan_id)
    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": str(plan.price),
        "item_name": f'{plan.name} Subscription',
        "invoice": "unique-invoice-id",
        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
        "return_url": request.build_absolute_uri(reverse('subscription_success')),
        "cancel_return": request.build_absolute_uri(reverse('payment_cancel')),
    }
    form = PayPalPaymentsForm(initial=paypal_dict)
    return render(request, 'paypal.html', {"form": form})
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)  # Plan name (e.g., 'Basic', 'Premium')
    price = models.DecimalField(max_digits=6, decimal_places=2)  # Price in USD
    duration_in_days = models.IntegerField()  # Plan duration (in days)

    def __str__(self):
        return self.name

class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)

    def is_active(self):
        return self.end_date > timezone.now() and self.active

    def __str__(self):
        return f'{self.user.username} - {self.plan.name}'

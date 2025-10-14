#subscription/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ('entry', 'Entry'),
        ('premium', 'Premium'),
        ('vip', 'VIP'),
    ]

    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2)
    yearly_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    free_monthly_tickets = models.PositiveIntegerField(default=0)
    ticket_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    is_popular = models.BooleanField(default=False)
    features = models.JSONField(default=list, blank=True, help_text="List of features included in the plan")
    
    stripe_price_id_monthly = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id_yearly = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        indexes = [models.Index(fields=['name'])]

    def yearly_price(self) -> Decimal:
        return self.monthly_price * Decimal('12') * (Decimal('1') - self.yearly_discount_percent / Decimal('100'))

    def __str__(self):
        return self.get_name_display()


class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    billing_cycle = models.CharField(max_length=10, choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')])
    
    last_usage_reset = models.DateTimeField(null=True, blank=True)
    
    monthly_tickets_used = models.PositiveIntegerField(default=0)
    yearly_tickets_used = models.PositiveIntegerField(default=0)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['stripe_subscription_id'])
        ]

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"

    def is_current(self):
        return self.is_active and self.end_date >= timezone.now().date()

    def get_discount(self) -> Decimal:
        if self.is_current():
            return self.plan.ticket_discount_percent
        return Decimal('0')

    def get_monthly_free_ticket_count(self) -> int:
        if self.is_current():
            return self.plan.free_monthly_tickets
        return 0
    
    def get_monthly_usable_ticket_count(self) -> int:

        if not self.is_current():
            return 0

        total = self.plan.free_monthly_tickets
        if self.billing_cycle == 'yearly':
            return max(total // 12, 1)  # prevent 0

        return total

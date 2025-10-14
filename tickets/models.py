# tickets/models.py
from django.db import models, transaction
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .utils import generate_ticket_id, generate_unique_purchase_id
from decimal import Decimal

User = get_user_model()

class GiveawayTicket(models.Model):
    ticket_id = models.CharField(
        max_length=10,
        unique=True,
        default=generate_ticket_id,
        editable=False
    )
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    total_available = models.PositiveIntegerField(default=0)
    ticket_expiry_date = models.DateField()
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Giveaway Ticket"
        verbose_name_plural = "Giveaway Tickets"

    def clean(self):
        # Only one active giveaway ticket allowed
        if self.ticket_expiry_date < timezone.now().date():
            raise ValidationError("Expiry date cannot be in the past.")
        if GiveawayTicket.objects.exclude(id=self.id).exists():
            raise ValidationError("Only one giveaway ticket can exist at a time.")

    @property
    def is_available(self):
        return self.total_available > 0 and self.ticket_expiry_date >= timezone.now().date()


class TicketPurchase(models.Model):
    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('subscription', 'Subscription'),
        ('first_time_bonus', 'First-Time Bonus'),
        ('purchase', 'Purchase'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ticket_purchases")
    ticket = models.ForeignKey(GiveawayTicket, on_delete=models.CASCADE, related_name="purchases")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unique_ticket_ids = models.JSONField(default=list, blank=True)
    is_used = models.BooleanField(default=False)
    purchase_date = models.DateTimeField(auto_now_add=True)

    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True)

    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='pending')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='purchase')

    class Meta:
        verbose_name = "Ticket Purchase"
        verbose_name_plural = "Ticket Purchases"
        ordering = ['-purchase_date']
        indexes = [
            models.Index(fields=['user', 'payment_status']),
            models.Index(fields=['ticket', 'is_used']),
        ]

    def clean(self):
        # Ensure ticket is available
        if not self.ticket.is_available:
            raise ValidationError("Cannot purchase expired or unavailable ticket.")
        # For paid purchases, check availability
        if self.source in ['manual', 'purchase']:
            if self.ticket.total_available < self.quantity:
                raise ValidationError("Not enough tickets available.")

    @property
    def is_free_ticket(self):
        # Tickets given by subscription or first time bonus are free
        return self.source in ['subscription', 'first_time_bonus']

    @property
    def total_price(self):
        if self.is_free_ticket:
            return Decimal('0.00')

        from subscription.models import UserSubscription

        subscription = UserSubscription.objects.filter(user=self.user, is_active=True).first()
        discount = subscription.get_discount() if subscription else Decimal('0')

        discount_rate = Decimal('1') - (discount / Decimal('100'))
        price = self.ticket.price * discount_rate

        return (price * self.quantity).quantize(Decimal('0.01'))

    @transaction.atomic    
    def confirm_purchase(self):
        if self.payment_status != 'succeeded':
            raise ValidationError("Cannot confirm purchase unless payment succeeded.")

        ticket = self.ticket

        # For free tickets, still reduce stock
        if ticket.total_available < self.quantity:
            raise ValidationError("Not enough tickets available to confirm purchase.")

        # Deduct ticket quantity
        ticket.total_available -= self.quantity
        ticket.save()

        # Generate unique ticket IDs if not already generated
        if not self.unique_ticket_ids or len(self.unique_ticket_ids) != self.quantity:
            self.unique_ticket_ids = [generate_unique_purchase_id() for _ in range(self.quantity)]

        # Always save self (even if IDs already existed)
        self.save()

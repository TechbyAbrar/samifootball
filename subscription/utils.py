#subscription/utils.py
from django.db import transaction
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta
import logging
from typing import Tuple
from .models import SubscriptionPlan, UserSubscription
from tickets.models import GiveawayTicket, TicketPurchase
from datetime import datetime

logger = logging.getLogger(__name__)

def calculate_subscription_end_date(billing_cycle: str, start_date: datetime = None) -> datetime:
    """Calculate subscription end date based on billing cycle."""
    start_date = start_date or now()
    if billing_cycle == 'yearly':
        return start_date + relativedelta(years=1)
    return start_date + relativedelta(months=1)

def get_subscription_benefits(plan_name: str) -> Tuple[int, float]:
    """Return free tickets and discount percentage for a plan."""
    plan = SubscriptionPlan.objects.get(name=plan_name)
    return plan.free_monthly_tickets, plan.ticket_discount_percent


from django.db import transaction
from django.utils.timezone import now
from tickets.utils import generate_unique_purchase_id
from tickets.models import GiveawayTicket, TicketPurchase
from subscription.models import UserSubscription
import logging

logger = logging.getLogger(__name__)

@transaction.atomic
def allocate_free_tickets(user_subscription_id):
    sub = UserSubscription.objects.select_for_update().get(id=user_subscription_id)
    user = sub.user
    current_month = now().date().replace(day=1)

    active_giveaway = GiveawayTicket.objects.filter(
        total_available__gt=0,
        ticket_expiry_date__gte=now().date()
    ).order_by('created_at').first()

    if not active_giveaway:
        raise Exception("No active giveaway ticket available.")

    # Check if this is user's first ticket allocation
    is_first_time = not TicketPurchase.objects.filter(user=user).exists()

    # Prevent reallocation in the same month for monthly users
    already_allocated = TicketPurchase.objects.filter(
        user=user,
        source='subscription',
        purchase_date__date__gte=current_month
    ).exists()

    ticket_count = 0
    bonus_count = 1 if is_first_time else 0

    if sub.billing_cycle == 'yearly':
        ticket_count = sub.plan.free_monthly_tickets * 12
    else:
        ticket_count = 0 if already_allocated else sub.plan.free_monthly_tickets

    total_allocated = 0

    # Allocate standard subscription tickets
    if ticket_count > 0:
        ticket_ids = [generate_unique_purchase_id() for _ in range(ticket_count)]
        TicketPurchase.objects.create(
            user=user,
            ticket=active_giveaway,
            quantity=ticket_count,
            unique_ticket_ids=ticket_ids,
            payment_status='succeeded',
            source='subscription'
        )
        active_giveaway.total_available -= ticket_count
        total_allocated += ticket_count

    # Allocate bonus ticket for first-time subscriber
    if bonus_count > 0:
        ticket_ids = [generate_unique_purchase_id()]
        TicketPurchase.objects.create(
            user=user,
            ticket=active_giveaway,
            quantity=1,
            unique_ticket_ids=ticket_ids,
            payment_status='succeeded',
            source='first_time_bonus'
        )
        active_giveaway.total_available -= 1
        total_allocated += 1

    if total_allocated > 0:
        active_giveaway.save()

    logger.info(f"[FREE TICKET ALLOCATED] user={user.email}, plan={sub.plan.name}, "
                f"standard={ticket_count}, bonus={bonus_count}, total={total_allocated}")

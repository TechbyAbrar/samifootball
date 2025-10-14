# from django.utils import timezone
# from datetime import timedelta
# import random
# import logging
# from django.db import transaction
# from .models import UserTicketConsolidation, UserTicketConsolidationArchive, RaffleWinner, GiveawayTicket

# logger = logging.getLogger(__name__)


# def reset_usage_if_needed(subscription):
#     now = timezone.now()

#     if not subscription.last_usage_reset:
#         # First time use, initialize
#         subscription.monthly_tickets_used = 0
#         subscription.yearly_tickets_used = 0
#         subscription.last_usage_reset = now
#         subscription.save(update_fields=['monthly_tickets_used', 'yearly_tickets_used', 'last_usage_reset'])
#         return

#     last_reset = subscription.last_usage_reset

#     if subscription.billing_cycle == 'monthly':
#         # Reset if month rolled over since last reset
#         if (now.year, now.month) != (last_reset.year, last_reset.month):
#             subscription.monthly_tickets_used = 0
#             subscription.last_usage_reset = now
#             subscription.save(update_fields=['monthly_tickets_used', 'last_usage_reset'])

#     elif subscription.billing_cycle == 'yearly':
#         # Reset if year rolled over since last reset
#         if now.year != last_reset.year:
#             subscription.yearly_tickets_used = 0
#             subscription.last_usage_reset = now
#             subscription.save(update_fields=['yearly_tickets_used', 'last_usage_reset'])
            
            

# def archive_and_clear_user_ticket_consolidation():
#     consolidations = list(UserTicketConsolidation.objects.all())
#     if not consolidations:
#         logger.info("No UserTicketConsolidation records to archive.")
#         return

#     archives = [
#         UserTicketConsolidationArchive(
#             user=c.user,
#             email=c.email,
#             full_name=c.full_name,
#             unique_ticket_ids=c.unique_ticket_ids,
#         ) for c in consolidations
#     ]

#     UserTicketConsolidationArchive.objects.bulk_create(archives)
#     UserTicketConsolidation.objects.all().delete()
#     logger.info(f"Archived and deleted {len(archives)} UserTicketConsolidation records.")


# def run_raffle_draw(winners_count: int, giveaway_id: int):
#     """
#     Runs a raffle draw for a given giveaway:
#     - Fetch all eligible tickets from UserTicketConsolidation
#     - Randomly pick `winners_count` unique tickets
#     - Save winners in RaffleWinner with positions "1st", "2nd", ...
#     - Archive & clear UserTicketConsolidation afterwards
#     """

#     eligible = []

#     # Fetch the giveaway object (raises DoesNotExist if not found)
#     giveaway = GiveawayTicket.objects.get(id=giveaway_id)

#     # Collect all (user, email, full_name, ticket_id) tuples
#     consolidations = UserTicketConsolidation.objects.all()
#     for consolidation in consolidations:
#         for ticket_id in consolidation.unique_ticket_ids:
#             eligible.append((consolidation.user, consolidation.email, consolidation.full_name, ticket_id))

#     if len(eligible) == 0:
#         raise ValueError("No eligible tickets found for raffle draw.")

#     winners_to_pick = min(winners_count, len(eligible))
#     selected_winners = random.sample(eligible, winners_to_pick)

#     position_labels = ['1st', '2nd', '3rd', '4th', '5th']

#     winners = []
#     with transaction.atomic():
#         for idx, (user, email, full_name, ticket_id) in enumerate(selected_winners):
#             position = position_labels[idx] if idx < len(position_labels) else f"{idx+1}th"
#             winner = RaffleWinner.objects.create(
#                 user=user,
#                 email=email,
#                 full_name=full_name,
#                 winning_ticket_id=ticket_id,
#                 position=position,
#                 giveaway=giveaway
#             )
#             winners.append(winner)

#         # Archive and clear consolidations after raffle
#         archive_and_clear_user_ticket_consolidation()

#     return winners

from django.utils import timezone
from datetime import timedelta
import random
import logging
from django.db import transaction
from .models import (
    UserTicketConsolidation,
    UserTicketConsolidationArchive,
    RaffleWinner,
    GiveawayTicket,
)
from django.core.mail import send_mail
from django.conf import settings


logger = logging.getLogger(__name__)


def reset_usage_if_needed(subscription):
    now = timezone.now()

    if not subscription.last_usage_reset:
        subscription.monthly_tickets_used = 0
        subscription.yearly_tickets_used = 0
        subscription.last_usage_reset = now
        subscription.save(update_fields=['monthly_tickets_used', 'yearly_tickets_used', 'last_usage_reset'])
        return

    last_reset = subscription.last_usage_reset

    if subscription.billing_cycle == 'monthly':
        if (now.year, now.month) != (last_reset.year, last_reset.month):
            subscription.monthly_tickets_used = 0
            subscription.last_usage_reset = now
            subscription.save(update_fields=['monthly_tickets_used', 'last_usage_reset'])

    elif subscription.billing_cycle == 'yearly':
        if now.year != last_reset.year:
            subscription.yearly_tickets_used = 0
            subscription.last_usage_reset = now
            subscription.save(update_fields=['yearly_tickets_used', 'last_usage_reset'])


def archive_and_clear_user_ticket_consolidation():
    consolidations = list(UserTicketConsolidation.objects.all())
    if not consolidations:
        logger.info("No UserTicketConsolidation records to archive.")
        return

    archives = [
        UserTicketConsolidationArchive(
            user=c.user,
            email=c.email,
            full_name=c.full_name,
            unique_ticket_ids=c.unique_ticket_ids,
        ) for c in consolidations
    ]

    UserTicketConsolidationArchive.objects.bulk_create(archives)

    # ✅ Validate successful archiving before deleting
    archived_count = UserTicketConsolidationArchive.objects.filter(
        user__in=[c.user for c in consolidations],
        email__in=[c.email for c in consolidations]
    ).count()

    if archived_count < len(archives):
        logger.error("Mismatch in archiving. Aborting deletion to avoid data loss.")
        raise Exception("Archiving failed. Data not deleted.")

    # ✅ Safe to delete after verification
    deleted_count, _ = UserTicketConsolidation.objects.all().delete()
    logger.info(f"Archived and deleted {deleted_count} UserTicketConsolidation records.")


def run_raffle_draw(winners_count: int, giveaway_id: int):
    eligible = []

    giveaway = GiveawayTicket.objects.filter(id=giveaway_id, is_active=True).first()
    if not giveaway:
        raise GiveawayTicket.DoesNotExist("Active giveaway not found.")

    consolidations = UserTicketConsolidation.objects.all()
    for consolidation in consolidations:
        for ticket_id in consolidation.unique_ticket_ids:
            eligible.append((consolidation.user, consolidation.email, consolidation.full_name, ticket_id))

    if len(eligible) == 0:
        raise ValueError("No eligible tickets found for raffle draw.")

    winners_to_pick = min(winners_count, len(eligible))
    selected_winners = random.sample(eligible, winners_to_pick)

    position_labels = ['1st', '2nd', '3rd', '4th', '5th']
    winners = []

    with transaction.atomic():
        for idx, (user, email, full_name, ticket_id) in enumerate(selected_winners):
            position = position_labels[idx] if idx < len(position_labels) else f"{idx+1}th"
            winner = RaffleWinner.objects.create(
                user=user,
                email=email,
                full_name=full_name,
                winning_ticket_id=ticket_id,
                position=position,
                giveaway=giveaway
            )
            winners.append(winner)

        # ✅ Archive and delete only inside transaction
        archive_and_clear_user_ticket_consolidation()

    logger.info(f"{winners_to_pick} winners selected for Giveaway ID: {giveaway_id}")
    return winners




def send_winner_congratulation_email(winner):
    """
    Sends a congratulatory plain-text email to a raffle winner with emojis and friendly formatting.
    
    Args:
        winner: RaffleWinner model instance
    """
    subject = f"🎉 Congratulations on Winning {winner.position} Place in Our Giveaway! 🎉"
    message = (
        f"✨ Dear {winner.full_name},\n\n"
        f"🥳 Congratulations! You have WON the {winner.position} place in our giveaway \"{winner.giveaway.title}\"!\n\n"
        f"🎟️ Your winning ticket ID: {winner.winning_ticket_id}\n\n"
        f"Thank you so much for your participation and support. We appreciate having you with us!\n\n"
        f"🌟 Stay tuned for upcoming giveaways and more chances to win!\n\n"
        f"Best wishes,\n"
        f"💫 The Giveaway Team"
    )
    recipient_list = [winner.email]

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        logger.info(f"Sent winner email to {winner.email} for position {winner.position}")
    except Exception as e:
        logger.error(f"Failed to send winner email to {winner.email}: {e}")

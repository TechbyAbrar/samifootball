# raffle/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from tickets.models import TicketPurchase
from subscription.models import UserSubscription
from .models import UserTicketConsolidation, UserTicketConsolidationArchive
from .serializers import UserTicketConsolidationSerializer, UserTicketConsolidationArchiveSerializer, RaffleWinnerArchiveSerializer
from tickets.models import GiveawayTicket
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from .utils import reset_usage_if_needed
from django.db.models import Prefetch
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# class ConsolidatedTicketsView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, user_id=None):
#         try:
#             user = request.user

#             if user_id is None:
#                 if not user.is_staff:
#                     return Response({
#                         'success': False,
#                         'message': 'You do not have permission to view all users.'
#                     }, status=status.HTTP_403_FORBIDDEN)
#                 user_queryset = User.objects.all()
#             else:
#                 if not user.is_staff and user.id != user_id:
#                     return Response({
#                         'success': False,
#                         'message': 'You are not allowed to access other users\' data.'
#                     }, status=status.HTTP_403_FORBIDDEN)
#                 user_queryset = User.objects.filter(id=user_id)

#             results = []
#             total_tickets = 0
#             total_users_with_tickets = 0

#             for user_obj in user_queryset:
#                 purchases = TicketPurchase.objects.filter(
#                     user=user_obj,
#                     payment_status='succeeded'
#                 ).only('id', 'unique_ticket_ids', 'source')

#                 if not purchases.exists():
#                     continue

#                 subscription = UserSubscription.objects.filter(
#                     user=user_obj,
#                     is_active=True
#                 ).only('billing_cycle', 'monthly_tickets_used', 'yearly_tickets_used', 'last_usage_reset', 'plan__free_monthly_tickets').first()

#                 fetched_ticket_ids = []
#                 purchases_to_update = []

#                 for purchase in purchases:
#                     original_ticket_ids = purchase.unique_ticket_ids or []
#                     used_now = original_ticket_ids[:]

#                     if purchase.source in ['subscription', 'first_time_bonus']:
#                         if subscription and subscription.billing_cycle == 'yearly':
#                             ticket_count = max(len(original_ticket_ids) // 12, 1)
#                             used_now = original_ticket_ids[:ticket_count]

#                     fetched_ticket_ids.extend(used_now)

#                     remaining = [t for t in original_ticket_ids if t not in used_now]
#                     if remaining != original_ticket_ids:
#                         purchase.unique_ticket_ids = remaining
#                         purchases_to_update.append(purchase)

#                 fetched_ticket_ids = list(dict.fromkeys(fetched_ticket_ids))
#                 if not fetched_ticket_ids:
#                     continue

#                 total_users_with_tickets += 1
#                 total_tickets += len(fetched_ticket_ids)

#                 with transaction.atomic():
#                     # Reset usage counters if period rolled over
#                     if subscription and subscription.is_active:
#                         reset_usage_if_needed(subscription)

#                     # Save/update consolidated tickets
#                     consolidation, _ = UserTicketConsolidation.objects.update_or_create(
#                         user=user_obj,
#                         defaults={
#                             'email': user_obj.email,
#                             'full_name': user_obj.full_name,
#                             'unique_ticket_ids': fetched_ticket_ids
#                         }
#                     )

#                     # Delete fetched tickets from TicketPurchase entries
#                     for purchase in purchases_to_update:
#                         purchase.save(update_fields=['unique_ticket_ids'])

#                     # Update subscription usage counters
#                     if subscription and subscription.is_active:
#                         if subscription.billing_cycle == 'monthly':
#                             used_count = len(fetched_ticket_ids)
#                             max_free = subscription.plan.free_monthly_tickets
#                             subscription.monthly_tickets_used = min(subscription.monthly_tickets_used + used_count, max_free)
#                             subscription.save(update_fields=['monthly_tickets_used'])
#                         elif subscription.billing_cycle == 'yearly':
#                             total_yearly_free = subscription.plan.free_monthly_tickets * 12
#                             used_count = len(fetched_ticket_ids)
#                             months_used_increment = used_count / max(total_yearly_free, 1) * 12
#                             new_yearly_used = subscription.yearly_tickets_used + months_used_increment
#                             subscription.yearly_tickets_used = min(new_yearly_used, 12)
#                             subscription.save(update_fields=['yearly_tickets_used'])

#                 serializer = UserTicketConsolidationSerializer(consolidation)
#                 results.append(serializer.data)

#             return Response({
#                 'success': True,
#                 'total_users_with_tickets': total_users_with_tickets,
#                 'total_tickets': total_tickets,
#                 'data': results
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             logger.error(f"Error in ConsolidatedTicketsView: {str(e)}")
#             return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class ConsolidatedTicketsView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, user_id=None):
#         try:
#             user = request.user

#             # Permission and user filtering
#             if user_id is None:
#                 if not user.is_staff:
#                     return Response({
#                         'success': False,
#                         'message': 'You do not have permission to view all users.'
#                     }, status=status.HTTP_403_FORBIDDEN)
#                 users = User.objects.all()
#             else:
#                 if not user.is_staff and user.id != user_id:
#                     return Response({
#                         'success': False,
#                         'message': 'You are not allowed to access other users\' data.'
#                     }, status=status.HTTP_403_FORBIDDEN)
#                 users = User.objects.filter(id=user_id)

#             # Optimized prefetching
#             users = users.prefetch_related(
#                 # Prefetch(
#                 #     'ticketpurchase_set',
#                 #     queryset=TicketPurchase.objects.filter(payment_status='succeeded')
#                 # ),
#                 Prefetch(
#                 'ticket_purchases',
#                 queryset=TicketPurchase.objects.filter(payment_status='succeeded')
#             ),
#                 Prefetch(
#                     'subscription',
#                     queryset=UserSubscription.objects.filter(is_active=True).select_related('plan')
#                 )
#             )

#             results = []
#             total_tickets = 0
#             total_users_with_tickets = 0
#             subscriptions_to_update = []
#             purchases_to_update = []

#             for user_obj in users:
#                 subscription = getattr(user_obj, 'subscription', None)
#                 ticket_purchases = list(user_obj.ticketpurchase_set.all())

#                 fetched_ticket_ids = []

#                 for purchase in ticket_purchases:
#                     original_ids = purchase.unique_ticket_ids or []
#                     used_now = original_ids[:]

#                     if purchase.source in ['subscription', 'first_time_bonus']:
#                         if subscription and subscription.billing_cycle == 'yearly':
#                             ticket_count = max(len(original_ids) // 12, 1)
#                             used_now = original_ids[:ticket_count]

#                     fetched_ticket_ids.extend(used_now)

#                     remaining = [t for t in original_ids if t not in used_now]
#                     if remaining != original_ids:
#                         purchase.unique_ticket_ids = remaining
#                         purchases_to_update.append(purchase)

#                 fetched_ticket_ids = list(dict.fromkeys(fetched_ticket_ids))
#                 if not fetched_ticket_ids:
#                     continue

#                 total_users_with_tickets += 1
#                 total_tickets += len(fetched_ticket_ids)

#                 with transaction.atomic():
#                     # Reset usage if needed
#                     if subscription:
#                         reset_usage_if_needed(subscription)

#                     # Save consolidated
#                     consolidation, _ = UserTicketConsolidation.objects.update_or_create(
#                         user=user_obj,
#                         defaults={
#                             'email': user_obj.email,
#                             'full_name': user_obj.full_name,
#                             'unique_ticket_ids': fetched_ticket_ids
#                         }
#                     )

#                     serializer = UserTicketConsolidationSerializer(consolidation)
#                     results.append(serializer.data)

#                     # Track subscription usage update
#                     if subscription:
#                         if subscription.billing_cycle == 'monthly':
#                             used = len(fetched_ticket_ids)
#                             max_free = subscription.plan.free_monthly_tickets
#                             subscription.monthly_tickets_used = min(
#                                 subscription.monthly_tickets_used + used, max_free
#                             )
#                             subscriptions_to_update.append(subscription)

#                         elif subscription.billing_cycle == 'yearly':
#                             used = len(fetched_ticket_ids)
#                             max_yearly = subscription.plan.free_monthly_tickets * 12
#                             months_used_inc = used / max(max_yearly, 1) * 12
#                             subscription.yearly_tickets_used = min(
#                                 subscription.yearly_tickets_used + months_used_inc, 12
#                             )
#                             subscriptions_to_update.append(subscription)

#             # Bulk update in the end for performance
#             if purchases_to_update:
#                 TicketPurchase.objects.bulk_update(purchases_to_update, ['unique_ticket_ids'])
#             if subscriptions_to_update:
#                 UserSubscription.objects.bulk_update(
#                     subscriptions_to_update, ['monthly_tickets_used', 'yearly_tickets_used']
#                 )

#             return Response({
#                 'success': True,
#                 'total_users_with_tickets': total_users_with_tickets,
#                 'total_tickets': total_tickets,
#                 'data': results
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             logger.error(f"Error in ConsolidatedTicketsView: {str(e)}")
#             return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConsolidatedTicketsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id=None):
        try:
            user = request.user

            # Permission check
            if user_id is None:
                if not user.is_staff:
                    return Response({
                        'success': False,
                        'message': 'You do not have permission to view all users. Only admin can access this.'
                    }, status=status.HTTP_403_FORBIDDEN)
                users = User.objects.all()
            else:
                if not user.is_staff and user.id != user_id:
                    return Response({
                        'success': False,
                        'message': 'You are not allowed to access other users\' data.'
                    }, status=status.HTTP_403_FORBIDDEN)
                users = User.objects.filter(id=user_id)

            # Prefetch related models
            users = users.prefetch_related(
                Prefetch(
                    'ticket_purchases',  # ✅ Correct related_name
                    queryset=TicketPurchase.objects.filter(payment_status='succeeded')
                ),
                Prefetch(
                    'subscription',
                    queryset=UserSubscription.objects.filter(is_active=True).select_related('plan')
                )
            )

            results = []
            total_tickets = 0
            total_users_with_tickets = 0
            subscriptions_to_update = []
            purchases_to_update = []

            for user_obj in users:
                subscription = getattr(user_obj, 'subscription', None)
                ticket_purchases = list(user_obj.ticket_purchases.all())  # ✅ Correct usage

                fetched_ticket_ids = []

                for purchase in ticket_purchases:
                    original_ids = purchase.unique_ticket_ids or []
                    used_now = original_ids[:]

                    # For yearly subscriptions, limit usage
                    if purchase.source in ['subscription', 'first_time_bonus']:
                        if subscription and subscription.billing_cycle == 'yearly':
                            ticket_count = max(len(original_ids) // 12, 1)
                            used_now = original_ids[:ticket_count]

                    fetched_ticket_ids.extend(used_now)

                    # Save remaining tickets
                    remaining = [t for t in original_ids if t not in used_now]
                    if remaining != original_ids:
                        purchase.unique_ticket_ids = remaining
                        purchases_to_update.append(purchase)

                # Deduplicate ticket IDs
                fetched_ticket_ids = list(dict.fromkeys(fetched_ticket_ids))
                if not fetched_ticket_ids:
                    continue

                total_users_with_tickets += 1
                total_tickets += len(fetched_ticket_ids)

                with transaction.atomic():
                    # Reset usage tracker if needed
                    if subscription:
                        reset_usage_if_needed(subscription)

                    # Save consolidated result
                    consolidation, _ = UserTicketConsolidation.objects.update_or_create(
                        user=user_obj,
                        defaults={
                            'email': user_obj.email,
                            'full_name': user_obj.full_name,
                            'unique_ticket_ids': fetched_ticket_ids
                        }
                    )

                    serializer = UserTicketConsolidationSerializer(consolidation)
                    results.append(serializer.data)

                    # Update ticket usage tracking
                    if subscription:
                        used = len(fetched_ticket_ids)

                        if subscription.billing_cycle == 'monthly':
                            max_free = subscription.plan.free_monthly_tickets
                            subscription.monthly_tickets_used = min(
                                subscription.monthly_tickets_used + used,
                                max_free
                            )
                            subscriptions_to_update.append(subscription)

                        elif subscription.billing_cycle == 'yearly':
                            max_yearly = subscription.plan.free_monthly_tickets * 12
                            months_used_inc = used / max(max_yearly, 1) * 12
                            subscription.yearly_tickets_used = min(
                                subscription.yearly_tickets_used + months_used_inc,
                                12
                            )
                            subscriptions_to_update.append(subscription)

            # Bulk save updates
            if purchases_to_update:
                TicketPurchase.objects.bulk_update(purchases_to_update, ['unique_ticket_ids'])

            if subscriptions_to_update:
                UserSubscription.objects.bulk_update(
                    subscriptions_to_update,
                    ['monthly_tickets_used', 'yearly_tickets_used']
                )
                
            all_consolidations = UserTicketConsolidation.objects.all().only('unique_ticket_ids')

            all_tickets = []
            for consolidation in all_consolidations:
                all_tickets.extend(consolidation.unique_ticket_ids or [])

            return Response({
                'success': True,
                'total_users_with_tickets': total_users_with_tickets,
                'total_tickets': total_tickets,
                'data': results,
                'spin_eligible_tickets': all_tickets
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in ConsolidatedTicketsView: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from .serializers import RaffleWinnerSerializer
from .utils import run_raffle_draw
from tickets.models import GiveawayTicket
from .utils import send_winner_congratulation_email 
from .models import RaffleWinner
import logging
import json

logger = logging.getLogger(__name__)


class RaffleDrawView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        winners_count = request.data.get('winners_count', 3)
        giveaway_id = request.data.get('giveaway_id')

        if not giveaway_id:
            return Response({
                'success': False,
                'message': 'giveaway_id is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            winners_count = int(winners_count)
            if winners_count < 1:
                raise ValueError()
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'message': 'winners_count must be a positive integer.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            winners = run_raffle_draw(winners_count, giveaway_id)
            serializer = RaffleWinnerSerializer(winners, many=True)

            # Send congratulation emails to winners
            for winner in winners:
                send_winner_congratulation_email(winner)

            # ✅ Log raffle metadata for auditing
            logger.info(json.dumps({
                'action': 'raffle_draw',
                'admin': request.user.email,
                'giveaway_id': giveaway_id,
                'winner_count': len(winners),
                'winners': serializer.data
            }, default=str))

            return Response({
                'success': True,
                'message': f'{len(winners)} winner(s) selected and notified.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except GiveawayTicket.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Active giveaway not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        except ValueError as ve:
            return Response({
                'success': False,
                'message': str(ve)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error during raffle draw: {str(e)}")
            return Response({
                'success': False,
                'message': 'Raffle draw failed due to an duplicate action.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class WinnerListView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        winners = RaffleWinner.objects.all().order_by('-created_at')
        serializer = RaffleWinnerSerializer(winners, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
        

class Spins_Eligible_tickets(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        try:
            all_consolidations = UserTicketConsolidation.objects.all().only('unique_ticket_ids')

            all_tickets = []
            for consolidation in all_consolidations:
                all_tickets.extend(consolidation.unique_ticket_ids or [])

            return Response({
                'success': True,
                'message': "Ticket numbers retrieved successfully.",
                'tickets': all_tickets
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ArchiveConsolidatedTicketsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            archived_tickets = UserTicketConsolidationArchive.objects.all().order_by('-archived_at')
            serializer = UserTicketConsolidationArchiveSerializer(archived_tickets, many=True)

            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in ArchiveConsolidatedTicketsView: {str(e)}")
            return Response({
                'success': False,
                'message': "An error occurred while retrieving archived tickets.",
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
# Delete Winner List & Archive Winners
from .models import RaffleWinnerArchive
from django.utils import timezone
from django.db import transaction
class WinnerDeleteAllView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request):
        winners = RaffleWinner.objects.all()
        count = winners.count()
        if count == 0:
            return Response({
                'success': True,
                'message': 'No winners found to archive and delete.'
            }, status=status.HTTP_200_OK)

        try:
            with transaction.atomic():
                archive_objs = [
                    RaffleWinnerArchive(
                        user=w.user,
                        email=w.email,
                        full_name=w.full_name,
                        winning_ticket_id=w.winning_ticket_id,
                        position=w.position,
                        giveaway=w.giveaway,
                        created_at=w.created_at,
                        archived_at=timezone.now()
                    ) for w in winners
                ]
                RaffleWinnerArchive.objects.bulk_create(archive_objs)
                winners.delete()

            logger.info(f"Admin user '{request.user.email}' archived and deleted all ({count}) raffle winners.")

            return Response({
                'success': True,
                'message': f'All {count} winners archived and deleted successfully. Please note that this action is irreversible. Check the archived winners list for details.',
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error archiving and deleting raffle winners by admin '{request.user.email}': {str(e)}")
            return Response({
                'success': False,
                'message': 'An error occurred while archiving and deleting winners. Please try again later. only admin can access this.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Archieve Winners List
class ArchivedWinnerListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        archived_winners = RaffleWinnerArchive.objects.all().order_by('-archived_at')
        serializer = RaffleWinnerArchiveSerializer(archived_winners, many=True)
        return Response({
            'success': True,
            'message': 'Archived winners retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
import logging
import stripe

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from .models import GiveawayTicket, TicketPurchase
from .serializers import (
    GiveawayTicketSerializer, UpdateGiveawayTicketSerializer, TicketPurchaseCreateSerializer, TicketPurchaseDetailsSerializer
)
from .utils import validate_quantity
from subscription.models import UserSubscription

from .pagination import StandardResultsSetPagination

from rest_framework.permissions import AllowAny


logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateGiveawayTicketView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = GiveawayTicketSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                cache.delete('giveaway_ticket')
                logger.info(f"Giveaway ticket created: {serializer.data['ticket_id']}")
                return Response({
                    'success': True,
                    'message': 'Giveaway ticket created successfully.',
                    'ticket': serializer.data
                    }, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "success": False,
            "message": "Only one active giveaway ticket is allowed at a time. After Raffle Draw or delete existing, you can create a new one.",
            'error': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class GiveawayTicketListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cached_ticket = cache.get('giveaway_ticket')

        if cached_ticket:
            serializer = GiveawayTicketSerializer(cached_ticket)
            return Response({
                "success": True,
                "message": "Active giveaway ticket retrieved successfully.",
                "ticket": serializer.data
            }, status=status.HTTP_200_OK)

        ticket = GiveawayTicket.objects.filter(
            total_available__gt=0,
            ticket_expiry_date__gte=timezone.now().date()
        ).first()

        if ticket:
            # cache.set('giveaway_ticket', ticket, timeout=3600)
            serializer = GiveawayTicketSerializer(ticket)
            return Response({
                "success": True,
                "message": "Active giveaway ticket retrieved successfully.",
                "ticket": serializer.data
            }, status=status.HTTP_200_OK)

        # If no active giveaway exists, find latest expired ticket (optional)
        latest_ticket = GiveawayTicket.objects.order_by('-ticket_expiry_date').first()
        if latest_ticket:
            serializer = GiveawayTicketSerializer(latest_ticket)
            return Response({
                "success": False,
                "message": f"The giveaway has expired on {latest_ticket.ticket_expiry_date}. No active giveaway is currently available.",
                "ticket": serializer.data
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "success": False,
            "message": "No giveaway tickets have been created yet."
        }, status=status.HTTP_404_NOT_FOUND)



class UpdateGiveawayTicketView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            ticket = GiveawayTicket.objects.get(pk=pk)
        except GiveawayTicket.DoesNotExist:
            return Response({"success": False, "message": "Giveaway ticket not found."},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateGiveawayTicketSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                cache.delete('giveaway_ticket')
                logger.info(f"Giveaway ticket updated: {ticket.ticket_id}")
                return Response({
                    "success": True,
                    "message": "Giveaway ticket updated successfully.",
                    "ticket": serializer.data
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error updating ticket {ticket.ticket_id}: {str(e)}")
                return Response({"success": False, "message": "Failed to update ticket."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"success": False, "errors": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            ticket = GiveawayTicket.objects.get(pk=pk)
        except GiveawayTicket.DoesNotExist:
            return Response({"success": False, "message": "Giveaway ticket not found."},
                            status=status.HTTP_404_NOT_FOUND)

        ticket_id = ticket.ticket_id
        ticket.delete()
        cache.delete('giveaway_ticket')
        logger.info(f"Giveaway ticket deleted: {ticket_id}")
        return Response({
            "success": True,
            "message": f"Giveaway ticket '{ticket_id}' has been deleted successfully."
        }, status=status.HTTP_200_OK)

# from decimal import Decimal
# from django.utils import timezone
# from subscription.permissions import IsSubscribed

# class PurchaseTicketView(APIView):
#     permission_classes = [IsAuthenticated, IsSubscribed]

#     @transaction.atomic
#     def post(self, request):
#         serializer = TicketPurchaseCreateSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         quantity = serializer.validated_data['quantity']
#         today = timezone.now().date()

#         try:
#             # Lock and get the first available ticket
#             ticket = GiveawayTicket.objects.select_for_update().filter(
#                 total_available__gt=0,
#                 ticket_expiry_date__gte=today
#             ).first()

#             if not ticket:
#                 return Response({"error": "No active giveaway ticket available."}, status=status.HTTP_404_NOT_FOUND)

#             # Validate quantity is available
#             validate_quantity(quantity, ticket.total_available)

#             # Get discount from subscription if exists
#             subscription = UserSubscription.objects.filter(user=request.user, is_active=True).first()
#             discount = Decimal(subscription.get_discount() if subscription else 0)

#             # Calculate discounted unit price
#             unit_price = ticket.price * (Decimal("1.00") - discount / Decimal("100"))
#             unit_price = unit_price.quantize(Decimal("0.01"))  # round to 2 decimals

#             # Create Stripe checkout session
#             checkout_session = stripe.checkout.Session.create(
#                 payment_method_types=['card'],
#                 line_items=[{
#                     'price_data': {
#                         'currency': 'usd',
#                         'unit_amount': int(unit_price * 100),  # Stripe expects cents
#                         'product_data': {'name': ticket.title},
#                     },
#                     'quantity': quantity,
#                 }],
#                 mode='payment',
#                 success_url=settings.SUCCESS_URL,
#                 cancel_url=settings.CANCEL_URL,
#                 metadata={
#                     'user_id': request.user.id,
#                     'ticket_id': ticket.ticket_id,
#                     'quantity': quantity,
#                 }
#             )

#             # Create the TicketPurchase record with status pending
#             purchase = TicketPurchase.objects.create(
#                 user=request.user,
#                 ticket=ticket,
#                 quantity=quantity,
#                 stripe_checkout_session_id=checkout_session.id,
#                 payment_status='pending'
#             )

#             logger.info(f"Purchase initiated | User: {request.user.email} | Purchase ID: {purchase.id}")
#             return Response({'success':True, 'message':'Successfully Added to Purchased.', "session_id": checkout_session.url}, status=status.HTTP_200_OK)

#         except ValidationError as e:
#             # Return detailed validation errors
#             return Response({
#                 'success': False,
#                 'message': 'Please, purchase a valid quantity of tickets. You can only purchase up to the available tickets.',
#                 "error": e.message if hasattr(e, 'message') else str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except stripe.error.StripeError as e:
#             logger.error(f"Stripe error: {str(e)}")
#             return Response({"error": "Payment processing failed."}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.exception("Unexpected error during ticket purchase.")
#             return Response({
#                 'success': False,
#                 'message': 'Please, purchase a valid quantity of tickets. You can only purchase up to the available tickets.',
#                 "error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TicketPurchaseListView(ListAPIView):
    serializer_class = TicketPurchaseDetailsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TicketPurchase.objects.filter(user=self.request.user, source='purchase').select_related('ticket', 'user')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        total_purchase_ticket_quantity = sum(item['quantity'] for item in serializer.data)
        
        return Response({
            'success': True,
            'message': 'Your purchased tickets retrieved successfully.',
            "purchase_tickets": serializer.data,
            "total_purchase_ticket_quantity": total_purchase_ticket_quantity,
        })
    
    

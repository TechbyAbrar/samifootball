# subscriptions/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import SubscriptionPlan, UserSubscription
from .serializers import SubscriptionPlanSerializer, MySubscriptionSerializer, SubscribeInputSerializer
from .utils import calculate_subscription_end_date, allocate_free_tickets
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.contrib.auth import get_user_model

User = get_user_model()

stripe.api_key = settings.STRIPE_SECRET_KEY


class AdminSubscriptionCRUDView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = SubscriptionPlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Subscription plan created successfully',
                'data': serializer.data
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, pk):
        plan = get_object_or_404(SubscriptionPlan, pk=pk)
        serializer = SubscriptionPlanSerializer(plan)
        return Response({
            'success': True,
            'message': 'Subscription plan fetched successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    

    def put(self, request, pk):
        plan = get_object_or_404(SubscriptionPlan, pk=pk)
        serializer = SubscriptionPlanSerializer(plan, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Subscription plan updated successfully',
                'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        plan = get_object_or_404(SubscriptionPlan, pk=pk)
        plan.delete()
        return Response({
            'success': True,
            'message': 'Subscription plan deleted successfully by Admin.'
            },status=status.HTTP_204_NO_CONTENT)


class PlansListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        plans = SubscriptionPlan.objects.all().order_by('monthly_price')
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response({
            'success': True,
            'message': 'All the Subscription plans retrieved successfully',
            'data': serializer.data
        })

class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubscribeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        name = serializer.validated_data['name']
        billing_cycle = serializer.validated_data['billing_cycle']

        try:
            plan = SubscriptionPlan.objects.get(name__iexact=name)
        except SubscriptionPlan.DoesNotExist:
            return Response({
                "detail": f"No subscription plan found for name '{name}'."}, status=404)

        # Check if user has any subscription record (active or inactive)
        existing_sub = UserSubscription.objects.filter(user=user).first()

        if existing_sub and existing_sub.is_active:
            return Response({
                'success': False,
                'message': 'User already have an active subscription.',
                "detail": "You already have an active subscription.Please cancel it first."}, status=400)

        stripe_price_id = (
            plan.stripe_price_id_monthly if billing_cycle == 'monthly'
            else plan.stripe_price_id_yearly
        )

        if not stripe_price_id:
            return Response({
                "detail": f"Stripe price ID not configured for {billing_cycle} billing of '{plan.name}'."
            }, status=400)

        try:
            checkout = stripe.checkout.Session.create(
                customer_email=user.email,
                payment_method_types=["card"],
                line_items=[{
                    'price': stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{settings.SUCCESS_URL}",
                cancel_url=f"{settings.CANCEL_URL}",
                metadata={
                    'user_id': str(user.id),
                    'plan_id': str(plan.id),
                    'billing_cycle': billing_cycle
                }
            )
        except Exception as e:
            return Response({"detail": f"Stripe error: {str(e)}"}, status=502)

        start_date = now().date()
        end_date = calculate_subscription_end_date(billing_cycle, start_date)

        if existing_sub:
            # Update existing subscription record (pending)
            existing_sub.plan = plan
            existing_sub.billing_cycle = billing_cycle
            existing_sub.start_date = start_date
            existing_sub.end_date = end_date
            existing_sub.is_active = False
            existing_sub.stripe_subscription_id = None
            existing_sub.save()
        else:
            # Create new subscription record
            UserSubscription.objects.create(
                user=user,
                plan=plan,
                billing_cycle=billing_cycle,
                start_date=start_date,
                end_date=end_date,
                is_active=False,  # pending subscription
                stripe_subscription_id=None,
            )

        return Response({
            "success": True,
            "message": "Checkout session created successfully.",
            "checkout_url": checkout.url
        }, status=201)



class MySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub = UserSubscription.objects.filter(user=request.user, is_active=True).first()
        if not sub:
            return Response({"detail": "No active subscription."}, status=404)
        serializer = MySubscriptionSerializer(sub)
        return Response({
            'success': True,
            'message': 'Your subscription details retrieved successfully',
            'data': serializer.data
        })


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sub = UserSubscription.objects.filter(user=request.user, is_active=True).first()
        if not sub:
            return Response({"detail": "No active subscription to cancel."}, status=400)

        try:
            stripe.Subscription.delete(sub.stripe_subscription_id)
            sub.is_active = False
            sub.save()
            return Response({
                'success': True,
                'message': 'Subscription cancelled successfully.',
                "detail": "Subscription cancelled."})
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=500)


from subscription.models import UserSubscription
from tickets.models import TicketPurchase
from tickets.serializers import TicketPurchaseDetailsSerializer

class MySubscriptionTicketsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        sub = UserSubscription.objects.filter(user=user, is_active=True).first()

        if not sub:
            return Response({"detail": "No active subscription found."}, status=404)

        # Get all tickets sourced from subscription or first-time bonus
        free_tickets = TicketPurchase.objects.filter(
            user=user,
            source__in=['subscription', 'first_time_bonus']
        ).order_by('-purchase_date')

        serializer = TicketPurchaseDetailsSerializer(free_tickets, many=True)

        subscription_data = {
            "plan": sub.plan.name,
            "billing_cycle": sub.billing_cycle,
            "start_date": sub.start_date,
            "end_date": sub.end_date,
            "is_active": sub.is_active,
        }

        return Response({
            'success': True,
            'message': 'Your subscription tickets retrieved successfully',
            "subscription": subscription_data,
            "free_tickets": serializer.data
        })



@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookSubscriptionView(APIView):
    permission_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = session['metadata']['user_id']
            plan_id = session['metadata']['plan_id']
            billing_cycle = session['metadata']['billing_cycle']
            stripe_sub_id = session['subscription']

            user = get_object_or_404(get_user_model(), id=user_id)
            plan = get_object_or_404(SubscriptionPlan, id=plan_id)

            start = now().date()
            end = calculate_subscription_end_date(billing_cycle, start)

            sub = UserSubscription.objects.filter(user_id=user_id).first()

            if sub:
                sub.plan = plan
                sub.billing_cycle = billing_cycle
                sub.start_date = start
                sub.end_date = end
                sub.is_active = True
                sub.stripe_subscription_id = stripe_sub_id
                sub.save()
            else:
                sub = UserSubscription.objects.create(
                    user=user,
                    plan=plan,
                    billing_cycle=billing_cycle,
                    start_date=start,
                    end_date=end,
                    is_active=True,
                    stripe_subscription_id=stripe_sub_id
                )

            allocate_free_tickets(sub.id)

        return Response(status=200)


#########


from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.utils import timezone
import stripe
import logging
from subscription.models import UserSubscription, SubscriptionPlan
from tickets.models import TicketPurchase
from django.conf import settings

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            return Response(status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return Response(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            metadata = session.get('metadata', {})

            # Check if the event is for a subscription (based on metadata)
            if metadata.get('user_id') and metadata.get('plan_id') and metadata.get('billing_cycle'):
                return self.handle_subscription_event(session)
            # Check if the event is for a purchase (based on session ID in TicketPurchase)
            elif TicketPurchase.objects.filter(stripe_checkout_session_id=session['id']).exists():
                return self.handle_purchase_event(session)
            else:
                logger.error("Webhook event does not match subscription or purchase criteria")
                return Response(status=400)

        return Response(status=200)

    def handle_subscription_event(self, session):
        user_id = session['metadata']['user_id']
        plan_id = session['metadata']['plan_id']
        billing_cycle = session['metadata']['billing_cycle']
        stripe_sub_id = session['subscription']

        user = get_object_or_404(get_user_model(), id=user_id)
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        start = timezone.now().date()
        end = calculate_subscription_end_date(billing_cycle, start)

        sub = UserSubscription.objects.filter(user_id=user_id).first()

        if sub:
            sub.plan = plan
            sub.billing_cycle = billing_cycle
            sub.start_date = start
            sub.end_date = end
            sub.is_active = True
            sub.stripe_subscription_id = stripe_sub_id
            sub.save()
            user.is_subscribed = True
            user.save()
        else:
            sub = UserSubscription.objects.create(
                user=user,
                plan=plan,
                billing_cycle=billing_cycle,
                start_date=start,
                end_date=end,
                is_active=True,
                stripe_subscription_id=stripe_sub_id
            )

        allocate_free_tickets(sub.id)
        logger.info(f"Subscription processed for user: {user_id}, subscription: {sub.id}")
        return Response(status=200)

    def handle_purchase_event(self, session):
        purchase = TicketPurchase.objects.filter(stripe_checkout_session_id=session['id']).first()

        if purchase and session.get('payment_status') == 'paid':
            purchase.payment_status = 'succeeded'
            purchase.stripe_payment_intent = session.get('payment_intent')

            try:
                purchase.confirm_purchase()
            except ValidationError as e:
                purchase.payment_status = 'failed'
                purchase.save()
                logger.error(f"Purchase confirmation failed: {str(e)}")
                return Response(status=400)
            except Exception as e:
                purchase.payment_status = 'failed'
                purchase.save()
                logger.exception(f"Unexpected error in purchase confirmation: {str(e)}")
                return Response(status=500)

            purchase.save()
            logger.info(f"Ticket purchase confirmed: {purchase.id}")
        else:
            logger.error(f"No valid purchase found or payment not completed for session: {session['id']}")
            return Response(status=400)

        return Response(status=200)
# subscriptions/urls.py
from django.urls import path
from .views import (
    AdminSubscriptionCRUDView,
    PlansListView,
    SubscribeView,
    StripeWebhookSubscriptionView,
    MySubscriptionView,
    CancelSubscriptionView,
    MySubscriptionTicketsView, StripeWebhookView
)

urlpatterns = [
    path('admin/subscription/', AdminSubscriptionCRUDView.as_view()),
    path('admin/subscription/<int:pk>/', AdminSubscriptionCRUDView.as_view()),
    path('plans/', PlansListView.as_view()),
    path('user-subscribe/', SubscribeView.as_view()),
    path('stripe/webhook/', StripeWebhookSubscriptionView.as_view()),
    path('my-subscription/', MySubscriptionView.as_view()),
    path('cancel-subscription/', CancelSubscriptionView.as_view()),
    path('my-subscription-tickets/', MySubscriptionTicketsView.as_view(), name='my-subscription-tickets'),
    path('webhook/', StripeWebhookView.as_view(), name='my-subscription-tickets'),

]

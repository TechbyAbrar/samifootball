# subscriptions/serializers.py
from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id','name', 'title', 'monthly_price', 'yearly_price', 'yearly_discount_percent', 'free_monthly_tickets',
                'ticket_discount_percent', 'is_popular', 'features',]
        
        read_only_fields = ['id', 'yearly_price', 'stripe_price_id_monthly', 'stripe_price_id_yearly']


class MySubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    free_tickets = serializers.SerializerMethodField()
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = ['plan_name', 'start_date', 'end_date', 'billing_cycle', 'is_active', 'is_current', 'free_tickets']

    def get_free_tickets(self, obj):
        return obj.get_monthly_free_ticket_count()

    def get_is_current(self, obj):
        return obj.is_current()
    
from rest_framework import serializers

class SubscribeInputSerializer(serializers.Serializer):
    # plan_id = serializers.IntegerField(required=True, help_text="ID of the subscription plan")
    name = serializers.CharField(max_length=20, required=True)
    billing_cycle = serializers.CharField(required=True)

    def validate_billing_cycle(self, value):
        value = value.lower()
        if value not in ['monthly', 'yearly']:
            raise serializers.ValidationError("Billing cycle must be 'monthly' or 'yearly'.")
        return value

    def validate_name(self, value):
        return value.strip().lower()




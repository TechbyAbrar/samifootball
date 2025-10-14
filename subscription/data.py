#subscription/data.py
from decimal import Decimal
from django.db import migrations
def create_subscription_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model('subscriptions', 'SubscriptionPlan')
    
    plans = [
        {
            'name': 'entry',
            'monthly_price': Decimal('10.00'),
            'free_monthly_tickets': 1,  # corrected key
            'ticket_discount_percent': Decimal('0.00')  # corrected key
        },
        {
            'name': 'premium',
            'monthly_price': Decimal('30.00'),
            'free_monthly_tickets': 4,
            'ticket_discount_percent': Decimal('15.00')
        },
        {
            'name': 'vip',
            'monthly_price': Decimal('60.00'),
            'free_monthly_tickets': 10,
            'ticket_discount_percent': Decimal('40.00')
        }
    ]
    
    for plan in plans:
        SubscriptionPlan.objects.create(**plan)

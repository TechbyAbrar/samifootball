from django.core.management.base import BaseCommand
from subscription.models import SubscriptionPlan
from django.conf import settings
from decimal import Decimal
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

class Command(BaseCommand):
    help = "Create monthly Stripe prices for all subscription plans"

    def handle(self, *args, **kwargs):
        plans = SubscriptionPlan.objects.all()

        for plan in plans:
            if plan.stripe_price_id_monthly:
                self.stdout.write(f"⚠️ Monthly price ID already exists for '{plan.name}'. Skipping.")
                continue

            if not getattr(plan, 'stripe_product_id', None):
                product = stripe.Product.create(name=f"{plan.get_name_display()} Plan")
                self.stdout.write(f"✅ Created Stripe product for plan '{plan.name}': {product.id}")
            else:
                product = stripe.Product.retrieve(plan.stripe_product_id)

            monthly_amount = int(plan.monthly_price * 100)  # amount in cents

            monthly_price = stripe.Price.create(
                unit_amount=monthly_amount,
                currency="usd",
                recurring={"interval": "month"},
                product=product.id,
            )
            plan.stripe_price_id_monthly = monthly_price.id
            plan.save()
            self.stdout.write(f"✅ Created monthly price for '{plan.name}': {monthly_price.id}")

        self.stdout.write(self.style.SUCCESS("🎉 All monthly Stripe prices processed successfully!"))

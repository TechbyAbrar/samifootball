from django.core.management.base import BaseCommand
from subscription.models import SubscriptionPlan
from django.conf import settings
from decimal import Decimal
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

class Command(BaseCommand):
    help = "Create yearly Stripe prices for all subscription plans"

    def handle(self, *args, **kwargs):
        plans = SubscriptionPlan.objects.all()

        for plan in plans:
            # Skip if yearly price already set
            if plan.stripe_price_id_yearly:
                self.stdout.write(f"⚠️ Yearly price ID already exists for '{plan.name}'. Skipping.")
                continue

            # Check if stripe product exists, else create it
            if not getattr(plan, 'stripe_product_id', None):
                product = stripe.Product.create(name=f"{plan.get_name_display()} Plan")
                # Optional: save product id if you add this field later
                # plan.stripe_product_id = product.id
                # plan.save()
                self.stdout.write(f"✅ Created Stripe product for plan '{plan.name}': {product.id}")
            else:
                product = stripe.Product.retrieve(plan.stripe_product_id)

            # Calculate yearly price with discount using your model method
            yearly_amount = int(plan.yearly_price() * 100)  # in cents

            # Create yearly price on Stripe
            yearly_price = stripe.Price.create(
                unit_amount=yearly_amount,
                currency="usd",
                recurring={"interval": "year"},
                product=product.id,
            )
            plan.stripe_price_id_yearly = yearly_price.id
            plan.save()
            self.stdout.write(f"✅ Created yearly price for '{plan.name}': {yearly_price.id}")

        self.stdout.write(self.style.SUCCESS("🎉 All yearly Stripe prices processed successfully!"))

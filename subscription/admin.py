from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name_display', 
        'monthly_price', 
        'yearly_discount_percent', 
        'free_monthly_tickets', 
        'ticket_discount_percent', 
        'yearly_price_display'
    )
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('monthly_price',)

    def name_display(self, obj):
        return obj.get_name_display()
    name_display.short_description = "Plan Name"

    def yearly_price_display(self, obj):
        return f"${obj.yearly_price():.2f}"
    yearly_price_display.short_description = "Yearly Price (after discount)"


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 
        'plan', 
        'start_date', 
        'end_date', 
        'is_active', 
        'is_current_status'
    )
    list_filter = ('plan', 'is_active', 'start_date', 'end_date')
    search_fields = ('user__email', 'stripe_subscription_id')
    ordering = ('-start_date',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User Email"

    def is_current_status(self, obj):
        return obj.is_current()
    is_current_status.boolean = True
    is_current_status.short_description = "Is Current"

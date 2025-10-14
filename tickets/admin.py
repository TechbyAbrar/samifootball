from django.contrib import admin
from .models import GiveawayTicket, TicketPurchase


@admin.register(GiveawayTicket)
class GiveawayTicketAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ticket_id',
        'title',
        'price',
        'total_available',
        'ticket_expiry_date',
        'is_available_status',
        'created_at',
        'updated_at',
    )
    list_filter = ('ticket_expiry_date', 'created_at')
    search_fields = ('ticket_id', 'title')
    ordering = ('-created_at',)

    def is_available_status(self, obj):
        return obj.is_available
    is_available_status.boolean = True
    is_available_status.short_description = "Available?"


@admin.register(TicketPurchase)
class TicketPurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_email',
        'ticket_title',
        'quantity',
        'total_price_display',
        'payment_status',
        'is_used',
        'purchase_date',
    )
    list_filter = ('payment_status', 'is_used', 'purchase_date')
    search_fields = ('user__email', 'stripe_payment_intent', 'stripe_checkout_session_id')
    ordering = ('-purchase_date',)
    readonly_fields = ('total_price_display', 'unique_ticket_ids')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User Email"

    def ticket_title(self, obj):
        return obj.ticket.title
    ticket_title.short_description = "Giveaway Ticket"

    def total_price_display(self, obj):
        return f"${obj.total_price:.2f}"
    total_price_display.short_description = "Total Price"

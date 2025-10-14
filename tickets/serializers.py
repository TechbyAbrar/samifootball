from rest_framework import serializers
from .models import GiveawayTicket, TicketPurchase
from django.contrib.auth import get_user_model

User = get_user_model()


class GiveawayTicketSerializer(serializers.ModelSerializer):
    is_available = serializers.ReadOnlyField()

    class Meta:
        model = GiveawayTicket
        fields = [
            'id',
            'ticket_id',
            'title',
            'description',
            'price',
            'total_available',
            'ticket_expiry_date',
            'is_available',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'ticket_id',
            'created_at',
            'updated_at',
            'is_available'
        ]

    def validate_title(self, value):
        if self.instance:
            if GiveawayTicket.objects.filter(title=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("A giveaway ticket with this title already exists.")
        else:
            if GiveawayTicket.objects.filter(title=value).exists():
                raise serializers.ValidationError("A giveaway ticket with this title already exists.")
        return value
    
    def validate(self, attrs):
        instance = GiveawayTicket(**attrs)
        if self.instance:
            instance.id = self.instance.id
        instance.full_clean() 
        return attrs
    
    
class UpdateGiveawayTicketSerializer(serializers.ModelSerializer):
    title = serializers.ReadOnlyField()  # Prevent updates

    class Meta:
        model = GiveawayTicket
        fields = [
            'title',
            'description',
            'price',
            'total_available',
            'ticket_expiry_date',
            'is_available',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['title','created_at', 'updated_at', 'is_available']

class TicketPurchaseCreateSerializer(serializers.ModelSerializer):
    # Read-only fields to show in response
    ticket_title = serializers.CharField(source='ticket.title', read_only=True)
    total_price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TicketPurchase
        # quantity is the only writable field
        fields = ['quantity', 'ticket_title', 'total_price']

    def get_total_price(self, obj):
        # obj is a TicketPurchase instance, use your model property
        return obj.total_price



# class TicketPurchaseDetailsSerializer(serializers.ModelSerializer):
#     user_email = serializers.EmailField(source='user.email', read_only=True)
#     ticket_title = serializers.CharField(source='ticket.title', read_only=True)
#     total_price = serializers.SerializerMethodField()
#     original_price_value = serializers.SerializerMethodField()
#     is_free = serializers.SerializerMethodField()
#     billing_source_label = serializers.SerializerMethodField()

#     class Meta:
#         model = TicketPurchase
#         fields = [
#             'id',
#             'user_email',
#             'ticket_title',
#             'quantity',
#             'unique_ticket_ids',
#             'is_used',
#             'purchase_date',
#             'payment_status',
#             'total_price',
#             'original_price_value',
#             'is_free',
#             'source',
#             'billing_source_label',
#         ]
#         read_only_fields = fields

#     def get_total_price(self, obj):
#         return obj.total_price

#     def get_original_price_value(self, obj):
#         if obj.ticket and obj.ticket.price:
#             return float(obj.ticket.price) * obj.quantity
#         return 0.0

#     def get_is_free(self, obj):
#         return obj.total_price == 0.0

#     def get_billing_source_label(self, obj):
#         return {
#             'subscription': 'Subscription Bonus',
#             'purchase': 'Manual Purchase',
#             'admin': 'Admin Granted',
#         }.get(obj.source, 'First Time Bonus')

class TicketPurchaseDetailsSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    ticket_title = serializers.CharField(source='ticket.title', read_only=True)
    total_price = serializers.SerializerMethodField()
    original_price_value = serializers.SerializerMethodField()
    is_free = serializers.SerializerMethodField()
    billing_source_label = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()  # override

    class Meta:
        model = TicketPurchase
        fields = [
            'id',
            'user_email',
            'ticket_title',
            'quantity',
            'unique_ticket_ids',
            'is_used',
            'purchase_date',
            'payment_status',
            'total_price',
            'original_price_value',
            'is_free',
            'source',
            'billing_source_label',
        ]
        read_only_fields = fields

    def get_total_price(self, obj):
        return obj.total_price

    def get_original_price_value(self, obj):
        if obj.ticket and obj.ticket.price:
            return float(obj.ticket.price) * obj.quantity
        return 0.0

    def get_is_free(self, obj):
        return obj.total_price == 0.0

    def get_billing_source_label(self, obj):
        return {
            'subscription': 'Subscription Bonus',
            'purchase': 'Manual Purchase',
            'admin': 'Admin Granted',
        }.get(obj.source, 'First Time Bonus')

    def get_quantity(self, obj):
        # If there are no unused ticket IDs, return 0
        if not obj.unique_ticket_ids:
            return 0
        return len(obj.unique_ticket_ids)

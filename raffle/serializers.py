from rest_framework import serializers
from .models import UserTicketConsolidation, RaffleWinner, UserTicketConsolidationArchive, RaffleWinnerArchive


class UserTicketConsolidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTicketConsolidation
        fields = ['id', 'email', 'full_name', 'unique_ticket_ids', 'created_at', 'updated_at']
        
        
class RaffleWinnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = RaffleWinner
        fields = ['user', 'email', 'full_name', 'winning_ticket_id', 'position', 'giveaway', 'created_at']


class UserTicketConsolidationArchiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTicketConsolidationArchive
        fields = ['user', 'email', 'full_name', 'unique_ticket_ids', 'archived_at']
        
        
# raffles/serializers.py

class RaffleWinnerArchiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = RaffleWinnerArchive
        fields = [
            'id',
            'user',
            'email',
            'full_name',
            'winning_ticket_id',
            'position',
            'giveaway',
            'created_at',
            'archived_at',
        ]
        read_only_fields = fields

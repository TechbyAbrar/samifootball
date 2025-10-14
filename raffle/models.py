    
# raffle/models.py
from tickets.models import GiveawayTicket
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
User = get_user_model()

class UserTicketConsolidation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ticket_consolidations")
    email = models.EmailField()
    full_name = models.CharField(max_length=255)
    unique_ticket_ids = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Ticket Consolidation"
        verbose_name_plural = "User Ticket Consolidations"
        indexes = [
            models.Index(fields=['user', 'email']),
            models.Index(fields=['created_at']),
        ]

    def clean(self):
        if not self.email:
            raise ValidationError("Email is required.")
        if not self.full_name:
            raise ValidationError("Full name is required.")
        if not self.unique_ticket_ids:
            raise ValidationError("Unique ticket IDs cannot be empty.")

    def __str__(self):
        return f"{self.email} - {len(self.unique_ticket_ids)} tickets"
    

class RaffleWinner(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    full_name = models.CharField(max_length=255)
    
    winning_ticket_id = models.CharField(max_length=255)
    position = models.CharField(max_length=25)
    giveaway = models.ForeignKey(GiveawayTicket, on_delete=models.CASCADE, related_name="winners")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'position', 'giveaway']
        indexes = [models.Index(fields=['position', 'giveaway'])]

    def __str__(self):
        return f"{self.position} winner: {self.email} (Ticket: {self.winning_ticket_id})"


class UserTicketConsolidationArchive(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    full_name = models.CharField(max_length=255)
    
    unique_ticket_ids = models.JSONField(default=list)
    archived_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Ticket Consolidation Archive"
        verbose_name_plural = "User Ticket Consolidation Archives"

    def __str__(self):
        return f"Archive for {self.email} at {self.archived_at}"
    

from django.utils import timezone
class RaffleWinnerArchive(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    full_name = models.CharField(max_length=255)

    winning_ticket_id = models.CharField(max_length=255)
    position = models.CharField(max_length=25)  # e.g. "1st", "2nd", ...
    giveaway = models.ForeignKey(GiveawayTicket, on_delete=models.CASCADE, related_name="archived_winners")

    created_at = models.DateTimeField()
    archived_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=['position', 'giveaway'])]
        verbose_name = "Archived Raffle Winner"
        verbose_name_plural = "Archived Raffle Winners"

    def __str__(self):
        return f"{self.position} (Archived) winner: {self.email} (Ticket: {self.winning_ticket_id})"

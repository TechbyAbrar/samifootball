from django.contrib import admin
from .models import (
    UserTicketConsolidation,
    RaffleWinner,
    UserTicketConsolidationArchive,
    RaffleWinnerArchive
)

@admin.register(UserTicketConsolidation)
class UserTicketConsolidationAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "user", "ticket_count", "created_at", "updated_at")
    search_fields = ("email", "full_name", "user__email")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")

    def ticket_count(self, obj):
        return len(obj.unique_ticket_ids)
    ticket_count.short_description = "Ticket Count"


@admin.register(RaffleWinner)
class RaffleWinnerAdmin(admin.ModelAdmin):
    list_display = ("position", "email", "winning_ticket_id", "giveaway", "created_at")
    search_fields = ("email", "full_name", "winning_ticket_id", "giveaway__title")
    list_filter = ("position", "giveaway", "created_at")
    readonly_fields = ("created_at",)


@admin.register(UserTicketConsolidationArchive)
class UserTicketConsolidationArchiveAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "user", "archived_ticket_count", "archived_at")
    search_fields = ("email", "full_name", "user__email")
    list_filter = ("archived_at",)
    readonly_fields = ("archived_at",)

    def archived_ticket_count(self, obj):
        return len(obj.unique_ticket_ids)
    archived_ticket_count.short_description = "Archived Ticket Count"


@admin.register(RaffleWinnerArchive)
class RaffleWinnerArchiveAdmin(admin.ModelAdmin):
    list_display = (
        'position',
        'email',
        'full_name',
        'winning_ticket_id',
        'giveaway',
        'created_at',
        'archived_at',
    )
    list_filter = (
        'position',
        'giveaway',
        'archived_at',
    )
    search_fields = (
        'email',
        'full_name',
        'winning_ticket_id',
    )
    ordering = ('-archived_at',)

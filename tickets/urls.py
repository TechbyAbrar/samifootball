from django.urls import path
from .views import CreateGiveawayTicketView, UpdateGiveawayTicketView, GiveawayTicketListView, TicketPurchaseListView

app_name = 'tickets'

# PurchaseTicketView

urlpatterns = [
    path("admin/create-ticket/", CreateGiveawayTicketView.as_view(), name="create-giveaway-ticket"),
    path("admin/update-delete/ticket/<int:pk>/", UpdateGiveawayTicketView.as_view(), name="update-giveaway-ticket"),
    path("available-ticket/", GiveawayTicketListView.as_view(), name="list-giveaway-ticket"),
    # path("purchase-tickets/", PurchaseTicketView.as_view(), name="purchase-ticket"),
    path("my-purchase/", TicketPurchaseListView.as_view(), name="my-ticket-purchases"),
]

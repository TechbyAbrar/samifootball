from django.urls import path
from .views import ConsolidatedTicketsView, RaffleDrawView, WinnerListView, Spins_Eligible_tickets, ArchiveConsolidatedTicketsView, WinnerDeleteAllView, ArchivedWinnerListView

urlpatterns = [
    path('consolidated-tickets/', ConsolidatedTicketsView.as_view(), name='consolidated-tickets'),
    path('spins-eligible-tickets/', Spins_Eligible_tickets.as_view(), name='spins-eligible-tickets'),
    path('admin/raffle/draw/', RaffleDrawView.as_view(), name='raffle-draw'),
    path('admin/winners/', WinnerListView.as_view(), name='raffle-winners'),
    path('admin/archive-consolidated-tickets/', ArchiveConsolidatedTicketsView.as_view(), name='archive-consolidated-tickets'),
    path('admin/winners/delete_all/', WinnerDeleteAllView.as_view(), name='winner-delete-all'),
    path('admin/winners/archived/list/', ArchivedWinnerListView.as_view(), name='archived-winner-list'),
]
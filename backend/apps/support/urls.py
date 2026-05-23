from django.urls import path

from . import views

urlpatterns = [
    path("webhooks/whatsapp/", views.WhatsAppWebhookView.as_view(), name="support-whatsapp-webhook"),
    path("tickets/", views.TicketListView.as_view(), name="support-ticket-list"),
    path("tickets/contact/", views.ContactTicketView.as_view(), name="support-ticket-contact"),
    path("tickets/<int:pk>/", views.TicketDetailView.as_view(), name="support-ticket-detail"),
    path("tickets/<int:pk>/reply/", views.TicketReplyView.as_view(), name="support-ticket-reply"),
    path("tickets/<int:pk>/status/", views.TicketStatusView.as_view(), name="support-ticket-status"),
]

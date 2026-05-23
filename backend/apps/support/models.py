from django.db import models

from apps.core.models import Business
from apps.leads.models import Customer


class Ticket(models.Model):
    """A support conversation with one customer over one channel.

    One open ticket per (business, channel, sender_id) at a time. Once status
    flips to 'resolved' the next inbound message starts a fresh ticket.
    """

    CHANNEL_CHOICES = [
        ("whatsapp", "WhatsApp"),
        ("sms", "SMS"),
        ("email", "Email"),
        ("webchat", "Web Chat"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("waiting", "Waiting on customer"),
        ("escalated", "Escalated to human"),
        ("resolved", "Resolved"),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="tickets")
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets",
    )

    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES)
    sender_id = models.CharField(
        max_length=255,
        help_text="WhatsApp number, email address, or chat-session ID. Identifies the customer on this channel.",
    )
    sender_name = models.CharField(max_length=200, blank=True, default="")

    subject = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open")
    human_only = models.BooleanField(
        default=False,
        help_text="If true, AI will not auto-reply — only human agents respond.",
    )

    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_message_at", "-created_at"]
        indexes = [
            models.Index(fields=["business", "status", "-last_message_at"]),
            models.Index(fields=["channel", "sender_id", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "channel", "sender_id"],
                condition=~models.Q(status="resolved"),
                name="support_ticket_one_open_per_sender",
            ),
        ]

    def __str__(self) -> str:
        return f"#{self.pk} · {self.channel} · {self.sender_name or self.sender_id}"


class TicketMessage(models.Model):
    """One message in a ticket thread (inbound from customer, outbound from AI/agent)."""

    DIRECTION_CHOICES = [("in", "Inbound"), ("out", "Outbound")]
    AUTHOR_CHOICES = [
        ("customer", "Customer"),
        ("ai", "AI"),
        ("agent", "Human agent"),
        ("system", "System"),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="messages")
    direction = models.CharField(max_length=4, choices=DIRECTION_CHOICES)
    author = models.CharField(max_length=16, choices=AUTHOR_CHOICES)
    body = models.TextField()
    provider_message_id = models.CharField(
        max_length=255, blank=True, default="",
        help_text="WhatsApp/Twilio message id — used to dedup webhook retries.",
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["ticket", "created_at"]),
            models.Index(fields=["provider_message_id"]),
        ]

    def __str__(self) -> str:
        return f"[{self.author}] {self.body[:60]}"

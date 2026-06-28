from django.db import models

from apps.core.models import Business
from apps.leads.models import Lead


class Call(models.Model):
    PROVIDER_CHOICES = [("vapi", "Vapi"), ("twilio", "Twilio")]
    STATUS_CHOICES = [
        ("ringing", "Ringing"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("no_answer", "No Answer"),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="calls")
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name="calls")
    provider = models.CharField(max_length=16, choices=PROVIDER_CHOICES)
    provider_call_id = models.CharField(max_length=128, db_index=True)
    from_number = models.CharField(max_length=32, blank=True)
    to_number = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="ringing")
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    recording_url = models.URLField(blank=True)
    transcript = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    persona_used = models.CharField(
        max_length=64, blank=True, default="",
        help_text="Persona name active when this call was answered. Snapshot — survives later renames.",
    )
    raw_payload = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"Call {self.provider_call_id} ({self.status})"


class OutboundTask(models.Model):
    """A queued outbound call the agent should place.

    Covers the four outbound use-cases — speed-to-lead, follow-up, reactivation,
    and appointment reminder. The cron runner (run_outbound_queue) picks up due
    rows, enforces quiet-hours / do-not-call guardrails, and places the call.
    """

    KIND_CHOICES = [
        ("speed_to_lead", "Speed to Lead"),
        ("follow_up", "Follow-up"),
        ("reactivation", "Reactivation"),
        ("reminder", "Appointment Reminder"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("calling", "Calling"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
        ("cancelled", "Cancelled"),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="outbound_tasks")
    lead = models.ForeignKey(
        Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name="outbound_tasks"
    )
    call = models.ForeignKey(
        Call, on_delete=models.SET_NULL, null=True, blank=True, related_name="outbound_tasks"
    )
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    to_number = models.CharField(max_length=32)
    objective = models.TextField(blank=True, help_text="Extra context for the agent's opening line.")
    campaign = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending", db_index=True)
    scheduled_for = models.DateTimeField(db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=3)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_for"]
        indexes = [models.Index(fields=["business", "status", "scheduled_for"])]

    def __str__(self) -> str:
        return f"OutboundTask {self.kind} → {self.to_number} ({self.status})"

"""Outbound trigger signals.

- New non-voice Lead  → speed-to-lead callback (guarded so we never call back
  someone who is currently on an inbound voice call).
- New AI-drafted Quote → scheduled follow-up call.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="leads.Lead", dispatch_uid="outbound_speed_to_lead")
def _speed_to_lead(sender, instance, created, **kwargs):
    if not created:
        return
    channel = instance.source_channel
    # Only chase leads that arrived on a non-voice channel; a lead with no
    # channel (or a phone channel) came from a live call — they're already on
    # the line with us, so don't dial them back.
    if channel is None or getattr(channel, "kind", "") == "phone":
        return
    if (instance.extracted_fields or {}).get("vapi_call_id"):
        return
    try:
        from .services.outbound import enqueue_speed_to_lead
        enqueue_speed_to_lead(instance)
    except Exception:  # noqa: BLE001
        logger.exception("speed_to_lead enqueue failed")


@receiver(post_save, sender="quotes.Quote", dispatch_uid="outbound_followup_after_quote")
def _followup_after_quote(sender, instance, created, **kwargs):
    if not created:
        return
    lead = getattr(instance, "lead", None)
    if lead is None:
        return
    try:
        from .services.outbound import enqueue_followup
        enqueue_followup(lead)
    except Exception:  # noqa: BLE001
        logger.exception("follow_up enqueue failed")

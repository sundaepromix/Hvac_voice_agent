"""Auto-sync Vapi assistant when Business config changes."""
from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Business

logger = logging.getLogger(__name__)

_SYNC_FIELDS = ("name", "voice_persona")


@receiver(post_save, sender=Business)
def push_to_vapi(sender, instance: Business, created: bool, **kwargs):  # noqa: ARG001
    """Push name/persona changes to the linked Vapi assistant.

    No-ops when vapi_assistant_id or vapi_api_key is unset (sync is opt-in:
    the dashboard owner has to paste the assistant ID once).
    """
    if not (instance.vapi_assistant_id or "").strip():
        return
    try:
        from apps.calls.services.vapi_sync import sync_assistant
        sync_assistant(instance)
    except Exception as exc:  # noqa: BLE001 — never break a Business save on a Vapi hiccup
        logger.warning("[VAPI SYNC SIGNAL] biz=%s err=%s", instance.id, exc)

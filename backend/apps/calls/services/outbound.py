"""Outbound calling engine.

Places outbound calls for the four use-cases — speed-to-lead, follow-up,
reactivation, and appointment reminder — through Vapi. Enforces quiet-hours and
do-not-call guardrails. The cron runner (`run_outbound_queue` management command,
wired to Vercel Cron) calls `run_due_tasks()`; the dashboard "Call now" action and
the trigger signals enqueue tasks.

Stubs out gracefully (no error, marks the task completed with a placeholder Call)
when the business has no Vapi credentials, so local dev never crashes.
"""
from __future__ import annotations

import logging
import uuid
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from apps.core.models import Business
from apps.leads.models import Lead

from ..models import Call, OutboundTask

logger = logging.getLogger(__name__)

VAPI_CALL_URL = "https://api.vapi.ai/call"
RETRY_DELAY_MINUTES = 30


# --------------------------------------------------------------------------- #
# Guardrails
# --------------------------------------------------------------------------- #

def _digits(number: str | None) -> str:
    return "".join(ch for ch in (number or "") if ch.isdigit())


def is_do_not_call(business: Business, number: str) -> bool:
    target = _digits(number)
    if not target:
        return True  # nothing to dial
    for line in (business.do_not_call or "").splitlines():
        if target == _digits(line):
            return True
    return False


def within_calling_window(business: Business, now=None) -> bool:
    """True when the business-local time is outside the configured quiet hours."""
    now = now or timezone.now()
    try:
        local = now.astimezone(ZoneInfo(business.timezone or "UTC"))
    except Exception:  # noqa: BLE001
        local = now
    hour = local.hour
    start = business.quiet_hours_start
    end = business.quiet_hours_end
    if start == end:
        return True  # quiet hours disabled
    if start < end:
        quiet = start <= hour < end
    else:  # overnight window, e.g. 21:00 → 08:00
        quiet = hour >= start or hour < end
    return not quiet


# --------------------------------------------------------------------------- #
# Opening lines per use-case
# --------------------------------------------------------------------------- #

def opening_line(task: OutboundTask, persona: str, business_name: str) -> str:
    name = ""
    if task.lead and task.lead.customer and task.lead.customer.name:
        name = task.lead.customer.name.split()[0]
    hi = f"Hi {name}, " if name else "Hi, "
    if task.kind == "speed_to_lead":
        return f"{hi}this is {persona} from {business_name} — I saw you just reached out. Is now a good time for a quick chat?"
    if task.kind == "follow_up":
        return f"{hi}this is {persona} from {business_name}, following up on the quote we put together. Do you have any questions I can help with?"
    if task.kind == "reactivation":
        return f"{hi}this is {persona} from {business_name}. We were going through our records and wanted to check in — are you still looking for help with this?"
    if task.kind == "reminder":
        return f"{hi}this is {persona} from {business_name} with a quick reminder about your upcoming appointment. Does that time still work for you?"
    return f"{hi}this is {persona} from {business_name}."


# --------------------------------------------------------------------------- #
# Placement
# --------------------------------------------------------------------------- #

def place_call(task: OutboundTask) -> dict:
    """Place a single outbound call via Vapi. Returns a result dict.

    Stubs (success, no real call) when Vapi isn't configured.
    """
    business = task.business
    persona = (getattr(business, "voice_persona", "") or "Mary").strip() or "Mary"

    api_key = (getattr(business, "resolved_vapi_key", "") or "").strip()
    assistant_id = (getattr(business, "vapi_assistant_id", "") or "").strip()
    phone_number_id = (getattr(business, "vapi_phone_number_id", "") or "").strip()

    if not (api_key and assistant_id and phone_number_id):
        # Stub path — record a placeholder Call so the dashboard shows the attempt.
        call = Call.objects.create(
            business=business,
            lead=task.lead,
            provider="vapi",
            provider_call_id=f"stub-{uuid.uuid4().hex[:12]}",
            from_number=getattr(business, "twilio_from_number", "") or "",
            to_number=task.to_number,
            status="completed",
            persona_used=persona,
            summary="(stubbed outbound — Vapi not configured)",
        )
        logger.info("[OUTBOUND STUB] task=%s kind=%s → %s", task.id, task.kind, task.to_number)
        return {"success": True, "stubbed": True, "call_id": call.id}

    try:
        import requests  # noqa: WPS433
    except ImportError:
        return {"success": False, "error": "requests not installed"}

    body = {
        "phoneNumberId": phone_number_id,
        "assistantId": assistant_id,
        "customer": {"number": task.to_number},
        "assistantOverrides": {
            "firstMessage": opening_line(task, persona, business.name),
            "metadata": {"outbound_task_id": task.id, "kind": task.kind},
        },
    }
    try:
        resp = requests.post(
            VAPI_CALL_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=20,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[OUTBOUND] task=%s network error: %s", task.id, exc)
        return {"success": False, "error": str(exc)[:200]}

    if resp.status_code >= 300:
        logger.warning("[OUTBOUND] task=%s vapi %s: %s", task.id, resp.status_code, resp.text[:200])
        return {"success": False, "status": resp.status_code, "error": resp.text[:200]}

    data = resp.json() if resp.content else {}
    provider_call_id = data.get("id") or f"vapi-{uuid.uuid4().hex[:12]}"
    call = Call.objects.create(
        business=business,
        lead=task.lead,
        provider="vapi",
        provider_call_id=provider_call_id,
        to_number=task.to_number,
        status="ringing",
        persona_used=persona,
        raw_payload=data if isinstance(data, dict) else {},
    )
    logger.info("[OUTBOUND] placed task=%s call=%s → %s", task.id, provider_call_id, task.to_number)
    return {"success": True, "call_id": call.id, "provider_call_id": provider_call_id}


# --------------------------------------------------------------------------- #
# Queue runner
# --------------------------------------------------------------------------- #

def run_due_tasks(now=None, limit: int = 25) -> dict:
    """Process pending tasks whose time has come. Returns a summary dict."""
    now = now or timezone.now()
    due = (
        OutboundTask.objects.select_related("business", "lead", "lead__customer")
        .filter(status="pending", scheduled_for__lte=now)
        .order_by("scheduled_for")[:limit]
    )
    placed = skipped = failed = deferred = 0
    for task in due:
        business = task.business
        if not business.outbound_enabled:
            task.status = "skipped"
            task.last_error = "outbound_disabled"
            task.save(update_fields=["status", "last_error", "updated_at"])
            skipped += 1
            continue
        if is_do_not_call(business, task.to_number):
            task.status = "skipped"
            task.last_error = "do_not_call"
            task.save(update_fields=["status", "last_error", "updated_at"])
            skipped += 1
            continue
        if not within_calling_window(business, now):
            deferred += 1
            continue  # leave pending; a later cron run inside the window picks it up

        result = place_call(task)
        task.attempts += 1
        task.last_attempt_at = now
        if result.get("success"):
            call_id = result.get("call_id")
            if call_id:
                task.call_id = call_id
            task.status = "completed"
            task.last_error = ""
            task.save(update_fields=["status", "attempts", "last_attempt_at", "last_error", "call", "updated_at"])
            placed += 1
        else:
            task.last_error = (result.get("error") or "call_failed")[:255]
            if task.attempts >= task.max_attempts:
                task.status = "failed"
                failed += 1
            else:
                task.scheduled_for = now + timedelta(minutes=RETRY_DELAY_MINUTES)
            task.save(update_fields=["status", "attempts", "last_attempt_at", "last_error", "scheduled_for", "updated_at"])
    return {"placed": placed, "skipped": skipped, "failed": failed, "deferred": deferred}


# --------------------------------------------------------------------------- #
# Enqueue helpers / triggers
# --------------------------------------------------------------------------- #

def enqueue(business: Business, *, kind: str, to_number: str, lead: Lead | None = None,
            scheduled_for=None, objective: str = "", campaign: str = "") -> OutboundTask | None:
    """Create a pending OutboundTask, de-duplicating on (lead, kind) while pending."""
    if not to_number:
        return None
    if lead is not None:
        existing = OutboundTask.objects.filter(
            business=business, lead=lead, kind=kind, status="pending"
        ).first()
        if existing:
            return existing
    return OutboundTask.objects.create(
        business=business,
        lead=lead,
        kind=kind,
        to_number=to_number,
        objective=objective,
        campaign=campaign,
        scheduled_for=scheduled_for or timezone.now(),
    )


def _lead_phone(lead: Lead) -> str:
    return (getattr(getattr(lead, "customer", None), "phone", "") or "").strip()


def enqueue_speed_to_lead(lead: Lead, delay_seconds: int = 60) -> OutboundTask | None:
    business = lead.business
    if not (business.outbound_enabled and business.speed_to_lead_enabled):
        return None
    phone = _lead_phone(lead)
    if not phone:
        return None
    return enqueue(
        business, kind="speed_to_lead", to_number=phone, lead=lead,
        scheduled_for=timezone.now() + timedelta(seconds=delay_seconds),
    )


def enqueue_followup(lead: Lead) -> OutboundTask | None:
    business = lead.business
    if not business.outbound_enabled:
        return None
    phone = _lead_phone(lead)
    if not phone:
        return None
    return enqueue(
        business, kind="follow_up", to_number=phone, lead=lead,
        scheduled_for=timezone.now() + timedelta(hours=business.followup_delay_hours or 24),
    )


def enqueue_reminder(lead: Lead, when, objective: str = "") -> OutboundTask | None:
    business = lead.business
    if not business.outbound_enabled:
        return None
    phone = _lead_phone(lead)
    if not phone:
        return None
    return enqueue(
        business, kind="reminder", to_number=phone, lead=lead,
        scheduled_for=when, objective=objective,
    )


def enqueue_reactivation_campaign(business: Business, limit: int = 50) -> int:
    """Queue reactivation calls for cold/lost leads that have gone quiet."""
    if not business.outbound_enabled:
        return 0
    cutoff = timezone.now() - timedelta(days=business.reactivation_days or 30)
    leads = (
        Lead.objects.select_related("customer")
        .filter(business=business, updated_at__lte=cutoff)
        .filter(models_q_cold_or_lost())
        .exclude(customer__phone="")
        .order_by("-updated_at")[:limit]
    )
    queued = 0
    for lead in leads:
        if enqueue(business, kind="reactivation", to_number=_lead_phone(lead), lead=lead, campaign="reactivation"):
            queued += 1
    return queued


def models_q_cold_or_lost():
    from django.db.models import Q
    return Q(temperature="cold") | Q(status="lost")

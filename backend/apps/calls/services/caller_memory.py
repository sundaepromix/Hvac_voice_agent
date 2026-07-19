"""Returning-caller memory — recognize a repeat caller by verified phone.

Builds a compact history block (past leads, latest quote, upcoming booking)
that gets appended to Mary's system prompt so she can greet a known caller by
name and pick the conversation back up. Keyed off the verified Vapi caller ID
only — never an LLM-provided number — and best-effort: any failure returns an
empty string so a live call can never break on a memory lookup.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime

from django.core.cache import cache

logger = logging.getLogger(__name__)

_CTX_TTL = 60 * 60  # matches the per-call state TTL in receptionist.py
_MAX_LEADS = 3
_SUMMARY_CHARS = 100


def _find_customer(business, phone: str):
    from apps.leads.models import Customer

    cust = Customer.objects.filter(business=business, phone=phone).first()
    if cust:
        return cust
    # Formats drift between channels ("+1 (555) 123-4567" vs "+15551234567"):
    # fall back to comparing the last 10 digits, normalized on BOTH sides.
    # The endswith on the last 4 is only a cheap DB prefilter.
    digits = re.sub(r"\D", "", phone)[-10:]
    if len(digits) < 7:
        return None
    candidates = (
        Customer.objects.filter(business=business, phone__endswith=digits[-4:])
        .exclude(phone="")[:50]
    )
    for cust in candidates:
        if re.sub(r"\D", "", cust.phone)[-10:] == digits:
            return cust
    return None


def _past_leads(customer, call_id: str | None) -> list:
    # The current call's own lead is history-in-the-making, not history —
    # filtered in Python because a JSON-key exclude() also drops rows that
    # lack the key entirely (chat/web leads have no vapi_call_id).
    out = []
    for lead in customer.leads.order_by("-created_at")[:_MAX_LEADS * 2]:
        fields = lead.extracted_fields or {}
        if call_id and fields.get("vapi_call_id") == call_id:
            continue
        out.append(lead)
        if len(out) >= _MAX_LEADS:
            break
    return out


def _upcoming_booking(leads: list) -> str:
    today = date.today()
    for lead in leads:
        booking = (lead.extracted_fields or {}).get("booking") or {}
        try:
            when = datetime.strptime(str(booking.get("date")), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue
        if when >= today:
            time_part = f" at {booking['time']}" if booking.get("time") else ""
            return f"{when.strftime('%A, %B %d')}{time_part}"
    return ""


def _latest_quote(customer):
    from apps.quotes.models import Quote

    return (
        Quote.objects.filter(lead__customer=customer)
        .order_by("-created_at").first()
    )


def _render(customer, leads: list, quote, booking_when: str) -> str:
    lines = ["RETURNING CALLER — our records show history with this phone number:"]
    who = customer.name or "Name not on file"
    if customer.address:
        who += f" (address on file: {customer.address})"
    lines.append(f"- Caller: {who}.")
    for lead in leads:
        summary = (lead.project_summary or "no summary recorded")[:_SUMMARY_CHARS]
        lines.append(
            f"- {lead.created_at.strftime('%B %d')}: \"{summary}\" — status: {lead.status}."
        )
    if quote:
        currency = (quote.photo_assessment or {}).get("currency") or "USD"
        lines.append(
            f"- Latest quote {quote.reference}: {currency} {quote.total} ({quote.status})."
        )
    if booking_when:
        lines.append(f"- Upcoming appointment: {booking_when}.")
    lines.append(
        "HOW TO USE THIS (natural, not creepy):\n"
        "- Early in your FIRST reply, greet them back by first name once, warmly — "
        "e.g. \"Of course — and it's great to hear from you again, Mark!\" Then, if it "
        "fits, ask ONE natural follow-up tied to the most recent item above (an open "
        "quote, an upcoming appointment, a recent project).\n"
        "- This may be a completely NEW matter. Never assume it's about the old "
        "project — offer, don't insist. If they're calling about something new, help "
        "with that and drop the history.\n"
        "- Do NOT recite the record. Never read out their address, phone, or quote "
        "amounts unprompted — reference history in passing, like a good receptionist "
        "who simply remembers people.\n"
        "- If the caller isn't this person (different name, borrowed phone), say a "
        "friendly \"my mistake!\", ignore this history entirely, and treat them as new.\n"
        "- Details they already gave before (name, address) still need a quick "
        "confirmation before you reuse them in a booking — \"still on Maple Street?\" "
        "beats re-asking from scratch.\n"
        "- All normal tools still apply: run qualify_lead for THIS call's request as usual."
    )
    return "\n".join(lines)


def known_caller_block(business, caller_phone: str | None, call_id: str | None = None) -> str:
    """The system-prompt block for a recognized repeat caller, or "" if unknown.

    Cached per call so the snapshot is taken on the first turn and later turns
    don't re-query (or start seeing rows created during this same call).
    """
    phone = (caller_phone or "").strip()
    if not phone or business is None:
        return ""

    cache_key = f"caller_ctx:{getattr(business, 'id', 0)}:{call_id}" if call_id else None
    if cache_key:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached.get("block", "")

    block = ""
    try:
        customer = _find_customer(business, phone)
        if customer:
            leads = _past_leads(customer, call_id)
            if leads or customer.name:
                block = _render(
                    customer, leads, _latest_quote(customer), _upcoming_booking(leads),
                )
                logger.info(
                    "[CALLER MEMORY] recognized %s (customer=%s, %d past leads) call=%s",
                    customer.name or phone, customer.id, len(leads), call_id or "?",
                )
    except Exception as exc:  # noqa: BLE001 — memory is a bonus; never break a live call
        logger.warning("[CALLER MEMORY] lookup failed for %s: %s", phone, exc)
        block = ""

    if cache_key:
        cache.set(cache_key, {"block": block}, timeout=_CTX_TTL)
    return block

"""Bridge tools → Workflow Auth domain models (Lead, Customer, Conversation, Call)."""
from __future__ import annotations

import logging
import secrets
from decimal import Decimal
from typing import Any

from django.utils import timezone

from apps.core.models import Business
from apps.leads.models import Conversation, Customer, Lead, Message

logger = logging.getLogger(__name__)


def _default_business() -> Business | None:
    return Business.objects.first()


def upsert_customer(business: Business, name: str | None = None, phone: str | None = None,
                    email: str | None = None, address: str | None = None) -> Customer:
    """Find-or-create a Customer for this business, keyed by phone (then email)."""
    cust = None
    if phone:
        cust = Customer.objects.filter(business=business, phone=phone).first()
    if not cust and email:
        cust = Customer.objects.filter(business=business, email=email).first()
    if not cust:
        cust = Customer.objects.create(
            business=business,
            name=name or "",
            phone=phone or "",
            email=email or "",
            address=address or "",
        )
    else:
        # Patch in any new info we learned
        dirty = False
        if name and cust.name != name:
            cust.name = name
            dirty = True
        if email and cust.email != email:
            cust.email = email
            dirty = True
        if address and cust.address != address:
            cust.address = address
            dirty = True
        if dirty:
            cust.save()
    return cust


def _resolve_phone(payload: dict[str, Any], verified_phone: str | None) -> tuple[str | None, str | None]:
    """Pick the canonical phone (always the verified caller ID when present).

    Returns (canonical_phone, callback_phone). If the LLM passed a different
    number, surface it as a separate callback so the human team can see what
    the caller asked us to use, but the customer record is keyed by the real
    caller ID — never a hallucinated value.
    """
    llm_phone = (payload.get("customer_phone") or "").strip() or None
    verified = (verified_phone or "").strip() or None
    if verified:
        callback = llm_phone if (llm_phone and llm_phone != verified) else None
        return verified, callback
    return llm_phone, None


def _find_lead_for_call(business: Business, customer: Customer, call_id: str | None) -> Lead | None:
    """Find the Lead row that belongs to the active call.

    Strategy: prefer dedup by `vapi_call_id` stored in extracted_fields — that
    binds every tool fire within one phone call to a single Lead row. Fall
    back to the most recent open lead for this customer.
    """
    if call_id:
        existing = Lead.objects.filter(
            business=business, customer=customer,
            extracted_fields__vapi_call_id=call_id,
        ).order_by("-created_at").first()
        if existing:
            return existing
    return Lead.objects.filter(
        business=business, customer=customer,
        status__in=["new", "qualifying", "quoted", "booked"],
    ).order_by("-created_at").first()


def qualify_lead_tool(payload: dict[str, Any], verified_phone: str | None = None,
                      call_id: str | None = None) -> dict[str, Any]:
    """Tool implementation: capture/update the lead record for the current call."""
    business = _default_business()
    if not business:
        return {"error": "No business configured. Add one in the dashboard settings."}

    canonical_phone, callback_phone = _resolve_phone(payload, verified_phone)

    cust = upsert_customer(
        business=business,
        name=payload.get("customer_name"),
        phone=canonical_phone,
        email=payload.get("customer_email"),
        address=payload.get("address"),
    )

    extracted = {k: v for k, v in payload.items() if v is not None}
    if canonical_phone:
        extracted["customer_phone"] = canonical_phone
    if callback_phone:
        extracted["callback_phone"] = callback_phone
    if call_id:
        extracted["vapi_call_id"] = call_id
    estimated = payload.get("estimated_value")
    estimated_dec = Decimal(str(estimated)) if isinstance(estimated, (int, float)) else None
    summary = (payload.get("project_summary") or "")[:512]
    temperature = payload.get("temperature") or "warm"

    lead = _find_lead_for_call(business, cust, call_id)

    if lead:
        if summary:
            lead.project_summary = summary
        if estimated_dec is not None:
            lead.estimated_value = estimated_dec
        if temperature:
            lead.temperature = temperature
        lead.extracted_fields = {**(lead.extracted_fields or {}), **extracted}
        lead.status = "qualifying"
        lead.save()
        action = "updated"
    else:
        lead = Lead.objects.create(
            business=business,
            customer=cust,
            project_summary=summary,
            status="qualifying",
            temperature=temperature,
            estimated_value=estimated_dec,
            extracted_fields=extracted,
        )
        action = "created"

    logger.info("[QUALIFY_LEAD] %s lead=%s customer=%s", action, lead.id, cust.id)
    return {
        "success": True,
        "lead_id": lead.id,
        "customer_id": cust.id,
        "message": f"Lead #{lead.id} {action} for {cust.name or cust.phone}",
    }


def book_appointment_tool(payload: dict[str, Any], verified_phone: str | None = None,
                           call_id: str | None = None, business: Business | None = None) -> dict[str, Any]:
    """Tool implementation: book a confirmed service appointment.

    Reuses the Lead row already opened by qualify_lead in this same call
    (matched by vapi_call_id), or the most recent open lead for the customer.
    """
    business = business or _default_business()
    if not business:
        return {"error": "No business configured."}

    canonical_phone, callback_phone = _resolve_phone(payload, verified_phone)

    cust = upsert_customer(
        business=business,
        name=payload.get("customer_name"),
        phone=canonical_phone,
        address=payload.get("address"),
    )

    estimated = payload.get("estimated_value")
    estimated_dec = Decimal(str(estimated)) if isinstance(estimated, (int, float)) else None

    booking_summary = (
        f"{payload.get('trade', 'service').title()} appointment on "
        f"{payload.get('date')} at {payload.get('time')}. "
        f"{payload.get('project_summary', '')}".strip()
    )

    lead = _find_lead_for_call(business, cust, call_id)
    booking_extracted = {
        "booking": payload,
        "booked_at": timezone.now().isoformat(),
    }
    if canonical_phone:
        booking_extracted["customer_phone"] = canonical_phone
    if callback_phone:
        booking_extracted["callback_phone"] = callback_phone
    if call_id:
        booking_extracted["vapi_call_id"] = call_id

    if lead:
        lead.status = "booked"
        lead.project_summary = booking_summary[:512]
        lead.estimated_value = estimated_dec or lead.estimated_value
        lead.extracted_fields = {
            **(lead.extracted_fields or {}),
            **booking_extracted,
        }
        lead.save()
    else:
        lead = Lead.objects.create(
            business=business,
            customer=cust,
            project_summary=booking_summary[:512],
            status="booked",
            temperature="hot",
            estimated_value=estimated_dec,
            extracted_fields=booking_extracted,
        )

    convo = Conversation.objects.create(lead=lead)
    Message.objects.create(
        conversation=convo,
        direction="out",
        role="system",
        body=f"Booking confirmed: {booking_summary}",
    )

    # Best-effort Google Calendar sync — booking succeeds in the dashboard
    # whether or not the calendar is configured/reachable.
    from apps.calls.services.scheduling import create_calendar_event
    tz_name = (business.timezone or "").strip() or "America/Los_Angeles"
    event_id = create_calendar_event(
        date_str=payload.get("date") or "",
        time_str=payload.get("time") or "",
        duration_minutes=payload.get("duration_minutes") or 60,
        summary=f"{payload.get('trade', 'Service').title()} — {cust.name or canonical_phone or 'customer'}",
        description=(
            f"{payload.get('project_summary', '')}\n"
            f"Phone: {canonical_phone or 'unknown'}\n"
            f"Address: {payload.get('address', '')}\n"
            f"Booked by the AI receptionist (lead #{lead.id})."
        ).strip(),
        tz_name=tz_name,
    )
    if event_id:
        lead.extracted_fields = {**(lead.extracted_fields or {}), "calendar_event_id": event_id}
        lead.save(update_fields=["extracted_fields", "updated_at"])

    logger.info("[BOOK] lead=%s when=%s %s calendar=%s",
                lead.id, payload.get("date"), payload.get("time"), event_id or "not-synced")
    return {
        "success": True,
        "lead_id": lead.id,
        "customer_id": cust.id,
        "calendar_synced": bool(event_id),
        "message": f"Booked {booking_summary}",
    }


def recover_lead_from_transcript(business: Business, call_id: str, transcript: str,
                                 caller_phone: str | None = None) -> Lead | None:
    """Safety net for the end-of-call report: if the agent never captured a
    lead during the call (model stalled, call dropped mid-flow), extract one
    from the final transcript so no conversation disappears from the dashboard.

    No-op when a Lead already exists for this call, or when the transcript
    yields nothing worth saving (wrong numbers, spam, instant hangups).
    """
    if Lead.objects.filter(business=business, extracted_fields__vapi_call_id=call_id).exists():
        return None

    from apps.ai.services import extract_lead_from_transcript
    data = extract_lead_from_transcript(transcript, business=business)
    name = (data.get("customer_name") or "").strip()
    summary = (data.get("project_summary") or "").strip()
    phone = (caller_phone or "").strip() or None
    if not (name or summary or phone):
        return None

    cust = upsert_customer(
        business=business,
        name=name or None,
        phone=phone,
        email=(data.get("customer_email") or "").strip() or None,
        address=(data.get("address") or "").strip() or None,
    )
    estimated = data.get("estimated_value")
    extracted = {k: v for k, v in data.items() if v not in (None, "", [])}
    extracted["vapi_call_id"] = call_id
    extracted["source"] = "transcript_recovery"
    lead = Lead.objects.create(
        business=business,
        customer=cust,
        project_summary=(summary or "Recovered from call transcript — review recording")[:512],
        status="qualifying",
        temperature=data.get("temperature") or "warm",
        estimated_value=Decimal(str(estimated)) if isinstance(estimated, (int, float)) else None,
        extracted_fields=extracted,
    )
    logger.info("[TRANSCRIPT RECOVERY] lead=%s customer=%s call=%s (agent captured nothing during the call)",
                lead.id, cust.id, call_id)
    return lead


def transfer_to_human_tool(payload: dict[str, Any], verified_phone: str | None = None,
                           call_id: str | None = None) -> dict[str, Any]:
    """Tool implementation: log a priority human-callback request.

    There is no live transfer line wired up yet, so the honest contract is:
    flag the lead for an urgent human callback and tell the model the transfer
    did NOT happen, so it follows its "transfer isn't possible" script instead
    of leaving the caller in dead air.
    """
    business = _default_business()
    if not business:
        return {"error": "No business configured."}

    canonical_phone, callback_phone = _resolve_phone(payload, verified_phone)
    reason = (payload.get("reason") or "caller requested a human")[:255]
    summary = (payload.get("summary") or "")[:512]
    urgency = payload.get("urgency") or "high"

    cust = upsert_customer(
        business=business,
        name=payload.get("customer_name"),
        phone=canonical_phone,
    )
    lead = _find_lead_for_call(business, cust, call_id)
    escalation = {
        "transfer_requested": True,
        "transfer_reason": reason,
        "transfer_urgency": urgency,
        "transfer_requested_at": timezone.now().isoformat(),
    }
    if callback_phone:
        escalation["callback_phone"] = callback_phone
    if call_id:
        escalation["vapi_call_id"] = call_id

    if lead:
        if summary and not lead.project_summary:
            lead.project_summary = summary
        lead.temperature = "hot"
        lead.extracted_fields = {**(lead.extracted_fields or {}), **escalation}
        lead.save()
    else:
        lead = Lead.objects.create(
            business=business,
            customer=cust,
            project_summary=summary or f"Escalation: {reason}",
            status="qualifying",
            temperature="hot",
            extracted_fields=escalation,
        )

    convo = lead.conversations.order_by("-started_at").first() or Conversation.objects.create(lead=lead)
    Message.objects.create(
        conversation=convo,
        direction="out",
        role="system",
        body=f"ESCALATION — human callback requested ({urgency}). Reason: {reason}. {summary}",
    )
    logger.info("[TRANSFER_TO_HUMAN] lead=%s reason=%s urgency=%s", lead.id, reason, urgency)
    return {
        "success": True,
        "transferred": False,
        "callback_logged": True,
        "lead_id": lead.id,
        "message": (
            "No live transfer line is available right now. The issue is flagged as a "
            "priority callback for the office team. Tell the caller you couldn't reach "
            "the team this second, that someone will call them back promptly, confirm "
            "their callback number, and summarize the issue back to them."
        ),
    }


def draft_quote_tool(payload: dict[str, Any], verified_phone: str | None = None,
                     call_id: str | None = None) -> dict[str, Any]:
    """Tool implementation: create a Quote on the active call's Lead.

    The Lead is found by `vapi_call_id` (the same dedup key used by qualify_lead
    and book_appointment), so all three tools land on one consistent row even
    if Mary fires them in a different order across turns.
    """
    from apps.quotes.models import LineItem, Quote
    business = _default_business()
    if not business:
        return {"error": "No business configured."}

    if not call_id:
        return {"error": "No call_id available — cannot tie quote to lead."}

    lead = Lead.objects.filter(
        business=business, extracted_fields__vapi_call_id=call_id,
    ).order_by("-created_at").first()
    if not lead:
        return {"error": "No lead found for this call. Run qualify_lead first."}

    raw_items = payload.get("line_items") or []
    line_items: list[dict[str, Any]] = []
    subtotal = Decimal("0")
    for item in raw_items:
        try:
            qty = Decimal(str(item.get("quantity", 1)))
            unit = Decimal(str(item.get("unit_price", 0)))
        except (ValueError, TypeError):
            continue
        line_total = (qty * unit).quantize(Decimal("0.01"))
        line_items.append({
            "description": (item.get("description") or "")[:255],
            "quantity": qty,
            "unit_price": unit,
            "total": line_total,
        })
        subtotal += line_total

    try:
        tax_rate = Decimal(str(payload.get("tax_rate", 0)))
    except (ValueError, TypeError):
        tax_rate = Decimal("0")
    tax = (subtotal * tax_rate).quantize(Decimal("0.01"))
    total = subtotal + tax
    notes = (payload.get("notes") or payload.get("summary") or "")[:1000]
    currency = (payload.get("currency") or "USD").strip()[:8]

    # Dedup: one Quote per phone call. If Mary refines the price across turns,
    # update the same Quote row (replace line items, recalc totals) instead of
    # writing a new one. Match by `photo_assessment.drafted_during_call == call_id`.
    quote = (
        Quote.objects.filter(lead=lead, photo_assessment__drafted_during_call=call_id)
        .order_by("-created_at").first()
    )
    if quote:
        quote.subtotal = subtotal
        quote.tax = tax
        quote.total = total
        quote.notes = notes
        quote.photo_assessment = {
            "scope_summary": (payload.get("summary") or "")[:1000],
            "currency": currency,
            "drafted_during_call": call_id,
        }
        quote.save()
        quote.line_items.all().delete()
        action = "updated"
        reference = quote.reference
    else:
        reference = "HL-" + secrets.token_hex(3).upper()
        quote = Quote.objects.create(
            lead=lead,
            reference=reference,
            subtotal=subtotal,
            tax=tax,
            total=total,
            notes=notes,
            status="draft",
            drafted_by_ai=True,
            photo_assessment={
                "scope_summary": (payload.get("summary") or "")[:1000],
                "currency": currency,
                "drafted_during_call": call_id,
            },
        )
        action = "created"
    for li in line_items:
        LineItem.objects.create(quote=quote, **li)

    if lead.status == "qualifying":
        lead.status = "quoted"
        lead.estimated_value = total
        lead.save(update_fields=["status", "estimated_value", "updated_at"])

    logger.info("[DRAFT_QUOTE] %s quote=%s lead=%s items=%d total=%s %s",
                action, quote.id, lead.id, len(line_items), total, currency)
    return {
        "success": True,
        "quote_id": quote.id,
        "reference": reference,
        "total": str(total),
        "currency": currency,
        "items": len(line_items),
        "action": action,
        "message": f"Quote {reference} {action} with {len(line_items)} line items, total {currency} {total}.",
    }

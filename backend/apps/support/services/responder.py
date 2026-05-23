"""Generate an AI support reply for a ticket using the business's knowledge_base.

Lightweight version of the support-agent brain — single Sonnet call, no Haiku
classifier and no pgvector RAG. The whole knowledge_base text is passed as
context. If there's no API key, returns a polite hand-off so dev never crashes.
"""
from __future__ import annotations

import logging

from django.conf import settings

from apps.core.models import Business
from apps.support.models import Ticket, TicketMessage

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-sonnet-4-6"
HISTORY_LIMIT = 12

FALLBACK_REPLY = (
    "Thanks for your message — a team member will get back to you shortly."
)


def _client(business: Business):
    key = business.resolved_anthropic_key or settings.ANTHROPIC_API_KEY
    if not key:
        return None
    try:
        import anthropic  # noqa: WPS433
        return anthropic.Anthropic(api_key=key)
    except ImportError:
        logger.warning("anthropic SDK not installed")
        return None


def _system_prompt(business: Business, persona: str) -> str:
    kb = (business.knowledge_base or "").strip() or "No knowledge base entries provided."
    return (
        f"You are {persona}, the support assistant for {business.name}, "
        f"a {business.get_trade_display()} business.\n\n"
        "RULES:\n"
        "- Be warm, concise, and professional. Match the customer's tone.\n"
        "- Only answer using the KNOWLEDGE BASE below. If the answer isn't there, "
        "say you'll have a teammate follow up — never invent prices, policies, "
        "warranties, or commitments.\n"
        "- For booking, scheduling, on-site visits, or anything requiring a person, "
        "tell the customer a teammate will reach out shortly.\n"
        "- Keep replies under 4 short sentences unless the customer asked a "
        "detailed technical question.\n\n"
        "KNOWLEDGE BASE:\n"
        f"{kb}"
    )


def _history(ticket: Ticket) -> list[dict]:
    """Most-recent N messages, oldest first, in Anthropic format."""
    rows = list(
        TicketMessage.objects.filter(ticket=ticket)
        .order_by("-created_at")
        .values("author", "body")[:HISTORY_LIMIT]
    )
    rows.reverse()
    out: list[dict] = []
    for row in rows:
        role = "user" if row["author"] == "customer" else "assistant"
        out.append({"role": role, "content": row["body"]})
    return out


def generate_reply(ticket: Ticket) -> str:
    """Run one Sonnet call against the ticket history and return Mary's reply text.

    Caller is responsible for persisting and sending the reply.
    """
    business = ticket.business
    persona = business.voice_persona or "Mary"

    client = _client(business)
    if not client:
        return FALLBACK_REPLY

    messages = _history(ticket)
    if not messages or messages[-1]["role"] != "user":
        return FALLBACK_REPLY

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            system=_system_prompt(business, persona),
            messages=messages,
        )
    except Exception as exc:  # noqa: BLE001 — never crash the webhook on a Claude error
        logger.exception("[SUPPORT RESPONDER] biz=%s err=%s", business.pk, exc)
        return FALLBACK_REPLY

    text_block = next((b for b in response.content if getattr(b, "type", "") == "text"), None)
    text = (text_block.text.strip() if text_block else "")
    return text or FALLBACK_REPLY

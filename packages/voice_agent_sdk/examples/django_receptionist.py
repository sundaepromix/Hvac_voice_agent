"""Drop-in replacement for ``apps/calls/agent/receptionist.py`` built on the SDK.

This shows the migration path: the SDK runs the loop, your existing Django code
keeps owning the business logic. Nothing here re-implements persistence,
prompts, or pricing — it wires the pieces you already have into the framework.

To adopt it, point `apps/calls/views.chat_completions` at `handle_turn` below
instead of the old `handle_conversation_turn`. The public contract is identical:
returns ``{"text": str, "end_call": bool}``.
"""
from __future__ import annotations

import logging
from typing import Any

from django.core.cache import cache

# --- your existing, untouched business logic --------------------------------
from apps.calls.agent.prompts import get_receptionist_prompt
from apps.calls.agent.tools import TOOLS  # reuse the exact same schemas
from apps.calls.services.email import send_email
from apps.calls.services.persistence import (
    book_appointment_tool,
    draft_quote_tool,
    qualify_lead_tool,
)
from apps.calls.services.scheduling import check_availability
from apps.calls.services.sms import send_sms
from apps.core.models import Business

# --- the SDK ----------------------------------------------------------------
from voice_agent import (
    AgentConfig,
    PromptBuilder,
    ProviderConfig,
    StateStore,
    Tool,
    ToolContext,
    ToolRegistry,
    VoiceAgent,
)

logger = logging.getLogger(__name__)


# 1) Back per-call state with Django's shared cache so all gunicorn workers see
#    the same dedup keys (the reason the original used FileBasedCache, not
#    locmem). Implementing StateStore is three thin methods.
class DjangoCacheStore:
    def get(self, key: str) -> Any | None:
        return cache.get(key)

    def set(self, key: str, value: Any, ttl: int) -> None:
        cache.set(key, value, timeout=ttl)

    def delete(self, key: str) -> None:
        cache.delete(key)


_STORE: StateStore = DjangoCacheStore()


# 2) Map each schema in TOOLS to a handler. Handlers are thin wrappers around
#    the persistence/integration functions you already have — same behaviour,
#    just reached through ToolContext.
def _schema(name: str) -> dict:
    return next(t["input_schema"] for t in TOOLS if t["name"] == name)


def _desc(name: str) -> str:
    return next(t.get("description", "") for t in TOOLS if t["name"] == name)


def _qualify(inp: dict, ctx: ToolContext) -> dict:
    return qualify_lead_tool(inp, verified_phone=ctx.caller_phone, call_id=ctx.call_id)


def _book(inp: dict, ctx: ToolContext) -> dict:
    return book_appointment_tool(inp, verified_phone=ctx.caller_phone, call_id=ctx.call_id)


def _quote(inp: dict, ctx: ToolContext) -> dict:
    return draft_quote_tool(inp, verified_phone=ctx.caller_phone, call_id=ctx.call_id)


def _availability(inp: dict, ctx: ToolContext) -> dict:
    return check_availability(inp["date"], inp.get("trade"))


def _sms(inp: dict, ctx: ToolContext) -> dict:
    to = (inp.get("to") or "").strip() or (ctx.caller_phone or "")
    return send_sms(to, inp["message"], business=ctx.extra.get("business"))


def _email(inp: dict, ctx: ToolContext) -> dict:
    return send_email(
        (inp.get("to") or "").strip(), inp.get("subject", ""), inp.get("body", ""),
        business=ctx.extra.get("business"),
    )


def _sms_dedup_key(inp: dict, ctx: ToolContext) -> str:
    to = (inp.get("to") or "").strip() or (ctx.caller_phone or "")
    return f"sms:{to}"


def build_registry() -> ToolRegistry:
    return ToolRegistry([
        Tool("qualify_lead", _desc("qualify_lead"), _schema("qualify_lead"), _qualify, dedup=True),
        Tool("book_appointment", _desc("book_appointment"), _schema("book_appointment"), _book, dedup=True),
        Tool("draft_quote", _desc("draft_quote"), _schema("draft_quote"), _quote, dedup=True),
        Tool("check_availability", _desc("check_availability"), _schema("check_availability"), _availability, dedup=True),
        # One SMS per recipient per call, and don't cache a failed send.
        Tool("send_sms", _desc("send_sms"), _schema("send_sms"), _sms,
             dedup=True, dedup_key=_sms_dedup_key,
             cache_predicate=lambda r: bool(r.get("success") or r.get("ok"))),
        Tool("send_email", _desc("send_email"), _schema("send_email"), _email),
        Tool("end_call", _desc("end_call"), _schema("end_call"),
             handler=lambda inp, ctx: (logger.info("[END_CALL] %s", inp.get("reason")), {"ok": True})[1],
             terminal=True),
    ])


_REGISTRY = build_registry()


def _resolve_business(call_id: str | None) -> Business | None:
    biz = next((b for b in Business.objects.all().order_by("id")
                if (b.anthropic_api_key or "").strip()), None)
    return biz or Business.objects.order_by("id").first()


def _provider_config(biz: Business | None) -> ProviderConfig:
    provider = (getattr(biz, "llm_provider", "") or "anthropic").lower()
    key = (biz.resolved_anthropic_key if provider == "anthropic" else biz.resolved_openai_key) if biz else ""
    return ProviderConfig(provider=provider, api_key=key, max_tokens=1024)


def _build_system_prompt(biz: Business | None, caller_phone: str | None,
                         call_id: str | None, agent: VoiceAgent) -> str:
    persona = (getattr(biz, "voice_persona", "") or "Mary").strip() or "Mary"
    base = get_receptionist_prompt(
        business_name=biz.name if biz else "Workflow Auth",
        trade=biz.trade if biz else "general",
        knowledge_base=biz.knowledge_base if biz else "",
        timezone=biz.timezone if biz else "America/Los_Angeles",
        currency=(getattr(biz, "currency", "") or "USD"),
        persona_name=persona,
    )

    builder = PromptBuilder(base)
    if caller_phone:
        builder.section("CALLER INFO:", f"- Caller's phone is {caller_phone}. Use it as the default contact.")
    else:
        builder.section("CALLER INFO:", "- Caller ID unavailable. Ask for the phone number early.")

    done = _REGISTRY.completed_this_call(agent.call_state(call_id))
    if done:
        builder.section(
            "TOOLS ALREADY DONE THIS CALL:",
            ", ".join(done) + ".\nDon't re-fire these; all other tools remain available.",
        )
    return builder.build()


def handle_turn(conversation_history: list, caller_phone: str | None = None,
                call_id: str | None = None) -> dict[str, Any]:
    """Public contract identical to the old handle_conversation_turn."""
    biz = _resolve_business(call_id)
    persona = (getattr(biz, "voice_persona", "") or "Mary").strip() or "Mary"

    agent = VoiceAgent.create(
        provider_config=_provider_config(biz),
        registry=_REGISTRY,
        config=AgentConfig(
            persona_name=persona,
            completion_tools=("book_appointment", "send_sms"),
        ),
        state_store=_STORE,
    )

    system_prompt = _build_system_prompt(biz, caller_phone, call_id, agent)
    result = agent.handle_turn(
        conversation_history,
        system_prompt=system_prompt,
        call_id=call_id,
        caller_phone=caller_phone,
        context_extra={"business": biz},
    )
    return {"text": result.text, "end_call": result.end_call}

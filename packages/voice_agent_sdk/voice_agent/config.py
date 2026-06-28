"""Configuration dataclasses for the SDK.

Everything that used to be a module-level constant or an env lookup buried in
``receptionist.py`` lives here as explicit, injectable config. Nothing reads
``os.environ`` or Django settings — the host app resolves values (per-tenant
override -> env fallback) and hands them in.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .metrics import TurnMetrics


@dataclass
class ProviderConfig:
    """Which LLM backs a turn, and with what credentials/limits.

    `provider` selects the implementation ("anthropic" | "openai"). Pass the
    key your host app already resolved (tenant credential or env fallback) —
    the SDK never reads the environment itself.
    """

    provider: str = "anthropic"
    api_key: str = ""
    model: str = ""  # empty -> provider default (see providers/*.py)
    max_tokens: int = 1024
    temperature: float | None = None

    # Mark the stable request prefix (system prompt + tool schemas) with
    # Anthropic's cache_control so repeated turns in a call reuse it — large KB
    # prompts get materially cheaper and faster after the first turn. No-op for
    # providers that cache automatically (OpenAI) or don't support it.
    prompt_caching: bool = True

    def normalized(self) -> "ProviderConfig":
        return ProviderConfig(
            provider=(self.provider or "anthropic").strip().lower(),
            api_key=(self.api_key or "").strip(),
            model=(self.model or "").strip(),
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            prompt_caching=self.prompt_caching,
        )


@dataclass
class AgentConfig:
    """Behavioural knobs for the agentic loop.

    Defaults reproduce Workflow Auth's production behaviour, but every voice-UX
    workaround is now a flag you can turn off in a non-voice context (e.g. a
    text chat widget doesn't need the two-turn hangup dance).
    """

    persona_name: str = "Assistant"

    # Stop runaway tool loops. The original code had no explicit cap and relied
    # on the model terminating; this is a hard safety net.
    max_tool_iterations: int = 8

    # Voice-only: never hang up in the same turn as the goodbye line, or the TTS
    # gets cut off. Defer the first end_call so the closing audio plays, then
    # honour the next one. Disable for text channels.
    defer_end_call_once: bool = True
    # A closing line shorter than this many chars is treated as "no real message
    # to play", so the hangup fires immediately instead of deferring.
    defer_min_closing_chars: int = 12

    # When the model says "let me draft that..." but never calls the tool, send
    # one explicit nudge and retry. Off by default for non-tool conversations.
    nudge_on_verbalized_intent: bool = True
    intent_phrases: tuple[str, ...] = (
        "let me draft", "let me get", "i'll draft", "i'll book",
        "let me book", "drafting that", "drafting it", "let me put",
        "one moment", "right now", "let me do that",
    )

    # Fallback spoken line when the model ends a turn on a tool with no text.
    # If the last tool called is in `completion_tools` (e.g. a booking/SMS that
    # finishes the job) use the upbeat line, otherwise the neutral one.
    completion_tools: tuple[str, ...] = ()
    fallback_after_completion: str = "You're all set! Anything else I can help with?"
    fallback_generic: str = "Is there anything else I can help you with?"

    # Validate tool input against the tool's input_schema before dispatch. On a
    # mismatch the handler is skipped and the model gets a specific, recoverable
    # error (e.g. "party_size is required") instead of the handler raising. Turn
    # off only if your handlers do their own validation.
    validate_tool_input: bool = True

    # Per-call state TTL (seconds) — longer than any realistic call.
    call_state_ttl: int = 60 * 60

    # Optional sink for per-turn metrics (latency, llm round-trips, tokens, tool
    # counts). Called once per handle_turn with a TurnMetrics. Exceptions raised
    # by the callback are swallowed — observability must never break a live call.
    on_turn: Callable[["TurnMetrics"], None] | None = None

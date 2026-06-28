"""VoiceAgent — one agentic loop, any provider.

This replaces both ``handle_conversation_turn`` (Anthropic) and
``run_openai_loop`` (OpenAI). The provider-specific parts moved behind
``BaseLLMProvider``; what's left here is the *behaviour* that was tangled into
those loops:

  * run tools until the model stops asking for them (with a hard iteration cap)
  * nudge the model once when it narrates intent but never fires the tool
  * never crash a turn on a tool error — feed the error back as a tool_result
  * defer the first end_call so the TTS can finish the goodbye line
  * supply a sensible spoken fallback when the model ends on a tool with no text
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from .config import AgentConfig, ProviderConfig
from .conversation import Messages
from .errors import ProviderNotConfigured, ToolExecutionError, ToolNotFound
from .metrics import TurnMetrics
from .providers import BaseLLMProvider, ToolResultPayload, build_provider
from .state import CallState, InMemoryStateStore, StateStore
from .tools import ToolContext, ToolRegistry
from .validation import validate_against_schema

logger = logging.getLogger("voice_agent.agent")

_NUDGE = "[system: please call the actual tool now — don't just talk about it]"


@dataclass
class TurnResult:
    text: str
    end_call: bool = False
    tools_called: list[str] = field(default_factory=list)
    stubbed: bool = False  # True when no provider was configured


class VoiceAgent:
    def __init__(
        self,
        provider: BaseLLMProvider | None,
        registry: ToolRegistry,
        config: AgentConfig | None = None,
        state_store: StateStore | None = None,
    ) -> None:
        self.provider = provider
        self.registry = registry
        self.config = config or AgentConfig()
        self.store: StateStore = state_store or InMemoryStateStore()

    @classmethod
    def create(
        cls,
        *,
        provider_config: ProviderConfig,
        registry: ToolRegistry,
        config: AgentConfig | None = None,
        state_store: StateStore | None = None,
    ) -> "VoiceAgent":
        """Build an agent, resolving the provider. If the provider can't be
        constructed (no key / SDK missing), the agent still works — it returns a
        friendly stub line — so local dev and key-less environments never crash."""
        try:
            provider: BaseLLMProvider | None = build_provider(provider_config)
        except ProviderNotConfigured as exc:
            logger.warning("[VOICE AGENT] provider unavailable (%s) — stubbing replies", exc)
            provider = None
        return cls(provider, registry, config, state_store)

    def call_state(self, call_id: str | None) -> CallState:
        return CallState(self.store, call_id, ttl=self.config.call_state_ttl)

    def handle_turn(
        self,
        history: Messages,
        *,
        system_prompt: str,
        call_id: str | None = None,
        caller_phone: str | None = None,
        context_extra: dict | None = None,
    ) -> TurnResult:
        metrics = TurnMetrics(call_id=call_id)
        started = time.perf_counter()

        if self.provider is None:
            metrics.stubbed = True
            metrics.duration_ms = (time.perf_counter() - started) * 1000
            self._emit_metrics(metrics)
            return TurnResult(text=self._stub_line(), stubbed=True)

        metrics.provider = self.provider.config.provider
        metrics.model = self.provider.model

        state = self.call_state(call_id)
        ctx = ToolContext(
            call_id=call_id, caller_phone=caller_phone, state=state,
            extra=context_extra or {},
        )

        native = self.provider.prepare_messages(history)
        native_tools = self.provider.format_tools(self.registry.schemas())

        response = self._complete(system_prompt, native_tools, native, metrics)
        logger.info("[LLM] stop=%s tools=%s", response.stop_reason,
                    [t.name for t in response.tool_calls])

        response = self._maybe_nudge(response, system_prompt, native_tools, native, metrics)

        should_end = False
        tools_called: list[str] = []
        iterations = 0

        while response.wants_tools and iterations < self.config.max_tool_iterations:
            iterations += 1
            results: list[ToolResultPayload] = []
            end_requested = False

            for call in response.tool_calls:
                if self.registry.is_terminal(call.name):
                    inv = self._safe_dispatch(call.name, call.input, ctx)
                    end_requested = True
                    results.append(ToolResultPayload(call.id, call.name, inv))
                    continue
                tools_called.append(call.name)
                logger.info("[TOOL] %s", call.name)
                result = self._safe_dispatch(call.name, call.input, ctx)
                logger.info("[RESULT] %s", result)
                results.append(ToolResultPayload(call.id, call.name, result))

            self.provider.record_assistant(native, response)
            self.provider.record_tool_results(native, results)

            if end_requested:
                should_end = True
                break

            response = self._complete(system_prompt, native_tools, native, metrics)

        text = response.text or self._fallback_text(tools_called)
        should_end = self._apply_end_call_deferral(should_end, text, state)

        metrics.tool_iterations = iterations
        metrics.tools_called = tools_called
        metrics.end_call = should_end
        metrics.duration_ms = (time.perf_counter() - started) * 1000
        self._emit_metrics(metrics)

        logger.info("[VOICE AGENT] reply=%r end_call=%s", text[:120], should_end)
        return TurnResult(text=text, end_call=should_end, tools_called=tools_called)

    async def ahandle_turn(
        self,
        history: Messages,
        *,
        system_prompt: str,
        call_id: str | None = None,
        caller_phone: str | None = None,
        context_extra: dict | None = None,
    ) -> TurnResult:
        """Async twin of handle_turn — same behaviour, awaits the provider so a
        slow LLM call doesn't tie up a worker. Requires a provider that
        implements acomplete() (the built-in Anthropic/OpenAI providers do).
        Tool handlers still run synchronously; keep them quick or offload IO."""
        metrics = TurnMetrics(call_id=call_id)
        started = time.perf_counter()

        if self.provider is None:
            metrics.stubbed = True
            metrics.duration_ms = (time.perf_counter() - started) * 1000
            self._emit_metrics(metrics)
            return TurnResult(text=self._stub_line(), stubbed=True)

        metrics.provider = self.provider.config.provider
        metrics.model = self.provider.model

        state = self.call_state(call_id)
        ctx = ToolContext(
            call_id=call_id, caller_phone=caller_phone, state=state,
            extra=context_extra or {},
        )

        native = self.provider.prepare_messages(history)
        native_tools = self.provider.format_tools(self.registry.schemas())

        response = await self._acomplete(system_prompt, native_tools, native, metrics)
        response = await self._amaybe_nudge(response, system_prompt, native_tools, native, metrics)

        should_end = False
        tools_called: list[str] = []
        iterations = 0

        while response.wants_tools and iterations < self.config.max_tool_iterations:
            iterations += 1
            results: list[ToolResultPayload] = []
            end_requested = False

            for call in response.tool_calls:
                if self.registry.is_terminal(call.name):
                    inv = self._safe_dispatch(call.name, call.input, ctx)
                    end_requested = True
                    results.append(ToolResultPayload(call.id, call.name, inv))
                    continue
                tools_called.append(call.name)
                result = self._safe_dispatch(call.name, call.input, ctx)
                results.append(ToolResultPayload(call.id, call.name, result))

            self.provider.record_assistant(native, response)
            self.provider.record_tool_results(native, results)

            if end_requested:
                should_end = True
                break

            response = await self._acomplete(system_prompt, native_tools, native, metrics)

        text = response.text or self._fallback_text(tools_called)
        should_end = self._apply_end_call_deferral(should_end, text, state)

        metrics.tool_iterations = iterations
        metrics.tools_called = tools_called
        metrics.end_call = should_end
        metrics.duration_ms = (time.perf_counter() - started) * 1000
        self._emit_metrics(metrics)
        return TurnResult(text=text, end_call=should_end, tools_called=tools_called)

    # ------------------------------------------------------------------ #
    def _complete(self, system: str, tools: list, messages: list, metrics: TurnMetrics):
        """One provider round-trip, accumulating call count + token usage."""
        response = self.provider.complete(system=system, tools=tools, messages=messages)
        metrics.llm_calls += 1
        usage = response.usage or {}
        metrics.input_tokens += usage.get("input_tokens", 0)
        metrics.output_tokens += usage.get("output_tokens", 0)
        return response

    async def _acomplete(self, system: str, tools: list, messages: list, metrics: TurnMetrics):
        response = await self.provider.acomplete(system=system, tools=tools, messages=messages)
        metrics.llm_calls += 1
        usage = response.usage or {}
        metrics.input_tokens += usage.get("input_tokens", 0)
        metrics.output_tokens += usage.get("output_tokens", 0)
        return response

    async def _amaybe_nudge(self, response, system_prompt, native_tools, native, metrics):
        if not self.config.nudge_on_verbalized_intent or response.wants_tools:
            return response
        low = (response.text or "").lower()
        if not any(p in low for p in self.config.intent_phrases):
            return response
        self.provider.record_assistant(native, response)
        native.append({"role": "user", "content": _NUDGE})
        return await self._acomplete(system_prompt, native_tools, native, metrics)

    def _emit_metrics(self, metrics: TurnMetrics) -> None:
        if self.config.on_turn is None:
            return
        try:
            self.config.on_turn(metrics)
        except Exception as exc:  # noqa: BLE001 — telemetry must never break a call
            logger.warning("[METRICS] on_turn callback raised: %s", exc)

    def _safe_dispatch(self, name: str, tool_input: dict, ctx: ToolContext) -> dict:
        """Dispatch a tool, converting any failure into a tool_result the model
        can read — a live call must never 500 on a tool bug."""
        invalid = self._validation_error(name, tool_input)
        if invalid is not None:
            return invalid
        try:
            return self.registry.dispatch(name, tool_input, ctx).result
        except ToolNotFound:
            return {"error": f"Unknown tool: {name}"}
        except ToolExecutionError as exc:
            logger.error("[TOOL ERROR] %s: %s", name, exc)
            return {"error": str(exc)}

    def _validation_error(self, name: str, tool_input: dict) -> dict | None:
        """If input validation is on and the tool input doesn't match its schema,
        return a recoverable error result (skipping the handler); else None."""
        if not self.config.validate_tool_input:
            return None
        tool = self.registry.get(name)
        if tool is None or tool.terminal:
            return None
        errors = validate_against_schema(tool_input, tool.input_schema)
        if not errors:
            return None
        logger.info("[VALIDATION] %s rejected: %s", name, errors)
        return {"error": "Invalid tool input: " + "; ".join(errors),
                "validation_errors": errors}

    def _maybe_nudge(self, response, system_prompt, native_tools, native, metrics):
        if not self.config.nudge_on_verbalized_intent or response.wants_tools:
            return response
        low = (response.text or "").lower()
        if not any(p in low for p in self.config.intent_phrases):
            return response
        logger.info("[NUDGE] verbalized intent without tool_use — retrying")
        self.provider.record_assistant(native, response)
        native.append({"role": "user", "content": _NUDGE})
        return self._complete(system_prompt, native_tools, native, metrics)

    def _fallback_text(self, tools_called: list[str]) -> str:
        if not tools_called:
            return ""
        if tools_called[-1] in self.config.completion_tools:
            return self.config.fallback_after_completion
        return self.config.fallback_generic

    def _apply_end_call_deferral(self, should_end: bool, text: str, state: CallState) -> bool:
        if not (should_end and self.config.defer_end_call_once):
            return should_end
        if state.end_call_deferred():
            return True  # already deferred once — honour the hangup now
        if len(text or "") > self.config.defer_min_closing_chars:
            state.mark_end_call_deferred()
            return False  # hold the hangup so the goodbye audio plays
        return True

    def _stub_line(self) -> str:
        return (
            f"{self.config.persona_name} here. I'd love to help, but my AI brain "
            "isn't connected right now. Please call back in a moment."
        )

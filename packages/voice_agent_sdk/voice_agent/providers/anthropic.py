"""Anthropic (Claude) provider."""
from __future__ import annotations

import json

from ..conversation import Messages
from ..errors import ProviderNotConfigured
from .base import BaseLLMProvider, LLMResponse, ToolCall, ToolResultPayload


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, config) -> None:
        super().__init__(config)
        if not self.config.api_key:
            raise ProviderNotConfigured("anthropic: no api_key")
        try:
            import anthropic  # noqa: WPS433 — optional dependency, imported on use
        except ImportError as exc:
            raise ProviderNotConfigured("anthropic SDK not installed") from exc
        self._client = anthropic.Anthropic(api_key=self.config.api_key)
        self._aclient = None  # built lazily on first async call

    def default_model(self) -> str:
        return "claude-sonnet-4-6"

    def prepare_messages(self, history: Messages) -> list:
        # Canonical history is already Anthropic-shaped; copy so we don't mutate
        # the caller's list as we append assistant/tool turns.
        return list(history)

    def format_tools(self, schemas: list[dict]) -> list:
        return schemas  # already Anthropic format

    _CACHE_CONTROL = {"type": "ephemeral"}

    def _request_kwargs(self, *, system: str, tools: list, messages: list) -> dict:
        """Assemble the messages.create kwargs. Split out from complete() so the
        request shape (especially prompt-cache markers) is unit-testable without
        the anthropic SDK or a network call."""
        system_field: object = system
        tool_field = tools
        if self.config.prompt_caching:
            # Cache the two stable prefix segments: the system prompt and the
            # tool definitions. A breakpoint on the last tool covers the whole
            # tools array; one on the system block covers the system text.
            if system:
                system_field = [
                    {"type": "text", "text": system, "cache_control": self._CACHE_CONTROL}
                ]
            if tools:
                tool_field = [dict(t) for t in tools]
                tool_field[-1] = {**tool_field[-1], "cache_control": self._CACHE_CONTROL}
        kwargs = dict(
            model=self.model,
            max_tokens=self.config.max_tokens,
            system=system_field,
            tools=tool_field,
            messages=messages,
        )
        if self.config.temperature is not None:
            kwargs["temperature"] = self.config.temperature
        return kwargs

    def complete(self, *, system: str, tools: list, messages: list) -> LLMResponse:
        resp = self._client.messages.create(
            **self._request_kwargs(system=system, tools=tools, messages=messages)
        )
        return self._parse(resp)

    async def acomplete(self, *, system: str, tools: list, messages: list) -> LLMResponse:
        if self._aclient is None:
            import anthropic  # noqa: WPS433
            self._aclient = anthropic.AsyncAnthropic(api_key=self.config.api_key)
        resp = await self._aclient.messages.create(
            **self._request_kwargs(system=system, tools=tools, messages=messages)
        )
        return self._parse(resp)

    def _parse(self, resp) -> LLMResponse:
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        tool_calls = [
            ToolCall(id=b.id, name=b.name, input=dict(b.input or {}))
            for b in resp.content if b.type == "tool_use"
        ]
        usage = getattr(resp, "usage", None)
        return LLMResponse(
            text=text,
            tool_calls=tool_calls,
            stop_reason=resp.stop_reason or "",
            raw=resp.to_dict()["content"],
            usage={
                "input_tokens": getattr(usage, "input_tokens", 0) or 0,
                "output_tokens": getattr(usage, "output_tokens", 0) or 0,
            } if usage else {},
        )

    def record_assistant(self, messages: list, response: LLMResponse) -> None:
        messages.append({"role": "assistant", "content": response.raw})

    def record_tool_results(self, messages: list, results: list[ToolResultPayload]) -> None:
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": r.call_id,
                    "content": json.dumps(r.content, default=str),
                }
                for r in results
            ],
        })

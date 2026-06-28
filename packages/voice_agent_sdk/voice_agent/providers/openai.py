"""OpenAI (chat-completions) provider."""
from __future__ import annotations

import json
import logging

from ..conversation import Messages, canonical_to_openai, tools_to_openai
from ..errors import ProviderNotConfigured
from .base import BaseLLMProvider, LLMResponse, ToolCall, ToolResultPayload

logger = logging.getLogger("voice_agent.providers.openai")


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, config) -> None:
        super().__init__(config)
        if not self.config.api_key:
            raise ProviderNotConfigured("openai: no api_key")
        try:
            import openai  # noqa: WPS433 — optional dependency, imported on use
        except ImportError as exc:
            raise ProviderNotConfigured("openai SDK not installed") from exc
        self._client = openai.OpenAI(api_key=self.config.api_key)
        self._aclient = None  # built lazily on first async call

    def default_model(self) -> str:
        return "gpt-4o"

    def prepare_messages(self, history: Messages) -> list:
        # System is injected per-request in complete(), so it's excluded here.
        return canonical_to_openai(history)

    def format_tools(self, schemas: list[dict]) -> list:
        return tools_to_openai(schemas)

    def _request_kwargs(self, *, system: str, tools: list, messages: list) -> dict:
        kwargs = dict(
            model=self.model,
            max_tokens=self.config.max_tokens,
            tools=tools,
            messages=[{"role": "system", "content": system}, *messages],
        )
        if self.config.temperature is not None:
            kwargs["temperature"] = self.config.temperature
        return kwargs

    def complete(self, *, system: str, tools: list, messages: list) -> LLMResponse:
        resp = self._client.chat.completions.create(
            **self._request_kwargs(system=system, tools=tools, messages=messages)
        )
        return self._parse(resp)

    async def acomplete(self, *, system: str, tools: list, messages: list) -> LLMResponse:
        if self._aclient is None:
            import openai  # noqa: WPS433
            self._aclient = openai.AsyncOpenAI(api_key=self.config.api_key)
        resp = await self._aclient.chat.completions.create(
            **self._request_kwargs(system=system, tools=tools, messages=messages)
        )
        return self._parse(resp)

    def _parse(self, resp) -> LLMResponse:
        choice = resp.choices[0]
        msg = choice.message

        tool_calls: list[ToolCall] = []
        for tc in msg.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                logger.warning("bad tool args for %s: %r", tc.function.name, tc.function.arguments)
                args = {}
            tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, input=args))

        usage = getattr(resp, "usage", None)
        return LLMResponse(
            text=(msg.content or "").strip(),
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason or "",
            raw=msg,
            usage={
                "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                "output_tokens": getattr(usage, "completion_tokens", 0) or 0,
            } if usage else {},
        )

    def record_assistant(self, messages: list, response: LLMResponse) -> None:
        msg: dict = {"role": "assistant", "content": response.text or None}
        # Omit the key entirely when empty — OpenAI rejects an empty tool_calls
        # array. This path is hit by the verbalized-intent nudge (text, no tools).
        if response.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.input)},
                }
                for tc in response.tool_calls
            ]
        messages.append(msg)

    def record_tool_results(self, messages: list, results: list[ToolResultPayload]) -> None:
        for r in results:
            messages.append({
                "role": "tool",
                "tool_call_id": r.call_id,
                "content": json.dumps(r.content, default=str),
            })

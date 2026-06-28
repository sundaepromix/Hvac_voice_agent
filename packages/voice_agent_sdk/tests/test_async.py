"""Async loop parity: ahandle_turn mirrors handle_turn over an async provider."""
from __future__ import annotations

import pytest

from voice_agent import (
    AgentConfig,
    InMemoryStateStore,
    ProviderConfig,
    Tool,
    ToolRegistry,
    VoiceAgent,
)
from voice_agent.providers.base import LLMResponse, ToolCall


def _agent(counter, **cfg):
    def qualify(inp, ctx):
        counter["qualify"] += 1
        return {"success": True, "lead_id": 7}

    registry = ToolRegistry([
        Tool("qualify", "q", {"type": "object", "properties": {}}, qualify, dedup=True),
        Tool("end_call", "e", {"type": "object", "properties": {}}, terminal=True),
    ])
    return VoiceAgent.create(
        provider_config=ProviderConfig(provider="scripted", api_key="x"),
        registry=registry,
        config=AgentConfig(persona_name="Mary", **cfg),
        state_store=InMemoryStateStore(),
    )


async def test_ahandle_turn_runs_tool_then_text(scripted):
    counter = {"qualify": 0}
    scripted(
        LLMResponse(text="", tool_calls=[ToolCall("1", "qualify", {})]),
        LLMResponse(text="You're qualified."),
    )
    agent = _agent(counter)
    r = await agent.ahandle_turn([{"role": "user", "content": "hi"}], system_prompt="p", call_id="a1")
    assert counter["qualify"] == 1
    assert r.text == "You're qualified."
    assert r.tools_called == ["qualify"]


async def test_ahandle_turn_emits_metrics(scripted):
    captured = []
    counter = {"qualify": 0}
    scripted(
        LLMResponse(text="", tool_calls=[ToolCall("1", "qualify", {})], usage={"input_tokens": 5, "output_tokens": 2}),
        LLMResponse(text="done", usage={"input_tokens": 6, "output_tokens": 1}),
    )
    agent = _agent(counter, on_turn=captured.append)
    await agent.ahandle_turn([{"role": "user", "content": "hi"}], system_prompt="p", call_id="a2")
    assert captured[0].llm_calls == 2
    assert captured[0].total_tokens == 14


async def test_async_stub_when_no_provider():
    agent = VoiceAgent.create(
        provider_config=ProviderConfig(provider="anthropic", api_key=""),
        registry=ToolRegistry([Tool("end_call", "e", {"type": "object", "properties": {}}, terminal=True)]),
        config=AgentConfig(persona_name="Mary"),
    )
    r = await agent.ahandle_turn([{"role": "user", "content": "hi"}], system_prompt="p", call_id="a3")
    assert r.stubbed is True and "Mary" in r.text


def test_base_provider_acomplete_not_implemented_by_default():
    """A sync-only provider surfaces a clear error rather than silently failing."""
    import asyncio

    from voice_agent.providers.base import BaseLLMProvider

    class SyncOnly(BaseLLMProvider):
        def default_model(self): return "x"
        def prepare_messages(self, h): return list(h)
        def format_tools(self, s): return s
        def complete(self, *, system, tools, messages): return LLMResponse(text="")
        def record_assistant(self, m, r): ...
        def record_tool_results(self, m, r): ...

    p = SyncOnly(ProviderConfig(provider="x", api_key="k"))
    with pytest.raises(NotImplementedError):
        asyncio.run(p.acomplete(system="", tools=[], messages=[]))

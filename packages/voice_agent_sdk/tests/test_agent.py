"""Loop behaviour: tool dispatch, dedup, end_call deferral, error recovery, stub."""
from __future__ import annotations

from voice_agent import (
    AgentConfig,
    InMemoryStateStore,
    ProviderConfig,
    Tool,
    ToolRegistry,
    VoiceAgent,
)
from voice_agent.providers.base import LLMResponse, ToolCall


def _registry(counter):
    def qualify(inp, ctx):
        counter["qualify"] += 1
        return {"success": True, "lead_id": 7}

    def boom(inp, ctx):
        raise RuntimeError("db down")

    return ToolRegistry([
        Tool("qualify_lead", "q", {"type": "object", "properties": {}}, qualify, dedup=True),
        Tool("boom", "b", {"type": "object", "properties": {}}, boom),
        Tool("end_call", "e", {"type": "object", "properties": {}}, terminal=True),
    ])


def _agent(counter, store=None, **cfg):
    return VoiceAgent.create(
        provider_config=ProviderConfig(provider="scripted", api_key="x"),
        registry=_registry(counter),
        config=AgentConfig(persona_name="Mary", **cfg),
        state_store=store or InMemoryStateStore(),
    )


def test_runs_tool_then_returns_text(scripted):
    counter = {"qualify": 0}
    scripted(
        LLMResponse(text="", tool_calls=[ToolCall("1", "qualify_lead", {})]),
        LLMResponse(text="You're qualified."),
    )
    agent = _agent(counter)
    r = agent.handle_turn([{"role": "user", "content": "hi"}], system_prompt="p", call_id="c1")
    assert counter["qualify"] == 1
    assert r.text == "You're qualified."
    assert r.end_call is False
    assert r.tools_called == ["qualify_lead"]


def test_dedup_across_turns(scripted):
    counter = {"qualify": 0}
    store = InMemoryStateStore()
    agent = _agent(counter, store=store)

    scripted(
        LLMResponse(text="", tool_calls=[ToolCall("1", "qualify_lead", {})]),
        LLMResponse(text="Done."),
    )
    agent.handle_turn([{"role": "user", "content": "hi"}], system_prompt="p", call_id="c1")

    scripted(
        LLMResponse(text="", tool_calls=[ToolCall("2", "qualify_lead", {})]),
        LLMResponse(text="Still done."),
    )
    agent.handle_turn([{"role": "user", "content": "again"}], system_prompt="p", call_id="c1")
    assert counter["qualify"] == 1  # second call served from cache
    assert agent.registry.completed_this_call(agent.call_state("c1")) == ["qualify_lead"]


def test_end_call_defers_once_then_fires(scripted):
    counter = {"qualify": 0}
    agent = _agent(counter, completion_tools=("qualify_lead",))

    scripted(LLMResponse(text="You're all set, goodbye!", tool_calls=[ToolCall("9", "end_call", {})]))
    r1 = agent.handle_turn([{"role": "user", "content": "bye"}], system_prompt="p", call_id="cE")
    assert r1.end_call is False  # deferred so TTS can play the goodbye

    scripted(LLMResponse(text="", tool_calls=[ToolCall("10", "end_call", {})]))
    r2 = agent.handle_turn([{"role": "user", "content": "ok"}], system_prompt="p", call_id="cE")
    assert r2.end_call is True


def test_short_closing_fires_immediately(scripted):
    counter = {"qualify": 0}
    agent = _agent(counter)
    scripted(LLMResponse(text="bye", tool_calls=[ToolCall("9", "end_call", {})]))
    r = agent.handle_turn([{"role": "user", "content": "bye"}], system_prompt="p", call_id="cS")
    assert r.end_call is True  # under defer_min_closing_chars -> no deferral


def test_tool_error_becomes_recoverable(scripted):
    counter = {"qualify": 0}
    agent = _agent(counter)
    scripted(
        LLMResponse(text="", tool_calls=[ToolCall("1", "boom", {})]),
        LLMResponse(text="Sorry, let me sort that out."),
    )
    r = agent.handle_turn([{"role": "user", "content": "x"}], system_prompt="p", call_id="cB")
    assert r.text == "Sorry, let me sort that out."  # loop survived the exception


def test_stub_when_no_provider():
    counter = {"qualify": 0}
    agent = VoiceAgent.create(
        provider_config=ProviderConfig(provider="anthropic", api_key=""),
        registry=_registry(counter),
        config=AgentConfig(persona_name="Mary"),
    )
    r = agent.handle_turn([{"role": "user", "content": "hi"}], system_prompt="p", call_id="c1")
    assert r.stubbed is True
    assert "Mary" in r.text


def test_nudge_retries_on_verbalized_intent(scripted):
    counter = {"qualify": 0}
    agent = _agent(counter)
    scripted(
        LLMResponse(text="Sure, let me draft that quote for you."),  # no tool -> triggers nudge
        LLMResponse(text="", tool_calls=[ToolCall("1", "qualify_lead", {})]),
        LLMResponse(text="All set."),
    )
    r = agent.handle_turn([{"role": "user", "content": "quote me"}], system_prompt="p", call_id="cN")
    assert counter["qualify"] == 1  # nudge made it actually fire the tool
    assert r.text == "All set."

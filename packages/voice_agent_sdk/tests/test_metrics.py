"""Per-turn metrics: counts, token aggregation, and callback safety."""
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


def _agent(captured, **cfg):
    def qualify(inp, ctx):
        return {"success": True}

    registry = ToolRegistry([
        Tool("qualify", "q", {"type": "object", "properties": {}}, qualify),
        Tool("end_call", "e", {"type": "object", "properties": {}}, terminal=True),
    ])
    return VoiceAgent.create(
        provider_config=ProviderConfig(provider="scripted", api_key="x"),
        registry=registry,
        config=AgentConfig(persona_name="Mary", on_turn=captured.append, **cfg),
        state_store=InMemoryStateStore(),
    )


def test_metrics_count_calls_tools_and_tokens(scripted):
    captured = []
    scripted(
        LLMResponse(text="", tool_calls=[ToolCall("1", "qualify", {})],
                    usage={"input_tokens": 100, "output_tokens": 20}),
        LLMResponse(text="All set.", usage={"input_tokens": 130, "output_tokens": 8}),
    )
    agent = _agent(captured)
    agent.handle_turn([{"role": "user", "content": "hi"}], system_prompt="p", call_id="c1")

    m = captured[0]
    assert m.call_id == "c1"
    assert m.llm_calls == 2
    assert m.tool_iterations == 1
    assert m.tools_called == ["qualify"]
    assert m.input_tokens == 230 and m.output_tokens == 28
    assert m.total_tokens == 258
    assert m.provider == "scripted"
    assert m.duration_ms >= 0


def test_metrics_emitted_for_stub():
    captured = []
    agent = VoiceAgent.create(
        provider_config=ProviderConfig(provider="anthropic", api_key=""),  # -> stub
        registry=ToolRegistry([Tool("end_call", "e", {"type": "object", "properties": {}}, terminal=True)]),
        config=AgentConfig(persona_name="Mary", on_turn=captured.append),
    )
    agent.handle_turn([{"role": "user", "content": "hi"}], system_prompt="p", call_id="c2")
    assert captured[0].stubbed is True
    assert captured[0].llm_calls == 0


def test_callback_exception_does_not_break_turn(scripted):
    def boom(_m):
        raise RuntimeError("metrics sink down")

    scripted(LLMResponse(text="Hello."))
    agent = _agent([], )
    agent.config.on_turn = boom
    r = agent.handle_turn([{"role": "user", "content": "hi"}], system_prompt="p", call_id="c3")
    assert r.text == "Hello."  # turn still succeeded

"""Schema validation: standalone validator + the agent's recoverable-error path."""
from __future__ import annotations

from voice_agent import (
    AgentConfig,
    InMemoryStateStore,
    ProviderConfig,
    Tool,
    ToolRegistry,
    VoiceAgent,
    validate_against_schema,
)
from voice_agent.providers.base import LLMResponse, ToolCall

_SCHEMA = {
    "type": "object",
    "properties": {
        "party_size": {"type": "integer"},
        "time": {"type": "string"},
        "channel": {"type": "string", "enum": ["sms", "email"]},
    },
    "required": ["party_size", "time"],
}


def test_valid_input_has_no_errors():
    assert validate_against_schema({"party_size": 4, "time": "7pm"}, _SCHEMA) == []


def test_missing_required_field():
    errs = validate_against_schema({"time": "7pm"}, _SCHEMA)
    assert errs == ["party_size is required"]


def test_wrong_type_reported():
    errs = validate_against_schema({"party_size": "four", "time": "7pm"}, _SCHEMA)
    assert errs == ["party_size must be a integer"]


def test_bool_is_not_an_integer():
    errs = validate_against_schema({"party_size": True, "time": "7pm"}, _SCHEMA)
    assert errs == ["party_size must be a integer"]


def test_enum_violation():
    errs = validate_against_schema(
        {"party_size": 2, "time": "7pm", "channel": "fax"}, _SCHEMA
    )
    assert any("channel" in e for e in errs)


def test_nested_array_items():
    schema = {"type": "object", "properties": {
        "ids": {"type": "array", "items": {"type": "integer"}}}}
    errs = validate_against_schema({"ids": [1, "two", 3]}, schema)
    assert errs == ["ids[1] must be a integer"]


def test_unknown_schema_does_not_false_reject():
    assert validate_against_schema({"anything": 1}, {}) == []
    assert validate_against_schema({"x": 1}, None) == []


# --- agent integration -------------------------------------------------------

def _agent_with_book(counter, **cfg):
    def book(inp, ctx):
        counter["book"] += 1
        return {"success": True}

    registry = ToolRegistry([
        Tool("book", "book a table", _SCHEMA, book),
        Tool("end_call", "e", {"type": "object", "properties": {}}, terminal=True),
    ])
    return VoiceAgent.create(
        provider_config=ProviderConfig(provider="scripted", api_key="x"),
        registry=registry,
        config=AgentConfig(persona_name="Sam", **cfg),
        state_store=InMemoryStateStore(),
    )


def test_invalid_input_skips_handler_and_recovers(scripted):
    counter = {"book": 0}
    scripted(
        LLMResponse(text="", tool_calls=[ToolCall("1", "book", {"time": "7pm"})]),  # missing party_size
        LLMResponse(text="How many people?"),
    )
    agent = _agent_with_book(counter)
    r = agent.handle_turn([{"role": "user", "content": "book"}], system_prompt="p", call_id="c1")
    assert counter["book"] == 0          # handler never ran
    assert r.text == "How many people?"  # model recovered on the next step


def test_validation_can_be_disabled(scripted):
    counter = {"book": 0}
    scripted(
        LLMResponse(text="", tool_calls=[ToolCall("1", "book", {"time": "7pm"})]),
        LLMResponse(text="ok"),
    )
    agent = _agent_with_book(counter, validate_tool_input=False)
    agent.handle_turn([{"role": "user", "content": "book"}], system_prompt="p", call_id="c2")
    assert counter["book"] == 1          # handler ran despite missing field

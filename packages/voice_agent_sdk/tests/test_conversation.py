"""Message/tool conversion between OpenAI and canonical (Anthropic) shapes."""
from __future__ import annotations

from voice_agent import canonical_to_openai, openai_to_canonical, tools_to_openai


def test_openai_to_canonical_drops_system_and_merges_roles():
    out = openai_to_canonical([
        {"role": "system", "content": "ignore me"},
        {"role": "user", "content": "a"},
        {"role": "user", "content": "b"},
        {"role": "assistant", "content": "c"},
    ])
    assert out == [
        {"role": "user", "content": "a\nb"},
        {"role": "assistant", "content": "c"},
    ]


def test_openai_to_canonical_prepends_user_when_starts_assistant():
    out = openai_to_canonical([{"role": "assistant", "content": "hi there"}])
    assert out[0]["role"] == "user"


def test_canonical_tool_use_to_openai():
    canonical = [
        {"role": "assistant", "content": [
            {"type": "text", "text": "let me check"},
            {"type": "tool_use", "id": "tu_1", "name": "check", "input": {"x": 1}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "tu_1", "content": {"ok": True}},
        ]},
    ]
    out = canonical_to_openai(canonical)
    assert out[0]["role"] == "assistant"
    assert out[0]["tool_calls"][0]["function"]["name"] == "check"
    assert out[1] == {"role": "tool", "tool_call_id": "tu_1", "content": '{"ok": true}'}


def test_tools_to_openai_shape():
    schemas = [{"name": "n", "description": "d", "input_schema": {"type": "object", "properties": {}}}]
    out = tools_to_openai(schemas)
    assert out[0]["type"] == "function"
    assert out[0]["function"]["name"] == "n"
    assert out[0]["function"]["parameters"] == {"type": "object", "properties": {}}

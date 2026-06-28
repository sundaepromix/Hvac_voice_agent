"""The public voice_agent.testing helpers behave as documented."""
from __future__ import annotations

import pytest

from voice_agent import Tool, ToolRegistry
from voice_agent.testing import call_tool, make_scripted_agent, say


def _registry(counter):
    def book(inp, ctx):
        counter["book"] += 1
        return {"success": True, "ref": "T-42"}

    return ToolRegistry([
        Tool("book_table", "book", {
            "type": "object",
            "properties": {"party_size": {"type": "integer"}, "time": {"type": "string"}},
            "required": ["party_size", "time"],
        }, book),
        Tool("end_call", "e", {"type": "object", "properties": {}}, terminal=True),
    ])


def test_scripted_agent_runs_tool_then_text():
    counter = {"book": 0}
    agent = make_scripted_agent(registry=_registry(counter), responses=[
        call_tool("book_table", {"party_size": 4, "time": "7pm"}),
        say("You're booked!"),
    ])
    r = agent.handle_turn([{"role": "user", "content": "table for 4 at 7"}],
                          system_prompt="PROMPT", call_id="t1")
    assert counter["book"] == 1
    assert r.text == "You're booked!"
    assert r.tools_called == ["book_table"]


def test_provider_records_requests():
    agent = make_scripted_agent(registry=_registry({"book": 0}), responses=[say("hi")])
    agent.handle_turn([{"role": "user", "content": "hello"}], system_prompt="SYS", call_id="t2")
    assert agent.provider.calls[0]["system"] == "SYS"


def test_running_out_of_script_raises():
    # Only one response, but the tool call forces a second completion.
    agent = make_scripted_agent(registry=_registry({"book": 0}), responses=[
        call_tool("book_table", {"party_size": 2, "time": "8pm"}),
    ])
    with pytest.raises(AssertionError, match="ran out of responses"):
        agent.handle_turn([{"role": "user", "content": "x"}], system_prompt="p", call_id="t3")

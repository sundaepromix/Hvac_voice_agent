"""Test/eval helpers for driving the agent without a live LLM.

Import from here in your own test suite — these let you script exactly what the
"model" returns each step and assert on the resulting turn, which is the seed of
a transcript-replay eval harness for prompt/tool changes:

    from voice_agent.testing import make_scripted_agent, say, call_tool

    agent = make_scripted_agent(registry=my_registry, responses=[
        call_tool("book_table", {"party_size": 4, "time": "7pm"}),
        say("You're booked!"),
    ])
    result = agent.handle_turn([{"role": "user", "content": "table for 4 at 7"}],
                               system_prompt=PROMPT, call_id="t1")
    assert "booked" in result.text

The ScriptedProvider is instance-based (each agent gets its own script + a
record of the requests it received), so tests don't share global state.
"""
from __future__ import annotations

from .agent import VoiceAgent
from .config import AgentConfig, ProviderConfig
from .providers.base import BaseLLMProvider, LLMResponse, ToolCall
from .state import StateStore


class ScriptedProvider(BaseLLMProvider):
    """A provider that returns pre-canned responses, one per completion.

    Records every request in ``.calls`` so a test can assert on what the agent
    sent (e.g. that the system prompt carried a 'tools already done' section, or
    that prompt-cache markers were applied)."""

    def __init__(self, responses, config: ProviderConfig | None = None) -> None:
        super().__init__(config or ProviderConfig(provider="scripted", api_key="x"))
        self.responses = list(responses)
        self.idx = 0
        self.calls: list[dict] = []

    def default_model(self) -> str:
        return "scripted"

    def prepare_messages(self, history):
        return list(history)

    def format_tools(self, schemas):
        return schemas

    def _next(self) -> LLMResponse:
        if self.idx >= len(self.responses):
            raise AssertionError(
                f"ScriptedProvider ran out of responses after {self.idx} "
                "completion(s) — the agent looped more than the script expected."
            )
        resp = self.responses[self.idx]
        self.idx += 1
        return resp

    def complete(self, *, system, tools, messages) -> LLMResponse:
        self.calls.append({"system": system, "tools": tools, "messages": list(messages)})
        return self._next()

    async def acomplete(self, *, system, tools, messages) -> LLMResponse:
        return self.complete(system=system, tools=tools, messages=messages)

    def record_assistant(self, messages, response) -> None:
        messages.append({"role": "assistant", "content": response.text or "[tool_use]"})

    def record_tool_results(self, messages, results) -> None:
        messages.append({"role": "user", "content": "[tool_results]"})


def say(text: str) -> LLMResponse:
    """A plain-text model reply (no tool calls)."""
    return LLMResponse(text=text)


def call_tool(name: str, tool_input: dict | None = None, *, id: str = "1",
              text: str = "") -> LLMResponse:
    """A model turn that calls one tool. ``id`` matches the tool_use/tool_call id."""
    return LLMResponse(text=text, tool_calls=[ToolCall(id=id, name=name, input=tool_input or {})])


def make_scripted_agent(*, registry, responses, config: AgentConfig | None = None,
                        state_store: StateStore | None = None) -> VoiceAgent:
    """Build a VoiceAgent backed by a fresh ScriptedProvider. ``responses`` is the
    full script consumed across however many turns/iterations the run needs."""
    provider = ScriptedProvider(responses)
    return VoiceAgent(provider, registry, config or AgentConfig(), state_store)


__all__ = ["ScriptedProvider", "say", "call_tool", "make_scripted_agent"]

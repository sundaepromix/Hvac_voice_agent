"""Shared test fixtures: a scriptable fake provider so the loop can be tested
without network access or API keys."""
from __future__ import annotations

import pytest

from voice_agent import register_provider
from voice_agent.providers.base import BaseLLMProvider, LLMResponse


class ScriptedProvider(BaseLLMProvider):
    """Returns pre-canned LLMResponses, one per complete() call."""

    script: list[LLMResponse] = []
    idx: int = 0

    def default_model(self) -> str:
        return "scripted"

    def prepare_messages(self, history):
        return list(history)

    def format_tools(self, schemas):
        return schemas

    def complete(self, *, system, tools, messages):
        resp = ScriptedProvider.script[ScriptedProvider.idx]
        ScriptedProvider.idx += 1
        return resp

    async def acomplete(self, *, system, tools, messages):
        return self.complete(system=system, tools=tools, messages=messages)

    def record_assistant(self, messages, response):
        messages.append({"role": "assistant", "content": "x"})

    def record_tool_results(self, messages, results):
        messages.append({"role": "user", "content": "tool_results"})


@pytest.fixture
def scripted():
    register_provider("scripted", ScriptedProvider)

    def _set(*responses: LLMResponse):
        ScriptedProvider.script = list(responses)
        ScriptedProvider.idx = 0

    yield _set
    ScriptedProvider.script = []
    ScriptedProvider.idx = 0

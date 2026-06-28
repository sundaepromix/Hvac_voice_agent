"""Anthropic prompt-cache markers on the stable request prefix.

We test _request_kwargs directly: constructing the client makes no network call,
and the kwargs assembly is where the cache_control placement lives.
"""
from __future__ import annotations

import pytest

from voice_agent import ProviderConfig
from voice_agent.providers import build_provider

anthropic = pytest.importorskip("anthropic")

_TOOLS = [
    {"name": "a", "description": "", "input_schema": {"type": "object", "properties": {}}},
    {"name": "b", "description": "", "input_schema": {"type": "object", "properties": {}}},
]


def _provider(caching: bool):
    return build_provider(
        ProviderConfig(provider="anthropic", api_key="x", prompt_caching=caching)
    )


def test_caching_marks_system_and_last_tool():
    kw = _provider(True)._request_kwargs(system="big stable prompt", tools=_TOOLS, messages=[])
    assert isinstance(kw["system"], list)
    assert kw["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert kw["system"][0]["text"] == "big stable prompt"
    # breakpoint on the last tool, not the first
    assert kw["tools"][-1]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in kw["tools"][0]


def test_caching_off_keeps_plain_shapes():
    kw = _provider(False)._request_kwargs(system="prompt", tools=_TOOLS, messages=[])
    assert kw["system"] == "prompt"
    assert all("cache_control" not in t for t in kw["tools"])


def test_caching_does_not_mutate_caller_tools():
    tools = [dict(t) for t in _TOOLS]
    _provider(True)._request_kwargs(system="p", tools=tools, messages=[])
    assert all("cache_control" not in t for t in tools)  # original list untouched

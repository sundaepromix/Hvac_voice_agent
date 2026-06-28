"""Per-turn metrics emitted to a pluggable callback.

A live voice turn is the unit you actually want to watch: how long it took, how
many LLM round-trips and tools it cost, and how many tokens it burned. The agent
fills a ``TurnMetrics`` for every turn and hands it to ``AgentConfig.on_turn`` if
set, so a host app can log it, push it to StatsD/OpenTelemetry, or assert on it
in tests — without the SDK taking a dependency on any metrics library.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TurnMetrics:
    call_id: str | None = None
    provider: str = ""
    model: str = ""
    duration_ms: float = 0.0
    llm_calls: int = 0          # provider.complete round-trips (incl. nudge)
    tool_iterations: int = 0    # loop passes that executed tools
    tools_called: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    end_call: bool = False
    stubbed: bool = False       # no provider configured -> stub reply

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

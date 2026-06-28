"""Provider abstraction.

The original code had two hand-written agentic loops (Anthropic in
``receptionist.py``, OpenAI in ``openai_loop.py``) that drifted apart over time.
The only real differences between them are: the wire shape of a request, how a
response is parsed, and how assistant/tool messages get appended back to
history. We isolate exactly those four concerns here so ``VoiceAgent`` can run
ONE loop against either provider.

A provider owns the *native* message list; the agent treats it as opaque.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..config import ProviderConfig
from ..conversation import Messages


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = ""
    raw: Any = None  # native assistant turn, used by record_assistant
    # Normalised token usage for this completion: {"input_tokens", "output_tokens"}.
    # Empty when the provider doesn't report it. Aggregated into TurnMetrics.
    usage: dict = field(default_factory=dict)

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


@dataclass
class ToolResultPayload:
    """A tool's output, ready to be written back into native history."""

    call_id: str  # tool_use id (Anthropic) / tool_call_id (OpenAI)
    name: str
    content: dict


class BaseLLMProvider(ABC):
    """Implement four methods and the agent loop works against your backend."""

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config.normalized()
        self.model = self.config.model or self.default_model()

    @abstractmethod
    def default_model(self) -> str: ...

    @abstractmethod
    def prepare_messages(self, history: Messages) -> list:
        """Convert canonical (Anthropic-shaped) history into native messages."""

    @abstractmethod
    def format_tools(self, schemas: list[dict]) -> list:
        """Convert canonical tool schemas into native tool definitions."""

    @abstractmethod
    def complete(self, *, system: str, tools: list, messages: list) -> LLMResponse: ...

    async def acomplete(self, *, system: str, tools: list, messages: list) -> LLMResponse:
        """Async twin of complete(). Optional: providers that don't override it
        can't be driven by VoiceAgent.ahandle_turn. Not abstract so existing and
        third-party sync-only providers keep working unchanged."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement async acomplete()"
        )

    @abstractmethod
    def record_assistant(self, messages: list, response: LLMResponse) -> None:
        """Append the model's tool-using turn so the next call has context."""

    @abstractmethod
    def record_tool_results(self, messages: list, results: list[ToolResultPayload]) -> None:
        """Append tool outputs in the provider's native convention."""

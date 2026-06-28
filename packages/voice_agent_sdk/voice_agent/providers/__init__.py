"""LLM provider implementations + factory."""
from __future__ import annotations

from ..config import ProviderConfig
from .base import BaseLLMProvider, LLMResponse, ToolCall, ToolResultPayload

_REGISTRY: dict[str, type[BaseLLMProvider]] = {}


def register_provider(name: str, cls: type[BaseLLMProvider]) -> None:
    """Register a custom provider so build() can construct it by name. Lets a
    host app add (say) a Bedrock or Azure provider without forking the SDK."""
    _REGISTRY[name.strip().lower()] = cls


def build_provider(config: ProviderConfig) -> BaseLLMProvider:
    """Construct the provider named in `config.provider`.

    Raises ProviderNotConfigured if the name is unknown, the SDK isn't
    installed, or no API key was supplied. Callers (VoiceAgent) catch this and
    fall back to a friendly stub instead of dropping the call.
    """
    cfg = config.normalized()
    cls = _REGISTRY.get(cfg.provider)
    if cls is None:
        from ..errors import ProviderNotConfigured
        raise ProviderNotConfigured(f"unknown provider: {cfg.provider!r}")
    return cls(cfg)


def _register_builtins() -> None:
    # Lazy so importing the package doesn't require the provider SDKs to exist.
    try:
        from .anthropic import AnthropicProvider
        register_provider("anthropic", AnthropicProvider)
    except Exception:  # noqa: BLE001 — registration is best-effort; build() reports the real error
        pass
    try:
        from .openai import OpenAIProvider
        register_provider("openai", OpenAIProvider)
    except Exception:  # noqa: BLE001
        pass


_register_builtins()

__all__ = [
    "BaseLLMProvider", "LLMResponse", "ToolCall", "ToolResultPayload",
    "build_provider", "register_provider",
]

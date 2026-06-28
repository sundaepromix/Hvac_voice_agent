"""voice_agent — a provider-agnostic agentic voice-receptionist toolkit.

Extracted from Workflow Auth's Mary agent. The SDK owns the *mechanics* of a
tool-using voice turn (the loop, dedup, prompt assembly, provider plumbing);
your app owns the *content* (tools, prompt copy, persistence, credentials).

Quick start:

    from voice_agent import (
        VoiceAgent, AgentConfig, ProviderConfig, ToolRegistry, Tool, ToolContext,
    )

    registry = ToolRegistry([
        Tool(name="end_call", description="Hang up.", terminal=True,
             input_schema={"type": "object", "properties": {}}),
        # ... your tools ...
    ])
    agent = VoiceAgent.create(
        provider_config=ProviderConfig(provider="anthropic", api_key=KEY),
        registry=registry,
        config=AgentConfig(persona_name="Mary"),
    )
    result = agent.handle_turn(history, system_prompt=PROMPT,
                               call_id=call_id, caller_phone=phone)
    print(result.text, result.end_call)
"""
from __future__ import annotations

from .agent import TurnResult, VoiceAgent
from .config import AgentConfig, ProviderConfig
from .conversation import (
    canonical_to_openai,
    openai_to_canonical,
    tools_to_openai,
)
from .currency import speaking_guide
from .errors import (
    ProviderNotConfigured,
    ToolExecutionError,
    ToolNotFound,
    VoiceAgentError,
)
from .integrations import (
    ConsoleEmailSender,
    ConsoleSmsSender,
    EmailSender,
    SmsSender,
    SmtpEmailSender,
    TwilioSmsSender,
)
from .metrics import TurnMetrics
from .prompts import PromptBuilder, current_datetime_section
from .providers import BaseLLMProvider, build_provider, register_provider
from .state import CallState, InMemoryStateStore, RedisStateStore, StateStore
from .tools import Tool, ToolContext, ToolInvocation, ToolRegistry
from .validation import validate_against_schema

__version__ = "0.2.0"

__all__ = [
    "VoiceAgent", "TurnResult", "TurnMetrics",
    "AgentConfig", "ProviderConfig",
    "ToolRegistry", "Tool", "ToolContext", "ToolInvocation",
    "PromptBuilder", "current_datetime_section", "speaking_guide",
    "CallState", "StateStore", "InMemoryStateStore", "RedisStateStore",
    "validate_against_schema",
    "BaseLLMProvider", "build_provider", "register_provider",
    "SmsSender", "EmailSender", "ConsoleSmsSender", "TwilioSmsSender",
    "ConsoleEmailSender", "SmtpEmailSender",
    "VoiceAgentError", "ProviderNotConfigured", "ToolNotFound", "ToolExecutionError",
    "__version__",
]

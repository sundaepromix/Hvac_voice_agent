"""Exception hierarchy for the voice_agent SDK."""
from __future__ import annotations


class VoiceAgentError(Exception):
    """Base class for every error the SDK raises on purpose."""


class ProviderNotConfigured(VoiceAgentError):
    """No usable LLM provider could be built (missing key or SDK not installed).

    The agent treats this as a recoverable condition: instead of 500-ing a live
    call it returns a friendly stub line. Catch it at the edge if you want to
    handle the fallback yourself.
    """


class ToolNotFound(VoiceAgentError):
    """A tool name returned by the model is not registered."""


class ToolExecutionError(VoiceAgentError):
    """A tool handler raised. The loop converts this into a tool_result the
    model can see, rather than crashing the turn — see VoiceAgent.handle_turn."""

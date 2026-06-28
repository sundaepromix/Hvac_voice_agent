# voice-agent-sdk

A provider-agnostic, framework-agnostic toolkit for building **agentic voice
receptionists** — the reusable core extracted from Workflow Auth's "Mary" agent.

The SDK owns the *mechanics* of a tool-using conversational turn. Your app owns
the *content*. That split is the whole point: drop this into any project
(Django, FastAPI, a Lambda, a CLI) and you only write tools + prompt copy.

```
┌─────────────────────────── your app ───────────────────────────┐
│  tools (handlers)   prompt copy   credentials   persistence     │
└───────────────┬─────────────────────────────────┬──────────────┘
                │ inject                            │
┌───────────────▼─────────────────────────────────▼──────────────┐
│  voice_agent SDK                                                │
│   VoiceAgent  ──  ToolRegistry  ──  PromptBuilder               │
│       │                                                         │
│   BaseLLMProvider (Anthropic | OpenAI | yours)                  │
│   StateStore (memory | Django cache | Redis)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Why it exists

The original agent had its value tangled into Django: two near-identical tool
loops (one per LLM), dedup logic wired to Django's cache, prompt assembly mixed
with home-services copy, and tool execution importing models directly. This
package factors all of that into clean, injectable pieces with **zero hard
dependencies** — the provider SDKs and Twilio are optional extras, lazy-imported
only when used.

## Install

```bash
pip install -e packages/voice_agent_sdk            # core only
pip install -e packages/voice_agent_sdk[anthropic] # + Claude
pip install -e packages/voice_agent_sdk[openai]    # + GPT
pip install -e packages/voice_agent_sdk[all]       # everything
```

## 60-second example

```python
from voice_agent import (
    VoiceAgent, AgentConfig, ProviderConfig, Tool, ToolContext, ToolRegistry,
)

def book_table(inp: dict, ctx: ToolContext) -> dict:
    return {"success": True, "ref": "T-42"}

registry = ToolRegistry([
    Tool("book_table", "Book a table.", {
        "type": "object",
        "properties": {"party_size": {"type": "integer"}, "time": {"type": "string"}},
        "required": ["party_size", "time"],
    }, handler=book_table, dedup=True),
    Tool("end_call", "Hang up.", {"type": "object", "properties": {}}, terminal=True),
])

agent = VoiceAgent.create(
    provider_config=ProviderConfig(provider="anthropic", api_key=KEY),
    registry=registry,
    config=AgentConfig(persona_name="Sam", completion_tools=("book_table",)),
)

result = agent.handle_turn(
    [{"role": "user", "content": "table for 4 at 7pm"}],
    system_prompt="You are Sam, a friendly restaurant host.",
    call_id="call-123",
    caller_phone="+15551234567",
)
print(result.text, result.end_call)
```

Run the full interactive demo:

```bash
python packages/voice_agent_sdk/examples/minimal_cli.py
```

## Core concepts

| Piece | What it does | Swap it for |
|---|---|---|
| `VoiceAgent` | Runs the agentic loop for one turn | — |
| `ProviderConfig` + `build_provider` | Selects + builds the LLM backend | `register_provider()` your own |
| `ToolRegistry` / `Tool` | Schema + handler + dedup policy per tool | any handlers you write |
| `ToolContext` | `call_id`, `caller_phone`, `state`, `extra` passed to handlers | — |
| `StateStore` | Per-call dedup/defer storage | `InMemoryStateStore`, Django cache, Redis |
| `PromptBuilder` | Compose base prompt + conditional sections | — |
| `speaking_guide(code)` | TTS-safe number phrasing per currency | — |
| `SmsSender` / `EmailSender` | Side-effect adapters with console stubs | Twilio, SMTP, yours |
| `TurnMetrics` + `AgentConfig.on_turn` | Per-turn latency / tokens / tool counts | log, StatsD, OTel |
| `validate_against_schema` | Pre-dispatch tool-input validation | `AgentConfig.validate_tool_input` |

## Behaviours you get for free

These were hard-won voice-UX fixes in the original; each is now a config flag:

- **Tool dedup per call** — Vapi replays history without tool results, so the
  model re-fires tools. Dedupable tools return their first result instead of
  re-running. (`Tool(dedup=True)`; per-target keys via `dedup_key`.)
- **Two-turn hangup** — never `end_call` in the same turn as the goodbye, or the
  TTS gets cut off. (`AgentConfig.defer_end_call_once`)
- **Intent nudge** — when the model says "let me draft that…" without calling
  the tool, it gets one explicit retry. (`AgentConfig.nudge_on_verbalized_intent`)
- **Never crash a live call** — tool exceptions become `tool_result` errors the
  model can recover from; a missing API key yields a spoken stub, not a 500.
- **Bad tool input is recoverable** — input is validated against the tool's
  schema before the handler runs, so a missing or wrong-typed field comes back
  as a specific message the model can fix, not a handler `KeyError`.
  (`AgentConfig.validate_tool_input`)
- **Cheaper repeat turns** — the stable prefix (system prompt + tools) is marked
  with Anthropic prompt caching by default. (`ProviderConfig.prompt_caching`)

## Async, metrics, and scaling

- **Async:** `await agent.ahandle_turn(...)` mirrors the sync loop over
  `AsyncAnthropic`/`AsyncOpenAI` so a slow LLM call doesn't tie up a worker.
- **Metrics:** set `AgentConfig.on_turn=fn` to receive a `TurnMetrics`
  (duration, `llm_calls`, `tools_called`, token totals) once per turn — wire it
  to your logger or OpenTelemetry. Callback errors never break the call.
- **Shared state:** `RedisStateStore(url=...)` (extra: `[redis]`) shares dedup
  across hosts; `InMemoryStateStore` for single-process, a Django cache adapter
  for single-host multi-worker (see the example).

## Testing your tools

```python
from voice_agent.testing import make_scripted_agent, say, call_tool

agent = make_scripted_agent(registry=my_registry, responses=[
    call_tool("book_table", {"party_size": 4, "time": "7pm"}),
    say("You're booked!"),
])
r = agent.handle_turn([{"role": "user", "content": "table for 4 at 7"}],
                      system_prompt=PROMPT, call_id="t1")
assert "booked" in r.text
```

## Plugging into an existing app

See [`examples/django_receptionist.py`](examples/django_receptionist.py) — a
drop-in replacement for `apps/calls/agent/receptionist.py` that keeps every bit
of business logic (persistence, pricing, the Mary prompt) and just routes it
through the SDK. It also shows a `DjangoCacheStore` (three methods) so dedup is
shared across gunicorn workers.

## Tests

```bash
pip install -e packages/voice_agent_sdk[dev]
pytest packages/voice_agent_sdk
```

## Architecture & migration notes

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the old→new mapping, design
rationale, and the optimization backlog.

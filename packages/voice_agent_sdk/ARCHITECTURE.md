# Architecture & migration notes

This document explains *why* the SDK is shaped the way it is, maps every piece
back to the original Workflow Auth code it came from, and lists the optimization
backlog.

## The problem with the original

The agent worked well in production, but its reusable value was welded to Django
and duplicated across providers:

1. **Two tool loops.** `receptionist.py` ran the Anthropic loop; `openai_loop.py`
   ran a near-identical OpenAI loop. Bug fixes (the end_call defer, the nudge)
   landed in one and drifted from the other.
2. **State was global + Django-only.** Module-level dicts (`_BIZ_CACHE`) and a
   dozen `cache.get/set` helpers (`_sms_already_sent`, `_tool_cache_get`,
   `_end_call_already_deferred`) hardcoded Django's cache. Unusable outside
   Django, untestable without it.
3. **Tool schema and execution were split and stringly-dispatched.** Schemas in
   `tools.py`, execution in a 30-line `if/elif` in `execute_tool`, dedup policy
   sprinkled inline per branch.
4. **Prompt assembly mixed mechanism and content.** Generic "append a section if
   non-empty" logic was interleaved with home-services copy and a 60-currency
   speaking table.
5. **Message conversion was duplicated** across `views._openai_to_claude` and
   `openai_loop._claude_to_openai`.

## Old → new mapping

| Original | Now in the SDK | Notes |
|---|---|---|
| `receptionist.handle_conversation_turn` (Anthropic loop) | `agent.VoiceAgent.handle_turn` | One loop, both providers |
| `openai_loop.run_openai_loop` | *deleted* — folded into `VoiceAgent` | Provider diff is now 4 methods |
| `receptionist._client` / `_openai_client` | `providers.build_provider` + `AnthropicProvider`/`OpenAIProvider` | Key passed in, not read from settings |
| `receptionist.execute_tool` (if/elif + dedup) | `tools.ToolRegistry.dispatch` | Dedup is per-`Tool` policy |
| `tools.TOOLS` (schemas) | `tools.Tool` (schema **+** handler **+** policy) | Reuse the same schema dicts |
| `_tool_cache_*`, `_sms_already_sent`, `_end_*` | `state.CallState` over a `StateStore` | Backend pluggable |
| Django `cache` backend | `StateStore` protocol (`InMemoryStateStore` + your adapter) | 3-method interface |
| `prompts.get_receptionist_prompt` append logic | `prompts.PromptBuilder` | Content stays in your app |
| `prompts.CURRENCY_SPEAKING_GUIDES` | `currency.speaking_guide` | Pure data, reusable |
| `services/sms.py`, `services/email.py` | `integrations.TwilioSmsSender`, `SmtpEmailSender` (+ console stubs) | Same stub-on-missing-creds contract |
| `views._openai_to_claude`, `openai_loop._claude_to_openai`, `_tools_for_openai` | `conversation.*` | One home, unit-tested |
| `Business.resolved_*` (tenant→env) | host responsibility; SDK takes resolved values via `ProviderConfig` / `ToolContext.extra` | Keeps the SDK tenant-agnostic |

The Django models, the `_persist_turn` timeline writes, the Mary prompt copy,
and the `Business` credential resolution **stay in your app** — they're business
logic, not framework. `examples/django_receptionist.py` shows them wired back in.

## Key design decisions

- **The provider owns native message shape.** `VoiceAgent` never touches
  Anthropic vs OpenAI message dicts. The four abstract methods
  (`prepare_messages`, `format_tools`, `complete`, `record_assistant`,
  `record_tool_results`) are exactly the points where the two diverged. Adding a
  third backend (Bedrock, Gemini, vLLM) is one subclass + `register_provider`.
- **State is a 3-method protocol.** `get/set/delete` over any store. The agent
  builds a `CallState` view that turns those primitives into the three concerns
  it actually needs (tool dedup, one-shot side effects, end_call defer). No
  `call_id`? Every method degrades to a cache-miss and the agent still runs.
- **Dedup is declarative.** `Tool(dedup=True)` is name-keyed; `dedup_key=` makes
  it per-target (one SMS per recipient); `cache_predicate=` avoids caching
  failures so a failed send retries next turn. The original special-cased all of
  this inline.
- **Every voice workaround is a flag.** `defer_end_call_once`,
  `nudge_on_verbalized_intent`, `completion_tools`, `max_tool_iterations`. A text
  chat widget turns the voice-only ones off; a phone agent leaves them on.
- **Fail soft, always.** No provider → spoken stub. Tool raises → error
  `tool_result` the model can recover from. Bad timezone → naive clock. A live
  call must never 500.
- **Zero hard dependencies.** Core imports only the stdlib. `anthropic`,
  `openai`, `twilio` are optional extras, imported inside the methods that use
  them, so the package installs and tests without any of them.

## What was intentionally NOT moved

- Django models / ORM writes (`qualify_lead_tool` etc.) — business logic.
- The Mary system-prompt copy — business content; composed via `PromptBuilder`.
- `Business.resolved_*` credential resolution — tenancy concern.
- Vapi/Twilio webhook signature verification + the OpenAI-compatible HTTP shell
  in `views.py` — transport/framework concern. (A FastAPI port of that shell is
  a good next addition; the agent call inside it is unchanged.)

## Shipped in 0.2

Six of the original backlog items are now in the package, each behind a flag or
an opt-in import and each covered by tests that run with **zero** provider SDKs:

- **Async loop.** `BaseLLMProvider.acomplete` + `VoiceAgent.ahandle_turn` mirror
  the sync path; the built-in providers build an `AsyncAnthropic`/`AsyncOpenAI`
  client lazily. Sync-only providers raise a clear `NotImplementedError` rather
  than breaking. (`tests/test_async.py`)
- **Prompt caching.** `ProviderConfig.prompt_caching` (default on) marks the
  stable prefix — system prompt + the tools array — with Anthropic
  `cache_control`. No-op for OpenAI (server-side) . The placement is unit-tested
  via `AnthropicProvider._request_kwargs` without a network call.
- **Schema validation before dispatch.** `validation.validate_against_schema`
  (stdlib-only JSON-Schema subset) runs before the handler when
  `AgentConfig.validate_tool_input` is on; a mismatch becomes a recoverable
  `tool_result` ("party_size is required") instead of a handler `KeyError`.
- **Redis `StateStore`.** `state.RedisStateStore` (JSON values, key prefix, TTL
  via `ex=`); inject a client for tests, or pass `url=` with the `[redis]` extra.
- **Observability.** `metrics.TurnMetrics` (latency, llm round-trips, tool
  counts, token totals) handed to `AgentConfig.on_turn` once per turn. Callback
  exceptions are swallowed — telemetry never breaks a call.
- **Eval/test harness.** `voice_agent.testing` exposes an instance-based
  `ScriptedProvider` plus `make_scripted_agent` / `say` / `call_tool`, the seed
  for transcript-replay evals of prompt and tool changes.

## Remaining backlog

Ordered by leverage:

1. **Real provider streaming.** Today the HTTP layer fakes SSE by
   sentence-splitting a finished string (`views._stream`). Stream real deltas
   from `acomplete` for lower time-to-first-word.
2. **Structured tool I/O.** Tools return free-form dicts; a light
   TypedDict/dataclass result type per tool would document outputs and catch
   handler bugs at the boundary.
3. **Per-tool model routing.** Cheap model for `check_availability`-style turns,
   strong model for quoting — a `ProviderConfig` per tool tier.
4. **OpenTelemetry bridge.** `TurnMetrics` already carries the data; ship a tiny
   `on_turn` adapter that opens a span per turn for drop-in tracing.

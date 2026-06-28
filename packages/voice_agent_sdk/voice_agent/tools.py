"""Tool abstraction + registry.

In the original code, tool *schemas* lived in ``tools.py`` and tool *execution*
was a 30-line ``if/elif`` chain in ``execute_tool`` with dedup logic inlined per
tool. Here a Tool bundles its schema, handler, and dedup policy, and the
registry owns dispatch. Adding a tool to a future app is: define a handler,
wrap it in ``Tool(...)``, register it. No edits to the loop.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .errors import ToolExecutionError, ToolNotFound
from .state import CallState

ToolHandler = Callable[[dict, "ToolContext"], dict]
DedupKeyFn = Callable[[dict, "ToolContext"], str]
CachePredicate = Callable[[dict], bool]


@dataclass
class ToolContext:
    """Everything a handler needs that isn't in the tool input itself.

    `caller_phone` is the verified channel identity (e.g. Vapi caller ID) — pass
    it as the canonical contact so a hallucinated phone in `tool_input` can't
    overwrite the real one. `extra` carries host-specific objects (the resolved
    tenant/Business, a DB session, request metadata) opaquely.
    """

    call_id: str | None = None
    caller_phone: str | None = None
    state: CallState | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    handler: ToolHandler | None = None
    # When True, a repeat call within the same call_id returns the first cached
    # result instead of re-running the handler.
    dedup: bool = False
    # Compute the dedup bucket. Defaults to the tool name. Use this to dedup
    # per-target (e.g. one SMS per recipient): lambda inp, ctx: f"sms:{inp['to']}".
    dedup_key: DedupKeyFn | None = None
    # Only cache the result for dedup when this returns True. Lets you avoid
    # caching failures (so a failed send can be retried next turn).
    cache_predicate: CachePredicate | None = None
    # Terminal tools (end_call) don't produce data; they signal the loop to stop.
    terminal: bool = False

    def schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class ToolInvocation:
    name: str
    result: dict
    terminal: bool = False
    deduped: bool = False


def _ok(result: dict) -> bool:
    if not isinstance(result, dict):
        return False
    if "ok" in result:
        return bool(result["ok"])
    if "success" in result:
        return bool(result["success"])
    return "error" not in result


class ToolRegistry:
    def __init__(self, tools: list[Tool] | None = None) -> None:
        self._tools: dict[str, Tool] = {}
        for t in tools or []:
            self.register(t)

    def register(self, tool: Tool) -> Tool:
        self._tools[tool.name] = tool
        return tool

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def is_terminal(self, name: str) -> bool:
        tool = self._tools.get(name)
        return bool(tool and tool.terminal)

    def schemas(self) -> list[dict]:
        return [t.schema() for t in self._tools.values()]

    def name_keyed_dedup_tools(self) -> list[str]:
        """Dedupable tools whose key is just the tool name — the set we can
        report to the model as 'already done this call'."""
        return [t.name for t in self._tools.values() if t.dedup and t.dedup_key is None]

    def completed_this_call(self, state: CallState | None) -> list[str]:
        if state is None:
            return []
        return state.completed_keys(self.name_keyed_dedup_tools())

    def dispatch(self, name: str, tool_input: dict, ctx: ToolContext) -> ToolInvocation:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFound(name)

        if tool.terminal:
            result = tool.handler(tool_input, ctx) if tool.handler else {"ok": True}
            return ToolInvocation(name, result, terminal=True)

        dedup_bucket: str | None = None
        if tool.dedup and ctx.state is not None:
            dedup_bucket = tool.dedup_key(tool_input, ctx) if tool.dedup_key else name
            cached = ctx.state.cached_result(dedup_bucket)
            if cached is not None:
                return ToolInvocation(name, {**cached, "deduped": True}, deduped=True)

        if tool.handler is None:
            raise ToolExecutionError(f"Tool '{name}' has no handler")
        try:
            result = tool.handler(tool_input, ctx)
        except Exception as exc:  # surface as a structured error the model can recover from
            raise ToolExecutionError(str(exc)) from exc

        if dedup_bucket is not None:
            predicate = tool.cache_predicate or _ok
            if predicate(result):
                ctx.state.remember_result(dedup_bucket, result)
        return ToolInvocation(name, result)

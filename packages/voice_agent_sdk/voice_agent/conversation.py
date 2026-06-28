"""Message-format conversion between provider wire formats.

Vapi (and most telephony custom-LLM hooks) speak the OpenAI chat-completions
shape. Anthropic uses a different message shape. These helpers were previously
duplicated across ``views.py`` and ``openai_loop.py``; here they live once and
are unit-testable in isolation.

Canonical internal format == Anthropic format:
    {"role": "user"|"assistant", "content": str | list[block]}
where a block is one of {type:"text"}, {type:"tool_use"}, {type:"tool_result"}.
"""
from __future__ import annotations

from typing import Any

Message = dict[str, Any]
Messages = list[Message]


def openai_to_canonical(messages: Messages) -> Messages:
    """OpenAI chat messages -> canonical (Anthropic) messages.

    Drops `system` (handled separately), coerces roles, then merges consecutive
    same-role turns because Anthropic requires strictly alternating roles. If
    the first surviving message isn't from the user, prepend a synthetic
    greeting so the conversation is well-formed.
    """
    out: Messages = []
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "") or ""
        if role == "system":
            continue
        if role == "assistant":
            out.append({"role": "assistant", "content": content})
        elif role in ("user", "human"):
            out.append({"role": "user", "content": content})

    merged: Messages = []
    for m in out:
        if merged and merged[-1]["role"] == m["role"]:
            merged[-1]["content"] = f"{merged[-1]['content']}\n{m['content']}"
        else:
            merged.append(dict(m))
    if merged and merged[0]["role"] != "user":
        merged.insert(0, {"role": "user", "content": "Hello"})
    return merged


def canonical_to_openai(messages: Messages) -> Messages:
    """Canonical (Anthropic) messages -> OpenAI chat messages.

    Expands tool_use blocks into assistant `tool_calls` and tool_result blocks
    into `role: "tool"` messages.
    """
    import json

    out: Messages = []
    for m in messages:
        role = m.get("role")
        content = m.get("content")
        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue
        if not isinstance(content, list):
            continue
        if role == "assistant":
            text_parts: list[str] = []
            tool_calls: list[dict] = []
            for block in content:
                btype = block.get("type")
                if btype == "text":
                    text_parts.append(block.get("text", ""))
                elif btype == "tool_use":
                    tool_calls.append({
                        "id": block.get("id"),
                        "type": "function",
                        "function": {
                            "name": block.get("name"),
                            "arguments": json.dumps(block.get("input") or {}),
                        },
                    })
            msg: dict[str, Any] = {"role": "assistant"}
            msg["content"] = "\n".join(text_parts) if text_parts else None
            if tool_calls:
                msg["tool_calls"] = tool_calls
            out.append(msg)
        elif role == "user":
            for block in content:
                if block.get("type") == "tool_result":
                    raw = block.get("content")
                    out.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id"),
                        "content": raw if isinstance(raw, str) else json.dumps(raw, default=str),
                    })
                elif block.get("type") == "text":
                    out.append({"role": "user", "content": block.get("text", "")})
    return out


def tools_to_openai(tools: list[dict]) -> list[dict]:
    """Anthropic-format tool schemas -> OpenAI function-tool schemas."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
            },
        }
        for t in tools
    ]

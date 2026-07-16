"""OpenAI tool-calling loop — mirrors the Anthropic loop in receptionist.py.

The OpenAI Chat Completions API returns tool calls in `message.tool_calls`
with a different shape from Anthropic's `tool_use` blocks. We translate the
shared TOOLS schema (Anthropic format) into OpenAI's function-tool format on
the fly so the dispatch layer stays provider-agnostic.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# gpt-4o-mini has dramatically lower time-to-first-token than gpt-4o, which is
# what voice callers feel as latency. Override with OPENAI_MODEL if you need a
# bigger model for a specific business.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# "Let me check that for you" with no tool call = the caller sits in dead air
# until they speak again (observed live: two stalled turns in a row before
# check_availability ever fired). When a text-only turn verbalizes intent like
# this, we retry ONCE with an explicit instruction to actually call the tool.
_INTENT_PHRASES = (
    "let me check", "let me see what", "let me look", "let me pull",
    "let me get that", "let me book", "let me draft", "let me put",
    "i'll check", "i'll book", "i'll draft", "i'll get that",
    "one moment", "just a moment", "give me a moment", "give me a second",
    "bear with me", "hold on", "checking availability", "checking the calendar",
    "right away", "checking that now",
)

_NUDGE_MESSAGE = (
    "[system: you told the caller you'd do it or that it's already done, but the "
    "matching tool has NOT been called this call. Call the actual tool NOW in this "
    "response — do not reply with more talk. If a required field is missing, ask "
    "for it instead.]"
)

# "You're all set for tomorrow at 1 PM" with no book_appointment call = the
# caller believes they're booked while the dashboard shows nothing (observed
# live). Only nudged when book_appointment hasn't already run this call.
_COMPLETION_PHRASES = (
    "you're booked", "you are booked", "you're all set", "you are all set",
    "you're set for", "you are set for", "i've booked", "i have booked",
    "i've scheduled", "i have scheduled", "we've got you down",
    "you'll get a confirmation", "you will get a confirmation",
    "you'll receive a confirmation", "confirmation by text",
)


def _verbalized_intent(text: str) -> bool:
    t = (text or "").lower()
    return any(p in t for p in _INTENT_PHRASES)


def _claimed_completion(text: str) -> bool:
    t = (text or "").lower()
    return any(p in t for p in _COMPLETION_PHRASES)


# Spoken immediately when a tool round starts, so the caller hears progress
# instead of silence during the tool + follow-up-LLM latency (1.5–4s). Only
# the tools slow/notable enough to warrant it.
_TOOL_FILLERS = {
    "check_availability": "Let me pull up the calendar real quick.",
    "book_appointment": "One second while I get that booked for you.",
    "draft_quote": "Give me just a moment to put those numbers together.",
}


def _tools_for_openai(tools: list[dict]) -> list[dict]:
    out = []
    for t in tools:
        out.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
            },
        })
    return out


def _claude_to_openai(messages: list[dict]) -> list[dict]:
    """Convert Claude-style turns to OpenAI chat.completions format.

    Claude messages look like {role, content: str | list[blocks]} where blocks
    can be text / tool_use / tool_result. OpenAI wants:
      - assistant text         → {role: "assistant", content: "..."}
      - assistant tool_use     → {role: "assistant", tool_calls: [...]}
      - tool_result            → {role: "tool", tool_call_id, content}
    """
    out: list[dict] = []
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
            if text_parts:
                msg["content"] = "\n".join(text_parts)
            else:
                msg["content"] = None
            if tool_calls:
                msg["tool_calls"] = tool_calls
            out.append(msg)
        elif role == "user":
            for block in content:
                if block.get("type") == "tool_result":
                    out.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id"),
                        "content": block.get("content") if isinstance(block.get("content"), str)
                        else json.dumps(block.get("content"), default=str),
                    })
                elif block.get("type") == "text":
                    out.append({"role": "user", "content": block.get("text", "")})
    return out


def _needs_nudge(text: str, done_tools: frozenset) -> bool:
    """A text-only turn that promises or claims tool work that never ran.

    Completion claims ("you're all set") are only nudged when book_appointment
    hasn't fired this call — after a real booking, closing lines like
    "You're all set!" are legitimate speech, not a stall.
    """
    if _verbalized_intent(text):
        return True
    return _claimed_completion(text) and "book_appointment" not in done_tools


def run_openai_loop(
    client,
    *,
    system_prompt: str,
    tools: list[dict],
    conversation_history: list[dict],
    execute_tool,
    done_tools: frozenset = frozenset(),
) -> dict[str, Any]:
    """Run the OpenAI agentic loop. Mirrors handle_conversation_turn in receptionist.py."""
    oa_tools = _tools_for_openai(tools)
    oa_messages = [{"role": "system", "content": system_prompt}, *_claude_to_openai(conversation_history)]

    should_end = False
    last_tool: str | None = None
    nudged = False

    while True:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=400,
            temperature=0.5,
            tools=oa_tools,
            messages=oa_messages,
        )
        choice = resp.choices[0]
        msg = choice.message
        if not msg.tool_calls:
            text = (msg.content or "").strip()
            if not nudged and last_tool is None and _needs_nudge(text, done_tools):
                nudged = True
                logger.info("[NUDGE] verbalized intent without tool_call — retrying with explicit instruction")
                oa_messages.append({"role": "assistant", "content": text})
                oa_messages.append({"role": "user", "content": _NUDGE_MESSAGE})
                continue
            return {"text": text, "end_call": should_end}

        # Append the assistant's tool-call message so the model has context for the result.
        oa_messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        })

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                tool_input = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                logger.warning("[TOOL JSON ERROR] %s args=%r", name, tc.function.arguments)
                tool_input = {}

            if name == "end_call":
                logger.info("[END_CALL] reason=%s", tool_input.get("reason", "unknown"))
                should_end = True
                oa_messages.append({"role": "tool", "tool_call_id": tc.id, "content": "{}"})
                continue

            last_tool = name
            logger.info("[TOOL] %s %s", name, json.dumps(tool_input))
            try:
                result = execute_tool(name, tool_input)
            except Exception as exc:  # noqa: BLE001
                logger.error("[TOOL ERROR] %s: %s", name, exc)
                result = {"error": str(exc)}
            logger.info("[RESULT] %s", json.dumps(result, default=str))
            oa_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, default=str),
            })

        if should_end:
            # Surface a closing line.
            if last_tool in ("book_appointment", "send_sms"):
                return {"text": "You're all set! Anything else I can help with?", "end_call": True}
            return {"text": "", "end_call": True}


def run_openai_loop_streaming(
    client,
    *,
    system_prompt: str,
    tools: list[dict],
    conversation_history: list[dict],
    execute_tool,
    out: dict[str, Any],
    done_tools: frozenset = frozenset(),
):
    """Streaming twin of run_openai_loop. A generator that yields assistant text
    deltas (str) as the model produces them, so Vapi can start speaking within a
    few hundred ms instead of after the full turn.

    Tool turns are resolved silently (no yield). When the model returns plain
    text it streams live. After the generator is exhausted, `out` holds
    {"text": <full spoken text>, "should_end": <bool>} for the caller to persist
    and apply the hangup-deferral.
    """
    oa_tools = _tools_for_openai(tools)
    oa_messages = [{"role": "system", "content": system_prompt}, *_claude_to_openai(conversation_history)]

    should_end = False
    last_tool: str | None = None
    spoken: list[str] = []
    nudged = False
    filler_sent = False
    ran_tool = False

    while True:
        stream = client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=400,
            temperature=0.5,
            tools=oa_tools,
            messages=oa_messages,
            stream=True,
        )

        tool_acc: dict[int, dict] = {}
        assistant_text: list[str] = []
        turn_spoken: list[str] = []
        for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            tcs = getattr(delta, "tool_calls", None)
            if tcs:
                for tcd in tcs:
                    acc = tool_acc.setdefault(tcd.index, {"id": None, "name": "", "arguments": ""})
                    if tcd.id:
                        acc["id"] = tcd.id
                    fn = getattr(tcd, "function", None)
                    if fn:
                        if fn.name:
                            acc["name"] += fn.name
                        if fn.arguments:
                            acc["arguments"] += fn.arguments
            content = getattr(delta, "content", None)
            if content:
                # The model commits to tool_calls XOR content early in the stream.
                # If no tool call has appeared, this is a plain text turn → stream
                # it live. Otherwise buffer it onto the assistant tool-call message.
                if not tool_acc:
                    spoken.append(content)
                    turn_spoken.append(content)
                    yield content
                else:
                    assistant_text.append(content)

        if not tool_acc:
            # "Let me check…" with no tool call would strand the caller in dead
            # air until they speak again. Nudge once; the filler text was already
            # streamed, so the retried turn's tool result follows it naturally.
            text_this_turn = "".join(turn_spoken)
            if not nudged and not ran_tool and _needs_nudge(text_this_turn, done_tools):
                nudged = True
                logger.info("[NUDGE·stream] verbalized intent without tool_call — retrying")
                oa_messages.append({"role": "assistant", "content": text_this_turn})
                oa_messages.append({"role": "user", "content": _NUDGE_MESSAGE})
                continue
            break  # plain text turn complete

        oa_messages.append({
            "role": "assistant",
            "content": "".join(assistant_text) or None,
            "tool_calls": [
                {"id": a["id"], "type": "function",
                 "function": {"name": a["name"], "arguments": a["arguments"]}}
                for a in tool_acc.values()
            ],
        })

        # Tool turns rarely carry spoken text, so without this the caller hears
        # pure silence for the tool + follow-up-model latency. Speak one short
        # progress line the moment we know which tool is running. (Skip after a
        # nudge — the caller already heard the model's own "one moment" line.)
        if not filler_sent and not nudged:
            for a in tool_acc.values():
                filler = _TOOL_FILLERS.get(a["name"])
                if filler:
                    filler_sent = True
                    prefix = " " if spoken else ""
                    spoken.append(prefix + filler)
                    yield prefix + filler
                    break

        for a in tool_acc.values():
            name = a["name"]
            try:
                tool_input = json.loads(a["arguments"] or "{}")
            except json.JSONDecodeError:
                logger.warning("[TOOL JSON ERROR] %s args=%r", name, a["arguments"])
                tool_input = {}

            if name == "end_call":
                logger.info("[END_CALL] reason=%s", tool_input.get("reason", "unknown"))
                should_end = True
                oa_messages.append({"role": "tool", "tool_call_id": a["id"], "content": "{}"})
                continue

            last_tool = name
            ran_tool = True
            logger.info("[TOOL] %s %s", name, json.dumps(tool_input))
            try:
                result = execute_tool(name, tool_input)
            except Exception as exc:  # noqa: BLE001
                logger.error("[TOOL ERROR] %s: %s", name, exc)
                result = {"error": str(exc)}
            logger.info("[RESULT] %s", json.dumps(result, default=str))
            oa_messages.append({
                "role": "tool",
                "tool_call_id": a["id"],
                "content": json.dumps(result, default=str),
            })

        if should_end:
            # Always speak a graceful closing so the streamed turn never goes
            # silent, then defer the hard hangup (the caller marks it deferred and
            # the next turn fires it via the blocking path with the header set).
            closing = ("You're all set! Anything else I can help with?"
                       if last_tool in ("book_appointment", "send_sms")
                       else "Thanks for calling — have a great day!")
            spoken.append(closing)
            yield closing
            break
        # otherwise loop: the next streaming call produces the post-tool reply

    out["should_end"] = should_end
    out["text"] = "".join(spoken)

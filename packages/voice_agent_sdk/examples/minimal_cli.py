"""Smallest possible standalone agent — no Django, no telephony.

    pip install -e packages/voice_agent_sdk[anthropic]
    export ANTHROPIC_API_KEY=sk-ant-...
    python packages/voice_agent_sdk/examples/minimal_cli.py

Type messages; the agent can call a `book_table` tool and `end_call`. Without a
key it runs in stub mode so you can still see the wiring.
"""
from __future__ import annotations

import os

from voice_agent import (
    AgentConfig,
    PromptBuilder,
    ProviderConfig,
    Tool,
    ToolContext,
    ToolRegistry,
    VoiceAgent,
    current_datetime_section,
)

PROMPT = PromptBuilder(
    "You are Sam, the host at a small restaurant. Answer questions warmly and "
    "book tables. Keep replies to one or two sentences."
).section("CURRENT CONTEXT:", current_datetime_section("America/New_York")).build()


def book_table(inp: dict, ctx: ToolContext) -> dict:
    return {
        "success": True,
        "confirmation": f"Table for {inp.get('party_size')} on {inp.get('date')} at {inp.get('time')}",
    }


registry = ToolRegistry([
    Tool(
        name="book_table",
        description="Book a table once the guest gives party size, date, and time.",
        input_schema={
            "type": "object",
            "properties": {
                "party_size": {"type": "integer"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "time": {"type": "string", "description": "HH:MM"},
            },
            "required": ["party_size", "date", "time"],
        },
        handler=book_table,
        dedup=True,
    ),
    Tool(
        name="end_call",
        description="Hang up after saying goodbye.",
        input_schema={"type": "object", "properties": {"reason": {"type": "string"}}},
        terminal=True,
    ),
])


def main() -> None:
    agent = VoiceAgent.create(
        provider_config=ProviderConfig(
            provider=os.environ.get("VOICE_AGENT_PROVIDER", "anthropic"),
            api_key=os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY", ""),
        ),
        registry=registry,
        config=AgentConfig(persona_name="Sam", completion_tools=("book_table",)),
    )

    history: list[dict] = []
    print("Sam is ready. Type 'quit' to exit.\n")
    while True:
        try:
            user = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user.lower() in {"quit", "exit"}:
            break
        history.append({"role": "user", "content": user})
        result = agent.handle_turn(history, system_prompt=PROMPT, call_id="cli-demo")
        print(f"sam> {result.text}\n")
        history.append({"role": "assistant", "content": result.text})
        if result.end_call:
            print("[call ended]")
            break


if __name__ == "__main__":
    main()

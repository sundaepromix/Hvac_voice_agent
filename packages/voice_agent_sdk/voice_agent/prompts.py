"""Prompt composition.

The production prompt is a fixed base + several *conditional* sections appended
at runtime (caller info, tools-already-done, knowledge base, current date).
`PromptBuilder` turns that ad-hoc string concatenation into a small, ordered,
skip-empty builder so the assembly is readable and reusable.

The home-services receptionist *content* is intentionally NOT here — it's
business copy, not framework. See ``examples/`` for the full Mary template
composed with this builder.
"""
from __future__ import annotations

from datetime import datetime


class PromptBuilder:
    def __init__(self, base: str) -> None:
        self._base = base.rstrip()
        self._sections: list[tuple[str | None, str]] = []

    def section(self, title: str | None, body: str | None) -> "PromptBuilder":
        """Append a titled block. No-op when body is empty/whitespace, so callers
        can chain unconditionally without `if body:` guards everywhere."""
        if body and body.strip():
            self._sections.append((title, body.strip()))
        return self

    def build(self) -> str:
        parts = [self._base]
        for title, body in self._sections:
            parts.append(f"\n\n{title}\n{body}" if title else f"\n\n{body}")
        return "".join(parts)

    def __str__(self) -> str:
        return self.build()


def current_datetime_section(timezone: str = "UTC") -> str:
    """A 'CURRENT CONTEXT' body so the model can resolve 'tomorrow' / 'Saturday'.
    Falls back to naive local time if the tz name is unknown."""
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo(timezone))
    except Exception:  # noqa: BLE001 — bad tz string shouldn't break a call
        now = datetime.now()
    return (
        f"- Today is {now.strftime('%A, %B %d, %Y')}. "
        f"The current time is {now.strftime('%I:%M %p')}.\n"
        "- Use this to resolve relative dates like 'tomorrow', 'next Monday'."
    )

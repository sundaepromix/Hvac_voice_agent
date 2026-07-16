"""Regression tests for the OpenAI streaming loop's voice-UX behaviours.

Observed live (call 019f6955, 2026-07-16): the model said "Let me check
availability for you. One moment, please." WITHOUT calling the tool, twice in
a row, stranding the caller in ~30s of dead air each time. These tests pin the
two defenses: the verbalized-intent nudge and the spoken tool-turn filler.
"""
from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.calls.agent.openai_loop import run_openai_loop_streaming


def _text_chunk(text):
    delta = SimpleNamespace(content=text, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


def _tool_chunk(index, call_id, name, arguments):
    fn = SimpleNamespace(name=name, arguments=arguments)
    tc = SimpleNamespace(index=index, id=call_id, function=fn)
    delta = SimpleNamespace(content=None, tool_calls=[tc])
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


class FakeStreamingClient:
    """Returns one scripted stream (a list of chunks) per API call."""

    def __init__(self, streams):
        self._streams = list(streams)
        self.calls = 0
        completions = SimpleNamespace(create=self._create)
        self.chat = SimpleNamespace(completions=completions)

    def _create(self, **kwargs):
        self.calls += 1
        return iter(self._streams.pop(0))


TOOLS = [{"name": "check_availability", "description": "check", "input_schema": {"type": "object", "properties": {}}}]


class StreamingNudgeTests(SimpleTestCase):
    def _run(self, client, execute_tool=None):
        out = {}
        tokens = list(run_openai_loop_streaming(
            client,
            system_prompt="test",
            tools=TOOLS,
            conversation_history=[{"role": "user", "content": "any times tomorrow?"}],
            execute_tool=execute_tool or (lambda n, i: {"available": ["08:00"]}),
            out=out,
        ))
        return tokens, out

    def test_verbalized_intent_without_tool_is_nudged_into_the_tool_call(self):
        client = FakeStreamingClient([
            # Turn 1: stalls — intent verbalized, no tool call.
            [_text_chunk("Let me check availability for you. One moment, please.")],
            # Turn 2 (after nudge): the actual tool call.
            [_tool_chunk(0, "call_1", "check_availability", '{"date": "2026-07-17"}')],
            # Turn 3: speaks the result.
            [_text_chunk("We have eight A M open. Does that work?")],
        ])
        fired = []
        tokens, out = self._run(client, lambda n, i: fired.append(n) or {"available": ["08:00"]})

        self.assertEqual(fired, ["check_availability"], "nudge must force the real tool call")
        self.assertEqual(client.calls, 3)
        text = "".join(tokens)
        self.assertIn("One moment", text)
        self.assertIn("eight A M", text)
        self.assertEqual(out["text"], text)

    def test_nudge_fires_at_most_once(self):
        client = FakeStreamingClient([
            [_text_chunk("Let me check that for you. One moment.")],
            # Model stalls AGAIN after the nudge — loop must exit, not spin.
            [_text_chunk("Just a moment while I check.")],
        ])
        tokens, out = self._run(client)
        self.assertEqual(client.calls, 2)
        self.assertFalse(out.get("should_end"))

    def test_plain_answer_is_not_nudged(self):
        client = FakeStreamingClient([
            [_text_chunk("We're open weekdays eight to six.")],
        ])
        tokens, out = self._run(client)
        self.assertEqual(client.calls, 1)
        self.assertEqual("".join(tokens), "We're open weekdays eight to six.")

    def test_tool_turn_speaks_a_filler_while_the_tool_runs(self):
        client = FakeStreamingClient([
            [_tool_chunk(0, "call_1", "check_availability", '{"date": "2026-07-17"}')],
            [_text_chunk("Eight A M is open.")],
        ])
        order = []
        original_tokens, out = self._run(
            client, lambda n, i: order.append("tool") or {"available": ["08:00"]})
        text = "".join(original_tokens)
        self.assertIn("Let me pull up the calendar", text,
                      "caller must hear progress instead of silence during the tool round")
        self.assertIn("Eight A M is open.", text)
        self.assertLess(text.index("calendar"), text.index("Eight"),
                        "filler must be spoken before the result")

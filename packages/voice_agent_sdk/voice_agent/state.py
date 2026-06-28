"""Per-call conversation state — the piece that makes a *stateless* webhook
agent behave like a stateful one.

Background: Vapi re-runs the agent loop on every turn but does NOT replay tool
history. So the model has no memory that it already booked / already texted,
and will happily re-fire tools. Workflow Auth solved this with a pile of
Django-cache helpers scattered through ``receptionist.py``. Here that logic is
consolidated behind a tiny pluggable `StateStore` so you can back it with an
in-memory dict (single process), Django's cache (multi-worker), or Redis
(multi-host) without touching the agent.
"""
from __future__ import annotations

import json
import time
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StateStore(Protocol):
    """Minimal key/value contract. Implement these three methods over any
    backend (dict, Django cache, Redis, Memcached)."""

    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, ttl: int) -> None: ...
    def delete(self, key: str) -> None: ...


class InMemoryStateStore:
    """Process-local store with TTL. Fine for tests, single-worker dev, and
    CLIs. NOT shared across processes — use the Django/Redis adapter in prod.
    """

    def __init__(self) -> None:
        self._data: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._data.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at and time.time() > expires_at:
            self._data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._data[key] = (time.time() + ttl if ttl else 0.0, value)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)


class RedisStateStore:
    """Shared, multi-host StateStore backed by Redis.

    Use this when you scale the agent across more than one machine (the
    ``InMemoryStateStore`` is per-process; a Django cache is per-host). Values
    are JSON-encoded, so anything CallState stores (dicts, bools) round-trips.

    Pass an existing client, or a ``url`` to connect with (requires the optional
    ``redis`` extra: ``pip install voice-agent-sdk[redis]``). Injecting a client
    keeps this unit-testable without a live server.
    """

    def __init__(self, client: Any = None, *, url: str | None = None,
                 key_prefix: str = "va:") -> None:
        if client is None:
            try:
                import redis  # noqa: WPS433 — optional dependency, imported on use
            except ImportError as exc:  # pragma: no cover - import guard
                raise RuntimeError(
                    "RedisStateStore needs the 'redis' package: pip install voice-agent-sdk[redis]"
                ) from exc
            client = redis.Redis.from_url(url or "redis://localhost:6379/0")
        self._r = client
        self._prefix = key_prefix

    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get(self, key: str) -> Any | None:
        raw = self._r.get(self._k(key))
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return None

    def set(self, key: str, value: Any, ttl: int) -> None:
        raw = json.dumps(value, default=str)
        if ttl:
            self._r.set(self._k(key), raw, ex=ttl)
        else:
            self._r.set(self._k(key), raw)

    def delete(self, key: str) -> None:
        self._r.delete(self._k(key))


class CallState:
    """High-level per-call helpers built on a StateStore, keyed by call_id.

    Centralises the three dedup/UX concerns the production agent needs:
      * tool-result dedup (don't re-run qualify_lead/book/quote within a call)
      * one-shot side effects (one confirmation SMS per recipient per call)
      * "defer the hangup once so the TTS can finish" bookkeeping

    With no call_id (test harness, manual invocation) every method degrades to a
    no-op / cache-miss, so the agent still runs — it just won't dedup.
    """

    def __init__(self, store: StateStore, call_id: str | None, ttl: int = 3600) -> None:
        self.store = store
        self.call_id = (call_id or "").strip() or None
        self.ttl = ttl

    # ---- generic ----------------------------------------------------------
    def _k(self, *parts: str) -> str | None:
        if not self.call_id:
            return None
        return ":".join(("call", self.call_id, *parts))

    # ---- tool-result dedup ------------------------------------------------
    def cached_result(self, dedup_key: str) -> dict | None:
        k = self._k("tool", dedup_key)
        return self.store.get(k) if k else None

    def remember_result(self, dedup_key: str, result: dict) -> None:
        k = self._k("tool", dedup_key)
        if k:
            self.store.set(k, result, self.ttl)

    def completed_keys(self, candidates: list[str]) -> list[str]:
        """Which of `candidates` already have a cached result this call —
        used to nudge the model not to re-fire them."""
        done = []
        for key in candidates:
            k = self._k("tool", key)
            if k and self.store.get(k) is not None:
                done.append(key)
        return done

    # ---- one-shot side effects (keyed, e.g. per SMS recipient) ------------
    def side_effect_done(self, name: str, target: str) -> dict | None:
        k = self._k("once", name, target)
        return self.store.get(k) if k else None

    def mark_side_effect(self, name: str, target: str, result: dict) -> None:
        k = self._k("once", name, target)
        if k:
            self.store.set(k, result, self.ttl)

    # ---- end_call deferral ------------------------------------------------
    def end_call_deferred(self) -> bool:
        k = self._k("end_deferred")
        return bool(self.store.get(k)) if k else False

    def mark_end_call_deferred(self) -> None:
        k = self._k("end_deferred")
        if k:
            self.store.set(k, True, self.ttl)

    def forget(self) -> None:
        """Best-effort cleanup hook for an end-of-call event."""
        if not self.call_id:
            return
        for suffix in ("end_deferred",):
            k = self._k(suffix)
            if k:
                self.store.delete(k)

"""StateStore behaviour: in-memory TTL + the Redis adapter (with a fake client)."""
from __future__ import annotations

import time

from voice_agent import CallState, InMemoryStateStore, RedisStateStore


def test_inmemory_ttl_expiry():
    store = InMemoryStateStore()
    store.set("k", {"v": 1}, ttl=1)
    assert store.get("k") == {"v": 1}
    store._data["k"] = (time.time() - 1, {"v": 1})  # force-expire
    assert store.get("k") is None


class FakeRedis:
    """Minimal stand-in for redis.Redis covering what RedisStateStore uses."""

    def __init__(self):
        self.kv: dict[str, str] = {}
        self.last_ex: int | None = None

    def get(self, key):
        return self.kv.get(key)

    def set(self, key, value, ex=None):
        self.kv[key] = value
        self.last_ex = ex

    def delete(self, key):
        self.kv.pop(key, None)


def test_redis_store_roundtrips_json_with_prefix_and_ttl():
    fake = FakeRedis()
    store = RedisStateStore(client=fake, key_prefix="t:")
    store.set("foo", {"a": 1, "b": [1, 2]}, ttl=900)
    assert "t:foo" in fake.kv               # prefixed
    assert fake.last_ex == 900              # ttl forwarded as ex=
    assert store.get("foo") == {"a": 1, "b": [1, 2]}
    assert store.get("missing") is None
    store.delete("foo")
    assert store.get("foo") is None


def test_redis_store_drives_callstate_dedup():
    store = RedisStateStore(client=FakeRedis())
    cs = CallState(store, call_id="call-1", ttl=60)
    assert cs.cached_result("qualify_lead") is None
    cs.remember_result("qualify_lead", {"lead_id": 7})
    assert cs.cached_result("qualify_lead") == {"lead_id": 7}
    assert cs.completed_keys(["qualify_lead", "book"]) == ["qualify_lead"]

"""Tiny, dependency-free validator for tool input against a JSON-Schema subset.

Why this exists: the model occasionally calls a tool with a missing required
field or a wrong type ("party_size": "four"). Without a guard that lands in the
handler as a ``KeyError``/``TypeError`` — which the loop turns into an opaque
error. Validating first lets us hand the model a *specific*, recoverable message
("party_size is required", "time must be a string") so it can correct itself on
the next step instead of the call degrading.

This is intentionally NOT a full JSON-Schema implementation (no ``$ref``,
``allOf``, ``patternProperties``, formats, …). It covers the shapes tool schemas
actually use: ``object`` with ``properties``/``required``, scalar ``type``,
``enum``, nested objects, and ``array`` with ``items``. Anything it doesn't
understand it skips rather than false-rejects — a validator that blocks valid
calls is worse than one that misses an edge case on a live call.
"""
from __future__ import annotations

from typing import Any

# JSON-Schema type name -> Python types. bool is excluded from the numeric types
# on purpose: in Python ``True`` is an ``int``, but a model that says
# ``"count": true`` is wrong and we want to catch it.
_TYPE_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
    "null": lambda v: v is None,
}


def validate_against_schema(data: Any, schema: dict | None, _path: str = "") -> list[str]:
    """Return a list of human-readable validation errors; empty means valid.

    Errors are phrased for the *model* to read and act on, not for a developer.
    """
    if not schema or not isinstance(schema, dict):
        return []

    errors: list[str] = []
    expected = schema.get("type")

    if expected and expected in _TYPE_CHECKS and not _TYPE_CHECKS[expected](data):
        where = _path or "input"
        return [f"{where} must be a {expected}"]

    if "enum" in schema and data not in schema["enum"]:
        where = _path or "value"
        allowed = ", ".join(repr(x) for x in schema["enum"])
        errors.append(f"{where} must be one of: {allowed}")

    if expected == "object" or (expected is None and isinstance(data, dict)):
        if isinstance(data, dict):
            for key in schema.get("required", []):
                if key not in data or data[key] is None:
                    errors.append(f"{_join(_path, key)} is required")
            props = schema.get("properties", {})
            for key, sub in props.items():
                if key in data and data[key] is not None:
                    errors.extend(validate_against_schema(data[key], sub, _join(_path, key)))

    if expected == "array" and isinstance(data, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, item in enumerate(data):
                errors.extend(validate_against_schema(item, item_schema, f"{_path or 'item'}[{i}]"))

    return errors


def _join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key

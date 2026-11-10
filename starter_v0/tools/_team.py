"""Helpers shared by the team tools (profile, profile_save, weather, now).

Result envelope for team tools:
- success: {"tool": <registry name>, "ok": True, ...}
- failure: {"tool": <registry name>, "ok": False, "error": <kind>, "message": <text>}
`error` is "invalid_input" when the model sent bad arguments (fix the args, do not retry as-is),
or the exception class name when the tool itself failed (network, file, ...).
"""
from __future__ import annotations

from typing import Any

from tools._shared import err


def invalid_input(tool: str, message: str) -> dict[str, Any]:
    return {"tool": tool, "ok": False, "error": "invalid_input", "message": message}


def failure(tool: str, exc: Exception) -> dict[str, Any]:
    return {**err(tool, exc), "ok": False}


def as_int(value: Any, *, default: int, low: int, high: int) -> int:
    """Coerce what models send (5, "5", 5.0, None, "abc") into an int within [low, high]."""
    if isinstance(value, bool):
        return default
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(low, min(number, high))


def is_true(value: Any) -> bool:
    """Strict yes: only True or the string "true". The string "false" must not count as confirmed."""
    if isinstance(value, bool):
        return value
    return isinstance(value, str) and value.strip().lower() == "true"

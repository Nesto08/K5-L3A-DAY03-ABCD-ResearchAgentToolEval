from __future__ import annotations

import re
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tools._profile_store import FIELDS, LIST_FIELDS, SCALAR_FIELDS, load_profile, save_profile
from tools._team import failure, invalid_input, is_true

TOOL = "profile_save"
ACTIONS = ("set", "add", "remove")
MAX_VALUE_CHARS = 80
MAX_LIST_ITEMS = 20
HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{1,15}$")


def _values(field: str, value: Any) -> list[str]:
    """Normalize the raw value into a list of clean strings."""
    if value is None:
        raw: list[Any] = []
    elif isinstance(value, list):
        raw = value
    elif field in LIST_FIELDS:
        raw = str(value).split(",")
    else:
        raw = [value]
    cleaned = [str(item).strip() for item in raw if str(item).strip()]
    if field == "followed_accounts":
        cleaned = [item.lstrip("@") for item in cleaned]
    return cleaned


def _validate(field: str, values: list[str]) -> str | None:
    for item in values:
        if "\n" in item or len(item) > MAX_VALUE_CHARS:
            return f"Each value must be one line of at most {MAX_VALUE_CHARS} characters"
    if field in SCALAR_FIELDS and len(values) > 1:
        return f"{field} takes a single value"
    if field == "timezone" and values:
        try:
            ZoneInfo(values[0])
        except (ZoneInfoNotFoundError, ValueError):
            return f"Unknown timezone '{values[0]}'. Use an IANA name such as Asia/Ho_Chi_Minh"
    if field == "followed_accounts":
        bad = [item for item in values if not HANDLE_RE.match(item)]
        if bad:
            return f"Invalid X handle(s) {bad}: letters, digits or _ only, at most 15 characters, no @"
    return None


def _apply(current: Any, field: str, action: str, values: list[str]) -> Any:
    if field in SCALAR_FIELDS:
        return values[0] if values else ""
    if action == "set":
        new = values
    elif action == "add":
        new = list(current) + values
    else:
        drop = {item.casefold() for item in values}
        new = [item for item in current if item.casefold() not in drop]
    deduped: list[str] = []
    for item in new:
        if item.casefold() not in {kept.casefold() for kept in deduped}:
            deduped.append(item)
    return deduped


def save_user_profile(field: str = "", value: Any = "", action: str = "set", confirmed: Any = False) -> dict[str, Any]:
    field = (field or "").strip()
    action = (action or "set").strip().lower()
    if field not in FIELDS:
        return invalid_input(TOOL, f"Unknown field '{field}'. Allowed: {list(FIELDS)}")
    if action not in ACTIONS:
        return invalid_input(TOOL, f"Unknown action '{action}'. Allowed: {list(ACTIONS)}")
    if field in SCALAR_FIELDS and action != "set":
        return invalid_input(TOOL, f"{field} only supports action=set")

    values = _values(field, value)
    if action in ("add", "remove") and not values:
        return invalid_input(TOOL, f"action={action} needs at least one value")
    problem = _validate(field, values)
    if problem:
        return invalid_input(TOOL, problem)

    try:
        profile, _ = load_profile()
        new_value = _apply(profile[field], field, action, values)
        if field in LIST_FIELDS and len(new_value) > MAX_LIST_ITEMS:
            return invalid_input(TOOL, f"{field} can hold at most {MAX_LIST_ITEMS} items")

        if not is_true(confirmed):
            return {
                "tool": TOOL,
                "ok": True,
                "status": "needs_confirmation",
                "field": field,
                "action": action,
                "pending_value": new_value,
                "message": "Nothing saved. Ask the user to confirm (yes_no), then call again with confirmed=true.",
            }

        profile[field] = new_value
        save_profile(profile)
        return {"tool": TOOL, "ok": True, "status": "saved", "field": field, "action": action, "value": new_value}
    except Exception as exc:
        return failure(TOOL, exc)

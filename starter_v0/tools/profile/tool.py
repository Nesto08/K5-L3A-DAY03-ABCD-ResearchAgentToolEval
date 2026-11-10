from __future__ import annotations

from typing import Any

from tools._profile_store import FIELDS, load_profile
from tools._team import failure, invalid_input

TOOL = "profile"
PRIVACY_NOTE = (
    "Profile data is personal. Use city, interests and followed_accounts as tool arguments; "
    "never send name to web, social or URL tools."
)


def get_user_profile(fields: list[str] | str | None = None) -> dict[str, Any]:
    if isinstance(fields, str):
        fields = [fields] if fields.strip() else []
    if fields is not None and not isinstance(fields, list):
        return invalid_input(TOOL, "fields must be a list of field names")
    wanted = [str(field).strip() for field in (fields or [])] or list(FIELDS)
    unknown = [field for field in wanted if field not in FIELDS]
    if unknown:
        return invalid_input(TOOL, f"Unknown field(s) {unknown}. Allowed: {list(FIELDS)}")

    try:
        profile, exists = load_profile()
    except Exception as exc:
        return failure(TOOL, exc)

    return {
        "tool": TOOL,
        "ok": True,
        "exists": exists,
        "profile": {field: profile[field] for field in wanted},
        "missing": [field for field in wanted if not profile[field]],
        "privacy_note": PRIVACY_NOTE,
    }

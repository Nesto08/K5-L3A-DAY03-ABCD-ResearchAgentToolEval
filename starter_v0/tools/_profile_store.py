"""Local user profile store shared by the profile, profile_save and now tools.

The profile is one JSON file. Default: starter_v0/user_profile/profile.json (gitignored).
Set SHERLOCK_PROFILE_PATH to use another file, e.g. a copy of user_profile/profile.example.json
when running eval, so eval runs never overwrite the real profile.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from tools._shared import ROOT

PROFILE_ENV = "SHERLOCK_PROFILE_PATH"
DEFAULT_PROFILE_PATH = ROOT / "user_profile" / "profile.json"
DEFAULT_TIMEZONE = "Asia/Ho_Chi_Minh"

SCALAR_FIELDS = ("name", "city", "timezone", "language")
LIST_FIELDS = ("interests", "followed_accounts")
FIELDS = SCALAR_FIELDS + LIST_FIELDS


def empty_profile() -> dict[str, Any]:
    return {**{field: "" for field in SCALAR_FIELDS}, **{field: [] for field in LIST_FIELDS}}


def profile_path() -> Path:
    raw = os.getenv(PROFILE_ENV, "").strip()
    if not raw:
        return DEFAULT_PROFILE_PATH
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def load_profile() -> tuple[dict[str, Any], bool]:
    """Return (profile, exists). Only known fields are read; anything else in the file is ignored."""
    path = profile_path()
    profile = empty_profile()
    if not path.exists():
        return profile, False
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    for field in SCALAR_FIELDS:
        value = data.get(field)
        if isinstance(value, str):
            profile[field] = value.strip()
    for field in LIST_FIELDS:
        value = data.get(field)
        if isinstance(value, list):
            profile[field] = [str(item).strip() for item in value if str(item).strip()]
    return profile, True


def save_profile(profile: dict[str, Any]) -> Path:
    path = profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path

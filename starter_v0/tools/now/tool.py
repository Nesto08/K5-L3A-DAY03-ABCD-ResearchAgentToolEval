from __future__ import annotations

from datetime import date, datetime, timedelta, timezone as dt_timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tools._profile_store import DEFAULT_TIMEZONE, load_profile
from tools._team import invalid_input

TOOL = "now"
WEEKDAYS_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def _utcnow() -> datetime:
    """Separate function so tests can freeze the clock."""
    return datetime.now(dt_timezone.utc)


def _resolve_timezone(requested: str) -> tuple[str, str]:
    if requested:
        return requested, "argument"
    try:
        profile, _ = load_profile()
        if profile.get("timezone"):
            return profile["timezone"], "profile"
    except Exception:
        pass  # a broken profile must not stop the clock
    return DEFAULT_TIMEZONE, "default"


def _weekend(today: date) -> tuple[date, date]:
    """Saturday and Sunday of the current weekend; on Sunday that is yesterday and today."""
    if today.weekday() == 6:
        return today - timedelta(days=1), today
    saturday = today + timedelta(days=5 - today.weekday())
    return saturday, saturday + timedelta(days=1)


def get_current_time(timezone: str = "") -> dict[str, Any]:
    tz_name, source = _resolve_timezone(str(timezone or "").strip())
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        return invalid_input(
            TOOL,
            f"Unknown timezone '{tz_name}'. Use an IANA name such as Asia/Ho_Chi_Minh "
            "(on Windows this also needs `pip install tzdata`).",
        )

    now = _utcnow().astimezone(tz)
    today = now.date()
    saturday, sunday = _weekend(today)
    offset = now.strftime("%z")
    return {
        "tool": TOOL,
        "ok": True,
        "timezone": tz_name,
        "timezone_source": source,
        "iso": now.isoformat(timespec="seconds"),
        "date": today.isoformat(),
        "time": now.strftime("%H:%M"),
        "weekday": WEEKDAYS_VI[today.weekday()],
        "utc_offset": f"{offset[:3]}:{offset[3:]}",
        "yesterday": (today - timedelta(days=1)).isoformat(),
        "tomorrow": (today + timedelta(days=1)).isoformat(),
        "weekend": {"saturday": saturday.isoformat(), "sunday": sunday.isoformat()},
    }

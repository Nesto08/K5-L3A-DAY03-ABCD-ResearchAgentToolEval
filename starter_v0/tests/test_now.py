"""Unit tests for the `now` tool, with a frozen clock."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

import tools.now.tool as now_module
from tools import TOOL_FUNCTIONS

now_tool = TOOL_FUNCTIONS["now"]


@pytest.fixture
def frozen(monkeypatch):
    def _freeze(iso_utc: str) -> None:
        moment = datetime.fromisoformat(iso_utc).replace(tzinfo=timezone.utc)
        monkeypatch.setattr(now_module, "_utcnow", lambda: moment)
    return _freeze


@pytest.fixture
def profile_file(tmp_path, monkeypatch):
    path = tmp_path / "profile.json"
    monkeypatch.setenv("SHERLOCK_PROFILE_PATH", str(path))
    return path


def test_now_default_timezone_converts_utc_to_vietnam_time(frozen, profile_file) -> None:
    frozen("2026-11-10T05:30:00")  # Tuesday, 12:30 in Vietnam

    result = now_tool()

    assert result["ok"] is True
    assert result["timezone"] == "Asia/Ho_Chi_Minh"
    assert result["timezone_source"] == "default"
    assert result["iso"] == "2026-11-10T12:30:00+07:00"
    assert result["time"] == "12:30"
    assert result["weekday"] == "Thứ Ba"
    assert result["utc_offset"] == "+07:00"
    assert result["yesterday"] == "2026-11-09"
    assert result["tomorrow"] == "2026-11-11"
    assert result["weekend"] == {"saturday": "2026-11-14", "sunday": "2026-11-15"}


def test_now_uses_timezone_from_profile(frozen, profile_file) -> None:
    profile_file.write_text(json.dumps({"timezone": "Asia/Tokyo"}), encoding="utf-8")
    frozen("2026-11-10T15:30:00")  # already Wednesday in Tokyo

    result = now_tool()

    assert result["timezone_source"] == "profile"
    assert result["date"] == "2026-11-11"
    assert result["weekday"] == "Thứ Tư"


def test_now_argument_overrides_profile(frozen, profile_file) -> None:
    profile_file.write_text(json.dumps({"timezone": "Asia/Tokyo"}), encoding="utf-8")
    frozen("2026-11-10T05:30:00")

    result = now_tool(timezone="Europe/London")

    assert result["timezone_source"] == "argument"
    assert result["time"] == "05:30"


@pytest.mark.parametrize("bad", ["Mars/Base", "GMT+7 Hanoi", "../etc/passwd"])
def test_now_invalid_timezone_from_model_returns_invalid_input(frozen, profile_file, bad) -> None:
    frozen("2026-11-10T05:30:00")

    result = now_tool(timezone=bad)

    assert result["ok"] is False
    assert result["error"] == "invalid_input"


def test_now_on_sunday_weekend_is_yesterday_and_today(frozen, profile_file) -> None:
    frozen("2026-11-15T03:00:00")  # Sunday 10:00 in Vietnam

    result = now_tool()

    assert result["weekday"] == "Chủ Nhật"
    assert result["weekend"] == {"saturday": "2026-11-14", "sunday": "2026-11-15"}


def test_now_corrupt_profile_falls_back_to_default(frozen, profile_file) -> None:
    profile_file.write_text("{broken", encoding="utf-8")
    frozen("2026-11-10T05:30:00")

    result = now_tool()

    assert result["ok"] is True
    assert result["timezone_source"] == "default"

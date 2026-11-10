"""Unit tests for the `profile_save` tool (write the local user profile, guarded by confirmation)."""
from __future__ import annotations

import json

import pytest

from tools import TOOL_FUNCTIONS

save_tool = TOOL_FUNCTIONS["profile_save"]


@pytest.fixture
def profile_file(tmp_path, monkeypatch):
    path = tmp_path / "nested" / "profile.json"
    monkeypatch.setenv("SHERLOCK_PROFILE_PATH", str(path))
    return path


def read(path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_profile_save_without_confirmation_does_not_write(profile_file) -> None:
    result = save_tool(field="city", value="Huế", confirmed=False)

    assert result["status"] == "needs_confirmation"
    assert result["pending_value"] == "Huế"
    assert not profile_file.exists()


def test_profile_save_string_false_is_not_confirmation(profile_file) -> None:
    result = save_tool(field="city", value="Huế", confirmed="false")

    assert result["status"] == "needs_confirmation"
    assert not profile_file.exists()


def test_profile_save_confirmed_writes_and_keeps_other_fields(profile_file) -> None:
    profile_file.parent.mkdir(parents=True)
    profile_file.write_text(json.dumps({"name": "Minh", "interests": ["AI"]}), encoding="utf-8")

    result = save_tool(field="city", value="  Huế ", confirmed=True)

    assert result == {"tool": "profile_save", "ok": True, "status": "saved", "field": "city", "action": "set", "value": "Huế"}
    saved = read(profile_file)
    assert saved["city"] == "Huế"
    assert saved["name"] == "Minh"
    assert saved["interests"] == ["AI"]


def test_profile_save_add_splits_commas_and_dedupes_case_insensitively(profile_file) -> None:
    save_tool(field="interests", value="AI", confirmed=True)

    result = save_tool(field="interests", value="ai, Bóng đá ,robotics", action="add", confirmed=True)

    assert result["value"] == ["AI", "Bóng đá", "robotics"]
    assert read(profile_file)["interests"] == ["AI", "Bóng đá", "robotics"]


def test_profile_save_remove_drops_matching_items(profile_file) -> None:
    save_tool(field="interests", value="AI, robotics", confirmed=True)

    result = save_tool(field="interests", value="ROBOTICS", action="remove", confirmed=True)

    assert result["value"] == ["AI"]


def test_profile_save_followed_accounts_strips_at_sign(profile_file) -> None:
    result = save_tool(field="followed_accounts", value="@karpathy, sama", confirmed=True)

    assert result["value"] == ["karpathy", "sama"]


@pytest.mark.parametrize("kwargs, needle", [
    ({"field": "password", "value": "x"}, "Unknown field"),
    ({"field": "city", "value": "Huế", "action": "replace"}, "Unknown action"),
    ({"field": "city", "value": "Huế", "action": "add"}, "only supports action=set"),
    ({"field": "interests", "value": "", "action": "add"}, "needs at least one value"),
    ({"field": "timezone", "value": "Mars/Base"}, "Unknown timezone"),
    ({"field": "followed_accounts", "value": "not a handle!"}, "Invalid X handle"),
    ({"field": "city", "value": "x" * 81}, "at most 80"),
])
def test_profile_save_bad_input_from_model_is_rejected_without_writing(profile_file, kwargs, needle) -> None:
    result = save_tool(confirmed=True, **kwargs)

    assert result["ok"] is False
    assert result["error"] == "invalid_input"
    assert needle in result["message"]
    assert not profile_file.exists()


def test_profile_save_empty_set_clears_field(profile_file) -> None:
    save_tool(field="city", value="Huế", confirmed=True)

    result = save_tool(field="city", value="", confirmed=True)

    assert result["value"] == ""
    assert read(profile_file)["city"] == ""


def test_profile_save_corrupt_file_returns_error_dict(profile_file) -> None:
    profile_file.parent.mkdir(parents=True)
    profile_file.write_text("[1, 2", encoding="utf-8")

    result = save_tool(field="city", value="Huế", confirmed=True)

    assert result["ok"] is False
    assert result["error"] == "JSONDecodeError"
    assert profile_file.read_text(encoding="utf-8") == "[1, 2"

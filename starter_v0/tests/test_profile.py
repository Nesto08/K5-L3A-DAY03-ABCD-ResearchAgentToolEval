"""Unit tests for the `profile` tool (read the local user profile)."""
from __future__ import annotations

import json

import pytest

from tools import TOOL_FUNCTIONS

profile_tool = TOOL_FUNCTIONS["profile"]


@pytest.fixture
def profile_file(tmp_path, monkeypatch):
    path = tmp_path / "profile.json"
    monkeypatch.setenv("SHERLOCK_PROFILE_PATH", str(path))
    return path


def test_profile_returns_saved_fields_and_lists_empty_ones_as_missing(profile_file) -> None:
    profile_file.write_text(json.dumps({"city": "Hà Nội", "interests": ["AI"], "name": ""}), encoding="utf-8")

    result = profile_tool()

    assert result["ok"] is True
    assert result["exists"] is True
    assert result["profile"]["city"] == "Hà Nội"
    assert result["profile"]["interests"] == ["AI"]
    assert set(result["missing"]) == {"name", "timezone", "language", "followed_accounts"}


def test_profile_fields_argument_limits_the_output(profile_file) -> None:
    profile_file.write_text(json.dumps({"city": "Huế", "name": "Minh"}), encoding="utf-8")

    result = profile_tool(fields=["city"])

    assert result["profile"] == {"city": "Huế"}
    assert result["missing"] == []


def test_profile_without_file_reports_not_exists_and_everything_missing(profile_file) -> None:
    result = profile_tool()

    assert result["ok"] is True
    assert result["exists"] is False
    assert len(result["missing"]) == 6
    assert not profile_file.exists()


def test_profile_unknown_field_from_model_is_invalid_input(profile_file) -> None:
    result = profile_tool(fields=["city", "password"])

    assert result["ok"] is False
    assert result["error"] == "invalid_input"
    assert "password" in result["message"]


def test_profile_ignores_keys_outside_the_schema(profile_file) -> None:
    profile_file.write_text(json.dumps({"city": "Huế", "phone": "0900000000"}), encoding="utf-8")

    result = profile_tool()

    assert "phone" not in result["profile"]
    assert "0900000000" not in json.dumps(result)


def test_profile_corrupt_file_returns_error_dict(profile_file) -> None:
    profile_file.write_text("{not json", encoding="utf-8")

    result = profile_tool()

    assert result["ok"] is False
    assert result["error"] == "JSONDecodeError"

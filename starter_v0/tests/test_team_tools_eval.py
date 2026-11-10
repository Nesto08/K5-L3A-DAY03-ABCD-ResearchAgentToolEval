"""Suite contract and profile isolation; no model/API/network calls."""
from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import run_eval
from providers.base import ModelResponse, ToolCall
from scripts.run_team_tools_eval import isolated_profile, run_case
from tools import TOOL_FUNCTIONS, load_tool_declarations

ROOT = Path(__file__).resolve().parents[1]
SUITE = json.loads((ROOT / "data/eval_team_tools.json").read_text(encoding="utf-8"))


def test_suite_has_five_cases_per_tool_and_ten_per_turn_type():
    cases = SUITE["cases"]
    assert len(cases) == len({case["id"] for case in cases}) == 20
    assert Counter(case["metadata"]["tool"] for case in cases) == {
        "weather": 5, "now": 5, "profile": 5, "profile_save": 5,
    }
    assert sum("query" in case for case in cases) == 10
    assert sum("turns" in case for case in cases) == 10
    declarations = load_tool_declarations(ROOT / "artifacts/tools.yaml")
    run_eval.validate_expected_tools(cases, declarations, ROOT / "data/eval_team_tools.json")
    run_eval.validate_case_failure_types(cases, ROOT / "data/eval_team_tools.json")
    for case in cases:
        assert case["phase"] == "B"
        assert ("query" in case) != ("turns" in case)
        assert case["metadata"]["what_it_tests"].strip()
        assert bool(case["expect"].get("tool_calls")) != bool(case["expect"].get("no_tool"))


def test_profile_is_reset_between_cases_and_real_profile_is_untouched(tmp_path, monkeypatch):
    real = tmp_path / "user-profile.json"
    original = '{"city":"Do not change"}'
    real.write_text(original, encoding="utf-8")
    monkeypatch.setenv("SHERLOCK_PROFILE_PATH", str(real))
    with isolated_profile({"city": "Fixture"}) as first:
        assert first != real
        TOOL_FUNCTIONS["profile_save"](field="city", value="Changed", confirmed=True)
        assert json.loads(first.read_text(encoding="utf-8"))["city"] == "Changed"
    assert os.environ["SHERLOCK_PROFILE_PATH"] == str(real)
    assert real.read_text(encoding="utf-8") == original
    with isolated_profile({"city": "Fixture"}) as second:
        assert json.loads(second.read_text(encoding="utf-8"))["city"] == "Fixture"
    assert not first.exists() and not second.exists()


def test_profile_environment_is_restored_after_exception(monkeypatch):
    monkeypatch.delenv("SHERLOCK_PROFILE_PATH", raising=False)
    with pytest.raises(RuntimeError, match="test failure"):
        with isolated_profile({}):
            raise RuntimeError("test failure")
    assert "SHERLOCK_PROFILE_PATH" not in os.environ


def prepared(case):
    return {**case, "_messages": [{"role": "user", "content": "test"}]}


def test_confirmed_save_is_checked_against_the_profile_on_disk():
    case = next(case for case in SUITE["cases"] if case["id"] == "TT_S01_explicit_save_city")
    call = case["expect"]["tool_calls"][0]
    provider = SimpleNamespace(complete=Mock(return_value=ModelResponse(
        text=None, tool_calls=[ToolCall(call["name"], call["args"])],
    )))
    result = run_case(prepared(case), provider=provider, tools=[], model=None, defaults={}, seed=SUITE["profile_fixture"])
    assert result["result"]["fully_passed"] is True
    assert result["profile_state"]["after"]["city"] == "Huế"
    assert result["profile_state"]["after"]["interests"] == ["AI", "robotics"]


def test_routing_pass_does_not_hide_a_failed_write(monkeypatch):
    case = next(case for case in SUITE["cases"] if case["id"] == "TT_S01_explicit_save_city")
    call = case["expect"]["tool_calls"][0]
    monkeypatch.setitem(TOOL_FUNCTIONS, "profile_save", lambda **kwargs: {"ok": False, "error": "disk_full"})
    provider = SimpleNamespace(complete=Mock(return_value=ModelResponse(
        text=None, tool_calls=[ToolCall(call["name"], call["args"])],
    )))
    result = run_case(prepared(case), provider=provider, tools=[], model=None, defaults={}, seed=SUITE["profile_fixture"])
    assert result["result"]["passed"] is True
    assert result["result"]["execution_correct"] is False
    assert result["result"]["profile_state_correct"] is False
    assert result["result"]["fully_passed"] is False


def test_wrong_external_action_is_recorded_but_never_executed(monkeypatch):
    external_action = Mock(side_effect=AssertionError("send must not run"))
    monkeypatch.setitem(TOOL_FUNCTIONS, "send", external_action)
    case = next(case for case in SUITE["cases"] if case["id"] == "TT_S05_decline_save")
    provider = SimpleNamespace(complete=Mock(return_value=ModelResponse(
        text=None, tool_calls=[ToolCall("send", {"text": "test", "confirmed": True})],
    )))
    result = run_case(prepared(case), provider=provider, tools=[], model=None, defaults={}, seed=SUITE["profile_fixture"])
    external_action.assert_not_called()
    assert result["result"]["passed"] is False
    assert result["tool_results"][0]["result"]["error"] == "execution_outside_suite"


def test_generic_runner_refuses_this_suite_before_creating_a_provider(monkeypatch):
    factory = Mock(side_effect=AssertionError("provider must not be created"))
    monkeypatch.setattr(run_eval, "make_provider", factory)
    monkeypatch.setattr("sys.argv", ["run_eval.py", "--provider", "openrouter", "--version", "test", "--eval-cases", str(ROOT / "data/eval_team_tools.json")])
    with pytest.raises(SystemExit, match="isolated profiles"):
        run_eval.main()
    factory.assert_not_called()


def test_provider_failure_does_not_claim_tool_execution_or_profile_success():
    case = next(case for case in SUITE["cases"] if case["id"] == "TT_S01_explicit_save_city")
    provider = SimpleNamespace(complete=Mock(side_effect=RuntimeError("provider unavailable")))
    result = run_case(prepared(case), provider=provider, tools=[], model=None, defaults={}, seed=SUITE["profile_fixture"])
    assert result["result"]["failure_type"] == "provider_error"
    assert result["result"]["profile_state_correct"] is None
    assert result["result"]["execution_correct"] is None
    assert result["result"]["fully_passed"] is False
    assert result["tool_results"] == []

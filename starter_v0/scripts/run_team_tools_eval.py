"""Run the team-tool suite with a fresh temporary profile for every case."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run_eval as evaluator
from chat import execute_tool_call
from providers import PROVIDER_NAMES, make_provider
from tools import load_tool_declarations, to_openai_tools
from tools._profile_store import empty_profile
from versioning import artifact_version_dict, build_artifact_version

ALLOWED_EXECUTION = {"weather", "now", "profile", "profile_save", "clarify"}


def redact(text: str) -> str:
    for name, value in os.environ.items():
        if value and any(part in name for part in ("API_KEY", "TOKEN", "SECRET")):
            text = text.replace(value, "[REDACTED]")
    return re.sub(r"(?<![A-Za-z0-9])(?:gsk_|sk-)[A-Za-z0-9_.*-]+", "[REDACTED]", text)


@contextmanager
def isolated_profile(seed: dict[str, Any]) -> Iterator[Path]:
    previous = os.environ.get("SHERLOCK_PROFILE_PATH")
    with tempfile.TemporaryDirectory(prefix="sherlock-team-eval-") as directory:
        folder = Path(directory).resolve()
        assert folder.parent == Path(tempfile.gettempdir()).resolve()
        profile = folder / "profile.json"
        profile.write_text(json.dumps(seed, ensure_ascii=False), encoding="utf-8")
        os.environ["SHERLOCK_PROFILE_PATH"] = str(profile)
        try:
            yield profile
        finally:
            if previous is None:
                os.environ.pop("SHERLOCK_PROFILE_PATH", None)
            else:
                os.environ["SHERLOCK_PROFILE_PATH"] = previous


def run_case(
    case: dict[str, Any], *, provider: Any, tools: list[dict[str, Any]],
    model: str | None, defaults: dict[str, dict[str, Any]], seed: dict[str, Any],
) -> dict[str, Any]:
    initial = empty_profile()
    initial.update(deepcopy(case.get("metadata", {}).get("profile_fixture", seed)))
    expected_after = deepcopy(initial)
    expected_after.update(case["expect"].get("profile_updates", {}))
    with isolated_profile(initial) as profile_path:
        events = []
        try:
            response = provider.complete(
                tools=tools,
                messages=case["_messages"],
                model=model,
                temperature=0.0,
                tool_choice=None if case["expect"].get("no_tool") else "required",
            )
            calls = [{"name": call.name, "args": call.args} for call in response.tool_calls]
            result = evaluator.evaluate_phase_b(case, calls, response.text, defaults)
            for call in response.tool_calls:
                if call.name in ALLOWED_EXECUTION:
                    events.append(execute_tool_call(call))
                else:
                    events.append({"tool": call.name, "args": call.args, "result": {
                        "ok": False, "error": "execution_outside_suite",
                        "message": "Call recorded for routing; execution is limited to team tools and clarify.",
                    }})
        except Exception as exc:
            result = {
                "passed": False, "failure_type": "provider_error",
                "case_failure_type": case["failure_type"], "observed_mismatch": "provider_error",
                "routing_correct": False, "args_correct": False, "actual_tool_calls": [],
                "actual_text": None, "failures": [redact(f"{type(exc).__name__}: {exc}")],
            }
        after = json.loads(profile_path.read_text(encoding="utf-8"))
        measured = result.get("failure_type") != "provider_error"
        state_correct = after == expected_after if measured else None
        execution_correct = not any(event.get("result", {}).get("error") for event in events) if measured else None
        result.update({"profile_state_correct": state_correct, "execution_correct": execution_correct,
                       "fully_passed": result["passed"] and state_correct and execution_correct})
        return {
            "id": case["id"], "phase": "B", "suite": "team_tools", "case_suite": "team_tools",
            "is_multiturn": "turns" in case, "metadata": case.get("metadata", {}),
            "input": case.get("query") or case.get("turns"), "expect": case["expect"],
            "result": result, "tool_results": events,
            "profile_state": {"before": initial, "expected_after": expected_after, "after": after},
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=[name for name in PROVIDER_NAMES if name not in {"auto", "gemini-openai"}], default="openrouter")
    parser.add_argument("--model", default=None)
    parser.add_argument("--version", required=True)
    parser.add_argument("--eval-cases", type=Path, default=ROOT / "data/eval_team_tools.json")
    parser.add_argument("--system-prompt", type=Path, default=ROOT / "artifacts/system_prompt.md")
    parser.add_argument("--tools", type=Path, default=ROOT / "artifacts/tools.yaml")
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "runs")
    args = parser.parse_args()
    dataset = json.loads(args.eval_cases.read_text(encoding="utf-8"))
    cases = evaluator.load_cases(args.eval_cases, "B")
    if not cases:
        raise SystemExit("No phase B cases in the selected suite.")
    seed = dataset.get("profile_fixture", {})
    declarations = load_tool_declarations(args.tools)
    evaluator.validate_expected_tools(cases, declarations, args.eval_cases)
    defaults = evaluator.tool_arg_defaults(declarations)
    tools = to_openai_tools(declarations)
    provider = make_provider(args.provider)
    model = args.model or getattr(provider, "default_model", None)
    system_prompt = args.system_prompt.read_text(encoding="utf-8")
    artifact = build_artifact_version(args.version, args.system_prompt, args.tools)
    results = []
    for case in cases:
        print(f"Running {case['id']}...", flush=True)
        prepared = {**case, "_messages": [{"role": "system", "content": system_prompt}, *evaluator.case_messages(case)]}
        results.append(run_case(prepared, provider=provider, tools=tools, model=model, defaults=defaults, seed=seed))
    summary = evaluator.summarize(results)
    measured = [item for item in results if item["result"].get("failure_type") != "provider_error"]
    summary.update({
        "profile_state_measured_cases": len(measured),
        "profile_state_accuracy": sum(item["result"]["profile_state_correct"] for item in measured) / len(measured) if measured else None,
        "tool_execution_error_cases": sum(item["result"]["execution_correct"] is False for item in measured),
        "fully_passed_cases": sum(item["result"]["fully_passed"] for item in results),
        "full_accuracy": sum(item["result"]["fully_passed"] for item in results) / len(results),
    })
    now = datetime.now()
    run_id = "_".join([evaluator.safe_slug(args.version), "B", "team_tools", args.provider, now.strftime("%Y%m%dT%H%M%S%f")])
    payload = {
        "run_id": run_id, **artifact_version_dict(artifact), "phase": "B", "suite": "team_tools",
        "provider": args.provider, "model": model, "system_prompt": str(args.system_prompt),
        "tools": str(args.tools), "eval_cases": str(args.eval_cases),
        **evaluator.load_dataset_info(args.eval_cases), "generated_at": now.isoformat(timespec="seconds"),
        "profile_isolation": "Fresh temporary profile per case; real profile is never used.",
        "execution_allowlist": sorted(ALLOWED_EXECUTION),
        "summary": summary, "results": results,
    }
    args.runs_dir.mkdir(parents=True, exist_ok=True)
    target = args.runs_dir / f"{run_id}.json"
    target.write_text(redact(json.dumps(payload, ensure_ascii=False, indent=2, default=str)) + "\n", encoding="utf-8")
    evaluator.print_table(results, summary)
    print(f"Saved: {target}")


if __name__ == "__main__":
    main()

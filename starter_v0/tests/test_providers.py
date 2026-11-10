"""Provider registry and fallback chain. Offline: fake providers, no SDK call."""
from __future__ import annotations

from typing import Any

import pytest

import providers
from providers import AllProvidersFailed, available_providers, make_provider, provider_problem
from providers.base import ModelResponse
from providers.fallback_provider import FallbackProvider

PROVIDER_ENV_VARS = [
    "GEMINI_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY",
    "OLLAMA_BASE_URL", "OLLAMA_MODEL", "LAB_PROVIDER", "LAB_PROVIDER_ORDER",
]


@pytest.fixture(autouse=True)
def no_provider_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in PROVIDER_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    # Treat every SDK as installed, so tests do not depend on the venv.
    monkeypatch.setattr(providers, "_module_installed", lambda module: True)


class FakeProvider:
    def __init__(self, error: Exception | None = None, default_model: str = "fake-model") -> None:
        self.error = error
        self.default_model = default_model
        self.models: list[str | None] = []

    def complete(self, messages: list[dict[str, str]], tools: Any = None, *, model: str | None = None, **kwargs: Any) -> ModelResponse:
        self.models.append(model)
        if self.error:
            raise self.error
        return ModelResponse(text="ok", tool_calls=[], raw=None)


def test_auto_uses_only_providers_with_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("GROQ_API_KEY", "x")

    assert available_providers() == ["openai", "groq"]
    assert make_provider("auto").names == ["openai", "groq"]


def test_auto_follows_lab_provider_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("LAB_PROVIDER_ORDER", "openai, gemini")

    assert make_provider("auto").names == ["openai", "gemini"]


def test_auto_without_any_key_says_which_key_is_missing() -> None:
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        make_provider("auto")


def test_provider_problem_reports_missing_key_and_package(monkeypatch: pytest.MonkeyPatch) -> None:
    assert "OPENROUTER_API_KEY" in provider_problem("openrouter")

    monkeypatch.setenv("GEMINI_API_KEY", "x")
    monkeypatch.setattr(providers, "_module_installed", lambda module: False)
    assert "google.genai" in provider_problem("gemini")


def test_fallback_moves_on_and_records_who_answered() -> None:
    first = FakeProvider(error=RuntimeError("429 RESOURCE_EXHAUSTED"))
    second = FakeProvider(default_model="gpt-4o-mini")
    chain = FallbackProvider([("gemini", first), ("openai", second)])

    response = chain.complete([{"role": "user", "content": "hi"}], model="gemini-3.5-flash")

    assert response.text == "ok"
    assert chain.last_provider == "openai"
    assert chain.last_model == "gpt-4o-mini"
    assert chain.last_errors[0].startswith("gemini: RuntimeError")
    # The model override belongs to the first provider only.
    assert first.models == ["gemini-3.5-flash"]
    assert second.models == [None]


def test_fallback_raises_with_every_error_when_all_fail() -> None:
    chain = FallbackProvider([
        ("gemini", FakeProvider(error=RuntimeError("quota"))),
        ("openai", FakeProvider(error=RuntimeError("bad key"))),
    ])

    with pytest.raises(AllProvidersFailed) as info:
        chain.complete([{"role": "user", "content": "hi"}])

    assert "gemini" in str(info.value) and "openai" in str(info.value)

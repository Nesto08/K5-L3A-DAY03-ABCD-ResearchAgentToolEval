from __future__ import annotations

from typing import Any

from providers.base import ModelResponse


class AllProvidersFailed(RuntimeError):
    """Every provider in the chain raised. The message lists each error."""


class FallbackProvider:
    """Try providers in order; when one raises, move on to the next.

    Any error moves on (quota, wrong key, network, a model that rejects the request),
    so the UI keeps answering as long as one provider works. That also means one
    conversation can be answered by different models. For eval, use a single fixed
    provider so the score belongs to one model.

    A `model` override is passed to the first provider only: a Gemini model name is
    not valid for OpenAI and vice versa. Later providers use their default model.
    """

    def __init__(self, chain: list[tuple[str, Any]]) -> None:
        if not chain:
            raise ValueError("FallbackProvider needs at least one provider")
        self.chain = chain
        self.default_model = getattr(chain[0][1], "default_model", None)
        self.last_provider: str | None = None
        self.last_model: str | None = None
        self.last_errors: list[str] = []

    @property
    def names(self) -> list[str]:
        return [name for name, _ in self.chain]

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        self.last_errors = []
        for index, (name, provider) in enumerate(self.chain):
            provider_model = model if index == 0 else None
            try:
                response = provider.complete(
                    messages, tools, model=provider_model, temperature=temperature, tool_choice=tool_choice
                )
            except Exception as exc:  # noqa: BLE001 - any failure moves on to the next provider
                self.last_errors.append(f"{name}: {type(exc).__name__}: {str(exc)[:300]}")
                print(f"[fallback] {name} lỗi ({type(exc).__name__}), thử provider tiếp theo.")
                continue
            self.last_provider = name
            self.last_model = provider_model or getattr(provider, "default_model", None)
            return response
        raise AllProvidersFailed("Tất cả provider đều lỗi:\n" + "\n".join(f"- {error}" for error in self.last_errors))

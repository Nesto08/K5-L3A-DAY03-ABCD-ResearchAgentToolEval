from __future__ import annotations

from typing import Any

from providers.base import ModelResponse


def is_quota_error(exc: BaseException) -> bool:
    """True when a provider error means the account ran out of usage/quota.

    Gemini (google-genai) raises ClientError with `.code == 429` and a
    RESOURCE_EXHAUSTED message. OpenAI raises RateLimitError (`status_code == 429`)
    with an `insufficient_quota` code.
    """
    for attr in ("code", "status_code"):
        if getattr(exc, attr, None) == 429:
            return True
    text = str(exc).lower()
    return "resource_exhausted" in text or "insufficient_quota" in text or "quota" in text


class FallbackProvider:
    """Try `primary` first; switch to `fallback` only when `primary` is out of quota.

    `model` is passed to the primary only. The fallback uses its own default model,
    because a Gemini model name is not valid for OpenAI and vice versa.
    """

    def __init__(self, primary: Any, fallback: Any, *, primary_name: str, fallback_name: str) -> None:
        self.primary = primary
        self.fallback = fallback
        self.primary_name = primary_name
        self.fallback_name = fallback_name
        self.default_model = getattr(primary, "default_model", None)
        self.last_provider: str | None = None

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        try:
            response = self.primary.complete(
                messages, tools, model=model, temperature=temperature, tool_choice=tool_choice
            )
            self.last_provider = self.primary_name
            return response
        except Exception as exc:  # noqa: BLE001 - only quota errors trigger fallback below
            if not is_quota_error(exc):
                raise
            print(f"[fallback] {self.primary_name} hết quota, chuyển sang {self.fallback_name}.")
            response = self.fallback.complete(
                messages, tools, model=None, temperature=temperature, tool_choice=tool_choice
            )
            self.last_provider = self.fallback_name
            return response

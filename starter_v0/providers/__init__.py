"""Provider registry: the one place that knows which providers exist and what each needs.

chat.py, run_eval.py, the preflight script and app.py all read the provider list from
here, so adding a provider means adding one line to `_REGISTRY`.
"""
from __future__ import annotations

import importlib.util
import os

from providers.openai_provider import OpenAIProvider
from providers.openrouter_provider import OpenRouterProvider
from providers.anthropic_provider import AnthropicProvider
from providers.gemini_provider import GeminiProvider
from providers.ollama_provider import OllamaProvider
from providers.groq_provider import GroqProvider
from providers.fallback_provider import AllProvidersFailed, FallbackProvider

# name -> (class, env var that holds the key or None, module the SDK provides)
_REGISTRY = {
    "gemini": (GeminiProvider, "GEMINI_API_KEY", "google.genai"),
    "openai": (OpenAIProvider, "OPENAI_API_KEY", "openai"),
    "openrouter": (OpenRouterProvider, "OPENROUTER_API_KEY", "openai"),
    "anthropic": (AnthropicProvider, "ANTHROPIC_API_KEY", "anthropic"),
    "groq": (GroqProvider, "GROQ_API_KEY", "openai"),
    "ollama": (OllamaProvider, None, "openai"),
}

# `auto` tries these in order. Override with LAB_PROVIDER_ORDER=openai,gemini in .env.
DEFAULT_AUTO_ORDER = ["gemini", "openai", "openrouter", "anthropic", "groq", "ollama"]

PROVIDER_NAMES = ["auto", "gemini-openai", *_REGISTRY]

__all__ = [
    "AllProvidersFailed",
    "PROVIDER_NAMES",
    "auto_order",
    "available_providers",
    "default_provider",
    "make_provider",
    "provider_problem",
]


def _module_installed(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


def provider_problem(name: str) -> str | None:
    """Why `name` cannot run on this machine, or None when it is ready."""
    _, key_env, module = _REGISTRY[name]
    if key_env and not os.getenv(key_env):
        return f"thiếu {key_env} trong .env"
    if name == "ollama" and not (os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_MODEL")):
        return "chưa đặt OLLAMA_BASE_URL hoặc OLLAMA_MODEL trong .env"
    if not _module_installed(module):
        return f"chưa cài `{module}`: chạy pip install -r requirements.txt trong venv"
    return None


def auto_order() -> list[str]:
    raw = os.getenv("LAB_PROVIDER_ORDER", "")
    order = [name.strip() for name in raw.split(",") if name.strip() in _REGISTRY]
    return order or list(DEFAULT_AUTO_ORDER)


def available_providers() -> list[str]:
    """Providers whose key and SDK are present, in `auto` order."""
    return [name for name in auto_order() if provider_problem(name) is None]


def default_provider() -> str:
    """Provider the UI selects first: LAB_PROVIDER from .env, else `auto`."""
    name = os.getenv("LAB_PROVIDER", "auto").strip()
    return name if name in PROVIDER_NAMES else "auto"


def make_provider(name: str):
    if name == "auto":
        ready = available_providers()
        if not ready:
            details = "; ".join(f"{n}: {provider_problem(n)}" for n in auto_order())
            raise RuntimeError(f"Không có provider nào dùng được ({details}). Thêm ít nhất một key vào starter_v0/.env.")
        return FallbackProvider([(n, _REGISTRY[n][0]()) for n in ready])
    if name == "gemini-openai":
        return FallbackProvider([("gemini", GeminiProvider()), ("openai", OpenAIProvider())])
    if name in _REGISTRY:
        return _REGISTRY[name][0]()
    raise ValueError(f"Unknown provider: {name}")

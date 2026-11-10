from providers.openai_provider import OpenAIProvider
from providers.openrouter_provider import OpenRouterProvider
from providers.anthropic_provider import AnthropicProvider
from providers.gemini_provider import GeminiProvider
from providers.ollama_provider import OllamaProvider
from providers.groq_provider import GroqProvider
from providers.fallback_provider import FallbackProvider


def make_provider(name: str):
    if name == "gemini-openai":
        # Gemini first; OpenAI only when Gemini reports quota exhausted.
        return FallbackProvider(
            GeminiProvider(),
            OpenAIProvider(),
            primary_name="gemini",
            fallback_name="openai",
        )
    if name == "openai":
        return OpenAIProvider()
    if name == "openrouter":
        return OpenRouterProvider()
    if name == "anthropic":
        return AnthropicProvider()
    if name == "gemini":
        return GeminiProvider()
    if name == "ollama":
        return OllamaProvider()
    if name == "groq":
        return GroqProvider()
    raise ValueError(f"Unknown provider: {name}")

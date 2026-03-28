"""Factory to instantiate the configured LLM provider."""
from .base import LLMProvider


def get_provider(provider_name: str, **kwargs) -> LLMProvider:
    """Return an LLMProvider instance for the given provider name."""
    if provider_name == 'ollama':
        from .ollama_provider import OllamaProvider
        return OllamaProvider(**kwargs)
    elif provider_name == 'openai':
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(**kwargs)
    elif provider_name == 'gemini':
        from .gemini_provider import GeminiProvider
        return GeminiProvider(**kwargs)
    elif provider_name == 'claude':
        from .claude_provider import ClaudeProvider
        return ClaudeProvider(**kwargs)
    else:
        raise ValueError(f"Proveedor LLM no soportado: {provider_name}")

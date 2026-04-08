"""
Shared LLM client factory for the Flask backend services.

Returns an ``openai.OpenAI`` client configured for the chosen provider
(Groq, Ollama, or any custom OpenAI-compatible server), allowing backend
services to be provider-agnostic.
"""

import sys
import os

# Allow importing from the project root when this module is executed directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from llm_providers import (
    PROVIDERS,
    DEFAULT_PROVIDER,
    get_openai_client,
    get_default_model,
)

__all__ = ["get_client", "get_model", "PROVIDERS", "DEFAULT_PROVIDER"]


def get_client(provider: str = DEFAULT_PROVIDER, api_key: str = None, base_url: str = None):
    """
    Return an ``openai.OpenAI`` client configured for the selected provider.

    Args:
        provider: One of 'groq', 'ollama', or 'openai_compatible'.
        api_key:  API key for providers that require authentication.
        base_url: Override the provider's default base URL.

    Returns:
        An ``openai.OpenAI`` instance ready for ``client.chat.completions.create(...)``.
    """
    return get_openai_client(provider=provider, api_key=api_key, base_url=base_url)


def get_model(provider: str = DEFAULT_PROVIDER, model: str = None) -> str:
    """
    Return the model name to use, falling back to the provider's default.

    Args:
        provider: Provider key.
        model:    Explicit model name supplied by the caller (may be None).

    Returns:
        A non-empty model name string.
    """
    return get_default_model(provider=provider, model=model)

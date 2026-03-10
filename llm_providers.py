"""
LLM Provider configuration for the Question Paper Generator.

Supports Groq (cloud), Ollama (local), and any custom OpenAI-compatible API,
so you are no longer dependent on a single provider. You can run your own
fine-tuned model or any open-source model locally via Ollama.
"""

# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

PROVIDERS = {
    "groq": {
        "name": "Groq (Cloud)",
        "description": (
            "Fast cloud inference via the Groq API. "
            "Get a free key at console.groq.com."
        ),
        "requires_api_key": True,
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ],
    },
    "ollama": {
        "name": "Ollama (Local)",
        "description": (
            "Run open-source models locally on your own machine via Ollama "
            "(ollama.com). No API key required."
        ),
        "requires_api_key": False,
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama3.2",
        "models": [],  # Populated dynamically based on locally pulled models
    },
    "openai_compatible": {
        "name": "Custom OpenAI-Compatible API",
        "description": (
            "Any fine-tuned or custom model that exposes an OpenAI-compatible "
            "REST API (e.g., LM Studio, vLLM, text-generation-webui, llama.cpp server)."
        ),
        "requires_api_key": False,
        "base_url": "",   # User must supply
        "default_model": "",  # User must supply
        "models": [],
    },
}

DEFAULT_PROVIDER = "groq"

# ---------------------------------------------------------------------------
# Factory: LangChain LLM (for Streamlit / generate_paper.py)
# ---------------------------------------------------------------------------

def get_langchain_llm(
    provider: str = DEFAULT_PROVIDER,
    api_key: str = None,
    model: str = None,
    base_url: str = None,
    temperature: float = 0,
):
    """
    Return a LangChain chat-model instance for the chosen provider.

    Uses the OpenAI-compatible interface, which works with Groq, Ollama, and
    any custom fine-tuned model server without changing the calling code.

    Args:
        provider:    One of 'groq', 'ollama', or 'openai_compatible'.
        api_key:     API key for providers that require one.
        model:       Model name. Falls back to the provider's default.
        base_url:    Override the provider's base URL for custom deployments.
        temperature: Sampling temperature (0 = deterministic).

    Returns:
        A ``ChatOpenAI`` instance configured for the selected provider.
    """
    from langchain_openai import ChatOpenAI

    config = PROVIDERS.get(provider, PROVIDERS[DEFAULT_PROVIDER])
    effective_base_url = base_url or config["base_url"]
    effective_model = model or config["default_model"]
    # Providers like Ollama don't need a real key, but the client still
    # requires a non-empty string value.
    effective_api_key = api_key or "not-needed"

    return ChatOpenAI(
        model=effective_model,
        temperature=temperature,
        api_key=effective_api_key,
        base_url=effective_base_url,
    )


# ---------------------------------------------------------------------------
# Factory: raw OpenAI-compatible client (for Flask backend services)
# ---------------------------------------------------------------------------

def get_openai_client(
    provider: str = DEFAULT_PROVIDER,
    api_key: str = None,
    base_url: str = None,
):
    """
    Return a raw ``openai.OpenAI`` client configured for the chosen provider.

    Suitable for direct ``client.chat.completions.create(...)`` calls,
    mirroring the interface previously provided by the ``groq`` package.

    Args:
        provider: One of 'groq', 'ollama', or 'openai_compatible'.
        api_key:  API key for providers that require one.
        base_url: Override the provider's base URL for custom deployments.

    Returns:
        An ``openai.OpenAI`` client configured for the selected provider.
    """
    from openai import OpenAI

    config = PROVIDERS.get(provider, PROVIDERS[DEFAULT_PROVIDER])
    effective_base_url = base_url or config["base_url"]
    effective_api_key = api_key or "not-needed"

    return OpenAI(
        api_key=effective_api_key,
        base_url=effective_base_url,
    )


def get_default_model(provider: str = DEFAULT_PROVIDER, model: str = None) -> str:
    """Return the model name to use: caller-supplied, or the provider default."""
    if model:
        return model
    return PROVIDERS.get(provider, PROVIDERS[DEFAULT_PROVIDER])["default_model"]

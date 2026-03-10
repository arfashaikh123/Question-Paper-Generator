"""
LLM Provider configuration for the Question Paper Generator.

Supports Groq (cloud), Ollama (local), Hugging Face Hub, local fine-tuned
models loaded directly via the transformers library, and any custom
OpenAI-compatible API.  You are no longer tied to a single provider and can
plug in your own custom-built or fine-tuned LLM.
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
    "huggingface_hub": {
        "name": "Hugging Face Hub",
        "description": (
            "Use any model hosted on Hugging Face Hub—including your own "
            "fine-tuned models—via the HF Inference API. "
            "Requires a Hugging Face access token (hf.co/settings/tokens). "
            "Enter the full model ID, e.g. 'username/my-finetuned-llama'."
        ),
        "requires_api_key": True,
        "base_url": "https://api-inference.huggingface.co/v1",
        "default_model": "",   # User must supply their model ID
        "models": [],
    },
    "local_transformers": {
        "name": "Local Custom Model (Transformers)",
        "description": (
            "Load a fine-tuned model directly from a local folder or Hugging "
            "Face Hub model ID using the 🤗 transformers library—no server "
            "process needed. Requires PyTorch and transformers to be installed. "
            "Enter a local path (e.g. /models/my-llm) or an HF model ID "
            "(e.g. username/my-finetuned-llama)."
        ),
        "requires_api_key": False,
        "base_url": "",   # Not used for local transformers
        "default_model": "",  # User must supply a path or model ID
        "models": [],
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

    For ``local_transformers``, the model is loaded directly from disk or
    Hugging Face Hub using the 🤗 transformers library (no server needed).
    For all other providers, the OpenAI-compatible interface is used.

    Args:
        provider:    One of 'groq', 'huggingface_hub', 'local_transformers',
                     'ollama', or 'openai_compatible'.
        api_key:     API key / token for providers that require one.
        model:       Model name, path, or HF model ID.
                     Falls back to the provider's default when not given.
        base_url:    Override the provider's base URL for custom deployments.
                     Ignored for 'local_transformers'.
        temperature: Sampling temperature (0 = deterministic).

    Returns:
        A LangChain chat-model instance configured for the selected provider.
    """
    # -----------------------------------------------------------------------
    # Local Transformers: load weights directly – no HTTP server required
    # -----------------------------------------------------------------------
    if provider == "local_transformers":
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
        except ImportError as exc:
            raise ImportError(
                "The 'local_transformers' provider requires 'transformers', "
                "'torch', and 'langchain-huggingface'. "
                "Install them with:\n"
                "  pip install langchain-huggingface transformers torch\n"
                f"Original error: {exc}"
            ) from exc

        model_id = model or ""
        if not model_id:
            raise ValueError(
                "A model path or Hugging Face model ID is required for the "
                "'local_transformers' provider (e.g. '/models/my-llm' or "
                "'username/my-finetuned-llama')."
            )

        hf_pipeline = pipeline(
            "text-generation",
            model=model_id,
            tokenizer=model_id,
            temperature=max(temperature, 1e-6),  # must be strictly > 0 for the pipeline
            do_sample=temperature > 0,
            max_new_tokens=2048,
        )
        llm = HuggingFacePipeline(pipeline=hf_pipeline)
        return ChatHuggingFace(llm=llm)

    # -----------------------------------------------------------------------
    # All OpenAI-compatible providers (Groq, HF Hub, Ollama, custom)
    # -----------------------------------------------------------------------
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

    Note: This function is not applicable to the ``local_transformers``
    provider.  For local models, use ``get_langchain_llm()`` instead.

    Args:
        provider: One of 'groq', 'huggingface_hub', 'ollama', or
                  'openai_compatible'.
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

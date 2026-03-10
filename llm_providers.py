"""
LLM Provider configuration for the Question Paper Generator.

Supports Groq (cloud), Ollama (local), Hugging Face Hub, local fine-tuned
models loaded directly via the transformers library, any custom
OpenAI-compatible API, and — most importantly — a **fully custom LLM you
built yourself** with no external API calls at all (``custom_callable``
provider).
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
    "custom_callable": {
        "name": "Custom Built LLM (No API)",
        "description": (
            "Use a LLM you built yourself — no API call, no server, no internet. "
            "Copy custom_llm_example.py to custom_llm.py and implement your "
            "generate(prompt: str) -> str function. "
            "The app loads it automatically."
        ),
        "requires_api_key": False,
        "base_url": "",
        "default_model": "custom",
        "models": [],
    },
}

DEFAULT_PROVIDER = "groq"

# ---------------------------------------------------------------------------
# Custom callable LLM — wraps any Python function/class in LangChain
# ---------------------------------------------------------------------------

# Module-level slot for a pre-registered callable (set by register_custom_llm).
_CUSTOM_LLM_FN = None


def register_custom_llm(fn):
    """
    Register a Python callable as the custom LLM for this session.

    ``fn`` must accept a single ``str`` (the prompt) and return a ``str``
    (the model's reply).  Call this *before* ``get_langchain_llm()`` when the
    ``custom_callable`` provider is selected.

    Example::

        from llm_providers import register_custom_llm

        def my_generate(prompt: str) -> str:
            # your own inference logic — no API, no internet
            return my_model.predict(prompt)

        register_custom_llm(my_generate)

    Args:
        fn: Any callable with signature ``(str) -> str``.
    """
    global _CUSTOM_LLM_FN
    if not callable(fn):
        raise TypeError(f"Expected a callable, got {type(fn)!r}")
    _CUSTOM_LLM_FN = fn


def _load_custom_llm_module(module_path: str = None):
    """
    Import the custom LLM module and return its ``generate`` callable.

    Search order:
    1. *module_path* argument (absolute or relative path to a .py file).
    2. ``LLM_CUSTOM_MODULE`` environment variable.
    3. ``custom_llm.py`` in the same directory as this file (project root).

    Raises:
        FileNotFoundError: when no module is found at any of the above paths.
        AttributeError: when the module does not expose a ``generate`` callable.
    """
    import importlib.util
    import os

    candidates = []
    if module_path:
        candidates.append(module_path)
    env_path = os.environ.get("LLM_CUSTOM_MODULE")
    if env_path:
        candidates.append(env_path)
    # Default: custom_llm.py next to this file (project root)
    candidates.append(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_llm.py")
    )

    for path in candidates:
        if os.path.isfile(path):
            spec = importlib.util.spec_from_file_location("_custom_llm_module", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            fn = getattr(module, "generate", None)
            if fn is None or not callable(fn):
                raise AttributeError(
                    f"Custom LLM module '{path}' must expose a callable named "
                    f"'generate(prompt: str) -> str', but none was found."
                )
            return fn

    raise FileNotFoundError(
        "No custom LLM module found.  Create 'custom_llm.py' in the project "
        "root by copying 'custom_llm_example.py' and implementing your "
        "'generate(prompt: str) -> str' function.  "
        "Alternatively set the LLM_CUSTOM_MODULE environment variable to the "
        "absolute path of your module."
    )


def _resolve_custom_llm_fn(module_path: str = None):
    """Return the registered callable, or load it from ``custom_llm.py``."""
    if _CUSTOM_LLM_FN is not None:
        return _CUSTOM_LLM_FN
    return _load_custom_llm_module(module_path)


def custom_llm_module_exists() -> bool:
    """Return True when ``custom_llm.py`` (or the env-var override) is present."""
    import os
    env_path = os.environ.get("LLM_CUSTOM_MODULE")
    if env_path and os.path.isfile(env_path):
        return True
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_llm.py")
    return os.path.isfile(default)


class _CustomCallableLLM:
    """
    Thin LangChain ``BaseChatModel`` that delegates to a plain Python callable.

    The callable receives the entire conversation history as a single formatted
    string (``SYSTEM: …\\nHUMAN: …``) and must return a plain ``str``.

    This class is intentionally defined *inside* this module so it is only
    imported when the ``custom_callable`` provider is actually selected,
    keeping the rest of the codebase free of LangChain imports at module load.
    """

    @staticmethod
    def build(fn):
        """Return a LangChain BaseChatModel instance backed by *fn*."""
        from typing import Any, List, Optional
        from langchain_core.language_models.chat_models import BaseChatModel
        from langchain_core.messages import BaseMessage, AIMessage
        from langchain_core.outputs import ChatGeneration, ChatResult

        class _LCWrapper(BaseChatModel):
            class Config:
                arbitrary_types_allowed = True

            _fn: Any  # stored as a private class-var, not a Pydantic field

            @property
            def _llm_type(self) -> str:
                return "custom_callable"

            def _generate(
                self,
                messages: List[BaseMessage],
                stop: Optional[List[str]] = None,
                run_manager: Any = None,
                **kwargs: Any,
            ) -> ChatResult:
                # Flatten the message list into a single prompt string
                prompt_parts = []
                for msg in messages:
                    role = getattr(msg, "type", "unknown").upper()
                    prompt_parts.append(f"{role}: {msg.content}")
                prompt = "\n".join(prompt_parts)

                response_text = self.__class__._fn(prompt)
                return ChatResult(
                    generations=[
                        ChatGeneration(message=AIMessage(content=response_text))
                    ]
                )

        # Attach the callable directly as a class-level attribute.
        # No staticmethod() wrapper needed — accessed as self.__class__._fn(prompt).
        _LCWrapper._fn = fn
        return _LCWrapper()

def get_langchain_llm(
    provider: str = DEFAULT_PROVIDER,
    api_key: str = None,
    model: str = None,
    base_url: str = None,
    temperature: float = 0,
    custom_module_path: str = None,
):
    """
    Return a LangChain chat-model instance for the chosen provider.

    For ``custom_callable``, the model is loaded from ``custom_llm.py`` (or
    the file pointed to by *custom_module_path* / ``LLM_CUSTOM_MODULE``) and
    invoked directly — **zero API calls, zero network traffic**.
    For ``local_transformers``, the model is loaded in-process via 🤗 transformers.
    For all other providers, the OpenAI-compatible interface is used.

    Args:
        provider:           One of 'groq', 'huggingface_hub', 'local_transformers',
                            'ollama', 'openai_compatible', or 'custom_callable'.
        api_key:            API key / token for providers that require one.
        model:              Model name, path, or HF model ID.
                            Falls back to the provider's default when not given.
        base_url:           Override the provider's base URL for custom deployments.
                            Ignored for 'local_transformers' and 'custom_callable'.
        temperature:        Sampling temperature (0 = deterministic).
        custom_module_path: Path to a Python file that exposes
                            ``generate(prompt: str) -> str``.
                            Only used when *provider* is ``'custom_callable'``.

    Returns:
        A LangChain chat-model instance configured for the selected provider.
    """
    # -----------------------------------------------------------------------
    # Custom callable: pure Python, no API call, no server
    # -----------------------------------------------------------------------
    if provider == "custom_callable":
        fn = _resolve_custom_llm_fn(module_path=custom_module_path)
        return _CustomCallableLLM.build(fn)

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
            temperature=max(temperature, 0.01),  # pipeline requires a strictly positive value
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

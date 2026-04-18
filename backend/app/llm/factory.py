from __future__ import annotations

from app.core.config import settings
from app.core.interfaces import LLMProvider
from app.llm.openai_compat import OpenAICompatProvider
from app.llm.llamacpp import LlamaCppProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai_compat": OpenAICompatProvider,
    "llamacpp": LlamaCppProvider,
}


def create_llm_provider() -> LLMProvider:
    """Instantiate the configured LLM provider."""
    provider_name = settings.llm.provider
    cls = _PROVIDERS.get(provider_name)
    if cls is None:
        raise ValueError(
            f"Unknown LLM provider '{provider_name}'. "
            f"Available: {', '.join(_PROVIDERS)}"
        )
    return cls()


def register_provider(name: str, cls: type[LLMProvider]) -> None:
    """Register a custom LLM provider at runtime."""
    _PROVIDERS[name] = cls

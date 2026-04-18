from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.interfaces import LLMProvider


class OpenAICompatProvider(LLMProvider):
    """Works with any OpenAI-compatible API: Ollama, vLLM, LiteLLM, OpenAI, etc."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self._base_url = (base_url or settings.llm.base_url).rstrip("/")
        self._api_key = api_key or settings.llm.api_key
        self._model = model or settings.llm.model

    async def complete(self, prompt: str, system: str | None = None) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": settings.llm.temperature,
            "max_tokens": settings.llm.max_tokens,
        }

        async with httpx.AsyncClient(timeout=settings.llm.timeout) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

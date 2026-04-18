from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.interfaces import LLMProvider


class LlamaCppProvider(LLMProvider):
    """Direct adapter for llama.cpp's native HTTP server (non-OpenAI endpoint)."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (base_url or settings.llm.base_url).rstrip("/")

    async def complete(self, prompt: str, system: str | None = None) -> str:
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        payload = {
            "prompt": full_prompt,
            "temperature": settings.llm.temperature,
            "n_predict": settings.llm.max_tokens,
            "stop": ["</s>", "<|im_end|>", "<|end|>"],
        }

        async with httpx.AsyncClient(timeout=settings.llm.timeout) as client:
            resp = await client.post(
                f"{self._base_url}/completion",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"]

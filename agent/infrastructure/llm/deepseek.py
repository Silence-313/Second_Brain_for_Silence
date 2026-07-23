"""DeepSeek LLM client — OpenAI-compatible API adapter."""

import json
from typing import Any

import httpx

from agent.exceptions import LLMAuthenticationError, LLMRateLimitError, LLMTimeoutError


class DeepSeekLLMClient:
    """Implements LLMClient protocol. OpenAI-compatible API."""

    def __init__(
        self,
        endpoint: str = "https://api.deepseek.com/v1",
        api_key: str = "",
        model: str = "deepseek-chat",
        timeout_ms: int = 60_000,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_ms = timeout_ms

    async def stream(
        self,
        messages: list[dict[str, Any]],
        on_chunk: Any = None,
        **kwargs: Any,
    ) -> str:
        url = f"{self._endpoint}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {
            "model": kwargs.get("model", self._model),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=self._timeout_ms / 1000) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                self._check_status(resp.status_code)
                full_text = ""
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_text += content
                                if on_chunk:
                                    await on_chunk(content)
                        except json.JSONDecodeError:
                            continue
                return full_text

    async def complete(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        url = f"{self._endpoint}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": kwargs.get("model", self._model),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=self._timeout_ms / 1000) as client:
            resp = await client.post(url, json=payload, headers=headers)
            self._check_status(resp.status_code)
            body = resp.json()
            choice = body.get("choices", [{}])[0]
            return {
                "content": choice.get("message", {}).get("content", ""),
                "model": body.get("model", self._model),
                "usage": body.get("usage", {}),
            }

    @staticmethod
    def _check_status(code: int) -> None:
        if code == 401:
            raise LLMAuthenticationError("Invalid API key")
        if code == 429:
            raise LLMRateLimitError("Rate limit exceeded")
        if code >= 500:
            raise LLMTimeoutError(f"Server error: {code}")

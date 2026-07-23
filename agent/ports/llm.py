"""LLM client protocol — abstract interface for language model API calls."""

from collections.abc import Awaitable, Callable
from typing import Any, Protocol


class LLMClient(Protocol):
    """Abstract LLM API client. Implementations: DeepSeekLLMClient, MockLLMClient."""

    async def stream(
        self,
        messages: list[dict[str, Any]],
        on_chunk: Callable[[str], Awaitable[None]],
        **kwargs: Any,
    ) -> str:
        """Stream a completion, calling on_chunk for each token. Returns full text."""
        ...

    async def complete(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Non-streaming completion. Returns full response with metadata."""
        ...

"""Mock LLM client — returns predetermined responses for testing."""

from typing import Any


class MockLLMClient:
    """Implements LLMClient protocol. Returns canned responses."""

    def __init__(
        self,
        responses: list[str] | None = None,
        default: str = "This is a mock response.",
    ) -> None:
        self._responses = responses or [default]
        self._index = 0
        self._calls: list[list[dict[str, Any]]] = []

    async def stream(
        self,
        messages: list[dict[str, Any]],
        on_chunk: Any = None,
        **kwargs: Any,
    ) -> str:
        self._calls.append(messages)
        response = self._next_response()
        if on_chunk:
            # Simulate streaming in chunks
            for i in range(0, len(response), 10):
                chunk = response[i : i + 10]
                await on_chunk(chunk)
        return response

    async def complete(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        self._calls.append(messages)
        return {
            "content": self._next_response(),
            "model": "mock",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

    def _next_response(self) -> str:
        resp = self._responses[self._index % len(self._responses)]
        self._index += 1
        return resp

    @property
    def call_count(self) -> int:
        return len(self._calls)

    @property
    def last_messages(self) -> list[dict[str, Any]] | None:
        return self._calls[-1] if self._calls else None

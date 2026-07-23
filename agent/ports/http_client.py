"""HTTP client protocol — abstract interface for HTTP requests."""

from typing import Any, Protocol


class HttpResponse(Protocol):
    """HTTP response wrapper."""

    @property
    def status_code(self) -> int: ...
    @property
    def text(self) -> str: ...
    @property
    def content(self) -> bytes: ...

    def json(self) -> Any: ...


class HttpClient(Protocol):
    """Abstract HTTP client. Implementation: HttpxHttpClient."""

    async def get(self, url: str, **kwargs: Any) -> HttpResponse:
        """HTTP GET request."""
        ...

    async def post(self, url: str, json: dict[str, Any] | None = None, **kwargs: Any) -> HttpResponse:
        """HTTP POST request with JSON body."""
        ...

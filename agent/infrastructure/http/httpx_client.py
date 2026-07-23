"""HTTPX client adapter — implements HttpClient protocol."""

from typing import Any

import httpx


class HttpxResponse:
    """Wraps httpx.Response to implement HttpResponse protocol."""

    def __init__(self, response: httpx.Response) -> None:
        self._resp = response

    @property
    def status_code(self) -> int:
        return self._resp.status_code

    @property
    def text(self) -> str:
        return self._resp.text

    @property
    def content(self) -> bytes:
        return self._resp.content

    def json(self) -> Any:
        return self._resp.json()


class HttpxHttpClient:
    """Implements HttpClient protocol using httpx."""

    def __init__(self, default_timeout: float = 30.0) -> None:
        self._timeout = default_timeout

    async def get(self, url: str, **kwargs: Any) -> HttpxResponse:
        timeout = kwargs.pop("timeout", self._timeout)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, **kwargs)
            return HttpxResponse(resp)

    async def post(
        self, url: str, json: dict[str, Any] | None = None, **kwargs: Any
    ) -> HttpxResponse:
        timeout = kwargs.pop("timeout", self._timeout)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=json, **kwargs)
            return HttpxResponse(resp)

"""Base HTTP client for AP REST API, one instance per AP."""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_HTTPS_PORT = 4431
DEFAULT_HTTP_PORT = 8001
DEFAULT_TIMEOUT = 15.0


class APClient:
    """httpx-based client for a single access point."""

    def __init__(
        self,
        ip: str,
        *,
        port: int = DEFAULT_HTTPS_PORT,
        scheme: str = "https",
        verify: bool = False,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.ip = ip
        self.port = port
        self.scheme = scheme
        self.base_url = f"{scheme}://{ip}:{port}/api"
        self._token: str | None = None
        self._client = httpx.Client(
            base_url=self.base_url,
            verify=verify,
            timeout=timeout,
        )

    @property
    def token(self) -> str | None:
        return self._token

    @token.setter
    def token(self, value: str | None) -> None:
        self._token = value

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._client.get(path, headers=self._headers(), **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._client.post(path, headers=self._headers(), **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._client.put(path, headers=self._headers(), **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._client.delete(path, headers=self._headers(), **kwargs)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> APClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

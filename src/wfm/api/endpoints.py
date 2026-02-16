"""Typed endpoint wrappers for AP /v1/ routes."""

from __future__ import annotations

from typing import Any

from wfm.api.client import APClient
from wfm.api.exceptions import APIError
from wfm.api.models import (
    ApplyResponse,
    DeviceInfoResponse,
    LoginResponse,
    NetworksResponse,
    SuccessResponse,
)


class APEndpoints:
    """High-level typed wrappers over APClient for specific API operations."""

    def __init__(self, client: APClient) -> None:
        self._client = client

    @property
    def client(self) -> APClient:
        return self._client

    def _check_err(self, data: dict[str, Any], path: str, status_code: int) -> None:
        err_code = data.get("errCode", 0)
        if err_code != 0:
            raise APIError(
                status_code=status_code,
                err_code=err_code,
                message=data.get("message", "unknown"),
                path=path,
            )

    # --- Auth ---

    def login(self, username: str, password: str) -> LoginResponse:
        resp = self._client.post(
            "/v1/sys/login",
            json={"login": {"username": username, "password": password}},
        )
        data = resp.json()
        self._check_err(data, "/v1/sys/login", resp.status_code)
        return LoginResponse.model_validate(data)

    # --- Wireless ---

    def get_networks(self) -> NetworksResponse:
        resp = self._client.get("/v1/wireless/networks")
        data = resp.json()
        self._check_err(data, "/v1/wireless/networks", resp.status_code)
        return NetworksResponse.model_validate(data)

    def get_radiostatus(self) -> dict[str, Any]:
        """Return raw radiostatus dict (shape differs between x20/x30)."""
        resp = self._client.get("/v1/wireless/radiostatus")
        data = resp.json()
        self._check_err(data, "/v1/wireless/radiostatus", resp.status_code)
        return data

    # --- Device ---

    def get_device_info(self) -> DeviceInfoResponse:
        resp = self._client.get("/v1/sys/mp-info")
        data = resp.json()
        self._check_err(data, "/v1/sys/mp-info", resp.status_code)
        return DeviceInfoResponse.model_validate(data)

    # --- Apply ---

    def apply(self) -> ApplyResponse:
        resp = self._client.post("/v1/sys/apply", json={})
        data = resp.json()
        self._check_err(data, "/v1/sys/apply", resp.status_code)
        return ApplyResponse.model_validate(data)

    def write_and_apply(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        requires_apply: bool = True,
    ) -> SuccessResponse:
        """Perform a config write, then optionally POST /v1/sys/apply.

        Args:
            method: HTTP method ("POST" or "PUT").
            path: API path (e.g. "/v1/wireless/network").
            json_body: JSON payload for the write operation.
            requires_apply: Whether to call /v1/sys/apply after the write.

        Returns:
            SuccessResponse from the write (or apply) operation.
        """
        if method.upper() == "POST":
            resp = self._client.post(path, json=json_body or {})
        elif method.upper() == "PUT":
            resp = self._client.put(path, json=json_body or {})
        else:
            raise ValueError(f"Unsupported method: {method}")

        data = resp.json()
        self._check_err(data, path, resp.status_code)
        result = SuccessResponse.model_validate(data)

        if requires_apply:
            self.apply()

        return result

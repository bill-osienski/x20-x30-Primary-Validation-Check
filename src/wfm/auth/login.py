"""Login service for AP authentication via POST /v1/sys/login."""

from __future__ import annotations

from dataclasses import dataclass

from wfm.api.endpoints import APEndpoints
from wfm.api.exceptions import APIError


@dataclass
class LoginResult:
    success: bool
    token: str = ""
    device_id: str = ""
    err_code: int = 0
    message: str = ""


class LoginService:
    """Authenticates against an AP and returns a JWT token."""

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

    def update_credentials(self, username: str, password: str) -> None:
        """Hot-swap credentials after re-entry."""
        self._username = username
        self._password = password

    @property
    def username(self) -> str:
        return self._username

    def login(self, endpoints: APEndpoints) -> LoginResult:
        """Attempt login and return result."""
        try:
            resp = endpoints.login(self._username, self._password)
        except APIError as e:
            return LoginResult(
                success=False,
                err_code=e.err_code,
                message=str(e),
            )
        except Exception as e:
            return LoginResult(success=False, message=str(e))

        if resp.login is None or not resp.login.token:
            return LoginResult(
                success=False,
                err_code=resp.errCode,
                message=resp.message or "No token in response",
            )

        return LoginResult(
            success=True,
            token=resp.login.token,
            device_id=resp.deviceId,
        )

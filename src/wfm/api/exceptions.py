"""Custom exception hierarchy for WFM API operations."""

from __future__ import annotations


class WfmError(Exception):
    """Base exception for all WFM errors."""


class AuthenticationError(WfmError):
    """Login or token acquisition failed."""


class TokenRefreshExhaustedError(AuthenticationError):
    """Re-authentication failed after maximum retries (per AP)."""

    def __init__(self, ip: str, attempts: int = 3) -> None:
        self.ip = ip
        self.attempts = attempts
        super().__init__(
            f"Token refresh exhausted for {ip} after {attempts} attempts. "
            "Credentials may have changed."
        )


class APIError(WfmError):
    """Non-auth API error from the access point."""

    def __init__(self, status_code: int, err_code: int, message: str, path: str = "") -> None:
        self.status_code = status_code
        self.err_code = err_code
        self.path = path
        super().__init__(f"API error {err_code} (HTTP {status_code}) on {path}: {message}")


class DeviceDetectionError(WfmError):
    """Could not determine AP hardware type from radiostatus response."""

    def __init__(self, ip: str, detail: str = "") -> None:
        self.ip = ip
        msg = f"Cannot detect device type for {ip}"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)


class GateBlockedError(WfmError):
    """Operation blocked by the compatibility gate."""

    def __init__(self, operation: str, ip: str, state: str) -> None:
        self.operation = operation
        self.ip = ip
        self.state = state
        super().__init__(
            f"Operation '{operation}' blocked for {ip}: compatibility state is {state}"
        )


class ConnectionError(WfmError):
    """Could not connect to the access point."""

    def __init__(self, ip: str, detail: str = "") -> None:
        self.ip = ip
        msg = f"Cannot connect to {ip}"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)

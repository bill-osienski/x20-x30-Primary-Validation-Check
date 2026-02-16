"""Per-AP JWT lifecycle: exp-based proactive refresh + reactive 401 handling."""

from __future__ import annotations

import time
from dataclasses import dataclass

import jwt

from wfm.api.endpoints import APEndpoints
from wfm.api.exceptions import TokenRefreshExhaustedError
from wfm.auth.login import LoginService

PROACTIVE_SKEW_SECONDS = 60  # Refresh 60s before exp
MAX_REAUTH_ATTEMPTS = 3


@dataclass
class TokenState:
    """Tracks token state for a single AP."""

    token: str = ""
    device_id: str = ""
    issued_at: float = 0.0
    expires_at: float | None = None  # From JWT exp claim, or None if unavailable
    consecutive_failures: int = 0


class TokenManager:
    """Manages JWT tokens for multiple APs, keyed by IP."""

    def __init__(self, login_service: LoginService) -> None:
        self._login_service = login_service
        self._tokens: dict[str, TokenState] = {}

    @property
    def login_service(self) -> LoginService:
        return self._login_service

    def get_state(self, ip: str) -> TokenState | None:
        return self._tokens.get(ip)

    def _decode_exp(self, token: str) -> float | None:
        """Decode JWT exp claim without signature verification."""
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"],
            )
            exp = payload.get("exp")
            if exp is not None:
                return float(exp)
        except (jwt.DecodeError, jwt.InvalidTokenError, KeyError, ValueError):
            pass
        return None

    def authenticate(self, ip: str, endpoints: APEndpoints) -> str:
        """Authenticate (or re-authenticate) with an AP. Returns the token."""
        result = self._login_service.login(endpoints)
        if not result.success:
            state = self._tokens.get(ip, TokenState())
            state.consecutive_failures += 1
            self._tokens[ip] = state
            if state.consecutive_failures >= MAX_REAUTH_ATTEMPTS:
                raise TokenRefreshExhaustedError(ip, state.consecutive_failures)
            raise TokenRefreshExhaustedError(ip, state.consecutive_failures)

        now = time.time()
        exp = self._decode_exp(result.token)

        self._tokens[ip] = TokenState(
            token=result.token,
            device_id=result.device_id,
            issued_at=now,
            expires_at=exp,
            consecutive_failures=0,
        )
        endpoints.client.token = result.token
        return result.token

    def ensure_token(self, ip: str, endpoints: APEndpoints) -> str:
        """Return a valid token, proactively refreshing if near expiry."""
        state = self._tokens.get(ip)

        if state is None or not state.token:
            return self.authenticate(ip, endpoints)

        # Proactive refresh based on JWT exp
        if state.expires_at is not None:
            if time.time() >= state.expires_at - PROACTIVE_SKEW_SECONDS:
                return self.authenticate(ip, endpoints)

        endpoints.client.token = state.token
        return state.token

    def handle_auth_error(self, ip: str, endpoints: APEndpoints) -> str:
        """Handle 401/403 by re-authenticating. Called reactively."""
        state = self._tokens.get(ip, TokenState())
        state.consecutive_failures += 1
        self._tokens[ip] = state

        if state.consecutive_failures >= MAX_REAUTH_ATTEMPTS:
            raise TokenRefreshExhaustedError(ip, state.consecutive_failures)

        result = self._login_service.login(endpoints)
        if not result.success:
            state.consecutive_failures += 1
            if state.consecutive_failures >= MAX_REAUTH_ATTEMPTS:
                raise TokenRefreshExhaustedError(ip, state.consecutive_failures)
            raise TokenRefreshExhaustedError(ip, state.consecutive_failures)

        now = time.time()
        exp = self._decode_exp(result.token)
        self._tokens[ip] = TokenState(
            token=result.token,
            device_id=result.device_id,
            issued_at=now,
            expires_at=exp,
            consecutive_failures=0,
        )
        endpoints.client.token = result.token
        return result.token

    def reset_failures(self, ip: str) -> None:
        """Reset consecutive failure count after a successful API call."""
        state = self._tokens.get(ip)
        if state:
            state.consecutive_failures = 0

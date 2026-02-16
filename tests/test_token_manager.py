"""Tests for JWT token lifecycle management."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import jwt
import pytest

from wfm.api.exceptions import TokenRefreshExhaustedError
from wfm.auth.login import LoginResult, LoginService
from wfm.auth.token_manager import MAX_REAUTH_ATTEMPTS, TokenManager


def _make_jwt(exp: float | None = None, extra: dict | None = None) -> str:
    """Create a JWT token with optional exp claim."""
    payload: dict = extra or {}
    if exp is not None:
        payload["exp"] = exp
    return jwt.encode(payload, "secret", algorithm="HS256")


@pytest.fixture
def login_service():
    return LoginService("admin", "password")


@pytest.fixture
def token_manager(login_service):
    return TokenManager(login_service)


@pytest.fixture
def mock_endpoints():
    return MagicMock()


class TestTokenManager:
    def test_authenticate_success(self, token_manager, login_service) -> None:
        exp_time = time.time() + 600
        token = _make_jwt(exp=exp_time)

        endpoints = MagicMock()
        login_service.login = MagicMock(
            return_value=LoginResult(success=True, token=token, device_id="AA:BB:CC:DD:EE:FF")
        )

        result = token_manager.authenticate("192.168.1.1", endpoints)
        assert result == token

        state = token_manager.get_state("192.168.1.1")
        assert state is not None
        assert state.token == token
        assert state.device_id == "AA:BB:CC:DD:EE:FF"
        assert state.expires_at is not None
        assert abs(state.expires_at - exp_time) < 2

    def test_authenticate_failure_increments_counter(self, token_manager, login_service) -> None:
        endpoints = MagicMock()
        login_service.login = MagicMock(
            return_value=LoginResult(success=False, message="bad password")
        )

        with pytest.raises(TokenRefreshExhaustedError):
            token_manager.authenticate("192.168.1.1", endpoints)

    def test_ensure_token_proactive_refresh(self, token_manager, login_service) -> None:
        """Token near expiry should trigger proactive refresh."""
        # First, set up an expired-soon token
        soon_exp = time.time() + 30  # < PROACTIVE_SKEW_SECONDS
        old_token = _make_jwt(exp=soon_exp)
        new_token = _make_jwt(exp=time.time() + 600)

        endpoints = MagicMock()
        call_count = 0

        def mock_login(ep):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LoginResult(success=True, token=old_token, device_id="dev1")
            return LoginResult(success=True, token=new_token, device_id="dev1")

        login_service.login = mock_login

        # First call: authenticate
        token_manager.ensure_token("192.168.1.1", endpoints)
        assert token_manager.get_state("192.168.1.1").token == old_token

        # Second call: should proactively refresh since exp is within skew
        token_manager.ensure_token("192.168.1.1", endpoints)
        assert token_manager.get_state("192.168.1.1").token == new_token

    def test_ensure_token_no_refresh_when_valid(self, token_manager, login_service) -> None:
        """Token well before expiry should not trigger refresh."""
        far_exp = time.time() + 3600  # 1 hour
        token = _make_jwt(exp=far_exp)

        endpoints = MagicMock()
        login_service.login = MagicMock(
            return_value=LoginResult(success=True, token=token, device_id="dev1")
        )

        token_manager.ensure_token("192.168.1.1", endpoints)
        assert login_service.login.call_count == 1

        # Second call should NOT re-login
        token_manager.ensure_token("192.168.1.1", endpoints)
        assert login_service.login.call_count == 1

    def test_jwt_without_exp(self, token_manager, login_service) -> None:
        """Token without exp claim should still work (no proactive refresh)."""
        token = _make_jwt()  # No exp

        endpoints = MagicMock()
        login_service.login = MagicMock(
            return_value=LoginResult(success=True, token=token, device_id="dev1")
        )

        token_manager.authenticate("192.168.1.1", endpoints)
        state = token_manager.get_state("192.168.1.1")
        assert state.expires_at is None
        assert state.token == token

    def test_handle_auth_error_retries(self, token_manager, login_service) -> None:
        """handle_auth_error should re-authenticate on 401."""
        new_token = _make_jwt(exp=time.time() + 600)
        endpoints = MagicMock()
        login_service.login = MagicMock(
            return_value=LoginResult(success=True, token=new_token, device_id="dev1")
        )

        result = token_manager.handle_auth_error("192.168.1.1", endpoints)
        assert result == new_token

    def test_handle_auth_error_exhausted(self, token_manager, login_service) -> None:
        """After MAX_REAUTH_ATTEMPTS failures, should raise TokenRefreshExhaustedError."""
        endpoints = MagicMock()
        login_service.login = MagicMock(
            return_value=LoginResult(success=False, message="bad")
        )

        with pytest.raises(TokenRefreshExhaustedError):
            for _ in range(MAX_REAUTH_ATTEMPTS + 1):
                token_manager.handle_auth_error("192.168.1.1", endpoints)

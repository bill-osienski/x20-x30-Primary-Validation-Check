"""Tests for encrypted .env manager."""

from __future__ import annotations

from pathlib import Path

import pytest

from wfm.config.crypto import CryptoEngine
from wfm.config.env_manager import EnvManager


@pytest.fixture
def env_setup(tmp_path: Path):
    key_path = tmp_path / ".env.key"
    env_path = tmp_path / ".env"
    crypto = CryptoEngine(key_path)
    env = EnvManager(env_path, crypto)
    return env, env_path


class TestEnvManager:
    def test_set_and_save(self, env_setup) -> None:
        env, env_path = env_setup
        env.set_credentials("admin", "pass123", ["192.168.1.1", "192.168.1.2"])
        env.save()

        assert env_path.exists()
        content = env_path.read_text()
        # All values should be encrypted
        for line in content.strip().splitlines():
            key, _, value = line.partition("=")
            assert value.startswith("ENC:")

    def test_load_decrypts(self, env_setup) -> None:
        env, _ = env_setup
        env.set_credentials("admin", "s3cret!", ["10.0.0.1"])
        env.save()

        # Load into a fresh manager (same crypto)
        env.load()
        assert env.username == "admin"
        assert env.password == "s3cret!"
        assert env.ap_ips == ["10.0.0.1"]

    def test_multiple_ips(self, env_setup) -> None:
        env, _ = env_setup
        env.set_credentials("user", "pw", ["1.1.1.1", "2.2.2.2", "3.3.3.3"])
        env.save()
        env.load()
        assert env.ap_ips == ["1.1.1.1", "2.2.2.2", "3.3.3.3"]

    def test_is_configured(self, env_setup) -> None:
        env, _ = env_setup
        assert not env.is_configured()
        env.set_credentials("admin", "pw", ["1.1.1.1"])
        assert env.is_configured()

    def test_empty_file(self, env_setup) -> None:
        env, _ = env_setup
        env.load()
        assert env.username == ""
        assert env.password == ""
        assert env.ap_ips == []

    def test_file_permissions(self, env_setup) -> None:
        env, env_path = env_setup
        env.set_credentials("a", "b", ["1.2.3.4"])
        env.save()
        mode = env_path.stat().st_mode & 0o777
        assert mode == 0o600

    def test_round_trip_special_chars(self, env_setup) -> None:
        env, _ = env_setup
        env.set_credentials("admin@host", "p@$$w0rd!#%", ["192.168.1.100"])
        env.save()
        env.load()
        assert env.username == "admin@host"
        assert env.password == "p@$$w0rd!#%"

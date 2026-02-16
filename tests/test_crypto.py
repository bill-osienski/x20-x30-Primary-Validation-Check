"""Tests for AES-256-GCM crypto engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from wfm.config.crypto import CryptoEngine


@pytest.fixture
def key_path(tmp_path: Path) -> Path:
    return tmp_path / ".env.key"


@pytest.fixture
def engine(key_path: Path) -> CryptoEngine:
    return CryptoEngine(key_path)


class TestCryptoEngine:
    def test_key_auto_generated(self, engine: CryptoEngine, key_path: Path) -> None:
        """Key file should be created on first encrypt."""
        engine.encrypt("hello")
        assert key_path.exists()

    def test_key_file_permissions(self, engine: CryptoEngine, key_path: Path) -> None:
        """Key file should be mode 0o600."""
        engine.encrypt("test")
        mode = key_path.stat().st_mode & 0o777
        assert mode == 0o600

    def test_round_trip(self, engine: CryptoEngine) -> None:
        """Encrypt then decrypt should return original plaintext."""
        for value in ["password123", "", "special chars: !@#$%^&*()", "unicode: ñ é ü"]:
            token = engine.encrypt(value)
            assert engine.decrypt(token) == value

    def test_unique_nonces(self, engine: CryptoEngine) -> None:
        """Each encryption of the same value should produce different ciphertext."""
        tokens = {engine.encrypt("same") for _ in range(10)}
        assert len(tokens) == 10

    def test_existing_key_reused(self, key_path: Path) -> None:
        """A second engine with the same key path should decrypt the first engine's data."""
        engine1 = CryptoEngine(key_path)
        token = engine1.encrypt("secret")

        engine2 = CryptoEngine(key_path)
        assert engine2.decrypt(token) == "secret"

    def test_wrong_key_fails(self, tmp_path: Path) -> None:
        """Decryption with a different key should fail."""
        engine1 = CryptoEngine(tmp_path / "key1")
        token = engine1.encrypt("secret")

        engine2 = CryptoEngine(tmp_path / "key2")
        with pytest.raises(Exception):
            engine2.decrypt(token)

    def test_tampered_ciphertext_fails(self, engine: CryptoEngine) -> None:
        """Modifying the ciphertext should fail GCM authentication."""
        import base64

        token = engine.encrypt("original")
        raw = bytearray(base64.b64decode(token))
        raw[-1] ^= 0xFF  # Flip last byte
        tampered = base64.b64encode(bytes(raw)).decode()
        with pytest.raises(Exception):
            engine.decrypt(tampered)

"""AES-256-GCM encryption engine for credential storage."""

from __future__ import annotations

import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_SIZE = 12  # 96-bit nonce per NIST recommendation


class CryptoEngine:
    """Manages AES-256-GCM encryption/decryption with file-backed key."""

    def __init__(self, key_path: Path) -> None:
        self._key_path = key_path
        self._aesgcm: AESGCM | None = None

    @property
    def key_path(self) -> Path:
        return self._key_path

    def _load_or_generate_key(self) -> bytes:
        """Load existing key or generate a new one."""
        if self._key_path.exists():
            encoded = self._key_path.read_text().strip()
            return base64.b64decode(encoded)
        key = AESGCM.generate_key(bit_length=256)
        self._key_path.parent.mkdir(parents=True, exist_ok=True)
        self._key_path.write_text(base64.b64encode(key).decode())
        self._key_path.chmod(0o600)
        return key

    def _get_aesgcm(self) -> AESGCM:
        if self._aesgcm is None:
            key = self._load_or_generate_key()
            self._aesgcm = AESGCM(key)
        return self._aesgcm

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string value. Returns base64(nonce + ciphertext)."""
        aesgcm = self._get_aesgcm()
        nonce = os.urandom(NONCE_SIZE)
        ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ct).decode()

    def decrypt(self, token: str) -> str:
        """Decrypt a base64(nonce + ciphertext) token back to plaintext."""
        aesgcm = self._get_aesgcm()
        raw = base64.b64decode(token)
        nonce = raw[:NONCE_SIZE]
        ct = raw[NONCE_SIZE:]
        return aesgcm.decrypt(nonce, ct, None).decode()

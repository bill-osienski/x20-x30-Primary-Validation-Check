"""Encrypted .env file manager."""

from __future__ import annotations

from pathlib import Path

from wfm.config.crypto import CryptoEngine

ENC_PREFIX = "ENC:"


class EnvManager:
    """Load and save .env files with transparent AES-256-GCM encryption."""

    def __init__(self, env_path: Path, crypto: CryptoEngine) -> None:
        self._env_path = env_path
        self._crypto = crypto
        self._data: dict[str, str] = {}

    @property
    def env_path(self) -> Path:
        return self._env_path

    @property
    def username(self) -> str:
        return self._data.get("USERNAME", "")

    @property
    def password(self) -> str:
        return self._data.get("PASSWORD", "")

    @property
    def ap_ips(self) -> list[str]:
        raw = self._data.get("AP_IPS", "")
        if not raw:
            return []
        return [ip.strip() for ip in raw.split(",") if ip.strip()]

    def load(self) -> None:
        """Load and decrypt .env file into memory."""
        self._data.clear()
        if not self._env_path.exists():
            return
        for line in self._env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if value.startswith(ENC_PREFIX):
                value = self._crypto.decrypt(value[len(ENC_PREFIX) :])
            self._data[key] = value

    def save(self) -> None:
        """Encrypt and write current data to .env file."""
        lines: list[str] = []
        for key, value in self._data.items():
            encrypted = self._crypto.encrypt(value)
            lines.append(f"{key}={ENC_PREFIX}{encrypted}")
        self._env_path.write_text("\n".join(lines) + "\n")
        self._env_path.chmod(0o600)

    def set_credentials(self, username: str, password: str, ap_ips: list[str]) -> None:
        """Set credentials in memory (call save() to persist)."""
        self._data["USERNAME"] = username
        self._data["PASSWORD"] = password
        self._data["AP_IPS"] = ",".join(ap_ips)

    def is_configured(self) -> bool:
        """Check if all required fields are present and non-empty."""
        return bool(self.username and self.password and self.ap_ips)

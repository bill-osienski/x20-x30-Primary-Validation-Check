"""Compatibility gate: block/allow operations based on SSID mismatch state."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from wfm.api.exceptions import GateBlockedError
from wfm.ssid.constants import GATED_OPERATIONS


class CompatibilityState(StrEnum):
    OK = "OK"
    PRIMARY_SSID_MISMATCH = "PRIMARY_SSID_MISMATCH"
    INDEX_COLLISION = "INDEX_COLLISION"
    UNKNOWN = "UNKNOWN"


@dataclass
class APGateState:
    """Per-AP gate state."""

    compatibility_state: CompatibilityState = CompatibilityState.UNKNOWN
    detected_at: str = ""
    last_checked_at: str = ""
    primary_ssid: str = ""
    details: str = ""
    index_to_ssid: dict[int, str] = field(default_factory=dict)


class CompatibilityGate:
    """Manages per-AP compatibility state with persistent JSON storage."""

    def __init__(self, state_path: Path) -> None:
        self._state_path = state_path
        self._states: dict[str, APGateState] = {}
        self._load()

    def _load(self) -> None:
        """Load persisted state from disk."""
        if not self._state_path.exists():
            return
        try:
            raw = json.loads(self._state_path.read_text())
            for ip, data in raw.items():
                idx_map = data.get("index_to_ssid", {})
                # JSON keys are always strings, convert back to int
                idx_map = {int(k): v for k, v in idx_map.items()}
                raw_state = data.get("compatibility_state", "UNKNOWN")
                self._states[ip] = APGateState(
                    compatibility_state=CompatibilityState(raw_state),
                    detected_at=data.get("detected_at", ""),
                    last_checked_at=data.get("last_checked_at", ""),
                    primary_ssid=data.get("primary_ssid", ""),
                    details=data.get("details", ""),
                    index_to_ssid=idx_map,
                )
        except (json.JSONDecodeError, KeyError, ValueError):
            self._states = {}

    def save(self) -> None:
        """Persist current state to disk."""
        raw: dict[str, dict] = {}
        for ip, state in self._states.items():
            d = asdict(state)
            d["compatibility_state"] = state.compatibility_state.value
            # Convert int keys to string for JSON
            d["index_to_ssid"] = {str(k): v for k, v in state.index_to_ssid.items()}
            raw[ip] = d
        self._state_path.write_text(json.dumps(raw, indent=2) + "\n")

    def get_state(self, ip: str) -> APGateState:
        return self._states.get(ip, APGateState())

    def update_state(
        self,
        ip: str,
        *,
        state: CompatibilityState,
        primary_ssid: str = "",
        details: str = "",
        index_to_ssid: dict[int, str] | None = None,
    ) -> None:
        """Update the gate state for an AP and persist."""
        now = datetime.now(UTC).isoformat()
        existing = self._states.get(ip)

        # Preserve detected_at if state hasn't changed
        detected_at = now
        if existing and existing.compatibility_state == state and existing.detected_at:
            detected_at = existing.detected_at

        self._states[ip] = APGateState(
            compatibility_state=state,
            detected_at=detected_at,
            last_checked_at=now,
            primary_ssid=primary_ssid,
            details=details,
            index_to_ssid=index_to_ssid or {},
        )
        self.save()

    def check_allowed(self, ip: str, operation: str) -> None:
        """Raise GateBlockedError if operation is gated and state is not OK."""
        if operation not in GATED_OPERATIONS:
            return
        ap_state = self.get_state(ip)
        if ap_state.compatibility_state != CompatibilityState.OK:
            raise GateBlockedError(operation, ip, ap_state.compatibility_state.value)

    @property
    def all_states(self) -> dict[str, APGateState]:
        return dict(self._states)

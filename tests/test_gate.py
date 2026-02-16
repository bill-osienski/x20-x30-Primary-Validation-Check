"""Tests for the compatibility gate and persisted state."""

from __future__ import annotations

from pathlib import Path

import pytest

from wfm.api.exceptions import GateBlockedError
from wfm.ssid.gate import CompatibilityGate, CompatibilityState


@pytest.fixture
def state_path(tmp_path: Path) -> Path:
    return tmp_path / ".wfm_state.json"


@pytest.fixture
def gate(state_path: Path) -> CompatibilityGate:
    return CompatibilityGate(state_path)


class TestCompatibilityGate:
    def test_initial_state_unknown(self, gate: CompatibilityGate) -> None:
        state = gate.get_state("192.168.1.1")
        assert state.compatibility_state == CompatibilityState.UNKNOWN

    def test_update_to_ok(self, gate: CompatibilityGate) -> None:
        gate.update_state(
            "192.168.1.1",
            state=CompatibilityState.OK,
            primary_ssid="MyNet",
            index_to_ssid={0: "MyNet", 50: "MyNet"},
        )
        state = gate.get_state("192.168.1.1")
        assert state.compatibility_state == CompatibilityState.OK
        assert state.primary_ssid == "MyNet"

    def test_update_to_mismatch(self, gate: CompatibilityGate) -> None:
        gate.update_state(
            "10.0.0.1",
            state=CompatibilityState.PRIMARY_SSID_MISMATCH,
            details="index 0 → 'A', index 50 → 'B'",
            index_to_ssid={0: "A", 50: "B"},
        )
        state = gate.get_state("10.0.0.1")
        assert state.compatibility_state == CompatibilityState.PRIMARY_SSID_MISMATCH
        assert state.details == "index 0 → 'A', index 50 → 'B'"

    def test_gated_operation_blocked(self, gate: CompatibilityGate) -> None:
        gate.update_state("1.1.1.1", state=CompatibilityState.PRIMARY_SSID_MISMATCH)
        with pytest.raises(GateBlockedError):
            gate.check_allowed("1.1.1.1", "import_ssids")

    def test_ungated_operation_allowed(self, gate: CompatibilityGate) -> None:
        gate.update_state("1.1.1.1", state=CompatibilityState.PRIMARY_SSID_MISMATCH)
        # Should not raise
        gate.check_allowed("1.1.1.1", "status")

    def test_ok_state_allows_gated(self, gate: CompatibilityGate) -> None:
        gate.update_state("1.1.1.1", state=CompatibilityState.OK)
        # Should not raise
        gate.check_allowed("1.1.1.1", "import_ssids")

    def test_unknown_state_blocks_gated(self, gate: CompatibilityGate) -> None:
        """UNKNOWN state should block gated operations."""
        with pytest.raises(GateBlockedError):
            gate.check_allowed("1.1.1.1", "sync_ssids")


class TestGatePersistence:
    def test_save_and_reload(self, state_path: Path) -> None:
        gate1 = CompatibilityGate(state_path)
        gate1.update_state(
            "192.168.1.1",
            state=CompatibilityState.OK,
            primary_ssid="MyNet",
            index_to_ssid={0: "MyNet", 50: "MyNet"},
        )
        gate1.update_state(
            "192.168.1.2",
            state=CompatibilityState.PRIMARY_SSID_MISMATCH,
            details="mismatch details",
            index_to_ssid={0: "A", 50: "B"},
        )

        # Load from same path
        gate2 = CompatibilityGate(state_path)
        s1 = gate2.get_state("192.168.1.1")
        assert s1.compatibility_state == CompatibilityState.OK
        assert s1.primary_ssid == "MyNet"
        assert s1.index_to_ssid == {0: "MyNet", 50: "MyNet"}

        s2 = gate2.get_state("192.168.1.2")
        assert s2.compatibility_state == CompatibilityState.PRIMARY_SSID_MISMATCH

    def test_detected_at_preserved_on_same_state(self, state_path: Path) -> None:
        gate = CompatibilityGate(state_path)
        gate.update_state("1.1.1.1", state=CompatibilityState.PRIMARY_SSID_MISMATCH)
        first_detected = gate.get_state("1.1.1.1").detected_at

        gate.update_state("1.1.1.1", state=CompatibilityState.PRIMARY_SSID_MISMATCH)
        assert gate.get_state("1.1.1.1").detected_at == first_detected

    def test_detected_at_updated_on_state_change(self, state_path: Path) -> None:
        gate = CompatibilityGate(state_path)
        gate.update_state("1.1.1.1", state=CompatibilityState.PRIMARY_SSID_MISMATCH)
        mismatch_detected = gate.get_state("1.1.1.1").detected_at

        gate.update_state("1.1.1.1", state=CompatibilityState.OK)
        assert gate.get_state("1.1.1.1").detected_at != mismatch_detected

    def test_corrupted_file_handled(self, state_path: Path) -> None:
        state_path.write_text("not valid json!!!")
        gate = CompatibilityGate(state_path)
        # Should gracefully handle corruption
        assert gate.get_state("1.1.1.1").compatibility_state == CompatibilityState.UNKNOWN

    def test_all_states(self, gate: CompatibilityGate) -> None:
        gate.update_state("a", state=CompatibilityState.OK)
        gate.update_state("b", state=CompatibilityState.PRIMARY_SSID_MISMATCH)
        states = gate.all_states
        assert len(states) == 2
        assert "a" in states
        assert "b" in states

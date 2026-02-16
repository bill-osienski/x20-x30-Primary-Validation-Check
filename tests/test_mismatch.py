"""Tests for the primary SSID mismatch detection algorithm."""

from __future__ import annotations

from wfm.api.models import WlanStatus
from wfm.ssid.mismatch import check_primary_ssid_mismatch


class TestX20Mismatch:
    """Mismatch detection for x20 (primary indices: {0, 50})."""

    def test_matching_separate_entries(self, matching_x20_networks, x20_profile) -> None:
        result = check_primary_ssid_mismatch(matching_x20_networks, x20_profile)
        assert result.is_ok
        assert result.primary_ssid == "MyNetwork"

    def test_matching_combined_entry(self, matching_x20_combined, x20_profile) -> None:
        result = check_primary_ssid_mismatch(matching_x20_combined, x20_profile)
        assert result.is_ok
        assert result.primary_ssid == "MyNetwork"

    def test_mismatch(self, mismatched_x20_networks, x20_profile) -> None:
        result = check_primary_ssid_mismatch(mismatched_x20_networks, x20_profile)
        assert not result.is_ok
        assert not result.has_collision
        assert "mismatch" in result.details.lower() or "Mismatch" in result.details

    def test_missing_index(self, x20_profile) -> None:
        networks = [
            WlanStatus(networkIndex=[0], ssid="MyNet", enabled=True),
        ]
        result = check_primary_ssid_mismatch(networks, x20_profile)
        assert not result.is_ok
        assert "missing" in result.details.lower() or "Missing" in result.details

    def test_duplicate_entries_union(self, x20_profile) -> None:
        """Duplicate entries for same SSID should be unioned."""
        networks = [
            WlanStatus(networkIndex=[0], ssid="MyNet", enabled=True, interface="2.4GHZ"),
            WlanStatus(networkIndex=[0], ssid="MyNet", enabled=True, interface="2.4GHZ"),
            WlanStatus(networkIndex=[50], ssid="MyNet", enabled=True, interface="5GHZ"),
        ]
        result = check_primary_ssid_mismatch(networks, x20_profile)
        assert result.is_ok

    def test_with_non_primary_indices(self, x20_profile) -> None:
        """Non-primary indices should not affect the result."""
        networks = [
            WlanStatus(networkIndex=[0, 1], ssid="MyNet", enabled=True),
            WlanStatus(networkIndex=[50, 51], ssid="MyNet", enabled=True),
            WlanStatus(networkIndex=[2], ssid="OtherNet", enabled=True),
        ]
        result = check_primary_ssid_mismatch(networks, x20_profile)
        assert result.is_ok

    def test_disabled_ssid_still_checked(self, x20_profile) -> None:
        """Even disabled SSIDs must match on primary indices."""
        networks = [
            WlanStatus(networkIndex=[0], ssid="MyNet", enabled=False, interface="2.4GHZ"),
            WlanStatus(networkIndex=[50], ssid="DifferentNet", enabled=False, interface="5GHZ"),
        ]
        result = check_primary_ssid_mismatch(networks, x20_profile)
        assert not result.is_ok


class TestX30Mismatch:
    """Mismatch detection for x30 (primary indices: {0, 50, 70})."""

    def test_matching(self, matching_x30_networks, x30_profile) -> None:
        result = check_primary_ssid_mismatch(matching_x30_networks, x30_profile)
        assert result.is_ok
        assert result.primary_ssid == "MyNetwork"

    def test_6ghz_mismatch(self, mismatched_x30_networks, x30_profile) -> None:
        result = check_primary_ssid_mismatch(mismatched_x30_networks, x30_profile)
        assert not result.is_ok
        assert 70 in result.index_to_ssid

    def test_missing_6ghz(self, x30_profile) -> None:
        networks = [
            WlanStatus(networkIndex=[0], ssid="MyNet", enabled=True),
            WlanStatus(networkIndex=[50], ssid="MyNet", enabled=True),
        ]
        result = check_primary_ssid_mismatch(networks, x30_profile)
        assert not result.is_ok
        assert "missing" in result.details.lower() or "Missing" in result.details


class TestIndexCollision:
    """Index collision guard: same index claimed by multiple SSIDs."""

    def test_collision_detected(self, x20_profile) -> None:
        """Two different SSIDs both claiming index 0."""
        networks = [
            WlanStatus(networkIndex=[0], ssid="NetA", enabled=True),
            WlanStatus(networkIndex=[0], ssid="NetB", enabled=True),
            WlanStatus(networkIndex=[50], ssid="NetA", enabled=True),
        ]
        result = check_primary_ssid_mismatch(networks, x20_profile)
        assert not result.is_ok
        assert result.has_collision
        assert "collision" in result.details.lower() or "Collision" in result.details

    def test_no_collision_same_ssid(self, x20_profile) -> None:
        """Same SSID on same index = no collision."""
        networks = [
            WlanStatus(networkIndex=[0], ssid="MyNet", enabled=True, interface="2.4GHZ"),
            WlanStatus(networkIndex=[0], ssid="MyNet", enabled=True, interface="2.4GHZ"),
            WlanStatus(networkIndex=[50], ssid="MyNet", enabled=True, interface="5GHZ"),
        ]
        result = check_primary_ssid_mismatch(networks, x20_profile)
        assert result.is_ok
        assert not result.has_collision


class TestEdgeCases:
    """Edge cases for the mismatch algorithm."""

    def test_empty_networks(self, x20_profile) -> None:
        result = check_primary_ssid_mismatch([], x20_profile)
        assert not result.is_ok

    def test_no_ssid_name(self, x20_profile) -> None:
        """Entries with empty SSID names should be skipped."""
        networks = [
            WlanStatus(networkIndex=[0], ssid="", enabled=True),
            WlanStatus(networkIndex=[50], ssid="MyNet", enabled=True),
        ]
        result = check_primary_ssid_mismatch(networks, x20_profile)
        assert not result.is_ok

"""Device type definitions and profiles for x20/x30 access points."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DeviceType(Enum):
    """SnapOne Access Point hardware generation."""

    X20 = "x20"  # Wi-Fi 6
    X30 = "x30"  # Wi-Fi 7


@dataclass(frozen=True)
class DeviceProfile:
    """Hardware-specific constants for an AP generation."""

    device_type: DeviceType
    primary_indices: frozenset[int]
    radio_count: int
    bands: tuple[str, ...]
    guest_index_start: int

    @property
    def label(self) -> str:
        return self.device_type.value.upper()


X20_PROFILE = DeviceProfile(
    device_type=DeviceType.X20,
    primary_indices=frozenset({0, 50}),
    radio_count=2,
    bands=("2.4GHz", "5GHz"),
    guest_index_start=100,
)

X30_PROFILE = DeviceProfile(
    device_type=DeviceType.X30,
    primary_indices=frozenset({0, 50, 70}),
    radio_count=3,
    bands=("2.4GHz", "5GHz", "6GHz"),
    guest_index_start=100,
)

PROFILES: dict[DeviceType, DeviceProfile] = {
    DeviceType.X20: X20_PROFILE,
    DeviceType.X30: X30_PROFILE,
}

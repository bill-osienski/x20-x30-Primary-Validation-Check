"""In-memory device registry tracking known APs and their profiles."""

from __future__ import annotations

from dataclasses import dataclass

from wfm.devices.types import DeviceProfile


@dataclass
class RegisteredDevice:
    """A known AP with its detected profile."""

    ip: str
    device_id: str
    profile: DeviceProfile


class DeviceRegistry:
    """Registry of detected APs, keyed by IP."""

    def __init__(self) -> None:
        self._devices: dict[str, RegisteredDevice] = {}

    def register(self, ip: str, device_id: str, profile: DeviceProfile) -> RegisteredDevice:
        dev = RegisteredDevice(ip=ip, device_id=device_id, profile=profile)
        self._devices[ip] = dev
        return dev

    def get(self, ip: str) -> RegisteredDevice | None:
        return self._devices.get(ip)

    def all_devices(self) -> list[RegisteredDevice]:
        return list(self._devices.values())

    def __len__(self) -> int:
        return len(self._devices)

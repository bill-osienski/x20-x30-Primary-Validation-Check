"""Auto-detect AP hardware type (x20 vs x30) via radiostatus response shape."""

from __future__ import annotations

from typing import Any

from wfm.api.exceptions import DeviceDetectionError
from wfm.devices.types import PROFILES, DeviceProfile, DeviceType


def detect_device_type(ip: str, radiostatus: dict[str, Any]) -> DeviceProfile:
    """Determine device type from the radiostatus response shape.

    Both x20 and x30 use named fields (radio0, radio1, ...).
    - x30 (Wi-Fi 7): has radio0, radio1, radio2 (3 radios, includes 6GHz)
    - x20 (Wi-Fi 6): has radio0, radio1 only (2 radios, no 6GHz)
    Fallback: x20 spec may also return `radios: [...]` array.
    """
    has_radio0 = "radio0" in radiostatus
    has_radio1 = "radio1" in radiostatus
    has_radio2 = "radio2" in radiostatus

    if has_radio0 and has_radio1 and has_radio2:
        return PROFILES[DeviceType.X30]

    if has_radio0 and has_radio1 and not has_radio2:
        return PROFILES[DeviceType.X20]

    # Fallback: x20 spec defines `radios` array shape
    if "radios" in radiostatus and isinstance(radiostatus["radios"], list):
        return PROFILES[DeviceType.X20]

    raise DeviceDetectionError(
        ip,
        detail=(
            "Unexpected radiostatus shape. "
            f"Keys found: {sorted(radiostatus.keys())}. "
            "Expected 'radio0'/'radio1' (x20) or 'radio0'/'radio1'/'radio2' (x30)."
        ),
    )

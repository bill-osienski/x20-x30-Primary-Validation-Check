"""Primary SSID mismatch detection algorithm."""

from __future__ import annotations

from dataclasses import dataclass, field

from wfm.api.models import WlanStatus
from wfm.devices.types import DeviceProfile


@dataclass(frozen=True)
class MismatchResult:
    """Result of running the mismatch detection algorithm."""

    is_ok: bool
    primary_ssid: str | None = None
    index_to_ssid: dict[int, str] = field(default_factory=dict)
    details: str = ""
    has_collision: bool = False


def check_primary_ssid_mismatch(
    networks: list[WlanStatus],
    profile: DeviceProfile,
) -> MismatchResult:
    """Detect whether all primary indices share the same SSID.

    Algorithm:
      1. Build ssid_to_indices: union of networkIndex[] per SSID name
      2. Build index_to_ssid: map primary indices → SSID name
      3. INDEX COLLISION GUARD: if any primary index appears under two different
         SSID names → block with specific error
      4. PASS if exactly one SSID's index set ⊇ required_primary
      5. FAIL otherwise with diagnostic mapping
    """
    required_primary = profile.primary_indices

    # 1. Build ssid → indices map (union by SSID name across entries)
    ssid_to_indices: dict[str, set[int]] = {}
    for net in networks:
        if not net.ssid:
            continue
        if net.ssid not in ssid_to_indices:
            ssid_to_indices[net.ssid] = set()
        ssid_to_indices[net.ssid].update(net.networkIndex)

    # 2. Build index → ssid for primary indices only
    index_to_ssid: dict[int, str] = {}
    collisions: dict[int, list[str]] = {}

    for ssid, indices in ssid_to_indices.items():
        for idx in indices:
            if idx in required_primary:
                if idx in index_to_ssid:
                    # 3. Index collision: same primary index claimed by multiple SSIDs
                    if idx not in collisions:
                        collisions[idx] = [index_to_ssid[idx]]
                    collisions[idx].append(ssid)
                else:
                    index_to_ssid[idx] = ssid

    # 3. Check for index collisions
    if collisions:
        parts = []
        for idx, ssids in sorted(collisions.items()):
            parts.append(f"index {idx} claimed by: {', '.join(sorted(ssids))}")
        detail = "Index collision — " + "; ".join(parts)
        return MismatchResult(
            is_ok=False,
            index_to_ssid=index_to_ssid,
            details=detail,
            has_collision=True,
        )

    # Check for missing primary indices
    missing = required_primary - set(index_to_ssid.keys())
    if missing:
        detail = f"Missing primary indices: {sorted(missing)}"
        return MismatchResult(
            is_ok=False,
            index_to_ssid=index_to_ssid,
            details=detail,
        )

    # 4. Check if one SSID covers all primary indices
    unique_ssids = set(index_to_ssid.values())
    if len(unique_ssids) == 1:
        return MismatchResult(
            is_ok=True,
            primary_ssid=unique_ssids.pop(),
            index_to_ssid=index_to_ssid,
        )

    # 5. Multiple SSIDs across primary indices → mismatch
    parts = []
    for idx in sorted(index_to_ssid.keys()):
        parts.append(f"index {idx} → '{index_to_ssid[idx]}'")
    detail = "Primary SSID mismatch: " + ", ".join(parts)
    return MismatchResult(
        is_ok=False,
        index_to_ssid=index_to_ssid,
        details=detail,
    )

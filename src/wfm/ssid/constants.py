"""SSID-related constants: primary indices, band mappings."""

from __future__ import annotations

# Maps primary network index → radio band label
INDEX_TO_BAND: dict[int, str] = {
    0: "2.4GHz",
    50: "5GHz",
    70: "6GHz",  # x30 only
}

# Operations that require a passing mismatch check (gated)
GATED_OPERATIONS: frozenset[str] = frozenset({
    "import_ssids",
    "sync_ssids",
    "apply_ssid_changes",
    "push_ssid",
    "reconcile",
})

# Operations that are always allowed regardless of gate state
UNGATED_OPERATIONS: frozenset[str] = frozenset({
    "status",
    "clients",
    "radios",
    "recheck",
    "device_info",
})

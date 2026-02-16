"""Shared fixtures for WFM tests."""

from __future__ import annotations

import pytest

from wfm.api.models import WlanStatus
from wfm.devices.types import X20_PROFILE, X30_PROFILE


@pytest.fixture
def x20_profile():
    return X20_PROFILE


@pytest.fixture
def x30_profile():
    return X30_PROFILE


@pytest.fixture
def matching_x20_networks():
    """Two WlanStatus entries for x20 where primary SSID matches (same SSID on 0 and 50)."""
    return [
        WlanStatus(networkIndex=[0], ssid="MyNetwork", enabled=True, interface="2.4GHZ"),
        WlanStatus(networkIndex=[50], ssid="MyNetwork", enabled=True, interface="5GHZ"),
    ]


@pytest.fixture
def matching_x20_combined():
    """Single WlanStatus entry covering both x20 primary indices."""
    return [
        WlanStatus(networkIndex=[0, 50], ssid="MyNetwork", enabled=True, interface="BOTH"),
    ]


@pytest.fixture
def mismatched_x20_networks():
    """x20 networks with different SSIDs on primary indices."""
    return [
        WlanStatus(networkIndex=[0], ssid="NetworkA", enabled=True, interface="2.4GHZ"),
        WlanStatus(networkIndex=[50], ssid="NetworkB", enabled=True, interface="5GHZ"),
    ]


@pytest.fixture
def matching_x30_networks():
    """Three WlanStatus entries for x30 where primary SSID matches."""
    return [
        WlanStatus(networkIndex=[0], ssid="MyNetwork", enabled=True, interface="2.4GHZ"),
        WlanStatus(networkIndex=[50], ssid="MyNetwork", enabled=True, interface="5GHZ"),
        WlanStatus(networkIndex=[70], ssid="MyNetwork", enabled=True, interface="6GHZ"),
    ]


@pytest.fixture
def mismatched_x30_networks():
    """x30 networks with 6GHz on a different SSID."""
    return [
        WlanStatus(networkIndex=[0], ssid="MyNetwork", enabled=True, interface="2.4GHZ"),
        WlanStatus(networkIndex=[50], ssid="MyNetwork", enabled=True, interface="5GHZ"),
        WlanStatus(networkIndex=[70], ssid="OtherNet", enabled=True, interface="6GHZ"),
    ]


@pytest.fixture
def x20_radiostatus_response():
    """x20-style radiostatus response with named radio fields (no radio2)."""
    r0 = {
        "interface": "2.4GHZ", "enabled": True,
        "rx": 100, "tx": 200, "networks": 1, "clients": 2,
    }
    r1 = {
        "interface": "5GHZ", "enabled": True,
        "rx": 300, "tx": 400, "networks": 1, "clients": 3,
    }
    return {
        "radio0": r0,
        "radio1": r1,
        "deviceId": "AA:BB:CC:DD:EE:FF",
        "errCode": 0,
        "message": "OK",
    }


@pytest.fixture
def x30_radiostatus_response():
    """x30-style radiostatus response with named radio fields."""
    r0 = {
        "interface": "2.4GHZ", "enabled": True,
        "rx": 100, "tx": 200, "networks": 1, "clients": 1,
    }
    r1 = {
        "interface": "5GHZ", "enabled": True,
        "rx": 300, "tx": 400, "networks": 1, "clients": 2,
    }
    r2 = {
        "interface": "6GHZ", "enabled": True,
        "rx": 500, "tx": 600, "networks": 1, "clients": 0,
    }
    return {
        "radio0": r0,
        "radio1": r1,
        "radio2": r2,
        "deviceId": "11:22:33:44:55:66",
        "errCode": 0,
        "message": "OK",
    }

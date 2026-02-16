"""Pydantic v2 models matching AP API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

# --- Login ---


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginToken(BaseModel):
    token: str


class LoginResponse(BaseModel):
    login: LoginToken | None = None
    deviceId: str = ""  # noqa: N815
    errCode: int = 0  # noqa: N815
    message: str = ""


# --- Wireless Networks ---


class WlanStatus(BaseModel):
    """Single SSID entry from GET /v1/wireless/networks."""

    networkIndex: list[int]  # noqa: N815
    enabled: bool = True
    mac: str = ""
    ssid: str = ""
    interface: str = ""
    clients: int = 0
    rx: int = 0
    tx: int = 0


class GuestWlanStatus(BaseModel):
    """Guest SSID entry from GET /v1/wireless/networks."""

    networkIndex: int  # noqa: N815 — single int for guest (x20: 39/89, x30: 39/79/89)
    enabled: bool = True
    mac: str = ""
    ssid: str = ""
    interface: str = ""
    clients: int = 0
    rx: int = 0
    tx: int = 0


class NetworksResponse(BaseModel):
    """Response from GET /v1/wireless/networks."""

    Networks: list[WlanStatus] = Field(default_factory=list)
    guestNetworks: list[GuestWlanStatus] = Field(default_factory=list)  # noqa: N815
    deviceId: str = ""  # noqa: N815
    errCode: int = 0  # noqa: N815
    message: str = ""


# --- Radio Status ---


class RadioStatus(BaseModel):
    """Single radio status entry."""

    interface: str = ""
    enabled: bool = True
    rx: int = 0
    tx: int = 0
    networks: int = 0
    clients: int = 0


class RadioStatusArrayResponse(BaseModel):
    """x20 response: radios as array."""

    radios: list[RadioStatus] = Field(default_factory=list)
    deviceId: str = ""  # noqa: N815
    errCode: int = 0  # noqa: N815
    message: str = ""


class RadioStatusNamedResponse(BaseModel):
    """x30 response: radios as named fields (radio0, radio1, radio2)."""

    radio0: RadioStatus | None = None
    radio1: RadioStatus | None = None
    radio2: RadioStatus | None = None
    deviceId: str = ""  # noqa: N815
    errCode: int = 0  # noqa: N815
    message: str = ""


# --- Device Info ---


class DeviceInfo(BaseModel):
    serial_no: str = ""
    base_mac_address: str = ""
    fw_ver: str = ""
    fw_build_date: str = ""
    country_code: int = 0
    model_name: str = ""
    activePartition: str = ""  # noqa: N815


class DeviceInfoResponse(BaseModel):
    deviceInfo: DeviceInfo | None = None  # noqa: N815
    deviceId: str = ""  # noqa: N815
    errCode: int = 0  # noqa: N815
    message: str = ""


# --- System Apply ---


class ApplyResponse(BaseModel):
    deviceId: str = ""  # noqa: N815
    errCode: int = 0  # noqa: N815
    message: str = ""


# --- Generic Success ---


class SuccessResponse(BaseModel):
    deviceId: str = ""  # noqa: N815
    errCode: int = 0  # noqa: N815
    message: str = ""

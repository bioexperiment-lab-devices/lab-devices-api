from enum import StrEnum

from pydantic import BaseModel


class DeviceType(StrEnum):
    PUMP = "pump"
    DENSITOMETER = "densitometer"


class Direction(StrEnum):
    LEFT = "left"
    RIGHT = "right"


class DiscoveredDevice(BaseModel):
    device_type: DeviceType
    port: str

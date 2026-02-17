from datetime import datetime

from lab_devices.models.device import DeviceType, Direction, DiscoveredDevice
from lab_devices.models.events import InstantEvent, StateRecord


class TestStateRecord:
    def test_create_with_defaults(self) -> None:
        record = StateRecord(name="rotating")
        assert record.name == "rotating"
        assert record.params == {}
        assert isinstance(record.started_at, datetime)
        assert record.ended_at is None

    def test_create_with_params(self) -> None:
        record = StateRecord(
            name="rotating",
            params={"direction": "left", "speed": 5.0},
        )
        assert record.params["direction"] == "left"
        assert record.params["speed"] == 5.0

    def test_ended_at_can_be_set(self) -> None:
        record = StateRecord(name="rotating")
        now = datetime.now()
        record.ended_at = now
        assert record.ended_at == now


class TestInstantEvent:
    def test_create_with_defaults(self) -> None:
        event = InstantEvent(name="get_temperature")
        assert event.name == "get_temperature"
        assert event.params == {}
        assert isinstance(event.timestamp, datetime)

    def test_create_with_params(self) -> None:
        event = InstantEvent(
            name="get_temperature",
            params={"temperature_c": 23.5},
        )
        assert event.params["temperature_c"] == 23.5


class TestDeviceType:
    def test_pump_value(self) -> None:
        assert DeviceType.PUMP == "pump"

    def test_densitometer_value(self) -> None:
        assert DeviceType.DENSITOMETER == "densitometer"


class TestDirection:
    def test_left_value(self) -> None:
        assert Direction.LEFT == "left"

    def test_right_value(self) -> None:
        assert Direction.RIGHT == "right"


class TestDiscoveredDevice:
    def test_create(self) -> None:
        device = DiscoveredDevice(device_type=DeviceType.PUMP, port="/dev/ttyUSB0")
        assert device.device_type == DeviceType.PUMP
        assert device.port == "/dev/ttyUSB0"

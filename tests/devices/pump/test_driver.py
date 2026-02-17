from unittest.mock import AsyncMock

from lab_devices.core.history import DeviceHistory
from lab_devices.devices.pump.driver import PumpDriver
from lab_devices.devices.pump.protocol import PumpLegacyProtocol
from lab_devices.models.device import Direction


def make_pump() -> tuple[PumpDriver, AsyncMock]:
    connection = AsyncMock()
    connection.port = "/dev/ttyUSB0"
    protocol = PumpLegacyProtocol()
    history = DeviceHistory()
    driver = PumpDriver(connection=connection, protocol=protocol, history=history)
    return driver, connection


class TestPumpDriver:
    async def test_start_rotation_left(self) -> None:
        pump, conn = make_pump()
        await pump.start_rotation(speed=5, direction=Direction.LEFT)
        conn.send_command.assert_awaited_once_with(
            bytes([0x0B, 0x6F, 0x00, 0x05, 0x00])
        )

    async def test_start_rotation_right(self) -> None:
        pump, conn = make_pump()
        await pump.start_rotation(speed=10, direction=Direction.RIGHT)
        conn.send_command.assert_awaited_once_with(
            bytes([0x0C, 0x6F, 0x00, 0x0A, 0x00])
        )

    async def test_start_rotation_updates_state(self) -> None:
        pump, _ = make_pump()
        await pump.start_rotation(speed=5, direction=Direction.LEFT)
        state = pump.history.current_state()
        assert state is not None
        assert state.name == "rotating"
        assert state.params["direction"] == "left"
        assert state.params["speed"] == 5

    async def test_stop_rotation(self) -> None:
        pump, conn = make_pump()
        await pump.start_rotation(speed=5, direction=Direction.LEFT)
        await pump.stop_rotation()
        conn.send_command.assert_awaited_with(
            bytes([0x0B, 0x6F, 0x00, 0x00, 0x00])
        )

    async def test_stop_rotation_ends_state(self) -> None:
        pump, _ = make_pump()
        await pump.start_rotation(speed=5, direction=Direction.LEFT)
        await pump.stop_rotation()
        assert pump.history.current_state() is None

    async def test_set_rotation_speed(self) -> None:
        pump, conn = make_pump()
        await pump.set_rotation_speed(3)
        conn.send_command.assert_awaited_once_with(
            bytes([0x0A, 0x00, 0x00, 0x03, 0x00])
        )

    async def test_set_rotation_speed_records_event(self) -> None:
        pump, _ = make_pump()
        await pump.set_rotation_speed(3)
        events = pump.history.get_events("set_speed")
        assert len(events) == 1
        assert events[0].params["speed"] == 3

    async def test_pour_volume_left(self) -> None:
        pump, conn = make_pump()
        await pump.pour_volume(direction=Direction.LEFT, volume=50)
        conn.send_command.assert_awaited_once_with(
            bytes([0x10, 0x00, 0x00, 0x00, 0x32])
        )

    async def test_pour_volume_right(self) -> None:
        pump, conn = make_pump()
        await pump.pour_volume(direction=Direction.RIGHT, volume=100)
        conn.send_command.assert_awaited_once_with(
            bytes([0x11, 0x00, 0x00, 0x00, 0x64])
        )

    async def test_pour_volume_records_event(self) -> None:
        pump, _ = make_pump()
        await pump.set_rotation_speed(5)
        await pump.pour_volume(direction=Direction.LEFT, volume=50)
        events = pump.history.get_events("pour_volume")
        assert len(events) == 1
        assert events[0].params["direction"] == "left"
        assert events[0].params["volume"] == 50
        assert events[0].params["speed"] == 5

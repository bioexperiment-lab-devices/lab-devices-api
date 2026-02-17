from unittest.mock import AsyncMock

from lab_devices.core.history import DeviceHistory
from lab_devices.devices.densitometer.driver import DensitometerDriver
from lab_devices.devices.densitometer.protocol import DensitometerLegacyProtocol


def make_densitometer(
    measurement_delay_s: float = 0.01,
) -> tuple[DensitometerDriver, AsyncMock]:
    connection = AsyncMock()
    connection.port = "/dev/ttyUSB1"
    protocol = DensitometerLegacyProtocol()
    history = DeviceHistory()
    driver = DensitometerDriver(
        connection=connection,
        protocol=protocol,
        history=history,
        measurement_delay_s=measurement_delay_s,
    )
    return driver, connection


class TestDensitometerDriver:
    async def test_get_temperature(self) -> None:
        densitometer, conn = make_densitometer()
        conn.send_and_receive = AsyncMock(
            return_value=bytes([0x00, 0x00, 0x17, 0x32])
        )
        result = await densitometer.get_temperature()
        assert result == 23.50
        conn.send_and_receive.assert_awaited_once_with(
            bytes([0x4C, 0x00, 0x00, 0x00, 0x00]), 4, 2.0
        )

    async def test_get_temperature_records_event(self) -> None:
        densitometer, conn = make_densitometer()
        conn.send_and_receive = AsyncMock(
            return_value=bytes([0x00, 0x00, 0x17, 0x32])
        )
        await densitometer.get_temperature()
        events = densitometer.history.get_events("get_temperature")
        assert len(events) == 1
        assert events[0].params["temperature_c"] == 23.50

    async def test_get_od(self) -> None:
        densitometer, conn = make_densitometer()
        conn.send_and_receive = AsyncMock(
            return_value=bytes([0x00, 0x00, 0x00, 0x2A])
        )
        result = await densitometer.get_od()
        assert result == 0.42

    async def test_get_od_sends_start_then_read(self) -> None:
        densitometer, conn = make_densitometer()
        conn.send_and_receive = AsyncMock(
            return_value=bytes([0x00, 0x00, 0x00, 0x2A])
        )
        await densitometer.get_od()
        conn.send_command.assert_awaited_once_with(
            bytes([0x4E, 0x04, 0x00, 0x00, 0x00])
        )
        conn.send_and_receive.assert_awaited_once_with(
            bytes([0x4F, 0x04, 0x00, 0x00, 0x00]), 4, 2.0
        )

    async def test_get_od_records_state_and_event(self) -> None:
        densitometer, conn = make_densitometer()
        conn.send_and_receive = AsyncMock(
            return_value=bytes([0x00, 0x00, 0x00, 0x2A])
        )
        await densitometer.get_od()
        states = densitometer.history.get_states("measuring_od")
        assert len(states) == 1
        assert states[0].ended_at is not None
        events = densitometer.history.get_events("get_od")
        assert len(events) == 1
        assert events[0].params["absorbance"] == 0.42

    async def test_get_od_no_state_after_completion(self) -> None:
        densitometer, conn = make_densitometer()
        conn.send_and_receive = AsyncMock(
            return_value=bytes([0x00, 0x00, 0x00, 0x2A])
        )
        await densitometer.get_od()
        assert densitometer.history.current_state() is None

import pytest
from unittest.mock import AsyncMock

from lab_devices.core.driver import BaseDeviceDriver
from lab_devices.core.history import DeviceHistory


class ConcreteDriver(BaseDeviceDriver):
    async def do_something(self) -> bytes:
        return await self._send_and_receive(b"\x01", 4)


class TestBaseDeviceDriver:
    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            BaseDeviceDriver(  # type: ignore[abstract]
                connection=AsyncMock(),
                protocol=AsyncMock(),
                history=DeviceHistory(),
            )

    def test_port_property(self) -> None:
        connection = AsyncMock()
        connection.port = "/dev/ttyUSB0"
        driver = ConcreteDriver(
            connection=connection,
            protocol=AsyncMock(),
            history=DeviceHistory(),
        )
        assert driver.port == "/dev/ttyUSB0"

    def test_history_property(self) -> None:
        history = DeviceHistory()
        driver = ConcreteDriver(
            connection=AsyncMock(),
            protocol=AsyncMock(),
            history=history,
        )
        assert driver.history is history

    async def test_send_command(self) -> None:
        connection = AsyncMock()
        driver = ConcreteDriver(
            connection=connection,
            protocol=AsyncMock(),
            history=DeviceHistory(),
        )
        await driver._send_command(b"\x01\x02")
        connection.send_command.assert_awaited_once_with(b"\x01\x02")

    async def test_send_and_receive(self) -> None:
        connection = AsyncMock()
        connection.send_and_receive = AsyncMock(return_value=b"\x0a\x00\x00\x00")
        driver = ConcreteDriver(
            connection=connection,
            protocol=AsyncMock(),
            history=DeviceHistory(),
        )
        result = await driver.do_something()
        connection.send_and_receive.assert_awaited_once_with(b"\x01", 4, 2.0)
        assert result == b"\x0a\x00\x00\x00"

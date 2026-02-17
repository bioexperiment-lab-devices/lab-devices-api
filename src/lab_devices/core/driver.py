from abc import ABC

from lab_devices.core.connection import SerialConnection
from lab_devices.core.history import DeviceHistory
from lab_devices.core.protocol import BaseProtocolHandler


class BaseDeviceDriver(ABC):  # noqa: B024
    def __init__(
        self,
        connection: SerialConnection,
        protocol: BaseProtocolHandler,
        history: DeviceHistory,
    ) -> None:
        if type(self) is BaseDeviceDriver:
            raise TypeError("Cannot instantiate abstract class BaseDeviceDriver directly")
        self._connection = connection
        self._protocol = protocol
        self._history = history

    @property
    def history(self) -> DeviceHistory:
        return self._history

    @property
    def port(self) -> str:
        return self._connection.port

    async def _send_command(self, data: bytes) -> None:
        await self._connection.send_command(data)

    async def _send_and_receive(self, data: bytes, response_size: int, timeout: float = 2.0) -> bytes:
        return await self._connection.send_and_receive(data, response_size, timeout)

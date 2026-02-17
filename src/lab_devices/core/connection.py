import asyncio
from typing import Self

from aioserial import AioSerial

from lab_devices.exceptions import DeviceConnectionError, DeviceTimeoutError


class SerialConnection:
    def __init__(self, port: str, baudrate: int = 9600) -> None:
        self._port = port
        self._baudrate = baudrate
        self._serial: AioSerial | None = None
        self._lock = asyncio.Lock()

    @property
    def port(self) -> str:
        return self._port

    @property
    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    async def connect(self) -> None:
        try:
            self._serial = AioSerial(port=self._port, baudrate=self._baudrate)
        except Exception as e:
            raise DeviceConnectionError(f"Failed to open {self._port}: {e}") from e

    async def disconnect(self) -> None:
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
        self._serial = None

    async def send_command(self, data: bytes) -> None:
        if self._serial is None:
            raise DeviceConnectionError("Not connected")
        async with self._lock:
            await self._serial.write_async(data)

    async def send_and_receive(self, data: bytes, response_size: int, timeout: float = 2.0) -> bytes:
        if self._serial is None:
            raise DeviceConnectionError("Not connected")
        async with self._lock:
            await self._serial.write_async(data)
            try:
                response = await asyncio.wait_for(
                    self._serial.read_async(response_size),
                    timeout=timeout,
                )
            except asyncio.TimeoutError as e:
                raise DeviceTimeoutError(f"Read timeout on {self._port}") from e
            return bytes(response)

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.disconnect()

from lab_devices.exceptions import DeviceConnectionError, DeviceTimeoutError


class SerialConnection:
    def __init__(self, port: str, baudrate: int = 9600) -> None:
        self._port = port
        self._baudrate = baudrate

    @property
    def port(self) -> str:
        return self._port

    @property
    def is_connected(self) -> bool:
        return False

    async def connect(self) -> None:
        raise NotImplementedError

    async def disconnect(self) -> None:
        raise NotImplementedError

    async def send_command(self, data: bytes) -> None:
        raise NotImplementedError

    async def send_and_receive(
        self, data: bytes, response_size: int, timeout: float = 2.0
    ) -> bytes:
        raise NotImplementedError

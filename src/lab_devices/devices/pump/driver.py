from lab_devices.core.connection import SerialConnection
from lab_devices.core.driver import BaseDeviceDriver
from lab_devices.core.history import DeviceHistory
from lab_devices.devices.pump.protocol import PumpLegacyProtocol
from lab_devices.models.device import Direction


class PumpDriver(BaseDeviceDriver):
    def __init__(
        self,
        connection: SerialConnection,
        protocol: PumpLegacyProtocol,
        history: DeviceHistory,
    ) -> None:
        super().__init__(connection, protocol, history)
        self._protocol: PumpLegacyProtocol = protocol
        self._stored_speed: int = 0

    async def start_rotation(self, speed: int, direction: Direction) -> None:
        if direction == Direction.LEFT:
            data = self._protocol.encode_rotate_left(speed)
        else:
            data = self._protocol.encode_rotate_right(speed)
        await self._send_command(data)
        self._history.start_state("rotating", {"direction": direction.value, "speed": speed})

    async def stop_rotation(self) -> None:
        data = self._protocol.encode_rotate_left(0)
        await self._send_command(data)
        self._history.end_current_state()

    async def set_rotation_speed(self, speed: int) -> None:
        data = self._protocol.encode_set_speed(speed)
        await self._send_command(data)
        self._stored_speed = speed
        self._history.record_event("set_speed", {"speed": speed})

    async def pour_volume(self, direction: Direction, volume: int) -> None:
        if direction == Direction.LEFT:
            data = self._protocol.encode_pour_left(volume)
        else:
            data = self._protocol.encode_pour_right(volume)
        await self._send_command(data)
        self._history.record_event(
            "pour_volume",
            {
                "direction": direction.value,
                "speed": self._stored_speed,
                "volume": volume,
            },
        )

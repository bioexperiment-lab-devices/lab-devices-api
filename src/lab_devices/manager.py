from typing import Self

from lab_devices.config import AppConfig
from lab_devices.core.connection import SerialConnection
from lab_devices.core.driver import BaseDeviceDriver
from lab_devices.core.history import DeviceHistory
from lab_devices.devices.densitometer.driver import DensitometerDriver
from lab_devices.devices.densitometer.protocol import DensitometerLegacyProtocol
from lab_devices.devices.pump.driver import PumpDriver
from lab_devices.devices.pump.protocol import PumpLegacyProtocol
from lab_devices.discovery import discover_devices
from lab_devices.exceptions import DeviceNotFoundError
from lab_devices.models.device import DeviceType


class DeviceManager:
    def __init__(self, config: AppConfig | None = None) -> None:
        self._config = config or AppConfig()
        self._devices: dict[str, BaseDeviceDriver] = {}
        self._connections: list[SerialConnection] = []

    @classmethod
    async def create(cls, config: AppConfig | None = None) -> Self:
        return cls(config)

    async def discover(self, ports: list[str] | None = None) -> dict[str, BaseDeviceDriver]:
        discovered = await discover_devices(
            ports=ports,
            extra_ports=self._config.discovery.extra_ports,
            baudrate=self._config.discovery.baudrate,
            timeout=self._config.discovery.timeout_s,
        )

        type_counts: dict[DeviceType, int] = {}

        for device_info in discovered:
            count = type_counts.get(device_info.device_type, 0)
            name = f"{device_info.device_type.value}_{count}"
            type_counts[device_info.device_type] = count + 1

            connection = SerialConnection(
                device_info.port,
                self._config.discovery.baudrate,
            )
            await connection.connect()
            self._connections.append(connection)

            history = DeviceHistory()
            driver = self._create_driver(device_info.device_type, connection, history)
            self._devices[name] = driver

        return dict(self._devices)

    def _create_driver(
        self,
        device_type: DeviceType,
        connection: SerialConnection,
        history: DeviceHistory,
    ) -> BaseDeviceDriver:
        if device_type == DeviceType.PUMP:
            pump_protocol = PumpLegacyProtocol()
            return PumpDriver(connection, pump_protocol, history)
        if device_type == DeviceType.DENSITOMETER:
            densitometer_protocol = DensitometerLegacyProtocol()
            return DensitometerDriver(
                connection,
                densitometer_protocol,
                history,
                measurement_delay_s=self._config.devices.densitometer.measurement_delay_s,
            )
        msg = f"Unknown device type: {device_type}"
        raise ValueError(msg)

    def get_device(self, name: str) -> BaseDeviceDriver:
        if name not in self._devices:
            raise DeviceNotFoundError(f"Device not found: {name}")
        return self._devices[name]

    def get_pump(self, name: str) -> PumpDriver:
        device = self.get_device(name)
        if not isinstance(device, PumpDriver):
            raise DeviceNotFoundError(f"Device {name} is not a pump")
        return device

    def get_densitometer(self, name: str) -> DensitometerDriver:
        device = self.get_device(name)
        if not isinstance(device, DensitometerDriver):
            raise DeviceNotFoundError(f"Device {name} is not a densitometer")
        return device

    def list_devices(self) -> dict[str, DeviceType]:
        result: dict[str, DeviceType] = {}
        for name, driver in self._devices.items():
            if isinstance(driver, PumpDriver):
                result[name] = DeviceType.PUMP
            elif isinstance(driver, DensitometerDriver):
                result[name] = DeviceType.DENSITOMETER
        return result

    async def close(self) -> None:
        for connection in self._connections:
            await connection.disconnect()
        self._connections.clear()
        self._devices.clear()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

import asyncio

from serial.tools.list_ports import comports

from lab_devices.core.connection import SerialConnection
from lab_devices.core.protocol import BaseProtocolHandler
from lab_devices.devices.densitometer.protocol import DensitometerLegacyProtocol
from lab_devices.devices.pump.protocol import PumpLegacyProtocol
from lab_devices.exceptions import DeviceConnectionError, DeviceTimeoutError
from lab_devices.models.device import DeviceType, DiscoveredDevice

_KNOWN_PROTOCOLS: dict[DeviceType, type[BaseProtocolHandler]] = {
    DeviceType.PUMP: PumpLegacyProtocol,
    DeviceType.DENSITOMETER: DensitometerLegacyProtocol,
}


async def _probe_port(
    port: str,
    baudrate: int,
    timeout: float,
) -> DiscoveredDevice | None:
    for device_type, protocol_cls in _KNOWN_PROTOCOLS.items():
        protocol = protocol_cls()
        connection = SerialConnection(port, baudrate)
        try:
            await connection.connect()
            try:
                response = await connection.send_and_receive(
                    protocol.build_identification_probe(),
                    protocol.get_identification_response_size(),
                    timeout=timeout,
                )
                if protocol.parse_identification_response(response):
                    await connection.disconnect()
                    return DiscoveredDevice(device_type=device_type, port=port)
            finally:
                await connection.disconnect()
        except (DeviceTimeoutError, DeviceConnectionError):
            continue
    return None


async def discover_devices(
    ports: list[str] | None = None,
    extra_ports: list[str] | None = None,
    baudrate: int = 9600,
    timeout: float = 1.0,
) -> list[DiscoveredDevice]:
    if ports is None:
        ports = [p.device for p in comports()]
    all_ports = list(set(ports + extra_ports)) if extra_ports else ports

    if not all_ports:
        return []

    tasks = [_probe_port(port, baudrate, timeout) for port in all_ports]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    devices: list[DiscoveredDevice] = []
    for result in results:
        if isinstance(result, DiscoveredDevice):
            devices.append(result)
    return devices

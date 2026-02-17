import asyncio

from lab_devices.core.connection import SerialConnection
from lab_devices.core.driver import BaseDeviceDriver
from lab_devices.core.history import DeviceHistory
from lab_devices.devices.densitometer.protocol import DensitometerLegacyProtocol


class DensitometerDriver(BaseDeviceDriver):
    def __init__(
        self,
        connection: SerialConnection,
        protocol: DensitometerLegacyProtocol,
        history: DeviceHistory,
        measurement_delay_s: float = 2.0,
    ) -> None:
        super().__init__(connection, protocol, history)
        self._protocol: DensitometerLegacyProtocol = protocol
        self._measurement_delay_s = measurement_delay_s

    async def get_temperature(self) -> float:
        data = self._protocol.encode_temperature_request()
        response = await self._send_and_receive(
            data, self._protocol.get_value_response_size()
        )
        temperature = self._protocol.decode_value(response)
        self._history.record_event(
            "get_temperature", {"temperature_c": temperature}
        )
        return temperature

    async def get_od(self) -> float:
        start_data = self._protocol.encode_start_measurement()
        await self._send_command(start_data)
        self._history.start_state("measuring_od")

        await asyncio.sleep(self._measurement_delay_s)

        read_data = self._protocol.encode_od_request()
        response = await self._send_and_receive(
            read_data, self._protocol.get_value_response_size()
        )
        od = self._protocol.decode_value(response)

        self._history.end_current_state()
        self._history.record_event("get_od", {"absorbance": od})
        return od

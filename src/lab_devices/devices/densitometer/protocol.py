from lab_devices.core.protocol import BaseProtocolHandler


class DensitometerLegacyProtocol(BaseProtocolHandler):
    _IDENTIFICATION_PROBE = bytes([0x01, 0x02, 0x03, 0x04, 0x00])
    _IDENTIFICATION_RESPONSE = bytes([0x46, 0x00, 0x00, 0x00])

    def build_identification_probe(self) -> bytes:
        return self._IDENTIFICATION_PROBE

    def parse_identification_response(self, data: bytes) -> bool:
        return data == self._IDENTIFICATION_RESPONSE

    def get_identification_response_size(self) -> int:
        return 4

    def encode_temperature_request(self) -> bytes:
        return bytes([0x4C, 0x00, 0x00, 0x00, 0x00])

    def encode_start_measurement(self) -> bytes:
        return bytes([0x4E, 0x04, 0x00, 0x00, 0x00])

    def encode_od_request(self) -> bytes:
        return bytes([0x4F, 0x04, 0x00, 0x00, 0x00])

    def decode_value(self, data: bytes) -> float:
        return float(data[2]) + float(data[3]) / 100

    def get_value_response_size(self) -> int:
        return 4

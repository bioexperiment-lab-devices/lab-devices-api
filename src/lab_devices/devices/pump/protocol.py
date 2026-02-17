from lab_devices.core.protocol import BaseProtocolHandler


class PumpLegacyProtocol(BaseProtocolHandler):
    _IDENTIFICATION_PROBE = bytes([0x01, 0x02, 0x03, 0x04, 0xB5])
    _IDENTIFICATION_RESPONSE = bytes([0x0A, 0x00, 0x00, 0x00])

    def build_identification_probe(self) -> bytes:
        return self._IDENTIFICATION_PROBE

    def parse_identification_response(self, data: bytes) -> bool:
        return data == self._IDENTIFICATION_RESPONSE

    def get_identification_response_size(self) -> int:
        return 4

    def encode_rotate_left(self, speed: int) -> bytes:
        return bytes([0x0B, 0x6F, 0x00, speed, 0x00])

    def encode_rotate_right(self, speed: int) -> bytes:
        return bytes([0x0C, 0x6F, 0x00, speed, 0x00])

    def encode_set_speed(self, speed: int) -> bytes:
        return bytes([0x0A, 0x00, 0x00, speed, 0x00])

    def encode_pour_left(self, volume: int) -> bytes:
        return bytes([0x10, 0x00, 0x00, 0x00, volume])

    def encode_pour_right(self, volume: int) -> bytes:
        return bytes([0x11, 0x00, 0x00, 0x00, volume])

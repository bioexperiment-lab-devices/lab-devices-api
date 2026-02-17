from lab_devices.devices.pump.protocol import PumpLegacyProtocol


class TestPumpLegacyProtocol:
    def setup_method(self) -> None:
        self.protocol = PumpLegacyProtocol()

    def test_identification_probe(self) -> None:
        assert self.protocol.build_identification_probe() == bytes(
            [0x01, 0x02, 0x03, 0x04, 0xB5]
        )

    def test_parse_identification_response_valid(self) -> None:
        assert self.protocol.parse_identification_response(
            bytes([0x0A, 0x00, 0x00, 0x00])
        ) is True

    def test_parse_identification_response_invalid(self) -> None:
        assert self.protocol.parse_identification_response(
            bytes([0x46, 0x00, 0x00, 0x00])
        ) is False

    def test_identification_response_size(self) -> None:
        assert self.protocol.get_identification_response_size() == 4

    def test_encode_rotate_left(self) -> None:
        result = self.protocol.encode_rotate_left(5)
        assert result == bytes([0x0B, 0x6F, 0x00, 0x05, 0x00])

    def test_encode_rotate_right(self) -> None:
        result = self.protocol.encode_rotate_right(10)
        assert result == bytes([0x0C, 0x6F, 0x00, 0x0A, 0x00])

    def test_encode_set_speed(self) -> None:
        result = self.protocol.encode_set_speed(3)
        assert result == bytes([0x0A, 0x00, 0x00, 0x03, 0x00])

    def test_encode_pour_left(self) -> None:
        result = self.protocol.encode_pour_left(50)
        assert result == bytes([0x10, 0x00, 0x00, 0x00, 0x32])

    def test_encode_pour_right(self) -> None:
        result = self.protocol.encode_pour_right(100)
        assert result == bytes([0x11, 0x00, 0x00, 0x00, 0x64])

    def test_encode_rotate_left_zero_speed(self) -> None:
        result = self.protocol.encode_rotate_left(0)
        assert result == bytes([0x0B, 0x6F, 0x00, 0x00, 0x00])

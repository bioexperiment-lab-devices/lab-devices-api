from lab_devices.devices.densitometer.protocol import DensitometerLegacyProtocol


class TestDensitometerLegacyProtocol:
    def setup_method(self) -> None:
        self.protocol = DensitometerLegacyProtocol()

    def test_identification_probe(self) -> None:
        assert self.protocol.build_identification_probe() == bytes(
            [0x01, 0x02, 0x03, 0x04, 0x00]
        )

    def test_parse_identification_response_valid(self) -> None:
        assert self.protocol.parse_identification_response(
            bytes([0x46, 0x00, 0x00, 0x00])
        ) is True

    def test_parse_identification_response_invalid(self) -> None:
        assert self.protocol.parse_identification_response(
            bytes([0x0A, 0x00, 0x00, 0x00])
        ) is False

    def test_identification_response_size(self) -> None:
        assert self.protocol.get_identification_response_size() == 4

    def test_encode_temperature_request(self) -> None:
        assert self.protocol.encode_temperature_request() == bytes(
            [0x4C, 0x00, 0x00, 0x00, 0x00]
        )

    def test_encode_start_measurement(self) -> None:
        assert self.protocol.encode_start_measurement() == bytes(
            [0x4E, 0x04, 0x00, 0x00, 0x00]
        )

    def test_encode_od_request(self) -> None:
        assert self.protocol.encode_od_request() == bytes(
            [0x4F, 0x04, 0x00, 0x00, 0x00]
        )

    def test_decode_value_temperature(self) -> None:
        # 23 + 50/100 = 23.50
        result = self.protocol.decode_value(bytes([0x00, 0x00, 0x17, 0x32]))
        assert result == 23.50

    def test_decode_value_od(self) -> None:
        # 0 + 42/100 = 0.42
        result = self.protocol.decode_value(bytes([0x00, 0x00, 0x00, 0x2A]))
        assert result == 0.42

    def test_decode_value_zero(self) -> None:
        result = self.protocol.decode_value(bytes([0x00, 0x00, 0x00, 0x00]))
        assert result == 0.0

    def test_value_response_size(self) -> None:
        assert self.protocol.get_value_response_size() == 4

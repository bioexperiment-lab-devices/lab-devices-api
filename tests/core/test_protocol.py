import pytest

from lab_devices.core.protocol import BaseProtocolHandler


class ConcreteProtocol(BaseProtocolHandler):
    def build_identification_probe(self) -> bytes:
        return b"\x01\x02"

    def parse_identification_response(self, data: bytes) -> bool:
        return data == b"\x0a\x00"

    def get_identification_response_size(self) -> int:
        return 2


class TestBaseProtocolHandler:
    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            BaseProtocolHandler()  # type: ignore[abstract]

    def test_concrete_build_probe(self) -> None:
        protocol = ConcreteProtocol()
        assert protocol.build_identification_probe() == b"\x01\x02"

    def test_concrete_parse_response(self) -> None:
        protocol = ConcreteProtocol()
        assert protocol.parse_identification_response(b"\x0a\x00") is True
        assert protocol.parse_identification_response(b"\xff\xff") is False

    def test_concrete_response_size(self) -> None:
        protocol = ConcreteProtocol()
        assert protocol.get_identification_response_size() == 2

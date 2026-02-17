from abc import ABC, abstractmethod


class BaseProtocolHandler(ABC):
    @abstractmethod
    def build_identification_probe(self) -> bytes: ...

    @abstractmethod
    def parse_identification_response(self, data: bytes) -> bool: ...

    @abstractmethod
    def get_identification_response_size(self) -> int: ...

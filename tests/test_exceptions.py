import pytest

from lab_devices.exceptions import (
    DeviceConnectionError,
    DeviceNotFoundError,
    DeviceTimeoutError,
    LabDevicesError,
    UnexpectedResponseError,
)


class TestExceptionHierarchy:
    def test_base_exception(self) -> None:
        with pytest.raises(LabDevicesError):
            raise LabDevicesError("base error")

    def test_timeout_is_lab_devices_error(self) -> None:
        with pytest.raises(LabDevicesError):
            raise DeviceTimeoutError("timeout")

    def test_not_found_is_lab_devices_error(self) -> None:
        with pytest.raises(LabDevicesError):
            raise DeviceNotFoundError("not found")

    def test_connection_is_lab_devices_error(self) -> None:
        with pytest.raises(LabDevicesError):
            raise DeviceConnectionError("connection failed")

    def test_unexpected_response_is_lab_devices_error(self) -> None:
        with pytest.raises(LabDevicesError):
            raise UnexpectedResponseError("bad response")

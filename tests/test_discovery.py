from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from lab_devices.discovery import discover_devices, _probe_port
from lab_devices.exceptions import DeviceConnectionError, DeviceTimeoutError
from lab_devices.models.device import DeviceType


class TestProbePort:
    async def test_probe_finds_pump(self) -> None:
        mock_conn = AsyncMock()
        mock_conn.send_and_receive = AsyncMock(
            return_value=bytes([0x0A, 0x00, 0x00, 0x00])
        )
        with patch(
            "lab_devices.discovery.SerialConnection", return_value=mock_conn
        ):
            result = await _probe_port("/dev/ttyUSB0", 9600, 1.0)
        assert result is not None
        assert result.device_type == DeviceType.PUMP
        assert result.port == "/dev/ttyUSB0"

    async def test_probe_finds_densitometer(self) -> None:
        mock_conn = AsyncMock()
        # First probe (pump) fails, second (densitometer) succeeds
        mock_conn.send_and_receive = AsyncMock(
            side_effect=[
                DeviceTimeoutError("timeout"),
                bytes([0x46, 0x00, 0x00, 0x00]),
            ]
        )
        with patch(
            "lab_devices.discovery.SerialConnection", return_value=mock_conn
        ):
            result = await _probe_port("/dev/ttyUSB1", 9600, 1.0)
        assert result is not None
        assert result.device_type == DeviceType.DENSITOMETER

    async def test_probe_finds_nothing(self) -> None:
        mock_conn = AsyncMock()
        mock_conn.send_and_receive = AsyncMock(
            side_effect=DeviceTimeoutError("timeout")
        )
        with patch(
            "lab_devices.discovery.SerialConnection", return_value=mock_conn
        ):
            result = await _probe_port("/dev/ttyUSB2", 9600, 1.0)
        assert result is None

    async def test_probe_connection_error(self) -> None:
        mock_conn = AsyncMock()
        mock_conn.connect = AsyncMock(
            side_effect=DeviceConnectionError("cannot open")
        )
        with patch(
            "lab_devices.discovery.SerialConnection", return_value=mock_conn
        ):
            result = await _probe_port("/dev/nonexistent", 9600, 1.0)
        assert result is None


class TestDiscoverDevices:
    async def test_discover_with_explicit_ports(self) -> None:
        mock_conn = AsyncMock()
        mock_conn.send_and_receive = AsyncMock(
            return_value=bytes([0x0A, 0x00, 0x00, 0x00])
        )
        with patch(
            "lab_devices.discovery.SerialConnection", return_value=mock_conn
        ):
            result = await discover_devices(ports=["/dev/ttyUSB0"])
        assert len(result) == 1
        assert result[0].device_type == DeviceType.PUMP

    async def test_discover_auto_detect(self) -> None:
        mock_port = MagicMock()
        mock_port.device = "/dev/ttyUSB0"
        mock_conn = AsyncMock()
        mock_conn.send_and_receive = AsyncMock(
            return_value=bytes([0x0A, 0x00, 0x00, 0x00])
        )
        with (
            patch("lab_devices.discovery.comports", return_value=[mock_port]),
            patch(
                "lab_devices.discovery.SerialConnection",
                return_value=mock_conn,
            ),
        ):
            result = await discover_devices()
        assert len(result) == 1

    async def test_discover_with_extra_ports(self) -> None:
        mock_conn = AsyncMock()
        mock_conn.send_and_receive = AsyncMock(
            side_effect=DeviceTimeoutError("timeout")
        )
        with (
            patch("lab_devices.discovery.comports", return_value=[]),
            patch(
                "lab_devices.discovery.SerialConnection",
                return_value=mock_conn,
            ),
        ):
            result = await discover_devices(
                extra_ports=["/dev/ttyUSB0"]
            )
        assert len(result) == 0

    async def test_discover_empty(self) -> None:
        with patch("lab_devices.discovery.comports", return_value=[]):
            result = await discover_devices()
        assert len(result) == 0

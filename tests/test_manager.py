from unittest.mock import AsyncMock, patch

import pytest

from lab_devices.config import AppConfig
from lab_devices.devices.densitometer.driver import DensitometerDriver
from lab_devices.devices.pump.driver import PumpDriver
from lab_devices.exceptions import DeviceNotFoundError
from lab_devices.manager import DeviceManager
from lab_devices.models.device import DeviceType, DiscoveredDevice


class TestDeviceManager:
    async def test_create(self) -> None:
        manager = await DeviceManager.create()
        assert manager is not None

    async def test_discover_creates_devices(self) -> None:
        discovered = [
            DiscoveredDevice(device_type=DeviceType.PUMP, port="/dev/ttyUSB0"),
        ]
        mock_conn = AsyncMock()
        mock_conn.port = "/dev/ttyUSB0"
        with (
            patch(
                "lab_devices.manager.discover_devices",
                return_value=discovered,
            ),
            patch(
                "lab_devices.manager.SerialConnection",
                return_value=mock_conn,
            ),
        ):
            manager = await DeviceManager.create()
            devices = await manager.discover()
        assert "pump_0" in devices
        assert isinstance(devices["pump_0"], PumpDriver)

    async def test_discover_multiple_devices(self) -> None:
        discovered = [
            DiscoveredDevice(device_type=DeviceType.PUMP, port="/dev/ttyUSB0"),
            DiscoveredDevice(
                device_type=DeviceType.DENSITOMETER, port="/dev/ttyUSB1"
            ),
        ]
        mock_conn = AsyncMock()
        with (
            patch(
                "lab_devices.manager.discover_devices",
                return_value=discovered,
            ),
            patch(
                "lab_devices.manager.SerialConnection",
                return_value=mock_conn,
            ),
        ):
            manager = await DeviceManager.create()
            devices = await manager.discover()
        assert "pump_0" in devices
        assert "densitometer_0" in devices

    async def test_get_device(self) -> None:
        discovered = [
            DiscoveredDevice(device_type=DeviceType.PUMP, port="/dev/ttyUSB0"),
        ]
        mock_conn = AsyncMock()
        with (
            patch(
                "lab_devices.manager.discover_devices",
                return_value=discovered,
            ),
            patch(
                "lab_devices.manager.SerialConnection",
                return_value=mock_conn,
            ),
        ):
            manager = await DeviceManager.create()
            await manager.discover()
        device = manager.get_device("pump_0")
        assert isinstance(device, PumpDriver)

    async def test_get_device_not_found(self) -> None:
        manager = await DeviceManager.create()
        with pytest.raises(DeviceNotFoundError):
            manager.get_device("nonexistent")

    async def test_get_pump(self) -> None:
        discovered = [
            DiscoveredDevice(device_type=DeviceType.PUMP, port="/dev/ttyUSB0"),
        ]
        mock_conn = AsyncMock()
        with (
            patch(
                "lab_devices.manager.discover_devices",
                return_value=discovered,
            ),
            patch(
                "lab_devices.manager.SerialConnection",
                return_value=mock_conn,
            ),
        ):
            manager = await DeviceManager.create()
            await manager.discover()
        pump = manager.get_pump("pump_0")
        assert isinstance(pump, PumpDriver)

    async def test_get_pump_wrong_type(self) -> None:
        discovered = [
            DiscoveredDevice(
                device_type=DeviceType.DENSITOMETER, port="/dev/ttyUSB0"
            ),
        ]
        mock_conn = AsyncMock()
        with (
            patch(
                "lab_devices.manager.discover_devices",
                return_value=discovered,
            ),
            patch(
                "lab_devices.manager.SerialConnection",
                return_value=mock_conn,
            ),
        ):
            manager = await DeviceManager.create()
            await manager.discover()
        with pytest.raises(DeviceNotFoundError):
            manager.get_pump("densitometer_0")

    async def test_get_densitometer(self) -> None:
        discovered = [
            DiscoveredDevice(
                device_type=DeviceType.DENSITOMETER, port="/dev/ttyUSB0"
            ),
        ]
        mock_conn = AsyncMock()
        with (
            patch(
                "lab_devices.manager.discover_devices",
                return_value=discovered,
            ),
            patch(
                "lab_devices.manager.SerialConnection",
                return_value=mock_conn,
            ),
        ):
            manager = await DeviceManager.create()
            await manager.discover()
        densitometer = manager.get_densitometer("densitometer_0")
        assert isinstance(densitometer, DensitometerDriver)

    async def test_list_devices(self) -> None:
        discovered = [
            DiscoveredDevice(device_type=DeviceType.PUMP, port="/dev/ttyUSB0"),
            DiscoveredDevice(
                device_type=DeviceType.DENSITOMETER, port="/dev/ttyUSB1"
            ),
        ]
        mock_conn = AsyncMock()
        with (
            patch(
                "lab_devices.manager.discover_devices",
                return_value=discovered,
            ),
            patch(
                "lab_devices.manager.SerialConnection",
                return_value=mock_conn,
            ),
        ):
            manager = await DeviceManager.create()
            await manager.discover()
        devices = manager.list_devices()
        assert devices == {
            "pump_0": DeviceType.PUMP,
            "densitometer_0": DeviceType.DENSITOMETER,
        }

    async def test_close(self) -> None:
        discovered = [
            DiscoveredDevice(device_type=DeviceType.PUMP, port="/dev/ttyUSB0"),
        ]
        mock_conn = AsyncMock()
        with (
            patch(
                "lab_devices.manager.discover_devices",
                return_value=discovered,
            ),
            patch(
                "lab_devices.manager.SerialConnection",
                return_value=mock_conn,
            ),
        ):
            manager = await DeviceManager.create()
            await manager.discover()
            await manager.close()
        mock_conn.disconnect.assert_awaited()

    async def test_context_manager(self) -> None:
        discovered = [
            DiscoveredDevice(device_type=DeviceType.PUMP, port="/dev/ttyUSB0"),
        ]
        mock_conn = AsyncMock()
        with (
            patch(
                "lab_devices.manager.discover_devices",
                return_value=discovered,
            ),
            patch(
                "lab_devices.manager.SerialConnection",
                return_value=mock_conn,
            ),
        ):
            async with await DeviceManager.create() as manager:
                await manager.discover()
        mock_conn.disconnect.assert_awaited()

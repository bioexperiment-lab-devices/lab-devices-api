import os
import pty

import pytest

from lab_devices.core.connection import SerialConnection
from lab_devices.exceptions import DeviceConnectionError, DeviceTimeoutError


@pytest.fixture()
def pty_pair() -> tuple[int, str]:
    """Create a PTY pair and return (master_fd, slave_path)."""
    master_fd, slave_fd = pty.openpty()
    slave_path = os.ttyname(slave_fd)
    yield master_fd, slave_path
    os.close(master_fd)
    os.close(slave_fd)


class TestSerialConnection:
    def test_port_property(self) -> None:
        conn = SerialConnection("/dev/ttyUSB0")
        assert conn.port == "/dev/ttyUSB0"

    def test_not_connected_initially(self) -> None:
        conn = SerialConnection("/dev/ttyUSB0")
        assert conn.is_connected is False

    async def test_connect_and_disconnect(self, pty_pair: tuple[int, str]) -> None:
        _, slave_path = pty_pair
        conn = SerialConnection(slave_path)
        await conn.connect()
        assert conn.is_connected is True
        await conn.disconnect()
        assert conn.is_connected is False

    async def test_connect_invalid_port(self) -> None:
        conn = SerialConnection("/dev/nonexistent_port_xyz")
        with pytest.raises(DeviceConnectionError):
            await conn.connect()

    async def test_send_and_receive(self, pty_pair: tuple[int, str]) -> None:
        master_fd, slave_path = pty_pair
        conn = SerialConnection(slave_path)
        await conn.connect()
        try:
            # Simulate device: write response to master before reading
            os.write(master_fd, b"\x0a\x00\x00\x00")

            response = await conn.send_and_receive(b"\x01\x02\x03\x04\xb5", 4, timeout=2.0)
            assert response == b"\x0a\x00\x00\x00"

            # Verify what was sent
            sent = os.read(master_fd, 5)
            assert sent == b"\x01\x02\x03\x04\xb5"
        finally:
            await conn.disconnect()

    async def test_send_command(self, pty_pair: tuple[int, str]) -> None:
        master_fd, slave_path = pty_pair
        conn = SerialConnection(slave_path)
        await conn.connect()
        try:
            await conn.send_command(b"\x0b\x6f\x00\x05\x00")
            sent = os.read(master_fd, 5)
            assert sent == b"\x0b\x6f\x00\x05\x00"
        finally:
            await conn.disconnect()

    async def test_send_command_not_connected(self) -> None:
        conn = SerialConnection("/dev/ttyUSB0")
        with pytest.raises(DeviceConnectionError):
            await conn.send_command(b"\x01")

    async def test_send_and_receive_not_connected(self) -> None:
        conn = SerialConnection("/dev/ttyUSB0")
        with pytest.raises(DeviceConnectionError):
            await conn.send_and_receive(b"\x01", 4)

    async def test_read_timeout(self, pty_pair: tuple[int, str]) -> None:
        _, slave_path = pty_pair
        conn = SerialConnection(slave_path)
        await conn.connect()
        try:
            with pytest.raises(DeviceTimeoutError):
                await conn.send_and_receive(b"\x01", 4, timeout=0.1)
        finally:
            await conn.disconnect()

    async def test_context_manager(self, pty_pair: tuple[int, str]) -> None:
        _, slave_path = pty_pair
        async with SerialConnection(slave_path) as conn:
            assert conn.is_connected is True
        assert conn.is_connected is False

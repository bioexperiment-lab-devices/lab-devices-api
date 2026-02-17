# Lab Devices API — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an async Python 3.14 library for discovering and communicating with laboratory hardware devices over serial ports.

**Architecture:** Layered design — SerialConnection → ProtocolHandler → DeviceDriver → History. DeviceManager orchestrates discovery and lifecycle. Each layer is independently testable with TDD.

**Tech Stack:** Python 3.14, aioserial, pyserial, pydantic, pydantic-settings[yaml], pytest, pytest-asyncio, mypy (strict), ruff, poetry, go-task

**Design doc:** `docs/plans/2026-02-17-lab-devices-design.md`

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `Taskfile.yml`
- Create: `config.yaml`
- Create: `.python-version`
- Create: `src/lab_devices/__init__.py`
- Create: `src/lab_devices/models/__init__.py`
- Create: `src/lab_devices/core/__init__.py`
- Create: `src/lab_devices/devices/__init__.py`
- Create: `src/lab_devices/devices/pump/__init__.py`
- Create: `src/lab_devices/devices/densitometer/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/core/__init__.py`
- Create: `tests/devices/__init__.py`
- Create: `tests/devices/pump/__init__.py`
- Create: `tests/devices/densitometer/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[tool.poetry]
name = "lab-devices"
version = "0.1.0"
description = "Async API for laboratory hardware devices with serial port interfaces"
packages = [{include = "lab_devices", from = "src"}]

[tool.poetry.dependencies]
python = "^3.14"
aioserial = "^1.3"
pyserial = "^3.5"
pydantic = "^2.0"
pydantic-settings = {version = "^2.6", extras = ["yaml"]}

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.25"
mypy = "^1.0"
ruff = "^0.9"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.mypy]
strict = true

[tool.ruff]
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "A", "SIM"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Step 2: Create Taskfile.yml**

```yaml
version: '3'

tasks:
  install:
    cmds:
      - poetry install

  lint:
    cmds:
      - poetry run ruff check src tests

  format:
    cmds:
      - poetry run ruff format src tests

  format-check:
    cmds:
      - poetry run ruff format --check src tests

  typecheck:
    cmds:
      - poetry run mypy src

  test:
    cmds:
      - poetry run pytest

  check:
    cmds:
      - task: lint
      - task: typecheck
      - task: test
```

**Step 3: Create config.yaml**

```yaml
discovery:
  extra_ports: []
  timeout_s: 1.0
  baudrate: 9600

devices:
  densitometer:
    measurement_delay_s: 2.0
```

**Step 4: Create .python-version**

```
3.14
```

**Step 5: Create all `__init__.py` files and conftest.py**

All `__init__.py` files are empty. `tests/conftest.py`:

```python
"""Shared test fixtures for lab_devices tests."""
```

**Step 6: Install dependencies**

Run: `poetry install`
Expected: Dependencies installed, virtualenv created.

**Step 7: Verify setup**

Run: `poetry run pytest --co`
Expected: "no tests ran" (no test files yet, but pytest finds the test directory)

**Step 8: Commit**

```bash
git add pyproject.toml Taskfile.yml config.yaml .python-version src/ tests/
git commit -m "feat: project scaffolding with poetry, taskfile, and package structure"
```

---

### Task 2: Data Models and Exceptions

**Files:**
- Create: `src/lab_devices/models/events.py`
- Create: `src/lab_devices/models/device.py`
- Create: `src/lab_devices/exceptions.py`
- Create: `tests/test_models.py`
- Create: `tests/test_exceptions.py`

**Step 1: Write failing tests for models**

`tests/test_models.py`:

```python
from datetime import datetime

from lab_devices.models.device import DeviceType, Direction, DiscoveredDevice
from lab_devices.models.events import InstantEvent, StateRecord


class TestStateRecord:
    def test_create_with_defaults(self) -> None:
        record = StateRecord(name="rotating")
        assert record.name == "rotating"
        assert record.params == {}
        assert isinstance(record.started_at, datetime)
        assert record.ended_at is None

    def test_create_with_params(self) -> None:
        record = StateRecord(
            name="rotating",
            params={"direction": "left", "speed": 5.0},
        )
        assert record.params["direction"] == "left"
        assert record.params["speed"] == 5.0

    def test_ended_at_can_be_set(self) -> None:
        record = StateRecord(name="rotating")
        now = datetime.now()
        record.ended_at = now
        assert record.ended_at == now


class TestInstantEvent:
    def test_create_with_defaults(self) -> None:
        event = InstantEvent(name="get_temperature")
        assert event.name == "get_temperature"
        assert event.params == {}
        assert isinstance(event.timestamp, datetime)

    def test_create_with_params(self) -> None:
        event = InstantEvent(
            name="get_temperature",
            params={"temperature_c": 23.5},
        )
        assert event.params["temperature_c"] == 23.5


class TestDeviceType:
    def test_pump_value(self) -> None:
        assert DeviceType.PUMP == "pump"

    def test_densitometer_value(self) -> None:
        assert DeviceType.DENSITOMETER == "densitometer"


class TestDirection:
    def test_left_value(self) -> None:
        assert Direction.LEFT == "left"

    def test_right_value(self) -> None:
        assert Direction.RIGHT == "right"


class TestDiscoveredDevice:
    def test_create(self) -> None:
        device = DiscoveredDevice(device_type=DeviceType.PUMP, port="/dev/ttyUSB0")
        assert device.device_type == DeviceType.PUMP
        assert device.port == "/dev/ttyUSB0"
```

`tests/test_exceptions.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_models.py tests/test_exceptions.py -v`
Expected: FAIL — modules not found

**Step 3: Implement models and exceptions**

`src/lab_devices/models/events.py`:

```python
from datetime import datetime

from pydantic import BaseModel, Field


class StateRecord(BaseModel):
    name: str
    params: dict[str, float | str] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: datetime | None = None


class InstantEvent(BaseModel):
    name: str
    params: dict[str, float | str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
```

`src/lab_devices/models/device.py`:

```python
from enum import StrEnum

from pydantic import BaseModel


class DeviceType(StrEnum):
    PUMP = "pump"
    DENSITOMETER = "densitometer"


class Direction(StrEnum):
    LEFT = "left"
    RIGHT = "right"


class DiscoveredDevice(BaseModel):
    device_type: DeviceType
    port: str
```

`src/lab_devices/exceptions.py`:

```python
class LabDevicesError(Exception):
    pass


class DeviceTimeoutError(LabDevicesError):
    pass


class DeviceNotFoundError(LabDevicesError):
    pass


class DeviceConnectionError(LabDevicesError):
    pass


class UnexpectedResponseError(LabDevicesError):
    pass
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_models.py tests/test_exceptions.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/lab_devices/models/ src/lab_devices/exceptions.py tests/test_models.py tests/test_exceptions.py
git commit -m "feat: add data models (StateRecord, InstantEvent, DeviceType, Direction) and exceptions"
```

---

### Task 3: DeviceHistory

**Files:**
- Create: `src/lab_devices/core/history.py`
- Create: `tests/core/test_history.py`

**Step 1: Write failing tests**

`tests/core/__init__.py` — ensure it exists (created in Task 1).

`tests/core/test_history.py`:

```python
from lab_devices.core.history import DeviceHistory


class TestDeviceHistory:
    def test_initial_state_is_none(self) -> None:
        history = DeviceHistory()
        assert history.current_state() is None

    def test_start_state(self) -> None:
        history = DeviceHistory()
        state = history.start_state("rotating", {"direction": "left", "speed": 5.0})
        assert state.name == "rotating"
        assert state.params["direction"] == "left"
        assert state.ended_at is None
        assert history.current_state() == state

    def test_start_new_state_ends_previous(self) -> None:
        history = DeviceHistory()
        first = history.start_state("rotating")
        second = history.start_state("idle")
        assert first.ended_at is not None
        assert second.ended_at is None
        assert history.current_state() == second

    def test_end_current_state(self) -> None:
        history = DeviceHistory()
        history.start_state("rotating")
        history.end_current_state()
        assert history.current_state() is None

    def test_end_current_state_when_none(self) -> None:
        history = DeviceHistory()
        history.end_current_state()  # Should not raise

    def test_record_event(self) -> None:
        history = DeviceHistory()
        event = history.record_event("get_temperature", {"temperature_c": 23.5})
        assert event.name == "get_temperature"
        assert event.params["temperature_c"] == 23.5

    def test_get_states_all(self) -> None:
        history = DeviceHistory()
        history.start_state("rotating")
        history.start_state("idle")
        assert len(history.get_states()) == 2

    def test_get_states_by_name(self) -> None:
        history = DeviceHistory()
        history.start_state("rotating")
        history.start_state("idle")
        history.start_state("rotating")
        assert len(history.get_states("rotating")) == 2

    def test_get_events_all(self) -> None:
        history = DeviceHistory()
        history.record_event("get_temperature")
        history.record_event("get_od")
        assert len(history.get_events()) == 2

    def test_get_events_by_name(self) -> None:
        history = DeviceHistory()
        history.record_event("get_temperature")
        history.record_event("get_od")
        history.record_event("get_temperature")
        assert len(history.get_events("get_temperature")) == 2

    def test_export(self) -> None:
        history = DeviceHistory()
        history.start_state("rotating", {"speed": 5.0})
        history.record_event("get_temperature", {"temperature_c": 23.5})
        exported = history.export()
        assert "states" in exported
        assert "events" in exported
        assert len(exported["states"]) == 1
        assert len(exported["events"]) == 1
```

**Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/core/test_history.py -v`
Expected: FAIL — module not found

**Step 3: Implement DeviceHistory**

`src/lab_devices/core/history.py`:

```python
from datetime import datetime

from lab_devices.models.events import InstantEvent, StateRecord


class DeviceHistory:
    def __init__(self) -> None:
        self._states: list[StateRecord] = []
        self._events: list[InstantEvent] = []

    def start_state(
        self, name: str, params: dict[str, float | str] | None = None
    ) -> StateRecord:
        self.end_current_state()
        state = StateRecord(name=name, params=params or {})
        self._states.append(state)
        return state

    def end_current_state(self) -> None:
        current = self.current_state()
        if current is not None:
            current.ended_at = datetime.now()

    def record_event(
        self, name: str, params: dict[str, float | str] | None = None
    ) -> InstantEvent:
        event = InstantEvent(name=name, params=params or {})
        self._events.append(event)
        return event

    def current_state(self) -> StateRecord | None:
        if self._states and self._states[-1].ended_at is None:
            return self._states[-1]
        return None

    def get_states(self, name: str | None = None) -> list[StateRecord]:
        if name is None:
            return list(self._states)
        return [s for s in self._states if s.name == name]

    def get_events(self, name: str | None = None) -> list[InstantEvent]:
        if name is None:
            return list(self._events)
        return [e for e in self._events if e.name == name]

    def export(self) -> dict[str, list[dict[str, object]]]:
        return {
            "states": [s.model_dump() for s in self._states],
            "events": [e.model_dump() for e in self._events],
        }
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/core/test_history.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/lab_devices/core/history.py tests/core/test_history.py
git commit -m "feat: add DeviceHistory with state/event tracking and export"
```

---

### Task 4: Core Abstractions (BaseProtocolHandler, BaseDeviceDriver)

**Files:**
- Create: `src/lab_devices/core/protocol.py`
- Create: `src/lab_devices/core/connection.py` (stub for type reference)
- Create: `src/lab_devices/core/driver.py`
- Create: `tests/core/test_protocol.py`
- Create: `tests/core/test_driver.py`

**Step 1: Write failing tests**

`tests/core/test_protocol.py`:

```python
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
```

`tests/core/test_driver.py`:

```python
import pytest
from unittest.mock import AsyncMock

from lab_devices.core.driver import BaseDeviceDriver
from lab_devices.core.history import DeviceHistory


class ConcreteDriver(BaseDeviceDriver):
    async def do_something(self) -> bytes:
        return await self._send_and_receive(b"\x01", 4)


class TestBaseDeviceDriver:
    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            BaseDeviceDriver(  # type: ignore[abstract]
                connection=AsyncMock(),
                protocol=AsyncMock(),
                history=DeviceHistory(),
            )

    def test_port_property(self) -> None:
        connection = AsyncMock()
        connection.port = "/dev/ttyUSB0"
        driver = ConcreteDriver(
            connection=connection,
            protocol=AsyncMock(),
            history=DeviceHistory(),
        )
        assert driver.port == "/dev/ttyUSB0"

    def test_history_property(self) -> None:
        history = DeviceHistory()
        driver = ConcreteDriver(
            connection=AsyncMock(),
            protocol=AsyncMock(),
            history=history,
        )
        assert driver.history is history

    async def test_send_command(self) -> None:
        connection = AsyncMock()
        driver = ConcreteDriver(
            connection=connection,
            protocol=AsyncMock(),
            history=DeviceHistory(),
        )
        await driver._send_command(b"\x01\x02")
        connection.send_command.assert_awaited_once_with(b"\x01\x02")

    async def test_send_and_receive(self) -> None:
        connection = AsyncMock()
        connection.send_and_receive = AsyncMock(return_value=b"\x0a\x00\x00\x00")
        driver = ConcreteDriver(
            connection=connection,
            protocol=AsyncMock(),
            history=DeviceHistory(),
        )
        result = await driver.do_something()
        connection.send_and_receive.assert_awaited_once_with(b"\x01", 4, 2.0)
        assert result == b"\x0a\x00\x00\x00"
```

**Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/core/test_protocol.py tests/core/test_driver.py -v`
Expected: FAIL — modules not found

**Step 3: Implement abstractions**

`src/lab_devices/core/protocol.py`:

```python
from abc import ABC, abstractmethod


class BaseProtocolHandler(ABC):
    @abstractmethod
    def build_identification_probe(self) -> bytes: ...

    @abstractmethod
    def parse_identification_response(self, data: bytes) -> bool: ...

    @abstractmethod
    def get_identification_response_size(self) -> int: ...
```

`src/lab_devices/core/driver.py`:

```python
from abc import ABC

from lab_devices.core.connection import SerialConnection
from lab_devices.core.history import DeviceHistory
from lab_devices.core.protocol import BaseProtocolHandler


class BaseDeviceDriver(ABC):
    def __init__(
        self,
        connection: SerialConnection,
        protocol: BaseProtocolHandler,
        history: DeviceHistory,
    ) -> None:
        self._connection = connection
        self._protocol = protocol
        self._history = history

    @property
    def history(self) -> DeviceHistory:
        return self._history

    @property
    def port(self) -> str:
        return self._connection.port

    async def _send_command(self, data: bytes) -> None:
        await self._connection.send_command(data)

    async def _send_and_receive(
        self, data: bytes, response_size: int, timeout: float = 2.0
    ) -> bytes:
        return await self._connection.send_and_receive(data, response_size, timeout)
```

`src/lab_devices/core/connection.py` (stub — full implementation in Task 5):

```python
import asyncio

from lab_devices.exceptions import DeviceConnectionError, DeviceTimeoutError


class SerialConnection:
    def __init__(self, port: str, baudrate: int = 9600) -> None:
        self._port = port
        self._baudrate = baudrate

    @property
    def port(self) -> str:
        return self._port

    @property
    def is_connected(self) -> bool:
        return False

    async def connect(self) -> None:
        raise NotImplementedError

    async def disconnect(self) -> None:
        raise NotImplementedError

    async def send_command(self, data: bytes) -> None:
        raise NotImplementedError

    async def send_and_receive(
        self, data: bytes, response_size: int, timeout: float = 2.0
    ) -> bytes:
        raise NotImplementedError
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/core/test_protocol.py tests/core/test_driver.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/lab_devices/core/protocol.py src/lab_devices/core/driver.py src/lab_devices/core/connection.py tests/core/test_protocol.py tests/core/test_driver.py
git commit -m "feat: add BaseProtocolHandler, BaseDeviceDriver ABCs, and SerialConnection stub"
```

---

### Task 5: SerialConnection

**Files:**
- Modify: `src/lab_devices/core/connection.py`
- Create: `tests/core/test_connection.py`

**Step 1: Write failing tests**

Tests use `pty.openpty()` to create virtual PTY pairs for real async I/O testing.

`tests/core/test_connection.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/core/test_connection.py -v`
Expected: FAIL — NotImplementedError from stub

**Step 3: Implement SerialConnection**

Replace `src/lab_devices/core/connection.py`:

```python
import asyncio
from typing import Self

from aioserial import AioSerial

from lab_devices.exceptions import DeviceConnectionError, DeviceTimeoutError


class SerialConnection:
    def __init__(self, port: str, baudrate: int = 9600) -> None:
        self._port = port
        self._baudrate = baudrate
        self._serial: AioSerial | None = None
        self._lock = asyncio.Lock()

    @property
    def port(self) -> str:
        return self._port

    @property
    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    async def connect(self) -> None:
        try:
            self._serial = AioSerial(port=self._port, baudrate=self._baudrate)
        except Exception as e:
            raise DeviceConnectionError(
                f"Failed to open {self._port}: {e}"
            ) from e

    async def disconnect(self) -> None:
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
        self._serial = None

    async def send_command(self, data: bytes) -> None:
        if self._serial is None:
            raise DeviceConnectionError("Not connected")
        async with self._lock:
            await self._serial.write_async(data)

    async def send_and_receive(
        self, data: bytes, response_size: int, timeout: float = 2.0
    ) -> bytes:
        if self._serial is None:
            raise DeviceConnectionError("Not connected")
        async with self._lock:
            await self._serial.write_async(data)
            try:
                response = await asyncio.wait_for(
                    self._serial.read_async(response_size),
                    timeout=timeout,
                )
            except asyncio.TimeoutError as e:
                raise DeviceTimeoutError(
                    f"Read timeout on {self._port}"
                ) from e
            return bytes(response)

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.disconnect()
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/core/test_connection.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/lab_devices/core/connection.py tests/core/test_connection.py
git commit -m "feat: implement SerialConnection with async read/write over aioserial"
```

---

### Task 6: PumpLegacyProtocol

**Files:**
- Create: `src/lab_devices/devices/pump/protocol.py`
- Create: `tests/devices/pump/test_protocol.py`

**Step 1: Write failing tests**

`tests/devices/pump/test_protocol.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/devices/pump/test_protocol.py -v`
Expected: FAIL — module not found

**Step 3: Implement PumpLegacyProtocol**

`src/lab_devices/devices/pump/protocol.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/devices/pump/test_protocol.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/lab_devices/devices/pump/protocol.py tests/devices/pump/test_protocol.py
git commit -m "feat: implement PumpLegacyProtocol for 5-byte binary command encoding"
```

---

### Task 7: PumpDriver

**Files:**
- Create: `src/lab_devices/devices/pump/driver.py`
- Create: `tests/devices/pump/test_driver.py`

**Step 1: Write failing tests**

`tests/devices/pump/test_driver.py`:

```python
from unittest.mock import AsyncMock

from lab_devices.core.history import DeviceHistory
from lab_devices.devices.pump.driver import PumpDriver
from lab_devices.devices.pump.protocol import PumpLegacyProtocol
from lab_devices.models.device import Direction


def make_pump() -> tuple[PumpDriver, AsyncMock]:
    connection = AsyncMock()
    connection.port = "/dev/ttyUSB0"
    protocol = PumpLegacyProtocol()
    history = DeviceHistory()
    driver = PumpDriver(connection=connection, protocol=protocol, history=history)
    return driver, connection


class TestPumpDriver:
    async def test_start_rotation_left(self) -> None:
        pump, conn = make_pump()
        await pump.start_rotation(speed=5, direction=Direction.LEFT)
        conn.send_command.assert_awaited_once_with(
            bytes([0x0B, 0x6F, 0x00, 0x05, 0x00])
        )

    async def test_start_rotation_right(self) -> None:
        pump, conn = make_pump()
        await pump.start_rotation(speed=10, direction=Direction.RIGHT)
        conn.send_command.assert_awaited_once_with(
            bytes([0x0C, 0x6F, 0x00, 0x0A, 0x00])
        )

    async def test_start_rotation_updates_state(self) -> None:
        pump, _ = make_pump()
        await pump.start_rotation(speed=5, direction=Direction.LEFT)
        state = pump.history.current_state()
        assert state is not None
        assert state.name == "rotating"
        assert state.params["direction"] == "left"
        assert state.params["speed"] == 5

    async def test_stop_rotation(self) -> None:
        pump, conn = make_pump()
        await pump.start_rotation(speed=5, direction=Direction.LEFT)
        await pump.stop_rotation()
        conn.send_command.assert_awaited_with(
            bytes([0x0B, 0x6F, 0x00, 0x00, 0x00])
        )

    async def test_stop_rotation_ends_state(self) -> None:
        pump, _ = make_pump()
        await pump.start_rotation(speed=5, direction=Direction.LEFT)
        await pump.stop_rotation()
        assert pump.history.current_state() is None

    async def test_set_rotation_speed(self) -> None:
        pump, conn = make_pump()
        await pump.set_rotation_speed(3)
        conn.send_command.assert_awaited_once_with(
            bytes([0x0A, 0x00, 0x00, 0x03, 0x00])
        )

    async def test_set_rotation_speed_records_event(self) -> None:
        pump, _ = make_pump()
        await pump.set_rotation_speed(3)
        events = pump.history.get_events("set_speed")
        assert len(events) == 1
        assert events[0].params["speed"] == 3

    async def test_pour_volume_left(self) -> None:
        pump, conn = make_pump()
        await pump.pour_volume(direction=Direction.LEFT, volume=50)
        conn.send_command.assert_awaited_once_with(
            bytes([0x10, 0x00, 0x00, 0x00, 0x32])
        )

    async def test_pour_volume_right(self) -> None:
        pump, conn = make_pump()
        await pump.pour_volume(direction=Direction.RIGHT, volume=100)
        conn.send_command.assert_awaited_once_with(
            bytes([0x11, 0x00, 0x00, 0x00, 0x64])
        )

    async def test_pour_volume_records_event(self) -> None:
        pump, _ = make_pump()
        await pump.set_rotation_speed(5)
        await pump.pour_volume(direction=Direction.LEFT, volume=50)
        events = pump.history.get_events("pour_volume")
        assert len(events) == 1
        assert events[0].params["direction"] == "left"
        assert events[0].params["volume"] == 50
        assert events[0].params["speed"] == 5
```

**Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/devices/pump/test_driver.py -v`
Expected: FAIL — module not found

**Step 3: Implement PumpDriver**

`src/lab_devices/devices/pump/driver.py`:

```python
from lab_devices.core.connection import SerialConnection
from lab_devices.core.driver import BaseDeviceDriver
from lab_devices.core.history import DeviceHistory
from lab_devices.devices.pump.protocol import PumpLegacyProtocol
from lab_devices.models.device import Direction


class PumpDriver(BaseDeviceDriver):
    def __init__(
        self,
        connection: SerialConnection,
        protocol: PumpLegacyProtocol,
        history: DeviceHistory,
    ) -> None:
        super().__init__(connection, protocol, history)
        self._protocol: PumpLegacyProtocol = protocol
        self._stored_speed: int = 0

    async def start_rotation(self, speed: int, direction: Direction) -> None:
        if direction == Direction.LEFT:
            data = self._protocol.encode_rotate_left(speed)
        else:
            data = self._protocol.encode_rotate_right(speed)
        await self._send_command(data)
        self._history.start_state(
            "rotating", {"direction": direction.value, "speed": speed}
        )

    async def stop_rotation(self) -> None:
        data = self._protocol.encode_rotate_left(0)
        await self._send_command(data)
        self._history.end_current_state()

    async def set_rotation_speed(self, speed: int) -> None:
        data = self._protocol.encode_set_speed(speed)
        await self._send_command(data)
        self._stored_speed = speed
        self._history.record_event("set_speed", {"speed": speed})

    async def pour_volume(self, direction: Direction, volume: int) -> None:
        if direction == Direction.LEFT:
            data = self._protocol.encode_pour_left(volume)
        else:
            data = self._protocol.encode_pour_right(volume)
        await self._send_command(data)
        self._history.record_event(
            "pour_volume",
            {
                "direction": direction.value,
                "speed": self._stored_speed,
                "volume": volume,
            },
        )
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/devices/pump/test_driver.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/lab_devices/devices/pump/driver.py tests/devices/pump/test_driver.py
git commit -m "feat: implement PumpDriver with rotation, speed, and pour commands"
```

---

### Task 8: DensitometerLegacyProtocol

**Files:**
- Create: `src/lab_devices/devices/densitometer/protocol.py`
- Create: `tests/devices/densitometer/test_protocol.py`

**Step 1: Write failing tests**

`tests/devices/densitometer/test_protocol.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/devices/densitometer/test_protocol.py -v`
Expected: FAIL — module not found

**Step 3: Implement DensitometerLegacyProtocol**

`src/lab_devices/devices/densitometer/protocol.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/devices/densitometer/test_protocol.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/lab_devices/devices/densitometer/protocol.py tests/devices/densitometer/test_protocol.py
git commit -m "feat: implement DensitometerLegacyProtocol with value encoding/decoding"
```

---

### Task 9: DensitometerDriver

**Files:**
- Create: `src/lab_devices/devices/densitometer/driver.py`
- Create: `tests/devices/densitometer/test_driver.py`

**Step 1: Write failing tests**

`tests/devices/densitometer/test_driver.py`:

```python
from unittest.mock import AsyncMock

from lab_devices.core.history import DeviceHistory
from lab_devices.devices.densitometer.driver import DensitometerDriver
from lab_devices.devices.densitometer.protocol import DensitometerLegacyProtocol


def make_densitometer(
    measurement_delay_s: float = 0.01,
) -> tuple[DensitometerDriver, AsyncMock]:
    connection = AsyncMock()
    connection.port = "/dev/ttyUSB1"
    protocol = DensitometerLegacyProtocol()
    history = DeviceHistory()
    driver = DensitometerDriver(
        connection=connection,
        protocol=protocol,
        history=history,
        measurement_delay_s=measurement_delay_s,
    )
    return driver, connection


class TestDensitometerDriver:
    async def test_get_temperature(self) -> None:
        densitometer, conn = make_densitometer()
        # Response: 23 + 50/100 = 23.50
        conn.send_and_receive = AsyncMock(
            return_value=bytes([0x00, 0x00, 0x17, 0x32])
        )
        result = await densitometer.get_temperature()
        assert result == 23.50
        conn.send_and_receive.assert_awaited_once_with(
            bytes([0x4C, 0x00, 0x00, 0x00, 0x00]), 4, 2.0
        )

    async def test_get_temperature_records_event(self) -> None:
        densitometer, conn = make_densitometer()
        conn.send_and_receive = AsyncMock(
            return_value=bytes([0x00, 0x00, 0x17, 0x32])
        )
        await densitometer.get_temperature()
        events = densitometer.history.get_events("get_temperature")
        assert len(events) == 1
        assert events[0].params["temperature_c"] == 23.50

    async def test_get_od(self) -> None:
        densitometer, conn = make_densitometer()
        # Response: 0 + 42/100 = 0.42
        conn.send_and_receive = AsyncMock(
            return_value=bytes([0x00, 0x00, 0x00, 0x2A])
        )
        result = await densitometer.get_od()
        assert result == 0.42

    async def test_get_od_sends_start_then_read(self) -> None:
        densitometer, conn = make_densitometer()
        conn.send_and_receive = AsyncMock(
            return_value=bytes([0x00, 0x00, 0x00, 0x2A])
        )
        await densitometer.get_od()
        # Should have sent start measurement command
        conn.send_command.assert_awaited_once_with(
            bytes([0x4E, 0x04, 0x00, 0x00, 0x00])
        )
        # Should have sent OD read command
        conn.send_and_receive.assert_awaited_once_with(
            bytes([0x4F, 0x04, 0x00, 0x00, 0x00]), 4, 2.0
        )

    async def test_get_od_records_state_and_event(self) -> None:
        densitometer, conn = make_densitometer()
        conn.send_and_receive = AsyncMock(
            return_value=bytes([0x00, 0x00, 0x00, 0x2A])
        )
        await densitometer.get_od()
        # Should have transitioned through measuring_od state
        states = densitometer.history.get_states("measuring_od")
        assert len(states) == 1
        assert states[0].ended_at is not None
        # Should have recorded get_od event
        events = densitometer.history.get_events("get_od")
        assert len(events) == 1
        assert events[0].params["absorbance"] == 0.42

    async def test_get_od_no_state_after_completion(self) -> None:
        densitometer, conn = make_densitometer()
        conn.send_and_receive = AsyncMock(
            return_value=bytes([0x00, 0x00, 0x00, 0x2A])
        )
        await densitometer.get_od()
        assert densitometer.history.current_state() is None
```

**Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/devices/densitometer/test_driver.py -v`
Expected: FAIL — module not found

**Step 3: Implement DensitometerDriver**

`src/lab_devices/devices/densitometer/driver.py`:

```python
import asyncio

from lab_devices.core.connection import SerialConnection
from lab_devices.core.driver import BaseDeviceDriver
from lab_devices.core.history import DeviceHistory
from lab_devices.devices.densitometer.protocol import DensitometerLegacyProtocol


class DensitometerDriver(BaseDeviceDriver):
    def __init__(
        self,
        connection: SerialConnection,
        protocol: DensitometerLegacyProtocol,
        history: DeviceHistory,
        measurement_delay_s: float = 2.0,
    ) -> None:
        super().__init__(connection, protocol, history)
        self._protocol: DensitometerLegacyProtocol = protocol
        self._measurement_delay_s = measurement_delay_s

    async def get_temperature(self) -> float:
        data = self._protocol.encode_temperature_request()
        response = await self._send_and_receive(
            data, self._protocol.get_value_response_size()
        )
        temperature = self._protocol.decode_value(response)
        self._history.record_event(
            "get_temperature", {"temperature_c": temperature}
        )
        return temperature

    async def get_od(self) -> float:
        # Start measurement
        start_data = self._protocol.encode_start_measurement()
        await self._send_command(start_data)
        self._history.start_state("measuring_od")

        # Wait for measurement to complete
        await asyncio.sleep(self._measurement_delay_s)

        # Read OD value
        read_data = self._protocol.encode_od_request()
        response = await self._send_and_receive(
            read_data, self._protocol.get_value_response_size()
        )
        od = self._protocol.decode_value(response)

        self._history.end_current_state()
        self._history.record_event("get_od", {"absorbance": od})
        return od
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/devices/densitometer/test_driver.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/lab_devices/devices/densitometer/driver.py tests/devices/densitometer/test_driver.py
git commit -m "feat: implement DensitometerDriver with temperature and OD measurement"
```

---

### Task 10: Configuration

**Files:**
- Create: `src/lab_devices/config.py`
- Create: `tests/test_config.py`

**Step 1: Write failing tests**

`tests/test_config.py`:

```python
import os
import tempfile

from lab_devices.config import AppConfig, DensitometerConfig, DevicesConfig, DiscoveryConfig


class TestDiscoveryConfig:
    def test_defaults(self) -> None:
        config = DiscoveryConfig()
        assert config.extra_ports == []
        assert config.timeout_s == 1.0
        assert config.baudrate == 9600


class TestDensitometerConfig:
    def test_defaults(self) -> None:
        config = DensitometerConfig()
        assert config.measurement_delay_s == 2.0


class TestDevicesConfig:
    def test_defaults(self) -> None:
        config = DevicesConfig()
        assert config.densitometer.measurement_delay_s == 2.0


class TestAppConfig:
    def test_defaults(self) -> None:
        config = AppConfig(yaml_file="nonexistent.yaml")
        assert config.discovery.timeout_s == 1.0
        assert config.devices.densitometer.measurement_delay_s == 2.0

    def test_from_yaml(self) -> None:
        yaml_content = """
discovery:
  extra_ports:
    - /dev/ttyUSB0
  timeout_s: 0.5
  baudrate: 115200

devices:
  densitometer:
    measurement_delay_s: 3.0
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()
            try:
                config = AppConfig(yaml_file=f.name)
                assert config.discovery.extra_ports == ["/dev/ttyUSB0"]
                assert config.discovery.timeout_s == 0.5
                assert config.discovery.baudrate == 115200
                assert config.devices.densitometer.measurement_delay_s == 3.0
            finally:
                os.unlink(f.name)
```

**Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_config.py -v`
Expected: FAIL — module not found

**Step 3: Implement configuration**

`src/lab_devices/config.py`:

```python
from pydantic import BaseModel
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, YamlConfigSettingsSource


class DiscoveryConfig(BaseModel):
    extra_ports: list[str] = []
    timeout_s: float = 1.0
    baudrate: int = 9600


class DensitometerConfig(BaseModel):
    measurement_delay_s: float = 2.0


class DevicesConfig(BaseModel):
    densitometer: DensitometerConfig = DensitometerConfig()


class AppConfig(BaseSettings):
    discovery: DiscoveryConfig = DiscoveryConfig()
    devices: DevicesConfig = DevicesConfig()
    yaml_file: str = "config.yaml"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            YamlConfigSettingsSource(settings_cls),
            env_settings,
        )
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_config.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/lab_devices/config.py tests/test_config.py
git commit -m "feat: add AppConfig with pydantic-settings and YAML support"
```

---

### Task 11: Discovery

**Files:**
- Create: `src/lab_devices/discovery.py`
- Create: `tests/test_discovery.py`

**Step 1: Write failing tests**

`tests/test_discovery.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_discovery.py -v`
Expected: FAIL — module not found

**Step 3: Implement discovery**

`src/lab_devices/discovery.py`:

```python
import asyncio

from serial.tools.list_ports import comports

from lab_devices.core.connection import SerialConnection
from lab_devices.core.protocol import BaseProtocolHandler
from lab_devices.devices.densitometer.protocol import DensitometerLegacyProtocol
from lab_devices.devices.pump.protocol import PumpLegacyProtocol
from lab_devices.exceptions import DeviceConnectionError, DeviceTimeoutError
from lab_devices.models.device import DeviceType, DiscoveredDevice

_KNOWN_PROTOCOLS: dict[DeviceType, type[BaseProtocolHandler]] = {
    DeviceType.PUMP: PumpLegacyProtocol,
    DeviceType.DENSITOMETER: DensitometerLegacyProtocol,
}


async def _probe_port(
    port: str,
    baudrate: int,
    timeout: float,
) -> DiscoveredDevice | None:
    for device_type, protocol_cls in _KNOWN_PROTOCOLS.items():
        protocol = protocol_cls()
        connection = SerialConnection(port, baudrate)
        try:
            await connection.connect()
            try:
                response = await connection.send_and_receive(
                    protocol.build_identification_probe(),
                    protocol.get_identification_response_size(),
                    timeout=timeout,
                )
                if protocol.parse_identification_response(response):
                    await connection.disconnect()
                    return DiscoveredDevice(device_type=device_type, port=port)
            finally:
                await connection.disconnect()
        except (DeviceTimeoutError, DeviceConnectionError):
            continue
    return None


async def discover_devices(
    ports: list[str] | None = None,
    extra_ports: list[str] | None = None,
    baudrate: int = 9600,
    timeout: float = 1.0,
) -> list[DiscoveredDevice]:
    if ports is None:
        ports = [p.device for p in comports()]
    if extra_ports:
        all_ports = list(set(ports + extra_ports))
    else:
        all_ports = ports

    if not all_ports:
        return []

    tasks = [_probe_port(port, baudrate, timeout) for port in all_ports]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    devices: list[DiscoveredDevice] = []
    for result in results:
        if isinstance(result, DiscoveredDevice):
            devices.append(result)
    return devices
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_discovery.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/lab_devices/discovery.py tests/test_discovery.py
git commit -m "feat: add device discovery with auto-detect and configurable ports"
```

---

### Task 12: DeviceManager

**Files:**
- Create: `src/lab_devices/manager.py`
- Create: `tests/test_manager.py`

**Step 1: Write failing tests**

`tests/test_manager.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_manager.py -v`
Expected: FAIL — module not found

**Step 3: Implement DeviceManager**

`src/lab_devices/manager.py`:

```python
from typing import Self

from lab_devices.config import AppConfig
from lab_devices.core.connection import SerialConnection
from lab_devices.core.driver import BaseDeviceDriver
from lab_devices.core.history import DeviceHistory
from lab_devices.devices.densitometer.driver import DensitometerDriver
from lab_devices.devices.densitometer.protocol import DensitometerLegacyProtocol
from lab_devices.devices.pump.driver import PumpDriver
from lab_devices.devices.pump.protocol import PumpLegacyProtocol
from lab_devices.discovery import discover_devices
from lab_devices.exceptions import DeviceNotFoundError
from lab_devices.models.device import DeviceType


class DeviceManager:
    def __init__(self, config: AppConfig | None = None) -> None:
        self._config = config or AppConfig()
        self._devices: dict[str, BaseDeviceDriver] = {}
        self._connections: list[SerialConnection] = []

    @classmethod
    async def create(cls, config: AppConfig | None = None) -> Self:
        return cls(config)

    async def discover(
        self, ports: list[str] | None = None
    ) -> dict[str, BaseDeviceDriver]:
        discovered = await discover_devices(
            ports=ports,
            extra_ports=self._config.discovery.extra_ports,
            baudrate=self._config.discovery.baudrate,
            timeout=self._config.discovery.timeout_s,
        )

        type_counts: dict[DeviceType, int] = {}

        for device_info in discovered:
            count = type_counts.get(device_info.device_type, 0)
            name = f"{device_info.device_type.value}_{count}"
            type_counts[device_info.device_type] = count + 1

            connection = SerialConnection(
                device_info.port,
                self._config.discovery.baudrate,
            )
            await connection.connect()
            self._connections.append(connection)

            history = DeviceHistory()
            driver = self._create_driver(
                device_info.device_type, connection, history
            )
            self._devices[name] = driver

        return dict(self._devices)

    def _create_driver(
        self,
        device_type: DeviceType,
        connection: SerialConnection,
        history: DeviceHistory,
    ) -> BaseDeviceDriver:
        if device_type == DeviceType.PUMP:
            protocol = PumpLegacyProtocol()
            return PumpDriver(connection, protocol, history)
        if device_type == DeviceType.DENSITOMETER:
            protocol = DensitometerLegacyProtocol()
            return DensitometerDriver(
                connection,
                protocol,
                history,
                measurement_delay_s=self._config.devices.densitometer.measurement_delay_s,
            )
        msg = f"Unknown device type: {device_type}"
        raise ValueError(msg)

    def get_device(self, name: str) -> BaseDeviceDriver:
        if name not in self._devices:
            raise DeviceNotFoundError(f"Device not found: {name}")
        return self._devices[name]

    def get_pump(self, name: str) -> PumpDriver:
        device = self.get_device(name)
        if not isinstance(device, PumpDriver):
            raise DeviceNotFoundError(f"Device {name} is not a pump")
        return device

    def get_densitometer(self, name: str) -> DensitometerDriver:
        device = self.get_device(name)
        if not isinstance(device, DensitometerDriver):
            raise DeviceNotFoundError(f"Device {name} is not a densitometer")
        return device

    def list_devices(self) -> dict[str, DeviceType]:
        result: dict[str, DeviceType] = {}
        for name, driver in self._devices.items():
            if isinstance(driver, PumpDriver):
                result[name] = DeviceType.PUMP
            elif isinstance(driver, DensitometerDriver):
                result[name] = DeviceType.DENSITOMETER
        return result

    async def close(self) -> None:
        for connection in self._connections:
            await connection.disconnect()
        self._connections.clear()
        self._devices.clear()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_manager.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/lab_devices/manager.py tests/test_manager.py
git commit -m "feat: implement DeviceManager with discovery, lifecycle, and typed accessors"
```

---

### Task 13: Public API Exports and Full Test Suite

**Files:**
- Modify: `src/lab_devices/__init__.py`

**Step 1: Add public API exports**

`src/lab_devices/__init__.py`:

```python
from lab_devices.config import AppConfig
from lab_devices.core.connection import SerialConnection
from lab_devices.core.history import DeviceHistory
from lab_devices.devices.densitometer.driver import DensitometerDriver
from lab_devices.devices.pump.driver import PumpDriver
from lab_devices.discovery import discover_devices
from lab_devices.exceptions import (
    DeviceConnectionError,
    DeviceNotFoundError,
    DeviceTimeoutError,
    LabDevicesError,
    UnexpectedResponseError,
)
from lab_devices.manager import DeviceManager
from lab_devices.models.device import DeviceType, Direction, DiscoveredDevice
from lab_devices.models.events import InstantEvent, StateRecord

__all__ = [
    "AppConfig",
    "DensitometerDriver",
    "DeviceConnectionError",
    "DeviceHistory",
    "DeviceManager",
    "DeviceNotFoundError",
    "DeviceTimeoutError",
    "DeviceType",
    "Direction",
    "DiscoveredDevice",
    "InstantEvent",
    "LabDevicesError",
    "PumpDriver",
    "SerialConnection",
    "StateRecord",
    "UnexpectedResponseError",
    "discover_devices",
]
```

**Step 2: Run full test suite**

Run: `poetry run pytest -v`
Expected: All tests PASS

**Step 3: Run linter and type checker**

Run: `task lint && task typecheck`
Expected: No errors. If mypy reports errors, fix type annotations as needed. Common fixes:
- Add `# type: ignore[...]` for aioserial (no stubs)
- Adjust return types if mypy infers differently

**Step 4: Commit**

```bash
git add src/lab_devices/__init__.py
git commit -m "feat: add public API exports in __init__.py"
```

---

### Task 14: Protocol Documentation

**Files:**
- Create: `docs/protocols/pump_legacy.md`
- Create: `docs/protocols/pump_target.md`
- Create: `docs/protocols/densitometer_legacy.md`
- Create: `docs/protocols/densitometer_target.md`

**Step 1: Copy protocol docs from reference project**

Copy the four protocol documentation files from `/Users/khamitovdr/virtual_lab_devices/docs/protocols/` into this project's `docs/protocols/` directory.

**Step 2: Commit**

```bash
git add docs/protocols/
git commit -m "docs: add protocol specifications for pump and densitometer"
```

---

### Task 15: Final Quality Check

**Step 1: Run full quality check**

Run: `task check`
Expected: lint, typecheck, and all tests pass

**Step 2: Format code**

Run: `task format`

**Step 3: Run check again after formatting**

Run: `task check`
Expected: All pass

**Step 4: Commit any formatting changes**

```bash
git add -A
git commit -m "chore: format code with ruff"
```

---

## Summary

| Task | Component | Key Files |
|------|-----------|-----------|
| 1 | Project scaffolding | pyproject.toml, Taskfile.yml, package structure |
| 2 | Data models + exceptions | models/events.py, models/device.py, exceptions.py |
| 3 | DeviceHistory | core/history.py |
| 4 | Core ABCs | core/protocol.py, core/driver.py, core/connection.py (stub) |
| 5 | SerialConnection | core/connection.py |
| 6 | PumpLegacyProtocol | devices/pump/protocol.py |
| 7 | PumpDriver | devices/pump/driver.py |
| 8 | DensitometerLegacyProtocol | devices/densitometer/protocol.py |
| 9 | DensitometerDriver | devices/densitometer/driver.py |
| 10 | Configuration | config.py |
| 11 | Discovery | discovery.py |
| 12 | DeviceManager | manager.py |
| 13 | Public API exports | __init__.py |
| 14 | Protocol docs | docs/protocols/*.md |
| 15 | Final quality check | All files |

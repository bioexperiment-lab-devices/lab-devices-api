# Lab Devices — Design Document

**Date:** 2026-02-17
**Status:** Approved

## Goal

Create a Python 3.14 async API library (`lab_devices`) for communicating with laboratory hardware devices over serial ports. The library discovers devices, creates typed driver instances, and manages their lifecycle. It supports both physical and virtual serial ports, tracks device state history, and is designed for protocol swappability when hardware firmware is upgraded.

## Usage Scenarios

1. **Manual** — discover devices, send commands, perform measurements interactively
2. **Experiment pipelines** — a future `Experiment` package uses this library to build automated pipelines based on time and measurement conditions

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Package name | `lab_devices` | Short, clear; REST API layer built on top later |
| Async serial library | aioserial | Same as reference project, simple async wrapper over pyserial |
| Architecture | Layered: Connection → Protocol → Driver → History | Clean protocol swap, independently testable layers |
| Discovery | Auto-detect ports + config overrides | pyserial list_ports + configurable extra ports |
| History | Device state mirror (StateRecord/InstantEvent) | Same model as virtual_lab_devices emulator |
| Error handling | Typed exceptions | Clean async/await error propagation |
| Lifecycle | DeviceManager with async context manager | Handles discovery, access, cleanup |
| Concurrency | asyncio.Lock per connection | Prevents garbled serial communication |
| Config | pydantic-settings with YAML | Consistent with reference project |
| Tooling | Poetry, pyproject.toml, go-task, ruff, mypy strict | Enforced code quality |
| Protocol strategy | Legacy only, document target | Implement current binary protocol; swap ProtocolHandler later |

## Architecture

### Layered Design

```
SerialConnection ←→ ProtocolHandler ←→ DeviceDriver ←→ History
                                            ↑
                                      DeviceManager
                                            ↑
                                        Discovery
```

1. **SerialConnection** — async read/write over aioserial with asyncio.Lock
2. **ProtocolHandler** — encodes commands to bytes, decodes responses (replaceable per protocol version)
3. **DeviceDriver** — typed public API per device type, manages state history
4. **DeviceHistory** — in-memory state/event store

**DeviceManager** handles discovery and lifecycle. **Discovery** probes ports with identification signals.

### Project Structure

```
lab_devices_api/
├── pyproject.toml
├── Taskfile.yml
├── config.yaml
├── .gitignore
├── .python-version
├── src/
│   └── lab_devices/
│       ├── __init__.py
│       ├── config.py
│       ├── exceptions.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── events.py
│       │   └── device.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── connection.py
│       │   ├── protocol.py
│       │   ├── driver.py
│       │   └── history.py
│       ├── devices/
│       │   ├── __init__.py
│       │   ├── pump/
│       │   │   ├── __init__.py
│       │   │   ├── protocol.py
│       │   │   └── driver.py
│       │   └── densitometer/
│       │       ├── __init__.py
│       │       ├── protocol.py
│       │       └── driver.py
│       ├── discovery.py
│       └── manager.py
├── tests/
│   ├── conftest.py
│   ├── core/
│   │   ├── test_connection.py
│   │   ├── test_protocol.py
│   │   ├── test_history.py
│   │   └── test_driver.py
│   ├── devices/
│   │   ├── pump/
│   │   │   ├── test_protocol.py
│   │   │   └── test_driver.py
│   │   └── densitometer/
│   │       ├── test_protocol.py
│   │       └── test_driver.py
│   ├── test_discovery.py
│   ├── test_config.py
│   └── test_manager.py
└── docs/
    └── protocols/
        ├── pump_legacy.md
        ├── pump_target.md
        ├── densitometer_legacy.md
        └── densitometer_target.md
```

## Core Components

### SerialConnection (`core/connection.py`)

Async wrapper around aioserial. Abstracts physical vs virtual serial ports.

- `__init__(port: str, baudrate: int = 9600)` — stores config, doesn't connect yet
- `async connect()` — opens aioserial connection
- `async disconnect()` — closes connection
- `async write(data: bytes)` — send bytes
- `async read(size: int, timeout: float = 2.0) -> bytes` — read exact number of bytes with timeout
- `is_connected: bool` — property
- Implements async context manager
- Uses `asyncio.Lock` internally to serialize access per connection

### BaseProtocolHandler (`core/protocol.py`) — ABC

Translates between typed commands and raw bytes. One implementation per device × protocol version.

```python
class BaseProtocolHandler(ABC):
    @abstractmethod
    def build_identification_probe(self) -> bytes: ...

    @abstractmethod
    def parse_identification_response(self, data: bytes) -> bool: ...

    @abstractmethod
    def get_expected_response_size(self) -> int: ...
```

Device-specific handlers add encode/decode methods for each command.

### BaseDeviceDriver (`core/driver.py`) — ABC

Typed public API. Composes connection + protocol + history.

```python
class BaseDeviceDriver(ABC):
    def __init__(self, connection: SerialConnection, protocol: BaseProtocolHandler, history: DeviceHistory): ...

    async def _send_command(self, data: bytes, response_size: int | None = None) -> bytes | None:
        """Send bytes, optionally read response. Uses connection lock."""

    @property
    def history(self) -> DeviceHistory: ...

    @property
    def port(self) -> str: ...
```

### DeviceHistory (`core/history.py`)

In-memory store of StateRecord and InstantEvent.

- `start_state(name, params)` — begin new state, end previous
- `end_current_state()` — mark current state as ended
- `record_event(name, params)` — record point-in-time event
- `current_state() -> StateRecord | None`
- `get_states(name?) -> list[StateRecord]`
- `get_events(name?) -> list[InstantEvent]`
- `export() -> dict` — JSON-serializable for future REST API

## Data Models

### StateRecord (`models/events.py`)

- `name: str` — state name (e.g., "rotating")
- `params: dict[str, float | str]` — state parameters
- `started_at: datetime`
- `ended_at: datetime | None` — None means still active

### InstantEvent (`models/events.py`)

- `name: str` — event name (e.g., "get_temperature")
- `params: dict[str, float | str]` — event parameters
- `timestamp: datetime`

### DeviceType (`models/device.py`)

```python
class DeviceType(str, Enum):
    PUMP = "pump"
    DENSITOMETER = "densitometer"
```

### Direction (`models/device.py`)

```python
class Direction(str, Enum):
    LEFT = "left"
    RIGHT = "right"
```

## Device Implementations

### Pump

**States:** `idle`, `rotating` (direction + speed)

**Driver methods:**
- `start_rotation(speed: int, direction: Direction) -> None`
- `stop_rotation() -> None`
- `set_rotation_speed(speed: int) -> None`
- `pour_volume(direction: Direction, volume: int) -> None`

**Legacy protocol (5-byte commands, no responses):**

| Command | Bytes |
|---------|-------|
| Identification probe | `[0x01, 0x02, 0x03, 0x04, 0xB5]` |
| Identification response | `[0x0A, 0x00, 0x00, 0x00]` (4 bytes) |
| Rotate left | `[0x0B, 0x6F, 0x00, speed, 0x00]` |
| Rotate right | `[0x0C, 0x6F, 0x00, speed, 0x00]` |
| Set speed | `[0x0A, 0x00, 0x00, speed, 0x00]` |
| Pour left | `[0x10, 0x00, 0x00, 0x00, volume]` |
| Pour right | `[0x11, 0x00, 0x00, 0x00, volume]` |

### Densitometer

**States:** `idle`, `measuring_od`

**Events:** `get_temperature`, `get_od`

**Driver methods:**
- `get_temperature() -> float`
- `get_od() -> float` — compound: start measurement, wait delay, read OD

**Legacy protocol (5-byte commands, 4-byte responses):**

| Command | Bytes |
|---------|-------|
| Identification probe | `[0x01, 0x02, 0x03, 0x04, 0x00]` |
| Identification response | `[0x46, 0x00, 0x00, 0x00]` (4 bytes) |
| Temperature request | `[0x4C, 0x00, 0x00, 0x00, 0x00]` |
| Start OD measurement | `[0x4E, 0x04, 0x00, 0x00, 0x00]` |
| OD request | `[0x4F, 0x04, 0x00, 0x00, 0x00]` |

**Value decoding:** `value = float(a3) + float(a4) / 100`

## Discovery

```python
async def discover_devices(
    ports: list[str] | None = None,
    timeout: float = 1.0,
) -> list[DiscoveredDevice]:
```

1. Get port list: auto-detect via `serial.tools.list_ports`, merge with config `extra_ports`
2. For each port, send identification probes for all known device types
3. Send probe, read response with timeout, check if it matches
4. Return list of `DiscoveredDevice(device_type, port)`
5. Ports probed concurrently via asyncio.gather

## DeviceManager

```python
class DeviceManager:
    @classmethod
    async def create(cls, config: AppConfig | None = None) -> Self: ...
    async def discover(self, ports: list[str] | None = None) -> dict[str, BaseDeviceDriver]: ...
    def get_device(self, name: str) -> BaseDeviceDriver: ...
    def get_pump(self, name: str) -> PumpDriver: ...
    def get_densitometer(self, name: str) -> DensitometerDriver: ...
    def list_devices(self) -> dict[str, DeviceType]: ...
    async def close(self) -> None: ...
    async def __aenter__(self) -> Self: ...
    async def __aexit__(...) -> None: ...
```

## Exceptions

```python
class LabDevicesError(Exception): ...
class DeviceTimeoutError(LabDevicesError): ...
class DeviceNotFoundError(LabDevicesError): ...
class ConnectionError(LabDevicesError): ...
class UnexpectedResponseError(LabDevicesError): ...
```

## Configuration

```yaml
# config.yaml
discovery:
  extra_ports: []
  timeout_s: 1.0
  baudrate: 9600

devices:
  densitometer:
    measurement_delay_s: 2.0
```

Loaded via pydantic-settings with YAML support.

## Tooling

- **Poetry** for dependency management
- **pyproject.toml** for all config (ruff, mypy strict, pytest)
- **go-task** Taskfile.yml: `install`, `lint`, `format`, `typecheck`, `test`, `check`
- **Runtime deps:** aioserial, pyserial, pydantic, pydantic-settings[yaml]
- **Dev deps:** pytest, pytest-asyncio, mypy, ruff

## Adding New Devices

1. Create `devices/<name>/protocol.py` — subclass `BaseProtocolHandler`
2. Create `devices/<name>/driver.py` — subclass `BaseDeviceDriver`
3. Register in discovery (add protocol handler to probe list)
4. Add creation branch in DeviceManager
5. Add tests

## Protocol Migration

When hardware firmware is upgraded:
1. Create `devices/<name>/protocol_v2.py` — new `BaseProtocolHandler` subclass implementing JSON framing
2. Swap protocol handler in DeviceManager factory — no changes to driver or history layers
3. Target protocol specs documented in `docs/protocols/*_target.md`

## Future Considerations

- REST API layer built on top of DeviceManager (out of scope)
- Experiment pipeline package uses DeviceManager for automated workflows (out of scope)
- Windows support: aioserial/pyserial handle cross-platform; no Unix-specific code in this library
- History export via `DeviceHistory.export()` provides JSON data for future API

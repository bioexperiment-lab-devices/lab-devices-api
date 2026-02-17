# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
task install          # Install dependencies via poetry
task check            # Run lint + typecheck + tests (use before committing)
task lint             # Ruff linter: poetry run ruff check src tests
task format           # Ruff formatter: poetry run ruff format src tests
task typecheck        # Mypy strict: poetry run mypy src
task test             # Full test suite: poetry run pytest

# Single test file or test
poetry run pytest tests/devices/pump/test_driver.py -v
poetry run pytest tests/test_discovery.py::TestProbePort::test_probe_finds_pump -v
```

## Architecture

Async Python 3.14 library for communicating with laboratory hardware devices over serial ports. Layered architecture with swappable protocol handlers to support migrating from legacy binary protocols to future JSON protocols.

### Layer stack

```
SerialConnection → ProtocolHandler → DeviceDriver → DeviceHistory
                                          ↑
                              DeviceManager (discovery + lifecycle)
                                          ↑
                                    AppConfig (YAML)
```

**SerialConnection** (`core/connection.py`) — async wrapper around aioserial with `asyncio.Lock` per connection. Supports fire-and-forget (`send_command`) and request/response (`send_and_receive` with timeout). Async context manager.

**BaseProtocolHandler** (`core/protocol.py`) — ABC defining identification probe/response methods. Each device has a concrete protocol (e.g., `PumpLegacyProtocol`, `DensitometerLegacyProtocol`). Protocols are pure encoders/decoders with no I/O. Legacy protocols use 5-byte binary frames.

**BaseDeviceDriver** (`core/driver.py`) — composes connection + protocol + history. Uses runtime `type(self)` guard instead of `@abstractmethod` (suppressed via `noqa: B024`). Subclasses (`PumpDriver`, `DensitometerDriver`) expose typed async methods.

**DeviceHistory** (`core/history.py`) — in-memory state/event tracker. States have start/end times (e.g., "rotating"). Events are instant (e.g., "get_temperature"). Both use pydantic models (`StateRecord`, `InstantEvent`).

**Discovery** (`discovery.py`) — probes serial ports concurrently with `asyncio.gather`, trying each known protocol's identification handshake. Returns `list[DiscoveredDevice]`. Auto-detects via `serial.tools.list_ports.comports()` or accepts explicit port lists.

**DeviceManager** (`manager.py`) — orchestrates discovery, creates driver instances named `{type}_{index}` (e.g., `pump_0`), manages connection lifecycle. Typed accessors: `get_pump()`, `get_densitometer()`. Async context manager for cleanup.

**AppConfig** (`config.py`) — pydantic-settings with YAML source (`config.yaml`). Priority: init kwargs > YAML > env vars.

### Adding a new device

1. Create `src/lab_devices/devices/<name>/protocol.py` — subclass `BaseProtocolHandler`, implement identification and command encoding methods
2. Create `src/lab_devices/devices/<name>/driver.py` — subclass `BaseDeviceDriver`, add typed async methods
3. Add `DeviceType.<NAME>` to `models/device.py`
4. Register protocol in `discovery.py::_KNOWN_PROTOCOLS`
5. Add factory branch in `manager.py::_create_driver`
6. Export from `__init__.py`

### Testing patterns

- **Protocol tests**: Pure unit tests, no mocking needed (encode/decode bytes)
- **Driver tests**: Use `AsyncMock` for connection, real protocol and history instances
- **Connection tests**: Use PTY pairs (`pty.openpty()`) for real serial I/O without hardware
- **Discovery/Manager tests**: Patch `SerialConnection` and `comports` with mocks
- pytest-asyncio with `asyncio_mode = "auto"` — async tests need no decorator

### Protocol documentation

Protocol specs for both legacy (current) and target (future JSON) protocols are in `docs/protocols/`.

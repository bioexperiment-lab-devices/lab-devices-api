# lab-devices

Async Python library for discovering and controlling laboratory hardware devices over serial ports.

Supports peristaltic pumps and densitometers with a layered architecture designed for adding new devices and swapping communication protocols.

## Requirements

- Python 3.14+
- [Poetry](https://python-poetry.org/)
- [go-task](https://taskfile.dev/) (optional, for development automation)

## Installation

```bash
# Clone and install
git clone <repo-url> && cd lab_devices_api
poetry install
```

## Configuration

The library reads settings from `config.yaml` in the working directory. All values have sensible defaults and can be overridden via the YAML file or environment variables.

```yaml
discovery:
  extra_ports: []       # Additional serial ports to scan beyond auto-detected ones
  timeout_s: 1.0        # Identification probe timeout per port
  baudrate: 9600        # Serial baudrate for discovery and communication

devices:
  densitometer:
    measurement_delay_s: 2.0  # Delay between starting OD measurement and reading result
```

You can also pass a custom config file path:

```python
from lab_devices import AppConfig, DeviceManager

config = AppConfig(yaml_file="/path/to/custom-config.yaml")
manager = await DeviceManager.create(config)
```

## Usage Examples

### Quick Start: Discover and Control Devices

```python
import asyncio
from lab_devices import DeviceManager, Direction

async def main():
    async with await DeviceManager.create() as manager:
        # Auto-discover all connected devices
        devices = await manager.discover()
        print(devices)  # {'pump_0': <PumpDriver>, 'densitometer_0': <DensitometerDriver>}

        # Control a pump
        pump = manager.get_pump("pump_0")
        await pump.start_rotation(speed=5, direction=Direction.LEFT)
        await pump.stop_rotation()

        # Read from a densitometer
        densitometer = manager.get_densitometer("densitometer_0")
        temp = await densitometer.get_temperature()
        print(f"Temperature: {temp} C")

asyncio.run(main())
```

### Discovery with Specific Ports

```python
import asyncio
from lab_devices import DeviceManager

async def main():
    manager = await DeviceManager.create()

    # Scan only specific ports instead of auto-detecting
    devices = await manager.discover(ports=["/dev/ttyUSB0", "/dev/ttyUSB1"])

    # List all discovered devices with their types
    for name, device_type in manager.list_devices().items():
        print(f"{name}: {device_type}")

    await manager.close()

asyncio.run(main())
```

### Discovery with Virtual Ports

Useful for testing with device emulators or virtual serial bridges:

```python
import asyncio
from lab_devices import AppConfig, DeviceManager

async def main():
    # Add virtual ports alongside auto-detected physical ones
    config = AppConfig(yaml_file="config.yaml")
    config.discovery.extra_ports = ["/tmp/virtual_pump", "/tmp/virtual_densitometer"]

    async with await DeviceManager.create(config) as manager:
        devices = await manager.discover()
        print(f"Found {len(devices)} devices")

asyncio.run(main())
```

### Pump Operations

```python
import asyncio
from lab_devices import DeviceManager, Direction

async def main():
    async with await DeviceManager.create() as manager:
        await manager.discover()
        pump = manager.get_pump("pump_0")

        # Continuous rotation
        await pump.start_rotation(speed=10, direction=Direction.RIGHT)
        await asyncio.sleep(5)
        await pump.stop_rotation()

        # Pour a specific volume
        # First set the speed that pour_volume will use
        await pump.set_rotation_speed(3)
        await pump.pour_volume(direction=Direction.LEFT, volume=50)

asyncio.run(main())
```

### Densitometer Measurements

```python
import asyncio
from lab_devices import DeviceManager

async def main():
    async with await DeviceManager.create() as manager:
        await manager.discover()
        densitometer = manager.get_densitometer("densitometer_0")

        # Single temperature reading
        temp = await densitometer.get_temperature()
        print(f"Temperature: {temp} C")

        # Optical density measurement (includes measurement delay)
        od = await densitometer.get_od()
        print(f"OD: {od}")

        # Periodic monitoring
        for _ in range(10):
            temp = await densitometer.get_temperature()
            od = await densitometer.get_od()
            print(f"T={temp} C, OD={od}")
            await asyncio.sleep(60)

asyncio.run(main())
```

### Device History and State Tracking

Every device tracks its operation history automatically:

```python
import asyncio
from lab_devices import DeviceManager, Direction

async def main():
    async with await DeviceManager.create() as manager:
        await manager.discover()
        pump = manager.get_pump("pump_0")

        await pump.start_rotation(speed=5, direction=Direction.LEFT)
        await pump.stop_rotation()
        await pump.set_rotation_speed(3)
        await pump.pour_volume(Direction.RIGHT, 100)

        # Query history
        history = pump.history

        # Get all rotation states (with start/end times)
        rotations = history.get_states("rotating")
        for state in rotations:
            print(f"Rotated {state.params['direction']} at speed {state.params['speed']}")
            print(f"  from {state.started_at} to {state.ended_at}")

        # Get all pour events
        pours = history.get_events("pour_volume")
        for event in pours:
            print(f"Poured {event.params['volume']} units {event.params['direction']}")

        # Check current device state (None if idle)
        print(f"Current state: {history.current_state()}")

        # Export full history as dict (for JSON serialization)
        data = history.export()
        print(data)  # {"states": [...], "events": [...]}

asyncio.run(main())
```

### Low-Level: Direct Serial Connection

For custom protocols or debugging:

```python
import asyncio
from lab_devices import SerialConnection

async def main():
    async with SerialConnection("/dev/ttyUSB0", baudrate=9600) as conn:
        # Fire-and-forget command
        await conn.send_command(bytes([0x0B, 0x6F, 0x00, 0x05, 0x00]))

        # Request-response with timeout
        response = await conn.send_and_receive(
            data=bytes([0x4C, 0x00, 0x00, 0x00, 0x00]),
            response_size=4,
            timeout=2.0,
        )
        print(f"Response: {response.hex()}")

asyncio.run(main())
```

### Error Handling

```python
import asyncio
from lab_devices import (
    DeviceManager,
    DeviceConnectionError,
    DeviceNotFoundError,
    DeviceTimeoutError,
)

async def main():
    async with await DeviceManager.create() as manager:
        try:
            await manager.discover(ports=["/dev/ttyUSB0"])
        except DeviceConnectionError as e:
            print(f"Cannot open port: {e}")

        try:
            pump = manager.get_pump("nonexistent")
        except DeviceNotFoundError as e:
            print(f"Device not found: {e}")

        try:
            densitometer = manager.get_densitometer("densitometer_0")
            await densitometer.get_temperature()
        except DeviceTimeoutError as e:
            print(f"Device did not respond: {e}")

asyncio.run(main())
```

## Development

```bash
task install        # Install all dependencies
task check          # Run lint + typecheck + tests
task lint           # Ruff linter
task format         # Ruff formatter
task typecheck      # Mypy in strict mode
task test           # pytest with async support

# Run a single test
poetry run pytest tests/devices/pump/test_driver.py::TestPumpDriver::test_start_rotation_left -v
```

## Supported Devices

| Device | Protocol | Commands |
|--------|----------|----------|
| Peristaltic pump | Legacy 5-byte binary | `start_rotation`, `stop_rotation`, `set_rotation_speed`, `pour_volume` |
| Densitometer | Legacy 5-byte binary | `get_temperature`, `get_od` |

Protocol specifications (including future JSON target protocols) are documented in `docs/protocols/`.

## Adding a New Device

1. Define a protocol handler in `src/lab_devices/devices/<name>/protocol.py` subclassing `BaseProtocolHandler`
2. Define a driver in `src/lab_devices/devices/<name>/driver.py` subclassing `BaseDeviceDriver`
3. Add a `DeviceType` enum value in `src/lab_devices/models/device.py`
4. Register the protocol in `src/lab_devices/discovery.py` (`_KNOWN_PROTOCOLS` dict)
5. Add a factory branch in `src/lab_devices/manager.py` (`_create_driver` method)
6. Export from `src/lab_devices/__init__.py`

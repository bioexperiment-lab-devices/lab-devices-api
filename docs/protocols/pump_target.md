# Pump — Target Protocol (Future)

## Overview

JSON-based protocol over serial with message framing. Replaces the legacy binary protocol.

## Message Framing

Each message: `<length_2bytes_big_endian><json_payload>\n`

## Commands

### Identify

```json
// Request:
{"cmd": "identify"}
// Response:
{"device": "pump", "version": "2.0", "capabilities": ["rotate", "pour"]}
```

### Start Rotation

```json
// Request:
{"cmd": "rotate", "direction": "left", "speed_ml_min": 3.0}
// Response:
{"status": "ok", "state": "rotating"}
```

### Stop

```json
// Request:
{"cmd": "stop"}
// Response:
{"status": "ok", "state": "idle"}
```

### Pour Volume

```json
// Request:
{"cmd": "pour", "direction": "left", "volume_ml": 10.0, "speed_ml_min": 3.0}
// Response:
{"status": "ok", "state": "pouring", "estimated_duration_s": 3.33}
```

### Query State

```json
// Request:
{"cmd": "status"}
// Response:
{"state": "rotating", "direction": "left", "speed_ml_min": 3.0}
```

### Error Response

```json
{"status": "error", "code": "INVALID_CMD", "message": "Unknown command: xyz"}
```

## Improvements Over Legacy

- Human-readable JSON
- Explicit acknowledgments for every command
- Floating-point speed and volume (no 0-255 limit)
- State query capability
- Standardized error responses
- Self-describing identification with version and capabilities

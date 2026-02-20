# Pump — Target Protocol (Future)

**Protocol version: 0.1**

## Overview

JSON-based protocol over serial with message framing. Replaces the legacy binary protocol.

## Message Framing

Each message: `<length_2bytes_big_endian><json_payload>\n`

## Commands

### Identify

```json
// Request:
{
  "cmd": "identify"
}

// Response:
{
  "device": "pump",
  "version": "2.0",
  "device_id": "<some_unique_id>"
}
```

### Start Rotation

```json
// Request:
{
  "cmd": "rotate",
  "direction": "left",
  "speed_ml_min": 3.0
}

// Response:
{
  "status": "ok",
  "state": "rotating",
  "state_id": "<some_unique_id>"
}
```

### Stop

```json
// Request:
{
  "cmd": "stop"
}

// Response:
{
  "status": "ok",
  "state": "idle",
  "last_state_id": "<some_unique_id>"
}
```

### Pour Volume

```json
// Request:
{
  "cmd": "pour",
  "direction": "left",
  "volume_ml": 10.0,
  "speed_ml_min": 3.0
}

// Initial response:
{
  "status": "ok",
  "state": "pouring",
  "state_id": "<some_unique_id>",
  "estimated_duration_s": 3.33
}

// Final response:
{
  "status": "ok",
  "state": "idle",
  "last_state_id": "<some_unique_id>"
}
```

### Query State

```json
// Request:
{
  "cmd": "status"
}

// Response:
{
  "state": "idle",
  "last_state_id": "<some_unique_id>"
}
// or:
{
  "state": "rotating",
  "state_id": "<some_unique_id>",
  "params": {
    "direction": "left",
    "speed_ml_min": 3.0
  }
}
// or:
{
  "state": "pouring",
  "state_id": "<some_unique_id>",
  "params": {
    "direction": "left",
    "speed_ml_min": 3.0,
    "volume_ml": 10.0
  },
  "estimated_duration_s": 3.33,
  "elapsed_s": 1.2
}
```

### Error Response

```json
{
  "status": "error",
  "code": "INVALID_CMD",
  "message": "Unknown command: xyz"
}
```

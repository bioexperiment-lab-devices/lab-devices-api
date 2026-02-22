# Densitometer — Target Protocol (Future)

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
  "device": "densitometer",
  "version": "2.0",
  "device_id": "<some_unique_id>"
}
```

### Get Temperature

```json
// Request:
{
  "cmd": "get_temperature"
}

// Response:
{
  "status": "ok",
  "temperature_c": 23.50
}
```

### Measure OD

```json
// Request:
{
  "cmd": "measure_od"
}

// Initial response:
{
  "status": "ok",
  "state": "measuring_od",
  "state_id": "<some_unique_id>",
  "estimated_duration_s": 2.0
}

// Final response:
{
  "status": "ok",
  "state": "idle",
  "last_state_id": "<some_unique_id>",
  "absorbance": 0.42
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
  "state": "measuring_od",
  "state_id": "<some_unique_id>",
  "estimated_duration_s": 2.0,
  "elapsed_s": 1.2
}
```

### Error Response

```json
{
  "status": "error",
  "code": "<error_code>",
  "message": "<human-readable description>"
}
```

Error codes:

| Code | Meaning |
|------|---------|
| `PARSE_ERROR` | Malformed JSON or missing `cmd` field |
| `INVALID_CMD` | Unknown command name |
| `INVALID_STATE` | Command not allowed in current state (e.g. `measure_od` while already measuring) |
| `TEMP_SENSOR_ERROR` | Temperature sensor failure (no reading or out of range) |
| `OD_SENSOR_ERROR` | Optical density sensor failure (no reading or out of range) |

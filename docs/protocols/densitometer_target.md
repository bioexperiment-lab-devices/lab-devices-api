# Densitometer — Target Protocol (Future)

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
{"device": "densitometer", "version": "2.0", "capabilities": ["temperature", "od"]}
```

### Read Temperature

```json
// Request:
{"cmd": "read_temperature"}
// Response:
{"status": "ok", "temperature_c": 23.50}
```

### Start OD Measurement

```json
// Request:
{"cmd": "start_od_measurement"}
// Response:
{"status": "ok", "state": "measuring", "estimated_duration_s": 2.0}
```

### Read OD

```json
// Request:
{"cmd": "read_od"}
// Response (ready):
{"status": "ok", "absorbance": 0.42}
// Response (not ready):
{"status": "error", "code": "MEASUREMENT_IN_PROGRESS", "message": "OD measurement not complete"}
```

### Query State

```json
// Request:
{"cmd": "status"}
// Response:
{"state": "idle"}
// or:
{"state": "measuring_od", "elapsed_s": 1.2, "estimated_remaining_s": 0.8}
```

### Error Response

```json
{"status": "error", "code": "INVALID_CMD", "message": "Unknown command: xyz"}
```

## Improvements Over Legacy

- Human-readable JSON
- Explicit acknowledgment for measurement start
- Measurement-not-ready error instead of silent bad data
- Full floating-point precision for all values
- State query with measurement progress
- Standardized error responses

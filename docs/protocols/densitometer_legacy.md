# Densitometer — Legacy Protocol

## Overview

Binary protocol over serial port. All incoming messages are **5 bytes**. Response sizes vary (4 bytes). No framing, no checksums.

## Identification

| Direction | Bytes | Description |
|-----------|-------|-------------|
| Host -> Device | `[0x01, 0x02, 0x03, 0x04, 0x00]` | Discovery probe |
| Device -> Host | `[0x46, 0x00, 0x00, 0x00]` | Identity response (4 bytes) |

## Commands

### Temperature Request

| Direction | Bytes | Description |
|-----------|-------|-------------|
| Host -> Device | `[0x4C, 0x00, 0x00, 0x00, 0x00]` | Request temperature |
| Device -> Host | `[a1, a2, a3, a4]` | Temperature response (4 bytes) |

**Decoding:** `temperature_c = float(a3) + float(a4) / 100`

Example: `[0x00, 0x00, 0x17, 0x32]` → 23 + 50/100 = 23.50°C

### Start OD Measurement

| Direction | Bytes | Description |
|-----------|-------|-------------|
| Host -> Device | `[0x4E, 0x04, 0x00, 0x00, 0x00]` | Start measurement |

- No response. Device begins measuring (takes ~2 seconds).
- Host must wait before requesting OD value.

### OD Request

| Direction | Bytes | Description |
|-----------|-------|-------------|
| Host -> Device | `[0x4F, 0x04, 0x00, 0x00, 0x00]` | Request OD value |
| Device -> Host | `[a1, a2, a3, a4]` | OD response (4 bytes) |

**Decoding:** `absorbance = float(a3) + float(a4) / 100`

Example: `[0x00, 0x00, 0x00, 0x2A]` → 0 + 42/100 = 0.42

## Known Limitations

- No acknowledgment for start measurement command
- No way to know when measurement is complete
- First two bytes of responses (a1, a2) appear unused
- No error reporting
- No way to query device state
- Must manually time the measurement delay

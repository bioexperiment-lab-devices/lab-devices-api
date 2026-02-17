# Pump — Legacy Protocol

## Overview

Binary protocol over serial port. All messages are **5 bytes**. No framing, no checksums, no acknowledgments (except identification).

## Identification

| Direction | Bytes | Description |
|-----------|-------|-------------|
| Host -> Device | `[0x01, 0x02, 0x03, 0x04, 0xB5]` | Discovery probe |
| Device -> Host | `[0x0A, 0x00, 0x00, 0x00]` | Identity response (4 bytes) |

## Commands

All commands are 5 bytes: `[command, param1, wildcard, param2, param3]`

### Continuous Rotation Left

`[0x0B, 0x6F, *, speed, 0x00]`

- `speed`: rotation speed in ml/min (single byte, 0-255)
- `*`: ignored byte
- Pump rotates continuously until another command is sent

### Continuous Rotation Right

`[0x0C, 0x6F, *, speed, 0x00]`

- Same as left rotation but clockwise

### Set Rotation Speed

`[0x0A, 0x00, *, speed, 0x00]`

- Stores speed for subsequent pour commands
- Must be sent before pour volume commands

### Pour Volume Left

`[0x10, *, *, *, volume]`

- `volume`: volume to pour (single byte, 0-255 ml)
- Uses previously set speed
- Duration = volume / speed

### Pour Volume Right

`[0x11, *, *, *, volume]`

- Same as pour left but clockwise

## Known Limitations

- No acknowledgment for commands (fire and forget)
- Single-byte speed and volume limits range to 0-255
- Wildcard bytes waste bandwidth
- No error reporting
- No way to query current state
- Identification response is only 4 bytes while all commands are 5

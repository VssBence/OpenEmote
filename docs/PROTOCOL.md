# Seiren Emote display protocol

Notes from reverse engineering the display on firmware 1.0. Everything here was
found by probing the device, not from official documentation.

## USB topology

The mic is a USB hub (Genesys `05E3:0610`) with two devices behind it:

| Device | VID:PID | Role |
|---|---|---|
| Seiren Emote audio | `1532:0524` | USB audio + mute/volume HID (16-byte reports) |
| Seiren Emote display | `1532:0F1B` | LED display controller, HID usage page `0x0C` |

The display controller has no input or output reports. It has a single
**91-byte feature report** (report ID `0x00` + 90 bytes), which is the standard
Razer peripheral protocol also used by keyboards and mice (see
[OpenRazer](https://github.com/openrazer/openrazer)).

## Packet format (90 bytes)

| Offset | Size | Field |
|---|---|---|
| 0 | 1 | status (request: `0x00`; response: `0x02` ok, `0x01` busy, `0x03` fail, `0x05` not supported) |
| 1 | 1 | transaction id (`0x1F` works; `0x3F`, `0xFF`, `0x9F` are accepted too) |
| 2 | 2 | remaining packets (0) |
| 4 | 1 | protocol type (0) |
| 5 | 1 | data size |
| 6 | 1 | command class |
| 7 | 1 | command id (bit 7 set = "get") |
| 8 | 80 | arguments |
| 88 | 1 | CRC: XOR of bytes 2..87 |
| 89 | 1 | reserved |

Send with `SetFeature`, then read the response with `GetFeature`.

## Commands that work

| Class | Id | Size | Args | Meaning |
|---|---|---|---|---|
| `0x00` | `0x82` | `0x16` | none | get serial (ASCII, matches the USB serial) |
| `0x00` | `0x81` | `0x02` | none | get firmware (`major, minor`) |
| `0x0F` | `0x03` | `5+3n` | `00 00 row start end RGB…` | write one row of the custom frame |
| `0x0F` | `0x02` | `0x0C` | `00 00 08` | switch to the custom-frame effect (no-store) |

## Pixel matrix

The firmware exposes the 64 LEDs as **4 rows × 16 columns**: rows `0..3` and
columns `0..15` are accepted, while row 4+ or column 16+ returns `0x05` (not
supported). OpenEmote's default `split` layout assumes each firmware row holds
two physical 8-pixel rows (`row r = physical rows 2r and 2r+1`). If your
display looks scrambled, run `openemote calibrate` and try
`--layout split-snake`, and please open an issue describing what you saw.

## Open questions

- Hardware brightness command (OpenEmote scales colors in software for now)
- Whether animations can be uploaded and stored on the device itself
- What Synapse sends when it takes control of the display again

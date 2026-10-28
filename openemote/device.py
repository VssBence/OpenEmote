"""Low-level driver for the Razer Seiren Emote's 8x8 LED display.

The display is driven by a separate USB HID device (1532:0F1B) that sits
behind the mic's internal USB hub. It speaks the standard Razer 90-byte
feature-report protocol. See docs/PROTOCOL.md for details.
"""
from __future__ import annotations

import threading
import time

import hid

from .frame import HEIGHT, WIDTH, Frame, scale

VID = 0x1532
PID = 0x0F1B

# The firmware addresses the 64 LEDs as 4 rows x 16 columns.
FW_ROWS = 4
FW_COLS = 16

STATUS_NEW = 0x00
STATUS_BUSY = 0x01
STATUS_OK = 0x02
STATUS_NAMES = {0x00: "new", 0x01: "busy", 0x02: "ok", 0x03: "failed", 0x04: "timeout", 0x05: "not supported"}

# How the 8x8 picture maps onto the firmware's 4x16 rows. "mirror" matches real hardware.
LAYOUTS = {
    "mirror": lambda rows: [rows[2 * r][::-1] + rows[2 * r + 1][::-1] for r in range(FW_ROWS)],
    "split": lambda rows: [rows[2 * r] + rows[2 * r + 1] for r in range(FW_ROWS)],
    "split-snake": lambda rows: [rows[2 * r] + rows[2 * r + 1][::-1] for r in range(FW_ROWS)],
}


class DeviceError(RuntimeError):
    pass


def _packet(cls: int, cmd: int, args: bytes, size: int | None, tid: int) -> bytes:
    r = bytearray(90)
    r[1] = tid
    r[5] = len(args) if size is None else size
    r[6] = cls
    r[7] = cmd
    r[8:8 + len(args)] = args
    crc = 0
    for b in r[2:88]:
        crc ^= b
    r[88] = crc
    return bytes(r)


class EmoteDisplay:
    def __init__(self, layout: str = "mirror", brightness: float = 1.0, transaction_id: int = 0x1F):
        if layout not in LAYOUTS:
            raise ValueError(f"unknown layout {layout!r}, choose from {', '.join(LAYOUTS)}")
        devices = hid.enumerate(VID, PID)
        if not devices:
            raise DeviceError("Seiren Emote display (USB 1532:0F1B) not found. Is the mic plugged in?")
        self._dev = hid.device()
        try:
            self._dev.open_path(devices[0]["path"])
        except OSError as e:
            raise DeviceError(f"could not open the display: {e}") from e
        self._lock = threading.Lock()
        self._tid = transaction_id
        self.layout = layout
        self.brightness = brightness

    def transfer(self, cls: int, cmd: int, args: bytes = b"", size: int | None = None) -> bytes:
        packet = _packet(cls, cmd, args, size, self._tid)
        with self._lock:
            self._dev.send_feature_report(b"\x00" + packet)
            for _ in range(20):
                time.sleep(0.003)
                resp = bytes(self._dev.get_feature_report(0, 91))
                if len(resp) == 91:
                    resp = resp[1:]
                if resp[0] not in (STATUS_NEW, STATUS_BUSY):
                    break
        if resp[0] != STATUS_OK:
            raise DeviceError(f"command {cls:#04x}/{cmd:#04x} -> {STATUS_NAMES.get(resp[0], resp[0])}")
        return resp

    def serial(self) -> str:
        resp = self.transfer(0x00, 0x82, size=0x16)
        return resp[8:30].split(b"\x00")[0].decode(errors="replace")

    def firmware(self) -> str:
        resp = self.transfer(0x00, 0x81, size=0x02)
        return f"{resp[8]}.{resp[9]}"

    def show(self, frame: Frame) -> None:
        """Push one 8x8 frame to the display."""
        if len(frame) != WIDTH * HEIGHT:
            raise ValueError(f"frame must have {WIDTH * HEIGHT} pixels, got {len(frame)}")
        if self.brightness < 1.0:
            frame = scale(frame, self.brightness)
        rows = [frame[y * WIDTH:(y + 1) * WIDTH] for y in range(HEIGHT)]
        for r, row in enumerate(LAYOUTS[self.layout](rows)):
            data = bytes(max(0, min(255, v)) for rgb in row for v in rgb)
            self.transfer(0x0F, 0x03, bytes([0x00, 0x00, r, 0, FW_COLS - 1]) + data)
        # switch to the custom-frame effect (varstore=no-store, led=0, effect=custom)
        self.transfer(0x0F, 0x02, bytes([0x00, 0x00, 0x08]), size=0x0C)

    def close(self) -> None:
        self._dev.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

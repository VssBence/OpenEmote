"""Watch the Seiren Emote's mute button.

The mic doesn't report whether it is muted (not over HID, not to Windows). It only
sends the same report every time the button is pressed, so each press flips our
state. Nothing here touches the audio stream.
"""
from __future__ import annotations

import threading
import time

AUDIO_VID, AUDIO_PID = 0x1532, 0x0524


class MuteWatcher(threading.Thread):
    def __init__(self, on_change):
        super().__init__(daemon=True)
        self.on_change = on_change
        self.muted = False
        self.error: Exception | None = None
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def flip(self) -> None:
        """Toggle the state by hand, for when it got out of sync."""
        self.muted = not self.muted
        self.on_change(self.muted)

    def run(self):
        try:
            import hid
            buttons = []
            for d in hid.enumerate(AUDIO_VID, AUDIO_PID):
                if d["usage_page"] == 0x0C:
                    h = hid.device()
                    h.open_path(d["path"])
                    h.set_nonblocking(True)
                    buttons.append(h)
            if not buttons:
                raise RuntimeError("mic button not found")
        except Exception as e:
            self.error = e
            return
        try:
            while not self._stop_event.is_set():
                for h in buttons:
                    data = h.read(64)
                    if data and data[0] == 0x01 and data[1] == 0x80:  # 0x80 = button pressed
                        self.flip()
                time.sleep(0.01)
        except Exception as e:
            self.error = e
        finally:
            for h in buttons:
                h.close()

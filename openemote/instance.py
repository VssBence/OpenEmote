"""Single running copy + a way to ask it to quit cleanly (Windows named kernel objects)."""
from __future__ import annotations

import ctypes

MUTEX_NAME = "OpenEmote.SingleInstance"
QUIT_EVENT_NAME = "OpenEmote.Quit"
ERROR_ALREADY_EXISTS = 183
EVENT_MODIFY_STATE = 0x0002

try:
    _k32 = ctypes.windll.kernel32
except AttributeError:  # not Windows
    _k32 = None


def already_running() -> bool:
    """Claim the single-instance mutex; True if another copy holds it."""
    if _k32 is None:
        return False
    _k32.CreateMutexW(None, False, MUTEX_NAME)
    return _k32.GetLastError() == ERROR_ALREADY_EXISTS


def quit_event():
    """Create the event a running copy watches; returns a handle (or None)."""
    if _k32 is None:
        return None
    return _k32.CreateEventW(None, True, False, QUIT_EVENT_NAME)


def quit_requested(event) -> bool:
    return bool(event) and _k32.WaitForSingleObject(event, 0) == 0


def signal_quit() -> bool:
    """Ask a running copy to close. Returns False if none is running."""
    if _k32 is None:
        return False
    event = _k32.OpenEventW(EVENT_MODIFY_STATE, False, QUIT_EVENT_NAME)
    if not event:
        return False
    _k32.SetEvent(event)
    _k32.CloseHandle(event)
    return True

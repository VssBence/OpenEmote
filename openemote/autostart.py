"""Start menu and Start with Windows shortcuts."""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

PROGRAMS = pathlib.Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
SHORTCUT = PROGRAMS / "Startup" / "OpenEmote.lnk"
START_MENU = PROGRAMS / "OpenEmote.lnk"


def _target() -> tuple[str, str]:
    if getattr(sys, "frozen", False):
        return sys.executable, ""
    pythonw = pathlib.Path(sys.executable).with_name("pythonw.exe")
    return str(pythonw if pythonw.exists() else sys.executable), "-m openemote"


def _make_shortcut(lnk: pathlib.Path, extra_args: str = "") -> None:
    target, args = _target()
    script = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:LNK); "
        "$s.TargetPath = $env:TARGET; $s.Arguments = $env:ARGS; "
        "$s.WorkingDirectory = $env:WORKDIR; $s.Save()"
    )
    env = dict(os.environ, LNK=str(lnk), TARGET=target, ARGS=f"{args} {extra_args}".strip(),
               WORKDIR=str(pathlib.Path(target).parent))
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], env=env, check=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), capture_output=True)
    if not lnk.exists():
        raise OSError("shortcut was not created")


def enabled() -> bool:
    return SHORTCUT.exists()


def set_enabled(on: bool) -> None:
    if on:
        _make_shortcut(SHORTCUT, "--tray")
    else:
        SHORTCUT.unlink(missing_ok=True)


def in_start_menu() -> bool:
    return START_MENU.exists()


def set_start_menu(on: bool) -> None:
    if on:
        _make_shortcut(START_MENU)
    else:
        START_MENU.unlink(missing_ok=True)

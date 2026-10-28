"""Start with Windows via a shortcut in the user's Startup folder."""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

SHORTCUT = (pathlib.Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            / "Startup" / "OpenEmote.lnk")


def _target() -> tuple[str, str]:
    if getattr(sys, "frozen", False):
        return sys.executable, "--tray"
    pythonw = pathlib.Path(sys.executable).with_name("pythonw.exe")
    return str(pythonw if pythonw.exists() else sys.executable), "-m openemote --tray"


def enabled() -> bool:
    return SHORTCUT.exists()


def set_enabled(on: bool) -> None:
    if not on:
        SHORTCUT.unlink(missing_ok=True)
        return
    target, args = _target()
    script = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:LNK); "
        "$s.TargetPath = $env:TARGET; $s.Arguments = $env:ARGS; "
        "$s.WorkingDirectory = $env:WORKDIR; $s.Save()"
    )
    env = dict(os.environ, LNK=str(SHORTCUT), TARGET=target, ARGS=args, WORKDIR=str(pathlib.Path(target).parent))
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], env=env, check=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), capture_output=True)
    if not SHORTCUT.exists():
        raise OSError("shortcut was not created")

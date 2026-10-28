"""Build dist/OpenEmote.exe (needs: pip install pyinstaller pillow)."""
import pathlib
import subprocess
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from openemote.presets import PRESETS  # noqa: E402

# app icon from the smiley preset
icon = Image.new("RGBA", (8, 8))
icon.putdata([c + ((255,) if any(c) else (0,)) for c in PRESETS["smiley"].thumbnail()])
ico = ROOT / "build" / "openemote.ico"
ico.parent.mkdir(exist_ok=True)
icon.resize((256, 256), Image.Resampling.NEAREST).save(ico, sizes=[(256, 256), (64, 64), (32, 32), (16, 16)])

entry = ROOT / "build" / "launch.py"
entry.write_text("from openemote.cli import main\nmain()\n")  # so the exe understands --tray

subprocess.check_call([
    sys.executable, "-m", "PyInstaller", "--onefile", "--windowed", "--noconfirm",
    "--name", "OpenEmote", "--icon", str(ico), "--hidden-import", "pystray._win32", "--paths", str(ROOT),
    "--distpath", str(ROOT), "--workpath", str(ROOT / "build" / "pyi"), "--specpath", str(ROOT / "build"),
    str(entry),
])

"""Render docs/presets.png: a gallery of every built-in preset."""
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from openemote.presets import PRESETS  # noqa: E402

PX, GAP, COLS = 10, 1, 12
TILE = 8 * PX
CELL_W, CELL_H = TILE + 28, TILE + 40
BG, LED_OFF = (22, 22, 28), (36, 36, 44)

presets = list(PRESETS.values())
rows = -(-len(presets) // COLS)
img = Image.new("RGB", (COLS * CELL_W + 14, rows * CELL_H + 14), BG)
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("segoeui.ttf", 13)
except OSError:
    font = ImageFont.load_default()

for n, preset in enumerate(presets):
    ox = 14 + (n % COLS) * CELL_W
    oy = 14 + (n // COLS) * CELL_H
    for i, color in enumerate(preset.thumbnail()):
        x, y = ox + (i % 8) * PX, oy + (i // 8) * PX
        draw.ellipse([x + GAP, y + GAP, x + PX - GAP, y + PX - GAP], fill=color if any(color) else LED_OFF)
    label = preset.name + (" *" if preset.animated else "")
    w = draw.textlength(label, font=font)
    draw.text((ox + (TILE - w) / 2, oy + TILE + 6), label, fill=(200, 200, 210), font=font)

out = pathlib.Path(__file__).resolve().parents[1] / "docs" / "presets.png"
out.parent.mkdir(exist_ok=True)
img.save(out)
print("wrote", out)

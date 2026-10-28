"""Load images and animated GIFs as 8x8 frames (requires Pillow)."""
from __future__ import annotations

from .frame import Frame


def load_image(path: str) -> list[tuple[Frame, int]]:
    try:
        from PIL import Image, ImageSequence
    except ImportError as e:
        raise RuntimeError("Loading images needs Pillow: pip install pillow") from e

    steps = []
    with Image.open(path) as im:
        for fr in ImageSequence.Iterator(im):
            rgba = fr.convert("RGBA")
            resample = Image.Resampling.NEAREST if min(rgba.size) < 8 else Image.Resampling.BOX
            data = rgba.resize((8, 8), resample).tobytes()
            # premultiply alpha so transparent areas are off
            frame = [(data[i] * data[i + 3] // 255, data[i + 1] * data[i + 3] // 255, data[i + 2] * data[i + 3] // 255)
                     for i in range(0, len(data), 4)]
            steps.append((frame, int(fr.info.get("duration") or 100)))
    return steps

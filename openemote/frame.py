"""Frame helpers. A frame is a flat, row-major list of 64 (r, g, b) tuples."""
from __future__ import annotations

import colorsys
from typing import List, Tuple

WIDTH = HEIGHT = 8

Color = Tuple[int, int, int]
Frame = List[Color]

BLACK: Color = (0, 0, 0)

# Palette used by the ASCII sprites in presets.py
PALETTE = {
    ".": BLACK,
    "K": BLACK,
    "W": (255, 255, 255),
    "w": (140, 140, 140),
    "R": (255, 0, 0),
    "r": (110, 0, 0),
    "P": (255, 70, 150),
    "O": (255, 100, 0),
    "Y": (255, 190, 0),
    "G": (0, 220, 0),
    "g": (0, 80, 0),
    "C": (0, 200, 255),
    "B": (0, 100, 255),
    "M": (170, 0, 255),
    "N": (170, 70, 10),
}

NAMED_COLORS = {
    "red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255),
    "white": (255, 255, 255), "yellow": (255, 190, 0), "orange": (255, 100, 0),
    "purple": (170, 0, 255), "pink": (255, 70, 150), "cyan": (0, 200, 255),
    "black": BLACK, "off": BLACK,
}


def blank(color: Color = BLACK) -> Frame:
    return [color] * (WIDTH * HEIGHT)


def sprite(rows, palette=PALETTE) -> Frame:
    """Build a frame from 8 strings of 8 palette characters."""
    if len(rows) != HEIGHT or any(len(r) != WIDTH for r in rows):
        raise ValueError("sprites must be 8 rows of 8 characters")
    return [palette.get(c, BLACK) for row in rows for c in row]


def shift(frame: Frame, dx: int = 0, dy: int = 0, wrap: bool = False) -> Frame:
    out = blank()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            sx, sy = x - dx, y - dy
            if wrap:
                sx, sy = sx % WIDTH, sy % HEIGHT
            if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
                out[y * WIDTH + x] = frame[sy * WIDTH + sx]
    return out


def overlay(frame: Frame, points, color: Color) -> Frame:
    out = list(frame)
    for x, y in points:
        out[y * WIDTH + x] = color
    return out


def mix(a: Color, b: Color, k: float) -> Color:
    return tuple(int(x + (y - x) * k) for x, y in zip(a, b))


def rotate(frame: Frame) -> Frame:
    """Rotate 90 degrees clockwise."""
    return [frame[(HEIGHT - 1 - x) * WIDTH + y] for y in range(HEIGHT) for x in range(WIDTH)]


def hsv(h: float, s: float = 1.0, v: float = 1.0) -> Color:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, max(0.0, min(1.0, v)))
    return int(r * 255), int(g * 255), int(b * 255)


def scale(frame: Frame, k: float) -> Frame:
    return [(int(r * k), int(g * k), int(b * k)) for r, g, b in frame]


def parse_color(text: str) -> Color:
    text = text.strip().lower()
    if text in NAMED_COLORS:
        return NAMED_COLORS[text]
    text = text.lstrip("#")
    if len(text) == 3:
        text = "".join(c * 2 for c in text)
    if len(text) != 6:
        raise ValueError(f"not a color: {text!r} (use a name or hex like ff8800)")
    return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(c: Color) -> str:
    return "#%02x%02x%02x" % c

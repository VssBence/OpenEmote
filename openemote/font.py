"""Tiny 3x5 pixel font and text scrolling."""
from __future__ import annotations

from .frame import WIDTH, Color, Frame, blank, hsv

GLYPHS = {
    "A": ".#./#.#/###/#.#/#.#", "B": "##./#.#/##./#.#/##.", "C": ".##/#../#../#../.##",
    "D": "##./#.#/#.#/#.#/##.", "E": "###/#../##./#../###", "F": "###/#../##./#../#..",
    "G": ".##/#../#.#/#.#/.##", "H": "#.#/#.#/###/#.#/#.#", "I": "###/.#./.#./.#./###",
    "J": "..#/..#/..#/#.#/.#.", "K": "#.#/#.#/##./#.#/#.#", "L": "#../#../#../#../###",
    "M": "#.#/###/###/#.#/#.#", "N": "##./#.#/#.#/#.#/#.#", "O": ".#./#.#/#.#/#.#/.#.",
    "P": "##./#.#/##./#../#..", "Q": ".#./#.#/#.#/##./.##", "R": "##./#.#/##./#.#/#.#",
    "S": ".##/#../.#./..#/##.", "T": "###/.#./.#./.#./.#.", "U": "#.#/#.#/#.#/#.#/###",
    "V": "#.#/#.#/#.#/#.#/.#.", "W": "#.#/#.#/###/###/#.#", "X": "#.#/#.#/.#./#.#/#.#",
    "Y": "#.#/#.#/.#./.#./.#.", "Z": "###/..#/.#./#../###",
    "0": "###/#.#/#.#/#.#/###", "1": ".#./##./.#./.#./###", "2": "##./..#/.#./#../###",
    "3": "##./..#/.#./..#/##.", "4": "#.#/#.#/###/..#/..#", "5": "###/#../##./..#/##.",
    "6": ".##/#../###/#.#/###", "7": "###/..#/.#./.#./.#.", "8": "###/#.#/###/#.#/###",
    "9": "###/#.#/###/..#/##.",
    " ": ".../.../.../.../...", "!": ".#./.#./.#./.../.#.", "?": "##./..#/.#./.../.#.",
    ".": ".../.../.../.../.#.", ":": ".../.#./.../.#./...", "-": ".../.../###/.../...",
}
TOP = 1  # first pixel row used by the glyphs
EMPTY = [False] * 5


def _columns(text: str):
    cols = []
    for i, ch in enumerate(text.upper()):
        rows = GLYPHS.get(ch, GLYPHS[" "]).split("/")
        if i:
            cols.append(EMPTY)
        for x in range(3):
            cols.append([rows[y][x] == "#" for y in range(5)])
    return cols


def _render(window, color: Color | None, hue_offset: int) -> Frame:
    f = blank()
    for x, col in enumerate(window):
        for y, on in enumerate(col):
            if on:
                f[(y + TOP) * WIDTH + x] = color or hsv((x + hue_offset) / 24)
    return f


def text_steps(text: str, color: Color | None = None, speed_ms: int = 90):
    """Return (frame, ms) steps. Short text is shown static, longer text scrolls.

    color=None renders a rainbow.
    """
    cols = _columns(text)
    if len(cols) <= WIDTH:
        pad = (WIDTH - len(cols)) // 2
        window = [EMPTY] * pad + cols + [EMPTY] * (WIDTH - len(cols) - pad)
        return [(_render(window, color, 0), 1000)]
    padded = [EMPTY] * WIDTH + cols + [EMPTY] * WIDTH
    return [(_render(padded[i:i + WIDTH], color, i), speed_ms) for i in range(len(cols) + WIDTH)]

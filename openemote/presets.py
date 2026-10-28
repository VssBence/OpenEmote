"""Built-in presets: faces, icons, animations and text.

Every preset is a factory returning an iterable of (frame, milliseconds)
steps. Finite sequences are looped by the player; procedural ones are
infinite generators.
"""
from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Callable, Iterable, Tuple

from .font import text_steps
from .frame import BLACK, HEIGHT, WIDTH, Frame, blank, hsv, mix, overlay, rotate, scale, shift, sprite

Step = Tuple[Frame, int]
CATEGORIES = ("faces", "icons", "animated", "text")


@dataclass
class Preset:
    name: str
    description: str
    category: str
    factory: Callable[[], Iterable[Step]]
    thumb_step: int = 0

    @property
    def animated(self) -> bool:
        steps = self.factory()
        return not (isinstance(steps, list) and len(steps) == 1)

    def thumbnail(self) -> Frame:
        frame = blank()
        for i, (frame, _) in enumerate(self.factory()):
            if i >= self.thumb_step:
                break
        return frame


PRESETS: dict[str, Preset] = {}


def playlist(presets, seconds: float):
    """Cycle through presets, giving each about `seconds`. Finite sequences finish their pass first."""
    budget = seconds * 1000
    while True:
        for p in presets:
            used, steps = 0, p.factory()
            if isinstance(steps, list):
                while used < budget:
                    for frame, ms in steps:
                        yield frame, ms
                        used += ms
            else:
                for frame, ms in steps:
                    yield frame, ms
                    used += ms
                    if used >= budget:
                        break


def _register(name, description, category, factory, thumb_step=0):
    if name in PRESETS:
        raise ValueError(f"duplicate preset name {name!r}")
    PRESETS[name] = Preset(name, description, category, factory, thumb_step)


def animation(name, description, thumb_step=0):
    def deco(fn):
        _register(name, description, "animated", fn, thumb_step)
        return fn
    return deco


def _plot(buf, x, y, v, h):
    xi, yi = int(round(x)), int(round(y))
    if 0 <= xi < WIDTH and 0 <= yi < HEIGHT and v > buf[yi * WIDTH + xi][0]:
        buf[yi * WIDTH + xi] = (v, h)


# --- animation helpers ------------------------------------------------------

WHITE = (255, 255, 255)
TEAR = (0, 120, 255)


def add(name, description, category, steps, thumb_step=0):
    factory = steps if callable(steps) else (lambda s=steps: s)
    _register(name, description, category, factory, thumb_step)


def lit(frame):
    return [i for i, c in enumerate(frame) if any(c)]


def var(rows, changes):
    """Sprite from rows with some rows replaced."""
    rows = list(rows)
    for k, v in changes.items():
        rows[k] = v
    return sprite(rows)


def cells(rows, ch, only_rows=range(HEIGHT)):
    return [y * WIDTH + x for y in only_rows for x, c in enumerate(rows[y]) if c == ch]


def paint(frame, idxs, color):
    f = list(frame)
    for i in idxs:
        f[i] = color
    return f


def blink(base, closed):
    return [(base, 2400), (closed, 140), (base, 1400), (closed, 120), (base, 120), (closed, 120)]


def shine(base, area=None, hold=1500):
    area = lit(base) if area is None else area
    steps = []
    for d in range(-2, WIDTH + HEIGHT):
        f = list(base)
        for i in area:
            if abs(i % WIDTH + i // WIDTH - d) <= 1:
                f[i] = mix(f[i], WHITE, 0.75)
        steps.append((f, 40))
    return steps + [(base, hold)]


def bob(base, ms=350):
    return [(base, ms), (shift(base, dy=-1), ms)]


def shake(base):
    return [(shift(base, dx=d), 60) for d in (1, -1, 1, -1, 1, 0)] + [(base, 900)]


def pulse(base, n=24):
    return [(scale(base, 0.35 + 0.65 * (0.5 + 0.5 * math.cos(2 * math.pi * i / n))), 50) for i in range(n)]


def draw_in(base, key):
    order = sorted(lit(base), key=lambda i: key(i % WIDTH, i // WIDTH))
    steps, f = [], blank()
    for i in order:
        f = paint(f, [i], base[i])
        steps.append((f, 45))
    return steps + [(base, 1500), (blank(), 300)]


def slide(base, dx=0, dy=0, ms=80):
    return [(shift(base, dx * k, dy * k, wrap=True), ms) for k in range(WIDTH)]


def flash(base):
    return [(base, 900), (blank(), 70), (base, 70), (blank(), 70), (base, 70)]


def sparkle_on(base, area=None, count=2, ms=150, colors=(WHITE,)):
    area = lit(base) if area is None else area

    def gen():
        while True:
            f = list(base)
            for i in random.sample(area, min(count, len(area))):
                f[i] = random.choice(colors)
            yield f, ms
    return gen


# --- faces ------------------------------------------------------------------

SMILEY_R = [
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYKYYKYY",
    "YPYYYYPY",
    "YKYYYYKY",
    ".YKKKKY.",
    "..YYYY..",
]
SMILEY = sprite(SMILEY_R)
add("smiley", "Smiley that blinks", "faces", blink(SMILEY, var(SMILEY_R, {2: "YYYYYYYY", 3: "YKKYYKKY"})))

SAD = sprite([
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYKYYKYY",
    "YYYYYYYY",
    "YYKKKKYY",
    ".KYYYYK.",
    "..YYYY..",
])
add("sad", "Sad face with a tear", "faces",
    [(SAD, 900)] + [(overlay(SAD, [(1, y)], TEAR), 160) for y in range(3, 7)])

WOW_R = [
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYKYYKYY",
    "YYYYYYYY",
    "YYYKKYYY",
    ".YYKKYY.",
    "..YYYY..",
]
WOW = sprite(WOW_R)
WOW_BIG = var(WOW_R, {2: "YKKYYKKY", 3: "YKKYYKKY", 4: "YYKKKKYY", 5: "YYKKKKYY", 6: ".YKKKKY."})
add("wow", "Jaw drop", "faces", [(var(WOW_R, {5: "YYYYYYYY"}), 500), (WOW, 250), (WOW_BIG, 1000), (WOW, 250)])

LOVE_R = [
    "..YYYY..",
    "RYRYYRYR",
    "RRRYYRRR",
    "YRYYYYRY",
    "YYYYYYYY",
    "YKYYYYKY",
    ".YKKKKY.",
    "..YYYY..",
]
add("love", "Heart eyes", "faces",
    [(sprite(LOVE_R), 300), (var(LOVE_R, {1: "PYPYYPYP", 2: "PPPYYPPP", 3: "YPYYYYPY"}), 300)])

COOL_R = [
    "..YYYY..",
    ".YYYYYY.",
    "KKKKKKKK",
    "YKKYYKKY",
    "YYYYYYYY",
    "YKYYYYKY",
    ".YKKKKY.",
    "..YYYY..",
]
add("cool", "Sunglasses with a glint", "faces", shine(sprite(COOL_R), cells(COOL_R, "K", range(2, 4)), 2000))

LAUGH = sprite([
    "..YYYY..",
    ".YYYYYY.",
    "YKYYYYKY",
    "YYKYYKYY",
    "YKYYYYKY",
    "YKKKKKKY",
    ".YKRRKY.",
    "..YYYY..",
])
add("laugh", "XD", "faces", [(LAUGH, 110), (shift(LAUGH, dy=-1), 110)])

CRY_DRY = sprite([
    "..YYYY..",
    ".YYYYYY.",
    "YKKYYKKY",
    "YYYYYYYY",
    "YYYKKYYY",
    "YYKYYKYY",
    ".YYYYYY.",
    "..YYYY..",
])
add("cry", "Crying", "faces", [
    (overlay(CRY_DRY, [(x, y) for x in (1, 6) for y in (3 + k, 4 + k) if y < HEIGHT], TEAR), 150)
    for k in range(5)
])

add("angry", "Shaking with rage", "faces", shake(sprite([
    "..RRRR..",
    ".RRRRRR.",
    "RKRRRRKR",
    "RRKRRKRR",
    "RRRRRRRR",
    "RRKKKKRR",
    ".KRRRRK.",
    "..RRRR..",
])))

SLEEPY_R = [
    "..YYYY..",
    ".YYYYYY.",
    "YKKYYKKY",
    "YYYYYYYY",
    "YYYYYYYY",
    "YYYKKYYY",
    ".YYYYYY.",
    "..YYYY..",
]
add("sleepy", "Snoring", "faces", [
    (sprite(SLEEPY_R), 900),
    (overlay(var(SLEEPY_R, {4: "YYYKKYYY"}), [(7, 0)], WHITE), 900),
])

TONGUE_R = [
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYKYYKYY",
    "YKKKKKKY",
    "YYYRRYYY",
    ".YYRRYY.",
    "..YYYY..",
]
TONGUE = sprite(TONGUE_R)
add("tongue", "Wiggling tongue", "faces", [
    (TONGUE, 250), (var(TONGUE_R, {5: "YYYYRRYY", 6: ".YYYRRY."}), 250),
    (TONGUE, 250), (var(TONGUE_R, {5: "YYRRYYYY", 6: ".YRRYYY."}), 250),
])

NEUTRAL_R = [
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYKYYKYY",
    "YYYYYYYY",
    "YYKKKKYY",
    ".YYYYYY.",
    "..YYYY..",
]
NEUTRAL = sprite(NEUTRAL_R)

STAR_R = [
    "..YYYY..",
    ".YYYYYY.",
    "YKKYYKKY",
    "YKKYYKKY",
    "YYYYYYYY",
    "YKKKKKKY",
    ".YKRRKY.",
    "..YYYY..",
]
STARSTRUCK = sprite(STAR_R)
add("starstruck", "Sparkling eyes", "faces", [
    (overlay(STARSTRUCK, [(1, 2), (2, 3), (5, 2), (6, 3)], WHITE), 200),
    (overlay(STARSTRUCK, [(2, 2), (1, 3), (6, 2), (5, 3)], WHITE), 200),
])

_head = var(WOW_R, {0: "........", 1: "........"})
add("mindblown", "Mind blown", "faces", [
    (WOW, 700), (WOW_BIG, 500),
    (overlay(_head, [(3, 1), (4, 1)], (255, 190, 0)), 100),
    (overlay(_head, [(2, 0), (5, 0), (3, 1), (4, 1)], (255, 100, 0)), 100),
    (overlay(_head, [(1, 0), (6, 0), (2, 1), (5, 1), (0, 1), (7, 1)], (255, 0, 0)), 150),
    (overlay(_head, [(0, 0), (7, 0)], (90, 90, 90)), 200),
    (_head, 900),
])

DEVIL_R = [
    "M......M",
    ".M.MM.M.",
    ".MMMMMM.",
    "MYMMMMYM",
    "MMMMMMMM",
    "MKMMMMKM",
    ".MKKKKM.",
    "..MMMM..",
]
add("devil", "Little devil, glowing eyes", "faces",
    [(sprite(DEVIL_R), 400), (var(DEVIL_R, {3: "MRMMMMRM"}), 400)])

ROBOT_R = [
    "...RR...",
    "...WW...",
    "WWWWWWWW",
    "WCCWWCCW",
    "WWWWWWWW",
    "WKKKKKKW",
    "WWWWWWWW",
    ".W....W.",
]
add("robot", "Robot scanning", "faces", [
    (sprite(ROBOT_R), 300),
    (var(ROBOT_R, {0: "...rr...", 3: "WCWWWCWW"}), 300),
    (sprite(ROBOT_R), 300),
    (var(ROBOT_R, {0: "...rr...", 3: "WWCWWWCW"}), 300),
])

FROG_R = [
    ".GG..GG.",
    "GWKGGWKG",
    "GGGGGGGG",
    "GGGGGGGG",
    "GKGGGGKG",
    "GGKKKKGG",
    ".GGGGGG.",
    "........",
]
FROG = sprite(FROG_R)
add("frog", "Frog catching flies", "faces", [
    (FROG, 1500), (var(FROG_R, {1: "GGGGGGGG"}), 150), (FROG, 900),
    (var(FROG_R, {5: "GGKRRKGG", 6: ".GGRRGG.", 7: "...RR..."}), 250), (FROG, 600),
])

CAT_R = [
    "O......O",
    "OO....OO",
    "OOOOOOOO",
    "OKOOOOKO",
    "OKOOOOKO",
    "OOOPPOOO",
    ".OOOOOO.",
    "..OOOO..",
]
CAT = sprite(CAT_R)
CAT_EAR = var(CAT_R, {0: "O.......", 1: "OO.....O"})
add("cat", "Cat blinking and twitching", "faces", [
    (CAT, 1800), (var(CAT_R, {3: "OOOOOOOO", 4: "OKKOOKKO"}), 150), (CAT, 900), (CAT_EAR, 200), (CAT, 200), (CAT_EAR, 200),
])

ALIEN_R = [
    "..GGGG..",
    ".GGGGGG.",
    "GGGGGGGG",
    "GKKGGKKG",
    "GKKGGKKG",
    ".GGGGGG.",
    "..GKKG..",
    "...GG...",
]
ALIEN = sprite(ALIEN_R)
ALIEN_GLOW = paint(ALIEN, cells(ALIEN_R, "K", range(3, 5)), (0, 200, 255))
add("alien", "Alien with glowing eyes", "faces", [(ALIEN, 1500), (ALIEN_GLOW, 120), (ALIEN, 120), (ALIEN_GLOW, 120)])

SKULL_R = [
    ".WWWWWW.",
    "WWWWWWWW",
    "WKKWWKKW",
    "WKKWWKKW",
    "WWWKKWWW",
    ".WWWWWW.",
    "..W.W.W.",
    "..WWWWW.",
]
SKULL = sprite(SKULL_R)
SKULL_OPEN = var(SKULL_R, {6: "........", 7: "..W.W.W."})
add("skull", "Chattering skull", "faces", [(SKULL, 150), (SKULL_OPEN, 150)] * 3 + [(SKULL, 1200)])

add("ghost", "Floating ghost", "faces", bob(sprite([
    "..WWWW..",
    ".WWWWWW.",
    "WWKWWKWW",
    "WWKWWKWW",
    "WWWWWWWW",
    "WWWKKWWW",
    "WWWWWWWW",
    "WW.WW.WW",
]), 450))

PUMPKIN_R = [
    "...gg...",
    "..OOOO..",
    ".OOOOOO.",
    "OOKOOKOO",
    "OOOOOOOO",
    "OKOKKOKO",
    ".OOOOOO.",
    "..OOOO..",
]
PUMPKIN = sprite(PUMPKIN_R)
_HOLES = cells(PUMPKIN_R, "K")


def _pumpkin():
    while True:
        k = random.uniform(0.4, 1.0)
        yield paint(PUMPKIN, _HOLES, (int(255 * k), int(random.uniform(120, 200) * k), 0)), 90


add("pumpkin", "Jack-o'-lantern with candlelight", "faces", _pumpkin)

POOP = sprite([
    "........",
    "........",
    "........",
    "...NN...",
    "..NNON..",
    ".NONNNN.",
    "NNNNNONN",
    ".NNNNNN.",
])
STINK = (110, 210, 0)


def _stink(phase):
    pts = []
    for c, offset in ((1, 0), (4, 1), (6, 0)):
        for y in range(3):
            pts.append((c + (y + phase + offset) % 2, y))
    return overlay(POOP, pts, STINK)


add("poop", "Stinky poop", "icons", [(_stink(p), 250) for p in (0, 1)])

PUKE = sprite([
    "..YYYY..",
    ".YYYYYY.",
    "YKKYYKKY",
    "YYYYYYYY",
    "YYYKKYYY",
    ".YYYYYY.",
    "..YYYY..",
    "........",
])
_stream = [[(3, 4), (4, 4)], [(3, 5), (4, 5)], [(3, 6), (4, 6)],
           [(x, 7) for x in range(2, 6)], [(1, 7), (6, 7)], [(0, 7), (7, 7)]]


def _puke():
    steps = [(PUKE, 900), (shift(PUKE, dy=1), 200), (PUKE, 200)]
    out = []
    for k, part in enumerate(_stream * 2):
        if k < len(_stream):
            out = out + part
        color = (0, 220, 0) if k % 2 else (120, 200, 0)
        steps.append((overlay(PUKE, out, color), 110))
    return steps + [(PUKE, 600)]


add("puke", "Throwing up", "faces", _puke())

PINK = (255, 70, 150)

KISS = sprite([
    "..YYYY..",
    ".YYYYYY.",
    "YKKYYKKY",
    "YYYYYYYY",
    "YYYYYYYY",
    "YYYRRYYY",
    ".YYRRYY.",
    "..YYYY..",
])
add("kiss", "Blowing a kiss", "faces",
    [(KISS, 900)] + [(overlay(KISS, [p], PINK), 200) for p in [(6, 4), (7, 3), (7, 1), (6, 0)]])

NERD_R = [
    "..YYYY..",
    ".YYYYYY.",
    "WWWWWWWW",
    "WKWYYWKW",
    "WWWYYWWW",
    "YYKKKKYY",
    ".YYWWYY.",
    "..YYYY..",
]
add("nerd", "Nerd pushing up glasses", "faces", [
    (sprite(NERD_R), 1500),
    (var(NERD_R, {1: "WWWWWWWW", 2: "WKWYYWKW", 3: "WWWYYWWW", 4: "YYYYYYYY"}), 300),
])

NERVOUS = sprite([
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYKYYKYY",
    "YKKKKKKY",
    "YKWWWWKY",
    ".YYYYYY.",
    "..YYYY..",
])
add("nervous", "Nervous sweat", "faces",
    [(NERVOUS, 900)] + [(overlay(NERVOUS, [p], TEAR), 200) for p in [(6, 1), (7, 2), (7, 3)]])

PARTY_R = [
    "...W....",
    "..MMM...",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYKYYKYY",
    "YKYYYYKY",
    ".YKKKKY.",
    "..YYYY..",
]
add("party", "Party hat and confetti", "faces", sparkle_on(
    sprite(PARTY_R), cells(PARTY_R, "."), count=3,
    colors=((255, 0, 0), (255, 190, 0), (0, 220, 0), (0, 200, 255), PINK)))

MONEY_R = [
    "..YYYY..",
    ".YYYYYY.",
    "YGGYYGGY",
    "YGGYYGGY",
    "YYYYYYYY",
    "YKKKKKKY",
    ".YKKKKY.",
    "..YYYY..",
]
add("money", "Money eyes", "faces",
    [(sprite(MONEY_R), 300), (var(MONEY_R, {2: "YggYYggY", 3: "YggYYggY"}), 300)])

ZIP_R = [
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYKYYKYY",
    "YYYYYYYY",
    "YKWKWKWY",
    ".YYYYWY.",
    "..YYYY..",
]
add("zipped", "Lips zipped", "faces", blink(sprite(ZIP_R), var(ZIP_R, {2: "YYYYYYYY", 3: "YKKYYKKY"})))

ANGEL_R = [
    "..CCCC..",
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYKYYKYY",
    "YKYYYYKY",
    ".YKKKKY.",
    "..YYYY..",
]
ANGEL = sprite(ANGEL_R)
add("angel", "Angel with a glowing halo", "faces", [(ANGEL, 500), (paint(ANGEL, cells(ANGEL_R, "C"), WHITE), 500)])

DIZZY = sprite([
    "..YYYY..",
    ".YYYYYY.",
    "YYYYYYYY",
    "YYYYYYYY",
    "YYYYYYYY",
    "YKYKKYKY",
    ".YYYYYY.",
    "..YYYY..",
])
_orbit_l = [(1, 2), (2, 2), (2, 3), (1, 3)]
_orbit_r = [(6, 3), (5, 3), (5, 2), (6, 2)]
add("dizzy", "Spinning eyes", "faces", [(overlay(DIZZY, [l, r], BLACK), 120) for l, r in zip(_orbit_l, _orbit_r)])

SICK = sprite([
    "..GGGG..",
    ".GGGGGG.",
    "GKKGGKKG",
    "GGGGGGGG",
    "GGGGGGGG",
    "GKGKKGKG",
    ".GGGGGG.",
    "..GGGG..",
])
add("sick", "Feeling sick", "faces", [(SICK, 400), (shift(SICK, dx=1), 400), (SICK, 400), (shift(SICK, dx=-1), 400)])

COLD = sprite([
    "..CCCC..",
    ".CCCCCC.",
    "CCKCCKCC",
    "CCCCCCCC",
    "CKKKKKKC",
    "CWKWKWKC",
    ".CCCCCC.",
    "..CCCC..",
])
add("cold", "Freezing and shivering", "faces", [(shift(COLD, dx=1), 60), (shift(COLD, dx=-1), 60)])

HOT = sprite([
    "..OOOO..",
    ".OOOOOO.",
    "OOKOOKOO",
    "OOOOOOOO",
    "OKKKKKKO",
    "OOORROOO",
    ".OOOOOO.",
    "..OOOO..",
])
add("hot", "Sweating in the heat", "faces", [
    (overlay(HOT, [(x, y) for x, y in ((0, 1 + k), (7, 2 + k)) if y < HEIGHT], TEAR), 150) for k in range(6)
])

SHUSH_R = [
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYKYYKYY",
    "YYYWYYYY",
    "YYKWKYYY",
    ".YYWYYY.",
    "..YWYY..",
]
_left, _right = "YKYYKYYY", "YYYKYYKY"
add("shush", "Shh!", "faces", [
    (sprite(SHUSH_R), 900), (var(SHUSH_R, {2: _left, 3: _left}), 600),
    (sprite(SHUSH_R), 300), (var(SHUSH_R, {2: _right, 3: _right}), 600),
])

_up = {1: ".YKYYKY.", 2: "YYKYYKYY", 3: "YYYYYYYY"}
add("eyeroll", "Rolling eyes", "faces", [
    (NEUTRAL, 1000),
    (var(NEUTRAL_R, _up), 200),
    (var(NEUTRAL_R, {1: ".YYKYYK.", 2: "YYYKYYKY", 3: "YYYYYYYY"}), 400),
    (var(NEUTRAL_R, _up), 200),
])

# --- icons ------------------------------------------------------------------

HEART = sprite([
    "........",
    ".RR..RR.",
    "RWRRRRRR",
    "RRRRRRRR",
    ".RRRRRR.",
    "..RRRR..",
    "...RR...",
    "........",
])
add("heart", "Glowing heart", "icons", pulse(HEART))

add("star", "Shiny gold star", "icons", shine(sprite([
    "...YY...",
    "...YY...",
    "YYYYYYYY",
    ".YYYYYY.",
    "..YYYY..",
    ".YYYYYY.",
    ".YY..YY.",
    "YY....YY",
])))

add("bolt", "Lightning flash", "icons", flash(sprite([
    "....YY..",
    "...YY...",
    "..YY....",
    ".YYYYYY.",
    "....YY..",
    "...YY...",
    "..YY....",
    ".Y......",
])))

_check = draw_in(sprite([
    "........",
    ".......G",
    "......GG",
    ".....GG.",
    "G...GG..",
    "GG.GG...",
    ".GGG....",
    "..G.....",
]), key=lambda x, y: (x, y))
add("check", "Check mark drawing itself", "icons", _check, thumb_step=len(_check) - 2)

_cross = draw_in(sprite([
    "R......R",
    ".R....R.",
    "..R..R..",
    "...RR...",
    "...RR...",
    "..R..R..",
    ".R....R.",
    "R......R",
]), key=lambda x, y: (x != y, x))
add("cross", "X drawing itself", "icons", _cross, thumb_step=len(_cross) - 2)

add("question", "Bouncing question mark", "icons", bob(sprite([
    "..BBBB..",
    ".BB..BB.",
    ".....BB.",
    "....BB..",
    "...BB...",
    "...BB...",
    "........",
    "...BB...",
])))

add("exclaim", "Blinking exclamation mark", "icons", [(sprite([
    "...RR...",
    "...RR...",
    "...RR...",
    "...RR...",
    "...RR...",
    "........",
    "...RR...",
    "...RR...",
]), 500), (blank(), 250)])

add("note", "Bouncing music note", "icons", bob(sprite([
    "...MM...",
    "...MMM..",
    "...M.MM.",
    "...M..M.",
    "...M....",
    ".MMM....",
    "MMMM....",
    ".MM.....",
]), 300))

add("thumbsup", "Thumbs up", "icons", bob(sprite([
    "...Y....",
    "..YY....",
    "..YY....",
    "BYYYYYY.",
    "BYYYYYYY",
    "BYYYYYY.",
    "BYYYYYYY",
    "BYYYYYY.",
]), 400))

add("sun", "Sun with turning rays", "icons", [(sprite([
    "...YY...",
    ".Y....Y.",
    "..YYYY..",
    "Y.YYYY.Y",
    "Y.YYYY.Y",
    "..YYYY..",
    ".Y....Y.",
    "...YY...",
]), 400), (sprite([
    "..O..O..",
    "O......O",
    "..YYYY..",
    "..YYYY..",
    "..YYYY..",
    "..YYYY..",
    "O......O",
    "..O..O..",
]), 400)])

MOON = sprite([
    "..YYYY..",
    ".YYY....",
    "YYY.....",
    "YY......",
    "YY......",
    "YYY.....",
    ".YYY....",
    "..YYYY..",
])


def _moon():
    while True:
        f = list(MOON)
        for x, y in ((6, 1), (5, 4), (7, 6)):
            v = random.choice((30, 120, 255))
            f[y * WIDTH + x] = (v, v, v)
        yield f, 250


add("moon", "Moon and twinkling stars", "icons", _moon)

add("cloud", "Drifting cloud", "icons", slide(sprite([
    "........",
    "........",
    "...WW...",
    "..WWWWW.",
    ".WWWWWWW",
    "WWWWWWWW",
    ".WWWWWW.",
    "........",
]), dx=1, ms=250))

add("snowflake", "Glittering snowflake", "icons", sparkle_on(sprite([
    "C..C..C.",
    ".C.C.C..",
    "..CCC...",
    "CCCCCCC.",
    "..CCC...",
    ".C.C.C..",
    "C..C..C.",
    "........",
])))

add("tree", "Tree with blinking lights", "icons", sparkle_on(sprite([
    "...YY...",
    "..GGGG..",
    ".GGGGGG.",
    "..GGGG..",
    ".GGGGGG.",
    "GGGGGGGG",
    "...NN...",
    "...NN...",
]), count=5, ms=400, colors=((255, 0, 0), (255, 190, 0), (0, 70, 255), (255, 70, 150), WHITE)))

FLOWER = sprite([
    "...PP...",
    "..PYYP..",
    "..PYYP..",
    "...PP...",
    "G..GG..G",
    ".G.GG.G.",
    "..GGGG..",
    "...GG...",
])


def _sway(d):
    top = shift(FLOWER, dx=d)
    return top[:4 * WIDTH] + FLOWER[4 * WIDTH:]


add("flower", "Flower in the wind", "icons", [(_sway(d), 350) for d in (0, 1, 0, -1)])

CROWN = sprite([
    "........",
    "Y..YY..Y",
    "YY.YY.YY",
    "YYYYYYYY",
    "YRYBBYRY",
    "YYYYYYYY",
    "YYYYYYYY",
    "........",
])
add("crown", "Shiny crown", "icons", shine(CROWN))


def _rainbow_crown():
    area, t = lit(CROWN), 0.0
    while True:
        f = blank()
        for i in area:
            f[i] = hsv((i % WIDTH + i // WIDTH) / 12 - t)
        for i in random.sample(area, 1):
            f[i] = WHITE
        yield f, 50
        t += 0.03


add("rgbcrown", "Crown cycling through rainbow colors", "icons", _rainbow_crown)

EGGPLANT = sprite([
    "......G.",
    "....GGG.",
    "...MGG..",
    "..MMMM..",
    ".MWMMM..",
    "MMMMMM..",
    "MMMMM...",
    ".MMM....",
])
add("eggplant", "Wiggling eggplant", "icons",
    [(EGGPLANT, 250), (shift(EGGPLANT, dx=1), 250), (EGGPLANT, 250), (shift(EGGPLANT, dx=-1), 250)]
    + shine(EGGPLANT, hold=500))

add("diamond", "Sparkling diamond", "icons", shine(sprite([
    "........",
    ".CCCCCC.",
    "CWCCCCCC",
    "CCCCCCCC",
    ".CCCCCC.",
    "..CCCC..",
    "...CC...",
    "........",
])))

add("trophy", "Shiny trophy", "icons", shine(sprite([
    "YYYYYYYY",
    "Y.YYYY.Y",
    ".YYYYYY.",
    "..YYYY..",
    "...YY...",
    "...YY...",
    "..YYYY..",
    ".YYYYYY.",
])))

GAMEPAD = sprite([
    "........",
    "........",
    ".BBBBBB.",
    "BBWBBBRB",
    "BWWWBGBB",
    "BBWBBBBB",
    "BB....BB",
    "........",
])
add("gamepad", "Controller, buttons blinking", "icons", [
    (overlay(GAMEPAD, [(5, 4)], (0, 60, 0)), 300),
    (overlay(GAMEPAD, [(6, 3)], (90, 0, 0)), 300),
])

COFFEE_R = [
    ".w.w....",
    "..w.w...",
    "........",
    "WWWWWW..",
    "WNNNNWWW",
    "WNNNNW.W",
    "WNNNNWWW",
    ".WWWW...",
]
add("coffee", "Steaming coffee", "icons",
    [(sprite(COFFEE_R), 350), (var(COFFEE_R, {0: "..w.w...", 1: ".w.w...."}), 350)])

add("pizza", "Cheesy pizza slice", "icons", bob(sprite([
    "NNNNNNNN",
    "YYRYYYRY",
    ".YYYYYY.",
    ".YYYRYY.",
    "..YYYY..",
    "..YRYY..",
    "...YY...",
    "...YY...",
]), 400))

BEER = sprite([
    "........",
    ".WWWWW..",
    ".YYYYYWW",
    ".YYYYY.W",
    ".YYYYY.W",
    ".YYYYYWW",
    ".YYYYY..",
    ".YYYYY..",
])


def _beer():
    bubbles = []
    while True:
        f = list(BEER)
        if random.random() < 0.6:
            bubbles.append([random.randint(1, 5), 7])
        for b in bubbles:
            b[1] -= 1
        bubbles = [b for b in bubbles if b[1] >= 2]
        for x, y in bubbles:
            f[y * WIDTH + x] = (255, 245, 200)
        for x in range(1, 6):
            if random.random() < 0.35:
                f[x] = WHITE
        yield f, 120


add("beer", "Fizzy beer", "icons", _beer)

MIC = sprite([
    "..WWWW..",
    "..WWWW..",
    "..WWWW..",
    "W.WWWW.W",
    ".W....W.",
    "..WWWW..",
    "...WW...",
    "..WWWW..",
])
_wave1 = overlay(MIC, [(1, 1), (6, 1)], (0, 200, 255))
add("mic", "Microphone picking up sound", "icons",
    [(MIC, 250), (_wave1, 250), (overlay(_wave1, [(0, 0), (0, 2), (7, 0), (7, 2)], (0, 200, 255)), 250)])

MUTED = overlay(MIC, [(i, i) for i in range(8)], (255, 0, 0))
add("muted", "Muted microphone", "icons", [(MUTED, 600), (MIC, 300)])

add("play", "Play", "icons", pulse(sprite([
    "..G.....",
    "..GG....",
    "..GGG...",
    "..GGGG..",
    "..GGGG..",
    "..GGG...",
    "..GG....",
    "..G.....",
])))

add("pause", "Pause", "icons", pulse(sprite([
    "........",
    ".WW..WW.",
    ".WW..WW.",
    ".WW..WW.",
    ".WW..WW.",
    ".WW..WW.",
    ".WW..WW.",
    "........",
])))

_UP = sprite([
    "...GG...",
    "..GGGG..",
    ".GGGGGG.",
    "GGGGGGGG",
    "...GG...",
    "...GG...",
    "...GG...",
    "...GG...",
])
add("up", "Arrow up", "icons", slide(_UP, dy=-1))
add("right", "Arrow right", "icons", slide(rotate(_UP), dx=1))
add("down", "Arrow down", "icons", slide(rotate(rotate(_UP)), dy=1))
add("left", "Arrow left", "icons", slide(rotate(rotate(rotate(_UP))), dx=-1))

# --- sprite animations ------------------------------------------------------

SMALL_HEART = sprite([
    "........",
    "........",
    "..R..R..",
    ".RRRRRR.",
    ".RRRRRR.",
    "..RRRR..",
    "...RR...",
    "........",
])
WINK = var(SMILEY_R, {2: "YYKYYYYY", 3: "YYKYYKKY"})
REC = sprite([
    "..RRRR..",
    ".RRRRRR.",
    "RRRRRRRR",
    "RRRRRRRR",
    "RRRRRRRR",
    "RRRRRRRR",
    ".RRRRRR.",
    "..RRRR..",
])


@animation("heartbeat", "Beating heart")
def heartbeat():
    return [(HEART, 140), (SMALL_HEART, 140), (HEART, 140), (SMALL_HEART, 650)]


@animation("wink", "Smiley that winks")
def wink():
    return [(SMILEY, 1800), (WINK, 300)]


@animation("rec", "Pulsing red recording dot")
def rec():
    n = 30
    return [(scale(REC, 0.2 + 0.8 * (0.5 + 0.5 * math.cos(2 * math.pi * i / n))), 50) for i in range(n)]


@animation("police", "Red and blue flashers")
def police():
    left = [(255, 0, 0) if i % WIDTH < 4 else BLACK for i in range(64)]
    right = [(0, 40, 255) if i % WIDTH >= 4 else BLACK for i in range(64)]
    off = blank()
    return [(left, 90), (off, 50), (left, 90), (off, 50), (right, 90), (off, 50), (right, 90), (off, 50)]


@animation("countdown", "3, 2, 1, GO!", thumb_step=0)
def countdown():
    steps = [(text_steps(n, (255, 190, 0))[0][0], 800) for n in "321"]
    return steps + [(text_steps("GO", (0, 220, 0))[0][0], 1500), (blank(), 500)]


@animation("typing", "Typing dots", thumb_step=1)
def typing():
    frames = []
    for active in range(4):
        f = blank()
        for k, x in enumerate((0, 3, 6)):
            color = (255, 255, 255) if k == active else (60, 60, 60)
            for dx in (0, 1):
                for y in (3, 4):
                    f[y * WIDTH + x + dx] = color
        frames.append((f, 250))
    return frames


@animation("loading", "Loading bar", thumb_step=5)
def loading():
    steps = []
    for n in range(WIDTH + 1):
        f = blank()
        for x in range(WIDTH):
            f[2 * WIDTH + x] = f[5 * WIDTH + x] = (60, 60, 60)
            if x < n:
                f[3 * WIDTH + x] = f[4 * WIDTH + x] = hsv(0.33 * x / WIDTH)
        steps.append((f, 900 if n == WIDTH else 180))
    return steps


_PIPS = {"tl": (0, 0), "tr": (6, 0), "ml": (0, 3), "c": (3, 3), "mr": (6, 3), "bl": (0, 6), "br": (6, 6)}
_DICE = {1: ["c"], 2: ["tl", "br"], 3: ["tl", "c", "br"], 4: ["tl", "tr", "bl", "br"],
         5: ["tl", "tr", "c", "bl", "br"], 6: ["tl", "tr", "ml", "mr", "bl", "br"]}


def _die(n):
    f = blank()
    for pip in _DICE[n]:
        x, y = _PIPS[pip]
        for dx in (0, 1):
            for dy in (0, 1):
                f[(y + dy) * WIDTH + x + dx] = (255, 255, 255)
    return f


@animation("dice", "Roll a die")
def dice():
    steps = [(_die(random.randint(1, 6)), 60 + 25 * i) for i in range(10)]
    return steps + [(_die(random.randint(1, 6)), 2500)]


# --- procedural animations --------------------------------------------------

@animation("rainbow", "Diagonal rainbow sweep", thumb_step=1)
def rainbow():
    t = 0.0
    while True:
        yield [hsv((x + y) / 16 + t) for y in range(HEIGHT) for x in range(WIDTH)], 40
        t += 0.015


@animation("colorcycle", "Whole display fades through colors")
def colorcycle():
    t = 0.0
    while True:
        yield blank(hsv(t)), 40
        t += 0.005


@animation("breathe", "Slow breathing glow", thumb_step=10)
def breathe():
    t = 0.0
    while True:
        yield blank(hsv(t / 20, 1, 0.1 + 0.9 * (0.5 - 0.5 * math.cos(t)))), 40
        t += 0.08


def _plasma(color):
    t = 0.0
    while True:
        f = []
        for y in range(HEIGHT):
            for x in range(WIDTH):
                v = (math.sin(x / 2 + t) + math.sin(y / 3 + t * 1.3)
                     + math.sin((x + y) / 3 + t * 0.7) + math.sin(math.hypot(x - 3.5, y - 3.5) / 1.5 - t))
                f.append(color(v / 8, t))
        yield f, 40
        t += 0.08


def _heat_color(h):
    h = max(0.0, min(1.0, h)) * 3
    return int(min(1, h) * 255), int(max(0, min(1, h - 1)) * 200), int(max(0, min(1, h - 2)) * 120)


@animation("plasma", "Psychedelic plasma", thumb_step=5)
def plasma():
    return _plasma(lambda v, t: hsv(v + t / 10))


@animation("lava", "Lava lamp", thumb_step=5)
def lava():
    return _plasma(lambda v, t: _heat_color(0.45 + v * 1.6))


@animation("ocean", "Deep blue waves", thumb_step=5)
def ocean():
    return _plasma(lambda v, t: hsv(0.58 + v / 3, 1, 0.45 + v * 1.2))


@animation("fire", "Crackling fire", thumb_step=15)
def fire():
    heat = [[0.0] * WIDTH for _ in range(HEIGHT + 1)]
    while True:
        heat[HEIGHT] = [random.uniform(0.6, 1.0) for _ in range(WIDTH)]
        for y in range(HEIGHT):
            below = heat[y + 1]
            heat[y] = [max(0.0, (below[x] * 2 + below[max(x - 1, 0)] + below[min(x + 1, WIDTH - 1)]) / 4
                           - random.uniform(0.06, 0.22)) for x in range(WIDTH)]
        yield [_heat_color(heat[y][x]) for y in range(HEIGHT) for x in range(WIDTH)], 60


@animation("matrix", "Digital green rain", thumb_step=20)
def matrix():
    level = [0.0] * (WIDTH * HEIGHT)
    drops = [[random.uniform(-8, 0), random.uniform(0.3, 0.8)] for _ in range(WIDTH)]
    while True:
        level = [v * 0.65 for v in level]
        for x, drop in enumerate(drops):
            drop[0] += drop[1]
            y = int(drop[0])
            if 0 <= y < HEIGHT:
                level[y * WIDTH + x] = 1.0
            if drop[0] > HEIGHT + 4:
                drop[:] = [random.uniform(-6, 0), random.uniform(0.3, 0.8)]
        yield [(int(90 * v ** 3), int(255 * v), int(90 * v ** 3)) for v in level], 50


def _falling(count, speed, color, trail, delay):
    flakes = [[random.uniform(0, WIDTH), random.uniform(-HEIGHT, HEIGHT), random.uniform(*speed), color()]
              for _ in range(count)]
    while True:
        f = blank()
        for fl in flakes:
            fl[1] += fl[2]
            if fl[1] > HEIGHT + trail:
                fl[:] = [random.uniform(0, WIDTH), -1.0, random.uniform(*speed), color()]
            x = int(fl[0]) % WIDTH
            for k in range(trail + 1):
                y = int(fl[1]) - k
                if 0 <= y < HEIGHT:
                    f[y * WIDTH + x] = scale([fl[3]], 1 - k / (trail + 1))[0]
        yield f, delay


@animation("snow", "Gentle snowfall", thumb_step=30)
def snow():
    return _falling(10, (0.06, 0.15), lambda: (200, 220, 255), 0, 60)


@animation("rain", "Rain", thumb_step=10)
def rain():
    return _falling(9, (0.5, 0.9), lambda: (40, 120, 255), 2, 40)


@animation("confetti", "Falling confetti", thumb_step=20)
def confetti():
    return _falling(14, (0.15, 0.35), lambda: hsv(random.random()), 0, 50)


@animation("equalizer", "Bouncing audio bars", thumb_step=10)
def equalizer():
    heights = [0.0] * WIDTH
    targets = [0.0] * WIDTH
    while True:
        for x in range(WIDTH):
            if random.random() < 0.3:
                targets[x] = random.uniform(1, HEIGHT)
            heights[x] += (targets[x] - heights[x]) * 0.45
        f = blank()
        for x in range(WIDTH):
            for level in range(int(round(heights[x]))):
                color = (0, 220, 0) if level < 4 else (255, 190, 0) if level < 6 else (255, 0, 0)
                f[(HEIGHT - 1 - level) * WIDTH + x] = color
        yield f, 70


_RING = ([(x, 0) for x in range(8)] + [(7, y) for y in range(1, 8)]
         + [(x, 7) for x in range(6, -1, -1)] + [(0, y) for y in range(6, 0, -1)])


@animation("spinner", "Rainbow loading spinner", thumb_step=8)
def spinner():
    i = 0
    while True:
        f = blank()
        for k in range(10):
            x, y = _RING[(i - k) % len(_RING)]
            f[y * WIDTH + x] = hsv(i / len(_RING), 1, 1 - k / 10)
        yield f, 45
        i += 1


@animation("radar", "Radar sweep", thumb_step=12)
def radar():
    level = [0.0] * (WIDTH * HEIGHT)
    angle = 0.0
    while True:
        level = [v * 0.85 for v in level]
        for k in range(1, 10):
            x = int(round(3.5 + math.cos(angle) * k * 0.5))
            y = int(round(3.5 + math.sin(angle) * k * 0.5))
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                level[y * WIDTH + x] = 1.0
        angle += 0.2
        yield [(0, int(255 * v), int(70 * v)) for v in level], 40


@animation("scanner", "Sweeping scanner light", thumb_step=4)
def scanner():
    level = [0.0] * WIDTH
    pos, d = 0, 1
    while True:
        level = [v * 0.55 for v in level]
        level[pos] = 1.0
        yield [(int(255 * level[x]), 0, 0) if y in (3, 4) else BLACK
               for y in range(HEIGHT) for x in range(WIDTH)], 70
        if not 0 <= pos + d < WIDTH:
            d = -d
        pos += d


@animation("wave", "Rainbow sine wave", thumb_step=3)
def wave():
    t = 0.0
    while True:
        f = blank()
        for x in range(WIDTH):
            y = min(HEIGHT - 1, max(0, int(round(3.5 + 3 * math.sin(x / 1.3 + t)))))
            f[y * WIDTH + x] = hsv(x / 8 + t / 6)
        yield f, 50
        t += 0.25


@animation("ripple", "Raindrop ripples", thumb_step=12)
def ripple():
    drops = []
    while True:
        if not drops or random.random() < 0.06:
            drops.append([random.uniform(0, 7), random.uniform(0, 7), 0.0, random.random()])
        f = []
        for y in range(HEIGHT):
            for x in range(WIDTH):
                best_v, best_h = 0.0, 0.0
                for cx, cy, t, h in drops:
                    v = max(0.0, 1 - abs(math.hypot(x - cx, y - cy) - t)) * max(0.0, 1 - t / 8)
                    if v > best_v:
                        best_v, best_h = v, h
                f.append(hsv(best_h, 1, best_v))
        for d in drops:
            d[2] += 0.3
        drops = [d for d in drops if d[2] < 8]
        yield f, 50


@animation("warp", "Flying through stars", thumb_step=15)
def warp():
    stars = [[random.uniform(0, 2 * math.pi), random.uniform(0.3, 5)] for _ in range(12)]
    while True:
        f = blank()
        for s in stars:
            s[1] *= 1.12
            x = int(round(3.5 + math.cos(s[0]) * s[1]))
            y = int(round(3.5 + math.sin(s[0]) * s[1]))
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                v = int(255 * min(1.0, s[1] / 4))
                f[y * WIDTH + x] = (v, v, v)
            else:
                s[:] = [random.uniform(0, 2 * math.pi), 0.3]
        yield f, 50


@animation("sparkle", "Random twinkling stars", thumb_step=20)
def sparkle():
    level = [0.0] * (WIDTH * HEIGHT)
    hues = [0.0] * (WIDTH * HEIGHT)
    while True:
        level = [v * 0.85 for v in level]
        for _ in range(2):
            i = random.randrange(len(level))
            level[i], hues[i] = 1.0, random.random()
        yield [hsv(h, 0.5, v) for h, v in zip(hues, level)], 50


@animation("fireworks", "Fireworks", thumb_step=40)
def fireworks():
    buf = [(0.0, 0.0)] * (WIDTH * HEIGHT)
    rockets, sparks = [], []
    while True:
        buf = [(v * 0.7, h) for v, h in buf]
        if len(rockets) < 2 and random.random() < 0.07:
            rockets.append([random.randint(1, 6), 7.0, random.uniform(1, 3), random.random()])
        for r in rockets[:]:
            r[1] -= 0.5
            _plot(buf, r[0], r[1], 1.0, r[3])
            if r[1] <= r[2]:
                rockets.remove(r)
                for _ in range(14):
                    a, s = random.uniform(0, 2 * math.pi), random.uniform(0.2, 0.6)
                    sparks.append([r[0], r[1], math.cos(a) * s, math.sin(a) * s, 1.0, r[3]])
        for s in sparks[:]:
            s[0] += s[2]
            s[1] += s[3]
            s[3] += 0.04
            s[4] -= 0.05
            if s[4] <= 0:
                sparks.remove(s)
            else:
                _plot(buf, s[0], s[1], s[4], s[5])
        yield [hsv(h, 0.8, v) for v, h in buf], 50


@animation("bounce", "Bouncing ball with a trail", thumb_step=12)
def bounce():
    x, y, dx, dy = 1.0, 2.0, 0.45, 0.31
    level = [0.0] * (WIDTH * HEIGHT)
    hue = 0.0
    while True:
        x, y = x + dx, y + dy
        if not 0 <= x <= WIDTH - 1:
            dx, x = -dx, max(0.0, min(WIDTH - 1.0, x))
        if not 0 <= y <= HEIGHT - 1:
            dy, y = -dy, max(0.0, min(HEIGHT - 1.0, y))
        level = [v * 0.7 for v in level]
        level[int(round(y)) * WIDTH + int(round(x))] = 1.0
        hue += 0.01
        yield [hsv(hue, 1, v) for v in level], 40


@animation("snake", "Snake that plays itself", thumb_step=25)
def snake():
    cells = [(x, y) for y in range(HEIGHT) for x in range(WIDTH)]

    def wrap_dist(a, b):
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        return min(dx, WIDTH - dx) + min(dy, HEIGHT - dy)

    while True:
        body = [(3, 4), (2, 4), (1, 4)]
        food = random.choice([c for c in cells if c not in body])
        while True:
            hx, hy = body[0]
            moves = [((hx + dx) % WIDTH, (hy + dy) % HEIGHT) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            safe = [m for m in moves if m not in body[:-1]]
            if not safe:
                break
            head = min(safe, key=lambda m: (wrap_dist(m, food), random.random()))
            body.insert(0, head)
            if head == food:
                free = [c for c in cells if c not in body]
                if len(body) > 30 or not free:
                    break
                food = random.choice(free)
            else:
                body.pop()
            f = blank()
            for i, (x, y) in enumerate(body):
                f[y * WIDTH + x] = hsv(0.3 + 0.2 * i / len(body), 1, 1 - 0.6 * i / len(body))
            f[food[1] * WIDTH + food[0]] = (255, 0, 0)
            yield f, 110
        yield blank((90, 0, 0)), 300


@animation("life", "Conway's Game of Life", thumb_step=3)
def life():
    def seed():
        return [random.random() < 0.35 for _ in range(WIDTH * HEIGHT)]

    cells, history, gen = seed(), [], 0
    while True:
        yield [hsv(gen / 40 + i / 128) if c else BLACK for i, c in enumerate(cells)], 180
        nxt = []
        for y in range(HEIGHT):
            for x in range(WIDTH):
                n = sum(cells[((y + dy) % HEIGHT) * WIDTH + (x + dx) % WIDTH]
                        for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy)
                nxt.append(n == 3 or (n == 2 and cells[y * WIDTH + x]))
        history = (history + [cells])[-4:]
        cells, gen = nxt, gen + 1
        if not any(cells) or cells in history or gen > 300:
            cells, history, gen = seed(), [], 0


@animation("clock", "Scrolling current time", thumb_step=9)
def clock():
    while True:
        yield from text_steps(time.strftime("%H:%M"), (0, 200, 255), 110)


# --- text -------------------------------------------------------------------

for _word, _color, _desc in [
    ("LIVE", (255, 0, 0), "Scrolling LIVE"),
    ("BRB", None, "Be right back"),
    ("AFK", (0, 200, 255), "Away from keyboard"),
    ("HYPE", None, "Hype!"),
    ("GG", (0, 220, 0), "Good game"),
    ("GL", (0, 200, 255), "Good luck"),
    ("HI", (255, 190, 0), "Hi!"),
    ("LOL", None, "LOL"),
    ("OMG", (255, 70, 150), "OMG"),
    ("POG", None, "POG"),
    ("FOLLOW", (170, 0, 255), "Follow reminder"),
    ("SUB", (255, 190, 0), "Subscribe reminder"),
    ("THANKS", None, "Thank you"),
]:
    _steps = text_steps(_word, _color)
    _register(_word.lower(), _desc, "text", (lambda s=_steps: s), thumb_step=min(9, len(_steps) - 1))

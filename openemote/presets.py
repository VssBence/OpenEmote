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
from .frame import BLACK, HEIGHT, WIDTH, Frame, blank, hsv, rotate, scale, sprite

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
        return self.category in ("animated", "text")

    def thumbnail(self) -> Frame:
        frame = blank()
        for i, (frame, _) in enumerate(self.factory()):
            if i >= self.thumb_step:
                break
        return frame


PRESETS: dict[str, Preset] = {}


def _register(name, description, category, factory, thumb_step=0):
    if name in PRESETS:
        raise ValueError(f"duplicate preset name {name!r}")
    PRESETS[name] = Preset(name, description, category, factory, thumb_step)


def static(name, description, art, category="icons"):
    frame = art if isinstance(art[0], tuple) else sprite(art)
    _register(name, description, category, lambda: [(frame, 1000)])
    return frame


def face(name, description, rows):
    return static(name, description, rows, "faces")


def animation(name, description, thumb_step=0):
    def deco(fn):
        _register(name, description, "animated", fn, thumb_step)
        return fn
    return deco


def _plot(buf, x, y, v, h):
    xi, yi = int(round(x)), int(round(y))
    if 0 <= xi < WIDTH and 0 <= yi < HEIGHT and v > buf[yi * WIDTH + xi][0]:
        buf[yi * WIDTH + xi] = (v, h)


# --- faces ------------------------------------------------------------------

SMILEY = face("smiley", "Classic yellow smiley", [
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYYYYYYY",
    "YKYYYYKY",
    "YYKKKKYY",
    ".YYYYYY.",
    "..YYYY..",
])
face("sad", "Sad face", [
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYYYYYYY",
    "YYYKKYYY",
    "YYKYYKYY",
    ".YYYYYY.",
    "..YYYY..",
])
face("wow", "Surprised face", [
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYYYYYYY",
    "YYYKKYYY",
    "YYYKKYYY",
    ".YYYYYY.",
    "..YYYY..",
])
face("love", "Heart eyes", [
    "..YYYY..",
    ".YYYYYY.",
    "YRRYYRRY",
    "YYRYYRYY",
    "YYYYYYYY",
    "YKYYYYKY",
    ".YKKKKY.",
    "..YYYY..",
])
face("cool", "Sunglasses", [
    "..YYYY..",
    ".YYYYYY.",
    "KKKKKKKK",
    "YKKYYKKY",
    "YYYYYYYY",
    "YKYYYYKY",
    ".YKKKKY.",
    "..YYYY..",
])
face("laugh", "XD", [
    "..YYYY..",
    ".YYYYYY.",
    "YKYYYYKY",
    "YYKYYKYY",
    "YKYYYYKY",
    "YKKKKKKY",
    ".YKRRKY.",
    "..YYYY..",
])
face("cry", "Crying", [
    "..YYYY..",
    ".YYYYYY.",
    "YKKYYKKY",
    "YBYYYYBY",
    "YBYKKYBY",
    "YYKYYKYY",
    ".YYYYYY.",
    "..YYYY..",
])
face("angry", "Angry red face", [
    "..RRRR..",
    ".RRRRRR.",
    "RKRRRRKR",
    "RRKRRKRR",
    "RRRRRRRR",
    "RRKKKKRR",
    ".KRRRRK.",
    "..RRRR..",
])
face("sleepy", "Eyes closed", [
    "..YYYY..",
    ".YYYYYY.",
    "YKKYYKKY",
    "YYYYYYYY",
    "YYYYYYYY",
    "YYYKKYYY",
    ".YYYYYY.",
    "..YYYY..",
])
face("tongue", "Tongue out", [
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYYYYYYY",
    "YKKKKKKY",
    "YYYRRYYY",
    ".YYRRYY.",
    "..YYYY..",
])
face("neutral", "Straight face", [
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYYYYYYY",
    "YYYYYYYY",
    "YYKKKKYY",
    ".YYYYYY.",
    "..YYYY..",
])
face("smirk", "Smirk", [
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKYY",
    "YYYYYYYY",
    "YYYYYYKY",
    "YYKKKKYY",
    ".YYYYYY.",
    "..YYYY..",
])
face("devil", "Little devil", [
    "M......M",
    ".M.MM.M.",
    ".MMMMMM.",
    "MYMMMMYM",
    "MMMMMMMM",
    "MKMMMMKM",
    ".MKKKKM.",
    "..MMMM..",
])
face("robot", "Robot", [
    "...RR...",
    "...WW...",
    "WWWWWWWW",
    "WCCWWCCW",
    "WWWWWWWW",
    "WKKKKKKW",
    "WWWWWWWW",
    ".W....W.",
])
face("frog", "Frog", [
    ".GG..GG.",
    "GWKGGWKG",
    "GGGGGGGG",
    "GGGGGGGG",
    "GKGGGGKG",
    "GGKKKKGG",
    ".GGGGGG.",
    "........",
])
face("cat", "Orange cat", [
    "O......O",
    "OO....OO",
    "OOOOOOOO",
    "OKOOOOKO",
    "OOOOOOOO",
    "OOOPPOOO",
    ".OOOOOO.",
    "..OOOO..",
])
face("alien", "Little green alien", [
    "..GGGG..",
    ".GGGGGG.",
    "GGGGGGGG",
    "GKKGGKKG",
    "GKKGGKKG",
    ".GGGGGG.",
    "..GKKG..",
    "...GG...",
])
face("skull", "Skull", [
    ".WWWWWW.",
    "WWWWWWWW",
    "WKKWWKKW",
    "WKKWWKKW",
    "WWWKKWWW",
    ".WWWWWW.",
    "..W.W.W.",
    "..WWWWW.",
])
face("ghost", "Boo!", [
    "..WWWW..",
    ".WWWWWW.",
    "WWKWWKWW",
    "WWKWWKWW",
    "WWWWWWWW",
    "WWWKKWWW",
    "WWWWWWWW",
    "WW.WW.WW",
])
face("pumpkin", "Jack-o'-lantern", [
    "...gg...",
    "..OOOO..",
    ".OOOOOO.",
    "OOKOOKOO",
    "OOOOOOOO",
    "OKOKKOKO",
    ".OOOOOO.",
    "..OOOO..",
])
face("poop", "Happy poop", [
    "....N...",
    "...NN...",
    "..NNNN..",
    ".NWNNWN.",
    ".NNNNNN.",
    "NNNNNNNN",
    "NWNNNNWN",
    ".NWWWWN.",
])

# --- icons ------------------------------------------------------------------

HEART = static("heart", "Red heart", [
    "........",
    ".RR..RR.",
    "RWRRRRRR",
    "RRRRRRRR",
    ".RRRRRR.",
    "..RRRR..",
    "...RR...",
    "........",
])
static("star", "Gold star", [
    "...YY...",
    "...YY...",
    "YYYYYYYY",
    ".YYYYYY.",
    "..YYYY..",
    ".YYYYYY.",
    ".YY..YY.",
    "YY....YY",
])
static("bolt", "Lightning bolt", [
    "....YY..",
    "...YY...",
    "..YY....",
    ".YYYYYY.",
    "....YY..",
    "...YY...",
    "..YY....",
    ".Y......",
])
static("check", "Green check mark", [
    "........",
    ".......G",
    "......GG",
    ".....GG.",
    "G...GG..",
    "GG.GG...",
    ".GGG....",
    "..G.....",
])
static("cross", "Red X", [
    "R......R",
    ".R....R.",
    "..R..R..",
    "...RR...",
    "...RR...",
    "..R..R..",
    ".R....R.",
    "R......R",
])
static("question", "Question mark", [
    "..BBBB..",
    ".BB..BB.",
    ".....BB.",
    "....BB..",
    "...BB...",
    "...BB...",
    "........",
    "...BB...",
])
static("exclaim", "Exclamation mark", [
    "...RR...",
    "...RR...",
    "...RR...",
    "...RR...",
    "...RR...",
    "........",
    "...RR...",
    "...RR...",
])
static("note", "Music note", [
    "...MM...",
    "...MMM..",
    "...M.MM.",
    "...M..M.",
    "...M....",
    ".MMM....",
    "MMMM....",
    ".MM.....",
])
static("thumbsup", "Thumbs up", [
    "...Y....",
    "..YY....",
    "..YY....",
    "BYYYYYY.",
    "BYYYYYYY",
    "BYYYYYY.",
    "BYYYYYYY",
    "BYYYYYY.",
])
static("sun", "Sun", [
    "...YY...",
    ".Y....Y.",
    "..YYYY..",
    "Y.YYYY.Y",
    "Y.YYYY.Y",
    "..YYYY..",
    ".Y....Y.",
    "...YY...",
])
static("moon", "Crescent moon", [
    "..YYYY..",
    ".YYY....",
    "YYY.....",
    "YY......",
    "YY......",
    "YYY.....",
    ".YYY....",
    "..YYYY..",
])
CLOUD = static("cloud", "Cloud", [
    "........",
    "........",
    "...WW...",
    "..WWWWW.",
    ".WWWWWWW",
    "WWWWWWWW",
    ".WWWWWW.",
    "........",
])
static("snowflake", "Snowflake", [
    "C..C..C.",
    ".C.C.C..",
    "..CCC...",
    "CCCCCCC.",
    "..CCC...",
    ".C.C.C..",
    "C..C..C.",
    "........",
])
static("tree", "Pine tree", [
    "...GG...",
    "..GGGG..",
    ".GGGGGG.",
    "..GGGG..",
    ".GGGGGG.",
    "GGGGGGGG",
    "...NN...",
    "...NN...",
])
static("flower", "Flower", [
    "...PP...",
    "..PYYP..",
    "..PYYP..",
    "...PP...",
    "G..GG..G",
    ".G.GG.G.",
    "..GGGG..",
    "...GG...",
])
static("crown", "Crown", [
    "........",
    "Y..YY..Y",
    "YY.YY.YY",
    "YYYYYYYY",
    "YRYBBYRY",
    "YYYYYYYY",
    "YYYYYYYY",
    "........",
])
static("diamond", "Diamond", [
    "........",
    ".CCCCCC.",
    "CWCCCCCC",
    "CCCCCCCC",
    ".CCCCCC.",
    "..CCCC..",
    "...CC...",
    "........",
])
static("trophy", "Trophy", [
    "YYYYYYYY",
    "Y.YYYY.Y",
    ".YYYYYY.",
    "..YYYY..",
    "...YY...",
    "...YY...",
    "..YYYY..",
    ".YYYYYY.",
])
static("gamepad", "Game controller", [
    "........",
    "........",
    ".BBBBBB.",
    "BBWBBBRB",
    "BWWWBGBB",
    "BBWBBBBB",
    "BB....BB",
    "........",
])
static("coffee", "Coffee break", [
    ".w.w....",
    "..w.w...",
    "........",
    "WWWWWW..",
    "WNNNNWWW",
    "WNNNNW.W",
    "WNNNNWWW",
    ".WWWW...",
])
static("pizza", "Pizza slice", [
    "NNNNNNNN",
    "YYRYYYRY",
    ".YYYYYY.",
    ".YYYRYY.",
    "..YYYY..",
    "..YRYY..",
    "...YY...",
    "...YY...",
])
MIC = static("mic", "Microphone", [
    "..WWWW..",
    "..WWWW..",
    "..WWWW..",
    "W.WWWW.W",
    ".W....W.",
    "..WWWW..",
    "...WW...",
    "..WWWW..",
])
_muted = list(MIC)
for _i in range(8):
    _muted[_i * WIDTH + _i] = (255, 0, 0)
static("muted", "Muted microphone", _muted)
static("play", "Play", [
    "..G.....",
    "..GG....",
    "..GGG...",
    "..GGGG..",
    "..GGGG..",
    "..GGG...",
    "..GG....",
    "..G.....",
])
static("pause", "Pause", [
    "........",
    ".WW..WW.",
    ".WW..WW.",
    ".WW..WW.",
    ".WW..WW.",
    ".WW..WW.",
    ".WW..WW.",
    "........",
])
_up = static("up", "Arrow up", [
    "...GG...",
    "..GGGG..",
    ".GGGGGG.",
    "GGGGGGGG",
    "...GG...",
    "...GG...",
    "...GG...",
    "...GG...",
])
static("right", "Arrow right", rotate(_up))
static("down", "Arrow down", rotate(rotate(_up)))
static("left", "Arrow left", rotate(rotate(rotate(_up))))

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
WINK = sprite([
    "..YYYY..",
    ".YYYYYY.",
    "YYKYYKKY",
    "YYYYYYYY",
    "YKYYYYKY",
    "YYKKKKYY",
    ".YYYYYY.",
    "..YYYY..",
])
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

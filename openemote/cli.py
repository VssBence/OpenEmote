"""Command line interface. Run with no command to open the GUI."""
from __future__ import annotations

import argparse
import difflib
import sys
import time

from .device import LAYOUTS, DeviceError, EmoteDisplay
from .font import text_steps
from .frame import blank, parse_color, sprite
from .presets import CATEGORIES, PRESETS, playlist


def play(display: EmoteDisplay, factory, duration: float | None = None, loop: bool = True) -> None:
    """Show a sequence of (frame, ms) steps. Single-frame sequences are shown once."""
    first = factory()
    if isinstance(first, list) and len(first) == 1:
        display.show(first[0][0])
        return
    start = time.monotonic()
    while True:
        for frame, ms in factory():
            t0 = time.monotonic()
            display.show(frame)
            if duration and time.monotonic() - start >= duration:
                return
            time.sleep(max(0.0, ms / 1000 - (time.monotonic() - t0)))
        if not loop:
            return


def cmd_list(_args, _display=None):
    for category in CATEGORIES:
        print(f"\n{category.upper()}")
        for p in PRESETS.values():
            if p.category == category:
                print(f"  {p.name:<12} {p.description}")


def cmd_show(args, display):
    preset = PRESETS.get(args.preset.lower())
    if not preset:
        close = difflib.get_close_matches(args.preset.lower(), PRESETS, n=3)
        hint = f" Did you mean: {', '.join(close)}?" if close else ""
        sys.exit(f"Unknown preset {args.preset!r}.{hint} Run 'openemote list' to see all presets.")
    if args.still:
        display.show(preset.thumbnail())
        return
    if preset.animated:
        print(f"Playing {preset.name} (Ctrl+C to stop)")
    play(display, preset.factory, args.duration)


def cmd_cycle(args, display):
    unknown = [n for n in args.presets if n.lower() not in PRESETS]
    if unknown:
        sys.exit(f"Unknown preset(s): {', '.join(unknown)}. Run 'openemote list' to see all presets.")
    presets = [PRESETS[n.lower()] for n in args.presets]
    print(f"Cycling {len(presets)} presets, {args.seconds:g}s each (Ctrl+C to stop)")
    play(display, lambda: playlist(presets, args.seconds))


def cmd_text(args, display):
    color = None if args.color == "rainbow" else parse_color(args.color)
    steps = text_steps(args.text, color, args.speed)
    if len(steps) > 1:
        print("Scrolling (Ctrl+C to stop)" if not args.once else "Scrolling")
    play(display, lambda: steps, loop=not args.once)


def cmd_image(args, display):
    from .media import load_image
    steps = load_image(args.path)
    if len(steps) > 1:
        print(f"Playing {len(steps)} frames (Ctrl+C to stop)")
    play(display, lambda: steps, args.duration)


def cmd_color(args, display):
    display.show(blank(parse_color(args.color)))


def cmd_off(_args, display):
    display.show(blank())


def cmd_info(_args, display):
    print(f"Serial:   {display.serial()}")
    print(f"Firmware: {display.firmware()}")
    print(f"Layout:   {display.layout}")


ORIENTATION = sprite([
    "WRRRRRRR",
    "G.......",
    "G.......",
    "G...B...",
    "G..BBB..",
    "G.......",
    "G.......",
    "G.......",
])


def cmd_calibrate(_args, display):
    print("Lighting each pixel in order: it should travel left->right, top->bottom.")
    for i in range(64):
        f = blank()
        f[i] = (255, 255, 255)
        display.show(f)
        time.sleep(0.08)
    display.show(ORIENTATION)
    print("Now showing: white top-left corner, red top row, green left column, blue arrow pointing up.")
    print(f"If that looks scrambled, try another layout: --layout {{{','.join(LAYOUTS)}}}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="openemote", description="Drive the Razer Seiren Emote display without Razer software.")
    p.add_argument("--layout", choices=list(LAYOUTS), default="mirror", help="pixel layout (see 'calibrate')")
    p.add_argument("--brightness", type=int, default=100, metavar="0-100")
    sub = p.add_subparsers(dest="cmd", metavar="command")

    sub.add_parser("gui", help="open the graphical app (default)")
    sub.add_parser("list", help="list presets")
    s = sub.add_parser("show", help="show a preset")
    s.add_argument("preset")
    s.add_argument("--duration", type=float, help="stop animations after N seconds")
    s.add_argument("--still", action="store_true", help="show one frame and exit")
    cy = sub.add_parser("cycle", help="cycle through several presets")
    cy.add_argument("presets", nargs="+")
    cy.add_argument("--seconds", type=float, default=5, help="time per preset")
    t = sub.add_parser("text", help="show or scroll text")
    t.add_argument("text")
    t.add_argument("--color", default="rainbow", help="name, hex (ff8800) or 'rainbow'")
    t.add_argument("--speed", type=int, default=90, help="ms per scroll step")
    t.add_argument("--once", action="store_true", help="scroll once instead of looping")
    i = sub.add_parser("image", help="show an image or animated GIF (scaled to 8x8)")
    i.add_argument("path")
    i.add_argument("--duration", type=float)
    c = sub.add_parser("color", help="fill with a solid color")
    c.add_argument("color")
    sub.add_parser("off", help="turn all pixels off")
    sub.add_parser("info", help="print serial and firmware")
    sub.add_parser("calibrate", help="check the pixel layout")

    args = p.parse_args(argv)
    brightness = max(0, min(100, args.brightness)) / 100

    if args.cmd in (None, "gui"):
        from .gui import run
        run(layout=args.layout, brightness=brightness)
        return
    if args.cmd == "list":
        cmd_list(args)
        return

    try:
        with EmoteDisplay(layout=args.layout, brightness=brightness) as display:
            globals()[f"cmd_{args.cmd}"](args, display)
    except DeviceError as e:
        sys.exit(f"Error: {e}")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

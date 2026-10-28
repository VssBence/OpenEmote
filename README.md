# OpenEmote

I wanted to put a smiley on my Razer Seiren Emote. Turns out you need Razer's Stream Controller app
for that, and while it's open it takes over the rest of my Razer RGB stuff. So I figured out how the
display talks over USB and wrote this instead.

**[Download OpenEmote.exe](https://github.com/VssBence/OpenEmote/releases/latest)**, run it, done. No install.

![OpenEmote app](docs/screenshot.png)

## What it does

**ANIMATED EMOJIS**\
112 presets and almost all of them move. The smiley blinks, the poop stinks, the pumpkin flickers,
the beer fizzes.

**MUTE STATUS**\
Hit mute on the mic and the display switches to a muted mic. Unmute and it goes back to whatever was
on. It only watches the button, never your audio.

**PLAYLISTS**\
Right-click a few presets and the display cycles through them every few seconds.

**RUNS IN THE BACKGROUND**\
Close the window and it keeps going from the tray. It can start with Windows too.

**DRAW YOUR OWN**\
Paint straight onto the mic, live. Or drop in an image or GIF.

**SCROLLING TEXT**\
LIVE, BRB, GG, or whatever you type.

**COMMAND LINE**\
Everything works from the terminal too, so you can hook it up to a Stream Deck.

![Presets](docs/presets.png)

## Install from source

Python 3.9+.

```sh
git clone https://github.com/VssBence/OpenEmote.git
cd OpenEmote
pip install .
```

To build the exe yourself: `pip install pyinstaller`, then `python tools/build_exe.py`.

## Usage

`openemote` opens the app. Or from the command line:

```sh
openemote list
openemote show smiley
openemote show smiley --still        # one frame, stays after exit
openemote show fire --duration 10
openemote cycle smiley love beer fire --seconds 5
openemote text "LIVE NOW" --color red
openemote image cat.gif
openemote color ff00ff
openemote off
openemote --quit                     # close the running app cleanly
openemote --brightness 30 show heart
```

From Python:

```python
from openemote import EmoteDisplay, hsv

with EmoteDisplay() as display:
    display.show([hsv(i / 64) for i in range(64)])  # 64 (r, g, b) tuples, row by row
```

## Adding presets

Presets are in [`openemote/presets.py`](openemote/presets.py). Draw it in ASCII and pick an animation:

```python
add("ghost", "Floating ghost", "faces", bob(sprite([
    "..WWWW..",
    ".WWWWWW.",
    "WWKWWKWW",
    "WWKWWKWW",
    "WWWWWWWW",
    "WWWKKWWW",
    "WWWWWWWW",
    "WW.WW.WW",
])))
```

There are helpers for `blink`, `bob`, `shake`, `shine`, `pulse`, `flash`, `slide` and `draw_in`.

PRs welcome.

## How it works

Inside the mic there's a USB hub with two devices: the audio part and a separate display controller
(`1532:0F1B`). The display uses the same HID protocol as Razer keyboards. Notes are in
[docs/PROTOCOL.md](docs/PROTOCOL.md).

## Problems

- **Mute icon is the wrong way round:** the mic doesn't tell anyone if it's muted, so the app counts
  button presses. If you muted while the app was closed, press **Flip** next to the switch (or
  "Flip mute state" in the tray menu).
- **Clicked a preset while muted and it went back to mute:** that's on purpose. It shows for 3 seconds,
  then the mute icon comes back.
- **Picture looks scrambled:** run `openemote calibrate`, try `--layout split-snake`, and open an issue.
- **Display goes back to Razer's emote:** close Stream Controller.
- **Linux/macOS:** not tested.

Not affiliated with Razer. MIT license.

"""Tkinter app: pixel painter, preset gallery, text and image playback."""
from __future__ import annotations

import atexit
import json
import os
import pathlib
import threading
import time
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from . import autostart, instance
from .device import DeviceError, EmoteDisplay
from .font import text_steps
from .frame import BLACK, HEIGHT, WIDTH, Frame, blank, to_hex
from .mute import MuteWatcher
from .presets import PRESETS, playlist

MUTED_LABEL = "MUTED"
MUTED_PEEK_MS = 3000

CONFIG_DIR = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home())) / "OpenEmote"
CONFIG = CONFIG_DIR / "settings.json"
OLD_CONFIG = CONFIG_DIR / "playlist.json"
CELL = 40
THUMB = 4  # thumbnail pixel size
BG = "#16161c"
QUICK_COLORS = [(255, 255, 255), (255, 0, 0), (255, 100, 0), (255, 190, 0),
                (0, 220, 0), (0, 200, 255), (0, 70, 255), (170, 0, 255), (255, 70, 150)]


class DeviceWorker(threading.Thread):
    """Sends frames off the UI thread, always skipping to the newest one."""

    def __init__(self, display: EmoteDisplay):
        super().__init__(daemon=True)
        self.display = display
        self.error: Exception | None = None
        self._frame: Frame | None = None
        self._running = True
        self._cv = threading.Condition()

    def submit(self, frame: Frame) -> None:
        with self._cv:
            self._frame = list(frame)
            self._cv.notify()

    def shutdown(self, timeout: float = 1.0) -> None:
        """Stop sending and wait for the frame in flight to finish."""
        with self._cv:
            self._running = False
            self._cv.notify()
        self.join(timeout)

    def run(self):
        while True:
            with self._cv:
                while self._frame is None and self._running:
                    self._cv.wait()
                if not self._running:
                    return
                frame, self._frame = self._frame, None
            try:
                self.display.show(frame)
                self.error = None
            except Exception as e:  # keep the UI alive if the mic is unplugged
                self.error = e


_scratch = None


def draw_thumbnail(img: tk.PhotoImage, frame: Frame) -> None:
    # draw at 8x8, then let Tk scale it up (much cheaper than putting every big pixel)
    global _scratch
    if _scratch is None:
        _scratch = tk.PhotoImage(width=WIDTH, height=HEIGHT)
    _scratch.put(" ".join("{" + " ".join(to_hex(c) for c in frame[y * WIDTH:(y + 1) * WIDTH]) + "}"
                          for y in range(HEIGHT)))
    img.tk.call(img, "copy", _scratch, "-zoom", THUMB, THUMB)


def thumbnail_image(frame: Frame) -> tk.PhotoImage:
    img = tk.PhotoImage(width=WIDTH * THUMB, height=HEIGHT * THUMB)
    draw_thumbnail(img, frame)
    return img


class Switch(tk.Frame):
    """On/off toggle switch with a label; clicking either flips the variable."""

    BG = "#1e1e26"

    def __init__(self, parent, variable: tk.BooleanVar, text: str, on_change=None):
        super().__init__(parent, bg=self.BG, cursor="hand2")
        self.variable, self.text, self.on_change = variable, text, on_change
        self.canvas = tk.Canvas(self, width=40, height=22, bg=self.BG, highlightthickness=0)
        self.canvas.pack(side="left", padx=(0, 6))
        self.label = tk.Label(self, bg=self.BG, font=("Segoe UI", 9))
        self.label.pack(side="left")
        for w in (self, self.canvas, self.label):
            w.bind("<Button-1>", self._toggle)
        variable.trace_add("write", lambda *_: self.redraw())
        self.redraw()

    def _toggle(self, _event=None):
        self.variable.set(not self.variable.get())
        if self.on_change:
            self.on_change()

    def redraw(self):
        on = self.variable.get()
        c = self.canvas
        c.delete("all")
        fill = "#2fbf71" if on else "#4a4a56"
        c.create_oval(1, 1, 21, 21, fill=fill, outline=fill)
        c.create_oval(19, 1, 39, 21, fill=fill, outline=fill)
        c.create_rectangle(11, 1, 29, 21, fill=fill, outline=fill)
        x = 21 if on else 3
        c.create_oval(x, 3, x + 16, 19, fill="#ffffff", outline="#ffffff")
        self.label.configure(text=self.text, fg="#f0f0f4" if on else "#8a8a96")


class App:
    def __init__(self, root: tk.Tk, layout: str, brightness: float, start_hidden: bool = False):
        self.root = root
        self.pixels = blank()
        self.color = (255, 190, 0)
        self._job = None
        self._factory = None
        self._steps = None
        self._thumbs = []
        self._thumb_anims = []
        self._tray = None
        self._tray_hint_shown = False
        self._paused = None
        self._label = ""
        self._cleared = False
        self._mute_watcher = None
        self._before_mute = None
        self._mute_return = None
        self.worker = None
        self.device_status = ""
        try:
            self.display = EmoteDisplay(layout=layout, brightness=brightness)
            self.device_status = f"Connected · firmware {self.display.firmware()} · layout {layout}"
            self.worker = DeviceWorker(self.display)
            self.worker.start()
            atexit.register(self._clear_display)  # also covers exits that skip _quit
        except (DeviceError, OSError) as e:
            self.display = None
            self.device_status = f"Preview only · {e}"
        self._build(int(brightness * 100))
        self._draw_all()
        self._poll_worker()
        self._animate_thumbs()
        if self.show_mute.get():
            self._start_mute_watch()
        else:
            self.flip_button.state(["disabled"])
        if start_hidden:  # launched at login: straight to the tray, play the playlist
            self._tray_hint_shown = True
            root.after(200, self._start_hidden)

    def _start_hidden(self):
        self._hide_to_tray()
        if self._playlist:
            self._play_playlist()

    # --- layout -------------------------------------------------------------

    def _build(self, brightness: int):
        root = self.root
        root.title("OpenEmote · Seiren Emote display")
        root.configure(bg=BG)
        self._icon = thumbnail_image(PRESETS["smiley"].thumbnail())
        root.iconphoto(True, self._icon)
        style = ttk.Style(root)
        style.theme_use("clam")
        for name in ("TFrame", "TLabelframe"):
            style.configure(name, background=BG)
        style.configure("TLabelframe.Label", background=BG, foreground="#c8c8d0")
        style.configure("TLabel", background=BG, foreground="#c8c8d0")
        style.configure("TCheckbutton", background=BG, foreground="#c8c8d0")
        style.configure("Status.TLabel", foreground="#8a8a96")

        saved = self._load_settings()
        self.tray_on_close = tk.BooleanVar(value=saved.get("tray", True))

        # top bar: app name + background toggle
        bar = tk.Frame(root, bg="#1e1e26")
        bar.pack(fill="x")
        tk.Label(bar, text="OpenEmote", bg="#1e1e26", fg="#f0f0f4",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=12, pady=8)
        ttk.Button(bar, text="Hide now", command=self._hide_to_tray).pack(side="right", padx=(6, 12))
        self.autostart = tk.BooleanVar(value=autostart.enabled())
        self.show_mute = tk.BooleanVar(value=saved.get("mute", False))
        self.flip_button = ttk.Button(bar, text="Flip", width=5, command=self._flip_mute)
        self.flip_button.pack(side="right", padx=(0, 8))
        Switch(bar, self.show_mute, "Show mute status", self._toggle_mute_watch).pack(side="right", padx=(8, 4))
        Switch(bar, self.tray_on_close, "Run in background when closed", self._save_playlist).pack(side="right", padx=8)
        Switch(bar, self.autostart, "Start with Windows", self._toggle_autostart).pack(side="right", padx=8)

        main = ttk.Frame(root, padding=12)
        main.pack(fill="both", expand=True)

        # left: painter
        left = ttk.Frame(main)
        left.grid(row=0, column=0, sticky="n", padx=(0, 12))
        self.canvas = tk.Canvas(left, width=WIDTH * CELL, height=HEIGHT * CELL, bg="#000", highlightthickness=0)
        self.canvas.pack()
        self.cells = [self.canvas.create_rectangle(x * CELL + 2, y * CELL + 2, (x + 1) * CELL - 2, (y + 1) * CELL - 2,
                                                   fill="#000", outline="#222")
                      for y in range(HEIGHT) for x in range(WIDTH)]
        self.canvas.bind("<Button-1>", lambda e: self._paint(e, self.color))
        self.canvas.bind("<B1-Motion>", lambda e: self._paint(e, self.color))
        self.canvas.bind("<Button-3>", lambda e: self._paint(e, BLACK))
        self.canvas.bind("<B3-Motion>", lambda e: self._paint(e, BLACK))
        ttk.Label(left, text="Left click: paint · right click: erase", style="Status.TLabel").pack(pady=(4, 6))

        swatches = ttk.Frame(left)
        swatches.pack(fill="x")
        self.swatch = tk.Button(swatches, width=3, bg=to_hex(self.color), relief="flat", command=self._pick_color)
        self.swatch.pack(side="left", padx=(0, 6))
        for c in QUICK_COLORS:
            tk.Button(swatches, width=2, bg=to_hex(c), activebackground=to_hex(c), relief="flat",
                      command=lambda c=c: self._set_color(c)).pack(side="left", padx=1)

        tools = ttk.Frame(left)
        tools.pack(fill="x", pady=6)
        ttk.Button(tools, text="Clear", command=lambda: self._show_static(blank())).pack(side="left")
        ttk.Button(tools, text="Fill", command=lambda: self._show_static(blank(self.color))).pack(side="left", padx=4)
        ttk.Button(tools, text="Send", command=self._send).pack(side="left")
        self.live = tk.BooleanVar(value=True)
        ttk.Checkbutton(tools, text="Live", variable=self.live).pack(side="left", padx=6)

        box = ttk.Labelframe(left, text="Text", padding=6)
        box.pack(fill="x", pady=(6, 0))
        self.text = tk.StringVar(value="HELLO")
        ttk.Entry(box, textvariable=self.text, width=14).pack(side="left")
        self.rainbow = tk.BooleanVar(value=True)
        ttk.Checkbutton(box, text="Rainbow", variable=self.rainbow).pack(side="left", padx=4)
        ttk.Button(box, text="Go", width=4, command=self._play_text).pack(side="left")

        box = ttk.Labelframe(left, text="Display", padding=6)
        box.pack(fill="x", pady=(6, 0))
        ttk.Button(box, text="Open image / GIF…", command=self._open_image).pack(side="left")
        ttk.Button(box, text="Stop", command=self.stop).pack(side="left", padx=4)
        ttk.Label(box, text="Brightness").pack(side="left", padx=(8, 2))
        self.brightness = tk.Scale(box, from_=5, to=100, orient="horizontal", length=90, showvalue=False,
                                   bg=BG, highlightthickness=0, troughcolor="#333", command=self._set_brightness)
        self.brightness.set(brightness)
        self.brightness.pack(side="left")

        box = ttk.Labelframe(left, text="Playlist · right-click presets to add", padding=6)
        box.pack(fill="x", pady=(6, 0))
        self.playlist_box = tk.Listbox(box, height=5, bg="#24242c", fg="#c8c8d0", selectbackground="#3a3a46",
                                       highlightthickness=0, relief="flat", activestyle="none")
        self.playlist_box.pack(side="left", fill="both", expand=True)
        ctrl = ttk.Frame(box)
        ctrl.pack(side="left", padx=(6, 0))
        ttk.Button(ctrl, text="Play", width=8, command=self._play_playlist).pack()
        ttk.Button(ctrl, text="Remove", width=8, command=self._playlist_remove).pack(pady=2)
        ttk.Button(ctrl, text="Clear", width=8, command=lambda: self._playlist_set([])).pack()
        secs = ttk.Frame(ctrl)
        secs.pack(pady=(4, 0))
        self.cycle_secs = tk.IntVar(value=saved.get("seconds", 5))
        tk.Spinbox(secs, from_=1, to=300, width=4, textvariable=self.cycle_secs,
                   command=self._save_playlist).pack(side="left")
        ttk.Label(secs, text="sec").pack(side="left", padx=2)
        self._playlist_set([n for n in saved.get("items", []) if n in PRESETS], save=False)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        # right: one long scrollable list of every preset
        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="ns")
        main.rowconfigure(0, weight=1)
        self.gallery = tk.Canvas(right, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(right, orient="vertical", command=self.gallery.yview)
        self.gallery.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.gallery.pack(side="left", fill="both", expand=True)
        inner = ttk.Frame(self.gallery)
        self.gallery.create_window((0, 0), window=inner, anchor="nw")
        row = 0
        for category, title in (("faces", "Faces"), ("icons", "Icons"), ("animated", "Animations"), ("text", "Text")):
            ttk.Label(inner, text=title, font=("Segoe UI", 10, "bold")).grid(
                row=row, column=0, columnspan=8, sticky="w", pady=(8 if row else 0, 2))
            row += 1
            items = [p for p in PRESETS.values() if p.category == category]
            for n, preset in enumerate(items):
                img = thumbnail_image(preset.thumbnail())
                self._thumbs.append(img)
                b = tk.Button(inner, image=img, text=preset.name, compound="top", width=62, bg="#24242c",
                              fg="#c8c8d0", activebackground="#34343e", relief="flat", font=("Segoe UI", 8),
                              command=lambda p=preset: self.play_preset(p))
                b.grid(row=row + n // 8, column=n % 8, padx=2, pady=2)
                b.bind("<Button-3>", lambda e, p=preset: self._playlist_add(p))
                if preset.animated:
                    self._thumb_anims.append({"img": img, "button": b, "preset": preset, "steps": None, "due": 0.0})
            row += -(-len(items) // 8)
        inner.update_idletasks()
        self.gallery.configure(width=inner.winfo_reqwidth(), height=left.winfo_reqheight(),
                               scrollregion=(0, 0, inner.winfo_reqwidth(), inner.winfo_reqheight()))
        root.bind_all("<MouseWheel>", lambda e: self.gallery.yview_scroll(int(-e.delta / 120), "units"))

        self.status = ttk.Label(root, text="", style="Status.TLabel", padding=(12, 0, 12, 8))
        self.status.pack(fill="x")
        self._set_status("Ready")

    # --- drawing --------------------------------------------------------------

    def _draw_all(self):
        for i, c in enumerate(self.pixels):
            self.canvas.itemconfigure(self.cells[i], fill=to_hex(c))

    def show(self, frame: Frame):
        self.pixels = list(frame)
        self._draw_all()
        self._send()

    def _send(self):
        if self.worker:
            self.worker.submit(self.pixels)

    def _paint(self, event, color):
        x, y = event.x // CELL, event.y // CELL
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
            return
        self.stop()
        i = y * WIDTH + x
        if self.pixels[i] == color:
            return
        self.pixels[i] = color
        self.canvas.itemconfigure(self.cells[i], fill=to_hex(color))
        if self.live.get():
            self._send()

    def _set_color(self, c):
        self.color = c
        self.swatch.configure(bg=to_hex(c), activebackground=to_hex(c))

    def _pick_color(self):
        rgb, _ = colorchooser.askcolor(color=to_hex(self.color), title="Pick a color")
        if rgb:
            self._set_color(tuple(int(v) for v in rgb))

    def _set_brightness(self, value):
        level = int(value) / 100
        if self.display and level != self.display.brightness:
            self.display.brightness = level
            self._send()

    # --- playback -------------------------------------------------------------

    def _show_static(self, frame):
        self.stop()
        self.show(frame)

    def play(self, factory, label):
        self.stop()
        self._paused = None
        self._label = label
        if self._mute_return:
            self.root.after_cancel(self._mute_return)
            self._mute_return = None
        if self._is_muted() and label != MUTED_LABEL:  # muted: just a quick peek, then back to mute
            self._mute_return = self.root.after(MUTED_PEEK_MS, self._back_to_mute, label)
        first = factory()
        if isinstance(first, list) and len(first) == 1:
            self.show(first[0][0])
            self._set_status(label)
            self._refresh_tray()
            return
        self._factory, self._steps, self._label = factory, iter(first), label
        self._set_status(f"Playing {label}")
        self._tick()
        self._refresh_tray()

    def toggle_pause(self):
        if self._paused:
            factory, label = self._paused
            self.play(factory, label)
        elif self._job:
            self._paused = (self._factory, self._label)
            self.stop()
            self._set_status("Paused")
            self._refresh_tray()

    def _tick(self):
        try:
            frame, ms = next(self._steps)
        except StopIteration:
            self._steps = iter(self._factory())
            frame, ms = next(self._steps)
        self.show(frame)
        self._job = self.root.after(max(int(ms), 20), self._tick)

    def stop(self):
        if self._job:
            self.root.after_cancel(self._job)
            self._job = None
            self._set_status("Stopped")

    def play_preset(self, preset):
        self.play(preset.factory, preset.name)

    def _play_text(self):
        text = self.text.get().strip()
        if text:
            steps = text_steps(text, None if self.rainbow.get() else self.color)
            self.play(lambda: steps, f"text '{text}'")

    def _open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.gif *.jpg *.jpeg *.bmp *.webp"), ("All", "*.*")])
        if not path:
            return
        try:
            from .media import load_image
            steps = load_image(path)
        except Exception as e:
            messagebox.showerror("OpenEmote", str(e))
            return
        self.play(lambda: steps, path.replace("\\", "/").rsplit("/", 1)[-1])

    # --- playlist -------------------------------------------------------------

    def _load_settings(self) -> dict:
        for path in (CONFIG, OLD_CONFIG):
            try:
                return json.loads(path.read_text())
            except (OSError, ValueError):
                pass
        return {}

    def _save_playlist(self):
        try:
            CONFIG.parent.mkdir(parents=True, exist_ok=True)
            CONFIG.write_text(json.dumps({"items": self._playlist, "seconds": self._seconds(),
                                          "tray": self.tray_on_close.get(), "mute": self.show_mute.get()}))
        except OSError:
            pass

    def _seconds(self) -> int:
        try:
            return max(1, int(self.cycle_secs.get()))
        except (tk.TclError, ValueError):
            return 5

    def _playlist_set(self, names, save=True):
        self._playlist = list(names)
        self.playlist_box.delete(0, "end")
        for n in self._playlist:
            self.playlist_box.insert("end", n)
        if save:
            self._save_playlist()

    def _playlist_add(self, preset):
        self._playlist_set(self._playlist + [preset.name])
        self._set_status(f"Added {preset.name} to playlist")

    def _playlist_remove(self):
        picked = set(self.playlist_box.curselection())
        self._playlist_set([n for i, n in enumerate(self._playlist) if i not in picked])

    def _play_playlist(self):
        if not self._playlist:
            self._set_status("Playlist is empty · right-click presets to add them")
            return
        self._save_playlist()
        presets, secs = [PRESETS[n] for n in self._playlist], self._seconds()
        self.play(lambda: playlist(presets, secs), f"playlist ({len(presets)} items, {secs}s each)")

    # --- tray -----------------------------------------------------------------

    # --- mute display -----------------------------------------------------------

    def _toggle_mute_watch(self):
        self._save_playlist()
        self.flip_button.state(["!disabled"] if self.show_mute.get() else ["disabled"])
        if self.show_mute.get():
            self._start_mute_watch()
        else:
            if self._mute_watcher:
                self._mute_watcher.stop()
                self._mute_watcher = None
            self._on_mute(False)

    def _start_mute_watch(self):
        if self._mute_watcher or self.display is None:
            return
        self._mute_watcher = MuteWatcher(lambda muted: self.root.after(0, self._on_mute, muted))
        self._mute_watcher.start()

    def _is_muted(self) -> bool:
        return bool(self._mute_watcher and self._mute_watcher.muted)

    def _back_to_mute(self, label):
        self._mute_return = None
        if self._is_muted() and self._label == label:
            self.play(PRESETS["muted"].factory, MUTED_LABEL)

    def _flip_mute(self):
        if self._mute_watcher:
            self._mute_watcher.flip()

    def _on_mute(self, muted: bool):
        if muted:
            if self._label != MUTED_LABEL:
                self._before_mute = (self._factory, self._label) if self._job else list(self.pixels)
            self.play(PRESETS["muted"].factory, MUTED_LABEL)
        elif (self._label == MUTED_LABEL and self._job) or self._mute_return:  # mute or a peek: go back
            before, self._before_mute = self._before_mute, None
            if isinstance(before, tuple):
                self.play(*before)
            else:
                self.stop()
                self._label = ""
                self.show(before or blank())

    def _toggle_autostart(self):
        try:
            autostart.set_enabled(self.autostart.get())
        except OSError as e:
            messagebox.showerror("OpenEmote", f"Could not change autostart: {e}")
        self.autostart.set(autostart.enabled())

    def _hide_to_tray(self):
        if self._start_tray():
            self.root.withdraw()

    def _on_close(self):
        if self.tray_on_close.get():
            self._hide_to_tray()
        if self.root.state() != "withdrawn":
            self._quit()

    def _start_tray(self) -> bool:
        try:
            import pystray
            from PIL import Image
        except ImportError:
            return False
        icon = Image.new("RGBA", (WIDTH, HEIGHT))
        icon.putdata([c + ((255,) if any(c) else (0,)) for c in PRESETS["smiley"].thumbnail()])
        menu = pystray.Menu(
            pystray.MenuItem("Open app", lambda: self.root.after(0, self._show_window), default=True),
            pystray.MenuItem(lambda item: "Resume" if self._paused else "Pause",
                             lambda: self.root.after(0, self.toggle_pause),
                             enabled=lambda item: bool(self._job or self._paused)),
            pystray.MenuItem("Flip mute state", lambda: self.root.after(0, self._flip_mute),
                             visible=lambda item: bool(self._mute_watcher)),
            pystray.MenuItem("Close", lambda: self.root.after(0, self._quit)),
        )
        self._tray = pystray.Icon("OpenEmote", icon.resize((64, 64), Image.Resampling.NEAREST), "OpenEmote", menu)

        def setup(tray):
            tray.visible = True
            if not self._tray_hint_shown:
                self._tray_hint_shown = True
                tray.notify("Still running here. Right-click the smiley for options.", "OpenEmote")

        self._tray.run_detached(setup)
        return True

    def _refresh_tray(self):
        if self._tray:
            self._tray.update_menu()

    def _show_window(self):
        if self._tray:
            self._tray.stop()
            self._tray = None
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _quit(self):
        if self._tray:
            self._tray.stop()
            self._tray = None
        self.stop()
        if self._mute_watcher:
            self._mute_watcher.stop()
        self._clear_display()
        self.root.destroy()

    def _clear_display(self):
        """Turn the LEDs off so the mic doesn't stay frozen on the last frame."""
        if self.display is None or self._cleared:
            return
        self._cleared = True
        if self.worker:
            self.worker.shutdown()
        try:
            self.display.show(blank())
            self.display.close()
        except Exception:
            pass

    def _animate_thumbs(self):
        """Play every visible gallery thumbnail as a little preview."""
        if self.root.state() == "withdrawn":
            self.root.after(500, self._animate_thumbs)
            return
        now = time.monotonic()
        top = self.gallery.canvasy(0)
        bottom = top + self.gallery.winfo_height()
        for t in self._thumb_anims:
            button = t["button"]
            if now < t["due"] or button.winfo_y() + button.winfo_height() < top or button.winfo_y() > bottom:
                continue
            if t["steps"] is None:
                t["steps"] = iter(t["preset"].factory())
            try:
                frame, ms = next(t["steps"])
            except StopIteration:
                t["steps"] = iter(t["preset"].factory())
                frame, ms = next(t["steps"])
            draw_thumbnail(t["img"], frame)
            t["due"] = now + max(ms, 100) / 1000
        self.root.after(50, self._animate_thumbs)

    # --- status ---------------------------------------------------------------

    def _set_status(self, text):
        self.status.configure(text=f"{text}   ·   {self.device_status}")

    def _poll_worker(self):
        if self.worker and self.worker.error:
            self.status.configure(text=f"Device error: {self.worker.error}")
        self.root.after(1000, self._poll_worker)


def run(layout: str = "mirror", brightness: float = 1.0, start_hidden: bool = False):
    try:  # crisp rendering on high-DPI Windows screens
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    if instance.already_running():  # only one copy, otherwise two apps fight over the display
        tk.Tk().withdraw()
        messagebox.showinfo("OpenEmote", "OpenEmote is already running. Look for it in the system tray.")
        return
    root = tk.Tk()
    app = App(root, layout, brightness, start_hidden)
    quit_event = instance.quit_event()

    def watch_quit():  # `openemote --quit` from elsewhere: close cleanly
        if instance.quit_requested(quit_event):
            app._quit()
        else:
            root.after(300, watch_quit)

    watch_quit()
    root.resizable(False, False)
    root.mainloop()

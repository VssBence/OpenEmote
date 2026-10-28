"""OpenEmote: drive the Razer Seiren Emote's LED display without Razer software."""
from .device import LAYOUTS, DeviceError, EmoteDisplay
from .frame import Frame, blank, hsv, parse_color, sprite
from .presets import PRESETS

__version__ = "0.1.0"
__all__ = ["EmoteDisplay", "DeviceError", "LAYOUTS", "PRESETS", "Frame", "blank", "hsv", "sprite", "parse_color"]

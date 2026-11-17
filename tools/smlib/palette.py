"""Palette helpers: SNES BGR555 <-> RGB and the Frigate recolor of the Wrecked Ship tileset."""
from __future__ import annotations

import colorsys

# Palette rows owned by the Wrecked Ship tileset (rows 0-3 are shared: doors, items, CRE).
FRIGATE_ROWS = (4, 5, 7)


def bgr555_to_rgb(c: int) -> tuple[int, int, int]:
    r, g, b = c & 31, (c >> 5) & 31, (c >> 10) & 31
    return (r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2)


def rgb_to_bgr555(r: int, g: int, b: int) -> int:
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


def frigate_color(c: int) -> int:
    """Turn olive/yellow-green metal into the steel blue-gray of a pirate frigate."""
    r, g, b = (v / 255 for v in bgr555_to_rgb(c))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if 0.08 <= h <= 0.40 and s > 0.08:
        h, s = 0.60, s * 0.45
        v = min(1.0, v * 1.05)
    elif 0.60 <= h <= 0.72 and s > 0.2:
        # the purple-blue lights become pirate red/orange
        h, s = 0.02, min(1.0, s * 1.1)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return rgb_to_bgr555(round(r * 255), round(g * 255), round(b * 255))


def recolor(palette_bytes: bytes, rows=FRIGATE_ROWS) -> bytes:
    out = bytearray(palette_bytes)
    for row in rows:
        for i in range(1, 15):
            o = 2 * (row * 16 + i)
            c = out[o] | (out[o + 1] << 8)
            n = frigate_color(c)
            out[o], out[o + 1] = n & 0xFF, n >> 8
    return bytes(out)

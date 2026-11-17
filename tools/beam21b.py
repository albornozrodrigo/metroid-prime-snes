"""specs/21b: the Prime's beam colours on the SNES beam palettes (test build only, --teste-21b).

Measured from the Prime's particle constants (scratchpad part_colours.json): Power orange, Wave purple, Ice light blue.
Only colour indices 2-7 of each beam palette change (index 0 transparent, index 1 white stay as they are). The
original brightness of each colour is kept as a ramp: the brightest entry gets a light tint, the darkest a deep shade.
Palette addresses come from the SM's pointer table (sm_90.c, UpdateBeamTilesAndPalette, read from base/sm_fix.sfc):
Power $90:C3E1, Charge $90:C421 (not changed here), Wave $90:C461 (combination 4), Ice $90:C401.
"""
from __future__ import annotations

from smlib.palette import bgr555_to_rgb, rgb_to_bgr555

PRIME_BEAM_RGB = {
    0xC3E1: (255, 178, 51),    # Power: orange (Prime 1.0, 0.62-0.85, 0-0.54 measured; mid value)
    0xC461: (170, 0, 128),     # Wave: purple (Prime 0.67, 0.0, 0.50)
    0xC401: (64, 153, 255),    # Ice: light blue (Prime 0.16-0.33, 0.30-0.67, 1.0; mid value)
}
RAMP = range(2, 8)


def recolor_beam_palette(pal: bytes, target: tuple[int, int, int]) -> bytes:
    out = bytearray(pal)
    cols = {i: out[2 * i] | (out[2 * i + 1] << 8) for i in RAMP}
    lum = {i: sum(bgr555_to_rgb(c)) / 3 for i, c in cols.items() if c}
    top = max(lum.values())
    for i, l in lum.items():
        t = l / top                                  # 1.0 = brightest original entry
        k = 0.7 + 0.3 * t                           # darker originals get a slightly darker shade (keeps the Prime hue)
        rgb = [min(255, int(v * k)) for v in target]
        if t > 0.85:                                 # brightest entries lean towards white
            w = (t - 0.85) / 0.15 * 0.5
            rgb = [round(v + (255 - v) * w) for v in rgb]
        n = rgb_to_bgr555(*rgb)
        out[2 * i], out[2 * i + 1] = n & 0xFF, n >> 8
    return bytes(out)


def apply(rom) -> None:
    """Writes the Prime beam colours into the test ROM's beam palettes (rom: smlib.rom.Rom)."""
    for addr, target in PRIME_BEAM_RGB.items():
        pal_addr = 0x900000 | addr
        rom.write(pal_addr, recolor_beam_palette(rom.read(pal_addr, 32), target))

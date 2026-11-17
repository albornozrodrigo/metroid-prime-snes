"""Boss looks for the frigate.

Parasite Queen = Phantoon with the Parasite Queen's own shape and colours. Her body (BG2: tiles,
tilemap blocks, the 8 health-stage palettes, hitboxes) is tools/frigate/queen_art.py; here only
Phantoon's flames (sprite palette) are recoloured.

Colour source: the Parasite_queen model in Prime (CMDL 9A43BD70), textures exported with
tools/dump_prime_textures.py to research/prime_textures/parasite_queen/. k-means over their
pixels (white filler dropped) gives two families of similar brightness:
  - carapace, dark grey-brown: (31,21,18) (54,46,38) (86,71,61) (151,107,95), belly (181,165,148);
  - flesh, crimson: (83,29,31) (137,53,58).
Phantoon's blue flames/eye (sprite palette) become fire, like the Queen's fireballs: each colour
keeps its brightness and takes the hue of the FIRE ramp.
"""
from __future__ import annotations

from smlib.rom import Rom

PHANTOON_SPRITE_PALETTE = 0xA7CA01  # species palette of Phantoon and its 3 parts ($A0:E4BF..E57F)
PHANTOON_SPECIES = (0xA0E4BF, 0xA0E4FF, 0xA0E53F, 0xA0E57F)

Ramp = list[tuple[int, int, int]]
FIRE: Ramp = [(0, 0, 0), (96, 16, 8), (200, 64, 16), (240, 136, 40), (252, 208, 112), (255, 255, 236)]


def luma(c: tuple[int, int, int]) -> float:
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def bgr555_to_rgb(v: int) -> tuple[int, int, int]:
    return (v & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, ((v >> 10) & 31) * 255 // 31


def rgb_to_bgr555(c: tuple[float, float, float]) -> int:
    r, g, b = (max(0, min(31, round(x * 31 / 255))) for x in c)
    return r | (g << 5) | (b << 10)


def along(ramp: Ramp, y: float) -> tuple[float, float, float]:
    """Colour of the ramp at brightness y (stops ordered by brightness)."""
    ys = [luma(c) for c in ramp]
    if y <= ys[0]:
        return ramp[0]
    for (a, ya), (b, yb) in zip(zip(ramp, ys), zip(ramp[1:], ys[1:])):
        if y <= yb:
            t = (y - ya) / (yb - ya)
            return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
    return ramp[-1]


def recolour(v: int, ramp_for) -> int:
    if v in (0x0000, 0x7FFF):   # transparent/black and the white hit flash stay
        return v
    c = bgr555_to_rgb(v)
    return rgb_to_bgr555(along(ramp_for(c), luma(c)))


def parasite_queen(rom: Rom) -> None:
    for sp in PHANTOON_SPECIES:
        assert (rom.u8(sp + 0x0C) << 16) | rom.u16(sp + 2) == PHANTOON_SPRITE_PALETTE, "paleta do Phantoon mudou"
    for k in range(16):
        a = PHANTOON_SPRITE_PALETTE + 2 * k
        rom.w16(a, recolour(rom.u16(a), lambda c: FIRE))

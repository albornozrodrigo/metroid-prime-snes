"""Impact Crater look (specs/20d-estilo-impact.md; epic 20): the Phazon Mines' rock look (smlib/mines.py, specs/19d) with the rock
in the crater's red-brown. Data only, and the test build (tools/build.py --teste-20d) writes it; the game's ROM writes it once a
crater room exists (20e on).

Read from Prime (research/prime_area_colours.json, tools/dump_prime_area_colours.py: the mean colour of every texture each room's
geometry draws with): the crater's textures are warm (121 of 298 red/orange, mean of those 57362E: hue 12, HLS saturation 0.31), the
Mines' grey (64 of 870 warm); the blue ones (the phazon) have the same hue in both worlds (crater 223F57, Mines 28384C). So:
  - the same pieces, graphics and metatile table as the Mines' rock ($08: green Brinstar's $06 graphics and a copy of its table with
    the purple wave doors on line 7): the crater is rock and phazon too, no pirate base (Prime's crater has no pirate machinery);
  - the phazon (the moss turned fungus, line 4 colours 4, 8, 9, 12, 14) = the Mines' exactly (mines.ROCK_COLOURS: mines.PHAZON),
    because Prime's phazon is the same blue in both worlds;
  - the rock (line 4 colours 3, 5, 6, 7, 10, 11, 13) = the Mines' grey rock with each colour's lightness kept and Prime's crater
    hue and saturation (ROCK_HUE, ROCK_SAT: the warm mean above);
  - the background = the Mines' rock's ($8F:BAF4, Brinstar's dark blue rock on line 2, vanilla colours: line 2 is the CRE's too).
A palette is per tileset entry, so the crater needs one of its own: entry TILESET = $03 (vanilla: Lower Crateria's twin of $02, used
by 2 orphan rooms, no attract demo room, no room of ours; validate.check_impact_style), pointed at $08's metatile table and graphics
(shared, not copied) and at its own palette. Music, the Lair's darker rooms (Prime: 2F262E against 4B3532) and the phazon that
hurts are the rooms' children (20e-20h).
"""
from __future__ import annotations

import colorsys
from dataclasses import replace

from smlib import mines
from smlib.ice import _bgr555
from smlib.rom import Rom
from tallon import beamdoors

TILESET = 0x03                      # entry repointed (Lower Crateria's twin, orphan rooms only)
SOURCE = mines.ROCK_TILESET         # the Mines' rock: its table and graphics are shared
GRAPHICS_SOURCE = mines.ROCK_SOURCE  # $06, green Brinstar's, the graphics both point at
PAINT_LINE = mines.PAINT_LINES[mines.ROCK_TILESET]
OWN_LINES = mines.OWN_LINES[mines.ROCK_TILESET]
STYLE = replace(mines.MINE_ROCK, name="cratera", tileset=TILESET)
BACKGROUND = mines.BACKGROUND[mines.ROCK_TILESET]

# Prime's crater rock: hue (degrees) and HLS saturation of the mean of its warm textures (research/prime_area_colours.json
# "Impact Crater" warm_hue, warm_sat; checked by the validator)
ROCK_HUE, ROCK_SAT = 12, 0.31
PHAZON_KEYS = ((4, 4), (4, 8), (4, 9), (4, 12), (4, 14))       # the Mines' fungus (the phazon), kept
ROCK_KEYS = ((4, 3), (4, 5), (4, 6), (4, 7), (4, 10), (4, 11), (4, 13))   # the Mines' grey rock, tinted


def tint(rgb_hex: str, hue: float = ROCK_HUE, sat: float = ROCK_SAT) -> str:
    """`rgb_hex` with its HLS lightness kept and `hue` (degrees) and `sat`."""
    _, light, _ = colorsys.rgb_to_hls(*(int(rgb_hex[i:i + 2], 16) / 255 for i in (0, 2, 4)))
    return "%02X%02X%02X" % tuple(round(c * 255) for c in colorsys.hls_to_rgb(hue / 360, light, sat))


# (palette line, colour) -> RGB hex: the Mines' rock look with the rock tinted (decision to confirm with the user: change, rebuild)
#   rock: 40444A -> 5A3830, 5A5E66 -> 7E4E42, 34383F -> 4B2F28, 1C1E24 -> 2A1A16, 4A4E55 -> 684137, 0E0F12 -> 150D0B, 202226 -> 2E1C18
COLOURS = {**{k: mines.ROCK_COLOURS[k] for k in PHAZON_KEYS},
           (4, 3): "5A3830", (4, 5): "7E4E42", (4, 6): "4B2F28", (4, 7): "2A1A16", (4, 10): "684137", (4, 11): "150D0B",
           (4, 13): "2E1C18"}


def palette(rom: Rom) -> bytes:
    """The crater's palette from `rom`'s vanilla bytes: green Brinstar's ($06) with the look's colours and the purple wave door on
    PAINT_LINE (as build.mines_palette makes the Mines' rock's, with the rock tinted)."""
    out = bytearray(mines.vanilla_palette(rom, GRAPHICS_SOURCE))
    for (line, i), c in COLOURS.items():
        out[2 * (line * 16 + i):2 * (line * 16 + i) + 2] = _bgr555(c).to_bytes(2, "little")
    return beamdoors.paint_palette(bytes(out), PAINT_LINE)


def hue_sat(rgb_hex: str) -> tuple[float, float]:
    """(hue in degrees, HLS saturation) of `rgb_hex`."""
    h, _, s = colorsys.rgb_to_hls(*(int(rgb_hex[i:i + 2], 16) / 255 for i in (0, 2, 4)))
    return h * 360, s

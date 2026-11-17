"""Crateria looks for the Tallon Overworld (SM area 0): wall styles, rain and music
(specs/07c-estilo-crateria.md).

Every value here was read from the vanilla ROM (base/sm_fix.sfc) with tools/smlib/room_reader.py:
  - SURFACE (tileset 0): green rock with a blue stone rim and grass on top, the most common piece
    for each air neighbourhood of the solid blocks of the outdoor/cave rooms $91F8 (Landing Site),
    $957D, $92FD, $948C, $9552, $9461, $95FF; grass tufts are air blocks of the same rooms.
  - CAVE (tileset 2): stone bricks of $99BD, $9A44, $9879, $98E2 (bricks laid in a checker of
    $2B6/$2B8, floor and ceiling rows of $2AD/$2AF); plant stalks are air blocks of $99BD/$9969.
  - RAIN_FX: FX entry of the Landing Site default state ($8F:91F8): type $0A = rain.
  - LANDING_SITE_MUSIC: song set / track of that same state.
check() proves, against the ROM, that every piece exists in its tileset and that vanilla uses it
with the collision the style gives it (solid pieces as solid, decoration as air).
"""
from __future__ import annotations

import collections

from .compression import decompress
from .gfx import TILESET_TABLE
from .rom import Rom, snes_to_pc
from .room_reader import read_level_data, read_room
from .style import H, V, EdgeStyle

SURFACE_TILESET = 0      # Upper Crateria (21 vanilla states)
CAVE_TILESET = 2         # Lower Crateria (23 vanilla states)
RAIN_FX = 0x80C0         # $83:80C0: 00 00 FF FF FF FF 00 00 00 0A 02 0E 00 01 00 22
LANDING_SITE_MUSIC = (0x06, 0x05)
# Sky behind the surface rooms (specs/07g): the vanilla Landing Site's BG2 is one of the cloud
# tilemaps of $8A:B180-$8A:D980 ($800 bytes = 32x32 tiles of tileset 0), picked by entry door in
# its library background $8F:B76A, with BG2 scroll $0181 (x at half speed, y fixed). Ours loads
# the cloud band $8A:C180 (its first choice) into both halves of the 64x32 BG2 tilemap, so nothing
# left in VRAM by the previous room shows when the sky scrolls sideways.
SKY_TILEMAP = 0x8AC180
SKY_LAYER2 = 0x0181
SKY_BG = (b"\x02\x00" + SKY_TILEMAP.to_bytes(3, "little") + b"\x00\x48\x00\x08"
          + b"\x02\x00" + SKY_TILEMAP.to_bytes(3, "little") + b"\x00\x4C\x00\x08" + b"\x00\x00")

SURFACE = EdgeStyle(
    name="superficie", tileset=SURFACE_TILESET,
    fill=(0x111, 0x111 | H, 0x111 | V, 0x111 | H | V),
    floor=(0x10C, 0x118, 0x10F, 0x101, 0x10C | H, 0x118, 0x10F | H, 0x101 | H),
    ceiling=(0x10F | V, 0x118 | V, 0x10F | H | V),
    wall_w=(0x110, 0x110 | V),
    wall_e=(0x110 | H, 0x110 | H | V),
    outer_nw=0x100, outer_ne=0x100 | H, outer_sw=0x10D | V, outer_se=0x10D | H | V,
    inner_nw=0x114, inner_ne=0x114 | H, inner_sw=0x114 | V, inner_se=0x114 | H | V,
    pillar=0x110,
    platform=(0x11B, 0x11B | H), platform_l=0x11A, platform_r=0x11A | H,
    grass=(0x12E, 0x12F, 0x130, 0x12D),
)

CAVE = EdgeStyle(
    name="caverna", tileset=CAVE_TILESET,
    fill=(0x2B6, 0x2B8),        # by (x + y) parity, like the bond of $99BD
    floor=(0x2AF, 0x2AD),       # by x parity, like rows 13 of $9879
    ceiling=(0x2AF | V, 0x2AD | V),
    wall_w=(0x2B6, 0x2B8),      # vanilla walls are plain bricks: corners, pillar and ends too
    wall_e=(0x2B6, 0x2B8),
    platform=(0x2B6, 0x2B8),
    grass=(0x36F, 0x36D),
)

STYLES = (SURFACE, CAVE)
SOURCE_ROOMS = {   # vanilla rooms the pieces were read from (and are checked against)
    SURFACE.name: (0x91F8, 0x957D, 0x92FD, 0x948C, 0x9552, 0x9461, 0x95FF),
    CAVE.name: (0x99BD, 0x9A44, 0x9879, 0x98E2, 0x9969),
}
SOLID, AIR = 0x8, 0x0


def sce_metatile_count(rom: Rom, tileset: int) -> int:
    """Metatiles $100.. defined by the tileset's own (SCE) table."""
    entry = 0x8F0000 | rom.u16(TILESET_TABLE + 2 * tileset)
    table, _ = decompress(rom.data, snes_to_pc(rom.u24(entry)))
    return min(len(table) // 8, 0x300)


def vanilla_types(rom: Rom, rooms, tileset: int) -> dict[int, collections.Counter]:
    """metatile id (no flips) -> Counter of block types, over the states of `rooms` with `tileset`."""
    out: dict[int, collections.Counter] = collections.defaultdict(collections.Counter)
    seen = set()
    for addr in rooms:
        for st in read_room(rom, 0x8F0000 | addr).states:
            if st.tileset != tileset or st.level_data in seen:
                continue
            seen.add(st.level_data)
            l1, _, _ = read_level_data(rom, st)
            for w in l1:
                out[w & 0x3FF][w >> 12] += 1
    return out


def check(rom: Rom) -> list[str]:
    """Each piece is in its tileset's table and vanilla gives that metatile, most of the time, the
    collision the style gives it. Also the rain FX and the music of the vanilla Landing Site."""
    problems = []
    for style in STYLES:
        count = sce_metatile_count(rom, style.tileset)
        types = vanilla_types(rom, SOURCE_ROOMS[style.name], style.tileset)
        for want, pieces in ((SOLID, style.solid_pieces()), (AIR, style.air_pieces())):
            for word in sorted(pieces):
                mt = word & 0x3FF
                if not 0x100 <= mt < 0x100 + count:
                    problems.append(f"estilo {style.name}: metatile ${mt:03X} fora do tileset {style.tileset}")
                    continue
                c = types.get(mt)
                if not c:
                    problems.append(f"estilo {style.name}: metatile ${mt:03X} não aparece nas salas de origem")
                elif c.most_common(1)[0][0] != want:
                    problems.append(f"estilo {style.name}: metatile ${mt:03X} é tipo {c.most_common(1)[0][0]:X} "
                                    f"no vanilla, o estilo usa como tipo {want:X}")
    landing = read_room(rom, 0x8F91F8).default_state
    if (landing.tileset, landing.fx, (landing.music_data, landing.music_track)) != (
            SURFACE_TILESET, RAIN_FX, LANDING_SITE_MUSIC):
        problems.append("Landing Site vanilla: tileset/FX/música diferentes das constantes")
    fx = rom.read(0x830000 | RAIN_FX, 16)
    if fx[0:2] != b"\x00\x00" or fx[9] != 0x0A:
        problems.append(f"FX ${RAIN_FX:04X} não é chuva padrão: {fx.hex(' ')}")
    return problems

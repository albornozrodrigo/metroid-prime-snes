"""Chozo Ruins look (specs/12d-estilo-das-ruinas.md): the stone bricks of tileset $0C, recoloured to sandstone.

Tileset $0C is vanilla Maridia's rocky set (27 rooms, all of SM area 4, none of them on a path of ours nor in an
attract-mode demo: specs/11, proved by validate.check_ruins_in_rom). Its bricks are purple; the Chozo Ruins of Prime are
sandstone. The build writes a recoloured COPY of the tileset's palette in the fixed expanded range and points the tileset
table entry at it ($8F:E7A7 + 2*$0C, third pointer); the tile graphics and the metatile table stay vanilla.

Every value here was read from the vanilla ROM (base/sm_fix.sfc):
  - RUINS: for each air neighbourhood of the solid blocks of the brick rooms $8F:DA2B, $D7E4 and $D72A, the most common
    brick piece of palette line 7 (the tileset's own line). The bricks have no floor piece of their own (the top row is
    plain brick, as in $DA2B/$D7E4); the ceiling row is $15B (bricks with their bottom edge), the walls $1E6/$1E7. The
    most common floor piece of $D72A, $116, is on palette line 2, which the tileset shares with the doors and items, so it
    would not take the recolour: left out.
  - SANDSTONE: the 15 colours of palette line 7. The vanilla line has 3 browns (kept) and 12 purples/lavenders; these
    became sandstone by hue 0.10, saturation 0.25 + 0.45 s, value 0.95 v (computed once, written out here so the colour is
    one table to edit). The user has not confirmed the colour (specs/12, question 8): change the table, rebuild.
check() proves each piece is in the tileset and vanilla gives it the collision the style gives it (as crateria.check).
"""
from __future__ import annotations

import struct

from .compression import decompress
from .crateria import AIR, SOLID, sce_metatile_count, vanilla_types
from .gfx import TILESET_TABLE
from .rom import Rom, snes_to_pc
from .style import EdgeStyle

RUINS_TILESET = 0x0C
PALETTE_LINE = 7            # the line every RUINS piece uses (lines 0-3 are shared: doors, items, CRE)
# palette line 7, colours 1-15, as RGB hex (colour 0 is transparent). Vanilla:
#   AD844A 8C5A31 5A3918 D663CE 9C4A9C 73397B 4A215A DED6F7 B5ADCE 948CAD 7B7394 6B4A7B 4A3152 291839 080010
SANDSTONE = ("AD844A", "8C5A31", "5A3918", "CBA367", "94774C", "755E3B", "564328",
             "EBCEA2", "C4AA85", "A48E6D", "8D795B", "756143", "4E402C", "362B1B", "0F0B05")

RUINS = EdgeStyle(
    name="ruinas", tileset=RUINS_TILESET,
    fill=(0x1E1, 0x1E3),        # by (x + y) parity, like the rows of $D7E4/$DA2B
    floor=(0x1E1, 0x1E3),       # plain brick on top (the bricks have no floor piece)
    ceiling=(0x15B,),           # $DA2B: the brick row over the air, with its bottom edge
    wall_w=(0x1E6,),
    wall_e=(0x1E7,),
    platform=(0x15B,),          # a 1-block ledge: the ceiling piece (most common NS piece of line 7)
)
STYLES = (RUINS,)
SOURCE_ROOMS = {RUINS.name: (0xDA2B, 0xD7E4, 0xD72A)}


def _bgr555(rgb_hex: str) -> int:
    r, g, b = (int(rgb_hex[i:i + 2], 16) for i in (0, 2, 4))
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


def recolor(palette: bytes) -> bytes:
    """Tileset $0C's palette with line PALETTE_LINE = SANDSTONE."""
    out = bytearray(palette)
    for i, c in enumerate(SANDSTONE, start=1):
        o = 2 * (PALETTE_LINE * 16 + i)
        w = _bgr555(c)
        out[o], out[o + 1] = w & 0xFF, w >> 8
    return bytes(out)


# specs/12f: the ruins' background (the library background $8F:E25A of the vanilla $0C rooms, tools/areas.py CHOZO_BG) draws
# with palette line 6 only (its BG2 tilemap, $BA:A69F, read). Vanilla line 6 is Maridia's dark greens and browns; here the
# same shades in a dark sandstone: each vanilla colour by hue 0.10, saturation 0.25 + 0.45 s, value 0.6 v (SANDSTONE's rule,
# darker: a background behind the bricks), computed once and written out. Vanilla:
#   204838 082820 001810 100000 180800 281008 301808 381810 402010 502818 583018 808080 F8F8F8 180800 001008
BACKGROUND_LINE = 6
SANDSTONE_BACKGROUND = ("2B2316", "181209", "0E0A04", "0A0703", "0E0A04", "181209", "1D160B", "221A0E",
                        "261D10", "302515", "352916", "4D453A", "958670", "0E0A04", "0A0703")


def recolor_background(palette: bytes) -> bytes:
    """specs/12f: tileset $0C's palette with line BACKGROUND_LINE = SANDSTONE_BACKGROUND."""
    out = bytearray(palette)
    for i, c in enumerate(SANDSTONE_BACKGROUND, start=1):
        o = 2 * (BACKGROUND_LINE * 16 + i)
        w = _bgr555(c)
        out[o], out[o + 1] = w & 0xFF, w >> 8
    return bytes(out)


def entry(rom: Rom) -> int:
    """Tileset $0C's entry in the tileset table: three 24-bit pointers (metatiles, graphics, palette)."""
    return 0x8F0000 | rom.u16(TILESET_TABLE + 2 * RUINS_TILESET)


def vanilla_palette(rom: Rom) -> bytes:
    return decompress(rom.data, snes_to_pc(rom.u24(entry(rom) + 6)))[0]


def vanilla_metatiles(rom: Rom) -> bytes:
    """Tileset $0C's metatile table (decompressed) as `rom`'s entry points at it (the base ROM's: vanilla)."""
    return decompress(rom.data, snes_to_pc(rom.u24(entry(rom))))[0]


def pieces_palette_lines(rom: Rom) -> set[int]:
    """Palette lines of the tiles of every RUINS piece (metatile table of tileset $0C)."""
    table = decompress(rom.data, snes_to_pc(rom.u24(entry(rom))))[0]
    lines = set()
    for word in RUINS.solid_pieces() | RUINS.air_pieces():
        mt = (word & 0x3FF) - 0x100
        lines |= {(w >> 10) & 7 for w in struct.unpack_from("<4H", table, mt * 8)}
    return lines


def check(rom: Rom) -> list[str]:
    """Each piece is in tileset $0C's own table, appears in the source rooms with the collision the style gives it, and
    its tiles use palette line PALETTE_LINE only (so the whole style takes the recolour)."""
    problems = []
    for style in STYLES:
        count = sce_metatile_count(rom, style.tileset)
        types = vanilla_types(rom, SOURCE_ROOMS[style.name], style.tileset)
        for want, pieces in ((SOLID, style.solid_pieces()), (AIR, style.air_pieces())):
            for word in sorted(pieces):
                mt = word & 0x3FF
                if not 0x100 <= mt < 0x100 + count:
                    problems.append(f"estilo {style.name}: metatile ${mt:03X} fora do tileset {style.tileset:02X}")
                    continue
                c = types.get(mt)
                if not c:
                    problems.append(f"estilo {style.name}: metatile ${mt:03X} não aparece nas salas de origem")
                elif c.most_common(1)[0][0] != want:
                    problems.append(f"estilo {style.name}: metatile ${mt:03X} é tipo {c.most_common(1)[0][0]:X} "
                                    f"no vanilla, o estilo usa como tipo {want:X}")
    lines = pieces_palette_lines(rom)
    if lines != {PALETTE_LINE}:
        problems.append(f"estilo ruinas: peças nas linhas de paleta {sorted(lines)}; o recolor só pinta a {PALETTE_LINE}")
    if len(SANDSTONE) != 15 or any(len(c) != 6 for c in SANDSTONE):
        problems.append("SANDSTONE precisa de 15 cores RGB em hex")
    return problems

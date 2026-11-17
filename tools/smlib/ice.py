"""Phendrana Drifts looks and snow (specs/18d-estilos-do-gelo.md; epic 18, decision 6 "padrão aceito, a confirmar": three looks,
snow where Prime snows).

Three looks, each on a tileset table entry no room the game loads uses (validate.check_ice_in_rom; their vanilla users are only
orphan rooms, specs/11), each a recoloured COPY of a palette we already draw with, written in the fixed range:

  - SNOW (outdoors, the rooms with sky in Prime): entry $01 (vanilla: Upper Crateria's metatiles $C1:B6F6 and graphics $BA:C629,
    the same as $00, the Tallon's surface; no vanilla state uses $01). Pieces = crateria.SURFACE without its grass (all on palette
    line 4: colours 1-3 and 12 draw the grass rim on top of the floors, 4-7 and 15 the rock, counted from the tiles), so line 4
    becomes snow on blue-grey ice (SNOW_COLOURS) and line 5, the cloud sky's (crateria.SKY_TILEMAP: every tile on line 5), a pale
    winter sky. Its metatile table is a copy of $00's with the purple wave door's 8 metatiles $3F0-$3F7 (vanilla filler there) on
    line SNOW_PAINT_LINE = 6 (no SURFACE piece, no sky tile and no CRE metatile uses it); specs/18j: and the vertical purple wave
    door's 8 ($3F8-$3FE, $3EF: tallon/beamdoors.py VERT_PAINT_METATILES, vanilla filler there too) on the same line.
  - RUINS (the icy Chozo ruins: Ice Temple, Ice Ruins, Chapel, Ruined Courtyard): entry $1C (vanilla: Draygon's room only, an
    orphan), pointed at tileset $0C's graphics and at the Chozo's own copy of $0C's metatile table (specs/12f/12g2: the wave door
    on line 5, the charge door on line 4); palette = the Chozo's (build.ruins_palette) with the bricks' line 7 in ice (RUINS_COLOURS)
    and the background's line 6 ($8F:E25A, every tile on line 6) in dark ice. Pieces = ruins.RUINS.
  - LAB (the pirates' labs: Research Entrance, the Research Labs, Observatory, towers, Research Core): entry $1B (vanilla:
    Crocomire's room only, an orphan; the epic proposed $05, the Wrecked Ship's twin of $04, but an attract demo room, $CC6F, uses
    $05 and $1A), pointed at tileset 4's vanilla graphics (the frigate's copy has the Parasite Queen's tiles appended) and at
    tileset 4's own copy of its table
    (specs/10d: the wave door on line 6); palette = tileset 4's vanilla with the frigate pieces' line 4 (smlib/style.py Style: every
    piece on line 4) and the background's line 5 ($8F:E117: lines 5 and 0) in cold lab steel (LAB_COLOURS), line 6 purple.

Door colours: lines 0 (colours 1-3) and 1 (1-7) of every look's palette = tileset 4's (checked on the base ROM): the blue, red,
green (ice), orange (plasma) caps look as everywhere; the wave door is purple (beamdoors.PURPLE) on each look's paint line.

Snow: SM has no snow. Its BG3 FX that fall: the spores (type 8, FxTypeFunc_8_Spores $88:DA11: the BG3 layer moves down 64/256 px a
frame, HdmaobjPreInstr_SporesBG3Xscroll $88:DA47; 4 vanilla states in area 1) and the rain (type $0A, $88:D950: 1536/256 px a frame
with a random sideways drift; the Tallon's Landing Site). Both draw their tilemap ($8A, kFxTypeTilemapPtrs $83:ABF0) with BG3
palette 6 = palette colours 24-27 = line 1 colours 8-11, and their animated tiles ($87:82FD / $87:82E7) use pixel values 1-2 for
the flakes/drops and 3 for the fill, which the FX's palette blend 0 makes black (LoadFxEntry $89:AB02: colour 27 = 0), invisible in
the additive layer blend. No CRE tile draws line 1 colours 8-11 (scanned, check()), so each look's line 1 colours 9 and 10 are the
snowflakes' (SNOW_FLAKES). Measured in the emulator (build.py --teste-18d, tests neve_medida): SNOW_FX = the spores' entry
(vanilla $83:82F4 with no palette FX nor animated tiles of an area list).
"""
from __future__ import annotations

import struct

from .compression import decompress
from .crateria import AIR, SOLID, SURFACE, SKY_BG, SKY_LAYER2, SKY_TILEMAP, sce_metatile_count, vanilla_types
from .crateria import SOURCE_ROOMS as CRATERIA_SOURCES
from .gfx import CRE_TILE_TABLE, CRE_TILES, TILESET_TABLE
from .rom import Rom, snes_to_pc
from .style import EdgeStyle
from . import ruins

SNOW_TILESET, SNOW_SOURCE = 0x01, 0x00     # entry repointed / the tileset whose table, graphics and palette it copies
RUINS_TILESET, RUINS_SOURCE = 0x1C, ruins.RUINS_TILESET
LAB_TILESET, LAB_SOURCE = 0x1B, 0x04
TILESETS = (SNOW_TILESET, RUINS_TILESET, LAB_TILESET)
SOURCE = {SNOW_TILESET: SNOW_SOURCE, RUINS_TILESET: RUINS_SOURCE, LAB_TILESET: LAB_SOURCE}
SNOW_PAINT_LINE = 6                       # the purple wave door's line in the snow look (tileset 4's is 6, $0C's 5)
# the purple door's line of each look: the snow's own; the icy ruins' = the Chozo table's (beamdoors.RUINS_PAINT_LINE); the
# lab's = tileset 4's table's (beamdoors.PAINT_LINE); validate.check_ice_in_rom checks them against beamdoors
PAINT_LINES = {SNOW_TILESET: SNOW_PAINT_LINE, RUINS_TILESET: 5, LAB_TILESET: 6}

# (palette line, colour) -> RGB hex, the only colour tables (decision to confirm with the user: change, rebuild). Written out
# from a transform of the vanilla colours (scratchpad s18d/scripts/explore.py) and adjusted by eye on the previews.
#   SNOW line 4 (vanilla 1D89 0D06 0CA3 2D0E 2D09 28C5 0C81 55CE 3D68 24A2 1400 320C 2108 7FFF 0420): 1-3, 12 the grass rim ->
#   snow; 4-7, 15 green rock -> blue-grey ice; line 5 (the sky, vanilla greys) -> a pale winter sky.
SNOW_COLOURS = {**{(4, i): c for i, c in enumerate(
    "F8FCFF D0E0F0 98B0CC A8C0D8 7E98B4 5C7894 445E7A 9AB4D0 7890B0 5A7090 3C506C E4EEF8 8CA4BC FFFFFF 22324A".split(), 1)},
    **{(5, i): c for i, c in enumerate(
        "98A3B3 727A86 4C525A 464E5A 404752 39404B 333944 242A34 242A34 1B222D 202226 61728D 576D8D D9E8FF 101B2D".split(), 1)}}
#   RUINS line 7 (ruins.SANDSTONE's line: vanilla purple bricks) -> ice bricks; line 6 (the background) -> dark ice
RUINS_COLOURS = {**{(7, i): c for i, c in enumerate(
    "80A6C2 698EA9 4D6C83 99C2E0 7C9DB5 6A879C 536F83 DCEDF9 BECEDA A5B6C2 93A3AF 758C9C 5E707D 465B6A 223A4C".split(), 1)},
    **{(6, i): c for i, c in enumerate(
        "27354A 121C2D 09111D 070D16 09111D 121C2D 142134 1A273B 1C2C43 243651 263B59 656F7E BED1ED 09111D 070D16".split(), 1)}}
#   LAB line 4 (the frigate pieces, vanilla olive metal) and 5 (the background) -> cold cyan-white steel
LAB_COLOURS = {**{(4, i): c for i, c in enumerate(
    "9DC6CF 749FA8 467680 98B6BC 708E94 41656D 4B5659 BDE2EA 95BAC3 6B929B 4D7780 71B4C3 6CDEF7 F2FDFF 353838".split(), 1)},
    **{(5, i): c for i, c in enumerate(
        "528F9D 2A5D68 1F454D 7D979D 546F75 26464D 223B41 9BBDC5 73959D 4A6E75 2A525B 479EB1 56C1D8 E6F0F2 242626".split(), 1)}}
COLOURS = {SNOW_TILESET: SNOW_COLOURS, RUINS_TILESET: RUINS_COLOURS, LAB_TILESET: LAB_COLOURS}
OWN_LINES = {SNOW_TILESET: (4, 5), RUINS_TILESET: (6, 7), LAB_TILESET: (4, 5)}   # the lines each look recolours
FLAKE_LINE = 1
SNOW_FLAKES = {(FLAKE_LINE, 9): "F8FCFF", (FLAKE_LINE, 10): "B8D0E8"}   # BG3 palette 6, pixel values 1 and 2

# the styles (pieces checked on the base ROM against the vanilla rooms they were read from, check())
SNOW = EdgeStyle(**{**SURFACE.__dict__, "name": "neve", "tileset": SNOW_TILESET, "grass": ()})
ICE_RUINS = EdgeStyle(**{**ruins.RUINS.__dict__, "name": "ruinas_de_gelo", "tileset": RUINS_TILESET})
STYLES = (SNOW, ICE_RUINS)
# backgrounds (library background list, BG2 scroll) per look
BACKGROUND = {SNOW_TILESET: (SKY_BG, SKY_LAYER2), RUINS_TILESET: (0xE25A, 0x01C1), LAB_TILESET: (0xE117, 0xC1C1)}
# music: Maridia's song set $1B (the Chozo's, already loaded there), track $06 (the inner Maridia theme; 4 vanilla states of
# tileset $0B): calm and slow, like Prime's Phendrana theme. A decision to confirm with the user.
MUSIC = (0x1B, 0x06)

# snow FX entries (16 bytes: door 0, base y, target y, y speed, timer, type, layer blends, liquid options, palette FX, animated
# tiles, palette blend): SNOW = the vanilla spores' ($83:82F4, read); SNOW_RAIN (test build only: the rain, for the comparison
# photo) = the Landing Site's rain $83:80C0 without its area palette FX (bit 0 of area 4's list is Maridia's) and palette blend 0
SPORES, RAIN = 0x08, 0x0A
VANILLA_SPORES_FX = 0x8382F4
SNOW_FX = {SPORES: bytes.fromhex("0000" "FFFF" "FFFF" "0000" "00" "08" "02" "0A" "00" "00" "00" "00"),
           RAIN: bytes.fromhex("0000" "FFFF" "FFFF" "0000" "00" "0A" "02" "0E" "00" "00" "00" "00")}
VANILLA_RAIN_FX = 0x8380C0


def _bgr555(rgb_hex: str) -> int:
    r, g, b = (int(rgb_hex[i:i + 2], 16) for i in (0, 2, 4))
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


def entry(rom: Rom, tileset: int) -> int:
    return 0x8F0000 | rom.u16(TILESET_TABLE + 2 * tileset)


def vanilla_palette(rom: Rom, tileset: int) -> bytes:
    return decompress(rom.data, snes_to_pc(rom.u24(entry(rom, tileset) + 6)))[0]


def vanilla_metatiles(rom: Rom, tileset: int) -> bytes:
    return decompress(rom.data, snes_to_pc(rom.u24(entry(rom, tileset))))[0]


def recolor(palette: bytes, tileset: int) -> bytes:
    """`palette` with the look's colours (COLOURS[tileset]) and the snowflakes' (SNOW_FLAKES)."""
    out = bytearray(palette)
    for (line, i), c in {**COLOURS[tileset], **SNOW_FLAKES}.items():
        out[2 * (line * 16 + i):2 * (line * 16 + i) + 2] = _bgr555(c).to_bytes(2, "little")
    return bytes(out)


def _tile_pixels(gfx: bytes, tile: int) -> set[int]:
    base = tile * 32
    out = set()
    for row in range(8):
        b = (gfx[base + 2 * row], gfx[base + 2 * row + 1], gfx[base + 16 + 2 * row], gfx[base + 17 + 2 * row])
        out |= {sum(((b[k] >> (7 - x)) & 1) << k for k in range(4)) for x in range(8)}
    return out


def piece_colours(rom: Rom, source: int, pieces, cre: bool = False) -> dict[int, set[int]]:
    """{palette line: colour indices} the tiles of the metatiles `pieces` draw with (tileset `source`'s table and graphics; `cre`:
    the CRE's table and graphics)."""
    if cre:
        table = decompress(rom.data, snes_to_pc(CRE_TILE_TABLE))[0]
        gfx, first = decompress(rom.data, snes_to_pc(CRE_TILES))[0], 0x280
    else:
        table = vanilla_metatiles(rom, source)
        gfx, first = decompress(rom.data, snes_to_pc(rom.u24(entry(rom, source) + 3)))[0], 0
    out: dict[int, set[int]] = {}
    for word in pieces:
        m = (word & 0x3FF) - (0 if cre else 0x100)
        for w in struct.unpack_from("<4H", table, m * 8):
            t = (w & 0x3FF) - first
            if 0 <= t * 32 < len(gfx):
                out.setdefault((w >> 10) & 7, set()).update(_tile_pixels(gfx, t))
    return out


def check(rom: Rom) -> list[str]:
    """On the base ROM: $01 shares $00's metatiles and graphics; the three entries are their own (no other
    tileset points at them); each style's pieces are the vanilla ones (crateria/ruins sources: the collision the style gives
    them) on the lines the look recolours; the lines the look recolours are not drawn by any CRE metatile, nor the wave door's
    paint line of the snow; the door colours (lines 0 1-3, 1 1-7) are tileset 4's in every source palette; no CRE tile draws
    line 1 colours 8-11 (the snowflakes'); the spores' and the rain's vanilla FX entries are what SNOW_FX copies; the colour
    tables are well formed."""
    problems = []
    words = [rom.u16(TILESET_TABLE + 2 * i) for i in range(0x1D)]
    for t in TILESETS:
        if words.count(words[t]) != 1:
            problems.append(f"gelo: a entrada do tileset {t:02X} é dividida com outro")
    for t, src in ((SNOW_TILESET, SNOW_SOURCE),):
        a, b = entry(rom, t), entry(rom, src)
        if rom.u24(a) != rom.u24(b) or rom.u24(a + 3) != rom.u24(b + 3):
            problems.append(f"gelo: tilesets {t:02X} e {src:02X} não dividem metatiles e gráficos no vanilla")
    # SNOW: SURFACE's pieces (crateria.check checks them against the Landing Site rooms), grass left out, all on line 4
    if SNOW.solid_pieces() != SURFACE.solid_pieces() or SNOW.air_pieces():
        problems.append("gelo: estilo neve diferente das peças da superfície (sem a grama)")
    if ICE_RUINS.solid_pieces() != ruins.RUINS.solid_pieces() or ICE_RUINS.air_pieces() != ruins.RUINS.air_pieces():
        problems.append("gelo: estilo ruínas de gelo diferente das peças das ruínas")
    count = sce_metatile_count(rom, SNOW_SOURCE)
    types = vanilla_types(rom, CRATERIA_SOURCES[SURFACE.name], SNOW_SOURCE)
    for word in sorted(SNOW.solid_pieces()):
        mt = word & 0x3FF
        c = types.get(mt)
        if not 0x100 <= mt < 0x100 + count or not c or c.most_common(1)[0][0] != SOLID:
            problems.append(f"estilo neve: metatile ${mt:03X} não é sólido nas salas de origem do tileset {SNOW_SOURCE:02X}")
    from .style import Style
    st = Style()
    lab_pieces = (set(st.floor + st.hull + st.ceiling_light)
                  | {st.wall_face_right, st.outer_corner, st.thin_pillar, st.inner_nw, st.inner_ne, st.inner_sw, st.inner_se,
                     st.strut})
    for t, pieces in ((SNOW_TILESET, SNOW.solid_pieces()), (RUINS_TILESET, ICE_RUINS.solid_pieces()),
                      (LAB_TILESET, lab_pieces)):
        used = piece_colours(rom, SOURCE[t], pieces)
        if set(used) - set(OWN_LINES[t]):
            problems.append(f"gelo: peças do tileset {t:02X} nas linhas {sorted(used)}, o recolor pinta {OWN_LINES[t]}")
    for t in TILESETS:
        if PAINT_LINES[t] in OWN_LINES[t] or PAINT_LINES[t] in (FLAKE_LINE, 0, 2, 3):
            problems.append(f"gelo: a linha {PAINT_LINES[t]} da porta de onda do tileset {t:02X} é das peças, do fundo ou do CRE")
    cre_table = decompress(rom.data, snes_to_pc(CRE_TILE_TABLE))[0]
    cre_used = piece_colours(rom, 0, range(len(cre_table) // 8), cre=True)
    for t in TILESETS:
        for line in OWN_LINES[t] + (PAINT_LINES[t],):
            if cre_used.get(line):
                problems.append(f"gelo: metatiles do CRE desenham na linha {line}, que o tileset {t:02X} repinta")
    if cre_used.get(FLAKE_LINE, set()) & {8, 9, 10, 11}:
        problems.append(f"gelo: metatiles do CRE desenham com as cores 8-11 da linha {FLAKE_LINE} (as da neve)")
    sky = rom.read(SKY_TILEMAP, 0x800)
    if {(w >> 10) & 7 for w in struct.unpack_from("<1024H", sky)} != {5}:
        problems.append("gelo: o céu (crateria.SKY_TILEMAP) não é todo da linha 5")
    snow_table = vanilla_metatiles(rom, SNOW_SOURCE)
    if any(snow_table[(m - 0x100) * 8:(m - 0x100) * 8 + 8] != bytes.fromhex("ff03ff03ff03ff03") for m in range(0x3F0, 0x3F8)):
        problems.append(f"gelo: metatiles $3F0-$3F7 do tileset {SNOW_SOURCE:02X} não são enchimento (a porta de onda)")
    # specs/18j: and the vertical wave door's 8 (tallon/beamdoors.py VERT_PAINT_METATILES: $3F8-$3FE, $3EF), painted there too
    from tallon.beamdoors import VERT_PAINT_METATILES
    if any(snow_table[(m - 0x100) * 8:(m - 0x100) * 8 + 8] != bytes.fromhex("ff03ff03ff03ff03")
           for m in VERT_PAINT_METATILES.values()):
        problems.append(f"gelo: metatiles da porta de onda vertical do tileset {SNOW_SOURCE:02X} não são enchimento")
    ref = vanilla_palette(rom, 4)
    for src in (SNOW_SOURCE, RUINS_SOURCE, LAB_SOURCE):
        pal = vanilla_palette(rom, src)
        for line, colours in ((0, range(1, 4)), (1, range(1, 8))):
            for i in colours:
                o = 2 * (line * 16 + i)
                if pal[o:o + 2] != ref[o:o + 2]:
                    problems.append(f"gelo: tileset {src:02X} linha {line} cor {i} diferente da do tileset 4 (cor das portas)")
    for t, colours in COLOURS.items():
        if (set(colours) - {(ln, i) for ln in OWN_LINES[t] for i in range(1, 16)}
                or any(len(c) != 6 for c in colours.values())):
            problems.append(f"gelo: cores do tileset {t:02X} mal formadas")
    if rom.read(VANILLA_SPORES_FX, 16) != SNOW_FX[SPORES]:
        problems.append(f"gelo: FX vanilla dos esporos ${VANILLA_SPORES_FX:06X} = {rom.read(VANILLA_SPORES_FX, 16).hex()}")
    rain = bytearray(rom.read(VANILLA_RAIN_FX, 16))
    rain[13], rain[15] = 0, 0   # the Landing Site's palette FX bit and palette blend left out
    if bytes(rain) != SNOW_FX[RAIN]:
        problems.append(f"gelo: FX vanilla da chuva ${VANILLA_RAIN_FX:06X} = {rom.read(VANILLA_RAIN_FX, 16).hex()}")
    return problems

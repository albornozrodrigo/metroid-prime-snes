"""Magmoor Caverns look and lava (specs/17d-estilo-das-cavernas-de-lava.md): Norfair's tilesets $09 (hot rooms) and $0A (cool
rooms), recoloured to Prime's Magmoor (dark rock, orange/red glow), the purple wave door painted in them, and SM's lava FX.

Every value here was read from the vanilla ROM (base/sm_fix.sfc; roteiros do scratchpad s17d/scripts):
  - $8F:E7A7 + 2*$09 -> $8F:E6F3 = metatiles $C1:E361, graphics $BD:C3F9, palette $C2:B5E4; $8F:E7A7 + 2*$0A -> $8F:E6FC = the
    same metatiles and graphics, palette $C2:B6BB. The two tilesets are one look with two palettes (epic 17, technical decision 3:
    hot rooms on $09, cool ones on $0A, so the colour tells the player where it burns). No room of ours and no attract demo uses
    them (validate.check_lava_in_rom).
  - LAVA: for each air neighbourhood of the solid blocks of the vanilla cave rooms $8F:A923 and $AE07 (dark rock with a red
    crust), the most common piece (fill $3FF, floors $11D/$11C/$10E, ceiling $113 v-flipped, walls $107/$105, the lower corners $13B, a 1-block pillar $10C, ledges $101). All of them are on palette line 4 (check()).
  - The recolour (COLOURS_HOT / COLOURS_COOL) changes only the colours of line 4 those pieces draw with (8-11, 13, 15: counted
    from their tiles) and colours 4-7 of line 6, the background's (BACKGROUND's tiles use 4-7 and 15). Colours 1-3, 12 and 13 of lines 4-6 and 5-7, 11-12 of line 3 are rewritten every frame by the lava glow
    palette FX objects of area 2's list (bits 1-4: $F785 line 3, $F789 line 4, $F78D line 5, $F791 line 6; decoded from $8D) in
    the rooms whose FX sets those bits (FX_HOT: the hot rooms, as vanilla Norfair's $1F), so colour 13 of the crust glows there.
  - The purple wave door (specs/10d, 12f): the 8 metatiles $3F0-$3F7 of the shared table (vanilla filler `$03FF x4`) and palette
    line PAINT_LINE = 7 (no LAVA piece, no CRE metatile and not the background BACKGROUND use it; the glow objects don't touch it).
    The green (ice) and orange (plasma) caps use lines 1 and 0, colours 1-3, with the frame on line 1 colours 4-7: the same
    colours as tileset 4's (checked).
  - Background: the library background $8F:BE5A (6 vanilla states of $09, 2 of $0A: $B9:A714 into BG2, every tile on palette
    line 6) with BG2 scroll $C1C1; music: Upper Norfair's song set $15, track $05 (9 vanilla states).
  - Lava: SM's FX type 2 (Samus_Animate_LavaFx $90:81C0: under the surface, without the Gravity Suit, half an energy a frame,
    halved again with the Varia by Samus_HandlePeriodicDamage; with the Gravity Suit nothing and normal physics). FX entry =
    vanilla Upper Norfair's lava entry ($83:8430: `0000 00B8 FFFF 0000 00 02 02 1E 0B 1F 02 02`) with our surface y and
    palette FX bits (fx_entry). Damage and the jump out of the lava are measured in the emulator (tools/build.py --teste-17d,
    tests lava_medida; smlib/reach.py LAVA_*).
"""
from __future__ import annotations

import struct

from .compression import decompress
from .crateria import AIR, SOLID, sce_metatile_count, vanilla_types
from .gfx import TILESET_TABLE
from .rom import Rom, snes_to_pc
from .style import H, V, EdgeStyle

HOT_TILESET, COOL_TILESET = 0x09, 0x0A
TILESETS = (HOT_TILESET, COOL_TILESET)
PALETTE_LINE = 4             # the line every LAVA piece uses
PAINT_LINE = 7               # the purple wave door's line in both palettes
BACKGROUND, LAYER2 = 0xBE5A, 0xC1C1   # library background (BG2 on line 6) and its scroll
BACKGROUND_LINE = 6
MUSIC = (0x15, 0x05)         # Upper Norfair

# (palette line, colour index) -> RGB hex. Vanilla line 4 ($09 / $0A): 8 0C99 / 4E79, 9 0C72 / 39D4, 10 0C49 / 1CED, 11 0C41,
# 13 0C77, 15 0000 (a black fill, the same as the air); here the fill is dark rock, the band under the crust dark brown, the
# crust orange-red in the hot rooms and dim embers in the cool ones. Line 6 colours 4-7 (the background BACKGROUND's tiles
# draw with 4-7 and 15; vanilla $0A 20CE 1C89 1465 1420: purple) become dark warm rock behind the walls. A decision to confirm
# with the user (the only tables to change: rebuild).
COLOURS_HOT = {(4, 8): "FFB840", (4, 9): "E86018", (4, 10): "962810", (4, 11): "40302A", (4, 13): "C84018", (4, 15): "261C18",
               (6, 4): "462419", (6, 5): "341C14", (6, 6): "261410", (6, 7): "1A0E0C"}
COLOURS_COOL = {(4, 8): "B06840", (4, 9): "884028", (4, 10): "582820", (4, 11): "3C3230", (4, 13): "703020", (4, 15): "241E1E",
                (6, 4): "3A2822", (6, 5): "2C1E1A", (6, 6): "221814", (6, 7): "18100E"}
COLOURS = {HOT_TILESET: COLOURS_HOT, COOL_TILESET: COLOURS_COOL}

_LAVA = dict(
    fill=(0x3FF,),
    floor=(0x11D, 0x11C, 0x10E),
    ceiling=(0x113 | V,),
    wall_w=(0x107 | H, 0x105 | H),
    wall_e=(0x107, 0x105),
    platform=(0x101,),
    outer_sw=0x13B | V, outer_se=0x13B | H | V,
    pillar=0x10C,
)
LAVA_HOT = EdgeStyle(name="lava_quente", tileset=HOT_TILESET, **_LAVA)
LAVA_COOL = EdgeStyle(name="lava_fria", tileset=COOL_TILESET, **_LAVA)
STYLES = (LAVA_HOT, LAVA_COOL)
SOURCE_ROOMS = (0xA923, 0xAE07)   # tileset $09 rooms the pieces were read from (and are checked against)

# SM's lava FX (type 2), as vanilla Upper Norfair's $83:8430 (door 0, base y, target $FFFF, speed 0, timer 0, type 2, blend
# $02/$1E, liquid options $0B, palette FX, animated tiles $02, palette blend $02)
LAVA_TYPE = 0x02
VANILLA_LAVA_FX = 0x838430
FX_HOT = 0x1F     # area 2's list: bit 0 the heat ($F761), bits 1-4 the lava glows (as vanilla Norfair's hot rooms)
FX_COOL = 0x00


# specs/20g: SM's acid (FX type 4), the crater's phazon that hurts (epic 20, decision 4; epic 19's option b of decision 6: the
# acid, which hurts with every suit). Samus_Animate_AcidFx ($90:8219): under the surface 1.5 energy a frame, then
# Samus_HandlePeriodicDamage: a quarter with the Gravity Suit, half with the Varia only; the body sinks as in the lava
# (Samus_Animate_SubmergedLavaAcid, the same liquid physics). FX entry = vanilla Crateria's acid ($83:80E0, room $92B3, area 0:
# `0000 00C8 FFFF 0000 00 04 02 1E 42 00 00 00`, no palette FX nor animated tiles: area 0's lists) with our surface y and liquid
# options $02 for its $42 (vanilla Norfair's acid $83:888C has $02): bit $40 is the big tide (FxHandleTide $88:B2C9 reads the
# options' low byte as the sign/bit 14 of a word: $40 = +-16 px, $80 = +-4 px), measured in the emulator (s20g: with $42 the
# surface went $29C-$2C8 round $2B0 and caught Samus standing on the floor over it); $02 = no tide: the surface stays on its row
ACID_TYPE = 0x04
VANILLA_ACID_FX = 0x8380E0
ACID_OPTIONS = 0x02
ACID_DAMAGE_PER_FRAME = {"nada": 1.5, "varia": 0.75, "gravity": 0.375}


def acid_fx_entry(surface_y: int) -> bytes:
    """A 16-byte FX entry of area 0: acid with its surface at pixel `surface_y`, no tide (the vanilla Crateria entry's other
    bytes)."""
    return struct.pack("<HHHHBBBBBBBB", 0, surface_y, 0xFFFF, 0, 0, ACID_TYPE, 0x02, 0x1E, ACID_OPTIONS, 0x00, 0x00, 0x00)


def fx_entry(surface_y: int | None, palette_fx: int) -> bytes:
    """A 16-byte FX entry of area 2: lava with its surface at pixel `surface_y` (None: no liquid, as heat.heat_fx), with the
    palette FX bits `palette_fx`."""
    if surface_y is None:
        return (bytes.fromhex("0000" "FFFF" "FFFF" "0000" "00" "00" "02" "02" "00") + bytes([palette_fx])
                + bytes.fromhex("0000"))
    return struct.pack("<HHHHBBBBBBBB", 0, surface_y, 0xFFFF, 0, 0, LAVA_TYPE, 0x02, 0x1E, 0x0B, palette_fx, 0x02, 0x02)


def _bgr555(rgb_hex: str) -> int:
    r, g, b = (int(rgb_hex[i:i + 2], 16) for i in (0, 2, 4))
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


def entry(rom: Rom, tileset: int) -> int:
    """The tileset's entry in the tileset table: three 24-bit pointers (metatiles, graphics, palette)."""
    return 0x8F0000 | rom.u16(TILESET_TABLE + 2 * tileset)


def vanilla_palette(rom: Rom, tileset: int) -> bytes:
    return decompress(rom.data, snes_to_pc(rom.u24(entry(rom, tileset) + 6)))[0]


def vanilla_metatiles(rom: Rom) -> bytes:
    """The metatile table both tilesets share (decompressed), as `rom`'s $09 entry points at it (the base ROM's: vanilla)."""
    return decompress(rom.data, snes_to_pc(rom.u24(entry(rom, HOT_TILESET))))[0]


def recolor(palette: bytes, tileset: int) -> bytes:
    """The tileset's palette with the colours of COLOURS[tileset] (the style's line PALETTE_LINE, the background's line 6)."""
    out = bytearray(palette)
    for (line, i), c in COLOURS[tileset].items():
        o = 2 * (line * 16 + i)
        out[o:o + 2] = _bgr555(c).to_bytes(2, "little")
    return bytes(out)


def piece_lines(table: bytes, pieces) -> set[int]:
    lines = set()
    for word in pieces:
        mt = (word & 0x3FF) - 0x100
        lines |= {(w >> 10) & 7 for w in struct.unpack_from("<4H", table, mt * 8)}
    return lines


def check(rom: Rom) -> list[str]:
    """On the base ROM: both tilesets share the metatile table and the graphics; each piece is in the table, appears in the
    source rooms with the collision the style gives it, and all are on palette line PALETTE_LINE; the paint line is used by no
    piece; the door colours of lines 0/1 are tileset 4's; the colour tables are well formed; the lava FX is vanilla's."""
    problems = []
    a, b = entry(rom, HOT_TILESET), entry(rom, COOL_TILESET)
    if rom.u24(a) != rom.u24(b) or rom.u24(a + 3) != rom.u24(b + 3):
        problems.append("lava: tilesets 09 e 0A não dividem metatiles e gráficos no vanilla")
    count = sce_metatile_count(rom, HOT_TILESET)
    types = vanilla_types(rom, SOURCE_ROOMS, HOT_TILESET)
    pieces = LAVA_HOT.solid_pieces()
    if pieces != LAVA_COOL.solid_pieces():
        problems.append("lava: estilos quente e frio com peças diferentes")
    for word in sorted(pieces):
        mt = word & 0x3FF
        if not 0x100 <= mt < 0x100 + count:
            problems.append(f"estilo lava: metatile ${mt:03X} fora do tileset 09")
            continue
        c = types.get(mt)
        if not c:
            problems.append(f"estilo lava: metatile ${mt:03X} não aparece nas salas de origem")
        elif c.most_common(1)[0][0] != SOLID:
            problems.append(f"estilo lava: metatile ${mt:03X} é tipo {c.most_common(1)[0][0]:X} no vanilla, o estilo usa "
                            f"como tipo {SOLID:X}")
    table = vanilla_metatiles(rom)
    lines = piece_lines(table, pieces)
    if lines != {PALETTE_LINE}:
        problems.append(f"estilo lava: peças nas linhas de paleta {sorted(lines)}; o recolor só pinta a {PALETTE_LINE}")
    ref = decompress(rom.data, snes_to_pc(rom.u24(entry(rom, 4) + 6)))[0]
    for ts in TILESETS:
        pal = vanilla_palette(rom, ts)
        for line, colours in ((0, range(1, 4)), (1, range(1, 8))):
            for i in colours:
                o = 2 * (line * 16 + i)
                if pal[o:o + 2] != ref[o:o + 2]:
                    problems.append(f"lava: tileset {ts:02X} linha {line} cor {i} diferente da do tileset 4 (cor das portas)")
        if (set(COLOURS[ts]) - {(ln, i) for ln in (PALETTE_LINE, BACKGROUND_LINE) for i in range(1, 16)}
                or any(len(c) != 6 for c in COLOURS[ts].values())):
            problems.append(f"lava: cores do tileset {ts:02X} mal formadas")
    fx = rom.read(VANILLA_LAVA_FX, 16)
    if fx != fx_entry(0x00B8, FX_HOT):
        problems.append(f"lava: FX vanilla ${VANILLA_LAVA_FX:06X} = {fx.hex()}, esperado {fx_entry(0x00B8, FX_HOT).hex()}")
    return problems

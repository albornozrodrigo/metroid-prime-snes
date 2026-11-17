"""Phazon Mines looks (specs/19d-estilos-da-mina.md; epic 19, decision 7 "padrão aceito, a confirmar": two looks, Tourian's music;
decision 6: the phazon is colour only, no damage).

Two looks, each on a tileset table entry no room the game loads uses (validate.check_mines_in_rom; their vanilla users are only
orphan rooms, specs/11, and no attract demo room), each a recoloured COPY of a vanilla palette, a painted copy of the source's
metatile table, and the source's vanilla graphics. Only the test build (tools/build.py --teste-19d) writes them until the Mines has
rooms (specs/19e on): the game's ROM keeps the vanilla entries (validate checks both).

  - BASE (the pirates' base: metal, pipes and screens; Elite Research, Elite Control, Omega Research, Central Dynamo, the
    quarantines, the elevator and save rooms): entry $0E (vanilla: the Mother Brain room's only, $DD58, an orphan), pointed at
    Tourian's ($0D) graphics and at a copy of $0D's metatile table (the one $0D/$0E share). Pieces = PIRATE_BASE, read from the
    vanilla Tourian rooms (the most common piece of each air neighbourhood: s19d/scripts/pieces.py): the glowing pipe border
    ($2EF floors/ceilings, $2EE walls, $316/$315 outer/inner corners: palette line 5) around a fill of plain panels ($169, line 6;
    Tourian's own fill is the CRE's black $044, which takes no recolour). Palette = $0D's with line 5 (the pipes) lit in phazon
    blue and line 6 (the panels) in dark steel (BASE_COLOURS). Background: $8F:E454 (Tourian's pipes and machinery, its tiles on
    lines 3 and 0: vanilla colours) with BG2 scroll $C1C1.
  - ROCK (the mine of rock and fungus: Main Quarry, Ore Processing, the tunnels, the Fungal Halls, the Phazon Mining Tunnel):
    entry $08 (vanilla: red Brinstar's twin of $07, used only by the orphan room $A5ED; the epic proposed $07 or $1A, but attract
    demo rooms use both: $A322/$A408/$A56B and $A59F), pointed at green Brinstar's ($06) graphics and at a copy of $06's metatile
    table. Pieces = MINE_ROCK, read from the vanilla green Brinstar rooms: the mossy rock (fill $16E, floor $16B, ceiling $196, walls
    $16F, top corners $16A/$16C, a 1-block pillar $173: all on palette line 4). Palette = $06's with line 4 in grey rock, the moss
    turned into blue phazon fungus (ROCK_COLOURS). Background: $8F:BAF4 (Brinstar's dark blue rock, every tile on line 2: vanilla
    colours) with BG2 scroll $C1C1.

The phazon: the blue of PHAZON, in the base's pipes (line 5) and the rock's fungus (line 4); no FX, no damage (decision 6). No room of
the Mines turns on a palette FX bit (area 5's list starts with the heat, $F761: specs/19b, check_mines_slot).

Doors (specs/10d, 12f, 17d, 18d, 18i): the purple wave door's 8 metatiles $3F0-$3F7 and the vertical one's 8 (VERT_PAINT_METATILES;
the Mines' map has two wave links on floor/ceiling walls, specs/19c) are vanilla filler in both source tables and get painted on
line PAINT_LINE = 7 (no piece of either look, neither background and no CRE metatile uses it). The green (ice) and orange (plasma)
caps use lines 0 and 1, colours 1-3 and the frame 4-7: the same colours as tileset 4's in both source palettes (checked). Music:
Tourian's song set $1E, track $05 (8 vanilla states of $0D): low and metallic, as the Mines' theme.
"""
from __future__ import annotations

import struct

from .compression import decompress
from .crateria import SOLID, sce_metatile_count, vanilla_types
from .gfx import CRE_TILE_TABLE, TILESET_TABLE
from .ice import _bgr555, piece_colours
from .rom import Rom, snes_to_pc
from .style import H, V, EdgeStyle

BASE_TILESET, BASE_SOURCE = 0x0E, 0x0D     # entry repointed / the tileset whose table, graphics and palette it copies
ROCK_TILESET, ROCK_SOURCE = 0x08, 0x06
TILESETS = (BASE_TILESET, ROCK_TILESET)
SOURCE = {BASE_TILESET: BASE_SOURCE, ROCK_TILESET: ROCK_SOURCE}
PAINT_LINE = 7                             # the purple wave door's line in both looks
PAINT_LINES = {BASE_TILESET: PAINT_LINE, ROCK_TILESET: PAINT_LINE}
OWN_LINES = {BASE_TILESET: (5, 6), ROCK_TILESET: (4,)}   # the lines each look recolours (its pieces' lines)

# the phazon's blue, light to dark (Prime's glowing blue phazon); used in both tables below
PHAZON = ("B8E8FF", "5C9CE8", "3A6CC0", "22407C", "101C3C")
# (palette line, colour) -> RGB hex, the only colour tables (decision to confirm with the user: change, rebuild).
#   BASE line 5 (vanilla: the white pipes, 4 A4A4A4, 5 737373, 6 414141, 7 202020, 14 FFFFFF; the pieces draw 4-7 and 14): the
#   pipes glow phazon blue; line 6 (vanilla khaki panels 1-8: E6E694 A4A46A 4A4A10 101000 BDBD83 949452 6A6A31 5A5A20; the fill
#   draws 1, 2, 5, 6): dark steel.
BASE_COLOURS = {(5, 14): PHAZON[0], (5, 4): PHAZON[1], (5, 5): PHAZON[2], (5, 6): PHAZON[3], (5, 7): PHAZON[4],
                **{(6, i): c for i, c in enumerate("485060 323844 1A1E26 0A0C10 3C4350 262B35 20242C 16191F".split(), 1)}}
#   ROCK line 4 (vanilla green Brinstar: the moss 4 396A39, 8 4AAC4A, 9 4A7B4A, 12 4AAC4A, 14 8BDE4A -> phazon fungus; the rock 3
#   003941, 5 084A5A, 6 002952, 7 000831, 10 105229, 11 000808, 13 102000 -> grey rock; the pieces draw 3-7, 9-12, 14)
ROCK_COLOURS = {(4, 14): PHAZON[0], (4, 8): "3C8CF0", (4, 12): "3C8CF0", (4, 9): PHAZON[2], (4, 4): PHAZON[3],
                (4, 3): "40444A", (4, 5): "5A5E66", (4, 6): "34383F", (4, 7): "1C1E24", (4, 10): "4A4E55", (4, 11): "0E0F12",
                (4, 13): "202226"}
COLOURS = {BASE_TILESET: BASE_COLOURS, ROCK_TILESET: ROCK_COLOURS}

PIRATE_BASE = EdgeStyle(
    name="base_pirata", tileset=BASE_TILESET,
    fill=(0x169,),
    floor=(0x2EF,), ceiling=(0x2EF | V,),
    wall_w=(0x2EE | H,), wall_e=(0x2EE,),
    platform=(0x2EF,), platform_l=0x2EF, platform_r=0x2EF,
    outer_nw=0x316 | H, outer_ne=0x316, outer_sw=0x316 | H | V, outer_se=0x316 | V,
    inner_nw=0x315, inner_ne=0x315 | H, inner_sw=0x315 | V, inner_se=0x315 | H | V,
    pillar=0x2EE,
)
MINE_ROCK = EdgeStyle(
    name="mina_de_rocha", tileset=ROCK_TILESET,
    fill=(0x16E,),
    floor=(0x16B,), ceiling=(0x196,),
    wall_w=(0x16F | H,), wall_e=(0x16F,),
    platform=(0x16B,),
    outer_nw=0x16A, outer_ne=0x16C,
    pillar=0x173,
)
STYLES = (PIRATE_BASE, MINE_ROCK)
STYLE_OF = {BASE_TILESET: PIRATE_BASE, ROCK_TILESET: MINE_ROCK}
# the vanilla rooms the pieces were read from (and are checked against): every Tourian room of $0D, green Brinstar rooms of $06
SOURCE_ROOMS = {
    PIRATE_BASE.name: (0xDAAE, 0xDAE1, 0xDB31, 0xDB7D, 0xDBCD, 0xDC19, 0xDC65, 0xDCB1, 0xDCFF, 0xDDC4, 0xDDF3, 0xDE4D, 0xDE7A,
                       0xDEA7, 0xDEDE),
    MINE_ROCK.name: (0x9AD9, 0x9B5B, 0x9B9D, 0x9BC8, 0x9C07, 0x9C5E, 0x9CB3, 0x9D19, 0x9D9C, 0x9DC7, 0x9E11, 0x9E52, 0x9E9F,
                     0x9F11, 0x9F64, 0x9FBA, 0x9FE5, 0xA011, 0xA051, 0xA0A4, 0xA0D2, 0xA107, 0xA130, 0xA15B, 0xA1AD, 0xA1D8),
}
# backgrounds (library background list, BG2 scroll) per look, and the palette lines their tilemaps draw with (read: check())
BACKGROUND = {BASE_TILESET: (0xE454, 0xC1C1), ROCK_TILESET: (0xBAF4, 0xC1C1)}
BACKGROUND_LINES = {BASE_TILESET: {0, 3}, ROCK_TILESET: {2}}
# music: Tourian's song set $1E, track $05 (decision 7 of the epic: the Tourian's; the 8 vanilla states of $0D that set a song)
MUSIC = (0x1E, 0x05)
VERT_FILLER = bytes.fromhex("ff03ff03ff03ff03")


def entry(rom: Rom, tileset: int) -> int:
    return 0x8F0000 | rom.u16(TILESET_TABLE + 2 * tileset)


def vanilla_palette(rom: Rom, tileset: int) -> bytes:
    return decompress(rom.data, snes_to_pc(rom.u24(entry(rom, tileset) + 6)))[0]


def vanilla_metatiles(rom: Rom, tileset: int) -> bytes:
    return decompress(rom.data, snes_to_pc(rom.u24(entry(rom, tileset))))[0]


def recolor(palette: bytes, tileset: int) -> bytes:
    """`palette` with the look's colours (COLOURS[tileset])."""
    out = bytearray(palette)
    for (line, i), c in COLOURS[tileset].items():
        out[2 * (line * 16 + i):2 * (line * 16 + i) + 2] = _bgr555(c).to_bytes(2, "little")
    return bytes(out)


def background_lines(rom: Rom, bg: int) -> set[int]:
    """Palette lines of the BG2 tilemap a library background list decompresses (its first command: $0004, decompress)."""
    if rom.u16(0x8F0000 | bg) != 0x0004:
        raise ValueError(f"fundo $8F:{bg:04X} não começa com o comando de descomprimir")
    tilemap = decompress(rom.data, snes_to_pc(rom.u24(0x8F0000 | bg + 2)))[0]
    return {(w >> 10) & 7 for w in struct.unpack_from(f"<{len(tilemap) // 2}H", tilemap)}


def check(rom: Rom) -> list[str]:
    """On the base ROM: the two entries are their own (no other tileset points at them); $0E shares $0D's metatiles and
    graphics; each style's pieces are in the source's table, solid most of the time in the source rooms, and on the lines the look
    recolours; the paint line is no look's, no CRE line, no background's; no CRE metatile draws a recoloured or the paint line; the
    wave doors' 16 metatiles are filler in both source tables; the door colours (lines 0 1-3, 1 1-7) are tileset 4's in both source
    palettes; the backgrounds' lines are BACKGROUND_LINES; the Tourian music is vanilla's; the colour tables are well formed."""
    from tallon.beamdoors import PAINT_METATILES, VERT_PAINT_METATILES
    problems = []
    words = [rom.u16(TILESET_TABLE + 2 * i) for i in range(0x1D)]
    for t in TILESETS:
        if words.count(words[t]) != 1:
            problems.append(f"mina: a entrada do tileset {t:02X} é dividida com outro")
    a, b = entry(rom, BASE_TILESET), entry(rom, BASE_SOURCE)
    if rom.u24(a) != rom.u24(b) or rom.u24(a + 3) != rom.u24(b + 3):
        problems.append(f"mina: tilesets {BASE_TILESET:02X} e {BASE_SOURCE:02X} não dividem metatiles e gráficos no vanilla")
    for style in STYLES:
        src = SOURCE[style.tileset]
        count = sce_metatile_count(rom, src)
        types = vanilla_types(rom, SOURCE_ROOMS[style.name], src)
        for word in sorted(style.solid_pieces()):
            mt = word & 0x3FF
            c = types.get(mt)
            if not 0x100 <= mt < 0x100 + count:
                problems.append(f"estilo {style.name}: metatile ${mt:03X} fora do tileset {src:02X}")
            elif not c or c.most_common(1)[0][0] != SOLID:
                problems.append(f"estilo {style.name}: metatile ${mt:03X} não é sólido nas salas de origem do tileset {src:02X}")
        if style.air_pieces():
            problems.append(f"estilo {style.name}: peças de ar {sorted(style.air_pieces())}")
        used = piece_colours(rom, src, style.solid_pieces())
        if set(used) - set(OWN_LINES[style.tileset]):
            problems.append(f"mina: peças do tileset {style.tileset:02X} nas linhas {sorted(used)}, o recolor pinta "
                            f"{OWN_LINES[style.tileset]}")
    cre_table = decompress(rom.data, snes_to_pc(CRE_TILE_TABLE))[0]
    cre_used = piece_colours(rom, 0, range(len(cre_table) // 8), cre=True)
    for t in TILESETS:
        bg_lines = background_lines(rom, BACKGROUND[t][0])
        if bg_lines != BACKGROUND_LINES[t]:
            problems.append(f"mina: fundo ${BACKGROUND[t][0]:04X} do tileset {t:02X} nas linhas {sorted(bg_lines)}")
        if PAINT_LINES[t] in OWN_LINES[t] or PAINT_LINES[t] in (0, 1, 2, 3) or PAINT_LINES[t] in bg_lines:
            problems.append(f"mina: a linha {PAINT_LINES[t]} da porta de onda do tileset {t:02X} é das peças, do fundo ou do CRE")
        if set(OWN_LINES[t]) & bg_lines:
            problems.append(f"mina: o fundo do tileset {t:02X} desenha nas linhas recoloridas {OWN_LINES[t]}")
        for line in OWN_LINES[t] + (PAINT_LINES[t],):
            if cre_used.get(line):
                problems.append(f"mina: metatiles do CRE desenham na linha {line}, que o tileset {t:02X} repinta")
        table = vanilla_metatiles(rom, SOURCE[t])
        for m in (*PAINT_METATILES.values(), *VERT_PAINT_METATILES.values()):
            if table[(m - 0x100) * 8:(m - 0x100) * 8 + 8] != VERT_FILLER:
                problems.append(f"mina: metatile ${m:03X} do tileset {SOURCE[t]:02X} não é enchimento (portas de onda)")
    ref = vanilla_palette(rom, 4)
    for src in (BASE_SOURCE, ROCK_SOURCE):
        pal = vanilla_palette(rom, src)
        for line, colours in ((0, range(1, 4)), (1, range(1, 8))):
            for i in colours:
                o = 2 * (line * 16 + i)
                if pal[o:o + 2] != ref[o:o + 2]:
                    problems.append(f"mina: tileset {src:02X} linha {line} cor {i} diferente da do tileset 4 (cor das portas)")
    for t, colours in COLOURS.items():
        if (set(colours) - {(ln, i) for ln in OWN_LINES[t] for i in range(1, 16)}
                or any(len(c) != 6 for c in colours.values())):
            problems.append(f"mina: cores do tileset {t:02X} mal formadas")
    from .room_reader import read_room
    music = {(st.music_data, st.music_track) for h in SOURCE_ROOMS[PIRATE_BASE.name]
             for st in read_room(rom, 0x8F0000 | h).states if st.tileset == BASE_SOURCE and st.music_data}
    if MUSIC not in music:
        problems.append(f"mina: música {MUSIC} não é a da Tourian vanilla ({sorted(music)})")
    return problems

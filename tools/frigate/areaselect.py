"""Area-select screen of the file-select map (continue after game over, or loading a save).

Vanilla shows "PLANET ZEBES" on top and "WRECKED SHIP" over area 3. Both are menu spritemaps
(specs/01-tela-de-continue.md):
  - pointer table of the 104 menu spritemaps at $82:C569 ($82 pointers); the title is spritemap
    $38 (`DrawAreaSelectMapLabels` $81:A97E loads it from $82:C749), area n's name is $38 + 1 + n;
  - spritemap = 16-bit piece count, then 5 bytes per piece: x (16 bits, 9 used), y (8 bits),
    attribute (16 bits = tile | palette << 9 | priority $3000);
  - tiles are the uncompressed menu sprite tiles at $B6:C000 (4bpp, 32 bytes each).
Big letters (8x16, the title's) are (top, bottom) tile pairs; there is no O, so one is made in the
two tiles no menu spritemap uses (15, all zero, and 23). Small letters (8x8): A-Z = tiles 106-131.
Here the title becomes "TALLON IV" (rewritten in place), area 3's name "FRIGATE / ORPHEON"
(new spritemap in $82 free space: 14 pieces don't fit in the vanilla 11) and, since spec 07f, area
0's "TALLON / OVERWORLD" (new spritemap after area 3's: 15 pieces, vanilla "CRATERIA" has 8).
The game draws an area's name only when one of its used load stations has a save icon
(`DrawAreaSelectMapLabels`), in the area order 0, 3, 5, 1, 4, 2.
"""
from __future__ import annotations

import struct

from smlib.rom import Rom

OBJ_TILES = 0xB6C000
MENU_SPRITEMAPS = 0x82C569
TITLE_ID_PTR = 0x82C749        # word read by DrawAreaSelectMapLabels: the title's spritemap id
TITLE_ID = 0x38
AREA3_LABEL_ID = 0x3C
TITLE_PTR, TITLE_COUNT = 0xCBFB, 22
AREA3_LABEL_PTR, AREA3_LABEL_COUNT = 0xCD2E, 11
PRIORITY = 0x3000
O_TOP, O_BOTTOM = 15, 23
SMALL_A = 106
TITLE = "TALLON IV"
AREA3_LABEL = ("FRIGATE", "ORPHEON")
TITLE_XY = (0x80, 0x10)        # screen position of the title (LDX/LDY in $81:A97E)
AREA3_LABEL_XY = (0xCE, 0x50)  # area 3 in the label position table at $81:AA1C
AREA0_LABEL_ID = 0x39
AREA0_LABEL_PTR, AREA0_LABEL_COUNT = 0xCC6B, 8   # vanilla "CRATERIA"
AREA0_LABEL = ("TALLON", "OVERWORLD")
AREA0_LABEL_XY = (0x5B, 0x32)  # area 0 in the label position table at $81:AA1C
# specs/12i: area 1's name (vanilla "BRINSTAR", 8 pieces) becomes "CHOZO / RUINS" (Save Station 1: a save in the Chozo);
# its spot on the planet picture stays vanilla's
AREA1_LABEL_ID = 0x3A
AREA1_LABEL_PTR, AREA1_LABEL_COUNT = 0xCC95, 8   # vanilla "BRINSTAR"
AREA1_LABEL = ("CHOZO", "RUINS")
AREA1_LABEL_XY = (0x2A, 0x7F)  # area 1 in the label position table at $81:AA1C
# specs/17e: area 2's name (vanilla "NORFAIR", 7 pieces) becomes "MAGMOOR / CAVERNS" (drawn once a save of the Magmoor's has its
# station used: its save stations come with region A, 17f); its spot on the planet picture stays vanilla's
AREA2_LABEL_ID = 0x3B
AREA2_LABEL_PTR, AREA2_LABEL_COUNT = 0xCCBF, 7   # vanilla "NORFAIR"
AREA2_LABEL = ("MAGMOOR", "CAVERNS")
AREA2_LABEL_XY = (0x5E, 0xB5)  # area 2 in the label position table at $81:AA1C
# specs/18e: area 4's name (vanilla "MARIDIA", 7 pieces) becomes "PHENDRANA / DRIFTS" (drawn once a save of Phendrana's has its
# station used: its save stations come with region A, 18f); its spot on the planet picture stays vanilla's
AREA4_LABEL_ID = 0x3D
AREA4_LABEL_PTR, AREA4_LABEL_COUNT = 0xCD09, 7   # vanilla "MARIDIA"
AREA4_LABEL = ("PHENDRANA", "DRIFTS")
AREA4_LABEL_XY = (0xCE, 0x9F)  # area 4 in the label position table at $81:AA1C
# specs/19e: area 5's name (vanilla "TOURIAN", 7 pieces) becomes "PHAZON / MINES" (drawn once a save of the Mines' has its station
# used: its save stations come with region A, 19f); its spot on the planet picture stays vanilla's
AREA5_LABEL_ID = 0x3E
AREA5_LABEL_PTR, AREA5_LABEL_COUNT = 0xCCE4, 7   # vanilla "TOURIAN"
AREA5_LABEL = ("PHAZON", "MINES")
AREA5_LABEL_XY = (0x87, 0x8B)  # area 5 in the label position table at $81:AA1C
# area: (spritemap id, vanilla pointer, vanilla piece count, lines, screen position), in the order
# the build allocates them (area 3 first: its address is the one spec 01 measured)
LABELS = {3: (AREA3_LABEL_ID, AREA3_LABEL_PTR, AREA3_LABEL_COUNT, AREA3_LABEL, AREA3_LABEL_XY),
          0: (AREA0_LABEL_ID, AREA0_LABEL_PTR, AREA0_LABEL_COUNT, AREA0_LABEL, AREA0_LABEL_XY),
          1: (AREA1_LABEL_ID, AREA1_LABEL_PTR, AREA1_LABEL_COUNT, AREA1_LABEL, AREA1_LABEL_XY),
          2: (AREA2_LABEL_ID, AREA2_LABEL_PTR, AREA2_LABEL_COUNT, AREA2_LABEL, AREA2_LABEL_XY),
          4: (AREA4_LABEL_ID, AREA4_LABEL_PTR, AREA4_LABEL_COUNT, AREA4_LABEL, AREA4_LABEL_XY),
          5: (AREA5_LABEL_ID, AREA5_LABEL_PTR, AREA5_LABEL_COUNT, AREA5_LABEL, AREA5_LABEL_XY)}

# big letters: (top tile, bottom tile), checked by drawing each pair
BIG = {
    "A": (10, 26), "B": (11, 27), "C": (12, 28), "D": (13, 29), "E": (14, 30), "F": (14, 31),
    "G": (12, 48), "H": (33, 49), "I": (34, 17), "J": (35, 51), "K": (36, 52), "L": (37, 53),
    "M": (38, 54), "N": (39, 55), "O": (O_TOP, O_BOTTOM), "P": (13, 56), "R": (13, 58),
    "S": (43, 59), "T": (44, 17), "U": (45, 28), "V": (45, 62), "W": (47, 63), "X": (64, 80),
    "Y": (65, 17), "Z": (66, 82),
}

O_TOP_VANILLA = bytes(32)
O_BOTTOM_VANILLA = bytes.fromhex("0618041804180418041804180c0000001e1e1c1c1c1c1c1c1c1c1c1c0c0c0000")
O_TOP_BYTES = bytes.fromhex("00000000003c18661166116611661166000000003c3c7e7e7777777777777777")
O_BOTTOM_BYTES = bytes.fromhex("11661166116611661166033c1e000000777777777777777777773f3f1e1e0000")


def tile(rom: Rom, n: int) -> bytes:
    return rom.read(OBJ_TILES + 32 * n, 32)


def splice(base: bytes, other: bytes, rows: range, cols: range) -> bytes:
    """`base` with the pixels at (rows, cols) taken from `other` (4bpp: bitplanes 0/1 in bytes
    2*row, 2*row+1; bitplanes 2/3 in 16+2*row, 17+2*row; column 0 = MSB)."""
    out = bytearray(base)
    mask = sum(0x80 >> c for c in cols)
    for r in rows:
        for i in (2 * r, 2 * r + 1, 16 + 2 * r, 17 + 2 * r):
            out[i] = (out[i] & ~mask & 0xFF) | (other[i] & mask)
    return bytes(out)


def o_tiles(rom: Rom) -> tuple[bytes, bytes]:
    """Big O: the C's rounded left side with the D's straight right side (columns 5-7)."""
    top = splice(tile(rom, BIG["C"][0]), tile(rom, BIG["D"][0]), range(4, 8), range(5, 8))
    bottom = splice(tile(rom, BIG["C"][1]), tile(rom, BIG["D"][1]), range(0, 3), range(5, 8))
    return top, bottom


def piece(x: int, y: int, t: int) -> bytes:
    return struct.pack("<HbH", x & 0x1FF, y, PRIORITY | t)


def title_pieces(text: str) -> list[tuple[int, int, int]]:
    """(x, y, tile) per half letter: top (y -8) then bottom (y 0); 8 px per letter or space."""
    out = []
    for i, c in enumerate(text):
        if c != " ":
            x = -36 + 8 * i
            out += [(x, -8, BIG[c][0]), (x, 0, BIG[c][1])]
    return out


def label_pieces(lines: tuple[str, ...]) -> list[tuple[int, int, int]]:
    """Small letters, each line centred (odd widths lean left); 8 px per letter, 6 before an I
    and 7 after one (as the vanilla names)."""
    out = []
    for row, line in enumerate(lines):
        advances = [6 if nxt == "I" else 7 if c == "I" else 8 for c, nxt in zip(line, line[1:])]
        x = -(sum(advances) + 8) // 2
        for c, adv in zip(line, advances + [0]):
            out.append((x, -8 + 8 * row, SMALL_A + ord(c) - ord("A")))
            x += adv
    return out


def spritemap(pieces: list[tuple[int, int, int]]) -> bytes:
    return struct.pack("<H", len(pieces)) + b"".join(piece(*p) for p in pieces)


def title_spritemap(text: str) -> bytes:
    return spritemap(title_pieces(text))


def label_spritemap(lines: tuple[str, ...]) -> bytes:
    return spritemap(label_pieces(lines))


def oam_entries(area: int = 3) -> list[tuple[int, int, int]]:
    """(x, y, tile) on screen of the sprites the area-select screen draws first for a save in
    `area`, in OAM order: the title, then that area's name (the first name drawn when no area
    before it in the game's order 0, 3, ... has a used station: true for area 3 in the frigate
    and for area 0 always)."""
    _, _, _, lines, xy = LABELS[area]
    out = []
    for (bx, by), pieces in ((TITLE_XY, title_pieces(TITLE)), (xy, label_pieces(lines))):
        out += [((bx + x) & 0x1FF, (by + y) & 0xFF, t) for x, y, t in pieces]
    return out


FREE_82 = (0xF70F, 0xFFFF)     # $82 free space (research/sm_room_format.md section 10)


def read_spritemap(rom: Rom, sid: int) -> tuple[int, list[tuple[int, int, int]]]:
    """($82 address, [(x, y, tile)]) of menu spritemap `sid`."""
    ptr = rom.u16(MENU_SPRITEMAPS + 2 * sid)
    count = rom.u16(0x820000 | ptr)
    pieces = []
    for i in range(count):
        x, y, attr = struct.unpack("<HbH", rom.read(0x820000 | ptr + 2 + 5 * i, 5))
        pieces.append((x, y, attr & 0x1FF))
    return ptr, pieces


def check_rom(rom: Rom) -> list[str]:
    """Problems with the area-select texts in a built ROM (tools/validate.py)."""
    problems = []
    ptr, pieces = read_spritemap(rom, TITLE_ID)
    if ptr != TITLE_PTR or len(pieces) != len(title_pieces(TITLE)):
        problems.append(f"tela de área: título em ${ptr:04X} com {len(pieces)} peças "
                        f"(esperado ${TITLE_PTR:04X} com {len(title_pieces(TITLE))})")
    tops, bottoms = {t for t, _ in BIG.values()}, {b for _, b in BIG.values()}
    for x, y, t in pieces:
        if t not in (tops if y < 0 else bottoms):
            problems.append(f"tela de área: tile {t} no título não é letra grande")
    for area, (sid, _, _, lines, _) in LABELS.items():
        ptr, pieces = read_spritemap(rom, sid)
        if not FREE_82[0] <= ptr <= FREE_82[1] or pieces != [(x & 0x1FF, y, t) for x, y, t in label_pieces(lines)]:
            problems.append(f"tela de área: nome da área {area} em ${ptr:04X} com {len(pieces)} peças "
                            f"(esperado {'/'.join(lines)!r} em $82:{FREE_82[0]:04X}-{FREE_82[1]:04X} "
                            f"com {len(label_pieces(lines))})")
        for x, y, t in pieces:
            if not SMALL_A <= t < SMALL_A + 26:
                problems.append(f"tela de área: tile {t} no nome da área {area} não é letra pequena")
    for n, want in ((O_TOP, O_TOP_BYTES), (O_BOTTOM, O_BOTTOM_BYTES)):
        if tile(rom, n) != want:
            problems.append(f"tela de área: tile {n} (letra O) diferente do esperado")
    return problems


def apply(rom: Rom, bank82) -> None:
    def check(addr: int, old: bytes, what: str) -> None:
        if rom.read(addr, len(old)) != old:
            raise RuntimeError(f"bytes inesperados em ${addr:06X} ({what})")

    check(TITLE_ID_PTR, struct.pack("<H", TITLE_ID), "número da spritemap do título")
    check(MENU_SPRITEMAPS + 2 * TITLE_ID, struct.pack("<H", TITLE_PTR), "ponteiro do título")
    check(0x820000 | TITLE_PTR, struct.pack("<H", TITLE_COUNT), "contagem do título")
    for area, (sid, ptr, count, _, _) in LABELS.items():
        check(MENU_SPRITEMAPS + 2 * sid, struct.pack("<H", ptr), f"ponteiro do nome da área {area}")
        check(0x820000 | ptr, struct.pack("<H", count), f"contagem do nome da área {area}")
    check(OBJ_TILES + 32 * O_TOP, O_TOP_VANILLA, "tile 15")
    check(OBJ_TILES + 32 * O_BOTTOM, O_BOTTOM_VANILLA, "tile 23")

    top, bottom = o_tiles(rom)
    if (top, bottom) != (O_TOP_BYTES, O_BOTTOM_BYTES):
        raise RuntimeError("letra O gerada diferente da esperada (tiles do C/D mudaram?)")
    rom.write(OBJ_TILES + 32 * O_TOP, top)
    rom.write(OBJ_TILES + 32 * O_BOTTOM, bottom)

    title = title_spritemap(TITLE)
    if len(title) > 2 + 5 * TITLE_COUNT:
        raise RuntimeError(f"título {TITLE!r} não cabe nas {TITLE_COUNT} peças vanilla")
    rom.write(0x820000 | TITLE_PTR, title)
    names = []
    for area, (sid, _, _, lines, _) in LABELS.items():
        label = bank82.put(label_spritemap(lines))
        rom.w16(MENU_SPRITEMAPS + 2 * sid, label & 0xFFFF)
        names.append(f"nome da área {area} {'/'.join(lines)!r} em ${label:06X}")
    print(f"  tela de área: título {TITLE!r} em ${0x820000 | TITLE_PTR:06X}, " + ", ".join(names))

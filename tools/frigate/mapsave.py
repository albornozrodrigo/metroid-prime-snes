"""Layout of the explored map in the save (SRAM), single source for build.py and validate.py.

Saving packs the explored map (C `PackMapToSave` $81:834B / `UnpackMapFromSave` $81:82E4): for
areas 0-5 only the bytes listed per area are copied from the area's 0x100-byte explored mask into
the buffer at $7ED91C. Tables in $81 (research/sm_room_format.md section 12):
  - count (bytes) per area at $81:8131; 16-bit loop counter, so 0 would mean 65536 (valid 1-255);
  - start in the buffer (words) at $81:8138;
  - $81 pointers to the byte-offset lists at $81:82D6.
The buffer runs $7ED91C-$7EDE1B (0x500 = 1280 bytes) and is saved and loaded whole; vanilla uses
the first 327, the other 953 are free.

Rule for remade areas (frigate = 3, Tallon Overworld = 0, Chozo Ruins = 1, Magmoor Caverns = 2; specs/18b, the plan of
areas.py: Phendrana Drifts = 4 (its list fits the vanilla place, 80 bytes), Phazon Mines = 5 (its list moves to $81, below),
the Impact Crater inside area 0 with the Tallon):
  - the list of an area is generated from its map-station reveal mask (`needed`), never by hand;
  - each mask byte covers 8 tiles of one row, so the count is the number of (row, group of 8
    columns) pairs with some room in them. At most 255 per area;
  - every remade area gets its own block after the 327 vanilla bytes, in build order (`layout`:
    the order of the dict, = tools/areas.py AREAS), so a new area never moves the blocks of the
    areas built before it (specs/07f: frigate +327, Tallon +357); no other area loses bytes. All
    remade areas together fit in 953 bytes;
  - the list stays in the vanilla place while it fits (`LIST_ROOM`): area 0 up to 80 bytes
    ($81:8146-$81:8195), area 5 up to 21. Past that (specs/19b, `list_at`): area 5's list (the
    Phazon Mines', ~45 bytes) goes to the start of the $81 free space (`FREE_81`, $81:EF1A-$81:FEFF,
    4070 bytes of $FF) and $81:82D6+2*5 points at it (PackMapToSave/UnpackMapFromSave read the list
    through that pointer, in bank $81: RomPtr_81); for the other areas the build stops.
"""
from __future__ import annotations

COUNTS = 0x818131
PACKED_OFFS = 0x818138
LISTS = 0x8182D6
VANILLA_COUNTS = (74, 72, 76, 18, 66, 21)
VANILLA_PACKED = (0, 74, 146, 222, 240, 306)
VANILLA_LIST_PTRS = (0x8146, 0x8196, 0x81E6, 0x8236, 0x8256, 0x82A6)
LIST_ROOM = (80, 80, 80, 32, 80, 21)   # bytes free for each list in its vanilla place
PACKED_SIZE = 0x500
VANILLA_END = 327
MAX_COUNT = 255
# specs/19b: the $81 free space (all $FF in the base ROM, validate.check_mines_slot) and the areas whose list goes there when it
# doesn't fit its vanilla place: only area 5's (one list, so it starts at FREE_81[0])
FREE_81 = (0x81EF1A, 0x81FEFF)
MOVES_TO_81 = (5,)


def list_room(area: int) -> int:
    """specs/19b: the most bytes `area`'s list may have: its vanilla place's (LIST_ROOM), or MAX_COUNT if it may move to $81."""
    return MAX_COUNT if area in MOVES_TO_81 else LIST_ROOM[area]


def list_at(area: int, size: int) -> int:
    """specs/19b: where `area`'s list of `size` bytes goes: its vanilla place ($81:VANILLA_LIST_PTRS[area]) while it fits
    (LIST_ROOM); past that, for an area of MOVES_TO_81, the start of FREE_81 (the pointer at LISTS + 2 * area then points there).
    ValueError for a list that fits neither."""
    if size <= LIST_ROOM[area]:
        return 0x810000 | VANILLA_LIST_PTRS[area]
    if area in MOVES_TO_81 and size <= min(MAX_COUNT, FREE_81[1] - FREE_81[0] + 1):
        return FREE_81[0]
    raise ValueError(f"área {area}: lista de {size} bytes não cabe no lugar vanilla ({LIST_ROOM[area]})"
                     + ("" if area in MOVES_TO_81 else " e a área não vai para o espaço livre de $81"))


def needed(mask: bytes) -> list[int]:
    """Offsets of the non-zero bytes of an area's reveal mask: the bytes the save must keep."""
    return [i for i, b in enumerate(mask) if b]


def layout(custom: dict[int, list[int]]) -> dict[int, int]:
    """Start in the save buffer of each remade area: blocks after the vanilla bytes, in the dict's
    order (build order)."""
    starts, at = {}, VANILLA_END
    for area in custom:
        starts[area] = at
        at += len(custom[area])
    return starts


def check(custom: dict[int, list[int]]) -> list[str]:
    problems = []
    for area, offs in sorted(custom.items()):
        if not 0 <= area <= 5:
            problems.append(f"área {area}: só as áreas 0-5 têm mapa salvo")
        if not 1 <= len(offs) <= MAX_COUNT:
            problems.append(f"área {area}: mapa usa {len(offs)} bytes; a SRAM aceita 1-{MAX_COUNT}")
    total = VANILLA_END + sum(len(o) for o in custom.values())
    if total > PACKED_SIZE:
        problems.append(f"mapas salvos somam {total} bytes; o save tem {PACKED_SIZE}")
    return problems

"""The room graph read from ROM bytes (specs/11-limpeza.md): which rooms the game can load.

A room is loaded by a door entry ($83) and nothing else: load stations ($80:C4B5) and attract-mode
demos ($82:876C) both name a door, and `LoadDoorHeader` loads the door's destination
(research/sm_room_format.md section 9). From a loaded room the game goes on through the door-out list
($8F, header +9), indexed by the BTS of the door blocks (type 9) Samus touches: the slots a room really
uses are the BTS (& $7F) of its type-9 blocks in the level data of any of its states.

Used by tools/validate.py (`check_orphans`, the vanilla door/item bits). Vanilla SM, crawled from every
load station and demo: 262 rooms (research/sm_rooms.json has 250: no Ceres, debug room nor 5 others).
"""
from __future__ import annotations

import struct

from .compression import decompress
from .rom import Rom, snes_to_pc
from .room_reader import DEFAULT_STATE, ELEVATOR_FLAGS_OFF, OUR_CONDITION_SIZE, STATE_COND_ARGS, our_condition, read_room

LOAD_STATIONS = 0x80C4B5          # 8 word pointers (one per area) into bank $80
STATION_SIZE = 14
STATION_COUNTS = (19, 19, 23, 18, 20, 18, 17, 17)   # entries per area (gaps between the tables)
DEMO_TABLE = 0x82876C             # kDemoRoomData: 4 word pointers to the demo sets ($82)
DEMO_SETS = 4                     # VerifySRAM ($80:8261): 3, or 4 when SRAM says "supermetroid"
DEMO_SCENE_SIZE = 18              # room, door, door slot, screen x/y, Samus x/y, length, code; $FFFF ends a set
SAVE_PLM = 0xB76F                 # argument & 7 = the area's load station
DOOR_BLOCK = 0x9


def door_slots(rom: Rom, header: int) -> set[int]:
    """Door-out list slots used by the door blocks of room `header` ($8F address), in any state."""
    slots = set()
    for st in read_room(rom, 0x8F0000 | header).states:
        raw, _ = decompress(rom.data, snes_to_pc(st.level_data))
        size = raw[0] | raw[1] << 8
        n = size // 2
        layer1 = struct.unpack_from(f"<{n}H", raw, 2)
        bts = raw[2 + size:2 + size + n]
        slots |= {bts[i] & 0x7F for i in range(n) if layer1[i] >> 12 == DOOR_BLOCK}
    return slots


def room_doors(rom: Rom, header: int) -> list[int]:
    """Door entries ($83, 16-bit) of the room's door-out list, up to the last slot its door blocks use."""
    slots = door_slots(rom, header)
    if not slots:
        return []
    door_list = 0x8F0000 | rom.u16(0x8F0000 | header + 9)
    return [rom.u16(door_list + 2 * i) for i in range(max(slots) + 1)]


def door_target(rom: Rom, door: int) -> int | None:
    """Destination room of door entry `door`, or None when it is no door ($8000 bit clear)."""
    if not door & 0x8000:
        return None
    dest = rom.u16(0x830000 | door)
    return dest if dest & 0x8000 else None


def station(rom: Rom, area: int, index: int) -> tuple[int, int]:
    """(room, door) words of load station `index` of `area`."""
    at = (0x800000 | rom.u16(LOAD_STATIONS + 2 * area)) + STATION_SIZE * index
    return rom.u16(at), rom.u16(at + 2)


def demo_scenes(rom: Rom) -> list[tuple[int, int, int, int]]:
    """(set, scene, room, door) of every attract-mode demo."""
    out = []
    for s in range(DEMO_SETS):
        base = 0x820000 | rom.u16(DEMO_TABLE + 2 * s)
        k = 0
        while rom.u16(base + DEMO_SCENE_SIZE * k) != 0xFFFF:
            at = base + DEMO_SCENE_SIZE * k
            out.append((s, k, rom.u16(at), rom.u16(at + 2)))
            k += 1
    return out


def walk(rom: Rom, starts: dict[int, str], expand=lambda room: True) -> dict[int, str]:
    """Rooms reached through doors from `starts` ({room: how}); {room: how it was reached}. Rooms for which
    `expand(room)` is false are reached but not gone through."""
    reached, stack = dict(starts), list(starts)
    while stack:
        h = stack.pop()
        if not expand(h):
            continue
        for slot, door in enumerate(room_doors(rom, h)):
            dest = door_target(rom, door)
            if dest is not None and dest not in reached:
                reached[dest] = f"{reached[h]} → ${h:04X} porta {slot} (${door:04X})"
                stack.append(dest)
    return reached


def vanilla_rooms(rom: Rom) -> set[int]:
    """Every room of the (base) ROM: from every load station of every area and every demo, through
    doors."""
    starts = {}
    for area, count in enumerate(STATION_COUNTS):
        for i in range(count):
            _, door = station(rom, area, i)
            dest = door_target(rom, door)
            if dest is not None:
                starts[dest] = f"estação {area}/{i:#x}"
    for s, k, _, door in demo_scenes(rom):
        dest = door_target(rom, door)
        if dest is not None:
            starts.setdefault(dest, f"demo {s}/{k}")
    return set(walk(rom, starts))


def save_stations(rom: Rom, header: int) -> set[int]:
    """Load stations the save PLMs of room `header` save to (any state)."""
    out = set()
    for st in read_room(rom, 0x8F0000 | header).states:
        p = 0x8F0000 | st.plm if st.plm else None
        while p and rom.u16(p):
            if rom.u16(p) == SAVE_PLM:
                out.add(rom.u16(p + 4) & 7)
            p += 6
    return out


# ---- the bank-locked bytes a room uses ($8F, $83, $A1, $B4), for space accounting ----

BG_ARGS = {0x0000: 0, 0x0002: 7, 0x0004: 5, 0x0006: 0, 0x0008: 7, 0x000A: 0, 0x000C: 0, 0x000E: 9}


def fx_size(rom: Rom, fx: int) -> int:
    """Bytes of the FX list at $83:fx: 16-byte entries up to the default ($0000) one, or a $FFFF word."""
    n = 0
    while True:
        w = rom.u16(0x830000 | fx + 16 * n)
        if w == 0xFFFF:
            return 16 * n + 2
        n += 1
        if w == 0:
            return 16 * n


def population_size(rom: Rom, pop: int) -> int:
    """Bytes of the enemy population at $A1:pop (16-byte entries, $FFFF and the kill count)."""
    n = 0
    while rom.u16(0xA10000 | pop + 16 * n) != 0xFFFF:
        n += 1
    return 16 * n + 3


def enemy_set_size(rom: Rom, eset: int) -> int:
    """Bytes of the enemy set at $B4:eset (4-byte entries and $FFFF; the 7-byte name before it not
    counted)."""
    n = 0
    while rom.u16(0xB40000 | eset + 4 * n) != 0xFFFF:
        n += 1
    return 4 * n + 2


def bg_size(rom: Rom, bg: int) -> int:
    """Bytes of the library-background command list at $8F:bg."""
    k = 0
    while True:
        op = rom.u16(0x8F0000 | bg + k)
        k += 2
        if op == 0:
            return k
        if op not in BG_ARGS:
            raise ValueError(f"comando de fundo ${op:04X} desconhecido em $8F:{bg + k - 2:04X}")
        k += BG_ARGS[op]


def structures(rom: Rom, header: int) -> list[tuple[int, int, str]]:
    """(address, size, kind) of the bank-locked data of room `header`: header and states, scroll,
    PLM, scroll-PLM, x-ray and background lists, door-out list and door entries, FX, enemy population
    and set (with its 7-byte name). Code (setup, main and door ASM) is not counted; specs/20e: a state condition of ours
    (room_reader.other_area_boss_condition) and the main ASM room_reader.ELEVATOR_FLAGS_OFF are."""
    room = read_room(rom, 0x8F0000 | header)
    out = []
    p = 0x8F0000 | header + 11
    while rom.u16(p) != DEFAULT_STATE:
        p += 2 + STATE_COND_ARGS.get(rom.u16(p), 0) + 2
    out.append((0x8F0000 | header, p + 2 + 26 - (0x8F0000 | header), "cabeçalho"))
    for st in room.states:
        if st.condition != DEFAULT_STATE:
            out.append((st.addr, 26, "estado"))
        if st.condition not in STATE_COND_ARGS and st.condition != DEFAULT_STATE and our_condition(rom, st.condition):
            out.append((0x8F0000 | st.condition, OUR_CONDITION_SIZE, "condição"))   # specs/20e: our code, in our space
        if st.main_asm and rom.read(0x8F0000 | st.main_asm, len(ELEVATOR_FLAGS_OFF)) == ELEVATOR_FLAGS_OFF:
            out.append((0x8F0000 | st.main_asm, len(ELEVATOR_FLAGS_OFF), "código"))   # specs/20e: likewise
        if st.scroll >= 0x8000:
            out.append((0x8F0000 | st.scroll, room.width * room.height, "scroll"))
        if st.plm:
            q, n = 0x8F0000 | st.plm, 0
            while rom.u16(q + 6 * n):
                if rom.u16(q + 6 * n) in (0xB703, 0xB707):   # scroll PLM: {screen, value} pairs, ended by bit 7
                    r, k = 0x8F0000 | rom.u16(q + 6 * n + 4), 0
                    while not rom.u8(r + k) & 0x80:
                        k += 2
                    out.append((r, k + 1, "scroll de PLM"))
                n += 1
            out.append((q, 6 * n + 2, "PLMs"))
        if st.xray:
            q, n = 0x8F0000 | st.xray, 0
            while rom.u16(q + 4 * n):
                n += 1
            out.append((q, 4 * n + 2, "raio X"))
        if st.bg_data & 0x8000:
            out.append((0x8F0000 | st.bg_data, bg_size(rom, st.bg_data), "fundo"))
        if st.fx:
            out.append((0x830000 | st.fx, fx_size(rom, st.fx), "FX"))
        if st.enemy_pop:
            out.append((0xA10000 | st.enemy_pop, population_size(rom, st.enemy_pop), "inimigos"))
        if st.enemy_set:
            out.append(((0xB40000 | st.enemy_set) - 7, 7 + enemy_set_size(rom, st.enemy_set), "set de inimigos"))
    doors = room_doors(rom, header)
    if doors:
        out.append((0x8F0000 | room.door_list, 2 * len(doors), "lista de portas"))
    out += [(0x830000 | d, 12, "porta") for d in doors if d & 0x8000]
    return out


def byte_set(structs: list[tuple[int, int, str]]) -> set[int]:
    return {a for addr, size, _ in structs for a in range(addr, addr + size)}

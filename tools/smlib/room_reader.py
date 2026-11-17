"""Read existing Super Metroid rooms (header, states, level data) from the ROM."""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

from .compression import decompress
from .rom import Rom, snes_to_pc

# State condition function -> number of argument bytes before the 2-byte state pointer.
# $E5E6 is the default state: its state data follows inline and ends the list.
STATE_COND_ARGS = {0xE612: 1, 0xE629: 1, 0xE5EB: 2}
DEFAULT_STATE = 0xE5E6
STATE_SIZE = 26


def other_area_boss_condition(area: int, mask: int) -> bytes:
    """specs/20e: a state condition of ours (tools/build.py puts it in $8F), no argument byte: the state is taken when the boss
    bits of `area` ($7ED828 + area) have `mask` (the SM's $E629 reads the current area's only). Run by the state check ($8F:E5D2)
    with X past the condition word, as the vanilla $E5FF: LDA $7ED828+area / AND #mask / BEQ +7 / LDA $0000,X / TAX / JMP $E5E6
    (use that state) / INX / INX / RTS (the next condition)."""
    return bytes([0xAF, 0x28 + area, 0xD8, 0x7E, 0x29, mask, 0x00, 0xF0, 0x07, 0xBD, 0x00, 0x00, 0xAA, 0x4C, 0xE6, 0xE5, 0xE8,
                  0xE8, 0x60])


OUR_CONDITION_SIZE = len(other_area_boss_condition(0, 1))
# specs/20e: a room main ASM of ours (JSR'd every frame, DB = $8F: $0E16 is WRAM's): STZ $0E16 / RTS. Standing on an elevator
# platform's door blocks sets elevator_flags ($0E16); in a vanilla elevator room the platform's AI clears them, so a room state
# with the blocks but without the platform (the Artifact Temple before the Omega Pirate dies) clears them itself: left on, the
# next door brought Samus into its room as off an elevator, frozen in a fall (measured in the emulator)
ELEVATOR_FLAGS_OFF = bytes.fromhex("9c160e60")


def our_condition(rom: Rom, cond: int) -> tuple[int, int] | None:
    """(area, mask) if the state condition at $8F:cond is other_area_boss_condition's code, else None."""
    code = rom.read(0x8F0000 | cond, OUR_CONDITION_SIZE)
    area, mask = code[1] - 0x28, code[5]
    return (area, mask) if 0 <= area < 8 and code == other_area_boss_condition(area, mask) else None


@dataclass
class RoomState:
    addr: int            # SNES address of the 26-byte state data
    condition: int
    level_data: int
    tileset: int
    music_data: int
    music_track: int
    fx: int
    enemy_pop: int
    enemy_set: int
    layer2_scroll: int
    scroll: int
    xray: int
    main_asm: int
    plm: int
    bg_data: int
    setup_asm: int


@dataclass
class RoomHeader:
    addr: int
    index: int
    area: int
    map_x: int
    map_y: int
    width: int   # in screens
    height: int
    up_scroller: int
    down_scroller: int
    cre_bitset: int
    door_list: int
    states: list[RoomState] = field(default_factory=list)

    @property
    def default_state(self) -> RoomState:
        return self.states[-1]


def parse_state(rom: Rom, addr: int, condition: int) -> RoomState:
    raw = rom.read(addr, STATE_SIZE)
    level = raw[0] | (raw[1] << 8) | (raw[2] << 16)
    (tileset, music_data, music_track) = raw[3], raw[4], raw[5]
    fx, enemy_pop, enemy_set, l2scroll, scroll, xray, main_asm, plm, bg, setup = struct.unpack_from("<HHHHHHHHHH", raw, 6)
    return RoomState(addr, condition, level, tileset, music_data, music_track, fx, enemy_pop, enemy_set,
                     l2scroll, scroll, xray, main_asm, plm, bg, setup)


def read_room(rom: Rom, addr: int) -> RoomHeader:
    h = rom.read(addr, 11)
    room = RoomHeader(addr, h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7], h[8], h[9] | (h[10] << 8))
    p = addr + 11
    while True:
        cond = rom.u16(p)
        if cond == DEFAULT_STATE:
            room.states.append(parse_state(rom, p + 2, cond))
            break
        if cond not in STATE_COND_ARGS and cond < 0xE5E6 and our_condition(rom, cond) is None:
            raise ValueError(f"condição de estado desconhecida ${cond:04X} na sala ${addr:06X}")
        nargs = STATE_COND_ARGS.get(cond, 0)
        state_ptr = rom.u16(p + 2 + nargs)
        room.states.append(parse_state(rom, 0x8F0000 | state_ptr, cond))
        p += 2 + nargs + 2
    return room


def read_level_data(rom: Rom, state: RoomState) -> tuple[list[int], bytes, list[int] | None]:
    """Return (layer1 block words, BTS bytes, layer2 block words or None)."""
    raw, _ = decompress(rom.data, snes_to_pc(state.level_data))
    size = raw[0] | (raw[1] << 8)
    blocks = size // 2
    layer1 = list(struct.unpack_from(f"<{blocks}H", raw, 2))
    bts = raw[2 + size:2 + size + blocks]
    layer2 = None
    if len(raw) >= 2 + size + blocks + size:
        layer2 = list(struct.unpack_from(f"<{blocks}H", raw, 2 + size + blocks))
    return layer1, bytes(bts), layer2

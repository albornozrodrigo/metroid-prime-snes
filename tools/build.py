"""Build the Metroid Prime SNES demake ROM from base/sm_fix.sfc.

Usage: python3 -I tools/build.py            -> build/metroid_prime_snes.sfc + .ips

Layout decisions (see research/sm_room_format.md for every address used here):
  - Room headers, state headers, door-out lists, scroll data: bank $8F free space ($8F:E9AF+).
  - Door entries: bank $83 free space ($83:AD66+).
  - Expanded banks (specs/09c): room level data only in $E0:8000-$EF:FFFF (LEVEL_BANKS, grows
    freely, a level may cross a bank); graphics, palettes and DMA sources in $F0:8000-$FF:FFFF
    (FIXED_BANKS, each in one bank), so level growth never moves them.
  - The game starts at area 3 (Wrecked Ship slot = Frigate), load station 0, which we repoint
    to the Exterior Docking Hangar. Intro and Ceres are skipped by a patch at $82:EED9.
  - Rooms, load stations and pause maps come per area from tools/areas.py (AREAS, in build order).
"""
from __future__ import annotations

import json
import struct
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from areas import (AREAS, CHOZO, ESCAPE_ARRIVAL_STATION, FRIGATE, MAGMOOR, MAGMOOR_AREA, MINES, MINES_AREA,  # noqa: E402
                   IMPACT_CRATER_AREA, PHENDRANA_AREA, START_AREA, PHENDRANA, TALLON, AreaDef, all_rooms, elevator_target)
from frigate import areaselect, bosses, ending, mapsave, pausemap, queen_art, space, timer, title  # noqa: E402
from frigate.enemies import Spawn, enemy_set, population  # noqa: E402
from frigate.props import BACKDROPS  # noqa: E402
from frigate.rooms import RoomDef  # noqa: E402
from tallon import beamdoors, items as tallon_items  # noqa: E402
from chozo import items as chozo_items  # noqa: E402
from magmoor import items as magmoor_items  # noqa: E402
from phendrana import items as phendrana_items  # noqa: E402
from mines import items as mines_items  # noqa: E402
from impact import ending as impact_ending, rooms as impact_rooms, style as impact_style  # noqa: E402
from chozo import bosses as chozo_bosses, heat, testrooms  # noqa: E402
from smlib.compression import compress, decompress  # noqa: E402
from smlib import ice, itemtouch, lava, mines, ruins  # noqa: E402
from smlib.palette import recolor  # noqa: E402
from smlib.rom import Rom, pc_to_snes, snes_to_pc  # noqa: E402
from smlib.room_reader import ELEVATOR_FLAGS_OFF, other_area_boss_condition  # noqa: E402

BASE = ROOT / "base/sm_fix.sfc"
OUT = ROOT / "build/metroid_prime_snes.sfc"
FLIPS = ROOT / "vendor/Flips/flips"

# Water over the whole room (specs/07l, the sunken frigate): the FX entry of the vanilla flooded Wrecked
# Ship room $8F:CD5C ($83:9B64: type 6 water, layer blend $02/$18, liquid options 3, no palette FX nor
# animated tiles of an area list, palette blend $48) with the surface at y $10, the value of the
# flooded Maridia rooms ($83:9D64 ...): Samus is under water everywhere in the room.
WATER_FX = bytes.fromhex("0000" "1000" "FFFF" "0000" "00" "06" "02" "18" "03" "00" "00" "48")
WATER_SURFACE_Y = 0x0010

EMPTY_ENEMY_POP = 0x85D8      # $A1:85D8 = FF FF 00 (vanilla)
EMPTY_ENEMY_SET = 0x8129      # $B4:8129 = FF FF (vanilla, after "SF1_05 ")

# Frigate-only rooms (the toolchain is per area, these set pieces are the frigate's).
# Parasite Queen = Phantoon. Fight state copied from the vanilla Phantoon room ($8F:CD13).
BOSS_ROOM = FRIGATE.boss_room
HANGAR_ROOM = "hangar"         # starfield background (tools/frigate/space.py)
RIDLEY_ROOM = "airlock"       # Meta Ridley flies off here during the escape (tools/frigate/ending.py)
PHANTOON_MUSIC = (0x27, 0x06)
PHANTOON_FX = 0x9C44
PHANTOON_ENEMY_POP = 0xCCD4   # $A1: Phantoon and its 3 helper parts, centred in a 1x1 room
PHANTOON_ENEMY_SET = 0x8D1D   # $B4: Phantoon
PHANTOON_LAYER2 = 0x0101
PHANTOON_BG = 0xE0FD          # clears BG2, where Phantoon's body is drawn
COND_BOSS_BITS = 0xE629       # state condition: boss_bits[area] & mask
ESCAPE_MINUTES = 5            # BCD minutes on the escape timer

# $82:848E in GameState_36_WhitingOutFromTimeUp ($82:8431)
TIME_UP_CHECK = 0x82848E
TIME_UP_VANILLA = bytes([0xA9, 0x0E, 0x00, 0x22, 0x33, 0x82, 0x80, 0x90, 0x18])  # LDA #$0E; JSL CheckEvent; BCC ceres
TIME_UP_PATCH = bytes([0xAD, 0x9F, 0x07, 0xC9, 0x06, 0x00, 0xEA, 0xF0, 0x18])    # LDA $079F; CMP #6; NOP; BEQ ceres

LOAD_STATION_TABLE = 0x80C4B5
LOAD_STATION_SIZE = 14
SPAWN_STATION = 0          # new game: station 0 of START_AREA (the frigate's hangar)
SAVE_PLM = 0xB76F          # argument = this area's load-station index (AreaDef.load_stations)
MAP_STATION_PLM = 0xB6D3
MAP_STATION_ARG = 0x8000
# specs/19l: the SM's missile refill station (PlmSetup_PlmB6EB, sm_84.c: the block solid, its neighbours the access blocks; the
# vanilla rooms put it on row 10 over the floor on row 12); its argument is not read (vanilla rooms give it any number)
MISSILE_STATION_PLM = 0xB6EB
MISSILE_STATION_ARG = 0x8000

# Pause map tables in $82 (research/sm_room_format.md section 12), indexed by area
PAUSE_TILEMAPS = 0x82964A      # 24-bit pointers to the 64x32 tilemaps
PAUSE_MAP_REVEAL = 0x829717    # $82 pointers to the 0x100-byte map-station reveal masks
PAUSE_AREA_LABELS = 0x82965F   # $82 pointers to 12-tile area names
MAP_ICONS = 0x82C7CB           # 0x10 bytes (8 areas) per icon kind
ICONS_BOSS, ICONS_MAP_STATION, ICONS_SAVE, ICONS_ELEVATOR = 0x00, 0x30, 0x40, 0x50
MAP_ELEVATOR_LABELS = 0x82C74D  # $82 pointers to "to <area>" labels drawn on the map


def _xy(x: int, y: int) -> bytes:
    return struct.pack("<HH", x, y)


# What each remade area's pause tables hold in vanilla, checked before writing over them in place:
# tilemap and reveal-mask addresses, and the icon / elevator-label lists (map pixels, FFFF ends).
VANILLA_PAUSE = {
    3: {"tilemap": 0xB5B000, "reveal": 0x829A27,              # Wrecked Ship
        "boss": _xy(0x98, 0xA0) + b"\xFF\xFF",                 # Phantoon's room
        "map_station": _xy(0x68, 0xA0) + b"\xFF\xFF",          # WS map room
        "save": _xy(0x88, 0x78) + _xy(0xFFFE, 0xFFFE),
        "elevators": _xy(0x40, 0x80)},
    0: {"tilemap": 0xB59000, "reveal": 0x829727,              # Crateria (specs/07f)
        "map_station": _xy(0xB8, 0x40) + b"\xFF\xFF",          # Crateria map room
        "save": _xy(0xD8, 0x28) + _xy(0x90, 0x38) + _xy(0xFFFE, 0xFFFE) * 6,
        # elevator icons = save-list entries 8-15 (drawn by the elevator bits)
        "elevator_icons": (_xy(0x1A0, 0x58) + _xy(0x110, 0x40) + _xy(0xB8, 0x90) + _xy(0x30, 0x48)
                           + _xy(0x88, 0x50) + _xy(0xFFFE, 0xFFFE) * 3),
        "elevators": bytes.fromhex("300070005a00b800b8005a00100168005a00780120005c00a00180005d00")},
    1: {"tilemap": 0xB58000, "reveal": 0x829827,              # Brinstar: the Chozo Ruins' slot (specs/12b)
        "boss": _xy(0x1BC, 0x9C) + b"\xFF\xFF",
        "map_station": _xy(0x28, 0x28) + b"\xFF\xFF",
        "save": (_xy(0x78, 0x28) + _xy(0x40, 0x30) + _xy(0x28, 0x60) + _xy(0x188, 0x98) + _xy(0x130, 0x48)
                 + _xy(0xFFFE, 0xFFFE) * 3),
        "elevator_icons": (_xy(0x48, 0x18) + _xy(0xD0, 0x58) + _xy(0x128, 0x38) + _xy(0x148, 0x98)
                           + _xy(0xFFFE, 0xFFFE) * 4),
        "elevators": bytes.fromhex("480008005900d00040005900280120005900400190005d004801c0005b00")},
    2: {"tilemap": 0xB5A000, "reveal": 0x829927,              # Norfair: the Magmoor Caverns' slot (specs/17b)
        "boss": _xy(0xB8, 0x90) + b"\xFF\xFF",
        "map_station": _xy(0x48, 0x28) + b"\xFF\xFF",
        "save": (_xy(0x60, 0x60) + _xy(0xA8, 0x20) + _xy(0x58, 0x30) + _xy(0x80, 0x48) + _xy(0xA0, 0x58) + _xy(0x120, 0x68)
                 + _xy(0xFFFE, 0xFFFE) * 2),
        "elevator_icons": _xy(0x50, 0x18) + _xy(0xA8, 0x58) + _xy(0xA8, 0x70) + _xy(0xFFFE, 0xFFFE) * 5,
        "elevators": bytes.fromhex("500008005a00")},   # one "to <area>" label ($82:C799, FFFF at $C79F)
    4: {"tilemap": 0xB5C000, "reveal": 0x829B27,              # Maridia: the Phendrana Drifts' slot (specs/18b)
        "boss": _xy(0x13C, 0x54) + b"\xFF\xFF",
        "map_station": _xy(0x88, 0x90) + b"\xFF\xFF",
        "save": _xy(0x60, 0xA0) + _xy(0x118, 0x28) + _xy(0x98, 0x60) + _xy(0x148, 0x38) + _xy(0xFFFE, 0xFFFE) * 4,
        "elevator_icons": _xy(0x110, 0x18) + _xy(0xFFFE, 0xFFFE) * 7,
        "elevators": bytes.fromhex("0801080059003000a0005a007800a0005a00")},   # three labels ($82:C7AF, FFFF at $C7C1)
    # specs/19b: Tourian, the Phazon Mines' slot. No boss icon list (its pointer is 0: DrawBossMapIcons skips it); the map station
    # list is empty ($82:CA4F = FFFF, 2 bytes: vanilla Tourian has no map station; the Mines' needs a list of its own, 19e)
    5: {"tilemap": 0xB5D000, "reveal": 0x829C27,
        "map_station": b"\xFF\xFF",
        "save": _xy(0x80, 0x90) + _xy(0xA8, 0x68) + _xy(0xFFFE, 0xFFFE) * 6,
        "elevator_icons": _xy(0xA0, 0x60) + _xy(0xFFFE, 0xFFFE) * 7,
        "elevators": bytes.fromhex("980048005900")},   # one "to <area>" label ($82:C7C3, FFFF at $C7C9)
}
# Area 0 only: the pause map ($82:B6BC) and the continue's room map ($82:B777) always draw the
# ship icon (menu spritemap $63) at area 0's save-icon entry 0, read at fixed $82:C853/$82:C855
# (LDA $079F; BNE; ...; LDA $C855; ...; LDA $C853; ...; LDA #$0063; JSL $81891F)
SHIP_ICON_SITES = (0x82B6BC, 0x82B777)
SHIP_ICON_CODE = bytes.fromhex("ad9f07d01aa9000e8503ad55c838e5b3a8ad53c838e5b1aaa96300221f8981")
SAVE_SLOTS = 8   # load stations 0-7 are the save slots (and save-icon entries)
DEBUG_AREA = 7   # specs/19b: the debug area (its one room is an orphan, specs/11); shares area 5's reveal-mask pointer

ESCAPE_STATION_SITE = 0x828035   # InitAndLoadGameData, loading state $22: LDA #$0012 (STA $078B)
NEW_GAME_PATCH_SITE = 0x82EED9
NEW_GAME_ROUTINE = 0x82F70F


# Vanilla free space of the banks a room's data must live in (research/sm_room_format.md section 10):
# everything of ours goes after these starts, everything before them is vanilla (specs/11: the
# validator's check_orphans tells our pointers from the vanilla ones we share on purpose by them).
FREE_8F = (0x8FE9AF, 0x8FFFFF)   # room headers, states, door-out lists, PLM lists, backgrounds, room code
FREE_83 = (0x83AD66, 0x83FFFF)   # door entries, FX
FREE_A1 = (0xA1EBD1, 0xA1FFFF)   # enemy populations
FREE_B4 = (0xB4F4B8, 0xB4FFFF)   # enemy sets

# specs/12a: $8F bytes given back from vanilla rooms nothing loads (specs/11 "órfãs"), used once FREE_8F is
# full. The validator (check_reclaimed) proves on the base ROM's bytes that every byte here belongs only to
# orphan rooms (not to a demo room, not to VANILLA_SHARED, no code) and that only our rooms' data is written
# here. $8F:D4EF-DDBD = headers, states, scrolls and door lists of 38 orphan Maridia/Tourian rooms, minus
# $8F:DD58, the Mother Brain room's header: vanilla code compares the room pointer with it (ROOM_PTR_COMPARED),
# so no header of ours may start there; leaving that one byte out of both ranges is enough.
# specs/17a: two more, at the end (first fit in order: nothing that fits the ranges before moves), only orphan Norfair (area 2)
# rooms' data, no demo room's, no compared header: $8F:8ED6-9193 = the PLM lists of 15 rooms ($B40A-$B741); $8F:A9E5-AD41 = the
# headers, states, door lists and scrolls of 18 rooms ($A9E5-$AD1B).
# specs/18a: one more, at the end again: $8F:8000-8ED3 (3796 bytes) = the scrolls and PLM lists of 149 orphan rooms of areas 0-2,
# no header, none compared; 716 of its bytes belong to 17 attract-demo rooms (DEMO_SCENES), which nothing loads while the demos stay
# off (specs/16, title.check_demos_off: validate.check_reclaimed accepts demo rooms' bytes only with it passing).
# specs/19a (the Phazon Mines): four more, at the end again (nothing that fits the ranges before moves): $8F:C215-C8C6 (1714) and
# $8F:AD5C-B218 (1213), with attract-demo rooms' data (only while the demos stay off, as 18a), $8F:A6A1-A97A (730) and $8F:CAAE-CCC7
# (538): only orphan rooms' structures, no header vanilla code compares (validate.check_reclaimed).
RECLAIMED_8F = ((0x8FD4EF, 0x8FDD57), (0x8FDD59, 0x8FDDBD), (0x8F8ED6, 0x8F9193), (0x8FA9E5, 0x8FAD41), (0x8F8000, 0x8F8ED3),
                (0x8FC215, 0x8FC8C6), (0x8FAD5C, 0x8FB218), (0x8FA6A1, 0x8FA97A), (0x8FCAAE, 0x8FCCC7))
# specs/19a: $A1 bytes given back the same way, used once FREE_A1 is full (first fit after it): $A1:AD09-CCD3 (8139) = enemy
# populations of orphan vanilla rooms only (validate.check_reclaimed; no vanilla code reads $A1 but through a room state's pointer:
# SpawnEnemy takes its entries from the caller's bank, no 0xA1xxxx constant in vendor/sm/src).
RECLAIMED_A1 = ((0xA1AD09, 0xA1CCD3),)
# Room headers vanilla code tells apart by address (LDA $079B; CMP #imm), read from the bytes: $88:81CC ($CEFB),
# $88:8200 ($A66A), $88:82CA (earthquake rooms: $9804 $96BA $B32E $B457 $DD58 $DEDE), $91:D143 ($A66A $CEFB).
# A header of ours at one of these would get that room's special effect (validate.check_reclaimed).
ROOM_PTR_COMPARED = (0x96BA, 0x9804, 0xA66A, 0xB32E, 0xB457, 0xCEFB, 0xDD58, 0xDEDE)


def ours_8f(addr: int) -> bool:
    """Whether a $8F address (16 or 24 bits) is in space the build allocates from (FREE_8F, RECLAIMED_8F)."""
    a = 0x8F0000 | addr & 0xFFFF
    return any(lo <= a <= hi for lo, hi in (FREE_8F, *RECLAIMED_8F))


def ours_a1(addr: int) -> bool:
    """specs/19a: whether an $A1 address (16 or 24 bits) is in space the build allocates populations from (FREE_A1, RECLAIMED_A1)."""
    a = 0xA10000 | addr & 0xFFFF
    return any(lo <= a <= hi for lo, hi in (FREE_A1, *RECLAIMED_A1))


class Allocator:
    """Bump allocator inside one bank's free range ($FF bytes from `start` to `end`). `reclaimed` (specs/12a):
    more (start, end) ranges of the same bank given back from orphan vanilla data; a payload that doesn't fit
    in the free range goes to the first of them where it fits (first fit, in order). Their bytes are not $FF:
    the allocator checks that nothing of the build wrote there before (the bytes it saw when it was made)."""

    def __init__(self, rom: Rom, start: int, end: int, name: str, reclaimed: tuple[tuple[int, int], ...] = ()):
        self.rom, self.ptr, self.end, self.name = rom, start, end, name
        for lo, hi in reclaimed:
            if lo >> 16 != start >> 16 or hi >> 16 != start >> 16 or hi < lo:
                raise RuntimeError(f"faixa recuperada ${lo:06X}-${hi:06X} fora do banco {name}")
        self.reclaimed = [(lo, hi, rom.read(lo, hi - lo + 1)) for lo, hi in reclaimed]
        self.reclaimed_ptr = [lo for lo, _ in reclaimed]

    def put(self, payload: bytes) -> int:
        addr = self.ptr
        # specs/12j: full addresses (the low 16 bits wrapped to 0 once the range was filled to its last byte, $xx:FFFF,
        # and the next payload was put in the next bank)
        if addr + len(payload) - 1 <= self.end:
            current = self.rom.read(addr, len(payload))
            if current != b"\xFF" * len(payload):
                raise RuntimeError(f"espaço em ${addr:06X} não está livre")
            self.rom.write(addr, payload)
            self.ptr += len(payload)
            return addr
        for i, (lo, hi, seen) in enumerate(self.reclaimed):
            addr = self.reclaimed_ptr[i]
            if addr + len(payload) - 1 > hi:
                continue
            if self.rom.read(addr, len(payload)) != seen[addr - lo:addr - lo + len(payload)]:
                raise RuntimeError(f"espaço recuperado em ${addr:06X} ({self.name}) já foi escrito")
            self.rom.write(addr, payload)
            self.reclaimed_ptr[i] += len(payload)
            return addr
        raise RuntimeError(f"sem espaço livre no banco {self.name}")

    def next_at(self, size: int) -> int:
        """specs/18h: where put() would write a payload of `size` bytes (nothing written): for data whose inner pointers
        depend on its own address (a conditional room header) once the free range is full and it goes to a reclaimed one."""
        if self.ptr + size - 1 <= self.end:
            return self.ptr
        for i, (lo, hi, _) in enumerate(self.reclaimed):
            if self.reclaimed_ptr[i] + size - 1 <= hi:
                return self.reclaimed_ptr[i]
        raise RuntimeError(f"sem espaço livre no banco {self.name}")

    def reclaimed_used(self) -> list[tuple[int, int, int]]:
        """(start, end, bytes used) of each reclaimed range."""
        return [(lo, hi, p - lo) for (lo, hi, _), p in zip(self.reclaimed, self.reclaimed_ptr)]


# The expanded banks (specs/09c). The base ROM is 3 MB (banks $80-$DF); the build makes it 4 MB
# (Rom.expand_to), which its header already declares ($80:FFD7 = $0C), and LoROM maps $80-$FF:8000-FFFF,
# so $E0:8000-$FF:FFFF (file $300000-$3FFFFF) is ours. Two allocators that never share a byte:
ROM_SIZE = 0x400000
LEVEL_BANKS = (0xE08000, 0xEFFFFF)   # room level data only; a level may cross a bank: the decompressor
                                     # ($80:B119/$80:B271) moves to the next bank after $xx:FFFF ($80:B266)
FIXED_BANKS = (0xF08000, 0xFFFFFF)   # graphics, palettes, DMA sources: each blob in one bank (DMA wraps
                                     # inside its bank), never moved by the level data growing


class ExpandedAllocator:
    """Bump allocator over the upper halves of consecutive LoROM banks start..end (contiguous in the
    file). With `cross_banks` a payload may run on from $xx:FFFF into the next bank; without it a payload
    that would cross starts at the next bank. Writes only over $FF bytes; `blobs` = (label, address, size)."""

    def __init__(self, rom: Rom, banks: tuple[int, int], name: str, cross_banks: bool):
        self.rom, self.name, self.cross_banks = rom, name, cross_banks
        self.start, self.end = banks
        self.pc, self.end_pc = snes_to_pc(self.start), snes_to_pc(self.end) + 1
        self.blobs: list[tuple[str, int, int]] = []

    def put(self, payload: bytes, label: str) -> int:
        if not self.cross_banks and self.pc // 0x8000 != (self.pc + len(payload) - 1) // 0x8000:
            self.pc = (self.pc // 0x8000 + 1) * 0x8000
        start = self.pc
        if start + len(payload) > self.end_pc:
            raise RuntimeError(f"sem espaço livre no alocador {self.name} para {label} ({len(payload)} bytes)")
        if self.rom.data[start:start + len(payload)] != b"\xFF" * len(payload):
            raise RuntimeError(f"espaço em ${pc_to_snes(start):06X} ({self.name}) não está livre")
        self.rom.data[start:start + len(payload)] = payload
        self.pc += len(payload)
        addr = pc_to_snes(start)
        self.blobs.append((label, addr, len(payload)))
        return addr

    def skip(self, n: int) -> None:
        """Leave n bytes empty ($FF): the bank-crossing test build (--cruzar-banco)."""
        if self.pc + n > self.end_pc:
            raise RuntimeError(f"enchimento de {n} bytes passa do fim do alocador {self.name}")
        self.pc += n

    def free(self) -> int:
        return self.end_pc - self.pc

    def info(self) -> dict:
        return {"start": self.start, "end": self.end, "next": pc_to_snes(self.pc) if self.free() else None,
                "free": self.free(), "blobs": self.blobs}


def crossing_pad(order: list[tuple[str, int]], room_key: str, start_pc: int) -> int:
    """Bytes to skip at the start of the level allocator so that `room_key`'s level (sizes in build
    `order`) starts half its size before the next bank boundary and runs across it."""
    offset = 0
    for key, size in order:
        if key == room_key:
            at = start_pc + offset
            boundary = ((at + size // 2) // 0x8000 + 1) * 0x8000
            return boundary - size // 2 - at
        offset += size
    raise RuntimeError(f"--cruzar-banco: sala {room_key!r} não existe")


def crossings(blobs: list[tuple[str, int, int]]) -> list[tuple[str, int, int]]:
    """The blobs that run across a bank boundary."""
    return [(k, a, n) for k, a, n in blobs if (a & 0xFFFF) + n - 1 > 0xFFFF]


@dataclass
class Placed:
    area: AreaDef
    room: RoomDef
    header: int = 0
    door_entries: list[int] = None
    states: list[int] = None     # addresses of the 26-byte state headers
    elevator_entries: list[int] = None   # specs/12e: the elevator's exit and platform door entries


def state_bytes(level_ptr: int, area: AreaDef, room: RoomDef, *, music=None, fx=None,
                enemy_pop=EMPTY_ENEMY_POP, enemy_set_ptr=EMPTY_ENEMY_SET, layer2=None, main_asm=0x0000,
                bg=None, bg_lists: dict[bytes, int] | None = None) -> bytes:
    """26-byte state header; music defaults to the area's, FX to the room's, BG2 scroll and
    background to the room's or else the area's."""
    music = area.music if music is None else music
    fx = room.fx if fx is None else fx
    layer2 = (area.layer2 if room.layer2 is None else room.layer2) if layer2 is None else layer2
    bg = (area.library_bg if room.library_bg is None else room.library_bg) if bg is None else bg
    if isinstance(bg, bytes):
        bg = bg_lists[bg]   # a list of our own, already in $8F
    state = struct.pack(
        "<BHBBBHHHHHHHHHH",
        level_ptr & 0xFF, (level_ptr >> 8) & 0xFFFF, area.tileset_of(room), music[0], music[1],
        fx, enemy_pop, enemy_set_ptr, layer2,
        0x0001,              # scroll: every screen green
        0x0000,              # special x-ray
        main_asm,
        0x0000,              # PLM population, filled in later
        bg,
        0x0000,              # setup ASM
    )
    assert len(state) == 26, len(state)
    return state


def escape_timer_routine(area: int) -> bytes:
    """Room main ASM for the boss fight ($8F, JSR'd every frame with DB=$8F). Once the area boss
    bit is set and no timer runs yet, start the escape timer the way Mother Brain's death does
    (SM $A9:B258-$A9:B2F9) with our own duration:
      - queue the timer digit tiles into the VRAM write queue ($D0 + tail at $0330);
      - timer RAM like ClearTimerRam/SetTimerMinutes ($80:9E93/$80:9E8C);
      - status $8003 (slide into place, then count down);
      - Samus code $0F: run the timer every frame (and game over at 00:00)."""
    queue = timer.queue_timer_tiles()
    start_timer = bytes([
        0xA9, 0x00, 0x80,                   # LDA #$8000
        0x8D, 0x48, 0x09,                   # STA $0948 (timer x)
        0x8D, 0x4A, 0x09,                   # STA $094A (timer y)
        0x9C, 0x45, 0x09,                   # STZ $0945 (centiseconds, seconds)
        0xA9, 0x00, ESCAPE_MINUTES,         # LDA #$MM00
        0x8D, 0x46, 0x09,                   # STA $0946 (seconds, minutes)
        0xA9, 0x03, 0x80,                   # LDA #$8003
        0x8D, 0x43, 0x09,                   # STA $0943 (timer status)
        0xA9, 0x0F, 0x00,                   # LDA #$000F
        0x22, 0x84, 0xF0, 0x90,             # JSL $90F084 (Samus code: enable timer handling)
    ])
    body = bytes(queue) + start_timer
    check_timer = bytes([0xAD, 0x43, 0x09, 0xD0, len(body)])                    # LDA $0943; BNE done
    head = bytes([
        0x08,                               # PHP
        0xC2, 0x30,                         # REP #$30
        0xAF, *struct.pack("<I", BOSS_BITS + area)[:3],   # LDA $7ED828+area (this area's boss bits)
        0x29, 0x01, 0x00,                   # AND #$0001
        0xF0, len(check_timer) + len(body), # BEQ done
    ])
    code = head + check_timer + body + bytes([0x28, 0x60])                      # done: PLP; RTS
    assert len(check_timer) + len(body) < 0x80
    return code


BOSS_BITS = 0x7ED828   # boss bits, one byte per area

# Door ASM ($8F, JSR'd during the transition): Samus made it to the ship, stop the timer.
STOP_TIMER_ROUTINE = bytes([0x08, 0xC2, 0x30, 0x9C, 0x43, 0x09, 0x28, 0x60])  # PHP; REP #$30; STZ $0943; PLP; RTS


# specs/12e: the working elevators (RoomDef.elevator, tools/areas.py ELEVATORS), as the vanilla ones read from the bytes
# ($8F:9938 <-> $9AD9, $962A, $97B5, $94CC, $A6A1: research in specs/12e):
#  - the platform = enemy $A0:D73F (no tiles of its own: no enemy-set entry, as $9938's set is empty), properties $2C00,
#    parameter 1 = the key that starts it (0 down, 1 up: Elevator_Func_1, $A3:9548), parameter 2 = the y where it shows up
#    when Samus arrives riding it (elevator_status 2, Elevator_Init $A3:94E6), from where it goes to its own y: off the
#    room's bottom by 64 px for a down elevator (vanilla $0140 in a 1-screen room), $0018 for an up one;
#    its own y = the platform blocks' row * 16 + 2 (vanilla 162 on row 10, 706 on row 44), x = the blocks' shared edge;
#  - the platform's door blocks use a door entry with no room ($0000): solid, and Samus standing on them sets
#    elevator_flags (BlockColl_Vert_Door $94:93CE); ELEVATOR_PAD_DOOR is a copy of the vanilla one, $83:88FC, in our $83;
#  - the exit's door entry: flags $C0 = elevator ($80, LoadDoorHeader $82:DE12) + area change ($40: the explored map is
#    saved and the other area's loaded, $82:DF99/$82:DFB6), orientation 2 down / 3 up, no push (0), the camera on the
#    screen of the other room's platform. The low nibble (an "elevator used" map icon, $80:CD07) stays 0: no icon.
ELEVATOR_SPECIES = 0xD73F
ELEVATOR_PROPERTIES = 0x2C00
ELEVATOR_UP_ARRIVAL_Y = 0x0018
ELEVATOR_DOWN_ARRIVAL_BELOW = 64
ELEVATOR_PAD_DOOR_VANILLA = 0x8388FC
ELEVATOR_PAD_DOOR = bytes.fromhex("0000f8910003000004000080")
ELEVATOR_DOOR_FLAGS = 0xC0
# specs/20e: an elevator inside one area (the Artifact Temple's teleporter down to the crater, both in area 0): flags $80 only,
# elevator without area change, as vanilla's Norfair <-> Lower Norfair one (area 2: $8F:AF3F <-> $B236, flags $A0/$B0, read from
# the bytes; the low nibble is the map's "elevator used" icon, 0 here, and $20 is left out as $C0 leaves it)
ELEVATOR_SAME_AREA_FLAGS = 0x80


def teleporter_condition() -> bytes:
    """specs/20e: the Artifact Temple's state condition ($8F code, smlib/room_reader.py other_area_boss_condition): the bit of the
    arena impact_rooms.OPENS_AFTER (the Omega Pirate's: $10) in its area's boss bits (the Mines', area 5)."""
    return other_area_boss_condition(MINES_AREA, chozo_bosses.arena_of(impact_rooms.OPENS_AFTER).bit)


def teleporter_header(header: bytes, at: int, cond: int, on: bytes, off: bytes) -> tuple[bytes, list[int]]:
    """specs/20e: the Artifact Temple's room header: `on` (with the elevator's platform) when the condition at $8F:cond holds (the
    Omega Pirate dead), else `off` (the default, no platform: the pad does nothing). Returns the bytes and the state addresses,
    default first (as conditional_header)."""
    default_at = at + len(header) + 4 + 2
    on_at = default_at + 26
    return header + struct.pack("<HH", cond & 0xFFFF, on_at & 0xFFFF) + b"\xE6\xE5" + off + on, [default_at, on_at]


def elevator_spawn(room: RoomDef) -> bytes:
    """The $A1 population entry of a room's elevator platform."""
    e = room.elevator
    y = e.row * 16 + 2
    arrival = ELEVATOR_UP_ARRIVAL_Y if e.up else room.height * 256 + ELEVATOR_DOWN_ARRIVAL_BELOW
    return struct.pack("<8H", ELEVATOR_SPECIES, (e.x + 1) * 16, y, 0, ELEVATOR_PROPERTIES, 0, 1 if e.up else 0, arrival)


def room_population(spawns: list[Spawn], room: RoomDef) -> bytes:
    """The room's enemy population ($A1): tools/frigate/enemies.py population, with the elevator platform first (specs/12e;
    the kill count stays the enemies')."""
    pop = population(spawns)
    return (elevator_spawn(room) + pop) if room.elevator else pop


def item_arena_door(key: str, d) -> bool:
    """specs/14d: door `d` of room `key` is an ITEM arena's boss door: blue (no PLM) until the fight starts, when the arena
    routine spawns its grey cap."""
    arena = chozo_bosses.arena_of(key)
    return d.lock == "boss" and arena is not None and arena.condition == chozo_bosses.ITEM


def arena_door_alive_cap(key: str, d) -> int | None:
    """specs/18h, 18k: the grey cap's argument of door `d` of room `key` if it is a boss door whose cap changes with the arena's
    state (the alive state's list: the grey cap, closed from the room's load until the fight is won; the dead state's: its
    dead_lock cap or none), None if not. A KILLS arena's: type 3 (the kill count, 18h); 18k: a BOSS_BIT arena waiting for the
    Torizo's bit: type 2 (the vanilla Torizo door, $84:BDF2, opens on the bit its death sets)."""
    arena = chozo_bosses.arena_of(key)
    if d.lock != "boss" or arena is None:
        return None
    if arena.condition == chozo_bosses.KILLS:
        return chozo_bosses.GREY_DOOR_KILLS
    if arena.condition == chozo_bosses.BOSS_BIT and arena.arg == chozo_bosses.TORIZO_BIT:
        return chozo_bosses.GREY_DOOR_TORIZO
    return None


def item_arena_population(spawns: list[Spawn], room: RoomDef) -> bytes:
    """specs/14d: an ITEM arena's alive population: the room's enemies but its boss kinds (the arena routine spawns those
    when the fight starts) and the quota 0 (the routine's "not started"; it sets the real one, chozo/bosses.py)."""
    pop = room_population([e for e in spawns if not e.species.boss], room)
    if pop[-3:-1] != b"\xFF\xFF" or room.elevator:
        raise RuntimeError(f"{room.key}: população da arena de item inesperada")
    if pop[:2] == b"\xFF\xFF":   # EnemyMain runs only when the population had one ($A0:8FD4: first_free_enemy_index)
        raise RuntimeError(f"{room.key}: arena de item sem nenhum inimigo antes da luta (o motor não processaria os gerados)")
    return pop[:-1] + b"\x00"


def elevator_exit_entry(room: RoomDef, target_header: int, target: RoomDef, same_area: bool = False) -> bytes:
    """Door entry ($83) of a room's elevator exit: to `target` (the other room of the pair), whose platform is where the
    camera starts. specs/20e: `same_area` (both rooms in one SM area): no area change (ELEVATOR_SAME_AREA_FLAGS)."""
    if not target.elevator or target.elevator.up == room.elevator.up:
        raise RuntimeError(f"{room.key} -> {target.key}: o par de elevadores precisa de um que desce e outro que sobe")
    e = target.elevator
    flags = ELEVATOR_SAME_AREA_FLAGS if same_area else ELEVATOR_DOOR_FLAGS
    return struct.pack("<HBBBBBBHH", target_header & 0xFFFF, flags, TRAVEL_DIR["T" if room.elevator.up else "B"],
                       0, 0, (e.x + 1) // 16, e.row // 16, 0x0000, 0x0000)


def ruins_palette(rom) -> bytes:
    """specs/12d/12f: tileset $0C's palette as the build writes it: line 7 = ruins.SANDSTONE, line 6 (the background's) =
    ruins.SANDSTONE_BACKGROUND, line beamdoors.RUINS_PAINT_LINE = the purple wave door's (from `rom`'s vanilla palette);
    specs/12g2: line beamdoors.CHARGE_LINE = the white charge door's."""
    purple = beamdoors.paint_palette(ruins.recolor_background(ruins.recolor(ruins.vanilla_palette(rom))),
                                     beamdoors.RUINS_PAINT_LINE)
    return beamdoors.paint_palette(purple, beamdoors.CHARGE_LINE, beamdoors.WHITE)


def ruins_metatiles(rom) -> bytes:
    """specs/12f: tileset $0C's metatile table (decompressed, from `rom`'s entry, still vanilla) with the purple wave door's 8
    metatiles $3F0-$3F7 (beamdoors.paint_table, line beamdoors.RUINS_PAINT_LINE); specs/12g2: and the white charge door's 8,
    $3E8-$3EF (line beamdoors.CHARGE_LINE)."""
    wave = beamdoors.paint_table(rom, ruins.vanilla_metatiles(rom), beamdoors.RUINS_PAINT_LINE, filler=False)
    return beamdoors.paint_table(rom, wave, beamdoors.CHARGE_LINE, filler=False, metatiles=beamdoors.CHARGE_METATILES)


def lava_palette(rom, tileset: int) -> bytes:
    """specs/17d: tileset $09's / $0A's palette as the build writes it: line lava.PALETTE_LINE with the Magmoor colours
    (lava.recolor) and line lava.PAINT_LINE = the purple wave door's (from `rom`'s vanilla palette)."""
    return beamdoors.paint_palette(lava.recolor(lava.vanilla_palette(rom, tileset), tileset), lava.PAINT_LINE)


def lava_metatiles(rom) -> bytes:
    """specs/17d: the metatile table tilesets $09 and $0A share (decompressed, vanilla) with the purple wave door's 8 metatiles
    $3F0-$3F7 (vanilla filler there) on line lava.PAINT_LINE."""
    return beamdoors.paint_table(rom, lava.vanilla_metatiles(rom), lava.PAINT_LINE)


def ice_palette(rom, tileset: int) -> bytes:
    """specs/18d: the palette of one of the ice looks (smlib/ice.py) as the build writes it, from `rom`'s vanilla palettes: the
    snow's = tileset $00's with its colours and the purple door on ice.SNOW_PAINT_LINE; the icy ruins' = the Chozo's (ruins_palette:
    the purple door on line 5, the white charge door on line 4) with its colours; the lab's = tileset 4's vanilla with its colours
    and the purple door on beamdoors.PAINT_LINE (tileset 4's table copy). Every one with the snowflakes' colours (ice.SNOW_FLAKES)."""
    if tileset == ice.SNOW_TILESET:
        return beamdoors.paint_palette(ice.recolor(ice.vanilla_palette(rom, ice.SNOW_SOURCE), tileset), ice.SNOW_PAINT_LINE)
    if tileset == ice.RUINS_TILESET:
        return ice.recolor(ruins_palette(rom), tileset)
    if tileset == ice.LAB_TILESET:
        return beamdoors.paint_palette(ice.recolor(ice.vanilla_palette(rom, ice.LAB_SOURCE), tileset), beamdoors.PAINT_LINE)
    raise ValueError(f"tileset {tileset:02X} não é um dos do gelo")


def ice_metatiles(rom) -> bytes:
    """specs/18d: the snow look's metatile table: tileset $00's (vanilla, decompressed) with the purple wave door's 8 metatiles
    $3F0-$3F7 (vanilla filler there) on line ice.SNOW_PAINT_LINE. (The icy ruins and the lab share the Chozo's and tileset 4's
    copies.) specs/18j: and the vertical purple wave door's 8 (beamdoors.VERT_PAINT_METATILES, vanilla filler there too: the
    North Quarantine Tunnel's ceiling door), on the same line."""
    return beamdoors.paint_vertical(rom, beamdoors.paint_table(rom, ice.vanilla_metatiles(rom, ice.SNOW_SOURCE),
                                                               ice.SNOW_PAINT_LINE), ice.SNOW_PAINT_LINE)


def mines_palette(rom, tileset: int) -> bytes:
    """specs/19d: the palette of one of the Mines' looks (smlib/mines.py) as the test build writes it, from `rom`'s vanilla
    palettes: the source's ($0D for the base, $06 for the rock) with the look's colours and the purple door on mines.PAINT_LINE."""
    return beamdoors.paint_palette(mines.recolor(mines.vanilla_palette(rom, mines.SOURCE[tileset]), tileset),
                                   mines.PAINT_LINES[tileset])


def mines_metatiles(rom, tileset: int) -> bytes:
    """specs/19d: the source's vanilla metatile table with the purple wave door's 8 metatiles $3F0-$3F7 and the vertical one's 8
    (vanilla filler there) on line mines.PAINT_LINE."""
    line = mines.PAINT_LINES[tileset]
    return beamdoors.paint_vertical(rom, beamdoors.paint_table(rom, mines.vanilla_metatiles(rom, mines.SOURCE[tileset]), line),
                                    line)


def room_fx(area: AreaDef, r: RoomDef) -> bytes | None:
    """The FX entry ($83, 16 bytes) of a room with lava, heat or snow (None: none of them; water is WATER_FX): specs/12g the heat
    (heat.heat_fx of the area); specs/17d lava (only in the Magmoor's area 2: smlib/lava.py fx_entry, its surface at the
    room's lava row, with the hot room's palette FX bits, heat and lava glows, or none)."""
    if r.snow:   # specs/18d: falling snow, Phendrana's area only
        if r.water or r.fx or r.lava is not None or r.heat or area.number != PHENDRANA_AREA or r.snow not in ice.SNOW_FX:
            raise RuntimeError(f"{r.key}: neve com água/lava/calor/outro FX, fora da área {PHENDRANA_AREA} ou tipo {r.snow:#x}")
        return ice.SNOW_FX[r.snow]
    if r.lava is not None:
        if r.water or r.fx or area.number != MAGMOOR_AREA:
            raise RuntimeError(f"{r.key}: lava com água/outro FX ou fora da área {MAGMOOR_AREA}")
        return lava.fx_entry(r.lava * 16, heat.heat_fx(area.number)[13] if r.heat else lava.FX_COOL)
    if r.acid is not None:   # specs/20g: the crater's phazon that hurts (SM's acid), its rooms in area 0 only
        if r.water or r.fx or r.heat or area.number != IMPACT_CRATER_AREA or not r.key.startswith("impact_"):
            raise RuntimeError(f"{r.key}: ácido com água/calor/outro FX ou fora da cratera (área {IMPACT_CRATER_AREA})")
        return lava.acid_fx_entry(r.acid * 16)
    if r.heat:
        if r.water or r.fx or area.number not in heat.HEAT_BITS:
            raise RuntimeError(f"{r.key}: sala quente com água/outro FX ou fora das áreas {sorted(heat.HEAT_BITS)}")
        return heat.heat_fx(area.number)
    return None


def door_cap_and_screen(room: RoomDef, door_index: int) -> tuple[int, int, int, int]:
    """Cap block (x, y) and screen (x, y) of a door, as the door entry that arrives there needs."""
    d = room.doors[door_index]
    wb, hb = room.width * 16, room.height * 16
    if d.side == "L":
        return 1, d.screen * 16 + 6, 0, d.screen
    if d.side == "R":
        return wb - 2, d.screen * 16 + 6, room.width - 1, d.screen
    if d.side == "T":
        return d.screen * 16 + 6, 2, d.screen, 0
    return d.screen * 16 + 6, hb - 3, d.screen, room.height - 1


def lair_exit_cap(room: RoomDef) -> tuple[int, int]:
    """specs/20i: the cap block (x, y) of the Lair's ceiling door, where its way out into the ending looks (impact/ending.py)."""
    tops = [k for k, d in enumerate(room.doors) if d.side == "T"]
    if len(tops) != 1:
        raise RuntimeError(f"{room.key}: {len(tops)} portas de teto (a saída para o fim espera uma)")
    return door_cap_and_screen(room, tops[0])[:2]


# Grey door cap PLMs by the wall the door is on (research/sm_room_format.md section 5).
GREY_DOOR_PLM = {"R": 0xC842, "L": 0xC848, "B": 0xC84E, "T": 0xC854}
GREY_DOOR_BOSS_DEAD = 0x8000  # type 0 (area boss dead), bit 15: don't save an "opened" bit
GREY_DOOR_MINI_BOSS = 0x8000 | (1 << 10)   # specs/14c: type 1 (the area's mini-boss bit $02, $84:BDE3), no "opened" bit
GREY_DOOR_NEVER = 0x8000 | (4 << 10)   # type 4 (never opens): no Tallon door uses it since specs/09d (07m: the Gully's bomb walls; ice/plasma/conduit doors until 09a)
RED_DOOR_PLM = {"R": 0xC88A, "L": 0xC890, "B": 0xC896, "T": 0xC89C}   # missile doors, argument = door bit
BEAM_DOOR_ARG = 0x8000   # beam doors (specs/09a, tallon/beamdoors.py): no door bit, closed again on every visit

# Prime's intro loadout. SM item bits: $09A2/$09A4 equipment, $09A6/$09A8 beams.
START_ITEMS = 0x0001 | 0x0004 | 0x1000 | 0x0200 | 0x4000 | 0x8000  # Varia Morph Bombs SpaceJump Grapple X-ray
START_BEAMS = 0x0001 | 0x0002 | 0x0008 | 0x1000                    # Wave Ice Plasma Charge
START_MISSILES = 30

# How far a door transition pushes Samus into the next room (door entry bytes 8-9, "distance from
# door"; research/sm_room_format.md section 3). One rule for every area (specs/08):
# - Going down through a floor door the default ($8000: $180 px/256 a frame, LoadDoorHeader
#   $82:DE12) ends with her feet 6-7 px inside the ledge that Canvas.door_gap puts on row 6 under
#   every ceiling door: stuck in it, she can't walk until she jumps (emulator: specs/07l Savestation ->
#   Reactor Access; specs/08 all 14 floor doors of the frigate). With $0140 (a vanilla value) she
#   stops above the ledge and lands on it.
DOWN_PUSH = 0x0140
# - Going up needs more than the default or she falls straight back through the floor door. Vanilla
#   upward doors use $01C0-$0240 (30 of 38); with $01C0 the jump peak was only 2px above our door
#   ledges. More ($0340) puts her head under the shaft steps 8 rows above the floor (Canvas shaft):
#   the frigate escape falls back (specs/08, Desvios). specs/10b: with $0240 she gets control with her
#   feet 47 px over the ledges, and steering from one edge of the 4-block hole to the ledge on the
#   other side she reached it 7 px too low (Tallon Canyon -> Gully: fell back); $02A0 gives 68 px
#   (+21): every dry ceiling door of both areas is climbed steering to either ledge (emulator sweep).
UP_PUSH = 0x02A0
# - Going up into a flooded room, $0240 leaves Samus inside the door: under water she doesn't keep
#   rising and falls straight back (emulator, specs/07l, Reactor Access -> Savestation). With $0340
#   she comes out 2 rows over the door ledges and steers onto one.
UP_PUSH_WATER = 0x0340
SIDE_PUSH = 0x8000   # side doors: the default


def door_push(side: str, into_water: bool) -> int:
    """Door entry push for a door on wall `side` of the room Samus leaves (she travels that way)
    into a room that is flooded (`into_water`, RoomDef.water) or not."""
    if side == "B":
        return DOWN_PUSH
    if side == "T":
        return UP_PUSH_WATER if into_water else UP_PUSH
    return SIDE_PUSH


TRAVEL_DIR = {"R": 0, "L": 1, "B": 2, "T": 3}  # direction Samus moves when leaving through that wall


def conditional_header(header: bytes, at: int, conditions: list[tuple[int, bytes]],
                       default: bytes) -> tuple[bytes, list[int]]:
    """Room header whose state depends on the area boss bits (E629): the first (mask, state) whose
    mask matches wins, else `default`. Returns the bytes and the state addresses, default first."""
    default_at = at + len(header) + 5 * len(conditions) + 2
    cond_at = [default_at + 26 * (i + 1) for i in range(len(conditions))]
    select = b"".join(struct.pack("<HBH", COND_BOSS_BITS, mask, a & 0xFFFF)
                      for (mask, _), a in zip(conditions, cond_at))
    out = header + select + b"\xE6\xE5" + default + b"".join(state for _, state in conditions)
    return out, [default_at] + cond_at


def put_at(bank: Allocator, data: bytes, at: int) -> int:
    """Put `data`, whose inner pointers were computed for address `at` (the free range's next byte, or specs/18h
    Allocator.next_at's): it must land there (specs/12a)."""
    addr = bank.put(data)
    if addr != at:
        raise RuntimeError(f"dados calculados para ${at:06X} foram para ${addr:06X} ({bank.name}, faixa recuperada)")
    return addr


def boss_conditional_header(header: bytes, at: int, alive: bytes, dead: bytes) -> tuple[bytes, list[int]]:
    """Two states: `dead` when the area boss bit is set (E629 #1), else `alive` (the default)."""
    return conditional_header(header, at, [(0x01, dead)], alive)


def station_camera(pos: int, room_px: int, view: int) -> int:
    """Camera start on one axis: the room's corner while Samus is near it (every frigate station),
    else Samus about mid-view, inside the room."""
    return 0 if pos < 192 else max(0, min(pos - view // 2, room_px - view))


def write_load_station(rom: Rom, bank83: Allocator, area: int, index: int, room: Placed,
                       samus_x: int, samus_y: int) -> int:
    """Point load station `index` of `area` at a room, through a dummy door that lands
    there (the game loads the door's destination). Samus at pixel (x, y) of the room."""
    room_header = room.header
    door = bank83.put(struct.pack("<HBBBBBBHH", room_header & 0xFFFF, 0, 0, 0, 0, 0, 0, 0x8000, 0))
    table = 0x800000 | rom.u16(LOAD_STATION_TABLE + 2 * area)
    station = table + LOAD_STATION_SIZE * index
    # whole screens horizontally, like every vanilla station: LoadFromLoadStation copies it into
    # bg1_x_offset, and the PLM drawing ($84:91DC) only accounts for its bit $100, so a camera at
    # x = 576 drew every animated PLM (item, door cap) 64 px to the left of its block (specs/07h)
    screen_x = round(station_camera(samus_x, room.room.width * 256, 256) / 256) * 256
    screen_y = station_camera(samus_y, room.room.height * 256, 224)
    rom.write(station, struct.pack("<HHHHHhh", room_header & 0xFFFF, door & 0xFFFF, 0, screen_x, screen_y,
                                   samus_y - screen_y, samus_x - screen_x - 128))
    return station


def enemy_set_name(area: AreaDef) -> bytes:
    """7-byte debug name before an area's enemy sets: the area name, padded ("FRIGATE", "TALLON ")."""
    return area.name.encode()[:7].ljust(7)


def area_label(name: str) -> bytes:
    """12-tile area name for the pause map: letters A-Z are tiles $30-$49 (palette word $38xx),
    blank is $2801, as in the vanilla labels."""
    pad = 12 - len(name)
    text = " " * (pad // 2) + name + " " * (pad - pad // 2)
    return b"".join(struct.pack("<H", 0x2801 if c == " " else 0x3830 + ord(c) - ord("A")) for c in text)


def replace_checked(rom: Rom, addr: int, old: bytes, new: bytes) -> None:
    if rom.read(addr, len(old)) != old:
        raise RuntimeError(f"bytes inesperados em ${addr:06X}")
    rom.write(addr, new)


def write_map_save_lists(rom: Rom, custom: dict[int, list[int]]) -> None:
    """Make SRAM keep every explored-map byte of each remade area ({area: offsets}). Vanilla saves
    18 bytes for area 3 (the Wrecked Ship's spots), so explored frigate rooms vanished after loading
    a save. Each area gets its own block after the vanilla bytes of the 1280-byte save buffer
    (tools/frigate/mapsave.py); no other area changes."""
    problems = mapsave.check(custom)
    if problems:
        raise RuntimeError("; ".join(problems))
    counts = list(rom.read(mapsave.COUNTS, 6))
    packed = [rom.u16(mapsave.PACKED_OFFS + 2 * i) for i in range(6)]
    lists = [rom.u16(mapsave.LISTS + 2 * i) for i in range(6)]
    assert (tuple(counts), tuple(packed), tuple(lists)) == (
        mapsave.VANILLA_COUNTS, mapsave.VANILLA_PACKED, mapsave.VANILLA_LIST_PTRS), "tabelas de save do mapa mudaram"
    starts = mapsave.layout(custom)
    used = mapsave.VANILLA_END + sum(len(o) for o in custom.values())
    for area, offs in sorted(custom.items()):
        try:
            at = mapsave.list_at(area, len(offs))   # specs/19b: area 5's list goes to $81's free space when it doesn't fit
        except ValueError as e:
            raise RuntimeError(str(e)) from None
        if at != 0x810000 | lists[area]:
            if rom.read(at, len(offs)) != b"\xFF" * len(offs):
                raise RuntimeError(f"área {area}: espaço livre do $81 em ${at:06X} já usado")
            rom.w16(mapsave.LISTS + 2 * area, at & 0xFFFF)
        rom.write(mapsave.COUNTS + area, bytes([len(offs)]))
        rom.w16(mapsave.PACKED_OFFS + 2 * area, starts[area])
        rom.write(at, bytes(offs))
    for i in range(6):
        if i not in custom:
            assert rom.read(mapsave.COUNTS + i, 1)[0] == mapsave.VANILLA_COUNTS[i]
            assert rom.u16(mapsave.PACKED_OFFS + 2 * i) == mapsave.VANILLA_PACKED[i]
    for area, offs in sorted(custom.items()):
        print(f"  mapa na SRAM: área {area} = {len(offs)} bytes em +{starts[area]} "
              f"({used}/{mapsave.PACKED_SIZE} usados)")


def write_pause_map(rom: Rom, area: AreaDef, bank82: "Allocator | None" = None) -> list[int]:
    """An area's pause map, minimap, map-station data, icons and name, written over the vanilla
    tables of that area in place (same sizes, checked against VANILLA_PAUSE). specs/19i: an area whose
    vanilla map station icon list is empty (FFFF: Tourian, the Mines' area 5) gets a new list in $82's
    free space (`bank82`) and its pointer; the vanilla FFFF is left where it is. Returns the
    explored-map bytes the save must keep (AreaDef.map_save_bytes; written for all areas by
    write_map_save_lists)."""
    a = area.number
    if a not in VANILLA_PAUSE:
        raise RuntimeError(f"área {a} ({area.key}): faltam os bytes vanilla do mapa de pausa em VANILLA_PAUSE")
    vanilla = VANILLA_PAUSE[a]
    tilemap, reveal = pausemap.build(area.rooms)
    tm_addr = rom.u24(PAUSE_TILEMAPS + 3 * a)
    reveal_addr = 0x820000 | rom.u16(PAUSE_MAP_REVEAL + 2 * a)
    assert tm_addr == vanilla["tilemap"] and reveal_addr == vanilla["reveal"], \
        f"tabelas do mapa da área {a} fora do lugar vanilla"
    # specs/19b: area 5's mask ($82:9C27) is also the debug area 7's pointer (nothing loads area 7: specs/11); no other sharing
    assert {b for b in range(8) if b != a and rom.u16(PAUSE_MAP_REVEAL + 2 * b) == reveal_addr & 0xFFFF} <= ({DEBUG_AREA} if a == 5
                                                                                                      else set())
    rom.write(tm_addr, tilemap)
    rom.write(reveal_addr, reveal)
    rom.write(0x820000 | rom.u16(PAUSE_AREA_LABELS + 2 * a), area_label(area.name))

    by_key = area.by_key()

    def icon_list(kind: int) -> int:
        return 0x820000 | rom.u16(MAP_ICONS + kind + 2 * a)

    def same_size(kind: str, new: bytes) -> bytes:
        """`new` padded with $FF to the vanilla list's size (an empty list is $FFFF); never longer."""
        if len(new) > len(vanilla[kind]):
            raise RuntimeError(f"área {a}: lista de ícones {kind} tem {len(new)} bytes, a vanilla {len(vanilla[kind])}")
        return new + b"\xFF" * (len(vanilla[kind]) - len(new))

    # boss icon (drawn once the area boss bit is set)
    if area.boss_room:
        replace_checked(rom, icon_list(ICONS_BOSS), vanilla["boss"],
                        same_size("boss", _xy(*pausemap.icon_xy(by_key[area.boss_room])) + b"\xFF\xFF"))
    elif "boss" in vanilla:   # specs/12e: no boss of ours yet (the Chozo): no vanilla boss icon left on the map
        replace_checked(rom, icon_list(ICONS_BOSS), vanilla["boss"], same_size("boss", b"\xFF\xFF"))
    # map station icons
    stations = b"".join(_xy(*pausemap.icon_xy(r, r.map_station[0] // 16)) for r in area.rooms if r.map_station)
    if stations and vanilla["map_station"] == b"\xFF\xFF":   # specs/19i: no vanilla list to write over
        if bank82 is None:
            raise RuntimeError(f"área {a}: a lista de ícones de map station precisa de espaço no $82")
        replace_checked(rom, icon_list(ICONS_MAP_STATION), vanilla["map_station"], vanilla["map_station"])
        at = bank82.put(stations + b"\xFF\xFF")
        rom.write(MAP_ICONS + ICONS_MAP_STATION + 2 * a, struct.pack("<H", at & 0xFFFF))
    else:
        replace_checked(rom, icon_list(ICONS_MAP_STATION), vanilla["map_station"],
                        same_size("map_station", stations + b"\xFF\xFF"))
    # save icons: entry n = load station n (also where the file-select map shows Samus); stations
    # 8+ are not save slots (the Tallon's escape arrival $12), the other entries are skipped ($FFFE)
    slots = len(vanilla["save"]) // 4
    entries = [_xy(0xFFFE, 0xFFFE)] * slots
    for st in area.load_stations:
        if st.index < SAVE_SLOTS:
            if st.index >= slots:
                raise RuntimeError(f"área {a}: estação {st.index} fora da lista vanilla de {slots} ícones de save")
            entries[st.index] = _xy(*pausemap.icon_xy(by_key[st.room], st.x // 256, st.y // 256))
    if a == 0:   # the ship icon follows entry 0 (SHIP_ICON_SITES)
        for site in SHIP_ICON_SITES:
            if rom.read(site, len(SHIP_ICON_CODE)) != SHIP_ICON_CODE:
                raise RuntimeError(f"bytes inesperados em ${site:06X} (ícone da nave da área 0)")
        assert icon_list(ICONS_SAVE) == 0x82C853, "lista de save da área 0 fora do lugar vanilla"
    replace_checked(rom, icon_list(ICONS_SAVE), vanilla["save"], b"".join(entries))
    # no elevators to other areas yet: no elevator icons (this also ends the save list after its 8
    # entries) and an empty "to <area>" label list
    if "elevator_icons" in vanilla:
        replace_checked(rom, icon_list(ICONS_ELEVATOR), vanilla["elevator_icons"], same_size("elevator_icons", b"\xFF\xFF"))
    labels = 0x820000 | rom.u16(MAP_ELEVATOR_LABELS + 2 * a)
    replace_checked(rom, labels, vanilla["elevators"], b"\xFF" * len(vanilla["elevators"]))
    keep = area.map_save_bytes()
    missing = sorted(set(mapsave.needed(reveal)) - set(keep))
    if missing:
        raise RuntimeError(f"área {a}: bytes do mapa {missing} das salas construídas fora da lista do save")
    return keep


def build(cross_room: str | None = None, test_12g: bool = False, out_dir: Path = ROOT / "build", test_17d: bool = False,
          test_18d: bool = False, test_19d: bool = False, test_20d: bool = False) -> Rom:
    """`cross_room`: test build (--cruzar-banco) with that room's level across a bank boundary. `test_12g`: test build
    (--teste-12g, specs/12g) with chozo/testrooms.py's room (heat, charge door, Charge Beam, Varia Suit); its manifest goes
    to `out_dir`. `test_17d`: test build (--teste-17d, specs/17d) with magmoor/testrooms.py's two lava rooms in area 2 (the Magmoor's).
    `test_18d`: test build (--teste-18d, specs/18d) with phendrana/testrooms.py's area 4 (the ice looks, the snow, the water).
    `test_19d`: test build (--teste-19d, specs/19d) with mines/testrooms.py's rooms (the Mines' two looks; specs/19e: added to a copy
    of the Mines' area 5 that takes MINES' place in AREAS only while this build runs). `test_20d`: test build (--teste-20d, specs/20d)
    with the Impact Crater's look (impact/style.py) on tileset $03, no room."""
    if test_19d:
        from mines import testrooms as mines_testrooms
        i = AREAS.index(MINES)
        AREAS[i] = mines_testrooms.area()
        try:
            return _build(cross_room, test_12g, out_dir, test_17d, test_18d, True, test_20d)
        finally:
            AREAS[i] = MINES
    return _build(cross_room, test_12g, out_dir, test_17d, test_18d, False, test_20d)


def _build(cross_room, test_12g, out_dir, test_17d, test_18d, test_19d, test_20d=False) -> Rom:
    test_items = testrooms.apply(CHOZO) if test_12g else []
    if test_17d:   # specs/17e: in the Magmoor's area, hung on its P16
        from magmoor import testrooms as lava_testrooms
        lava_testrooms.apply(MAGMOOR)
    if test_18d:   # specs/18d: Phendrana's area 4 with the ice looks' test rooms (phendrana/testrooms.py; specs/18e: added to it)
        from phendrana import testrooms as ice_testrooms
        ice_testrooms.apply(PHENDRANA)
    rom = Rom.load(BASE)
    rom.expand_to(ROM_SIZE)
    bank8f = Allocator(rom, *FREE_8F, "$8F", reclaimed=RECLAIMED_8F)
    bank83 = Allocator(rom, *FREE_83, "$83")
    bank_a1 = Allocator(rom, *FREE_A1, "$A1", reclaimed=RECLAIMED_A1)   # specs/19a
    bank_b4 = Allocator(rom, *FREE_B4, "$B4")
    bank_a0 = Allocator(rom, 0xA0F7D3, 0xA0FFFF, "$A0")   # enemy species headers
    bank_a3 = Allocator(rom, 0xA3F311, 0xA3FFFF, "$A3")   # specs/14a: palettes of species copies whose AI is in $A3
    bank_a2 = Allocator(rom, 0xA2F498, 0xA2FFFF, "$A2")   # gunship code
    bank_a6 = Allocator(rom, 0xA6FEBC, 0xA6FFFF, "$A6")   # Ridley code
    bank_b2 = Allocator(rom, 0xB2FEAA, 0xB2FFFF, "$B2")   # specs/19h: the Phazon Elite's palettes (its AI is in $B2)
    bank_aa = Allocator(rom, 0xAAF7D3, 0xAAFFFF, "$AA")   # specs/19k: the Omega Pirate's palettes and selectors (the Torizo's AI)
    level_alloc = ExpandedAllocator(rom, LEVEL_BANKS, "nível", cross_banks=True)
    fixed = ExpandedAllocator(rom, FIXED_BANKS, "fixo", cross_banks=False)

    rooms = {r.key: Placed(area, r) for area, r in all_rooms()}
    levels = {key: p.room.level().compressed() for key, p in rooms.items()}
    pad = 0
    if cross_room is not None:
        pad = crossing_pad([(k, len(v)) for k, v in levels.items()], cross_room, level_alloc.pc)
        level_alloc.skip(pad)
    bg_lists: dict[bytes, int] = {}   # library background lists given as bytes (the Tallon sky)
    water_fx = bank83.put(WATER_FX) & 0xFFFF   # FX of the flooded rooms (RoomDef.water, specs/07l)
    # specs/12g: area 1's palette FX list gets SM's heat object (chozo/heat.py); the FX entry goes in once a room is hot.
    # specs/17b: per area (heat.HEAT_BITS): area 2's list has it already (heat.patch gives None: nothing written)
    for heat_area in sorted(heat.HEAT_BITS):
        if (heat_patch := heat.patch(rom, heat_area)) is not None:
            rom.write(*heat_patch)
    rom.write(*heat.varia_only_patch(rom))   # specs/12g2: only the Varia Suit protects from the heat ($8D:E37D)
    fx_entries: dict[bytes, int] = {}   # specs/12g/17d: heat and lava FX entries ($83), each put once, by its first room
    if rom.read(ELEVATOR_PAD_DOOR_VANILLA, len(ELEVATOR_PAD_DOOR)) != ELEVATOR_PAD_DOOR:
        raise RuntimeError(f"bytes inesperados em ${ELEVATOR_PAD_DOOR_VANILLA:06X} (porta da plataforma do elevador)")
    pad_door = bank83.put(ELEVATOR_PAD_DOOR)   # specs/12e: the elevator platforms' door blocks
    timer_start = bank8f.put(escape_timer_routine(FRIGATE.number))
    timer_stop = bank8f.put(STOP_TIMER_ROUTINE)
    timer_restore = bank8f.put(timer.restore_timer_door_asm())
    arena_stub = bank8f.put(chozo_bosses.stub()) & 0xFFFF   # specs/14b: every arena's alive-state main ASM
    ridley = ending.meta_ridley(rom, bank_a0, bank_a6)
    chozo_bosses.build_copies(rom, bank_a0, {0xA3: bank_a3, 0xB4: bank_b4, 0xB2: bank_b2})   # specs/14a: the Plated Beetle's species (after Ridley's); specs/18l: the Metroid's shot AI ($A3) and table ($B4); specs/19h: the Phazon Elite's palette ($B2)
    # specs/19h: the ninja pirates' leap palette (sprite line 7): the init's operand -> the Phazon Elite's colours in $B2
    for addr, data in chozo_bosses.ninja_patches(rom, bank_b2.next_at(32)):
        if addr >> 16 == 0xB2 and addr & 0xFFFF >= 0xFEAA:
            bank_b2.put(data)
        else:
            rom.write(addr, data)
    ending.gunship(rom, bank_a2)
    ending.tallon_text(rom, lambda b: fixed.put(b, "cena de Ceres (TALLON IV)"))
    # the end of the frigate lands at the Tallon's Landing Site (specs/07g): load station $12 of
    # area 0 ($82:8032: STZ area; $82:8035: LDA #$0012; STA load station) and the ship's landing height
    if rom.read(ESCAPE_STATION_SITE, 3) != bytes([0xA9, ESCAPE_ARRIVAL_STATION, 0x00]):
        raise RuntimeError(f"bytes inesperados em ${ESCAPE_STATION_SITE:06X}")
    arrival = next(st for st in TALLON.load_stations if st.index == ESCAPE_ARRIVAL_STATION)
    ending.landing_height(rom, ending.ship_top_y(TALLON.by_key()[arrival.room].ship[1]))

    # 1) room headers first (doors need their addresses), with placeholder door lists/state
    teleporter_cond = None   # specs/20e: the Artifact Temple's state condition, put in $8F by its room
    for p in rooms.values():
        r, area = p.room, p.area
        bg = area.library_bg if r.library_bg is None else r.library_bg
        if isinstance(bg, bytes) and bg not in bg_lists:
            bg_lists[bg] = bank8f.put(bg) & 0xFFFF     # into $8F once, before the first room using it
        level_ptr = level_alloc.put(levels[r.key], r.key)
        if r.water and r.fx:
            raise RuntimeError(f"{r.key}: sala inundada com outro FX (${r.fx:04X})")
        fx = water_fx if r.water else None
        # specs/12g: the heat FX (chozo/heat.py), only where the area's list has the heat object (specs/17b); specs/17d: lava
        if (entry := room_fx(area, r)) is not None:
            if entry not in fx_entries:
                fx_entries[entry] = bank83.put(entry) & 0xFFFF
            fx = fx_entries[entry]
        spawns = area.enemies.get(r.key, [])
        arena = chozo_bosses.arena_of(r.key)
        if spawns or r.elevator:
            pop = bank_a1.put(room_population(spawns, r) if arena is None or arena.condition != chozo_bosses.ITEM
                              else item_arena_population(spawns, r)) & 0xFFFF
            set_ptr = ((bank_b4.put(enemy_set(spawns, enemy_set_name(area))) + 7) & 0xFFFF   # skip the 7-byte debug name
                       if spawns else EMPTY_ENEMY_SET)
        elif r.ship:
            assert not spawns, "a nave ocupa a VRAM de inimigos da sala"
            pop = bank_a1.put(ending.gunship_population(*r.ship)) & 0xFFFF
            set_ptr = (bank_b4.put(ending.gunship_enemy_set()) + 7) & 0xFFFF
        else:
            pop, set_ptr = EMPTY_ENEMY_POP, EMPTY_ENEMY_SET
        if r.key == HANGAR_ROOM:
            # Prime's hangar is open to space: a starfield on BG2 instead of the WS wall pattern
            tiles = space.star_tiles()
            tiles_at = fixed.put(tiles, "estrelas do hangar (tiles)")
            map_at = fixed.put(space.star_tilemap(), "estrelas do hangar (mapa)")
            bg = bank8f.put(space.library_bg(tiles_at, len(tiles), map_at)) & 0xFFFF
            normal = state_bytes(level_ptr, area, r, fx=fx, enemy_pop=pop, enemy_set_ptr=set_ptr,
                                 layer2=space.LAYER2_SCROLL, bg=bg)
        else:
            normal = state_bytes(level_ptr, area, r, fx=fx, enemy_pop=pop, enemy_set_ptr=set_ptr, bg_lists=bg_lists)
        header = bytes([0, area.number, r.map_x, r.map_y, r.width, r.height, 0x70, 0xA0, 0x00]) + b"\x00\x00"
        if r.key == BOSS_ROOM:
            # default state = boss alive (Phantoon); E629 #1 selects the boss-dead state
            fight = state_bytes(level_ptr, area, r, music=PHANTOON_MUSIC, fx=PHANTOON_FX, enemy_pop=PHANTOON_ENEMY_POP,
                                enemy_set_ptr=PHANTOON_ENEMY_SET, layer2=PHANTOON_LAYER2,
                                main_asm=timer_start & 0xFFFF, bg=PHANTOON_BG)
            data, p.states = boss_conditional_header(header, bank8f.ptr, fight, normal)
            p.header = put_at(bank8f, data, bank8f.ptr)   # its state pointers were computed for bank8f.ptr
            assert rom.read(p.states[1], 26) == normal
        elif r.key == RIDLEY_ROOM:
            # escape (boss bit 1) until Meta Ridley has flown off (bit 2): his state; else normal
            assert not spawns, "o Ridley ocupa toda a VRAM de inimigos da sala"
            flyby = state_bytes(level_ptr, area, r, enemy_pop=bank_a1.put(ending.ridley_population(ridley)) & 0xFFFF,
                                enemy_set_ptr=(bank_b4.put(ending.ridley_enemy_set(ridley)) + 7) & 0xFFFF)
            data, p.states = conditional_header(header, bank8f.ptr, [(ending.RIDLEY_GONE_BIT, normal), (0x01, flyby)],
                                                normal)
            p.header = put_at(bank8f, data, bank8f.ptr)   # its state pointers were computed for bank8f.ptr
        elif arena is not None:
            # specs/14b: the arena alive (the default: all its enemies, the mini-boss music, the arena routine as main ASM)
            # until its boss bit (E629 #bit) selects the dead state (no boss kinds, the area's music)
            if r.save_station or r.elevator:
                raise RuntimeError(f"{r.key}: arena com estação ou elevador")
            dead_pop = bank_a1.put(room_population([e for e in spawns if not e.species.boss], r)) & 0xFFFF
            alive_asm, dead_asm = arena_stub, 0x0000
            if r.key == impact_rooms.LAIR:
                # specs/20i: the way out of the Lair into the ending (impact/ending.py), in both states (the bit decides)
                exit_at = bank8f.put(impact_ending.exit_routine(area.number, arena.bit, *lair_exit_cap(r))) & 0xFFFF
                alive_asm = bank8f.put(impact_ending.alive_main_asm(chozo_bosses.ROUTINE, exit_at)) & 0xFFFF
                dead_asm = exit_at
            alive = state_bytes(level_ptr, area, r, music=arena.music, fx=fx, enemy_pop=pop, enemy_set_ptr=set_ptr,
                                main_asm=alive_asm, bg_lists=bg_lists)
            dead = state_bytes(level_ptr, area, r, fx=fx, enemy_pop=dead_pop, enemy_set_ptr=set_ptr, main_asm=dead_asm,
                               bg_lists=bg_lists)
            # specs/18h: where it lands (the main range of $8F is full since 12a: Phendrana's go to the demos' range, 18a)
            at = bank8f.next_at(len(conditional_header(header, 0, [(arena.bit, dead)], alive)[0]))
            data, p.states = conditional_header(header, at, [(arena.bit, dead)], alive)
            p.header = put_at(bank8f, data, at)   # its state pointers were computed for `at`
        elif r.key == impact_rooms.TELEPORTER[0]:
            # specs/20e: the Artifact Temple's teleporter works once the Omega Pirate is dead: the default state without the
            # elevator's platform (its enemies only) and with the main ASM that keeps elevator_flags off (no platform AI does it),
            # our condition (the Omega arena's bit of area 5) selects the one with it
            if teleporter_cond is None:
                teleporter_cond = bank8f.put(teleporter_condition())
                flags_off = bank8f.put(ELEVATOR_FLAGS_OFF)
            off = state_bytes(level_ptr, area, r, fx=fx, bg_lists=bg_lists,
                              enemy_pop=(bank_a1.put(population(spawns)) & 0xFFFF) if spawns else EMPTY_ENEMY_POP,
                              enemy_set_ptr=set_ptr, main_asm=flags_off & 0xFFFF)
            at = bank8f.next_at(len(teleporter_header(header, 0, 0, normal, off)[0]))
            data, p.states = teleporter_header(header, at, teleporter_cond, normal, off)
            p.header = put_at(bank8f, data, at)   # its state pointers were computed for `at`
        elif r.save_station and area.boss_room:
            # The frigate, like Prime ("Save Disabled" in this room): the station works until the boss dies.
            # Saving mid-escape would let a continue skip the timer. The save PLM only goes in
            # the boss-alive state (states[0]), see step 2.
            data, p.states = boss_conditional_header(header, bank8f.ptr, normal, normal)
            p.header = put_at(bank8f, data, bank8f.ptr)   # its state pointers were computed for bank8f.ptr
        else:
            p.header = bank8f.put(header + b"\xE6\xE5" + normal)
            p.states = [p.header + 11 + 2]

    # 2) door entries in $83 and door-out lists in $8F (plus each room's PLM list); the Tallon's beam
    # door PLMs in $84 (specs/09a)
    beam_bytes = beamdoors.apply(rom)
    # specs/13: Samus' touch of an item finds the item, not a dead PLM slot with its block index ($84:EEAB)
    touch_bytes = itemtouch.apply(rom)
    # the Gravity Suit's cutscene leaves Samus where she is (specs/09b, tallon/items.py gravity_patch)
    rom.write(*tallon_items.gravity_patch(rom))
    rom.write(*tallon_items.varia_patch(rom))   # specs/12g: the Varia Suit's cutscene too
    placed_items: dict[str, list] = {}
    arena_entries: dict[str, tuple] = {}   # specs/14b: the arena routine's table, by room (header, arena, prize entry)
    arena_doors: dict[str, int] = {}   # specs/14d: an ITEM arena's door cap entry ($8F), spawned when its fight starts
    for n, it in tallon_items.placed({r.key for r in TALLON.rooms}):
        placed_items.setdefault(it.room, []).append((tallon_items.BITS[n], it))
    for n, it in chozo_items.placed({r.key for r in CHOZO.rooms}):   # specs/12f: the Chozo's, bits after the Tallon's
        placed_items.setdefault(it.room, []).append((chozo_items.BITS[n], it))
    for n, it in magmoor_items.placed({r.key for r in MAGMOOR.rooms}):   # specs/17f: the Magmoor's, bits after the Chozo's
        placed_items.setdefault(it.room, []).append((magmoor_items.BITS[n], it))
    for n, it in phendrana_items.placed({r.key for r in PHENDRANA.rooms}):   # specs/18f: Phendrana's, bits after the Magmoor's
        placed_items.setdefault(it.room, []).append((phendrana_items.BITS[n], it))
    for n, it in mines_items.placed({r.key for r in MINES.rooms}):   # specs/19f: the Mines', bits after Phendrana's
        placed_items.setdefault(it.room, []).append((mines_items.BITS[n], it))
    for bit, it in test_items:   # specs/12g: the test build's Charge Beam and Varia Suit (chozo/testrooms.py)
        placed_items.setdefault(it.room, []).append((bit, it))
    for p in rooms.values():
        entries = []
        for d in p.room.doors:
            target = rooms[d.to_room]
            cap_x, cap_y, scr_x, scr_y = door_cap_and_screen(target.room, d.to_door)
            arrival = target.room.doors[d.to_door]
            close_behind = 4 if arrival.has_cap or item_arena_door(target.room.key, arrival) else 0   # re-close the blue cap
            door_asm = 0x0000
            if d.to_room == HANGAR_ROOM:
                door_asm = timer_stop & 0xFFFF       # escaped: stop the timer
            elif p.room.key == RIDLEY_ROOM:
                door_asm = timer_restore & 0xFFFF    # Meta Ridley's tiles may still cover the digits
            push = door_push(d.side, target.room.water)
            entry = struct.pack("<HBBBBBBHH", target.header & 0xFFFF, 0x00, TRAVEL_DIR[d.side] | close_behind,
                                cap_x, cap_y, scr_x, scr_y, push, door_asm)
            entries.append(bank83.put(entry))
        p.door_entries = entries
        if p.room.elevator:   # specs/12e: the door-out list goes on with the exit and the platform (RoomDef.elevator_slots)
            other = rooms[elevator_target(p.room.key)]
            same = other.area is p.area
            if same and p.room.key not in impact_rooms.TELEPORTER:   # specs/20e: only the crater's teleporter stays in its area
                raise RuntimeError(f"{p.room.key}: elevador para {other.room.key}, na mesma área")
            p.elevator_entries = [bank83.put(elevator_exit_entry(p.room, other.header, other.room, same)), pad_door]
            entries = entries + p.elevator_entries
        # specs/12g2: no item goes first any more (12f put the Chozo's power bomb item first, in the top PLM slot, over
        # dead slots a power bomb leaves; specs/13's touch fix skips them, smlib/itemtouch.py; user decision)
        plms, dead_caps = b"", []   # specs/18h: dead_caps = (where in plms, the dead state's cap) of a KILLS arena's boss door
        for i, d in enumerate(p.room.doors):
            cap_x, cap_y, _, _ = door_cap_and_screen(p.room, i)
            if (alive_cap := arena_door_alive_cap(p.room.key, d)) is not None:
                # specs/18h: the fight's grey cap of type 3 (opens on the room's kill count, as the arena routine's KILLS) in
                # the alive state; the door's own cap (dead_lock: Prime's key lock) or none in the dead state; 18k: the
                # Torizo's grey cap of type 2 (opens on the bit its death sets)
                dead = b""
                if d.dead_lock is not None:
                    if (d.dead_lock, d.side) not in beamdoors.PLM:
                        raise RuntimeError(f"{p.room.key}: porta de chefe com tampa {d.dead_lock} na parede {d.side}")
                    dead = struct.pack("<HBBH", beamdoors.PLM[(d.dead_lock, d.side)], cap_x, cap_y, BEAM_DOOR_ARG)
                dead_caps.append((len(plms), dead))
                plms += struct.pack("<HBBH", GREY_DOOR_PLM[d.side], cap_x, cap_y, alive_cap)
                continue
            if d.locked:
                plms += struct.pack("<HBBH", GREY_DOOR_PLM[d.side], cap_x, cap_y, GREY_DOOR_BOSS_DEAD)
            elif d.lock == "grey":
                plms += struct.pack("<HBBH", GREY_DOOR_PLM[d.side], cap_x, cap_y, GREY_DOOR_NEVER)
            elif item_arena_door(p.room.key, d):   # specs/14d: no PLM; the routine spawns this cap (type 3) at the start
                if p.room.key in arena_doors:
                    raise RuntimeError(f"{p.room.key}: arena de item com duas portas de chefe")
                arena_doors[p.room.key] = bank8f.put(struct.pack("<HBBH", GREY_DOOR_PLM[d.side], cap_x, cap_y,
                                                                 chozo_bosses.GREY_DOOR_KILLS))
            elif d.lock == "boss":   # specs/14c: opens when the room's boss (the Spore Spawn) sets the mini-boss bit
                arena = chozo_bosses.arena_of(p.room.key)
                if arena is None or arena.condition != chozo_bosses.BOSS_BIT or arena.arg != chozo_bosses.MINI_BOSS_BIT:
                    raise RuntimeError(f"{p.room.key}: porta de chefe sem arena que espere o bit de mini-chefe")
                plms += struct.pack("<HBBH", GREY_DOOR_PLM[d.side], cap_x, cap_y, GREY_DOOR_MINI_BOSS)
            elif d.lock == "missile":
                plms += struct.pack("<HBBH", RED_DOOR_PLM[d.side], cap_x, cap_y, d.lock_bit)
            elif (d.lock, d.side) in beamdoors.PLM:
                plms += struct.pack("<HBBH", beamdoors.PLM[(d.lock, d.side)], cap_x, cap_y, BEAM_DOOR_ARG)
            elif d.lock in beamdoors.BEAMS:
                raise RuntimeError(f"{p.room.key}: porta de feixe {d.lock} na parede {d.side} (só L/R existem)")
            elif d.lock is not None:
                raise RuntimeError(f"{p.room.key}: tampa desconhecida {d.lock!r}")
        for x, y, side, beam in p.room.caps:   # specs/18i: a niche's beam cap inside the room (RoomDef.caps)
            if (beam, side) not in beamdoors.PLM or side not in "LR":
                raise RuntimeError(f"{p.room.key}: tampa de feixe {beam} {side} dentro da sala sem PLM")
            plms += struct.pack("<HBBH", beamdoors.PLM[(beam, side)], x, y, BEAM_DOOR_ARG)
        for bit, it in placed_items.get(p.room.key, []):   # Tallon (specs/07h) and Chozo (12f) items: PLM, block, item bit
            plms += struct.pack("<HBBH", it.kind, *it.spot, bit)
        if p.room.map_station:
            mx, mfloor = p.room.map_station
            plms += struct.pack("<HBBH", MAP_STATION_PLM, mx, mfloor - 2, MAP_STATION_ARG)
        if p.room.missile_station:   # specs/19l
            sx, sfloor = p.room.missile_station
            plms += struct.pack("<HBBH", MISSILE_STATION_PLM, sx, sfloor - 2, MISSILE_STATION_ARG)
        state_plms = [plms] * len(p.states)
        arena = chozo_bosses.arena_of(p.room.key)
        if dead_caps:   # specs/18h: the boss door's grey cap only in the alive state, its own cap (or none) in the dead
            dead_list = plms
            for at, cap in reversed(dead_caps):
                dead_list = dead_list[:at] + cap + dead_list[at + 6:]
            state_plms = [plms, dead_list]
        if arena is not None and arena.prize is not None:
            # specs/14b: the prize only in the dead state's list; the routine spawns that entry of it
            prize = next((struct.pack("<HBBH", it.kind, *it.spot, bit) for bit, it in placed_items.get(p.room.key, [])
                          if (it.room, it.spot) == arena.prize), None)
            if prize is None:
                raise RuntimeError(f"{p.room.key}: o prêmio da arena {arena.prize} não é um item colocado da sala")
            state_plms = [state_plms[0].replace(prize, b"", 1), state_plms[1]]
        if p.room.save_station:
            sx, sfloor = p.room.save_station
            state_plms[0] = struct.pack("<HBBH", SAVE_PLM, sx, sfloor, p.area.station_in(p.room.key)) + plms
        written: dict[bytes, int] = {}
        for st, data in zip(p.states, state_plms):
            if data:
                if arena is not None and data in written:   # specs/14b: an arena's states share an equal list
                    rom.w16(st + 20, written[data])
                    continue
                written[data] = bank8f.put(data + b"\x00\x00") & 0xFFFF
                rom.w16(st + 20, written[data])
        if arena is not None:
            prize_at = 0
            if arena.prize is not None:
                dead_list = 0x8F0000 | rom.u16(p.states[1] + 20)
                prize_at = dead_list + state_plms[1].index(prize)
            arena_entries[p.room.key] = (p.header, arena, prize_at)
        door_list = bank8f.put(b"".join(struct.pack("<H", e & 0xFFFF) for e in entries)) if entries else 0x8000
        rom.w16(p.header + 9, door_list & 0xFFFF)

    # specs/14b: the arena routine and its table in $84 (after the beam doors' and the item touch's code)
    if len(arena_entries) != len(chozo_bosses.ARENAS):
        raise RuntimeError(f"{len(arena_entries)} arenas construídas, a tabela tem {len(chozo_bosses.ARENAS)}")
    code = chozo_bosses.routine(chozo_bosses.ROUTINE + len(chozo_bosses.routine(0)))
    records, record_at = b"", chozo_bosses.ROUTINE + len(code) + chozo_bosses.ENTRY_SIZE * len(chozo_bosses.ARENAS) + 2
    arena_table = b""
    for a in chozo_bosses.ARENAS:   # in ARENAS' order; specs/14d: the ITEM arenas' fight records after the table
        header, arena, prize_at = arena_entries[a.room]
        record = 0
        if a.condition == chozo_bosses.ITEM:
            if a.room not in arena_doors:
                raise RuntimeError(f"{a.room}: arena de item sem porta de chefe (BOSS_DOORS)")
            area = next(ar for ar in AREAS if a.room in ar.by_key())
            spawns = area.enemies.get(a.room, [])
            spawned = [s.entry() for s in spawns if s.species.boss]
            record = record_at + len(records)
            records += chozo_bosses.fight_record(a, sum(not s.species.harmless for s in spawns), arena_doors[a.room],
                                                 spawned)
        arena_table += chozo_bosses.table_entry(header, arena, prize_at, record)
    arena_bytes = code + arena_table + b"\x00\x00" + records
    if rom.read(chozo_bosses.ROUTINE, len(arena_bytes)) != b"\xFF" * len(arena_bytes):
        raise RuntimeError(f"${chozo_bosses.ROUTINE:06X} não está livre para a rotina das arenas")
    rom.write(chozo_bosses.ROUTINE, arena_bytes)

    # 3) recolor each area's tileset palette into expanded space (once per tileset)
    recolored: dict[int, tuple[int, ...]] = {}
    for area in AREAS:
        if not area.palette_rows:
            continue
        if area.tileset in recolored:
            if recolored[area.tileset] != area.palette_rows:
                raise RuntimeError(f"tileset {area.tileset} recolorido de dois jeitos (o recolor é global)")
            continue
        recolored[area.tileset] = area.palette_rows
        entry = 0x8F0000 | rom.u16(0x8FE7A7 + 2 * area.tileset)
        pal_ptr = rom.u24(entry + 6)
        palette, _ = decompress(rom.data, snes_to_pc(pal_ptr))
        palette = recolor(palette, area.palette_rows)
        if area.tileset == beamdoors.PAINT_TILESET:   # specs/10d: the purple wave door's palette line
            palette = beamdoors.paint_palette(palette)
        rom.w24(entry + 6, fixed.put(compress(palette), f"paleta do tileset {area.tileset}"))
    if beamdoors.PAINT_TILESET not in recolored:
        raise RuntimeError(f"tileset {beamdoors.PAINT_TILESET} sem recolor: a paleta da porta de onda não foi escrita")
    # specs/10d: the purple wave door's 8 metatiles in tileset 4's own copy of its metatile table (tileset 5, which
    # shared the vanilla table, keeps it)
    entry = 0x8F0000 | rom.u16(0x8FE7A7 + 2 * beamdoors.PAINT_TILESET)
    table, _ = decompress(rom.data, snes_to_pc(rom.u24(entry)))
    # specs/18i: and the vertical purple wave door's 8 (beamdoors.VERT_PAINT_METATILES: the labs' floor/ceiling wave doors)
    rom.w24(entry, fixed.put(compress(beamdoors.paint_vertical(rom, beamdoors.paint_table(rom, table))),
                             f"metatiles do tileset {beamdoors.PAINT_TILESET}"))
    entry = 0x8F0000 | rom.u16(0x8FE7A7 + 2 * FRIGATE.tileset)
    # the hangar's star tiles sit right after the tileset graphics (space.py), and its back wall
    # must not cover Samus: no BG priority bit in the backdrop metatiles
    gfx, _ = decompress(rom.data, snes_to_pc(rom.u24(entry + 3)))
    if len(gfx) > space.STAR_VRAM * 2:
        raise RuntimeError(f"gráficos do tileset {FRIGATE.tileset} ({len(gfx):#x} bytes) cobrem as estrelas do hangar")
    table, _ = decompress(rom.data, snes_to_pc(rom.u24(entry)))
    for mt in sorted({c[2] & 0x3FF for cells in BACKDROPS.values() for c in cells}):
        if mt < 0x100 or any(w & 0x2000 for w in struct.unpack_from("<4H", table, (mt - 0x100) * 8)):
            raise RuntimeError(f"metatile ${mt:03X} do fundo do hangar tem prioridade (cobriria a Samus)")

    # 4) load stations of every area (frigate: 0 -> hangar, 1 -> the save station room)
    stations = {area.key: [(st, write_load_station(rom, bank83, area.number, st.index, rooms[st.room],
                                                   st.x, st.y))
                           for st in sorted(area.load_stations, key=lambda s: s.index)]
                for area in AREAS}
    routine = bytearray([
        0xA9, 0x06, 0x00, 0x8D, 0x98, 0x09,                 # game_state = 6 (loading game)
        0xA9, 0x05, 0x00, 0x8F, 0x14, 0xD9, 0x7E,           # loading_game_state = 5 (main)
        0xA9, START_AREA.number, 0x00, 0x8D, 0x9F, 0x07,    # area
        0xA9, SPAWN_STATION, 0x00, 0x8D, 0x8B, 0x07,        # load station (hangar)
        0x9C, 0x9E, 0x09, 0x9C, 0x23, 0x07, 0x9C, 0x25, 0x07,
    ])
    for addr, value in ((0x09A2, START_ITEMS), (0x09A4, START_ITEMS), (0x09A6, START_BEAMS),
                        (0x09A8, START_BEAMS), (0x09C6, START_MISSILES), (0x09C8, START_MISSILES)):
        routine += bytes([0xA9, value & 0xFF, value >> 8, 0x8D, addr & 0xFF, addr >> 8])  # LDA #v; STA addr
    # Save right away, like vanilla does when the intro starts ($8B:C100). Without this the slot
    # stays empty and "continue" after a game over loads vanilla Crateria instead of the frigate.
    routine += bytes([0xAD, 0x52, 0x09,                 # LDA $0952 (selected save slot)
                      0x22, 0x00, 0x80, 0x81])          # JSL $818000 (SaveToSram)
    routine += bytes([0x60])
    routine = bytes(routine)
    if rom.read(NEW_GAME_ROUTINE, len(routine)) != b"\xFF" * len(routine):
        raise RuntimeError("$82:F70F não está livre")
    rom.write(NEW_GAME_ROUTINE, routine)
    bank82 = Allocator(rom, NEW_GAME_ROUTINE + len(routine), 0x82FFFF, "$82")
    if rom.read(NEW_GAME_PATCH_SITE, 3) != bytes([0xA9, 0x1E, 0x00]):
        raise RuntimeError("bytes inesperados em $82:EED9")
    rom.write(NEW_GAME_PATCH_SITE, bytes([0x4C, NEW_GAME_ROUTINE & 0xFF, (NEW_GAME_ROUTINE >> 8) & 0xFF]))

    # areas without their own pause map yet (the Tallon until 07f) keep the vanilla tables and list
    write_map_save_lists(rom, {area.number: write_pause_map(rom, area, bank82) for area in AREAS if area.pause_map})
    areaselect.apply(rom, bank82)
    bosses.parasite_queen(rom)
    queen = queen_art.apply(rom, lambda b: fixed.put(b, "Parasite Queen (tileset 4)"))   # her own shape (BG2 tiles, tilemaps, hitboxes)
    # specs/12d: tileset $0C (the Chozo Ruins' bricks) gets its sandstone line in a copy of its palette (last of the fixed blobs, so
    # none of the earlier ones moves); no room of ours
    # nor any attract demo uses it (validate.check_ruins_in_rom)
    if ruins.RUINS_TILESET in recolored:
        raise RuntimeError(f"tileset {ruins.RUINS_TILESET:02X} recolorido também por uma área")
    # specs/12f: with the purple wave door's line (beamdoors.RUINS_PAINT_LINE) and, in the next blob, the door's 8 metatiles
    # in a copy of the tileset's metatile table (the Tower of Light's wave doors)
    sandstone = ruins_palette(rom)
    rom.w24(ruins.entry(rom) + 6, fixed.put(compress(sandstone), f"paleta do tileset {ruins.RUINS_TILESET:02X} (ruínas)"))
    # specs/14c: Flaahgra = the Spore Spawn, patched in place in $A5 (its colours, its death's BG rows = the ruins' lines,
    # no camera hook); `rom` still has the vanilla bytes there (checked)
    for addr, data in chozo_bosses.spore_spawn_patches(rom, sandstone):
        rom.write(addr, data)
    # specs/18k: the Thardus = the Bomb Torizo, patched in place in $AA (the area reads as area 0, its spot, Thardus' colours);
    # `rom` still has the vanilla bytes there (checked)
    from frigate.enemies import SPECIES as _species
    # specs/19k: first the Omega Pirate's palettes (read from the vanilla tables) and the loads' selectors by area, then the
    # Thardus' patches (which recolour the tables in place); the two copies share the Torizo's spot (validate.check_torizo)
    for addr, data in chozo_bosses.omega_patches(rom, bank_aa.put):
        rom.write(addr, data)
    for addr, data in chozo_bosses.torizo_patches(rom, _species["thardus"].fixed):
        rom.write(addr, data)
    rom.w24(ruins.entry(rom), fixed.put(compress(ruins_metatiles(rom)), f"metatiles do tileset {ruins.RUINS_TILESET:02X} (ruínas)"))
    # specs/16: the title screen: no attract demos, and the logo says METROID PRIME (its graphic: last of the fixed blobs)
    title.apply(rom, lambda b: fixed.put(b, "logo do título (METROID PRIME)"))
    # specs/17d: the Magmoor's tilesets $09 (hot) and $0A (cool): each palette's copy with the Magmoor colours and the purple
    # door's line, and one copy of the metatile table they share with the purple door's metatiles (after the title's logo, so
    # no earlier blob moves); no room of ours outside the Magmoor uses them (validate.check_lava_in_rom)
    for ts in lava.TILESETS:
        if ts in recolored:
            raise RuntimeError(f"tileset {ts:02X} recolorido também por uma área")
        rom.w24(lava.entry(rom, ts) + 6, fixed.put(compress(lava_palette(rom, ts)), f"paleta do tileset {ts:02X} (Magmoor)"))
    table_at = fixed.put(compress(lava_metatiles(rom)), "metatiles dos tilesets 09/0A (Magmoor)")
    for ts in lava.TILESETS:
        rom.w24(lava.entry(rom, ts), table_at)
    # specs/18d: Phendrana's three looks (smlib/ice.py), after the Magmoor's blobs (no earlier blob moves): entries $01 (snow),
    # $1C (icy ruins) and $1B (labs), each repointed at its graphics, a metatile table (the snow's own copy; the Chozo's $0C
    # copy; tileset 4's copy) and its own palette copy. No room of ours outside area 4 uses them (validate.check_ice_in_rom).
    for ts in ice.TILESETS:
        if ts in recolored:
            raise RuntimeError(f"tileset {ts:02X} recolorido também por uma área")
    vanilla = Rom.load(BASE)   # the palettes and the table from the vanilla bytes (tileset 4's palette is the frigate's by now)
    ice_tables = {ice.SNOW_TILESET: fixed.put(compress(ice_metatiles(vanilla)), "metatiles do tileset 01 (neve)"),
                  ice.RUINS_TILESET: rom.u24(ruins.entry(rom)),
                  ice.LAB_TILESET: rom.u24(ice.entry(rom, beamdoors.PAINT_TILESET))}
    for ts in ice.TILESETS:
        e = ice.entry(rom, ts)
        rom.w24(e, ice_tables[ts])
        rom.w24(e + 3, vanilla.u24(ice.entry(vanilla, ice.SOURCE[ts]) + 3))   # the source's vanilla graphics
        rom.w24(e + 6, fixed.put(compress(ice_palette(vanilla, ts)), f"paleta do tileset {ts:02X} (gelo)"))
    # specs/19d: the Mines' two looks (smlib/mines.py), in the test build and (specs/19e) once area 5 has rooms: entries $0E (pirate
    # base) and $08 (rock and fungus), each repointed at its source's vanilla graphics, a painted copy of the source's metatile table
    # and its own palette copy, after every other fixed blob. No room of ours outside area 5 uses them (validate.check_mines_in_rom,
    # on both ROMs).
    if test_19d or any(a.number == MINES_AREA and a.rooms for a in AREAS):
        for ts in mines.TILESETS:
            if ts in recolored:
                raise RuntimeError(f"tileset {ts:02X} recolorido também por uma área")
            e = mines.entry(rom, ts)
            rom.w24(e, fixed.put(compress(mines_metatiles(vanilla, ts)), f"metatiles do tileset {ts:02X} (mina)"))
            rom.w24(e + 3, vanilla.u24(mines.entry(vanilla, mines.SOURCE[ts]) + 3))   # the source's vanilla graphics
            rom.w24(e + 6, fixed.put(compress(mines_palette(vanilla, ts)), f"paleta do tileset {ts:02X} (mina)"))
    # specs/20d: the Impact Crater's look (impact/style.py), in the test build and once a crater room exists: entry $03 pointed at the
    # Mines' rock's ($08) metatile table and graphics (shared) and at its own palette, after every other fixed blob
    # (validate.check_impact_style, on both ROMs).
    if test_20d or any(r.key.startswith("impact_") for a in AREAS for r in a.rooms):
        if impact_style.TILESET in recolored or rom.read(mines.entry(rom, impact_style.SOURCE), 9) == \
                vanilla.read(mines.entry(vanilla, impact_style.SOURCE), 9):
            raise RuntimeError(f"tileset {impact_style.TILESET:02X} recolorido por uma área, ou o {impact_style.SOURCE:02X} "
                               f"(rocha da mina) não escrito")
        e, src = mines.entry(rom, impact_style.TILESET), mines.entry(rom, impact_style.SOURCE)
        rom.w24(e, rom.u24(src))
        rom.w24(e + 3, rom.u24(src + 3))
        rom.w24(e + 6, fixed.put(compress(impact_style.palette(vanilla)), f"paleta do tileset {impact_style.TILESET:02X} (cratera)"))

    # Time up outside Ceres must be a game over. Vanilla picks "Ceres explodes" unless event $0E
    # (Zebes timebomb) is set, which our escape never sets: decide by area instead.
    if rom.read(TIME_UP_CHECK, len(TIME_UP_VANILLA)) != TIME_UP_VANILLA:
        raise RuntimeError(f"bytes inesperados em ${TIME_UP_CHECK:06X}")
    rom.write(TIME_UP_CHECK, TIME_UP_PATCH)

    for p in rooms.values():
        print(f"  {p.room.key:12} ${p.header:06X}  portas {[f'${e:06X}' for e in p.door_entries]}"
              + (f"  elevador (saída, plataforma) {[f'${e:06X}' for e in p.elevator_entries]}" if p.elevator_entries else ""))
    for area in AREAS:
        parts = [f"spawn: estação {st.index} da área {area.number} em ${addr:06X}" if st.index == SPAWN_STATION
                 else f"chegada da fragata: estação ${st.index:02X} ({st.room}) em ${addr:06X}"
                 if area is TALLON and st.index == ESCAPE_ARRIVAL_STATION
                 else f"save: estação {st.index} ({st.room}) em ${addr:06X}" for st, addr in stations[area.key]]
        print("  " + "; ".join(parts))
    print(f"  livre: $8F até ${bank8f.ptr:06X}, $83 até ${bank83.ptr:06X}, $A1 até ${bank_a1.ptr:06X}, "
          f"$B4 até ${bank_b4.ptr:06X}, $A0 até ${bank_a0.ptr:06X}, $A3 até ${bank_a3.ptr:06X}, $A2 até ${bank_a2.ptr:06X}, "
          f"$A6 até ${bank_a6.ptr:06X}, $82 até ${bank82.ptr:06X}, $B2 até ${bank_b2.ptr:06X}, $AA até ${bank_aa.ptr:06X}")
    print("  $8F recuperado (specs/12a): " + ", ".join(f"${lo:06X}-${hi:06X} {used}/{hi - lo + 1} bytes usados"
                                                       for lo, hi, used in bank8f.reclaimed_used()))
    print("  $A1 recuperado (specs/19a): " + ", ".join(f"${lo:06X}-${hi:06X} {used}/{hi - lo + 1} bytes usados"
                                                       for lo, hi, used in bank_a1.reclaimed_used()))
    for alloc in (level_alloc, fixed):
        print(f"  alocador {alloc.name} (${alloc.start:06X}-${alloc.end:06X}): {len(alloc.blobs)} blobs, "
              f"{sum(n for _, _, n in alloc.blobs)} bytes usados, livres {alloc.free()} a partir de "
              f"${pc_to_snes(alloc.pc):06X}" + (f" (enchimento de teste: {pad} bytes)" if alloc is level_alloc and pad else ""))
    for key, addr, size in crossings(level_alloc.blobs):
        print(f"  AVISO nível de {key} cruza banco: ${addr:06X} + {size} bytes")
    print(f"  portas de feixe: {beam_bytes} bytes no $84 a partir de ${beamdoors.START:06X} "
          f"(PLMs {', '.join(f'{b} {s} ${v:04X}' for (b, s), v in beamdoors.PLM.items())})")
    print(f"  toque no item (specs/13): busca em ${itemtouch.SITE:06X} -> rotina em ${itemtouch.FIND:06X}; tiro na porta de cor "
          f"(specs/12g2): busca em ${itemtouch.DOOR_SITE:06X} -> rotina em ${itemtouch.DOOR_FIND:06X} ({touch_bytes} bytes no $84)")
    print(f"  Meta Ridley: espécie ${ridley:06X}")
    print(f"  arenas (specs/14b): rotina ${chozo_bosses.ROUTINE:06X} ({len(code)} bytes) + tabela ({len(arena_table)} bytes), "
          f"chamada ${0x8F0000 | arena_stub:06X}")
    print(f"  timer: início ${timer_start:06X}, parada ${timer_stop:06X}")
    print(f"  Parasite Queen: {queen['tiles']} tiles, gráficos do tileset {FRIGATE.tileset} em ${queen['gfx']:06X} "
          f"({queen['gfx_bytes']} bytes)")
    manifest = {p.room.key: {"header": p.header, "width": p.room.width, "height": p.room.height,
                             "prime": p.room.prime, "name": p.room.name, "states": p.states,
                             "doors": p.door_entries, "level": [rom.u24(p.states[0]), len(levels[p.room.key])],
                             **({"elevator": p.elevator_entries} if p.elevator_entries else {})}
                for p in rooms.values()}
    manifest[RIDLEY_ROOM]["meta_ridley"] = ridley
    manifest[BOSS_ROOM]["parasite_queen"] = queen
    manifest["banks"] = {"level": level_alloc.info(), "fixed": fixed.info(), "level_pad": pad}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return rom


TEST_12G_DIR = ROOT / "build/teste-12g"   # specs/12g: the test build's ROM and manifest (the game's are not touched)
TEST_17D_DIR = ROOT / "build/teste-17d"   # specs/17d: the lava test build's
TEST_18D_DIR = ROOT / "build/teste-18d"   # specs/18d: the ice looks' test build's
TEST_19D_DIR = ROOT / "build/teste-19d"   # specs/19d: the Mines looks' test build's
TEST_20D_DIR = ROOT / "build/teste-20d"   # specs/20d: the crater look's test build's
TEST_21B_DIR = ROOT / "build/teste-21b"   # specs/21b: the Prime beam colours' test build


def main() -> None:
    """Usage: build.py [--cruzar-banco SALA | --teste-12g | --teste-17d | --teste-18d | --teste-19d | --teste-20d | --teste-21b]  (test builds: SALA's level across a bank boundary,
    specs/09c; the new locks' test room, specs/12g, written to build/teste-12g/ only; the lava test rooms, specs/17d, to
    build/teste-17d/ only; the ice looks' test area, specs/18d, to build/teste-18d/ only; the Mines looks' test area, specs/19d, to
    build/teste-19d/ only; the crater look, specs/20d, to build/teste-20d/ only)"""
    args = sys.argv[1:]
    if args == ["--teste-21b"]:   # specs/21b: beam colours from the Prime (tools/beam21b.py), this test build only
        from beam21b import apply as beam_colours
        TEST_21B_DIR.mkdir(parents=True, exist_ok=True)
        rom = build(out_dir=TEST_21B_DIR)
        beam_colours(rom)
        rom.save(TEST_21B_DIR / OUT.name)
        print(f"ROM de teste (specs/21b): {(TEST_21B_DIR / OUT.name).relative_to(ROOT)}")
        return
    if args == ["--teste-20d"]:   # specs/20d
        TEST_20D_DIR.mkdir(parents=True, exist_ok=True)
        rom = build(test_20d=True, out_dir=TEST_20D_DIR)
        rom.save(TEST_20D_DIR / OUT.name)
        print(f"ROM de teste (specs/20d): {(TEST_20D_DIR / OUT.name).relative_to(ROOT)}")
        return
    if args == ["--teste-19d"]:
        TEST_19D_DIR.mkdir(parents=True, exist_ok=True)
        rom = build(test_19d=True, out_dir=TEST_19D_DIR)
        rom.save(TEST_19D_DIR / OUT.name)
        print(f"ROM de teste (specs/19d): {(TEST_19D_DIR / OUT.name).relative_to(ROOT)}")
        return
    if args == ["--teste-18d"]:
        TEST_18D_DIR.mkdir(parents=True, exist_ok=True)
        rom = build(test_18d=True, out_dir=TEST_18D_DIR)
        rom.save(TEST_18D_DIR / OUT.name)
        print(f"ROM de teste (specs/18d): {(TEST_18D_DIR / OUT.name).relative_to(ROOT)}")
        return
    if args == ["--teste-17d"]:
        TEST_17D_DIR.mkdir(parents=True, exist_ok=True)
        rom = build(test_17d=True, out_dir=TEST_17D_DIR)
        rom.save(TEST_17D_DIR / OUT.name)
        print(f"ROM de teste (specs/17d): {(TEST_17D_DIR / OUT.name).relative_to(ROOT)}")
        return
    if args == ["--teste-12g"]:
        TEST_12G_DIR.mkdir(parents=True, exist_ok=True)
        rom = build(test_12g=True, out_dir=TEST_12G_DIR)
        rom.save(TEST_12G_DIR / OUT.name)
        print(f"ROM de teste (specs/12g): {(TEST_12G_DIR / OUT.name).relative_to(ROOT)}")
        return
    if args and (args[0] != "--cruzar-banco" or len(args) != 2):
        raise SystemExit("uso: build.py [--cruzar-banco SALA | --teste-12g | --teste-17d | --teste-18d | --teste-19d | --teste-20d | --teste-21b]")
    rom = build(cross_room=args[1] if args else None)
    OUT.parent.mkdir(exist_ok=True)
    rom.save(OUT)
    ips = OUT.with_suffix(".ips")
    subprocess.run([str(FLIPS), "--create", "--ips", str(BASE), str(OUT), str(ips)], check=True,
                   stdout=subprocess.DEVNULL)
    print(f"ROM: {OUT.relative_to(ROOT)}  patch: {ips.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

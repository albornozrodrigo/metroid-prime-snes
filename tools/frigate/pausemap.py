"""Pause map of one area (frigate = area 3 today), generated from its rooms (tools/areas.py).

Formats (C refs in vendor/sm/src, details in research/sm_room_format.md section 12):
  - Tilemap: 64x32 tiles of 8x8, as two 32x32 pages (x 0-31, then x 32-63), one word per tile.
    Each room screen is one tile, at column map_x + screen_x and row map_y + screen_y + 1
    (the game adds 1 to the row: C `MarkMapTileAsExplored` / `UpdateMinimap`).
  - Bit masks (explored tiles in WRAM, map-station reveal in ROM): 0x100 bytes, same layout,
    4 bytes per row, MSB = leftmost tile.
  - Icons: map pixel (tile * 8) of the tile's top-left corner.

Vanilla draws room outlines only (no door marks), with this tile set (pause BG1 tiles at $B6:8000):
walls on the listed sides, other orientations by flipping. Palette 3; the game clears bit $400
(palette 2) on explored tiles.

specs/10c: a screen of solid rock from edge to edge (`solid_screens`) is not drawn (BLANK) and its neighbours
get a wall on that side, so the map shows the room's shape (before, the box: a room with rock screens showed
open sides there). The reveal mask, and with it the save list, still covers the whole box.
"""
from __future__ import annotations

import struct

from .rooms import RoomDef

MAP_W, MAP_H = 64, 32
BLANK = 0x001F
PALETTE = 0x0C00
H, V = 0x4000, 0x8000

WALL_TILES = {
    "": 0x1B,
    "T": 0x26, "B": 0x26 | V, "L": 0x27 | H, "R": 0x27,
    "LR": 0x23, "TB": 0x22,
    "LT": 0x25, "RT": 0x25 | H, "LB": 0x25 | V, "RB": 0x25 | H | V,
    "LRT": 0x24, "LRB": 0x24 | V, "LTB": 0x21, "RTB": 0x21 | H,
    "LRTB": 0x20,
}
SAVE_ROOM_TILE = 0x4D   # one-screen box with an "S", used by every vanilla save room


def cells(room: RoomDef):
    """(screen_x, screen_y, tile_x, tile_y) for each screen of the room."""
    for sx in range(room.width):
        for sy in range(room.height):
            yield sx, sy, room.map_x + sx, room.map_y + sy + 1


def tile_index(tx: int, ty: int) -> int:
    return (tx >> 5) * 0x400 + ty * 32 + (tx & 31)


def bit(tx: int, ty: int) -> tuple[int, int]:
    return (tx >> 5) * 128 + ty * 4 + ((tx & 31) >> 3), 0x80 >> (tx & 7)


def icon_xy(room: RoomDef, screen_x: int = 0, screen_y: int = 0) -> tuple[int, int]:
    return (room.map_x + screen_x) * 8, (room.map_y + screen_y + 1) * 8


def out_of_bounds(room: RoomDef) -> bool:
    return any(not (0 <= tx < MAP_W and 0 <= ty < MAP_H) for _, _, tx, ty in cells(room))


SOLID = 0x8   # block type of solid rock


def solid_screens(room: RoomDef) -> frozenset[tuple[int, int]]:
    """Screens (sx, sy) of the room that are solid rock from edge to edge (every block of type $8): Samus never
    goes there, so the map leaves them out of the room's shape (specs/10c)."""
    l1, _ = room.level().build_blocks()
    wb = room.width * 16
    return frozenset((sx, sy) for sy in range(room.height) for sx in range(room.width)
                     if all(l1[(sy * 16 + y) * wb + sx * 16 + x] >> 12 == SOLID for y in range(16) for x in range(16)))


def room_tile(room: RoomDef, sx: int, sy: int, solid: frozenset[tuple[int, int]] | None = None) -> int:
    """Map tile of screen (sx, sy): a wall on each side whose neighbour is outside the room or a solid screen
    (specs/10c; before, only the room's box edges had walls). BLANK for a solid screen."""
    if room.save_station and room.width == room.height == 1:
        return PALETTE | SAVE_ROOM_TILE
    if solid is None:
        solid = solid_screens(room)
    if (sx, sy) in solid:
        return BLANK

    def wall(nx: int, ny: int) -> bool:
        return not (0 <= nx < room.width and 0 <= ny < room.height) or (nx, ny) in solid

    walls = "".join(s for s, (nx, ny) in (("L", (sx - 1, sy)), ("R", (sx + 1, sy)),
                                          ("T", (sx, sy - 1)), ("B", (sx, sy + 1))) if wall(nx, ny))
    return PALETTE | WALL_TILES[walls]


def build(rooms: list[RoomDef]) -> tuple[bytes, bytes]:
    """Return (tilemap 0x1000 bytes, map-station reveal mask 0x100 bytes)."""
    words = [BLANK] * (MAP_W * MAP_H)
    reveal = bytearray(0x100)
    taken = set()
    for r in rooms:
        solid = solid_screens(r)
        for sx, sy, tx, ty in cells(r):
            i = tile_index(tx, ty)
            if i in taken:
                raise ValueError(f"{r.key}: tile do mapa ({tx},{ty}) já ocupado")
            taken.add(i)
            words[i] = room_tile(r, sx, sy, solid)
            # the reveal mask (and with it the save list, tools/frigate/mapsave.py) keeps the whole box: a solid
            # screen's BLANK tile shows nothing, and the SRAM layout stays as it was (specs/10c)
            byte, mask = bit(tx, ty)
            reveal[byte] |= mask
    return struct.pack(f"<{len(words)}H", *words), bytes(reveal)

"""specs/17d: the lava test build's rooms (tools/build.py --teste-17d -> build/teste-17d/), never the game's ROM.

No region of the Magmoor is built yet (17f is region A), but the lava, the two palettes and the purple wave door in tilesets
$09/$0A must be measured and seen in the emulator first (epic 17: "física e dano medidos na 17d antes de qualquer sala depender
deles"). The test build adds two rooms to the Magmoor's area 2, hung on a door the game doesn't have: specs/17e-17h on the
Tallon West transport's (P16) east door R0, until region C (specs/17i) built the Twin Fires Tunnel there; since 17i on the
decorative transport to the Mines West (P26) by a door R1 on the east of its bottom screen (its hall reaches that wall), on the
pause map east of it (columns 60-62 of row 11: in the bytes of the explored-map save list, the whole table's, that the P26
already has); the tests get in by door teleport:

  - COOL (2x1, tileset $0A, cool): a hall (floor row 10) over a lava pit with three floors at three depths, its surface on row
    LAVA_ROW (block rows 11 and down are lava): feet 3 rows under the surface (columns 8-9 and 14-15, fully under), 2 (10-11)
    and 1 (12-13). Its west door (to the host) is a wave door on its side, its east door leads to HOT.
  - HOT (1x1, tileset $09, hot: the heat and the lava glows of area 2's palette FX list): a hall over a small lava pit, its
    west door (to COOL) a wave door on its side.

tests/run_tests.py lava_medida measures there the damage with no suit, the Varia, the Gravity Suit (and the heat on top in HOT),
the jump out of the lava from each depth (smlib/reach.py LAVA_*), and porta_de_onda_lava the purple caps in $0A and $09.
"""
from __future__ import annotations

from frigate.rooms import DoorLink, RoomDef
from smlib import lava
from smlib.canvas import Canvas
from tallon.rooms import LOCK_OF, WAVE

COOL, HOT = "teste_lava_fria", "teste_lava_quente"
HOST = "magmoor_transport_mines_west"    # specs/17i: the Magmoor's P26 (17e-17h: the P16, until its R0 door opened)
HOST_DOOR = ("R", 1)                     # the host's door to COOL (the game has none there)
LAVA_ROW = 11
# (first column, last column, feet row) of the pit's floors in COOL: feet rows 13, 12, 11 = 3, 2, 1 rows under the surface
PIT_FLOORS = ((8, 9, 13), (10, 11, 12), (12, 13, 11), (14, 15, 13))
HOT_PIT = (6, 9, 12)


def cool_room() -> RoomDef:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    for x0, x1, feet in PIT_FLOORS:
        c.carve(x0, 10, x1, feet)
    return RoomDef(COOL, -1, "Teste da lava (fria)", 2, 1, 60, 11, c, style=lava.LAVA_COOL, tileset=lava.COOL_TILESET,
                   lava=LAVA_ROW)


def hot_room() -> RoomDef:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 9)
    x0, x1, feet = HOT_PIT
    c.carve(x0, 10, x1, feet)
    return RoomDef(HOT, -1, "Teste da lava (quente)", 1, 1, 62, 11, c, style=lava.LAVA_HOT, tileset=lava.HOT_TILESET,
                   lava=LAVA_ROW, heat=True)


def link(a: RoomDef, sa: str, na: int, b: RoomDef, sb: str, nb: int, lock_a: str | None = None) -> None:
    da, db = DoorLink(sa, na, b.key, lock=lock_a), DoorLink(sb, nb, a.key)
    a.doors.append(da)
    b.doors.append(db)
    da.to_door, db.to_door = len(b.doors) - 1, len(a.doors) - 1


def apply(magmoor):
    """Add the test rooms to `magmoor` (the Magmoor's AreaDef, changed in place), linked to its HOST room's HOST_DOOR (a wall
    in the game: specs/17i, the P26's east wall of its bottom screen; its L1 door leads to the Workstation Tunnel). Returns the
    area."""
    host = magmoor.by_key()[HOST]
    if any((d.side, d.screen) == HOST_DOOR for d in host.doors):
        raise RuntimeError(f"{HOST}: esperado sem a porta {HOST_DOOR} (parede no jogo), achado {host.doors}")
    cool, hot = cool_room(), hot_room()
    link(cool, "L", 0, host, *HOST_DOOR, lock_a=LOCK_OF[WAVE])
    link(hot, "L", 0, cool, "R", 0, lock_a=LOCK_OF[WAVE])
    magmoor.rooms = magmoor.rooms + [cool, hot]
    return magmoor

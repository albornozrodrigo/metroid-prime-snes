"""specs/19d: the Mines looks' test build (tools/build.py --teste-19d -> build/teste-19d/), never the game's ROM.

The two looks of the Mines (smlib/mines.py), their phazon blue and the beam door caps must be seen in the emulator before a region
depends on them (epic 19, the 19d row: "emulador: a tampa de plasma abre"). specs/19d had an area 5 of its own; since specs/19e
(the AreaDef MINES) the test build adds the four rooms to a copy of the Mines' area 5 (area(): it takes MINES' place in
areas.AREAS only inside that build, as phendrana/testrooms.py does to Phendrana's), in a row, west to east, on the pause map's row
MAP_Y (under the Mines' map, rows 8-23, specs/19c; their explored-map bytes are added to the area's save list in this build only),
with a load station of their own (TEST_STATION, a save slot no Mines save takes) in ENTRY; the tests get there by loading it by RAM
(game state 6, as a continue), as specs/18d's did:

  ENTRY (1x1, pirate base $0E) -R0/L0- BASE (2x1, pirate base) -R0/L0- ROCK (2x1, rock and fungus $08) -R0/L0- END (1x1, rock).

Doors: BASE's west door is an ice door (green) on its side, its east door a wave door (purple); ROCK's west door is a plasma door
(orange) on its side, its east door a wave door: each look shows the purple cap and another colour, and the plasma cap of the mine
is the one tests/run_tests.py porta_de_plasma_mina opens. Each look room has a ledge, a platform and a bump hanging from the ceiling, so
the photos show the style's floors, walls, corners and platforms.
"""
from __future__ import annotations

import copy

from areas import MINES, AreaDef, LoadStation
from frigate.rooms import DoorLink, RoomDef
from smlib import mines
from smlib.canvas import Canvas
from tallon.rooms import ICE, LOCK_OF, PLASMA, WAVE

ENTRY, BASE, ROCK, END = "teste_mina_entrada", "teste_base_pirata", "teste_mina_de_rocha", "teste_mina_fim"
MAP_Y = 26                       # under the Mines' map (rows 8-23, specs/19c)
MAP_X = 3                        # ENTRY's column; the others follow east
SPAWN = (5 * 16, 10 * 16 - 24)   # ENTRY: Samus on its floor (row 10)
TEST_STATION = 7                 # the last save slot of area 5 (specs/19e: station 0 is the Mines' arrival; saves 1-3 from 19f on)


def hall(width: int, features: bool) -> Canvas:
    """A hall one screen tall, floor on row 10, rows 3-9 open; `features`: a ledge, a platform and a bump in the ceiling in the
    middle of the room (away from the doors' 8 blocks)."""
    c = Canvas(width, 1)
    c.carve(1, 3, width * 16 - 2, 9)
    if features:
        c.fill(10, 8, 13, 9)          # a ledge 2 blocks high
        c.platform(16, 19, 6)         # a '=' platform
        c.fill(21, 3, 23, 4)          # a bump hanging from the ceiling
    return c


def look(key: str, name: str, width: int, map_x: int, tileset: int, **kw) -> RoomDef:
    bg, layer2 = mines.BACKGROUND[tileset]
    return RoomDef(key, -1, name, width, 1, map_x, MAP_Y, hall(width, width > 1), tileset=tileset, library_bg=bg,
                   layer2=layer2, style=mines.STYLE_OF[tileset], **kw)


def link(a: RoomDef, b: RoomDef, lock_a: str | None = None, lock_b: str | None = None) -> None:
    """a's east door R0 <-> b's west door L0."""
    da, db = DoorLink("R", 0, b.key, lock=lock_a), DoorLink("L", 0, a.key, lock=lock_b)
    a.doors.append(da)
    b.doors.append(db)
    da.to_door, db.to_door = len(b.doors) - 1, len(a.doors) - 1


def rooms() -> list[RoomDef]:
    entry = look(ENTRY, "Teste da mina (entrada)", 1, MAP_X, mines.BASE_TILESET)
    base = look(BASE, "Teste da base pirata", 2, MAP_X + 1, mines.BASE_TILESET)
    rock = look(ROCK, "Teste da mina de rocha", 2, MAP_X + 3, mines.ROCK_TILESET)
    end = look(END, "Teste da mina (fim)", 1, MAP_X + 5, mines.ROCK_TILESET)
    link(entry, base, lock_b=LOCK_OF[ICE])
    link(base, rock, lock_a=LOCK_OF[WAVE], lock_b=LOCK_OF[PLASMA])
    link(rock, end, lock_a=LOCK_OF[WAVE])
    return [entry, base, rock, end]


def area() -> AreaDef:
    """The test build's area 5: a copy of the Mines' (areas.MINES, a new one each call: nothing of the game's areas changes) with
    the test rooms, their explored-map bytes in its save list (save_map_rooms) and the load station TEST_STATION in ENTRY."""
    out = copy.copy(MINES)   # the attributes changed below get new lists: MINES' own stay as they are
    if any(st.index == TEST_STATION for st in out.load_stations):
        raise RuntimeError(f"mines: estação {TEST_STATION} já usada, a ROM de teste da mina precisa de outra")
    rs = rooms()
    out.save_map_rooms = (out.save_map_rooms or out.rooms) + rs
    out.rooms = out.rooms + rs
    out.load_stations = out.load_stations + [LoadStation(TEST_STATION, ENTRY, *SPAWN)]
    return out

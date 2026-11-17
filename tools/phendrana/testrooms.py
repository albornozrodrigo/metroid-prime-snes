"""specs/18d: the ice looks' test build (tools/build.py --teste-18d -> build/teste-18d/), never the game's ROM.

The three looks, the snow and the doors must be seen and measured in the emulator before a region depends on them (epic 18:
"neve medida numa ROM de teste", as the lava in 17d). The test build adds five rooms in a row, west to east, to Phendrana's area
4 (specs/18e: to the AreaDef PHENDRANA, changed in place, as magmoor/testrooms.py does to the Magmoor's; 18d had an area 4 of its
own), on the pause map's row MAP_Y under every room of Phendrana's table (their explored-map bytes are added to the area's save
list in this build only), with a load station of their own (TEST_STATION, a save slot no Phendrana save will take in this build);
the tests get there by loading it by RAM (game state 6, as a continue), Samus standing in RAIN:

  RAIN (1x1, snow look $01, the rain FX: ice.RAIN, for the comparison photo) -R0/L0- SNOW (2x1, $01, snow = ice.SPORES)
  -R0/L0- RUINS (2x1, icy ruins $1C, snow) -R0/L0- LAB (2x1, labs $1B, no snow) -R0/L0- WATER (2x1, $01, flooded: build.WATER_FX).

Doors: each look room's east door (R0) is a purple wave door on its side; the west doors of RUINS and LAB are an ice door (green)
and a plasma door (orange) on their side, so each look shows the purple cap and another colour. WATER's floor is row 13, open up to row 3
and 2 screens wide (the jumps' room: as the Savestation's, tests pulo_na_agua_medido): tests agua_medida_area_4 measures there.
"""
from __future__ import annotations

from areas import LoadStation
from frigate.rooms import DoorLink, RoomDef
from smlib import ice
from smlib.canvas import Canvas
from tallon.rooms import ICE, LOCK_OF, PLASMA, WAVE

RAIN, SNOW, RUINS, LAB, WATER = ("teste_chuva", "teste_neve", "teste_ruinas_de_gelo", "teste_laboratorio", "teste_agua")
MAP_Y = 25                       # under Phendrana's table (rows 8-22, specs/18c)
MAP_X = 3                        # RAIN's column; the others follow east
SPAWN = (5 * 16, 10 * 16 - 24)   # RAIN: Samus on its floor (row 10)
TEST_STATION = 7                 # the last save slot of area 4 (Phendrana's saves are stations 1-4, specs/18f on)


def hall(width: int) -> Canvas:
    """A hall one screen tall, floor on row 10, rows 3-9 open."""
    c = Canvas(width, 1)
    c.carve(1, 3, width * 16 - 2, 9)
    return c


def look(key: str, name: str, width: int, map_x: int, tileset: int, **kw) -> RoomDef:
    bg, layer2 = ice.BACKGROUND[tileset]
    style = {ice.SNOW_TILESET: ice.SNOW, ice.RUINS_TILESET: ice.ICE_RUINS}.get(tileset)
    extra = {"style": style} if style else {}
    return RoomDef(key, -1, name, width, 1, map_x, MAP_Y, kw.pop("canvas", None) or hall(width), tileset=tileset,
                   library_bg=bg if isinstance(bg, int) else None, layer2=layer2, **extra, **kw)


def water_room() -> RoomDef:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 12)
    return look(WATER, "Teste da água (área 4)", 2, MAP_X + 7, ice.SNOW_TILESET, canvas=c, water=True)


def link(a: RoomDef, b: RoomDef, lock_a: str | None = None, lock_b: str | None = None) -> None:
    """a's east door R0 <-> b's west door L0."""
    da, db = DoorLink("R", 0, b.key, lock=lock_a), DoorLink("L", 0, a.key, lock=lock_b)
    a.doors.append(da)
    b.doors.append(db)
    da.to_door, db.to_door = len(b.doors) - 1, len(a.doors) - 1


def rooms() -> list[RoomDef]:
    rain = look(RAIN, "Teste da chuva (neve rápida)", 1, MAP_X, ice.SNOW_TILESET, snow=ice.RAIN)
    snow = look(SNOW, "Teste da neve", 2, MAP_X + 1, ice.SNOW_TILESET, snow=ice.SPORES)
    ruins = look(RUINS, "Teste das ruínas de gelo", 2, MAP_X + 3, ice.RUINS_TILESET, snow=ice.SPORES)
    lab = look(LAB, "Teste do laboratório", 2, MAP_X + 5, ice.LAB_TILESET)
    water = water_room()
    link(rain, snow)
    link(snow, ruins, lock_a=LOCK_OF[WAVE], lock_b=LOCK_OF[ICE])
    link(ruins, lab, lock_a=LOCK_OF[WAVE], lock_b=LOCK_OF[PLASMA])
    link(lab, water, lock_a=LOCK_OF[WAVE])
    return [rain, snow, ruins, lab, water]


def apply(phendrana):
    """Add the test rooms to `phendrana` (Phendrana's AreaDef, changed in place): the rooms, their explored-map bytes to its save
    list (save_map_rooms) and the load station TEST_STATION in RAIN. Returns the area."""
    rs = rooms()
    if any(st.index == TEST_STATION for st in phendrana.load_stations):
        raise RuntimeError(f"phendrana: estação {TEST_STATION} já usada, a ROM de teste do gelo precisa de outra")
    phendrana.save_map_rooms = (phendrana.save_map_rooms or phendrana.rooms) + rs
    phendrana.rooms = phendrana.rooms + rs
    phendrana.load_stations = phendrana.load_stations + [LoadStation(TEST_STATION, RAIN, *SPAWN)]
    return phendrana

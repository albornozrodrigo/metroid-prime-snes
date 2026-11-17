"""The game's areas: one AreaDef per SM area the project rebuilds (specs/07a-toolchain-multi-area.md).

build.py, validate.py, preview_rooms.py and tests/run_tests.py go through AREAS instead of
importing the frigate's rooms directly. Built areas: the Frigate Orpheon (SM area 3, the Wrecked
Ship slot) and, since spec 07g, the Tallon Overworld (area 0, the Crateria slot) with the 5 rooms
of Prime's item-free path (spec 07g), since spec 07k regions B and C (20 rooms), since spec 07l
region D, the sunken frigate (34 rooms), and since spec 07m region E and Gully/Alcove: all 44 rooms of
the table (tools/tallon/rooms.py ACTIVE_ROOMS). Since spec 07f the Tallon has its own
pause map, minimap, name and explored-map save list (written over vanilla Crateria's tables). Since spec 12e the
Chozo Ruins (area 1, Brinstar's slot) have their three elevator rooms, linked to the Tallon's transports by working
elevators (ELEVATORS).

Room keys are global: the manifest and the tests use the key alone, so `all_rooms` stops on a key
used by two areas. Rooms of new areas carry the area's prefix (e.g. `tallon_reactor_core`).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from frigate import ending, mapsave, pausemap
from frigate.enemies import ENEMIES, Spawn
from frigate.props import PROPS, Prop
from frigate.rooms import ROOMS, RoomDef
from smlib import crateria
from smlib.palette import FRIGATE_ROWS
from smlib.reach import POWER_BEAM_ONLY, SPACE_JUMP_MORPH, Loadout
from tallon import rooms as tallon_rooms
from tallon.enemies import ENEMIES as TALLON_ENEMIES
from chozo import rooms as chozo_rooms
from chozo.enemies import ENEMIES as CHOZO_ENEMIES
from magmoor import rooms as magmoor_rooms
from magmoor.enemies import ENEMIES as MAGMOOR_ENEMIES
from phendrana.enemies import ENEMIES as PHENDRANA_ENEMIES
from mines.enemies import ENEMIES as MINES_ENEMIES
from phendrana import rooms as phendrana_rooms
from mines import rooms as mines_rooms
from impact import rooms as impact_rooms
from impact.enemies import ENEMIES as IMPACT_ENEMIES
from smlib import ice, lava, mines

SAVE_SAMUS_ABOVE_FLOOR = 24   # vanilla WS save room: Samus Y offset $98, pedestal top at $B0


@dataclass(frozen=True)
class LoadStation:
    index: int   # station of the area (0 = arrival / new game; 0-7 are the save slots)
    room: str    # room key
    x: int       # Samus pixel position in the room
    y: int


@dataclass
class AreaDef:
    key: str                     # short name ("frigate"); preview files are <key>_<room>.png
    number: int                  # SM area byte (frigate = 3)
    name: str                    # pause-map name, up to 12 letters A-Z
    rooms: list[RoomDef]
    tileset: int                 # default tileset of the rooms (RoomDef.tileset overrides it)
    music: tuple[int, int]       # default (song set, track) of the room states
    layer2: int                  # default BG2 scroll word
    library_bg: int | bytes      # default library background command list ($8F; bytes = a new list)
    load_stations: list[LoadStation]
    enemies: dict[str, list[Spawn]] = field(default_factory=dict)
    props: dict[str, list[Prop]] = field(default_factory=dict)
    palette_rows: tuple[int, ...] = ()   # tileset palette rows recoloured (empty = none)
    boss_room: str | None = None         # room of the pause-map boss icon
    # what Samus has when she gets here: the validator's reachability (specs/07b); the strictest
    # by default
    loadout: Loadout = POWER_BEAM_ONLY
    # the build writes the area's pause map, icons and explored-map save list (False: the vanilla
    # tables of that area stay)
    pause_map: bool = True
    # rooms whose explored-map bytes the save keeps (None = `rooms`). The Tallon keeps its whole
    # table's (specs/07f), so the save list doesn't change as regions get built
    save_map_rooms: list[RoomDef] | None = None

    def by_key(self) -> dict[str, RoomDef]:
        return {r.key: r for r in self.rooms}

    def tileset_of(self, room: RoomDef) -> int:
        return self.tileset if room.tileset is None else room.tileset

    def station_in(self, room_key: str) -> int:
        return next(s.index for s in self.load_stations if s.room == room_key)

    def map_save_bytes(self) -> list[int]:
        """Offsets of the explored-map bytes the save keeps for this area (tools/frigate/mapsave.py)."""
        rooms = self.rooms if self.save_map_rooms is None else self.save_map_rooms
        return mapsave.needed(pausemap.build(rooms)[1])


def stations_from_rooms(rooms: list[RoomDef]) -> list[LoadStation]:
    """Station 0 = the room with the spawn point; 1, 2... = rooms with a save station, in order.
    Samus stands on the save pedestal's right block, like in the vanilla save rooms."""
    out = [LoadStation(0, r.key, *r.spawn) for r in rooms if r.spawn]
    if len(out) != 1:
        raise ValueError(f"a área precisa de exatamente uma sala com spawn (tem {len(out)})")
    for r in rooms:
        if r.save_station:
            px, floor = r.save_station
            out.append(LoadStation(len(out), r.key, (px + 1) * 16, floor * 16 - SAVE_SAMUS_ABOVE_FLOOR))
    if len(out) > 8:
        raise ValueError(f"{len(out)} estações; uma área tem no máximo 8 no save")
    return out


FRIGATE = AreaDef(
    key="frigate", number=3, name="FRIGATE", rooms=ROOMS,
    tileset=4,
    music=(0x30, 0x05),          # Wrecked Ship song set / track
    layer2=0xC1C1,               # library background, like the vanilla Wrecked Ship rooms
    library_bg=0xE117,           # vanilla WS background command list ($8F:E117)
    load_stations=stations_from_rooms(ROOMS),
    enemies=ENEMIES, props=PROPS, palette_rows=FRIGATE_ROWS, boss_room="reactor_core",
    loadout=SPACE_JUMP_MORPH,    # Prime's frigate: Samus still has her suit upgrades
)

# Tallon load stations (specs/07g): the two at the Landing Site gunship, and (specs/07l) station 1 =
# the sunken frigate's Savestation (Prime's other save point, P28).
#  0 = standing on top of the ship: where the ship saves (GunshipTop_7/8 set load station 0) and
#      where a continue starts. Vanilla station 0 has Samus 31 px above the ship top's y.
#  ESCAPE_ARRIVAL_STATION ($12) = the end of the frigate (spec 05): after the Ceres escape cutscene
#      the game loads area 0 station $12 ($82:8035) and the ship comes down from the sky with
#      Samus inside, starting 17 px above her (GunshipTop_Init); vanilla has her at y $80.
ESCAPE_ARRIVAL_STATION = 0x12
ARRIVAL_Y = 0x80


def gunship_stations(rooms: list[RoomDef]) -> list[LoadStation]:
    """Station 0 and the escape arrival at the gunship; 1, 2... = rooms with a save station, in
    order, as in stations_from_rooms (specs/07l: the sunken frigate's Savestation = station 1)."""
    ship_rooms = [r for r in rooms if r.ship]
    if len(ship_rooms) != 1:
        raise ValueError(f"o Tallon precisa de exatamente uma sala com a nave (tem {len(ship_rooms)})")
    r = ship_rooms[0]
    cx, ground = r.ship
    out = [LoadStation(0, r.key, cx * 16, ending.ship_top_y(ground) - 31)]
    for s in rooms:
        if s.save_station:
            px, floor = s.save_station
            out.append(LoadStation(len(out), s.key, (px + 1) * 16, floor * 16 - SAVE_SAMUS_ABOVE_FLOOR))
    if len(out) > 8:
        raise ValueError(f"{len(out)} estações; uma área tem no máximo 8 no save")
    return out + [LoadStation(ESCAPE_ARRIVAL_STATION, r.key, cx * 16, ARRIVAL_Y)]


# Tallon Overworld (specs/07d-grafo-e-mapa-tallon.md, 07g): rooms of tallon/rooms.py ROOMS.
# Background of the surface = the Landing Site's cloudy sky (crateria.SKY_BG, a command list the
# build puts in $8F); the cave rooms set their own (tallon/rooms.py CAVE_BG).
# specs/20e: the Impact Crater lives in area 0 with the Tallon (IMPACT_CRATER_AREA, epic 20 decision 2): its built rooms
# (impact/rooms.py ROOMS) come after the Tallon's in this AreaDef (one SM area: one pause map, one load-station list, one saved
# map), each with its own look (tileset $03, the rock background: impact/style.py); the Tallon's music. Its Save Station is the
# next load station of area 0 (gunship_stations: 2). The saved map keeps both whole tables (70 of 80 bytes, specs/20c), so it
# does not change as the crater's regions get built.
TALLON_AND_CRATER = tallon_rooms.ROOMS + impact_rooms.ROOMS
TALLON = AreaDef(
    key="tallon", number=0, name="TALLON", rooms=TALLON_AND_CRATER,
    tileset=crateria.SURFACE_TILESET,
    music=crateria.LANDING_SITE_MUSIC,
    layer2=crateria.SKY_LAYER2,
    library_bg=crateria.SKY_BG,
    load_stations=gunship_stations(TALLON_AND_CRATER),
    enemies={**TALLON_ENEMIES, **IMPACT_ENEMIES},   # specs/07i: Prime's layer 0 enemies of the built rooms; 20f: the crater's
    loadout=POWER_BEAM_ONLY,     # Prime: Samus lands with the Power Beam only (no Space Jump, no Morph)
    save_map_rooms=tallon_rooms.ALL_ROOMS + impact_rooms.ALL_ROOMS,   # spec 07f: the whole table's 47 bytes; 20e: and the crater's
)

# specs/12b: the SM area slot the Chozo Ruins (specs/12) take, Brinstar's: the fewest area-specific vanilla code paths of the
# free slots 1, 2, 4 (2 = Norfair: enemy projectiles and freeze time by area; 4 = Maridia: the pause map scrolls 24 px; 1:
# one X-ray case). Confirmed by the user (specs/12, decisions).
CHOZO_AREA = 1

# specs/17b: the SM area slot the Magmoor Caverns (specs/17) take, Norfair's (user decision 6 of the epic, 01/11/2026): its
# palette FX list has SM's heat at bit 0 and 4 lava glows already (chozo/heat.py HEAT_BITS: no patch); the area's own vanilla
# code is the ice freezing enemies 300 frames instead of 400 (sm_a0.c:2751, 2789) and Ridley's fireball (sm_86.c:1163, Ridley
# lives in area 3's frigate here). specs/17e: the AreaDef MAGMOOR below.
MAGMOOR_AREA = 2

# specs/18b: the SM area slots of the last three worlds (epic 18, decision 2, option (a): "padrão aceito, a confirmar"). Only areas
# 0-5 have a saved map and a continue screen (frigate/mapsave.py; area 6 = Ceres, 7 = debug), and 0-3 are taken, so two slots for
# three worlds: Phendrana Drifts in area 4 (Maridia's: its explored-map list fits its vanilla place, 80 bytes; its own vanilla code
# is the pause map scrolling 24 px further left, sm_82.c:1811, its palette FX list $83:ACE6 = 3 Maridia objects and its animated
# tiles list $83:ACF6 = 2 Maridia entries, which no room of ours may turn on: validate.check_phendrana_slot; and Botwoon reading
# the area's boss byte); the Phazon Mines in area 5 (Tourian's: its vanilla list holds 21 bytes, so the Mines' epic moves it to
# $81 free space, mapsave.py); the Impact Crater inside area 0 with the Tallon (Prime enters it from the Tallon's Artifact Temple;
# no save nor map station; the Tallon's list, 47 of 80 bytes, has room). specs/18e: the AreaDef PHENDRANA below.
PHENDRANA_AREA = 4
MINES_AREA = 5
IMPACT_CRATER_AREA = 0

# specs/12e: the Chozo Ruins' rooms built so far: the three elevator rooms to the Tallon (tools/chozo/rooms.py ELEVATOR_ROOMS),
# dead ends until their regions come; specs/12f: region A. Sandstone bricks (tileset $0C, specs/12d).
# specs/12f: the background and the music of the vanilla rooms of tileset $0C (read from their state headers): the library
# background $8F:E25A (rooms $8F:D461 and $D4C2: decompress $BA:A69F into BG2, tiles of tileset $0C on palette line 6) with
# BG2 scroll $01C1, and Maridia's song set $1B, track $05 (rooms $D5A7, $D617, $D78F, $D7E4; the other $0C rooms keep the
# song playing: $00). Until 12e the BG2 was cleared (a list of our own, $000A ClearBG2Tilemap) and the music was green
# Brinstar's ($0F/$05) as placeholders.
# Load station 0 = the floor by the North transport's platform (epic 12: "0 = chegada"); specs/12i: 1, 2... = the rooms with
# a save station, in order (the epic: 1-3 = Save Stations 1-3; region B built Save Station 1, P22).
CHOZO_BG, CHOZO_LAYER2 = 0xE25A, 0x01C1
CHOZO_MUSIC = (0x1B, 0x05)
CHOZO_ARRIVAL = LoadStation(0, "chozo_transport_tallon_north", 4 * 16 + 8, 26 * 16 - 21)


def chozo_stations(rooms: list[RoomDef]) -> list[LoadStation]:
    """specs/12i: station 0 = the arrival (CHOZO_ARRIVAL); 1, 2... = the rooms with a save station, in order, Samus on the
    pedestal's right block (as stations_from_rooms)."""
    out = [CHOZO_ARRIVAL]
    for r in rooms:
        if r.save_station:
            px, floor = r.save_station
            out.append(LoadStation(len(out), r.key, (px + 1) * 16, floor * 16 - SAVE_SAMUS_ABOVE_FLOOR))
    if len(out) > 8:
        raise ValueError(f"{len(out)} estações; uma área tem no máximo 8 no save")
    return out


CHOZO = AreaDef(
    key="chozo", number=CHOZO_AREA, name="CHOZO", rooms=chozo_rooms.ROOMS,
    tileset=0x0C, music=CHOZO_MUSIC, layer2=CHOZO_LAYER2, library_bg=CHOZO_BG,
    load_stations=chozo_stations(chozo_rooms.ROOMS),
    loadout=POWER_BEAM_ONLY,     # what the Tallon gives before its round 1 (the North elevator is in round 0)
    save_map_rooms=chozo_rooms.ALL_ROOMS,   # the whole table's 41 bytes (specs/12c), as the Tallon keeps its 47
    enemies=CHOZO_ENEMIES,       # specs/12h: Prime's layer 0 enemies of the built rooms
)

# specs/17e: the Magmoor Caverns (area 2, Norfair's slot, specs/17b): its two elevator rooms (magmoor/rooms.py ELEVATOR_ROOMS),
# dead ends until their regions come (17f, 17h), in the lava caves' style (specs/17d: tilesets $09/$0A, background $8F:BE5A,
# Upper Norfair's music $15/$05). Load station 0 = the floor by the Chozo North elevator's platform (as the Chozo's 0, the
# arrival from the Chozo); specs/17f: 1, 2 = the rooms with a save station, in order (the epic: 1 = Save Station A, region
# A; 2 = Save Station B, region C), as the Chozo's (chozo_stations). Its explored-map save list is the whole table's
# 30 bytes (specs/17c), so it does not change as regions get built.
MAGMOOR_ARRIVAL = LoadStation(0, "magmoor_transport_chozo_north", 4 * 16 + 8, 26 * 16 - 21)


def magmoor_stations(rooms: list[RoomDef]) -> list[LoadStation]:
    """specs/17f: station 0 = the arrival (MAGMOOR_ARRIVAL); 1, 2... = the rooms with a save station, in order, Samus on the
    pedestal's right block (as chozo_stations)."""
    out = [MAGMOOR_ARRIVAL]
    for r in rooms:
        if r.save_station:
            px, floor = r.save_station
            out.append(LoadStation(len(out), r.key, (px + 1) * 16, floor * 16 - SAVE_SAMUS_ABOVE_FLOOR))
    if len(out) > 8:
        raise ValueError(f"{len(out)} estações; uma área tem no máximo 8 no save")
    return out


MAGMOOR = AreaDef(
    key="magmoor", number=MAGMOOR_AREA, name="MAGMOOR", rooms=magmoor_rooms.ROOMS,
    tileset=lava.COOL_TILESET, music=lava.MUSIC, layer2=lava.LAYER2, library_bg=lava.BACKGROUND,
    load_stations=magmoor_stations(magmoor_rooms.ROOMS),
    loadout=POWER_BEAM_ONLY,     # the weakest arrival (its elevators are first reached in round 1)
    save_map_rooms=magmoor_rooms.ALL_ROOMS,
    enemies=MAGMOOR_ENEMIES,     # specs/17g: Prime's layer 0 enemies of the built rooms
)

# specs/18e: Phendrana Drifts (area 4, Maridia's slot, specs/18b): its two elevator rooms (phendrana/rooms.py ELEVATOR_ROOMS),
# dead ends until their regions come, in specs/18d's looks (smlib/ice.py: the snow look by default, its sky and Maridia's inner
# theme $1B/$06). Load station 0 = the floor by the north elevator's platform (the P0, the arrival from the Magmoor's P13), as
# the Magmoor's 0; 1, 2... = the rooms with a save station, in order (the epic: Save Stations B, A, D, C, regions A-E). Its
# explored-map save list is the whole table's 57 bytes (specs/18c).
PHENDRANA_ARRIVAL = LoadStation(0, "phendrana_transport_magmoor_west", 4 * 16 + 8, 26 * 16 - 21)


def phendrana_stations(rooms: list[RoomDef]) -> list[LoadStation]:
    """specs/18e: station 0 = the arrival (PHENDRANA_ARRIVAL); 1, 2... = the rooms with a save station, in order (as
    magmoor_stations)."""
    out = [PHENDRANA_ARRIVAL]
    for r in rooms:
        if r.save_station:
            px, floor = r.save_station
            out.append(LoadStation(len(out), r.key, (px + 1) * 16, floor * 16 - SAVE_SAMUS_ABOVE_FLOOR))
    if len(out) > 8:
        raise ValueError(f"{len(out)} estações; uma área tem no máximo 8 no save")
    return out


PHENDRANA = AreaDef(
    key="phendrana", number=PHENDRANA_AREA, name="PHENDRANA", rooms=phendrana_rooms.ROOMS,
    tileset=ice.SNOW_TILESET, music=ice.MUSIC, layer2=ice.BACKGROUND[ice.SNOW_TILESET][1],
    library_bg=ice.BACKGROUND[ice.SNOW_TILESET][0],
    load_stations=phendrana_stations(phendrana_rooms.ROOMS),
    loadout=POWER_BEAM_ONLY,     # the weakest arrival (as the Magmoor's)
    save_map_rooms=phendrana_rooms.ALL_ROOMS,
    enemies=PHENDRANA_ENEMIES,   # specs/18g: Prime's layer 0 enemies of the built rooms
)

# specs/19e: the Phazon Mines (area 5, Tourian's slot, specs/19b): its two elevator rooms (mines/rooms.py ELEVATOR_ROOMS), dead ends
# until their regions come (19f, 19j), in specs/19d's pirate base look (smlib/mines.py: tileset $0E, background $8F:E454, Tourian's
# music $1E/$05). Load station 0 = the floor by the P0's platform (the arrival from the Tallon's P43, Prime's way in), as
# Phendrana's 0; 1, 2... = the rooms with a save station, in order (the epic: Save Stations A, B, C, regions A, B, D). Its
# explored-map save list is the whole table's 39 bytes (specs/19c), past the 21 of area 5's vanilla place: in $81 (mapsave.list_at,
# specs/19b).
MINES_ARRIVAL = LoadStation(0, "mines_transport_tallon_south", 4 * 16 + 8, 26 * 16 - 21)


def mines_stations(rooms: list[RoomDef]) -> list[LoadStation]:
    """specs/19e: station 0 = the arrival (MINES_ARRIVAL); 1, 2... = the rooms with a save station, in order (as
    phendrana_stations)."""
    out = [MINES_ARRIVAL]
    for r in rooms:
        if r.save_station:
            px, floor = r.save_station
            out.append(LoadStation(len(out), r.key, (px + 1) * 16, floor * 16 - SAVE_SAMUS_ABOVE_FLOOR))
    if len(out) > 8:
        raise ValueError(f"{len(out)} estações; uma área tem no máximo 8 no save")
    return out


MINES = AreaDef(
    key="mines", number=MINES_AREA, name="MINES", rooms=mines_rooms.ROOMS,
    tileset=mines.BASE_TILESET, music=mines.MUSIC, layer2=mines.BACKGROUND[mines.BASE_TILESET][1],
    library_bg=mines.BACKGROUND[mines.BASE_TILESET][0],
    load_stations=mines_stations(mines_rooms.ROOMS),
    loadout=POWER_BEAM_ONLY,     # the weakest arrival (as the Magmoor's)
    save_map_rooms=mines_rooms.ALL_ROOMS,
    enemies=MINES_ENEMIES,       # specs/19g: Prime's layer 0 enemies of the built rooms
)

# specs/12e: the working elevators between areas, (upper room: going down, lower room: going up): Prime's transports (epic 12,
# "Ponto de ligação"; specs/17e: epic 17, the WorldTeleporter destinations). Each room's RoomDef.elevator is the geometry;
# the build links its exit door block to the other room of the pair. The Tallon's are over the Chozo's and the Magmoor's,
# the Chozo's over the Magmoor's, Phendrana's over the Magmoor's (specs/18e), the Tallon's and the Magmoor's over the Mines'
# (specs/19e).
ELEVATORS = [("tallon_transport_chozo_west", "chozo_transport_tallon_north"),
             ("tallon_transport_chozo_east", "chozo_transport_tallon_east"),
             ("tallon_transport_chozo_south", "chozo_transport_tallon_south"),
             ("chozo_transport_magmoor_north", "magmoor_transport_chozo_north"),   # specs/17e
             ("tallon_transport_magmoor_east", "magmoor_transport_tallon_west"),
             ("phendrana_transport_magmoor_west", "magmoor_transport_phendrana_north"),   # specs/18e
             ("phendrana_transport_magmoor_south", "magmoor_transport_phendrana_south"),
             ("tallon_transport_mines_east", "mines_transport_tallon_south"),   # specs/19e
             ("magmoor_transport_mines_west", "mines_transport_magmoor_south"),
             impact_rooms.TELEPORTER]   # specs/20e: the Artifact Temple's teleporter down to the crater (both in area 0)


def elevator_target(key: str) -> str:
    """The room at the other end of room `key`'s elevator (ELEVATORS)."""
    for a, b in ELEVATORS:
        if key in (a, b):
            return b if key == a else a
    raise KeyError(f"{key}: elevador sem par em ELEVATORS")


AREAS: list[AreaDef] = [FRIGATE, TALLON, CHOZO, MAGMOOR, PHENDRANA, MINES]   # build order = allocation order in the ROM
START_AREA = FRIGATE               # a new game starts at station 0 of this area


def all_rooms() -> list[tuple[AreaDef, RoomDef]]:
    """(area, room) of every area, in build order; a room key used twice is an error."""
    out, seen = [], {}
    for area in AREAS:
        for r in area.rooms:
            if r.key in seen:
                raise ValueError(f"sala {r.key!r} existe nas áreas {seen[r.key]} e {area.key}")
            seen[r.key] = area.key
            out.append((area, r))
    return out

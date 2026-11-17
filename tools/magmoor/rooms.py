"""Magmoor Caverns rooms (SM area 2, specs/17b): the room graph, the map and Prime's locks (specs/17c-grafo-e-mapa-magmoor.md).

All 29 rooms of Prime's Magmoor Caverns (research/prime_worlds.json, MLVL "Magmoor Caverns"), one SM room per Prime room (epic
17, decision 1 and technical decision 1), with the Prime door graph in LINKS (29 pairs, 58 docks, all with their way back; one
loop: Monitor Station, Warrior Shrine, Fiery Shores, Shore Tunnel). The size comes from the Prime box by the Tallon's rule
(tallon/rooms.py `screens`: 30 m a screen, at most 6 x 4): 156 screens.

Map: x/y in area 2's 64x32 pause-map grid. The Magmoor is a long cave running north to south in Prime (1.5 km by 0.6 km), so
here it runs west to east from the north (the Chozo's elevator, P0) to the south (Phendrana South, the Mines West), and up/down
follows Prime's height loosely. The sides and screens of the doors were found by a search (a discarded script, as in specs/12c:
a randomized placement where each room touches every placed neighbour, the best of many by a cost) that keeps every door
touching its neighbour, the fewest floor/ceiling doors (1, Shore Tunnel -> Fiery Shores: the loop needs one, a room 2 screens
wide and one 3 wide can't both fit the same gap), no floor/ceiling door on an elevator room (its shaft is the ceiling) and a
side door on an elevator room's bottom screen where it can, and the saved map small (32 bytes of area 2's 80). The validator
checks the whole table (tools/validate.py check_magmoor) and each region alone.

Regions (epic 17, "Regiões"): A the north, from the Chozo (Burning Trail to the Monitor Tunnel); B the middle and the way out to
the Tallon (Monitor Station to the Tallon West transport); C the south (Twin Fires to the Workstation and the transports to
Phendrana South and the Mines West).

Built (specs/17e): the two elevator rooms to the Chozo (P0) and the Tallon (P16) (ELEVATOR_ROOMS, drawn in
tools/magmoor/layouts.py), as dead ends until their regions come; in the lava caves' style (smlib/lava.py, specs/17d: tileset
$09 for the hot rooms, $0A for the cool ones). specs/17f: region A (ACTIVE_REGIONS): the P0's door opens into the Burning
Trail; the Monitor Tunnel's door to the Monitor Station (region B) stays a wall until 17h. Prime's lock there (the missile
shield of Save Station A) is mapped in GATES, the hot rooms need the Varia Suit (heat_gates), the rooms' lava surfaces come
from tools/magmoor/layouts.py LAVA. ALL_ROOMS (placeholder boxes but the drawn ones) is for the validator's table and
map checks.
Prime's locks are recorded as data (DOCK_LOCKS, KEY_BEAM, FEATURES, HOT_ROOMS), read from Prime's objects
(research/prime_magmoor_locks.json, written by tools/dump_prime_locks.py); no SM item or mechanism is chosen here (the region
children, 17f-17i, by the epic's technical decision 5).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from chozo.rooms import EVENT, KEY, MISSILE, MORPH, ONE_WAY, prime_dock_locks   # noqa: F401 (the lock kinds, as the Chozo's)
from frigate.rooms import OPPOSITE, DoorLink, RoomDef
from smlib import lava
from tallon.rooms import (BOMBS, GEOMETRY, ICE, LOCK_OF, MISSILE as MISSILE_ITEM, MORPH as MORPH_ITEM, PLASMA, POWER_BOMB,
                          SPACE_JUMP, VARIA, WAVE, Gate, placeholder, screens)

from .layouts import LAVA, LAYOUTS

REGIONS = {
    "A": "Norte, vinda da Chozo: Burning Trail, Lava Lake, Triclops Pit",
    "B": "Centro e a saída para o Tallon: Monitor Station, Warrior Shrine, Fiery Shores",
    "C": "Sul: Twin Fires, Geothermal Core, Magmoor Workstation",
}
ACTIVE_REGIONS: frozenset[str] = frozenset({"A", "B", "C"})   # 17c: none built; specs/17f: A; specs/17h: B; specs/17i: C
# the transports to worlds that exist (epic 17, technical decision 6: working elevators from specs/17e): P0 to the Chozo's
# P24 (chozo_transport_magmoor_north) and P16 to the Tallon's P23 (tallon_transport_magmoor_east); specs/18e (epic 18, technical
# decision 4): P13 up to Phendrana's P0 and P27 up to its P29; specs/19e (epic 19, technical decision 4): P26 down to the Mines' P25
ELEVATOR_ROOMS = frozenset({"magmoor_transport_chozo_north", "magmoor_transport_tallon_west", "magmoor_transport_phendrana_north",
                            "magmoor_transport_phendrana_south", "magmoor_transport_mines_west"})
# the ones to a world that doesn't exist yet: decorative and empty (epic 17, user decision 5: the Mines' P25, until specs/19e)
DECORATIVE_ELEVATORS: frozenset[str] = frozenset()
# Prime's other side of each transport (WorldTeleporter destinations read from the bytes, epic 17): the room key of a built
# world's room, else the world and its P#
TRANSPORT_TO = {"magmoor_transport_chozo_north": "chozo_transport_magmoor_north",
                "magmoor_transport_tallon_west": "tallon_transport_magmoor_east",
                "magmoor_transport_phendrana_north": "phendrana_transport_magmoor_west",
                "magmoor_transport_phendrana_south": "phendrana_transport_magmoor_south",
                "magmoor_transport_mines_west": "mines_transport_magmoor_south"}   # specs/19e


@dataclass(frozen=True)
class Row:
    key: str
    prime: int                   # room index in Prime's MLVL
    name: str                    # Prime name
    region: str
    box: tuple[int, int, int]    # Prime room box (x, y, z) in metres, rounded (aabb)
    map_x: int
    map_y: int


TABLE = [
    # --- A ---
    Row("magmoor_transport_chozo_north", 0, "Transport to Chozo Ruins North", "A", (35, 40, 54), 3, 12),
    Row("magmoor_burning_trail", 1, "Burning Trail", "A", (57, 178, 62), 4, 12),
    Row("magmoor_lake_tunnel", 2, "Lake Tunnel", "A", (38, 80, 19), 10, 13),
    Row("magmoor_save_station_a", 3, "Save Station Magmoor A", "A", (39, 37, 25), 10, 12),
    Row("magmoor_lava_lake", 4, "Lava Lake", "A", (176, 110, 38), 13, 13),
    Row("magmoor_pit_tunnel", 5, "Pit Tunnel", "A", (50, 61, 29), 19, 13),
    Row("magmoor_triclops_pit", 6, "Triclops Pit", "A", (192, 158, 93), 21, 12),
    Row("magmoor_monitor_tunnel", 7, "Monitor Tunnel", "A", (64, 73, 26), 27, 12),
    Row("magmoor_storage_cavern", 8, "Storage Cavern", "A", (49, 60, 27), 19, 12),
    # --- B ---
    Row("magmoor_monitor_station", 9, "Monitor Station", "B", (144, 183, 108), 29, 12),
    Row("magmoor_transport_tunnel_a", 10, "Transport Tunnel A", "B", (73, 30, 35), 27, 15),
    Row("magmoor_warrior_shrine", 11, "Warrior Shrine", "B", (53, 46, 49), 35, 15),
    Row("magmoor_shore_tunnel", 12, "Shore Tunnel", "B", (45, 75, 27), 35, 14),
    Row("magmoor_transport_phendrana_north", 13, "Transport to Phendrana Drifts North", "B", (42, 37, 51), 26, 15),
    Row("magmoor_fiery_shores", 14, "Fiery Shores", "B", (98, 165, 50), 37, 15),
    Row("magmoor_transport_tunnel_b", 15, "Transport Tunnel B", "B", (31, 72, 21), 43, 15),
    Row("magmoor_transport_tallon_west", 16, "Transport to Tallon Overworld West", "B", (34, 51, 36), 45, 15),
    # --- C ---
    Row("magmoor_twin_fires_tunnel", 17, "Twin Fires Tunnel", "C", (67, 78, 60), 47, 14),
    Row("magmoor_twin_fires", 18, "Twin Fires", "C", (110, 165, 30), 50, 14),
    Row("magmoor_north_core_tunnel", 19, "North Core Tunnel", "C", (64, 73, 29), 56, 14),
    Row("magmoor_geothermal_core", 20, "Geothermal Core", "C", (123, 92, 90), 58, 12),
    Row("magmoor_plasma_processing", 21, "Plasma Processing", "C", (88, 89, 31), 55, 13),
    Row("magmoor_south_core_tunnel", 22, "South Core Tunnel", "C", (38, 80, 27), 55, 12),
    Row("magmoor_workstation", 23, "Magmoor Workstation", "C", (132, 128, 91), 51, 11),
    Row("magmoor_workstation_tunnel", 24, "Workstation Tunnel", "C", (46, 87, 12), 55, 11),
    Row("magmoor_transport_tunnel_c", 25, "Transport Tunnel C", "C", (44, 30, 8), 50, 13),
    Row("magmoor_transport_mines_west", 26, "Transport to Phazon Mines West", "C", (40, 72, 50), 58, 10),
    Row("magmoor_transport_phendrana_south", 27, "Transport to Phendrana Drifts South", "C", (45, 47, 54), 48, 12),
    Row("magmoor_save_station_b", 28, "Save Station Magmoor B", "C", (28, 28, 16), 50, 12),
]

# (room, side, screen) <-> (room, side, screen), one per Prime door pair; sides opposite (R-L, B-T)
LINKS = [
    (("magmoor_transport_chozo_north", "R", 1), ("magmoor_burning_trail", "L", 1)),
    (("magmoor_burning_trail", "R", 1), ("magmoor_lake_tunnel", "L", 0)),
    (("magmoor_burning_trail", "R", 0), ("magmoor_save_station_a", "L", 0)),
    (("magmoor_lake_tunnel", "R", 0), ("magmoor_lava_lake", "L", 0)),
    (("magmoor_lava_lake", "R", 0), ("magmoor_pit_tunnel", "L", 0)),
    (("magmoor_pit_tunnel", "R", 0), ("magmoor_triclops_pit", "L", 1)),
    (("magmoor_triclops_pit", "R", 0), ("magmoor_monitor_tunnel", "L", 0)),
    (("magmoor_storage_cavern", "R", 0), ("magmoor_triclops_pit", "L", 0)),
    (("magmoor_monitor_tunnel", "R", 0), ("magmoor_monitor_station", "L", 0)),
    (("magmoor_transport_tunnel_a", "R", 0), ("magmoor_monitor_station", "L", 3)),
    (("magmoor_monitor_station", "R", 3), ("magmoor_warrior_shrine", "L", 0)),
    (("magmoor_monitor_station", "R", 2), ("magmoor_shore_tunnel", "L", 0)),
    (("magmoor_transport_phendrana_north", "R", 0), ("magmoor_transport_tunnel_a", "L", 0)),
    (("magmoor_warrior_shrine", "R", 0), ("magmoor_fiery_shores", "L", 0)),
    (("magmoor_shore_tunnel", "B", 2), ("magmoor_fiery_shores", "T", 0)),
    (("magmoor_fiery_shores", "R", 0), ("magmoor_transport_tunnel_b", "L", 0)),
    (("magmoor_transport_tunnel_b", "R", 0), ("magmoor_transport_tallon_west", "L", 0)),
    (("magmoor_transport_tallon_west", "R", 0), ("magmoor_twin_fires_tunnel", "L", 1)),
    (("magmoor_twin_fires_tunnel", "R", 0), ("magmoor_twin_fires", "L", 0)),
    (("magmoor_twin_fires", "R", 0), ("magmoor_north_core_tunnel", "L", 0)),
    (("magmoor_north_core_tunnel", "R", 0), ("magmoor_geothermal_core", "L", 2)),
    (("magmoor_plasma_processing", "R", 0), ("magmoor_geothermal_core", "L", 1)),
    (("magmoor_south_core_tunnel", "R", 0), ("magmoor_geothermal_core", "L", 0)),
    (("magmoor_workstation", "R", 1), ("magmoor_south_core_tunnel", "L", 0)),
    (("magmoor_workstation", "R", 0), ("magmoor_workstation_tunnel", "L", 0)),
    (("magmoor_transport_tunnel_c", "R", 0), ("magmoor_workstation", "L", 2)),
    (("magmoor_workstation_tunnel", "R", 0), ("magmoor_transport_mines_west", "L", 1)),
    (("magmoor_transport_phendrana_south", "R", 1), ("magmoor_transport_tunnel_c", "L", 0)),
    (("magmoor_transport_phendrana_south", "R", 0), ("magmoor_save_station_b", "L", 0)),
]

# --- Prime's locks, as data (specs/17c) ------------------------------------------------------------------------------
# Per dock (this room, the room the door leads to): the kinds of lock Prime has there, by the Chozo's rule
# (chozo/rooms.py prime_dock_locks, on research/prime_magmoor_locks.json): missile = "Actor Missile Lock" (blast shield), key =
# "Trigger_DoorKey" without one (a coloured door), morph = a "Door_Area Morphball" door, event = "Actor Door Lock", one_way = a
# "one way door" scan. The Magmoor has 16: missile 2 (the two save stations), key 13, morph 1 (Warrior Shrine -> Fiery Shores;
# the Fiery Shores' side of that dock has no door in Prime, only a camera); no event lock (no boss, user decision 7), no one-way scan.
DOCK_LOCKS = {
    ("magmoor_burning_trail", "magmoor_save_station_a"): {"missile"},
    ("magmoor_warrior_shrine", "magmoor_fiery_shores"): {"morph"},
    ("magmoor_twin_fires", "magmoor_north_core_tunnel"): {"key"},
    ("magmoor_north_core_tunnel", "magmoor_twin_fires"): {"key"},
    ("magmoor_north_core_tunnel", "magmoor_geothermal_core"): {"key"},
    ("magmoor_geothermal_core", "magmoor_plasma_processing"): {"key"},
    ("magmoor_plasma_processing", "magmoor_geothermal_core"): {"key"},
    ("magmoor_south_core_tunnel", "magmoor_geothermal_core"): {"key"},
    ("magmoor_south_core_tunnel", "magmoor_workstation"): {"key"},
    ("magmoor_workstation", "magmoor_transport_tunnel_c"): {"key"},
    ("magmoor_workstation_tunnel", "magmoor_transport_mines_west"): {"key"},
    ("magmoor_transport_tunnel_c", "magmoor_transport_phendrana_south"): {"key"},
    ("magmoor_transport_tunnel_c", "magmoor_workstation"): {"key"},
    ("magmoor_transport_mines_west", "magmoor_workstation_tunnel"): {"key"},
    ("magmoor_transport_phendrana_south", "magmoor_save_station_b"): {"missile"},
    ("magmoor_transport_phendrana_south", "magmoor_transport_tunnel_c"): {"key"},
}

# specs/17c: the beam of each key dock, from its "Trigger_DoorKey" DamageVulnerability (research/prime_magmoor_locks.json
# "key_vuln": power, ice, wave, plasma; 1 = hurts, 2 = immune): Wave only 2 2 1 2, Ice only 2 1 2 2, Plasma only 2 2 2 1. Prime's
# beam, not yet the SM mechanism: the Plasma Processing's inside door (Plasma) becomes an ice door in the SM (epic 17, technical
# decision 5, specs/17i), so Samus is never shut in with the item that replaces the Plasma Beam (a missile, user decision 2).
BEAM_OF_VULN = {(2, 2, 1, 2): WAVE, (2, 1, 2, 2): ICE, (2, 2, 2, 1): PLASMA}
KEY_BEAM = {
    ("magmoor_twin_fires", "magmoor_north_core_tunnel"): WAVE,
    ("magmoor_north_core_tunnel", "magmoor_twin_fires"): WAVE,
    ("magmoor_north_core_tunnel", "magmoor_geothermal_core"): WAVE,
    ("magmoor_geothermal_core", "magmoor_plasma_processing"): ICE,
    ("magmoor_plasma_processing", "magmoor_geothermal_core"): PLASMA,
    ("magmoor_south_core_tunnel", "magmoor_geothermal_core"): WAVE,
    ("magmoor_south_core_tunnel", "magmoor_workstation"): WAVE,
    ("magmoor_workstation", "magmoor_transport_tunnel_c"): WAVE,
    ("magmoor_workstation_tunnel", "magmoor_transport_mines_west"): ICE,
    ("magmoor_transport_tunnel_c", "magmoor_transport_phendrana_south"): WAVE,
    ("magmoor_transport_tunnel_c", "magmoor_workstation"): WAVE,
    ("magmoor_transport_mines_west", "magmoor_workstation_tunnel"): ICE,
    ("magmoor_transport_phendrana_south", "magmoor_transport_tunnel_c"): WAVE,
}

# In-room features of Prime that gate movement (same file, the Chozo's names: chozo/rooms.py FEATURES): spider, bomb_slot,
# breakable, halfpipe, grapple, heat (names with "varia"/"heat": item checks, Thermal faders, the heat itself), water, lava (a
# "Water" object named lava), morph_door
FEATURES = {
    "magmoor_burning_trail": {"heat", "lava"},
    "magmoor_lake_tunnel": {"heat", "lava"},
    "magmoor_lava_lake": {"breakable", "grapple", "heat", "lava"},
    "magmoor_pit_tunnel": {"heat"},
    "magmoor_triclops_pit": {"breakable", "heat", "lava"},
    "magmoor_monitor_tunnel": {"heat", "lava"},
    "magmoor_storage_cavern": {"lava"},
    "magmoor_monitor_station": {"heat", "lava"},
    "magmoor_transport_tunnel_a": {"heat", "lava"},
    "magmoor_warrior_shrine": {"heat", "lava", "morph_door"},
    "magmoor_shore_tunnel": {"heat", "lava"},
    "magmoor_transport_phendrana_north": {"lava"},
    "magmoor_fiery_shores": {"grapple", "heat", "lava", "morph_door"},
    "magmoor_transport_tunnel_b": {"heat", "lava"},
    "magmoor_transport_tallon_west": {"heat", "lava"},
    "magmoor_twin_fires_tunnel": {"heat", "lava", "spider"},
    "magmoor_twin_fires": {"grapple", "lava"},
    "magmoor_north_core_tunnel": {"lava"},
    "magmoor_geothermal_core": {"bomb_slot", "grapple", "lava", "spider"},
    "magmoor_plasma_processing": {"lava"},
    "magmoor_south_core_tunnel": {"lava"},
    "magmoor_workstation": {"lava"},
    "magmoor_transport_phendrana_south": {"lava"},
    "magmoor_save_station_b": {"lava"},
}

# specs/17c (epic 17, user decision 3): the hot rooms, Prime's superheated ones: the rooms with a "SpecialFunction" of function 18
# (Area Damage; research/prime_magmoor_locks.json "area_damage"; the Lava Lake has 2). Every door into one will need the Varia
# Suit (the 12g model, from the region children); area 2's heat is native (chozo/heat.py HEAT_BITS, specs/17b).
HOT_ROOMS: frozenset[str] = frozenset({
    "magmoor_fiery_shores",
    "magmoor_lake_tunnel",
    "magmoor_lava_lake",
    "magmoor_monitor_station",
    "magmoor_monitor_tunnel",
    "magmoor_pit_tunnel",
    "magmoor_shore_tunnel",
    "magmoor_transport_tunnel_a",
    "magmoor_transport_tunnel_b",
    "magmoor_triclops_pit",
    "magmoor_twin_fires_tunnel",
    "magmoor_warrior_shrine",
})


# --- region A's lock in the SM (specs/17f; epic 17, technical decision 5: Prime's locks -> mechanisms that exist) -----------
# Prime's one lock in region A (DOCK_LOCKS): the missile shield of the Burning Trail's door to Save Station A, on the trail's
# side = a red door there (door bit MAGMOOR_MISSILE_BIT0 on: the Tallon's $B0-$B2, the Chozo's $B3-$BF). The hot rooms
# (HOT_ROOMS) get the Varia Suit in every door into them (heat_gates, the Chozo's rule: a hot room is impassable without it).
MAGMOOR_MISSILE_BIT0 = 0xC0
GATES = {
    frozenset({"magmoor_burning_trail", "magmoor_save_station_a"}): Gate(frozenset({MISSILE_ITEM}), ("magmoor_burning_trail",)),
    # specs/17h, region B: Prime's Morph Ball door of the Warrior Shrine to the Fiery Shores ("Door_Area Morphball", behind a
    # wall only a power bomb breaks: DOCK_LOCKS morph) = geometry on both sides (tools/magmoor/layouts.py): the shrine's R0
    # door in a chamber entered by a 1-row tunnel shut by a power bomb block, and on the Fiery Shores' side the tunnel's end (a
    # pocket under the ceiling door's platform) whose way out is a 1-row tunnel shut by a power bomb block too. Prime's
    # Fiery Shores side has no door (only a camera: probably one way); here the door works both ways and each side needs the
    # Morph Ball and the Power Bomb (decision to confirm, specs/17h): the items behind it (the missile and the power bomb
    # expansion) are never picked up before round 6.
    frozenset({"magmoor_warrior_shrine", "magmoor_fiery_shores"}): Gate(
        frozenset({MORPH_ITEM, POWER_BOMB}), (), ("magmoor_warrior_shrine", "magmoor_fiery_shores")),
    # specs/17i, region C. Prime's locks there (DOCK_LOCKS, KEY_BEAM): the missile shield of the transport to Phendrana South's
    # door to Save Station B (its side: a red door, bit $C1, the second missile gate here); the coloured doors = beam doors of
    # Prime's beam on the docks' sides (wave on both sides of Twin Fires <-> North Core Tunnel, Workstation <-> Transport
    # Tunnel C and Transport Tunnel C <-> Phendrana South; on the North Core Tunnel's side of its Geothermal Core door and on
    # both doors of the South Core Tunnel; ice on both sides of the Workstation Tunnel <-> Mines West), and the Plasma
    # Processing's own door, a plasma door in Prime, an ice door here (SM_BEAM: Samus came in through the Geothermal Core's
    # ice door with the Ice Beam; a plasma door would shut her in with the missile that replaces the Plasma Beam, epic 17
    # technical decision 5). Prime's in-room locks (FEATURES) that gate a door, as geometry on that door's side (layouts.py):
    # the Twin Fires Tunnel's Spider Ball track (its R0 door on a cliff the Space Jump climbs), the Geothermal Core's puzzle
    # (bomb slots: the Plasma Processing's door in a chamber behind a 1-row tunnel shut by a bomb block) and its spider tracks
    # and grapple point (the South Core Tunnel's door on a shelf the Space Jump reaches).
    frozenset({"magmoor_transport_phendrana_south", "magmoor_save_station_b"}): Gate(
        frozenset({MISSILE_ITEM}), ("magmoor_transport_phendrana_south",)),
    frozenset({"magmoor_twin_fires_tunnel", "magmoor_twin_fires"}): Gate(frozenset({SPACE_JUMP}), (), ("magmoor_twin_fires_tunnel",)),
    frozenset({"magmoor_twin_fires", "magmoor_north_core_tunnel"}): Gate(
        frozenset({WAVE}), ("magmoor_twin_fires", "magmoor_north_core_tunnel")),
    frozenset({"magmoor_north_core_tunnel", "magmoor_geothermal_core"}): Gate(frozenset({WAVE}), ("magmoor_north_core_tunnel",)),
    frozenset({"magmoor_geothermal_core", "magmoor_plasma_processing"}): Gate(
        frozenset({ICE, MORPH_ITEM, BOMBS}), ("magmoor_geothermal_core", "magmoor_plasma_processing"), ("magmoor_geothermal_core",)),
    frozenset({"magmoor_south_core_tunnel", "magmoor_geothermal_core"}): Gate(
        frozenset({WAVE, SPACE_JUMP}), ("magmoor_south_core_tunnel",), ("magmoor_geothermal_core",)),
    frozenset({"magmoor_south_core_tunnel", "magmoor_workstation"}): Gate(frozenset({WAVE}), ("magmoor_south_core_tunnel",)),
    frozenset({"magmoor_workstation", "magmoor_transport_tunnel_c"}): Gate(
        frozenset({WAVE}), ("magmoor_workstation", "magmoor_transport_tunnel_c")),
    frozenset({"magmoor_workstation_tunnel", "magmoor_transport_mines_west"}): Gate(
        frozenset({ICE}), ("magmoor_workstation_tunnel", "magmoor_transport_mines_west")),
    frozenset({"magmoor_transport_tunnel_c", "magmoor_transport_phendrana_south"}): Gate(
        frozenset({WAVE}), ("magmoor_transport_tunnel_c", "magmoor_transport_phendrana_south")),
}
# specs/17i: the SM beam of a key dock whose Prime beam is not the one its cap uses (epic 17, technical decision 5): the Plasma
# Processing's inside door, Prime's plasma door, is an ice door (validate.check_magmoor_locks_mapped compares the caps with
# KEY_BEAM through this)
SM_BEAM = {("magmoor_plasma_processing", "magmoor_geothermal_core"): ICE}
# specs/17i: Prime's in-room features (FEATURES) that may gate a door of their room as geometry (GATES with a ledge but no
# Prime dock lock): the Spider Ball tracks and grapple points = the Space Jump, the bomb slots = the Morph Ball and the Bombs
FEATURE_GEOMETRY = {"spider": frozenset({SPACE_JUMP}), "grapple": frozenset({SPACE_JUMP}),
                    "bomb_slot": frozenset({MORPH_ITEM, BOMBS})}

# specs/17e: the round each built room is first reached in (the walk of the three areas together, validate.check_magmoor_rounds):
# both elevator rooms in round 1, as their other sides (the Chozo's P24 and the Tallon's P23); dead ends (no door yet).
# specs/17f: region A from the Chozo's elevator (round 1): the Burning Trail and, through its red door (the Landing Site's
# missiles, round 0), Save Station A in round 1; every other room of the region is hot (or, the Storage Cavern, behind a hot
# one): round 3, with the Varia Suit (the Sunchamber's, round 2).
_ROUNDS = [[],
           ["magmoor_transport_chozo_north", "magmoor_transport_tallon_west", "magmoor_burning_trail", "magmoor_save_station_a"],
           [],
           ["magmoor_lake_tunnel", "magmoor_lava_lake", "magmoor_pit_tunnel", "magmoor_triclops_pit", "magmoor_storage_cavern",
            "magmoor_monitor_tunnel",
            # specs/17h: region B, from the Monitor Tunnel (region A, round 3) and from the Tallon's elevator (the P16, round 1)
            # through the hot Transport Tunnel B: every room of the region but the P16 is hot or behind a hot one (the
            # transport to Phendrana North, behind the Transport Tunnel A): round 3, with the Varia Suit, from both sides
            "magmoor_monitor_station", "magmoor_transport_tunnel_a", "magmoor_transport_phendrana_north",
            "magmoor_warrior_shrine", "magmoor_shore_tunnel", "magmoor_fiery_shores", "magmoor_transport_tunnel_b",
            # specs/17i: region C, from the P16 (round 1) through the hot Twin Fires Tunnel (the Varia Suit; its R0 door on a
            # Space Jump ledge, round 2's too): round 3; the wave doors with the Wave Beam (round 0's, the Tallon's Magmoor East)
            "magmoor_twin_fires_tunnel", "magmoor_twin_fires", "magmoor_north_core_tunnel", "magmoor_geothermal_core",
            "magmoor_south_core_tunnel", "magmoor_workstation", "magmoor_workstation_tunnel", "magmoor_transport_tunnel_c",
            "magmoor_transport_phendrana_south", "magmoor_save_station_b"],
           # specs/17i: behind the ice doors (the Ice Beam is the Tallon's Root Cave's, round 3): the Plasma Processing and the
           # transport to the Mines West
           ["magmoor_plasma_processing", "magmoor_transport_mines_west"]]
FIRST_ROUND = {k: n for n, keys in enumerate(_ROUNDS) for k in keys}


def build_rooms(regions, extra=frozenset()) -> list[RoomDef]:
    """RoomDefs of the rooms in `regions` and in `extra`, in TABLE order, with the doors between them; a link to a room left
    out is left out too (wall). specs/17e: a room with a layout (tools/magmoor/layouts.py) gets it, the others are placeholder
    boxes; all in the lava caves' style, the hot rooms on tileset $09 and the cool ones on $0A (smlib/lava.py)."""
    regions = set(regions)
    unknown = regions - set(REGIONS)
    if unknown:
        raise ValueError(f"regiões desconhecidas: {sorted(unknown)}")
    rooms: dict[str, RoomDef] = {}
    for t in TABLE:
        if t.region not in regions and t.key not in extra:
            continue
        w, h = screens(t.box)
        shape = LAYOUTS[t.key]() if t.key in LAYOUTS else None
        canvas = shape.canvas if shape else placeholder(w, h)
        if (canvas.w, canvas.h) != (w * 16, h * 16):
            raise ValueError(f"{t.key}: desenho {canvas.w}x{canvas.h} blocos, a tabela diz {w}x{h} telas")
        hot = t.key in HOT_ROOMS
        rooms[t.key] = RoomDef(t.key, t.prime, t.name, w, h, t.map_x, t.map_y, canvas, heat=hot,
                               style=lava.LAVA_HOT if hot else lava.LAVA_COOL,
                               tileset=lava.HOT_TILESET if hot else lava.COOL_TILESET,
                               skin=shape.skin if shape else [], blocks=shape.blocks if shape else [],
                               elevator=shape.elevator if shape else None, lava=LAVA.get(t.key) if shape else None,
                               save_station=shape.save if shape else None)
    bits = {k: MAGMOOR_MISSILE_BIT0 + n for n, k in enumerate(k for k, g in GATES.items() if MISSILE_ITEM in g.items)}
    for (ra, sa, na), (rb, sb, nb) in LINKS:
        if OPPOSITE[sa] != sb:
            raise ValueError(f"porta {ra}.{sa} liga em {rb}.{sb}: lados precisam ser opostos")
        if ra not in rooms or rb not in rooms:
            continue
        da, db = DoorLink(sa, na, rb), DoorLink(sb, nb, ra)
        gate = GATES.get(frozenset({ra, rb}))
        if gate:   # specs/17f: the Chozo's rule (chozo/rooms.py build_rooms): one kind of cap on its side(s), or (specs/17h) a
            # ledge only: the side(s) behind the GEOMETRY items (DoorLink.ledge)
            caps = {LOCK_OF[i] for i in gate.items if i in LOCK_OF}
            if (len(caps) > 1 or bool(caps) != bool(gate.capped) or not set(gate.capped) <= {ra, rb}
                    or not set(gate.ledge) <= {ra, rb} or bool(gate.ledge) != bool(gate.items & GEOMETRY)):
                raise ValueError(f"trava {ra}-{rb}: precisa de um tipo de tampa e do lado dela ({gate})")
            cap = caps.pop() if caps else None
            for d, key in ((da, ra), (db, rb)):
                d.gate, d.ledge = gate.items, key in gate.ledge
                if key in gate.capped:
                    d.lock, d.lock_bit = cap, bits.get(frozenset({ra, rb}))
        rooms[ra].doors.append(da)
        rooms[rb].doors.append(db)
        da.to_door = len(rooms[rb].doors) - 1
        db.to_door = len(rooms[ra].doors) - 1
    heat_gates(rooms)
    return list(rooms.values())


def heat_gates(rooms: dict) -> None:
    """specs/17f (the Chozo's rule, specs/12g): every door into a hot room needs the Varia Suit (VARIA in its gate)."""
    for r in rooms.values():
        for d in r.doors:
            if d.to_room in rooms and rooms[d.to_room].heat:
                d.gate = d.gate | {VARIA}


def region_of(key: str) -> str:
    return next(t.region for t in TABLE if t.key == key)


def check_prime(worlds_json: Path, locks_json: Path) -> list[str]:
    """TABLE and LINKS against Prime's data (every room once with its name and box, the links = Prime's door pairs), and
    DOCK_LOCKS / KEY_BEAM / FEATURES / HOT_ROOMS = what research/prime_magmoor_locks.json gives; the elevator lists = the
    TABLE's transports."""
    world = next(w for w in json.loads(worlds_json.read_text()) if w["name"] == "Magmoor Caverns")
    prime = {a["index"]: a for a in world["areas"]}
    problems = []
    by_prime = {t.prime: t for t in TABLE}
    if len(by_prime) != len(TABLE) or set(by_prime) != set(prime):
        problems.append(f"magmoor: tabela tem as salas {sorted(by_prime)}, o Prime tem {sorted(prime)}")
    if len({t.key for t in TABLE}) != len(TABLE):
        problems.append("magmoor: chave de sala repetida na tabela")
    for t in TABLE:
        if t.region not in REGIONS:
            problems.append(f"{t.key}: região {t.region!r} desconhecida")
        if not t.key.startswith("magmoor_"):
            problems.append(f"{t.key}: chave sem o prefixo magmoor_")
        a = prime.get(t.prime)
        if a is None:
            continue
        b = a["aabb"]
        box = tuple(round(b[i + 3] - b[i]) for i in range(3))
        if (a["name"], box) != (t.name, t.box):
            problems.append(f"{t.key}: P{t.prime} no Prime é {a['name']!r} {box}, a tabela diz {t.name!r} {t.box}")
    transports = {t.key for t in TABLE if t.name.startswith("Transport to ")}
    if ELEVATOR_ROOMS | DECORATIVE_ELEVATORS != transports or ELEVATOR_ROOMS & DECORATIVE_ELEVATORS \
            or set(TRANSPORT_TO) != transports:
        problems.append(f"magmoor: elevadores {sorted(ELEVATOR_ROOMS)} + de enfeite {sorted(DECORATIVE_ELEVATORS)}, os "
                        f"transportes do Prime são {sorted(transports)}")
    key_of = {t.prime: t.key for t in TABLE}
    key_prime = {t.key: t.prime for t in TABLE}
    unknown = sorted({k for a, b in LINKS for k in (a[0], b[0])} - set(key_prime))
    if unknown:
        return problems + [f"magmoor: ligações com salas fora da tabela: {unknown}"]
    ours = [frozenset((key_prime[a[0]], key_prime[b[0]])) for a, b in LINKS]
    theirs = {frozenset((a["index"], d["to_area"])) for a in world["areas"] for d in a["docks"]}
    if len(set(ours)) != len(ours) or set(ours) != theirs:
        problems.append(f"magmoor: ligações diferentes do Prime: sobram {sorted(map(sorted, set(ours) - theirs))}, "
                        f"faltam {sorted(map(sorted, theirs - set(ours)))}")
    data = json.loads(locks_json.read_text())
    want_locks, want_beam, want_features, want_hot = {}, {}, {}, set()
    for i, room in data.items():
        if int(i) not in key_of:
            continue
        for d in room["docks"]:
            kinds = prime_dock_locks(d["objects"])
            if kinds:
                want_locks[(key_of[int(i)], key_of[d["to"]])] = kinds
            if KEY in kinds:
                vuln = tuple(d.get("key_vuln") or ())
                want_beam[(key_of[int(i)], key_of[d["to"]])] = BEAM_OF_VULN.get(vuln, f"vulnerabilidade {vuln}")
        if room["features"]:
            want_features[key_of[int(i)]] = set(room["features"])
        if room.get("area_damage"):
            want_hot.add(key_of[int(i)])
    for k in sorted(set(want_locks) | set(DOCK_LOCKS)):
        if want_locks.get(k) != DOCK_LOCKS.get(k):
            problems.append(f"magmoor: trava da doca {k[0]} -> {k[1]}: o Prime tem {sorted(want_locks.get(k, ()))}, "
                            f"a tabela diz {sorted(DOCK_LOCKS.get(k, ()))}")
    for k in sorted(set(want_beam) | set(KEY_BEAM)):
        if want_beam.get(k) != KEY_BEAM.get(k):
            problems.append(f"magmoor: cor da porta {k[0]} -> {k[1]}: o Prime tem {want_beam.get(k)}, KEY_BEAM diz {KEY_BEAM.get(k)}")
    for k in sorted(set(want_features) | set(FEATURES)):
        if want_features.get(k) != FEATURES.get(k):
            problems.append(f"magmoor: {k}: o Prime tem {sorted(want_features.get(k, ()))}, "
                            f"FEATURES diz {sorted(FEATURES.get(k, ()))}")
    if want_hot != HOT_ROOMS:
        problems.append(f"magmoor: salas quentes (Area Damage) do Prime {sorted(want_hot)}, HOT_ROOMS diz {sorted(HOT_ROOMS)}")
    return problems


ALL_ROOMS = build_rooms(REGIONS)          # the whole world, for the validator's map checks
ROOMS = build_rooms(ACTIVE_REGIONS, ELEVATOR_ROOMS)   # what the build gets (specs/17e: the elevator rooms; since 17i all 29)

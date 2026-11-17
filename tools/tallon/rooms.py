"""Tallon Overworld rooms (SM area 0): the room graph and the map (specs/07d-grafo-e-mapa-tallon.md).

All 44 rooms of Prime's Tallon Overworld (research/prime_worlds.json, MLVL "Tallon Overworld"),
one SM room per Prime room (epic decision 4), with the Prime door graph in LINKS. Each row of
TABLE gives the Prime room's box in metres; the SM size comes from it by `screens` (the same
loose scale as the frigate: the longer floor axis is the width, the height is the height).

Map: x/y in area 0's 64x32 pause-map grid. As in the frigate (research/frigate_design.md), Prime
is 3D, so only the pairs of linked rooms come from it: sides and screens of the doors were chosen
so that every door touches its neighbour on the map, west-to-east roughly as in Prime, rooms of
the same region together. The validator checks the full table (tools/validate.py, check_tallon).

Regions (epic, "Regiões"): A surface/start, B temple, C waterfall + crash site + roots, D sunken
frigate, E great tree. The build only gets the rooms of ACTIVE_REGIONS (epic decision 8); a door
to a room of a region that is off becomes wall (no door in the level) and no link is checked.

Rooms with a layout in tallon/layouts.py (the MVP rooms, specs/07g; the transports and the
Artifact Temple shell, specs/07j; regions B and C, specs/07k; region D, the sunken frigate, flooded,
specs/07l; region E, the great tree, and Gully/Alcove, specs/07m: since then all 44) get it; a room
without one would be a placeholder (an open box). Prime's gates (missile shields, ice/plasma doors,
Space Jump ledges) are kept as in Prime (GATES, specs/07k): the rooms behind them are built but out
of reach until the items exist; FIRST_ROUND says when each room becomes reachable (specs/09f). A drawn room waits for its region: it is built when the region is
activated (the validator checks its reach meanwhile, with its region alone). Within the active regions only
ACTIVE_ROOMS are built (None = all; 07g-07l left Gully and Alcove out, 07m built them); a door to a room
that is not built is wall, like a door to a region that is off.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from frigate.rooms import OPPOSITE, DoorLink, RoomDef
from smlib import crateria
from smlib.canvas import Canvas
from smlib.style import FRIGATE

from .layouts import LAYOUTS

REGIONS = {
    "A": "Superfície (início)",
    "B": "Templo",
    "C": "Cachoeira, Crash Site e Raízes",
    "D": "Fragata afundada",
    "E": "Grande Árvore",
}
ACTIVE_REGIONS: frozenset[str] = frozenset({"A", "B", "C", "D", "E"})
# rooms built inside the active regions (None = all of them). 07g: Prime's item-free path; 07k:
# all of B and C; 07l: all of D; 07m: all of E and Gully/Alcove, so the whole table (44 rooms).
ACTIVE_ROOMS: frozenset[str] | None = None

METRES_PER_SCREEN = 30
MAX_W, MAX_H = 6, 4   # keeps the big Prime rooms (Crash Site, Artifact Temple) at 24 screens


def screens(box: tuple[int, int, int]) -> tuple[int, int]:
    """SM size (width, height) in screens of a Prime room box (x, y, z) in metres: the longer of
    x/y and z, METRES_PER_SCREEN each, rounded half up, at least 1, at most MAX_W x MAX_H."""
    def scale(m: float, top: int) -> int:
        return min(top, max(1, math.floor(m / METRES_PER_SCREEN + 0.5)))
    return scale(max(box[0], box[1]), MAX_W), scale(box[2], MAX_H)


# looks (epic decision 5): surface = tileset 0 (rain where Prime has it), caves and tunnels =
# stone bricks of tileset 2, sunken frigate = the frigate's tileset 4 (recoloured like the frigate,
# with the frigate's background: specs/07l)
SUP, CAV, FRI = "superficie", "caverna", "fragata"
LOOKS = {SUP: (crateria.SURFACE, None), CAV: (crateria.CAVE, crateria.CAVE_TILESET), FRI: (FRIGATE, 4)}
# background of the cave rooms: the library background of the vanilla tileset 2 rooms $8F:99F9,
# $9A90, $9804 (BG2 scroll $C1C1, as the area's); the surface keeps the area's ($8F:B8B4, Parlor)
CAVE_BG = 0xB905
# background of the sunken frigate rooms = the frigate's (areas.FRIGATE): the vanilla Wrecked Ship
# library background $8F:E117 with BG2 scroll $C1C1
FRIGATE_BG, FRIGATE_LAYER2 = 0xE117, 0xC1C1
# Prime rooms with a "Rain Simulator" (epic, "Chuva")
RAIN = {"tallon_landing_site", "tallon_canyon", "tallon_temple_security", "tallon_root_cave",
        "tallon_arbor_chamber", "tallon_life_grove"}
# Prime rooms of region D with a "Water" object (13 of its 14: not the Deck Beta Transit Hall;
# research/prime_fs, MREA layer 0). In Prime the sunken frigate is under water, so here they are
# flooded to the top (water FX, specs/07l). The ponds of regions A-C stay dry (out of scope).
FLOODED = {"tallon_vent_c", "tallon_vent_b", "tallon_vent_a", "tallon_reactor_core", "tallon_reactor_access",
           "tallon_cargo_lift", "tallon_savestation", "tallon_biohazard", "tallon_security_hall",
           "tallon_biotech_1", "tallon_conduit_hall", "tallon_elevator_beta", "tallon_hydro_access"}


@dataclass(frozen=True)
class Row:
    key: str
    prime: int                   # room index in Prime's MLVL
    name: str                    # Prime name
    region: str
    look: str
    box: tuple[int, int, int]    # Prime room box (x, y, z) in metres, rounded (aabb)
    map_x: int
    map_y: int


TABLE = [
    # key, Prime index, Prime name, region, look, Prime box (m), map x, map y
    # --- A: surface (start) ---
    Row("tallon_landing_site", 0, "Landing Site", "A", SUP, (135, 135, 94), 24, 6),
    Row("tallon_gully", 1, "Gully", "A", SUP, (79, 52, 31), 21, 7),
    Row("tallon_canyon_cavern", 2, "Canyon Cavern", "A", CAV, (56, 70, 23), 22, 8),
    Row("tallon_alcove", 4, "Alcove", "A", SUP, (133, 146, 55), 19, 5),
    Row("tallon_canyon", 6, "Tallon Canyon", "A", SUP, (125, 112, 79), 18, 8),
    Row("tallon_tunnel_a", 9, "Transport Tunnel A", "A", CAV, (17, 51, 11), 16, 9),
    Row("tallon_transport_chozo_west", 14, "Transport to Chozo Ruins West", "A", CAV, (36, 46, 51), 14, 9),
    # --- B: temple ---
    Row("tallon_temple_hall", 3, "Temple Hall", "B", SUP, (8, 51, 10), 29, 8),
    Row("tallon_temple_security", 7, "Temple Security Station", "B", SUP, (41, 92, 22), 31, 8),
    Row("tallon_temple_lobby", 11, "Temple Lobby", "B", CAV, (20, 51, 10), 34, 8),
    Row("tallon_artifact_temple", 16, "Artifact Temple", "B", SUP, (406, 447, 234), 32, 9),
    # --- C: waterfall, crash site, roots ---
    Row("tallon_waterfall_cavern", 5, "Waterfall Cavern", "C", CAV, (55, 86, 28), 29, 7),
    Row("tallon_crash_site", 8, "Frigate Crash Site", "C", SUP, (315, 353, 222), 32, 4),
    Row("tallon_root_tunnel", 10, "Root Tunnel", "C", CAV, (79, 25, 25), 15, 8),
    Row("tallon_frigate_access", 12, "Frigate Access Tunnel", "C", CAV, (49, 29, 7), 38, 7),
    Row("tallon_overgrown_cavern", 13, "Overgrown Cavern", "C", CAV, (15, 51, 14), 38, 6),
    Row("tallon_root_cave", 15, "Root Cave", "C", SUP, (84, 81, 113), 12, 5),
    Row("tallon_tunnel_c", 18, "Transport Tunnel C", "C", CAV, (107, 122, 110), 40, 3),
    Row("tallon_tunnel_b", 19, "Transport Tunnel B", "C", CAV, (44, 101, 37), 9, 8),
    Row("tallon_arbor_chamber", 20, "Arbor Chamber", "C", SUP, (46, 48, 28), 10, 5),
    Row("tallon_transport_chozo_east", 22, "Transport to Chozo Ruins East", "C", CAV, (41, 36, 50), 44, 5),
    Row("tallon_transport_magmoor_east", 23, "Transport to Magmoor Caverns East", "C", CAV, (34, 42, 48), 8, 7),
    # --- D: sunken frigate ---
    Row("tallon_vent_c", 17, "Main Ventilation Shaft Section C", "D", FRI, (63, 66, 49), 40, 7),
    Row("tallon_vent_b", 21, "Main Ventilation Shaft Section B", "D", FRI, (55, 22, 62), 42, 7),
    Row("tallon_vent_a", 24, "Main Ventilation Shaft Section A", "D", FRI, (46, 73, 18), 44, 7),
    Row("tallon_reactor_core", 25, "Reactor Core", "D", FRI, (86, 107, 99), 46, 6),
    Row("tallon_reactor_access", 26, "Reactor Access", "D", FRI, (32, 28, 23), 50, 8),
    Row("tallon_cargo_lift", 27, "Cargo Freight Lift to Deck Gamma", "D", FRI, (39, 133, 80), 51, 7),
    Row("tallon_savestation", 28, "Savestation", "D", FRI, (18, 16, 18), 50, 7),
    Row("tallon_transit_hall", 29, "Deck Beta Transit Hall", "D", FRI, (45, 9, 6), 49, 9),
    Row("tallon_biohazard", 30, "Biohazard Containment", "D", FRI, (44, 59, 48), 47, 9),
    Row("tallon_security_hall", 31, "Deck Beta Security Hall", "D", FRI, (27, 30, 10), 46, 10),
    Row("tallon_biotech_1", 32, "Biotech Research Area 1", "D", FRI, (70, 68, 77), 44, 8),
    Row("tallon_conduit_hall", 33, "Deck Beta Conduit Hall", "D", FRI, (24, 46, 13), 42, 10),
    Row("tallon_elevator_beta", 34, "Connection Elevator to Deck Beta", "D", FRI, (29, 21, 80), 41, 9),
    Row("tallon_hydro_access", 35, "Hydro Access Tunnel", "D", CAV, (87, 31, 57), 38, 10),
    # --- E: great tree ---
    Row("tallon_great_tree_hall", 36, "Great Tree Hall", "E", SUP, (89, 84, 144), 40, 12),
    Row("tallon_great_tree_chamber", 37, "Great Tree Chamber", "E", SUP, (81, 68, 41), 43, 13),
    Row("tallon_tunnel_d", 38, "Transport Tunnel D", "E", CAV, (26, 51, 11), 43, 12),
    Row("tallon_life_grove_tunnel", 39, "Life Grove Tunnel", "E", CAV, (17, 67, 35), 43, 15),
    Row("tallon_tunnel_e", 40, "Transport Tunnel E", "E", CAV, (35, 94, 20), 43, 14),
    Row("tallon_transport_chozo_south", 41, "Transport to Chozo Ruins South", "E", CAV, (41, 36, 50), 45, 11),
    Row("tallon_life_grove", 42, "Life Grove", "E", SUP, (122, 148, 100), 45, 15),
    Row("tallon_transport_mines_east", 43, "Transport to Phazon Mines East", "E", CAV, (42, 34, 48), 46, 13),
]

# (room, side, screen) <-> (room, side, screen), one per Prime door pair; sides opposite (R-L, B-T)
LINKS = [
    (("tallon_landing_site", "L", 1), ("tallon_gully", "R", 0)),
    (("tallon_landing_site", "L", 2), ("tallon_canyon_cavern", "R", 0)),
    (("tallon_landing_site", "R", 2), ("tallon_temple_hall", "L", 0)),
    (("tallon_landing_site", "L", 0), ("tallon_alcove", "R", 1)),
    (("tallon_landing_site", "R", 1), ("tallon_waterfall_cavern", "L", 0)),
    (("tallon_gully", "B", 0), ("tallon_canyon", "T", 3)),
    (("tallon_canyon_cavern", "L", 0), ("tallon_canyon", "R", 0)),
    (("tallon_canyon", "L", 1), ("tallon_tunnel_a", "R", 0)),
    (("tallon_canyon", "L", 0), ("tallon_root_tunnel", "R", 0)),
    (("tallon_tunnel_a", "L", 0), ("tallon_transport_chozo_west", "R", 0)),
    (("tallon_temple_hall", "R", 0), ("tallon_temple_security", "L", 0)),
    (("tallon_temple_security", "R", 0), ("tallon_temple_lobby", "L", 0)),
    (("tallon_temple_lobby", "B", 1), ("tallon_artifact_temple", "T", 3)),
    (("tallon_waterfall_cavern", "R", 0), ("tallon_crash_site", "L", 3)),
    (("tallon_crash_site", "R", 3), ("tallon_frigate_access", "L", 0)),
    (("tallon_crash_site", "R", 2), ("tallon_overgrown_cavern", "L", 0)),
    (("tallon_root_tunnel", "L", 0), ("tallon_root_cave", "R", 3)),
    (("tallon_frigate_access", "R", 0), ("tallon_vent_c", "L", 0)),
    (("tallon_overgrown_cavern", "R", 0), ("tallon_tunnel_c", "L", 3)),
    (("tallon_root_cave", "L", 3), ("tallon_tunnel_b", "R", 0)),
    (("tallon_root_cave", "L", 0), ("tallon_arbor_chamber", "R", 0)),
    (("tallon_tunnel_c", "R", 2), ("tallon_transport_chozo_east", "L", 0)),
    (("tallon_tunnel_b", "L", 0), ("tallon_transport_magmoor_east", "R", 1)),
    (("tallon_vent_c", "R", 0), ("tallon_vent_b", "L", 0)),
    (("tallon_vent_b", "R", 0), ("tallon_vent_a", "L", 0)),
    (("tallon_vent_a", "R", 0), ("tallon_reactor_core", "L", 1)),
    (("tallon_reactor_core", "R", 2), ("tallon_reactor_access", "L", 0)),
    (("tallon_reactor_access", "R", 0), ("tallon_cargo_lift", "L", 1)),
    (("tallon_reactor_access", "T", 0), ("tallon_savestation", "B", 0)),
    (("tallon_cargo_lift", "L", 2), ("tallon_transit_hall", "R", 0)),
    (("tallon_transit_hall", "L", 0), ("tallon_biohazard", "R", 0)),
    (("tallon_biohazard", "L", 1), ("tallon_security_hall", "R", 0)),
    (("tallon_security_hall", "L", 0), ("tallon_biotech_1", "R", 2)),
    (("tallon_biotech_1", "L", 2), ("tallon_conduit_hall", "R", 0)),
    (("tallon_conduit_hall", "L", 0), ("tallon_elevator_beta", "R", 1)),
    (("tallon_elevator_beta", "L", 1), ("tallon_hydro_access", "R", 0)),
    (("tallon_hydro_access", "B", 2), ("tallon_great_tree_hall", "T", 0)),
    (("tallon_great_tree_hall", "R", 1), ("tallon_great_tree_chamber", "L", 0)),
    (("tallon_great_tree_hall", "R", 0), ("tallon_tunnel_d", "L", 0)),
    (("tallon_great_tree_hall", "R", 3), ("tallon_life_grove_tunnel", "L", 0)),
    (("tallon_great_tree_hall", "R", 2), ("tallon_tunnel_e", "L", 0)),
    (("tallon_tunnel_d", "R", 0), ("tallon_transport_chozo_south", "L", 1)),
    (("tallon_life_grove_tunnel", "R", 0), ("tallon_life_grove", "L", 0)),
    (("tallon_tunnel_e", "R", 0), ("tallon_transport_mines_east", "L", 1)),
]


# --- progression gates (specs/07k-regioes-b-e-c.md) ------------------------------------------------
# Prime's gates on the links, as they are in Prime (no temporary access): the items a link needs
# and the side(s) of the cap. Source per gate in the spec's table: blast shields and coloured-door
# locks read from Prime's objects (Trigger_DoorKey, "Actor Missile Lock"); the colours (ice, plasma)
# and the Space Jump ledges from what Prime is known to need.
MISSILE, SPACE_JUMP, ICE, XRAY, PLASMA = "missile", "space_jump", "ice", "xray", "plasma"
GRAVITY, WAVE = "gravity", "wave"   # specs/07l (the sunken frigate)
# specs/07m: Morph Ball Bombs (the bomb walls by the Gully door in the Tallon Canyon); Power Bombs
# (the Life Grove's walls round the X-Ray, epic 09: 09e). specs/09a (epic 09, decision 1): the
# Thermal Visor, grapple, X-Ray, Spider Ball and Boost Ball leave the gates (no SM equivalent the
# gates need); the X-Ray stays as what the Life Grove's item gives.
BOMBS, POWER_BOMB = "bombs", "power_bomb"
MORPH = "morph"   # specs/09d: the Morph Ball (the reach model's ball)
# specs/12g (epic 12, decision 2): the Chozo's new locks. Charge Beam = a beam door that opens only to a charged shot
# (tallon/beamdoors.py); Varia Suit = a hot room (RoomDef.heat, chozo/heat.py), modelled as impassable without it: every
# door into a hot room has VARIA in its gate (chozo/rooms.py build_rooms; the user's rule: no damage is ever tanked)
CHARGE, VARIA = "charge", "varia"
# specs/18l (epic 18, user decision 3): the SM's Super Missile (Phendrana's Observatory) is what its item gives; no gate needs it
# (no green door nor super missile block in the game: validate.check_no_super_locks), as the X-Ray: it only adds ammunition and damage
SUPER = "super"
# specs/19f (epic 19, user decision 3a): the SM's Grapple Beam (the Mines' Storage Depot B) is what its item gives; no gate needs it
# (no grapple block nor enemy Samus latches onto in the game: validate.check_no_grapple_locks), as the Super Missile: it only adds
# to the ending's percentage and to the HUD
GRAPPLE = "grapple"
# gates that are geometry, not a cap (specs/09d, epic decision 4; was MOVEMENT): the door's side marked
# `ledge` sits behind geometry those items get through. A Space Jump ledge is out of reach on foot; a
# Gravity Suit ledge is in reach on foot with the suit, out of reach underwater without it; a Morph Ball
# tunnel with bomb blocks (the Tallon Canyon's Gully door) is out of reach without the ball and the
# Bombs, in reach with them. The progression walk lets the geometry decide them (a ledge door may be
# reached from another ledge door, e.g. the Landing Site's Gully and Alcove doors, specs/07m); the other
# items of a gate are needed to go through it either way.
GEOMETRY = frozenset({SPACE_JUMP, GRAVITY, MORPH, BOMBS, POWER_BOMB})
# cap of each item: missile = red door; ice/wave/plasma = beam door (specs/09a, tallon/beamdoors.py:
# opens only with a shot of that beam; green, grey, orange). No grey "never opens" door is left in the
# Tallon (specs/09d: the Gully's bomb walls are bomb blocks in a Morph Ball tunnel).
LOCK_OF = {MISSILE: "missile", ICE: "ice", WAVE: "wave", PLASMA: "plasma", CHARGE: "charge"}   # 12g: charge
BEAM_LOCKS = frozenset({ICE, WAVE, PLASMA, CHARGE})
MISSILE_DOOR_BIT0 = 0xB0     # red doors' bits ($7ED8B0): vanilla uses 0-172 (validate.check_gates)


@dataclass(frozen=True)
class Gate:
    items: frozenset[str]
    capped: tuple[str, ...] = ()   # rooms whose side of the door has the cap
    ledge: tuple[str, ...] = ()    # rooms whose side of the door is behind the GEOMETRY items


GATES = {
    frozenset({"tallon_temple_security", "tallon_temple_lobby"}): Gate(frozenset({MISSILE}), ("tallon_temple_security",)),
    frozenset({"tallon_waterfall_cavern", "tallon_crash_site"}): Gate(frozenset({MISSILE}), ("tallon_waterfall_cavern",)),
    frozenset({"tallon_root_tunnel", "tallon_root_cave"}): Gate(frozenset({MISSILE}), ("tallon_root_tunnel",)),
    frozenset({"tallon_crash_site", "tallon_overgrown_cavern"}): Gate(
        frozenset({ICE, SPACE_JUMP}), ("tallon_crash_site", "tallon_overgrown_cavern"), ("tallon_crash_site",)),
    frozenset({"tallon_crash_site", "tallon_frigate_access"}): Gate(
        frozenset({ICE}), ("tallon_crash_site", "tallon_frigate_access")),
    frozenset({"tallon_overgrown_cavern", "tallon_tunnel_c"}): Gate(
        frozenset({ICE}), ("tallon_overgrown_cavern", "tallon_tunnel_c")),
    frozenset({"tallon_tunnel_c", "tallon_transport_chozo_east"}): Gate(
        frozenset({ICE}), ("tallon_tunnel_c", "tallon_transport_chozo_east")),
    frozenset({"tallon_root_cave", "tallon_arbor_chamber"}): Gate(
        frozenset({PLASMA, SPACE_JUMP}), ("tallon_root_cave",), ("tallon_root_cave",)),   # 09a: grapple/X-Ray out
    # region D (specs/07l): Prime needs the Gravity Suit under water (knowledge): the Main Ventilation
    # Shaft Section C (no lock on its doors in the data) is reachable after the ice door, its door on
    # to Section B sits behind a bulkhead the underwater jump without the suit can't climb
    frozenset({"tallon_vent_c", "tallon_vent_b"}): Gate(frozenset({GRAVITY}), (), ("tallon_vent_c",)),
    # power-conduit doors (data: "Thermal Door Scan" + thermal panels by the dock, no blast shield;
    # Thermal Visor to see the conduits, Wave Beam to charge them: knowledge). Reactor Core <->
    # Reactor Access and Reactor Access <-> Cargo Lift have no unlock trigger on either side.
    # specs/09a: wave doors, the Wave Beam alone (the SM has no Thermal Visor)
    frozenset({"tallon_reactor_core", "tallon_reactor_access"}): Gate(
        frozenset({WAVE}), ("tallon_reactor_core", "tallon_reactor_access")),
    frozenset({"tallon_reactor_access", "tallon_cargo_lift"}): Gate(
        frozenset({WAVE}), ("tallon_reactor_access", "tallon_cargo_lift")),
    frozenset({"tallon_cargo_lift", "tallon_transit_hall"}): Gate(frozenset({WAVE}), ("tallon_cargo_lift",)),
    frozenset({"tallon_biohazard", "tallon_security_hall"}): Gate(frozenset({WAVE}), ("tallon_biohazard",)),
    frozenset({"tallon_biotech_1", "tallon_conduit_hall"}): Gate(frozenset({WAVE}), ("tallon_biotech_1",)),
    # Gully and Alcove (region A, specs/07m). Tallon Canyon -> Gully: two "Breakable Block"s and a
    # "RumbleEffect_bomb_walls" by the Gully dock, normal shields on both docks (data): Morph Ball Bombs
    # (knowledge). specs/09d: a Morph Ball tunnel with two bomb blocks before the platform under the
    # Gully door (tallon/layouts.py), no cap (07m had a grey one). The Landing Site's Gully and Alcove doors are on a
    # high ledge in the west cliff (docks 7.5 m above the Canyon Cavern one, data; out of reach from the
    # ground without the Space Jump, knowledge, uncertain): the Gully leads up onto it, and from it the
    # Alcove (Prime's Space Jump Boots)
    frozenset({"tallon_canyon", "tallon_gully"}): Gate(frozenset({MORPH, BOMBS}), (), ("tallon_canyon",)),
    frozenset({"tallon_landing_site", "tallon_gully"}): Gate(frozenset({SPACE_JUMP}), (), ("tallon_landing_site",)),
    frozenset({"tallon_landing_site", "tallon_alcove"}): Gate(frozenset({SPACE_JUMP}), (), ("tallon_landing_site",)),
    # region E (specs/07m). Coloured-door shields ("Actor_DoorShield_Key") on both docks of every link
    # but Hydro Access <-> Great Tree Hall, Great Tree Hall <-> Great Tree Chamber and Life Grove Tunnel
    # <-> Life Grove (data); the colour, ice, is knowledge: grey on both sides
    frozenset({"tallon_great_tree_hall", "tallon_tunnel_d"}): Gate(
        frozenset({ICE}), ("tallon_great_tree_hall", "tallon_tunnel_d")),
    frozenset({"tallon_great_tree_hall", "tallon_tunnel_e"}): Gate(
        frozenset({ICE}), ("tallon_great_tree_hall", "tallon_tunnel_e")),
    frozenset({"tallon_tunnel_d", "tallon_transport_chozo_south"}): Gate(
        frozenset({ICE}), ("tallon_tunnel_d", "tallon_transport_chozo_south")),
    frozenset({"tallon_tunnel_e", "tallon_transport_mines_east"}): Gate(
        frozenset({ICE}), ("tallon_tunnel_e", "tallon_transport_mines_east")),
    # the Great Tree Chamber door is 70 m above the Hydro Access one (data), a ledge for the Space Jump
    # (knowledge, uncertain)
    frozenset({"tallon_great_tree_hall", "tallon_great_tree_chamber"}): Gate(
        frozenset({SPACE_JUMP}), (), ("tallon_great_tree_hall",)),
    # to the Life Grove: an ice door (shields: data; colour: knowledge) at the top of the tree's Spider
    # Ball track ("POI_Spiderball Track", "Ice Spidertrack" by the dock: data), then the Life Grove
    # Tunnel's boulder and Morph Ball puzzle ("remove this boulder", "Player Hint_wallpuzzle": data) and
    # the Life Grove's walls round the X-Ray ("Destroyable Wall" x5, "Power Bomb Scan Hint": data):
    # Boost Ball and Power Bombs (knowledge)
    frozenset({"tallon_great_tree_hall", "tallon_life_grove_tunnel"}): Gate(
        frozenset({ICE}), ("tallon_great_tree_hall", "tallon_life_grove_tunnel")),   # 09a: Spider/Boost/PB out
}

# one door bit per red door link, in GATES order
MISSILE_BITS = {k: MISSILE_DOOR_BIT0 + n for n, k in enumerate(k for k, g in GATES.items() if MISSILE in g.items)}

# The round at which each room first becomes reachable from the Landing Site gunship (specs/09f, epic 09
# decision 3; replaces 07k's hypothetical TIERS/FIRST_TIER). Round 0 = the arrival, Power Beam only; round k
# = with every item picked up in rounds 0..k-1 (the validator walks them, tools/validate.py tallon_rounds,
# and compares). What opens each round: 1 the Landing Site missile (red doors) and the Morph Ball; 2 the
# Bombs (the Tallon Canyon's Morph Ball tunnel to the Gully); 3 the Space Jump (no new room: the Root Cave
# shelf); 4 the Ice (ice doors); 5 the Gravity Suit (Section C's bulkhead, then regions D and E); 6 the
# Plasma (the Arbor Chamber).
_ROUNDS = [
    ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", "tallon_transport_chozo_west",
     "tallon_temple_hall", "tallon_temple_security", "tallon_waterfall_cavern", "tallon_root_tunnel"],
    ["tallon_temple_lobby", "tallon_artifact_temple", "tallon_crash_site", "tallon_root_cave", "tallon_tunnel_b",
     "tallon_transport_magmoor_east"],
    ["tallon_gully", "tallon_alcove"],
    [],
    ["tallon_overgrown_cavern", "tallon_tunnel_c", "tallon_transport_chozo_east", "tallon_frigate_access", "tallon_vent_c"],
    ["tallon_vent_b", "tallon_vent_a", "tallon_reactor_core", "tallon_reactor_access", "tallon_cargo_lift",
     "tallon_savestation", "tallon_transit_hall", "tallon_biohazard", "tallon_security_hall", "tallon_biotech_1",
     "tallon_conduit_hall", "tallon_elevator_beta", "tallon_hydro_access", "tallon_great_tree_hall",
     "tallon_great_tree_chamber", "tallon_tunnel_d", "tallon_life_grove_tunnel", "tallon_tunnel_e",
     "tallon_transport_chozo_south", "tallon_life_grove", "tallon_transport_mines_east"],
    ["tallon_arbor_chamber"],
]
FIRST_ROUND = {k: n for n, keys in enumerate(_ROUNDS) for k in keys}


def placeholder(w: int, h: int) -> Canvas:
    """Open box until the room's layout is drawn."""
    c = Canvas(w, h)
    c.carve(1, 2, w * 16 - 2, h * 16 - 3)
    return c


def build_rooms(regions, only=None) -> list[RoomDef]:
    """RoomDefs of the rooms in `regions` (and in `only`, if given), in TABLE order, with the doors
    between them; a link to a room left out is left out too (wall)."""
    regions = set(regions)
    unknown = regions - set(REGIONS)
    if unknown:
        raise ValueError(f"regiões desconhecidas: {sorted(unknown)}")
    if only is not None:
        outside = set(only) - {t.key for t in TABLE if t.region in regions}
        if outside:
            raise ValueError(f"salas ativas fora das regiões ativas: {sorted(outside)}")
    rooms: dict[str, RoomDef] = {}
    for t in TABLE:
        if t.region not in regions or (only is not None and t.key not in only):
            continue
        w, h = screens(t.box)
        style, tileset = LOOKS[t.look]
        shape = LAYOUTS[t.key]() if t.key in LAYOUTS else None
        canvas = shape.canvas if shape else placeholder(w, h)
        if (canvas.w, canvas.h) != (w * 16, h * 16):
            raise ValueError(f"{t.key}: desenho {canvas.w}x{canvas.h} blocos, a tabela diz {w}x{h} telas")
        rooms[t.key] = RoomDef(t.key, t.prime, t.name, w, h, t.map_x, t.map_y, canvas,
                               style=style, tileset=tileset,
                               fx=crateria.RAIN_FX if t.key in RAIN else 0x0000, water=t.key in FLOODED,
                               library_bg={CAV: CAVE_BG, FRI: FRIGATE_BG}.get(t.look),
                               layer2=FRIGATE_LAYER2 if t.look == FRI else None,
                               ship=shape.ship if shape else None, save_station=shape.save if shape else None,
                               skin=shape.skin if shape else [], backdrop=shape.backdrop if shape else [],
                               blocks=shape.blocks if shape else [], elevator=shape.elevator if shape else None)
    for (ra, sa, na), (rb, sb, nb) in LINKS:
        if OPPOSITE[sa] != sb:
            raise ValueError(f"porta {ra}.{sa} liga em {rb}.{sb}: lados precisam ser opostos")
        if ra not in rooms or rb not in rooms:
            continue
        da, db = DoorLink(sa, na, rb), DoorLink(sb, nb, ra)
        gate = GATES.get(frozenset({ra, rb}))
        if gate:
            caps = {LOCK_OF[i] for i in gate.items if i in LOCK_OF}
            # one kind of cap and its side(s), or none at all (a movement-only gate: a ledge)
            if (len(caps) > 1 or bool(caps) != bool(gate.capped) or not set(gate.capped) <= {ra, rb}
                    or not set(gate.ledge) <= {ra, rb} or bool(gate.ledge) != bool(gate.items & GEOMETRY)):
                raise ValueError(f"trava {ra}-{rb}: precisa de um tipo de tampa e do lado dela ({gate})")
            cap = caps.pop() if caps else None
            for d, key in ((da, ra), (db, rb)):
                d.gate, d.ledge = gate.items, key in gate.ledge
                if key in gate.capped:
                    d.lock, d.lock_bit = cap, MISSILE_BITS.get(frozenset({ra, rb}))
        rooms[ra].doors.append(da)
        rooms[rb].doors.append(db)
        da.to_door = len(rooms[rb].doors) - 1
        db.to_door = len(rooms[ra].doors) - 1
    return list(rooms.values())


def region_of(key: str) -> str:
    return next(t.region for t in TABLE if t.key == key)


def check_prime(worlds_json: Path) -> list[str]:
    """TABLE and LINKS against Prime's data: every room once with its name and box, every region
    known, the links = Prime's door pairs, and the rain rooms in the table."""
    world = next(w for w in json.loads(worlds_json.read_text()) if w["name"] == "Tallon Overworld")
    prime = {a["index"]: a for a in world["areas"]}
    problems = []
    by_prime = {t.prime: t for t in TABLE}
    if len(by_prime) != len(TABLE) or set(by_prime) != set(prime):
        problems.append(f"tabela tem as salas {sorted(by_prime)}, o Prime tem {sorted(prime)}")
    if len({t.key for t in TABLE}) != len(TABLE):
        problems.append("chave de sala repetida na tabela")
    for t in TABLE:
        if t.region not in REGIONS or t.look not in LOOKS:
            problems.append(f"{t.key}: região {t.region!r} / visual {t.look!r} desconhecidos")
        a = prime.get(t.prime)
        if a is None:
            continue
        b = a["aabb"]
        box = tuple(round(b[i + 3] - b[i]) for i in range(3))
        if (a["name"], box) != (t.name, t.box):
            problems.append(f"{t.key}: P{t.prime} no Prime é {a['name']!r} {box}, a tabela diz {t.name!r} {t.box}")
    key_prime = {t.key: t.prime for t in TABLE}
    ours = [frozenset((key_prime.get(a[0]), key_prime.get(b[0]))) for a, b in LINKS]
    theirs = {frozenset((a["index"], d["to_area"])) for a in world["areas"] for d in a["docks"]}
    if len(set(ours)) != len(ours) or set(ours) != theirs:
        problems.append(f"ligações diferentes do Prime: sobram {sorted(map(sorted, set(ours) - theirs))}, "
                        f"faltam {sorted(map(sorted, theirs - set(ours)))}")
    if not RAIN <= set(key_prime):
        problems.append(f"chuva em salas fora da tabela: {sorted(RAIN - set(key_prime))}")
    return problems


ALL_ROOMS = build_rooms(REGIONS)        # the whole world, for the validator's map checks
ROOMS = build_rooms(ACTIVE_REGIONS, ACTIVE_ROOMS)     # what the build gets

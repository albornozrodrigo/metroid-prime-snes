"""Chozo Ruins rooms (SM area 1, specs/12b): the room graph, the map and Prime's locks (specs/12c-grafo-e-mapa-chozo.md).

All 64 rooms of Prime's Chozo Ruins (research/prime_worlds.json, MLVL "Chozo Ruins"), one SM room per Prime room (epic 12,
decision 2), with the Prime door graph in LINKS (68 pairs, 136 docks, all with their way back). The size comes from the
Prime box by the Tallon's rule (tallon/rooms.py `screens`: 30 m a screen, at most 6 x 4).

Map: x/y in area 1's 64x32 pause-map grid. Prime is 3D, so only the pairs of linked rooms come from it; the sides and
screens of the doors were found by a search (a discarded script, as in specs/07d) that keeps every door touching its
neighbour, few floor/ceiling doors (15 of 68: rooms 1 screen tall with 3+ doors, and the 5 loops of the graph, need some),
the saved map small (41 bytes of the 80 of area 1's vanilla list place) and Prime's west-east/north-south order loosely.
The validator checks the whole table (tools/validate.py check_chozo) and each region alone.

Regions (epic, "Regiões"): A entrance, Main Plaza and the Tower of Light; B north wing (Nursery, Gallery, Hive Totem,
Vault); C fountain, Arboretum, Sunchamber, Sun Tower; D Watery Hall, Energy Core, Burn Dome; E Elders, Reflecting Pool and
the ways out to the Tallon.

Built (specs/12e): the three elevator rooms to the Tallon (ELEVATOR_ROOMS, drawn in tools/chozo/layouts.py), as dead ends
until their regions come; specs/12f: region A (ACTIVE_REGIONS), whose links to the rooms of regions B-E stay walls until
those regions are built; specs/12i: region B (the Nursery Access and Plaza Access doors open; its doors to region C, the
Magmoor transport's to the Sun Tower, stay walls); specs/12j: region C (the Ruined Fountain Access', the Piston Tunnel's
and the Magmoor transport's doors open; the Gathering Hall's two doors to region D stay walls); specs/12k: region D (the
Gathering Hall's two doors open; the Furnace's two doors to region E stay walls); specs/12l: region E, the last (the
Furnace's two doors and the East and South elevator rooms' doors open: all 64 rooms built). ALL_ROOMS (placeholder boxes, but the drawn rooms with their layout) is for the validator's table
and map checks. Prime's locks are recorded as data (DOCK_LOCKS, FEATURES), read from Prime's objects
(research/prime_chozo_locks.json, written by tools/dump_prime_locks.py). specs/12f maps the ones of region A to the
Tallon's items (epic 12, decision B): GATES and ONE_WAY below, the rounds in FIRST_ROUND.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from frigate.rooms import OPPOSITE, DoorLink, RoomDef
from smlib import ruins
from tallon.rooms import BOMBS as BOMBS_ITEM, GEOMETRY, GRAVITY, ICE, LOCK_OF, MISSILE as MISSILE_ITEM, MORPH as MORPH_ITEM
from tallon.rooms import SPACE_JUMP, VARIA, WAVE
from tallon.rooms import Gate, placeholder, screens

from .layouts import LAYOUTS

REGIONS = {
    "A": "Entrada, Main Plaza e Torre da Luz",
    "B": "Ala norte: Nursery, Gallery, Hive Totem e Vault",
    "C": "Fonte, Arboreto, Sunchamber e Sun Tower",
    "D": "Watery Hall, Energy Core e Burn Dome",
    "E": "Elders, Reflecting Pool e as saídas para o Tallon",
}
ACTIVE_REGIONS: frozenset[str] = frozenset({"A", "B", "C", "D", "E"})   # 12c: none; specs/12f: A; 12i: B; 12j: C; 12k: D; 12l: E
# specs/12e: rooms built outside the active regions: the three elevator rooms to the Tallon (tools/areas.py ELEVATORS),
# dead ends until their regions are built
ELEVATOR_ROOMS = frozenset({"chozo_transport_tallon_north", "chozo_transport_tallon_east", "chozo_transport_tallon_south"})


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
    # key, Prime index, Prime name, region, Prime box (m), map x, map y
    # --- A ---
    Row("chozo_transport_tallon_north", 0, "Transport to Tallon Overworld North", "A", (32, 40, 66), 13, 11),
    Row("chozo_ruins_entrance", 1, "Ruins Entrance", "A", (64, 74, 33), 14, 12),
    Row("chozo_main_plaza", 2, "Main Plaza", "A", (107, 183, 62), 16, 12),
    Row("chozo_ruined_fountain_access", 3, "Ruined Fountain Access", "A", (90, 38, 18), 22, 13),
    Row("chozo_ruined_shrine_access", 4, "Ruined Shrine Access", "A", (92, 31, 11), 13, 13),
    Row("chozo_nursery_access", 5, "Nursery Access", "A", (44, 29, 6), 16, 11),
    Row("chozo_plaza_access", 6, "Plaza Access", "A", (41, 54, 14), 17, 11),
    Row("chozo_piston_tunnel", 7, "Piston Tunnel", "A", (7, 56, 30), 15, 14),
    Row("chozo_ruined_shrine", 9, "Ruined Shrine", "A", (73, 82, 31), 10, 13),
    Row("chozo_tower_of_light_access", 15, "Tower of Light Access", "A", (54, 30, 8), 8, 13),
    Row("chozo_tower_of_light", 21, "Tower of Light", "A", (60, 96, 125), 5, 13),
    Row("chozo_tower_chamber", 27, "Tower Chamber", "A", (21, 20, 15), 4, 16),
    # --- B ---
    Row("chozo_eyon_tunnel", 10, "Eyon Tunnel", "B", (46, 39, 11), 14, 11),
    Row("chozo_vault", 11, "Vault", "B", (57, 80, 16), 19, 11),
    Row("chozo_ruined_nursery", 16, "Ruined Nursery", "B", (51, 51, 23), 13, 10),
    Row("chozo_vault_access", 17, "Vault Access", "B", (17, 106, 31), 16, 10),
    Row("chozo_save_station_1", 22, "Save Station 1", "B", (11, 23, 14), 15, 10),
    Row("chozo_north_atrium", 23, "North Atrium", "B", (49, 32, 12), 11, 10),
    Row("chozo_transport_magmoor_north", 24, "Transport to Magmoor Caverns North", "B", (41, 40, 53), 20, 9),
    Row("chozo_ruined_gallery", 28, "Ruined Gallery", "B", (57, 55, 24), 10, 9),
    Row("chozo_transport_access_north", 30, "Transport Access North", "B", (78, 31, 23), 17, 9),
    Row("chozo_totem_access", 33, "Totem Access", "B", (63, 54, 22), 12, 9),
    Row("chozo_map_station", 34, "Map Station", "B", (23, 10, 14), 9, 9),
    Row("chozo_hive_totem", 36, "Hive Totem", "B", (87, 87, 33), 14, 9),
    # --- C ---
    Row("chozo_ruined_fountain", 8, "Ruined Fountain", "C", (73, 70, 29), 25, 13),
    Row("chozo_training_chamber", 12, "Training Chamber", "C", (38, 73, 32), 17, 14),
    Row("chozo_arboretum_access", 13, "Arboretum Access", "C", (54, 93, 55), 27, 13),
    Row("chozo_meditation_fountain", 14, "Meditation Fountain", "C", (49, 41, 16), 24, 14),
    Row("chozo_training_chamber_access", 18, "Training Chamber Access", "C", (65, 38, 19), 19, 14),
    Row("chozo_arboretum", 19, "Arboretum", "C", (80, 95, 91), 30, 13),
    Row("chozo_magma_pool", 20, "Magma Pool", "C", (51, 93, 24), 21, 14),
    Row("chozo_sunchamber_lobby", 25, "Sunchamber Lobby", "C", (61, 21, 15), 33, 13),
    Row("chozo_gathering_hall_access", 26, "Gathering Hall Access", "C", (49, 16, 20), 33, 15),
    Row("chozo_sun_tower", 29, "Sun Tower", "C", (63, 43, 94), 21, 8),
    Row("chozo_sunchamber_access", 31, "Sunchamber Access", "C", (60, 18, 20), 32, 12),
    Row("chozo_gathering_hall", 32, "Gathering Hall", "C", (46, 85, 63), 35, 15),
    Row("chozo_sun_tower_access", 35, "Sun Tower Access", "C", (55, 140, 19), 23, 10),
    Row("chozo_sunchamber", 37, "Sunchamber", "C", (118, 133, 84), 28, 10),
    Row("chozo_save_station_2", 39, "Save Station 2", "C", (10, 23, 14), 34, 16),
    # --- D ---
    Row("chozo_watery_hall_access", 38, "Watery Hall Access", "D", (38, 86, 16), 38, 15),
    Row("chozo_east_atrium", 40, "East Atrium", "D", (32, 49, 15), 38, 16),
    Row("chozo_watery_hall", 41, "Watery Hall", "D", (85, 126, 55), 41, 14),
    Row("chozo_energy_core_access", 42, "Energy Core Access", "D", (47, 28, 11), 40, 16),
    Row("chozo_dynamo_access", 43, "Dynamo Access", "D", (30, 44, 7), 45, 14),
    Row("chozo_energy_core", 44, "Energy Core", "D", (81, 109, 37), 42, 16),
    Row("chozo_dynamo", 45, "Dynamo", "D", (27, 25, 41), 46, 14),
    Row("chozo_burn_dome_access", 46, "Burn Dome Access", "D", (13, 66, 8), 45, 15),
    Row("chozo_west_furnace_access", 47, "West Furnace Access", "D", (44, 31, 6), 46, 16),
    Row("chozo_burn_dome", 48, "Burn Dome", "D", (48, 85, 22), 47, 15),
    Row("chozo_furnace", 49, "Furnace", "D", (107, 87, 58), 47, 16),
    # --- E ---
    Row("chozo_east_furnace_access", 50, "East Furnace Access", "E", (44, 31, 6), 50, 18),
    Row("chozo_crossway_access_west", 51, "Crossway Access West", "E", (61, 66, 17), 51, 16),
    Row("chozo_hall_of_the_elders", 52, "Hall of the Elders", "E", (90, 72, 52), 51, 18),
    Row("chozo_crossway", 53, "Crossway", "E", (82, 41, 53), 53, 16),
    Row("chozo_reflecting_pool_access", 54, "Reflecting Pool Access", "E", (31, 44, 6), 53, 20),
    Row("chozo_elder_hall_access", 55, "Elder Hall Access", "E", (36, 58, 10), 54, 18),
    Row("chozo_crossway_access_south", 56, "Crossway Access South", "E", (30, 48, 24), 51, 17),
    Row("chozo_elder_chamber", 57, "Elder Chamber", "E", (34, 21, 11), 54, 19),
    Row("chozo_reflecting_pool", 58, "Reflecting Pool", "E", (39, 88, 42), 51, 21),
    Row("chozo_save_station_3", 59, "Save Station 3", "E", (80, 20, 14), 51, 22),
    Row("chozo_transport_access_south", 60, "Transport Access South", "E", (23, 40, 9), 54, 21),
    Row("chozo_antechamber", 61, "Antechamber", "E", (24, 21, 9), 50, 21),
    Row("chozo_transport_tallon_east", 62, "Transport to Tallon Overworld East", "E", (41, 35, 62), 50, 22),
    Row("chozo_transport_tallon_south", 63, "Transport to Tallon Overworld South", "E", (33, 40, 57), 55, 21),
]

# (room, side, screen) <-> (room, side, screen), one per Prime door pair; sides opposite (R-L, B-T)
LINKS = [
    (("chozo_transport_tallon_north", "R", 1), ("chozo_ruins_entrance", "L", 0)),
    (("chozo_ruins_entrance", "R", 0), ("chozo_main_plaza", "L", 0)),
    (("chozo_main_plaza", "R", 1), ("chozo_ruined_fountain_access", "L", 0)),
    (("chozo_main_plaza", "L", 1), ("chozo_ruined_shrine_access", "R", 0)),
    (("chozo_main_plaza", "T", 0), ("chozo_nursery_access", "B", 0)),
    (("chozo_main_plaza", "T", 1), ("chozo_plaza_access", "B", 0)),
    (("chozo_main_plaza", "B", 0), ("chozo_piston_tunnel", "T", 1)),
    (("chozo_ruined_fountain_access", "R", 0), ("chozo_ruined_fountain", "L", 0)),
    (("chozo_ruined_shrine_access", "L", 0), ("chozo_ruined_shrine", "R", 0)),
    (("chozo_nursery_access", "L", 0), ("chozo_eyon_tunnel", "R", 0)),
    (("chozo_plaza_access", "R", 0), ("chozo_vault", "L", 0)),
    (("chozo_piston_tunnel", "R", 0), ("chozo_training_chamber", "L", 0)),
    (("chozo_ruined_fountain", "R", 0), ("chozo_arboretum_access", "L", 0)),
    (("chozo_ruined_fountain", "B", 0), ("chozo_meditation_fountain", "T", 1)),
    (("chozo_ruined_shrine", "L", 0), ("chozo_tower_of_light_access", "R", 0)),
    (("chozo_eyon_tunnel", "T", 0), ("chozo_ruined_nursery", "B", 1)),
    (("chozo_vault", "T", 0), ("chozo_vault_access", "B", 3)),
    (("chozo_training_chamber", "R", 0), ("chozo_training_chamber_access", "L", 0)),
    (("chozo_arboretum_access", "R", 0), ("chozo_arboretum", "L", 0)),
    (("chozo_meditation_fountain", "L", 0), ("chozo_magma_pool", "R", 0)),
    (("chozo_tower_of_light_access", "L", 0), ("chozo_tower_of_light", "R", 0)),
    (("chozo_ruined_nursery", "R", 0), ("chozo_save_station_1", "L", 0)),
    (("chozo_ruined_nursery", "L", 0), ("chozo_north_atrium", "R", 0)),
    (("chozo_vault_access", "R", 0), ("chozo_transport_magmoor_north", "L", 1)),
    (("chozo_training_chamber_access", "R", 0), ("chozo_magma_pool", "L", 0)),
    (("chozo_arboretum", "R", 0), ("chozo_sunchamber_lobby", "L", 0)),
    (("chozo_arboretum", "R", 2), ("chozo_gathering_hall_access", "L", 0)),
    (("chozo_tower_of_light", "L", 3), ("chozo_tower_chamber", "R", 0)),
    (("chozo_north_atrium", "T", 0), ("chozo_ruined_gallery", "B", 1)),
    (("chozo_transport_magmoor_north", "R", 0), ("chozo_sun_tower", "L", 1)),
    (("chozo_transport_magmoor_north", "L", 0), ("chozo_transport_access_north", "R", 0)),
    (("chozo_sunchamber_lobby", "T", 0), ("chozo_sunchamber_access", "B", 1)),
    (("chozo_gathering_hall_access", "R", 0), ("chozo_gathering_hall", "L", 0)),
    (("chozo_ruined_gallery", "R", 0), ("chozo_totem_access", "L", 0)),
    (("chozo_ruined_gallery", "L", 0), ("chozo_map_station", "R", 0)),
    (("chozo_sun_tower", "R", 2), ("chozo_sun_tower_access", "L", 0)),
    (("chozo_transport_access_north", "L", 0), ("chozo_hive_totem", "R", 0)),
    (("chozo_sunchamber_access", "L", 0), ("chozo_sunchamber", "R", 2)),
    (("chozo_gathering_hall", "R", 0), ("chozo_watery_hall_access", "L", 0)),
    (("chozo_gathering_hall", "L", 1), ("chozo_save_station_2", "R", 0)),
    (("chozo_gathering_hall", "R", 1), ("chozo_east_atrium", "L", 0)),
    (("chozo_totem_access", "R", 0), ("chozo_hive_totem", "L", 0)),
    (("chozo_sun_tower_access", "R", 0), ("chozo_sunchamber", "L", 0)),
    (("chozo_watery_hall_access", "R", 0), ("chozo_watery_hall", "L", 1)),
    (("chozo_east_atrium", "R", 0), ("chozo_energy_core_access", "L", 0)),
    (("chozo_watery_hall", "R", 0), ("chozo_dynamo_access", "L", 0)),
    (("chozo_energy_core_access", "R", 0), ("chozo_energy_core", "L", 0)),
    (("chozo_dynamo_access", "R", 0), ("chozo_dynamo", "L", 0)),
    (("chozo_energy_core", "T", 3), ("chozo_burn_dome_access", "B", 0)),
    (("chozo_energy_core", "R", 0), ("chozo_west_furnace_access", "L", 0)),
    (("chozo_burn_dome_access", "R", 0), ("chozo_burn_dome", "L", 0)),
    (("chozo_west_furnace_access", "R", 0), ("chozo_furnace", "L", 0)),
    (("chozo_furnace", "B", 3), ("chozo_east_furnace_access", "T", 0)),
    (("chozo_furnace", "R", 0), ("chozo_crossway_access_west", "L", 0)),
    (("chozo_east_furnace_access", "R", 0), ("chozo_hall_of_the_elders", "L", 0)),
    (("chozo_crossway_access_west", "R", 0), ("chozo_crossway", "L", 0)),
    (("chozo_hall_of_the_elders", "B", 2), ("chozo_reflecting_pool_access", "T", 0)),
    (("chozo_hall_of_the_elders", "R", 0), ("chozo_elder_hall_access", "L", 0)),
    (("chozo_hall_of_the_elders", "T", 0), ("chozo_crossway_access_south", "B", 0)),
    (("chozo_hall_of_the_elders", "R", 1), ("chozo_elder_chamber", "L", 0)),
    (("chozo_crossway", "B", 1), ("chozo_elder_hall_access", "T", 0)),
    (("chozo_crossway", "L", 1), ("chozo_crossway_access_south", "R", 0)),
    (("chozo_reflecting_pool_access", "B", 0), ("chozo_reflecting_pool", "T", 2)),
    (("chozo_reflecting_pool", "B", 0), ("chozo_save_station_3", "T", 0)),
    (("chozo_reflecting_pool", "R", 0), ("chozo_transport_access_south", "L", 0)),
    (("chozo_reflecting_pool", "L", 0), ("chozo_antechamber", "R", 0)),
    (("chozo_save_station_3", "L", 0), ("chozo_transport_tallon_east", "R", 0)),
    (("chozo_transport_access_south", "R", 0), ("chozo_transport_tallon_south", "L", 0)),
]

# --- Prime's locks, as data (specs/12c) ------------------------------------------------------------------------------
# Per dock (this room, the room the door leads to): the kinds of lock Prime has there, read from the objects at the dock
# (research/prime_chozo_locks.json; prime_dock_locks below gives the rule, the validator compares):
#   missile  "Actor Missile Lock": a blast shield that opens with missiles (the 07k rule);
#   key      "Trigger_DoorKey" without a missile lock: a coloured (beam) door; the colour is not in the names;
#   morph    the dock's door is "Door_Area Morphball": a Morph Ball tunnel door;
#   event    "Actor Door Lock": the door locks during an event (a fight: Flaahgra, the Incinerator Drone, ghosts...);
#   one_way  a "one way door" scan at the dock.
# No SM mechanism or item is chosen here (12g, after the user's decision).
MISSILE, KEY, MORPH, EVENT, ONE_WAY = "missile", "key", "morph", "event", "one_way"
DOCK_LOCKS = {
    ("chozo_main_plaza", "chozo_ruined_shrine_access"): {"missile"},
    ("chozo_main_plaza", "chozo_plaza_access"): {"one_way"},
    ("chozo_main_plaza", "chozo_piston_tunnel"): {"morph"},
    ("chozo_piston_tunnel", "chozo_main_plaza"): {"morph"},
    ("chozo_piston_tunnel", "chozo_training_chamber"): {"morph"},
    ("chozo_ruined_shrine", "chozo_tower_of_light_access"): {"key"},
    ("chozo_training_chamber", "chozo_training_chamber_access"): {"event", "key"},
    ("chozo_training_chamber", "chozo_piston_tunnel"): {"morph"},
    ("chozo_arboretum_access", "chozo_arboretum"): {"missile"},
    ("chozo_tower_of_light_access", "chozo_tower_of_light"): {"key"},
    ("chozo_training_chamber_access", "chozo_magma_pool"): {"key"},
    ("chozo_training_chamber_access", "chozo_training_chamber"): {"key"},
    ("chozo_arboretum", "chozo_sunchamber_lobby"): {"missile"},
    ("chozo_arboretum", "chozo_gathering_hall_access"): {"missile"},
    ("chozo_magma_pool", "chozo_training_chamber_access"): {"key"},
    ("chozo_tower_of_light", "chozo_tower_of_light_access"): {"key"},
    ("chozo_tower_of_light", "chozo_tower_chamber"): {"key"},
    ("chozo_tower_chamber", "chozo_tower_of_light"): {"key"},
    ("chozo_ruined_gallery", "chozo_map_station"): {"missile"},
    ("chozo_transport_access_north", "chozo_hive_totem"): {"missile"},
    ("chozo_gathering_hall", "chozo_save_station_2"): {"missile"},
    ("chozo_hive_totem", "chozo_transport_access_north"): {"missile"},
    ("chozo_sunchamber", "chozo_sun_tower_access"): {"event"},
    ("chozo_watery_hall_access", "chozo_watery_hall"): {"missile"},
    ("chozo_watery_hall", "chozo_dynamo_access"): {"missile"},
    ("chozo_dynamo_access", "chozo_dynamo"): {"missile"},
    ("chozo_energy_core", "chozo_burn_dome_access"): {"morph"},
    ("chozo_energy_core", "chozo_west_furnace_access"): {"event"},
    ("chozo_burn_dome_access", "chozo_energy_core"): {"morph"},
    ("chozo_burn_dome", "chozo_burn_dome_access"): {"event"},
    ("chozo_furnace", "chozo_east_furnace_access"): {"key"},
    ("chozo_furnace", "chozo_crossway_access_west"): {"morph"},
    ("chozo_east_furnace_access", "chozo_hall_of_the_elders"): {"key"},
    ("chozo_east_furnace_access", "chozo_furnace"): {"key"},
    ("chozo_crossway_access_west", "chozo_crossway"): {"key"},
    ("chozo_crossway_access_west", "chozo_furnace"): {"morph"},
    ("chozo_hall_of_the_elders", "chozo_reflecting_pool_access"): {"event"},
    ("chozo_hall_of_the_elders", "chozo_elder_hall_access"): {"event"},
    ("chozo_hall_of_the_elders", "chozo_east_furnace_access"): {"event", "key"},
    ("chozo_hall_of_the_elders", "chozo_crossway_access_south"): {"event", "key"},
    ("chozo_hall_of_the_elders", "chozo_elder_chamber"): {"key"},
    ("chozo_crossway", "chozo_crossway_access_south"): {"key"},
    ("chozo_crossway", "chozo_elder_hall_access"): {"missile"},
    ("chozo_crossway_access_south", "chozo_crossway"): {"key"},
    ("chozo_crossway_access_south", "chozo_hall_of_the_elders"): {"key"},
    ("chozo_elder_chamber", "chozo_hall_of_the_elders"): {"key"},
    ("chozo_reflecting_pool", "chozo_save_station_3"): {"missile"},
    ("chozo_reflecting_pool", "chozo_transport_access_south"): {"key"},
    ("chozo_reflecting_pool", "chozo_antechamber"): {"missile"},
    ("chozo_transport_access_south", "chozo_reflecting_pool"): {"key"},
    ("chozo_antechamber", "chozo_reflecting_pool"): {"key"},
}

# In-room features of Prime that gate movement (same file; names of the room's objects): spider (Spider Ball track),
# bomb_slot, breakable (bomb walls, breakable blocks), halfpipe (Boost Ball), grapple, heat (Varia checks), water, lava,
# morph_door (a Morph Ball tunnel door, also inside a room)
FEATURES = {
    "chozo_main_plaza": {"grapple", "halfpipe", "morph_door"},
    "chozo_piston_tunnel": {"morph_door"},
    "chozo_ruined_fountain": {"heat", "spider", "water"},
    "chozo_ruined_shrine": {"breakable", "halfpipe", "heat", "spider"},
    "chozo_training_chamber": {"bomb_slot", "halfpipe", "morph_door", "spider"},
    "chozo_meditation_fountain": {"heat", "lava", "water"},
    "chozo_training_chamber_access": {"heat"},
    "chozo_arboretum": {"breakable", "heat", "water"},
    "chozo_magma_pool": {"grapple", "heat", "lava", "water"},
    "chozo_tower_of_light": {"water"},
    "chozo_ruined_gallery": {"heat", "water"},
    "chozo_sun_tower": {"spider"},
    "chozo_gathering_hall": {"water"},
    "chozo_totem_access": {"water"},
    "chozo_sun_tower_access": {"water"},
    "chozo_hive_totem": {"water"},
    "chozo_sunchamber": {"bomb_slot", "heat", "water"},
    "chozo_watery_hall_access": {"water"},
    "chozo_watery_hall": {"breakable", "water"},
    "chozo_energy_core_access": {"breakable"},
    "chozo_energy_core": {"bomb_slot", "morph_door", "water"},
    "chozo_dynamo": {"spider"},
    "chozo_burn_dome_access": {"morph_door"},
    "chozo_burn_dome": {"breakable", "water"},
    "chozo_furnace": {"halfpipe", "morph_door", "spider"},
    "chozo_crossway_access_west": {"halfpipe", "morph_door"},
    "chozo_hall_of_the_elders": {"halfpipe", "morph_door", "spider"},
    "chozo_crossway": {"bomb_slot", "halfpipe", "spider"},
    "chozo_elder_hall_access": {"halfpipe"},
    "chozo_crossway_access_south": {"halfpipe"},
    "chozo_reflecting_pool": {"water"},
}


def prime_dock_locks(objects: list) -> set[str]:
    """The lock kinds of one dock from its objects ([type, name, layer]), by the rule above."""
    names = [o[1] for o in objects]
    kinds = set()
    if "Actor Missile Lock" in names:
        kinds.add(MISSILE)
    elif any(n.startswith("Trigger_DoorKey") for n in names):
        kinds.add(KEY)
    if any(o[0] == "Door" and o[1].startswith("Door_Area Morphball") for o in objects):
        kinds.add(MORPH)
    if "Actor Door Lock" in names:
        kinds.add(EVENT)
    if any("one way door" in n.lower() for n in names):
        kinds.add(ONE_WAY)
    return kinds


# --- region A's locks in the SM (specs/12f; epic 12, decision B: the Tallon's items) ---------------------------------------
# Each Prime lock of DOCK_LOCKS on a link of a built region becomes one of the Tallon's mechanisms, with the Tallon's gate
# items (tallon/rooms.py): missile = red door (door bit from CHOZO_MISSILE_BIT0); key (a coloured door; the colour is not in
# Prime's data) = beam door of the colour Prime is known to have (knowledge, specs/12c: the Tower of Light's doors are
# purple, Wave Beam); morph = a Morph Ball tunnel in front of the door (geometry: the door's side marked `ledge`, as the
# Tallon Canyon's, specs/09d). Prime's in-room features (FEATURES) the drawings turn into items behind geometry
# (chozo/items.py: Space Jump ledges for the Boost Ball half-pipes and the grapple ledge, a tunnel with a bomb block, a
# hut of power bomb blocks for the Super Missile tree).
CHOZO_MISSILE_BIT0 = 0xB3     # red doors' bits ($7ED8B0): vanilla 0-$A9 (validate.check_gates), the Tallon's $B0-$B2
GATES = {
    # Main Plaza -> Ruined Shrine Access: "Actor Missile Lock" on the plaza's side (data)
    frozenset({"chozo_main_plaza", "chozo_ruined_shrine_access"}): Gate(frozenset({MISSILE_ITEM}), ("chozo_main_plaza",)),
    # Main Plaza <-> Piston Tunnel: "Door_Area Morphball" on both docks (data): the plaza's floor door sits under a Morph
    # Ball tunnel (tools/chozo/layouts.py main_plaza); the Piston Tunnel's side is open (Samus drops in from the plaza)
    frozenset({"chozo_main_plaza", "chozo_piston_tunnel"}): Gate(frozenset({MORPH_ITEM}), (), ("chozo_main_plaza",)),
    # Ruined Shrine -> Tower of Light Access, Tower of Light Access <-> Tower of Light <-> Tower Chamber: "Trigger_DoorKey"
    # (data), purple = Wave Beam (knowledge); the shrine's link only on the shrine's side (data)
    frozenset({"chozo_ruined_shrine", "chozo_tower_of_light_access"}): Gate(frozenset({WAVE}), ("chozo_ruined_shrine",)),
    frozenset({"chozo_tower_of_light_access", "chozo_tower_of_light"}): Gate(
        frozenset({WAVE}), ("chozo_tower_of_light_access", "chozo_tower_of_light")),
    frozenset({"chozo_tower_of_light", "chozo_tower_chamber"}): Gate(
        frozenset({WAVE}), ("chozo_tower_of_light", "chozo_tower_chamber")),
    # specs/12i, region B: Prime's two locks there are missile shields (data): the Ruined Gallery's door to the Map Station
    # (on the gallery's side) and the Hive Totem <-> Transport Access North (on both sides: one red door bit for the link,
    # opened from either side). No coloured door (no charge door), no hot room (the Gallery's "Check Varia Suit" swaps its
    # poison water for clean water: a hazard of the pool, dry here, not a lock).
    frozenset({"chozo_ruined_gallery", "chozo_map_station"}): Gate(frozenset({MISSILE_ITEM}), ("chozo_ruined_gallery",)),
    frozenset({"chozo_hive_totem", "chozo_transport_access_north"}): Gate(
        frozenset({MISSILE_ITEM}), ("chozo_hive_totem", "chozo_transport_access_north")),
    # specs/12j, region C. Prime's locks there (data, DOCK_LOCKS; the colour of each "key" door read from its
    # Trigger_DoorKey's damage vulnerability, scratchpad s12j/doorkeys.out: the region's are Wave-only, as the Tower of
    # Light's; no charge door, Prime has none):
    #  - missile shields: the Arboretum Access' door to the Arboretum (its side), the Arboretum's to the Sunchamber Lobby
    #    and to the Gathering Hall Access (its side), the Gathering Hall's to Save Station 2 (its side);
    #  - the Arboretum's door to the Sunchamber Lobby sits behind its breakable block too (FEATURES "breakable"; the rune
    #    gate opens by scanning: no SM item): a Morph Ball tunnel shut by a bomb block (layouts.arboretum);
    #  - Piston Tunnel <-> Training Chamber: "Door_Area Morphball" on both docks and the piston the bomb slots move: a Morph
    #    Ball tunnel shut by a bomb block on the chamber's side (layouts.training_chamber);
    #  - Training Chamber <-> Training Chamber Access <-> Magma Pool: "Trigger_DoorKey" on both sides of both links, Wave =
    #    purple doors (the Training Chamber's "Actor Door Lock" is the Chozo Ghosts' fight, an event layer: out);
    #  - the Sun Tower's Spider Ball track (FEATURES "spider"): its R2 door (to the Sun Tower Access) out of reach from the
    #    Magmoor door without the Space Jump (layouts.sun_tower; Prime's free way is down, from the Sunchamber);
    #  - the Sunchamber's "Actor Door Lock" on its door to the Sun Tower Access is Flaahgra's fight (the boss later, epic
    #    decision 3): no lock until then;
    #  - the Magma Pool is hot (HOT_ROOMS): every door into it gets the Varia Suit (heat_gates).
    frozenset({"chozo_arboretum_access", "chozo_arboretum"}): Gate(frozenset({MISSILE_ITEM}), ("chozo_arboretum_access",)),
    frozenset({"chozo_arboretum", "chozo_sunchamber_lobby"}): Gate(
        frozenset({MISSILE_ITEM, MORPH_ITEM, BOMBS_ITEM}), ("chozo_arboretum",), ("chozo_arboretum",)),
    frozenset({"chozo_arboretum", "chozo_gathering_hall_access"}): Gate(frozenset({MISSILE_ITEM}), ("chozo_arboretum",)),
    frozenset({"chozo_gathering_hall", "chozo_save_station_2"}): Gate(frozenset({MISSILE_ITEM}), ("chozo_gathering_hall",)),
    frozenset({"chozo_piston_tunnel", "chozo_training_chamber"}): Gate(
        frozenset({MORPH_ITEM, BOMBS_ITEM}), (), ("chozo_training_chamber",)),
    frozenset({"chozo_training_chamber", "chozo_training_chamber_access"}): Gate(
        frozenset({WAVE}), ("chozo_training_chamber", "chozo_training_chamber_access")),
    frozenset({"chozo_training_chamber_access", "chozo_magma_pool"}): Gate(
        frozenset({WAVE}), ("chozo_training_chamber_access", "chozo_magma_pool")),
    frozenset({"chozo_sun_tower", "chozo_sun_tower_access"}): Gate(frozenset({SPACE_JUMP}), (), ("chozo_sun_tower",)),
    # specs/12k, region D. Prime's locks there (data, DOCK_LOCKS; every door of the region is blue under its shield: the
    # damage vulnerability of each Trigger_DoorKey is 1 for every beam, scratchpad s12k/dtrig.out; no "key" door, so no
    # beam door and no charge door: Prime has no door only a charged shot opens; no "SpecialFunction Area Damage" in the
    # region, s12k/specialfn.out: no hot room):
    #  - missile shields: the Watery Hall Access' door to the Watery Hall (its side), the Watery Hall's to the Dynamo Access
    #    (its side), the Dynamo Access' to the Dynamo (its side);
    #  - the Watery Hall's door to the Dynamo Access sits behind the room's "Breakable Block" too (a DamageableTrigger only
    #    bombs and power bombs hurt, s12k/dtrig.out) and the path camera of a Morph Ball tunnel next to it: a Morph Ball
    #    tunnel shut by a bomb block in front of the door (layouts.watery_hall);
    #  - Energy Core <-> Burn Dome Access: Prime's Morph Ball door ("Door_Area Morphball", one door object on both docks):
    #    a Morph Ball tunnel on the Burn Dome Access' side, over its floor door (layouts.burn_dome_access; the Energy Core's
    #    side is open, as the Main Plaza's Piston Tunnel door, 12f);
    #  - the Energy Core's "Actor Door Lock" on its door to the West Furnace Access is the bomb-slot puzzle (three bomb slots
    #    switch the cores on: "Part 1/2 Solved", no fight): a Morph Ball tunnel shut by a bomb block in front of the door
    #    (layouts.energy_core; EVENT_LOCKS below makes the validator check it);
    #  - the Burn Dome's "Actor Door Lock" (its door to the Burn Dome Access) is the Incinerator Drone's fight: specs/14d, a
    #    boss door (BOSS_DOORS below).
    frozenset({"chozo_watery_hall_access", "chozo_watery_hall"}): Gate(frozenset({MISSILE_ITEM}), ("chozo_watery_hall_access",)),
    frozenset({"chozo_watery_hall", "chozo_dynamo_access"}): Gate(
        frozenset({MISSILE_ITEM, MORPH_ITEM, BOMBS_ITEM}), ("chozo_watery_hall",), ("chozo_watery_hall",)),
    frozenset({"chozo_dynamo_access", "chozo_dynamo"}): Gate(frozenset({MISSILE_ITEM}), ("chozo_dynamo_access",)),
    frozenset({"chozo_energy_core", "chozo_burn_dome_access"}): Gate(frozenset({MORPH_ITEM}), (), ("chozo_burn_dome_access",)),
    frozenset({"chozo_energy_core", "chozo_west_furnace_access"}): Gate(
        frozenset({MORPH_ITEM, BOMBS_ITEM}), (), ("chozo_energy_core",)),
    # specs/12l, region E. Prime's locks there (data, DOCK_LOCKS; the colour of each "key" door read from its
    # Trigger_DoorKey's damage vulnerability, scratchpad s12l/dtrig.out: power/ice/wave/plasma 2 1 2 2 = Ice only, 2 2 1 2 =
    # Wave only; the missile shields' doors are blue under the shield; no "SpecialFunction Area Damage": no hot room):
    #  - Ice on both sides: Furnace <-> East Furnace Access (a floor/ceiling door here: beamdoors' vertical ice doors), East
    #    Furnace Access <-> Hall of the Elders, Hall <-> Elder Chamber, Hall <-> Crossway Access South (ceiling/floor),
    #    Crossway Access South <-> Crossway, Reflecting Pool <-> Transport Access South; on the Antechamber's side of its door
    #    to the Reflecting Pool (SIDE_CAPS: the Reflecting Pool's side is a missile shield);
    #  - Wave: the Crossway Access West's door to the Crossway (its side);
    #  - missile shields: the Crossway's floor door to the Elder Hall Access, the Reflecting Pool's floor door to Save
    #    Station 3 and its door to the Antechamber (their side);
    #  - Furnace <-> Crossway Access West: Prime's Morph Ball door (one door object on both docks) = a Morph Ball tunnel on
    #    the Furnace's side, in its east balcony, which only the Space Jump reaches (Prime's half-pipe and Spider Ball
    #    track in the Furnace) (layouts.furnace);
    #  - the Hall of the Elders' "Actor Door Lock"s (all four of its doors) are the Chozo Ghosts' fights (layers 1/2): out
    #    until the bosses, as the Training Chamber's; its statue ("Chozo bowling": the purple bomb slot throws the ball to
    #    the Reflecting Pool Access door, s12l/conns52.txt) = a Morph Ball tunnel shut by a bomb block into the chamber over
    #    the B2 floor door (layouts.hall_of_the_elders; the coloured membranes and the throw are left out);
    #  - the Reflecting Pool is flooded (FLOODED: Prime's pool) and its doors to Save Station 3, the Antechamber and the
    #    Transport Access South sit behind 4-block climbs under water: the Gravity Suit (layouts.reflecting_pool). This
    #    keeps the two elevators' Chozo sides in the Tallon's rounds (East 4, South 5): Prime's way in, the Crossway and the
    #    statue, gets to the pool in round 3 (specs/12l, "O conflito").
    frozenset({"chozo_furnace", "chozo_east_furnace_access"}): Gate(
        frozenset({ICE}), ("chozo_furnace", "chozo_east_furnace_access")),
    frozenset({"chozo_furnace", "chozo_crossway_access_west"}): Gate(
        frozenset({MORPH_ITEM, SPACE_JUMP}), (), ("chozo_furnace",)),
    frozenset({"chozo_east_furnace_access", "chozo_hall_of_the_elders"}): Gate(
        frozenset({ICE}), ("chozo_east_furnace_access", "chozo_hall_of_the_elders")),
    frozenset({"chozo_crossway_access_west", "chozo_crossway"}): Gate(frozenset({WAVE}), ("chozo_crossway_access_west",)),
    frozenset({"chozo_hall_of_the_elders", "chozo_reflecting_pool_access"}): Gate(
        frozenset({MORPH_ITEM, BOMBS_ITEM}), (), ("chozo_hall_of_the_elders",)),
    frozenset({"chozo_hall_of_the_elders", "chozo_crossway_access_south"}): Gate(
        frozenset({ICE}), ("chozo_hall_of_the_elders", "chozo_crossway_access_south")),
    frozenset({"chozo_hall_of_the_elders", "chozo_elder_chamber"}): Gate(
        frozenset({ICE}), ("chozo_hall_of_the_elders", "chozo_elder_chamber")),
    frozenset({"chozo_crossway", "chozo_elder_hall_access"}): Gate(frozenset({MISSILE_ITEM}), ("chozo_crossway",)),
    frozenset({"chozo_crossway", "chozo_crossway_access_south"}): Gate(
        frozenset({ICE}), ("chozo_crossway", "chozo_crossway_access_south")),
    frozenset({"chozo_reflecting_pool", "chozo_save_station_3"}): Gate(
        frozenset({MISSILE_ITEM, GRAVITY}), ("chozo_reflecting_pool",), ("chozo_reflecting_pool",)),
    frozenset({"chozo_reflecting_pool", "chozo_transport_access_south"}): Gate(
        frozenset({ICE, GRAVITY}), ("chozo_reflecting_pool", "chozo_transport_access_south"), ("chozo_reflecting_pool",)),
    frozenset({"chozo_reflecting_pool", "chozo_antechamber"}): Gate(
        frozenset({MISSILE_ITEM, ICE, GRAVITY}), ("chozo_reflecting_pool", "chozo_antechamber"), ("chozo_reflecting_pool",)),
}
# specs/12l: the beam of each Prime "key" door (DOCK_LOCKS "key"), read from its Trigger_DoorKey's damage vulnerability
# (power/ice/wave/plasma: 2 2 1 2 = Wave only, 2 1 2 2 = Ice only; scratchpad s12j/doorkeys.out for the whole Chozo,
# s12l/dtrig.out for region E): validate.check_chozo_locks_mapped checks each built key dock's cap is this beam's.
KEY_BEAM = {
    ("chozo_ruined_shrine", "chozo_tower_of_light_access"): WAVE,
    ("chozo_tower_of_light_access", "chozo_tower_of_light"): WAVE, ("chozo_tower_of_light", "chozo_tower_of_light_access"): WAVE,
    ("chozo_tower_of_light", "chozo_tower_chamber"): WAVE, ("chozo_tower_chamber", "chozo_tower_of_light"): WAVE,
    ("chozo_training_chamber", "chozo_training_chamber_access"): WAVE,
    ("chozo_training_chamber_access", "chozo_training_chamber"): WAVE,
    ("chozo_training_chamber_access", "chozo_magma_pool"): WAVE, ("chozo_magma_pool", "chozo_training_chamber_access"): WAVE,
    ("chozo_furnace", "chozo_east_furnace_access"): ICE, ("chozo_east_furnace_access", "chozo_furnace"): ICE,
    ("chozo_east_furnace_access", "chozo_hall_of_the_elders"): ICE, ("chozo_hall_of_the_elders", "chozo_east_furnace_access"): ICE,
    ("chozo_crossway_access_west", "chozo_crossway"): WAVE,
    ("chozo_hall_of_the_elders", "chozo_crossway_access_south"): ICE, ("chozo_crossway_access_south", "chozo_hall_of_the_elders"): ICE,
    ("chozo_hall_of_the_elders", "chozo_elder_chamber"): ICE, ("chozo_elder_chamber", "chozo_hall_of_the_elders"): ICE,
    ("chozo_crossway", "chozo_crossway_access_south"): ICE, ("chozo_crossway_access_south", "chozo_crossway"): ICE,
    ("chozo_reflecting_pool", "chozo_transport_access_south"): ICE, ("chozo_transport_access_south", "chozo_reflecting_pool"): ICE,
    ("chozo_antechamber", "chozo_reflecting_pool"): ICE,
}
# specs/12l: a link whose two sides have different caps (Prime: the Reflecting Pool's side of the Antechamber door is a
# missile shield, the Antechamber's side is Ice-only): (room, the room its door leads to) -> the gate item of that side's cap.
# That side's door gets that cap, and its gate drops the other side's cap item (going through a door asks for the items of
# its own side: the Antechamber is left with the Ice Beam, as in Prime, where it is found there).
SIDE_CAPS = {("chozo_reflecting_pool", "chozo_antechamber"): MISSILE_ITEM,
             ("chozo_antechamber", "chozo_reflecting_pool"): ICE}
# specs/12k: Prime's "Actor Door Lock"s (DOCK_LOCKS "event") that are a puzzle, not a fight, mapped now: (room, the room its
# door leads to) -> the items its SM mechanism needs (in the link's gate; validate.check_chozo_locks_mapped). The other
# event locks (the Chozo Ghosts', Flaahgra's, the Incinerator Drone's fights) wait for the bosses (epic decision 3).
EVENT_LOCKS = {("chozo_energy_core", "chozo_west_furnace_access"): frozenset({MORPH_ITEM, BOMBS_ITEM})}
# One-way doors (Prime: the "one way door" scan at the Main Plaza's dock to the Plaza Access: from the plaza the door never
# opens, from the Plaza Access side it does): (room, the room its door leads to). The room's side gets a grey cap that never
# opens (build.GREY_DOOR_NEVER) and the gate ONE_WAY_GATE, an item nothing gives, so the progression walk never goes through
# it that way; the other side has no gate. The plaza's ceiling door also sits over a Space Jump ledge (the E-tank's, Prime's
# "Locked Door" ledge): the ledge is the geometry of the gate.
ONE_WAY_GATE = "one_way"
ONE_WAY_DOORS = {("chozo_main_plaza", "chozo_plaza_access"): frozenset({SPACE_JUMP})}
# specs/14c: Prime's "Actor Door Lock"s of a boss fight, mapped now: (room, the room its door leads to). That side's door gets a
# grey cap that opens when the boss dies (build: the grey door of type 1, the SM's mini-boss bit $02, which the room's boss
# sets: tools/chozo/bosses.py ARENAS) and the gate BOSS_GATE: the progression walk (validate.exit_open) goes through it only
# with the room's arena's `needs` (the fight won); the other side stays blue (Prime locks only the arena's side). The
# Sunchamber's door to the Sun Tower Access: Flaahgra's (the Spore Spawn's) fight.
BOSS_GATE = "boss"
# specs/14d: the Burn Dome's door to the Burn Dome Access (the Incinerator Drone's fight, an ITEM arena): blue until Samus
# takes the stand's missile, then the arena routine spawns its grey cap of type 3 (the kill count: build.item_arena_door).
BOSS_DOORS = frozenset({("chozo_sunchamber", "chozo_sun_tower_access"), ("chozo_burn_dome", "chozo_burn_dome_access")})

# specs/12g (epic 12, decision 2): hot rooms (SM's heat, chozo/heat.py; RoomDef.heat). The user's model: a hot room is
# impassable without the Varia Suit (no damage tanked): every door into one gets VARIA in its gate (build_rooms). Which
# rooms are hot is the region children's (Prime's `heat` FEATURES are the candidates: Arboretum, Magma Pool, Ruined
# Gallery, Sunchamber, Ruined Shrine); none of region A is (12f built the Ruined Shrine cool), so none yet. The test build
# (build.py --teste-12g, chozo/testrooms.py) makes one.
# specs/12j: the Magma Pool, the only room of Prime's Chozo with a "SpecialFunction Area Damage" (function 18: Prime's heat,
# the one every superheated room of the Magmoor Caverns has; scratchpad s12j/specialfn.out reads them all). The other
# region-C `heat` features are "Check Varia Suit" item checks (function 5) that swap a pool's water, and the Meditation
# Fountain's and the Training Chamber Access' "Thermal Heat Fader"s are the Thermal Visor's glow by the Magma Pool's doors.
HOT_ROOMS: frozenset[str] = frozenset({"chozo_magma_pool"})
# specs/12l: flooded rooms (water FX over the whole room, the sunken frigate's mechanism, specs/07l; RoomDef.water): the
# Reflecting Pool, Prime's pool (FEATURES "water"), the one whose water gates the way (the Gravity Suit, GATES above). The other
# Prime pools stay dry (epic question 7).
FLOODED: frozenset[str] = frozenset({"chozo_reflecting_pool"})

# The round (validate.world_rounds: the Tallon and the Chozo walked together, from the Landing Site gunship; round 0 = the
# Power Beam only, round k = with the items of rounds 0..k-1, as tallon/rooms.py FIRST_ROUND) at which each built Chozo room
# is first reached. The North elevator is in the Tallon's round 0. 1: missiles (the Landing Site's) and the Morph Ball (the
# Chozo West's); 2: the Wave Beam (the Magmoor East's) and the Bombs; 4 and 5: the East and South elevator rooms (dead ends
# until region E), as their Tallon sides. A room that waits for a region not built yet is in WAITS_FOR (its region's
# letter), out of the rounds.
# specs/12i: region B, from the Nursery Access (round 0) round its loop: 0 up to the Hive Totem; 1 behind the missile
# shields (the Map Station; the Transport Access North and on, through the Magmoor transport and the Vault, to the Plaza
# Access, whose floor door drops onto the Main Plaza's one-way ledge).
# specs/12j: region C. 0: on foot from the Ruined Fountain Access (the Ruined Fountain, the Arboretum Access, down to the
# Meditation Fountain); 1: behind the red doors (the Arboretum, the Gathering Hall Access, the Gathering Hall, Save Station 2)
# and the doorways of the rooms behind geometry (the Sun Tower's Magmoor door, its pocket under the shaft; the Training
# Chamber's piston chamber, off the Piston Tunnel); 2: the Bombs (the Arboretum's tunnel to the Sunchamber Lobby, the
# Sunchamber Access, the Sunchamber and out to the Sun Tower Access; through the piston's tunnel into the Training Chamber's
# hall) and the Wave Beam (the Training Chamber Access); 3: the Varia Suit (the Sunchamber's, round 2): the Magma Pool.
# specs/12k: region D. 1: past the Gathering Hall (round 1): the Watery Hall Access and, through its red door, the Watery
# Hall; the East Atrium, the Energy Core Access and the Energy Core; up its ceiling door to the Burn Dome Access and, with
# the Morph Ball (round 0's), the Burn Dome; 2: the Bombs: the Watery Hall's tunnel to the Dynamo Access and the Dynamo, the
# Energy Core's bomb-slot tunnel to the West Furnace Access and the Furnace.
# specs/12l: region E. 3: the Space Jump (round 2's): onto the Furnace's east balcony and through its Morph Ball tunnel to
# the Crossway Access West, the Crossway (its wave door), down its red floor door to the Elder Hall Access and into the Hall
# of the Elders; through the statue's bomb tunnel down the Reflecting Pool Access into the Reflecting Pool (its top only:
# the rest is under water past 4-block climbs); 4: the Ice Beam (round 3's): the ice doors (the East Furnace Access, the
# Crossway Access South, the Elder Chamber) and, down the Tallon's East elevator, Save Station 3 and up into the Reflecting
# Pool's west part, the Antechamber; 5: the Gravity Suit (round 4's): the Reflecting Pool's ice door to the Transport Access
# South (and the Tallon's South elevator).
_ROUNDS = [
    ["chozo_transport_tallon_north", "chozo_ruins_entrance", "chozo_main_plaza", "chozo_ruined_fountain_access",
     "chozo_nursery_access",
     "chozo_eyon_tunnel", "chozo_ruined_nursery", "chozo_save_station_1", "chozo_north_atrium", "chozo_ruined_gallery",
     "chozo_totem_access", "chozo_hive_totem",
     "chozo_ruined_fountain", "chozo_arboretum_access", "chozo_meditation_fountain"],
    ["chozo_ruined_shrine_access", "chozo_ruined_shrine", "chozo_piston_tunnel",
     "chozo_map_station", "chozo_transport_access_north", "chozo_transport_magmoor_north", "chozo_vault_access",
     "chozo_vault", "chozo_plaza_access",
     "chozo_arboretum", "chozo_gathering_hall_access", "chozo_gathering_hall", "chozo_save_station_2", "chozo_sun_tower",
     "chozo_training_chamber",
     "chozo_watery_hall_access", "chozo_watery_hall", "chozo_east_atrium", "chozo_energy_core_access", "chozo_energy_core",
     "chozo_burn_dome_access", "chozo_burn_dome"],
    ["chozo_tower_of_light_access", "chozo_tower_of_light", "chozo_tower_chamber",
     "chozo_sunchamber_lobby", "chozo_sunchamber_access", "chozo_sunchamber", "chozo_sun_tower_access",
     "chozo_training_chamber_access",
     "chozo_dynamo_access", "chozo_dynamo", "chozo_west_furnace_access", "chozo_furnace"],
    ["chozo_magma_pool",
     "chozo_crossway_access_west", "chozo_crossway", "chozo_elder_hall_access", "chozo_hall_of_the_elders",
     "chozo_reflecting_pool_access", "chozo_reflecting_pool"],
    ["chozo_transport_tallon_east",     # specs/12e: down the Tallon's Chozo East elevator (behind its ice door)
     "chozo_east_furnace_access", "chozo_crossway_access_south", "chozo_elder_chamber", "chozo_save_station_3",
     "chozo_antechamber"],
    ["chozo_transport_tallon_south",    # down the Chozo South's (region E of the Tallon)
     "chozo_transport_access_south"],
]
FIRST_ROUND = {k: n for n, keys in enumerate(_ROUNDS) for k in keys}
# Plaza Access: in Prime reached from the Vault (region B) only, the Main Plaza's door being one-way (12f: it waited for
# region B; specs/12i built it: none waits now)
WAITS_FOR: dict[str, str] = {}


def build_rooms(regions, extra=frozenset()) -> list[RoomDef]:
    """RoomDefs of the rooms in `regions` and in `extra`, in TABLE order, with the doors between them; a link to a room left
    out is left out too (wall). A room with a layout (tools/chozo/layouts.py, specs/12e) gets it, in the ruins style
    (tileset $0C, specs/12d); the others are placeholder boxes."""
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
        rooms[t.key] = RoomDef(t.key, t.prime, t.name, w, h, t.map_x, t.map_y, canvas, style=ruins.RUINS,
                               tileset=ruins.RUINS_TILESET, skin=shape.skin if shape else [],
                               backdrop=shape.backdrop if shape else [], blocks=shape.blocks if shape else [],
                               elevator=shape.elevator if shape else None, heat=t.key in HOT_ROOMS,
                               water=t.key in FLOODED,
                               save_station=shape.save if shape else None,
                               map_station=shape.map_station if shape else None)
    bits = {k: CHOZO_MISSILE_BIT0 + n for n, k in enumerate(k for k, g in GATES.items() if MISSILE_ITEM in g.items)}
    for (ra, sa, na), (rb, sb, nb) in LINKS:
        if OPPOSITE[sa] != sb:
            raise ValueError(f"porta {ra}.{sa} liga em {rb}.{sb}: lados precisam ser opostos")
        if ra not in rooms or rb not in rooms:
            continue
        da, db = DoorLink(sa, na, rb), DoorLink(sb, nb, ra)
        gate = GATES.get(frozenset({ra, rb}))
        if gate:   # the Tallon's rule (tallon/rooms.py build_rooms): one kind of cap and its side(s), or a ledge only
            caps = {LOCK_OF[i] for i in gate.items if i in LOCK_OF}
            if (bool(caps) != bool(gate.capped) or not set(gate.capped) <= {ra, rb}
                    or not set(gate.ledge) <= {ra, rb} or bool(gate.ledge) != bool(gate.items & GEOMETRY)):
                raise ValueError(f"trava {ra}-{rb}: precisa de um tipo de tampa e do lado dela ({gate})")
            split = {key: SIDE_CAPS[(key, to)] for key, to in ((ra, rb), (rb, ra)) if (key, to) in SIDE_CAPS}
            if split:   # specs/12l: one cap kind per side
                if set(split) != set(gate.capped) or set(split.values()) != {i for i in gate.items if i in LOCK_OF}:
                    raise ValueError(f"trava {ra}-{rb}: SIDE_CAPS {split} não bate com a trava ({gate})")
            elif len(caps) > 1:
                raise ValueError(f"trava {ra}-{rb}: precisa de um tipo de tampa e do lado dela ({gate})")
            cap = caps.pop() if caps and not split else None
            for d, key in ((da, ra), (db, rb)):
                d.gate, d.ledge = gate.items, key in gate.ledge
                if key in split:
                    d.gate = gate.items - (set(split.values()) - {split[key]})
                if key in gate.capped:
                    d.lock, d.lock_bit = LOCK_OF[split[key]] if key in split else cap, bits.get(frozenset({ra, rb}))
        for d, key, to in ((da, ra, rb), (db, rb, ra)):
            if (key, to) in ONE_WAY_DOORS:
                if gate:
                    raise ValueError(f"porta de mão única {key}->{to} com trava {gate}")
                d.gate, d.ledge, d.lock = ONE_WAY_DOORS[(key, to)] | {ONE_WAY_GATE}, True, "grey"
            if (key, to) in BOSS_DOORS:   # specs/14c
                if gate:
                    raise ValueError(f"porta de chefe {key}->{to} com trava {gate}")
                d.gate, d.lock = frozenset({BOSS_GATE}), "boss"
        rooms[ra].doors.append(da)
        rooms[rb].doors.append(db)
        da.to_door = len(rooms[rb].doors) - 1
        db.to_door = len(rooms[ra].doors) - 1
    heat_gates(rooms)
    return list(rooms.values())


def heat_gates(rooms: dict) -> None:
    """specs/12g: every door into a hot room needs the Varia Suit (VARIA in its gate; the rounds walk goes through a door
    only with every item of its gate but the GEOMETRY ones)."""
    for r in rooms.values():
        for d in r.doors:
            if d.to_room in rooms and rooms[d.to_room].heat:
                d.gate = d.gate | {VARIA}


def region_of(key: str) -> str:
    return next(t.region for t in TABLE if t.key == key)


def check_prime(worlds_json: Path, locks_json: Path) -> list[str]:
    """TABLE and LINKS against Prime's data (every room once with its name and box, the links = Prime's door pairs),
    and DOCK_LOCKS / FEATURES = what research/prime_chozo_locks.json gives."""
    world = next(w for w in json.loads(worlds_json.read_text()) if w["name"] == "Chozo Ruins")
    prime = {a["index"]: a for a in world["areas"]}
    problems = []
    by_prime = {t.prime: t for t in TABLE}
    if len(by_prime) != len(TABLE) or set(by_prime) != set(prime):
        problems.append(f"chozo: tabela tem as salas {sorted(by_prime)}, o Prime tem {sorted(prime)}")
    if len({t.key for t in TABLE}) != len(TABLE):
        problems.append("chozo: chave de sala repetida na tabela")
    for t in TABLE:
        if t.region not in REGIONS:
            problems.append(f"{t.key}: região {t.region!r} desconhecida")
        if not t.key.startswith("chozo_"):
            problems.append(f"{t.key}: chave sem o prefixo chozo_")
        a = prime.get(t.prime)
        if a is None:
            continue
        b = a["aabb"]
        box = tuple(round(b[i + 3] - b[i]) for i in range(3))
        if (a["name"], box) != (t.name, t.box):
            problems.append(f"{t.key}: P{t.prime} no Prime é {a['name']!r} {box}, a tabela diz {t.name!r} {t.box}")
    key_of = {t.prime: t.key for t in TABLE}
    key_prime = {t.key: t.prime for t in TABLE}
    unknown = sorted({k for a, b in LINKS for k in (a[0], b[0])} - set(key_prime))
    if unknown:
        return problems + [f"chozo: ligações com salas fora da tabela: {unknown}"]
    ours = [frozenset((key_prime[a[0]], key_prime[b[0]])) for a, b in LINKS]
    theirs = {frozenset((a["index"], d["to_area"])) for a in world["areas"] for d in a["docks"]}
    if len(set(ours)) != len(ours) or set(ours) != theirs:
        problems.append(f"chozo: ligações diferentes do Prime: sobram {sorted(map(sorted, set(ours) - theirs))}, "
                        f"faltam {sorted(map(sorted, theirs - set(ours)))}")
    data = json.loads(locks_json.read_text())
    want_locks, want_features = {}, {}
    for i, room in data.items():
        if int(i) not in key_of:
            continue
        for d in room["docks"]:
            kinds = prime_dock_locks(d["objects"])
            if kinds:
                want_locks[(key_of[int(i)], key_of[d["to"]])] = kinds
        if room["features"]:
            want_features[key_of[int(i)]] = set(room["features"])
    for k in sorted(set(want_locks) | set(DOCK_LOCKS)):
        if want_locks.get(k) != DOCK_LOCKS.get(k):
            problems.append(f"chozo: trava da doca {k[0]} -> {k[1]}: o Prime tem {sorted(want_locks.get(k, ()))}, "
                            f"a tabela diz {sorted(DOCK_LOCKS.get(k, ()))}")
    for k in sorted(set(want_features) | set(FEATURES)):
        if want_features.get(k) != FEATURES.get(k):
            problems.append(f"chozo: {k}: o Prime tem {sorted(want_features.get(k, ()))}, "
                            f"FEATURES diz {sorted(FEATURES.get(k, ()))}")
    return problems


ALL_ROOMS = build_rooms(REGIONS)                 # the whole world, for the validator's map checks
ROOMS = build_rooms(ACTIVE_REGIONS, ELEVATOR_ROOMS)   # what the build gets (specs/12e: the elevator rooms)

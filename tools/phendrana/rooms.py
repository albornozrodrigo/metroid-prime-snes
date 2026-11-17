"""Phendrana Drifts rooms (SM area 4, specs/18b): the room graph, the map and Prime's locks (specs/18c-grafo-e-mapa-phendrana.md).

All 56 rooms of Prime's Phendrana Drifts (research/prime_worlds.json, MLVL "Phendrana Drifts"), one SM room per Prime room (epic
18, user decision 1 and technical decision 1), with the Prime door graph in LINKS (59 pairs, 118 docks, all with their way back;
four loops: Shorelines / Plaza Walkway / Ice Ruins East / Ice Ruins Access; the big ring Ruined Courtyard -> the labs -> the
towers -> Research Core -> Frozen Pike -> Transport Access -> the south elevator -> Quarantine Cave -> Ruined Courtyard; and
in the south Frozen Pike / Frost Cave / Phendrana's Edge / Hunter Cave and Hunter Cave / Gravity Chamber). The size comes from
the Prime box by the Tallon's rule (tallon/rooms.py `screens`: 30 m a screen, at most 6 x 4): 302 screens.

Map: x/y in area 4's 64x32 pause-map grid. Phendrana is long north to south in Prime (1.5 km by 0.7 km) and its rooms spread
west/east more than up/down, so here the map is Prime seen from above: west to east on the map = north to south in Prime (the
north elevator, P0, at the left; Phendrana's Edge at the right), top to bottom = Prime's west to east (the labs and the towers
above, the quarantine and the south elevator below), loosely. The sides and screens of the doors were found by a search (a
discarded script, as in specs/12c and 17c: a randomized placement where each room touches every placed neighbour, pulled toward
its Prime position, the best of many by a cost) that keeps every door touching its neighbour, few floor/ceiling doors, none on
an elevator room (its shaft is the ceiling), an elevator room's side door on its bottom screen where it can, and the saved map
small. The validator checks the whole table (tools/validate.py check_phendrana) and each region alone.

Regions (epic 18, "Regiões"): A the north (Shorelines, the Ice Temple, the Chapel of the Elders); B the Ice Ruins West, the
Ruined Courtyard and the first lab (Hydra); C the quarantine and the south elevator; D the Observatory, the towers and the labs
(Aether, Research Core); E the deep south (Frozen Pike, the caves, Phendrana's Edge, the Gravity Chamber).

Built (specs/18e): the two elevator rooms (ELEVATOR_ROOMS, drawn in tools/phendrana/layouts.py), dead ends until their regions.
specs/18f: region A (ACTIVE_REGIONS): the P0's door opens into the Shoreline Entrance; the Ruins Entryway's door to the Ice Ruins
West (region B) stays a wall until 18i. Prime's locks there are mapped in GATES (the Chapel of the Elders' wave door, the Ice
Temple's bomb slot); the Sheegoth's door lock (an event lock) waits for its fight (BOSS_DOORS, specs/18h). Prime's locks are recorded as data (DOCK_LOCKS, KEY_BEAM,
FEATURES, SNOW_ROOMS, WATER_ROOMS, PLASMA_ICE, WAVE_PANELS), read from Prime's objects (research/prime_phendrana_locks.json,
written by tools/dump_prime_locks.py); no SM item or mechanism is chosen here (the region children, by the epic's technical
decision 3). No room is hot nor cold (no "Area Damage" in Phendrana: the epic's user decision 5); check_prime checks it.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from chozo.rooms import EVENT, KEY, MISSILE, MORPH, ONE_WAY, prime_dock_locks   # noqa: F401 (the lock kinds, as the Chozo's)
from frigate.rooms import OPPOSITE, DoorLink, RoomDef
from magmoor.rooms import BEAM_OF_VULN, TRANSPORT_TO as MAGMOOR_TRANSPORT_TO
from smlib import ice
from smlib.style import Style
from tallon.rooms import (BOMBS, GEOMETRY, ICE, LOCK_OF, MISSILE as MISSILE_ITEM, MORPH as MORPH_ITEM, PLASMA, POWER_BOMB,  # noqa: F401
                          SPACE_JUMP, WAVE, Gate, placeholder, screens)

from .layouts import LAYOUTS

REGIONS = {
    "A": "Norte: Phendrana Shorelines, Chozo Ice Temple, Chapel of the Elders",
    "B": "Ice Ruins West, Ruined Courtyard e o primeiro laboratório (Hydra)",
    "C": "Quarentena e o elevador sul",
    "D": "Observatório, torres e laboratórios (Aether, Research Core)",
    "E": "Sul fundo: Frozen Pike, cavernas, Phendrana's Edge, Gravity Chamber",
}
ACTIVE_REGIONS: frozenset[str] = frozenset({"A", "B", "C", "D", "E"})   # specs/18c: none built; specs/18f: A; specs/18i: B; 18j: C;
# 18l: D; 18m: E (all 56 rooms of the table)
# specs/18e: each built room's look (smlib/ice.py tileset; the snow look unless here) and the round it is first reached in
# (the walk of the four areas: Phendrana is entered only by the Magmoor's lifts, whose rooms are round 3's)
# specs/18f: the snow look (the exterior, the sky) for the open shore and its paths (the P0, the Shoreline Entrance, the
# Shorelines, the Ruins Entryway); the icy ruins (the Chozo's sandstone in ice, specs/18d) for the Chozo-built rooms: the temple,
# its entryway and chapel, the Ice Ruins East and their walkways, the save room. Whether it snows is Prime's (SNOW_ROOMS).
LOOK = {"phendrana_transport_magmoor_south": ice.RUINS_TILESET,   # the P0: snow (Prime snows there); the P29: Chozo-built, dry
        "phendrana_temple_entryway": ice.RUINS_TILESET, "phendrana_save_station_b": ice.RUINS_TILESET,
        "phendrana_plaza_walkway": ice.RUINS_TILESET, "phendrana_ice_ruins_access": ice.RUINS_TILESET,
        "phendrana_chozo_ice_temple": ice.RUINS_TILESET, "phendrana_ice_ruins_east": ice.RUINS_TILESET,
        "phendrana_chapel_tunnel": ice.RUINS_TILESET, "phendrana_chapel_of_the_elders": ice.RUINS_TILESET,
        # specs/18i: region B. The icy ruins for the Chozo-built rooms (the Ice Ruins West, the Ruined Courtyard, their
        # entryways, the Quarantine Access, Save Station A); the labs' look for the pirates' rooms (the Specimen Storage, the
        # Research Entrance, the Map Station, the Hydra Lab Entryway, the Research Lab Hydra); the snow look (the default) for the
        # Phendrana Canyon, the open canyon under the sky
        "phendrana_ice_ruins_west": ice.RUINS_TILESET, "phendrana_courtyard_entryway": ice.RUINS_TILESET,
        "phendrana_canyon_entryway": ice.RUINS_TILESET, "phendrana_ruined_courtyard": ice.RUINS_TILESET,
        "phendrana_save_station_a": ice.RUINS_TILESET, "phendrana_quarantine_access": ice.RUINS_TILESET,
        "phendrana_specimen_storage": ice.LAB_TILESET, "phendrana_research_entrance": ice.LAB_TILESET,
        "phendrana_map_station": ice.LAB_TILESET, "phendrana_hydra_lab_entryway": ice.LAB_TILESET,
        "phendrana_research_lab_hydra": ice.LAB_TILESET}
# specs/18j: region C keeps the snow look (the default) in its five new rooms, all under Prime's sky and snow (the tunnels, the
# Thardus' cave, the Quarantine Monitor's lookout, the Transport Access); the P29 stays in the icy ruins (above)
# specs/18l: region D, the pirates' observatory, towers and labs: the labs' look for all but the Control Tower (its courtyard under
# the sky, snow falling as in Prime) and the Pike Access (an ice tunnel; no snow falls there in Prime): the snow look (the default)
# specs/18m: region E, Prime's natural ice caves and the snowy cliffs at the world's edge: the snow look (the default) in all 14,
# the snow falling only where Prime snows (the Frozen Pike, the Frost Cave Access, Save Station C, Phendrana's Edge, the Storage and
# Security Caves)
LOOK.update({k: ice.LAB_TILESET for k in ("phendrana_observatory_access", "phendrana_observatory", "phendrana_west_tower_entrance",
                                          "phendrana_save_station_d", "phendrana_west_tower", "phendrana_east_tower",
                                          "phendrana_aether_lab_entryway", "phendrana_research_lab_aether",
                                          "phendrana_research_core_access", "phendrana_research_core")})
STYLE_OF = {ice.SNOW_TILESET: ice.SNOW, ice.RUINS_TILESET: ice.ICE_RUINS, ice.LAB_TILESET: Style()}
# specs/18f: region A from the P0 (round 3, the Magmoor's P13 under it): every room in round 3 (its only locks, the chapel's wave
# door and the temple's bomb slot, want the Wave Beam and the Bombs, rounds 0 and 1; its two Space Jump ledges hold items only)
FIRST_ROUND = {"phendrana_transport_magmoor_west": 3, "phendrana_transport_magmoor_south": 3,
               **{k: 3 for k in ("phendrana_shoreline_entrance", "phendrana_shorelines", "phendrana_temple_entryway",
                                 "phendrana_save_station_b", "phendrana_ruins_entryway", "phendrana_plaza_walkway",
                                 "phendrana_ice_ruins_access", "phendrana_chozo_ice_temple", "phendrana_ice_ruins_east",
                                 "phendrana_chapel_tunnel", "phendrana_chapel_of_the_elders")},
               # specs/18i: region B, from the Ruins Entryway (round 3): its locks want the missiles (the red doors: the Landing
               # Site's, round 0), the Wave Beam (round 1), the Morph Ball and the Bombs (the Courtyard's Energy Tank, rounds
               # 0-1) and, for the Ice Ruins West's niche only, the Plasma Beam (round 5: its item in round 6): every room in round 3
               **{k: 3 for k in ("phendrana_ice_ruins_west", "phendrana_courtyard_entryway", "phendrana_canyon_entryway",
                                 "phendrana_ruined_courtyard", "phendrana_canyon", "phendrana_save_station_a",
                                 "phendrana_specimen_storage", "phendrana_quarantine_access", "phendrana_research_entrance",
                                 "phendrana_map_station", "phendrana_hydra_lab_entryway", "phendrana_research_lab_hydra")},
               # specs/18j: region C, from the Quarantine Access (round 3) and the P29 (the Magmoor's P27 lift, round 3): its
               # wave doors (round 1) and the Quarantine Monitor's Morph Ball tunnel (round 0) keep it in round 3; the Transport
               # Access behind the ice doors of the P29 (the Ice Beam: picked up in round 3, the Tallon's Root Cave) in round 4;
               # its Energy Tank behind the plasma cap (round 6, as the Ice Ruins West's power bomb)
               **{k: 3 for k in ("phendrana_north_quarantine_tunnel", "phendrana_quarantine_cave",
                                 "phendrana_south_quarantine_tunnel", "phendrana_quarantine_monitor")},
               "phendrana_transport_access": 4,
               # specs/18l: region D, from the Research Lab Hydra (round 3): its wave doors (round 1), red doors (round 0) and the
               # Observatory's bomb block (the Super Missile's chamber: rounds 0-1) keep it in round 3; the Pike Access behind the
               # Research Core's ice doors (the Ice Beam, picked up in round 3) in round 4, as the Transport Access
               **{k: 3 for k in ("phendrana_observatory_access", "phendrana_observatory", "phendrana_west_tower_entrance",
                                 "phendrana_save_station_d", "phendrana_west_tower", "phendrana_control_tower",
                                 "phendrana_east_tower", "phendrana_aether_lab_entryway", "phendrana_research_lab_aether",
                                 "phendrana_research_core_access", "phendrana_research_core")},
               "phendrana_pike_access": 4,
               # specs/18m: region E, from the Transport Access and the Pike Access (round 4: the ice doors of the P29 and the
               # Research Core): its wave doors (round 1) and the Gravity Chamber's water (walked without the Gravity Suit, the
               # Tallon's, picked up in round 4: rounds.py's walk) keep it in round 4; the Storage Cave behind the plasma doors of
               # Phendrana's Edge (the Plasma Beam: round 5's, the Ice Ruins West's rule) and the Security Cave behind its power
               # bomb blocks (the Power Bomb: round 5's, the Warrior Shrine's rule) in round 6
               **{k: 4 for k in ("phendrana_frozen_pike", "phendrana_frost_cave_access", "phendrana_hunter_cave_access",
                                 "phendrana_frost_cave", "phendrana_save_station_c", "phendrana_hunter_cave",
                                 "phendrana_upper_edge_tunnel", "phendrana_lower_edge_tunnel", "phendrana_chamber_access",
                                 "phendrana_lake_tunnel", "phendrana_edge", "phendrana_gravity_chamber")},
               "phendrana_storage_cave": 6, "phendrana_security_cave": 6}
# the two transports, both to the Magmoor (WorldTeleporter destinations read from the bytes, epic 18): P0 to the Magmoor's P13
# (magmoor_transport_phendrana_north) and P29 to its P27 (magmoor_transport_phendrana_south); working elevators from specs/18e
ELEVATOR_ROOMS = frozenset({"phendrana_transport_magmoor_west", "phendrana_transport_magmoor_south"})
DECORATIVE_ELEVATORS: frozenset[str] = frozenset()
TRANSPORT_TO = {"phendrana_transport_magmoor_west": "magmoor_transport_phendrana_north",
                "phendrana_transport_magmoor_south": "magmoor_transport_phendrana_south"}


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
    Row("phendrana_transport_magmoor_west", 0, "Transport to Magmoor Caverns West", "A", (55, 56, 52), 3, 13),
    Row("phendrana_shoreline_entrance", 1, "Shoreline Entrance", "A", (91, 114, 34), 5, 14),
    Row("phendrana_shorelines", 2, "Phendrana Shorelines", "A", (175, 162, 70), 9, 13),
    Row("phendrana_temple_entryway", 3, "Temple Entryway", "A", (82, 38, 9), 9, 12),
    Row("phendrana_save_station_b", 4, "Save Station B", "A", (33, 30, 23), 8, 13),
    Row("phendrana_ruins_entryway", 5, "Ruins Entryway", "A", (86, 78, 47), 15, 12),
    Row("phendrana_plaza_walkway", 6, "Plaza Walkway", "A", (108, 61, 18), 15, 14),
    Row("phendrana_ice_ruins_access", 7, "Ice Ruins Access", "A", (82, 36, 11), 13, 15),
    Row("phendrana_chozo_ice_temple", 8, "Chozo Ice Temple", "A", (96, 147, 62), 4, 11),
    Row("phendrana_ice_ruins_east", 10, "Ice Ruins East", "A", (95, 99, 56), 16, 15),
    Row("phendrana_chapel_tunnel", 11, "Chapel Tunnel", "A", (73, 15, 20), 9, 11),
    Row("phendrana_chapel_of_the_elders", 14, "Chapel of the Elders", "A", (111, 85, 36), 11, 11),
    # --- B ---
    Row("phendrana_ice_ruins_west", 9, "Ice Ruins West", "B", (114, 99, 55), 18, 11),
    Row("phendrana_courtyard_entryway", 12, "Courtyard Entryway", "B", (41, 88, 14), 22, 12),
    Row("phendrana_canyon_entryway", 13, "Canyon Entryway", "B", (82, 35, 9), 15, 11),
    Row("phendrana_ruined_courtyard", 15, "Ruined Courtyard", "B", (95, 147, 70), 25, 12),
    Row("phendrana_canyon", 16, "Phendrana Canyon", "B", (178, 130, 104), 10, 8),
    Row("phendrana_save_station_a", 17, "Save Station A", "B", (26, 33, 17), 30, 13),
    Row("phendrana_specimen_storage", 18, "Specimen Storage", "B", (31, 64, 13), 30, 12),
    Row("phendrana_quarantine_access", 19, "Quarantine Access", "B", (51, 61, 17), 23, 13),
    Row("phendrana_research_entrance", 20, "Research Entrance", "B", (60, 104, 41), 32, 12),
    Row("phendrana_map_station", 22, "Map Station", "B", (34, 30, 12), 35, 12),
    Row("phendrana_hydra_lab_entryway", 23, "Hydra Lab Entryway", "B", (31, 82, 9), 33, 11),
    Row("phendrana_research_lab_hydra", 25, "Research Lab Hydra", "B", (67, 74, 45), 36, 11),
    # --- C ---
    Row("phendrana_north_quarantine_tunnel", 21, "North Quarantine Tunnel", "C", (173, 232, 113), 19, 14),
    Row("phendrana_quarantine_cave", 24, "Quarantine Cave", "C", (176, 182, 74), 25, 17),
    Row("phendrana_south_quarantine_tunnel", 26, "South Quarantine Tunnel", "C", (235, 167, 139), 31, 17),
    Row("phendrana_quarantine_monitor", 27, "Quarantine Monitor", "C", (78, 62, 44), 22, 18),
    Row("phendrana_transport_magmoor_south", 29, "Transport to Magmoor Caverns South", "C", (55, 59, 70), 37, 17),
    Row("phendrana_transport_access", 31, "Transport Access", "C", (28, 71, 27), 39, 17),
    # --- D ---
    Row("phendrana_observatory_access", 28, "Observatory Access", "D", (34, 76, 9), 38, 11),
    Row("phendrana_observatory", 30, "Observatory", "D", (60, 104, 72), 41, 11),
    Row("phendrana_west_tower_entrance", 32, "West Tower Entrance", "D", (31, 44, 6), 40, 12),
    Row("phendrana_save_station_d", 33, "Save Station D", "D", (29, 34, 11), 44, 12),
    Row("phendrana_west_tower", 35, "West Tower ", "D", (47, 47, 47), 38, 12),
    Row("phendrana_pike_access", 36, "Pike Access", "D", (62, 25, 15), 44, 17),
    Row("phendrana_control_tower", 39, "Control Tower", "D", (123, 111, 69), 34, 13),
    Row("phendrana_research_core", 40, "Research Core", "D", (69, 67, 67), 46, 16),
    Row("phendrana_east_tower", 43, "East Tower", "D", (47, 49, 47), 38, 14),
    Row("phendrana_research_core_access", 44, "Research Core Access", "D", (25, 51, 9), 44, 16),
    Row("phendrana_aether_lab_entryway", 50, "Aether Lab Entryway", "D", (31, 44, 6), 40, 15),
    Row("phendrana_research_lab_aether", 51, "Research Lab Aether", "D", (66, 80, 48), 41, 15),
    # --- E ---
    Row("phendrana_frozen_pike", 34, "Frozen Pike", "E", (83, 78, 107), 41, 17),
    Row("phendrana_frost_cave_access", 37, "Frost Cave Access", "E", (64, 166, 48), 44, 18),
    Row("phendrana_hunter_cave_access", 38, "Hunter Cave Access", "E", (57, 166, 38), 44, 20),
    Row("phendrana_frost_cave", 41, "Frost Cave", "E", (91, 95, 88), 50, 16),
    Row("phendrana_hunter_cave", 42, "Hunter Cave", "E", (87, 80, 52), 50, 19),
    Row("phendrana_save_station_c", 45, "Save Station C", "E", (52, 44, 28), 48, 17),
    Row("phendrana_upper_edge_tunnel", 46, "Upper Edge Tunnel", "E", (64, 83, 12), 53, 17),
    Row("phendrana_lower_edge_tunnel", 47, "Lower Edge Tunnel", "E", (59, 97, 18), 53, 19),
    Row("phendrana_chamber_access", 48, "Chamber Access", "E", (61, 40, 22), 53, 20),
    Row("phendrana_lake_tunnel", 49, "Lake Tunnel", "E", (65, 15, 17), 51, 21),
    Row("phendrana_edge", 52, "Phendrana's Edge", "E", (69, 71, 108), 56, 16),
    Row("phendrana_gravity_chamber", 53, "Gravity Chamber", "E", (70, 104, 60), 53, 21),
    Row("phendrana_storage_cave", 54, "Storage Cave", "E", (34, 33, 14), 58, 19),
    Row("phendrana_security_cave", 55, "Security Cave", "E", (43, 50, 24), 58, 18),
]

# (room, side, screen) <-> (room, side, screen), one per Prime door pair; sides opposite (R-L, B-T)
LINKS = [
    (("phendrana_transport_magmoor_west", "R", 1), ("phendrana_shoreline_entrance", "L", 0)),
    (("phendrana_shoreline_entrance", "R", 0), ("phendrana_shorelines", "L", 1)),
    (("phendrana_temple_entryway", "B", 0), ("phendrana_shorelines", "T", 0)),
    (("phendrana_save_station_b", "R", 0), ("phendrana_shorelines", "L", 0)),
    (("phendrana_shorelines", "R", 0), ("phendrana_ruins_entryway", "L", 1)),
    (("phendrana_shorelines", "R", 1), ("phendrana_plaza_walkway", "L", 0)),
    (("phendrana_shorelines", "B", 4), ("phendrana_ice_ruins_access", "T", 0)),
    (("phendrana_chozo_ice_temple", "R", 1), ("phendrana_temple_entryway", "L", 0)),
    (("phendrana_ruins_entryway", "R", 0), ("phendrana_ice_ruins_west", "L", 1)),
    (("phendrana_plaza_walkway", "B", 1), ("phendrana_ice_ruins_east", "T", 0)),
    (("phendrana_ice_ruins_access", "R", 0), ("phendrana_ice_ruins_east", "L", 0)),
    (("phendrana_chozo_ice_temple", "R", 0), ("phendrana_chapel_tunnel", "L", 0)),
    (("phendrana_ice_ruins_west", "R", 1), ("phendrana_courtyard_entryway", "L", 0)),
    (("phendrana_canyon_entryway", "R", 0), ("phendrana_ice_ruins_west", "L", 0)),
    (("phendrana_chapel_tunnel", "R", 0), ("phendrana_chapel_of_the_elders", "L", 0)),
    (("phendrana_courtyard_entryway", "R", 0), ("phendrana_ruined_courtyard", "L", 0)),
    (("phendrana_canyon", "B", 5), ("phendrana_canyon_entryway", "T", 0)),
    (("phendrana_ruined_courtyard", "R", 1), ("phendrana_save_station_a", "L", 0)),
    (("phendrana_ruined_courtyard", "R", 0), ("phendrana_specimen_storage", "L", 0)),
    (("phendrana_quarantine_access", "R", 0), ("phendrana_ruined_courtyard", "L", 1)),
    (("phendrana_specimen_storage", "R", 0), ("phendrana_research_entrance", "L", 0)),
    (("phendrana_quarantine_access", "B", 0), ("phendrana_north_quarantine_tunnel", "T", 4)),
    (("phendrana_research_entrance", "R", 0), ("phendrana_map_station", "L", 0)),
    (("phendrana_hydra_lab_entryway", "B", 0), ("phendrana_research_entrance", "T", 1)),
    (("phendrana_north_quarantine_tunnel", "R", 3), ("phendrana_quarantine_cave", "L", 0)),
    (("phendrana_hydra_lab_entryway", "R", 0), ("phendrana_research_lab_hydra", "L", 0)),
    (("phendrana_quarantine_cave", "R", 0), ("phendrana_south_quarantine_tunnel", "L", 0)),
    (("phendrana_quarantine_monitor", "R", 0), ("phendrana_quarantine_cave", "L", 1)),
    (("phendrana_research_lab_hydra", "R", 0), ("phendrana_observatory_access", "L", 0)),
    (("phendrana_south_quarantine_tunnel", "R", 1), ("phendrana_transport_magmoor_south", "L", 1)),
    (("phendrana_observatory_access", "R", 0), ("phendrana_observatory", "L", 0)),
    (("phendrana_transport_magmoor_south", "R", 0), ("phendrana_transport_access", "L", 0)),
    (("phendrana_west_tower_entrance", "R", 0), ("phendrana_observatory", "L", 1)),
    (("phendrana_observatory", "R", 1), ("phendrana_save_station_d", "L", 0)),
    (("phendrana_transport_access", "R", 0), ("phendrana_frozen_pike", "L", 0)),
    (("phendrana_west_tower", "R", 0), ("phendrana_west_tower_entrance", "L", 0)),
    (("phendrana_frozen_pike", "R", 0), ("phendrana_pike_access", "L", 0)),
    (("phendrana_frozen_pike", "R", 1), ("phendrana_frost_cave_access", "L", 0)),
    (("phendrana_frozen_pike", "R", 3), ("phendrana_hunter_cave_access", "L", 0)),
    (("phendrana_control_tower", "R", 0), ("phendrana_west_tower", "L", 1)),
    (("phendrana_pike_access", "R", 0), ("phendrana_research_core", "L", 1)),
    (("phendrana_frost_cave_access", "R", 0), ("phendrana_frost_cave", "L", 2)),
    (("phendrana_hunter_cave_access", "R", 0), ("phendrana_hunter_cave", "L", 1)),
    (("phendrana_control_tower", "R", 1), ("phendrana_east_tower", "L", 0)),
    (("phendrana_research_core_access", "R", 0), ("phendrana_research_core", "L", 0)),
    (("phendrana_save_station_c", "R", 0), ("phendrana_frost_cave", "L", 1)),
    (("phendrana_frost_cave", "R", 1), ("phendrana_upper_edge_tunnel", "L", 0)),
    (("phendrana_hunter_cave", "R", 0), ("phendrana_lower_edge_tunnel", "L", 0)),
    (("phendrana_hunter_cave", "R", 1), ("phendrana_chamber_access", "L", 0)),
    (("phendrana_hunter_cave", "B", 1), ("phendrana_lake_tunnel", "T", 0)),
    (("phendrana_east_tower", "R", 1), ("phendrana_aether_lab_entryway", "L", 0)),
    (("phendrana_research_lab_aether", "R", 1), ("phendrana_research_core_access", "L", 0)),
    (("phendrana_upper_edge_tunnel", "R", 0), ("phendrana_edge", "L", 1)),
    (("phendrana_lower_edge_tunnel", "R", 0), ("phendrana_edge", "L", 3)),
    (("phendrana_chamber_access", "B", 0), ("phendrana_gravity_chamber", "T", 0)),
    (("phendrana_lake_tunnel", "R", 0), ("phendrana_gravity_chamber", "L", 0)),
    (("phendrana_aether_lab_entryway", "R", 0), ("phendrana_research_lab_aether", "L", 0)),
    (("phendrana_edge", "R", 3), ("phendrana_storage_cave", "L", 0)),
    (("phendrana_edge", "R", 2), ("phendrana_security_cave", "L", 0)),
]

# --- Prime's locks, as data (specs/18c) ------------------------------------------------------------------------------
# Per dock (this room, the room the door leads to): the kinds of lock Prime has there, by the Chozo's rule
# (chozo/rooms.py prime_dock_locks, on research/prime_phendrana_locks.json): missile = "Actor Missile Lock" (blast shield), key =
# "Trigger_DoorKey" without one (a coloured door), morph = a "Door_Area Morphball" door, event = "Actor Door Lock" (a door that
# locks during a fight or a scene: the Sheegoth's chapel, the Thardus' cave, the labs' ambushes, the Shorelines' and Plaza
# Walkway's 2nd-pass Sheegoths...), one_way = a "one way door" scan. Phendrana has 72 key docks, 20 event, 5 missile, 4 morph.
DOCK_LOCKS = {
    ("phendrana_shorelines", "phendrana_ice_ruins_access"): {"event"},
    ("phendrana_plaza_walkway", "phendrana_shorelines"): {"event"},
    ("phendrana_plaza_walkway", "phendrana_ice_ruins_east"): {"event"},
    ("phendrana_ice_ruins_west", "phendrana_courtyard_entryway"): {"key"},
    ("phendrana_ice_ruins_west", "phendrana_canyon_entryway"): {"missile"},
    ("phendrana_canyon_entryway", "phendrana_ice_ruins_west"): {"key"},
    ("phendrana_chapel_of_the_elders", "phendrana_chapel_tunnel"): {"event", "key"},
    ("phendrana_ruined_courtyard", "phendrana_courtyard_entryway"): {"event"},
    ("phendrana_ruined_courtyard", "phendrana_save_station_a"): {"missile"},
    ("phendrana_ruined_courtyard", "phendrana_specimen_storage"): {"key"},
    ("phendrana_specimen_storage", "phendrana_research_entrance"): {"key"},
    ("phendrana_specimen_storage", "phendrana_ruined_courtyard"): {"key"},
    ("phendrana_quarantine_access", "phendrana_north_quarantine_tunnel"): {"event"},
    ("phendrana_quarantine_access", "phendrana_ruined_courtyard"): {"event"},
    ("phendrana_research_entrance", "phendrana_specimen_storage"): {"event", "key"},
    ("phendrana_research_entrance", "phendrana_map_station"): {"event"},
    ("phendrana_research_entrance", "phendrana_hydra_lab_entryway"): {"event", "key"},
    ("phendrana_north_quarantine_tunnel", "phendrana_quarantine_cave"): {"key"},
    ("phendrana_north_quarantine_tunnel", "phendrana_quarantine_access"): {"key"},
    ("phendrana_hydra_lab_entryway", "phendrana_research_entrance"): {"key"},
    ("phendrana_hydra_lab_entryway", "phendrana_research_lab_hydra"): {"key"},
    ("phendrana_quarantine_cave", "phendrana_north_quarantine_tunnel"): {"event", "key"},
    ("phendrana_quarantine_cave", "phendrana_south_quarantine_tunnel"): {"event", "key"},
    ("phendrana_quarantine_cave", "phendrana_quarantine_monitor"): {"morph"},
    ("phendrana_research_lab_hydra", "phendrana_hydra_lab_entryway"): {"key"},
    ("phendrana_research_lab_hydra", "phendrana_observatory_access"): {"key"},
    ("phendrana_south_quarantine_tunnel", "phendrana_quarantine_cave"): {"key"},
    ("phendrana_south_quarantine_tunnel", "phendrana_transport_magmoor_south"): {"key"},
    ("phendrana_quarantine_monitor", "phendrana_quarantine_cave"): {"morph"},
    ("phendrana_observatory_access", "phendrana_observatory"): {"event", "key"},
    ("phendrana_observatory_access", "phendrana_research_lab_hydra"): {"event", "key"},
    ("phendrana_transport_magmoor_south", "phendrana_transport_access"): {"key"},
    ("phendrana_transport_magmoor_south", "phendrana_south_quarantine_tunnel"): {"key"},
    ("phendrana_observatory", "phendrana_observatory_access"): {"event", "key"},
    ("phendrana_observatory", "phendrana_west_tower_entrance"): {"key"},
    ("phendrana_observatory", "phendrana_save_station_d"): {"missile"},
    ("phendrana_transport_access", "phendrana_transport_magmoor_south"): {"key"},
    ("phendrana_transport_access", "phendrana_frozen_pike"): {"key"},
    ("phendrana_west_tower_entrance", "phendrana_west_tower"): {"missile"},
    ("phendrana_west_tower_entrance", "phendrana_observatory"): {"key"},
    ("phendrana_frozen_pike", "phendrana_pike_access"): {"key"},
    ("phendrana_frozen_pike", "phendrana_transport_access"): {"key"},
    ("phendrana_frozen_pike", "phendrana_frost_cave_access"): {"key"},
    ("phendrana_frozen_pike", "phendrana_hunter_cave_access"): {"key"},
    ("phendrana_west_tower", "phendrana_west_tower_entrance"): {"missile"},
    ("phendrana_west_tower", "phendrana_control_tower"): {"key"},
    ("phendrana_pike_access", "phendrana_frozen_pike"): {"key"},
    ("phendrana_pike_access", "phendrana_research_core"): {"key"},
    ("phendrana_frost_cave_access", "phendrana_frozen_pike"): {"key"},
    ("phendrana_frost_cave_access", "phendrana_frost_cave"): {"key"},
    ("phendrana_hunter_cave_access", "phendrana_frozen_pike"): {"key"},
    ("phendrana_hunter_cave_access", "phendrana_hunter_cave"): {"key"},
    ("phendrana_control_tower", "phendrana_east_tower"): {"event", "key"},
    ("phendrana_control_tower", "phendrana_west_tower"): {"event", "key"},
    ("phendrana_research_core", "phendrana_pike_access"): {"key"},
    ("phendrana_research_core", "phendrana_research_core_access"): {"key"},
    ("phendrana_frost_cave", "phendrana_save_station_c"): {"key"},
    ("phendrana_frost_cave", "phendrana_frost_cave_access"): {"key"},
    ("phendrana_frost_cave", "phendrana_upper_edge_tunnel"): {"key"},
    ("phendrana_hunter_cave", "phendrana_hunter_cave_access"): {"key"},
    ("phendrana_hunter_cave", "phendrana_lower_edge_tunnel"): {"key"},
    ("phendrana_hunter_cave", "phendrana_chamber_access"): {"key"},
    ("phendrana_hunter_cave", "phendrana_lake_tunnel"): {"key"},
    ("phendrana_east_tower", "phendrana_aether_lab_entryway"): {"key"},
    ("phendrana_east_tower", "phendrana_control_tower"): {"key"},
    ("phendrana_research_core_access", "phendrana_research_core"): {"event", "key"},
    ("phendrana_research_core_access", "phendrana_research_lab_aether"): {"event", "key"},
    ("phendrana_save_station_c", "phendrana_frost_cave"): {"key"},
    ("phendrana_upper_edge_tunnel", "phendrana_edge"): {"key"},
    ("phendrana_upper_edge_tunnel", "phendrana_frost_cave"): {"key"},
    ("phendrana_lower_edge_tunnel", "phendrana_edge"): {"key"},
    ("phendrana_lower_edge_tunnel", "phendrana_hunter_cave"): {"key"},
    ("phendrana_chamber_access", "phendrana_hunter_cave"): {"key"},
    ("phendrana_chamber_access", "phendrana_gravity_chamber"): {"key"},
    ("phendrana_lake_tunnel", "phendrana_hunter_cave"): {"key"},
    ("phendrana_lake_tunnel", "phendrana_gravity_chamber"): {"key"},
    ("phendrana_aether_lab_entryway", "phendrana_east_tower"): {"key"},
    ("phendrana_aether_lab_entryway", "phendrana_research_lab_aether"): {"key"},
    ("phendrana_research_lab_aether", "phendrana_aether_lab_entryway"): {"event", "key"},
    ("phendrana_research_lab_aether", "phendrana_research_core_access"): {"key"},
    ("phendrana_edge", "phendrana_lower_edge_tunnel"): {"key"},
    ("phendrana_edge", "phendrana_upper_edge_tunnel"): {"key"},
    ("phendrana_edge", "phendrana_storage_cave"): {"key"},
    ("phendrana_edge", "phendrana_security_cave"): {"morph"},
    ("phendrana_gravity_chamber", "phendrana_lake_tunnel"): {"key"},
    ("phendrana_gravity_chamber", "phendrana_chamber_access"): {"key"},
    ("phendrana_storage_cave", "phendrana_edge"): {"key"},
    ("phendrana_security_cave", "phendrana_edge"): {"morph"},
}

# The beam of each key dock, from its "Trigger_DoorKey" DamageVulnerability (research/prime_phendrana_locks.json "key_vuln": power,
# ice, wave, plasma; 1 = hurts, 2 = immune), magmoor/rooms.py BEAM_OF_VULN, and ANY_BEAM (1 1 1 1): a key door any beam opens (the
# Canyon Entryway's door to the Ice Ruins West). Prime's beam, not yet the SM mechanism (the region children).
ANY_BEAM = "any_beam"
BEAM_OF_KEY = {**BEAM_OF_VULN, (1, 1, 1, 1): ANY_BEAM}
KEY_BEAM = {
    ("phendrana_ice_ruins_west", "phendrana_courtyard_entryway"): WAVE,
    ("phendrana_canyon_entryway", "phendrana_ice_ruins_west"): ANY_BEAM,
    ("phendrana_chapel_of_the_elders", "phendrana_chapel_tunnel"): WAVE,
    ("phendrana_ruined_courtyard", "phendrana_specimen_storage"): WAVE,
    ("phendrana_specimen_storage", "phendrana_research_entrance"): WAVE,
    ("phendrana_specimen_storage", "phendrana_ruined_courtyard"): WAVE,
    ("phendrana_research_entrance", "phendrana_specimen_storage"): WAVE,
    ("phendrana_research_entrance", "phendrana_hydra_lab_entryway"): WAVE,
    ("phendrana_north_quarantine_tunnel", "phendrana_quarantine_cave"): WAVE,
    ("phendrana_north_quarantine_tunnel", "phendrana_quarantine_access"): WAVE,
    ("phendrana_hydra_lab_entryway", "phendrana_research_entrance"): WAVE,
    ("phendrana_hydra_lab_entryway", "phendrana_research_lab_hydra"): WAVE,
    ("phendrana_quarantine_cave", "phendrana_north_quarantine_tunnel"): WAVE,
    ("phendrana_quarantine_cave", "phendrana_south_quarantine_tunnel"): WAVE,
    ("phendrana_research_lab_hydra", "phendrana_hydra_lab_entryway"): WAVE,
    ("phendrana_research_lab_hydra", "phendrana_observatory_access"): WAVE,
    ("phendrana_south_quarantine_tunnel", "phendrana_quarantine_cave"): WAVE,
    ("phendrana_south_quarantine_tunnel", "phendrana_transport_magmoor_south"): WAVE,
    ("phendrana_observatory_access", "phendrana_observatory"): WAVE,
    ("phendrana_observatory_access", "phendrana_research_lab_hydra"): WAVE,
    ("phendrana_transport_magmoor_south", "phendrana_transport_access"): ICE,
    ("phendrana_transport_magmoor_south", "phendrana_south_quarantine_tunnel"): WAVE,
    ("phendrana_observatory", "phendrana_observatory_access"): WAVE,
    ("phendrana_observatory", "phendrana_west_tower_entrance"): WAVE,
    ("phendrana_transport_access", "phendrana_transport_magmoor_south"): ICE,
    ("phendrana_transport_access", "phendrana_frozen_pike"): WAVE,
    ("phendrana_west_tower_entrance", "phendrana_observatory"): WAVE,
    ("phendrana_frozen_pike", "phendrana_pike_access"): WAVE,
    ("phendrana_frozen_pike", "phendrana_transport_access"): WAVE,
    ("phendrana_frozen_pike", "phendrana_frost_cave_access"): WAVE,
    ("phendrana_frozen_pike", "phendrana_hunter_cave_access"): WAVE,
    ("phendrana_west_tower", "phendrana_control_tower"): WAVE,
    ("phendrana_pike_access", "phendrana_frozen_pike"): WAVE,
    ("phendrana_pike_access", "phendrana_research_core"): ICE,
    ("phendrana_frost_cave_access", "phendrana_frozen_pike"): WAVE,
    ("phendrana_frost_cave_access", "phendrana_frost_cave"): WAVE,
    ("phendrana_hunter_cave_access", "phendrana_frozen_pike"): WAVE,
    ("phendrana_hunter_cave_access", "phendrana_hunter_cave"): WAVE,
    ("phendrana_control_tower", "phendrana_east_tower"): WAVE,
    ("phendrana_control_tower", "phendrana_west_tower"): WAVE,
    ("phendrana_research_core", "phendrana_pike_access"): ICE,
    ("phendrana_research_core", "phendrana_research_core_access"): WAVE,
    ("phendrana_frost_cave", "phendrana_save_station_c"): WAVE,
    ("phendrana_frost_cave", "phendrana_frost_cave_access"): WAVE,
    ("phendrana_frost_cave", "phendrana_upper_edge_tunnel"): WAVE,
    ("phendrana_hunter_cave", "phendrana_hunter_cave_access"): WAVE,
    ("phendrana_hunter_cave", "phendrana_lower_edge_tunnel"): WAVE,
    ("phendrana_hunter_cave", "phendrana_chamber_access"): WAVE,
    ("phendrana_hunter_cave", "phendrana_lake_tunnel"): WAVE,
    ("phendrana_east_tower", "phendrana_aether_lab_entryway"): WAVE,
    ("phendrana_east_tower", "phendrana_control_tower"): WAVE,
    ("phendrana_research_core_access", "phendrana_research_core"): WAVE,
    ("phendrana_research_core_access", "phendrana_research_lab_aether"): WAVE,
    ("phendrana_save_station_c", "phendrana_frost_cave"): WAVE,
    ("phendrana_upper_edge_tunnel", "phendrana_edge"): WAVE,
    ("phendrana_upper_edge_tunnel", "phendrana_frost_cave"): WAVE,
    ("phendrana_lower_edge_tunnel", "phendrana_edge"): WAVE,
    ("phendrana_lower_edge_tunnel", "phendrana_hunter_cave"): WAVE,
    ("phendrana_chamber_access", "phendrana_hunter_cave"): WAVE,
    ("phendrana_chamber_access", "phendrana_gravity_chamber"): WAVE,
    ("phendrana_lake_tunnel", "phendrana_hunter_cave"): WAVE,
    ("phendrana_lake_tunnel", "phendrana_gravity_chamber"): WAVE,
    ("phendrana_aether_lab_entryway", "phendrana_east_tower"): WAVE,
    ("phendrana_aether_lab_entryway", "phendrana_research_lab_aether"): WAVE,
    ("phendrana_research_lab_aether", "phendrana_aether_lab_entryway"): WAVE,
    ("phendrana_research_lab_aether", "phendrana_research_core_access"): WAVE,
    ("phendrana_edge", "phendrana_lower_edge_tunnel"): WAVE,
    ("phendrana_edge", "phendrana_upper_edge_tunnel"): WAVE,
    ("phendrana_edge", "phendrana_storage_cave"): PLASMA,
    ("phendrana_gravity_chamber", "phendrana_lake_tunnel"): WAVE,
    ("phendrana_gravity_chamber", "phendrana_chamber_access"): WAVE,
    ("phendrana_storage_cave", "phendrana_edge"): PLASMA,
}

# In-room features of Prime that gate movement (the dumper's names: chozo/rooms.py FEATURES): spider, bomb_slot, breakable,
# halfpipe, grapple, heat, water (a "Water" object: Phendrana's are all "ice water"), lava, morph_door
FEATURES = {
    "phendrana_shorelines": {"spider", "water"},
    "phendrana_chozo_ice_temple": {"bomb_slot"},
    "phendrana_ice_ruins_east": {"spider"},
    "phendrana_ruined_courtyard": {"bomb_slot", "spider", "water"},
    "phendrana_canyon": {"halfpipe"},
    "phendrana_quarantine_cave": {"grapple", "morph_door", "spider"},
    "phendrana_quarantine_monitor": {"morph_door"},
    "phendrana_transport_magmoor_south": {"spider"},
    "phendrana_observatory": {"bomb_slot"},
    "phendrana_frozen_pike": {"water"},
    "phendrana_hunter_cave_access": {"water"},
    "phendrana_frost_cave": {"water"},
    "phendrana_hunter_cave": {"grapple", "water"},
    "phendrana_lower_edge_tunnel": {"water"},
    "phendrana_lake_tunnel": {"water"},
    "phendrana_edge": {"grapple", "morph_door", "water"},
    "phendrana_gravity_chamber": {"grapple", "water"},
    "phendrana_security_cave": {"morph_door"},
}

# specs/18c: the rooms where it snows in Prime: an "AreaAttributes" with fx type 1 (research/prime_phendrana_locks.json
# "env_fx"; the epic's user decision 6, padrão aceito: falling snow there, specs/18d)
SNOW_ROOMS: frozenset[str] = frozenset({
    "phendrana_canyon",
    "phendrana_chapel_of_the_elders",
    "phendrana_chozo_ice_temple",
    "phendrana_control_tower",
    "phendrana_edge",
    "phendrana_frost_cave_access",
    "phendrana_frozen_pike",
    "phendrana_ice_ruins_east",
    "phendrana_ice_ruins_west",
    "phendrana_north_quarantine_tunnel",
    "phendrana_quarantine_cave",
    "phendrana_quarantine_monitor",
    "phendrana_ruined_courtyard",
    "phendrana_ruins_entryway",
    "phendrana_save_station_a",
    "phendrana_save_station_c",
    "phendrana_security_cave",
    "phendrana_shoreline_entrance",
    "phendrana_shorelines",
    "phendrana_south_quarantine_tunnel",
    "phendrana_storage_cave",
    "phendrana_transport_access",
    "phendrana_transport_magmoor_west",
})
# the rooms with a "Water" object (FEATURES water): only the Gravity Chamber is flooded, the other lakes dry (user decision 5,
# specs/18m: FLOODED)
WATER_ROOMS: frozenset[str] = frozenset({
    "phendrana_edge",
    "phendrana_frost_cave",
    "phendrana_frozen_pike",
    "phendrana_gravity_chamber",
    "phendrana_hunter_cave",
    "phendrana_hunter_cave_access",
    "phendrana_lake_tunnel",
    "phendrana_lower_edge_tunnel",
    "phendrana_ruined_courtyard",
    "phendrana_shorelines",
})
# specs/18m (the epic's user decision 5): the flooded rooms of Phendrana (the whole room under water, RoomDef.water: the sunken
# frigate's and the Reflecting Pool's water, specs/07l and 12l; measured in area 4 by specs/18d): the Gravity Chamber alone
FLOODED: frozenset[str] = frozenset({"phendrana_gravity_chamber"})
# the rooms with ice only the Plasma Beam melts (a DamageableTrigger that is not a door's, hurt only by the Plasma: "beam_only"):
# the Chozo Ice Temple's artifact, the Ice Ruins West's power bomb expansion, the Transport Access' energy tank
PLASMA_ICE: frozenset[str] = frozenset({
    "phendrana_chozo_ice_temple",
    "phendrana_ice_ruins_west",
    "phendrana_transport_access",
})
# the rooms with a panel only the Wave Beam hurts ("beam_only" wave; Prime's Thermal Visor shows the wire): the Ruined
# Courtyard and the Research Core
WAVE_PANELS: frozenset[str] = frozenset({
    "phendrana_research_core",
    "phendrana_ruined_courtyard",
})


# --- region A's locks in the SM (specs/18f; epic 18, technical decision 3: Prime's locks -> mechanisms that exist) -------------
# Prime's locks in region A (DOCK_LOCKS): the Chapel of the Elders' door to the Chapel Tunnel, a wave door from the chapel's side
# (and the Sheegoth's event lock: BOSS_DOORS, its fight in specs/18h) = a wave beam door there (the Wave Beam: the Tallon's Magmoor
# East, round 1); the Shorelines' and the Plaza Walkway's event locks (the Ice Sheegoths of Prime's 2nd pass, an event layer: out,
# EVENT_OUT). Prime's in-room locks of the region (FEATURES) that gate a door, as geometry on that door's side (layouts.py, as the
# Magmoor's FEATURE_GEOMETRY): the Chozo Ice Temple's bomb slot = its R0 door to the Chapel Tunnel in a chamber behind a 1-row
# tunnel shut by a bomb block (the Morph Ball and the Bombs). The Spider Ball tracks of the Shorelines and the Ice Ruins East gate
# only items (Space Jump ledges: tools/phendrana/items.py `needs`).
GATES = {
    frozenset({"phendrana_chapel_of_the_elders", "phendrana_chapel_tunnel"}): Gate(
        frozenset({WAVE}), ("phendrana_chapel_of_the_elders",)),
    frozenset({"phendrana_chozo_ice_temple", "phendrana_chapel_tunnel"}): Gate(
        frozenset({MORPH_ITEM, BOMBS}), (), ("phendrana_chozo_ice_temple",)),
    # specs/18i, region B. Prime's locks there (DOCK_LOCKS, KEY_BEAM): the missile shields of the Ice Ruins West's door to the
    # Canyon Entryway and of the Ruined Courtyard's door to Save Station A, each on its side = red doors (bits
    # PHENDRANA_MISSILE_BIT0 + n in this order: $C2, $C3); the wave doors = wave beam doors on Prime's sides (the Ice Ruins
    # West's side of its Courtyard Entryway door; both sides of the Courtyard <-> Specimen Storage, Specimen Storage <->
    # Research Entrance, Research Entrance <-> Hydra Lab Entryway (a ceiling/floor door: the vertical wave door,
    # tallon/beamdoors.py) and Hydra Lab Entryway <-> Research Lab Hydra links); the Canyon Entryway's door to the Ice Ruins
    # West opens to any beam (ANY_BEAM: no cap); the event locks (the labs' ambushes, the 2nd pass) are event layers' (out).
    # Prime's in-room locks of the region gate items only (tools/phendrana/items.py `needs`): the Courtyard's bomb slot (its
    # Energy Tank behind a bomb block) and the Ice Ruins West's plasma ice (its power bomb expansion behind a plasma cap,
    # RoomDef.caps); the Courtyard's Spider Ball track and the Canyon's half-pipe gate nothing here (no item there: the Boost
    # Ball's place is empty, the user's decision 3).
    frozenset({"phendrana_ice_ruins_west", "phendrana_canyon_entryway"}): Gate(
        frozenset({MISSILE_ITEM}), ("phendrana_ice_ruins_west",)),
    frozenset({"phendrana_ruined_courtyard", "phendrana_save_station_a"}): Gate(
        frozenset({MISSILE_ITEM}), ("phendrana_ruined_courtyard",)),
    frozenset({"phendrana_ice_ruins_west", "phendrana_courtyard_entryway"}): Gate(
        frozenset({WAVE}), ("phendrana_ice_ruins_west",)),
    frozenset({"phendrana_ruined_courtyard", "phendrana_specimen_storage"}): Gate(
        frozenset({WAVE}), ("phendrana_ruined_courtyard", "phendrana_specimen_storage")),
    frozenset({"phendrana_specimen_storage", "phendrana_research_entrance"}): Gate(
        frozenset({WAVE}), ("phendrana_specimen_storage", "phendrana_research_entrance")),
    frozenset({"phendrana_research_entrance", "phendrana_hydra_lab_entryway"}): Gate(
        frozenset({WAVE}), ("phendrana_research_entrance", "phendrana_hydra_lab_entryway")),
    frozenset({"phendrana_hydra_lab_entryway", "phendrana_research_lab_hydra"}): Gate(
        frozenset({WAVE}), ("phendrana_hydra_lab_entryway", "phendrana_research_lab_hydra")),
    # specs/18j, region C. Prime's locks there (DOCK_LOCKS, KEY_BEAM): the wave doors on Prime's sides (the North Quarantine
    # Tunnel's ceiling door to the Quarantine Access: only on the tunnel's side, a vertical wave door in the snow look, whose
    # table has its paint since this spec; both sides of the tunnel <-> Quarantine Cave, Quarantine Cave <-> South Quarantine
    # Tunnel and South Quarantine Tunnel <-> P29 links); the ice doors on both sides of the P29 <-> Transport Access link; the
    # Morph Ball doors on both sides of the Quarantine Cave <-> Quarantine Monitor link = each side's door behind a 1-row Morph
    # Ball tunnel (the Chozo's Main Plaza way, specs/12f), a chamber at the door to stand up in and open it; the event locks:
    # the Thardus' doors of the cave (BOSS_DOORS: specs/18k) and the Quarantine Access' (the scenes of the quarantine, out).
    # Prime's in-room locks of the region: the Transport Access' plasma ice = its Energy Tank's niche behind a plasma cap
    # (RoomDef.caps, items `needs`); the cave's Spider Ball track and grapple points and the P29's track gate nothing (the
    # Spider Ball's place is empty, the user's decision 3; the Monitor's door is the Morph Ball's).
    frozenset({"phendrana_north_quarantine_tunnel", "phendrana_quarantine_access"}): Gate(
        frozenset({WAVE}), ("phendrana_north_quarantine_tunnel",)),
    frozenset({"phendrana_north_quarantine_tunnel", "phendrana_quarantine_cave"}): Gate(
        frozenset({WAVE}), ("phendrana_north_quarantine_tunnel", "phendrana_quarantine_cave")),
    frozenset({"phendrana_quarantine_cave", "phendrana_south_quarantine_tunnel"}): Gate(
        frozenset({WAVE}), ("phendrana_quarantine_cave", "phendrana_south_quarantine_tunnel")),
    frozenset({"phendrana_quarantine_cave", "phendrana_quarantine_monitor"}): Gate(
        frozenset({MORPH_ITEM}), (), ("phendrana_quarantine_cave", "phendrana_quarantine_monitor")),
    frozenset({"phendrana_south_quarantine_tunnel", "phendrana_transport_magmoor_south"}): Gate(
        frozenset({WAVE}), ("phendrana_south_quarantine_tunnel", "phendrana_transport_magmoor_south")),
    frozenset({"phendrana_transport_magmoor_south", "phendrana_transport_access"}): Gate(
        frozenset({ICE}), ("phendrana_transport_magmoor_south", "phendrana_transport_access")),
    # specs/18l, region D. Prime's locks there (DOCK_LOCKS, KEY_BEAM): the missile shields of the Observatory's door to Save
    # Station D (on the Observatory's side) and of the West Tower Entrance <-> West Tower link (on both sides: one bit for the
    # two, opened from either side, specs/12i's rule) = red doors (PHENDRANA_MISSILE_BIT0 + n in GATES' order: $C4, $C5); the
    # wave doors on both sides of the Hydra <-> Observatory Access, Observatory Access <-> Observatory, Observatory <-> West
    # Tower Entrance, West Tower <-> Control Tower, Control Tower <-> East Tower, East Tower <-> Aether Lab Entryway, Aether Lab
    # Entryway <-> Research Lab Aether, Research Lab Aether <-> Research Core Access and Research Core Access <-> Research Core
    # links; the ice doors on both sides of the Research Core <-> Pike Access link; the event locks (the labs' ambushes, the
    # Control Tower's) are event layers' (out). Prime's in-room locks of the region: the Observatory's bomb slot = the Super
    # Missile's chamber behind a bomb block (items `needs`); the Research Core's wave panel (the Thermal Visor's puzzle: its
    # place is empty, the user's decision 3) gates nothing.
    frozenset({"phendrana_observatory", "phendrana_save_station_d"}): Gate(
        frozenset({MISSILE_ITEM}), ("phendrana_observatory",)),
    frozenset({"phendrana_west_tower_entrance", "phendrana_west_tower"}): Gate(
        frozenset({MISSILE_ITEM}), ("phendrana_west_tower_entrance", "phendrana_west_tower")),
    **{frozenset({a, b}): Gate(frozenset({WAVE}), (a, b)) for a, b in (
        ("phendrana_research_lab_hydra", "phendrana_observatory_access"),
        ("phendrana_observatory_access", "phendrana_observatory"),
        ("phendrana_observatory", "phendrana_west_tower_entrance"),
        ("phendrana_west_tower", "phendrana_control_tower"),
        ("phendrana_control_tower", "phendrana_east_tower"),
        ("phendrana_east_tower", "phendrana_aether_lab_entryway"),
        ("phendrana_aether_lab_entryway", "phendrana_research_lab_aether"),
        ("phendrana_research_lab_aether", "phendrana_research_core_access"),
        ("phendrana_research_core_access", "phendrana_research_core"))},
    frozenset({"phendrana_research_core", "phendrana_pike_access"}): Gate(
        frozenset({ICE}), ("phendrana_research_core", "phendrana_pike_access")),
    # specs/18m, region E. Prime's locks there (DOCK_LOCKS, KEY_BEAM): the wave doors on both sides of every link of the region
    # (and of its links to the Transport Access and the Pike Access; the Hunter Cave <-> Lake Tunnel and Chamber Access <->
    # Gravity Chamber links are floor/ceiling doors: the vertical wave door, in the snow look's table since specs/18j); the
    # plasma doors on both sides of Phendrana's Edge <-> Storage Cave; the Morph Ball doors on both sides of Phendrana's Edge <->
    # Security Cave = each side's door behind a 1-row Morph Ball tunnel (specs/18j's way) shut by a power bomb block (the epic's
    # technical decision 3: the Security Cave's power bomb expansion; the Magmoor's Warrior Shrine, specs/17h): the Morph Ball
    # and the Power Bomb (round 5's: the expansion in round 6, never before). Prime's in-room locks of the region: the Gravity
    # Chamber's grapple point = its missile's Space Jump ledge (items `needs`; under water the Space Jump works only with the
    # Gravity Suit); the Hunter Cave's and Phendrana's Edge's grapple points and the stalactites gate nothing; the lakes are dry.
    **{frozenset({a, b}): Gate(frozenset({WAVE}), (a, b)) for a, b in (
        ("phendrana_transport_access", "phendrana_frozen_pike"),
        ("phendrana_frozen_pike", "phendrana_pike_access"),
        ("phendrana_frozen_pike", "phendrana_frost_cave_access"),
        ("phendrana_frozen_pike", "phendrana_hunter_cave_access"),
        ("phendrana_frost_cave_access", "phendrana_frost_cave"),
        ("phendrana_hunter_cave_access", "phendrana_hunter_cave"),
        ("phendrana_save_station_c", "phendrana_frost_cave"),
        ("phendrana_frost_cave", "phendrana_upper_edge_tunnel"),
        ("phendrana_hunter_cave", "phendrana_lower_edge_tunnel"),
        ("phendrana_hunter_cave", "phendrana_chamber_access"),
        ("phendrana_hunter_cave", "phendrana_lake_tunnel"),
        ("phendrana_upper_edge_tunnel", "phendrana_edge"),
        ("phendrana_lower_edge_tunnel", "phendrana_edge"),
        ("phendrana_chamber_access", "phendrana_gravity_chamber"),
        ("phendrana_lake_tunnel", "phendrana_gravity_chamber"))},
    frozenset({"phendrana_edge", "phendrana_storage_cave"}): Gate(
        frozenset({PLASMA}), ("phendrana_edge", "phendrana_storage_cave")),
    frozenset({"phendrana_edge", "phendrana_security_cave"}): Gate(
        frozenset({MORPH_ITEM, POWER_BOMB}), (), ("phendrana_edge", "phendrana_security_cave")),
}
# specs/18i: Phendrana's red doors' bits ($7ED8B0 + bit), one per missile gate in GATES' order, after the Magmoor's $C0-$C1
# (magmoor/rooms.py MAGMOOR_MISSILE_BIT0); the epic's five shields: the Ice Ruins West's ($C2) and Save Station A's ($C3);
# specs/18l: the Observatory's to Save Station D ($C4) and the West Tower Entrance <-> West Tower link's two ($C5, one bit for the
# link, validate.check_gates: the epic's $C6 stays free)
PHENDRANA_MISSILE_BIT0 = 0xC2
MISSILE_BITS = {k: PHENDRANA_MISSILE_BIT0 + n for n, k in enumerate(k for k, g in GATES.items() if MISSILE_ITEM in g.items)}
# Prime's in-room features (FEATURES) that may gate a door of their room as geometry (a GATES ledge with no Prime dock lock),
# and those whose Space Jump ledge may hold an item (an item's `needs` = {Space Jump}): the Magmoor's rule (specs/17i)
FEATURE_GEOMETRY = {"spider": frozenset({SPACE_JUMP}), "grapple": frozenset({SPACE_JUMP}), "halfpipe": frozenset({SPACE_JUMP}),
                    "bomb_slot": frozenset({MORPH_ITEM, BOMBS})}
# the event locks of the bosses' fights (specs/18h: the Sheegoth's chapel; 18k: the Thardus' cave): mapped by their child, the
# validator says which wait (validate.check_phendrana_locks_mapped); every other event lock of Phendrana is an event layer's
# (the 2nd pass' Sheegoths, the labs' ambushes, the quarantine's scenes): out (epic 18, "Fora de escopo")
BOSS_DOORS = {("phendrana_chapel_of_the_elders", "phendrana_chapel_tunnel"): "18h",
              ("phendrana_quarantine_cave", "phendrana_north_quarantine_tunnel"): "18k",
              ("phendrana_quarantine_cave", "phendrana_south_quarantine_tunnel"): "18k"}


BEAM_CAPS = ("ice", "wave", "plasma")   # specs/18h: the key caps a boss door keeps for its dead state (tallon/rooms.py LOCK_OF)


def build_rooms(regions, extra=frozenset()) -> list[RoomDef]:
    """RoomDefs of the rooms in `regions` and in `extra`, in TABLE order, with the doors between them; a link to a room left
    out is left out too (wall). specs/18c: placeholder boxes; specs/18e: a room with a layout (tools/phendrana/layouts.py) gets
    it, in its look (LOOK: smlib/ice.py, specs/18d; the snow look by default) with its background, and the falling snow
    (ice.SPORES) if Prime snows there (SNOW_ROOMS)."""
    from chozo.bosses import arena_of   # specs/18h (chozo/bosses.py imports this package's layouts)
    from chozo.rooms import BOSS_GATE
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
        tileset = LOOK.get(t.key, ice.SNOW_TILESET)
        bg, layer2 = ice.BACKGROUND[tileset]
        rooms[t.key] = RoomDef(t.key, t.prime, t.name, w, h, t.map_x, t.map_y, canvas, tileset=tileset,
                               style=STYLE_OF[tileset], library_bg=bg if isinstance(bg, int) else None, layer2=layer2,
                               snow=ice.SPORES if t.key in SNOW_ROOMS and shape else 0,
                               water=t.key in FLOODED and shape is not None,   # specs/18m: the Gravity Chamber
                               elevator=shape.elevator if shape else None,
                               skin=shape.skin if shape else [], blocks=shape.blocks if shape else [],
                               save_station=shape.save if shape else None,   # specs/18f
                               map_station=shape.map_station if shape else None,   # specs/18i
                               caps=shape.caps if shape else [])   # specs/18i
    for (ra, sa, na), (rb, sb, nb) in LINKS:
        if OPPOSITE[sa] != sb:
            raise ValueError(f"porta {ra}.{sa} liga em {rb}.{sb}: lados precisam ser opostos")
        if ra not in rooms or rb not in rooms:
            continue
        da, db = DoorLink(sa, na, rb), DoorLink(sb, nb, ra)
        gate = GATES.get(frozenset({ra, rb}))
        if gate:   # specs/18f: the Magmoor's rule (magmoor/rooms.py build_rooms): one kind of cap on its side(s), or a ledge
            caps = {LOCK_OF[i] for i in gate.items if i in LOCK_OF}
            if (len(caps) > 1 or bool(caps) != bool(gate.capped) or not set(gate.capped) <= {ra, rb}
                    or not set(gate.ledge) <= {ra, rb} or bool(gate.ledge) != bool(gate.items & GEOMETRY)):
                raise ValueError(f"trava {ra}-{rb}: precisa de um tipo de tampa e do lado dela ({gate})")
            cap = caps.pop() if caps else None
            for d, key in ((da, ra), (db, rb)):
                d.gate, d.ledge = gate.items, key in gate.ledge
                if key in gate.capped:
                    d.lock = cap
                    if cap == "missile":   # specs/18i: the red doors' bits
                        d.lock_bit = MISSILE_BITS[frozenset({ra, rb})]
        for d, key, to in ((da, ra, rb), (db, rb, ra)):
            # specs/18h: a boss door whose arena is built (tools/chozo/bosses.py ARENAS): the fight's grey cap (lock "boss",
            # the gate BOSS_GATE: the walk goes through only with the arena's `needs`), Prime's key cap of the dock (if any)
            # in the dead state (dead_lock); the Chozo's rule (chozo/rooms.py BOSS_DOORS, specs/14c), with the key lock kept
            if (key, to) in BOSS_DOORS and arena_of(key) is not None:
                if d.lock not in (None, *BEAM_CAPS):
                    raise ValueError(f"porta de chefe {key}->{to} com tampa {d.lock}")
                d.dead_lock, d.lock, d.gate = d.lock, "boss", d.gate | {BOSS_GATE}
        rooms[ra].doors.append(da)
        rooms[rb].doors.append(db)
        da.to_door = len(rooms[rb].doors) - 1
        db.to_door = len(rooms[ra].doors) - 1
    return list(rooms.values())


def region_of(key: str) -> str:
    return next(t.region for t in TABLE if t.key == key)


def check_prime(worlds_json: Path, locks_json: Path) -> list[str]:
    """TABLE and LINKS against Prime's data (every room once with its name and box, the links = Prime's door pairs), and
    DOCK_LOCKS / KEY_BEAM / FEATURES / SNOW_ROOMS / WATER_ROOMS / PLASMA_ICE / WAVE_PANELS = what research/prime_phendrana_locks.json
    gives; no room with Prime's heat ("area_damage"); the elevator lists = the TABLE's transports, each one's other side the
    Magmoor transport that names it."""
    world = next(w for w in json.loads(worlds_json.read_text()) if w["name"] == "Phendrana Drifts")
    prime = {a["index"]: a for a in world["areas"]}
    problems = []
    by_prime = {t.prime: t for t in TABLE}
    if len(by_prime) != len(TABLE) or set(by_prime) != set(prime):
        problems.append(f"phendrana: tabela tem as salas {sorted(by_prime)}, o Prime tem {sorted(prime)}")
    if len({t.key for t in TABLE}) != len(TABLE):
        problems.append("phendrana: chave de sala repetida na tabela")
    for t in TABLE:
        if t.region not in REGIONS:
            problems.append(f"{t.key}: região {t.region!r} desconhecida")
        if not t.key.startswith("phendrana_"):
            problems.append(f"{t.key}: chave sem o prefixo phendrana_")
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
        problems.append(f"phendrana: elevadores {sorted(ELEVATOR_ROOMS)} + de enfeite {sorted(DECORATIVE_ELEVATORS)}, os "
                        f"transportes do Prime são {sorted(transports)}")
    if DECORATIVE_ELEVATORS:   # epic 18, technical decision 4: both lead to the Magmoor, a world that exists
        problems.append(f"phendrana: elevadores de enfeite {sorted(DECORATIVE_ELEVATORS)}: os dois levam à Magmoor, que existe "
                        "(de verdade, decisão técnica 4 do épico 18)")
    for t in TABLE:   # the other side: the Magmoor transport that names this room (magmoor/rooms.py TRANSPORT_TO)
        if t.key in TRANSPORT_TO and MAGMOOR_TRANSPORT_TO.get(TRANSPORT_TO[t.key]) != t.key:
            problems.append(f"phendrana: {t.key} leva a {TRANSPORT_TO[t.key]}, que leva a "
                            f"{MAGMOOR_TRANSPORT_TO.get(TRANSPORT_TO[t.key])!r}")
    key_of = {t.prime: t.key for t in TABLE}
    key_prime = {t.key: t.prime for t in TABLE}
    unknown = sorted({k for a, b in LINKS for k in (a[0], b[0])} - set(key_prime))
    if unknown:
        return problems + [f"phendrana: ligações com salas fora da tabela: {unknown}"]
    ours = [frozenset((key_prime[a[0]], key_prime[b[0]])) for a, b in LINKS]
    theirs = {frozenset((a["index"], d["to_area"])) for a in world["areas"] for d in a["docks"]}
    if len(set(ours)) != len(ours) or set(ours) != theirs:
        problems.append(f"phendrana: ligações diferentes do Prime: sobram {sorted(map(sorted, set(ours) - theirs))}, "
                        f"faltam {sorted(map(sorted, theirs - set(ours)))}")
    data = json.loads(locks_json.read_text())
    want_locks, want_beam, want_features = {}, {}, {}
    want = {"neve": set(), "água": set(), "gelo de plasma": set(), "painel de onda": set(), "calor": set()}
    for i, room in data.items():
        if int(i) not in key_of:
            continue
        k = key_of[int(i)]
        for d in room["docks"]:
            kinds = prime_dock_locks(d["objects"])
            if kinds:
                want_locks[(k, key_of[d["to"]])] = kinds
            if KEY in kinds:
                vuln = tuple(d.get("key_vuln") or ())
                want_beam[(k, key_of[d["to"]])] = BEAM_OF_KEY.get(vuln, f"vulnerabilidade {vuln}")
        if room["features"]:
            want_features[k] = set(room["features"])
        for name, hit in (("neve", room.get("env_fx") == 1), ("água", "water" in room["features"]),
                          ("gelo de plasma", "plasma" in room.get("beam_only", {})),
                          ("painel de onda", "wave" in room.get("beam_only", {})), ("calor", room.get("area_damage"))):
            if hit:
                want[name].add(k)
    for k in sorted(set(want_locks) | set(DOCK_LOCKS)):
        if want_locks.get(k) != DOCK_LOCKS.get(k):
            problems.append(f"phendrana: trava da doca {k[0]} -> {k[1]}: o Prime tem {sorted(want_locks.get(k, ()))}, "
                            f"a tabela diz {sorted(DOCK_LOCKS.get(k, ()))}")
    for k in sorted(set(want_beam) | set(KEY_BEAM)):
        if want_beam.get(k) != KEY_BEAM.get(k):
            problems.append(f"phendrana: cor da porta {k[0]} -> {k[1]}: o Prime tem {want_beam.get(k)}, KEY_BEAM diz "
                            f"{KEY_BEAM.get(k)}")
    for k in sorted(set(want_features) | set(FEATURES)):
        if want_features.get(k) != FEATURES.get(k):
            problems.append(f"phendrana: {k}: o Prime tem {sorted(want_features.get(k, ()))}, "
                            f"FEATURES diz {sorted(FEATURES.get(k, ()))}")
    for name, ours_set in (("neve", SNOW_ROOMS), ("água", WATER_ROOMS), ("gelo de plasma", PLASMA_ICE),
                           ("painel de onda", WAVE_PANELS), ("calor", frozenset())):
        if want[name] != ours_set:
            problems.append(f"phendrana: salas com {name} no Prime {sorted(want[name])}, a tabela diz {sorted(ours_set)}")
    return problems


ALL_ROOMS = build_rooms(REGIONS)          # the whole world, for the validator's map checks
ROOMS = build_rooms(ACTIVE_REGIONS, ELEVATOR_ROOMS)   # what the build gets (specs/18c: nothing; specs/18e: the elevator rooms)

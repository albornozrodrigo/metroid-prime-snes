"""Phazon Mines rooms (SM area 5, specs/19b): the room graph, the map and Prime's locks (specs/19c-grafo-e-mapa-mines.md).

All 42 rooms of Prime's Phazon Mines (research/prime_worlds.json, MLVL "Phazon Mines"), one SM room per Prime room (epic 19, user
decision 1 and technical decision 1), with the Prime door graph in LINKS (43 pairs, 86 docks, all with their way back; two loops:
the upper level's ring Main Quarry -> Security Access A -> Mine Security Station -> Security Access B -> Elite Research -> Research
Access -> Ore Processing -> Waste Disposal -> Main Quarry, and the big ring of the levels below, Elite Control -> Maintenance Tunnel
-> Phazon Processing Center -> ... -> Elite Quarters -> ... -> Metroid Quarantine B -> the fungal halls -> Elevator B -> Metroid
Quarantine A -> Central Dynamo -> Omega Research -> Ventilation Shaft -> Elite Control). The size comes from the Prime box by the
Tallon's rule (tallon/rooms.py `screens`: 30 m a screen, at most 6 x 4): 205 screens.

Map: x/y in area 5's 64x32 pause-map grid. The Mines is a pit of three levels whose rings lie flat, so neither a side view nor a
top view keeps it: here each level is a band of the map, top to bottom (region A the upper level, B the middle, C the west with the
Magmoor's elevator and the Omega Pirate, D the lower level), and inside a band west to east on the map = Prime's y (south to north),
loosely, with a little of Prime's x. The sides and screens of the doors were found by a search (a discarded script, as in specs/12c,
17c and 18c: a randomized placement along the two rings, with backtracking, where each room touches every placed neighbour, pulled
toward its place in the bands, the best of many by a cost) that keeps every door touching its neighbour, few floor/ceiling doors,
none on an elevator room and an elevator room's side door on its bottom screen (its shaft is the ceiling), and the saved map small.
The validator checks the whole table (tools/validate.py check_mines) and each region alone.

Regions (epic 19, "Regiões"): A the upper level (the quarry and the security station, the Phazon Elite's Elite Research); B the
middle level (Elite Control, Omega Research, Central Dynamo, Metroid Quarantine A); C the west (the Magmoor's elevator, the Phazon
Processing Center, the Omega Pirate's Elite Quarters); D the lower level (the fungal halls, Metroid Quarantine B).

Prime's locks are recorded as data (DOCK_LOCKS, KEY_BEAM, FEATURES, PB_ONLY, WAVE_PANELS), read from Prime's objects
(research/prime_mines_locks.json, written by tools/dump_prime_locks.py); no SM item or mechanism is chosen here (the region
children, by the epic's technical decision 3). No room is hot, cold, snowy or flooded (none of it in the Mines' data: the epic's
technical decision 2; the phazon is colour only, user decision 6); check_prime checks it. No room is built (specs/19c).

Built (specs/19e): the two elevator rooms (ELEVATOR_ROOMS, drawn in tools/mines/layouts.py), dead ends until their regions (19f:
the P0's door to the Quarry Access; 19j: the P25's to the Transport Access), in the pirate base's look (smlib/mines.py, specs/19d).
specs/19f: region A (ACTIVE_REGIONS), the upper level: the P0's door opens into the Quarry Access; the Elevator Access A's door to
the Elevator A (region B) stays a wall until 19i. Prime's locks there are mapped in GATES (the coloured doors, the Waste Disposal's
Morph Ball tunnel, the Mine Security Station's Bendezium wall before the Storage Depot A); the Phazon Elite's door lock (an event
lock) waits for its fight (BOSS_DOORS, specs/19h).
specs/19i: region B, the middle level (the Elevator A down from the Elevator Access A, the Elite Control, the vent, the Omega
Research, the Map Station, the Central Dynamo and its maze, Save Station B, the Metroid Quarantine A): its coloured doors in GATES,
the Maintenance Tunnel's destructible rock a power bomb wall before its L0 (a wall until 19j; its gate waits for region C), the
Ventilation Shaft's grating and the Metroid Quarantine A's walls gate their items (items.py), the Omega Research's and the Central
Dynamo's rocks gate nothing (PB_NOTHING), the Central Dynamo's maze (MAZES) gates its missile. The Metroid Quarantine A's L1 to
the Elevator Access B (region D) stays a wall until 19l.
specs/19j: region C, the west (the P25's door opens into the Transport Access, the Phazon Processing Center, the Processing Center
Access, the Elite Quarters and its access): its ice and plasma doors in GATES; the Maintenance Tunnel's gate (19i) now applies,
so from the Magmoor's lift the way on to region B opens in round 6 only; the Phazon Processing Center's Bendezium wall gates its
missile (items.py); the Transport Access' grapple points gate nothing (a one-screen corridor: no Space Jump cliff fits; the
Space Jump is round 2's); the Elite Quarters keeps its plasma doors until its arena (19k). The Elite Quarters Access' floor door
to the Metroid Quarantine B (region D) stays a wall until 19l.
specs/19l: region D, the lower level (the Elevator Access B from the Metroid Quarantine A's L1, the Elevator B, the fungal halls,
the Phazon Mining Tunnel, the Missile Station, the Metroid Quarantine B from the Elite Quarters Access' floor door, Save Station C):
its plasma doors in GATES (the floor/ceiling ones the vertical plasma doors, tallon/beamdoors.py), the Fungal Hall A's two links
with an ice cap on its side and a plasma cap on the other (SIDE_CAPS, Prime's colours), the Phazon Mining Tunnel's bomb blocks and
Bendezium wall a Morph Ball tunnel before its ceiling door (MAZES, PB_ONLY), the Metroid Quarantine B's track and grapple point
its missile (a Space Jump column, items.py). All 42 rooms of the Mines are built.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from chozo.rooms import EVENT, KEY, MISSILE, MORPH, ONE_WAY, prime_dock_locks   # noqa: F401 (the lock kinds, as the Chozo's)
from frigate.rooms import OPPOSITE, DoorLink, RoomDef
from magmoor.rooms import BEAM_OF_VULN, TRANSPORT_TO as MAGMOOR_TRANSPORT_TO
from magmoor.rooms import TABLE as MAGMOOR_TABLE
from smlib import mines
from tallon.rooms import (BOMBS, GEOMETRY, ICE, LOCK_OF, MORPH as MORPH_ITEM, PLASMA, POWER_BOMB, SPACE_JUMP, WAVE,  # noqa: F401
                          Gate, placeholder, screens)
from tallon.rooms import TABLE as TALLON_TABLE

from .layouts import LAYOUTS

REGIONS = {
    "A": "Nível de cima: a pedreira e a segurança (Main Quarry, Mine Security Station, Elite Research)",
    "B": "Nível do meio: Elite Control, Omega Research, Central Dynamo, Metroid Quarantine A",
    "C": "Oeste: o elevador da Magmoor, o Phazon Processing Center e o Omega Pirate (Elite Quarters)",
    "D": "Nível de baixo: os fungos e a Metroid Quarantine B",
}
ACTIVE_REGIONS: frozenset[str] = frozenset({"A", "B", "C", "D"})   # specs/19c: none; 19f: A; 19i: B; 19j: C; 19l: D
# the two transports (WorldTeleporter destinations read from the bytes, epic 19): P0 to the Tallon's P43 (tallon_transport_mines_east)
# and P25 to the Magmoor's P26 (magmoor_transport_mines_west); working elevators from specs/19e (epic 19, technical decision 4)
ELEVATOR_ROOMS = frozenset({"mines_transport_tallon_south", "mines_transport_magmoor_south"})
DECORATIVE_ELEVATORS: frozenset[str] = frozenset()
TRANSPORT_TO = {"mines_transport_tallon_south": "tallon_transport_mines_east",
                "mines_transport_magmoor_south": "magmoor_transport_mines_west"}
# specs/19e: each built room's look (smlib/mines.py tileset; the pirate base unless here) and the round it is first reached in (the
# walk of the five areas: the Mines are entered only by the two lifts, each in its other side's round: the Tallon's P43 behind the
# ice doors of the Tunnel E, round 5; the Magmoor's P26 behind the ice doors of the Workstation Tunnel, round 4)
# specs/19f: region A. The rock and fungus look for the mine itself (the Quarry Access, the Main Quarry under the sky, the Waste
# Disposal's chute, the Ore Processing's hall round the ore column); the pirate base (the default) for the pirates' rooms: the
# save room, the security accesses and station, the store rooms, the Research Access, the Elevator Access A, the Elite Research
# specs/19i: region B: the rock for the Maintenance Tunnel (Prime's rock tunnel with the destructible rock); the pirate base for
# the rest (the lift, the control rooms, the vent, the research hall, the dynamo, the quarantine and the save and map rooms)
# specs/19l: region D: the rock for the fungal halls, their shaft and the mining tunnel (Prime's caverns of fungus and phazon);
# the pirate base for the quarantine, its access, the lift and its access, the save and the missile rooms
LOOK: dict[str, int] = {k: mines.ROCK_TILESET for k in ("mines_quarry_access", "mines_main_quarry", "mines_waste_disposal",
                                                         "mines_ore_processing", "mines_maintenance_tunnel",
                                                         "mines_fungal_hall_b", "mines_phazon_mining_tunnel",
                                                         "mines_fungal_hall_access", "mines_fungal_hall_a")}
# specs/19f: region A from the P0 (round 5, the Tallon's P43 over it): its doors want the Wave and the Ice (rounds 1 and 3), the
# Waste Disposal's tunnel the Morph Ball (round 0): every room in round 5 but the Storage Depot A, behind the Mine Security
# Station's power bomb blocks and plasma door (the Power Bomb and the Plasma Beam: round 5's, so round 6)
FIRST_ROUND = {"mines_transport_tallon_south": 5, "mines_transport_magmoor_south": 4,
               **{k: 5 for k in ("mines_quarry_access", "mines_main_quarry", "mines_waste_disposal", "mines_save_station_a",
                                 "mines_security_access_a", "mines_ore_processing", "mines_security_station",
                                 "mines_research_access", "mines_storage_depot_b", "mines_elevator_access_a",
                                 "mines_security_access_b", "mines_elite_research")},
               "mines_storage_depot_a": 6,
               # specs/19i: region B from the Elevator Access A (round 5): its doors want the Ice and the Wave (rounds 3 and 1):
               # every room in round 5 (the Maintenance Tunnel's power bomb wall closes only its L0, a wall until 19j)
               **{k: 5 for k in ("mines_elevator_a", "mines_elite_control_access", "mines_elite_control",
                                 "mines_maintenance_tunnel", "mines_ventilation_shaft", "mines_omega_research",
                                 "mines_map_station", "mines_dynamo_access", "mines_central_dynamo",
                                 "mines_quarantine_access_a", "mines_save_station_b", "mines_metroid_quarantine_a")},
               # specs/19j: region C from the P25 (round 4, the Magmoor's P26 over it): the Transport Access and the Phazon
               # Processing Center want the Ice (round 3); the plasma doors of the Processing Center Access and the Elite Quarters
               # (and its access) the Plasma Beam (round 5's: round 6); the Maintenance Tunnel's power bomb wall shuts the way
               # on to region B (and the Tallon) until round 6 (the epic's rule: no Magmoor <-> Tallon shortcut before it)
               # (the Maintenance Tunnel, round 5 from region B, is entered from the Phazon Processing Center in round 4: only its
               # bit between the L0 and the power bomb wall)
               **{k: 4 for k in ("mines_transport_access", "mines_phazon_processing_center", "mines_maintenance_tunnel")},
               **{k: 6 for k in ("mines_processing_center_access", "mines_elite_quarters", "mines_elite_quarters_access")},
               # specs/19l: region D. The Elevator Access B from the Metroid Quarantine A (round 5: its ice door); every other room
               # behind a plasma door (the Plasma Beam is round 5's: round 6), from the Elevator Access B's L1 or the Elite Quarters
               # Access' floor door
               "mines_elevator_access_b": 5,
               **{k: 6 for k in ("mines_metroid_quarantine_b", "mines_quarantine_access_b", "mines_save_station_c",
                                 "mines_fungal_hall_b", "mines_elevator_b", "mines_missile_station", "mines_phazon_mining_tunnel",
                                 "mines_fungal_hall_access", "mines_fungal_hall_a")}}


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
    Row("mines_transport_tallon_south", 0, "Transport to Tallon Overworld South", "A", (44, 40, 50), 32, 8),
    Row("mines_quarry_access", 1, "Quarry Access", "A", (59, 39, 46), 33, 8),
    Row("mines_main_quarry", 2, "Main Quarry", "A", (155, 148, 100), 35, 9),
    Row("mines_waste_disposal", 3, "Waste Disposal", "A", (21, 33, 33), 37, 12),
    Row("mines_save_station_a", 4, "Save Station Mines A", "A", (25, 38, 9), 34, 11),
    Row("mines_security_access_a", 5, "Security Access A", "A", (77, 33, 22), 32, 10),
    Row("mines_ore_processing", 6, "Ore Processing", "A", (72, 75, 66), 34, 12),
    Row("mines_security_station", 7, "Mine Security Station", "A", (65, 96, 29), 29, 10),
    Row("mines_research_access", 8, "Research Access", "A", (46, 23, 66), 32, 11),
    Row("mines_storage_depot_b", 9, "Storage Depot B", "A", (36, 38, 20), 37, 13),
    Row("mines_elevator_access_a", 10, "Elevator Access A", "A", (29, 44, 66), 33, 13),
    Row("mines_security_access_b", 11, "Security Access B", "A", (45, 88, 29), 29, 11),
    Row("mines_storage_depot_a", 12, "Storage Depot A", "A", (36, 38, 23), 28, 10),
    Row("mines_elite_research", 13, "Elite Research", "A", (116, 116, 68), 28, 12),
    # --- B ---
    Row("mines_elevator_a", 14, "Elevator A", "B", (39, 26, 92), 34, 14),
    Row("mines_elite_control_access", 15, "Elite Control Access", "B", (56, 54, 33), 35, 16),
    Row("mines_elite_control", 16, "Elite Control", "B", (111, 79, 74), 37, 16),
    Row("mines_maintenance_tunnel", 17, "Maintenance Tunnel", "B", (85, 69, 23), 34, 17),
    Row("mines_ventilation_shaft", 18, "Ventilation Shaft", "B", (60, 63, 26), 41, 17),
    Row("mines_omega_research", 20, "Omega Research", "B", (109, 107, 99), 43, 17),
    Row("mines_map_station", 23, "Map Station Mines", "B", (28, 19, 42), 47, 19),
    Row("mines_dynamo_access", 24, "Dynamo Access", "B", (71, 44, 22), 41, 18),
    Row("mines_central_dynamo", 27, "Central Dynamo", "B", (79, 150, 71), 36, 18),
    Row("mines_quarantine_access_a", 29, "Quarantine Access A", "B", (50, 61, 23), 41, 19),
    Row("mines_save_station_b", 30, "Save Station Mines B", "B", (23, 24, 9), 35, 18),
    Row("mines_metroid_quarantine_a", 32, "Metroid Quarantine A", "B", (135, 178, 62), 39, 20),
    # --- C ---
    Row("mines_phazon_processing_center", 19, "Phazon Processing Center", "C", (66, 106, 104), 30, 15),
    Row("mines_transport_access", 21, "Transport Access", "C", (20, 62, 22), 28, 15),
    Row("mines_processing_center_access", 22, "Processing Center Access", "C", (43, 53, 21), 28, 16),
    Row("mines_transport_magmoor_south", 25, "Transport to Magmoor Caverns South", "C", (44, 38, 77), 27, 13),
    Row("mines_elite_quarters", 26, "Elite Quarters", "C", (110, 138, 65), 23, 16),
    Row("mines_elite_quarters_access", 28, "Elite Quarters Access", "C", (57, 38, 26), 21, 17),
    # --- D ---
    Row("mines_metroid_quarantine_b", 31, "Metroid Quarantine B", "D", (186, 110, 76), 17, 18),
    Row("mines_quarantine_access_b", 33, "Quarantine Access B", "D", (52, 45, 21), 23, 19),
    Row("mines_save_station_c", 34, "Save Station Mines C", "D", (36, 38, 23), 17, 21),
    Row("mines_elevator_access_b", 35, "Elevator Access B", "D", (60, 61, 48), 37, 21),
    Row("mines_fungal_hall_b", 36, "Fungal Hall B", "D", (89, 179, 52), 25, 18),
    Row("mines_elevator_b", 37, "Elevator B", "D", (25, 37, 86), 36, 20),
    Row("mines_missile_station", 38, "Missile Station Mines", "D", (63, 44, 23), 31, 19),
    Row("mines_phazon_mining_tunnel", 39, "Phazon Mining Tunnel", "D", (55, 29, 40), 26, 20),
    Row("mines_fungal_hall_access", 40, "Fungal Hall Access", "D", (48, 53, 83), 34, 19),
    Row("mines_fungal_hall_a", 41, "Fungal Hall A", "D", (76, 170, 52), 28, 20),
]

# (room, side, screen) <-> (room, side, screen), one per Prime door pair; sides opposite (R-L, B-T)
LINKS = [
    (("mines_transport_tallon_south", "R", 1), ("mines_quarry_access", "L", 1)),
    (("mines_quarry_access", "R", 1), ("mines_main_quarry", "L", 0)),
    (("mines_main_quarry", "B", 2), ("mines_waste_disposal", "T", 0)),
    (("mines_save_station_a", "R", 0), ("mines_main_quarry", "L", 2)),
    (("mines_security_access_a", "R", 0), ("mines_main_quarry", "L", 1)),
    (("mines_ore_processing", "R", 0), ("mines_waste_disposal", "L", 0)),
    (("mines_security_station", "R", 0), ("mines_security_access_a", "L", 0)),
    (("mines_research_access", "R", 1), ("mines_ore_processing", "L", 0)),
    (("mines_ore_processing", "R", 1), ("mines_storage_depot_b", "L", 0)),
    (("mines_elevator_access_a", "R", 0), ("mines_ore_processing", "L", 1)),
    (("mines_security_station", "B", 2), ("mines_security_access_b", "T", 2)),
    (("mines_storage_depot_a", "R", 0), ("mines_security_station", "L", 0)),
    (("mines_elite_research", "R", 0), ("mines_research_access", "L", 1)),
    (("mines_elevator_access_a", "R", 1), ("mines_elevator_a", "L", 0)),
    (("mines_security_access_b", "B", 2), ("mines_elite_research", "T", 3)),
    (("mines_elevator_a", "R", 2), ("mines_elite_control_access", "L", 0)),
    (("mines_elite_control_access", "R", 0), ("mines_elite_control", "L", 0)),
    (("mines_maintenance_tunnel", "R", 0), ("mines_elite_control", "L", 1)),
    (("mines_elite_control", "R", 1), ("mines_ventilation_shaft", "L", 0)),
    (("mines_phazon_processing_center", "R", 2), ("mines_maintenance_tunnel", "L", 0)),
    (("mines_ventilation_shaft", "R", 0), ("mines_omega_research", "L", 0)),
    (("mines_transport_access", "R", 0), ("mines_phazon_processing_center", "L", 0)),
    (("mines_processing_center_access", "R", 0), ("mines_phazon_processing_center", "L", 1)),
    (("mines_omega_research", "R", 2), ("mines_map_station", "L", 0)),
    (("mines_dynamo_access", "R", 0), ("mines_omega_research", "L", 1)),
    (("mines_transport_magmoor_south", "R", 2), ("mines_transport_access", "L", 0)),
    (("mines_elite_quarters", "R", 0), ("mines_processing_center_access", "L", 0)),
    (("mines_central_dynamo", "R", 0), ("mines_dynamo_access", "L", 0)),
    (("mines_elite_quarters_access", "R", 0), ("mines_elite_quarters", "L", 1)),
    (("mines_central_dynamo", "R", 1), ("mines_quarantine_access_a", "L", 0)),
    (("mines_save_station_b", "R", 0), ("mines_central_dynamo", "L", 0)),
    (("mines_elite_quarters_access", "B", 1), ("mines_metroid_quarantine_b", "T", 5)),
    (("mines_quarantine_access_a", "B", 1), ("mines_metroid_quarantine_a", "T", 3)),
    (("mines_metroid_quarantine_b", "R", 1), ("mines_quarantine_access_b", "L", 0)),
    (("mines_metroid_quarantine_b", "B", 0), ("mines_save_station_c", "T", 0)),
    (("mines_elevator_access_b", "R", 0), ("mines_metroid_quarantine_a", "L", 1)),
    (("mines_quarantine_access_b", "R", 0), ("mines_fungal_hall_b", "L", 1)),
    (("mines_elevator_b", "R", 2), ("mines_elevator_access_b", "L", 1)),
    (("mines_fungal_hall_b", "R", 1), ("mines_missile_station", "L", 0)),
    (("mines_fungal_hall_b", "B", 2), ("mines_phazon_mining_tunnel", "T", 1)),
    (("mines_fungal_hall_access", "R", 2), ("mines_elevator_b", "L", 1)),
    (("mines_phazon_mining_tunnel", "R", 0), ("mines_fungal_hall_a", "L", 0)),
    (("mines_fungal_hall_a", "R", 1), ("mines_fungal_hall_access", "L", 2)),
]

# --- Prime's locks, as data (specs/19c) ------------------------------------------------------------------------------
# Per dock (this room, the room the door leads to): the kinds of lock Prime has there, by the Chozo's rule (chozo/rooms.py
# prime_dock_locks, on research/prime_mines_locks.json): key = "Trigger_DoorKey" without a blast shield (a coloured door: all 86
# docks of the Mines), event = "Actor Door Lock" (a door that locks during a fight or a scene: the Phazon Elite's Elite Research, the
# Omega Pirate's Elite Quarters, the Elite Pirates' Elite Control and Omega Research, the pirates' and drones' ambushes of the
# security rooms and of the Central Dynamo). No blast shield, no Morph Ball door at a dock (the Waste Disposal's are the tunnel's
# own, inside the room: FEATURES morph_door), no one-way door.
DOCK_LOCKS = {
    ("mines_transport_tallon_south", "mines_quarry_access"): {"key"},
    ("mines_quarry_access", "mines_main_quarry"): {"key"},
    ("mines_quarry_access", "mines_transport_tallon_south"): {"key"},
    ("mines_main_quarry", "mines_waste_disposal"): {"key"},
    ("mines_main_quarry", "mines_quarry_access"): {"key"},
    ("mines_main_quarry", "mines_save_station_a"): {"key"},
    ("mines_main_quarry", "mines_security_access_a"): {"key"},
    ("mines_waste_disposal", "mines_main_quarry"): {"key"},
    ("mines_waste_disposal", "mines_ore_processing"): {"key"},
    ("mines_save_station_a", "mines_main_quarry"): {"key"},
    ("mines_security_access_a", "mines_main_quarry"): {"event", "key"},
    ("mines_security_access_a", "mines_security_station"): {"event", "key"},
    ("mines_ore_processing", "mines_research_access"): {"key"},
    ("mines_ore_processing", "mines_storage_depot_b"): {"key"},
    ("mines_ore_processing", "mines_waste_disposal"): {"key"},
    ("mines_ore_processing", "mines_elevator_access_a"): {"key"},
    ("mines_security_station", "mines_security_access_a"): {"event", "key"},
    ("mines_security_station", "mines_security_access_b"): {"event", "key"},
    ("mines_security_station", "mines_storage_depot_a"): {"key"},
    ("mines_research_access", "mines_ore_processing"): {"key"},
    ("mines_research_access", "mines_elite_research"): {"key"},
    ("mines_storage_depot_b", "mines_ore_processing"): {"key"},
    ("mines_elevator_access_a", "mines_ore_processing"): {"key"},
    ("mines_elevator_access_a", "mines_elevator_a"): {"key"},
    ("mines_security_access_b", "mines_elite_research"): {"key"},
    ("mines_security_access_b", "mines_security_station"): {"key"},
    ("mines_storage_depot_a", "mines_security_station"): {"key"},
    ("mines_elite_research", "mines_research_access"): {"key"},
    ("mines_elite_research", "mines_security_access_b"): {"event", "key"},
    ("mines_elevator_a", "mines_elevator_access_a"): {"key"},
    ("mines_elevator_a", "mines_elite_control_access"): {"key"},
    ("mines_elite_control_access", "mines_elevator_a"): {"key"},
    ("mines_elite_control_access", "mines_elite_control"): {"key"},
    ("mines_elite_control", "mines_maintenance_tunnel"): {"event", "key"},
    ("mines_elite_control", "mines_elite_control_access"): {"key"},
    ("mines_elite_control", "mines_ventilation_shaft"): {"key"},
    ("mines_maintenance_tunnel", "mines_elite_control"): {"key"},
    ("mines_maintenance_tunnel", "mines_phazon_processing_center"): {"key"},
    ("mines_ventilation_shaft", "mines_omega_research"): {"key"},
    ("mines_ventilation_shaft", "mines_elite_control"): {"key"},
    ("mines_phazon_processing_center", "mines_transport_access"): {"key"},
    ("mines_phazon_processing_center", "mines_maintenance_tunnel"): {"key"},
    ("mines_phazon_processing_center", "mines_processing_center_access"): {"key"},
    ("mines_omega_research", "mines_map_station"): {"event", "key"},
    ("mines_omega_research", "mines_ventilation_shaft"): {"event", "key"},
    ("mines_omega_research", "mines_dynamo_access"): {"event", "key"},
    ("mines_transport_access", "mines_phazon_processing_center"): {"key"},
    ("mines_transport_access", "mines_transport_magmoor_south"): {"key"},
    ("mines_processing_center_access", "mines_phazon_processing_center"): {"key"},
    ("mines_processing_center_access", "mines_elite_quarters"): {"key"},
    ("mines_map_station", "mines_omega_research"): {"key"},
    ("mines_dynamo_access", "mines_central_dynamo"): {"event", "key"},
    ("mines_dynamo_access", "mines_omega_research"): {"event", "key"},
    ("mines_transport_magmoor_south", "mines_transport_access"): {"key"},
    ("mines_elite_quarters", "mines_elite_quarters_access"): {"event", "key"},
    ("mines_elite_quarters", "mines_processing_center_access"): {"event", "key"},
    ("mines_central_dynamo", "mines_dynamo_access"): {"event", "key"},
    ("mines_central_dynamo", "mines_quarantine_access_a"): {"key"},
    ("mines_central_dynamo", "mines_save_station_b"): {"event", "key"},
    ("mines_elite_quarters_access", "mines_metroid_quarantine_b"): {"key"},
    ("mines_elite_quarters_access", "mines_elite_quarters"): {"key"},
    ("mines_quarantine_access_a", "mines_central_dynamo"): {"key"},
    ("mines_quarantine_access_a", "mines_metroid_quarantine_a"): {"key"},
    ("mines_save_station_b", "mines_central_dynamo"): {"key"},
    ("mines_metroid_quarantine_b", "mines_quarantine_access_b"): {"key"},
    ("mines_metroid_quarantine_b", "mines_elite_quarters_access"): {"key"},
    ("mines_metroid_quarantine_b", "mines_save_station_c"): {"key"},
    ("mines_metroid_quarantine_a", "mines_quarantine_access_a"): {"key"},
    ("mines_metroid_quarantine_a", "mines_elevator_access_b"): {"key"},
    ("mines_quarantine_access_b", "mines_metroid_quarantine_b"): {"key"},
    ("mines_quarantine_access_b", "mines_fungal_hall_b"): {"key"},
    ("mines_save_station_c", "mines_metroid_quarantine_b"): {"key"},
    ("mines_elevator_access_b", "mines_metroid_quarantine_a"): {"key"},
    ("mines_elevator_access_b", "mines_elevator_b"): {"key"},
    ("mines_fungal_hall_b", "mines_missile_station"): {"key"},
    ("mines_fungal_hall_b", "mines_quarantine_access_b"): {"key"},
    ("mines_fungal_hall_b", "mines_phazon_mining_tunnel"): {"key"},
    ("mines_elevator_b", "mines_elevator_access_b"): {"key"},
    ("mines_elevator_b", "mines_fungal_hall_access"): {"key"},
    ("mines_missile_station", "mines_fungal_hall_b"): {"key"},
    ("mines_phazon_mining_tunnel", "mines_fungal_hall_b"): {"key"},
    ("mines_phazon_mining_tunnel", "mines_fungal_hall_a"): {"key"},
    ("mines_fungal_hall_access", "mines_fungal_hall_a"): {"key"},
    ("mines_fungal_hall_access", "mines_elevator_b"): {"key"},
    ("mines_fungal_hall_a", "mines_phazon_mining_tunnel"): {"key"},
    ("mines_fungal_hall_a", "mines_fungal_hall_access"): {"key"},
}

# The beam of each key dock, from its "Trigger_DoorKey" DamageVulnerability (research/prime_mines_locks.json "key_vuln": power,
# ice, wave, plasma; 1 = hurts, 2 = immune), magmoor/rooms.py BEAM_OF_VULN: 48 ice, 26 plasma, 12 wave. Prime's beam, not yet the
# SM mechanism (the region children).
KEY_BEAM = {
    ("mines_transport_tallon_south", "mines_quarry_access"): WAVE,
    ("mines_quarry_access", "mines_main_quarry"): WAVE,
    ("mines_quarry_access", "mines_transport_tallon_south"): WAVE,
    ("mines_main_quarry", "mines_waste_disposal"): ICE,
    ("mines_main_quarry", "mines_quarry_access"): WAVE,
    ("mines_main_quarry", "mines_save_station_a"): WAVE,
    ("mines_main_quarry", "mines_security_access_a"): ICE,
    ("mines_waste_disposal", "mines_main_quarry"): ICE,
    ("mines_waste_disposal", "mines_ore_processing"): ICE,
    ("mines_save_station_a", "mines_main_quarry"): WAVE,
    ("mines_security_access_a", "mines_main_quarry"): ICE,
    ("mines_security_access_a", "mines_security_station"): ICE,
    ("mines_ore_processing", "mines_research_access"): ICE,
    ("mines_ore_processing", "mines_storage_depot_b"): ICE,
    ("mines_ore_processing", "mines_waste_disposal"): ICE,
    ("mines_ore_processing", "mines_elevator_access_a"): ICE,
    ("mines_security_station", "mines_security_access_a"): ICE,
    ("mines_security_station", "mines_security_access_b"): WAVE,
    ("mines_security_station", "mines_storage_depot_a"): PLASMA,
    ("mines_research_access", "mines_ore_processing"): ICE,
    ("mines_research_access", "mines_elite_research"): ICE,
    ("mines_storage_depot_b", "mines_ore_processing"): ICE,
    ("mines_elevator_access_a", "mines_ore_processing"): ICE,
    ("mines_elevator_access_a", "mines_elevator_a"): ICE,
    ("mines_security_access_b", "mines_elite_research"): ICE,
    ("mines_security_access_b", "mines_security_station"): WAVE,
    ("mines_storage_depot_a", "mines_security_station"): PLASMA,
    ("mines_elite_research", "mines_research_access"): ICE,
    ("mines_elite_research", "mines_security_access_b"): ICE,
    ("mines_elevator_a", "mines_elevator_access_a"): ICE,
    ("mines_elevator_a", "mines_elite_control_access"): ICE,
    ("mines_elite_control_access", "mines_elevator_a"): ICE,
    ("mines_elite_control_access", "mines_elite_control"): WAVE,
    ("mines_elite_control", "mines_maintenance_tunnel"): ICE,
    ("mines_elite_control", "mines_elite_control_access"): WAVE,
    ("mines_elite_control", "mines_ventilation_shaft"): ICE,
    ("mines_maintenance_tunnel", "mines_elite_control"): ICE,
    ("mines_maintenance_tunnel", "mines_phazon_processing_center"): ICE,
    ("mines_ventilation_shaft", "mines_omega_research"): ICE,
    ("mines_ventilation_shaft", "mines_elite_control"): ICE,
    ("mines_phazon_processing_center", "mines_transport_access"): ICE,
    ("mines_phazon_processing_center", "mines_maintenance_tunnel"): ICE,
    ("mines_phazon_processing_center", "mines_processing_center_access"): PLASMA,
    ("mines_omega_research", "mines_map_station"): ICE,
    ("mines_omega_research", "mines_ventilation_shaft"): ICE,
    ("mines_omega_research", "mines_dynamo_access"): ICE,
    ("mines_transport_access", "mines_phazon_processing_center"): ICE,
    ("mines_transport_access", "mines_transport_magmoor_south"): ICE,
    ("mines_processing_center_access", "mines_phazon_processing_center"): PLASMA,
    ("mines_processing_center_access", "mines_elite_quarters"): PLASMA,
    ("mines_map_station", "mines_omega_research"): ICE,
    ("mines_dynamo_access", "mines_central_dynamo"): ICE,
    ("mines_dynamo_access", "mines_omega_research"): ICE,
    ("mines_transport_magmoor_south", "mines_transport_access"): ICE,
    ("mines_elite_quarters", "mines_elite_quarters_access"): PLASMA,
    ("mines_elite_quarters", "mines_processing_center_access"): PLASMA,
    ("mines_central_dynamo", "mines_dynamo_access"): ICE,
    ("mines_central_dynamo", "mines_quarantine_access_a"): ICE,
    ("mines_central_dynamo", "mines_save_station_b"): ICE,
    ("mines_elite_quarters_access", "mines_metroid_quarantine_b"): PLASMA,
    ("mines_elite_quarters_access", "mines_elite_quarters"): PLASMA,
    ("mines_quarantine_access_a", "mines_central_dynamo"): ICE,
    ("mines_quarantine_access_a", "mines_metroid_quarantine_a"): WAVE,
    ("mines_save_station_b", "mines_central_dynamo"): ICE,
    ("mines_metroid_quarantine_b", "mines_quarantine_access_b"): PLASMA,
    ("mines_metroid_quarantine_b", "mines_elite_quarters_access"): PLASMA,
    ("mines_metroid_quarantine_b", "mines_save_station_c"): PLASMA,
    ("mines_metroid_quarantine_a", "mines_quarantine_access_a"): WAVE,
    ("mines_metroid_quarantine_a", "mines_elevator_access_b"): ICE,
    ("mines_quarantine_access_b", "mines_metroid_quarantine_b"): PLASMA,
    ("mines_quarantine_access_b", "mines_fungal_hall_b"): PLASMA,
    ("mines_save_station_c", "mines_metroid_quarantine_b"): PLASMA,
    ("mines_elevator_access_b", "mines_metroid_quarantine_a"): ICE,
    ("mines_elevator_access_b", "mines_elevator_b"): PLASMA,
    ("mines_fungal_hall_b", "mines_missile_station"): PLASMA,
    ("mines_fungal_hall_b", "mines_quarantine_access_b"): PLASMA,
    ("mines_fungal_hall_b", "mines_phazon_mining_tunnel"): PLASMA,
    ("mines_elevator_b", "mines_elevator_access_b"): PLASMA,
    ("mines_elevator_b", "mines_fungal_hall_access"): PLASMA,
    ("mines_missile_station", "mines_fungal_hall_b"): PLASMA,
    ("mines_phazon_mining_tunnel", "mines_fungal_hall_b"): PLASMA,
    ("mines_phazon_mining_tunnel", "mines_fungal_hall_a"): PLASMA,
    ("mines_fungal_hall_access", "mines_fungal_hall_a"): PLASMA,
    ("mines_fungal_hall_access", "mines_elevator_b"): PLASMA,
    ("mines_fungal_hall_a", "mines_phazon_mining_tunnel"): ICE,
    ("mines_fungal_hall_a", "mines_fungal_hall_access"): ICE,
}

# In-room features of Prime that gate movement (the dumper's names: chozo/rooms.py FEATURES): spider, grapple, halfpipe, morph_door
# (the Waste Disposal's Morph Ball tunnel: its four "Door_Area Morphball" are inside the room, 15-35 m from its docks)
FEATURES = {
    "mines_main_quarry": {"grapple", "spider"},
    "mines_waste_disposal": {"morph_door"},
    "mines_ore_processing": {"grapple", "spider"},
    "mines_research_access": {"spider"},
    "mines_elevator_access_a": {"spider"},
    "mines_ventilation_shaft": {"halfpipe"},
    "mines_phazon_processing_center": {"spider"},
    "mines_transport_access": {"grapple"},
    "mines_metroid_quarantine_b": {"grapple", "spider"},
    "mines_metroid_quarantine_a": {"spider"},
}

# specs/19c: the rooms with something only the Power Bomb breaks, on Prime's layer 0 (research/prime_mines_locks.json "pb_only":
# a DamageableTrigger, Platform or Actor whose DamageVulnerability has only the power bomb's value as hurting): the Bendezium walls
# (Security Access A, Mine Security Station, Phazon Processing Center, Phazon Mining Tunnel), the destructible rocks (Maintenance
# Tunnel, Omega Research, Central Dynamo), the Ventilation Shaft's grating, the Ore Processing's platform and the Metroid Quarantine
# A's two. How many each room has. (The Elite Research's two are on event layers 1-2: the Phazon Elite's tank and a crate.)
PB_ONLY = {
    "mines_security_access_a": 1,
    "mines_ore_processing": 1,
    "mines_security_station": 1,
    "mines_maintenance_tunnel": 1,
    "mines_ventilation_shaft": 1,
    "mines_phazon_processing_center": 1,
    "mines_omega_research": 1,
    "mines_central_dynamo": 1,
    "mines_metroid_quarantine_a": 2,
    "mines_phazon_mining_tunnel": 1,
}
# the rooms with a panel only the Wave Beam hurts ("beam_only" wave; Prime's Thermal Visor shows it): the Main Quarry's
WAVE_PANELS: frozenset[str] = frozenset({"mines_main_quarry"})


# --- region A's locks in the SM (specs/19f; epic 19, technical decision 3: Prime's locks -> mechanisms that exist) -------------
# Prime's door locks in region A (DOCK_LOCKS, KEY_BEAM): every dock a coloured door = the beam door of Prime's colour on that side
# (both sides of each link: the ice doors (the Ice Beam, round 3), the wave doors (round 1), the plasma doors of the Mine Security
# Station <-> Storage Depot A link (round 5's Plasma Beam); the floor/ceiling links are the vertical ice and wave doors,
# tallon/beamdoors.py); the event locks: the Phazon Elite's of the Elite Research's ceiling door (BOSS_DOORS, its fight in specs/19h)
# and the pirates' ambushes of the security rooms (event layers: out). Prime's in-room locks of the region that gate a door, as
# geometry on that door's side (layouts.py): the Waste Disposal's Morph Ball tunnel (FEATURES morph_door) = its L0 door behind a
# 1-row tunnel (the Morph Ball); the Mine Security Station's Bendezium wall (PB_ONLY) = power bomb blocks before its L0 door to the
# Storage Depot A (the Morph Ball and the Power Bomb, as the plasma door: round 6). The Security Access A's Bendezium wall gates its
# missile (tools/mines/items.py `needs`), the Main Quarry's Spider Ball track and grapple point its missile (a Space Jump ledge);
# the Ore Processing's Spider Ball tracks, grapple point and power-bomb-only platform and the other tracks gate nothing here.
GATES = {
    **{frozenset({a, b}): Gate(frozenset({beam}), (a, b)) for a, b, beam in (
        ("mines_transport_tallon_south", "mines_quarry_access", WAVE),
        ("mines_quarry_access", "mines_main_quarry", WAVE),
        ("mines_main_quarry", "mines_save_station_a", WAVE),
        ("mines_main_quarry", "mines_security_access_a", ICE),
        ("mines_main_quarry", "mines_waste_disposal", ICE),
        ("mines_security_access_a", "mines_security_station", ICE),
        ("mines_ore_processing", "mines_research_access", ICE),
        ("mines_ore_processing", "mines_storage_depot_b", ICE),
        ("mines_ore_processing", "mines_elevator_access_a", ICE),
        ("mines_security_station", "mines_security_access_b", WAVE),
        ("mines_research_access", "mines_elite_research", ICE),
        ("mines_security_access_b", "mines_elite_research", ICE),
        # specs/19i: region B (and its link to region A); the floor/ceiling link Quarantine Access A <-> Metroid Quarantine A is
        # the vertical wave door
        ("mines_elevator_access_a", "mines_elevator_a", ICE),
        ("mines_elevator_a", "mines_elite_control_access", ICE),
        ("mines_elite_control_access", "mines_elite_control", WAVE),
        ("mines_elite_control", "mines_maintenance_tunnel", ICE),
        ("mines_elite_control", "mines_ventilation_shaft", ICE),
        ("mines_ventilation_shaft", "mines_omega_research", ICE),
        ("mines_omega_research", "mines_map_station", ICE),
        ("mines_omega_research", "mines_dynamo_access", ICE),
        ("mines_dynamo_access", "mines_central_dynamo", ICE),
        ("mines_central_dynamo", "mines_quarantine_access_a", ICE),
        ("mines_central_dynamo", "mines_save_station_b", ICE),
        ("mines_quarantine_access_a", "mines_metroid_quarantine_a", WAVE),
        # specs/19j: region C (the Elite Quarters Access' floor door to the Metroid Quarantine B, region D, waits for 19l)
        ("mines_transport_magmoor_south", "mines_transport_access", ICE),
        ("mines_transport_access", "mines_phazon_processing_center", ICE),
        ("mines_phazon_processing_center", "mines_processing_center_access", PLASMA),
        ("mines_processing_center_access", "mines_elite_quarters", PLASMA),
        ("mines_elite_quarters", "mines_elite_quarters_access", PLASMA),
        # specs/19l: region D (and its links to regions B and C); the floor/ceiling links (the Elite Quarters Access <-> Metroid
        # Quarantine B, the Metroid Quarantine B <-> Save Station C) are the vertical plasma doors
        ("mines_elite_quarters_access", "mines_metroid_quarantine_b", PLASMA),
        ("mines_metroid_quarantine_b", "mines_quarantine_access_b", PLASMA),
        ("mines_metroid_quarantine_b", "mines_save_station_c", PLASMA),
        ("mines_metroid_quarantine_a", "mines_elevator_access_b", ICE),
        ("mines_quarantine_access_b", "mines_fungal_hall_b", PLASMA),
        ("mines_elevator_b", "mines_elevator_access_b", PLASMA),
        ("mines_fungal_hall_b", "mines_missile_station", PLASMA),
        ("mines_fungal_hall_access", "mines_elevator_b", PLASMA))},
    # specs/19l: the Fungal Hall A's two links: Prime's ice cap on its side, plasma on the other (SIDE_CAPS)
    **{frozenset({a, b}): Gate(frozenset({ICE, PLASMA}), (a, b)) for a, b in (
        ("mines_phazon_mining_tunnel", "mines_fungal_hall_a"), ("mines_fungal_hall_a", "mines_fungal_hall_access"))},
    # specs/19l: the Phazon Mining Tunnel's bomb blocks and Bendezium wall (MAZES, PB_ONLY) = the 1-row tunnel to the chamber under
    # its ceiling door, a bomb block and a power bomb block in it (the Morph Ball, the Bombs and the Power Bomb on its side, with the
    # plasma doors: round 6)
    frozenset({"mines_fungal_hall_b", "mines_phazon_mining_tunnel"}): Gate(
        frozenset({PLASMA, MORPH_ITEM, BOMBS, POWER_BOMB}), ("mines_fungal_hall_b", "mines_phazon_mining_tunnel"),
        ("mines_phazon_mining_tunnel",)),
    frozenset({"mines_waste_disposal", "mines_ore_processing"}): Gate(
        frozenset({ICE, MORPH_ITEM}), ("mines_waste_disposal", "mines_ore_processing"), ("mines_waste_disposal",)),
    frozenset({"mines_security_station", "mines_storage_depot_a"}): Gate(
        frozenset({PLASMA, MORPH_ITEM, POWER_BOMB}), ("mines_security_station", "mines_storage_depot_a"),
        ("mines_security_station",)),
    # specs/19i: the Maintenance Tunnel's destructible rock (PB_ONLY) = power bomb blocks before its L0 to the Phazon Processing
    # Center (the Morph Ball and the Power Bomb on its side, with the ice doors): applied once region C is built (19j), so the
    # way Magmoor -> Tallon through the Mines opens in round 6 only (the epic's rule 1)
    frozenset({"mines_maintenance_tunnel", "mines_phazon_processing_center"}): Gate(
        frozenset({ICE, MORPH_ITEM, POWER_BOMB}), ("mines_maintenance_tunnel", "mines_phazon_processing_center"),
        ("mines_maintenance_tunnel",)),
}
# Prime's in-room features (FEATURES) that may gate a door of their room as geometry (a GATES ledge), and those whose Space Jump
# ledge may hold an item (an item's `needs` = {Space Jump}): Phendrana's rule (phendrana/rooms.py FEATURE_GEOMETRY); the Morph
# Ball door inside a room (the Waste Disposal's tunnel) and, specs/19f, what only the Power Bomb breaks (PB_ONLY: the Morph Ball and
# the Power Bomb)
FEATURE_GEOMETRY = {"spider": frozenset({SPACE_JUMP}), "grapple": frozenset({SPACE_JUMP}), "halfpipe": frozenset({SPACE_JUMP}),
                    "morph_door": frozenset({MORPH_ITEM}), "pb_only": frozenset({MORPH_ITEM, POWER_BOMB})}
# specs/19f: the rooms with something only the Power Bomb breaks (PB_ONLY) whose object gates nothing in the SM (no power bomb block
# there): the Ore Processing's platform (Prime's rubble by the ore column; the hall's ways are its zigzags)
# specs/19i: and the Omega Research's and the Central Dynamo's destructible rocks (where they stand in Prime's rooms is uncertain:
# the data give no place; the halls' ways are their zigzags and the Central Dynamo's maze is the bombs')
PB_NOTHING: frozenset[str] = frozenset({"mines_ore_processing", "mines_omega_research", "mines_central_dynamo"})
# specs/19i: Prime's Morph Ball maze of the Central Dynamo (its "DamageableTrigger Bomb" objects, which the dumper's features do
# not name): the geometry it may gate an item behind (validate.check_mines_locks_mapped: the missile in Prime's Power Bomb place)
# specs/19l: and the Phazon Mining Tunnel's bomb blocks (Prime's 17 "blocks" the bombs break: the tunnel's Morph Ball ways)
MAZES = {"mines_central_dynamo": frozenset({MORPH_ITEM, BOMBS}), "mines_phazon_mining_tunnel": frozenset({MORPH_ITEM, BOMBS})}
# specs/19l: a link whose two sides have different caps (the Chozo's rule, chozo/rooms.py SIDE_CAPS): (room, the room its door leads
# to) -> the gate item of that side's cap; that side's door gets that cap and its gate drops the other side's cap item. Prime: the
# Fungal Hall A's docks are Ice-only, the docks across from them Plasma-only (KEY_BEAM)
SIDE_CAPS = {("mines_fungal_hall_a", "mines_phazon_mining_tunnel"): ICE, ("mines_phazon_mining_tunnel", "mines_fungal_hall_a"): PLASMA,
             ("mines_fungal_hall_a", "mines_fungal_hall_access"): ICE, ("mines_fungal_hall_access", "mines_fungal_hall_a"): PLASMA}
# the event locks of the bosses' fights (epic 19, user decision 4: specs/19h the Phazon Elite's Elite Research; 19k the Omega
# Pirate's Elite Quarters): mapped by their child, the validator says which wait (validate.check_mines_locks_mapped); every other
# event lock of the Mines is an event layer's (the pirates' ambushes, the Elite Pirates, the drones): out (epic 19)
BOSS_DOORS = {("mines_elite_research", "mines_security_access_b"): "19h",
              ("mines_elite_quarters", "mines_elite_quarters_access"): "19k",
              ("mines_elite_quarters", "mines_processing_center_access"): "19k"}


def build_rooms(regions, extra=frozenset()) -> list[RoomDef]:
    """RoomDefs of the rooms in `regions` and in `extra`, in TABLE order, with the doors between them; a link to a room left out is
    left out too (wall). specs/19c: placeholder boxes; specs/19e: a room with a layout (tools/mines/layouts.py) gets it, in its look
    (LOOK: smlib/mines.py, specs/19d; the pirate base by default) with its background."""
    from chozo.bosses import arena_of   # specs/19h (chozo/bosses.py imports other areas' packages)
    from chozo.rooms import BOSS_GATE
    from phendrana.rooms import BEAM_CAPS
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
        tileset = LOOK.get(t.key, mines.BASE_TILESET)
        bg, layer2 = mines.BACKGROUND[tileset]
        rooms[t.key] = RoomDef(t.key, t.prime, t.name, w, h, t.map_x, t.map_y, canvas, tileset=tileset,
                               style=mines.STYLE_OF[tileset], library_bg=bg, layer2=layer2,
                               elevator=shape.elevator if shape else None,
                               skin=shape.skin if shape else [], blocks=shape.blocks if shape else [],   # specs/19f
                               save_station=shape.save if shape else None,
                               map_station=shape.map_station if shape else None,   # specs/19i
                               missile_station=shape.missile_station if shape else None)   # specs/19l
    for (ra, sa, na), (rb, sb, nb) in LINKS:
        if OPPOSITE[sa] != sb:
            raise ValueError(f"porta {ra}.{sa} liga em {rb}.{sb}: lados precisam ser opostos")
        if ra not in rooms or rb not in rooms:
            continue
        da, db = DoorLink(sa, na, rb), DoorLink(sb, nb, ra)
        gate = GATES.get(frozenset({ra, rb}))
        if gate:   # specs/19f: Phendrana's rule (phendrana/rooms.py build_rooms): one kind of cap on its side(s), and the ledge
            caps = {LOCK_OF[i] for i in gate.items if i in LOCK_OF}
            if (bool(caps) != bool(gate.capped) or not set(gate.capped) <= {ra, rb}
                    or not set(gate.ledge) <= {ra, rb} or bool(gate.ledge) != bool(gate.items & GEOMETRY)):
                raise ValueError(f"trava {ra}-{rb}: precisa de um tipo de tampa e do lado dela ({gate})")
            split = {key: SIDE_CAPS[(key, to)] for key, to in ((ra, rb), (rb, ra)) if (key, to) in SIDE_CAPS}
            if split:   # specs/19l: one cap kind per side (the Chozo's rule, specs/12l)
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
                    d.lock = LOCK_OF[split[key]] if key in split else cap
        for d, key, to in ((da, ra, rb), (db, rb, ra)):
            # specs/19h: a boss door whose arena is built (tools/chozo/bosses.py ARENAS): the fight's grey cap (lock "boss", the
            # gate BOSS_GATE), Prime's key cap of the dock in the dead state (dead_lock): Phendrana's rule (specs/18h)
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


def super_only(full: list[int] | None) -> bool:
    """specs/19c: a door key's whole DamageVulnerability (research/prime_mines_locks.json "key_vuln_full": 16 weaknesses, the charged
    beams' 5, the beam combos' 5) that only the Super Missile (the power beam's combo) opens: none of power, ice, wave, plasma, missile
    hurts (1, or 0 = double) and the combo does."""
    if not full:
        return False
    return full[21] in (0, 1) and all(full[i] not in (0, 1) for i in (0, 1, 2, 3, 6))


def check_prime(worlds_json: Path, locks_json: Path) -> list[str]:
    """TABLE and LINKS against Prime's data (every room once with its name and box, the links = Prime's door pairs), and
    DOCK_LOCKS / KEY_BEAM / FEATURES / PB_ONLY / WAVE_PANELS = what research/prime_mines_locks.json gives; no room with Prime's heat
    ("area_damage"), snow or rain ("env_fx"), water or plasma ice; no door only the Super Missile opens; the elevator lists = the
    TABLE's transports, each one's other side the Tallon / Magmoor transport that names the Mines (the Magmoor's TRANSPORT_TO names
    it, magmoor/rooms.py: the room key since specs/19e)."""
    world = next(w for w in json.loads(worlds_json.read_text()) if w["name"] == "Phazon Mines")
    prime = {a["index"]: a for a in world["areas"]}
    problems = []
    by_prime = {t.prime: t for t in TABLE}
    if len(by_prime) != len(TABLE) or set(by_prime) != set(prime):
        problems.append(f"mines: tabela tem as salas {sorted(by_prime)}, o Prime tem {sorted(prime)}")
    if len({t.key for t in TABLE}) != len(TABLE):
        problems.append("mines: chave de sala repetida na tabela")
    for t in TABLE:
        if t.region not in REGIONS:
            problems.append(f"{t.key}: região {t.region!r} desconhecida")
        if not t.key.startswith("mines_"):
            problems.append(f"{t.key}: chave sem o prefixo mines_")
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
        problems.append(f"mines: elevadores {sorted(ELEVATOR_ROOMS)} + de enfeite {sorted(DECORATIVE_ELEVATORS)}, os "
                        f"transportes do Prime são {sorted(transports)}")
    if DECORATIVE_ELEVATORS:   # epic 19, technical decision 4: they lead to the Tallon and the Magmoor, worlds that exist
        problems.append(f"mines: elevadores de enfeite {sorted(DECORATIVE_ELEVATORS)}: os dois levam a mundos que existem "
                        "(de verdade, decisão técnica 4 do épico 19)")
    others = {r.key: r.name for r in (*TALLON_TABLE, *MAGMOOR_TABLE)}
    for t in TABLE:   # the other side: a transport of the Tallon or the Magmoor named for the Mines
        if t.key not in TRANSPORT_TO:
            continue
        other = TRANSPORT_TO[t.key]
        if not others.get(other, "").startswith("Transport to Phazon Mines"):
            problems.append(f"mines: {t.key} leva a {other!r}, que não é um transporte da Mines no Tallon nem na Magmoor")
        if other in MAGMOOR_TRANSPORT_TO and MAGMOOR_TRANSPORT_TO[other] != t.key:   # specs/19e: the room key
            problems.append(f"mines: {t.key} leva a {other}, que leva a {MAGMOOR_TRANSPORT_TO[other]!r}")
    key_of = {t.prime: t.key for t in TABLE}
    key_prime = {t.key: t.prime for t in TABLE}
    unknown = sorted({k for a, b in LINKS for k in (a[0], b[0])} - set(key_prime))
    if unknown:
        return problems + [f"mines: ligações com salas fora da tabela: {unknown}"]
    ours = [frozenset((key_prime[a[0]], key_prime[b[0]])) for a, b in LINKS]
    theirs = {frozenset((a["index"], d["to_area"])) for a in world["areas"] for d in a["docks"]}
    if len(set(ours)) != len(ours) or set(ours) != theirs:
        problems.append(f"mines: ligações diferentes do Prime: sobram {sorted(map(sorted, set(ours) - theirs))}, "
                        f"faltam {sorted(map(sorted, theirs - set(ours)))}")
    data = json.loads(locks_json.read_text())
    want_locks, want_beam, want_features, want_pb, supers = {}, {}, {}, {}, []
    want = {"neve ou chuva": set(), "água": set(), "gelo de plasma": set(), "painel de onda": set(), "calor": set()}
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
                want_beam[(k, key_of[d["to"]])] = BEAM_OF_VULN.get(vuln, f"vulnerabilidade {vuln}")
            if super_only(d.get("key_vuln_full")):
                supers.append((k, key_of[d["to"]]))
        if room["features"]:
            want_features[k] = set(room["features"])
        n = sum(1 for *_, layer in room.get("pb_only", []) if layer == 0)
        if n:
            want_pb[k] = n
        for name, hit in (("neve ou chuva", room.get("env_fx") not in (None, 0)), ("água", "water" in room["features"]),
                          ("gelo de plasma", "plasma" in room.get("beam_only", {})),
                          ("painel de onda", "wave" in room.get("beam_only", {})), ("calor", room.get("area_damage"))):
            if hit:
                want[name].add(k)
    for k in sorted(set(want_locks) | set(DOCK_LOCKS)):
        if want_locks.get(k) != DOCK_LOCKS.get(k):
            problems.append(f"mines: trava da doca {k[0]} -> {k[1]}: o Prime tem {sorted(want_locks.get(k, ()))}, "
                            f"a tabela diz {sorted(DOCK_LOCKS.get(k, ()))}")
    for k in sorted(set(want_beam) | set(KEY_BEAM)):
        if want_beam.get(k) != KEY_BEAM.get(k):
            problems.append(f"mines: cor da porta {k[0]} -> {k[1]}: o Prime tem {want_beam.get(k)}, KEY_BEAM diz "
                            f"{KEY_BEAM.get(k)}")
    for k in sorted(set(want_features) | set(FEATURES)):
        if want_features.get(k) != FEATURES.get(k):
            problems.append(f"mines: {k}: o Prime tem {sorted(want_features.get(k, ()))}, "
                            f"FEATURES diz {sorted(FEATURES.get(k, ()))}")
    if want_pb != PB_ONLY:
        problems.append(f"mines: o que só a Power Bomb quebra (camada 0) no Prime: {want_pb}, PB_ONLY diz {PB_ONLY}")
    for name, ours_set in (("neve ou chuva", frozenset()), ("água", frozenset()), ("gelo de plasma", frozenset()),
                           ("painel de onda", WAVE_PANELS), ("calor", frozenset())):
        if want[name] != ours_set:
            problems.append(f"mines: salas com {name} no Prime {sorted(want[name])}, a tabela diz {sorted(ours_set)}")
    for k in supers:
        problems.append(f"mines: a porta {k[0]} -> {k[1]} só abre com o Super Missile no Prime (o épico conta com nenhuma)")
    return problems


ALL_ROOMS = build_rooms(REGIONS)          # the whole world, for the validator's map checks
ROOMS = build_rooms(ACTIVE_REGIONS, ELEVATOR_ROOMS)   # what the build gets (specs/19c: nothing; specs/19e: the elevator rooms)

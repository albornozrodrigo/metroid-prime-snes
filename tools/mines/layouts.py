"""Layouts of the Phazon Mines rooms (specs/19d's two looks, smlib/mines.py).

specs/19e: the two elevator rooms (Prime's P0 to the Tallon's P43 and P25 to the Magmoor's P26; tools/mines/rooms.py ELEVATOR_ROOMS),
built before their regions as finished dead ends, as specs/12e, 17e and 18e did. The Mines lie under both worlds (Prime: the
Tallon's and the Magmoor's lifts go down into it; the map of specs/19c puts each room's side door on its bottom screen, its shaft
being the ceiling), so here the elevators go up: the hall across the bottom screen (floor = the side door's ledge row), the
platform on its floor at x 128 (SHAFT_X, as every elevator of ours) and the 2-block shaft from the top row down through the rock
to the platform's row (its blocks go on air). Both in the pirate base's look (metal, the phazon-blue pipes): Prime's transport
rooms are the pirates' lifts. The doors of the table are not there yet: their walls stay shut until the neighbours are built (19f:
the Quarry Access; 19j: the Transport Access), so a region's spec only opens the wall.

specs/19f: region A, the upper level (the quarry and the security station), by the rules of the other worlds: a side door on rows
6-9 of its screen with the floor (its ledge) on row 10; a room with a floor door has its floor on that door's ledge row (13 on a
one-screen room) and the side doors a 3-row step over it (the Temple Entryway's); a ceiling door has the platform under it (row 6,
Canvas.door_gap) and a way up to it (4 rows or less); climbs of 5 rows by floating ledges in zigzag (magmoor/layouts.py zigzag), so
every door is reached on foot without the Space Jump (the validator's walk). Prime's Spider Ball tracks and grapple points are Space
Jump ledges (the Main Quarry's missile), its Morph Ball doors a 1-row tunnel (the Waste Disposal's), its Bendezium walls power bomb
blocks (tallon/layouts.py power_bomb_block: the Security Access A's missile, the Mine Security Station's way to the Storage Depot A).
"""
from __future__ import annotations

from frigate.rooms import Elevator
from magmoor.layouts import zigzag
from smlib.canvas import Canvas
from tallon.layouts import Shape, bomb_block, power_bomb_block

SHAFT_X = 7          # the shaft's left column: the platform's centre is x 128 of its screen, as the vanilla elevators


def up_elevator_room(height: int) -> Shape:
    """A 1-screen-wide elevator room `height` screens tall going up: the hall across the bottom screen (rows 3-9 of it, floor 10
    = the side door's ledge row), the shaft from the top row down to the platform on the hall's floor, two pipes hanging from
    the hall's ceiling either side of the shaft."""
    c = Canvas(1, height)
    top = (height - 1) * 16
    floor = top + 10
    c.carve(1, top + 3, 14, floor - 1)
    c.carve(SHAFT_X, 0, SHAFT_X + 1, floor)
    for x in (3, 11):
        c.fill(x, top + 3, x + 1, top + 4)
    return Shape(c, elevator=Elevator(SHAFT_X, floor, up=True))


def transport_tallon_south() -> Shape:    # P0 (1x2), door R1 -> Quarry Access (19f)
    return up_elevator_room(2)


def transport_magmoor_south() -> Shape:   # P25 (1x3), door R2 -> Transport Access (19j)
    return up_elevator_room(3)


# --- region A (specs/19f) ---------------------------------------------------------------------------------------------------
# --- P1 Quarry Access (2x2, rock) ---------------------------------------------------------------------------------------------
# Prime: a rock tunnel from the elevator (L1) down to the Main Quarry (R1). Here: a cavern over the way on row 26 (both doors'
# ledge row), a hump of rubble to jump over, two stalactites.
def quarry_access() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 8, 30, 25)
    c.fill(13, 23, 18, 25)                      # rubble
    for x0, x1, y1 in ((7, 9, 12), (21, 24, 14)):
        c.fill(x0, 8, x1, y1)                   # stalactites
    return Shape(c)


# --- P2 Main Quarry (5x3, rock) -----------------------------------------------------------------------------------------------
# Prime: the open quarry under the sky, the pirates' crane and machines in it: the Quarry Access' door (L0) high in the west, the
# Security Access A's (L1) half-way down, Save Station A's (L2) at the bottom, the Waste Disposal's floor door (B2); a missile on
# the crane, up its Spider Ball track and grapple point; a panel only the Wave Beam hurts (the Thermal Visor's: decor). Here: the
# quarry's floor on row 42 (the L2 door's ledge row), a basin round the floor door B2 (floor 45: its ledge row); the west cliff of
# two thin shelves, the L1 door's on row 26 and the L0 door's on row 10, each reached by three floating ledges in zigzag (37, 32,
# 27; 21, 16, 11); the crane tower in the east, its top (row 14) out of every jump: the Space Jump's (the Spider Ball's track and
# the grapple point) with the missile; the crane's arm and cable hanging from the sky.
MQ_FLOOR, MQ_BASIN = 42, (34, 47, 42, 44)        # the floor row; the basin's columns and rows (its floor: the door's ledge row 45)
MQ_SHELVES = (10, 26)                           # the L0 and L1 doors' shelves (columns 1-10)
MQ_ZIGZAGS = ((11, 17, (37, 32, 27)), (11, 17, (21, 16, 11)))
MQ_TOWER = (62, 67, 14)                         # the crane tower: columns, top row (to the floor)
MQ_MISSILE = (65, 13)


def main_quarry() -> Shape:
    c = Canvas(5, 3)
    c.carve(1, 1, 78, MQ_FLOOR - 1)
    x0, x1, y0, y1 = MQ_BASIN
    c.carve(x0, y0, x1, y1)
    for y in MQ_SHELVES:
        c.fill(1, y, 10, y)
    for zz in MQ_ZIGZAGS:
        zigzag(c, *zz)
    tx0, tx1, top = MQ_TOWER
    c.fill(tx0, top, tx1, MQ_FLOOR - 1)
    c.fill(tx0, top - 1, tx0, top - 1)          # the tower's broken rails, round the missile
    c.fill(tx1, top - 2, tx1, top - 1)
    c.fill(40, 1, 41, 6)                        # the crane's cable
    c.fill(36, 7, 47, 8)                        # its arm
    c.fill(28, 39, 31, MQ_FLOOR - 1)            # a boulder on the floor (3 rows: jumped over)
    return Shape(c)


# --- P3 Waste Disposal (1x1, rock) --------------------------------------------------------------------------------------------
# Prime: a chute from the Main Quarry (its ceiling door T0) down to the Ore Processing (L0), its way a Morph Ball tunnel (the four
# "Door_Area Morphball" inside the room). Here: the chute's chamber under the ceiling door (floor 10, the platform under the door
# 4 rows up) and the wall to the L0 door's alcove with a 1-row tunnel through its foot (row 9): the Morph Ball.
WD_CHAMBER = (6, 1, 13, 9)
WD_TUNNEL = (4, 5, 9)                           # columns, row


def waste_disposal() -> Shape:
    c = Canvas(1, 1)
    c.carve(*WD_CHAMBER)
    x0, x1, y = WD_TUNNEL
    c.carve(x0, y, x1, y)
    c.fill(6, 1, 7, 1)                          # the chute's lip
    return Shape(c)


# --- P4 Save Station Mines A (1x1, pirate base) --------------------------------------------------------------------------------
# Prime's save room off the Main Quarry's floor (R0). Load station 1 of area 5 (tools/areas.py MINES): Phendrana's Save Station B.
SAVE_STATION_A = (6, 13)   # (x, floor) of the save pedestal's left block


def save_station_a() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    c.fill(10, 11, 14, 12)                      # a 3-block step down from the R0 door's ledge (row 10) to the floor (13)
    return Shape(c, save=SAVE_STATION_A)


# --- P5 Security Access A (3x1, pirate base) -----------------------------------------------------------------------------------
# Prime: the corridor from the Main Quarry (R0) to the Mine Security Station (L0), a missile behind a Bendezium wall only the Power
# Bomb breaks. Here: the corridor on row 10, a niche under the floor (rows 10-12) roofed by power bomb blocks, the missile in it
# (round 6: the Power Bomb is round 5's).
SAA_NICHE = (21, 26, 10, 12)                    # columns, rows (the top row: the power bomb blocks)
SAA_MISSILE = (23, 12)


def security_access_a() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 3, 46, 9)
    x0, x1, y0, y1 = SAA_NICHE
    c.carve(x0, y0, x1, y1)
    for x in (10, 34):
        c.fill(x, 3, x + 1, 4)                  # the corridor's frames
    return Shape(c, blocks=[power_bomb_block(x, y0) for x in range(x0, x1 + 1)])


# --- P6 Ore Processing (3x2, rock) ---------------------------------------------------------------------------------------------
# Prime: the tall processing hall round the ore column (its bomb slots turn it, its Spider Ball tracks climb it; a grapple point):
# the Waste Disposal's door (R0) and the Research Access' (L0) high up, the Storage Depot B's (R1) and the Elevator Access A's (L1)
# at the bottom. Here: the floor on row 26 (R1, L1), the two doors' shelves on row 10 against the walls, each reached from the floor
# by three ledges in zigzag (21, 16, 11); the ore column hanging in the middle (to row 20: the floor passes under it).
OP_SHELVES = ((1, 8), (39, 46))
OP_ZIGZAGS = ((9, 15, (21, 16, 11)), (33, 27, (21, 16, 11)))
OP_COLUMN = (22, 25, 4, 20)


def ore_processing() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 2, 46, 25)
    for x0, x1 in OP_SHELVES:
        c.fill(x0, 10, x1, 10)
    for zz in OP_ZIGZAGS:
        zigzag(c, *zz)
    c.fill(*OP_COLUMN)
    c.fill(21, 2, 26, 3)                        # the column's top, against the roof
    return Shape(c)


# --- P7 Mine Security Station (3x1, pirate base) -------------------------------------------------------------------------------
# Prime: the pirates' security hall: the Security Access A's door (R0), the Security Access B's floor door (B2, a wave door), the
# Storage Depot A's plasma door (L0) and a Bendezium wall only the Power Bomb breaks. Here: the floor on row 13 (the floor door's
# ledge row), each side door on a 3-row step; the wall of power bomb blocks on the L0 step, in front of its door (the way to the
# Storage Depot A: the Power Bomb and the Plasma Beam, round 6); the pipes under the roof.
MSS_WALL = (6, 7, 7, 9)                         # columns, rows of the power bomb blocks (the rock over them to the roof)


def security_station() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 3, 46, 12)
    c.fill(1, 10, 8, 12)                        # the L0 door's step
    c.fill(43, 10, 46, 12)                      # the R0 door's step
    c.fill(MSS_WALL[0], 3, MSS_WALL[1], MSS_WALL[2] - 1)   # the Bendezium wall's rock over the blocks
    for x in (14, 20, 26):
        c.fill(x, 3, x + 2, 3)                  # pipes
    x0, x1, y0, y1 = MSS_WALL
    return Shape(c, blocks=[power_bomb_block(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)])


# --- P8 Research Access (2x2, pirate base) -------------------------------------------------------------------------------------
# Prime: the way from the Ore Processing (R1) to the Elite Research (L1), a Spider Ball track up its shaft (to nothing). Here: the
# hall on row 26 (both doors' ledge row) and the shaft over it.
def research_access() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 14, 30, 25)
    c.carve(11, 4, 20, 13)                      # the shaft
    c.fill(15, 4, 16, 9)                        # the track's beam
    return Shape(c)


# --- P9 Storage Depot B (1x1, pirate base) -------------------------------------------------------------------------------------
# Prime: a store room off the Ore Processing (L0) with the Grapple Beam. Here: the room on row 10, crates in the east corner, the
# SM's Grapple Beam on the floor.
SDB_GRAPPLE = (8, 9)


def storage_depot_b() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 9)
    c.fill(11, 8, 14, 9)                        # crates
    c.fill(13, 6, 14, 7)
    return Shape(c)


# --- P10 Elevator Access A (1x2, pirate base) ----------------------------------------------------------------------------------
# Prime: the shaft down from the Ore Processing (R0) to the Elevator A (R1, region B: its wall until specs/19i), a Spider Ball
# track. Here: the shaft, the floor on row 26 (the R1 door's ledge row) and three ledges in zigzag (21, 16, 11) up to the R0 door's
# shelf (row 10).
EAA_LEDGES = ((3, 8, 21), (9, 14, 16), (3, 8, 11))


def elevator_access_a() -> Shape:
    c = Canvas(1, 2)
    c.carve(1, 2, 14, 25)
    for x0, x1, y in EAA_LEDGES:
        c.fill(x0, y, x1, y)
    return Shape(c)


# --- P11 Security Access B (3x1, pirate base) ----------------------------------------------------------------------------------
# Prime: the corridor down from the Mine Security Station (its ceiling door T2) to the Elite Research (its floor door B2). Here: the
# corridor on row 13 (the floor door's ledge row), the ceiling door's platform (row 6) over the floor door, a ledge (row 9) west of
# it from the floor to the platform.
SAB_LEDGE = (29, 34, 9)


def security_access_b() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 3, 46, 12)
    x0, x1, y = SAB_LEDGE
    c.fill(x0, y, x1, y)
    for x in (8, 18):
        c.fill(x, 3, x + 1, 4)                  # the corridor's frames
    return Shape(c)


# --- P12 Storage Depot A (1x1, pirate base) ------------------------------------------------------------------------------------
# Prime: a store room behind the Mine Security Station's plasma door (R0) with the Flamethrower (no SM item: empty here). Here: the
# room on row 10, crates in the west corner.
def storage_depot_a() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 9)
    c.fill(1, 8, 4, 9)                          # crates
    c.fill(1, 6, 2, 7)
    return Shape(c)


# --- P13 Elite Research (4x2, pirate base) -------------------------------------------------------------------------------------
# Prime: the lab of the Phazon Elite (its tank; the fight: specs/19h), the Research Access' door (R0) high in the east, the
# Security Access B's ceiling door (T3); a missile. Here: the lab's floor on row 26 across the room (the arena of 19h); three
# ledges in zigzag (21, 16, 11) from the floor up to the ceiling door's platform (row 6), and from it east down onto the R0
# door's shelf (row 10; nothing under the platform: she jumps onto it from the top ledge); the empty tank hanging from the roof;
# the missile in the west corner, on foot.
ER_SHELF = (58, 62, 10)
ER_ZIGZAG = (46, 40, (21, 16, 11))
ER_MISSILE = (3, 25)


def elite_research() -> Shape:
    c = Canvas(4, 2)
    c.carve(1, 2, 62, 25)
    x0, x1, y = ER_SHELF
    c.fill(x0, y, x1, y)
    zigzag(c, *ER_ZIGZAG)
    c.fill(26, 2, 31, 5)                        # the Phazon Elite's tank
    c.fill(28, 6, 29, 7)
    return Shape(c)


# --- region B (specs/19i) ---------------------------------------------------------------------------------------------------
# The middle level, by region A's rules (a side door on rows 6-9 of its screen over its ledge row 10; a floor door's room with its
# floor on that door's ledge row; a ceiling door's platform on row 6; climbs of 5 rows by ledges in zigzag), reusing region A's
# measured shapes where Prime's room is alike: the Ore Processing's walls of zigzags (the Elite Control, the Central Dynamo), the
# Main Quarry's west cliff (the Omega Research), the Elite Research's climb to its ceiling door (the Metroid Quarantine A), the
# Security Access A's power bomb niche (the Ventilation Shaft), the Mine Security Station's power bomb wall (the Maintenance
# Tunnel, the Metroid Quarantine A), Save Station A (Save Station B) and Phendrana's map room (the Map Station).

# --- P14 Elevator A (1x3, pirate base) ------------------------------------------------------------------------------------------
# Prime: the pirates' lift from the upper level (L0, the Elevator Access A) down to the middle one (R2, the Elite Control Access):
# a platform riding a shaft inside the room (no WorldTeleporter). Here (the epic's technical decision 4: no machine): the shaft,
# the floor on row 42 (the R2 door's ledge row) and six ledges in zigzag (37 .. 12) up to the L0 door's shelf (row 10); the lift's
# platform stopped at the top, its rails along the walls.
EA_LEDGES = (3, 9, (37, 32, 27, 22, 17, 12))


def elevator_a() -> Shape:
    c = Canvas(1, 3)
    c.carve(1, 2, 14, 41)
    zigzag(c, *EA_LEDGES)
    c.fill(5, 2, 10, 3)                         # the lift's platform, stopped at the top
    for x in (1, 14):
        c.fill(x, 2, x, 4)                      # the rails' tops
    return Shape(c)


# --- P15 Elite Control Access (2x1, pirate base) ----------------------------------------------------------------------------------
# Prime: the corridor from the Elevator A (L0) to the Elite Control (R0, a wave door), two Space Pirates, a missile. Here: the
# corridor on row 10, a catwalk over it in the middle (row 6: she walks under it) with a pirate on guard (tools/mines/enemies.py:
# its laser runs along its row, 3 rows over her head, never at her height), the missile on the floor past it (on foot).
ECA_CATWALK = (12, 19, 6)                       # columns, row
ECA_MISSILE = (24, 9)


def elite_control_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 2, 30, 9)                        # a row higher than the other corridors: the pirate stands on the catwalk
    x0, x1, y = ECA_CATWALK
    c.fill(x0, y, x1, y)
    for x in (6, 25):
        c.fill(x, 2, x + 1, 3)                  # the corridor's frames
    return Shape(c)


# --- P16 Elite Control (4x2, pirate base) --------------------------------------------------------------------------------------
# Prime: the pirates' control hall (an Elite Pirate on an event layer): the Elite Control Access' wave door (L0) high in the west,
# the Maintenance Tunnel's (L1) and the Ventilation Shaft's (R1) at the bottom. Here: the floor on row 26 (L1, R1), the L0 shelf
# on row 10 reached by three ledges in zigzag (21, 16, 11): the Ore Processing's west wall; the control console hanging from the
# roof in the middle, two screens' pipes.
EC_SHELF = (1, 8)
EC_ZIGZAG = (9, 15, (21, 16, 11))


def elite_control() -> Shape:
    c = Canvas(4, 2)
    c.carve(1, 2, 62, 25)
    c.fill(EC_SHELF[0], 10, EC_SHELF[1], 10)
    zigzag(c, *EC_ZIGZAG)
    c.fill(30, 2, 37, 7)                        # the console
    c.fill(33, 8, 34, 10)
    for x in (24, 46):
        c.fill(x, 2, x + 1, 3)                  # pipes
    return Shape(c)


# --- P17 Maintenance Tunnel (3x1, rock) -----------------------------------------------------------------------------------------
# Prime: a rock tunnel from the Elite Control (R0) to the Phazon Processing Center (L0, region C: a wall until specs/19j), a
# destructible rock only the Power Bomb breaks across it. Here: the tunnel on row 10, the wall of power bomb blocks before the L0
# (the Mine Security Station's: rock over it to the roof); rubble, a stalactite.
MT_WALL = (6, 7, 7, 9)                          # columns, rows of the power bomb blocks


def maintenance_tunnel() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 3, 46, 9)
    c.fill(MT_WALL[0], 3, MT_WALL[1], MT_WALL[2] - 1)
    c.fill(20, 8, 23, 9)                        # rubble (2 rows: jumped over)
    c.fill(32, 3, 34, 5)                        # a stalactite
    x0, x1, y0, y1 = MT_WALL
    return Shape(c, blocks=[power_bomb_block(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)])


# --- P18 Ventilation Shaft (2x1, pirate base) -----------------------------------------------------------------------------------
# Prime: the vent between the Elite Control (L0) and the Omega Research (R0), Puffers in its gas, half-pipes (the Boost Ball), an
# Energy Tank behind a grating only the Power Bomb breaks (uncertain: Prime's "Platform - Grating"). Here: the vent on row 10,
# the fans in its roof; a duct under the floor (rows 10-12) roofed by power bomb blocks, the Energy Tank in it (round 6).
VS_DUCT = (14, 19, 10, 12)                      # columns, rows (the top row: the power bomb blocks)
VS_ETANK = (16, 12)


def ventilation_shaft() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    x0, x1, y0, y1 = VS_DUCT
    c.carve(x0, y0, x1, y1)
    for x in (7, 24):
        c.fill(x, 3, x + 1, 4)                  # the fans
    return Shape(c, blocks=[power_bomb_block(x, y0) for x in range(x0, x1 + 1)])


# --- P20 Omega Research (4x3, pirate base) --------------------------------------------------------------------------------------
# Prime: the Omega Pirate's research hall, three levels: the Ventilation Shaft's door (L0) at the top, the Dynamo Access' (L1) in
# the middle, the Map Station's (R2) at the bottom; a destructible rock only the Power Bomb breaks (gates nothing here:
# rooms.PB_NOTHING); an Elite Pirate on an event layer. Here: the floor on row 42 (R2), the west cliff of two shelves (the L1's on
# row 26, the L0's on row 10), each reached by three ledges in zigzag: the Main Quarry's; the research tank hanging in the east.
OR_SHELVES = (10, 26)
OR_ZIGZAGS = ((11, 17, (37, 32, 27)), (11, 17, (21, 16, 11)))


def omega_research() -> Shape:
    c = Canvas(4, 3)
    c.carve(1, 1, 62, 41)
    for y in OR_SHELVES:
        c.fill(1, y, 10, y)
    for zz in OR_ZIGZAGS:
        zigzag(c, *zz)
    c.fill(40, 1, 49, 4)                        # the tank's cap
    c.fill(41, 5, 41, 20)                       # its frame
    c.fill(48, 5, 48, 20)
    c.fill(40, 21, 49, 22)                      # its base
    return Shape(c)


# --- P23 Map Station Mines (1x1, pirate base) -----------------------------------------------------------------------------------
# Prime's map room of the Mines, off the Omega Research (L0). The SM map station (PLM $B6D3), as Phendrana's (specs/18i): Samus
# walks into its terminal from the west, standing on the floor (row 13); area 5's map station icon list is a new one (build.py).
MAP_STATION = (11, 13)


def map_station() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    c.fill(1, 11, 5, 12)                        # the step under the L0 door's ledge
    c.map_station(*MAP_STATION)
    return Shape(c, map_station=MAP_STATION)


# --- P24 Dynamo Access (2x1, pirate base) ---------------------------------------------------------------------------------------
# Prime: the corridor from the Omega Research (R0) to the Central Dynamo (L0). Here: the corridor on row 10, pipes.
def dynamo_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    for x in (9, 21):
        c.fill(x, 3, x + 1, 4)
    return Shape(c)


# --- P27 Central Dynamo (5x2, pirate base) --------------------------------------------------------------------------------------
# Prime: the dynamo's hall, the Dynamo Access' door (R0) high in the east, Save Station B's (L0) high in the west, the Quarantine
# Access A's (R1) at the bottom; a Morph Ball maze in its floor (bomb triggers; electric barriers) with the Power Bomb, a
# destructible rock only the Power Bomb breaks (gates nothing here: rooms.PB_NOTHING), drones on an event layer. Here: the floor on
# row 26, the two shelves on row 10 against the walls, each reached from the floor by three ledges in zigzag (the Ore Processing's
# walls); the maze: a pit in the floor (3 rows), from its bottom a 1-row tunnel west through a bomb block into a chamber with the
# missile (Prime's Power Bomb: the Tallon's since specs/09e, a missile here, epic 19 decision 3a: round 5, the Morph Ball and the
# Bombs); the dynamo hanging from the roof.
CD_SHELVES = ((1, 8), (71, 78))
CD_ZIGZAGS = ((9, 15, (21, 16, 11)), (65, 59, (21, 16, 11)))
CD_PIT = (38, 41, 26, 28)                       # columns, rows
CD_TUNNEL = (24, 37, 28)                        # columns, row
CD_BOMB_BLOCK = (31, 28)
CD_CHAMBER = (20, 23, 28, 28)
CD_MISSILE = (21, 28)


def central_dynamo() -> Shape:
    c = Canvas(5, 2)
    c.carve(1, 2, 78, 25)
    for x0, x1 in CD_SHELVES:
        c.fill(x0, 10, x1, 10)
    for zz in CD_ZIGZAGS:
        zigzag(c, *zz)
    x0, x1, y0, y1 = CD_PIT
    c.carve(x0, y0, x1, y1)
    x0, x1, y = CD_TUNNEL
    c.carve(x0, y, x1, y)
    x0, x1, y0, y1 = CD_CHAMBER
    c.carve(x0, y0, x1, y1)
    c.fill(36, 2, 43, 6)                        # the dynamo
    c.fill(39, 7, 40, 9)
    return Shape(c, blocks=[bomb_block(*CD_BOMB_BLOCK)])


# --- P29 Quarantine Access A (2x1, pirate base) ---------------------------------------------------------------------------------
# Prime: the way from the Central Dynamo (L0) down to the Metroid Quarantine A (its floor door B1, a wave door). Here: the floor on
# row 13 (the floor door's ledge row), the L0 door on a 3-row step; frames.
def quarantine_access_a() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 12)
    c.fill(1, 10, 8, 12)                        # the L0 door's step
    for x in (12, 18):
        c.fill(x, 3, x + 1, 4)
    return Shape(c)


# --- P30 Save Station Mines B (1x1, pirate base) --------------------------------------------------------------------------------
# Prime's save room off the Central Dynamo (R0). Load station 2 of area 5: Save Station A's room.
SAVE_STATION_B = (6, 13)


def save_station_b() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    c.fill(10, 11, 14, 12)                      # a 3-block step down from the R0 door's ledge (row 10) to the floor (13)
    return Shape(c, save=SAVE_STATION_B)


# --- P32 Metroid Quarantine A (6x2, pirate base) --------------------------------------------------------------------------------
# Prime: the Metroids' quarantine hall: the Quarantine Access A's wave door in the roof (T3), the Elevator Access B's (L1, region
# D: a wall until specs/19l) at the bottom; Spider Ball tracks, platforms only the X-Ray shows (plain here: the X-Ray is round 6's
# and nothing needs it), two "Powerbomb Wall"s and a missile, five Metroids. Here: the floor on row 26 (L1), from it three ledges
# in zigzag (21, 16, 11) up to the ceiling door's platform (row 6): the Elite Research's climb; the missile in a chamber at the
# east end behind a wall of power bomb blocks (round 6); the Spider Ball track's beam hanging in the west.
MQA_ZIGZAG = (46, 40, (21, 16, 11))
MQA_WALL = (84, 85, 23, 25)                     # columns, rows of the power bomb blocks (rock over them to the roof)
MQA_MISSILE = (90, 25)


def metroid_quarantine_a() -> Shape:
    c = Canvas(6, 2)
    c.carve(1, 2, 94, 25)
    zigzag(c, *MQA_ZIGZAG)
    x0, x1, y0, y1 = MQA_WALL
    c.fill(x0, 2, x1, y0 - 1)
    c.fill(20, 2, 21, 14)                       # the track's beam
    for x in (30, 66):
        c.fill(x, 2, x + 3, 3)                  # the tanks' caps
    return Shape(c, blocks=[power_bomb_block(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)])


# --- region C (specs/19j) ---------------------------------------------------------------------------------------------------
# --- P21 Transport Access (2x1, pirate base) -----------------------------------------------------------------------------------
# Prime: the corridor from the Magmoor's elevator (L0) to the Phazon Processing Center (R0), its way over a gap by two grapple
# points ("check for grapple beam"). Here: the corridor on row 10 (one screen high: no room for a Space Jump cliff; the Space
# Jump is round 2's either way), the two grapple points' pylons hanging from the roof (decor).
def transport_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    for x in (11, 20):
        c.fill(x, 3, x + 1, 5)                  # the grapple points' pylons
    return Shape(c)


# --- P19 Phazon Processing Center (4x3, pirate base) -------------------------------------------------------------------------
# Prime: the refinery hall, three levels: the Transport Access' door (L0) at the top, the Processing Center Access' plasma door
# (L1) in the middle, the Maintenance Tunnel's (R2) at the bottom; Spider Ball tracks down its walls, a Bendezium wall only the
# Power Bomb breaks and a missile (uncertain: behind the wall). Here: the Omega Research's hall (the floor on row 42, the west
# cliff of two shelves, the L1's on row 26 and the L0's on row 10, each reached by three ledges in zigzag), the missile in a pit
# under the floor roofed by power bomb blocks (the Security Access A's niche: round 6); the refinery vat hanging in the east.
PPC_SHELVES = (10, 26)
PPC_ZIGZAGS = ((11, 17, (37, 32, 27)), (11, 17, (21, 16, 11)))
PPC_NICHE = (30, 35, 42, 44)                    # columns, rows (the top row: the power bomb blocks)
PPC_MISSILE = (32, 44)


def phazon_processing_center() -> Shape:
    c = Canvas(4, 3)
    c.carve(1, 1, 62, 41)
    for y in PPC_SHELVES:
        c.fill(1, y, 10, y)
    for zz in PPC_ZIGZAGS:
        zigzag(c, *zz)
    c.fill(40, 1, 49, 4)                        # the vat's cap
    c.fill(41, 5, 41, 20)                       # its frame
    c.fill(48, 5, 48, 20)
    c.fill(40, 21, 49, 22)                      # its base
    x0, x1, y0, y1 = PPC_NICHE
    c.carve(x0, y0, x1, y1)
    return Shape(c, blocks=[power_bomb_block(x, y0) for x in range(x0, x1 + 1)])


# --- P22 Processing Center Access (2x1, pirate base) ---------------------------------------------------------------------------
# Prime: the corridor between the Phazon Processing Center (R0) and the Elite Quarters (L0), plasma doors both ways, an Energy
# Tank. Here: the corridor on row 10, the Energy Tank on its floor (round 6: the Plasma Beam is round 5's).
PCA_ETANK = (16, 9)


def processing_center_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    for x in (6, 25):
        c.fill(x, 3, x + 1, 4)                  # frames
    return Shape(c)


# --- P26 Elite Quarters (5x2, pirate base) -------------------------------------------------------------------------------------
# Prime: the Omega Pirate's hall (its fight: specs/19k; the lift out after it, decor), the Processing Center Access' plasma door
# (R0) high in the east, the Elite Quarters Access' (L1) at the bottom. Here: the arena's floor on row 26 across the room (L1),
# the R0 shelf on row 10 reached by three ledges in zigzag (21, 16, 11): the Elite Control's, mirrored; pipes in the roof.
EQ_SHELF = (71, 78)
EQ_ZIGZAG = (65, 59, (21, 16, 11))


def elite_quarters() -> Shape:
    c = Canvas(5, 2)
    c.carve(1, 2, 78, 25)
    c.fill(EQ_SHELF[0], 10, EQ_SHELF[1], 10)
    zigzag(c, *EQ_ZIGZAG)
    for x in (16, 32, 48):
        c.fill(x, 2, x + 1, 3)                  # pipes
    return Shape(c)


# --- P28 Elite Quarters Access (2x1, pirate base) ------------------------------------------------------------------------------
# Prime: the way from the Elite Quarters (R0) down to the Metroid Quarantine B (its floor door B1, a plasma door; region D: a
# wall until specs/19l). Here: the Quarantine Access A's, mirrored: the floor on row 13 (the floor door's ledge row), the R0
# door on a 3-row step; frames.
def elite_quarters_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 12)
    c.fill(26, 10, 30, 12)                      # the R0 door's step (specs/19l: clear of the floor door's columns 22-25)
    for x in (12, 18):
        c.fill(x, 3, x + 1, 4)
    return Shape(c)


# --- region D (specs/19l) ---------------------------------------------------------------------------------------------------
# The lower level, by the rules of regions A-C, reusing their measured shapes where Prime's room is alike: the Elite Research's
# climb to a ceiling door (the Metroid Quarantine B), the Elite Control's west wall (the Fungal Hall A) and its mirror (the Elevator
# Access B), the Elevator A's shaft (the Elevator B), the Mine Security Station's steps over a floor door (the Fungal Hall B), the
# Elite Control Access' catwalk (the Fungal Hall Access), Phendrana's/the Map Station's room (the Missile Station), Save Station A.

# --- P31 Metroid Quarantine B (6x3, pirate base) ---------------------------------------------------------------------------------
# Prime: the second quarantine hall: the Elite Quarters Access' plasma door in the roof (T5), the Quarantine Access B's (R1) half-way
# down the east wall, Save Station C's floor door (B0) in the west; Spider Ball tracks and a grapple point, a missile. Here: the
# floor on row 45 (the floor door's ledge row); the east wall's climb: three ledges in zigzag (40, 35, 30) from the floor onto the
# R1 shelf (row 26), three more (21, 16, 11) from it onto the ceiling door's platform (row 6): the Elite Research's climb; the
# missile on top of a column against the west wall, out of every jump: the Space Jump's (Prime's track and grapple point); the
# tanks' caps.
MQB_FLOOR = 45
MQB_SHELF = (84, 94, 26)                        # the R1 shelf: columns, row
MQB_ZIGZAGS = ((78, 72, (40, 35, 30)), (78, 72, (21, 16, 11)))
MQB_COLUMN = (1, 3, 33)                         # the column against the west wall: columns, top row (to the floor)
MQB_MISSILE = (2, 32)


def metroid_quarantine_b() -> Shape:
    c = Canvas(6, 3)
    c.carve(1, 2, 94, MQB_FLOOR - 1)
    x0, x1, y = MQB_SHELF
    c.fill(x0, y, x1, y)
    for zz in MQB_ZIGZAGS:
        zigzag(c, *zz)
    cx0, cx1, top = MQB_COLUMN
    c.fill(cx0, top, cx1, MQB_FLOOR - 1)
    for x in (20, 56):
        c.fill(x, 2, x + 3, 3)                  # the tanks' caps
    return Shape(c)


# --- P33 Quarantine Access B (2x1, pirate base) ----------------------------------------------------------------------------------
# Prime: the corridor from the Metroid Quarantine B (L0) to the Fungal Hall B (R0), plasma doors, three Atomic Alphas. Here: the
# corridor on row 10, frames (the orb: tools/mines/enemies.py).
def quarantine_access_b() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    for x in (7, 24):
        c.fill(x, 3, x + 1, 4)
    return Shape(c)


# --- P34 Save Station Mines C (1x1, pirate base) ---------------------------------------------------------------------------------
# Prime's save room under the Metroid Quarantine B (its ceiling door T0, a plasma door). Load station 3 of area 5. Here: the floor
# on row 13, the pedestal under the ceiling door's platform (row 6), a ledge in the east (row 10) from the floor up to it.
SAVE_STATION_C = (6, 13)
SSC_LEDGE = (12, 14, 10)


def save_station_c() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    x0, x1, y = SSC_LEDGE
    c.fill(x0, y, x1, y)
    return Shape(c, save=SAVE_STATION_C)


# --- P35 Elevator Access B (2x2, pirate base) -------------------------------------------------------------------------------------
# Prime: the way from the Metroid Quarantine A (R0, an ice door; region B) down to the Elevator B (L1, plasma), three Burrowers.
# Here: the floor on row 26 (L1), the R0 shelf on row 10 against the east wall reached by three ledges in zigzag (21, 16, 11): the
# Elite Quarters' east climb (19j), in a 2-screen room; a pipe.
EAB_SHELF = (23, 30)
EAB_ZIGZAG = (17, 11, (21, 16, 11))


def elevator_access_b() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 2, 30, 25)
    c.fill(EAB_SHELF[0], 10, EAB_SHELF[1], 10)
    zigzag(c, *EAB_ZIGZAG)
    c.fill(4, 2, 5, 3)                          # a pipe
    return Shape(c)


# --- P36 Fungal Hall B (6x2, rock) ------------------------------------------------------------------------------------------------
# Prime: the fungus cavern: the Quarantine Access B's door (L1) and the Missile Station's (R1), the Phazon Mining Tunnel's floor door
# (B2); a floor only the X-Ray shows (plain here), a missile, six Metroids. Here: the floor on row 29 (the floor door's ledge row),
# each side door on a 3-row step (the Mine Security Station's); the missile on the floor in the west, on foot; fungus columns
# hanging from the roof.
FHB_FLOOR = 29
FHB_MISSILE = (24, 28)


def fungal_hall_b() -> Shape:
    c = Canvas(6, 2)
    c.carve(1, 2, 94, FHB_FLOOR - 1)
    c.fill(1, 26, 8, FHB_FLOOR - 1)             # the L1 door's step
    c.fill(87, 26, 94, FHB_FLOOR - 1)           # the R1 door's step
    for x0, y1 in ((30, 8), (52, 12), (66, 9)):
        c.fill(x0, 2, x0 + 1, y1)               # fungus columns
    return Shape(c)


# --- P37 Elevator B (1x3, pirate base) ---------------------------------------------------------------------------------------------
# Prime: the pirates' second lift, from the middle level (R2, the Elevator Access B) down to the lower one (L1, the Fungal Hall
# Access). Here (the epic's technical decision 4: no machine): the Elevator A's shaft, the floor on row 42 (R2) and three ledges in
# zigzag (37, 32, 27) up to the L1 door's ledge (row 26); the lift's platform stopped at the top, its rails.
EB_LEDGES = (9, 3, (37, 32, 27))


def elevator_b() -> Shape:
    c = Canvas(1, 3)
    c.carve(1, 2, 14, 41)
    zigzag(c, *EB_LEDGES)
    c.fill(5, 2, 10, 3)                         # the lift's platform, stopped at the top
    for x in (1, 14):
        c.fill(x, 2, x, 4)                      # the rails' tops
    return Shape(c)


# --- P38 Missile Station Mines (2x1, pirate base) ----------------------------------------------------------------------------------
# Prime's missile recharge room off the Fungal Hall B (L0). The SM's missile refill station (PLM $B6EB: the epic's technical
# decision 6), as the vanilla refill rooms: Samus walks into it from the west, standing on the floor (row 13); a 3-row step under the
# L0 door's ledge (the Map Station's); missile racks.
MISSILE_STATION = (24, 13)


def missile_station() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 12)
    c.fill(1, 11, 5, 12)                        # the step under the L0 door's ledge
    c.refill_station(*MISSILE_STATION)
    for x in (12, 16):
        c.fill(x, 3, x + 1, 5)                  # missile racks
    return Shape(c, missile_station=MISSILE_STATION)


# --- P39 Phazon Mining Tunnel (2x1, rock) ------------------------------------------------------------------------------------------
# Prime: the mining tunnel under the Fungal Hall B (its ceiling door T1) to the Fungal Hall A (R0), Morph Ball ways shut by bomb
# blocks and a Bendezium wall only the Power Bomb breaks (PB_ONLY), an artifact (none here). Here: the tunnel on row 10 from the R0
# west; over its east end the chamber under the ceiling door (its platform, row 6, the chamber's floor), shut on the west by a
# 1-row tunnel (row 5) with a bomb block and a power bomb block; past them a ledge (row 6) over the west cavern, where the tunnel
# comes out (from the floor the jump onto that ledge is 4 rows). The ceiling door is behind the Morph Ball, the Bombs and the
# Power Bomb (rooms.GATES: round 6).
PMT_ROOF = (10, 27, 6)                          # the tunnel's roof = the chamber's floor and the ledge: columns, row
PMT_TUNNEL = (12, 17, 5)                        # the 1-row tunnel: columns, row
PMT_BOMB_BLOCK = (15, 5)
PMT_PB_BLOCK = (13, 5)


def phazon_mining_tunnel() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    c.carve(1, 1, 11, 2)                        # the west cavern's roof higher: room for the jump onto the ledge
    x0, x1, y = PMT_ROOF
    c.fill(x0, y, x1, y)
    tx0, tx1, ty = PMT_TUNNEL
    c.fill(tx0, 3, tx1, ty - 1)                 # the rock over the tunnel
    c.fill(28, 3, 30, 5)                        # the rock over the R0 door
    c.fill(4, 1, 5, 3)                          # a stalactite
    return Shape(c, blocks=[bomb_block(*PMT_BOMB_BLOCK), power_bomb_block(*PMT_PB_BLOCK)])


# --- P40 Fungal Hall Access (2x3, rock) --------------------------------------------------------------------------------------------
# Prime: the tall fungus shaft between the Fungal Hall A (L2) and the Elevator B (R2), three Atomic Alphas and a Space Pirate, a
# missile. Here: the floor on row 42 (both doors' ledge row), a catwalk over it in the middle (row 38: the pirate's, its laser never
# at her height: the Elite Control Access'), the missile on the floor past it (on foot); the shaft over them, fungus ledges.
FHAC_CATWALK = (12, 19, 38)                     # columns, row
FHAC_MISSILE = (24, 41)


def fungal_hall_access() -> Shape:
    c = Canvas(2, 3)
    c.carve(1, 2, 30, 41)
    x0, x1, y = FHAC_CATWALK
    c.fill(x0, y, x1, y)
    for x0, x1, y in ((4, 9, 14), (22, 27, 22)):
        c.fill(x0, y, x1, y)                    # fungus ledges
    return Shape(c)


# --- P41 Fungal Hall A (6x2, rock) ------------------------------------------------------------------------------------------------
# Prime: the second fungus cavern: the Phazon Mining Tunnel's door (L0) high in the west, the Fungal Hall Access' (R1) at the
# bottom; four Hunter Metroids. Here: the floor on row 26 (R1), the L0 shelf on row 10 reached by three ledges in zigzag (21, 16,
# 11): the Elite Control's west wall; fungus columns.
FHA_SHELF = (1, 8)
FHA_ZIGZAG = (9, 15, (21, 16, 11))


def fungal_hall_a() -> Shape:
    c = Canvas(6, 2)
    c.carve(1, 2, 94, 25)
    c.fill(FHA_SHELF[0], 10, FHA_SHELF[1], 10)
    zigzag(c, *FHA_ZIGZAG)
    for x0, y1 in ((36, 9), (60, 12), (78, 8)):
        c.fill(x0, 2, x0 + 1, y1)               # fungus columns
    return Shape(c)


LAYOUTS = {
    "mines_transport_tallon_south": transport_tallon_south,
    "mines_transport_magmoor_south": transport_magmoor_south,
    # specs/19f: region A
    "mines_quarry_access": quarry_access,
    "mines_main_quarry": main_quarry,
    "mines_waste_disposal": waste_disposal,
    "mines_save_station_a": save_station_a,
    "mines_security_access_a": security_access_a,
    "mines_ore_processing": ore_processing,
    "mines_security_station": security_station,
    "mines_research_access": research_access,
    "mines_storage_depot_b": storage_depot_b,
    "mines_elevator_access_a": elevator_access_a,
    "mines_security_access_b": security_access_b,
    "mines_storage_depot_a": storage_depot_a,
    "mines_elite_research": elite_research,
    # specs/19i: region B
    "mines_elevator_a": elevator_a,
    "mines_elite_control_access": elite_control_access,
    "mines_elite_control": elite_control,
    "mines_maintenance_tunnel": maintenance_tunnel,
    "mines_ventilation_shaft": ventilation_shaft,
    "mines_omega_research": omega_research,
    "mines_map_station": map_station,
    "mines_dynamo_access": dynamo_access,
    "mines_central_dynamo": central_dynamo,
    "mines_quarantine_access_a": quarantine_access_a,
    "mines_save_station_b": save_station_b,
    "mines_metroid_quarantine_a": metroid_quarantine_a,
    # specs/19j: region C
    "mines_phazon_processing_center": phazon_processing_center,
    "mines_transport_access": transport_access,
    "mines_processing_center_access": processing_center_access,
    "mines_elite_quarters": elite_quarters,
    "mines_elite_quarters_access": elite_quarters_access,
    # specs/19l: region D
    "mines_metroid_quarantine_b": metroid_quarantine_b,
    "mines_quarantine_access_b": quarantine_access_b,
    "mines_save_station_c": save_station_c,
    "mines_elevator_access_b": elevator_access_b,
    "mines_fungal_hall_b": fungal_hall_b,
    "mines_elevator_b": elevator_b,
    "mines_missile_station": missile_station,
    "mines_phazon_mining_tunnel": phazon_mining_tunnel,
    "mines_fungal_hall_access": fungal_hall_access,
    "mines_fungal_hall_a": fungal_hall_a,
}

"""Layouts of the Impact Crater rooms (specs/20e-entrada-impact.md; the crater's look: impact/style.py, specs/20d).

specs/20e: region A, the way in (impact/rooms.py REGIONS), by the rules of the other worlds (mines/layouts.py): a side door on rows
6-9 of its screen with the floor (its ledge) on row 10; every door and the platform reached on foot without the Space Jump (the
validator's walk). Prime enters the crater by the Artifact Temple's teleporter (epic 20, decision 7: it works once the Omega Pirate
is dead): here a working elevator (frigate/rooms.py Elevator) from the temple down to the Crater Entry Point, which has it going
up: the platform on the hall's floor at x 128 of its screen (SHAFT_X, as every elevator of ours) and the 2-block shaft from the top
row down through the rock to the platform's row (mines/layouts.py up_elevator_room).

specs/20f: region B, the upper crater (the Phazon Core, the Crater Missile Station, the Crater Tunnel B), by the same rules: climbs
of 5 rows by floating ledges in zigzag (magmoor/layouts.py zigzag; the Mines' Omega Research's west cliff); Prime's Missile Station
= the SM's missile refill station (Canvas.refill_station, as the Mines', specs/19l); the Tunnel B's Spider Ball track left out (the
game has no Spider Ball, epic 18): a plain tunnel.

specs/20g: region C, the descent (the Phazon Infusion Chamber, Subchambers One to Five; the section below), with the phazon that
hurts (SM's acid, ACID) in three of them.
"""
from __future__ import annotations

from frigate.rooms import Elevator
from magmoor.layouts import zigzag
from smlib.canvas import Canvas
from tallon.layouts import Shape, jagged_ceiling

SHAFT_X = 7          # the shaft's left column: the platform's centre is x 128 of its screen, as the vanilla elevators


# --- P0 Crater Entry Point (2x2) -----------------------------------------------------------------------------------------------
# Prime: the teleporter's landing pad and the crater's Save Station, a door (R1) to the Crater Tunnel A. Here: a cavern over the
# whole room, its floor on row 26 (the R1 door's ledge row) from the west wall to the door; the elevator's platform in the east
# screen (Samus comes down the shaft from the temple and goes back up), the save pedestal in the west, on the same floor, off the
# way from the platform to the door (a save station stops Samus as she walks onto it; load station 2 of area 0, tools/areas.py); a
# jagged roof and two stalactites over the hall.
ENTRY_FLOOR = 26
ENTRY_SHAFT_X = 16 + SHAFT_X     # the platform on the east screen (x 128 of it)
ENTRY_SAVE = (8, ENTRY_FLOOR)    # (x, floor) of the save pedestal's left block


def entry_point() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 6, 30, ENTRY_FLOOR - 1)
    jagged_ceiling(c, 1, 30, 3, (2, 3, 1, 0, 1, 2, 4, 3, 1, 0, 2))
    c.carve(ENTRY_SHAFT_X, 0, ENTRY_SHAFT_X + 1, ENTRY_FLOOR)   # the shaft, from the top row to the platform's (its blocks go on air)
    for x0, x1, y1 in ((4, 6, 11), (12, 14, 13)):
        c.fill(x0, 6, x1, y1)                       # stalactites (the hall keeps 12 rows under them)
    return Shape(c, save=ENTRY_SAVE, elevator=Elevator(ENTRY_SHAFT_X, ENTRY_FLOOR, up=True))


# --- P1 Crater Tunnel A (2x1) --------------------------------------------------------------------------------------------------
# Prime: a rock tunnel from the Entry Point (L0) to the Phazon Core (R0). Here: the tunnel on row 10 (both doors' ledge row), its
# roof hanging in stalactites (always 4 rows over the floor or more). The R0 door (a wall in 20e) leads to the Phazon Core since
# specs/20f.
def tunnel_a() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    jagged_ceiling(c, 5, 26, 2, (1, 2, 3, 2, 1, 0, 1, 3, 2, 0))
    return Shape(c)


# --- P2 Phazon Core (5x3) -------------------------------------------------------------------------------------------------------
# Prime: the great hall of phazon over the crater's core, three doors: the Tunnel A's (L2) at the bottom in the west, the Missile
# Station's (L1) and the Tunnel B's (R1) half-way up; 4 Fission Metroids hanging in it (impact/enemies.py). Here: the hall's floor
# on row 42 (the L2 door's ledge row); the L1 door's shelf (row 26, columns 1-10) on the west wall, reached from the floor by three
# ledges in zigzag (37, 32, 27: the Mines' Omega Research's), and its mirror on the east wall for the R1 door's shelf; a phazon
# column hanging from the roof in the middle; two rock perches high in the hall (row 12), each a Metroid's (far over the walk:
# off the camera of every door's screen, specs/18l).
PC_FLOOR = 42
PC_SHELVES = ((1, 10), (69, 78))                # the L1 and R1 doors' shelves (row 26): columns
PC_SHELF_ROW = 26
PC_ZIGZAGS = ((11, 17, (37, 32, 27)), (63, 57, (37, 32, 27)))
PC_PERCHES = ((22, 27), (52, 57))               # columns of the Metroids' perches (rows 12-13)
PC_PERCH_ROW = 12
PC_COLUMN = (38, 41, 16)                        # the phazon column: columns, its lowest row (from the roof)


def phazon_core() -> Shape:
    c = Canvas(5, 3)
    c.carve(1, 1, 78, PC_FLOOR - 1)
    jagged_ceiling(c, 1, 78, 1, (1, 2, 0, 3, 1, 0, 2, 1))
    for x0, x1 in PC_SHELVES:
        c.fill(x0, PC_SHELF_ROW, x1, PC_SHELF_ROW)
    for zz in PC_ZIGZAGS:
        zigzag(c, *zz)
    x0, x1, low = PC_COLUMN
    c.fill(x0, 1, x1, low)
    for x0, x1 in PC_PERCHES:
        c.fill(x0, PC_PERCH_ROW, x1, PC_PERCH_ROW + 1)
    return Shape(c)


# --- P3 Crater Missile Station (1x1) ------------------------------------------------------------------------------------------
# Prime: a dead end off the Phazon Core (R0) with a missile recharge station (its SpecialFunction "Missile Station", specs/20a): no
# item, a refill. Here the SM's missile refill station (PLM $B6EB, as the Mines', specs/19l: tools/mines/layouts.py
# missile_station), mirrored: Samus walks into it from the east, standing on the floor (row 13); a 3-row step under the R0 door's
# ledge; a missile rack.
MISSILE_STATION = (5, 13)


def missile_station() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    c.fill(10, 11, 14, 12)                      # the step under the R0 door's ledge
    c.refill_station(*MISSILE_STATION)
    c.fill(8, 3, 9, 5)                          # a missile rack
    return Shape(c, missile_station=MISSILE_STATION)


# --- P4 Crater Tunnel B (2x1) --------------------------------------------------------------------------------------------------
# Prime: a tunnel from the Phazon Core (L0) to the Phazon Infusion Chamber (R0), its way a Spider Ball track along the roof. Here
# (no Spider Ball, epic 18; the track left out): the tunnel on row 10 (both doors' ledge row), its roof in stalactites (always 4
# rows over the floor or more). The R0 door (a wall in 20f) leads to the Infusion Chamber since specs/20g.
def tunnel_b() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    jagged_ceiling(c, 5, 26, 2, (2, 1, 0, 1, 3, 2, 0, 1, 3, 2))
    return Shape(c)


# --- region C, the descent (specs/20g) ------------------------------------------------------------------------------------------
# Prime: from the Phazon Infusion Chamber down there is no door: the way falls room by room (the Subchambers, Metroid Prime's
# first stage, epic 20 decision 3: no fight here) to the Lair. Here by the same rules: a side door on rows 6-9 of its screen over
# its ledge row; a floor door's room with its floor on that door's ledge row (h - 3), the door with no cap (Prime's fall); a
# ceiling door's platform on row 6 (Canvas.door_gap) reached from a ledge 5 rows under it; climbs of 5 rows by ledges in zigzag,
# every door on foot without the Space Jump (the validator's walk), the way back up too. The phazon that hurts (epic 20, decision
# 4) = SM's acid (smlib/lava.py ACID_TYPE: it hurts with the Gravity Suit too; SM's lava does not), in pits off the way: its
# surface (ACID, the row under the floor's top: the walk's feet never reach it) covers the room from there down (an SM FX, BG3),
# so a room with a floor door (the Infusion Chamber, Subchambers Three and Five) can have none: the fall would go through it.
# Every pit is 2 rows deep (the lava's measured jump, specs/17d: out in one jump).


# --- P5 Phazon Infusion Chamber (3x2) -------------------------------------------------------------------------------------------
# Prime: the chamber where the crater's phazon is infused, the Tunnel B's plasma door (L0) high in the west, the way down a hole in
# its floor (no door). Here: the L0 shelf (row 10, columns 1-10), the chamber's floor on row 29 (the floor door's ledge row) with the
# hole (B1, no cap) in the middle; back up, three ledges in zigzag (24, 19, 14) from the floor to the shelf (4 rows over the top
# one); the infusion tanks hanging from the roof. No acid (the hole is the only way down).
INFUSION_FLOOR = 29
INFUSION_ZIGZAG = (11, 17, (24, 19, 14))


def infusion_chamber() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 2, 46, INFUSION_FLOOR - 1)
    jagged_ceiling(c, 1, 46, 1, (1, 0, 2, 1, 0, 3, 1, 2))
    c.fill(1, 10, 10, 10)                       # the L0 shelf
    zigzag(c, *INFUSION_ZIGZAG)
    for x in (32, 40):
        c.fill(x, 2, x + 2, 11)                 # the infusion tanks
    return Shape(c)


# --- P6 Subchamber One (4x3) ----------------------------------------------------------------------------------------------------
# Prime: the first chamber of the fall (Metroid Prime's first stage: decision 3, no fight), the Infusion Chamber's hole in its roof
# (T2), the Subchamber Two's way (L2) at the bottom in the west. Here: the floor on row 42 (the L2 door's ledge row); the ceiling
# door's platform (row 6) and, west of it, seven ledges in zigzag (37 .. 7) from the floor up to it; a pool of phazon in the floor
# at the east end, off the way (Samus lands from the platform west of it and walks west).
SUB1_FLOOR = 42
SUB1_ZIGZAG = (30, 24, (37, 32, 27, 22, 17, 12, 7))
SUB1_POOL = (51, 57)                            # columns of the pool (rows: the floor's and 2 under it)


def subchamber_one() -> Shape:
    c = Canvas(4, 3)
    c.carve(1, 2, 62, SUB1_FLOOR - 1)
    jagged_ceiling(c, 1, 22, 1, (0, 1, 2, 1))
    jagged_ceiling(c, 46, 62, 1, (2, 1, 0, 3, 2))
    zigzag(c, *SUB1_ZIGZAG)
    x0, x1 = SUB1_POOL
    c.carve(x0, SUB1_FLOOR, x1, SUB1_FLOOR + 2)
    c.fill(54, 2, 55, 16)                       # a phazon column hanging over the pool
    return Shape(c)


# --- P7 Subchamber Two (4x2) ----------------------------------------------------------------------------------------------------
# Prime: the second chamber, from the Subchamber One (R0, high in the east) down to the Subchamber Three (L1). Here: the R0 shelf
# (row 10, columns 53-62), the floor on row 26 (the L1 door's ledge row); back up, three ledges in zigzag (21, 16, 11) from the
# floor to the shelf (the Phazon Core's east climb, 16 rows higher); a pool of phazon under the shelf, against the east wall.
SUB2_FLOOR = 26
SUB2_ZIGZAG = (47, 41, (21, 16, 11))
SUB2_POOL = (55, 61)


def subchamber_two() -> Shape:
    c = Canvas(4, 2)
    c.carve(1, 2, 62, SUB2_FLOOR - 1)
    jagged_ceiling(c, 1, 38, 1, (1, 2, 0, 1, 3, 1))
    c.fill(53, 10, 62, 10)                      # the R0 shelf
    zigzag(c, *SUB2_ZIGZAG)
    x0, x1 = SUB2_POOL
    c.carve(x0, SUB2_FLOOR, x1, SUB2_FLOOR + 2)
    c.fill(20, 2, 21, 12)                       # a phazon column
    return Shape(c)


# --- P8 Subchamber Three (4x2) --------------------------------------------------------------------------------------------------
# Prime: the third chamber, from the Subchamber Two (R0, high in the east) down a hole in its floor (B1, no door) to the Subchamber
# Four. Here: the R0 shelf (row 10), the floor on row 29 (the floor door's ledge row) with the hole; back up, three ledges in
# zigzag (24, 19, 14) to the shelf (4 rows over the top one). No acid (the hole is the only way down).
SUB3_FLOOR = 29
SUB3_ZIGZAG = (47, 41, (24, 19, 14))


def subchamber_three() -> Shape:
    c = Canvas(4, 2)
    c.carve(1, 2, 62, SUB3_FLOOR - 1)
    jagged_ceiling(c, 1, 36, 1, (2, 0, 1, 3, 1, 0))
    c.fill(53, 10, 62, 10)                      # the R0 shelf
    zigzag(c, *SUB3_ZIGZAG)
    c.fill(8, 2, 9, 13)                         # a phazon column
    return Shape(c)


# --- P9 Subchamber Four (4x2) ---------------------------------------------------------------------------------------------------
# Prime: the fourth chamber, the Subchamber Three's hole in its roof (T0, in the west), the Subchamber Five's way (R1) at the
# bottom in the east. Here: the floor on row 26 (the R1 door's ledge row); the ceiling door's platform (row 6) and, east of it,
# three ledges in zigzag (21, 16, 11) from the floor up to it (the Mines' Elite Research's climb, mirrored); a pool of phazon in the
# floor under the platform, against the west wall (Samus lands on the platform and walks east).
SUB4_FLOOR = 26
SUB4_ZIGZAG = (12, 18, (21, 16, 11))
SUB4_POOL = (3, 9)


def subchamber_four() -> Shape:
    c = Canvas(4, 2)
    c.carve(1, 2, 62, SUB4_FLOOR - 1)
    jagged_ceiling(c, 26, 62, 1, (1, 0, 2, 3, 1, 2, 0))
    zigzag(c, *SUB4_ZIGZAG)
    x0, x1 = SUB4_POOL
    c.carve(x0, SUB4_FLOOR, x1, SUB4_FLOOR + 2)
    c.fill(40, 2, 41, 13)                       # a phazon column
    return Shape(c)


# --- P10 Subchamber Five (2x4) --------------------------------------------------------------------------------------------------
# Prime: the last chamber, a shaft from the Subchamber Four (L0, at the top in the west) down a hole in its floor (B0, no door) to
# the Metroid Prime Lair (region D: a wall until specs/20h). Here: the L0 shelf (row 10, columns 1-13), the shaft's floor on row 61
# (the floor door's ledge row); back up, ten ledges in zigzag (56 .. 11) from the floor to the shelf. No acid (the hole is the way
# down).
SUB5_FLOOR = 61
SUB5_ZIGZAG = (14, 20, tuple(range(56, 10, -5)))


def subchamber_five() -> Shape:
    c = Canvas(2, 4)
    c.carve(1, 2, 30, SUB5_FLOOR - 1)
    jagged_ceiling(c, 14, 30, 1, (1, 2, 0, 1))
    c.fill(1, 10, 13, 10)                       # the L0 shelf
    zigzag(c, *SUB5_ZIGZAG)
    return Shape(c)


# --- region D, the Metroid Prime Lair (specs/20h) ------------------------------------------------------------------------------
# --- P11 Metroid Prime Lair (4x4) -----------------------------------------------------------------------------------------------
# Prime: the bottom of the fall, the Subchamber Five's hole in its roof (T1, no door), Metroid Prime's second stage and its phazon
# pool. Here: Metroid Prime's arena (tools/chozo/bosses.py ARENAS: the Bomb Torizo's copy, which stands at the Torizo's one spot,
# (776, 368): column 48 on the floor of row 26, specs/19k) in the top half: the hall from row 2 to the floor on row 26 from wall
# to wall, the ceiling door's platform (row 6) and, west of it, three ledges in zigzag (21, 16, 11) from the floor up to it (the
# Subchamber Four's climb, mirrored), so the floor east of the climb is the fight's, clear up to the roof; the bottom half rock (the
# Torizo's spot fixes the floor's row). Samus lands on the platform, drops to the floor, fights; the door back up is shut until
# the win (impact/rooms.py BOSS_DOORS). Phazon columns hang over the climb, away from the fight.
LAIR_FLOOR = 26
LAIR_ZIGZAG = (14, 8, (21, 16, 11))


def lair() -> Shape:
    c = Canvas(4, 4)
    c.carve(1, 2, 62, LAIR_FLOOR - 1)
    jagged_ceiling(c, 30, 62, 1, (1, 0, 2, 1, 0, 1, 2, 0))
    zigzag(c, *LAIR_ZIGZAG)
    for x in (4, 30):
        c.fill(x, 2, x + 1, 8)                  # phazon columns
    return Shape(c)


LAYOUTS = {
    "impact_entry_point": entry_point,
    "impact_tunnel_a": tunnel_a,
    "impact_phazon_core": phazon_core,
    "impact_missile_station": missile_station,
    "impact_tunnel_b": tunnel_b,
    "impact_infusion_chamber": infusion_chamber,
    "impact_subchamber_one": subchamber_one,
    "impact_subchamber_two": subchamber_two,
    "impact_subchamber_three": subchamber_three,
    "impact_subchamber_four": subchamber_four,
    "impact_subchamber_five": subchamber_five,
    "impact_lair": lair,                        # specs/20h
}

# specs/20g: the surface row of each room's acid (the phazon that hurts: RoomDef.acid), the row under its floor's top
ACID = {
    "impact_subchamber_one": SUB1_FLOOR + 1,
    "impact_subchamber_two": SUB2_FLOOR + 1,
    "impact_subchamber_four": SUB4_FLOOR + 1,
}

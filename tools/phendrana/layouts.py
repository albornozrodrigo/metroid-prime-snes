"""Layouts of the Phendrana Drifts rooms (specs/18d's three looks, smlib/ice.py).

specs/18e: the two elevator rooms (Prime's P0 to the Magmoor's P13 and P29 to its P27; tools/phendrana/rooms.py ELEVATOR_ROOMS),
built before their regions as finished dead ends, as specs/12e and 17e did: Phendrana is over the Magmoor (the Magmoor's lifts go
up to it), so here the elevator goes down: its platform on the floor of a hall across the bottom screens (rows 19-25, floor 26 =
the ledge row of the doors on that screen) and its 2-block shaft from under the platform down to the room's last row, at x 128 of
the west screen (SHAFT_X, as every elevator of ours). The doors of the table are not there yet: their walls stay shut until the
neighbours are built (18f: the Shoreline Entrance; 18j: the South Quarantine Tunnel and the Transport Access), so a region's
spec only opens the wall. The P29's R0 door is on its top screen (specs/18c): the shaft goes down from the bottom screen's floor
and never crosses the top screen, so the region C child only has to draw the way up to it.
"""
from __future__ import annotations

from frigate.rooms import Elevator
from magmoor.layouts import zigzag
from smlib.canvas import Canvas
from tallon.layouts import Shape, bomb_block, power_bomb_block

SHAFT_X = 7          # the shaft's left column: the platform's centre is x 128 of its screen, as the vanilla elevators
HALL = (1, 19, 30, 25)   # the hall across the two bottom screens of a 2x2 elevator room
PLATFORM_ROW = 26


def down_elevator_room() -> Shape:
    """A 2x2 elevator room going down: the hall across the bottom screens, the platform on its floor under the shaft."""
    c = Canvas(2, 2)
    c.carve(*HALL)
    c.carve(SHAFT_X, PLATFORM_ROW, SHAFT_X + 1, 31)   # the platform's row too: its blocks go on air
    return Shape(c, elevator=Elevator(SHAFT_X, PLATFORM_ROW, up=False))


def transport_magmoor_west() -> Shape:    # P0 (2x2), door R1 -> Shoreline Entrance (18f)
    return down_elevator_room()


# specs/18j: the P29's way up to its R0 door (the Transport Access, the top screen's east wall): the east half of the top screen
# opened down into the hall, three ledges in zigzag from the hall's floor (21, 16, 11) and the R0 door's shelf (row 10) against
# the east wall, a step over the zigzag's top ledge
P29_UP = (11, 2, 30, HALL[1] - 1)                # the top screen's opened part (columns, rows) down to the hall's ceiling
P29_ZIGZAG = (19, 13, (21, 16, 11))
P29_SHELF = (25, 30, 10)


def transport_magmoor_south() -> Shape:   # P29 (2x2), doors L1 <- South Quarantine Tunnel, R0 -> Transport Access (18j)
    shape = down_elevator_room()
    c = shape.canvas
    c.carve(*P29_UP)
    zigzag(c, *P29_ZIGZAG)
    x0, x1, y = P29_SHELF
    c.fill(x0, y, x1, y)
    for x in (14, 22):
        c.fill(x, 2, x + 1, 4)                   # broken lintels hanging from the roof (the icy ruins)
    return shape


# --- region A (specs/18f) ---------------------------------------------------------------------------------------------------
# --- P1 Shoreline Entrance (4x1) ------------------------------------------------------------------------------------------
# Prime: a snowy path from the elevator (L0) down to the Shorelines (R0). Here: the path on row 10 (both doors' ledge row) under
# the open sky, two drifts of snow (2 rows and 1 row) to jump over, icicles from the rock above.
SHORELINE_DRIFTS = ((14, 21, 8), (36, 45, 9))   # (x0, x1, top row)


def shoreline_entrance() -> Shape:
    c = Canvas(4, 1)
    c.carve(1, 1, 62, 9)
    for x0, x1, top in SHORELINE_DRIFTS:
        c.fill(x0, top, x1, 9)
    for x in (8, 29, 52):
        c.fill(x, 1, x + 1, 2)                  # icicles
    return Shape(c)


# --- P2 Phendrana Shorelines (6x2) --------------------------------------------------------------------------------------------
# Prime: a wide frozen shore under cliffs: the way in from the Shoreline Entrance (L1) at the beach, Save Station B's door (L0)
# and the Temple Entryway's (T0, Prime's path up to the Ice Temple) on the west cliff, the Ruins Entryway's (R0) on the east
# cliff, the Plaza Walkway's (R1) at the east end of the beach, the Ice Ruins Access' (B4) down in the ice; a ruined tower with a
# Spider Ball track up to a missile, another missile on the frozen lake. Here: the beach on row 26 (the L1 and R1 doors' ledge
# row) under the sky; the west cliff (rows 10-21, the L0 shelf on top, the T0 door's platform over it) climbed from the beach by
# three floating ledges 5 rows apart (zigzag); in the east an overhang of ice (rows 10-12, the R0 shelf on top) over the basin
# round the B4 door (floor 29: the floor door's ledge row) and the way to the R1 door, its rock to the wall over the R1 door's
# passage, climbed by three ledges west of the basin; the ruined tower in the middle, its top (row 9) out of every jump: the
# Space Jump's (the Spider Ball's track); a hole in the frozen lake (2 rows) with the other missile.
SHORE_WEST_CLIFF = (1, 14)
SHORE_OVERHANG, SHORE_EAST_ROCK = (64, 94, 10, 12), (81, 94, 13, 21)   # columns, rows
SHORE_WEST, SHORE_EAST = (15, 21, (21, 16, 11)), (58, 52, (21, 16, 11))
SHORE_TOWER = (36, 43, 9, 21)                   # columns, top row, bottom row (the arch under it: rows 22-25)
SHORE_HOLE = (28, 31, 27)                       # the frozen lake's hole: columns, its bottom row
SHORE_BASIN = (64, 79, 26, 28)                  # columns, rows (its floor: the door's ledge row 29)
SHORE_TOWER_MISSILE = (40, 8)
SHORE_LAKE_MISSILE = (29, 27)


def shorelines() -> Shape:
    c = Canvas(6, 2)
    c.carve(1, 1, 94, 25)
    c.fill(SHORE_WEST_CLIFF[0], 10, SHORE_WEST_CLIFF[1], 21)
    for x0, x1, y0, y1 in (SHORE_OVERHANG, SHORE_EAST_ROCK):
        c.fill(x0, y0, x1, y1)
    zigzag(c, *SHORE_WEST)
    zigzag(c, *SHORE_EAST)
    x0, x1, top, bottom = SHORE_TOWER
    c.fill(x0, top, x1, bottom)
    c.fill(x0, top - 1, x0, top - 1)            # the parapet's stumps, round the missile
    c.fill(x1, top - 2, x1, top - 1)
    hx0, hx1, hb = SHORE_HOLE
    c.carve(hx0, 26, hx1, hb)
    bx0, bx1, by0, by1 = SHORE_BASIN
    c.carve(bx0, by0, bx1, by1)
    return Shape(c)


# --- P3 Temple Entryway (3x1) ----------------------------------------------------------------------------------------------
# Prime: a corridor up from the Shorelines (B0) to the Chozo Ice Temple (L0). Here: the corridor on row 13 (the floor door's
# ledge row) with the L0 door's ledge a 3-row step over it (the Chozo's Nursery Access), ruined columns hanging from the roof.
def temple_entryway() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 3, 46, 12)
    c.fill(1, 10, 5, 12)                        # the step under the L0 door's ledge
    for x in (18, 30, 42):
        c.fill(x, 3, x + 1, 5)
    return Shape(c)


# --- P4 Save Station B (1x1) -------------------------------------------------------------------------------------------------
# Prime's save room off the Shorelines' west cliff (R0). Load station 1 of area 4 (tools/areas.py PHENDRANA): the Magmoor's Save
# Station A mirrored.
SAVE_STATION_B = (6, 13)   # (x, floor) of the save pedestal's left block


def save_station_b() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    c.fill(10, 11, 14, 12)                      # a 3-block step down from the R0 door's ledge (row 10) to the floor (13)
    return Shape(c, save=SAVE_STATION_B)


# --- P5 Ruins Entryway (3x2) -------------------------------------------------------------------------------------------------
# Prime: the snowy way from the Shorelines (L1, at the beach) up to the Ice Ruins West (R0, region B). Here: the floor on row 26,
# the east cliff (top row 10: the R0 door's shelf, its wall until specs/18i) climbed by three ledges in zigzag.
RUINS_ENTRY_CLIFF = 33
RUINS_ENTRY_ZIGZAG = (27, 21, (21, 16, 11))


def ruins_entryway() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 1, 46, 25)
    c.fill(RUINS_ENTRY_CLIFF, 10, 46, 25)
    zigzag(c, *RUINS_ENTRY_ZIGZAG)
    for x in (6, 16):
        c.fill(x, 1, x + 1, 3)                  # icicles
    return Shape(c)


# --- P6 Plaza Walkway (4x1) --------------------------------------------------------------------------------------------------
# Prime: a walkway from the Shorelines (L0) over the Ice Ruins East (its floor door B1). Here: the walkway on row 13 (the floor
# door's ledge row), the L0 door's ledge a 3-row step over it.
def plaza_walkway() -> Shape:
    c = Canvas(4, 1)
    c.carve(1, 3, 62, 12)
    c.fill(1, 10, 5, 12)
    for x in (12, 36, 48):
        c.fill(x, 3, x + 1, 4)                  # the walkway's ribs
    return Shape(c)


# --- P7 Ice Ruins Access (3x1) -------------------------------------------------------------------------------------------------
# Prime: a passage from the Shorelines' ice (its ceiling door T0) to the Ice Ruins East (R0). Here: the passage on row 10, the
# ceiling door's platform (row 6) in the west.
def ice_ruins_access() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 2, 46, 9)
    for x in (22, 34):
        c.fill(x, 2, x + 1, 3)
    return Shape(c)


# --- P10 Ice Ruins East (3x2) --------------------------------------------------------------------------------------------------
# Prime: the eastern ruins, entered from the Plaza Walkway (its ceiling door T0) and the Ice Ruins Access (L0); a missile at the
# top of a Spider Ball track, another in a block of ice. Here: the west block (top row 10: the L0 door's shelf and the T0 door's
# platform over it) down to the ruins' floor (row 26) by three ledges in zigzag; a ruined tower against the east wall, its top
# (row 9) out of every jump: the Space Jump's (the Spider Ball's track); an ice niche in the foot of the west block (the missile
# in the ice).
RUINS_EAST_BLOCK = 14
RUINS_EAST_ZIGZAG = (15, 21, (21, 16, 11))
RUINS_EAST_TOWER = (36, 9)                      # the tower's west column and top row (to the east wall)
RUINS_EAST_NICHE = (10, 23)                     # the niche's west column and top row (to the block's east face, the floor)
RUINS_EAST_TOWER_MISSILE = (41, 8)
RUINS_EAST_NICHE_MISSILE = (11, 25)


def ice_ruins_east() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 1, 46, 25)
    c.fill(1, 10, RUINS_EAST_BLOCK, 25)
    zigzag(c, *RUINS_EAST_ZIGZAG)
    x, top = RUINS_EAST_TOWER
    c.fill(x, top, 46, 25)
    c.fill(x, top - 2, x, top - 1)              # the tower's broken parapet
    nx, ny = RUINS_EAST_NICHE
    c.carve(nx, ny, RUINS_EAST_BLOCK, 25)
    return Shape(c)


# --- P8 Chozo Ice Temple (5x2) ---------------------------------------------------------------------------------------------------
# Prime: the temple's hall, the Chozo statue at its west end with the bomb slot in its hand, the Temple Entryway's door (R1) at
# the floor in the east, the Chapel Tunnel's (R0) high in the east behind ice the statue's flame melts. Here: the hall's floor on
# row 26 (the R1 door's ledge row), the statue against the west wall (a dais of rock and the figure on it), the east cliff (rows
# 10-21, the R1 door's passage under it) climbed by three ledges in zigzag to a shelf on row 10, and on it the R0 door's chamber
# behind an ice wall with a 1-row tunnel through its foot, shut by a bomb block (the bomb slot: the Morph Ball and the Bombs).
TEMPLE_CLIFF = 66
TEMPLE_ZIGZAG = (60, 54, (21, 16, 11))
TEMPLE_WALL = (68, 71)                          # the ice wall's columns (rows 2-8; its tunnel on row 9)
TEMPLE_BOMB = (69, 9)


def chozo_ice_temple() -> Shape:
    c = Canvas(5, 2)
    c.carve(1, 2, 78, 25)
    c.fill(1, 20, 12, 25)                       # the statue's dais
    c.fill(3, 8, 9, 19)                         # the figure
    c.fill(10, 12, 14, 13)                      # its arm, held out east (the bomb slot's hand)
    c.fill(TEMPLE_CLIFF, 10, 78, 21)
    zigzag(c, *TEMPLE_ZIGZAG)
    c.fill(TEMPLE_WALL[0], 2, TEMPLE_WALL[1], 8)
    for x in (30, 44):
        c.fill(x, 2, x + 2, 4)                  # the roof's beams
    return Shape(c, blocks=[bomb_block(*TEMPLE_BOMB)])


# --- P11 Chapel Tunnel (2x1) -------------------------------------------------------------------------------------------------------
# Prime: a short tunnel from the Ice Temple (L0) to the Chapel of the Elders (R0), its ice blocks shot by any beam (decor here).
def chapel_tunnel() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    c.fill(14, 3, 17, 4)
    return Shape(c)


# --- P14 Chapel of the Elders (4x1) ---------------------------------------------------------------------------------------------------
# Prime: the Sheegoth's chapel (its fight: specs/18h), its only door (L0) a Wave Beam door from inside. Here: the nave on row 10,
# the altar (a 2-row dais) at the east end, columns hanging from the roof. specs/18h: the arena as it was (the nave is flat and
# 8 rows high: room for the Dessgeega's leaps under the roof); the prize (the missile where Prime has the Wave Beam) appears on
# the altar's middle when the fight is won (tools/chozo/bosses.py ARENAS)
CHAPEL_ALTAR_MISSILE = (58, 7)


def chapel_of_the_elders() -> Shape:
    c = Canvas(4, 1)
    c.carve(1, 2, 62, 9)
    c.fill(54, 8, 62, 9)                        # the altar
    for x in (16, 30, 44):
        c.fill(x, 2, x + 1, 4)
    return Shape(c)


# --- region B (specs/18i) -------------------------------------------------------------------------------------------------
# The rooms with two side doors on one wall a screen apart (the Ice Ruins West's L0/L1, the Ruined Courtyard's L0/L1 and R0/R1)
# use the Shorelines' west cliff: rock on rows 10-21 against the wall (the upper door's shelf on top, the lower door's passage
# under it), climbed from the floor (row 26) by three ledges in zigzag; the niches of Prime's in-room locks are cut into that
# cliff's face at the first ledge's height (Samus stands on the ledge, feet row 20, in front of them).
WEST_CLIFF = 14                                  # the west cliff's last column (from column 1)
WEST_ZIGZAG = (15, 21, (21, 16, 11))             # its ledges: columns 15-20 (rows 21, 11) and 21-26 (row 16)
NICHE_TOP = 17                                   # a niche in the cliff's face: rows 17-20, its floor the cliff's row 21


def west_cliff(c: Canvas) -> None:
    c.fill(1, 10, WEST_CLIFF, 21)
    zigzag(c, *WEST_ZIGZAG)


# --- P9 Ice Ruins West (4x2) ---------------------------------------------------------------------------------------------------
# Prime: the snowy western ruins, entered from the Ruins Entryway (L1, at the ground); the Canyon Entryway's door (L0) high in the
# west behind a missile shield on this side, the Courtyard Entryway's (R1) a wave door on this side at the ground in the east;
# a Power Bomb Expansion in a block of ice only the Plasma Beam melts (Prime's "_Iceblockpickup", plasma-only). Here: the
# ground on row 26 (L1 and R1), the west cliff (WEST_CLIFF: the L0 shelf, the L1 passage under it) climbed by the zigzag; the
# expansion in a niche in the cliff's face shut by a plasma door cap (the epic's technical decision 3: Prime's plasma ice = a
# niche shut by a plasma cap; RoomDef.caps), in front of the first ledge; ruined Chozo columns hang from the snowy heights.
IRW_NICHE = (10, NICHE_TOP)                      # the niche: columns 10-13, rows 17-20
IRW_CAP = (WEST_CLIFF, NICHE_TOP, "L", "plasma")   # the cap in the cliff's face: shot from the east, as a left wall's door
IRW_PB = (11, 20)


def ice_ruins_west() -> Shape:
    c = Canvas(4, 2)
    c.carve(1, 1, 62, 25)
    west_cliff(c)
    nx, ny = IRW_NICHE
    c.carve(nx, ny, WEST_CLIFF, ny + 3)          # the niche and the cap's 4 blocks (the PLM draws the cap on them)
    for x in (30, 44):
        c.fill(x, 1, x + 1, 12)                  # ruined columns hanging from the heights
    c.fill(29, 13, 32, 13)
    c.fill(43, 13, 46, 13)
    for x in (22, 38, 54):
        c.fill(x, 1, x, 3)                       # icicles
    return Shape(c, caps=[IRW_CAP])


# --- P12 Courtyard Entryway (3x1) ------------------------------------------------------------------------------------------------
# Prime: a Chozo passage from the Ice Ruins West (L0) to the Ruined Courtyard (R0). Here: the passage on row 10 (both doors' ledge
# row), broken lintels hanging from the roof.
def courtyard_entryway() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 2, 46, 9)
    for x in (14, 32):
        c.fill(x, 2, x + 2, 3)
    return Shape(c)


# --- P13 Canyon Entryway (3x1) --------------------------------------------------------------------------------------------------
# Prime: the passage from the Ice Ruins West (R0) up to the Phendrana Canyon (its ceiling door T0). Here: the Ice Ruins Access'
# shape: the passage on row 10, the ceiling door's platform (row 6) in the west.
def canyon_entryway() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 2, 46, 9)
    for x in (22, 34):
        c.fill(x, 2, x + 1, 3)
    return Shape(c)


# --- P16 Phendrana Canyon (6x3) --------------------------------------------------------------------------------------------------
# Prime: a deep snowy canyon, a dead end over the Canyon Entryway (its floor door B5), the Boost Ball on floating platforms in a
# half-pipe (nothing there here: the epic's user decision 3). Here: the canyon's floor on row 45 (the floor door's ledge row),
# rock walls stepping in from both sides, floating ice platforms over the floor in two zigzags (Prime's), spires from the roof.
CANYON_FLOOR = 45


def phendrana_canyon() -> Shape:
    c = Canvas(6, 3)
    c.carve(1, 1, 94, CANYON_FLOOR - 1)
    c.fill(1, 30, 6, CANYON_FLOOR - 1)           # the west wall's foot
    c.fill(1, 14, 3, 29)
    zigzag(c, 30, 36, (40, 35, 30))              # the floating platforms
    zigzag(c, 56, 62, (40, 35, 30))
    for x, bottom in ((20, 10), (46, 8), (72, 12)):
        c.fill(x, 1, x + 2, bottom)              # spires from the roof
    return Shape(c)


# --- P15 Ruined Courtyard (5x2) --------------------------------------------------------------------------------------------------
# Prime: the great snowy courtyard of the ruins, its doors high and low on both sides: the Courtyard Entryway (L0) and the
# Quarantine Access (L1) in the west, the Specimen Storage (R0, wave on both sides) and Save Station A (R1, a missile shield on
# this side) in the east; a dry pool in the middle (its water, Prime's bomb slot puzzle, is dry here: the user's decision 5); an
# Energy Tank Prime reaches with the bomb slot. Here: the floor on row 26 (L1, R1), the west cliff and its zigzag (the L0 shelf)
# and the Ice Temple's east cliff and zigzag (the R0 shelf, the R1 passage under it); the dry pool a 2-row dip in the floor; the
# Energy Tank in a chamber in the west cliff behind a 1-row tunnel shut by a bomb block in the cliff's face (the bomb slot: the
# Morph Ball and the Bombs, the Ice Temple's way, specs/18f).
COURT_EAST_CLIFF = 66
COURT_EAST_ZIGZAG = (60, 54, (21, 16, 11))
COURT_CHAMBER = (4, 9)                           # the Energy Tank's chamber: columns 4-9, rows 17-20 (its floor the cliff's 21)
COURT_TUNNEL_ROW = 20                            # the 1-row tunnel to the cliff's face (columns 10-14), its roof rows 17-19
COURT_BOMB = (WEST_CLIFF, COURT_TUNNEL_ROW)
COURT_ETANK = (6, 20)
COURT_POOL = (30, 49)                            # the dry pool's columns (rows 26-27)


def ruined_courtyard() -> Shape:
    c = Canvas(5, 2)
    c.carve(1, 1, 78, 25)
    west_cliff(c)
    c.fill(COURT_EAST_CLIFF, 10, 78, 21)
    zigzag(c, *COURT_EAST_ZIGZAG)
    x0, x1 = COURT_CHAMBER
    c.carve(x0, NICHE_TOP, x1, COURT_TUNNEL_ROW)
    c.carve(x1 + 1, COURT_TUNNEL_ROW, WEST_CLIFF, COURT_TUNNEL_ROW)
    c.carve(COURT_POOL[0], 26, COURT_POOL[1], 27)
    for x in (34, 44):
        c.fill(x, 1, x + 1, 9)                   # broken columns of the courtyard's arcade
    return Shape(c, blocks=[bomb_block(*COURT_BOMB)])


# --- P17 Save Station A (1x1) -----------------------------------------------------------------------------------------------------
# Prime's save room off the Ruined Courtyard (L0, the missile shield on the courtyard's side; snow falls there in Prime). Load
# station 2 of area 4 (tools/areas.py PHENDRANA): the Magmoor's Save Station A.
SAVE_STATION_A = (8, 13)


def save_station_a() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    c.fill(1, 11, 5, 12)                         # a 3-block step down from the L0 door's ledge (row 10) to the floor (13)
    return Shape(c, save=SAVE_STATION_A)


# --- P18 Specimen Storage (2x1) ---------------------------------------------------------------------------------------------------
# Prime: the pirates' storage between the Ruined Courtyard (L0) and the Research Entrance (R0), wave doors on both sides. Here: the
# hall on row 10, specimen tanks hanging from the roof.
def specimen_storage() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 2, 30, 9)
    for x in (10, 20):
        c.fill(x, 2, x + 1, 4)
    return Shape(c)


# --- P19 Quarantine Access (2x1) ---------------------------------------------------------------------------------------------------
# Prime: a passage from the Ruined Courtyard (R0) down to the North Quarantine Tunnel (its floor door B0, region C: a door since
# specs/18j, no cap on this side: only Prime's event lock). Here: the floor on row 13 (the floor door's ledge row), the R0 door's ledge a 3-row step over it.
def quarantine_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 12)
    c.fill(26, 11, 30, 12)                       # the step under the R0 door's ledge
    c.fill(14, 3, 16, 5)
    return Shape(c)


# --- P20 Research Entrance (3x1) --------------------------------------------------------------------------------------------------
# Prime: the labs' entrance hall: the Specimen Storage's door (L0), the Map Station's (R0), the Hydra Lab Entryway's up in the
# roof (T1); wave doors on the specimen and Hydra sides. Here: the hall on row 10, the ceiling door's platform (row 6) in the
# middle screen.
def research_entrance() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 2, 46, 9)
    for x in (10, 36):
        c.fill(x, 2, x + 1, 4)                   # the lab's light fittings
    return Shape(c)


# --- P22 Map Station (1x1) ----------------------------------------------------------------------------------------------------------
# Prime's map room of Phendrana, off the Research Entrance (L0). The SM map station (PLM $B6D3, as the Chozo's, specs/12i,
# mirrored): Samus walks into its terminal from the west, standing on the floor (row 13).
MAP_STATION = (11, 13)


def map_station() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    c.fill(1, 11, 5, 12)                         # the step under the L0 door's ledge
    c.map_station(*MAP_STATION)
    return Shape(c, map_station=MAP_STATION)


# --- P23 Hydra Lab Entryway (3x1) -------------------------------------------------------------------------------------------------
# Prime: the corridor from the Research Entrance (its floor door B0) to the Research Lab Hydra (R0), wave doors on both sides of
# both. Here: the corridor on row 13 (the floor door's ledge row), the R0 door's ledge a 3-row step over it.
def hydra_lab_entryway() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 3, 46, 12)
    c.fill(42, 11, 46, 12)                       # the step under the R0 door's ledge
    for x in (20, 32):
        c.fill(x, 3, x + 1, 5)
    return Shape(c)


# --- P25 Research Lab Hydra (2x2) -------------------------------------------------------------------------------------------------
# Prime: a two-storey lab, the Hydra Lab Entryway's door (L0) and the Observatory Access' (R0, region D: a door since specs/18l)
# on the upper floor, Metroids in glass tubes, a Missile Expansion. Here: the upper floor two slabs on row 10 (the doors' ledge
# row) over a gap, the lower lab under them (floor 26) climbed back by three ledges in zigzag up through the gap; the missile in
# the lower lab's west corner; the tubes' bases hang from the slabs.
HYDRA_GAP = (10, 23)                             # the gap between the slabs (columns)
HYDRA_ZIGZAG = (11, 17, (21, 16, 11))
HYDRA_MISSILE = (3, 25)


def research_lab_hydra() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 1, 30, 25)
    c.fill(1, 10, HYDRA_GAP[0] - 1, 10)
    c.fill(HYDRA_GAP[1] + 1, 10, 30, 10)
    zigzag(c, *HYDRA_ZIGZAG)
    c.fill(5, 11, 6, 12)                         # the tubes' bases under the slabs
    c.fill(27, 11, 28, 12)
    return Shape(c)


# --- region C (specs/18j) -------------------------------------------------------------------------------------------------
# --- P21 North Quarantine Tunnel (6x4) -------------------------------------------------------------------------------------
# Prime: a long snowy ravine winding down from the Quarantine Access (its ceiling door T4, a wave door on this side) to the
# Quarantine Cave (R3, wave doors on both sides). Here: a switchback trail: terraces of snowy rock 5 rows apart, each from a wall
# to the middle of the room (west ones to NQT_SPLIT - 1, east ones from NQT_SPLIT), alternating sides, so Samus walks off each
# one onto the next and climbs back at the split as on a zigzag; the ceiling door's platform (row 6) over the top terrace; at the
# foot a 2-row step (row 56) and the floor (row 58: the R3 door's ledge row); a wedge of rock under each terrace at its wall.
NQT_SPLIT = 47
NQT_TERRACES = (11, 16, 21, 26, 31, 36, 41, 46, 51)   # the first (row 11) from the east wall, then alternating
NQT_STEP = 56
NQT_FLOOR = 58


def north_quarantine_tunnel() -> Shape:
    c = Canvas(6, 4)
    c.carve(1, 2, 94, NQT_FLOOR - 1)
    for k, y in enumerate(NQT_TERRACES):
        east = k % 2 == 0
        x0, x1 = (NQT_SPLIT, 94) if east else (1, NQT_SPLIT - 1)
        c.fill(x0, y, x1, y)
        wall = 94 if east else 1                 # the wedge under it at its wall
        for dy, w in ((1, 6), (2, 3)):
            c.fill(min(wall, wall - (w - 1) * (1 if east else -1)), y + dy, max(wall, wall - (w - 1) * (1 if east else -1)),
                   y + dy)
    c.fill(1, NQT_STEP, NQT_SPLIT - 1, NQT_FLOOR - 1)
    for x in (12, 30, 86):
        c.fill(x, 2, x + 1, 4)                   # icicles
    return Shape(c)


# --- P24 Quarantine Cave (6x2) ---------------------------------------------------------------------------------------------
# Prime: the snowy cave where the Thardus wakes (its fight: specs/18k), the North Quarantine Tunnel's door (L0) and the South
# Quarantine Tunnel's (R0) high on its walls (wave doors on both sides), the Quarantine Monitor's (L1) behind a Morph Ball door
# on both sides (Prime reaches it with the Grapple Beam: no SM item here, the user's decision 3); a Spider Ball track round the
# arena (the Spider Ball's place: nothing). Here: the floor on row 26 (the arena: flat between the cliffs), the two cliffs of
# the Ruined Courtyard (rows 10-21: the L0 and R0 shelves on top) climbed by three ledges in zigzag each; under the west cliff the
# L1 door's chamber (Samus stands up in it to open the door) and a 1-row Morph Ball tunnel (row 25) from it to the arena;
# spires of ice from the roof.
QC_WEST, QC_EAST = 14, 81                         # the cliffs' last / first column (rows 10-21)
QC_WEST_ZIGZAG, QC_EAST_ZIGZAG = (15, 21, (21, 16, 11)), (75, 69, (21, 16, 11))
QC_CHAMBER = 6                                    # the L1 door's chamber: columns 1-6, rows 22-25
QC_TUNNEL_ROW = 25                                # the Morph Ball tunnel: columns 7-14


def quarantine_cave() -> Shape:
    c = Canvas(6, 2)
    c.carve(1, 1, 94, 25)
    c.fill(1, 10, QC_WEST, 25)
    c.carve(1, 22, QC_CHAMBER, 25)
    c.carve(QC_CHAMBER + 1, QC_TUNNEL_ROW, QC_WEST, QC_TUNNEL_ROW)
    zigzag(c, *QC_WEST_ZIGZAG)
    c.fill(QC_EAST, 10, 94, 21)
    zigzag(c, *QC_EAST_ZIGZAG)
    for x, bottom in ((34, 4), (47, 6), (60, 4)):
        c.fill(x, 1, x + 1, bottom)              # spires of ice from the roof
    return Shape(c)


# --- P26 South Quarantine Tunnel (6x4) -------------------------------------------------------------------------------------
# Prime: the winding snowy tunnel from the Quarantine Cave (L0, high) down and round to the south elevator (R1), wave doors on
# both sides of both. Here: a tunnel of steps from the L0 door's shelf (row 10) down to a floor on row 58: 11 steps 5 columns
# wide, each 4 rows under the one before (Samus walks off them and climbs them back), the tunnel's roof 9 rows over each; at
# its foot an icy hall to the east wall, and in it the R1 door's shelf (rows 26-57 of rock against the east wall) climbed from
# the floor by a step and five ledges in zigzag.
SQT_SHELF = 14                                    # the L0 door's shelf: columns 1-14, row 10
SQT_STEPS = tuple((SQT_SHELF + 1 + 5 * k, 14 + 4 * k) for k in range(11))   # (first column, floor row): 5 wide
SQT_HALL = (70, 17)                               # the east hall: from column 70 to the east wall, rows 17-57
SQT_FLOOR = 58
SQT_EAST_SHELF = 84                               # the R1 door's shelf: columns 84-94, top row 26
SQT_ZIGZAG = (78, 72, (51, 46, 41, 36, 31))
SQT_STEP = (72, 56)                               # a 2-row step on the floor under the zigzag (columns 72-77)


def south_quarantine_tunnel() -> Shape:
    c = Canvas(6, 4)
    c.carve(1, 1, SQT_SHELF, 9)
    for x0, y in SQT_STEPS:
        c.carve(x0, y - 9, x0 + 4, y - 1)
    hx, hy = SQT_HALL
    c.carve(hx, hy, 94, SQT_FLOOR - 1)
    c.fill(SQT_EAST_SHELF, 26, 94, SQT_FLOOR - 1)
    zigzag(c, *SQT_ZIGZAG)
    sx, sy = SQT_STEP
    c.fill(sx, sy, sx + 5, SQT_FLOOR - 1)
    for x in (88, 76):
        c.fill(x, hy, x, hy + 2)                 # icicles over the hall
    return Shape(c)


# --- P27 Quarantine Monitor (3x1) ------------------------------------------------------------------------------------------
# Prime: a small snowy lookout over the Quarantine Cave, reached by a Morph Ball door (R0, on both sides); a Missile Expansion.
# Here: the lookout on row 10, the R0 door's chamber (columns 41-46: Samus stands up in it) behind a wall with a 1-row Morph Ball
# tunnel at its foot (row 9); the missile at the lookout's west end.
QM_WALL = (33, 40)                                # the wall's columns (rows 2-8; the tunnel on row 9)
QM_MISSILE = (4, 9)


def quarantine_monitor() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 2, 46, 9)
    c.fill(QM_WALL[0], 2, QM_WALL[1], 8)
    for x in (12, 22):
        c.fill(x, 2, x, 3)                       # icicles
    return Shape(c)


# --- P31 Transport Access (2x1) --------------------------------------------------------------------------------------------
# Prime: an icy passage from the south elevator (L0, ice doors on both sides) to the Frozen Pike (R0, region E: a door since
# specs/18m); an Energy Tank in a block of ice only the Plasma Beam melts (Prime's "DamageableTrigger_ice01"). Here: the floor
# on row 13, the doors' ledges 3-row steps over it, a pillar of ice in the middle (top row 8, Samus climbs over it) with a niche
# in its east face shut by a plasma cap (the epic's technical decision 3, the Ice Ruins West's way: RoomDef.caps), the Energy
# Tank inside.
TA_PILLAR = (12, 17, 8)                           # columns, top row (to the floor)
TA_CAP = (TA_PILLAR[1], 9, "L", "plasma")         # the cap in the pillar's east face: shot from the east
TA_ETANK = (14, 12)


def transport_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 2, 30, 12)
    c.fill(1, 10, 4, 12)                         # the L0 door's step
    c.fill(27, 10, 30, 12)                       # the R0 door's step (a door since specs/18m)
    x0, x1, top = TA_PILLAR
    c.fill(x0, top, x1, 12)
    c.carve(x0 + 1, top + 1, x1, 12)             # the niche and the cap's 4 blocks (the PLM draws the cap on them)
    for x in (8, 23):
        c.fill(x, 2, x, 3)                       # icicles
    return Shape(c, caps=[TA_CAP])


# --- region D (specs/18l) -------------------------------------------------------------------------------------------------
# The pirates' observatory, towers and labs (the labs' look but the Control Tower's courtyard and the Pike Access' ice tunnel,
# under Prime's sky); the rooms with two doors on one wall a screen apart use the Shorelines' west cliff (west_cliff) or its
# mirror against the east wall.
# --- P28 Observatory Access (3x1) ------------------------------------------------------------------------------------------
# Prime: the corridor from the Research Lab Hydra (L0) to the Observatory (R0), wave doors on both sides of both. Here: the
# corridor on row 10 (both doors' ledge row), the lab's light fittings in the roof.
def observatory_access() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 2, 46, 9)
    for x in (12, 24, 36):
        c.fill(x, 2, x + 1, 3)
    return Shape(c)


# --- P30 Observatory (3x2) ------------------------------------------------------------------------------------------------
# Prime: the pirates' observatory under its dome: the Observatory Access' door (L0) high in the west, the West Tower Entrance's
# (L1) at the floor under it (wave doors on both sides of both), Save Station D's (R1) at the floor in the east behind a missile
# shield on this side; the planetarium projector the bomb slots wake, the Super Missile at the top. Here: the floor on row 26
# (L1, R1), the west cliff (west_cliff: the L0 shelf, the L1 passage under it) and the mirror cliff against the east wall (rows
# 10-21, the R1 passage under it), each climbed from the floor by three ledges in zigzag; on the east cliff's top the
# projector's chamber in the dome's corner, behind a wall with a 1-row tunnel at its foot shut by a bomb block (the bomb slot:
# the Morph Ball and the Bombs, the Ice Temple's way), the Super Missile inside; the projector's lens hanging from the dome.
OBS_EAST_CLIFF = 34                              # the east cliff's first column (to the east wall), rows 10-21
OBS_EAST_ZIGZAG = (28, 22, (21, 16, 11))
OBS_WALL = (36, 38)                              # the projector chamber's wall (rows 1-8; its tunnel on row 9)
OBS_BOMB = (37, 9)
OBS_SUPER = (43, 9)


def observatory() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 1, 46, 25)
    west_cliff(c)
    c.fill(OBS_EAST_CLIFF, 10, 46, 21)
    zigzag(c, *OBS_EAST_ZIGZAG)
    c.fill(OBS_WALL[0], 1, OBS_WALL[1], 8)
    c.fill(20, 1, 27, 2)                         # the projector's mount in the dome
    c.fill(22, 3, 25, 4)                         # its lens
    return Shape(c, blocks=[bomb_block(*OBS_BOMB)])


# --- P32 West Tower Entrance (1x1) ------------------------------------------------------------------------------------------
# Prime: a short hall from the West Tower (L0, a missile shield on both sides) to the Observatory (R0, a wave door on both
# sides). Here: the hall on row 10, a light fitting.
def west_tower_entrance() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 2, 14, 9)
    c.fill(7, 2, 8, 3)
    return Shape(c)


# --- P33 Save Station D (1x1) -------------------------------------------------------------------------------------------------
# Prime's save room off the Observatory (L0, the missile shield on the Observatory's side). Load station 3 of area 4
# (tools/areas.py PHENDRANA): Save Station A's room (the labs' look here).
SAVE_STATION_D = (8, 13)


def save_station_d() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    c.fill(1, 11, 5, 12)                         # a 3-block step down from the L0 door's ledge (row 10) to the floor (13)
    return Shape(c, save=SAVE_STATION_D)


# --- P35 West Tower (2x2) -----------------------------------------------------------------------------------------------------
# Prime: the inside of the west tower: the Control Tower's door (L1) at its foot, the West Tower Entrance's (R0) at its top (a
# missile shield on both sides). Here: the floor on row 26 (L1), a mass of rock against the east wall (rows 10-25: the R0
# shelf on top) climbed by three ledges in zigzag; the tower's beams in the roof.
WT_EAST = 22                                     # the east rock's first column
WT_ZIGZAG = (16, 10, (21, 16, 11))


def west_tower() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 1, 30, 25)
    c.fill(WT_EAST, 10, 30, 25)
    zigzag(c, *WT_ZIGZAG)
    for x in (4, 12):
        c.fill(x, 1, x + 1, 3)
    return Shape(c)


# --- P39 Control Tower (4x2) ----------------------------------------------------------------------------------------------------
# Prime: the snowy courtyard of the pirates' control tower (the tower Samus brings down for an artifact: nothing here), its two
# doors in the east: the West Tower's (R0) high, the East Tower's (R1) at the floor, wave doors on both sides. Here: the floor on
# row 26 (R1) under the sky, the mirror cliff against the east wall (rows 10-21: the R0 shelf, the R1 passage under it) climbed
# by three ledges in zigzag; the control tower in the west, standing (its top out of every jump: the artifact's place, empty).
CT_EAST_CLIFF = 50
CT_EAST_ZIGZAG = (44, 38, (21, 16, 11))
CT_TOWER = (10, 15, 6)                           # columns, top row (to the floor)


def control_tower() -> Shape:
    c = Canvas(4, 2)
    c.carve(1, 1, 62, 25)
    c.fill(CT_EAST_CLIFF, 10, 62, 21)
    zigzag(c, *CT_EAST_ZIGZAG)
    x0, x1, top = CT_TOWER
    c.fill(x0, top, x1, 25)
    c.fill(x0 - 1, top, x1 + 1, top + 1)         # the tower's head
    c.fill(x0 + 2, top - 3, x0 + 3, top - 1)     # its antenna
    for x in (26, 58):
        c.fill(x, 1, x, 2)                       # icicles
    return Shape(c)


# --- P43 East Tower (2x2) -------------------------------------------------------------------------------------------------------
# Prime: the inside of the east tower: the Control Tower's door (L0) at its top, the Aether Lab Entryway's (R1) at its foot,
# wave doors on both sides. Here: the West Tower mirrored: a mass of rock against the west wall (rows 10-25: the L0 shelf on
# top) climbed by three ledges in zigzag from the floor (row 26: R1).
ET_WEST = 9                                      # the west rock's last column
ET_ZIGZAG = (10, 16, (21, 16, 11))


def east_tower() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 1, 30, 25)
    c.fill(1, 10, ET_WEST, 25)
    zigzag(c, *ET_ZIGZAG)
    for x in (18, 26):
        c.fill(x, 1, x + 1, 3)
    return Shape(c)


# --- P50 Aether Lab Entryway (1x1) ----------------------------------------------------------------------------------------------
# Prime: a short hall from the East Tower (L0) to the Research Lab Aether (R0), wave doors on both sides. Here: the hall on row
# 10, a light fitting under the roof (row 4) with room over it (rows 1-3): its orb floats there, over 60 px above both doors
# (validate.homing_problems: 120 frames of its drift).
ALE_FITTING = (5, 10, 4)                         # columns, row


def aether_lab_entryway() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 1, 14, 9)
    x0, x1, y = ALE_FITTING
    c.fill(x0, y, x1, y)
    return Shape(c)


# --- P51 Research Lab Aether (3x2) ------------------------------------------------------------------------------------------------
# Prime: a two-storey lab, the Aether Lab Entryway's door (L0) on the upper floor, the Research Core Access' (R1) on the lower
# (wave doors on both sides), a Metroid out of its tube, an Energy Tank and a Missile Expansion. Here: the upper floor a slab on
# row 10 (the L0 door's ledge row) from the west wall to column 30, the lower lab under it (floor 26: R1); east of the slab the
# way down, climbed back by three ledges in zigzag; the Metroid's empty tank in the lower lab (its glass a pedestal, the Energy
# Tank on it), the missile in the lower lab's west corner; the tubes' bases hang from the slab.
AETHER_SLAB = 30                                 # the upper floor's last column (row 10)
AETHER_ZIGZAG = (31, 37, (21, 16, 11))
AETHER_TANK = (12, 17, 22)                       # the tank's columns and top row (to the floor)
AETHER_ETANK = (14, 21)
AETHER_MISSILE = (3, 25)


def research_lab_aether() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 1, 46, 25)
    c.fill(1, 10, AETHER_SLAB, 10)
    zigzag(c, *AETHER_ZIGZAG)
    x0, x1, top = AETHER_TANK
    c.fill(x0, top, x1, 25)
    for x in (6, 22):
        c.fill(x, 11, x + 1, 12)                 # the tubes' bases under the slab
    return Shape(c)


# --- P44 Research Core Access (2x1) ----------------------------------------------------------------------------------------------
# Prime: the corridor from the Research Lab Aether (L0) to the Research Core (R0), wave doors on both sides. Here: the corridor on
# row 10, light fittings.
def research_core_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 2, 30, 9)
    for x in (10, 20):
        c.fill(x, 2, x + 1, 3)
    return Shape(c)


# --- P40 Research Core (2x2) ------------------------------------------------------------------------------------------------------
# Prime: the labs' core, a tall room round its machine, 3 Metroids, the Thermal Visor (nothing here: the user's decision 3); the
# Research Core Access' door (L0, wave on both sides) high in the west, the Pike Access' (L1, ice on both sides) under it. Here:
# the core a mass of rock from the west wall (rows 10-21: the L0 shelf and the core's top one walk, the L1 passage under it),
# the shaft round it to the east wall (columns 22-30) where the Metroids wait, off the camera of both doors; the walk goes over
# the core, down the shaft and back west under it (and up the shaft by three ledges in zigzag the other way); the core's
# machine and its pipes in the roof.
RC_CORE = 21                                     # the core's last column (rows 10-21, from the west wall)
RC_ZIGZAG = (22, 25, (21, 16, 11))


def research_core() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 1, 30, 25)
    c.fill(1, 10, RC_CORE, 21)
    zigzag(c, *RC_ZIGZAG)
    c.fill(8, 1, 13, 3)                          # the core's machine
    c.fill(10, 4, 11, 5)
    return Shape(c)


# --- P36 Pike Access (2x1) --------------------------------------------------------------------------------------------------------
# Prime: an icy tunnel from the Frozen Pike (L0, region E: a door since specs/18m; wave doors on both sides) to the Research
# Core (R0, ice doors on both sides). Here: the tunnel on row 10, icicles, in the snow look (no snow falls: Prime's has none).
def pike_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 2, 30, 9)
    for x in (7, 16, 25):
        c.fill(x, 2, x, 3)
    return Shape(c)


# --- region E (specs/18m) -------------------------------------------------------------------------------------------------
# The deep south: Prime's natural ice caves and the snowy cliffs at Phendrana's edge, all in the snow look (snow falling only
# where Prime snows: SNOW_ROOMS). No vertical door of the region is in the icy ruins (its table has no vertical wave door).
# --- P34 Frozen Pike (3x4) --------------------------------------------------------------------------------------------------
# Prime: a tall frozen ravine, the Transport Access' door (L0) and the Pike Access' (R0) at its top, the Frost Cave Access' (R1)
# half-way down, the Hunter Cave Access' (R3) at the bottom by a frozen pond (its water dry here: the user's decision 5); wave
# doors on both sides of all four. Here: two storeys of slabs (rows 10 and 26: the L0/R0 and the R1 doors' ledge rows) with a
# gap between them (columns 18-29), the floor on row 58 (R3); from the floor up through the gaps two zigzags (the Research Lab
# Hydra's way), each ending on a ledge beside the east slab, the dry pond a 2-row dip in the floor, icicles from the rock.
PIKE_GAP = (18, 29)                              # the gap between the slabs (columns) on rows 10 and 26
PIKE_FLOOR = 58
PIKE_UPPER_ZIGZAG = (24, 18, (21, 16, 11))      # the slab of row 26 up to the top slabs (row 11: beside the east one)
PIKE_LOWER_ZIGZAG = (18, 24, (53, 48, 43, 38, 33, 28))   # the floor up to the slabs of row 26
PIKE_POND = (5, 14)                              # the dry pond's columns (rows 58-59)


def frozen_pike() -> Shape:
    c = Canvas(3, 4)
    c.carve(1, 1, 46, PIKE_FLOOR - 1)
    for y in (10, 26):
        c.fill(1, y, PIKE_GAP[0] - 1, y)
        c.fill(PIKE_GAP[1] + 1, y, 46, y)
    zigzag(c, *PIKE_UPPER_ZIGZAG)
    zigzag(c, *PIKE_LOWER_ZIGZAG)
    c.carve(PIKE_POND[0], PIKE_FLOOR, PIKE_POND[1], PIKE_FLOOR + 1)
    for x, bottom in ((8, 3), (22, 5), (38, 3)):
        c.fill(x, 1, x + 1, bottom)              # icicles
    for x in (6, 40):
        c.fill(x, 27, x, 29)                     # icicles under the slabs of row 26
    return Shape(c)


# --- P37 Frost Cave Access (6x2) ------------------------------------------------------------------------------------------
# Prime: a long snowy gully from the Frozen Pike (L0) to the Frost Cave (R0), wave doors on both sides; 2 Beetles and a Wall
# Crawler Swarm. Here: the two doors on cliffs (rows 10-25: their shelves on row 10), the gully between them down on row 26, each
# cliff climbed from it by three ledges in zigzag (the Ruins Entryway's).
FCA_WEST, FCA_EAST = 20, 75                       # the west cliff's last column, the east cliff's first (rows 10-25)
FCA_WEST_ZIGZAG = (21, 27, (21, 16, 11))
FCA_EAST_ZIGZAG = (69, 63, (21, 16, 11))


def frost_cave_access() -> Shape:
    c = Canvas(6, 2)
    c.carve(1, 1, 94, 25)
    c.fill(1, 10, FCA_WEST, 25)
    c.fill(FCA_EAST, 10, 94, 25)
    zigzag(c, *FCA_WEST_ZIGZAG)
    zigzag(c, *FCA_EAST_ZIGZAG)
    for x, bottom in ((34, 3), (50, 4), (58, 2)):
        c.fill(x, 1, x + 1, bottom)              # icicles
    return Shape(c)


# --- P38 Hunter Cave Access (6x1) -----------------------------------------------------------------------------------------
# Prime: a long icy tunnel with a lake from the Frozen Pike (L0) to the Hunter Cave (R0), wave doors on both sides; 3 Jelly Zaps
# in the water (out: the lake is dry). Here: the tunnel on row 10, the dry lake a 2-row dip in its floor, icicles.
HCA_LAKE = (32, 63)                              # the dry lake's columns (rows 10-11)


def hunter_cave_access() -> Shape:
    c = Canvas(6, 1)
    c.carve(1, 2, 94, 9)
    c.carve(HCA_LAKE[0], 10, HCA_LAKE[1], 11)
    for x in (14, 28, 44, 58, 76):
        c.fill(x, 2, x, 3)                       # icicles
    return Shape(c)


# --- P41 Frost Cave (3x3) -------------------------------------------------------------------------------------------------
# Prime: a deep ice cave, the Frost Cave Access' door (L2) at its floor, Save Station C's (L1) on the west cliff over it, the
# Upper Edge Tunnel's (R1) on the east cliff (wave doors on both sides of all three); stalactites over a frozen lake whose ice
# they break when shot, a Missile Expansion under it (the lake is dry here: the user's decision 5). Here: the floor on row 42
# (L2), the west cliff (rows 26-37: the L1 shelf, the L2 passage under it) and the east rock (rows 26-41: the R1 shelf), each
# climbed from the floor by three ledges in zigzag (the two meet over the lake on row 32); the dry lake a 2-row dip in the floor
# between them, the missile in it; stalactites from the roof.
FROST_FLOOR = 42
FROST_WEST, FROST_EAST = 12, 35                  # the west cliff's last column (rows 26-37), the east rock's first (26-41)
FROST_WEST_ZIGZAG = (13, 19, (37, 32, 27))
FROST_EAST_ZIGZAG = (29, 23, (37, 32, 27))
FROST_LAKE = (19, 28)                            # the dry lake's columns (rows 42-43)
FROST_MISSILE = (23, 43)


def frost_cave() -> Shape:
    c = Canvas(3, 3)
    c.carve(1, 1, 46, FROST_FLOOR - 1)
    c.fill(1, 26, FROST_WEST, 37)
    c.fill(FROST_EAST, 26, 46, FROST_FLOOR - 1)
    zigzag(c, *FROST_WEST_ZIGZAG)
    zigzag(c, *FROST_EAST_ZIGZAG)
    c.carve(FROST_LAKE[0], FROST_FLOOR, FROST_LAKE[1], FROST_FLOOR + 1)
    for x, bottom in ((10, 8), (18, 12), (27, 10), (36, 7)):
        c.fill(x, 1, x + 1, bottom)              # the stalactites
        c.fill(x, bottom + 1, x, bottom + 2)
    return Shape(c)


# --- P45 Save Station C (2x1) ---------------------------------------------------------------------------------------------------
# Prime's save room off the Frost Cave (R0, a wave door on both sides; snow falls there in Prime). Load station 4 of area 4
# (tools/areas.py PHENDRANA): Save Station B's room, two screens wide, the station in the west one.
SAVE_STATION_C = (8, 13)


def save_station_c() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 12)
    c.fill(26, 11, 30, 12)                       # a 3-block step down from the R0 door's ledge (row 10) to the floor (13)
    for x in (18, 22):
        c.fill(x, 3, x, 4)                       # icicles
    return Shape(c, save=SAVE_STATION_C)


# --- P42 Hunter Cave (3x2) ------------------------------------------------------------------------------------------------
# Prime: a cave over a lake (a grapple point, stalactites), the Hunter Cave Access' door (L1) and the Chamber Access' (R1) at
# its floor, the Lower Edge Tunnel's (R0) high in the east, the Lake Tunnel's down in the lake (B1); wave doors on both sides of
# all four. Here: the floor on row 26 (L1, R1), the east cliff (rows 10-21: the R0 shelf, the R1 passage under it) climbed by
# three ledges in zigzag; the lake dry, a basin round the floor door (floor 29: the floor door's ledge row); stalactites.
HUNTER_EAST = 38                                 # the east cliff's first column (rows 10-21)
HUNTER_ZIGZAG = (32, 26, (21, 16, 11))
HUNTER_BASIN = (19, 28)                          # columns, rows 26-28 (its floor: row 29)


def hunter_cave() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 1, 46, 25)
    c.fill(HUNTER_EAST, 10, 46, 21)
    zigzag(c, *HUNTER_ZIGZAG)
    c.carve(HUNTER_BASIN[0], 26, HUNTER_BASIN[1], 28)
    for x, bottom in ((8, 5), (20, 7), (30, 4)):
        c.fill(x, 1, x + 1, bottom)              # stalactites
    return Shape(c)


# --- P46 Upper Edge Tunnel (3x1) ------------------------------------------------------------------------------------------
# Prime: an icy tunnel from the Frost Cave (L0) to Phendrana's Edge (R0), wave doors on both sides. Here: the tunnel on row 10.
def upper_edge_tunnel() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 2, 46, 9)
    for x in (12, 26, 38):
        c.fill(x, 2, x + 1, 3)
    return Shape(c)


# --- P47 Lower Edge Tunnel (3x1) ------------------------------------------------------------------------------------------
# Prime: a tunnel with a pool (dry here) from the Hunter Cave (L0) to Phendrana's Edge (R0), wave doors on both sides; 2 Atomic
# Betas. Here: the Ice Ruins Access' shape (its orbs' places, specs/18g: more than 120 frames of drift from both doors).
def lower_edge_tunnel() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 2, 46, 9)
    for x in (22, 34):
        c.fill(x, 2, x + 1, 3)
    return Shape(c)


# --- P48 Chamber Access (2x1) ---------------------------------------------------------------------------------------------
# Prime: the passage from the Hunter Cave (L0) down to the Gravity Chamber (its floor door B0), wave doors on both sides. Here:
# the Quarantine Access mirrored: the floor on row 13 (the floor door's ledge row), the L0 door's ledge a 3-row step over it.
def chamber_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 12)
    c.fill(1, 11, 5, 12)                         # the step under the L0 door's ledge
    c.fill(18, 3, 20, 5)
    return Shape(c)


# --- P49 Lake Tunnel (2x1) ------------------------------------------------------------------------------------------------
# Prime: a flooded tunnel from the Hunter Cave's lake (its ceiling door T0) to the Gravity Chamber (R0), wave doors on both
# sides; an Atomic Beta. Here (dry: only the Gravity Chamber is flooded): the passage on row 10, the ceiling door's platform
# (row 6) in the west.
def lake_tunnel() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 2, 30, 9)
    c.fill(22, 2, 23, 3)
    return Shape(c)


# --- P52 Phendrana's Edge (2x4) -------------------------------------------------------------------------------------------
# Prime: the tall snowy cliffs at the world's edge: the Upper Edge Tunnel's door (L1) and the Lower Edge Tunnel's (L3) in the
# west (wave doors on both sides), the Storage Cave's (R3, plasma doors on both sides) at the floor and the Security Cave's (R2,
# a Morph Ball door on both sides) on the east cliff; grapple points up the cliffs (no SM item: decision 3). Here: the floor
# on row 58 (L3, R3), the east rock (rows 42-53, columns 13-30: the R3 passage under it), on it the R2 door's chamber (columns
# 25-30, rows 38-41: Samus stands up in it) behind rock with a 1-row Morph Ball tunnel at its foot (row 41) shut by a power bomb
# block at its west mouth (the Warrior Shrine's way, specs/17h: the expansion behind it is never picked up before round 6); the
# west cliff (rows 26-37: the L1 shelf); from the floor up to the east rock three ledges in zigzag, and from it three more up to
# the shelf over the chamber's rock (row 32); icicles and a spire of ice from the sky's rocks.
EDGE_FLOOR = 58
EDGE_WEST = 6                                    # the west cliff's last column (rows 26-37)
EDGE_ROCK = (13, 42, 53)                         # the east rock: first column (to the east wall), top row, bottom row
EDGE_LOW_ZIGZAG = (7, 1, (53, 48, 43))
EDGE_HIGH_ZIGZAG = (7, 13, (37, 32, 27))
EDGE_BLOCK = (19, 32)                            # the R2 chamber's rock: first column (to the east wall), top row (to 41)
EDGE_CHAMBER = 25                                # the chamber's first column (rows 38-41)
EDGE_PB = (19, 41)                               # the power bomb block at the tunnel's west mouth (the tunnel: 19-24)


def phendrana_edge() -> Shape:
    c = Canvas(2, 4)
    c.carve(1, 1, 30, EDGE_FLOOR - 1)
    c.fill(1, 26, EDGE_WEST, 37)
    x0, top, bottom = EDGE_ROCK
    c.fill(x0, top, 30, bottom)
    zigzag(c, *EDGE_LOW_ZIGZAG)
    zigzag(c, *EDGE_HIGH_ZIGZAG)
    bx, by = EDGE_BLOCK
    c.fill(bx, by, 30, top - 1)
    c.carve(EDGE_CHAMBER, top - 4, 30, top - 1)  # the chamber
    c.carve(bx, top - 1, EDGE_CHAMBER - 1, top - 1)   # the tunnel
    for x, bottom in ((10, 4), (24, 6)):
        c.fill(x, 1, x + 1, bottom)              # icicles
    c.fill(26, 1, 29, 3)                         # an overhang of ice
    return Shape(c, blocks=[power_bomb_block(*EDGE_PB)])


# --- P53 Gravity Chamber (3x2, flooded) -----------------------------------------------------------------------------------------
# Prime: the deep flooded chamber (its water kept: the user's decision 5, rooms.py FLOODED), the Chamber Access' door (T0) and
# the Lake Tunnel's (L0) at its top in the west, wave doors on both sides; the Gravity Suit at the bottom (a missile here: the
# suit is the Tallon's, decision 3) and a Missile Expansion up on a ledge Prime reaches with the Grapple Beam. Here (specs/07l's
# water: without the Gravity Suit she jumps 3 blocks under water, with it as on land, and the Space Jump only works with it):
# the west rock (from row 10: the L0 shelf under the T0 door's platform, row 6; its east end 2 rows higher, the step she climbs
# to the platform from), the deep water east of it to the floor (row 29), a stair of 3-row steps 4 wide climbing west to the
# rock's east end (what she has without the suit; the Reflecting Pool's, specs/12l: a zigzag's ledge two steps up, 6 rows over,
# leaves her no room for the 3-row jump; the steps are solid down to the floor); the Gravity Suit's missile on the floor
# east of the stair, the other on a ledge against the east wall
# (row 9): out of every jump, the Space Jump's with the suit (Prime's grapple point).
GRAV_FLOOR = 29
GRAV_WEST = (13, 10)                             # the west rock's last column at the L0 shelf's height (row 10)
GRAV_STEP = (16, 8)                              # its east end: columns 14-16 from row 8 (the step to the platform)
GRAV_STAIR = tuple((17 + 4 * k, 11 + 3 * k) for k in range(6))   # (first column, row) of each step, 4 wide
GRAV_LEDGE = (39, 9)                             # the high ledge: from column 39 to the east wall, row 9
GRAV_LOW_MISSILE = (43, 28)
GRAV_HIGH_MISSILE = (43, 8)


def gravity_chamber() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 1, 46, GRAV_FLOOR - 1)
    wx, wy = GRAV_WEST
    c.fill(1, wy, wx, GRAV_FLOOR - 1)
    sx, sy = GRAV_STEP
    c.fill(wx + 1, sy, sx, GRAV_FLOOR - 1)
    for x, y in GRAV_STAIR:
        c.fill(x, y, x + 3, GRAV_FLOOR - 1)      # a staircase of rock (no crawlspace nor pit under the steps)
    lx, ly = GRAV_LEDGE
    c.fill(lx, ly, 46, ly)
    for x, bottom in ((22, 3), (30, 5), (36, 2)):
        c.fill(x, 1, x + 1, bottom)              # icicles
    return Shape(c)


# --- P54 Storage Cave (1x1) ---------------------------------------------------------------------------------------------------
# Prime: a small snowy cave behind plasma doors off Phendrana's Edge (L0), an artifact on a pedestal (artifacts are out: the
# epic). Here: the floor on row 13, a step under the L0 door's ledge, the empty pedestal.
def storage_cave() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    c.fill(1, 11, 5, 12)
    c.fill(9, 11, 11, 12)                        # the empty pedestal
    return Shape(c)


# --- P55 Security Cave (2x1) ---------------------------------------------------------------------------------------------------
# Prime: a snowy cave behind a Morph Ball door off Phendrana's Edge (L0, on both sides), a Power Bomb Expansion. Here: the L0
# door's chamber (columns 1-6) behind a wall with a 1-row Morph Ball tunnel at its foot (row 9) shut by a power bomb block at its
# east mouth (Phendrana's Edge's side has the same: the door's gate is the Morph Ball and the Power Bomb, rooms.py GATES), the
# cave east of it on row 10, the expansion at its east end.
SEC_WALL = (7, 12)                               # the wall's columns (rows 2-8; its tunnel on row 9)
SEC_PB_BLOCK = (12, 9)
SEC_PB = (26, 9)


def security_cave() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 2, 30, 9)
    c.fill(SEC_WALL[0], 2, SEC_WALL[1], 8)
    for x in (18, 23):
        c.fill(x, 2, x, 3)                       # icicles
    return Shape(c, blocks=[power_bomb_block(*SEC_PB_BLOCK)])


LAYOUTS = {
    "phendrana_transport_magmoor_west": transport_magmoor_west,
    "phendrana_transport_magmoor_south": transport_magmoor_south,
    # specs/18f: region A
    "phendrana_shoreline_entrance": shoreline_entrance,
    "phendrana_shorelines": shorelines,
    "phendrana_temple_entryway": temple_entryway,
    "phendrana_save_station_b": save_station_b,
    "phendrana_ruins_entryway": ruins_entryway,
    "phendrana_plaza_walkway": plaza_walkway,
    "phendrana_ice_ruins_access": ice_ruins_access,
    "phendrana_chozo_ice_temple": chozo_ice_temple,
    "phendrana_ice_ruins_east": ice_ruins_east,
    "phendrana_chapel_tunnel": chapel_tunnel,
    "phendrana_chapel_of_the_elders": chapel_of_the_elders,
    # specs/18i: region B
    "phendrana_ice_ruins_west": ice_ruins_west,
    "phendrana_courtyard_entryway": courtyard_entryway,
    "phendrana_canyon_entryway": canyon_entryway,
    "phendrana_canyon": phendrana_canyon,
    "phendrana_ruined_courtyard": ruined_courtyard,
    "phendrana_save_station_a": save_station_a,
    "phendrana_specimen_storage": specimen_storage,
    "phendrana_quarantine_access": quarantine_access,
    "phendrana_research_entrance": research_entrance,
    "phendrana_map_station": map_station,
    "phendrana_hydra_lab_entryway": hydra_lab_entryway,
    "phendrana_research_lab_hydra": research_lab_hydra,
    # specs/18j: region C (the P29 above: its way up to the R0)
    "phendrana_north_quarantine_tunnel": north_quarantine_tunnel,
    "phendrana_quarantine_cave": quarantine_cave,
    "phendrana_south_quarantine_tunnel": south_quarantine_tunnel,
    "phendrana_quarantine_monitor": quarantine_monitor,
    "phendrana_transport_access": transport_access,
    # specs/18l: region D
    "phendrana_observatory_access": observatory_access,
    "phendrana_observatory": observatory,
    "phendrana_west_tower_entrance": west_tower_entrance,
    "phendrana_save_station_d": save_station_d,
    "phendrana_west_tower": west_tower,
    "phendrana_control_tower": control_tower,
    "phendrana_east_tower": east_tower,
    "phendrana_aether_lab_entryway": aether_lab_entryway,
    "phendrana_research_lab_aether": research_lab_aether,
    "phendrana_research_core_access": research_core_access,
    "phendrana_research_core": research_core,
    "phendrana_pike_access": pike_access,
    # specs/18m: region E
    "phendrana_frozen_pike": frozen_pike,
    "phendrana_frost_cave_access": frost_cave_access,
    "phendrana_hunter_cave_access": hunter_cave_access,
    "phendrana_frost_cave": frost_cave,
    "phendrana_save_station_c": save_station_c,
    "phendrana_hunter_cave": hunter_cave,
    "phendrana_upper_edge_tunnel": upper_edge_tunnel,
    "phendrana_lower_edge_tunnel": lower_edge_tunnel,
    "phendrana_chamber_access": chamber_access,
    "phendrana_lake_tunnel": lake_tunnel,
    "phendrana_edge": phendrana_edge,
    "phendrana_gravity_chamber": gravity_chamber,
    "phendrana_storage_cave": storage_cave,
    "phendrana_security_cave": security_cave,
}

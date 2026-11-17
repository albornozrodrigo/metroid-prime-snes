"""Layouts of the Chozo Ruins rooms (sandstone bricks of tileset $0C, specs/12d).

specs/12e: the three elevator rooms to the Tallon Overworld (Prime's P0, P62, P63; 1x2 each, tools/chozo/rooms.py TABLE), built
before their regions (12f and later) as finished dead ends: the elevator from the Tallon comes down a 2-block shaft from the
top row onto its platform, on the floor of a hall (as the vanilla arrival room $8F:9AD9: shaft and exit on the top row). The
hall is on the screen of the room's door (LINKS), its floor on that door's ledge row; the door itself is not there yet: its
wall stays shut until its neighbour is built (12f: the Ruins Entrance; 12l: Save Station 3 and the Transport Access South),
so the region's spec only opens the wall. The other screen is rock, the shaft through it. Same rules as the Tallon's rooms
(tools/tallon/layouts.py), checked by tools/validate.py with the platform as the room's way out.

specs/12f: region A (12 rooms: the North transport's door opens into the Ruins Entrance). Shapes after Prime's rooms (the
plaza's courtyard, the shrine's bowl, the tower), on the Tallon's rules: side doors on rows 6-9 of their screen with the
floor on row 10, steps of at most 4 blocks, the jump measured (smlib/reach.py) deciding every climb; a door to a room of a
region not built yet is not drawn (its wall), but its floor is already at the door's ledge row so the region's spec only
opens the wall. Items (tools/chozo/items.py) sit where the drawing puts Prime's lock in front of them: Space Jump ledges
(Boost Ball half-pipes, the grapple ledge, the plaza's locked-door ledge), a Morph Ball tunnel shut by a bomb block (the
shrine's lower tunnel) and a hut of power bomb blocks (the plaza's tree, Super Missiles in Prime).
"""
from __future__ import annotations

from frigate.rooms import Elevator
from smlib.canvas import Canvas
from tallon.layouts import Shape, bomb_block, power_bomb_block

SHAFT_X = 7          # the shaft's left column: the platform's centre is x 128, as the vanilla elevators ($D73F at x 128)


def transport(door_screen: int) -> Shape:
    """1x2 elevator room: a hall across the screen `door_screen` (rows 3-9 of it, the floor on row 10, a side door's ledge
    row) and the shaft from the top row down to the platform's blocks on that floor (SHAFT_X)."""
    c = Canvas(1, 2)
    top = door_screen * 16
    c.carve(1, top + 3, 14, top + 9)                   # the hall
    c.carve(SHAFT_X, 0, SHAFT_X + 1, top + 10)         # the shaft, the exit row and the platform's blocks
    return Shape(c, elevator=Elevator(SHAFT_X, top + 10, up=True))


def transport_tallon_north() -> Shape:   # P0, door R1 -> Ruins Entrance
    return transport(1)


def transport_tallon_east() -> Shape:    # P62, door R0 -> Save Station 3
    return transport(0)


def transport_tallon_south() -> Shape:   # P63, door L0 -> Transport Access South
    return transport(0)


# --- P1 Ruins Entrance (2x1) --------------------------------------------------------------------------------------------
# Prime: a long hall from the elevator to the plaza, its floor broken in the middle. Hall rows 3-9 (floor 10 = both doors'
# ledge row), a sunken stretch 3 blocks deep in the middle, broken columns hanging from the roof.
def ruins_entrance() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    c.carve(9, 10, 22, 12)                      # the broken floor: 3 blocks down, 3 up
    for x in (5, 15, 26):
        c.fill(x, 3, x + 1, 4)                  # column stubs (5 rows of headroom left)
    c.fill(15, 12, 16, 12)                      # rubble in the dip (a 1-block hop)
    return Shape(c)


# --- P2 Main Plaza (6x2) ------------------------------------------------------------------------------------------------
# Prime's courtyard: open to the sky, the Ruins Entrance door high on the west wall, the Ruined Shrine Access door low on
# it behind a missile shield, the Ruined Fountain Access door low on the east wall, the Nursery Access and Plaza Access
# (Vault) doors in the north, the Piston Tunnel's Morph Ball door under the floor; a half-pipe in the middle, the big tree
# in the east half, a grapple ledge in the east. Here: the floor on row 26 (the low side doors' ledge row) from wall to
# wall; the west balcony of the L0 door (row 10, out to column 13) and a stair of three platforms (tops 22, 18, 14) up to
# it; the T0 door's platform (row 6, Canvas.door_gap) reached from the balcony past its east end. Prime's locks, decision B:
#  - the B0 floor door (Piston Tunnel) under a dais (row 22, columns 5-14, on walls down to the floor): the chamber
#    under it (rows 23-28, 6 rows: room to rise out of the door and steer onto its east ledge, emulator) opens on the hole
#    of the door; the only way in is a 1-row Morph Ball tunnel (row 28, columns 14-17) from a pit in the floor (columns
#    18-19): Morph Ball;
#  - the T1 ceiling door (Plaza Access) is one-way (tools/chozo/rooms.py ONE_WAY_DOORS): its platform (row 6) is a Space Jump
#    ledge 19 rows over the floor, with the E-tank of Prime's "Locked Door" ledge;
#  - the half-pipe's missile on a platform over the middle (row 13), the grapple ledge's on one in the east (row 14): Space
#    Jump; the tree's missile in the hollow of the tree's fallen trunk (Prime's tree: Super Missiles), behind 3 power
#    bomb blocks; the trunk's roof (row 22) is a 4-block climb over.
PLAZA_FLOOR = 26
PLAZA_TREE_HUT = (60, PLAZA_FLOOR - 3, PLAZA_FLOOR - 1)    # west wall column, rows of the power bomb blocks
PLAZA_TRUNK = 9        # the trunk's east wall, columns from its west one


def main_plaza() -> Shape:
    c = Canvas(6, 2)
    c.carve(1, 1, 94, PLAZA_FLOOR - 1)          # the courtyard, open to the top
    c.fill(0, 10, 13, 11)                       # the L0 door's balcony
    # the stair from the floor up to the balcony's east end (tops 22, 18, 14, then the balcony's 10)
    c.fill(22, 22, 25, 22)
    c.fill(18, 18, 21, 18)
    c.fill(14, 14, 17, 14)
    # the Piston Tunnel's door (B0, columns 6-9): its hole goes up to the chamber under the dais
    c.fill(5, 22, 14, 22)                       # the dais over the chamber (a 4-block step), on its two walls
    c.fill(5, 23, 5, PLAZA_FLOOR - 1)
    c.fill(14, 23, 14, PLAZA_FLOOR - 1)
    c.carve(6, 23, 13, PLAZA_FLOOR + 2)         # the chamber (rows 23-28): coming up the door she rises into it and
                                                # steers onto the door's east ledge (row 29, Canvas.door_gap)
    c.carve(14, PLAZA_FLOOR + 2, 17, PLAZA_FLOOR + 2)   # the Morph Ball tunnel
    c.carve(18, PLAZA_FLOOR, 19, PLAZA_FLOOR + 2)   # the pit she morphs in
    # the half-pipe's ledge and the grapple ledge (Space Jump)
    c.fill(34, 13, 39, 13)
    c.fill(80, 14, 86, 14)
    # the tree's fallen trunk (columns 60-69, roof on row 22) with its hollow (61-68) behind a west wall of power bomb
    # blocks; the missile at the hollow's far end (68) (specs/12f put it out of the explosion's first-phase box and first
    # in the PLM list, because a bombed item block leaves a dead PLM slot with its block index that Samus' touch could find
    # first; specs/13 fixed the touch in the engine, smlib/itemtouch.py, and specs/12g2 dropped the 12f rule)
    hut_x, top, bottom = PLAZA_TREE_HUT
    c.fill(hut_x, top - 1, hut_x + PLAZA_TRUNK, bottom)
    c.carve(hut_x, top, hut_x + PLAZA_TRUNK - 1, bottom)
    return Shape(c, blocks=[power_bomb_block(hut_x, y) for y in range(top, bottom + 1)])


# --- P3 Ruined Fountain Access (3x1) -------------------------------------------------------------------------------------
# A hall from the plaza east to the Ruined Fountain (region C: its door is still wall). Arches hang from the roof; a raised
# stretch in the middle.
def ruined_fountain_access() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 3, 46, 9)
    c.fill(18, 8, 29, 9)                        # raised middle (2 blocks)
    for x in (10, 22, 36):
        c.fill(x, 3, x + 2, 3)                  # arches
    return Shape(c)


# --- P4 Ruined Shrine Access (3x1) ---------------------------------------------------------------------------------------
# From the plaza (R0, the red door is on the plaza's side) west to the shrine: a hall with a step down in the middle.
def ruined_shrine_access() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 3, 46, 9)
    c.carve(14, 10, 33, 11)                     # the lower middle (2 blocks)
    for x in (8, 24, 40):
        c.fill(x, 3, x + 1, 4)
    return Shape(c)


# --- P5 Nursery Access (1x1) ---------------------------------------------------------------------------------------------
# Up from the plaza's T0 door (B0, the floor door), to the Eyon Tunnel (L0, region B: wall). Floor on row 13 round the
# hole; a step up to row 10, the L0 door's ledge row.
def nursery_access() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    c.fill(1, 10, 5, 12)                        # step to the L0 door's ledge (specs/12i: under all of it, the 6 blocks
                                                # Canvas.door_gap draws: columns 4-5 left a 2-row pocket)
    return Shape(c)


# --- P6 Plaza Access (2x1) -----------------------------------------------------------------------------------------------
# From the Vault (R0, region B: wall) down to the plaza's one-way T1 door (B0). Floor on row 13, a step to row 10 for the
# future R0 door.
def plaza_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 12)
    c.fill(26, 10, 30, 12)                      # specs/12i: under the whole R0 ledge (column 26 left a 2-row pocket)
    return Shape(c)


# --- P7 Piston Tunnel (2x1) ----------------------------------------------------------------------------------------------
# Under the plaza: Samus drops in through the T1 door onto its platform (row 6), in a chamber whose floor (row 10) is the
# R0 door's ledge row (the Training Chamber, region C: wall until then, Prime's Morph Ball door).
def piston_tunnel() -> Shape:
    c = Canvas(2, 1)
    c.carve(14, 1, 30, 9)
    c.fill(14, 1, 17, 4)                        # the piston's housing over the west end
    return Shape(c)


# --- P9 Ruined Shrine (3x1) ----------------------------------------------------------------------------------------------
# Prime's round shrine: a bowl with a half-pipe floor, the Plated Beetle's arena; the Morph Ball on the floor (decision B:
# a missile there), a missile over the half-pipe, a missile in the lower tunnel behind a bomb block. Here: the R0 door's
# terrace (row 10) east, the bowl floor on row 13, the west terrace (row 10) with the L0 door (to the Tower of Light Access,
# a wave door); under the west terrace a 1-row tunnel (row 12) shut by a bomb block, the missile at its end; a floating
# ledge (row 4) over the middle of the bowl, 8 rows over its floor (Space Jump).
SHRINE_BOMB = (9, 12)


def ruined_shrine() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 1, 46, 9)
    c.carve(10, 10, 37, 12)                     # the bowl
    c.carve(4, 12, 9, 12)                       # the lower tunnel (the bomb block at its mouth)
    c.fill(22, 4, 26, 4)                        # the half-pipe's ledge
    for x in (2, 44):
        c.fill(x, 1, x + 1, 2)                  # the shrine's corners
    return Shape(c, blocks=[bomb_block(*SHRINE_BOMB)])


# --- P15 Tower of Light Access (2x1) -------------------------------------------------------------------------------------
def tower_of_light_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    c.fill(12, 8, 19, 9)                        # a raised stretch (2 blocks)
    c.fill(13, 3, 18, 3)
    return Shape(c)


# --- P21 Tower of Light (3x4) --------------------------------------------------------------------------------------------
# Prime's tower: a tall shaft of ledges (the Wavebuster at the top in Prime: no SM item, decision B). Here the R0 door (to
# the access) is at the top, the L3 door (Tower Chamber) at the bottom: from the R0 ledge (row 10, widened to column 40)
# ten platforms of 8 blocks zigzag down 5 rows at a time (east x 32-39, tops 15-55; west x 24-31, tops 20-60) to the floor
# (row 62); the L3 ledge (row 58) is 4 over it. 5 rows a step, not 4: a platform 8 rows over the one she jumps from would
# cover the column she takes off from (smlib/reach.py: the climb needs a block of headroom over her head), 10 rows does not.
# Prime's water at the tower's foot stays dry (the Tallon's rule for pools; epic question 7).
TOWER_FLOOR = 62


def tower_of_light() -> Shape:
    c = Canvas(3, 4)
    c.carve(1, 1, 46, TOWER_FLOOR - 1)
    c.fill(40, 10, 46, 10)                      # the R0 door's ledge, widened west
    for k, top in enumerate(range(15, TOWER_FLOOR, 5)):
        x0 = 32 if k % 2 == 0 else 24
        c.fill(x0, top, x0 + 7, top)
    for y in range(4, 52, 8):                   # the tower's ribs on the west wall (over the L3 door)
        c.fill(1, y, 2, y + 1)
    return Shape(c)


# --- P27 Tower Chamber (1x1) ---------------------------------------------------------------------------------------------
# Prime: the Lifegiver artifact's chamber (artifacts out, epic decision 1): an empty shrine behind the wave door.
def tower_chamber() -> Shape:
    c = Canvas(1, 1)
    c.carve(2, 3, 14, 9)
    c.fill(4, 8, 6, 9)                          # the empty pedestal
    return Shape(c)


# --- region B (specs/12i): the north wing -------------------------------------------------------------------------------
# Prime's loop north of the Main Plaza: Nursery Access -> Eyon Tunnel -> Ruined Nursery (Save Station 1) -> North Atrium ->
# Ruined Gallery (Map Station) -> Totem Access -> Hive Totem -> Transport Access North -> Transport to Magmoor North ->
# Vault Access -> Vault -> Plaza Access -> (one way) Main Plaza. Same rules as region A; Prime's pools (the Gallery's poison
# water, the Hive Totem's and the Totem Access') stay dry (epic question 7, the Tallon's rule). Items behind geometry:
# Morph Ball tunnels (the Gallery's "Tunnel", the Transport Access North's ball hole) and tunnels shut by a bomb block (the
# Vault's cage and its three bomb slots, the Ruined Nursery's wall puzzle, the Gallery's missile wall: the SM has no block
# only missiles break, specs/12i).
DOOR_STEP = 12   # rows 11-12 under a side door's ledge (row 10) filled: a 3-block step down to a floor on row 13


def under_ledges(c: Canvas, left: bool, right: bool) -> None:
    """Fill the rows under the side doors' ledges (row 10, 6 blocks: Canvas.door_gap) down to the floor on row 13."""
    if left:
        c.fill(1, 11, 5, DOOR_STEP)
    if right:
        c.fill(c.w - 6, 11, c.w - 2, DOOR_STEP)


# --- P10 Eyon Tunnel (2x1) ----------------------------------------------------------------------------------------------
# Prime: a dark winding tunnel lined with Eyons (eyes in the walls) between the Nursery Access (R0) and the Ruined Nursery
# above it (T0). Here: the tunnel on rows 2-9 (floor 10, the R0 door's ledge row), the T0 door's platform (row 6) in the west
# screen (the jump onto it from beside it wants 8 rows of air over the floor: smlib/reach.py), the roof dropping in the
# middle (a bend) and a stub hanging from it; the eye (tools/chozo/enemies.py) is set in the west end wall.
EYON_STUB = (20, 2, 21, 6)


def eyon_tunnel() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 2, 30, 9)
    c.fill(*EYON_STUB)
    c.fill(13, 2, 16, 4)                        # the bend: the roof lower (5 rows of headroom)
    c.fill(26, 2, 30, 4)
    return Shape(c)


# --- P16 Ruined Nursery (2x1) -------------------------------------------------------------------------------------------
# Prime: the Chozo nursery, a round hall with the Save Station 1 door (R0), the North Atrium's (L0) and the Eyon Tunnel's
# floor door (B1); its missile behind the "wall puzzle" (Morph Ball and Bombs). Here: the hall on rows 1-12 (floor 13), steps
# under the side doors' ledges, a dais in the middle (rows 9-12, a 4-block climb) with a 1-row tunnel at its foot shut by a
# bomb block on its west face, the missile at its far end.
NURSERY_BOMB = (9, 12)


def ruined_nursery() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 1, 30, 12)
    under_ledges(c, True, True)
    c.fill(9, 9, 17, 12)                        # the dais
    c.carve(9, 12, 14, 12)                      # its tunnel (the bomb block at its mouth, the missile at 14)
    for x in (5, 24):
        c.fill(x, 1, x + 2, 2)                  # the nursery's roof beams
    return Shape(c, blocks=[bomb_block(*NURSERY_BOMB)])


# --- P22 Save Station 1 (1x1) -------------------------------------------------------------------------------------------
# Prime's first save room of the Chozo: the door (L0) to the Ruined Nursery, the station in the middle. Load station 1 of
# area 1 (tools/areas.py CHOZO).
SAVE_STATION_1 = (8, 13)   # (x, floor) of the save pedestal's left block


def save_station_1() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    under_ledges(c, True, False)
    return Shape(c, save=SAVE_STATION_1)


# --- P23 North Atrium (2x1) ---------------------------------------------------------------------------------------------
# Prime: a curving hall up from the Ruined Nursery (R0) to the Ruined Gallery (T0). Here: the hall on rows 2-9 (floor 10), a
# raised stretch in the middle, the T0 door's platform (row 6) in the west screen.
def north_atrium() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 2, 30, 9)
    c.fill(17, 8, 23, 9)                        # raised stretch (2 blocks)
    c.fill(18, 2, 22, 3)
    return Shape(c)


# --- P28 Ruined Gallery (2x1) -------------------------------------------------------------------------------------------
# Prime: a hall of Chozo murals over a pool of poison water (dry here), with the Map Station door behind a missile shield
# (L0, data), the Totem Access door (R0) and the North Atrium's floor door (B1); two missiles: "Tunnel" (a Morph Ball tunnel
# at the bottom) and the one behind a missile wall. Here: the hall on rows 1-12 (floor 13), the dry pool (rows 13-14, floor on
# the room's last row) and, off its two ends, 1-row tunnels: west under the floor, open (Morph Ball); east behind a bomb
# block (the missile wall: specs/12i).
GALLERY_POOL = (8, 17)
GALLERY_BOMB = (18, 14)


def ruined_gallery() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 1, 30, 12)
    under_ledges(c, True, True)
    x0, x1 = GALLERY_POOL
    c.carve(x0, 13, x1, 14)                     # the dry pool
    c.carve(3, 14, x0 - 1, 14)                  # "Tunnel": its missile at the far end (3, 14)
    c.carve(x1 + 1, 14, x1 + 2, 14)             # the missile wall's niche: the bomb block, the missile (19, 14)
    for x in (10, 15):
        c.fill(x, 1, x + 1, 3)                  # mural pillars
    return Shape(c, blocks=[bomb_block(*GALLERY_BOMB)])


# --- P34 Map Station (1x1) ----------------------------------------------------------------------------------------------
# Prime's Chozo map room, behind the Ruined Gallery's missile shield (its R0 door). The SM map station (PLM $B6D3, as the
# frigate's Map Facility, specs 4): Samus walks into its terminal from the east, standing on the floor (row 13).
MAP_STATION = (5, 13)


def map_station() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    under_ledges(c, False, True)
    c.map_station(*MAP_STATION)
    return Shape(c, map_station=MAP_STATION)


# --- P33 Totem Access (2x1) ---------------------------------------------------------------------------------------------
# Prime: a passage from the Gallery (L0) to the Hive Totem (R0) through shallow water with Fire Fleas. Here: the hall on rows
# 3-9 (floor 10) with a dry dip in the middle.
def totem_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    c.carve(11, 10, 20, 11)                     # the dry dip (2 blocks)
    for x in (8, 23):
        c.fill(x, 3, x + 1, 4)
    return Shape(c)


# --- P36 Hive Totem (3x1) -----------------------------------------------------------------------------------------------
# Prime: the Hive Mecha's room (bosses later, epic decision 3): the totem in the middle of a pool, the Missile Launcher at
# its foot (Prime's "Lower Totem Part"); the door to the Transport Access North (R0) behind a missile shield on both sides
# (data). Here: the hall on rows 1-12 (floor 13), the totem (columns 22-25) up to row 9 (a 4-block climb over it), the
# missile on its top (decision B: a Missile Expansion, our missiles exist since the Tallon), dry pools both sides of it.
TOTEM = (22, 25, 9)


def hive_totem() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 1, 46, 12)
    under_ledges(c, True, True)
    x0, x1, top = TOTEM
    c.carve(12, 13, x0 - 1, 14)                 # the dry pool, west of the totem
    c.carve(x1 + 1, 13, 35, 14)                 # and east of it
    c.fill(x0, top, x1, 14)                     # the totem
    for x in (6, 40):
        c.fill(x, 1, x + 2, 3)                  # the hive's combs hanging from the roof
    return Shape(c)


# --- P30 Transport Access North (3x1) -----------------------------------------------------------------------------------
# Prime: a hall from the Hive Totem (L0, missile shield on both sides) to the Magmoor transport (R0); crates; the Energy Tank
# in a cubby reached through a Morph Ball hole. Here: the hall on rows 3-9 (floor 10), crates, a pit (columns 22-23, 2 deep)
# and a 1-row tunnel east from its bottom under the floor, the E-tank at its end.
TAN_PIT = (22, 23)


def transport_access_north() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 3, 46, 9)
    c.fill(13, 8, 14, 9)                        # crates
    c.fill(34, 9, 35, 9)
    x0, x1 = TAN_PIT
    c.carve(x0, 10, x1, 11)                     # the pit
    c.carve(x1 + 1, 11, x1 + 5, 11)             # the ball hole's tunnel, the E-tank at its end (28, 11)
    return Shape(c)


# --- P24 Transport to Magmoor Caverns North (1x2) -----------------------------------------------------------------------
# Prime's elevator down to the Magmoor Caverns: decorative until specs/17e (epic 12, decision 6). The Transport Access North's
# door (L0) up, the Vault Access' (L1) down, the Sun Tower's (R0). Here: the upper hall (rows 3-9, floor 10 on both sides) over
# a well (columns 6-9) down to the lower hall (floor 26), steps of 4 up the well; the elevator's pad is the lower floor under
# the well. specs/17e: it rides down to the Magmoor's P0: the platform's two blocks (SHAFT_X, the vanilla x 128) on that
# floor and a 2-block shaft under them to the bottom row (as the Tallon's ride=True pads).


def transport_magmoor_north() -> Shape:
    c = Canvas(1, 2)
    c.carve(1, 3, 14, 25)
    c.fill(1, 10, 5, 10)                        # the upper floor west of the well (the L0 door's ledge)
    c.fill(10, 10, 14, 10)                      # and east of it (the future R0's)
    for x0, x1, top in ((10, 12, 22), (6, 7, 18), (8, 9, 14)):
        c.fill(x0, top, x1, top)                # the steps up the well
    c.carve(SHAFT_X, 26, SHAFT_X + 1, 31)       # specs/17e: the platform's blocks and the shaft down to the bottom row
    return Shape(c, elevator=Elevator(SHAFT_X, 26, up=False))


# --- P17 Vault Access (4x1) ---------------------------------------------------------------------------------------------
# Prime: a long hall from the Magmoor transport (R0) to the Vault under its east end (B3). Here: the hall on rows 3-12 (floor
# 13) with ribs on the roof, a step under the R0 door's ledge.
def vault_access() -> Shape:
    c = Canvas(4, 1)
    c.carve(1, 3, 62, 12)
    under_ledges(c, False, True)
    for x in range(8, 50, 10):
        c.fill(x, 3, x + 1, 4)
    return Shape(c)


# --- P11 Vault (3x1) ----------------------------------------------------------------------------------------------------
# Prime: the Chozo vault: a sealed cage with a missile, opened by bombs in its three Morph Ball slots; the Plaza Access door
# (L0) and the Vault Access' ceiling door (T0) in the west. Here: the hall on rows 1-12 (floor 13), the west end raised to
# the L0 door's ledge (row 10, out to column 15) under the T0 door's platform (row 6), the cage in the east: a block (rows
# 9-12) with a 1-row tunnel at its foot shut by a bomb block on its west face, the missile at its far end.
VAULT_CAGE = (28, 38)
VAULT_BOMB = (28, 12)


def vault() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 1, 46, 12)
    c.fill(1, 10, 15, 12)                       # the raised west end: from it a jump onto the T0 door's platform
    x0, x1 = VAULT_CAGE
    c.fill(x0, 9, x1, 12)                       # the cage
    c.carve(x0, 12, x0 + 6, 12)                 # its tunnel (the bomb block at its mouth, the missile at 34)
    return Shape(c, blocks=[bomb_block(*VAULT_BOMB)])


# --- region C (specs/12j): the Ruined Fountain, the Arboretum, the Sunchamber and the Sun Tower -------------------------
# Prime's south-east wing: from the Ruined Fountain Access (region A) to the Ruined Fountain, down to the Meditation Fountain
# and the Magma Pool (hot: Prime's only "Area Damage" of the Chozo) to the Training Chamber Access and the Training Chamber
# (back to the Piston Tunnel, region A); east through the Arboretum Access to the Arboretum, up to the Sunchamber Lobby,
# the Sunchamber Access and the Sunchamber (Flaahgra's arena: the Varia Suit, the boss later), out through the Sun Tower
# Access and the Sun Tower down to the Magmoor transport (region B); down from the Arboretum to the Gathering Hall Access, the
# Gathering Hall and Save Station 2. Same rules as regions A and B; Prime's pools (the fountains', the Arboretum's, the
# Gathering Hall's) and the Magma Pool's lava stay dry (epic question 7). Prime's movement items mapped to the Tallon's
# (decision B, as 12f): the Spider Ball tracks (the fountain's missile, the Training Chamber's E-tank, the Sun Tower's climb)
# = Space Jump ledges; the bomb slots and the piston = a Morph Ball tunnel shut by a bomb block; the Gathering Hall's bomb
# gate = a bomb block; the Magma Pool's power bomb wall = a power bomb block.

# --- P8 Ruined Fountain (2x1) -------------------------------------------------------------------------------------------
# Prime: a bath hall round a fountain (its pool poison or clean: "Check Varia Suit" swaps the water, a hazard of the pool,
# dry here), the Ruined Fountain Access door (L0), the Arboretum Access' (R0) and the Meditation Fountain's floor door (B0);
# the missile at the top of a Spider Ball track over the fountain. Here: the hall on rows 1-12 (floor 13), steps under the
# side doors' ledges, the dry basin in the middle (1 deep) and over it the track's top: a ledge on row 4, 9 rows over the
# floor and far from the side ledges (Space Jump), the missile on it.
FOUNTAIN_LEDGE = (14, 19, 4)    # columns and row of the track's top ledge


def ruined_fountain() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 1, 30, 12)
    under_ledges(c, True, True)
    c.carve(14, 13, 19, 13)                     # the fountain's dry basin
    x0, x1, y = FOUNTAIN_LEDGE
    c.fill(x0, y, x1, y)                        # the Spider Ball track's top (Space Jump)
    for x in (4, 26):
        c.fill(x, 1, x + 1, 2)                  # the bath's roof beams
    return Shape(c)


# --- P13 Arboretum Access (3x2) -----------------------------------------------------------------------------------------
# Prime: a winding passage from the fountain (L0) to the Arboretum (R0, a missile shield on this side), Metarees hanging
# from its roof. Here: the top hall (rows 3-9, floor 10) from door to door is broken by a pit down to a lower hall (floor
# 28): down a stair of 4-block steps on the west, up the same on the east (a U, Prime's bend).
def arboretum_access() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 3, 46, 9)                        # the top hall
    c.carve(13, 10, 34, 27)                     # the pit and the lower hall
    for x0, top in ((17, 24), (15, 20), (13, 16), (29, 24), (31, 20), (33, 16)):
        c.fill(x0, top, x0 + 1, 27)             # the steps (west down, east up)
    return Shape(c)


# --- P19 Arboretum (3x3) ------------------------------------------------------------------------------------------------
# Prime: the overgrown courtyard: the Arboretum Access door (L0) high in the west, the Gathering Hall Access' (R2) low in the
# east, the Sunchamber Lobby's (R0) high in the east behind a missile shield, a breakable block and a rune gate (the gate
# opens by scanning: no SM item, left out). Here: the courtyard (floor 42, a dry pool in the middle), a zigzag of ledges up
# the west side from the floor to the L0 ledge (5 rows a step, as the Tower of Light), the tree's crown (rows 10-12) east of
# them, reached from the zigzag by a branch; from the crown a 1-row Morph Ball tunnel (row 9) shut by a bomb block (Prime's
# breakable block) into the walled R0 chamber: Morph Ball, Bombs (and the missiles of the red door).
ARBORETUM_BOMB = (37, 9)
ARBORETUM_CROWN = (26, 35, 10)   # columns and top row of the tree's crown


def arboretum() -> Shape:
    c = Canvas(3, 3)
    c.carve(1, 1, 46, 41)                       # the courtyard (floor 42, the R2 door's ledge row)
    c.carve(16, 42, 38, 43)                     # the dry pool
    for k, top in enumerate(range(37, 11, -5)):   # 37, 32, 27, 22, 17, 12
        x0 = 14 if k % 2 == 0 else 6
        c.fill(x0, top, x0 + 7, top)            # the zigzag up the west side
    c.fill(22, 12, 25, 12)                      # the branch from the zigzag's 17 to the crown (high enough to walk
                                                # under it off the 17's east end, down to the floor)
    x0, x1, top = ARBORETUM_CROWN
    c.fill(x0, top, x1, top + 2)                # the crown
    for x in (28, 33):
        c.fill(x, top + 3, x, top + 8)          # vines hanging from it
    c.fill(36, 1, 46, 13)                       # the rock round the R0 door's chamber
    c.carve(38, 6, 46, 9)                       # the chamber (the door's ledge row 10)
    c.carve(36, 9, 37, 9)                       # the tunnel from the crown (the bomb block at 37)
    return Shape(c, blocks=[bomb_block(*ARBORETUM_BOMB)])


# --- P25 Sunchamber Lobby (2x1) -----------------------------------------------------------------------------------------
# Prime: a short hall up from the Arboretum (L0) to the Sunchamber Access (T0). Here: the hall on rows 2-9 (floor 10), the T0
# door's platform (row 6; Samus walks under it from the L0 door and jumps on it from its east end), a raised stretch.
def sunchamber_lobby() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 2, 30, 9)
    c.fill(19, 8, 25, 9)                        # raised stretch (2 blocks)
    c.fill(20, 2, 24, 3)
    return Shape(c)


# --- P31 Sunchamber Access (2x1) ----------------------------------------------------------------------------------------
# Prime: a vine-covered passage from the lobby (B1, the floor door) west to the Sunchamber (L0). Here: the hall on rows 1-12
# (floor 13), a step under the L0 ledge, crates and vines.
def sunchamber_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 1, 30, 12)
    under_ledges(c, True, False)
    c.fill(11, 11, 12, 12)                      # crates
    for x in (9, 16):
        c.fill(x, 1, x, 4)                      # vines
    return Shape(c)


# --- P37 Sunchamber (4x3) -----------------------------------------------------------------------------------------------
# Prime: Flaahgra's arena: a sunlit bowl with its four bomb slots in pits, the Varia Suit appearing where Flaahgra falls; the
# Sunchamber Access door (R2) low in the east, the Sun Tower Access' (L0) high in the west, shut during the fight ("Actor Door
# Lock"). specs/14c: Flaahgra = the Spore Spawn (tools/chozo/bosses.py), whose code assumes the vanilla room ($8F:9DC7, 1x3):
# its stalk at x 128 and its death spot (128, 624) ($A5:E87C), its spores born at y 520 over x 32-224 ($86:DCD4), the
# roof's 2x2 blocks at (7, 30) turned to air by a PLM at its death ($A5:EE30: $B78F). So its pit is the west screen of the
# bottom row, as vanilla's: rows 32-43 (floor 44, two below the R2 ledge row: the sunlit bowl), cols 1-15, under a roof of
# rock up to the L0 door's gallery (floor 10, rows 1-9), with a notch over the stalk where that PLM works (air already:
# nothing changes when it runs; (7-8, 30-31)). The Varia appears on the pit's floor under the husk, where Flaahgra falls in
# Prime (SUNCHAMBER_VARIA: the husk's lowest shell ends at y 679, the item's block starts at 688).
# East of the pit the sunlit hall (rows 1-41, floor 42 = the R2 ledge row, two dry bomb-slot pits) and a zigzag of ledges
# (5 rows a step, as 12j's) up its west side, against the pit's roof, to the L0 gallery.
SUNCHAMBER_PIT = (1, 15, 32, 44)       # columns, top row and floor row of Flaahgra's pit
SUNCHAMBER_NOTCH = (7, 30, 8, 31)      # the roof's blocks the Spore Spawn's death PLM clears ($B78F at (7, 30), 2x2)
SUNCHAMBER_VARIA = (8, 43)             # where the Varia Suit appears (tools/chozo/items.py, the arena's prize)


def sunchamber() -> Shape:
    c = Canvas(4, 3)
    x0, x1, top, floor = SUNCHAMBER_PIT
    c.carve(x1 + 1, 1, 62, 41)                  # the sunlit hall (floor 42)
    c.carve(1, 1, x1, 9)                        # the L0 door's gallery (floor 10) over the pit's roof
    c.carve(x0, top, x1, floor - 1)             # the pit (the arena)
    c.carve(*SUNCHAMBER_NOTCH)                  # the notch over the stalk
    for p0 in (36, 48):
        c.carve(p0, 42, p0 + 3, 43)             # the bomb slots' pits (dry)
    for k, row in enumerate(range(37, 11, -5)):   # 37, 32, 27, 22, 17, 12
        x = 24 if k % 2 == 0 else 16
        c.fill(x, row, x + 7, row)
    for x in range(34, 60, 8):
        c.fill(x, 1, x + 1, 4)                  # the sun's rays from the roof
    return Shape(c)


# --- P35 Sun Tower Access (5x1) -----------------------------------------------------------------------------------------
# Prime: a long passage from the Sunchamber (R0) to the Sun Tower (L0) through shallow water (dry here). Here: the hall on rows
# 3-9 (floor 10), two dry channels, arches.
def sun_tower_access() -> Shape:
    c = Canvas(5, 1)
    c.carve(1, 3, 78, 9)
    for x0 in (20, 50):
        c.carve(x0, 10, x0 + 11, 11)            # the dry channels (2 deep)
    for x in range(10, 75, 12):
        c.fill(x, 3, x + 2, 3)                  # arches
    return Shape(c)


# --- P29 Sun Tower (2x3) ------------------------------------------------------------------------------------------------
# Prime: a tall tower from the Sun Tower Access door (at its top) down to the Magmoor transport's (at its foot): coming from
# the Sunchamber Samus drops down it; going up wants the Spider Ball track. Here the map puts the Magmoor door (L1) over the
# Sun Tower Access' (R2), so the drop is kept by the shape: from the R2 ledge (row 42) a zigzag of ledges up the east hall
# (5 rows a step) to the top passage (floor 8), west along it and down the west shaft onto the L1 door's floor (row 26). Back
# up the shaft (18 rows) = Prime's Spider Ball track = Space Jump (chozo/rooms.py GATES: the R2 door behind it).
SUN_TOWER_FLOOR = 42


def sun_tower() -> Shape:
    c = Canvas(2, 3)
    c.carve(1, 1, 30, 7)                        # the top passage (its floor row 8 on the wall between)
    c.carve(1, 8, 9, 25)                        # the west shaft down to the L1 door (floor 26)
    c.carve(16, 8, 30, SUN_TOWER_FLOOR - 1)     # the east hall (floor 42, the R2 door's ledge row)
    for k, top in enumerate(range(37, 11, -5)):   # 37, 32, 27, 22, 17, 12
        x0 = 23 if k % 2 == 0 else 16
        c.fill(x0, top, x0 + 6, top)
    return Shape(c)


# --- P39 Save Station 2 (1x1) -------------------------------------------------------------------------------------------
# Prime's second save room of the Chozo, off the Gathering Hall (R0, the missile shield on the hall's side). Load station 2
# of area 1 (tools/areas.py chozo_stations).
SAVE_STATION_2 = (6, 13)   # (x, floor) of the save pedestal's left block


def save_station_2() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    under_ledges(c, False, True)
    return Shape(c, save=SAVE_STATION_2)


# --- P26 Gathering Hall Access (2x1) ------------------------------------------------------------------------------------
# Prime: a short passage with steam vents from the Arboretum (L0) to the Gathering Hall (R0). Here: the hall on rows 3-9
# (floor 10), the vents' grates.
def gathering_hall_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    for x in (11, 19):
        c.fill(x, 9, x + 1, 9)                  # vent grates (1 block)
    c.fill(14, 3, 17, 4)
    return Shape(c)


# --- P32 Gathering Hall (3x2) -------------------------------------------------------------------------------------------
# Prime: a tall hall over a pool (poison or clean water, dry here) with the Gathering Hall Access door (L0) and Save Station
# 2's (L1) on the west, the Watery Hall Access' (R0) and the East Atrium's (R1) on the east (region D: walls until 12k, their
# floors at the doors' ledge rows); its missile up high behind a bomb gate. Here: the lower floor (row 26) with the dry pool,
# two galleries on row 10 (west under the L0 door, east under the future R0), a stair of platforms up to each, the missile
# in a cage on the east gallery: a 1-row tunnel shut by a bomb block (Prime's bomb gate).
GATHERING_CAGE = (37, 41)      # columns of the cage on the east gallery (rows 6-9; the future R0 door's 44-47 kept clear)
GATHERING_BOMB = (37, 9)


def gathering_hall() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 1, 46, 25)                       # the hall (lower floor row 26)
    c.carve(30, 26, 40, 27)                     # the dry pool
    c.fill(1, 10, 9, 10)                        # the west gallery (the L0 door's ledge, widened)
    c.fill(34, 10, 46, 10)                      # the east gallery (the future R0 door's ledge)
    c.fill(12, 22, 29, 22)                      # a plinth in the middle (4 over the floor; wider than the steps over it:
                                                # a step 8 rows over her takes the headroom of a 4-row climb)
    for x0, top in ((14, 18), (10, 14)):        # the west stair up from it: each step further west
        c.fill(x0, top, x0 + 3, top)
    for x0, top in ((26, 18), (30, 14)):        # the east stair: each step further east
        c.fill(x0, top, x0 + 3, top)
    x0, x1 = GATHERING_CAGE
    c.fill(x0, 6, x1, 9)                        # the cage
    c.carve(x0, 9, x1 - 1, 9)                   # its tunnel (the bomb block at its mouth, the missile at its far end)
    return Shape(c, blocks=[bomb_block(*GATHERING_BOMB)])


# --- P12 Training Chamber (2x1) -----------------------------------------------------------------------------------------
# Prime: the Chozo's training hall: the Piston Tunnel's Morph Ball door (L0) opens on a piston moved by two bomb slots, the
# Training Chamber Access door (R0, a wave door; Prime's "Actor Door Lock" is the Chozo Ghosts' fight, an event layer: out),
# the Energy Tank up a Spider Ball track ("Powerup Room"). Here: the L0 door opens into the piston's chamber (rows 6-9), a
# 1-row Morph Ball tunnel (row 9) shut by a bomb block leads east into the hall (rows 1-12, floor 13), onto a ledge (row 10)
# at its mouth; the E-tank on a ledge (row 4) high over the hall's middle (the track's top: Space Jump).
TRAINING_BOMB = (7, 9)
TRAINING_LEDGE = (18, 21, 4)   # columns and row of the E-tank's ledge (3 rows of air over it: on row 3 she could not stand)


def training_chamber() -> Shape:
    c = Canvas(2, 1)
    c.carve(11, 1, 30, 12)                      # the hall
    under_ledges(c, False, True)
    c.carve(1, 6, 6, 9)                         # the piston's chamber at the L0 door
    c.carve(7, 9, 10, 9)                        # the tunnel (the bomb block at its west end)
    c.fill(11, 10, 13, 12)                      # the ledge at its mouth (a 3-block climb from the floor)
    x0, x1, y = TRAINING_LEDGE
    c.fill(x0, y, x1, y)
    return Shape(c, blocks=[bomb_block(*TRAINING_BOMB)])


# --- P18 Training Chamber Access (2x1) ----------------------------------------------------------------------------------
# Prime: a passage between two wave doors (the Magma Pool's, R0, and the Training Chamber's, L0); its missile at the end of
# a Morph Ball path (a path camera, under the leaves). Here: the hall on rows 3-9 (floor 10), a hole (2 deep) and a 1-row
# tunnel east from its bottom, the missile at its end.
TCA_HOLE = (12, 13)


def training_chamber_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    x0, x1 = TCA_HOLE
    c.carve(x0, 10, x1, 11)                     # the hole
    c.carve(x1 + 1, 11, x1 + 5, 11)             # the tunnel, the missile at its end (18, 11)
    c.fill(22, 3, 25, 4)
    return Shape(c)


# --- P20 Magma Pool (3x1) -----------------------------------------------------------------------------------------------
# Prime: a lava pool (dry here: a sunken basin) crossed by grapple points; the room is hot (Prime's "SpecialFunction Area
# Damage", the only one of the Chozo: chozo/rooms.py HOT_ROOMS, the Varia Suit); the Power Bomb expansion at the Training
# Chamber Access' end behind a wall a power bomb breaks. Here: the hall on rows 3-9 over the basin (rows 10-14, 5 deep: in
# and out on foot; the grapple points hang from the roof as scenery), the doors' ledges on row 10; in the basin's west wall
# a 1-row tunnel shut by a power bomb block, the expansion at its end.
MAGMA_PB = (9, 14)


def magma_pool() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 3, 46, 9)
    c.carve(10, 10, 39, 14)                     # the basin (floor 15)
    c.carve(6, 14, 9, 14)                       # the tunnel (the power bomb block at its mouth), the expansion at (6, 14)
    for x in (18, 30):
        c.fill(x, 3, x + 1, 4)                  # the grapple points' mounts
    return Shape(c, blocks=[power_bomb_block(*MAGMA_PB)])


# --- P14 Meditation Fountain (2x1) --------------------------------------------------------------------------------------
# Prime: a quiet fountain room (its pool poison or clean, dry here) between the Magma Pool (L0) and the Ruined Fountain
# above (T1, the ceiling door). Here: the hall on rows 2-9 (floor 10), the T1 door's platform (row 6), the fountain's rim.
def meditation_fountain() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 2, 30, 9)
    c.fill(9, 9, 13, 9)                         # the fountain's rim (1 block)
    c.fill(10, 2, 12, 3)
    return Shape(c)


# --- region D (specs/12k): the Watery Hall, the Energy Core, the Burn Dome and the Furnace ------------------------------
# Prime's east wing, past the Gathering Hall (region C): its R0 door to the Watery Hall Access and the Watery Hall (the
# Charge Beam) and on, past the Watery Hall's breakable block, to the Dynamo Access and the Dynamo; its R1 door to the East
# Atrium, the Energy Core Access and the Energy Core, up its Morph Ball door to the Burn Dome Access and the Burn Dome (the
# Incinerator Drone's arena: the boss later), and through the Energy Core's bomb-slot door to the West Furnace Access and the
# Furnace (whose doors to region E stay walls until 12l, their floors already on the doors' ledge rows). Same rules as
# regions A-C; Prime's pools (the Watery Hall's, the Energy Core's, the Burn Dome's) stay dry (epic question 7). Prime's
# locks mapped to the Tallon's items (decision B, as 12f/12i/12j): the missile walls (Watery Hall Access, Dynamo) = a bomb
# block (12i's rule: the SM has no block only missiles break); the breakable blocks (Watery Hall, Burn Dome) and the
# Furnace's breakable floor = a Morph Ball tunnel shut by a bomb block; the Energy Core's bomb slots (they open its door to
# the West Furnace Access) = a tunnel with a bomb block in front of that door; the Spider Ball tracks (the Dynamo's, the
# Furnace's) = Space Jump ledges with 3 rows of air over them (she stands there: validate's headroom rule, specs/12k).

# --- P38 Watery Hall Access (3x1) ---------------------------------------------------------------------------------------
# Prime: a passage from the Gathering Hall (L0) to the Watery Hall (R0, a missile shield on this side), Metarees on its roof;
# its missile low in a niche behind a missile wall (only missiles break it in Prime). Here: the hall on rows 3-9 (floor 10),
# a sunken stretch in the middle (3 deep, floor 13) and in its east wall a 1-row tunnel shut by a bomb block, the missile at
# its far end.
WHA_BOMB = (32, 12)


def watery_hall_access() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 3, 46, 9)
    c.carve(16, 10, 31, 12)                     # the sunken stretch (floor 13)
    c.carve(32, 12, 35, 12)                     # the missile wall's tunnel (the bomb block at its mouth, the missile at 35)
    for x in (9, 24, 40):
        c.fill(x, 3, x + 1, 3)                  # roof beams (the Skrees hang between them)
    return Shape(c, blocks=[bomb_block(*WHA_BOMB)])


# --- P41 Watery Hall (4x2) ----------------------------------------------------------------------------------------------
# Prime: a long flooded hall (its water clean or poison, dry here): the Watery Hall Access door (L1) low in the west, the
# Dynamo Access' (R0) high in the east behind a missile shield and the breakable block next to the Charge Beam's ledge; the
# Charge Beam behind a gate opened by scanning four runes (Scan Visor: no SM item, the gate is open), its missile at the far
# end of the pool, down a Morph Ball path. Here: the lower hall (floor 26) with the dry pool (3 deep), a 1-row tunnel off the
# pool's east end (the missile at its end); a stair of platforms (4 rows a step, each further east) up to the upper gallery
# (row 10), the Charge Beam on its pedestal there; at the gallery's east end the R0 door's chamber (rows 7-9 under the rock),
# entered only by a 1-row tunnel shut by a bomb block (Prime's breakable block): Morph Ball, Bombs (and the red door).
WATERY_POOL = (20, 50)               # columns of the dry pool (rows 26-28)
WATERY_BOMB = (52, 9)
WATERY_CHARGE = (44, 8)              # the Charge Beam: on the pedestal (row 9), on the gallery (row 10)


def watery_hall() -> Shape:
    c = Canvas(4, 2)
    c.carve(1, 1, 62, 25)                       # the hall (lower floor row 26)
    x0, x1 = WATERY_POOL
    c.carve(x0, 26, x1, 28)                     # the dry pool (floor 29)
    c.carve(x1 + 1, 28, x1 + 6, 28)             # the Morph Ball path off its east end (the missile at 56)
    c.fill(24, 22, 29, 22)                      # the stair up to the gallery: each step 4 higher, further east
    c.fill(28, 18, 31, 18)
    c.fill(32, 14, 35, 14)
    c.fill(36, 10, 62, 10)                      # the upper gallery (the R0 door's ledge row)
    c.fill(43, 9, 45, 9)                        # the Charge Beam's pedestal
    for x in (39, 48):
        c.fill(x, 1, x + 1, 4)                  # the rune gate's posts (the gate itself is open)
    c.fill(52, 1, 62, 8)                        # the rock round the R0 door's chamber
    c.carve(54, 7, 62, 8)                       # the chamber (rows 7-9; the door rows 6-9 come with it)
    c.carve(52, 9, 53, 9)                       # the tunnel (the bomb block at its west mouth)
    return Shape(c, blocks=[bomb_block(*WATERY_BOMB)])


# --- P43 Dynamo Access (1x1) --------------------------------------------------------------------------------------------
# Prime: a short shaft ("monkey shaft") from the Watery Hall (L0) to the Dynamo (R0, a missile shield on this side). Here: the
# hall on rows 3-9 (floor 10), a crate.
def dynamo_access() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 9)
    c.fill(7, 8, 8, 9)                          # a crate (2 blocks)
    return Shape(c)


# --- P45 Dynamo (1x1) ---------------------------------------------------------------------------------------------------
# Prime: a tall round room off the Dynamo Access (L0): a missile behind a breakable wall at its foot (missiles break it in
# Prime) and one at the top of a Spider Ball track. Here: the room on rows 1-12 (floor 13, a step under the L0 ledge); a pit in
# the floor (2 deep) with a 1-row tunnel east from its bottom, shut by a bomb block (the missile wall), the missile at its
# end; a ledge high in the east (row 4, 3 rows of air over it: she stands there), 9 rows over the floor and too far from the
# L0 ledge for a jump: Space Jump (the track).
DYNAMO_PIT = (8, 9)
DYNAMO_BOMB = (10, 14)
DYNAMO_LEDGE = (11, 14, 4)           # columns and row of the track's top


def dynamo() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 1, 14, 12)
    under_ledges(c, True, False)
    x0, x1 = DYNAMO_PIT
    c.carve(x0, 13, x1, 14)                     # the pit
    c.carve(x1 + 1, 14, 13, 14)                 # the tunnel (the bomb block at its mouth, the missile at 13)
    x0, x1, y = DYNAMO_LEDGE
    c.fill(x0, y, x1, y)
    return Shape(c, blocks=[bomb_block(*DYNAMO_BOMB)])


# --- P40 East Atrium (2x1) ----------------------------------------------------------------------------------------------
# Prime: a passage from the Gathering Hall (L0) to the Energy Core Access (R0), Metarees on its roof. Here: the hall on rows
# 3-9 (floor 10), a raised stretch and roof beams.
def east_atrium() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    c.fill(14, 8, 18, 9)                        # raised stretch (2 blocks)
    for x in (8, 23):
        c.fill(x, 3, x + 1, 3)
    return Shape(c)


# --- P42 Energy Core Access (2x1) ---------------------------------------------------------------------------------------
# Prime: a short winding passage from the East Atrium (L0) to the Energy Core (R0), Eyons in its walls; two breakable blocks
# by a Morph Ball crawlspace beside the way (no item or door behind them: left out, specs/12k). Here: the hall on rows 3-9
# (floor 10) under a high vault at its west end (rows 1-2), the roof dropping in the middle (a bend); the eye
# (tools/chozo/enemies.py) in the west end wall at the top of the vault, facing east: Samus is never behind it.
def energy_core_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    c.carve(1, 1, 5, 2)                         # the vault over the L0 door
    c.fill(15, 3, 20, 5)                        # the bend: the roof lower (4 rows of headroom under it)
    c.fill(26, 3, 30, 4)
    return Shape(c)


# --- P44 Energy Core (4x1) ----------------------------------------------------------------------------------------------
# Prime: the hall of the three energy cores, switched on by bombs in three bomb slots, which unlock its door to the West
# Furnace Access (R0, Prime's "Actor Door Lock"); its water (dry here) rises and falls with them; the Burn Dome Access door
# (T3) up a Morph Ball door. Here: the hall on rows 1-12 (floor 13), dry pools, the cores' columns; at the east end a step
# (rows 10-12) under the T3 door's platform (row 6), and the R0 door's chamber (rows 7-9 under the platform, the rock over
# the door) entered only by a 1-row tunnel (row 9) shut by a bomb block: Morph Ball, Bombs (the bomb slots). The Morph Ball
# door is on the Burn Dome Access' side (its floor door's chamber).
ENERGY_CORE_BOMB = (56, 9)
ENERGY_CORE_STEP = (48, 55)          # columns of the step (top row 10) under the T3 platform


def energy_core() -> Shape:
    c = Canvas(4, 1)
    c.carve(1, 1, 62, 12)                       # the hall (floor 13)
    under_ledges(c, True, False)
    for x0, x1 in ((12, 18), (30, 38)):
        c.carve(x0, 13, x1, 14)                 # the dry pools (2 deep)
    for x in (22, 42):
        c.fill(x, 1, x + 1, 5)                  # the cores' columns hanging from the roof
    x0, x1 = ENERGY_CORE_STEP
    c.fill(x0, 10, x1, 12)                      # the step under the platform (a 3-block climb)
    c.fill(56, 7, 57, 12)                       # the chamber's west wall (the tunnel cut through it below)
    c.fill(58, 11, 62, 12)                      # under the chamber (its floor = the R0 ledge row 10)
    c.fill(60, 1, 62, 5)                        # the rock over the door (the platform's east end does not lead into it)
    c.carve(56, 9, 57, 9)                       # the tunnel (the bomb block at its west mouth)
    return Shape(c, blocks=[bomb_block(*ENERGY_CORE_BOMB)])


# --- P46 Burn Dome Access (2x1) -----------------------------------------------------------------------------------------
# Prime: the Morph Ball passage from the Energy Core (B0, its floor door: Prime's Morph Ball door) to the Burn Dome (R0).
# Here: the hall on rows 3-9 (floor 10) in the east; in the west, over the floor door, a closed chamber (rows 7-12): coming up
# the door she rises into it and steers onto the door's east ledge (row 13, Canvas.door_gap); the only way on is a 1-row
# Morph Ball tunnel (row 12) east to a pit in the hall's floor (as the Main Plaza's B0, specs/12f).
BDA_PIT = (18, 19)


def burn_dome_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(18, 3, 30, 9)                       # the hall
    c.carve(3, 7, 13, 12)                       # the chamber over the floor door
    c.carve(14, 12, 17, 12)                     # the Morph Ball tunnel
    x0, x1 = BDA_PIT
    c.carve(x0, 10, x1, 12)                     # the pit she morphs in
    return Shape(c)


# --- P48 Burn Dome (3x1) ------------------------------------------------------------------------------------------------
# Prime: the Incinerator Drone's arena (the boss later, epic decision 3), a dome over a pool (dry here); the Bombs on a stand
# in the middle after the fight (already the Tallon's: decision B, a missile there); a missile behind a breakable block at the
# end of a Morph Ball tunnel; War Wasps from the hives on the roof. Here: the hall on rows 1-12 (floor 13), a step under the
# L0 ledge, the stand in the middle (2 high) with the missile on it, the dry pool, and in the east a block (rows 9-12) with a
# 1-row tunnel at its foot shut by a bomb block, the missile at its far end.
BURN_DOME_STAND = (22, 25, 11)       # columns and top row of the stand (Prime's Bombs)
BURN_DOME_BLOCK = (35, 46)           # columns of the east block
BURN_DOME_BOMB = (35, 12)


def burn_dome() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 1, 46, 12)
    under_ledges(c, True, False)
    x0, x1, top = BURN_DOME_STAND
    c.fill(x0, top, x1, 12)
    c.carve(27, 13, 32, 13)                     # the dry pool (1 deep)
    x0, x1 = BURN_DOME_BLOCK
    c.fill(x0, 9, x1, 12)
    c.carve(x0, 12, x0 + 8, 12)                 # the tunnel (the bomb block at its mouth, the missile at 43)
    for x in (14, 31):
        c.fill(x, 1, x + 2, 2)                  # the hives on the roof
    return Shape(c, blocks=[bomb_block(*BURN_DOME_BOMB)])


# --- P47 West Furnace Access (1x1) --------------------------------------------------------------------------------------
# Prime: a short passage from the Energy Core (L0) to the Furnace (R0). Here: the hall on rows 3-9 (floor 10).
def west_furnace_access() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 9)
    c.fill(6, 3, 9, 4)
    return Shape(c)


# --- P49 Furnace (4x2) --------------------------------------------------------------------------------------------------
# Prime: the Chozo furnace: the West Furnace Access door (L0) high in the west, the East Furnace Access' (B3) under its east end
# and the Crossway Access West's (R0, a Morph Ball door) in the east (region E: walls until 12l, their floors already on the
# doors' ledge rows: the lower floor on row 28 there, the east balcony on row 10); the Energy Tank in the furnace's core under a
# floor the bombs break, a missile at the top of a Spider Ball track over it, half-pipes and Parasites. Here: the upper
# corridor from the L0 door (rows 3-9, floor 10) onto a balcony over the big hall (floor 28); a zigzag of platforms (5 rows a
# step) between the hall's floor and the balcony; in the floor a pit (2 deep) and a 1-row tunnel west from its bottom shut
# by a bomb block, the E-tank at its end; the track's top a ledge high in the hall (row 4, 3 rows of air over it), far
# from the balconies: Space Jump.
FURNACE_FLOOR = 28
FURNACE_PIT = (44, 45)
FURNACE_BOMB = (43, 29)
FURNACE_LEDGE = (46, 50, 4)          # columns and row of the track's top


def furnace() -> Shape:
    c = Canvas(4, 2)
    c.carve(1, 3, 30, 9)                        # the upper corridor from the L0 door
    c.carve(31, 1, 62, FURNACE_FLOOR - 1)       # the hall
    c.fill(31, 10, 36, 10)                      # the west balcony (the corridor's floor, out over the hall)
    for x0, top in ((39, 23), (31, 18), (39, 13)):
        c.fill(x0, top, x0 + 7, top)            # the zigzag up from the floor to the balcony
    x0, x1 = FURNACE_PIT
    c.carve(x0, FURNACE_FLOOR, x1, FURNACE_FLOOR + 1)       # the pit
    c.carve(37, FURNACE_FLOOR + 1, x0 - 1, FURNACE_FLOOR + 1)   # the tunnel west (the bomb block at its mouth, the E-tank at 37)
    x0, x1, y = FURNACE_LEDGE
    c.fill(x0, y, x1, y)
    c.fill(52, 10, 62, 10)                      # the east balcony (the R0 door's ledge row)
    # specs/12l: the R0 door (Crossway Access West) is Prime's Morph Ball door: its chamber (rows 6-9, columns 58-62) under
    # the rock, entered from the balcony only by a 1-row tunnel (row 9, columns 55-57): Morph Ball (and the Space Jump that
    # gets her onto the balcony: Prime's half-pipe and Spider Ball track)
    c.fill(55, 1, 57, 8)
    c.fill(58, 1, 62, 5)
    for x in (52, 58):
        c.fill(x, FURNACE_FLOOR - 4, x + 1, FURNACE_FLOOR - 1)   # the furnace's grates (4-block posts: a climb)
    return Shape(c, blocks=[bomb_block(*FURNACE_BOMB)])


# --- region E (specs/12l): the Hall of the Elders, the Crossway, the Reflecting Pool and the ways out to the Tallon -------
# Prime's south-east wing, past the Furnace (region D): its floor door (B3, Ice-only) down to the East Furnace Access and
# the Hall of the Elders; its Morph Ball door (R0) to the Crossway Access West, the Crossway (Prime's way in before the Ice
# Beam) and down the Elder Hall Access into the Hall; the Hall's statue to the Reflecting Pool Access and the Reflecting
# Pool (flooded here: specs/12l, the Gravity Suit keeps the two elevators in the Tallon's rounds), Save Station 3 and the
# Transport to Tallon East, the Transport Access South and the Transport to Tallon South, the Antechamber (Prime's Ice Beam:
# a missile, decision B). Same rules as regions A-D. Prime has no enemy on layer 0 in the whole region.

# --- P50 East Furnace Access (1x1) ---------------------------------------------------------------------------------------
# Prime: a short passage between two ice doors (the Furnace's, T0 here: the Furnace's floor door, and the Hall's, R0). Here:
# the hall on rows 1-9 (floor 10); coming down the T0 door she lands on its platform (row 6) and drops east to the R0 door.
def east_furnace_access() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 1, 14, 9)
    c.fill(1, 1, 3, 3)                          # rubble in the corner
    return Shape(c)


# --- P51 Crossway Access West (2x1) -------------------------------------------------------------------------------------
# Prime: a Morph Ball half-pipe from the Furnace's Morph Ball door (L0; the tunnel is on the Furnace's side here) to the
# Crossway (R0, a wave door on this side, s12l/dtrig.out). Here: the hall on rows 3-9 (floor 10), the half-pipe's bowl in
# the middle (2 deep).
def crossway_access_west() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    c.carve(11, 10, 20, 11)                     # the half-pipe's bowl
    for x in (9, 22):
        c.fill(x, 3, x + 1, 4)
    return Shape(c)


# --- P52 Hall of the Elders (3x2) ---------------------------------------------------------------------------------------
# Prime: the Chozo statue's hall ("Chozo bowling"): the East Furnace Access door (L0) and the Crossway Access South's (T0) on
# the west, the Elder Hall Access' (R0) up on the east, the Elder Chamber's (R1) low on the east (Prime: under the statue),
# the Reflecting Pool Access' (B2) reached by the statue's "Right" launch from its purple bomb slot; the Energy Tank in an
# alcove under the floor where the "Down" launch drops the ball (the white slot). Here: the hall on rows 1-25 (floor 26), the
# statue's head hanging from the roof in the middle, stairs of platforms (4 rows a step) up to the west balcony
# (row 10: the L0 ledge, the T0 door's platform over it) and the east balcony (row 10: the R0 ledge); the dais (top row 22) on
# the east over the B2 floor door's chamber (rows 23-28), entered only by a 1-row tunnel (row 28) shut by a bomb block (the
# bomb slots) from a pit in the floor; the R1 ledge (row 26) east of the dais; the E-tank at the end of a 1-row tunnel shut by
# a bomb block under the floor (the "Down Launch" alcove).
HALL_FLOOR = 26
HALL_PIT = (30, 31)                  # the pit to the B2 chamber's tunnel (rows 26-28)
HALL_B2_BOMB = (32, 28)
HALL_DAIS = (33, 42, 22)             # walls and top row of the dais over the B2 door
HALL_ETANK_PIT = (14, 15)            # the pit to the E-tank's tunnel (rows 26-27)
HALL_ETANK_BOMB = (13, 27)


def hall_of_the_elders() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 1, 46, HALL_FLOOR - 1)           # the hall
    c.fill(0, 10, 13, 10)                       # the west balcony (the L0 ledge, the T0 door's platform over it)
    c.fill(22, 22, 25, 22)                      # the west stair (each step 4 higher, further west)
    c.fill(18, 18, 21, 18)
    c.fill(14, 14, 17, 14)
    c.fill(26, 1, 29, 6)                        # the statue's head and shoulders, from the roof
    x0, x1, top = HALL_DAIS
    c.fill(x0, top, x1, HALL_FLOOR + 2)         # the dais over the B2 door
    c.carve(x0 + 1, top + 1, x1 - 1, HALL_FLOOR + 2)   # its chamber (rows 23-28; the door's ledges on row 29)
    c.fill(28, 18, 31, 18)                      # the east stair: from the dais up to the east balcony
    c.fill(36, 14, 39, 14)
    c.fill(40, 10, 47, 10)                      # the east balcony (the R0 ledge)
    x0, x1 = HALL_PIT
    c.carve(x0, HALL_FLOOR, x1, HALL_FLOOR + 2)       # the pit she morphs in
    c.carve(x1 + 1, HALL_FLOOR + 2, HALL_DAIS[0], HALL_FLOOR + 2)   # the tunnel into the chamber (the bomb block at 32)
    x0, x1 = HALL_ETANK_PIT
    c.carve(x0, HALL_FLOOR, x1, HALL_FLOOR + 1)       # the pit
    c.carve(8, HALL_FLOOR + 1, x0 - 1, HALL_FLOOR + 1)   # the "Down Launch" alcove (the bomb block at 13, the E-tank at 8)
    return Shape(c, blocks=[bomb_block(*HALL_B2_BOMB), bomb_block(*HALL_ETANK_BOMB)])


# --- P53 Crossway (3x2) -------------------------------------------------------------------------------------------------
# Prime: a tall hall from the Crossway Access West (L0, high) down to the Crossway Access South's ice door (L1) and the Elder
# Hall Access' missile door (B1, its floor door here); two bomb slots turn Spider Ball tracks, a cracked plaque (Super
# Missiles) and a piston carry Samus to a Missile Expansion high up. Here: the hall on rows 1-27 (floor 28), a zigzag of
# platforms (5 rows a step, as the Tower of Light) from the floor up to the L0 balcony (row 10); the missile in a hut of power
# bomb blocks at the east end of the floor (the plaque: the Super Missile's stand-in, as the Main Plaza's tree, 12f): Morph
# Ball and Power Bomb (the tracks and the piston are left out: on a Space Jump ledge the power bomb hut is not modelled).
CROSSWAY_FLOOR = 28
CROSSWAY_HUT = (36, CROSSWAY_FLOOR - 3, CROSSWAY_FLOOR - 1)   # west wall column, rows of the power bomb blocks


def crossway() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 1, 46, CROSSWAY_FLOOR - 1)
    c.fill(1, 27, 5, 27)                        # under the L1 ledge (row 26)
    c.fill(0, 10, 7, 10)                        # the L0 balcony
    for x0, top in ((8, 23), (16, 18), (8, 13)):
        c.fill(x0, top, x0 + 7, top)            # the zigzag up to it (5 rows a step, as the Tower of Light)
    hut_x, top, bottom = CROSSWAY_HUT
    c.fill(hut_x, top - 1, hut_x + 9, bottom)
    c.carve(hut_x, top, hut_x + 8, bottom)
    return Shape(c, blocks=[power_bomb_block(hut_x, y) for y in range(top, bottom + 1)])


# --- P54 Reflecting Pool Access (1x1) -----------------------------------------------------------------------------------
# Prime: a short shaft from the Hall (T0) down to the Reflecting Pool (B0). Here: the hall on rows 1-12 (floor 13), the T0
# door's platform (row 6) over the B0 floor door, a step (row 10) east of it for the climb back up.
def reflecting_pool_access() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 1, 14, 12)
    c.fill(12, 10, 14, 12)                      # the step (3 over the floor, 4 under the platform)
    return Shape(c)


# --- P55 Elder Hall Access (2x1) ----------------------------------------------------------------------------------------
# Prime: a half-pipe passage from the Crossway (T0: its floor door, the missile shield on the Crossway's side) to the Hall
# (L0). Here: the hall on rows 1-9 (floor 10), the T0 door's platform (row 6), the half-pipe's bowl (2 deep).
def elder_hall_access() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 1, 30, 9)
    c.carve(15, 10, 25, 11)                     # the half-pipe's bowl
    c.fill(26, 1, 30, 3)
    return Shape(c)


# --- P56 Crossway Access South (2x1) ------------------------------------------------------------------------------------
# Prime: a half-pipe passage between two ice doors: the Hall's (B0, its floor door here) and the Crossway's (R0). Here: the
# hall on rows 3-12 (floor 13), a step under the R0 ledge, the half-pipe's bowl (1 deep).
def crossway_access_south() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 12)
    under_ledges(c, False, True)
    c.carve(15, 13, 22, 13)                     # the half-pipe's bowl
    return Shape(c)


# --- P57 Elder Chamber (1x1) --------------------------------------------------------------------------------------------
# Prime: the World artifact's chamber under the statue (artifacts out, epic decision 1), behind an ice door: an empty shrine.
def elder_chamber() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 13, 9)
    c.fill(9, 8, 11, 9)                         # the empty pedestal
    return Shape(c)


# --- P58 Reflecting Pool (3x1, flooded) ---------------------------------------------------------------------------------
# Prime: a deep pool (its water kept here: the room is flooded, chozo/rooms.py FLOODED) with the Reflecting Pool Access door
# (T2) at one end, the Transport Access South's (R0, Ice) and Save Station 3's (B0, a missile shield) and the Antechamber's (L0,
# a missile shield) round it. Here (specs/12l): under water without the Gravity Suit Samus jumps 3 blocks (smlib/reach.py,
# specs/07l), with it as on land. From the T2 door she lands on its platform (row 6) and drops into the pool (floor 14, rows
# 19-35), and a stair of 3-row steps takes her back up: that is all she gets without the suit. The other doors sit behind
# 4-block climbs: the west part (the B0 floor door's ledges and the L0 ledge, floor 13) through a 3-row passage in the
# divider (rows 7-9, floor 10: 4 over the pool's floor), the R0 ledge from a step under the T2 platform (row 10, 4 over the
# pool's floor). Coming up the B0 door without the suit (from Save Station 3) she gets to the Antechamber and drops into the
# pool, back up to the T2 door.
POOL_FLOOR = 14
POOL_DIVIDER = (17, 18)              # columns of the divider between the west part and the pool


def reflecting_pool() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 1, 46, 12)                       # the room (west floor 13)
    x0, x1 = POOL_DIVIDER
    c.carve(x1 + 1, 13, 41, POOL_FLOOR - 1)     # the pool (floor 14)
    under_ledges(c, True, True)
    c.fill(x0, 1, x1, 12)                       # the divider
    c.carve(x0, 7, x1, 9)                       # its passage (floor 10)
    c.fill(31, 11, 34, 11)                      # the stair back up to the T2 platform: 3 rows a step (with the suit she
    c.fill(28, 8, 30, 8)                        # jumps from the first step's east end straight onto the platform)
    c.fill(36, 10, 41, 13)                      # the step under the T2 platform (top row 10) to the R0 ledge
    c.fill(44, 1, 46, 5)                        # the rock over the R0 door (the T2 platform does not lead onto its ledge)
    return Shape(c)


# --- P59 Save Station 3 (3x1) -------------------------------------------------------------------------------------------
# Prime: the third save room, a long hall from the Reflecting Pool (T0: its floor door) to the Transport to Tallon East (L0).
# Load station 3 of area 1 (tools/areas.py chozo_stations). Here: the hall on rows 1-12 (floor 13), a step under the L0
# ledge, the station in the middle screen.
SAVE_STATION_3 = (23, 13)   # (x, floor) of the save pedestal's left block


def save_station_3() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 1, 46, 12)
    under_ledges(c, True, False)
    for x in (14, 34):
        c.fill(x, 1, x + 1, 3)
    return Shape(c, save=SAVE_STATION_3)


# --- P60 Transport Access South (1x1) -----------------------------------------------------------------------------------
# Prime: a short passage from the Reflecting Pool's ice door (L0) to the Transport to Tallon South (R0).
def transport_access_south() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 9)
    c.fill(6, 3, 9, 4)
    return Shape(c)


# --- P61 Antechamber (1x1) ----------------------------------------------------------------------------------------------
# Prime: the Ice Beam's room (already the Tallon's: decision B, a missile on its pedestal), behind the Reflecting Pool's
# missile shield; its door is Ice-only on this side (s12l/dtrig.out: in Prime the Ice Beam found here opens it).
ANTECHAMBER_PEDESTAL = (4, 6, 8)     # columns and top row of the pedestal (the missile on it)


def antechamber() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 9)
    x0, x1, top = ANTECHAMBER_PEDESTAL
    c.fill(x0, top, x1, 9)
    return Shape(c)


LAYOUTS = {
    "chozo_transport_tallon_north": transport_tallon_north,
    "chozo_transport_tallon_east": transport_tallon_east,
    "chozo_transport_tallon_south": transport_tallon_south,
    "chozo_ruins_entrance": ruins_entrance,
    "chozo_main_plaza": main_plaza,
    "chozo_ruined_fountain_access": ruined_fountain_access,
    "chozo_ruined_shrine_access": ruined_shrine_access,
    "chozo_nursery_access": nursery_access,
    "chozo_plaza_access": plaza_access,
    "chozo_piston_tunnel": piston_tunnel,
    "chozo_ruined_shrine": ruined_shrine,
    "chozo_tower_of_light_access": tower_of_light_access,
    "chozo_tower_of_light": tower_of_light,
    "chozo_tower_chamber": tower_chamber,
    # region B (specs/12i)
    "chozo_eyon_tunnel": eyon_tunnel,
    "chozo_ruined_nursery": ruined_nursery,
    "chozo_save_station_1": save_station_1,
    "chozo_north_atrium": north_atrium,
    "chozo_ruined_gallery": ruined_gallery,
    "chozo_map_station": map_station,
    "chozo_totem_access": totem_access,
    "chozo_hive_totem": hive_totem,
    "chozo_transport_access_north": transport_access_north,
    "chozo_transport_magmoor_north": transport_magmoor_north,
    "chozo_vault_access": vault_access,
    "chozo_vault": vault,
    # region C (specs/12j)
    "chozo_ruined_fountain": ruined_fountain,
    "chozo_arboretum_access": arboretum_access,
    "chozo_arboretum": arboretum,
    "chozo_sunchamber_lobby": sunchamber_lobby,
    "chozo_sunchamber_access": sunchamber_access,
    "chozo_sunchamber": sunchamber,
    "chozo_sun_tower_access": sun_tower_access,
    "chozo_sun_tower": sun_tower,
    "chozo_save_station_2": save_station_2,
    "chozo_gathering_hall_access": gathering_hall_access,
    "chozo_gathering_hall": gathering_hall,
    "chozo_training_chamber": training_chamber,
    "chozo_training_chamber_access": training_chamber_access,
    "chozo_magma_pool": magma_pool,
    "chozo_meditation_fountain": meditation_fountain,
    # region D (specs/12k)
    "chozo_watery_hall_access": watery_hall_access,
    "chozo_watery_hall": watery_hall,
    "chozo_dynamo_access": dynamo_access,
    "chozo_dynamo": dynamo,
    "chozo_east_atrium": east_atrium,
    "chozo_energy_core_access": energy_core_access,
    "chozo_energy_core": energy_core,
    "chozo_burn_dome_access": burn_dome_access,
    "chozo_burn_dome": burn_dome,
    "chozo_west_furnace_access": west_furnace_access,
    "chozo_furnace": furnace,
    # region E (specs/12l)
    "chozo_east_furnace_access": east_furnace_access,
    "chozo_crossway_access_west": crossway_access_west,
    "chozo_hall_of_the_elders": hall_of_the_elders,
    "chozo_crossway": crossway,
    "chozo_reflecting_pool_access": reflecting_pool_access,
    "chozo_elder_hall_access": elder_hall_access,
    "chozo_crossway_access_south": crossway_access_south,
    "chozo_elder_chamber": elder_chamber,
    "chozo_reflecting_pool": reflecting_pool,
    "chozo_save_station_3": save_station_3,
    "chozo_transport_access_south": transport_access_south,
    "chozo_antechamber": antechamber,
}

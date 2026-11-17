"""Layouts of the Magmoor Caverns rooms (lava caves of tilesets $09/$0A, specs/17d).

specs/17e: the two elevator rooms to worlds that exist (Prime's P0 to the Chozo Ruins North, P16 to the Tallon Overworld West;
specs/18e: and P13/P27 up to Phendrana Drifts;
tools/magmoor/rooms.py ELEVATOR_ROOMS), built before their regions as finished dead ends, as specs/12e did for the Chozo's: the
elevator comes down a 2-block shaft from the top row onto its platform on the floor of a hall; the hall's floor is on the
ledge row of the room's doors (row 10 of their screen), but the doors are not there yet: their walls stay shut until the
neighbours are built (17f: the Burning Trail; 17h: the Transport Tunnel B; 17i: the Twin Fires Tunnel), so the region's spec
only opens the wall. Both rooms are cool (not in HOT_ROOMS: tileset $0A) and dry (no lava: Prime's elevator rooms stand over it).

specs/17f: region A, the north (Prime's P1-P8: the Burning Trail and Save Station A, the Lake Tunnel, the Lava Lake, the Pit
Tunnel, the Triclops Pit with the Storage Cavern, the Monitor Tunnel). The Tallon's and the Chozo's rules (side doors on rows 6-9
of their screen, the floor on row 10; the jump measured, smlib/reach.py, deciding every climb; a door to a room of a region not
built yet is its wall, with the floor already at its ledge row) and the lava's (specs/17d, validate.check_lava): the lava's
surface (LAVA below: the block row from which every air block is lava, SM's FX covers the room's whole width) lies under every
floor she walks on, so the lava is only in the pits dug into those floors, at most 3 rows deep and narrow enough to get out of
in a few moves; a pit on the way is jumped over (the walks never go into the lava). A jump over a pit wants 10 rows of air over
the floor (the jump's apex: reach.apex_row), so the one-screen tunnels with lava keep their floor on row 12, two rows under the
doors' ledges. Prime's in-room locks of the region (FEATURES) map to the Chozo's mechanisms: the Triclops Pit's missile, in a
hollow pillar Prime reaches with the Space Jump, sits in a hollow of a rock column hanging from the roof that only the Space Jump
reaches (a Space Jump ledge, as specs/12f's). The Lava Lake's breakable rocks and grapple points lead to its artifact in Prime
(artifacts out, epic 17 decision 2): the artifact's pillar stays, empty, with nothing to break.
"""
from __future__ import annotations

from frigate.rooms import Elevator
from smlib.canvas import Canvas
from tallon.layouts import Shape, bomb_block, power_bomb_block

SHAFT_X = 7          # the shaft's left column: the platform's centre is x 128 of its screen, as the vanilla elevators


def transport_chozo_north() -> Shape:   # P0 (1x2), door R1 -> Burning Trail (17f)
    """The hall across the bottom screen (rows 19-25, floor 26 = the R1 door's ledge row), the shaft from the top row down
    through the rock of the top screen to the platform on the hall's floor."""
    c = Canvas(1, 2)
    c.carve(1, 19, 14, 25)
    c.carve(SHAFT_X, 0, SHAFT_X + 1, 26)
    return Shape(c, elevator=Elevator(SHAFT_X, 26, up=True))


def transport_tallon_west() -> Shape:   # P16 (2x1), doors L0 -> Transport Tunnel B (17h), R0 -> Twin Fires Tunnel (17i)
    """One screen high (Prime's box is low): the hall across both screens (rows 3-9, floor 10 = both doors' ledge row) and
    the shaft from the top row down to the platform on the floor of the west screen."""
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    c.carve(SHAFT_X, 0, SHAFT_X + 1, 10)
    return Shape(c, elevator=Elevator(SHAFT_X, 10, up=True))


# --- region A (specs/17f) ---------------------------------------------------------------------------------------------------
LOW_FLOOR = 12        # the floor of a one-screen tunnel with lava pits (10 rows of air over it: rows 2-11)


def pits(c: Canvas, floor: int, xs, width: int = 4, depth: int = 2) -> None:
    """Lava pits dug into the floor (its top row `floor`): `width` columns from each x, `depth` rows under the surface (the
    surface is the row under the floor's top: floor + 1)."""
    for x in xs:
        c.carve(x, floor, x + width - 1, floor + depth)


def low_tunnel(c: Canvas, x0: int, x1: int, west_door: bool, east_door: bool) -> None:
    """A one-screen tunnel with its floor on LOW_FLOOR from x0 to x1, the side doors' ledges (row 10) a 2-row step over it."""
    c.carve(x0, 2, x1, LOW_FLOOR - 1)
    if west_door:
        c.fill(1, 10, 5, LOW_FLOOR - 1)
    if east_door:
        c.fill(c.w - 6, 10, c.w - 2, LOW_FLOOR - 1)


# --- P1 Burning Trail (6x2) -----------------------------------------------------------------------------------------------
# Prime: the trail from the Chozo's elevator along a river of lava, a side passage up to Save Station A (the missile shield on
# the trail's side), the way on to the Lake Tunnel. Here: the trail across the bottom screen (floor 26 = the L1 and R1 doors'
# ledge row; rows 13-25 of air, the jump's apex over the pits), three lava pits in its floor, and at the east end a cavern up
# to the R0 door's shelf (row 10) by three floating ledges, 5 rows apart, zigzagging as the Chozo's Tower of Light (the ledge
# two steps up is 10 rows over the one she jumps from, out of her jump).
BURNING_TRAIL_LAVA = 27
BURNING_TRAIL_PITS = (17, 33, 49)
# specs/17g: the teeth reach row 16, so the Skrees hanging under them (tools/magmoor/enemies.py) are in the camera's rows while
# Samus walks the trail (the camera's top is y 256-288 there, and an enemy above it is not run: DetermineWhichEnemiesToProcess
# $A0:8EB6 wants y + 8 >= the camera's top; under 17f's 2-row teeth they hung at y 260 and stayed asleep)
BURNING_TRAIL_TEETH, BURNING_TRAIL_TOOTH_END = (8, 24, 40), 16


def burning_trail() -> Shape:
    c = Canvas(6, 2)
    c.carve(1, 13, 94, 25)                      # the trail
    c.carve(60, 3, 94, 12)                      # the cavern up to the save station's door
    c.fill(1, 3, 59, 12)
    pits(c, 26, BURNING_TRAIL_PITS)
    c.fill(85, 10, 94, 10)                      # the R0 shelf, widened west
    c.fill(79, 21, 84, 21)                      # the ledges: 21 east, 16 west, 11 east
    c.fill(73, 16, 78, 16)
    c.fill(79, 11, 84, 11)
    for x in BURNING_TRAIL_TEETH:               # rock teeth hanging from the trail's roof (out of the jumps' arcs)
        c.fill(x, 13, x + 2, BURNING_TRAIL_TOOTH_END)
    return Shape(c)


# --- P3 Save Station Magmoor A (1x1) -----------------------------------------------------------------------------------------
# Prime's first save room of the Magmoor, off the Burning Trail (L0, the missile shield on the trail's side). Load station 1 of
# area 2 (tools/areas.py MAGMOOR).
SAVE_STATION_A = (8, 13)   # (x, floor) of the save pedestal's left block
DOOR_STEP = 12             # rows 11-12 under a side door's ledge (row 10) filled: a 3-block step down to a floor on row 13


def save_station_a() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    c.fill(1, 11, 5, DOOR_STEP)
    return Shape(c, save=SAVE_STATION_A)


# --- P2 Lake Tunnel (3x1) ---------------------------------------------------------------------------------------------------
# Prime: a short hot tunnel over lava from the Burning Trail (L0) to the Lava Lake (R0). Here: the tunnel on LOW_FLOOR, two pits.
LAKE_TUNNEL_PITS = (14, 30)


def lake_tunnel() -> Shape:
    c = Canvas(3, 1)
    low_tunnel(c, 1, 46, True, True)
    pits(c, LOW_FLOOR, LAKE_TUNNEL_PITS)
    c.fill(22, 2, 25, 3)                        # a rib of the roof
    return Shape(c)


# --- P4 Lava Lake (6x1) -----------------------------------------------------------------------------------------------------
# Prime: a lake of lava crossed along rocks, the artifact (Nature) on a pillar in the middle (out). Here: the lake from wall to
# wall, pools of 3 columns between flat rocks of 5 (the floor on LOW_FLOOR), the empty pillar in the middle a climb of 4.
LAVA_LAKE_PITS = (10, 18, 26, 34, 52, 60, 68, 76, 84)
LAVA_LAKE_PILLAR = (43, 47, 8)                  # columns, top row


def lava_lake() -> Shape:
    c = Canvas(6, 1)
    low_tunnel(c, 1, 94, True, True)
    pits(c, LOW_FLOOR, LAVA_LAKE_PITS, width=3)
    x0, x1, top = LAVA_LAKE_PILLAR
    c.fill(x0, top, x1, LOW_FLOOR - 1)
    return Shape(c)


# --- P5 Pit Tunnel (2x1) ----------------------------------------------------------------------------------------------------
# Prime: a short hot tunnel (no lava) from the Lava Lake (L0) to the Triclops Pit (R0). Here: the tunnel on rows 3-9 (floor 10),
# a raised stretch in the middle.
def pit_tunnel() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    c.fill(12, 8, 19, 9)
    c.fill(13, 3, 18, 3)
    return Shape(c)


# --- P6 Triclops Pit (6x3) --------------------------------------------------------------------------------------------------
# Prime: a deep pit of lava crossed on rocks, the doors high on its sides (the Pit Tunnel's lower in the west, the Storage
# Cavern's and the Monitor Tunnel's at the top), the missile in a hollow pillar. Here: the L1 door (Pit Tunnel) on a floor
# (row 26) by the west wall, a stair of rock down to the pit's bottom (floor 42; lava pools between its rocks) and up the east
# wall to a floor on row 26 again; from each of those floors three floating ledges zigzag up (as the Burning Trail's) to the
# top shelves (row 10) of the L0 door (Storage Cavern) and of the R0 door (Monitor Tunnel). The missile lies in a hollow of
# a rock column hanging from the roof over the middle of the pit, out of every jump: the Space Jump's.
TRICLOPS_LAVA = 43
TRICLOPS_PITS = (24, 33, 42, 51, 60, 69)
TRICLOPS_COLUMN = (44, 51, 2, 12)               # the hanging column (x0, x1, top, bottom row)
TRICLOPS_HOLLOW = (45, 50, 5, 7)                # its hollow (the missile's ledge is row 8)


def triclops_pit() -> Shape:
    c = Canvas(6, 3)
    c.carve(1, 2, 94, 41)
    c.fill(1, 11, 5, 21)                        # the rock between the L0 shelf and the L1 door
    c.fill(0, 10, 10, 10)                       # the L0 shelf, widened east
    c.fill(1, 26, 10, 47)                       # the L1 floor
    for x0, x1, top in ((11, 13, 30), (14, 16, 34), (17, 19, 38)):   # the west stair down to the bottom
        c.fill(x0, top, x1, 47)
    c.fill(11, 21, 16, 21)                      # the west ledges: 21, 16 (east of them), 11
    c.fill(17, 16, 22, 16)
    c.fill(11, 11, 16, 11)
    pits(c, 42, TRICLOPS_PITS)
    for x0, x1, top in ((76, 78, 38), (79, 81, 34), (82, 84, 30)):   # the east stair
        c.fill(x0, top, x1, 47)
    c.fill(85, 26, 94, 47)                      # the east floor
    c.fill(85, 10, 94, 10)                      # the R0 shelf, widened west
    c.fill(90, 11, 94, 25)                      # the rock under it
    c.fill(79, 21, 84, 21)                      # the east ledges: 21, 16 (west of them), 11
    c.fill(73, 16, 78, 16)
    c.fill(79, 11, 84, 11)
    x0, x1, top, bottom = TRICLOPS_COLUMN
    c.fill(x0, top, x1, bottom)
    hx0, hx1, hy0, hy1 = TRICLOPS_HOLLOW
    c.carve(hx0, hy0, hx1, hy1)
    c.carve(x1, hy0, x1, hy1)                   # its mouth, on the east side
    return Shape(c)


# --- P8 Storage Cavern (2x1) ------------------------------------------------------------------------------------------------
# Prime: a cool storage cave off the Triclops Pit's top (R0), the missile at its far end. Here: the cave on LOW_FLOOR, a pit.
def storage_cavern() -> Shape:
    c = Canvas(2, 1)
    low_tunnel(c, 1, 30, False, True)
    pits(c, LOW_FLOOR, (12,))
    c.fill(1, 2, 3, 6)                          # stored crates of rock in the corner
    return Shape(c)


# --- P7 Monitor Tunnel (2x1) ------------------------------------------------------------------------------------------------
# Prime: a hot tunnel over lava from the Triclops Pit (L0) to the Monitor Station (R0: region B, 17h; its wall until then, the
# floor already on the door's ledge row). Here: the tunnel on LOW_FLOOR, a pit.
def monitor_tunnel() -> Shape:
    c = Canvas(2, 1)
    low_tunnel(c, 1, 30, True, False)
    c.fill(c.w - 6, 10, c.w - 2, LOW_FLOOR - 1)     # the R0 door's ledge (its wall until region B)
    pits(c, LOW_FLOOR, (14,))
    return Shape(c)


# --- region B (specs/17h) ---------------------------------------------------------------------------------------------------
# Prime's P9-P16: the Monitor Station (the hub of the middle), the Transport Tunnel A and the transport to Phendrana North
# (decorative: Phendrana doesn't exist, epic 17 decision 5), the Warrior Shrine and its power bomb wall, the Shore Tunnel and
# its floor door down into the Fiery Shores, the Transport Tunnel B and the transport to the Tallon West (17e's P16, its L0
# door open now; its R0 to the Twin Fires Tunnel, region C, stays a wall until 17i). The same rules as region A (side doors on
# rows 6-9 of their screen with the floor on row 10, the jump measured deciding every climb, 5-row zigzag ledges where she
# climbs more than her jump; the lava under every floor she walks on, only in pits). Prime's in-room locks of the region map
# to the Chozo's mechanisms: the Transport Tunnel A's energy tank, in a Morph Ball tunnel under the floor in Prime, at the end of
# a 1-row tunnel shut by a bomb block; the Warrior Shrine's Morph Ball door behind a wall only a power bomb breaks = its R0
# door in a closed chamber entered by a 1-row tunnel shut by a power bomb block; on the Fiery Shores' side of that door the
# tunnel's end (Prime's missile) is a pocket under the ceiling door's platform, its way out a 1-row tunnel (Prime's power bomb
# expansion "in a Morph Ball track") shut by a power bomb block too: both items only with the Power Bomb (round 6, never
# before: an SM power bomb pack turns the power bombs on, epic 17).
def zigzag(c: Canvas, x0: int, x1: int, rows) -> None:
    """Floating ledges 6 wide (Prime's rock shelves; the Burning Trail's and the Triclops Pit's zigzag) on `rows`, alternating
    between columns x0..x0+5 and x1..x1+5 (the first on x0): each ledge 5 rows over the one under it, the one two steps up 10
    rows over (out of her jump: she climbs one at a time)."""
    for k, y in enumerate(rows):
        x = x0 if k % 2 == 0 else x1
        c.fill(x, y, x + 5, y)


# --- P9 Monitor Station (6x4) ---------------------------------------------------------------------------------------------
# Prime: the tall hub over a lava pool, the Monitor Tunnel's door high in the west (L0, from region A), the Transport Tunnel A's
# (L3) and the Warrior Shrine's (R3) at the bottom, the Shore Tunnel's (R2) half-way up the east wall. Here: the cavern from row
# 2 to the floor on row 58 (the L3 and R3 doors' ledge row), four lava pits in the floor between the walls; the L0 shelf (row
# 10) in the north-west corner over a zigzag of 9 ledges up the west wall from the floor, the R2 shelf (row 42) on a rock over the
# R3 door, reached from the floor by 3 ledges up the east wall (the Triclops Pit's east climb, 32 rows lower).
MONITOR_FLOOR, MONITOR_LAVA = 58, 59
MONITOR_PITS = (30, 40, 50, 60)
MONITOR_WEST = (13, 19, tuple(range(53, 12, -5)))      # the west zigzag: x0, x1, rows 53 .. 13
MONITOR_EAST = (79, 73, (53, 48, 43))                  # the east zigzag under the R2 shelf


def monitor_station() -> Shape:
    c = Canvas(6, 4)
    c.carve(1, 2, 94, MONITOR_FLOOR - 1)
    c.fill(1, 10, 12, 10)                       # the L0 shelf, widened east
    c.fill(1, 11, 4, 20)                        # the rock under it, against the west wall
    c.fill(1, 2, 4, 5)                          # the rock over the L0 door
    c.fill(1, 46, 4, 53)                        # and over the L3 door (she doesn't land on its cap)
    zigzag(c, *MONITOR_WEST)
    c.fill(85, 42, 94, 42)                      # the R2 shelf, widened west
    c.fill(90, 43, 94, 53)                      # the rock under it, over the R3 door
    zigzag(c, *MONITOR_EAST)
    pits(c, MONITOR_FLOOR, MONITOR_PITS)
    for x in (30, 52, 66):                      # the monitors' stone posts hanging from the roof
        c.fill(x, 2, x + 1, 5)
    return Shape(c)


# --- P10 Transport Tunnel A (2x1) ----------------------------------------------------------------------------------------
# Prime: a hot tunnel from the Monitor Station (R0) to the transport to Phendrana North (L0), its energy tank in a Morph Ball
# tunnel under the bridge. Here: the tunnel on rows 3-9 (floor 10), a dais in the middle (rows 7-9, a climb of 3) with a 1-row
# tunnel at its foot (row 9) shut by a bomb block on its east face, the energy tank at its far end.
TTA_DAIS = (12, 20)                             # its columns
TTA_BOMB = (20, 9)
TTA_TANK = (13, 9)


def transport_tunnel_a() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    x0, x1 = TTA_DAIS
    c.fill(x0, 7, x1, 9)
    c.carve(TTA_TANK[0], 9, x1, 9)              # the tunnel (the bomb block at its mouth)
    c.fill(5, 3, 7, 4)                          # ribs of the roof
    c.fill(24, 3, 26, 4)
    return Shape(c, blocks=[bomb_block(*TTA_BOMB)])


# --- P13 Transport to Phendrana Drifts North (1x2) --------------------------------------------------------------------------
# Decorative until specs/18e (epic 17, user decision 5): the hall in the top screen (rows 3-9, floor 10 = the R0 door's ledge
# row) and the 2-block shaft from the top row down to the platform (x 128, as the P0's and the P16's). specs/18e: a working
# elevator up to Phendrana's P0 (Phendrana is over the Magmoor, as Prime's lifts go up to it); the bottom screen stays rock.
# Cool, dry (Prime's elevator rooms stand over the lava).
def transport_phendrana_north() -> Shape:
    c = Canvas(1, 2)
    c.carve(1, 3, 14, 9)
    c.carve(SHAFT_X, 0, SHAFT_X + 1, 10)        # specs/18e: down to the platform's row (its blocks go on air)
    return Shape(c, elevator=Elevator(SHAFT_X, 10, up=True))


# --- P11 Warrior Shrine (2x2) --------------------------------------------------------------------------------------------
# Prime: a shrine of a Chozo warrior over the Monitor Station (the artifact of Strength on top: out), its Morph Ball door to the
# Fiery Shores behind a wall only a power bomb breaks. Here: the hall on rows 2-9 (floor 10) from the L0 door, the warrior's
# dais in the middle, and in the east the R0 door's chamber (rows 6-9) behind a wall with a 1-row tunnel at its foot (row 9),
# a power bomb block at its west mouth. The shrine's base (the bottom screens) is rock.
SHRINE_WALL = (22, 26)
SHRINE_PB = (22, 9)


def warrior_shrine() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 2, 27, 9)
    c.fill(SHRINE_WALL[0], 2, SHRINE_WALL[1], 8)    # the wall (rows 2-8), its tunnel on row 9
    c.fill(11, 8, 15, 9)                        # the warrior's dais
    c.fill(12, 2, 14, 4)                        # the statue's canopy
    return Shape(c, blocks=[power_bomb_block(*SHRINE_PB)])


# --- P12 Shore Tunnel (3x1) ------------------------------------------------------------------------------------------------
# Prime: a glass tunnel over the lava from the Monitor Station (L0) to its floor door down to the Fiery Shores (B2; the Ice
# Spreader in a glass case: nothing, epic 17 decision 2). Here: the tunnel on rows 2-9 (floor 10) east to a step down (floor 13)
# round the B2 door; coming up through it she lands on its ledges (row 13, Canvas.door_gap) and steps up west.
def shore_tunnel() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 2, 46, 9)
    c.carve(30, 10, 46, 12)                     # the step down round the floor door (floor 13)
    for x in (10, 22):
        c.fill(x, 2, x + 1, 3)                  # the glass tube's ribs
    return Shape(c)


# --- P14 Fiery Shores (6x2) ------------------------------------------------------------------------------------------------
# Prime: a long shore of lava under cliffs: the Shore Tunnel's ceiling door (T0) and the Warrior Shrine's Morph Ball door (L0)
# in the west, the Transport Tunnel B's (R0) high in the east; 2 Tryclops on the rocks, the missile at the end of the Warrior
# Shrine's tunnel, the power bomb expansion on a Morph Ball track. Here: the shore's floor on row 26 (lava pits in it), the west
# cliff a block of rock (columns 1-17, rows 7-25) with the T0 door's platform (row 6) on it; under the platform the pocket of
# the L0 door (rows 7-9: the tunnel's end, the missile) and its 1-row tunnel east through the cliff (row 9: the expansion; a
# power bomb block at its east mouth) onto a ledge (row 10) the west zigzag reaches from the shore; the R0 shelf (row 10) on a
# rock over the shore in the east, up 3 ledges (the Triclops Pit's east climb).
SHORES_LAVA = 27
SHORES_PITS = (32, 42, 52, 62)
SHORES_CLIFF = (17, 7)                          # the west cliff's east column and top row
SHORES_PB = (17, 9)
SHORES_MISSILE = (5, 9)
SHORES_EXPANSION = (14, 9)
SHORES_WEST = (18, 24, (21, 16))                # the west zigzag from the shore up to the tunnel's ledge (row 10, columns 18-23)
SHORES_EAST = (79, 73, (21, 16, 11))


def fiery_shores() -> Shape:
    c = Canvas(6, 2)
    c.carve(1, 2, 94, 25)
    c.fill(1, 2, 3, 5)                          # the rock over the L0 door: the pocket is closed from above
    c.fill(1, SHORES_CLIFF[1], SHORES_CLIFF[0], 25)   # the west cliff
    c.carve(1, 7, 11, 9)                        # the pocket under the T0 door's platform (row 6)
    c.carve(12, 9, SHORES_CLIFF[0], 9)          # its tunnel east through the cliff
    c.fill(18, 10, 23, 10)                      # the tunnel's ledge
    zigzag(c, *SHORES_WEST)
    c.fill(85, 10, 94, 10)                      # the R0 shelf, widened west
    c.fill(90, 11, 94, 25)                      # the rock under it
    zigzag(c, *SHORES_EAST)
    pits(c, 26, SHORES_PITS)
    return Shape(c, blocks=[power_bomb_block(*SHORES_PB)])


# --- P15 Transport Tunnel B (2x1) ----------------------------------------------------------------------------------------
# Prime: a hot tunnel over lava from the Fiery Shores (L0) to the transport to the Tallon West (R0). Here: the tunnel on
# LOW_FLOOR, a pit.
def transport_tunnel_b() -> Shape:
    c = Canvas(2, 1)
    low_tunnel(c, 1, 30, True, True)
    pits(c, LOW_FLOOR, (14,))
    c.fill(22, 2, 25, 3)                        # a rib of the roof
    return Shape(c)


# --- region C (specs/17i) ---------------------------------------------------------------------------------------------------
# Prime's P17-P28, the south: the Twin Fires Tunnel (hot) and its Spider Ball track over the lava, the Twin Fires, the North
# Core Tunnel, the Geothermal Core and its puzzle (the Plasma Processing behind it), the South Core Tunnel, the Magmoor
# Workstation (its energy tank on a platform Prime raises with the Wave Beam), the Workstation Tunnel and the transport to the
# Mines West, the Transport Tunnel C, the transport to Phendrana South and Save Station B (both decorative transports: the
# user's decision 5). Only the Twin Fires Tunnel is hot (Prime's Area Damage, the user's decision 3): the rest is on tileset
# $0A. The same rules as regions A and B; Prime's in-room locks of the region map to the Chozo's mechanisms (epic 17, technical
# decision 5): the Twin Fires Tunnel's Spider Ball track and the Geothermal Core's spider tracks and grapple point (to its top
# door, the South Core Tunnel's) = Space Jump ledges; the Geothermal Core's bomb-slot puzzle (it opens the Plasma
# Processing's door) = a 1-row tunnel shut by a bomb block in front of that door; the Workstation's energy tank on its
# raised platform = a Space Jump ledge (the Wave Beam, its panels' beam, is needed anyway: every door into the room is a
# wave door). Climbs of 16 rows between door shelves are the zigzags of regions A and B (3 ledges, 5 rows apart).
def save_station_b() -> Shape:   # P28 (1x1), door L0 <- Transport to Phendrana South (red on that side)
    """Save Station A's room (the pedestal at SAVE_STATION_A, the step under the L0 door's ledge). Load station 2 of area 2."""
    return save_station_a()


# --- P17 Twin Fires Tunnel (3x2, hot) -------------------------------------------------------------------------------------
# Prime: a hot tunnel from the Tallon West transport (L1) up to the Twin Fires (R0), a Spider Ball track over the lava between
# them. Here: the bottom hall (floor 26 = the L1 door's ledge row) with two lava pits, and in the east a cliff of rock whose top
# is the R0 door's shelf (row 10), 16 rows over the floor with nothing between: the Space Jump's (the track).
TFT_LAVA = 27
TFT_PITS = (12, 22)
TFT_CLIFF = (35, 10)                            # its west column and top row


def twin_fires_tunnel() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 2, 46, 25)
    c.fill(TFT_CLIFF[0], TFT_CLIFF[1], 46, 25)   # the cliff (its top: the R0 shelf)
    pits(c, 26, TFT_PITS)
    for x in (8, 18, 28):                       # rock teeth from the roof (out of the climb)
        c.fill(x, 2, x + 1, 5)
    return Shape(c)


# --- P18 Twin Fires (6x1) -----------------------------------------------------------------------------------------------
# Prime: a long cool cave over a lava river (stalactites a shot drops: ornaments here), 15 Puffers. Here: the cave on LOW_FLOOR
# from the L0 door to the R0 door, five lava pits, rock ribs.
TWIN_FIRES_PITS = (14, 30, 46, 62, 78)


def twin_fires() -> Shape:
    c = Canvas(6, 1)
    low_tunnel(c, 1, 94, True, True)
    pits(c, LOW_FLOOR, TWIN_FIRES_PITS)
    for x in (22, 54, 86):                      # stalactites
        c.fill(x, 2, x + 1, 4)
    return Shape(c)


# --- P19 North Core Tunnel (2x1) -------------------------------------------------------------------------------------------
# Prime: a short cool tunnel over lava between two wave doors (the Twin Fires', the Geothermal Core's). Here: on LOW_FLOOR, a pit.
def north_core_tunnel() -> Shape:
    c = Canvas(2, 1)
    low_tunnel(c, 1, 30, True, True)
    pits(c, LOW_FLOOR, (14,))
    c.fill(8, 2, 9, 4)                          # a stalactite
    return Shape(c)


# --- P20 Geothermal Core (4x3) ----------------------------------------------------------------------------------------------
# Prime: the tall core of the Magmoor: the North Core Tunnel's door at the bottom (L2), the Plasma Processing's (L1, ice) in
# the middle, opened by the puzzle of bomb slots, spider tracks, a grapple point and boost spinners, the South Core Tunnel's
# (L0) at the top. Here: the bottom floor (row 42 = the L2 door's ledge row) with two lava pits; on the west wall the slab of
# the L1 door's shelf (row 26), reached from the floor by a zigzag of 3 ledges (z1 37, z2 32, z3 27; the Triclops Pit's west
# climb, 16 rows lower); the L1 door in a closed chamber (rows 22-25) whose wall's 1-row tunnel at its foot is shut by a bomb
# block on its east mouth (the puzzle); the L0 door's shelf (row 10) on the rock over that chamber, 16 rows over the slab with
# nothing between: the Space Jump's (the spider tracks and the grapple point).
GC_FLOOR, GC_LAVA = 42, 43
GC_PITS = (34, 48)
GC_SLAB = (1, 10, 26)                           # the L1 shelf's slab: columns, row
GC_ZIGZAG = (11, 17, (37, 32, 27))              # x0 (z1, z3), x1 (z2), rows
GC_CHAMBER = (1, 4, 22, 25)                     # the L1 door's chamber
GC_WALL = (5, 7)                                # its wall's columns (the tunnel on row 25)
GC_BOMB = (7, 25)


def geothermal_core() -> Shape:
    c = Canvas(4, 3)
    c.carve(1, 2, 62, GC_FLOOR - 1)
    x0, x1, row = GC_SLAB
    c.fill(x0, row, x1, row)                    # the slab
    c.fill(1, 10, GC_WALL[1], 24)               # the rock over the chamber and its wall (its top: the L0 shelf, no overhang:
    #                                             the Space Jump climbs its east face from the slab)
    cx0, cx1, cy0, cy1 = GC_CHAMBER
    c.carve(cx0, cy0, cx1, cy1)                 # the chamber
    c.carve(GC_WALL[0], 25, GC_WALL[1], 25)     # the tunnel through the wall's foot
    zigzag(c, *GC_ZIGZAG)
    pits(c, GC_FLOOR, GC_PITS)
    for x in (30, 44, 56):                      # the boost spinners' stone posts hanging from the roof
        c.fill(x, 2, x + 1, 5)
    return Shape(c, blocks=[bomb_block(*GC_BOMB)])


# --- P21 Plasma Processing (3x1) -------------------------------------------------------------------------------------------
# Prime: the room of the Plasma Beam behind the Geothermal Core's ice door (its own door a plasma door: an ice door here, epic
# 17 technical decision 5). Here: the hall on LOW_FLOOR from the R0 door west, a lava pit, the missile (user decision 2: a
# missile where Prime has the Plasma Beam) on the floor at its west end.
PP_MISSILE = (5, 11)


def plasma_processing() -> Shape:
    c = Canvas(3, 1)
    low_tunnel(c, 1, 46, False, True)
    pits(c, LOW_FLOOR, (24,))
    c.fill(1, 2, 3, 7)                          # the processing machine's block in the corner
    return Shape(c)


# --- P22 South Core Tunnel (3x1) -------------------------------------------------------------------------------------------
# Prime: a cool tunnel over lava between two wave doors (the Workstation's, L0; the Geothermal Core's top, R0), 2 Burrowers.
# Here: the Lake Tunnel's shape (LOW_FLOOR, two pits).
def south_core_tunnel() -> Shape:
    c = Canvas(3, 1)
    low_tunnel(c, 1, 46, True, True)
    pits(c, LOW_FLOOR, LAKE_TUNNEL_PITS)
    c.fill(22, 2, 25, 3)                        # a rib of the roof
    return Shape(c)


# --- P23 Magmoor Workstation (4x3) -------------------------------------------------------------------------------------------
# Prime: the big works over the lava: the South Core Tunnel's door half-way up (R1), the Workstation Tunnel's at the top (R0),
# the Transport Tunnel C's at the bottom (L2); its energy tank on a platform the Wave Beam's panels raise. Here: the bottom
# floor (row 42 = the L2 door's ledge) with two lava pits; the middle slab (row 26 = the R1 door's ledge) from the east wall
# west to column 17, reached from the bottom by the west zigzag (z1 37, z2 32, z3 27); the R0 door's shelf (row 10) on a rock
# over the R1 door, by the east zigzag (21, 16, 11: the Fiery Shores' east climb); the energy tank on a ledge high in the west
# (row 8), out of every jump: the Space Jump's (the raised platform).
WS_FLOOR, WS_LAVA = 42, 43
WS_PITS = (30, 44)
WS_SLAB = (17, 62, 26)
WS_WEST = (11, 5, (37, 32, 27))
WS_EAST = (47, 41, (21, 16, 11))
WS_TANK_LEDGE = (3, 8, 8)                       # columns, row
WS_TANK = (5, 7)


def workstation() -> Shape:
    c = Canvas(4, 3)
    c.carve(1, 2, 62, WS_FLOOR - 1)
    x0, x1, row = WS_SLAB
    c.fill(x0, row, x1, row)                    # the slab
    zigzag(c, *WS_WEST)
    c.fill(1, 36, 4, 37)                        # rock over the L2 door (she doesn't land on its cap, specs/17h)
    c.fill(59, 2, 62, 5)                        # and over the R0 door
    c.fill(53, 10, 62, 10)                      # the R0 shelf, widened west
    c.fill(58, 11, 62, 21)                      # the rock under it, over the R1 door
    zigzag(c, *WS_EAST)
    tx0, tx1, ty = WS_TANK_LEDGE
    c.fill(tx0, ty, tx1, ty)                    # the raised platform
    pits(c, WS_FLOOR, WS_PITS)
    for x in (26, 38):                          # the works' pillars hanging from the roof
        c.fill(x, 2, x + 1, 6)
    return Shape(c)


# --- P24 Workstation Tunnel (3x1) ----------------------------------------------------------------------------------------
# Prime: a dry tunnel from the Workstation (L0) to the Mines West transport (R0, ice on both sides), 3 Parasites. Here: the
# tunnel on rows 3-9 (floor 10), ribs.
def workstation_tunnel() -> Shape:
    c = Canvas(3, 1)
    c.carve(1, 3, 46, 9)
    for x in (12, 24, 36):
        c.fill(x, 3, x + 1, 4)
    return Shape(c)


# --- P25 Transport Tunnel C (1x1) ---------------------------------------------------------------------------------------
# Prime: a short dry tunnel between two wave doors (Phendrana South's, L0; the Workstation's bottom, R0). Here: the hall.
def transport_tunnel_c() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 9)
    return Shape(c)


# --- P26 Transport to Phazon Mines West (2x2) -------------------------------------------------------------------------------
# Decorative until specs/19e (user decision 5: the Mines didn't exist; the shaft went up from the platform), then a working
# elevator DOWN to the Mines' P25 (the Mines lie under the Magmoor: specs/19e): the hall across the bottom screen (rows 19-25,
# floor 26 = the L1 door's ledge row), the platform on its floor at x 128 of the west screen and the 2-block shaft from it down
# to the room's last row (Phendrana's down rooms, specs/18e); the ceiling over it shut.
MINES_WEST_HALL = (1, 19, 30, 25)


def transport_mines_west() -> Shape:
    c = Canvas(2, 2)
    c.carve(*MINES_WEST_HALL)
    c.carve(SHAFT_X, 26, SHAFT_X + 1, 31)       # the platform's row too: its blocks go on air
    return Shape(c, elevator=Elevator(SHAFT_X, 26, up=False))


# --- P27 Transport to Phendrana Drifts South (2x2) ----------------------------------------------------------------------------
# Decorative until specs/18e (user decision 5), then a working elevator up to Phendrana's P29: the hall in the bottom screen
# (floor 26 = the R1 door's ledge row, to the Transport Tunnel C), the 2-block shaft from the top row down to its platform on the
# hall's floor, and the R0 door's shelf (row 10, Save Station B's red
# door) on a rock over the R1 door, by a zigzag of 3 ledges (21, 16, 11: the Fiery Shores' east climb).
PS_EAST = (15, 9, (21, 16, 11))


def transport_phendrana_south() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 19, 30, 25)                      # the hall
    c.carve(9, 2, 30, 18)                       # the cave up to the R0 door
    c.carve(SHAFT_X, 0, SHAFT_X + 1, 26)        # the shaft (specs/18e: down to the platform's row, its blocks go on air)
    c.fill(27, 2, 30, 5)                        # rock over the R0 door (she doesn't land on its cap, specs/17h)
    c.fill(21, 10, 30, 10)                      # the R0 shelf, widened west
    c.fill(26, 11, 30, 21)                      # the rock under it, over the R1 door
    zigzag(c, *PS_EAST)
    return Shape(c, elevator=Elevator(SHAFT_X, 26, up=True))


LAYOUTS = {
    "magmoor_transport_chozo_north": transport_chozo_north,
    "magmoor_transport_tallon_west": transport_tallon_west,
    "magmoor_burning_trail": burning_trail,
    "magmoor_save_station_a": save_station_a,
    "magmoor_lake_tunnel": lake_tunnel,
    "magmoor_lava_lake": lava_lake,
    "magmoor_pit_tunnel": pit_tunnel,
    "magmoor_triclops_pit": triclops_pit,
    "magmoor_storage_cavern": storage_cavern,
    "magmoor_monitor_tunnel": monitor_tunnel,
    # specs/17h: region B
    "magmoor_monitor_station": monitor_station,
    "magmoor_transport_tunnel_a": transport_tunnel_a,
    "magmoor_transport_phendrana_north": transport_phendrana_north,
    "magmoor_warrior_shrine": warrior_shrine,
    "magmoor_shore_tunnel": shore_tunnel,
    "magmoor_fiery_shores": fiery_shores,
    "magmoor_transport_tunnel_b": transport_tunnel_b,
    # specs/17i: region C
    "magmoor_twin_fires_tunnel": twin_fires_tunnel,
    "magmoor_twin_fires": twin_fires,
    "magmoor_north_core_tunnel": north_core_tunnel,
    "magmoor_geothermal_core": geothermal_core,
    "magmoor_plasma_processing": plasma_processing,
    "magmoor_south_core_tunnel": south_core_tunnel,
    "magmoor_workstation": workstation,
    "magmoor_workstation_tunnel": workstation_tunnel,
    "magmoor_transport_tunnel_c": transport_tunnel_c,
    "magmoor_transport_mines_west": transport_mines_west,
    "magmoor_transport_phendrana_south": transport_phendrana_south,
    "magmoor_save_station_b": save_station_b,
}
# specs/17f: the lava's surface row of the rooms with lava (RoomDef.lava): the row under the floor every pit is dug into
LAVA = {
    "magmoor_burning_trail": BURNING_TRAIL_LAVA,
    "magmoor_lake_tunnel": LOW_FLOOR + 1,
    "magmoor_lava_lake": LOW_FLOOR + 1,
    "magmoor_triclops_pit": TRICLOPS_LAVA,
    "magmoor_storage_cavern": LOW_FLOOR + 1,
    "magmoor_monitor_tunnel": LOW_FLOOR + 1,
    # specs/17h
    "magmoor_monitor_station": MONITOR_LAVA,
    "magmoor_fiery_shores": SHORES_LAVA,
    "magmoor_transport_tunnel_b": LOW_FLOOR + 1,
    # specs/17i
    "magmoor_twin_fires_tunnel": TFT_LAVA,
    "magmoor_twin_fires": LOW_FLOOR + 1,
    "magmoor_north_core_tunnel": LOW_FLOOR + 1,
    "magmoor_geothermal_core": GC_LAVA,
    "magmoor_plasma_processing": LOW_FLOOR + 1,
    "magmoor_south_core_tunnel": LOW_FLOOR + 1,
    "magmoor_workstation": WS_LAVA,
}

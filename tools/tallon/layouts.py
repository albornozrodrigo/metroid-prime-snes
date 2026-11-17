"""Layouts of the Tallon Overworld rooms: the MVP rooms (specs/07g-salas-mvp-tallon.md), the
decorative elevators + Artifact Temple shell (specs/07j-elevadores-de-enfeite.md), the other
rooms of regions B and C (specs/07k-regioes-b-e-c.md), region D, the sunken frigate
(specs/07l-regiao-d-fragata-afundada.md), and region E, the great tree, with Gully and Alcove
(specs/07m-regiao-e-grande-arvore.md): all 44 rooms of the table. Since specs/12e the three transports to the Chozo
Ruins have working elevators (elevator(..., ride=True)).

Prime's item-free path: Landing Site -> Canyon Cavern -> Tallon Canyon -> Transport Tunnel A ->
Transport to Chozo Ruins West. Samus has the Power Beam only (no Space Jump, no Morph Ball), so
every room is walkable with plain jumps: ledges of at most 4 blocks, no gap jumps on the way, no
pit she can't climb out of. tools/validate.py checks this with the 07b model (tools/smlib/reach.py)
from every entry to every door.

Coordinates in blocks (16x16 px). Side doors use rows 6-9 of their screen with a 6-block ledge on
row 10 (Canvas.door_gap); a door to a room that is not built is not drawn (wall).
Each layout returns a Shape: the canvas plus the extras of the room (gunship, art over blocks).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from frigate.rooms import Elevator
from smlib.canvas import Canvas

H = 0x400   # metatile h-flip


@dataclass
class Shape:
    canvas: Canvas
    ship: tuple[int, int] | None = None                            # gunship (centre block, ground row)
    skin: list[tuple[int, int, int]] = field(default_factory=list)  # art on solid blocks (collision kept)
    backdrop: list[tuple[int, int, int]] = field(default_factory=list)  # art on plain air
    save: tuple[int, int] | None = None                            # save station (RoomDef.save_station)
    blocks: list[tuple[int, int, int, int]] = field(default_factory=list)   # raw (x, y, word, BTS): bomb blocks
    elevator: Elevator | None = None                               # specs/12e: a working elevator (RoomDef.elevator)
    map_station: tuple[int, int] | None = None                     # specs/12i: a map station (RoomDef.map_station)
    missile_station: tuple[int, int] | None = None                 # specs/19l: a missile refill station (RoomDef.missile_station)
    caps: list[tuple[int, int, str, str]] = field(default_factory=list)   # specs/18i: in-room beam caps (RoomDef.caps)


# specs/09d: a bomb block = block type F (broken by a bomb or a power bomb, sm_94.c:1535) drawn with the
# CRE metatile $058, the one the game's own bomb-block code draws (PlmSetup_RespawningBombBlock2,
# sm_84.c:2227: a block that comes back is redrawn as $058, seen in the emulator); BTS 4: a 1x1 block that
# does not come back (PLM $D0C8, list $84:CCEA ends on air; BTS 0 = PLM $D0B8 comes back after ~380 frames:
# the PLM table $94:A012 + 2 * BTS, read; both measured in the emulator, specs/09d)
BOMB_BLOCK_METATILE, BOMB_BLOCK_BTS = 0x058, 0x04


def bomb_block(x: int, y: int) -> tuple[int, int, int, int]:
    return x, y, 0xF000 | BOMB_BLOCK_METATILE, BOMB_BLOCK_BTS


# specs/09e: a power bomb block = shot block type C with BTS $09 (PLM $D088, setup $CF2E =
# PlmSetup_RespawningPowerBombBlock, sm_84.c:2250: only a power bomb breaks it; list $84:CC20 ends on air and
# deletes itself: it does not come back; BTS $08 = PLM $D084, list $CB94 waits $0180 frames and redraws it;
# the PLM table $94:9EA6 + 2 * BTS, read; measured in the emulator, specs/09e) drawn with the CRE metatile $057,
# the one the game's own code redraws a power bomb block with (the SM's visible power bomb block)
POWER_BOMB_BLOCK_METATILE, POWER_BOMB_BLOCK_BTS = 0x057, 0x09


def power_bomb_block(x: int, y: int) -> tuple[int, int, int, int]:
    return x, y, 0xC000 | POWER_BOMB_BLOCK_METATILE, POWER_BOMB_BLOCK_BTS


def floor_from(c: Canvas, x0: int, x1: int, top: int) -> None:
    """Solid ground from row `top` down to the bottom of the room, columns x0..x1."""
    c.fill(x0, top, x1, c.h - 1)


def ceiling_to(c: Canvas, x0: int, x1: int, bottom: int) -> None:
    """Solid rock from the top of the room down to row `bottom`, columns x0..x1."""
    c.fill(x0, 0, x1, bottom)


def jagged_ceiling(c: Canvas, x0: int, x1: int, base: int, pattern: tuple[int, ...]) -> None:
    """Rock hanging from the top down to `base` + pattern[k] (stalactites), column by column."""
    for k, x in enumerate(range(x0, x1 + 1)):
        ceiling_to(c, x, x, base + pattern[k % len(pattern)])


# --- P0 Landing Site (5x3, surface, rain) ---------------------------------------------------------
# Open sky over a basin. Samus' gunship sits in the middle; a mossy rock beside it lets her climb on
# top (the ship saves, like vanilla). West: a cliff with a cave mouth to the Canyon Cavern door
# (L2). East (07k): terraces from the ship's top up to the Waterfall Cavern door (R1), and under them a
# corridor at ground level to the Temple Hall door (R2). Since 07m the doors to Alcove (L0) and Gully
# (L1) open into a chamber high in the west cliff: steps of 4 join them, and a lip over the basin lets
# Samus drop down to the ship (one way: 15 blocks above the ground, a Space Jump ledge).
LANDING_SHIP = (44, 42)


def landing_site() -> Shape:
    c = Canvas(5, 3)
    c.carve(0, 0, 79, 42)
    # west cliff: solid from the top, its face stepping out as it goes down, cave mouth at the bottom
    for x0, x1, bottom in ((0, 9, 35), (10, 11, 30), (12, 13, 24), (14, 14, 16), (15, 15, 9)):
        ceiling_to(c, x0, x1, bottom)
    c.fill(0, 30, 9, 35)
    c.carve(0, 36, 9, 41)                       # cave mouth to the door
    jagged_ceiling(c, 1, 9, 35, (0, 1, 0, 0, 1, 1, 0, 1, 0))
    # specs/07m: the chamber of the Gully (L1) and Alcove (L0) doors, high in the cliff: the L0 ledge
    # runs on to column 9, three steps of 4 climb to it from the L1 ledge's floor, which runs out of a
    # mouth in the cliff face to a lip 15 blocks over the ground (out of reach without the Space Jump)
    c.carve(1, 3, 13, 25)
    c.fill(14, 0, 15, 21)                       # the cliff face over the mouth
    c.fill(0, 26, 15, 27)                       # the L1 ledge's floor and the lip
    c.fill(0, 10, 9, 10)                        # the L0 ledge, longer
    for x, top in ((5, 22), (8, 18), (11, 14)):
        c.fill(x, top, x + 2, top)
    # ground: shallow pond west of the ship, flat pad under it
    floor_from(c, 0, 79, 42)
    c.carve(18, 42, 25, 43)                     # pond bed (2 blocks deep)
    c.fill(16, 41, 17, 41)                      # small bank before the pond
    # mossy rock left of the ship: the way up onto it (4 blocks, then a hop onto the hull); the
    # 2 columns between it and the ship lead down under the ship (specs/07k)
    c.fill(30, 38, 35, 41)
    c.fill(32, 37, 34, 37)
    # east (specs/07k): terraces from the top of the ship up to the Waterfall Cavern door (R1, its
    # ledge = the top terrace, row 26); under them, at ground level, a corridor of 3 rows from under
    # the ship to the Temple Hall door (R2)
    c.fill(50, 34, 61, 38)                      # level with the ship's top (row 34)
    c.fill(62, 30, 69, 38)
    c.fill(70, 26, 79, 38)
    # east overhang and wall over the R1 door
    ceiling_to(c, 76, 79, 21)
    jagged_ceiling(c, 58, 75, 6, (0, 1, 3, 2, 1, 0, 2, 4, 3, 1, 0, 1, 2, 5, 4, 2, 1, 0))
    ceiling_to(c, 64, 79, 8)
    # a couple of rock spurs in the sky to the north-west
    c.fill(16, 0, 22, 3)
    c.fill(17, 4, 19, 5)
    return Shape(c, ship=LANDING_SHIP)


# --- P2 Canyon Cavern (2x1, cave) -----------------------------------------------------------------
def canyon_cavern() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    c.carve(10, 10, 21, 11)                     # dip in the middle of the floor (2 blocks)
    jagged_ceiling(c, 1, 30, 2, (0, 0, 1, 1, 0, 1, 1, 0, 0, 1))
    c.fill(14, 3, 17, 5)                        # fallen block hanging from the roof
    c.fill(24, 8, 25, 9)                        # rubble on the floor (2 blocks, a hop)
    return Shape(c)


# --- P6 Tallon Canyon (4x3, surface, rain) ----------------------------------------------------------
# From the Canyon Cavern door (R0, high up on the east) terraces go down into the canyon; its floor
# rises again in steps to the Transport Tunnel A door (L1) on the west wall. From the L1 ledge three
# rock platforms climb to the right and a jump up to the left reaches the stone bridge of the Root
# Tunnel door (L0), high on the west wall (Prime: 11.5 m above the L1 door; specs/07k). Since 07m the
# Gully door (T3) opens in the roof over the east shelf, over the platform Canvas.door_gap puts under a
# ceiling door; Samus climbs onto it from the shelf's west end. specs/09d: Prime's bomb walls = a Morph
# Ball tunnel on the platform, one row high (roof at rows 3-4 of columns 53-54), with two bomb blocks
# (53, 5) and (54, 5); past them the chamber under the door (columns 55-57, rows 3-5: the ball unmorphs)
# and the jump up into it.
def tallon_canyon() -> Shape:
    c = Canvas(4, 3)
    c.carve(0, 0, 63, 47)
    floor_from(c, 0, 63, 44)
    # east: the high shelf of the door and the terraces down
    floor_from(c, 50, 63, 10)
    floor_from(c, 45, 49, 14)
    floor_from(c, 40, 44, 18)
    floor_from(c, 35, 39, 22)
    floor_from(c, 31, 34, 26)
    floor_from(c, 27, 30, 30)
    floor_from(c, 22, 26, 34)
    # canyon bottom (rows 38-) and the climb back up on the west side
    floor_from(c, 14, 21, 38)
    c.carve(16, 38, 19, 39)                     # stream bed
    floor_from(c, 10, 13, 34)
    floor_from(c, 8, 9, 30)
    floor_from(c, 0, 7, 26)                     # L1 door ledge (rows 22-25 open above it)
    # west wall between the two doors: rock from the L0 ledge (row 10) down to over the L1 door
    c.fill(0, 10, 5, 21)
    ceiling_to(c, 0, 5, 5)                      # over the L0 door (rows 6-9)
    # the climb to L0: platforms of 4 up to the right, then up to the left onto the bridge
    c.fill(10, 22, 12, 22)
    c.fill(14, 18, 17, 18)
    c.fill(18, 14, 20, 14)
    c.fill(6, 10, 16, 10)                       # stone bridge, one with the L0 ledge (x 0-5)
    jagged_ceiling(c, 6, 20, 1, (0, 1, 2, 1, 0, 0, 1, 2, 1, 0))
    # a mossy rock shelf jutting from nowhere over the canyon (scenery; Samus may land on it and
    # drops back into the canyon from either end)
    c.fill(21, 20, 26, 20)
    c.fill(22, 21, 25, 21)
    # east wall above the shelf, and an overhang over the terraces; the Gully door's shaft (07m)
    ceiling_to(c, 58, 63, 5)
    jagged_ceiling(c, 44, 50, 2, (0, 1, 0, 2, 1, 0, 0))
    ceiling_to(c, 51, 51, 1)
    ceiling_to(c, 52, 53, 2)
    c.carve(54, 0, 57, 5)
    c.fill(53, 3, 53, 4)                        # the Morph Ball tunnel's roof (specs/09d)
    c.fill(54, 4, 54, 4)
    return Shape(c, blocks=[bomb_block(53, 5), bomb_block(54, 5)])


# --- P9 Transport Tunnel A (2x1, cave) --------------------------------------------------------------
def tunnel_a() -> Shape:
    c = Canvas(2, 1)
    c.carve(1, 3, 30, 9)
    c.fill(12, 8, 19, 9)                        # raised middle section (2 blocks)
    c.fill(13, 3, 18, 3)                        # low beam over it (4 rows of headroom + 1)
    for x in (6, 25):
        c.fill(x, 3, x + 1, 4)                  # brick ribs hanging from the roof
    return Shape(c)


# --- the decorative elevator (epic decision 7; specs/07j-elevadores-de-enfeite.md) -----------------
# Metal pieces from the vanilla tileset 2 elevator rooms ($8F:9938, $8F:94CC): pad $392/$397,
# shaft edges $377, wall $3B2. No elevator enemy and no door: it never moves (dead end, like Prime
# before the other worlds exist). specs/12e: the three transports to the Chozo Ruins ride (`ride`): the pad's two
# middle blocks become the elevator's door blocks (RoomDef.elevator: air drawn, the platform is the $D73F sprite on
# them), with a 2-block shaft under them down to the bottom row, as vanilla $8F:9938; Magmoor East and Mines East
# stay decorative (epic 12, decision 4).
def elevator(c: Canvas, sx: int, floor: int, shaft_bottom: int, ride: bool = False) -> list[tuple[int, int, int]]:
    """A metal shaft from the top of the room down to row `shaft_bottom` (open columns sx..sx+3,
    solid walls on sx-1 and sx+4) and a 4-block metal pad on the floor row `floor` below it.
    Returns the art (skin) for the room's Shape; the pad and its two edge blocks must be solid.
    `ride` (specs/12e): the pad's middle blocks sx+1, sx+2 and the shaft under them to the bottom row are air
    (the elevator's door blocks go there: ride_down)."""
    c.carve(sx, 0, sx + 3, shaft_bottom)
    c.fill(sx - 1, 0, sx - 1, shaft_bottom)
    c.fill(sx + 4, 0, sx + 4, shaft_bottom)
    skin = []
    for y in range(0, shaft_bottom + 1):          # shaft walls (solid) left and right
        skin += [(sx - 1, y, 0x3B2), (sx + 4, y, 0x3B2)]
    skin += [(sx - 1, shaft_bottom, 0x377), (sx + 4, shaft_bottom, 0x377 | H)]
    # pad on the floor: 4 metal blocks between two edge pieces
    skin += [(sx - 1, floor, 0x377), (sx + 4, floor, 0x377 | H)]
    skin += [(sx + k, floor, (0x392, 0x397, 0x397, 0x392 | H)[k]) for k in range(4) if not (ride and k in (1, 2))]
    if ride:
        c.carve(sx + 1, floor, sx + 2, c.h - 1)
    return skin


def ride_down(sx: int, floor: int) -> Elevator:
    """specs/12e: the elevator of a pad drawn by elevator(..., ride=True): it goes down to the Chozo Ruins (specs/17e: or the
    Magmoor Caverns)."""
    return Elevator(sx + 1, floor, up=False)


# --- P14 Transport to Chozo Ruins West (2x2, cave) -----------------------------------------------
# Dead end: steps go down from the door to the elevator floor; above the pad the metal shaft goes up
# into the rock.
ELEVATOR_X = 7          # left column of the 4-block pad
ELEVATOR_FLOOR = 26


def transport_chozo_west() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 3, 30, 9)                        # upper hall from the door
    c.carve(1, 10, 25, 25)                      # chamber
    floor_from(c, 1, 30, ELEVATOR_FLOOR)
    floor_from(c, 22, 25, 14)                   # steps down from the door ledge (row 10)
    floor_from(c, 18, 21, 18)
    floor_from(c, 14, 17, 22)
    # ceiling of the chamber, with the elevator shaft open to the top of the room
    ceiling_to(c, 1, 30, 2)
    c.fill(1, 3, 13, 9)
    return Shape(c, skin=elevator(c, ELEVATOR_X, ELEVATOR_FLOOR, 9, ride=True), elevator=ride_down(ELEVATOR_X, ELEVATOR_FLOOR))


# --- P22 Transport to Chozo Ruins East (1x2, cave) -----------------------------------------------
# Door L0 high on the west wall; the rock under its ledge goes down to the floor and three steps
# go down east to the elevator, whose shaft runs up the east wall.
def transport_chozo_east() -> Shape:
    c = Canvas(1, 2)
    c.carve(1, 3, 14, 25)
    ceiling_to(c, 1, 14, 2)
    floor_from(c, 1, 5, 10)                     # the door ledge, rock down to the floor
    floor_from(c, 6, 7, 14)                     # steps of 4 down to the floor
    floor_from(c, 8, 9, 18)
    floor_from(c, 10, 10, 22)
    floor_from(c, 1, 14, 26)
    return Shape(c, skin=elevator(c, 11, 26, 9, ride=True), elevator=ride_down(11, 26))


# --- P23/P41/P43 the other transports (1x2, cave) ---------------------------------------------------
# Door on the bottom screen (L1 or R1): a flat hall from the door to the elevator at the far end,
# its shaft going up through the rock of the top screen to the top of the room.
def low_transport(door_side: str, ride: bool = False) -> Shape:
    c = Canvas(1, 2)
    c.carve(1, 17, 14, 25)                      # hall, floor on row 26 (the door ledge's row)
    sx = 9 if door_side == "L" else 3           # pad at the end away from the door
    near = (1, sx - 2) if door_side == "L" else (sx + 5, 14)
    jagged_ceiling(c, near[0], near[1], 16, (0, 1, 1, 0, 1, 0, 0))
    skin = elevator(c, sx, 26, 16, ride=ride)
    return Shape(c, skin=skin, elevator=ride_down(sx, 26) if ride else None)


def transport_magmoor_east() -> Shape:   # specs/17e: rides down to the Magmoor's P16 (the Wave Beam stays at (9, 25))
    return low_transport("R", ride=True)


def transport_chozo_south() -> Shape:
    return low_transport("L", ride=True)


def transport_mines_east() -> Shape:   # specs/19e: rides down to the Mines' P0 (the Power Bomb stays at (6, 25))
    return low_transport("L", ride=True)


# --- P16 Artifact Temple (6x4, surface) ------------------------------------------------------------
# No Meta Ridley, no artifacts (epic decision 7). Samus drops in through the ceiling door (T3) onto
# the altar slab (the door's platform, row 6, set into the top) of a stepped Chozo pyramid; steps of 4
# (2 wide) go down both sides to the temple floor, with low totem pedestals. specs/20e (epic 20,
# decision 7): Prime's teleporter to the Impact Crater = a working elevator down to the crater's Entry
# Point (impact/rooms.py TELEPORTER), its pad on the floor between the third and the fourth totems
# (TEMPLE_PAD: the 4 blocks there, the middle two and the shaft under them to the bottom row air for its
# door blocks, as ride_down's); the platform is there only once the Omega Pirate is dead (the build's
# room state).
TEMPLE_FLOOR = 54
TEMPLE_PAD = 18          # left column of the 4-block pad (totems at 16-17 and 22-23)


def artifact_temple() -> Shape:
    c = Canvas(6, 4)
    c.carve(1, 3, 94, TEMPLE_FLOOR - 1)
    jagged_ceiling(c, 1, 43, 2, (0, 1, 2, 1, 0, 0, 1, 3, 2, 1, 0, 1))
    jagged_ceiling(c, 68, 94, 2, (1, 0, 0, 2, 3, 1, 0, 1, 2, 0))
    c.carve(44, 1, 52, 2)                       # headroom to climb onto the top (rock beside the
    c.carve(59, 1, 67, 2)                       # door shaft, columns 53 and 58, stays)
    floor_from(c, 1, 94, TEMPLE_FLOOR)
    floor_from(c, 48, 63, 6)                    # pyramid top, the altar slab level
    for k in range(11):                         # steps: tops 10, 14, ..., 50
        top = 10 + 4 * k
        floor_from(c, 46 - 2 * k, 47 - 2 * k, top)
        floor_from(c, 64 + 2 * k, 65 + 2 * k, top)
    for x in (4, 10, 16, 22, 88, 92):           # totem pedestals (4 blocks)
        c.fill(x, TEMPLE_FLOOR - 4, x + 1, TEMPLE_FLOOR - 1)
    c.carve(TEMPLE_PAD + 1, TEMPLE_FLOOR, TEMPLE_PAD + 2, c.h - 1)   # specs/20e: the teleporter's shaft
    return Shape(c, elevator=ride_down(TEMPLE_PAD, TEMPLE_FLOOR))


# --- regions B and C (specs/07k-regioes-b-e-c.md) ------------------------------------------------
# Same rules as the MVP rooms for every path on foot. A door behind a Space Jump gate (Crash Site ->
# Overgrown Cavern, Root Cave -> Arbor Chamber) sits on a ledge more than 7 blocks above anything
# reachable on foot; the validator checks it can't be reached without the Space Jump.

def hall(width: int, base: int = 2, pattern: tuple[int, ...] = (0, 1, 1, 0, 0, 1, 2, 1)) -> Canvas:
    """One-screen-tall passage between two side doors (floor row 10, like the door ledges) with an
    uneven roof hanging from row `base`."""
    c = Canvas(width, 1)
    c.carve(1, base + 1, width * 16 - 2, 9)
    jagged_ceiling(c, 1, width * 16 - 2, base, pattern)
    # rock right over the side doors: a closed red/grey cap must not be a ledge under a low roof
    # (Samus got wedged on top of one in the emulator)
    c.fill(1, 0, 3, 5)
    c.fill(width * 16 - 4, 0, width * 16 - 2, 5)
    return c


# P3 Temple Hall (2x1, surface): a path between rock walls over a stone mound.
def temple_hall() -> Shape:
    c = hall(2, 1, (0, 1, 0, 0, 1, 2, 1, 0))
    c.fill(12, 8, 19, 9)
    c.fill(14, 7, 17, 7)
    return Shape(c)


# P7 Temple Security Station (3x1, surface, rain): broken Chozo pillars hang from the roof over a
# raised dais; the door to the Temple Lobby (R0) has a missile shield (red door).
def temple_security() -> Shape:
    c = hall(3, 0, (0, 0, 1, 0, 0, 0, 1, 1))
    for x in (9, 21, 35):
        c.fill(x, 0, x + 1, 3)
    c.fill(17, 8, 30, 9)
    return Shape(c)


# P11 Temple Lobby (2x1, cave): a passage from the Temple Security door (L0) to a pit over the floor
# door down into the Artifact Temple (B1); the floor door's ledges (row 13) are 3 below the passage.
def temple_lobby() -> Shape:
    c = hall(2)
    c.carve(18, 10, 29, 12)
    return Shape(c)


# P5 Waterfall Cavern (3x1, cave): a dry basin under the lip where the waterfall comes down, and a
# boulder; the door to the Crash Site (R0) has a missile shield (red door).
def waterfall_cavern() -> Shape:
    c = hall(3, 2, (0, 1, 0, 2, 1, 0, 0, 1))
    c.carve(14, 10, 25, 11)
    c.fill(19, 3, 21, 5)
    c.fill(32, 8, 36, 9)
    return Shape(c)


# P10 Root Tunnel (3x1, cave): roots hanging from the roof; the door to the Root Cave (L0) has a
# missile shield (red door).
def root_tunnel() -> Shape:
    c = hall(3, 2, (0, 1, 2, 1, 0, 1, 0, 0, 1, 1, 2, 1))
    c.fill(10, 9, 13, 9)
    c.fill(26, 9, 31, 9)
    for x in (18, 38):
        c.fill(x, 3, x + 1, 5)
    return Shape(c)


# P8 Frigate Crash Site (6x4, surface): the frigate's wreck lies across the middle, nose down to the
# west, high over the floor; Samus walks under it from the Waterfall Cavern door (L3) to the Frigate
# Access door (R3, ice). The Overgrown Cavern door (R2, ice) is on an overhang of the east wall 16
# blocks over the floor: Space Jump only (Prime: 37 m above the entry).
def crash_site() -> Shape:
    c = Canvas(6, 4)
    c.carve(1, 0, 94, 57)
    floor_from(c, 0, 95, 58)
    c.carve(22, 58, 29, 59)                     # pond bed (2)
    for x0, y0, x1, y1 in ((30, 44, 44, 49), (38, 40, 58, 47), (50, 34, 72, 43), (64, 30, 80, 37)):
        c.fill(x0, y0, x1, y1)                  # the wreck's hull, in steps
    c.fill(86, 42, 94, 49)                      # R2 overhang (under it, the way to R3)
    ceiling_to(c, 0, 5, 53)                     # cliff over the L3 door
    ceiling_to(c, 88, 95, 37)                   # east wall over the R2 door
    c.fill(81, 8, 94, 13)                       # rock spur in the sky
    return Shape(c)


# P12 Frigate Access Tunnel (2x1, cave): from the Crash Site door (L0, ice) over the rubble to the way
# into the sunken frigate (R0, region D; specs/07l opened it: the rubble wall became a mound).
def frigate_access() -> Shape:
    c = hall(2)
    c.fill(22, 8, 25, 9)
    c.fill(11, 3, 13, 4)                        # what is left of the rubble wall, hanging
    return Shape(c)


# P13 Overgrown Cavern (2x1, cave): overgrown rubble between two ice doors.
def overgrown_cavern() -> Shape:
    c = hall(2, 2, (0, 1, 2, 1, 0, 0, 1))
    c.fill(8, 8, 11, 9)
    c.fill(20, 3, 23, 4)
    return Shape(c)


# P18 Transport Tunnel C (4x4, cave): a tall cavern; steps of 4 climb from the Overgrown door (L3) to
# the Transport to Chozo Ruins East door (R2), both ice.
def tunnel_c() -> Shape:
    c = Canvas(4, 4)
    c.carve(1, 7, 62, 57)
    floor_from(c, 0, 63, 58)
    floor_from(c, 30, 63, 54)
    floor_from(c, 38, 63, 50)
    floor_from(c, 46, 63, 46)
    floor_from(c, 54, 63, 42)
    ceiling_to(c, 56, 63, 37)                   # over the R2 door
    jagged_ceiling(c, 1, 55, 6, (0, 2, 4, 3, 1, 0, 2, 5, 3, 1, 0, 1))
    c.fill(10, 30, 20, 33)                      # rock islands in the dark
    c.fill(28, 22, 34, 24)
    return Shape(c)


# P15 Root Cave (3x4, surface, rain): a tall cave; the floor goes from the Root Tunnel door (R3) to
# the Transport Tunnel B door (L3) round a pool; roots hang from the top. The Arbor Chamber door (L0,
# plasma) is on a shelf near the top: Space Jump (and Prime's grapple point) only.
def root_cave() -> Shape:
    c = Canvas(3, 4)
    c.carve(1, 1, 46, 57)
    floor_from(c, 0, 47, 58)
    c.carve(18, 58, 27, 59)                     # pool bed (2)
    c.fill(0, 10, 7, 12)                        # L0 shelf
    ceiling_to(c, 0, 5, 5)
    for x, bottom in ((12, 30), (24, 40), (35, 24), (42, 34)):
        c.fill(x, 0, x + 1, bottom)             # hanging roots
    c.fill(0, 13, 5, 53)                        # walls over the bottom doors
    ceiling_to(c, 42, 47, 53)
    return Shape(c)


# P19 Transport Tunnel B (3x1, cave): a low passage with a step up in the middle.
def tunnel_b() -> Shape:
    c = hall(3, 2, (0, 0, 1, 2, 1, 0, 1))
    c.fill(18, 8, 29, 9)
    c.fill(21, 3, 26, 3)
    return Shape(c)


# P20 Arbor Chamber (2x1, surface, rain): a small dead end under the trees.
def arbor_chamber() -> Shape:
    c = hall(2, 1, (0, 1, 2, 1, 0, 0, 1, 1))
    c.fill(4, 7, 9, 9)
    c.fill(1, 2, 3, 9)
    return Shape(c)


# --- region D: the sunken frigate (specs/07l-regiao-d-fragata-afundada.md) ------------------------
# The Frigate Orpheon on the bottom of the lake: frigate tileset 4, flooded to the top (water FX).
# Region D assumes the Gravity Suit (Prime needs it): on foot, with it, Samus jumps underwater as on
# land (measured), so the same rules hold: steps of 4, nothing she can't climb back out of. Only the
# Section C bulkhead is a gate for the jump without the suit (4 blocks; without it she climbs 3).

def steps(c: Canvas, x0: int, top0: int, direction: int, count: int, width: int = 3, rise: int = 4) -> None:
    """A climb of `count` one-block-thick platforms, each `rise` blocks above the last and `width`
    columns further in `direction` (+1 east, -1 west), starting with columns x0.. at row top0;
    nothing hangs over the column Samus jumps from, so the on-foot model climbs it."""
    for k in range(count):
        a = x0 + direction * k * width
        b = a + direction * (width - 1)
        c.fill(min(a, b), top0 - k * rise, max(a, b), top0 - k * rise)


def ribs(c: Canvas, x0: int, x1: int, y: int, every: int = 12) -> None:
    """The frigate's hull frames: 2-block-wide ribs hanging 2 blocks from the ceiling row `y`."""
    for x in range(x0, x1 - 1, every):
        c.fill(x, y, x + 1, y + 1)


# P17 Main Ventilation Shaft Section C (2x2): the duct from the Frigate Access door (L0) to Section B
# (R0). A collapsed bulkhead (4 blocks) blocks it: without the Gravity Suit the underwater jump
# reaches 3 (Prime: the frigate needs the suit). Past it the duct sags into a flooded trough.
def vent_c() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 1, 30, 9)
    c.fill(12, 6, 13, 9)                        # bulkhead (top row 6: 4 over the duct floor)
    c.carve(17, 10, 24, 13)                     # trough (4 deep)
    ribs(c, 20, 29, 1)
    c.fill(4, 1, 5, 2)
    return Shape(c)


# P21 Main Ventilation Shaft Section B (2x2): the shaft goes down from the Section C door (L0) in steps
# to the bottom of the bottom screen and up again to the Section A door (R0).
def vent_b() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 1, 30, 25)
    floor_from(c, 0, 31, 26)
    for k in range(3):                          # steps down from the L0 ledge (row 10) and up to R0
        floor_from(c, 6 + 3 * k, 8 + 3 * k, 14 + 4 * k)
        floor_from(c, 23 - 3 * k, 25 - 3 * k, 14 + 4 * k)
    floor_from(c, 0, 5, 10)
    floor_from(c, 26, 31, 10)
    c.fill(15, 1, 16, 6)                        # a vent baffle hanging in the middle
    return Shape(c)


# P24 Main Ventilation Shaft Section A (2x1): a straight duct with the hull frames; Prime's Wall Crawler
# Swarm lives here.
def vent_a() -> Shape:
    c = hall(2, 2, (0, 0, 1, 0, 0, 0, 1, 0))
    ribs(c, 6, 10, 3)
    ribs(c, 23, 26, 3)
    c.fill(14, 8, 17, 9)                        # a fallen duct section
    return Shape(c)


# P25 Reactor Core (4x3): the frigate's reactor. From the Section A door (L1, a catwalk at row 26)
# steps go down to the floor (row 42) under the reactor, which hangs in the middle; the door to the
# Reactor Access (R2, power conduits: grey) is at the floor's east end.
def reactor_core() -> Shape:
    c = Canvas(4, 3)
    c.carve(1, 1, 62, 41)
    floor_from(c, 0, 63, 42)
    floor_from(c, 0, 13, 26)                    # the catwalk from the L1 door
    for k in range(4):                          # steps of 4 down to the floor
        floor_from(c, 14 + 3 * k, 16 + 3 * k, 30 + 4 * k)
    c.fill(28, 6, 41, 31)                       # the reactor, hanging (8 rows under it)
    c.fill(31, 2, 38, 5)
    c.fill(33, 32, 36, 33)
    jagged_ceiling(c, 1, 62, 0, (0, 1, 0, 0, 2, 1, 0, 1))
    return Shape(c)


# P26 Reactor Access (1x1): a small hall between the Reactor Core (L0) and the Cargo Freight Lift
# (R0), both power-conduit doors (grey), with the Savestation up through the ceiling (T0).
def reactor_access() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 1, 14, 9)
    return Shape(c)


# P28 Savestation (1x1): the sunken frigate's save station (load station 1 of area 0), on the floor
# east of the floor door (B0) from the Reactor Access. The ceiling is high enough for the full jump
# (pulo_na_agua_medido measures the underwater jump here).
SAVESTATION = (11, 13)   # (x, floor) of the save pedestal's left block


def savestation() -> Shape:
    c = Canvas(1, 1)
    c.carve(1, 3, 14, 12)
    return Shape(c, save=SAVESTATION)


# P27 Cargo Freight Lift to Deck Gamma (4x3): the lift shaft. The Reactor Access door (L1, grey) opens
# on a deck (row 26) running east to the shaft; under it the lower deck runs from the Deck Beta Transit
# Hall door (L2, grey) to the shaft, where platforms climb back to the upper deck. Prime's Energy Tank
# sits at the Reactor Access door's height, at the deck's end over the shaft.
CARGO_DECK_END = 40


def cargo_lift() -> Shape:
    c = Canvas(4, 3)
    c.carve(1, 1, 62, 41)
    floor_from(c, 0, 63, 42)
    c.fill(0, 26, CARGO_DECK_END, 27)           # upper deck
    steps(c, 47, 38, -1, 3)                     # platforms from the lower deck up to the upper one
    for x in (12, 24, 36):
        c.fill(x, 28, x + 1, 29)                # deck girders under the upper deck
    c.fill(50, 1, 51, 22)                       # the lift's guide rails, up the shaft
    c.fill(60, 1, 61, 22)
    return Shape(c)


# P29 Deck Beta Transit Hall (2x1, dry: the only room of the sunken frigate without water in Prime).
def transit_hall() -> Shape:
    c = hall(2, 2, (0, 0, 1, 0, 0, 0, 1, 0))
    ribs(c, 9, 24, 3, 7)
    return Shape(c)


# P30 Biohazard Containment (2x2): containment tanks; from the Transit Hall door (R0, top) steps go
# down to the floor of the bottom screen and the Deck Beta Security Hall door (L1, power conduits:
# grey). Four of Prime's Gun Turrets on mounts; the Missile Expansion low on the west side, as in Prime.
def biohazard() -> Shape:
    c = Canvas(2, 2)
    c.carve(1, 1, 30, 25)
    floor_from(c, 0, 31, 26)
    floor_from(c, 26, 31, 10)                   # R0 ledge, then steps down to the floor
    for k in range(3):
        floor_from(c, 23 - 3 * k, 25 - 3 * k, 14 + 4 * k)
    for x in (7, 13):
        c.fill(x, 22, x + 2, 25)                # containment tanks (4 blocks)
    c.fill(3, 1, 12, 4)
    return Shape(c)


# P31 Deck Beta Security Hall (1x1).
def security_hall() -> Shape:
    c = hall(1, 2, (0, 0, 1, 0, 0, 1, 0, 0))
    c.fill(7, 3, 8, 6)                          # the security gate's frame
    return Shape(c)


# P32 Biotech Research Area 1 (2x3): the lab; both doors on the bottom screen (R2 to the Security Hall,
# L2 to the Conduit Hall, power conduits: grey). Platforms climb to the stasis-tank galleries above.
def biotech_1() -> Shape:
    c = Canvas(2, 3)
    c.carve(1, 1, 30, 41)
    floor_from(c, 0, 31, 42)
    steps(c, 9, 38, 1, 4)                       # galleries: platforms up to the east
    c.fill(21, 26, 30, 26)                      # top gallery
    c.fill(1, 22, 6, 22)
    jagged_ceiling(c, 1, 30, 0, (0, 1, 0, 0, 1, 2))
    return Shape(c)


# P33 Deck Beta Conduit Hall (2x1).
def conduit_hall() -> Shape:
    c = hall(2, 2, (0, 1, 0, 0, 0, 1, 0, 0))
    c.fill(10, 8, 13, 9)
    c.fill(20, 8, 21, 9)
    return Shape(c)


# P34 Connection Elevator to Deck Beta (1x3): the elevator shaft, doors in the middle (R1 Conduit Hall,
# L1 Hydro Access) on the stopped car (row 26); Prime's Space Pirate stands on it.
def elevator_beta() -> Shape:
    c = Canvas(1, 3)
    c.carve(1, 1, 14, 46)
    c.fill(1, 26, 14, 27)                       # the car
    c.fill(1, 1, 2, 25)                         # guide rails up the shaft
    c.fill(13, 1, 14, 25)
    c.fill(1, 28, 14, 46)                       # the shaft under the car: rubble
    return Shape(c)


# P35 Hydro Access Tunnel (3x2, cave, flooded): from the Elevator door (R0) down a flooded tunnel to
# the Great Tree Hall floor door (B2; 07m: a pit of 3 down to the door's ledges). In Prime the Energy
# Tank floats high in the middle (a Morph Ball maze there: no Morph Ball here, so it sits on a shelf).
def hydro_access() -> Shape:
    c = Canvas(3, 2)
    c.carve(1, 3, 46, 25)
    floor_from(c, 0, 47, 26)
    floor_from(c, 42, 47, 10)                   # R0 ledge, steps down to the tunnel floor
    for k in range(3):
        floor_from(c, 39 - 3 * k, 41 - 3 * k, 14 + 4 * k)
    c.fill(18, 22, 26, 22)                      # the shelf of the Energy Tank (4 over the floor)
    jagged_ceiling(c, 1, 46, 2, (0, 1, 2, 1, 0, 0, 1, 3, 2, 1))
    # 07m: the floor door (B2) to the Great Tree Hall, under the steps: they become one block thick,
    # with the tunnel going on under them to a pit of 3 over the door's ledges
    c.carve(33, 15, 46, 25)
    c.carve(36, 11, 41, 14)
    c.carve(39, 15, 41, 17)
    for k in range(3):
        c.fill(39 - 3 * k, 14 + 4 * k, 41 - 3 * k, 14 + 4 * k)
    c.fill(42, 11, 47, 11)
    c.carve(35, 26, 44, 28)
    return Shape(c)


# --- Gully and Alcove (region A) and region E, the great tree (specs/07m-regiao-e-grande-arvore.md) --
# Same rules: steps of at most 4, nothing without a way back, every door from every entry on foot but
# the Space Jump ledges (the Landing Site's Gully/Alcove ledge, the Great Tree Chamber door), which the
# ground can't reach. The ponds and pools (Gully, Alcove, Great Tree Hall, Life Grove) stay dry, like
# those of regions A-C. Walking Seedlings need flat ground under their whole walk (validate.py).

# P1 Gully (3x1, surface): a stream bed from the Tallon Canyon's roof door (B0: Samus comes up through
# the floor, behind the bomb walls) to the Landing Site's cliff chamber (R0); Prime's 3 Parasites.
def gully() -> Shape:
    c = hall(3, 1, (0, 1, 2, 1, 0, 1, 3, 2, 1, 0))
    floor_from(c, 0, 47, 13)
    c.carve(1, 10, 46, 12)
    c.fill(17, 11, 19, 12)                      # boulders in the stream bed
    c.fill(30, 10, 33, 12)
    c.fill(39, 10, 46, 12)                      # the bank up to the R0 ledge (3)
    c.fill(24, 2, 26, 4)
    return Shape(c)


# P4 Alcove (5x2, surface): a hollow in the cliffs; the Landing Site door (R1) on a shelf 2 over the
# floor; Prime's Space Jump Boots on the floor in the middle (9 m under the door, 37 m from it).
ALCOVE_FLOOR = 28


def alcove() -> Shape:
    c = Canvas(5, 2)
    c.carve(1, 1, 78, ALCOVE_FLOOR - 1)
    floor_from(c, 0, 79, ALCOVE_FLOOR)
    for x0, x1, top in ((1, 6, 16), (7, 10, 20), (11, 14, 24)):
        floor_from(c, x0, x1, top)              # west wall stepping down
    floor_from(c, 66, 79, 26)                   # the shelf of the door
    jagged_ceiling(c, 1, 30, 4, (0, 2, 4, 3, 1, 0, 1, 3, 5, 2))
    jagged_ceiling(c, 48, 78, 6, (1, 0, 2, 4, 3, 1, 0, 2, 3, 1))
    c.fill(54, 15, 60, 17)                      # a rock outcrop over the floor
    return Shape(c)


# P36 Great Tree Hall (3x4, surface): the tree's hall. Samus drops in from the Hydro Access floor door
# (T0, on the platform under it); a floor on row 10 runs east to the Transport Tunnel D door (R0) with
# a hole by the trunk. Branches climb in two flights: up to the left from the Transport Tunnel E
# door's ledge (R2) to the hole, and up to the right from the floor of the bottom (Life Grove Tunnel
# door, R3) to the R2 ledge. The Great Tree Chamber door (R1) is on the east wall in the open air
# between the floor and the R2 ledge, 9+ blocks from every branch: a Space Jump ledge (the roof keeps
# Samus from falling onto it). In Prime the Hydro Access door is at the bottom, under water; here the
# map (07d) puts it on top, and the pool is left dry.
TREE_FLOOR = 10


def great_tree_hall() -> Shape:
    c = Canvas(3, 4)
    c.carve(1, 1, 46, 61)
    floor_from(c, 0, 47, 62)
    c.fill(0, TREE_FLOOR, 15, TREE_FLOOR)       # the top floor, west of the hole...
    c.fill(21, TREE_FLOOR, 47, TREE_FLOOR)      # ...and east of it, to the R0 door
    c.fill(1, 11, 12, 58)                       # the trunk, under the west part of the top floor
    for k in range(5):                          # bottom flight: up to the right, to the R2 ledge
        c.fill(27 + 3 * k, 58 - 4 * k, 29 + 3 * k, 58 - 4 * k)
    c.fill(39, 42, 41, 42)                      # (one with the R2 ledge)
    for k in range(7):                          # top flight: up to the left, from the R2 ledge
        c.fill(34 - 3 * k, 38 - 4 * k, 36 - 3 * k, 38 - 4 * k)
    jagged_ceiling(c, 13, 46, 0, (0, 1, 0, 0, 1, 2, 1, 0))
    return Shape(c)


# P37 Great Tree Chamber (3x1, surface): a dead end under the tree's roots; Prime's Missile Expansion
# on the floor in the middle.
def great_tree_chamber() -> Shape:
    c = hall(3, 1, (0, 1, 2, 3, 2, 1, 0, 0, 1, 2))
    c.fill(36, 6, 46, 9)                        # roots down to the floor at the far end
    c.fill(12, 3, 14, 5)
    c.fill(30, 3, 31, 6)
    return Shape(c)


# P38 Transport Tunnel D (2x1, cave): between two ice doors (grey); flat floor for Prime's 2 Seedlings.
def tunnel_d() -> Shape:
    c = hall(2, 2, (0, 1, 1, 0, 2, 1, 0, 0))
    c.fill(15, 3, 16, 5)
    return Shape(c)


# P39 Life Grove Tunnel (2x1, cave): from the ice door of the Great Tree Hall (L0) to the Life Grove
# (R0); Prime's Missile Expansion in the middle, at the doors' height.
def life_grove_tunnel() -> Shape:
    c = hall(2, 2, (0, 1, 2, 1, 0, 1, 2, 2))
    c.fill(9, 9, 11, 9)
    c.fill(22, 9, 24, 9)
    return Shape(c)


# P40 Transport Tunnel E (3x1, cave): between two ice doors (grey); flat floor for Prime's 3 Seedlings.
def tunnel_e() -> Shape:
    c = hall(3, 2, (0, 0, 1, 2, 1, 0, 1, 1, 0))
    for x in (16, 30):
        c.fill(x, 3, x + 1, 5)
    return Shape(c)


# P42 Life Grove (5x3, surface, rain): from the Life Grove Tunnel door (L0) terraces of 4 go down to
# the grove's floor, where the X-Ray Visor lies (Prime: 13 m under the door, 54 m from it, inside walls
# a Power Bomb breaks). East of it the dry bed of the pool, two terraces lower. specs/09e: Prime's
# "Destroyable Wall"s = a hut of 15 power bomb blocks round the X-Ray (40, 29): walls on columns 37 and 43
# (rows 26-29) and a roof on row 25 (columns 37-43; without it she would climb the 4-block wall and drop
# in); inside, columns 38-42, 4 rows. Over the roof she goes on east (a 5-block step).
GROVE_FLOOR = 30
XRAY_HUT = (37, 43, GROVE_FLOOR - 5)    # west wall, east wall, roof row


def xray_hut() -> list[tuple[int, int, int, int]]:
    x0, x1, roof = XRAY_HUT
    cells = [(x, roof) for x in range(x0, x1 + 1)]
    cells += [(x, y) for x in (x0, x1) for y in range(roof + 1, GROVE_FLOOR)]
    return [power_bomb_block(x, y) for x, y in cells]


def life_grove() -> Shape:
    c = Canvas(5, 3)
    c.carve(1, 1, 78, 45)
    floor_from(c, 0, 79, 46)
    for k in range(5):                          # terraces from the L0 ledge (row 10) down to the grove
        floor_from(c, 6 + 3 * k, 8 + 3 * k, 14 + 4 * k - (4 if k == 4 else 0))
    floor_from(c, 18, 56, GROVE_FLOOR)
    floor_from(c, 57, 60, GROVE_FLOOR + 4)      # down into the pool's bed
    floor_from(c, 61, 78, GROVE_FLOOR + 8)
    floor_from(c, 0, 5, 10)
    for x in (24, 50):                          # Chozo pillars on the grove's floor
        c.fill(x, GROVE_FLOOR - 4, x + 1, GROVE_FLOOR - 1)
    jagged_ceiling(c, 30, 78, 1, (0, 1, 3, 2, 0, 1, 2, 4, 3, 1))
    return Shape(c, blocks=xray_hut())


LAYOUTS = {
    "tallon_landing_site": landing_site,
    "tallon_canyon_cavern": canyon_cavern,
    "tallon_canyon": tallon_canyon,
    "tallon_tunnel_a": tunnel_a,
    "tallon_transport_chozo_west": transport_chozo_west,
    # regions B and C (specs/07j, 07k)
    "tallon_temple_hall": temple_hall,
    "tallon_temple_security": temple_security,
    "tallon_temple_lobby": temple_lobby,
    "tallon_artifact_temple": artifact_temple,
    "tallon_waterfall_cavern": waterfall_cavern,
    "tallon_crash_site": crash_site,
    "tallon_root_tunnel": root_tunnel,
    "tallon_frigate_access": frigate_access,
    "tallon_overgrown_cavern": overgrown_cavern,
    "tallon_root_cave": root_cave,
    "tallon_tunnel_c": tunnel_c,
    "tallon_tunnel_b": tunnel_b,
    "tallon_arbor_chamber": arbor_chamber,
    "tallon_transport_chozo_east": transport_chozo_east,
    "tallon_transport_magmoor_east": transport_magmoor_east,
    # region D (specs/07l)
    "tallon_vent_c": vent_c,
    "tallon_vent_b": vent_b,
    "tallon_vent_a": vent_a,
    "tallon_reactor_core": reactor_core,
    "tallon_reactor_access": reactor_access,
    "tallon_savestation": savestation,
    "tallon_cargo_lift": cargo_lift,
    "tallon_transit_hall": transit_hall,
    "tallon_biohazard": biohazard,
    "tallon_security_hall": security_hall,
    "tallon_biotech_1": biotech_1,
    "tallon_conduit_hall": conduit_hall,
    "tallon_elevator_beta": elevator_beta,
    "tallon_hydro_access": hydro_access,
    # region E and Gully/Alcove (specs/07m; the two transports drawn in 07j)
    "tallon_gully": gully,
    "tallon_alcove": alcove,
    "tallon_great_tree_hall": great_tree_hall,
    "tallon_great_tree_chamber": great_tree_chamber,
    "tallon_tunnel_d": tunnel_d,
    "tallon_life_grove_tunnel": life_grove_tunnel,
    "tallon_tunnel_e": tunnel_e,
    "tallon_transport_chozo_south": transport_chozo_south,
    "tallon_life_grove": life_grove,
    "tallon_transport_mines_east": transport_mines_east,
}

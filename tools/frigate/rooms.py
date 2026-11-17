"""Frigate Orpheon rooms (2D demake of Metroid Prime's Space Pirate Frigate).

Coordinates are in blocks (16x16 px); each screen is 16x16 blocks.
- Horizontal doors use rows 6-9 of their screen (floor right below, at row 10).
- Vertical doors use columns 6-9 of their screen.
Samus has the Space Jump in the frigate (as in Prime), so any connected air is reachable.

Door links follow the Prime door graph (research/prime_worlds.json). Each link is declared once in
LINKS; `locked=True` makes a grey door that opens when the area boss (Parasite Queen) is dead,
which gates the escape route exactly like the debris/sealed doors in Prime.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from smlib.canvas import Canvas
from smlib.level import Door, Level, Palette, word as level_word
from smlib.style import FRIGATE, EdgeStyle, Style

from .ending import ship_blocks
from .props import BACKDROPS, PROPS, SKINS

OPPOSITE = {"L": "R", "R": "L", "T": "B", "B": "T"}


@dataclass
class DoorLink:
    side: str
    screen: int
    to_room: str
    to_door: int = -1
    locked: bool = False
    # Tallon (specs/07k): items the link needs (both sides) and, on the side with the cap, the
    # cap PLM ("missile" = red door; "ice"/"wave"/"plasma" = beam door, specs/09a); like the grey doors
    # above, the blue cap blocks stay in the level under the PLM
    gate: frozenset[str] = frozenset()
    lock: str | None = None
    lock_bit: int | None = None   # door bit of a red door ($7ED8B0)
    ledge: bool = False           # this side is behind geometry only the gate's GEOMETRY items get through
    # specs/18h: a boss door's cap in its arena's dead state (lock "boss": the fight's grey cap in the alive state), when Prime
    # also has a key lock on that dock (the Chapel of the Elders' wave door): None = blue
    dead_lock: str | None = None

    @property
    def has_cap(self) -> bool:
        """Blue cap only on side doors; shafts (top/bottom) are open passages; grey/red doors are PLMs."""
        return self.side in "LR" and not self.locked and self.lock is None


# specs/12e: a working elevator to another area, as the vanilla ones ($8F:9938 <-> $9AD9, read from the bytes): the
# platform is enemy $D73F standing on two door blocks (type 9) whose door entry has no room ($0000: solid, and Samus
# standing on them sets elevator_flags, BlockColl_Vert_Door $94:93CE); a 2-block shaft runs from them to the room's
# edge, where two more door blocks lead to the other area (door flags $C0: elevator + area change). The level is
# drawn by the layout (the shaft carved as air); RoomDef.level() puts the four door blocks. The pairs of rooms are
# in tools/areas.py ELEVATORS.
ELEVATOR_DOOR_METATILE = 0x0FF   # the vanilla elevator door blocks are drawn as air ($90FF): the platform is a sprite


@dataclass(frozen=True)
class Elevator:
    x: int        # left column of the two door blocks under the platform (the platform's centre is x+1, block edge)
    row: int      # row of those blocks (the platform stands in it; Samus' feet on top of it)
    up: bool      # True: Samus rides up (shaft and exit at the top row); False: down (exit at the bottom row)

    def exit_row(self, room_height_blocks: int) -> int:
        return 0 if self.up else room_height_blocks - 1

    def shaft(self, room_height_blocks: int) -> list[tuple[int, int]]:
        """Air cells of the shaft between the platform blocks and the exit blocks (both excluded)."""
        rows = range(1, self.row) if self.up else range(self.row + 1, room_height_blocks - 1)
        return [(self.x + k, y) for y in rows for k in (0, 1)]


@dataclass
class RoomDef:
    key: str
    prime: int
    name: str
    width: int
    height: int
    map_x: int
    map_y: int
    canvas: Canvas
    doors: list[DoorLink] = field(default_factory=list)
    spawn: tuple[int, int] | None = None   # Samus start (pixel x, y) if the game starts here
    # save station: (x, floor) of the left block of the 2-block pedestal; Samus saves standing on
    # blocks x and x+1 of row `floor` (like the vanilla save rooms, PLM on the left block)
    save_station: tuple[int, int] | None = None
    # map station: (x, floor) given to Canvas.map_station; Samus stands on row `floor` next to it
    map_station: tuple[int, int] | None = None
    # specs/19l: missile refill station (the SM's, PLM $B6EB): (x, floor) given to Canvas.refill_station; Samus stands on row
    # `floor` next to it and walks into its access block (x-1 or x+1, floor-2) at cannon height, as the map station's
    missile_station: tuple[int, int] | None = None
    # Samus' gunship: (centre block, ground row); its invisible collision goes into the level
    ship: tuple[int, int] | None = None
    # look of the room: wall style, metatile palette and tileset (None = the area's, tools/areas.py);
    # an EdgeStyle (smlib/crateria.py) must go with its own tileset (validate.py checks it)
    style: Style | EdgeStyle = FRIGATE
    palette: Palette = field(default_factory=Palette)
    tileset: int | None = None
    fx: int = 0x0000   # FX of the room's states ($83 pointer; 0 = none; e.g. crateria.RAIN_FX)
    # flooded: water FX over the whole room (the build writes the entry; specs/07l). Samus moves
    # with the underwater jump there (tools/smlib/reach.py); `fx` stays 0
    water: bool = False
    # specs/12g: hot (SM's heat: hurts without the Varia Suit; chozo/heat.py, area 1 only); the build writes the FX entry
    heat: bool = False
    # specs/17d: lava (SM's FX type 2, smlib/lava.py; Magmoor's area 2 only): the block row of its surface (every air block from
    # that row down is in the lava); the build writes the FX entry. None = no lava
    lava: int | None = None
    # specs/20g: the crater's phazon that hurts = SM's acid (FX type 4, smlib/lava.py ACID_TYPE: hurts with every suit, the
    # Gravity's too; the Impact Crater's area 0 only): the block row of its surface, as `lava`. None = none
    acid: int | None = None
    # specs/18d: falling snow (an SM BG3 FX, smlib/ice.py SNOW_FX: ice.SPORES in the game, ice.RAIN only in the test build;
    # Phendrana's area 4 only); the build writes the FX entry. 0 = none
    snow: int = 0
    # background command list ($8F) and BG2 scroll of the states (None = the area's)
    library_bg: int | None = None
    layer2: int | None = None
    # (x, y, metatile) art of the room itself, added to props.SKINS/BACKDROPS (same rules)
    skin: list[tuple[int, int, int]] = field(default_factory=list)
    backdrop: list[tuple[int, int, int]] = field(default_factory=list)
    # (x, y, block word, BTS) raw collision blocks on air (specs/09d: the Tallon's bomb blocks)
    blocks: list[tuple[int, int, int, int]] = field(default_factory=list)
    # specs/12e: a working elevator to another area (door-out list slots: after the doors, the exit, then the platform)
    elevator: Elevator | None = None
    # specs/18i: beam door caps inside the room (Prime's ice that only a beam melts: a niche shut by that beam's door cap):
    # (x, top row, wall side "R"/"L" = the cap's PLM by the wall it would be on, the beam); the 4 blocks from the top row down
    # are air in the drawing and get a door cap's blocks in the level (cap_blocks: the PLM draws the cap on them);
    # validate.niche_cap_cells
    caps: list[tuple[int, int, str, str]] = field(default_factory=list)

    @property
    def liquid(self) -> int | None:
        """specs/20g: the surface row of the room's hurting liquid (lava or acid: no place to walk, a way out of it), None: none."""
        return self.lava if self.lava is not None else self.acid

    @property
    def elevator_slots(self) -> tuple[int, int] | None:
        """(exit, platform) slots of the door-out list: right after the room's doors."""
        return (len(self.doors), len(self.doors) + 1) if self.elevator else None

    def elevator_blocks(self) -> list[tuple[int, int, int, int]]:
        """(x, y, block word, BTS) of the elevator's four door blocks: the exit at the room's edge, the platform's."""
        if not self.elevator:
            return []
        e, (exit_slot, pad_slot) = self.elevator, self.elevator_slots
        word = 0x9000 | ELEVATOR_DOOR_METATILE
        ey = e.exit_row(self.height * 16)
        return [(e.x + k, ey, word, exit_slot) for k in (0, 1)] + [(e.x + k, e.row, word, pad_slot) for k in (0, 1)]

    def cap_blocks(self) -> list[tuple[int, int, int, int]]:
        """specs/18i: (x, y, block word, BTS) of the in-room beam caps (RoomDef.caps): a side door's cap blocks as the level
        stamps them (smlib/level.py Level._stamp_door): the top a shot block (type C, BTS $40/$41 by the side: the PLM's setup
        rewrites it to its own $44), the 3 under it vertical extensions of it (type D, BTS $FF/$FE/$FD). The PLM's frames draw
        the cap's tiles and, opened, air (emulator: with the extensions' BTS 0 Samus walked through the shut cap)."""
        out = []
        for x, y, side, _beam in self.caps:
            hf = side == "L"
            out.append((x, y, level_word(0xC, 0x00C, hf, False), 0x41 if hf else 0x40))
            out += [(x, y + k, level_word(0xD, 0x00C if k == 3 else 0x02C, hf, k >= 2), 0x100 - k) for k in (1, 2, 3)]
        return out

    def level(self) -> Level:
        for d in self.doors:
            self.canvas.door_gap(d.side, d.screen)
        # grey/red doors keep the cap blocks in the level data; the PLM sits on top of them (vanilla does this)
        doors = [Door(d.side, d.screen, i, cap=d.has_cap or d.locked or d.lock is not None)
                 for i, d in enumerate(self.doors)]
        decor = [cell for prop in PROPS.get(self.key, []) for cell in prop.cells()]
        overlay = (ship_blocks(*self.ship) if self.ship else []) + self.blocks + self.elevator_blocks() + self.cap_blocks()
        return Level(self.width, self.height, self.canvas.rows(), doors=doors, style=self.style,
                     palette=self.palette, decor=decor,
                     overlay=overlay, backdrop=BACKDROPS.get(self.key, []) + self.backdrop,
                     skin=SKINS.get(self.key, []) + self.skin)


# --- generic shapes -----------------------------------------------------------------------------

RIB_EVERY = 12   # blocks between the ceiling ribs of a corridor


def hall(w: int, ribs: bool = True) -> Canvas:
    """One-screen-tall corridor. Ribs: 2-block-wide frames hanging 2 blocks from the ceiling, like
    a ship's hull frames; they leave 5 rows of headroom and stay clear of the side doors."""
    c = Canvas(w, 1)
    c.carve(1, 3, w * 16 - 2, 9)
    if ribs:
        for x in range(RIB_EVERY, w * 16 - 8, RIB_EVERY):
            c.fill(x, 3, x + 1, 4)
    return c


def shaft(h: int, steps: bool = True) -> Canvas:
    """One-screen-wide vertical shaft with alternating ledges."""
    c = Canvas(1, h)
    c.carve(2, 1, 13, h * 16 - 2)
    if steps:
        # stop 8 rows above the floor: the floor-door ledges sit at h*16-3 and Samus needs headroom
        for i, y in enumerate(range(12, h * 16 - 8, 5)):
            if i % 2:
                c.platform(2, 5, y)
            else:
                c.platform(10, 13, y)
    return c


def box(w: int, h: int) -> Canvas:
    c = Canvas(w, h)
    c.carve(1, 2, w * 16 - 2, h * 16 - 6)
    return c


# --- rooms (Prime index in comments) ------------------------------------------------------------

def make_rooms() -> dict[str, RoomDef]:
    R: dict[str, RoomDef] = {}

    def add(key, prime, name, w, h, mx, my, canvas, spawn=None, save_station=None, map_station=None, ship=None):
        if map_station:
            canvas.map_station(*map_station)
        R[key] = RoomDef(key, prime, name, w, h, mx, my, canvas, spawn=spawn, save_station=save_station,
                         map_station=map_station, ship=ship)

    # P0 Exterior Docking Hangar: Samus lands on the deck at the left. Her gunship is parked on the
    # hangar floor near the Air Lock door (tools/frigate/ending.py); she boards it at the end.
    c = Canvas(4, 2)
    c.carve(2, 2, 61, 25)
    c.fill(2, 12, 14, 25)
    c.platform(20, 26, 20)
    c.platform(30, 36, 16)
    c.platform(40, 46, 20)
    add("hangar", 0, "Exterior Docking Hangar", 4, 2, 1, 1, c, spawn=(6 * 16, 12 * 16 - 24), ship=(54, 26))

    # P1 Air Lock
    c = Canvas(1, 1)
    c.carve(2, 3, 13, 12)
    c.fill(2, 10, 5, 12)
    c.fill(10, 10, 13, 12)
    add("airlock", 1, "Air Lock", 1, 1, 5, 2, c)

    # P2 Deck Alpha Access Hall (Parasites)
    c = hall(4)
    c.fill(14, 3, 17, 5)
    c.fill(30, 8, 33, 9)
    c.fill(46, 3, 49, 5)
    add("access_hall", 2, "Deck Alpha Access Hall", 4, 1, 6, 2, c)

    # P3 Deck Alpha Mech Shaft (escape route)
    add("mech_shaft", 3, "Deck Alpha Mech Shaft", 1, 2, 5, 3, shaft(2))

    # P4 Emergency Evacuation Area
    c = box(2, 2)
    c.carve(1, 2, 30, 25)
    c.platform(6, 12, 20)
    c.platform(16, 22, 15)
    c.platform(24, 30, 10)
    add("evac_area", 4, "Emergency Evacuation Area", 2, 2, 10, 1, c)

    # P5 Connection Elevator to Deck Alpha (escape)
    add("elevator_alpha", 5, "Connection Elevator to Deck Alpha", 1, 3, 4, 4, shaft(3))

    # P6 Deck Alpha Umbilical Hall (debris)
    c = hall(3)
    c.fill(12, 3, 13, 6)
    c.fill(20, 7, 21, 9)
    c.fill(34, 3, 35, 6)
    add("umbilical_hall", 6, "Deck Alpha Umbilical Hall", 3, 1, 12, 1, c)

    # P7 Biotech Research Area 2 (escape; flooded lab in Prime)
    c = box(3, 2)
    c.carve(1, 1, 46, 28)
    c.platform(8, 14, 22)
    c.platform(20, 27, 17)
    c.platform(32, 38, 12)
    add("biotech_2", 7, "Biotech Research Area 2", 3, 2, 2, 7, c)

    # P8 Map Facility: the frigate's map station (Prime has one here too)
    c = hall(2)
    c.carve(1, 3, 30, 13)
    c.platform(12, 19, 10)
    add("map_facility", 8, "Map Facility", 2, 1, 15, 1, c, map_station=(8, 14))

    # P9, P11, P13, P15, P19, P23 Main Ventilation Shaft sections F..A (escape, climbing up)
    # Escape order: A (from the cargo lift) -> B down -> C left -> D, E, F up -> Biotech Area 2.
    add("vent_f", 9, "Main Ventilation Shaft Section F", 1, 2, 2, 9, shaft(2))
    add("vent_e", 11, "Main Ventilation Shaft Section E", 1, 2, 2, 11, shaft(2))
    add("vent_d", 13, "Main Ventilation Shaft Section D", 1, 2, 2, 13, shaft(2))
    add("vent_c", 15, "Main Ventilation Shaft Section C", 2, 1, 3, 14, hall(2))
    add("vent_b", 19, "Main Ventilation Shaft Section B", 1, 2, 5, 13, shaft(2))
    c = Canvas(2, 2)
    c.carve(1, 2, 13, 29)
    c.carve(1, 20, 30, 25)
    add("vent_a", 23, "Main Ventilation Shaft Section A", 2, 2, 5, 11, c)

    # P10 Connection Elevator to Deck Beta
    add("elevator_beta", 10, "Connection Elevator to Deck Beta", 1, 3, 16, 2, shaft(3))

    # P12 Deck Beta Conduit Hall: Morph Ball tunnel in the middle
    c = Canvas(3, 1)
    c.carve(1, 3, 14, 9)
    c.carve(33, 3, 46, 9)
    c.carve(14, 9, 33, 9)            # 1-block-high tunnel: Morph Ball only
    c.carve(35, 1, 44, 9)            # opening under the top door (screen 2)
    add("conduit_hall", 12, "Deck Beta Conduit Hall", 3, 1, 14, 5, c)

    # P14 Biotech Research Area 1: pirates in stasis tanks
    c = box(3, 2)
    c.carve(1, 1, 46, 30)
    c.platform(6, 12, 22)
    c.platform(18, 29, 18)
    c.platform(34, 41, 22)
    c.platform(18, 29, 11)
    add("biotech_1", 14, "Biotech Research Area 1", 3, 2, 11, 5, c)

    # P16 Deck Beta Security Hall
    c = hall(2)
    c.fill(15, 3, 16, 7)
    add("security_hall", 16, "Deck Beta Security Hall", 2, 1, 9, 6, c)

    # P17 Connection Elevator to Deck Beta (Gamma side, escape): climbs from the reactor deck
    # back up to Biotech Area 1, so it spans the cargo lift's height on the map
    c = shaft(7)
    add("elevator_gamma", 17, "Connection Elevator to Deck Beta (Gamma)", 1, 7, 12, 7, c)

    # P18 / P22 Subventilation Shafts A / B
    add("subvent_a", 18, "Subventilation Shaft Section A", 1, 2, 11, 7, shaft(2))
    c = Canvas(3, 1)
    c.carve(2, 2, 45, 13)
    add("subvent_b", 22, "Subventilation Shaft Section B", 3, 1, 9, 9, c)

    # P20 Biohazard Containment
    c = box(2, 2)
    c.carve(1, 2, 30, 29)
    c.platform(4, 10, 20)
    c.platform(18, 26, 14)
    add("biohazard", 20, "Biohazard Containment", 2, 2, 7, 5, c)

    # P21 Deck Gamma Monitor Hall (escape)
    add("monitor_hall", 21, "Deck Gamma Monitor Hall", 3, 1, 9, 13, hall(3))

    # P24 Deck Beta Transit Hall
    add("transit_hall", 24, "Deck Beta Transit Hall", 1, 2, 7, 7, shaft(2))

    # P26 Cargo Freight Lift to Deck Gamma: tall lift shaft
    c = Canvas(2, 4)
    c.carve(1, 1, 30, 62)
    for i, y in enumerate(range(10, 60, 6)):
        if i % 2:
            c.platform(2, 9, y)
        else:
            c.platform(22, 29, y)
    add("cargo_lift", 26, "Cargo Freight Lift to Deck Gamma", 2, 4, 7, 9, c)

    # P27 Reactor Core Entrance: the frigate's only save station in Prime, right before the boss.
    # Pedestal in the left corner, clear of the ledge under the ceiling door.
    c = Canvas(1, 1)
    c.carve(2, 1, 13, 9)
    add("reactor_entrance", 27, "Reactor Core Entrance", 1, 1, 7, 13, c, save_station=(2, 10))

    # P25 Reactor Core: Parasite Queen arena. One screen, same shape as the vanilla Phantoon room
    # ($8F:CD13): Phantoon's movement is hard-coded for a 1x1 room.
    c = Canvas(1, 1)
    c.carve(2, 3, 13, 12)
    add("reactor_core", 25, "Reactor Core", 1, 1, 8, 13, c)
    return R


# (room, side, screen) <-> (room, side, screen); side pairs must be opposite (R-L, B-T)
LINKS = [
    # intro route
    (("hangar", "R", 1), ("airlock", "L", 0), False),
    (("airlock", "R", 0), ("access_hall", "L", 0), False),
    (("access_hall", "R", 0), ("evac_area", "L", 1), False),
    (("evac_area", "R", 0), ("umbilical_hall", "L", 0), False),
    (("umbilical_hall", "R", 0), ("map_facility", "L", 0), False),
    (("map_facility", "B", 1), ("elevator_beta", "T", 0), False),
    (("elevator_beta", "B", 0), ("conduit_hall", "T", 2), False),
    (("conduit_hall", "L", 0), ("biotech_1", "R", 0), False),
    (("biotech_1", "L", 1), ("security_hall", "R", 0), False),
    (("security_hall", "L", 0), ("biohazard", "R", 1), False),
    (("biohazard", "B", 0), ("transit_hall", "T", 0), False),
    (("transit_hall", "B", 0), ("cargo_lift", "T", 0), False),
    (("cargo_lift", "B", 0), ("reactor_entrance", "T", 0), False),
    # boss door: grey on the arena side, Samus is locked in until the Parasite Queen dies
    (("reactor_core", "L", 0), ("reactor_entrance", "R", 0), True),
    # escape route (grey doors on the intro side open when the Parasite Queen dies)
    (("reactor_core", "R", 0), ("monitor_hall", "L", 0), True),
    (("monitor_hall", "R", 0), ("elevator_gamma", "L", 6), False),
    (("biotech_1", "B", 1), ("elevator_gamma", "T", 0), True),
    (("biotech_1", "B", 0), ("subvent_a", "T", 0), True),
    (("subvent_a", "B", 0), ("subvent_b", "T", 2), False),
    (("cargo_lift", "R", 0), ("subvent_b", "L", 0), True),
    (("cargo_lift", "L", 3), ("vent_a", "R", 1), True),
    (("vent_a", "B", 0), ("vent_b", "T", 0), False),
    (("vent_b", "L", 1), ("vent_c", "R", 0), False),
    (("vent_c", "L", 0), ("vent_d", "R", 1), False),
    (("vent_d", "T", 0), ("vent_e", "B", 0), False),
    (("vent_e", "T", 0), ("vent_f", "B", 0), False),
    (("vent_f", "T", 0), ("biotech_2", "B", 0), False),
    (("biotech_2", "T", 2), ("elevator_alpha", "B", 0), False),
    (("elevator_alpha", "R", 0), ("mech_shaft", "L", 1), False),
    (("airlock", "B", 0), ("mech_shaft", "T", 0), True),
]

# When the flag is True, the FIRST side of the link is the locked one: always the side Samus can
# reach before the boss. The far side stays open (it is only reachable during the escape).


def build_rooms() -> list[RoomDef]:
    rooms = make_rooms()
    for (a, b, locked) in LINKS:
        (ra, sa, na), (rb, sb, nb) = a, b
        if OPPOSITE[sa] != sb:
            raise ValueError(f"porta {ra}.{sa} liga em {rb}.{sb}: lados precisam ser opostos")
        da = DoorLink(sa, na, rb, locked=locked)
        db = DoorLink(sb, nb, ra)
        rooms[ra].doors.append(da)
        rooms[rb].doors.append(db)
        da.to_door = len(rooms[rb].doors) - 1
        db.to_door = len(rooms[ra].doors) - 1
    return list(rooms.values())


ROOMS = build_rooms()

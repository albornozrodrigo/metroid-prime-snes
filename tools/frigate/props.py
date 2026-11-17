"""Background set pieces of the frigate, built from Wrecked Ship (tileset 4) metatiles.

A prop is drawn on layer 1 as air (block type 0): Samus passes in front of it. Props stand on
the floor; tools/validate.py checks that every cell is open air and the row under the prop is
solid. Positions are in blocks: `x` is the left column, `floor` the row of the solid block under it.
"""
from __future__ import annotations

from dataclasses import dataclass

H = 0x400  # h-flip

# rows top to bottom; None leaves the cell as it is
STAMPS: dict[str, list[list[int | None]]] = {
    # Prime's Biotech Research Areas: pirates asleep in stasis tanks.
    # Glass dome with a specimen ($1CA/$1CB), tank body with blue fluid ($1E8), machine base ($1E9).
    "stasis_tank": [
        [0x1CA, 0x1CB],
        [0x1E8, 0x1E8 | H],
        [0x1E8, 0x1E8 | H],
        [0x1E9, 0x1E9 | H],
    ],
    # pirate workstation: blue displays ($1DE/$1DF) over a control panel ($113/$114)
    "console": [
        [0x1DE, 0x1DF],
        [0x113, 0x114],
    ],
}


@dataclass(frozen=True)
class Prop:
    stamp: str
    x: int
    floor: int

    @property
    def rows(self) -> list[list[int | None]]:
        return STAMPS[self.stamp]

    def cells(self):
        """(x, y, metatile) for each drawn cell."""
        rows = self.rows
        top = self.floor - len(rows)
        for dy, row in enumerate(rows):
            for dx, mt in enumerate(row):
                if mt is not None:
                    yield self.x + dx, top + dy, mt


def tanks(xs: list[int], floor: int) -> list[Prop]:
    return [Prop("stasis_tank", x, floor) for x in xs]


def consoles(xs: list[int], floor: int) -> list[Prop]:
    return [Prop("console", x, floor) for x in xs]


PROPS: dict[str, list[Prop]] = {
    "biotech_1": tanks([14, 31, 36, 42], 31),
    "biotech_2": tanks([16, 30], 29) + consoles([40], 29),
    "map_facility": consoles([12], 14),
    "monitor_hall": consoles([12, 22, 34], 10),     # Prime: the hall of pirate monitors
    "security_hall": consoles([7, 24], 10),
    "reactor_entrance": consoles([8], 10),
}


# --- Exterior Docking Hangar (Prime P0): open to space above, docking bay below -----------------
# Background pieces are the dark Wrecked Ship back-wall metatiles ($2xx), drawn as air: they read
# as far away, so nothing that looks solid is passable (same rule as tools/smlib/style.py).
V = 0x800  # v-flip

HANGAR_SHIP_X = 54            # tools/frigate/rooms.py: hangar ship=(54, 26)
HANGAR_FLOOR = 26


def hangar_backdrop() -> list[tuple[int, int, int]]:
    cells = []
    # docking clamps: columns from the deck up to the ship's belly, at both ends of the hull
    for x in (HANGAR_SHIP_X - 4, HANGAR_SHIP_X + 3):
        cells += [(x, y, 0x2DB) for y in range(HANGAR_FLOOR - 3, HANGAR_FLOOR)]
    # back wall of the bay: 5 rows over the deck, a light band on top, starfield above it
    top = HANGAR_FLOOR - 5
    for x in range(15, 61):
        cells.append((x, top, (0x2D0, 0x2D1)[x % 2]))
        for y in range(top + 1, HANGAR_FLOOR):
            cells.append((x, y, (0x2EF, 0x2F0)[(x + y) % 2]))
    return cells


def hangar_pad() -> list[tuple[int, int, int]]:
    """Landing pad: the deck under the ship gets a lit strip (ceiling light pieces, v-flipped)."""
    x0 = HANGAR_SHIP_X - 6
    out = []
    for i, x in enumerate(range(x0, x0 + 13)):
        out.append((x, HANGAR_FLOOR, (0x115, 0x116, 0x117)[i % 3] | V))
    return out


BACKDROPS: dict[str, list[tuple[int, int, int]]] = {"hangar": hangar_backdrop()}
SKINS: dict[str, list[tuple[int, int, int]]] = {"hangar": hangar_pad()}

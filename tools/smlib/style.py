"""Dress the walls of a level built from ASCII with Wrecked Ship (tileset 4) metatiles.

Pieces come from the vanilla WS rooms. Wall faces ($120), corners ($15B, $129/$12E/$186/$187)
are what vanilla uses most for each neighbourhood. The hull texture, ceiling and floor are the ones
of the clean WS room $8F:CC27: a 3-block repeat of light ($100) and bars ($198/$199) inside walls
and along ceilings, riveted plates ($12B/$12C) on floors. The WS set is full of moss and debris;
the frigate is a working pirate ship, so only clean metal pieces are used.

Only blocks of type 8 (solid) are restyled; doors, caps and platforms keep their metatiles.
Decorations are embedded in wall surfaces (never in the air), so nothing that looks solid is
passable.
"""
from __future__ import annotations

from dataclasses import dataclass

H = 0x400   # metatile h-flip bit in a block word
SOLID = 0x8
PLATFORM = 0x13C
AIR_WORD = 0x00FF


@dataclass(frozen=True)
class Style:
    floor: tuple[int, ...] = (0x12B, 0x12C)
    hull: tuple[int, ...] = (0x100, 0x198, 0x199)   # also the ceiling surface, as in $8F:CC27
    wall_face_right: int = 0x120          # wall whose right side touches air; h-flip for the left
    outer_corner: int = 0x15B             # h-flip for the right-hand corners
    thin_pillar: int = 0x118
    inner_nw: int = 0x129
    inner_ne: int = 0x12E | H
    inner_sw: int = 0x186
    inner_se: int = 0x187
    ceiling_light: tuple[int, ...] = (0x115, 0x116, 0x117)   # blue light strip
    light_every: int = 16                  # blocks between ceiling lights
    strut: int = 0x11F                     # background column under platforms (tiles vertically)
    strut_min_platform: int = 4

    def apply(self, l1: list[int], wb: int, hb: int) -> list[int]:
        solid = [[(l1[y * wb + x] >> 12) == SOLID for x in range(wb)] for y in range(hb)]

        def s(x: int, y: int) -> bool:
            return solid[y][x] if 0 <= x < wb and 0 <= y < hb else True

        out = list(l1)
        for y in range(hb):
            for x in range(wb):
                w = l1[y * wb + x]
                if w >> 12 != SOLID or (w & 0x3FF) == PLATFORM:
                    continue
                out[y * wb + x] = (w & 0xF000) | self.pick(x, y, s)
        self._ceiling_lights(out, l1, wb, hb, s)
        self._struts(out, wb, hb)
        return out

    def _struts(self, out: list[int], wb: int, hb: int) -> None:
        """Background columns from both ends of each platform down to the floor, so platforms
        read as catwalks on supports instead of floating bricks. Only through plain air; a column
        that would end anywhere but on a solid block is not drawn."""
        def is_platform(x: int, y: int) -> bool:
            w = out[y * wb + x]
            return w >> 12 == SOLID and (w & 0x3FF) == PLATFORM

        for y in range(hb - 1):
            x = 0
            while x < wb:
                if not is_platform(x, y):
                    x += 1
                    continue
                start = x
                while x < wb and is_platform(x, y):
                    x += 1
                if x - start < self.strut_min_platform:
                    continue
                for cx in (start + 1, x - 2):
                    cells = []
                    cy = y + 1
                    while cy < hb and out[cy * wb + cx] == AIR_WORD:
                        cells.append(cy)
                        cy += 1
                    if cells and cy < hb and out[cy * wb + cx] >> 12 == SOLID:
                        for yy in cells:
                            out[yy * wb + cx] = self.strut

    def pick(self, x: int, y: int, s) -> int:
        n, e, so, w = not s(x, y - 1), not s(x + 1, y), not s(x, y + 1), not s(x - 1, y)
        if n and so:
            return PLATFORM
        if w and e:
            return self.thin_pillar
        if (n or so) and w:
            return self.outer_corner
        if (n or so) and e:
            return self.outer_corner | H
        if n:
            return self.floor[x % len(self.floor)]
        if so:
            return self.hull[x % len(self.hull)]
        if w:
            return self.wall_face_right | H
        if e:
            return self.wall_face_right
        if not s(x - 1, y - 1):
            return self.inner_nw
        if not s(x + 1, y - 1):
            return self.inner_ne
        if not s(x - 1, y + 1):
            return self.inner_sw
        if not s(x + 1, y + 1):
            return self.inner_se
        return self.hull[x % len(self.hull)]

    def _ceiling_lights(self, out: list[int], l1: list[int], wb: int, hb: int, s) -> None:
        """Blue light strips set into long ceilings, centred in runs of plain ceiling blocks."""
        k = len(self.ceiling_light)

        def plain_ceiling(x: int, y: int) -> bool:
            return s(x, y) and not s(x, y + 1) and (out[y * wb + x] & 0x3FF) in self.hull

        for y in range(hb):
            x = 0
            while x < wb:
                if not plain_ceiling(x, y):
                    x += 1
                    continue
                start = x
                while x < wb and plain_ceiling(x, y):
                    x += 1
                run = x - start
                if run < k + 4:
                    continue
                n = max(1, run // self.light_every)
                for i in range(n):
                    cx = start + (2 * i + 1) * run // (2 * n) - k // 2
                    for j in range(k):
                        out[y * wb + cx + j] = (l1[y * wb + cx + j] & 0xF000) | self.ceiling_light[j]


FRIGATE = Style()


V = 0x800   # metatile v-flip bit in a block word


@dataclass(frozen=True)
class EdgeStyle:
    """Dresses solid blocks by which of their 4 sides touch air, with pieces read from vanilla
    rooms (tools/smlib/crateria.py; specs/07c-estilo-crateria.md). Every piece is a metatile word
    (id + flip bits). Sequences are picked by position, so the result is the same on every build.

    Solid blocks (type 8) are restyled; doors, caps and anything else keep their metatiles. A
    block with air above and below (a 1-block-thick ledge, or a '=' platform) gets the platform
    pieces. `grass` pieces are drawn as plain air (type 0) on the air block right above a floor,
    never on a block that already has something.
    """
    name: str
    tileset: int
    fill: tuple[int, ...]       # inside walls, and wherever no other piece fits
    floor: tuple[int, ...]      # air above
    ceiling: tuple[int, ...]    # air below
    wall_w: tuple[int, ...]     # air to the west (left)
    wall_e: tuple[int, ...]     # air to the east (right)
    platform: tuple[int, ...]   # air above and below: middle of a ledge
    # single pieces; None = no piece of its own: an outer corner continues the floor/ceiling row,
    # the others continue the fill (keeps a pattern like a brick bond unbroken)
    outer_nw: int | None = None     # air above and to the west
    outer_ne: int | None = None
    outer_sw: int | None = None     # air below and to the west
    outer_se: int | None = None
    inner_nw: int | None = None     # solid on all 4 sides, air diagonally up-left
    inner_ne: int | None = None
    inner_sw: int | None = None
    inner_se: int | None = None
    pillar: int | None = None       # air west and east (1-block-wide column)
    platform_l: int | None = None   # left end of a ledge (air to the west too)
    platform_r: int | None = None   # its right end
    grass: tuple[int, ...] = ()     # air decoration on top of floors
    grass_every: int = 3            # one tuft every N floor blocks (0 = none)

    def solid_pieces(self) -> set[int]:
        single = {self.outer_nw, self.outer_ne, self.outer_sw, self.outer_se, self.inner_nw,
                  self.inner_ne, self.inner_sw, self.inner_se, self.pillar, self.platform_l,
                  self.platform_r} - {None}
        return single | {*self.fill, *self.floor, *self.ceiling, *self.wall_w, *self.wall_e,
                         *self.platform}

    def air_pieces(self) -> set[int]:
        return set(self.grass)

    def apply(self, l1: list[int], wb: int, hb: int) -> list[int]:
        solid = [[(l1[y * wb + x] >> 12) == SOLID for x in range(wb)] for y in range(hb)]

        def s(x: int, y: int) -> bool:
            return solid[y][x] if 0 <= x < wb and 0 <= y < hb else True

        out = list(l1)
        for y in range(hb):
            for x in range(wb):
                if solid[y][x]:
                    out[y * wb + x] = (SOLID << 12) | self.pick(x, y, s)
        if self.grass and self.grass_every:
            for y in range(1, hb):
                for x in range(wb):
                    if (solid[y][x] and not s(x, y - 1) and out[(y - 1) * wb + x] == AIR_WORD
                            and (x * 7 + y * 3) % self.grass_every == 0):
                        out[(y - 1) * wb + x] = self.grass[(x + y) % len(self.grass)]
        return out

    def pick(self, x: int, y: int, s) -> int:
        def seq(pieces: tuple[int, ...], i: int) -> int:
            return pieces[i % len(pieces)]

        fill = seq(self.fill, x + y)
        n, e, so, w = not s(x, y - 1), not s(x + 1, y), not s(x, y + 1), not s(x - 1, y)
        if n and so:
            if w and not e:
                return fill if self.platform_l is None else self.platform_l
            if e and not w:
                return fill if self.platform_r is None else self.platform_r
            return seq(self.platform, x + y)
        if w and e:
            return fill if self.pillar is None else self.pillar
        top, bottom = seq(self.floor, x), seq(self.ceiling, x)
        for side, corner, row in ((n and w, self.outer_nw, top), (n and e, self.outer_ne, top),
                                  (so and w, self.outer_sw, bottom), (so and e, self.outer_se, bottom)):
            if side:
                return row if corner is None else corner
        if n:
            return top
        if so:
            return bottom
        if w:
            return seq(self.wall_w, x + y)
        if e:
            return seq(self.wall_e, x + y)
        for dx, dy, corner in ((-1, -1, self.inner_nw), (1, -1, self.inner_ne),
                               (-1, 1, self.inner_sw), (1, 1, self.inner_se)):
            if not s(x + dx, y + dy):
                return fill if corner is None else corner
        return fill

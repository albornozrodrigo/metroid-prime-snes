"""Tiny drawing API to author room layouts in code instead of 256-character ASCII lines."""
from __future__ import annotations

from .level import SCREEN

TOP_DOOR_LEDGE_ROW = 6


class Canvas:
    def __init__(self, width_screens: int, height_screens: int):
        self.w = width_screens * SCREEN
        self.h = height_screens * SCREEN
        self.cells = [["#"] * self.w for _ in range(self.h)]

    def _set(self, x: int, y: int, c: str) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.cells[y][x] = c

    def carve(self, x0: int, y0: int, x1: int, y1: int) -> "Canvas":
        """Open air in the inclusive block rectangle."""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self._set(x, y, ".")
        return self

    def fill(self, x0: int, y0: int, x1: int, y1: int, c: str = "#") -> "Canvas":
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self._set(x, y, c)
        return self

    def platform(self, x0: int, x1: int, y: int) -> "Canvas":
        for x in range(x0, x1 + 1):
            self._set(x, y, "=")
        return self

    def map_station(self, x: int, floor: int) -> "Canvas":
        """T-shaped base of a map station, copied from the vanilla map rooms ($8F:9994): the
        station PLM sits at (x, floor-2), at the height of Samus' cannon, on a row of 4 solid
        blocks (x-2..x+1; the two ends become the access blocks) over a 2-block stem."""
        self.fill(x - 2, floor - 2, x + 1, floor - 2)
        self.fill(x - 1, floor - 1, x, floor - 1)
        return self

    def refill_station(self, x: int, floor: int) -> "Canvas":
        """specs/19l: base of a refill station (the SM's missile station, PLM $B6EB), copied from the vanilla refill rooms
        ($8F:8550's room, level $CE:8CB3: the station block on row 10 over a 1-block stem, the floor on row 12): the PLM sits at
        (x, floor-2), at the height of Samus' cannon, its two neighbours (x-1, x+1) the access blocks it writes (type B, BTS
        $4C/$4B: PlmSetup_PlmB6EB, sm_84.c), here solid already, over the stem (x, floor-1)."""
        self.fill(x - 1, floor - 2, x + 1, floor - 2)
        self.fill(x, floor - 1, x, floor - 1)
        return self

    def door_gap(self, side: str, screen: int) -> "Canvas":
        """Make sure the 4 rows/cols in front of a door are open air."""
        if side in "LR":
            y0 = screen * SCREEN + 6
            xs = range(0, 4) if side == "L" else range(self.w - 4, self.w)
            for x in xs:
                for y in range(y0, y0 + 4):
                    self._set(x, y, ".")
            # 6-block ledge under the door, like vanilla rooms
            ledge = range(0, 6) if side == "L" else range(self.w - 6, self.w)
            for x in ledge:
                self._set(x, y0 + 4, "#")
        else:
            x0 = screen * SCREEN + 6
            ys = range(0, 4) if side == "T" else range(self.h - 4, self.h)
            for y in ys:
                for x in range(x0, x0 + 4):
                    self._set(x, y, ".")
            if side == "B":
                # ledges on both sides of a floor door: Samus coming up through it lands here
                # instead of falling straight back down (vanilla rooms do the same)
                y = self.h - 3  # same row as the door cap, like vanilla
                for x in list(range(x0 - 3, x0)) + list(range(x0 + 4, x0 + 7)):
                    self._set(x, y, "=")
            if side == "T":
                # platform under a ceiling door so Samus can jump up into it
                for x in range(x0 - 2, x0 + 6):
                    self._set(x, TOP_DOOR_LEDGE_ROW, "=")
        return self

    def rows(self) -> list[str]:
        return ["".join(r) for r in self.cells]

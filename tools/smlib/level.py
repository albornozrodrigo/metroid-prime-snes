"""Build Super Metroid level data (layer 1 blocks + BTS) from an ASCII drawing.

Block word: bits 0-9 metatile, bit 10 h-flip, bit 11 v-flip, bits 12-15 block type.
Block types used here: 0 air, 3 special air, 5 horizontal extension, 8 solid, 9 door,
C shootable (door caps), D vertical extension.
The door patterns below were copied from vanilla Wrecked Ship rooms ($8F:CA08, $8F:CAF6).
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

from .compression import compress
from .style import EdgeStyle, Style

AIR = 0x00FF
SCREEN = 16  # blocks per screen side


def word(block_type: int, metatile: int, hflip: bool = False, vflip: bool = False) -> int:
    return (block_type << 12) | (0x800 if vflip else 0) | (0x400 if hflip else 0) | (metatile & 0x3FF)


@dataclass
class Palette:
    """Metatiles used to dress the ASCII map. Defaults: Wrecked Ship tileset (4/5)."""
    wall_fill: int = 0x3FF       # solid filler deep inside walls
    wall_edge: int = 0x101       # wall surface that touches air
    platform: int = 0x13C        # thin platform / girder
    background: int = AIR        # empty space


# ASCII legend
#   '.' air            '#' wall (auto: edge or fill)      '=' platform (solid)
#   ' ' same as '.'    'S' Samus spawn marker (air)       'x' wall forced as fill
LEGEND_AIR = set(". S")


@dataclass
class Door:
    side: str          # 'L', 'R', 'T', 'B'
    screen: int        # which screen along that wall (0-based)
    index: int = -1    # door list index, filled in by the builder
    cap: bool = True   # draw a blue door cap


@dataclass
class Level:
    width: int   # screens
    height: int  # screens
    rows: list[str]
    palette: Palette = field(default_factory=Palette)
    doors: list[Door] = field(default_factory=list)
    style: Style | EdgeStyle | None = None   # restyles the walls after the doors are stamped
    decor: list[tuple[int, int, int]] = field(default_factory=list)   # (x, y, metatile) drawn as air
    # (x, y, block word, BTS) written last, as is: collision that the level art doesn't draw
    overlay: list[tuple[int, int, int, int]] = field(default_factory=list)
    # (x, y, metatile) drawn after the style: on plain air cells only (background, e.g. a back
    # wall), or on solid cells keeping their collision (`skin`, e.g. a landing pad)
    backdrop: list[tuple[int, int, int]] = field(default_factory=list)
    skin: list[tuple[int, int, int]] = field(default_factory=list)

    @property
    def wb(self) -> int:
        return self.width * SCREEN

    @property
    def hb(self) -> int:
        return self.height * SCREEN

    def validate(self) -> None:
        if len(self.rows) != self.hb:
            raise ValueError(f"desenho tem {len(self.rows)} linhas, esperado {self.hb}")
        for i, r in enumerate(self.rows):
            if len(r) != self.wb:
                raise ValueError(f"linha {i} tem {len(r)} colunas, esperado {self.wb}: {r!r}")

    def build_blocks(self) -> tuple[list[int], bytearray]:
        self.validate()
        wb, hb = self.wb, self.hb
        l1 = [AIR] * (wb * hb)
        bts = bytearray(wb * hb)
        solid = [[c not in LEGEND_AIR for c in row] for row in self.rows]

        def is_solid(x: int, y: int) -> bool:
            if 0 <= x < wb and 0 <= y < hb:
                return solid[y][x]
            return True

        for y, row in enumerate(self.rows):
            for x, c in enumerate(row):
                i = y * wb + x
                if c in LEGEND_AIR:
                    l1[i] = word(0, self.palette.background)
                elif c == "=":
                    l1[i] = word(8, self.palette.platform)
                elif c == "x":
                    l1[i] = word(8, self.palette.wall_fill)
                elif c == "#":
                    touches_air = any(not is_solid(x + dx, y + dy)
                                      for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
                    l1[i] = word(8, self.palette.wall_edge if touches_air else self.palette.wall_fill)
                else:
                    raise ValueError(f"caractere desconhecido {c!r} em ({x},{y})")
        for door in self.doors:
            self._stamp_door(l1, bts, door)
        if self.style:
            l1 = self.style.apply(l1, wb, hb)
        for x, y, mt in self.backdrop:
            if l1[y * wb + x] == AIR:
                l1[y * wb + x] = word(0, mt & 0x3FF, bool(mt & 0x400), bool(mt & 0x800))
        for x, y, mt in self.skin:
            if l1[y * wb + x] >> 12 != 8:
                raise ValueError(f"acabamento em ({x},{y}) cai num bloco que não é sólido")
            l1[y * wb + x] = word(8, mt & 0x3FF, bool(mt & 0x400), bool(mt & 0x800))
        for x, y, mt in self.decor:
            if l1[y * wb + x] >> 12 != 0:
                raise ValueError(f"decoração em ({x},{y}) cai num bloco que não é ar")
            l1[y * wb + x] = word(0, mt & 0x3FF, bool(mt & 0x400), bool(mt & 0x800))
        for x, y, w, b in self.overlay:
            if l1[y * wb + x] >> 12 != 0:
                raise ValueError(f"bloco sobreposto em ({x},{y}) cai num bloco que não é ar")
            l1[y * wb + x] = w
            bts[y * wb + x] = b
        return l1, bts

    def _stamp_door(self, l1: list[int], bts: bytearray, d: Door) -> None:
        wb, hb = self.wb, self.hb

        def put(x: int, y: int, w: int, b: int = 0) -> None:
            l1[y * wb + x] = w
            bts[y * wb + x] = b

        if d.side in "LR":
            y0 = d.screen * SCREEN + 6  # doors sit on rows 6-9 of their screen, like vanilla
            frame = [0x040, 0x060, 0x060, 0x040]
            vfl = [False, False, True, True]
            ext = [None, 0xFF, 0xFE, 0xFD]
            if d.side == "L":
                xd, xc, hf, cap_bts = 0, 1, True, 0x41
            else:
                xd, xc, hf, cap_bts = wb - 1, wb - 2, False, 0x40
            for k in range(4):
                put(xd, y0 + k, word(9, frame[k], hf, vfl[k]), d.index)
                cap_mt = 0x00C if k in (0, 3) else 0x02C
                if d.cap:
                    if k == 0:
                        put(xc, y0, word(0xC, 0x00C, hf, False), cap_bts)
                    else:
                        put(xc, y0 + k, word(0xD, cap_mt, hf, k >= 2), ext[k])
                else:
                    put(xc, y0 + k, word(0, AIR))
            # clear the 2 columns inside the door so Samus can walk through
            for k in range(4):
                xin = xc + (1 if d.side == "L" else -1)
                if l1[(y0 + k) * wb + xin] >> 12 == 8:
                    put(xin, y0 + k, word(0, AIR))
        else:
            x0 = d.screen * SCREEN + 6
            frame = [0x063, 0x062, 0x062, 0x063]
            hfl = [True, True, False, False]
            frame2 = [0x043, 0x042, 0x042, 0x043]
            cap_mt = [0x01D, 0x01C, 0x01C, 0x01D]
            ext = [None, 0xFF, 0xFE, 0xFD]
            if d.side == "T":
                yd, yf, yc, vf, cap_bts = 0, 1, 2, True, 0x43
            else:
                yd, yf, yc, vf, cap_bts = hb - 1, hb - 2, hb - 3, False, 0x42
            for k in range(4):
                put(x0 + k, yd, word(9, frame[k], hfl[k], vf), d.index)
                put(x0 + k, yf, word(0, frame2[k], hfl[k], vf))
                if d.cap:
                    if k == 0:
                        put(x0, yc, word(0xC, cap_mt[0], hfl[0], vf), cap_bts)
                    else:
                        put(x0 + k, yc, word(5, cap_mt[k], hfl[k], vf), ext[k])
                else:
                    put(x0 + k, yc, word(0, AIR))

    def compressed(self) -> bytes:
        l1, bts = self.build_blocks()
        size = len(l1) * 2
        raw = struct.pack("<H", size) + struct.pack(f"<{len(l1)}H", *l1) + bytes(bts)
        return compress(raw)

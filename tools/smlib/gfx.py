"""Render Super Metroid tilesets and room level data to PNG (for design and checking)."""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

from .compression import decompress
from .rom import Rom, snes_to_pc

TILESET_TABLE = 0x8FE7A7  # word pointers (bank $8F) to {tile table, tiles, palette} 24-bit pointers
CRE_TILES = 0xB98000      # common room elements graphics
CRE_TILE_TABLE = 0xB9A09D  # common room elements metatile table
CERES_AREA = 6


def write_png(path: str | Path, width: int, height: int, rgb: bytes) -> None:
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    Path(path).write_bytes(png)


@dataclass
class Tileset:
    index: int
    vram: bytes        # 4bpp tiles, tile n at n*32
    palette: list[tuple[int, int, int]]  # 256 colors
    metatiles: bytes   # 4 tilemap words per metatile, metatile n at n*8


def _decomp(rom: Rom, addr: int) -> bytes:
    return decompress(rom.data, snes_to_pc(addr))[0]


def load_tileset(rom: Rom, index: int, area: int = 0) -> Tileset:
    entry = 0x8F0000 | rom.u16(TILESET_TABLE + 2 * index)
    table_ptr, tiles_ptr, pal_ptr = rom.u24(entry), rom.u24(entry + 3), rom.u24(entry + 6)
    sce_tiles = _decomp(rom, tiles_ptr)
    vram = bytearray(0x8000)
    vram[:min(len(sce_tiles), 0x8000)] = sce_tiles[:0x8000]
    if area != CERES_AREA:
        cre = _decomp(rom, CRE_TILES)
        vram[0x5000:0x5000 + min(len(cre), 0x3000)] = cre[:0x3000]
    pal_raw = _decomp(rom, pal_ptr)
    palette = []
    for i in range(256):
        c = pal_raw[2 * i] | (pal_raw[2 * i + 1] << 8) if 2 * i + 1 < len(pal_raw) else 0
        r, g, b = c & 31, (c >> 5) & 31, (c >> 10) & 31
        palette.append(((r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2)))
    sce_table = _decomp(rom, table_ptr)
    if area == CERES_AREA:
        metatiles = sce_table
    else:
        metatiles = bytearray(0x2000)
        cre_table = _decomp(rom, CRE_TILE_TABLE)
        metatiles[:0x800] = cre_table[:0x800]
        metatiles[0x800:0x800 + len(sce_table)] = sce_table[:0x2000 - 0x800]
        metatiles = bytes(metatiles)
    return Tileset(index, bytes(vram), palette, metatiles)


def _draw_tile(canvas: bytearray, cw: int, x0: int, y0: int, ts: Tileset, word: int) -> None:
    tile = word & 0x3FF
    pal = (word >> 10) & 7
    hflip = word & 0x4000
    vflip = word & 0x8000
    base = tile * 32
    for row in range(8):
        sy = 7 - row if vflip else row
        b0 = ts.vram[base + sy * 2] if base + 32 <= len(ts.vram) else 0
        b1 = ts.vram[base + sy * 2 + 1] if base + 32 <= len(ts.vram) else 0
        b2 = ts.vram[base + 16 + sy * 2] if base + 32 <= len(ts.vram) else 0
        b3 = ts.vram[base + 16 + sy * 2 + 1] if base + 32 <= len(ts.vram) else 0
        for col in range(8):
            sx = col if hflip else 7 - col
            ci = ((b0 >> sx) & 1) | (((b1 >> sx) & 1) << 1) | (((b2 >> sx) & 1) << 2) | (((b3 >> sx) & 1) << 3)
            if ci == 0:
                continue
            r, g, b = ts.palette[pal * 16 + ci]
            o = ((y0 + row) * cw + x0 + col) * 3
            canvas[o:o + 3] = bytes((r, g, b))


def draw_metatile(canvas: bytearray, cw: int, x0: int, y0: int, ts: Tileset, block_word: int) -> None:
    mt = block_word & 0x3FF
    hflip = bool(block_word & 0x400)
    vflip = bool(block_word & 0x800)
    words = struct.unpack_from("<4H", ts.metatiles, mt * 8) if mt * 8 + 8 <= len(ts.metatiles) else (0, 0, 0, 0)
    for k, w in enumerate(words):
        qx, qy = k & 1, k >> 1
        if hflip:
            qx ^= 1
            w ^= 0x4000
        if vflip:
            qy ^= 1
            w ^= 0x8000
        _draw_tile(canvas, cw, x0 + qx * 8, y0 + qy * 8, ts, w)


def render_tileset_sheet(ts: Tileset, path: str | Path, first: int = 0, count: int = 1024, cols: int = 32) -> None:
    """Grid of metatiles; metatile id = first + row*cols + col. A 1px grid separates them."""
    rows = (count + cols - 1) // cols
    cw, ch = cols * 17 + 1, rows * 17 + 1
    canvas = bytearray(b"\x30\x00\x30" * (cw * ch))
    for i in range(count):
        x0, y0 = 1 + (i % cols) * 17, 1 + (i // cols) * 17
        for yy in range(16):
            o = ((y0 + yy) * cw + x0) * 3
            canvas[o:o + 48] = bytes(ts.palette[0]) * 16
        draw_metatile(canvas, cw, x0, y0, ts, first + i)
    write_png(path, cw, ch, bytes(canvas))


BLOCK_TYPE_COLORS = {
    0x1: (255, 0, 255), 0x3: (0, 255, 0), 0x9: (0, 160, 255), 0xA: (255, 0, 0),
    0xB: (255, 255, 0), 0xC: (255, 128, 0), 0xE: (0, 255, 255), 0xF: (255, 255, 255),
}


def render_level(ts: Tileset, layer1: list[int], width_blocks: int, height_blocks: int, path: str | Path,
                 overlay_types: bool = False) -> None:
    cw, ch = width_blocks * 16, height_blocks * 16
    canvas = bytearray(bytes(ts.palette[0]) * (cw * ch))
    for by in range(height_blocks):
        for bx in range(width_blocks):
            word = layer1[by * width_blocks + bx]
            draw_metatile(canvas, cw, bx * 16, by * 16, ts, word)
            btype = word >> 12
            if overlay_types and btype in BLOCK_TYPE_COLORS:
                color = bytes(BLOCK_TYPE_COLORS[btype])
                for k in range(16):  # outline the block
                    for (x, y) in ((bx * 16 + k, by * 16), (bx * 16 + k, by * 16 + 15),
                                   (bx * 16, by * 16 + k), (bx * 16 + 15, by * 16 + k)):
                        o = (y * cw + x) * 3
                        canvas[o:o + 3] = color
    write_png(path, cw, ch, bytes(canvas))


# --- 4bpp tiles (SNES planar) -------------------------------------------------------------------

def decode_4bpp(tile: bytes) -> list[int]:
    """32 bytes of SNES 4bpp planar data -> 64 colour indices, row by row."""
    out = []
    for row in range(8):
        b0, b1, b2, b3 = tile[row * 2], tile[row * 2 + 1], tile[16 + row * 2], tile[16 + row * 2 + 1]
        for col in range(8):
            s = 7 - col
            out.append(((b0 >> s) & 1) | (((b1 >> s) & 1) << 1) | (((b2 >> s) & 1) << 2) | (((b3 >> s) & 1) << 3))
    return out


def encode_4bpp(px: list[int]) -> bytes:
    """64 colour indices (0-15) -> 32 bytes of SNES 4bpp planar data."""
    out = bytearray(32)
    for row in range(8):
        for col in range(8):
            v = px[row * 8 + col]
            if not 0 <= v <= 15:
                raise ValueError(f"cor {v} fora de 0-15")
            bit = 0x80 >> col
            if v & 1: out[row * 2] |= bit
            if v & 2: out[row * 2 + 1] |= bit
            if v & 4: out[16 + row * 2] |= bit
            if v & 8: out[16 + row * 2 + 1] |= bit
    return bytes(out)


def flip_tile(px: list[int], h: bool, v: bool) -> list[int]:
    return [px[(7 - r if v else r) * 8 + (7 - c if h else c)] for r in range(8) for c in range(8)]


class TileDeduper:
    """Collects unique 8x8 tiles; a tile equal to a flipped copy of a known one reuses it."""

    def __init__(self, limit: int):
        self.limit = limit
        self.tiles: list[list[int]] = []
        self._index: dict[tuple, tuple[int, bool, bool]] = {}

    def add(self, px: list[int]) -> tuple[int, bool, bool]:
        """Returns (tile number from 0, hflip, vflip) such that drawing it gives `px`."""
        key = tuple(px)
        if key in self._index:
            return self._index[key]
        if len(self.tiles) >= self.limit:
            raise ValueError(f"arte precisa de mais de {self.limit} tiles")
        n = len(self.tiles)
        self.tiles.append(list(px))
        for h in (False, True):
            for v in (False, True):
                self._index.setdefault(tuple(flip_tile(px, h, v)), (n, h, v))
        return self._index[key]

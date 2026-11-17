"""Starfield behind the Exterior Docking Hangar (Prime P0 is open to space).

The hangar gets its own library background ($8F command list, research/sm_room_format.md §1):
  - DMA a few star tiles to VRAM word $2400 (BG tiles $240-$27F). The Wrecked Ship SCE graphics
    are $4800 bytes (tiles $000-$23F) and the CRE starts at tile $280, so these 64 tiles are not
    used by any frigate room.
  - DMA a 64x32 BG2 tilemap of those tiles to $4800 (the same place the vanilla WS background
    $8F:E117 writes its two 32x32 screens).
Pixels use colour 0 (transparent: the black backdrop shows) and BG palette line 4, whose colours
1/2/3/13/14 are greys, a pale blue and white in the recoloured frigate palette.
"""
from __future__ import annotations

import random
import struct

STAR_VRAM = 0x2400           # VRAM word address; tile number = STAR_VRAM // 16
STAR_TILE0 = STAR_VRAM // 16
BG2_TILEMAP_VRAM = 0x4800
PALETTE_LINE = 4
LAYER2_SCROLL = 0x2121       # library BG (bit 0) + slow parallax $20/256 on both axes

# 8x8 tiles as {(x, y): colour}
TILES: list[dict[tuple[int, int], int]] = [
    {},                                                     # 0 empty space
    {(2, 5): 3},                                            # dim
    {(6, 1): 2},
    {(4, 3): 1},
    {(1, 6): 14},                                           # bright
    {(5, 2): 13},                                           # blue
    {(3, 3): 14, (2, 3): 13, (4, 3): 13, (3, 2): 13, (3, 4): 13},   # big star
    {(1, 1): 3, (6, 5): 2},
]
WEIGHTS = [72, 7, 6, 5, 3, 3, 1, 3]


def tile_bytes(pixels: dict[tuple[int, int], int]) -> bytes:
    """One 4bpp SNES tile (planes 0/1 interleaved in the first 16 bytes, 2/3 in the last 16)."""
    out = bytearray(32)
    for (x, y), c in pixels.items():
        bit = 0x80 >> x
        for plane in range(4):
            if c >> plane & 1:
                out[(plane >> 1) * 16 + y * 2 + (plane & 1)] |= bit
    return bytes(out)


def star_tiles() -> bytes:
    return b"".join(tile_bytes(t) for t in TILES)


def star_tilemap(seed: int = 4) -> bytes:
    """64x32 BG2 tilemap (two 32x32 screens, $1000 bytes); random flips vary the star positions."""
    rng = random.Random(seed)
    words = []
    for _ in range(64 * 32):
        t = rng.choices(range(len(TILES)), WEIGHTS)[0]
        w = (STAR_TILE0 + t) | (PALETTE_LINE << 10)
        if t:
            w |= rng.choice((0, 0x4000, 0x8000, 0xC000))
        words.append(w)
    return struct.pack(f"<{len(words)}H", *words)


def library_bg(tiles_at: int, n_tile_bytes: int, map_at: int) -> bytes:
    """Library-BG command list: op 2 = DMA (src24, VRAM word dst, size in bytes); 0 = end."""
    def dma(src: int, dst: int, size: int) -> bytes:
        return struct.pack("<H", 2) + struct.pack("<I", src)[:3] + struct.pack("<HH", dst, size)
    return dma(tiles_at, STAR_VRAM, n_tile_bytes) + dma(map_at, BG2_TILEMAP_VRAM, 0x1000) + b"\x00\x00"

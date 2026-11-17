"""Parasite Queen shape: Phantoon's body redrawn (specs/06-forma-parasite-queen.md).

Phantoon's body is BG2, not sprites: a 10x14-tile (80x112 px) tilemap built in WRAM $7E:2000 by
22 "extended tilemap" blocks in $A7:E0AA-$A7:E3D1 (body, eye 3 poses, iris 9 directions,
tentacles 3 poses, mouth 3 poses). Its tiles are tileset 4/5 graphics tiles $110-$18F, palette
line 7, and no metatile uses them. This module keeps that skeleton (AI, block sizes, hitbox
counts) and swaps the content: new tiles, new words and destinations inside the blocks, new
hitbox coordinates, new colours (tools/frigate/queen_draw.py has the drawing).

The tileset graphics are recompressed into the expanded banks and only tileset 4 is repointed;
tileset 5 (vanilla Wrecked Ship rooms) keeps Phantoon at $BB:AE9E.
"""
from __future__ import annotations

from frigate import queen_draw
from smlib.compression import compress, decompress
from smlib.gfx import TileDeduper, decode_4bpp, encode_4bpp, flip_tile
from smlib.rom import Rom, snes_to_pc

W, H = queen_draw.W, queen_draw.H   # BG2 area drawn by the blocks (10 x 14 tiles)
TILESET_TABLE = 0x8FE7A7
TILESET, TWIN_TILESET = 4, 5              # same graphics pointer in vanilla
VANILLA_GFX = 0xBBAE9E
FIRST_TILE, TILE_LIMIT = 0x110, 0x80      # $110-$18F: only Phantoon uses them
BLANK = 0x2338                            # transparent CRE tile $338, priority 1, as the vanilla blocks use
TILE_ATTRS = (7 << 10) | 0x2000           # palette line 7, priority 1
TILEMAP_RAM = 0x2000                      # $7E:2000, row = 64 bytes
BODY_BLOCK = 0xA7E0AA
BODY_PALETTES = 0xA7DC4A                  # 8 pointers ($A7) to 16 colours, one per health stage
HITBOX_ALL, HITBOX_CORE, HITBOX_NONE = 0xA7E02E, 0xA7E06C, 0xA7E020   # n, then 12-byte boxes

# block address -> vanilla structure [(row, col, n), ...]; checked against the ROM before writing
VANILLA = {
    BODY_BLOCK: [(r, 0, 10) for r in range(12)],
    **{a: [(r, 3, 4) for r in range(7, 11)] for a in (0xA7E1CE, 0xA7E202, 0xA7E236)},
    **{a: [(8, 4, 2), (9, 4, 2)] for a in range(0xA7E26A, 0xA7E31E, 0x14)},
    **{a: [(12, 2, 1), (13, 2, 1)] for a in (0xA7E31E, 0xA7E32E, 0xA7E33E)},
    **{a: [(12, 7, 1), (13, 7, 1)] for a in (0xA7E34E, 0xA7E35E, 0xA7E36E)},
    **{a: [(12, 3, 4), (13, 3, 4)] for a in (0xA7E37E, 0xA7E39A, 0xA7E3B6)},
}
assert set(queen_draw.LAYOUT) == set(VANILLA)


def block_size(entries) -> int:
    return 2 + sum(4 + 2 * n for _, _, n in entries) + 2


def read_block(rom: Rom, addr: int) -> list[tuple[int, int, list[int]]]:
    if rom.u16(addr) != 0xFFFE:
        raise ValueError(f"${addr:06X} não é bloco de tilemap")
    p, out = addr + 2, []
    while rom.u16(p) != 0xFFFF:
        dst, n = rom.u16(p), rom.u16(p + 2)
        off = dst - TILEMAP_RAM
        out.append((off // 64, (off % 64) // 2, [rom.u16(p + 4 + 2 * i) for i in range(n)]))
        p += 4 + 2 * n
    return out


def check_vanilla_shape(rom: Rom) -> None:
    for addr, entries in VANILLA.items():
        got = [(r, c, len(ws)) for r, c, ws in read_block(rom, addr)]
        if got != entries:
            raise RuntimeError(f"bloco ${addr:06X} da Parasite Queen mudou: {got}")


def tileset_entry(rom: Rom, index: int = TILESET) -> int:
    return 0x8F0000 | rom.u16(TILESET_TABLE + 2 * index)


def tileset_gfx(rom: Rom) -> bytes:
    return decompress(rom.data, snes_to_pc(rom.u24(tileset_entry(rom) + 3)))[0]


def cells(layout_entries) -> list[tuple[int, int]]:
    """(x, y) pixel origin of every tile a block writes."""
    return [((col + k) * 8, row * 8) for row, col, n in layout_entries for k in range(n)]


# --- reading the current shape back as images ---------------------------------------------------

def render_block(rom: Rom, addr: int, gfx: bytes, canvas: list[int] | None = None) -> list[int]:
    """Draw a block onto an 80x112 index canvas (0 = transparent)."""
    canvas = canvas if canvas is not None else [0] * (W * H)
    for row, col, words in read_block(rom, addr):
        for k, w in enumerate(words):
            t = w & 0x3FF
            px = [0] * 64 if t == BLANK & 0x3FF else decode_4bpp(gfx[t * 32:t * 32 + 32])
            px = flip_tile(px, bool(w & 0x4000), bool(w & 0x8000))
            x0, y0 = (col + k) * 8, row * 8
            for i in range(64):
                canvas[(y0 + i // 8) * W + x0 + i % 8] = px[i]
    return canvas


def frames_from_rom(rom: Rom) -> dict[int, list[int]]:
    """One canvas per block: the body with that block drawn over it."""
    gfx = tileset_gfx(rom)
    body = render_block(rom, BODY_BLOCK, gfx)
    return {a: body if a == BODY_BLOCK else render_block(rom, a, gfx, list(body)) for a in VANILLA}


def differing_pixels(a: dict[int, list[int]], b: dict[int, list[int]], layout) -> int:
    """Pixels that differ between two frame sets, counted only in the cells each block writes."""
    n = 0
    for addr, entries in layout.items():
        for x0, y0 in cells(entries):
            for i in range(64):
                p = (y0 + i // 8) * W + x0 + i % 8
                n += a[addr][p] != b[addr][p]
    return n


# --- writing a new shape -------------------------------------------------------------------------

def encode(frames: dict[int, list[int]], layout: dict[int, list[tuple[int, int, int]]]):
    """frames: block -> 80x112 canvas; layout: block -> [(row, col, n)] (same counts as vanilla).
    Returns (tile bytes, {block: payload bytes})."""
    dedup = TileDeduper(TILE_LIMIT)
    blocks = {}
    for addr, entries in layout.items():
        if [n for *_, n in entries] != [n for *_, n in VANILLA[addr]]:
            raise ValueError(f"bloco ${addr:06X}: tamanhos diferentes do vanilla")
        canvas = frames[addr]
        out = bytearray(b"\xFE\xFF")
        for row, col, n in entries:
            out += (TILEMAP_RAM + row * 64 + col * 2).to_bytes(2, "little") + n.to_bytes(2, "little")
            for k in range(n):
                x0, y0 = (col + k) * 8, row * 8
                px = [canvas[(y0 + i // 8) * W + x0 + i % 8] for i in range(64)]
                if not any(px):
                    w = BLANK
                else:
                    t, h, v = dedup.add(px)
                    w = (FIRST_TILE + t) | TILE_ATTRS | (0x4000 if h else 0) | (0x8000 if v else 0)
                out += w.to_bytes(2, "little")
        out += b"\xFF\xFF"
        assert len(out) == block_size(VANILLA[addr])
        blocks[addr] = bytes(out)
    tiles = b"".join(encode_4bpp(px) for px in dedup.tiles)
    return tiles, blocks


def bgr555(c: tuple[float, float, float]) -> int:
    r, g, b = (max(0, min(31, round(x * 31 / 255))) for x in c)
    return r | (g << 5) | (b << 10)


def stage_palettes(base: list[tuple[int, int, int]]) -> list[list[int]]:
    """8 health stages (index 0 = HP <= 312 ... 7 = full HP, $A7:DC0F): colours 8-15 (flesh and
    glow) move towards HOT as she weakens, up to 45% at stage 0. Colour 0 = 0."""
    out = []
    for s in range(8):
        t = (7 - s) / 7 * 0.45
        pal = [0]
        for i, c in enumerate(base[1:], 1):
            target = queen_draw.HOT if 8 <= i <= 15 else c
            pal.append(bgr555(tuple(c[k] + (target[k] - c[k]) * t for k in range(3))))
        out.append(pal)
    return out


def write_hitboxes(rom: Rom, addr: int, boxes) -> None:
    if rom.u16(addr) != len(boxes):
        raise RuntimeError(f"lista de caixas ${addr:06X} tem {rom.u16(addr)} caixas, não {len(boxes)}")
    for i, box in enumerate(boxes):
        for k, v in enumerate(box):        # left, top, right, bottom; the 2 handler words stay
            rom.w16(addr + 2 + 12 * i + 2 * k, v & 0xFFFF)


def metatiles_using_queen_tiles(rom: Rom) -> list[int]:
    table = decompress(rom.data, snes_to_pc(rom.u24(tileset_entry(rom))))[0]
    words = [table[i] | table[i + 1] << 8 for i in range(0, len(table) - 1, 2)]
    return sorted({0x100 + i // 4 for i, w in enumerate(words)
                   if FIRST_TILE <= w & 0x3FF < FIRST_TILE + TILE_LIMIT})


def apply(rom: Rom, put_in_bank) -> dict:
    """Write the new shape. `put_in_bank(payload) -> SNES address` must keep the data in one bank (the
    build's fixed allocator, specs/09c; DecompressToVRAM, used when a save is loaded, does cross banks,
    $80:B271 reads every source byte through $80:B266, but the fixed blobs never do)."""
    check_vanilla_shape(rom)
    used = metatiles_using_queen_tiles(rom)
    if used:
        raise RuntimeError(f"metatiles {[f'${m:03X}' for m in used]} do tileset {TILESET} usam os tiles da Queen")
    twin = tileset_entry(rom, TWIN_TILESET)
    if rom.u24(twin + 3) != VANILLA_GFX:
        raise RuntimeError(f"gráficos do tileset {TWIN_TILESET} não estão mais em ${VANILLA_GFX:06X}")
    frames = queen_draw.frames()
    tiles, blocks = encode(frames, queen_draw.LAYOUT)
    old = tileset_gfx(rom)
    gfx = bytearray(old)
    lo, hi = FIRST_TILE * 32, (FIRST_TILE + TILE_LIMIT) * 32
    gfx[lo:hi] = tiles + bytes(hi - lo - len(tiles))
    packed = compress(bytes(gfx))
    if decompress(packed)[0] != gfx:
        raise RuntimeError("compressor: ida e volta dos gráficos do tileset falhou")
    at = put_in_bank(packed)
    if (at & 0xFFFF) + len(packed) - 1 > 0xFFFF:
        raise RuntimeError(f"gráficos da Queen em ${at:06X} atravessam o banco")
    rom.w24(tileset_entry(rom) + 3, at)
    for addr, payload in blocks.items():
        rom.write(addr, payload)
    for s, pal in enumerate(stage_palettes(queen_draw.PALETTE)):
        a = 0xA70000 | rom.u16(BODY_PALETTES + 2 * s)
        for k, v in enumerate(pal):
            rom.w16(a + 2 * k, v)
    write_hitboxes(rom, HITBOX_ALL, queen_draw.HITBOX_ALL)
    write_hitboxes(rom, HITBOX_CORE, queen_draw.HITBOX_CORE)

    new = tileset_gfx(rom)
    if new[:lo] != old[:lo] or new[hi:] != old[hi:] or len(new) != len(old):
        raise RuntimeError("os gráficos novos do tileset mudaram tiles fora de $110-$18F")
    if rom.u24(twin + 3) != VANILLA_GFX:
        raise RuntimeError(f"tileset {TWIN_TILESET} foi repontado")
    wrong = differing_pixels(frames_from_rom(rom), frames, queen_draw.LAYOUT)
    if wrong:
        raise RuntimeError(f"Parasite Queen lida de volta da ROM difere do desenho em {wrong} pixels")
    body = {r: ws for r, _, ws in read_block(rom, BODY_BLOCK)}
    samples = {f"{0x7E0000 + TILEMAP_RAM + r * 64 + c * 2:06X}": body[r][c] for r, c in queen_draw.SAMPLE_CELLS}
    return {"tiles": len(tiles) // 32, "gfx": at, "gfx_bytes": len(packed), "tilemap_samples": samples}


def check(base: Rom, built: Rom | None) -> list[str]:
    """validate.py check_queen_art: (1) LZ round trip of the vanilla tileset graphics; (2) the
    vanilla Phantoon read as images, encoded again and read back is pixel-identical in the 22
    blocks with <= 128 tiles; (3) in the built ROM the shape read back equals queen_draw.frames()."""
    problems = []
    raw = tileset_gfx(base)
    if decompress(compress(raw))[0] != raw:
        problems.append("compressor: gráficos do tileset 4 não voltam iguais")
    vanilla = frames_from_rom(base)
    copy = Rom(bytes(base.data))
    try:
        tiles, blocks = encode(vanilla, VANILLA)
    except ValueError as e:
        return problems + [f"Phantoon ida e volta: {e}"]
    gfx = bytearray(raw)
    gfx[FIRST_TILE * 32:(FIRST_TILE + TILE_LIMIT) * 32] = tiles + bytes(TILE_LIMIT * 32 - len(tiles))
    copy.expand_to(0x400000)
    packed = compress(bytes(gfx))
    pc = len(copy.data) - 0x8000                       # last bank of the in-memory copy
    copy.data[pc:pc + len(packed)] = packed
    copy.w24(tileset_entry(copy) + 3, 0x800000 | (pc // 0x8000) << 16 | 0x8000)
    for addr, payload in blocks.items():
        copy.write(addr, payload)
    wrong = differing_pixels(frames_from_rom(copy), vanilla, VANILLA)
    if wrong:
        problems.append(f"Phantoon ida e volta: {wrong} pixels diferentes")
    if built is not None:
        try:
            wrong = differing_pixels(frames_from_rom(built), queen_draw.frames(), queen_draw.LAYOUT)
        except ValueError as e:
            return problems + [f"Parasite Queen na ROM: {e}"]
        if wrong:
            problems.append(f"Parasite Queen na ROM difere do desenho em {wrong} pixels")
    return problems

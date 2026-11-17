"""Title screen (specs/16): no attract demos, and the logo says "METROID / PRIME" instead of "SUPER / METROID".

Demos. After the title's logo is up, CinematicFunc_Func1 ($8B:9F29) counts the demo timer ($1F53, 900 frames) down:
DEC $1F53; BEQ +2; BPL +8; LDA #$9FAE; STA $1F51 (the next cinematic function = $8B:9FAE, which fades out and sets game
state $28, the attract demo); then the A/B/START check at $8B:9F38. The BEQ at $8B:9F2C becomes BRA $9F38 (2 bytes):
the timer runs out and nothing happens, the title stays (music looping) until a button is pressed. The only other store
of state $28 is at $82:862F, in the demo's own exit (state $2C: "next scene of this demo"), reached only from a demo.
`check_demos_off` proves it from the ROM's bytes (validate.check_orphans uses it: no demo, so no vanilla room loads).

Logo. LoadTitleSequenceGraphics ($8B:9B87) decompresses the title's sprite graphics from $95:80D8 (16 KB, both sprite
name tables, VRAM $6000); the logo is the spritemap $8C:879D (39 pieces, palette 2, priority 3: 37 16x16 + 2 8x8, the
"TM" among them), drawn by the cinematic sprite object's instruction list ($8B:A0C3). Its tiles are rows $00-$9F of the
graphic, which nothing else of the title shows (the boot logo, which also shows $95:80D8, loads it with its own pointer
at $8B:9293, untouched). Here:
  - the vanilla logo is drawn into an image (spritemap over the graphic); "SUPER" is its rows above y = -10 (relative to
    the object), "METROID" + "TM" the rows from -10 down; METROID (and TM) go up LIFT pixels, where SUPER was;
  - "PRIME" goes below it: 5 letters drawn here (PRIME_GLYPHS, masks), coloured like the METROID face (the same palette
    indices by row: white top and left edge, yellow -> orange gradient with the dither rows, a red base line) with a
    3-pixel dark extrusion below (indices 11/12 dithered, like METROID's);
  - the new image is cut into 16-pixel bands, each band into 16x16 cells at the x offset that needs the fewest; the cells'
    tiles go into rows $00-$9F of a copy of the graphic (cleared first; the rest of the graphic is vanilla), the copy
    goes to the fixed banks (`put`) and the title's pointer ($8B:9BC8/$8B:9BCD) points at it. It is compressed as the
    logo rows + the vanilla stream's tail (`pack`), so the title loads in as many frames as vanilla;
  - the spritemap is rewritten in place (at most its 39 pieces).
"""
from __future__ import annotations

import struct

from smlib.compression import compress, decompress
from smlib.rom import Rom, snes_to_pc

# --- demos ---------------------------------------------------------------------------------------------------------------
DEMO_TIMER_DEC = 0x8B9F29                 # CE 53 1F: DEC $1F53 (demo timer)
DEMO_BRANCH = 0x8B9F2C                    # vanilla F0 02 (BEQ to the LDA #$9FAE), here 80 0A (BRA $9F38)
DEMO_BRANCH_VANILLA = bytes.fromhex("f002")
DEMO_BRANCH_OFF = bytes.fromhex("800a")
DEMO_FUNC_STORE = 0x8B9F30                # A9 AE 9F 8D 51 1F: cinematic function = $9FAE (fade out to the demo)
DEMO_FUNC = 0x8B9FAE                      # CinematicFunc_Func9: ... LDA #$0028; STA $0998 at $8B:A000
BUTTON_CHECK = 0x8B9F38                   # A5 8F: LDA joypad 1 new keys (A/B/START leave the title)
GAME_STATE_DEMO_STORE = bytes.fromhex("a928008d9809")   # LDA #$0028; STA $0998
TITLE_DEMO_STATE_STORE = 0x8BA000
DEMO_STATE_STORES = {TITLE_DEMO_STATE_STORE: "a rotina $8B:9FAE (fim do título → demo)",
                     0x82862F: "a saída da demo ($82:85FB, estado $2C: próxima cena da mesma demo)"}

# --- logo ----------------------------------------------------------------------------------------------------------------
TITLE_GFX = 0x9580D8                      # the title's sprite graphics (both name tables), 0x4000 bytes
GFX_SIZE = 0x4000
GFX_BANK_SITE = 0x8B9BC8                  # A9 00 95: LDA #$9500; STA $48 (bank in $49) in LoadTitleSequenceGraphics
GFX_ADDR_SITE = 0x8B9BCD                  # A9 D8 80: LDA #$80D8; STA $47
LOGO_SPRITEMAP = 0x8C879D                 # count + pieces (x word, bit 15 = 16x16; y byte; attribute word)
LOGO_PIECES = 39
LOGO_ATTR = 0x3400                        # priority 3, palette 2, name table 0
LOGO_TILES = range(0x00, 0xA0)            # rows 0-9 of the graphic: the vanilla logo's, nothing else of the title's
LOGO_REF = 0x8BA0C7                       # instruction list: 20 00 9D 87 ... 01 00 9D 87 (the spritemap, twice)
SPLIT_Y = -10                             # SUPER above, METROID (and TM) from here down (rows of the vanilla image)
LIFT = 16                                 # METROID goes up this much (into SUPER's place)
PRIME_Y = 18                              # top row of PRIME's letters (relative to the object, after the lift)
PRIME_GAP = 8                             # pixels between letters
PRIME_GLYPHS = {
    "P": ["###########...",
          "############..",
          "####.....####.",
          "####.....####.",
          "####.....####.",
          "############..",
          "###########...",
          "####..........",
          "####..........",
          "####..........",
          "####..........",
          "####.........."],
    "R": ["###########...",
          "############..",
          "####.....####.",
          "####.....####.",
          "####.....####.",
          "############..",
          "###########...",
          "####...####...",
          "####....####..",
          "####.....####.",
          "####......####",
          "####......####"],
    "I": ["####"] * 12,
    "M": ["#####......#####",
          "######....######",
          "#######..#######",
          "################",
          "####.######.####",
          "####..####..####",
          "####...##...####",
          "####........####",
          "####........####",
          "####........####",
          "####........####",
          "####........####"],
    "E": ["#############",
          "#############",
          "####.........",
          "####.........",
          "####.........",
          "###########..",
          "###########..",
          "####.........",
          "####.........",
          "####.........",
          "#############",
          "#############"],
}
# palette-2 index of each letter row, like METROID's face: 1 white, 2 yellow ... 6 orange, 8 red; two digits = dithered
PRIME_ROWS = [1, 2, 2, 3, 34, 4, 4, 45, 5, 56, 6, 8]
EDGE, DEPTH, DEPTH_DITHER = 1, 12, 11     # left edge white; extrusion dark blue / purple (palette 2)
DEPTH_ROWS = 3
WORD = "PRIME"


def _tile(gfx: bytes, t: int) -> list[list[int]]:
    b = gfx[32 * t:32 * t + 32]
    return [[sum(((b[(p // 2) * 16 + 2 * y + (p & 1)] >> (7 - x)) & 1) << p for p in range(4)) for x in range(8)]
            for y in range(8)]


def _encode(px: list[list[int]]) -> bytes:
    out = bytearray(32)
    for y in range(8):
        for x in range(8):
            for p in range(4):
                if px[y][x] >> p & 1:
                    out[(p // 2) * 16 + 2 * y + (p & 1)] |= 0x80 >> x
    return bytes(out)


def spritemap(rom: Rom, addr: int = LOGO_SPRITEMAP) -> list[tuple[int, int, int, bool]]:
    """(x, y, attribute, 16x16) of each piece, in the spritemap's order."""
    out = []
    for k in range(rom.u16(addr)):
        x, y, attr = struct.unpack_from("<HbH", rom.data, snes_to_pc(addr) + 2 + 5 * k)
        out.append(((x & 0x1FF) - (0x200 if x & 0x100 else 0), y, attr, bool(x & 0x8000)))
    return out


def draw(gfx: bytes, pieces) -> dict[tuple[int, int], int]:
    """{(x, y): colour index} of the spritemap over the graphic (relative to the object; first piece on top)."""
    img: dict[tuple[int, int], int] = {}
    for x, y, attr, big in reversed(pieces):
        t = attr & 0x1FF
        for dx, dy, tt in [(0, 0, t)] + ([(8, 0, t + 1), (0, 8, t + 16), (8, 8, t + 17)] if big else []):
            for yy, row in enumerate(_tile(gfx, tt)):
                for xx, v in enumerate(row):
                    if v:
                        img[(x + dx + xx, y + dy + yy)] = v
    return img


def prime_word() -> dict[tuple[int, int], int]:
    """PRIME's pixels, centred on x = 0, top row PRIME_Y."""
    width = sum(len(PRIME_GLYPHS[c][0]) for c in WORD) + PRIME_GAP * (len(WORD) - 1)
    face, x = set(), -(width // 2)
    for c in WORD:
        for r, row in enumerate(PRIME_GLYPHS[c]):
            face |= {(x + i, PRIME_Y + r) for i, ch in enumerate(row) if ch == "#"}
        x += len(PRIME_GLYPHS[c][0]) + PRIME_GAP
    out = {}
    last = len(PRIME_ROWS) - 1
    for fx, fy in face:
        r = fy - PRIME_Y
        v = PRIME_ROWS[r]
        if v >= 10:
            v = v // 10 if (fx + fy) % 2 else v % 10
        if (fx - 1, fy) not in face and r != last:
            v = EDGE
        out[(fx, fy)] = v
    for fx, fy in sorted(face):
        for d in range(1, DEPTH_ROWS + 1):
            if (fx, fy + d) in face:
                break
            out.setdefault((fx, fy + d), DEPTH if d == 1 or (fx + fy + d) % 2 else DEPTH_DITHER)
    return out


def logo_image(base: Rom) -> dict[tuple[int, int], int]:
    """The new logo: the vanilla METROID (+ TM) LIFT pixels up, PRIME below (from the base ROM's bytes)."""
    gfx = decompress(base.data, snes_to_pc(TITLE_GFX))[0]
    old = draw(gfx, spritemap(base))
    img = {(x, y - LIFT): v for (x, y), v in old.items() if y >= SPLIT_Y}
    prime = prime_word()
    if min(y for _, y in prime) <= max(y for _, y in img):
        raise RuntimeError("PRIME encosta no METROID (PRIME_Y/LIFT)")
    img.update(prime)
    return img


def cells(img: dict[tuple[int, int], int]) -> list[tuple[int, int]]:
    """Top-left corners of the 16x16 cells covering the image: 16-pixel bands from its top row, each at the x offset
    (0-15) that needs the fewest cells (the smallest offset on a tie)."""
    out, ys = [], sorted({y for _, y in img})
    y0 = ys[0]
    while y0 <= ys[-1]:
        xs = {x for x, y in img if y0 <= y < y0 + 16}
        if xs:
            best = min(range(16), key=lambda o: (len({(x - o) // 16 for x in xs}), o))
            out += [(16 * c + best, y0) for c in sorted({(x - best) // 16 for x in xs})]
        y0 += 16
    return out


def new_logo(base: Rom) -> tuple[bytes, bytes]:
    """(the title's sprite graphics with the new logo, the new spritemap), from the base ROM."""
    gfx = bytearray(decompress(base.data, snes_to_pc(TITLE_GFX))[0])
    if len(gfx) != GFX_SIZE:
        raise RuntimeError(f"gráfico do título com {len(gfx):#x} bytes, esperado {GFX_SIZE:#x}")
    used = set()
    for x, y, attr, big in spritemap(base):
        t = attr & 0x1FF
        used |= {t, t + 1, t + 16, t + 17} if big else {t}
        if attr & ~0x1FF != LOGO_ATTR:
            raise RuntimeError(f"peça do logo com atributo ${attr:04X} (esperado ${LOGO_ATTR:04X} | tile)")
    if not used <= set(LOGO_TILES):
        raise RuntimeError("o logo vanilla usa tiles fora das linhas $00-$9F")
    img = logo_image(base)
    corners = cells(img)
    slots = [r * 16 + c for r in range(0, LOGO_TILES.stop // 16, 2) for c in range(0, 16, 2)]
    if len(corners) > min(LOGO_PIECES, len(slots)):
        raise RuntimeError(f"logo novo precisa de {len(corners)} peças 16x16 (cabem {min(LOGO_PIECES, len(slots))})")
    gfx[32 * LOGO_TILES.start:32 * LOGO_TILES.stop] = bytes(32 * len(LOGO_TILES))
    pieces = b""
    for (cx, cy), t in zip(corners, slots):
        for dx, dy, tt in ((0, 0, t), (8, 0, t + 1), (0, 8, t + 16), (8, 8, t + 17)):
            gfx[32 * tt:32 * tt + 32] = _encode([[img.get((cx + dx + x, cy + dy + y), 0) for x in range(8)]
                                                  for y in range(8)])
        pieces += struct.pack("<HbH", 0x8000 | (cx & 0x1FF), cy, LOGO_ATTR | t)
    return bytes(gfx), struct.pack("<H", len(corners)) + pieces


def _commands(data: bytes, start: int) -> list[tuple[int, int, int, int | None, int, int]]:
    """The compressed stream's commands: (output position, command, length, source position or None, stream position,
    stream size)."""
    out, pos, at = [], start, 0
    while (h := data[pos]) != 0xFF:
        head = pos
        pos += 1
        cmd, length = h >> 5, (h & 0x1F) + 1
        if cmd == 7:
            cmd, length = (h >> 2) & 7, ((h & 3) << 8 | data[pos]) + 1
            pos += 1
        src = (data[pos] | data[pos + 1] << 8) if cmd in (4, 5) else at - data[pos] if cmd in (6, 7) else None
        pos += {0: length, 1: 1, 2: 2, 3: 1}.get(cmd, 2 if cmd in (4, 5) else 1)
        out.append((at, cmd, length, src, head, pos - head))
        at += length
    return out


def pack(gfx: bytes, base: Rom) -> bytes:
    """The graphic compressed so that the title takes as long to load as vanilla: the logo rows (`compress`) and then the
    vanilla stream's own commands for the rest (those that start in the logo rows or copy from them become literal
    copies of the vanilla bytes). With the whole graphic recompressed the load took 4 frames more, and the frame counter
    and the random number at the new game changed ($05B6/$05E5; tests whose fights depend on them failed): with this
    they are the vanilla ones (test titulo_metroid_prime)."""
    cut = 32 * LOGO_TILES.stop
    vanilla_at = snes_to_pc(TITLE_GFX)
    vanilla = decompress(base.data, vanilla_at)[0]
    if gfx[cut:] != vanilla[cut:]:
        raise RuntimeError("gráfico do título mudou fora das linhas do logo")
    head = compress(gfx[:cut])
    out = bytearray(head[:-1])
    for at, cmd, length, src, pos, size in _commands(base.data, vanilla_at):
        if at + length <= cut:
            continue
        if at < cut or (src is not None and src < cut):
            for k in range(max(at, cut), at + length, 1024):
                chunk = vanilla[k:min(at + length, k + 1024)]
                out += _literal(chunk)
        else:
            out += base.data[pos:pos + size]
    return bytes(out) + b"\xFF"


def _literal(chunk: bytes) -> bytes:
    n = len(chunk) - 1
    return (bytes([n]) if n < 32 else bytes([0xE0 | n >> 8, n & 0xFF])) + chunk


def gfx_pointer(rom: Rom) -> int:
    return rom.u8(GFX_BANK_SITE + 2) << 16 | rom.u16(GFX_ADDR_SITE + 1)


def apply(rom: Rom, put) -> None:
    """Demos off and the new logo (`put(payload) -> SNES address`: the build's fixed allocator). `rom` has the vanilla
    bytes at every site (checked)."""
    if rom.read(DEMO_TIMER_DEC, 3) != bytes.fromhex("ce531f") or rom.read(DEMO_BRANCH, 2) != DEMO_BRANCH_VANILLA:
        raise RuntimeError(f"bytes inesperados em ${DEMO_TIMER_DEC:06X} (contagem das demos)")
    if rom.read(GFX_BANK_SITE, 3) != bytes.fromhex("a90095") or rom.read(GFX_ADDR_SITE, 3) != bytes.fromhex("a9d880"):
        raise RuntimeError(f"bytes inesperados em ${GFX_BANK_SITE:06X} (gráfico do título)")
    if rom.u16(LOGO_SPRITEMAP) != LOGO_PIECES or rom.read(LOGO_REF, 2) != struct.pack("<H", LOGO_SPRITEMAP & 0xFFFF):
        raise RuntimeError(f"bytes inesperados em ${LOGO_SPRITEMAP:06X} (spritemap do logo)")
    rom.write(DEMO_BRANCH, DEMO_BRANCH_OFF)
    gfx, pieces = new_logo(rom)
    packed = pack(gfx, rom)
    if decompress(packed)[0] != gfx:
        raise RuntimeError("compressão do gráfico do título não volta igual")
    at = put(packed)
    rom.write(GFX_BANK_SITE + 2, bytes([at >> 16]))
    rom.w16(GFX_ADDR_SITE + 1, at & 0xFFFF)
    rom.write(LOGO_SPRITEMAP, pieces)
    print(f"  título: sem demos (${DEMO_BRANCH:06X} = BRA); logo METROID PRIME, {rom.u16(LOGO_SPRITEMAP)} peças, "
          f"gráfico em ${at:06X} ({len(packed)} bytes)")


def _all(data: bytes, pattern: bytes) -> list[int]:
    out, i = [], data.find(pattern)
    while i >= 0:
        out.append(i)
        i = data.find(pattern, i + 1)
    return out


def check_demos_off(rom: Rom) -> list[str]:
    """specs/16, from the bytes: the title never starts an attract demo. The demo timer's BEQ is a BRA over the store of
    the fade-to-demo function ($8B:9FAE), which is the only reference to it in bank $8B, and the only code that sets game
    state $28 (LDA #$0028; STA $0998, anywhere in the ROM) is that function and the demo's own exit."""
    problems = []
    if rom.read(DEMO_TIMER_DEC, 3) != bytes.fromhex("ce531f"):
        problems.append(f"demos: ${DEMO_TIMER_DEC:06X} não é DEC $1F53 (contagem das demos)")
    branch = rom.read(DEMO_BRANCH, 2)
    if branch != DEMO_BRANCH_OFF:
        problems.append(f"demos: ${DEMO_BRANCH:06X} = {branch.hex(' ')}, esperado {DEMO_BRANCH_OFF.hex(' ')} "
                        f"(BRA ${BUTTON_CHECK & 0xFFFF:04X}): o título começaria a demo de atração")
    elif DEMO_BRANCH + 2 + branch[1] != BUTTON_CHECK or rom.read(BUTTON_CHECK, 2) != bytes.fromhex("a58f"):
        problems.append(f"demos: o BRA em ${DEMO_BRANCH:06X} não cai na leitura dos botões ${BUTTON_CHECK:06X}")
    if rom.read(DEMO_FUNC_STORE, 6) != bytes.fromhex("a9ae9f8d511f"):
        problems.append(f"demos: ${DEMO_FUNC_STORE:06X} não é LDA #$9FAE; STA $1F51")
    if not DEMO_BRANCH + 2 <= DEMO_FUNC_STORE < BUTTON_CHECK:
        problems.append("demos: o BRA não pula a troca para a rotina da demo")
    bank = bytes(rom.data[snes_to_pc(0x8B8000):snes_to_pc(0x8B8000) + 0x8000])
    refs = [0x8B8000 + i for i in _all(bank, struct.pack("<H", DEMO_FUNC & 0xFFFF))]
    if refs != [DEMO_FUNC_STORE + 1]:
        problems.append(f"demos: a rotina ${DEMO_FUNC:06X} é citada em {[f'${a:06X}' for a in refs]} "
                        f"(só ${DEMO_FUNC_STORE + 1:06X}, pulado, esperado)")
    stores = {0x800000 | (i // 0x8000) << 16 | 0x8000 + i % 0x8000 for i in _all(bytes(rom.data), GAME_STATE_DEMO_STORE)}
    if stores != set(DEMO_STATE_STORES):
        problems.append(f"demos: estado $28 gravado em {sorted(f'${a:06X}' for a in stores)}, esperado só em "
                        f"{sorted(f'${a:06X}' for a in DEMO_STATE_STORES)}")
    elif not DEMO_FUNC <= TITLE_DEMO_STATE_STORE < DEMO_FUNC + 0x60:
        problems.append("demos: o estado $28 do título não está na rotina $8B:9FAE")
    return problems


def check_logo(rom: Rom, base: Rom) -> list[str]:
    """specs/16, built ROM (the demos: check_demos_off, in validate.check_orphans): the title loads its own graphic (the
    vanilla one but rows $00-$9F), and the spritemap, drawn over it, is exactly logo_image (METROID + TM lifted, PRIME
    below, no SUPER), with pieces like the vanilla ones (16x16, palette 2, priority 3, tiles in rows $00-$9F)."""
    problems = []
    at = gfx_pointer(rom)
    if at == TITLE_GFX:
        return problems + ["título: o gráfico do logo ainda é o vanilla ($95:80D8, SUPER METROID)"]
    try:
        gfx = decompress(rom.data, snes_to_pc(at))[0]
    except (ValueError, IndexError) as e:
        return problems + [f"título: gráfico em ${at:06X} não descomprime ({e})"]
    vanilla = decompress(base.data, snes_to_pc(TITLE_GFX))[0]
    if len(gfx) != len(vanilla):
        problems.append(f"título: gráfico com {len(gfx):#x} bytes (o vanilla tem {len(vanilla):#x})")
    lo, hi = 32 * LOGO_TILES.start, 32 * LOGO_TILES.stop
    if gfx[:lo] != vanilla[:lo] or gfx[hi:] != vanilla[hi:]:
        problems.append("título: o gráfico mudou fora das linhas $00-$9F do logo")
    if rom.read(LOGO_REF, 2) != struct.pack("<H", LOGO_SPRITEMAP & 0xFFFF):
        problems.append(f"título: a lista de instruções ${LOGO_REF:06X} não aponta para o spritemap ${LOGO_SPRITEMAP:06X}")
    pieces = spritemap(rom)
    if not 0 < len(pieces) <= LOGO_PIECES:
        return problems + [f"título: spritemap do logo com {len(pieces)} peças (1 a {LOGO_PIECES})"]
    for x, y, attr, big in pieces:
        if not big or attr & ~0x1FF != LOGO_ATTR or (attr & 0x1FF) + 17 >= LOGO_TILES.stop:
            problems.append(f"título: peça ({x}, {y}) atributo ${attr:04X} (esperado 16x16, ${LOGO_ATTR:04X} | tile < $A0)")
    if draw(gfx, pieces) != logo_image(base):
        problems.append("título: o logo desenhado não é METROID + PRIME (logo_image)")
    return problems

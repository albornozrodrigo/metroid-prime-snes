"""Render the Parasite Queen as the built ROM has her to research/render/parasite_queen.png.

Reads the tilemap blocks and tiles back from build/metroid_prime_snes.sfc, so it shows what the
game draws: the body block, then the tail and claw blocks in their first pose, then the block(s)
of each picture. Top row, full health: body (mouth closed), mouth half open, mouth open, core
looking right/up-left/down, claws and tail in poses 2 and 3. Bottom row: the same at the lowest
health stage. Scale 3x, on black like the Reactor Core.

Usage: python3 -I tools/preview_queen.py   (after tools/build.py)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from frigate import queen_art  # noqa: E402
from smlib.gfx import write_png  # noqa: E402
from smlib.rom import Rom  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCALE, GAP = 3, 6
BASE = [0xA7E0AA, 0xA7E37E, 0xA7E31E, 0xA7E34E]          # body, tail and both claws in pose 1
SHOWN = [(), (0xA7E202,), (0xA7E1CE,), (0xA7E1CE, 0xA7E2BA), (0xA7E1CE, 0xA7E2F6), (0xA7E1CE, 0xA7E292),
         (0xA7E32E, 0xA7E35E), (0xA7E39A,), (0xA7E33E, 0xA7E36E), (0xA7E3B6,)]


def stage_rgb(rom: Rom, stage: int) -> list[tuple[int, int, int]]:
    a = 0xA70000 | rom.u16(queen_art.BODY_PALETTES + 2 * stage)
    out = []
    for k in range(16):
        v = rom.u16(a + 2 * k)
        out.append(tuple(((v >> s) & 31) * 255 // 31 for s in (0, 5, 10)))
    return out


def main() -> None:
    rom = Rom.load(ROOT / "build/metroid_prime_snes.sfc")
    gfx = queen_art.tileset_gfx(rom)
    base = [0] * (queen_art.W * queen_art.H)
    for addr in BASE:
        queen_art.render_block(rom, addr, gfx, base)
    frames = []
    for blocks in SHOWN:
        canvas = list(base)
        for addr in blocks:
            queen_art.render_block(rom, addr, gfx, canvas)
        frames.append(canvas)
    w, h = queen_art.W * SCALE, queen_art.H * SCALE
    cw, ch = len(SHOWN) * (w + GAP) + GAP, 2 * (h + GAP) + GAP
    rgb = bytearray(b"\x20\x20\x28" * (cw * ch))
    for row, stage in enumerate((7, 0)):
        pal = stage_rgb(rom, stage)
        for n, canvas in enumerate(frames):
            x0, y0 = GAP + n * (w + GAP), GAP + row * (h + GAP)
            for y in range(h):
                for x in range(w):
                    i = canvas[(y // SCALE) * queen_art.W + x // SCALE]
                    o = ((y0 + y) * cw + x0 + x) * 3
                    rgb[o:o + 3] = bytes(pal[i]) if i else b"\x00\x00\x00"
    out = ROOT / "research/render/parasite_queen.png"
    write_png(out, cw, ch, bytes(rgb))
    print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()

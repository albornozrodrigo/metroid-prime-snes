"""Beam doors (specs/09a-portas-de-feixe.md, epic 09 decision 2): door caps that open only with a
shot of one beam, for the Tallon's ice, wave and plasma doors.

A shot reaching a coloured door's block (type C, BTS $44) puts `projectile_type & $1FFF | $8000` in
the door PLM's timer (PlmSetup_Door_Strange, sm_84.c:2129); a beam shot's low bits are the equipped
beams (Wave $1, Ice $2, Plasma $8), a missile/bomb has a high nibble ($100, $500...). The pre-instruction
is a copy of $84:BD88 (go to the link instruction if shot with a super missile: AND #$0F00 / CMP
#$0200) with AND #($0F00|m) / CMP #m: only a beam shot that has beam m opens it; any other shot plays
the "dud" sound.

Per beam and wall side (R, L): a 50-byte block = the 23 closing frames of the vanilla door of the
beam's colour (copied: the vanilla closing list falls through into the vanilla main list, which would
turn the door back into the vanilla one when Samus enters through it, CheckIfColoredDoorCapSpawned
sm_82.c:4270) + the main list (GotoIfDoorBitSet, SetLinkReg, SetPreInstr, closed frame, Sleep; link:
IncrementDoorHitCounterAndJGE 1 -> the vanilla opening). Header = setup $C7B1 (coloured door: writes
block C/$44), main list, closing list. The room argument is $8000 (build.BEAM_DOOR_ARG): no door bit,
the door is closed again on every visit.

The layout is fixed from $84:F10F, so PLM ids are known without building (validate, tests).

specs/10d: the wave door is purple (Prime's), not grey (low contrast on the sunken frigate's walls). It is the green door's
shape (cap tiles $300..., colours 1-3 of the metatile's palette line) drawn with 8 metatiles of its own in tileset 4, where
the 7 wave doors are: SCE metatiles $3F0-$3F7 (vanilla filler `$03FF x4`, used by no room of tileset 4/5), copies of the
green cap's CRE metatiles $004-$007/$024-$027 with palette line 6 (no tileset-4 metatile uses it) instead of 1; line 6
gets purple in colours 1-3 and the door frame's colours (4-7, 12, 15) copied from line 1. Its drawing frames (closed + 3
opening frames, 12 bytes each) and opening list are copies of the green door's with those metatiles, after the headers
(the PLM ids don't move); its closing frames point at them.

specs/12f: the Chozo Ruins' Tower of Light doors are wave doors too, in tileset $0C (smlib/ruins.py). The PLM frames are
global, so tileset $0C's own copy of its metatile table (the build's, after its palette blob) gets the same 8 metatiles
$3F0-$3F7 (vanilla $0C has metatiles there, but no room the game loads in $0C draws them: only the Chozo's, whose levels
the validator checks, check_wave_paint_free) drawn with palette line RUINS_PAINT_LINE = 5 (no piece of the ruins style uses
it: they are all line 7; the ruins' background, $8F:E25A, is line 6), which gets the same purple and frame colours.
"""
from __future__ import annotations

from .rooms import CHARGE, ICE, PLASMA, WAVE

START, END = 0x84F10F, 0x84FFFF            # free in the built ROM (epic 09, "Espaço")
SUPER_PRE, PRE_LEN = 0x84BD88, 42          # PlmPreInstr_GoToLinkInstrIfShotWithSuperMissile
SETUP_COLORED = 0xC7B1                     # PlmSetup_Door_Colored
CLOSE_LEN = 23                             # closing frames before the main list
MAIN_LEN = 27
# vanilla door headers of each colour by wall side (research/sm_room_format.md section 5)
VANILLA = {"green": {"R": 0xC872, "L": 0xC878}, "yellow": {"R": 0xC85A, "L": 0xC860},
           "grey": {"R": 0xC842, "L": 0xC848}}
# beam -> (colour of the vanilla door it copies, beam bit in the shot's projectile type)
BEAMS = {ICE: ("green", 0x0002), WAVE: ("green", 0x0001), PLASMA: ("yellow", 0x0008)}
SIDES = ("R", "L")
COLOUR_NAME = {"green": "verde", "yellow": "laranja", "grey": "cinza"}

# specs/10d: the purple wave door
PAINTED = WAVE                 # the beam whose door is repainted
PAINT_TILESET = 4              # the wave doors' rooms (region D)
PAINT_LINE = 6                 # BG palette line, unused by tileset 4's metatiles
FRAME_LINE = 1                 # the door frame colours come from the green cap's line
FRAME_COLOURS = (4, 5, 6, 7, 12, 15)
PURPLE = (0x7DB5, 0x64CE, 0x3847)   # colours 1-3, light to dark: RGB (168,104,248), (112,48,200), (56,16,112)
RUINS_PAINT_LINE = 5           # specs/12f: tileset $0C's line for the purple door (the ruins use 7, their background 6)
CRE_TILE_TABLE = 0xB9A09D      # common room elements' metatile table (metatiles $000-$0FF)
# green cap metatile (CRE) -> its purple copy (SCE of tileset 4)
PAINT_METATILES = {0x004: 0x3F0, 0x024: 0x3F1, 0x005: 0x3F2, 0x025: 0x3F3,
                   0x006: 0x3F4, 0x026: 0x3F5, 0x007: 0x3F6, 0x027: 0x3F7}
FILLER = bytes.fromhex("ff03ff03ff03ff03")   # what $3F0-$3F7 hold in the vanilla table
FRAME_LEN, OPEN_LEN = 12, 21   # a drawing frame (one 4-block column); the opening list (sound, 4 frames, delete)

PRE = {beam: START + PRE_LEN * n for n, beam in enumerate(BEAMS)}
_BLOCKS = START + PRE_LEN * len(BEAMS)
BLOCK = {(beam, side): _BLOCKS + (CLOSE_LEN + MAIN_LEN) * (2 * n + k)
         for n, beam in enumerate(BEAMS) for k, side in enumerate(SIDES)}
_HEADERS = _BLOCKS + (CLOSE_LEN + MAIN_LEN) * len(BLOCK)
PLM = {key: (_HEADERS + 6 * n) & 0xFFFF for n, key in enumerate(BLOCK)}   # PLM id of each beam door
_PAINT = _HEADERS + 6 * len(PLM)
# per wall side: the 4 painted frames (closed first, then the 3 opening frames as the green door's lists use them), then
# the painted opening list
PAINT_FRAMES = {side: _PAINT + (4 * FRAME_LEN + OPEN_LEN) * k for k, side in enumerate(SIDES)}
PAINT_OPEN = {side: PAINT_FRAMES[side] + 4 * FRAME_LEN for side in SIDES}
SIZE = _PAINT + (4 * FRAME_LEN + OPEN_LEN) * len(SIDES) - START

# specs/12g (epic 12, decision 2): the charge door, appended after the wave door's paint (the ids above do not move). A
# charged shot's projectile type is `equipped_beams & $100F | $8010` (sm_90.c:3490, the SBA shots too, 4312-4396), an
# uncharged one's has no $10; the door's timer gets `type & $1FFF | $8000` (PlmSetup_Door_Strange, sm_84.c:2129), so the
# pre-instruction copy with AND #$0F10 / CMP #$0010 opens it to a charged beam shot of any beams, never to an uncharged
# shot, a missile ($0100), a bomb or a power bomb. Its look is a copy of the vanilla yellow door's (the plasma door's
# colour: CHARGE_COLOUR, one constant, a decision for the user, specs/12g).
# specs/12g2 (user decision, 12g question 2): the charge door gets a colour of its own, painted as the wave door's (10d,
# 12f): the green door's shape (CHARGE_COLOUR) with 8 metatiles of its own, CHARGE_METATILES $3E8-$3EF, drawn with palette
# line CHARGE_LINE = 4 of tileset $0C (no level metatile of the Chozo's rooms, no CRE metatile and no item graphics use
# line 4 there: scanned, specs/12g2), which gets WHITE in colours 1-3 (chosen side by side with the blue, missile, ice,
# plasma, grey and wave caps on the sandstone, specs/img/12g2-cores-das-portas.png) and the green line's frame colours.
# Only tileset $0C has it: tileset 4 has no free line (0-5 its rooms and the CRE, 6 the wave door, 7 the Parasite Queen),
# and the charge lock is the Chozo's only (validate.check_charge_doors). Its frames and opening list follow its headers
# (the PLM ids $F3F5/$F3FB do not move).
CHARGE_COLOUR, CHARGE_MASK = "green", 0x0010
CHARGE_NAME = "branca"
CHARGE_LINE = 4
WHITE = (0x7FFF, 0x6AF5, 0x3D6A)   # colours 1-3, light to dark: RGB (248,248,248), (168,184,208), (80,88,120)
CHARGE_METATILES = {0x004: 0x3E8, 0x024: 0x3E9, 0x005: 0x3EA, 0x025: 0x3EB,
                    0x006: 0x3EC, 0x026: 0x3ED, 0x007: 0x3EE, 0x027: 0x3EF}
DOORS = {**BEAMS, CHARGE: (CHARGE_COLOUR, CHARGE_MASK)}   # every beam-door kind: colour copied, mask
_CHARGE = START + SIZE
PRE[CHARGE] = _CHARGE
BLOCK.update({(CHARGE, side): _CHARGE + PRE_LEN + (CLOSE_LEN + MAIN_LEN) * k for k, side in enumerate(SIDES)})
_CHARGE_HEADERS = _CHARGE + PRE_LEN + (CLOSE_LEN + MAIN_LEN) * len(SIDES)
PLM.update({(CHARGE, side): (_CHARGE_HEADERS + 6 * k) & 0xFFFF for k, side in enumerate(SIDES)})
_CHARGE_PAINT = _CHARGE_HEADERS + 6 * len(SIDES)
CHARGE_FRAMES = {side: _CHARGE_PAINT + (4 * FRAME_LEN + OPEN_LEN) * k for k, side in enumerate(SIDES)}
CHARGE_OPEN = {side: CHARGE_FRAMES[side] + 4 * FRAME_LEN for side in SIDES}
SIZE = _CHARGE_PAINT + (4 * FRAME_LEN + OPEN_LEN) * len(SIDES) - START
# the painted doors: beam -> (its metatiles, where its frames go by side, where its opening list goes by side)
PAINTS = {PAINTED: (PAINT_METATILES, PAINT_FRAMES, PAINT_OPEN), CHARGE: (CHARGE_METATILES, CHARGE_FRAMES, CHARGE_OPEN)}
COLOUR_NAME["white"] = CHARGE_NAME

# specs/12l: the Chozo's region E has ice doors on floor and ceiling walls (Prime's data: the Furnace <-> East Furnace
# Access and the Hall of the Elders <-> Crossway Access South doors are Ice-only on both sides, s12l/dtrig.out). Ice door
# blocks for walls B (on the floor, facing up) and T (in the ceiling), copies of the vanilla green door's ($C87E/$C884: same
# list shape as the side ones, read from the bytes by vanilla_parts), appended after the charge door (no id above moves).
# Green is the ice door's colour already (no paint).
VERTICAL = ("B", "T")
VANILLA["green"].update({"B": 0xC87E, "T": 0xC884})
_VERT = START + SIZE              # the vertical ice doors share the ice pre-instruction (PRE[ICE])
BLOCK.update({(ICE, side): _VERT + (CLOSE_LEN + MAIN_LEN) * k for k, side in enumerate(VERTICAL)})
_VERT_HEADERS = _VERT + (CLOSE_LEN + MAIN_LEN) * len(VERTICAL)
PLM.update({(ICE, side): (_VERT_HEADERS + 6 * k) & 0xFFFF for k, side in enumerate(VERTICAL)})
SIZE = _VERT_HEADERS + 6 * len(VERTICAL) - START

# specs/18i: Phendrana's labs have wave doors on floor and ceiling walls (Prime's data: the Research Entrance's ceiling door to
# the Hydra Lab Entryway and the entryway's floor door are Wave-only on both sides). Purple wave door blocks for walls B and T,
# copies of the vanilla green door's ($C87E/$C884) with the wave pre-instruction (PRE[WAVE]) and drawn purple as the side
# ones (specs/10d): the vertical green cap's 8 CRE metatiles ($014-$017/$034-$037, read from its frames) painted into
# VERT_PAINT_METATILES of tileset 4's own table (vanilla filler there; the labs' look shares that table: smlib/ice.py LAB), on
# its paint line. Not after the vertical ice doors (the arena routine, chozo/bosses.py ROUTINE, starts 5 bytes after them):
# a block of their own at VERT_WAVE_START, near the end of $84's free range (the arena table grows from $84:F500 up to it).
VERT_PAINT_METATILES = {0x014: 0x3F8, 0x034: 0x3F9, 0x015: 0x3FA, 0x035: 0x3FB,
                        0x016: 0x3FC, 0x036: 0x3FD, 0x017: 0x3FE, 0x037: 0x3EF}
VERT_PAINT_TILESETS = (PAINT_TILESET,)   # the tables painted with them (tileset 4's: the frigate's and the labs', $1B)
VERT_WAVE_START = 0x84FE00
VERT_WAVE_END = 0x84FFBA                  # $84's free range ends there (epic 14, "Espaço")
BLOCK.update({(WAVE, side): VERT_WAVE_START + (CLOSE_LEN + MAIN_LEN) * k for k, side in enumerate(VERTICAL)})
_VW_HEADERS = VERT_WAVE_START + (CLOSE_LEN + MAIN_LEN) * len(VERTICAL)
PLM.update({(WAVE, side): (_VW_HEADERS + 6 * k) & 0xFFFF for k, side in enumerate(VERTICAL)})
_VW_PAINT = _VW_HEADERS + 6 * len(VERTICAL)
PAINT_FRAMES.update({side: _VW_PAINT + (4 * FRAME_LEN + OPEN_LEN) * k for k, side in enumerate(VERTICAL)})
PAINT_OPEN.update({side: PAINT_FRAMES[side] + 4 * FRAME_LEN for side in VERTICAL})
VERT_WAVE_SIZE = _VW_PAINT + (4 * FRAME_LEN + OPEN_LEN) * len(VERTICAL) - VERT_WAVE_START

# specs/19l: the Mines' region D has plasma doors on floor and ceiling walls (Prime's data: the Elite Quarters Access <-> Metroid
# Quarantine B, Metroid Quarantine B <-> Save Station C and Fungal Hall B <-> Phazon Mining Tunnel docks are Plasma-only on both
# sides). Plasma door blocks for walls B and T, copies of the vanilla yellow door's ($C866/$C86C: the same list shape as the green
# ones, read from the bytes by vanilla_parts) with the plasma pre-instruction (PRE[PLASMA]); yellow is the plasma door's colour
# already (no paint). Right after the vertical wave doors, in $84's free range before VERT_WAVE_END (only $FF there in the build).
VANILLA["yellow"].update({"B": 0xC866, "T": 0xC86C})
VERT_PLASMA_START = VERT_WAVE_START + VERT_WAVE_SIZE
BLOCK.update({(PLASMA, side): VERT_PLASMA_START + (CLOSE_LEN + MAIN_LEN) * k for k, side in enumerate(VERTICAL)})
_VP_HEADERS = VERT_PLASMA_START + (CLOSE_LEN + MAIN_LEN) * len(VERTICAL)
PLM.update({(PLASMA, side): (_VP_HEADERS + 6 * k) & 0xFFFF for k, side in enumerate(VERTICAL)})
VERT_PLASMA_SIZE = _VP_HEADERS + 6 * len(VERTICAL) - VERT_PLASMA_START


def _w(v: int) -> bytes:
    return bytes([v & 0xFF, (v >> 8) & 0xFF])


OPEN_FRAMES = (0xA677, 0xA683, 0xA68F, 0xA69B)   # the open-door frames by wall (R, L; specs/18i: B, T), every door's


def vanilla_parts(rom, colour: str, side: str) -> tuple[bytes, int, int]:
    """(23 closing-frame bytes, GotoIfDoorBitSet target, opening list) of a vanilla coloured door,
    read from the ROM and checked against the shape this module copies."""
    h = 0x840000 | VANILLA[colour][side]
    main, close = rom.u16(h + 2), rom.u16(h + 4)
    tag = f"porta {colour} {side} (${h & 0xFFFF:04X})"
    if close + CLOSE_LEN != main:
        raise RuntimeError(f"{tag}: a lista de fechar ${close:04X} não cai na principal ${main:04X}")
    frames = rom.read(0x840000 | close, CLOSE_LEN)
    lst = rom.read(0x840000 | main, 0x40)
    if lst[0:2] != b"\x72\x8A" or frames[-4:-2] != b"\x01\x00":
        raise RuntimeError(f"{tag}: lista inesperada {lst[:4].hex()} / fechar {frames.hex()}")
    closed = int.from_bytes(frames[-2:], "little")
    if _w(closed) not in lst[:0x10]:
        raise RuntimeError(f"{tag}: quadro fechado ${closed:04X} não está na lista principal")
    at = lst.find(b"\x91\x8A\x01")
    if at < 0:
        raise RuntimeError(f"{tag}: sem IncrementDoorHitCounterAndJGE 1")
    opening = int.from_bytes(lst[at + 3:at + 5], "little")
    if rom.read(0x840000 | opening, 3) != b"\x19\x8C\x07":
        raise RuntimeError(f"{tag}: abertura ${opening:04X} não começa com o som da porta")
    return frames, int.from_bytes(lst[2:4], "little"), opening


def pre_instruction(rom, mask: int) -> bytes:
    """$84:BD88 with AND #($0F00|mask) / CMP #mask."""
    r = bytearray(rom.read(SUPER_PRE, PRE_LEN))
    if r[5:8] != b"\x29\x00\x0F" or r[8:11] != b"\xC9\x00\x02" or r[-1] != 0x60:
        raise RuntimeError(f"bytes inesperados em ${SUPER_PRE:06X}: {r.hex()}")
    r[5:8] = bytes([0x29, mask, 0x0F])
    r[8:11] = bytes([0xC9, mask, 0x00])
    return bytes(r)


def _list_frames(lst: bytes, stop: bytes = b"") -> list[int]:
    """Offsets of the drawing-frame pointers in a PLM instruction list made of (timer, frame) pairs and the door sound
    ($8C19 + 1 byte), up to `stop` (an instruction word) or the end."""
    at, out = 0, []
    while at < len(lst):
        word = int.from_bytes(lst[at:at + 2], "little")
        if stop and lst[at:at + 2] == stop:
            break
        if word == 0x8C19:
            at += 3
        elif word < 0x8000:
            out.append(at + 2)
            at += 4
        else:
            raise RuntimeError(f"instrução inesperada ${word:04X} numa lista de porta")
    return out


def paint_frame(rom, frame: int, metatiles: dict[int, int] = PAINT_METATILES) -> bytes:
    """A green door drawing frame ($84) with its metatiles swapped for the painted ones (purple; specs/12g2: white)."""
    data = bytearray(rom.read(0x840000 | frame, FRAME_LEN))
    if data[:2] not in (b"\x04\x80", b"\x04\x00") or data[-2:] != b"\x00\x00":   # a column of 4; specs/18i: a row of 4
        raise RuntimeError(f"quadro de porta ${frame:04X} inesperado: {data.hex()}")
    for k in range(4):
        w = int.from_bytes(data[2 + 2 * k:4 + 2 * k], "little")
        if (w & 0x3FF) not in metatiles:
            raise RuntimeError(f"quadro ${frame:04X}: metatile ${w & 0x3FF:03X} fora da porta verde")
        data[2 + 2 * k:4 + 2 * k] = _w((w & 0xFC00) | metatiles[w & 0x3FF])
    return bytes(data)


def painted(rom, side: str, frames: bytes, opening: int, beam: str = PAINTED) -> tuple[bytes, bytes, dict[int, int]]:
    """A painted door's (the wave door's; specs/12g2: the charge door's) (closing frames, frames + opening list block,
    green frame -> painted frame) for a wall side, from the green door's closing frames and opening list."""
    metatiles, frames_at, _ = PAINTS[beam]
    if side in VERTICAL:   # specs/18i: the vertical wave door's own metatiles
        metatiles = VERT_PAINT_METATILES
    green = [int.from_bytes(frames[o:o + 2], "little") for o in _list_frames(frames)]
    own = [f for f in dict.fromkeys(green) if f not in OPEN_FRAMES]   # the open-door frames are every door's
    closed = int.from_bytes(frames[-2:], "little")
    order = [closed] + [f for f in own if f != closed]
    if len(order) != 4:
        raise RuntimeError(f"porta verde {side}: quadros {[hex(f) for f in order]}, esperado 4")
    swap = {f: (frames_at[side] + FRAME_LEN * k) & 0xFFFF for k, f in enumerate(order)}
    close = bytearray(frames)
    for o in _list_frames(frames):
        f = int.from_bytes(close[o:o + 2], "little")
        close[o:o + 2] = _w(swap.get(f, f))
    lst = bytearray(rom.read(0x840000 | opening, OPEN_LEN))
    if lst[:3] != b"\x19\x8C\x07" or lst[-2:] != b"\xBC\x86":
        raise RuntimeError(f"abertura verde ${opening:04X} inesperada: {lst.hex()}")
    for o in _list_frames(lst[:-2]):
        f = int.from_bytes(lst[o:o + 2], "little")
        lst[o:o + 2] = _w(swap.get(f, f))
    return bytes(close), b"".join(paint_frame(rom, f, metatiles) for f in order) + bytes(lst), swap


def code(rom) -> list[tuple[int, bytes]]:
    """(address, bytes) of everything this module puts in $84, generated from the vanilla bytes of `rom`."""
    out = [(PRE[beam], pre_instruction(rom, mask)) for beam, (_, mask) in DOORS.items()]
    for (beam, side), at in BLOCK.items():
        frames, bit_set, opening = vanilla_parts(rom, DOORS[beam][0], side)
        if beam in PAINTS:
            _, frames_at, open_at = PAINTS[beam]
            frames, block, _ = painted(rom, side, frames, opening, beam)
            out.append((frames_at[side], block))
            opening = open_at[side] & 0xFFFF
        closed = int.from_bytes(frames[-2:], "little")
        main = (at + CLOSE_LEN) & 0xFFFF
        sleep, link = main + 16, main + 22
        lst = (b"\x72\x8A" + _w(bit_set) + b"\x24\x8A" + _w(link) + b"\xC1\x86" + _w(PRE[beam])
               + b"\x01\x00" + _w(closed) + b"\xB4\x86" + b"\x24\x87" + _w(sleep)
               + b"\x91\x8A\x01" + _w(opening))
        assert len(lst) == MAIN_LEN and main + len(lst) - 2 == link + 3
        out.append((at, frames + lst))
        out.append((0x840000 | PLM[(beam, side)], _w(SETUP_COLORED) + _w(main) + _w(at)))
    return out


def apply(rom) -> int:
    """Write the beam doors into $84 (free space checked); returns the bytes used."""
    for addr, data in code(rom):
        if rom.read(addr, len(data)) != b"\xFF" * len(data):
            raise RuntimeError(f"espaço em ${addr:06X} não está livre (portas de feixe)")
        rom.write(addr, data)
    if (START + SIZE - 1 > END or VERT_WAVE_START + VERT_WAVE_SIZE > VERT_WAVE_END
            or VERT_PLASMA_START + VERT_PLASMA_SIZE > VERT_WAVE_END):   # specs/19l
        raise RuntimeError("portas de feixe não cabem no $84")
    return SIZE + VERT_WAVE_SIZE + VERT_PLASMA_SIZE


def paint_table(rom, table: bytes, line: int = PAINT_LINE, filler: bool = True,
                metatiles: dict[int, int] = PAINT_METATILES) -> bytes:
    """Tileset 4's metatile table (SCE, decompressed: metatile m at (m - $100) * 8) with the purple metatiles: the green
    cap's CRE metatiles (read from `rom`) with palette line `line` where they use FRAME_LINE. `filler`: the 8 metatiles must
    be the vanilla filler (tileset 4); specs/12f: tileset $0C's are real metatiles no room of ours draws (False). specs/12g2:
    `metatiles` = CHARGE_METATILES for the white charge door."""
    from smlib.compression import decompress
    from smlib.rom import snes_to_pc
    cre, _ = decompress(rom.data, snes_to_pc(CRE_TILE_TABLE))
    out = bytearray(table)
    for src, dst in metatiles.items():
        at = (dst - 0x100) * 8
        if filler and bytes(out[at:at + 8]) != FILLER:
            raise RuntimeError(f"metatile ${dst:03X} do tileset {PAINT_TILESET} não está livre: {bytes(out[at:at + 8]).hex()}")
        words = [int.from_bytes(cre[src * 8 + 2 * k:src * 8 + 2 * k + 2], "little") for k in range(4)]
        if not any((w >> 10) & 7 == FRAME_LINE for w in words):
            raise RuntimeError(f"metatile ${src:03X} da porta verde sem tile na linha {FRAME_LINE}: {[hex(w) for w in words]}")
        # only the tiles drawn with the green line change line (the opening frame's $338 stays on line 0, as vanilla)
        out[at:at + 8] = b"".join(_w((w & ~0x1C00) | (line << 10) if (w >> 10) & 7 == FRAME_LINE else w)
                                  for w in words)
    return bytes(out)


def paint_vertical(rom, table: bytes, line: int = PAINT_LINE) -> bytes:
    """specs/18i: `table` (tileset 4's, already with the side doors' paint) with the vertical purple wave door's 8 metatiles
    VERT_PAINT_METATILES (vanilla filler there) on line `line`."""
    return paint_table(rom, table, line, metatiles=VERT_PAINT_METATILES)


def paint_palette(palette: bytes, line: int = PAINT_LINE, colours: tuple[int, int, int] = PURPLE) -> bytes:
    """Tileset 4's palette (decompressed, BGR555 words; after the frigate recolour) with line `line` purple: colours
    1-3 PURPLE, the door frame's colours copied from line FRAME_LINE (specs/12f: tileset $0C's, line RUINS_PAINT_LINE;
    specs/12g2: line CHARGE_LINE with `colours` = WHITE)."""
    out = bytearray(palette)
    for i, c in enumerate(colours, 1):
        out[2 * (line * 16 + i):2 * (line * 16 + i) + 2] = _w(c)
    for i in FRAME_COLOURS:
        src = 2 * (FRAME_LINE * 16 + i)
        out[2 * (line * 16 + i):2 * (line * 16 + i) + 2] = palette[src:src + 2]
    return bytes(out)

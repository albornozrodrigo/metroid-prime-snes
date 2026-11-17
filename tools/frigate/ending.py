"""End of the frigate: Meta Ridley flies off, Samus boards her gunship and flies to Tallon IV.

Prime: during the escape Meta Ridley rises past the docking hangar and flies off to Tallon IV;
Samus runs to her gunship and follows him. Here:

  - Air Lock, escape only (area boss bit 1 set, bit 2 clear): Meta Ridley appears, roars and flies
    out through the ceiling. He is Ceres Ridley ($A0:E13F) with his own init/main in $A6 that
    reuse Ceres Ridley's code: the fade-in from the dark, the roar, and the getaway flight
    (CeresRidley_Func_22, used in Ceres when Samus is nearly dead). No fight, no baby Metroid,
    and no Ceres mode-7 cutscene: once he is above the room he is deleted and area boss bit 2
    ("Meta Ridley gone") is set, so he doesn't come back.
    His tiles cover the escape timer's digits (tools/frigate/timer.py), so the timer is hidden
    while he is in the room (it keeps counting) and its digits are copied back when he leaves,
    or when Samus leaves first (door ASM on the Air Lock's doors, tools/build.py).
    He can't be in the hangar: his tiles take the whole enemy VRAM ($2000 bytes) and the gunship
    needs $1200 of it.
  - Exterior Docking Hangar: Samus' gunship, the Landing Site enemies ($A0:D07F top, $A0:D0BF
    bottom and hatch), with the ship's invisible collision blocks copied from the Landing Site.
    Two patches in $A2 tie it to the frigate (vanilla areas behave as before):
      * area 3: the ship can't be entered until the area boss is dead (before that it would save
        the game as Crateria's ship does, and mark a Crateria save station as used);
      * the lift-off that vanilla starts after Mother Brain (event $0E, Zebes timebomb) also
        starts in area 3 once the area boss is dead. In area 3 it plays the Ceres escape instead
        of SM's ending (game state $21 instead of $26, specs/05-final-da-fragata.md): the station
        (the frigate) explodes, the ship flies to the planet and lands at the Tallon's Landing Site,
        where the game saves and goes on. Samus loses her equipment at that lift-off, before the
        black-out saves: Power Beam only, no missiles, 99 energy (specs/07e);
      * in area 3 the ship climbs to lower heights before the fade (the hangar is 2 screens tall,
        the Landing Site 5).
  - The Ceres escape cutscene names the planet "TALLON IV" instead of "PLANET ZEBES": three new
    letters in its sprite graphics and its spritemap rewritten in place (`tallon_text`).
  - Colours: Ridley's body palette and his fade-in table are recoloured with Meta Ridley's
    (Prime CMDL B2B41738, textures in research/prime_textures/ridley/): purple skin -> the
    violet-tinted steel of the armour, pink membranes -> the lilac muscles. The orange eyes stay.
    These tables are shared by every Ridley in the ROM; Prime only has Meta Ridley.
"""
from __future__ import annotations

import struct

from smlib.compression import compress, decompress
from smlib.rom import Rom, snes_to_pc

from . import timer
from .bosses import along, bgr555_to_rgb, luma, rgb_to_bgr555

# --- Meta Ridley ---------------------------------------------------------------------------------

CERES_RIDLEY = 0xA0E13F
SPECIES_SIZE = 0x40
SPECIES_INIT, SPECIES_MAIN = 0x12, 0x18
RIDLEY_INIT_PAST_BOSS_CHECK = 0xA6A10E   # CeresRidley_Init after "boss dead -> delete myself"
RIDLEY_INIT_START = bytes.fromhex("ae9f07bf28d87e290100f00d")   # LDX $079F; LDA $7ED828,x; AND #1; BEQ
RIDLEY_MAIN = 0xA6A288
FN_WAIT_IN_DARK = 0xA377     # cry_var_A values (functions in $A6)
FN_IDLE = 0xA354             # after the roar; the roar's last instruction ($A6:E969) then
FN_TAKE_OFF = 0xA6AF         # starts the fight's take-off (CeresRidley_Func_9) in the same frame
FN_GETAWAY = 0xA971          # CeresRidley_Func_22: fly to (192, -128)
FN_ABOVE_ROOM = 0xA9A0       # CeresRidley_Func_23: next comes Ceres' mode-7 cutscene
WAIT_IN_DARK = 30            # frames before the eyes light up (Ceres waits 512)
RIDLEY_XY = (0x00B0, 0x0080)
RIDLEY_GONE_BIT = 0x02       # area boss bit set when he has flown away
ENEMY0 = {"x": 0x0F7A, "y": 0x0F7E, "props": 0x0F86, "fn": 0x0FA8, "timer": 0x0FB2}
BABY_METROID_IP = 0x7E7806   # cry_var_03: bit 15 clear = nothing to draw
DRAW_HOOK = 0x178C           # enemy_gfx_drawn_hook (24-bit); LoadEnemies resets it to $A0:804C
SET_BOSS_BIT = 0x8081A6      # SetBossBitForCurArea(A)
CHECK_BOSS_BIT = 0x8081DC    # carry = boss_bits[area] & A
CHECK_EVENT = 0x808233       # carry = event A happened
RIDLEY_POP_PROPS = 0x2800    # vanilla Ceres Ridley placement ($A1:E939)
RIDLEY_PALETTE_SLOT = 0x0001
MINIMAP_DISABLED = 0x05F7    # debug_disable_minimap: UpdateMinimap ($90:A91B) does nothing while set

RIDLEY_SPECIES_PALETTE = 0xA6E14F   # body: colours 1-8 skin, 9-11 membranes, 12-14 eyes
RIDLEY_FADE_TABLE = 0xA6E30A        # 16 steps x colours 1-11 (CeresRidley_Func_5)
RIDLEY_FADE_STEPS = 16

Ramp = list[tuple[int, int, int]]
# k-means over the Meta Ridley textures (dark filler dropped)
ARMOUR: Ramp = [(0, 0, 0), (22, 20, 23), (38, 36, 38), (54, 52, 56), (97, 94, 98), (120, 117, 123),
                (151, 149, 154), (196, 194, 198), (236, 234, 240)]
MUSCLE: Ramp = [(0, 0, 0), (40, 32, 52), (73, 63, 89), (110, 92, 140), (160, 140, 190), (214, 200, 236)]


def _meta_ridley_colour(index: int, value: int) -> int:
    """Colour `index` of Ridley's body palette, recoloured by brightness."""
    if value == 0 or not 1 <= index <= 11:
        return value
    c = bgr555_to_rgb(value)
    return rgb_to_bgr555(along(ARMOUR if index <= 8 else MUSCLE, luma(c)))


def recolour_ridley(rom: Rom) -> None:
    for i in range(16):
        a = RIDLEY_SPECIES_PALETTE + 2 * i
        rom.w16(a, _meta_ridley_colour(i, rom.u16(a)))
    for step in range(RIDLEY_FADE_STEPS):
        for k in range(11):
            a = RIDLEY_FADE_TABLE + 22 * step + 2 * k
            rom.w16(a, _meta_ridley_colour(k + 1, rom.u16(a)))


def _lda(v: int) -> bytes:
    return bytes([0xA9, v & 0xFF, v >> 8])


def _abs(op: int, addr: int) -> bytes:
    return bytes([op, addr & 0xFF, addr >> 8])


def _long(op: int, addr: int) -> bytes:
    return bytes([op, addr & 0xFF, (addr >> 8) & 0xFF, addr >> 16])


def _if_fn(fns: list[int], body: bytes) -> bytes:
    """LDA cry_var_A; CMP #fn1; BEQ body; CMP #fn2; BEQ body; ...; CMP #last; BNE skip; body"""
    assert len(body) < 0x80
    out = _abs(0xAD, ENEMY0["fn"])
    for i, fn in enumerate(fns[:-1]):
        later = 5 * (len(fns) - 2 - i) + 5    # the CMP/BEQ pairs after this one, then CMP/BNE
        out += bytes([0xC9, fn & 0xFF, fn >> 8, 0xF0, later])
    last = fns[-1]
    return out + bytes([0xC9, last & 0xFF, last >> 8, 0xD0, len(body)]) + body


def meta_ridley_init() -> bytes:
    """Species init ($A6, JSL'd, DB=$A6). Ceres Ridley's own init deletes him when the area boss
    is dead, which is always true during the escape: jump past that check. The rest of his init
    turns the HUD minimap off (JSL $90:A7E2 at $A6:A122, as in every SM boss room); this is a
    cutscene in a normal room, so turn it back on: the minimap redraws and marks the map next frame."""
    return (_long(0x22, RIDLEY_INIT_PAST_BOSS_CHECK) + bytes([0xC2, 0x30])     # JSL; REP #$30
            + _abs(0x9C, MINIMAP_DISABLED)                                      # STZ $05F7
            + _lda(0x0000) + _long(0x8F, BABY_METROID_IP)                       # no baby Metroid
            + _lda(RIDLEY_XY[0]) + _abs(0x8D, ENEMY0["x"])
            + _lda(RIDLEY_XY[1]) + _abs(0x8D, ENEMY0["y"])
            + timer.if_timer_running(timer.set_timer_y(timer.TIMER_Y_HIDDEN))   # his tiles cover the digits
            + bytes([0x6B]))


def meta_ridley_main() -> bytes:
    """Species main: Ceres Ridley's main, steered from the outside by his state (cry_var_A)."""
    shorten_wait = (_abs(0xAD, ENEMY0["timer"]) + bytes([0xC9, WAIT_IN_DARK + 1, 0x00, 0x90, 0x06])
                    + _lda(WAIT_IN_DARK) + _abs(0x8D, ENEMY0["timer"]))
    fly_away = _lda(FN_GETAWAY) + _abs(0x8D, ENEMY0["fn"])
    leave = (_abs(0xAD, ENEMY0["props"]) + bytes([0x09, 0x00, 0x07]) + _abs(0x8D, ENEMY0["props"])  # delete
             + _lda(0x804C) + _abs(0x8D, DRAW_HOOK)                                                  # draw hook
             + bytes([0xE2, 0x20, 0xA9, 0xA0]) + _abs(0x8D, DRAW_HOOK + 2) + bytes([0xC2, 0x20])     # -> $A0:804C
             + _lda(RIDLEY_GONE_BIT) + _long(0x22, SET_BOSS_BIT)
             + timer.restore_timer())
    # Checked before Ridley's main runs: the take-off is set by the roar animation, which the
    # engine processes after the main, and Func_9 would turn into the fight right away.
    return (_if_fn([FN_IDLE, FN_TAKE_OFF], fly_away)   # roar done: Ceres would start the fight here
            + _long(0x22, RIDLEY_MAIN) + bytes([0xC2, 0x30])
            # a cutscene, not a fight: stay intangible (Ceres makes him tangible after the fade-in)
            + _abs(0xAD, ENEMY0["props"]) + bytes([0x09, 0x00, 0x04]) + _abs(0x8D, ENEMY0["props"])
            + _if_fn([FN_WAIT_IN_DARK], shorten_wait)
            + _if_fn([FN_ABOVE_ROOM], leave)             # out of sight: Ceres would start mode 7 here
            + bytes([0x6B]))


def meta_ridley(rom: Rom, bank_a0, bank_a6) -> int:
    """Create the Meta Ridley species; returns its $A0 header address."""
    if rom.read(RIDLEY_INIT_PAST_BOSS_CHECK - len(RIDLEY_INIT_START) - 13, len(RIDLEY_INIT_START)) != RIDLEY_INIT_START:
        raise RuntimeError("início do CeresRidley_Init mudou")
    if rom.read(RIDLEY_INIT_PAST_BOSS_CHECK, 1) != b"\x8B":   # PHB
        raise RuntimeError("bytes inesperados em $A6:A10E")
    header = bytearray(rom.read(CERES_RIDLEY, SPECIES_SIZE))
    assert struct.unpack_from("<H", header, SPECIES_INIT)[0] == 0xA0F5 and header[0x0C] == 0xA6
    init = bank_a6.put(meta_ridley_init())
    main = bank_a6.put(meta_ridley_main())
    struct.pack_into("<H", header, SPECIES_INIT, init & 0xFFFF)
    struct.pack_into("<H", header, SPECIES_MAIN, main & 0xFFFF)
    # vanilla species headers sit at $xx3F/$xx7F/$xxBF/$xxFF: keep the same grid
    bank_a0.ptr += (0x3F - bank_a0.ptr) % 0x40
    addr = bank_a0.put(bytes(header))
    recolour_ridley(rom)
    return addr


def ridley_population(species: int) -> bytes:
    x, y = RIDLEY_XY
    return struct.pack("<8H", species & 0xFFFF, x, y, 0, RIDLEY_POP_PROPS, 0, 0, 0) + b"\xFF\xFF\x00"


def ridley_enemy_set(species: int) -> bytes:
    return b"MRIDLEY" + struct.pack("<HH", species & 0xFFFF, RIDLEY_PALETTE_SLOT) + b"\xFF\xFF"


# --- Samus' gunship ------------------------------------------------------------------------------

GUNSHIP_TOP, GUNSHIP_BOTTOM = 0xD07F, 0xD0BF
GUNSHIP_SET = [(GUNSHIP_TOP, 0x0002), (GUNSHIP_BOTTOM, 0x0007)]   # vanilla Landing Site set $B4:8193
GUNSHIP_PROPS = 0x2400
GUNSHIP_Y_ABOVE_GROUND = 88   # Landing Site: ship at y $478, ground row 77 ($4D0)

# Collision of the ship (Landing Site $8F:91F8, rows 69-73, ship centre on block 72, ground row 77):
# (dx, dy from (centre, ground), block word, BTS). Word $x0FF = invisible: the ship is a sprite.
_SHIP_ROWS = {
    -8: (-4, [(0x10FF, 0x12), (0x10FF, 0x13), (0x10FF, 0x55), (0x10FF, 0x00), (0x10FF, 0x40), (0x10FF, 0x15),
              (0x10FF, 0x53), (0x10FF, 0x52)]),
    -7: (-5, [(0x10FF, 0x12), (0x10FF, 0x13)] + [(0x80FF, 0)] * 6 + [(0x10FF, 0x53), (0x10FF, 0x52)]),
    -6: (-6, [(0x10FF, 0x12), (0x10FF, 0x13)] + [(0x80FF, 0)] * 8 + [(0x10FF, 0x53), (0x10FF, 0x52)]),
    -5: (-6, [(0x10FF, 0x80)] * 2 + [(0x80FF, 0)] * 8 + [(0x10FF, 0xC0)] * 2),
    -4: (-4, [(0x10FF, 0x80)] * 4 + [(0x10FF, 0xC0)] * 4),
}
SHIP_TOP_ROW, SHIP_BOTTOM_ROW = -8, -4    # relative to the ground row
SHIP_HALF_WIDTH = 6
SHIP_TOP_INIT_RISE = 25   # GunshipTop_Init (normal start): the top part moves up 25 px from its placement


def ship_top_y(ground: int) -> int:
    """y of the gunship's top part once placed (vanilla Landing Site: ground row 77 -> $45F)."""
    return ground * 16 - GUNSHIP_Y_ABOVE_GROUND - SHIP_TOP_INIT_RISE


def ship_blocks(centre: int, ground: int) -> list[tuple[int, int, int, int]]:
    out = []
    for dy, (dx0, cells) in _SHIP_ROWS.items():
        for k, (w, b) in enumerate(cells):
            out.append((centre + dx0 + k, ground + dy, w, b))
    return out


def gunship_population(centre: int, ground: int) -> bytes:
    """Top, bottom and hatch (bottom with param 2 = 1), in the Landing Site order: the code
    finds the parts at enemy index +$40 and +$80."""
    x, y = centre * 16, ground * 16 - GUNSHIP_Y_ABOVE_GROUND
    parts = [(GUNSHIP_TOP, 0), (GUNSHIP_BOTTOM, 0), (GUNSHIP_BOTTOM, 1)]
    return b"".join(struct.pack("<8H", sp, x, y, 0, GUNSHIP_PROPS, 0, 0, p2) for sp, p2 in parts) + b"\xFF\xFF\x00"


def gunship_enemy_set() -> bytes:
    return b"GUNSHIP" + b"".join(struct.pack("<HH", sp, pal) for sp, pal in GUNSHIP_SET) + b"\xFF\xFF"


FRIGATE_AREA = 3
ENTER_SITE = 0xA2A9BD                     # GunshipTop_8: LDA $0998 (game state); CMP #8; BNE
ENTER_VANILLA = bytes.fromhex("ad9809c90800d043")
LAUNCH_SITE = 0xA2AAA2                    # GunshipTop_12: LDA #$0E; JSL CheckEvent; BCS lift-off
LAUNCH_VANILLA = bytes.fromhex("a90e0022338280b04d")
ENDING_STATE_SITE = 0xA2AD20              # GunshipTop_20: LDA #$26; STA $0998 (fade -> SM's ending)
ENDING_STATE_VANILLA = bytes.fromhex("a92600")
GAME_STATE_ENDING = 0x26                  # $82:84BD: fade out, then $27 (ending and credits)
GAME_STATE_CERES_BLACKOUT = 0x21          # $82:8388: fade out, save, then $22 (Ceres escape cutscene)


# Lift-off heights. Vanilla's are for the 5-screen-tall Landing Site (ship at y $45F): rise slowly
# until y < $380 (GunshipTop_19), then speed up until y < $100 (GunshipTop_20) and fade out. The
# hangar ship sits at y ~$12F, so it would fade out almost at once: in area 3 use lower heights.
LIFTOFF_SITES = [
    (0xA2ACF9, bytes.fromhex("bd7e0fc98003"), 0x00E0),   # LDA $0F7E,x; CMP #$0380 (then BPL)
    (0xA2AD12, bytes.fromhex("bd7e0fc90001"), 0x0060),   # LDA $0F7E,x; CMP #$0100 (then BPL)
]


def _liftoff_height(vanilla: bytes, frigate: int) -> bytes:
    """LDA area; CMP #3; BEQ frigate; <vanilla LDA/CMP>; RTS; frigate: LDA $0F7E,x; CMP #h; RTS.
    The caller's BPL reads the flags of the CMP (RTS keeps them)."""
    own = vanilla[:3] + bytes([0xC9, frigate & 0xFF, frigate >> 8, 0x60])
    other = vanilla + bytes([0x60])
    return _abs(0xAD, 0x079F) + bytes([0xC9, FRIGATE_AREA, 0x00, 0xF0, len(other)]) + other + own


def _boss_dead_in_frigate(if_not_frigate: bytes, if_alive: bytes, if_dead: bytes) -> bytes:
    """LDA area; CMP #3; BNE other; LDA #1; JSL CheckBossBit; BCS dead; <alive> dead: <dead>
    other: <if_not_frigate>. Each tail must end in RTS."""
    alive_and_dead = if_alive + if_dead
    check = _lda(0x0001) + _long(0x22, CHECK_BOSS_BIT) + bytes([0xB0, len(if_alive)])
    return (_abs(0xAD, 0x079F) + bytes([0xC9, FRIGATE_AREA, 0x00, 0xD0, len(check) + len(alive_and_dead)])
            + check + alive_and_dead + if_not_frigate)


def gunship(rom: Rom, bank_a2) -> None:
    if rom.read(ENTER_SITE, len(ENTER_VANILLA)) != ENTER_VANILLA:
        raise RuntimeError(f"bytes inesperados em ${ENTER_SITE:06X}")
    if rom.read(LAUNCH_SITE, len(LAUNCH_VANILLA)) != LAUNCH_VANILLA:
        raise RuntimeError(f"bytes inesperados em ${LAUNCH_SITE:06X}")
    game_state = _abs(0xAD, 0x0998) + bytes([0x60])
    # replaces "LDA $0998": a fake game state (0, not gameplay) keeps the ship shut
    enter = bank_a2.put(_boss_dead_in_frigate(game_state, _lda(0x0000) + bytes([0x60]), game_state))
    rom.write(ENTER_SITE, _abs(0x20, enter & 0xFFFF))
    # replaces "LDA #$0E; JSL CheckEvent" (carry = lift off): event $0E, or area 3 with the boss dead
    event = _lda(0x000E) + _long(0x22, CHECK_EVENT)
    not_frigate = bytes([0x18, 0x60])                      # CLC; RTS
    frigate = _boss_dead_in_frigate(not_frigate, bytes([0x18, 0x60]), bytes([0x38, 0x60]))
    launch = bank_a2.put(event + bytes([0x90, 1, 0x60]) + frigate)   # BCC check frigate; RTS (carry set)
    rom.write(LAUNCH_SITE, _abs(0x20, launch & 0xFFFF) + bytes([0xEA] * 4))
    for site, vanilla, height in LIFTOFF_SITES:
        if rom.read(site, len(vanilla)) != vanilla:
            raise RuntimeError(f"bytes inesperados em ${site:06X}")
        routine = bank_a2.put(_liftoff_height(vanilla, height))
        rom.write(site, _abs(0x20, routine & 0xFFFF) + bytes([0xEA] * 3))
    if rom.read(ENDING_STATE_SITE, len(ENDING_STATE_VANILLA)) != ENDING_STATE_VANILLA:
        raise RuntimeError(f"bytes inesperados em ${ENDING_STATE_SITE:06X}")
    # replaces "LDA #$26" before "STA $0998": the frigate's ship flies off like Samus from Ceres
    ending_state = bank_a2.put(ending_state_routine())
    rom.write(ENDING_STATE_SITE, _abs(0x20, ending_state & 0xFFFF))


# The ship landing at the end of the Ceres escape (GunshipTop_3, $A2:A80C) has the vanilla Landing
# Site's heights as constants: fast descent until y $300, then slow until y $45F, where the top
# part stops (bottom = top + 40, hatch = top - 1, relative). Only that cutscene uses them, and it
# only plays in area 0 (load station $12), where the Tallon's Landing Site now is
# (specs/07g-salas-mvp-tallon.md): they become that room's heights. Vanilla Crateria is unreachable.
LANDING_SLOWDOWN_SITE = 0xA2A80F          # CMP #$0300 (fast while above)
LANDING_STOP_SITES = (0xA2A8AD, 0xA2A8B2)  # CMP #$045F; ... LDA #$045F
LANDING_VANILLA_STOP, LANDING_VANILLA_SLOWDOWN = 0x045F, 0x0300


def landing_height(rom: Rom, top_y: int) -> None:
    """Make the escape landing stop with the ship's top part at `top_y` (same slow stretch)."""
    if rom.read(LANDING_SLOWDOWN_SITE, 3) != bytes([0xC9]) + struct.pack("<H", LANDING_VANILLA_SLOWDOWN):
        raise RuntimeError(f"bytes inesperados em ${LANDING_SLOWDOWN_SITE:06X}")
    for site, op in zip(LANDING_STOP_SITES, (0xC9, 0xA9)):
        if rom.read(site, 3) != bytes([op]) + struct.pack("<H", LANDING_VANILLA_STOP):
            raise RuntimeError(f"bytes inesperados em ${site:06X}")
    slowdown = top_y - (LANDING_VANILLA_STOP - LANDING_VANILLA_SLOWDOWN)
    if not 0 < slowdown < top_y < 0x8000:
        raise ValueError(f"altura de pouso ${top_y:04X} fora do alcance")
    rom.w16(LANDING_SLOWDOWN_SITE + 1, slowdown)
    for site in LANDING_STOP_SITES:
        rom.w16(site + 1, top_y)


# Prime: Samus loses her equipment in the frigate's explosion and reaches Tallon IV with the Power
# Beam only (specs/07e-chegada-e-perda-de-itens.md). Cleared at the lift-off, before state $21 saves:
# the mid-cutscene save, the load and the landing save all come out without items.
ARRIVAL_ZEROED = (0x09A2, 0x09A4, 0x09A6, 0x09A8,   # items and beams (beam 0 = Power Beam)
                  0x09C0,                           # reserve mode
                  0x09C6, 0x09C8, 0x09CA, 0x09CC, 0x09CE, 0x09D0,   # missiles, supers, power bombs
                  0x09D2, 0x09D4, 0x09D6,           # HUD item, reserve tanks
                  0x0A04)                           # HUD auto-cancel item
ARRIVAL_ENERGY = 99                                 # $09C2/$09C4


def ending_state_routine() -> bytes:
    """LDA area; CMP #3; BNE vanilla; <lose the items>; LDA #$21; RTS; vanilla: LDA #$26; RTS"""
    lose_items = (b"".join(_abs(0x9C, a) for a in ARRIVAL_ZEROED)                 # STZ
                  + _lda(ARRIVAL_ENERGY) + _abs(0x8D, 0x09C2) + _abs(0x8D, 0x09C4))
    frigate = lose_items + _lda(GAME_STATE_CERES_BLACKOUT) + bytes([0x60])
    assert len(frigate) < 0x80
    return (_abs(0xAD, 0x079F) + bytes([0xC9, FRIGATE_AREA, 0x00, 0xD0, len(frigate)]) + frigate
            + _lda(GAME_STATE_ENDING) + bytes([0x60]))


# --- "TALLON IV" in the Ceres escape cutscene ----------------------------------------------------

# $8B:C699 (CinematicFunction for the planet) loads the cutscene's sprite tiles from $96:EC76:
# LDA #$9600; STA $48 (bank in $49); LDA #$EC76; STA $47. Nothing else reads that graphic.
ESCAPE_GFX = 0x96EC76
ESCAPE_GFX_BANK_SITE = 0x8BC6BE           # A9 00 96: bank = byte at +2
ESCAPE_GFX_ADDR_SITE = 0x8BC6C3           # A9 76 EC: address = word at +1
PLANET_TEXT = 0x8C9654                    # spritemap "PLANET ZEBES" (11 pieces), rewritten in place
PLANET_TEXT_COUNT = 11
TEXT_X0, TEXT_ADVANCE, TEXT_Y = -36, 8, -8
# vanilla letters (tiles of the graphic): P $8F, L $97, A $98, N $99, E $9A, T $9B, Z $9C, B $9D, S $9E
TEXT_TILES = {"T": 0x9B, "A": 0x98, "L": 0x97, "N": 0x99, "O": 0xAC, "I": 0xAD, "V": 0xAE}
VANILLA_LETTER_TILES = [0x8F] + list(range(0x97, 0x9F))
NEW_LETTERS = {   # colour 3 = outline, 1 = inside, like the vanilla letters (planes 0/1 only)
    0xAC: ".333333. 33111133 31133113 31133113 31133113 31133113 33111133 .333333.",
    0xAD: ".333333. .311113. ..3113.. ..3113.. ..3113.. ..3113.. .311113. .333333.",
    0xAE: "333..333 313..313 313..313 3133.313 .31313.. .31113.. ..313... ..333...",
}
PLANET_NAME = "TALLON IV"


def letter_tile(rows: str) -> bytes:
    out = bytearray(32)
    for y, row in enumerate(rows.split()):
        for x, c in enumerate(row):
            v = 0 if c == "." else int(c)
            if v & 1:
                out[2 * y] |= 0x80 >> x
            if v & 2:
                out[2 * y + 1] |= 0x80 >> x
    return bytes(out)


def text_spritemap(name: str) -> bytes:
    """Count, then per letter: x (16 bits, 9 used), y (8 bits), attribute (tile, palette 0)."""
    pieces = [struct.pack("<HbH", (TEXT_X0 + TEXT_ADVANCE * i) & 0x1FF, TEXT_Y, TEXT_TILES[c])
              for i, c in enumerate(name) if c != " "]
    return struct.pack("<H", len(pieces)) + b"".join(pieces)


def escape_gfx_pointer(rom: Rom) -> int:
    return rom.u8(ESCAPE_GFX_BANK_SITE + 2) << 16 | rom.u16(ESCAPE_GFX_ADDR_SITE + 1)


def tallon_text(rom: Rom, put) -> None:
    """The Ceres escape cutscene says "TALLON IV": letters O, I, V drawn in empty tiles of its
    sprite graphic (recompressed into the expanded banks: `put(payload) -> SNES address`, the build's
    fixed allocator, specs/09c) and the text spritemap rewritten."""
    if rom.read(ESCAPE_GFX_BANK_SITE, 3) != bytes.fromhex("a90096"):
        raise RuntimeError(f"bytes inesperados em ${ESCAPE_GFX_BANK_SITE:06X}")
    if rom.read(ESCAPE_GFX_ADDR_SITE, 3) != bytes.fromhex("a976ec"):
        raise RuntimeError(f"bytes inesperados em ${ESCAPE_GFX_ADDR_SITE:06X}")
    if rom.u16(PLANET_TEXT) != PLANET_TEXT_COUNT:
        raise RuntimeError(f"bytes inesperados em ${PLANET_TEXT:06X}")
    gfx = bytearray(decompress(rom.data, snes_to_pc(ESCAPE_GFX))[0])
    for t, rows in NEW_LETTERS.items():
        if any(gfx[32 * t:32 * t + 32]):
            raise RuntimeError(f"tile ${t:02X} da cena de Ceres não está vazio")
        gfx[32 * t:32 * t + 32] = letter_tile(rows)
    packed = compress(bytes(gfx))
    if decompress(packed)[0] != bytes(gfx):
        raise RuntimeError("compressão do gráfico da cena de Ceres não volta igual")
    at = put(packed)
    rom.write(ESCAPE_GFX_BANK_SITE + 2, bytes([at >> 16]))
    rom.w16(ESCAPE_GFX_ADDR_SITE + 1, at & 0xFFFF)
    text = text_spritemap(PLANET_NAME)
    assert len(text) <= 2 + 5 * PLANET_TEXT_COUNT
    rom.write(PLANET_TEXT, text)
    print(f"  cena de Ceres: {PLANET_NAME!r}, gráfico em ${at:06X} ({len(packed)} bytes)")


def check_rom(rom: Rom) -> list[str]:
    """Problems with the frigate's lift-off and the escape cutscene text in a built ROM
    (tools/validate.py)."""
    problems = []
    site = rom.read(ENDING_STATE_SITE, 3)
    routine = ending_state_routine()
    if site[0] != 0x20 or rom.read(ENDING_STATE_SITE & 0xFF0000 | rom.u16(ENDING_STATE_SITE + 1), len(routine)) != routine:
        problems.append(f"decolagem: ${ENDING_STATE_SITE:06X} não chama a rotina área 3 → perde os itens e $21, "
                        "outras → $26")
    if rom.u16(PLANET_TEXT) != len(PLANET_NAME.replace(" ", "")):
        problems.append(f"cena de Ceres: texto em ${PLANET_TEXT:06X} com {rom.u16(PLANET_TEXT)} letras")
    elif rom.read(PLANET_TEXT, len(text_spritemap(PLANET_NAME))) != text_spritemap(PLANET_NAME):
        problems.append(f"cena de Ceres: texto em ${PLANET_TEXT:06X} não é {PLANET_NAME!r}")
    vanilla = decompress(rom.data, snes_to_pc(ESCAPE_GFX))[0]
    gfx = decompress(rom.data, snes_to_pc(escape_gfx_pointer(rom)))[0]
    for t in VANILLA_LETTER_TILES:
        if gfx[32 * t:32 * t + 32] != vanilla[32 * t:32 * t + 32]:
            problems.append(f"cena de Ceres: letra vanilla no tile ${t:02X} mudou")
    for t, rows in NEW_LETTERS.items():
        if gfx[32 * t:32 * t + 32] != letter_tile(rows):
            problems.append(f"cena de Ceres: tile ${t:02X} sem a letra nova")
    return problems

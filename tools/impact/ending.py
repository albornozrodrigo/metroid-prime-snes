"""specs/20i: the game's end, after Metroid Prime (specs/20h) - the way out of the Lair into the ending.

Epic 20, decision 5 (the user's, the default): the credits and the end screen with the item percentage, the frigate's end reused.
The frigate's end (specs/05) was SM's ending: game state $26 (GameState_38_SamusEscapesFromZebes, $82:84BD: main gameplay while
the screen fades out) -> $27 (the ending and credits, the cinematic $8B:D480: Zebes exploding, the credits, and at their end
"YOUR RATE FOR COLLECTING ITEMS IS N%", CalcItemPercentageCount $8B:E627 from the capacities and the item and beam bits). Since
specs/05 the frigate's take-off plays Ceres' escape instead; the SM ending stays in the ROM, as it was (the gunship of area 0 still
takes off into it with the event $0E, which no play sets: tests/run_tests.py fc_ending). Nothing of it is changed here: the Lair
starts it.

The way out: the Lair's only door is the ceiling one (back up to the Subchamber Five, specs/20h), shut by the Torizo's grey cap
until the win. Prime's Lair has no door at all: the fight is the world's end. Here Samus, after the win (the bit $10 of area 0,
the arena's: chozo/bosses.py ARENAS), shoots the cap open and jumps up into the door: before she touches its door blocks (a door
transition cannot be turned into another game state: its last step sets $0998 = 8, $82:E737), the Lair's main ASM sees her past
the cap's row inside the door's columns, locks her (Samus code 0, $90:F084: no movement, no input) and starts the ending ($0998 =
$26, the fade at once: $0723/$0725 = 0, as GunshipTop_20 $A2:AD0E does).

Where (measured in the emulator, scratchpad s20i): the door's cap is 4 blocks wide from the door entry's cap block (build.py
door_cap_and_screen: (screen * 16 + 6, 2) for a ceiling door); with the cap shut Samus' top stops exactly at its bottom edge
(y = (cap row + 1) * 16) and only while her box overlaps its columns (x radius $0AFE: centre X in [348, 420] for the 5 px of
standing and spinning); with the cap open her top passes that edge and reaches the door's blocks 8 frames later. So the check is
"her box overlaps the door's columns and her top is above the cap's bottom edge": reachable only through the open cap, and
always before the door.
"""
from __future__ import annotations

GAME_STATE = 0x0998
GAMEPLAY, ENDING_START, ENDING_CREDITS = 0x08, 0x26, 0x27   # main gameplay; GameState_38 (fade, then $27 = ending and credits)
BOSS_BITS = 0x7ED828            # + area: the area's boss bits (SetBossBitForCurArea $80:81A6)
SAMUS_X, SAMUS_Y, SAMUS_X_RADIUS, SAMUS_Y_RADIUS = 0x0AF6, 0x0AFA, 0x0AFE, 0x0B00
FADE_DELAY, FADE_COUNTER = 0x0723, 0x0725
CALL_SAMUS_CODE = 0x90F084      # CallSomeSamusCode (A = the code; 0 = lock Samus, $90:F109), JSL / RTL
LOCK_SAMUS = 0x00
DOOR_WIDTH = 4                  # blocks of a ceiling door (its cap PLM's width)
PERCENT_ROUTINE = 0x8BE627      # CalcItemPercentageCount
# its tables (read by it, $8B:E70D-$8B:E768): the 5 RAM words and their divisors, the 11 item bits, the 5 beam bits, the digits
PERCENT_TABLES = (0x8BE70D, 0x8BE769 - 0x8BE70D)   # up to CinematicFunction_Intro_Func146
PERCENT_ROUTINE_SIZE = 0x8BE70D - PERCENT_ROUTINE


def exit_routine(area: int, bit: int, cap_x: int, cap_y: int) -> bytes:
    """The Lair's way out (in $8F, run by RunRoomMainCode $8F:E8BD with JSR, DB = $8F: WRAM's low 8 KB mirrored). In main
    gameplay, with the boss bit `bit` of `area` set, Samus' box overlapping the ceiling door's columns (cap_x .. cap_x + 3) and
    her top above the bottom edge of the cap's row: lock Samus, game state $26, fade at once."""
    left, right, edge = cap_x * 16, (cap_x + DOOR_WIDTH) * 16, (cap_y + 1) * 16
    w = lambda v: v.to_bytes(2, "little")   # noqa: E731
    code = [
        bytes([0x08, 0xC2, 0x30]),                                          # PHP / REP #$30
        b"\xad" + w(GAME_STATE) + b"\xc9" + w(GAMEPLAY), ("bne",),          # LDA $0998 / CMP #8 / BNE done
        b"\xaf" + (BOSS_BITS + area).to_bytes(3, "little") + b"\x29" + w(bit), ("beq",),   # LDA $7ED828+area / AND #bit / BEQ
        b"\xad" + w(SAMUS_X) + b"\x18\x6d" + w(SAMUS_X_RADIUS) + b"\xc9" + w(left + 1), ("bcc",),   # X + r > left
        b"\xad" + w(SAMUS_X) + b"\x38\xed" + w(SAMUS_X_RADIUS) + b"\xc9" + w(right), ("bcs",),      # X - r < right
        b"\xad" + w(SAMUS_Y) + b"\x38\xed" + w(SAMUS_Y_RADIUS) + b"\xc9" + w(edge), ("bcs",),       # Y - r < edge (top past it)
        b"\xa9" + w(LOCK_SAMUS) + b"\x22" + CALL_SAMUS_CODE.to_bytes(3, "little"),                 # LDA #0 / JSL lock Samus
        b"\xa9" + w(ENDING_START) + b"\x8d" + w(GAME_STATE),                                        # LDA #$26 / STA $0998
        b"\x9c" + w(FADE_DELAY) + b"\x9c" + w(FADE_COUNTER),                                        # STZ $0723 / STZ $0725
        bytes([0x28, 0x60]),                                                # done: PLP / RTS
    ]
    ops = {"bne": 0xD0, "beq": 0xF0, "bcc": 0x90, "bcs": 0xB0}
    size = sum(2 if isinstance(c, tuple) else len(c) for c in code)
    done = size - 2
    out = bytearray()
    for c in code:
        if isinstance(c, tuple):
            out += bytes([ops[c[0]], (done - (len(out) + 2)) & 0xFF])
        else:
            out += c
    return bytes(out)


def alive_main_asm(arena_routine: int, exit_at: int) -> bytes:
    """The Lair's alive state's main ASM: the arena routine (chozo/bosses.py stub's JSL) then the way out (JMP, its RTS returns)."""
    return b"\x22" + arena_routine.to_bytes(3, "little") + b"\x4c" + (exit_at & 0xFFFF).to_bytes(2, "little")

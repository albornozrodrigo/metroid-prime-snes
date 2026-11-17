"""Escape timer pieces shared by the boss room (starts it) and the Meta Ridley scene.

The timer digits are sprites whose tiles sit at the end of the enemy VRAM ($7E00/$7F00). Nothing
reloads them by itself: whoever starts the timer copies them (Mother Brain does, so does our boss
room), and anything that loads enemy tiles over them (Meta Ridley's tiles fill all of the enemy
VRAM) has to copy them back.
"""
from __future__ import annotations

# The first two transfers of Mother Brain's escape list ($A6:C4CB): (size, source, VRAM word address)
TIMER_TILE_TRANSFERS = [(0x0200, 0xB0C000, 0x7E00), (0x0120, 0xB0C200, 0x7F00)]
TIMER_STATUS = 0x0943
TIMER_Y = 0x094A
TIMER_Y_IN_PLACE = 0x3000   # where ProcessTimer_MovingIntoPlace ($80:9E58) parks it
TIMER_Y_HIDDEN = 0xF000     # below the screen; the timer keeps counting


def queue_timer_tiles() -> bytes:
    """Append the digit tiles to the VRAM write queue ($D0 + tail at $0330), 16-bit A/X.
    Uses only bank-0 addresses, so it runs with any data bank between $80 and $BF."""
    code = bytearray([0xAE, 0x30, 0x03])                                       # LDX $0330
    for size, src, vram in TIMER_TILE_TRANSFERS:
        code += bytes([0xA9, size & 0xFF, size >> 8, 0x9D, 0xD0, 0x00])          # LDA #size; STA $00D0,x
        code += bytes([0xA9, src & 0xFF, (src >> 8) & 0xFF, 0x9D, 0xD2, 0x00])   # LDA #src;  STA $00D2,x
        code += bytes([0xA9, src >> 16, 0x00, 0x9D, 0xD4, 0x00])                 # LDA #bank; STA $00D4,x
        code += bytes([0xA9, vram & 0xFF, vram >> 8, 0x9D, 0xD5, 0x00])          # LDA #vram; STA $00D5,x
        code += bytes([0x8A, 0x18, 0x69, 0x07, 0x00, 0xAA])                       # TXA; CLC; ADC #7; TAX
    code += bytes([0x8E, 0x30, 0x03])                                           # STX $0330
    return bytes(code)


def set_timer_y(value: int) -> bytes:
    return bytes([0xA9, value & 0xFF, value >> 8, 0x8D, TIMER_Y & 0xFF, TIMER_Y >> 8])   # LDA #v; STA $094A


def if_timer_running(body: bytes) -> bytes:
    """LDA $0943; BEQ skip; body (16-bit A)."""
    assert len(body) < 0x80
    return bytes([0xAD, TIMER_STATUS & 0xFF, TIMER_STATUS >> 8, 0xF0, len(body)]) + body


def restore_timer() -> bytes:
    """If the timer runs: copy its digits back to VRAM and put it back in place."""
    return if_timer_running(queue_timer_tiles() + set_timer_y(TIMER_Y_IN_PLACE))


def restore_timer_door_asm() -> bytes:
    """Door ASM ($8F, JSR'd during the transition) for the doors out of Meta Ridley's room:
    Samus may leave before he does, with his tiles still over the digits."""
    return bytes([0x08, 0xC2, 0x30]) + restore_timer() + bytes([0x28, 0x60])   # PHP; REP #$30; ...; PLP; RTS

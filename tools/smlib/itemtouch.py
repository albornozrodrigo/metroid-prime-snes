"""specs/13: Samus' touch of an item finds the item, not a dead PLM slot left with the item's block index.

Vanilla (bytes of base/sm_fix.sfc, C vendor/sm/src/sm_84.c:2882): touching an item's block (type B, BTS $45) spawns a PLM
whose setup, $84:EEAB, takes the block index from its own slot, zeroes it, and looks for the first slot from the top (39)
down with that block index (`CMP $1C87,X`), then marks it touched (`plm_timers = $FF`). It does not look at the slot's
header. A PLM that ends with PlmInstr_Delete ($84:86BC) zeroes only its header, so its block index stays behind; a bomb or a
power bomb sweeping an item's block spawns kBlockBombedReact_Special_Plm[$45] = $84:B62F (setup nullsub $84:B3CF, list
$84:AAE3 = Delete) with the item's block index: a dead slot with the item's index (emulator, specs/13). If that dead slot is
above the item's and the touch's own PLM lands in a slot above both, the touch marks the dead slot and the item is not
taken until the room reloads (specs/12f found it in the Main Plaza).

The patch replaces the search loop at $84:EEB7 (13 bytes: LDX #$004E / CMP $1C87,X / BEQ / DEX DEX / BPL / BRK) with a JSR
to a routine at FIND (end of bank $84) that looks for a *live* slot (header $1C37,X non-zero) with the index first and, only
if there is none, does the vanilla search (first slot with the index, dead or not; BRK when there is none, as vanilla). The
two words after the JSR (BRA to $EEC4) skip the old loop's remaining bytes, left as they were. Y is kept (PHY/PLY).
"""
from __future__ import annotations

SITE = 0x84EEB7            # LDX #$004E: the start of the vanilla search loop
RESUME = 0x84EEC4          # LDA #$00FF / STA $1D77,X: mark the slot found
VANILLA_LOOP = bytes.fromhex("a24e00dd871cf005caca10f700")   # $84:EEB7-EEC3, read from the base ROM
PROLOGUE = bytes.fromhex("ad780ad01cbbbd871c9e871c")       # $84:EEAB-EEB6: LDA $0A78 / BNE / TYX / LDA $1C87,X / STZ $1C87,X
ROUTINE = bytes.fromhex(
    "5a"            # PHY
    "a24e00"        # LDX #$004E
    "dd871c"        # live: CMP $1C87,X
    "d005"          #       BNE next
    "bc371c"        #       LDY $1C37,X      (the slot's PLM header)
    "d011"          #       BNE found        (a live PLM with this block index)
    "caca"          # next: DEX DEX
    "10f2"          #       BPL live
    "a24e00"        # LDX #$004E           (no live slot: the vanilla search)
    "dd871c"        # any:  CMP $1C87,X
    "f005"          #       BEQ found
    "caca"          #       DEX DEX
    "10f7"          #       BPL any
    "00"            # BRK                  (no slot at all: vanilla's BRK)
    "7a"            # found: PLY
    "60"            # RTS
)
FIND = 0x850000 - len(ROUTINE)   # the last bytes of bank $84 (free in the base ROM: $FF)

# specs/12g2: a shot on a coloured door's block spawns a PLM whose setup, PlmSetup_Door_Strange ($84:C7E2, sm_84.c:2129),
# has the same lookup: it takes its own block index, zeroes it and looks for the first slot from the top (39) down with
# that index, then puts the shot's type in that slot's timer; none found: RTS (no BRK). A dead slot with the door's block
# index above the door's PLM (left by a PLM that ended there, as specs/13's power bomb on an item) would take the shot and
# the door would not react to it (the next shot spawns into the dead slot itself and hits). Same fix: its loop at
# DOOR_SITE (13 bytes: LDX #$004E / CMP $1C87,X / BEQ found / DEX DEX / BPL / RTS) becomes JSR DOOR_FIND / BCC to the
# vanilla RTS / BRA to the vanilla `found` (7 bytes; the other 6 stay as they were, unreachable); the routine, just before
# FIND, looks for a live slot first, then does the vanilla search, and returns with carry set when it found a slot (X =
# the slot), clear when none.
DOOR_SITE = 0x84C7E9            # LDX #$004E: the start of the door shot's search loop
DOOR_RTS = 0x84C7F5             # its RTS when no slot has the index
DOOR_FOUND = 0x84C7F6           # LDY $0DDE / LDA $0C18,Y / AND #$1FFF / ORA #$8000 / STA $1D77,X / RTS
DOOR_LOOP = bytes.fromhex("a24e00dd871cf005caca10f760")    # $84:C7E9-C7F5, read from the base ROM
DOOR_PROLOGUE = bytes.fromhex("bbbd871c9e871c")           # $84:C7E2-C7E8: TYX / LDA $1C87,X / STZ $1C87,X
DOOR_AFTER = bytes.fromhex("acde0db9180c29ff1f0900809d771d60")   # $84:C7F6-C805, the vanilla `found`, kept
DOOR_ROUTINE = bytes.fromhex(
    "5a"            # PHY
    "a24e00"        # LDX #$004E
    "dd871c"        # live: CMP $1C87,X
    "d005"          #       BNE next
    "bc371c"        #       LDY $1C37,X      (the slot's PLM header)
    "d013"          #       BNE found        (a live PLM with this block index)
    "caca"          # next: DEX DEX
    "10f2"          #       BPL live
    "a24e00"        # LDX #$004E           (no live slot: the vanilla search)
    "dd871c"        # any:  CMP $1C87,X
    "f007"          #       BEQ found
    "caca"          #       DEX DEX
    "10f7"          #       BPL any
    "7a"            # PLY
    "18"            # CLC                  (no slot at all: the caller returns, as vanilla)
    "60"            # RTS
    "7a"            # found: PLY
    "38"            # SEC
    "60"            # RTS
)
DOOR_FIND = FIND - len(DOOR_ROUTINE)   # just before the item touch's routine (free in the base ROM: $FF)


def code(rom) -> list[tuple[int, bytes]]:
    """(address, bytes) the patches write (the item touch, specs/13; the door shot, specs/12g2); checks the vanilla bytes
    they replace in `rom` (the base ROM)."""
    if rom.read(SITE - len(PROLOGUE), len(PROLOGUE)) != PROLOGUE or rom.read(SITE, len(VANILLA_LOOP)) != VANILLA_LOOP:
        raise RuntimeError(f"$84:EEAB não é a busca vanilla do toque no item: "
                           f"{rom.read(SITE - len(PROLOGUE), len(PROLOGUE) + len(VANILLA_LOOP)).hex()}")
    door_vanilla = DOOR_PROLOGUE + DOOR_LOOP + DOOR_AFTER
    if rom.read(DOOR_SITE - len(DOOR_PROLOGUE), len(door_vanilla)) != door_vanilla:
        raise RuntimeError(f"$84:C7E2 não é a busca vanilla do tiro na porta de cor: "
                           f"{rom.read(DOOR_SITE - len(DOOR_PROLOGUE), len(door_vanilla)).hex()}")
    after_jsr = SITE + 5                               # JSR (3) + BRA (2)
    bra = bytes([0x80, (RESUME - after_jsr) & 0xFF])
    door = (bytes([0x20, DOOR_FIND & 0xFF, (DOOR_FIND >> 8) & 0xFF])                  # JSR DOOR_FIND
            + bytes([0x90, (DOOR_RTS - (DOOR_SITE + 5)) & 0xFF])                       # BCC -> the vanilla RTS
            + bytes([0x80, (DOOR_FOUND - (DOOR_SITE + 7)) & 0xFF]))                    # BRA -> the vanilla `found`
    return [(SITE, bytes([0x20, FIND & 0xFF, (FIND >> 8) & 0xFF]) + bra), (FIND, ROUTINE),
            (DOOR_SITE, door), (DOOR_FIND, DOOR_ROUTINE)]


def apply(rom) -> int:
    """Write the patches (the routines' space must be free, $FF); returns the bytes used in free space."""
    for addr, data in code(rom):
        if addr in (FIND, DOOR_FIND) and rom.read(addr, len(data)) != b"\xFF" * len(data):
            raise RuntimeError(f"espaço em ${addr:06X} não está livre (toque no item, specs/13; tiro na porta, specs/12g2)")
    for addr, data in code(rom):
        rom.write(addr, data)
    return len(ROUTINE) + len(DOOR_ROUTINE)


def simulate(rom, routine: int, headers: list[int], indices: list[int], index: int, steps: int = 2000):
    """Run the lookup routine at `routine` ($84, read from `rom`) on a PLM table (40 slots: headers $1C37, block indices
    $1C87) for block index `index` (in A), with a tiny interpreter of the opcodes the routines use; returns ("rts", X, carry)
    or ("brk", None, None). Independent of how the bytes were generated (validate: mutation-proof)."""
    pc, x, y, carry, stack, z, n = routine, 0, 0xBEEF, None, [], False, False
    def table(addr):
        return headers if addr == 0x1C37 else indices if addr == 0x1C87 else None
    for _ in range(steps):
        def byte(a):   # the bank's last instruction has no operand bytes after it
            return rom.u8(a) if a & 0xFFFF >= 0x8000 and (a >> 16) == (routine >> 16) else 0
        op = byte(pc)
        arg16 = byte(pc + 1) | byte(pc + 2) << 8
        rel = byte(pc + 1)
        rel = rel - 256 if rel >= 128 else rel
        if op == 0x5A:   # PHY
            stack.append(y); pc += 1
        elif op == 0x7A:   # PLY
            y = stack.pop(); z, n = y == 0, bool(y & 0x8000); pc += 1
        elif op == 0xA2:   # LDX #imm16
            x = arg16; z, n = x == 0, bool(x & 0x8000); pc += 3
        elif op == 0xDD:   # CMP abs,X
            v = table(arg16)[x // 2]; z, n, carry = index == v, bool((index - v) & 0x8000), index >= v; pc += 3
        elif op == 0xBC:   # LDY abs,X
            y = table(arg16)[x // 2]; z, n = y == 0, bool(y & 0x8000); pc += 3
        elif op == 0xCA:   # DEX
            x = (x - 1) & 0xFFFF; z, n = x == 0, bool(x & 0x8000); pc += 1
        elif op in (0xD0, 0xF0, 0x10, 0x80):   # BNE, BEQ, BPL, BRA
            take = {0xD0: not z, 0xF0: z, 0x10: not n, 0x80: True}[op]
            pc += 2 + (rel if take else 0)
        elif op == 0x18:
            carry = False; pc += 1
        elif op == 0x38:
            carry = True; pc += 1
        elif op == 0x60:
            if y != 0xBEEF or stack:
                raise RuntimeError(f"rotina em ${routine:06X}: Y ou a pilha não voltaram")
            return "rts", x // 2, carry
        elif op == 0x00:
            return "brk", None, None
        else:
            raise RuntimeError(f"rotina em ${routine:06X}: opcode ${op:02X} em ${pc:06X} fora do interpretador")
    raise RuntimeError(f"rotina em ${routine:06X}: não termina")


def behaviour_problems(rom) -> list[str]:
    """The two lookups (built ROM) on synthetic PLM tables: a dead slot (header 0) with the index above the live one ->
    the live one; only dead ones -> the highest (vanilla); none -> BRK (item touch) / carry clear (door shot); a live one
    alone -> it."""
    problems = []
    def table(dead=(), live=()):
        headers, indices = [0] * 40, [0] * 40
        for k in dead:
            indices[k] = 0x1234
        for k in live:
            headers[k], indices[k] = 0xC8A0, 0x1234
        return headers, indices
    cases = [((38,), (35,), 35), ((), (37,), 37), ((39, 36), (), 39), ((), (), None)]
    for name, at, none in (("toque no item (specs/13)", FIND, ("brk", None, None)),
                           ("tiro na porta de cor (specs/12g2)", DOOR_FIND, ("rts", None, False))):
        for dead, live, want in cases:
            try:
                got = simulate(rom, at, *table(dead, live), 0x1234)
            except (RuntimeError, IndexError, TypeError, ValueError) as e:
                problems.append(f"{name}: {e}")
                break
            ok = (got[0] == none[0] and (none[2] is None or got[2] == none[2])) if want is None else \
                (got[0] == "rts" and got[1] == want and (at == FIND or got[2] is True))
            if not ok:
                problems.append(f"{name}: com mortos {list(dead)} e vivos {list(live)} a rotina dá {got}, esperado o slot {want}")
    return problems


def check(rom, base) -> list[str]:
    """Built ROM: the patch bytes are there (from `base`'s vanilla bytes) and the rest of $84:EEAB and of $84:C7E2 is
    vanilla."""
    problems = []
    for addr, data in code(base):
        if rom.read(addr, len(data)) != data:
            what = "tiro na porta de cor (specs/12g2)" if addr in (DOOR_SITE, DOOR_FIND) else "toque no item (specs/13)"
            problems.append(f"{what}: ${addr:06X} = {rom.read(addr, len(data)).hex()}, esperado {data.hex()}")
    tail = SITE + 5
    if rom.read(tail, RESUME + 10 - tail) != base.read(tail, RESUME + 10 - tail):
        problems.append(f"toque no item (specs/13): ${tail:06X}-${RESUME + 9:06X} diferente da ROM base")
    tail = DOOR_SITE + 7
    end = DOOR_FOUND + len(DOOR_AFTER)
    if rom.read(tail, end - tail) != base.read(tail, end - tail):
        problems.append(f"tiro na porta de cor (specs/12g2): ${tail:06X}-${end - 1:06X} diferente da ROM base")
    return problems + behaviour_problems(rom)

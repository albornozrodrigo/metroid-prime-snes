"""specs/12g: hot rooms (epic 12, decision 2: rooms that hurt without the Varia Suit), with Super Metroid's own heat.

SM's heat is a palette FX object, not an area check (bytes of base/sm_fix.sfc, C vendor/sm/src): a room state's FX entry
($83, 16 bytes) has a palette FX bitset (byte 13); LoadFXHeader (sm_89.c:97) spawns, for each bit k set, the
object number k of the area's list (`kAreaPalFxListPointers` $83:AC46 + 2 * area). Norfair's (area 2, $83:ACA6) bit 0 is
**$F761**: init PalInit_F761_Norfair1 ($8D:E440; Samus' heat palette list by suit), list $8D:E45E, whose first instruction
sets the pre-instruction **PalPreInstr_SamusInHeat** ($8D:E379): every frame, without the Varia ($0001) and the Gravity Suit
($0020) in equipped_items ($09A2, `AND #$0021`), periodic damage += $4000 sub (a quarter of energy a frame, 15 a second),
and the heat sound every 8 frames while the energy is over 70. (The Tourian's list has $F761 at bit 0 too, $83:AD06.)

Area 1's list ($83:AC86, the Chozo's area, areas.CHOZO_AREA) is Brinstar's: bits 0-3 used by vanilla rooms ($F775, $F77D,
$F781, $F779), bits 4-7 = $F745 (no vanilla room of area 1 sets them: validate reads every vanilla FX entry). The build
puts $F761 at bit HEAT_BIT and gives each hot room (RoomDef.heat) the FX entry HEAT_FX: no liquid (type 0, surface $FFFF,
the most common vanilla "no FX" entry of area 1, `0000 FFFF FFFF 0000 00 00 02 02 00 xx 00 00`) with that bit.
"""
from __future__ import annotations

AREA_PALFX_LISTS = 0x83AC46   # kAreaPalFxListPointers: one $83 pointer per area
HEAT_OBJECT = 0xF761          # Norfair's heat palette FX object (area 2's list, bit 0)
UNUSED_OBJECT = 0xF745        # what the unused entries of an area's list hold
HEAT_BIT = 4                  # area 1's list entry the build turns into the heat object
NORFAIR = 2
# specs/17b: the heat per area, {area: entry of its palette FX list that holds the heat object}. Area 1 (the Chozo): entry 4,
# written by the build (patch); area 2 (Norfair: the Magmoor Caverns' slot, areas.MAGMOOR_AREA): entry 0, the heat object in
# the base ROM already ($83:ACA6 = F761 F785 F789 F78D F791 F745 F745 F745: heat, then 4 lava glows): nothing to patch.
HEAT_BITS = {1: HEAT_BIT, NORFAIR: 0}
# specs/17d: more palette FX bits a hot room of the area sets with the heat: area 2's lava glows (bits 1-4: $F785, $F789, $F78D,
# $F791 of its list), as vanilla Norfair's hot rooms ($1F); smlib/lava.py FX_HOT
GLOWS = {NORFAIR: 0x1E}


def heat_fx(area: int) -> bytes:
    """The FX entry of a hot room of `area`: no liquid (type 0, surface $FFFF, `0000 FFFF FFFF 0000 00 00 02 02 00 xx 00 00`)
    with the palette FX bit of the area's heat object (HEAT_BITS) and, specs/17d, the area's GLOWS."""
    return (bytes.fromhex("0000" "FFFF" "FFFF" "0000" "00" "00" "02" "02" "00") + bytes([1 << HEAT_BITS[area] | GLOWS.get(area, 0)])
            + bytes.fromhex("0000"))


HEAT_FX = heat_fx(1)          # area 1's (specs/12g)


# specs/12g2 (user decision, 12g question 1, option b): only the Varia Suit protects from the heat. PalPreInstr_SamusInHeat's
# `AND #$0021` ($8D:E37C: 29 21 00, read from the base ROM) tests the Varia ($0001) or the Gravity Suit ($0020); its operand
# byte at $8D:E37D becomes #$01, so the Gravity Suit alone no longer protects (validate's model: a hot room needs the Varia,
# whatever else Samus has). The two attract demos in hot Norfair rooms ($AFFB, $AF14) give Samus the Varia: unchanged.
SUIT_CHECK = 0x8DE37C            # AND #$0021 in PalPreInstr_SamusInHeat ($8D:E379)
SUIT_CHECK_VANILLA = bytes.fromhex("292100")
VARIA_ONLY = bytes.fromhex("290100")


def varia_only_patch(base) -> tuple[int, bytes]:
    """(address, bytes) of the 1-byte patch (written as the whole AND #imm16); checks the base ROM's bytes."""
    if base.read(SUIT_CHECK, len(SUIT_CHECK_VANILLA)) != SUIT_CHECK_VANILLA:
        raise RuntimeError(f"calor: ${SUIT_CHECK:06X} = {base.read(SUIT_CHECK, 3).hex()}, esperado {SUIT_CHECK_VANILLA.hex()} "
                           f"(AND #$0021 de PalPreInstr_SamusInHeat)")
    return SUIT_CHECK, VARIA_ONLY


def list_entry(rom, area: int, bit: int) -> int:
    """$83 address of entry `bit` of `area`'s palette FX list."""
    return 0x830000 | (rom.u16(AREA_PALFX_LISTS + 2 * area) + 2 * bit)


def native(base, area: int) -> bool:
    """specs/17b: whether `area`'s list already holds the heat object at its HEAT_BITS entry in the base ROM (Norfair)."""
    return base.u16(list_entry(base, area, HEAT_BITS[area])) == HEAT_OBJECT


def patch(base, area: int) -> tuple[int, bytes] | None:
    """(address, bytes) that put the heat object at entry HEAT_BITS[area] of `area`'s list; checks the base ROM's bytes (the
    entry unused, Norfair's bit 0 the heat object). specs/17b: None for an area whose list has it there already (native)."""
    if base.u16(list_entry(base, NORFAIR, 0)) != HEAT_OBJECT:
        raise RuntimeError(f"lista de FX de paleta da Norfair: entrada 0 = ${base.u16(list_entry(base, NORFAIR, 0)):04X}, "
                           f"esperado o calor ${HEAT_OBJECT:04X}")
    if area not in HEAT_BITS:
        raise RuntimeError(f"área {area}: sem entrada de calor em HEAT_BITS")
    if native(base, area):
        return None
    bit = HEAT_BITS[area]
    at = list_entry(base, area, bit)
    if base.u16(at) != UNUSED_OBJECT:
        raise RuntimeError(f"lista de FX de paleta da área {area}: entrada {bit} (${at:06X}) = ${base.u16(at):04X}, "
                           f"não está livre (${UNUSED_OBJECT:04X}) nem é o calor (${HEAT_OBJECT:04X})")
    return at, bytes([HEAT_OBJECT & 0xFF, HEAT_OBJECT >> 8])

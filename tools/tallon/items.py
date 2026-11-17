"""Items of the Tallon Overworld (specs/07h-itens-tallon.md).

Prime's 15 Tallon pickups (epic 07, "Itens"; positions read from research/prime_fs) minus the two
artifacts, which have no SM item: 9 Missile Expansions, 2 Energy Tanks, the Space Jump Boots and
the X-Ray Visor. Each one is a visible SM item PLM ($84, research/sm_room_format.md section 5) with
its own item bit ($7ED870). The table is the whole Tallon's, so the bits never change as regions
get built: an item whose room is not built yet has no spot (07l placed region D's; 07m region E's
and the Alcove's Space Jump: since then all 13 are in the ROM). Epic 09 (specs/09-itens-de-trava.md,
decision 3) adds the 7 lock items as rows 13-19, all at once so no bit moves: 09b placed the Ice, Wave and
Plasma beams and the Gravity Suit; 09d the Morph Ball and the Bombs; 09e the Power Bomb (and the X-Ray's power
bomb blocks: its `needs`).

spot = (x, y) block of the item in its room (an air block where Samus' body passes); needs = the on-foot
geometry items (tallon/rooms.py) its spot sits behind in its room (specs/09e: the X-Ray's power bomb hut;
validate.check_item_geometry: with them it is picked up from every door, without any one of them it is not); round = the
round (specs/09f, epic 09 decision 3: round 0 = the arrival with the Power Beam, round k = with the items of rounds
0..k-1; tallon/rooms.py FIRST_ROUND) at which it is first reachable from the gunship, declared here and checked by
tools/validate.py (check_tallon_rounds walks the rounds collecting the items). Until 09f it was a hypothetical tier
(TIERS): since 09d every item was in tier 0, and the comments below keep that history.
"""
from __future__ import annotations

from dataclasses import dataclass

from .rooms import (BOMBS, CHARGE, GRAPPLE, GRAVITY, ICE, MISSILE, MORPH, PLASMA, POWER_BOMB, SPACE_JUMP, SUPER, VARIA, WAVE,
                    XRAY)

# visible item PLMs ($84): base $EED7 + 4 * SM item number (research/sm_room_format.md section 5)
MISSILE_TANK, ENERGY_TANK, SPACE_JUMP_BOOTS, XRAY_SCOPE = 0xEEDB, 0xEED7, 0xEF1B, 0xEF0F
# the lock items (epic 09, decision 1; headers read in $84, setup $EE64 for the four of 09b)
ICE_BEAM, WAVE_BEAM, GRAVITY_SUIT, PLASMA_BEAM = 0xEEEF, 0xEEFB, 0xEF0B, 0xEF13
MORPH_BALL, BOMB_ITEM, POWER_BOMB_ITEM = 0xEF23, 0xEEE7, 0xEEE3
# specs/12g: the Chozo's two new items (headers read in $84: setup $EE64, as the Ice Beam's and the Gravity Suit's)
CHARGE_BEAM, VARIA_SUIT = 0xEEEB, 0xEF07
# specs/18l: the Super Missile (SM item 2: PLM $EED7 + 4 * 2; header read in $84, setup $EE57 as the Missile and Power Bomb
# packs': 5 super missiles of capacity and ammunition, the HUD's super icon)
SUPER_MISSILE_TANK = 0xEEDF
# specs/19f: the Grapple Beam (SM item 16: PLM $EED7 + 4 * 16 = $EF17; header read in $84: setup $EE64, instructions $E366, as the
# X-Ray's and the beams'): the equipment bit $4000 of $09A4, the HUD's grapple icon; one point of the ending's percentage
GRAPPLE_BEAM = 0xEF17
KIND_NAME = {MISSILE_TANK: "Missile Expansion", ENERGY_TANK: "Energy Tank",
             SPACE_JUMP_BOOTS: "Space Jump", XRAY_SCOPE: "X-Ray",
             ICE_BEAM: "Ice Beam", WAVE_BEAM: "Wave Beam", GRAVITY_SUIT: "Gravity Suit", PLASMA_BEAM: "Plasma Beam",
             MORPH_BALL: "Morph Ball", BOMB_ITEM: "Bombs", POWER_BOMB_ITEM: "Power Bomb",
             CHARGE_BEAM: "Charge Beam", VARIA_SUIT: "Varia Suit", SUPER_MISSILE_TANK: "Super Missile",
             GRAPPLE_BEAM: "Grapple Beam"}
# what each item adds to the progression walk (gate items of tallon/rooms.py); an E-tank opens nothing;
# specs/09d: the Morph Ball gives the reach model's ball
GRANTS = {MISSILE_TANK: frozenset({MISSILE}), ENERGY_TANK: frozenset(),
          SPACE_JUMP_BOOTS: frozenset({SPACE_JUMP}), XRAY_SCOPE: frozenset({XRAY}),
          ICE_BEAM: frozenset({ICE}), WAVE_BEAM: frozenset({WAVE}), GRAVITY_SUIT: frozenset({GRAVITY}),
          PLASMA_BEAM: frozenset({PLASMA}), MORPH_BALL: frozenset({MORPH}), BOMB_ITEM: frozenset({BOMBS}),
          POWER_BOMB_ITEM: frozenset({POWER_BOMB}), CHARGE_BEAM: frozenset({CHARGE}), VARIA_SUIT: frozenset({VARIA}),
          SUPER_MISSILE_TANK: frozenset({SUPER}),   # specs/18l: opens nothing (no gate has SUPER)
          GRAPPLE_BEAM: frozenset({GRAPPLE})}   # specs/19f: opens nothing (no gate has GRAPPLE)
# item bits of the vanilla item PLMs are 0-154 (validate.check_tallon_items reads the base ROM);
# the Tallon's start at $A0, one per row of ITEMS, in order
ITEM_BIT0 = 0xA0
ITEM_BITS = 0x200   # $7ED870-$7ED8AF


@dataclass(frozen=True)
class Item:
    room: str
    prime: int                          # Prime room index (P#) of the pickup
    kind: int                           # item PLM id
    spot: tuple[int, int] | None = None   # block in the room; None = room not built yet
    round: int | None = None            # declared first round (None while there is no spot; specs/09f)
    needs: frozenset[str] = frozenset()   # geometry items its spot is behind (specs/09e)


ITEMS = [
    # region A. Landing Site: in Prime low on the west side, behind a Morph Ball tunnel; there is
    # no Morph Ball here, so it lies where Samus walks (deviation, specs/07h): in the pond bed on
    # the way from the ship to the Canyon Cavern door. The first missile opens the red doors.
    Item("tallon_landing_site", 0, MISSILE_TANK, (21, 43), 0),
    # Alcove (07m): Prime's Space Jump Boots on the floor in the middle, 9 m under the door; reached
    # through the Gully (bomb walls: tier 1), it gives the Space Jump in the same tier
    Item("tallon_alcove", 4, SPACE_JUMP_BOOTS, (40, 27), 2),
    # region C
    Item("tallon_crash_site", 8, MISSILE_TANK, (25, 59), 1),  # pond bed under the wreck's nose
    Item("tallon_overgrown_cavern", 13, MISSILE_TANK, (16, 9), 4),   # 09b: 3 -> 1 (the Ice is real)
    # high, on the Arbor Chamber shelf; 07m: tier 1, as the Alcove's Space Jump comes in tier 1
    Item("tallon_root_cave", 15, MISSILE_TANK, (6, 9), 3),
    Item("tallon_tunnel_b", 19, MISSILE_TANK, (23, 7), 1),    # on the step in the middle
    Item("tallon_arbor_chamber", 20, MISSILE_TANK, (20, 9), 6),   # 07l: 4 -> 5; 07m: 5 -> 6; 09b: 6 -> 1
    # region D (07l), all with the Gravity Suit tier (09b: 4 -> 1, the suit and the beams are real
    # items now). Cargo Lift: in Prime at the height of the
    # Reactor Access door, so on the upper deck over the shaft; Biohazard: low on the west side, in
    # the pocket between the containment tanks; Hydro Access: in Prime high in the middle of the
    # Morph Ball maze (no Morph Ball here: deviation), on the shelf over the tunnel floor
    Item("tallon_cargo_lift", 27, ENERGY_TANK, (38, 25), 5),
    Item("tallon_biohazard", 30, MISSILE_TANK, (11, 25), 5),
    Item("tallon_hydro_access", 35, ENERGY_TANK, (22, 21), 5),
    # region E (07m). Great Tree Chamber: on the floor in the middle (Prime: same); Life Grove Tunnel:
    # in the middle at the doors' height (Prime: same); Life Grove: the X-Ray Visor on the grove's
    # floor, 20 blocks under and 40 from the door (Prime: 13 m under and 54 m from it, inside the walls
    # the Power Bombs break). 09a: tier 5 -> 4 (the Life Grove's gate is the ice door alone); 09b: 4 -> 1;
    # specs/09e: inside a hut of power bomb blocks (tallon/layouts.py), so it needs the Power Bomb (in the ball)
    Item("tallon_great_tree_chamber", 37, MISSILE_TANK, (24, 9), 5),
    Item("tallon_life_grove_tunnel", 39, MISSILE_TANK, (16, 9), 5),
    Item("tallon_life_grove", 42, XRAY_SCOPE, (40, 29), 6, frozenset({MORPH, POWER_BOMB})),
    # the lock items (epic 09, decision 3: each decorative elevator keeps the item "that would come from
    # there"); `prime` = the room's P# (they are not Tallon pickups in Prime). Ice: on the Arbor Chamber
    # door's shelf, by the missile (Space Jump only; the orange door asking for another beam is right
    # there); Wave: on the Magmoor East floor (Phendrana is reached through Magmoor); Gravity Suit: on
    # the Chozo East floor, down the steps (the dead end of region C's ice branch, before region D's
    # water); Plasma: on the Chozo South floor (region E's dead end)
    Item("tallon_root_cave", 15, ICE_BEAM, (4, 9), 3),
    Item("tallon_transport_magmoor_east", 23, WAVE_BEAM, (9, 25), 1),
    Item("tallon_transport_chozo_east", 22, GRAVITY_SUIT, (10, 21), 4),   # specs/12e: (12, 25) -> on the step by the pad
    Item("tallon_transport_chozo_south", 41, PLASMA_BEAM, (6, 25), 5),
    # specs/09d: Morph Ball on the Chozo West's elevator platform (Prime's first elevator, to the Chozo
    # Ruins: the ball early, as in Prime); specs/12e: the platform rides now, so the ball lies on the floor beside it,
    # east of it, at the foot of the steps from the door (reached before the platform); Bombs on the Artifact Temple floor between the totems (a Chozo
    # item in the Chozo temple, behind the Temple Security's red door). specs/09e: the Power Bomb on the Mines East
    # floor (Prime's Power Bombs come from the Phazon Mines; the same spot as the Plasma in the Chozo South)
    Item("tallon_transport_chozo_west", 14, MORPH_BALL, (12, 25), 0),   # specs/12e: (8, 25) -> the floor east of the pad, at the foot of the steps
    Item("tallon_artifact_temple", 16, BOMB_ITEM, (13, 53), 1),
    Item("tallon_transport_mines_east", 43, POWER_BOMB_ITEM, (6, 25), 5),
]
BITS = {n: ITEM_BIT0 + n for n in range(len(ITEMS))}   # item bit of ITEMS[n]


# The Gravity Suit's cutscene (GravitySuitPickup, $91:D5BA, sm_91.c:1320) puts Samus at the middle of the
# screen, layer1 + (120, 136): where a vanilla one-screen room has its floor. In the Tallon's transport
# rooms (one screen wide, floor at row 26) that is inside the wall and the floor, and she is stuck there
# for good (emulator, specs/09b). The patch branches over the 26 bytes that set her position, so she
# stays where she picked it up (the light beam stays at the middle of the screen: looks only).
GRAVITY_POS = 0x91D64E
GRAVITY_POS_VANILLA = bytes.fromhex("AD1109186978008DF60A8D100BAD1509186988008DFA0A8D140B")
GRAVITY_POS_PATCH = bytes([0x80, len(GRAVITY_POS_VANILLA) - 2])   # BRA to $91:D668 (the sound, as before)


def gravity_patch(base) -> tuple[int, bytes]:
    """(address, bytes) of the Gravity Suit cutscene patch, from the base ROM: the vanilla position code
    with its first 2 bytes turned into a branch over it; error if the vanilla bytes differ."""
    got = base.read(GRAVITY_POS, len(GRAVITY_POS_VANILLA))
    if got != GRAVITY_POS_VANILLA:
        raise RuntimeError(f"cena da Gravity Suit: ${GRAVITY_POS:06X} = {got.hex()}, esperado {GRAVITY_POS_VANILLA.hex()}")
    return GRAVITY_POS, GRAVITY_POS_PATCH + GRAVITY_POS_VANILLA[2:]


# specs/12g: the Varia Suit's cutscene (VariaSuitPickup, $91:D4E4, sm_91.c:1282) has the same 26 bytes at $91:D576 (read):
# the same branch over them, so she stays where she picks it up (in the Chozo's rooms the middle of the screen may be rock)
VARIA_POS = 0x91D576


def varia_patch(base) -> tuple[int, bytes]:
    """(address, bytes) of the Varia Suit cutscene patch (gravity_patch's, at VARIA_POS)."""
    got = base.read(VARIA_POS, len(GRAVITY_POS_VANILLA))
    if got != GRAVITY_POS_VANILLA:
        raise RuntimeError(f"cena da Varia Suit: ${VARIA_POS:06X} = {got.hex()}, esperado {GRAVITY_POS_VANILLA.hex()}")
    return VARIA_POS, GRAVITY_POS_PATCH + GRAVITY_POS_VANILLA[2:]


def placed(built: set[str]) -> list[tuple[int, Item]]:
    """(index, item) of the items with a spot; a spot in a room that is not built is an error."""
    out = []
    for n, it in enumerate(ITEMS):
        if it.spot is None:
            continue
        if it.room not in built:
            raise ValueError(f"item {n} ({KIND_NAME[it.kind]}) em {it.room}, sala fora do build")
        out.append((n, it))
    return out

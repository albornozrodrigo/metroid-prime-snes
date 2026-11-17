"""Items of Phendrana Drifts (specs/18f-regiao-a-phendrana.md; epic 18, user decision 3: items as in the Chozo and the Magmoor).

The user's decision 3 (epic 18): Prime's Phendrana pickups that have an SM item: the 9 Missile Expansions, the 3 Energy Tanks, the
2 Power Bomb Expansions (never before round 6), the Super Missile (the SM's, in the Observatory), and a missile where Prime has the
Wave Beam and the Gravity Suit (already the Tallon's, specs/09b); nothing where Prime has the Boost Ball, the Spider Ball, the
Thermal Visor (no SM item) or an artifact (out). Rows are added region by region (18f: region A, $DA-$DD; 18h: the Chapel's, $DE;
18i: region B, $DF-$E1; 18j: region C, $E2-$E3; 18l: region D, $E4-$E6; 18m: region E, $E7-$EA: the 17); the bits never move once
given: ITEM_BIT0 + the row's index, after the Magmoor's $D3-$D9. Item, KIND_NAME and GRANTS are the Tallon's (the progression walk
is one, validate.world_rounds). spot = (x, y) block in the room; round = the round of the walk of the four areas together (round
0 = the arrival with the Power Beam) at which it is first picked up; needs = the on-foot geometry items its spot sits behind
(validate.check_item_geometry).
"""
from __future__ import annotations

from tallon.items import ENERGY_TANK, GRANTS, KIND_NAME, MISSILE_TANK, POWER_BOMB_ITEM, SUPER_MISSILE_TANK, Item  # noqa: F401
from tallon.rooms import BOMBS, MORPH, PLASMA, SPACE_JUMP

from .layouts import (AETHER_ETANK, AETHER_MISSILE, CHAPEL_ALTAR_MISSILE, COURT_ETANK, FROST_MISSILE, GRAV_HIGH_MISSILE,
                      GRAV_LOW_MISSILE, HYDRA_MISSILE, IRW_PB, OBS_SUPER, QM_MISSILE, RUINS_EAST_NICHE_MISSILE,
                      RUINS_EAST_TOWER_MISSILE, SEC_PB, SHORE_LAKE_MISSILE, SHORE_TOWER_MISSILE, TA_ETANK)

ITEM_BIT0 = 0xDA   # the Tallon's are $A0-$B3, the Chozo's $B4-$D2, the Magmoor's $D3-$D9; vanilla items use 0-$9A

ITEMS = [
    # region A (specs/18f; bits $DA-$DD). Prime's pickups there (epic 18, the item table): the 2 Missile Expansions of the
    # Phendrana Shorelines (P2) and the 2 of the Ice Ruins East (P10); the Chapel of the Elders' Wave Beam (P14, after the
    # Sheegoth: a missile, the arena's prize) is specs/18h's row below; the Chozo Ice Temple's artifact (out) is not here.
    #  - Shorelines: at the top of the tower's Spider Ball track -> the top of the ruined tower (layouts.py SHORE_TOWER), a Space
    #    Jump ledge (round 3: Phendrana's; needs = the Space Jump: validate.check_item_geometry proves the ledge, which the round
    #    alone cannot: the Space Jump is round 2's); the other on the frozen lake -> in the lake's hole (SHORE_HOLE), on foot;
    #  - Ice Ruins East: on a Spider Ball track -> the top of the tower against the east wall (RUINS_EAST_TOWER), a Space Jump
    #    ledge; the other in a block of ice (no beam-only trigger in Prime's data) -> an ice niche at the floor, on foot.
    Item("phendrana_shorelines", 2, MISSILE_TANK, SHORE_TOWER_MISSILE, 3, frozenset({SPACE_JUMP})),
    Item("phendrana_shorelines", 2, MISSILE_TANK, SHORE_LAKE_MISSILE, 3),
    Item("phendrana_ice_ruins_east", 10, MISSILE_TANK, RUINS_EAST_TOWER_MISSILE, 3, frozenset({SPACE_JUMP})),
    Item("phendrana_ice_ruins_east", 10, MISSILE_TANK, RUINS_EAST_NICHE_MISSILE, 3),
    # specs/18h (bit $DE): the Chapel of the Elders' Wave Beam (after the Sheegoth) -> a missile (the Wave is the Tallon's), the
    # Sheegoth's arena's prize (tools/chozo/bosses.py ARENAS): it appears on the altar when the fight is won (round 3: the
    # fight takes missiles, the walk's boss lock)
    Item("phendrana_chapel_of_the_elders", 14, MISSILE_TANK, CHAPEL_ALTAR_MISSILE, 3),
    # region B (specs/18i; bits $DF-$E1). Prime's pickups there (epic 18, the item table): the Ice Ruins West's Power Bomb
    # Expansion (P9, in ice only the Plasma Beam melts), the Ruined Courtyard's Energy Tank (P15, Prime's bomb slot puzzle) and
    # the Research Lab Hydra's Missile Expansion (P25); the Phendrana Canyon's Boost Ball (P16: no SM item) is not here.
    #  - Ice Ruins West: in a niche of the west cliff's face shut by a plasma cap (layouts.py IRW_CAP: the epic's technical
    #    decision 3); needs = the Plasma Beam (round 5's, the Tallon's Chozo South: picked up in round 6, never before: the epic's
    #    rule for the power bomb expansions, which turn the Power Bombs on);
    #  - Ruined Courtyard: in the west cliff's chamber behind a 1-row tunnel shut by a bomb block (COURT_BOMB: the bomb slot);
    #    needs = the Morph Ball and the Bombs (round 3: Phendrana's);
    #  - Research Lab Hydra: on the lower lab's floor (on foot, round 3).
    Item("phendrana_ice_ruins_west", 9, POWER_BOMB_ITEM, IRW_PB, 6, frozenset({PLASMA})),
    Item("phendrana_ruined_courtyard", 15, ENERGY_TANK, COURT_ETANK, 3, frozenset({MORPH, BOMBS})),
    Item("phendrana_research_lab_hydra", 25, MISSILE_TANK, HYDRA_MISSILE, 3),
    # region C (specs/18j; bits $E2-$E3). Prime's pickups there (epic 18, the item table): the Quarantine Monitor's Missile
    # Expansion (P27) and the Transport Access' Energy Tank (P31, in ice only the Plasma Beam melts); the Quarantine Cave's Spider
    # Ball (P24, the Thardus' prize: no SM item) is not here.
    #  - Quarantine Monitor: at the lookout's west end, past the Morph Ball tunnel of its door (the gate of the door, not of the
    #    item: round 3);
    #  - Transport Access: in the ice pillar's niche shut by a plasma cap (layouts.py TA_CAP); needs = the Plasma Beam (round 6,
    #    the Ice Ruins West's rule).
    Item("phendrana_quarantine_monitor", 27, MISSILE_TANK, QM_MISSILE, 3),
    Item("phendrana_transport_access", 31, ENERGY_TANK, TA_ETANK, 6, frozenset({PLASMA})),
    # region D (specs/18l; bits $E4-$E6). Prime's pickups there (epic 18, the item table): the Observatory's Super Missile (P30,
    # at the top, after the bomb slots wake the projector) and the Research Lab Aether's Energy Tank and Missile Expansion (P51);
    # the Research Core's Thermal Visor (P40: no SM item) is not here.
    #  - Observatory: the SM's Super Missile (the user's decision 3: the same item; 5 super missiles), in the projector's chamber
    #    on the east cliff behind the bomb block (layouts.py OBS_BOMB: the bomb slot); needs = the Morph Ball and the Bombs
    #    (round 3: Phendrana's);
    #  - Research Lab Aether: the Energy Tank on the Metroid's empty tank in the lower lab, the missile in its west corner (on
    #    foot, round 3).
    Item("phendrana_observatory", 30, SUPER_MISSILE_TANK, OBS_SUPER, 3, frozenset({MORPH, BOMBS})),
    Item("phendrana_research_lab_aether", 51, ENERGY_TANK, AETHER_ETANK, 3),
    Item("phendrana_research_lab_aether", 51, MISSILE_TANK, AETHER_MISSILE, 3),
    # region E (specs/18m; bits $E7-$EA). Prime's pickups there (epic 18, the item table): the Frost Cave's Missile Expansion
    # (P41, under the frozen lake), the Gravity Chamber's Gravity Suit and Missile Expansion (P53) and the Security Cave's Power
    # Bomb Expansion (P55); the Storage Cave's artifact (P54) is not here.
    #  - Frost Cave: in the dry lake between the two zigzags (layouts.py FROST_LAKE; the lake is dry, the user's decision 5), on
    #    foot (round 4: region E is behind the ice doors);
    #  - Gravity Chamber (flooded): the Gravity Suit -> a missile (the suit is the Tallon's, decision 3) on the chamber's floor,
    #    walked without the suit (round 4); the Missile Expansion on the ledge against the east wall (Prime's grapple point ->
    #    a Space Jump ledge, FEATURE_GEOMETRY), needs = the Space Jump, which under water works only with the Gravity Suit
    #    (picked up in round 4): round 5;
    #  - Security Cave: at the cave's east end, past the door's power bomb blocks (the gate of the door: round 6, the epic's
    #    rule for the power bomb expansions).
    Item("phendrana_frost_cave", 41, MISSILE_TANK, FROST_MISSILE, 4),
    Item("phendrana_gravity_chamber", 53, MISSILE_TANK, GRAV_LOW_MISSILE, 4),
    Item("phendrana_gravity_chamber", 53, MISSILE_TANK, GRAV_HIGH_MISSILE, 5, frozenset({SPACE_JUMP})),
    Item("phendrana_security_cave", 55, POWER_BOMB_ITEM, SEC_PB, 6),
]
BITS = {n: ITEM_BIT0 + n for n in range(len(ITEMS))}   # item bit of ITEMS[n]


def placed(built: set[str]) -> list[tuple[int, Item]]:
    """(index, item) of the items with a spot; a spot in a room that is not built is an error."""
    out = []
    for n, it in enumerate(ITEMS):
        if it.spot is None:
            continue
        if it.room not in built:
            raise ValueError(f"item de Phendrana {n} ({KIND_NAME[it.kind]}) em {it.room}, sala fora do build")
        out.append((n, it))
    return out

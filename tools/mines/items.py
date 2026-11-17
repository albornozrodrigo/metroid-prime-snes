"""Items of the Phazon Mines (specs/19f-regiao-a-mines.md; epic 19, user decision 3a: items as in the other worlds, and the SM's
Grapple Beam).

The user's decision 3a (epic 19): Prime's Mines pickups that have an SM item: the 9 Missile Expansions, the 2 Energy Tanks, a missile
where Prime has the Power Bomb (the Tallon's since specs/09e) and the SM's Grapple Beam where Prime has its Grapple Beam (the Storage
Depot B; no gate needs it: validate.check_no_grapple_locks); nothing where Prime has the Flamethrower, the Phazon Suit or an artifact.
13 items, the bits $EB-$F7. Rows are added region by region (19f: region A, $EB-$EE; 19i: region B, $EF-$F2; 19j: region C, $F3-$F4;
19l: region D, $F5-$F7); the bits never move once given: ITEM_BIT0 + the
row's index, after Phendrana's $DA-$EA. Item, KIND_NAME and GRANTS are the Tallon's (the progression walk is one,
validate.world_rounds). spot = (x, y) block in the room; round = the round of the walk of the five areas together (round 0 = the
arrival with the Power Beam) at which it is first picked up; needs = the on-foot geometry items its spot sits behind
(validate.check_item_geometry).
"""
from __future__ import annotations

from tallon.items import ENERGY_TANK, GRANTS, GRAPPLE_BEAM, KIND_NAME, MISSILE_TANK, Item  # noqa: F401
from tallon.rooms import BOMBS, MORPH, POWER_BOMB, SPACE_JUMP

from .layouts import (CD_MISSILE, ECA_MISSILE, ER_MISSILE, FHAC_MISSILE, FHB_MISSILE, MQ_MISSILE, MQA_MISSILE, MQB_MISSILE,
                      PCA_ETANK, PPC_MISSILE, SAA_MISSILE, SDB_GRAPPLE, VS_ETANK)

ITEM_BIT0 = 0xEB   # the Tallon's are $A0-$B3, the Chozo's $B4-$D2, the Magmoor's $D3-$D9, Phendrana's $DA-$EA

ITEMS = [
    # region A (specs/19f; bits $EB-$EE). Prime's pickups there (epic 19, the item table): the Missile Expansions of the Main
    # Quarry (P2), the Security Access A (P5) and the Elite Research (P13), the Grapple Beam of the Storage Depot B (P9); the
    # Storage Depot A's Flamethrower (P12, behind the plasma door) and the Elite Research's artifact (the Phazon Elite's) are not
    # here (no SM item).
    #  - Main Quarry: on the crane, up its Spider Ball track and grapple point -> the top of the crane tower (layouts.py
    #    MQ_TOWER), a Space Jump ledge (round 5: the Mines'; needs = the Space Jump: validate.check_item_geometry proves the
    #    ledge, which the round alone cannot: the Space Jump is round 2's);
    #  - Security Access A: behind the Bendezium wall -> in the niche under the floor roofed by power bomb blocks (SAA_NICHE);
    #    needs = the Morph Ball and the Power Bomb (round 5's: picked up in round 6);
    #  - Storage Depot B: the SM's Grapple Beam on the store room's floor (on foot, round 5);
    #  - Elite Research: in the lab's west corner (on foot, round 5; no bomb slot in Prime's data for it).
    Item("mines_main_quarry", 2, MISSILE_TANK, MQ_MISSILE, 5, frozenset({SPACE_JUMP})),
    Item("mines_security_access_a", 5, MISSILE_TANK, SAA_MISSILE, 6, frozenset({MORPH, POWER_BOMB})),
    Item("mines_storage_depot_b", 9, GRAPPLE_BEAM, SDB_GRAPPLE, 5),
    Item("mines_elite_research", 13, MISSILE_TANK, ER_MISSILE, 5),
    # region B (specs/19i; bits $EF-$F2). Prime's pickups there: the Missile Expansions of the Elite Control Access (P15) and of
    # the Metroid Quarantine A (P32), the Energy Tank of the Ventilation Shaft (P18), the Power Bomb of the Central Dynamo (P27:
    # the game's Power Bomb is the Tallon's since specs/09e, so a missile here, decision 3a).
    #  - Elite Control Access: on the corridor's floor past the catwalk (layouts.py ECA_CATWALK), on foot (round 5);
    #  - Ventilation Shaft: behind the grating only the Power Bomb breaks (uncertain) -> in the duct under the floor roofed by
    #    power bomb blocks (VS_DUCT); needs = the Morph Ball and the Power Bomb (round 6);
    #  - Central Dynamo: in the Morph Ball maze -> in the chamber at the end of the tunnel from the floor's pit, behind a bomb block
    #    (CD_TUNNEL); needs = the Morph Ball and the Bombs (round 5; rooms.MAZES);
    #  - Metroid Quarantine A: behind the "Powerbomb Wall" -> in the east chamber behind the power bomb wall (MQA_WALL); needs =
    #    the Morph Ball and the Power Bomb (round 6).
    Item("mines_elite_control_access", 15, MISSILE_TANK, ECA_MISSILE, 5),
    Item("mines_ventilation_shaft", 18, ENERGY_TANK, VS_ETANK, 6, frozenset({MORPH, POWER_BOMB})),
    Item("mines_central_dynamo", 27, MISSILE_TANK, CD_MISSILE, 5, frozenset({MORPH, BOMBS})),
    Item("mines_metroid_quarantine_a", 32, MISSILE_TANK, MQA_MISSILE, 6, frozenset({MORPH, POWER_BOMB})),
    # region C (specs/19j; bits $F3-$F4). Prime's pickups there: the Missile Expansion of the Phazon Processing Center (P19) and the
    # Energy Tank of the Processing Center Access (P22); the Elite Quarters' Phazon Suit (the Omega Pirate's) is not here.
    #  - Phazon Processing Center: behind the Bendezium wall (uncertain where in Prime) -> in the pit under the floor roofed by
    #    power bomb blocks (layouts.py PPC_NICHE); needs = the Morph Ball and the Power Bomb (round 6);
    #  - Processing Center Access: on the corridor's floor between its plasma doors (round 6: the Plasma Beam is round 5's).
    Item("mines_phazon_processing_center", 19, MISSILE_TANK, PPC_MISSILE, 6, frozenset({MORPH, POWER_BOMB})),
    Item("mines_processing_center_access", 22, ENERGY_TANK, PCA_ETANK, 6),
    # region D (specs/19l; bits $F5-$F7). Prime's pickups there: the Missile Expansions of the Metroid Quarantine B (P31), the Fungal
    # Hall B (P36) and the Fungal Hall Access (P40); the Phazon Mining Tunnel's artifact is not here. All behind plasma doors
    # (round 6).
    #  - Metroid Quarantine B: up its Spider Ball track and grapple point -> on top of the column in the west (layouts.py
    #    MQB_COLUMN), a Space Jump ledge (needs = the Space Jump, as the Main Quarry's);
    #  - Fungal Hall B: on the cavern's floor (on foot; Prime's X-Ray floor is plain here);
    #  - Fungal Hall Access: on the shaft's floor past the pirate's catwalk (on foot).
    Item("mines_metroid_quarantine_b", 31, MISSILE_TANK, MQB_MISSILE, 6, frozenset({SPACE_JUMP})),
    Item("mines_fungal_hall_b", 36, MISSILE_TANK, FHB_MISSILE, 6),
    Item("mines_fungal_hall_access", 40, MISSILE_TANK, FHAC_MISSILE, 6),
]
BITS = {n: ITEM_BIT0 + n for n in range(len(ITEMS))}   # item bit of ITEMS[n]


def placed(built: set[str]) -> list[tuple[int, Item]]:
    """(index, item) of the items with a spot; a spot in a room that is not built is an error."""
    out = []
    for n, it in enumerate(ITEMS):
        if it.spot is None:
            continue
        if it.room not in built:
            raise ValueError(f"item da Mines {n} ({KIND_NAME[it.kind]}) em {it.room}, sala fora do build")
        out.append((n, it))
    return out

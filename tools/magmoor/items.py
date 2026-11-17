"""Items of the Magmoor Caverns (specs/17f-regiao-a-magmoor.md; epic 17, user decision 2: items as in the Chozo).

The user's decision 2 (epic 17): Prime's Magmoor pickups that have an SM item, as the Chozo did (tools/chozo/items.py): the 3
Missile Expansions, the 2 Energy Tanks and the Power Bomb Expansion (behind its power bomb wall, never before round 6), and a
missile where Prime has the Plasma Beam (already the Tallon's, specs/09b); nothing where Prime has the Ice Spreader (no SM item)
or an artifact (out). Rows are added region by region (17f: region A, $D3-$D4); the bits never move once given: ITEM_BIT0 + the
row's index, after the Chozo's $B4-$D2 (17h: region B, $D5-$D7; 17i: region C, $D8-$D9). Item, KIND_NAME and GRANTS are the Tallon's (the progression walk is one,
validate.world_rounds). spot = (x, y) block in the room; round = the round of the walk of the three areas together (round 0 =
the arrival with the Power Beam) at which it is first picked up; needs = the on-foot geometry items its spot sits behind
(validate.check_item_geometry).
"""
from __future__ import annotations

from tallon.items import ENERGY_TANK, GRANTS, KIND_NAME, MISSILE_TANK, POWER_BOMB_ITEM, Item  # noqa: F401
from tallon.rooms import BOMBS, MORPH, POWER_BOMB, SPACE_JUMP

ITEM_BIT0 = 0xD3   # the Tallon's are $A0-$B3, the Chozo's $B4-$D2 (31 rows); vanilla items use 0-$9A (validate.check_tallon_items)

ITEMS = [
    # region A (specs/17f; bits $D3-$D4). Prime's pickups there (epic 17, the item table): the Missile Expansions of the
    # Triclops Pit (P6) and of the Storage Cavern (P8); the Lava Lake's artifact (Nature) is out.
    #  - Triclops Pit: in a hollow pillar Prime reaches with the Space Jump -> the hollow of the rock column hanging over the
    #    pit (tools/magmoor/layouts.py TRICLOPS_HOLLOW), a Space Jump ledge (round 3: the room is hot, the Varia Suit's round;
    #    needs = the Space Jump: validate.check_item_geometry proves the ledge, which the round alone cannot here);
    #  - Storage Cavern: on the floor at the cave's far end (round 3: behind the hot Triclops Pit).
    Item("magmoor_triclops_pit", 6, MISSILE_TANK, (47, 7), 3, frozenset({SPACE_JUMP})),
    Item("magmoor_storage_cavern", 8, MISSILE_TANK, (5, 11), 3),
    # region B (specs/17h; bits $D5-$D7). Prime's pickups there (epic 17, the item table): the Energy Tank of the Transport
    # Tunnel A (P10), the Missile Expansion and the Power Bomb Expansion of the Fiery Shores (P14); the Shore Tunnel's Ice
    # Spreader (no SM item) and the Warrior Shrine's artifact (Strength) are out (user decision 2).
    #  - Transport Tunnel A: in a Morph Ball tunnel under the bridge in Prime -> the far end of the 1-row tunnel at the foot of
    #    the dais, shut by a bomb block (layouts.py TTA_TANK; round 3: the room is hot; needs the Morph Ball and the Bombs);
    #  - Fiery Shores: the missile at the end of the Warrior Shrine's tunnel -> the pocket of the L0 door under the ceiling
    #    door's platform (SHORES_MISSILE), the expansion on its Morph Ball track -> in the tunnel out of it (SHORES_EXPANSION):
    #    both behind power bomb blocks on either side (rooms.py GATES), round 6 (the Power Bomb is the Mines East's, round 5),
    #    never before: an SM power bomb pack turns the power bombs on (epic 17).
    Item("magmoor_transport_tunnel_a", 10, ENERGY_TANK, (13, 9), 3, frozenset({MORPH, BOMBS})),
    Item("magmoor_fiery_shores", 14, MISSILE_TANK, (5, 9), 6, frozenset({MORPH, POWER_BOMB})),
    Item("magmoor_fiery_shores", 14, POWER_BOMB_ITEM, (14, 9), 6, frozenset({MORPH, POWER_BOMB})),
    # region C (specs/17i; bits $D8-$D9). Prime's pickups there (epic 17, the item table): the Plasma Beam of the Plasma
    # Processing (P21; already the Tallon's, specs/09b) and the Energy Tank of the Magmoor Workstation (P23).
    #  - Plasma Processing: a Missile Expansion in the Plasma Beam's place (user decision 2), on the floor at the hall's west
    #    end (layouts.py PP_MISSILE); round 4: behind the Geothermal Core's ice door (the Ice Beam, round 3's) and its bomb
    #    block (rooms.py GATES);
    #  - Workstation: on the platform Prime raises with the Wave Beam's panels -> a ledge high in the west (WS_TANK), a Space
    #    Jump ledge (round 3: the Space Jump is round 2's; needs = the Space Jump, validate.check_item_geometry).
    Item("magmoor_plasma_processing", 21, MISSILE_TANK, (5, 11), 4),
    Item("magmoor_workstation", 23, ENERGY_TANK, (5, 7), 3, frozenset({SPACE_JUMP})),
]
BITS = {n: ITEM_BIT0 + n for n in range(len(ITEMS))}   # item bit of ITEMS[n]


def placed(built: set[str]) -> list[tuple[int, Item]]:
    """(index, item) of the items with a spot; a spot in a room that is not built is an error."""
    out = []
    for n, it in enumerate(ITEMS):
        if it.spot is None:
            continue
        if it.room not in built:
            raise ValueError(f"item da Magmoor {n} ({KIND_NAME[it.kind]}) em {it.room}, sala fora do build")
        out.append((n, it))
    return out

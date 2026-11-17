"""Items of the Chozo Ruins (specs/12f-regiao-a-chozo.md; epic 12, decision B).

Decision B: the Tallon stays as it is (its 20 items, tools/tallon/items.py); the Chozo gets Prime's Chozo pickups that have
no place in the game yet: the Charge Beam (Watery Hall), the Varia Suit (Sunchamber), the missiles (Prime's 19 Missile
Expansions and the Missile Launcher as one more), the 5 Energy Tanks and the Power Bomb expansion (Magma Pool); no artifacts
(no SM item), no Wavebuster (no SM item). Where Prime has the Morph Ball, the Bombs or the Ice Beam (already in the Tallon) a
missile goes (the Ruined Shrine's Morph Ball: decided, epic 12 table "12f").

Rows are added region by region (12f: region A; 12g: the Charge Beam and the Varia Suit; 12i: region B, $BD-$C2; 12j: region
C, $C3-$C7, and the Varia Suit's spot; 12k: region D, $C8-$CF, and the Charge Beam's spot; 12l: region E, $D0-$D2); the bits
never move once given: ITEM_BIT0 + the row's index, after the
Tallon's $A0-$B3 (tools/tallon/items.py). Item, KIND_NAME and GRANTS are the Tallon's (the progression walk is one,
validate.world_rounds). spot = (x, y) block in the room; round = the round of the walk of the Tallon and the Chozo together
(round 0 = the arrival with the Power Beam; the North elevator is in the Tallon's round 0) at which it is first picked up;
needs = the on-foot geometry items its spot sits behind (validate.check_item_geometry).
"""
from __future__ import annotations

from tallon.items import CHARGE_BEAM, ENERGY_TANK, GRANTS, ITEM_BITS, KIND_NAME, MISSILE_TANK, POWER_BOMB_ITEM, VARIA_SUIT, Item  # noqa: F401
from tallon.rooms import BOMBS, MORPH, POWER_BOMB

ITEM_BIT0 = 0xB4   # the Tallon's are $A0-$B3 (20 rows); vanilla items use 0-$9A (validate.check_tallon_items)

ITEMS = [
    # region A (specs/12f). Main Plaza (P2: 3 Missile Expansions and an Energy Tank in Prime):
    #  - "Half-Pipe" (Boost Ball in Prime): on the ledge over the middle of the courtyard, a Space Jump ledge;
    #  - "Grapple Ledge" (Grapple Beam): on the east ledge, a Space Jump ledge;
    #  - "Tree" (Super Missile): at the far end of the hollow trunk, behind power bomb blocks (the strongest blast there is;
    #    tools/chozo/layouts.py main_plaza; the blast sweeps it too: specs/13's touch fix makes that harmless);
    #  - "Locked Door" Energy Tank: on the ledge of the one-way door to the Plaza Access (from the Vault in Prime; a Space
    #    Jump ledge from the plaza: round 3 until specs/12i built region B, round 1 since: down the Plaza Access' floor door
    #    from the Vault, as in Prime).
    Item("chozo_main_plaza", 2, MISSILE_TANK, (36, 12), 3),
    Item("chozo_main_plaza", 2, MISSILE_TANK, (83, 13), 3),
    Item("chozo_main_plaza", 2, MISSILE_TANK, (68, 25), 6, frozenset({MORPH, POWER_BOMB})),
    Item("chozo_main_plaza", 2, ENERGY_TANK, (21, 5), 1),
    # Ruined Shrine (P9: the Morph Ball and 2 Missile Expansions in Prime):
    #  - the Morph Ball's spot on the bowl's floor (after the Plated Beetle in Prime): a missile (decision B);
    #  - "Half-Pipe" (Boost Ball): on the ledge over the bowl, a Space Jump ledge;
    #  - "Lower Tunnel" (Morph Ball and Bombs): at the end of the tunnel shut by a bomb block.
    Item("chozo_ruined_shrine", 9, MISSILE_TANK, (24, 12), 1),
    Item("chozo_ruined_shrine", 9, MISSILE_TANK, (24, 3), 3),
    Item("chozo_ruined_shrine", 9, MISSILE_TANK, (5, 12), 2, frozenset({MORPH, BOMBS})),
    # specs/12g: the Chozo's two new items, rows (and bits $BB, $BC) given now so they never move; no spot until their rooms
    # are built (the Watery Hall, region D, 12k; the Sunchamber, region C, 12j). In the test build (build.py --teste-12g,
    # chozo/testrooms.py) they lie in a test room.
    # specs/12k: the Charge Beam on its pedestal in the Watery Hall's upper gallery (layouts.WATERY_CHARGE), round 1: Prime's
    # rune gate (Scan Visor) and the pickup's cutscene are left out, a plain item (decision B)
    Item("chozo_watery_hall", 41, CHARGE_BEAM, (44, 8), 1),
    # specs/12j: the Varia Suit on the Sunchamber's pedestal, round 2; specs/14c: it appears on the floor of Flaahgra's pit
    # under the husk when the boss dies (layouts.SUNCHAMBER_VARIA; the arena's prize, tools/chozo/bosses.py ARENAS), round 2
    Item("chozo_sunchamber", 37, VARIA_SUIT, (8, 43), 2),
    # region B (specs/12i; bits $BD-$C2). Prime's pickups there and the lock in front of each (Prime's objects next to the
    # pickup, scratchpad s12i/objs_b.txt; knowledge where the data is not plain), mapped to the Tallon's items (decision B):
    #  - Vault (P11): the cage opened by bombs in its 3 Morph Ball slots ("BallTrigger - Suck In Ball", "Lock Destroyed")
    #    -> the cage's tunnel shut by a bomb block (Morph Ball and Bombs);
    #  - Ruined Nursery (P16): behind the "Wall Puzzle" (Morph Ball and Bombs, knowledge) -> the dais' tunnel, a bomb block;
    #  - Ruined Gallery (P28) "Tunnel" ("Enter Tunnel Trigger", "Ball Opening 1/2") -> a Morph Ball tunnel off the pool;
    #  - Ruined Gallery (P28) behind the missile wall ("POI_03_Mon up Missile Wall Scan") -> a bomb block (the SM has no
    #    block only missiles break: shot blocks break with any shot, the super missile block wants Super Missiles,
    #    $84:CF67; specs/12i, to confirm);
    #  - Transport Access North (P30) Energy Tank: in a cubby past a Morph Ball hole ("POI_0t ball hole") -> the pit's tunnel;
    #  - Hive Totem (P36) Missile Launcher (after the Hive Mecha: bosses later) -> a Missile Expansion (our missiles exist
    #    since the Tallon's first one, epic 07), on top of the totem.
    Item("chozo_vault", 11, MISSILE_TANK, (34, 12), 2, frozenset({MORPH, BOMBS})),
    Item("chozo_ruined_nursery", 16, MISSILE_TANK, (14, 12), 2, frozenset({MORPH, BOMBS})),
    Item("chozo_ruined_gallery", 28, MISSILE_TANK, (3, 14), 1, frozenset({MORPH})),
    Item("chozo_ruined_gallery", 28, MISSILE_TANK, (19, 14), 2, frozenset({MORPH, BOMBS})),
    Item("chozo_transport_access_north", 30, ENERGY_TANK, (28, 11), 1, frozenset({MORPH})),
    Item("chozo_hive_totem", 36, MISSILE_TANK, (23, 8), 0),
    # region C (specs/12j; bits $C3-$C7, and the Varia Suit's row above gets its spot). Prime's pickups there (objects
    # next to each Pickup, scratchpad s12j/objs_c.txt) and the lock in front of each, mapped to the Tallon's items:
    #  - Ruined Fountain (P8): the missile at the top of the Spider Ball track over the fountain ("SpiderBallWaypoint"s
    #    up to it) -> a Space Jump ledge over the basin (layouts.ruined_fountain);
    #  - Training Chamber (P12): the Energy Tank of the "Powerup Room", up the Spider Ball track past the bomb slots ->
    #    a Space Jump ledge over the hall (layouts.training_chamber; the bomb slots are its door's bomb block);
    #  - Training Chamber Access (P18): the missile at the end of a Morph Ball path ("Path Camera") -> a 1-row tunnel;
    #  - Magma Pool (P20): the Power Bomb expansion behind the "Grapple Powerbomb wall" -> a power bomb block (the grapple
    #    crossing is not kept: the room is one screen tall, the basin is crossed on foot; it is hot: the Varia Suit);
    #  - Gathering Hall (P32): the missile behind the "Bomb Gate" grate up on the east side -> a cage with a bomb block;
    #  - Sunchamber (P37): the Varia Suit (row 8 above), on the arena's floor after Flaahgra (the boss later, epic decision
    #    3: a plain item on its pedestal now); the Sunchamber's artifact (Wild) is out (decision 1).
    Item("chozo_ruined_fountain", 8, MISSILE_TANK, (16, 3), 3),
    Item("chozo_training_chamber", 12, ENERGY_TANK, (19, 3), 3),
    Item("chozo_training_chamber_access", 18, MISSILE_TANK, (18, 11), 2, frozenset({MORPH})),
    Item("chozo_magma_pool", 20, POWER_BOMB_ITEM, (6, 14), 6, frozenset({MORPH, POWER_BOMB})),
    Item("chozo_gathering_hall", 32, MISSILE_TANK, (40, 9), 2, frozenset({MORPH, BOMBS})),
    # region D (specs/12k; bits $C8-$CF, and the Charge Beam's row above gets its spot). Prime's pickups there (objects next
    # to each Pickup and the damage vulnerability of the DamageableTrigger in front of it, scratchpad s12k/objs_d.txt,
    # s12k/dtrig.out) and the lock, mapped to the Tallon's items:
    #  - Watery Hall Access (P38): the missile low in a niche behind a missile wall (its DamageableTrigger: only missiles,
    #    charged Power Beam shots and super missiles hurt it) -> a bomb block (12i's rule: the SM has no block only missiles
    #    break; layouts.watery_hall_access);
    #  - Watery Hall (P41): the missile at the far end of the pool down a Morph Ball path ("Path Camera", collision
    #    blockers) -> a 1-row tunnel off the dry pool;
    #  - Dynamo (P45): the missile behind a breakable wall ("Platform-breakable wall": missiles, charged shots) -> a bomb
    #    block; the missile at the top of the Spider Ball track ("POI_Spiderball Track") -> a Space Jump ledge;
    #  - Burn Dome (P48): the Bombs on the stand after the Incinerator Drone (the Tallon's: decision B, as the Ruined
    #    Shrine's Morph Ball, a missile there; the boss later); the missile past the "Breakable Block" (bombs and power bombs
    #    only) and a Morph Ball tunnel ("Trigger_mb tunnel") -> a tunnel shut by a bomb block;
    #  - Furnace (P49): the Energy Tank in the furnace's core, under the floor the bombs break ("dest floor") -> a tunnel
    #    shut by a bomb block under a pit; the missile at the top of the Spider Ball track over it -> a Space Jump ledge.
    Item("chozo_watery_hall_access", 38, MISSILE_TANK, (35, 12), 2, frozenset({MORPH, BOMBS})),
    Item("chozo_watery_hall", 41, MISSILE_TANK, (56, 28), 1, frozenset({MORPH})),
    Item("chozo_dynamo", 45, MISSILE_TANK, (13, 14), 2, frozenset({MORPH, BOMBS})),
    Item("chozo_dynamo", 45, MISSILE_TANK, (12, 3), 3),
    Item("chozo_burn_dome", 48, MISSILE_TANK, (23, 10), 1),
    Item("chozo_burn_dome", 48, MISSILE_TANK, (43, 12), 2, frozenset({MORPH, BOMBS})),
    Item("chozo_furnace", 49, ENERGY_TANK, (37, 29), 2, frozenset({MORPH, BOMBS})),
    Item("chozo_furnace", 49, MISSILE_TANK, (48, 3), 3),
    # region E (specs/12l; bits $D0-$D2). Prime's pickups there (objects next to each Pickup and the scripts, scratchpad
    # s12l/objs_e.txt, s12l/conns52.txt) and the lock, mapped to the Tallon's items:
    #  - Hall of the Elders (P52): the Energy Tank in the alcove under the floor where the statue's "Down Launch" drops the
    #    ball (its white bomb slot) -> a tunnel shut by a bomb block under a pit (layouts.hall_of_the_elders; the slot's
    #    white membrane, Ice in Prime's colours, is left out: the bomb slot stays);
    #  - Crossway (P53): a Missile Expansion (its object is named "P_Missile_Launcher": one of the epic's 19) high over the piston the two
    #    bomb slots and the cracked plaque (Super Missiles) work, up the Spider Ball tracks -> a hut of power bomb blocks on a
    #    Space Jump ledge (the Main Plaza tree's mapping of the Super Missile, 12f);
    #  - Antechamber (P61): the Ice Beam (already the Tallon's: decision B) -> a missile on its pedestal;
    #  - Elder Chamber (P57): an artifact (out, epic decision 1).
    Item("chozo_hall_of_the_elders", 52, ENERGY_TANK, (8, 27), 3, frozenset({MORPH, BOMBS})),
    Item("chozo_crossway", 53, MISSILE_TANK, (44, 27), 6, frozenset({MORPH, POWER_BOMB})),
    Item("chozo_antechamber", 61, MISSILE_TANK, (5, 7), 4),
]
BITS = {n: ITEM_BIT0 + n for n in range(len(ITEMS))}   # item bit of ITEMS[n]


def placed(built: set[str]) -> list[tuple[int, Item]]:
    """(index, item) of the items with a spot; a spot in a room that is not built is an error."""
    out = []
    for n, it in enumerate(ITEMS):
        if it.spot is None:
            continue
        if it.room not in built:
            raise ValueError(f"item da Chozo {n} ({KIND_NAME[it.kind]}) em {it.room}, sala fora do build")
        out.append((n, it))
    return out

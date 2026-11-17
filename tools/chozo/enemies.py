"""Enemies of the Chozo Ruins rooms that are built (specs/12h-inimigos-chozo.md), on the Tallon's model (specs/07i).

Counts = Prime's layer 0 ("Default") of each room (PRIME_LAYER0, read from research/prime_fs per layer: scratchpad script
s12h/chozo_layers_all.py), trimmed to at most one enemy per screen of the SM room (the Ruined Shrine's 7 Beetles -> 3, the
Tower of Light's 18 -> 12, the Ruined Fountain Access' 4 Wall Crawlers -> 3, the Nursery Access' 2 -> 1, the Plaza Access'
3 Beetles -> 2). Prime enemy -> SM stand-in (species in tools/frigate/enemies.py SPECIES):
  - Beetle -> the small Sidehopper ($A0:D93F), as in the Tallon (07i): 3 Power Beam shots, 20 a touch.
  - Wall Crawler Swarm -> the frigate's crawler (HZOOMER $A0:DC3F), as in the Tallon's region D (07l): 1 shot, 5 a touch.
  - Oculus (Prime's wall-crawling eye of the Tower of Light) -> Viola ($A0:DABF, "VIOLA"): a crawler of walls and floors;
    2 shots, 15 a touch (the epic's choice).
  - Puffer (Prime's floating gas bag) -> Mella ($A0:D13F, "MELLA"): a small floater that drifts at Samus; 2 shots, 16 a touch
    (the epic proposed PUYO $CFBF or PUU $E8BF: Puyo hops on the floor and takes 60 a touch, Puu 100: refused).
Rooms with none on layer 0 (the three elevator rooms, the Piston Tunnel, the Tower of Light Access, the Tower Chamber) stay
empty. Positions in blocks, like the Tallon's: `x` the column, `floor` the row of the solid block it starts on; floaters start
on a ledge top too (tools/validate.py checks open air for the hitbox, ground under it and the distance to the doors).
"""
from __future__ import annotations

from frigate.enemies import Spawn

B, W = "beetle", "parasite"          # the Tallon's stand-ins (07i, 07l)
O, PF = "oculus", "puffer"           # specs/12h
EY, WW, FF = "eyon", "wasp", "fireflea"   # specs/12i
MT = "metaree"                            # specs/12j
PB = "plated_beetle"                      # specs/14a (a boss: tools/chozo/bosses.py)
HV = "hive"                               # specs/14b (the Hive Mecha's hives: an arena of tools/chozo/bosses.py)
FL = "flaahgra"                           # specs/14c (Flaahgra = the Spore Spawn: an arena of tools/chozo/bosses.py)
AW = "arena_wasp"                         # specs/14d (the Incinerator Drone's wasps: spawned by its arena)
ZM = "zoomer"                             # specs/12k: the Tallon's Parasite stand-in (Zeela, specs/07i)

ENEMIES: dict[str, list[Spawn]] = {
    # Prime: 2 Beetles, in the broken floor's dip (both sides of the rubble)
    "chozo_ruins_entrance": [Spawn(B, 12, 13), Spawn(B, 20, 13)],
    # Prime: 4 Beetles; on the courtyard floor east of the stair, the pit and the dais (the way to the Ruined Shrine Access'
    # red door), two of them past the tree
    # spec 15: the east one 87 -> 72, off the screen of the R1 door (at 87 it hit Samus 10 frames after she came in by it;
    # an enemy off the camera does not move, sm_a0.c:578)
    "chozo_main_plaza": [Spawn(B, 42, 26), Spawn(B, 52, 26), Spawn(B, 76, 26), Spawn(B, 72, 26)],
    # Prime: 4 Wall Crawler Swarms; 3 screens here: 3, on the floor and on the raised middle
    "chozo_ruined_fountain_access": [Spawn(W, 12, 10), Spawn(W, 26, 8), Spawn(W, 38, 10)],
    # Prime: 3 Wall Crawler Swarms: one on each stretch of the floor
    "chozo_ruined_shrine_access": [Spawn(W, 9, 10), Spawn(W, 24, 12), Spawn(W, 39, 10)],
    # Prime: 2 Wall Crawler Swarms; 1 screen: 1, on the floor east of the hole
    "chozo_nursery_access": [Spawn(W, 12, 13)],
    # Prime: 3 Beetles; 2 screens: 2, at the east end, away from the floor door Samus comes up through (at 14 one leapt on
    # her as she rose out of it and knocked her back down: emulator, specs/12h); specs/12i opened the R0 door (the Vault):
    # the one on its ledge (29, 10) moved down to the floor. spec 15: 22 -> 19 (from 22 it leapt onto the R0 ledge ~65
    # frames after Samus came in by that door)
    "chozo_plaza_access": [Spawn(B, 19, 13), Spawn(B, 18, 13)],
    # Prime: 7 Beetles; 3 screens: 3, in the bowl (the floor missile at 24 between them). specs/14a: and the Plated Beetle
    # (Prime's layer 1 "First Pass"; a boss, tools/chozo/bosses.py, not counted with layer 0), in the middle of the bowl,
    # in the last slot (the small ones keep slots 0-2). spec 15: the small ones all in the middle screen (14 -> 18, 31 -> 29):
    # off the camera of both doors they do not move (sm_a0.c:578) until Samus walks in (from 14 and 31 one hopped onto the
    # door's terrace and hit her standing there ~200 / ~320 frames after she came in by the L0 / R0)
    "chozo_ruined_shrine": [Spawn(B, 18, 13), Spawn(B, 20, 13), Spawn(B, 29, 13), Spawn(PB, 26, 13)],
    # Prime: 6 Oculi and 12 Puffers; 12 screens: 6 + 6. Oculi on the platforms and the floor, Puffers on the other platforms
    "chozo_tower_of_light": [Spawn(O, 35, 25), Spawn(O, 27, 30), Spawn(O, 35, 45), Spawn(O, 27, 50), Spawn(O, 12, 62),
                             Spawn(O, 40, 62),
                             Spawn(PF, 36, 15), Spawn(PF, 28, 20), Spawn(PF, 36, 35), Spawn(PF, 28, 40), Spawn(PF, 36, 55),
                             Spawn(PF, 22, 62)],
    # region B (specs/12i). Prime: 5 Eyons in the tunnel's walls; 1 here, in the west end wall at Samus' height, facing east
    # down the whole tunnel: the eye's light beam (an HDMA window, MorphBallEye_Func_2) is drawn wrong once Samus is behind
    # the eye (a second one on the east face of the roof stub lit a wedge up to the top of the screen when she passed west
    # of it, emulator), and the vanilla rooms never have two of them lit at once
    "chozo_eyon_tunnel": [Spawn(EY, 1, 9, True)],
    # Prime: 2 Beetles and 2 War Wasps; 2 screens: one of each, the Sidehopper on the floor west of the dais, the wasp (Mella)
    # on the dais: it darts at Samus within 112 px (Flies_4), so it sits farther than that from where she comes in by both
    # side doors and from where she lands rising out of the floor door's hole (x 168: 131 px from the L0 entry, 127 from
    # that landing, x 295; at x 200 it darted at her as she landed, emulator). spec 15: walking in by the L0 she coasts a
    # little into the room and it hit her standing there ~60 frames later at 10 (shooting from the door it never does);
    # specs/14c: at 11 (x 184) it does not (spec 15's audit, 8 ways); the full chain's walk then reaches the North Atrium's
    # platform from a fixed spot (tests/run_tests.py CHAIN_ATRIUM_TO_DOOR)
    "chozo_ruined_nursery": [Spawn(B, 7, 13), Spawn(WW, 11, 9)],
    # Prime: 2 Wall Crawler Swarms: on the floor and on the raised stretch
    "chozo_north_atrium": [Spawn(W, 13, 10), Spawn(W, 20, 8)],
    # Prime: 3 Fire Fleas (and 5 Snake Weeds, out); 2 screens: 2, bobbing over the floor either side of the dip
    "chozo_totem_access": [Spawn(FF, 7, 10), Spawn(FF, 24, 10)],
    # Prime: 3 War Wasps (the hive's); 3 screens: 3 wasps (Mella), more than 112 px from where Samus comes in by either door:
    # west of the totem, on its top (east of the missile), past the east pool. spec 15: the west one 10 -> 11 (walking in by
    # the L0, at 10 it hit her ~65 frames after she came in). specs/14b: and the Hive Mecha (Prime's `Actor - Totem`, layer 0;
    # an arena, tools/chozo/bosses.py, not counted with layer 0): 2 hives (Kago) hanging under the combs, in the last slots
    # (the east one under the comb's west block: 5 blocks from the R0 door)
    "chozo_hive_totem": [Spawn(WW, 11, 13), Spawn(WW, 25, 9), Spawn(WW, 36, 13), Spawn(HV, 7, 6), Spawn(HV, 40, 6)],
    # region C (specs/12j). Prime: 4 Fire Fleas; 2 screens: 2, bobbing over the fountain's basin and the floor east of it
    # (5 blocks or more from the floor door's hole)
    "chozo_ruined_fountain": [Spawn(FF, 14, 14), Spawn(FF, 24, 13)],
    # Prime: 8 Metarees (they hang from the roof and dive at Samus); 6 screens, but the lower hall's are under the open pit:
    # 3 Skrees hanging from the top hall's roof (row 2), over the pit and over the east stretch to the red door
    "chozo_arboretum_access": [Spawn(MT, 20, 5), Spawn(MT, 27, 5), Spawn(MT, 39, 5)],
    # Prime: 8 Oculi (on the Spider Ball track's wall) and 1 War Wasp; 6 screens: 4 Violas on the east hall's ledges and
    # the wasp (Mella) on the wall's top by the shaft; none in the Magmoor door's pocket (no way out of it but the door)
    "chozo_sun_tower": [Spawn(O, 19, 32), Spawn(O, 26, 27), Spawn(O, 19, 22), Spawn(O, 26, 17), Spawn(WW, 12, 8)],
    # Prime: 20 Metarees (and 20 AmbientAI, out); 6 screens: 3 Skrees hanging from the roof (row 0) over the stairs
    "chozo_gathering_hall": [Spawn(MT, 15, 3), Spawn(MT, 24, 3), Spawn(MT, 31, 3)],
    # region D (specs/12k). Prime: 12 Metarees (and 2 AmbientAI, out); 3 screens: 3 Skrees hanging from the roof (row 2),
    # 14 blocks or more from the doors
    "chozo_watery_hall_access": [Spawn(MT, 16, 5), Spawn(MT, 28, 5), Spawn(MT, 36, 5)],
    # Prime: 6 Eyons (and 3 Spank Weeds, 11 AmbientAI: out); 1 eye (12i: never two lit at once), in the west wall high over
    # the L1 door, facing east: Samus is always in front of it
    "chozo_watery_hall": [Spawn(EY, 1, 12, True)],
    # Prime: 8 Metarees; 2 screens: 2 Skrees on the roof (row 2), off the raised stretch
    "chozo_east_atrium": [Spawn(MT, 11, 5), Spawn(MT, 21, 5)],
    # Prime: 3 Eyons; 1 eye in the west end wall at the top of the vault over the L0 door (5 rows over the doorway), facing
    # east down the passage (as the Eyon Tunnel's)
    "chozo_energy_core_access": [Spawn(EY, 1, 2, True)],
    # Prime: 12 Metarees (and a Puddle Toad, out); 4 screens: 3 Skrees on the roof (row 0), between the cores' columns
    "chozo_energy_core": [Spawn(MT, 15, 3), Spawn(MT, 32, 3), Spawn(MT, 46, 3)],
    # specs/14c: Prime's Flaahgra (layer 1 "1st Pass Enemies", with its 4 tentacles and bomb slots: out) -> the Spore Spawn, alone
    # (slot 0: its code keeps its state there), at its fixed spot over the pit (layouts.SUNCHAMBER_PIT: x 128, the stalk; it
    # comes down to y 624 from the roof); no layer-0 enemy (12j)
    "chozo_sunchamber": [Spawn(FL, 8, 44)],
    # Prime: 1 Fire Flea, over the floor east of the pit
    "chozo_dynamo": [Spawn(FF, 11, 13)],
    # Prime: 1 War Wasp (the hives'); a Mella, 12k's over the floor west of the stand, 14 blocks from the L0 door; specs/14d: on
    # the east block (top row 9), above where Samus stands on the floor, the stand and in the pool (a Mella below her height
    # sinks a step each dart, Flies_6/Flies_7 $A2:B1AA: 12k's sank under the floor in the fight and froze off the camera,
    # emulator); the fight counts it (the room's kill count). And the
    # Incinerator Drone's arena (Prime's 7 `Actor Hive` and its War Wasp generator; an ITEM arena of tools/chozo/bosses.py:
    # not in the population, the routine spawns them when Samus takes the stand's missile, in the first free slots): 2 hives
    # (Kago) under the roof's combs (layouts.burn_dome: columns 14-16 and 31-33, rows 1-2) and 2 wasps over the floor, 10
    # blocks either side of the stand (more than the Mella's 112 px dart from Samus on it)
    "chozo_burn_dome": [Spawn(WW, 40, 9), Spawn(HV, 15, 5), Spawn(HV, 32, 5), Spawn(AW, 13, 13), Spawn(AW, 34, 13)],
    # Prime: 8 Parasites; 4 Zeelas (the Tallon's stand-in): on the hall's floor either side of the pit and on two
    # platforms of the zigzag (specs/12l: the east one from column 50 to 48, off the B3 floor door, now a door)
    "chozo_furnace": [Spawn(ZM, 34, 28), Spawn(ZM, 48, 28), Spawn(ZM, 42, 23), Spawn(ZM, 34, 18)],
}

# Prime -> SM: the stand-in kind of each Prime enemy type on layer 0 of the built rooms (None = left out: scenery or a
# hazard that is not an enemy; specs/07i)
STAND_IN: dict[str, str | None] = {
    "Beetle": B, "WallCrawlerSwarm": W, "Oculus": O, "Puffer": PF,
    # specs/12i: War Wasp -> Mella ($A0:D13F, as the Puffer: it darts at Samus), 2 Power Beam shots, 16 a touch (the epic's
    # green Kihunter takes 6 shots, over the fairness rule; Rio's swoop reaches every spot of the Ruined Nursery);
    # Fire Flea -> Fireflea ($A0:D6BF), 1 shot, 4 a touch (12h's proposal); Eyeball (Eyon) -> the morph ball eye ($A0:E6BF):
    # harmless (no damage, no collision with Samus, no shot: it only lights her once she has the Morph Ball), immune to the
    # Power Beam (the epic's; the orchestrator's decision: fair, it never blocks a door)
    "WarWasp": WW, "FireFlea": FF, "Eyeball": EY,
    # specs/12j: Metaree Alpha (Prime's bug that hangs from the roof and dives at Samus) -> Skree ($A0:DB7F, "SKREE": hangs
    # from the ceiling and dives at her, as vanilla Crateria's and Brinstar's), 1 Power Beam shot, 10 a touch (the epic's
    # proposal, 12h's PROPOSED_LATER)
    "MetareeAlpha": MT,
    # specs/12k: Parasite (the Furnace's) -> the Tallon's Parasite stand-in, Zeela ($A0:DC7F, specs/07i: 1 Power Beam shot);
    # Puddle Toad Gamma (the Energy Core's, a platform-like toad in the water) left out, as the Tallon's scenery (12h's
    # proposal: None)
    "Parasite": ZM, "PuddleToadGamma": None,
    "AmbientAI": None, "SnakeWeedSwarm": None, "FishCloud": None, "SpankWeed": None,
}
PRIME_OF = {kind: prime for prime, kind in STAND_IN.items() if kind}

# Prime's layer 0 ("Default") enemies of every Chozo room (P# index: research/prime_fs, MREA script layers; FishCloud and the
# non-enemies left out); rooms not listed have none. Only the built rooms' (region A) have stand-ins placed; the rest is the
# record for the regions' children (12i-12l).
PRIME_LAYER0: dict[str, dict[str, int]] = {
    # region A (12h)
    "chozo_ruins_entrance": {"Beetle": 2},
    "chozo_main_plaza": {"Beetle": 4},
    "chozo_ruined_fountain_access": {"WallCrawlerSwarm": 4},
    "chozo_ruined_shrine_access": {"WallCrawlerSwarm": 3},
    "chozo_nursery_access": {"WallCrawlerSwarm": 2},
    "chozo_plaza_access": {"Beetle": 3},
    "chozo_ruined_shrine": {"Beetle": 7},
    "chozo_tower_of_light": {"Puffer": 12, "Oculus": 6},
    # region B (12i)
    "chozo_eyon_tunnel": {"Eyeball": 5},
    "chozo_ruined_nursery": {"WarWasp": 2, "Beetle": 2},
    "chozo_north_atrium": {"WallCrawlerSwarm": 2},
    "chozo_ruined_gallery": {"SnakeWeedSwarm": 6, "AmbientAI": 3},
    "chozo_transport_access_north": {"SnakeWeedSwarm": 2},
    "chozo_totem_access": {"FireFlea": 3, "SnakeWeedSwarm": 5},
    "chozo_hive_totem": {"WarWasp": 3},
    # region C (12j)
    "chozo_ruined_fountain": {"FireFlea": 4},
    "chozo_arboretum_access": {"MetareeAlpha": 8},
    "chozo_meditation_fountain": {"AmbientAI": 4},
    "chozo_sunchamber_lobby": {"SpankWeed": 2, "SnakeWeedSwarm": 3},
    "chozo_sun_tower": {"Oculus": 8, "WarWasp": 1},
    "chozo_sunchamber_access": {"SpankWeed": 3, "SnakeWeedSwarm": 1},
    "chozo_gathering_hall": {"MetareeAlpha": 20, "AmbientAI": 20},
    "chozo_sun_tower_access": {"SnakeWeedSwarm": 3},
    # region D (12k)
    "chozo_watery_hall_access": {"MetareeAlpha": 12, "AmbientAI": 2},
    "chozo_east_atrium": {"MetareeAlpha": 8},
    "chozo_watery_hall": {"SpankWeed": 3, "Eyeball": 6, "AmbientAI": 11},
    "chozo_energy_core_access": {"Eyeball": 3},
    "chozo_energy_core": {"MetareeAlpha": 12, "PuddleToadGamma": 1},
    "chozo_dynamo": {"FireFlea": 1},
    "chozo_burn_dome": {"WarWasp": 1},
    "chozo_furnace": {"Parasite": 8},
}
# Prime's layer 0 of the rooms of region E (B since specs/12i, C since specs/12j and D since specs/12k are in PRIME_LAYER0), by Prime room
# index (P#), and the stand-ins the epic (and 12h) propose for their types: a record only, no room of theirs is built (each
# region's child decides and the validator checks it then: a built room still here is an error, check_chozo_enemies).
# specs/12l: region E has no enemy on Prime's layer 0 (s12h/chozo_layers_all.txt: the Hall of the Elders' Chozo Ghosts, the
# Furnace's Beetles, the Elder Hall Access' Wall Crawlers and the Reflecting Pool's Stone Toads are on other layers): its rooms
# stay empty, and with it every region is built: the record is empty.
PRIME_LAYER0_LATER: dict[int, dict[str, int]] = {}
# War Wasp, Eyeball and Fire Flea have their stand-ins since specs/12i, Metaree Alpha since specs/12j, Parasite and Puddle
# Toad Gamma since specs/12k (STAND_IN); the rest are proposals
PROPOSED_LATER: dict[str, str | None] = {
    "ThermalHeatFader": None, "AmbientAI": None, "SnakeWeedSwarm": None, "SpankWeed": None,
}

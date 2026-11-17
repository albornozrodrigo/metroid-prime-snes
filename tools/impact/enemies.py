"""Enemies of the Impact Crater rooms that are built (specs/20f-phazon-core-impact.md), on the Mines' model (specs/19g).

Counts = Prime's layer 0 ("Default") of each room (PRIME_LAYER0, read from research/prime_fs per layer: scratchpad script
s20f/impact_layers.py -> s20f/impact_layers.out), at least one of each Prime type that has a stand-in and at most one enemy per
screen of the SM room (tools/validate.py check_impact_enemies, with check_layer0_enemies' rule). Prime enemy -> SM stand-in
(species in tools/frigate/enemies.py SPECIES): every stand-in dies to the uncharged Power Beam in at most 5 shots and takes at
most 20 a touch, in every crater room (validate.IMPACT_FAIR_EVERY_ROUND, as the Mines': the crater is entered at round 6 only):
  - MetroidAlpha (Prime's Fission Metroid, "Beta Metroid") -> Phendrana's fair copy of the SM's Metroid (specs/18l), the Mines'
    stand-in for the same type (specs/19i): it flies at Samus while on camera (Species.chase), so it starts off the camera of
    every door's screen (validate.chaser_problems).
  - FishCloud (decor), WallCrawlerSwarm (a swarm on the walls, no SM match: specs/20a's proposal) -> left out (None).
The Crater Tunnel B's Burrower and its Lumigek swarm are on Prime's layer 1 "Don't load", inactive (PRIME_INACTIVE_LAYERS): not
loaded with the room, so the room stays empty (specs/20a proposed a Burrower there: deviation recorded in specs/20f). The Entry Point
has none. Regions C and D (the descent and the Lair) are Metroid Prime's fight (epic 20, decision 3; 20g, 20h): the descent's
Prime layer 0 has only the boss (PRIME_FIGHT_LAYER0, specs/20g), so its rooms stay empty.

Positions in blocks, like the Mines': `x` the column, `floor` the row of the solid block it starts on (a floater: the floor under
it, Species.hover px below its centre).
"""
from __future__ import annotations

from frigate.enemies import Spawn

MT = "metroid"                                 # Phendrana's fair copy of the SM's Metroid (specs/18l; the Mines', specs/19i)
MP = "metroid_prime"                           # specs/20h: Metroid Prime (the Bomb Torizo's third copy)

ENEMIES: dict[str, list[Spawn]] = {
    # Prime: 4 Fission Metroids; 15 screens: two, each over a rock perch high in the hall (row 12) in the top screens 1 and 3,
    # either side of the phazon column: off the camera of the three doors' screens (validate.chaser_problems), far over the walk
    # (the floor, the zigzags, the shelves of row 26)
    "impact_phazon_core": [Spawn(MT, 24, 12), Spawn(MT, 54, 12)],
    # specs/20h: Metroid Prime's arena (tools/chozo/bosses.py ARENAS): the Bomb Torizo's third copy at the Torizo's spot (776, 368)
    "impact_lair": [Spawn(MP, 48, 26)],
}

# specs/20h: the arena's room and its boss kind (Prime's object): the Mines' ARENA_ROOMS / ARENA_KINDS
ARENA_ROOMS: dict[str, str] = {"impact_lair": "20h"}
ARENA_KINDS: dict[str, str] = {MP: "MetroidPrimeStage2"}
# Prime's layer 0 of the Lair (specs/20a): the fight's objects. The second stage stands in (MP); its MetroidBeta and 2 MetroidAlpha
# (the Metroids it spawns as it fights) and the Phazon Pool are left out (the Torizo's tiles take the room's whole enemy VRAM:
# validate.check_torizo, the only enemy of its room)
PRIME_LAIR_LAYER0: dict[str, int] = {"MetroidPrimeStage2": 1, "MetroidBeta": 1, "MetroidAlpha": 2}

# Prime -> SM: the stand-in kind of each Prime enemy type on layer 0 of the region A and B rooms (None = left out)
STAND_IN: dict[str, str | None] = {
    "MetroidAlpha": MT,
    "FishCloud": None,           # decor fish (the Tallon's rule, tallon/enemies.py)
    "WallCrawlerSwarm": None,    # the Lumigek swarm on the walls: no SM match (specs/20a's proposal)
}
PRIME_OF = {kind: prime for prime, kind in STAND_IN.items() if kind}

# Prime's layer 0 ("Default") enemies of the crater's rooms of regions A and B (research/prime_fs, MREA script layers:
# s20f/impact_layers.out; the Phazon Core's TeamAIMgr, an AI manager, and the Tunnel A's VisorGoo, a visor effect, left out);
# rooms not listed have none (the Entry Point, the Tunnel B)
PRIME_LAYER0: dict[str, dict[str, int]] = {
    "impact_tunnel_a": {"WallCrawlerSwarm": 1},
    "impact_phazon_core": {"MetroidAlpha": 4, "FishCloud": 3},
    "impact_missile_station": {"FishCloud": 4},
}

# specs/20g: Prime's layer 0 of the descent's rooms (research/prime_fs, s20g/impact_layers.py -> layers.txt) has no common enemy:
# only Metroid Prime's first stage (MetroidPrimeStage1, one in each of Subchambers One to Four) and its energy balls (EnergyBall,
# 4 in Two, Three and Four: Ice, Plasma, Power, Wave, specs/20a), the boss's fight, which the game has in the Lair only (epic 20,
# decision 3: the Subchambers a descent, no fight). Recorded, never placed; the Infusion Chamber and the Subchamber Five have none.
PRIME_FIGHT_LAYER0: dict[str, dict[str, int]] = {
    "impact_subchamber_one": {"MetroidPrimeStage1": 1},
    "impact_subchamber_two": {"MetroidPrimeStage1": 1, "EnergyBall": 4},
    "impact_subchamber_three": {"MetroidPrimeStage1": 1, "EnergyBall": 4},
    "impact_subchamber_four": {"MetroidPrimeStage1": 1, "EnergyBall": 4},
}

# Prime's enemies on layers that are not active when the room loads (the layer's "active" flag False, its name "Don't load";
# whether some script turns it on was not read: uncertain, specs/20f): recorded, never placed
PRIME_INACTIVE_LAYERS: dict[str, dict[str, int]] = {
    "impact_tunnel_b": {"Burrower": 1, "WallCrawlerSwarm": 1},   # layer 1 "Don't load"
}

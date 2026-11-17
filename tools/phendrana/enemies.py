"""Enemies of the Phendrana Drifts rooms that are built (specs/18g-inimigos-phendrana.md), on the Magmoor's model (specs/17g).

Counts = Prime's layer 0 ("Default") of each room (PRIME_LAYER0, read from research/prime_fs per layer: scratchpad script
s18/scripts/phen_objs.py, epic 18 -> s18/phen_objs.out), at least one of each Prime type that has a stand-in and at most one
enemy per screen of the SM room (tools/validate.py check_phendrana_enemies). Prime enemy -> SM stand-in (species in
tools/frigate/enemies.py SPECIES); every stand-in dies to the uncharged Power Beam in at most 5 shots and takes at most 20 a
touch, in every Phendrana room whatever its round (validate.PHENDRANA_FAIR_EVERY_ROUND, as the Magmoor's: the region's walks
run along ledges and over floor doors, a knock-back drops Samus off them):
  - Parasite -> Zeela ($A0:DC7F, the Tallon's, the Chozo's and the Magmoor's, specs/07i): a crawler; 2 shots, 10 a touch.
  - Atomic Alpha / Atomic Beta (Prime's electric Bombu, floating and drifting toward Samus) -> the Wrecked Ship's orb
    ("ATOMIC", $A0:E9FF: 250 health, 40 a touch) as its copy $A0:F8BF (tools/chozo/bosses.py ATOMIC_COPY: 100 health = 5
    shots, 20 a touch): it floats and drifts straight at Samus through the walls at 1/2 px a frame while it is on camera
    (WreckedShipOrbs_Main $A8:E3C3), as the Bombu drift at her. Two kinds (one species, one enemy-set entry), so Prime's
    two types keep their counts apart.
The Chapel of the Elders' layer 0 (4 Babygoths and the Ice Sheegoth) is the Sheegoth's fight: specs/18h's arena (ARENA_ROOMS,
ARENA_KINDS): the Dessgeega's copy and 2 small Sidehoppers, boss kinds (Species.boss: the layer-0 rules leave them out, the
arena's fairness rule weighs them). Rooms with none on layer 0 stay empty.

Positions in blocks, like the Magmoor's: `x` the column, `floor` the row of the solid block it starts on (a floater: the floor
under it, Species.hover px below its centre; tools/validate.py checks open air for the hitbox, the ground, the distance to the
doors and, for a drifter (Species.homing), that it can't reach Samus within 120 frames of her coming in by any door).

Regions B-E (18i, 18j, 18l, 18m) add their rooms to ENEMIES with the same Spawn rows and move their types from PROPOSED_LATER
to STAND_IN; PRIME_LAYER0 already has every room of the table (a built room with a Prime type not in STAND_IN is an error, and
every type of an unbuilt room is in STAND_IN or PROPOSED_LATER: validate.check_phendrana_enemies).
"""
from __future__ import annotations

from frigate.enemies import Spawn

ZM = "zoomer"                                  # the Tallon's Parasite stand-in (Zeela, specs/07i)
AA, AB = "atomic_alpha", "atomic_beta"         # specs/18g: the Atomic copy, one kind per Prime type
SG, SB = "sheegoth", "sheegoth_baby"           # specs/18h: the Sheegoth's arena (boss kinds: ARENA_KINDS)
TH = "thardus"                                 # specs/18k: the Thardus' arena
WC, BG = "parasite", "babygoth"                # specs/18i: the Wrecked Ship's zoomer; the small Sidehopper out of an arena
MT = "metroid"                                 # specs/18l: the SM's Metroid's fair copy
BT = "beetle"                                  # specs/18m: the Chozo's Beetle (the small Sidehopper)

ENEMIES: dict[str, list[Spawn]] = {
    # region A (specs/18g)
    # Prime: 4 Parasites; 12 screens: 3 Zeelas, on the beach under the west cliff, on the beach between the tower and the east
    # zigzag, and on the ice overhang (the R0 shelf)
    "phendrana_shorelines": [Spawn(ZM, 9, 26), Spawn(ZM, 50, 26), Spawn(ZM, 74, 10)],
    # Prime: 2 Atomic Betas; 3 screens: 2 orbs over the passage, more than 120 frames of their drift from both doors (validate.homing_problems; at 40 the east one touched Samus 90 frames after she came in by the R0)
    "phendrana_ice_ruins_access": [Spawn(AB, 18, 10), Spawn(AB, 32, 10)],
    # Prime: 4 Parasites; 6 screens: 2 Zeelas on the ruins' floor, between the zigzag's foot and the tower
    "phendrana_ice_ruins_east": [Spawn(ZM, 22, 26), Spawn(ZM, 30, 26)],
    # specs/18h, the Sheegoth's arena (tools/chozo/bosses.py ARENAS): Prime's 4 Babygoths and the Ice Sheegoth -> 2 small
    # Sidehoppers in the nave's middle and the Dessgeega's copy before the altar, all off the screen Samus comes in by (the
    # L0: they wait there until the camera reaches them), the Sheegoth in the last slot
    "phendrana_chapel_of_the_elders": [Spawn(SB, 24, 10), Spawn(SB, 34, 10), Spawn(SG, 46, 10)],
    # region B (specs/18i)
    # Prime: an Atomic Alpha and 2 Wall Crawler Swarms; 3 screens: the orb over the passage's middle, a zoomer on its floor in
    # the east screen
    "phendrana_courtyard_entryway": [Spawn(AA, 24, 10), Spawn(WC, 38, 10)],
    # Prime: 2 Atomic Betas; 3 screens: the Ice Ruins Access' shape and places (18g)
    "phendrana_canyon_entryway": [Spawn(AB, 18, 10), Spawn(AB, 32, 10)],
    # Prime: a Babygoth and 7 Parasites; 18 screens: the small Sidehopper on the canyon's floor between the floating platforms,
    # 2 Zeelas on the floor west and east of them (each far from the floor door, in the east)
    "phendrana_canyon": [Spawn(BG, 44, 45), Spawn(ZM, 16, 45), Spawn(ZM, 70, 45)],
    # Prime: 2 Atomic Betas; 3 screens: 2 orbs over the corridor, far from the floor door and the R0
    "phendrana_hydra_lab_entryway": [Spawn(AB, 24, 13), Spawn(AB, 34, 13)],
    # region C (specs/18j; 18g's proposal: Atomic Alpha = the orb)
    # Prime: 2 Atomic Alphas; 24 screens: an orb over a west terrace (row 26) and one over an east terrace (row 41), away from the
    # split Samus comes down at, far from both doors
    "phendrana_north_quarantine_tunnel": [Spawn(AA, 24, 26), Spawn(AA, 70, 41)],
    # Prime: 2 Atomic Alphas; 24 screens: 2 orbs in the tunnel of steps (over the steps of rows 30 and 42)
    "phendrana_south_quarantine_tunnel": [Spawn(AA, 37, 30), Spawn(AA, 52, 42)],
    # Prime: an Atomic Alpha; 2 screens: the orb over the ice pillar, midway between the doors
    "phendrana_transport_access": [Spawn(AA, 15, 8)],
    # specs/18k, the Thardus' arena (tools/chozo/bosses.py ARENAS): Prime's Thardus (layer 3: PRIME_BOSS_LAYERS) -> the Bomb
    # Torizo's copy alone (its tiles take the whole enemy VRAM), on the cave's floor in the middle of the arena (its fixed spot,
    # Species.fixed), far from the three doors
    "phendrana_quarantine_cave": [Spawn(TH, 48, 26)],
    # region D (specs/18l; 18g's proposals: Atomic Beta = the orb, MetroidAlpha = the Metroid's fair copy)
    # Prime: 3 Atomic Betas; 1 screen: 1 orb over the light fitting under the roof, over 60 px above both doors
    "phendrana_aether_lab_entryway": [Spawn(AB, 8, 4)],
    # Prime: a Metroid; 6 screens: in the lower lab east of the empty tank, off the camera of both doors (validate.chaser_problems)
    "phendrana_research_lab_aether": [Spawn(MT, 24, 26)],
    # Prime: 3 Metroids; 4 screens: in the shaft round the core (columns 22-30), off the camera of both doors (west)
    "phendrana_research_core": [Spawn(MT, 26, 11), Spawn(MT, 28, 16), Spawn(MT, 24, 26)],
    # region E (specs/18m; 18g's proposals: Beetle = the small Sidehopper, Atomic Beta = the orb; the Ripper, the Jelly Zaps,
    # the Drone, the Flying Pirates and the Spank Weeds out: PROPOSED_LATER's decision taken, STAND_IN None)
    # Prime: 2 Beetles and a Wall Crawler Swarm; 12 screens: in the gully between the cliffs (floor 26), a Beetle and the zoomer
    # in its west half and a Beetle in its east, far below both doors
    "phendrana_frost_cave_access": [Spawn(BT, 38, 26), Spawn(WC, 52, 26), Spawn(BT, 66, 26)],
    # Prime: 2 Atomic Betas; 3 screens: the Ice Ruins Access' shape and places (18g)
    "phendrana_lower_edge_tunnel": [Spawn(AB, 18, 10), Spawn(AB, 32, 10)],
    # Prime: an Atomic Beta; 2 screens: the orb over the passage's middle, more than 120 frames of drift from both doors
    "phendrana_lake_tunnel": [Spawn(AB, 18, 10)],
}

# Prime -> SM: the stand-in kind of each Prime enemy type on layer 0 of the built rooms (None = left out; specs/07i)
STAND_IN: dict[str, str | None] = {
    "Parasite": ZM, "AtomicAlpha": AA, "AtomicBeta": AB,
    "WallCrawlerSwarm": WC, "Babygoth": BG,   # specs/18i: 18g's proposals (PROPOSED_LATER) taken
    "MetroidAlpha": MT,   # specs/18l: 18g's proposal taken (the user's decision 7: the SM's Metroid weakened)
    # specs/18m: 18g's proposals for region E taken: the Beetle = the small Sidehopper (the Chozo's Beetle, specs/12h: 3 Power
    # Beam shots, 20 a touch); out (None), as the Tallon's and the Magmoor's types with no fair stand-in: the Ripper (the SM's
    # RIPPER $A0:D47F is immune to every beam, as Prime's armoured Ripper, which Samus uses as a grapple point: the fairness rule
    # refuses it, and a Ripper the beam kills would not be one), the Jelly Zaps (under water in Prime: the lakes are dry, the
    # Gravity Chamber's are fixed electric traps), the Drone, the Flying Pirates (an event of the pirates) and the Spank Weeds
    "Beetle": BT, "Ripper": None, "JellyZap": None, "Drone": None, "FlyingPirate": None, "SpankWeed": None,
    # not enemies: Prime's colour modulation and the pickup generators (the drops)
    "ColorModulate": None, "PickupGenerator": None,
}
PRIME_OF = {kind: prime for prime, kind in STAND_IN.items() if kind}

# Prime's layer 0 ("Default") enemies of every Phendrana room (research/prime_fs, MREA script layers: s18/phen_objs.out; the
# colour modulators, pickup generators and the Chapel's TeamAIMgr left out); rooms not listed have none. Only the built rooms
# (rooms.ACTIVE_REGIONS) have stand-ins placed; the rest is the record for 18h-18m. The epic's list (its "Inimigos") left out
# the Ice Ruins East's 4 Parasites: the data have them.
PRIME_LAYER0: dict[str, dict[str, int]] = {
    # region A (18g; the Chapel: 18h)
    "phendrana_shorelines": {"Parasite": 4},
    "phendrana_ice_ruins_access": {"AtomicBeta": 2},
    "phendrana_ice_ruins_east": {"Parasite": 4},
    "phendrana_chapel_of_the_elders": {"Babygoth": 4, "IceSheegoth": 1},
    # region B (18i)
    "phendrana_courtyard_entryway": {"AtomicAlpha": 1, "WallCrawlerSwarm": 2},
    "phendrana_canyon_entryway": {"AtomicBeta": 2},
    "phendrana_canyon": {"Babygoth": 1, "Parasite": 7},
    "phendrana_hydra_lab_entryway": {"AtomicBeta": 2},
    # region C (18j)
    "phendrana_north_quarantine_tunnel": {"AtomicAlpha": 2},
    "phendrana_south_quarantine_tunnel": {"AtomicAlpha": 2},
    "phendrana_transport_access": {"AtomicAlpha": 1},
    # region D (18l)
    "phendrana_research_core": {"MetroidAlpha": 3},
    "phendrana_aether_lab_entryway": {"AtomicBeta": 3},
    "phendrana_research_lab_aether": {"MetroidAlpha": 1},
    # region E (18m)
    "phendrana_frozen_pike": {"JellyZap": 1},
    "phendrana_frost_cave_access": {"Beetle": 2, "WallCrawlerSwarm": 1},
    "phendrana_hunter_cave_access": {"JellyZap": 3},
    "phendrana_frost_cave": {"Ripper": 1},
    "phendrana_lower_edge_tunnel": {"AtomicBeta": 2},
    "phendrana_chamber_access": {"Drone": 1},
    "phendrana_lake_tunnel": {"AtomicBeta": 1},
    "phendrana_edge": {"FlyingPirate": 2, "JellyZap": 2, "Ripper": 1},
    "phendrana_gravity_chamber": {"JellyZap": 2, "SpankWeed": 6},
}

# rooms whose layer 0 is a boss fight, placed by the boss' child as an arena (tools/chozo/bosses.py ARENAS), not by the layer-0
# rules: only the arena's kinds there (Species.boss), each a stand-in of a Prime type of the room (ARENA_KINDS), at most Prime's
# count, once its child built the arena (validate.check_phendrana_enemies). specs/18h: the Chapel's is built; 18k: the Quarantine Cave's (the Thardus is on Prime's layer 3: PRIME_BOSS_LAYERS)
ARENA_ROOMS: dict[str, str] = {"phendrana_chapel_of_the_elders": "18h", "phendrana_quarantine_cave": "18k"}
# specs/18h: the arenas' kinds -> the Prime type each stands in for
ARENA_KINDS: dict[str, str] = {SG: "IceSheegoth", SB: "Babygoth", TH: "Thardus"}
# specs/18k: a boss that is not on Prime's layer 0 (the Thardus: layer 3 of the Quarantine Cave, read from research/prime_fs,
# scratchpad s18k/scripts/qc_types.py: one `Thardus` object; its rocks are its own parts): Prime's count of it in its arena
PRIME_BOSS_LAYERS: dict[str, dict[str, int]] = {"phendrana_quarantine_cave": {"Thardus": 1}}

# the stand-ins proposed for the types of regions B-E that have none yet (the region's child decides and moves them to
# STAND_IN; None = left out); every type of an unbuilt room is here or in STAND_IN
PROPOSED_LATER: dict[str, str | None] = {
    # specs/18i: the Babygoth's and the Wall Crawler Swarm's taken (STAND_IN: the small Sidehopper, the Wrecked Ship's zoomer)
    # specs/18l: MetroidAlpha taken (STAND_IN: the Metroid's fair copy, tools/chozo/bosses.py METROID)
    # specs/18m: the rest decided (STAND_IN): the Beetle = the small Sidehopper; the Ripper, the Jelly Zap, the Drone, the Flying
    # Pirate and the Spank Weed out. Nothing is left to propose: every room of the table is built.
}

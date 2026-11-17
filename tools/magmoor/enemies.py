"""Enemies of the Magmoor Caverns rooms that are built (specs/17g-inimigos-magmoor.md), on the Chozo's model (specs/12h).

Counts = Prime's layer 0 ("Default") of each room (PRIME_LAYER0, read from research/prime_fs per layer: scratchpad script
s17/scripts/magmoor_objs.py, epic 17), at least one of each Prime type that has a stand-in and at most one enemy per screen of
the SM room (tools/validate.py check_magmoor_enemies). Prime enemy -> SM stand-in (species in tools/frigate/enemies.py
SPECIES); every stand-in dies to the uncharged Power Beam in at most 5 shots and takes at most 20 a touch, in every Magmoor room
whatever its round (validate.MAGMOOR_FAIR: lava lies under the walks, a knock-back can drop Samus into a pit):
  - Metaree Alpha -> Skree ($A0:DB7F, the Chozo's, specs/12j): hangs from the roof, dives at Samus; 1 shot, 10 a touch.
  - Parasite -> Zeela ($A0:DC7F, the Tallon's and the Chozo's, specs/07i, 12k): a crawler; 2 shots, 10 a touch.
  - Puffer -> Mella ($A0:D13F, the Chozo's, specs/12h): a small floater that darts at Samus within $70 px; 2 shots, 16.
  - Burrower (Prime's small digger that runs under the floor and comes up at Samus) -> Sova ($A0:DCBF, "NOVA": Norfair's fire
    crawler, the vanilla Upper Norfair's); 2 shots, 20 a touch.
  - Tryclops (Prime's three-jawed clinger that sits on the Triclops Pit's rocks and waits to grab the Morph Ball) -> Viola
    ($A0:DABF, "VIOLA": Norfair's slow fire ball; the Chozo's Oculus species, specs/12h) clinging to its rock without moving
    (parameter 1 = $FF: the crawlers' init, StoneZoomer_E67A $A3:E67A, leaves its speed at 0); 2 shots, 15 a touch. A crawling
    one (any speed) went down into the pools and along their bottoms under the lava, where no shot reaches it, and came up
    under Samus' feet on the rocks (emulator, scratchpad s17g).
specs/17h: the Magdolite (regions B/C) is out (STAND_IN: no fair SM species lives in the lava, and none may be there); specs/17i: the Puddle Spore too; Flying Pirates and the event layers are out, as in the Chozo. Rooms with none on layer 0 (the elevator rooms,
Save Station A, the Storage Cavern) stay empty.

Positions in blocks, like the Chozo's: `x` the column, `floor` the row of the solid block it starts on (a Skree: the row under
its block, hanging from the roof; tools/validate.py checks open air for the hitbox, the ground or roof, the distance to the
doors and, in the Magmoor, that it is out of the lava).

Regions B and C (17h, 17i) add their rooms to ENEMIES with the same Spawn rows; PRIME_LAYER0 already has every room of the
table (a built room with a Prime type not in STAND_IN is an error: validate.check_magmoor_enemies).
"""
from __future__ import annotations

from frigate.enemies import Spawn

MT, ZM, PF = "metaree", "zoomer", "puffer"   # the Chozo's stand-ins (specs/12j, 12k, 12h)
BU, TR = "burrower", "tryclops"              # specs/17g

ENEMIES: dict[str, list[Spawn]] = {
    # region A (specs/17g)
    # Prime: 16 Metarees and 1 Parasite; 12 screens. 3 Skrees hanging under the trail roof's 3 rock teeth (layouts.py
    # BURNING_TRAIL_TEETH, rows 13-16: from the roof itself, row 12, they were above the camera's top while Samus walks the
    # trail and never woke, DetermineWhichEnemiesToProcess $A0:8EB6), the Zeela on the trail's floor between the first two pits
    "magmoor_burning_trail": [Spawn(MT, 9, 19), Spawn(MT, 25, 19), Spawn(MT, 41, 19), Spawn(ZM, 28, 26)],
    # Prime: 1 Burrower and 2 Parasites; 3 screens: the Sova between the pits, the Zeelas on the floor by the doors' steps
    # (7 blocks from the doors: walking in, the east one reaches a still Samus ~220 frames later, spec 15's audit)
    "magmoor_lake_tunnel": [Spawn(BU, 24, 12), Spawn(ZM, 10, 12), Spawn(ZM, 38, 12)],
    # Prime: 6 Puffers; 6 screens: 3 Mellas, on the rocks of the lake and on the artifact's empty pillar (the west one at 31:
    # from 23 it darted at Samus on the rock past the first pool, magmoor_calor's lava exit)
    "magmoor_lava_lake": [Spawn(PF, 31, 12), Spawn(PF, 45, 8), Spawn(PF, 65, 12)],
    # Prime: 3 Tryclops; 2 screens: 2 Violas, on the raised stretch and on the floor east of it
    "magmoor_pit_tunnel": [Spawn(TR, 16, 8), Spawn(TR, 24, 10)],
    # Prime: 5 Tryclops (on the rocks in the pit's lava); 18 screens: 5 Violas, one on each rock between the bottom's pools
    "magmoor_triclops_pit": [Spawn(TR, 30, 42), Spawn(TR, 39, 42), Spawn(TR, 48, 42), Spawn(TR, 57, 42), Spawn(TR, 66, 42)],
    # Prime: 5 Puffers; 2 screens: 2 Mellas over the tunnel's floor. specs/17h: the east one 24 -> 12 (its R0 door opens to
    # the Monitor Station now: from 24 it darted at Samus 20 frames after she came in by it, spec 15's audit)
    "magmoor_monitor_tunnel": [Spawn(PF, 12, 12), Spawn(PF, 20, 12)],
    # region B (specs/17h)
    # Prime: 1 Magdolite (out: STAND_IN) and 2 Tryclops (on the shore's rocks); 12 screens: 2 Violas, still, on the rocks of
    # the shore's floor between its lava pits (layouts.py SHORES_PITS)
    "magmoor_fiery_shores": [Spawn(TR, 47, 26), Spawn(TR, 57, 26)],
    # the Transport Tunnel B: Prime's only one there is a Magdolite (out): empty
    # region C (specs/17i)
    # Prime: 15 Puffers (and Magdolites on layers 1-2: out); 6 screens: 3 Mellas over the rocks between the cave's lava pits
    # (layouts.py TWIN_FIRES_PITS), away from both doors
    "magmoor_twin_fires": [Spawn(PF, 24, 12), Spawn(PF, 40, 12), Spawn(PF, 70, 12)],
    # Prime: 2 Burrowers (and a Puddle Spore: out, STAND_IN); 3 screens: 2 Sovas on the floor (the Lake Tunnel's shape:
    # between the pits and on the west rock, away from the doors)
    "magmoor_south_core_tunnel": [Spawn(BU, 24, 12), Spawn(BU, 10, 12)],
    # Prime: 3 Parasites; 3 screens: 2 Zeelas on the tunnel's floor, away from both doors
    "magmoor_workstation_tunnel": [Spawn(ZM, 18, 10), Spawn(ZM, 30, 10)],
}

# Prime -> SM: the stand-in kind of each Prime enemy type on layer 0 (None = left out; specs/07i)
STAND_IN: dict[str, str | None] = {
    "MetareeAlpha": MT, "Parasite": ZM, "Puffer": PF, "Burrower": BU, "Tryclops": TR,
    # specs/17h: the Magdolite (Prime's lava dweller that rises out of the lava and breathes fire) is out: the SM's lava
    # dwellers (LAVAMAN $A0:E83F, the Magdollite: 40 a touch; DRAGON $A0:D4BF: 24) are immune to the Power Beam and live in the
    # lava, where no Magmoor enemy may be (validate.check_magmoor_enemies: every enemy out of the lava, fair in every room); a
    # copy (tools/chozo/bosses.py SpeciesCopy) changes only the touch, not the immunity nor the lava; a fair species out of the
    # lava would not be a Magdolite (decision to confirm, specs/17h)
    "Magdolite": None,
    # specs/17i: the Puddle Spore (Prime's lava-pool spore that flips over and spits) is out, as the Chozo's event-layer ones:
    # no SM species is a spore that lives in a pool; the South Core Tunnel keeps its Burrowers (Sovas)
    "PuddleSpore": None,
    # not enemies: Prime's colour modulation of the elevator rooms and the pickup generators (the drops)
    "ColorModulate": None, "PickupGenerator": None,
}
PRIME_OF = {kind: prime for prime, kind in STAND_IN.items() if kind}

# Prime's layer 0 ("Default") enemies of every Magmoor room (research/prime_fs, MREA script layers: s17/magmoor_objs.out; the
# colour modulators and pickup generators left out); rooms not listed have none. Only the built rooms (ACTIVE_REGIONS) have
# stand-ins placed; the rest is the record for 17h/17i.
PRIME_LAYER0: dict[str, dict[str, int]] = {
    # region A (17g)
    "magmoor_burning_trail": {"MetareeAlpha": 16, "Parasite": 1},
    "magmoor_lake_tunnel": {"Burrower": 1, "Parasite": 2},
    "magmoor_lava_lake": {"Puffer": 6},
    "magmoor_pit_tunnel": {"Tryclops": 3},
    "magmoor_triclops_pit": {"Tryclops": 5},
    "magmoor_monitor_tunnel": {"Puffer": 5},
    # region B (17h)
    "magmoor_fiery_shores": {"Magdolite": 1, "Tryclops": 2},
    "magmoor_transport_tunnel_b": {"Magdolite": 1},
    # region C (17i)
    "magmoor_twin_fires": {"Puffer": 15},
    "magmoor_south_core_tunnel": {"Burrower": 2, "PuddleSpore": 1},
    "magmoor_workstation_tunnel": {"Parasite": 3},
}
# the stand-ins proposed for the types of regions B/C that have none yet (the region's child decides; a built room with a type
# missing from STAND_IN is an error)
PROPOSED_LATER: dict[str, str | None] = {}   # specs/17i: none left (every region is built)

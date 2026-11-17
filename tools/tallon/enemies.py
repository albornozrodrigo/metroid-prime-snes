"""Enemies of the Tallon Overworld rooms that are built (specs/07i-inimigos-tallon.md).

Counts = Prime's layer 0 ("Default") of each room (PRIME_LAYER0, read from research/prime_fs),
trimmed to one enemy per screen of the SM room where Prime packs more into its 3D room (Canyon
Cavern 3 -> 2 Beetles, Transport Tunnel B 4 -> 3 Parasites), like the frigate. Prime enemy -> SM
stand-in (species in tools/frigate/enemies.py SPECIES):
  - Beetle -> small Sidehopper ($A0:D93F): a ground enemy that leaps at Samus; 3 Power Beam shots.
  - Geemer -> Geemer ($A0:DCFF, "ZOOMER"): the same spiky crawler; 1 shot.
  - Parasite ("Platform Zoomer", Prime's Tallon Zoomer) -> Zeela ($A0:DC7F): a crawler that looks
    different from the Geemer (both share rooms); 2 shots.
  - Blood Flower -> Cacatac ($A0:CFFF, "SABOTEN"): a plant that sits still and shoots spikes; 3 shots.
  - Seedling (specs/07m) -> the same Cacatac walking: a plant that walks and shoots needles; it walks
    64 px to each side of its spawn, so it needs 9 blocks of flat ground (tools/validate.py).
Chubb Weed (AmbientAI), Snake Weed and FishCloud are scenery/hazards in Prime and are left out; the
Landing Site has none (its gunship takes the enemy VRAM). Every stand-in dies to the Power Beam
(tools/validate.py check_enemy_sets reads it from the ROM).

Positions in blocks, like the frigate's: `x` is the column, `floor` the row of the solid block the
enemy stands on (tools/validate.py checks open air for its whole hitbox, ground under it and the
distance to the doors).
"""
from __future__ import annotations

from frigate.enemies import Spawn

B, G, Z, F = "beetle", "geemer", "zoomer", "blood_flower"
W, P, T = "parasite", "pirate", "turret"   # region D (specs/07l): the frigate's crawler and pirate, Rinka
SD = "seedling"                            # region E (specs/07m): the walking Cacatac

ENEMIES: dict[str, list[Spawn]] = {
    # Prime: 3 Beetles; 2 screens here: 2, in the dip in the middle of the floor
    "tallon_canyon_cavern": [Spawn(B, 13, 12), Spawn(B, 19, 12)],
    # Prime: 4 Parasites, 1 Geemer, 2 Beetles (10 Chubb Weeds left out). Zoomers on the terraces and
    # on the floating mossy shelf, the Geemer on a terrace (off the climb to the Root Tunnel door,
    # where a knock-back would drop Samus), the Beetles at the canyon bottom
    "tallon_canyon": [Spawn(Z, 23, 20), Spawn(Z, 47, 14), Spawn(Z, 37, 22), Spawn(Z, 29, 30),
                      Spawn(G, 42, 18), Spawn(B, 20, 38), Spawn(B, 24, 34)],
    # Prime: 2 Parasites
    "tallon_tunnel_a": [Spawn(Z, 14, 8), Spawn(Z, 9, 10)],
    # Prime: 1 Blood Flower (1 Snake Weed left out)
    "tallon_root_tunnel": [Spawn(F, 20, 10)],
    # Prime: 1 Blood Flower, 2 Geemers, 3 Parasites (the 6 Alpha Beetles are layer 1, "1st Pass")
    "tallon_root_cave": [Spawn(F, 22, 60), Spawn(G, 9, 58), Spawn(G, 35, 58),
                         Spawn(Z, 16, 58), Spawn(Z, 30, 58), Spawn(Z, 37, 58)],   # spec 15: the east one 40 -> 37
    # Prime: 4 Parasites; 3 screens here: 3
    "tallon_tunnel_b": [Spawn(Z, 8, 10), Spawn(Z, 27, 8), Spawn(Z, 38, 10)],
    # Prime: 2 Geemers, 2 Parasites (7 Chubb Weeds left out); behind the ice doors (tier 3)
    "tallon_tunnel_c": [Spawn(Z, 15, 30), Spawn(Z, 31, 22), Spawn(G, 14, 58), Spawn(G, 41, 50)],
    # region D (specs/07l), behind the ice door and the Gravity Suit (tier 4)
    # Prime: 1 Wall Crawler Swarm -> the frigate's crawler (HZOOMER), on the duct floor
    "tallon_vent_a": [Spawn(W, 22, 10)],
    # Prime: 4 Gun Turrets -> Rinka, on the steps and the tops of the containment tanks
    "tallon_biohazard": [Spawn(T, 24, 14), Spawn(T, 21, 18), Spawn(T, 8, 22), Spawn(T, 14, 22)],
    # Prime: 1 Space Pirate, on the stopped elevator car
    "tallon_elevator_beta": [Spawn(P, 8, 26)],
    # specs/07m. Gully (tier 1): Prime's 3 Parasites, on the stream bed
    "tallon_gully": [Spawn(Z, 12, 13), Spawn(Z, 25, 13), Spawn(Z, 36, 13)],
    # region E (tier 4). Great Tree Hall: 4 Seedlings walking the bottom floor and the top floor east of
    # the hole, 2 Blood Flowers at the ends of the top floor (the 2 Jelly Zaps live in the pool at the
    # bottom of Prime's hall, which stays dry here: left out). spec 15: the east Blood Flower 38 -> 24, west of the Seedling
    # (its spikes hit Samus standing at the R0 door ~90 frames after coming in)
    "tallon_great_tree_hall": [Spawn(SD, 8, 62), Spawn(SD, 18, 62), Spawn(SD, 33, 62), Spawn(SD, 28, 10),
                               Spawn(F, 24, 10), Spawn(F, 2, 10)],
    # Prime: 2 and 3 Seedlings. spec 15 (their spikes hit Samus standing at a door ~100 frames after coming in): the Tunnel D's
    # two in the middle (11, 20 -> 16, 17: spikes are shot at random, the farther from both doors the better); the Tunnel E's
    # outer two off the screen of their door (11 -> 18, 36 -> 29: an enemy off the camera does not move, sm_a0.c:578)
    "tallon_tunnel_d": [Spawn(SD, 16, 10), Spawn(SD, 17, 10)],
    "tallon_tunnel_e": [Spawn(SD, 18, 10), Spawn(SD, 23, 10), Spawn(SD, 29, 10)],
}

# Prime -> SM: the stand-in kind of each Prime enemy type (None = left out: scenery or a hazard
# that is not an enemy, or none in the built rooms' layer 0 yet; the spec has the reasons)
STAND_IN: dict[str, str | None] = {
    "Beetle": B, "Geemer": G, "Parasite": Z, "BloodFlower": F,
    "AmbientAI": None, "SnakeWeedSwarm": None, "FishCloud": None,
    # specs/07l. Spank Weed: a plant trap like the Snake Weed (07i). Jelly Zap and Drone are only on
    # event layers of region D (Reactor Core "1st pass - Jelly Zaps", Biotech/Biohazard "1st pass
    # enemies"), out like the other event layers.
    "WallCrawlerSwarm": W, "SpacePirate": P, "GunTurret": T, "SpankWeed": None,
    "JellyZap": None, "Drone": None,
    # specs/07m. Jelly Zap: in region E only in the Great Tree Hall's pool (layer 0), which stays dry
    "Seedling": SD,
}
PRIME_OF = {kind: prime for prime, kind in STAND_IN.items() if kind}

# Prime's layer 0 ("Default") enemies of the built rooms (research/prime_fs, MREA script layers;
# FishCloud left out). Rooms not listed have none on layer 0.
PRIME_LAYER0: dict[str, dict[str, int]] = {
    "tallon_landing_site": {"SnakeWeedSwarm": 2},
    "tallon_canyon_cavern": {"Beetle": 3},
    "tallon_temple_hall": {"SnakeWeedSwarm": 2},
    "tallon_waterfall_cavern": {"AmbientAI": 7},
    "tallon_canyon": {"AmbientAI": 10, "Beetle": 2, "Geemer": 1, "Parasite": 4},
    "tallon_tunnel_a": {"Parasite": 2},
    "tallon_root_tunnel": {"BloodFlower": 1, "SnakeWeedSwarm": 1},
    "tallon_frigate_access": {"SnakeWeedSwarm": 1},
    "tallon_overgrown_cavern": {"SnakeWeedSwarm": 1},
    "tallon_root_cave": {"BloodFlower": 1, "Geemer": 2, "Parasite": 3},
    "tallon_tunnel_c": {"AmbientAI": 7, "Geemer": 2, "Parasite": 2},
    "tallon_tunnel_b": {"Parasite": 4},
    # region D (specs/07l; the others have none on layer 0)
    "tallon_vent_a": {"WallCrawlerSwarm": 1},
    "tallon_cargo_lift": {"SpankWeed": 2},
    "tallon_biohazard": {"GunTurret": 4},
    "tallon_security_hall": {"SpankWeed": 5},
    "tallon_conduit_hall": {"SpankWeed": 6},
    "tallon_elevator_beta": {"SpacePirate": 1},
    # specs/07m: Gully/Alcove and region E (the Alcove, Great Tree Chamber, Life Grove Tunnel, the two
    # transports and the Life Grove have none on layer 0: the Life Grove's Chozo Ghosts and Seedling are
    # its "1st Pass Enemy" layer, its Spank Weeds the "2nd Pass")
    "tallon_gully": {"Parasite": 3},
    "tallon_great_tree_hall": {"Seedling": 4, "BloodFlower": 2, "JellyZap": 2},
    "tallon_tunnel_d": {"Seedling": 2},
    "tallon_tunnel_e": {"Seedling": 3},
}

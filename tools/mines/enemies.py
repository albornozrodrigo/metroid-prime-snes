"""Enemies of the Phazon Mines rooms that are built (specs/19g-inimigos-mines.md), on Phendrana's model (specs/18g).

Counts = Prime's layer 0 ("Default") of each room (PRIME_LAYER0, read from research/prime_fs per layer: scratchpad script
s19g/scripts/mines_objs.py -> s19g/mines_objs.txt), at least one of each Prime type that has a stand-in and at most one enemy per
screen of the SM room (tools/validate.py check_mines_enemies). Prime enemy -> SM stand-in (species in tools/frigate/enemies.py
SPECIES, the epic's technical decision 5); every stand-in dies to the uncharged Power Beam in at most 5 shots and takes at most
20 a touch, in every Mines room whatever its round (validate.MINES_FAIR_EVERY_ROUND, as the Magmoor's and Phendrana's: the walks
run along ledges and over floor doors, a knock-back drops Samus off them):
  - SpacePirate -> the frigate's and the Tallon's grey walking pirate ($A0:F653, specs/07l): 1 Power Beam shot (20 health), 15 a
    touch; it walks up to 48 px either way of its spawn (parameter 2 $30), turning at a ledge's end or a wall, and fires its laser
    (10) along its row at Samus whenever she is within 16 px of its height and it is on camera (WalkingSpacePirates_FD44
    $B2:FD44: Species.fires), so it starts where no door's camera sees it at her height (validate.shooter_problems).
  - Atomic Alpha / Atomic Beta -> Phendrana's fair copy of the Wrecked Ship's orb ($A0:F8BF, specs/18g: 5 shots, 20 a touch),
    drifting at Samus through the walls at 1/2 px a frame while on camera (Species.homing: validate.homing_problems).
The Elite Research's and the Elite Quarters' layer 0 have no enemy (the Phazon Elite is on Prime's layer 1, the Omega Pirate on
layer 5): their rooms are the arenas of specs/19h and 19k (ARENA_ROOMS), placed by those children (19h: the Phazon Elite, the
gold ninja pirate's copy, ARENA_KINDS / PRIME_BOSS_LAYERS). Rooms with none on layer 0 stay
empty. The event layers (the pirates of the ambushes, the Shadow Pirates, the Drones, the tanks' Metroids, the Elite Pirates:
the epic's user decision 5) are out.

Positions in blocks, like Phendrana's: `x` the column, `floor` the row of the solid block it starts on (a floater: the floor
under it, Species.hover px below its centre; tools/validate.py checks open air for the hitbox, the ground, the distance to the
doors, for a drifter that it can't reach Samus within 120 frames of her coming in by any door, and for a shooter that no door's
camera shows it at her height as she comes in).

Regions B-D (19i, 19j, 19l) add their rooms to ENEMIES with the same Spawn rows and move their types from PROPOSED_LATER to
STAND_IN; PRIME_LAYER0 already has every room of the table (a built room with a Prime type not in STAND_IN is an error, and every
type of an unbuilt room is in STAND_IN or PROPOSED_LATER: validate.check_mines_enemies).
"""
from __future__ import annotations

from frigate.enemies import Spawn

P = "pirate"                                   # the frigate's and the Tallon's walking pirate (specs/07l)
AB = "atomic_beta"                             # specs/18g: the Atomic copy (Prime's Atomic Beta)
PE = "phazon_elite"                            # specs/19h: the Phazon Elite (the gold ninja pirate's copy)
OP = "omega_pirate"                            # specs/19k: the Omega Pirate (the Bomb Torizo's copy)
PF = "puffer"                                  # specs/19i: the Chozo's Mella (Prime's Puffer, specs/12h)
MT = "metroid"                                 # specs/19i: Phendrana's fair copy of the SM's Metroid (specs/18l)
AA = "atomic_alpha"                            # specs/19l: Prime's Atomic Alpha (the same copy as the Beta, specs/18g)
BR = "burrower"                                # specs/19l: the Magmoor's Sova (Prime's Burrower, specs/17g)
HM = "hunter_metroid"                          # specs/19l: Prime's Hunter Metroid (MetroidBeta): the same fair Metroid

ENEMIES: dict[str, list[Spawn]] = {
    # region A (specs/19g)
    # Prime: 4 Space Pirates; 15 screens: 2 pirates, one on the crane's arm east of its cable (row 7, the sky's screen) and one
    # on the quarry's floor east of the crane tower (row 42): where no door's camera shows them at Samus' height (their laser
    # runs along their row) and the walk of region A passes under the arm and west of the tower
    "mines_main_quarry": [Spawn(P, 45, 7), Spawn(P, 77, 42)],
    # Prime: 4 Atomic Betas; 2 screens: an orb over the top ledge in the west of the shaft's top screen and one over the floor in
    # the east of its bottom screen, both far from the R0 (more than 120 frames of their drift: validate.homing_problems).
    # specs/19i: the R1 is a door now (the Elevator A's): the bottom orb moves west on the floor (x 12 -> 6), out of its reach
    "mines_elevator_access_a": [Spawn(AB, 4, 11), Spawn(AB, 6, 26)],
    # specs/19h, the Phazon Elite's arena (tools/chozo/bosses.py ARENAS): Prime's ElitePirate (layer 1: PRIME_BOSS_LAYERS) -> the
    # gold ninja pirate's copy alone, on the lab's floor (row 26) west of the zigzag: its leap (parameter 2, from its spawn
    # westward) between x 263 and 457, under no ledge, the missile's corner (x 3) out of it
    "mines_elite_research": [Spawn(PE, 28, 26)],
    "mines_elite_quarters": [Spawn(OP, 48, 26)],   # specs/19k: at the Torizo's spot (776, 368)
    # region B (specs/19i)
    # Prime: 2 Space Pirates; 2 screens (both a door's): one pirate, on the catwalk over the corridor (row 6: never at her
    # height, as she comes in by either door or walks under it: validate.shooter_problems)
    "mines_elite_control_access": [Spawn(P, 14, 6)],
    # Prime: 8 Puffers in the vent's gas; 2 screens: one Mella in the middle of the vent, over the duct (as far from both doors:
    # at x 24 it reached her 20 frames after she came in by the R0, entradas_de_porta_mines)
    "mines_ventilation_shaft": [Spawn(PF, 16, 10)],
    # Prime: 5 Metroids; 12 screens: two, in the west half of the hall (columns 24 and 36, over the floor), off the camera of the
    # ceiling door's screen and of the L1's (a wall until 19l): validate.chaser_problems; the walks keep to the east half
    "mines_metroid_quarantine_a": [Spawn(MT, 24, 26), Spawn(MT, 36, 26)],
    # region D (specs/19l)
    # Prime: 3 Atomic Alphas (invisible); 2 screens: one orb over the middle of the corridor
    "mines_quarantine_access_b": [Spawn(AA, 16, 10)],
    # Prime: 3 Burrowers; 4 screens: one Sova on the floor in the middle of the room, under the zigzag
    "mines_elevator_access_b": [Spawn(BR, 14, 26)],
    # Prime: 6 Metroids and a Ripper (out); 12 screens: two, in the east half (columns 54 and 70, over the floor), off the camera
    # of the three doors' screens (validate.chaser_problems)
    "mines_fungal_hall_b": [Spawn(MT, 54, 29), Spawn(MT, 70, 29)],
    # Prime: 3 Atomic Alphas and a Space Pirate; 6 screens: the pirate on the catwalk over the floor (row 38: never at her height),
    # one orb high in the shaft (over the top fungus ledge)
    "mines_fungal_hall_access": [Spawn(P, 14, 38), Spawn(AA, 6, 14)],
    # Prime: 4 Hunter Metroids (MetroidBeta) and a Ripper (out); 12 screens: two, in the middle of the floor (columns 54 and 70)
    "mines_fungal_hall_a": [Spawn(HM, 54, 26), Spawn(HM, 70, 26)],
}

# Prime -> SM: the stand-in kind of each Prime enemy type on layer 0 of the built rooms (None = left out; specs/07i)
STAND_IN: dict[str, str | None] = {
    "SpacePirate": P, "AtomicBeta": AB,
    "AtomicAlpha": "atomic_alpha",   # the epic's decision 5: the same copy as the Beta (Phendrana's two kinds, specs/18g)
    # the Ripper out (None), as in Phendrana (specs/18m): the SM's RIPPER $A0:D47F is immune to every beam (the fairness rule
    # refuses it), as Prime's armoured Ripper
    "Ripper": None,
    # specs/19i: 19g's proposals taken for region B: the Puffer = the Chozo's Mella, the Metroid Alpha = Phendrana's fair Metroid
    "Puffer": PF, "MetroidAlpha": MT,
    # specs/19l: 19g's proposals taken for region D: the Hunter Metroid = the same fair Metroid; the Burrower = the Magmoor's Sova
    "MetroidBeta": HM, "Burrower": BR,
}
PRIME_OF = {kind: prime for prime, kind in STAND_IN.items() if kind}

# Prime's layer 0 ("Default") enemies of every Mines room (research/prime_fs, MREA script layers: s19g/mines_objs.txt; the
# Metroid Quarantine A's TeamAIMgr, an AI manager, left out); rooms not listed have none. Only the built rooms (rooms.ACTIVE_REGIONS)
# have stand-ins placed; the rest is the record for 19i, 19j and 19l. The same as the epic's list ("Inimigos").
PRIME_LAYER0: dict[str, dict[str, int]] = {
    # region A (19g)
    "mines_main_quarry": {"SpacePirate": 4},
    "mines_elevator_access_a": {"AtomicBeta": 4},
    # region B (19i)
    "mines_elite_control_access": {"SpacePirate": 2},
    "mines_ventilation_shaft": {"Puffer": 8},
    "mines_metroid_quarantine_a": {"MetroidAlpha": 5},
    # region C (19j): none on layer 0 (the Processing Center Access' 3 Atomic Alphas are its layer 3)
    # region D (19l)
    "mines_quarantine_access_b": {"AtomicAlpha": 3},
    "mines_elevator_access_b": {"Burrower": 3},
    "mines_fungal_hall_b": {"MetroidAlpha": 6, "Ripper": 1},
    "mines_fungal_hall_access": {"AtomicAlpha": 3, "SpacePirate": 1},
    "mines_fungal_hall_a": {"MetroidBeta": 4, "Ripper": 1},
}

# rooms whose fight is a boss of the epic (user decision 4), placed by the boss' child as an arena (tools/chozo/bosses.py ARENAS),
# not by the layer-0 rules: no layer-0 stand-in there (neither has one on Prime's layer 0)
ARENA_ROOMS: dict[str, str] = {"mines_elite_research": "19h", "mines_elite_quarters": "19k"}
# specs/19h: the arenas' kinds -> the Prime type each stands in for (as Phendrana's, specs/18h)
ARENA_KINDS: dict[str, str] = {PE: "ElitePirate", OP: "OmegaPirate"}
# specs/19h: a boss not on Prime's layer 0 (the Phazon Elite: layer 1 of the Elite Research, one `ElitePirate`, read from
# research/prime_fs, s19h/scripts/er_types.py): Prime's count of it in its arena
# specs/19k: the Omega Pirate, layer 5 "Omega Pirate Battle" of the Elite Quarters, one `OmegaPirate` (type $86, read from
# research/prime_fs, s19k/eq_types.py; its 8 SpacePirates and the healing nodes there are out: decision 5)
PRIME_BOSS_LAYERS: dict[str, dict[str, int]] = {"mines_elite_research": {"ElitePirate": 1}, "mines_elite_quarters": {"OmegaPirate": 1}}

# the stand-ins proposed for the types of regions B-D that have none yet (the region's child decides and moves them to STAND_IN;
# None = left out); every type of an unbuilt room is here or in STAND_IN
# specs/19l: none left (every room is built: the Hunter Metroid and the Burrower moved to STAND_IN)
PROPOSED_LATER: dict[str, str | None] = {}

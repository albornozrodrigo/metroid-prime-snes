"""Enemies of the Frigate Orpheon, mapped from Prime's objects to Super Metroid species.

Counts follow Prime's MREA layers (research/frigate_objects.json), trimmed where Prime packs
more actors than a 2D room can hold:
  - Parasite / WallCrawlerSwarm -> Wrecked Ship orange zoomer ($A0:DC3F). It crawls on any
    surface and turns toward Samus, like Prime's parasites.
  - SpacePirate -> grey walking Space Pirate ($A0:F653). It patrols, shoots and dodges shots.
  - NewIntroBoss (Parasite Queen) -> Phantoon ($A0:E4BF), the native boss of area 3. Its death
    sets the area-3 boss bit, which opens the grey escape doors. The boss room is built in
    tools/build.py from the vanilla Phantoon state.

SPECIES also holds the Tallon Overworld's stand-ins (specs/07i-inimigos-tallon.md, 07l, 07m), placed by
tools/tallon/enemies.py, and the Chozo Ruins' (specs/12h, tools/chozo/enemies.py). Two kinds may share a species (07m: the Blood Flower's still Cacatac and the
Seedling's walking one): the enemy set lists that species once, so they share its palette.

Positions are in blocks: `x` is the column, `floor` is the row of the solid block the enemy stands
on. tools/validate.py checks that each spot is open air standing on solid ground.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass


@dataclass(frozen=True)
class Species:
    ptr: int          # species header in $A0
    height: int       # y radius in pixels (from the species header)
    init: int         # population "init param"
    properties: int
    extra: int
    param1: int
    param2: int
    palette: int      # enemy-set word: sprite palette slot
    patrol: int = 0   # px it walks to each side of its spawn (0 = stays put; validate.py checks the ground)
    # specs/12i: a second population entry the vanilla placements always put with this one, at the same spot, in the slot
    # before it (the morph ball eye's socket, same species): (species, properties, param 1, param 2), param 2 None = the
    # wall side's ($8000 | Spawn.wall_side()); it is not an enemy of its own (no kill count)
    companion: tuple[int, int, int, int | None] | None = None
    # specs/12i: what it starts against: "floor" (standing on it), "wall" (the morph ball eye: its socket is drawn in the
    # wall beside it) or "ceiling" (the Rio hangs from it); `floor` is the row under its block either way, and validate.py
    # checks the floor, the wall block or the ceiling block over it
    mount: str = "floor"
    # specs/12i: never hurts (header damage 0, its init sets "no collision with Samus", no projectile: the morph ball eye
    # only lights her with its beam): it counts for no kill, and the fairness rule takes it although it can't be shot dead
    harmless: bool = False
    # specs/12i: a floater that bobs up and down `bob` px from where it starts, `hover` px over its spawn's floor (the
    # Fireflea: its lowest point on the floor); validate.py checks open air over the whole bob
    hover: int = 0
    bob: int = 0
    # specs/14a: a boss stand-in (tools/chozo/bosses.py BOSSES): not one of Prime's layer-0 enemies, so the layer-0 counts,
    # the one-per-screen rule and the common fairness rule leave it out; validate.check_bosses checks it instead
    boss: bool = False
    # specs/14c: a boss whose own code puts it at a fixed pixel (the Spore Spawn: x 128, its fight around (128, 624),
    # $A5:E87C); the spawn's x/floor only say where it is drawn in the layout (validate.check_enemies checks its hitbox
    # there, in open air; it hangs from its stalk, no ground)
    fixed: tuple[int, int] | None = None
    # specs/18g: it drifts straight at Samus through walls while it runs (the Wrecked Ship's orb, WreckedShipOrbs_Main
    # $A8:E3C3: x and y each at the speed of entry param2 of kCommonEnemySpeeds_Linear $A2:8187); validate.py checks that it
    # starts far enough from every door that it can't reach Samus within spec 15's 120 frames of her coming in
    homing: bool = False
    # specs/18l: it flies at Samus, up to `chase` px a frame on each axis, only while it is on the camera (its properties lack
    # $0800: off the camera an enemy is not run, sm_a0.c:578), and walls stop it (the Metroid: Metroid_Func_1 $A3:EC11 clamps
    # its speed to 3); validate.py checks it is off the camera of every door's screen as she comes in (at 3 px a frame it would
    # cross a screen in spec 15's 120 frames)
    chase: float = 0.0
    # specs/19g: it fires along its own row at Samus whenever she is within `fires` px of its height, at any distance, while it is
    # on camera (the walking pirate: WalkingSpacePirates_FD44 $B2:FD44, IsSamusWithinEnemy_Y 16, then its laser, $86:A17B: 10);
    # validate.py checks (in the Mines) that no door's camera shows it within that height of Samus as she comes in
    fires: int = 0


SPECIES = {
    # values copied from vanilla placements: $8F:968F (zoomer), $8F:975C (walking pirate)
    "parasite": Species(0xDC3F, 8, 0x0003, 0x2001, 0x0000, 0x0001, 0x0000, 0x0001),
    "pirate": Species(0xF653, 32, 0x0000, 0x2000, 0x0004, 0x8000, 0x0030, 0x0002, fires=16),
    # Tallon Overworld stand-ins (specs/07i-inimigos-tallon.md; placed by tools/tallon/enemies.py).
    # Values copied from vanilla floor placements: crawlers upright on the floor = init 3 (Brinstar
    # $8F:9F11 zoomer; $8F:9FBA zeela, param 2 = 2 picks the Zeela's turning frames), small
    # sidehopper $8F:9E52, cactus $8F:9FBA (param 1/2 = 0: stays put, upright). Palette slots differ
    # per species, so any mix shares a room (validate.check_enemy_sets).
    "geemer": Species(0xDCFF, 8, 0x0003, 0x2001, 0x0000, 0x0002, 0x0000, 0x0001),
    "zoomer": Species(0xDC7F, 8, 0x0003, 0x2001, 0x0000, 0x0001, 0x0002, 0x0002),
    "beetle": Species(0xD93F, 13, 0x0000, 0x2000, 0x0000, 0x0000, 0x0000, 0x0003),
    "blood_flower": Species(0xCFFF, 8, 0x0000, 0x2000, 0x0000, 0x0000, 0x0000, 0x0007),
    # specs/07l: Prime's Gun Turret (sunken frigate) -> Rinka ($A0:D23F, "RINKA"): a fixed emitter
    # that keeps firing a ring at Samus, as a turret; values of the vanilla Tourian placements
    # ($8F:DAE1: init 0, properties $6000, parameters 0 = the plain Rinka, not Mother Brain's)
    "turret": Species(0xD23F, 8, 0x0000, 0x6000, 0x0000, 0x0000, 0x0000, 0x0003),
    # specs/07m: Prime's Seedling (a plant that walks and shoots needles) -> the Cacatac walking, as the
    # vanilla Maridia placements ($8F:9FBA: parameter 2 = $0301, speed 3 = 3/16 px a frame, range index 1
    # = 64 px each side, $A2:9F36), upright like the Blood Flower's (parameter 1 = 0: starts walking left);
    # same species, so same palette (one enemy-set entry)
    "seedling": Species(0xCFFF, 8, 0x0000, 0x2000, 0x0000, 0x0000, 0x0301, 0x0007, patrol=64),
    # specs/12h (Chozo Ruins, placed by tools/chozo/enemies.py). Prime's Oculus (the Tower of Light's wall-crawling eye) ->
    # Viola ($A0:DABF, "VIOLA"), values of the vanilla Norfair placements ($8F:AB07: init 3, properties $2001, parameters
    # 2 / 6: upright on the floor, crawling); Prime's Puffer (a floating gas bag) -> Mella ($A0:D13F, "MELLA"), values of the
    # vanilla ones ($8F:A815: all 0, properties $2000). Palette slots 2 and 7: they share the tower's set.
    "oculus": Species(0xDABF, 8, 0x0003, 0x2001, 0x0000, 0x0002, 0x0006, 0x0002),
    "puffer": Species(0xD13F, 4, 0x0000, 0x2000, 0x0000, 0x0000, 0x0000, 0x0007),
    # specs/12i (region B). Prime's War Wasp -> Mella ($A0:D13F, the Puffer's species, as the Cacatac is both the Blood
    # Flower and the Seedling since 07m: one enemy-set entry, one palette): it hovers in a small circle and darts at Samus
    # when she comes within $70 px (Flies_4, sm_a2.c:1802), as a wasp. Measured and refused: the green Kihunter (HACHI1
    # $EABF, the epic's: 6 Power Beam shots, over the fairness rule's 5) and Rio ($D27F: it swoops from the ceiling within
    # $A0 px, Rio_1 sm_a2.c:2278; in the Ruined Nursery no spot is that far from both side doors and from the floor door's
    # hole, and over the hole it knocked Samus back down it as she came up, emulator). Prime's Fire Flea -> Fireflea ($A0:D6BF, "HOTARY"),
    # floating up and down (vanilla $8F:9C5E: parameter 1 = 0, parameter 2 = range index << 8 | speed index; here 24 px
    # each way, speed 8). Prime's Eyon (Eyeball) -> the morph ball eye ($A0:E6BF, "EYE"), as the vanilla Morph Ball Room
    # ($8F:9E9F, $A1:93AC): its socket entry (parameter 2 $8000 | wall side: 0 = the wall on its left, 1 = on its right)
    # then the eye (parameter 1 = 1 facing right, 0 left), properties $2C00; harmless (the epic's proposal; orchestrator's
    # decision for 12i: fair if it never blocks a door).
    "wasp": Species(0xD13F, 4, 0x0000, 0x2000, 0x0000, 0x0000, 0x0000, 0x0007),
    "fireflea": Species(0xD6BF, 8, 0x0000, 0x2000, 0x0000, 0x0000, 0x0208, 0x0002, hover=24, bob=24),
    "eyon": Species(0xE6BF, 8, 0x0000, 0x2C00, 0x0000, 0x0000, 0x0000, 0x0007, companion=(0xE6BF, 0x2C00, 0x0000, None),
                    mount="wall", harmless=True),
    # specs/12j (region C). Prime's Metaree Alpha -> Skree ($A0:DB7F, "SKREE"): hangs from the ceiling and dives at Samus;
    # values of the vanilla placements (Crateria $8F:92FD's, Brinstar $8F:9F64's and $A3DD's: init 0, properties $2000,
    # parameters 0), y radius 12 (its header); palette slot 3 (vanilla $8F:9F64's set; the Sidehopper's slot, no region-C
    # room has both)
    "metaree": Species(0xDB7F, 12, 0x0000, 0x2000, 0x0000, 0x0000, 0x0000, 0x0003, mount="ceiling"),
    # specs/14a (Chozo boss, tools/chozo/bosses.py): Prime's Plated Beetle -> a copy of the big Sidehopper ($A0:D9BF) at
    # $A0:F83F (touch 40, the Plated Beetle's colours), y radius 20 (its header); values of the vanilla floor placements
    # ($8F:9E9F's, $A1: init 0, properties $2000, parameters 0 = on the floor); palette slot 2 (vanilla $8F:9E11's set)
    "plated_beetle": Species(0xF83F, 20, 0x0000, 0x2000, 0x0000, 0x0000, 0x0000, 0x0002, boss=True),
    # specs/14b (an arena of tools/chozo/bosses.py ARENAS): Prime's Hive Mecha (the Hive Totem's hives) -> Kago ($A0:E7FF,
    # "KAGO", the bug hive), hanging under the hall's combs; values of the vanilla placements ($8F:9552, $9969, $ADAD: init 0,
    # properties $A000, parameter 1 = $000A) but parameter 1 = 4: it dies after parameter 1 + 1 hits (its shot AI counts
    # them, $A8:AB83: bosses.KAGO_HITS), not by its 1600 health; each hit throws a bug (20 a touch); y radius 16 (its header);
    # palette slot 2 (E3's set, with the wasps' 7). specs/14d: the copy with 1 part ($A0:F87F, bosses.KAGO_COPY: SpawnEnemy
    # spawns as many slots as the header's parts, the Kago's says 9)
    "hive": Species(0xF87F, 16, 0x0000, 0xA000, 0x0000, 0x0004, 0x0000, 0x0002, mount="ceiling", boss=True),
    # specs/14d (the Incinerator Drone's arena, tools/chozo/bosses.py ARENAS, an ITEM one): the wasps that come with the hives
    # when the fight starts (Prime's War Wasp generator) -> the wasp's Mella, marked as the arena's (spawned by the routine,
    # not in the room's population; one enemy-set entry and palette with the wasp's), 72 px over its floor: above Samus on the
    # floor and on the stand (a Mella below her height sinks a step a dart: Flies_6/Flies_7, emulator)
    "arena_wasp": Species(0xD13F, 4, 0x0000, 0x2000, 0x0000, 0x0000, 0x0000, 0x0007, boss=True, hover=72),
    # specs/14c (an arena of tools/chozo/bosses.py ARENAS): Prime's Flaahgra -> the Spore Spawn ($A0:DF3F, "the plant boss" of
    # SM's area 1, recoloured in place with Flaahgra's colours: bosses.FLAAHGRA_PALETTES), values of its vanilla placement
    # ($A1:A0FD: x 128, y 624, init 0, properties $2800, extra properties $0004 (its extended spritemaps: without it the body is
    # not drawn, emulator), parameters 0; set palette 1, $B4:8663), y radius 32 (its header); it must be the room's slot 0
    # (its code keeps its state in enemy 0's fields)
    "flaahgra": Species(0xDF3F, 32, 0x0000, 0x2800, 0x0004, 0x0000, 0x0000, 0x0001, boss=True, fixed=(128, 624)),
    # specs/17g (Magmoor Caverns, placed by tools/magmoor/enemies.py). Prime's Burrower -> Sova ($A0:DCBF, "NOVA", Norfair's
    # fire crawler), values of the vanilla Upper Norfair placements ($8F:A7DE's, $A1:B9D8: init 3 = upright on the floor,
    # properties $2000, parameter 1 = speed index 1 ($A3:E5F0: $80, 1/2 px a frame), parameter 2 = 4); palette slot 1 (the
    # Lake Tunnel's set has the Zeela's 2). Prime's Tryclops -> Viola ($A0:DABF, the Oculus' species and palette, specs/12h)
    # that does not move: parameter 1 = $FF (StoneZoomer_E67A $A3:E67A sets the speed from parameter 1 unless it is $FF: it
    # stays 0; emulator: still on its rock for good), the rest as the Oculus' ($8F:AB07's).
    "burrower": Species(0xDCBF, 8, 0x0003, 0x2000, 0x0000, 0x0001, 0x0004, 0x0001),
    "tryclops": Species(0xDABF, 8, 0x0003, 0x2001, 0x0000, 0x00FF, 0x0006, 0x0002),
    # specs/18g (Phendrana Drifts, placed by tools/phendrana/enemies.py). Prime's Atomic Alpha / Beta (the electric Bombu that
    # float and drift toward Samus) -> the Wrecked Ship's orb ("ATOMIC") as its fair copy ($A0:F8BF, tools/chozo/bosses.py
    # ATOMIC_COPY: 100 health, 20 a touch), values of the vanilla moving placements ($8F:CA7E's, $A1:BFE6: init 0, properties
    # $2000, parameter 1 = its animation (0), parameter 2 = speed index 8: 1/2 px a frame on each axis), floating `hover` px
    # over its spawn's floor; palette slot 3 (vanilla $CA7E's set gives it 2: the Zeela's; slot 3 lets a room hold both). Two
    # kinds, one species (one enemy-set entry, as the Blood Flower's and the Seedling's): Prime's Alpha and Beta
    "atomic_alpha": Species(0xF8BF, 8, 0x0000, 0x2000, 0x0000, 0x0000, 0x0008, 0x0003, hover=32, homing=True),
    "atomic_beta": Species(0xF8BF, 8, 0x0000, 0x2000, 0x0000, 0x0000, 0x0008, 0x0003, hover=32, homing=True),
    # specs/18h (the Sheegoth's arena, tools/chozo/bosses.py ARENAS): Prime's IceSheegoth -> the Dessgeega's copy ($A0:F8FF,
    # bosses.SHEEGOTH: touch 40, the Ice Sheegoth's colours), y radius 20 (its header); values of the vanilla floor
    # placements ($A1:A560's: init 0, properties $2000, parameters 0 = on the floor); palette slot 2. Prime's Babygoths of the
    # chapel -> the small Sidehopper ($A0:D93F, as the Chozo's Beetle: 60 health = 3 Power Beam shots, 20 a touch), marked as
    # the arena's (they are the Sheegoth's brood: gone with it in the dead state); palette slot 3 (the 14a set's)
    "sheegoth": Species(0xF8FF, 20, 0x0000, 0x2000, 0x0000, 0x0000, 0x0000, 0x0002, boss=True),
    "sheegoth_baby": Species(0xD93F, 13, 0x0000, 0x2000, 0x0000, 0x0000, 0x0000, 0x0003, boss=True),
    # specs/18i (Phendrana's region B): Prime's Babygoth out of an arena (the Phendrana Canyon's, layer 0) -> the small
    # Sidehopper as the Chozo's Beetle (60 health = 3 Power Beam shots, 20 a touch), a layer-0 kind (not the arena's)
    "babygoth": Species(0xD93F, 13, 0x0000, 0x2000, 0x0000, 0x0000, 0x0000, 0x0003),
    # specs/18k (the Thardus' arena, tools/chozo/bosses.py ARENAS): Prime's Thardus -> the Bomb Torizo's copy ($A0:F93F,
    # bosses.THARDUS: 400 health), y radius 48 (its header); values of its vanilla placement ($A1:84ED: init 0, properties
    # $2000, parameters 0; set palette 1, $B4:80B3); its init puts it at its tables' spot whatever the population says
    # (bosses.TORIZO_SPOT, patched to this one: the cave's floor, row 26, in the middle of the arena) and sets its own
    # properties ($2800: processed off the camera) and extended spritemaps
    "thardus": Species(0xF93F, 48, 0x0000, 0x2000, 0x0000, 0x0000, 0x0000, 0x0001, boss=True, fixed=(776, 368)),
    # specs/18l (Phendrana's region D, the labs): Prime's MetroidAlpha -> the SM's Metroid as its fair copy ($A0:F97F,
    # bosses.METROID: 100 health, 20 a touch, no latch, the beams hurt it, the ice freezes it), y radius 10 (its header); values
    # of the vanilla Tourian placements ($A1:E1D8's: init 0, properties $2000, parameters 0 and 5), floating `hover` px over its
    # spawn's floor; palette slot 1
    "metroid": Species(0xF97F, 10, 0x0000, 0x2000, 0x0000, 0x0000, 0x0005, 0x0001, hover=40, chase=3.0),
    # specs/19l (the Mines' region D): Prime's MetroidBeta (the Hunter Metroid) -> the same fair copy, one kind per Prime type (as the
    # two Atomics, specs/18g)
    "hunter_metroid": Species(0xF97F, 10, 0x0000, 0x2000, 0x0000, 0x0000, 0x0005, 0x0001, hover=40, chase=3.0),
    # specs/19h (the Phazon Elite's arena, tools/chozo/bosses.py ARENAS): Prime's ElitePirate of the Elite Research -> the gold
    # ninja pirate's copy ($A0:F9BF, bosses.PHAZON_ELITE: 400 health, 40 a touch, the phazon colours), y radius 32 (its header);
    # values of the vanilla placements ($A1:A219, $8F:B62B: init 0, properties $2800 = processed off the camera too, extra $0004,
    # parameter 1 = 0: it starts at the east end of its leap, parameter 2 = $C0: the leap's span, 194 px); set palette 1 (its
    # code sets the sprite line 1 back after each leap: bosses.NINJA_PALETTE_INDEX)
    "phazon_elite": Species(0xF9BF, 32, 0x0000, 0x2800, 0x0004, 0x0000, 0x00C0, 0x0001, boss=True),
    # specs/19k (the Omega Pirate's arena, tools/chozo/bosses.py ARENAS): Prime's OmegaPirate -> the Bomb Torizo's second copy
    # ($A0:F9FF, bosses.OMEGA: 1200 health, no uncharged beam hurts it), the Thardus' values (y radius 48; init 0, properties $2000,
    # parameters 0; set palette 1); its init puts it at the Torizo's tables' spot, the Thardus' (bosses.TORIZO_SPOT: one spot for
    # both copies), on the Elite Quarters' floor, row 26
    "omega_pirate": Species(0xF9FF, 48, 0x0000, 0x2000, 0x0000, 0x0000, 0x0000, 0x0001, boss=True, fixed=(776, 368)),
    # specs/20h: Prime's MetroidPrimeStage2 (the Impact Crater's Metroid Prime Lair) -> the Bomb Torizo's third copy ($A0:FA3F,
    # bosses.METROID_PRIME: 3000 health), the Omega Pirate's values; at the Torizo's spot (one for every copy), on the Lair's floor,
    # row 26
    "metroid_prime": Species(0xFA3F, 48, 0x0000, 0x2000, 0x0000, 0x0000, 0x0000, 0x0001, boss=True, fixed=(776, 368)),
}


@dataclass(frozen=True)
class Spawn:
    kind: str
    x: int
    floor: int
    facing_right: bool = False

    @property
    def species(self) -> Species:
        return SPECIES[self.kind]

    def pixel_pos(self) -> tuple[int, int]:
        if self.species.fixed:
            return self.species.fixed
        return self.x * 16 + 8, self.floor * 16 - self.species.height - self.species.hover

    def wall_side(self) -> int:
        """specs/12i, a wall-mounted one: 0 = the wall on its left (it faces right), 1 = on its right."""
        return 0 if self.facing_right else 1

    def entries(self) -> list[tuple[int, int, int, int, int, int, int, int]]:
        """Its population entries (species, x, y, init, properties, extra, param 1, param 2), in slot order: its companion
        (the eye's socket) first, as vanilla."""
        s = self.species
        x, y = self.pixel_pos()
        p1 = s.param1 | (1 if self.facing_right and self.kind in ("pirate", "eyon") else 0)
        out = [(s.ptr, x, y, s.init, s.properties, s.extra, p1, s.param2)]
        if s.companion:
            ptr, props, c1, c2 = s.companion
            other = (ptr, x, y, 0, props, 0, c1, 0x8000 | self.wall_side() if c2 is None else c2)
            out = [other] + out
        return out

    def entry(self) -> bytes:
        return b"".join(struct.pack("<8H", *e) for e in self.entries())


P, S = "parasite", "pirate"

ENEMIES: dict[str, list[Spawn]] = {
    # Prime: 3 Parasites
    "access_hall": [Spawn(P, 10, 10), Spawn(P, 24, 10), Spawn(P, 31, 8)],
    # Prime: 3 Parasites + 1 Space Pirate
    "evac_area": [Spawn(P, 9, 20), Spawn(P, 19, 15), Spawn(P, 14, 27), Spawn(S, 20, 27)],
    # Prime: 2 Parasites
    "map_facility": [Spawn(P, 29, 14), Spawn(P, 15, 10)],   # 29: clear of the map station
    # Prime: 8 Space Pirates (most break out of stasis tanks); 3 here
    "biotech_1": [Spawn(S, 24, 18), Spawn(S, 23, 11, True), Spawn(S, 38, 31)],
    # Prime: 4 Space Pirates; 2 here
    "biohazard": [Spawn(S, 22, 14), Spawn(S, 18, 30, True)],
    # Prime: 2 Parasites + 1 Space Pirate
    "cargo_lift": [Spawn(P, 25, 34), Spawn(P, 5, 40), Spawn(S, 20, 63)],
    # Prime: WallCrawlerSwarm (parasite swarms in the vents)
    "vent_c": [Spawn(P, 12, 10), Spawn(P, 20, 10)],
    "vent_b": [Spawn(P, 3, 17)],
    "vent_a": [Spawn(P, 20, 26)],
    "subvent_a": [Spawn(P, 12, 12), Spawn(P, 3, 17)],
    "subvent_b": [Spawn(P, 16, 14), Spawn(P, 22, 14)],
}


def population(spawns: list[Spawn]) -> bytes:
    """Enemy population list ($A1): entries, FF FF, kills needed to clear the room."""
    return b"".join(s.entry() for s in spawns) + b"\xFF\xFF" + bytes([sum(not s.species.harmless for s in spawns)])


def slots(spawns: list[Spawn]) -> list[int]:
    """specs/12i: the species in each enemy slot the population fills (a spawn with a companion takes two), in order."""
    return [e[0] for s in spawns for e in s.entries()]


def set_species(spawns: list[Spawn]) -> list[tuple[int, int]]:
    """(species pointer, palette) of a room's enemy set, one per species, in order of the first kind
    (sorted by name) that uses it; kinds sharing a species must share its palette."""
    out: dict[int, int] = {}
    for k in sorted({s.kind for s in spawns}):
        sp = SPECIES[k]
        if out.setdefault(sp.ptr, sp.palette) != sp.palette:
            raise ValueError(f"espécie ${sp.ptr:04X} com duas paletas no mesmo enemy set")
    return list(out.items())


def enemy_set(spawns: list[Spawn], name: bytes = b"FRIGATE") -> bytes:
    """Enemy set ($B4): 7-byte debug name, {species, palette} pairs, FF FF. Max 4 species."""
    species = set_species(spawns)
    if len(species) > 4:
        raise ValueError("no máximo 4 espécies por sala")
    if len(name) != 7:
        raise ValueError(f"nome do enemy set {name!r} precisa de 7 bytes")
    body = b"".join(struct.pack("<HH", ptr, pal) for ptr, pal in species)
    return name + body + b"\xFF\xFF"

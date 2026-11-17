"""Bosses of the Chozo Ruins (specs/14-chefes.md; specs/14a-plated-beetle.md) and, specs/18h, of Phendrana Drifts (the
Sheegoth's arena: specs/18h-sheegoth.md; the Thardus' = the Bomb Torizo, patched in place: specs/18k-thardus.md; epic 18's
technical decision 1: the arenas of every area here).

A boss here is a Super Metroid species stand-in placed with the room's enemies (tools/chozo/enemies.py), not one of Prime's
layer-0 enemies: Prime has it on an event layer, so check_layer0_enemies leaves it out (Species.boss) and check_bosses
(tools/validate.py) checks it instead.

Species copies (SpeciesCopy): a vanilla species header (64 bytes, $A0) copied to our free space in $A0 with a few fields
changed, so the vanilla species stays as it is wherever vanilla uses it. Everything else (AI, tiles, hitbox, health,
vulnerabilities, drops) is the source's. A copy may get its own palette (16 colours), written in the free space of the
species' own bank (the header's +$0C bank byte: the engine reads the palette from that bank, sm_a0.c:522).

14a, the Plated Beetle (Prime: the Ruined Shrine's `GarBeetle`, layer 1 "First Pass", ANCS 469111D0 character
`gar_beetle_beta`, CMDL 78A82871): the big Sidehopper ($A0:D9BF, "SIDE": 320 health, 80 a touch, tiles $600 from $AE:AA00,
palette $A3:B085) with the touch cut to 40 (epic decision 5) and the Plated Beetle's colours (epic decision 7): k-means-like
luma ramps over its Prime textures (dumped with tools/dump_prime_textures.py; the grey noise and glass-bubble textures
dropped): the verdigris armour plates and the red glowing joints.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

from frigate.bosses import Ramp, along, bgr555_to_rgb, luma, rgb_to_bgr555
from phendrana.layouts import CHAPEL_ALTAR_MISSILE
from tallon.rooms import MISSILE

from .items import BITS as ITEM_BITS, ITEMS

SPECIES_SIZE = 0x40
DAMAGE, PALETTE, BANK = 0x06, 0x02, 0x0C       # header offsets (vendor EnemyDef): touch damage, palette pointer, AI bank
HEALTH = 0x04                                  # specs/18g: health (header +4)
TOUCH, SHOT, VULN = 0x30, 0x32, 0x3C            # specs/18l: touch AI, shot AI, vulnerability table (header offsets)
VULN_SIZE = 22                                 # a vulnerability table ($B4, vendor Vulnerability)
METROID_SHOT_VANILLA = bytes.fromhex("bd7a0f8f34f47ebd7e0f8f36f47e223280a3bd8c0fd033")   # specs/18l: $A3:EF2E, read
PARTS = 0x14                                   # specs/14d: the number of parts (SpawnEnemy $A0:9275 spawns that many)

# the Plated Beetle's textures (CMDL 78A82871), pixels by brightness: the armour plates (greenish grey metal) and the
# red parts (hue < 0.06 or > 0.94, saturation > 0.45); 6 and 4 equal slices, averaged (scratchpad s14a/beetle_tex). The
# glow's last stop is not from the textures: a highlight, so the brighter browns and the eyes keep their shading
ARMOUR: Ramp = [(0, 0, 0), (22, 24, 24), (48, 52, 45), (72, 77, 64), (98, 107, 87), (131, 144, 116), (203, 211, 182)]
GLOW: Ramp = [(0, 0, 0), (46, 14, 13), (87, 25, 22), (123, 40, 33), (215, 80, 60), (255, 176, 128)]


@dataclass(frozen=True)
class SpeciesCopy:
    ptr: int                       # where the build puts the copy ($A0 offset; the vanilla 64-byte grid, $xx3F/7F/BF/FF)
    source: int                    # the vanilla species copied ($A0 offset)
    damage: int                    # its touch damage (header +6)
    recolour: tuple[Ramp, ...] = ()   # ramps by colour index group (RECOLOUR_GROUPS), empty = the source's palette
    parts: int | None = None       # specs/14d: its number of parts (header +$14), None = the source's
    health: int | None = None      # specs/18g: its health (header +4), None = the source's
    # specs/18l: its touch AI (header +$30, an address in its AI bank), None = the source's
    touch: int | None = None
    # specs/18l: its own shot AI (header +$32): code written in the free space of its AI bank, None = the source's
    shot: bytes | None = None
    # specs/18l: its own vulnerability table (header +$3C: 22 bytes written in $B4's free space), None = the source's
    vulnerability: bytes | None = None

    def palette(self, source_palette: list[int]) -> list[int]:
        """The copy's 16 colours from the source's (BGR555): each colour keeps its brightness and takes its group's ramp;
        colour 0 (transparent) stays."""
        out = list(source_palette)
        for (lo, hi), ramp in zip(RECOLOUR_GROUPS, self.recolour):
            for i in range(lo, hi + 1):
                out[i] = rgb_to_bgr555(along(ramp, luma(bgr555_to_rgb(source_palette[i]))))
        return out


# the big Sidehopper's palette ($A3:B085, the small one's too): 1-8 the shell (yellow), 9-12 the body and legs (brown),
# 13-15 the eyes (green)
RECOLOUR_GROUPS = ((1, 8), (9, 12), (13, 15))

PLATED_BEETLE = SpeciesCopy(0xF83F, 0xD9BF, 40, (ARMOUR, GLOW, GLOW))
# specs/14d: the bug hive (Kago $A0:E7FF, below) with 1 part: its header says 9 ($A0:E813), which no population load reads
# (InitializeEnemies $A0:8A9E puts one slot per entry) but SpawnEnemy ($A0:9275) does: it spawns that many slots from
# consecutive entries, and with 9 it read past the Burn Dome's list and jumped into garbage (a crash: BRK, the CPU stuck at
# $80:8573, emulator). Everything else the Kago's (touch 0, its palette): the Hive Totem's and the Burn Dome's hives use it
KAGO_COPY = SpeciesCopy(0xF87F, 0xE7FF, 0, parts=1)
# specs/18g (Phendrana's Atomic Alpha/Beta, the electric Bombu that drift toward Samus; tools/phendrana/enemies.py): the Wrecked
# Ship's orb ($A0:E9FF, "ATOMIC": 250 health, 40 a touch, $A8:E388) with health 100 (5 uncharged Power Beam shots: the
# fairness rule's most, validate.FAIR_SHOTS) and touch 20 (FAIR_TOUCH); its AI, tiles, palette and vulnerabilities the orb's
ATOMIC_COPY = SpeciesCopy(0xF8BF, 0xE9FF, 20, health=100)
# specs/18h, Phendrana's Sheegoth (the Chapel of the Elders' IceSheegoth, Prime's layer 0, ANCS EAD9FE87 character 0,
# CMDL B1DAB41D): the Dessgeega ($A0:DA3F, Maridia's big hopper: 800 health, 160 a touch, the Sidehopper's AI in $A3 with
# header +$2A = 2, its own jumps and frames, tiles $400 from $AE:D120, palette $A3:B217) with the touch cut to 40 (the
# epic's boss ceiling, validate.FAIR_BOSS_TOUCH) and the Ice Sheegoth's colours; its health (800) and its vulnerabilities
# ($B4:EC32: the Power Beam, the Wave, the Ice and the Ice + Wave do nothing, the Plasma x2, a missile x2 = 100, a charged
# shot x2 = 60) the Dessgeega's: the user's "harder copy" (epic 18, decision 4) is the Dessgeega whole, a beam-proof shell as
# Prime's Sheegoth's, won by the epic 14 rule 13 (the missiles of the round's capacity, or at most 20 charged shots:
# validate.arena_gear_fight). Ramps from its textures (s18h/sheegoth_tex, scripts/sheegoth_ramps.py: pixels of each family
# by brightness in equal slices): the shell (1-8, the Dessgeega's purple) the blue-white hide; the body (9-12, its red) the
# back's cyan crystals; the eyes (13-15, green) the eyes' glow. The last stop of each is a highlight (not in the textures)
SHEEGOTH_HIDE: Ramp = [(0, 0, 0), (46, 63, 90), (86, 112, 138), (109, 136, 162), (132, 161, 184), (156, 183, 200),
                       (188, 212, 222), (236, 246, 252)]
SHEEGOTH_CRYSTAL: Ramp = [(0, 0, 0), (8, 36, 51), (21, 73, 98), (60, 125, 152), (120, 188, 202), (210, 246, 250)]
SHEEGOTH_EYES: Ramp = [(0, 0, 0), (40, 70, 80), (88, 134, 130), (154, 239, 235), (209, 251, 247)]
SHEEGOTH = SpeciesCopy(0xF8FF, 0xDA3F, 40, (SHEEGOTH_HIDE, SHEEGOTH_CRYSTAL, SHEEGOTH_EYES))
# specs/18k, Phendrana's Thardus (the Quarantine Cave's `Thardus`, Prime's layer 3, ANCS 76C35773 character 0, CMDL CE196B36):
# the Bomb Torizo ($A0:EEFF: 800 health, 8 a touch, tiles $2000 = the room's whole enemy VRAM, AI in $AA) with its health cut
# to 400 (the epic's boss rule: 20 uncharged Power Beam shots, validate.FAIR_BOSS_SHOTS; its vulnerabilities are a common
# enemy's, $B4:F0C0); touch, AI, tiles and vulnerabilities the Torizo's. Its colours are not in its header: its code writes
# its own palettes ($AA:8687 on; TORIZO_PALETTES, recoloured in place below)
THARDUS = SpeciesCopy(0xF93F, 0xEEFF, 8, health=400)
# specs/18l, Phendrana's Metroids (Prime's MetroidAlpha, layer 0 of the Research Core and the Research Lab Aether; the epic's
# user decision 7: the SM's Metroid weakened, a copy fair by the rules, the ice freezes it). The SM's Metroid ($A0:DD7F, Tourian's:
# 500 health, 120 a touch, AI in $A3) is not fair as it is: its shot AI (Metroid_Shot $A3:EF07, sm_a3.c:3042) only knocks it
# back unless it is frozen, and then only missiles hurt it (and its vulnerability table, $B4:EF60, gives the beams 0); its
# touch AI (Metroid_Touch $A3:EDEB) latches on and drains her energy every frame until a bomb shakes it off (no ceiling per
# touch). The copy: health 100 (5 uncharged Power Beam shots, validate.FAIR_SHOTS); the common touch AI of $A3
# (Enemy_NormalTouchAI_A3 $A3:8023: the header's damage, 20 = FAIR_TOUCH, knock-back and 96 frames of invincibility: no latch,
# no drain); its shot AI = METROID_SHOT, the vanilla routine's frozen branch for every shot (the common shot AI with this
# table, then, dead, the Metroid's own end: its two sprite objects cleared, the death animation, its drops); its table the
# vanilla one with the non-ice beams (power, wave, spazer, plasma and their wave mixes) and the charged beam at x1 (2): an
# ice beam still only freezes it ($FF), and a missile (x1), a super missile (x2) or a power bomb then kill it as in Tourian.
# Its main AI (Metroid_Main: it flies at Samus, up to 3 px a frame on each axis, while on camera), init, frozen and hurt AI,
# tiles and palette are the Metroid's
METROID_SHOT_ENTRY = 0xEF2E       # Metroid_Shot's frozen branch (LDA $0F7A,X ...: X = the enemy, read from $0E54 at $EF16)
METROID_SHOT = bytes([0xAE, 0x54, 0x0E, 0x4C]) + METROID_SHOT_ENTRY.to_bytes(2, "little")   # LDX $0E54 / JMP $EF2E
METROID_VULN = bytes.fromhex("0202ffff0202ffff0202ffff0204000102020202" "0202")
METROID = SpeciesCopy(0xF97F, 0xDD7F, 20, health=100, touch=0x8023, shot=METROID_SHOT, vulnerability=METROID_VULN)
# specs/19h, the Mines' Phazon Elite (the Elite Research's `ElitePirate`, Prime's layer 1, ANCS 6B45F06D character
# Elite_Phazon_Pirate, CMDL 87BFC431; the epic's user decision 4): the SM's gold ninja pirate ($A0:F593, "BATTA2Na", Lower
# Norfair's: 1800 health, 100 a touch, tiles $1800 from $AD:C600, AI in $B2: NinjaSpacePirates_Init $B2:F5DE / _Main $F6A2,
# its claws $86:A189 = 20) with its health cut to 400 (20 uncharged Power Beam shots: the epic's boss rule, FAIR_BOSS_SHOTS) and
# its touch to 40 (FAIR_BOSS_TOUCH). Its own vulnerability table: the gold one's ($B4:EC74) with the Power, Wave, Ice and Ice +
# Wave Beams at x1 ($82: the high bit = never frozen) where the gold pirate takes none of them (its shot AI reflects them, but
# only for the vanilla species: WalkingSpacePirates_87C8 $B2:87C8 compares the pointer with $F593; a copy gets the common shot
# AI, NormalEnemyShotAi, and so the drop of 5 items of WalkingSpacePirates_8789 neither). Its code reads no area, no room and no
# wall: it leaps between two x of its population entry (NinjaSpacePirates_Init: parameter 2 = the span, parameter 1 bit 0 = it
# starts at the west end), its y the spawn's (the vanilla room $8F:B62B is 3 screens wide). Colours (s19h/scripts/elite_ramps.py,
# its textures in s19h/elite_tex: pixels of each family by brightness in equal slices, the last stop a highlight): the gold
# ninja's palette ($B2:8707: 1-8 its grey-white armour, 9-12 its pinkish joints, 13-15 its gold trim) -> the grey armour, the
# phazon blue of its veins, the phazon glow (a first try with the lilac flesh on 9-12 showed no blue at all: s19h/emu/zoom.png). Its other palette (sprite line 7: the init copies 16 colours from $B2:8727, kWallSpacePirates_
# Palette_3, and its leaps show it, SpacePirates_Instr_20 $B2:F536 with $0E00; $0200 = line 1 again: its enemy-set palette must be
# 1): the init's operand points at a copy in $B2's free space with 1-8 the phazon glow (NINJA_LINE7, patched in place: no room of
# ours has a vanilla ninja; $B2:8727 stays, the palette of 2 vanilla pirates)
ELITE_ARMOUR: Ramp = [(0, 0, 0), (46, 47, 46), (82, 84, 83), (100, 104, 104), (116, 120, 120), (143, 143, 143), (182, 181, 183),
                      (232, 232, 236)]
ELITE_PHAZON: Ramp = [(0, 0, 0), (11, 39, 79), (25, 64, 103), (42, 93, 127), (65, 122, 153), (99, 158, 180), (190, 240, 255)]
ELITE_GLOW: Ramp = [(0, 0, 0), (25, 64, 103), (65, 122, 153), (99, 158, 180), (150, 215, 240), (225, 250, 255)]
NINJA = 0xF593
ELITE_VULN = bytes.fromhex("82828282818181818282828202040000000000028000")
PHAZON_ELITE = SpeciesCopy(0xF9BF, NINJA, 40, (ELITE_ARMOUR, ELITE_PHAZON, ELITE_GLOW), health=400,
                           vulnerability=ELITE_VULN)
# specs/19k, the Mines' Omega Pirate (the Elite Quarters' `OmegaPirate`, Prime's layer 5 "Omega Pirate Battle"; the epic's user
# decision 4): the Bomb Torizo again ($A0:EEFF, as the Thardus: its code patched in place, the area read as 0, TORIZO_SPOT), with
# its health 1200 and its own vulnerability table: the Torizo's ($B4:F0C0) with the 12 uncharged beams at $80 (no damage, never
# frozen: Prime's Omega's armour takes no beam), a missile x1 (100: 12 missiles), a super missile x2, a power bomb x1 (Prime's
# weak spots take the Power Bomb), a charged shot x1 (byte 19: the charged Power Beam's 60, 20 shots = FAIR_BOSS_SHOTS); touch 8
# and its projectiles the Torizo's. Its colours: the Torizo's palette loads choose by the area (TORIZO_AREA_LOADS, omega_patches)
OMEGA_VULN = bytes.fromhex("80808080808080808080808002040002000000020000")
OMEGA = SpeciesCopy(0xF9FF, 0xEEFF, 8, health=1200, vulnerability=OMEGA_VULN)
# specs/20h, the Impact Crater's Metroid Prime (the Metroid Prime Lair's `MetroidPrimeStage2`, Prime's layer 0; its first stage,
# `MetroidPrimeStage1`, is in the Subchambers, which are a descent here: epic 20, user decision 3, one arena in the Lair on the
# Omega Pirate's model): the Bomb Torizo a third time ($A0:EEFF, as the Thardus and the Omega: its code patched in place, the area
# read as 0, TORIZO_SPOT), its health 3000 (Prime's health and attacks were not read, specs/20a: our choice, the game's last
# fight above the Omega's 1200) and the Torizo's own vulnerability table ($B4:F0C0: every uncharged beam x1, a missile x1, a
# super missile x2, a charged shot x1: Prime's exoskeleton takes the beams and the missiles; specs/20a measured a DamageableTrigger
# of the first stage with the Power Beam's weakness): 30 missiles, or 150 uncharged Power Beam shots, or 10 shots of the
# Plasma + Ice + Wave Beam (300); touch 8 and its projectiles the Torizo's (its swipe, orbs and sonic boom: the attacks). Its
# colours: the Torizo's palette loads choose by the area (omega_selector): outside the Mines, the Thardus' (no Prime texture
# dumped: a question to the user, specs/20h)
METROID_PRIME = SpeciesCopy(0xFA3F, 0xEEFF, 8, health=3000)
COPIES: dict[int, SpeciesCopy] = {c.ptr: c for c in (PLATED_BEETLE, KAGO_COPY, ATOMIC_COPY, SHEEGOTH, THARDUS, METROID,
                                                     PHAZON_ELITE, OMEGA, METROID_PRIME)}


@dataclass(frozen=True)
class Boss:
    room: str          # the built room
    kind: str          # its stand-in kind (tools/frigate/enemies.py SPECIES, boss=True)
    prime: str         # Prime's object (MREA script)
    prime_layer: int   # the Prime layer it is on
    shots: int         # uncharged Power Beam shots that kill it (checked against its header: health / damage a shot)
    lock: bool         # does the fight shut a door? (the Plated Beetle's: no, Prime has no Actor Door Lock there)


BOSSES: list[Boss] = [
    # specs/14a: Prime's layer 1 "First Pass" of the Ruined Shrine (P9): GarBeetle + its Master Beetle Generator, the 7 Alpha
    # Beetles of layer 0 (3 small Sidehoppers here, 12h); no Actor Door Lock in the room
    Boss("chozo_ruined_shrine", "plated_beetle", "GarBeetle", 1, 16, False),
]


def build_copies(rom, bank_a0, banks: dict[int, object]) -> list[int]:
    """Write every species copy: its palette (if recoloured) in the free space of its bank (`banks`: bank -> Allocator),
    then its header on the 64-byte grid of $A0 at the address the table declares. Returns the headers' addresses."""
    out = []
    for c in COPIES.values():
        src = 0xA00000 | c.source
        header = bytearray(rom.read(src, SPECIES_SIZE))
        header[DAMAGE:DAMAGE + 2] = c.damage.to_bytes(2, "little")
        if c.parts is not None:
            header[PARTS:PARTS + 2] = c.parts.to_bytes(2, "little")
        if c.health is not None:   # specs/18g
            header[HEALTH:HEALTH + 2] = c.health.to_bytes(2, "little")
        if c.touch is not None:   # specs/18l
            header[TOUCH:TOUCH + 2] = c.touch.to_bytes(2, "little")
        if c.shot is not None:   # specs/18l: its code in the free space of its AI bank (the vanilla code it jumps into checked)
            if c is METROID and rom.read(0xA30000 | METROID_SHOT_ENTRY, len(METROID_SHOT_VANILLA)) != METROID_SHOT_VANILLA:
                raise RuntimeError(f"bytes inesperados em $A3:{METROID_SHOT_ENTRY:04X} (o ramo congelado do Metroid_Shot)")
            header[SHOT:SHOT + 2] = (banks[header[BANK]].put(c.shot) & 0xFFFF).to_bytes(2, "little")
        if c.vulnerability is not None:   # specs/18l: its table in $B4
            if len(c.vulnerability) != VULN_SIZE:
                raise RuntimeError(f"cópia ${c.ptr:04X}: tabela de vulnerabilidade com {len(c.vulnerability)} bytes")
            header[VULN:VULN + 2] = (banks[0xB4].put(c.vulnerability) & 0xFFFF).to_bytes(2, "little")
        if c.recolour:
            bank = header[BANK]
            pal_at = (bank << 16) | int.from_bytes(header[PALETTE:PALETTE + 2], "little")
            colours = c.palette([rom.u16(pal_at + 2 * i) for i in range(16)])
            new = banks[bank].put(b"".join(v.to_bytes(2, "little") for v in colours))
            header[PALETTE:PALETTE + 2] = (new & 0xFFFF).to_bytes(2, "little")
        bank_a0.ptr += (0x3F - bank_a0.ptr) % 0x40      # the vanilla grid, as the Meta Ridley's copy
        at = bank_a0.put(bytes(header))
        if at != 0xA00000 | c.ptr:
            raise RuntimeError(f"cópia da espécie ${c.source:04X} em ${at:06X}, a tabela diz $A0:{c.ptr:04X}")
        out.append(at)
    return out


# --- specs/14b: arenas (a fight of several SM enemies, or a boss, whose end the game notices) --------------------------------
# One routine in $84 serves every arena (epic 14, "Mudança proposta"): the alive state's main ASM (5 bytes in $8F: JSL + RTS,
# shared by every arena) calls it each frame; it finds the current room ($079B) in its table and, while the arena's boss bit
# is clear, checks the arena's condition; when it holds, it sets the bit (SetBossBitForCurArea $80:81A6), stops the fight's
# music (QueueMusic $80:8FC1 with 0, as LoadRoomMusic $82:E071 does before a song set: the room is silent until Samus leaves
# it; queuing the area's song set back stops the game ~40 frames while it uploads, measured, scratchpad s14b) and spawns
# the prize's PLM (SpawnRoomPLM $84:846A, the room's own entry in its dead state's PLM list). The room's header picks the dead
# state by that bit (condition E629, as the Parasite Queen's): no boss kinds in its population, the area's music, no main ASM,
# the prize in its PLM list (taken: the item PLM sees its bit and goes, vanilla).
KILLS, SLOT, BOSS_BIT, ITEM = 0, 1, 2, 3
# conditions: KILLS = the room's kills reached its population's quota ($0E50 >= $0E52, the quota the population's last byte
# sets: sm_a0.c:423, and the vanilla grey door type 3 compares); SLOT = an enemy slot ($0F78 + arg) emptied (its species
# pointer 0: the enemy died); BOSS_BIT = a boss bit of the area (arg = its mask: a boss of the SM that sets its own, as the
# Spore Spawn's $02, 14c); ITEM (specs/14d, the Incinerator Drone) = a fight that STARTS when an item is taken (arg = its
# bit: $7ED870 + bit / 8) and is won by the kills: the alive state's population has the quota 0 (sm_a0.c:423: $0E52 = 0,
# "not started"); while $0E52 is 0 the routine waits for the item; taken, it starts the fight from the entry's fight record
# (FIGHT_RECORD, in $84): $0E52 = the record's quota (every enemy of the room that can die, the spawned ones too), the
# fight's song queued (a track of the alive state's song set: no upload, no freeze), the door's grey cap spawned
# (SpawnRoomPLM, a $8F entry: type 3, the kill count, $84:BE01), the arena's enemies spawned (SpawnEnemy $A0:9275, DB = $84:
# 16-byte population entries in the record; graphics from the room's enemy set); from then on $0E52 is not 0 and the arena
# is a KILLS one (the grey cap's own pre-instruction opens it on the same count). $0E52 is per room visit (each load sets it
# from the population): a reload with the item taken and the bit off (never by play: the door is shut until the win and no
# save station is inside) starts the fight again.
ROUTINE = 0x84F500            # in $84's free range $84:F4FB-FFBA (only $FF in the base and the build: epic 14, "Espaço")
# room header (2), condition (1), argument (2), bit (1), prize PLM entry in $8F (2), music (2), fight record in $84 (2, ITEM)
ENTRY_SIZE = 12
MUSIC_STOP, MUSIC_KEEP = 0x0000, 0xFFFF   # the entry's music: queued when the arena is won ($FFFF: none)
MINI_BOSS_MUSIC = (0x2A, 0x05)   # the SM's mini-boss song (Spore Spawn's and Botwoon's rooms, $8F:9DD9 / $8F:D970)
# specs/14d: an ITEM arena's alive state loads the mini-boss song set with track 3 (as the vanilla Bomb Torizo's room, $8F:9804:
# its default state is song set $24 track $03, and the statue's waking queues track 5, Torizo_Instr_42 $AA:CAE2; the Spore
# Spawn's death queues 3 in set $2A, $A5); the fight queues track 5 (the mini-boss song) when it starts
WAITING_MUSIC, FIGHT_SONG = (0x2A, 0x03), 0x05
SPAWN_ENEMY, SPAWN_ROOM_PLM = 0xA09275, 0x84846A   # SpawnEnemy (X = population entry, DB its bank), SpawnRoomPLM (X, $8F)
GREY_DOOR_KILLS = 0x8000 | (3 << 10)   # the grey cap of type 3 (kill count, $84:BE01), no "opened" bit
KAGO = 0xE7FF                 # the bug hive ("KAGO"): its shot AI ($A8:AB83) counts hits down from parameter 1 and dies
                              # below 0, whatever its health (1600): parameter 1 + 1 hits; each hit spawns a bug ($86:D02E)
KAGO_SHOT, KAGO_COUNT = 0xA8AB83, bytes.fromhex("bf08787e38e901009f08787e1010")   # LDA $7E7808,X / SEC / SBC #1 / STA / BPL
KAGO_BUG = 0x86D02E           # the bug's projectile header: damage = properties ($+8) & $0FFF
KAGO_HITS = 5                 # parameter 1 = 4 (vanilla $000A = 11 hits): two hives and the 3 wasps die in 16 Power Beam shots


@dataclass(frozen=True)
class Arena:
    room: str                  # the built room
    bit: int                   # our boss bit of the area ($08-$80: the SM uses $01, $02, $04)
    condition: int             # KILLS, SLOT, BOSS_BIT or ITEM
    arg: int                   # SLOT: the enemy slot's offset ($40 a slot); BOSS_BIT: the mask; ITEM: the item bit
    prize: tuple[str, tuple[int, int]] | None   # the item (room, spot) of chozo/items.py the routine spawns, None = none
    needs: frozenset           # the gear the fight needs (tallon/rooms.py gate items); empty = the Power Beam
    prime: str                 # Prime's objects
    music: tuple[int, int] = MINI_BOSS_MUSIC   # the alive state's (the area's in the dead one)
    fight_song: int | None = None   # ITEM: the track queued when the fight starts (of the alive state's song set)


def item_bit(room: str, spot: tuple[int, int]) -> int:
    """The item bit of the Chozo item placed at (room, spot) (chozo/items.py)."""
    return next(ITEM_BITS[n] for n, it in enumerate(ITEMS) if (it.room, it.spot) == (room, spot))


ARENAS: list[Arena] = [
    # specs/14b, the Hive Mecha (Prime's Hive Totem, P36: `Actor - Totem` with 4 stages, 3 War Wasp generators, the Missile
    # Launcher after it; no Actor Door Lock): 2 bug hives (Kago) under the combs and the 3 wasps (Mella, 12i); all dead: the
    # missile appears on top of the totem (bit $C2, round 0); no door shuts (epic decision 4)
    Arena("chozo_hive_totem", 0x08, KILLS, 0, ("chozo_hive_totem", (23, 8)), frozenset(), "Actor - Totem (Hive Mecha)"),
    # specs/14b, the Plated Beetle (14a) gets the mini-boss music while it lives (epic decision 7): its slot emptied (the
    # 4th, after the 3 small ones) sets the bit; nothing to spawn (it guards nothing in Prime)
    Arena("chozo_ruined_shrine", 0x20, SLOT, 3 * 0x40, None, frozenset(), "GarBeetle (Plated Beetle)"),
    # specs/14c, Flaahgra (Prime's Sunchamber, P37: `Flaahgra` + 4 tentacles and 4 bomb slots on layer 1, "Flaahgra Dead" ->
    # "Relay Activate Suit Pickup"; an Actor Door Lock on its door to the Sun Tower Access): the Spore Spawn, which sets the
    # SM's mini-boss bit of the area ($02, $A5:EE1D: area 1 = $7ED829, measured, epic E1) when it dies; that bit is the
    # condition (BOSS_BIT), the arena's own bit is $40 (the routine stops once its bit is set: it cannot be $02 too); the
    # Varia Suit appears (bit $BC, round 2). It takes no Power Beam shot (SPORE_SPAWN_SHOT): the fight needs missiles (or a
    # charged shot: validate.check_arenas weighs both with the arrival's gear). The door to the Sun Tower Access is the
    # grey mini-boss door (chozo/rooms.py BOSS_DOORS: type 1 opens on the bit $02).
    Arena("chozo_sunchamber", 0x40, BOSS_BIT, 0x02, ("chozo_sunchamber", (8, 43)), frozenset({MISSILE}), "Flaahgra"),
    # specs/14d, the Incinerator Drone (Prime's Burn Dome, P48: `ActorContraption` + its eye, 4 stages, 7 `Actor Hive`, a War
    # Wasp generator; taking the Bombs starts it; an Actor Door Lock on its only door, to the Burn Dome Access): epic decision 6
    # (the user's), an arena that starts when Samus takes the missile on the stand (Prime's Bombs, bit $CC, round 1): the door
    # shuts (a grey cap of type 3: chozo/rooms.py BOSS_DOORS), 2 bug hives (Kago) under the roof's combs and 2 wasps (Mella)
    # spawn (chozo/enemies.py: the boss kinds of the room), the mini-boss song starts; all dead (with the Mella that was there
    # before: the room's kill count), the door opens, the song stops, the bit $10 (reserved for it since 14b). No prize: the
    # missile is the trigger. Won with the Power Beam (16 shots, the Hive Mecha's numbers).
    Arena("chozo_burn_dome", 0x10, ITEM, item_bit("chozo_burn_dome", (23, 10)), None, frozenset(),
          "ActorContraption (Incinerator Drone)", WAITING_MUSIC, FIGHT_SONG),
    # specs/18h, the Sheegoth (Prime's Chapel of the Elders, Phendrana P14: `IceSheegoth` + 4 `Babygoth` on layer 0, the Wave
    # Beam after it; an Actor Door Lock on its only door, to the Chapel Tunnel): the Dessgeega copy (SHEEGOTH) and 2 small
    # Sidehoppers (the Babygoths, tools/phendrana/enemies.py); all dead (the kill count): the bit $08 of area 4 (Phendrana's
    # first, the SM's Maridia uses $01 and $02), the door's grey cap of type 3 opens on the same count (phendrana/rooms.py
    # BOSS_DOORS: a wave door again in the dead state), the missile where Prime has the Wave Beam (epic 18, decision 3: the
    # Wave is the Tallon's) appears on the altar. Won with missiles (the Dessgeega's shell takes no uncharged beam: needs)
    Arena("phendrana_chapel_of_the_elders", 0x08, KILLS, 0, ("phendrana_chapel_of_the_elders", CHAPEL_ALTAR_MISSILE), frozenset({MISSILE}),
          "IceSheegoth + Babygoth (Sheegoth)"),
    # specs/18k, the Thardus (Prime's Quarantine Cave, Phendrana P24: `Thardus` and its rocks on layer 3, the Spider Ball after
    # it; an Actor Door Lock on its two doors, to the North and the South Quarantine Tunnels): the Bomb Torizo's copy (THARDUS),
    # the statue that wakes as the room loads, alone in the arena (its tiles take the whole enemy VRAM); its death sets the
    # Torizo's boss bit of the area ($04, Torizo_Instr_38 $AA:B24D: area 4 = $7ED82C), which is the condition (BOSS_BIT, as
    # Flaahgra's $02) and opens the doors' grey caps of type 2 ($84:BDF2, the vanilla Torizo door: phendrana/rooms.py
    # BOSS_DOORS; wave doors again in the dead state); the arena's own bit is $10 (reserved for it by the epic). No prize
    # (epic 18, decision 3: the Spider Ball has no SM item). The vanilla Torizo room's music (song set $24, track 3: the
    # Torizo's own code queues its waking and fight tracks of that set, TORIZO_MUSIC). Won with the Power Beam (20 shots)
    Arena("phendrana_quarantine_cave", 0x10, BOSS_BIT, 0x04, None, frozenset(), "Thardus", music=(0x24, 0x03)),
    # specs/19h, the Phazon Elite (Prime's Elite Research, Mines P13: `ElitePirate` on layer 1, out of its tank; an Actor Door
    # Lock on its door to the Security Access B, the ceiling one): the gold ninja pirate's copy (PHAZON_ELITE) alone; dead (the
    # kill count, 1): the bit $08 of area 5 (the Mines' first; the SM's Tourian uses $01 and $02), the ceiling door's grey cap of
    # type 3 opens on the same count (mines/rooms.py BOSS_DOORS: an ice door again in the dead state); no prize (epic 19, user
    # decision 4: the Warrior artifact has no SM item). Won with the Power Beam (20 shots)
    Arena("mines_elite_research", 0x08, KILLS, 0, None, frozenset(), "ElitePirate (Phazon Elite)"),
    # specs/19k, the Omega Pirate (Prime's Elite Quarters, Mines P26: `OmegaPirate` on layer 5 with its 8 pirates and 9 healing
    # nodes, out here; an Actor Door Lock on its two doors, to the Processing Center Access and the Elite Quarters Access): the
    # Bomb Torizo's copy (OMEGA) alone, the Thardus' way (18k): it wakes as the room loads, its death sets the Torizo's bit $04 of
    # area 5 (the condition; vanilla's area-5 rooms use $04 only in orphan rooms' grey doors, validate.MINES_VANILLA_BOSS_BITS),
    # which opens the two doors' grey caps of type 2 (plasma doors again in the dead state); the arena's own bit $10 (reserved by
    # the epic). No prize (the Phazon Suit has no SM item). The Torizo's music. Won with missiles (no uncharged beam hurts it)
    Arena("mines_elite_quarters", 0x10, BOSS_BIT, 0x04, None, frozenset({MISSILE}), "OmegaPirate (Omega Pirate)",
          music=(0x24, 0x03)),
    # specs/20h, Metroid Prime (Prime's Metroid Prime Lair, Impact Crater P11: `MetroidPrimeStage2` with its Phazon Pool and the
    # Metroids it spawns, out here; no door at all in Prime: the Lair is the bottom of the fall): the Bomb Torizo's third copy
    # (METROID_PRIME) alone, the Omega's way (19k): it wakes as the room loads, its death sets the Torizo's bit $04 of area 0 (the
    # condition: no room of ours in area 0 waits for it, validate.check_impact_boss), which opens the grey cap of type 2 on the
    # Lair's only door, the ceiling one back up to the Subchamber Five (epic 20, decision 3: the doors shut until the win;
    # impact/rooms.py BOSS_DOORS); the arena's own bit $10 of area 0 = the game's "final boss beaten" (specs/20i's ending reads
    # it). No prize. The Torizo's music. Won with missiles (30 of the 235 of round 6) or the beams (it takes them, unlike the Omega)
    Arena("impact_lair", 0x10, BOSS_BIT, 0x04, None, frozenset({MISSILE}), "MetroidPrimeStage2 (Metroid Prime)",
          music=(0x24, 0x03)),
]


def arena_of(room: str) -> Arena | None:
    return next((a for a in ARENAS if a.room == room), None)


def stub() -> bytes:
    """The alive state's main ASM (in $8F, run by RunRoomMainCode $8F:E8BD with JSR): JSL ROUTINE / RTS."""
    return b"\x22" + ROUTINE.to_bytes(3, "little") + b"\x60"


def _assemble(at: int, code: list) -> bytes:
    """Bytes and ("label",) / ("br", opcode, label) items: branches resolved (8-bit relative)."""
    labels, pos = {}, 0
    for c in code:
        if isinstance(c, str):
            labels[c] = pos
        else:
            pos += 2 if isinstance(c, tuple) else len(c)
    out = bytearray()
    for c in code:
        if isinstance(c, str):
            continue
        if isinstance(c, tuple):
            rel = labels[c[1]] - (len(out) + 2)
            if not -128 <= rel <= 127:
                raise ValueError(f"desvio longe demais para {c[1]}")
            out += bytes([c[0], rel & 0xFF])
        else:
            out += c
    return bytes(out)


def routine(table: int) -> bytes:
    """The arena routine (at ROUTINE), its table at `table` ($84). 16-bit registers, DB = $84 (WRAM's first 8 KB is mirrored
    there: $079B, $0E50, $0E52, $0F78). SetBossBit/CheckBossBit and QueueMusic keep X and Y; SpawnRoomPLM keeps them too
    (PHY/PHX ... PLX/PLY); SpawnEnemy does not: Y is pushed around it."""
    t = table & 0xFFFF
    return _assemble(ROUTINE, [
        bytes.fromhex("08c2308b4bab"),                     # PHP / REP #$30 / PHB / PHK / PLB
        b"\xa2" + t.to_bytes(2, "little"),                  # LDX #table
        "loop", bytes.fromhex("bd0000"), (0xF0, "done"),    # LDA $0000,X (room) / BEQ done (end of the table)
        bytes.fromhex("cd9b07"), (0xF0, "found"),           # CMP $079B / BEQ found
        bytes.fromhex("8a1869") + ENTRY_SIZE.to_bytes(2, "little") + b"\xaa", (0x80, "loop"),   # TXA / CLC / ADC #size / TAX
        "found", bytes.fromhex("bd050029ff00"),             # LDA $0005,X / AND #$00FF (the bit)
        bytes.fromhex("22dc8180"), (0xB0, "done"),          # JSL CheckBossBitForCurArea / BCS done (set: dead already)
        bytes.fromhex("bd020029ff00"), (0xD0, "other"),     # LDA $0002,X / AND #$00FF / BNE other
        "kills", bytes.fromhex("ad500ecd520e"), (0x90, "done"), (0x80, "win"),   # KILLS: LDA $0E50 / CMP $0E52 / BCC / BRA win
        "other", b"\x3a", (0xD0, "bit"),                    # DEC / BNE bit
        bytes.fromhex("bc0300b9780f"), (0xD0, "done"), (0x80, "win"),   # SLOT: LDY $0003,X / LDA $0F78,Y / BNE done / BRA win
        "bit", b"\x3a", (0xD0, "item"),                     # DEC / BNE item
        bytes.fromhex("bd030022dc8180"), (0x90, "done"), (0x80, "win"),   # BOSS_BIT: LDA $0003,X / JSL CheckBossBit / BCC done
        "win", bytes.fromhex("bd050029ff00"), bytes.fromhex("22a68180"),   # LDA $0005,X / AND #$00FF / JSL SetBossBit
        bytes.fromhex("bd0800c9ffff"), (0xF0, "plm"),       # LDA $0008,X (the music to queue) / CMP #$FFFF / BEQ plm
        bytes.fromhex("22c18f80"),                          # JSL QueueMusic
        "plm", bytes.fromhex("bd0600"), (0xF0, "done"),     # LDA $0006,X (the prize's PLM entry, $8F) / BEQ done
        bytes.fromhex("aa22 6a8484".replace(" ", "")),       # TAX / JSL SpawnRoomPLM
        "done", bytes.fromhex("ab286b"),                    # PLB / PLP / RTL
        # ITEM (after the end: the short branches above reach `done`)
        "item", bytes.fromhex("ad520e"), (0xD0, "kills"),   # ITEM: LDA $0E52 / BNE kills (started: the quota is set)
        bytes.fromhex("dabd030048 29ff00 aa 68 eb 3f70d87e fa 29ff00".replace(" ", "")),
        # PHX / LDA $0003,X (byte | mask << 8) / PHA / AND #$FF / TAX / PLA / XBA / AND $7ED870,X / PLX / AND #$FF
        # (the AND after the PLX: PLX sets Z by X)
        (0xF0, "done"),                                      # BEQ done (not taken)
        bytes.fromhex("bc0a00"),                            # LDY $000A,X (the fight record)
        bytes.fromhex("b900008d520e"),                      # LDA $0000,Y / STA $0E52 (the quota: started)
        bytes.fromhex("b9020022c18f80"),                    # LDA $0002,Y / JSL QueueMusic (the fight's song)
        bytes.fromhex("b90400aa22") + SPAWN_ROOM_PLM.to_bytes(3, "little"),   # LDA $0004,Y / TAX / JSL SpawnRoomPLM (the cap)
        bytes.fromhex("98186906 00a8".replace(" ", "")),     # TYA / CLC / ADC #6 / TAY (the first enemy entry)
        "spawn", bytes.fromhex("b90000"), (0xF0, "awake"),  # LDA $0000,Y / BEQ awake (the list's end)
        bytes.fromhex("5abb22") + SPAWN_ENEMY.to_bytes(3, "little") + b"\x7a",   # PHY / TYX / JSL SpawnEnemy / PLY
        bytes.fromhex("98186910 00a8".replace(" ", "")), (0x80, "spawn"),   # TYA / CLC / ADC #16 / TAY / BRA spawn
        # every enemy of the room (the spawned ones and those of before) processed off the camera too (properties $0800,
        # DetermineWhichEnemiesToProcess $A0:8EB6): a wasp (Mella) has no collision with the room and drifts a step a dart
        # (Flies_6/Flies_7, $A2:B1AA); one that left the camera froze there for good (emulator: under the floor, the fight
        # unwinnable behind the shut door). Processed, it keeps darting at Samus' height
        "awake", bytes.fromhex("a2c007"),                   # LDX #$07C0 (the last slot)
        "slot", bytes.fromhex("bd780f"), (0xF0, "next"),    # LDA $0F78,X / BEQ next (empty)
        bytes.fromhex("bd860f090008 9d860f".replace(" ", "")),   # LDA $0F86,X / ORA #$0800 / STA $0F86,X
        "next", bytes.fromhex("8a38e94000aa"), (0x10, "slot"),   # TXA / SEC / SBC #$40 / TAX / BPL slot
        (0x80, "done"),                                      # BRA done
    ])


def table_arg(a: Arena) -> int:
    """The table's argument word: ITEM's bit as its byte in $7ED870 and its mask (byte | mask << 8), the others as they are."""
    return (a.arg >> 3) | (1 << (a.arg & 7)) << 8 if a.condition == ITEM else a.arg


def table_entry(room_header: int, a: Arena, plm_entry: int, record: int = 0) -> bytes:
    return struct.pack("<HBHBHHH", room_header & 0xFFFF, a.condition, table_arg(a), a.bit, plm_entry & 0xFFFF, MUSIC_STOP,
                       record & 0xFFFF)


def fight_record(a: Arena, quota: int, door_entry: int, spawned: list[bytes]) -> bytes:
    """specs/14d, an ITEM arena's fight record ($84, after the table): the quota (the room's enemies that can die, the
    spawned ones too), the fight's song, the door cap's PLM entry ($8F), then the spawned enemies' 16-byte population
    entries and a 0 word."""
    if a.condition != ITEM or a.fight_song is None or not spawned or not 0 < quota < 0x100:
        raise RuntimeError(f"{a.room}: registro de luta de uma arena que não é ITEM, sem canção, sem inimigos ou cota {quota}")
    return struct.pack("<HHH", quota, a.fight_song, door_entry & 0xFFFF) + b"".join(spawned) + b"\x00\x00"


# --- specs/14c: Flaahgra = the Spore Spawn ($A0:DF3F, AI in $A5), patched in place ------------------------------------------
# No other room of ours uses the Spore Spawn (its vanilla room, $8F:9DC7, is an orphan: specs/11), so its tables are changed
# where they are (a species copy would not help: its code reads its palettes from fixed addresses).
SPORE_SPAWN = 0xDF3F
MINI_BOSS_BIT = 0x02          # the SM's mini-boss bit, the one SporeSpawn_Func_6 ($A5:EDF3) sets: area 1 = $7ED829 bit 1
# SporeSpawn_Shot ($A5:ED5A): only a projectile of type & $0700 (missile, super missile, bomb) or a charged beam ($0010)
# reaches the damage routine; the uncharged Power Beam never hurts it (epic E1)
SPORE_SPAWN_SHOT = 0xA5ED5A
SPORE_SPAWN_SHOT_CODE = bytes.fromhex("ada6180aaabd180c890007d006891000d0016b")
# its palettes (16 colours each): the body's at init (sprite line 7, $A5:E359), the body's by health (sprite line 9: 4 rows,
# $A5:E379, SporeSpawn_Func_7 $A5:EE4A) and the death's fade (sprite line 9: 8 rows, $A5:E3F9, Draygon_Instr_29/19 $A5:E8CA
# / $E91C); the same fade repaints BG lines 4 and 7 (7 rows each: $A5:E4F9 -> line 4, $A5:E5D9 -> line 7), vanilla's room
# withering: our line 7 is the ruins' sandstone (smlib/ruins.py), and it went dark brown (epic E1). Here every row of those
# two tables is the ruins' own line (build: the tileset's palette as written), so the death leaves the room's colours
SPORE_SPAWN_SPRITE_PALETTES = ((0xA5E359, 1), (0xA5E379, 4), (0xA5E3F9, 8))   # (table, rows)
SPORE_SPAWN_DEATH_BG = ((0xA5E4F9, 4, 7), (0xA5E5D9, 7, 7))                    # (table, BG palette line, rows)
# SporeSpawn_Init ($A5:EA2A) sets the scroll hook Samus_ScrollFinishedHook_SporeSpawnFight ($90:9589: the camera kept at
# y >= 464 during the fight, vanilla's room shows nothing of its shaft): `LDA #$9589 / STA $07E9` at $A5:EAD7. The
# Sunchamber's zigzag up to the L0 door rises over the pit (layouts.sunchamber): with the hook Samus climbing it during the
# fight went over the top of the screen. Patched to no hook (LDA #$0000): the camera follows her as in any room.
SPORE_SPAWN_HOOK = 0xA5EAD7
SPORE_SPAWN_HOOK_VANILLA, SPORE_SPAWN_HOOK_OURS = bytes.fromhex("a989958de907"), bytes.fromhex("a900008de907")
# its fixed spots (bytes, base ROM): the death's position ($A5:E87C: LDA #$0080 / STA $0F7A / LDA #$0270 / STA $0F7E = (128,
# 624), the spot of frigate/enemies.py's "flaahgra") and the roof's PLM at its death ($A5:EE41: JSL SpawnHardcodedPlm $84:83D7,
# db 07 1E, dw $B78F: the 2x2 blocks at (7, 30) to air; $A5:EAB3 the same with $B793 when the room loads with it dead)
SPORE_SPAWN_DEATH_SPOT = (0xA5E87C, bytes.fromhex("a980008d7a0fa970028d7e0f"))
SPORE_SPAWN_DEATH_PLM = (0xA5EE41, bytes.fromhex("22d78384071e8fb7"))
SPORE_SPAWN_ROOF = (7, 30, 8, 31)       # the blocks those PLMs clear (layouts.SUNCHAMBER_NOTCH must leave them air)
SPORE_SPAWN_POPULATION = 0xA1A0FD     # its vanilla placement (16 bytes): frigate/enemies.py "flaahgra" copies its values
# what hurts Samus in the fight besides its touch: its spores ($86:DE7A), its stalk's pieces ($86:DE6C) and the spores'
# spawners ($86:DE88) (projectile headers: damage = properties (+8) & $0FFF)
SPORE_SPAWN_EPROJS = (0x86DE7A, 0x86DE6C, 0x86DE88)
# Samus' projectile damage (bank $93, InitializeProjectile $93:8000): the non-beam table ($93:83F1, index = type >> 8: 1 =
# the missile) and the charged beams' ($93:83D9, index = the beam bits: 0 = the charged Power Beam); each entry points at a
# projectile header whose first word is its damage. A hit takes (damage >> 1) x the target's vulnerability multiplier
# (NormalEnemyShotAiSkipDeathAnim $A0:A6DE: the missile's byte 12 & $7F; a charged shot the byte 19's low nibble)
DAMAGE_TABLES = {"missile": (0x9383F1, 1, 12), "charge": (0x9383D9, 0, 19)}   # (table, index, vulnerability byte)
# Flaahgra's colours (Prime, CMDL EC81CD52 of the Sunchamber's `Flaahgra` object, ANCS BF5F05CD character
# Plant_Boss_Creature; textures dumped with tools/dump_prime_textures.py, scratchpad s14c/flaahgra_tex): pixels by hue family,
# sorted by brightness, averaged in 6 equal slices (s14c/scripts/flaahgra_ramps.py): the olive-green plates and leaves, the
# cream vertebrae, the red-pink gills. The last stop of each is a highlight (not in the textures), so the Spore Spawn's
# lighter shades keep their shading
FL_GREEN: Ramp = [(0, 0, 0), (34, 39, 21), (54, 62, 39), (68, 78, 53), (79, 91, 64), (91, 103, 72), (113, 123, 88),
                  (176, 188, 138)]
FL_BONE: Ramp = [(0, 0, 0), (132, 111, 84), (162, 129, 89), (174, 142, 98), (184, 156, 106), (193, 168, 120), (212, 190, 154),
                 (240, 228, 200)]
FL_FLESH: Ramp = [(0, 0, 0), (33, 12, 14), (57, 24, 28), (74, 34, 35), (90, 44, 42), (109, 56, 52), (143, 80, 78),
                  (236, 150, 140)]
# the Spore Spawn's palette ($A5:E359, read): 1-8 the shell's greens, 9-12 the stalk and the core's frame (cream to olive),
# 13-15 the core (yellow, orange, red-brown)
SPORE_SPAWN_GROUPS = (((1, 8), FL_GREEN), ((9, 12), FL_BONE), ((13, 15), FL_FLESH))


def flaahgra_colours(row: list[int]) -> list[int]:
    """A row of the Spore Spawn's sprite palettes in Flaahgra's colours: each colour keeps its brightness and takes its group's
    ramp; colour 0 (transparent) stays."""
    out = list(row)
    for (lo, hi), ramp in SPORE_SPAWN_GROUPS:
        for i in range(lo, hi + 1):
            out[i] = rgb_to_bgr555(along(ramp, luma(bgr555_to_rgb(row[i]))))
    return out


def spore_spawn_patches(base, bg_palette: bytes) -> list[tuple[int, bytes]]:
    """(address, bytes) of the Spore Spawn's patches, from the base ROM `base` and the ruins' tileset palette as the build
    writes it (`bg_palette`, 8 lines of 16 BGR555 colours): its sprite palettes in Flaahgra's colours, the death's BG rows =
    the ruins' lines, the scroll hook off. Raises if a patched place does not hold the vanilla bytes it expects."""
    if base.read(SPORE_SPAWN_HOOK, 6) != SPORE_SPAWN_HOOK_VANILLA:
        raise RuntimeError(f"bytes inesperados em ${SPORE_SPAWN_HOOK:06X} (gancho de câmera do Spore Spawn)")
    if base.read(SPORE_SPAWN_SHOT, len(SPORE_SPAWN_SHOT_CODE)) != SPORE_SPAWN_SHOT_CODE:
        raise RuntimeError(f"bytes inesperados em ${SPORE_SPAWN_SHOT:06X} (tiro do Spore Spawn)")
    out = [(SPORE_SPAWN_HOOK, SPORE_SPAWN_HOOK_OURS)]
    for table, rows in SPORE_SPAWN_SPRITE_PALETTES:
        data = b""
        for k in range(rows):
            row = [base.u16(table + 32 * k + 2 * i) for i in range(16)]
            data += b"".join(v.to_bytes(2, "little") for v in flaahgra_colours(row))
        out.append((table, data))
    for table, line, rows in SPORE_SPAWN_DEATH_BG:
        out.append((table, bg_palette[32 * line:32 * line + 32] * rows))
    return out


# --- specs/18k: Thardus = the Bomb Torizo ($A0:EEFF, AI in $AA), patched in place --------------------------------------------
# No other room of ours uses a Torizo (both vanilla rooms, the Bomb Torizo's $8F:9804 and the Golden Torizo's $8F:B283, are
# orphans: specs/11), so its code and palettes are changed where they are (as the Spore Spawn's, 14c). Its code picks the Bomb
# or the Golden Torizo by the area ($079F: 0 = the Bomb Torizo's Crateria, else the Golden one's Norfair; in area 4 the tables
# indexed by it read past their end): the 7 reads (epic 14, "Torizo fora da área 0") become a constant 0, the Bomb Torizo's
# way everywhere (also gone: the debug cheat that gives every item with the pad at $C0C0 outside area 0, $AA:C917).
TORIZO, GOLDEN_TORIZO = 0xEEFF, 0xEF7F
TORIZO_BIT = 0x04             # the boss bit of the current area its death sets (Torizo_Instr_38 $AA:B24D: SetBossBitForCurArea)
GREY_DOOR_TORIZO = 0x8000 | (2 << 10)   # the grey cap of type 2: opens on that bit ($84:BDF2), no "opened" bit
# (address, vanilla bytes, ours): LDA $079F -> LDA #0 (the Z flag as area 0's); the init's LDY $079F -> LDY #0
TORIZO_AREA_READS = tuple((a, bytes.fromhex(v), bytes.fromhex(o)) for a, v, o in (
    (0xAAB25E, "ad9f07", "a90000"),   # Torizo_Instr_38: the Bomb Torizo's item drop
    (0xAAC2E0, "ad9f07", "a90000"),   # Torizo_Instr_25: the Golden Torizo's branch of an instruction list
    (0xAAC620, "ad9f07", "a90000"),   # Torizo_C620: the drool when hurt (area 0 only)
    (0xAAC895, "ac9f07", "a00000"),   # Torizo_Init: the index of its tables (properties, hitbox, instructions, x, y)
    (0xAAC907, "ad9f07", "a90000"),   # Torizo_Init: the Bomb Torizo's palettes and haze, or the Golden one's and the cheat
    (0xAAC97C, "ad9f07", "a90000"),   # Torizo_Shot
    (0xAAC9C2, "ad9f07", "a90000"),   # Torizo_Func_8
))
TORIZO_CODE = (0xAAB09C, 0xAAD7FF)   # the Torizos' code in $AA (sm_aa.c): no other read of the area there
# its spot: Torizo_Init puts it at the word of these tables (index 0 = the Bomb Torizo's (219, 179) in its 1x1 room), whatever
# the population says; here the Thardus' spot (frigate/enemies.py "thardus", Species.fixed): it falls from there to the floor
TORIZO_SPOT = (0xAAC95F, 0xAAC963)
# its palettes (16 colours each, sprite lines 1 and 2: $7EC320, $7EC340): the statue's at init (Torizo_C250 $AA:C250: $AA:86C7,
# $AA:86E7) and the awake body's (Torizo_C268 / Torizo_C2B0 after each hit's flash: $AA:8707, $AA:8727); 1-8 the body (the
# Chozo statue's pinkish stone), 9-11 the chest's orb, 12-14 the eyes and the highlights, 15 the outline (kept). The orbs' and
# the flashes' ($AA:8687, $AA:86A7, $AA:8787, $AA:87A7) and the Golden Torizo's ($AA:8747, $AA:8767) stay
TORIZO_PALETTES = (0xAA86C7, 0xAA86E7, 0xAA8707, 0xAA8727)
# the chest's pulse once it is awake (Torizo_Instr_9 $AA:B951: SpawnPalfxObject $8D:F759, list $8D:E2E9 = set the colour
# index $0132 (sprite line 1, colours 9-11), then frames of (timer, 3 colours, $C595) looping from $8D:E2F1 by $C61E): its
# colours recoloured as the palettes' 9-11 (emulator: without it the chest stayed the Torizo's pink)
TORIZO_PALFX = 0x8DE2F1
PALFX_FRAME_END, PALFX_GOTO = 0xC595, 0xC61E
# Thardus' colours (Prime: the Thardus object's rock CMDLs and its body CE196B36, textures dumped with
# tools/dump_prime_textures.py, scratchpad s18k/thardus_tex; the glow TXTR 6FC03D46 it names): the brown-grey stones (hue
# under 0.17, saturation over 0.12), the snow between them (luma over 120, saturation under 0.12) and the glow, each sorted by
# brightness and averaged in equal slices (s18k/scripts/thardus_ramps.py); the last stop of the stone a highlight (not in the
# textures), so the statue's lighter shades keep their shading
THARDUS_ROCK: Ramp = [(0, 0, 0), (41, 36, 31), (63, 57, 51), (82, 75, 65), (102, 94, 82), (126, 117, 102), (173, 160, 138),
                      (236, 226, 206)]
THARDUS_SNOW: Ramp = [(0, 0, 0), (134, 135, 132), (160, 163, 162), (187, 190, 190), (216, 220, 217)]
THARDUS_GLOW: Ramp = [(0, 0, 0), (155, 165, 175), (191, 198, 204), (219, 223, 226), (246, 247, 247)]
TORIZO_GROUPS = (((1, 8), THARDUS_ROCK), ((9, 11), THARDUS_GLOW), ((12, 14), THARDUS_SNOW))
# the vanilla room's haze (Torizo_Init $AA:C90F: JSL SpawnBombTorizoHaze $88:DD32, two HDMA objects that set the colour math,
# area 0's branch): in the snowy cave it washed the colours out and hid the falling snow (emulator, s18k/emu/m4.png); NOPs
TORIZO_HAZE = (0xAAC90F, bytes.fromhex("2232dd88"), bytes.fromhex("eaeaeaea"))
# what hurts Samus in the fight besides its touch (projectile headers in $86: damage = properties (+8) & $0FFF): the
# explosive swipe ($86:A985), the Chozo orbs ($86:AD5E), the sonic boom ($86:AEA8); its drool, falling parts, low-health and
# death explosions do none ($86:A95B, A969, A977, A9A1, A9AF)
TORIZO_EPROJS = (0x86A985, 0x86AD5E, 0x86AEA8, 0x86A95B, 0x86A969, 0x86A977, 0x86A9A1, 0x86A9AF)
# the PLM of the vanilla statue ($84:D6EA: it waits for the Bombs, breaks the statue's blocks and deletes itself; the Torizo
# wakes when it is gone, Torizo_Func_4 $AA:C6C6): never placed here, so the Thardus wakes as the room loads (Prime's Thardus
# forms as Samus comes in)
TORIZO_STATUE_PLM = 0xD6EA


def thardus_colours(row: list[int]) -> list[int]:
    """A row of the Torizo's palettes in Thardus' colours: each colour keeps its brightness and takes its group's ramp."""
    out = list(row)
    for (lo, hi), ramp in TORIZO_GROUPS:
        for i in range(lo, hi + 1):
            out[i] = rgb_to_bgr555(along(ramp, luma(bgr555_to_rgb(row[i]))))
    return out


def palfx_frames(base, at: int) -> list[int]:
    """The addresses of the colour triples of the palette-effect frames from `at` ($8D: timer, 3 colours, $C595 each) up to
    its loop ($C61E back to `at`); raises if the list is not that."""
    out, p = [], at
    while base.u16(p) != PALFX_GOTO:
        if not 0 < base.u16(p) < 0x100 or base.u16(p + 8) != PALFX_FRAME_END or len(out) > 16:
            raise RuntimeError(f"efeito de paleta inesperado em ${p:06X}")
        out.append(p + 2)
        p += 10
    if base.u16(p + 2) != at & 0xFFFF or not out:
        raise RuntimeError(f"efeito de paleta em ${at:06X} sem o laço esperado")
    return out


def torizo_patches(base, spot: tuple[int, int]) -> list[tuple[int, bytes]]:
    """(address, bytes) of the Torizo's patches, from the base ROM `base`: the area reads as area 0, no haze, its spot (x, y)
    in its tables, its body's palettes and its chest's pulse in Thardus' colours. Raises if a patched place does not hold the
    vanilla bytes it expects."""
    out = []
    for at, vanilla, ours in TORIZO_AREA_READS + (TORIZO_HAZE,):
        if base.read(at, len(vanilla)) != vanilla:
            raise RuntimeError(f"bytes inesperados em ${at:06X} (leitura da área ou bruma no Torizo)")
        out.append((at, ours))
    for table, v in zip(TORIZO_SPOT, spot):
        out.append((table, v.to_bytes(2, "little")))
    for table in TORIZO_PALETTES:
        row = [base.u16(table + 2 * i) for i in range(16)]
        out.append((table, b"".join(v.to_bytes(2, "little") for v in thardus_colours(row))))
    (lo, _), ramp = TORIZO_GROUPS[1]   # the chest's pulse: colours 9-11
    for at in palfx_frames(base, TORIZO_PALFX):
        out.append((at, b"".join(rgb_to_bgr555(along(ramp, luma(bgr555_to_rgb(base.u16(at + 2 * i)))))
                                 .to_bytes(2, "little") for i in range(3))))
    return out


# --- specs/19k: the Omega Pirate = the Bomb Torizo again (OMEGA); its body's palettes chosen by the area ----------------------
# The Torizo's palette routines copy 16 colours of two tables with LDA abs,X (Torizo_C250 $AA:C250: the statue's, $86E7 / $86C7;
# Torizo_C268 $AA:C268 and Torizo_C2B0 $AA:C2B0: the awake body's, $8727 / $8707). Each of those 6 loads becomes a JSR (same 3
# bytes) to a selector in $AA's free space ($AA:F7D3-FFFF, only $FF in the base): in OMEGA_AREA, LDA from the Omega Pirate's copy
# of the table (also in $AA), else from the table in place (the Thardus' colours, torizo_patches). The chest's pulse (TORIZO_PALFX,
# $8D) stays the Thardus' glow in every area (a spawned palette-effect object: one list)
OMEGA_AREA = 5                 # areas.MINES_AREA (validate checks it)
TORIZO_AREA_LOADS = ((0xAAC254, 0x86E7), (0xAAC25B, 0x86C7), (0xAAC26C, 0x8727), (0xAAC273, 0x8707),
                     (0xAAC2B4, 0x8727), (0xAAC2BB, 0x8707))   # (address of LDA abs,X = BD lo hi, its table)
# the Omega Pirate's colours: the Phazon Elite's ramps (19h, from the Elite Pirate's Prime textures: the same pirate armour and
# phazon): the body (1-8) the grey armour, the chest's orb (9-11) the phazon glow, the eyes and highlights (12-14) the phazon blue
OMEGA_GROUPS = (((1, 8), ELITE_ARMOUR), ((9, 11), ELITE_GLOW), ((12, 14), ELITE_PHAZON))


def omega_colours(row: list[int]) -> list[int]:
    """A row of the Torizo's palettes in the Omega Pirate's colours (OMEGA_GROUPS), each colour keeping its brightness."""
    out = list(row)
    for (lo, hi), ramp in OMEGA_GROUPS:
        for i in range(lo, hi + 1):
            out[i] = rgb_to_bgr555(along(ramp, luma(bgr555_to_rgb(row[i]))))
    return out


def omega_selector(table: int, omega_table: int) -> bytes:
    """LDA $079F / CMP #OMEGA_AREA / BEQ +4 / LDA table,X / RTS / LDA omega_table,X / RTS (16-bit A and X, as the routines)."""
    return (bytes([0xAD, 0x9F, 0x07, 0xC9]) + OMEGA_AREA.to_bytes(2, "little") + bytes([0xF0, 0x04, 0xBD])
            + (table & 0xFFFF).to_bytes(2, "little") + bytes([0x60, 0xBD]) + (omega_table & 0xFFFF).to_bytes(2, "little")
            + bytes([0x60]))


def omega_patches(base, put) -> list[tuple[int, bytes]]:
    """(address, bytes) of the Omega Pirate's palette patches, from the base ROM `base` (the vanilla Torizo tables, read before
    torizo_patches recolours them in place): its 4 tables and a selector per table written with `put` ($AA's free space; returns
    the address), each of TORIZO_AREA_LOADS turned into JSR to its table's selector. Raises if a load is not LDA table,X."""
    selectors, out = {}, []
    for at, table in TORIZO_AREA_LOADS:
        if base.read(at, 3) != bytes([0xBD]) + table.to_bytes(2, "little"):
            raise RuntimeError(f"bytes inesperados em ${at:06X} (carga de paleta do Torizo)")
        if table not in selectors:
            row = [base.u16(0xAA0000 | table + 2 * i) for i in range(16)]
            omega = put(b"".join(v.to_bytes(2, "little") for v in omega_colours(row)))
            selectors[table] = put(omega_selector(table, omega))
        out.append((at, bytes([0x20]) + (selectors[table] & 0xFFFF).to_bytes(2, "little")))
    return out


# --- specs/19h: the Phazon Elite = the gold ninja pirate's copy (PHAZON_ELITE); its leap palette patched in place -------------
# NinjaSpacePirates_Init ($B2:F5DE) copies 16 colours from $B2:8727 (LDA $8727,Y at $B2:F692) into sprite line 7, which its
# leaps show (SpacePirates_Instr_20 with $0E00). $B2:8727 is the palette of two vanilla pirates' headers ($A0:F413, $F713), so it
# stays: the operand points at the Phazon Elite's leap colours in $B2's free space ($B2:FEAA-FFFF, only $FF in the base). Every
# ninja pirate shares that init: no room of ours has a vanilla one (validate: only the copy)
NINJA_INIT = 0xB2F5DE
NINJA_LINE7_LOAD = (0xB2F692, bytes.fromhex("b92787"))   # LDA $8727,Y
NINJA_LINE7 = 0xB28727
NINJA_PALETTE_INDEX = 0x0200   # SpacePirates_Instr_20's other value: sprite line 1 (the enemy set's palette must be 1)
# what hurts Samus in the fight besides its touch (projectile headers in $86: damage = properties (+8) & $0FFF): its claws
# (SpacePirates_Instr_15 $B2:F564 -> addr_kEproj_PirateClaw $86:A189); it fires no laser (the walking pirates' $86:A17B)
NINJA_EPROJS = (0x86A189,)
# the ninja's x radius and the leap: the init turns parameter 2 (the span) into a leap whose half is R24 (NinjaSpacePirates_Init:
# r18 += 32, R22 += r18 while R22 < (span / 2) << 8; R24 = R22 >> 8), between centre - R24 and centre + R24
NINJA_X_RADIUS = 16
# the leap's rise: x moves HIBYTE of a speed that grows by 32 a frame until the centre, 2 px up each frame (SpacePirates_Func_11/
# 13), then down the same: the top is 2 x the frames to the centre over its feet


def ninja_leap(span: int) -> tuple[int, int]:
    """(half of the leap R24, its rise in px) of a ninja pirate with parameter 2 = `span` (NinjaSpacePirates_Init $B2:F5DE,
    SpacePirates_Func_11 $B2:F817)."""
    half = (span >> 1) & 0xFF
    r18 = r22 = 0
    while True:
        r18 += 32
        r22 += r18
        if r22 >= half << 8:
            break
    r24 = r22 >> 8
    x = frames = 0
    v = 0
    while x < r24:
        v += 32
        x += v >> 8
        frames += 1
    return r24, 2 * frames


def elite_line7(base) -> list[int]:
    """The Phazon Elite's leap colours: $B2:8727's 16 (read from the base ROM `base`) with 1-8 and 13-15 on the phazon glow,
    9-12 the phazon (each colour keeps its brightness)."""
    row = [base.u16(NINJA_LINE7 + 2 * i) for i in range(16)]
    out = list(row)
    for (lo, hi), ramp in zip(RECOLOUR_GROUPS, (ELITE_GLOW, ELITE_PHAZON, ELITE_GLOW)):
        for i in range(lo, hi + 1):
            out[i] = rgb_to_bgr555(along(ramp, luma(bgr555_to_rgb(row[i]))))
    return out


def ninja_patches(base, line7_at: int) -> list[tuple[int, bytes]]:
    """(address, bytes) of the ninja pirates' patch, from the base ROM: the init's LDA operand -> `line7_at` ($B2), where the
    leap colours go (elite_line7). Raises if the patched place does not hold the vanilla bytes."""
    at, vanilla = NINJA_LINE7_LOAD
    if base.read(at, len(vanilla)) != vanilla or line7_at >> 16 != 0xB2:
        raise RuntimeError(f"bytes inesperados em ${at:06X} (a paleta do salto do pirata ninja) ou paleta fora do $B2")
    colours = b"".join(v.to_bytes(2, "little") for v in elite_line7(base))
    return [(at, bytes([vanilla[0]]) + (line7_at & 0xFFFF).to_bytes(2, "little")), (line7_at, colours)]

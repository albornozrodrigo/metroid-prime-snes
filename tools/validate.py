"""Static checks for the rooms of every area (tools/areas.py), run before building the ROM.

Catches the kind of bugs that softlock players:
  - a door that cannot be reached from the room's other doors (or from the spawn point);
  - two doors drawn on top of each other, or a door outside the room;
  - links that don't come back (door A -> B must have B -> A);
  - rooms overlapping on the pause map, or off its 64x32 grid;
  - a door whose neighbour room is not right next to it on the pause map (the map would show
    rooms floating apart, and the minimap would jump when Samus goes through);
  - rooms larger than the engine's 50-screen limit.
  - back-wall / landing-pad art (props.BACKDROPS/SKINS) that changes any collision, the gunship's
    included (hangar_colisao_nave_igual).
  - in the last built ROM (build/, if there is one): the area-select screen's title and area 3
    name spritemaps and the big O tiles (tools/frigate/areaselect.py); the frigate's lift-off
    going to the Ceres escape only in area 3, and that cutscene's "TALLON IV" text and letter
    tiles (tools/frigate/ending.py).
  - check_queen_art (tools/frigate/queen_art.py): the LZ compressor gives back the vanilla tileset 4
    graphics; vanilla Phantoon read as images, re-encoded and read back is pixel-identical; and, in
    the last built ROM, the Parasite Queen read back equals tools/frigate/queen_draw.py.
  - the Tallon Overworld's whole room table (tools/tallon/rooms.py, specs/07d), built or not: names,
    boxes and door pairs equal Prime's (research/prime_worlds.json), the map checks above on the 44
    rooms and on each region alone, and its explored map within area 0's save list (80 bytes);
    the rooms already drawn but not built yet (specs/07j) get the room checks (reach included),
    each with its region alone.
  - check_pause_maps, in the last built ROM: each remade area's pause tilemap, name, icons and
    explored-map save list (the Tallon's included, specs/07f).
  - Tallon progression (specs/07k; rounds since specs/09f): the round (0 = the arrival with the Power Beam; round
    k = with the items picked up in rounds 0..k-1; the walk stops at the first pass that adds no room and no
    item) at which each built room and each placed item is first reached from the gunship, walking room by room
    and going through a gated door only with its items, must be the declared FIRST_ROUND / Item.round; in every
    round every room is walked from every entry Samus gets in by with that round's equipment and no place leaves
    her without a door she can use (check_tallon_round_stuck); a door behind a Space Jump gate must be out of reach on foot from every entry that is
    not on a ledge itself; in the built ROM each capped door has its red (missile), beam (ice, wave,
    plasma: specs/09a, argument $8000, code in $84 as tallon/beamdoors.py generates it) PLM (specs/09d: no
    grey "never opens" door left), red door bits unused by vanilla. The walk lets the geometry decide the
    GEOMETRY items of a gate (a ledge reached from another ledge door: the Landing Site's Gully/Alcove
    ledge, specs/07m; the Tallon Canyon's Morph Ball tunnel to the Gully, specs/09d).
  - Morph Ball and Bombs (specs/09d): the reach model has the ball (tools/smlib/reach.py); a door behind
    geometry (DoorLink.ledge) is out of reach without its items from every entry not behind the same geometry,
    each foot item of it needed on its own, and in reach with them; every room walked on foot is walked with the
    Morph Ball and the Bombs too (no place without a way back); check_breakables: every bomb block is the
    project's, in a room behind a Bombs gate, and can really be bombed; check_tallon_return: in every round
    every room and entry reached has a way back to the gunship; the enemy
    fairness rule covers the rooms first reached with at most missiles and the Morph Ball.
  - Tallon items (specs/07h, tools/tallon/items.py): the progression walk picks up the items Samus'
    body gets to (a Missile Expansion gives missiles, so the red doors open in the same tier); each
    item sits in an air block, off the doorways, first reachable at its declared round; its bit is
    unique and unused by the vanilla items; in the built ROM each room has exactly its item PLMs.
    specs/09b: the Ice, Wave, Plasma and Gravity Suit are items the walk picks up (bits $AD-$B0; the
    Morph Ball, Bombs and Power Bomb rows, $B1-$B3, wait for their spot), and the Gravity Suit cutscene
    patch (tallon/items.py gravity_patch) is in the built ROM.
  - Enemies (specs/07i): each enemy's whole hitbox (radii read from its species header) is open air
    inside the room, on solid ground, away from the doors; each room's enemy set has at most 4
    species with one vanilla enemy palette slot each and fits the enemy VRAM ($2000 bytes; $1C00 in
    the frigate, whose escape timer digits sit at $7E00); none in the gunship's room; in the built
    ROM every state points at the table's population and set; a walking enemy (specs/07m, the
    Seedling's Cacatac) has air and ground along its whole walk; kinds sharing a species share its
    palette (one enemy-set entry). Tallon (tools/tallon/enemies.py):
    each Prime layer-0 enemy with a stand-in is there, never more than Prime has nor more than one
    per screen, and in the rooms first reached with at most missiles and the Morph Ball every enemy dies to the Power Beam in at most 5 shots and a
    touch takes at most 20 energy.
  - Expanded banks (specs/09c, check_banks), in the built ROM: the level allocator ($E0-$EF) and the
    fixed one ($F0-$FF) don't overlap and sit in the 4 MB ROM, outside the 3 MB base; every state of
    every room points at its level in the level range and the bytes there are the room's compressed
    level; the recoloured palettes, the Parasite Queen's tileset graphics, the "TALLON IV" graphic and
    the hangar's star DMAs are in the fixed range, none across a bank (the stars' bytes checked); no two
    blobs overlap. Prints the free bytes of each allocator and the rooms whose level crosses a bank.
  - Water (specs/07l): a flooded room (RoomDef.water) is walked with the underwater jump measured in
    the emulator, with the Gravity Suit (the sunken frigate assumes it); the flooded rooms Samus can
    reach without the suit (specs/09b: what she has when she first gets in, the walk records it) are
    walked without it too (check_tallon_water: the suit's bulkhead holds,
    nothing traps her); in the built ROM every flooded room has the whole-room water FX and no other
    room has water (check_water_in_rom).
  - Orphans (specs/11, check_orphans), in the built ROM: from the new game, the end of the frigate, every save PLM's
    station and every area's station 0 (the gunship), through the doors the door blocks use (smlib/roomgraph.py), the
    rooms the game can load are exactly ours; no vanilla room loads: the attract-mode demos, the last way in, are off
    since specs/16 (title.check_demos_off, from the bytes); our rooms use vanilla data only from VANILLA_SHARED (each used,
    unchanged). The vanilla door and item bits come from the 262 rooms crawled from the base ROM's bytes.
  - Reclaimed $8F (specs/12a, check_reclaimed), in the built ROM: the orphan ranges the allocator may use after FREE_8F
    (build.RECLAIMED_8F) hold, in the base ROM, only orphan rooms' structures (VANILLA_SHARED and code excluded; specs/18a: a
    demo room's only while the attract demos are off, title.check_demos_off), none
    of the headers vanilla code compares the room pointer with (read from the bytes, build.ROOM_PTR_COMPARED); only our
    rooms' structures are written there and no header of ours is at a compared address. specs/19a: the same for the $A1 ranges
    (build.RECLAIMED_A1, enemy populations), and check_orphans accepts our populations there.
  - Chozo slot (specs/12b): every build.VANILLA_PAUSE entry equals the base ROM's tables (check_vanilla_pause); the area set
    aside for the Chozo Ruins (areas.CHOZO_AREA) is free, has a saved map and its list fits the SRAM left (check_chozo_slot).
  - Chozo table (specs/12c, check_chozo): the 64 rooms of tools/chozo/rooms.py (built: specs/12e's 3): names, boxes and door pairs
    equal Prime's, the Prime locks per dock and features per room equal what research/prime_chozo_locks.json gives
    (tools/dump_prime_locks.py), the map checks on the whole table and on each region alone, and the explored map within
    area 1's vanilla save-list place (80 bytes).
  - Ruins style (specs/12d): smlib/ruins.py's pieces are in tileset $0C with vanilla's collision and all on palette line 7
    (ruins.check); in the built ROM tileset $0C's palette is a copy with line 7 = ruins.SANDSTONE, its graphics and metatiles
    vanilla, its table entry its own, and no room of ours outside the Chozo nor any attract-demo room uses it
    (check_ruins_in_rom).
  - Phendrana (specs/18b, check_phendrana_slot): area 4's slot, its vanilla pause tables, no heat, no Maridia palette FX or
    animated tiles in our rooms there, the plan of the areas (Mines 5, Impact Crater 0). specs/18c, check_phendrana: the whole
    Phendrana Drifts table (tools/phendrana/rooms.py) against Prime (rooms, links, locks, door colours, features, snow, water,
    plasma ice, wave panels), the map on all regions and on each alone, area 4's save-list place; check_no_super_locks, built
    ROM: no green door nor super missile block in any room of ours (the Super Missile opens nothing).
  - Phazon Mines table (specs/19c, check_mines): the 42 rooms of tools/mines/rooms.py against Prime (rooms, links, locks, door
    colours, features, power-bomb-only objects, wave panels; no heat, snow, water, plasma ice nor super-missile-only door), the map
    on all regions and on each alone, the elevator rooms' doors, area 5's saved-map list; check_no_grapple_locks, built ROM: no
    grapple block nor latchable enemy in any room of ours (the Grapple Beam opens nothing).
  - Phazon Mines (specs/19b, check_mines_slot): area 5's slot (Tourian's), its vanilla pause tables and map icons, its saved-map
    list moving to $81's free space when it outgrows the vanilla place (mapsave.list_at), no heat (area 5's palette FX list starts
    with the heat object), no Tourian palette FX or animated tiles in our rooms there, vanilla's area-5 boss bits.
  - Elevators (specs/12e, check_elevators / check_elevators_in_rom): each pair of areas.ELEVATORS is one of Prime's
    (PRIME_ELEVATORS), a Tallon room going down and a Chozo room (area CHOZO_AREA) going up, and no other room has an
    elevator; the platform's and the exit's door blocks and the shaft between them are in each level; every room with an
    elevator is walked from every entry, the platform included (she arrives standing on it), the platform must be
    reached from each and nothing may leave her without a way back to a door or to it; in the built ROM the door-out
    list goes on with the exit (flags $C0, to the other room) and the platform's no-room entry, and every state's
    population starts with the platform ($D73F). specs/12f: the progression walk rides the elevators, so the Chozo's rooms
    and items get rounds of the same walk as the Tallon's (check_chozo_rounds: a line of their own; the Tallon's stays).
    specs/19e: the Tallon's P43 and the Magmoor's P26 down to the Mines' P0 and P25 (area 5, the AreaDef MINES), walked with the
    other four areas (check_mines_rounds: the line "mines (specs/19e)", the lifts in the epic's rounds 5 and 4; the rounds line
    leaves them out until 19m).
Reachability follows each area's loadout (AreaDef.loadout, tools/smlib/reach.py): with Space Jump
(the frigate) any 4-connected open space counts as reachable; without it Samus walks, falls,
climbs ledges and jumps gaps as far as the jump measured in the emulator allows, and every door
must be reachable from every entry of the room (specs/07b-alcance-sem-space-jump.md). The model
itself is checked on synthetic rooms (reach.self_test). The Crateria styles (smlib/crateria.py,
specs/07c) are checked against the vanilla ROM: every piece is in its tileset and vanilla gives it
the same collision; a room with an EdgeStyle must use that style's tileset. Room checks run per area; the boss /
escape-route progression is the frigate's own (PROGRESSION).

Usage: python3 -I tools/validate.py   (exit code 1 on any problem)
"""
from __future__ import annotations

import collections
import dataclasses
import hashlib
import json
import struct
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from areas import AREAS, CHOZO, CHOZO_AREA, MAGMOOR, MAGMOOR_AREA, ELEVATORS, FRIGATE, TALLON, all_rooms  # noqa: E402
from areas import IMPACT_CRATER_AREA, MINES, MINES_AREA, PHENDRANA, PHENDRANA_AREA  # noqa: E402
import build  # noqa: E402
from build import LOAD_STATION_SIZE, LOAD_STATION_TABLE  # noqa: E402
from frigate import areaselect, ending, mapsave, pausemap, queen_art, space, title  # noqa: E402
from frigate.enemies import enemy_set, population, set_species, slots  # noqa: E402
from smlib import crateria, ice, itemtouch, lava, mines, reach, roomgraph, ruins  # noqa: E402
from smlib.compression import CompressionError, decompress  # noqa: E402
from smlib.palette import recolor  # noqa: E402
from smlib.rom import Rom, pc_to_snes, snes_to_pc  # noqa: E402
from smlib.room_reader import read_room  # noqa: E402
from tallon import enemies as tallon_enemies  # noqa: E402
from chozo import enemies as chozo_enemies  # noqa: E402
from chozo import bosses as chozo_bosses  # noqa: E402
from tallon import beamdoors  # noqa: E402
from tallon import items as tallon_items  # noqa: E402
from tallon import layouts as tallon_layouts  # noqa: E402
from tallon import rooms as tallon_rooms  # noqa: E402
from chozo import items as chozo_items  # noqa: E402
from chozo import rooms as chozo_rooms  # noqa: E402
from chozo import heat  # noqa: E402
from magmoor import rooms as magmoor_rooms  # noqa: E402
from magmoor import items as magmoor_items  # noqa: E402
from magmoor import enemies as magmoor_enemies  # noqa: E402
from phendrana import rooms as phendrana_rooms  # noqa: E402
from phendrana import items as phendrana_items  # noqa: E402
from phendrana import enemies as phendrana_enemies  # noqa: E402
from mines import enemies as mines_enemies  # noqa: E402
from mines import rooms as mines_rooms  # noqa: E402
from mines import items as mines_items  # noqa: E402
from impact import ending as impact_ending  # noqa: E402
from impact import rooms as impact_rooms  # noqa: E402
from impact import style as impact_style  # noqa: E402
from impact import layouts as impact_layouts  # noqa: E402
from impact import enemies as impact_enemies  # noqa: E402
from areas import AreaDef, elevator_target  # noqa: E402

BUILT_ROM = Path(__file__).resolve().parent.parent / "build/metroid_prime_snes.sfc"
BASE_ROM = Path(__file__).resolve().parent.parent / "base/sm_fix.sfc"
PRIME_WORLDS = Path(__file__).resolve().parent.parent / "research/prime_worlds.json"
SOLID_TYPES = {0x8, reach.BOMB_BLOCK, reach.LAVA}   # specs/09d: a bomb block is solid but to the Bombs; specs/17d: lava is
# no place for the walks (reach.with_lava)
MAX_SCREENS = 50


def door_inner_cells(side: str, screen: int, wb: int, hb: int) -> list[tuple[int, int]]:
    if side == "L":
        return [(2, screen * 16 + 6 + k) for k in range(4)]
    if side == "R":
        return [(wb - 3, screen * 16 + 6 + k) for k in range(4)]
    if side == "T":
        return [(screen * 16 + 6 + k, 3) for k in range(4)]
    return [(screen * 16 + 6 + k, hb - 4) for k in range(4)]


def check() -> list[str]:
    try:
        all_rooms()
    except ValueError as e:   # a room key used by two areas
        return [str(e)]
    reset_tallon_cache()
    problems = [f"modelo de pulo: {p}" for p in reach.self_test()]
    problems += crateria.check(Rom.load(BASE_ROM))
    problems += ruins.check(Rom.load(BASE_ROM))   # specs/12d
    problems += lava.check(Rom.load(BASE_ROM))    # specs/17d
    problems += ice.check(Rom.load(BASE_ROM))     # specs/18d
    problems += mines.check(Rom.load(BASE_ROM))   # specs/19d
    problems += check_lava_test_rooms()           # specs/17d
    problems += check_ice_test_rooms()            # specs/18d
    problems += check_mines_test_rooms()          # specs/19d
    for area in AREAS:
        problems += check_area(area)
    problems += mapsave.check({a.number: a.map_save_bytes() for a in AREAS if a.pause_map})
    problems += check_tallon()   # the whole table, whatever regions are built
    problems += check_wave_paint_free()
    problems += check_charge_doors()   # specs/12g2
    problems += check_vertical_wave_doors()   # specs/18i
    problems += check_vanilla_pause(Rom.load(BASE_ROM))
    problems += check_chozo_slot()
    problems += check_magmoor_slot(Rom.load(BASE_ROM))   # specs/17b
    problems += check_phendrana_slot(Rom.load(BASE_ROM), Rom.load(BUILT_ROM) if BUILT_ROM.exists() else None)   # specs/18b
    problems += check_mines_slot(Rom.load(BASE_ROM), Rom.load(BUILT_ROM) if BUILT_ROM.exists() else None)   # specs/19b
    problems += check_chozo()   # specs/12c: the whole Chozo table
    problems += check_magmoor()   # specs/17c: the whole Magmoor table
    problems += check_phendrana()   # specs/18c: the whole Phendrana table
    problems += check_mines()   # specs/19c: the whole Phazon Mines table
    problems += check_impact_graph()   # specs/20c: the whole Impact Crater table
    problems += check_chozo_locks_mapped()   # specs/12j
    problems += check_magmoor_locks_mapped()   # specs/17f
    problems += check_phendrana_locks_mapped()   # specs/18f
    problems += check_mines_locks_mapped()   # specs/19f
    problems += check_ball_ledges()          # specs/12l
    problems += check_elevators()   # specs/12e
    problems += check_impact_rooms()   # specs/20e
    problems += check_heat()   # specs/12g
    built = Rom.load(BUILT_ROM) if BUILT_ROM.exists() else None
    problems += check_impact_style(Rom.load(BASE_ROM), built)   # specs/20d
    if built:
        problems += areaselect.check_rom(built)
        problems += ending.check_rom(built)
        problems += title.check_logo(built, Rom.load(BASE_ROM))   # specs/16
        problems += check_arrival(built)
        problems += check_pause_maps(built)
        problems += check_map_shapes(built)
        problems += check_gates(built, Rom.load(BASE_ROM))
        problems += check_tallon_items(built, Rom.load(BASE_ROM))
        problems += check_enemies_in_rom(built)
        problems += check_water_in_rom(built)
        problems += check_door_push(built)
        problems += check_orphans(built, Rom.load(BASE_ROM), json.loads((BUILT_ROM.parent / "manifest.json").read_text()))
        problems += check_reclaimed(built, Rom.load(BASE_ROM), json.loads((BUILT_ROM.parent / "manifest.json").read_text()))
        problems += check_impact_space(built, json.loads((BUILT_ROM.parent / "manifest.json").read_text()))   # specs/20b
        problems += check_banks(built, Rom.load(BASE_ROM), json.loads((BUILT_ROM.parent / "manifest.json").read_text()))
        problems += check_ruins_in_rom(built, Rom.load(BASE_ROM), json.loads((BUILT_ROM.parent / "manifest.json").read_text()))
        problems += check_lava_in_rom(built, Rom.load(BASE_ROM), json.loads((BUILT_ROM.parent / "manifest.json").read_text()))
        problems += check_ice_in_rom(built, Rom.load(BASE_ROM), json.loads((BUILT_ROM.parent / "manifest.json").read_text()))
        problems += check_mines_in_rom(built, Rom.load(BASE_ROM), json.loads((BUILT_ROM.parent / "manifest.json").read_text()))
        test_rom, test_manifest, test_pairs = mines_test_build()   # specs/19d: the test build, made in memory
        problems += check_mines_in_rom(test_rom, Rom.load(BASE_ROM), test_manifest, test_pairs, "ROM de teste")
        problems += check_elevators_in_rom(built, json.loads((BUILT_ROM.parent / "manifest.json").read_text()))
        problems += itemtouch.check(built, Rom.load(BASE_ROM))   # specs/13
        problems += check_no_super_locks(built, Rom.load(BASE_ROM),
                                         json.loads((BUILT_ROM.parent / "manifest.json").read_text()))   # specs/18c
        problems += check_no_grapple_locks(built, Rom.load(BASE_ROM),
                                           json.loads((BUILT_ROM.parent / "manifest.json").read_text()))   # specs/19c
        problems += check_heat_in_rom(built, Rom.load(BASE_ROM))   # specs/12g
    else:
        print(f"AVISO {BUILT_ROM.name} ainda não existe: textos da tela de área, final da fragata e "
              "forma da Parasite Queen não conferidos")
    problems += check_queen_art(built)
    problems += check_bosses(built, Rom.load(BASE_ROM) if built else None)   # specs/14a
    problems += check_impact_boss(Rom.load(BASE_ROM), built)   # specs/20h
    problems += check_impact_ending(Rom.load(BASE_ROM), built)   # specs/20i
    return problems


def check_layout(area, rooms) -> list[str]:
    """Room table and pause map of `rooms` (all in `area`): sizes, map overlap and bounds, door
    slots, links that come back, style x tileset, doors touching their neighbours on the map."""
    problems: list[str] = []
    by_key = {r.key: r for r in rooms}
    occupied: dict[tuple[int, int], str] = {}
    for r in rooms:
        if r.width * r.height > MAX_SCREENS:
            problems.append(f"{r.key}: {r.width}x{r.height} passa de {MAX_SCREENS} telas")
        for x in range(r.map_x, r.map_x + r.width):
            for y in range(r.map_y, r.map_y + r.height):
                if (x, y) in occupied:
                    problems.append(f"{r.key} sobrepõe {occupied[(x, y)]} no mapa em ({x},{y})")
                occupied[(x, y)] = r.key

        seen_slots = set()
        for i, d in enumerate(r.doors):
            limit = r.height if d.side in "LR" else r.width
            if not 0 <= d.screen < limit:
                problems.append(f"{r.key}: porta {i} ({d.side}{d.screen}) fora da sala")
            if (d.side, d.screen) in seen_slots:
                problems.append(f"{r.key}: duas portas em {d.side}{d.screen}")
            seen_slots.add((d.side, d.screen))
            if d.to_room not in by_key:
                problems.append(f"{r.key}: porta {i} -> {d.to_room}: sala fora da área {area.key}")
                continue
            back = by_key[d.to_room].doors[d.to_door]
            if back.to_room != r.key or back.to_door != i:
                problems.append(f"{r.key}: porta {i} -> {d.to_room}.{d.to_door} não volta")

        style_tileset = getattr(r.style, "tileset", None)   # EdgeStyle pieces belong to one tileset
        if style_tileset is not None and style_tileset != area.tileset_of(r):
            problems.append(f"{r.key}: estilo {r.style.name} é do tileset {style_tileset}, a sala usa "
                            f"o {area.tileset_of(r)}")
    return problems + check_map(by_key)


def check_area(area) -> list[str]:
    problems = check_layout(area, area.rooms)
    by_key = area.by_key()
    for r in area.rooms:
        problems += check_room(area, r)
        if r is area.rooms[0]:
            unknown = set(area.props) - set(by_key)
            if unknown:
                problems.append(f"objetos em salas que não existem: {sorted(unknown)}")
    unknown = set(area.enemies) - set(by_key)
    if unknown:
        problems.append(f"inimigos em salas que não existem: {sorted(unknown)}")
    problems += check_enemy_sets(area)
    if area.key in PROGRESSION:
        problems += PROGRESSION[area.key](by_key)
    return problems


def elevator_solid(r, types: list[int]) -> list[int]:
    """specs/12e: the elevator platform's two door blocks are solid to Samus in the game (their door entry has no room:
    BlockColl_Vert_Door $94:93CE treats them as solid), the reach model's door type is air to her body: solid here."""
    if r.elevator:
        for x, y in elevator_pad(r):
            types[y * r.width * 16 + x] = reach.SOLID
    return types


def niche_cap_cells(r) -> list[tuple[str, list[tuple[int, int]]]]:
    """specs/18i: (beam, the 4 blocks) of each in-room beam cap of room r (RoomDef.caps: a niche's door cap)."""
    return [(beam, [(x, y + k) for k in range(4)]) for x, y, _side, beam in r.caps]


def room_cap_items(r) -> frozenset:
    """specs/18i: the beams (gate items) that open room r's in-room caps."""
    return frozenset(beam for *_, beam in r.caps)


def with_caps(r, types: list[int], loadout: reach.Loadout) -> list[int]:
    """specs/18i: the blocks of room r's in-room beam caps solid unless `loadout` has their beam (LOADOUT_FIELD): shut, Samus
    stands on and bumps into them as into a door's cap; open (shot with the beam), air."""
    wb = r.width * 16
    for beam, cells in niche_cap_cells(r):
        if not getattr(loadout, LOADOUT_FIELD.get(beam, "-"), False):
            for x, y in cells:
                types[y * wb + x] = reach.SOLID
    return types


def elevator_pad(r) -> list[tuple[int, int]]:
    """The two blocks of a room's elevator platform."""
    e = r.elevator
    return [(e.x, e.row), (e.x + 1, e.row)] if e else []


def elevator_stands(r) -> frozenset:
    """Where Samus stands on a room's elevator platform (reach model stands: column, feet row)."""
    return frozenset((x, y - 1) for x, y in elevator_pad(r))


def check_room(area, r) -> list[str]:
    """One room's level: reach with the area's loadout (every door from every entry), enemies,
    save/map station, props, ship, and art that keeps the collision."""
    problems = []
    if r.snow and (area.number != PHENDRANA_AREA or r.snow != ice.SPORES):   # specs/18d: the game's snow = the spores, area 4
        problems.append(f"{r.key}: neve tipo {r.snow:#x} na área {area.number} (só os esporos, {ice.SPORES:#x}, na área "
                        f"{PHENDRANA_AREA})")
    lv = r.level()
    try:
        l1, bts = lv.build_blocks()
    except ValueError as e:   # e.g. the ship's collision drawn over a wall or platform
        return [f"{r.key}: {e}"]
    wb, hb = lv.wb, lv.hb
    # specs/09e: the power bomb blocks (shot type C) are solid here, not the air of the door caps
    bare = reach.with_lava(with_caps(r, elevator_solid(r, reach.with_breakables([w >> 12 for w in l1], bts,
                                                                                  reach.POWER_BEAM_ONLY)), reach.POWER_BEAM_ONLY),
                           wb, r.liquid)   # specs/18i: the in-room caps shut; 20g: the acid too

    def passable(x: int, y: int) -> bool:
        return 0 <= x < wb and 0 <= y < hb and bare[y * wb + x] not in SOLID_TYPES

    if not (r.doors or r.spawn or r.elevator):
        return [f"{r.key}: sala sem portas"]
    loadout = room_loadout(area, r)
    if loadout.flies:
        found, seen = reach_space_jump(r, passable, wb, hb, loadout)
    else:
        def grid_of(lo: reach.Loadout) -> reach.Grid:
            return foot_grid(r, l1, bts, wb, hb, lo)
        found, seen = reach_on_foot(r, grid_of, loadout)
        # specs/09d: with the Morph Ball and the Bombs too (what Samus has from the Gully on): every door
        # still reached, the Space Jump ledges still out of reach, no place without a way back
        more, _ = reach_on_foot(r, grid_of, dataclasses.replace(loadout, morph=True, bombs=True))
        found += [f"{p} (com Morph Ball e Bombas)" for p in more]
        # specs/09e: a room with power bomb blocks also with the Power Bomb (the blocks gone: nothing traps her)
        if any(reach.is_power_bomb_block(w >> 12, b) for w, b in zip(l1, bts)):
            more, _ = reach_on_foot(r, grid_of, dataclasses.replace(loadout, morph=True, bombs=True, power_bomb=True))
            found += [f"{p} (com Morph Ball, Bombas e Power Bomb)" for p in more]
        # specs/18i: a room with an in-room beam cap also with it open (the niche behind it: nothing traps her there)
        if r.caps:
            more, _ = reach_on_foot(r, grid_of, with_items(dataclasses.replace(loadout, morph=True, bombs=True),
                                                           room_cap_items(r) & set(LOADOUT_FIELD)))
            found += [f"{p} (com Morph Ball, Bombas e a tampa de feixe da sala aberta)" for p in more]
    problems += found
    problems += check_lava(area, r, l1, bts)   # specs/17d
    problems += check_enemies(r, area.enemies, passable, wb, hb)
    problems += check_save_station(r, passable, seen)
    problems += check_map_station(r, passable, seen)
    problems += check_missile_station(r, passable, seen)   # specs/19l
    problems += check_props(r, area.props, l1, wb)
    problems += check_ship(r, passable, seen)
    problems += check_backdrop(r, lv, l1, bts)
    return problems


def room_loadout(area, r) -> reach.Loadout:
    """The area's loadout, in a flooded room with the Gravity Suit and the underwater jump (specs/07l:
    the sunken frigate assumes the suit, as Prime; check_tallon_water checks the rooms Samus can be
    in without it)."""
    return dataclasses.replace(area.loadout, water=True, gravity=True) if r.water else area.loadout


def foot_grid(r, l1: list[int], bts, wb: int, hb: int, loadout: reach.Loadout = reach.POWER_BEAM_ONLY,
              lava_blocks: bool = True) -> reach.Grid:
    """Block types for the on-foot model; the cap blocks of a side or floor door with a red/beam cap
    (DoorLink.lock, specs/07k) are solid: they stay shut with the arrival loadout, and Samus can
    stand on them (a ledge on top of a closed door can trap her). A ceiling door's cap (specs/07m)
    stays as it is: Samus reaches that door by jumping up against it. specs/09d: the bomb blocks are
    air with the loadout's Bombs, solid without them; specs/09e: the power bomb blocks air with the Power
    Bomb and the Morph Ball, solid without them (reach.with_breakables, from the room's BTS). specs/17d: a room's lava (from
    RoomDef.lava down) is no place to walk (reach.with_lava), but with `lava_blocks` False (the lava's escapes, check_lava)."""
    types = with_caps(r, elevator_solid(r, reach.with_breakables([w >> 12 for w in l1], bts, loadout)), loadout)   # 18i
    if lava_blocks:
        types = reach.with_lava(types, wb, r.liquid)   # specs/20g: the acid as the lava
    for i, d in enumerate(r.doors):
        if d.lock is not None and d.side != "T":
            x, y, _, _ = build.door_cap_and_screen(r, i)
            cells = [(x, y + k) for k in range(4)] if d.side in "LR" else [(x + k, y) for k in range(4)]
            for cx, cy in cells:
                types[cy * wb + cx] = reach.SOLID
    return reach.Grid(types, wb, hb)


def check_lava(area, r, l1, bts) -> list[str]:
    """specs/17d, a room with lava (RoomDef.lava; the user's rule: real lava in pits and lakes, never on a mandatory path
    without a way out); specs/20g: the same rule for the crater's acid (RoomDef.acid, the phazon that hurts: epic 20, decision 4),
    only in the Impact Crater's rooms (area 0, impact_*), never with lava. Lava only in the Magmoor's area 2, no water nor other
    FX, its surface inside the room; the walks never go
    into it (foot_grid, reach.with_lava: every door, item and station is reached without the lava), and from every place she
    can stand in the lava (fallen in, pushed in) she is out in at most reach.LAVA_MAX_MOVES moves with the lava jump measured
    at its depth (reach.lava_escapes; no stand deeper than reach.LAVA_MAX_DEPTH), onto a place the room's entries reach on
    foot. Walked with the area's loadout and with the Morph Ball and the Bombs too, never with the Space Jump: the weakest gear
    of any round that gets there, so the rule holds for every round (more gear only adds ways out)."""
    if r.liquid is None:
        return []
    problems = []
    name, row = ("lava", r.lava) if r.lava is not None else ("ácido", r.acid)
    if r.lava is not None and area.number != MAGMOOR_AREA:
        problems.append(f"{r.key}: lava fora da área {MAGMOOR_AREA} (Magmoor)")
    if r.acid is not None and (area.number != IMPACT_CRATER_AREA or not r.key.startswith(impact_rooms.PREFIX)):
        problems.append(f"{r.key}: ácido (o phazon que machuca) fora da cratera (área {IMPACT_CRATER_AREA}, salas impact_*)")
    if r.lava is not None and r.acid is not None:
        problems.append(f"{r.key}: lava e ácido na mesma sala")
    if r.water or r.fx:
        problems.append(f"{r.key}: {name} com água ou outro FX")
    wb, hb = r.width * 16, r.height * 16
    if not 0 < row < hb:
        return problems + [f"{r.key}: superfície do {name} na linha {row}, fora da sala"]
    pad = elevator_stands(r)
    if any(y >= row for _, y in pad):
        problems.append(f"{r.key}: plataforma do elevador dentro do {name}")
    if r.save_station and r.save_station[1] - 1 >= row:
        problems.append(f"{r.key}: estação de save dentro do {name}")
    for loadout in (area.loadout, dataclasses.replace(area.loadout, morph=True, bombs=True)):
        walk = dataclasses.replace(loadout, space_jump=False, water=False)
        dry = foot_grid(r, l1, bts, wb, hb, walk)
        starts = [reach.door_entry(dry, d.side, d.screen) for d in r.doors]
        starts += [dry.land(r.spawn[0] // 16, r.spawn[1] // 16)] if r.spawn else []
        starts += [min(pad)] if pad else []
        out = set()
        for st in starts:
            if st is not None:
                out |= {s for s in reach.reach(dry, [st], walk) if len(s) == 2}
        esc = reach.lava_escapes(foot_grid(r, l1, bts, wb, hb, walk, lava_blocks=False), row, out, walk)
        stuck = sorted(s for s, n in esc.items() if n is None)
        if stuck:
            x, y = stuck[0]
            deep = y - row + 1 > reach.LAVA_MAX_DEPTH
            problems.append(f"{r.key}: {len(stuck)} lugares no {name} sem saída em {reach.LAVA_MAX_MOVES} movimentos"
                            + (" (com Morph Ball e Bombas)" if loadout is not area.loadout else "")
                            + f" (ex.: coluna {x}, pé na linha {y}" + (f", {y - row + 1} linhas abaixo da superfície: "
                                                                       f"mais fundo que o medido" if deep else "") + ")")
    return problems


def lava_rooms_report(rooms) -> tuple[int, int, int]:
    """(rooms with lava, places to stand in their lava, the most moves any of them needs to get out) with the area loadout."""
    places, worst = 0, 0
    for area, r in rooms:
        if r.lava is None:
            continue
        l1, bts = r.level().build_blocks()
        wb, hb = r.width * 16, r.height * 16
        walk = dataclasses.replace(area.loadout, space_jump=False)
        dry = foot_grid(r, l1, bts, wb, hb, walk)
        out = set()
        for d in r.doors:
            st = reach.door_entry(dry, d.side, d.screen)
            if st is not None:
                out |= {s for s in reach.reach(dry, [st], walk) if len(s) == 2}
        esc = reach.lava_escapes(foot_grid(r, l1, bts, wb, hb, walk, lava_blocks=False), r.lava, out, walk)
        places += len(esc)
        worst = max([worst] + [n for n in esc.values() if n is not None])
    return sum(r.lava is not None for _, r in rooms), places, worst


def lava_test_area():
    """specs/17d: the lava test build's area (magmoor/testrooms.py: specs/17e, the Magmoor's with the test rooms) on a copy (the
    game's tables are not touched)."""
    import copy
    from magmoor import testrooms
    return testrooms.apply(copy.deepcopy(MAGMOOR))


def check_lava_test_rooms() -> list[str]:
    """specs/17d: the lava test build's rooms keep the rule too (check_lava), and the test pit has a stand at every depth
    measured (1 to reach.LAVA_MAX_DEPTH). Prints the line "lava (specs/17d)"."""
    area = lava_test_area()
    from magmoor import testrooms
    problems = []
    for r in area.rooms:
        l1, bts = r.level().build_blocks()
        problems += check_lava(area, r, l1, bts)
    cool = area.by_key()[testrooms.COOL]
    depths = {feet - cool.lava + 1 for _, _, feet in testrooms.PIT_FLOORS}
    if depths != set(range(1, reach.LAVA_MAX_DEPTH + 1)):
        problems.append(f"{testrooms.COOL}: fundos do fosso a {sorted(depths)} linhas, o medido é 1-{reach.LAVA_MAX_DEPTH}")
    if not problems:
        n, places, worst = lava_rooms_report(all_rooms())
        tn, tplaces, tworst = lava_rooms_report([(area, r) for r in area.rooms if r.key in (testrooms.COOL, testrooms.HOT)])
        print(f"lava (specs/17d): FX tipo {lava.LAVA_TYPE} da área {MAGMOOR_AREA}, medido na ROM de teste (build.py --teste-17d): "
              f"dano por quadro sem roupa {reach.LAVA_DAMAGE_PER_FRAME['nada']}, Varia {reach.LAVA_DAMAGE_PER_FRAME['varia']}, "
              f"Gravity {reach.LAVA_DAMAGE_PER_FRAME['gravity']}; pulo de dentro (pé a 1/2/3 linhas): "
              f"{'/'.join(str(reach.LAVA_RISE_PX[k]) for k in sorted(reach.LAVA_RISE_PX))} px; regra: nunca no caminho, "
              f"todo lugar de pé na lava sai em até {reach.LAVA_MAX_MOVES} movimentos, no máximo {reach.LAVA_MAX_DEPTH} linhas "
              f"de fundo; salas do jogo com lava: {n} ({places} lugares, pior saída {worst}); salas de teste: {tn} "
              f"({tplaces} lugares, pior saída {tworst})")
    return problems


def check_ice_test_rooms() -> list[str]:
    """specs/18d: the ice looks' test build (phendrana/testrooms.py; specs/18e: added to Phendrana's area, on the map with its
    built rooms, check_layout): the rooms build; one room per look
    (snow $01, icy ruins $1C, lab $1B) with its style and a wave door on its east wall; the snow rooms are snow/icy-ruins
    rooms with the spores, the rain room has the rain; the flooded room is area 4's (the water the Gravity Chamber will have,
    specs/18m); every room's FX turns on no palette FX and no animated tiles bit of area 4's lists (Maridia's: specs/18b). Prints
    the line "gelo (specs/18d): ROM de teste"."""
    import copy
    from phendrana import testrooms
    area = testrooms.apply(copy.deepcopy(PHENDRANA))   # specs/18e: hung on Phendrana's area (a copy: the game's is not touched)
    test_keys = {r.key for r in testrooms.rooms()}
    problems = []
    if area.number != PHENDRANA_AREA:
        problems.append(f"ROM de teste do gelo na área {area.number}")
    try:
        problems += [f"ROM de teste do gelo: {p}" for p in check_layout(area, area.rooms)]
    except Exception as e:   # noqa: BLE001 (any failure of the layout check is a problem here)
        problems.append(f"ROM de teste do gelo: mapa: {e}")
    looks = {}
    for r in (r for r in area.rooms if r.key in test_keys):
        try:
            r.level().build_blocks()
        except ValueError as e:
            problems.append(f"{r.key}: {e}")
        ts = area.tileset_of(r)
        if getattr(r.style, "tileset", ts) != ts:
            problems.append(f"{r.key}: estilo do tileset {r.style.tileset:02X} num tileset {ts:02X}")
        if any(d.lock == tallon_rooms.LOCK_OF[tallon_rooms.WAVE] and d.side == "R" for d in r.doors):
            looks.setdefault(ts, []).append(r.key)
        try:
            fx = build.WATER_FX if r.water else build.room_fx(area, r)
        except RuntimeError as e:
            problems.append(f"{r.key}: FX: {e}")
            continue
        if fx and (fx[13] or fx[14]):
            problems.append(f"{r.key}: FX liga listas da área {PHENDRANA_AREA} (paleta ${fx[13]:02X}, tiles ${fx[14]:02X})")
    if sorted(looks) != sorted(ice.TILESETS) or any(len(v) != 1 for v in looks.values()):
        problems.append(f"ROM de teste do gelo: portas de onda por tileset {looks}, esperado uma em cada um de "
                        f"{[f'{t:02X}' for t in ice.TILESETS]}")
    tests = [r for r in area.rooms if r.key in test_keys]
    snow = sorted((r.key, r.snow) for r in tests if r.snow)
    if {t for _, t in snow} != {ice.SPORES, ice.RAIN} or not any(r.water for r in tests):
        problems.append(f"ROM de teste do gelo: neve {snow}, água {[r.key for r in tests if r.water]}")
    if not problems:
        print(f"gelo (specs/18d): ROM de teste (build.py --teste-18d): área {area.number}, {len(tests)} salas (um estilo por "
              f"sala com a porta de onda, neve = esporos tipo {ice.SPORES:#x} em {sum(t == ice.SPORES for _, t in snow)}, chuva "
              f"tipo {ice.RAIN:#x} em {sum(t == ice.RAIN for _, t in snow)} para comparar, água em "
              f"{sum(r.water for r in tests)}; penduradas na área de Phendrana, estação {testrooms.TEST_STATION}); medido: o BG3 da neve desce 16 px em 64 quadros (a chuva 122), o pulo na água "
              f"da área 4 = reach.WATER_* (alcance nunca menor)")
    return problems


def demo_rooms_kept(rom, base) -> list[int]:
    """specs/19a: the attract demos' rooms (DEMO_SCENES) whose header and states are still the base ROM's bytes in `rom`. The build
    may write over a demo room's header only inside build.RECLAIMED_8F, and only while the demos are off (check_reclaimed): such a
    room is no room any more, nothing loads it, and its header no longer parses."""
    out = []
    for room in sorted({d[2] for d in DEMO_SCENES}):
        if all(rom.read(a, n) == base.read(a, n) for a, n, kind in roomgraph.structures(base, room)
               if kind in ("cabeçalho", "estado")):
            out.append(room)
    return out


def check_lava_in_rom(rom, base, manifest) -> list[str]:
    """specs/17d, built ROM: tilesets $09 and $0A (smlib/lava.py) keep their own table entries in place and the vanilla
    graphics; each palette is a copy in the fixed range = the build's (lava.recolor + the purple door's line, read directly
    too), both point at one copy of the shared metatile table = vanilla + the purple door's 8 metatiles; no room the game
    loads uses them outside the Magmoor's area 2 (the manifest: check_orphans proves it is every room reachable; the demos are
    off); every state of a room with lava points at its lava FX (build.room_fx) and no other room of ours has lava; specs/20g:
    the same for the crater's acid (RoomDef.acid, FX type lava.ACID_TYPE)."""
    problems = []
    lo, hi = build.FIXED_BANKS
    tables = set()
    entries = [rom.u16(TILESET_TABLE + 2 * i) for i in range(0x1D)]
    for t in lava.TILESETS:
        e, be = lava.entry(rom, t), lava.entry(base, t)
        if e != be or entries.count(entries[t]) != 1:
            problems.append(f"tileset {t:02X}: entrada da tabela mudou de lugar ou é dividida")
        if rom.u24(e + 3) != base.u24(be + 3):
            problems.append(f"tileset {t:02X}: gráficos diferentes dos vanilla")
        tables.add(rom.u24(e))
        pal = rom.u24(e + 6)
        try:
            got = decompress(rom.data, snes_to_pc(pal))[0] if lo <= pal <= hi else None
        except (CompressionError, IndexError, ValueError):
            got = None
        if got is None:
            problems.append(f"tileset {t:02X}: paleta em ${pal:06X} fora do alocador fixo ou não descomprime")
            continue
        words = tuple(int.from_bytes(got[2 * (lava.PAINT_LINE * 16 + i):2 * (lava.PAINT_LINE * 16 + i) + 2], "little")
                      for i in (1, 2, 3))
        if words != beamdoors.PURPLE:
            problems.append(f"tileset {t:02X}: linha {lava.PAINT_LINE} sem o roxo da porta de onda")
        if got != build.lava_palette(base, t):
            problems.append(f"tileset {t:02X}: paleta em ${pal:06X} não é a vanilla com as cores da Magmoor e a porta de onda")
    if len(tables) != 1:
        problems.append(f"tilesets 09/0A: metatiles em {sorted(map(hex, tables))}, esperado uma cópia só")
    else:
        mt = tables.pop()
        try:
            got = decompress(rom.data, snes_to_pc(mt))[0] if lo <= mt <= hi else None
        except (CompressionError, IndexError, ValueError):
            got = None
        if got != build.lava_metatiles(base):
            problems.append(f"tilesets 09/0A: metatiles em ${mt:06X} não são os vanilla com os da porta de onda")
    by_key = {r.key: (area, r) for area, r in all_rooms()}
    users, lava_states, acid_states = [], 0, 0
    for key, v in manifest.items():
        if not (isinstance(v, dict) and "header" in v) or key not in by_key:
            continue
        area, r = by_key[key]
        want = build.room_fx(area, r) if r.liquid is not None else None   # specs/20g: the acid's too
        for st in read_room(rom, 0x8F0000 | (v["header"] & 0xFFFF)).states:
            if st.tileset in lava.TILESETS and area.number != MAGMOOR_AREA:
                users.append(key)
            entry = rom.read(0x830000 | st.fx, 16) if st.fx else b""
            if want is not None:
                lava_states += r.lava is not None
                acid_states += r.acid is not None
                if entry != want:
                    problems.append(f"{key}: estado ${st.addr & 0xFFFF:04X} sem o FX de {'lava' if r.lava is not None else 'ácido'}"
                                    f" da sala (FX ${st.fx:04X})")
            elif entry and entry[9] == lava.LAVA_TYPE:
                problems.append(f"{key}: estado ${st.addr & 0xFFFF:04X} com lava, a sala não tem (RoomDef.lava)")
            elif entry and entry[9] == lava.ACID_TYPE:
                problems.append(f"{key}: estado ${st.addr & 0xFFFF:04X} com ácido, a sala não tem (RoomDef.acid)")
    if users:
        problems.append(f"tilesets 09/0A (Magmoor, recoloridos) usados fora da área {MAGMOOR_AREA}: {sorted(set(users))}")
    if not problems:
        magmoor = sum(1 for k in manifest if k in by_key and by_key[k][0].number == MAGMOOR_AREA)
        print(f"lava (specs/17d): tilesets 09 (quente) e 0A (frio) com as cores da Magmoor (paletas em "
              f"${rom.u24(lava.entry(rom, 9) + 6):06X}/${rom.u24(lava.entry(rom, 10) + 6):06X}; linha {lava.PAINT_LINE} e "
              f"metatiles da porta de onda, tabela em ${rom.u24(lava.entry(rom, 9)):06X}); usados só pela área "
              f"{MAGMOOR_AREA} ({magmoor} salas); estados com lava: {lava_states}; com ácido (specs/20g): {acid_states}")
    return problems


def check_ice_in_rom(rom, base, manifest, area_rooms=None) -> list[str]:
    """specs/18d, built ROM: Phendrana's three looks (smlib/ice.py) on tileset entries $01, $1C and $05: each entry in its vanilla
    place, its own (no other tileset's word points at it); graphics = its source's vanilla ones ($00, $0C, $04); metatiles = the
    snow's own copy (= $00's vanilla with the purple door's 8 metatiles: build.ice_metatiles), the Chozo's $0C copy, tileset 4's
    copy (the same addresses as those entries'); palette = a copy in the fixed range = build.ice_palette (and the purple door's
    colours and the snowflakes' read directly). No room the game
    loads uses them outside area 4 (the manifest: check_orphans proves it is every room reachable; the demos' rooms too). Every
    state of a room with snow (RoomDef.snow) points at its snow FX entry (ice.SNOW_FX) and no other room of ours has a snow FX
    (type 8, or $0A outside the Tallon's rain rooms, RoomDef.fx). `area_rooms`: the (area, room) list of the build (the test
    build's, validate_ice_test_build); default all_rooms(). Prints the line "gelo (specs/18d)"."""
    problems = []
    lo, hi = build.FIXED_BANKS
    words = [rom.u16(TILESET_TABLE + 2 * i) for i in range(0x1D)]
    want_tables = {ice.SNOW_TILESET: None, ice.RUINS_TILESET: rom.u24(ruins.entry(rom)),
                   ice.LAB_TILESET: rom.u24(ice.entry(rom, beamdoors.PAINT_TILESET))}
    for t in ice.TILESETS:
        e, be = ice.entry(rom, t), ice.entry(base, t)
        if e != be or words.count(words[t]) != 1:
            problems.append(f"tileset {t:02X} (gelo): entrada da tabela mudou de lugar ou é dividida")
        if rom.u24(e + 3) != base.u24(ice.entry(base, ice.SOURCE[t]) + 3):
            problems.append(f"tileset {t:02X} (gelo): gráficos não são os vanilla do tileset {ice.SOURCE[t]:02X}")
        mt = rom.u24(e)
        if want_tables[t] is not None:
            if mt != want_tables[t]:
                problems.append(f"tileset {t:02X} (gelo): metatiles em ${mt:06X}, esperado a cópia ${want_tables[t]:06X}")
        else:
            try:
                got = decompress(rom.data, snes_to_pc(mt))[0] if lo <= mt <= hi else None
            except (CompressionError, IndexError, ValueError):
                got = None
            if got != build.ice_metatiles(base):
                problems.append(f"tileset {t:02X} (gelo): metatiles em ${mt:06X} não são os do {ice.SNOW_SOURCE:02X} com a porta "
                                f"de onda")
            # specs/18j: and, read independently of the build's function, the vertical purple wave door's 8 metatiles
            # (beamdoors.VERT_PAINT_METATILES) painted there on the snow's line: VERTICAL_WAVE_TILESETS counts on them
            vert = beamdoors.paint_vertical(base, beamdoors.paint_table(base, ice.vanilla_metatiles(base, ice.SNOW_SOURCE),
                                                                        ice.SNOW_PAINT_LINE), ice.SNOW_PAINT_LINE)
            if got is None or any(got[(m - 0x100) * 8:(m - 0x100) * 8 + 8] != vert[(m - 0x100) * 8:(m - 0x100) * 8 + 8]
                                  for m in beamdoors.VERT_PAINT_METATILES.values()):
                problems.append(f"tileset {t:02X} (gelo): metatiles da porta de onda vertical ausentes na tabela "
                                f"${mt:06X} (VERTICAL_WAVE_TILESETS conta com eles)")
        pal = rom.u24(e + 6)
        try:
            got = decompress(rom.data, snes_to_pc(pal))[0] if lo <= pal <= hi else None
        except (CompressionError, IndexError, ValueError):
            got = None
        if got is None:
            problems.append(f"tileset {t:02X} (gelo): paleta em ${pal:06X} fora do alocador fixo ou não descomprime")
            continue
        paint = ice.PAINT_LINES[t]
        if ice.PAINT_LINES != {ice.SNOW_TILESET: ice.SNOW_PAINT_LINE, ice.RUINS_TILESET: beamdoors.RUINS_PAINT_LINE,
                               ice.LAB_TILESET: beamdoors.PAINT_LINE}:
            problems.append("gelo: ice.PAINT_LINES diferente das linhas das tabelas que os estilos usam")
        purple = tuple(int.from_bytes(got[2 * (paint * 16 + i):2 * (paint * 16 + i) + 2], "little") for i in (1, 2, 3))
        if purple != beamdoors.PURPLE:
            problems.append(f"tileset {t:02X} (gelo): linha {paint} sem o roxo da porta de onda")
        for (line, i), c in ice.SNOW_FLAKES.items():
            if int.from_bytes(got[2 * (line * 16 + i):2 * (line * 16 + i) + 2], "little") != ice._bgr555(c):
                problems.append(f"tileset {t:02X} (gelo): linha {line} cor {i} sem a cor da neve")
        if got != build.ice_palette(base, t):
            problems.append(f"tileset {t:02X} (gelo): paleta em ${pal:06X} não é a do build (cores do gelo, porta de onda, neve)")
    pairs = all_rooms() if area_rooms is None else area_rooms
    by_key = {r.key: (area, r) for area, r in pairs}
    users, snow_states, snow_rooms = [], 0, 0
    for key, v in manifest.items():
        if not (isinstance(v, dict) and "header" in v) or key not in by_key:
            continue
        area, r = by_key[key]
        snow_rooms += bool(r.snow)
        for st in read_room(rom, 0x8F0000 | (v["header"] & 0xFFFF)).states:
            if st.tileset in ice.TILESETS and area.number != PHENDRANA_AREA:
                users.append(key)
            entry = rom.read(0x830000 | st.fx, 16) if st.fx else b""
            if r.snow:
                snow_states += 1
                if entry != ice.SNOW_FX[r.snow]:
                    problems.append(f"{key}: estado ${st.addr & 0xFFFF:04X} sem o FX de neve da sala (FX ${st.fx:04X})")
            elif entry and (entry[9] == ice.SPORES or (entry[9] == ice.RAIN and st.fx != r.fx)):
                problems.append(f"{key}: estado ${st.addr & 0xFFFF:04X} com FX de neve/chuva {entry[9]:#x}, a sala não tem")
    for room in demo_rooms_kept(rom, base):   # specs/19a: a demo room whose header was reclaimed is no room any more
        if any(st.tileset in ice.TILESETS for st in read_room(rom, 0x8F0000 | room).states):
            users.append(f"demo ${room:04X}")
    if users:
        problems.append(f"tilesets do gelo (01/1C/1B, recoloridos) usados fora da área {PHENDRANA_AREA}: {sorted(set(users))}")
    if not problems:
        n = sum(1 for k in manifest if k in by_key and by_key[k][0].number == PHENDRANA_AREA)
        print(f"gelo (specs/18d): neve no tileset {ice.SNOW_TILESET:02X} (tabela do {ice.SNOW_SOURCE:02X} com a porta de onda na "
              f"linha {ice.SNOW_PAINT_LINE}, ${rom.u24(ice.entry(rom, ice.SNOW_TILESET)):06X}), ruínas de gelo no "
              f"{ice.RUINS_TILESET:02X} (gráficos e tabela do {ice.RUINS_SOURCE:02X}), laboratórios no {ice.LAB_TILESET:02X} "
              f"(tabela do tileset 4); paletas em "
              + "/".join(f"${rom.u24(ice.entry(rom, t) + 6):06X}" for t in ice.TILESETS)
              + f"; usados só pela área {PHENDRANA_AREA} ({n} salas); neve = FX tipo {ice.SPORES} (os esporos do SM); salas "
              f"com neve: {snow_rooms} ({snow_states} estados)")
    return problems


def check_mines_test_rooms() -> list[str]:
    """specs/19d: the Mines looks' test build (mines/testrooms.py; specs/19e: its rooms on a copy of the Mines' area 5, in MINES' place
    in AREAS only inside that build):
    the area is 5, with the Mines' music and its rooms on the map (check_layout); the rooms build; every room is in one of the two
    looks (tileset mines.TILESETS with its own style); one wave door on an east wall per look, a plasma door in the rock and an ice
    door in the base (the caps the emulator test sees); no room has an FX (area 5's palette FX list starts with the heat, specs/19b).
    Prints the line "mina (specs/19d): ROM de teste"."""
    from mines import testrooms
    area = testrooms.area()
    problems = []
    if area.number != MINES_AREA or area.music != mines.MUSIC:
        problems.append(f"ROM de teste da mina na área {area.number}, música {area.music}")
    try:
        problems += [f"ROM de teste da mina: {p}" for p in check_layout(area, area.rooms)]
    except Exception as e:   # noqa: BLE001 (any failure of the layout check is a problem here)
        problems.append(f"ROM de teste da mina: mapa: {e}")
    problems += [f"ROM de teste da mina: {p}" for p in check_wave_paint_free([area])]
    waves, locks = {}, set()
    test_keys = {r.key for r in testrooms.rooms()}   # specs/19f: the Mines' own rooms have wave doors too
    for r in area.rooms:
        try:
            r.level().build_blocks()
        except ValueError as e:
            problems.append(f"{r.key}: {e}")
        ts = area.tileset_of(r)
        if ts not in mines.TILESETS or r.style is not mines.STYLE_OF[ts]:
            problems.append(f"{r.key}: tileset {ts:02X} com o estilo {getattr(r.style, 'name', r.style)}, esperado um dos da mina")
        for d in (r.doors if r.key in test_keys else []):
            if d.lock == tallon_rooms.LOCK_OF[tallon_rooms.WAVE] and d.side == "R":
                waves.setdefault(ts, []).append(r.key)
            if d.lock:
                locks.add((ts, d.lock))
        if r.fx or r.water or r.heat or r.snow or r.lava is not None or build.room_fx(area, r) is not None:
            problems.append(f"{r.key}: sala de teste da mina com FX")
    if sorted(waves) != sorted(mines.TILESETS) or any(len(v) != 1 for v in waves.values()):
        problems.append(f"ROM de teste da mina: portas de onda por tileset {waves}, esperado uma em cada um de "
                        f"{[f'{t:02X}' for t in mines.TILESETS]}")
    want = {(mines.ROCK_TILESET, tallon_rooms.LOCK_OF[tallon_rooms.PLASMA]), (mines.BASE_TILESET, tallon_rooms.LOCK_OF[tallon_rooms.ICE])}
    if not want <= locks:
        problems.append(f"ROM de teste da mina: sem as tampas {sorted(want - locks)}")
    if not problems:
        print(f"mina (specs/19d, 19e): ROM de teste (build.py --teste-19d): área {area.number} (cópia da Mines), "
              f"{len(testrooms.rooms())} salas de teste "
              f"(base pirata {mines.BASE_TILESET:02X} e rocha {mines.ROCK_TILESET:02X}, uma porta de onda em cada, tampas de gelo "
              f"e de plasma), estação {testrooms.TEST_STATION}; teste porta_de_plasma_mina")
    return problems


def mines_test_build():
    """specs/19d: the Mines looks' test build made in memory (build.build(test_19d=True), its output and manifest in a temporary
    folder): (rom, manifest, its (area, room) pairs). The game's AREAS are back as they were when it returns."""
    import contextlib
    import io
    import tempfile
    from mines import testrooms
    with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
        rom = build.build(test_19d=True, out_dir=Path(tmp))
        manifest = json.loads((Path(tmp) / "manifest.json").read_text())
    test = testrooms.area()   # specs/19e: a copy of the Mines' area with the test rooms, in MINES' place
    return rom, manifest, [(a, r) for a, r in all_rooms() if a.number != MINES_AREA] + [(test, r) for r in test.rooms]


def check_mines_in_rom(rom, base, manifest, area_rooms=None, label="ROM do jogo") -> list[str]:
    """specs/19d: the Mines' two looks (smlib/mines.py) on tileset entries $0E (pirate base) and $08 (rock and fungus), in `rom`
    (the game's, or the test build's: mines_test_build). Each entry stays in its vanilla place and is its own. While no room of
    area 5 is built (`area_rooms`, default all_rooms(): the game's until specs/19e) the 9 bytes of each entry are the vanilla ones
    (the game's ROM does not change); with rooms of area 5 each entry points at its source's vanilla graphics, a metatile table in
    the fixed range = build.mines_metatiles (and the 16 painted wave door metatiles read on mines.PAINT_LINE independently) and a
    palette in the fixed range = build.mines_palette (the purple and the look's colours read directly). In both: no room of ours
    outside area 5 nor demo room uses $0E/$08, and no state of an area 5 room points at an FX with palette FX or animated tiles
    bits (area 5's list: the heat first, specs/19b). Prints the line "mina (specs/19d): <label>"."""
    from tallon.beamdoors import PAINT_METATILES, VERT_PAINT_METATILES
    problems = []
    lo, hi = build.FIXED_BANKS
    pairs = all_rooms() if area_rooms is None else area_rooms
    written = any(area.number == MINES_AREA for area, _ in pairs)
    words = [rom.u16(TILESET_TABLE + 2 * i) for i in range(0x1D)]

    def unpack(ptr):
        try:
            return decompress(rom.data, snes_to_pc(ptr))[0] if lo <= ptr <= hi else None
        except (CompressionError, IndexError, ValueError):
            return None

    for t in mines.TILESETS:
        e, be = mines.entry(rom, t), mines.entry(base, t)
        if e != be or words.count(words[t]) != 1:
            problems.append(f"{label}: tileset {t:02X} (mina): entrada da tabela mudou de lugar ou é dividida")
            continue
        if not written:
            if rom.read(e, 9) != base.read(be, 9):
                problems.append(f"{label}: tileset {t:02X} (mina) mudou sem sala da Mines (só a ROM de teste o escreve)")
            continue
        if rom.u24(e + 3) != base.u24(mines.entry(base, mines.SOURCE[t]) + 3):
            problems.append(f"{label}: tileset {t:02X} (mina): gráficos não são os vanilla do tileset {mines.SOURCE[t]:02X}")
        table = unpack(rom.u24(e))
        if table != build.mines_metatiles(base, t):
            problems.append(f"{label}: tileset {t:02X} (mina): metatiles em ${rom.u24(e):06X} não são os do "
                            f"{mines.SOURCE[t]:02X} com as portas de onda")
        if table is None or any(not any((w >> 10) & 7 == mines.PAINT_LINES[t]
                                        for w in struct.unpack_from("<4H", table, (m - 0x100) * 8))
                                for m in (*PAINT_METATILES.values(), *VERT_PAINT_METATILES.values())):
            problems.append(f"{label}: tileset {t:02X} (mina): metatiles da porta de onda fora da linha {mines.PAINT_LINES[t]}")
        pal = unpack(rom.u24(e + 6))
        if pal is None:
            problems.append(f"{label}: tileset {t:02X} (mina): paleta fora do alocador fixo ou não descomprime")
            continue

        def colour(line, i):
            return int.from_bytes(pal[2 * (line * 16 + i):2 * (line * 16 + i) + 2], "little")

        if tuple(colour(mines.PAINT_LINES[t], i) for i in (1, 2, 3)) != beamdoors.PURPLE:
            problems.append(f"{label}: tileset {t:02X} (mina): linha {mines.PAINT_LINES[t]} sem o roxo da porta de onda")
        if any(colour(ln, i) != mines._bgr555(c) for (ln, i), c in mines.COLOURS[t].items()):
            problems.append(f"{label}: tileset {t:02X} (mina): sem as cores da mina (o azul do phazon)")
        if pal != build.mines_palette(base, t):
            problems.append(f"{label}: tileset {t:02X} (mina): paleta não é a do build")
    by_key = {r.key: (area, r) for area, r in pairs}
    users, n = [], 0
    for key, v in manifest.items():
        if not (isinstance(v, dict) and "header" in v) or key not in by_key:
            continue
        area, r = by_key[key]
        n += area.number == MINES_AREA
        for st in read_room(rom, 0x8F0000 | (v["header"] & 0xFFFF)).states:
            if st.tileset in mines.TILESETS and area.number != MINES_AREA:
                users.append(key)
            # specs/19f: each Mines room in its own look (RoomDef.tileset: mines_rooms.LOOK, the rock or the pirate base)
            if area.number == MINES_AREA and r.tileset is not None and st.tileset != r.tileset:
                problems.append(f"{label}: {key}: estado no tileset {st.tileset:02X}, a cara dela é o {r.tileset:02X}")
            if area.number == MINES_AREA and st.fx:
                fx = rom.read(0x830000 | st.fx, 16)
                if fx[13] or fx[14]:
                    problems.append(f"{label}: {key}: FX ${st.fx:04X} liga a lista da área {MINES_AREA} (paleta ${fx[13]:02X}, "
                                    f"tiles ${fx[14]:02X})")
    for room in demo_rooms_kept(rom, base):
        if any(st.tileset in mines.TILESETS for st in read_room(rom, 0x8F0000 | room).states):
            users.append(f"demo ${room:04X}")
    if users:
        problems.append(f"{label}: tilesets da mina ({'/'.join(f'{t:02X}' for t in mines.TILESETS)}) usados fora da área "
                        f"{MINES_AREA}: {sorted(set(users))}")
    if not problems:
        what = (f"base pirata no {mines.BASE_TILESET:02X} (gráficos e tabela do {mines.BASE_SOURCE:02X}), rocha e fungos no "
                f"{mines.ROCK_TILESET:02X} (do {mines.ROCK_SOURCE:02X}), paletas em "
                + "/".join(f"${rom.u24(mines.entry(rom, t) + 6):06X}" for t in mines.TILESETS)
                + f", portas de onda (e a vertical) na linha {mines.PAINT_LINE}" if written
                else f"entradas {'/'.join(f'{t:02X}' for t in mines.TILESETS)} vanilla (sem sala da Mines; só a ROM de teste as "
                     f"escreve)")
        print(f"mina (specs/19d): {label}: {what}; usados só pela área {MINES_AREA} ({n} salas)")
    return problems


def check_arrival(rom) -> list[str]:
    """Built ROM (specs/07g): area 0's load stations 0 (the ship's save) and $12 (end of the
    frigate) go to the Tallon's Landing Site, and the escape landing stops at its ship's height."""
    manifest = json.loads((BUILT_ROM.parent / "manifest.json").read_text())
    problems = []
    for area in (TALLON, CHOZO, MAGMOOR, PHENDRANA, MINES):   # specs/12i: the Chozo's too; 17f: the Magmoor's; 18e: Phendrana's; 19e
        table = 0x800000 | rom.u16(LOAD_STATION_TABLE + 2 * area.number)
        for st in area.load_stations:
            got = rom.u16(table + LOAD_STATION_SIZE * st.index)
            # specs/12i: the game loads the station's door's destination (build.write_load_station's dummy door), not
            # the station's own room word: both checked
            door = rom.u16(0x830000 | rom.u16(table + LOAD_STATION_SIZE * st.index + 2))
            want = manifest.get(st.room, {}).get("header", -1) & 0xFFFF
            if got != want or door != want:
                problems.append(f"área {area.number}, estação ${st.index:02X}: sala ${got:04X}, porta para ${door:04X}, "
                                f"esperado {st.room} (${want:04X})")
    # specs/12i: every save station's PLM ($B76F) on its pedestal, its argument = the room's load station, in the room's
    # first state (the frigate's only there: "Save Disabled" after the boss)
    for area in AREAS:
        for r in area.rooms:
            if not r.save_station or r.key not in manifest:
                continue
            x, floor = r.save_station
            want = (build.SAVE_PLM, x, floor, area.station_in(r.key))
            if want not in room_plms(rom, manifest[r.key]["states"][0]):
                problems.append(f"{r.key}: sem o PLM de save ${build.SAVE_PLM:04X} em ({x},{floor}) com a estação "
                                f"{area.station_in(r.key)} da área {area.number}")
    # specs/12i: every map station's PLM ($B6D3, argument $8000) at cannon height over its base, in every state
    for area in AREAS:
        for r in area.rooms:
            if not r.map_station or r.key not in manifest:
                continue
            x, floor = r.map_station
            want = (build.MAP_STATION_PLM, x, floor - 2, build.MAP_STATION_ARG)
            if any(want not in room_plms(rom, st) for st in manifest[r.key]["states"]):
                problems.append(f"{r.key}: sem o PLM de map station ${build.MAP_STATION_PLM:04X} em ({x},{floor - 2})")
    # specs/19l: every missile station's PLM ($B6EB) at cannon height over its stem, in every state
    for area in AREAS:
        for r in area.rooms:
            if not r.missile_station or r.key not in manifest:
                continue
            x, floor = r.missile_station
            want = (build.MISSILE_STATION_PLM, x, floor - 2, build.MISSILE_STATION_ARG)
            if any(want not in room_plms(rom, st) for st in manifest[r.key]["states"]):
                problems.append(f"{r.key}: sem o PLM de missile station ${build.MISSILE_STATION_PLM:04X} em ({x},{floor - 2})")
    ship_room = next(r for r in TALLON.rooms if r.ship)
    top = ending.ship_top_y(ship_room.ship[1])
    if any(rom.u16(a + 1) != top for a in ending.LANDING_STOP_SITES):
        problems.append(f"pouso da nave no fim da fragata não para em y ${top:04X} ({ship_room.key})")
    return problems


def check_pause_maps(rom) -> list[str]:
    """Built ROM (specs/03, 07f): for every area with its own pause map, the tables
    build.write_pause_map writes: tilemap and reveal mask = pausemap.build of the built rooms, the
    pause name, the explored-map save list (count, start, offsets = AreaDef.map_save_bytes, which
    must hold every byte of the built rooms), the save icon of each save slot, map-station icons
    only for rooms that have one; areas without elevators yet have no elevator icons nor labels."""
    problems = []
    custom = {a.number: a.map_save_bytes() for a in AREAS if a.pause_map}
    starts = mapsave.layout(custom)
    for area in AREAS:
        if not area.pause_map:
            continue
        a, name = area.number, f"mapa da área {area.number} ({area.key})"
        tilemap, reveal = pausemap.build(area.rooms)
        if rom.read(rom.u24(build.PAUSE_TILEMAPS + 3 * a), len(tilemap)) != tilemap:
            problems.append(f"{name}: tilemap diferente de pausemap.build")
        if rom.read(0x820000 | rom.u16(build.PAUSE_MAP_REVEAL + 2 * a), len(reveal)) != reveal:
            problems.append(f"{name}: máscara da map station diferente de pausemap.build")
        if rom.read(0x820000 | rom.u16(build.PAUSE_AREA_LABELS + 2 * a), 24) != build.area_label(area.name):
            problems.append(f"{name}: nome da pausa não é {area.name!r}")
        offs = custom[a]
        if not set(mapsave.needed(reveal)) <= set(offs):
            problems.append(f"{name}: bytes das salas construídas fora da lista do save")
        if (rom.u8(mapsave.COUNTS + a), rom.u16(mapsave.PACKED_OFFS + 2 * a)) != (len(offs), starts[a]) \
                or list(rom.read(0x810000 | rom.u16(mapsave.LISTS + 2 * a), len(offs))) != offs:
            problems.append(f"{name}: lista do save diferente ({len(offs)} bytes em +{starts[a]} esperados)")

        def icons(kind: int) -> list[tuple[int, int]]:
            at, out = 0x820000 | rom.u16(build.MAP_ICONS + kind + 2 * a), []
            while rom.u16(at) != 0xFFFF and len(out) < 32:
                out.append((rom.u16(at), rom.u16(at + 2)))
                at += 4
            return out

        by_key = area.by_key()
        if not area.boss_room and "boss" in build.VANILLA_PAUSE[a] and icons(build.ICONS_BOSS):
            problems.append(f"{name}: sobrou ícone de chefe da área vanilla {icons(build.ICONS_BOSS)}")
        want = [pausemap.icon_xy(r, r.map_station[0] // 16) for r in area.rooms if r.map_station]
        if icons(build.ICONS_MAP_STATION) != want:
            problems.append(f"{name}: ícones de map station {icons(build.ICONS_MAP_STATION)}, esperado {want}")
        saves = icons(build.ICONS_SAVE)
        for st in area.load_stations:
            if st.index < build.SAVE_SLOTS:
                xy = pausemap.icon_xy(by_key[st.room], st.x // 256, st.y // 256)
                if st.index >= len(saves) or saves[st.index] != xy:
                    problems.append(f"{name}: ícone de save da estação {st.index} não está em {xy}")
        if "elevator_icons" in build.VANILLA_PAUSE[a]:
            if icons(build.ICONS_ELEVATOR) or len(saves) != len(build.VANILLA_PAUSE[a]["save"]) // 4:
                problems.append(f"{name}: sobrou ícone de elevador da área vanilla")
        if rom.u16(0x820000 | rom.u16(build.MAP_ELEVATOR_LABELS + 2 * a)) != 0xFFFF:
            problems.append(f"{name}: sobrou rótulo de elevador (\"to <área>\") da área vanilla")
    return problems


def check_wave_paint_free(areas=None) -> list[str]:
    """specs/10d: no room on the purple wave door's tileset uses its metatiles in the level (they are the door's).
    specs/12f: tileset $0C's (the ruins: its copy of the metatile table has them too) as well. specs/12g2: and no room of
    tileset $0C uses the white charge door's (beamdoors.CHARGE_METATILES). specs/19d: `areas` (default AREAS; the Mines' test
    area too, check_mines_test_rooms) and the Mines' looks."""
    wave, charge = set(beamdoors.PAINT_METATILES.values()), set(beamdoors.CHARGE_METATILES.values())
    problems = []
    for area in (AREAS if areas is None else areas):
        for r in area.rooms:
            ts = area.tileset_of(r)
            if ts not in (beamdoors.PAINT_TILESET, ruins.RUINS_TILESET, *lava.TILESETS, *ice.TILESETS,   # 17d: $09/$0A; 18d
                          *mines.TILESETS):   # specs/19d
                continue
            l1, _ = r.level().build_blocks()
            used = sorted({w & 0x3FF for w in l1} & wave)
            if used:
                problems.append(f"{r.key}: o nível usa os metatiles da porta de onda {[f'${m:03X}' for m in used]}")
            # specs/18d: the icy ruins ($1C) share the Chozo's $0C table, with the charge door's metatiles
            used = sorted({w & 0x3FF for w in l1} & charge) if ts in (ruins.RUINS_TILESET, ice.RUINS_TILESET) else []
            if used:
                problems.append(f"{r.key}: o nível usa os metatiles da porta de charge {[f'${m:03X}' for m in used]}")
            # specs/18i: tileset 4's table (the frigate's and the labs', $1B) has the vertical wave door's too; specs/18j: and
            # the snow look's ($01: its own copy of $00's)
            used = (sorted({w & 0x3FF for w in l1} & set(beamdoors.VERT_PAINT_METATILES.values()))
                    if ts in VERTICAL_WAVE_TILESETS else [])
            if used:
                problems.append(f"{r.key}: o nível usa os metatiles da porta de onda vertical {[f'${m:03X}' for m in used]}")
    return problems


# specs/18i: the tilesets whose metatile table has the vertical purple wave door's 8 metatiles (beamdoors.VERT_PAINT_METATILES):
# tileset 4's own copy (the frigate's, beamdoors.VERT_PAINT_TILESETS, and the labs' look, $1B, which shares it); specs/18j: the
# snow look's own copy (build.ice_metatiles; the North Quarantine Tunnel's ceiling door). The icy ruins' ($1C, the Chozo's $0C
# copy) has none yet.
VERTICAL_WAVE_TILESETS = frozenset({*beamdoors.VERT_PAINT_TILESETS, ice.LAB_TILESET, ice.SNOW_TILESET,
                                    *mines.TILESETS})   # specs/19d: both Mines looks' copies (build.mines_metatiles)


def check_vertical_wave_doors() -> list[str]:
    """specs/18i: a wave door on a floor or ceiling wall (its cap drawn with beamdoors.VERT_PAINT_METATILES, painted only in
    the tables of VERTICAL_WAVE_TILESETS: tileset 4's, the frigate's and the labs' look, smlib/ice.py LAB_TILESET; specs/18j:
    the snow look's, SNOW_TILESET) is only in a room of those tilesets: elsewhere its cap would be drawn with whatever that
    tileset holds there."""
    lock = tallon_rooms.LOCK_OF[tallon_rooms.WAVE]
    painted = VERTICAL_WAVE_TILESETS
    return [f"{r.key}: porta de onda {d.side}{d.screen} num tileset sem a pintura vertical dela ({area.tileset_of(r):02X}; só "
            f"{', '.join(f'{t:02X}' for t in sorted(painted))})"
            for area in AREAS for r in area.rooms for d in r.doors
            if d.side in beamdoors.VERTICAL and lock in (d.lock, d.dead_lock) and area.tileset_of(r) not in painted]


def check_charge_doors() -> list[str]:
    """specs/12g2: a charge door (its cap drawn with beamdoors.CHARGE_METATILES, painted only in tileset $0C's table and
    palette line beamdoors.CHARGE_LINE) is only in a room of tileset $0C (the Chozo's): elsewhere its cap would be drawn
    with whatever that tileset holds there."""
    lock = tallon_rooms.LOCK_OF[tallon_rooms.CHARGE]
    return [f"{r.key}: porta de charge {d.side}{d.screen} num tileset sem a pintura dela ({area.tileset_of(r):02X}; só o "
            f"{ruins.RUINS_TILESET:02X} tem)"
            for area in AREAS for r in area.rooms for d in r.doors
            if d.lock == lock and area.tileset_of(r) != ruins.RUINS_TILESET]


# tile word -> the sides with a wall (pausemap.WALL_TILES, flips included)
WALLS_OF_TILE = {word: frozenset(sides) for sides, word in pausemap.WALL_TILES.items()}


def check_map_shapes(rom) -> list[str]:
    """specs/10c: on the built pause map of every area, each screen of a room has the tile of its shape, read from the
    ROM's tilemap and checked against the room's level (not against pausemap.build): a screen of solid rock from edge
    to edge (every block of type $8) is blank; any other screen has a wall exactly on the sides whose neighbour is
    outside the room or solid rock (the save room's one-screen tile aside)."""
    problems = []
    for area in AREAS:
        if not area.pause_map:
            continue
        base = rom.u24(build.PAUSE_TILEMAPS + 3 * area.number)
        for r in area.rooms:
            l1, _ = r.level().build_blocks()
            wb = r.width * 16
            solid = {(sx, sy) for sy in range(r.height) for sx in range(r.width)
                     if all(l1[(sy * 16 + y) * wb + sx * 16 + x] >> 12 == 8 for y in range(16) for x in range(16))}
            for sx, sy, tx, ty in pausemap.cells(r):
                word = rom.u16(base + 2 * pausemap.tile_index(tx, ty))
                tag = f"mapa da área {area.number}: {r.key} tela ({sx},{sy})"
                if (sx, sy) in solid:
                    if word != pausemap.BLANK:
                        problems.append(f"{tag} é rocha maciça e o mapa a desenha (${word:04X})")
                    continue
                if r.save_station and r.width == r.height == 1:
                    continue
                want = frozenset(side for side, (nx, ny) in (("L", (sx - 1, sy)), ("R", (sx + 1, sy)), ("T", (sx, sy - 1)),
                                                             ("B", (sx, sy + 1)))
                                 if not (0 <= nx < r.width and 0 <= ny < r.height) or (nx, ny) in solid)
                got = WALLS_OF_TILE.get(word & ~pausemap.PALETTE)
                if got != want:
                    problems.append(f"{tag}: paredes {sorted(got) if got is not None else f'${word:04X}'}, a forma da sala pede {sorted(want)}")
    return problems


def tallon_map_bytes(rooms) -> list[int]:
    """Bytes of the explored map the save keeps for these Tallon rooms (mapsave.needed)."""
    return mapsave.needed(pausemap.build(rooms)[1])


def check_tallon() -> list[str]:
    """The whole Tallon table (44 rooms, tallon/rooms.py), built or not: against Prime's data, the
    room/map checks of check_layout on all regions together and on each region alone (the links to
    regions that are off are dropped), and the area 0 map in the save: the vanilla list place holds
    mapsave.LIST_ROOM[0] bytes (spec 03); past that 07f must move the list."""
    problems = tallon_rooms.check_prime(PRIME_WORLDS)
    problems += check_layout(TALLON, tallon_rooms.ALL_ROOMS)
    for region in tallon_rooms.REGIONS:
        problems += [f"só a região {region}: {p}"
                     for p in check_layout(TALLON, tallon_rooms.build_rooms({region}))]
    for r in tallon_drafts():   # drawn rooms not built yet: reach as if their region were on
        problems += [f"desenhada fora do build: {p}" for p in check_room(TALLON, r)]
    problems += check_tallon_rounds()
    problems += check_chozo_rounds()   # specs/12f: the Chozo's rooms and items in the same walk
    problems += check_world_rounds()   # specs/12m: both areas' rounds, the elevators' two sides, the item percentage
    problems += check_magmoor_rounds()   # specs/17e: the Magmoor's rooms in the same walk
    problems += check_phendrana_rounds()   # specs/18e: Phendrana's rooms in the same walk
    problems += check_mines_rounds()   # specs/19e: the Mines' rooms in the same walk
    problems += check_epic_magmoor()   # specs/17j: epic 17 closed
    problems += check_epic_phendrana()   # specs/18n: epic 18 closed
    problems += check_epic_mines()   # specs/19m: epic 19 closed
    problems += check_epic_impact()   # specs/20j: epic 20 closed
    problems += check_tallon_return()
    problems += check_tallon_round_stuck()
    problems += check_breakables()
    problems += check_item_geometry()
    problems += check_niche_caps()   # specs/18i
    problems += check_tallon_water()
    problems += check_tallon_enemies()
    problems += check_chozo_enemies()   # specs/12h
    problems += check_magmoor_enemies()   # specs/17g
    problems += check_phendrana_enemies()   # specs/18g
    problems += check_mines_enemies()   # specs/19g
    problems += check_impact_enemies()   # specs/20f
    if problems:
        return problems
    try:
        offs = tallon_map_bytes(tallon_rooms.ALL_ROOMS)
    except ValueError as e:   # a map tile used twice
        return [f"tallon: {e}"]
    problems += [f"tallon: {p}" for p in mapsave.check({TALLON.number: offs})]
    if len(offs) > mapsave.LIST_ROOM[TALLON.number]:
        problems.append(f"tallon: mapa usa {len(offs)} bytes da SRAM; o lugar vanilla da área "
                        f"{TALLON.number} tem {mapsave.LIST_ROOM[TALLON.number]}")
    return problems


# the reach model's Loadout field of each GEOMETRY item (tallon/rooms.py)
LOADOUT_FIELD = {tallon_rooms.SPACE_JUMP: "space_jump", tallon_rooms.GRAVITY: "gravity", tallon_rooms.MORPH: "morph",
                 tallon_rooms.BOMBS: "bombs", tallon_rooms.POWER_BOMB: "power_bomb",
                 tallon_rooms.PLASMA: "plasma"}   # specs/18i: the Plasma Beam opens the in-room plasma caps (RoomDef.caps)


def items_loadout(have, water: bool = False) -> reach.Loadout:
    """The reach model's loadout for a set of gate items (tallon/rooms.py)."""
    return reach.Loadout(water=water, **{f: True for item, f in LOADOUT_FIELD.items() if item in have})


def loadout_items(loadout: reach.Loadout) -> frozenset:
    """The gate items (GEOMETRY) a reach loadout has."""
    return frozenset(item for item, f in LOADOUT_FIELD.items() if getattr(loadout, f))


def with_items(loadout: reach.Loadout, items) -> reach.Loadout:
    """`loadout` plus the GEOMETRY items `items`."""
    return dataclasses.replace(loadout, **{LOADOUT_FIELD[i]: True for i in items})


# geometry items the on-foot model walks (the others: Space Jump = flood fill, Gravity = the room's water)
FOOT_GEOMETRY = frozenset({tallon_rooms.MORPH, tallon_rooms.BOMBS, tallon_rooms.POWER_BOMB})


ELEVATOR = "elevador"   # specs/12f: the entry/exit of a room's elevator in the progression walk (a door index otherwise)


def tallon_room_reach(r, entry, have=frozenset()) -> tuple[set, set[tuple[int, int]]]:
    """Doors of room `r` Samus reaches from `entry` (a door index, or None = the gunship, load
    station 0) with the gate items `have`, on foot (specs/07b; specs/09d: with the Morph Ball's ball and
    the Bombs' blocks) or with Space Jump (flood fill), and the blocks her body gets
    into: with the flood fill the blocks of flood_touch (specs/12k: where she can stand or rest in the ball), on foot
    the 3 standing rows of every stand and the block of every ball reached (an item there is picked up, specs/07h). In a flooded room the jump is the
    underwater one, with or without the Gravity Suit, and the Space Jump only works with the suit (specs/07l).
    specs/12f (the Tallon and the Chozo walked together): `entry` may be ELEVATOR (she arrives standing on the room's
    elevator platform), and ELEVATOR is among the exits when she gets onto the platform."""
    loadout = items_loadout(have, r.water)
    lv = r.level()
    l1, bts = lv.build_blocks()
    wb, hb = lv.wb, lv.hb
    pad = elevator_stands(r)
    if entry is None:
        st = TALLON.load_stations[0]
        start_cell = (st.x // 16, st.y // 16)
    elif entry == ELEVATOR:
        start_cell = min(pad)
    else:
        d = r.doors[entry]
        start_cell = door_inner_cells(d.side, d.screen, wb, hb)[0]
    if loadout.flies:
        types = reach.with_lava(with_caps(r, elevator_solid(r, reach.with_breakables([w >> 12 for w in l1], bts, loadout)),
                                          loadout), wb, r.liquid)   # specs/18i: the in-room caps; 20g: acid

        def passable(x: int, y: int) -> bool:
            return 0 <= x < wb and 0 <= y < hb and types[y * wb + x] not in SOLID_TYPES
        seen = reach.flood(passable, start_cell, loadout)
        exits = {i for i, d in enumerate(r.doors) if door_inner_cells(d.side, d.screen, wb, hb)[0] in seen}
        return exits | ({ELEVATOR} if pad & seen else set()), flood_touch(types, wb, hb, seen)
    grid, seen, walk = tallon_foot_walk(r, entry, loadout, (l1, bts))
    exits = {i for i, d in enumerate(r.doors) if reach.door_reached(grid, d.side, d.screen, seen, walk)}
    return exits | ({ELEVATOR} if pad & seen else set()), reach.body_cells(seen)


def flood_touch(types: list[int], wb: int, hb: int, seen: set) -> set[tuple[int, int]]:
    """specs/12k: the blocks of the Space Jump's flood fill `seen` where an item is picked up: the 3 rows of every place in
    it she can stand on (a floor under her, 3 free rows: reach.Grid.stands) and every block a ball rests in under a roof
    (a floor under it, no free block over it: a 1-row tunnel). A block she only flies through, or one on a ledge with 2
    free rows over it, does not count: 12j's Training Chamber E-tank sat on such a ledge, the fill took it, and in the game
    she could not stand there (the validator gap 12j recorded)."""
    g = reach.Grid(types, wb, hb)
    stands = {(x, y) for x, y in seen if g.stands(x, y)}
    balls = {(x, y, reach.BALL) for x, y in seen if g.body(x, y) and g.floor(x, y + 1) and not g.body(x, y - 1)}
    return reach.body_cells(stands | balls)


def tallon_foot_walk(r, entry, loadout: reach.Loadout, blocks=None) -> tuple[reach.Grid, set, reach.Loadout]:
    """The on-foot walk of room r from `entry` (a door index, or None = the gunship): its grid, the states reached
    (empty if there is no place to stand there) and the walk's loadout (`loadout` without the Space Jump)."""
    l1, bts = blocks or r.level().build_blocks()
    wb, hb = r.width * 16, r.height * 16
    walk = dataclasses.replace(loadout, space_jump=False)
    grid = foot_grid(r, l1, bts, wb, hb, walk)
    if entry is None:
        st = TALLON.load_stations[0]
        start = grid.land(st.x // 16, st.y // 16)
    elif entry == ELEVATOR:   # specs/12f: standing on the platform (validate.check_room proves she can)
        pad = elevator_stands(r)
        start = min(pad) if all(grid.stands(*s) for s in pad) else None
    else:
        d = r.doors[entry]
        start = reach.door_entry(grid, d.side, d.screen)
    return grid, (reach.reach(grid, [start], walk) if start is not None else set()), walk


_progress_cache = None   # tallon_progress_built(), reset by check() (the mutation scripts change the tables)
_walk_memo: dict = {}    # tallon_room_walk, reset by check()


def reset_tallon_cache() -> None:
    """Forget the rounds and the room walks (check() does it; so must a script that changes the tables)."""
    global _progress_cache
    _progress_cache = None
    _walk_memo.clear()


def tallon_room_walk(r, entry, have) -> tuple[set, set[tuple[int, int]]]:
    """tallon_room_reach, memoised until the next check(): it depends only on the GEOMETRY items of `have`."""
    k = (r.key, entry, frozenset(have) & (tallon_rooms.GEOMETRY | room_cap_items(r)))   # specs/18i: and its caps' beams
    if k not in _walk_memo:
        _walk_memo[k] = tallon_room_reach(r, entry, k[2])
    return _walk_memo[k]


@dataclasses.dataclass(frozen=True)
class Round:
    """One round of the progression walk (specs/09f, epic 09 decision 3)."""
    have: frozenset     # what Samus has: what the items picked up in the rounds before give (items.GRANTS)
    states: frozenset   # the (room, entry) states she gets to (entry None = the gunship, load station 0)
    rooms: frozenset    # rooms first reached in this round
    items: frozenset    # placed items first picked up in this round: index n in tallon/items.py ITEMS, ("chozo", n)
                        # in chozo/items.py ITEMS (specs/12f)


def world_rooms() -> list:
    """specs/12f: the rooms the progression walk goes through: the Tallon's and the Chozo's (the elevators link them); specs/17e:
    and the Magmoor's (its two elevator rooms, dead ends: check_magmoor_rounds); specs/18e: and Phendrana's (its two elevator
    rooms, dead ends: check_phendrana_rounds); specs/19e: and the Mines' (its two elevator rooms, dead ends: check_mines_rounds)."""
    # specs/20e: the Impact Crater's rooms (in area 0, TALLON's AreaDef) are left out: the Artifact Temple's teleporter opens only
    # once the Omega Pirate is dead, and check_impact_rooms walks them from it with that round's gear
    return ([r for r in TALLON.rooms if not r.key.startswith(impact_rooms.PREFIX)] + CHOZO.rooms + MAGMOOR.rooms
            + PHENDRANA.rooms + MINES.rooms)


def world_items(built: set[str]) -> list[tuple]:
    """(key, item) of the placed items of the Tallon (key n) and of the Chozo (key ("chozo", n)), specs/12f; specs/17f: and of
    the Magmoor (key ("magmoor", n)); specs/18f: and of Phendrana (key ("phendrana", n)); specs/19f: and of the Mines (key
    ("mines", n))."""
    return (list(tallon_items.placed(built)) + [(("chozo", n), it) for n, it in chozo_items.placed(built)]
            + [(("magmoor", n), it) for n, it in magmoor_items.placed(built)]
            + [(("phendrana", n), it) for n, it in phendrana_items.placed(built)]
            + [(("mines", n), it) for n, it in mines_items.placed(built)])


# specs/17f: an item key's world -> its items module; specs/18f: Phendrana's
ITEM_TABLES = {"chozo": chozo_items, "magmoor": magmoor_items, "phendrana": phendrana_items, "mines": mines_items}   # 19f


def item_world(key) -> str:
    """The world of a placed item's key: "tallon" (n), "chozo" (("chozo", n)), "magmoor" (("magmoor", n)) or (specs/18f)
    "phendrana" (("phendrana", n))."""
    return key[0] if isinstance(key, tuple) else "tallon"


def item_of(key):
    return ITEM_TABLES[key[0]].ITEMS[key[1]] if isinstance(key, tuple) else tallon_items.ITEMS[key]


def item_bit(key) -> int:
    """The item bit of a placed item's key (tallon/items.py, chozo/items.py, magmoor/items.py BITS)."""
    return ITEM_TABLES[key[0]].BITS[key[1]] if isinstance(key, tuple) else tallon_items.BITS[key]


def exit_to(r, i) -> tuple[str, object]:
    """The (room, entry) state an exit `i` of room `r` leads to: a door's room and door, or the elevator's other room."""
    if i == ELEVATOR:
        return elevator_target(r.key), ELEVATOR
    d = r.doors[i]
    return d.to_room, d.to_door


def door_open(r, d, have) -> bool:
    """Samus may go through door `d` of room `r` with `have`: every item of its gate but the GEOMETRY ones (the room walk
    decides those); specs/14c: a boss door's gate (chozo_rooms.BOSS_GATE) only once the room's arena can be won with what
    she has (its Arena.needs: she is in the arena when she gets to the door)."""
    if chozo_rooms.BOSS_GATE in d.gate:
        arena = chozo_bosses.arena_of(r.key)
        # specs/14d: an ITEM arena's door shuts only once Samus takes its item (boss_locks: only with the arena's `needs`)
        if arena is None or not (arena.needs <= have or arena.condition == chozo_bosses.ITEM):
            return False
    return d.gate - tallon_rooms.GEOMETRY - {chozo_rooms.BOSS_GATE} <= have


def exit_open(r, i, have) -> bool:
    """Samus may go through exit `i` of room `r` with `have` (door_open); an elevator has no gate."""
    return i == ELEVATOR or door_open(r, r.doors[i], have)


def tallon_rounds(rooms, room_reach=None) -> list[Round]:
    """The rounds from the Landing Site gunship (specs/09f, replaces 07k's hypothetical tiers). Round 0 starts with
    the Power Beam only; each round walks the rooms entry by entry (room_reach: on foot, or the Space Jump's flood
    fill), goes through a door only if Samus has every item of its gate but the GEOMETRY ones (the room walk decides
    those: a ledge, a Morph Ball tunnel, specs/07m, 09d), and picks up every item her body gets to; what they give
    (items.GRANTS) counts from the next round on. The walk stops at the first pass that adds no room and no item:
    that pass is not a round, and it is not an error (with no new item the next pass would have the same
    equipment: the fixed point; in the Tallon the X-Ray gives `xray`, which no gate asks for)."""
    room_reach = room_reach or tallon_room_walk
    by_key = {r.key: r for r in rooms}
    ship = next(r.key for r in rooms if r.ship)
    spots: dict[str, list[tuple[object, tuple[int, int]]]] = {}
    for n, it in world_items(set(by_key)):
        spots.setdefault(it.room, []).append((n, it.spot))
    locks = boss_locks(set(by_key))
    have, out, rooms_before, items_before = frozenset(), [], set(), set()
    while True:
        states, queue, picked = {(ship, None)}, [(ship, None)], set()
        while queue:
            key, entry = queue.pop()
            r = by_key[key]
            exits, body = room_reach(r, entry, have)
            # specs/14b: an arena's prize (the boss lock) only once the fight can be won with what she has (Arena.needs)
            picked |= {n for n, spot in spots.get(key, ()) if spot in body and (n not in locks or locks[n].needs <= have)}
            for i in exits:
                nxt = exit_to(r, i)
                if nxt[0] in by_key and exit_open(r, i, have) and nxt not in states:
                    states.add(nxt)
                    queue.append(nxt)
        new_rooms = {k for k, _ in states} - rooms_before
        new_items = picked - items_before
        if not new_rooms and not new_items:
            return out
        out.append(Round(have, frozenset(states), frozenset(new_rooms), frozenset(new_items)))
        rooms_before |= new_rooms
        items_before |= new_items
        have = have.union(*(tallon_items.GRANTS[item_of(n).kind] for n in picked))


def boss_locks(built: set[str]) -> dict:
    """specs/14b: the "boss" lock of the progression walk: placed item key -> the arena (tools/chozo/bosses.py ARENAS) whose
    end spawns it; the walk picks it up only when Samus is in its room with the arena's `needs` (the fight won). specs/14d:
    and an ITEM arena's item (the one that starts its fight): taking it shuts the room's boss door until the fight is won,
    so the walk takes it only with the arena's `needs` (before, the door is open: door_open)."""
    out = {}
    for n, it in world_items(built):
        bit = item_bit(n)
        for a in chozo_bosses.ARENAS:
            if a.prize == (it.room, it.spot) or (a.condition == chozo_bosses.ITEM and a.arg == bit and a.room == it.room):
                out[n] = a
    return out


def tallon_progress_built() -> tuple[list[Round], dict[str, int], dict, dict[str, frozenset]]:
    """The rounds of the built rooms (walked once per check()), the first round of each room and of each placed
    item, and what Samus has when she first gets into each room (the equipment of that round: specs/09b's
    `arrival`, for the water and the enemy fairness rules). specs/12f: the Tallon and the Chozo walked together
    (world_rooms: the elevators link them); the Tallon's checks and line look at the Tallon's rooms and items only."""
    global _progress_cache
    if _progress_cache is None:
        rounds = tallon_rounds(world_rooms())
        first = {k: n for n, rd in enumerate(rounds) for k in rd.rooms}
        first_item = {i: n for n, rd in enumerate(rounds) for i in rd.items}
        _progress_cache = rounds, first, first_item, {k: rounds[n].have for k, n in first.items()}
    return _progress_cache


def have_names(have) -> list[str]:
    return sorted(have) or ["Power Beam"]


def check_tallon_return() -> list[str]:
    """specs/09d (the cheap part of epic 09's "no point of no return", 09f): in every round, from every room and
    entry Samus gets to with what she has then, the Landing Site can be reached with those same items (rooms
    linked through the doors her walk of each room gets to), and in the Landing Site the gunship's top from
    every entry she gets in by."""
    by_key = {r.key: r for r in world_rooms()}   # specs/12f: from the Chozo too, through the elevators
    home = next(r for r in TALLON.rooms if r.ship)
    cx, ground = home.ship
    top = (cx, ground + ending.SHIP_TOP_ROW - 1)
    problems = []
    try:
        rounds = tallon_progress_built()[0]
    except ValueError as e:   # an item in a room that is not built (check_tallon_rounds says it too)
        return [f"tallon: {e}"]
    for k, rd in enumerate(rounds):
        have, states = rd.have, rd.states
        nxt = {}
        for key, entry in states:
            r = by_key[key]
            exits, _ = tallon_room_walk(r, entry, have)
            nxt[(key, entry)] = {exit_to(r, i) for i in exits if exit_open(r, i, have) and exit_to(r, i)[0] in by_key}
        good = {s for s in states if s[0] == home.key}
        for key, entry in sorted(good, key=str):
            if top not in tallon_room_walk(home, entry, have)[1]:
                problems.append(f"tallon: rodada {k}: na {home.key} pela entrada {entry} a nave fica fora de alcance")
        changed = True
        while changed:
            changed = False
            for s, succ in nxt.items():
                if s not in good and succ & good:
                    good.add(s)
                    changed = True
        for key, entry in sorted(set(states) - good, key=str):
            problems.append(f"tallon: rodada {k} ({have_names(have)}): de {key} (entrada {entry}) "
                            f"não há volta à nave")
    return problems


def check_tallon_round_stuck() -> list[str]:
    """specs/09f (epic 09 decision 4, final proof 3): in every round, every room Samus gets to is walked from every
    entry she gets in by with that round's equipment (and the room's water), and no place she gets to may leave her
    with no way back to a door she can use then (no gate, or one whose items but the GEOMETRY ones she has). With
    the Space Jump the model is the flood fill (open space connected both ways): nothing to walk. check_room walks
    every room only with the arrival's loadout, the Morph Ball and the Bombs (and the Power Bomb by its blocks)."""
    problems = []
    try:
        rounds = tallon_progress_built()[0]
    except ValueError as e:   # an item in a room that is not built (check_tallon_rounds says it too)
        return [f"tallon: {e}"]
    by_key = {r.key: r for r in world_rooms()}   # specs/12f: the Chozo's rooms too
    done = set()
    for k, rd in enumerate(rounds):
        for key, entry in sorted(rd.states, key=str):
            r = by_key[key]
            loadout = items_loadout(rd.have, r.water)
            if loadout.flies:
                continue
            usable = tuple((d.side, d.screen) for d in r.doors if door_open(r, d, rd.have))
            memo = (key, entry, loadout, usable)
            if memo in done:
                continue
            done.add(memo)
            grid, seen, walk = tallon_foot_walk(r, entry, loadout)
            # the elevator's platform is a way out too (specs/12f: the walk rides the elevators)
            trapped = reach.stuck(grid, seen, list(usable), walk, elevator_stands(r)) if seen else set()
            if trapped:
                x, y = min(s[:2] for s in trapped)
                problems.append(f"tallon: rodada {k} ({have_names(rd.have)}): em {key} pela entrada {entry}, "
                                f"{len(trapped)} lugares sem volta a uma porta que ela possa usar "
                                f"(ex.: coluna {x}, pé na linha {y})")
    return problems


def check_tallon_rounds() -> list[str]:
    """specs/09f (was 07k/07h's check_tallon_tiers): the round each built room is first reached in =
    tallon_rooms.FIRST_ROUND, the round each placed item (tallon/items.py) is first picked up in = its Item.round;
    every built room and placed item reached; each placed item sits in an air block of its room, away from the
    doors."""
    problems = []
    try:
        rounds, got, got_items, _ = tallon_progress_built()
    except ValueError as e:   # an item in a room that is not built
        return [f"tallon: {e}"]

    def when(n: int) -> str:
        return f"na rodada {n} (com {have_names(rounds[n].have)})"

    want = tallon_rooms.FIRST_ROUND
    for r in TALLON.rooms:
        if r.key.startswith(impact_rooms.PREFIX):   # specs/20e: the crater's rounds are check_impact_rooms'
            continue
        g, w = got.get(r.key), want.get(r.key)
        if g is None:
            problems.append(f"tallon: {r.key} inalcançável da nave em todas as {len(rounds)} rodadas")
        elif g != w:
            problems.append(f"tallon: {r.key} fica alcançável {when(g)}, FIRST_ROUND diz {w}")
    extra = set(want) - set(TALLON.by_key())
    if extra:
        problems.append(f"tallon: FIRST_ROUND tem salas fora do build: {sorted(extra)}")
    by_key = TALLON.by_key()
    for n, it in tallon_items.placed(set(by_key)):
        r, (x, y) = by_key[it.room], it.spot
        tag = f"tallon: item {n} ({tallon_items.KIND_NAME[it.kind]}) em {it.room} ({x},{y})"
        l1, _ = r.level().build_blocks()
        wb, hb = r.width * 16, r.height * 16
        doors = {c for d in r.doors for c in door_inner_cells(d.side, d.screen, wb, hb)}
        if not (0 <= x < wb and 0 <= y < hb) or l1[y * wb + x] >> 12 != 0:
            problems.append(f"{tag} não está num bloco de ar")
        elif (x, y) in doors or any(abs(x - dx) + abs(y - dy) < 2 for dx, dy in doors):
            problems.append(f"{tag} está na passagem de uma porta")
        g = got_items.get(n)   # the Tallon's items (specs/12f: the Chozo's are ("chozo", n), check_chozo_rounds)
        if g is None:
            problems.append(f"{tag} nunca é pego (inalcançável da nave em todas as {len(rounds)} rodadas)")
        elif g != it.round:
            problems.append(f"{tag} é pego {when(g)}, declarado na rodada {it.round}")
    for n, it in enumerate(tallon_items.ITEMS):
        if (it.spot is None) != (it.round is None):
            problems.append(f"tallon: item {n} em {it.room}: lugar e rodada vêm juntos")
    return problems


def item_spot_problems(tag: str, r, spot) -> list[str]:
    """An item's spot (x, y) must be an air block of its room, away from the doorways (specs/07h)."""
    x, y = spot
    l1, _ = r.level().build_blocks()
    wb, hb = r.width * 16, r.height * 16
    doors = {c for d in r.doors for c in door_inner_cells(d.side, d.screen, wb, hb)}
    if not (0 <= x < wb and 0 <= y < hb) or l1[y * wb + x] >> 12 != 0:
        return [f"{tag} não está num bloco de ar"]
    if (x, y) in doors or any(abs(x - dx) + abs(y - dy) < 2 for dx, dy in doors):
        return [f"{tag} está na passagem de uma porta"]
    return []


def check_chozo_rounds() -> list[str]:
    """specs/12f: the Chozo's built rooms and items in the walk of the Tallon and the Chozo together (tallon_rounds over
    world_rooms: the elevators link the areas): the round each built Chozo room is first reached in = chozo_rooms.FIRST_ROUND,
    or, for a room that waits for a region not built yet (chozo_rooms.WAITS_FOR), never; the round each placed Chozo item
    (chozo/items.py) is first picked up in = its Item.round; each item in an air block away from the doors. The Tallon's
    rooms and items keep their own check (check_tallon_rounds), so its line stays the Tallon's. Prints the line "chozo
    (specs/12f)": the Chozo's rooms and items per round."""
    problems = []
    try:
        rounds, got, got_items, _ = tallon_progress_built()
    except ValueError as e:   # an item in a room that is not built
        return [f"chozo: {e}"]
    want = chozo_rooms.FIRST_ROUND
    for r in CHOZO.rooms:
        g, w = got.get(r.key), want.get(r.key)
        if r.key in chozo_rooms.WAITS_FOR:
            if g is not None:
                problems.append(f"chozo: {r.key} espera a região {chozo_rooms.WAITS_FOR[r.key]} mas fica alcançável "
                                f"na rodada {g} (com {have_names(rounds[g].have)})")
        elif g is None:
            problems.append(f"chozo: {r.key} inalcançável da nave do Tallon em todas as {len(rounds)} rodadas")
        elif g != w:
            problems.append(f"chozo: {r.key} fica alcançável na rodada {g} (com {have_names(rounds[g].have)}), "
                            f"FIRST_ROUND diz {w}")
    extra = (set(want) | set(chozo_rooms.WAITS_FOR)) - set(CHOZO.by_key())
    if extra:
        problems.append(f"chozo: FIRST_ROUND/WAITS_FOR com salas fora do build: {sorted(extra)}")
    by_key = CHOZO.by_key()
    try:
        placed = chozo_items.placed(set(by_key))
    except ValueError as e:
        return problems + [f"chozo: {e}"]
    for n, it in placed:
        tag = f"chozo: item {n} ({chozo_items.KIND_NAME[it.kind]}) em {it.room} {it.spot}"
        problems += item_spot_problems(tag, by_key[it.room], it.spot)
        g = got_items.get(("chozo", n))
        if g is None:
            problems.append(f"{tag} nunca é pego (inalcançável da nave do Tallon em todas as {len(rounds)} rodadas)")
        elif g != it.round:
            problems.append(f"{tag} é pego na rodada {g} (com {have_names(rounds[g].have)}), declarado na rodada {it.round}")
    for n, it in enumerate(chozo_items.ITEMS):
        if (it.spot is None) != (it.round is None):
            problems.append(f"chozo: item {n} em {it.room}: lugar e rodada vêm juntos")
    if not problems:
        rooms_by = {k: sorted(key.removeprefix("chozo_") for key in rd.rooms if key in by_key) for k, rd in enumerate(rounds)}
        items_by = {k: sum(item_world(i) == "chozo" for i in rd.items) for k, rd in enumerate(rounds)}
        per = "; ".join(f"rodada {k}: {len(rooms_by[k])} salas, {items_by[k]} itens" for k in range(len(rounds))
                        if rooms_by[k] or items_by[k])
        waiting = ", ".join(f"{k.removeprefix('chozo_')} (espera a região {g})" for k, g in chozo_rooms.WAITS_FOR.items())
        print(f"chozo (specs/12f, 12i, 12j, 12k, 12l; regiões ativas: {''.join(sorted(chozo_rooms.ACTIVE_REGIONS))}): {len(CHOZO.rooms)} salas "
              f"construídas, alcançáveis a pé da nave do Tallon: {sum(k in by_key for k in got)}, "
              f"{sum(item_world(i) == 'chozo' for i in got_items)} itens; andadas junto com o Tallon (mesmas rodadas): {per}; "
              f"fora das rodadas: {waiting or 'nenhuma'}")
    return problems


# specs/12m: what each item kind adds to the game's ending percentage (CalcItemPercentageCount, $8B:E627): the capacity it
# adds (the arguments of the vanilla collect instructions; the full chain in the emulator ends with them: 799 energy, 160
# missiles, 10 power bombs) or the bit it sets in collected items ($09A4) / collected beams ($09A8)
ITEM_GAIN = {0xEED7: ("energy", 100), 0xEEDB: ("missiles", 5), 0xEEE3: ("power_bombs", 5),
             0xEEE7: ("items", 0x1000), 0xEF07: ("items", 0x0001), 0xEF0B: ("items", 0x0020), 0xEF0F: ("items", 0x8000),
             0xEF1B: ("items", 0x0200), 0xEF23: ("items", 0x0004),
             0xEEEB: ("beams", 0x1000), 0xEEEF: ("beams", 0x0002), 0xEEFB: ("beams", 0x0001), 0xEF13: ("beams", 0x0008),
             0xEEDF: ("supers", 5),   # specs/18l: the Super Missile (5 of capacity, as the vanilla collect instruction)
             0xEF17: ("items", 0x4000)}   # specs/19f: the Grapple Beam (its equipment bit, $8B:E721's 10th)


def item_percentage(rom, have: dict) -> int:
    """The ending's item percentage (CalcItemPercentageCount, $8B:E627) for `have` (energy, reserve, missiles, supers,
    power_bombs: capacities; items, beams: bit masks), its tables read from the ROM's bytes ($8B:E70D the 5 RAM words,
    $8B:E717 their divisors, $8B:E721 the 11 item bits, $8B:E737 the 5 beam bits)."""
    words = lambda addr, n: [rom.u16(addr + 2 * i) for i in range(n)]   # noqa: E731
    by_ram = {0x09C4: "energy", 0x09D4: "reserve", 0x09C8: "missiles", 0x09CC: "supers", 0x09D0: "power_bombs"}
    n = sum(have.get(by_ram[a], 0) // d for a, d in zip(words(0x8BE70D, 5), words(0x8BE717, 5)))
    n += sum(bool(b & have.get("items", 0)) for b in words(0x8BE721, 11))
    return n + sum(bool(b & have.get("beams", 0)) for b in words(0x8BE737, 5))


def items_gear(placed) -> tuple[dict, list[str]]:
    """The gear of all the `placed` items taken (ITEM_GAIN: capacities added, item and beam bits), from the start's 99 energy;
    and the problems (an item kind with no value). specs/20i: the same sum for the ending's check (check_impact_ending)."""
    problems, have = [], {"energy": 99}
    for n, it in placed:
        if it.kind not in ITEM_GAIN:
            problems.append(f"rodadas: item {n} em {it.room}: tipo {it.kind:04X} sem valor na porcentagem (ITEM_GAIN)")
            continue
        what, v = ITEM_GAIN[it.kind]
        have[what] = have.get(what, 0) | v if what in ("items", "beams") else have.get(what, 0) + v
    return have, problems


def check_world_rounds() -> list[str]:
    """specs/12m (the declared rounds across both areas; specs/17j: the three, the Magmoor's too; specs/18n: the four,
    Phendrana's too; specs/19f: and the Mines' items, in the line and the percentage): the walk of the Tallon, the Chozo, the
    Magmoor, Phendrana and the Mines together (tallon_progress_built) takes every placed item of the five areas, each in its declared round (check_tallon_rounds / check_chozo_rounds / check_magmoor_rounds /
    check_phendrana_rounds compare them one by one), every declared round has something new (a room or an item) and the walk has
    exactly the declared rounds; the ending's item percentage of all the items taken (ITEM_GAIN, the formula of $8B:E627 with
    its tables read from the base ROM) is one per item. Prints the line "rodadas (specs/12m, 17j, 18n)". (The two sides of an
    elevator are always first reached in the same round: the walk rides it both ways; specs/12l's flooded pool keeps the
    Tallon's rounds, check_tallon_rounds.) specs/17f's guard stays (specs/18e: and Phendrana's): no round is there for the
    Magmoor or Phendrana alone (every round adds a room or an item of the Tallon or of the Chozo: they never move their rounds,
    epic 17's and epic 18's criterion 3)."""
    problems = []
    try:
        rounds, first, first_item, _ = tallon_progress_built()
        placed = world_items({r.key for r in world_rooms()})
    except ValueError as e:
        return [f"rodadas: {e}"]
    declared = {n: it.round for n, it in placed}
    if set(first_item) != set(declared):
        problems.append(f"rodadas: itens com lugar fora do passeio: {sorted(set(declared) - set(first_item), key=str)}")
    want_rounds = ({r for r in declared.values()} | set(tallon_rooms.FIRST_ROUND.values()) | set(chozo_rooms.FIRST_ROUND.values())
                   | set(magmoor_rooms.FIRST_ROUND.values()) | set(phendrana_rooms.FIRST_ROUND.values())   # specs/18n
                   | set(mines_rooms.FIRST_ROUND.values()))   # specs/19e
    if want_rounds != set(range(len(rounds))):
        problems.append(f"rodadas: declaradas {sorted(want_rounds)}, o passeio tem {len(rounds)} (0–{len(rounds) - 1})")
    for k, rd in enumerate(rounds):
        if not rd.rooms and not rd.items:
            problems.append(f"rodadas: a rodada {k} não acrescenta sala nem item")
        if (not {r for r in rd.rooms if not r.startswith(("magmoor_", "phendrana_", "mines_"))}
                and not {i for i in rd.items if item_world(i) not in ("magmoor", "phendrana", "mines")}):
            problems.append(f"rodadas: a rodada {k} só acrescenta salas ou itens da Magmoor, de Phendrana ou da Mines")   # specs/17f, 18e, 19e
    have, unknown = items_gear(placed)
    problems += unknown
    base = Rom.load(BASE_ROM)
    pct = item_percentage(base, have)
    if pct != len(placed):
        problems.append(f"rodadas: a porcentagem do fim ($8B:E627) com os {len(placed)} itens é {pct}%: um item vale 0 ou mais de 1")
    if not problems:
        worlds = ("tallon", "chozo", "magmoor", "phendrana", "mines")   # specs/19f: the Mines' items too
        per = "; ".join(f"{k}: " + " + ".join(str(sum(item_world(i) == w for i in rd.items)) for w in worlds)
                        for k, rd in enumerate(rounds))
        side = {"tallon": "do Tallon", "chozo": "da Chozo", "magmoor": "da Magmoor"}

        def pair(a: str, b: str) -> str:
            # specs/19m: the Mines' two, named by the room they go down from (tallon_transport_mines_east -> mines_east) and its side
            if b.startswith("mines_"):
                return f"{a.split('_transport_')[1]} {first[a]} ({side[a.split('_')[0]]})"
            # specs/17j: the Magmoor's two with the side they leave from; specs/18n: Phendrana's two, named by the Magmoor
            # room they go up from (magmoor_transport_phendrana_north -> phendrana_north)
            if a.startswith("phendrana_"):
                return f"{b.removeprefix('magmoor_transport_')} {first[a]} ({side['magmoor']})"
            name = a.removeprefix("tallon_transport_").removeprefix("chozo_transport_")
            return f"{name} {first[a]}" + (f" ({side[a.split('_')[0]]})" if b.startswith("magmoor_") else "")
        # specs/19m: the Mines' two too (since 19e in their own line, check_mines_rounds)
        pairs = ", ".join(pair(a, b) for a, b in ELEVATORS if (a, b) != impact_rooms.TELEPORTER)   # 20e: its own line
        print(f"rodadas (specs/12m, 17j, 18n, 19m): Tallon + Chozo + Magmoor + Phendrana + Mines andados juntos, {len(placed)} "
              f"itens em {len(rounds)} rodadas, cada um na rodada declarada (itens por rodada, Tallon + Chozo + Magmoor + "
              f"Phendrana + Mines: "
              f"{per}); elevadores a partir da rodada: {pairs}; porcentagem do fim ($8B:E627) com todos: {pct}% (energia "
              f"{have['energy']}, mísseis {have.get('missiles', 0)}, super mísseis {have.get('supers', 0)}, power bombs "
              f"{have.get('power_bombs', 0)})")
    return problems


# specs/17j, epic 17 closed: what the epic's definition of done and the user's decisions say of the Magmoor, item by item.
# Prime's pickups by room (epic 17, the item table) -> the SM items of the user's decision 2: the 3 Missile Expansions, the 2
# Energy Tanks, the Power Bomb Expansion and a missile where Prime has the Plasma Beam; nothing where Prime has the Ice
# Spreader (Shore Tunnel) or an artifact (Lava Lake, Warrior Shrine)
EPIC_MAGMOOR_ITEMS = {"magmoor_triclops_pit": [tallon_items.MISSILE_TANK], "magmoor_storage_cavern": [tallon_items.MISSILE_TANK],
                      "magmoor_transport_tunnel_a": [tallon_items.ENERGY_TANK],
                      "magmoor_fiery_shores": [tallon_items.MISSILE_TANK, tallon_items.POWER_BOMB_ITEM],
                      "magmoor_plasma_processing": [tallon_items.MISSILE_TANK], "magmoor_workstation": [tallon_items.ENERGY_TANK]}
EPIC_MAGMOOR_NO_ITEM = ("magmoor_shore_tunnel", "magmoor_lava_lake", "magmoor_warrior_shrine")   # Ice Spreader, artifacts
EPIC_MAGMOOR_HOT = 12             # Prime's superheated rooms (Area Damage; user decision 3)
EPIC_MAGMOOR_SAVES = ("magmoor_save_station_a", "magmoor_save_station_b")
EPIC_MAGMOOR_PB_ROUND = 6         # the power bomb pack never before round 6 (epic 17: it turns the power bombs on)


def check_epic_magmoor() -> list[str]:
    """specs/17j, epic 17 closed (its criterion 4 and the user's decisions 1-7): the 29 rooms of the Magmoor table built (the
    three regions) with its 29 links; the 7 items of decision 2 (EPIC_MAGMOOR_ITEMS: kinds by Prime room; none where Prime has
    the Ice Spreader or an artifact; the power bomb pack not before round 6); every Prime door lock (DOCK_LOCKS) on a built
    link (check_magmoor_locks_mapped gives each its mechanism); heat in exactly Prime's 12 superheated rooms (decision 3);
    lava (decision 4) only in the Magmoor's area and only where Prime has it; the working elevators exactly the two to worlds
    that exist (decision 5 / technical decision 6: the Chozo's P24 <-> P0, the Tallon's P23 <-> P16) and the three to
    Phendrana and the Mines built without an elevator; the two save stations (load stations 1 and 2 of area 2); no boss
    (decision 7). The line "magmoor (specs/17)"."""
    problems = []
    built = MAGMOOR.by_key()
    table = {t.key for t in magmoor_rooms.TABLE}
    if set(built) != table or magmoor_rooms.ACTIVE_REGIONS != set(magmoor_rooms.REGIONS):
        problems.append(f"magmoor (épico): salas construídas {len(built)} de {len(table)} (faltam {sorted(table - set(built))}), "
                        f"regiões {sorted(magmoor_rooms.ACTIVE_REGIONS)}")
    links = {frozenset((r.key, d.to_room)) for r in MAGMOOR.rooms for d in r.doors if d.to_room in built}
    if len(links) != len(magmoor_rooms.LINKS):
        problems.append(f"magmoor (épico): {len(links)} ligações construídas, o Prime tem {len(magmoor_rooms.LINKS)}")
    got: dict[str, list[int]] = {}
    for n, it in magmoor_items.placed(set(built)):
        got.setdefault(it.room, []).append(it.kind)
        if it.kind == tallon_items.POWER_BOMB_ITEM and it.round < EPIC_MAGMOOR_PB_ROUND:
            problems.append(f"magmoor (épico): a expansão de PB de {it.room} na rodada {it.round}, antes da {EPIC_MAGMOOR_PB_ROUND}")
    if {k: sorted(v) for k, v in got.items()} != {k: sorted(v) for k, v in EPIC_MAGMOOR_ITEMS.items()}:
        problems.append(f"magmoor (épico): itens por sala {got}, a decisão 2 diz {EPIC_MAGMOOR_ITEMS}")
    stray = [k for k in EPIC_MAGMOOR_NO_ITEM if k in got]
    if stray:
        problems.append(f"magmoor (épico): item onde o Prime tem o Ice Spreader ou um artefato: {stray}")
    off = sorted(f"{a}->{b}" for a, b in magmoor_rooms.DOCK_LOCKS if frozenset((a, b)) not in links)
    if off:
        problems.append(f"magmoor (épico): travas do Prime fora das ligações construídas: {off}")
    hot = {k for k, r in built.items() if r.heat}
    if hot != set(magmoor_rooms.HOT_ROOMS) or len(hot) != EPIC_MAGMOOR_HOT:
        problems.append(f"magmoor (épico): salas quentes {sorted(hot)}, o Prime tem {EPIC_MAGMOOR_HOT}: {sorted(magmoor_rooms.HOT_ROOMS)}")
    lava_rooms = {r.key for r in MAGMOOR.rooms if r.lava is not None}
    lava_out = [r.key for a in AREAS if a is not MAGMOOR for r in a.rooms if r.lava is not None]
    if lava_out or any("lava" not in magmoor_rooms.FEATURES.get(k, ()) for k in lava_rooms):
        problems.append(f"magmoor (épico): lava fora da Magmoor {lava_out} ou onde o Prime não tem "
                        f"{sorted(k for k in lava_rooms if 'lava' not in magmoor_rooms.FEATURES.get(k, ()))}")
    working = {(a, b) for a, b in ELEVATORS if b in built or a in built}
    # specs/19e: as unordered pairs (the Magmoor's P26 is over the Mines' P25: the upper room of its pair)
    if {frozenset(w) for w in working} != {frozenset((magmoor_rooms.TRANSPORT_TO[k], k)) for k in magmoor_rooms.ELEVATOR_ROOMS}:
        problems.append(f"magmoor (épico): elevadores de verdade {sorted(working)}, a tabela diz {magmoor_rooms.TRANSPORT_TO}")
    fake = [k for k in magmoor_rooms.DECORATIVE_ELEVATORS if k not in built or built[k].elevator is not None]
    if fake:
        problems.append(f"magmoor (épico): elevadores de enfeite sem a sala ou com elevador: {fake}")
    saves = tuple(st.room for st in MAGMOOR.load_stations[1:])
    if saves != EPIC_MAGMOOR_SAVES:
        problems.append(f"magmoor (épico): save stations {saves}, o Prime tem {EPIC_MAGMOOR_SAVES}")
    bosses = sorted({a.room for a in chozo_bosses.ARENAS} & set(built))
    if bosses:
        problems.append(f"magmoor (épico): chefe na Magmoor {bosses} (decisão 7: nenhum)")
    if not problems:
        kinds = collections.Counter(tallon_items.KIND_NAME[k] for v in got.values() for k in v)
        rounds = sorted(it.round for _, it in magmoor_items.placed(set(built)))
        print(f"magmoor (specs/17, épico fechado na 17j): as {len(built)} salas construídas (regiões "
              f"{' '.join(sorted(magmoor_rooms.ACTIVE_REGIONS))}), {len(links)} ligações; {sum(kinds.values())} itens ("
              + ", ".join(f"{n} {k}" for k, n in sorted(kinds.items())) + f"; rodadas {', '.join(map(str, rounds))}; um míssil "
              f"no lugar do Plasma, nada no do Ice Spreader, sem artefatos); {len(magmoor_rooms.DOCK_LOCKS)} travas do Prime nas "
              f"ligações construídas; calor nas {len(hot)} salas superaquecidas do Prime; lava em {len(lava_rooms)} salas, todas "
              f"com lava no Prime e nenhuma fora da área {MAGMOOR.number}; elevadores: {len(working)} de verdade ("
              + ", ".join(f"{a} <-> {b}" for a, b in sorted(working)) + f"), {len(magmoor_rooms.DECORATIVE_ELEVATORS)} de enfeite "
              f"sem elevador; {len(saves)} save stations; nenhum chefe")
    return problems


# specs/18n, epic 18 closed: what the epic's definition of done and the user's decisions say of Phendrana, item by item. Prime's
# pickups by room (epic 18, the item table) -> the SM items of the user's decision 3: the 9 Missile Expansions, the 3 Energy
# Tanks, the 2 Power Bomb Expansions, the SM's Super Missile where Prime has its Super Missile (the Observatory), a missile where
# Prime has the Wave Beam (the Chapel, the Sheegoth's prize) and the Gravity Suit (the Gravity Chamber); nothing where Prime has
# the Boost Ball (Phendrana Canyon), the Spider Ball (Quarantine Cave, the Thardus'), the Thermal Visor (Research Core) or an
# artifact (Chozo Ice Temple, Control Tower, Storage Cave)
EPIC_PHENDRANA_ITEMS = {
    "phendrana_shorelines": [tallon_items.MISSILE_TANK] * 2, "phendrana_ice_ruins_east": [tallon_items.MISSILE_TANK] * 2,
    "phendrana_chapel_of_the_elders": [tallon_items.MISSILE_TANK], "phendrana_ice_ruins_west": [tallon_items.POWER_BOMB_ITEM],
    "phendrana_ruined_courtyard": [tallon_items.ENERGY_TANK], "phendrana_research_lab_hydra": [tallon_items.MISSILE_TANK],
    "phendrana_quarantine_monitor": [tallon_items.MISSILE_TANK], "phendrana_transport_access": [tallon_items.ENERGY_TANK],
    "phendrana_observatory": [phendrana_items.SUPER_MISSILE_TANK],
    "phendrana_research_lab_aether": [tallon_items.ENERGY_TANK, tallon_items.MISSILE_TANK],
    "phendrana_frost_cave": [tallon_items.MISSILE_TANK], "phendrana_gravity_chamber": [tallon_items.MISSILE_TANK] * 2,
    "phendrana_security_cave": [tallon_items.POWER_BOMB_ITEM]}
EPIC_PHENDRANA_NO_ITEM = ("phendrana_canyon", "phendrana_quarantine_cave", "phendrana_research_core", "phendrana_chozo_ice_temple",
                          "phendrana_control_tower", "phendrana_storage_cave")   # Boost, Spider, Thermal, the 3 artifacts
EPIC_PHENDRANA_PB_ROUND = 6       # the power bomb packs never before round 6 (epic 18, decision 3)
EPIC_PHENDRANA_SNOW = 23          # Prime's snowing rooms (AreaAttributes fx_type 1; user decision 6)


def check_epic_phendrana() -> list[str]:
    """specs/18n, epic 18 closed (its criterion 4 and the user's decisions 1-7): the 56 rooms of the Phendrana table built (the
    five regions) with its 59 links; the 17 items of decision 3 (EPIC_PHENDRANA_ITEMS: kinds by Prime room; none where Prime has
    the Boost Ball, the Spider Ball, the Thermal Visor or an artifact; the power bomb packs not before round 6); every Prime door
    lock (DOCK_LOCKS) on a built link (check_phendrana_locks_mapped gives each its mechanism); falling snow in exactly Prime's 23
    snowing rooms (decision 6), water only in the Gravity Chamber (decision 5), no heat nor lava; the working elevators exactly
    the two to the Magmoor (technical decision 4: P0 <-> the Magmoor's P13, P29 <-> its P27), none decorative; the four save
    stations (load stations 1-4 of area 4, in Prime's save rooms) and the map station; the two bosses of decision 4 (the
    Sheegoth's arena in the Chapel of the Elders, the Thardus' in the Quarantine Cave) and no other arena in area 4. The line
    "phendrana (specs/18, épico fechado na 18n)"."""
    problems = []
    built = PHENDRANA.by_key()
    table = {t.key for t in phendrana_rooms.TABLE}
    if set(built) != table or phendrana_rooms.ACTIVE_REGIONS != set(phendrana_rooms.REGIONS):
        problems.append(f"phendrana (épico): salas construídas {len(built)} de {len(table)} (faltam {sorted(table - set(built))}), "
                        f"regiões {sorted(phendrana_rooms.ACTIVE_REGIONS)}")
    links = {frozenset((r.key, d.to_room)) for r in PHENDRANA.rooms for d in r.doors if d.to_room in built}
    if len(links) != len(phendrana_rooms.LINKS):
        problems.append(f"phendrana (épico): {len(links)} ligações construídas, o Prime tem {len(phendrana_rooms.LINKS)}")
    got: dict[str, list[int]] = {}
    placed = phendrana_items.placed(set(built))
    for n, it in placed:
        got.setdefault(it.room, []).append(it.kind)
        if it.kind == tallon_items.POWER_BOMB_ITEM and it.round < EPIC_PHENDRANA_PB_ROUND:
            problems.append(f"phendrana (épico): a expansão de PB de {it.room} na rodada {it.round}, antes da "
                            f"{EPIC_PHENDRANA_PB_ROUND}")
    if {k: sorted(v) for k, v in got.items()} != {k: sorted(v) for k, v in EPIC_PHENDRANA_ITEMS.items()}:
        problems.append(f"phendrana (épico): itens por sala {got}, a decisão 3 diz {EPIC_PHENDRANA_ITEMS}")
    stray = [k for k in EPIC_PHENDRANA_NO_ITEM if k in got]
    if stray:
        problems.append(f"phendrana (épico): item onde o Prime tem a Boost, a Spider, o Thermal ou um artefato: {stray}")
    off = sorted(f"{a}->{b}" for a, b in phendrana_rooms.DOCK_LOCKS if frozenset((a, b)) not in links)
    if off:
        problems.append(f"phendrana (épico): travas do Prime fora das ligações construídas: {off}")
    snow = {k for k, r in built.items() if r.snow}
    if snow != set(phendrana_rooms.SNOW_ROOMS) or len(snow) != EPIC_PHENDRANA_SNOW:
        problems.append(f"phendrana (épico): neve em {sorted(snow)}, o Prime neva em {EPIC_PHENDRANA_SNOW}: "
                        f"{sorted(phendrana_rooms.SNOW_ROOMS)}")
    water = {k for k, r in built.items() if r.water}
    hot = sorted(k for k, r in built.items() if r.heat or r.lava is not None)
    if water != EPIC_PHENDRANA_FLOODED or hot:
        problems.append(f"phendrana (épico): água em {sorted(water)} (decisão 5: só {sorted(EPIC_PHENDRANA_FLOODED)}), calor ou "
                        f"lava em {hot}")
    working = {(a, b) for a, b in ELEVATORS if a in built or b in built}
    if working != {(k, phendrana_rooms.TRANSPORT_TO[k]) for k in phendrana_rooms.ELEVATOR_ROOMS} \
            or phendrana_rooms.DECORATIVE_ELEVATORS:
        problems.append(f"phendrana (épico): elevadores de verdade {sorted(working)}, de enfeite "
                        f"{sorted(phendrana_rooms.DECORATIVE_ELEVATORS)}; o épico diz os dois para a Magmoor")
    saves = tuple(st.room for st in PHENDRANA.load_stations[1:])
    maps = sorted(k for k, r in built.items() if r.map_station)
    if saves != EPIC_PHENDRANA_SAVES or maps != [EPIC_PHENDRANA_MAP]:
        problems.append(f"phendrana (épico): save stations {saves} e map station {maps}, o Prime tem {EPIC_PHENDRANA_SAVES} e "
                        f"{EPIC_PHENDRANA_MAP}")
    bosses = sorted(a.room for a in chozo_bosses.ARENAS if a.room in built)
    if bosses != sorted(EPIC_PHENDRANA_BOSS_ROOMS):
        problems.append(f"phendrana (épico): arenas em {bosses}, a decisão 4 diz {sorted(EPIC_PHENDRANA_BOSS_ROOMS)}")
    if not problems:
        kinds = collections.Counter(tallon_items.KIND_NAME[k] for v in got.values() for k in v)
        rounds = sorted(it.round for _, it in placed)
        name = lambda k: k.removeprefix("phendrana_")   # noqa: E731
        print(f"phendrana (specs/18, épico fechado na 18n): as {len(built)} salas construídas (regiões "
              f"{' '.join(sorted(phendrana_rooms.ACTIVE_REGIONS))}), {len(links)} ligações; {sum(kinds.values())} itens ("
              + ", ".join(f"{n} {k}" for k, n in sorted(kinds.items())) + f"; rodadas {', '.join(map(str, rounds))}; o Super "
              f"Missile no Observatory, um míssil no lugar do Wave e da Gravity, nada no da Boost, da Spider, do Thermal e dos "
              f"artefatos); {len(phendrana_rooms.DOCK_LOCKS)} travas do Prime nas ligações construídas; neve nas {len(snow)} "
              f"salas onde neva no Prime; inundada só a {', '.join(name(k) for k in sorted(water))}, sem calor nem lava; "
              f"elevadores: {len(working)} de verdade (" + ", ".join(f"{a} <-> {b}" for a, b in sorted(working)) + f"); "
              f"{len(saves)} save stations e a map station; chefes: "
              + ", ".join(f"{name(k)} ({EPIC_PHENDRANA_BOSS_ROOMS[k]})" for k in bosses))
    return problems


# specs/19m, epic 19 closed: what the epic's definition of done and the user's decisions say of the Mines, item by item. Prime's
# pickups by room (epic 19, the item table) -> the SM items of the user's decision 3 (a): the 9 Missile Expansions, the 2 Energy
# Tanks, a missile where Prime has the Power Bomb (the Central Dynamo: the game's is the Tallon's since specs/09e) and the SM's
# Grapple Beam where Prime has its Grapple Beam (the Storage Depot B); nothing where Prime has the Flamethrower (Storage Depot A),
# the Phazon Suit (Elite Quarters) or an artifact (the Phazon Mining Tunnel's; the Elite Research's is beside its missile)
EPIC_MINES_ITEMS = {k: [tallon_items.MISSILE_TANK] for k in (
    "mines_main_quarry", "mines_security_access_a", "mines_elite_research", "mines_elite_control_access",
    "mines_phazon_processing_center", "mines_metroid_quarantine_b", "mines_metroid_quarantine_a", "mines_fungal_hall_b",
    "mines_fungal_hall_access", "mines_central_dynamo")}
EPIC_MINES_ITEMS.update({"mines_ventilation_shaft": [tallon_items.ENERGY_TANK],
                         "mines_processing_center_access": [tallon_items.ENERGY_TANK],
                         "mines_storage_depot_b": [tallon_items.GRAPPLE_BEAM]})
EPIC_MINES_NO_ITEM = ("mines_storage_depot_a", "mines_elite_quarters", "mines_phazon_mining_tunnel")   # Flamethrower, Suit, artifact
EPIC_MINES_SAVES = ("mines_save_station_a", "mines_save_station_b", "mines_save_station_c")
EPIC_MINES_MAP = "mines_map_station"
EPIC_MINES_BOSS_ROOMS = {"mines_elite_research": "19h", "mines_elite_quarters": "19k"}   # epic 19, decision 4


def check_epic_mines() -> list[str]:
    """specs/19m, epic 19 closed (its criterion 4 and the user's decisions 1-8): the 42 rooms of the Mines table built (the four
    regions) with its 43 links; the 13 items of decision 3 (EPIC_MINES_ITEMS: kinds by Prime room; none where Prime has the
    Flamethrower, the Phazon Suit or an artifact); every Prime door lock (DOCK_LOCKS) on a built link (check_mines_locks_mapped gives
    each its mechanism); no heat, water, snow nor lava (decision 6: the phazon is only colour); the working elevators exactly the
    two (technical decision 4: P0 <-> the Tallon's P43, P25 <-> the Magmoor's P26), none decorative; the three save stations (load
    stations 1-3 of area 5) and the map station; the two bosses of decision 4 (the Phazon Elite's arena in the Elite Research, the
    Omega Pirate's in the Elite Quarters) and no other arena in area 5. The line "mines (specs/19, épico fechado na 19m)"."""
    problems = []
    built = MINES.by_key()
    table = {t.key for t in mines_rooms.TABLE}
    if set(built) != table or mines_rooms.ACTIVE_REGIONS != set(mines_rooms.REGIONS):
        problems.append(f"mines (épico): salas construídas {len(built)} de {len(table)} (faltam {sorted(table - set(built))}), "
                        f"regiões {sorted(mines_rooms.ACTIVE_REGIONS)}")
    links = {frozenset((r.key, d.to_room)) for r in MINES.rooms for d in r.doors if d.to_room in built}
    if len(links) != len(mines_rooms.LINKS):
        problems.append(f"mines (épico): {len(links)} ligações construídas, o Prime tem {len(mines_rooms.LINKS)}")
    got: dict[str, list[int]] = {}
    placed = mines_items.placed(set(built))
    for _, it in placed:
        got.setdefault(it.room, []).append(it.kind)
    if {k: sorted(v) for k, v in got.items()} != {k: sorted(v) for k, v in EPIC_MINES_ITEMS.items()}:
        problems.append(f"mines (épico): itens por sala {got}, a decisão 3 diz {EPIC_MINES_ITEMS}")
    stray = [k for k in EPIC_MINES_NO_ITEM if k in got]
    if stray:
        problems.append(f"mines (épico): item onde o Prime tem o Flamethrower, o Phazon Suit ou um artefato: {stray}")
    off = sorted(f"{a}->{b}" for a, b in mines_rooms.DOCK_LOCKS if frozenset((a, b)) not in links)
    if off:
        problems.append(f"mines (épico): travas do Prime fora das ligações construídas: {off}")
    wet = sorted(k for k, r in built.items() if r.heat or r.water or r.snow or r.lava is not None)
    if wet:
        problems.append(f"mines (épico): calor, água, neve ou lava em {wet} (decisão 6: o phazon é só cor)")
    working = {(a, b) for a, b in ELEVATORS if a in built or b in built}
    if {frozenset(w) for w in working} != {frozenset((k, mines_rooms.TRANSPORT_TO[k])) for k in mines_rooms.ELEVATOR_ROOMS} \
            or mines_rooms.DECORATIVE_ELEVATORS:
        problems.append(f"mines (épico): elevadores de verdade {sorted(working)}, de enfeite "
                        f"{sorted(mines_rooms.DECORATIVE_ELEVATORS)}; o épico diz os dois, para o Tallon e a Magmoor")
    saves = tuple(st.room for st in MINES.load_stations[1:])
    maps = sorted(k for k, r in built.items() if r.map_station)
    if saves != EPIC_MINES_SAVES or maps != [EPIC_MINES_MAP]:
        problems.append(f"mines (épico): save stations {saves} e map station {maps}, o Prime tem {EPIC_MINES_SAVES} e "
                        f"{EPIC_MINES_MAP}")
    bosses = sorted(a.room for a in chozo_bosses.ARENAS if a.room in built)
    if bosses != sorted(EPIC_MINES_BOSS_ROOMS):
        problems.append(f"mines (épico): arenas em {bosses}, a decisão 4 diz {sorted(EPIC_MINES_BOSS_ROOMS)}")
    if not problems:
        kinds = collections.Counter(tallon_items.KIND_NAME[k] for v in got.values() for k in v)
        rounds = sorted(it.round for _, it in placed)
        name = lambda k: k.removeprefix("mines_")   # noqa: E731
        print(f"mines (specs/19, épico fechado na 19m): as {len(built)} salas construídas (regiões "
              f"{' '.join(sorted(mines_rooms.ACTIVE_REGIONS))}), {len(links)} ligações; {sum(kinds.values())} itens ("
              + ", ".join(f"{n} {k}" for k, n in sorted(kinds.items())) + f"; rodadas {', '.join(map(str, rounds))}; um míssil "
              f"no lugar da Power Bomb, o Grapple Beam do SM na Storage Depot B, nada no do Flamethrower, do Phazon Suit e dos "
              f"artefatos); {len(mines_rooms.DOCK_LOCKS)} travas do Prime nas ligações construídas; sem calor, água, neve nem lava; "
              f"elevadores: {len(working)} de verdade (" + ", ".join(f"{a} <-> {b}" for a, b in sorted(working)) + f"); "
              f"{len(saves)} save stations e a map station; chefes: "
              + ", ".join(f"{name(k)} ({EPIC_MINES_BOSS_ROOMS[k]})" for k in bosses))
    return problems


# specs/20j, epic 20 closed: what the epic's definition of done and the user's decisions say of the Impact Crater
EPIC_IMPACT_BOSS_ROOMS = {"impact_lair": "20h"}   # decision 3: one arena, in the Lair


def check_epic_impact() -> list[str]:
    """specs/20j, epic 20 closed (its criteria and the user's decisions 1-7): the 12 rooms of the crater table built (the four
    regions, decision 1) in area 0 (decision 2); the links between them exactly Prime's 11 (impact_rooms.LINKS: each pair of docks
    a built door pair, same rooms, sides and screens, both ways) and no door out of the crater (the way in and out is the
    teleporter); no item in a crater room (decision 6, specs/20a: Prime has none there), so the game's items and the ending's
    percentage are the same with the crater's rooms as without them (world_items over every room = over the rounds' walk; the
    percentage of $8B:E627 one per item); every Prime door lock (DOCK_LOCKS) on a built link; the only working elevator into it the
    Artifact Temple's teleporter (decision 7), opened in the last round of the walk; the save station and the missile station; one
    arena (decision 3), Metroid Prime's in the Lair, whose bit (IMPACT_FINAL_BIT) is the one the ending reads (check_impact_ending).
    The line "impact (specs/20, épico fechado na 20j)"."""
    problems = []
    built = {r.key: r for r in TALLON.rooms if r.key.startswith(impact_rooms.PREFIX)}
    table = [t.key for t in impact_rooms.TABLE]
    if list(built) != table or impact_rooms.ACTIVE_REGIONS != set(impact_rooms.REGIONS):
        problems.append(f"impact (épico): salas construídas {len(built)} de {len(table)} (faltam {sorted(set(table) - set(built))}), "
                        f"regiões {sorted(impact_rooms.ACTIVE_REGIONS)}")
    links, out = set(), []
    for r in built.values():
        for d in r.doors:
            if d.to_room not in built:
                out.append(f"{r.key} -> {d.to_room}")
                continue
            back = built[d.to_room].doors[d.to_door]
            if back.to_room != r.key:
                problems.append(f"impact (épico): a porta {r.key} -> {d.to_room} não volta ({back.to_room})")
            links.add(frozenset({(r.key, d.side, d.screen), (d.to_room, back.side, back.screen)}))
    want = {frozenset(link) for link in impact_rooms.LINKS}
    if links != want:
        problems.append(f"impact (épico): ligações construídas {len(links)}, o Prime tem {len(want)}; a mais "
                        f"{sorted(map(sorted, links - want))}, faltam {sorted(map(sorted, want - links))}")
    if out:
        problems.append(f"impact (épico): portas para fora da cratera {sorted(out)} (a entrada é só o teleporte)")
    every = {r.key for _, r in all_rooms()}
    placed_all = world_items(every)
    in_crater = sorted(f"{item_world(n)} {it.room}" for n, it in placed_all if it.room.startswith(impact_rooms.PREFIX))
    if in_crater:
        return problems + [f"impact (épico): itens na cratera {in_crater} (a decisão 6 e a 20a: nenhum)"]
    placed_walk = world_items({r.key for r in world_rooms()})
    have, unknown = items_gear(placed_all)
    pct = item_percentage(Rom.load(BASE_ROM), have) if not unknown else None
    if len(placed_all) != len(placed_walk) or pct != len(placed_all):
        problems.append(f"impact (épico): {len(placed_all)} itens com a cratera, {len(placed_walk)} no passeio das rodadas, "
                        f"porcentagem do fim {pct}%")
    off = sorted(f"{a}->{b}" for a, b in impact_rooms.DOCK_LOCKS
                 if not any({a, b} == {x for x, _, _ in link} for link in links))
    if off:
        problems.append(f"impact (épico): travas do Prime fora das ligações construídas: {off}")
    working = sorted((a, b) for a, b in ELEVATORS if a in built or b in built)
    opens = impact_opens()
    last = len(tallon_progress_built()[0]) - 1
    if working != [impact_rooms.TELEPORTER] or opens is None or opens[0] != last:
        problems.append(f"impact (épico): elevadores {working}, aberto na rodada {opens and opens[0]}; a decisão 7 diz o "
                        f"teleporte {impact_rooms.TELEPORTER} depois do Omega Pirate (a última rodada, {last})")
    saves = [k for k, r in built.items() if r.save_station]
    refills = [k for k, r in built.items() if r.missile_station]
    if saves != [impact_rooms.ENTRY] or refills != [impact_rooms.MISSILE_STATION]:
        problems.append(f"impact (épico): save stations {saves}, recargas {refills}; o Prime tem a da {impact_rooms.ENTRY} e a da "
                        f"{impact_rooms.MISSILE_STATION}")
    arenas = [a for a in chozo_bosses.ARENAS if a.room in built]
    if sorted(a.room for a in arenas) != sorted(EPIC_IMPACT_BOSS_ROOMS) or any(a.bit != IMPACT_FINAL_BIT for a in arenas):
        problems.append(f"impact (épico): arenas {[(a.room, a.bit) for a in arenas]}, a decisão 3 diz a da Lair com o bit "
                        f"${IMPACT_FINAL_BIT:02X} (o que o fim lê)")
    if not problems:
        name = lambda k: k.removeprefix(impact_rooms.PREFIX)   # noqa: E731
        print(f"impact (specs/20, épico fechado na 20j): as {len(built)} salas construídas (regiões "
              f"{' '.join(sorted(impact_rooms.ACTIVE_REGIONS))}) na área {TALLON.number}, {len(links)} ligações = as do Prime "
              f"(lados e telas), nenhuma porta para fora; nenhum item na cratera: {len(placed_all)} itens no jogo, porcentagem do "
              f"fim {pct}% (igual sem a cratera); {len(impact_rooms.DOCK_LOCKS)} travas do Prime nas ligações construídas; elevador: "
              f"o teleporte {' <-> '.join(impact_rooms.TELEPORTER)}, a partir da rodada {opens[0]} (a última); save station "
              f"{name(saves[0])}, recarga de mísseis {name(refills[0])}; chefe: "
              + ", ".join(f"{name(a.room)} ({EPIC_IMPACT_BOSS_ROOMS[a.room]}, bit ${a.bit:02X} da área {TALLON.number}, o que o "
                          f"fim lê)" for a in arenas))
    return problems


def check_phendrana_rounds() -> list[str]:
    """specs/18e: Phendrana's built rooms in the walk of the four areas together (tallon_rounds over world_rooms: the Magmoor's
    lifts link them): each first reached in its phendrana_rooms.FIRST_ROUND, in the same round as the Magmoor room under it
    (only the elevators lead in: no shortcut into an earlier round of another area); the other areas' lines stay theirs.
    specs/18f: and Phendrana's placed items (phendrana/items.py), each picked up in its declared Item.round, in an air block away
    from the doors (check_magmoor_rounds' rule). Prints the line "phendrana (specs/18e, 18f)": the rooms and items per round."""
    problems = []
    try:
        rounds, got, got_items, _ = tallon_progress_built()
    except ValueError as e:
        return [f"phendrana: {e}"]
    for r in PHENDRANA.rooms:
        g, w = got.get(r.key), phendrana_rooms.FIRST_ROUND.get(r.key)
        if g != w:
            problems.append(f"phendrana: {r.key} fica alcançável na rodada {g}"
                            + (f" (com {have_names(rounds[g].have)})" if g is not None else "") + f", FIRST_ROUND diz {w}")
    extra = set(phendrana_rooms.FIRST_ROUND) - set(PHENDRANA.by_key())
    if extra:
        problems.append(f"phendrana: FIRST_ROUND com salas fora do build: {sorted(extra)}")
    pairs = [(a, b) for a, b in ELEVATORS if a.startswith("phendrana_")]
    if {a for a, _ in pairs} != set(phendrana_rooms.ELEVATOR_ROOMS) or any(
            phendrana_rooms.TRANSPORT_TO[a] != b for a, b in pairs):
        problems.append(f"phendrana: elevadores {pairs}, a tabela diz {phendrana_rooms.TRANSPORT_TO}")
    for a, b in pairs:
        if got.get(a) is None or got.get(a) != got.get(b):
            problems.append(f"phendrana: elevador {a} (rodada {got.get(a)}) <-> {b} (rodada {got.get(b)}): os dois lados "
                            f"deviam ficar alcançáveis na mesma rodada")
    by_key = PHENDRANA.by_key()
    try:
        placed = phendrana_items.placed(set(by_key))
    except ValueError as e:
        return problems + [f"phendrana: {e}"]
    for n, it in placed:
        tag = f"phendrana: item {n} ({phendrana_items.KIND_NAME[it.kind]}) em {it.room} {it.spot}"
        problems += item_spot_problems(tag, by_key[it.room], it.spot)
        g = got_items.get(("phendrana", n))
        if g is None:
            problems.append(f"{tag} nunca é pego (inalcançável da nave do Tallon em todas as {len(rounds)} rodadas)")
        elif g != it.round:
            problems.append(f"{tag} é pego na rodada {g} (com {have_names(rounds[g].have)}), declarado na rodada {it.round}")
    for n, it in enumerate(phendrana_items.ITEMS):
        if (it.spot is None) != (it.round is None):
            problems.append(f"phendrana: item {n} em {it.room}: lugar e rodada vêm juntos")
    # specs/18l (epic 18, user decision 3): the SM's Super Missile is the game's only one, where Prime has its Super Missile (the
    # Observatory), once that room is built
    supers = sorted(f"{item_world(n)} {it.room}" for n, it in world_items({r.key for r in world_rooms()})
                    if it.kind == phendrana_items.SUPER_MISSILE_TANK)
    want = [f"phendrana {EPIC_PHENDRANA_SUPER}"] if EPIC_PHENDRANA_SUPER in by_key else []
    if supers != want:
        problems.append(f"phendrana: Super Missiles em {supers}; a decisão 3 do épico põe um, no Observatory ({want})")
    if not problems:
        per = "; ".join(f"rodada {k}: {sum(key in by_key for key in rd.rooms)} salas, "
                        f"{sum(item_world(i) == 'phendrana' for i in rd.items)} itens" for k, rd in enumerate(rounds)
                        if any(key in by_key for key in rd.rooms) or any(item_world(i) == "phendrana" for i in rd.items))
        print(f"phendrana (specs/18e, 18f; regiões ativas: {''.join(sorted(phendrana_rooms.ACTIVE_REGIONS)) or 'nenhuma'}): "
              f"{len(PHENDRANA.rooms)} salas construídas, {len(placed)} itens, andadas com o Tallon, a Chozo e a Magmoor pelos "
              f"elevadores: {per}; elevadores: "
              + ", ".join(f"{b} (rodada {got[b]}) <-> {a} (rodada {got[a]})" for a, b in pairs)
              + f"; área {PHENDRANA.number}, mapa \"{PHENDRANA.name}\", estações: "
              + ", ".join(f"{st.index} {st.room.removeprefix('phendrana_')}" for st in PHENDRANA.load_stations)
              + "; nenhuma rodada, sala ou item das outras áreas muda (linhas acima)"
              + (f"; specs/18l: o Super Missile do SM só em {EPIC_PHENDRANA_SUPER.removeprefix('phendrana_')}" if supers else ""))
    return problems


# specs/19e (epic 19, "Como a Mines encaixa"): the round each Mines lift is first reached in, by its other side: the Tallon's P43 (round
# 5, behind the Tunnel E's ice doors) and the Magmoor's P26 (round 4, behind the Workstation Tunnel's)
EPIC_MINES_LIFT_ROUNDS = {"tallon_transport_mines_east": 5, "magmoor_transport_mines_west": 4}
# specs/19f (epic 19, user decision 3a): the SM's Grapple Beam is the game's only one, where Prime has its Grapple Beam
EPIC_MINES_GRAPPLE = "mines_storage_depot_b"


def check_mines_rounds() -> list[str]:
    """specs/19e: the Mines' built rooms in the walk of the five areas together (tallon_rounds over world_rooms: the Tallon's and the
    Magmoor's lifts link them): each first reached in its mines_rooms.FIRST_ROUND, in the same round as the room over it (only the
    elevators lead in: no shortcut into an earlier round of another area), and the other side of each lift in the epic's round
    (EPIC_MINES_LIFT_ROUNDS); the lifts are the table's (TRANSPORT_TO). specs/19f: and the Mines' placed items (mines/items.py),
    each picked up in its declared Item.round, in an air block away from the doors (check_phendrana_rounds' rule); the SM's Grapple
    Beam only in the Storage Depot B (EPIC_MINES_GRAPPLE, once built), nowhere else in the game. Prints the line "mines (specs/19e,
    19f)": the rooms and items per round, the lifts, the area, its map name and stations. (The other areas' lines stay theirs:
    check_world_rounds leaves the Mines' lifts out of its line.)"""
    problems = []
    try:
        rounds, got, got_items, _ = tallon_progress_built()
    except ValueError as e:
        return [f"mines: {e}"]
    for r in MINES.rooms:
        g, w = got.get(r.key), mines_rooms.FIRST_ROUND.get(r.key)
        if g != w:
            problems.append(f"mines: {r.key} fica alcançável na rodada {g}"
                            + (f" (com {have_names(rounds[g].have)})" if g is not None else "") + f", FIRST_ROUND diz {w}")
    extra = set(mines_rooms.FIRST_ROUND) - set(MINES.by_key())
    if extra:
        problems.append(f"mines: FIRST_ROUND com salas fora do build: {sorted(extra)}")
    pairs = [(a, b) for a, b in ELEVATORS if b.startswith("mines_")]
    if {b for _, b in pairs} != set(mines_rooms.ELEVATOR_ROOMS) or any(mines_rooms.TRANSPORT_TO[b] != a for a, b in pairs) \
            or any(a.startswith("mines_") for a, _ in ELEVATORS):
        problems.append(f"mines: elevadores {pairs}, a tabela diz {mines_rooms.TRANSPORT_TO} (a Mines embaixo dos dois)")
    for a, b in pairs:
        if got.get(b) is None or got.get(a) != got.get(b):
            problems.append(f"mines: elevador {a} (rodada {got.get(a)}) <-> {b} (rodada {got.get(b)}): os dois lados "
                            f"deviam ficar alcançáveis na mesma rodada")
        if a in EPIC_MINES_LIFT_ROUNDS and got.get(a) != EPIC_MINES_LIFT_ROUNDS[a]:
            problems.append(f"mines: {a} na rodada {got.get(a)}, o épico diz {EPIC_MINES_LIFT_ROUNDS[a]}")
    if set(EPIC_MINES_LIFT_ROUNDS) != {a for a, _ in pairs}:
        problems.append(f"mines: elevadores do épico {sorted(EPIC_MINES_LIFT_ROUNDS)}, construídos {sorted(a for a, _ in pairs)}")
    by_key = MINES.by_key()
    try:
        placed = mines_items.placed(set(by_key))
    except ValueError as e:
        return problems + [f"mines: {e}"]
    for n, it in placed:   # specs/19f
        tag = f"mines: item {n} ({mines_items.KIND_NAME[it.kind]}) em {it.room} {it.spot}"
        problems += item_spot_problems(tag, by_key[it.room], it.spot)
        g = got_items.get(("mines", n))
        if g is None:
            problems.append(f"{tag} nunca é pego (inalcançável da nave do Tallon em todas as {len(rounds)} rodadas)")
        elif g != it.round:
            problems.append(f"{tag} é pego na rodada {g} (com {have_names(rounds[g].have)}), declarado na rodada {it.round}")
    for n, it in enumerate(mines_items.ITEMS):
        if (it.spot is None) != (it.round is None):
            problems.append(f"mines: item {n} em {it.room}: lugar e rodada vêm juntos")
    grapples = sorted(f"{item_world(n)} {it.room}" for n, it in world_items({r.key for r in world_rooms()})
                      if it.kind == tallon_items.GRAPPLE_BEAM)
    want = [f"mines {EPIC_MINES_GRAPPLE}"] if EPIC_MINES_GRAPPLE in by_key else []
    if grapples != want:
        problems.append(f"mines: Grapple Beams em {grapples}; a decisão 3a do épico põe um, na Storage Depot B ({want})")
    if not problems:
        per = "; ".join(f"rodada {k}: {sum(key in by_key for key in rd.rooms)} salas, "
                        f"{sum(item_world(i) == 'mines' for i in rd.items)} itens" for k, rd in enumerate(rounds)
                        if any(key in by_key for key in rd.rooms) or any(item_world(i) == "mines" for i in rd.items))
        print(f"mines (specs/19e, 19f; regiões ativas: {''.join(sorted(mines_rooms.ACTIVE_REGIONS)) or 'nenhuma'}): "
              f"{len(MINES.rooms)} salas construídas, {len(placed)} itens, andadas com o Tallon, a Chozo, a Magmoor e Phendrana "
              f"pelos elevadores: {per}; elevadores: "
              + ", ".join(f"{a} (rodada {got[a]}) <-> {b} (rodada {got[b]})" for a, b in pairs)
              + f"; área {MINES.number}, mapa \"{MINES.name}\", estações: "
              + ", ".join(f"{st.index} {st.room.removeprefix('mines_')}" for st in MINES.load_stations)
              + "; nenhuma rodada, sala ou item das outras áreas muda (linhas acima)"
              + (f"; specs/19f: o Grapple Beam do SM só em {EPIC_MINES_GRAPPLE.removeprefix('mines_')}" if grapples else ""))
    return problems


def check_magmoor_rounds() -> list[str]:
    """specs/17e: the Magmoor's built rooms in the walk of the three areas together (tallon_rounds over world_rooms: the
    elevators link them): each first reached in its magmoor_rooms.FIRST_ROUND, in the same round as the other side of its
    elevator; the Tallon's and the Chozo's rounds stay theirs (check_tallon_rounds, check_chozo_rounds, check_world_rounds:
    their lines are unchanged). specs/17f: and the Magmoor's placed items (magmoor/items.py), each picked up in its declared
    Item.round, in an air block away from the doors. Prints the line "magmoor (specs/17e, 17f)": the Magmoor's rooms and
    items per round."""
    problems = []
    try:
        rounds, got, got_items, _ = tallon_progress_built()
    except ValueError as e:
        return [f"magmoor: {e}"]
    for r in MAGMOOR.rooms:
        g, w = got.get(r.key), magmoor_rooms.FIRST_ROUND.get(r.key)
        if g != w:
            problems.append(f"magmoor: {r.key} fica alcançável na rodada {g}"
                            + (f" (com {have_names(rounds[g].have)})" if g is not None else "") + f", FIRST_ROUND diz {w}")
    extra = set(magmoor_rooms.FIRST_ROUND) - set(MAGMOOR.by_key())
    if extra:
        problems.append(f"magmoor: FIRST_ROUND com salas fora do build: {sorted(extra)}")
    pairs = [(a, b) for a, b in ELEVATORS if b.startswith("magmoor_")]
    for a, b in pairs:
        if got.get(a) != got.get(b):
            problems.append(f"magmoor: elevador {a} (rodada {got.get(a)}) <-> {b} (rodada {got.get(b)}): os dois lados "
                            f"deviam ficar alcançáveis na mesma rodada")
    by_key = MAGMOOR.by_key()
    try:
        placed = magmoor_items.placed(set(by_key))
    except ValueError as e:
        return problems + [f"magmoor: {e}"]
    for n, it in placed:
        tag = f"magmoor: item {n} ({magmoor_items.KIND_NAME[it.kind]}) em {it.room} {it.spot}"
        problems += item_spot_problems(tag, by_key[it.room], it.spot)
        g = got_items.get(("magmoor", n))
        if g is None:
            problems.append(f"{tag} nunca é pego (inalcançável da nave do Tallon em todas as {len(rounds)} rodadas)")
        elif g != it.round:
            problems.append(f"{tag} é pego na rodada {g} (com {have_names(rounds[g].have)}), declarado na rodada {it.round}")
    for n, it in enumerate(magmoor_items.ITEMS):
        if (it.spot is None) != (it.round is None):
            problems.append(f"magmoor: item {n} em {it.room}: lugar e rodada vêm juntos")
    if not problems:
        per = "; ".join(f"rodada {k}: {sum(key in by_key for key in rd.rooms)} salas, "
                        f"{sum(item_world(i) == 'magmoor' for i in rd.items)} itens" for k, rd in enumerate(rounds)
                        if any(key in by_key for key in rd.rooms) or any(item_world(i) == "magmoor" for i in rd.items))
        print(f"magmoor (specs/17e, 17f; regiões ativas: {''.join(sorted(magmoor_rooms.ACTIVE_REGIONS)) or 'nenhuma'}): "
              f"{len(MAGMOOR.rooms)} salas construídas, {len(placed)} itens, andadas com o Tallon e a Chozo pelos elevadores: "
              f"{per}; elevadores: " + ", ".join(f"{a} (rodada {got[a]}) <-> {b} (rodada {got[b]})" for a, b in pairs)
              + "; nenhuma rodada, sala ou item do Tallon e da Chozo muda (linhas acima)")
    return problems


def check_tallon_water() -> list[str]:
    """specs/07l (specs/12l: and the Chozo's, chozo/rooms.py FLOODED): the flooded rooms (tallon/rooms.py FLOODED) that Samus can get into before she has
    the Gravity Suit (specs/09b: what she has when she first gets into the room, the rounds' walk, lacks it:
    Section C, after the ice door) are walked with the
    underwater jump without the suit (no Space Jump there): from every door that is not on a Gravity
    Suit ledge, the doors behind the suit's gate stay out of reach (the bulkhead holds), the other
    doors are reached, and no place leaves her with no way back to them."""
    problems = []
    try:
        arrival = tallon_progress_built()[3]
    except ValueError as e:   # an item in a room that is not built (check_tallon_rounds says it too)
        return [f"tallon: {e}"]
    # specs/12l: the Chozo's Reflecting Pool too; specs/18m: Phendrana's Gravity Chamber
    flooded = tallon_rooms.FLOODED | chozo_rooms.FLOODED | phendrana_rooms.FLOODED
    walked = []
    for r in world_rooms():
        if r.key in flooded and not r.water:
            problems.append(f"tallon: {r.key} está em FLOODED mas a sala não é inundada")
        if r.water and r.key not in flooded:
            problems.append(f"{r.key}: sala inundada fora de FLOODED")
        have = arrival.get(r.key)
        if not r.water or have is None or tallon_rooms.GRAVITY in have:
            continue
        # specs/09d: with what else she has then (the Morph Ball and the Bombs)
        no_suit = dataclasses.replace(items_loadout(have & FOOT_GEOMETRY), water=True)
        l1, bts = r.level().build_blocks()
        grid = foot_grid(r, l1, bts, r.width * 16, r.height * 16, no_suit)
        gated = {i for i, d in enumerate(r.doors) if tallon_rooms.GRAVITY in d.gate}
        free = [(d.side, d.screen) for i, d in enumerate(r.doors) if i not in gated]
        for i, d in enumerate(r.doors):
            if i in gated:
                continue
            tag = f"{r.key} sem a Gravity Suit, entrando pela porta {i} ({d.side}{d.screen})"
            walked.append(f"{r.key} porta {i}")
            start = reach.door_entry(grid, d.side, d.screen)
            if start is None:
                problems.append(f"{tag}: sem lugar de pé")
                continue
            seen = reach.reach(grid, [start], no_suit)
            for j, e in enumerate(r.doors):
                got = reach.door_reached(grid, e.side, e.screen, seen, no_suit)
                if j in gated and got:
                    problems.append(f"{tag}: alcança a porta {j} ({e.side}{e.screen} -> {e.to_room}), "
                                    f"atrás da trava da Gravity Suit")
                elif j not in gated and not got:
                    problems.append(f"{tag}: não alcança a porta {j} ({e.side}{e.screen} -> {e.to_room})")
            stuck = reach.stuck(grid, seen, free, no_suit)
            if stuck:
                x, y = min(stuck)
                problems.append(f"{tag}: {len(stuck)} lugares sem volta (ex.: coluna {x}, pé na linha {y})")
    if not problems:
        print(f"água (specs/07l, 12l, 18m): salas inundadas andadas sem a Gravity Suit a partir de {len(walked)} entradas "
              f"({', '.join(walked)}); as portas atrás da suit fora de alcance, nenhum lugar sem volta")
    return problems


def check_ball_ledges() -> list[str]:
    """specs/12l: a Morph Ball tunnel on a Space Jump ledge (a door whose ledge gate has both: the Furnace's R0) is out of
    reach of the walk on foot whatever the tunnel is, and the Space Jump's flood fill assumes the ball: neither proves the
    tunnel. Here the standing body (3 free rows) flies anywhere open (the flood fill without the ball) from every other
    door's inner cells: the door must stay out of its reach (it would not, with the tunnel's roof gone)."""
    problems, n = [], 0
    for area, r in all_rooms():
        if area not in (TALLON, CHOZO):
            continue
        gated = [i for i, d in enumerate(r.doors)
                 if d.ledge and {tallon_rooms.MORPH, tallon_rooms.SPACE_JUMP} <= d.gate]
        if not gated:
            continue
        l1, bts = r.level().build_blocks()
        wb, hb = r.width * 16, r.height * 16
        types = elevator_solid(r, reach.with_breakables([w >> 12 for w in l1], bts, reach.SPACE_JUMP_MORPH))

        def body(x: int, y: int) -> bool:
            return all(0 <= x < wb and 0 <= yy < hb and types[yy * wb + x] not in SOLID_TYPES for yy in (y - 2, y - 1, y))
        starts = {c for j, d in enumerate(r.doors) if j not in gated
                  for c in door_inner_cells(d.side, d.screen, wb, hb) if body(*c)}
        seen, stack = set(starts), list(starts)
        while stack:
            x, y = stack.pop()
            for c in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if c not in seen and body(*c):
                    seen.add(c)
                    stack.append(c)
        for i in gated:
            n += 1
            d = r.doors[i]
            if seen & set(door_inner_cells(d.side, d.screen, wb, hb)):
                problems.append(f"{r.key}: porta {i} ({d.side}{d.screen} -> {d.to_room}) tem trava de Morph Ball numa borda "
                                f"de Space Jump, mas a Samus de pé, voando, chega nela sem a bola")
    if not problems:
        print(f"bola na borda (specs/12l): {n} porta(s) com túnel de Morph numa borda de Space Jump; de pé, voando, fora de "
              f"alcance")
    return problems


def check_breakables() -> list[str]:
    """specs/09d: every bomb block (block type F) of the built Tallon rooms is the project's (type F,
    metatile and BTS of tallon/layouts.py: drawn as vanilla's visible bomb block, does not come back), sits
    in a room with a door behind a Bombs gate, and can really be bombed: with the Morph Ball and the Bombs
    (and the room's water), from some door, the ball gets to a block next to it (4 sides) while it still
    stands (the room's other bomb blocks already broken).
    specs/09e: the same for every power bomb block (shot type C with BTS $08/$09): the project's (metatile $057,
    BTS $09: does not come back), in a room with an item that needs the Power Bomb (items.Item.needs), and in
    reach of a power bomb: with the Morph Ball and the Bombs, every power bomb block still standing, from some
    door, the ball gets within 2 blocks of it (either way; the explosion reaches ~8 x 6, sm_94.c:1567)."""
    problems = []
    built = {r.key for r in world_rooms()}
    pb_rooms = {it.room for _, it in world_items(built) if tallon_rooms.POWER_BOMB in it.needs}
    bomb_rooms = {it.room for _, it in world_items(built) if tallon_rooms.BOMBS in it.needs}   # specs/12f
    for area in AREAS:
        for r in area.rooms:
            lv = r.level()
            l1, bts = lv.build_blocks()
            wb, hb = lv.wb, lv.hb
            blocks = [(i % wb, i // wb) for i, w in enumerate(l1) if w >> 12 == reach.BOMB_BLOCK]
            pbs = [(i % wb, i // wb) for i, w in enumerate(l1) if reach.is_power_bomb_block(w >> 12, bts[i])]
            if pbs:   # specs/17h: or a door behind a Power Bomb gate (the Warrior Shrine's)
                # specs/19i: or the Mines' power bomb ledge of a link whose other room comes in a later child (the Maintenance
                # Tunnel's wall before its L0, a wall until region C: mines_rooms.GATES)
                waiting = area is MINES and any(r.key in g.ledge and tallon_rooms.POWER_BOMB in g.items
                                                for g in mines_rooms.GATES.values())
                problems += check_power_bomb_blocks(area, r, l1, bts, pbs, r.key in pb_rooms or waiting or any(
                    d.ledge and tallon_rooms.POWER_BOMB in d.gate for d in r.doors))
            if not blocks:
                continue
            if area not in (TALLON, CHOZO, MAGMOOR, PHENDRANA, MINES) or not (   # specs/17h: the Magmoor's; 18f: Phendrana's; 19f
                    any(d.ledge and tallon_rooms.BOMBS in d.gate for d in r.doors) or r.key in bomb_rooms):
                problems.append(f"{r.key}: blocos de bomba {blocks} numa sala sem trava de Bombas")
                continue
            loadout = dataclasses.replace(room_loadout(area, r), morph=True, bombs=True)
            open_types = foot_grid(r, l1, bts, wb, hb, loadout).types
            for x, y in blocks:
                tag = f"{r.key}: bloco de bomba em ({x},{y})"
                if l1[y * wb + x] & 0x3FF != tallon_layouts.BOMB_BLOCK_METATILE or bts[y * wb + x] != tallon_layouts.BOMB_BLOCK_BTS:
                    problems.append(f"{tag} com metatile ${l1[y * wb + x] & 0x3FF:03X} e BTS ${bts[y * wb + x]:02X}, "
                                    f"esperado ${tallon_layouts.BOMB_BLOCK_METATILE:03X}/${tallon_layouts.BOMB_BLOCK_BTS:02X}")
                types = list(open_types)
                types[y * wb + x] = reach.BOMB_BLOCK          # this one still stands
                grid = reach.Grid(types, wb, hb)
                starts = [st for d in r.doors if (st := reach.door_entry(grid, d.side, d.screen))]
                seen = reach.reach(grid, starts, loadout)
                if not any(len(s) == 3 and abs(s[0] - x) + abs(s[1] - y) == 1 for s in seen):
                    problems.append(f"{tag}: a bola não chega a nenhum bloco vizinho (não dá para bombá-lo)")
    return problems


POWER_BOMB_REACH = 2   # blocks (Chebyshev) from the ball to a power bomb block (specs/09e, epic decision 4)


def check_power_bomb_blocks(area, r, l1, bts, pbs, needed: bool) -> list[str]:
    """check_breakables for the power bomb blocks `pbs` of room r (specs/09e)."""
    wb, hb = r.width * 16, r.height * 16
    # specs/12f: the Chozo's too; specs/17h: the Magmoor's; specs/18m: Phendrana's (the Security Cave's door); specs/19f: the Mines'
    if area not in (TALLON, CHOZO, MAGMOOR, PHENDRANA, MINES) or not needed:
        return [f"{r.key}: blocos de Power Bomb {pbs} numa sala sem item que peça a Power Bomb"]
    problems = []
    for x, y in pbs:
        if l1[y * wb + x] & 0x3FF != tallon_layouts.POWER_BOMB_BLOCK_METATILE or bts[y * wb + x] != tallon_layouts.POWER_BOMB_BLOCK_BTS:
            problems.append(f"{r.key}: bloco de Power Bomb em ({x},{y}) com metatile ${l1[y * wb + x] & 0x3FF:03X} e BTS "
                            f"${bts[y * wb + x]:02X}, esperado ${tallon_layouts.POWER_BOMB_BLOCK_METATILE:03X}/"
                            f"${tallon_layouts.POWER_BOMB_BLOCK_BTS:02X}")
    loadout = dataclasses.replace(room_loadout(area, r), morph=True, bombs=True)   # the blocks all standing
    grid = foot_grid(r, l1, bts, wb, hb, loadout)
    starts = [st for d in r.doors if (st := reach.door_entry(grid, d.side, d.screen))]
    balls = [s for s in reach.reach(grid, starts, loadout) if len(s) == 3]
    for x, y in pbs:
        if not any(max(abs(s[0] - x), abs(s[1] - y)) <= POWER_BOMB_REACH for s in balls):
            problems.append(f"{r.key}: bloco de Power Bomb em ({x},{y}): a bola não chega a {POWER_BOMB_REACH} blocos "
                            f"dele (a Power Bomb não o alcança)")
    return problems


def check_niche_caps() -> list[str]:
    """specs/18i: every in-room beam cap (RoomDef.caps: a niche shut by a beam's door cap, Prime's ice that only that beam
    melts) is a side wall's cap (R/L, a beam door PLM of beamdoors), its 4 blocks air in the drawing and a door cap's blocks in
    the level (RoomDef.cap_blocks: the extensions point at the top one, or Samus walks through it: emulator), inside the room,
    with solid rock right over and under it (the niche's roof and floor, as a door's frame); behind it is an item
    that needs its beam (Item.needs), and that item is out of reach without the beam from every door with every other
    geometry item, the Space Jump's flood fill included (check_item_geometry walks it on foot with and without). Prints the line
    "nichos (specs/18i)"."""
    problems, caps = [], []
    by_key = {r.key: r for r in world_rooms()}
    items = world_items(set(by_key))
    for area, r in all_rooms():
        if not r.caps:
            continue
        l1, bts = r.level().build_blocks()
        wb, hb = r.width * 16, r.height * 16
        for (x, y, side, beam), (_, cells) in zip(r.caps, niche_cap_cells(r)):
            tag = f"{r.key}: tampa de {beam} dentro da sala em ({x},{y})"
            caps.append(f"{r.key.split('_', 1)[1]} ({beam} {side} em {x},{y})")
            if side not in "LR" or (beam, side) not in beamdoors.PLM:
                problems.append(f"{tag}: parede {side} sem porta de feixe de {beam}")
                continue
            if beam not in LOADOUT_FIELD:   # the reach model opens only the beams it has a Loadout field for
                problems.append(f"{tag}: o modelo de alcance não abre uma tampa de {beam} (Loadout: só {tallon_rooms.PLASMA})")
            # the top a shot block (type C), each block under it a vertical extension (type D) pointing at it (BTS $FF,
            # $FE, $FD: the rows up to the top), as a door's cap (smlib/level.py _stamp_door)
            want = {(x, y + k): (0xC if k == 0 else 0xD, None if k == 0 else 0x100 - k) for k in range(4)}
            if any(not (0 < cx < wb - 1 and 0 < cy < hb - 1) or r.canvas.rows()[cy][cx] != "."
                   or l1[cy * wb + cx] >> 12 != want[(cx, cy)][0]
                   or want[(cx, cy)][1] not in (None, bts[cy * wb + cx]) for cx, cy in cells):
                problems.append(f"{tag}: os 4 blocos da tampa não são ar no desenho com os blocos de tampa de porta no nível "
                                f"(tipo C e 3 extensões D, RoomDef.cap_blocks)")
                continue
            if l1[(y - 1) * wb + x] >> 12 != 8 or l1[(y + 4) * wb + x] >> 12 != 8:
                problems.append(f"{tag}: sem rocha logo acima e logo abaixo (o teto e o chão do nicho)")
            behind = [(n, it) for n, it in items if it.room == r.key and beam in it.needs]
            if not behind:
                problems.append(f"{tag}: nenhum item atrás dela (Item.needs com {beam})")
            for n, it in behind:
                others = frozenset(tallon_rooms.GEOMETRY | room_cap_items(r)) - {beam}
                got = [i for i in range(len(r.doors)) if it.spot in tallon_room_reach(r, i, others)[1]]
                if got:
                    problems.append(f"{tag}: o item em {it.spot} se pega sem o {beam} pelas portas {got} (com "
                                    f"{sorted(others)})")
    if not problems:
        print(f"nichos (specs/18i): {len(caps)} tampa(s) de feixe dentro de sala: {', '.join(caps) or 'nenhuma'}; cada uma "
              f"fecha um item que pede o feixe, fora de alcance sem ele de toda porta (com o Space Jump e a geometria toda)")
    return problems


def check_item_geometry() -> list[str]:
    """specs/09e: every placed Tallon item behind on-foot geometry (items.Item.needs: the X-Ray's power bomb hut)
    is picked up from every door of its room with the Morph Ball, the Bombs and the Power Bomb (and the room's
    water), and from none without any one of its `needs` (the others kept). specs/17f: needs = {Space Jump} (a Space Jump
    ledge): from no door without it, from every door with it."""
    problems = []
    by_key = {r.key: r for r in world_rooms()}   # specs/12f: the Chozo's items too
    for n, it in world_items(set(by_key)):
        if not it.needs:
            continue
        r = by_key[it.room]
        tag = (f"{item_world(n)}: item {n[1] if isinstance(n, tuple) else n} "
               f"({tallon_items.KIND_NAME[it.kind]}) em {it.room} {it.spot}")
        # specs/18i: and the beams of the room's in-room caps (a niche's: walked as foot geometry, validate.with_caps)
        full = FOOT_GEOMETRY | ({tallon_rooms.GRAVITY} if r.water else set()) | room_cap_items(r)
        if it.needs == {tallon_rooms.SPACE_JUMP}:
            # specs/17f: a Space Jump ledge (the Triclops Pit's hollow): from no door on foot with every foot geometry item, from
            # every door with the Space Jump (the flood fill). Needed where the room's round already has the Space Jump (a hot
            # room: the round alone cannot tell the ledge from the floor)
            for i in range(len(r.doors)):
                if it.spot in tallon_room_reach(r, i, frozenset(full))[1]:
                    problems.append(f"{tag}: pega-se pela porta {i} sem o Space Jump (uma borda de Space Jump)")
                if it.spot not in tallon_room_reach(r, i, frozenset(full | it.needs))[1]:
                    problems.append(f"{tag}: não se pega pela porta {i} nem com o Space Jump")
            continue
        if not it.needs <= FOOT_GEOMETRY | room_cap_items(r):
            problems.append(f"{tag}: needs {sorted(it.needs)} fora dos itens de geometria a pé")
            continue
        for i, d in enumerate(r.doors):
            if it.spot not in tallon_room_reach(r, i, frozenset(full))[1]:
                problems.append(f"{tag}: não se pega pela porta {i} nem com {sorted(full)}")
            # specs/17h: a door behind the same geometry (the Fiery Shores' L0, behind the Warrior Shrine's power bomb tunnel) is
            # only ever come through with those items (reach_on_foot's rule): its entry has them
            behind = d.gate & tallon_rooms.GEOMETRY if d.ledge else frozenset()
            for item in sorted(it.needs - behind):
                if it.spot in tallon_room_reach(r, i, frozenset(full - {item}))[1]:
                    problems.append(f"{tag}: pega-se pela porta {i} sem {item} (precisa de {sorted(it.needs)})")
    return problems


def check_water_in_rom(rom) -> list[str]:
    """Built ROM (specs/07l): every state of every flooded room (RoomDef.water) points at the water FX
    entry (build.WATER_FX: type 6, surface at y build.WATER_SURFACE_Y, so the room is under water from
    top to bottom, as the reach model assumes); no other room of the remade areas has water."""
    manifest = json.loads((BUILT_ROM.parent / "manifest.json").read_text())
    problems = []
    for area, r in all_rooms():
        if r.key not in manifest:
            problems.append(f"{r.key}: fora do manifest.json da ROM construída (reconstruir)")
            continue
        for st in manifest[r.key]["states"]:
            fx = rom.u16(st + 6)
            entry = rom.read(0x830000 | fx, 16) if fx else b""
            water = bool(fx) and entry[9] == 0x06
            if r.water and (entry != build.WATER_FX or rom.u16(0x830000 | fx + 2) != build.WATER_SURFACE_Y):
                problems.append(f"{r.key}: estado ${st & 0xFFFF:04X} sem a água da sala inteira (FX ${fx:04X})")
            elif not r.water and water:
                problems.append(f"{r.key}: estado ${st & 0xFFFF:04X} com água, a sala não é inundada")
    return problems


# specs/17b: each world with hot rooms: {area number: (its table's keys, its hot rooms)}; the area must be in heat.HEAT_BITS
HOT_WORLDS = {CHOZO_AREA: ({t.key for t in chozo_rooms.TABLE}, chozo_rooms.HOT_ROOMS),
              MAGMOOR_AREA: ({t.key for t in magmoor_rooms.TABLE}, magmoor_rooms.HOT_ROOMS)}   # specs/17c


def check_heat() -> list[str]:
    """specs/12g, static: a hot room (RoomDef.heat) is a room of an area whose palette FX list has the heat object (specs/17b:
    heat.HEAT_BITS, HOT_WORLDS; the Chozo's area 1, and the Magmoor's area 2 once it has rooms), not an elevator room, in its
    world's HOT_ROOMS; every door into it needs the Varia Suit (VARIA in its gate: the user's model, a hot room is impassable
    without it)."""
    problems = []
    for a, (table, hot_rooms) in sorted(HOT_WORLDS.items()):
        unknown = hot_rooms - table
        if unknown:
            problems.append(f"área {a}: salas quentes fora da tabela: {sorted(unknown)}")
        if a not in heat.HEAT_BITS:
            problems.append(f"área {a}: tem salas quentes e nenhuma entrada de calor em heat.HEAT_BITS")
    rooms = {r.key: (area, r) for area, r in all_rooms()}
    for key, (area, r) in rooms.items():
        world = HOT_WORLDS.get(area.number)
        if r.heat and (world is None or area.number not in heat.HEAT_BITS or r.elevator or key not in world[1]):
            problems.append(f"{key}: sala quente fora das áreas com calor, de elevador ou fora de HOT_ROOMS")
        for i, d in enumerate(r.doors):
            if d.to_room in rooms and rooms[d.to_room][1].heat and tallon_rooms.VARIA not in d.gate:
                problems.append(f"{key}: porta {i} ({d.side}{d.screen}) para a sala quente {d.to_room} sem a Varia na trava")
    return problems


def check_heat_in_rom(rom, base) -> list[str]:
    """specs/12g, built ROM: area 1's palette FX list has SM's heat object at heat.HEAT_BIT and its other entries are the
    base ROM's; every state of a hot room points at heat.HEAT_FX and no other state of a room of ours sets the heat bit; no
    vanilla room of area 1 (base ROM) sets it. specs/17b: per area of heat.HEAT_BITS — an area whose list holds the heat
    object natively (Norfair's area 2, bit 0) keeps its whole list as the base ROM's (no patch), a patched one (area 1) only
    the heat entry changed; a hot room's states point at that area's heat.heat_fx; the vanilla rooms of a patched area never
    set its heat bit (in a native area they do: that is their heat)."""
    manifest = json.loads((BUILT_ROM.parent / "manifest.json").read_text())
    problems = []
    for a, bit in sorted(heat.HEAT_BITS.items()):
        try:
            patched = heat.patch(base, a)
            if patched is None:
                if a != heat.NORFAIR:
                    problems.append(f"área {a}: calor: a lista vanilla já tem o calor fora da Norfair?")
            elif rom.read(patched[0], len(patched[1])) != patched[1]:
                problems.append(f"área {a}: calor: ${patched[0]:06X} = {rom.read(patched[0], 2).hex()}, esperado "
                                f"{patched[1].hex()} (reconstruir?)")
        except RuntimeError as e:
            problems.append(f"área {a}: calor: {e}")
            continue
        for k in range(8):
            at = heat.list_entry(base, a, k)
            if (patched is None or k != bit) and rom.u16(at) != base.u16(at):
                problems.append(f"área {a}: calor: entrada {k} da lista de FX de paleta da área {a} mudou")
        if rom.u16(heat.list_entry(rom, a, bit)) != heat.HEAT_OBJECT:
            problems.append(f"área {a}: calor: entrada {bit} da lista não é o calor ${heat.HEAT_OBJECT:04X}")
    try:   # specs/12g2: only the Varia protects (the model's rule, check_heat), not the Gravity Suit too
        at, data = heat.varia_only_patch(base)
        if rom.read(at, len(data)) != data:
            problems.append(f"chozo: calor: ${at:06X} = {rom.read(at, len(data)).hex()}, esperado {data.hex()} (só a Varia "
                            f"protege, specs/12g2; reconstruir?)")
    except RuntimeError as e:
        problems.append(f"chozo: calor: {e}")
    for area, r in all_rooms():
        bit = heat.HEAT_BITS.get(area.number)
        for st in manifest.get(r.key, {}).get("states", []):
            fx = rom.u16(st + 6)
            entry = rom.read(0x830000 | fx, 16) if fx else b""
            hot = bit is not None and bool(fx) and bool(entry[13] & (1 << bit))
            if r.heat and (bit is None or entry != build.room_fx(area, r)):   # specs/17d: a hot room with lava, its lava FX
                problems.append(f"{r.key}: estado ${st & 0xFFFF:04X} sem o FX de calor (FX ${fx:04X})")
            elif not r.heat and hot:
                problems.append(f"{r.key}: estado ${st & 0xFFFF:04X} com o bit de calor, a sala não é quente")
    patched_areas = {a: b for a, b in heat.HEAT_BITS.items() if not heat.native(base, a)}
    for h in vanilla_rooms(base):
        rh = read_room(base, 0x8F0000 | h)
        if rh.area not in patched_areas:
            continue
        for st in rh.states:
            p = 0x830000 | st.fx if st.fx else None
            while p:
                e = base.read(p, 16)
                if e[0:2] == b"\xff\xff":
                    break
                if e[13] & (1 << patched_areas[rh.area]):
                    problems.append(f"chozo: calor: sala vanilla ${h & 0xFFFF:04X} da área {rh.area} usa o bit "
                                    f"{patched_areas[rh.area]}")
                p = None if e[0:2] == b"\x00\x00" else p + 16
    if not problems:
        hot = sorted(r.key for _, r in all_rooms() if r.heat)
        new = [(n, it) for n, it in enumerate(chozo_items.ITEMS) if it.kind in (tallon_items.CHARGE_BEAM, tallon_items.VARIA_SUIT)]
        print(f"chozo (specs/12g): travas novas prontas: porta de charge (PLMs "
              f"${beamdoors.PLM[(tallon_rooms.CHARGE, 'R')]:04X}/${beamdoors.PLM[(tallon_rooms.CHARGE, 'L')]:04X}, "
              f"{beamdoors.CHARGE_NAME}), calor (lista de FX de paleta da área {CHOZO.number}, "
              f"bit {heat.HEAT_BIT} = ${heat.HEAT_OBJECT:04X}, só a Varia protege; sala quente = sem a Varia não entra); itens "
              + ", ".join(f"{tallon_items.KIND_NAME[it.kind]} ${chozo_items.BITS[n]:02X} ({it.room}: "
                          f"{'sem lugar' if it.spot is None else it.spot})" for n, it in new)
              + f"; salas quentes: {', '.join(hot) or 'nenhuma'}; portas de charge: "
              f"{sum(d.lock == tallon_rooms.LOCK_OF[tallon_rooms.CHARGE] for _, r in all_rooms() for d in r.doors) or 'nenhuma'}"
              " (o teste no emulador usa a ROM de teste, build.py --teste-12g)")
    return problems


def check_door_push(rom) -> list[str]:
    """Built ROM (specs/08): every door entry of the remade areas pushes Samus by build.door_push
    (door entry bytes 8-9): floor doors down $0140 (the default sinks her into the ledge under the
    ceiling door), ceiling doors up $02A0 (specs/10b) or $0340 into a flooded room, side doors the default."""
    manifest = json.loads((BUILT_ROM.parent / "manifest.json").read_text())
    by_key = {r.key: r for _, r in all_rooms()}
    problems = []
    for _, r in all_rooms():
        entries = manifest.get(r.key, {}).get("doors", [])
        if len(entries) != len(r.doors):
            problems.append(f"{r.key}: {len(entries)} entradas de porta no manifest.json, {len(r.doors)} portas (reconstruir)")
            continue
        for i, (d, entry) in enumerate(zip(r.doors, entries)):
            got, want = rom.u16(0x830000 | (entry & 0xFFFF) + 8), build.door_push(d.side, by_key[d.to_room].water)
            if got != want:
                problems.append(f"{r.key}: porta {i} ({d.side} → {d.to_room}) empurra ${got:04X}, a regra diz ${want:04X}")
    return problems


# specs/11: the attract-mode demos ($82:876C), played with recorded input when the title screen sat idle, were the
# last vanilla rooms the game loaded; specs/16 turned them off (title.check_demos_off; emulator: test
# titulo_sem_demo_e_novo_jogo). (set, scene, room, door), in the table's order: check_orphans wants the table still the
# base ROM's; check_reclaimed and check_ruins_in_rom keep these rooms off-limits all the same (conservative).
DEMO_SCENES = (
    (0, 0, 0x91F8, 0x896A), (0, 1, 0x9F11, 0x8EAA), (0, 2, 0x9D9C, 0x8DC6), (0, 3, 0xB106, 0x970E),
    (0, 4, 0xAFFB, 0x9792), (0, 5, 0x9D19, 0x8E7A),
    (1, 0, 0xA408, 0xA36C), (1, 1, 0x9C5E, 0x8CCA), (1, 2, 0x9E52, 0x8DEA), (1, 3, 0xAF14, 0x967E),
    (1, 4, 0x9879, 0x8982), (1, 5, 0x9CB3, 0x8DD2),
    (2, 0, 0xCC6F, 0xA21C), (2, 1, 0x91F8, 0x896A), (2, 2, 0xA56B, 0x919E), (2, 3, 0xA322, 0x90EA),
    (2, 4, 0xA59F, 0x91B6), (2, 5, 0xA66A, 0x91F2),
    (3, 0, 0x91F8, 0x890A), (3, 1, 0xD0B9, 0xA474), (3, 2, 0x91F8, 0x890A), (3, 3, 0x9AD9, 0x8D42),
    (3, 4, 0x91F8, 0x890A),
)
# specs/11: vanilla data (outside build.FREE_*) our rooms' states point at on purpose: FX ($83), library
# background ($8F), enemy population ($A1) and set ($B4). Anything else of ours must sit in the build's free space.
VANILLA_SHARED = {
    "FX": {crateria.RAIN_FX: "chuva da Crateria", build.PHANTOON_FX: "FX do Phantoon"},
    "fundo": {FRIGATE.library_bg: "fundo da Wrecked Ship", tallon_rooms.CAVE_BG: "fundo das cavernas (tileset 2)",
              build.PHANTOON_BG: "fundo do Phantoon", CHOZO.library_bg: "fundo das ruínas (tileset $0C, specs/12f)",
              MAGMOOR.library_bg: "fundo das cavernas de lava (tilesets 09/0A, specs/17d)",
              MINES.library_bg: "fundo da base pirata (tileset $0E: canos e máquinas da Tourian, specs/19d, 19e)",
              mines.BACKGROUND[mines.ROCK_TILESET][0]: "fundo da mina de rocha (tileset $08: a rocha do Brinstar, specs/19d, 19f)"},
    "inimigos": {build.EMPTY_ENEMY_POP: "população vazia", build.PHANTOON_ENEMY_POP: "Phantoon"},
    "set de inimigos": {build.EMPTY_ENEMY_SET: "set vazio", build.PHANTOON_ENEMY_SET: "Phantoon"},
}


def entry_stations(rom) -> tuple[dict[tuple[int, int], str], list[str]]:
    """specs/11: the load stations the game itself loads, read from the built ROM's bytes: the new game
    (build's routine at $82:F70F, reached by the JMP at $82:EED9 instead of the intro and Ceres) and the end of
    the frigate (area 0 by STZ $079F at $82:8032, station by LDA #imm at $82:8035). {(area, station): why}."""
    problems, out = [], {}
    if rom.read(build.NEW_GAME_PATCH_SITE, 3) != bytes([0x4C]) + struct.pack("<H", build.NEW_GAME_ROUTINE & 0xFFFF):
        problems.append(f"novo jogo: ${build.NEW_GAME_PATCH_SITE:06X} não pula para ${build.NEW_GAME_ROUTINE:06X} "
                        "(a introdução e Ceres voltariam)")
    code = rom.read(build.NEW_GAME_ROUTINE, 64)
    ops = {}
    for target in (0x079F, 0x078B):   # LDA #imm; STA area / load station
        sta = bytes([0x8D]) + struct.pack("<H", target)
        at = next((i for i in range(len(code) - 5) if code[i] == 0xA9 and code[i + 3:i + 6] == sta), None)
        if at is None:
            problems.append(f"novo jogo: sem LDA #; STA ${target:04X} na rotina ${build.NEW_GAME_ROUTINE:06X}")
        else:
            ops[target] = struct.unpack_from("<H", code, at + 1)[0]
    if len(ops) == 2:
        out[(ops[0x079F], ops[0x078B])] = "novo jogo"
    if rom.read(build.ESCAPE_STATION_SITE - 3, 6) != bytes([0x9C, 0x9F, 0x07, 0xA9, rom.u8(build.ESCAPE_STATION_SITE + 1), 0x00]):
        problems.append(f"fim da fragata: bytes inesperados em ${build.ESCAPE_STATION_SITE - 3:06X}")
    else:
        out[(0, rom.u8(build.ESCAPE_STATION_SITE + 1))] = "fim da fragata"
    return out, problems


def check_orphans(rom, base, manifest, verbose: bool = True) -> list[str]:
    """specs/11, built ROM: no way the game has into a room enters a vanilla room. From the new game and the end of
    the frigate (entry_stations), every load station a save PLM ($B76F) of a reached room saves to and station 0 of
    every area reached (the gunship saves there), through the doors the door blocks use (smlib/roomgraph), the
    rooms reached are exactly ours (manifest); every used station is a door into one of them; each room's door-out
    list as long as its RoomDef's doors. No vanilla room is loaded: the attract-mode demos, the last way in (specs/11),
    are off since specs/16 (title.check_demos_off, from the bytes; their table DEMO_SCENES stays the base ROM's, unused).
    Our rooms' states point outside the build's free
    space (build.FREE_*) only at VANILLA_SHARED, each entry used and with its base bytes. The debug load stations
    ($08-$0F elevators, $10+) need the debug flag $7E05D1, which no code sets: not entry points. Prints the
    orphans (vanilla rooms nothing loads) and the bank-locked bytes only they use."""
    ours = {v["header"] & 0xFFFF: k for k, v in manifest.items() if isinstance(v, dict) and "header" in v}
    defs = {r.key: r for _, r in all_rooms()}
    vanilla = vanilla_rooms(base)
    stations, problems = entry_stations(rom)
    reached: dict[int, str] = {}
    pending = dict(stations)
    while pending:
        starts = {}
        for (area, index), why in sorted(pending.items()):
            _, door = roomgraph.station(rom, area, index)
            dest = roomgraph.door_target(rom, door)
            if dest is None:
                problems.append(f"órfãs: área {area}, estação ${index:02X} ({why}) sem porta (${door:04X})")
            elif dest not in reached:
                starts[dest] = f"estação {area}/${index:02X} ({why})"
        pending = {}
        for h, how in roomgraph.walk(rom, {**starts, **reached}, expand=ours.__contains__).items():
            if h in reached:
                continue
            reached[h] = how
            if h not in ours:
                continue   # a vanilla room: reported below, not walked for saves
            area = rom.u8(0x8F0000 | h + 1)
            for index in sorted(roomgraph.save_stations(rom, h) | {0}):
                if (area, index) not in stations:
                    stations[(area, index)] = pending[(area, index)] = (
                        f"save em {ours[h]}" if index else f"estação 0 da área {area} (nave)")
    for h, how in sorted(reached.items()):
        if h not in ours:
            kind = "vanilla" if h in vanilla else "desconhecida"
            problems.append(f"órfãs: sala {kind} ${h:04X} (área {rom.u8(0x8F0000 | h + 1)}) alcançável: {how}")
    for h, key in sorted(ours.items(), key=lambda kv: kv[1]):
        if h not in reached:
            problems.append(f"{key}: sem caminho do início do jogo (estações {sorted(stations)} e portas)")
        elif len(roomgraph.room_doors(rom, h)) != len(defs[key].doors) + (2 if defs[key].elevator else 0):
            problems.append(f"{key}: {len(roomgraph.room_doors(rom, h))} portas usadas pelos blocos de porta, "
                            f"{len(defs[key].doors)} no RoomDef" + (" (+ 2 do elevador)" if defs[key].elevator else ""))
    # specs/16: the attract demos are off (title.check_demos_off, from the bytes): the title never loads a demo room,
    # so the demos' rooms are orphans like the rest. Their table stays the base ROM's (DEMO_SCENES, which
    # check_reclaimed and check_ruins_in_rom still keep off-limits)
    problems += [f"órfãs: {p}" for p in title.check_demos_off(rom)]
    scenes = tuple(roomgraph.demo_scenes(rom))
    if scenes != DEMO_SCENES or scenes != tuple(roomgraph.demo_scenes(base)):
        problems.append(f"órfãs: tabela das demos (${roomgraph.DEMO_TABLE:06X}) diferente da DEMO_SCENES/da ROM base")
    demo_rooms = {roomgraph.door_target(rom, door) for *_, door in scenes} | {room for _, _, room, _ in scenes}
    # our states point at vanilla data only through VANILLA_SHARED
    free = {"FX": build.FREE_83, "fundo": build.FREE_8F, "inimigos": build.FREE_A1, "set de inimigos": build.FREE_B4}
    size_of = {"FX": lambda p: roomgraph.fx_size(base, p), "fundo": lambda p: roomgraph.bg_size(base, p),
               "inimigos": lambda p: roomgraph.population_size(base, p),
               "set de inimigos": lambda p: roomgraph.enemy_set_size(base, p) + 7}
    bank = {"FX": 0x830000, "fundo": 0x8F0000, "inimigos": 0xA10000, "set de inimigos": 0xB40000}
    used = {k: set() for k in VANILLA_SHARED}
    for h, key in ours.items():
        for st in read_room(rom, 0x8F0000 | h).states:
            pointers = {"FX": st.fx, "fundo": st.bg_data if st.bg_data & 0x8000 else 0, "inimigos": st.enemy_pop,
                        "set de inimigos": st.enemy_set}
            for kind, p in pointers.items():
                # specs/19a: a population of ours may be in a reclaimed $A1 range too (build.ours_a1)
                if not p or (build.ours_8f(p) if kind == "fundo" else build.ours_a1(p) if kind == "inimigos"
                             else p >= free[kind][0] & 0xFFFF):
                    continue
                if p not in VANILLA_SHARED[kind]:
                    problems.append(f"{key}: {kind} em ${bank[kind] | p:06X}, dado vanilla fora da VANILLA_SHARED")
                used[kind].add(p)
            for name, p in (("PLMs", st.plm), ("código de entrada", st.setup_asm), ("código", st.main_asm),
                            ("raio X", st.xray), ("scroll", st.scroll if st.scroll >= 0x8000 else 0)):
                if p and not build.ours_8f(p):
                    problems.append(f"{key}: {name} em $8F:{p:04X}, fora do espaço livre do build")
        for door in roomgraph.room_doors(rom, h):
            asm = rom.u16(0x830000 | door + 10)
            if not rom.u16(0x830000 | door) & 0x8000:
                asm = 0   # specs/12e: the elevator platform's entry has no room: never a transition, its ASM never runs
            if door < build.FREE_83[0] & 0xFFFF or (asm and not build.ours_8f(asm)):
                problems.append(f"{key}: porta ${door:04X} (código ${asm:04X}) fora do espaço livre do build")
    for kind, entries in VANILLA_SHARED.items():
        for p, what in entries.items():
            addr = bank[kind] | p - (7 if kind == "set de inimigos" else 0)
            if p not in used[kind]:
                problems.append(f"órfãs: VANILLA_SHARED {kind} ${bank[kind] | p:06X} ({what}) sem uso nas nossas salas")
            elif rom.read(addr, size_of[kind](p)) != base.read(addr, size_of[kind](p)):
                problems.append(f"órfãs: {kind} vanilla ${bank[kind] | p:06X} ({what}) diferente da ROM base")
    if verbose and not problems:
        orphans = sorted(vanilla)
        keep = set().union(*(roomgraph.byte_set(roomgraph.structures(rom, h)) for h in ours))
        for area in range(8):   # station doors stay (the station tables point at them)
            for index in range(roomgraph.STATION_COUNTS[area]):
                door = roomgraph.station(rom, area, index)[1]
                if door & 0x8000:
                    keep |= set(range(0x830000 | door, (0x830000 | door) + 12))
        only = set().union(*(roomgraph.byte_set(roomgraph.structures(base, h)) for h in orphans)) - keep
        per_area = [sum(1 for h in orphans if base.u8(0x8F0000 | h + 1) == a) for a in range(8)]
        print(f"órfãs: {len(orphans)} salas vanilla sem caminho (por área 0-7: {' '.join(map(str, per_area))}), "
              f"{len(demo_rooms & vanilla)} delas das demos de atração, desligadas (specs/16); bytes só delas: "
              + ", ".join(f"${b:02X} {sum(1 for x in only if x >> 16 == b)}" for b in (0x8F, 0x83, 0xA1, 0xB4)))
    return list(dict.fromkeys(problems))   # states sharing a list would repeat a message


def check_vanilla_pause(base) -> list[str]:
    """specs/12b, base ROM: every build.VANILLA_PAUSE entry is what the vanilla tables of that area hold (the build
    checks it only when it writes an area; this also covers the slot no area uses yet): tilemap and reveal-mask
    pointers, and each icon / elevator-label list starts with the bytes the entry gives."""
    problems = []
    kinds = {"boss": build.ICONS_BOSS, "map_station": build.ICONS_MAP_STATION, "save": build.ICONS_SAVE,
             "elevator_icons": build.ICONS_ELEVATOR}
    for a, vanilla in sorted(build.VANILLA_PAUSE.items()):
        if base.u24(build.PAUSE_TILEMAPS + 3 * a) != vanilla["tilemap"]:
            problems.append(f"VANILLA_PAUSE[{a}]: tilemap ${vanilla['tilemap']:06X}, a ROM base diz "
                            f"${base.u24(build.PAUSE_TILEMAPS + 3 * a):06X}")
        if 0x820000 | base.u16(build.PAUSE_MAP_REVEAL + 2 * a) != vanilla["reveal"]:
            problems.append(f"VANILLA_PAUSE[{a}]: máscara ${vanilla['reveal']:06X} diferente da ROM base")
        lists = {k: 0x820000 | base.u16(build.MAP_ICONS + v + 2 * a) for k, v in kinds.items()}
        lists["elevators"] = 0x820000 | base.u16(build.MAP_ELEVATOR_LABELS + 2 * a)
        for k, at in lists.items():
            if k in vanilla and base.read(at, len(vanilla[k])) != vanilla[k]:
                problems.append(f"VANILLA_PAUSE[{a}]: lista {k} em ${at:06X} diferente da ROM base")
    return problems


def check_slot(world: str, number: int, stations: int = 0) -> tuple[list[str], int]:
    """specs/12b (and 17b): the area slot `number` set aside for `world` is free (no AreaDef of another world uses it), has a
    saved map (areas 0-4; specs/18b: 5 is the Phazon Mines', whose list moves to $81, tools/frigate/mapsave.py; 6 Ceres and 7
    debug have their own code), its
    vanilla pause tables are in build.VANILLA_PAUSE, its explored-map list, at the most its vanilla place holds
    (mapsave.LIST_ROOM), fits the save buffer after the built areas' (the slot's own world left out), and (specs/17b) the
    vanilla load-station table of the area has room for `stations` entries (roomgraph.STATION_COUNTS; at most the 8 save
    slots). Returns the problems and the SRAM left."""
    problems = []
    users = [a.key for a in AREAS if a.number == number and a.key != world]
    if users:
        problems.append(f"área {number} da {world} já usada por {users}")
    if not 0 <= number <= 5:
        problems.append(f"área {number} da {world}: só 0-5 servem (a 5 com a lista do mapa no $81, specs/19b; 6 Ceres, 7 debug)")
        return problems, 0
    if number not in build.VANILLA_PAUSE:
        problems.append(f"área {number} da {world} sem as tabelas vanilla do mapa de pausa em build.VANILLA_PAUSE")
    if stations > min(roomgraph.STATION_COUNTS[number], build.SAVE_SLOTS):
        problems.append(f"área {number} da {world}: {stations} estações, a tabela vanilla tem {roomgraph.STATION_COUNTS[number]} "
                        f"(save: no máximo {build.SAVE_SLOTS})")
    used = mapsave.VANILLA_END + sum(len(a.map_save_bytes()) for a in AREAS if a.pause_map and a.key != world)
    left = mapsave.PACKED_SIZE - used
    if mapsave.LIST_ROOM[number] > left:
        problems.append(f"área {number} da {world}: lista de até {mapsave.LIST_ROOM[number]} bytes, sobram {left} na SRAM")
    return problems, left


def own_fx_bits(base, number: int, region: str) -> list[str]:
    """specs/18b (generalized in 19b): every room of ours in area `number` (its FX entry: build.room_fx, the water's or a vanilla
    one, RoomDef.fx) turns on no palette FX bit of the area's list and no animated tiles bit of the area's own (an entry not shared
    by all 8 areas: `region`'s, the vanilla area's)."""
    problems = []
    lists = [fx_lists(base, a)[1] for a in range(8)]
    shared = sum(1 << k for k in range(8) if len({lst[k] for lst in lists}) == 1)
    for area in AREAS:
        if area.number != number:
            continue
        for r in area.rooms:
            try:
                fx = build.WATER_FX if r.water else build.room_fx(area, r)
            except RuntimeError as e:
                problems.append(f"{r.key}: FX: {e}")
                continue
            if fx is None and r.fx:   # a vanilla FX entry (e.g. crateria.RAIN_FX)
                fx = base.read(0x830000 | r.fx, 16)
            if fx and fx[13]:
                problems.append(f"{r.key}: FX liga os bits ${fx[13]:02X} da lista de FX de paleta da área {number} ({region})")
            if fx and fx[14] & ~shared:
                problems.append(f"{r.key}: FX liga os bits ${fx[14] & ~shared:02X} da lista de tiles animados da área "
                                f"{number} (os da {region})")
    return problems


def check_chozo_slot() -> list[str]:
    """specs/12b: the Chozo Ruins' slot (areas.CHOZO_AREA), check_slot. Prints the slot and the SRAM left."""
    problems, left = check_slot("chozo", CHOZO_AREA)
    if not problems:
        chozo = [a for a in AREAS if a.number == CHOZO_AREA and a.pause_map]
        built = sum(len(a.rooms) for a in chozo)
        uses = sum(len(a.map_save_bytes()) for a in chozo)   # specs/12e: the area is built (its whole table's list)
        print(f"chozo (specs/12b): área {CHOZO_AREA}, {built} salas construídas; tabelas vanilla do mapa de pausa conferidas; "
              f"lista do mapa salvo até {mapsave.LIST_ROOM[CHOZO_AREA]} bytes no lugar vanilla (usa {uses}); SRAM do mapa "
              f"livre: {left - uses} de {mapsave.PACKED_SIZE}")
    return problems


# specs/17b: the Magmoor's load stations (epic 17): 0 = the arrival from the Chozo (P0), 1-2 = Save Stations A and B
MAGMOOR_STATIONS = 3


def check_magmoor_slot(base) -> list[str]:
    """specs/17b: the Magmoor Caverns' slot (areas.MAGMOOR_AREA), check_slot with its 3 load stations; and its heat: the area
    is in heat.HEAT_BITS, natively (the base ROM's list holds the heat object at that entry, so the build patches nothing
    there, heat.patch gives None). Prints the slot, the SRAM left (after the Chozo's too) and the heat entry."""
    problems, left = check_slot("magmoor", MAGMOOR_AREA, MAGMOOR_STATIONS)
    if MAGMOOR_AREA == CHOZO_AREA:
        problems.append(f"área {MAGMOOR_AREA} da magmoor é a da Chozo")
    if MAGMOOR_AREA not in heat.HEAT_BITS:
        problems.append(f"área {MAGMOOR_AREA} da magmoor sem entrada de calor em heat.HEAT_BITS")
    else:
        try:
            if heat.patch(base, MAGMOOR_AREA) is not None:
                problems.append(f"área {MAGMOOR_AREA} da magmoor: a entrada {heat.HEAT_BITS[MAGMOOR_AREA]} da lista de FX de "
                                f"paleta não é o calor ${heat.HEAT_OBJECT:04X} na ROM base (pediria patch)")
        except RuntimeError as e:
            problems.append(f"área {MAGMOOR_AREA} da magmoor: calor: {e}")
    if not problems:
        built = [a for a in AREAS if a.number == MAGMOOR_AREA]
        print(f"magmoor (specs/17b): área {MAGMOOR_AREA}, {sum(len(a.rooms) for a in built)} salas construídas; tabelas vanilla do "
              f"mapa de pausa conferidas; lista do mapa salvo até {mapsave.LIST_ROOM[MAGMOOR_AREA]} bytes no lugar vanilla; "
              f"estações {MAGMOOR_STATIONS} de {roomgraph.STATION_COUNTS[MAGMOOR_AREA]} (save até {build.SAVE_SLOTS}); SRAM do "
              f"mapa livre: {left} de {mapsave.PACKED_SIZE}; calor nativo (lista de FX de paleta "
              f"${heat.list_entry(base, MAGMOOR_AREA, 0):06X}, entrada {heat.HEAT_BITS[MAGMOOR_AREA]} = "
              f"${heat.HEAT_OBJECT:04X}, sem patch)")
    return problems


# specs/18b: the Phendrana Drifts' load stations (epic 18): 0 = the arrival by the north elevator (P0), 1-4 = Save Stations A-D (the
# map station needs none)
PHENDRANA_STATIONS = 5
# specs/18b: area 4's (Maridia's) palette FX and animated tiles lists ($83:AC46/$83:AC56 + 2 * area), read from the base ROM: the
# palette FX list has 3 Maridia objects, then the unused $F745; the animated tiles list has the 2 entries every area shares, 2
# Maridia ones, then the unused $824B. A room of ours in the area turns on no palette FX bit (no heat, no cold: epic 18 decision 5)
# and only animated tiles bits whose entry is the same in all 8 areas' lists.
AREA_ANIMTILES_LISTS = 0x83AC56
PHENDRANA_PALFX = (0xF795, 0xF799, 0xF79D) + (heat.UNUSED_OBJECT,) * 5
PHENDRANA_ANIMTILES = (0x8257, 0x8251, 0x8287, 0x828D) + (0x824B,) * 4


def fx_lists(rom, area: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """specs/18b: `area`'s palette FX and animated tiles lists (8 words each)."""
    pal = 0x830000 | rom.u16(heat.AREA_PALFX_LISTS + 2 * area)
    anim = 0x830000 | rom.u16(AREA_ANIMTILES_LISTS + 2 * area)
    return tuple(rom.u16(pal + 2 * k) for k in range(8)), tuple(rom.u16(anim + 2 * k) for k in range(8))


def check_phendrana_slot(base, built=None) -> list[str]:
    """specs/18b: the Phendrana Drifts' slot (areas.PHENDRANA_AREA), check_slot with its 5 load stations; the area plan of
    areas.py (Phendrana, Mines, Impact Crater: the Mines' slot free, the Impact Crater's the Tallon's); no heat in the area
    (heat.HEAT_BITS, heat.GLOWS); area 4's palette FX and animated tiles lists equal PHENDRANA_PALFX / PHENDRANA_ANIMTILES in the
    base ROM and, if there is one, in the built ROM (nothing patches them), and every room of ours in the area (its FX entry,
    build.room_fx, the water's or a vanilla one, RoomDef.fx) turns on no palette FX bit and no animated tiles bit of the area's own (an entry not shared by
    all 8 areas: Maridia's). Prints the slot and the SRAM left."""
    problems, left = check_slot("phendrana", PHENDRANA_AREA, PHENDRANA_STATIONS)
    for other, number in (("chozo", CHOZO_AREA), ("magmoor", MAGMOOR_AREA)):
        if PHENDRANA_AREA == number:
            problems.append(f"área {PHENDRANA_AREA} da phendrana é a da {other}")
    if MINES_AREA in {a.number for a in AREAS if a.key != "mines"} | {PHENDRANA_AREA, CHOZO_AREA, MAGMOOR_AREA} \
            or not 0 <= MINES_AREA <= 5:   # specs/19e: the Mines' own AreaDef
        problems.append(f"plano das áreas: a área {MINES_AREA} da Phazon Mines já é usada ou não tem mapa salvo")
    if IMPACT_CRATER_AREA != TALLON.number:
        problems.append(f"plano das áreas: a Impact Crater na área {IMPACT_CRATER_AREA}, não na do Tallon ({TALLON.number})")
    if PHENDRANA_AREA in heat.HEAT_BITS or PHENDRANA_AREA in heat.GLOWS:
        problems.append(f"área {PHENDRANA_AREA} da phendrana com calor (heat.HEAT_BITS/GLOWS): Phendrana não tem calor nem frio")
    roms = [("ROM base", base)] + ([("ROM construída", built)] if built else [])
    for name, rom in roms:
        pal, anim = fx_lists(rom, PHENDRANA_AREA)
        if pal != PHENDRANA_PALFX:
            problems.append(f"área {PHENDRANA_AREA}: lista de FX de paleta na {name} = {' '.join(f'{w:04X}' for w in pal)}, esperado "
                            f"{' '.join(f'{w:04X}' for w in PHENDRANA_PALFX)}")
        if anim != PHENDRANA_ANIMTILES:
            problems.append(f"área {PHENDRANA_AREA}: lista de tiles animados na {name} = {' '.join(f'{w:04X}' for w in anim)}, "
                            f"esperado {' '.join(f'{w:04X}' for w in PHENDRANA_ANIMTILES)}")
    lists = [fx_lists(base, a)[1] for a in range(8)]
    shared = sum(1 << k for k in range(8) if len({lst[k] for lst in lists}) == 1)
    problems += own_fx_bits(base, PHENDRANA_AREA, "Maridia")
    if not problems:
        built_rooms = [a for a in AREAS if a.number == PHENDRANA_AREA]
        print(f"phendrana (specs/18b): área {PHENDRANA_AREA}, {sum(len(a.rooms) for a in built_rooms)} salas construídas; tabelas "
              f"vanilla do mapa de pausa conferidas; lista do mapa salvo até {mapsave.LIST_ROOM[PHENDRANA_AREA]} bytes no lugar "
              f"vanilla; estações {PHENDRANA_STATIONS} de {roomgraph.STATION_COUNTS[PHENDRANA_AREA]} (save até {build.SAVE_SLOTS}); "
              f"SRAM do mapa livre: {left} de {mapsave.PACKED_SIZE}; sem calor; listas de FX da área (paleta "
              f"${0x830000 | base.u16(heat.AREA_PALFX_LISTS + 2 * PHENDRANA_AREA):06X}, tiles animados "
              f"${0x830000 | base.u16(AREA_ANIMTILES_LISTS + 2 * PHENDRANA_AREA):06X}) iguais à ROM base, nenhum bit da Maridia "
              f"(tiles animados comuns: ${shared:02X}); plano: Mines na área {MINES_AREA}, Impact Crater na {IMPACT_CRATER_AREA}")
    return problems


# specs/19b: the Phazon Mines' load stations (epic 19): 0 = the arrival by the Tallon's elevator (P0), 1-3 = Save Stations A-C; one
# map station (P23)
MINES_STATIONS = 4
MINES_MAP_STATIONS = 1
# specs/19b: area 5's (Tourian's) lists, read from the base ROM: the palette FX list starts with the heat object $F761 (as Norfair's:
# a room turning on bit 0 there would be hot), then 6 Tourian objects, then the unused $F745; the animated tiles list has only the 2
# entries every area shares, then the unused $824B. A room of ours in the area turns on no palette FX bit (no heat: epic 19 decision
# 2) and only shared animated tiles bits.
MINES_PALFX = (heat.HEAT_OBJECT, 0xF7A1, 0xF7A5, 0xFFC9, 0xFFCD, 0xFFD1, 0xFFD5, heat.UNUSED_OBJECT)
MINES_ANIMTILES = (0x8257, 0x8251) + (0x824B,) * 6
# specs/19b: the boss bits vanilla's area-5 rooms use (vanilla_boss_bits): $04, the grey doors of type 2 of the orphan rooms $DC65 and
# $DCB1 (no code reads area 5's boss byte outside room data: vendor/sm/src); the arenas the epic plans: $08 (Phazon Elite, 19h) and
# $10 (Omega Pirate, 19k; the Torizo's code turns on the area's $04 by itself, 18k)
MINES_VANILLA_BOSS_BITS = {0x04}
MINES_ARENA_BITS = (0x08, 0x10)


def check_mines_slot(base, built=None) -> list[str]:
    """specs/19b: the Phazon Mines' slot (areas.MINES_AREA = 5, Tourian's): check_slot with its 4 load stations; not another world's
    area; its explored-map list may move to $81 (mapsave.MOVES_TO_81) and the $81 free space (mapsave.FREE_81) is all $FF in the
    base ROM and, in the built ROM, $FF but for area 5's list when it went there (the list pointer then points at its start; else the
    pointer is the vanilla one); no heat (heat.HEAT_BITS, heat.GLOWS); area 5's palette FX and animated tiles lists equal
    MINES_PALFX / MINES_ANIMTILES in the base ROM and in the built one, and no room of ours there turns on an area-5 bit
    (own_fx_bits); vanilla's area-5 boss bits are MINES_VANILLA_BOSS_BITS and the planned arena bits none of them; the map icons:
    no boss list (pointer 0), save and elevator lists with room for the stations, the map-station list (vanilla: empty) and how
    many it holds; area 5's reveal mask its own; while no area 5 is built, its pause tables in the built ROM are the base ROM's.
    Prints the slot."""
    problems, left = check_slot("mines", MINES_AREA, MINES_STATIONS)
    if not 0 <= MINES_AREA <= 5:
        return problems   # no saved map, no tables to read
    for other, number in (("chozo", CHOZO_AREA), ("magmoor", MAGMOOR_AREA), ("phendrana", PHENDRANA_AREA),
                          ("tallon", TALLON.number), ("fragata", FRIGATE.number)):
        if MINES_AREA == number:
            problems.append(f"área {MINES_AREA} da mines é a da {other}")
    if MINES_AREA not in mapsave.MOVES_TO_81:
        problems.append(f"área {MINES_AREA} da mines fora de mapsave.MOVES_TO_81: a lista do mapa (~45 bytes) não cabe nos "
                        f"{mapsave.LIST_ROOM[MINES_AREA]} do lugar vanilla")
    lo, hi = mapsave.FREE_81
    if base.read(lo, hi - lo + 1) != b"\xFF" * (hi - lo + 1):
        problems.append(f"$81 livre: ${lo:06X}-${hi:06X} não é todo $FF na ROM base")
    mines = [a for a in AREAS if a.number == MINES_AREA and a.pause_map]
    offs = mines[0].map_save_bytes() if mines else []
    if built is not None:
        ptr = 0x810000 | built.u16(mapsave.LISTS + 2 * MINES_AREA)
        want = mapsave.list_at(MINES_AREA, len(offs)) if offs else 0x810000 | mapsave.VANILLA_LIST_PTRS[MINES_AREA]
        if ptr != want:
            problems.append(f"área {MINES_AREA}: ponteiro da lista do mapa salvo ${ptr:06X}, esperado ${want:06X}")
        n = len(offs) if want == lo else 0
        if built.read(lo + n, hi - lo + 1 - n) != b"\xFF" * (hi - lo + 1 - n):
            problems.append(f"$81 livre: bytes escritos em ${lo + n:06X}-${hi:06X} (só a lista do mapa da área {MINES_AREA} vai ali)")
    # specs/19i: the map station's icon list of area 5 (vanilla: only FFFF, at $82:CA4F) is a new one in $82's free space (the
    # build's $82 allocator, after the new-game routine) once a map station of the Mines is built; the vanilla FFFF stays
    station_list = None
    if built is not None and mines and any(r.map_station for r in mines[0].rooms):
        at = build.MAP_ICONS + build.ICONS_MAP_STATION + 2 * MINES_AREA
        vanilla_at = 0x820000 | base.u16(at)
        station_list = 0x820000 | built.u16(at)
        if not build.NEW_GAME_ROUTINE < station_list <= 0x82FFFF or built.read(vanilla_at, 2) != b"\xFF\xFF":
            problems.append(f"área {MINES_AREA}: lista de ícones de map station em ${station_list:06X} (esperado no $82 livre, "
                            f"depois de ${build.NEW_GAME_ROUTINE:06X}; a vanilla FFFF em ${vanilla_at:06X} intacta)")
    if MINES_AREA in heat.HEAT_BITS or MINES_AREA in heat.GLOWS:
        problems.append(f"área {MINES_AREA} da mines com calor (heat.HEAT_BITS/GLOWS): a Mines não tem calor")
    for name, rom in [("ROM base", base)] + ([("ROM construída", built)] if built else []):
        pal, anim = fx_lists(rom, MINES_AREA)
        if pal != MINES_PALFX:
            problems.append(f"área {MINES_AREA}: lista de FX de paleta na {name} = {' '.join(f'{w:04X}' for w in pal)}, esperado "
                            f"{' '.join(f'{w:04X}' for w in MINES_PALFX)}")
        if anim != MINES_ANIMTILES:
            problems.append(f"área {MINES_AREA}: lista de tiles animados na {name} = {' '.join(f'{w:04X}' for w in anim)}, "
                            f"esperado {' '.join(f'{w:04X}' for w in MINES_ANIMTILES)}")
    lists = [fx_lists(base, a)[1] for a in range(8)]
    shared = sum(1 << k for k in range(8) if len({lst[k] for lst in lists}) == 1)
    problems += own_fx_bits(base, MINES_AREA, "Tourian")
    vanilla_bits = vanilla_boss_bits(base, MINES_AREA)
    if vanilla_bits != MINES_VANILLA_BOSS_BITS:
        problems.append(f"área {MINES_AREA}: bits de chefe vanilla {sorted(vanilla_bits)}, MINES_VANILLA_BOSS_BITS diz "
                        f"{sorted(MINES_VANILLA_BOSS_BITS)}")
    for bit in MINES_ARENA_BITS:
        if bit in vanilla_bits or MINES_ARENA_BITS.count(bit) > 1:
            problems.append(f"área {MINES_AREA}: bit de arena ${bit:02X} repetido ou de sala vanilla")
    vanilla = build.VANILLA_PAUSE.get(MINES_AREA, {})
    if base.u16(build.MAP_ICONS + build.ICONS_BOSS + 2 * MINES_AREA) != 0 or "boss" in vanilla:
        problems.append(f"área {MINES_AREA}: lista de ícones de chefe na ROM base (o épico conta com nenhuma)")
    room = {k: (len(vanilla.get(k, b"")) - (2 if k == "map_station" else 0)) // 4 for k in ("map_station", "save", "elevator_icons")}
    if room["save"] < MINES_STATIONS:
        problems.append(f"área {MINES_AREA}: {room['save']} ícones de save na lista vanilla, a Mines tem {MINES_STATIONS} estações")
    if room["elevator_icons"] < 2:
        problems.append(f"área {MINES_AREA}: {room['elevator_icons']} ícones de elevador na lista vanilla, a Mines tem 2 elevadores")
    reveal = [base.u16(build.PAUSE_MAP_REVEAL + 2 * a) for a in range(8)]
    sharing = {a for a in range(8) if a != MINES_AREA and reveal[a] == reveal[MINES_AREA]}
    if sharing - {build.DEBUG_AREA}:   # the debug area 7's pointer is area 5's: nothing loads area 7 (specs/11)
        problems.append(f"área {MINES_AREA}: máscara da map station dividida com as áreas {sorted(sharing)}")
    if built is not None and not mines:   # nothing of area 5 is written yet
        for k, v in (("tilemap", build.PAUSE_TILEMAPS), ("reveal", build.PAUSE_MAP_REVEAL), ("label", build.PAUSE_AREA_LABELS),
                     ("ícones", build.MAP_ICONS), ("rótulos", build.MAP_ELEVATOR_LABELS)):
            size = 3 if k == "tilemap" else 2
            for kind in ((0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60) if k == "ícones" else (0,)):
                at = v + kind + size * MINES_AREA
                if built.read(at, size) != base.read(at, size):
                    problems.append(f"área {MINES_AREA}: ponteiro {k} em ${at:06X} mudou sem sala da Mines")
        for k, at in (("save", build.ICONS_SAVE), ("map_station", build.ICONS_MAP_STATION),
                      ("elevator_icons", build.ICONS_ELEVATOR)):
            p = 0x820000 | base.u16(build.MAP_ICONS + at + 2 * MINES_AREA)
            if k in vanilla and built.read(p, len(vanilla[k])) != vanilla[k]:
                problems.append(f"área {MINES_AREA}: lista {k} em ${p:06X} mudou sem sala da Mines")
    if not problems:
        print(f"mines (specs/19b): área {MINES_AREA}, {sum(len(a.rooms) for a in mines)} salas construídas; tabelas vanilla do mapa "
              f"de pausa conferidas (ícones: save {room['save']}, elevador {room['elevator_icons']}, map station "
              f"{room['map_station']} de {MINES_MAP_STATIONS}: a lista vanilla é só FFFF; "
              + (f"specs/19i: a nova, com a map station, em ${station_list:06X} no $82 livre" if station_list
                 else "a 19i dá uma nova com a map station") + "; sem lista de chefe); "
              f"lista do mapa salvo até {mapsave.LIST_ROOM[MINES_AREA]} bytes no lugar vanilla, maior no $81 livre (${lo:06X}-"
              f"${hi:06X}, {hi - lo + 1} bytes $FF; usa {len(offs)}); estações {MINES_STATIONS} de "
              f"{roomgraph.STATION_COUNTS[MINES_AREA]} (save até {build.SAVE_SLOTS}); máscara da map station "
              f"${0x820000 | reveal[MINES_AREA]:06X} dividida só com a área {build.DEBUG_AREA} (debug); SRAM do mapa livre: {left} de "
              f"{mapsave.PACKED_SIZE}; sem calor (a entrada 0 da lista de paleta da área é o calor ${heat.HEAT_OBJECT:04X}, nenhuma "
              f"sala nossa a liga); listas de FX da área (paleta ${0x830000 | base.u16(heat.AREA_PALFX_LISTS + 2 * MINES_AREA):06X}, "
              f"tiles animados ${0x830000 | base.u16(AREA_ANIMTILES_LISTS + 2 * MINES_AREA):06X}) iguais à ROM base, nenhum bit da "
              f"Tourian (tiles animados comuns: ${shared:02X}); bits de chefe vanilla da área: "
              f"{', '.join(f'${b:02X}' for b in sorted(vanilla_bits))} (salas órfãs); arenas planejadas: "
              f"{', '.join(f'${b:02X}' for b in MINES_ARENA_BITS)}")
    return problems


PRIME_CHOZO_LOCKS = Path(__file__).resolve().parent.parent / "research/prime_chozo_locks.json"
# the Chozo table's own area for check_layout (not in AREAS: no room is built, specs/12c)
CHOZO_TABLE_AREA = AreaDef(key="chozo", number=CHOZO_AREA, name="CHOZO", rooms=chozo_rooms.ALL_ROOMS, tileset=0x0C,
                           music=(0, 0), layer2=0, library_bg=0, load_stations=[], pause_map=False)


def check_chozo() -> list[str]:
    """specs/12c: the whole Chozo Ruins table (chozo/rooms.py), built or not, as check_tallon does for the Tallon: against
    Prime's data (rooms, boxes, door pairs, and the locks/features read from Prime's objects), check_layout on all regions
    together and on each region alone, and the explored map within area CHOZO_AREA's vanilla save-list place."""
    problems = chozo_rooms.check_prime(PRIME_WORLDS, PRIME_CHOZO_LOCKS)
    problems += check_layout(CHOZO_TABLE_AREA, chozo_rooms.ALL_ROOMS)
    for region in chozo_rooms.REGIONS:
        problems += [f"chozo, só a região {region}: {p}"
                     for p in check_layout(CHOZO_TABLE_AREA, chozo_rooms.build_rooms({region}))]
    built = [r.key for r in all_rooms_flat() if r.key.startswith("chozo_")]
    if built != [r.key for r in chozo_rooms.ROOMS]:
        problems.append(f"chozo: salas no build {built}, a tabela diz {[r.key for r in chozo_rooms.ROOMS]}")
    if problems:
        return problems
    try:
        offs = mapsave.needed(pausemap.build(chozo_rooms.ALL_ROOMS)[1])
        by_region = {g: len(mapsave.needed(pausemap.build(chozo_rooms.build_rooms({g}))[1])) for g in chozo_rooms.REGIONS}
    except ValueError as e:   # a map tile used twice
        return [f"chozo: {e}"]
    problems += [f"chozo: {p}" for p in mapsave.check({CHOZO_AREA: offs})]
    if len(offs) > mapsave.LIST_ROOM[CHOZO_AREA]:
        problems.append(f"chozo: mapa usa {len(offs)} bytes da SRAM; o lugar vanilla da área {CHOZO_AREA} tem "
                        f"{mapsave.LIST_ROOM[CHOZO_AREA]}")
    if not problems:
        rooms = chozo_rooms.ALL_ROOMS
        vertical = sum(d.side in "TB" for r in rooms for d in r.doors) // 2
        kinds = {}
        for ks in chozo_rooms.DOCK_LOCKS.values():
            for k in ks:
                kinds[k] = kinds.get(k, 0) + 1
        print(f"chozo (tabela inteira, specs/12c, salas construídas: {len(chozo_rooms.ROOMS)}): {len(rooms)} salas, "
              f"{len(chozo_rooms.LINKS)} ligações ({vertical} de chão/teto), {sum(r.width * r.height for r in rooms)} telas, "
              f"mapa {len(offs)}/{mapsave.LIST_ROOM[CHOZO_AREA]} bytes de SRAM (por região: "
              f"{' '.join(f'{g} {n}' for g, n in by_region.items())}); travas do Prime em {len(chozo_rooms.DOCK_LOCKS)} docas "
              f"({', '.join(f'{k} {n}' for k, n in sorted(kinds.items()))}), sem item SM")
    return problems


PRIME_MAGMOOR_LOCKS = Path(__file__).resolve().parent.parent / "research/prime_magmoor_locks.json"
# the Magmoor table's own area for check_layout (not in AREAS: no room is built, specs/17c); tileset $09, Norfair's hot one (epic 17,
# technical decision 3; the style is specs/17d's)
MAGMOOR_TABLE_AREA = AreaDef(key="magmoor", number=MAGMOOR_AREA, name="MAGMOOR", rooms=magmoor_rooms.ALL_ROOMS, tileset=0x09,
                             music=(0, 0), layer2=0, library_bg=0, load_stations=[], pause_map=False)


def check_magmoor() -> list[str]:
    """specs/17c: the whole Magmoor Caverns table (magmoor/rooms.py), built or not, as check_chozo does for the Chozo: against
    Prime's data (rooms, boxes, door pairs, the locks/beams/features/hot rooms read from Prime's objects), check_layout on all
    regions together and on each region alone, no floor/ceiling door on an elevator room (the shaft is its ceiling), the rooms of
    the build = magmoor_rooms.ROOMS, and the explored map within area MAGMOOR_AREA's vanilla save-list place."""
    problems = magmoor_rooms.check_prime(PRIME_WORLDS, PRIME_MAGMOOR_LOCKS)
    try:
        problems += check_layout(MAGMOOR_TABLE_AREA, magmoor_rooms.ALL_ROOMS)
        for region in magmoor_rooms.REGIONS:
            problems += [f"magmoor, só a região {region}: {p}"
                         for p in check_layout(MAGMOOR_TABLE_AREA, magmoor_rooms.build_rooms({region}))]
    except (IndexError, ValueError) as e:   # a door pointing past the other room's doors, sides not opposite
        return problems + [f"magmoor: {e}"]
    for r in magmoor_rooms.ALL_ROOMS:
        if r.key in magmoor_rooms.ELEVATOR_ROOMS | magmoor_rooms.DECORATIVE_ELEVATORS and any(d.side in "TB" for d in r.doors):
            problems.append(f"{r.key}: sala de elevador com porta de chão/teto (o poço do elevador é o teto)")
    built = [r.key for r in all_rooms_flat() if r.key.startswith("magmoor_")]
    if built != [r.key for r in magmoor_rooms.ROOMS]:
        problems.append(f"magmoor: salas no build {built}, a tabela diz {[r.key for r in magmoor_rooms.ROOMS]}")
    if problems:
        return problems
    try:
        offs = mapsave.needed(pausemap.build(magmoor_rooms.ALL_ROOMS)[1])
        by_region = {g: len(mapsave.needed(pausemap.build(magmoor_rooms.build_rooms({g}))[1])) for g in magmoor_rooms.REGIONS}
    except ValueError as e:   # a map tile used twice
        return [f"magmoor: {e}"]
    problems += [f"magmoor: {p}" for p in mapsave.check({MAGMOOR_AREA: offs})]
    if len(offs) > mapsave.LIST_ROOM[MAGMOOR_AREA]:
        problems.append(f"magmoor: mapa usa {len(offs)} bytes da SRAM; o lugar vanilla da área {MAGMOOR_AREA} tem "
                        f"{mapsave.LIST_ROOM[MAGMOOR_AREA]}")
    if not problems:
        rooms = magmoor_rooms.ALL_ROOMS
        vertical = sum(d.side in "TB" for r in rooms for d in r.doors) // 2
        kinds = {}
        for ks in magmoor_rooms.DOCK_LOCKS.values():
            for k in ks:
                kinds[k] = kinds.get(k, 0) + 1
        beams = {}
        for b in magmoor_rooms.KEY_BEAM.values():
            beams[b] = beams.get(b, 0) + 1
        print(f"magmoor (tabela inteira, specs/17c, salas construídas: {len(magmoor_rooms.ROOMS)}): {len(rooms)} salas, "
              f"{len(magmoor_rooms.LINKS)} ligações ({vertical} de chão/teto), {sum(r.width * r.height for r in rooms)} telas, "
              f"mapa {len(offs)}/{mapsave.LIST_ROOM[MAGMOOR_AREA]} bytes de SRAM (por região: "
              f"{' '.join(f'{g} {n}' for g, n in by_region.items())}); travas do Prime em {len(magmoor_rooms.DOCK_LOCKS)} docas "
              f"({', '.join(f'{k} {n}' for k, n in sorted(kinds.items()))}; cor das portas: "
              f"{', '.join(f'{b} {n}' for b, n in sorted(beams.items()))}); {len(magmoor_rooms.HOT_ROOMS)} salas quentes "
              f"(Area Damage); elevadores: {len(magmoor_rooms.ELEVATOR_ROOMS)} de verdade (17e), "
              f"{len(magmoor_rooms.DECORATIVE_ELEVATORS)} de enfeite; sem item SM")
    return problems


PRIME_PHENDRANA_LOCKS = Path(__file__).resolve().parent.parent / "research/prime_phendrana_locks.json"
# the Phendrana table's own area for check_layout (not in AREAS: no room is built, specs/18c); tileset 0 until the style (specs/18d)
PHENDRANA_TABLE_AREA = AreaDef(key="phendrana", number=PHENDRANA_AREA, name="PHENDRANA", rooms=phendrana_rooms.ALL_ROOMS,
                               tileset=0x00, music=(0, 0), layer2=0, library_bg=0, load_stations=[], pause_map=False)


PHENDRANA_MIN_MAP_X = 3   # specs/18e: 3 columns * 8 px = the 24 px area 4's map scrolls further left


def check_phendrana() -> list[str]:
    """specs/18c: the whole Phendrana Drifts table (phendrana/rooms.py), built or not, as check_magmoor does for the Magmoor:
    against Prime's data (rooms, boxes, door pairs, the locks/beams/features/snow/water/plasma ice/wave panels read from Prime's
    objects, no heat), check_layout on all regions together and on each region alone, no floor/ceiling door on an elevator room,
    the rooms of the build = phendrana_rooms.ROOMS, and the explored map within area PHENDRANA_AREA's vanilla save-list place."""
    problems = phendrana_rooms.check_prime(PRIME_WORLDS, PRIME_PHENDRANA_LOCKS)
    try:
        problems += check_layout(PHENDRANA_TABLE_AREA, phendrana_rooms.ALL_ROOMS)
        for region in phendrana_rooms.REGIONS:
            problems += [f"phendrana, só a região {region}: {p}"
                         for p in check_layout(PHENDRANA_TABLE_AREA, phendrana_rooms.build_rooms({region}))]
    except (IndexError, ValueError) as e:   # a door pointing past the other room's doors, sides not opposite
        return problems + [f"phendrana: {e}"]
    for r in phendrana_rooms.ALL_ROOMS:
        if r.key in phendrana_rooms.ELEVATOR_ROOMS | phendrana_rooms.DECORATIVE_ELEVATORS and any(d.side in "TB" for d in r.doors):
            problems.append(f"{r.key}: sala de elevador com porta de chão/teto (o poço do elevador é o teto)")
    # specs/18e: area 4's pause map may scroll 24 px left of its leftmost column (DetermineMapScrollLimits $82:9EC4,
    # sm_82.c:1811): from column PHENDRANA_MIN_MAP_X on that never goes under 0 (measured: both rooms seen scrolling, 18e)
    west = [r.key for r in phendrana_rooms.ALL_ROOMS if r.map_x < PHENDRANA_MIN_MAP_X]
    if west:
        problems.append(f"phendrana: salas antes da coluna {PHENDRANA_MIN_MAP_X} do mapa (a rolagem da área 4 passaria de 0): {west}")
    built = [r.key for r in all_rooms_flat() if r.key.startswith("phendrana_")]
    if built != [r.key for r in phendrana_rooms.ROOMS]:
        problems.append(f"phendrana: salas no build {built}, a tabela diz {[r.key for r in phendrana_rooms.ROOMS]}")
    if problems:
        return problems
    try:
        offs = mapsave.needed(pausemap.build(phendrana_rooms.ALL_ROOMS)[1])
        by_region = {g: len(mapsave.needed(pausemap.build(phendrana_rooms.build_rooms({g}))[1])) for g in phendrana_rooms.REGIONS}
    except ValueError as e:   # a map tile used twice
        return [f"phendrana: {e}"]
    problems += [f"phendrana: {p}" for p in mapsave.check({PHENDRANA_AREA: offs})]
    if len(offs) > mapsave.LIST_ROOM[PHENDRANA_AREA]:
        problems.append(f"phendrana: mapa usa {len(offs)} bytes da SRAM; o lugar vanilla da área {PHENDRANA_AREA} tem "
                        f"{mapsave.LIST_ROOM[PHENDRANA_AREA]}")
    if not problems:
        rooms = phendrana_rooms.ALL_ROOMS
        vertical = sum(d.side in "TB" for r in rooms for d in r.doors) // 2
        kinds: dict[str, int] = {}
        for ks in phendrana_rooms.DOCK_LOCKS.values():
            for k in ks:
                kinds[k] = kinds.get(k, 0) + 1
        beams: dict[str, int] = {}
        for b in phendrana_rooms.KEY_BEAM.values():
            beams[b] = beams.get(b, 0) + 1
        built_n = len(phendrana_rooms.ROOMS)
        print(f"phendrana (tabela inteira, specs/18c, salas construídas: {built_n}"
              + (f", todas as {len(rooms)} do Prime (specs/18m)" if built_n == len(rooms) else "") + f"): {len(rooms)} salas, "
              f"{len(phendrana_rooms.LINKS)} ligações ({vertical} de chão/teto), {sum(r.width * r.height for r in rooms)} telas, "
              f"mapa {len(offs)}/{mapsave.LIST_ROOM[PHENDRANA_AREA]} bytes de SRAM (por região: "
              f"{' '.join(f'{g} {n}' for g, n in by_region.items())}); travas do Prime em {len(phendrana_rooms.DOCK_LOCKS)} docas "
              f"({', '.join(f'{k} {n}' for k, n in sorted(kinds.items()))}; cor das portas: "
              f"{', '.join(f'{b} {n}' for b, n in sorted(beams.items()))}); neve em {len(phendrana_rooms.SNOW_ROOMS)} salas, água "
              f"em {len(phendrana_rooms.WATER_ROOMS)}, gelo de plasma em {len(phendrana_rooms.PLASMA_ICE)}, painel de onda em "
              f"{len(phendrana_rooms.WAVE_PANELS)}, nenhuma quente nem fria; elevadores: {len(phendrana_rooms.ELEVATOR_ROOMS)} "
              f"de verdade (18e); sem item SM")
    return problems


PRIME_MINES_LOCKS = Path(__file__).resolve().parent.parent / "research/prime_mines_locks.json"
# the Mines table's own area for check_layout (not in AREAS: no room is built, specs/19c); tileset 0 until the style (specs/19d)
MINES_TABLE_AREA = AreaDef(key="mines", number=MINES_AREA, name="MINES", rooms=mines_rooms.ALL_ROOMS,
                           tileset=0x00, music=(0, 0), layer2=0, library_bg=0, load_stations=[], pause_map=False)


def check_mines() -> list[str]:
    """specs/19c: the whole Phazon Mines table (mines/rooms.py), built or not, as check_phendrana does for Phendrana: against Prime's
    data (rooms, boxes, door pairs, the locks/beams/features/power-bomb-only objects/wave panels read from Prime's objects, no heat,
    snow, water nor plasma ice, no door only the Super Missile opens), check_layout on all regions together and on each region alone,
    no floor/ceiling door on an elevator room and its side door on its bottom screen (specs/18e: the shaft above), the rooms of the
    build = mines_rooms.ROOMS, and the explored map: within what area 5 may keep (mapsave.list_room: in $81 past the vanilla 21
    bytes, specs/19b) and within the save buffer left by the built areas."""
    problems = mines_rooms.check_prime(PRIME_WORLDS, PRIME_MINES_LOCKS)
    try:
        problems += check_layout(MINES_TABLE_AREA, mines_rooms.ALL_ROOMS)
        for region in mines_rooms.REGIONS:
            problems += [f"mines, só a região {region}: {p}"
                         for p in check_layout(MINES_TABLE_AREA, mines_rooms.build_rooms({region}))]
    except (IndexError, ValueError) as e:   # a door pointing past the other room's doors, sides not opposite
        return problems + [f"mines: {e}"]
    for r in mines_rooms.ALL_ROOMS:
        if r.key in mines_rooms.ELEVATOR_ROOMS | mines_rooms.DECORATIVE_ELEVATORS:
            if any(d.side in "TB" for d in r.doors):
                problems.append(f"{r.key}: sala de elevador com porta de chão/teto (o poço do elevador é o teto)")
            if any(d.side in "LR" and d.screen != r.height - 1 for d in r.doors):
                problems.append(f"{r.key}: sala de elevador com porta fora da tela de baixo")
    built = [r.key for r in all_rooms_flat() if r.key.startswith("mines_")]
    if built != [r.key for r in mines_rooms.ROOMS]:
        problems.append(f"mines: salas no build {built}, a tabela diz {[r.key for r in mines_rooms.ROOMS]}")
    if problems:
        return problems
    try:
        offs = mapsave.needed(pausemap.build(mines_rooms.ALL_ROOMS)[1])
        by_region = {g: len(mapsave.needed(pausemap.build(mines_rooms.build_rooms({g}))[1])) for g in mines_rooms.REGIONS}
    except ValueError as e:   # a map tile used twice
        return [f"mines: {e}"]
    problems += [f"mines: {p}" for p in mapsave.check({MINES_AREA: offs})]
    if len(offs) > mapsave.list_room(MINES_AREA):
        problems.append(f"mines: mapa usa {len(offs)} bytes da SRAM; a área {MINES_AREA} guarda até {mapsave.list_room(MINES_AREA)}")
    left = mapsave.PACKED_SIZE - mapsave.VANILLA_END - sum(len(a.map_save_bytes()) for a in AREAS
                                                            if a.pause_map and a.number != MINES_AREA)
    if len(offs) > left:
        problems.append(f"mines: mapa usa {len(offs)} bytes da SRAM, sobram {left}")
    if not problems:
        rooms = mines_rooms.ALL_ROOMS
        vertical = sum(d.side in "TB" for r in rooms for d in r.doors) // 2
        kinds: dict[str, int] = {}
        for ks in mines_rooms.DOCK_LOCKS.values():
            for k in ks:
                kinds[k] = kinds.get(k, 0) + 1
        beams: dict[str, int] = {}
        for b in mines_rooms.KEY_BEAM.values():
            beams[b] = beams.get(b, 0) + 1
        where = (f"no $81 (passa dos {mapsave.LIST_ROOM[MINES_AREA]} do lugar vanilla, specs/19b)"
                 if len(offs) > mapsave.LIST_ROOM[MINES_AREA] else "no lugar vanilla")
        print(f"mines (tabela inteira, specs/19c, salas construídas: {len(mines_rooms.ROOMS)}): {len(rooms)} salas, "
              f"{len(mines_rooms.LINKS)} ligações ({vertical} de chão/teto), {sum(r.width * r.height for r in rooms)} telas, "
              f"mapa {len(offs)} bytes de SRAM {where}, sobram {left} (por região: "
              f"{' '.join(f'{g} {n}' for g, n in by_region.items())}); travas do Prime em {len(mines_rooms.DOCK_LOCKS)} docas "
              f"({', '.join(f'{k} {n}' for k, n in sorted(kinds.items()))}; cor das portas: "
              f"{', '.join(f'{b} {n}' for b, n in sorted(beams.items()))}); só a Power Bomb quebra em "
              f"{len(mines_rooms.PB_ONLY)} salas ({sum(mines_rooms.PB_ONLY.values())} objetos), painel de onda em "
              f"{len(mines_rooms.WAVE_PANELS)}, nenhuma quente, fria, com neve ou água, nenhuma porta só de Super Missile; "
              f"elevadores: {len(mines_rooms.ELEVATOR_ROOMS)} de verdade (19e), a porta na tela de baixo; sem item SM")
    return problems


PRIME_IMPACT_LOCKS = Path(__file__).resolve().parent.parent / "research/prime_impact_locks.json"
# the Impact Crater table's own area for check_layout (not in AREAS: no room is built, specs/20c); the crater's look (specs/20d)
IMPACT_TABLE_AREA = AreaDef(key="impact", number=IMPACT_CRATER_AREA, name="IMPACT", rooms=impact_rooms.ALL_ROOMS,
                            tileset=impact_style.TILESET, music=(0, 0), layer2=0, library_bg=0, load_stations=[], pause_map=False)


def check_impact_graph() -> list[str]:
    """specs/20c: the whole Impact Crater table (impact/rooms.py), built or not, as check_mines does for the Mines: against Prime's
    data (rooms, boxes, door pairs, the locks/beams/features read from Prime's objects, no heat, snow, water, plasma ice, wave panel
    nor power-bomb-only object, no door only the Super Missile opens, the way from the Entry Point to the Lair), check_layout on all
    regions together and on each region alone, the rooms of the build (and of the manifest, if built) = impact_rooms.ROOMS, and the
    map shared with the Tallon in area 0: no screen on a Tallon room, the explored map of both within area 0's list
    (mapsave.list_room) and within the save buffer left by the other areas."""
    problems = impact_rooms.check_prime(PRIME_WORLDS, PRIME_IMPACT_LOCKS)
    try:
        problems += check_layout(IMPACT_TABLE_AREA, impact_rooms.ALL_ROOMS)
        for region in impact_rooms.REGIONS:
            problems += [f"impact, só a região {region}: {p}"
                         for p in check_layout(IMPACT_TABLE_AREA, impact_rooms.build_rooms({region}))]
    except (IndexError, ValueError) as e:   # a door pointing past the other room's doors, sides not opposite
        return problems + [f"impact: {e}"]
    tallon_cells = {(x, y): r.key for r in tallon_rooms.ALL_ROOMS
                    for x in range(r.map_x, r.map_x + r.width) for y in range(r.map_y, r.map_y + r.height)}
    for r in impact_rooms.ALL_ROOMS:
        hit = sorted({tallon_cells[(x, y)] for x in range(r.map_x, r.map_x + r.width)
                      for y in range(r.map_y, r.map_y + r.height) if (x, y) in tallon_cells})
        if hit:
            problems.append(f"{r.key}: sobrepõe {hit} do Tallon no mapa da área {IMPACT_CRATER_AREA}")
    built = [r.key for r in all_rooms_flat() if r.key.startswith(impact_rooms.PREFIX)]
    if built != [r.key for r in impact_rooms.ROOMS]:
        problems.append(f"impact: salas no build {built}, a tabela diz {[r.key for r in impact_rooms.ROOMS]}")
    manifest_path = BUILT_ROM.parent / "manifest.json"
    if manifest_path.exists():
        in_rom = sorted(k for k in json.loads(manifest_path.read_text()) if k.startswith(impact_rooms.PREFIX))
        if in_rom != sorted(r.key for r in impact_rooms.ROOMS) or not set(in_rom) <= {t.key for t in impact_rooms.TABLE}:
            problems.append(f"impact: salas no manifest {in_rom}, a tabela diz {sorted(r.key for r in impact_rooms.ROOMS)}")
    if problems:
        return problems
    try:
        tallon_offs = mapsave.needed(pausemap.build(tallon_rooms.ALL_ROOMS)[1])
        offs = mapsave.needed(pausemap.build([*tallon_rooms.ALL_ROOMS, *impact_rooms.ALL_ROOMS])[1])
    except ValueError as e:   # a map tile used twice
        return [f"impact: {e}"]
    if len(offs) > mapsave.list_room(IMPACT_CRATER_AREA):
        problems.append(f"impact: mapa da área {IMPACT_CRATER_AREA} (Tallon e cratera) usa {len(offs)} bytes da SRAM; a área "
                        f"guarda até {mapsave.list_room(IMPACT_CRATER_AREA)}")
    left = mapsave.PACKED_SIZE - mapsave.VANILLA_END - sum(len(a.map_save_bytes()) for a in AREAS
                                                            if a.pause_map and a.number != IMPACT_CRATER_AREA)
    if len(offs) > left:
        problems.append(f"impact: mapa da área {IMPACT_CRATER_AREA} (Tallon e cratera) usa {len(offs)} bytes da SRAM, sobram {left}")
    if not problems:
        rooms = impact_rooms.ALL_ROOMS
        vertical = sum(d.side in "TB" for r in rooms for d in r.doors) // 2
        kinds: dict[str, int] = {}
        for ks in impact_rooms.DOCK_LOCKS.values():
            for k in ks:
                kinds[k] = kinds.get(k, 0) + 1
        beams: dict[str, int] = {}
        for b in impact_rooms.KEY_BEAM.values():
            beams[b] = beams.get(b, 0) + 1
        print(f"impact crater (specs/20c): {len(rooms)} salas no grafo, {len(impact_rooms.LINKS)} ligações ({vertical} de "
              f"chão/teto), {sum(r.width * r.height for r in rooms)} telas, caminho da entrada à Lair; mapa da área "
              f"{IMPACT_CRATER_AREA} com o Tallon {len(offs)} bytes de SRAM (Tallon {len(tallon_offs)}, de "
              f"{mapsave.list_room(IMPACT_CRATER_AREA)}), nenhuma tela sobre o Tallon; travas do Prime em "
              f"{len(impact_rooms.DOCK_LOCKS)} docas ({', '.join(f'{k} {n}' for k, n in sorted(kinds.items()))}; cor das "
              f"portas: {', '.join(f'{b} {n}' for b, n in sorted(beams.items()))}), "
              f"{sum(len(a['docks']) for a in json.loads(PRIME_IMPACT_LOCKS.read_text()).values()) - len(impact_rooms.DOCK_LOCKS)}"
              f" sem porta (a descida); nenhuma quente, fria, com água, só de Power Bomb ou só de Super Missile; "
              f"{len(impact_rooms.ROOMS)} construídas")
    return problems


def impact_opens() -> tuple[int, frozenset] | None:
    """specs/20e: the round the Artifact Temple's teleporter opens (the first of the walk, tallon_progress_built, in which Samus gets to
    the Omega Pirate's arena, impact_rooms.OPENS_AFTER, with its `needs`) and that round's gear; None if never. specs/20h: the gear she
    gets into every crater room with (the crater is out of the rounds' walk: world_rooms)."""
    arena = chozo_bosses.arena_of(impact_rooms.OPENS_AFTER)
    if arena is None:
        return None
    rounds = tallon_progress_built()[0]
    n = next((n for n, rd in enumerate(rounds) if any(k == arena.room for k, _ in rd.states) and arena.needs <= rd.have), None)
    return None if n is None else (n, rounds[n].have)


def impact_arrival() -> tuple[dict[str, frozenset], dict[str, int]]:
    """specs/20h: (the gear Samus has in each built crater room, the round she first gets there): the teleporter's round
    (impact_opens) for every one (check_impact_rooms walks them all with it); empty if it never opens."""
    opens = impact_opens()
    if opens is None:
        return {}, {}
    keys = [r.key for r in TALLON.rooms if r.key.startswith(impact_rooms.PREFIX)]
    return {k: opens[1] for k in keys}, {k: opens[0] for k in keys}


def check_impact_rooms() -> list[str]:
    """specs/20e: the Impact Crater's built rooms (impact/rooms.py ROOMS: the regions of ACTIVE_REGIONS, each with its drawing in
    impact/layouts.py, in area 0's AreaDef after the Tallon's rooms, in the crater's look); the way in = the Artifact Temple's
    teleporter (impact_rooms.TELEPORTER, an elevator of areas.ELEVATORS: check_elevators, check_elevators_in_rom), opened by the
    Omega Pirate's arena (OPENS_AFTER): the round it opens = the first round of the walk (tallon_progress_built) in which Samus
    gets to that arena with its `needs`; with that round's gear, from the Entry Point's platform (where the teleporter puts her),
    every built crater room is reached through its doors (their gates), and from every state reached the platform again (the way
    back to the temple). Prime's locks of the built links mapped (mines' rule): each key dock = the cap of KEY_BEAM's beam and
    that gate on its side; GATES only on links with a Prime lock; no event lock waits in the built links. The save station only in
    the Entry Point (Prime's, specs/20a), a load station of area 0. specs/20g: an event lock only if impact_rooms.EVENT_OUT leaves
    it out (with why); the acid (the phazon that hurts, decision 4) exactly in the descent's rooms (region C) with no floor door in
    Prime's graph. Prints the line "impact crater (specs/20e)"."""
    problems = []
    built = {r.key: r for r in TALLON.rooms if r.key.startswith(impact_rooms.PREFIX)}
    want = [t.key for t in impact_rooms.TABLE if t.region in impact_rooms.ACTIVE_REGIONS]
    if list(built) != want:
        problems.append(f"impact: salas construídas {list(built)}, as regiões ativas {sorted(impact_rooms.ACTIVE_REGIONS)} têm {want}")
    missing = sorted(set(built) - set(impact_layouts.LAYOUTS))
    if missing:
        problems.append(f"impact: salas construídas sem desenho (caixa provisória): {missing}")
    for k, r in built.items():
        if (TALLON.tileset_of(r), r.style, r.library_bg, r.layer2) != (impact_style.TILESET, impact_style.STYLE,
                                                                        *impact_style.BACKGROUND):
            problems.append(f"impact: {k} fora da cara da cratera (tileset, peças ou fundo de impact/style.py)")
    temple, entry = impact_rooms.TELEPORTER
    arena = chozo_bosses.arena_of(impact_rooms.OPENS_AFTER)
    if entry != impact_rooms.ENTRY or entry not in built or arena is None:
        return problems + [f"impact: teleporte {impact_rooms.TELEPORTER} sem a entrada construída ou sem a arena de "
                           f"{impact_rooms.OPENS_AFTER}"]
    # Prime's locks of the built links
    capped = 0
    for (a, to), kinds in impact_rooms.DOCK_LOCKS.items():
        if a not in built or to not in built:
            continue
        d = next(d for d in built[a].doors if d.to_room == to)
        beam = impact_rooms.KEY_BEAM.get((a, to))
        if "event" in kinds and (a, to) not in impact_rooms.EVENT_OUT:
            problems.append(f"impact: a trava de evento {a} -> {to} numa ligação construída (nenhuma filha a mapeou)")
        if "key" in kinds and (d.lock != tallon_rooms.LOCK_OF.get(beam) or d.gate != frozenset({beam})):
            problems.append(f"impact: a porta {a} -> {to} é de {beam} no Prime, a sala tem a tampa {d.lock} e a trava "
                            f"{sorted(d.gate)}")
        capped += "key" in kinds
    for link in impact_rooms.GATES:
        a, b = sorted(link)
        if (a, b) not in impact_rooms.DOCK_LOCKS and (b, a) not in impact_rooms.DOCK_LOCKS:
            problems.append(f"impact: trava {a}-{b} em GATES sem trava do Prime")
    stray = sorted(k for k in impact_rooms.EVENT_OUT if "event" not in impact_rooms.DOCK_LOCKS.get(k, ()))
    if stray:
        problems.append(f"impact: EVENT_OUT com docas sem a trava event do Prime: {stray}")
    # specs/20g (epic 20, decision 4): the phazon that hurts (SM's acid, check_lava's rule: off the way, a way out) only in the
    # descent's rooms (region C: the Infusion Chamber and the Subchambers), in each of them that has no floor door in Prime's
    # graph (a floor door's fall would go through the acid, which covers the room from its surface down), never elsewhere
    floor_door = {ra for (ra, sa, _), _ in impact_rooms.LINKS if sa == "B"} | {rb for _, (rb, sb, _) in impact_rooms.LINKS
                                                                               if sb == "B"}
    acid = sorted(k for k, r in built.items() if r.acid is not None)
    want_acid = sorted(k for k in built if impact_rooms.region_of(k) == "C" and k not in floor_door)
    if acid != want_acid:
        problems.append(f"impact: ácido (o phazon que machuca) em {acid}; a decisão 4 pede nas salas da descida sem porta de "
                        f"chão: {want_acid}")
    saves = [k for k, r in built.items() if r.save_station]
    if saves != [entry]:
        problems.append(f"impact: save stations em {saves}, o Prime tem a da {entry}")
    stations = [st.index for st in TALLON.load_stations if st.room in saves]
    if len(stations) != len(saves):
        problems.append(f"impact: save station sem estação de carga da área {TALLON.number}")
    # specs/20f: Prime's missile recharge (the Crater Missile Station's) = the SM's refill station, only there, once built
    refills = [k for k, r in built.items() if r.missile_station]
    if refills != ([impact_rooms.MISSILE_STATION] if impact_rooms.MISSILE_STATION in built else []):
        problems.append(f"impact: recarga de mísseis em {refills}, o Prime tem a da {impact_rooms.MISSILE_STATION}")
    if problems:
        return problems
    if impact_opens() is None:
        return [f"impact: a arena de {arena.room} nunca é alcançada com {sorted(arena.needs)}: o teleporte nunca abre"]
    opens, have = impact_opens()

    def walk(start):
        seen, todo = {start}, [start]
        while todo:
            key, at = todo.pop()
            r = built[key]
            exits, _ = tallon_room_walk(r, at, have)
            for i in exits:
                if i == ELEVATOR:
                    continue
                nxt = exit_to(r, i)
                if nxt[0] in built and exit_open(r, i, have) and nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
        return seen

    reached = walk((entry, ELEVATOR))
    lost = sorted(set(built) - {k for k, _ in reached})
    if lost:
        problems.append(f"impact: {lost} inalcançáveis da plataforma da {entry} na rodada {opens} (com {have_names(have)})")
    for state in sorted(reached, key=str):
        back = walk(state)
        if not any(k == entry and ELEVATOR in tallon_room_walk(built[k], at, have)[0] for k, at in back):
            problems.append(f"impact: de {state} não há volta à plataforma da {entry} (o teleporte para o templo)")
    if not problems:
        st = ", ".join(f"{st.room} (estação {st.index} da área {TALLON.number})" for st in TALLON.load_stations
                       if st.room in saves)
        print(f"impact crater (specs/20e; regiões ativas: {''.join(sorted(impact_rooms.ACTIVE_REGIONS))}): {len(built)} salas "
              f"construídas ({', '.join(built)}), ligações entre elas: {sum(len(r.doors) for r in built.values()) // 2}; entrada pelo "
              f"teleporte do {temple} (elevador da área {TALLON.number}, sem troca de área) depois do Omega Pirate (arena "
              f"{arena.room}, bit ${arena.bit:02X} da área {MINES_AREA}): rodada {opens}; com o equipamento dela, da plataforma "
              f"toda sala construída e de toda sala a volta à plataforma; travas do Prime nas ligações construídas: {capped} "
              f"docas key com a tampa da cor do Prime; save station: {st}"
              + (f"; recarga de mísseis: {', '.join(refills)}" if refills else "")
              + (f"; trava de evento fora: {', '.join(f'{a} -> {b}' for a, b in impact_rooms.EVENT_OUT if a in built)}"
                 if any(a in built for a, _ in impact_rooms.EVENT_OUT) else "")
              + (f"; phazon que machuca (ácido do SM, specs/20g): {', '.join(f'{k} (linha {built[k].acid})' for k in acid)}; "
                 f"sem ácido (porta de chão, a queda): "
                 f"{', '.join(k for k in built if impact_rooms.region_of(k) == 'C' and k in floor_door)}" if acid else ""))
    return problems


# specs/20h: area 0's boss bits: vanilla's ($04, the grey door and the state of the Bomb Torizo's room $8F:9804, an orphan; no code
# reads area 0's boss byte outside room data, vendor/sm/src) and the one arena of ours there, Metroid Prime's ($10: the game's
# "final boss beaten", which specs/20i's ending reads; the Torizo's own code turns on $04 as it dies, 18k)
TALLON_VANILLA_BOSS_BITS = {0x04}
IMPACT_FINAL_BIT = 0x10


def check_impact_boss(base, built) -> list[str]:
    """specs/20h (epic 20, decision 3): Metroid Prime's arena in the Lair, the Omega Pirate's model. ARENAS has exactly one arena in a
    crater room, the Lair's (impact_rooms.LAIR; impact_enemies.ARENA_ROOMS), and none in another room of area 0: a Torizo arena
    (check_arenas: check_torizo) of bit IMPACT_FINAL_BIT waiting for the Torizo's bit, with `needs`; area 0's vanilla boss bits =
    TALLON_VANILLA_BOSS_BITS, the arena's bit none of them; its one boss the stand-in of Prime's MetroidPrimeStage2 (ARENA_KINDS,
    in PRIME_LAIR_LAYER0), a copy whose health and touch the line shows; every door of the Lair a boss door (BOSS_DOORS: lock
    "boss", the gate BOSS_GATE, the Torizo's grey cap while it lives, none dead: check_tallon_doors_in_rom reads the ROM) and no
    BOSS_DOORS entry elsewhere; with the teleporter round's gear (impact_opens) less the arena's `needs` the door stays shut (no
    way out of the Lair), with it open; in the built ROM, no other room state of area 0 picks a state by area 0's boss bits (E629).
    Prints the line "impact crater (specs/20h)"."""
    B, T = chozo_bosses, impact_enemies
    problems = []
    crater = {r.key: r for r in crater_only().rooms}
    area0 = {r.key for r in TALLON.rooms}
    arenas = [a for a in B.ARENAS if a.room in area0]
    if [a.room for a in arenas] != [impact_rooms.LAIR] or set(T.ARENA_ROOMS) != {impact_rooms.LAIR}:
        return [f"impact: arenas da área {TALLON.number} {[a.room for a in arenas]}, ARENA_ROOMS {sorted(T.ARENA_ROOMS)}: só a "
                f"{impact_rooms.LAIR} (decisão 3)"]
    a = arenas[0]
    r = crater.get(a.room)
    if r is None:
        return [f"impact: a arena {a.room} não está construída"]
    vanilla = vanilla_boss_bits(base or base_rom(), TALLON.number)
    if vanilla != TALLON_VANILLA_BOSS_BITS:
        problems.append(f"área {TALLON.number}: bits de chefe vanilla {sorted(vanilla)}, TALLON_VANILLA_BOSS_BITS diz "
                        f"{sorted(TALLON_VANILLA_BOSS_BITS)}")
    if a.bit != IMPACT_FINAL_BIT or a.bit in vanilla or a.condition != B.BOSS_BIT or a.arg != B.TORIZO_BIT \
            or not torizo_arena(a) or not a.needs or a.prize is not None:
        problems.append(f"impact: a arena {a.room} (bit ${a.bit:02X}, condição {a.condition} ${a.arg:02X}, needs {sorted(a.needs)}, "
                        f"prêmio {a.prize}) não é a do Torizo com o bit ${IMPACT_FINAL_BIT:02X} da área {TALLON.number}, sem "
                        "prêmio, vencida com o equipamento")
    spawns = TALLON.enemies.get(a.room, [])
    kinds = [e.kind for e in spawns if e.species.boss]
    if len(spawns) != 1 or len(kinds) != 1 or T.ARENA_KINDS.get(kinds[0]) not in T.PRIME_LAIR_LAYER0:
        problems.append(f"impact: a Lair com {[e.kind for e in spawns]}: um só chefe, o do MetroidPrimeStage2 do Prime")
    doors = [(a.room, d.to_room) for d in r.doors]
    if set(doors) != set(impact_rooms.BOSS_DOORS) or not r.doors:
        problems.append(f"impact: portas da Lair {doors}, BOSS_DOORS {sorted(impact_rooms.BOSS_DOORS)}: toda porta da arena "
                        "tranca até a vitória")
    for d in r.doors:
        if d.lock != "boss" or d.gate != {chozo_rooms.BOSS_GATE} or d.dead_lock is not None \
                or build.arena_door_alive_cap(a.room, d) != B.GREY_DOOR_TORIZO:
            problems.append(f"impact: a porta {a.room} -> {d.to_room} (tampa {d.lock}, trava {sorted(d.gate)}, morta "
                            f"{d.dead_lock}) não é a cinza do Torizo que abre na vitória (nenhum PLM depois: o Prime não tem porta)")
    opens = impact_opens()
    if opens is None:
        return problems + ["impact: o teleporte nunca abre (sem rodada para a luta)"]
    k, have = opens
    shut = [d.to_room for d in r.doors if door_open(r, d, have - a.needs)]
    if shut or not all(door_open(r, d, have) for d in r.doors):
        problems.append(f"impact: a porta da Lair abre sem {sorted(a.needs)} ({shut}) ou não abre com o equipamento da rodada {k}")
    if built is not None:
        manifest = json.loads((BUILT_ROM.parent / "manifest.json").read_text())
        for key in sorted(area0 - {a.room}):
            info = manifest.get(key)
            if info is None:
                continue
            q = 0x8F0000 | (info["header"] & 0xFFFF) + 11
            while built.u16(q) != 0xE5E6:
                c = built.u16(q)
                if c == 0xE629:
                    problems.append(f"{key}: estado escolhido pelo bit de chefe ${built.u8(q + 2):02X} da área {TALLON.number} "
                                    "(só a arena do Metroid Prime usa os bits da área 0)")
                q += 2 + {0xE612: 1, 0xE629: 1, 0xE5EB: 2}.get(c, 0) + 2
    if not problems:
        info = species_info(spawns[0].species.ptr)
        copy = B.COPIES[spawns[0].species.ptr]
        print(f"impact crater (specs/20h): Metroid Prime na {a.room} (Prime: {a.prime}; decisão 3: uma arena, a luta em duas fases "
              f"do Prime fora): cópia $A0:{copy.ptr:04X} do Bomb Torizo ${copy.source:04X}, vida {info['hp']}, toque "
              f"{info['damage']}, os ataques do Torizo; vence quando o Torizo liga o bit ${a.arg:02X}, a arena liga o bit "
              f"${a.bit:02X} da área {TALLON.number} (o chefe final vencido; nenhum dos vanilla dela: "
              f"{', '.join(f'${b:02X}' for b in sorted(vanilla))}, só de salas órfãs), nenhum prêmio; a porta para "
              f"{', '.join(d.to_room for d in r.doors)} tranca até a vitória (cinza do Torizo; depois a tampa azul do nível, qualquer tiro abre: o Prime não tem porta), "
              f"sem {', '.join(sorted(a.needs))} não há saída; rodada {k}; fora: "
              + ", ".join(f"{t} {n}" for t, n in sorted(T.PRIME_LAIR_LAYER0.items()) if t not in T.ARENA_KINDS.values())
              + " e a Phazon Pool")
    return problems


# specs/20i: the SM's ending, reused as it is (epic 20, decision 5): the game state table's entries $26 and $27 ($82:8981 + 2 *
# state), GameState_38 ($82:84BD, the fade) and the ending's state ($8B:D443), the percentage's routine ($8B:E627) and its tables
GAME_STATE_TABLE = 0x828981
ENDING_CODE = [(GAME_STATE_TABLE + 2 * impact_ending.ENDING_START, 4), (0x8284BD, 0x60), (0x8BD443, 0x30),
               (impact_ending.PERCENT_ROUTINE, impact_ending.PERCENT_ROUTINE_SIZE), impact_ending.PERCENT_TABLES]
LAIR_EXIT_BIT_READ = bytes([0xAF, 0x28 + 0, 0xD8, 0x7E, 0x29, IMPACT_FINAL_BIT, 0x00])   # LDA $7ED828 (area 0) / AND #$0010
LAIR_EXIT_ENDING = bytes([0xA9, impact_ending.ENDING_START, 0x00, 0x8D, 0x98, 0x09])     # LDA #$0026 / STA $0998


def check_impact_ending(base, built) -> list[str]:
    """specs/20i (epic 20, decision 5): the game's end. The Lair (the arena of IMPACT_FINAL_BIT, check_impact_boss) has one
    door, the ceiling one; both its states run the way out (impact_ending.exit_routine for the arena's bit of area 0 and that
    door's cap block: the alive state after the arena routine, the dead one alone), and that code reads area 0's boss bit
    IMPACT_FINAL_BIT and sets the game state $26 (the SM's ending, LAIR_EXIT_* checked in the bytes themselves, not only against
    the generator); the SM's ending is the vanilla one (ENDING_CODE: the state table's $26/$27, the fade, the ending, the
    percentage's routine and tables, byte for byte); the percentage of every placed item (items_gear, CalcItemPercentageCount's
    formula with the BUILT ROM's tables) is one per item, the rounds' count. Prints the line "fim do jogo (specs/20i)"."""
    if built is None:
        return []
    problems = []
    a = chozo_bosses.arena_of(impact_rooms.LAIR)
    r = {x.key: x for x in crater_only().rooms}.get(impact_rooms.LAIR)
    if a is None or r is None:
        return [f"fim do jogo: a arena ou a sala {impact_rooms.LAIR} não existe"]
    if a.bit != IMPACT_FINAL_BIT:
        problems.append(f"fim do jogo: a arena da Lair liga o bit ${a.bit:02X}, o fim lê o ${IMPACT_FINAL_BIT:02X}")
    tops = [d for d in r.doors if d.side == "T"]
    if len(r.doors) != 1 or len(tops) != 1 or (r.key, tops[0].to_room) not in impact_rooms.BOSS_DOORS:
        problems.append(f"fim do jogo: a Lair tem {[(d.side, d.to_room) for d in r.doors]}: a saída para o fim é a única porta, "
                        "a do teto (a de chefe)")
        return problems
    cap = build.lair_exit_cap(r)
    want = impact_ending.exit_routine(TALLON.number, IMPACT_FINAL_BIT, *cap)
    info = json.loads((BUILT_ROM.parent / "manifest.json").read_text()).get(r.key)
    if info is None:
        return problems + [f"fim do jogo: {r.key} fora do manifest.json (reconstruir)"]
    room = read_room(built, info["header"])
    if len(room.states) != 2:
        return problems + [f"fim do jogo: a Lair com {len(room.states)} estados (o vivo e o morto)"]
    dead, alive = room.states
    exit_at = dead.main_asm
    code = built.read(0x8F0000 | exit_at, len(want)) if exit_at >= 0x8000 else b""
    if code != want or LAIR_EXIT_BIT_READ not in code or LAIR_EXIT_ENDING not in code:
        problems.append(f"fim do jogo: a saída da Lair (main ASM do estado morto ${exit_at:04X}) não é a que lê o bit "
                        f"${IMPACT_FINAL_BIT:02X} da área {TALLON.number} e liga o estado ${impact_ending.ENDING_START:02X} "
                        f"na porta do teto (tampa em {cap})")
    want_alive = impact_ending.alive_main_asm(chozo_bosses.ROUTINE, exit_at)
    if alive.main_asm < 0x8000 or built.read(0x8F0000 | alive.main_asm, len(want_alive)) != want_alive:
        problems.append(f"fim do jogo: o estado vivo da Lair (main ASM ${alive.main_asm:04X}) não passa pela saída depois da "
                        "rotina das arenas")
    for addr, n in ENDING_CODE:
        if built.read(addr, n) != base.read(addr, n):
            problems.append(f"fim do jogo: ${addr:06X} (+{n}) difere do SM (o fim reaproveitado como está)")
    placed = world_items({x.key for x in world_rooms()})
    have, unknown = items_gear(placed)
    pct = item_percentage(built, have)
    if unknown or pct != len(placed):
        problems.append(f"fim do jogo: a porcentagem da tela de fim com os {len(placed)} itens é {pct}% (um por item)")
    if not problems:
        print(f"fim do jogo (specs/20i): a saída da {r.key} = a porta do teto para {tops[0].to_room} (tampa em {cap}, aberta "
              f"só depois da vitória): com o bit ${IMPACT_FINAL_BIT:02X} da área {TALLON.number} (o chefe final vencido) a "
              f"Samus para antes da porta e o jogo vai ao estado ${impact_ending.ENDING_START:02X} -> "
              f"${impact_ending.ENDING_CREDITS:02X} (o fim do SM, como a fragata usava: créditos e a tela 'YOUR RATE FOR "
              f"COLLECTING ITEMS', {len(ENDING_CODE)} trechos iguais ao SM), sem o bit nada; código nos dois estados da Lair "
              f"(${alive.main_asm:04X} / ${exit_at:04X}); a porcentagem na tela com os {len(placed)} itens (tabelas da ROM "
              f"construída): {pct}% (energia {have['energy']}, mísseis {have.get('missiles', 0)}, super mísseis "
              f"{have.get('supers', 0)}, power bombs {have.get('power_bombs', 0)})")
    return problems


PRIME_AREA_COLOURS = Path(__file__).resolve().parent.parent / "research/prime_area_colours.json"


def impact_test_build():
    """specs/20d: the crater look's test build made in memory (build.build(test_20d=True), its output in a temporary folder)."""
    import contextlib
    import io
    import tempfile
    with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
        return build.build(test_20d=True, out_dir=Path(tmp))


def check_impact_style(base, built) -> list[str]:
    """specs/20d: the Impact Crater's look (impact/style.py). Against the Mines (smlib/mines.py): the same pieces, table, graphics,
    background and paint line as the Mines' rock; the phazon colours = the Mines'; the rock = the Mines' grey tinted with the
    crater's hue/saturation (so different from it). Against Prime (research/prime_area_colours.json): that hue/saturation is the
    crater's warm textures' mean; the crater has a larger share of warm textures than the Mines; the phazon blue (mines.PHAZON) has
    the hue of both worlds' blue textures. Against the other areas: entry $03 is its own in the base ROM, no look nor area of ours
    and no attract demo room uses it; the palette = the Mines' rock's but for the rock's colours, the door colours (lines 0 1-3, 1
    1-7) are tileset 4's and line PAINT_LINE the purple. In the game's ROM (`built`), while no crater room exists, entry $03 keeps
    its 9 vanilla bytes, and no room of ours uses $03; in the test build (impact_test_build) entry $03 points at the $08 entry's
    table and graphics and at a palette in the fixed range = impact_style.palette, and it differs from the game's ROM only there.
    Prints the line "impact crater (specs/20d)"."""
    problems = []
    t, src = impact_style.TILESET, impact_style.SOURCE
    words = [base.u16(TILESET_TABLE + 2 * i) for i in range(0x1D)]
    if words.count(words[t]) != 1:
        problems.append(f"cratera: a entrada do tileset {t:02X} é dividida com outra no vanilla")
    looks = {crateria.SURFACE_TILESET, crateria.CAVE_TILESET, ruins.RUINS_TILESET, beamdoors.PAINT_TILESET, *lava.TILESETS,
             *ice.TILESETS, *mines.TILESETS} | {a.tileset_of(r) for a, r in all_rooms()
                                                if not r.key.startswith(impact_rooms.PREFIX)} | {a.tileset for a in AREAS}
    if t in looks or t == mines.ROCK_SOURCE:
        problems.append(f"cratera: o tileset {t:02X} já é de outra área ou cara")
    demos = sorted(room for room in {d[2] for d in DEMO_SCENES}
                   if any(st.tileset == t for st in read_room(base, 0x8F0000 | room).states))
    if demos:
        problems.append(f"cratera: salas de demo no tileset {t:02X}: {[f'${r:04X}' for r in demos]}")
    style = impact_style.STYLE
    if (style.tileset != t or dataclasses.replace(style, name=mines.MINE_ROCK.name, tileset=mines.ROCK_TILESET) != mines.MINE_ROCK
            or src != mines.ROCK_TILESET or impact_style.GRAPHICS_SOURCE != mines.SOURCE[src]
            or impact_style.BACKGROUND != mines.BACKGROUND[src] or impact_style.PAINT_LINE != mines.PAINT_LINES[src]
            or impact_style.OWN_LINES != mines.OWN_LINES[src]):
        problems.append("cratera: peças, tabela, gráficos, fundo ou linhas diferentes dos da rocha da mina")
    colours = impact_style.COLOURS
    if set(colours) != set(mines.ROCK_COLOURS) or set(impact_style.PHAZON_KEYS) | set(impact_style.ROCK_KEYS) != set(colours):
        problems.append("cratera: cores em lugares diferentes dos da rocha da mina")
    else:
        for k in impact_style.PHAZON_KEYS:
            if colours[k] != mines.ROCK_COLOURS[k]:
                problems.append(f"cratera: linha {k[0]} cor {k[1]} (phazon) {colours[k]}, a mina usa {mines.ROCK_COLOURS[k]}")
        for k in impact_style.ROCK_KEYS:
            if colours[k] != impact_style.tint(mines.ROCK_COLOURS[k]) or colours[k] == mines.ROCK_COLOURS[k]:
                problems.append(f"cratera: linha {k[0]} cor {k[1]} (rocha) {colours[k]}, esperado a da mina "
                                f"{mines.ROCK_COLOURS[k]} na matiz da cratera ({impact_style.tint(mines.ROCK_COLOURS[k])})")
    prime = json.loads(PRIME_AREA_COLOURS.read_text())
    crater, mine = prime["Impact Crater"], prime["Phazon Mines"]
    if (impact_style.ROCK_HUE, impact_style.ROCK_SAT) != (crater["warm_hue"], round(crater["warm_sat"], 2)):
        problems.append(f"cratera: rocha na matiz {impact_style.ROCK_HUE} saturação {impact_style.ROCK_SAT}, o Prime diz "
                        f"{crater['warm_hue']} {crater['warm_sat']}")
    share = {n: w["kinds"].get("warm", 0) / w["textures"] for n, w in prime.items()}
    if not share["Impact Crater"] > share["Phazon Mines"]:
        problems.append(f"cratera: o Prime não tem mais texturas quentes na cratera que na mina ({share})")
    blue = [impact_style.hue_sat(crater["blue_mean"])[0], impact_style.hue_sat(mine["blue_mean"])[0],
            impact_style.hue_sat(mines.PHAZON[1])[0]]
    if max(blue) - min(blue) > 20:
        problems.append(f"cratera: o azul do phazon (matiz {blue[2]:.0f}) não é o das texturas azuis do Prime "
                        f"(cratera {blue[0]:.0f}, mina {blue[1]:.0f})")
    pal, rock = impact_style.palette(base), build.mines_palette(base, src)
    changed = {i for i in range(len(pal) // 2) if pal[2 * i:2 * i + 2] != rock[2 * i:2 * i + 2]}
    if len(pal) != len(rock) or changed != {line * 16 + i for line, i in impact_style.ROCK_KEYS}:
        problems.append(f"cratera: a paleta muda as cores {sorted(changed)} da rocha da mina, esperado só as da rocha")
    ref = mines.vanilla_palette(base, beamdoors.PAINT_TILESET)
    for line, idx in ((0, range(1, 4)), (1, range(1, 8))):
        if any(pal[2 * (line * 16 + i):2 * (line * 16 + i) + 2] != ref[2 * (line * 16 + i):2 * (line * 16 + i) + 2] for i in idx):
            problems.append(f"cratera: linha {line} (cores das portas) diferente da do tileset 4")
    if tuple(int.from_bytes(pal[2 * (impact_style.PAINT_LINE * 16 + i):][:2], "little") for i in (1, 2, 3)) != beamdoors.PURPLE:
        problems.append(f"cratera: linha {impact_style.PAINT_LINE} sem o roxo da porta de onda")
    if problems or built is None:
        return problems
    manifest = json.loads((BUILT_ROM.parent / "manifest.json").read_text())
    users = sorted(k for k, v in manifest.items() if isinstance(v, dict) and "header" in v and not k.startswith(impact_rooms.PREFIX)
                   and any(st.tileset == t for st in read_room(built, 0x8F0000 | (v["header"] & 0xFFFF)).states))
    if users:
        problems.append(f"cratera: salas fora da cratera no tileset {t:02X}: {users}")
    e = mines.entry(built, t)
    if e != mines.entry(base, t):
        problems.append(f"cratera: a entrada do tileset {t:02X} mudou de lugar")
    written = any(r.key.startswith(impact_rooms.PREFIX) for r in all_rooms_flat())
    if not written and built.read(e, 9) != base.read(e, 9):
        problems.append(f"ROM do jogo: tileset {t:02X} (cratera) mudou sem sala da cratera (só a ROM de teste o escreve)")
    test = built if written else impact_test_build()
    te, ts = mines.entry(test, t), mines.entry(test, src)
    lo, hi = build.FIXED_BANKS
    at = test.u24(te + 6)
    if test.u24(te) != test.u24(ts) or test.u24(te + 3) != test.u24(ts + 3) or test.u24(ts + 3) != base.u24(
            mines.entry(base, impact_style.GRAPHICS_SOURCE) + 3):
        problems.append(f"ROM de teste: tileset {t:02X} (cratera) não aponta a tabela e os gráficos do {src:02X}")
    try:
        got, size = decompress(test.data, snes_to_pc(at)) if lo <= at <= hi else (None, 0)
    except (CompressionError, IndexError, ValueError):
        got, size = None, 0
    if got != pal:
        problems.append(f"ROM de teste: tileset {t:02X} (cratera): paleta em ${at:06X} fora do alocador fixo ou diferente da do estilo")
    if not written:
        allowed = set(range(snes_to_pc(te), snes_to_pc(te) + 9)) | set(range(snes_to_pc(at), snes_to_pc(at) + size))
        extra = [i for i in range(len(built.data)) if built.data[i] != test.data[i] and i not in allowed]
        if extra:
            problems.append(f"ROM de teste: {len(extra)} bytes diferentes da ROM do jogo fora da entrada {t:02X} e da paleta "
                            f"(o primeiro em ${pc_to_snes(extra[0]):06X})")
    if not problems:
        print(f"impact crater (specs/20d): estilo no tileset {t:02X} (tabela, gráficos e peças da rocha da mina, "
              f"{src:02X}), paleta própria em ${at:06X} na ROM de teste ({size} bytes); rocha na matiz "
              f"{impact_style.ROCK_HUE}/saturação {impact_style.ROCK_SAT} do Prime (texturas quentes: cratera "
              f"{crater['kinds']['warm']}/{crater['textures']}, mina {mine['kinds']['warm']}/{mine['textures']}), phazon = o da mina "
              f"(matiz {blue[2]:.0f}; azul do Prime {blue[0]:.0f} na cratera, {blue[1]:.0f} na mina); ROM do jogo: "
              + ("entrada escrita" if written else f"entrada {t:02X} vanilla (sem sala da cratera)")
              + f"; {len(users)} salas fora da cratera no {t:02X}")
    return problems


# specs/19c (epic 19, rule 3 of "Como a Mines encaixa", user decision 3a): the Grapple Beam (the Mines' Storage Depot B, specs/19f)
# must open nothing: no grapple block (block type $E) in any of our rooms' levels and no enemy of ours Samus latches onto with it
# (the species header's grapple reaction, +$1A: Enemy_GrappleReact_SamusLatchesOn $8005, ..NoInvinc $8014, ..Paralyze $8019 of its
# bank; GrappleBeam's enemy check, sm_a0.c:2339, treats any other value as no latch)
GRAPPLE_BLOCK = 0xE
GRAPPLE_LATCH = (0x8005, 0x8014, 0x8019)


def check_no_grapple_locks(rom, base, manifest) -> list[str]:
    """specs/19c, built ROM: no grapple block in any room of ours (the levels the build compresses: RoomDef.level) and no species
    in our rooms' enemy populations (every state, manifest) whose grapple reaction latches Samus on (read from the built ROM's
    headers: our species copies too). Prints the count of rooms and species scanned."""
    problems, species = [], {}
    for key, v in sorted(manifest.items()):
        if not isinstance(v, dict) or "header" not in v:
            continue
        for st in read_room(rom, 0x8F0000 | v["header"] & 0xFFFF).states:
            p = 0xA10000 | st.enemy_pop if st.enemy_pop else 0
            while p and rom.u16(p) != 0xFFFF:
                species.setdefault(rom.u16(p), set()).add(key)
                p += 16
    for sp, keys in sorted(species.items()):
        if rom.u16(0xA00000 | sp + 0x1A) in GRAPPLE_LATCH:
            problems.append(f"espécie ${sp:04X} (nas salas {sorted(keys)[:3]}): a Samus se agarra nela com o Grapple "
                            f"(reação ${rom.u16(0xA00000 | sp + 0x1A):04X})")
    rooms = all_rooms_flat()
    for r in rooms:
        l1, _ = r.level().build_blocks()
        hits = [i for i, w in enumerate(l1) if w >> 12 == GRAPPLE_BLOCK]
        if hits:
            wb = r.width * 16
            problems.append(f"{r.key}: bloco de gancho em {[(i % wb, i // wb) for i in hits[:3]]}")
    if not problems:
        print(f"grapple (specs/19c): nenhum bloco de gancho (tipo ${GRAPPLE_BLOCK:X}) nas {len(rooms)} salas do jogo e nenhuma "
              f"das {len(species)} espécies delas agarrável (reação {'/'.join(f'${x:04X}' for x in GRAPPLE_LATCH)}): o item só "
              "soma à porcentagem e ao HUD")
    return problems


# specs/18c (epic 18, rule 3 of "Como Phendrana encaixa"): the Super Missile (Phendrana's Observatory, specs/18l) must open nothing
# in the game: no green door (research/sm_room_format.md section 5: C872 C878 C87E C884, argument = door bit) in any state of our
# rooms, and no super missile block (shot block, type C, with a BTS whose PLM of the table $94:9EA6 has the setup $84:CF67,
# PlmSetup_D08C_SuperMissileBlockRespawning: read from the bytes, $0A and $0B) in any of our rooms' levels.
GREEN_DOOR_PLM = (0xC872, 0xC878, 0xC87E, 0xC884)
SHOT_BLOCK_PLMS = 0x949EA6
SUPER_BLOCK_SETUP = 0xCF67


def check_no_super_locks(rom, base, manifest) -> list[str]:
    """specs/18c, built ROM: no green door PLM in any state of our rooms (manifest), no super missile block in any room of ours
    (the levels the build compresses: RoomDef.level). Prints the count of rooms scanned."""
    problems = []
    super_bts = {b for b in range(0x80) if base.u16(0x840000 | base.u16(SHOT_BLOCK_PLMS + 2 * b)) == SUPER_BLOCK_SETUP}
    if not super_bts:
        problems.append(f"super missile: nenhum BTS da tabela ${SHOT_BLOCK_PLMS:06X} com o setup ${SUPER_BLOCK_SETUP:04X}")
    for key, v in sorted(manifest.items()):
        if not isinstance(v, dict):
            continue
        for st in v.get("states", []):
            green = [pl for pl in room_plms(rom, st) if pl[0] in GREEN_DOOR_PLM]
            if green:
                problems.append(f"{key}: porta verde (Super Missile) no estado ${st & 0xFFFF:04X}: {green[:2]}")
    rooms = all_rooms_flat()
    for r in rooms:
        l1, bts = r.level().build_blocks()
        hits = [i for i, (w, b) in enumerate(zip(l1, bts)) if w >> 12 == reach.SHOT_BLOCK and b in super_bts]
        if hits:
            wb = r.width * 16
            problems.append(f"{r.key}: bloco de Super Missile em {[(i % wb, i // wb) for i in hits[:3]]}")
    if not problems:
        print(f"super missile (specs/18c): nenhuma porta verde nem bloco de super (BTS "
              f"{' '.join(f'${b:02X}' for b in sorted(super_bts))}) nas {len(rooms)} salas do jogo: o item só soma munição e dano")
    return problems


def check_chozo_locks_mapped() -> list[str]:
    """specs/12j: every Prime lock (chozo_rooms.DOCK_LOCKS) on a link between two built Chozo rooms has its SM mechanism in
    chozo_rooms.GATES / ONE_WAY_DOORS, on the dock's side: missile = a red cap (MISSILE capped on that room's side); key (a
    coloured door) = a beam cap (an item of tallon_rooms.BEAM_LOCKS capped there); morph = MORPH among the gate's items;
    one_way = the one-way door. "event" (a fight's door lock: ghosts, bosses) is out until the bosses (epic decision 3);
    specs/12k: an event lock that is a puzzle (chozo_rooms.EVENT_LOCKS: the Energy Core's bomb slots) has its items in the
    link's gate. Before this the rounds alone caught a forgotten lock only when it changed a round (a forgotten wave door
    between two rooms of the same round passed). Prints a line with the count of locks mapped."""
    built = {r.key: r for r in CHOZO.rooms}
    problems, mapped = [], 0
    for (key, to), kinds in sorted(chozo_rooms.DOCK_LOCKS.items()):
        if key not in built or not any(d.to_room == to for d in built[key].doors):
            continue
        gate = chozo_rooms.GATES.get(frozenset({key, to}))
        items = gate.items if gate else frozenset()
        capped = gate.capped if gate else ()
        # specs/12l: the cap item(s) on this dock's side (one per side where SIDE_CAPS splits the link)
        side = ({chozo_rooms.SIDE_CAPS[(key, to)]} if (key, to) in chozo_rooms.SIDE_CAPS
                else {i for i in items if i in tallon_rooms.LOCK_OF}) if key in capped else set()
        puzzle = chozo_rooms.EVENT_LOCKS.get((key, to))
        # specs/14c: a boss fight's door lock, mapped now; and an arena's room (tools/chozo/bosses.py ARENAS) must map its
        # Prime door lock (a fight built without its lock would leave the door open)
        boss = (key, to) in chozo_rooms.BOSS_DOORS or chozo_bosses.arena_of(key) is not None
        door = next(d for d in built[key].doors if d.to_room == to)
        for kind in sorted(kinds - ({chozo_rooms.EVENT} if puzzle is None and not boss else set())):
            ok = {chozo_rooms.MISSILE: tallon_rooms.MISSILE in side,
                  chozo_rooms.KEY: side == {chozo_rooms.KEY_BEAM.get((key, to))},   # specs/12l: Prime's beam
                  chozo_rooms.MORPH: tallon_rooms.MORPH in items,
                  chozo_rooms.EVENT: (puzzle is not None and puzzle <= items)
                  or (boss and door.lock == "boss" and chozo_rooms.BOSS_GATE in door.gate
                      and chozo_bosses.arena_of(key) is not None),
                  chozo_rooms.ONE_WAY: (key, to) in chozo_rooms.ONE_WAY_DOORS}[kind]
            mapped += ok
            if not ok:
                problems.append(f"chozo: a doca {key} -> {to} tem a trava {kind} do Prime e nenhum mecanismo SM dela do "
                                f"lado de {key} (GATES: {sorted(items) or 'nenhuma'}; tampa {sorted(side) or 'nenhuma'}"
                                + (f", o Prime: {chozo_rooms.KEY_BEAM.get((key, to))}" if kind == chozo_rooms.KEY else "") + ")")
    keyless = sorted(set(chozo_rooms.KEY_BEAM) ^ {k for k, v in chozo_rooms.DOCK_LOCKS.items() if chozo_rooms.KEY in v})
    if keyless:
        problems.append(f"chozo: KEY_BEAM e as travas key do Prime diferem em {keyless}")
    stray = sorted(k for k in chozo_rooms.EVENT_LOCKS.keys() | chozo_rooms.BOSS_DOORS
                   if chozo_rooms.EVENT not in chozo_rooms.DOCK_LOCKS.get(k, ()))
    if stray:
        problems.append(f"chozo: EVENT_LOCKS/BOSS_DOORS com docas sem a trava event do Prime: {stray}")
    if not problems:
        print(f"chozo (specs/12j, 12k, 12l): {mapped} travas do Prime nas ligações construídas, cada uma com o seu mecanismo SM "
              f"(key: a tampa do feixe do Prime, KEY_BEAM, por lado; event: os quebra-cabeças de EVENT_LOCKS e, specs/14c, as portas "
              f"de chefe de BOSS_DOORS mapeados, a da 14c e a da 14d; os Chozo Ghosts fora, 14e)")
    return problems


def check_magmoor_locks_mapped() -> list[str]:
    """specs/17f (the Chozo's check_chozo_locks_mapped, from the Magmoor's first region): every Prime lock
    (magmoor_rooms.DOCK_LOCKS) on a link between two built Magmoor rooms has its SM mechanism in magmoor_rooms.GATES on the
    dock's side: missile = a red cap there (the door's lock "missile", MISSILE in its gate); specs/17h: morph = the Morph Ball
    in the gate, that side behind the geometry (DoorLink.ledge). specs/17i: key (a coloured door) = the cap of Prime's beam
    (magmoor_rooms.KEY_BEAM, or its SM beam in magmoor_rooms.SM_BEAM: the Plasma Processing's plasma door is an ice door,
    epic 17 technical decision 5; SM_BEAM only remaps Prime's plasma docks, and every plasma dock is remapped: no plasma door
    in the Magmoor) on that side, the beam in the gate. A gate on a link with no Prime lock is a problem, unless (specs/17i)
    it is geometry only (no cap) on a side whose room has the Prime feature behind it (magmoor_rooms.FEATURE_GEOMETRY: the
    Spider Ball tracks and grapple points = the Space Jump, the bomb slots = the Morph Ball and the Bombs). And the lava: a
    built room has lava (RoomDef.lava) only if Prime's room has it (FEATURES "lava"; the user's decision 4: lava in Prime's
    pits and lakes). Prints a line with the count of locks mapped."""
    built = {r.key: r for r in MAGMOOR.rooms}
    problems, mapped = [], 0
    for r in MAGMOOR.rooms:
        if r.lava is not None and "lava" not in magmoor_rooms.FEATURES.get(r.key, ()):
            problems.append(f"magmoor: {r.key} com lava, a sala do Prime não tem")
    for (key, to), kinds in sorted(magmoor_rooms.DOCK_LOCKS.items()):
        if key not in built or not any(d.to_room == to for d in built[key].doors):
            continue
        door = next(d for d in built[key].doors if d.to_room == to)
        for kind in sorted(kinds):
            # specs/17h: morph (Prime's Morph Ball door) = the Morph Ball among the gate's items, that side behind the geometry
            # (DoorLink.ledge: a 1-row tunnel; the Warrior Shrine's, shut by a power bomb block)
            beam = magmoor_rooms.SM_BEAM.get((key, to), magmoor_rooms.KEY_BEAM.get((key, to)))   # specs/17i
            ok = {magmoor_rooms.MISSILE: door.lock == "missile" and tallon_rooms.MISSILE in door.gate,
                  magmoor_rooms.MORPH: door.ledge and tallon_rooms.MORPH in door.gate,
                  magmoor_rooms.KEY: beam is not None and door.lock == tallon_rooms.LOCK_OF.get(beam) and beam in door.gate,
                  }.get(kind, False)
            mapped += ok
            if not ok:
                problems.append(f"magmoor: a doca {key} -> {to} tem a trava {kind} do Prime e nenhum mecanismo SM dela do "
                                f"lado de {key} (tampa {door.lock or 'nenhuma'}, trava {sorted(door.gate) or 'nenhuma'})")
    keyless = sorted(set(magmoor_rooms.KEY_BEAM) ^ {k for k, v in magmoor_rooms.DOCK_LOCKS.items() if magmoor_rooms.KEY in v})
    if keyless:
        problems.append(f"magmoor: KEY_BEAM e as travas key do Prime diferem em {keyless}")
    plasma = {k for k, b in magmoor_rooms.KEY_BEAM.items() if b == tallon_rooms.PLASMA}
    if set(magmoor_rooms.SM_BEAM) != plasma or tallon_rooms.PLASMA in magmoor_rooms.SM_BEAM.values():
        problems.append(f"magmoor: SM_BEAM {magmoor_rooms.SM_BEAM} deve trocar exatamente as portas de plasma do Prime "
                        f"{sorted(plasma)} por outro feixe (specs/17i)")

    def feature_gate(k, g) -> bool:   # specs/17i: geometry only, on a side whose room has the Prime feature behind it
        allowed = frozenset().union(*[magmoor_rooms.FEATURE_GEOMETRY.get(f, frozenset())
                                      for r in g.ledge for f in magmoor_rooms.FEATURES.get(r, ())])
        return not g.capped and bool(g.ledge) and g.items <= allowed
    stray = sorted(k for k, g in magmoor_rooms.GATES.items()
                   if not any(magmoor_rooms.DOCK_LOCKS.get((a, b)) for a in k for b in k if a != b) and not feature_gate(k, g))
    if stray:
        problems.append(f"magmoor: GATES com ligações sem trava do Prime: {[sorted(k) for k in stray]}")
    if not problems:
        geo = sorted("-".join(sorted(k)) for k, g in magmoor_rooms.GATES.items()
                     if not any(magmoor_rooms.DOCK_LOCKS.get((a, b)) for a in k for b in k if a != b))
        print(f"magmoor (specs/17f, 17h, 17i): {mapped} trava(s) do Prime nas ligações construídas, cada uma com o seu mecanismo SM "
              f"(os escudos de míssil das Save Stations A e B = portas vermelhas; a porta de Morph Ball da Warrior "
              f"Shrine = túnel de Morph com bloco de Power Bomb; as portas key = tampas do feixe do Prime, a de plasma da Plasma "
              f"Processing de gelo, SM_BEAM); travas de geometria pelas features do Prime: {len(geo)}; salas quentes: "
              f"{sum(r.heat for r in MAGMOOR.rooms)} construídas, toda porta para elas com a Varia; lava em "
              f"{sum(r.lava is not None for r in MAGMOOR.rooms)} salas, todas com lava no Prime")
    return problems


EPIC_PHENDRANA_BOSS_ROOMS = {"phendrana_chapel_of_the_elders": "18h", "phendrana_quarantine_cave": "18k"}   # epic 18, decision 4
# specs/18i: Prime's save rooms (P4 Save Station B, P17 A, P33 D, P45 C) and map room (P22) of Phendrana (epic 18, "Phendrana no
# Prime"): the only rooms with a save / map station
EPIC_PHENDRANA_SAVES = ("phendrana_save_station_b", "phendrana_save_station_a", "phendrana_save_station_d",
                        "phendrana_save_station_c")
EPIC_PHENDRANA_MAP = "phendrana_map_station"
EPIC_PHENDRANA_SUPER = "phendrana_observatory"   # specs/18l: Prime's Super Missile (P30, the item table of epic 18)
# specs/18m: the epic's user decision 5 (no cold; water only where the room is deep): the Gravity Chamber flooded, the whole room;
# the other 9 rooms with Prime's water have dry lakes
EPIC_PHENDRANA_FLOODED = frozenset({"phendrana_gravity_chamber"})


def check_phendrana_locks_mapped() -> list[str]:
    """specs/18f (the Magmoor's check_magmoor_locks_mapped, from Phendrana's first region): every Prime lock
    (phendrana_rooms.DOCK_LOCKS) on a link between two built Phendrana rooms has its SM mechanism on the dock's side: missile = a
    red cap there; morph = the Morph Ball in the gate, that side behind the geometry; key = the cap of Prime's beam
    (phendrana_rooms.KEY_BEAM; a door any beam opens, ANY_BEAM: no cap), the beam in the gate; event = a boss fight's door lock
    (phendrana_rooms.BOSS_DOORS) once the room's arena is built (a boss door; before, it waits for its child, named in the line),
    any other event lock is an event layer's (out, the epic). A gate on a link with no Prime lock is a problem, unless it is
    geometry only (no cap) on a side whose room has the Prime feature behind it (phendrana_rooms.FEATURE_GEOMETRY); an item behind
    the Space Jump (Item.needs) only in a room whose Prime feature gates it (a Spider Ball track, a grapple point, a half-pipe).
    And the epic's look rules on every built room: falling snow exactly where Prime snows (SNOW_ROOMS, user decision 6), no water
    but the Gravity Chamber's (user decision 5), no heat nor lava (decision 5: no cold; Phendrana has neither). Prints a line."""
    built = PHENDRANA.by_key()
    problems, mapped, waiting, out = [], 0, [], 0
    for (key, to), kinds in sorted(phendrana_rooms.DOCK_LOCKS.items()):
        if key not in built or not any(d.to_room == to for d in built[key].doors):
            continue
        door = next(d for d in built[key].doors if d.to_room == to)
        for kind in sorted(kinds):
            if kind == phendrana_rooms.EVENT:
                if (key, to) not in phendrana_rooms.BOSS_DOORS:
                    out += 1
                    continue
                if chozo_bosses.arena_of(key) is None:
                    waiting.append(f"{key.removeprefix('phendrana_')} ({phendrana_rooms.BOSS_DOORS[(key, to)]})")
                    continue
                ok = door.lock == "boss" and chozo_rooms.BOSS_GATE in door.gate
            else:
                beam = phendrana_rooms.KEY_BEAM.get((key, to))
                # specs/18h: a boss door (lock "boss") keeps Prime's key cap for its arena's dead state (dead_lock)
                cap = door.dead_lock if door.lock == "boss" else door.lock
                ok = {phendrana_rooms.MISSILE: door.lock == "missile" and tallon_rooms.MISSILE in door.gate,
                      phendrana_rooms.MORPH: door.ledge and tallon_rooms.MORPH in door.gate,
                      phendrana_rooms.KEY: (cap is None if beam == phendrana_rooms.ANY_BEAM else
                                            beam is not None and cap == tallon_rooms.LOCK_OF.get(beam) and beam in door.gate),
                      }.get(kind, False)
            mapped += ok
            if not ok:
                problems.append(f"phendrana: a doca {key} -> {to} tem a trava {kind} do Prime e nenhum mecanismo SM dela do "
                                f"lado de {key} (tampa {door.lock or 'nenhuma'}, trava {sorted(door.gate) or 'nenhuma'})")
    keyless = sorted(set(phendrana_rooms.KEY_BEAM) ^ {k for k, v in phendrana_rooms.DOCK_LOCKS.items() if phendrana_rooms.KEY in v})
    if keyless:
        problems.append(f"phendrana: KEY_BEAM e as travas key do Prime diferem em {keyless}")
    stray = sorted(k for k in phendrana_rooms.BOSS_DOORS if phendrana_rooms.EVENT not in phendrana_rooms.DOCK_LOCKS.get(k, ()))
    if stray:
        problems.append(f"phendrana: BOSS_DOORS com docas sem a trava event do Prime: {stray}")
    # the epic's user decision 4: the Sheegoth's chapel and the Thardus' cave are the bosses' rooms; every event dock out of them
    # is a boss door (none counted as an event layer's)
    boss_docks = {k for k, v in phendrana_rooms.DOCK_LOCKS.items()
                  if k[0] in EPIC_PHENDRANA_BOSS_ROOMS and phendrana_rooms.EVENT in v}
    if set(phendrana_rooms.BOSS_DOORS) != boss_docks or {k[0]: c for k, c in phendrana_rooms.BOSS_DOORS.items()} != \
            EPIC_PHENDRANA_BOSS_ROOMS:
        problems.append(f"phendrana: BOSS_DOORS {sorted(phendrana_rooms.BOSS_DOORS)}, as docas de evento das salas dos chefes "
                        f"(decisão 4 do épico) são {sorted(boss_docks)}")

    def allowed(rooms) -> frozenset:
        return frozenset().union(*[phendrana_rooms.FEATURE_GEOMETRY.get(f, frozenset())
                                   for r in rooms for f in phendrana_rooms.FEATURES.get(r, ())])
    stray = sorted(k for k, g in phendrana_rooms.GATES.items()
                   if not any(phendrana_rooms.DOCK_LOCKS.get((a, b)) for a in k for b in k if a != b)
                   and not (not g.capped and g.ledge and g.items <= allowed(g.ledge)))
    if stray:
        problems.append(f"phendrana: GATES com ligações sem trava do Prime: {[sorted(k) for k in stray]}")
    ledges, niches = 0, 0
    for n, it in phendrana_items.placed(set(built)):
        if tallon_rooms.SPACE_JUMP in it.needs:
            ledges += 1
            if tallon_rooms.SPACE_JUMP not in allowed([it.room]):
                problems.append(f"phendrana: item {n} em {it.room} numa borda de Space Jump, a sala do Prime não tem trilho de "
                                f"Spider, gancho nem meio-tubo")
        # specs/18i: an item behind other geometry (the Morph Ball and the Bombs: a bomb block) only where Prime's feature gates
        # it (a bomb slot); an item behind a beam cap in the room (RoomDef.caps) only where Prime's ice melts to that beam alone
        # (PLASMA_ICE: the plasma), and every built room with that ice and a Phendrana item has it behind the plasma cap
        geo = (it.needs & tallon_rooms.GEOMETRY) - {tallon_rooms.SPACE_JUMP}
        if geo and not geo <= allowed([it.room]):
            problems.append(f"phendrana: item {n} em {it.room} atrás de {sorted(geo)}, a sala do Prime não tem a feature que "
                            f"pede isso ({sorted(allowed([it.room]))})")
        beams = it.needs - tallon_rooms.GEOMETRY
        if beams:
            niches += 1
            if beams != {tallon_rooms.PLASMA} or it.room not in phendrana_rooms.PLASMA_ICE \
                    or tallon_rooms.PLASMA not in room_cap_items(built[it.room]):
                problems.append(f"phendrana: item {n} em {it.room} atrás de {sorted(beams)}: só o gelo de plasma do Prime "
                                f"(PLASMA_ICE) vira um nicho com tampa de plasma na sala")
        elif it.room in phendrana_rooms.PLASMA_ICE:
            problems.append(f"phendrana: item {n} em {it.room}, sala com o gelo de plasma do Prime, sem a tampa de plasma "
                            f"(needs {sorted(it.needs) or 'nada'})")
        if tallon_rooms.SPACE_JUMP not in it.needs:   # an item with no Space Jump in its needs is picked up on foot (with
            # the foot geometry and, specs/18i, its room's caps open) from some door
            r = built[it.room]
            full = frozenset(FOOT_GEOMETRY | ({tallon_rooms.GRAVITY} if r.water else set()) | room_cap_items(r))   # 18i
            if not any(it.spot in tallon_room_reach(r, i, full)[1] for i in range(len(r.doors))):
                problems.append(f"phendrana: item {n} em {it.room} {it.spot} não se pega a pé de nenhuma porta: falta o Space "
                                f"Jump no seu needs")
    # specs/18j: a Morph Ball door of Prime (a "morph" dock, its side behind a Morph Ball tunnel: DoorLink.ledge) shuts something
    # in its own room: from that door's entry, with every foot geometry item, she gets to more places than without the Morph
    # Ball (reach_on_foot checks the tunnel from the room's other entries; a room whose only door is that one, the Quarantine
    # Monitor, has none: without this its tunnel could be gone)
    morph_doors = 0
    for (key, to), kinds in sorted(phendrana_rooms.DOCK_LOCKS.items()):
        if phendrana_rooms.MORPH not in kinds or key not in built or not any(d.to_room == to for d in built[key].doors):
            continue
        r = built[key]
        i = next(i for i, d in enumerate(r.doors) if d.to_room == to)
        morph_doors += 1
        full = frozenset(FOOT_GEOMETRY)
        # specs/18m: and every other foot geometry item of the door's gate (the Security Cave's Power Bomb: the mutation V11 of
        # 18m showed a room whose only door is that one could lose its power bomb block)
        for item in sorted({tallon_rooms.MORPH} | (r.doors[i].gate & FOOT_GEOMETRY)):
            if len(tallon_room_reach(r, i, full - {item})[1]) >= len(tallon_room_reach(r, i, full)[1]):
                problems.append(f"phendrana: a porta de Morph Ball {key} -> {to} (doca morph do Prime) não fecha nada na sala "
                                f"sem {item}: da entrada dela, sem {item}, a Samus chega aos mesmos lugares (falta o túnel ou o "
                                f"bloco)")
    stray = sorted(r.key for r in PHENDRANA.rooms if r.caps and (r.key not in phendrana_rooms.PLASMA_ICE or any(
        beam != tallon_rooms.PLASMA for *_, beam in r.caps)))
    if stray:
        problems.append(f"phendrana: tampas de feixe dentro de sala fora do gelo de plasma do Prime: {stray}")
    # specs/18i: the save and map stations exactly in Prime's save rooms and map room (the built ones; epic 18, "4 save stations
    # e 1 map station")
    saves = sorted(r.key for r in PHENDRANA.rooms if r.save_station)
    maps = sorted(r.key for r in PHENDRANA.rooms if r.map_station)
    if saves != sorted(k for k in EPIC_PHENDRANA_SAVES if k in built) or maps != sorted(
            k for k in (EPIC_PHENDRANA_MAP,) if k in built):
        problems.append(f"phendrana: save stations {saves} e map station {maps}, as do Prime construídas são "
                        f"{sorted(k for k in EPIC_PHENDRANA_SAVES if k in built)} e "
                        f"{[k for k in (EPIC_PHENDRANA_MAP,) if k in built]}")
    for r in PHENDRANA.rooms:
        if bool(r.snow) != (r.key in phendrana_rooms.SNOW_ROOMS):
            problems.append(f"phendrana: {r.key} {'com' if r.snow else 'sem'} neve, o Prime {'não ' if r.snow else ''}neva nela")
        # specs/18m: the epic's user decision 5: the Gravity Chamber flooded (the whole room), no other room
        if r.water != (r.key in EPIC_PHENDRANA_FLOODED):
            problems.append(f"phendrana: {r.key} {'inundada' if r.water else 'seca'} (decisão 5 do épico: inundada só a "
                            f"Gravity Chamber, a sala inteira)")
        if r.heat or r.lava is not None:
            problems.append(f"phendrana: {r.key} com calor ou lava (o Prime não tem)")
    if phendrana_rooms.FLOODED != EPIC_PHENDRANA_FLOODED or not phendrana_rooms.FLOODED <= phendrana_rooms.WATER_ROOMS:
        problems.append(f"phendrana: FLOODED {sorted(phendrana_rooms.FLOODED)}; a decisão 5 do épico inunda só "
                        f"{sorted(EPIC_PHENDRANA_FLOODED)}, uma sala com a água do Prime (WATER_ROOMS)")
    if not problems:
        geo = sorted("-".join(sorted(x.removeprefix("phendrana_") for x in k)) for k, g in phendrana_rooms.GATES.items()
                     if not any(phendrana_rooms.DOCK_LOCKS.get((a, b)) for a in k for b in k if a != b))
        print(f"phendrana (specs/18f): {mapped} trava(s) do Prime nas ligações construídas, cada uma com o seu mecanismo SM (as "
              f"portas key = tampas do feixe do Prime); esperando o chefe: {', '.join(waiting) or 'nenhuma'}; travas de evento "
              f"fora (camadas de evento do Prime): {out}; travas de geometria pelas features do Prime: {', '.join(geo) or 'nenhuma'}; "
              f"itens em bordas de Space Jump (trilhos de Spider): {ledges}; specs/18i: itens em nichos de gelo de plasma: "
              f"{niches}; specs/18j: portas de Morph Ball do Prime atrás de túnel (de cada uma, sem a Morph, menos lugares): "
              f"{morph_doors}; save stations: {', '.join(k.removeprefix('phendrana_') for k in saves)}; map station: "
              f"{', '.join(k.removeprefix('phendrana_') for k in maps) or 'nenhuma'}; neve em "
              f"{sum(bool(r.snow) for r in PHENDRANA.rooms)} das {len(PHENDRANA.rooms)} salas construídas, todas onde neva no "
              f"Prime; inundada: {', '.join(r.key.removeprefix('phendrana_') for r in PHENDRANA.rooms if r.water) or 'nenhuma'} "
              f"(decisão 5: só a Gravity Chamber), nenhuma quente ou com lava")
    return problems


# specs/19f (epic 19, user decision 4): the rooms of the Mines' two bosses (their arenas: 19h the Phazon Elite, 19k the Omega Pirate)
EPIC_MINES_BOSS_ROOMS = {"mines_elite_research": "19h", "mines_elite_quarters": "19k"}
EPIC_MINES_SAVES = ("mines_save_station_a", "mines_save_station_b", "mines_save_station_c")   # Prime's save rooms (load stations 1-3)
EPIC_MINES_MAP = "mines_map_station"   # specs/19i: Prime's map room of the Mines (P23)


def check_mines_locks_mapped() -> list[str]:
    """specs/19f (Phendrana's check_phendrana_locks_mapped, from the Mines' first region): every Prime lock (mines_rooms.DOCK_LOCKS)
    on a link between two built Mines rooms has its SM mechanism on the dock's side: key = the cap of Prime's beam (KEY_BEAM; a
    boss door keeps it as its dead_lock), the beam in the gate; event = a boss fight's door lock (mines_rooms.BOSS_DOORS, the docks
    of the rooms of decision 4) once the room's arena is built (before, it waits for its child, named in the line), any other event
    lock is an event layer's (out, the epic). A gate on a link with no Prime lock is a problem; a gate's geometry on a side only
    where the room has the Prime feature behind it (mines_rooms.FEATURE_GEOMETRY: a Spider Ball track, a grapple point or a
    half-pipe = the Space Jump; the Morph Ball door inside the room = the Morph Ball; what only the Power Bomb breaks, PB_ONLY = the
    Morph Ball and the Power Bomb); an item behind the Space Jump only in a room with a track, a grapple point or a half-pipe, an
    item behind other geometry only where the feature gates it, an item with no Space Jump in its needs picked up on foot. The power
    bomb blocks only in rooms where Prime has something only the Power Bomb breaks (PB_ONLY), and every built such room has them
    but PB_NOTHING's. The Morph Ball door of Prime inside a room (FEATURES morph_door: the Waste Disposal's) is a ledge door behind
    the Morph Ball, which shuts something there. The save stations exactly in Prime's save rooms; no heat, snow, water nor lava in
    the Mines (the epic's technical decision 2). Prints a line."""
    built = MINES.by_key()
    problems, mapped, waiting, out = [], 0, [], 0
    for (key, to), kinds in sorted(mines_rooms.DOCK_LOCKS.items()):
        if key not in built or not any(d.to_room == to for d in built[key].doors):
            continue
        door = next(d for d in built[key].doors if d.to_room == to)
        for kind in sorted(kinds):
            if kind == mines_rooms.EVENT:
                if (key, to) not in mines_rooms.BOSS_DOORS:
                    out += 1
                    continue
                if chozo_bosses.arena_of(key) is None:
                    waiting.append(f"{key.removeprefix('mines_')} ({mines_rooms.BOSS_DOORS[(key, to)]})")
                    continue
                ok = door.lock == "boss" and chozo_rooms.BOSS_GATE in door.gate
            else:
                beam = mines_rooms.KEY_BEAM.get((key, to))
                cap = door.dead_lock if door.lock == "boss" else door.lock
                ok = kind == mines_rooms.KEY and beam is not None and cap == tallon_rooms.LOCK_OF.get(beam) and beam in door.gate
            mapped += ok
            if not ok:
                problems.append(f"mines: a doca {key} -> {to} tem a trava {kind} do Prime e nenhum mecanismo SM dela do lado de "
                                f"{key} (tampa {door.lock or 'nenhuma'}, trava {sorted(door.gate) or 'nenhuma'})")
    keyless = sorted(set(mines_rooms.KEY_BEAM) ^ {k for k, v in mines_rooms.DOCK_LOCKS.items() if mines_rooms.KEY in v})
    if keyless:
        problems.append(f"mines: KEY_BEAM e as travas key do Prime diferem em {keyless}")
    boss_docks = {k for k, v in mines_rooms.DOCK_LOCKS.items() if k[0] in EPIC_MINES_BOSS_ROOMS and mines_rooms.EVENT in v}
    if set(mines_rooms.BOSS_DOORS) != boss_docks or any(c != EPIC_MINES_BOSS_ROOMS[k[0]] for k, c in
                                                         mines_rooms.BOSS_DOORS.items() if k[0] in EPIC_MINES_BOSS_ROOMS):
        problems.append(f"mines: BOSS_DOORS {sorted(mines_rooms.BOSS_DOORS)}, as docas de evento das salas dos chefes (decisão 4 "
                        f"do épico) são {sorted(boss_docks)}")

    def allowed(rooms) -> frozenset:
        feats = [f for r in rooms for f in mines_rooms.FEATURES.get(r, ())] + ["pb_only" for r in rooms if r in mines_rooms.PB_ONLY]
        return frozenset().union(*[mines_rooms.FEATURE_GEOMETRY.get(f, frozenset()) for f in feats],
                                 *[mines_rooms.MAZES.get(r, frozenset()) for r in rooms])   # specs/19i: the Central Dynamo's maze
    for k, g in sorted(mines_rooms.GATES.items(), key=lambda kv: sorted(kv[0])):
        if not any(mines_rooms.DOCK_LOCKS.get((a, b)) for a in k for b in k if a != b):
            problems.append(f"mines: GATES com ligação sem trava do Prime: {sorted(k)}")
        geo = g.items & tallon_rooms.GEOMETRY
        for side in g.ledge:
            if not geo <= allowed([side]):
                problems.append(f"mines: trava {sorted(k)} com {sorted(geo)} do lado de {side}, a sala do Prime não tem a feature "
                                f"que pede isso ({sorted(allowed([side]))})")
    ledges = 0
    for n, it in mines_items.placed(set(built)):
        if tallon_rooms.SPACE_JUMP in it.needs:
            ledges += 1
            if tallon_rooms.SPACE_JUMP not in allowed([it.room]):
                problems.append(f"mines: item {n} em {it.room} numa borda de Space Jump, a sala do Prime não tem trilho de Spider, "
                                f"gancho nem meio-tubo")
        geo = (it.needs & tallon_rooms.GEOMETRY) - {tallon_rooms.SPACE_JUMP}
        if geo and not geo <= allowed([it.room]):
            problems.append(f"mines: item {n} em {it.room} atrás de {sorted(geo)}, a sala do Prime não tem a feature que pede "
                            f"isso ({sorted(allowed([it.room]))})")
        if it.needs - tallon_rooms.GEOMETRY:
            problems.append(f"mines: item {n} em {it.room} atrás de {sorted(it.needs - tallon_rooms.GEOMETRY)} (nenhum gelo de "
                            f"feixe na Mines)")
        if tallon_rooms.SPACE_JUMP not in it.needs:
            r = built[it.room]
            full = frozenset(FOOT_GEOMETRY | room_cap_items(r))
            if not any(it.spot in tallon_room_reach(r, i, full)[1] for i in range(len(r.doors))):
                problems.append(f"mines: item {n} em {it.room} {it.spot} não se pega a pé de nenhuma porta: falta o Space Jump "
                                f"no seu needs")
    # what only the Power Bomb breaks (PB_ONLY): power bomb blocks there and only there (but PB_NOTHING's, which gate nothing)
    pb_rooms = set()
    for r in MINES.rooms:
        l1, bts = r.level().build_blocks()
        if any(reach.is_power_bomb_block(w >> 12, b) for w, b in zip(l1, bts)):
            pb_rooms.add(r.key)
    want_pb = {k for k in mines_rooms.PB_ONLY if k in built} - mines_rooms.PB_NOTHING
    if pb_rooms != want_pb or not mines_rooms.PB_NOTHING <= set(mines_rooms.PB_ONLY):
        problems.append(f"mines: blocos de Power Bomb em {sorted(pb_rooms)}; o Prime tem o que só a Power Bomb quebra em "
                        f"{sorted(want_pb)} (fora PB_NOTHING {sorted(mines_rooms.PB_NOTHING)})")
    # the Morph Ball door inside a room (FEATURES morph_door): a ledge door behind the Morph Ball whose tunnel shuts something
    morph_doors = 0
    for r in MINES.rooms:
        if "morph_door" not in mines_rooms.FEATURES.get(r.key, ()):
            continue
        doors = [i for i, d in enumerate(r.doors) if d.ledge and tallon_rooms.MORPH in d.gate]
        if len(doors) != 1 and len(r.doors) > 1:
            problems.append(f"mines: {r.key} tem a porta de Morph Ball do Prime (o túnel) e {len(doors)} portas atrás da Morph")
        for i in doors:
            morph_doors += 1
            full = frozenset(FOOT_GEOMETRY)
            if len(tallon_room_reach(r, i, full - {tallon_rooms.MORPH})[1]) >= len(tallon_room_reach(r, i, full)[1]):
                problems.append(f"mines: a porta de Morph Ball {r.key} -> {r.doors[i].to_room} não fecha nada na sala sem a Morph "
                                f"(falta o túnel)")
    saves = sorted(r.key for r in MINES.rooms if r.save_station)
    if saves != sorted(k for k in EPIC_MINES_SAVES if k in built):
        problems.append(f"mines: save stations {saves}, as do Prime construídas são {sorted(k for k in EPIC_MINES_SAVES if k in built)}")
    maps = sorted(r.key for r in MINES.rooms if r.map_station)   # specs/19i
    if maps != [k for k in (EPIC_MINES_MAP,) if k in built]:
        problems.append(f"mines: map station em {maps}, a do Prime é {EPIC_MINES_MAP}")
    for r in MINES.rooms:
        if r.heat or r.lava is not None or r.water or r.snow:
            problems.append(f"mines: {r.key} com calor, lava, água ou neve (decisão técnica 2 do épico: nada disso na Mines)")
    if not problems:
        print(f"mines (specs/19f): {mapped} trava(s) do Prime nas ligações construídas, cada uma com o seu mecanismo SM (as portas "
              f"key = tampas do feixe do Prime: gelo, onda, plasma); esperando o chefe: {', '.join(waiting) or 'nenhuma'}; travas de "
              f"evento fora (camadas de evento do Prime): {out}; itens em bordas de Space Jump (trilho de Spider e gancho): {ledges}; "
              f"blocos de Power Bomb onde só a Power Bomb quebra no Prime: {', '.join(k.removeprefix('mines_') for k in sorted(pb_rooms))}"
              f" (nada: {', '.join(k.removeprefix('mines_') for k in sorted(mines_rooms.PB_NOTHING & set(built)))}); portas de Morph "
              f"Ball do Prime atrás de túnel: {morph_doors}; save stations: {', '.join(k.removeprefix('mines_') for k in saves)}; "
              f"map station: {', '.join(k.removeprefix('mines_') for k in maps) or 'nenhuma'}; "
              f"nenhuma sala quente, fria, com água ou lava")
    return problems


def elevator_rooms() -> dict[str, tuple]:
    """{room key: (area, RoomDef)} of every built room."""
    return {r.key: (a, r) for a, r in all_rooms()}


# specs/12e: Prime's elevators between the Tallon and the Chozo Ruins, (Tallon room P#, Chozo room P#): read from the
# WorldTeleporter objects' destination MREA ids (epic 12, "Ponto de ligação"; scratchpad s12/tele.py). specs/17e: by world,
# ((area, P#), (area, P#)) of the upper and the lower room; the Magmoor's two read the same way (epic 17, the table "elevadores":
# the Chozo's P24 <-> the Magmoor's P0, the Tallon's P23 <-> the Magmoor's P16); Phendrana's two (epic 18, "Phendrana no Prime")
PRIME_ELEVATORS = {((0, 14), (1, 0)), ((0, 22), (1, 62)), ((0, 41), (1, 63)),
                   ((1, 24), (2, 0)), ((0, 23), (2, 16)),
                   ((4, 0), (2, 13)), ((4, 29), (2, 27)),   # specs/18e: Phendrana's P0 <-> the Magmoor's P13, P29 <-> P27 (epic 18)
                   ((0, 43), (5, 0)), ((2, 26), (5, 25))}   # specs/19e: the Tallon's P43 <-> the Mines' P0, the Magmoor's P26 <-> P25 (epic 19)


def check_elevators() -> list[str]:
    """specs/12e: the working elevators (areas.ELEVATORS; RoomDef.elevator; tools/build.py): each pair is a built Tallon room
    (area 0) going down and a built Chozo room (area CHOZO_AREA) going up, and no other room has an elevator; in each
    room's level the platform's two door blocks (type 9, BTS = its slot after the doors) sit on the platform row, the
    shaft over (up) or under (down) them is air to the room's edge row, and the exit's two door blocks (BTS = the exit
    slot) are on that edge row, right over/under the shaft. check_room already walks every room with an elevator from
    every entry, the platform included (she arrives standing on it): the platform is reached from each, and no place
    leaves her without a way back to a door or to the platform. Each pair is one of Prime's (PRIME_ELEVATORS). The
    line here gives the round of each Tallon side (tallon/rooms.py FIRST_ROUND); specs/12f: the walk rides the elevators
    (check_chozo_rounds)."""
    problems = []
    built = elevator_rooms()
    paired = set()
    for tallon_key, chozo_key in ELEVATORS:   # specs/17e: (upper room going down, lower room going up), any two areas
        paired |= {tallon_key, chozo_key}
        if (tallon_key, chozo_key) == impact_rooms.TELEPORTER and tallon_key in built and chozo_key in built:
            # specs/20e: Prime's teleporter from the Tallon's Artifact Temple (P16) to the Impact Crater's Entry Point (P0 of
            # that world): both in area 0 (the crater lives there, IMPACT_CRATER_AREA), an elevator with no area change
            (ua, ur), (la, lr) = built[tallon_key], built[chozo_key]
            if (ua.number, la.number, ur.prime, ur.name, chozo_key) != (IMPACT_CRATER_AREA, IMPACT_CRATER_AREA, 16,
                                                                        "Artifact Temple", impact_rooms.ENTRY):
                problems.append(f"teleporte da cratera {tallon_key} <-> {chozo_key}: P{ur.prime} {ur.name!r} (área {ua.number}) "
                                f"<-> P{lr.prime} (área {la.number}), esperado o Artifact Temple (P16) e {impact_rooms.ENTRY}, "
                                f"os dois na área {IMPACT_CRATER_AREA}")
        elif tallon_key in built and chozo_key in built:
            (ua, ur), (la, lr) = built[tallon_key], built[chozo_key]
            pair = ((ua.number, ur.prime), (la.number, lr.prime))
            if pair not in PRIME_ELEVATORS:
                problems.append(f"elevador {tallon_key} <-> {chozo_key}: P{ur.prime} (área {ua.number}) <-> P{lr.prime} (área "
                                f"{la.number}), o Prime liga {sorted(PRIME_ELEVATORS)}")
            if ua.number == la.number:
                problems.append(f"elevador {tallon_key} <-> {chozo_key}: os dois na área {ua.number}")
        for key, up in ((tallon_key, False), (chozo_key, True)):
            if key not in built:
                problems.append(f"elevador {tallon_key} <-> {chozo_key}: {key} fora do build")
                continue
            area, r = built[key]
            if not r.elevator:
                problems.append(f"elevador: {key} sem RoomDef.elevator")
                continue
            if r.elevator.up != up:
                problems.append(f"elevador: {key} {'sobe' if r.elevator.up else 'desce'}, esperado o contrário")
            problems += check_elevator_level(r)
    for key, (_, r) in built.items():
        if r.elevator and key not in paired:
            problems.append(f"elevador: {key} tem elevador fora de areas.ELEVATORS")
    if not problems:
        first = tallon_progress_built()[1]
        pairs = ", ".join(f"{t} (rodada {first.get(t, '?')}) <-> {c}" for t, c in ELEVATORS
                          if t.startswith("tallon_") and c.startswith("chozo_"))   # specs/17e: the Magmoor's, line 17e
        print(f"chozo (specs/12e): {pairs.count('<->')} elevadores área {TALLON.number} <-> área {CHOZO_AREA}: {pairs}; "
              f"{len(CHOZO.rooms)} salas da Chozo construídas, andadas com o Tallon pelos elevadores (linha specs/12f); ida e volta: "
              f"de toda entrada a plataforma é alcançável, nenhum lugar sem volta a ela")
    return problems


def check_elevator_level(r) -> list[str]:
    """The four door blocks of a room's elevator and the air of its shaft, in the room's level (RoomDef.level())."""
    l1, bts = r.level().build_blocks()
    wb, hb = r.width * 16, r.height * 16
    e = r.elevator
    exit_slot, pad_slot = r.elevator_slots
    problems = []
    for x, y in elevator_pad(r):
        if l1[y * wb + x] >> 12 != 9 or bts[y * wb + x] != pad_slot:
            problems.append(f"{r.key}: bloco ({x},{y}) da plataforma não é porta para a entrada {pad_slot}")
    ey = e.exit_row(hb)
    for x in (e.x, e.x + 1):
        if l1[ey * wb + x] >> 12 != 9 or bts[ey * wb + x] != exit_slot:
            problems.append(f"{r.key}: bloco ({x},{ey}) da saída do elevador não é porta para a entrada {exit_slot}")
    blocked = [(x, y) for x, y in e.shaft(hb) if l1[y * wb + x] >> 12 != 0]
    if blocked:
        problems.append(f"{r.key}: poço do elevador fechado em {blocked[:3]}")
    return problems


def check_elevators_in_rom(rom, manifest) -> list[str]:
    """specs/12e, built ROM: each elevator room's door-out list goes on after its doors with the exit and the platform's
    entries (manifest "elevator"); the exit's entry = build.elevator_exit_entry to the other room's header (flags $C0:
    elevator + area change, orientation 2 down / 3 up, no push, camera on the other platform's screen); the platform's
    = build.ELEVATOR_PAD_DOOR (no room); every state's population starts with build.elevator_spawn ($D73F: x, y, the key,
    the arrival y); the header's area byte is the room's area."""
    problems = []
    built = elevator_rooms()
    for key, (area, r) in built.items():
        if not r.elevator:
            if "elevator" in manifest.get(key, {}):
                problems.append(f"{key}: entradas de elevador no manifest sem RoomDef.elevator (reconstruir)")
            continue
        m = manifest.get(key, {})
        if "elevator" not in m:
            problems.append(f"{key}: sem as entradas do elevador no manifest.json (reconstruir)")
            continue
        header = m["header"]
        if rom.u8(header + 1) != area.number:
            problems.append(f"{key}: cabeçalho na área {rom.u8(header + 1)}, a sala é da área {area.number}")
        exit_door, pad_door = m["elevator"]
        door_list = 0x8F0000 | rom.u16(header + 9)
        slots = [rom.u16(door_list + 2 * i) for i in range(len(r.doors) + 2)]
        if slots[len(r.doors):] != [exit_door & 0xFFFF, pad_door & 0xFFFF]:
            problems.append(f"{key}: lista de portas sem a saída e a plataforma do elevador nos lugares {r.elevator_slots}")
        other_key = next(((b if a == key else a) for a, b in ELEVATORS if key in (a, b)), None)
        if other_key not in built or other_key not in manifest:
            problems.append(f"{key}: elevador sem par construído em areas.ELEVATORS (reconstruir?)")
            continue
        other_area, other = built[other_key]
        teleporter = key in impact_rooms.TELEPORTER   # specs/20e: the crater's, inside area 0
        try:
            want = build.elevator_exit_entry(r, manifest[other_key]["header"], other, teleporter)
        except RuntimeError as e:   # check_elevators says why
            problems.append(f"{key}: {e}")
            continue
        got = rom.read(exit_door, 12)
        if got != want:
            problems.append(f"{key}: saída do elevador = {got.hex()}, esperado {want.hex()} (para {other_key})")
        if teleporter:
            if got[2] != build.ELEVATOR_SAME_AREA_FLAGS or other_area.number != area.number:
                problems.append(f"{key}: saída do teleporte da cratera com as flags ${got[2]:02X} para a área {other_area.number}: "
                                f"esperado ${build.ELEVATOR_SAME_AREA_FLAGS:02X} (elevador sem troca de área) na mesma área")
        elif got[2] & 0xC0 != 0xC0 or other_area.number == area.number:
            problems.append(f"{key}: saída do elevador sem as flags de elevador e troca de área (${got[2]:02X})")
        if rom.read(pad_door, 12) != build.ELEVATOR_PAD_DOOR:
            problems.append(f"{key}: porta da plataforma do elevador diferente de ${build.ELEVATOR_PAD_DOOR_VANILLA:06X}")
        spawn = build.elevator_spawn(r)
        if key == impact_rooms.TELEPORTER[0]:
            problems += check_teleporter_states(rom, key, header, spawn)
            continue
        for st in m["states"]:
            if rom.read(0xA10000 | rom.u16(st + 8), len(spawn)) != spawn:
                problems.append(f"{key}: estado ${st & 0xFFFF:04X} sem a plataforma do elevador ($D73F) na população")
    return problems


def check_teleporter_states(rom, key: str, header: int, spawn: bytes) -> list[str]:
    """specs/20e, built ROM: the Artifact Temple's teleporter works only once the Omega Pirate is dead: the room has two states, the
    default without the elevator's platform ($D73F) in its population, and one with it, selected by our state condition
    (room_reader.other_area_boss_condition) on the bit of impact_rooms.OPENS_AFTER's arena (chozo/bosses.py: the Omega Pirate's
    $10) in the boss bits of its area (the Mines', area 5) = build.teleporter_condition; the default state's main ASM keeps
    elevator_flags off (room_reader.ELEVATOR_FLAGS_OFF: no platform AI clears them there), the other has none."""
    from smlib.room_reader import ELEVATOR_FLAGS_OFF, our_condition
    problems = []
    arena = chozo_bosses.arena_of(impact_rooms.OPENS_AFTER)
    room = read_room(rom, 0x8F0000 | header & 0xFFFF)
    if arena is None or arena.room != impact_rooms.OPENS_AFTER:
        return [f"{key}: o teleporte da cratera espera a arena de {impact_rooms.OPENS_AFTER}, que não existe"]
    if len(room.states) != 2:
        return [f"{key}: {len(room.states)} estados, esperado 2 (sem e com a plataforma do teleporte)"]
    on, off = room.states
    if our_condition(rom, on.condition) != (MINES_AREA, arena.bit) or rom.read(0x8F0000 | on.condition, 19) != \
            build.teleporter_condition():
        problems.append(f"{key}: a condição do estado com a plataforma (${on.condition:04X}) não é o bit ${arena.bit:02X} da área "
                        f"{MINES_AREA} (a arena de {impact_rooms.OPENS_AFTER})")
    if rom.read(0xA10000 | on.enemy_pop, len(spawn)) != spawn:
        problems.append(f"{key}: o estado do Omega morto sem a plataforma do elevador ($D73F) na população")
    pop = rom.read(0xA10000 | off.enemy_pop, 2)
    if rom.read(0xA10000 | off.enemy_pop, len(spawn)) == spawn or pop[:2] == spawn[:2]:
        problems.append(f"{key}: o estado padrão (Omega vivo) com a plataforma do elevador: o teleporte funcionaria antes do chefe")
    if any(getattr(on, f) != getattr(off, f) for f in ("level_data", "tileset", "music_data", "music_track", "fx", "layer2_scroll",
                                                       "bg_data", "setup_asm")):
        problems.append(f"{key}: os dois estados diferem em algo além da população, do código da sala (e da lista de PLMs)")
    if on.main_asm or not off.main_asm or rom.read(0x8F0000 | off.main_asm, len(ELEVATOR_FLAGS_OFF)) != ELEVATOR_FLAGS_OFF:
        problems.append(f"{key}: o estado sem a plataforma precisa do código que desliga elevator_flags ($0E16) e o com ela de "
                        f"nenhum (código ${off.main_asm:04X} / ${on.main_asm:04X})")
    return problems


def check_ruins_in_rom(rom, base, manifest) -> list[str]:
    """specs/12d: tileset $0C (smlib/ruins.py) in the built ROM: its table entry is its own (no other tileset points at
    it), its graphics are the vanilla ones, its palette is a copy in the fixed range with line 7 = ruins.SANDSTONE (specs/12f:
    and line beamdoors.RUINS_PAINT_LINE the purple wave door's) and the rest vanilla, its metatile table (specs/12f) a copy in
    the fixed range, vanilla but the wave door's 8 metatiles; and the recolour is seen by no one yet: no state of any room the game loads
    (ours, the manifest, which check_orphans proves is every room reachable, and the attract demos' rooms, DEMO_SCENES)
    uses tileset $0C, except rooms of the Chozo area (since specs/12e its 3 elevator rooms). Prints the line "ruínas"."""
    problems = []
    t = ruins.RUINS_TILESET
    entries = [rom.u16(TILESET_TABLE + 2 * i) for i in range(0x1D)]
    if entries.count(entries[t]) != 1:
        problems.append(f"tileset {t:02X}: a entrada ${entries[t]:04X} da tabela é de mais de um tileset")
    e, be = ruins.entry(rom), ruins.entry(base)
    if e != be:
        problems.append(f"tileset {t:02X}: entrada da tabela mudou de lugar (${be:06X} -> ${e:06X})")
    if rom.u24(e + 3) != base.u24(be + 3):
        problems.append(f"tileset {t:02X}: gráficos diferentes dos vanilla")
    lo, hi = build.FIXED_BANKS
    # specs/12f: the metatile table is a copy in the fixed range: vanilla + the purple wave door's 8 metatiles
    mt = rom.u24(e)
    if not lo <= mt <= hi:
        problems.append(f"tileset {t:02X}: metatiles em ${mt:06X}, fora do alocador fixo")
    else:
        try:
            got_mt = decompress(rom.data, snes_to_pc(mt))[0]
        except (CompressionError, IndexError, ValueError) as err:
            got_mt = None
            problems.append(f"tileset {t:02X}: metatiles em ${mt:06X} não descomprimem ({err})")
        vanilla_mt = ruins.vanilla_metatiles(base)
        if got_mt is not None and got_mt != build.ruins_metatiles(base):
            problems.append(f"tileset {t:02X}: metatiles em ${mt:06X} não são os vanilla com os das portas de onda e de charge")
        if got_mt is not None:   # specs/12g2: each painted metatile = the green cap's CRE one on its line, read directly
            cre = decompress(base.data, snes_to_pc(beamdoors.CRE_TILE_TABLE))[0]
            for mts, line, what in ((beamdoors.PAINT_METATILES, beamdoors.RUINS_PAINT_LINE, "onda"),
                                    (beamdoors.CHARGE_METATILES, beamdoors.CHARGE_LINE, "charge")):
                for src, dst in mts.items():
                    want = [int.from_bytes(cre[src * 8 + 2 * k:src * 8 + 2 * k + 2], "little") for k in range(4)]
                    want = [(w & ~0x1C00) | (line << 10) if (w >> 10) & 7 == beamdoors.FRAME_LINE else w for w in want]
                    at = (dst - 0x100) * 8
                    have = [int.from_bytes(got_mt[at + 2 * k:at + 2 * k + 2], "little") for k in range(4)]
                    if have != want:
                        problems.append(f"tileset {t:02X}: metatile ${dst:03X} (porta de {what}) não é o ${src:03X} da porta "
                                        f"verde na linha {line}")
        if got_mt is not None and got_mt == build.ruins_metatiles(base):
            changed = {k // 8 + 0x100 for k in range(0, len(got_mt), 8) if got_mt[k:k + 8] != vanilla_mt[k:k + 8]}
            if not changed <= set(beamdoors.PAINT_METATILES.values()) | set(beamdoors.CHARGE_METATILES.values()):
                problems.append(f"tileset {t:02X}: metatiles mudados além dos das portas de onda e de charge: "
                                f"{sorted(map(hex, changed))}")
    pal = rom.u24(e + 6)
    if not lo <= pal <= hi:
        problems.append(f"tileset {t:02X}: paleta em ${pal:06X}, fora do alocador fixo")
    else:
        try:
            got = decompress(rom.data, snes_to_pc(pal))[0]
        except (CompressionError, IndexError, ValueError) as err:
            got = None
            problems.append(f"tileset {t:02X}: paleta em ${pal:06X} não descomprime ({err})")
        if got is not None:   # specs/12g2: the two painted lines read directly (not through the build's function)
            for line, colours, what in ((beamdoors.RUINS_PAINT_LINE, beamdoors.PURPLE, "onda"),
                                        (beamdoors.CHARGE_LINE, beamdoors.WHITE, "charge")):
                words = [int.from_bytes(got[2 * (line * 16 + i):2 * (line * 16 + i) + 2], "little") for i in (1, 2, 3)]
                if tuple(words) != tuple(colours):
                    problems.append(f"tileset {t:02X}: linha {line} da paleta (porta de {what}) com as cores "
                                    f"{[f'${w:04X}' for w in words]}, esperado {[f'${w:04X}' for w in colours]}")
        if got is not None and got != build.ruins_palette(base):
            problems.append(f"tileset {t:02X}: paleta em ${pal:06X} não é a vanilla com a linha {ruins.PALETTE_LINE} = SANDSTONE, "
                            f"a {beamdoors.RUINS_PAINT_LINE} da porta de onda e a {beamdoors.CHARGE_LINE} da de charge")
    users = []
    ours = {k: v for k, v in manifest.items() if isinstance(v, dict) and "header" in v}
    for key, v in ours.items():
        if key.startswith("chozo_"):
            continue
        if any(st.tileset == t for st in read_room(rom, 0x8F0000 | (v["header"] & 0xFFFF)).states):
            users.append(key)
    for room in demo_rooms_kept(rom, base):   # specs/19a: a demo room whose header was reclaimed is no room any more
        if any(st.tileset == t for st in read_room(rom, 0x8F0000 | room).states):
            users.append(f"demo ${room:04X}")
    if users:
        problems.append(f"tileset {t:02X} (ruínas, recolorido) usado fora da Chozo: {users}")
    if not problems:
        chozo = sum(k.startswith("chozo_") for k in ours)
        print(f"ruínas (specs/12d): tileset {t:02X} com a linha {ruins.PALETTE_LINE} em arenito (paleta em ${pal:06X}; specs/12f: "
              f"linha {beamdoors.RUINS_PAINT_LINE} e metatiles da porta de onda, tabela em ${rom.u24(e):06X}; specs/12g2: "
              f"linha {beamdoors.CHARGE_LINE} e metatiles da porta de charge, {beamdoors.CHARGE_NAME}); "
              f"usado só pelas {chozo} salas da Chozo; nenhuma das outras {len(ours) - chozo} salas nossas nem das "
              f"{len(kept := demo_rooms_kept(rom, base))} salas das demos usa o tileset"
              + (f" (mais {n} das demos com o cabeçalho recuperado, specs/19a: nenhuma sala)"
                 if (n := len({d[2] for d in DEMO_SCENES}) - len(kept)) else ""))
    return problems


def all_rooms_flat() -> list:
    return [r for _, r in all_rooms()]


LDA_ROOM_PTR_CMP = b"\xAD\x9B\x07\xC9"   # LDA $079B; CMP #imm16
# specs/17a: the same with X and Y (LDX $079B; CPX #imm16 / LDY $079B; CPY #imm16; none in the base ROM)
ROOM_PTR_LOADS = ((0xAD, 0xC9), (0xAE, 0xE0), (0xAC, 0xC0))
# specs/17a: CMP/CPX/CPY $079B (absolute) and CMP $7E079B (long): a compare with memory, whose other side is no immediate the scan
# can read (none in the base ROM)
ROOM_PTR_MEM_COMPARES = (b"\xCD\x9B\x07", b"\xEC\x9B\x07", b"\xCC\x9B\x07", b"\xCF\x9B\x07\x7E")


def room_ptr_compares(rom) -> set[int]:
    """specs/12a: the room headers vanilla code tells apart by address, read from the bytes: every LDA $079B
    followed by a chain of CMP #imm16 (each with its BEQ/BNE) anywhere in the ROM; specs/17a: LDX/CPX and LDY/CPY too."""
    out = set()
    data = bytes(rom.data)
    for load, cmp in ROOM_PTR_LOADS:
        at = 0
        while (at := data.find(bytes([load, 0x9B, 0x07, cmp]), at)) >= 0:
            p = at + 3
            while data[p] == cmp:
                out.add(data[p + 1] | data[p + 2] << 8)
                p += 3
                if data[p] not in (0xF0, 0xD0):
                    break
                p += 2
            at += 3
    return out


def room_ptr_memory_compares(rom) -> list[int]:
    """specs/17a: ROM offsets of every compare of the room pointer with memory (ROOM_PTR_MEM_COMPARES); meant for the base ROM
    (vanilla code)."""
    data = bytes(rom.data)
    out = []
    for pat in ROOM_PTR_MEM_COMPARES:
        at = 0
        while (at := data.find(pat, at)) >= 0:
            out.append(at)
            at += 1
    return sorted(out)


def check_reclaimed(rom, base, manifest, verbose: bool = True) -> list[str]:
    """specs/12a, built ROM: the $8F ranges the build takes back from orphan rooms (build.RECLAIMED_8F) sit in
    $8F, outside build.FREE_8F and apart; on the base ROM's bytes every byte of them belongs to the structures
    (smlib/roomgraph.structures) of vanilla rooms nothing loads (specs/18a: a demo room's, DEMO_SCENES, only while the
    attract demos are off, title.check_demos_off on the built ROM), none to
    VANILLA_SHARED data, and no range holds a header address vanilla code compares the room pointer with
    (build.ROOM_PTR_COMPARED, which must equal what the bytes compare: room_ptr_compares). In the built ROM the
    only bytes there that differ from the base are our rooms' structures, and every header of ours is in the
    build's space and at none of the compared addresses. specs/19a: the same for the $A1 ranges (build.RECLAIMED_A1,
    enemy populations; outside build.FREE_A1, none of VANILLA_SHARED's populations). Prints the range use."""
    problems: list[str] = []
    compared = room_ptr_compares(rom)
    if compared != set(build.ROOM_PTR_COMPARED):
        problems.append(f"$8F recuperado: o código compara a sala com {sorted(f'${c:04X}' for c in compared)}, "
                        f"build.ROOM_PTR_COMPARED diz {sorted(f'${c:04X}' for c in build.ROOM_PTR_COMPARED)}")
    compared |= set(build.ROOM_PTR_COMPARED)
    # specs/17a: vanilla code (base ROM; the arenas' routine of ours, specs/14b, compares $079B with its own table of our headers)
    for at in room_ptr_memory_compares(base):
        problems.append(f"$8F recuperado: comparação da sala ($079B) com memória no offset ${at:06X} da ROM base: o cabeçalho "
                        "comparado não se lê dos bytes")
    ours = {v["header"] & 0xFFFF: k for k, v in manifest.items() if isinstance(v, dict) and "header" in v}
    for h, key in sorted(ours.items()):
        if h in compared:
            problems.append(f"{key}: cabeçalho em $8F:{h:04X}, endereço que o código vanilla compara com a sala atual")
        if not build.ours_8f(h):
            problems.append(f"{key}: cabeçalho em $8F:{h:04X}, fora do espaço livre do build")
    banks = ((0x8F, build.RECLAIMED_8F, build.FREE_8F), (0xA1, build.RECLAIMED_A1, build.FREE_A1))   # specs/19a: $A1 too
    for bank, ranges, free in banks:
        for i, (lo, hi) in enumerate(ranges):
            if lo >> 16 != bank or hi >> 16 != bank or hi < lo or lo & 0xFFFF < 0x8000:   # specs/18a: $xx:0000-7FFF is no ROM
                problems.append(f"${bank:02X} recuperado: faixa ${lo:06X}-${hi:06X} fora do banco ${bank:02X}")
            if not (hi < free[0] or lo > free[1]):
                problems.append(f"${bank:02X} recuperado: faixa ${lo:06X}-${hi:06X} cruza o espaço livre ${free[0]:06X}")
            for lo2, hi2 in ranges[i + 1:]:
                if not (hi < lo2 or hi2 < lo):
                    problems.append(f"${bank:02X} recuperado: faixas ${lo:06X}-${hi:06X} e ${lo2:06X}-${hi2:06X} se cruzam")
            for c in sorted(compared) if bank == 0x8F else ():
                if lo <= 0x8F0000 | c <= hi:
                    problems.append(f"$8F recuperado: faixa ${lo:06X}-${hi:06X} contém o cabeçalho $8F:{c:04X}, que o "
                                    "código vanilla compara com a sala atual")
    if problems and any(lo >> 16 != bank or hi >> 16 != bank or lo & 0xFFFF < 0x8000
                        for bank, ranges, _ in banks for lo, hi in ranges):
        return problems   # the byte checks below read the ranges' bytes
    vanilla = vanilla_rooms(base)
    demo = {roomgraph.door_target(base, door) for *_, door in DEMO_SCENES} | {room for _, _, room, _ in DEMO_SCENES}
    orphan_bytes = set().union(*(roomgraph.byte_set(roomgraph.structures(base, h)) for h in vanilla - demo))
    demo_bytes = set().union(*(roomgraph.byte_set(roomgraph.structures(base, h)) for h in demo & vanilla))
    shared = {0x8F: {0x8F0000 | p + k for p in VANILLA_SHARED["fundo"] for k in range(roomgraph.bg_size(base, p))},
              0xA1: {0xA10000 | p + k for p in VANILLA_SHARED["inimigos"] for k in range(roomgraph.population_size(base, p))}}

    def runs(addrs: set[int]) -> str:
        out: list[list[int]] = []
        for a in sorted(addrs):
            if out and out[-1][1] == a - 1:
                out[-1][1] = a
            else:
                out.append([a, a])
        return ", ".join(f"${lo:06X}" + (f"-${hi:06X}" if hi > lo else "") for lo, hi in out[:4]) + (" …" if len(out) > 4 else "")

    # specs/18a: the attract demos' rooms are orphans too while the demos stay off (specs/16, from the bytes): their bytes may be
    # reclaimed only then; with the demos back on, any reclaimed byte of a demo room is an error
    demos_on = title.check_demos_off(rom)
    ours_bytes = set().union(*(roomgraph.byte_set(roomgraph.structures(rom, h)) for h in ours))
    ours_bytes |= {a + k for a in item_arena_doors(rom) for k in range(6)}   # specs/14d: the ITEM arenas' door caps
    # specs/19a: a population of ours inside a reclaimed $A1 range is one the build wrote there, never an orphan room's left as it was
    # (check_orphans takes any pointer in the build's $A1 space as ours)
    orphan_pops = {a for h in vanilla for a, _, kind in roomgraph.structures(base, h) if kind == "inimigos"}
    for h, key in sorted(ours.items(), key=lambda kv: kv[1]):
        for st in read_room(rom, 0x8F0000 | h).states:
            a = 0xA10000 | st.enemy_pop
            n = roomgraph.population_size(rom, st.enemy_pop) if st.enemy_pop else 0
            if n and a in orphan_pops and st.enemy_pop not in VANILLA_SHARED["inimigos"] and any(lo <= a <= hi for lo, hi in build.RECLAIMED_A1) \
                    and rom.read(a, n) == base.read(a, n):
                problems.append(f"{key}: população em ${a:06X}, a de uma sala vanilla órfã deixada como está na faixa "
                                "recuperada do $A1")
    lines = []
    for bank, ranges, _ in banks:
        reclaimed = {a for lo, hi in ranges for a in range(lo, hi + 1)}
        what = "VANILLA_SHARED: fundo" if bank == 0x8F else "VANILLA_SHARED: inimigos"
        for addrs, why in ((reclaimed - orphan_bytes - (set() if demos_on else demo_bytes),
                            "não é dado só de sala órfã (código, dado sem dono ou sala usada)"),
                           (reclaimed & demo_bytes if demos_on else set(),
                            f"é dado de sala das demos (DEMO_SCENES) e as demos não estão desligadas ({'; '.join(demos_on)})"),
                           (reclaimed & shared[bank], f"é dado vanilla que nossas salas usam ({what})")):
            if addrs:
                problems.append(f"${bank:02X} recuperado: {len(addrs)} bytes {why}: {runs(addrs)}")
        stray = {a for a in reclaimed if rom.u8(a) != base.u8(a)} - ours_bytes
        if stray:
            problems.append(f"${bank:02X} recuperado: {len(stray)} bytes escritos fora das estruturas das nossas salas: {runs(stray)}")
        used = len(ours_bytes & reclaimed)
        per = [sum(1 for a in ours_bytes if lo <= a <= hi) for lo, hi in ranges]   # specs/17a: use per range
        uses = ' '.join(f'{n}/{hi - lo + 1}' for n, (lo, hi) in zip(per, ranges))
        head = (f"${bank:02X} recuperado: {len(reclaimed)} bytes em {len(ranges)} faixa{'s' if len(ranges) > 1 else ''} "
                f"({', '.join(f'${lo:06X}-${hi:06X}' for lo, hi in ranges)}), só de salas órfãs; usados pelas nossas salas: "
                f"{used} ({uses}); ")
        lines.append(head + (f"o código compara a sala com {len(compared)} cabeçalhos, nenhum nosso nem nas faixas; "
                             f"{len(reclaimed & demo_bytes)} bytes de salas das demos, só com as demos desligadas (specs/18a, 19a)"
                             if bank == 0x8F else
                             f"{len(reclaimed & demo_bytes)} bytes de salas das demos, só com as demos desligadas; populações "
                             f"nossas só em $A1 do build ou na VANILLA_SHARED (check_orphans) (specs/19a)"))
    if verbose and not problems:
        for line in lines:
            print(line)
    return problems


_VANILLA_ROOMS: dict[bytes, frozenset[int]] = {}


def vanilla_rooms(rom) -> frozenset[int]:
    """The rooms of a (base) ROM, crawled from its bytes (smlib/roomgraph.vanilla_rooms), once per ROM."""
    key = hashlib.sha1(rom.data).digest()
    if key not in _VANILLA_ROOMS:
        _VANILLA_ROOMS[key] = frozenset(roomgraph.vanilla_rooms(rom))
    return _VANILLA_ROOMS[key]


def vanilla_door_bits(rom) -> set[int]:
    """Door bits of the grey and coloured door PLMs of every vanilla room (specs/11: the 262 rooms read from
    the base ROM's bytes, smlib/roomgraph.vanilla_rooms; research/sm_rooms.json missed 12)."""
    bits = set()
    for h in vanilla_rooms(rom):
        for st in read_room(rom, 0x8F0000 | h).states:
            p = 0x8F0000 | st.plm if st.plm else None
            while p and rom.u16(p):
                # grey, yellow, green and red doors all keep their opened bit in the low bits
                if min(build.GREY_DOOR_PLM.values()) <= rom.u16(p) <= max(build.RED_DOOR_PLM.values()):
                    bits.add(rom.u16(p + 4) & 0x1FF)
                p += 6
    return bits


def check_gates(rom, base) -> list[str]:
    """Built ROM (specs/07k, 09a): every Tallon door with a cap (DoorLink.lock) has its PLM on the cap
    block in every state of the room: red door with its door bit, beam door of its beam and wall side
    (tallon/beamdoors.py) with argument $8000 (no door bit: closed on every visit), or grey that never
    opens, only on the Bombs gate (the Tallon Canyon's bomb walls, until 09d); the beam doors' code in
    $84 (pre-instructions, lists, headers) is what beamdoors generates from the base ROM's vanilla
    doors; the red doors' bits are unique and unused by the vanilla rooms."""
    manifest = json.loads((BUILT_ROM.parent / "manifest.json").read_text())
    problems, bits = [], []
    try:
        for addr, data in beamdoors.code(base):
            got = rom.read(addr, len(data))
            if got != data:
                at = next(k for k in range(len(data)) if got[k] != data[k])
                problems.append(f"tallon: portas de feixe: ${addr + at:06X} na ROM é ${got[at]:02X}, "
                                f"beamdoors gera ${data[at]:02X} (reconstruir?)")
    except RuntimeError as e:
        problems.append(f"tallon: portas de feixe: {e}")
    for r in world_rooms() + crater_only().rooms:   # specs/12f: the Chozo's doors too; specs/20h: the crater's (out of the walk)
        for i, d in enumerate(r.doors):
            if d.lock is None:
                continue
            x, y, _, _ = build.door_cap_and_screen(r, i)
            if d.lock == "grey" and chozo_rooms.ONE_WAY_GATE in d.gate and r in CHOZO.rooms:
                want = (build.GREY_DOOR_PLM[d.side], build.GREY_DOOR_NEVER)   # specs/12f: the Chozo's one-way doors
            elif d.lock == "missile":
                want = (build.RED_DOOR_PLM[d.side], d.lock_bit)
                bits.append((d.lock_bit, frozenset({r.key, d.to_room})))
            elif d.lock == "boss" and d.gate == {chozo_rooms.BOSS_GATE} and (r.key, d.to_room) in chozo_rooms.BOSS_DOORS \
                    and build.item_arena_door(r.key, d):
                # specs/14d: an ITEM arena's boss door: no cap in any state's list (blue until the fight; the arena routine
                # spawns its grey cap from the fight record: check_arenas_in_rom)
                want = (build.GREY_DOOR_PLM[d.side], chozo_bosses.GREY_DOOR_KILLS)
                for st in manifest.get(r.key, {}).get("states", []):
                    if any(pl[0] == want[0] and pl[1:3] == (x, y) for pl in room_plms(rom, st)):
                        problems.append(f"{r.key}: porta {i} ({d.side}{d.screen}) da arena de item com tampa cinza na lista "
                                        f"do estado ${st & 0xFFFF:04X} (fechada antes da luta)")
                continue
            elif d.lock == "boss" and d.gate == {chozo_rooms.BOSS_GATE} and (r.key, d.to_room) in chozo_rooms.BOSS_DOORS:
                want = (build.GREY_DOOR_PLM[d.side], build.GREY_DOOR_MINI_BOSS)   # specs/14c: the boss' grey door, type 1
            elif build.arena_door_alive_cap(r.key, d) is not None and ((r.key, d.to_room) in phendrana_rooms.BOSS_DOORS
                                                                    or (r.key, d.to_room) in mines_rooms.BOSS_DOORS
                                                                    or (r.key, d.to_room) in impact_rooms.BOSS_DOORS) \
                    and {tallon_rooms.LOCK_OF.get(g) for g in d.gate - {chozo_rooms.BOSS_GATE}} == \
                    ({d.dead_lock} if d.dead_lock else set()):
                # specs/18h: a KILLS arena's boss door: the grey cap of type 3 (the kill count) in the alive state's list only,
                # its dead_lock cap (Prime's key lock: the Chapel's wave door) in the dead state's only; 18k: a Torizo arena's,
                # the grey cap of type 2 (the Torizo's bit)
                states = manifest.get(r.key, {}).get("states", [])
                arena = chozo_bosses.arena_of(r.key)
                grey = (build.GREY_DOOR_PLM[d.side], x, y, chozo_bosses.GREY_DOOR_KILLS if arena.condition == chozo_bosses.KILLS
                        else chozo_bosses.GREY_DOOR_TORIZO)
                dead = (beamdoors.PLM[(d.dead_lock, d.side)], x, y, build.BEAM_DOOR_ARG) if d.dead_lock else None
                if len(states) != 2:
                    problems.append(f"{r.key}: arena com {len(states)} estados no manifest.json (reconstruir?)")
                for k, st in enumerate(states):
                    caps = [pl for pl in room_plms(rom, st) if pl[1:3] == (x, y)]
                    if caps != ([grey] if k == 0 else [dead] if dead else []):
                        problems.append(f"{r.key}: porta {i} ({d.side}{d.screen}) da arena com as tampas {caps} no estado "
                                        f"${st & 0xFFFF:04X} ({'vivo' if k == 0 else 'morto'}: esperado "
                                        f"{grey if k == 0 else dead})")
                continue
            elif d.lock in tallon_rooms.BEAM_LOCKS:
                if d.lock not in d.gate or (d.lock, d.side) not in beamdoors.PLM:
                    problems.append(f"{r.key}: porta {i} ({d.side}{d.screen}) com tampa {d.lock} fora da trava "
                                    f"{sorted(d.gate)} ou numa parede sem porta de feixe")
                    continue
                want = (beamdoors.PLM[(d.lock, d.side)], build.BEAM_DOOR_ARG)
            else:   # specs/09d: no grey "never opens" door is left in the Tallon (specs/12f: the Chozo's one-way ones)
                problems.append(f"{r.key}: porta {i} ({d.side}{d.screen}) com tampa {d.lock!r} na trava "
                                f"{sorted(d.gate)}: só portas vermelhas, de feixe e (na Chozo) cinza de mão única ou de chefe")
                continue
            if r.key not in manifest:
                problems.append(f"{r.key}: fora do manifest.json da ROM construída (reconstruir)")
                break
            for st in manifest[r.key]["states"]:
                plms, p = [], 0x8F0000 | rom.u16(st + 20)
                while p != 0x8F0000 and rom.u16(p):
                    plms.append((rom.u16(p), rom.u8(p + 2), rom.u8(p + 3), rom.u16(p + 4)))
                    p += 6
                if (want[0], x, y, want[1]) not in plms:
                    problems.append(f"{r.key}: porta {i} ({d.side}{d.screen}) sem a tampa {d.lock} "
                                    f"(PLM ${want[0]:04X} em ({x},{y}), argumento ${want[1]:04X})")
    for r in world_rooms():   # specs/18i: the in-room beam caps (RoomDef.caps), a beam door PLM in every state
        for x, y, side, beam in r.caps:
            if (beam, side) not in beamdoors.PLM:
                continue   # check_niche_caps says it
            want = (beamdoors.PLM[(beam, side)], x, y, build.BEAM_DOOR_ARG)
            for st in manifest.get(r.key, {}).get("states", []):
                if want not in room_plms(rom, st):
                    problems.append(f"{r.key}: estado ${st & 0xFFFF:04X} sem a tampa de {beam} dentro da sala em ({x},{y}) "
                                    f"(PLM ${want[0]:04X}, argumento ${want[3]:04X})")
    # specs/12i: a link with a red door on both sides (the Hive Totem <-> Transport Access North) has one bit for both
    # (opened from either side); a bit is never shared by two links
    links: dict[int, list] = {}
    for bit, link in bits:
        links.setdefault(bit, []).append(link)
    shared = {b: v for b, v in links.items() if len(set(v)) > 1 or len(v) > 2}
    if shared:
        problems.append(f"tallon/chozo: bits de porta vermelha repetidos entre ligações {sorted(shared)}")
    used = vanilla_door_bits(base) & set(links)
    if used:
        problems.append(f"tallon: bits de porta vermelha {sorted(used)} já usados por portas vanilla")
    return problems


def vanilla_item_bits(rom) -> set[int]:
    """Item bits of the item PLMs ($84:EED7-$EFD2: visible, Chozo orb, hidden) of every vanilla room (specs/11:
    read from the base ROM's bytes, smlib/roomgraph.vanilla_rooms)."""
    bits = set()
    for h in vanilla_rooms(rom):
        for st in read_room(rom, 0x8F0000 | h).states:
            p = 0x8F0000 | st.plm if st.plm else None
            while p and rom.u16(p):
                if 0xEED7 <= rom.u16(p) < 0xEFD3:
                    bits.add(rom.u16(p + 4))
                p += 6
    return bits


def room_plms(rom, state: int) -> list[tuple[int, int, int, int]]:
    """(PLM id, x, y, argument) of a room state's PLM list."""
    plms, p = [], 0x8F0000 | rom.u16(state + 20)
    while p != 0x8F0000 and rom.u16(p):
        plms.append((rom.u16(p), rom.u8(p + 2), rom.u8(p + 3), rom.u16(p + 4)))
        p += 6
    return plms


def check_tallon_items(rom, base) -> list[str]:
    """specs/07h: the Tallon item bits (tallon/items.py) are unique, inside the item-bit array and
    unused by the vanilla item PLMs (base ROM); in the built ROM every placed item has its PLM
    (kind, block, bit) in every state of its room, and no other Tallon item PLM is there (09b: the 7
    lock items' kinds count). specs/09b: the Gravity Suit cutscene's patch (items.gravity_patch, from
    the base ROM) is in the built ROM."""
    manifest = json.loads((BUILT_ROM.parent / "manifest.json").read_text())
    problems = []
    for name, patch in (("Gravity Suit", tallon_items.gravity_patch), ("Varia Suit", tallon_items.varia_patch)):   # 12g
        try:
            addr, data = patch(base)
            got = rom.read(addr, len(data))
            if got != data:
                problems.append(f"tallon: cena da {name}: ${addr:06X} na ROM = {got.hex()}, "
                                f"items.{patch.__name__} gera {data.hex()} (reconstruir?)")
        except RuntimeError as e:
            problems.append(f"tallon: {e}")
    # specs/12f: the Chozo's item bits (chozo/items.py, after the Tallon's) in the same check: one array, no bit twice
    bits = (list(tallon_items.BITS.values()) + list(chozo_items.BITS.values()) + list(magmoor_items.BITS.values())   # 17f
            + list(phendrana_items.BITS.values()) + list(mines_items.BITS.values()))   # 18f, 19f
    if len(set(bits)) != len(bits) or not all(0 <= b < tallon_items.ITEM_BITS for b in bits):
        problems.append(f"tallon/chozo/magmoor/phendrana: bits de item repetidos ou fora do vetor: {bits}")
    used = vanilla_item_bits(base) & set(bits)
    if used:
        problems.append(f"tallon/chozo: bits de item {sorted(used)} já usados por itens vanilla")
    want: dict[str, set] = {}
    for n, it in world_items({r.key for r in world_rooms()}):
        want.setdefault(it.room, set()).add((it.kind, *it.spot, item_bit(n)))
    for r in world_rooms():
        if r.key not in manifest:
            problems.append(f"{r.key}: fora do manifest.json da ROM construída (reconstruir)")
            continue
        arena = chozo_bosses.arena_of(r.key)
        for n, st in enumerate(manifest[r.key]["states"]):
            got = {p for p in room_plms(rom, st) if p[0] in tallon_items.KIND_NAME}
            if n == 0 and arena is not None and arena.prize is not None:   # specs/14b: the prize not in the alive state
                got |= {p for p in want.get(r.key, set()) if (p[1], p[2]) == arena.prize[1]}
                if any((p[1], p[2]) == arena.prize[1] for p in room_plms(rom, st) if p[0] in tallon_items.KIND_NAME):
                    problems.append(f"{r.key}: o prêmio da arena {arena.prize[1]} está no estado vivo (aparece antes da luta)")
            if got != want.get(r.key, set()):
                problems.append(f"{r.key}: PLMs de item {sorted(got)}, esperado {sorted(want.get(r.key, set()))}")
    return problems


def tallon_drafts() -> list:
    """Rooms with a layout (tallon/layouts.py) that the build does not get yet, each built with its
    region alone, so its doors are there (specs/07j)."""
    built = {r.key for r in tallon_rooms.ROOMS}
    return [r for g in tallon_rooms.REGIONS for r in tallon_rooms.build_rooms({g})
            if r.key in tallon_rooms.LAYOUTS and r.key not in built]


def tallon_report() -> str:
    """One line: the Tallon map's save bytes, total and per region (each region alone)."""
    total = len(tallon_map_bytes(tallon_rooms.ALL_ROOMS))
    per = " ".join(f"{g} {len(tallon_map_bytes(tallon_rooms.build_rooms({g})))}" for g in tallon_rooms.REGIONS)
    rooms = tallon_rooms.ALL_ROOMS
    built = f", {len(tallon_rooms.ROOMS)} salas construídas" if tallon_rooms.ROOMS else ""
    drafts = len(tallon_drafts())
    built += f", {drafts} desenhadas fora do build" if drafts else ""
    rounds, first, first_item, _ = tallon_progress_built()
    tallon_first = [k for k in first if k in TALLON.by_key()]   # specs/12f: the walk has the Chozo's rooms and items too
    tallon_got = [n for n in first_item if not isinstance(n, tuple)]
    built += f", alcançáveis agora: {len(tallon_first)}, {len(tallon_got)} itens em {len(rounds)} rodadas"
    return (f"tallon (tabela inteira, regiões ativas: {''.join(sorted(tallon_rooms.ACTIVE_REGIONS)) or 'nenhuma'}{built}): "
            f"{len(rooms)} salas, {sum(len(r.doors) for r in rooms) // 2} ligações, "
            f"{sum(r.width * r.height for r in rooms)} telas, mapa {total}/{mapsave.LIST_ROOM[TALLON.number]} "
            f"bytes de SRAM (por região: {per})")


def reach_space_jump(r, passable, wb: int, hb: int, loadout: reach.Loadout) -> tuple[list[str], set]:
    """Space Jump + Morph: flood fill of the open cells from the first entry point."""
    problems = []
    starts = [door_inner_cells(d.side, d.screen, wb, hb)[0] for d in r.doors]
    if r.spawn:
        starts.append((r.spawn[0] // 16, r.spawn[1] // 16))
    for (x, y) in starts:
        if not passable(x, y):
            problems.append(f"{r.key}: célula de entrada ({x},{y}) é sólida")
    seen = reach.flood(passable, starts[0], loadout)
    for i, d in enumerate(r.doors):
        if door_inner_cells(d.side, d.screen, wb, hb)[0] not in seen:
            problems.append(f"{r.key}: porta {i} ({d.side}{d.screen} -> {d.to_room}) inalcançável")
    if r.spawn and (r.spawn[0] // 16, r.spawn[1] // 16) not in seen:
        problems.append(f"{r.key}: spawn não alcança as portas")
    return problems, seen


def reach_on_foot(r, grid_of, loadout) -> tuple[list[str], set]:
    """No Space Jump: from every entry (each door and the spawn) every door must be reachable;
    a fall can be one-way, so the first entry alone is not enough, and no place she can get to may
    leave her with no way back to any door (a pit: softlock, specs/07j). The returned set (stands
    reached from the first entry) feeds the save/map station and ship checks. `grid_of(loadout)`
    gives the room's grid for a loadout (the bomb blocks depend on the Bombs).

    Doors behind geometry (DoorLink.ledge, tallon/rooms.py GEOMETRY; specs/07k, 07m, 09d): an entry
    through such a door walks with the foot geometry of its gate too (the Tallon Canyon's Gully door:
    Samus comes down it with the Morph Ball and the Bombs); a door behind geometry items the walk does not
    have stays out of reach from every entry that is not behind the same geometry (a Space Jump ledge on
    foot; the Gully's Morph Ball tunnel without the ball and the Bombs), and a door whose geometry the
    walk has must be reached (the Vent C bulkhead with the suit; the tunnel with the ball and the Bombs)."""
    problems, first = [], None

    def geometry(d) -> frozenset:
        return d.gate & tallon_rooms.GEOMETRY if d.ledge else frozenset()

    entries = [(f"porta {i} ({d.side}{d.screen})", d, geometry(d)) for i, d in enumerate(r.doors)]
    if r.spawn:
        entries.append(("spawn", None, frozenset()))
    # specs/12e: an elevator is one more way in (she arrives standing on its platform) and out (from every entry she must
    # get onto the platform, and nothing may leave her without a way back to a door or to it)
    pad = elevator_stands(r)
    if r.elevator:
        entries.append(("elevador", "elevador", frozenset()))
    for name, entry, behind in entries:
        walk = with_items(loadout, behind & FOOT_GEOMETRY)
        grid = grid_of(walk)
        start = (min(pad) if entry == "elevador" and all(grid.stands(*s) for s in pad) else None if entry == "elevador"
                 else reach.door_entry(grid, entry.side, entry.screen) if entry is not None
                 else grid.land(r.spawn[0] // 16, r.spawn[1] // 16))
        if start is None:
            problems.append(f"{r.key}: entrada {name} sem lugar para a Samus ficar de pé")
            continue
        seen = reach.reach(grid, [start], walk)
        if first is None:
            first = seen
        walk_has = loadout_items(walk)
        for i, d in enumerate(r.doors):
            reached = reach.door_reached(grid, d.side, d.screen, seen, walk)
            need = geometry(d) - walk_has
            if need and geometry(d) != behind:
                if reached:
                    problems.append(f"{r.key}: porta {i} ({d.side}{d.screen} -> {d.to_room}) tem trava "
                                    f"{sorted(geometry(d))} mas é alcançável sem {sorted(need)} a partir "
                                    f"da entrada {name}")
            elif not reached and not need:
                problems.append(f"{r.key}: porta {i} ({d.side}{d.screen} -> {d.to_room}) inalcançável "
                                f"a partir da entrada {name}")
        if pad and not pad & seen:
            problems.append(f"{r.key}: a plataforma do elevador fica fora de alcance a partir da entrada {name}")
        stuck = reach.stuck(grid, seen, [(d.side, d.screen) for d in r.doors], walk, pad)
        if stuck and (r.doors or pad):
            x, y = min(s[:2] for s in stuck)
            problems.append(f"{r.key}: {len(stuck)} lugares sem volta a nenhuma porta a partir da entrada "
                            f"{name} (ex.: coluna {x}, pé na linha {y})")
        # specs/09d: each foot geometry item of a gate is needed on its own (the tunnel's bomb blocks hold
        # without the Bombs, its height without the Morph Ball): with all the others, still out of reach
        for i, d in enumerate(r.doors):
            foot = geometry(d) & FOOT_GEOMETRY
            if behind == geometry(d) or not foot or foot & loadout_items(loadout):
                continue
            for item in sorted(foot):
                less = with_items(loadout, ((foot - {item}) | behind) & FOOT_GEOMETRY)
                less_grid = grid_of(less)
                if reach.door_reached(less_grid, d.side, d.screen, reach.reach(less_grid, [start], less), less):
                    problems.append(f"{r.key}: porta {i} ({d.side}{d.screen} -> {d.to_room}) tem trava "
                                    f"{sorted(geometry(d))} mas é alcançável sem {item} a partir da entrada {name}")
    return problems, first or set()


STATE_BG = 22          # library-background list pointer in a state header ($8F)
TILESET_TABLE = 0x8FE7A7


def fixed_blobs(rom, base) -> tuple[list[tuple[str, int, int]], list[str]]:
    """The blobs the build puts in its fixed allocator, found through the ROM's own pointers:
    (label, SNES address, size), and problems with their contents (contents of the Queen and
    "TALLON IV" graphics are check_queen_art's and ending.check_rom's)."""
    blobs, problems = [], []

    def compressed(label: str, addr: int) -> bytes | None:
        try:
            out, n = decompress(rom.data, snes_to_pc(addr))
        except (CompressionError, IndexError, ValueError) as e:
            problems.append(f"{label} em ${addr:06X}: não descomprime ({e})")
            return None
        blobs.append((label, addr, n))
        return out

    recolored = {}
    for area in AREAS:
        if area.palette_rows:
            recolored.setdefault(area.tileset, area.palette_rows)
    for tileset, rows in sorted(recolored.items()):
        entry = 0x8F0000 | rom.u16(TILESET_TABLE + 2 * tileset)
        vanilla = decompress(base.data, snes_to_pc(base.u24((0x8F0000 | base.u16(TILESET_TABLE + 2 * tileset)) + 6)))[0]
        got = compressed(f"paleta do tileset {tileset}", rom.u24(entry + 6))
        want = recolor(vanilla, rows)
        if tileset == beamdoors.PAINT_TILESET:   # specs/10d: + the purple wave door's line
            want = beamdoors.paint_palette(want)
        if got is not None and got != want:
            problems.append(f"paleta do tileset {tileset} em ${rom.u24(entry + 6):06X} não é a recolorida"
                            + (" com a linha da porta de onda" if tileset == beamdoors.PAINT_TILESET else ""))
    # specs/10d: tileset 4's own metatile table = the vanilla one with the purple wave door's 8 metatiles
    t = beamdoors.PAINT_TILESET
    entry, base_entry = 0x8F0000 | rom.u16(TILESET_TABLE + 2 * t), 0x8F0000 | base.u16(TILESET_TABLE + 2 * t)
    got = compressed(f"metatiles do tileset {t}", rom.u24(entry))
    if got is not None and got != beamdoors.paint_vertical(base, beamdoors.paint_table(   # specs/18i: + the vertical door's
            base, decompress(base.data, snes_to_pc(base.u24(base_entry)))[0])):
        problems.append(f"metatiles do tileset {t} em ${rom.u24(entry):06X} diferentes dos vanilla + os da porta de onda")
    compressed(f"Parasite Queen (tileset {queen_art.TILESET})", rom.u24(queen_art.tileset_entry(rom) + 3))
    compressed("cena de Ceres (TALLON IV)", ending.escape_gfx_pointer(rom))
    compressed("logo do título (METROID PRIME)", title.gfx_pointer(rom))   # specs/16 (contents: title.check_logo)
    # specs/12d: tileset $0C's sandstone palette (contents: check_ruins_in_rom)
    compressed(f"paleta do tileset {ruins.RUINS_TILESET:02X} (ruínas)", rom.u24(ruins.entry(rom) + 6))
    # specs/12f: its metatile table with the purple wave door's metatiles (contents: check_ruins_in_rom)
    compressed(f"metatiles do tileset {ruins.RUINS_TILESET:02X} (ruínas)", rom.u24(ruins.entry(rom)))
    # specs/17d: the Magmoor's two palettes and the metatile table they share (contents: check_lava_in_rom)
    for t in lava.TILESETS:
        compressed(f"paleta do tileset {t:02X} (Magmoor)", rom.u24(lava.entry(rom, t) + 6))
    compressed("metatiles dos tilesets 09/0A (Magmoor)", rom.u24(lava.entry(rom, lava.HOT_TILESET)))

    return blobs, problems


def hangar_star_blobs(rom, manifest) -> tuple[list[tuple[str, int, int]], list[str]]:
    """The hangar's library background (tools/frigate/space.py): its DMAs, with their bytes checked."""
    want = {space.STAR_VRAM: ("estrelas do hangar (tiles)", space.star_tiles()),
            space.BG2_TILEMAP_VRAM: ("estrelas do hangar (mapa)", space.star_tilemap())}
    blobs, problems, seen = [], [], set()
    for st in manifest[build.HANGAR_ROOM]["states"]:
        at = 0x8F0000 | rom.u16(st + STATE_BG)
        while (op := rom.u16(at)) != 0:
            if op != 2:
                problems.append(f"hangar: comando {op} na lista de fundo ${at:06X} (só DMA, 2, esperado)")
                break
            src, dst, size = rom.u24(at + 2), rom.u16(at + 5), rom.u16(at + 7)
            at += 9
            if dst not in want:
                problems.append(f"hangar: DMA para a VRAM ${dst:04X} inesperado")
                continue
            label, payload = want[dst]
            if (label, src) not in seen:
                seen.add((label, src))
                blobs.append((label, src, size))
            if size != len(payload) or bytes(rom.data[snes_to_pc(src):snes_to_pc(src) + size]) != payload:
                problems.append(f"{label} em ${src:06X}: bytes diferentes de tools/frigate/space.py")
        missing = {lb for lb, _ in want.values()} - {lb for lb, _ in seen}
        if missing:
            problems.append(f"hangar: lista de fundo sem {sorted(missing)}")
    return blobs, problems


# specs/20b: what the Impact Crater (epic 20, 12 rooms) still needs in the two room-data banks, measured in specs/20a
# (upper ends: ~700-1050 bytes of headers/states/lists in $8F, ~200 of enemy populations in $A1)
IMPACT_ROOMS = 12
IMPACT_NEED_8F = 1050
IMPACT_NEED_A1 = 200
IMPACT_KEY_PREFIX = "impact_"


def bank_tail_free(lo: int, hi: int, used: set[int]) -> int:
    """Bytes after the last used one in [lo, hi] (the allocators are bump allocators: only the tail is free)."""
    inside = [a for a in used if lo <= a <= hi]
    return hi - max(inside) if inside else hi - lo + 1


def ff_tail_free(rom, lo: int, hi: int) -> int:
    """Bytes of $FF at the end of [lo, hi] (the free ranges start as $FF; the build writes from lo up)."""
    n = 0
    while hi - n >= lo and rom.u8(hi - n) == 0xFF:
        n += 1
    return n


def check_impact_space(rom, manifest, verbose: bool = True) -> list[str]:
    """specs/20b, built ROM: the free bytes left for the Impact Crater in $8F (build.FREE_8F tail plus the tails of
    build.RECLAIMED_8F) and in $A1 (build.FREE_A1 tail plus the tails of build.RECLAIMED_A1) cover what its rooms not yet
    built still need (IMPACT_NEED_* scaled by the rooms left; a room is built once a manifest key starts with
    IMPACT_KEY_PREFIX)."""
    problems: list[str] = []
    ours = {v["header"] & 0xFFFF for v in manifest.values() if isinstance(v, dict) and "header" in v}
    used = set().union(*(roomgraph.byte_set(roomgraph.structures(rom, h)) for h in ours))
    used |= {a + k for a in item_arena_doors(rom) for k in range(6)}
    built = sum(1 for k in manifest if k.startswith(IMPACT_KEY_PREFIX))
    left = max(IMPACT_ROOMS - built, 0)
    parts = []
    for bank, free, ranges, need_all in (("$8F", build.FREE_8F, build.RECLAIMED_8F, IMPACT_NEED_8F),
                                         ("$A1", build.FREE_A1, build.RECLAIMED_A1, IMPACT_NEED_A1)):
        main = ff_tail_free(rom, *free)
        tails = [bank_tail_free(lo, hi, used) for lo, hi in ranges]
        have = main + sum(tails)
        need = -(-need_all * left // IMPACT_ROOMS)
        if have < need:
            problems.append(f"impact crater (specs/20b): {bank} livre {have} bytes, as {left} salas por construir pedem ~{need}")
        parts.append(f"{bank} livre {have} (principal {main}, faixas recuperadas {sum(tails)}) para ~{need}")
    if verbose:
        print(f"impact crater (specs/20b): {'; '.join(parts)}; {left} de {IMPACT_ROOMS} salas por construir")
    return problems


def check_banks(rom, base, manifest, verbose: bool = True) -> list[str]:
    """specs/09c: the two expanded-bank allocators (build.LEVEL_BANKS, build.FIXED_BANKS) in a built ROM."""
    problems = []
    ranges = {"nível": build.LEVEL_BANKS, "fixo": build.FIXED_BANKS}
    pc_range = {k: (snes_to_pc(a), snes_to_pc(b) + 1) for k, (a, b) in ranges.items()}
    (a0, a1), (b0, b1) = pc_range.values()
    if a0 < b1 and b0 < a1:
        problems.append(f"alocadores nível ${build.LEVEL_BANKS[0]:06X}-${build.LEVEL_BANKS[1]:06X} e fixo "
                        f"${build.FIXED_BANKS[0]:06X}-${build.FIXED_BANKS[1]:06X} se sobrepõem")
    header_size = 1024 << base.data[0x7FD7]
    for k, (lo, hi) in pc_range.items():
        if lo < len(base.data):
            problems.append(f"alocador {k} começa dentro da ROM base (${pc_to_snes(lo):06X} < {len(base.data):#x})")
        if hi > len(rom.data) or hi > header_size:
            problems.append(f"alocador {k} passa do fim da ROM ({len(rom.data):#x} bytes, cabeçalho {header_size:#x})")

    def inside(label: str, addr: int, size: int, k: str) -> None:
        lo, hi = pc_range[k]
        try:
            pc = snes_to_pc(addr)
        except ValueError:
            pc = -1
        if not (lo <= pc and pc + size <= hi):
            problems.append(f"{label} em ${addr:06X} ({size} bytes) fora do alocador {k}")

    levels = []
    for area, r in all_rooms():
        m = manifest.get(r.key)
        if m is None:
            problems.append(f"{r.key}: fora do manifest.json da ROM construída (reconstruir)")
            continue
        want = r.level().compressed()
        for addr in sorted({rom.u24(st) for st in m["states"]}):   # what the game reads
            if addr != m["level"][0] or len(want) != m["level"][1]:
                problems.append(f"{r.key}: nível em ${addr:06X} ({len(want)} bytes), o manifest diz "
                                f"${m['level'][0]:06X} ({m['level'][1]})")
            inside(f"nível de {r.key}", addr, len(want), "nível")
            pc = snes_to_pc(addr) if addr & 0x8000 else 0
            if bytes(rom.data[pc:pc + len(want)]) != want:
                problems.append(f"{r.key}: bytes do nível em ${addr:06X} não são os da sala")
            levels.append((f"nível de {r.key}", addr, len(want)))
    fixed, more = fixed_blobs(rom, base)
    stars, star_problems = hangar_star_blobs(rom, manifest)
    problems += more + star_problems
    fixed += stars
    for label, addr, size in fixed:
        inside(label, addr, size, "fixo")
        if (addr & 0xFFFF) + size - 1 > 0xFFFF:
            problems.append(f"{label} em ${addr:06X} ({size} bytes) cruza o banco")
    spans = sorted((snes_to_pc(a), snes_to_pc(a) + n, label) for label, a, n in levels + fixed)
    for (s0, e0, l0), (s1, e1, l1) in zip(spans, spans[1:]):
        if s1 < e0:
            problems.append(f"{l0} (${pc_to_snes(s0):06X}-${pc_to_snes(e0 - 1):06X}) e {l1} "
                            f"(${pc_to_snes(s1):06X}) se sobrepõem")
    if verbose:
        for k, blobs in (("nível", levels), ("fixo", fixed)):
            lo, hi = pc_range[k]
            ends = [snes_to_pc(a) + n for _, a, n in blobs]
            last = max(ends, default=lo)
            print(f"bancos: alocador {k} ${ranges[k][0]:06X}-${ranges[k][1]:06X}: {len(blobs)} blobs, "
                  f"{sum(n for _, _, n in blobs)} bytes, livres {hi - last} depois do último")
        crossing = build.crossings(levels)
        print("bancos: " + ("; ".join(f"AVISO {label} cruza banco (${a:06X} + {n})" for label, a, n in crossing)
                            if crossing else "nenhum nível cruza banco"))
    return problems


def check_queen_art(built) -> list[str]:
    return queen_art.check(Rom.load(BASE_ROM), built)


STEP = {"L": (-1, 0), "R": (1, 0), "T": (0, -1), "B": (0, 1)}


def door_map_cell(r, d) -> tuple[int, int]:
    sx, sy = {"L": (0, d.screen), "R": (r.width - 1, d.screen),
              "T": (d.screen, 0), "B": (d.screen, r.height - 1)}[d.side]
    return r.map_x + sx, r.map_y + sy


def check_map(by_key: dict) -> list[str]:
    problems = []
    for r in by_key.values():
        if pausemap.out_of_bounds(r):
            problems.append(f"{r.key}: fora da grade do mapa de pausa")
        for d in r.doors:
            x, y = door_map_cell(r, d)
            dx, dy = STEP[d.side]
            other = by_key.get(d.to_room)
            if other is None:
                continue   # reported by check_area
            if door_map_cell(other, other.doors[d.to_door]) != (x + dx, y + dy):
                problems.append(f"{r.key}: porta {d.side}{d.screen} -> {d.to_room} não encosta na vizinha no mapa")
    return problems


DOOR_CLEARANCE = 5  # blocks between an enemy and a door, so nothing camps the doorway

# Enemy sets (specs/07i). Enemy tiles go to VRAM $7000-$7FFF one species after the other
# (LoadEnemyGfxToVram $82:DFD1; ProcessEnemyTilesets $A0:8D64 copies them through WRAM $7E:7800-$97FF);
# in the area of the escape timer its digits sit at $7E00 (research/sm_room_format.md §13), so the
# sets there stop before them. Palette slots: the ones every vanilla enemy set uses (lines 9-11, 15).
ENEMY_VRAM, TIMER_AREA_ENEMY_VRAM = 0x2000, 0x1C00
ENEMY_PALETTE_SLOTS = {1, 2, 3, 7}
MAX_ENEMY_SPECIES = 4                # ProcessEnemyTilesets fills 4-entry arrays
# fairness of the Tallon's arrival tier (Power Beam only, 99 energy): every enemy there dies to the
# uncharged Power Beam (20 a shot: tallon_power_beam_mata_inimigo sees 60 -> 40) in a few shots
# and a touch takes at most a fifth of the energy
POWER_BEAM_DAMAGE, FAIR_SHOTS, FAIR_TOUCH = 20, 5, 20
_base_rom = None


def base_rom() -> Rom:
    global _base_rom
    if _base_rom is None:
        _base_rom = Rom.load(BASE_ROM)
    return _base_rom


def species_info(ptr: int) -> dict[str, int]:
    """Fields of an enemy species header ($A0, vendor EnemyDef) and its Power Beam multiplier: the
    vulnerability table's first byte ($B4; header +$3C, 0 = the default table $B4:EC1C) & $7F, a shot
    taking (damage >> 1) x multiplier; $FF only freezes (vendor/sm/src/sm_a0.c:2771, 2720). specs/14a: a species copy
    (tools/chozo/bosses.py COPIES, not in the base ROM) is its source's header with the copy's touch damage (specs/18g: and health, if it sets one) (check_bosses
    checks the built ROM's bytes against that)."""
    copy = chozo_bosses.COPIES.get(ptr)
    rom, at = base_rom(), 0xA00000 | (copy.source if copy else ptr)
    vuln = rom.u8(0xB40000 | (rom.u16(at + 0x3C) or 0xEC1C))
    if copy and copy.vulnerability is not None:   # specs/18l: a copy's own table (check_species_copies: its shot AI uses it)
        vuln = copy.vulnerability[0]
    hp = copy.health if copy and copy.health is not None else rom.u16(at + 4)   # specs/18g: a copy's own health
    damage = copy.damage if copy else rom.u16(at + 6)
    if at & 0xFFFF == METROID_SOURCE:   # specs/18l: the Metroid's own AI ignores its table and header damage (sm_a3.c:2984, 3042)
        if not (copy and copy.shot == chozo_bosses.METROID_SHOT):
            vuln = 0          # Metroid_Shot: a beam only knocks it back (unfrozen), only missiles hurt it frozen
        if not (copy and copy.touch == NORMAL_TOUCH_A3):
            damage = DRAIN    # Metroid_Touch: it latches on and drains every frame until a bomb shakes it off
    return {"tiles": rom.u16(at), "hp": hp, "damage": damage,
            "x_radius": rom.u16(at + 8), "y_radius": rom.u16(at + 10), "power": 0 if vuln == 0xFF else vuln & 0x7F}


# specs/18l: the SM's Metroid ($A0:DD7F) and what makes a copy of it fair (tools/chozo/bosses.py METROID): the common touch AI of
# its bank ($A3:8023, Enemy_NormalTouchAI_A3: the header's damage) instead of the latch; DRAIN = no ceiling per touch
METROID_SOURCE, NORMAL_TOUCH_A3, DRAIN = 0xDD7F, 0x8023, 0xFFFF
METROID_SPEED = 3   # specs/18l: Metroid_Func_1 ($A3:EC11) clamps its speed to 3 px a frame on each axis (read in sm_a3.c:2848)


def check_enemies(r, enemies: dict, passable, wb: int, hb: int) -> list[str]:
    """Each enemy's whole hitbox (radii from its species header in the ROM) is open air inside the
    room, it stands on solid ground, away from the doors; a walking one (Species.patrol, specs/07m)
    keeps all that over its whole walk: open air for its hitbox and ground under every column."""
    problems = []
    for e in enemies.get(r.key, []):
        tag = f"{r.key}: {e.kind} em ({e.x},{e.floor})"
        info = species_info(e.species.ptr)
        cx, cy = e.pixel_pos()
        xr, yr, walk, bob = info["x_radius"], info["y_radius"], e.species.patrol, e.species.bob
        cols = range((cx - walk - xr) // 16, (cx + walk + xr - 1) // 16 + 1)   # its hitbox, as it walks
        centre = range((cx - walk) // 16, (cx + walk) // 16 + 1)              # the column it stands in
        # specs/12i: a floater's hitbox over its whole bob up and down
        body = [(x, y) for x in cols for y in range((cy - yr - bob) // 16, (cy + yr + bob - 1) // 16 + 1)]
        what = "anda" if walk else "nasce"
        if not all(0 <= x < wb and 0 <= y < hb for x, y in body):
            problems.append(f"{tag} fica fora da sala")
        elif not all(passable(x, y) for x, y in body):
            problems.append(f"{tag} {what} dentro da parede")
        if e.species.mount == "wall":   # specs/12i: the wall its socket is set in, beside its block
            wall_x = cx // 16 + (-1 if e.wall_side() == 0 else 1)
            if passable(wall_x, cy // 16):
                problems.append(f"{tag} não tem parede ao lado (coluna {wall_x}) para o encaixe")
        elif e.species.mount == "ceiling":   # specs/12i: hanging from the block over its hitbox
            if any(passable(x, (cy - yr) // 16 - 1) for x in centre):
                problems.append(f"{tag} não tem teto em cima")
        elif e.species.fixed:   # specs/14c: put by its own code (the Spore Spawn hangs from its stalk): no ground
            pass
        elif any(passable(x, e.floor) for x in centre):
            problems.append(f"{tag} não tem chão embaixo" + (f" em todo o caminho (colunas {centre.start}-{centre.stop - 1})" if walk else ""))
        for i, d in enumerate(r.doors):
            dx, dy = door_inner_cells(d.side, d.screen, wb, hb)[0]
            if max(min(abs(dx - x) for x in centre), abs(dy - (e.floor - 1))) < DOOR_CLEARANCE:
                problems.append(f"{tag} está colado na porta {i} ({d.side}{d.screen})")
    return problems


def check_enemy_sets(area) -> list[str]:
    """specs/07i: each room's enemy set fits the engine: at most 4 species, one palette slot each
    (a vanilla enemy slot), tiles loaded one after the other (no fixed VRAM placement) within the
    enemy VRAM ($2000 bytes; $1C00 in the area of the escape timer), each species' height in
    tools/frigate/enemies.py = its header's y radius (the spawn's y depends on it), and no enemy in
    the gunship's room (the ship takes that VRAM)."""
    problems = []
    limit = TIMER_AREA_ENEMY_VRAM if area.boss_room else ENEMY_VRAM
    by_key = area.by_key()
    for key, spawns in area.enemies.items():
        species = sorted({s.kind: s.species for s in spawns}.items())
        tag = f"{key}: enemy set {[k for k, _ in species]}"
        try:   # one entry per species: kinds sharing one share its palette (specs/07m)
            entries = set_species(spawns)
        except ValueError as e:
            problems.append(f"{tag}: {e}")
            continue
        if len(entries) > MAX_ENEMY_SPECIES:
            problems.append(f"{tag} tem {len(entries)} espécies (máximo {MAX_ENEMY_SPECIES})")
        slots = [pal for _, pal in entries]
        if len(set(slots)) != len(slots) or not set(slots) <= ENEMY_PALETTE_SLOTS:
            problems.append(f"{tag}: paletas {slots} (uma por espécie, entre {sorted(ENEMY_PALETTE_SLOTS)})")
        tiles = [species_info(ptr)["tiles"] for ptr, _ in entries]
        if any(t & 0x8000 for t in tiles):
            problems.append(f"{tag}: espécie com lugar fixo na VRAM")
        elif sum(tiles) > limit:
            problems.append(f"{tag}: ${sum(tiles):04X} bytes de VRAM de inimigos, cabem ${limit:04X}")
        for k, sp in species:
            if sp.height != species_info(sp.ptr)["y_radius"]:
                problems.append(f"{key}: {k} tem altura {sp.height}, o cabeçalho ${sp.ptr:04X} diz "
                                f"{species_info(sp.ptr)['y_radius']}")
        if key in by_key and by_key[key].ship and spawns:
            problems.append(f"{key}: inimigos na sala da nave (a nave ocupa a VRAM de inimigos)")
    return problems


def check_enemies_in_rom(rom) -> list[str]:
    """Built ROM (specs/07i): every state of every room with enemies points at its population
    ($A1: tools/frigate/enemies.py population) and enemy set ($B4, after the 7-byte name)."""
    manifest = json.loads((BUILT_ROM.parent / "manifest.json").read_text())
    problems = []
    for area in AREAS:
        for key, spawns in area.enemies.items():
            if key not in manifest:
                problems.append(f"{key}: fora do manifest.json da ROM construída (reconstruir)")
                continue
            try:
                pop, eset = population(spawns), enemy_set(spawns)[7:]
            except ValueError:   # more than 4 species: check_enemy_sets reports it
                continue
            arena = chozo_bosses.arena_of(key)
            for n, st in enumerate(manifest[key]["states"]):
                if n == 1 and arena:   # specs/14b: an arena's dead state, without its boss kinds
                    pop = population([e for e in spawns if not e.species.boss])
                elif n == 0 and arena and arena.condition == chozo_bosses.ITEM:   # specs/14d: alive, before the fight: the
                    pop = population([e for e in spawns if not e.species.boss])[:-1] + b"\x00"   # boss kinds spawn later
                if (rom.read(0xA10000 | rom.u16(st + 8), len(pop)) != pop
                        or rom.read(0xB40000 | rom.u16(st + 10), len(eset)) != eset):
                    problems.append(f"{key}: estado ${st & 0xFFFF:04X} sem a população/enemy set da tabela")
    return problems


# specs/09d (epic decision 4): the enemy fairness rule covers the rooms Samus first gets into with no
# more than the Power Beam, missiles and the Morph Ball (the epic's rounds 0-1: 99 energy, no other item)
FAIR_ARRIVAL = frozenset({tallon_rooms.MISSILE, tallon_rooms.MORPH})


def check_tallon_enemies() -> list[str]:
    """specs/07i: check_layer0_enemies for the Tallon (tools/tallon/enemies.py). specs/20f: the crater's rooms, in the same
    AreaDef (area 0), have their own table (check_impact_enemies)."""
    return check_layer0_enemies(tallon_only(), tallon_enemies, "tallon")


def tallon_only():
    """specs/20f: area 0 without the Impact Crater's rooms and enemies (they share the AreaDef, specs/20e)."""
    return types.SimpleNamespace(rooms=[r for r in TALLON.rooms if not r.key.startswith(impact_rooms.PREFIX)],
                                 enemies={k: v for k, v in TALLON.enemies.items() if not k.startswith(impact_rooms.PREFIX)})


def crater_only():
    """specs/20f: area 0's Impact Crater rooms and their enemies (impact/enemies.py)."""
    return types.SimpleNamespace(rooms=[r for r in TALLON.rooms if r.key.startswith(impact_rooms.PREFIX)],
                                 enemies={k: v for k, v in TALLON.enemies.items() if k.startswith(impact_rooms.PREFIX)})


# specs/20f: in the crater the fairness rule holds in every room (the Mines' rule: the crater is entered at round 6 only, and the
# Phazon Core's climbs run along ledges and shelves)
IMPACT_FAIR_EVERY_ROUND = True


def check_impact_enemies() -> list[str]:
    """specs/20f: check_layer0_enemies for the Impact Crater's built rooms (tools/impact/enemies.py, area 0's crater rooms: at
    least one of each Prime type with a stand-in, at most Prime's layer-0 count, at most one per screen, fair in every room:
    IMPACT_FAIR_EVERY_ROUND); PRIME_LAYER0 and PRIME_INACTIVE_LAYERS only with rooms of regions A and B of the crater's table
    (C and D are Metroid Prime's fight, 20g/20h), ENEMIES only in built rooms and never in a room whose enemies Prime keeps on an
    inactive layer only; at most one per screen, screen by screen (the screen of its centre); every Prime type of PRIME_LAYER0
    decided (STAND_IN); no boss kind (Species.boss); the chasers off every
    door's camera (chaser_problems), the drifters and shooters as the Mines' (homing_problems, shooter_problems). Prints the line
    "impact crater (specs/20f)"."""
    T = impact_enemies
    crater = crater_only()
    problems = check_layer0_enemies(crater, T, "impact", every_round=IMPACT_FAIR_EVERY_ROUND)
    regions = {t.key: t.region for t in impact_rooms.TABLE}
    for name, table in (("PRIME_LAYER0", T.PRIME_LAYER0), ("PRIME_INACTIVE_LAYERS", T.PRIME_INACTIVE_LAYERS)):
        wrong = sorted(k for k in table if regions.get(k) not in ("A", "B"))
        if wrong:
            problems.append(f"impact: {name} com salas fora das regiões A e B da tabela: {wrong}")
    by_key = {r.key: r for r in crater.rooms}
    unbuilt = sorted(set(T.ENEMIES) - set(by_key))
    if unbuilt:
        problems.append(f"impact: inimigos em salas fora do build: {unbuilt}")
    inactive = sorted(k for k in T.ENEMIES if k in T.PRIME_INACTIVE_LAYERS and k not in T.PRIME_LAYER0)
    if inactive:
        problems.append(f"impact: inimigos em {inactive}, onde o Prime só os tem numa camada que não carrega")
    missing = sorted({t for v in T.PRIME_LAYER0.values() for t in v} - set(T.STAND_IN))
    if missing:
        problems.append(f"impact: tipos do Prime sem decisão (STAND_IN): {missing}")
    # specs/20h: a boss kind only in the arena's room (ARENA_ROOMS: Metroid Prime's Lair), each of its kinds of ARENA_KINDS
    bosses = sorted(k for k, v in T.ENEMIES.items() if any(e.species.boss for e in v) and k not in T.ARENA_ROOMS)
    if bosses:
        problems.append(f"impact: inimigos de chefe (Species.boss) em {bosses}, fora da arena (ARENA_ROOMS)")
    wrong = sorted({e.kind for k in T.ARENA_ROOMS for e in T.ENEMIES.get(k, []) if e.kind not in T.ARENA_KINDS})
    if wrong or not set(T.ARENA_ROOMS) <= set(T.ENEMIES):
        problems.append(f"impact: arenas {sorted(T.ARENA_ROOMS)} sem o chefe ou com {wrong} (só os de ARENA_KINDS)")
    # specs/20g: the descent's Prime layer 0 = Metroid Prime's first stage only (decision 3: the fight in the Lair): nothing there
    fight = sorted(k for k in T.ENEMIES if k in T.PRIME_FIGHT_LAYER0)
    off = sorted(k for k in T.PRIME_FIGHT_LAYER0 if regions.get(k) != "C")
    if fight or off:
        problems.append(f"impact: inimigos em {fight}, onde o Prime só tem a luta do Metroid Prime (decisão 3: só na Lair); "
                        f"PRIME_FIGHT_LAYER0 fora da região C: {off}")
    for key, spawns in T.ENEMIES.items():
        r = by_key.get(key)
        if r is None:
            continue
        # specs/20f: at most one per screen, screen by screen (check_layer0_enemies counts them against the room's screens):
        # the screen of each one's centre
        screens = collections.Counter((e.pixel_pos()[0] // 256, e.pixel_pos()[1] // 256) for e in spawns)
        crowded = sorted(sc for sc, n in screens.items() if n > 1)
        if crowded:
            problems.append(f"{key}: mais de um inimigo nas telas {crowded} (no máximo 1 por tela)")
        for e in spawns:
            if e.species.homing:
                problems += homing_problems(r, e)
            if e.species.chase:
                problems += chaser_problems(r, e)
            if e.species.fires:
                problems += shooter_problems(r, e)
    if not problems:
        rooms = {k: v for k, v in crater.enemies.items() if v}
        kinds = sorted({e.kind for v in rooms.values() for e in v})
        print(f"impact crater (specs/20f): {sum(map(len, rooms.values()))} inimigos em {len(rooms)} salas "
              f"({', '.join(f'{k} {sum(e.kind == k for v in rooms.values() for e in v)}' for k in kinds)}); camada 0 do Prime, "
              f"no máximo 1 por tela (tela a tela); justos em toda sala (até {FAIR_SHOTS} tiros do Power Beam, até {FAIR_TOUCH} por "
              f"toque); os que voam até a Samus fora da câmera de toda porta; fora (camada que não carrega no Prime): "
              + ", ".join(f"{k.removeprefix('impact_')} ({', '.join(f'{t} {n}' for t, n in sorted(v.items()))})"
                          for k, v in sorted(T.PRIME_INACTIVE_LAYERS.items()))
              + f"; a descida (specs/20g) vazia: no Prime só a luta do Metroid Prime (decisão 3: só na Lair) em "
              + ", ".join(f"{k.removeprefix('impact_')} ({', '.join(f'{t} {n}' for t, n in sorted(v.items()))})"
                          for k, v in sorted(T.PRIME_FIGHT_LAYER0.items())))
    return problems


def check_chozo_enemies() -> list[str]:
    """specs/12h: check_layer0_enemies for the Chozo (tools/chozo/enemies.py; the walk is the Tallon's and the Chozo's together,
    so a Chozo room's arrival is its round's equipment); PRIME_LAYER0's rooms are in the Chozo table. Prints the line "chozo
    (specs/12h)"."""
    problems = check_layer0_enemies(CHOZO, chozo_enemies, "chozo")
    table = {t.key for t in chozo_rooms.TABLE}
    unknown = sorted(set(chozo_enemies.PRIME_LAYER0) - table)
    if unknown:
        problems.append(f"chozo: PRIME_LAYER0 com salas fora da tabela: {unknown}")
    # specs/12j: a built room's Prime layer 0 must be decided (PRIME_LAYER0), not left in the record of the regions to come
    later = sorted(r.key for r in CHOZO.rooms if r.prime in chozo_enemies.PRIME_LAYER0_LATER)
    if later:
        problems.append(f"chozo: salas construídas com a camada 0 do Prime ainda só em PRIME_LAYER0_LATER: {later}")
    if not problems:
        # the layer-0 enemies (specs/14a: the bosses have their own line, check_bosses)
        rooms = {k: [e for e in v if not e.species.boss] for k, v in CHOZO.enemies.items()}
        rooms = {k: v for k, v in rooms.items() if v}
        kinds = sorted({e.kind for v in rooms.values() for e in v})
        print(f"chozo (specs/12h): {sum(map(len, rooms.values()))} inimigos em {len(rooms)} salas "
              f"({', '.join(f'{k} {sum(e.kind == k for v in rooms.values() for e in v)}' for k in kinds)}); camada 0 do Prime, "
              f"no máximo 1 por tela; justos na chegada (rodadas 0-1); "
              + (f"regiões {''.join(sorted(set(chozo_rooms.REGIONS) - chozo_rooms.ACTIVE_REGIONS))}: só a tabela do Prime"
                 if set(chozo_rooms.REGIONS) - chozo_rooms.ACTIVE_REGIONS else
                 "todas as regiões construídas (specs/12l: a região E não tem inimigo na camada 0 do Prime)"))
    return problems


# specs/17g: in the Magmoor the fairness rule (FAIR_SHOTS Power Beam shots, FAIR_TOUCH a touch) holds in every room whatever its
# round: lava lies under the walks (specs/17d, 17f), a knock-back can drop Samus into a pit, and the rooms are hot
MAGMOOR_FAIR_EVERY_ROUND = True


def check_magmoor_enemies() -> list[str]:
    """specs/17g: check_layer0_enemies for the Magmoor (tools/magmoor/enemies.py; the walk is the three areas' together), with
    the fairness rule in every room (MAGMOOR_FAIR_EVERY_ROUND); PRIME_LAYER0's rooms are in the Magmoor table, ENEMIES only in
    built rooms; every enemy's hitbox (over its bob and walk) above the room's lava surface (a crawler may wander into a pit later:
    every one dies to the Power Beam, so none blocks a way out for good). Prints the line "magmoor (specs/17g)"."""
    problems = check_layer0_enemies(MAGMOOR, magmoor_enemies, "magmoor", every_round=MAGMOOR_FAIR_EVERY_ROUND)
    table = {t.key for t in magmoor_rooms.TABLE}
    unknown = sorted(set(magmoor_enemies.PRIME_LAYER0) - table)
    if unknown:
        problems.append(f"magmoor: PRIME_LAYER0 com salas fora da tabela: {unknown}")
    by_key = MAGMOOR.by_key()
    unbuilt = sorted(set(magmoor_enemies.ENEMIES) - set(by_key))
    if unbuilt:
        problems.append(f"magmoor: inimigos em salas fora do build: {unbuilt}")
    for key, spawns in magmoor_enemies.ENEMIES.items():
        r = by_key.get(key)
        if r is None or r.lava is None:
            continue
        for e in spawns:
            info = species_info(e.species.ptr)
            _, cy = e.pixel_pos()
            if (cy + info["y_radius"] + e.species.bob - 1) // 16 >= r.lava:
                problems.append(f"{key}: {e.kind} em ({e.x},{e.floor}) nasce dentro da lava (superfície na linha {r.lava})")
    if not problems:
        rooms = {k: v for k, v in MAGMOOR.enemies.items() if v}
        kinds = sorted({e.kind for v in rooms.values() for e in v})
        later = sorted({magmoor_rooms.region_of(k) for k in magmoor_enemies.PRIME_LAYER0} - magmoor_rooms.ACTIVE_REGIONS)
        print(f"magmoor (specs/17g): {sum(map(len, rooms.values()))} inimigos em {len(rooms)} salas "
              f"({', '.join(f'{k} {sum(e.kind == k for v in rooms.values() for e in v)}' for k in kinds)}); camada 0 do Prime, "
              f"no máximo 1 por tela; justos em toda sala (até {FAIR_SHOTS} tiros do Power Beam, até {FAIR_TOUCH} por toque), "
              f"fora da lava" + (f"; regiões {''.join(later)}: só a tabela do Prime" if later else ""))
    return problems


# specs/18g: in Phendrana the fairness rule holds in every room whatever its round, as in the Magmoor (the walks run along ledges
# and over floor doors: a knock-back drops Samus off them), and a drifter (Species.homing) starts so far from every door that it
# can't touch Samus within spec 15's ENTRY_FRAMES of her coming in by it
PHENDRANA_FAIR_EVERY_ROUND = True
ENTRY_FRAMES = 120            # spec 15: no damage in the first 120 frames of a real door entry
ENTRY_REACH = 2               # blocks past the door's inner cells where she may stand as she comes in (emulator: the Ice Ruins
                              # Access' R0, an orb 4 blocks from the cells touched her 90 frames after she arrived)
COMMON_SPEEDS = 0xA28187      # kCommonEnemySpeeds_Linear: entry n = 8 bytes (whole px, subpixel, then the negative pair)


def homing_speed(sp) -> float:
    """A drifter's speed, px a frame on each axis: entry param2 of the common speed table (base ROM; WreckedShipOrbs_Init
    $A8:E388 reads it so)."""
    at = COMMON_SPEEDS + 8 * sp.param2
    return base_rom().u16(at) + base_rom().u16(at + 2) / 0x10000


def homing_problems(r, e) -> list[str]:
    """specs/18g: a drifter `e` of room `r` against every door: Samus stands in the door's inner cells (or up to ENTRY_REACH
    blocks further in) when she comes in; the drifter closes in on her on each axis at homing_speed, so it touches her no sooner than (the larger axis gap between the
    hitboxes) / speed frames; that must be over ENTRY_FRAMES (it may run from the first frame: on camera)."""
    out = []
    info = species_info(e.species.ptr)
    speed = homing_speed(e.species)
    cx, cy = e.pixel_pos()
    wb, hb = r.width * 16, r.height * 16
    for i, d in enumerate(r.doors):
        cells = door_inner_cells(d.side, d.screen, wb, hb)
        ix, iy = {"L": (1, 0), "R": (-1, 0), "T": (0, 1), "B": (0, -1)}[d.side]   # into the room
        cells += [(x + ix * k, y + iy * k) for x, y in cells for k in range(1, ENTRY_REACH + 1)]
        xs, ys = [x * 16 for x, _ in cells], [y * 16 for _, y in cells]
        sx0, sx1, sy0, sy1 = min(xs), max(xs) + 16, min(ys), max(ys) + 16   # where she can be standing in the doorway
        gap_x = max(0, max(sx0 - (cx + info["x_radius"]), (cx - info["x_radius"]) - sx1))
        gap_y = max(0, max(sy0 - (cy + info["y_radius"]), (cy - info["y_radius"]) - sy1))
        gap = max(gap_x, gap_y)
        if speed and gap < speed * ENTRY_FRAMES:
            out.append(f"{r.key}: {e.kind} em ({e.x},{e.floor}) vai até a Samus na porta {i} ({d.side}{d.screen}) em "
                       f"{gap / speed:.0f} quadros ({gap} px a {speed:g} px por quadro; mínimo {ENTRY_FRAMES})")
    return out


CAMERA_SLACK = 32   # specs/18l: px the camera may sit off the door's screen as she comes in and stands (the scroll's lead)


def chaser_problems(r, e) -> list[str]:
    """specs/18l: a chaser `e` of room `r` (Species.chase: it flies at Samus at up to `chase` px a frame, only while the game
    runs it, i.e. while its hitbox is in the camera's window, sm_a0.c:578: x within its width of the 256 px, y from 8 over to
    248 under the camera's top) against every door: as she comes in by it and stands, the camera shows the door's screen
    (CAMERA_SLACK px either way); in that window it reaches her no sooner than (the larger axis gap between the hitboxes, as
    homing_problems) / chase frames, which must be over ENTRY_FRAMES (at 3 px a frame never within one screen: so it must start
    off the camera of every door's screen; walls, which stop it, are not counted)."""
    out = []
    info = species_info(e.species.ptr)
    cx, cy = e.pixel_pos()
    wb, hb = r.width * 16, r.height * 16
    for i, d in enumerate(r.doors):
        sx, sy = {"L": (0, d.screen), "R": (r.width - 1, d.screen), "T": (d.screen, 0), "B": (d.screen, r.height - 1)}[d.side]
        cam_x, cam_y = sx * 256, sy * 256
        if not (cam_x - CAMERA_SLACK - info["x_radius"] <= cx <= cam_x + CAMERA_SLACK + 256 + info["x_radius"]
                and cam_y - CAMERA_SLACK - 8 <= cy <= cam_y + CAMERA_SLACK + 248):
            continue   # off the camera: it does not move until she goes on into the room
        cells = door_inner_cells(d.side, d.screen, wb, hb)
        ix, iy = {"L": (1, 0), "R": (-1, 0), "T": (0, 1), "B": (0, -1)}[d.side]
        cells += [(x + ix * k, y + iy * k) for x, y in cells for k in range(1, ENTRY_REACH + 1)]
        xs, ys = [x * 16 for x, _ in cells], [y * 16 for _, y in cells]
        sx0, sx1, sy0, sy1 = min(xs), max(xs) + 16, min(ys), max(ys) + 16
        gap = max(0, sx0 - (cx + info["x_radius"]), (cx - info["x_radius"]) - sx1,
                  sy0 - (cy + info["y_radius"]), (cy - info["y_radius"]) - sy1)
        if gap < e.species.chase * ENTRY_FRAMES:
            out.append(f"{r.key}: {e.kind} em ({e.x},{e.floor}) na câmera da porta {i} ({d.side}{d.screen}) quando a Samus "
                       f"entra: vai até ela em {gap / e.species.chase:.0f} quadros ({gap} px a {e.species.chase:g} px por "
                       f"quadro; mínimo {ENTRY_FRAMES})")
    return out


def check_phendrana_enemies() -> list[str]:
    """specs/18g: check_layer0_enemies for Phendrana (tools/phendrana/enemies.py; the walk is the four areas' together), with the
    fairness rule in every room (PHENDRANA_FAIR_EVERY_ROUND); PRIME_LAYER0's rooms are in Phendrana's table, ENEMIES only in
    built rooms; the rooms of a boss' arena (ARENA_ROOMS: the epic's boss rooms, EPIC_PHENDRANA_BOSS_ROOMS) get no layer-0
    stand-in (their child places the fight; specs/18h: once it did, only the arena's kinds, Species.boss, there, each a stand-in
    of a Prime type of the room, ARENA_KINDS, at least one of each and at most Prime's count, and the room an arena of
    tools/chozo/bosses.py ARENAS); every Prime type of the table is decided (STAND_IN) or proposed (PROPOSED_LATER),
    a proposal that is a kind of ours is fair; a drifter can't reach a door within ENTRY_FRAMES (homing_problems). Prints the
    line "phendrana (specs/18g)"."""
    T = phendrana_enemies
    arenas = set(T.ARENA_ROOMS)
    table = types.SimpleNamespace(STAND_IN=T.STAND_IN, PRIME_OF=T.PRIME_OF,
                                  PRIME_LAYER0={k: v for k, v in T.PRIME_LAYER0.items() if k not in arenas})
    problems = check_layer0_enemies(PHENDRANA, table, "phendrana", every_round=PHENDRANA_FAIR_EVERY_ROUND)
    keys = {t.key for t in phendrana_rooms.TABLE}
    unknown = sorted(set(T.PRIME_LAYER0) - keys)
    if unknown:
        problems.append(f"phendrana: PRIME_LAYER0 com salas fora da tabela: {unknown}")
    by_key = PHENDRANA.by_key()
    unbuilt = sorted(set(T.ENEMIES) - set(by_key))
    if unbuilt:
        problems.append(f"phendrana: inimigos em salas fora do build: {unbuilt}")
    stray = sorted(k for k, v in T.ENEMIES.items() if k not in arenas and any(e.species.boss for e in v))   # specs/18k
    if stray:
        problems.append(f"phendrana: inimigos de arena (Species.boss) em salas fora de ARENA_ROOMS: {stray}")
    for key, child in sorted(T.ARENA_ROOMS.items()):
        if EPIC_PHENDRANA_BOSS_ROOMS.get(key) != child:
            problems.append(f"phendrana: ARENA_ROOMS {key} ({child}) não é sala de chefe do épico {EPIC_PHENDRANA_BOSS_ROOMS}")
        spawns = T.ENEMIES.get(key, [])
        if not spawns:
            continue
        # specs/18h: the arena built: only its kinds, the stand-ins of the room's Prime types, within Prime's counts
        if chozo_bosses.arena_of(key) is None:
            problems.append(f"{key}: inimigos na sala de uma arena que não está em ARENAS ({child} põe a luta)")
        layer0 = {**T.PRIME_LAYER0.get(key, {}), **T.PRIME_BOSS_LAYERS.get(key, {})}   # specs/18k: a boss of a later layer
        got = collections.Counter(T.ARENA_KINDS.get(e.kind) for e in spawns)
        for e in spawns:
            if not e.species.boss or e.kind not in T.ARENA_KINDS:
                problems.append(f"{key}: {e.kind} na sala da arena sem ser um tipo dela (Species.boss, ARENA_KINDS)")
        for prime, n in sorted(layer0.items()):
            if not 1 <= got.get(prime, 0) <= n:
                problems.append(f"{key}: {got.get(prime, 0)} {prime} na arena (Prime: {n}; ao menos 1)")
        extra = sorted(set(got) - set(layer0) - {None})
        if extra:
            problems.append(f"{key}: tipos {extra} na arena que o Prime não tem na sala")
    types_ = {t for k, v in T.PRIME_LAYER0.items() if k not in arenas for t in v}   # an arena's: its boss child
    missing = sorted(types_ - set(T.STAND_IN) - set(T.PROPOSED_LATER))
    if missing:
        problems.append(f"phendrana: tipos do Prime sem decisão nem proposta (STAND_IN/PROPOSED_LATER): {missing}")
    both = sorted(set(T.STAND_IN) & set(T.PROPOSED_LATER))
    if both:
        problems.append(f"phendrana: tipos decididos e ainda em PROPOSED_LATER: {both}")
    for key, spawns in T.ENEMIES.items():
        r = by_key.get(key)
        if r is None:
            continue
        for e in spawns:
            if e.species.homing:
                problems += homing_problems(r, e)
            if e.species.chase:   # specs/18l
                problems += chaser_problems(r, e)
            copy = chozo_bosses.COPIES.get(e.species.ptr)
            if (copy.source if copy else e.species.ptr) == METROID_SOURCE and e.species.chase < METROID_SPEED:
                problems.append(f"{key}: {e.kind} é um Metroid (voa até a Samus a {METROID_SPEED} px por quadro, Metroid_Func_1 "
                                f"$A3:EC11) e a espécie diz chase {e.species.chase:g}: a regra da câmera não o confere")
    if not problems:
        rooms = {k: [e for e in v if not e.species.boss] for k, v in PHENDRANA.enemies.items()}   # specs/18h: layer 0's
        rooms = {k: v for k, v in rooms.items() if v}
        kinds = sorted({e.kind for v in rooms.values() for e in v})
        later = sorted({phendrana_rooms.region_of(k) for k in T.PRIME_LAYER0} - phendrana_rooms.ACTIVE_REGIONS)
        drifters = sorted({homing_speed(e.species) for v in rooms.values() for e in v if e.species.homing})
        arenas_later = ", ".join(f"{k.removeprefix('phendrana_')} ({c}" + (": construída" if T.ENEMIES.get(k) else "") + ")"
                                 for k, c in T.ARENA_ROOMS.items())
        print(f"phendrana (specs/18g): {sum(map(len, rooms.values()))} inimigos em {len(rooms)} salas "
              f"({', '.join(f'{k} {sum(e.kind == k for v in rooms.values() for e in v)}' for k in kinds)}); camada 0 do Prime, "
              f"no máximo 1 por tela; justos em toda sala (até {FAIR_SHOTS} tiros do Power Beam, até {FAIR_TOUCH} por toque); "
              f"os que vêm até a Samus ({', '.join(f'{v:g}' for v in drifters)} px por quadro) a mais de {ENTRY_FRAMES} quadros de "
              f"toda porta; arenas: {arenas_later}"
              + (f"; specs/18l: os que voam até ela na câmera ({', '.join(sorted({f'{e.species.chase:g}' for v in rooms.values() for e in v if e.species.chase}))} px por quadro, os Metroids) fora da câmera de toda porta"
                 if any(e.species.chase for v in rooms.values() for e in v) else "")
              + (f"; regiões {''.join(later)}: só a tabela do Prime" if later else ""))
    return problems


# specs/19g: in the Mines the fairness rule holds in every room whatever its round, as in the Magmoor and Phendrana (the walks run
# along ledges and over floor doors, the Main Quarry's west cliff and the shafts: a knock-back drops Samus off them)
MINES_FAIR_EVERY_ROUND = True


def shooter_problems(r, e) -> list[str]:
    """specs/19g: a shooter `e` of room `r` (Species.fires: the walking pirate fires along its row at Samus whenever she is within
    `fires` px of its height, at any distance, while it is on camera; WalkingSpacePirates_FD44 $B2:FD44) against every door: as
    she comes in by it and stands (the door's inner cells and ENTRY_REACH blocks further in, her centre 21 px over her feet, as
    homing_problems), the camera shows the door's screen (CAMERA_SLACK px either way, as chaser_problems); anywhere on its walk
    (its parameter 2: px either way of its spawn) it must be off that camera, or more than `fires` px above or below her."""
    out = []
    info = species_info(e.species.ptr)
    cx, cy = e.pixel_pos()
    walk = e.species.param2
    wb, hb = r.width * 16, r.height * 16
    for i, d in enumerate(r.doors):
        sx, sy = {"L": (0, d.screen), "R": (r.width - 1, d.screen), "T": (d.screen, 0), "B": (d.screen, r.height - 1)}[d.side]
        cam_x, cam_y = sx * 256, sy * 256
        if (cx + walk + info["x_radius"] < cam_x - CAMERA_SLACK or cx - walk - info["x_radius"] > cam_x + 256 + CAMERA_SLACK
                or not cam_y - CAMERA_SLACK - 8 <= cy <= cam_y + CAMERA_SLACK + 248):
            continue   # off the camera: it does not run until she goes on into the room
        cells = door_inner_cells(d.side, d.screen, wb, hb)
        ix, iy = {"L": (1, 0), "R": (-1, 0), "T": (0, 1), "B": (0, -1)}[d.side]
        cells += [(x + ix * k, y + iy * k) for x, y in cells for k in range(1, ENTRY_REACH + 1)]
        ys = [y * 16 for _, y in cells]
        low, high = min(ys) + 21, max(ys) + 16 - 21   # her centre, standing anywhere in the doorway
        if low - e.species.fires < cy < high + e.species.fires:
            out.append(f"{r.key}: {e.kind} em ({e.x},{e.floor}) na câmera da porta {i} ({d.side}{d.screen}) à altura da Samus "
                       f"quando ela entra (centro y {cy}, ela {low}-{high}; atira a menos de {e.species.fires} px de altura)")
    return out


def check_mines_enemies() -> list[str]:
    """specs/19g: check_layer0_enemies for the Mines (tools/mines/enemies.py; the walk is the five areas' together), with the
    fairness rule in every room (MINES_FAIR_EVERY_ROUND); PRIME_LAYER0's rooms are in the Mines' table, ENEMIES only in built
    rooms; the rooms of a boss' arena (ARENA_ROOMS = the epic's boss rooms, EPIC_MINES_BOSS_ROOMS, with their children) get no
    layer-0 stand-in (their child places the fight, as Phendrana's: only the arena's kinds, Species.boss, once it is an arena of
    tools/chozo/bosses.py ARENAS), and no boss kind is elsewhere; every Prime type of the table is decided (STAND_IN) or proposed
    (PROPOSED_LATER), never both, a proposal that is a kind of ours dies to the Power Beam in at most FAIR_SHOTS shots and takes
    at most FAIR_TOUCH a touch; a drifter can't reach a door within ENTRY_FRAMES (homing_problems), a chaser starts off every
    door's camera (chaser_problems), a shooter is not at Samus' height on a door's camera (shooter_problems). Prints the line
    "mines (specs/19g)"."""
    T = mines_enemies
    arenas = set(T.ARENA_ROOMS)
    table = types.SimpleNamespace(STAND_IN=T.STAND_IN, PRIME_OF=T.PRIME_OF,
                                  PRIME_LAYER0={k: v for k, v in T.PRIME_LAYER0.items() if k not in arenas})
    problems = check_layer0_enemies(MINES, table, "mines", every_round=MINES_FAIR_EVERY_ROUND)
    keys = {t.key for t in mines_rooms.TABLE}
    unknown = sorted(set(T.PRIME_LAYER0) - keys)
    if unknown:
        problems.append(f"mines: PRIME_LAYER0 com salas fora da tabela: {unknown}")
    by_key = MINES.by_key()
    unbuilt = sorted(set(T.ENEMIES) - set(by_key))
    if unbuilt:
        problems.append(f"mines: inimigos em salas fora do build: {unbuilt}")
    if T.ARENA_ROOMS != EPIC_MINES_BOSS_ROOMS:
        problems.append(f"mines: ARENA_ROOMS {T.ARENA_ROOMS} não são as salas de chefe do épico {EPIC_MINES_BOSS_ROOMS}")
    stray = sorted(k for k, v in T.ENEMIES.items() if k not in arenas and any(e.species.boss for e in v))
    if stray:
        problems.append(f"mines: inimigos de arena (Species.boss) em salas fora de ARENA_ROOMS: {stray}")
    for key, child in sorted(T.ARENA_ROOMS.items()):
        spawns = T.ENEMIES.get(key, [])
        if spawns and (chozo_bosses.arena_of(key) is None or not all(e.species.boss for e in spawns)):
            problems.append(f"{key}: inimigos na sala da arena de {child} (só os da luta, quando ela estiver em ARENAS)")
        if not spawns:
            continue
        # specs/19h: the arena built (Phendrana's rule, specs/18h, 18k): only its kinds, the stand-ins of the room's Prime types
        # (the boss' later layer: PRIME_BOSS_LAYERS), at least one of each and at most Prime's count
        layer0 = {**T.PRIME_LAYER0.get(key, {}), **T.PRIME_BOSS_LAYERS.get(key, {})}
        got = collections.Counter(T.ARENA_KINDS.get(e.kind) for e in spawns)
        for e in spawns:
            if e.kind not in T.ARENA_KINDS:
                problems.append(f"{key}: {e.kind} na sala da arena sem ser um tipo dela (ARENA_KINDS)")
        for prime, n in sorted(layer0.items()):
            if not 1 <= got.get(prime, 0) <= n:
                problems.append(f"{key}: {got.get(prime, 0)} {prime} na arena (Prime: {n}; ao menos 1)")
        extra = sorted(set(got) - set(layer0) - {None})
        if extra:
            problems.append(f"{key}: tipos {extra} na arena que o Prime não tem na sala")
    stray = sorted(set(T.PRIME_BOSS_LAYERS) - set(T.ARENA_ROOMS))
    if stray:
        problems.append(f"mines: PRIME_BOSS_LAYERS com salas fora de ARENA_ROOMS: {stray}")
    types_ = {t for k, v in T.PRIME_LAYER0.items() if k not in arenas for t in v}
    missing = sorted(types_ - set(T.STAND_IN) - set(T.PROPOSED_LATER))
    if missing:
        problems.append(f"mines: tipos do Prime sem decisão nem proposta (STAND_IN/PROPOSED_LATER): {missing}")
    both = sorted(set(T.STAND_IN) & set(T.PROPOSED_LATER))
    if both:
        problems.append(f"mines: tipos decididos e ainda em PROPOSED_LATER: {both}")
    for prime, kind in sorted(T.PROPOSED_LATER.items()):
        if kind is None:
            continue
        sp = frigate_species(kind)
        if sp is None:
            problems.append(f"mines: proposta {prime} -> {kind}: não é uma espécie nossa (frigate/enemies.py SPECIES)")
            continue
        info = species_info(sp.ptr)
        per_shot = (POWER_BEAM_DAMAGE >> 1) * info["power"]
        if not per_shot or -(-info["hp"] // per_shot) > FAIR_SHOTS or info["damage"] > FAIR_TOUCH:
            problems.append(f"mines: proposta {prime} -> {kind} não é justa ({info['hp']} de vida, {per_shot} por tiro do Power "
                            f"Beam, {info['damage']} por toque; até {FAIR_SHOTS} tiros e {FAIR_TOUCH})")
    for key, spawns in T.ENEMIES.items():
        r = by_key.get(key)
        if r is None:
            continue
        for e in spawns:
            if e.species.homing:
                problems += homing_problems(r, e)
            if e.species.chase:
                problems += chaser_problems(r, e)
            if e.species.fires:
                problems += shooter_problems(r, e)
    if not problems:
        rooms = {k: [e for e in v if not e.species.boss] for k, v in MINES.enemies.items()}
        rooms = {k: v for k, v in rooms.items() if v}
        kinds = sorted({e.kind for v in rooms.values() for e in v})
        later = sorted({mines_rooms.region_of(k) for k in T.PRIME_LAYER0} - mines_rooms.ACTIVE_REGIONS)
        drifters = sorted({homing_speed(e.species) for v in rooms.values() for e in v if e.species.homing})
        print(f"mines (specs/19g): {sum(map(len, rooms.values()))} inimigos em {len(rooms)} salas "
              f"({', '.join(f'{k} {sum(e.kind == k for v in rooms.values() for e in v)}' for k in kinds)}); camada 0 do Prime, "
              f"no máximo 1 por tela; justos em toda sala (até {FAIR_SHOTS} tiros do Power Beam, até {FAIR_TOUCH} por toque); "
              f"os que vêm até a Samus ({', '.join(f'{v:g}' for v in drifters)} px por quadro) a mais de {ENTRY_FRAMES} quadros de "
              f"toda porta; os que atiram na altura dela fora da câmera de toda porta; arenas: "
              + ", ".join(f"{k.removeprefix('mines_')} ({c}: "
                          + ("construída" if chozo_bosses.arena_of(k) is not None else "livre") + ")"
                          for k, c in T.ARENA_ROOMS.items())
              + (f"; regiões {''.join(later)}: só a tabela do Prime (propostas: "
                 f"{', '.join(f'{p} -> {k}' for p, k in sorted(T.PROPOSED_LATER.items()))})" if later else ""))
    return problems


def check_layer0_enemies(area, table, tag: str, every_round: bool = False) -> list[str]:
    """specs/07i: the built rooms' enemies of `area` (`table`: tools/tallon/enemies.py; specs/12h: tools/chozo/enemies.py) against Prime's layer 0
    (PRIME_LAYER0): each Prime enemy with a stand-in is there (at least 1, at most Prime's count),
    nothing Prime doesn't have, at most one enemy per screen of the SM room; and, in the rooms Samus
    first gets into with at most the Power Beam, missiles and the Morph Ball (FAIR_ARRIVAL: the walk of
    the rounds' walk records it, specs/09d; 99 energy), every species dies to the Power Beam
    in at most FAIR_SHOTS shots and a touch takes at most FAIR_TOUCH."""
    problems = []
    try:
        arrival = tallon_progress_built()[3]
    except ValueError as e:   # an item in a room that is not built (check_tallon_rounds says it too)
        return [f"{tag}: {e}"]
    for r in area.rooms:
        # specs/14a: a boss stand-in is not a layer-0 enemy (check_bosses)
        spawns = [e for e in area.enemies.get(r.key, []) if not e.species.boss]
        got = {}
        for e in spawns:
            if e.kind not in table.PRIME_OF:
                problems.append(f"{r.key}: {e.kind} não substitui nenhum inimigo do Prime (STAND_IN)")
                continue
            got[table.PRIME_OF[e.kind]] = got.get(table.PRIME_OF[e.kind], 0) + 1
        layer0 = table.PRIME_LAYER0.get(r.key, {})
        undecided = sorted(set(layer0) - set(table.STAND_IN))
        if undecided:
            problems.append(f"{r.key}: inimigos do Prime sem decisão em STAND_IN: {undecided}")
        prime = {t: n for t, n in layer0.items() if table.STAND_IN.get(t)}
        for t in sorted(set(got) | set(prime)):
            n, want = got.get(t, 0), prime.get(t, 0)
            if not (min(1, want) <= n <= want):
                problems.append(f"{r.key}: {n} {t}, o Prime tem {want} na camada 0")
        if len(spawns) > r.width * r.height:
            problems.append(f"{r.key}: {len(spawns)} inimigos em {r.width * r.height} telas (no máximo 1 por tela)")
        if not every_round and (r.key not in arrival or not arrival[r.key] <= FAIR_ARRIVAL):
            continue
        why = "chegada só com Power Beam, mísseis, Morph" if not every_round else f"{tag.capitalize()}: toda rodada"
        for kind, sp in sorted({e.kind: e.species for e in spawns}.items()):
            info = species_info(sp.ptr)
            if sp.harmless:   # specs/12i: never hurts: fair although the Power Beam can't kill it
                problems += [f"{r.key}: {kind}: {p}" for p in harmless_problems(sp)]
                continue
            if sp.companion and species_info(sp.companion[0])["damage"] > FAIR_TOUCH:
                problems.append(f"{r.key}: {kind}: a parte ${sp.companion[0]:04X} tira "
                                f"{species_info(sp.companion[0])['damage']} por toque (máximo {FAIR_TOUCH})")
            per_shot = (POWER_BEAM_DAMAGE >> 1) * info["power"]
            shots = -(-info["hp"] // per_shot) if per_shot else None
            if shots is None or shots > FAIR_SHOTS:
                problems.append(f"{r.key}: {kind} ({why}) não morre com até {FAIR_SHOTS} tiros do Power Beam "
                                f"({info['hp']} de vida, {per_shot} por tiro)")
            if info["damage"] > FAIR_TOUCH:
                problems.append(f"{r.key}: {kind} ({why}) tira {info['damage']} por toque (máximo {FAIR_TOUCH})")
    return problems


# specs/14a: the fairness rule for a boss in a room Samus first gets into with no more than FAIR_ARRIVAL (99 energy): it
# must die to the uncharged Power Beam alone, in at most FAIR_BOSS_SHOTS shots (the common rule's 5 is for a room's small
# fry; a boss takes more, and BOSSES records exactly how many), and a touch takes at most FAIR_BOSS_TOUCH (99 energy = 3
# touches: the epic's decision 5, the big Sidehopper's 80 cut to 40); a fight that shuts no door (Boss.lock False) can be
# left at any time
FAIR_BOSS_SHOTS, FAIR_BOSS_TOUCH = 20, 40
BOSS_KILLS_BYTE = 1   # population: entries, FF FF, then the kill count (frigate.enemies.population)


def check_bosses(built, base) -> list[str]:
    """specs/14a: every boss of tools/chozo/bosses.py BOSSES: its room is built and has exactly one of it among its enemies
    (and no boss kind elsewhere); its kind is a boss stand-in (Species.boss) whose species is a copy (COPIES); its declared
    Power Beam shots = its health / a shot's damage, within the fairness rule for a boss where Samus first gets in with at
    most FAIR_ARRIVAL; a fight with no lock: no grey door in its room. No room of ours uses a copied species' vanilla source
    (the copy is what we place). In the built ROM (`built`, with the base ROM `base`): each copy's 64 header bytes are its
    source's with only the touch damage (and, recoloured, the palette pointer) changed: health, tiles, the tile data
    pointer, hitbox, AI the source's; a recoloured palette, in the source's bank, holds the colours the table gives; the
    source's header and palette are the base ROM's (vanilla untouched where vanilla uses it). Prints the line "chefes
    (specs/14a)"."""
    problems = []
    try:
        arrival = {**tallon_progress_built()[3], **impact_arrival()[0]}   # specs/20h: and the crater's rooms
    except ValueError as e:
        return [f"chefes: {e}"]
    by_key = {r.key: r for a in AREAS for r in a.rooms}
    boss_kinds = {b.kind for b in chozo_bosses.BOSSES}
    arena_rooms = {a.room for a in chozo_bosses.ARENAS}
    sources = {c.source for c in chozo_bosses.COPIES.values()} | {chozo_bosses.GOLDEN_TORIZO}   # specs/18k: patched in place
    for area in AREAS:
        for key, spawns in area.enemies.items():
            for e in spawns:
                if e.species.boss and e.kind not in boss_kinds and key not in arena_rooms:
                    problems.append(f"{key}: {e.kind} marcado como chefe e fora de BOSSES")
                if e.species.ptr in sources:
                    problems.append(f"{key}: {e.kind} usa a espécie vanilla ${e.species.ptr:04X} (a cópia é a nossa)")
    lines = []
    for b in chozo_bosses.BOSSES:
        tag = f"{b.room}: chefe {b.kind}"
        r = by_key.get(b.room)
        if r is None:
            problems.append(f"{tag}: sala não construída")
            continue
        area = next(a for a in AREAS if r in a.rooms)
        mine = [e for e in area.enemies.get(b.room, []) if e.kind == b.kind]
        if len(mine) != 1:
            problems.append(f"{tag}: {len(mine)} na sala (1 esperado)")
        others = [k for k, v in area.enemies.items() if k != b.room and any(e.kind == b.kind for e in v)]
        if others:
            problems.append(f"{tag}: também em {others}")
        sp = frigate_species(b.kind)
        if sp is None or not sp.boss:
            problems.append(f"{tag}: espécie sem a marca de chefe (Species.boss)")
            continue
        copy = chozo_bosses.COPIES.get(sp.ptr)
        if copy is None:
            problems.append(f"{tag}: espécie ${sp.ptr:04X} não é uma cópia de COPIES")
            continue
        info = species_info(sp.ptr)
        per_shot = (POWER_BEAM_DAMAGE >> 1) * info["power"]
        shots = -(-info["hp"] // per_shot) if per_shot else None
        if shots != b.shots:
            problems.append(f"{tag}: morre com {shots} tiros do Power Beam ({info['hp']} de vida, {per_shot} por tiro), "
                            f"BOSSES diz {b.shots}")
        fair = b.room in arrival and arrival[b.room] <= FAIR_ARRIVAL
        if fair and (shots is None or shots > FAIR_BOSS_SHOTS):
            problems.append(f"{tag} (chegada só com Power Beam, mísseis, Morph) não morre com até {FAIR_BOSS_SHOTS} tiros "
                            f"do Power Beam ({info['hp']} de vida, {per_shot} por tiro)")
        if fair and info["damage"] > FAIR_BOSS_TOUCH:
            problems.append(f"{tag} (chegada só com Power Beam, mísseis, Morph) tira {info['damage']} por toque "
                            f"(máximo {FAIR_BOSS_TOUCH})")
        if b.room not in arrival:
            problems.append(f"{tag}: sala fora do passeio das rodadas")
        if not b.lock and any(d.lock == "grey" for d in r.doors):
            problems.append(f"{tag}: luta sem trava (Prime) e a sala tem porta cinza")
        rnd = f"rodada {tallon_progress_built()[1].get(b.room, '?')}" if b.room in arrival else "?"
        lines.append(f"{b.kind} na {b.room} (Prime: {b.prime}, camada {b.prime_layer}): cópia $A0:{copy.ptr:04X} de "
                     f"${copy.source:04X}, vida {info['hp']}, toque {info['damage']}, {shots} tiros do Power Beam "
                     f"(chegada {rnd}: {', '.join(sorted(arrival.get(b.room, ())))}, 99 de energia; máximo de chefe "
                     f"{FAIR_BOSS_SHOTS} tiros, {FAIR_BOSS_TOUCH} por toque), "
                     + ("tranca a sala" if b.lock else "sem trava de porta"))
    if built is not None:
        problems += check_species_copies(built, base)
    arena_problems, arena_lines = check_arenas(built, base, arrival)
    problems += arena_problems
    epic_problems, epic_line = check_epic_bosses(base)
    problems += epic_problems
    if not problems:
        print("chefes (specs/14a): " + "; ".join(lines) + f"; {len(chozo_bosses.COPIES)} cópia(s) de espécie conferida(s) "
              "nos bytes, as espécies vanilla intactas")
        print("arenas (specs/14b): " + "; ".join(arena_lines))
        print(epic_line)
    return problems


# specs/14f: the Chozo's bosses of epic 14 (decision 1 of the user: the 4 of the Chozo; the Chozo Ghosts, 14e, out), by room,
# and what each locks in Prime (the epic's inventory: Prime's layers and connections, decisions 3, 4 and 6): (name, a prize
# that appears when it dies, a door shut until it dies, an item that starts the fight)
EPIC_BOSSES = {"chozo_ruined_shrine": ("Plated Beetle", False, False, False),
               "chozo_hive_totem": ("Hive Mecha", True, False, False),
               "chozo_sunchamber": ("Flaahgra", True, True, False),
               "chozo_burn_dome": ("Incinerator Drone", False, True, True)}


def vanilla_boss_bits(rom, area: int) -> set[int]:
    """specs/14f: the boss bits of `area` vanilla uses, read from the base ROM's rooms of that area: the masks of their
    state conditions E629 and the bits their grey door caps of types 0-2 wait for (type t = bit 1 << t, $84:BE4B)."""
    bits = set()
    for h in vanilla_rooms(rom):
        r = read_room(rom, 0x8F0000 | h)
        if r.area != area:
            continue
        q = 0x8F0000 | h + 11
        while rom.u16(q) != 0xE5E6:
            c = rom.u16(q)
            if c == 0xE629:
                bits.add(rom.u8(q + 2))
            q += 2 + {0xE612: 1, 0xE629: 1, 0xE5EB: 2}.get(c, 0) + 2
        for st in r.states:
            for plm in (room_plms(rom, st.addr) if st.plm else []):
                if plm[0] in build.GREY_DOOR_PLM.values() and (plm[3] >> 10) & 0x1F < 3:
                    bits.add(1 << ((plm[3] >> 10) & 0x1F))
    return bits


def check_epic_bosses(base) -> tuple[list[str], str]:
    """specs/14f, epic 14 closed: its 4 Chozo bosses (EPIC_BOSSES) each an arena of tools/chozo/bosses.py ARENAS (and no other
    arena of area 1); their boss bits of area 1 distinct and none a bit vanilla's area-1 rooms use (vanilla_boss_bits, read from
    the base ROM: the Spore Spawn's $02 may be an arena's condition, the bit its own death sets, never an arena's bit); every
    lock a fight makes modelled in the progression walk: a prize or an ITEM arena's trigger item in boss_locks (picked up only
    with the arena's `needs`), a boss door (BOSS_DOORS) a built door with the boss gate. The line "chefes (specs/14)".
    specs/18h: the same for Phendrana's (epic 18, decision 4: EPIC_PHENDRANA_BOSSES, area 4), each an arena once its child is
    done (PHENDRANA_BOSS_CHILDREN_DONE), the others waiting; the line "chefes de Phendrana (specs/18h, 18k)". specs/19h: the Mines'
    (epic 19, decision 4: EPIC_MINES_BOSSES, area 5; MINES_BOSS_CHILDREN_DONE); the line "chefes da Mines (specs/19h)"."""
    base = base or base_rom()
    problems, parts, vanilla = epic_area_bosses(base, CHOZO, EPIC_BOSSES, chozo_rooms.BOSS_DOORS, set(EPIC_BOSSES), "chefes")
    line = (f"chefes (specs/14): {len(EPIC_BOSSES)} da Chozo, cada um uma arena (a Parasite Queen da fragata é a etapa 6; os Chozo "
            f"Ghosts, 14e, fora): " + "; ".join(parts) + f"; bits da área {CHOZO.number} distintos, nenhum dos vanilla dela "
            f"({', '.join(f'${b:02X}' for b in sorted(vanilla))}, lidos da ROM base; o $02 do Spore Spawn só como condição)")
    done = {k for k, c in EPIC_PHENDRANA_BOSS_ROOMS.items() if c in PHENDRANA_BOSS_CHILDREN_DONE}
    p2, parts2, vanilla2 = epic_area_bosses(base, PHENDRANA, EPIC_PHENDRANA_BOSSES, set(phendrana_rooms.BOSS_DOORS), done,
                                            "chefes de Phendrana")
    waiting = ", ".join(f"{EPIC_PHENDRANA_BOSSES[k][0]} ({c})" for k, c in sorted(EPIC_PHENDRANA_BOSS_ROOMS.items()) if k not in done)
    if set(EPIC_PHENDRANA_BOSSES) != set(EPIC_PHENDRANA_BOSS_ROOMS):
        p2.append(f"chefes de Phendrana: EPIC_PHENDRANA_BOSSES {sorted(EPIC_PHENDRANA_BOSSES)} != as salas da decisão 4 "
                  f"{sorted(EPIC_PHENDRANA_BOSS_ROOMS)}")
    line += ("\nchefes de Phendrana (specs/18h, 18k): " + ("; ".join(parts2) or "nenhum") + f"; esperando: {waiting or 'nenhum'}; bits "
             f"da área {PHENDRANA.number} distintos, nenhum dos vanilla dela ({', '.join(f'${b:02X}' for b in sorted(vanilla2))}, "
             "lidos da ROM base)")
    # specs/19h: the Mines' (epic 19, user decision 4: EPIC_MINES_BOSSES, area 5), each an arena once its child is done
    done3 = {k for k, c in EPIC_MINES_BOSS_ROOMS.items() if c in MINES_BOSS_CHILDREN_DONE}
    p3, parts3, vanilla3 = epic_area_bosses(base, MINES, EPIC_MINES_BOSSES, set(mines_rooms.BOSS_DOORS), done3,
                                            "chefes da Mines")
    waiting3 = ", ".join(f"{EPIC_MINES_BOSSES[k][0]} ({c})" for k, c in sorted(EPIC_MINES_BOSS_ROOMS.items()) if k not in done3)
    if set(EPIC_MINES_BOSSES) != set(EPIC_MINES_BOSS_ROOMS):
        p3.append(f"chefes da Mines: EPIC_MINES_BOSSES {sorted(EPIC_MINES_BOSSES)} != as salas da decisão 4 "
                  f"{sorted(EPIC_MINES_BOSS_ROOMS)}")
    line += ("\nchefes da Mines (specs/19h): " + ("; ".join(parts3) or "nenhum") + f"; esperando: {waiting3 or 'nenhum'}; bits da "
             f"área {MINES.number} distintos, nenhum dos vanilla dela ({', '.join(f'${b:02X}' for b in sorted(vanilla3))}, lidos "
             "da ROM base)")
    return problems + p2 + p3, line


# specs/18h: Phendrana's bosses of epic 18 (decision 4 of the user), as EPIC_BOSSES: (name, a prize that appears when it dies, a
# door shut until it dies, an item that starts the fight). The Sheegoth: the missile in the Wave Beam's place (decision 3), the
# Chapel's Actor Door Lock; the Thardus (18k): no prize (the Spider Ball has no SM item), its doors shut until it dies
EPIC_PHENDRANA_BOSSES = {"phendrana_chapel_of_the_elders": ("Sheegoth", True, True, False),
                         "phendrana_quarantine_cave": ("Thardus", False, True, False)}
PHENDRANA_BOSS_CHILDREN_DONE = frozenset({"18h", "18k"})   # the children of EPIC_PHENDRANA_BOSS_ROOMS whose arena is built
# specs/19h: the Mines' bosses of epic 19 (decision 4 of the user), as EPIC_BOSSES: the Phazon Elite (no prize: the Warrior artifact
# has no SM item; the Elite Research's Actor Door Lock on its door to the Security Access B), the Omega Pirate (19k: no prize, the
# Phazon Suit has no SM item; its two doors shut until it dies)
EPIC_MINES_BOSSES = {"mines_elite_research": ("Phazon Elite", False, True, False),
                     "mines_elite_quarters": ("Omega Pirate", False, True, False)}
MINES_BOSS_CHILDREN_DONE = frozenset({"19h", "19k"})   # the children of EPIC_MINES_BOSS_ROOMS whose arena is built


def epic_area_bosses(base, area, epic: dict, boss_doors: set, required: set, tag: str) -> tuple[list[str], list[str], set]:
    """check_epic_bosses for one area: its arenas (ARENAS in its built rooms) = `required` (each a boss of `epic`), their bits
    distinct and none vanilla's of the area, each lock of `epic` modelled in the walk. Returns (problems, the parts of the line,
    the area's vanilla bits)."""
    B, problems = chozo_bosses, []
    arenas = [a for a in B.ARENAS if a.room in area.by_key()]
    if {a.room for a in arenas} != set(required) or len(arenas) != len(required) or not set(required) <= set(epic):
        problems.append(f"{tag}: arenas {sorted(a.room for a in arenas)} != os chefes do épico {sorted(required)}")
    vanilla = vanilla_boss_bits(base, area.number)
    bits = [a.bit for a in arenas]
    if len(set(bits)) != len(bits) or set(bits) & vanilla:
        problems.append(f"{tag}: bits da área {area.number} {[f'${b:02X}' for b in bits]} repetidos ou vanilla "
                        f"({[f'${b:02X}' for b in sorted(vanilla)]})")
    for a in arenas:
        # specs/18k: or the Torizo's bit, whose death sets it in whatever area it is (Torizo_Instr_38), if its copy is the
        # arena's boss (and no vanilla room of the area uses that bit)
        torizo = a.arg == B.TORIZO_BIT and torizo_arena(a) and B.TORIZO_BIT not in vanilla
        if a.condition == B.BOSS_BIT and a.arg not in vanilla and not torizo:
            problems.append(f"{tag}: {a.room} espera o bit ${a.arg:02X}, que nenhum chefe vanilla da área liga")
    try:
        rounds, first, first_item, _ = tallon_progress_built()
    except ValueError as e:
        return [f"{tag}: {e}"], [], vanilla
    by_key = {r.key: r for r in world_rooms()}
    locks = boss_locks(set(by_key))
    parts = []
    for a in sorted(arenas, key=lambda a: (first.get(a.room, 99), a.room)):
        name, prize, door, trigger = epic.get(a.room, (a.room, None, None, None))
        has = (a.prize is not None, any(key == a.room for key, _ in boss_doors), a.condition == B.ITEM)
        if (prize, door, trigger) != has:
            problems.append(f"{tag}: {name} ({a.room}) trava (prêmio, porta, item que começa) = {has}, o épico diz "
                            f"{(prize, door, trigger)}")
        what = []
        for n, arena in locks.items():
            if arena is a:
                it = item_of(n)
                verb = "começa a luta" if a.condition == B.ITEM else "só depois da luta"
                what.append(f"{tallon_items.KIND_NAME[it.kind]} {verb} (rodada {first_item.get(n, '?')})")
        if a.prize is not None and not any(item_of(n).spot == a.prize[1] and item_of(n).room == a.room for n in locks
                                           if locks[n] is a):
            problems.append(f"{tag}: o prêmio de {a.room} fora da trava boss do passeio")
        if a.condition == B.ITEM and not any(locks[n] is a for n in locks):
            problems.append(f"{tag}: o item que começa a luta de {a.room} fora da trava boss do passeio")
        for key, to in sorted(boss_doors):
            if key != a.room:
                continue
            d = next((d for d in by_key[key].doors if d.to_room == to), None)
            if d is None or d.lock != "boss" or chozo_rooms.BOSS_GATE not in d.gate:
                problems.append(f"{tag}: a porta de chefe {key} -> {to} sem a trava boss")
            else:
                # specs/18k: a door whose cap changes with the arena's state (build.arena_door_alive_cap) is shut from the load
                what.append(f"a porta para {to} " + ("tranca até a vitória" if a.condition in (B.ITEM, B.KILLS) or
                                                     build.arena_door_alive_cap(key, d) is not None else "só depois da luta"))
        if a.condition == B.BOSS_BIT and torizo_arena(a):   # specs/18k
            what.append(f"vence quando o Torizo liga o bit ${a.arg:02X} da área (o código dele), nenhum prêmio "
                        f"({TORIZO_NO_PRIZE.get(a.room, 'nenhum item SM')} não existe no SM)")
        parts.append(f"{name} ({a.room}, rodada {first.get(a.room, '?')}, bit ${a.bit:02X}): " + (", ".join(what) or "nenhuma trava"))
    return problems, parts, vanilla


def kago_hits(base, e) -> int | None:
    """specs/14b: Power Beam hits that kill a bug hive (Kago): its shot AI ($A8:AB83) counts parameter 1 down and dies below 0
    (the bytes of the count, bosses.KAGO_COUNT, must be in it), whatever its health; None if the code is not that."""
    code = base.read(chozo_bosses.KAGO_SHOT, 0x40)
    return e.species.param1 + 1 if chozo_bosses.KAGO_COUNT in code else None


def arena_kills(base, e) -> tuple[int | None, int]:
    """(uncharged Power Beam shots that kill enemy `e`, the most it takes from Samus in one hit: its touch, or a Kago's bug;
    specs/14c: the Spore Spawn's spores and stalk, and None shots: its shot AI takes no uncharged beam)."""
    info = species_info(e.species.ptr)
    copy = chozo_bosses.COPIES.get(e.species.ptr)
    if (copy.source if copy else e.species.ptr) == chozo_bosses.KAGO:   # specs/14d: the hive is a copy of the Kago
        bug = base.u16(chozo_bosses.KAGO_BUG + 8) & 0x0FFF
        return kago_hits(base, e), max(info["damage"], bug)
    if (copy.source if copy else e.species.ptr) == chozo_bosses.TORIZO:   # specs/18k: its swipe, orbs and sonic boom too
        per_shot = (POWER_BEAM_DAMAGE >> 1) * info["power"]
        hits = [base.u16(p + 8) & 0x0FFF for p in chozo_bosses.TORIZO_EPROJS]
        return (-(-info["hp"] // per_shot) if per_shot else None), max([info["damage"]] + hits)
    if (copy.source if copy else e.species.ptr) == chozo_bosses.NINJA:   # specs/19h: its claws too
        per_shot = (POWER_BEAM_DAMAGE >> 1) * info["power"]
        hits = [base.u16(p + 8) & 0x0FFF for p in chozo_bosses.NINJA_EPROJS]
        return (-(-info["hp"] // per_shot) if per_shot else None), max([info["damage"]] + hits)
    if e.species.ptr == chozo_bosses.SPORE_SPAWN:
        hits = [base.u16(p + 8) & 0x0FFF for p in chozo_bosses.SPORE_SPAWN_EPROJS]
        immune = base.read(chozo_bosses.SPORE_SPAWN_SHOT, len(chozo_bosses.SPORE_SPAWN_SHOT_CODE)) == \
            chozo_bosses.SPORE_SPAWN_SHOT_CODE
        per_shot = (POWER_BEAM_DAMAGE >> 1) * info["power"]
        return (None if immune or not per_shot else -(-info["hp"] // per_shot)), max([info["damage"]] + hits)
    per_shot = (POWER_BEAM_DAMAGE >> 1) * info["power"]
    return (-(-info["hp"] // per_shot) if per_shot else None), info["damage"]


def weapon_damage(base, ptr: int, weapon: str) -> int:
    """specs/14c: the damage one `weapon` ("missile", "charge": the charged Power Beam) does to species `ptr` in ROM `base`
    (the built one when there is one): Samus' projectile damage (bosses.DAMAGE_TABLES, read) >> 1, times the species'
    vulnerability multiplier (0 = immune)."""
    table, index, byte = chozo_bosses.DAMAGE_TABLES[weapon]
    damage = base.u16(0x930000 | base.u16(table + 2 * index))
    at = 0xA00000 | ptr
    v = base.u8(0xB40000 | (base.u16(at + 0x3C) or 0xEC1C) + byte)
    mult = (v & 0x7F) if weapon == "missile" else (0 if v == 0xFF else v & 0x0F)
    return (damage >> 1) * mult


def round_missiles(k: int) -> int:
    """specs/14c: the missile capacity Samus can have in round k: the missiles of the items first picked up in the rounds
    before it (ITEM_GAIN; the frigate leaves her none, specs/07e)."""
    rounds = tallon_progress_built()[0]
    return sum(ITEM_GAIN[item_of(n).kind][1] for rd in rounds[:k] for n in rd.items
               if ITEM_GAIN.get(item_of(n).kind, ("", 0))[0] == "missiles")


def arena_gear_fight(base, a, waits, arrival) -> tuple[str, list[str]]:
    """specs/14c, the boss fairness rule for a fight the uncharged Power Beam does not win (Arena.needs not empty: the
    Spore Spawn's shot AI takes only missiles, bombs and charged shots, bosses.SPORE_SPAWN_SHOT), with the gear of the round
    Samus first gets into the room: won with the missiles she can carry by then (round_missiles: every missile hits; each
    does weapon_damage) or with at most FAIR_BOSS_SHOTS charged shots, if she has the Charge Beam. The declared `needs`
    must be such a way on its own (the progression walk opens the prize and the boss door with them) and she must have
    them on arrival. Returns the line's text and the problems."""
    problems = []
    have = arrival.get(a.room, frozenset())
    k = {**tallon_progress_built()[1], **impact_arrival()[1]}.get(a.room)   # specs/20h: a crater room's, the teleporter's
    cap = round_missiles(k) if k is not None else 0
    need = {}
    for weapon in ("missile", "charge"):
        n = 0
        for e in waits:
            d = weapon_damage(base, e.species.ptr, weapon)
            if not d:
                n = None
                break
            n += -(-base.u16(0xA00000 | e.species.ptr + 4) // d)   # its health, in the same ROM
        need[weapon] = n
    ok = {tallon_rooms.MISSILE: tallon_rooms.MISSILE in have and need["missile"] is not None and need["missile"] <= cap,
          tallon_rooms.CHARGE: tallon_rooms.CHARGE in have and need["charge"] is not None and need["charge"] <= FAIR_BOSS_SHOTS}
    text = (f"{need['missile'] if need['missile'] is not None else 'nenhum'} mísseis (capacidade na rodada {k}: {cap}) ou "
            f"{need['charge'] if need['charge'] is not None else 'nenhum'} tiros carregados "
            f"({'com' if tallon_rooms.CHARGE in have else 'sem'} o Charge Beam na chegada; máximo de chefe {FAIR_BOSS_SHOTS})")
    if not any(ok.values()):
        problems.append(f"não se vence com o equipamento da rodada {k} ({have_names(have)}): {text}")
    if not a.needs <= have:
        problems.append(f"a luta pede {sorted(a.needs)} e a Samus chega com {have_names(have)}")
    if len(a.needs) != 1 or not ok.get(next(iter(a.needs)), False):
        problems.append(f"needs {sorted(a.needs)} não é, sozinho, um jeito de vencer a luta na chegada ({text})")
    return text, problems


def check_spore_spawn(r, spawns) -> list[str]:
    """specs/14c: the Spore Spawn's assumptions about its room (bytes of the base ROM, tools/chozo/bosses.py): it is the
    room's only enemy and in slot 0 (its code keeps its state in enemy 0's fields); its fixed spot (frigate/enemies.py
    Species.fixed) = the death's position in its code ($A5:E87C); the 2x2 roof blocks its death's PLM clears ($A5:EE41: db
    x, y) are air in the room (they would open a hole in the roof); its shot AI is the one that takes no uncharged beam."""
    B, base = chozo_bosses, base_rom()
    problems = []
    if slots(spawns)[:1] != [B.SPORE_SPAWN] or len(spawns) != 1:
        problems.append(f"o Spore Spawn não é o único inimigo, no slot 0 ({[f'${p:04X}' for p in slots(spawns)]})")
    at, want = B.SPORE_SPAWN_DEATH_SPOT
    code = base.read(at, len(want))
    spot = (int.from_bytes(code[1:3], "little"), int.from_bytes(code[7:9], "little"))
    fixed = next(e.species.fixed for e in spawns if e.species.ptr == B.SPORE_SPAWN)
    if code[0] != 0xA9 or code[6] != 0xA9 or spot != fixed:
        problems.append(f"posição fixa {fixed}, o código em ${at:06X} diz {spot}")
    at, want = B.SPORE_SPAWN_DEATH_PLM
    if base.read(at, len(want)) != want or tuple(want[4:6]) != B.SPORE_SPAWN_ROOF[:2]:
        problems.append(f"o PLM da morte em ${at:06X} não é o esperado ({base.read(at, len(want)).hex()})")
    x0, y0, x1, y1 = B.SPORE_SPAWN_ROOF
    l1, _ = r.level().build_blocks()
    wb = r.width * 16
    solid = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if (l1[y * wb + x] >> 12) != 0]
    if solid:
        problems.append(f"blocos {solid} não são ar: o PLM da morte ($B78F) os abre (buraco no teto)")
    if base.read(B.SPORE_SPAWN_SHOT, len(B.SPORE_SPAWN_SHOT_CODE)) != B.SPORE_SPAWN_SHOT_CODE:
        problems.append(f"o tiro do Spore Spawn (${B.SPORE_SPAWN_SHOT:06X}) não é o esperado: a imunidade ao feixe não vale")
    # its population entry: the vanilla placement's values (init, properties, extra properties: $0004 = its extended
    # spritemaps, without it the body is not drawn; parameters), the spot the fixed one
    want = base.read(B.SPORE_SPAWN_POPULATION, 16)
    e = next(e for e in spawns if e.species.ptr == B.SPORE_SPAWN)
    got = struct.pack("<8H", *e.entries()[0])
    if got != want:
        problems.append(f"entrada da população {got.hex()} != a vanilla ${B.SPORE_SPAWN_POPULATION:06X} {want.hex()}")
    return problems


def torizo_species(ptr: int) -> bool:
    """specs/18k: species `ptr` is a Torizo or a copy of one."""
    copy = chozo_bosses.COPIES.get(ptr)
    return (copy.source if copy else ptr) in (chozo_bosses.TORIZO, chozo_bosses.GOLDEN_TORIZO)


# specs/18k, 19k: the item Prime's Torizo arenas guard, which has no SM item (no prize)
TORIZO_NO_PRIZE = {"phendrana_quarantine_cave": "a Spider Ball", "mines_elite_quarters": "o Phazon Suit"}


def torizo_arena(a) -> bool:
    """specs/18k: arena `a`'s room has a Torizo (its copy) among its enemies."""
    area = arena_area(a)
    return area is not None and any(torizo_species(e.species.ptr) for e in area.enemies.get(a.room, []))


def check_torizo(a, r, spawns) -> list[str]:
    """specs/18k: the Torizo's assumptions about its arena (tools/chozo/bosses.py, the base ROM's bytes): it is the room's only
    enemy (its tiles take the whole enemy VRAM: header +0 = $2000) and a copy of the Bomb Torizo (never the vanilla one nor
    the Golden Torizo: their code is patched in place, the Golden one would play as the Bomb one); its fixed spot (Species.fixed,
    which bosses.TORIZO_SPOT takes) in open air and standing on the floor (it falls from there: emulator); the arena waits for
    the Torizo's bit (BOSS_BIT, bosses.TORIZO_BIT: Torizo_Instr_38 sets it, $AA:B24D), the room's boss doors grey caps of type 2
    (build.arena_door_alive_cap). (check_arenas_in_rom: no vanilla statue PLM, $84:D6EA, in the room's lists: it breaks the
    statue's blocks; without it the Torizo wakes as the room loads.)"""
    B, base = chozo_bosses, base_rom()
    problems = []
    torizos = [e for e in spawns if torizo_species(e.species.ptr)]
    if len(spawns) != 1 or len(torizos) != 1:
        problems.append(f"o Torizo não é o único inimigo da sala ({[e.kind for e in spawns]}: os tiles dele ocupam a VRAM toda)")
    for e in torizos:
        copy = B.COPIES.get(e.species.ptr)
        if copy is None or copy.source != B.TORIZO:
            problems.append(f"{e.kind}: espécie ${e.species.ptr:04X} não é uma cópia do Bomb Torizo ${B.TORIZO:04X}")
        if base.u16(0xA00000 | B.TORIZO) != 0x2000:
            problems.append("o Torizo da ROM base não ocupa $2000 bytes de VRAM (o cabeçalho mudou?)")
        if e.species.fixed is None:
            problems.append(f"{e.kind}: sem posição fixa (Species.fixed: o init do Torizo põe a posição da tabela dele)")
            continue
        info = species_info(e.species.ptr)
        x, y = e.species.fixed
        x0, x1, y0, y1 = (x - info["x_radius"]) // 16, (x + info["x_radius"] - 1) // 16, (y - info["y_radius"]) // 16, \
            (y + info["y_radius"] - 1) // 16
        l1, _ = r.level().build_blocks()
        wb = r.width * 16
        solid = lambda bx, by: (l1[by * wb + bx] >> 12) != 0   # noqa: E731
        inside = [(bx, by) for by in range(y0, y1 + 1) for bx in range(x0, x1 + 1) if solid(bx, by)]
        if inside:
            problems.append(f"{e.kind} em {e.species.fixed}: blocos sólidos na caixa {inside}")
        if (y + info["y_radius"]) % 16 or not all(solid(bx, y1 + 1) for bx in range(x0, x1 + 1)):
            problems.append(f"{e.kind} em {e.species.fixed}: não está de pé no chão (pés em y {y + info['y_radius']})")
        if (e.x, e.floor) != (x // 16, (y + info["y_radius"]) // 16):
            problems.append(f"{e.kind}: a coluna/chão da tabela ({e.x},{e.floor}) não é a posição fixa {e.species.fixed}")
    if a.condition != B.BOSS_BIT or a.arg != B.TORIZO_BIT:
        problems.append(f"a arena não espera o bit do Torizo (condição {a.condition}, ${a.arg:02X})")
    for d in r.doors:
        if d.lock == "boss" and build.arena_door_alive_cap(r.key, d) != B.GREY_DOOR_TORIZO:
            problems.append(f"porta para {d.to_room}: tampa do estado vivo não é a cinza do Torizo (tipo 2)")
    return problems


def ninja_species(ptr: int) -> bool:
    """specs/19h: species `ptr` is a ninja pirate (its init NinjaSpacePirates_Init $B2:F5DE, read from the base ROM: the 6
    vanilla colours $A0:F4D3-F613) or a copy of one."""
    copy = chozo_bosses.COPIES.get(ptr)
    src = copy.source if copy else ptr
    return base_rom().u8(0xA00000 | src + 0x0C) == 0xB2 and base_rom().u16(0xA00000 | src + 0x12) == chozo_bosses.NINJA_INIT & 0xFFFF


def check_ninja(r, spawns) -> list[str]:
    """specs/19h: the gold ninja pirate's assumptions about its arena (tools/chozo/bosses.py PHAZON_ELITE, the base ROM's bytes):
    a copy (never a vanilla ninja: the copy's shot AI is the common one, and the leap palette is patched for all of them), the
    room's only enemy (its tiles $1800 and its leap palette in sprite line 7: nothing else may use that line) with the enemy set's
    palette 1 (its code puts line 1 back after each leap, bosses.NINJA_PALETTE_INDEX); its leap (bosses.ninja_leap: the span of
    parameter 2 from its spawn, west if parameter 1 bit 0 is clear) over a solid floor, row by row, and its whole box in the air
    up to the leap's top (it moves through blocks: SpacePirates_Func_11/13 change x and y with no collision), the room's walls
    out of it."""
    B, base = chozo_bosses, base_rom()
    problems = []
    ninjas = [e for e in spawns if ninja_species(e.species.ptr)]
    if len(spawns) != 1 or len(ninjas) != 1:
        problems.append(f"o pirata ninja não é o único inimigo da sala ({[e.kind for e in spawns]}: a linha 7 de paleta é dele)")
    l1, _ = r.level().build_blocks()
    wb = r.width * 16
    solid = lambda bx, by: not (0 <= bx < wb and 0 <= by < r.height * 16) or (l1[by * wb + bx] >> 12) != 0   # noqa: E731
    for e in ninjas:
        copy = B.COPIES.get(e.species.ptr)
        if copy is None or copy.source != B.NINJA:
            problems.append(f"{e.kind}: espécie ${e.species.ptr:04X} não é uma cópia do ninja dourado ${B.NINJA:04X}")
        if e.species.palette != 1:
            problems.append(f"{e.kind}: paleta do enemy set {e.species.palette} (o código dele volta à linha 1: "
                            f"${B.NINJA_PALETTE_INDEX:04X})")
        info = species_info(e.species.ptr)
        x, y = e.pixel_pos()
        span = e.species.param2
        half, rise = B.ninja_leap(span)
        mid = x + span // 2 if e.species.param1 & 1 else x - span // 2
        x0, x1 = mid - half - B.NINJA_X_RADIUS, mid + half + B.NINJA_X_RADIUS - 1
        feet = y + info["y_radius"]
        if feet % 16:
            problems.append(f"{e.kind}: pés em y {feet}, fora de uma linha de blocos")
            continue
        under = [bx for bx in range(x0 // 16, x1 // 16 + 1) if not solid(bx, feet // 16)]
        if under:
            problems.append(f"{e.kind}: o salto ({x0}-{x1}) passa sobre colunas sem chão na linha {feet // 16}: {under}")
        top = y - info["y_radius"] - rise
        inside = [(bx, by) for by in range(max(top, 0) // 16, feet // 16) for bx in range(x0 // 16, x1 // 16 + 1)
                  if solid(bx, by)]
        if inside or top < 0:
            problems.append(f"{e.kind}: blocos sólidos na caixa do salto (x {x0}-{x1}, y {top}-{feet}): {inside[:6]}")
    return problems


def check_arenas(built, base, arrival) -> tuple[list[str], list[str]]:
    """specs/14b: every arena of tools/chozo/bosses.py ARENAS (specs/18h: of any area; Phendrana's fair in every round, as its
    enemies, PHENDRANA_FAIR_EVERY_ROUND; the bits one per arena of each area). Tables: a built room with its boss kinds (Species.boss:
    the arena's enemies; SLOT: the boss kind in that slot); our bit one of $08-$80 (the SM's are $01/$02/$04), one per arena of
    the area (BOSS_BIT: one bit; ITEM: one of our item bits); the prize a placed item of the room; with the arrival's gear (at most Power Beam, missiles, Morph) and no
    `needs`, the enemies the condition waits for die to the Power Beam in at most FAIR_BOSS_SHOTS shots in all (a Kago by its
    hits, kago_hits) and take at most FAIR_BOSS_TOUCH a hit. Built ROM: the room's header picks the dead state by E629 with the
    arena's bit (the alive one the default); alive = the arena routine's call as main ASM and the mini-boss music; dead = no
    main ASM, the area's music; the call ($8F) and the routine ($84) the bytes bosses.py makes, its table one entry per arena
    (room, condition, argument, bit, the prize's entry in the dead state's PLM list, the music stopped) and the end mark; no
    room state of ours uses condition E612 (event 0, which the vanilla kill-count door type 3 sets)."""
    problems, lines = [], []
    B = chozo_bosses
    by_key = {r.key: r for r in world_rooms() + crater_only().rooms}   # specs/20h: the crater's (out of the rounds' walk) too
    # specs/18h: the arenas of every area (the Chozo's, Phendrana's); the prize a placed item of any area's table
    placed = {(it.room, it.spot): (n, it) for n, it in world_items(set(by_key))}
    bits = [(arena_area(a).number, a.bit) for a in B.ARENAS if arena_area(a) is not None]
    if len(set(bits)) != len(bits):   # specs/18h: one per arena of an area (each area has its own boss bits)
        problems.append(f"arenas: bits repetidos numa área {[f'{n}:${b:02X}' for n, b in bits]}")
    rounds = {**tallon_progress_built()[1], **impact_arrival()[1]} if arrival is not None else {}   # specs/20h: the crater's
    for a in B.ARENAS:
        tag = f"arena {a.room}"
        r, area = by_key.get(a.room), arena_area(a)
        if r is None or area is None:
            problems.append(f"{tag}: sala não construída")
            continue
        if a.bit not in (0x08, 0x10, 0x20, 0x40, 0x80):
            problems.append(f"{tag}: bit de chefe ${a.bit:02X} (os nossos: um de $08-$80; o SM usa $01, $02, $04)")
        spawns = area.enemies.get(a.room, [])
        bosses_here = [e for e in spawns if e.species.boss]
        if not bosses_here:
            problems.append(f"{tag}: nenhum inimigo da arena (Species.boss) na sala")
            continue
        if a.condition == B.KILLS:
            waits = [e for e in spawns if not e.species.harmless]
        elif a.condition == B.SLOT:
            species = slots(spawns)
            k = a.arg // 0x40
            if a.arg % 0x40 or not 0 <= k < len(species) or species[k] not in {e.species.ptr for e in bosses_here}:
                problems.append(f"{tag}: o slot {a.arg:#x} não é de um inimigo da arena ({[f'${p:04X}' for p in species]})")
                continue
            waits = [next(e for e in bosses_here if e.species.ptr == species[k])]
        elif a.condition == B.BOSS_BIT:   # the boss (its kinds) sets the bit
            waits = bosses_here
            if a.arg not in (1, 2, 4, 8, 16, 32, 64, 128):
                problems.append(f"{tag}: condição bit de chefe com máscara {a.arg:#x} (um bit só)")
        elif a.condition == B.ITEM:   # specs/14d: taking the item starts the fight (the boss kinds spawn), the kills end it
            waits = [e for e in spawns if not e.species.harmless]
            problems += [f"{tag}: {w}" for w in check_item_arena(a, r, spawns, placed)]
        else:
            problems.append(f"{tag}: condição {a.condition} desconhecida")
            continue
        if a.prize is not None and a.prize not in placed:
            problems.append(f"{tag}: prêmio {a.prize} não é um item colocado da sala")
        total, worst = 0, 0
        for e in waits:
            shots, hit = arena_kills(base or base_rom(), e)
            worst = max(worst, hit)
            if shots is None:
                total = None
                if not a.needs:
                    problems.append(f"{tag}: {e.kind} em ({e.x},{e.floor}) não morre com o Power Beam")
            elif total is not None:
                total += shots
        # specs/18h: Phendrana's fairness in every round (PHENDRANA_FAIR_EVERY_ROUND, as its enemies'), whatever she brings
        fair = a.room in arrival and (arrival[a.room] <= FAIR_ARRIVAL or area is PHENDRANA
                                      or (area is MINES and MINES_FAIR_EVERY_ROUND)) and not a.needs   # specs/19h
        if fair and total is not None and total > FAIR_BOSS_SHOTS:
            problems.append(f"{tag} (chegada só com Power Beam, mísseis, Morph): {total} tiros do Power Beam para vencer "
                            f"(máximo de chefe {FAIR_BOSS_SHOTS})")
        if fair and worst > FAIR_BOSS_TOUCH:
            problems.append(f"{tag}: tira {worst} num golpe (máximo de chefe {FAIR_BOSS_TOUCH})")
        if a.room not in arrival:
            problems.append(f"{tag}: sala fora do passeio das rodadas")
        cond = {B.KILLS: "cota de mortes", B.SLOT: f"slot {a.arg // 0x40} vazio", B.BOSS_BIT: f"bit de chefe ${a.arg:02X}",
                B.ITEM: f"o item ${a.arg:02X} pego começa a luta (a porta tranca, os {len(bosses_here)} gerados), "
                        f"cota de mortes {len(waits)}"}[a.condition]
        prize = f"o item {prize_name(placed[a.prize][0])} ({tallon_items.KIND_NAME[placed[a.prize][1].kind]}, rodada " \
                f"{placed[a.prize][1].round}) aparece" if a.prize in placed else "nenhum prêmio"
        if a.needs:   # specs/14c: a fight the Power Beam does not win, weighed with the gear of the round she gets there
            way, ways_problems = arena_gear_fight(built if built is not None else base or base_rom(), a, waits, arrival)
            problems += [f"{tag}: {w}" for w in ways_problems]
            if worst > FAIR_BOSS_TOUCH:
                problems.append(f"{tag}: tira {worst} num golpe (máximo de chefe {FAIR_BOSS_TOUCH})")
            # specs/20h: a fight with `needs` the Power Beam still hurts (Metroid Prime: the Torizo's table)
            weapon = (f"imune ao Power Beam; {way}" if total is None else f"{total} tiros do Power Beam ou {way}")
        else:
            weapon = f"{total} tiros do Power Beam"
        kinds = ", ".join(f"{n} {k}" for k, n in sorted(collections.Counter(e.kind for e in bosses_here).items()))
        lines.append(f"{a.room} (Prime: {a.prime}): {kinds} + "
                     f"{len(spawns) - len(bosses_here)} outros, {cond}, bit ${a.bit:02X}, {weapon} "
                     f"(rodada {rounds.get(a.room, '?')}), até {worst} por golpe, {prize}")
        if any(e.species.ptr == B.SPORE_SPAWN for e in spawns):
            problems += [f"{tag}: {w}" for w in check_spore_spawn(r, spawns)]
        if torizo_arena(a):   # specs/18k
            problems += [f"{tag}: {w}" for w in check_torizo(a, r, spawns)]
        if any(ninja_species(e.species.ptr) for e in spawns):   # specs/19h
            problems += [f"{tag}: {w}" for w in check_ninja(r, spawns)]
    if built is not None:
        problems += check_arenas_in_rom(built)
    return problems, lines


def arena_area(a):
    """specs/18h: the area (tools/areas.py AREAS) whose built rooms hold arena `a`'s room, None if none."""
    return next((ar for ar in AREAS if a.room in ar.by_key()), None)


def prize_name(key) -> str:
    """specs/18h: a placed item's key as the arenas' line names it: the Chozo's by its index (as 14b's line), others by world."""
    return str(key[1]) if isinstance(key, tuple) and key[0] == "chozo" else \
        (f"{key[0]} {key[1]}" if isinstance(key, tuple) else f"tallon {key}")


def check_item_arena(a, r, spawns, placed) -> list[str]:
    """specs/14d, an ITEM arena (tools/chozo/bosses.py): its item a placed item of its room; a boss door of BOSS_DOORS in the
    room (the one the fight shuts) and no other cap kind there; enemies before the fight (the engine runs the enemies only
    when the room's population had one: EnemyMain $A0:8FD4, first_free_enemy_index); the boss kinds (spawned by
    SpawnEnemy, which spawns as many slots as the header's parts: build reads the copy's) of one part each; the fight's
    song set."""
    B, problems = chozo_bosses, []
    mine = [(n, it) for (room, spot), (n, it) in placed.items() if room == a.room and item_bit(n) == a.arg]
    if not mine:
        problems.append(f"condição item com o bit ${a.arg:02X}, de nenhum item colocado da sala")
    doors = [d for d in r.doors if (a.room, d.to_room) in chozo_rooms.BOSS_DOORS]
    if len(doors) != 1 or any(d.lock not in (None, "boss") for d in r.doors):
        problems.append(f"{len(doors)} portas de chefe (BOSS_DOORS) na sala, tampas {[d.lock for d in r.doors]}: a luta "
                        "tranca uma porta, a de chefe")
    if all(e.species.boss for e in spawns):
        problems.append("nenhum inimigo antes da luta: o motor não processaria os gerados ($A0:8FD4)")
    for e in spawns:
        if not e.species.boss:
            continue
        copy = B.COPIES.get(e.species.ptr)
        parts = copy.parts if copy and copy.parts is not None else \
            base_rom().u16(0xA00000 | (copy.source if copy else e.species.ptr) + B.PARTS)
        if parts != 1:
            problems.append(f"{e.kind} em ({e.x},{e.floor}): espécie de {parts} partes (o SpawnEnemy geraria {parts} slots)")
    if a.prize is not None or a.fight_song is None or a.music[0] != B.MINI_BOSS_MUSIC[0]:
        problems.append(f"prêmio {a.prize}, canção da luta {a.fight_song}, música do estado vivo {a.music}: o item é o "
                        "gatilho, a canção uma faixa do set de mini-chefe")
    return problems


def arena_record_at(table: int, k: int) -> int:
    """specs/14d: the address the build gives the fight records ($84, after the table and its end mark)."""
    return table + chozo_bosses.ENTRY_SIZE * len(chozo_bosses.ARENAS) + 2 + k


def item_arena_doors(rom) -> set[int]:
    """specs/14d: the $8F addresses of the ITEM arenas' door cap entries (in their fight records)."""
    B = chozo_bosses
    table = B.ROUTINE + len(B.routine(0))
    out = set()
    for k, a in enumerate(B.ARENAS):
        rec = rom.u16(table + B.ENTRY_SIZE * k + 10)
        if a.condition == B.ITEM and 0x8000 <= rec <= 0xFFF9:
            out.add(0x8F0000 | rom.u16(0x840000 | rec + 4))
    return out


def check_arenas_in_rom(rom) -> list[str]:
    """check_arenas' built-ROM part."""
    B = chozo_bosses
    manifest = json.loads((BUILT_ROM.parent / "manifest.json").read_text())
    problems = []
    table = B.ROUTINE + len(B.routine(0))
    if rom.read(B.ROUTINE, len(B.routine(table))) != B.routine(table):
        problems.append(f"arenas: a rotina em ${B.ROUTINE:06X} difere da que bosses.py gera (reconstruir?)")
    want_entries, records = [], b""
    for a in B.ARENAS:
        if a.room not in manifest:
            problems.append(f"arena {a.room}: fora do manifest.json (reconstruir)")
            continue
        info = manifest[a.room]
        room = read_room(rom, info["header"])
        conds = [(st.condition, st.addr) for st in room.states]
        alive, dead = (info["states"] + [None, None])[:2]
        # the selector: E629 #bit -> dead, then the default (alive)
        sel = info["header"] + 11
        if rom.u16(sel) != 0xE629 or rom.u8(sel + 2) != a.bit or rom.u16(sel + 3) != (dead or 0) & 0xFFFF \
                or len(room.states) != 2 or room.states[1].addr != alive:
            problems.append(f"arena {a.room}: o cabeçalho não escolhe o estado morto por E629 #${a.bit:02X} "
                            f"(condições {[(f'${c:04X}', f'${s:06X}') for c, s in conds]})")
            continue
        st_alive, st_dead = room.states[1], room.states[0]
        stub = 0x8F0000 | st_alive.main_asm
        # specs/20i: the Lair's alive state calls the routine and then its way out into the ending, which is the dead state's
        # main ASM (check_impact_ending reads that code)
        want_stub, dead_asm = B.stub(), 0
        if a.room == impact_rooms.LAIR:
            dead_asm = st_dead.main_asm
            want_stub = impact_ending.alive_main_asm(B.ROUTINE, dead_asm)
        if st_alive.main_asm < 0x8000 or rom.read(stub, len(want_stub)) != want_stub:
            problems.append(f"arena {a.room}: o estado vivo não chama a rotina (main ASM ${st_alive.main_asm:04X})")
        if (st_alive.music_data, st_alive.music_track) != a.music:
            problems.append(f"arena {a.room}: música do estado vivo {st_alive.music_data:02X}/{st_alive.music_track:02X}")
        area = arena_area(a)   # specs/18h: the dead state plays its area's music
        if (st_dead.main_asm != dead_asm or (dead_asm and dead_asm < 0x8000) or area is None
                or (st_dead.music_data, st_dead.music_track) != area.music):
            problems.append(f"arena {a.room}: estado morto com main ASM ${st_dead.main_asm:04X} ou música "
                            f"{st_dead.music_data:02X}/{st_dead.music_track:02X}")
        prize_at = 0
        placed = [(n, it) for n, it in world_items({r.key for r in world_rooms()}) if (it.room, it.spot) == a.prize]
        if a.prize is not None and not placed:
            continue   # check_arenas says it (the prize is not a placed item)
        if a.prize is not None:
            n, it = placed[0]
            entry = struct.pack("<HBBH", it.kind, *it.spot, item_bit(n))
            lst = 0x8F0000 | st_dead.plm
            k = 0
            while rom.u16(lst + 6 * k) and rom.read(lst + 6 * k, 6) != entry:
                k += 1
            if rom.u16(lst + 6 * k) == 0:
                problems.append(f"arena {a.room}: o prêmio não está na lista de PLMs do estado morto")
            prize_at = lst + 6 * k
        record = 0
        if a.condition == B.ITEM:   # specs/14d: its fight record after the table (quota, song, the door's cap, the enemies)
            record = arena_record_at(table, len(records))
            door_at = 0x8F0000 | rom.u16(record + 4)
            r = area.by_key()[a.room]
            i = next((i for i, d in enumerate(r.doors) if (a.room, d.to_room) in chozo_rooms.BOSS_DOORS), None)
            if i is None:
                problems.append(f"arena {a.room}: sem porta de chefe")
                continue
            x, y, _, _ = build.door_cap_and_screen(r, i)
            cap = struct.pack("<HBBH", build.GREY_DOOR_PLM[r.doors[i].side], x, y, B.GREY_DOOR_KILLS)
            if rom.read(door_at, 6) != cap:
                problems.append(f"arena {a.room}: a tampa da porta em ${door_at:06X} é {rom.read(door_at, 6).hex()}, "
                                f"esperado {cap.hex()} (cinza de cota de mortes, sem bit de porta)")
            spawns = area.enemies.get(a.room, [])
            records += B.fight_record(a, sum(not e.species.harmless for e in spawns), door_at,
                                      [e.entry() for e in spawns if e.species.boss])
        want_entries.append(B.table_entry(info["header"], a, prize_at, record))
    want = b"".join(want_entries) + b"\x00\x00" + records
    if rom.read(table, len(want)) != want:
        problems.append(f"arenas: a tabela em ${table:06X} (e os registros de luta) difere das ARENAS "
                        f"({rom.read(table, len(want)).hex()} != {want.hex()})")
    # specs/14c: the Spore Spawn's patches in $A5 (Flaahgra's colours, the death's BG rows = the ruins' lines, no camera hook);
    # its species header and vulnerability table the vanilla ones (the fight check_arenas weighs is the base ROM's)
    if any(e.species.ptr == B.SPORE_SPAWN for a in B.ARENAS for e in CHOZO.enemies.get(a.room, [])):   # the Chozo's
        base = base_rom()
        head = 0xA00000 | B.SPORE_SPAWN
        vuln = 0xB40000 | base.u16(head + 0x3C)
        for what, addr, n in (("cabeçalho da espécie", head, 0x40), ("tabela de vulnerabilidade", vuln, 22)):
            if rom.read(addr, n) != base.read(addr, n):
                problems.append(f"Spore Spawn: {what} em ${addr:06X} difere da base")
        for addr, data in B.spore_spawn_patches(base, build.ruins_palette(base)):
            got = rom.read(addr, len(data))
            if got != data:
                at = next(k for k in range(len(data)) if got[k] != data[k])
                problems.append(f"Spore Spawn: ${addr + at:06X} na ROM é ${got[at]:02X}, bosses.py gera ${data[at]:02X} "
                                f"(cores do Flaahgra, linhas do fundo na morte, gancho da câmera)")
    # specs/18k: the Torizo's patches in $AA and $8D (the area reads as area 0, no haze, its spot, Thardus' colours); its
    # species header and vulnerability table the vanilla ones; no read of the area left in its code
    # specs/19h: the ninja pirates' leap palette patch ($B2: the init's operand -> the Phazon Elite's colours); the vanilla
    # palette $B2:8727 and the vanilla ninja's header untouched; no room of ours with a vanilla ninja (check_bosses: no copied
    # source in a room)
    if any(ninja_species(e.species.ptr) for a in B.ARENAS for e in (arena_area(a).enemies.get(a.room, []) if arena_area(a) else [])):
        base = base_rom()
        at, vanilla = B.NINJA_LINE7_LOAD
        got = rom.read(at, 3)
        line7 = 0xB20000 | int.from_bytes(got[1:3], "little")
        if got[0] != vanilla[0] or line7 == B.NINJA_LINE7 or base.read(line7, 32) != b"\xFF" * 32:
            problems.append(f"Phazon Elite: o init dos ninjas em ${at:06X} lê {got.hex()} (a paleta do salto fora do espaço livre "
                            "do $B2?)")
        else:
            for addr, data in B.ninja_patches(base, line7):
                if rom.read(addr, len(data)) != data:
                    problems.append(f"Phazon Elite: ${addr:06X} na ROM difere do que bosses.py gera (cores do salto)")
        if rom.read(B.NINJA_LINE7, 32) != base.read(B.NINJA_LINE7, 32):
            problems.append(f"Phazon Elite: a paleta vanilla ${B.NINJA_LINE7:06X} mudou (é de 2 piratas vanilla)")
        if [rom.u16(line7 + 2 * i) for i in range(16)] == [base.u16(B.NINJA_LINE7 + 2 * i) for i in range(16)]:
            problems.append("Phazon Elite: as cores do salto iguais às vanilla")
    torizos = [a for a in B.ARENAS if torizo_arena(a)]
    if torizos:
        base = base_rom()
        head = 0xA00000 | B.TORIZO
        vuln = 0xB40000 | base.u16(head + 0x3C)
        for what, addr, n in (("cabeçalho da espécie", head, 0x40), ("tabela de vulnerabilidade", vuln, 22)):
            if rom.read(addr, n) != base.read(addr, n):
                problems.append(f"Torizo: {what} em ${addr:06X} difere da base")
        spot = next(e.species.fixed for a in torizos for e in arena_area(a).enemies.get(a.room, [])
                    if torizo_species(e.species.ptr))
        for addr, data in B.torizo_patches(base, spot):
            got = rom.read(addr, len(data))
            if got != data:
                at = next(k for k in range(len(data)) if got[k] != data[k])
                problems.append(f"Torizo: ${addr + at:06X} na ROM é ${got[at]:02X}, bosses.py gera ${data[at]:02X} "
                                f"(leituras da área, bruma, posição, cores do Thardus)")
        # the colours read back on their own: every body colour (1-14, but black, which stays) of its palettes and every colour
        # of the chest's pulse differs from the base ROM's (the Torizo's pink would show: emulator, 18k)
        same = [f"${t + 2 * i:06X}" for t in B.TORIZO_PALETTES for i in range(1, 15)
                if base.u16(t + 2 * i) and rom.u16(t + 2 * i) == base.u16(t + 2 * i)]
        same += [f"${at + 2 * i:06X}" for at in B.palfx_frames(base, B.TORIZO_PALFX) for i in range(3)
                 if base.u16(at + 2 * i) and rom.u16(at + 2 * i) == base.u16(at + 2 * i)]
        if same:
            problems.append(f"Torizo: cores iguais às do Torizo vanilla (sem as do Thardus) em {same[:6]}")
        # specs/19k: one spot for every Torizo copy (its tables hold one); in a Torizo arena of OMEGA_AREA (the Mines), each palette
        # load of TORIZO_AREA_LOADS a JSR to a selector in $AA's free space that, in that area, reads the Omega Pirate's copy of its
        # table (omega_colours of the vanilla one: not the Thardus' nor the vanilla colours), else the table in place
        spots = {e.species.fixed for a in torizos for e in arena_area(a).enemies.get(a.room, []) if torizo_species(e.species.ptr)}
        if len(spots) != 1:
            problems.append(f"Torizo: posições fixas diferentes {sorted(spots)} (as tabelas do init guardam uma só)")
        if B.OMEGA_AREA != MINES.number:
            problems.append(f"Torizo: OMEGA_AREA {B.OMEGA_AREA} não é a área da Mines ({MINES.number})")
        if any(arena_area(a) is MINES for a in torizos):
            for at, table in B.TORIZO_AREA_LOADS:
                got = rom.read(at, 3)
                sel = 0xAA0000 | int.from_bytes(got[1:3], "little")
                if got[0] != 0x20 or sel & 0xFFFF < 0xF7D3:
                    problems.append(f"Omega Pirate: ${at:06X} é {got.hex()} (não um JSR ao seletor no espaço livre do $AA)")
                    continue
                omega = 0xAA0000 | rom.u16(sel + 13)
                if rom.read(sel, 16) != B.omega_selector(table, omega) or omega & 0xFFFF < 0xF7D3:
                    problems.append(f"Omega Pirate: o seletor em ${sel:06X} difere de bosses.omega_selector (tabela ${table:04X})")
                    continue
                row = [base.u16(0xAA0000 | table + 2 * i) for i in range(16)]
                mine = [rom.u16(omega + 2 * i) for i in range(16)]
                if mine != B.omega_colours(row):
                    problems.append(f"Omega Pirate: as cores em ${omega:06X} não são as de bosses.omega_colours")
                # (a near-black shade, every channel <= 1 of 31, may be the Thardus' too: both ramps start at black)
                dark = lambda c: all((c >> k) & 0x1F <= 1 for k in (0, 5, 10))   # noqa: E731
                if any(mine[i] == row[i] or (mine[i] == rom.u16(0xAA0000 | table + 2 * i) and not dark(mine[i]))
                       for i in range(1, 15) if row[i]):
                    problems.append(f"Omega Pirate: cores em ${omega:06X} iguais às vanilla ou às do Thardus")
        lo, hi = B.TORIZO_CODE
        code = rom.read(lo, hi - lo + 1)
        reads = [lo + k for k in range(len(code) - 2) if code[k] in (0xAC, 0xAD, 0xAE) and code[k + 1:k + 3] == b"\x9f\x07"]
        if reads:
            problems.append(f"Torizo: leituras da área ($079F) que sobraram no código: {[f'${a:06X}' for a in reads]}")
        for a in torizos:
            for st in manifest.get(a.room, {}).get("states", []):
                if any(pl[0] == B.TORIZO_STATUE_PLM for pl in room_plms(rom, st)):
                    problems.append(f"arena {a.room}: o PLM da estátua ${B.TORIZO_STATUE_PLM:04X} no estado ${st & 0xFFFF:04X}")
    for key, info in manifest.items():
        if key == "banks":
            continue
        if any(st.condition == 0xE612 for st in read_room(rom, info["header"]).states):
            problems.append(f"{key}: estado com a condição E612 (evento 0: a porta cinza tipo 3 o liga)")
    return problems


def frigate_species(kind: str):
    from frigate.enemies import SPECIES
    return SPECIES.get(kind)


def check_species_copies(rom, base) -> list[str]:
    """specs/14a: the built ROM's species copies (tools/chozo/bosses.py COPIES) against their sources in the base ROM."""
    problems = []
    B = chozo_bosses
    for c in B.COPIES.values():
        tag = f"cópia $A0:{c.ptr:04X} de ${c.source:04X}"
        src, at = base.read(0xA00000 | c.source, B.SPECIES_SIZE), 0xA00000 | c.ptr
        got = rom.read(at, B.SPECIES_SIZE)
        if rom.read(0xA00000 | c.source, B.SPECIES_SIZE) != src:
            problems.append(f"{tag}: o cabeçalho vanilla ${c.source:04X} mudou na ROM construída")
        bank = src[B.BANK]
        src_pal = (bank << 16) | int.from_bytes(src[B.PALETTE:B.PALETTE + 2], "little")
        if rom.read(src_pal, 32) != base.read(src_pal, 32):
            problems.append(f"{tag}: a paleta vanilla ${src_pal:06X} mudou na ROM construída")
        want = bytearray(src)
        want[B.DAMAGE:B.DAMAGE + 2] = c.damage.to_bytes(2, "little")
        if c.parts is not None:   # specs/14d
            want[B.PARTS:B.PARTS + 2] = c.parts.to_bytes(2, "little")
        if c.health is not None:   # specs/18g
            want[B.HEALTH:B.HEALTH + 2] = c.health.to_bytes(2, "little")
        if c.touch is not None:   # specs/18l
            want[B.TOUCH:B.TOUCH + 2] = c.touch.to_bytes(2, "little")
        own = {}   # specs/18l: the copy's own shot AI (in its AI bank) and table ($B4), at the pointers its header has
        for off, data, in_bank in ((B.SHOT, c.shot, src[B.BANK]), (B.VULN, c.vulnerability, 0xB4)):
            if data is not None:
                want[off:off + 2] = got[off:off + 2]
                own[off] = ((in_bank << 16) | int.from_bytes(got[off:off + 2], "little"), data)
        if c.recolour:
            want[B.PALETTE:B.PALETTE + 2] = got[B.PALETTE:B.PALETTE + 2]   # its own palette: checked below
        diff = [i for i in range(B.SPECIES_SIZE) if got[i] != want[i]]
        if diff:
            problems.append(f"{tag}: bytes do cabeçalho diferentes da origem com toque {c.damage} em "
                            f"{[f'+${i:02X}' for i in diff]} (vida {int.from_bytes(got[4:6], 'little')}, "
                            f"toque {int.from_bytes(got[6:8], 'little')}, tiles {got[0x36:0x39][::-1].hex().upper()})")
            continue
        for off, (where, data) in own.items():   # specs/18l
            what = "a IA de tiro" if off == B.SHOT else "a tabela de vulnerabilidade"
            if where & 0xFFFF < 0x8000 or base.read(where, len(data)) != b"\xFF" * len(data):
                problems.append(f"{tag}: {what} em ${where:06X}, fora do espaço livre do banco")
            elif rom.read(where, len(data)) != data:
                problems.append(f"{tag}: {what} em ${where:06X} diferente da tabela de cópias ({rom.read(where, len(data)).hex()})")
        if c is B.METROID and base.read(0xA30000 | B.METROID_SHOT_ENTRY, len(B.METROID_SHOT_VANILLA)) != B.METROID_SHOT_VANILLA:
            problems.append(f"{tag}: o ramo do Metroid_Shot em $A3:{B.METROID_SHOT_ENTRY:04X} não é o esperado")
        if c.recolour:
            pal_at = (bank << 16) | int.from_bytes(got[B.PALETTE:B.PALETTE + 2], "little")
            colours = c.palette([base.u16(src_pal + 2 * i) for i in range(16)])
            if pal_at == src_pal or pal_at & 0xFFFF < 0x8000:
                problems.append(f"{tag}: paleta própria em ${pal_at:06X} (a vanilla é ${src_pal:06X})")
            elif base.read(pal_at, 32) != b"\xFF" * 32:
                problems.append(f"{tag}: paleta própria em ${pal_at:06X}, fora do espaço livre do banco")
            elif [rom.u16(pal_at + 2 * i) for i in range(16)] != colours:
                problems.append(f"{tag}: paleta em ${pal_at:06X} diferente das cores da tabela (texturas do Prime)")
    return problems


# specs/12i: what makes a species harmless (Species.harmless), read from the base ROM: its header's touch damage is 0 and
# its init routine starts by setting "no collision with Samus" in its properties (kEnemyProps_DisableSamusColl $2000:
# LDX $0E54; LDA $0F86,X; ORA #$2000; STA $0F86,X; the morph ball eye's $A8:9058, sm_a8.c:402). That it fires nothing is
# read in its code (MorphBallEye_*, sm_a8.c:402-482: only the HDMA light beam), not checked here.
HARMLESS_INIT = bytes.fromhex("AE540EBD860F0900209D860F")


def harmless_problems(sp) -> list[str]:
    rom, at = base_rom(), 0xA00000 | sp.ptr
    out = []
    if rom.u16(at + 6):
        out.append(f"espécie ${sp.ptr:04X} marcada inofensiva tira {rom.u16(at + 6)} por toque")
    init = (rom.u8(at + 0x0C) << 16) | rom.u16(at + 0x12)
    if rom.read(init, len(HARMLESS_INIT)) != HARMLESS_INIT:
        out.append(f"espécie ${sp.ptr:04X} marcada inofensiva: o init ${init:06X} não desliga a colisão com a Samus")
    return out


def check_props(r, props: dict, l1: list[int], wb: int) -> list[str]:
    """Set pieces are background: open air (type 0) standing on a solid row."""
    problems = []
    for p in props.get(r.key, []):
        tag = f"{r.key}: {p.stamp} em ({p.x},{p.floor})"
        if any(l1[y * wb + x] >> 12 != 0 for x, y, _ in p.cells()):
            problems.append(f"{tag} invade parede, porta ou plataforma")
        if any(l1[p.floor * wb + x] >> 12 != 8 for x in range(p.x, p.x + len(p.rows[0]))):
            problems.append(f"{tag} não está apoiado no chão")
    return problems


def check_backdrop(r, lv, l1: list[int], bts: bytearray) -> list[str]:
    """hangar_colisao_nave_igual: the back wall (only on air) and the landing pad (only on solid
    blocks) change the art, never the collision: every block type and BTS, the gunship's
    invisible blocks included, matches the room built without them."""
    if not (lv.backdrop or lv.skin):
        return []
    plain_l1, plain_bts = dataclasses.replace(lv, backdrop=[], skin=[]).build_blocks()
    ship = {(x, y) for x, y, _, _ in ending.ship_blocks(*r.ship)} if r.ship else set()
    problems = []
    for i, (a, b) in enumerate(zip(l1, plain_l1)):
        x, y = i % lv.wb, i // lv.wb
        if (x, y) in ship and (a != b or bts[i] != plain_bts[i]):
            problems.append(f"{r.key}: colisão da nave mudou em ({x},{y})")
        elif a >> 12 != b >> 12 or bts[i] != plain_bts[i]:
            problems.append(f"{r.key}: fundo/acabamento mudou a colisão em ({x},{y})")
    return problems


SAMUS_STANDING_ROWS = 3   # standing Samus is 42 px tall


def check_save_station(r, passable, reached: set) -> list[str]:
    """Pedestal = 2 solid blocks; Samus must fit standing on them and be able to walk there."""
    if not r.save_station:
        return []
    x, floor = r.save_station
    tag = f"{r.key}: save station em ({x},{floor})"
    problems = []
    if passable(x, floor) or passable(x + 1, floor):
        problems.append(f"{tag} sem pedestal sólido")
    body = [(bx, floor - 1 - k) for bx in (x, x + 1) for k in range(SAMUS_STANDING_ROWS)]
    if not all(passable(bx, by) for bx, by in body):
        problems.append(f"{tag} sem altura para a Samus em pé")
    elif (x, floor - 1) not in reached:
        problems.append(f"{tag} inalcançável a partir das portas")
    return problems


def check_map_station(r, passable, reached: set) -> list[str]:
    """Samus uses the station by walking into an access block (x-2 or x+1, floor-2) at cannon
    height, standing on row `floor`: that side needs room for her and must be reachable."""
    if not r.map_station:
        return []
    x, floor = r.map_station
    tag = f"{r.key}: map station em ({x},{floor})"
    usable = []
    for side_x, access_x in ((x + 2, x + 1), (x - 3, x - 2)):
        stand = [(side_x, floor - 1 - k) for k in range(SAMUS_STANDING_ROWS)]
        if (not passable(access_x, floor - 2) and passable(access_x, floor - 1) and not passable(side_x, floor)
                and all(passable(bx, by) for bx, by in stand) and (side_x, floor - 1) in reached):
            usable.append(side_x)
    return [] if usable else [f"{tag} sem lado onde a Samus alcance o terminal de pé"]


def check_missile_station(r, passable, reached: set) -> list[str]:
    """specs/19l: the missile refill station (Canvas.refill_station: the block (x, floor-2) and its access blocks x-1 / x+1 over
    the stem (x, floor-1)): Samus uses it walking into an access block at cannon height, standing on row `floor` next to it
    (x+2 or x-2): that side needs room for her and must be reachable (check_map_station's rule)."""
    if not r.missile_station:
        return []
    x, floor = r.missile_station
    usable = []
    for side_x, access_x in ((x + 2, x + 1), (x - 2, x - 1)):
        stand = [(side_x, floor - 1 - k) for k in range(SAMUS_STANDING_ROWS)]
        if (not passable(access_x, floor - 2) and passable(access_x, floor - 1) and not passable(side_x, floor)
                and all(passable(bx, by) for bx, by in stand) and (side_x, floor - 1) in reached):
            usable.append(side_x)
    return [] if usable else [f"{r.key}: missile station em ({x},{floor}) sem lado onde a Samus alcance o terminal de pé"]


def check_ship(r, passable, reached: set) -> list[str]:
    """The gunship hovers over the ground like on the Landing Site: Samus walks under it, and
    boards it standing on the top centre (GunshipTop_8 wants her within 8 px of the centre)."""
    if not r.ship:
        return []
    cx, ground = r.ship
    tag = f"{r.key}: nave em ({cx},{ground})"
    problems = []
    xs = range(cx - ending.SHIP_HALF_WIDTH, cx + ending.SHIP_HALF_WIDTH)
    if any(passable(x, ground) for x in xs):
        problems.append(f"{tag} sem chão embaixo")
    under = [(x, y) for x in xs for y in range(ground + ending.SHIP_BOTTOM_ROW + 1, ground)]
    if not all(passable(x, y) for x, y in under):
        problems.append(f"{tag}: vão sob a nave bloqueado")
    top = ground + ending.SHIP_TOP_ROW
    stand = [(x, top - 1 - k) for x in (cx - 1, cx) for k in range(SAMUS_STANDING_ROWS)]
    if not all(passable(x, y) for x, y in stand):
        problems.append(f"{tag} sem altura para a Samus em pé em cima")
    elif (cx, top - 1) not in reached:
        problems.append(f"{tag}: topo inalcançável a partir das portas")
    return problems


BOSS_ROOM = FRIGATE.boss_room
START_ROOM = FRIGATE.load_stations[0].room   # the hangar


def reachable_rooms(by_key: dict, start: str, boss_dead: bool) -> set[str]:
    seen, stack = {start}, [start]
    while stack:
        r = by_key[stack.pop()]
        for d in r.doors:
            if d.locked and not boss_dead:
                continue
            if d.to_room not in seen:
                seen.add(d.to_room)
                stack.append(d.to_room)
    return seen


def check_progression(by_key: dict) -> list[str]:
    """Before the boss the route must lead to the boss and stay off the escape route;
    after the boss, the escape must lead back to the hangar."""
    problems = []
    before = reachable_rooms(by_key, START_ROOM, boss_dead=False)
    if BOSS_ROOM not in before:
        problems.append("antes do chefe: o Reactor Core é inalcançável a partir do hangar")
    escape_only = {"mech_shaft", "elevator_alpha", "biotech_2", "vent_a", "vent_b", "vent_c", "vent_d",
                   "vent_e", "vent_f", "subvent_a", "subvent_b", "monitor_hall", "elevator_gamma"}
    leaked = sorted(before & escape_only)
    if leaked:
        problems.append(f"antes do chefe dá para entrar na rota de fuga: {leaked}")
    after = reachable_rooms(by_key, BOSS_ROOM, boss_dead=True)
    if START_ROOM not in after:
        problems.append("depois do chefe: não há caminho de volta ao hangar")
    unreached = sorted(set(by_key) - after)
    if unreached:
        problems.append(f"salas nunca alcançadas: {unreached}")
    return problems


# area-specific progression checks, by AreaDef.key
PROGRESSION = {FRIGATE.key: check_progression}


def main() -> int:
    problems = check()
    for p in problems:
        print("ERRO", p)
    if not problems:
        print(tallon_report())
    rooms = [r for a in AREAS for r in a.rooms]
    print(f"{len(rooms)} salas, {sum(len(r.doors) for r in rooms)} portas, {len(problems)} problemas")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

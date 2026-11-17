"""Impact Crater rooms (inside SM area 0, with the Tallon: tools/areas.py IMPACT_CRATER_AREA): the room graph, the map and Prime's
locks (specs/20c-grafo-e-mapa-impact.md). specs/20c: data only; the regions' children build the rooms (ACTIVE_REGIONS).

All 12 rooms of Prime's Impact Crater (research/prime_worlds.json, MLVL "Impact Crater"), one SM room per Prime room (epic 20, user
decision 1), with the Prime door graph in LINKS (11 pairs, 22 docks, all with their way back; no loop: a straight path Crater Entry
Point -> Crater Tunnel A -> Phazon Core -> Crater Tunnel B -> Phazon Infusion Chamber -> Subchambers One to Five -> Metroid Prime
Lair, and the Crater Missile Station a dead end off the Phazon Core). The size comes from the Prime box by the Tallon's rule
(tallon/rooms.py `screens`: 30 m a screen, at most 6 x 4): 90 screens (specs/20a).

Map: x/y in area 0's 64x32 pause-map grid, shared with the Tallon (tools/tallon/rooms.py ALL_ROOMS, rows 3-17). The crater sits in the
free space right under the Tallon's Artifact Temple (x 32-37, y 9-12: Prime enters the crater from it, epic 20 decision 7), as a side
view: west to east on the map = Prime's north to south (-y) for the upper rooms (Entry Point, Tunnel A, Phazon Core, Tunnel B,
Infusion Chamber, rows 13-15), then the Subchambers step down and back west, as Prime's descent does (each Subchamber lower in z than
the one before), to the Lair at the bottom (rows 26-29). Hand-placed (12 rooms in a line: no search needed): every door touches its
neighbour, no room overlaps a Tallon room, and the three falls of Prime's descent (Infusion Chamber -> Subchamber One, Subchamber
Three -> Four, Subchamber Five -> Lair: each dock on the floor of the upper room and the ceiling of the lower one, or nearly) are
floor/ceiling doors. The validator checks the whole table (tools/validate.py check_impact_graph), each region alone, and the area 0
map with the Tallon's (no tile twice, the save list within area 0's 80 bytes).

Regions (the epic's children that build them): A the way in (Crater Entry Point, Tunnel A; 20e), B the upper crater (Phazon Core,
Missile Station, Tunnel B; 20f), C the descent (Phazon Infusion Chamber, Subchambers One to Five; 20g), D the Metroid Prime Lair
(20h).

Prime's locks are recorded as data (DOCK_LOCKS, KEY_BEAM, FEATURES), read from Prime's objects (research/prime_impact_locks.json,
written by tools/dump_prime_locks.py for "Impact Crater"); no SM item or mechanism is chosen here (the region children). Every door
of the five upper links is a plasma door on both sides; the Phazon Infusion Chamber's door to the Tunnel B also has an event lock
("Actor Door Lock"); from the Infusion Chamber down there is no door at all (Prime's fall). No room is hot (no "Area Damage"),
snowy, rainy or flooded, nothing only the Power Bomb breaks, no door only the Super Missile opens: check_prime checks it.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from chozo.rooms import EVENT, KEY, prime_dock_locks   # noqa: F401 (the lock kinds, as the Chozo's)
from frigate.rooms import OPPOSITE, DoorLink, RoomDef
from magmoor.rooms import BEAM_OF_VULN
from mines.rooms import super_only
from tallon.rooms import LOCK_OF, PLASMA, Gate, placeholder, screens

from . import style
from .layouts import ACID, LAYOUTS

PREFIX = "impact_"
REGIONS = {
    "A": "A entrada: Crater Entry Point e Crater Tunnel A (20e)",
    "B": "A cratera de cima: Phazon Core, Crater Missile Station e Crater Tunnel B (20f)",
    "C": "A descida: Phazon Infusion Chamber e Subchambers One a Five (20g)",
    "D": "A Metroid Prime Lair (20h)",
}
ACTIVE_REGIONS: frozenset[str] = frozenset({"A", "B", "C", "D"})   # specs/20c: none built; 20e: A; 20f: B; 20g: C; 20h: D
ENTRY = "impact_entry_point"   # Prime's way in (its WorldTeleporter from the Artifact Temple; epic 20, decision 7)
LAIR = "impact_lair"           # the last room (Metroid Prime's second stage, the world's end)
# specs/20e (epic 20, decision 7, accepted by the user): the way in = the Artifact Temple's teleporter, a working elevator of ours
# (tools/areas.py ELEVATORS) from the Tallon's temple (going down) to the Entry Point (going up), both in area 0. It works once the
# Omega Pirate (specs/19k) is dead: the temple's room state with the elevator's platform is selected by the Omega arena's own bit
# ($10 of area 5, set by the arena routine when the fight is won: tools/chozo/bosses.py ARENAS), no artifact; before, the temple's
# default state has no platform (the pad does nothing). The build and the validator read the arena of OPENS_AFTER.
TELEPORTER = ("tallon_artifact_temple", ENTRY)
# specs/20f: Prime's missile recharge station (the Crater Missile Station's SpecialFunction "Missile Station", function 23, specs/20a)
# = the SM's missile refill station (RoomDef.missile_station), only there; no item in the crater
MISSILE_STATION = "impact_missile_station"
OPENS_AFTER = "mines_elite_quarters"   # the Omega Pirate's arena (chozo/bosses.py ARENAS)


@dataclass(frozen=True)
class Row:
    key: str
    prime: int                   # room index in Prime's MLVL
    name: str                    # Prime name
    region: str
    box: tuple[int, int, int]    # Prime room box (x, y, z) in metres, rounded (aabb)
    map_x: int
    map_y: int


TABLE = [
    # --- A ---
    Row("impact_entry_point", 0, "Crater Entry Point", "A", (63, 64, 55), 26, 14),
    Row("impact_tunnel_a", 1, "Crater Tunnel A", "A", (35, 71, 21), 28, 15),
    # --- B ---
    Row("impact_phazon_core", 2, "Phazon Core", "B", (142, 150, 102), 30, 13),
    Row("impact_missile_station", 3, "Crater Missile Station", "B", (34, 36, 23), 29, 14),
    Row("impact_tunnel_b", 4, "Crater Tunnel B", "B", (36, 71, 25), 35, 14),
    # --- C ---
    Row("impact_infusion_chamber", 5, "Phazon Infusion Chamber", "C", (73, 100, 72), 37, 14),
    Row("impact_subchamber_one", 6, "Subchamber One", "C", (120, 60, 76), 36, 16),
    Row("impact_subchamber_two", 7, "Subchamber Two", "C", (56, 134, 51), 32, 18),
    Row("impact_subchamber_three", 8, "Subchamber Three", "C", (55, 126, 53), 28, 19),
    Row("impact_subchamber_four", 9, "Subchamber Four", "C", (118, 53, 47), 29, 21),
    Row("impact_subchamber_five", 10, "Subchamber Five", "C", (50, 57, 142), 33, 22),
    # --- D ---
    Row("impact_lair", 11, "Metroid Prime Lair", "D", (121, 125, 144), 32, 26),
]

# (room, side, screen) <-> (room, side, screen), one per Prime door pair; sides opposite (R-L, B-T)
LINKS = [
    (("impact_entry_point", "R", 1), ("impact_tunnel_a", "L", 0)),
    (("impact_tunnel_a", "R", 0), ("impact_phazon_core", "L", 2)),
    (("impact_missile_station", "R", 0), ("impact_phazon_core", "L", 1)),
    (("impact_phazon_core", "R", 1), ("impact_tunnel_b", "L", 0)),
    (("impact_tunnel_b", "R", 0), ("impact_infusion_chamber", "L", 0)),
    (("impact_infusion_chamber", "B", 1), ("impact_subchamber_one", "T", 2)),
    (("impact_subchamber_two", "R", 0), ("impact_subchamber_one", "L", 2)),
    (("impact_subchamber_three", "R", 0), ("impact_subchamber_two", "L", 1)),
    (("impact_subchamber_three", "B", 1), ("impact_subchamber_four", "T", 0)),
    (("impact_subchamber_four", "R", 1), ("impact_subchamber_five", "L", 0)),
    (("impact_subchamber_five", "B", 0), ("impact_lair", "T", 1)),
]

# --- Prime's locks, as data (specs/20c) ------------------------------------------------------------------------------
# Per dock (this room, the room the door leads to): the kinds of lock Prime has there, by the Chozo's rule (chozo/rooms.py
# prime_dock_locks, on research/prime_impact_locks.json): key = "Trigger_DoorKey" (a coloured door: the 10 docks of the five upper
# links), event = "Actor Door Lock" (the Phazon Infusion Chamber's door back to the Tunnel B: it locks behind Samus, knowledge:
# the way down has no way back). The 12 docks from the Infusion Chamber down have no lock: Prime's fall (absent here).
DOCK_LOCKS = {
    ("impact_entry_point", "impact_tunnel_a"): {"key"},
    ("impact_tunnel_a", "impact_phazon_core"): {"key"},
    ("impact_tunnel_a", "impact_entry_point"): {"key"},
    ("impact_phazon_core", "impact_missile_station"): {"key"},
    ("impact_phazon_core", "impact_tunnel_a"): {"key"},
    ("impact_phazon_core", "impact_tunnel_b"): {"key"},
    ("impact_missile_station", "impact_phazon_core"): {"key"},
    ("impact_tunnel_b", "impact_infusion_chamber"): {"key"},
    ("impact_tunnel_b", "impact_phazon_core"): {"key"},
    ("impact_infusion_chamber", "impact_tunnel_b"): {"event", "key"},
}

# The beam of each key dock, from its "Trigger_DoorKey" DamageVulnerability (research/prime_impact_locks.json "key_vuln": power,
# ice, wave, plasma; 1 = hurts, 2 = immune), magmoor/rooms.py BEAM_OF_VULN: all 10 plasma (2 2 2 1). Prime's beam, not yet the SM
# mechanism (the region children).
KEY_BEAM = {k: PLASMA for k in DOCK_LOCKS}

# In-room features of Prime (the dumper's names: chozo/rooms.py FEATURES): the Tunnel B's Spider Ball track (77 waypoints; the game
# has no Spider Ball, epic 18: the region child, 20f, gives it another way); "heat" in the Lair = 4 objects whose names have
# "heat"/"varia" (what they are: uncertain, specs/20a; not Prime's heat, which is a SpecialFunction "Area Damage": none here)
FEATURES = {
    "impact_tunnel_b": {"spider"},
    "impact_lair": {"heat"},
}


# specs/20e: Prime's locks of the built links, mapped to the SM's mechanisms (mines/rooms.py GATES' rule): each key dock = the
# beam cap of Prime's colour (KEY_BEAM) on both sides. Region A: the Entry Point <-> Tunnel A plasma doors. specs/20f: region B's
# three links (Tunnel A, Missile Station, Tunnel B <-> Phazon Core), plasma on both sides. specs/20g: the Tunnel B <-> Infusion
# Chamber link, plasma on both sides; the five links down from the Infusion Chamber have no lock (Prime's fall: no cap).
GATES = {frozenset({a, b}): Gate(frozenset({beam}), (a, b)) for a, b, beam in (
    ("impact_entry_point", "impact_tunnel_a", PLASMA),
    ("impact_tunnel_a", "impact_phazon_core", PLASMA),
    ("impact_missile_station", "impact_phazon_core", PLASMA),
    ("impact_phazon_core", "impact_tunnel_b", PLASMA),
    ("impact_tunnel_b", "impact_infusion_chamber", PLASMA))}

# specs/20g: Prime's event locks left out, each with why (the validator waits for every other one in a built link). The Infusion
# Chamber's "Actor Door Lock" on its door back to the Tunnel B shuts the way back once Samus goes down (Prime's final descent, its
# fight scripted room by room): the fight is the Lair's only (epic 20, decision 3), and the game keeps the way back to the
# temple (the validator's walk back to the Entry Point's platform), so the door stays the plasma door of both sides.
EVENT_OUT = {
    ("impact_infusion_chamber", "impact_tunnel_b"): "a porta que tranca atrás na descida final do Prime (a luta é só na Lair, "
                                                    "decisão 3; a volta ao templo fica aberta)",
}


# specs/20h (epic 20, decision 3: Metroid Prime's arena in the Lair, the Omega Pirate's model, its doors shut until the win): the
# Lair's only door, the ceiling one back up to the Subchamber Five, waits for the fight (tools/chozo/bosses.py ARENAS): the grey
# cap of the Torizo's arenas while it lives, no PLM once it is dead (Prime has no door there: the fall; the level's own blue cap
# stays, any shot opens it: the level is the same in both states, build: frigate/rooms.py RoomDef.level). Not a lock of Prime's
# (DOCK_LOCKS has none there): our arena's, as the epic decided.
BOSS_DOORS = {("impact_lair", "impact_subchamber_five"): "20h"}


def build_rooms(regions, extra=frozenset()) -> list[RoomDef]:
    """RoomDefs of the rooms in `regions` and in `extra`, in TABLE order, with the doors between them; a link to a room left out is
    left out too (wall). specs/20c: placeholder boxes; specs/20e: a room with a layout (tools/impact/layouts.py) gets it, in the
    crater's look (impact/style.py: tileset $03, the Mines' rock pieces, its background), and the doors of a link in GATES its caps."""
    from chozo.bosses import arena_of   # specs/20h (chozo/bosses.py imports other areas' packages)
    from chozo.rooms import BOSS_GATE
    regions = set(regions)
    unknown = regions - set(REGIONS)
    if unknown:
        raise ValueError(f"regiões desconhecidas: {sorted(unknown)}")
    rooms: dict[str, RoomDef] = {}
    for t in TABLE:
        if t.region not in regions and t.key not in extra:
            continue
        w, h = screens(t.box)
        shape = LAYOUTS[t.key]() if t.key in LAYOUTS else None
        canvas = shape.canvas if shape else placeholder(w, h)
        if (canvas.w, canvas.h) != (w * 16, h * 16):
            raise ValueError(f"{t.key}: desenho {canvas.w}x{canvas.h} blocos, a tabela diz {w}x{h} telas")
        bg, layer2 = style.BACKGROUND
        rooms[t.key] = RoomDef(t.key, t.prime, t.name, w, h, t.map_x, t.map_y, canvas, tileset=style.TILESET,
                               style=style.STYLE, library_bg=bg, layer2=layer2,
                               elevator=shape.elevator if shape else None, skin=shape.skin if shape else [],
                               save_station=shape.save if shape else None,
                               missile_station=shape.missile_station if shape else None,   # specs/20f
                               acid=ACID.get(t.key) if shape else None)                     # specs/20g
    for (ra, sa, na), (rb, sb, nb) in LINKS:
        if OPPOSITE[sa] != sb:
            raise ValueError(f"porta {ra}.{sa} liga em {rb}.{sb}: lados precisam ser opostos")
        if ra not in rooms or rb not in rooms:
            continue
        da, db = DoorLink(sa, na, rb), DoorLink(sb, nb, ra)
        gate = GATES.get(frozenset({ra, rb}))
        if gate:
            caps = {LOCK_OF[i] for i in gate.items if i in LOCK_OF}
            if len(caps) != 1 or set(gate.capped) != {ra, rb}:
                raise ValueError(f"trava {ra}-{rb}: precisa de um tipo de tampa dos dois lados ({gate})")
            for d in (da, db):
                d.gate, d.lock = gate.items, next(iter(caps))
        for d, key, to in ((da, ra, rb), (db, rb, ra)):
            # specs/20h: the arena's boss door (the Mines' rule, mines/rooms.py build_rooms): lock "boss", the gate BOSS_GATE, its
            # cap in the dead state none (dead_lock)
            if (key, to) in BOSS_DOORS and arena_of(key) is not None:
                if d.lock is not None:
                    raise ValueError(f"porta de chefe {key}->{to} com tampa {d.lock}")
                d.dead_lock, d.lock, d.gate = d.lock, "boss", d.gate | {BOSS_GATE}
        rooms[ra].doors.append(da)
        rooms[rb].doors.append(db)
        da.to_door = len(rooms[rb].doors) - 1
        db.to_door = len(rooms[ra].doors) - 1
    return list(rooms.values())


def region_of(key: str) -> str:
    return next(t.region for t in TABLE if t.key == key)


def reachable(start: str) -> set[str]:
    """The rooms LINKS joins to `start` (doors both ways: Prime's locks are opened by items, not one-way)."""
    seen, todo = {start}, [start]
    while todo:
        k = todo.pop()
        for (ra, _, _), (rb, _, _) in LINKS:
            for a, b in ((ra, rb), (rb, ra)):
                if a == k and b not in seen:
                    seen.add(b)
                    todo.append(b)
    return seen


def check_prime(worlds_json: Path, locks_json: Path) -> list[str]:
    """TABLE and LINKS against Prime's data (every room once with its name and box, the links = Prime's door pairs), and
    DOCK_LOCKS / KEY_BEAM / FEATURES = what research/prime_impact_locks.json gives; no room with Prime's heat ("area_damage"),
    snow or rain ("env_fx"), water, plasma ice or a wave panel ("beam_only"), nothing only the Power Bomb breaks ("pb_only", layer
    0), no door only the Super Missile opens, no transport room (the crater is entered by the Artifact Temple's teleporter, epic
    20 decision 7); the way from the Crater Entry Point to the Metroid Prime Lair exists."""
    world = next(w for w in json.loads(worlds_json.read_text()) if w["name"] == "Impact Crater")
    prime = {a["index"]: a for a in world["areas"]}
    problems = []
    by_prime = {t.prime: t for t in TABLE}
    if len(by_prime) != len(TABLE) or set(by_prime) != set(prime):
        problems.append(f"impact: tabela tem as salas {sorted(by_prime)}, o Prime tem {sorted(prime)}")
    if len({t.key for t in TABLE}) != len(TABLE):
        problems.append("impact: chave de sala repetida na tabela")
    for t in TABLE:
        if t.region not in REGIONS:
            problems.append(f"{t.key}: região {t.region!r} desconhecida")
        if not t.key.startswith(PREFIX):
            problems.append(f"{t.key}: chave sem o prefixo {PREFIX}")
        if t.name.startswith("Transport to "):
            problems.append(f"{t.key}: sala de transporte na cratera (a entrada é o teleporte do Artifact Temple)")
        a = prime.get(t.prime)
        if a is None:
            continue
        b = a["aabb"]
        box = tuple(round(b[i + 3] - b[i]) for i in range(3))
        if (a["name"], box) != (t.name, t.box):
            problems.append(f"{t.key}: P{t.prime} no Prime é {a['name']!r} {box}, a tabela diz {t.name!r} {t.box}")
    key_of = {t.prime: t.key for t in TABLE}
    key_prime = {t.key: t.prime for t in TABLE}
    unknown = sorted({k for a, b in LINKS for k in (a[0], b[0])} - set(key_prime))
    if unknown:
        return problems + [f"impact: ligações com salas fora da tabela: {unknown}"]
    ours = [frozenset((key_prime[a[0]], key_prime[b[0]])) for a, b in LINKS]
    theirs = {frozenset((a["index"], d["to_area"])) for a in world["areas"] for d in a["docks"]}
    if len(set(ours)) != len(ours) or set(ours) != theirs:
        problems.append(f"impact: ligações diferentes do Prime: sobram {sorted(map(sorted, set(ours) - theirs))}, "
                        f"faltam {sorted(map(sorted, theirs - set(ours)))}")
    if {ENTRY, LAIR} <= set(key_prime) and LAIR not in reachable(ENTRY):
        problems.append(f"impact: sem caminho de {ENTRY} até {LAIR} pelas ligações")
    data = json.loads(locks_json.read_text())
    if set(data) != {str(i) for i in prime}:
        problems.append(f"impact: {locks_json.name} tem as salas {sorted(data, key=int)}, o Prime tem {sorted(prime)}")
    want_locks, want_beam, want_features, supers = {}, {}, {}, []
    want = {"neve ou chuva": set(), "água": set(), "gelo de plasma": set(), "painel de onda": set(), "calor": set(),
            "só Power Bomb": set()}
    for i, room in data.items():
        if int(i) not in key_of:
            continue
        k = key_of[int(i)]
        for d in room["docks"]:
            if d["to"] not in key_of:
                continue
            kinds = prime_dock_locks(d["objects"])
            if kinds:
                want_locks[(k, key_of[d["to"]])] = kinds
            if KEY in kinds:
                vuln = tuple(d.get("key_vuln") or ())
                want_beam[(k, key_of[d["to"]])] = BEAM_OF_VULN.get(vuln, f"vulnerabilidade {vuln}")
            if super_only(d.get("key_vuln_full")):
                supers.append((k, key_of[d["to"]]))
        if room["features"]:
            want_features[k] = set(room["features"])
        for name, hit in (("neve ou chuva", room.get("env_fx") not in (None, 0)), ("água", "water" in room["features"]),
                          ("gelo de plasma", "plasma" in room.get("beam_only", {})),
                          ("painel de onda", "wave" in room.get("beam_only", {})), ("calor", room.get("area_damage")),
                          ("só Power Bomb", any(layer == 0 for *_, layer in room.get("pb_only", [])))):
            if hit:
                want[name].add(k)
    for k in sorted(set(want_locks) | set(DOCK_LOCKS)):
        if want_locks.get(k) != DOCK_LOCKS.get(k):
            problems.append(f"impact: trava da doca {k[0]} -> {k[1]}: o Prime tem {sorted(want_locks.get(k, ()))}, "
                            f"a tabela diz {sorted(DOCK_LOCKS.get(k, ()))}")
    for k in sorted(set(want_beam) | set(KEY_BEAM)):
        if want_beam.get(k) != KEY_BEAM.get(k):
            problems.append(f"impact: cor da porta {k[0]} -> {k[1]}: o Prime tem {want_beam.get(k)}, KEY_BEAM diz "
                            f"{KEY_BEAM.get(k)}")
    for k in sorted(set(want_features) | set(FEATURES)):
        if want_features.get(k) != FEATURES.get(k):
            problems.append(f"impact: {k}: o Prime tem {sorted(want_features.get(k, ()))}, "
                            f"FEATURES diz {sorted(FEATURES.get(k, ()))}")
    for name, rooms in want.items():
        if rooms:
            problems.append(f"impact: salas com {name} no Prime {sorted(rooms)}; a tabela conta com nenhuma")
    for k in supers:
        problems.append(f"impact: a porta {k[0]} -> {k[1]} só abre com o Super Missile no Prime (o épico conta com nenhuma)")
    return problems


ALL_ROOMS = build_rooms(REGIONS)                 # the whole world, for the validator's map checks
ROOMS = build_rooms(ACTIVE_REGIONS)              # what the build gets (specs/20c: nothing; 20e: region A; 20f: and B; 20g: C)

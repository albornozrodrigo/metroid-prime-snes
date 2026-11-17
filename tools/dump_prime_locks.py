"""Dump, per room of one Metroid Prime world, the objects at each door (dock) and the in-room features that gate
movement, for the lock tables of the rooms modules (specs/12c-grafo-e-mapa-chozo.md).

Usage: venv/bin/python -I dump_prime_locks.py <prime_fs dir> <research/prime_worlds.json> "<World name>" <out.json>

retro-data-structures 0.44.1 does not parse every object type (DamageableTrigger, Door): the name and the position are
read from the raw property bytes (property count, name, then the position vector, big endian), as specs/07k did. The
docks' corners in prime_worlds.json are in the room's own space: they are moved by the room's transform. An object is
"at" a dock when it is the dock nearest to it and at most AT_DOCK metres away.
Output: {room index: {"name", "docks": [{"dock", "to", "objects": [[type, name, layer], ...], "key_vuln": [...]}],
"features": {kind: n}, "area_damage": n, "env_fx": n, "beam_only": {beam: n}}}.
specs/17c: "key_vuln" = the beam vulnerabilities (power, ice, wave, plasma; 1 = hurts, 2 = immune) of the dock's
"Trigger_DoorKey" DamageableTrigger (its DamageVulnerability, 40 bytes after the name; the colour of a coloured door: Wave
only = 2 2 1 2), or null; "area_damage" = the room's "SpecialFunction" objects of function 18 (Area Damage: Prime's heat of a
superheated room; the function id 24 bytes after the name). Both read from the raw bytes, as the names and positions are.
specs/18c: "env_fx" = the room's environmental effect, the "AreaAttributes" fx type (0 none, 1 snow, 2 rain, 3 bubbles; parsed
by retro-data-structures; the largest of the room's AreaAttributes) or null without one; "beam_only" = how many of the room's
DamageableTriggers that are not a door's ("Trigger_DoorKey") only one beam hurts (DamageVulnerability as "key_vuln"): Phendrana's
ice that only the Plasma Beam melts (2 2 2 1) and its Wave Beam panels (2 2 1 2), {beam: n}.
specs/19c: "key_vuln_full" = the whole DamageVulnerability of the dock's "Trigger_DoorKey" (its property count, $12, then 16
weaknesses: power, ice, wave, plasma, bomb, power bomb, missile, boost, phazon, ...; then the charged beams' 5 and the beam
combos' 5: super missile, ice spreader, wavebuster, flamethrower, phazon), or null; "pb_only" = the room's objects only the Power
Bomb hurts ([type, name, layer]: a DamageableTrigger, a Platform or an Actor whose DamageVulnerability has the power bomb's value
0 or 1 and none of power, ice, wave, plasma, bomb, missile, boost 0 or 1: the Phazon Mines' Bendezium rocks, walls and grate;
the Platform's vulnerability is read from the raw bytes, 222 after the name: retro-data-structures 0.44.1 fails on it).
"""
import json
import logging
import re
import struct
import sys
from pathlib import Path

from retro_data_structures.asset_manager import AssetManager
from retro_data_structures.file_provider import PathFileProvider
from retro_data_structures.game_check import Game
from retro_data_structures.properties.prime.objects import _FOUR_CC_MAPPING

AT_DOCK = 3.0
AREA_DAMAGE = 18   # SpecialFunction function id of Prime's heat (specs/17c)
BEAMS = ("power", "ice", "wave", "plasma")   # DamageVulnerability order (specs/17c, 18c)
NAME = re.compile(rb"\x00\x00\x00[\x01-\x40]([\x20-\x7e]{2,})\x00")
# specs/19c: where the DamageVulnerability's property count is, after the name, per object type (fixed properties before it)
VULN_AT = {"DamageableTrigger": 36, "Platform": 222, "Actor": 80}
VULN_COUNT = 0x12
PB_INDEX = 5   # power bomb's place in the weaknesses (BEAMS, then bomb, power bomb, missile, boost)


def vulnerability(raw: bytes, at: int) -> list[int] | None:
    """specs/19c: the DamageVulnerability whose property count is at `at` (VULN_COUNT: the plain weaknesses, then two structs,
    each a count and its values), flattened; None if the count is not there."""
    if raw[at:at + 4] != struct.pack(">I", VULN_COUNT):
        return None
    n = VULN_COUNT - 2
    out = list(struct.unpack(f">{n}I", raw[at + 4:at + 4 + 4 * n]))
    p = at + 4 + 4 * n
    for _ in range(2):
        c = struct.unpack(">I", raw[p:p + 4])[0]
        out += struct.unpack(f">{c}I", raw[p + 4:p + 4 + 4 * c])
        p += 4 + 4 * c
    return out
# in-room features (name patterns; type names for GrapplePoint / SpiderBallWaypoint / Water)
FEATURES = {
    "spider": re.compile(r"spider", re.I),
    "bomb_slot": re.compile(r"bomb ?slot", re.I),
    "breakable": re.compile(r"Breakable Block|bomb_wall", re.I),
    "halfpipe": re.compile(r"halfpipe|need boost", re.I),
    "heat": re.compile(r"varia|heat", re.I),
    "morph_door": re.compile(r"^Door_Area Morphball", re.I),
}


def dock_world(area: dict, coords: list) -> tuple[float, float, float]:
    c = [sum(p[k] for p in coords) / len(coords) for k in range(3)]
    t = area["transform"]
    return tuple(t[4 * r] * c[0] + t[4 * r + 1] * c[1] + t[4 * r + 2] * c[2] + t[4 * r + 3] for r in range(3))


def main(root: str, worlds_json: str, world_name: str, out_path: str) -> None:
    logging.disable(logging.WARNING)
    areas = next(w for w in json.loads(Path(worlds_json).read_text()) if w["name"] == world_name)["areas"]
    manager = AssetManager(PathFileProvider(Path(root)), Game.PRIME)
    out = {}
    for mlvl_id in manager.all_asset_ids_of_type("MLVL"):
        mlvl = manager.get_parsed_asset(mlvl_id)
        try:
            if mlvl.world_name != world_name:
                continue
        except Exception:  # noqa: BLE001 - unnamed world, not the one we want
            continue
        for area in mlvl.areas:
            meta = areas[area.index]
            docks = [(d["dock"], d["to_area"], dock_world(meta, d["coords"])) for d in meta["docks"]]
            at = {d: set() for d, _, _ in docks}
            vuln: dict[int, list[int]] = {}
            vuln_full: dict[int, list[int]] = {}
            pb_only: list[tuple[str, str, int]] = []   # a list: two objects may share a name
            features: dict[str, int] = {}
            area_damage = 0
            env_fx = None
            beam_only: dict[str, int] = {}
            for layer in area.layers:
                for inst in layer.instances:
                    kind = str(inst.type_name)
                    if kind.isdigit() and int(kind) in _FOUR_CC_MAPPING:
                        kind = _FOUR_CC_MAPPING[int(kind)].__name__
                    if kind == "AreaAttributes":   # specs/18c: snow (or rain)
                        env_fx = max(env_fx or 0, int(inst.get_properties().fx_type_))
                    raw = bytes(inst.raw_properties)
                    m = NAME.search(raw)
                    if not m:
                        continue
                    name = m.group(1).decode()
                    for f, pattern in FEATURES.items():
                        if pattern.search(name):
                            features[f] = features.get(f, 0) + 1
                    if kind in ("GrapplePoint", "SpiderBallWaypoint", "Water"):
                        f = {"GrapplePoint": "grapple", "SpiderBallWaypoint": "spider", "Water": "water"}[kind]
                        if kind == "Water" and "lava" in name.lower():
                            f = "lava"
                        features[f] = features.get(f, 0) + 1
                    if kind == "SpecialFunction" and len(raw) >= m.end() + 28 \
                            and struct.unpack(">I", raw[m.end() + 24:m.end() + 28])[0] == AREA_DAMAGE:
                        area_damage += 1
                    if kind == "DamageableTrigger" and not name.startswith("Trigger_DoorKey") and len(raw) >= m.end() + 56:
                        v = struct.unpack(">4I", raw[m.end() + 40:m.end() + 56])
                        if sorted(v) == [1, 2, 2, 2]:   # specs/18c: only one beam hurts it
                            b = BEAMS[v.index(1)]
                            beam_only[b] = beam_only.get(b, 0) + 1
                    if kind in VULN_AT and len(raw) >= m.end() + VULN_AT[kind] + 4 * (VULN_COUNT + 13):   # specs/19c
                        v = vulnerability(raw, m.end() + VULN_AT[kind])
                        if v and v[PB_INDEX] in (0, 1) and all(v[i] not in (0, 1) for i in (0, 1, 2, 3, 4, 6, 7)):
                            pb_only.append((kind, name, layer.index))
                    if len(raw) < m.end() + 12:
                        continue
                    pos = struct.unpack(">3f", raw[m.end():m.end() + 12])
                    if not all(abs(v) < 5000 for v in pos) or not docks:
                        continue
                    dist, dock = min((sum((a - b) ** 2 for a, b in zip(pos, p)) ** 0.5, d) for d, _, p in docks)
                    if dist <= AT_DOCK:
                        at[dock].add((kind, name, layer.index))
                        if kind == "DamageableTrigger" and name.startswith("Trigger_DoorKey") and len(raw) >= m.end() + 56:
                            vuln[dock] = list(struct.unpack(">4I", raw[m.end() + 40:m.end() + 56]))
                            vuln_full[dock] = vulnerability(raw, m.end() + 36)   # specs/19c
            out[str(area.index)] = {
                "name": area.name,
                "docks": [{"dock": d, "to": t, "objects": sorted(map(list, at[d])), "key_vuln": vuln.get(d),
                           "key_vuln_full": vuln_full.get(d)} for d, t, _ in docks],
                "features": dict(sorted(features.items())),
                "area_damage": area_damage,
                "env_fx": env_fx,
                "beam_only": dict(sorted(beam_only.items())),
                "pb_only": sorted(map(list, pb_only)),
            }
    Path(out_path).write_text(json.dumps(dict(sorted(out.items(), key=lambda kv: int(kv[0]))), indent=1,
                                          ensure_ascii=False))
    print(f"{len(out)} salas -> {out_path}")


if __name__ == "__main__":
    main(*sys.argv[1:5])

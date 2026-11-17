"""Dump the script objects (enemies, pickups, triggers...) of one Metroid Prime world.

Usage: venv/bin/python -I dump_prime_area_objects.py <prime_fs dir> "<World name>" <out.json>
Output: per area, object counts by type plus the names of the interesting objects.
"""
import collections
import json
import sys
from pathlib import Path

from retro_data_structures.asset_manager import AssetManager
from retro_data_structures.file_provider import PathFileProvider
from retro_data_structures.game_check import Game
from retro_data_structures.properties.prime.objects import _FOUR_CC_MAPPING

# Object types worth listing by name (everything else is only counted).
INTERESTING = {
    "Pickup", "SpacePirate", "Parasite", "ParasiteQueen" , "NewIntroBoss", "Drone", "Ridley", "MetroidBeta",
    "Metroid", "AtomicAlpha", "AtomicBeta", "Beetle", "Ripper", "PuddleSpore", "Flaahgra", "WarWasp",
    "SpankWeed", "Turret", "AmbientAI", "Puffer", "Babygoth", "Eyeball", "ElitePirate", "Seedling",
    "SpecialFunction", "Timer", "Door", "PointOfInterest", "Dock", "SpawnPoint", "Debris", "Waypoint",
    "CameraHint", "Water", "DamageableTrigger", "Platform", "Effect", "PlayerHint", "HUDMemo",
}


def main(root: str, world_name: str, out_path: str) -> None:
    manager = AssetManager(PathFileProvider(Path(root)), Game.PRIME)
    out = []
    for mlvl_id in manager.all_asset_ids_of_type("MLVL"):
        mlvl = manager.get_parsed_asset(mlvl_id)
        try:
            if mlvl.world_name != world_name:
                continue
        except Exception:  # noqa: BLE001 - unnamed world, not the one we want
            continue
        for area in mlvl.areas:
            counts = collections.Counter()
            named = collections.defaultdict(list)
            for layer in area.layers:
                for inst in layer.instances:
                    t = str(inst.type_name)
                    if t.isdigit() and int(t) in _FOUR_CC_MAPPING:
                        t = _FOUR_CC_MAPPING[int(t)].__name__
                    counts[t] += 1
                    if t in INTERESTING:
                        try:
                            name = inst.name
                        except Exception as exc:  # noqa: BLE001 - some property blobs fail to parse
                            name = f"<nome ilegivel: {type(exc).__name__}>"
                        named[t].append(f"{name} [layer {layer.index}]")
            out.append({"index": area.index, "name": area.name,
                        "counts": dict(counts.most_common()), "named": dict(named)})
    Path(out_path).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    for a in out:
        top = ", ".join(f"{k}x{v}" for k, v in list(a["counts"].items())[:12])
        print(f"{a['index']:2} {a['name'][:32]:32} {top}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

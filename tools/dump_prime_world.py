"""Dump the room list and door graph of every Metroid Prime world to JSON.

Usage: venv/bin/python -I dump_prime_world.py <prime_fs dir> <out.json>
"""
import json
import sys
from pathlib import Path

from retro_data_structures.asset_manager import AssetManager
from retro_data_structures.file_provider import PathFileProvider
from retro_data_structures.game_check import Game


def safe_name(get):
    """Some worlds/areas have no name string (asset id 0xFFFFFFFF)."""
    try:
        return get()
    except Exception as exc:  # noqa: BLE001 - report which name failed
        return f"<sem nome: {type(exc).__name__}>"


def main(files_dir: str, out_path: str) -> None:
    manager = AssetManager(PathFileProvider(Path(files_dir)), Game.PRIME)
    worlds = []
    for mlvl_id in manager.all_asset_ids_of_type("MLVL"):
        mlvl = manager.get_parsed_asset(mlvl_id)
        areas = []
        for area in mlvl.areas:
            raw = area._raw
            docks = []
            for dock_index, dock in enumerate(raw.docks):
                for conn in dock.connecting_dock:
                    docks.append({
                        "dock": dock_index,
                        "to_area": conn.area_index,
                        "to_dock": conn.dock_index,
                        "coords": [[round(c, 2) for c in v] for v in dock.dock_coordinates],
                    })
            areas.append({
                "index": area.index,
                "name": safe_name(lambda: area.name),
                "internal_name": area.internal_name,
                "mrea": hex(area.mrea_asset_id),
                "transform": [round(v, 2) for v in raw.area_transform],
                "aabb": [round(v, 2) for v in raw.area_bounding_box],
                "docks": docks,
            })
        worlds.append({"mlvl": hex(mlvl_id), "name": safe_name(lambda: mlvl.world_name),
                       "paks": sorted(manager.find_paks(mlvl_id)), "areas": areas})
    Path(out_path).write_text(json.dumps(worlds, indent=1, ensure_ascii=False))
    for w in worlds:
        print(f"{w['name']!r:40} {len(w['areas']):3} salas  {w['paks']}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

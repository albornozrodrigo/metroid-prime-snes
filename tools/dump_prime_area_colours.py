"""Measure the colours of the textures each room of one Metroid Prime world draws with, for the look of an area
(specs/20d-estilo-impact.md: the Impact Crater against the Phazon Mines).

Usage: venv/bin/python -I dump_prime_area_colours.py <prime_fs dir> <research/prime_worlds.json> "<World name>" ... <out.json>

A room's textures = the TXTR assets in its MLVL area's non-layer dependencies (the room geometry's materials). Each texture is
reduced to 16x16 RGB and averaged. A texture is "warm" (red/orange: hue < 40 or > 331 degrees), "blue" (hue 162-259) or
"purple" (259-331) when its HLS saturation is at least 0.15 and its lightness at least 0.06; else "grey".
Output: {world: {"textures": n (unique), "mean": "RRGGBB", "hue": degrees, "sat": HLS saturation, "kinds": {kind: n},
"blue_mean"/"warm_mean": "RRGGBB" (mean of the blue / warm ones), "warm_hue"/"warm_sat": that warm mean's hue and
saturation, "rooms": {room: {"textures": n, "mean": "RRGGBB"}}}}.
"""
import colorsys
import json
import sys
from pathlib import Path

from retro_data_structures.asset_manager import AssetManager
from retro_data_structures.file_provider import PathFileProvider
from retro_data_structures.game_check import Game


def kind(rgb) -> str:
    h, light, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    if s < 0.15 or light < 0.06:
        return "grey"
    h *= 360
    if h < 40 or h > 331:
        return "warm"
    if 162 <= h < 259:
        return "blue"
    if 259 <= h <= 331:
        return "purple"
    return "other"


def hexrgb(rgb) -> str:
    return "%02X%02X%02X" % tuple(round(c) for c in rgb)


def mean(cols):
    return tuple(sum(c[i] for c in cols) / len(cols) for i in range(3)) if cols else (0, 0, 0)


def measure(manager: AssetManager, mlvl_id: int) -> dict:
    mlvl = manager.get_parsed_asset(mlvl_id)
    cache: dict[int, tuple] = {}
    rooms = {}
    for area in mlvl.areas:
        cols = []
        for dep in dict.fromkeys(d.id for d in area.dependencies.non_layer if d.type == "TXTR"):
            if dep not in cache:
                img = manager.get_parsed_asset(dep).main_image_data.convert("RGB").resize((16, 16))
                cache[dep] = mean([img.getpixel((x, y)) for x in range(16) for y in range(16)])
            cols.append(cache[dep])
        rooms[area.name] = {"textures": len(cols), "mean": hexrgb(mean(cols))}
    every = list(cache.values())
    avg = mean(every)
    h, _, s = colorsys.rgb_to_hls(*(c / 255 for c in avg))
    kinds: dict[str, int] = {}
    for c in every:
        kinds[kind(c)] = kinds.get(kind(c), 0) + 1
    warm = mean([c for c in every if kind(c) == "warm"])
    wh, _, ws = colorsys.rgb_to_hls(*(c / 255 for c in warm))
    return {"textures": len(every), "mean": hexrgb(avg), "hue": round(h * 360), "sat": round(s, 3), "kinds": kinds,
            "blue_mean": hexrgb(mean([c for c in every if kind(c) == "blue"])), "warm_mean": hexrgb(warm),
            "warm_hue": round(wh * 360), "warm_sat": round(ws, 3), "rooms": rooms}


def main(root: str, worlds_json: str, *rest: str) -> None:
    *names, out = rest
    manager = AssetManager(PathFileProvider(Path(root)), Game.PRIME)
    worlds = {w["name"]: w for w in json.loads(Path(worlds_json).read_text())}
    result = {name: measure(manager, int(worlds[name]["mlvl"], 16)) for name in names}
    Path(out).write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    for name, r in result.items():
        print(name, r["textures"], r["mean"], r["hue"], r["sat"], r["kinds"], r["blue_mean"], r["warm_mean"], r["warm_hue"], r["warm_sat"])


if __name__ == "__main__":
    main(*sys.argv[1:])

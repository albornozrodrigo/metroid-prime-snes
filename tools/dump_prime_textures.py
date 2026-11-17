"""Export the textures of a Metroid Prime model (CMDL) as PNG, for colour reference.

Usage: venv/bin/python -I dump_prime_textures.py <prime_fs dir> <CMDL id hex> <out dir>
Known ids (found by character name in the ANCS sets): Parasite_queen 9A43BD70, Ridley B2B41738.
"""
import sys
from pathlib import Path

from retro_data_structures.asset_manager import AssetManager
from retro_data_structures.file_provider import PathFileProvider
from retro_data_structures.game_check import Game


def main(root: str, cmdl_hex: str, out_dir: str) -> None:
    manager = AssetManager(PathFileProvider(Path(root)), Game.PRIME)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cmdl_id = int(cmdl_hex, 16)
    seen = set()
    for dep in manager.get_dependencies_for_asset(cmdl_id):
        if dep.type != "TXTR" or dep.id in seen:
            continue
        seen.add(dep.id)
        txtr = manager.get_parsed_asset(dep.id)
        image = txtr.main_image_data
        path = out / f"{dep.id:08X}_{txtr.width}x{txtr.height}.png"
        image.save(path)
        print(path.name, txtr.format.name)


if __name__ == "__main__":
    main(*sys.argv[1:4])

"""Render every room of every area (tools/areas.py) to research/render/<area>_<key>.png, with each
area's tileset and palette recolor.

--estilos: also render a synthetic test room per Crateria style (tools/smlib/crateria.py) to
specs/img/07c-<style>.png (with block-type outlines) and 07c-<style>-limpo.png (as in the game),
to check the pieces before any Tallon room exists (specs/07c-estilo-crateria.md).

--mapa-tallon: also draw the whole Tallon map (all 44 rooms of tools/tallon/rooms.py, built or
not) on area 0's 64x32 pause-map grid to specs/img/07d-mapa.png: rooms coloured by region with
their Prime index, a white mark on every door, and a line every 8 columns (one save byte per row
between two lines; specs/07d-grafo-e-mapa-tallon.md).

--mapa-chozo: the same for the whole Chozo Ruins table (tools/chozo/rooms.py, specs/12c) on area 1's grid, to
specs/img/12c-mapa.png.

--mapa-magmoor: the same for the whole Magmoor Caverns table (tools/magmoor/rooms.py, specs/17c) on area 2's grid, to
specs/img/17c-mapa.png.

--mapa-phendrana: the same for the whole Phendrana Drifts table (tools/phendrana/rooms.py, specs/18c) on area 4's grid, to
specs/img/18c-mapa.png.

--mapa-mines: the same for the whole Phazon Mines table (tools/mines/rooms.py, specs/19c) on area 5's grid, to
specs/img/19c-mapa.png.

--mapa-impact: the whole Impact Crater table (tools/impact/rooms.py, specs/20c) on area 0's grid with the Tallon's rooms in grey,
to specs/img/20c-mapa.png.

--rascunhos-tallon: also render the Tallon rooms already drawn (tools/tallon/layouts.py) but not built
yet, each with its region alone (so its doors are there), as in the game, to
specs/img/07j-sala-<name>.png (specs/07j-elevadores-de-enfeite.md).

--salas-07k: also render the built Tallon rooms of regions B and C and the two region A rooms that
specs/07k changed (Landing Site, Tallon Canyon), as in the game, to specs/img/07k-sala-<name>.png.

--salas-07l: also render the rooms of region D (the sunken frigate) and the Frigate Access Tunnel that
specs/07l changed, as in the game (tileset 4 with the frigate's recolor), to specs/img/07l-sala-<name>.png.
The water (an FX layer) is not drawn here: the emulator shots show it.

--salas-07m: also render the rooms of region E (the great tree), Gully and Alcove, and the three rooms
specs/07m changed (Landing Site, Tallon Canyon, Hydro Access), as in the game, to
specs/img/07m-sala-<name>.png.

--estilo-lava: render the synthetic test room with the Magmoor style (tools/smlib/lava.py, specs/17d) on tileset $09 (hot) and
$0A (cool), recoloured, and the vanilla cave room $8F:A923 before and after, to specs/img/17d-lava-(quente|fria)(-limpo).png and
17d-sala-A923-(antes|depois).png.
--estilo-gelo: render the synthetic test room in Phendrana's three looks (tools/smlib/ice.py, specs/18d) with the build's
palettes, to specs/img/18d-(neve|ruinas-de-gelo|laboratorio)(-limpo).png.
--estilo-mina: render the synthetic test room in the Phazon Mines' two looks (tools/smlib/mines.py, specs/19d) with the test
build's palettes, to specs/img/19d-(base-pirata|mina-de-rocha)(-limpo).png.
--estilo-impact: render the synthetic test room in the Impact Crater's look (tools/impact/style.py, specs/20d) next to the Mines'
rock (the look it comes from), with the test build's palettes, to specs/img/20d-estilo.png.
--estilo-ruinas: render the synthetic test room with the Chozo Ruins style (tools/smlib/ruins.py, specs/12d) and the
vanilla brick room $8F:DA2B, with tileset $0C recoloured to sandstone, to specs/img/12d-ruinas(-limpo).png and
12d-sala-DA2B-(antes|depois).png.

The palette recolor is per tileset (it is global in the ROM: tools/build.py), so a Tallon room on the
frigate's tileset 4 is drawn with the frigate's recolor too."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from areas import AREAS, TALLON  # noqa: E402
from smlib import crateria, ruins  # noqa: E402
from smlib.canvas import Canvas  # noqa: E402
from smlib.gfx import load_tileset, render_level, write_png  # noqa: E402
from smlib.level import Door, Level  # noqa: E402
from smlib.palette import bgr555_to_rgb, frigate_color, rgb_to_bgr555  # noqa: E402
from smlib.rom import Rom  # noqa: E402
from tallon import rooms as tallon_rooms  # noqa: E402

TALLON_AREA = 0   # SM area byte of the Tallon (specs/07-tallon-overworld.md, decision 1)


def style_test_level(style) -> Level:
    """3x2 screens with every neighbourhood the styles handle: floors and ceilings, steps up and
    down, overhangs, a pillar, a 1-block ledge, '=' platforms, a pit, inner corners, side and
    floor doors."""
    c = Canvas(3, 2)
    c.carve(1, 2, 46, 26)
    c.fill(0, 27, 47, 31)                    # ground
    c.fill(8, 23, 13, 26)                    # step up...
    c.fill(10, 20, 13, 22)                   # ...and a higher one
    c.carve(16, 27, 20, 29)                  # pit
    c.fill(24, 2, 30, 8)                     # ceiling bump with an overhang
    c.fill(24, 9, 26, 12)
    c.fill(34, 14, 34, 26)                   # 1-block pillar
    c.fill(38, 18, 44, 18)                   # 1-block-thick ledge
    c.platform(20, 26, 21)                   # '=' platform
    c.platform(2, 4, 14)
    c.carve(40, 3, 44, 6)                    # notch into the ceiling (inner corners)
    c.fill(1, 2, 6, 5)                       # corner block in the top left
    for d in (("L", 1), ("R", 0)):
        c.door_gap(*d)
    return Level(3, 2, c.rows(), doors=[Door("L", 1, 0), Door("R", 0, 1)], style=style)


def render_style_tests(rom: Rom, root: Path) -> None:
    for style in crateria.STYLES:
        ts = load_tileset(rom, style.tileset, TALLON_AREA)
        lv = style_test_level(style)
        l1, _ = lv.build_blocks()
        for suffix, types in (("", True), ("-limpo", False)):
            out = root / f"specs/img/07c-{style.name}{suffix}.png"
            render_level(ts, l1, lv.wb, lv.hb, out, overlay_types=types)
            print(out.name, f"tileset {style.tileset}")


def ruins_tileset(rom: Rom, recoloured: bool):
    """Tileset $0C with (or without) the sandstone line (smlib/ruins.py), as the built ROM has it."""
    ts = load_tileset(rom, ruins.RUINS_TILESET, 4)
    if recoloured:
        for i, c in enumerate(ruins.SANDSTONE, start=1):
            ts.palette[ruins.PALETTE_LINE * 16 + i] = tuple(int(c[k:k + 2], 16) for k in (0, 2, 4))
    return ts


def render_ruins(rom: Rom, root: Path) -> None:
    from smlib.room_reader import read_level_data, read_room
    ts = ruins_tileset(rom, True)
    lv = style_test_level(ruins.RUINS)
    l1, _ = lv.build_blocks()
    for suffix, types in (("", True), ("-limpo", False)):
        out = root / f"specs/img/12d-ruinas{suffix}.png"
        render_level(ts, l1, lv.wb, lv.hb, out, overlay_types=types)
        print(out.name)
    r = read_room(rom, 0x8FDA2B)
    st = next(s for s in r.states if s.tileset == ruins.RUINS_TILESET)
    l1, _, _ = read_level_data(rom, st)
    for name, recoloured in (("antes", False), ("depois", True)):
        out = root / f"specs/img/12d-sala-DA2B-{name}.png"
        render_level(ruins_tileset(rom, recoloured), l1, r.width * 16, r.height * 16, out)
        print(out.name)


def lava_tileset(rom: Rom, tileset: int, recoloured: bool):
    """specs/17d: tileset $09/$0A with (or without) the Magmoor colours and the purple door line, as the built ROM has it."""
    from smlib import lava
    from tallon import beamdoors
    ts = load_tileset(rom, tileset, 2)
    if recoloured:
        pal = beamdoors.paint_palette(lava.recolor(lava.vanilla_palette(rom, tileset), tileset), lava.PAINT_LINE)
        for i in range(len(pal) // 2):
            ts.palette[i] = bgr555_to_rgb(pal[2 * i] | pal[2 * i + 1] << 8)
    return ts


def render_lava(rom: Rom, root: Path) -> None:
    from smlib import lava
    from smlib.room_reader import read_level_data, read_room
    for style, name in ((lava.LAVA_HOT, "quente"), (lava.LAVA_COOL, "fria")):
        lv = style_test_level(style)
        l1, _ = lv.build_blocks()
        for suffix, types in (("", True), ("-limpo", False)):
            out = root / f"specs/img/17d-lava-{name}{suffix}.png"
            render_level(lava_tileset(rom, style.tileset, True), l1, lv.wb, lv.hb, out, overlay_types=types)
            print(out.name)
    r = read_room(rom, 0x8FA923)
    l1, _, _ = read_level_data(rom, r.default_state)
    for name, recoloured in (("antes", False), ("depois", True)):
        out = root / f"specs/img/17d-sala-A923-{name}.png"
        render_level(lava_tileset(rom, lava.HOT_TILESET, recoloured), l1, r.width * 16, r.height * 16, out)
        print(out.name)


def render_ice(rom: Rom, root: Path) -> None:
    """specs/18d: the synthetic test room in each of Phendrana's looks (smlib/ice.py), with the palettes the build writes, to
    specs/img/18d-<look>(-limpo).png."""
    import build
    from smlib import ice
    from smlib.style import Style
    from smlib.palette import bgr555_to_rgb as rgb
    for tileset, style, name in ((ice.SNOW_TILESET, ice.SNOW, "neve"), (ice.RUINS_TILESET, ice.ICE_RUINS, "ruinas-de-gelo"),
                                 (ice.LAB_TILESET, Style(), "laboratorio")):
        ts = load_tileset(rom, ice.SOURCE[tileset], 4)
        pal = build.ice_palette(rom, tileset)
        for i in range(len(pal) // 2):
            ts.palette[i] = rgb(pal[2 * i] | pal[2 * i + 1] << 8)
        lv = style_test_level(style)
        l1, _ = lv.build_blocks()
        for suffix, types in (("", True), ("-limpo", False)):
            out = root / f"specs/img/18d-{name}{suffix}.png"
            render_level(ts, l1, lv.wb, lv.hb, out, overlay_types=types)
            print(out.name)


def render_mines(rom: Rom, root: Path) -> None:
    """specs/19d: the synthetic test room in each of the Mines' looks (smlib/mines.py), with the palettes the test build writes,
    to specs/img/19d-<look>(-limpo).png."""
    import build
    from smlib import mines
    from smlib.palette import bgr555_to_rgb as rgb
    for tileset, name in ((mines.BASE_TILESET, "base-pirata"), (mines.ROCK_TILESET, "mina-de-rocha")):
        ts = load_tileset(rom, mines.SOURCE[tileset], 5)
        pal = build.mines_palette(rom, tileset)
        for i in range(len(pal) // 2):
            ts.palette[i] = rgb(pal[2 * i] | pal[2 * i + 1] << 8)
        lv = style_test_level(mines.STYLE_OF[tileset])
        l1, _ = lv.build_blocks()
        for suffix, types in (("", True), ("-limpo", False)):
            out = root / f"specs/img/19d-{name}{suffix}.png"
            render_level(ts, l1, lv.wb, lv.hb, out, overlay_types=types)
            print(out.name)


def render_impact(rom: Rom, root: Path) -> None:
    """specs/20d: the synthetic test room in the Mines' rock look (left) and in the crater's (right; impact/style.py: the same pieces
    and graphics, the rock tinted), side by side with an 8 px gap, to specs/img/20d-estilo.png."""
    import build
    from impact import style as impact_style
    from smlib import mines
    from smlib.gfx import draw_metatile
    lv = style_test_level(mines.MINE_ROCK)
    l1, _ = lv.build_blocks()
    w, h, gap = lv.wb * 16, lv.hb * 16, 8
    cw = 2 * w + gap
    canvas = bytearray(bytes((24, 24, 32)) * (cw * h))
    for i, pal in enumerate((build.mines_palette(rom, mines.ROCK_TILESET), impact_style.palette(rom))):
        ts = load_tileset(rom, impact_style.GRAPHICS_SOURCE, 0)
        for j in range(len(pal) // 2):
            ts.palette[j] = bgr555_to_rgb(pal[2 * j] | pal[2 * j + 1] << 8)
        x0 = i * (w + gap)
        for y in range(h):
            canvas[(y * cw + x0) * 3:(y * cw + x0 + w) * 3] = bytes(ts.palette[0]) * w
        for by in range(lv.hb):
            for bx in range(lv.wb):
                draw_metatile(canvas, cw, x0 + bx * 16, by * 16, ts, l1[by * lv.wb + bx])
    out = root / "specs/img/20d-estilo.png"
    write_png(out, cw, h, bytes(canvas))
    print(out.name)


REGION_RGB = {"A": (90, 170, 90), "B": (200, 170, 70), "C": (80, 150, 200), "D": (160, 110, 190),
              "E": (210, 110, 90), "-": (96, 96, 104)}   # "-": another area's rooms on the same grid (specs/20c)
DIGITS = {"0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111",
          "4": "101101111001001", "5": "111100111001111", "6": "111100111101111", "7": "111001001001001",
          "8": "111101111101111", "9": "111101111001111"}   # 3x5 pixel digits


def render_tallon_map(root: Path, scale: int = 14, rooms=None, region_of=None, name: str = "07d-mapa.png") -> None:
    """Pause-map tile (x, map_y + 1 + screen row) as a scale x scale square, like pausemap.cells."""
    w, h = 64 * scale, 32 * scale
    img = bytearray(bytes((24, 24, 32)) * (w * h))

    def px(x, y, c):
        if 0 <= x < w and 0 <= y < h:
            img[(y * w + x) * 3:(y * w + x) * 3 + 3] = bytes(c)

    for gx in range(0, 64, 8):
        for y in range(h):
            px(gx * scale, y, (54, 54, 70))
    rooms = tallon_rooms.ALL_ROOMS if rooms is None else rooms
    region_of = tallon_rooms.region_of if region_of is None else region_of
    for r in rooms:
        x0, y0, x1, y1 = r.map_x * scale, (r.map_y + 1) * scale, (r.map_x + r.width) * scale - 1, (r.map_y + 1 + r.height) * scale - 1
        colour = REGION_RGB[region_of(r.key)]
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                px(x, y, (16, 16, 16) if x in (x0, x1) or y in (y0, y1) else colour)
        for k, ch in enumerate(str(r.prime)):
            for i, on in enumerate(DIGITS[ch]):
                if on == "1":
                    px(x0 + 3 + 4 * k + i % 3, y0 + 3 + i // 3, (255, 255, 255))
    for r in rooms:
        for d in r.doors:
            sx, sy = {"L": (0, d.screen), "R": (r.width - 1, d.screen),
                      "T": (d.screen, 0), "B": (d.screen, r.height - 1)}[d.side]
            cx, cy = (r.map_x + sx) * scale + scale // 2, (r.map_y + 1 + sy) * scale + scale // 2
            dx, dy = {"L": (-1, 0), "R": (1, 0), "T": (0, -1), "B": (0, 1)}[d.side]
            mx, my = cx + dx * (scale // 2), cy + dy * (scale // 2)
            for i in range(-3, 4):
                for j in (-1, 0):
                    px(mx + j, my + i, (255, 255, 255)) if dx else px(mx + i, my + j, (255, 255, 255))
    out = root / "specs/img" / name
    write_png(out, w, h, bytes(img))
    print(out.name, f"{len(rooms)} salas")


def render_tallon_drafts(rom: Rom, root: Path) -> None:
    built = {r.key for r in tallon_rooms.ROOMS}
    for region in tallon_rooms.REGIONS:
        for room in tallon_rooms.build_rooms({region}):
            if room.key not in tallon_rooms.LAYOUTS or room.key in built:
                continue
            ts = load_tileset(rom, TALLON.tileset_of(room), TALLON.number)
            lv = room.level()
            l1, _ = lv.build_blocks()
            out = root / f"specs/img/07j-sala-{room.key.removeprefix('tallon_').replace('_', '-')}.png"
            render_level(ts, l1, lv.wb, lv.hb, out, overlay_types=False)
            print(out.name, f"{room.width}x{room.height}", f"{len(lv.compressed())} bytes comprimidos")


def recolored_tileset(rom: Rom, index: int, area_number: int):
    """Tileset `index` as the built ROM has it: recoloured by the area that recolours it (global)."""
    ts = load_tileset(rom, index, area_number)
    rows = next((a.palette_rows for a in AREAS if a.tileset == index and a.palette_rows), ())
    for row in rows:
        for i in range(1, 15):
            ts.palette[row * 16 + i] = bgr555_to_rgb(frigate_color(rgb_to_bgr555(*ts.palette[row * 16 + i])))
    return ts


def render_07l(rom: Rom, root: Path) -> None:
    for room in TALLON.rooms:
        if tallon_rooms.region_of(room.key) != "D" and room.key != "tallon_frigate_access":
            continue
        ts = recolored_tileset(rom, TALLON.tileset_of(room), TALLON.number)
        lv = room.level()
        l1, _ = lv.build_blocks()
        out = root / f"specs/img/07l-sala-{room.key.removeprefix('tallon_').replace('_', '-')}.png"
        render_level(ts, l1, lv.wb, lv.hb, out, overlay_types=False)
        print(out.name, f"{room.width}x{room.height}", f"{len(lv.compressed())} bytes comprimidos")


def render_07m(rom: Rom, root: Path) -> None:
    changed = {"tallon_gully", "tallon_alcove", "tallon_landing_site", "tallon_canyon", "tallon_hydro_access"}
    for room in TALLON.rooms:
        if tallon_rooms.region_of(room.key) != "E" and room.key not in changed:
            continue
        ts = recolored_tileset(rom, TALLON.tileset_of(room), TALLON.number)
        lv = room.level()
        l1, _ = lv.build_blocks()
        out = root / f"specs/img/07m-sala-{room.key.removeprefix('tallon_').replace('_', '-')}.png"
        render_level(ts, l1, lv.wb, lv.hb, out, overlay_types=False)
        print(out.name, f"{room.width}x{room.height}", f"{len(lv.compressed())} bytes comprimidos")


def render_07k(rom: Rom, root: Path) -> None:
    changed_a = {"tallon_landing_site", "tallon_canyon"}
    for room in TALLON.rooms:
        if tallon_rooms.region_of(room.key) not in "BC" and room.key not in changed_a:
            continue
        ts = load_tileset(rom, TALLON.tileset_of(room), TALLON.number)
        lv = room.level()
        l1, _ = lv.build_blocks()
        out = root / f"specs/img/07k-sala-{room.key.removeprefix('tallon_').replace('_', '-')}.png"
        render_level(ts, l1, lv.wb, lv.hb, out, overlay_types=False)
        print(out.name, f"{room.width}x{room.height}", f"{len(lv.compressed())} bytes comprimidos")


root = Path(__file__).resolve().parent.parent
rom = Rom.load(root / "base/sm_fix.sfc")
for area in AREAS:
    tilesets = {}
    for room in area.rooms:
        index = area.tileset_of(room)
        if index not in tilesets:
            tilesets[index] = recolored_tileset(rom, index, area.number)
        lv = room.level()
        l1, _ = lv.build_blocks()
        out = root / f"research/render/{area.key}_{room.key}.png"
        render_level(tilesets[index], l1, lv.wb, lv.hb, out, overlay_types=True)
        print(out.name, f"{room.width}x{room.height}", f"{len(lv.compressed())} bytes comprimidos")
if "--estilos" in sys.argv[1:]:
    render_style_tests(rom, root)
if "--estilo-lava" in sys.argv[1:]:   # specs/17d
    render_lava(rom, root)
if "--estilo-ruinas" in sys.argv[1:]:
    render_ruins(rom, root)
if "--estilo-gelo" in sys.argv[1:]:   # specs/18d
    render_ice(rom, root)
if "--estilo-mina" in sys.argv[1:]:   # specs/19d
    render_mines(rom, root)
if "--estilo-impact" in sys.argv[1:]:   # specs/20d
    render_impact(rom, root)
if "--mapa-tallon" in sys.argv[1:]:
    render_tallon_map(root)
if "--mapa-chozo" in sys.argv[1:]:
    from chozo import rooms as chozo_rooms
    render_tallon_map(root, rooms=chozo_rooms.ALL_ROOMS, region_of=chozo_rooms.region_of, name="12c-mapa.png")
if "--mapa-magmoor" in sys.argv[1:]:   # specs/17c
    from magmoor import rooms as magmoor_rooms
    render_tallon_map(root, rooms=magmoor_rooms.ALL_ROOMS, region_of=magmoor_rooms.region_of, name="17c-mapa.png")
if "--mapa-phendrana" in sys.argv[1:]:   # specs/18c
    from phendrana import rooms as phendrana_rooms
    render_tallon_map(root, rooms=phendrana_rooms.ALL_ROOMS, region_of=phendrana_rooms.region_of, name="18c-mapa.png")
if "--mapa-mines" in sys.argv[1:]:   # specs/19c
    from mines import rooms as mines_rooms
    render_tallon_map(root, rooms=mines_rooms.ALL_ROOMS, region_of=mines_rooms.region_of, name="19c-mapa.png")
if "--mapa-impact" in sys.argv[1:]:   # specs/20c: area 0's grid, the Tallon in grey
    from impact import rooms as impact_rooms
    render_tallon_map(root, rooms=[*tallon_rooms.ALL_ROOMS, *impact_rooms.ALL_ROOMS], name="20c-mapa.png",
                      region_of=lambda k: impact_rooms.region_of(k) if k.startswith(impact_rooms.PREFIX) else "-")
if "--rascunhos-tallon" in sys.argv[1:]:
    render_tallon_drafts(rom, root)
if "--salas-07k" in sys.argv[1:]:
    render_07k(rom, root)
if "--salas-07l" in sys.argv[1:]:
    render_07l(rom, root)
if "--salas-07m" in sys.argv[1:]:
    render_07m(rom, root)

"""End-to-end tests: run the built ROM in the headless emulator and check WRAM.

Usage: python3 -I tests/run_tests.py [--grupo A|B|C] [name-substring ...]   (after tools/build.py)
Each test is an input script; `expect` lines fail the test when WRAM differs. specs/17i: the suite outgrew one run of the
tool's time limit, so it is split in two groups (TEST_GROUPS, by the test's name: every test is in exactly one); with no
--grupo every test runs, as before. The verification runs one command per group (README, HANDOFF). specs/18e: a third group, C
(Phendrana's), run after A and B.
"""
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from build import SAVE_PLM, START_ITEMS, START_MISSILES, area_label  # noqa: E402
from areas import CHOZO, FRIGATE, MAGMOOR, MINES, PHENDRANA, TALLON, all_rooms  # noqa: E402
from frigate import areaselect, ending, pausemap, space, title  # noqa: E402
from impact import layouts as impact_layouts  # noqa: E402
from impact import rooms as impact_rooms  # noqa: E402
from frigate.enemies import SPECIES, slots  # noqa: E402
from smlib import crateria, reach, ruins  # noqa: E402
from smlib.compression import decompress  # noqa: E402
from smlib.rom import Rom, snes_to_pc  # noqa: E402
ROOMS = FRIGATE.rooms   # these scripts play the frigate (area 3)
RUNNER = ROOT / "tools/snesrun"
ROM = ROOT / "build/metroid_prime_snes.sfc"
WORK = ROOT / "build/tests"

ROOM_PTR, AREA, GAME_STATE, SAMUS_X, HEALTH = "7E079B", "7E079F", "7E0998", "7E0AF6", "7E09C2"
NEW_GAME = ["wait 600", "hold START 2", "wait 120", "hold A 2", "wait 120", "hold A 2", "wait 120",
            "hold A 2", "wait 240", "wait 400"]


def walk(direction: str, steps: int, jump_every: int = 12) -> list[str]:
    out = []
    for i in range(steps):
        out += [f"hold {direction}+X 2", f"hold {direction} 10"]
        if i % jump_every == 0:
            out.append(f"hold {direction}+A 20")
    return out


BOSS_BITS_AREA3 = f"{0x7ED828 + FRIGATE.number:06X}"   # boss bits of the area: $7ED82B
TIMER_STATUS, TIMER_TIME = "7E0943", "7E0945"   # $0945 centiseconds, $0946 seconds, $0947 minutes (BCD)
TIMER_COUNTING = "8006"                          # slid into place, counting down
# time up: $23 white-out -> $19/$1A game over menu (vanilla would go to $25, Ceres exploding)
GAME_STATE_GAME_OVER = "001A"
ENEMY0_SPECIES = "7E0F78"
PHANTOON = "E4BF"
ESCAPE = ["reactor_core", "monitor_hall", "elevator_gamma", "biotech_1", "subvent_a", "subvent_b",
          "cargo_lift", "vent_a", "vent_b", "vent_c", "vent_d", "vent_e", "vent_f", "biotech_2",
          "elevator_alpha", "mech_shaft", "airlock", "hangar"]


def poke16(addr: int, value: int) -> list[str]:
    return [f"poke {addr:06X} {value & 0xFF:02X}", f"poke {addr + 1:06X} {value >> 8:02X}"]


def go_through(room, door_index: int, side_actions: list[str] | None = None) -> list[str]:
    """Teleport Samus in front of a door and move through it (`side_actions`: other inputs for a
    side door, e.g. missiles for a red one)."""
    d = room.doors[door_index]
    wb, hb = room.width * 16, room.height * 16
    if d.side in "LR":
        x = 4 * 16 + 8 if d.side == "L" else (wb - 5) * 16 + 8
        y = (d.screen * 16 + 10) * 16 - 22
        move = "LEFT" if d.side == "L" else "RIGHT"
        actions = side_actions or ([f"hold {move} 8", "wait 10"] + [f"hold {move}+X 2", "wait 12"] * 4
                                   + ["wait 30", f"hold {move} 90"])
    elif d.side == "T":
        x, y = (d.screen * 16 + 7) * 16 + 8, 6 * 16 - 22   # on the ledge, right under the door
        # shoot the cap (if any), spin jump up-right, keep space jumping to the right on arrival
        actions = (["wait 10"] + ["hold UP+X 2", "wait 12"] * 3 + ["wait 30", "hold LEFT 14", "wait 10", "hold RIGHT 8", "hold RIGHT+A 30"]
                   + ["hold RIGHT 1", "hold RIGHT+A 1"] * 90)   # tap A every other frame: space jump
    else:
        x, y = (d.screen * 16 + 8) * 16, (hb - 5) * 16
        # an unlocked grey floor door turns blue (vanilla): jump and shoot down to open it
        actions = ["wait 10", "hold A 6", "hold A+DOWN 4", "hold A+DOWN+X 2", "hold A+DOWN 6", "hold A+DOWN+X 2",
                   "wait 60"]
    cam_x = max(0, min(x - 128, wb * 16 - 256))
    cam_y = max(0, min(y - 112, hb * 16 - 224))
    out = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y),
                    (0x7E0911, cam_x), (0x7E0915, cam_y)):
        out += poke16(addr, v)
    return out + ["wait 2"] + actions + ["wait 150"]


def kill_parasite_queen() -> list[str]:
    """Fight Phantoon (the Parasite Queen) for real, with a shortcut: its HP starts at 1 instead of
    2500 and Samus' energy/missiles are refilled, so a blind input loop can finish the fight.
    Missiles from the middle of the arena floor, alternating up / right / left."""
    floor_y = 13 * 16 - 21
    out = ["poke 7E0F8C 01", "poke 7E0F8D 00"]
    for addr, v in ((0x7E0AF6, 0x80), (0x7E0B10, 0x80), (0x7E0AFA, floor_y), (0x7E0B14, floor_y)):
        out += poke16(addr, v)
    out += ["wait 30", "hold SELECT 2", "wait 10"]   # select missiles
    for _ in range(200):   # long enough for any fireball pattern to open her mouth near Samus
        out += ["poke 7E09C2 63", "poke 7E09C6 1E", "hold UP+X 2", "wait 10", "hold RIGHT+X 2", "wait 10",
                "hold UP+X 2", "wait 10", "hold LEFT+X 2", "wait 10"]
    return out + ["poke 7E09D2 00", "wait 10"]   # back to the beam (HUD selection), missiles stay for doors


LOAD_STATION, USED_STATIONS_AREA3 = "7E078B", f"{0x7ED8F8 + 2 * FRIGATE.number:06X}"   # $7ED8FE
SAVE = FRIGATE.load_stations[1]                  # Reactor Core Entrance
SAVE_ROOM, SAVE_STATION = SAVE.room, SAVE.index
GAME_OVER_CONTINUE = ["hold A 2", "wait 1200"] + ["hold A 2", "wait 60"] * 25 + ["wait 300"]


OAM_BUFFER = 0x7E0370               # sprites built this frame: x, y, tile, attribute (4 bytes each)
FILE_SELECT_MAP, AREA_SELECT_STEP = "0005", "0006"   # game state 5, menu step $0727 = 6


def area_select_shows_frigate(shot: str) -> list[str]:
    return area_select_shows(FRIGATE.number, SAVE_STATION, shot)


def area_select_shows(area: int, station: int, shot: str) -> list[str]:
    """`expect` lines for the area-select screen: still on it, the save's area / station picked,
    and the 1st sprite (top of the title's first letter) and the 17th (first letter of the save
    area's name: the first name drawn) are the ones tools/frigate/areaselect.py placed."""
    out = [f"expect {GAME_STATE} {FILE_SELECT_MAP}", f"expect 7E0727 {AREA_SELECT_STEP}", f"expect {AREA} {area:04X}",
           f"expect {LOAD_STATION} {station:04X}"]
    entries = areaselect.oam_entries(area)
    for i in (0, len(areaselect.title_pieces(areaselect.TITLE))):
        x, y, tile = entries[i]
        addr = OAM_BUFFER + 4 * i
        out += [f"expect {addr:06X} {y << 8 | x:04X}", f"expect {addr + 2:06X} {areaselect.PRIORITY | tile:04X}"]
    return out + [f"shot {shot}"]


def step_on_save_station() -> list[str]:
    """Drop Samus on the pedestal (where the game puts her when it loads that station), then
    answer YES to "would you like to save?" and close "save completed"."""
    sx, sy = SAVE.x, SAVE.y
    out = []
    for addr, v in ((0x7E0AF6, sx), (0x7E0B10, sx), (0x7E0AFA, sy), (0x7E0B14, sy)):
        out += poke16(addr, v)
    return out + ["wait 180", "hold A 2", "wait 300", "hold A 2", "wait 200"]


MAP_STATION_AREA3 = f"{0x7ED908 + FRIGATE.number:06X}"   # map_station_byte_array[3] = $7ED90B
EXPLORED_TILES = 0x7E07F7          # explored bits of the current area (0x100 bytes; $7ECD52 = saved copies)
GAME_STATE_PAUSED = "000F"
MAP_ROOM = "map_facility"


def use_map_station() -> list[str]:
    """Stand right of the terminal at cannon height and walk into it, then close the message.
    Closing "map data access completed" opens the pause map by itself (vanilla, C $85:0407)."""
    x, floor = {r.key: r for r in ROOMS}[MAP_ROOM].map_station
    sx, sy = (x + 3) * 16 + 8, floor * 16 - 21
    out = []
    for addr, v in ((0x7E0AF6, sx), (0x7E0B10, sx), (0x7E0AFA, sy), (0x7E0B14, sy)):
        out += poke16(addr, v)
    return out + ["wait 30", "hold LEFT 40", "wait 260", "hold A 2", "wait 200"]


def explored_bit(room_key: str, screen_x: int = 0, screen_y: int = 0) -> str:
    """`expect` line for the explored bit of one room screen, at the address the game uses."""
    r = {r.key: r for r in ROOMS}[room_key]
    tx, ty = r.map_x + screen_x, r.map_y + screen_y + 1
    byte, mask = pausemap.bit(tx, ty)
    return f"expectbit {EXPLORED_TILES + byte:06X} {mask:02X}"


def forget_explored(room_key: str) -> str:
    """Clear the explored byte that holds this room's first screen (and its neighbours in it)."""
    r = {r.key: r for r in ROOMS}[room_key]
    byte, _ = pausemap.bit(r.map_x, r.map_y + 1)
    return f"poke {EXPLORED_TILES + byte:06X} 00"


ROOM_STATE = "7E07BB"
TIMER_Y = "7E094A"
TIMER_HIDDEN, TIMER_IN_PLACE = "F000", "3000"   # hidden while Meta Ridley's tiles cover its digits
ENEMY0_PROPS_HI = "7E0F87"      # high byte of enemy 0's properties: $02 = deleted
ENEMY0_AI = "7E0FB2"            # gunship top: its current step (gtp_var_F)
GUNSHIP_WAITING = "A9BD"        # GunshipTop_8: waiting for Samus to board
GAME_STATE_ESCAPE_CUTSCENE = "0022"   # Ceres escape cutscene (station explodes, ship flies to the planet)
LOADING_GAME_STATE = "7ED914"   # $22 until the Landing Site ship has landed, then 5 (normal)
LANDING_SITE = TALLON.load_stations[0].room   # the Tallon's Landing Site (area 0), with the gunship (spec 07g)
USED_STATIONS_AREA0 = "7ED8F8"
EQUIPMENT = "7E09A4"
BOSS_AND_RIDLEY_GONE = "0003"   # area 3 boss bits: Parasite Queen dead (1) + Meta Ridley gone (2)
MINIMAP_OFF = "7E05F7"           # 1 = HUD minimap off (SM boss rooms; Ceres Ridley's init sets it)


# spec 07e: what Samus has when she reaches Tallon IV (she loses the rest in the frigate's
# explosion): Power Beam only, no missiles/supers/power bombs/reserve, 99 energy, HUD on the beam.
# Written out here (not imported from ending.py) so the test checks the spec, not the code.
ARRIVAL_LOADOUT = {"7E09A2": "0000", "7E09A4": "0000", "7E09A6": "0000", "7E09A8": "0000",   # items, beams
                   "7E09C0": "0000", "7E09C2": "0063", "7E09C4": "0063",                       # reserve mode, energy
                   "7E09C6": "0000", "7E09C8": "0000", "7E09CA": "0000", "7E09CC": "0000",     # missiles, supers
                   "7E09CE": "0000", "7E09D0": "0000", "7E09D2": "0000",                       # power bombs, HUD item
                   "7E09D4": "0000", "7E09D6": "0000"}                                          # reserve tanks


def has_arrival_loadout() -> list[str]:
    return [f"expect {a} {v}" for a, v in ARRIVAL_LOADOUT.items()]


def lands_on_landing_site(landing_ptr: str) -> list[str]:
    """`expect` lines once the ship has landed at the Tallon's Landing Site (room header
    `landing_ptr`) and saved there (GunshipTop_7: load station 0 of area 0), with the arrival
    equipment (spec 07e)."""
    return [f"expect {GAME_STATE} 0008", f"expect {AREA} 0000", f"expect {ROOM_PTR} {landing_ptr}",
            f"expect {LOADING_GAME_STATE} 0005", f"expect {LOAD_STATION} 0000", f"expectbit {USED_STATIONS_AREA0} 01",
            ] + has_arrival_loadout()


GAME_HOURS = "7E09E0"   # in the saved player data: a marker that tells which save a continue loaded


def save_on_tallon_ship(shot: str = "build/tests/tallon_nave_save.png", energy: int = 99) -> list[str]:
    """Samus stands on the landed ship: low energy, a marker in the saved data and another load
    station in RAM, then crouch (DOWN), the ship refills her (to `energy`, her maximum), A answers YES to
    "save?" and A closes "save completed"."""
    return (poke16(0x7E09C2, 16) + poke16(0x7E09E0, 5) + poke16(0x7E078B, 1)
            + ["wait 30", "hold DOWN 2", "wait 600", f"expect {HEALTH} {energy:04X}", f"shot {shot}",
               # YES, then close "save completed" (box $18): the ship saves only after it ($85:80BF)
               "hold A 2", "wait 300", "hold A 2", "wait 500", f"expect {LOAD_STATION} 0000", f"expectbit {USED_STATIONS_AREA0} 01",
               f"expect {GAME_STATE} 0008"])


def load_slot_a_after_reset() -> list[str]:
    """Power off and on, then START on the title and A on slot A (as `carregar_save_mostra_a_fragata`)."""
    return ["reset", "wait 600", "hold START 2", "wait 200"] + ["hold A 2", "wait 120"] * 3 + ["wait 200"]


def board_ship() -> list[str]:
    """Put Samus on top of the gunship's centre (where she stands on the Landing Site ship) and
    press down, like a player boarding it."""
    cx, ground = {r.key: r for r in ROOMS}["hangar"].ship
    x, y = cx * 16, (ground + ending.SHIP_TOP_ROW) * 16 - 20
    out = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y), (0x7E0911, x - 128), (0x7E0915, 160)):
        out += poke16(addr, v)
    return out + ["wait 60", "hold DOWN 2"]


WS_LIBRARY_BG = 0x8FE117          # vanilla WS background: decompress $BA:8DE7, BG2 map to VRAM $4800 and $4C00
WS_LIBRARY_BG_BYTES = bytes.fromhex("0400e78dba0040" "020000407e00480008" "020000407e004c0008" "0000")
XRAY_SELECTED, TIME_FROZEN = "7E09D2", "7E0A78"   # HUD item 5 = X-ray; $0A78 = 1 while the beam is out


def vram_refs() -> dict[str, str]:
    """Write what VRAM must hold (for `expectvram`) and return the file paths, relative to ROOT:
    the hangar's star tiles and BG2 map (tools/frigate/space.py) and the WS background map."""
    rom = Rom.load(ROM)
    assert rom.read(WS_LIBRARY_BG, len(WS_LIBRARY_BG_BYTES)) == WS_LIBRARY_BG_BYTES, "fundo do WS mudou"
    ws_map, _ = decompress(rom.data, snes_to_pc(0xBA8DE7))
    refs = {"stars": space.star_tiles(), "star_map": space.star_tilemap(), "ws_map": ws_map[:0x800] * 2}
    out = {}
    for name, data in refs.items():
        path = WORK / f"vram_{name}.bin"
        path.write_bytes(data)
        out[name] = str(path.relative_to(ROOT))
    return out


TITLE_FUNCTION = "7E1F51"   # the title's cinematic function: $9F29 = logo up, waiting for a button (specs/16)
FRAME_COUNTER, RANDOM = "7E05B6", "7E05E5"   # NMI frame counter (lag frames not counted), random number


def title_logo_in_vram() -> str:
    """specs/16: the title's sprite tiles of the logo (rows $00-$9F of its graphic, VRAM $6000) are the built ROM's,
    METROID PRIME (tools/frigate/title.py)."""
    rom = Rom.load(ROM)
    gfx, _ = decompress(rom.data, snes_to_pc(title.gfx_pointer(rom)))
    path = WORK / "vram_title_logo.bin"
    path.write_bytes(gfx[32 * title.LOGO_TILES.start:32 * title.LOGO_TILES.stop])
    return f"expectvram {0x6000 + 16 * title.LOGO_TILES.start:04X} {path.relative_to(ROOT)}"


OAM_BUFFER = 0x7E0370          # the game's OAM copy: 4 bytes per sprite (x, y, tile, attribute)
TITLE_LOGO_SCREEN = (128, 48)  # where the title's logo object draws its spritemap (vanilla's OAM at frame 2000: +128, +48)


def title_logo_in_oam() -> list[str]:
    """specs/16: the logo's sprites, in the spritemap's order (the first ones in the OAM buffer), are the built ROM's
    pieces at the logo's place on screen."""
    out = []
    for k, (x, y, attr, _) in enumerate(title.spritemap(Rom.load(ROM))):
        sx, sy = (TITLE_LOGO_SCREEN[0] + x) & 0xFF, TITLE_LOGO_SCREEN[1] + y
        out += [f"expect {OAM_BUFFER + 4 * k:06X} {sy:02X}{sx:02X}", f"expect {OAM_BUFFER + 4 * k + 2:06X} {attr:04X}"]
    return out


def hangar_has_stars(vram: dict[str, str]) -> list[str]:
    return [f"expectvram {space.STAR_VRAM:04X} {vram['stars']}",
            f"expectvram {space.BG2_TILEMAP_VRAM:04X} {vram['star_map']}"]


def walk_under_ship() -> list[str]:
    """Put Samus on the hangar floor right of the gunship and walk left under its belly."""
    cx, ground = {r.key: r for r in ROOMS}["hangar"].ship
    x, y = (cx + 5) * 16, ground * 16 - 21
    out = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y), (0x7E0911, x - 192), (0x7E0915, 288)):
        out += poke16(addr, v)
    return out + ["wait 10", "hold LEFT 45"]


# spec 07b: the jump the validator assumes without Space Jump (tools/smlib/reach.py), measured on
# the evac_area floor (row 27, feet at y 432) at column 14, open up to row 2; its enemies are
# deleted first (a hit's knock-back would spoil the numbers)
JUMP_ROOM, JUMP_X, JUMP_Y = "evac_area", 14 * 16 + 8, 27 * 16 - 21
HI_JUMP = 0x0100
SAMUS_X_Y_RADIUS = ("7E0AF6", "7E0AFA", "7E0B00")   # feet = y + vertical radius (smaller when spinning)
JUMPS = [("parado", 0, "A", 100), ("hi_jump", HI_JUMP, "A", 120), ("com_direcao", 0, "RIGHT+A", 110)]
LEDGE_X, LEDGE_FEET = 16 * 16 + 7, 20 * 16   # 3 blocks right of the 7-block platform (row 20, columns 6-12)


def stand_still(items: int, x: int) -> list[str]:
    """Only `items` equipped, Samus on the floor at x (placed twice: the first stops her slide)."""
    place = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, JUMP_Y), (0x7E0B14, JUMP_Y)):
        place += poke16(addr, v)
    return poke16(0x7E09A2, items) + place + ["wait 30"] + place + ["wait 60"]


def measure_jumps() -> list[str]:
    out = [f"poke {0x7E0F87 + 0x40 * i:06X} 02" for i in range(len(FRIGATE.enemies[JUMP_ROOM]))] + ["wait 10"]
    for _, items, buttons, frames in JUMPS:
        out += stand_still(items, JUMP_X)
        out += ([f"hold {buttons} 1"] + [f"peekw {a}" for a in SAMUS_X_Y_RADIUS]) * frames
    # the highest ledge the model allows (7 blocks) is really climbable: she ends up on top
    return out + stand_still(0, LEDGE_X) + ["hold LEFT+A 60", "wait 30", f"expect 7E0AFA {LEDGE_FEET - 21:04X}"]


def check_jumps(stdout: str) -> list[str]:
    """The trajectories printed by measure_jumps() must give reach.py's constants exactly."""
    vals = [int(v, 16) for v in re.findall(r"7E0(?:AF6|AFA|B00) = ([0-9A-F]{4})", stdout)]
    frames = [(x, y + r) for x, y, r in zip(vals[0::3], vals[1::3], vals[2::3])]
    if len(frames) != sum(j[3] for j in JUMPS):
        return [f"FAIL pulo: {len(frames)} quadros lidos"]
    got, at = {}, 0
    for name, _, _, n in JUMPS:
        try:
            got[name] = reach.arc_from_samples(frames[at:at + n])
        except ValueError as e:
            return [f"FAIL pulo {name}: {e}"]
        at += n
    want = {"parado": reach.JUMP_RISE_PX, "hi_jump": reach.HIJUMP_RISE_PX, "com_direcao": reach.JUMP_RISE_PX}
    fails = [f"FAIL pulo {k}: subiu {got[k][0]} px, reach.py diz {v}" for k, v in want.items() if got[k][0] != v]
    if got["com_direcao"][1] != reach.JUMP_ARC_PX:
        fails.append(f"FAIL pulo com_direcao: alcance {got['com_direcao'][1]}, reach.py diz {reach.JUMP_ARC_PX}")
    return fails


# spec 07g: Prime's item-free path in the Tallon (tools/tallon/rooms.py ACTIVE_ROOMS), from the
# Landing Site to the dead-end elevator room and back. Samus arrives with the Power Beam only (the
# lift-off takes the rest, spec 07e; no RAM poke any more) and walks
# like a player would, no teleport: hold the direction, shoot (blue caps), and jump every cycle
# (a jump against a ledge climbs it). The room pointer is read every cycle; check_tallon_route
# wants exactly the rooms of the path, in order, and keeps one screenshot per room.
TALLON_PATH = ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a",
               "tallon_transport_chozo_west"]
TALLON_CYCLES = 70        # going (left): the walk needs 43, then the elevator room's wall stops her
# coming back (right): the Landing Site is reached at cycle 50; since 07k its east side leads on to
# Waterfall Cavern (cycle 68) and Temple Hall, so the walk stops a few cycles after entering it.
# specs/09d: the Morph Ball lies on the Chozo West elevator pad; going west the walker jumps over it,
# coming back it walks into it and its message box (closed by the next jump's A) takes a few cycles:
# the Landing Site is reached at cycle 59 and the Waterfall Cavern at 78. specs/12e: the ball lies at the foot of the
# steps, east of the platform (which rides now); tallon_rota_mvp still picks it up with these counts (measured);
# tallon_mapa_salvo, without the pause at the wall, needs an odd number of cycles going west (MAP_WALK_WEST)
TALLON_CYCLES_BACK = 65
# specs/12e: the west walk of tallon_mapa_salvo: one more cycle against the Chozo West's west wall than TALLON_CYCLES, so
# the walk back starts on the other beat of the walker's jump and walks into the Morph Ball (with 70 it jumps over it;
# measured: 67, 69, 71, 73 pick it up, 66, 68, 70, 72, 74 don't)
MAP_WALK_WEST = TALLON_CYCLES + 1
# specs/09d: what Samus has at the end of the walks through the Chozo West: the Morph Ball only
# (equipped and collected $0004, no beam)
MORPH_BALL_EQUIPMENT = 0x0004
MORPH_ONLY_RAM = {0x7E09A2: MORPH_BALL_EQUIPMENT, 0x7E09A4: MORPH_BALL_EQUIPMENT, 0x7E09A6: 0, 0x7E09A8: 0}
TALLON_SHOTS = WORK / "tallon_rota"
TALLON_SHOT_EVERY = 5
POWER_BEAM_ONLY_RAM = (0x7E09A2, 0x7E09A4, 0x7E09A6, 0x7E09A8)   # equipment and beams: nothing


def tallon_walk(direction: str, tag: str, cycles: int | None = None, jump: bool = True) -> list[str]:
    """One cycle = shoot, walk, (jump), walk, read the room. Default length: TALLON_CYCLES going
    left, TALLON_CYCLES_BACK coming back right. Since spec 07i the energy is refilled at the start
    of each cycle: these walks test the way through the rooms, not the fights (a blind walker
    shooting once a cycle loses its 99 to the Beetles' leaps); the enemies stay, knock-back and all."""
    if cycles is None:
        cycles = TALLON_CYCLES if direction == "LEFT" else TALLON_CYCLES_BACK
    out = []
    for i in range(cycles):
        out += [f"poke {HEALTH} 63", f"hold {direction}+X 2", f"hold {direction} 8",
                f"hold {direction}+A 40" if jump else f"hold {direction} 40", f"hold {direction} 10",
                f"peekw {ROOM_PTR}"]
        if i % TALLON_SHOT_EVERY == 0:
            out.append(f"shot {(TALLON_SHOTS / f'{tag}{i:03d}.png').relative_to(ROOT)}")
    return out


# the pause map as shown (LoadPauseMenuMapTilemapAndAreaLabel $82:93C3): VRAM word $3000 = the 64x32
# map (explored tiles = tilemap word without $400, others $001F), $38AA = the area name (12 words)
PAUSE_MAP_VRAM, PAUSE_NAME_VRAM = 0x3000, 0x38AA


def tallon_door_screens() -> list[tuple[str, int, int]]:
    """(room, screen x, screen y) of every door between two MVP rooms (Samus crosses each one on
    the walk there and back; since 07k the MVP rooms also have doors to B/C, not crossed here) and
    of the Landing Site ship (where she lands and saves)."""
    by = TALLON.by_key()
    out = [(k, 0 if d.side == "L" else by[k].width - 1, d.screen) for k in TALLON_PATH for d in by[k].doors
           if d.to_room in TALLON_PATH]
    st = TALLON.load_stations[0]
    return out + [(st.room, st.x // 256, st.y // 256)]


def tallon_tile(room_key: str, sx: int, sy: int) -> tuple[int, int]:
    r = TALLON.by_key()[room_key]
    return r.map_x + sx, r.map_y + sy + 1


def tallon_explored(screens) -> list[str]:
    out = []
    for k, sx, sy in screens:
        byte, mask = pausemap.bit(*tallon_tile(k, sx, sy))
        out.append(f"expectbit {EXPLORED_TILES + byte:06X} {mask:02X}")
    return out


TALLON_BLANK = (30, 30)   # specs/20g: a blank tile of area 0's pause map (no Tallon nor crater room, built or not)


def tallon_pause_shows(screens) -> list[str]:
    """While paused (VRAM): those screens show the Tallon tilemap's tile (explored), a tile outside
    every built room is blank, and the name is "TALLON". Writes the reference files to WORK."""
    def vram_line(addr: int, data: bytes, name: str) -> str:
        path = WORK / f"vram_tallon_{name}.bin"
        path.write_bytes(data)
        return f"expectvram {addr:04X} {path.relative_to(ROOT)}"

    # no Tallon room there, built or not ((30, 8) became the Temple Hall in 07k); specs/20g: (30, 20) is the Subchamber Three's
    # (the crater shares area 0's map): (30, 30), under every crater room, built or not (impact_rooms.ALL_ROOMS)
    blank = TALLON_BLANK
    assert all(blank not in {(tx, ty) for *_, tx, ty in pausemap.cells(r)} for r in [*TALLON.rooms, *impact_rooms.ALL_ROOMS])
    tiles = [(tallon_tile(k, sx, sy), pausemap.room_tile(TALLON.by_key()[k], sx, sy) & 0xFBFF) for k, sx, sy in screens]
    out = [vram_line(PAUSE_MAP_VRAM + pausemap.tile_index(tx, ty), struct.pack("<H", w), f"{tx}_{ty}")
           for (tx, ty), w in tiles + [(blank, pausemap.BLANK)]]
    return out + [vram_line(PAUSE_NAME_VRAM, area_label(TALLON.name), "nome")]


# specs/10c: the pause map shows each room's shape. Every screen of the Tallon Canyon and the Artifact Temple that is not
# solid rock is marked explored by RAM (as if Samus had been there: she can't stand in rock, so the solid ones never
# are); paused, each of those screens shows its tile with walls toward the rock (VRAM), as pausemap.room_tile draws it.
MAP_SHAPE_ROOMS = ("tallon_canyon", "tallon_artifact_temple")


def map_shape_screens() -> list[tuple[str, int, int]]:
    by = TALLON.by_key()
    return [(k, sx, sy) for k in MAP_SHAPE_ROOMS for sx, sy, _, _ in pausemap.cells(by[k])
            if (sx, sy) not in pausemap.solid_screens(by[k])]


def explore(screens) -> list[str]:
    masks: dict[int, int] = {}
    for k, sx, sy in screens:
        byte, mask = pausemap.bit(*tallon_tile(k, sx, sy))
        masks[byte] = masks.get(byte, 0) | mask
    return [f"poke {EXPLORED_TILES + b:06X} {m:02X}" for b, m in sorted(masks.items())]


def map_shows_shapes() -> list[str]:
    out = []
    for k, sx, sy in map_shape_screens():
        tx, ty = tallon_tile(k, sx, sy)
        path = WORK / f"vram_forma_{tx}_{ty}.bin"
        path.write_bytes(struct.pack("<H", pausemap.room_tile(TALLON.by_key()[k], sx, sy) & 0xFBFF))
        out.append(f"expectvram {PAUSE_MAP_VRAM + pausemap.tile_index(tx, ty):04X} {path.relative_to(ROOT)}")
    return out


def stand_on_tallon_ship() -> list[str]:
    """Put Samus where load station 0 of area 0 has her: on top of the Landing Site ship."""
    st = TALLON.load_stations[0]
    r = TALLON.by_key()[st.room]
    cam_x = max(0, min(st.x - 128, r.width * 256 - 256))
    cam_y = max(0, min(st.y - 112, r.height * 256 - 224))
    out = []
    for addr, v in ((0x7E0AF6, st.x), (0x7E0B10, st.x), (0x7E0AFA, st.y), (0x7E0B14, st.y),
                    (0x7E0911, cam_x), (0x7E0915, cam_y)):
        out += poke16(addr, v)
    return out + ["wait 60"]


def check_tallon_route(stdout: str) -> list[str]:
    """Rooms visited (room pointer per cycle, repeats merged) = the path there and back; the
    middle screenshot of each room's first visit is copied to build/tests/tallon_<room>.png."""
    return check_walk(stdout, TALLON_PATH + TALLON_PATH[-2::-1], "rota do Tallon")


def check_walk(stdout: str, want: list[str], what: str) -> list[str]:
    manifest = json.loads((ROOT / "build/manifest.json").read_text())
    key_of = {f"{manifest[k]['header'] & 0xFFFF:04X}": k for k in want}
    visits: list[list] = []   # [room, [shots]]
    for line in stdout.splitlines():
        m = re.search(rf"{ROOM_PTR} = ([0-9A-F]{{4}})", line)
        if m:
            k = key_of.get(m.group(1), m.group(1))
            if not visits or visits[-1][0] != k:
                visits.append([k, []])
        m = re.search(r"shot (\S+)", line)
        if m and visits:
            visits[-1][1].append(m.group(1))
    got = [k for k, _ in visits]
    if got != want:
        return [f"FAIL {what}: salas {got}, esperado {want}"]
    done = set()
    for k, shots in visits:
        if shots and k not in done:
            done.add(k)
            (WORK / f"{k}.png").write_bytes((ROOT / shots[len(shots) // 2]).read_bytes())
    return []


# spec 07k: from the landing, with the Power Beam only, through the 4 rooms of regions B and C that
# are reachable now (Temple Hall, Temple Security Station, Waterfall Cavern, Root Tunnel), each up
# to its red (missile) door, which the beam doesn't open, and back. Walking, no teleport: legs of
# tallon_walk cycles (with or without the jump) and, for the climb to the Root Tunnel door, plain
# inputs. The emulator is deterministic; the leg lengths were measured (spec 07k, Desvios).
TALLON_BC_PATH = ["tallon_landing_site", "tallon_temple_hall", "tallon_temple_security", "tallon_temple_hall",
                  "tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a",
                  "tallon_transport_chozo_west", "tallon_tunnel_a", "tallon_canyon", "tallon_root_tunnel",
                  "tallon_canyon", "tallon_canyon_cavern", "tallon_landing_site", "tallon_waterfall_cavern",
                  "tallon_landing_site"]
# from the Chozo West wall: back to the Tallon Canyon's L1 ledge, the three platforms up to the right,
# turn round and jump up to the left onto the Root Tunnel door's bridge. specs/09d: 21 -> 28 cycles (on the
# way back from the wall the walker picks up the Morph Ball: its message box; the Canyon is entered at 27).
# specs/12e: 28 -> 25 (the ball lies at the foot of the steps now, picked up on the way west; measured: 24-26 end in
# the Canyon for the climb, 20-23 and 27-30 don't)
TALLON_CLIMB = (["wait 60"] + tallon_walk("RIGHT", "bc_sobe", 25)
                # spec 07i: the walk ends wherever the enemies' knock-back left her, so the climb
                # starts from a fixed spot: back against the closed cap of the L1 door, then turned
                # right without moving (x $27, standing: where the walk used to end)
                + ["wait 30", "hold LEFT 40", "wait 30", "hold RIGHT 2", "wait 40",
                   "hold RIGHT 30", "hold RIGHT+A 30", "hold A 10", "wait 30",       # onto P1
                   "hold A 14", "hold RIGHT+A 22", "hold A 10", "wait 40",                      # P2
                   "hold RIGHT 10", "hold A 14", "hold RIGHT+A 26", "hold A 10", "wait 40",     # P3
                   "hold LEFT 2", "wait 10", "hold A 20", "hold LEFT+A 24", "hold LEFT 10", "wait 40"])  # bridge


def red_door_shut(a: str, b: str) -> list[str]:
    """The red door's bit ($7ED8B0) is still off: the Power Beam didn't open it. The Tallon's red
    door bits ($B0-$B2) share their 16-bit word only with unused bits (vanilla stops at 172), so
    the whole word must be 0."""
    from tallon import rooms as tallon_rooms
    bit = tallon_rooms.MISSILE_BITS[frozenset({a, b})]
    assert 176 <= bit < 192
    return [f"expect {0x7ED8B0 + 22:06X} 0000"]


def tallon_route_bc() -> list[str]:
    return (["hold LEFT 70", "wait 60"]                          # off the ship's west side, onto the ground
            + tallon_walk("RIGHT", "bc_templo", 9, jump=False)   # under the ship, the corridor, Temple Hall
            + tallon_walk("RIGHT", "bc_seguranca", 20)           # Temple Security, up to the red door
            + ["shot build/tests/tallon_porta_vermelha_templo.png"]
            + red_door_shut("tallon_temple_security", "tallon_temple_lobby")
            + tallon_walk("LEFT", "bc_oeste", 100)               # all the way to the Chozo West elevator
            + TALLON_CLIMB
            + tallon_walk("LEFT", "bc_raiz", 20)                 # Root Tunnel, up to the red door
            + ["shot build/tests/tallon_porta_vermelha_raiz.png"]
            + red_door_shut("tallon_root_tunnel", "tallon_root_cave")
            + tallon_walk("RIGHT", "bc_leste", 75)               # back, over the ship, Waterfall Cavern
            + ["shot build/tests/tallon_porta_vermelha_cachoeira.png"]
            + red_door_shut("tallon_waterfall_cavern", "tallon_crash_site")
            + tallon_walk("LEFT", "bc_volta", 16))               # back into the Landing Site


# spec 07h: the Tallon's items (tools/tallon/items.py). The first Missile Expansion lies in the
# Landing Site pond, on the way from the ship to the Canyon Cavern door.
MISSILES, MAX_MISSILES, HUD_ITEM = "7E09C6", "7E09C8", "7E09D2"


def item_taken(n: int) -> str:
    """`expectbit` line for the item bit ($7ED870) of tallon/items.py ITEMS[n]."""
    from tallon import items as tallon_items
    bit = tallon_items.BITS[n]
    return f"expectbit {0x7ED870 + bit // 8:06X} {1 << (bit % 8):02X}"


def item_not_taken(n: int) -> str:
    """The item bit's byte is still 0 (the Tallon's bits $A0-$AC share bytes only among themselves)."""
    from tallon import items as tallon_items
    bit = tallon_items.BITS[n]
    return f"expect {0x7ED870 + bit // 8:06X} 0000"


def item_not_taken_with(n: int, taken: tuple[int, ...]) -> str:
    """specs/09e: item n's bit is not set, the 16 bits read there (its byte and the next) holding exactly the bits of
    the items `taken` in this run (the Tallon's bits share bytes)."""
    from tallon import items as tallon_items
    byte = tallon_items.BITS[n] // 8
    word = sum(1 << (tallon_items.BITS[k] - 8 * byte) for k in taken if 0 <= tallon_items.BITS[k] - 8 * byte < 16)
    return f"expect {0x7ED870 + byte:06X} {word:04X}"


def red_door_open(a: str, b: str) -> str:
    from tallon import rooms as tallon_rooms
    bit = tallon_rooms.MISSILE_BITS[frozenset({a, b})]
    return f"expectbit {0x7ED8B0 + bit // 8:06X} {1 << (bit % 8):02X}"


def tallon_first_missile(name: str = "tallon_missil") -> list[str]:
    """From the landing: off the ship's west side and left along the ground into the pond, where
    the Missile Expansion is; A closes its message box. `name`: of the screenshots (specs/09f: tallon_cadeia_completa
    has its own, the tests run in parallel). specs/10a: the A comes 300 frames after the walk (it was 240, before the
    box takes it: the box stayed until the walker's next button)."""
    tag = name.removeprefix("tallon_")
    return (["hold LEFT 70", "wait 60", item_not_taken(0), f"expect {MAX_MISSILES} 0000",
             f"shot build/tests/{name}_no_lago.png"]
            + tallon_walk("LEFT", tag, 1)                  # off the mossy rock
            + tallon_walk("LEFT", f"{tag}_lago", MISSILE_WALK, jump=False)   # into the pond, to its west bank
            + ["wait 120", f"shot build/tests/{name}_mensagem.png", "wait 180", "hold A 2", "wait 120",
               f"expect {MISSILES} 0005", f"expect {MAX_MISSILES} 0005", item_taken(0)])


MISSILE_WALK = 4   # cycles without jumping from the foot of the mossy rock to the pond's west bank (spec 07h)


def tallon_missile_red_door() -> list[str]:
    """Spec 07h: pick up the first missile, walk right over the ship and the terraces into the
    Waterfall Cavern up to its red door, select missiles (SELECT), fire them at the door until it
    opens (5 hits), and go through to the Frigate Crash Site."""
    shots = ["hold RIGHT+X 2", "wait 30"] * 6
    return (tallon_first_missile()
            + tallon_walk("RIGHT", "missil_leste", 40)          # up to the Waterfall red door
            + [f"expect {ROOM_PTR} WATERFALL", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001"]
            + shots + ["wait 60", "shot build/tests/tallon_porta_vermelha_aberta.png",
                       red_door_open("tallon_waterfall_cavern", "tallon_crash_site"), f"expect {MISSILES} 0000"]
            + tallon_walk("RIGHT", "missil_crash", 4)
            + [f"expect {ROOM_PTR} CRASH", "shot build/tests/tallon_crash_site.png",
               "hold RIGHT 100", "shot build/tests/tallon_crash_site_item.png"])   # its missile, in the pond


# spec 07i: the Tallon's enemies (tools/tallon/enemies.py). WRAM enemy table: slot n at $7E0F78 +
# $40·n, species word first, health at +$14; a dead enemy's species word is cleared ($A0:8EB6,
# research/sm_room_format.md §11). These tests teleport in front of each door (go_through), like
# the frigate's inimigos_nascem_nas_salas, so the enemies are met as the room spawns them.
ENEMY_TABLE, ENEMY_SLOT, ENEMY_HEALTH = 0x7E0F78, 0x40, 0x14


def tallon_traverse(keys: list[str], room: dict) -> list[str]:
    """Through the doors between consecutive Tallon rooms (go_through: teleport in front of the door)."""
    by = TALLON.by_key()
    out = []
    for a, b in zip(keys, keys[1:]):
        i = next(i for i, d in enumerate(by[a].doors) if d.to_room == b)
        out += go_through(by[a], i) + [f"expect {ROOM_PTR} {room[b]}"]
    return out


def tallon_enemies_alive(key: str) -> list[str]:
    """Every enemy of the room is in its slot with the species' full health (alive, unhurt)."""
    rom = Rom.load(ROM)
    out = []
    for n, e in enumerate(TALLON.enemies[key]):
        at = ENEMY_TABLE + ENEMY_SLOT * n
        out += [f"expect {at:06X} {e.species.ptr:04X}",
                f"expect {at + ENEMY_HEALTH:06X} {rom.u16(0xA00000 | e.species.ptr + 4):04X}"]
    return out + [f"expect {ENEMY_TABLE + ENEMY_SLOT * len(TALLON.enemies[key]):06X} 0000"]   # and no more


def tallon_look(x: int, floor: int, cam_x: int, cam_y: int, shot: str, settle: int = 200) -> list[str]:
    """Samus standing on block (x, floor), the camera at (cam_x, cam_y) px; pausing and unpausing
    redraws the screen after the camera jump (as in hangar_ceu_estrelado); then a screenshot `settle` frames after the unpause
    (specs/19g: sooner where a pirate fires at her)."""
    sx, sy = x * 16 + 8, floor * 16 - 21
    out = []
    for addr, v in ((0x7E0AF6, sx), (0x7E0B10, sx), (0x7E0AFA, sy), (0x7E0B14, sy), (0x7E0911, cam_x), (0x7E0915, cam_y)):
        out += poke16(addr, v)
    return out + ["wait 4", "hold START 10", "wait 200", "hold START 10", f"wait {settle}", f"poke {HEALTH} 63", f"shot {shot}"]


# spec 07l: region D, the sunken frigate. It is behind the ice door (a beam door since 09a) and Prime's
# Gravity Suit, so no walk from the landing gets there: the tests start at its save station, load
# station 1 of area 0, the way the new-game routine starts the frigate (game state 6 = load the game
# at area/station, tools/build.py), with the Gravity Suit equipped as the region assumes (Prime).
GRAVITY_SUIT = 0x0020
DOOR_HIT_TRANSITION = 0xE17D   # DoorTransitionFunction_HandleElevator ($82:E17D)
SAVESTATION = TALLON.load_stations[1]            # Savestation (P28)
WATER_FX_TYPE, WATER_SURFACE = "7E196E", "7E195E"


def load_tallon_station(n: int) -> list[str]:
    """Load station n of area 0 (as a continue would); Samus takes input ~550 frames later."""
    return (["poke 7E079F 00", "poke 7E07A0 00"] + poke16(0x7E078B, n) + poke16(0x7ED914, 5) + poke16(0x7E0998, 6)
            + ["wait 600"])


def with_gravity_suit() -> list[str]:
    return poke16(0x7E09A2, GRAVITY_SUIT) + poke16(0x7E09A4, GRAVITY_SUIT)


def camera_bottom(r) -> int:
    """Camera y ($0915) on the room's bottom screen, as walking there leaves it (Savestation, 1 screen: $1F)."""
    return (r.height - 1) * 256 + 31


def door_teleport(m: dict, key: str, to: str) -> list[str]:
    """Through the door of `key` that leads to `to` without walking to it: Samus is put in front of
    it and the door transition starts as the door block collision starts it ($94:938B: transition
    function $099C = $E17D, $078D = door entry, game state 9).
    For the rooms behind the power-conduit doors (wave doors since 09a) the game can't reach yet.
    specs/10a: the camera ($0911/$0915) is put on the door's screen too, where walking to the door leaves it. Without it
    a floor or ceiling door's transition left BG1's offsets ($091D/$091F) off a whole screen (Savestation -> Reactor
    Access $00E1, walking $0100) for the rest of the chain (PLMs drawn off their blocks: items and caps twice), and a
    teleport up through a ceiling door didn't change room. specs/12f: any built room (the Chozo's too)."""
    r = built_room(key)
    i = next(i for i, d in enumerate(r.doors) if d.to_room == to)
    d, wb, hb = r.doors[i], r.width * 16, r.height * 16
    if d.side in "LR":
        x, y = (24 if d.side == "L" else (wb - 2) * 16 + 8), (d.screen * 16 + 10) * 16 - 21
        cam = (0 if d.side == "L" else (r.width - 1) * 256, min(d.screen * 256, camera_bottom(r)))
    elif d.side == "T":
        x, y = (d.screen * 16 + 7) * 16 + 8, 4 * 16
        cam = (d.screen * 256, 0)
    else:
        x, y = (d.screen * 16 + 7) * 16 + 8, (hb - 2) * 16
        cam = (d.screen * 256, camera_bottom(r))
    place = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y)):
        place += poke16(addr, v)
    # placed twice: the first stops a walk (with speed left, the transition doesn't start)
    return (place + ["wait 30"] + place + poke16(0x7E0911, cam[0]) + poke16(0x7E0915, cam[1]) + ["wait 2"]
            + poke16(0x7E099C, DOOR_HIT_TRANSITION)
            + poke16(0x7E078D, m[key]["doors"][i] & 0xFFFF) + poke16(0x7E0998, 9) + ["wait 300"])


# the underwater jump (tools/smlib/reach.py WATER_*), measured on the Savestation floor (row 13) at
# column 2, open up to row 3: without the Gravity Suit, then with it; facing right before each jump
WATER_JUMP_X, WATER_JUMP_Y = 2 * 16 + 8, 13 * 16 - 21
WATER_JUMPS = [("sem_gravity_parado", 0, "A", 260), ("sem_gravity_direcao", 0, "RIGHT+A", 260),
               ("gravity_parado", GRAVITY_SUIT, "A", 140), ("gravity_direcao", GRAVITY_SUIT, "RIGHT+A", 140)]


def measure_water_jumps() -> list[str]:
    out = ["hold LEFT 20", "wait 60"]                    # off the save pedestal
    place = []
    for addr, v in ((0x7E0AF6, WATER_JUMP_X), (0x7E0B10, WATER_JUMP_X), (0x7E0AFA, WATER_JUMP_Y), (0x7E0B14, WATER_JUMP_Y)):
        place += poke16(addr, v)
    for _, items, buttons, frames in WATER_JUMPS:
        out += poke16(0x7E09A2, items) + ["hold RIGHT 2", "wait 20"] + place + ["wait 30"] + place + ["wait 90"]
        out += ([f"hold {buttons} 1"] + [f"peekw {a}" for a in SAMUS_X_Y_RADIUS]) * frames
    return out


def check_water_jumps(stdout: str, at_least: bool = False) -> list[str]:
    """The underwater trajectories must give reach.py's WATER_* constants exactly. specs/18d: `at_least` (area 4's flooded test
    room, check_ice_water_jumps): the rises exactly, each horizontal reach at least the model's (never shorter: the model stays
    on the safe side), the differences printed."""
    vals = [int(v, 16) for v in re.findall(r"7E0(?:AF6|AFA|B00) = ([0-9A-F]{4})", stdout)]
    frames = [(x, y + r) for x, y, r in zip(vals[0::3], vals[1::3], vals[2::3])]
    if len(frames) != sum(j[3] for j in WATER_JUMPS):
        return [f"FAIL pulo na água: {len(frames)} quadros lidos"]
    got, at = {}, 0
    for name, _, _, n in WATER_JUMPS:
        try:
            got[name] = reach.arc_from_samples(frames[at:at + n])
        except ValueError as e:
            return [f"FAIL pulo na água {name}: {e}"]
        at += n
    want = {"sem_gravity_parado": (reach.WATER_RISE_PX, None), "sem_gravity_direcao": (reach.WATER_RISE_PX, reach.WATER_ARC_PX),
            "gravity_parado": (reach.WATER_GRAVITY_RISE_PX, None),
            "gravity_direcao": (reach.WATER_GRAVITY_RISE_PX, reach.WATER_GRAVITY_ARC_PX)}
    fails = []
    for k, (rise, arc) in want.items():
        if got[k][0] != rise:
            fails.append(f"FAIL pulo na água {k}: subiu {got[k][0]} px, reach.py diz {rise}")
        if arc is not None and at_least and set(got[k][1]) == set(arc) and all(got[k][1][h] >= arc[h] for h in arc):
            if got[k][1] != arc:
                print(f"água (área 4) {k}: alcance {got[k][1]}, reach.py {arc} (nunca menor)")
        elif arc is not None and got[k][1] != arc:
            fails.append(f"FAIL pulo na água {k}: alcance {got[k][1]}, reach.py diz {arc}")
    return fails


def check_ice_water_jumps(stdout: str) -> list[str]:
    return check_water_jumps(stdout, at_least=True)


# the walk from the save station: off the pedestal into the floor door, down into the Reactor Access
# (onto the ledge under its ceiling door), left to the Reactor Core door and right to the Cargo Lift
# door (power-conduit doors: grey, the Power Beam doesn't open them), back onto the ledge and up the
# ceiling door into the Savestation. Legs measured in the emulator (spec 07l, Desvios).
TALLON_D_PATH = ["tallon_landing_site", "tallon_savestation", "tallon_reactor_access", "tallon_savestation"]


def tallon_route_d() -> list[str]:
    return ([f"peekw {ROOM_PTR}", "hold LEFT 40", "wait 200", f"peekw {ROOM_PTR}"]   # into the floor door, down
            # to the Reactor Core door: against its grey cap (x $25), so she landed on the ledge and
            # walked off it (with the default push she was stuck in it, build.DOWN_PUSH)
            + tallon_walk("LEFT", "d_oeste", 6, jump=False) + [f"expect {SAMUS_X} 0025"]
            + ["shot build/tests/tallon_d_porta_reactor_core.png"]
            + tallon_walk("RIGHT", "d_leste", 8, jump=False) + [f"expect {SAMUS_X} 00DB"]   # the Cargo Lift door's cap
            + ["shot build/tests/tallon_d_porta_cargo_lift.png"]
            + ["hold LEFT 12", "wait 20", "hold LEFT+A 40", "wait 30",        # onto the ledge
               # up the ceiling door, steering right onto the floor beside the floor door on arrival
               "hold LEFT 20", "wait 20", "hold A 40", "hold RIGHT 250", "wait 100", f"peekw {ROOM_PTR}"])


# spec 08: down a floor door of the frigate on foot (no teleport). From the Map Facility's west door
# ledge Samus space jumps onto the platform, walks off its east end and falls into the floor door
# to the Connection Elevator to Deck Beta. Standing on the ledge under its ceiling door (row 6, feet
# at y 96: y $004B with the standing radius) she walks right. With the default push ($8000) she stopped
# at y $0052, 7 px inside the ledge, and walked 0 px until she jumped (build.DOWN_PUSH).
FLOOR_DOOR_LANDING_Y, FLOOR_DOOR_ARRIVAL_X, FLOOR_DOOR_WALK_X = "004B", "007A", "00C6"


def walk_down_floor_door() -> list[str]:
    return (["hold RIGHT 8", "hold RIGHT+A 30"] + ["hold RIGHT 1", "hold RIGHT+A 1"] * 20   # onto the platform
            + ["hold RIGHT 140", "wait 200"]                                                  # off it, down the door
            + [f"expect {SAMUS_X} {FLOOR_DOOR_ARRIVAL_X}", f"expect 7E0AFA {FLOOR_DOOR_LANDING_Y}",
               "hold RIGHT 30", "wait 20", f"expect {SAMUS_X} {FLOOR_DOOR_WALK_X}"])


def route(start: str, goal: str, allow_locked: bool) -> list[str]:
    by = {r.key: r for r in ROOMS}
    prev, queue = {start: None}, [start]
    while queue:
        k = queue.pop(0)
        for i, d in enumerate(by[k].doors):
            if d.locked and not allow_locked:
                continue
            if d.to_room not in prev:
                prev[d.to_room] = (k, i)
                queue.append(d.to_room)
    path, k = [], goal
    while prev[k]:
        path.append(prev[k])
        k = prev[k][0]
    return list(reversed(path))


def walk_rooms(room_keys: list[str]) -> list[tuple[str, int]]:
    by = {r.key: r for r in ROOMS}
    steps = []
    for a, b in zip(room_keys, room_keys[1:]):
        i = next(i for i, d in enumerate(by[a].doors) if d.to_room == b)
        steps.append((a, i))
    return steps


def traverse(steps, room_ptr: dict) -> list[str]:
    by = {r.key: r for r in ROOMS}
    out = []
    for key, i in steps:
        target = by[key].doors[i].to_room
        out += go_through(by[key], i) + [f"expect {ROOM_PTR} {room_ptr[target]}"]
    return out


TALLON_D_CHAINS = [["tallon_savestation", "tallon_reactor_access", "tallon_cargo_lift", "tallon_transit_hall",
                    "tallon_biohazard", "tallon_security_hall", "tallon_biotech_1", "tallon_conduit_hall",
                    "tallon_elevator_beta", "tallon_hydro_access"],
                   ["tallon_savestation", "tallon_reactor_access", "tallon_reactor_core", "tallon_vent_a",
                    "tallon_vent_b", "tallon_vent_c"]]


def tallon_sunken_tour(m: dict, room: dict) -> list[str]:
    from tallon import items as tallon_items
    by = TALLON.by_key()
    n_tank = next(n for n, it in tallon_items.placed(set(by)) if it.room == "tallon_cargo_lift")
    tank = tallon_items.ITEMS[n_tank]
    out = []
    for k, chain in enumerate(TALLON_D_CHAINS):
        if k:
            out += load_tallon_station(SAVESTATION.index)
        for a, b in zip(chain, chain[1:]):
            out += door_teleport(m, a, b) + [f"expect {ROOM_PTR} {room[b]}",
                                             f"expect {WATER_FX_TYPE} {'0006' if by[b].water else '0000'}"]
            if b in TALLON.enemies:
                out += tallon_enemies_alive(b)
            out += [f"poke {HEALTH} 63", "hold START 10", "wait 200", "hold START 10", "wait 200",
                    f"shot build/tests/tallon_d_{b.removeprefix('tallon_')}.png"]
            if b == tank.room:   # its Energy Tank: on the upper deck, over the shaft
                # put on the deck 3 blocks west of it, then walk into it (the pickup needs her to move)
                x, y = (tank.spot[0] - 3) * 16 + 8, (tank.spot[1] + 1) * 16 - 21
                out += [item_not_taken(n_tank), "expect 7E09C4 0063"]
                for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y)):
                    out += poke16(addr, v)
                out += ["wait 30", "hold RIGHT 40", "wait 120", "shot build/tests/tallon_d_energy_tank.png", "wait 300",
                        "hold A 2", "wait 120", "expect 7E09C4 00C7", item_taken(n_tank), f"expect {GAME_STATE} 0008"]
    return out


# spec 07m: region E (the great tree) and Gully/Alcove. Region E is behind the sunken frigate (Gravity
# Suit, power conduits) and its ice doors; the Gully behind the Tallon Canyon's bomb walls (grey). As in
# 07l, the tests go through the doors with door_teleport: region E from the Savestation (load station 1)
# down the sunken frigate's first chain to the Hydro Access and through its floor door; Gully and Alcove
# from the landing.
TALLON_E_TOUR = ["tallon_hydro_access", "tallon_great_tree_hall", "tallon_great_tree_chamber", "tallon_great_tree_hall",
                 "tallon_tunnel_d", "tallon_transport_chozo_south", "tallon_tunnel_d", "tallon_great_tree_hall",
                 "tallon_tunnel_e", "tallon_transport_mines_east", "tallon_tunnel_e", "tallon_great_tree_hall",
                 "tallon_life_grove_tunnel", "tallon_life_grove"]
XRAY_EQUIPMENT, SPACE_JUMP_EQUIPMENT = 0x8000, 0x0200   # $09A4 bits (collected items)
RAIN_FX_TYPE = "000A"   # FX type of crateria.RAIN_FX ($83:80C0, byte 9)


def pick_up(n: int, shot: str, taken: tuple[int, ...] = (), start: int = -3, frames: int = 40) -> list[str]:
    """Walk into item n of tallon/items.py from `start` blocks from it on its floor (negative = west; she
    walks toward it for `frames`: a pickup needs her to move), close its message box (A after ~240
    frames). `taken`: items of this run already picked up (their bits may share n's byte; specs/09f: or the next
    one, which the 16-bit `expect` reads too, as item_not_taken_with)."""
    return [item_not_taken_with(n, taken)] + near_item(n, start) + ["wait 30", f"hold {'RIGHT' if start < 0 else 'LEFT'} {frames}", "wait 120", f"shot {shot}", "wait 300",
                  "hold A 2", "wait 120", item_taken(n), f"expect {GAME_STATE} 0008"]


def near_item(n: int, start: int, floor: int | None = None) -> list[str]:
    """Samus put by RAM `start` blocks from item n of tallon/items.py, on its floor (negative = west), or on the floor row
    `floor` there (specs/12e: the Chozo East's step before the Gravity Suit's)."""
    from tallon import items as tallon_items
    it = tallon_items.ITEMS[n]
    x, y = (it.spot[0] + start) * 16 + 8, (it.spot[1] + 1 if floor is None else floor) * 16 - 21
    out = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y)):
        out += poke16(addr, v)
    return out


def item_index(room: str) -> int:
    from tallon import items as tallon_items
    return next(n for n, it in enumerate(tallon_items.ITEMS) if it.room == room)


def tallon_visit(m: dict, room: dict, a: str, b: str, tag: str) -> list[str]:
    """door_teleport from a to b: b loads, dry (no water FX: the rain's, $0A, in the rooms with rain),
    its enemies alive; a screenshot."""
    fx = RAIN_FX_TYPE if TALLON.by_key()[b].fx == crateria.RAIN_FX else "0000"
    out = door_teleport(m, a, b) + [f"expect {ROOM_PTR} {room[b]}", f"expect {WATER_FX_TYPE} {fx}"]
    if TALLON.by_key()[a].doors[next(i for i, d in enumerate(TALLON.by_key()[a].doors) if d.to_room == b)].side == "B":
        out += ["wait 60", f"expect 7E0AFA {6 * 16 - 21:04X}"]   # down a floor door: on the platform under the ceiling door
    if b in TALLON.enemies:
        out += tallon_enemies_alive(b)
    return out + [f"poke {HEALTH} 63", "hold START 10", "wait 200", "hold START 10", "wait 200",
                  f"shot build/tests/tallon_{tag}_{b.removeprefix('tallon_')}.png"]


# specs/09e: the Life Grove's hut of power bomb blocks round the X-Ray (tools/tallon/layouts.py xray_hut): from the
# Life Grove Tunnel door, walking east she drops down the terraces and 4 jumps take her over the Chozo pillar to the
# grove's floor west of the hut (measured); walking on, she stops against its west wall (column 37: x = 37 * 16 - 5)
LIFE_GROVE_TO_HUT = ["hold RIGHT 150", "wait 60"] + ["hold RIGHT+A 40", "hold RIGHT 10", "wait 30"] * 4 + [
    "hold RIGHT 40", "wait 20"]
HUT_WEST_X = 37 * 16 - 5
POWER_BOMBS, MAX_POWER_BOMBS, HUD_ITEM = "7E09CE", "7E09D0", "7E09D2"   # $09D2 = 3: power bombs selected
POWER_BOMB_BLOCK = f"{0xC000 | 0x057:04X}"
# a chain of door_teleports leaves BG1's offsets ($091D/$091F) off a whole screen (in the Life Grove $091F = $01C4,
# in the Mines East $00C4: from the first teleport down the Savestation's floor door, $00E1, where walking down it
# gives $0100; tallon_grande_arvore also $091D = $FC4C): the PLMs (item, broken blocks) then draw off their blocks
# (4 rows, 4 columns), a ghost item shows in the rock and Samus is lost from the photo. Set to whole screens ($091D
# as tallon_power_bomb's chain leaves it, $091F the next whole screen), then a pause redraws the room (as
# tallon_morph_and_bombs does for the Tallon Canyon)
LIFE_GROVE_BG1_OFFSETS, MINES_EAST_BG1_OFFSETS = (0xFC00, 0x0200), (0xFC00, 0x0100)


def whole_screen_bg1(offsets: tuple[int, int] = LIFE_GROVE_BG1_OFFSETS) -> list[str]:
    return (poke16(0x7E091D, offsets[0]) + poke16(0x7E091F, offsets[1])
            + ["hold START 10", "wait 200", "hold START 10", "wait 200"])


def power_bomb_hut() -> list[tuple[int, int]]:
    from tallon import layouts as tallon_layouts
    return [(x, y) for x, y, _, _ in tallon_layouts.xray_hut()]


def tallon_great_tree_tour(m: dict, room: dict) -> list[str]:
    out = []
    for a, b in zip(TALLON_D_CHAINS[0], TALLON_D_CHAINS[0][1:]):   # down to the Hydro Access
        out += door_teleport(m, a, b) + [f"expect {ROOM_PTR} {room[b]}"]
    for a, b in zip(TALLON_E_TOUR, TALLON_E_TOUR[1:]):
        out += tallon_visit(m, room, a, b, "e")
        if (a, b) == ("tallon_great_tree_hall", "tallon_great_tree_chamber"):   # its Missile Expansion
            out += [f"expect {MAX_MISSILES} 0000"] + pick_up(item_index(b), "build/tests/tallon_e_missil.png") + [
                f"expect {MAX_MISSILES} 0005"]
        if (a, b) == ("tallon_tunnel_e", "tallon_transport_mines_east"):   # specs/09e: the Power Bomb
            out += pick_up(lock_item(b), "build/tests/tallon_e_power_bomb.png") + [
                f"expect {POWER_BOMBS} 0005", f"expect {MAX_POWER_BOMBS} 0005"]
    # specs/09e (was: the X-Ray picked up on the open floor): the X-Ray Visor inside its power bomb hut; walking to
    # it she stops against the hut's west wall, and the X-Ray stays where it is (tallon_power_bomb breaks the hut)
    taken = (item_index("tallon_great_tree_chamber"), lock_item("tallon_transport_mines_east"))
    return out + whole_screen_bg1() + LIFE_GROVE_TO_HUT + [f"expect {SAMUS_X} {HUT_WEST_X:04X}",
                                                           item_not_taken_with(item_index("tallon_life_grove"), taken),
                                                           "shot build/tests/tallon_e_cabana_do_xray.png"]


def tallon_power_bomb(m: dict, room: dict) -> list[str]:
    """specs/09e. Shortcuts (each noted): from the Savestation (load station 1, the Gravity Suit by RAM, as the other
    region D/E tests) the rooms are reached by door_teleport: down the sunken frigate to the Hydro Access, the Great
    Tree Hall, through the ice doors to the Transport to Phazon Mines East and back, then the Life Grove Tunnel and
    the Life Grove (BG1's row offset set back to a whole screen: WHOLE_SCREEN_BG1_ROW); the Morph Ball by RAM (picked
    up and used in tallon_morph_e_bombas). Then, for real: walk into the Power Bomb (bit $B3, 5/5 power bombs);
    from the Life Grove's door walk to the hut (LIFE_GROVE_TO_HUT): standing she stops against its west wall, a
    Power Beam shot leaves it, the X-Ray is not taken; DOWN DOWN = ball, SELECT = power bombs ($09D2 = 3), X lays one:
    the 15 power bomb blocks turn to air in the level in WRAM (4 power bombs left), 600 frames later still air (BTS
    $09 does not come back); UP UP = standing, she walks into the X-Ray (bit $AC, $09A4 with $8000)."""
    pb, xray = lock_item("tallon_transport_mines_east"), item_index("tallon_life_grove")
    hut = [level_block("tallon_life_grove", x, y) for x, y in power_bomb_hut()]
    wall = level_block("tallon_life_grove", 37, 29)
    out = []
    for a, b in zip(TALLON_D_CHAINS[0], TALLON_D_CHAINS[0][1:]):
        out += door_teleport(m, a, b)
    for a, b in (("tallon_hydro_access", "tallon_great_tree_hall"), ("tallon_great_tree_hall", "tallon_tunnel_e"),
                 ("tallon_tunnel_e", "tallon_transport_mines_east")):
        out += door_teleport(m, a, b)
    out += [f"expect {ROOM_PTR} {room['tallon_transport_mines_east']}", f"expect {POWER_BOMBS} 0000"]
    out += whole_screen_bg1(MINES_EAST_BG1_OFFSETS) + ["shot build/tests/tallon_power_bomb_sala.png"]
    out += pick_up(pb, "build/tests/tallon_power_bomb_mensagem.png") + [
        f"expect {POWER_BOMBS} 0005", f"expect {MAX_POWER_BOMBS} 0005", "shot build/tests/tallon_power_bomb_pega.png"]
    out += poke16(0x7E09A2, GRAVITY_SUIT | MORPH_BALL_EQUIPMENT) + poke16(0x7E09A4, GRAVITY_SUIT | MORPH_BALL_EQUIPMENT)
    for a, b in (("tallon_transport_mines_east", "tallon_tunnel_e"), ("tallon_tunnel_e", "tallon_great_tree_hall"),
                 ("tallon_great_tree_hall", "tallon_life_grove_tunnel"), ("tallon_life_grove_tunnel", "tallon_life_grove")):
        out += door_teleport(m, a, b)
    out += [f"expect {ROOM_PTR} {room['tallon_life_grove']}"] + whole_screen_bg1()
    out += LIFE_GROVE_TO_HUT + [f"expect {SAMUS_X} {HUT_WEST_X:04X}", item_not_taken_with(xray, (pb,))]
    out += [f"expect {a:06X} {POWER_BOMB_BLOCK}" for a in hut] + ["shot build/tests/tallon_cabana_do_xray.png"]
    out += ["hold X 2", "wait 40", f"expect {wall:06X} {POWER_BOMB_BLOCK}"]          # the Power Beam does nothing
    out += ["hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_POSE}"]
    out += ["hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0003"]
    out += ["hold X 2", "wait 80", "shot build/tests/tallon_power_bomb_explodindo.png", "wait 220"]
    out += [f"expect {a:06X} 00FF" for a in hut] + [f"expect {POWER_BOMBS} 0004", "shot build/tests/tallon_cabana_aberta.png"]
    out += ["wait 600"] + [f"expect {a:06X} 00FF" for a in hut]
    out += ["hold UP 2", "wait 30", "hold UP 2", "wait 30", f"expect {POSE} {STAND_POSE}"]
    return out + ["hold RIGHT 40", "wait 120", "shot build/tests/tallon_xray_mensagem.png", "wait 300", "hold A 2",
                  "wait 120", item_taken(xray), f"expectbit 7E09A5 {XRAY_EQUIPMENT >> 8:02X}", f"expect {GAME_STATE} 0008",
                  "shot build/tests/tallon_xray_pego.png"]


# specs/13: the PLM table in WRAM (40 slots, 39 at the top): headers $1C37, block indices $1C87 (sm_84.c)
PLM_HEADERS, PLM_BLOCKS = 0x7E1C37, 0x7E1C87


def plm_slot(table: int, slot: int) -> str:
    return f"{table + 2 * slot:06X}"


def bombed_item_touch(m: dict, room: dict) -> list[str]:
    """specs/13, power_bomb_nao_apaga_item: in the Overgrown Cavern (PLM slots: 39 west ice cap, 38 east ice cap, 37 the
    missile at (16, 9)), the east door is opened with the Ice Beam (its PLM ends: slot 38 free); a power bomb laid 4 blocks
    east of the missile (its sweep stops short of the west cap) sweeps the missile's block: the engine leaves a dead PLM in
    slot 38 (header 0) with the missile's block index ($84:B62F, list $84:AAE3 = Delete). Then a slot above it frees without
    a PLM spawned first, as the power bomb blocks' PLMs end in the Main Plaza or the Life Grove: shortcut, the west cap's PLM
    ended by RAM (header 0). Walking into the missile, the touch's PLM takes slot 39; vanilla's lookup ($84:EEAB) took the
    dead slot 38 and the missile was not picked up (emulator, the ROM before specs/13); now the missile is taken. Shortcuts,
    each noted: the rooms by door_teleport, the Ice Beam, the Morph Ball and 5 power bombs by RAM, Samus put by RAM."""
    key = "tallon_overgrown_cavern"
    n = item_index(key)
    it = TALLON.by_key()[key]
    index = 2 * (tallon_item_spot(n)[1] * it.width * 16 + tallon_item_spot(n)[0])
    out = chain_teleports(m, room, tallon_door_path(LANDING_SITE, key))
    out += give_beams(ICE_BEAM) + poke16(0x7E09A2, MORPH_BALL_EQUIPMENT) + poke16(0x7E09A4, MORPH_BALL_EQUIPMENT)
    out += poke16(0x7E09CE, 5) + poke16(0x7E09D0, 5)
    out += [f"expect {plm_slot(PLM_HEADERS, 37)} EEDB", f"expect {plm_slot(PLM_BLOCKS, 37)} {index:04X}",
            f"expect {plm_slot(PLM_HEADERS, 38)} {beamdoors_plm('R'):04X}", f"expect {plm_slot(PLM_HEADERS, 39)} {beamdoors_plm('L'):04X}"]
    out += (stand_before_door(key, "tallon_tunnel_c") + beam_door_shut(key, "tallon_tunnel_c")
            + beam_door_shoot(key, "tallon_tunnel_c", 1) + ["wait 120", f"expect {plm_slot(PLM_HEADERS, 38)} 0000"])
    out += near_item(n, 4) + ["wait 30", "hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_POSE}",
                              "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0003", "hold X 2", "wait 80",
                              "shot build/tests/13_power_bomb.png", "wait 220", f"expect {POWER_BOMBS} 0004"]
    out += [f"expect {plm_slot(PLM_HEADERS, 38)} 0000", f"expect {plm_slot(PLM_BLOCKS, 38)} {index:04X}",   # the dead slot
            f"expect {plm_slot(PLM_HEADERS, 37)} EEDB", item_not_taken(n),
            "hold UP 2", "wait 30", "hold UP 2", "wait 30", f"expect {POSE} {STAND_POSE}"]
    out += poke16(PLM_HEADERS + 2 * 39, 0)    # shortcut: the PLM above the dead slot ends (the west cap's, by RAM)
    return out + pick_up(n, "build/tests/13_missil_mensagem.png") + ["shot build/tests/13_missil_pego.png"]


def tallon_item_spot(n: int) -> tuple[int, int]:
    from tallon import items as tallon_items
    return tallon_items.ITEMS[n].spot


def beamdoors_plm(side: str) -> int:
    from tallon import beamdoors
    from tallon.rooms import ICE
    return beamdoors.PLM[(ICE, side)]


def tallon_gully_alcove(m: dict, room: dict) -> list[str]:
    """From the landing: into the Alcove (the Landing Site's ledge door), pick up the Space Jump; back
    onto the ledge; through the Gully door into the Gully (its 3 Parasites); down its floor door into
    the Tallon Canyon, onto the platform under the Gully door. specs/09d (was: the grey cap the jumps don't
    open): the door has no cap; walking west she stops against the bomb blocks (no Morph Ball, no Bombs:
    x GULLY_TUNNEL_X), and a jump steered onto the Gully's floor-door ledge takes her back up into it."""
    out = tallon_visit(m, room, "tallon_landing_site", "tallon_alcove", "a")
    out += pick_up(item_index("tallon_alcove"), "build/tests/tallon_a_space_jump.png") + [
        f"expectbit 7E09A5 {SPACE_JUMP_EQUIPMENT >> 8:02X}"]
    out += tallon_visit(m, room, "tallon_alcove", "tallon_landing_site", "a")
    out += tallon_visit(m, room, "tallon_landing_site", "tallon_gully", "a")
    out += tallon_visit(m, room, "tallon_gully", "tallon_canyon", "a")   # onto the platform under the Gully door
    out += ["hold LEFT 40", "wait 20", f"expect {ROOM_PTR} {room['tallon_canyon']}", f"expect 7E0AFA {6 * 16 - 21:04X}",
            f"expect {SAMUS_X} {GULLY_TUNNEL_X:04X}", "shot build/tests/tallon_a_blocos_de_bomba.png"]
    return out + GULLY_UP + [f"expect {ROOM_PTR} {room['tallon_gully']}", f"expect {GAME_STATE} 0008"]


# specs/09d: the Tallon Canyon's Morph Ball tunnel (tools/tallon/layouts.py): bomb blocks (53, 5) and (54, 5),
# standing Samus stops against the first from the west (x $34B) and against the second from the east (x $375);
# up into the Gully: jump, then steer left onto the floor door's west ledge (straight up she drops back down)
GULLY_TUNNEL_X = 54 * 16 + 16 + 5
TUNNEL_WEST_X = 53 * 16 - 5
GULLY_UP = ["hold A 30", "hold A+LEFT 30", "hold LEFT 200", "wait 100"]
POSE = "7E0A1C"                       # Samus' pose: $1D = morph ball, $27 = crouching, $01 = standing (facing right)
BALL_POSE, CROUCH_POSE, STAND_POSE = "001D", "0027", "0001"
BOMB_ITEM_EQUIPMENT = 0x1000
CANYON_BG1_OFFSETS = (0xFC00, 0x0200)   # $091D/$091F after walking into the Tallon Canyon from the Canyon Cavern


def level_block(key: str, x: int, y: int) -> int:
    """WRAM address of a block of the current room's layer 1 (its level at $7F:0002)."""
    return LEVEL_RAM + 2 * (y * built_room(key).width * 16 + x)   # specs/12f: any built room


# specs/12e: the Morph Ball lies at the foot of the Chozo West's steps, east of the elevator platform (was on it, (8, 25),
# walked into from 3 blocks east): walked into from 2 blocks west, the platform's fixed east end
MORPH_START = -2


def tallon_morph_and_bombs(m: dict, room: dict) -> list[str]:
    """specs/09d. Shortcuts (each noted): the rooms are reached by door_teleport (Tunnel A -> Chozo West: the
    walk there is tallon_rota_mvp's; Temple Lobby -> Artifact Temple: behind the red door; Canyon Cavern ->
    Tallon Canyon, with BG1's offsets set as a walk-in leaves them), and Samus is put by RAM near each item (on its floor) and on the west end of the Canyon's
    platform (the climb from the shelf onto it is the 07m one). Then, for real: walk into the Morph Ball (bit
    $B1, $0004) and the Bombs (bit $B2, $1004); standing she stops against the first bomb block; DOWN DOWN =
    ball; a bomb breaks the first block (air in the level in WRAM), she rolls in; UP under the tunnel roof
    keeps the ball; a bomb breaks the second; past it, in the chamber under the Gully door, UP UP = stand;
    600 frames later both blocks are still air (BTS 4 does not come back); the jump takes her into the Gully."""
    morph, bombs = item_index("tallon_transport_chozo_west"), item_index("tallon_artifact_temple")
    b1, b2 = level_block("tallon_canyon", 53, 5), level_block("tallon_canyon", 54, 5)
    block = f"{0xF000 | 0x058:04X}"
    return (door_teleport(m, "tallon_tunnel_a", "tallon_transport_chozo_west")
            + [f"expect {ROOM_PTR} {room['tallon_transport_chozo_west']}", f"expect {COLLECTED_ITEMS} 0000"]
            + tallon_look(11, 26, 0, 288, "build/tests/tallon_morph_sala.png")
            + pick_up(morph, "build/tests/tallon_morph_mensagem.png", start=MORPH_START)
            + [f"expect {EQUIPPED_ITEMS} {MORPH_BALL_EQUIPMENT:04X}", f"expect {COLLECTED_ITEMS} {MORPH_BALL_EQUIPMENT:04X}"]
            + door_teleport(m, "tallon_temple_lobby", "tallon_artifact_temple")
            + [f"expect {ROOM_PTR} {room['tallon_artifact_temple']}"]
            + tallon_look(15, 54, 0, 731, "build/tests/tallon_bombas_sala.png")
            + pick_up(bombs, "build/tests/tallon_bombas_mensagem.png", (morph,), start=2, frames=24)
            + [f"expect {EQUIPPED_ITEMS} {MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT:04X}",
               f"expect {COLLECTED_ITEMS} {MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT:04X}"]
            + door_teleport(m, "tallon_canyon_cavern", "tallon_canyon") + [f"expect {ROOM_PTR} {room['tallon_canyon']}"]
            # BG1's offsets as walking in through the Canyon Cavern door leaves them (measured: $FC00, $0200): a door
            # transition keeps them from the old room's camera ($80:AE29), and after the teleports from rooms whose
            # camera was moved by RAM the row offset came here as $0281, off a whole screen: the PLMs that redraw the
            # broken blocks then draw on the wrong rows and the blocks stay drawn (tallon_look's pause redraws all)
            + poke16(0x7E091D, CANYON_BG1_OFFSETS[0]) + poke16(0x7E091F, CANYON_BG1_OFFSETS[1])
            + tallon_look(52, 6, 640, 0, "build/tests/tallon_blocos_de_bomba.png")
            + ["hold RIGHT 30", "wait 20", f"expect {SAMUS_X} {TUNNEL_WEST_X:04X}", f"expect {b1:06X} {block}", f"expect {b2:06X} {block}"]
            + ["hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_POSE}", "shot build/tests/tallon_bola.png"]
            + ["hold RIGHT 20", "hold X 2", "wait 24", "shot build/tests/tallon_bomba_explodindo.png", "wait 66",
               f"expect {b1:06X} 00FF", f"expect {b2:06X} {block}", "shot build/tests/tallon_bloco_quebrado.png"]
            + ["hold RIGHT 20", "wait 10", f"expect {SAMUS_X} {TUNNEL_WEST_X + 16:04X}",
               "hold UP 2", "wait 30", f"expect {POSE} {BALL_POSE}", "shot build/tests/tallon_bola_no_tunel.png"]
            + ["hold RIGHT 4", "hold X 2", "wait 90", f"expect {b2:06X} 00FF", "hold RIGHT 30", "wait 10",
               f"expect {SAMUS_X} {57 * 16 + 11:04X}", "hold UP 2", "wait 30", f"expect {POSE} {CROUCH_POSE}",
               "hold UP 2", "wait 30", f"expect {POSE} {STAND_POSE}", f"expect 7E0AFA {6 * 16 - 21:04X}",
               "shot build/tests/tallon_tunel_aberto.png"]
            + ["wait 600", f"expect {b1:06X} 00FF", f"expect {b2:06X} 00FF"]
            # standing, the tunnel roof stops her at the chamber's west end: where tallon_gully_alcove jumps from
            + ["hold LEFT 40", "wait 20", f"expect {SAMUS_X} {GULLY_TUNNEL_X:04X}"]
            + GULLY_UP + [f"expect {ROOM_PTR} {room['tallon_gully']}", f"expect {GAME_STATE} 0008",
                          "shot build/tests/tallon_morph_gully.png"])


# spec 09a: the beam doors (tools/tallon/beamdoors.py). The beams come as items in 09b, so here the
# test setup gives them by RAM ($09A6 equipped / $09A8 collected beams), and the missiles too; the room
# is reached by door_teleport THROUGH the beam door, so its cap closes behind Samus (the beam door's own
# closing list). Shut = walking into the cap stops her against it: x $25 at a west-wall cap (block 1),
# (room width - 2) * 16 - 5 at an east-wall one (as tallon_rota_d measured on the grey caps).
WAVE_BEAM, ICE_BEAM, PLASMA_BEAM = 0x0001, 0x0002, 0x0008
BEAM_DOORS = {  # test -> (room entered through the door, room on the other side, its beam, a wrong beam)
    "porta_de_gelo": ("tallon_frigate_access", "tallon_crash_site", ICE_BEAM, WAVE_BEAM),
    "porta_de_onda": ("tallon_reactor_access", "tallon_reactor_core", WAVE_BEAM, ICE_BEAM),
    "porta_de_plasma": ("tallon_root_cave", "tallon_arbor_chamber", PLASMA_BEAM, ICE_BEAM | WAVE_BEAM),
}


def beam_door_side(key: str, to: str):
    r = TALLON.by_key()[key]
    return r, next(d for d in r.doors if d.to_room == to)


def beam_door_shut(key: str, to: str) -> list[str]:
    """Walk into the cap of key's door to `to`: she stops against it (the door is shut)."""
    r, d = beam_door_side(key, to)
    x = 2 * 16 + 5 if d.side == "L" else (r.width * 16 - 2) * 16 - 5
    toward = "LEFT" if d.side == "L" else "RIGHT"
    return [f"poke {HEALTH} 63", f"hold {toward} 40", "wait 20", f"expect {SAMUS_X} {x:04X}"]


def beam_door_shoot(key: str, to: str, n: int = 3) -> list[str]:
    toward = "LEFT" if beam_door_side(key, to)[1].side == "L" else "RIGHT"
    return [f"hold {toward}+X 2", "wait 30"] * n


def give_beams(v: int) -> list[str]:
    return poke16(0x7E09A6, v) + poke16(0x7E09A8, v) + ["wait 10"]


def beam_door_open_and_through(m: dict, room: dict, key: str, to: str, beam: int | None, tag: str) -> list[str]:
    """The right beam (None: the beams Samus has, picked up: specs/09b): one shot opens it (photo while it
    opens and once open), she walks through."""
    toward = "LEFT" if beam_door_side(key, to)[1].side == "L" else "RIGHT"
    return ((give_beams(beam) if beam is not None else []) + [f"hold {toward}+X 2", "wait 6", f"shot build/tests/{tag}_abrindo.png", "wait 120",
                                f"shot build/tests/{tag}_aberta.png", f"hold {toward} 90", "wait 200",
                                f"expect {ROOM_PTR} {room[to]}", f"expect {GAME_STATE} 0008"])


def wave_door_purple(key: str, to: str) -> list[str]:
    """specs/10d: the shut wave door is drawn with the purple metatiles (the cap's top block in the level in WRAM,
    $7F0002 + 2 * block) and palette line 6 holds the purple (the palette in WRAM, $7EC000 + 2 * colour)."""
    from tallon import beamdoors
    r, d = beam_door_side(key, to)
    cx, cy = (1 if d.side == "L" else r.width * 16 - 2), d.screen * 16 + 6     # build.door_cap_and_screen
    top = 0xC000 | (0x400 if d.side == "L" else 0) | beamdoors.PAINT_METATILES[0x004]
    return ([f"expect {0x7F0002 + 2 * (cy * r.width * 16 + cx):06X} {top:04X}"]
            + [f"expect {0x7EC000 + 2 * (beamdoors.PAINT_LINE * 16 + i):06X} {c:04X}" for i, c in enumerate(beamdoors.PURPLE, 1)])


def beam_door(m: dict, room: dict, name: str) -> list[str]:
    """Through the door into X; it is shut behind her; the Power Beam, missiles and a wrong beam leave it
    shut; the right beam opens it and she walks into Y; back through it (from Y's side: shut too if Y has
    a cap, opened with the beam; else door_teleport) into X, where it is shut again (no door bit: closed
    on every visit)."""
    x, y, beam, wrong = BEAM_DOORS[name]
    out = door_teleport(m, y, x) + [f"expect {ROOM_PTR} {room[x]}", "wait 30"]
    out += beam_door_shut(x, y) + [f"shot build/tests/{name}_fechada.png"]
    if beam == WAVE_BEAM:
        out += wave_door_purple(x, y)
    out += beam_door_shoot(x, y) + beam_door_shut(x, y)                                   # Power Beam
    out += (poke16(0x7E09C6, 5) + poke16(0x7E09C8, 5) + ["hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001"]
            + beam_door_shoot(x, y) + [f"expect {MISSILES} 0002"] + beam_door_shut(x, y)  # missiles
            + ["hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0000"])
    out += give_beams(wrong) + beam_door_shoot(x, y) + beam_door_shut(x, y)               # the wrong beam
    out += beam_door_open_and_through(m, room, x, y, beam, name)
    if beam_door_side(y, x)[1].lock is not None:      # Y's side has its cap: shut behind her, the beam opens it
        out += ["wait 30"] + beam_door_shut(y, x) + beam_door_open_and_through(m, room, y, x, beam, f"{name}_volta")
    else:   # no cap there (the Arbor Chamber: its door is up a step from the floor): back through it by teleport
        out += door_teleport(m, y, x) + [f"expect {ROOM_PTR} {room[x]}"]
    return out + ["wait 30"] + beam_door_shut(x, y) + [f"shot build/tests/{name}_fechada_de_novo.png"]


# spec 09b: the lock items of tools/tallon/items.py (rows 13-16: Ice, Wave, Gravity Suit, Plasma), each
# picked up by walking into it and used on its gate. The rooms are reached by door_teleport (behind red,
# ice and Space Jump gates the blind walkers don't climb), each noted; equipment RAM: $09A2/$09A4 equipped
# / collected items (Gravity Suit $0020, Space Jump $0200), $09A6/$09A8 equipped / collected beams.
EQUIPPED_ITEMS, COLLECTED_ITEMS, EQUIPPED_BEAMS, COLLECTED_BEAMS = "7E09A2", "7E09A4", "7E09A6", "7E09A8"
PAUSE_SCREEN = "7E0727"   # pause menu: 0 = map, 1 = equipment


def lock_item(room_key: str) -> int:
    from tallon import items as tallon_items
    return next(n for n, it in enumerate(tallon_items.ITEMS) if it.room == room_key and it.kind in tallon_items.GRANTS
                and tallon_items.GRANTS[it.kind] - {"missile", "space_jump", "xray"})


def has_beams(v: int) -> list[str]:
    return [f"expect {EQUIPPED_BEAMS} {v:04X}", f"expect {COLLECTED_BEAMS} {v:04X}"]


def equipment_screen(shot: str) -> list[str]:
    """Pause, R to the equipment screen (photo: the beams Samus has), back to the map, unpause."""
    return ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}", "hold R 10", "wait 200",
            f"expect {PAUSE_SCREEN} 0001", f"shot {shot}", "hold L 10", "wait 200", "hold START 10", "wait 200",
            f"expect {GAME_STATE} 0008"]


def beam_door_with_item(m: dict, room: dict, x: str, y: str, tag: str) -> list[str]:
    """Through the beam door of y into x (shut behind her), one shot of the beams she picked up opens it,
    she walks back into y."""
    return (door_teleport(m, y, x) + [f"expect {ROOM_PTR} {room[x]}", "wait 30"] + beam_door_shut(x, y)
            + [f"shot build/tests/{tag}_fechada.png"] + beam_door_open_and_through(m, room, x, y, None, tag))


def tallon_wave(m: dict, room: dict) -> list[str]:
    """Wave Beam: into the Transport to Magmoor East (door_teleport from Tunnel B: behind the Root Tunnel's red
    door), walk into it from the west; the bit and the beam are saved (ship's station by RAM, save on the ship,
    game over, continue); then the wave door: Reactor Access entered through it from the Reactor Core (region D:
    the Gravity Suit by RAM, the room is flooded), one shot opens it."""
    n = lock_item("tallon_transport_magmoor_east")
    return (door_teleport(m, "tallon_tunnel_b", "tallon_transport_magmoor_east")
            + [f"expect {ROOM_PTR} {room['tallon_transport_magmoor_east']}", "shot build/tests/tallon_onda_sala.png"]
            + has_beams(0) + pick_up(n, "build/tests/tallon_onda_mensagem.png") + has_beams(WAVE_BEAM)
            + load_tallon_station(0) + [f"expect {ROOM_PTR} {room[LANDING_SITE]}"] + has_beams(WAVE_BEAM)
            + ["hold UP 2", "wait 60"] + stand_on_tallon_ship() + save_on_tallon_ship("build/tests/tallon_onda_save.png")
            + ["poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}"]
            + GAME_OVER_CONTINUE
            + [f"expect {GAME_STATE} 0008", f"expect {ROOM_PTR} {room[LANDING_SITE]}", item_taken(n)] + has_beams(WAVE_BEAM)
            + equipment_screen("build/tests/tallon_onda_equipamento.png")
            + with_gravity_suit() + beam_door_with_item(m, room, "tallon_reactor_access", "tallon_reactor_core", "tallon_onda_porta"))


def tallon_ice(m: dict, room: dict) -> list[str]:
    """Ice Beam: the Space Jump by RAM (its shelf is Space Jump only); into the Root Cave (door_teleport from the
    Root Tunnel: behind its red door), put on the Arbor door's shelf 2 blocks west of the Ice (climbing the cave
    with the Space Jump is not what this tests) and walk into it, stopping before the shelf's missile; the
    equipment screen; then the ice door: Frigate Access entered through it from the Crash Site, one shot opens it."""
    n, missile = lock_item("tallon_root_cave"), item_index("tallon_root_cave")
    return (poke16(0x7E09A2, SPACE_JUMP_EQUIPMENT) + poke16(0x7E09A4, SPACE_JUMP_EQUIPMENT)
            + door_teleport(m, "tallon_root_tunnel", "tallon_root_cave") + [f"expect {ROOM_PTR} {room['tallon_root_cave']}"]
            # on the shelf with the camera on it, redrawn (a camera jump by RAM leaves the old background)
            + has_beams(0) + tallon_look(2, 10, 0, 0, "build/tests/tallon_gelo_sala.png")
            + pick_up(n, "build/tests/tallon_gelo_mensagem.png", start=-2, frames=24) + has_beams(ICE_BEAM)
            # the shelf from its west end, the camera on it (redrawn): the Ice gone, the missile still there
            + [f"expect {MAX_MISSILES} 0000"] + tallon_look(2, 10, 0, 0, "build/tests/tallon_gelo_prateleira.png")
            + equipment_screen("build/tests/tallon_gelo_equipamento.png")
            + beam_door_with_item(m, room, "tallon_frigate_access", "tallon_crash_site", "tallon_gelo_porta"))


# the Section C bulkhead (specs/07l): from its west door walk east and jump at it 8 times, then off the
# Section B door's cap (the jumps land on it) and shoot the blue door: without the suit she stays west of the
# bulkhead (x $BB: against it), with it she gets over and through into Section B
BULKHEAD_X = 12 * 16 - 5
BULKHEAD_TRY = (["hold RIGHT 120"] + ["hold RIGHT+A 40", "hold RIGHT 20"] * 8
                + ["wait 120", "hold LEFT 30", "wait 30", "hold RIGHT+X 2", "wait 30", "hold RIGHT+X 2", "wait 30",
                   "hold RIGHT 120", "wait 200"])


# specs/12e: the Gravity Suit lies on the Chozo East's last step (column 10, floor row 22), beside the elevator platform.
# Walking in from the door ("hold RIGHT 70") she stops on the step before it (column 9, floor row 18); a short walk
# (10-20 frames, measured) takes her off its edge onto the suit's step (40 frames, the old walk, ran past it).
GRAVITY_STEP_OFF = "hold RIGHT 14"
GRAVITY_TAKEN_X, GRAVITY_PAD_X = 0x00AC, 0x00CC   # measured (specs/12e)


def tallon_gravity(m: dict, room: dict) -> list[str]:
    """Gravity Suit: Section C without the suit (door_teleport from Frigate Access: behind the ice door), the
    bulkhead holds; into the Transport to Chozo Ruins East through its ice door (door_teleport from Tunnel C),
    walk down its steps into the suit (specs/12e: on the last step, beside the elevator platform); after the cutscene
    (specs/09b: she stays where she picked it up, not in the middle of the screen, which is inside the wall here) she
    is on that step and walks off it onto the elevator platform; Section C again, with the suit she gets over the
    bulkhead into Section B."""
    n = lock_item("tallon_transport_chozo_east")
    vent = door_teleport(m, "tallon_frigate_access", "tallon_vent_c") + [f"expect {ROOM_PTR} {room['tallon_vent_c']}", "wait 30"]
    return (vent + BULKHEAD_TRY + [f"expect {ROOM_PTR} {room['tallon_vent_c']}", f"expect {SAMUS_X} {BULKHEAD_X:04X}",
                                   "shot build/tests/tallon_gravity_sem_suit.png"]
            # camera back on a whole screen before the teleport: a door is always met with the camera on its
            # screen, and the transition keeps the camera's x offset (an animated PLM, as the item, drawn 64 px
            # off: specs/07h's bg1_x_offset)
            + poke16(0x7E0911, 0) + ["wait 2"]
            + door_teleport(m, "tallon_tunnel_c", "tallon_transport_chozo_east")
            + [f"expect {ROOM_PTR} {room['tallon_transport_chozo_east']}", item_not_taken(n), f"expect {EQUIPPED_ITEMS} 0000",
               "hold RIGHT 70", "wait 100", "shot build/tests/tallon_gravity_sala.png",
               GRAVITY_STEP_OFF, "wait 120", "shot build/tests/tallon_gravity_mensagem.png", "wait 300", "hold A 2",
               "wait 200", "shot build/tests/tallon_gravity_cena.png", "wait 1000", f"expect {GAME_STATE} 0008",
               item_taken(n), f"expect {EQUIPPED_ITEMS} {GRAVITY_SUIT:04X}", f"expect {COLLECTED_ITEMS} {GRAVITY_SUIT:04X}",
               # where she took it (specs/12e: x GRAVITY_TAKEN_X, on the last step; was $D0 on the elevator platform),
               # not the screen's middle ($78, in the wall)
               f"expect {SAMUS_X} {GRAVITY_TAKEN_X:04X}", "shot build/tests/tallon_gravity_paleta.png",
               # she walks: off the step onto the elevator platform (was: west along the platform to x $B5)
               "hold RIGHT 30", "wait 60", f"expect {SAMUS_X} {GRAVITY_PAD_X:04X}", f"expect 7E0AFA {26 * 16 - 21:04X}"]
            + vent + BULKHEAD_TRY + [f"expect {ROOM_PTR} {room['tallon_vent_b']}", "shot build/tests/tallon_gravity_vent_b.png"])


def tallon_plasma(m: dict, room: dict) -> list[str]:
    """Plasma Beam: Wave + Ice by RAM (picked up before it in the epic's order: $0003); into the Transport to
    Chozo Ruins South through its ice door (door_teleport from Tunnel D), walk into it from the west: $000B (no
    beam leaves); the plasma door (Root Cave entered through it from the Arbor Chamber) and an ice door
    (Frigate Access) each open with one shot of the combination."""
    n = lock_item("tallon_transport_chozo_south")
    return (give_beams(WAVE_BEAM | ICE_BEAM)
            + door_teleport(m, "tallon_tunnel_d", "tallon_transport_chozo_south")
            + [f"expect {ROOM_PTR} {room['tallon_transport_chozo_south']}", "shot build/tests/tallon_plasma_sala.png"]
            + pick_up(n, "build/tests/tallon_plasma_mensagem.png") + has_beams(WAVE_BEAM | ICE_BEAM | PLASMA_BEAM)
            + equipment_screen("build/tests/tallon_plasma_equipamento.png")
            + beam_door_with_item(m, room, "tallon_root_cave", "tallon_arbor_chamber", "tallon_plasma_porta")
            + beam_door_with_item(m, room, "tallon_frigate_access", "tallon_crash_site", "tallon_plasma_porta_de_gelo"))


LOCK_ITEM_TESTS = {"tallon_onda": tallon_wave, "tallon_gelo": tallon_ice, "tallon_gravity": tallon_gravity,
                   "tallon_plasma": tallon_plasma}


# specs/09f: the whole chain (tallon_cadeia_completa). From the landing, in the order of the rounds (tools/validate.py
# tallon_rounds; tallon/rooms.py FIRST_ROUND, tallon/items.py Item.round), the 20 items each picked up by walking into
# it (its message box closed with A), each round's lock opened for real: the red doors with missiles (1), the Tallon
# Canyon's bomb blocks (2), the Root Cave's Space Jump ledge, climbed (3), the ice doors (4), the Section C bulkhead
# with the Gravity Suit underwater and a wave door (5), the Power Bomb hut and the plasma door (6). Shortcuts, each
# noted where it is used (as in the earlier tests): rooms reached by door_teleport (CHAIN), only through doors with no
# lock or already opened in this run (a red door with its bit on; a beam door once Samus has its beam and opened one
# of its kind here; a Space Jump ledge once climbed); Samus put by RAM in front of a door, near an item (pick_up) or
# on the Tallon Canyon's platform; missiles and energy refilled by RAM (ammo, never capacity); back to the gunship by
# RAM (load station 0). No item or beam is ever given by RAM.
CHAIN_SHOT = "build/tests/cadeia"


def chain_teleports(m: dict, room: dict, path: list[str]) -> list[str]:
    """door_teleport through the consecutive rooms of `path` (shortcut: see the comment above)."""
    out = []
    for a, b in zip(path, path[1:]):
        out += door_teleport(m, a, b) + [f"expect {ROOM_PTR} {room[b]}"]
    return out


def stand_before_door(key: str, to: str, blocks: int = 4) -> list[str]:
    """Shortcut: Samus put by RAM standing `blocks` blocks inside key's side door to `to` (on the door's floor row,
    which must be ground there), placed twice to stop any run; pausing and unpausing redraws the screen after the
    camera's jump, put on the door's screen (for the photos)."""
    from smlib import reach as reach_model
    r = built_room(key)   # specs/12i: any built room (the Chozo's too)
    d = next(d for d in r.doors if d.to_room == to)
    wb = r.width * 16
    x = 2 + blocks if d.side == "L" else wb - 3 - blocks
    feet = d.screen * 16 + 9
    lv = r.level()
    l1, _ = lv.build_blocks()
    grid = reach_model.Grid([w >> 12 for w in l1], wb, r.height * 16)
    if not grid.stands(x, feet):
        raise ValueError(f"{key}: não dá para ficar de pé em ({x},{feet}) diante da porta para {to}")
    place = []
    for addr, v in ((0x7E0AF6, x * 16 + 8), (0x7E0B10, x * 16 + 8), (0x7E0AFA, (feet + 1) * 16 - 21),
                    (0x7E0B14, (feet + 1) * 16 - 21)):
        place += poke16(addr, v)
    camera = poke16(0x7E0911, 0 if d.side == "L" else (r.width - 1) * 256) + poke16(0x7E0915, d.screen * 256)
    return (place + ["wait 30"] + place + ["wait 30"] + camera
            + ["wait 4", "hold START 10", "wait 200", "hold START 10", "wait 200"])


def chain_red_door(room: dict, key: str, to: str, tag: str) -> list[str]:
    """In front of key's red door to `to` (stand_before_door): walking into it she stops; SELECT = missiles, 6 shots
    (5 hits open it, 5 missiles spent), its bit on; SELECT back to the beam; she walks through into `to`."""
    toward = "LEFT" if beam_door_side(key, to)[1].side == "L" else "RIGHT"
    return (stand_before_door(key, to) + beam_door_shut(key, to) + [f"expect {MISSILES} 0005", f"shot {CHAIN_SHOT}_{tag}_fechada.png",
            "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001"] + [f"hold {toward}+X 2", "wait 30"] * 6
            + ["wait 60", red_door_open(key, to), f"expect {MISSILES} 0000", f"shot {CHAIN_SHOT}_{tag}_aberta.png",
               "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0000", f"hold {toward} 90", "wait 200",
               f"expect {ROOM_PTR} {room[to]}", f"expect {GAME_STATE} 0008"])


def chain_beam_door(m: dict, room: dict, key: str, to: str, tag: str) -> list[str]:
    """In front of key's beam door to `to`: shut; one shot of the beams Samus picked up opens it; through it."""
    return (stand_before_door(key, to) + beam_door_shut(key, to) + [f"shot {CHAIN_SHOT}_{tag}_fechada.png"]
            + beam_door_open_and_through(m, room, key, to, None, f"cadeia_{tag}"))


def chain_round_2(m: dict, room: dict) -> list[str]:
    """Round 2, + the Bombs and the Wave: the Tallon Canyon's 2 bomb blocks bombed in the ball (as
    tallon_morph_e_bombas: Samus put on the west end of the platform, BG1's offsets as a walk-in leaves them), up the
    Gully door; through the Gully to the Landing Site's ledge and into the Alcove: the Space Jump."""
    taken = tuple(item_index(k) for k in ("tallon_landing_site", "tallon_transport_chozo_west", "tallon_artifact_temple",
                                          "tallon_tunnel_b", "tallon_crash_site")) + (lock_item("tallon_transport_magmoor_east"),)
    b1, b2 = level_block("tallon_canyon", 53, 5), level_block("tallon_canyon", 54, 5)
    block = f"{0xF000 | 0x058:04X}"
    out = chain_teleports(m, room, ["tallon_crash_site", "tallon_waterfall_cavern", "tallon_landing_site",
                                    "tallon_canyon_cavern", "tallon_canyon"])
    out += poke16(0x7E091D, CANYON_BG1_OFFSETS[0]) + poke16(0x7E091F, CANYON_BG1_OFFSETS[1])
    out += tallon_look(52, 6, 640, 0, f"{CHAIN_SHOT}_2_blocos_de_bomba.png")
    out += ["hold RIGHT 30", "wait 20", f"expect {SAMUS_X} {TUNNEL_WEST_X:04X}", f"expect {b1:06X} {block}", f"expect {b2:06X} {block}"]
    out += ["hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_POSE}"]
    out += ["hold RIGHT 20", "hold X 2", "wait 90", f"expect {b1:06X} 00FF", "hold RIGHT 20", "wait 10",
            "hold RIGHT 4", "hold X 2", "wait 90", f"expect {b2:06X} 00FF", f"shot {CHAIN_SHOT}_2_tunel_aberto.png",
            "hold RIGHT 30", "wait 10", "hold UP 2", "wait 30", "hold UP 2", "wait 30", f"expect {POSE} {STAND_POSE}"]
    out += ["hold LEFT 40", "wait 20", f"expect {SAMUS_X} {GULLY_TUNNEL_X:04X}"] + GULLY_UP
    out += [f"expect {ROOM_PTR} {room['tallon_gully']}", f"shot {CHAIN_SHOT}_2_gully.png"]
    out += chain_teleports(m, room, ["tallon_gully", "tallon_landing_site", "tallon_alcove"])
    return out + pick_up(item_index("tallon_alcove"), f"{CHAIN_SHOT}_2_space_jump.png", taken) + [
        f"expectbit 7E09A5 {SPACE_JUMP_EQUIPMENT >> 8:02X}"]


# specs/09f: up the Root Cave with the Space Jump (measured): from the Root Tunnel door west along the floor, a spin
# jump to the left (a run-up first: from a standstill the jump is not a spin), then the Space Jump's rhythm (A held 30
# frames, released 12: the next jump only takes while falling); with no direction she drifts west to the wall under
# the shelf, then held right against the hanging root (x 11) up past the shelf; a last jump to the left lands on it
ROOT_CAVE_CLIMB = (["hold LEFT 200", "wait 30", "hold LEFT 8", "hold LEFT+A 30"] + ["wait 12", "hold A 30"] * 5
                   + ["hold RIGHT 12", "hold RIGHT+A 30"] * 4 + ["hold LEFT 12", "hold LEFT+A 20", "hold LEFT 30"])
ROOT_CAVE_SHELF_ROW = 9   # Samus' feet on the Arbor door's shelf


def chain_round_3(m: dict, room: dict) -> list[str]:
    """Round 3, + the Space Jump: the Root Cave's ledge climbed for real (ROOT_CAVE_CLIMB); on the shelf, walking
    west, the Root Cave missile and then the Ice."""
    taken = tuple(item_index(k) for k in ("tallon_landing_site", "tallon_transport_chozo_west", "tallon_artifact_temple",
                                          "tallon_tunnel_b", "tallon_crash_site", "tallon_alcove")) + (
        lock_item("tallon_transport_magmoor_east"),)
    missile, ice = item_index("tallon_root_cave"), lock_item("tallon_root_cave")
    out = chain_teleports(m, room, ["tallon_alcove", "tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon",
                                    "tallon_root_tunnel", "tallon_root_cave"])
    out += [item_not_taken_with(missile, taken)] + ROOT_CAVE_CLIMB
    out += ["wait 60", f"shot {CHAIN_SHOT}_3_missil_root_cave.png",
            "wait 240", "hold A 2", "wait 120", item_taken(missile), f"expect {MAX_MISSILES} 0014"]
    # the box closed, she ends her landing (~20 frames) and walks on west into the Ice
    out += [item_not_taken_with(ice, taken + (missile,)), "hold LEFT 60", "wait 120", f"shot {CHAIN_SHOT}_3_ice.png",
            "wait 300", "hold A 2", "wait 120", item_taken(ice), f"expect {GAME_STATE} 0008",
            f"expect 7E0AFA {(ROOT_CAVE_SHELF_ROW + 1) * 16 - 21:04X}"]
    return out + has_beams(WAVE_BEAM | ICE_BEAM)


CHAIN_TAKEN_3 = (("tallon_landing_site", "tallon_transport_chozo_west", "tallon_artifact_temple", "tallon_tunnel_b",
                  "tallon_crash_site", "tallon_alcove", "tallon_root_cave"), ("tallon_transport_magmoor_east", "tallon_root_cave"))


def chain_taken(rooms: tuple, locks: tuple) -> tuple[int, ...]:
    """Indexes (tallon/items.py) of the Tallon items in `rooms` and of the lock items in `locks`."""
    return tuple(item_index(k) for k in rooms) + tuple(lock_item(k) for k in locks)


def chain_round_4(m: dict, room: dict) -> list[str]:
    """Round 4, + the Ice: the ice doors opened with one shot each (Crash Site -> Overgrown, put by RAM on the Crash
    Site's Space Jump ledge, climbed for real in round 3; Overgrown -> Tunnel C; Tunnel C -> Chozo East), the Overgrown
    missile, the Gravity Suit (its cutscene leaves her where she took it, specs/09b)."""
    taken = chain_taken(*CHAIN_TAKEN_3)
    overgrown, gravity = item_index("tallon_overgrown_cavern"), lock_item("tallon_transport_chozo_east")
    out = chain_teleports(m, room, ["tallon_root_cave", "tallon_root_tunnel", "tallon_canyon", "tallon_canyon_cavern",
                                    "tallon_landing_site", "tallon_waterfall_cavern", "tallon_crash_site"])
    out += chain_beam_door(m, room, "tallon_crash_site", "tallon_overgrown_cavern", "4_porta_de_gelo_overgrown")
    out += pick_up(overgrown, f"{CHAIN_SHOT}_4_missil_overgrown.png", taken) + [f"expect {MAX_MISSILES} 0019"]
    out += chain_beam_door(m, room, "tallon_overgrown_cavern", "tallon_tunnel_c", "4_porta_de_gelo_tunnel_c")
    out += chain_beam_door(m, room, "tallon_tunnel_c", "tallon_transport_chozo_east", "4_porta_de_gelo_chozo_east")
    # specs/12e: the suit is on the last step beside the elevator platform; Samus put on the step before it (column 9,
    # where the walk from the door stops: tallon_gravity), she walks off its edge onto the suit (GRAVITY_STEP_OFF)
    out += [item_not_taken_with(gravity, taken + (overgrown,)), "wait 60"] + near_item(gravity, -1, floor=18) + ["wait 30"] + near_item(gravity, -1, floor=18) + [
            "wait 30", GRAVITY_STEP_OFF, "wait 120", f"shot {CHAIN_SHOT}_4_gravity.png", "wait 300", "hold A 2", "wait 200", "wait 1000", f"expect {GAME_STATE} 0008",
            item_taken(gravity), f"expectbit 7E09A2 {GRAVITY_SUIT:02X}", f"expectbit 7E09A4 {GRAVITY_SUIT:02X}",
            f"shot {CHAIN_SHOT}_4_gravity_depois.png"]
    return out


CHAIN_TAKEN_4 = (CHAIN_TAKEN_3[0] + ("tallon_overgrown_cavern",), CHAIN_TAKEN_3[1] + ("tallon_transport_chozo_east",))
ENERGY, MAX_ENERGY = HEALTH, "7E09C4"


def chain_round_5(m: dict, room: dict) -> list[str]:
    """Round 5, + the Gravity Suit: the Section C bulkhead climbed underwater with the suit (BULKHEAD_TRY, as
    tallon_gravity); down the sunken frigate, the Reactor Core's wave door opened with a shot; the Cargo Lift's and the
    Hydro Access' Energy Tanks, the Biohazard missile; region E: the Great Tree Chamber (its Space Jump ledge, by
    door_teleport) and Life Grove Tunnel missiles, the Plasma (Chozo South), the Power Bomb (Mines East)."""
    taken = list(chain_taken(*CHAIN_TAKEN_4))
    out = chain_teleports(m, room, ["tallon_transport_chozo_east", "tallon_tunnel_c", "tallon_overgrown_cavern",
                                    "tallon_crash_site", "tallon_frigate_access", "tallon_vent_c"])
    out += ["wait 30"] + BULKHEAD_TRY + [f"expect {ROOM_PTR} {room['tallon_vent_b']}", f"shot {CHAIN_SHOT}_5_vent_b.png"]
    out += chain_teleports(m, room, ["tallon_vent_b", "tallon_vent_a", "tallon_reactor_core"])
    out += chain_beam_door(m, room, "tallon_reactor_core", "tallon_reactor_access", "5_porta_de_onda")

    full = [99]   # energy refilled by RAM to the maximum Samus has (each Energy Tank adds 100)

    def take(key: str, shot: str, n: int | None = None, start: int = -3, after: tuple = ()) -> list[str]:
        n = item_index(key) if n is None else n
        lines = poke16(0x7E09C2, full[0]) + pick_up(n, f"{CHAIN_SHOT}_5_{shot}.png", tuple(taken), start)
        taken.append(n)
        if key in ("tallon_cargo_lift", "tallon_hydro_access"):
            full[0] += 100
        return lines + list(after)

    out += chain_teleports(m, room, ["tallon_reactor_access", "tallon_cargo_lift"])
    out += take("tallon_cargo_lift", "energy_tank_cargo_lift", after=(f"expect {MAX_ENERGY} 00C7",))
    out += chain_teleports(m, room, ["tallon_cargo_lift", "tallon_transit_hall", "tallon_biohazard"])
    out += take("tallon_biohazard", "missil_biohazard", start=-1, after=(f"expect {MAX_MISSILES} 001E",))
    out += chain_teleports(m, room, ["tallon_biohazard", "tallon_security_hall", "tallon_biotech_1", "tallon_conduit_hall",
                                     "tallon_elevator_beta", "tallon_hydro_access"])
    out += take("tallon_hydro_access", "energy_tank_hydro", after=(f"expect {MAX_ENERGY} 012B",))
    out += chain_teleports(m, room, ["tallon_hydro_access", "tallon_great_tree_hall", "tallon_great_tree_chamber"])
    out += take("tallon_great_tree_chamber", "missil_gtc", after=(f"expect {MAX_MISSILES} 0023",))
    out += chain_teleports(m, room, ["tallon_great_tree_chamber", "tallon_great_tree_hall", "tallon_life_grove_tunnel"])
    out += take("tallon_life_grove_tunnel", "missil_lgt", after=(f"expect {MAX_MISSILES} 0028",))
    out += chain_teleports(m, room, ["tallon_life_grove_tunnel", "tallon_great_tree_hall", "tallon_tunnel_d",
                                     "tallon_transport_chozo_south"])
    out += take("tallon_transport_chozo_south", "plasma", lock_item("tallon_transport_chozo_south"),
                after=tuple(has_beams(WAVE_BEAM | ICE_BEAM | PLASMA_BEAM)))
    out += chain_teleports(m, room, ["tallon_transport_chozo_south", "tallon_tunnel_d", "tallon_great_tree_hall",
                                     "tallon_tunnel_e", "tallon_transport_mines_east"])
    out += whole_screen_bg1(MINES_EAST_BG1_OFFSETS)
    return out + take("tallon_transport_mines_east", "power_bomb", lock_item("tallon_transport_mines_east"),
                      after=(f"expect {POWER_BOMBS} 0005", f"expect {MAX_POWER_BOMBS} 0005"))


CHAIN_TAKEN_5 = (CHAIN_TAKEN_4[0] + ("tallon_cargo_lift", "tallon_biohazard", "tallon_hydro_access", "tallon_great_tree_chamber",
                                    "tallon_life_grove_tunnel"),
                 CHAIN_TAKEN_4[1] + ("tallon_transport_chozo_south", "tallon_transport_mines_east"))
CHAIN_ITEMS = MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT | GRAVITY_SUIT | SPACE_JUMP_EQUIPMENT | XRAY_EQUIPMENT   # $09A4 at the end


def chain_round_6(m: dict, room: dict) -> list[str]:
    """Round 6, + the Power Bomb and the Plasma: the Life Grove's hut broken by a power bomb laid in the ball (as
    tallon_power_bomb), the X-Ray; back to the gunship by RAM, the Root Cave climbed again with the Space Jump, the
    plasma door opened with a shot, the Arbor Chamber missile."""
    taken = chain_taken(*CHAIN_TAKEN_5)
    xray, arbor = item_index("tallon_life_grove"), item_index("tallon_arbor_chamber")
    hut = [level_block("tallon_life_grove", x, y) for x, y in power_bomb_hut()]
    out = chain_teleports(m, room, ["tallon_transport_mines_east", "tallon_tunnel_e", "tallon_great_tree_hall",
                                    "tallon_life_grove_tunnel", "tallon_life_grove"])
    out += poke16(0x7E09C2, 299) + whole_screen_bg1() + LIFE_GROVE_TO_HUT
    out += [f"expect {SAMUS_X} {HUT_WEST_X:04X}", item_not_taken_with(xray, taken)]
    out += [f"expect {a:06X} {POWER_BOMB_BLOCK}" for a in hut] + [f"shot {CHAIN_SHOT}_6_cabana.png"]
    out += ["hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_POSE}"]
    out += ["hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0003"]
    out += ["hold X 2", "wait 80", f"shot {CHAIN_SHOT}_6_power_bomb_explodindo.png", "wait 220"]
    out += [f"expect {a:06X} 00FF" for a in hut] + [f"expect {POWER_BOMBS} 0004", f"shot {CHAIN_SHOT}_6_cabana_aberta.png"]
    out += ["hold UP 2", "wait 30", "hold UP 2", "wait 30", f"expect {POSE} {STAND_POSE}"]
    out += ["hold RIGHT 40", "wait 120", f"shot {CHAIN_SHOT}_6_xray.png", "wait 300", "hold A 2", "wait 120", item_taken(xray),
            f"expectbit 7E09A5 {XRAY_EQUIPMENT >> 8:02X}", f"expect {GAME_STATE} 0008"]
    # back to the beam: SELECT through the X-Ray (5) to nothing (0)
    out += ["hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0005", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0000"]
    out += chain_home(room) + chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon",
                                                         "tallon_root_tunnel", "tallon_root_cave"])
    # up the cave again (the same climb as in round 3); on the shelf, walking west, she stops against the plasma door
    out += ROOT_CAVE_CLIMB + ["wait 60"] + beam_door_shut("tallon_root_cave", "tallon_arbor_chamber")
    out += [f"shot {CHAIN_SHOT}_6_porta_de_plasma_fechada.png"]
    out += beam_door_open_and_through(m, room, "tallon_root_cave", "tallon_arbor_chamber", None, "cadeia_6_porta_de_plasma")
    return out + pick_up(arbor, f"{CHAIN_SHOT}_6_missil_arbor.png", taken + (xray,)) + [f"expect {MAX_MISSILES} 002D"]


def chain_end(room: dict) -> list[str]:
    """The 20 item bits ($7ED884: $A0-$AF; $7ED886: $B0-$B3), the items and beams, 45 missiles, 5 power bombs, 299
    energy; saved on the gunship (back there by RAM), game over, continue: all of it comes back."""
    have = [f"expect 7ED884 FFFF", f"expect 7ED886 000F", f"expect {COLLECTED_ITEMS} {CHAIN_ITEMS:04X}"] + has_beams(
        WAVE_BEAM | ICE_BEAM | PLASMA_BEAM) + [f"expect {MAX_MISSILES} 002D", f"expect {MAX_POWER_BOMBS} 0005",
                                               f"expect {MAX_ENERGY} 012B"]
    return (have + chain_home(room) + ["hold UP 2", "wait 60"] + stand_on_tallon_ship()
            + save_on_tallon_ship(f"{CHAIN_SHOT}_fim_save.png", 299)
            + ["poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}"]
            + GAME_OVER_CONTINUE + [f"expect {GAME_STATE} 0008", f"expect {ROOM_PTR} {room[LANDING_SITE]}"] + have
            + equipment_screen(f"{CHAIN_SHOT}_fim_equipamento.png"))


def tallon_full_chain(m: dict, room: dict) -> list[str]:
    return (chain_round_0(m, room) + chain_round_1(m, room) + chain_round_2(m, room) + chain_round_3(m, room)
            + chain_round_4(m, room) + chain_round_5(m, room) + chain_round_6(m, room) + chain_end(room))


def chain_home(room: dict) -> list[str]:
    """Shortcut: back to the gunship by RAM (load station 0 of area 0, as a continue would)."""
    return load_tallon_station(0) + [f"expect {ROOM_PTR} {room[LANDING_SITE]}", f"expect {GAME_STATE} 0008"]


def chain_round_0(m: dict, room: dict) -> list[str]:
    """Round 0, the Power Beam only: the Landing Site's missile (walked to from the ship, tallon_first_missile) and
    the Morph Ball (Chozo West, behind no lock)."""
    morph = item_index("tallon_transport_chozo_west")
    # specs/10a: tallon_first_missile's A now closes the box (it used to come too early: here a second A followed)
    return (tallon_first_missile(f"{CHAIN_SHOT.removeprefix('build/tests/')}_0_missil")
            + ["wait 322", f"shot {CHAIN_SHOT}_0_missil_pego.png"]
            + chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a",
                                        "tallon_transport_chozo_west"])
            + tallon_look(11, 26, 0, 288, f"{CHAIN_SHOT}_0_morph_sala.png")
            + pick_up(morph, f"{CHAIN_SHOT}_0_morph.png", (0,), start=MORPH_START)
            + [f"expect {COLLECTED_ITEMS} {MORPH_BALL_EQUIPMENT:04X}"])


def chain_round_1(m: dict, room: dict) -> list[str]:
    """Round 1, + missiles and the Morph Ball: the three red doors opened with missiles (the Landing Site's 5 for the
    Temple Security's; refilled by RAM to 5 for the Root Tunnel's; the Tunnel B missile's 5 for the Waterfall's);
    the Bombs (Artifact Temple), the Tunnel B missile, the Wave (Magmoor East), the Crash Site missile."""
    morph, bombs = item_index("tallon_transport_chozo_west"), item_index("tallon_artifact_temple")
    tunnel_b, wave = item_index("tallon_tunnel_b"), lock_item("tallon_transport_magmoor_east")
    crash = item_index("tallon_crash_site")
    out = chain_teleports(m, room, ["tallon_transport_chozo_west", "tallon_tunnel_a", "tallon_canyon", "tallon_canyon_cavern",
                                    "tallon_landing_site", "tallon_temple_hall", "tallon_temple_security"])
    out += chain_red_door(room, "tallon_temple_security", "tallon_temple_lobby", "1_porta_vermelha_templo")
    out += chain_teleports(m, room, ["tallon_temple_lobby", "tallon_artifact_temple"])
    out += tallon_look(15, 54, 0, 731, f"{CHAIN_SHOT}_1_bombas_sala.png")
    out += pick_up(bombs, f"{CHAIN_SHOT}_1_bombas.png", (0, morph), start=2, frames=24)
    # back to the gunship by RAM (load station 0): door_teleport up through the Artifact Temple's ceiling door leaves
    # her in the temple (game state $0B, then 8 at its top; measured), and the walk back is the way she came
    out += chain_home(room)
    out += chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_root_tunnel"])
    out += poke16(0x7E09C6, 5) + chain_red_door(room, "tallon_root_tunnel", "tallon_root_cave", "1_porta_vermelha_raizes")
    out += chain_teleports(m, room, ["tallon_root_cave", "tallon_tunnel_b"])
    out += pick_up(tunnel_b, f"{CHAIN_SHOT}_1_missil_tunnel_b.png", (0, morph, bombs)) + [f"expect {MAX_MISSILES} 000A"]
    out += chain_teleports(m, room, ["tallon_tunnel_b", "tallon_transport_magmoor_east"])
    out += pick_up(wave, f"{CHAIN_SHOT}_1_wave.png", (0, morph, bombs, tunnel_b)) + has_beams(WAVE_BEAM)
    out += chain_teleports(m, room, ["tallon_transport_magmoor_east", "tallon_tunnel_b", "tallon_root_cave",
                                     "tallon_root_tunnel", "tallon_canyon", "tallon_canyon_cavern", "tallon_landing_site",
                                     "tallon_waterfall_cavern"])
    out += chain_red_door(room, "tallon_waterfall_cavern", "tallon_crash_site", "1_porta_vermelha_cachoeira")
    out += [f"poke {HEALTH} 63"] + pick_up(crash, f"{CHAIN_SHOT}_1_missil_crash_site.png", (0, morph, bombs, tunnel_b, wave))
    return out + [f"expect {MAX_MISSILES} 000F", f"expect {COLLECTED_ITEMS} {MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT:04X}"]


# spec 09c: a room whose compressed level runs across a bank boundary (only in the test build
# `tools/build.py --cruzar-banco SALA`, or once the level data outgrows a bank): the game's decompressor
# ($80:B119, which moves to the next bank after $xx:FFFF) must give back the room's level. A test per such
# room, from the manifest: get there (frigate: on foot from the new game; Tallon: from the landing, by
# door teleport), read the level in WRAM (layer 1 at $7F:0002, BTS at $7F:6402, sm_82.c:4211) and compare
# with the tool's (only the blocks of the room's PLMs may differ: door caps, items, stations), Samus
# standing still (same y 60 frames apart).
LEVEL_RAM, BTS_RAM = 0x7F0002, 0x7F6402
# specs/12e: the working elevators (tools/areas.py ELEVATORS, tools/build.py): a Tallon transport goes down to its
# Chozo room (area 1) and back up. Samus starts the platform standing on it with the key of its parameter 1 (DOWN /
# UP), after landing on it: elevator_flags ($0E16) turns on when she stands on the platform's door blocks after a fall
# or a walk (not after a RAM placement or a station load: measured, as vanilla), and stays on while she stands on both
# (on one block and a solid one next to it, it is on every other frame only: a press then may miss; vanilla's the same).
ELEVATOR_FLAGS, ELEVATOR_STATUS = "7E0E16", "7E0E18"
SAVED_MAPS = 0x7ECD52   # each area's explored map as saved / as left (0x100 bytes per area; $07F7 = the current one)
ELEVATOR_RIDE = 900     # frames from the press to standing on the other platform (measured: ~600 down, ~540 up)


def built_room(key: str):
    return {r.key: r for _, r in all_rooms()}[key]


def map_tile(key: str, sx: int, sy: int) -> tuple[int, int]:
    r = built_room(key)
    return r.map_x + sx, r.map_y + sy + 1


def explored_at(key: str, sx: int, sy: int, saved_area: int | None = None) -> str:
    """`expectbit` for a room screen's explored bit: in the current area's map ($07F7) or in area `saved_area`'s saved
    copy ($7ECD52 + area * $100)."""
    byte, mask = pausemap.bit(*map_tile(key, sx, sy))
    base = EXPLORED_TILES if saved_area is None else SAVED_MAPS + 0x100 * saved_area
    return f"expectbit {base + byte:06X} {mask:02X}"


def platform_screen(key: str) -> tuple[int, int]:
    e = built_room(key).elevator
    return (e.x + 1) // 16, e.row // 16


def onto_platform(key: str) -> list[str]:
    """Shortcut: Samus put by RAM on the middle of room `key`'s elevator platform (camera on its screen), placed twice
    to stop a run (pausing and unpausing redraws the screen after the camera's jump, for the photos); then 4 frames right
    and 4 left (back on the middle, measured): walking on it turns elevator_flags on (a jump in place doesn't: put by RAM
    she faces the screen, $0A1C = $9B, and A does nothing then)."""
    r = built_room(key)
    e = r.elevator
    x, y = (e.x + 1) * 16, e.row * 16 - 21
    place = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y)):
        place += poke16(addr, v)
    sx, sy = platform_screen(key)
    camera = poke16(0x7E0911, sx * 256) + poke16(0x7E0915, min(sy * 256, camera_bottom(r)))
    return (place + ["wait 30"] + place + camera + ["wait 4", "hold START 10", "wait 200", "hold START 10", "wait 200",
                                                     "hold RIGHT 4", "hold LEFT 4", "wait 30",
                                                     f"expect {ELEVATOR_FLAGS} 0001", f"expect 7E0AF6 {x:04X}"])


def ride_elevator(room: dict, key: str, shot: str) -> list[str]:
    """Press the key of room `key`'s elevator (DOWN / UP): it starts ($0E18 = 1); ELEVATOR_RIDE frames later Samus stands
    on the other room's platform (tools/areas.py ELEVATORS), in that room's area ($079F), the ride over ($0E18 = 0),
    where the platform put her (its y - 26). `shot`: a photo on the way (50 frames into a ride down, going into the
    shaft; 230 into a ride up, in the Chozo's shaft: the fade between the rooms is black)."""
    from areas import elevator_target
    to = elevator_target(key)
    area = next(a for a, r in all_rooms() if r.key == to)
    e = built_room(to).elevator
    return [f"hold {'UP' if built_room(key).elevator.up else 'DOWN'} 1", "wait 30", f"expect {ELEVATOR_STATUS} 0001",
            f"wait {200 if built_room(key).elevator.up else 20}", f"shot {shot}",
            f"wait {ELEVATOR_RIDE - 30 - (200 if built_room(key).elevator.up else 20)}", f"expect {ROOM_PTR} {room[to]}",
            f"expect {AREA} {area.number:04X}", f"expect {ELEVATOR_STATUS} 0000", f"expect {GAME_STATE} 0008",
            f"expect 7E0AF6 {(e.x + 1) * 16:04X}", f"expect 7E0AFA {e.row * 16 + 2 - 26:04X}"]


def pause_shows(area, screens, tag: str) -> list[str]:
    """While paused (VRAM, as tallon_pause_shows): those screens of `area` show its tilemap's tile (explored), a tile
    outside every built room of it is blank, and the name is the area's."""
    def vram_line(addr: int, data: bytes, name: str) -> str:
        path = WORK / f"vram_{tag}_{name}.bin"
        path.write_bytes(data)
        return f"expectvram {addr:04X} {path.relative_to(ROOT)}"

    # specs/19l: (30, 20) is the Fungal Hall A's in the whole Mines: the Mines' blank tile is (30, 26), under every room of it;
    # specs/20g: area 0's is TALLON_BLANK (30, 20 is the Subchamber Three's)
    blank = (30, 26) if area is MINES else TALLON_BLANK if area is TALLON else (30, 20)
    assert all(blank not in {(tx, ty) for *_, tx, ty in pausemap.cells(r)}
               for r in [*area.rooms, *(impact_rooms.ALL_ROOMS if area is TALLON else ())])
    by = area.by_key()
    tiles = [(map_tile(k, sx, sy), pausemap.room_tile(by[k], sx, sy) & 0xFBFF) for k, sx, sy in screens]
    out = [vram_line(PAUSE_MAP_VRAM + pausemap.tile_index(tx, ty), struct.pack("<H", w), f"{tx}_{ty}")
           for (tx, ty), w in tiles + [(blank, pausemap.BLANK)]]
    return out + [vram_line(PAUSE_NAME_VRAM, area_label(area.name), "nome")]


IMG_12E = "build/tests/12e"   # the photos of the elevator tests (specs/img/12e-* are copies of some)
# specs/12e: the sandstone in a real Chozo room: palette line 7 of the WRAM palette ($7EC000 + 2 * (16 * 7 + i)) =
# ruins.SANDSTONE (the room has no FX: no palette change by area, unlike the Maridia room of the 12d photo)
SANDSTONE_RAM = [f"expect {0x7EC000 + 2 * (16 * ruins.PALETTE_LINE + i):06X} {ruins._bgr555(c):04X}"
                 for i, c in enumerate(ruins.SANDSTONE, start=1)]
WEST, NORTH = "tallon_transport_chozo_west", "chozo_transport_tallon_north"


def elevator_round_trip(m: dict, room: dict) -> list[str]:
    """specs/12e, elevador_chozo_ida_e_volta: from the landing (a real Tallon game), to the Chozo West (door_teleport
    through the round-0 rooms: the walk there is tallon_rota_mvp's), onto its platform (onto_platform: shortcut), DOWN:
    the Chozo's North transport, area 1; the Tallon room's explored bit went to area 0's saved copy and the Chozo room's
    is on in the current map; paused, the map is the Chozo's ("CHOZO", its room's tile); UP from its platform: back in
    the Chozo West, area 0, the Chozo room's bit in area 1's saved copy. Back to the ship (door_teleport), saved there,
    game over, continue: the Landing Site, area 0, both areas' explored bits kept (the SRAM's area 1 list, specs/12b)."""
    sx, sy = platform_screen(NORTH)
    wx, wy = platform_screen(WEST)
    return (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
            + onto_platform(WEST) + [f"shot {IMG_12E}_tallon_plataforma.png", explored_at(WEST, wx, wy)]
            + ride_elevator(room, WEST, f"{IMG_12E}_descendo.png")
            + [f"shot {IMG_12E}_chozo_chegada.png", explored_at(NORTH, sx, sy), explored_at(WEST, wx, wy, TALLON.number)]
            + SANDSTONE_RAM
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(CHOZO, [(NORTH, sx, sy)], "chozo") + [f"shot {IMG_12E}_chozo_mapa.png",
                                                               "hold START 10", "wait 200", f"expect {GAME_STATE} 0008"]
            + onto_platform(NORTH) + ride_elevator(room, NORTH, f"{IMG_12E}_subindo.png")
            + [f"shot {IMG_12E}_tallon_volta.png", explored_at(WEST, wx, wy), explored_at(NORTH, sx, sy, CHOZO.number)]
            + chain_teleports(m, room, [WEST, "tallon_tunnel_a", "tallon_canyon", "tallon_canyon_cavern", "tallon_landing_site"])
            + stand_on_tallon_ship() + ["hold UP 2", "wait 60"] + stand_on_tallon_ship()
            + save_on_tallon_ship(f"{IMG_12E}_save.png")
            + ["poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}"]
            + GAME_OVER_CONTINUE
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0000", f"expect {ROOM_PTR} {room[LANDING_SITE]}",
               explored_at(WEST, wx, wy), explored_at(NORTH, sx, sy, CHOZO.number), f"shot {IMG_12E}_continue.png"])


def elevator_east_and_south(m: dict, room: dict) -> list[str]:
    """specs/12e, elevador_chozo_east_e_south: the other two, down and back up. Shortcuts: each Tallon room by
    door_teleport (Tunnel C -> Chozo East: behind the ice door, round 4; Tunnel D -> Chozo South: round 5), Samus put
    on the platform (onto_platform); the Gravity Suit and the Plasma stay where they are (not on the way)."""
    out = []
    for tallon_key, chozo_key, tunnel, tag in (("tallon_transport_chozo_east", "chozo_transport_tallon_east", "tallon_tunnel_c", "east"),
                                               ("tallon_transport_chozo_south", "chozo_transport_tallon_south", "tallon_tunnel_d", "south")):
        out += (poke16(0x7E0911, 0) + ["wait 2"] + door_teleport(m, tunnel, tallon_key) + [f"expect {ROOM_PTR} {room[tallon_key]}"]
                + onto_platform(tallon_key) + [f"shot {IMG_12E}_{tag}_tallon.png"]
                + ride_elevator(room, tallon_key, f"{IMG_12E}_{tag}_descendo.png") + [f"shot {IMG_12E}_{tag}_chozo.png"]
                + onto_platform(chozo_key) + ride_elevator(room, chozo_key, f"{IMG_12E}_{tag}_subindo.png")
                + [f"shot {IMG_12E}_{tag}_volta.png"])
    return out


# specs/17e: the two elevators to the Magmoor Caverns (area 2): the Chozo's P24 down to the Magmoor's P0, the Tallon's P23 down
# to the Magmoor's P16 (2x1, one screen high: its shaft is 10 rows), and back up; the Magmoor's map, save and continue
IMG_17E = "build/tests/17e"
MAGMOOR_FROM_CHOZO, CHOZO_TO_MAGMOOR = "magmoor_transport_chozo_north", "chozo_transport_magmoor_north"
MAGMOOR_FROM_TALLON, TALLON_TO_MAGMOOR = "magmoor_transport_tallon_west", "tallon_transport_magmoor_east"
USED_STATIONS_AREA2 = f"{0x7ED8F8 + 2 * 2:06X}"   # $7ED8FC


def magmoor_round_trip(m: dict, room: dict) -> list[str]:
    """specs/17e, elevador_magmoor_ida_e_volta: from the landing, down the Chozo West elevator (as elevador_chozo_ida_e_volta),
    to the Chozo's Magmoor North transport (door_teleport from the Vault Access: shortcut), onto its platform (onto_platform),
    DOWN: the Magmoor's P0, area 2, standing on its platform; the Chozo room's explored bit went to area 1's saved copy and
    the Magmoor room's is on; the Magmoor's palette (lava.COLOURS_COOL, line 4 in WRAM); paused, the map is the Magmoor's
    ("MAGMOOR", its room's tile); UP: back in the Chozo, area 1, the Magmoor room's bit in area 2's saved copy. Back up the
    West elevator to the Tallon and the ship (door_teleport), the Magmoor's used-station bit put by RAM (shortcut: its save
    stations come with region A, 17f; the area-select screen draws an area's name only with a used station), saved there,
    game over: the area-select screen draws "MAGMOOR / CAVERNS" (its first letter in the OAM at its place, check_magmoor_label);
    continue: the Landing Site, area 0, all three areas' explored bits kept (the SRAM's area 2 list)."""
    from smlib import lava
    sx, sy = platform_screen(MAGMOOR_FROM_CHOZO)
    cx, cy = platform_screen(CHOZO_TO_MAGMOOR)
    wx, wy = platform_screen(WEST)
    cool = [f"expect {0x7EC000 + 2 * (16 * line + i):06X} {lava._bgr555(c):04X}" for (line, i), c in lava.COLOURS_COOL.items()
            if line == lava.PALETTE_LINE]
    return (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
            + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_17E}_chozo_descendo.png")
            + door_teleport(m, "chozo_vault_access", CHOZO_TO_MAGMOOR) + [f"expect {ROOM_PTR} {room[CHOZO_TO_MAGMOOR]}"]
            + onto_platform(CHOZO_TO_MAGMOOR) + [f"shot {IMG_17E}_chozo_plataforma.png"]
            + ride_elevator(room, CHOZO_TO_MAGMOOR, f"{IMG_17E}_descendo.png")
            + [f"shot {IMG_17E}_magmoor_chegada.png", explored_at(MAGMOOR_FROM_CHOZO, sx, sy),
               explored_at(CHOZO_TO_MAGMOOR, cx, cy, CHOZO.number)] + cool
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(MAGMOOR, [(MAGMOOR_FROM_CHOZO, sx, sy)], "magmoor") + [f"shot {IMG_17E}_magmoor_mapa.png",
                                                                             "hold START 10", "wait 200", f"expect {GAME_STATE} 0008"]
            + onto_platform(MAGMOOR_FROM_CHOZO) + ride_elevator(room, MAGMOOR_FROM_CHOZO, f"{IMG_17E}_subindo.png")
            + [f"shot {IMG_17E}_chozo_volta.png", explored_at(CHOZO_TO_MAGMOOR, cx, cy),
               explored_at(MAGMOOR_FROM_CHOZO, sx, sy, MAGMOOR.number)]
            + door_teleport(m, "chozo_ruins_entrance", NORTH) + [f"expect {ROOM_PTR} {room[NORTH]}"]
            + onto_platform(NORTH) + ride_elevator(room, NORTH, f"{IMG_17E}_tallon_subindo.png")
            + chain_teleports(m, room, [WEST, "tallon_tunnel_a", "tallon_canyon", "tallon_canyon_cavern", "tallon_landing_site"])
            + stand_on_tallon_ship() + ["hold UP 2", "wait 60"] + stand_on_tallon_ship()
            + [f"poke {USED_STATIONS_AREA2} 01"] + save_on_tallon_ship(f"{IMG_17E}_save.png")
            + ["poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}"]
            + ["hold A 2", "wait 300", f"expect {GAME_STATE} {FILE_SELECT_MAP}", f"expect 7E0727 {AREA_SELECT_STEP}",
               f"peek {OAM_BUFFER:06X} 512", f"shot {IMG_17E}_continue_nomes.png"]
            + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0000", f"expect {ROOM_PTR} {room[LANDING_SITE]}",
               explored_at(WEST, wx, wy), explored_at(CHOZO_TO_MAGMOOR, cx, cy, CHOZO.number),
               explored_at(MAGMOOR_FROM_CHOZO, sx, sy, MAGMOOR.number), f"shot {IMG_17E}_continue.png"])


def check_magmoor_label(stdout: str) -> list[str]:
    """specs/17e: in the OAM dump of the area-select screen (magmoor_round_trip), the first letter of "MAGMOOR / CAVERNS" at its
    place (areaselect.LABELS[2]: x, y and the small letter's tile; drawn in the unselected areas' palette)."""
    _, _, _, lines, (bx, by) = areaselect.LABELS[2]
    x, y, tile = areaselect.label_pieces(lines)[0]
    want = bytes([(bx + x) & 0xFF, (by + y) & 0xFF, tile & 0xFF])   # x, y, tile (the palette shows the area unselected)
    dumps = re.findall(rf"{OAM_BUFFER:06X}:((?: [0-9A-F]{{2}})+)", stdout)
    if not dumps:
        return ["FAIL tela de área: OAM não lida"]
    oam = bytes(int(v, 16) for v in dumps[-1].split())
    if not any(oam[i:i + 3] == want for i in range(0, len(oam), 4)):
        return [f"FAIL tela de área: o M de MAGMOOR ({want.hex()}) não está na OAM"]
    return []


def check_phendrana_label(stdout: str) -> list[str]:
    """specs/18e: in the OAM dump of the area-select screen (phendrana_north_elevator), the first letter of "PHENDRANA / DRIFTS"
    at its place (areaselect.LABELS[4]), as check_magmoor_label."""
    _, _, _, lines, (bx, by) = areaselect.LABELS[4]
    x, y, tile = areaselect.label_pieces(lines)[0]
    want = bytes([(bx + x) & 0xFF, (by + y) & 0xFF, tile & 0xFF])
    dumps = re.findall(rf"{OAM_BUFFER:06X}:((?: [0-9A-F]{{2}})+)", stdout)
    if not dumps:
        return ["FAIL tela de área: OAM não lida"]
    oam = bytes(int(v, 16) for v in dumps[-1].split())
    if not any(oam[i:i + 3] == want for i in range(0, len(oam), 4)):
        return [f"FAIL tela de área: o P de PHENDRANA ({want.hex()}) não está na OAM"]
    return []


# specs/18e: the Magmoor's two lifts up to Phendrana Drifts (area 4): its P13 up to Phendrana's P0 (the snow look, falling snow),
# its P27 up to Phendrana's P29 (the icy ruins' look), and back down; Phendrana's map, save and continue
IMG_18E = "build/tests/18e"
PHENDRANA_NORTH, MAGMOOR_TO_NORTH = "phendrana_transport_magmoor_west", "magmoor_transport_phendrana_north"
PHENDRANA_SOUTH, MAGMOOR_TO_SOUTH = "phendrana_transport_magmoor_south", "magmoor_transport_phendrana_south"
USED_STATIONS_AREA4 = f"{0x7ED8F8 + 2 * 4:06X}"   # $7ED900


def to_magmoor_p16(m: dict, room: dict) -> list[str]:
    """From the landing: to the Tallon's Magmoor East transport (door_teleport from the Tunnel B: a shortcut, as
    elevador_magmoor_tallon), onto its platform, down to the Magmoor's P16 (area 2)."""
    return (door_teleport(m, "tallon_tunnel_b", TALLON_TO_MAGMOOR) + [f"expect {ROOM_PTR} {room[TALLON_TO_MAGMOOR]}"]
            + onto_platform(TALLON_TO_MAGMOOR) + ride_elevator(room, TALLON_TO_MAGMOOR, f"{IMG_18E}_tallon_descendo.png"))


def phendrana_ride(m: dict, room: dict, via: str, lift: str, top: str, tag: str, look: list[str]) -> list[str]:
    """In the Magmoor (area 2): to the lift `lift` (door_teleport from its neighbour `via`: round 3's rooms, a shortcut), onto
    its platform, UP: Phendrana's room `top`, area 4, standing on its platform (ride_elevator), its explored bit on and the
    Magmoor room's in area 2's saved copy, the look's colours (`look`: expects); paused, Phendrana's map ("PHENDRANA", its room's
    tile; photo: the whole map, area 4's scroll of 24 px more, sm_82.c:1811); DOWN from its platform: back in the Magmoor,
    Phendrana's room's bit in area 4's saved copy."""
    sx, sy = platform_screen(top)
    mx, my = platform_screen(lift)
    return (door_teleport(m, via, lift) + [f"expect {ROOM_PTR} {room[lift]}"]
            + onto_platform(lift) + [f"shot {IMG_18E}_{tag}_magmoor_plataforma.png"]
            + ride_elevator(room, lift, f"{IMG_18E}_{tag}_subindo.png")
            + [f"shot {IMG_18E}_{tag}_chegada.png", explored_at(top, sx, sy), explored_at(lift, mx, my, MAGMOOR.number)] + look
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(PHENDRANA, [(top, sx, sy)], f"phendrana_{tag}") + [f"shot {IMG_18E}_{tag}_mapa.png",
                                                                             "hold START 10", "wait 200", f"expect {GAME_STATE} 0008"]
            + onto_platform(top) + [f"shot {IMG_18E}_{tag}_plataforma.png"]
            + ride_elevator(room, top, f"{IMG_18E}_{tag}_descendo.png")
            + [f"shot {IMG_18E}_{tag}_volta.png", explored_at(lift, mx, my), explored_at(top, sx, sy, PHENDRANA.number)])


def phendrana_north_elevator(m: dict, room: dict) -> list[str]:
    """specs/18e, elevador_phendrana_norte: from the landing down to the Magmoor's P16 (to_magmoor_p16), to its P13 and up to
    Phendrana's P0 (phendrana_ride: the snow FX, $196E = 8, and the snow look's line 4 in WRAM), back down; up the P16's lift to
    the Tallon and the ship (door_teleport), Phendrana's used-station bit put by RAM (its save stations come with region A, 18f),
    saved there, game over: the area-select screen draws "PHENDRANA / DRIFTS" (check_phendrana_label); continue: the Landing
    Site, area 0, the explored bits of the Tallon, the Magmoor and Phendrana kept (the SRAM's area 4 list)."""
    from smlib import ice
    sx, sy = platform_screen(PHENDRANA_NORTH)
    mx, my = platform_screen(MAGMOOR_TO_NORTH)
    snow = [f"expect {WATER_FX_TYPE} 0008"] + palette_expect(4, ice.SNOW_COLOURS)
    return (to_magmoor_p16(m, room)
            + phendrana_ride(m, room, "magmoor_transport_tunnel_a", MAGMOOR_TO_NORTH, PHENDRANA_NORTH, "norte", snow)
            + door_teleport(m, "magmoor_transport_tunnel_b", MAGMOOR_FROM_TALLON) + [f"expect {ROOM_PTR} {room[MAGMOOR_FROM_TALLON]}"]
            + onto_platform(MAGMOOR_FROM_TALLON) + ride_elevator(room, MAGMOOR_FROM_TALLON, f"{IMG_18E}_tallon_subindo.png")
            + chain_teleports(m, room, tallon_door_path(TALLON_TO_MAGMOOR, LANDING_SITE))
            + stand_on_tallon_ship() + ["hold UP 2", "wait 60"] + stand_on_tallon_ship()
            + [f"poke {USED_STATIONS_AREA4} 01"] + save_on_tallon_ship(f"{IMG_18E}_save.png")
            + ["poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}"]
            + ["hold A 2", "wait 300", f"expect {GAME_STATE} {FILE_SELECT_MAP}", f"expect 7E0727 {AREA_SELECT_STEP}",
               f"peek {OAM_BUFFER:06X} 512", f"shot {IMG_18E}_continue_nomes.png"]
            + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0000", f"expect {ROOM_PTR} {room[LANDING_SITE]}",
               explored_at(MAGMOOR_TO_NORTH, mx, my, MAGMOOR.number), explored_at(PHENDRANA_NORTH, sx, sy, PHENDRANA.number),
               f"shot {IMG_18E}_continue.png"])


def phendrana_south_elevator(m: dict, room: dict) -> list[str]:
    """specs/18e, elevador_phendrana_sul: from the landing down to the Magmoor's P16, to its P27 and up to Phendrana's P29
    (phendrana_ride: no FX, the icy ruins' line 7 in WRAM), back down."""
    from smlib import ice
    ruins_look = [f"expect {WATER_FX_TYPE} 0000"] + palette_expect(7, ice.RUINS_COLOURS)
    return (to_magmoor_p16(m, room)
            + phendrana_ride(m, room, "magmoor_transport_tunnel_c", MAGMOOR_TO_SOUTH, PHENDRANA_SOUTH, "sul", ruins_look))


# specs/19e: the two elevators down to the Phazon Mines (area 5): the Tallon's P43 down to the Mines' P0, the Magmoor's P26 down to
# its P25 (3 screens tall: the longest shaft), and back up; the Mines' look (the pirate base, smlib/mines.py) in WRAM, its map
# ("MINES", its explored-map list in $81: specs/19b), save, game over and continue with the five areas' names
IMG_19E = "build/tests/19e"
MINES_EAST, TALLON_TO_MINES = "mines_transport_tallon_south", "tallon_transport_mines_east"
MINES_WEST, MAGMOOR_TO_MINES = "mines_transport_magmoor_south", "magmoor_transport_mines_west"
USED_STATIONS_AREA5 = f"{0x7ED8F8 + 2 * 5:06X}"   # $7ED902
FIVE_AREAS = (0, 5, 1, 4, 2)   # the area-select screen's order of the five worlds (0, 3, 5, 1, 4, 2 without the frigate)


def mines_look() -> list[str]:
    """The Mines' pirate base in the room (specs/19d): no FX ($196E), the look's colours (lines 5-6) and the purple of the paint
    line in the WRAM palette, Tourian's music (song set and track)."""
    from smlib import mines
    from tallon import beamdoors
    ts = mines.BASE_TILESET
    return ([f"expect {WATER_FX_TYPE} 0000"]
            + [f"expect {0x7EC000 + 2 * (ln * 16 + i):06X} {mines._bgr555(c):04X}" for (ln, i), c in mines.COLOURS[ts].items()]
            + [f"expect {0x7EC000 + 2 * (mines.PAINT_LINES[ts] * 16 + i):06X} {c:04X}" for i, c in enumerate(beamdoors.PURPLE, 1)]
            + [f"expect 7E07F3 {mines.MUSIC[0]:04X}", f"expect 7E07F5 {mines.MUSIC[1]:04X}"])


def mines_ride(room: dict, lift: str, low: str, area, tag: str) -> list[str]:
    """In room `lift` (the Tallon's or the Magmoor's, area `area`): onto its platform, DOWN: the Mines' room `low`, area 5, standing
    on its platform (ride_elevator), its explored bit on and `lift`'s in `area`'s saved copy, the pirate base's look (mines_look);
    paused, the Mines' map ("MINES", its room's tile); UP from its platform: back in `lift`, `low`'s bit in area 5's saved copy."""
    sx, sy = platform_screen(low)
    mx, my = platform_screen(lift)
    return (onto_platform(lift) + [f"shot {IMG_19E}_{tag}_plataforma.png", explored_at(lift, mx, my)]
            + ride_elevator(room, lift, f"{IMG_19E}_{tag}_descendo.png")
            + [f"shot {IMG_19E}_{tag}_chegada.png", explored_at(low, sx, sy), explored_at(lift, mx, my, area.number)]
            + mines_look()
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(MINES, [(low, sx, sy)], f"mines_{tag}") + [f"shot {IMG_19E}_{tag}_mapa.png",
                                                                    "hold START 10", "wait 200", f"expect {GAME_STATE} 0008"]
            + onto_platform(low) + [f"shot {IMG_19E}_{tag}_mina_plataforma.png"]
            + ride_elevator(room, low, f"{IMG_19E}_{tag}_subindo.png")
            + [f"shot {IMG_19E}_{tag}_volta.png", explored_at(lift, mx, my), explored_at(low, sx, sy, MINES.number)])


def mines_east_elevator(m: dict, room: dict) -> list[str]:
    """specs/19e, elevador_mines_leste: from the landing to the Tallon's P43 (door_teleport from the Tunnel E, as
    elevador_chozo_east_e_south: a shortcut, its round-5 ice doors not opened), down to the Mines' P0 and back up (mines_ride); back to the ship (door_teleport), a used station put by RAM
    in each of the other four worlds (the Mines', the Chozo's, the Magmoor's, Phendrana's: station 0, their arrivals), saved there,
    game over: the area-select screen draws the five names, "TALLON / OVERWORLD", "PHAZON / MINES", "CHOZO / RUINS", "PHENDRANA /
    DRIFTS", "MAGMOOR / CAVERNS" (check_five_labels); continue: the Landing Site, area 0, the explored bits of the Tallon and the
    Mines kept (area 5's list in $81, the SRAM)."""
    sx, sy = platform_screen(MINES_EAST)
    tx, ty = platform_screen(TALLON_TO_MINES)
    used = [f"poke {0x7ED8F8 + 2 * a:06X} 01" for a in FIVE_AREAS[1:]]
    return (poke16(0x7E0911, 0) + ["wait 2"] + door_teleport(m, "tallon_tunnel_e", TALLON_TO_MINES)
            + [f"expect {ROOM_PTR} {room[TALLON_TO_MINES]}"]
            + mines_ride(room, TALLON_TO_MINES, MINES_EAST, TALLON, "leste")
            + chain_teleports(m, room, tallon_door_path(TALLON_TO_MINES, LANDING_SITE))
            + stand_on_tallon_ship() + ["hold UP 2", "wait 60"] + stand_on_tallon_ship()
            + used + save_on_tallon_ship(f"{IMG_19E}_save.png")
            + ["poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}"]
            + ["hold A 2", "wait 300", f"expect {GAME_STATE} {FILE_SELECT_MAP}", f"expect 7E0727 {AREA_SELECT_STEP}",
               f"expect {AREA} 0000", f"peek {OAM_BUFFER:06X} 512", f"shot {IMG_19E}_continue_nomes.png"]
            + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0000", f"expect {ROOM_PTR} {room[LANDING_SITE]}",
               explored_at(TALLON_TO_MINES, tx, ty), explored_at(MINES_EAST, sx, sy, MINES.number),
               f"shot {IMG_19E}_continue.png"])


def mines_west_elevator(m: dict, room: dict) -> list[str]:
    """specs/19e, elevador_mines_oeste: from the landing down to the Magmoor's P16 (to_magmoor_p16), to its P26 (door_teleport: a
    shortcut, its round-4 ice doors not opened), down to the Mines' P25 (the 3-screen shaft) and back up (mines_ride)."""
    return (to_magmoor_p16(m, room) + door_teleport(m, "magmoor_workstation_tunnel", MAGMOOR_TO_MINES)
            + [f"expect {ROOM_PTR} {room[MAGMOOR_TO_MINES]}"]
            + mines_ride(room, MAGMOOR_TO_MINES, MINES_WEST, MAGMOOR, "oeste"))


def check_five_labels(stdout: str) -> list[str]:
    """specs/19e: in the OAM dump of the area-select screen (elevador_mines_leste), right after the title's sprites, the five worlds'
    names in the game's order (FIVE_AREAS: each with a used station), each piece at its place (areaselect.LABELS: x, y, tile)."""
    dumps = re.findall(rf"{OAM_BUFFER:06X}:((?: [0-9A-F]{{2}})+)", stdout)
    if not dumps:
        return ["FAIL tela de área: OAM não lida"]
    oam = bytes(int(v, 16) for v in dumps[-1].split())
    at = len(areaselect.title_pieces(areaselect.TITLE))
    out = []
    for a in FIVE_AREAS:
        _, _, _, lines, (bx, by) = areaselect.LABELS[a]
        for x, y, tile in areaselect.label_pieces(lines):
            want = bytes([(bx + x) & 0xFF, (by + y) & 0xFF, tile & 0xFF])
            if oam[4 * at:4 * at + 3] != want:
                out.append(f"FAIL tela de área: peça {at} da OAM = {oam[4 * at:4 * at + 3].hex()}, esperado {want.hex()} "
                           f"({'/'.join(lines)})")
                return out
            at += 1
    return out


# specs/18f: region A of Phendrana (tools/phendrana/layouts.py, items.py; item bits $DA-$DD). The walks are measured in the
# emulator (scratchpad s18f/scripts: mv.py runs MAGMOOR_MOVES strings, hopx.py searches the walk frames before each jump as
# 17f's chain.py, the middle of the window taken): no damage, the energy 99 the whole way. specs/18g: with the enemies
# (tools/phendrana/enemies.py) the walks past them were searched again (P18G_*, and P18F_TOWER_OFF, P18F_ACCESS, P18F_RUINS_DOWN). The gear of round 3
# by RAM: the Varia Suit, the Space Jump, the Morph Ball, the Bombs, the Wave Beam; 10 missiles.
IMG_18G = "build/tests/18g"   # specs/18g: the photos of the enemies (specs/img/18g-* are copies of some)
IMG_18F = "build/tests/18f"   # the photos of the region A tests (specs/img/18f-* are copies of some)
P18G_OVERHANG_ZEELA = "cc"   # specs/18g: on the overhang, two shots crouching at its Zeela (the room's 3 are back: a new visit)
P18G_SHORE_ZEELA = "cc"   # specs/18g: from the Shorelines' L1, two shots crouching at the west Zeela coming along the beach
P18F_P0_OUT = ["hold RIGHT+X 2", "hold RIGHT 60", "hold RIGHT+X 2", "hold RIGHT 120", "wait 200"]   # the P0's platform to its door
P18F_ENTRANCE = "RRRRRxRRRRRRRRxRRRRRRD"   # the Shoreline Entrance over its two drifts into the Shorelines' L1
SPACE_JUMP_UP = {d: ["hold " + d + "+A 30", "hold " + d + " 16"] for d in ("LEFT", "RIGHT")}   # one spin of the Space Jump
P18F_DISMISS = ["wait 300", "hold A 2", "wait 120"]   # the item's message box
# the Shorelines' beach: east into the frozen lake's hole (its missile); out east, past the tower's arch; west up the Space Jump
# onto the tower's top (feet row 8) and east into its missile; east over the stump, off the tower and into the floor door (B4)
P18F_LAKE = "RRRRRRRRRRRRR"
P18F_TOWER = "xRRRRR"
P18F_TOWER_OFF = "xgXcRggR"   # specs/18g (beam search, s18g/scripts/srch.py): the beach's Zeela shot crouching on the way (was "xRRRRRRRRRR")
# the Ice Ruins Access from its ceiling door's platform east to its R0; the Ice Ruins East off the L0 shelf down to its floor,
# west into the ice niche (its missile), east to the tower's foot, back, the Space Jump east onto the tower (its missile)
P18F_ACCESS = "RxaasRRxrraas"   # specs/18g (beam search): its 2 orbs shot up and ahead as they come, then "DD" to the R0 (was 20 R and D)
P18F_RUINS_DOWN, P18F_NICHE, P18F_TOWER_FOOT = "RRRRRRRRXcLc", "LLLLLLLLLLL", "RRRRRRRRR"   # specs/18g: down the zigzag, the 2 Zeelas shot crouching on the floor (was 12 R; the niche's wall stops the walk west the same)
# from the tower's top west down (the Space Jump against the stump: she falls) to the floor; up the zigzag (21 west, 16 east,
# 11 west) onto the T0 door's platform (row 6), a jump up into the Plaza Walkway (she lands on the floor door's east ledge, row
# 13); into the Temple Entryway she lands there held east as she rises (P18F_RISE_EAST)
P18F_RUINS_CLIMB = [("LEFT", [(39, 30, 40)]), ("RIGHT", [(11, 30, -60)]), ("LEFT", [(10, 30, -60), (22, 30, -60)])]
P18F_RISE = ["wait 5", "hold A 30", "wait 200"]
P18F_RISE_EAST = ["wait 5", "hold A 30", "wait 120", "hold RIGHT 30", "wait 60"]
# the Plaza Walkway west over the floor door's hole, along it and up the step into the Shorelines' R1
P18F_PLAZA = "LLLLLLLLyLLE"
# the Shorelines from the R1: west into the basin (east of the floor door's hole), over the hole, out of the basin; up the east
# zigzag (21 east, 16 west, 11 east) onto the overhang (row 10), east into the Ruins Entryway's L1
P18F_BASIN = [(18, 30, -60), (23, 30, -60)]
P18F_EAST_CLIMB = [("RIGHT", [(14, 30, -60)]), ("LEFT", [(9, 30, -60)]), ("RIGHT", [(12, 30, -60), (15, 30, -60)])]
# the Ruins Entryway up its zigzag (21 east, 16 west, 11 east) onto the shelf (row 10) and east to the R0's wall (region B)
P18F_RUINS_ENTRY_CLIMB = [("RIGHT", [(13, 30, -60)]), ("LEFT", [(9, 30, -60)]), ("RIGHT", [(12, 30, -60), (15, 30, -60)])]
# the Shorelines' west zigzag from the beach (21 west, 16 east, 11 west) onto the cliff (row 10: the L0 shelf); onto the T0
# door's platform (row 6)
P18F_WEST_CLIMB = [("LEFT", [(21, 30, -60)]), ("RIGHT", [(6, 30, -60)]), ("LEFT", [(12, 30, -60), (11, 30, -60)])]
P18F_TO_PLATFORM = ["hold RIGHT 20", "wait 10"] + ["hold LEFT 10", "hold LEFT+A 30", "wait 60"]
# the Chozo Ice Temple from the R1: west under the east cliff, up its zigzag (21 east, 16 west, 11 east) onto the shelf (row
# 10) against the ice wall; the ball, a bomb on the bomb block, rolling east through the tunnel into the R0 door's chamber
P18F_TEMPLE_CLIMB = [("RIGHT", [(16, 30, -60)]), ("LEFT", [(4, 30, -60)]), ("RIGHT", [(12, 30, -60), (15, 30, -60)])]
PHENDRANA_A_SCREENS = [("phendrana_transport_magmoor_west", 1, 1), ("phendrana_shoreline_entrance", 0, 0),
                       ("phendrana_shoreline_entrance", 3, 0), ("phendrana_shorelines", 0, 1), ("phendrana_shorelines", 2, 1),
                       ("phendrana_shorelines", 2, 0), ("phendrana_shorelines", 4, 1), ("phendrana_ice_ruins_access", 0, 0),
                       ("phendrana_ice_ruins_access", 2, 0), ("phendrana_ice_ruins_east", 0, 0),
                       ("phendrana_ice_ruins_east", 0, 1), ("phendrana_ice_ruins_east", 2, 0),
                       ("phendrana_plaza_walkway", 1, 0), ("phendrana_plaza_walkway", 0, 0), ("phendrana_shorelines", 5, 1),
                       ("phendrana_shorelines", 5, 0), ("phendrana_ruins_entryway", 0, 1), ("phendrana_ruins_entryway", 2, 0)]
PHENDRANA_TEMPLE_SCREENS = [("phendrana_shorelines", 0, 0), ("phendrana_temple_entryway", 0, 0),
                            ("phendrana_chozo_ice_temple", 4, 1), ("phendrana_chozo_ice_temple", 4, 0),
                            ("phendrana_chapel_tunnel", 0, 0), ("phendrana_chapel_tunnel", 1, 0),
                            ("phendrana_chapel_of_the_elders", 0, 0), ("phendrana_chapel_of_the_elders", 3, 0)]


def region_shot(path: str) -> str:
    """The photo line of the region tests' walks (the pieces of the regions' tests; specs/18n: moved up here, before Phendrana's): `path` without its .png (specs/17j: the full chain gives
    the same pieces its own photo names)."""
    return f"shot {path}.png"


def phendrana_bit(n: int) -> str:
    """`expectbit` of Phendrana item n's bit (tools/phendrana/items.py)."""
    from phendrana import items as phendrana_items
    bit = phendrana_items.BITS[n]
    return f"expectbit {0x7ED870 + bit // 8:06X} {1 << (bit % 8):02X}"


def phendrana_arrive(room: dict, key: str, feet_row: int) -> list[str]:
    """In Phendrana's room `key`, the game running, standing with her feet in row `feet_row`, all her energy."""
    return magmoor_arrive(room, key, feet_row)


def phendrana_up(m: dict, room: dict, tag: str) -> list[str]:
    """Shortcut (as elevador_phendrana_norte): from the landing down to the Magmoor's P16, by door_teleport to its P13 (round
    3's rooms), onto its platform, up: Phendrana's P0, area 4; the gear of round 3 by RAM (the Varia Suit, the Space Jump, the
    Morph Ball and the Bombs; the Wave Beam; 10 missiles: no item of the Tallon, the Chozo or the Magmoor is on the way)."""
    eq = VARIA_EQUIPMENT | SPACE_JUMP_EQUIPMENT | MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT
    return (to_magmoor_p16(m, room) + door_teleport(m, "magmoor_transport_tunnel_a", MAGMOOR_TO_NORTH)
            + [f"expect {ROOM_PTR} {room[MAGMOOR_TO_NORTH]}"] + onto_platform(MAGMOOR_TO_NORTH)
            + ride_elevator(room, MAGMOOR_TO_NORTH, f"{IMG_18F}_{tag}_subindo.png")
            + poke16(0x7E09A2, eq) + poke16(0x7E09A4, eq) + give_beams(WAVE_BEAM) + poke16(0x7E09C6, 10)
            + poke16(0x7E09C8, 10) + ["wait 10"])


def phendrana_full(room: dict, key: str, feet: int, energy: int = 0x63) -> list[str]:
    """phendrana_arrive with `energy` (specs/18n: the full chain's, all she has)."""
    return magmoor_full(room, key, feet, energy)


def phendrana_to_shorelines(room: dict, energy: int = 0x63) -> list[str]:
    """From the P0's platform walking east: the Shoreline Entrance (under the snow, over its drifts) into the Shorelines' L1;
    specs/18g: its 3 Zeelas there, the west one (crawling at her along the beach) killed with two shots crouching. specs/18n:
    `energy`, all she has (the full chain's)."""
    return (P18F_P0_OUT + phendrana_full(room, "phendrana_shoreline_entrance", 9, energy) + [f"expect {WATER_FX_TYPE} 0008"]
            + moves(P18F_ENTRANCE) + phendrana_full(room, "phendrana_shorelines", 25, energy)
            + enemies_alive(PHENDRANA, "phendrana_shorelines") + moves(P18G_SHORE_ZEELA)
            + [f"expect {ENEMY_TABLE:06X} 0000", f"expect {HEALTH} {energy:04X}"])


def phendrana_take(n: int, missiles: int, shot: str) -> list[str]:
    """Walking into Phendrana item n (a Missile Expansion): its message (photo), dismissed; its bit, `missiles` of capacity."""
    return (["wait 120", f"shot {shot}"] + P18F_DISMISS
            + [phendrana_bit(n), f"expect {MAX_MISSILES} {missiles:04X}", f"expect {GAME_STATE} 0008", f"expect {HEALTH} 0063"])


def phendrana_route_a(m: dict, room: dict) -> list[str]:
    """specs/18f, phendrana_regiao_a_rota: up to Phendrana's P0 (phendrana_up: shortcuts), the gear of round 3 by RAM; then
    WALKING region A's open part and its 4 missiles (energy 99 all the way: no enemy until 18g, no damage): the Shoreline
    Entrance (snow falling: FX 8) into the Shorelines; its frozen lake's hole (missile, bit $DB, 15); the Space Jump up onto the
    ruined tower (Prime's Spider Ball track) and its missile (bit $DA, 20); off the tower down the floor door B4 into the Ice
    Ruins Access (on its ceiling door's platform), east into the Ice Ruins East; down to its floor, its ice niche (bit $DD, 25),
    the Space Jump onto its tower (bit $DC, 30); up its zigzag onto the T0 platform, up through the ceiling door into the
    Plaza Walkway (onto the floor door's ledge), west over the hole and up the step into the Shorelines' R1; over the floor door's
    hole in the basin, up the east zigzag onto the overhang, the R0 into the Ruins Entryway; up its zigzag onto the shelf, to the
    R0 (specs/18i: a door now) and through it into the Ice Ruins West (region B). Each room's explored bit; the pause map
    ("PHENDRANA"). specs/18g:
    the enemies alive on arrival in each room that has them (enemies_alive), and killed on the way with the Power Beam alone (two
    Zeelas of the Shorelines, the Ice Ruins Access' 2 orbs, the Ice Ruins East's 2 Zeelas; walks found by a beam search in the
    emulator, scratchpad s18g/scripts/srch.py), the energy still 99 all the way."""
    return (phendrana_up(m, room, "rota") + [f"shot {IMG_18F}_rota_chegada.png"] + phendrana_a_to_lake(room)
            + phendrana_take(1, 15, f"{IMG_18F}_rota_missil_lago.png") + phendrana_a_to_tower(room)
            + phendrana_take(0, 20, f"{IMG_18F}_rota_missil_torre.png") + phendrana_a_to_niche(room)
            + phendrana_take(3, 25, f"{IMG_18F}_rota_missil_nicho.png") + phendrana_a_to_east_tower()
            + phendrana_take(2, 30, f"{IMG_18F}_rota_missil_torre_leste.png") + phendrana_a_to_irw(room)
            + [explored_at(*screen) for screen in PHENDRANA_A_SCREENS + [("phendrana_ice_ruins_west", 0, 1)]]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(PHENDRANA, PHENDRANA_A_SCREENS, "phendrana_a") + [f"shot {IMG_18F}_rota_mapa.png", "hold START 10",
                                                                            "wait 200"])


# specs/18n: the walks of phendrana_regiao_a_rota as pieces shared with the full chain (each ends walking into an item, or at
# the room it names): `energy` checked at each arrival (all she has), `sh` the photo lines (region_shot: the test's names)
def phendrana_a_to_lake(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """From the P0's platform into the Shorelines and east into the frozen lake's hole (its missile)."""
    return phendrana_to_shorelines(room, energy) + [sh(f"{IMG_18F}_rota_shorelines")] + moves(P18F_LAKE)


def phendrana_a_to_tower(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """Out of the lake east past the tower's arch, the Space Jump west up onto the ruined tower's top and east into its missile."""
    return (moves(P18F_TOWER) + SPACE_JUMP_UP["LEFT"] * 4 + ["wait 60", f"expect 7E0AFA {9 * 16 - 21:04X}",
                                                              sh(f"{IMG_18F}_rota_torre"), "hold RIGHT 24"])


def phendrana_a_to_niche(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """Off the tower down the floor door B4 into the Ice Ruins Access (its 2 orbs shot), east into the Ice Ruins East, down to
    its floor (its 2 Zeelas shot), west into the ice niche (its missile)."""
    dead = lambda n: [f"expect {ENEMY_TABLE + ENEMY_SLOT * k:06X} 0000" for k in range(n)]   # noqa: E731  (specs/18g)
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return (moves(P18F_TOWER_OFF) + ["wait 200"] + full("phendrana_ice_ruins_access", 5)
            + enemies_alive(PHENDRANA, "phendrana_ice_ruins_access")
            + [sh(f"{IMG_18F}_rota_ice_ruins_access")] + moves(P18F_ACCESS) + [sh(f"{IMG_18G}_rota_orbes")] + dead(2)
            + moves("DD") + full("phendrana_ice_ruins_east", 9) + enemies_alive(PHENDRANA, "phendrana_ice_ruins_east")
            + moves(P18F_RUINS_DOWN) + ["wait 60"] + full("phendrana_ice_ruins_east", 25) + dead(2)
            + [sh(f"{IMG_18F}_rota_ice_ruins_east")] + moves(P18F_NICHE))


def phendrana_a_to_east_tower() -> list[str]:
    """From the niche east to the tower's foot, back, the Space Jump east onto the tower (its missile)."""
    return moves(P18F_TOWER_FOOT) + ["hold LEFT 40"] + SPACE_JUMP_UP["RIGHT"] * 4


def phendrana_a_to_irw(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """From the Ice Ruins East's tower down and up its zigzag onto the T0 platform, up into the Plaza Walkway, west into the
    Shorelines' R1, over the basin, up the east zigzag onto the overhang (its Zeela shot), the Ruins Entryway, up its zigzag,
    through its R0 into the Ice Ruins West (region B)."""
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    out = SPACE_JUMP_UP["LEFT"] * 4 + ["wait 60", "hold RIGHT 40", "wait 10"]
    for direction, mv in P18F_RUINS_CLIMB:
        out += hops(direction, mv)
    out += ([f"expect 7E0AFA {6 * 16 - 21:04X}", sh(f"{IMG_18F}_rota_plataforma"), "hold LEFT 10"] + P18F_RISE
            + full("phendrana_plaza_walkway", 12) + hops("LEFT", [(4, 30, -60)]) + moves(P18F_PLAZA)
            + full("phendrana_shorelines", 25) + ["hold LEFT 110", "wait 30", f"expect 7E0AFA {29 * 16 - 21:04X}"]
            + hops("LEFT", P18F_BASIN) + full("phendrana_shorelines", 25) + ["hold LEFT 40", "wait 10"])
    for direction, mv in P18F_EAST_CLIMB:
        out += hops(direction, mv)
    out += ([f"expect 7E0AFA {10 * 16 - 21:04X}", sh(f"{IMG_18F}_rota_saliencia")] + moves(P18G_OVERHANG_ZEELA)
            + [f"expect {ENEMY_TABLE + 2 * ENEMY_SLOT:06X} 0000"] + moves("RRRRRRRRRRRD")
            + full("phendrana_ruins_entryway", 25) + moves("RRRRRR") + ["hold LEFT 30", "wait 10"])
    for direction, mv in P18F_RUINS_ENTRY_CLIMB:
        out += hops(direction, mv)
    # specs/18i: the R0 is a door now (the Ice Ruins West, region B: a blue door on both sides): she stops at its cap, then
    # goes through it
    return (out + moves("RRRRRR") + ["wait 30"] + full("phendrana_ruins_entryway", 9)
            + [f"expect {SAMUS_X} 02DB", sh(f"{IMG_18F}_rota_ruins_entryway")] + moves("D")
            + full("phendrana_ice_ruins_west", 25))


def phendrana_to_l0_shelf(room: dict, energy: int = 0x63) -> list[str]:
    """From the Shorelines' L1 east along the beach, up the west zigzag onto the cliff (the L0 shelf, feet row 9)."""
    out = ["hold RIGHT 130", "wait 10"]
    for direction, mv in P18F_WEST_CLIMB:
        out += hops(direction, mv)
    return out + phendrana_full(room, "phendrana_shorelines", 9, energy)


def phendrana_temple(m: dict, room: dict) -> list[str]:
    """specs/18f, phendrana_regiao_a_templo: up to Phendrana's P0 (phendrana_up), WALKING: the Shorelines' west zigzag onto the
    cliff and the T0 door's platform, up through the ceiling door into the Temple Entryway (onto the floor door's east ledge),
    west over its hole onto the step, the L0 into the Chozo Ice Temple (the icy ruins' look, snow falling); up its east zigzag
    onto the shelf against the ice wall; the bomb block (Prime's bomb slot) standing against it, the ball and a bomb break it,
    the ball rolls through the 1-row tunnel into the R0 door's chamber; the Chapel Tunnel, the Chapel of the Elders (specs/18h:
    the Sheegoth's arena won by RAM before, its boss bit: the dead state, no enemy, the missile on the altar not reached); its
    only door (L0) is a wave door from inside: the Power Beam leaves it shut, the Wave Beam opens it, back in the Chapel Tunnel. Energy 99 the whole way; the explored bits and the pause map."""
    return (phendrana_up(m, room, "templo") + phendrana_a_to_chapel_tunnel(room)
            + ["poke 7ED82C 08"]   # specs/18h, a shortcut: the Sheegoth won by RAM (its bit; phendrana_sheegoth fights it)
            + moves("RRRRRRRRRRRRRRD")
            + phendrana_arrive(room, "phendrana_chapel_of_the_elders", 9) + [f"expect {WATER_FX_TYPE} 0008",
                                                                             f"expect {ENEMY_TABLE:06X} 0000"]
            + moves("RRRRRRRRRRRRRRRRR") + ["wait 30", f"shot {IMG_18F}_templo_capela.png"] + moves("LLLLLLLLLLLLLLLLLLL")
            + ["wait 30", f"shot {IMG_18F}_templo_porta_de_onda.png"]
            + give_beams(0) + ["hold RIGHT 30", "hold LEFT 2", "wait 5", "hold X 2", "wait 60", "hold LEFT 80", "wait 60",
                               f"expect {ROOM_PTR} {room['phendrana_chapel_of_the_elders']}"]
            + give_beams(WAVE_BEAM) + ["hold RIGHT 30", "hold LEFT 2", "wait 5", "hold X 2", "wait 60", "hold LEFT 80", "wait 200"]
            + phendrana_arrive(room, "phendrana_chapel_tunnel", 9)
            + [explored_at(*screen) for screen in PHENDRANA_TEMPLE_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(PHENDRANA, PHENDRANA_TEMPLE_SCREENS, "phendrana_templo")
            + [f"shot {IMG_18F}_templo_mapa.png", "hold START 10", "wait 200"])


def phendrana_a_to_chapel_tunnel(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """specs/18n, phendrana_regiao_a_templo's walk as a piece shared with the full chain: from the P0's platform the Shorelines'
    west zigzag onto the cliff and the T0 door's platform, up into the Temple Entryway, west into the Chozo Ice Temple, up its
    east zigzag onto the shelf, the bomb block broken in the ball, the ball through the tunnel into the R0 door's chamber, the
    Chapel Tunnel (at its L0)."""
    block = level_block("phendrana_chozo_ice_temple", *__import__("phendrana.layouts", fromlist=["TEMPLE_BOMB"]).TEMPLE_BOMB)
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    out = (phendrana_to_shorelines(room, energy) + phendrana_to_l0_shelf(room, energy) + P18F_TO_PLATFORM
           + [f"expect 7E0AFA {6 * 16 - 21:04X}", sh(f"{IMG_18F}_templo_plataforma"), "hold LEFT 10"] + P18F_RISE_EAST
           + full("phendrana_temple_entryway", 12) + [sh(f"{IMG_18F}_templo_entryway")]
           + hops("LEFT", [(9, 30, -60)]) + moves("E") + full("phendrana_chozo_ice_temple", 25)
           + [f"expect {WATER_FX_TYPE} 0008", sh(f"{IMG_18F}_templo_chegada"), "hold LEFT 120", "wait 10"])
    for direction, mv in P18F_TEMPLE_CLIMB:
        out += hops(direction, mv)
    return (out + full("phendrana_chozo_ice_temple", 9)
            + [f"expect {block:06X} F058", "hold RIGHT 10", "wait 10", f"expect {block:06X} F058",
               sh(f"{IMG_18F}_templo_parede")]
            + MORPH + [f"expect {POSE} {BALL_POSE}", "hold RIGHT 14", "wait 10", "hold X 2", "wait 90", f"expect {block:06X} 00FF",
                       "hold RIGHT 100", "wait 30"] + UNMORPH + [f"expect {POSE} {STAND_POSE}", sh(f"{IMG_18F}_templo_camara")]
            + moves("D") + full("phendrana_chapel_tunnel", 9))


def phendrana_save_b(m: dict, room: dict) -> list[str]:
    """specs/18f, phendrana_save_station_b: up to Phendrana's P0 (phendrana_up), WALKING to the Shorelines' cliff (the west
    zigzag) and through the L0 into Save Station B (P4, the icy ruins' look, no snow). Samus on the pedestal (where the game puts
    her when it loads the station), a marker in the saved data (game hours 6), YES, "save completed": load station 1 of area 4,
    its used-station bit ($7ED900 bit 1); paused, Phendrana's map. Game over: the area-select screen picks area 4, station 1, and
    draws "PHENDRANA / DRIFTS" (after "TALLON / OVERWORLD": the landing's save at the ship); continue: back on Save Station B's
    pedestal, area 4, the marker loaded, the explored bits kept."""
    st = PHENDRANA.load_stations[1]
    out = (phendrana_up(m, room, "save") + phendrana_to_shorelines(room) + phendrana_to_l0_shelf(room) + moves("E")
           + phendrana_arrive(room, "phendrana_save_station_b", 9) + [f"expect {WATER_FX_TYPE} 0000",
                                                                      f"shot {IMG_18F}_save_sala.png"] + poke16(0x7E09E0, 6))
    for addr, v in ((0x7E0AF6, st.x), (0x7E0B10, st.x), (0x7E0AFA, st.y), (0x7E0B14, st.y)):
        out += poke16(addr, v)
    screens = [("phendrana_transport_magmoor_west", 1, 1), ("phendrana_shoreline_entrance", 0, 0),
               ("phendrana_shorelines", 0, 1), ("phendrana_shorelines", 0, 0), ("phendrana_save_station_b", 0, 0)]
    return (out + ["hold RIGHT 1", "wait 180", f"shot {IMG_18F}_save_pergunta.png", "hold A 2", "wait 300", "hold A 2",
                   "wait 200", f"expect {LOAD_STATION} 0001", f"expect {AREA} 0004", f"expectbit {USED_STATIONS_AREA4} 02",
                   f"expect {GAME_STATE} 0008", f"shot {IMG_18F}_save_salvo.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}", f"shot {IMG_18F}_save_mapa.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} 0008",
                   "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
                   "hold A 2", "wait 300"]
            + area_select_shows_after(PHENDRANA.number, st.index, (TALLON.number,), f"{IMG_18F}_save_tela_de_area.png")
            + ["hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0004", f"expect {ROOM_PTR} {room[st.room]}",
               f"expect {LOAD_STATION} 0001", f"expect {GAME_HOURS} 0006", f"expect 7E0AF6 {st.x:04X}",
               f"shot {IMG_18F}_save_continue.png"]
            + [explored_at(*sc) for sc in screens])


# specs/18i: region B of Phendrana (tools/phendrana/layouts.py, items.py; item bits $DF-$E1, the red doors' $C2-$C3). The walks
# are MAGMOOR_MOVES strings found by a beam search in the emulator (scratchpad s18i/scripts/srch.py), the enemies alive on
# arrival and killed on the way with the round-3 gear (phendrana_up), the energy 99 all the way.
IMG_18I = "build/tests/18i"   # the photos of the region B tests (specs/img/18i-* are copies of some)
IRW = "phendrana_ice_ruins_west"
IRW_RED_BIT, SAVE_A_RED_BIT = 0xC2, 0xC3   # the epic's red door bits: the Ice Ruins West's L0, the Courtyard's R1
IRW_CAP_SLOT, IRW_CAP_PLM = 37, 0xF2D7   # the plasma cap's PLM slot (after the R1 wave cap's 39 and the L0 red cap's 38) and id
# the Ice Ruins West from the L1: east under the west cliff and up onto its zigzag's first ledge (feet row 20), facing the plasma
# cap in the cliff's face; up the zigzag onto the cliff (the L0 shelf, feet row 9)
P18I_IRW_LEDGE = "GGGIL"
P18I_IRW_CLIMB = "GYIYp"
COURT, HLE, HYDRA = "phendrana_ruined_courtyard", "phendrana_hydra_lab_entryway", "phendrana_research_lab_hydra"
P18I_IRW_TO_R1 = "DDD"            # off the L0 shelf down to the floor, east through the R1's wave door
P18I_ENTRYWAY = "GRGXRDD"         # the Courtyard Entryway past its orb and zoomer into the Ruined Courtyard's L0 (no damage)
P18I_COURT_DOWN = "GxRGLI"        # the Courtyard's L0 shelf down the west zigzag onto its first ledge (feet row 20)
P18I_COURT_TO_R0 = "DGXXgXD"      # from the first ledge east, up the east zigzag onto the R0 shelf, through its wave door
P18I_SPECIMEN = "RRRRRRD"         # the Specimen Storage east to its R0 (a wave door: the shot from near it)
P18I_TO_PLATFORM = "gxggxp"       # the Research Entrance from the L0 onto the T1 door's platform (feet row 5)
P18I_HLE = "xgXcDXD"              # the Hydra Lab Entryway from its floor door's cap past the 2 orbs, the R0 (wave) into the lab
P18I_HYDRA_DOWN = "RRRLLLLLL"     # the lab's west slab east off into the gap, down to the lower floor, west into the missile
PHENDRANA_B_SCREENS = [(IRW, 0, 1), (IRW, 0, 0), (IRW, 3, 1), ("phendrana_canyon_entryway", 2, 0),
                       ("phendrana_courtyard_entryway", 0, 0), ("phendrana_courtyard_entryway", 2, 0), (COURT, 0, 0),
                       (COURT, 0, 1), (COURT, 4, 0), ("phendrana_specimen_storage", 0, 0),
                       ("phendrana_research_entrance", 0, 0), ("phendrana_research_entrance", 1, 0), (HLE, 0, 0), (HLE, 2, 0),
                       (HYDRA, 0, 0), (HYDRA, 0, 1)]


def phendrana_arrive_e(room: dict, key: str, feet_row: int, energy: int) -> list[str]:
    """phendrana_arrive with `energy` (specs/18i: after the Ruined Courtyard's Energy Tank, 199)."""
    return [f"expect {ROOM_PTR} {room[key]}", f"expect {GAME_STATE} 0008", f"expect 7E0AFA {(feet_row + 1) * 16 - 21:04X}",
            f"expect {HEALTH} {energy:04X}"]


def phendrana_red_door(room: dict, key: str, toward: str, to: str, missiles: int, shot: str, bit: int) -> list[str]:
    """specs/18i: standing against `key`'s red door (toward `toward`), `missiles` in hand: missiles selected, 6 shots (5 hits open
    it), its bit on, back to the beam, through into `to` (the energy untouched: the arrival is spec 15's, the enemies there far
    off); a photo `shot` 160 frames after (as red_door, without refilling the missiles or the energy). `bit`: the door bit the
    epic gives it (Phendrana's $C2-$C6 in order), written out: the test does not read it from the build's tables."""
    return (["wait 30", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001"] + [f"hold {toward}+X 2", "wait 30"] * 6
            + ["wait 60", f"expectbit {0x7ED8B0 + bit // 8:06X} {1 << (bit % 8):02X}", f"expect {MISSILES} {missiles - 6:04X}",
               "poke 7E09D2 00", "wait 10", f"hold {toward} 90", "wait 160", f"expect {ROOM_PTR} {room[to]}",
               f"expect {GAME_STATE} 0008", f"expect {HEALTH} 0063", f"shot {shot}"])


def phendrana_route_b(m: dict, room: dict) -> list[str]:
    """specs/18i, phendrana_regiao_b_rota: up to Phendrana's P0 (phendrana_up: shortcuts, the gear of round 3), into the Ice Ruins
    West through the Ruins Entryway's R0 (door_teleport: phendrana_regiao_a_rota walks there); then WALKING region B with the
    gear of round 3: the Ice Ruins West's first ledge before the plasma cap (a Wave Beam shot leaves it shut, it stops her),
    up the zigzag, its red door (Prime's missile shield) opened with missiles (bit $C2) into the Canyon Entryway and back; the
    R1's wave door, the Courtyard Entryway (its orb and zoomer alive on arrival, no damage), the Ruined Courtyard: the bomb
    block in the cliff's face (Prime's bomb slot) bombed in the ball, the Energy Tank in the chamber (bit $E0, 199); the east
    zigzag, the wave doors into the Specimen Storage and the Research Entrance; the vertical wave door in its roof (the
    Power Beam leaves it shut, the Wave Beam opens it), up into the Hydra Lab Entryway (its 2 orbs), the Research Lab Hydra's
    missile on the lower floor (bit $E1, 15); the explored bits and the pause map. Then the gear of round 6 by RAM (the Plasma
    Beam: a shortcut, its round's walk is specs/18n's chain) and back into the Ice Ruins West: the Plasma Beam opens the cap,
    the power bomb expansion in the niche (bit $DF, 5 power bombs)."""
    out = (phendrana_up(m, room, "rota_b") + door_teleport(m, "phendrana_ruins_entryway", IRW) + ["wait 200"]
           + phendrana_arrive(room, IRW, 25) + [f"shot {IMG_18I}_rota_chegada.png"] + phendrana_b_to_red_door(room)
           + phendrana_red_door(room, IRW, "LEFT", "phendrana_canyon_entryway", 10, f"{IMG_18I}_rota_canyon_entryway.png",
                                IRW_RED_BIT)
           + phendrana_b_to_tank(room) + ["wait 30", f"shot {IMG_18I}_rota_energy_tank.png"] + P18F_DISMISS
           + [phendrana_bit(6), f"expect {MAX_ENERGY} 00C7", f"expect {HEALTH} 00C7"] + phendrana_b_to_hydra(room, 199)
           + ["wait 120", f"shot {IMG_18I}_rota_missil.png"] + P18F_DISMISS
           + [phendrana_bit(7), f"expect {MAX_MISSILES} 000F", f"expect {GAME_STATE} 0008", f"expect {HEALTH} 00C7"]
           + [explored_at(*screen) for screen in PHENDRANA_B_SCREENS]
           + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
           + pause_shows(PHENDRANA, PHENDRANA_B_SCREENS, "phendrana_b") + [f"shot {IMG_18I}_rota_mapa.png", "hold START 10",
                                                                           "wait 200"]
           # the gear of round 6 by RAM (the Plasma Beam, round 5's: a shortcut), back into the Ice Ruins West (door_teleport):
           # onto the first ledge, a Plasma Beam shot opens the cap, into the niche: the power bomb expansion
           + give_beams(PLASMA_BEAM) + door_teleport(m, "phendrana_ruins_entryway", IRW) + ["wait 200"]
           + phendrana_arrive_e(room, IRW, 25, 199) + phendrana_b_to_pb(room, 199)
           + ["wait 60", f"shot {IMG_18I}_rota_power_bomb.png"] + P18F_DISMISS
           + [phendrana_bit(5), f"expect {MAX_POWER_BOMBS} 0005", f"expect {POWER_BOMBS} 0005", f"expect {GAME_STATE} 0008",
              f"expect {HEALTH} 00C7", "hold RIGHT 60", "wait 30", f"shot {IMG_18I}_rota_nicho.png"])
    return out


# specs/18n: the walks of phendrana_regiao_b_rota as pieces shared with the full chain (each ends walking into an item, or at
# the place it names): `energy` checked at each arrival, `sh` the photo lines (region_shot: the test's names)
def phendrana_b_to_red_door(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """The Ice Ruins West from the L1 onto the first ledge before the plasma cap (a Wave Beam shot leaves it shut, it stops her),
    up the zigzag onto the L0 shelf, against the red door to the Canyon Entryway."""
    lay = __import__("phendrana.layouts", fromlist=["IRW_CAP"])
    cap = level_block(IRW, *lay.IRW_CAP[:2])
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return (moves(P18I_IRW_LEDGE) + full(IRW, 20) + moves("fs") + ["wait 30"]
            + [f"expect {plm_slot(PLM_HEADERS, IRW_CAP_SLOT)} {IRW_CAP_PLM:04X}", f"expect {cap:06X} C400",
               sh(f"{IMG_18I}_rota_tampa_fechada"), "hold LEFT 30", "wait 10", f"expect {SAMUS_X} 00F5"]   # the cap stops her
            + moves(P18I_IRW_CLIMB) + full(IRW, 9))


def phendrana_b_to_tank(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """From the Canyon Entryway (behind the red door) back into the Ice Ruins West, down to the floor, east through the R1 (a
    wave door: the Wave Beam's shot) into the Courtyard Entryway (its orb and zoomer), the Ruined Courtyard: down the west
    zigzag onto its first ledge, against the bomb block in the cliff's face (the bomb slot): the ball, a bomb breaks it,
    rolling west through the tunnel into the chamber: into the Energy Tank."""
    lay = __import__("phendrana.layouts", fromlist=["COURT_BOMB"])
    bomb = level_block(COURT, *lay.COURT_BOMB)
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return (moves("kepD") + full(IRW, 9)
            # down to the floor, east through the R1 (a wave door on this side: the Wave Beam's shot) into the Courtyard Entryway
            + moves(P18I_IRW_TO_R1) + full("phendrana_courtyard_entryway", 9)
            + enemies_alive(PHENDRANA, "phendrana_courtyard_entryway") + [sh(f"{IMG_18I}_rota_courtyard_entryway")]
            + moves(P18I_ENTRYWAY) + full(COURT, 9) + [sh(f"{IMG_18I}_rota_courtyard")]
            # the Ruined Courtyard: down the west zigzag onto its first ledge, against the bomb block in the cliff's face (the
            # bomb slot): the ball, a bomb breaks it, rolling west through the tunnel into the chamber: the Energy Tank
            + moves(P18I_COURT_DOWN) + full(COURT, 20) + ["hold LEFT 8", "wait 10", f"expect {bomb:06X} F058"]
            + MORPH + [f"expect {POSE} {BALL_POSE_LEFT}", "hold LEFT 14", "wait 10", "hold X 2", "wait 90",
                       f"expect {bomb:06X} 00FF", sh(f"{IMG_18I}_rota_tunel"), "hold LEFT 100"])


def phendrana_b_to_hydra(room: dict, energy: int, sh=region_shot, beam_proof: bool = True) -> list[str]:
    """From the Ruined Courtyard's Energy Tank (all of `energy` after it) out of the chamber, east and up the east zigzag onto the
    R0 shelf, its wave door into the Specimen Storage, its wave door into the Research Entrance; onto the ceiling door's
    platform, a Wave Beam shot up opens the vertical wave door (`beam_proof`: the Power Beam does not: specs/18i's door), a jump
    up into the Hydra Lab Entryway (she lands on its floor door's cap), its 2 orbs, the R0 into the Research Lab Hydra: off the
    west slab down the gap to the lower lab, west into the missile."""
    up_cap = level_block("phendrana_research_entrance", 22, 2)   # the T1 door's cap (its first block)
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return (["hold RIGHT 100", "wait 20"] + UNMORPH + [f"expect {POSE} {STAND_POSE}"]
            # east and up the east zigzag onto the R0 shelf, its wave door into the Specimen Storage, its wave door into the
            # Research Entrance; onto the ceiling door's platform, a Wave Beam shot up opens the vertical wave door (the Power
            # Beam does not: specs/18i's door), a jump up into the Hydra Lab Entryway (she lands on its floor door's cap)
            + moves(P18I_COURT_TO_R0) + full("phendrana_specimen_storage", 9)
            + moves(P18I_SPECIMEN) + full("phendrana_research_entrance", 9)
            + moves(P18I_TO_PLATFORM) + full("phendrana_research_entrance", 5)
            + [f"expect {up_cap:06X} CFFA", sh(f"{IMG_18I}_rota_porta_vertical")]
            + (give_beams(0) + ["hold UP 6", "hold UP+X 2", "wait 40", f"expect {up_cap:06X} CFFA"] + give_beams(WAVE_BEAM)
               if beam_proof else [])
            + ["hold UP 6", "hold UP+X 2", "wait 10", sh(f"{IMG_18I}_rota_porta_vertical_abrindo"), "wait 30",
               "hold A 30", "wait 300"] + full(HLE, 12)
            + enemies_alive(PHENDRANA, HLE) + [sh(f"{IMG_18I}_rota_hydra_entryway")]
            + moves(P18I_HLE) + full(HYDRA, 9) + [sh(f"{IMG_18I}_rota_hydra")]
            # the Research Lab Hydra: off the west slab down the gap to the lower lab, west into the missile
            + moves(P18I_HYDRA_DOWN))


def phendrana_b_to_pb(room: dict, energy: int, sh=region_shot) -> list[str]:
    """From the Ice Ruins West's L1 (in from the Ruins Entryway) onto the first ledge, a Plasma Beam shot opens the cap (its PLM
    gone, the block a plain one), west into the niche: the power bomb expansion."""
    lay = __import__("phendrana.layouts", fromlist=["IRW_CAP"])
    cap = level_block(IRW, *lay.IRW_CAP[:2])
    return (moves(P18I_IRW_LEDGE) + phendrana_full(room, IRW, 20, energy)
            + [f"expect {plm_slot(PLM_HEADERS, IRW_CAP_SLOT)} {IRW_CAP_PLM:04X}"] + moves("fs")
            + ["wait 10", sh(f"{IMG_18I}_rota_tampa_abrindo"), "wait 50", f"expect {plm_slot(PLM_HEADERS, IRW_CAP_SLOT)} 0000",
               f"expect {cap:06X} 0482", "hold LEFT 60"])


P18I_COURT_TO_R1 = "GGXGGGGGxGG"   # the Courtyard's L0 shelf down the west zigzag, east along the floor to near the R1


def phendrana_save_a(m: dict, room: dict) -> list[str]:
    """specs/18i, phendrana_save_station_a: up to Phendrana's P0 (phendrana_up), into the Ruined Courtyard by its L0
    (door_teleport from the Courtyard Entryway: phendrana_regiao_b_rota walks there), WALKING down to its floor and east to the
    R1, a red door on the courtyard's side (Prime's missile shield): 6 missiles open it (its bit $C3), into Save Station A (P17,
    the icy ruins, snow falling as in Prime). Samus on the pedestal, a marker in the saved data (game hours 7), YES: load station
    2 of area 4, its used-station bit ($7ED900 bit 2); paused, the map. Game over: the area-select screen picks area 4, station
    2 (after "TALLON / OVERWORLD"); continue: back on Save Station A's pedestal, area 4, the marker, the red door's bit kept."""
    st = PHENDRANA.load_stations[2]
    ssa = "phendrana_save_station_a"
    bit = SAVE_A_RED_BIT
    out = (phendrana_up(m, room, "save_a") + door_teleport(m, "phendrana_courtyard_entryway", COURT) + ["wait 200"]
           + phendrana_arrive(room, COURT, 9) + moves(P18I_COURT_TO_R1) + phendrana_arrive(room, COURT, 25)
           + phendrana_red_door(room, COURT, "RIGHT", ssa, 10, f"{IMG_18I}_save_sala.png", SAVE_A_RED_BIT)
           + [f"expect {WATER_FX_TYPE} 0008"] + poke16(0x7E09E0, 7))
    for addr, v in ((0x7E0AF6, st.x), (0x7E0B10, st.x), (0x7E0AFA, st.y), (0x7E0B14, st.y)):
        out += poke16(addr, v)
    return (out + ["hold RIGHT 1", "wait 180", f"shot {IMG_18I}_save_pergunta.png", "hold A 2", "wait 300", "hold A 2",
                   "wait 200", f"expect {LOAD_STATION} 0002", f"expect {AREA} 0004", f"expectbit {USED_STATIONS_AREA4} 04",
                   f"expect {GAME_STATE} 0008", f"shot {IMG_18I}_save_salvo.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}", f"shot {IMG_18I}_save_mapa.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} 0008",
                   "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
                   "hold A 2", "wait 300"]
            + area_select_shows_after(PHENDRANA.number, st.index, (TALLON.number,), f"{IMG_18I}_save_tela_de_area.png")
            + ["hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0004", f"expect {ROOM_PTR} {room[st.room]}",
               f"expect {LOAD_STATION} 0002", f"expect {GAME_HOURS} 0007", f"expect 7E0AF6 {st.x:04X}",
               f"expectbit {0x7ED8B0 + bit // 8:06X} {1 << (bit % 8):02X}", f"shot {IMG_18I}_save_continue.png",
               explored_at(ssa, 0, 0), explored_at(COURT, 4, 1)])


MAP_STATION_AREA4 = f"{0x7ED908 + 4:06X}"   # map_station_byte_array[4]
P18I_TO_MAP = "RRRRRRRRRRRRD"   # the Research Entrance from its L0 east through the R0 into the Map Station


def phendrana_map(m: dict, room: dict) -> list[str]:
    """specs/18i, phendrana_map_station: up to Phendrana's P0 (phendrana_up), into the Research Entrance by its L0
    (door_teleport from the Specimen Storage: phendrana_regiao_b_rota walks there), WALKING east through its R0 into the Map
    Station (P22, the labs' look); on the pause map before, rooms not visited (Save Station A, the Phendrana Canyon, the
    Research Lab Hydra, the Chozo Ice Temple) are blank; she walks east off the door's ledge into the terminal (the station
    mirrored: its west side): "map data access completed", the pause map opens by itself with the whole built Phendrana drawn:
    those rooms' tiles (palette 3: not explored) and the map station byte of area 4 set ($7ED90C = $FF)."""
    unvisited = [("phendrana_save_station_a", 0, 0), ("phendrana_canyon", 2, 1), ("phendrana_research_lab_hydra", 0, 1),
                 ("phendrana_chozo_ice_temple", 0, 0)]
    (WORK / "vram_18i_vazio.bin").write_bytes(struct.pack("<H", pausemap.BLANK))
    return (phendrana_up(m, room, "mapa") + door_teleport(m, "phendrana_specimen_storage", "phendrana_research_entrance")
            + ["wait 200"] + phendrana_arrive(room, "phendrana_research_entrance", 9) + [f"expect {MAP_STATION_AREA4} 00"]
            + moves(P18I_TO_MAP) + phendrana_arrive(room, "phendrana_map_station", 9) + [f"shot {IMG_18I}_mapa_sala.png",
                                                                                          "hold START 10", "wait 200",
                                                                                          f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + [f"expectvram {PAUSE_MAP_VRAM + pausemap.tile_index(*map_tile(k, a, b)):04X} "
               f"{(WORK / 'vram_18i_vazio.bin').relative_to(ROOT)}" for k, a, b in unvisited]
            + [f"shot {IMG_18I}_mapa_antes.png", "hold START 10", "wait 200", f"expect {GAME_STATE} 0008",
               "hold RIGHT 60", "wait 260", f"shot {IMG_18I}_mapa_mensagem.png", "hold A 2", "wait 200",
               f"expect {MAP_STATION_AREA4} FF", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + revealed_tiles(unvisited, "18i_revelado") + [f"shot {IMG_18I}_mapa_revelado.png"])


# specs/18j: region C of Phendrana (tools/phendrana/layouts.py, items.py; item bits $E2-$E3). The walks are MAGMOOR_MOVES strings
# and hops found in the emulator (scratchpad s18j/scripts: srch.py's beam search, hopx.py's walk frames before each jump, the
# middle of the window taken), from the round-3 gear of phendrana_up, the energy 99 until the Energy Tank.
IMG_18J = "build/tests/18j"   # the photos of the region C test (specs/img/18j-* are copies of some)
QA, NQT, QC = "phendrana_quarantine_access", "phendrana_north_quarantine_tunnel", "phendrana_quarantine_cave"
QM, SQT, P29, TA = ("phendrana_quarantine_monitor", "phendrana_south_quarantine_tunnel", "phendrana_transport_magmoor_south",
                    "phendrana_transport_access")
# the plasma cap's PLM slot (after the L0 ice cap's 39; specs/18m: and the R0 wave cap's 38, the R0 a door since then) and id
TA_CAP_SLOT, TA_CAP_PLM = 37, 0xF2D7
STAND_POSE_LEFT = "0002"              # standing, facing west ($0A1C)
P18J_QA = "LLLLLLLLLL"            # the Quarantine Access west along its floor into the floor door (no cap on its side)
# the North Quarantine Tunnel from the ceiling door's platform: west off it onto the top terrace and down the switchback at the
# middle (the orbs over the terraces off camera: they stay where they are), then east along the floor through the R3
P18J_NQT_DOWN = "LLLLLLLlRRRLLLRRRLLLRRRLLLRRRLLLRRRpp"
P18J_NQT_OUT = "RRRRRRRRRRRRRRRRRRRRD"
# the Quarantine Cave from the L0 shelf down the west zigzag to the floor, west under it to the Morph Ball tunnel's mouth
P18J_QC_DOWN = "RRRRRRRRLLLLLLLLLLLRRRRLLL"
def ball_through(d: str) -> list[str]:
    """Walking `d` into a 1-row tunnel's mouth, the ball, rolling through it, standing up at its end."""
    return ["hold " + d + " 40"] + MORPH + ["hold " + d + " 80", "wait 10"] + UNMORPH
# the Quarantine Cave's east zigzag (21, 16, 11) from the floor onto the R0 shelf (row 10)
P18J_QC_CLIMB = [("RIGHT", [(114, 30, -60)]), ("LEFT", [(9, 30, -60)]), ("RIGHT", [(12, 30, -60), (15, 30, -60)])]
# the South Quarantine Tunnel down its steps, its 2 orbs shot as they come on camera; up the step and the zigzag (51 east, 46
# west, 41 east, 36 west, 31 east) onto the R1 shelf (row 26)
P18J_SQT_DOWN = "RRRRRRRRRRRalrccRRRRRRrcccRRRRRRRRRRRRRppp"
P18J_SQT_CLIMB = [("LEFT", [(15, 30, -60)]), ("RIGHT", [(23, 30, -60)]), ("LEFT", [(6, 30, -60)]), ("RIGHT", [(12, 30, -60)]),
                  ("LEFT", [(10, 30, -60)]), ("RIGHT", [(11, 30, -60), (15, 30, -60)])]
# the P29 from the L1 east under the zigzag, up it from the east (21 west, 16 west, 11 east) onto the R0 shelf (row 10)
P18J_P29_CLIMB = [("LEFT", [(25, 30, -60)]), ("LEFT", [(19, 30, -60)]), ("RIGHT", [(8, 30, -60), (15, 30, -60)])]
# the Transport Access: its orb shot from the L0 step and the floor; onto the ice pillar and off it east, facing its niche
P18J_TA = "XRaRapRlccs"
PHENDRANA_C_SCREENS = [(QA, 0, 0), (NQT, 4, 0), (NQT, 2, 1), (NQT, 3, 3), (NQT, 5, 3), (QC, 0, 0), (QC, 0, 1), (QC, 5, 0),
                       (QM, 2, 0), (QM, 0, 0), (SQT, 0, 0), (SQT, 2, 1), (SQT, 4, 3), (SQT, 5, 1), (P29, 0, 1), (P29, 1, 0),
                       (TA, 0, 0), (TA, 1, 0)]


def phendrana_route_c(m: dict, room: dict) -> list[str]:
    """specs/18j, phendrana_regiao_c_rota: up to Phendrana's P0 (phendrana_up: shortcuts, the gear of round 3), into the
    Quarantine Access by its R0 (door_teleport from the Ruined Courtyard: phendrana_regiao_b_rota walks there); then WALKING
    region C: down the Quarantine Access' floor door onto the North Quarantine Tunnel's ceiling door's platform: its door is a
    vertical wave door in the snow look (the Power Beam leaves it shut, the Wave Beam opens it; specs/18j's paint); its 2 orbs
    alive; down the switchback (no damage) and the R3's wave door into the Quarantine Cave; down the west zigzag, the ball through
    the 1-row tunnel to the L1's chamber (Prime's Morph Ball door), standing up there, through the door into the Quarantine
    Monitor, the ball through its tunnel, the missile at the lookout's end (bit $E2, 15); back through both tunnels, up the
    cave's east zigzag, its R0 (wave) into the South Quarantine Tunnel (its 2 orbs alive on arrival, shot on the steps, no
    damage), up its zigzag, the R1 (wave) into the P29; up its zigzag to the R0, an ice door: the Wave Beam leaves it shut, the
    gear of round 4 by RAM (the Ice Beam: a shortcut) opens it; the Transport Access (its orb alive, shot); onto the ice pillar,
    off it, the plasma cap that the Wave and Ice shot leaves shut; the gear of round 6 by RAM (the Plasma Beam: a shortcut, its
    round's walk is specs/18n's chain): the cap opens, the Energy Tank in the niche (bit $E3, 199); the explored bits and the
    pause map."""
    out = (phendrana_up(m, room, "rota_c") + door_teleport(m, "phendrana_ruined_courtyard", QA) + ["wait 200"]
           + phendrana_arrive(room, QA, 9) + phendrana_c_to_nqt_foot(room)
           + ["poke 7ED82C 10"]   # specs/18k, a shortcut: the Thardus won by RAM (the arena's bit; phendrana_thardus fights it)
           + moves(P18J_NQT_OUT) + phendrana_arrive(room, QC, 9) + [f"shot {IMG_18J}_rota_quarantine_cave.png"]
           # the cave: down to the floor, the ball through the tunnel, standing in the L1's chamber, through into the Monitor
           + moves(P18J_QC_DOWN) + phendrana_arrive(room, QC, 25) + phendrana_c_to_monitor_missile(room)
           + ["wait 120", f"shot {IMG_18J}_rota_missil.png"]
           + P18F_DISMISS + [phendrana_bit(8), f"expect {MAX_MISSILES} 000F", f"expect {GAME_STATE} 0008",
                             f"expect {HEALTH} 0063"] + phendrana_c_to_p29(room) + phendrana_c_to_ta(room)
           + phendrana_c_ta_to_cap(room) + phendrana_c_to_ta_tank(room) + ["wait 100", f"shot {IMG_18J}_rota_energy_tank.png"] + P18F_DISMISS
           + [phendrana_bit(9), f"expect {MAX_ENERGY} 00C7", f"expect {HEALTH} 00C7", f"expect {GAME_STATE} 0008",
              "hold RIGHT 60", "wait 30", f"shot {IMG_18J}_rota_nicho.png"]
           + [explored_at(*screen) for screen in PHENDRANA_C_SCREENS]
           + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
           + pause_shows(PHENDRANA, PHENDRANA_C_SCREENS, "phendrana_c") + [f"shot {IMG_18J}_rota_mapa.png", "hold START 10",
                                                                           "wait 200"])
    return out


# specs/18n: the walks of phendrana_regiao_c_rota as pieces shared with the full chain (each ends walking into an item, or at
# the place it names): `energy` checked at each arrival, `sh` the photo lines (region_shot: the test's names); `beam_proof`:
# the test's shots with less than the beam a door needs (beams by RAM: the chain never gives a beam)
def phendrana_c_to_nqt_foot(room: dict, energy: int = 0x63, sh=region_shot, beam_proof: bool = True) -> list[str]:
    """From the Quarantine Access' R0: west into its floor door, onto the North Quarantine Tunnel's ceiling door's platform (its
    2 orbs alive); its door a vertical wave door in the snow look (`beam_proof`: the Power Beam leaves it shut), the Wave Beam
    opens it; down the switchback to the tunnel's foot."""
    up_cap = level_block(NQT, 4 * 16 + 6, 2)   # the T4 door's cap (its first block)
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return (moves(P18J_QA) + ["wait 200"] + full(NQT, 5)
            + enemies_alive(PHENDRANA, NQT) + [f"expect {up_cap:06X} CFFA", sh(f"{IMG_18J}_rota_porta_vertical")]
            + (give_beams(0) + ["hold UP 6", "hold UP+X 2", "wait 40", f"expect {up_cap:06X} CFFA"] + give_beams(WAVE_BEAM)
               if beam_proof else [])
            + ["hold UP 6", "hold UP+X 2", "wait 10", sh(f"{IMG_18J}_rota_porta_vertical_abrindo"), "wait 30",
               f"expect {up_cap:06X} 0C84", f"expect {ROOM_PTR} {room[NQT]}"]   # open (measured)
            + moves(P18J_NQT_DOWN) + full(NQT, 57) + [sh(f"{IMG_18J}_rota_nqt_pe")])


def phendrana_c_to_monitor_missile(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """From the Quarantine Cave's floor at the Morph Ball tunnel's mouth: the ball through the tunnel, standing in the L1's
    chamber, through into the Quarantine Monitor, the ball through its tunnel, west into the missile at the lookout's end."""
    return (ball_through("LEFT") + [f"expect {POSE} {STAND_POSE_LEFT}", f"expect {SAMUS_X} 0025", sh(f"{IMG_18J}_rota_camara")]
            + moves("E") + phendrana_full(room, QM, 9, energy) + ball_through("LEFT") + ["hold LEFT 200"])


def phendrana_c_to_p29(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """From the Quarantine Monitor's missile back through both tunnels, up the cave's east zigzag, its R0 (wave) into the South
    Quarantine Tunnel (its 2 orbs alive on arrival, shot on the steps, no damage), up its zigzag, the R1 (wave) into the P29 (at
    its L1)."""
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    out = (["hold RIGHT 160"] + ball_through("RIGHT") + moves("D") + full(QC, 25)
           + MORPH + ["hold RIGHT 80", "wait 10"] + UNMORPH + [f"expect {POSE} {STAND_POSE}", "hold RIGHT 200"])
    for direction, mv in P18J_QC_CLIMB:
        out += hops(direction, mv)
    out += (full(QC, 9) + moves("D") + full(SQT, 9) + enemies_alive(PHENDRANA, SQT)
            + [sh(f"{IMG_18J}_rota_sqt")] + moves(P18J_SQT_DOWN) + full(SQT, 57)
            + [f"expect {ENEMY_TABLE + ENEMY_SLOT * k:06X} 0000" for k in range(2)] + [sh(f"{IMG_18J}_rota_sqt_pe")])
    for direction, mv in P18J_SQT_CLIMB:
        out += hops(direction, mv)
    return out + full(SQT, 25) + moves("D") + full(P29, 25) + [sh(f"{IMG_18J}_rota_p29")]


def phendrana_c_to_ta(room: dict, energy: int = 0x63, sh=region_shot, beam_proof: bool = True) -> list[str]:
    """From the P29's floor (its L1, or its platform: she walks east against the wall the same) east under the zigzag, up it from
    the east onto the R0 shelf; the R0 an ice door (Prime's: `beam_proof`, the Wave Beam's shot leaves it shut, the gear of round
    4 by RAM, the Ice Beam, opens it) into the Transport Access, at its L0 (phendrana_c_ta_to_cap goes on)."""
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    out = ["hold RIGHT 200"]
    for direction, mv in P18J_P29_CLIMB:
        out += hops(direction, mv)
    return (out + full(P29, 9) + [sh(f"{IMG_18J}_rota_p29_r0")]
            # the R0: an ice door (Prime's): the Wave Beam's shot leaves it shut; the gear of round 4 (+ the Ice Beam) opens it
            + (moves("D") + [f"expect {ROOM_PTR} {room[P29]}"] + give_beams(WAVE_BEAM | ICE_BEAM) if beam_proof else [])
            + moves("D") + full(TA, 9))


def phendrana_c_ta_to_cap(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """In the Transport Access from its L0: its orb shot, onto the ice pillar and off it east, facing the niche's plasma cap."""
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return (enemies_alive(PHENDRANA, TA) + [sh(f"{IMG_18J}_rota_transport_access")]
            + moves(P18J_TA) + [f"expect {ENEMY_TABLE:06X} 0000"] + full(TA, 12)
            + hops("RIGHT", [(16, 30, -60)]) + full(TA, 7) + ["hold RIGHT 60", "wait 20", "hold LEFT 2", "wait 5"])


def phendrana_c_to_ta_tank(room: dict, sh=region_shot, beam_proof: bool = True) -> list[str]:
    """Facing the Transport Access' plasma cap (`beam_proof`: the Wave and Ice shot leaves it shut, it stops her; the gear of round
    6 by RAM, the Plasma Beam): a Plasma Beam shot opens it, west into the Energy Tank in the niche."""
    lay = __import__("phendrana.layouts", fromlist=["TA_CAP"])
    cap = level_block(TA, *lay.TA_CAP[:2])
    return ([f"expect {plm_slot(PLM_HEADERS, TA_CAP_SLOT)} {TA_CAP_PLM:04X}", f"expect {cap:06X} C400"]
            + (["hold X 2", "wait 40", f"expect {cap:06X} C400", sh(f"{IMG_18J}_rota_tampa_fechada"), "hold LEFT 40", "wait 10",
                f"expect {SAMUS_X} 0125"]   # the cap stops her
               # the gear of round 6 by RAM (the Plasma Beam, round 5's: a shortcut): the cap opens, the Energy Tank in the niche
               + give_beams(PLASMA_BEAM) + ["hold RIGHT 20", "hold LEFT 2", "wait 5"] if beam_proof else [])
            + ["hold X 2", "wait 10", sh(f"{IMG_18J}_rota_tampa_abrindo"), "wait 50",
               f"expect {plm_slot(PLM_HEADERS, TA_CAP_SLOT)} 0000", f"expect {cap:06X} 0482", "hold LEFT 80"])


# specs/18l: region D of Phendrana (tools/phendrana/layouts.py, items.py; item bits $E4-$E6, red door bits $C4-$C5). The walks are
# MAGMOOR_MOVES strings found in the emulator (scratchpad s18l/scripts: seg.py, fight.py's beam search: no energy lost, the enemies
# dead first), from the round-3 gear of phendrana_up; they hold for these exact entries.
IMG_18L = "build/tests/18l"   # the photos of the region D tests (specs/img/18l-* are copies of some)
OBS, SAVE_D = "phendrana_observatory", "phendrana_save_station_d"
WTE, WT, CT, ET = ("phendrana_west_tower_entrance", "phendrana_west_tower", "phendrana_control_tower", "phendrana_east_tower")
ALE, AETHER, RCA, RC, PIKE = ("phendrana_aether_lab_entryway", "phendrana_research_lab_aether", "phendrana_research_core_access",
                              "phendrana_research_core", "phendrana_pike_access")
SAVE_D_RED_BIT, WT_RED_BIT = 0xC4, 0xC5   # the epic's red door bits: the Observatory's R1; the WTE <-> West Tower link (both sides)
SUPERS, MAX_SUPERS = "7E09CA", "7E09CC"
P18L_HYDRA = "DgD"                  # the Hydra from its L0: off the west slab, up the zigzag onto the east slab, its R0 (wave)
P18L_OBS_CLIMB = "GGxGXXR"          # the Observatory from the L0 shelf to the east cliff's top, against the projector's wall
P18L_OBS_DOWN = "RygGR"             # from the row-16 ledge (out of the tunnel) down to the floor and east to the R1's cap
P18L_TO_SAVE_D = "RRRRRRRRRRR"      # the Observatory from the L1 (door_teleport) east along the floor to the R1's cap


P18L_SAVE_D_BACK = "EE"            # Save Station D west through its L0 back into the Observatory (at the R1)
P18L_TO_WTE = "EE"                  # the Observatory from the R1 west along the floor through the L1 (wave) into the WTE
P18L_WT = "EEE"                     # the West Tower from the R0 shelf down the zigzag, west through the L1 (wave)
P18L_CT_DOWN, P18L_CT_OUT = "LLLLLLLLLL", "DD"   # the Control Tower: off the R0 shelf down to the floor; east through the R1
P18L_ET = "DDD"                     # the East Tower from the L0 shelf down to the floor, east through the R1 (wave)
P18L_ALE = "ruaRXR"                 # the Aether Lab Entryway: its orb shot as it comes down (no damage)
P18L_AETHER_FIGHT = "GXGGGRLGLLlcc"   # the Aether: off the slab's east end down to the lower lab, its Metroid shot (no damage)
P18L_AETHER_TANK = "LLLL"           # west to the empty tank's foot
P18L_AETHER_OUT = "RRRx"            # from the missile east, up onto the tank (then "wait 20" and DD: the R1, the RCA's R0)
P18L_RC_TOP = "XRRXRscR"            # the Research Core over the core: the Metroid that comes up shot from its top
P18L_RC_DOWN = "hccRIGLsL"          # down the shaft, the second Metroid shot
P18L_RC_OUT = "rcIII"               # the third shot, west under the core to the L1 (ice)
PHENDRANA_D_SCREENS = [("phendrana_observatory_access", 0, 0), ("phendrana_observatory_access", 2, 0), (OBS, 0, 0),
                       (OBS, 2, 0), (OBS, 2, 1), (OBS, 0, 1), (SAVE_D, 0, 0), (WTE, 0, 0), (WT, 1, 0), (WT, 0, 1),
                       (CT, 3, 0), (CT, 3, 1), (ET, 0, 0), (ET, 1, 1), (ALE, 0, 0), (AETHER, 0, 0), (AETHER, 2, 1),
                       (AETHER, 0, 1), (RCA, 0, 0), (RCA, 1, 0), (RC, 0, 0), (RC, 1, 1), (RC, 0, 1), (PIKE, 1, 0)]


def phendrana_route_d(m: dict, room: dict) -> list[str]:
    """specs/18l, phendrana_regiao_d_rota: up to Phendrana's P0 (phendrana_up: shortcuts, the gear of round 3), into the Research
    Lab Hydra by its L0 (door_teleport from the Hydra Lab Entryway: phendrana_regiao_b_rota walks there); then WALKING region D:
    the Hydra's R0 (wave, a door since this spec) into the Observatory Access and the Observatory; up its zigzags onto the east
    cliff, the ball under the projector's wall, a bomb breaks the bomb block (Prime's bomb slot), the SUPER MISSILE in the chamber
    (its message, bit $E4, 5 of capacity and ammunition); down to the R1, a red door: SELECT twice (the super missiles), ONE super
    missile opens it (bit $C4; 4 left, the missiles untouched): Save Station D, and back; west through the L1 (wave) into the
    West Tower Entrance, its red door opened with 6 missiles (bit $C5), the West Tower, the Control Tower (snow falling), the East
    Tower; the Aether Lab Entryway's orb alive on arrival and shot, no damage; the Research Lab Aether's Metroid alive on
    arrival (the copy: 100 health, no latch) and shot dead, no damage; its Energy Tank on the empty tank (bit $E5, 199) and its
    missile (bit $E6, 15); the Research Core Access, the Research Core's 3 Metroids alive on arrival, shot dead round the core with
    no damage; the L1 an ice door: the Wave Beam's shot leaves it shut, the gear of round 4 by RAM (the Ice Beam: a shortcut)
    opens it: the Pike Access; the explored bits and the pause map."""
    out = (phendrana_up(m, room, "rota_d") + door_teleport(m, HLE, HYDRA) + ["wait 200"] + phendrana_arrive(room, HYDRA, 9)
           + phendrana_d_to_super(room) + ["wait 120", f"shot {IMG_18L}_rota_super_missile.png"] + P18F_DISMISS
           + [phendrana_bit(10), f"expect {SUPERS} 0005", f"expect {MAX_SUPERS} 0005", f"expect {MISSILES} 000A",
              f"expect {GAME_STATE} 0008", f"shot {IMG_18L}_rota_hud.png"] + phendrana_d_to_save_d_door(room)
           # down to the R1's red door: one super missile opens it
           + ["wait 30", "hold SELECT 2", "wait 10", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0002", "hold RIGHT 2",
              "hold RIGHT+X 2", "wait 10", f"shot {IMG_18L}_rota_super_disparo.png", "wait 50", f"expect {SUPERS} 0004",
              f"expect {MISSILES} 000A", red_door_bit(SAVE_D_RED_BIT), f"shot {IMG_18L}_rota_super_porta.png",
              "poke 7E09D2 00", "wait 10", "hold RIGHT 90", "wait 160"] + phendrana_d_to_wte_door(room)
           + phendrana_red_door(room, WTE, "LEFT", WT, 10, f"{IMG_18L}_rota_west_tower.png", WT_RED_BIT)
           + phendrana_d_to_aether_tank(room) + ["wait 60", f"shot {IMG_18L}_rota_energy_tank.png"] + P18F_DISMISS
           + [phendrana_bit(11), f"expect {MAX_ENERGY} 00C7", f"expect {HEALTH} 00C7", "hold LEFT 120", "wait 60",
              f"shot {IMG_18L}_rota_missil.png"] + P18F_DISMISS
           + [phendrana_bit(12), f"expect {MAX_MISSILES} 000F", f"expect {GAME_STATE} 0008"] + phendrana_d_to_core(room, 199)
           # the L1: an ice door (Prime's): the Wave Beam's shot leaves it shut; the gear of round 4 (+ the Ice Beam) opens it
           + moves("E") + phendrana_arrive_e(room, RC, 25, 199) + [f"shot {IMG_18L}_rota_porta_de_gelo.png"]
           + give_beams(WAVE_BEAM | ICE_BEAM) + moves("E") + phendrana_arrive_e(room, PIKE, 9, 199)
           + [f"shot {IMG_18L}_rota_pike_access.png"])
    return (out + [explored_at(*screen) for screen in PHENDRANA_D_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(PHENDRANA, PHENDRANA_D_SCREENS, "phendrana_d") + [f"shot {IMG_18L}_rota_mapa.png", "hold START 10",
                                                                            "wait 200"])


# specs/18n: the walks of phendrana_regiao_d_rota as pieces shared with the full chain (each ends walking into an item, or at
# the place it names): `energy` checked at each arrival, `sh` the photo lines (region_shot: the test's names)
def phendrana_d_to_super(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """From the Research Lab Hydra's L0: the Hydra's R0 (wave) into the Observatory Access and the Observatory; up its zigzags
    onto the east cliff, the ball under the projector's wall, a bomb breaks the bomb block (Prime's bomb slot), rolling into the
    chamber: into the Super Missile."""
    lay = __import__("phendrana.layouts", fromlist=["OBS_BOMB"])
    bomb = level_block(OBS, *lay.OBS_BOMB)
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return (moves(P18L_HYDRA) + full("phendrana_observatory_access", 9) + moves("DD")
            + full(OBS, 9) + [sh(f"{IMG_18L}_rota_observatory")]
            # the east cliff's top, against the projector's wall; the ball, a bomb, into the chamber: the Super Missile
            + moves(P18L_OBS_CLIMB) + full(OBS, 9) + [f"expect {SAMUS_X} 023B", f"expect {bomb:06X} F058"]
            + MORPH + [f"expect {POSE} {BALL_POSE}", "hold RIGHT 14", "wait 10", "hold X 2", "wait 90",
                       f"expect {bomb:06X} 00FF", sh(f"{IMG_18L}_rota_tunel"), "hold RIGHT 100"])


def phendrana_d_to_save_d_door(room: dict, energy: int = 0x63) -> list[str]:
    """From the Super Missile out of the chamber, down to the Observatory's floor and east to the R1's red cap (Save Station D's)."""
    return (["hold LEFT 100", "wait 20"] + UNMORPH + [f"expect {POSE} {STAND_POSE_LEFT}"]
            + moves(P18L_OBS_DOWN) + phendrana_full(room, OBS, 25, energy) + [f"expect {SAMUS_X} 02D6"])


def phendrana_d_to_wte_door(room: dict, energy: int = 0x63) -> list[str]:
    """From Save Station D (in through the red door) back into the Observatory, west through the L1 (wave) into the West Tower
    Entrance, against its red door (the West Tower's)."""
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return (full(SAVE_D, 9) + moves(P18L_SAVE_D_BACK) + full(OBS, 25) + moves(P18L_TO_WTE) + full(WTE, 9)
            + ["hold LEFT 80", "wait 20"])


def phendrana_d_to_aether_tank(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """From the West Tower (in through the red door) down its zigzag, the Control Tower (snow falling), the East Tower, the Aether
    Lab Entryway's orb shot (no damage), the Research Lab Aether's Metroid shot dead (no damage), onto the empty tank: into the
    Energy Tank."""
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return (full(WT, 9) + moves(P18L_WT) + full(CT, 9)
            + [f"expect {WATER_FX_TYPE} 0008", sh(f"{IMG_18L}_rota_control_tower")]
            + moves(P18L_CT_DOWN) + full(CT, 25) + moves(P18L_CT_OUT) + full(ET, 9)
            + moves(P18L_ET) + full(ALE, 9) + enemies_alive(PHENDRANA, ALE)
            + [sh(f"{IMG_18L}_rota_ale")] + moves(P18L_ALE) + [f"expect {ENEMY_TABLE:06X} 0000"]
            + full(ALE, 9)
            # the Research Lab Aether: its Metroid, its Energy Tank and missile
            + moves("D") + full(AETHER, 9) + enemies_alive(PHENDRANA, AETHER)
            + [sh(f"{IMG_18L}_rota_aether")] + moves(P18L_AETHER_FIGHT) + [f"expect {ENEMY_TABLE:06X} 0000"]
            + full(AETHER, 25) + [sh(f"{IMG_18L}_rota_aether_baixo")] + moves(P18L_AETHER_TANK) + moves("Y"))


def phendrana_d_to_core(room: dict, energy: int, sh=region_shot) -> list[str]:
    """From the Research Lab Aether's missile (all of `energy` after its Energy Tank) east, up onto the tank, the R1 into the
    Research Core Access and the Research Core: its 3 Metroids shot dead round the core with no damage, to the floor at its L1
    (an ice door: Prime's)."""
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return (moves(P18L_AETHER_OUT) + ["wait 20"] + moves("DD") + full(RCA, 9)
            # the Research Core: its 3 Metroids
            + moves("DD") + full(RC, 9) + enemies_alive(PHENDRANA, RC)
            + [sh(f"{IMG_18L}_rota_research_core")] + moves(P18L_RC_TOP)
            + [f"expect {HEALTH} {energy:04X}", sh(f"{IMG_18L}_rota_metroid")] + moves(P18L_RC_DOWN) + moves(P18L_RC_OUT)
            + [f"expect {ENEMY_TABLE + ENEMY_SLOT * k:06X} 0000" for k in range(3)] + full(RC, 25))


def red_door_bit(bit: int) -> str:
    return f"expectbit {0x7ED8B0 + bit // 8:06X} {1 << (bit % 8):02X}"


def phendrana_save_d(m: dict, room: dict) -> list[str]:
    """specs/18l, phendrana_save_station_d: up to Phendrana's P0 (phendrana_up), into the Observatory by its L1 (door_teleport from
    the West Tower Entrance: phendrana_regiao_d_rota walks there), WALKING east along its floor to the R1, a red door on the
    Observatory's side (Prime's missile shield): 6 missiles open it (its bit $C4), into Save Station D (P33, the labs' look). Samus on
    the pedestal, a marker in the saved data (game hours 7), YES: load station 3 of area 4, its used-station bit ($7ED900 bit 3);
    paused, the map. Game over: the area-select screen picks area 4, station 3; continue: back on Save Station D's pedestal, area 4,
    the marker, the red door's bit kept."""
    st = PHENDRANA.load_stations[3]
    out = (phendrana_up(m, room, "save_d") + door_teleport(m, WTE, OBS) + ["wait 200"] + phendrana_arrive(room, OBS, 25)
           + moves(P18L_TO_SAVE_D) + phendrana_arrive(room, OBS, 25)
           + phendrana_red_door(room, OBS, "RIGHT", SAVE_D, 10, f"{IMG_18L}_save_sala.png", SAVE_D_RED_BIT) + poke16(0x7E09E0, 7))
    for addr, v in ((0x7E0AF6, st.x), (0x7E0B10, st.x), (0x7E0AFA, st.y), (0x7E0B14, st.y)):
        out += poke16(addr, v)
    return (out + ["hold RIGHT 1", "wait 180", f"shot {IMG_18L}_save_pergunta.png", "hold A 2", "wait 300", "hold A 2",
                   "wait 200", f"expect {LOAD_STATION} 0003", f"expect {AREA} 0004", f"expectbit {USED_STATIONS_AREA4} 08",
                   f"expect {GAME_STATE} 0008", f"shot {IMG_18L}_save_salvo.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}", f"shot {IMG_18L}_save_mapa.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} 0008",
                   "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
                   "hold A 2", "wait 300"]
            + area_select_shows_after(PHENDRANA.number, st.index, (TALLON.number,), f"{IMG_18L}_save_tela_de_area.png")
            + ["hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0004", f"expect {ROOM_PTR} {room[st.room]}",
               f"expect {LOAD_STATION} 0003", f"expect {GAME_HOURS} 0007", f"expect 7E0AF6 {st.x:04X}",
               red_door_bit(SAVE_D_RED_BIT), f"shot {IMG_18L}_save_continue.png", explored_at(SAVE_D, 0, 0),
               explored_at(OBS, 2, 1)])


# specs/18m: region E of Phendrana (tools/phendrana/layouts.py, items.py; item bits $E7-$EA). The walks are MAGMOOR_MOVES strings
# and inputs found in the emulator (scratchpad s18m/scripts: seg.py's beam search, no energy lost; sjsearch.py the Space Jump's
# spins under water), from the gear of round 3 (phendrana_up) with the Ice Beam (round 4: the region is behind the ice doors);
# they hold for these exact entries. Shortcuts (counted): into the Frozen Pike by door_teleport from the Transport Access
# (phendrana_regiao_c_rota walks there), the gear by RAM (the Ice Beam of round 4; the Plasma Beam and the Power Bomb of round 6
# for the Storage Cave's doors and the Security Cave's blocks; the Gravity Suit of round 5 for the Gravity Chamber's ledge).
IMG_18M = "build/tests/18m"   # the photos of the region E tests (specs/img/18m-* are copies of some)
FROZEN_PIKE, FCA, FROST, SAVE_C = ("phendrana_frozen_pike", "phendrana_frost_cave_access", "phendrana_frost_cave",
                            "phendrana_save_station_c")
HCA, HUNTER, UET, LET = ("phendrana_hunter_cave_access", "phendrana_hunter_cave", "phendrana_upper_edge_tunnel",
                         "phendrana_lower_edge_tunnel")
CHAMBER, LAKE, EDGE, GRAV = ("phendrana_chamber_access", "phendrana_lake_tunnel", "phendrana_edge", "phendrana_gravity_chamber")
STORAGE, SECURITY = "phendrana_storage_cave", "phendrana_security_cave"
P18M_PIKE = "DDD"                   # the Frozen Pike from the L0 slab: off it, onto the slab of row 26, east through the R1 (wave)
P18M_FCA = "GDGGGGGGXXD"            # the Frost Cave Access over the gully (its 2 Beetles and zoomer left below), its R0 (wave)
P18M_FROST_LAKE = "xxxx"            # the Frost Cave from the L2 east into the dry lake, before its missile
P18M_FROST_UP = "GXIgXD"            # out of the lake, up the east zigzag onto the R1 shelf, its wave door
P18M_EDGE_DOWN = "rGiXIxYx"         # Phendrana's Edge from the L1 shelf down the cliffs to the floor (row 58)
P18M_EDGE_R3 = "RRRRRRRRRRRR"       # east along the floor to the R3's plasma cap
P18M_STORAGE_OUT = "fpsE"           # the Storage Cave: facing west, a shot at its cap, out
P18M_EDGE_UP = "yILIGrYgG"          # from the R3 west and up the low zigzag (53, 48, 43) onto the east rock (row 42)
P18M_INTO_SECURITY = ["poke 7E09D2 00", "hold LEFT 30", "hold RIGHT 2", "wait 5", "hold X 2", "wait 30", "hold RIGHT 100",
                      "wait 200"]   # out of the R2 chamber's ball, back to the beam: a shot at the R2's door, through it
P18M_PIKE_MID, P18M_PIKE_DOWN = "DD", "LLLLLRRLRRLLRRRL"   # the Pike: onto the slab of row 26; down the lower zigzag
P18M_PIKE_R3 = "RRRRRRRRRRRD"       # east along the floor through the R3 (wave) into the Hunter Cave Access
P18M_HCA = "RRRRRRRRRRRRRRRRRRRRRRRRxRRRRRRRRRRRRRRD"   # through the dry lake (a jump out of it), the R0 (wave)
P18M_HUNTER = "DgD"                 # the Hunter Cave from the L1 east over the basin, the R1 (wave) into the Chamber Access
P18M_DOWN_SHOT = ["hold A 12", "hold A+DOWN 6", "hold DOWN+X 2"]   # a jump, aiming down in the air, a shot at the floor
P18M_STAIR_HOP = ["hold LEFT 20", "hold LEFT+A 50", "hold LEFT 30", "wait 60"]   # one 3-row step west under water, no suit
P18M_SPACE_JUMP = [("RIGHT+A", 30), ("RIGHT", 8), ("RIGHT+A", 30), ("RIGHT", 24), ("RIGHT+A", 30), ("RIGHT", 8),
                   ("RIGHT+A", 20), ("RIGHT", 16), ("RIGHT+A", 30), ("RIGHT", 12), ("RIGHT+A", 30), ("RIGHT", 8),
                   ("RIGHT+A", 30), ("RIGHT", 8)]   # with the Gravity Suit, from the stair's top over the water to the ledge
P18M_GRAV_OUT = "IiiiyYE"           # off the ledge west, up the stair (as on land, with the suit), the L0 (wave)
P18M_LAKE = "YiIiY"                 # the Lake Tunnel from the R0 west onto the ceiling door's platform (its orb left alive)
P18M_RISE = ["hold UP 10", "hold UP+X 2", "wait 40", "hold A 30", "wait 200"]   # the cap above shot open, a jump up through
P18M_HUNTER_UP = "GXygXD"           # the Hunter Cave out of the basin, up the zigzag onto the R0 shelf (wave)
P18M_LET = "xxXxRRXD"               # the Lower Edge Tunnel past its 2 orbs (no damage), the R0 into Phendrana's Edge
PHENDRANA_E_SCREENS = [(FROZEN_PIKE, 0, 0), (FROZEN_PIKE, 2, 1), (FCA, 0, 0), (FCA, 5, 0), (FROST, 0, 2), (FROST, 1, 2), (FROST, 2, 1),
                       (UET, 0, 0), (UET, 2, 0), (EDGE, 0, 1), (EDGE, 0, 3), (EDGE, 1, 3), (STORAGE, 0, 0), (EDGE, 1, 2),
                       (SECURITY, 0, 0), (SECURITY, 1, 0)]
PHENDRANA_E_WATER_SCREENS = [(FROZEN_PIKE, 1, 3), (FROZEN_PIKE, 2, 3), (HCA, 0, 0), (HCA, 5, 0), (HUNTER, 0, 1), (HUNTER, 2, 1),
                             (CHAMBER, 0, 0), (GRAV, 0, 0), (GRAV, 2, 1), (GRAV, 2, 0), (LAKE, 1, 0), (LAKE, 0, 0),
                             (HUNTER, 1, 1), (HUNTER, 2, 0), (LET, 0, 0), (LET, 2, 0)]


def phendrana_pike(m: dict, room: dict, tag: str) -> list[str]:
    """Up to Phendrana's P0 (phendrana_up: the gear of round 3), the Ice Beam by RAM (round 4: a shortcut), into the Frozen Pike
    by its L0 (door_teleport from the Transport Access: phendrana_regiao_c_rota walks there; snow falling as in Prime)."""
    return (phendrana_up(m, room, tag) + give_beams(WAVE_BEAM | ICE_BEAM) + door_teleport(m, TA, FROZEN_PIKE) + ["wait 200"]
            + phendrana_arrive(room, FROZEN_PIKE, 9) + [f"expect {WATER_FX_TYPE} 0008"])


def phendrana_route_e(m: dict, room: dict) -> list[str]:
    """specs/18m, phendrana_regiao_e_rota: into the Frozen Pike (phendrana_pike: shortcuts, the gear of round 4); then WALKING
    region E's dry part: the Pike's slabs, its R1 (wave) into the Frost Cave Access (its 2 Beetles and zoomer alive, no damage),
    the Frost Cave: the missile in the dry lake (bit $E7, 15), up the east zigzag, the Upper Edge Tunnel, Phendrana's Edge down to
    its floor; the R3 a plasma door: the Wave Beam's shot leaves it shut, the Plasma Beam of round 6 by RAM (a shortcut) opens
    it: the Storage Cave (empty: the artifact is out), and back; up the low zigzag onto the east rock, the ball against the
    tunnel's power bomb block (Prime's Morph Ball door: the Morph Ball and the Power Bomb, round 6's by RAM): a power bomb breaks
    it, into the R2 door's chamber, standing, the door; the Security Cave: its tunnel's block broken the same way, the POWER BOMB
    EXPANSION (bit $EA, 5 more); the energy 99 all the way; the explored bits and the pause map."""
    out = (phendrana_pike(m, room, "rota_e") + phendrana_e_to_frost_missile(room) + ["wait 120", f"shot {IMG_18M}_rota_missil.png"]
           + P18F_DISMISS + [phendrana_bit(13), f"expect {MAX_MISSILES} 000F", f"expect {GAME_STATE} 0008"]
           + phendrana_e_to_edge(room) + phendrana_e_to_storage(room) + phendrana_e_to_security(room)
           + ["wait 120", f"shot {IMG_18M}_rota_power_bomb.png"] + P18F_DISMISS
           + [phendrana_bit(16), f"expect {MAX_POWER_BOMBS} 000A", f"expect {GAME_STATE} 0008", f"expect {HEALTH} 0063"])
    return (out + [explored_at(*screen) for screen in PHENDRANA_E_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(PHENDRANA, PHENDRANA_E_SCREENS, "phendrana_e") + [f"shot {IMG_18M}_rota_mapa.png", "hold START 10",
                                                                            "wait 200"])


# specs/18n: the walks of phendrana_regiao_e_rota and phendrana_regiao_e_agua as pieces shared with the full chain (each ends
# walking into an item, or at the place it names): `energy` checked at each arrival, `sh` the photo lines (region_shot: the
# test's names); `beam_proof`: the test's shots with less than the beam a door needs (beams by RAM: the chain never gives a beam)
def phendrana_e_to_frost_missile(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """From the Frozen Pike's L0 slab: off it, onto the slab of row 26, east through the R1 (wave) into the Frost Cave Access
    (its 2 Beetles and zoomer alive, no damage), over its gully, the Frost Cave: east into the dry lake, into its missile."""
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return ([sh(f"{IMG_18M}_rota_pike")] + moves(P18M_PIKE)
            + full(FCA, 9) + enemies_alive(PHENDRANA, FCA) + [sh(f"{IMG_18M}_rota_fca")]
            + moves(P18M_FCA) + full(FROST, 41) + moves(P18M_FROST_LAKE) + full(FROST, 43) + ["hold RIGHT 20"])


def phendrana_e_to_edge(room: dict, energy: int = 0x63, sh=region_shot, up: str = P18M_FROST_UP) -> list[str]:
    """From the Frost Cave's missile out of the lake, up the east zigzag onto the R1 shelf (`up`), its wave door, the Upper Edge
    Tunnel, Phendrana's Edge down its cliffs to the floor and east along it to the R3's plasma cap."""
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return (moves(up) + full(UET, 9) + moves("DD") + full(EDGE, 25)
            + [f"expect {WATER_FX_TYPE} 0008", sh(f"{IMG_18M}_rota_edge")]
            + moves(P18M_EDGE_DOWN) + full(EDGE, 57) + moves(P18M_EDGE_R3))


def phendrana_e_to_storage(room: dict, energy: int = 0x63, sh=region_shot, beam_proof: bool = True) -> list[str]:
    """At Phendrana's Edge's R3, a plasma door (`beam_proof`: the Wave Beam's shot leaves it shut; the Plasma Beam of round 6 by
    RAM, a shortcut): the Plasma Beam opens it: the Storage Cave (empty: the artifact is out), and back out."""
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return ((moves("D") + [f"expect {ROOM_PTR} {room[EDGE]}", sh(f"{IMG_18M}_rota_porta_de_plasma")]   # the Wave Beam: shut
             + give_beams(WAVE_BEAM | PLASMA_BEAM) if beam_proof else [])
            + moves("D") + full(STORAGE, 9)
            + [sh(f"{IMG_18M}_rota_storage")] + moves(P18M_STORAGE_OUT) + full(EDGE, 57))


def phendrana_e_to_security(room: dict, energy: int = 0x63, sh=region_shot, power_bombs: int = 0, lay_bomb=None) -> list[str]:
    """From Phendrana's Edge's R3 west and up the low zigzag onto the east rock; the ball against the tunnel's power bomb block
    (Prime's Morph Ball door): a power bomb breaks it, into the R2 door's chamber, standing, the door; the Security Cave: its
    tunnel's block broken the same way, into the POWER BOMB EXPANSION. `power_bombs`: what she has before (0: the test's 5 of
    round 6 given by RAM, a shortcut); `lay_bomb`: the lines laying one (LAY_POWER_BOMB; specs/18n: the chain's HUD)."""
    lay = __import__("phendrana.layouts", fromlist=["EDGE_PB"])
    edge_pb, sec_pb = level_block(EDGE, *lay.EDGE_PB), level_block(SECURITY, *lay.SEC_PB_BLOCK)
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    have = power_bombs or 5
    return (moves(P18M_EDGE_UP) + full(EDGE, 41)
            # the power bomb blocks of the Morph Ball door (the Power Bomb of round 6 by RAM: a shortcut)
            + (poke16(0x7E09CE, 5) + poke16(0x7E09D0, 5) if not power_bombs else [])
            + ["wait 10", "hold RIGHT 40", "wait 10", f"expect {edge_pb:06X} {POWER_BOMB_BLOCK}", sh(f"{IMG_18M}_rota_tunel")]
            + MORPH + [f"expect {POSE} {BALL_POSE}"] + (lay_bomb() if lay_bomb else LAY_POWER_BOMB)
            + [f"expect {edge_pb:06X} 00FF", f"expect {POWER_BOMBS} {have - 1:04X}", "hold RIGHT 90", "wait 10"] + UNMORPH
            + ["wait 10", f"expect {POSE} {STAND_POSE}", f"expect {SAMUS_X} 01DB", sh(f"{IMG_18M}_rota_camara")]
            + P18M_INTO_SECURITY + full(SECURITY, 9) + [f"expect {WATER_FX_TYPE} 0008"]
            + ["hold RIGHT 40", "wait 10", f"expect {sec_pb:06X} {POWER_BOMB_BLOCK}"] + MORPH + ["hold RIGHT 60", "wait 10"]
            + (lay_bomb() if lay_bomb else LAY_POWER_BOMB) + [f"expect {sec_pb:06X} 00FF", f"expect {POWER_BOMBS} {have - 2:04X}",
                                                     "hold RIGHT 90"])


def phendrana_water(m: dict, room: dict) -> list[str]:
    """specs/18m, phendrana_regiao_e_agua: into the Frozen Pike (phendrana_pike: shortcuts, the gear of round 4, no Gravity Suit);
    then WALKING down the Pike to its R3, the Hunter Cave Access (its dry lake), the Hunter Cave, the Chamber Access: the floor
    door's cap a vertical wave door (shut to the Power Beam, a shot down in the air with the Wave Beam opens it); down into the
    flooded Gravity Chamber (the water FX, type 6, the whole room: the user's decision 5): WITHOUT THE GRAVITY SUIT down to its
    floor, the Gravity Suit's missile (bit $E8, 15), back up the stair of 3-row steps with the underwater jump (the model's 3
    blocks) to the rock; the Gravity Suit by RAM (round 5's: a shortcut): the Space Jump over the water onto the east ledge, its
    missile (bit $E9, 20); the L0 into the Lake Tunnel (its orb alive), up through its ceiling door (wave) into the Hunter Cave,
    the Lower Edge Tunnel (its 2 orbs, no damage), Phendrana's Edge; the energy 99 all the way (the water does no harm); the
    explored bits and the pause map."""
    eq = VARIA_EQUIPMENT | SPACE_JUMP_EQUIPMENT | MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT
    out = (phendrana_pike(m, room, "agua") + phendrana_e_to_chamber(room)
           + [f"expect 7E09A2 {eq:04X}", f"shot {IMG_18M}_agua_chegada.png"] + phendrana_e_to_low_missile()
           + ["wait 120", f"shot {IMG_18M}_agua_missil.png"] + P18F_DISMISS
           + [phendrana_bit(14), f"expect {MAX_MISSILES} 000F", f"expect {GAME_STATE} 0008"] + phendrana_e_up_the_stair(room)
           # the Gravity Suit by RAM (round 5): the Space Jump under water, onto the ledge, its missile
           + poke16(0x7E09A2, eq | GRAVITY_SUIT) + poke16(0x7E09A4, eq | GRAVITY_SUIT) + ["wait 10"]
           + phendrana_e_to_high_missile() + ["wait 120", f"shot {IMG_18M}_agua_borda.png"]
           + P18F_DISMISS + [phendrana_bit(15), f"expect {MAX_MISSILES} 0014", f"expect {GAME_STATE} 0008"]
           + moves(P18M_GRAV_OUT) + phendrana_e_lake_to_edge(room) + [f"expect {HEALTH} 0063"])
    return (out + [explored_at(*screen) for screen in PHENDRANA_E_WATER_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(PHENDRANA, PHENDRANA_E_WATER_SCREENS, "phendrana_e_agua")
            + [f"shot {IMG_18M}_agua_mapa.png", "hold START 10", "wait 200"])


def phendrana_e_to_chamber(room: dict, energy: int = 0x63, sh=region_shot, beam_proof: bool = True,
                           mid: list[str] | None = None) -> list[str]:
    """From the Frozen Pike's L0 slab down the Pike to its R3, the Hunter Cave Access (its dry lake), the Hunter Cave, the
    Chamber Access: the floor door's cap a vertical wave door (`beam_proof`: shut to the Power Beam), a shot down in the air with
    the Wave Beam opens it; down into the flooded Gravity Chamber (the water FX, type 6). `mid`: the moves onto the Pike's slab of
    row 26 (P18M_PIKE_MID; specs/18n: the chain's, CHAIN_PIKE_MID)."""
    cap = level_block(CHAMBER, 6, 13)   # the B0 door's cap (its first block)
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return ((moves(P18M_PIKE_MID) if mid is None else mid) + full(FROZEN_PIKE, 25) + moves(P18M_PIKE_DOWN)
            + full(FROZEN_PIKE, 57) + moves(P18M_PIKE_R3) + full(HCA, 9) + moves(P18M_HCA)
            + full(HUNTER, 25) + [sh(f"{IMG_18M}_agua_hunter")] + moves(P18M_HUNTER)
            + full(CHAMBER, 9)
            # the floor door's wave cap: the Power Beam's shot down leaves it shut, the Wave Beam's opens it
            + ["hold RIGHT 24", "wait 30", f"expect {cap:06X} C7FA"]
            + (give_beams(0) + P18M_DOWN_SHOT + ["wait 60", f"expect {cap:06X} C7FA", f"expect {ROOM_PTR} {room[CHAMBER]}"]
               + give_beams(WAVE_BEAM | ICE_BEAM) if beam_proof else [])
            + P18M_DOWN_SHOT + ["wait 6", sh(f"{IMG_18M}_agua_porta_de_chao"), "wait 254"]
            + full(GRAV, 5) + [f"expect {WATER_FX_TYPE} 0006"])


def phendrana_e_to_low_missile() -> list[str]:
    """From the Gravity Chamber's ceiling door down to its floor, WITHOUT THE GRAVITY SUIT, into the Gravity Suit's missile."""
    return moves("R" * 30) + ["hold LEFT 70"]


def phendrana_e_up_the_stair(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """From the low missile back up the stair of 3-row steps with the underwater jump (no suit: the model's 3 blocks) to the rock."""
    return (P18M_STAIR_HOP * 6 + phendrana_full(room, GRAV, 10, energy) + [sh(f"{IMG_18M}_agua_escada")])


def phendrana_e_to_high_missile() -> list[str]:
    """With the Gravity Suit, from the stair's top the Space Jump over the water onto the east ledge, into its missile."""
    return [f"hold {d} {n}" for d, n in P18M_SPACE_JUMP] + ["hold RIGHT 20"]


def phendrana_e_lake_to_edge(room: dict, energy: int = 0x63) -> list[str]:
    """From the Gravity Chamber's L0 (out of it) the Lake Tunnel (its orb alive) onto the ceiling door's platform, up through its
    wave door into the Hunter Cave, up the zigzag onto the R0 shelf, the Lower Edge Tunnel (its 2 orbs, no damage), into
    Phendrana's Edge (its floor)."""
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return (phendrana_e_lake_to_hunter(room, energy) + [f"shot {IMG_18M}_agua_subida.png"] + moves(P18M_HUNTER_UP)
            + full(LET, 9) + enemies_alive(PHENDRANA, LET) + moves(P18M_LET) + full(EDGE, 57))


def phendrana_e_lake_to_hunter(room: dict, energy: int = 0x63, walk: str = P18M_LAKE) -> list[str]:
    """From the Gravity Chamber's L0 (out of it) the Lake Tunnel (its orb alive) onto the ceiling door's platform (`walk`), up
    through its wave door into the Hunter Cave."""
    full = lambda key, feet: phendrana_full(room, key, feet, energy)   # noqa: E731
    return full(LAKE, 9) + enemies_alive(PHENDRANA, LAKE) + moves(walk) + full(LAKE, 5) + P18M_RISE + full(HUNTER, 28)


def phendrana_save_c(m: dict, room: dict) -> list[str]:
    """specs/18m, phendrana_save_station_c: up to Phendrana's P0 (phendrana_up), the Ice Beam by RAM, into the Frost Cave by its
    L1 (door_teleport from Save Station C: phendrana_regiao_e_rota walks the cave), WALKING west through the L1 (a wave door on
    both sides) into Save Station C (P45, snow falling as in Prime). Samus on the pedestal, a marker in the saved data (game
    hours 7), YES: load station 4 of area 4, its used-station bit ($7ED900 bit 4); paused, the map. Game over: the area-select
    screen picks area 4, station 4; continue: back on Save Station C's pedestal, area 4, the marker."""
    st = PHENDRANA.load_stations[4]
    out = (phendrana_up(m, room, "save_c") + give_beams(WAVE_BEAM | ICE_BEAM) + door_teleport(m, SAVE_C, FROST) + ["wait 200"]
           + phendrana_arrive(room, FROST, 25) + moves("fpsE") + phendrana_arrive(room, SAVE_C, 9)
           + [f"expect {WATER_FX_TYPE} 0008", f"shot {IMG_18M}_save_sala.png"] + poke16(0x7E09E0, 7))
    for addr, v in ((0x7E0AF6, st.x), (0x7E0B10, st.x), (0x7E0AFA, st.y), (0x7E0B14, st.y)):
        out += poke16(addr, v)
    return (out + ["hold RIGHT 1", "wait 180", f"shot {IMG_18M}_save_pergunta.png", "hold A 2", "wait 300", "hold A 2",
                   "wait 200", f"expect {LOAD_STATION} 0004", f"expect {AREA} 0004", f"expectbit {USED_STATIONS_AREA4} 10",
                   f"expect {GAME_STATE} 0008", f"shot {IMG_18M}_save_salvo.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}", f"shot {IMG_18M}_save_mapa.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} 0008",
                   "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
                   "hold A 2", "wait 300"]
            + area_select_shows_after(PHENDRANA.number, st.index, (TALLON.number,), f"{IMG_18M}_save_tela_de_area.png")
            + ["hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0004", f"expect {ROOM_PTR} {room[st.room]}",
               f"expect {LOAD_STATION} 0004", f"expect {GAME_HOURS} 0007", f"expect 7E0AF6 {st.x:04X}",
               f"shot {IMG_18M}_save_continue.png", explored_at(SAVE_C, 0, 0), explored_at(FROST, 0, 1)])


# specs/18h, phendrana_sheegoth: the Sheegoth's arena (tools/chozo/bosses.py ARENAS: the Dessgeega's copy and 2 small
# Sidehoppers in the Chapel of the Elders) fought with the gear of round 3 (phendrana_up) and 30 missiles (the 10 of
# phendrana_up and region A's 4 expansions: what phendrana_regiao_a_rota ends with; the round's capacity is 85,
# validate.round_missiles); moves of MAGMOOR_MOVES found by a beam search in the emulator (scratchpad s18h/scripts/boss.py:
# the enemies' health left, the energy lost, the distance to the nearest), nothing refilled, no RAM; they hold for this exact
# entry (as 14a's)
IMG_18H = "build/tests/18h"   # the photos of the Sheegoth's test (specs/img/18h-* are copies of some)
SHEEGOTH = "phendrana_chapel_of_the_elders"
SHEEGOTH_MISSILES = 30
SHEEGOTH_SHUT = "Ls"   # a step west against the grey cap behind her and a shot at it: still shut
SHEEGOTH_INTO = "rS"   # a step east, SELECT: missiles (in pose 0, facing the screen as the door leaves her, SELECT does nothing)
SHEEGOTH_FIGHT = "RXhcRRRsXrxccsLscccs"
SHEEGOTH_ENERGY_AT_WIN = 79   # measured: the small ones' and the Sheegoth's touches (10 and 20 with the Varia Suit)
SHEEGOTH_MISSILES_AT_WIN = 22  # measured: 8 fired, a drop picked up on the way
SHEEGOTH_TO_ALTAR = "RRRRRRXR"  # from where the fight ends (x 572) east, up onto the altar into the missile
SHEEGOTH_GREY_SLOT, SHEEGOTH_PRIZE_SLOT = 39, 38   # the PLM slots of the door's grey cap (the list's first) and the prize


def sheegoth_entry(m: dict, room: dict) -> list[str]:
    """phendrana_sheegoth up to the fight: up to Phendrana's P0 (phendrana_up: shortcuts, the gear of round 3), 30 missiles by
    RAM, door_teleport into the Chapel by its L0 (from the Chapel Tunnel: the only way in); the arena alive (the 3 in their
    slots with full health, the quota 3, the bit $08 of area 4 off, the mini-boss song, the grey cap of type 3 on the L0, no
    missile); a step west into the cap and a shot at it: still in the Chapel (SHEEGOTH_SHUT); a step east and SELECT."""
    from chozo import bosses
    arena = bosses.arena_of(SHEEGOTH)
    return (phendrana_up(m, room, "sheegoth") + poke16(0x7E09C6, SHEEGOTH_MISSILES) + poke16(0x7E09C8, SHEEGOTH_MISSILES)
            + door_teleport(m, "phendrana_chapel_tunnel", SHEEGOTH) + [f"expect {ROOM_PTR} {room[SHEEGOTH]}"]
            + enemies_alive(PHENDRANA, SHEEGOTH)
            + ["expect 7E0E52 0003", "expect 7E0E50 0000", "expect 7ED82C 0000", f"expect 7E07F3 {arena.music[0]:04X}",
               f"expect 7E07F5 {arena.music[1]:04X}", f"expect {plm_slot(PLM_HEADERS, SHEEGOTH_GREY_SLOT)} C848",
               f"expect {plm_slot(PLM_HEADERS, SHEEGOTH_PRIZE_SLOT)} 0000", f"expect {HEALTH} 0063",
               f"shot {IMG_18H}_entrada.png"]
            + moves(SHEEGOTH_SHUT) + ["wait 30", f"expect {ROOM_PTR} {room[SHEEGOTH]}", f"expect {GAME_STATE} 0008",
                                     f"expect {plm_slot(PLM_HEADERS, SHEEGOTH_GREY_SLOT)} C848"]
            + moves(SHEEGOTH_INTO) + [f"expect {HUD_ITEM} 0001"])


def sheegoth_dead(room: dict) -> list[str]:
    """The Chapel in its dead state: no enemy, the area's song, the wave door's cap on the L0 (Prime's key lock), no grey cap,
    the missile taken (its PLM gone), the bit $08 on."""
    from tallon import beamdoors
    wave = beamdoors.PLM[("wave", "L")]
    return ([f"expect {ROOM_PTR} {room[SHEEGOTH]}", f"expect {ENEMY_TABLE:06X} 0000", "expectbit 7ED82C 08",
             f"expect 7E07F3 {PHENDRANA.music[0]:04X}", f"expect 7E07F5 {PHENDRANA.music[1]:04X}",
             f"expect {plm_slot(PLM_HEADERS, SHEEGOTH_GREY_SLOT)} {wave:04X}",
             f"expect {plm_slot(PLM_HEADERS, SHEEGOTH_PRIZE_SLOT)} 0000", phendrana_bit(4)])


def phendrana_sheegoth(m: dict, room: dict) -> list[str]:
    """specs/18h, phendrana_sheegoth: sheegoth_entry (the arena alive, the door shut); SHEEGOTH_FIGHT with missiles (the
    Dessgeega's shell takes no uncharged beam), nothing refilled, no RAM: the 3 dead (kill count 3), the bit $08 of area 4, the
    song stopped, the missile spawned on the altar (PLM slot 38), the grey cap opened by its own count (a blue door now: a
    shot opens it); SHEEGOTH_TO_ALTAR into the missile (bit $DE, 35 of capacity: Prime's Wave Beam's place); west out through
    the L0 into the Chapel Tunnel; back:
    the dead state (sheegoth_dead). Saved at Save Station B (door_teleport: a shortcut), game over, continue: the bits on;
    back in the Chapel: dead."""
    st = PHENDRANA.load_stations[1]
    out = sheegoth_entry(m, room) + ["# the fight (SHEEGOTH_FIGHT) starts here"]
    for i, move in enumerate(SHEEGOTH_FIGHT):
        out += MAGMOOR_MOVES[move]
        if i in (7, 12, 16):
            out += [f"shot {IMG_18H}_luta_{i:02d}.png"]
    out += (["wait 2", f"expect {KILLS} 0003"] + [f"expect {ENEMY_TABLE + ENEMY_SLOT * n:06X} 0000" for n in range(3)]
            + ["expectbit 7ED82C 08", "expect 7E07F5 0000", f"expect {HEALTH} {SHEEGOTH_ENERGY_AT_WIN:04X}",
               f"expect {MISSILES} {SHEEGOTH_MISSILES_AT_WIN:04X}", f"expect {plm_slot(PLM_HEADERS, SHEEGOTH_PRIZE_SLOT)} EEDB",
               "wait 30", f"shot {IMG_18H}_vitoria.png"]
            + moves(SHEEGOTH_TO_ALTAR) + ["wait 120", f"shot {IMG_18H}_missil.png"] + P18F_DISMISS
            + [phendrana_bit(4), f"expect {MAX_MISSILES} {SHEEGOTH_MISSILES + 5:04X}", f"expect {GAME_STATE} 0008",
               "hold LEFT 560", f"expect {plm_slot(PLM_HEADERS, SHEEGOTH_GREY_SLOT)} C848", f"shot {IMG_18H}_porta_aberta.png"]
            + moves("E") + phendrana_arrive(room, "phendrana_chapel_tunnel", 9)[:3]
            + door_teleport(m, "phendrana_chapel_tunnel", SHEEGOTH) + ["wait 60"] + sheegoth_dead(room)
            + [f"shot {IMG_18H}_morto.png"]
            + door_teleport(m, "phendrana_shorelines", "phendrana_save_station_b") + [f"poke {HEALTH} 63"])
    for addr, v in ((0x7E0AF6, st.x), (0x7E0B10, st.x), (0x7E0AFA, st.y), (0x7E0B14, st.y)):
        out += poke16(addr, v)
    return (out + ["hold RIGHT 1", "wait 180", "hold A 2", "wait 300", "hold A 2", "wait 200", f"expect {LOAD_STATION} 0001",
                   f"expect {AREA} 0004", "poke 7E09C2 00", "poke 7E09C3 00", "wait 400",
                   f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}", "hold A 2", "wait 300", "hold A 2", "wait 200"]
            + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {ROOM_PTR} {room[st.room]}", "expectbit 7ED82C 08", phendrana_bit(4)]
            + door_teleport(m, "phendrana_chapel_tunnel", SHEEGOTH) + ["wait 60"] + sheegoth_dead(room)
            + [f"shot {IMG_18H}_depois_do_continue.png"])


# specs/18k, phendrana_thardus: the Thardus' arena (tools/chozo/bosses.py ARENAS: the Bomb Torizo's copy in the Quarantine
# Cave) fought with the gear of round 3 (phendrana_up: the Wave Beam, 10 missiles; nothing refilled, no RAM); moves of
# MAGMOOR_MOVES found by a beam search in the emulator (scratchpad s18k/scripts/boss.py: its health left, the energy lost, the
# distance), from this exact entry (as 18h's)
IMG_18K = "build/tests/18k"   # the photos of the Thardus' test (specs/img/18k-* are copies of some)
THARDUS = "phendrana_quarantine_cave"
THARDUS_SHUT = "Ls"   # a step west against the L0's grey cap behind her and a shot at it: still shut
THARDUS_FIGHT = "XxXXXRXcRYsychsSsls"   # down off the shelf, shots and 2 missiles: its health 0 at the last shot
THARDUS_DEATH = 400   # frames of its death (Torizo_Instr_38 $AA:B24D sets the bit at the end of its list: measured ~370)
THARDUS_ENERGY_AT_WIN = 95   # measured: one touch (8, 4 with the Varia Suit)
THARDUS_MISSILES_AT_WIN = 8
THARDUS_L0_SLOT, THARDUS_R0_SLOT = 39, 38   # the PLM slots of the doors' grey caps (the L0's is the list's first)
# from the west cliff's foot (where the fight leaves her: walking west against it, then 200 frames east) up the east zigzag
# onto the R0's shelf: 18j's climb with the first walk measured from here (141-153 frames work: s18k/scripts/climb.py)
THARDUS_CLIMB = [("RIGHT", [(147, 30, -60)])] + P18J_QC_CLIMB[1:]


def thardus_entry(m: dict, room: dict) -> list[str]:
    """phendrana_thardus up to the fight: up to Phendrana's P0 (phendrana_up: shortcuts, the gear of round 3), door_teleport
    into the Quarantine Cave by its L0 (from the North Quarantine Tunnel); the arena alive (the Thardus in slot 0 with full
    health, the bits $04 and $10 of area 4 off, the Torizo's song set $24 (its waking track queued), the snow's colour math
    (no haze), the grey caps of type 2 on the L0 and the R0); a step west into the L0's cap and a shot at it: still in the cave (THARDUS_SHUT)."""
    from chozo import bosses
    arena, grey = bosses.arena_of(THARDUS), f"{bosses.GREY_DOOR_TORIZO:04X}"
    return (phendrana_up(m, room, "thardus") + door_teleport(m, "phendrana_north_quarantine_tunnel", THARDUS)
            + [f"expect {ROOM_PTR} {room[THARDUS]}"] + enemies_alive(PHENDRANA, THARDUS)
            + ["expect 7ED82C 0000", f"expect 7E07F3 {arena.music[0]:04X}",
               "expect 7E1986 000A",   # the snow's colour math as in the dead state (no Torizo haze: bosses.TORIZO_HAZE)
               f"expect {plm_slot(PLM_HEADERS, THARDUS_L0_SLOT)} C848", f"expect {plm_slot(PLM_HEADERS, THARDUS_R0_SLOT)} C842",
               f"expect {HEALTH} 0063", f"shot {IMG_18K}_entrada.png"]
            + moves(THARDUS_SHUT) + ["wait 30", f"expect {ROOM_PTR} {room[THARDUS]}", f"expect {GAME_STATE} 0008",
                                     f"expect {plm_slot(PLM_HEADERS, THARDUS_L0_SLOT)} C848"])


def thardus_dead(room: dict) -> list[str]:
    """The Quarantine Cave in its dead state: no enemy, the area's song, the wave doors' caps on the L0 and the R0 (Prime's
    key locks), no grey cap, the bits $04 and $10 on."""
    from tallon import beamdoors
    return ([f"expect {ROOM_PTR} {room[THARDUS]}", f"expect {ENEMY_TABLE:06X} 0000", "expectbit 7ED82C 14",
             f"expect 7E07F3 {PHENDRANA.music[0]:04X}", f"expect 7E07F5 {PHENDRANA.music[1]:04X}",
             f"expect {plm_slot(PLM_HEADERS, THARDUS_L0_SLOT)} {beamdoors.PLM[('wave', 'L')]:04X}",
             f"expect {plm_slot(PLM_HEADERS, THARDUS_R0_SLOT)} {beamdoors.PLM[('wave', 'R')]:04X}"])


def phendrana_thardus(m: dict, room: dict) -> list[str]:
    """specs/18k, phendrana_thardus: thardus_entry (the arena alive, the doors shut); THARDUS_FIGHT (the Wave Beam and 2
    missiles), nothing refilled, no RAM: its health 0, its death (THARDUS_DEATH frames), the slot empty, the bits $04 (the
    Torizo's, its own code) and $10 (the arena's) of area 4, the song stopped; walking east under the zigzag and up it onto the
    R0's shelf, the R0's grey cap opened by the bit (a blue door now: a shot opens it) into the South Quarantine Tunnel; back
    (door_teleport): the dead state (thardus_dead); again by the L0, SELECT back to the beam, out by the L0 (a wave door now:
    the Wave Beam opens it) into the North Quarantine Tunnel."""
    out = thardus_entry(m, room) + ["# the fight (THARDUS_FIGHT) starts here"]
    for i, move in enumerate(THARDUS_FIGHT):
        out += MAGMOOR_MOVES[move]
        if i in (4, 9, 14):
            out += [f"shot {IMG_18K}_luta_{i:02d}.png"]
    out += ([f"expect {ENEMY_TABLE + ENEMY_HEALTH:06X} 0000", f"shot {IMG_18K}_morrendo.png", f"wait {THARDUS_DEATH}",
             f"expect {ENEMY_TABLE:06X} 0000", "expectbit 7ED82C 14", "expect 7E07F5 0000",
             f"expect {HEALTH} {THARDUS_ENERGY_AT_WIN:04X}", f"expect {MISSILES} {THARDUS_MISSILES_AT_WIN:04X}",
             f"shot {IMG_18K}_vitoria.png", "hold LEFT 400", "wait 10", "hold RIGHT 200"])   # against the west cliff, then 18j's walk
    for direction, mv in THARDUS_CLIMB:
        out += hops(direction, mv)
    return (out + phendrana_arrive(room, THARDUS, 9)[:3] + [f"expect {HEALTH} {THARDUS_ENERGY_AT_WIN:04X}",
                                                             f"shot {IMG_18K}_porta_aberta.png"] + moves("D")
            + phendrana_arrive(room, "phendrana_south_quarantine_tunnel", 9)[:3]
            + door_teleport(m, "phendrana_south_quarantine_tunnel", THARDUS) + ["wait 60"] + thardus_dead(room)
            + [f"shot {IMG_18K}_morto.png"] + door_teleport(m, "phendrana_north_quarantine_tunnel", THARDUS) + ["wait 60"]
            + thardus_dead(room) + ["hold RIGHT 30", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0000", "hold LEFT 2", "wait 5",
                                    "hold X 2", "wait 60", "hold LEFT 150", "wait 200"] + phendrana_arrive(room, "phendrana_north_quarantine_tunnel", 57)[:3])


def magmoor_tallon_elevator(m: dict, room: dict) -> list[str]:
    """specs/17e, elevador_magmoor_tallon: to the Tallon's Magmoor East transport (door_teleport from the Tunnel B: round 1's
    rooms, a shortcut), onto its platform (the Wave Beam stays on the hall's floor, not taken: its bit off), DOWN: the
    Magmoor's P16 (2x1, one screen high: the platform comes down the 10 rows of its shaft), area 2, standing on its platform;
    paused, its map tile; UP: back in the Tallon, area 0, the Magmoor room's bit in area 2's saved copy."""
    from tallon import items as tallon_items
    sx, sy = platform_screen(MAGMOOR_FROM_TALLON)
    wave = next(n for n, it in enumerate(tallon_items.ITEMS) if it.room == TALLON_TO_MAGMOOR)
    bit = tallon_items.BITS[wave]
    return (door_teleport(m, "tallon_tunnel_b", TALLON_TO_MAGMOOR) + [f"expect {ROOM_PTR} {room[TALLON_TO_MAGMOOR]}"]
            + onto_platform(TALLON_TO_MAGMOOR) + [f"shot {IMG_17E}_tallon_plataforma.png"]
            + ride_elevator(room, TALLON_TO_MAGMOOR, f"{IMG_17E}_tallon_descendo.png")
            + [f"shot {IMG_17E}_p16_chegada.png", explored_at(MAGMOOR_FROM_TALLON, sx, sy)]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(MAGMOOR, [(MAGMOOR_FROM_TALLON, sx, sy)], "magmoor_p16") + [f"shot {IMG_17E}_p16_mapa.png",
                                                                                  "hold START 10", "wait 200"]
            + onto_platform(MAGMOOR_FROM_TALLON) + ride_elevator(room, MAGMOOR_FROM_TALLON, f"{IMG_17E}_p16_subindo.png")
            + [f"shot {IMG_17E}_tallon_volta.png", explored_at(MAGMOOR_FROM_TALLON, sx, sy, MAGMOOR.number),
               f"expect {0x7ED870 + bit // 8:06X} 0000"])   # no item taken in this test: the Wave's byte (and the next) clear


# specs/17f: region A of the Magmoor (tools/magmoor/layouts.py, items.py; item bits $D3-$D4, the red door's bit $C0). The
# walks are measured in the emulator (scratchpad s17f/scripts/route.py, chain.py: for each pit the frames of walk before the
# jump found by a search over a window, the middle of it taken; `hops` rebuilds the inputs): (walk frames, jump frames, after:
# > 0 frames still holding the direction, < 0 frames of wait with nothing held, the fall straight down; jump 0 = walk off an
# edge and fall).
IMG_17F = "build/tests/17f"   # the photos of the region A tests (specs/img/17f-* are copies of some)
IMG_17G = "build/tests/17g"   # specs/17g: the photos of the enemies (specs/img/17g-* are copies of some)


def hops(direction: str, moves: list[tuple[int, int, int]]) -> list[str]:
    out = []
    for walk_frames, jump, after in moves:
        out += ([f"hold {direction} {walk_frames}"] if walk_frames else []) + ([f"hold {direction}+A {jump}"] if jump else [])
        out += [f"hold {direction} {after}"] if after > 0 else [f"wait {-after}"]
    return out


# specs/17g: the walks through region A with its enemies alive, as strings of moves (each letter a few frames of input),
# found by a beam search in the emulator (scratchpad s17g/scripts/route.py, fight.py: from each room's entry, the sequences
# that lose no energy kept, fewer enemies alive and nearer the target first): walks, jumps, the shots that kill on the way
MAGMOOR_MOVES = {
    "r": ["hold RIGHT 8"], "q": ["hold RIGHT 3"], "R": ["hold RIGHT 24"],
    "l": ["hold LEFT 8"], "k": ["hold LEFT 3"], "L": ["hold LEFT 24"],
    "x": ["hold RIGHT+A 30", "hold RIGHT 20"], "X": ["hold RIGHT+A 30", "wait 30"],
    "y": ["hold LEFT+A 30", "hold LEFT 20"], "Y": ["hold LEFT+A 30", "wait 30"],
    "g": ["hold RIGHT 12", "hold RIGHT+A 30", "hold RIGHT 20"], "G": ["hold RIGHT 24", "hold RIGHT+A 30", "hold RIGHT 20"],
    "i": ["hold LEFT 12", "hold LEFT+A 30", "hold LEFT 20"], "I": ["hold LEFT 24", "hold LEFT+A 30", "hold LEFT 20"],   # run, jump
    "h": ["hold A 30", "wait 20"],                                     # a jump straight up
    "a": ["hold R 6", "hold R+X 2", "hold R 4"],                       # a shot up and ahead (R held first)
    "d": ["hold L 6", "hold L+X 2", "hold L 4"],                       # a shot down and ahead
    "c": ["hold DOWN 6", "hold DOWN+X 2", "wait 8", "hold UP 2", "wait 4"],   # a shot crouching (low enemies)
    "s": ["hold X 2", "wait 8"], "u": ["hold UP 6", "hold UP+X 2", "hold UP 4", "wait 6"],
    "p": ["wait 10"], "e": ["hold RIGHT 2"], "f": ["hold LEFT 2"],     # wait; turn to face east / west
    "D": ["hold RIGHT+X 2", "hold RIGHT 150", "wait 200"], "E": ["hold LEFT+X 2", "hold LEFT 150", "wait 200"],   # a side door
    "S": ["hold SELECT 2", "wait 10"],                                 # specs/18h: the HUD's next item (missiles)
}


def moves(seq: str) -> list[str]:
    """specs/17g: the input lines of a string of MAGMOOR_MOVES."""
    return [line for c in seq for line in MAGMOOR_MOVES[c]]


def magmoor_down(m: dict, room: dict, tag: str) -> list[str]:
    """Shortcut (as elevador_magmoor_ida_e_volta): from the landing down the Chozo West elevator, the Chozo's Magmoor North
    transport by door_teleport from the Vault Access (round 1's rooms), onto its platform, down: the Magmoor's P0, area 2."""
    return (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
            + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_17F}_{tag}_chozo.png")
            + door_teleport(m, "chozo_vault_access", CHOZO_TO_MAGMOOR) + [f"expect {ROOM_PTR} {room[CHOZO_TO_MAGMOOR]}"]
            + onto_platform(CHOZO_TO_MAGMOOR) + ride_elevator(room, CHOZO_TO_MAGMOOR, f"{IMG_17F}_{tag}_descendo.png"))


def magmoor_bit(n: int) -> str:
    """`expectbit` of Magmoor item n's bit (tools/magmoor/items.py)."""
    from magmoor import items as magmoor_items
    bit = magmoor_items.BITS[n]
    return f"expectbit {0x7ED870 + bit // 8:06X} {1 << (bit % 8):02X}"


def magmoor_arrive(room: dict, key: str, feet_row: int) -> list[str]:
    """In room `key`, the game running, standing on the row under `feet_row`... with all her energy (no heat, no lava, no
    damage in the door's first frames: specs/15's rule, and none after either)."""
    return [f"expect {ROOM_PTR} {room[key]}", f"expect {GAME_STATE} 0008", f"expect 7E0AFA {(feet_row + 1) * 16 - 21:04X}",
            f"expect {HEALTH} 0063"]


# the measured walks of magmoor_regiao_a_rota (the gear of round 3: Varia Suit, Space Jump, Morph Ball, Bombs; 10 missiles).
# specs/17g: with the enemies the rooms with them are crossed by MAGMOOR_MOVES strings (the beam search's; spin jumps, the
# Space Jump of round 3 included, and shots), the Triclops Pit's bottom by a shot crouching at each rock's Viola then the hop
# over the pool (walk frames searched as 17f's); the climbs and the Space Jump, where no enemy reaches, stay 17f's
M_P0_TO_TRAIL = ["hold RIGHT+X 2", "hold RIGHT 60", "hold RIGHT+X 2", "hold RIGHT 100", "wait 200"]
M_STEP_UP_DOOR = ["hold RIGHT 20", "hold RIGHT+A 24", "hold RIGHT 30", "hold RIGHT+X 2", "hold RIGHT 150", "wait 200"]
M17G_TRAIL = "XxRXRRXpXaxxX"            # the Burning Trail: 3 pits; the Skrees shot (up and ahead) or left diving behind her
M17G_TRAIL_DOOR = "DD"                   # its R1 door
M17G_LAKE_TUNNEL = "xxxXXXXX"            # the Lake Tunnel: over the Sova and the Zeelas, 2 pits
M17G_LAVA_LAKE = ("qXxXXXXXX", "RXXXXXXXXXD")   # the Lava Lake onto the empty pillar; past the Mellas to the Pit Tunnel
M17G_PIT_TUNNEL = "DxXccxxXD"            # the Pit Tunnel: its 2 Violas (stationary), into the Triclops Pit
M_TRICLOPS_WEST = [(14, 30, 40), (4, 30, 40)]                         # onto the west ledges z1 (row 21), z2 (16)
M_TRICLOPS_WEST_BACK = [(23, 30, 40), (16, 30, 70)]                   # z3 (11), the L0 shelf (10)
M_STORAGE_IN = [(61, 30, 60)]                                         # over the pit, west into the missile
M_STORAGE_OUT = [(45, 30, 60)]
M_TRICLOPS_DOWN = [(109, 0, -60), (38, 0, -150)]                      # off the shelf and z3 onto z2, off it to the bottom
# specs/17g: from each rock of the bottom two shots crouching kill the Viola on the next rock (2 Power Beam shots), then the
# hop over the pool; the last hop onto the stretch before the east stair
M17G_TRICLOPS_POOLS = [(6, 30, 50), (15, 30, 50), (21, 30, 50), (20, 30, 50), (19, 30, 50)]
M17G_TRICLOPS_LAST_POOL = (17, 30, 50)
M_TRICLOPS_EAST = [(31, 30, 50), (30, 30, 50), (30, 30, 50), (20, 30, 50)]   # the east stair (38, 34, 30), the east floor
M_TRICLOPS_LEDGES = [("LEFT", [(15, 30, 50), (3, 30, -60)]), ("RIGHT", [(12, 30, -60), (20, 30, 70)])]   # g1, g2; g3, shelf
M_SPACE_JUMP_WEST = ["hold LEFT 10"] + ["hold LEFT+A 30", "hold LEFT 16"] * 12    # into the column's hollow (feet row 7)
M_SPACE_JUMP_EAST = ["hold RIGHT 10"] + ["hold RIGHT+A 30", "hold RIGHT 15"] * 11 + ["hold RIGHT 60", "wait 60"]
M17G_MONITOR_TUNNEL = "xxXxXD"           # the Monitor Tunnel over its Mellas to its east ledge (specs/17h: and its door)
# the screens magmoor_regiao_a_rota walks through (and the P0's): explored bits and the pause map
MAGMOOR_A_SCREENS = [("magmoor_transport_chozo_north", 0, 1), ("magmoor_burning_trail", 0, 1), ("magmoor_burning_trail", 5, 1),
                     ("magmoor_lake_tunnel", 0, 0), ("magmoor_lake_tunnel", 2, 0), ("magmoor_lava_lake", 0, 0),
                     ("magmoor_lava_lake", 3, 0), ("magmoor_lava_lake", 5, 0), ("magmoor_pit_tunnel", 1, 0),
                     ("magmoor_triclops_pit", 0, 1), ("magmoor_triclops_pit", 0, 0), ("magmoor_storage_cavern", 0, 0),
                     ("magmoor_triclops_pit", 2, 2), ("magmoor_triclops_pit", 5, 1), ("magmoor_triclops_pit", 3, 0),
                     ("magmoor_triclops_pit", 5, 0), ("magmoor_monitor_tunnel", 0, 0), ("magmoor_monitor_tunnel", 1, 0)]


def magmoor_full(room: dict, key: str, feet: int, energy: int = 0x63) -> list[str]:
    """magmoor_arrive with `energy` (specs/17h: after an energy tank; specs/17j: the full chain's, all she has)."""
    return magmoor_arrive(room, key, feet)[:-1] + [f"expect {HEALTH} {energy:04X}"]


def magmoor_a_to_storage(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """Region A walked from the P0's platform to the Storage Cavern's missile (the last line walks into it): the pieces of
    magmoor_regiao_a_rota (specs/17f, 17g), shared with the full chain (specs/17j)."""
    full = lambda key, feet: magmoor_full(room, key, feet, energy)   # noqa: E731
    tp = "magmoor_triclops_pit"
    dead = lambda *slots: [f"expect {ENEMY_TABLE + ENEMY_SLOT * n:06X} 0000" for n in slots]   # noqa: E731
    return (M_P0_TO_TRAIL + full("magmoor_burning_trail", 25)
            + enemies_alive(MAGMOOR, "magmoor_burning_trail") + [sh(f"{IMG_17F}_rota_burning_trail")]
            + moves(M17G_TRAIL) + [f"expect {ROOM_PTR} {room['magmoor_burning_trail']}", f"expect {HEALTH} {energy:04X}"]
            + dead(0, 1, 2) + [sh(f"{IMG_17G}_rota_burning_trail_fim")]
            + moves(M17G_TRAIL_DOOR) + full("magmoor_lake_tunnel", 9) + enemies_alive(MAGMOOR, "magmoor_lake_tunnel")
            + moves(M17G_LAKE_TUNNEL) + [sh(f"{IMG_17F}_rota_lake_tunnel")] + moves("D")
            + full("magmoor_lava_lake", 9) + enemies_alive(MAGMOOR, "magmoor_lava_lake")
            + moves(M17G_LAVA_LAKE[0]) + [f"expect 7E0AFA {8 * 16 - 21:04X}", f"expect {HEALTH} {energy:04X}",
                                           sh(f"{IMG_17F}_rota_lava_lake")]
            + moves(M17G_LAVA_LAKE[1]) + full("magmoor_pit_tunnel", 9) + enemies_alive(MAGMOOR, "magmoor_pit_tunnel")
            + moves(M17G_PIT_TUNNEL) + full(tp, 25) + enemies_alive(MAGMOOR, tp)
            + [sh(f"{IMG_17F}_rota_triclops_l1")]
            + ["hold RIGHT 20"] + hops("RIGHT", M_TRICLOPS_WEST) + hops("LEFT", M_TRICLOPS_WEST_BACK)
            + [f"expect 7E0AFA {10 * 16 - 21:04X}"] + ["hold LEFT 60", "hold LEFT+X 2", "hold LEFT 150", "wait 200"]
            + full("magmoor_storage_cavern", 9) + ["hold LEFT 30"] + hops("LEFT", M_STORAGE_IN) + ["hold LEFT 60"])


def magmoor_a_to_column(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """From the Storage Cavern's missile back into the Triclops Pit, down to its bottom, its Violas shot dead, up the east
    side onto the R0 shelf, the Space Jump west into the hanging column's hollow (the last line walks into its missile)."""
    full = lambda key, feet: magmoor_full(room, key, feet, energy)   # noqa: E731
    tp = "magmoor_triclops_pit"
    dead = lambda *slots: [f"expect {ENEMY_TABLE + ENEMY_SLOT * n:06X} 0000" for n in slots]   # noqa: E731
    pools = []
    for hop in M17G_TRICLOPS_POOLS:
        pools += moves("cc") + hops("RIGHT", [hop])
    out = (hops("RIGHT", M_STORAGE_OUT) + M_STEP_UP_DOOR + full(tp, 9)
           + hops("RIGHT", M_TRICLOPS_DOWN) + [f"expect 7E0AFA {42 * 16 - 21:04X}", sh(f"{IMG_17F}_rota_triclops_fundo")]
           + pools + [sh(f"{IMG_17G}_rota_triclops_violas")] + hops("RIGHT", [M17G_TRICLOPS_LAST_POOL])
           + [f"expect 7E0AFA {42 * 16 - 21:04X}", f"expect {HEALTH} {energy:04X}"] + dead(0, 1, 2, 3, 4)
           + hops("RIGHT", M_TRICLOPS_EAST) + [f"expect 7E0AFA {26 * 16 - 21:04X}"])
    for direction, mv in M_TRICLOPS_LEDGES:
        out += hops(direction, mv)
    return (out + full(tp, 9) + [sh(f"{IMG_17F}_rota_triclops_r0")]
            + M_SPACE_JUMP_WEST + [sh(f"{IMG_17F}_rota_triclops_oco"), "hold LEFT 40"])


def magmoor_a_to_station(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """From the column's missile east onto the R0 shelf, the Monitor Tunnel over its Mellas into the Monitor Station."""
    full = lambda key, feet: magmoor_full(room, key, feet, energy)   # noqa: E731
    tp = "magmoor_triclops_pit"
    return (M_SPACE_JUMP_EAST + full(tp, 9) + ["hold RIGHT+X 2", "hold RIGHT 150", "wait 200"]
            + full("magmoor_monitor_tunnel", 9) + enemies_alive(MAGMOOR, "magmoor_monitor_tunnel")
            + moves(M17G_MONITOR_TUNNEL[:-1])
            + full("magmoor_monitor_tunnel", 9) + [f"expect {SAMUS_X} 01AA", sh(f"{IMG_17F}_rota_monitor_tunnel")]
            # specs/17h: its R0 door opens now (region B): the walk's last move goes through it into the Monitor Station
            + moves(M17G_MONITOR_TUNNEL[-1]) + full("magmoor_monitor_station", 9))


def magmoor_route_a(m: dict, room: dict) -> list[str]:
    """specs/17f, magmoor_regiao_a_rota: from the landing down to the Magmoor's P0 (magmoor_down: shortcuts), the gear of round
    3 by RAM (the Varia Suit, the Space Jump, the Morph Ball and the Bombs; 10 missiles: the Tallon's and the Chozo's rounds
    0-2 are not on the way); then WALKING through region A, every pit jumped (measured: no lava touched, the energy checked at
    every room and never refilled: the hot rooms with the Varia and every door's first frames hurt nothing, specs/15's rule):
    the P0's door, the Burning Trail's 3 pits, the Lake Tunnel's 2 (hot), the Lava Lake's 8 pools and its empty pillar, the
    Pit Tunnel, the Triclops Pit up its west ledges to the L0 shelf, the Storage Cavern over its pit into the missile (bit
    $D3+1, 15 missiles) and back, off the shelf down to the pit's bottom, over its 6 pools, up the east stair and the east
    ledges to the R0 shelf; the Space Jump west into the hollow of the hanging column, into its missile (20 missiles), back
    east onto the shelf; the Monitor Tunnel to its east ledge (the Monitor Station's wall until region B). Each room's
    explored bit is set; the pause map shows them ("MAGMOOR").
    specs/17g: with region A's enemies ALIVE (tools/magmoor/enemies.py), never touched: the energy stays 99 the whole way
    (MAGMOOR_MOVES strings where the enemies are, found by the beam search); the Burning Trail's 3 Skrees are gone when she
    leaves it (shot, or burst on the floor behind her), the Triclops Pit's 5 Violas are shot dead from the rocks of its bottom
    (two shots crouching each, the Power Beam), each room's enemies are in their slots when she comes in."""
    eq = VARIA_EQUIPMENT | SPACE_JUMP_EQUIPMENT | MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT
    return (magmoor_down(m, room, "rota") + poke16(0x7E09A2, eq) + poke16(0x7E09A4, eq) + poke16(0x7E09C6, 10)
            + poke16(0x7E09C8, 10) + ["wait 10", f"shot {IMG_17F}_rota_chegada.png"]
            + magmoor_a_to_storage(room)
            + ["wait 120", f"shot {IMG_17F}_rota_storage_missil.png", "wait 300", "hold A 2", "wait 120",
               magmoor_bit(1), f"expect {MAX_MISSILES} 000F", f"expect {GAME_STATE} 0008"]
            + magmoor_a_to_column(room)
            + ["wait 120", f"shot {IMG_17F}_rota_triclops_missil.png", "wait 300", "hold A 2", "wait 120",
               magmoor_bit(0), f"expect {MAX_MISSILES} 0014", f"expect {GAME_STATE} 0008"]
            + magmoor_a_to_station(room)
            + [explored_at(*screen) for screen in MAGMOOR_A_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(MAGMOOR, MAGMOOR_A_SCREENS, "magmoor_a") + [f"shot {IMG_17F}_rota_mapa.png", "hold START 10", "wait 200"])


# magmoor_calor: the heat (12g's numbers: HEAT_DROP in HEAT_FRAMES without the Varia) and the lava with the Varia (1/4 a frame,
# specs/17d: 30 in 120 frames) in the region's rooms
MAGMOOR_LAVA_DROP = 30
LAVA_LAKE_POOL = (11, 15)       # Samus put by RAM standing in the Lava Lake's first pool (10-12), feet 2 rows under the surface


def magmoor_heat_test(m: dict, room: dict) -> list[str]:
    """specs/17f, magmoor_calor: down to the Magmoor (magmoor_down) with the Power Suit; through the Burning Trail (cool:
    nothing) into the Lake Tunnel (hot, Prime's "Area Damage") by door_teleport: HEAT_DROP energy lost in HEAT_FRAMES frames;
    the Varia Suit by RAM: none. Into the Lava Lake (door_teleport), Samus put by RAM in its first pool (shortcut: the walks
    never go into the lava): with the Varia MAGMOOR_LAVA_DROP in 120 frames; one jump east and she stands on the rock past the
    pool (the lava's way out, validate.check_lava), the energy stays."""
    drop = [f"poke {HEALTH} 63", f"wait {HEAT_FRAMES}", f"expect {HEALTH} {99 - HEAT_DROP:04X}"]
    stay = [f"poke {HEALTH} 63", f"wait {HEAT_FRAMES}", f"expect {HEALTH} 0063"]
    burning = [f"poke {HEALTH} 63", f"wait {HEAT_FRAMES}", f"expect {HEALTH} 0063"]
    return (magmoor_down(m, room, "calor")
            + chain_teleports(m, room, [MAGMOOR_FROM_CHOZO, "magmoor_burning_trail"]) + burning
            + chain_teleports(m, room, ["magmoor_burning_trail", "magmoor_lake_tunnel"])
            + [f"expect {ROOM_PTR} {room['magmoor_lake_tunnel']}"] + drop + [f"shot {IMG_17F}_calor_sem_varia.png"]
            + poke16(0x7E09A2, VARIA_EQUIPMENT) + poke16(0x7E09A4, VARIA_EQUIPMENT) + stay
            + [f"shot {IMG_17F}_calor_com_varia.png"]
            + chain_teleports(m, room, ["magmoor_lake_tunnel", "magmoor_lava_lake"])
            + put_samus(*LAVA_LAKE_POOL, 0, 0)
            + [f"expect 7E0AFA {LAVA_LAKE_POOL[1] * 16 - 21:04X}", f"poke {HEALTH} 63", "wait 120",
               f"expect {HEALTH} {99 - MAGMOOR_LAVA_DROP:04X}", f"shot {IMG_17F}_lava_com_varia.png",
               "hold RIGHT+A 30", "hold RIGHT 30", f"expect 7E0AFA {12 * 16 - 21:04X}", f"poke {HEALTH} 63", "wait 120",
               f"expect {HEALTH} 0063", f"shot {IMG_17F}_lava_saida.png"])


# the measured walk of magmoor_save_station_a (round 1's gear: 5 missiles): the Burning Trail's pits, under the R0 shelf, up the
# east cavern's three ledges (21 west, 16 west, 11 east) onto the shelf (10), against the red door
# specs/17g: the trail with its enemies (the beam search's string: 3 pits, the Skrees shot or left behind, round 1's plain
# jumps), then back west under the shelf and its 3 ledges (17f's hops, the walk frames searched again)
M17G_SAVE_TRAIL = "XxRXRRxcrXxGGGGGRr"
M_SAVE_CLIMB = [("LEFT", [(35, 0, -30), (11, 30, -60), (12, 30, -60)]), ("RIGHT", [(4, 30, -60), (20, 30, 60)])]


def magmoor_save_test(m: dict, room: dict) -> list[str]:
    """specs/17f, magmoor_save_station_a: down to the Magmoor (magmoor_down), 5 missiles by RAM (the Landing Site's, round 0),
    WALKING: into the Burning Trail, over its pits, up its east cavern's ledges to the R0 shelf (round 1: no Space Jump, no
    Varia: the trail is cool), its red door opened with the missiles (bit $C0), into Save Station A (P3). Samus on the pedestal
    (where the game puts her when it loads the station), a marker in the saved data (game hours 5), YES, "save completed":
    load station 1 of area 2, its used-station bit ($7ED8FC bit 1); paused, the Magmoor's map. Game over: the area-select screen
    picks area 2, station 1, and draws "MAGMOOR / CAVERNS" (after "TALLON / OVERWORLD": the landing's save at the ship);
    continue: back on Save Station A's pedestal, area 2, the marker loaded, the region's explored bits kept."""
    st = MAGMOOR.load_stations[1]
    out = (magmoor_down(m, room, "save") + poke16(0x7E09C6, 5) + poke16(0x7E09C8, 5) + ["wait 10"]
           + M_P0_TO_TRAIL + magmoor_arrive(room, "magmoor_burning_trail", 25) + moves(M17G_SAVE_TRAIL)
           + [f"expect {HEALTH} 0063"])
    for direction, mv in M_SAVE_CLIMB:
        out += hops(direction, mv)
    out += ([f"expect 7E0AFA {10 * 16 - 21:04X}", f"expect {HEALTH} 0063", f"shot {IMG_17F}_save_prateleira.png"]
            + red_door(room, "magmoor_burning_trail", "RIGHT", "magmoor_save_station_a", False)
            + [f"shot {IMG_17F}_save_sala.png"] + poke16(0x7E09E0, 5))
    for addr, v in ((0x7E0AF6, st.x), (0x7E0B10, st.x), (0x7E0AFA, st.y), (0x7E0B14, st.y)):
        out += poke16(addr, v)
    screens = [("magmoor_transport_chozo_north", 0, 1), ("magmoor_burning_trail", 0, 1), ("magmoor_burning_trail", 5, 0),
               ("magmoor_save_station_a", 0, 0)]
    return (out + ["hold RIGHT 1", "wait 180", f"shot {IMG_17F}_save_pergunta.png", "hold A 2", "wait 300", "hold A 2",
                   "wait 200", f"expect {LOAD_STATION} 0001", f"expect {AREA} 0002", f"expectbit {USED_STATIONS_AREA2} 02",
                   f"expect {GAME_STATE} 0008", f"shot {IMG_17F}_save_salvo.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}", f"shot {IMG_17F}_save_mapa.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} 0008",
                   "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
                   "hold A 2", "wait 300"]
            + area_select_shows_after(MAGMOOR.number, st.index, (TALLON.number,), f"{IMG_17F}_save_tela_de_area.png")
            + ["hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0002", f"expect {ROOM_PTR} {room[st.room]}",
               f"expect {LOAD_STATION} 0001", f"expect {GAME_HOURS} 0005", f"expect 7E0AF6 {st.x:04X}",
               f"shot {IMG_17F}_save_continue.png"]
            + [explored_at(*sc) for sc in screens])


# specs/17h: region B of the Magmoor (tools/magmoor/layouts.py, items.py; item bits $D5-$D7). The walks are measured in the
# emulator (scratchpad s17h/scripts: tr.py traces, hops.py / grid.py the walk frames before each jump over a pit, chain.py the
# zigzag climbs as 17f's, the Monitor Tunnel's string by the beam search of 17g, fight.py): no lava touched, no damage.
IMG_17H = "build/tests/17h"   # the photos of the region B tests (specs/img/17h-* are copies of some)
MAGMOOR_A_PATH = ["magmoor_transport_chozo_north", "magmoor_burning_trail", "magmoor_lake_tunnel", "magmoor_lava_lake",
                  "magmoor_pit_tunnel", "magmoor_triclops_pit", "magmoor_monitor_tunnel"]
M17H_MONITOR_TUNNEL = "XRXXXXD"         # the Monitor Tunnel (from its L0, door_teleport) over its Mellas into the Monitor Station
# the Monitor Station from the L0 shelf: east off it onto the west zigzag's ledges 13 and 18, east off that onto the floor
# (58), west to the L3 door (a shot from near: from far the shot leaves the screen)
M17H_STATION_DOWN = ["hold RIGHT 60", "hold RIGHT 40", "hold RIGHT 60", "wait 60", "hold RIGHT 20", "wait 120", "hold LEFT 220"]
# the Transport Tunnel A from its R0: west to the dais' east face, the ball, a bomb on the bomb block, rolling west into the
# energy tank; back out east, standing, onto the dais and west to the L0 door
BALL_POSE_LEFT = "0041"                 # the morph ball facing west ($0A1C; BALL_POSE faces east)
MORPH, UNMORPH = ["hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30"], ["hold UP 2", "wait 30", "hold UP 2", "wait 30"]


# specs/19f: region A of the Phazon Mines (tools/mines/layouts.py, items.py; item bits $EB-$EE). The gear of round 5 by RAM (what
# the walk of the five areas gives before it: the Varia Suit, the Space Jump, the Morph Ball, the Bombs, the Gravity Suit; the Wave,
# the Ice and the Charge Beams; 30 missiles, 5 super missiles); the walks measured in the emulator (scratchpad s19f/scripts: drv.py)
IMG_19F = "build/tests/19f"   # the photos of the region A tests (specs/img/19f-* are copies of some)
GRAPPLE_EQUIPMENT = 0x4000   # $09A2/$09A4 bit of the Grapple Beam (the ending's table $8B:E721 counts it)
# HUD_ITEM ($09D2): 1 missiles, 2 super missiles, 3 power bombs, 4 grapple, 5 x-ray


def mines_bit(n: int) -> str:
    """`expectbit` of Mines item n's bit (tools/mines/items.py)."""
    from mines import items as mines_items
    bit = mines_items.BITS[n]
    return f"expectbit {0x7ED870 + bit // 8:06X} {1 << (bit % 8):02X}"


def mines_gear(items: int | None = None, beams: int | None = None, missiles: int = 30) -> list[str]:
    """The gear by RAM (round 5's by default: the Varia Suit, the Space Jump, the Morph Ball, the Bombs, the Gravity Suit; the Wave,
    the Ice and the Charge Beams): items, beams, missiles and 5 super missiles."""
    if items is None:
        items = VARIA_EQUIPMENT | SPACE_JUMP_EQUIPMENT | MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT | GRAVITY_SUIT
    if beams is None:
        beams = WAVE_BEAM | ICE_BEAM | CHARGE_EQUIPMENT
    return (poke16(0x7E09A2, items) + poke16(0x7E09A4, items) + give_beams(beams) + poke16(0x7E09C6, missiles)
            + poke16(0x7E09C8, missiles) + poke16(0x7E09CA, 5) + poke16(0x7E09CC, 5) + ["wait 10"])


def mines_down(m: dict, room: dict, tag: str) -> list[str]:
    """Shortcut (as elevador_mines_leste): from the landing to the Tallon's P43 (door_teleport from the Tunnel E: its round-5 ice
    doors not opened), onto its platform, down: the Mines' P0, area 5; the gear of round 5 by RAM (mines_gear)."""
    return (poke16(0x7E0911, 0) + ["wait 2"] + door_teleport(m, "tallon_tunnel_e", TALLON_TO_MINES)
            + [f"expect {ROOM_PTR} {room[TALLON_TO_MINES]}"] + onto_platform(TALLON_TO_MINES)
            + ride_elevator(room, TALLON_TO_MINES, f"{IMG_19F}_{tag}_descendo.png") + mines_gear())


def mines_full(room: dict, key: str, feet: int, energy: int = 0x63) -> list[str]:
    """In the Mines' room `key`, the game running, feet in row `feet`, `energy` (magmoor_full)."""
    return magmoor_full(room, key, feet, energy)


def mines_take(n: int, shot: str, check: list[str]) -> list[str]:
    """Walking into Mines item n: its message (photo), dismissed; its bit, the `check` lines (its capacity or equipment)."""
    return ["wait 120", f"shot {shot}"] + P18F_DISMISS + [mines_bit(n), f"expect {GAME_STATE} 0008", f"expect {HEALTH} 0063"] + check


# the walks of mines_regiao_a_rota (measured in the emulator, scratchpad s19f/scripts: drv.py, hop.py)
M19F_TURN_SHOT = {d: [f"hold {d} 4", "wait 10", "hold X 2", "wait 40"] for d in ("LEFT", "RIGHT")}   # turn, then a shot
M19F_OUT = {d: M19F_TURN_SHOT[d] + [f"hold {d} 150", "wait 200"] for d in ("LEFT", "RIGHT")}   # through a side door just shot
M19F_QUARRY_ACCESS = "RRRxRRRRRR"         # the Quarry Access over its rubble to the R1
M19F_QUARRY_DOWN = "R" * 20            # the Main Quarry from the L0 shelf down the west ledges, east to the basin's east wall
# from the basin's east wall up the crane tower's west face (7 spins of the Space Jump), one more over its top, onto it
M19F_TOWER_UP = SPACE_JUMP_UP["RIGHT"] * 7 + ["hold RIGHT+A 30", "hold RIGHT 8", "wait 60"]
M19F_TOWER_OFF = ["hold LEFT 20"] + ["hold LEFT+A 30", "hold LEFT 20", "wait 90"] + ["hold LEFT 10", "wait 20"] * 10   # onto the cap
M19F_WASTE = (["hold RIGHT 50", "wait 30", "hold LEFT 60", "wait 10"] + MORPH + ["hold LEFT 60", "wait 10"] + UNMORPH
              + ["hold LEFT+X 2", "hold LEFT 150", "wait 200"])   # off the platform, the ball through the tunnel, the L0
M19F_ORE_DOWN = ["hold LEFT 10", "wait 10"] * 22 + ["wait 30"]   # the Ore Processing's R0 shelf down the east ledges
M19F_ORE_TO_DEPOT = "RRRRRRRRRD"          # its floor east to the R1 (the Storage Depot B)
M19F_STEPS_DOWN = ["hold LEFT 10", "wait 10"] * 16   # the Elevator Access A's R0 shelf off its west end to the floor
M19F_EAA_UP = [("RIGHT", [(8, 30, -60), (10, 30, -60)]), ("LEFT", [(8, 30, -60)]), ("RIGHT", [(12, 30, -30)])]   # 21, 16, 11, shelf
M19F_ORE_UP = [("RIGHT", [(20, 30, -60), (14, 30, -60)]), ("LEFT", [(6, 30, -60), (0, 20, 30)])]   # 21, 16, 11, the L0 shelf
M19F_ELITE_UP = [("LEFT", [(6, 30, -60), (9, 30, -60)]), ("RIGHT", [(9, 30, -60), (9, 30, -60)])]   # 21, 16, 11, platform
M19F_SAB_UP = [("LEFT", [(24, 30, -60)]), ("RIGHT", [(24, 30, -60)])]   # the ledge (9), the ceiling door's platform (6)
M19F_UP_DOOR = ["hold UP 6", "hold UP+X 2", "hold UP 4", "wait 66"] + P18F_RISE   # a shot up at a ceiling door, through it
# specs/19g: the Elevator Access A's 2 orbs (tools/mines/enemies.py) in the walk. The Ice Beam of round 5 freezes an orb (a
# frozen one only stops: it thaws and drifts on), so each dies to a missile (100: the copy's health) as it comes at her: the top
# one from the R0 shelf as she comes in (30 frames on: right after the door the missile flew past it), the bottom one from the
# floor turned east, then turned back west (the measured climb starts so); the HUD back to the beam (missiles, supers, grapple,
# nothing). Measured in the emulator (scratchpad s19g/scripts/trace.py).
IMG_19G = "build/tests/19g"   # the photos of the 19g tests (specs/img/19g-* are copies of some)
M19G_EAA_IN = ["hold LEFT 150", "wait 30"]   # through the L1 just shot, into the Elevator Access A's R0
M19G_ORB_WEST = ["hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001", "hold X 2", "wait 40"]
M19G_ORB_EAST = ["hold RIGHT 2", "wait 10", "hold X 2", "wait 40", "hold LEFT 2", "wait 10"]
M19G_HUD_OFF = ["hold SELECT 2", "wait 10"] * 3 + [f"expect {HUD_ITEM} 0000"]
# the screens mines_regiao_a_rota walks through (and the P0's): explored bits and the pause map
MINES_A_SCREENS = [("mines_transport_tallon_south", 0, 1), ("mines_quarry_access", 0, 1), ("mines_quarry_access", 1, 1),
                   ("mines_main_quarry", 0, 0), ("mines_main_quarry", 2, 2), ("mines_main_quarry", 4, 0),
                   ("mines_waste_disposal", 0, 0), ("mines_ore_processing", 2, 0), ("mines_ore_processing", 2, 1),
                   ("mines_storage_depot_b", 0, 0), ("mines_ore_processing", 0, 1), ("mines_elevator_access_a", 0, 0),
                   ("mines_elevator_access_a", 0, 1), ("mines_ore_processing", 0, 0), ("mines_research_access", 1, 1),
                   ("mines_research_access", 0, 1), ("mines_elite_research", 3, 0), ("mines_elite_research", 0, 1),
                   ("mines_security_access_b", 2, 0), ("mines_security_station", 2, 0), ("mines_security_station", 0, 0),
                   ("mines_security_access_a", 0, 0), ("mines_security_access_a", 2, 0), ("mines_main_quarry", 0, 1),
                   ("mines_main_quarry", 0, 2), ("mines_save_station_a", 0, 0)]


# specs/19h: the walks cross the Elite Research with the Phazon Elite's arena won by RAM (a noted shortcut, as Phendrana's
# `poke 7ED82C 08` for the Chapel, 18h): its bit $08 of area 5 on before the door, so the room loads dead (no enemy, the ice door
# on the ceiling); the real fight is mines_phazon_elite's
MINES_ELITE_WON_BY_RAM = ["poke 7ED82D 08"]


# specs/19k: the walks cross the Elite Quarters with the Omega Pirate's arena won by RAM (a noted shortcut, as the Elite Research's):
# its bit $10 of area 5 on before the door, so the room loads dead (no enemy, the plasma doors); the real fight is mines_omega_pirate's
MINES_OMEGA_WON_BY_RAM = ["poke 7ED82D 10"]


def mines_climb(steps) -> list[str]:
    out = []
    for direction, mv in steps:
        out += hops(direction, mv)
    return out + ["wait 30"]


def mines_route_a(m: dict, room: dict) -> list[str]:
    """specs/19f, mines_regiao_a_rota: down the Tallon's P43 to the Mines' P0 (mines_down: shortcuts), the gear of round 5 by RAM;
    then WALKING region A, its doors opened by their beams (the wave doors by the Wave, the ice ones by the Ice: shots), its two
    missiles of round 5 and the Grapple Beam (energy 99 all the way; specs/19g: with the enemies alive, checked on arrival in
    the rooms that have them): the Quarry Access over its rubble; the Main Quarry (its 2 pirates, on the crane's arm and on the
    floor east of the tower, never on the walk's camera at her height) from the L0 shelf down to the basin, the Space Jump up the crane tower (Prime's Spider Ball track and grapple point)
    onto its top, its missile (bit $EB, 35); off the tower onto the floor door's ice cap, a shot down, through it: the Waste
    Disposal (the rock look) on its ceiling door's platform, down, the ball through the 1-row tunnel to the L0, the Ore Processing
    down its east ledges; the R1: the Storage Depot B, the SM's Grapple Beam (bit $ED: the message "GRAPPLING BEAM", the equipment
    bit $4000 in $09A2/$09A4; SELECT: missiles, super missiles, then the grapple on the HUD, $09D2 = 4; again: the beam); back,
    the L1: the Elevator Access A (specs/19g: its top orb killed by a missile from the R0 shelf) down its ledges to the floor (its
    R1, the Elevator A's, a wall until 19i; the bottom orb killed by a missile, turned east) and up again; the Ore
    Processing up its west ledges to the L0, the Research Access, the Elite Research (the arena of 19h, won by RAM before its
    door: MINES_ELITE_WON_BY_RAM, a shortcut) down to its west corner,
    its missile (bit $EE, 40); up its ledges onto the ceiling door's platform, a shot up, through it: the Security Access B (on
    its floor door's cap), up its ledge onto the platform, through its ceiling door (wave): the Mine Security Station (the power
    bomb wall before the plasma door, a photo), its R0: the Security Access A (its niche's power bomb blocks, a photo), its R0:
    the Main Quarry's L1 shelf, down to the floor, its L2: Save Station A. Each room's explored bit; the pause map ("MINES")."""
    full = lambda key, feet: mines_full(room, key, feet)   # noqa: E731
    dead = lambda *slots: [f"expect {ENEMY_TABLE + ENEMY_SLOT * n:06X} 0000" for n in slots]   # noqa: E731  (specs/19g)
    grapple = (VARIA_EQUIPMENT | SPACE_JUMP_EQUIPMENT | MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT | GRAVITY_SUIT
               | GRAPPLE_EQUIPMENT)
    shot = lambda name: f"shot {IMG_19F}_rota_{name}.png"   # noqa: E731
    return (mines_down(m, room, "rota") + [shot("chegada"), "hold RIGHT 4", "wait 10"] + moves("D")
            + full("mines_quarry_access", 25) + [shot("quarry_access")] + moves(M19F_QUARRY_ACCESS + "D")
            + full("mines_main_quarry", 9) + enemies_alive(MINES, "mines_main_quarry") + [shot("main_quarry")]
            + moves(M19F_QUARRY_DOWN) + M19F_TOWER_UP
            + [f"expect 7E0AFA {14 * 16 - 21:04X}", shot("torre"), "hold LEFT 12"]
            + mines_take(0, f"{IMG_19F}_rota_missil_torre.png", [f"expect {MAX_MISSILES} 0023"])
            + M19F_TOWER_OFF + [shot("tampa_de_gelo")] + SHOOT_DOWN + ["wait 200"] + full("mines_waste_disposal", 5)
            + [f"expect {WATER_FX_TYPE} 0000", shot("waste_disposal")] + M19F_WASTE + full("mines_ore_processing", 9)
            + [shot("ore_processing")] + M19F_ORE_DOWN + full("mines_ore_processing", 25) + moves(M19F_ORE_TO_DEPOT)
            + full("mines_storage_depot_b", 9) + [shot("storage_depot_b"), "hold RIGHT 30"]
            + mines_take(2, f"{IMG_19F}_rota_grapple.png", [f"expect 7E09A2 {grapple:04X}", f"expect {COLLECTED_ITEMS} {grapple:04X}"])
            + ["hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0002",
               "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0004", shot("hud_grapple"), "hold SELECT 2", "wait 10",
               f"expect {HUD_ITEM} 0000"]
            + M19F_OUT["LEFT"] + full("mines_ore_processing", 25) + ["hold LEFT 300", "wait 30"] + M19F_TURN_SHOT["LEFT"]
            + M19G_EAA_IN + full("mines_elevator_access_a", 9) + enemies_alive(MINES, "mines_elevator_access_a")
            + [f"shot {IMG_19G}_rota_orbe_de_cima.png"] + M19G_ORB_WEST + dead(0) + M19F_STEPS_DOWN
            + full("mines_elevator_access_a", 25) + [shot("elevator_access_a")] + M19G_ORB_EAST + dead(1)
            + [f"shot {IMG_19G}_rota_orbes_mortos.png"] + M19G_HUD_OFF
            + mines_climb(M19F_EAA_UP) + full("mines_elevator_access_a", 9) + M19F_OUT["RIGHT"]
            + full("mines_ore_processing", 25) + mines_climb(M19F_ORE_UP) + full("mines_ore_processing", 9)
            + M19F_OUT["LEFT"] + full("mines_research_access", 25) + [shot("research_access"), "hold LEFT 200", "wait 10"]
            + MINES_ELITE_WON_BY_RAM + M19F_OUT["LEFT"] + full("mines_elite_research", 9)
            + [shot("elite_research"), "hold LEFT 520", "wait 30"]
            + mines_take(3, f"{IMG_19F}_rota_missil_elite_research.png", [f"expect {MAX_MISSILES} 0028"])
            + ["hold RIGHT 300", "wait 20"] + mines_climb(M19F_ELITE_UP) + ["hold RIGHT 10", "wait 20"]
            + full("mines_elite_research", 5) + [shot("plataforma")] + M19F_UP_DOOR + full("mines_security_access_b", 12)
            + [shot("security_access_b")] + mines_climb(M19F_SAB_UP) + ["hold RIGHT 12", "wait 20"] + M19F_UP_DOOR
            + full("mines_security_station", 12) + ["hold LEFT 260", "wait 20", shot("parede_de_pb"), "hold RIGHT 330", "wait 20"]
            + hops("RIGHT", [(8, 30, -30)]) + M19F_OUT["RIGHT"] + full("mines_security_access_a", 9)
            + ["hold RIGHT 110", "wait 20", shot("nicho_de_pb"), "hold RIGHT 390", "wait 10"] + M19F_OUT["RIGHT"]
            + full("mines_main_quarry", 25) + ["hold RIGHT 10", "wait 10"] * 20 + ["wait 30", "hold LEFT 300", "wait 10"]
            + M19F_OUT["LEFT"] + full("mines_save_station_a", 9) + [shot("save_station_a")]
            + [explored_at(*screen) for screen in MINES_A_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(MINES, MINES_A_SCREENS, "mines_a") + [shot("mapa"), "hold START 10", "wait 200"])


def mines_round6_a(m: dict, room: dict) -> list[str]:
    """specs/19f, mines_regiao_a_rodada_6: the P0 (mines_down), the gear of round 6 by RAM (+ 10 power bombs; the Plasma Beam
    given when it is used), by door_teleport (shortcuts) through the Quarry Access and the Main Quarry into the Security Access A;
    WALKING: west onto the niche's power bomb blocks; in the ball a bomb leaves them, a power bomb (SELECT to it) breaks them; down
    into the niche, its missile (bit $EC, 35); out, the L0 (ice): the Mine Security Station, west onto the L0 step against the
    Bendezium wall; a bomb leaves it, a power bomb breaks it; the plasma door: a shot of the Wave and the Ice leaves it shut, of the
    Plasma opens it: the Storage Depot A (empty: Prime's Flamethrower has no SM item)."""
    full = lambda key, feet: mines_full(room, key, feet)   # noqa: E731
    shot = lambda name: f"shot {IMG_19F}_rodada6_{name}.png"   # noqa: E731
    niche = level_block("mines_security_access_a", 24, 10)
    wall = level_block("mines_security_station", 7, 8)
    to_pb = ["hold SELECT 2", "wait 10"] * 3 + [f"expect {HUD_ITEM} 0003"]   # missiles, super missiles, power bombs
    lay = ["hold X 2", "wait 300", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0000"]
    return (mines_down(m, room, "rodada6") + poke16(0x7E09CE, 10) + poke16(0x7E09D0, 10)
            + chain_teleports(m, room, ["mines_transport_tallon_south", "mines_quarry_access", "mines_main_quarry",
                                        "mines_security_access_a"])
            + full("mines_security_access_a", 9) + ["hold LEFT 130", "wait 20"] + MORPH
            + ["hold X 2", "wait 150", f"expect {niche:06X} C057", shot("bomba")] + to_pb + lay
            + [f"expect {niche:06X} 00FF", f"expect {POWER_BOMBS} 0009"] + UNMORPH + ["hold LEFT 20"]
            + mines_take(1, f"{IMG_19F}_rodada6_missil_nicho.png", [f"expect {MAX_MISSILES} 0023"])
            + ["hold LEFT+A 30", "hold LEFT 200", "wait 20"] + M19F_OUT["LEFT"] + full("mines_security_station", 9)
            + ["hold LEFT 320", "wait 20", "hold LEFT+A 20", "hold LEFT 20", "wait 30", shot("parede")] + MORPH
            + ["hold X 2", "wait 150", f"expect {wall:06X} C057"] + to_pb + lay + [f"expect {wall:06X} 00FF"] + UNMORPH
            + ["hold LEFT 30", "wait 10", "hold RIGHT 16", "wait 10", "hold LEFT 4", "wait 10", "hold X 2", "wait 60",
               shot("porta_de_plasma"), "hold LEFT 60", "wait 60", f"expect {ROOM_PTR} {room['mines_security_station']}"]
            + give_beams(PLASMA_BEAM | WAVE_BEAM | CHARGE_EQUIPMENT)
            + ["hold RIGHT 16", "wait 10", "hold LEFT 4", "wait 10", "hold X 2", "wait 60", "hold LEFT 150", "wait 200"]
            + full("mines_storage_depot_a", 9) + [shot("storage_depot_a")])


def mines_save_a(m: dict, room: dict) -> list[str]:
    """specs/19f, mines_save_station_a: down to the Mines' P0 (mines_down), WALKING through the Quarry Access, the Main Quarry
    from its L0 shelf down to the floor, its L2: Save Station A (the pirate base). Samus on the pedestal (where the game puts her
    when it loads the station), a marker in the saved data (game hours 7), YES, "save completed": load station 1 of area 5, its
    used-station bit ($7ED902 bit 1); paused, the Mines' map. Game over: the area-select screen picks area 5, station 1, and draws
    "PHAZON / MINES" (after "TALLON / OVERWORLD": the landing's save at the ship); continue: back on Save Station A's pedestal, area
    5, the marker loaded, the explored bits kept (area 5's list in $81)."""
    st = MINES.load_stations[1]
    out = (mines_down(m, room, "save") + ["hold RIGHT 4", "wait 10"] + moves("D") + full_mines(room, "mines_quarry_access", 25)
           + moves(M19F_QUARRY_ACCESS + "D") + full_mines(room, "mines_main_quarry", 9) + ["hold RIGHT 10", "wait 10"] * 30
           + ["wait 30", "hold LEFT 400", "wait 10"] + M19F_OUT["LEFT"] + full_mines(room, "mines_save_station_a", 9)
           + [f"expect {WATER_FX_TYPE} 0000", f"shot {IMG_19F}_save_sala.png"] + poke16(0x7E09E0, 7))
    for addr, v in ((0x7E0AF6, st.x), (0x7E0B10, st.x), (0x7E0AFA, st.y), (0x7E0B14, st.y)):
        out += poke16(addr, v)
    screens = [("mines_transport_tallon_south", 0, 1), ("mines_quarry_access", 0, 1), ("mines_main_quarry", 0, 0),
               ("mines_main_quarry", 0, 2), ("mines_save_station_a", 0, 0)]
    return (out + ["hold RIGHT 1", "wait 180", f"shot {IMG_19F}_save_pergunta.png", "hold A 2", "wait 300", "hold A 2",
                   "wait 200", f"expect {LOAD_STATION} 0001", f"expect {AREA} 0005", f"expectbit {USED_STATIONS_AREA5} 02",
                   f"expect {GAME_STATE} 0008", f"shot {IMG_19F}_save_salvo.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}", f"shot {IMG_19F}_save_mapa.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} 0008",
                   "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
                   "hold A 2", "wait 300"]
            + area_select_shows_after(MINES.number, st.index, (TALLON.number,), f"{IMG_19F}_save_tela_de_area.png")
            + ["hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0005", f"expect {ROOM_PTR} {room[st.room]}",
               f"expect {LOAD_STATION} 0001", f"expect {GAME_HOURS} 0007", f"expect 7E0AF6 {st.x:04X}",
               f"shot {IMG_19F}_save_continue.png"]
            + [explored_at(*sc) for sc in screens])


def full_mines(room: dict, key: str, feet: int) -> list[str]:
    return mines_full(room, key, feet)


# specs/19i: region B of the Phazon Mines (tools/mines/layouts.py, items.py; item bits $EF-$F2). The gear of round 5 by RAM
# (mines_down); the walks measured in the emulator (scratchpad s19i/scripts: drv.py, hop_search: the walk frames before each
# jump, the middle of the window taken), with the enemies alive (the Elite Control Access' pirate on its catwalk, never at her
# height; the Ventilation Shaft's Mella, killed by two shots crouching; the Metroid Quarantine A's two Metroids, west, off camera)
IMG_19I = "build/tests/19i"   # the photos of the region B tests (specs/img/19i-* are copies of some)
MAP_STATION_AREA5 = f"{0x7ED908 + 5:06X}"   # map_station_byte_array[5]
# the Elevator A from the L0 shelf down the zigzag (off the shelf onto the 17 ledge, off it onto the 22, back west onto the 27,
# off it to the floor) and east to the R2
M19I_EA_DOWN = ["hold RIGHT 40", "wait 40", "hold RIGHT 40", "wait 40", "hold LEFT 40", "wait 40", "hold LEFT 60", "wait 60",
                "hold RIGHT 200", "wait 20"]
M19I_ECA_TO_MISSILE = ["hold RIGHT 200"]   # under the catwalk east into the missile on the floor
M19I_DOWN_EAST = ["hold RIGHT 60", "wait 30", "hold RIGHT 60", "wait 30", "hold RIGHT 400", "wait 30"]   # a west zigzag down
M19I_DOWN_WEST = ["hold LEFT 60", "wait 30", "hold LEFT 60", "wait 30", "hold LEFT 200", "wait 40"]   # an east one (to the pit)
M19I_MT_TO_WALL = ["hold LEFT 200", "wait 20"] + moves("Y") + ["hold LEFT 300", "wait 20"]   # over the rubble to the wall
M19I_MT_BACK = ["hold RIGHT 300", "wait 10"] + moves("X") + ["hold RIGHT 300", "wait 20"]
# the Ventilation Shaft east from the L0, the Mella (bobbing over the duct) killed by shots crouching, on onto the duct's blocks
M19I_VS_MELLA = moves("RRcccccc") + ["hold RIGHT 40", "wait 20"]
# the Omega Research from the R2 (the Map Station's) west to the wall, up the cliff's lower zigzag (37, 32, 27) onto the L1 shelf
M19I_OR_UP = (hops("RIGHT", [(50, 30, -60), (16, 30, -60)]) + hops("LEFT", [(6, 30, -60), (6, 24, 30)])
              + ["hold LEFT 200", "wait 20"])
# the Central Dynamo's maze: in the pit, the ball west to the bomb block, a bomb, on into the chamber (the missile); back east to
# the pit; out of it west (or east), to the west wall, up the west zigzag (21, 16, 11) onto the L0 shelf
M19I_PIT_OUT = {d: ["hold A 12", f"hold {d}+A 20", f"hold {d} 40", "wait 20"] for d in ("LEFT", "RIGHT")}
M19I_CD_UP = (["hold LEFT 600", "wait 30"] + hops("RIGHT", [(40, 30, -60), (14, 30, -60)])
              + hops("LEFT", [(6, 30, -60), (4, 20, 30)]) + ["hold LEFT 200", "wait 20"])
M19I_QAA_TO_FLOOR_DOOR = ["hold RIGHT 142", "wait 30"]
# from the duct east through the R0 (its cap opened by the shots at the Mella, or by this one), only as long as it takes: the
# Omega Research's L0 shelf is short (walking on into the door, the run went on off it to the floor)
M19I_VS_OUT = M19F_TURN_SHOT["RIGHT"] + ["hold RIGHT 110", "wait 200"]   # off the L0 step onto the floor door's wave cap
# the screens mines_regiao_b_rota walks through: explored bits and the pause map
MINES_B_SCREENS = [("mines_elevator_a", 0, 0), ("mines_elevator_a", 0, 2), ("mines_elite_control_access", 0, 0),
                   ("mines_elite_control_access", 1, 0), ("mines_elite_control", 0, 0), ("mines_elite_control", 3, 1),
                   ("mines_maintenance_tunnel", 2, 0), ("mines_maintenance_tunnel", 0, 0), ("mines_ventilation_shaft", 0, 0),
                   ("mines_ventilation_shaft", 1, 0), ("mines_omega_research", 0, 0), ("mines_omega_research", 3, 2),
                   ("mines_map_station", 0, 0), ("mines_omega_research", 0, 1), ("mines_dynamo_access", 1, 0),
                   ("mines_dynamo_access", 0, 0), ("mines_central_dynamo", 4, 0), ("mines_central_dynamo", 2, 1),
                   ("mines_central_dynamo", 0, 0), ("mines_save_station_b", 0, 0), ("mines_central_dynamo", 4, 1),
                   ("mines_quarantine_access_a", 1, 0), ("mines_metroid_quarantine_a", 3, 0)]


def mines_route_b(m: dict, room: dict) -> list[str]:
    """specs/19i, mines_regiao_b_rota: down the Tallon's P43 to the Mines' P0 (mines_down: the gear of round 5 by RAM), into the
    Elevator A by its L0 (door_teleport from the Elevator Access A: a shortcut, mines_regiao_a_rota walks region A); then WALKING
    region B, its doors opened by their beams (the ice doors by the Ice, the wave ones by the Wave; the floor door of the
    Quarantine Access A by a shot down), energy 99 all the way, with its enemies alive: the Elevator A down its zigzag to the R2;
    the Elite Control Access under the pirate's catwalk (it never fires: never at her height) to its missile (bit $EF, 35), the R0
    (wave); the Elite Control from its L0 shelf down to the floor, the L1: the Maintenance Tunnel (the rock look) over its rubble
    to the power bomb wall before its L0 (a wall until 19j: the blocks there, a photo), back; the Elite Control's R1: the
    Ventilation Shaft (its Mella killed crouching, over the duct's power bomb blocks), the R0: the Omega Research from its L0
    shelf down to the floor, the R2: the Map Station (not used: mines_map_station), back; the Omega Research up the lower
    zigzag onto the L1 shelf, the L1: the Dynamo Access, its L0: the Central Dynamo from its R0 shelf down into the floor's pit;
    the ball west through the tunnel, a bomb on the bomb block (broken), on into the missile (bit $F1, 40: Prime's Power Bomb's
    place); back to the pit, out, up the west zigzag to the L0: Save Station B; back down, over the pit, the R1: the Quarantine
    Access A, a shot down at its floor door's wave cap, through: the Metroid Quarantine A on the ceiling door's platform (its two
    Metroids alive, west, off camera). Each room's explored bit; the pause map ("MINES")."""
    full = lambda key, feet: mines_full(room, key, feet)   # noqa: E731
    shot = lambda name: f"shot {IMG_19I}_rota_{name}.png"   # noqa: E731
    cd = "mines_central_dynamo"
    wall = level_block("mines_maintenance_tunnel", 6, 8)
    duct = level_block("mines_ventilation_shaft", 16, 10)
    maze = level_block(cd, 31, 28)
    return (mines_down(m, room, "rota_b") + door_teleport(m, "mines_elevator_access_a", "mines_elevator_a")
            + full("mines_elevator_a", 9) + [shot("elevator_a")] + M19I_EA_DOWN + full("mines_elevator_a", 41)
            + M19F_OUT["RIGHT"] + full("mines_elite_control_access", 9) + enemies_alive(MINES, "mines_elite_control_access")
            + [shot("elite_control_access")] + M19I_ECA_TO_MISSILE
            + mines_take(4, f"{IMG_19I}_rota_missil_elite_control_access.png", [f"expect {MAX_MISSILES} 0023"])
            + enemies_alive(MINES, "mines_elite_control_access") + ["hold RIGHT 100", "wait 20"] + M19F_OUT["RIGHT"]
            + full("mines_elite_control", 9) + [shot("elite_control")] + M19I_DOWN_EAST + full("mines_elite_control", 25)
            + ["hold LEFT 500", "wait 20"] + M19F_OUT["LEFT"] + full("mines_maintenance_tunnel", 9) + M19I_MT_TO_WALL
            + [f"expect {wall:06X} C057", shot("parede_de_pb")] + M19I_MT_BACK + M19F_OUT["RIGHT"]
            + full("mines_elite_control", 25) + ["hold RIGHT 900", "wait 20"] + M19F_OUT["RIGHT"]
            + full("mines_ventilation_shaft", 9) + enemies_alive(MINES, "mines_ventilation_shaft") + [shot("ventilation_shaft")]
            + M19I_VS_MELLA + [f"expect {ENEMY_TABLE:06X} 0000", f"expect {duct:06X} C057", shot("duto")]
            + M19I_VS_OUT + full("mines_omega_research", 9) + [shot("omega_research")]
            + M19I_DOWN_EAST + full("mines_omega_research", 41) + M19F_OUT["RIGHT"] + full("mines_map_station", 9)
            + [shot("map_station")] + M19F_OUT["LEFT"] + full("mines_omega_research", 41) + ["hold LEFT 900", "wait 30"]
            + M19I_OR_UP + full("mines_omega_research", 25) + M19F_OUT["LEFT"] + full("mines_dynamo_access", 9)
            + ["hold LEFT 400", "wait 20"] + M19F_OUT["LEFT"] + full(cd, 9) + [shot("central_dynamo")] + M19I_DOWN_WEST
            + full(cd, 28) + MORPH + ["hold LEFT 60", "wait 10", f"expect {maze:06X} F058", "hold X 2", "wait 120",
                                      f"expect {maze:06X} 00FF", shot("labirinto"), "hold LEFT 150"]
            + mines_take(6, f"{IMG_19I}_rota_missil_central_dynamo.png", [f"expect {MAX_MISSILES} 0028"])
            + ["hold RIGHT 200", "wait 10"] + UNMORPH + M19I_PIT_OUT["LEFT"] + full(cd, 25) + M19I_CD_UP + full(cd, 9)
            + M19F_OUT["LEFT"] + full("mines_save_station_b", 9) + [shot("save_station_b")] + M19F_OUT["RIGHT"] + full(cd, 9)
            + M19I_DOWN_EAST[:4] + ["hold RIGHT 300", "wait 40"] + full(cd, 28) + M19I_PIT_OUT["RIGHT"]
            + ["hold RIGHT 600", "wait 20"] + full(cd, 25) + M19F_OUT["RIGHT"] + full("mines_quarantine_access_a", 9)
            + [shot("quarantine_access_a")] + M19I_QAA_TO_FLOOR_DOOR + SHOOT_DOWN + ["wait 300"]
            + full("mines_metroid_quarantine_a", 5) + enemies_alive(MINES, "mines_metroid_quarantine_a")
            + [shot("metroid_quarantine_a")] + [explored_at(*screen) for screen in MINES_B_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(MINES, MINES_B_SCREENS, "mines_b") + [shot("mapa"), "hold START 10", "wait 200"])


def mines_round6_b(m: dict, room: dict) -> list[str]:
    """specs/19i, mines_regiao_b_rodada_6: the P0 (mines_down), the gear of round 6 by RAM (+ 10 power bombs), by door_teleport
    (shortcuts) into each room with a power bomb lock of region B; WALKING: the Maintenance Tunnel from its R0 over the rubble to
    the wall before its L0: in the ball a bomb leaves it, a power bomb breaks it; the Ventilation Shaft from its L0 (its Mella
    killed crouching) onto the duct's blocks: a bomb leaves them, a power bomb breaks them, the ball falls into the duct and rolls
    east onto the Energy Tank (bit $F0: energy 199 of 199); the Metroid Quarantine A from its ceiling door's platform east to the wall before
    the east chamber: a bomb leaves it, a power bomb breaks it, the missile (bit $F2, 35)."""
    full = lambda key, feet: mines_full(room, key, feet)   # noqa: E731
    shot = lambda name: f"shot {IMG_19I}_rodada6_{name}.png"   # noqa: E731
    wall = level_block("mines_maintenance_tunnel", 6, 8)
    duct = level_block("mines_ventilation_shaft", 16, 10)
    mqa = level_block("mines_metroid_quarantine_a", 84, 24)
    to_pb = ["hold SELECT 2", "wait 10"] * 3 + [f"expect {HUD_ITEM} 0003"]   # missiles, super missiles, power bombs
    lay = ["hold X 2", "wait 300", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0000"]

    def bomb_then_pb(block: int, tag: str) -> list[str]:
        return (MORPH + ["hold X 2", "wait 150", f"expect {block:06X} C057", shot(f"{tag}_bomba")] + to_pb + lay
                + [f"expect {block:06X} 00FF"])
    return (mines_down(m, room, "rodada6_b") + poke16(0x7E09CE, 10) + poke16(0x7E09D0, 10)
            + door_teleport(m, "mines_elite_control", "mines_maintenance_tunnel") + full("mines_maintenance_tunnel", 9)
            + M19I_MT_TO_WALL + bomb_then_pb(wall, "parede") + [f"expect {POWER_BOMBS} 0009"] + UNMORPH
            + ["hold LEFT 60", "wait 20", shot("parede_quebrada")]
            + door_teleport(m, "mines_elite_control", "mines_ventilation_shaft") + full("mines_ventilation_shaft", 9)
            + M19I_VS_MELLA + [f"expect {ENEMY_TABLE:06X} 0000"] + MORPH
            + ["hold X 2", "wait 150", f"expect {duct:06X} C057", shot("duto_bomba")] + to_pb
            + ["hold X 2", "wait 300", "hold RIGHT 30", "wait 120", shot("etank")] + P18F_DISMISS
            + [mines_bit(5), f"expect {GAME_STATE} 0008", f"expect {HEALTH} 00C7", "expect 7E09C4 00C7",
               f"expect {duct:06X} 00FF", f"expect {POWER_BOMBS} 0008", "hold SELECT 2", "wait 10"] + UNMORPH
            + door_teleport(m, "mines_quarantine_access_a", "mines_metroid_quarantine_a")
            + [f"expect {ROOM_PTR} {room['mines_metroid_quarantine_a']}", "hold RIGHT 400", "wait 30"]
            + mines_full(room, "mines_metroid_quarantine_a", 25, 0xC7) + bomb_then_pb(mqa, "quarentena") + UNMORPH
            + ["hold RIGHT 200"] + ["wait 120", f"shot {IMG_19I}_rodada6_missil_quarentena.png"] + P18F_DISMISS
            + [mines_bit(7), f"expect {GAME_STATE} 0008", f"expect {HEALTH} 00C7", f"expect {MAX_MISSILES} 0023"])


def mines_save_b(m: dict, room: dict) -> list[str]:
    """specs/19i, mines_save_station_b: down to the Mines' P0 (mines_down), into Save Station B by its R0 (door_teleport from the
    Central Dynamo: mines_regiao_b_rota walks there). Samus on the pedestal (where the game puts her when it loads the station), a
    marker in the saved data (game hours 7), YES, "save completed": load station 2 of area 5, its used-station bit ($7ED902 bit
    2); paused, the Mines' map. Game over: the area-select screen picks area 5, station 2, and draws "PHAZON / MINES"; continue:
    back on Save Station B's pedestal, area 5, the marker loaded, the explored bits kept (area 5's list in $81)."""
    st = MINES.load_stations[2]
    out = (mines_down(m, room, "save_b") + door_teleport(m, "mines_central_dynamo", "mines_save_station_b")
           + full_mines(room, "mines_save_station_b", 9) + [f"expect {WATER_FX_TYPE} 0000", f"shot {IMG_19I}_save_sala.png"]
           + poke16(0x7E09E0, 7))
    for addr, v in ((0x7E0AF6, st.x), (0x7E0B10, st.x), (0x7E0AFA, st.y), (0x7E0B14, st.y)):
        out += poke16(addr, v)
    screens = [("mines_transport_tallon_south", 0, 1), ("mines_save_station_b", 0, 0)]
    return (out + ["hold RIGHT 1", "wait 180", f"shot {IMG_19I}_save_pergunta.png", "hold A 2", "wait 300", "hold A 2",
                   "wait 200", f"expect {LOAD_STATION} 0002", f"expect {AREA} 0005", f"expectbit {USED_STATIONS_AREA5} 04",
                   f"expect {GAME_STATE} 0008", f"shot {IMG_19I}_save_salvo.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}", f"shot {IMG_19I}_save_mapa.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} 0008",
                   "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
                   "hold A 2", "wait 300"]
            + area_select_shows_after(MINES.number, st.index, (TALLON.number,), f"{IMG_19I}_save_tela_de_area.png")
            + ["hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0005", f"expect {ROOM_PTR} {room[st.room]}",
               f"expect {LOAD_STATION} 0002", f"expect {GAME_HOURS} 0007", f"expect 7E0AF6 {st.x:04X}",
               f"shot {IMG_19I}_save_continue.png"]
            + [explored_at(*sc) for sc in screens])


def mines_map(m: dict, room: dict) -> list[str]:
    """specs/19i, mines_map_station: down to the Mines' P0 (mines_down), into the Map Station by its L0 (door_teleport from the
    Omega Research: mines_regiao_b_rota walks there; the pirate base); on the pause map before, rooms not visited (Save Station
    A, the Main Quarry, the Central Dynamo, the Metroid Quarantine A) are blank; she walks east off the door's ledge into the
    terminal: "map data access completed", the pause map opens by itself with the whole built Mines drawn (regions A and B):
    those rooms' tiles (palette 3: not explored) and the map station byte of area 5 set ($7ED90D = $FF). The station's icon is
    in area 5's new icon list (build.py: vanilla Tourian has none)."""
    unvisited = [("mines_save_station_a", 0, 0), ("mines_main_quarry", 2, 1), ("mines_central_dynamo", 2, 1),
                 ("mines_metroid_quarantine_a", 3, 0)]
    (WORK / "vram_19i_vazio.bin").write_bytes(struct.pack("<H", pausemap.BLANK))
    return (mines_down(m, room, "mapa") + door_teleport(m, "mines_omega_research", "mines_map_station")
            + full_mines(room, "mines_map_station", 9) + [f"expect {MAP_STATION_AREA5} 00", f"shot {IMG_19I}_mapa_sala.png",
                                                          "hold START 10", "wait 200",
                                                          f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + [f"expectvram {PAUSE_MAP_VRAM + pausemap.tile_index(*map_tile(k, a, b)):04X} "
               f"{(WORK / 'vram_19i_vazio.bin').relative_to(ROOT)}" for k, a, b in unvisited]
            + [f"shot {IMG_19I}_mapa_antes.png", "hold START 10", "wait 200", f"expect {GAME_STATE} 0008",
               "hold RIGHT 100", "wait 260", f"shot {IMG_19I}_mapa_mensagem.png", "hold A 2", "wait 200",
               f"expect {MAP_STATION_AREA5} FF", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + revealed_tiles(unvisited, "19i_revelado") + [f"shot {IMG_19I}_mapa_revelado.png"])


# specs/19j: region C (the west) walked with the gear of round 6: the walks of the Phazon Processing Center are the Omega
# Research's (the same hall, layouts.py: M19I_DOWN_EAST, M19I_OR_UP), the Elite Quarters' the Elite Control's mirrored
IMG_19J = "build/tests/19j"   # the photos of the region C test (specs/img/19j-* are copies of some)
M19J_TA_EAST = ["hold RIGHT 200", "wait 20"]   # the Transport Access from its L0 east to the R0
M19J_PPC_TO_NICHE = ["hold LEFT 140", "wait 20"]   # from the R2 west onto the niche's power bomb blocks
M19J_MT_TO_WALL = ["hold RIGHT 60", "wait 20"]   # the Maintenance Tunnel from its L0 east against the power bomb wall
M19J_EQ_DOWN = ["hold LEFT 60", "wait 30", "hold LEFT 60", "wait 30", "hold LEFT 400", "wait 30"]   # the R0 shelf down west
M19J_EQA_DOWN = ["hold LEFT 100", "wait 30"]   # off the R0 door's step onto the floor
MINES_C_SCREENS = [("mines_transport_access", 0, 0), ("mines_transport_access", 1, 0),
                   ("mines_phazon_processing_center", 0, 0), ("mines_phazon_processing_center", 3, 2),
                   ("mines_phazon_processing_center", 0, 1), ("mines_maintenance_tunnel", 0, 0),
                   ("mines_processing_center_access", 1, 0), ("mines_processing_center_access", 0, 0),
                   ("mines_elite_quarters", 4, 0), ("mines_elite_quarters", 0, 1), ("mines_elite_quarters_access", 1, 0)]


def mines_route_c(m: dict, room: dict) -> list[str]:
    """specs/19j, mines_regiao_c_rota: down the Tallon's P43 to the Mines' P0 (mines_down), the gear of round 6 by RAM (+ 10 power
    bombs, the Plasma Beam with the Ice, the Wave and the Charge), into the Transport Access by its L0 (door_teleport from the
    P25, the Magmoor's lift room: elevador_mines_oeste rides it); then WALKING region C, its doors opened by their beams (ice,
    plasma), energy 99 until the Energy Tank: the Transport Access east to the R0; the Phazon Processing Center from its L0
    shelf down to the floor, the R2: the Maintenance Tunnel's west end, against the power bomb wall (19i's: from this side now):
    a bomb leaves it, a power bomb breaks it (the way on to region B); back, the hall's floor west onto the pit's power bomb
    blocks: a bomb leaves them, a power bomb breaks them, the missile in the pit (bit $F3, 35); out of the pit, to the west
    wall, up the lower zigzag onto the L1 shelf, the plasma door: the Processing Center Access, its Energy Tank (bit $F4: energy
    199 of 199), the L0 (plasma): the Elite Quarters (the Omega Pirate's arena, won by RAM: MINES_OMEGA_WON_BY_RAM, specs/19k) from the R0
    shelf down to the floor, the L1 (plasma): the Elite Quarters Access, down its step. Each room's explored bit; the pause
    map ("MINES")."""
    full = lambda key, feet, energy=0x63: mines_full(room, key, feet, energy)   # noqa: E731
    shot = lambda name: f"shot {IMG_19J}_rota_{name}.png"   # noqa: E731
    ppc = "mines_phazon_processing_center"
    wall = level_block("mines_maintenance_tunnel", 6, 8)
    niche = level_block(ppc, 33, 42)
    to_pb = ["hold SELECT 2", "wait 10"] * 3 + [f"expect {HUD_ITEM} 0003"]   # missiles, super missiles, power bombs
    lay = ["hold X 2", "wait 300", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0000"]

    def bomb_then_pb(block: int, tag: str) -> list[str]:
        return (MORPH + ["hold X 2", "wait 150", f"expect {block:06X} C057", shot(f"{tag}_bomba")] + to_pb + lay
                + [f"expect {block:06X} 00FF"])
    return (mines_down(m, room, "rota_c") + poke16(0x7E09CE, 10) + poke16(0x7E09D0, 10)
            + give_beams(ICE_BEAM | WAVE_BEAM | PLASMA_BEAM | CHARGE_EQUIPMENT)
            + door_teleport(m, "mines_transport_magmoor_south", "mines_transport_access")
            + full("mines_transport_access", 9) + [shot("transport_access")] + M19J_TA_EAST + M19F_OUT["RIGHT"]
            + full(ppc, 9) + [shot("phazon_processing_center")] + M19I_DOWN_EAST + full(ppc, 41) + M19F_OUT["RIGHT"]
            + full("mines_maintenance_tunnel", 9) + M19J_MT_TO_WALL + bomb_then_pb(wall, "parede")
            + [f"expect {POWER_BOMBS} 0009"] + UNMORPH + [shot("parede_quebrada")] + M19F_OUT["LEFT"]
            + full(ppc, 41) + M19J_PPC_TO_NICHE + bomb_then_pb(niche, "fosso") + [f"expect {POWER_BOMBS} 0008"] + UNMORPH
            + ["hold LEFT 45"]
            + mines_take(8, f"{IMG_19J}_rota_missil_phazon_processing_center.png", [f"expect {MAX_MISSILES} 0023"])
            + M19I_PIT_OUT["LEFT"] + ["hold LEFT 900", "wait 30"] + M19I_OR_UP + full(ppc, 25) + M19F_OUT["LEFT"]
            + full("mines_processing_center_access", 9) + [shot("processing_center_access"), "hold LEFT 120", "wait 120",
                                                           f"shot {IMG_19J}_rota_etank.png"] + P18F_DISMISS
            + [mines_bit(9), f"expect {GAME_STATE} 0008", f"expect {HEALTH} 00C7", "expect 7E09C4 00C7"]
            + ["hold LEFT 100", "wait 20"] + MINES_OMEGA_WON_BY_RAM + M19F_OUT["LEFT"] + full("mines_elite_quarters", 9, 0xC7)
            + [f"expect {ENEMY_TABLE:06X} 0000", shot("elite_quarters")] + M19J_EQ_DOWN
            + full("mines_elite_quarters", 25, 0xC7) + ["hold LEFT 900", "wait 20"] + M19F_OUT["LEFT"]
            + full("mines_elite_quarters_access", 9, 0xC7) + M19J_EQA_DOWN + full("mines_elite_quarters_access", 12, 0xC7)
            + [shot("elite_quarters_access")] + [explored_at(*screen) for screen in MINES_C_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(MINES, MINES_C_SCREENS, "mines_c") + [shot("mapa"), "hold START 10", "wait 200"])


# specs/19l: region D (the lower level) walked with the gear of round 6; the walks measured in the emulator (scratchpad
# s19l/drv.py: a state per room, hop_search: the walk frames before each jump, the middle of the window taken)
IMG_19L = "build/tests/19l"   # the photos of the region D tests (specs/img/19l-* are copies of some)
M19L_EQA_TO_FLOOR_DOOR = ["hold RIGHT 45", "wait 20"]   # after M19J_EQA_DOWN: back east over the floor door's plasma cap
# the Metroid Quarantine B from the ceiling door's platform west down the upper zigzag (11, 16), off it to the floor, west to the
# column; back east, the Space Jump up its face (5 spins and one over the top), a step onto the missile
M19L_MQB_DOWN = ["hold LEFT 40", "wait 40", "hold LEFT 40", "wait 40", "hold LEFT 60", "wait 120", "hold LEFT 600", "wait 20"]
M19L_MQB_UP = ["hold RIGHT 120", "wait 10"] + SPACE_JUMP_UP["LEFT"] * 5 + ["hold LEFT+A 30", "hold LEFT 8", "wait 90",
                                                                       "hold RIGHT 14"]
M19L_MQB_TO_FLOOR_DOOR = ["hold RIGHT 54", "wait 90"]   # off the column east onto the floor door's plasma cap
# the Quarantine Access B: the orb (frozen by the Ice Beam, as 19g's) killed by a missile as she comes in, then east to the R0
M19L_QAB_ORB = ["hold RIGHT 2", "wait 10", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001", "hold X 2", "wait 60"]
M19L_HUD_OFF = ["hold SELECT 2", "wait 10"] * 3 + [f"expect {HUD_ITEM} 0000"]   # missiles -> supers -> power bombs -> beam
M19L_FHB_TO_MISSILE = ["hold RIGHT 165"]   # off the L1 step east into the missile on the floor
M19L_FHB_TO_FLOOR_DOOR = ["hold RIGHT 88", "wait 20"]   # on east over the floor door's plasma cap (the Metroids off camera)
# the Phazon Mining Tunnel: from the platform west against the tunnel, the ball in: a bomb on the bomb block (broken), on west
# against the power bomb block, a power bomb (broken), on out of the tunnel off the ledge to the floor; east to the R0
M19L_PMT_TO_TUNNEL = ["hold LEFT 80", "wait 10"]
M19L_PMT_OUT = ["hold LEFT 40", "wait 60"]
M19L_FHAC_TO_MISSILE = ["hold RIGHT 136"]   # under the pirate's catwalk east into the missile on the floor
# the Elevator B from the L1 door's ledge down the zigzag (onto the 32 ledge, the 37, the floor) and east to the R2
M19L_EB_DOWN = ["hold RIGHT 20", "wait 60", "hold RIGHT 30", "wait 40", "hold LEFT 30", "wait 60", "hold RIGHT 100", "wait 20"]
# the Elevator Access B: the Sova killed by three shots from the L1, the zigzag (21, 16, 11) up onto the R0 shelf
M19L_EAB_SOVA = ["hold RIGHT 2", "wait 10"] + moves("sss") + ["wait 30"]
M19L_EAB_UP = (hops("RIGHT", [(66, 30, -60)]) + hops("LEFT", [(7, 30, -60)]) + ["hold LEFT 16", "wait 10"]
               + hops("RIGHT", [(12, 30, -60)]) + ["hold RIGHT 10", "hold RIGHT+A 20", "hold RIGHT 30", "wait 30"])
M19L_MS_IN = ["hold RIGHT 150", "wait 10"]   # the Missile Station from the L0 off the step east into the station
MINES_D_SCREENS = [("mines_metroid_quarantine_b", 5, 0), ("mines_metroid_quarantine_b", 0, 2), ("mines_save_station_c", 0, 0),
                   ("mines_quarantine_access_b", 0, 0), ("mines_quarantine_access_b", 1, 0), ("mines_fungal_hall_b", 0, 1),
                   ("mines_fungal_hall_b", 2, 1), ("mines_phazon_mining_tunnel", 1, 0), ("mines_phazon_mining_tunnel", 0, 0),
                   ("mines_fungal_hall_a", 0, 0), ("mines_fungal_hall_access", 0, 2), ("mines_fungal_hall_access", 1, 2),
                   ("mines_elevator_b", 0, 1), ("mines_elevator_b", 0, 2), ("mines_elevator_access_b", 0, 1),
                   ("mines_elevator_access_b", 1, 0), ("mines_missile_station", 0, 0), ("mines_missile_station", 1, 0)]


def mines_route_d(m: dict, room: dict) -> list[str]:
    """specs/19l, mines_regiao_d_rota: down the Tallon's P43 to the Mines' P0 (mines_down), the gear of round 6 by RAM (+ 10 power
    bombs; the Plasma Beam given when it is used), into the Elite Quarters Access by its R0 (door_teleport from the Elite Quarters:
    mines_regiao_c_rota walks there); then WALKING region D, energy 99 all the way, its enemies alive on arrival: down the step,
    over the floor door: a shot down of the Ice and the Wave leaves its plasma cap shut, of the Plasma opens it (the first vertical
    plasma door): the Metroid Quarantine B on the ceiling door's platform, down the zigzag to the floor, the Space Jump up the
    west column (Prime's track and grapple point) onto its missile (bit $F5, 35); off it onto the floor door's plasma cap, a shot
    down: Save Station C on its ceiling door's platform. By door_teleport (a shortcut: the east climb is the Elite Research's) the
    Quarantine Access B: its orb killed by a missile, the R0: the Fungal Hall B (the rock look) off the step to its missile on the
    floor (bit $F6, 40), on over the floor door (the two Metroids off camera), a shot down: the Phazon Mining Tunnel on the
    chamber's platform; the ball through the tunnel, a bomb on the bomb block, a power bomb on the power bomb block, out to the
    floor, the R0 (plasma on this side): the Fungal Hall A on its L0 shelf (its two Hunter Metroids alive). By door_teleport (the
    hall's floor is theirs) the Fungal Hall Access: under the pirate's catwalk to its missile (bit $F7, 45), the R2: the Elevator B
    down its zigzag, the R2: the Elevator Access B (its Sova killed by three shots), up the zigzag to the R0 shelf, the ice door:
    the Metroid Quarantine A by its L1 (region B, its Metroids alive). By door_teleport the Missile Station: 10 missiles, walking
    into the station: "missile reload completed", 45 of 45. Each room's explored bit; the pause map ("MINES")."""
    full = lambda key, feet: mines_full(room, key, feet)   # noqa: E731
    shot = lambda name: f"shot {IMG_19L}_rota_{name}.png"   # noqa: E731
    pmt = "mines_phazon_mining_tunnel"
    bomb, pb = level_block(pmt, 15, 5), level_block(pmt, 13, 5)
    to_pb = ["hold SELECT 2", "wait 10"] * 3 + [f"expect {HUD_ITEM} 0003"]
    lay = ["hold X 2", "wait 300", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0000"]
    dead = [f"expect {ENEMY_TABLE:06X} 0000"]
    return (mines_down(m, room, "rota_d") + poke16(0x7E09CE, 10) + poke16(0x7E09D0, 10)
            + give_beams(ICE_BEAM | WAVE_BEAM | CHARGE_EQUIPMENT)
            + door_teleport(m, "mines_elite_quarters", "mines_elite_quarters_access") + full("mines_elite_quarters_access", 9)
            + M19J_EQA_DOWN + M19L_EQA_TO_FLOOR_DOOR + full("mines_elite_quarters_access", 12) + [shot("tampa_de_plasma")]
            + SHOOT_DOWN + ["wait 200", f"expect {ROOM_PTR} {room['mines_elite_quarters_access']}"]
            + give_beams(ICE_BEAM | WAVE_BEAM | PLASMA_BEAM | CHARGE_EQUIPMENT) + SHOOT_DOWN + ["wait 300"]
            + full("mines_metroid_quarantine_b", 5) + [shot("metroid_quarantine_b")] + M19L_MQB_DOWN
            + full("mines_metroid_quarantine_b", 44) + M19L_MQB_UP
            + mines_take(10, f"{IMG_19L}_rota_missil_coluna.png", [f"expect {MAX_MISSILES} 0023"])
            + M19L_MQB_TO_FLOOR_DOOR + full("mines_metroid_quarantine_b", 44) + SHOOT_DOWN + ["wait 300"]
            + full("mines_save_station_c", 5) + [shot("save_station_c")]
            + door_teleport(m, "mines_metroid_quarantine_b", "mines_quarantine_access_b") + full("mines_quarantine_access_b", 9)
            + enemies_alive(MINES, "mines_quarantine_access_b") + [shot("quarantine_access_b")] + M19L_QAB_ORB + dead
            + M19L_HUD_OFF + ["hold RIGHT 300", "wait 20"] + M19F_OUT["RIGHT"] + full("mines_fungal_hall_b", 25)
            + enemies_alive(MINES, "mines_fungal_hall_b") + [shot("fungal_hall_b")] + M19L_FHB_TO_MISSILE
            + mines_take(11, f"{IMG_19L}_rota_missil_fungal_hall_b.png", [f"expect {MAX_MISSILES} 0028"])
            + M19L_FHB_TO_FLOOR_DOOR + full("mines_fungal_hall_b", 28) + SHOOT_DOWN + ["wait 300"] + full(pmt, 5)
            + [shot("phazon_mining_tunnel")] + M19L_PMT_TO_TUNNEL + MORPH
            + ["hold LEFT 30", "wait 10", f"expect {bomb:06X} F058", "hold X 2", "wait 150", f"expect {bomb:06X} 00FF",
               "hold LEFT 30", "wait 10", f"expect {pb:06X} C057"] + to_pb + lay
            + [f"expect {pb:06X} 00FF", f"expect {POWER_BOMBS} 0009", shot("tunel")] + M19L_PMT_OUT + UNMORPH
            + full(pmt, 9) + ["hold RIGHT 300", "wait 20"] + M19F_OUT["RIGHT"] + full("mines_fungal_hall_a", 9)
            + enemies_alive(MINES, "mines_fungal_hall_a") + [shot("fungal_hall_a")]
            + door_teleport(m, "mines_fungal_hall_a", "mines_fungal_hall_access") + full("mines_fungal_hall_access", 41)
            + enemies_alive(MINES, "mines_fungal_hall_access") + [shot("fungal_hall_access")] + M19L_FHAC_TO_MISSILE
            + mines_take(12, f"{IMG_19L}_rota_missil_fungal_hall_access.png", [f"expect {MAX_MISSILES} 002D"])
            + ["hold RIGHT 100", "wait 20"] + M19F_OUT["RIGHT"] + full("mines_elevator_b", 25) + [shot("elevator_b")]
            + M19L_EB_DOWN + full("mines_elevator_b", 41) + M19F_OUT["RIGHT"] + full("mines_elevator_access_b", 25)
            + enemies_alive(MINES, "mines_elevator_access_b") + [shot("elevator_access_b")] + M19L_EAB_SOVA + dead
            + M19L_EAB_UP + full("mines_elevator_access_b", 9) + M19F_OUT["RIGHT"] + full("mines_metroid_quarantine_a", 25)
            + enemies_alive(MINES, "mines_metroid_quarantine_a") + [shot("metroid_quarantine_a")]
            + door_teleport(m, "mines_fungal_hall_b", "mines_missile_station") + full("mines_missile_station", 9)
            + poke16(0x7E09C6, 10) + M19L_MS_IN + ["wait 200", shot("missile_station")] + P18F_DISMISS
            + ["expect 7E09C6 002D", f"expect {MAX_MISSILES} 002D", f"expect {GAME_STATE} 0008"]
            + [explored_at(*screen) for screen in MINES_D_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(MINES, MINES_D_SCREENS, "mines_d") + [shot("mapa"), "hold START 10", "wait 200"])


def mines_save_c(m: dict, room: dict) -> list[str]:
    """specs/19l, mines_save_station_c: down to the Mines' P0 (mines_down), into Save Station C by its ceiling door (door_teleport
    from the Metroid Quarantine B's floor door: mines_regiao_d_rota walks there), onto its platform. Samus on the pedestal (where
    the game puts her when it loads the station), a marker in the saved data (game hours 7), YES, "save completed": load station 3
    of area 5, its used-station bit ($7ED902 bit 3); paused, the Mines' map. Game over: the area-select screen picks area 5,
    station 3, and draws "PHAZON / MINES"; continue: back on Save Station C's pedestal, area 5, the marker loaded, the explored
    bits kept (area 5's list in $81)."""
    st = MINES.load_stations[3]
    out = (mines_down(m, room, "save_c") + door_teleport(m, "mines_metroid_quarantine_b", "mines_save_station_c")
           # down through the ceiling door, landed facing forward (pose 0): a turn east stands her up (pose 1)
           + ["wait 60", "hold RIGHT 2", "wait 20"] + full_mines(room, "mines_save_station_c", 5) + [f"expect {WATER_FX_TYPE} 0000", f"shot {IMG_19L}_save_sala.png"]
           + poke16(0x7E09E0, 7))
    for addr, v in ((0x7E0AF6, st.x), (0x7E0B10, st.x), (0x7E0AFA, st.y), (0x7E0B14, st.y)):
        out += poke16(addr, v)
    screens = [("mines_transport_tallon_south", 0, 1), ("mines_save_station_c", 0, 0)]
    return (out + ["hold RIGHT 1", "wait 180", f"shot {IMG_19L}_save_pergunta.png", "hold A 2", "wait 300", "hold A 2",
                   "wait 200", f"expect {LOAD_STATION} 0003", f"expect {AREA} 0005", f"expectbit {USED_STATIONS_AREA5} 08",
                   f"expect {GAME_STATE} 0008", f"shot {IMG_19L}_save_salvo.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}", f"shot {IMG_19L}_save_mapa.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} 0008",
                   "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
                   "hold A 2", "wait 300"]
            + area_select_shows_after(MINES.number, st.index, (TALLON.number,), f"{IMG_19L}_save_tela_de_area.png")
            + ["hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0005", f"expect {ROOM_PTR} {room[st.room]}",
               f"expect {LOAD_STATION} 0003", f"expect {GAME_HOURS} 0007", f"expect 7E0AF6 {st.x:04X}",
               f"shot {IMG_19L}_save_continue.png"]
            + [explored_at(*sc) for sc in screens])


# specs/19h, mines_phazon_elite: the Phazon Elite's arena (tools/chozo/bosses.py ARENAS: the gold ninja pirate's copy in the Elite
# Research) fought with the gear of round 5 (mines_down: the Wave, Ice and Charge Beams, 30 missiles; nothing refilled, no RAM);
# moves of MAGMOOR_MOVES (and a charged shot, "C") found by a beam search in the emulator (scratchpad s19h/scripts/boss.py: its
# health left, the energy, the distance), from this exact entry (as 18h's and 18k's)
IMG_19H = "build/tests/19h"   # the photos of the Phazon Elite's test (specs/img/19h-* are copies of some)
ELITE = "mines_elite_research"
MAGMOOR_MOVES["C"] = ["hold X 70", "wait 10"]   # specs/19h: a charged shot (held, then released)
ELITE_FIGHT = "LLLLLLLLCCL"   # off the R0 shelf west onto the floor; two charged shots (Ice + Wave), a step: its health 0
ELITE_DEATH = 120             # frames of its death (EnemyDeathAnimation): the slot empty
ELITE_ENERGY_AT_WIN = 94      # measured: one touch (40, 10 with the Varia and the Gravity Suits) ... see the spec
ELITE_T3_SLOT, ELITE_R0_SLOT = 38, 39
# from the east wall (where the fight leaves her: walking east 400 frames) up the zigzag (21, 16, 11) onto the ceiling door's
# platform: the walk frames before each jump measured from this state (s19h/scripts/climb.py: windows 47-68, 1-25, 0-11, 1-20,
# the middle taken; 19f's M19F_ELITE_UP starts from the west, at a run)
ELITE_CLIMB = [("LEFT", [(58, 30, -60), (13, 30, -60)]), ("RIGHT", [(6, 30, -60), (11, 30, -60)])]   # the PLM slots of the ceiling door's grey cap and the R0's ice cap


def elite_entry(m: dict, room: dict) -> list[str]:
    """mines_phazon_elite up to the fight: down to the Mines (mines_down: shortcuts, the gear of round 5), door_teleport into the
    Elite Research by its R0 (from the Research Access); the arena alive (the Phazon Elite in slot 0 with full health, 400, the
    quota 1, the bit $08 of area 5 off, the mini-boss song, the grey cap of type 3 on the ceiling door T3, the ice cap on the R0,
    the missile in the west corner)."""
    from chozo import bosses
    arena = bosses.arena_of(ELITE)
    return (mines_down(m, room, "elite") + door_teleport(m, "mines_research_access", ELITE) + [f"expect {ROOM_PTR} {room[ELITE]}"]
            + enemies_alive(MINES, ELITE)
            + ["expect 7E0E52 0001", f"expect {KILLS} 0000", "expect 7ED82D 0000", f"expect 7E07F3 {arena.music[0]:04X}",
               f"expect 7E07F5 {arena.music[1]:04X}", f"expect {plm_slot(PLM_HEADERS, ELITE_T3_SLOT)} C854",
               f"expect {plm_slot(PLM_HEADERS, ELITE_R0_SLOT)} {beam_cap_plm('ice', 'R'):04X}", f"expect {HEALTH} 0063",
               f"shot {IMG_19H}_entrada.png"])


def beam_cap_plm(beam: str, side: str) -> int:
    from tallon import beamdoors
    return beamdoors.PLM[(beam, side)]


def elite_dead(room: dict) -> list[str]:
    """The Elite Research in its dead state: no enemy, the area's song, the ice door's cap on the T3 (Prime's key lock), the bit
    $08 of area 5 on."""
    return ([f"expect {ROOM_PTR} {room[ELITE]}", f"expect {ENEMY_TABLE:06X} 0000", "expectbit 7ED82D 08",
             f"expect 7E07F3 {MINES.music[0]:04X}", f"expect 7E07F5 {MINES.music[1]:04X}",
             f"expect {plm_slot(PLM_HEADERS, ELITE_T3_SLOT)} {beam_cap_plm('ice', 'T'):04X}"])


def mines_phazon_elite(m: dict, room: dict) -> list[str]:
    """specs/19h, mines_phazon_elite: elite_entry (the arena alive, the ceiling door shut by its grey cap); ELITE_FIGHT with the
    gear of round 5, nothing refilled, no RAM: its health 0, its death, the slot empty, the kill count 1, the bit $08 of area 5,
    the song stopped; east against the wall, up the zigzag onto the ceiling door's platform (the grey cap opened by the count: a
    blue door now), a shot up, through it: the Security Access B; back (door_teleport): the dead state (elite_dead). Saved at
    Save Station A (door_teleport: a shortcut), game over, continue: the bit on; back in the Elite Research: dead."""
    st = MINES.load_stations[1]
    out = elite_entry(m, room) + ["# the fight (ELITE_FIGHT) starts here"]
    for i, move in enumerate(ELITE_FIGHT):
        out += MAGMOOR_MOVES[move]
        if i in (7, 8, 9):
            out += [f"shot {IMG_19H}_luta_{i:02d}.png"]
    out += ([f"expect {ENEMY_TABLE + ENEMY_HEALTH:06X} 0000", f"wait {ELITE_DEATH}", f"expect {ENEMY_TABLE:06X} 0000",
             f"expect {KILLS} 0001", "expectbit 7ED82D 08", "expect 7E07F5 0000", f"expect {HEALTH} {ELITE_ENERGY_AT_WIN:04X}",
             f"expect {MISSILES} 001E", f"shot {IMG_19H}_vitoria.png", "hold RIGHT 400", "wait 20"]
            + mines_climb(ELITE_CLIMB) + ["hold RIGHT 10", "wait 20"] + mines_full(room, ELITE, 5, ELITE_ENERGY_AT_WIN)
            + [f"shot {IMG_19H}_porta_aberta.png"] + M19F_UP_DOOR
            + ["wait 60", f"expect {ROOM_PTR} {room['mines_security_access_b']}", f"expect {GAME_STATE} 0008",
               f"expect {HEALTH} {ELITE_ENERGY_AT_WIN:04X}", f"shot {IMG_19H}_security_access_b.png"]
            + door_teleport(m, "mines_security_access_b", ELITE) + ["wait 60"] + elite_dead(room) + [f"shot {IMG_19H}_morto.png"]
            + door_teleport(m, "mines_main_quarry", "mines_save_station_a") + [f"poke {HEALTH} 63"])
    for addr, v in ((0x7E0AF6, st.x), (0x7E0B10, st.x), (0x7E0AFA, st.y), (0x7E0B14, st.y)):
        out += poke16(addr, v)
    return (out + ["hold RIGHT 1", "wait 180", "hold A 2", "wait 300", "hold A 2", "wait 200", f"expect {LOAD_STATION} 0001",
                   f"expect {AREA} 0005", "poke 7E09C2 00", "poke 7E09C3 00", "wait 400",
                   f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}", "hold A 2", "wait 300", "hold A 2", "wait 200"]
            + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {ROOM_PTR} {room[st.room]}", "expectbit 7ED82D 08"]
            + door_teleport(m, "mines_research_access", ELITE) + ["wait 60"] + elite_dead(room)
            + [f"shot {IMG_19H}_depois_do_continue.png"])


# specs/19k, mines_omega_pirate: the Omega Pirate's arena (tools/chozo/bosses.py ARENAS: the Bomb Torizo's second copy in the
# Elite Quarters) fought with the gear of round 6 (mines_down's round 5 + 10 power bombs and the Plasma Beam, as mines_regiao_c_rota;
# 30 missiles; nothing refilled, no RAM in the fight): no uncharged beam hurts it, so missiles (100 each: 12 of its 1200, one
# every ~3 shots past its flashes). Moves of MAGMOOR_MOVES found by a greedy search in the emulator (scratchpad
# s19k/greedy.py: each step every candidate move from the state, the best by its health lost, Samus' energy and the missiles),
# from this exact entry
IMG_19K = "build/tests/19k"   # the photos of the Omega Pirate's test (specs/img/19k-* are copies of some)
OMEGA = "mines_elite_quarters"
OMEGA_FIGHT = ("rSRRRRRRRRRespesppespespespesppppppppppppppppppppppppesppesppesppespppppespesrpes")   # east, missiles: its health 0
OMEGA_DEATH = 400              # frames of its death (Torizo_Instr_38 sets the bit at the end: the Thardus' measure)
OMEGA_ENERGY_AT_WIN = 95       # measured: two touches (8, 2 with the Varia and the Gravity Suits)
OMEGA_MISSILES_AT_WIN = 19     # measured: 11 missiles hit or missed, one picked up from its drops
OMEGA_L1_SLOT, OMEGA_R0_SLOT = 38, 39   # the PLM slots of the doors' caps (measured: the L1's first; alive C848 / C842 grey)


def omega_entry(m: dict, room: dict) -> list[str]:
    """mines_omega_pirate up to the fight: down to the Mines (mines_down: shortcuts, the gear of round 5), the round-6 gear by RAM
    (10 power bombs, the Plasma Beam), door_teleport into the Elite Quarters by its L1 (from the Elite Quarters Access); the arena
    alive (the Omega Pirate in slot 0 with full health, 1200, at the Torizo's spot (776, 368), the bits $04 and $10 of area 5 off,
    the Torizo's song set $24, the grey caps of type 2 on the R0 and the L1)."""
    from chozo import bosses
    arena = bosses.arena_of(OMEGA)
    return (mines_down(m, room, "omega") + poke16(0x7E09CE, 10) + poke16(0x7E09D0, 10)
            + give_beams(ICE_BEAM | WAVE_BEAM | PLASMA_BEAM | CHARGE_EQUIPMENT)
            + door_teleport(m, "mines_elite_quarters_access", OMEGA) + [f"expect {ROOM_PTR} {room[OMEGA]}"]
            + enemies_alive(MINES, OMEGA)
            + ["expect 7E0F7A 0308", "expect 7E0F7E 0170", "expect 7ED82D 0000", f"expect 7E07F3 {arena.music[0]:04X}",
               f"expect {plm_slot(PLM_HEADERS, OMEGA_L1_SLOT)} C848", f"expect {plm_slot(PLM_HEADERS, OMEGA_R0_SLOT)} C842",
               f"expect {HEALTH} 0063", f"shot {IMG_19K}_entrada.png"])


def omega_dead(room: dict) -> list[str]:
    """The Elite Quarters in its dead state: no enemy, the area's song, the plasma doors' caps on the R0 and the L1 (Prime's key
    locks), no grey cap, the bits $04 and $10 of area 5 on."""
    return ([f"expect {ROOM_PTR} {room[OMEGA]}", f"expect {ENEMY_TABLE:06X} 0000", "expectbit 7ED82D 14",
             f"expect 7E07F3 {MINES.music[0]:04X}", f"expect 7E07F5 {MINES.music[1]:04X}",
             f"expect {plm_slot(PLM_HEADERS, OMEGA_L1_SLOT)} {beam_cap_plm('plasma', 'L'):04X}",
             f"expect {plm_slot(PLM_HEADERS, OMEGA_R0_SLOT)} {beam_cap_plm('plasma', 'R'):04X}"])


def mines_omega_pirate(m: dict, room: dict) -> list[str]:
    """specs/19k, mines_omega_pirate: omega_entry (the arena alive, both doors shut); OMEGA_FIGHT with the gear of round 6,
    nothing refilled, no RAM: its health 0 (the uncharged beams never hurt it: only the missiles took it down), its death
    (OMEGA_DEATH frames), the slot empty, the bits $04 (the Torizo's, its own code) and $10 (the arena's) of area 5, the song
    stopped; west along the floor to the L1, its grey cap opened by the bit (a blue door now: a shot opens it), through it: the
    Elite Quarters Access; back (door_teleport): the dead state (omega_dead), again from the Processing Center Access: dead."""
    out = omega_entry(m, room) + ["# the fight (OMEGA_FIGHT) starts here"]
    for i, move in enumerate(OMEGA_FIGHT):
        out += MAGMOOR_MOVES[move]
        if i in (14, 38, 60):
            out += [f"shot {IMG_19K}_luta_{i:02d}.png"]
    return (out + [f"expect {ENEMY_TABLE + ENEMY_HEALTH:06X} 0000", f"shot {IMG_19K}_morrendo.png", f"wait {OMEGA_DEATH}",
                   f"expect {ENEMY_TABLE:06X} 0000", "expectbit 7ED82D 14", "expect 7E07F5 0000",
                   f"expect {HEALTH} {OMEGA_ENERGY_AT_WIN:04X}", f"expect {MISSILES} {OMEGA_MISSILES_AT_WIN:04X}",
                   f"shot {IMG_19K}_vitoria.png", "hold SELECT 2", "wait 10", "hold SELECT 2", "wait 10", "hold SELECT 2",
                   "wait 10", f"expect {HUD_ITEM} 0000", "hold LEFT 400", "wait 20",
                   f"shot {IMG_19K}_porta_aberta.png"] + moves("E")
            + ["wait 60", f"expect {ROOM_PTR} {room['mines_elite_quarters_access']}", f"expect {GAME_STATE} 0008",
               f"expect {HEALTH} {OMEGA_ENERGY_AT_WIN:04X}", f"shot {IMG_19K}_elite_quarters_access.png"]
            + door_teleport(m, "mines_elite_quarters_access", OMEGA) + ["wait 60"] + omega_dead(room) + [f"shot {IMG_19K}_morto.png"]
            + door_teleport(m, "mines_processing_center_access", OMEGA) + ["wait 60"] + omega_dead(room))


# specs/20e: the Impact Crater's way in (tools/impact/rooms.py TELEPORTER, region A). The Omega Pirate's death by RAM: the bit $10 of
# area 5 its arena sets when the fight is won (MINES_OMEGA_WON_BY_RAM; mines_omega_pirate wins it for real and reads the bit);
# the round-6 gear by RAM (mines_gear with the Plasma Beam). The temple's teleporter = an elevator inside area 0
IMG_20E = "build/tests/20e"   # the photos of the 20e tests (specs/img/20e-* are copies of some)
TEMPLE, CRATER_ENTRY, CRATER_TUNNEL_A = "tallon_artifact_temple", "impact_entry_point", "impact_tunnel_a"
CRATER_TO_SAVE = 96   # frames of LEFT from the Entry Point's platform to stop on the save pedestal (measured: 92-100 stop on it)


def crater_gear() -> list[str]:
    """The gear of round 6 by RAM: mines_gear's with the Plasma Beam (the crater's doors are plasma)."""
    return mines_gear(beams=PLASMA_BEAM | WAVE_BEAM | ICE_BEAM | CHARGE_EQUIPMENT)


def crater_down(m: dict, room: dict, tag: str) -> list[str]:
    """Shortcut: from the landing into the Artifact Temple (door_teleport from the Temple Lobby) with the Omega Pirate dead by RAM
    (the platform there: the elevator's species in slot 0), onto the pad, down: the crater's Entry Point, area 0 still; the gear of
    round 6 by RAM."""
    return (MINES_OMEGA_WON_BY_RAM + poke16(0x7E0911, 0) + ["wait 2"] + door_teleport(m, "tallon_temple_lobby", TEMPLE)
            + [f"expect {ROOM_PTR} {room[TEMPLE]}", f"expect {ENEMY_TABLE:06X} D73F"] + onto_platform(TEMPLE)
            + [f"shot {IMG_20E}_{tag}_templo_plataforma.png"] + ride_elevator(room, TEMPLE, f"{IMG_20E}_{tag}_descendo.png")
            + [f"expect {AREA} 0000", f"shot {IMG_20E}_{tag}_chegada.png"] + crater_gear())


def crater_entrance_route(m: dict, room: dict) -> list[str]:
    """specs/20e, impact_entrada_rota: in the Artifact Temple with the Omega Pirate alive (its arena's bit clear): no platform
    (slot 0 empty), Samus on the pad (elevator_flags kept off by the state's main ASM) presses DOWN and nothing happens (no ride,
    still in the temple). The bit set (crater_down): out and back in, the platform is there; down to the Entry Point (area 0, no area change);
    WALKING from the platform east, a shot (the Plasma Beam) opens the R1 plasma cap, through it: the Crater Tunnel A; along it to
    its east end (the R0 was a wall until 20f; now its closed plasma cap: impact_regiao_b_rota goes through it), back west, a shot opens the L0 plasma cap, through it: the Entry Point; onto the
    platform, UP: back in the temple; paused, area 0's map shows the crater's screens walked (explored) and the name TALLON."""
    sx, sy = platform_screen(CRATER_ENTRY)
    out = (poke16(0x7E0911, 0) + ["wait 2"] + door_teleport(m, "tallon_temple_lobby", TEMPLE)
           + [f"expect {ROOM_PTR} {room[TEMPLE]}", "expect 7ED82C 0000", f"expect {ENEMY_TABLE:06X} 0000"]
           # on the pad: its door blocks set elevator_flags, the state's main ASM clears them every frame (no platform AI)
           + [f"expect {ELEVATOR_FLAGS} 0000" if line == f"expect {ELEVATOR_FLAGS} 0001" else line for line in onto_platform(TEMPLE)]
           + [f"shot {IMG_20E}_rota_templo_apagado.png", "hold DOWN 1", "wait 300",
              f"expect {ROOM_PTR} {room[TEMPLE]}", f"expect {ELEVATOR_STATUS} 0000", f"expect {ELEVATOR_FLAGS} 0000",
              f"expect {GAME_STATE} 0008", f"expect {ENEMY_TABLE:06X} 0000",
              "hold UP 2", "wait 30"]   # DOWN crouched her: up again
           # the temple loaded again (crater_down's door_teleport from the Temple Lobby's floor door: going up through the
           # ceiling door to the lobby first left her hanging there, frozen in a fall, measured)
           + crater_down(m, room, "rota") + [explored_at(CRATER_ENTRY, sx, sy)]
           + M19F_OUT["RIGHT"] + [f"expect {ROOM_PTR} {room[CRATER_TUNNEL_A]}", f"expect {GAME_STATE} 0008",
                                  f"expect {AREA} 0000", f"expect {HEALTH} 0063", f"shot {IMG_20E}_rota_tunnel_a.png"]
           # specs/20f: its east end is the R0 door's plasma cap now (column 30; the wall of 20e was column 31: x $01EB)
           + ["hold RIGHT 400", "wait 30", f"expect {ROOM_PTR} {room[CRATER_TUNNEL_A]}", "expect 7E0AF6 01DB",
              f"shot {IMG_20E}_rota_tunnel_a_fim.png", explored_at(CRATER_TUNNEL_A, 1, 0)]
           + ["hold LEFT 330", "wait 10"] + M19F_OUT["LEFT"]
           + [f"expect {ROOM_PTR} {room[CRATER_ENTRY]}", f"expect {GAME_STATE} 0008", f"shot {IMG_20E}_rota_volta.png"]
           + onto_platform(CRATER_ENTRY) + ride_elevator(room, CRATER_ENTRY, f"{IMG_20E}_rota_subindo.png")
           + [f"expect {AREA} 0000", f"shot {IMG_20E}_rota_templo.png",
              explored_at(CRATER_ENTRY, sx, sy), explored_at(CRATER_TUNNEL_A, 0, 0), explored_at(CRATER_TUNNEL_A, 1, 0)]
           + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
           + pause_shows(TALLON, [(CRATER_ENTRY, sx, sy), (CRATER_TUNNEL_A, 0, 0), (CRATER_TUNNEL_A, 1, 0)], "impact_20e")
           + [f"shot {IMG_20E}_rota_mapa.png", "hold START 10", "wait 200", f"expect {GAME_STATE} 0008"])
    return out


def crater_save(m: dict, room: dict) -> list[str]:
    """specs/20e, impact_save_station: down to the crater (crater_down), WALKING west from the platform, stopping on the save
    pedestal (CRATER_TO_SAVE: the station takes her once she stands on it; running over it does not), a marker in the saved data (game hours 7), YES, "save completed": load station 2 of
    area 0, its used-station bit ($7ED8F8 bit 2). Game over: the area-select screen picks area 0, station 2, and draws "TALLON /
    OVERWORLD"; continue: on the Entry Point's pedestal, area 0, the marker loaded, the crater's explored bit kept, the Omega
    Pirate's bit kept (the saved boss bits)."""
    st = TALLON.load_stations[TALLON.station_in(CRATER_ENTRY)]
    sx, sy = platform_screen(CRATER_ENTRY)
    return (crater_down(m, room, "save") + poke16(0x7E09E0, 7) + [f"hold LEFT {CRATER_TO_SAVE}", "wait 180", f"shot {IMG_20E}_save_pergunta.png",
                                                                  "hold A 2", "wait 300", "hold A 2", "wait 200",
                                                                  f"expect {LOAD_STATION} {st.index:04X}", f"expect {AREA} 0000",
                                                                  f"expectbit {USED_STATIONS_AREA0} {1 << st.index:02X}",
                                                                  f"expect {GAME_STATE} 0008", f"expect 7E0AF6 {st.x:04X}",
                                                                  f"shot {IMG_20E}_save_salvo.png",
                                                                  "poke 7E09C2 00", "poke 7E09C3 00", "wait 400",
                                                                  f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}", "hold A 2", "wait 300"]
            + area_select_shows_after(TALLON.number, st.index, (), f"{IMG_20E}_save_tela_de_area.png")
            + ["hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0000", f"expect {ROOM_PTR} {room[CRATER_ENTRY]}",
               f"expect {LOAD_STATION} {st.index:04X}", f"expect {GAME_HOURS} 0007", f"expect 7E0AF6 {st.x:04X}",
               "expectbit 7ED82D 10", explored_at(CRATER_ENTRY, sx, sy), f"shot {IMG_20E}_save_continue.png"])


# specs/20f: the crater's region B (tools/impact/layouts.py: the Phazon Core, the Crater Missile Station, the Crater Tunnel B;
# impact/enemies.py: the Phazon Core's two Metroids). The walks measured in the emulator (scratchpad s20f): the Phazon Core's west
# zigzag is the Mines' Omega Research's (M19I_OR_UP, M19I_DOWN_EAST), its east one the mirror
IMG_20F = "build/tests/20f"   # the photos of the 20f tests (specs/img/20f-* are copies of some)
CRATER_CORE, CRATER_MISSILES, CRATER_TUNNEL_B = "impact_phazon_core", "impact_missile_station", "impact_tunnel_b"
M20F_EAST_UP = (hops("LEFT", [(50, 30, -60), (16, 30, -60)]) + hops("RIGHT", [(6, 30, -60), (6, 24, 30)])
                + ["hold RIGHT 200", "wait 20"])   # from the east wall up the east zigzag onto the R1 shelf (M19I_OR_UP's mirror)
M20F_MS_IN = ["hold LEFT 150", "wait 10"]          # the Missile Station from the R0 off the step west into the station
M20F_MS_OUT = ["hold RIGHT 20", "hold RIGHT+A 30", "hold RIGHT 60", "wait 20"]   # from the station east up onto the step
# the screens impact_regiao_b_rota walks through: explored bits and the pause map
CRATER_B_SCREENS = [(CRATER_CORE, 0, 2), (CRATER_CORE, 4, 2), (CRATER_CORE, 4, 1), (CRATER_TUNNEL_B, 0, 0),
                    (CRATER_TUNNEL_B, 1, 0), (CRATER_CORE, 0, 1), (CRATER_MISSILES, 0, 0)]


def crater_route_b(m: dict, room: dict) -> list[str]:
    """specs/20f, impact_regiao_b_rota: down to the crater (crater_down: the Omega Pirate dead by RAM, the round-6 gear); then
    WALKING, the plasma doors opened by the Plasma Beam, energy 99 all the way: the Entry Point east to the Tunnel A, along it,
    its R0 (a wall in 20e): the Phazon Core at the bottom of its west wall (L2), its two Metroids alive (off camera, high in the
    hall); along the floor to the east wall, up the east zigzag onto the R1 shelf, the R1: the Tunnel B to its east end (the R0
    a wall until 20g; its closed plasma cap since: impact_descida_rota goes through it); back west through its L0 to the Phazon Core's R1 shelf, down to the floor, west to the west wall, up the
    west zigzag onto the L1 shelf, the L1: the Crater Missile Station, west into its station with 10 missiles: refilled to the
    maximum (30); out east through the R0 to the L1 shelf, down, west to the L2: the Tunnel A, the Entry Point, onto the
    platform, up to the temple. Each screen's explored bit; the pause map ("TALLON")."""
    full = lambda key, feet: mines_full(room, key, feet)   # noqa: E731
    shot = lambda name: f"shot {IMG_20F}_rota_{name}.png"   # noqa: E731
    sx, sy = platform_screen(CRATER_ENTRY)
    return (crater_down(m, room, "rota_b") + M19F_OUT["RIGHT"] + full(CRATER_TUNNEL_A, 9)
            + ["hold RIGHT 400", "wait 30"] + M19F_OUT["RIGHT"] + full(CRATER_CORE, 41)
            + enemies_alive(TALLON, CRATER_CORE) + [shot("phazon_core")]
            + ["hold RIGHT 900", "wait 30"] + M20F_EAST_UP + full(CRATER_CORE, 25) + [shot("prateleira_r1")]
            + M19F_OUT["RIGHT"] + full(CRATER_TUNNEL_B, 9) + [shot("tunnel_b")]
            # its east end: specs/20g, the R0's plasma cap (column 30; the wall of 20f was column 31: x $01EB)
            + ["hold RIGHT 400", "wait 30", f"expect {ROOM_PTR} {room[CRATER_TUNNEL_B]}", "expect 7E0AF6 01DB",
               shot("tunnel_b_fim"), "hold LEFT 330", "wait 10"] + M19F_OUT["LEFT"] + full(CRATER_CORE, 25)
            + M19I_DOWN_WEST + full(CRATER_CORE, 41) + ["hold LEFT 900", "wait 30"] + M19I_OR_UP + full(CRATER_CORE, 25)
            + enemies_alive(TALLON, CRATER_CORE) + M19F_OUT["LEFT"] + full(CRATER_MISSILES, 9) + [shot("missile_station")]
            + poke16(0x7E09C6, 10) + ["wait 2", f"expect {MISSILES} 000A"] + M20F_MS_IN + ["wait 200", shot("recarga")]
            + P18F_DISMISS + [f"expect {MISSILES} 001E", f"expect {MAX_MISSILES} 001E", f"expect {GAME_STATE} 0008",
                              f"expect {HEALTH} 0063"]
            + M20F_MS_OUT + M19F_OUT["RIGHT"] + full(CRATER_CORE, 25) + M19I_DOWN_EAST + full(CRATER_CORE, 41)
            + ["hold LEFT 900", "wait 30"] + M19F_OUT["LEFT"] + full(CRATER_TUNNEL_A, 9)
            + ["hold LEFT 330", "wait 10"] + M19F_OUT["LEFT"] + full(CRATER_ENTRY, 25) + [shot("volta")]
            + onto_platform(CRATER_ENTRY) + ride_elevator(room, CRATER_ENTRY, f"{IMG_20F}_rota_subindo.png")
            + [f"expect {AREA} 0000", f"expect {ROOM_PTR} {room[TEMPLE]}", shot("templo")]
            + [explored_at(*screen) for screen in CRATER_B_SCREENS] + [explored_at(CRATER_ENTRY, sx, sy)]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(TALLON, CRATER_B_SCREENS, "impact_20f") + [shot("mapa"), "hold START 10", "wait 200",
                                                                    f"expect {GAME_STATE} 0008"])


# specs/20f, impact_inimigos_vivos: the Phazon Core entered by each of its three doors (enter_through, a shortcut); the photos
# of its Metroids (tallon_look: Samus on the east end of each one's perch, the camera on its screen; 120 frames: at 30, as the
# Mines', the screen was still black from the pause, measured), each after the room loaded again (the Metroid of the first look
# holds on to Samus: the next pause did not take, measured)
CRATER_ENEMY_LOOKS = [(27, 12, 256, 0, "metroide_oeste", 120), (57, 12, 768, 0, "metroide_leste", 120)]


def crater_enemies_test(m: dict, room: dict) -> list[str]:
    """specs/20f, impact_inimigos_vivos: down to the crater (crater_down); into the Phazon Core through each neighbour's door
    to it (the Tunnel A, the Missile Station, the Tunnel B: enter_through, a shortcut, as mines_inimigos_vivos): both Metroids of
    tools/impact/enemies.py in their slots of the WRAM table with the species' full health, standing still at the door 300
    frames (the transition and 2 s more) she loses no energy; a photo of each Metroid (tallon_look). (spec 15: the door audit
    with real entries, every door of the Phazon Core, is entradas_de_porta_tallon: area 0's.)"""
    out = crater_down(m, room, "vivos")
    for frm in (CRATER_TUNNEL_A, CRATER_MISSILES, CRATER_TUNNEL_B):
        enter = enter_through(m, room, frm, CRATER_CORE)
        enter[-3:-3] = ["wait 10", f"poke {HEALTH} 63"]   # refilled in the transition (mines_inimigos_vivos)
        out += [f"poke {HEALTH} 63"] + enter + enemies_alive(TALLON, CRATER_CORE) + [f"expect {HEALTH} 0063"]
    for x, floor, cx, cy, name, settle in CRATER_ENEMY_LOOKS:
        out += (enter_through(m, room, CRATER_TUNNEL_A, CRATER_CORE) + enemies_alive(TALLON, CRATER_CORE)
                + tallon_look(x, floor, cx, cy, f"{IMG_20F}_{name}.png", settle))
    return out


# specs/20g: the crater's region C (tools/impact/layouts.py: the Phazon Infusion Chamber, Subchambers One to Five; the phazon that
# hurts = SM's acid in Subchambers One, Two and Four, impact/layouts.py ACID). The walks measured in the emulator (scratchpad
# s20g/drv.py): the Infusion Chamber's climb is the Phazon Core's west one (M19I_OR_UP: the same columns, the shelf 4 rows over the
# top ledge here); coming up through its floor door (no cap) she gets control ~150 frames after the jump, 51 px over the floor, in
# the middle of the hole: a spin jump into the ceiling door and the Space Jump west when the control comes back (M20G_RISE_WEST),
# or she falls back down the hole (measured: with a straight jump and the direction held, x did not move)
IMG_20G = "build/tests/20g"   # the photos of the 20g tests (specs/img/20g-* are copies of some)
CRATER_INFUSION, CRATER_SUB1, CRATER_SUB2 = "impact_infusion_chamber", "impact_subchamber_one", "impact_subchamber_two"
M20G_INTO_HOLE = ["hold RIGHT 185", "wait 400"]   # the Infusion Chamber from the L0 shelf east, down the ledges, into the hole
M20G_TO_L2 = ["hold LEFT 300", "wait 60"]         # the Subchamber One from its platform west down the zigzag to the L2
M20G_TO_CLIMB = ["hold RIGHT 262", "wait 30", "hold LEFT 2", "wait 20", "hold LEFT 64"]   # from the L2 east, short of the pool
# up the Subchamber One's zigzag (37 .. 7: a jump west onto 37, then three times west and east), onto the platform, under the door
M20G_SUB1_UP = (["hold LEFT+A 30", "hold LEFT 10", "wait 60"]
                + sum(([f"hold {d} {w}", f"hold {d}+A 30", f"hold {d} 4", "wait 60"] for d, w in [("LEFT", 14), ("RIGHT", 6)] * 3), [])
                + ["hold RIGHT 16", "hold RIGHT+A 30", "hold RIGHT 6", "wait 30", "hold RIGHT 14", "wait 20"])
M20G_RISE_WEST = ["hold LEFT 2", "wait 10", "hold LEFT+A 3", "hold A 27", "wait 126", "hold LEFT 24", "hold LEFT+A 20",
                  "hold LEFT 30", "wait 60"]
M20G_POOL_IN = ["hold RIGHT 300", "wait 60"]      # from the L2 east along the floor into the pool (its east wall)
M20G_POOL_OUT = ["hold LEFT+A 30", "hold LEFT 20", "wait 30"]   # a jump west out of it, onto the floor
CRATER_C_SCREENS = [(CRATER_INFUSION, 0, 0), (CRATER_INFUSION, 1, 1), (CRATER_SUB1, 2, 0), (CRATER_SUB1, 0, 2)]


def crater_route_c(m: dict, room: dict) -> list[str]:
    """specs/20g, impact_descida_rota: down to the crater (crater_down: the Omega Pirate dead by RAM, the round-6 gear), into the
    Tunnel B (door_teleport from the Phazon Core's R1, a shortcut: region B's walk is impact_regiao_b_rota's); then WALKING, energy
    99 all the way (no phazon on the way): east, the R0's plasma cap shot: the Infusion Chamber's L0 shelf; east down its ledges
    into the hole (no door): the Subchamber One, on its ceiling door's platform; west down its zigzag to the floor, the L2 (a blue
    cap, shot): the Subchamber Two's R0 shelf; back east: the Subchamber One's L2; east along the floor (short of the pool), up
    its zigzag onto the platform, a spin jump up through the ceiling door: the Infusion Chamber's hole, the Space Jump west onto
    its floor; west to the wall, up its zigzag onto the L0 shelf, the L0: the Tunnel B. Each room's explored bits; the pause map."""
    full = lambda key, feet: mines_full(room, key, feet)   # noqa: E731
    shot = lambda name: f"shot {IMG_20G}_rota_{name}.png"   # noqa: E731
    return (crater_down(m, room, "rota_c") + door_teleport(m, CRATER_CORE, CRATER_TUNNEL_B) + full(CRATER_TUNNEL_B, 9)
            + ["hold RIGHT 400", "wait 30"] + M19F_OUT["RIGHT"] + full(CRATER_INFUSION, 9) + [shot("infusion")]
            + M20G_INTO_HOLE + full(CRATER_SUB1, 5) + [shot("subchamber_one")]
            + M20G_TO_L2 + full(CRATER_SUB1, 41) + M19F_OUT["LEFT"] + full(CRATER_SUB2, 9) + [shot("subchamber_two")]
            + M19F_OUT["RIGHT"] + full(CRATER_SUB1, 41)
            + M20G_TO_CLIMB + M20G_SUB1_UP + full(CRATER_SUB1, 5) + [shot("plataforma")]
            + M20G_RISE_WEST + full(CRATER_INFUSION, 28) + [shot("subiu")]
            + ["hold LEFT 200", "wait 20"] + M19I_OR_UP + full(CRATER_INFUSION, 9)
            + M19F_OUT["LEFT"] + full(CRATER_TUNNEL_B, 9) + [shot("tunnel_b")]
            + [explored_at(*screen) for screen in CRATER_C_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(TALLON, CRATER_C_SCREENS, "impact_20g") + [shot("mapa"), "hold START 10", "wait 200",
                                                                    f"expect {GAME_STATE} 0008"])


# specs/20g, impact_phazon_dano: SM's acid with the round-6 gear (the Gravity Suit: a quarter of 1.5 a frame, Samus_Animate_AcidFx
# $90:8219 and Samus_HandlePeriodicDamage; smlib/lava.py ACID_DAMAGE_PER_FRAME), measured: in PHAZON_FRAMES frames in the pool
# she loses PHAZON_DROP; on the floor beside it, PHAZON_FRAMES frames, nothing
PHAZON_FRAMES = 120
PHAZON_DROP = 45


def crater_phazon_test(m: dict, room: dict) -> list[str]:
    """specs/20g, impact_phazon_dano: down to the crater (crater_down), into the Subchamber One through the Infusion Chamber's hole
    (door_teleport, a shortcut): energy 99, the acid's FX loaded (type 4, its surface); west down to the floor, 120 frames there
    (the way, energy 99); east
    along the floor into the pool of phazon (the acid's FX in the room, its surface on row impact/layouts.py ACID): in it, from
    99, PHAZON_FRAMES frames later 99 - PHAZON_DROP; a jump west out of it onto the floor: PHAZON_FRAMES frames more, the energy
    the same (out of the phazon, no damage); photos in and out."""
    full = lambda key, feet: mines_full(room, key, feet)   # noqa: E731
    shot = lambda name: f"shot {IMG_20G}_dano_{name}.png"   # noqa: E731
    # (put at the hole by RAM, she stops 5 px over the platform, measured: walked in, impact_descida_rota, she stands on it)
    out = (crater_down(m, room, "dano") + door_teleport(m, CRATER_INFUSION, CRATER_SUB1)
           + [f"expect {ROOM_PTR} {room[CRATER_SUB1]}", f"expect {GAME_STATE} 0008", f"expect {HEALTH} 0063"]
           + [f"expect {WATER_FX_TYPE} 0004", f"expect 7E1962 {impact_layouts.ACID[CRATER_SUB1] * 16:04X}"]
           + M20G_TO_L2 + full(CRATER_SUB1, 41) + ["wait 120", f"expect {HEALTH} 0063"]
           + M20G_POOL_IN + [f"expect 7E0AFA {(impact_layouts.SUB1_FLOOR + 3) * 16 - 21:04X}", f"poke {HEALTH} 63", "poke 7E09C3 00",
                             f"wait {PHAZON_FRAMES}", f"expect {HEALTH} {99 - PHAZON_DROP:04X}", shot("na_poca")]
           + M20G_POOL_OUT + magmoor_arrive(room, CRATER_SUB1, 41)[:-1] + [f"poke {HEALTH} 63", "poke 7E09C3 00", f"wait {PHAZON_FRAMES}",
                                                           f"expect {HEALTH} 0063", shot("fora")])
    return out


# specs/20h: Metroid Prime's arena in the Lair (tools/chozo/bosses.py ARENAS: the Bomb Torizo's third copy, METROID_PRIME), fought
# with the round-6 gear by RAM (crater_gear: the Plasma, Ice, Wave and Charge Beams, 30 missiles; nothing refilled, no RAM in the
# fight). Moves of MAGMOOR_MOVES found by a greedy search in the emulator (scratchpad s20h/greedy.py: each step every candidate
# move from the state, the best by its health lost, Samus' energy), from this exact entry
IMG_20H = "build/tests/20h"   # the photos of the 20h tests (specs/img/20h-* are copies of some)
CRATER_SUB5, CRATER_LAIR = "impact_subchamber_five", "impact_lair"
PRIME_DOOR_SLOT = 39   # the PLM slot of the ceiling door's grey cap (measured: the last one, as the Omega's R0)
PRIME_FIGHT = "xXxxrRasahsaraeaexsXsXs"   # east off the platform to the floor, the beams (Plasma + Ice + Wave, 300 a hit): its health 0
PRIME_DEATH = 400              # frames of its death (Torizo_Instr_38 sets the bit at the end: the Omega's measure)
PRIME_ENERGY_AT_WIN = 95       # measured: two touches (8, 2 with the Varia and the Gravity Suits)
# from where the fight ends (x 830 on the floor) west up the zigzag (21, 16, 11) onto the ceiling door's platform (measured)
M20H_UP = [line for d, walk, jump in (("LEFT", 180, "LEFT"), ("LEFT", 18, "LEFT"), ("LEFT", 8, "RIGHT"), ("RIGHT", 16, "RIGHT"))
           for line in (f"hold {d} {walk}", "wait 20", f"hold {jump}+A 30", f"hold {jump} 10", "wait 40")]
# under the door, a shot up (the grey cap open once the bit is set: a shot opens it), a spin jump up through it, the Space Jump
# east when the control comes back in the Subchamber Five's hole (go_through's ceiling door), onto its floor east of the hole
M20H_OUT = (["hold RIGHT 16", "wait 20", "hold UP 6", "hold UP+X 2", "hold UP 4", "wait 66", "hold LEFT 14", "wait 10",
             "hold RIGHT 8", "hold RIGHT+A 30"] + ["hold RIGHT 1", "hold RIGHT+A 1"] * 90 + ["hold RIGHT 40", "wait 60"])
# on the platform with the arena alive: three shots up at the grey cap and the same spin jump: the cap stays, she stays in the Lair
M20H_SHUT = ["wait 10"] + ["hold UP+X 2", "wait 12"] * 3 + ["wait 30", "hold LEFT 14", "wait 10", "hold RIGHT 8",
                                                              "hold RIGHT+A 30", "wait 200"]


def prime_entry(m: dict, room: dict, tag: str) -> list[str]:
    """impact_metroid_prime up to the fight: down to the crater (crater_down: the Omega Pirate dead by RAM, the round-6 gear), into
    the Lair through the Subchamber Five's floor door (door_teleport, a shortcut: the descent is impact_descida_rota's), on the
    ceiling door's platform; the arena alive (Metroid Prime in slot 0 with full health, 3000, at the Torizo's spot (776, 368), the bits $04 and
    $10 of area 0 off, the Torizo's song set $24, the ceiling door's grey cap of type 2)."""
    from chozo import bosses
    arena = bosses.arena_of(CRATER_LAIR)
    return (crater_down(m, room, tag) + door_teleport(m, CRATER_SUB5, CRATER_LAIR)
            + [f"expect {ROOM_PTR} {room[CRATER_LAIR]}", f"expect {GAME_STATE} 0008"] + enemies_alive(TALLON, CRATER_LAIR)
            + ["expect 7E0F7A 0308", "expect 7E0F7E 0170", "expect 7ED828 0000", f"expect 7E07F3 {arena.music[0]:04X}",
               f"expect {plm_slot(PLM_HEADERS, PRIME_DOOR_SLOT)} C854", f"expect {HEALTH} 0063",
               f"shot {IMG_20H}_{tag}_entrada.png"])


def prime_dead(room: dict) -> list[str]:
    """The Lair in its dead state: no enemy, the area's song, no cap PLM on the ceiling door (Prime has no door there; the level's
    blue cap, any shot opens it), the bits $04 and $10 of area 0 on."""
    return ([f"expect {ROOM_PTR} {room[CRATER_LAIR]}", f"expect {ENEMY_TABLE:06X} 0000", "expectbit 7ED828 14",
             f"expect 7E07F3 {TALLON.music[0]:04X}", f"expect 7E07F5 {TALLON.music[1]:04X}",
             f"expect {plm_slot(PLM_HEADERS, PRIME_DOOR_SLOT)} 0000", f"expect {PLM_HEADERS:06X} 0000"])


def prime_won(m: dict, room: dict, tag: str = "luta") -> list[str]:
    """prime_entry (the arena alive, the ceiling door shut); PRIME_FIGHT with the round-6 gear, nothing refilled, no RAM: its
    health 0 by the beams' real hits (300 each), its death (PRIME_DEATH frames), the slot empty, the bits $04 (the Torizo's, its
    own code) and $10 (the arena's: the final boss beaten) of area 0, the song stopped; WALKING west up the zigzag onto the
    ceiling door's platform. `tag` names the photos (two tests run it)."""
    out = prime_entry(m, room, tag) + ["# the fight (PRIME_FIGHT) starts here"]
    for i, move in enumerate(PRIME_FIGHT):
        out += MAGMOOR_MOVES[move]
        if i in (7, 15):
            out += [f"shot {IMG_20H}_{tag}_{i:02d}.png"]
    return (out + [f"expect {ENEMY_TABLE + ENEMY_HEALTH:06X} 0000", f"shot {IMG_20H}_{tag}_morrendo.png", f"wait {PRIME_DEATH}",
                   f"expect {ENEMY_TABLE:06X} 0000", "expectbit 7ED828 14", "expect 7E07F5 0000",
                   f"expect {HEALTH} {PRIME_ENERGY_AT_WIN:04X}", f"shot {IMG_20H}_{tag}_vitoria.png"]
            + M20H_UP + [f"expect {ROOM_PTR} {room[CRATER_LAIR]}", f"expect 7E0AFA {6 * 16 - 21:04X}",
                         f"expect {GAME_STATE} 0008", f"shot {IMG_20H}_{tag}_plataforma.png"])


def impact_metroid_prime(m: dict, room: dict) -> list[str]:
    """specs/20h, impact_metroid_prime: the fight won for real and up onto the ceiling door's platform (prime_won). specs/20i: from
    there the door is the game's end (impact_fim_do_jogo); 20h's way back up to the Subchamber Five and the temple, and the Lair's
    dead state seen in a visit after the win, are gone with it (no play reaches them now: the validator reads the dead state)."""
    return prime_won(m, room)


# specs/20i: the game's end (tools/impact/ending.py): after the win, the cap shot open and a spin jump up into the ceiling door; her
# top past the cap's bottom edge inside the door's columns, the Lair's main ASM locks her and starts the SM's ending (game state
# $26, the fade, then $27: the ending, the credits, the rate screen). Measured (scratchpad s20i): locked at Y 57 the 4th frame of
# the jump (state $26), $27 16 frames later; the rate's digits written 13176..13676 frames after; the cinematic function then
# nullsub_127 ($8B:E7BA) for good (the credits done, the screen stays)
IMG_20I = "build/tests/20i"
M20I_EXIT = M20H_OUT[:9] + ["hold RIGHT+A 6"]   # the shot that opens the cap, the spin jump: 6 frames of it
EXIT_LOCK_Y = 57
ENDING_CREDITS_AT, ENDING_RATE_AT = 7000, 14000   # frames after the exit: the credits rolling, the rate screen
ENDING_DONE = 0xE7BA          # nullsub_127: the ending's last cinematic function (an RTS)
# the exit's spot by RAM (impact_fim_sem_vitoria): in the door's columns, her top (62 - 21) past the cap's bottom edge (48)
EXIT_SPOT = (380, 62)


def chain_end_gear() -> tuple[dict, int]:
    """The gear of every placed item of the five areas taken (validate.items_gear: the validator's and the 19m chain's sum, from
    the start's 99 energy) and the number of items."""
    from validate import items_gear, world_items, world_rooms
    placed = world_items({r.key for r in world_rooms()})
    have, unknown = items_gear(placed)
    if unknown:
        raise ValueError(f"20i: {unknown}")
    return have, len(placed)


def impact_end(m: dict, room: dict) -> list[str]:
    """specs/20i, impact_fim_do_jogo: prime_won (the fight won for real, no RAM in it); on the platform, the gear of the whole
    chain by RAM (chain_end_gear: the capacities and the item and beam bits of the 88 items; the chain itself is 20j's, the cut
    declared); a shot opens the cap, the spin jump up into the door: in the Lair still, game state $26, Samus held still under
    the door (EXIT_LOCK_Y); then $27 (the ending: no door transition, no temple); the credits rolling (photo); at the end the rate
    screen with the digits CalcItemPercentageCount wrote (ending_digits) for the percentage COMPUTED from that gear with the built
    ROM's tables (item_percentage), which must be one per item and the 19m chain's CHAIN_END_PERCENT (else the script is not
    made); the cinematic at its last function for good (ENDING_DONE, twice, 2000 frames apart)."""
    have, n = chain_end_gear()
    rom = ROM.read_bytes()
    pct = item_percentage(rom, have["energy"], 0, have.get("missiles", 0), have.get("supers", 0), have.get("power_bombs", 0),
                          have.get("items", 0), have.get("beams", 0))
    if pct != n or pct != CHAIN_END_PERCENT:
        raise ValueError(f"20i: a porcentagem do fim com o equipamento da cadeia é {pct}% ({n} itens; a 19m: {CHAIN_END_PERCENT}%)")
    if rom[snes_to_pc(0x8B0000 | ENDING_DONE)] != 0x60:
        raise ValueError("20i: $8B:E7BA não é o RTS do fim dos créditos")
    gear = (poke16(0x7E09C4, have["energy"]) + poke16(0x7E09C8, have.get("missiles", 0)) + poke16(0x7E09C6, have.get("missiles", 0))
            + poke16(0x7E09CC, have.get("supers", 0)) + poke16(0x7E09CA, have.get("supers", 0))
            + poke16(0x7E09D0, have.get("power_bombs", 0)) + poke16(0x7E09CE, have.get("power_bombs", 0))
            + poke16(0x7E09A2, have.get("items", 0)) + poke16(0x7E09A4, have.get("items", 0)) + give_beams(have.get("beams", 0)))
    return (prime_won(m, room, "fim") + ["# specs/20i: the chain's gear by RAM (the percentage's input)"] + gear
            + [f"expect {MAX_ENERGY} {have['energy']:04X}", f"expect {COLLECTED_ITEMS} {have.get('items', 0):04X}",
               f"expect {COLLECTED_BEAMS} {have.get('beams', 0):04X}", f"expect {GAME_STATE} 0008"]
            + M20I_EXIT + [f"expect {ROOM_PTR} {room[CRATER_LAIR]}", f"expect {GAME_STATE} 0026",
                           f"expect 7E0AFA {EXIT_LOCK_Y:04X}", f"shot {IMG_20I}_saida.png", "wait 30",
                           f"expect {GAME_STATE} 0027", f"expect {ROOM_PTR} {room[CRATER_LAIR]}", f"expect 7E0AFA {EXIT_LOCK_Y:04X}",
                           f"wait {ENDING_CREDITS_AT - 30}", f"expect {GAME_STATE} 0027", f"shot {IMG_20I}_creditos.png",
                           f"wait {ENDING_RATE_AT - ENDING_CREDITS_AT}", f"expect {GAME_STATE} 0027",
                           f"expect 7E1F51 {ENDING_DONE:04X}"]
            + ending_digits(rom, pct) + [f"shot {IMG_20I}_porcentagem.png", "wait 2000", f"expect {GAME_STATE} 0027",
                                         f"expect 7E1F51 {ENDING_DONE:04X}"] + ending_digits(rom, pct))


def impact_end_not_won(m: dict, room: dict) -> list[str]:
    """specs/20i, impact_fim_sem_vitoria: prime_entry (the arena alive, the bits $04 and $10 of area 0 off); Samus put by RAM at
    the exit's spot (EXIT_SPOT: in the door's columns, her top past the cap's bottom edge, where the win's exit locks her): 120
    frames later the game state is still 8 (no ending), in the Lair. (The same spot after the win starts the ending at once:
    measured, scratchpad s20i; the test of the real exit is impact_fim_do_jogo.)"""
    x, y = EXIT_SPOT
    spot = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y)):
        spot += poke16(addr, v)
    return (prime_entry(m, room, "sem_vitoria") + spot + ["wait 1", f"expect {GAME_STATE} 0008", "expect 7ED828 0000",
                                                          "wait 120", f"expect {GAME_STATE} 0008",
                                                          f"expect {ROOM_PTR} {room[CRATER_LAIR]}", "expect 7ED828 0000",
                                                          f"shot {IMG_20I}_sem_vitoria.png"])


def impact_prime_death(m: dict, room: dict) -> list[str]:
    """specs/20h, impact_prime_porta_e_morte: saved at the Entry Point's station (crater_save's walk onto the pedestal, a marker:
    game hours 9); into the Lair (door_teleport, a shortcut): the arena alive; on the platform three shots up at the grey cap and a
    spin jump into it: the cap stays (slot PRIME_DOOR_SLOT), she stays in the Lair (no way out before the win). Her energy put at 2
    by RAM (the death made short; the hit is real): east off the platform into Metroid Prime, its touch: energy 0, game over;
    continue: the game's rule, the last save station (the Entry Point's pedestal, area 0, the marker), the bits $04 and $10 of area
    0 off (the fight not won); the Lair again: the arena alive, full health."""
    st = TALLON.load_stations[TALLON.station_in(CRATER_ENTRY)]
    return (crater_down(m, room, "morte") + poke16(0x7E09E0, 9) + [f"hold LEFT {CRATER_TO_SAVE}", "wait 180",
                                                                    "hold A 2", "wait 300", "hold A 2", "wait 200",
                                                                    f"expect {LOAD_STATION} {st.index:04X}"]
            + door_teleport(m, CRATER_SUB5, CRATER_LAIR) + [f"expect {ROOM_PTR} {room[CRATER_LAIR]}"]
            + enemies_alive(TALLON, CRATER_LAIR) + [f"expect {plm_slot(PLM_HEADERS, PRIME_DOOR_SLOT)} C854"]
            + M20H_SHUT + [f"expect {ROOM_PTR} {room[CRATER_LAIR]}", f"expect {GAME_STATE} 0008",
                           f"expect {plm_slot(PLM_HEADERS, PRIME_DOOR_SLOT)} C854", f"shot {IMG_20H}_porta_fechada.png"]
            + [f"poke {HEALTH} 02", "poke 7E09C3 00", "hold RIGHT 200", "wait 700", f"expect {HEALTH} 0000",
               f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}", f"shot {IMG_20H}_game_over.png", "hold A 2", "wait 300",
               "hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0000", f"expect {ROOM_PTR} {room[CRATER_ENTRY]}",
               f"expect {LOAD_STATION} {st.index:04X}", f"expect {GAME_HOURS} 0009", f"expect 7E0AF6 {st.x:04X}",
               "expect 7ED828 0000", f"shot {IMG_20H}_continue.png"]
            + door_teleport(m, CRATER_SUB5, CRATER_LAIR) + [f"expect {ROOM_PTR} {room[CRATER_LAIR]}"]
            + enemies_alive(TALLON, CRATER_LAIR) + [f"expect {plm_slot(PLM_HEADERS, PRIME_DOOR_SLOT)} C854"])


# specs/19g, mines_inimigos_vivos: the rooms with enemies (tools/mines/enemies.py), the neighbour each is entered from, and the
# photos of its enemies (tallon_look: Samus' block, the camera): the Main Quarry's pirate on the crane's arm (Samus on the arm's
# west end, the cable between them) and the one on the floor east of the tower, each 110 frames after the unpause, as it starts
# firing (its laser goes through the cable; at 200 the photo caught Samus blinking, hit); the Elevator Access A's top orb (Samus
# on the top ledge's west end: the orb drifted to the R0 while she stood there) and bottom one (Samus on the floor's west end).
# specs/19i: and region B's rooms with enemies
MINES_ENEMY_ROOMS = [
    ("mines_main_quarry", "mines_quarry_access", [(37, 7, 512, 0, "braco", 110), (69, 42, 1024, 543, "chao_leste", 110)]),
    ("mines_elevator_access_a", "mines_ore_processing", [(5, 11, 0, 0, "orbe_de_cima", 110), (2, 26, 0, 287, "orbe_de_baixo", 110)]),
    # specs/19i: region B: the Elite Control Access' pirate on its catwalk (Samus on the floor west of it), the Ventilation
    # Shaft's Mella (Samus west of it, on the duct's blocks), the Metroid Quarantine A's Metroids (Samus on the floor east of them)
    ("mines_elite_control_access", "mines_elevator_a", [(5, 10, 0, 0, "pirata_passarela", 60)]),
    ("mines_ventilation_shaft", "mines_elite_control", [(9, 10, 128, 0, "mella", 30)]),
    ("mines_metroid_quarantine_a", "mines_quarantine_access_a", [(44, 26, 512, 256, "metroides", 30)]),
]
# specs/19i: the rooms entered by a floor door from above: by RAM from wherever she stood (enter_through) the transition through
# the Quarantine Access A's floor door did not end (game state $0B), so first into the room over it (enter_through from its own
# neighbour: {room: that neighbour}), then through its floor door with Samus put there (door_teleport)
MINES_ENTER_AT_DOOR = {"mines_metroid_quarantine_a": "mines_central_dynamo"}


def mines_enemies_test(m: dict, room: dict) -> list[str]:
    """specs/19g, mines_inimigos_vivos: down the Tallon's P43 to the Mines' P0 (mines_down: shortcuts, the gear of round 5 by
    RAM); then into each region-A room with enemies (enter_through, a shortcut, as chozo_inimigos_vivos): every enemy of
    tools/mines/enemies.py in its slot of the WRAM table with the species' full health (the 2 pirates of the Main Quarry, the 2
    orbs of the Elevator Access A), standing still at the door 300 frames (the transition and 2 s more) she loses no energy; a
    photo of each enemy (tallon_look). (spec 15: this entry is by RAM, Samus not at the door: the door audit with real entries,
    every door, is entradas_de_porta_mines.)"""
    out = mines_down(m, room, "vivos")
    for key, frm, looks in MINES_ENEMY_ROOMS:
        enter = enter_through(m, room, frm, key)
        if key in MINES_ENTER_AT_DOOR:   # specs/19i
            enter = (enter_through(m, room, MINES_ENTER_AT_DOOR[key], frm) + door_teleport(m, frm, key)
                     + [f"expect {ROOM_PTR} {room[key]}", f"expect {GAME_STATE} 0008"])
        enter[-3:-3] = ["wait 10", f"poke {HEALTH} 63"]   # refilled in the transition (chozo_inimigos_vivos, specs/12j)
        out += [f"poke {HEALTH} 63"] + enter + enemies_alive(MINES, key) + [f"expect {HEALTH} 0063"]
        for x, floor, cx, cy, name, settle in looks:
            out += tallon_look(x, floor, cx, cy, f"{IMG_19G}_{name}.png", settle)
    return out

M17H_TTA_TO_DAIS = ["hold LEFT 120", "wait 20"]
M17H_TTA_DAIS_WEST = ["hold RIGHT 40", "wait 20"] + UNMORPH + ["hold LEFT 30", "hold LEFT+A 30", "hold LEFT 20", "hold LEFT 100"]
# back from the transport to Phendrana North: a shot at its door from 4 blocks (point-blank the shot starts past the cap),
# through the Transport Tunnel A over the dais, a shot at the R0 door from the floor
M17H_P13_BACK = ["hold LEFT 40", "hold RIGHT 2", "wait 5", "hold X 2", "wait 30", "hold RIGHT 120", "wait 200"]
M17H_TTA_EAST = ["hold RIGHT 40", "hold RIGHT+A 30", "hold RIGHT 20", "hold RIGHT 70", "wait 20", "hold X 2", "wait 30",
                 "hold RIGHT 150", "wait 200"]
# the Monitor Station's floor east from the L3 door: the 4 lava pits (walk frames before each jump: windows of 13-14 frames
# measured, the middle taken), under the east zigzag, its 3 ledges and the R2 shelf (chain.py, the Triclops Pit's climb)
M17H_STATION_PITS = [(155, 30, 50), (22, 30, 50), (22, 30, 50), (22, 30, 50)]
M17H_STATION_CLIMB = ["hold RIGHT 120", "wait 10", "hold LEFT 9", "hold LEFT+A 30", "wait 60", "hold LEFT 11", "hold LEFT+A 30",
                      "wait 60", "hold RIGHT 10", "hold RIGHT+A 30", "wait 60", "hold RIGHT 20", "hold RIGHT+A 30", "hold RIGHT 60"]
# the Shore Tunnel east: down the step to its floor door (B2), walking into the hole: down into the Fiery Shores' T0 door,
# onto its platform
M17H_SHORE_TUNNEL = ["hold RIGHT 230", "wait 300"]
# the Fiery Shores from the T0 platform: east down the cliff onto the tunnel's ledge (10) and the west zigzag's ledge (16), a
# jump over the first pit onto the first rock; from each rock two shots crouching kill the Viola on the next one; the pits
M17H_SHORES = (["hold RIGHT 60", "wait 30", "hold RIGHT 30", "wait 60", "hold RIGHT 25", "wait 60", "hold RIGHT 20", "wait 60",
                "hold RIGHT 30", "hold RIGHT+A 30", "wait 100"] + moves("cc") + ["wait 30", "hold RIGHT 28", "hold RIGHT+A 30",
                "wait 100"] + moves("cc") + ["wait 30", "hold RIGHT 24", "hold RIGHT+A 30", "wait 100", "hold RIGHT 28",
                "hold RIGHT+A 30", "wait 100"])
M17H_SHORES_CLIMB = ["hold RIGHT 150", "wait 20", "hold LEFT 22", "hold LEFT+A 30", "wait 60", "hold LEFT 17", "hold LEFT+A 30",
                     "wait 60", "hold RIGHT 10", "hold RIGHT+A 30", "wait 60", "hold RIGHT 20", "hold RIGHT+A 30", "hold RIGHT 60"]
M17H_TTB = "xxXxX"                      # the Transport Tunnel B: down to its floor, over its pit, to the east step
M17H_P16_PAD = 26                       # from the P16's L0 door east onto the middle of the elevator's platform (frames)
# the screens magmoor_regiao_b_rota walks through: explored bits and the pause map
MAGMOOR_B_SCREENS = [("magmoor_monitor_station", 0, 0), ("magmoor_monitor_station", 1, 1), ("magmoor_monitor_station", 0, 3),
                     ("magmoor_monitor_station", 5, 3), ("magmoor_monitor_station", 5, 2), ("magmoor_transport_tunnel_a", 0, 0),
                     ("magmoor_transport_tunnel_a", 1, 0), ("magmoor_transport_phendrana_north", 0, 0),
                     ("magmoor_shore_tunnel", 0, 0), ("magmoor_shore_tunnel", 2, 0), ("magmoor_fiery_shores", 0, 0),
                     ("magmoor_fiery_shores", 2, 1), ("magmoor_fiery_shores", 5, 0), ("magmoor_transport_tunnel_b", 0, 0),
                     ("magmoor_transport_tunnel_b", 1, 0), ("magmoor_transport_tallon_west", 0, 0)]


def magmoor_route_b(m: dict, room: dict) -> list[str]:
    """specs/17h, magmoor_regiao_b_rota: from the landing down to the Magmoor's P0 (magmoor_down) and through region A to the
    Monitor Tunnel by door_teleport (shortcuts: region A is walked in magmoor_regiao_a_rota), the gear of round 3 by RAM (the
    Varia Suit, the Space Jump, the Morph Ball and the Bombs; 10 missiles); then WALKING through region B: the Monitor Tunnel
    over its Mellas (alive) into the Monitor Station, down its west zigzag to the floor, the L3 door, the Transport Tunnel A:
    the bomb block of the dais' tunnel bombed, the energy tank rolled into in the ball (bit $D5, 199 energy), on to the
    transport to Phendrana North (decorative) and back; the Monitor Station's 4 pits, its east zigzag up to the R2 shelf; the
    Shore Tunnel and down its floor door into the Fiery Shores (onto the T0 platform); down the cliff, the Violas (alive when
    she comes in) shot dead from the rocks, the pits, up the east zigzag; the Transport Tunnel B; the P16 (the Tallon West
    transport): each room's explored bit and the pause map ("MAGMOOR"); WALKING east onto the elevator's platform, UP: the
    Tallon's Magmoor East transport (area 0). The energy is checked in every room: no heat (the Varia), no lava, no enemy
    touch, no damage in any door's first frames (specs/15)."""
    eq = VARIA_EQUIPMENT | SPACE_JUMP_EQUIPMENT | MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT
    from magmoor import items as magmoor_items
    tank = next(n for n, it in enumerate(magmoor_items.ITEMS) if it.room == "magmoor_transport_tunnel_a")
    return (magmoor_down(m, room, "17h_rota") + poke16(0x7E09A2, eq) + poke16(0x7E09A4, eq) + poke16(0x7E09C6, 10)
            + poke16(0x7E09C8, 10) + ["wait 10"] + chain_teleports(m, room, MAGMOOR_A_PATH)
            + enemies_alive(MAGMOOR, "magmoor_monitor_tunnel") + moves(M17H_MONITOR_TUNNEL)
            + magmoor_b_to_tank(room)
            + ["wait 120", f"shot {IMG_17H}_rota_tanque.png", "wait 300", "hold A 2",
               "wait 120", magmoor_bit(tank), f"expect {MAX_ENERGY} 00C7", f"expect {GAME_STATE} 0008"]
            + magmoor_b_to_p16(room, 0xC7)
            + [explored_at(*sc) for sc in MAGMOOR_B_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(MAGMOOR, MAGMOOR_B_SCREENS, "magmoor_b")
            + [f"shot {IMG_17H}_rota_mapa.png", "hold START 10", "wait 200", f"expect {GAME_STATE} 0008"]
            + [f"hold RIGHT {M17H_P16_PAD}", "wait 20", f"expect {ELEVATOR_FLAGS} 0001", f"shot {IMG_17H}_rota_p16.png"]
            + ride_elevator(room, MAGMOOR_FROM_TALLON, f"{IMG_17H}_rota_subindo.png")
            + [f"expect {HEALTH} 00C7", f"shot {IMG_17H}_rota_tallon.png"])


def magmoor_b_to_tank(room: dict, energy: int = 0x63, sh=region_shot) -> list[str]:
    """Region B walked from the Monitor Station's L0 door down its west zigzag, the L3 door, the Transport Tunnel A's bomb block
    (the last line rolls into the energy tank): the pieces of magmoor_regiao_b_rota (specs/17h), shared with the full chain
    (specs/17j)."""
    return (magmoor_full(room, "magmoor_monitor_station", 9, energy) + [sh(f"{IMG_17H}_rota_monitor_station")]
            + M17H_STATION_DOWN + moves("E") + magmoor_full(room, "magmoor_transport_tunnel_a", 9, energy)
            + M17H_TTA_TO_DAIS + MORPH + [f"expect {POSE} {BALL_POSE_LEFT}", "hold X 2", "wait 90",
                                          f"expect {level_block('magmoor_transport_tunnel_a', 20, 9):06X} 00FF",
                                          "hold LEFT 100"])


def magmoor_b_to_p16(room: dict, energy: int, sh=region_shot) -> list[str]:
    """From the Transport Tunnel A's energy tank (all of `energy` after it) on to the transport to Phendrana North and back,
    the Monitor Station's pits and east zigzag, the Shore Tunnel, the Fiery Shores (its Violas shot dead), the Transport
    Tunnel B, into the P16 (the Tallon West transport)."""
    dead = lambda *slots: [f"expect {ENEMY_TABLE + ENEMY_SLOT * n:06X} 0000" for n in slots]   # noqa: E731
    full = lambda key, feet: magmoor_full(room, key, feet, energy)   # noqa: E731
    return (M17H_TTA_DAIS_WEST + moves("E") + full("magmoor_transport_phendrana_north", 9)
            + [sh(f"{IMG_17H}_rota_phendrana_north")] + M17H_P13_BACK + full("magmoor_transport_tunnel_a", 9)
            + M17H_TTA_EAST + full("magmoor_monitor_station", 57) + hops("RIGHT", M17H_STATION_PITS)
            + [f"expect 7E0AFA {58 * 16 - 21:04X}", f"expect {HEALTH} {energy:04X}", sh(f"{IMG_17H}_rota_monitor_pocos")]
            + M17H_STATION_CLIMB + [f"expect 7E0AFA {42 * 16 - 21:04X}", sh(f"{IMG_17H}_rota_monitor_r2")]
            + moves("D") + full("magmoor_shore_tunnel", 9) + M17H_SHORE_TUNNEL
            + full("magmoor_fiery_shores", 5) + enemies_alive(MAGMOOR, "magmoor_fiery_shores")
            + [sh(f"{IMG_17H}_rota_fiery_shores_t0")] + M17H_SHORES
            + [f"expect 7E0AFA {26 * 16 - 21:04X}", f"expect {HEALTH} {energy:04X}"] + dead(0, 1)
            + [sh(f"{IMG_17H}_rota_fiery_shores_praia")] + M17H_SHORES_CLIMB + [f"expect 7E0AFA {10 * 16 - 21:04X}"]
            + moves("D") + full("magmoor_transport_tunnel_b", 9) + moves(M17H_TTB)
            + ["hold RIGHT 20", "hold RIGHT+A 24", "hold RIGHT 30", "hold RIGHT+X 2", "hold RIGHT 150", "wait 200"]
            + full(MAGMOOR_FROM_TALLON, 9))


# magmoor_regiao_b_itens: the gear of round 6 (+ 5 power bombs); from the Monitor Station's L0 (door_teleport) down, over the
# floor's pits to the R3 door, the Warrior Shrine's power bomb wall, the Fiery Shores' pocket and tunnel, up its T0 door
M17H_B_DOWN = ["hold RIGHT 80", "wait 60", "hold RIGHT 40", "wait 60", "hold RIGHT 40", "wait 300"]
M17H_B_PITS = [(28, 30, -100), (27, 30, -100), (27, 30, -100), (27, 30, -100)]
M17H_B_TO_R3 = ["hold RIGHT 120", "wait 10", "hold X 2", "wait 30", "hold RIGHT 150", "wait 200"]
M17H_SHRINE_TO_WALL = ["hold RIGHT 60", "wait 10", "hold RIGHT+A 30", "hold RIGHT 60", "wait 10", "hold RIGHT 40", "wait 10"]
LAY_POWER_BOMB = ["hold SELECT 2", "wait 10", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0003", "hold X 2", "wait 300",
                  "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0000"]   # the beam again (power bombs -> beam)
# from the Fiery Shores' tunnel ledge (16, after the ball rolls off the tunnel's ledge): onto the tunnel's ledge (10, a jump
# straight up and west over its edge), the cliff (7), the platform (6), under the T0 door; up through it steering west: she
# lands on the Shore Tunnel's floor round its B2 door (its west ledge, row 13) and walks to the step (spec 10b's slack)
M17H_SHORES_UP = ["hold A 12", "hold LEFT+A 18", "hold LEFT 30", "wait 60", "hold LEFT+A 30", "hold LEFT 20", "wait 30",
                  "hold LEFT 20", "wait 20", "hold LEFT+A 20", "hold LEFT 12", "wait 60", "hold LEFT 14", "wait 20"]
M17H_RISE = ["hold A 40", "wait 20", "hold LEFT 200", "wait 100"]


def magmoor_items_b(m: dict, room: dict) -> list[str]:
    """specs/17h, magmoor_regiao_b_itens: from the landing down to the Magmoor's P0 and through region A into the Monitor
    Station by door_teleport (shortcuts), the gear of round 6 by RAM (round 3's + 5 power bombs: the Mines East's, round 5);
    WALKING: down the west zigzag, over the 4 pits, the R3 door: the Warrior Shrine; against its wall, the power bomb block
    (22, 9) stays after a Power Beam shot and a bomb, a power bomb breaks it (one power bomb spent); the ball through its
    tunnel into the R0 door's chamber; standing, the door shot open; the Fiery Shores' pocket: the Missile Expansion (bit $D6,
    15 missiles), in the ball east along the tunnel into the Power Bomb Expansion (bit $D7, 10 power bombs), a power bomb on
    the block at its east mouth (17, 9), out onto the shore's ledges, up onto the T0 door's platform and up through the
    ceiling door, steering west: the Shore Tunnel, on its floor west of the B2 door (spec 10b). Energy 99 the whole way."""
    eq = VARIA_EQUIPMENT | SPACE_JUMP_EQUIPMENT | MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT
    from magmoor import items as magmoor_items
    from tallon import items as tallon_items
    missile, expansion = (next(n for n, it in enumerate(magmoor_items.ITEMS) if it.room == "magmoor_fiery_shores" and it.kind == k)
                          for k in (tallon_items.MISSILE_TANK, tallon_items.POWER_BOMB_ITEM))
    wall, mouth = level_block("magmoor_warrior_shrine", 22, 9), level_block("magmoor_fiery_shores", 17, 9)
    return (magmoor_down(m, room, "17h_itens") + poke16(0x7E09A2, eq) + poke16(0x7E09A4, eq) + poke16(0x7E09C6, 10)
            + poke16(0x7E09C8, 10) + poke16(0x7E09CE, 5) + poke16(0x7E09D0, 5) + ["wait 10"]
            + chain_teleports(m, room, MAGMOOR_A_PATH + ["magmoor_monitor_station"])
            + M17H_B_DOWN + [f"expect 7E0AFA {58 * 16 - 21:04X}"] + hops("RIGHT", M17H_B_PITS) + M17H_B_TO_R3
            + magmoor_arrive(room, "magmoor_warrior_shrine", 9) + M17H_SHRINE_TO_WALL
            + [f"expect {wall:06X} {POWER_BOMB_BLOCK}", f"shot {IMG_17H}_itens_parede.png", "hold X 2", "wait 40",
               f"expect {wall:06X} {POWER_BOMB_BLOCK}"] + MORPH + [f"expect {POSE} {BALL_POSE}", "hold X 2", "wait 120",
                                                                    f"expect {wall:06X} {POWER_BOMB_BLOCK}"]
            + LAY_POWER_BOMB + [f"expect {wall:06X} 00FF", f"expect {POWER_BOMBS} 0004", f"shot {IMG_17H}_itens_parede_aberta.png",
                                "hold RIGHT 60", "wait 10"] + UNMORPH + [f"expect {POSE} {STAND_POSE}"]
            + ["hold LEFT 30", "hold RIGHT 2", "wait 5", "hold X 2", "wait 30", "hold RIGHT 100", "wait 200"]
            + magmoor_arrive(room, "magmoor_fiery_shores", 9) + enemies_alive(MAGMOOR, "magmoor_fiery_shores")
            + [f"shot {IMG_17H}_itens_bolso.png", f"expect {MAX_MISSILES} 000A", "hold RIGHT 30", "wait 420",
               f"shot {IMG_17H}_itens_missil.png", "hold A 2", "wait 120", magmoor_bit(missile), f"expect {MAX_MISSILES} 000F",
               "hold RIGHT 40", "wait 10"] + MORPH + ["hold RIGHT 40", "wait 420", f"shot {IMG_17H}_itens_expansao.png",
                                                     "hold A 2", "wait 120", magmoor_bit(expansion),
                                                     f"expect {MAX_POWER_BOMBS} 000A", f"expect {mouth:06X} {POWER_BOMB_BLOCK}"]
            + LAY_POWER_BOMB + [f"expect {mouth:06X} 00FF", f"expect {POWER_BOMBS} 0008", "hold RIGHT 60", "wait 30"]
            + UNMORPH + [f"expect 7E0AFA {16 * 16 - 21:04X}"] + M17H_SHORES_UP
            + [f"expect 7E0AFA {6 * 16 - 21:04X}", f"expect {HEALTH} 0063", f"shot {IMG_17H}_itens_plataforma.png"]
            + M17H_RISE + magmoor_arrive(room, "magmoor_shore_tunnel", 12) + [f"shot {IMG_17H}_itens_shore_tunnel.png"])



# specs/17i: region C of the Magmoor (tools/magmoor/layouts.py, items.py; item bits $D8-$D9, Save Station B's red door bit $C1).
# The walks are measured in the emulator (scratchpad s17i/scripts: seg.py the beam search of 17g over MAGMOOR_MOVES strings with
# the enemies alive, hops.py the walk frames before each zigzag jump, trp.py traces of the Space Jump climbs): no lava touched, no
# damage. Shortcuts (counted): to the P16 by the Tallon's elevator (door_teleport to its Magmoor East transport, onto its
# platform, as elevador_magmoor_tallon), into the Geothermal Core, the Workstation and the Workstation Tunnel by door_teleport
# in the items and save tests, the gear by RAM.
IMG_17I = "build/tests/17i"   # the photos of the region C tests (specs/img/17i-* are copies of some)
M17I_TFT = "GgghGXXr"                   # the Twin Fires Tunnel: over its pits, the Space Jump up the cliff onto the R0 shelf
M17I_TWIN_FIRES = "rXXXaRXXXXXXRXXXXXXrXD"   # the Twin Fires past its Mellas, the wave door to the North Core Tunnel
M17I_NCT = "xxXxXD"                     # the North Core Tunnel: its pit, the wave door into the Geothermal Core (L2)
M17I_GC_ZIGZAG = [("RIGHT", [(35, 30, -100), (12, 30, -100)]), ("LEFT", [(7, 30, -100), (30, 30, -100)])]   # z1, z2; z3, slab
SPACE_JUMP_LEFT, SPACE_JUMP_RIGHT = ["hold LEFT+A 30", "hold LEFT 16"], ["hold RIGHT+A 30", "hold RIGHT 16"]
M17I_GC_UP = ["hold RIGHT 10"] + SPACE_JUMP_LEFT * 3 + ["wait 60"]   # up the rock's east face onto the L0 shelf (row 10)
M17I_SCT = "yycyyYYYYE"                 # the South Core Tunnel west over its Sovas, the wave door into the Workstation (R1)
# the Workstation from the R1 door: west off the slab down the west zigzag to the floor, the Space Jump up the west wall onto
# the raised platform (the energy tank), then the Space Jump east along the roof onto the R0 shelf
M17I_WS_DOWN = ["hold LEFT 380", "wait 60", "hold LEFT 40", "hold RIGHT 10"]
M17I_WS_TANK = SPACE_JUMP_LEFT * 4 + ["hold RIGHT+A 30", "hold RIGHT 10", "wait 30", "hold RIGHT 20"]   # onto it, into the tank
M17I_WS_EAST = SPACE_JUMP_RIGHT * 15 + ["wait 60"]
M17I_WT = "DcRRxR"                      # the Workstation Tunnel over its Zeelas to the ice door
M17I_SCREENS = [("magmoor_twin_fires_tunnel", 0, 1), ("magmoor_twin_fires_tunnel", 2, 0), ("magmoor_twin_fires", 0, 0),
                ("magmoor_twin_fires", 5, 0), ("magmoor_north_core_tunnel", 0, 0), ("magmoor_north_core_tunnel", 1, 0),
                ("magmoor_geothermal_core", 0, 2), ("magmoor_geothermal_core", 0, 0), ("magmoor_south_core_tunnel", 2, 0),
                ("magmoor_south_core_tunnel", 0, 0), ("magmoor_workstation", 3, 1), ("magmoor_workstation", 0, 2),
                ("magmoor_workstation", 0, 0), ("magmoor_workstation", 3, 0), ("magmoor_workstation_tunnel", 0, 0),
                ("magmoor_workstation_tunnel", 2, 0)]


def magmoor_c_start(room: dict, m: dict, beams: int) -> list[str]:
    """Shortcut: from the landing to the Tallon's Magmoor East transport (door_teleport from the Tunnel B) and down its elevator
    to the Magmoor's P16 (as elevador_magmoor_tallon); the gear of round 3 by RAM (the Varia Suit, the Space Jump, the Morph
    Ball, the Bombs; 10 missiles) and `beams` (the Wave Beam of round 0's Magmoor East: the wave doors; + the Ice Beam, round
    3's, for the round-4 rooms)."""
    eq = VARIA_EQUIPMENT | SPACE_JUMP_EQUIPMENT | MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT
    return (door_teleport(m, "tallon_tunnel_b", TALLON_TO_MAGMOOR) + onto_platform(TALLON_TO_MAGMOOR)
            + ride_elevator(room, TALLON_TO_MAGMOOR, f"{IMG_17I}_descendo.png")
            + poke16(0x7E09A2, eq) + poke16(0x7E09A4, eq) + poke16(0x7E09C6, 10) + poke16(0x7E09C8, 10)
            + poke16(0x7E09CE, 0) + poke16(0x7E09D0, 0) + give_beams(beams))


def magmoor_item(room_key: str) -> int:
    from magmoor import items as magmoor_items
    return next(n for n, it in enumerate(magmoor_items.ITEMS) if it.room == room_key)


def phendrana_item(room_key: str, k: int = 0) -> int:
    """specs/18n: the index (tools/phendrana/items.py) of the k-th item of a Phendrana room."""
    from phendrana import items as phendrana_items
    return [n for n, it in enumerate(phendrana_items.ITEMS) if it.room == room_key][k]


def magmoor_c_to_slab(room: dict, energy: int = 0x63, sh=region_shot, door: str = "DD") -> list[str]:
    """Region C walked from the P16's elevator platform: the Twin Fires Tunnel and its cliff, the Twin Fires, the North Core
    Tunnel, the Geothermal Core's zigzag onto the slab of its L1 chamber: the pieces of magmoor_regiao_c_rota (specs/17i),
    shared with the full chain (specs/17j, with magmoor_c_to_tank). `door`: the moves through the P16's R0 door (from the platform after the ride up
    the first shot leaves the screen, "DD"; walked in from the L0 door the first one opens it, "D": measured)."""
    full = lambda key, feet: magmoor_full(room, key, feet, energy)   # noqa: E731
    out = (moves(door) + full("magmoor_twin_fires_tunnel", 25)
           + [sh(f"{IMG_17I}_rota_twin_fires_tunnel")] + moves(M17I_TFT) + [f"expect 7E0AFA {10 * 16 - 21:04X}"]
           + moves("D") + full("magmoor_twin_fires", 9) + enemies_alive(MAGMOOR, "magmoor_twin_fires")
           + [sh(f"{IMG_17I}_rota_twin_fires")] + moves(M17I_TWIN_FIRES) + full("magmoor_north_core_tunnel", 9)
           + moves(M17I_NCT) + full("magmoor_geothermal_core", 41) + [sh(f"{IMG_17I}_rota_geothermal_core")])
    for direction, mv in M17I_GC_ZIGZAG:
        out += hops(direction, mv)
    return out + [f"expect 7E0AFA {26 * 16 - 21:04X}", f"expect {HEALTH} {energy:04X}"]


def magmoor_c_to_tank(room: dict, energy: int = 0x63, sh=region_shot, door: str = "DD") -> list[str]:
    """magmoor_c_to_slab, then the Space Jump up the Geothermal Core's rock face onto the L0 shelf, the South Core Tunnel, the
    Workstation's west side and its raised platform (the last line walks into the energy tank)."""
    full = lambda key, feet: magmoor_full(room, key, feet, energy)   # noqa: E731
    return (magmoor_c_to_slab(room, energy, sh, door) + M17I_GC_UP
            + [f"expect 7E0AFA {10 * 16 - 21:04X}"]
            + [sh(f"{IMG_17I}_rota_geothermal_l0")] + moves("E") + full("magmoor_south_core_tunnel", 9)
            + enemies_alive(MAGMOOR, "magmoor_south_core_tunnel") + moves(M17I_SCT) + full("magmoor_workstation", 25)
            + [sh(f"{IMG_17I}_rota_workstation")] + M17I_WS_DOWN + M17I_WS_TANK)


def magmoor_route_c(m: dict, room: dict) -> list[str]:
    """specs/17i, magmoor_regiao_c_rota: from the landing down the Tallon's elevator to the Magmoor's P16 (shortcut), the gear
    of round 3 by RAM with the Wave Beam; then WALKING through region C with its enemies alive: the P16's east door, the Twin
    Fires Tunnel (hot: the Varia) over its pits and up its cliff with the Space Jump (Prime's Spider Ball track) onto the R0
    shelf, the Twin Fires past its 3 Mellas, its wave door (the Wave Beam opens it), the North Core Tunnel and its wave door
    into the Geothermal Core's bottom; up its zigzag onto the slab and with the Space Jump up the rock's face onto the L0 shelf
    (Prime's spider tracks), into the South Core Tunnel, west over its Sovas through its wave door into the Workstation; down
    its west side, the Space Jump up the west wall onto the raised platform: the energy tank (bit $D9, 199 energy); the Space
    Jump east along the roof onto the R0 shelf, the Workstation Tunnel over its Zeelas to its ice door: the Wave Beam leaves
    it shut (the Ice Beam is round 3's: the Mines West transport is round 4). Each room's energy checked (no heat, no lava,
    no enemy touch, no damage in any door's first frames: spec 15), its explored bits and the pause map ("MAGMOOR")."""
    full = lambda key, feet, energy=0x63: magmoor_arrive(room, key, feet)[:-1] + [f"expect {HEALTH} {energy:04X}"]   # noqa: E731
    shut_x = (MAGMOOR.by_key()["magmoor_workstation_tunnel"].width * 16 - 2) * 16 - 5
    out = (magmoor_c_start(room, m, WAVE_BEAM) + magmoor_c_to_tank(room)
           + ["wait 120", f"shot {IMG_17I}_rota_tanque.png", "wait 300", "hold A 2", "wait 120", magmoor_bit(magmoor_item("magmoor_workstation")),
              f"expect {MAX_ENERGY} 00C7", f"expect {GAME_STATE} 0008", f"expect 7E0AFA {8 * 16 - 21:04X}"]
            + M17I_WS_EAST + [f"expect 7E0AFA {10 * 16 - 21:04X}", f"expect {HEALTH} 00C7"]
            + moves("D") + full("magmoor_workstation_tunnel", 9, 0xC7) + enemies_alive(MAGMOOR, "magmoor_workstation_tunnel")
            + moves(M17I_WT) + ["hold RIGHT 60", "wait 20", f"expect {SAMUS_X} {shut_x:04X}"]
            + ["hold RIGHT+X 2", "wait 30"] * 3 + ["hold RIGHT 60", "wait 60", f"expect {SAMUS_X} {shut_x:04X}",
                                                 f"expect {ROOM_PTR} {room['magmoor_workstation_tunnel']}", f"expect {HEALTH} 00C7",
                                                 f"shot {IMG_17I}_rota_porta_de_gelo.png"]
            + [explored_at(*sc) for sc in M17I_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(MAGMOOR, M17I_SCREENS, "magmoor_c") + [f"shot {IMG_17I}_rota_mapa.png", "hold START 10", "wait 200",
                                                                  f"expect {GAME_STATE} 0008"])
    return out


# magmoor_regiao_c_itens: round 4's gear (+ the Ice Beam). The Geothermal Core's zigzag on foot (from the door_teleport's
# arrival), the puzzle's bomb block, the chamber's ice door; the Plasma Processing west to the missile; the Workstation Tunnel's
# ice door and the Mines West transport (decorative until specs/19e; now its elevator down to the Mines' P25)
M17I_GC_ZIGZAG_TP = [("RIGHT", [(47, 30, -100), (13, 30, -100)]), ("LEFT", [(8, 30, -100), (31, 30, -100)])]
M17I_PP = "yyYYYyYl"                    # the Plasma Processing west over its pit to the missile
M17I_WT_TP = "RDcccDD"                  # the Workstation Tunnel (from the door_teleport) over its Zeelas through the ice door


def magmoor_items_c(m: dict, room: dict) -> list[str]:
    """specs/17i, magmoor_regiao_c_itens: down to the P16 (shortcut), round 4's gear by RAM (round 3's + the Ice Beam), into the
    Geothermal Core by door_teleport from the North Core Tunnel (the walk there is magmoor_regiao_c_rota's); WALKING up its
    zigzag on foot (no Space Jump used) onto the slab; against the puzzle's wall the bomb block (7, 25) stays after a Wave Beam
    shot, a bomb breaks it; the ball through the tunnel into the chamber; standing, the Wave Beam leaves the ice door shut, the
    Ice Beam opens it: the Plasma Processing (Prime's plasma door is an ice door here, SM_BEAM), west over its pit into the
    Missile Expansion where Prime has the Plasma Beam (bit $D8, 15 missiles). Then by door_teleport into the Workstation Tunnel:
    over its Zeelas, the ice door opened, the transport to the Mines West (decorative until specs/19e: its shaft's floor was no
    elevator; since 19e walked onto its platform DOWN rides to the Mines' P25, area 5). Energy 99 the whole way."""
    block = level_block("magmoor_geothermal_core", *__import__("magmoor.layouts", fromlist=["GC_BOMB"]).GC_BOMB)
    out = (magmoor_c_start(room, m, WAVE_BEAM | ICE_BEAM) + door_teleport(m, "magmoor_north_core_tunnel", "magmoor_geothermal_core")
           + magmoor_arrive(room, "magmoor_geothermal_core", 41))
    for direction, mv in M17I_GC_ZIGZAG_TP:
        out += hops(direction, mv)
    out += ([f"expect 7E0AFA {26 * 16 - 21:04X}"] + give_beams(WAVE_BEAM) + ["hold LEFT 40", "wait 10", "hold X 2", "wait 40",
                                                                            f"expect {block:06X} F058",
                                                                            f"shot {IMG_17I}_itens_quebra_cabeca.png"]
            + MORPH + [f"expect {POSE} {BALL_POSE_LEFT}", "hold X 2", "wait 90", f"expect {block:06X} 00FF", "hold LEFT 100",
                       "wait 30"] + UNMORPH + [f"expect {POSE} 0002", f"expect {SAMUS_X} 0025"]
            + ["hold LEFT+X 2", "wait 30", "hold LEFT+X 2", "wait 30", "hold LEFT 60", "wait 20", f"expect {SAMUS_X} 0025",
               f"shot {IMG_17I}_itens_porta_de_gelo.png"]
            + give_beams(WAVE_BEAM | ICE_BEAM) + ["hold LEFT+X 2", "wait 120", "hold LEFT 90", "wait 200"]
            + magmoor_arrive(room, "magmoor_plasma_processing", 9) + [f"shot {IMG_17I}_itens_plasma_processing.png"]
            + moves(M17I_PP) + ["hold LEFT 30", "wait 120", f"shot {IMG_17I}_itens_missil.png", "wait 300", "hold A 2", "wait 120",
                                magmoor_bit(magmoor_item("magmoor_plasma_processing")), f"expect {MAX_MISSILES} 000F",
                                f"expect {HEALTH} 0063"]
            + door_teleport(m, "magmoor_workstation", "magmoor_workstation_tunnel")
            + magmoor_arrive(room, "magmoor_workstation_tunnel", 9) + enemies_alive(MAGMOOR, "magmoor_workstation_tunnel")
            + moves(M17I_WT_TP) + magmoor_arrive(room, "magmoor_transport_mines_west", 25)
            # specs/19e: the transport is real now (was: decorative, DOWN did nothing): walked onto its platform, DOWN rides to
            # the Mines' P25 (area 5)
            + ["hold RIGHT 30", "wait 20", f"expect {ELEVATOR_FLAGS} 0001", "hold DOWN 1", "wait 30",
               f"expect {ELEVATOR_STATUS} 0001", f"shot {IMG_17I}_itens_mines_west.png", f"wait {ELEVATOR_RIDE - 30}",
               f"expect {ROOM_PTR} {room['mines_transport_magmoor_south']}", f"expect {AREA} 0005",
               f"expect {ELEVATOR_STATUS} 0000", f"expect {GAME_STATE} 0008", f"shot {IMG_17I}_itens_mines_p25.png"])
    return out


# magmoor_save_station_b: from the Workstation's R1 (door_teleport) down to its L2 door, the Transport Tunnel C, the transport
# to Phendrana South and its zigzag on foot to the R0 shelf, the red door of Save Station B
M17I_WS_TO_TTC = ["hold LEFT 380", "wait 60", "hold RIGHT 20", "wait 60"]
M17I_PS_ZIGZAG = [("LEFT", [(34, 30, -100), (13, 30, -100)]), ("RIGHT", [(7, 30, -100), (27, 30, -100)])]


def magmoor_save_b(m: dict, room: dict) -> list[str]:
    """specs/17i, magmoor_save_station_b: down to the P16 (shortcut), round 3's gear by RAM, into the Workstation by door_teleport
    from the South Core Tunnel; WALKING: down to its L2 door (wave), the Transport Tunnel C and its wave door, the transport to
    Phendrana South (decorative) up its zigzag ON FOOT to the R0 shelf, its red door opened with missiles (bit $C1), Save
    Station B (P28). Samus on the pedestal, a marker in the saved data (game hours 5), YES, "save completed": load station 2
    of area 2, its used-station bit ($7ED8FC bit 2); paused, the Magmoor's map. Game over: the area-select screen picks area 2,
    station 2, "MAGMOOR / CAVERNS"; continue: back on Save Station B's pedestal, area 2, the marker loaded."""
    st = MAGMOOR.load_stations[2]
    out = (magmoor_c_start(room, m, WAVE_BEAM) + door_teleport(m, "magmoor_south_core_tunnel", "magmoor_workstation")
           + magmoor_arrive(room, "magmoor_workstation", 25) + M17I_WS_TO_TTC + moves("E")
           + [f"expect {ROOM_PTR} {room['magmoor_workstation']}"] + moves("E")   # from far the first shot leaves the screen
           + magmoor_arrive(room, "magmoor_transport_tunnel_c", 9) + moves("E")
           + magmoor_arrive(room, "magmoor_transport_phendrana_south", 25) + [f"shot {IMG_17I}_save_phendrana_south.png"])
    for direction, mv in M17I_PS_ZIGZAG:
        out += hops(direction, mv)
    out += ([f"expect 7E0AFA {10 * 16 - 21:04X}", f"expect {HEALTH} 0063", "hold RIGHT 60", "wait 20"]
            + red_door(room, "magmoor_transport_phendrana_south", "RIGHT", "magmoor_save_station_b", True)   # 5 missiles: 6 shots
            + [f"shot {IMG_17I}_save_sala.png"] + poke16(0x7E09E0, 5))
    for addr, v in ((0x7E0AF6, st.x), (0x7E0B10, st.x), (0x7E0AFA, st.y), (0x7E0B14, st.y)):
        out += poke16(addr, v)
    return (out + ["hold RIGHT 1", "wait 180", f"shot {IMG_17I}_save_pergunta.png", "hold A 2", "wait 300", "hold A 2",
                   "wait 200", f"expect {LOAD_STATION} 0002", f"expect {AREA} 0002", f"expectbit {USED_STATIONS_AREA2} 04",
                   f"expect {GAME_STATE} 0008", f"shot {IMG_17I}_save_salvo.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}", f"shot {IMG_17I}_save_mapa.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} 0008",
                   "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
                   "hold A 2", "wait 300"]
            + area_select_shows_after(MAGMOOR.number, st.index, (TALLON.number,), f"{IMG_17I}_save_tela_de_area.png")
            + ["hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0002", f"expect {ROOM_PTR} {room[st.room]}",
               f"expect {LOAD_STATION} 0002", f"expect {GAME_HOURS} 0005", f"expect 7E0AF6 {st.x:04X}",
               f"shot {IMG_17I}_save_continue.png", explored_at("magmoor_save_station_b", 0, 0),
               explored_at("magmoor_transport_phendrana_south", 1, 0)])

# specs/12f: region A of the Chozo Ruins (tools/chozo/layouts.py, items.py). The Chozo's item bits ($B4-$BA) share the
# 16 bits at $7ED886 with the Tallon's $B0-$B3 (Plasma, Morph Ball, Bombs, Power Bomb).
CHOZO_BITS_WORD = 0x7ED886


def chozo_item(n: int):
    from chozo import items as chozo_items
    return chozo_items.ITEMS[n]


def chozo_bits_word(chozo: tuple[int, ...] = (), tallon: tuple[int, ...] = ()) -> str:
    """`expect` of the 16 bits at CHOZO_BITS_WORD holding exactly the bits of the Chozo items `chozo` and the Tallon items
    `tallon` (tools/chozo/items.py, tools/tallon/items.py indexes) picked up so far."""
    from chozo import items as chozo_items
    from tallon import items as tallon_items
    bits = [chozo_items.BITS[n] for n in chozo] + [tallon_items.BITS[n] for n in tallon]
    word = sum(1 << (b - 8 * (CHOZO_BITS_WORD - 0x7ED870)) for b in bits if 0 <= b - 8 * (CHOZO_BITS_WORD - 0x7ED870) < 16)
    return f"expect {CHOZO_BITS_WORD:06X} {word:04X}"


def chozo_near(n: int, start: int) -> list[str]:
    """Samus put by RAM `start` blocks from Chozo item n, on its floor (negative = west), placed twice (stops a run), the
    camera on the item's screen (the camera does not follow a RAM placement; pause/unpause redraws it). After this a door
    teleport up through a ceiling door hung in the transition (BG1's offsets off a whole screen, as specs/10a found):
    chozo_regiao_a_itens does its door teleports before (or a real door transition after)."""
    it = chozo_item(n)
    r = built_room(it.room)
    x, y = (it.spot[0] + start) * 16 + 8, (it.spot[1] + 1) * 16 - 21
    place = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y)):
        place += poke16(addr, v)
    cam = poke16(0x7E0911, x // 256 * 256) + poke16(0x7E0915, min(it.spot[1] // 16 * 256, camera_bottom(r)))
    return place + ["wait 30"] + place + cam + ["wait 4", "hold START 10", "wait 200", "hold START 10", "wait 200"]


def chozo_pick_up(n: int, shot: str, start: int = -2, frames: int = 40) -> list[str]:
    """Walk into Chozo item n from `start` blocks (she must move to take it), close its message box with A (~240 frames
    after it opens), its bit set."""
    toward = "RIGHT" if start < 0 else "LEFT"
    bit = __import__("chozo.items", fromlist=["BITS"]).BITS[n]
    return (chozo_near(n, start) + [f"hold {toward} {frames}", "wait 120", f"shot {shot}", "wait 300", "hold A 2", "wait 120",
                                    f"expectbit {0x7ED870 + bit // 8:06X} {1 << (bit % 8):02X}", f"expect {GAME_STATE} 0008"])


IMG_12F = "build/tests/12f"   # the photos of the region A tests (specs/img/12f-* are copies of some)
# the screens chozo_regiao_a_rota walks through, one or two per room (the tower: its top east, where she comes in, and its
# bottom west, where she leaves)
CHOZO_A_SCREENS = [("chozo_ruins_entrance", 0, 0), ("chozo_ruins_entrance", 1, 0), ("chozo_main_plaza", 0, 0),
                   ("chozo_main_plaza", 1, 1), ("chozo_ruined_shrine_access", 0, 0), ("chozo_ruined_shrine", 1, 0),
                   ("chozo_tower_of_light_access", 0, 0), ("chozo_tower_of_light", 2, 0), ("chozo_tower_of_light", 0, 3),
                   ("chozo_tower_chamber", 0, 0)]
# the walks of chozo_regiao_a_rota, measured in the emulator (scratchpad s12f): blue doors opened by the walker's shots
CHOZO_NORTH_TO_ENTRANCE = ["hold RIGHT+X 2", "hold RIGHT 60", "hold RIGHT+X 2", "hold RIGHT 100", "wait 200"]
CHOZO_ENTRANCE_TO_FLOOR = 42    # walk() cycles (a jump every 2): over the broken floor, off the balcony, down the stair
CHOZO_FLOOR_TO_RED_DOOR = 18    # back west: into the pit and out, over the dais, onto the door's ledge
CHOZO_ACCESS_TO_SHRINE = 40     # the Ruined Shrine Access, its blue door, the shrine's terrace (then into the missile)
CHOZO_SHRINE_TO_TOWER = 20      # up the west terrace, the wave door, the Tower of Light Access's floor
CHOZO_ACCESS_TO_TOWER = 30      # the access, its wave door, onto the tower's top ledge
CHOZO_TOWER_DOWN = 20           # off the ledge, down the platforms to the floor, the L3 wave door, the Tower Chamber
# specs/12h: from the shrine's east terrace into the bowl's floor missile through the Sidehoppers (Prime's Beetles): shooting
# and stepping west, the energy refilled each step (as chozo_walk); measured: she takes the missile, 2 of the 3 die (specs/14a:
# with the Plated Beetle there, 1 of the 3, and the beetle takes 2 shots and stays)
SHRINE_FIGHT = [f"poke {HEALTH} 63", "hold LEFT+X 2", "hold LEFT 6"] * 20


def chozo_walk(direction: str, cycles: int, to: str, room: dict) -> list[str]:
    """walk(direction, cycles, 2), the energy refilled at the start of each cycle (specs/12h, as tallon_walk since 07i: the
    walk tests the way through the rooms, not the fights; the enemies stay, knock-back and all)."""
    out = []
    for i in range(cycles):
        out += [f"poke {HEALTH} 63", f"hold {direction}+X 2", f"hold {direction} 10"] + ([f"hold {direction}+A 20"] if i % 2 == 0 else [])
    return out + ["wait 200", f"expect {ROOM_PTR} {room[to]}", f"expect {GAME_STATE} 0008", f"poke {HEALTH} 63"]


def chozo_walk_paused(direction: str, cycles: int, split: int, pause: int, to: str, room: dict) -> list[str]:
    """specs/17e: chozo_walk with a pause of `pause` frames after its cycle `split` (the jumps keep their beat)."""
    walk = chozo_walk(direction, cycles, to, room)
    per = lambda i: 3 + (i % 2 == 0)   # noqa: E731 (lines of cycle i)
    at = sum(per(i) for i in range(split))
    return walk[:at] + [f"wait {pause}"] + walk[at:]


def out_of_arena(walk: list[str]) -> list[str]:
    """specs/14b: a chozo_walk out of an arena still alive (its mini-boss song set, $2A) into a room of the area's music: the
    door's transition uploads the area's song set ($1B) and takes ~45 frames more (measured: ~216 frames to game state 8,
    ~170 between two rooms of the area's song; scratchpad s14b/scripts/trans.py): its 200-frame wait gets 150 more. specs/14c:
    the same into an arena alive (the Sunchamber: the area's set out, $2A in)."""
    return walk[:-3] + ["wait 150"] + walk[-3:]


def chozo_route(m: dict, room: dict) -> list[str]:
    """specs/12f, chozo_regiao_a_rota: from the landing (a real game), the Landing Site's missile picked up walking
    (tallon_first_missile: 5 missiles), to the Chozo West (door_teleport through the round-0 rooms) and down the North
    elevator (onto_platform: shortcut, as elevador_chozo_ida_e_volta); then WALKING through region A to its farthest room
    (specs/12h: with the enemies alive, the energy refilled each walk cycle, chozo_walk):
    the North transport's door, the Ruins Entrance's broken floor, the Main Plaza's balcony and stair down to the floor,
    back west to the Ruined Shrine Access's red door (missiles: 5 hits, its bit $B3, 0 missiles left), through the access
    into the Ruined Shrine, into its floor missile (Prime's Morph Ball spot: bit $B8, 5/10 missiles; A closes the box;
    specs/12h: through the Sidehoppers, shooting and stepping west, SHRINE_FIGHT, two of them shot dead; specs/14a: one, the
    Plated Beetle passed alive),
    the Wave Beam by RAM (shortcut: the Tallon's Magmoor East item, round 1), up the terrace through the wave door, the
    Tower of Light Access and its wave door, down the Tower of Light's platforms, through its bottom wave door into the
    Tower Chamber. Each room's explored bit is set; the pause map is the Chozo's."""
    shrine_missile = 4
    bit = __import__("chozo.items", fromlist=["BITS"]).BITS[shrine_missile]
    red = next(d for d in built_room("chozo_main_plaza").doors if d.lock == "missile").lock_bit
    return (tallon_first_missile("tallon_chozo_rota")
            + chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
            + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12F}_rota_descendo.png")
            + [f"shot {IMG_12F}_rota_chegada.png"] + CHOZO_NORTH_TO_ENTRANCE
            + [f"expect {ROOM_PTR} {room['chozo_ruins_entrance']}", f"shot {IMG_12F}_rota_entrance.png"]
            + chozo_walk("RIGHT", CHOZO_ENTRANCE_TO_FLOOR, "chozo_main_plaza", room)
            + [f"expect 7E0AFA {PLAZA_FEET:04X}", f"shot {IMG_12F}_rota_praca.png"]
            + chozo_walk("LEFT", CHOZO_FLOOR_TO_RED_DOOR, "chozo_main_plaza", room)
            + [f"expect {MISSILES} 0005", "wait 60", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001"]
            + ["hold LEFT+X 2", "wait 30"] * 6
            + ["wait 60", f"expectbit {0x7ED8B0 + red // 8:06X} {1 << (red % 8):02X}", f"expect {MISSILES} 0000",
               f"shot {IMG_12F}_rota_porta_vermelha.png", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0000",
               "hold LEFT 90", "wait 200", f"expect {ROOM_PTR} {room['chozo_ruined_shrine_access']}"]
            + chozo_walk("LEFT", CHOZO_ACCESS_TO_SHRINE, "chozo_ruined_shrine", room)
            + [chozo_bits_word()] + SHRINE_FIGHT
            # 12h: two Sidehoppers shot dead; specs/14a: with the Plated Beetle in the bowl (slot 3) one of them (slot 1),
            # the beetle hit twice and left alive (the route walks past it, energy refilled; its fight: chozo_plated_beetle);
            # spec 15: the small ones moved to the bowl's middle screen (off the camera of both doors) wait there until she
            # comes: none dies in this walk, all 4 alive (measured; she walks past them, energy refilled)
            + [f"expect {ENEMY_TABLE + ENEMY_SLOT * n:06X} {sp:04X}" for n, sp in enumerate(slots(CHOZO.enemies["chozo_ruined_shrine"]))]
            + ["wait 120", f"shot {IMG_12F}_rota_missil_mensagem.png", "wait 180",
               "hold A 2", "wait 120", f"expectbit {0x7ED870 + bit // 8:06X} {1 << (bit % 8):02X}", chozo_bits_word((shrine_missile,)),
               f"expect {MISSILES} 0005", f"expect {MAX_MISSILES} 000A", f"expect {GAME_STATE} 0008",
               f"shot {IMG_12F}_rota_shrine.png"]
            + give_beams(WAVE_BEAM)
            + out_of_arena(chozo_walk("LEFT", CHOZO_SHRINE_TO_TOWER, "chozo_tower_of_light_access", room))
            + chozo_walk("LEFT", CHOZO_ACCESS_TO_TOWER, "chozo_tower_of_light", room) + [f"shot {IMG_12F}_rota_torre.png"]
            + chozo_walk("LEFT", CHOZO_TOWER_DOWN, "chozo_tower_chamber", room) + [f"shot {IMG_12F}_rota_tower_chamber.png"]
            + [explored_at(*screen) for screen in CHOZO_A_SCREENS] + [explored_at(NORTH, *platform_screen(NORTH))]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(CHOZO, CHOZO_A_SCREENS, "chozo_a") + [f"shot {IMG_12F}_rota_mapa.png", "hold START 10", "wait 200"])


# specs/12i: region B. A climb up a ceiling door into a 1-screen room's floor door (the 10b technique, as climb_ceiling_door):
# Samus put by RAM on the platform under the door, `dx` px from its left column, facing `steer`; a full jump, `steer`
# held as she rises out of the hole above: she lands on the far side's floor (the near side, or no steering, falls back
# down the door, as specs/10b measured: not a softlock).
def chozo_climb(room: dict, key: str, to: str, dx: int, steer: str) -> list[str]:
    r = built_room(key)
    d = next(d for d in r.doors if d.to_room == to)
    x, y = (d.screen * 16 + 6) * 16 + dx, 6 * 16 - 21
    place = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y), (0x7E0911, d.screen * 256), (0x7E0915, 0)):
        place += poke16(addr, v)
    return place + ["wait 30"] + place + ["wait 30"] + climb_jump(steer) + [f"expect {ROOM_PTR} {room[to]}",
                                                                          f"expect {GAME_STATE} 0008"]


def rise_through(m: dict, room: dict, key: str, to: str, col: int, steer: str) -> list[str]:
    """Shortcut: Samus put by RAM under key's ceiling door to `to` (column `col` of its 4, at the platform's height), the
    door transition up started by RAM (as door_teleport), `steer` held: she rises out of the floor door above and lands on
    that side (the Nursery Access from the Main Plaza: column 3, east; a real jump there was knocked back down by the
    crawler, as specs/12h saw)."""
    r = built_room(key)
    i = next(i for i, d in enumerate(r.doors) if d.to_room == to)
    d = r.doors[i]
    x, y = (d.screen * 16 + 6 + col) * 16 + 8, 4 * 16
    place = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y)):
        place += poke16(addr, v)
    return (place + ["wait 30"] + place + poke16(0x7E0911, d.screen * 256) + poke16(0x7E0915, 0) + ["wait 2"]
            + poke16(0x7E099C, DOOR_HIT_TRANSITION) + poke16(0x7E078D, m[key]["doors"][i] & 0xFFFF) + poke16(0x7E0998, 9)
            + [f"hold {steer} 400", "wait 60", f"expect {ROOM_PTR} {room[to]}", f"expect {GAME_STATE} 0008"])


def climb_jump(steer: str) -> list[str]:
    """The jump of chozo_climb from where Samus stands under the ceiling door (measured, scratchpad s12i)."""
    return [f"poke {HEALTH} 63", f"hold {steer} 2", "wait 20", "hold A 4", f"hold A+{steer} 30", f"hold {steer} 180", "wait 60"]


IMG_12I = "build/tests/12i"   # the photos of the region B tests (specs/img/12i-* are copies of some)
# the walks of chozo_regiao_b_rota, measured in the emulator (scratchpad s12i): (direction, cycles of chozo_walk) or a
# list of inputs; the blue doors opened by the walker's shots
B_ACCESS_TO_EYON = ["hold LEFT 36", "hold LEFT+A 30", "hold LEFT 60", "wait 60", "hold LEFT+X 2", "hold LEFT 80", "wait 200"]
B_EYON_TO_PLATFORM = ["hold LEFT 92", "wait 20", "hold A+LEFT 30", "hold LEFT 10", "wait 30"]   # onto the T0 platform
B_PLATFORM_TO_DOOR = ["hold LEFT 16", "wait 20"]   # under the door's west half: the climb lands west (B1's west floor)
B_NURSERY_TO_ATRIUM = 22
B_ATRIUM_WALK = 8                   # to the floor east of the T0 platform
B_ATRIUM_TO_PLATFORM = ["wait 50", "hold A+LEFT 30", "hold LEFT 10", "wait 30"]
B_GALLERY_OVER_THE_HOLE = ["hold RIGHT 28", "hold RIGHT+A 30", "hold RIGHT 60", "wait 30", "hold RIGHT+X 2", "hold RIGHT 80",
                           "wait 200"]
B_TOTEM_ACCESS = 20
B_TO_THE_TOTEM = 10                 # into the west pool, against the totem
B_TOTEM_CLIMB = ["poke 7E09C2 63", "hold A+RIGHT 40", "hold RIGHT 20"]   # a full jump: 6 blocks up from the pool
B_TOTEM_TO_RED_DOOR = 16
B_TAN = 26
B_DOWN_THE_WELL = ["hold RIGHT 30", "wait 60", "hold LEFT 40", "wait 60"]
B_WELL_TO_VAULT = 16                # Vault Access' R0 step, down its floor door onto the Vault's T0 platform
# specs/17e: the P24 got its elevator (the platform enemy $D73F, two more door-list entries): the walk's way out of it into the
# Vault Access changed by a few frames and the walker jumped over the Vault Access' floor door (stuck past it, measured). A pause
# of B_WELL_PAUSE frames after cycle B_WELL_SPLIT (the door is crossed in cycle 13) puts the walk back on the beat that drops
# into it: measured, waits of 12-20 after cycle 13 or 14 work on the new ROM, and every wait 0-20 after 13-15 on the old one
B_WELL_SPLIT, B_WELL_PAUSE = 13, 16
B_VAULT_TO_PLAZA_ACCESS = ["hold LEFT 80", "wait 20", "hold LEFT+X 2", "wait 30", "hold LEFT 60", "wait 200"]
B_PLAZA_ACCESS_DOWN = 12            # down its floor door onto the Main Plaza's one-way ledge
CHOZO_B_SCREENS = [("chozo_nursery_access", 0, 0), ("chozo_eyon_tunnel", 0, 0), ("chozo_eyon_tunnel", 1, 0),
                   ("chozo_ruined_nursery", 0, 0), ("chozo_ruined_nursery", 1, 0), ("chozo_north_atrium", 0, 0),
                   ("chozo_north_atrium", 1, 0), ("chozo_ruined_gallery", 1, 0), ("chozo_totem_access", 0, 0),
                   ("chozo_totem_access", 1, 0), ("chozo_hive_totem", 0, 0), ("chozo_hive_totem", 2, 0),
                   ("chozo_transport_access_north", 0, 0), ("chozo_transport_access_north", 2, 0),
                   ("chozo_transport_magmoor_north", 0, 0), ("chozo_transport_magmoor_north", 0, 1),
                   ("chozo_vault_access", 3, 0), ("chozo_vault", 0, 0), ("chozo_plaza_access", 1, 0),
                   ("chozo_plaza_access", 0, 0)]


def chozo_item_bit(n: int) -> str:
    """`expectbit` of Chozo item n's bit (tools/chozo/items.py)."""
    bit = __import__("chozo.items", fromlist=["BITS"]).BITS[n]
    return f"expectbit {0x7ED870 + bit // 8:06X} {1 << (bit % 8):02X}"


def chozo_item_index(room_key: str, kind: int | None = None) -> int:
    from chozo import items as chozo_items
    return next(n for n, it in enumerate(chozo_items.ITEMS) if it.room == room_key and (kind is None or it.kind == kind))


KILLS = "7E0E50"   # the room's kill count (EnemyDeathAnimation $A0:A3AF adds one; the population's quota is $0E52)


def arena_won_by_ram(key: str) -> list[str]:
    """specs/14b, a shortcut (epic 14 decision 9: the walks and the chain win a boss fight by a noted RAM shortcut; the real
    fight is the boss' own test, chozo_hive_mecha), as Samus comes into the arena: its enemies deleted (clear_room_enemies)
    and the room's kill count set to its population's quota ($0E52, the count of its enemies that can die): the arena
    routine ($84, tools/chozo/bosses.py) sets the boss bit, stops the music and spawns the prize. (Deleting the hives only
    and keeping the wasps left the walks on through the room to how the wasps met her: once they knocked her off the
    totem's climb, once into the gallery's floor door.)"""
    quota = sum(not e.species.harmless for e in CHOZO.enemies[key])
    return ([f"expect {ROOM_PTR} {built_room_ptr(key)}"] + clear_room_enemies(key)
            + [f"poke {KILLS} {quota:02X}", "wait 10"])


def built_room_ptr(key: str) -> str:
    return f"{json.loads((ROOT / 'build/manifest.json').read_text())[key]['header'] & 0xFFFF:04X}"


def chozo_route_b(m: dict, room: dict) -> list[str]:
    """specs/12i, chozo_regiao_b_rota: from the landing (a real game), the Landing Site's missile picked up walking
    (tallon_first_missile: 5 missiles), to the Chozo West (door_teleport through the round-0 rooms) and down the North
    elevator (onto_platform), the Ruins Entrance and the Main Plaza by door_teleport (region A's walk is
    chozo_regiao_a_rota's); up the plaza's T0 into the Nursery Access (rise_through: the transition by RAM, steered east);
    then WALKING round region B's loop with its enemies alive (chozo_walk refills the energy each cycle): over the
    Nursery Access' floor door to its L0, the Eyon Tunnel onto its T0 platform and up into the Ruined Nursery (a real
    climb, steered west), over the dais to the North Atrium, onto its T0 platform and up into the Ruined Gallery, over its
    floor door to the Totem Access, the Hive Totem: up the totem (a full jump from the pool) into its missile (Prime's
    Missile Launcher: bit $C2, 10 missiles), the red door to the Transport Access North opened with missiles (its bit
    $B5), the Transport Access North, down the Magmoor transport's well, the Vault Access' R0 and down its floor door into
    the Vault, its L0 to the Plaza Access and down its floor door onto the Main Plaza's one-way ledge: the "Locked Door"
    E-tank (as in Prime, from the Vault; bit $B7, 199). Each room's explored bit is set; the pause map shows them."""
    totem = chozo_item_index("chozo_hive_totem")
    etank = chozo_item_index("chozo_main_plaza", 0xEED7)   # Prime's "Locked Door" Energy Tank
    red = next(d for d in built_room("chozo_hive_totem").doors if d.lock == "missile").lock_bit
    return (tallon_first_missile("tallon_chozo_b")
            + chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
            + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12I}_rota_descendo.png")
            + chain_teleports(m, room, [NORTH, "chozo_ruins_entrance", "chozo_main_plaza"])
            + rise_through(m, room, "chozo_main_plaza", "chozo_nursery_access", 3, "RIGHT")
            + [f"shot {IMG_12I}_rota_nursery_access.png"] + B_ACCESS_TO_EYON
            + [f"expect {ROOM_PTR} {room['chozo_eyon_tunnel']}", f"poke {HEALTH} 63", f"shot {IMG_12I}_rota_eyon.png"]
            + B_EYON_TO_PLATFORM + [f"expect 7E0AFA {6 * 16 - 21:04X}"] + B_PLATFORM_TO_DOOR + climb_jump("LEFT")
            + [f"expect {ROOM_PTR} {room['chozo_ruined_nursery']}", f"expect 7E0AFA {13 * 16 - 21:04X}",
               f"shot {IMG_12I}_rota_nursery.png"]
            + chozo_walk("LEFT", B_NURSERY_TO_ATRIUM, "chozo_north_atrium", room)
            + chozo_walk("LEFT", B_ATRIUM_WALK, "chozo_north_atrium", room)[:-3] + B_ATRIUM_TO_PLATFORM
            + [f"expect 7E0AFA {6 * 16 - 21:04X}"] + B_PLATFORM_TO_DOOR + climb_jump("LEFT")
            + [f"expect {ROOM_PTR} {room['chozo_ruined_gallery']}", f"expect 7E0AFA {13 * 16 - 21:04X}",
               f"shot {IMG_12I}_rota_gallery.png"]
            + B_GALLERY_OVER_THE_HOLE + [f"expect {ROOM_PTR} {room['chozo_totem_access']}"]
            + chozo_walk("RIGHT", B_TOTEM_ACCESS, "chozo_hive_totem", room)
            + arena_won_by_ram("chozo_hive_totem")   # specs/14b: the Hive Mecha won by RAM as she comes in (a shortcut)
            + chozo_walk("RIGHT", B_TO_THE_TOTEM, "chozo_hive_totem", room)[:-3] + ["wait 30"] + B_TOTEM_CLIMB
            + ["wait 120", f"shot {IMG_12I}_rota_totem_mensagem.png", "wait 180", "hold A 2", "wait 120",
               chozo_item_bit(totem), f"expect {MISSILES} 000A", f"expect {MAX_MISSILES} 000A", f"expect {GAME_STATE} 0008"]
            + chozo_walk("RIGHT", B_TOTEM_TO_RED_DOOR, "chozo_hive_totem", room)[:-3]
            + ["wait 30", f"shot {IMG_12I}_rota_porta_vermelha.png", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001"]
            + [f"poke {HEALTH} 63", "hold RIGHT+X 2", "wait 30"] * 6   # the wasps dart at her meanwhile: energy refilled
            + ["wait 60", f"expectbit {0x7ED8B0 + red // 8:06X} {1 << (red % 8):02X}",
               "poke 7E09D2 00", "wait 10", "hold RIGHT 90", "wait 200",   # back to the beam (HUD selection), as select_beam
               f"expect {ROOM_PTR} {room['chozo_transport_access_north']}"]
            + chozo_walk("RIGHT", B_TAN, "chozo_transport_magmoor_north", room) + [f"shot {IMG_12I}_rota_magmoor.png"]
            + B_DOWN_THE_WELL + [f"expect 7E0AFA {26 * 16 - 21:04X}"]
            + chozo_walk_paused("LEFT", B_WELL_TO_VAULT, B_WELL_SPLIT, B_WELL_PAUSE, "chozo_vault", room)
            + [f"expect 7E0AFA {6 * 16 - 21:04X}",
                                                                          f"shot {IMG_12I}_rota_vault.png"]
            + B_VAULT_TO_PLAZA_ACCESS + [f"expect {ROOM_PTR} {room['chozo_plaza_access']}"]
            + chozo_walk("LEFT", B_PLAZA_ACCESS_DOWN, "chozo_main_plaza", room) + [f"expect 7E0AFA {6 * 16 - 21:04X}"]
            # the box takes the A only ~420 frames after the walk (at 300 it stayed open and the START closed it, measured)
            + ["hold LEFT 30", "wait 120", f"shot {IMG_12I}_rota_etank_mensagem.png", "wait 300", "hold A 2", "wait 120",
               chozo_item_bit(etank), f"expect {HEALTH} 00C7", "expect 7E09C4 00C7", f"expect {GAME_STATE} 0008"]
            + [explored_at(*screen) for screen in CHOZO_B_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(CHOZO, CHOZO_B_SCREENS, "chozo_b") + [f"shot {IMG_12I}_rota_mapa.png", "hold START 10", "wait 200"])


def b_take_and_close(n: int, shot: str, toward: str, frames: int = 60) -> list[str]:
    """Roll (or walk) `toward` into Chozo item n, close its box with A ~420 frames later (as chozo_regiao_b_rota measured),
    its bit on."""
    return [f"hold {toward} {frames}", "wait 120", f"shot {shot}", "wait 300", "hold A 2", "wait 120", chozo_item_bit(n),
            f"expect {GAME_STATE} 0008"]


def b_bomb_tunnel(n: int, start: int, toward: str, block: tuple[int, int], tag: str, back_frames: int = 80,
                  img: str = IMG_12I) -> list[str]:
    """Chozo item n at the end of a 1-row tunnel shut by a bomb block (`block`): Samus put by RAM `start` blocks from the
    item on the floor before the tunnel (chozo_near), standing she walks `toward` and stops against the block (the
    Power Beam does not break it: a shot first), ball, a bomb: the block is air in the level in WRAM; she rolls in to the
    item; back out and stands."""
    it = chozo_item(n)
    at = level_block(it.room, *block)
    back = "LEFT" if toward == "RIGHT" else "RIGHT"
    return (chozo_near(n, start) + [f"hold {toward} 40", "wait 30", f"hold {toward}+X 2", "wait 40",
                                    f"expect {at:06X} {0xF000 | 0x058:04X}", f"shot {img}_itens_{tag}_bloco.png",
                                    "hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_POSE if toward == 'RIGHT' else BALL_LEFT_POSE}",
                                    "hold X 2", "wait 100", f"expect {at:06X} 00FF"]
            + b_take_and_close(n, f"{img}_itens_{tag}_mensagem.png", toward)
            + [f"hold {back} {back_frames}", "wait 30", "hold UP 2", "wait 30", "hold UP 2", "wait 30"])


def b_ball_tunnel(n: int, start: int, toward: str, tag: str, img: str = IMG_12I) -> list[str]:
    """Chozo item n at the end of an open 1-row tunnel (Morph Ball): Samus put by RAM `start` blocks from it on the floor
    before the tunnel, ball, she rolls in to the item; back out and stands."""
    back = "LEFT" if toward == "RIGHT" else "RIGHT"
    return (chozo_near(n, start) + [f"shot {img}_itens_{tag}_antes.png", f"hold {toward} 2", "wait 10",
                                    "hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30",
                                    f"expect {POSE} {BALL_POSE if toward == 'RIGHT' else BALL_LEFT_POSE}"]
            + b_take_and_close(n, f"{img}_itens_{tag}_mensagem.png", toward, 120)
            + [f"hold {back} 80", "wait 30", "hold UP 2", "wait 30", "hold UP 2", "wait 30"])


def chozo_items_b_test(m: dict, room: dict) -> list[str]:
    """specs/12i, chozo_regiao_b_itens: the region B items chozo_regiao_b_rota does not take, each picked up by walking or
    rolling into it, A closing its box. From the landing to the Chozo West (door_teleport), down the North elevator
    (onto_platform). Shortcuts, each noted: the Morph Ball and the Bombs by RAM (the Tallon's items of rounds 0 and 1), the
    rooms by door_teleport (from the Main Plaza up the one-way door into the Plaza Access, the Vault, the Vault Access (up
    its floor door: rise_through, steered west), the Magmoor transport, the Transport Access North, the Hive Totem, the Totem Access, the Ruined Gallery, the North
    Atrium, the Ruined Nursery: round the loop the other way, no climb), the rooms' enemies deleted by RAM on arrival
    (clear_room_enemies: the test is of the items), Samus put by RAM near each item (chozo_near). The Vault's missile
    (Prime's cage and its three bomb slots: a bomb block), the Transport Access North's E-tank (Prime's ball hole: the
    pit's tunnel, Morph Ball), the Ruined Gallery's two (the "Tunnel": Morph Ball; the missile wall: a bomb block), the
    Ruined Nursery's (the wall puzzle: a bomb block). At the end the 5 bits, 15 missiles' capacity, 199 energy."""
    vault, nursery, tunnel, wall, etank = (chozo_item_index("chozo_vault"), chozo_item_index("chozo_ruined_nursery"),
                                           *[n for n, it in enumerate(__import__("chozo.items", fromlist=["ITEMS"]).ITEMS)
                                             if it.room == "chozo_ruined_gallery"],
                                           chozo_item_index("chozo_transport_access_north"))
    from chozo import layouts as chozo_layouts
    out = (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
           + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12I}_itens_descendo.png")
           + poke16(0x7E09A2, MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT) + poke16(0x7E09A4, MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT)
           + chain_teleports(m, room, [NORTH, "chozo_ruins_entrance", "chozo_main_plaza", "chozo_plaza_access", "chozo_vault"]))
    out += b_bomb_tunnel(vault, -8, "RIGHT", chozo_layouts.VAULT_BOMB, "vault")
    out += (rise_through(m, room, "chozo_vault", "chozo_vault_access", 0, "LEFT")
            + chain_teleports(m, room, ["chozo_vault_access", "chozo_transport_magmoor_north", "chozo_transport_access_north"])
            + b_ball_tunnel(etank, -5, "RIGHT", "tan")
            + [f"expect {HEALTH} 00C7", "expect 7E09C4 00C7"])
    out += (chain_teleports(m, room, ["chozo_transport_access_north", "chozo_hive_totem", "chozo_totem_access",
                                      "chozo_ruined_gallery"])
            + b_ball_tunnel(tunnel, 6, "LEFT", "galeria_tunel")
            + b_bomb_tunnel(wall, -3, "RIGHT", chozo_layouts.GALLERY_BOMB, "galeria_parede", 30))
    out += (chain_teleports(m, room, ["chozo_ruined_gallery", "chozo_north_atrium", "chozo_ruined_nursery"])
            + clear_room_enemies("chozo_ruined_nursery")
            + b_bomb_tunnel(nursery, -7, "RIGHT", chozo_layouts.NURSERY_BOMB, "nursery"))
    taken = (vault, nursery, tunnel, wall, etank)
    return out + [chozo_item_bit(n) for n in taken] + [f"expect {MAX_MISSILES} 0014", "expect 7E09C4 00C7"]


CHOZO_SAVE = CHOZO.load_stations[1]                       # specs/12i: Save Station 1 (P22), load station 1 of area 1
USED_STATIONS_AREA1 = f"{0x7ED8F8 + 2 * CHOZO.number:06X}"   # $7ED8FA
MAP_STATION_AREA1 = f"{0x7ED908 + CHOZO.number:06X}"         # map_station_byte_array[1] = $7ED909


def area_select_shows_after(area: int, station: int, before: tuple[int, ...], shot: str) -> list[str]:
    """area_select_shows for a save in `area` when the areas `before` it in the game's order (0, 3, 5, 1, 4, 2) have used
    stations too: their names are drawn first, so the save area's first letter is the sprite after the title's and theirs."""
    out = [f"expect {GAME_STATE} {FILE_SELECT_MAP}", f"expect 7E0727 {AREA_SELECT_STEP}", f"expect {AREA} {area:04X}",
           f"expect {LOAD_STATION} {station:04X}"]
    title = len(areaselect.title_pieces(areaselect.TITLE))
    first = title + sum(len(areaselect.label_pieces(areaselect.LABELS[a][3])) for a in before)
    _, _, _, lines, (bx, by) = areaselect.LABELS[area]
    x, y, tile = areaselect.label_pieces(lines)[0]
    addr = OAM_BUFFER + 4 * first
    return out + [f"expect {addr:06X} {((by + y) & 0xFF) << 8 | ((bx + x) & 0xFF):04X}",
                  f"expect {addr + 2:06X} {areaselect.PRIORITY | tile:04X}", f"shot {shot}"]


def chozo_save_test(m: dict, room: dict) -> list[str]:
    """specs/12i, chozo_save_e_continue: from the landing to the Chozo (door_teleport, the North elevator: shortcuts, as
    chozo_regiao_a_itens), the Main Plaza, up into the Nursery Access (rise_through), the Eyon Tunnel, up into the Ruined
    Nursery (rise_through), through its R0 into Save Station 1 (door_teleport); Samus on the pedestal (where the game puts
    her when it loads the station, as tallon_save_fragata), a marker in the saved data (game hours 7), YES, "save
    completed": load station 1 of area 1, its used-station bit ($7ED8FA bit 1); paused, the Chozo's map with its save icon.
    Game over: the area-select screen picks area 1, station 1, and draws "CHOZO / RUINS" (after "TALLON / OVERWORLD": the
    landing's save at the ship); A: the Chozo's room map; continue: back on Save Station 1's pedestal, area 1, the marker
    loaded, the region-B rooms' explored bits kept (the SRAM's area 1 list), the minimap's."""
    out = (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
           + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12I}_save_descendo.png")
           + chain_teleports(m, room, [NORTH, "chozo_ruins_entrance", "chozo_main_plaza"])
           + rise_through(m, room, "chozo_main_plaza", "chozo_nursery_access", 3, "RIGHT")
           + chain_teleports(m, room, ["chozo_nursery_access", "chozo_eyon_tunnel"])
           + rise_through(m, room, "chozo_eyon_tunnel", "chozo_ruined_nursery", 0, "LEFT")
           + chain_teleports(m, room, ["chozo_ruined_nursery", "chozo_save_station_1"])
           + [f"poke {HEALTH} 63"] + poke16(0x7E09E0, 7))
    sx, sy = CHOZO_SAVE.x, CHOZO_SAVE.y
    for addr, v in ((0x7E0AF6, sx), (0x7E0B10, sx), (0x7E0AFA, sy), (0x7E0B14, sy)):
        out += poke16(addr, v)
    screens = [("chozo_nursery_access", 0, 0), ("chozo_eyon_tunnel", 1, 0), ("chozo_ruined_nursery", 1, 0),
               ("chozo_save_station_1", 0, 0)]
    return (out + ["wait 180", f"shot {IMG_12I}_save_pergunta.png", "hold A 2", "wait 300", "hold A 2", "wait 200",
                   f"expect {LOAD_STATION} 0001", f"expect {AREA} 0001", f"expectbit {USED_STATIONS_AREA1} 02",
                   f"expect {GAME_STATE} 0008", f"shot {IMG_12I}_save_salvo.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}", f"shot {IMG_12I}_save_mapa.png",
                   "hold START 10", "wait 200", f"expect {GAME_STATE} 0008",
                   "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
                   "hold A 2", "wait 300"]
            + area_select_shows_after(CHOZO.number, CHOZO_SAVE.index, (TALLON.number,), f"{IMG_12I}_continue_tela_de_area.png")
            + ["hold A 2", "wait 200", f"shot {IMG_12I}_continue_mapa_da_chozo.png"]
            + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0001", f"expect {ROOM_PTR} {room[CHOZO_SAVE.room]}",
               f"expect {LOAD_STATION} 0001", f"expect {GAME_HOURS} 0007", f"expect 7E0AF6 {sx:04X}",
               f"shot {IMG_12I}_continue_na_save_station.png"]
            + [explored_at(*sc) for sc in screens])


def chozo_map_station_test(m: dict, room: dict) -> list[str]:
    """specs/12i, chozo_map_station: from the landing to the Chozo (shortcuts as chozo_save_e_continue), 5 missiles by RAM
    (the Landing Site's), to the Ruined Gallery (door_teleport round the loop from the Plaza Access, rise_through up into
    the Vault Access: no walk) and its L0 (stand_before_door): the red door opened with missiles (its bit $B4), into the
    Map Station; on the pause map before, rooms not visited (the Ruined Nursery, Save Station 1, the Eyon Tunnel, the
    Tower of Light's bottom) are blank; Samus stands east of the terminal and walks into it (use_map_station's way): "map
    data access completed", the pause map opens by itself (vanilla) with the whole built Chozo drawn: those rooms' tiles
    (palette 3: not explored) and the map station byte of area 1 set ($7ED909 = $FF, as the frigate's)."""
    red = next(d for d in built_room("chozo_ruined_gallery").doors if d.lock == "missile").lock_bit
    unvisited = [("chozo_ruined_nursery", 0, 0), ("chozo_save_station_1", 0, 0), ("chozo_eyon_tunnel", 0, 0),
                 ("chozo_tower_of_light", 0, 3)]
    x, floor = built_room("chozo_map_station").map_station
    sx, sy = (x + 3) * 16 + 8, floor * 16 - 21
    place = []
    for addr, v in ((0x7E0AF6, sx), (0x7E0B10, sx), (0x7E0AFA, sy), (0x7E0B14, sy)):
        place += poke16(addr, v)
    (WORK / "vram_12i_vazio.bin").write_bytes(struct.pack("<H", pausemap.BLANK))   # an unexplored, unrevealed screen
    return (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
            + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12I}_mapa_descendo.png")
            + poke16(0x7E09C6, 5) + poke16(0x7E09C8, 5)
            + chain_teleports(m, room, [NORTH, "chozo_ruins_entrance", "chozo_main_plaza", "chozo_plaza_access", "chozo_vault"])
            + rise_through(m, room, "chozo_vault", "chozo_vault_access", 0, "LEFT")
            + chain_teleports(m, room, ["chozo_vault_access", "chozo_transport_magmoor_north", "chozo_transport_access_north",
                                        "chozo_hive_totem", "chozo_totem_access", "chozo_ruined_gallery"])
            + [f"expect {MAP_STATION_AREA1} 00"]
            + stand_before_door("chozo_ruined_gallery", "chozo_map_station", 2)
            + ["hold LEFT 30", "wait 30", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001"] + ["hold LEFT+X 2", "wait 30"] * 6
            + ["wait 60", f"expectbit {0x7ED8B0 + red // 8:06X} {1 << (red % 8):02X}", f"shot {IMG_12I}_mapa_porta_vermelha.png",
               "hold SELECT 2", "wait 10", "hold LEFT 90", "wait 200", f"expect {ROOM_PTR} {room['chozo_map_station']}",
               "hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + [f"expectvram {PAUSE_MAP_VRAM + pausemap.tile_index(*map_tile(k, a, b)):04X} "
               f"{(WORK / f'vram_12i_vazio.bin').relative_to(ROOT)}" for k, a, b in unvisited]
            + [f"shot {IMG_12I}_mapa_antes.png", "hold START 10", "wait 200", f"expect {GAME_STATE} 0008"]
            + place + ["wait 30"] + place + ["wait 30", "hold LEFT 40", "wait 260", f"shot {IMG_12I}_mapa_mensagem.png",
                                              "hold A 2", "wait 200", f"expect {MAP_STATION_AREA1} FF",
                                              f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + revealed_tiles(unvisited, "12i_revelado") + [f"shot {IMG_12I}_mapa_revelado.png"])


def revealed_tiles(screens, tag: str) -> list[str]:
    """While paused (VRAM): those screens show their room's tile as the map station reveals it: not explored, palette 3
    (pausemap.room_tile with bit $400 kept; explored ones lose it, pause_shows)."""
    out = []
    for key, sx, sy in screens:
        tx, ty = map_tile(key, sx, sy)
        path = WORK / f"vram_{tag}_{tx}_{ty}.bin"
        path.write_bytes(struct.pack("<H", pausemap.room_tile(built_room(key), sx, sy)))
        out.append(f"expectvram {PAUSE_MAP_VRAM + pausemap.tile_index(tx, ty):04X} {path.relative_to(ROOT)}")
    return out


# specs/12j: region C (tools/chozo/layouts.py, items.py). Item bits $C3-$C7 (and the Varia Suit's $BC).
IMG_12J = "build/tests/12j"   # the photos of the region C tests (specs/img/12j-* are copies of some)
MAGMA = "chozo_magma_pool"
MEDITATION_RISE = (3, "RIGHT")   # up the Meditation Fountain's T1 into the Ruined Fountain: (column, steer) of rise_through
VARIA_TAKEN_X = 0x0094           # (measured) where the Varia Suit's cutscene leaves her (walking west into it from 2 blocks east;
                                 # specs/14c: on the floor of Flaahgra's pit; 12j's pedestal: $0204)


def chozo_down(m: dict, room: dict, tag: str) -> list[str]:
    """Shortcut (as chozo_regiao_a_itens): from the landing to the Chozo West by door_teleport, down the North elevator."""
    return (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
            + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12J}_{tag}_descendo.png"))


def c_power_bomb_tunnel(n: int, start: int, toward: str, block: tuple[int, int], tag: str) -> list[str]:
    """Chozo item n at the end of a 1-row tunnel shut by a power bomb block (`block`): Samus put by RAM `start` blocks from the
    item (chozo_near), standing she walks `toward` and stops against the wall, the Power Beam leaves the block, ball, SELECT
    twice (power bombs, with missiles in hand: $09D2 = 3), X: the block is air in the level in WRAM; she rolls in to the item."""
    at = level_block(chozo_item(n).room, *block)
    pb = f"{0xC000 | 0x057:04X}"
    return (chozo_near(n, start) + [f"hold {toward} 60", "wait 30", f"expect {at:06X} {pb}", f"shot {IMG_12J}_itens_{tag}_bloco.png",
                                    f"hold {toward}+X 2", "wait 40", f"expect {at:06X} {pb}",
                                    "hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30",
                                    f"expect {POSE} {BALL_POSE if toward == 'RIGHT' else BALL_LEFT_POSE}",
                                    "hold SELECT 2", "wait 10", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0003",
                                    "hold X 2", "wait 80", f"shot {IMG_12J}_itens_{tag}_power_bomb.png", "wait 220",
                                    f"expect {at:06X} 00FF"]
            + b_take_and_close(n, f"{IMG_12J}_itens_{tag}_mensagem.png", toward))


def chozo_items_c_test(m: dict, room: dict) -> list[str]:
    """specs/12j, chozo_regiao_c_itens: the region C items chozo_regiao_c_rota does not take (all but the Varia Suit), each
    picked up by walking or rolling into it, A closing its box, and the piston's lock of the Training Chamber from inside.
    Shortcuts, each noted: the elevator and the rooms by door_teleport (through red and wave doors too), the Morph Ball, the
    Bombs, the Varia Suit (the Magma Pool is hot), the Wave Beam, 5 missiles and 5 power bombs by RAM (the Tallon's items of
    rounds 0-5 and the Sunchamber's), the rooms' enemies deleted by RAM (clear_room_enemies), Samus put by RAM near each
    item (chozo_near; on the Space Jump ledges, as chozo_regiao_a_itens). Ruined Fountain: the Spider Ball track's missile
    (its ledge); Gathering Hall: the bomb gate's (a bomb block); Magma Pool: the expansion behind the power bomb block;
    Training Chamber Access: the Morph Ball path's missile (the hole's tunnel); Training Chamber: the E-tank (its ledge),
    then from the ledge at the piston's tunnel, ball, she rolls west, stops against the bomb block, a bomb breaks it, she
    rolls on into the piston's chamber, stands (facing west), shoots the L0 door's blue cap and walks into the Piston Tunnel. At the end the 5 bits, 20 missiles' and
    10 power bombs' capacity, 199 energy."""
    from chozo import layouts as chozo_layouts
    rf, tc, tca, mp, gh = (chozo_item_index(k) for k in ("chozo_ruined_fountain", "chozo_training_chamber",
                                                          "chozo_training_chamber_access", MAGMA, "chozo_gathering_hall"))
    eq = MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT | VARIA_EQUIPMENT
    out = (chozo_down(m, room, "itens") + poke16(0x7E09A2, eq) + poke16(0x7E09A4, eq) + give_beams(WAVE_BEAM)
           + poke16(0x7E09C6, 5) + poke16(0x7E09C8, 5) + poke16(0x7E09CE, 5) + poke16(0x7E09D0, 5)
           + chain_teleports(m, room, [NORTH, "chozo_ruins_entrance", "chozo_main_plaza", FOUNTAIN, "chozo_ruined_fountain"])
           + clear_room_enemies("chozo_ruined_fountain")
           + chozo_pick_up(rf, f"{IMG_12J}_itens_fonte.png"))
    out += (chain_teleports(m, room, ["chozo_ruined_fountain", "chozo_arboretum_access", "chozo_arboretum",
                                      "chozo_gathering_hall_access", "chozo_gathering_hall"])
            + clear_room_enemies("chozo_gathering_hall")
            + b_bomb_tunnel(gh, -5, "RIGHT", chozo_layouts.GATHERING_BOMB, "gathering", img=IMG_12J))
    out += (chain_teleports(m, room, ["chozo_gathering_hall", "chozo_gathering_hall_access", "chozo_arboretum",
                                      "chozo_arboretum_access", "chozo_ruined_fountain", "chozo_meditation_fountain", MAGMA])
            + c_power_bomb_tunnel(mp, 5, "LEFT", chozo_layouts.MAGMA_PB, "magma"))
    out += (chain_teleports(m, room, [MAGMA, "chozo_training_chamber_access"])
            + b_ball_tunnel(tca, -6, "RIGHT", "tca", img=IMG_12J))
    bomb = level_block("chozo_training_chamber", *chozo_layouts.TRAINING_BOMB)
    x, y = 12 * 16 + 8, 10 * 16 - 21
    place = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y)):
        place += poke16(addr, v)
    out += (chain_teleports(m, room, ["chozo_training_chamber_access", "chozo_training_chamber"])
            + chozo_pick_up(tc, f"{IMG_12J}_itens_training_etank.png", start=2)
            + [f"expect {HEALTH} 00C7", "expect 7E09C4 00C7"]
            + place + ["wait 30"] + place + poke16(0x7E0911, 0) + poke16(0x7E0915, 0)
            + ["wait 4", "hold START 10", "wait 200", "hold START 10", "wait 200", "hold LEFT 30", "wait 20",
               f"expect {bomb:06X} {0xF000 | 0x058:04X}", "hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30",
               f"expect {POSE} {BALL_LEFT_POSE}", "hold LEFT 40", "wait 20", f"shot {IMG_12J}_itens_pistao_bloco.png",
               "hold X 2", "wait 100", f"expect {bomb:06X} 00FF", "hold LEFT 120", "wait 30",
               f"shot {IMG_12J}_itens_pistao_camara.png", "hold UP 2", "wait 30", "hold UP 2", "wait 30",
               f"expect {POSE} 0002", "hold LEFT+X 2", "wait 40", "hold LEFT 90", "wait 200",
               f"expect {ROOM_PTR} {room['chozo_piston_tunnel']}", f"expect {GAME_STATE} 0008",
               f"shot {IMG_12J}_itens_piston_tunnel.png"])
    return out + [chozo_item_bit(n) for n in (rf, tc, tca, mp, gh)] + [
        f"expect {MAX_MISSILES} 0014", f"expect {MAX_POWER_BOMBS} 000A", "expect 7E09C4 00C7"]


def chozo_varia_heat_test(m: dict, room: dict) -> list[str]:
    """specs/12j, chozo_varia_e_calor: the Varia Suit in the game's ROM (the 12g test build proved the mechanism; this is its
    real room). Shortcuts: the elevator and the rooms by door_teleport, the Morph Ball and the Bombs by RAM. Into the Magma
    Pool (the region's hot room, Prime's "Area Damage") with the Power Suit: HEAT_DROP energy lost in HEAT_FRAMES frames;
    to the Sunchamber (up the Sunchamber Lobby's ceiling door: rise_through), Flaahgra won by RAM (specs/14c,
    flaahgra_won_by_ram: Samus put under it in its pit), Samus put by RAM 2 blocks east of the Varia Suit, she walks into it: its bit ($BC), $09A2/$09A4 with $0001, the cutscene leaves her in the Sunchamber
    where she took it (tallon/items.py varia_patch); back in the Magma Pool (door_teleport) the energy stays."""
    varia = chozo_item_index("chozo_sunchamber")
    drop = [f"poke {HEALTH} 63", f"wait {HEAT_FRAMES}", f"expect {HEALTH} {99 - HEAT_DROP:04X}"]
    stay = [f"poke {HEALTH} 63", f"wait {HEAT_FRAMES}", f"expect {HEALTH} 0063"]
    eq = MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT
    out = (chozo_down(m, room, "varia") + poke16(0x7E09A2, eq) + poke16(0x7E09A4, eq)
           + chain_teleports(m, room, [NORTH, "chozo_ruins_entrance", "chozo_main_plaza", FOUNTAIN, "chozo_ruined_fountain",
                                       "chozo_meditation_fountain", MAGMA])
           + [f"expect {ROOM_PTR} {room[MAGMA]}"] + drop + [f"shot {IMG_12J}_calor_sem_varia.png"])
    out += (chain_teleports(m, room, [MAGMA, "chozo_meditation_fountain"])
            + rise_through(m, room, "chozo_meditation_fountain", "chozo_ruined_fountain", *MEDITATION_RISE)
            + clear_room_enemies("chozo_ruined_fountain")
            + chain_teleports(m, room, ["chozo_ruined_fountain", "chozo_arboretum_access", "chozo_arboretum",
                                        "chozo_sunchamber_lobby"])
            + rise_through(m, room, "chozo_sunchamber_lobby", "chozo_sunchamber_access", 0, "LEFT")
            + chain_teleports(m, room, ["chozo_sunchamber_access", "chozo_sunchamber"])
            # specs/14c: Flaahgra won by RAM (its health 0; Samus put by RAM in the pit under it: its touch kills it, by its
            # own code); the Varia Suit appears
            + flaahgra_won_by_ram() + chozo_near(varia, 5) + ["wait 900", "expectbit 7ED829 42"]
            + chozo_pick_up(varia, f"{IMG_12J}_varia_mensagem.png", start=2)
            + [f"expectbit 7E09A2 {VARIA_EQUIPMENT:02X}", f"expectbit 7E09A4 {VARIA_EQUIPMENT:02X}",
               f"expect {ROOM_PTR} {room['chozo_sunchamber']}", f"expect {SAMUS_X} {VARIA_TAKEN_X:04X}",
               f"shot {IMG_12J}_varia_pega.png"])
    out += (chain_teleports(m, room, ["chozo_sunchamber", "chozo_sunchamber_access", "chozo_sunchamber_lobby",
                                      "chozo_arboretum", "chozo_arboretum_access", "chozo_ruined_fountain",
                                      "chozo_meditation_fountain", MAGMA])
            + stay + [f"shot {IMG_12J}_calor_com_varia.png"])
    return out


# the walks of chozo_regiao_c_rota, measured in the emulator (scratchpad s12j: sweep.py, try.py): (cycles of chozo_walk) or
# a list of inputs; the blue doors opened by the walker's shots
C_RFA_WALK = 39                     # through the Ruined Fountain Access (its crawlers) into the Ruined Fountain
C_OVER_THE_HOLE = ["hold RIGHT 4", "hold RIGHT+A 30", "hold RIGHT 20", "wait 30"]   # off the L0 ledge over the floor door
C_FOUNTAIN_WALK = 14                # past the Fireflies, the basin, up the R0 step into the Arboretum Access
C_AA_DOWN = 14                      # down the U's west steps to the bottom of the lower hall
C_AA_CLIMB = ([f"poke {HEALTH} 63", "hold RIGHT 2", "wait 10"]
              + ["hold A+RIGHT 40", "hold RIGHT 15", "wait 10", f"poke {HEALTH} 63"] * 6)   # up the east steps (full jumps)
C_ARB_DOWN = ["hold RIGHT 400", "hold A+RIGHT 30", "hold RIGHT 60", "wait 30"]   # off the L0 ledge, the zigzag's tops, under
                                    # the branch, down to the dry pool, out of it to the R2 door
C_GHA_WALK = 16
C_GH_DOWN = ["hold RIGHT 60", "wait 60", "hold LEFT 200", "wait 30"]   # off the west gallery onto the stair and the plinth,
                                    # then west off it to the L1 door
C_LOBBY_TO_PLATFORM = ["hold RIGHT 60", "wait 20", "hold A+LEFT 30", "hold LEFT 10", "wait 30", "hold LEFT 20", "wait 20"]
C_ACCESS_WALK = 12                  # west over the floor and up the L0 step into the Sunchamber
# specs/14c: the Sunchamber is Flaahgra's arena (the Spore Spawn in the pit of its bottom-west screen, layouts.sunchamber):
# west across the hall over the bomb slots' pits (FLAAHGRA_HALL's measured walk) and down into the pit's east end, under the
# right lobe of the boss' figure 8 (x ~$D9: its shells reach x 235); the boss, its health 0 by RAM as she came in
# (flaahgra_won_by_ram), dies at its first touch of her there (its own death code: the bits $02 and $40, the Varia appears
# under its husk at (8, 43)), whatever the loop's phase (900 frames: a loop and its stop); then west into the Varia Suit
C_TO_THE_PIT = ["hold LEFT 60", "hold LEFT+A 25", "hold LEFT 80", "hold LEFT+A 25", "hold LEFT 110", "wait 20", "hold LEFT 72",
                f"poke {HEALTH} 63", "wait 300", f"poke {HEALTH} 63", "wait 300", f"poke {HEALTH} 63", "wait 300",
                f"poke {HEALTH} 63"]
C_PIT_TO_VARIA = ["hold LEFT 80"]
C_STA_WALK = 40                     # the Sun Tower Access, west over its channels, into the Sun Tower


def flaahgra_won_by_ram() -> list[str]:
    """specs/14c, a shortcut (epic 14 decision 9: the walks and the chain win a boss fight by a noted RAM shortcut; the real
    fight is chozo_flaahgra's), as Samus comes into the Sunchamber: the Spore Spawn's health (slot 0) set to 0. It dies at its
    next touch of her, by its own code (SporeSpawn_Touch -> $A5:EDF3: the mini-boss bit $02, the roof's PLM, the death's
    fade), and the arena routine then sets the bit $40, stops the music and spawns the Varia Suit."""
    return [f"expect {ROOM_PTR} {built_room_ptr('chozo_sunchamber')}", f"expect {ENEMY_TABLE:06X} {SPECIES['flaahgra'].ptr:04X}",
            f"poke {ENEMY_TABLE + ENEMY_HEALTH:06X} 00", f"poke {ENEMY_TABLE + ENEMY_HEALTH + 1:06X} 00"]


def red_door(room: dict, key: str, toward: str, to: str, refill: bool) -> list[str]:
    """Standing against `key`'s red door (toward `toward`): missiles selected, 6 shots (the energy refilled: enemies around),
    its bit on, back to the beam, through into `to`. `refill`: 5 missiles by RAM first (shortcut: the Chozo's and the
    Tallon's expansions of rounds 0-1 are not on the way)."""
    bit = next(d for d in built_room(key).doors if d.to_room == to).lock_bit
    return ((poke16(0x7E09C6, 5) if refill else []) + ["wait 30", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001"]
            + [f"poke {HEALTH} 63", f"hold {toward}+X 2", "wait 30"] * 6
            + ["wait 60", f"expectbit {0x7ED8B0 + bit // 8:06X} {1 << (bit % 8):02X}", f"expect {MISSILES} 0000",
               "poke 7E09D2 00", "wait 10", f"hold {toward} 90", "wait 200", f"expect {ROOM_PTR} {room[to]}",
               f"expect {GAME_STATE} 0008", f"poke {HEALTH} 63"])


def put_samus(x: int, floor: int, cam_x: int, cam_y: int) -> list[str]:
    """Shortcut: Samus put by RAM standing on (block x, floor row), placed twice (stops a run), the camera at (cam_x, cam_y)
    px, the screen redrawn by pausing and unpausing."""
    place = []
    for addr, v in ((0x7E0AF6, x * 16 + 8), (0x7E0B10, x * 16 + 8), (0x7E0AFA, floor * 16 - 21), (0x7E0B14, floor * 16 - 21)):
        place += poke16(addr, v)
    return (place + ["wait 30"] + place + poke16(0x7E0911, cam_x) + poke16(0x7E0915, cam_y)
            + ["wait 4", "hold START 10", "wait 200", "hold START 10", "wait 200"])


CHOZO_C_SCREENS = [("chozo_ruined_fountain_access", 2, 0), ("chozo_ruined_fountain", 0, 0), ("chozo_ruined_fountain", 1, 0),
                   ("chozo_arboretum_access", 0, 0), ("chozo_arboretum_access", 1, 1), ("chozo_arboretum_access", 2, 0),
                   ("chozo_arboretum", 0, 0), ("chozo_arboretum", 1, 2), ("chozo_arboretum", 2, 2), ("chozo_arboretum", 2, 0),
                   ("chozo_gathering_hall_access", 0, 0), ("chozo_gathering_hall_access", 1, 0),
                   ("chozo_gathering_hall", 0, 0), ("chozo_gathering_hall", 0, 1), ("chozo_save_station_2", 0, 0),
                   ("chozo_sunchamber_lobby", 0, 0), ("chozo_sunchamber_access", 1, 0), ("chozo_sunchamber_access", 0, 0),
                   ("chozo_sunchamber", 3, 2), ("chozo_sunchamber", 1, 2), ("chozo_sun_tower_access", 4, 0),
                   ("chozo_sun_tower_access", 0, 0), ("chozo_sun_tower", 1, 2), ("chozo_sun_tower", 0, 0),
                   ("chozo_sun_tower", 0, 1)]


def chozo_route_c(m: dict, room: dict) -> list[str]:
    """specs/12j, chozo_regiao_c_rota: from the landing (a real game), the Landing Site's missile picked up walking (5
    missiles), to the Chozo West (door_teleport) and down the North elevator (onto_platform), the Ruins Entrance, the Main
    Plaza and the Ruined Fountain Access by door_teleport (region A's walk is chozo_regiao_a_rota's); then WALKING with the
    enemies alive (chozo_walk refills the energy): the Ruined Fountain Access, over the Ruined Fountain's floor door, its
    basin, the Arboretum Access' U (down its west steps, up its east ones with full jumps), its red door opened with the
    Landing Site's missiles (bit $B6), the Arboretum from its L0 ledge down the zigzag to the floor, the dry pool, its R2 red
    door, the Gathering Hall Access, the Gathering Hall down from its west gallery to the L1 red door, Save Station 2 (5
    missiles by RAM before each of these doors: shortcut). The Sunchamber leg (round 2): the Morph Ball and the Bombs by RAM
    (the Tallon's), back to the Arboretum by door_teleport, Samus put by RAM on the tree's crown by the tunnel (shortcut:
    the zigzag and the branch up to it are the validator's), ball, a bomb breaks the block, she rolls into the R0 chamber,
    stands, its red door, the Sunchamber Lobby onto the T0 platform and up the ceiling door into the Sunchamber Access (a
    real climb, steered west), west into the Sunchamber; specs/14c: Flaahgra won by RAM (flaahgra_won_by_ram: its health 0,
    it dies at its first touch as she walks into its pit), west into the Varia Suit on the pit's floor (bit $BC, $09A2 bit 0). Out: door_teleport to the Sun Tower Access (the arena's zigzag up to the L0 is the validator's), west
    along it into the Sun Tower (its R2), Samus put by RAM on the top passage (shortcut: the east zigzag up to it is the
    validator's), she walks west and drops down the shaft onto the L1 door's floor, through it into the Magmoor transport
    (Prime's free way down the tower). Each room's explored bit is set; the pause map shows them."""
    varia = chozo_item_index("chozo_sunchamber")
    return (tallon_first_missile("tallon_chozo_c")
            + chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
            + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12J}_rota_descendo.png")
            + chain_teleports(m, room, [NORTH, "chozo_ruins_entrance", "chozo_main_plaza", FOUNTAIN])
            # the last cycles may start the door's transition late: 150 frames more before the checks
            + chozo_walk("RIGHT", C_RFA_WALK, "chozo_ruined_fountain", room)[:-3]
            + ["wait 150", f"expect {ROOM_PTR} {room['chozo_ruined_fountain']}", f"expect {GAME_STATE} 0008",
               f"poke {HEALTH} 63", f"shot {IMG_12J}_rota_fonte.png"]
            + C_OVER_THE_HOLE + [f"expect {ROOM_PTR} {room['chozo_ruined_fountain']}", f"expect 7E0AFA {13 * 16 - 21:04X}"]
            + chozo_walk("RIGHT", C_FOUNTAIN_WALK, "chozo_arboretum_access", room)
            + chozo_walk("RIGHT", C_AA_DOWN, "chozo_arboretum_access", room) + [f"expect 7E0AFA {28 * 16 - 21:04X}",
                                                                              f"shot {IMG_12J}_rota_arboretum_access.png"]
            + C_AA_CLIMB + [f"expect 7E0AFA {10 * 16 - 21:04X}"]
            + red_door(room, "chozo_arboretum_access", "RIGHT", "chozo_arboretum", False)
            + C_ARB_DOWN + [f"expect {ROOM_PTR} {room['chozo_arboretum']}", f"shot {IMG_12J}_rota_arboretum.png"]
            + red_door(room, "chozo_arboretum", "RIGHT", "chozo_gathering_hall_access", True)
            + chozo_walk("RIGHT", C_GHA_WALK, "chozo_gathering_hall", room) + C_GH_DOWN
            + [f"expect 7E0AFA {26 * 16 - 21:04X}", f"shot {IMG_12J}_rota_gathering_hall.png"]
            + red_door(room, "chozo_gathering_hall", "LEFT", "chozo_save_station_2", True)
            + [f"shot {IMG_12J}_rota_save_station_2.png"]
            # round 2: the crown's tunnel, the Sunchamber
            + poke16(0x7E09A2, MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT) + poke16(0x7E09A4, MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT)
            + chain_teleports(m, room, ["chozo_save_station_2", "chozo_gathering_hall", "chozo_gathering_hall_access",
                                        "chozo_arboretum"])
            + put_samus(34, 10, 512, 0) + [f"shot {IMG_12J}_rota_copa.png", "hold RIGHT 20", "wait 10",
                                          "hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_POSE}",
                                          "hold RIGHT 30", "wait 10", "hold X 2", "wait 100",
                                          f"expect {level_block('chozo_arboretum', 37, 9):06X} 00FF",
                                          "hold RIGHT 80", "wait 30", "hold UP 2", "wait 30", "hold UP 2", "wait 30",
                                          f"shot {IMG_12J}_rota_camara.png"]
            + red_door(room, "chozo_arboretum", "RIGHT", "chozo_sunchamber_lobby", True)
            + C_LOBBY_TO_PLATFORM + [f"expect 7E0AFA {6 * 16 - 21:04X}"] + climb_jump("LEFT")
            + [f"expect {ROOM_PTR} {room['chozo_sunchamber_access']}", f"expect 7E0AFA {13 * 16 - 21:04X}"]
            + out_of_arena(chozo_walk("LEFT", C_ACCESS_WALK, "chozo_sunchamber", room)) + [f"shot {IMG_12J}_rota_sunchamber.png"]
            + flaahgra_won_by_ram() + C_TO_THE_PIT + ["expectbit 7ED829 42"] + C_PIT_TO_VARIA
            # the box takes the A ~420 frames after the walk (earlier, Samus stayed frozen: measured)
            + ["wait 120", f"shot {IMG_12J}_rota_varia_mensagem.png", "wait 300", "hold A 2", "wait 200",
               chozo_item_bit(varia), f"expectbit 7E09A2 {VARIA_EQUIPMENT:02X}", f"expectbit 7E09A4 {VARIA_EQUIPMENT:02X}",
               f"expect {GAME_STATE} 0008", f"shot {IMG_12J}_rota_varia.png"]
            + door_teleport(m, "chozo_sunchamber", "chozo_sun_tower_access")
            + chozo_walk("LEFT", C_STA_WALK, "chozo_sun_tower", room) + [f"shot {IMG_12J}_rota_sun_tower.png"]
            + put_samus(14, 8, 0, 0) + [f"shot {IMG_12J}_rota_torre_alto.png", "hold LEFT 60", "wait 60",
                                        f"expect 7E0AFA {26 * 16 - 21:04X}", f"shot {IMG_12J}_rota_torre_bolso.png",
                                        f"poke {HEALTH} 63", "hold LEFT+X 2", "wait 30", "hold LEFT 90", "wait 200",
                                        f"expect {ROOM_PTR} {room['chozo_transport_magmoor_north']}", f"expect {GAME_STATE} 0008"]
            + [explored_at(*screen) for screen in CHOZO_C_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(CHOZO, CHOZO_C_SCREENS, "chozo_c") + [f"shot {IMG_12J}_rota_mapa.png", "hold START 10", "wait 200"])


CHOZO_SAVE_2 = CHOZO.load_stations[2]                     # specs/12j: Save Station 2 (P39), load station 2 of area 1


def chozo_save_2_test(m: dict, room: dict) -> list[str]:
    """specs/12j, chozo_save_station_2: as chozo_save_e_continue, at Save Station 2 (off the Gathering Hall: door_teleport
    there, through its red door). Samus on the pedestal, a marker in the saved data (game hours 9), YES, "save completed":
    load station 2 of area 1, its used-station bit ($7ED8FA bit 2). Game over: the area-select screen picks area 1, station
    2, and draws "CHOZO / RUINS"; continue: back on Save Station 2's pedestal, area 1, the marker loaded."""
    out = (chozo_down(m, room, "save2")
           + chain_teleports(m, room, [NORTH, "chozo_ruins_entrance", "chozo_main_plaza", FOUNTAIN, "chozo_ruined_fountain",
                                       "chozo_arboretum_access", "chozo_arboretum", "chozo_gathering_hall_access",
                                       "chozo_gathering_hall", "chozo_save_station_2"])
           + [f"poke {HEALTH} 63"] + poke16(0x7E09E0, 9))
    sx, sy = CHOZO_SAVE_2.x, CHOZO_SAVE_2.y
    for addr, v in ((0x7E0AF6, sx), (0x7E0B10, sx), (0x7E0AFA, sy), (0x7E0B14, sy)):
        out += poke16(addr, v)
    # a touch of LEFT: put by RAM after a door from the east she faces the screen and the station does not ask (measured)
    return (out + ["hold LEFT 1", "wait 180", f"shot {IMG_12J}_save2_pergunta.png", "hold A 2", "wait 300", "hold A 2", "wait 200",
                   f"expect {LOAD_STATION} 0002", f"expect {AREA} 0001", f"expectbit {USED_STATIONS_AREA1} 04",
                   f"expect {GAME_STATE} 0008", f"shot {IMG_12J}_save2_salvo.png",
                   "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
                   "hold A 2", "wait 300"]
            + area_select_shows_after(CHOZO.number, CHOZO_SAVE_2.index, (TALLON.number,), f"{IMG_12J}_save2_tela_de_area.png")
            + ["hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0001", f"expect {ROOM_PTR} {room[CHOZO_SAVE_2.room]}",
               f"expect {LOAD_STATION} 0002", f"expect {GAME_HOURS} 0009", f"expect 7E0AF6 {sx:04X}",
               f"shot {IMG_12J}_save2_continue.png"])


# specs/12k: region D (tools/chozo/layouts.py, items.py). Item bits $C8-$CF (and the Charge Beam's $BB).
IMG_12K = "build/tests/12k"   # the photos of the region D tests (specs/img/12k-* are copies of some)
TO_GATHERING = [NORTH, "chozo_ruins_entrance", "chozo_main_plaza", "chozo_ruined_fountain_access", "chozo_ruined_fountain", "chozo_arboretum_access",
                "chozo_arboretum", "chozo_gathering_hall_access", "chozo_gathering_hall"]


def ball_through_bomb_block(toward: str, block_at: int, tag: str) -> list[str]:
    """Standing just before a 1-row tunnel shut by a bomb block (level block in WRAM at `block_at`): ball, roll against it, a
    bomb: the block is air; she rolls on `toward` and stands up past it (as chozo_regiao_c_rota's crown)."""
    return ["hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30",
            f"expect {POSE} {BALL_POSE if toward == 'RIGHT' else BALL_LEFT_POSE}", f"hold {toward} 30", "wait 10",
            f"expect {block_at:06X} {0xF000 | 0x058:04X}", f"shot {IMG_12K}_{tag}_bloco.png",
            "hold X 2", "wait 100", f"expect {block_at:06X} 00FF", f"hold {toward} 80", "wait 30",
            "hold UP 2", "wait 30", "hold UP 2", "wait 30", f"shot {IMG_12K}_{tag}_depois.png"]


def chozo_items_d_test(m: dict, room: dict) -> list[str]:
    """specs/12k, chozo_regiao_d_itens: the region D items chozo_regiao_d_rota does not take, each picked up by walking or
    rolling into it, A closing its box. Shortcuts, each noted: the elevator and the rooms by door_teleport (through red doors
    too), the Morph Ball and the Bombs by RAM (the Tallon's items of rounds 0-1), the rooms' enemies deleted by RAM
    (clear_room_enemies), Samus put by RAM near each item (chozo_near; on the Space Jump ledges: the Dynamo's and the
    Furnace's tracks, standing there: the headroom the validator now checks, specs/12k). Watery Hall Access: the missile
    wall's (a bomb block); Watery Hall: the pool's Morph Ball path; Dynamo: the breakable wall's (a bomb block in the pit's
    tunnel) and the track's (its ledge); Burn Dome: the tunnel's (a bomb block); Furnace: the E-tank under the floor (a bomb
    block in the pit's tunnel) and the track's missile (its ledge). At the end the 7 bits, 35 missiles' capacity (5 + 6 x 5),
    199 energy."""
    from chozo import layouts as L
    from chozo import items as chozo_items
    of = lambda key: [n for n, it in enumerate(chozo_items.ITEMS) if it.room == key]   # noqa: E731 (table order)
    wha, wh_pool = of("chozo_watery_hall_access")[0], chozo_item_index("chozo_watery_hall", 0xEEDB)
    dyn_wall, dyn_track = of("chozo_dynamo")
    bd_tunnel = of("chozo_burn_dome")[1]
    fur_etank, fur_track = chozo_item_index("chozo_furnace", 0xEED7), chozo_item_index("chozo_furnace", 0xEEDB)
    eq = MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT
    out = (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
           + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12K}_itens_descendo.png")
           + poke16(0x7E09A2, eq) + poke16(0x7E09A4, eq) + poke16(0x7E09C6, 5) + poke16(0x7E09C8, 5)
           + chain_teleports(m, room, TO_GATHERING + ["chozo_watery_hall_access"])
           + clear_room_enemies("chozo_watery_hall_access")
           + b_bomb_tunnel(wha, -5, "RIGHT", L.WHA_BOMB, "wha", img=IMG_12K))
    out += (chain_teleports(m, room, ["chozo_watery_hall_access", "chozo_watery_hall"])
            + b_ball_tunnel(wh_pool, -7, "RIGHT", "watery_pool", img=IMG_12K))
    out += (chain_teleports(m, room, ["chozo_watery_hall", "chozo_dynamo_access", "chozo_dynamo"])
            + clear_room_enemies("chozo_dynamo")
            + b_bomb_tunnel(dyn_wall, -5, "RIGHT", L.DYNAMO_BOMB, "dynamo", img=IMG_12K)
            + chozo_pick_up(dyn_track, f"{IMG_12K}_itens_dynamo_trilho.png", start=2))
    out += (chain_teleports(m, room, ["chozo_dynamo", "chozo_dynamo_access", "chozo_watery_hall", "chozo_watery_hall_access",
                                      "chozo_gathering_hall", "chozo_east_atrium", "chozo_energy_core_access",
                                      "chozo_energy_core"])
            # up the T3 ceiling door into the Burn Dome Access' chamber (rise_through: a door_teleport up hangs, 10a), then
            # through its Morph Ball tunnel by door_teleport
            + rise_through(m, room, "chozo_energy_core", "chozo_burn_dome_access", 3, "RIGHT")
            + chain_teleports(m, room, ["chozo_burn_dome_access", "chozo_burn_dome"])
            + clear_room_enemies("chozo_burn_dome")
            + b_bomb_tunnel(bd_tunnel, -9, "RIGHT", L.BURN_DOME_BOMB, "burn_dome", img=IMG_12K))
    out += (chain_teleports(m, room, ["chozo_burn_dome", "chozo_burn_dome_access", "chozo_energy_core",
                                      "chozo_west_furnace_access", "chozo_furnace"])
            + clear_room_enemies("chozo_furnace")
            + b_bomb_tunnel(fur_etank, 7, "LEFT", L.FURNACE_BOMB, "furnace", img=IMG_12K)
            + [f"expect {HEALTH} 00C7", "expect 7E09C4 00C7"]
            + chozo_pick_up(fur_track, f"{IMG_12K}_itens_furnace_trilho.png", start=2))
    return out + [chozo_item_bit(n) for n in (wha, wh_pool, dyn_wall, dyn_track, bd_tunnel, fur_etank, fur_track)] + [
        f"expect {MAX_MISSILES} 0023", "expect 7E09C4 00C7"]


CHOZO_D_SCREENS = [("chozo_watery_hall_access", 0, 0), ("chozo_watery_hall_access", 2, 0), ("chozo_watery_hall", 0, 1),
                   ("chozo_watery_hall", 2, 0), ("chozo_watery_hall", 3, 0), ("chozo_dynamo_access", 0, 0),
                   ("chozo_dynamo", 0, 0), ("chozo_east_atrium", 0, 0), ("chozo_east_atrium", 1, 0),
                   ("chozo_energy_core_access", 0, 0), ("chozo_energy_core_access", 1, 0), ("chozo_energy_core", 0, 0),
                   ("chozo_energy_core", 3, 0), ("chozo_burn_dome_access", 0, 0), ("chozo_burn_dome_access", 1, 0),
                   ("chozo_burn_dome", 0, 0), ("chozo_burn_dome", 1, 0), ("chozo_west_furnace_access", 0, 0),
                   ("chozo_furnace", 0, 0), ("chozo_furnace", 2, 0)]
D_WHA_WALK = 22                     # through the Watery Hall Access (its Skrees, the sunken stretch), out of the dip
D_EA_WALK = 16                      # the East Atrium (its Skrees), over the raised stretch
D_ECA_WALK = 12                     # the Energy Core Access, under the bend
D_EC_WALK = 26                      # over the dry pools to the step under the T3 platform
D_BDA_WALK = 14                     # from the pit, east along the hall into the Burn Dome
D_TO_THE_STAND = 10                 # west of the stand, up onto it into the missile (Prime's Bombs)
D_FURNACE_WALK = ["hold RIGHT 260", "wait 60", f"expect 7E0AFA {13 * 16 - 21:04X}",   # along the corridor, off the balcony
                  f"poke {HEALTH} 63", "hold RIGHT 40", "wait 90"]   # onto the zigzag's top platform, off it to the floor


def to_the_door(toward: str, to: str, room: dict) -> list[str]:
    """After a chozo_walk: on to the blue door ahead without jumping (a jump by a door in a 1-screen hall lands on top of
    its cap: emulator), a shot opens it, through it into `to` (the energy refilled)."""
    return [f"poke {HEALTH} 63", f"hold {toward} 120", f"hold {toward}+X 2", "wait 20", f"poke {HEALTH} 63",
            f"hold {toward} 100", "wait 200", f"expect {ROOM_PTR} {room[to]}", f"expect {GAME_STATE} 0008", f"poke {HEALTH} 63"]


def chozo_route_d(m: dict, room: dict) -> list[str]:
    """specs/12k, chozo_regiao_d_rota: from the landing (a real game), the Landing Site's missile picked up walking (5
    missiles), to the Chozo West (door_teleport) and down the North elevator, region A-C's rooms to the Gathering Hall by
    door_teleport (their walks are 12f-12j's) and on to the Watery Hall Access (shortcut: the Gathering Hall's east gallery is
    the validator's); then WALKING with the enemies alive (chozo_walk refills the energy): the Watery Hall Access, its red
    door opened with the Landing Site's missiles (bit $BA), into the Watery Hall; Samus put by RAM on the upper gallery
    (shortcut: the stair is the validator's), she walks into the Charge Beam (bit $BB, $09A6/$09A8 bit $1000). With the
    Morph Ball and the Bombs by RAM (the Tallon's, round 1): from the gallery's east end, ball, a bomb breaks the block
    (Prime's breakable block), she rolls into the R0 chamber, stands, its red door (5 missiles by RAM: shortcut; bit $BB of
    the doors), the Dynamo Access and its red door into the Dynamo. The east branch: back to the Gathering Hall by
    door_teleport, its R1 into the East Atrium, walking the East Atrium, the Energy Core Access and the Energy Core to the step
    under the T3 platform; up the ceiling door (Samus put on the platform, a real climb steered east) into the Burn Dome
    Access' chamber, ball, she rolls through the Morph Ball tunnel to the pit, stands, walks into the Burn Dome and onto the
    stand into its missile (Prime's Bombs; specs/14d: it starts the Incinerator Drone's fight, won by RAM: arena_won_by_ram).
    Back in the Energy Core (door_teleport), Samus put on the step by the bomb-slot
    tunnel: ball, a bomb, she rolls into the R0 chamber, stands, walks through the West Furnace Access into the Furnace and
    down off its balcony into the hall. Each room's explored bit is set; the pause map shows them."""
    from chozo import layouts as L
    charge = chozo_item_index("chozo_watery_hall", 0xEEEB)
    stand = chozo_item_index("chozo_burn_dome", 0xEEDB)
    eq = MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT
    return (tallon_first_missile("tallon_chozo_d")
            + chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
            + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12K}_rota_descendo.png")
            + chain_teleports(m, room, TO_GATHERING + ["chozo_watery_hall_access"]) + [f"shot {IMG_12K}_rota_wha.png"]
            + chozo_walk("RIGHT", D_WHA_WALK, "chozo_watery_hall_access", room)[:-3]
            + ["hold RIGHT 150", "wait 30"]   # on to the red door without jumping (a jump there lands on its cap)
            + red_door(room, "chozo_watery_hall_access", "RIGHT", "chozo_watery_hall", False)
            + [f"shot {IMG_12K}_rota_watery_hall.png"]
            + chozo_pick_up(charge, f"{IMG_12K}_rota_charge_mensagem.png", start=1)
            + [f"expectbit 7E09A7 {CHARGE_EQUIPMENT >> 8:02X}", f"expectbit 7E09A9 {CHARGE_EQUIPMENT >> 8:02X}",
               f"shot {IMG_12K}_rota_charge.png"]
            + poke16(0x7E09A2, eq) + poke16(0x7E09A4, eq)
            + put_samus(L.WATERY_BOMB[0] - 1, 10, 768, 0) + ["hold RIGHT 20", "wait 10"]
            + ball_through_bomb_block("RIGHT", level_block("chozo_watery_hall", *L.WATERY_BOMB), "rota_watery")
            + red_door(room, "chozo_watery_hall", "RIGHT", "chozo_dynamo_access", True)
            + chozo_walk("RIGHT", 6, "chozo_dynamo_access", room)[:-3] + ["hold RIGHT 60", "wait 30"]
            + red_door(room, "chozo_dynamo_access", "RIGHT", "chozo_dynamo", True) + [f"shot {IMG_12K}_rota_dynamo.png"]
            # the east branch
            + chain_teleports(m, room, ["chozo_dynamo", "chozo_dynamo_access", "chozo_watery_hall", "chozo_watery_hall_access",
                                        "chozo_gathering_hall", "chozo_east_atrium"])
            + chozo_walk("RIGHT", D_EA_WALK, "chozo_east_atrium", room)[:-3] + to_the_door("RIGHT", "chozo_energy_core_access", room)
            + chozo_walk("RIGHT", D_ECA_WALK, "chozo_energy_core_access", room)[:-3] + to_the_door("RIGHT", "chozo_energy_core", room)
            + [f"shot {IMG_12K}_rota_energy_core.png"]
            + chozo_walk("RIGHT", D_EC_WALK, "chozo_energy_core", room)
            + chozo_climb(room, "chozo_energy_core", "chozo_burn_dome_access", 40, "RIGHT")
            + [f"expect 7E0AFA {13 * 16 - 21:04X}", f"shot {IMG_12K}_rota_bda_camara.png",
               "hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_POSE}", "hold RIGHT 90", "wait 30",
               "hold UP 2", "wait 30", "hold UP 2", "wait 30", f"expect 7E0AFA {13 * 16 - 21:04X}",
               f"shot {IMG_12K}_rota_bda_poco.png", "hold A+RIGHT 30", "hold RIGHT 10", "wait 30"]
            + chozo_walk("RIGHT", D_BDA_WALK, "chozo_burn_dome", room) + [f"shot {IMG_12K}_rota_burn_dome.png"]
            + chozo_walk("RIGHT", D_TO_THE_STAND, "chozo_burn_dome", room)[:-3]
            + ["wait 120", f"shot {IMG_12K}_rota_suporte_mensagem.png", "wait 300", "hold A 2", "wait 120",
               chozo_item_bit(stand), f"expect {GAME_STATE} 0008"]
            # specs/14d: the missile started the Incinerator Drone's fight: won by RAM (chozo_incinerator_drone fights it)
            + arena_won_by_ram("chozo_burn_dome") + ["expectbit 7ED829 10"]
            # the bomb slots' door
            + chain_teleports(m, room, ["chozo_burn_dome", "chozo_burn_dome_access", "chozo_energy_core"])
            + put_samus(L.ENERGY_CORE_BOMB[0] - 1, 10, 768, 0) + ["hold RIGHT 20", "wait 10"]
            + ball_through_bomb_block("RIGHT", level_block("chozo_energy_core", *L.ENERGY_CORE_BOMB), "rota_energy_core")
            + [f"poke {HEALTH} 63", "hold RIGHT+X 2", "wait 30", "hold RIGHT 90", "wait 200",
               f"expect {ROOM_PTR} {room['chozo_west_furnace_access']}", f"expect {GAME_STATE} 0008"]
            + chozo_walk("RIGHT", 8, "chozo_furnace", room) + D_FURNACE_WALK
            + [f"expect {ROOM_PTR} {room['chozo_furnace']}", f"expect 7E0AFA {28 * 16 - 21:04X}", f"shot {IMG_12K}_rota_furnace.png"]
            + [explored_at(*screen) for screen in CHOZO_D_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(CHOZO, CHOZO_D_SCREENS, "chozo_d") + [f"shot {IMG_12K}_rota_mapa.png", "hold START 10", "wait 200"])


# specs/12l: region E (tools/chozo/layouts.py, items.py). Item bits $D0-$D2, red door bits $BD-$BF.
IMG_12L = "build/tests/12l"   # the photos of the region E tests (specs/img/12l-* are copies of some)
TO_FURNACE = TO_GATHERING + ["chozo_east_atrium", "chozo_energy_core_access", "chozo_energy_core", "chozo_west_furnace_access",
                             "chozo_furnace"]
SOUTH, EAST = "chozo_transport_tallon_south", "chozo_transport_tallon_east"
# shooting a floor door's cap: a short jump, aiming down in the air (as the grey floor doors of door_walk)
SHOOT_DOWN = ["hold A 6", "hold A+DOWN 4", "hold A+DOWN+X 2", "hold A+DOWN 6", "hold A+DOWN+X 2", "wait 60"]
STAND_ON_B3 = 29 * 16 - 21      # Samus' y standing on the Furnace's B3 cap (row 29), in the floor's 1-row dip
POOL_FLOOR_Y = 14 * 16 - 21     # standing on the Reflecting Pool's floor (row 14)
POOL_PLATFORM_Y = 6 * 16 - 21   # on the T2 door's platform (row 6)
POOL_STEP_Y = 10 * 16 - 21      # on the step under the platform (row 10), the R0 ledge's row
POOL_CLIMB = ["hold RIGHT 2", "wait 20", "hold A 20", "hold A+RIGHT 25", "hold RIGHT 60", "wait 60"]   # from (35, 14) beside the step
CHOZO_E_SCREENS = [("chozo_furnace", 3, 1), ("chozo_east_furnace_access", 0, 0), ("chozo_hall_of_the_elders", 0, 0),
                   ("chozo_hall_of_the_elders", 1, 1), ("chozo_hall_of_the_elders", 2, 1), ("chozo_reflecting_pool_access", 0, 0),
                   ("chozo_reflecting_pool", 2, 0), ("chozo_transport_access_south", 0, 0),
                   (SOUTH, 0, 0)]


def chozo_door_shut(key: str, to: str) -> list[str]:
    """Walk into the cap of key's side door to `to`: she stops against it (any built room; beam_door_shut's rule)."""
    r = built_room(key)
    d = next(d for d in r.doors if d.to_room == to)
    x = 2 * 16 + 5 if d.side == "L" else (r.width * 16 - 2) * 16 - 5
    toward = "LEFT" if d.side == "L" else "RIGHT"
    return [f"poke {HEALTH} 63", f"hold {toward} 60", "wait 20", f"expect {SAMUS_X} {x:04X}"]


def ball_through_bomb_block_e(toward: str, block_at: int, tag: str) -> list[str]:
    """ball_through_bomb_block with the region E photos."""
    return [line.replace(IMG_12K, IMG_12L) for line in ball_through_bomb_block(toward, block_at, tag)]


def chozo_ice_door_holds(room: dict, key: str, to: str, tag: str) -> list[str]:
    """At key's shut ice side door to `to`: the Power Beam (3 shots), missiles (3, 5 given by RAM) and the Wave Beam
    (given by RAM, the wrong beam) leave it shut; the Ice Beam (by RAM: the Tallon's, round 3) opens it."""
    toward = "LEFT" if next(d for d in built_room(key).doors if d.to_room == to).side == "L" else "RIGHT"
    shots = [f"hold {toward}+X 2", "wait 30"] * 3
    return (chozo_door_shut(key, to) + [f"shot {IMG_12L}_{tag}_fechada.png"] + give_beams(0) + shots + chozo_door_shut(key, to)
            + poke16(0x7E09C6, 5) + poke16(0x7E09C8, 5) + ["hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001"] + shots
            + [f"expect {MISSILES} 0002", "hold SELECT 2", "wait 10", "poke 7E09D2 00", "wait 10"] + chozo_door_shut(key, to)
            + give_beams(WAVE_BEAM) + shots + chozo_door_shut(key, to)
            + give_beams(ICE_BEAM) + [f"hold {toward}+X 2", "wait 6", f"shot {IMG_12L}_{tag}_abrindo.png", "wait 120",
                                      f"hold {toward} 90", "wait 200", f"expect {ROOM_PTR} {room[to]}", f"expect {GAME_STATE} 0008"])


def chozo_route_e(m: dict, room: dict) -> list[str]:
    """specs/12l, chozo_regiao_e_rota: from the landing (a real game), to the Chozo West (door_teleport) and down the North
    elevator, regions A-D's rooms to the Furnace by door_teleport (their walks are 12f-12k's; the Furnace's enemies deleted
    by RAM: shortcut). Then, for real: Samus put by RAM on the B3 floor door's cap (shortcut: its dip in the floor), the
    Power Beam, missiles and the Wave Beam shot down at it leave her in the Furnace; with the Ice Beam (by RAM: the
    Tallon's, round 3) one shot down opens it and she drops into the East Furnace Access onto its platform; walking east off
    it, its R0 ice door shut, one ice shot, through into the Hall of the Elders' west balcony. With the Morph Ball and the
    Bombs (by RAM: the Tallon's, round 1) she walks east down the stair into the pit, ball, a bomb breaks the statue's block
    (Prime's bomb slots), she rolls into the chamber and drops through the B2 floor door into the Reflecting Pool Access,
    onto its platform, stands, walks off it and into the B0 hole: the Reflecting Pool, flooded, on the T2 platform. Without
    the Gravity Suit: a jump up the ceiling door, steering, takes her back into the Reflecting Pool Access (no softlock:
    the validator's water model, in the game), and down again; put by RAM on the pool's floor beside the step under the
    platform (shortcut: the drop is a walk off the platform) her jump does not get onto it; with the Gravity Suit (by RAM:
    the Tallon's, round 4) the same jump does; east under the platform to the R0 ice door, one ice shot, the Transport
    Access South, east into the Transport to Tallon South (Prime's link, a wall until now), onto its platform (shortcut),
    UP: the Tallon's Chozo South transport, area 0. Each room's explored bit and the pause map."""
    from chozo import layouts as L
    eq = MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT
    return (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
            + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12L}_rota_descendo.png")
            + chain_teleports(m, room, TO_FURNACE) + clear_room_enemies("chozo_furnace")
            # the B3 ice door, from above
            + put_samus(55, 29, 768, 256) + ["hold RIGHT 1", "wait 20", f"expect 7E0AFA {STAND_ON_B3:04X}",
                                               f"shot {IMG_12L}_rota_b3_fechada.png"]
            + SHOOT_DOWN * 2 + [f"expect {ROOM_PTR} {room['chozo_furnace']}", f"expect 7E0AFA {STAND_ON_B3:04X}"]
            + poke16(0x7E09C6, 5) + poke16(0x7E09C8, 5) + ["hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001"]
            + SHOOT_DOWN + [f"expect {MISSILES} 0004", "hold SELECT 2", "wait 10", "poke 7E09D2 00", "wait 10",
                            f"expect {ROOM_PTR} {room['chozo_furnace']}", f"expect 7E0AFA {STAND_ON_B3:04X}"]
            + give_beams(WAVE_BEAM) + SHOOT_DOWN * 2 + [f"expect {ROOM_PTR} {room['chozo_furnace']}", f"expect 7E0AFA {STAND_ON_B3:04X}"]
            + give_beams(ICE_BEAM) + SHOOT_DOWN + ["wait 300", f"expect {ROOM_PTR} {room['chozo_east_furnace_access']}",
                                                   f"expect {GAME_STATE} 0008", f"shot {IMG_12L}_rota_efa.png"]
            # the East Furnace Access' ice door (R0) into the Hall
            + ["hold RIGHT 60", "wait 30"] + chozo_door_shut("chozo_east_furnace_access", "chozo_hall_of_the_elders")
            + ["hold RIGHT+X 2", "wait 6", f"shot {IMG_12L}_rota_efa_abrindo.png", "wait 120", "hold RIGHT 90", "wait 200",
               f"expect {ROOM_PTR} {room['chozo_hall_of_the_elders']}", f"expect {GAME_STATE} 0008", f"shot {IMG_12L}_rota_hall.png"]
            # the statue: down the stair into the pit, the bomb slots' block, the chamber, down B2
            + poke16(0x7E09A2, eq) + poke16(0x7E09A4, eq) + ["hold RIGHT 300", "wait 60", f"expect 7E0AFA {29 * 16 - 21:04X}"]
            + ball_through_bomb_block_e("RIGHT", level_block("chozo_hall_of_the_elders", *L.HALL_B2_BOMB), "rota_estatua")[:-5]
            + ["wait 300", f"expect {ROOM_PTR} {room['chozo_reflecting_pool_access']}", f"expect {GAME_STATE} 0008",
               "hold UP 2", "wait 30", "hold UP 2", "wait 30", f"shot {IMG_12L}_rota_rpa.png",
               "hold RIGHT 40", "wait 40", "hold LEFT 60", "wait 300", f"expect {ROOM_PTR} {room['chozo_reflecting_pool']}",
               f"expect {GAME_STATE} 0008", f"expect 7E0AFA {POOL_PLATFORM_Y:04X}", f"shot {IMG_12L}_rota_pool.png"]
            # without the Gravity Suit: back up the ceiling door, and down again
            + ["hold A 40", "hold RIGHT 250", "wait 200", f"expect {ROOM_PTR} {room['chozo_reflecting_pool_access']}",
               f"expect {GAME_STATE} 0008", f"shot {IMG_12L}_rota_pool_volta.png",
               "hold LEFT 60", "wait 300", f"expect {ROOM_PTR} {room['chozo_reflecting_pool']}", f"expect 7E0AFA {POOL_PLATFORM_Y:04X}"]
            + put_samus(35, 14, 512, 0) + POOL_CLIMB + [f"expect 7E0AFA {POOL_FLOOR_Y:04X}", f"shot {IMG_12L}_rota_pool_sem_gravity.png"]
            + poke16(0x7E09A2, eq | GRAVITY_SUIT) + poke16(0x7E09A4, eq | GRAVITY_SUIT)
            + put_samus(35, 14, 512, 0) + POOL_CLIMB + [f"expect 7E0AFA {POOL_STEP_Y:04X}", f"shot {IMG_12L}_rota_pool_gravity.png"]
            + ["hold RIGHT 60"] + chozo_door_shut("chozo_reflecting_pool", "chozo_transport_access_south")
            + give_beams(ICE_BEAM) + ["hold RIGHT+X 2", "wait 6", f"shot {IMG_12L}_rota_pool_r0_abrindo.png", "wait 120",
                                      "hold RIGHT 120", "wait 200", f"expect {ROOM_PTR} {room['chozo_transport_access_south']}",
                                      f"expect {GAME_STATE} 0008"]
            + ["hold RIGHT 100", "hold RIGHT+X 2", "hold RIGHT 100", "wait 200", f"expect {ROOM_PTR} {room[SOUTH]}",
               f"expect {GAME_STATE} 0008", f"shot {IMG_12L}_rota_south.png"]
            + [explored_at(*screen) for screen in CHOZO_E_SCREENS]
            + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
            + pause_shows(CHOZO, CHOZO_E_SCREENS, "chozo_e") + [f"shot {IMG_12L}_rota_mapa.png", "hold START 10", "wait 200"]
            # facing west first: after the walk east she faced east and onto_platform's 4 + 4 frames ended 2 px off (measured)
            + ["hold LEFT 2", "wait 30"] + onto_platform(SOUTH) + ride_elevator(room, SOUTH, f"{IMG_12L}_rota_subindo.png")
            + [f"expect {ROOM_PTR} {room['tallon_transport_chozo_south']}", f"shot {IMG_12L}_rota_tallon_south.png"])


CHOZO_SAVE_3 = CHOZO.load_stations[3]                     # specs/12l: Save Station 3 (P59), load station 3 of area 1
BALCONY_Y = 10 * 16 - 21          # standing on a row-10 ledge


def chozo_red_bit(key: str, to: str) -> str:
    """`expectbit` of the door bit of key's red door to `to` (chozo/rooms.py: CHOZO_MISSILE_BIT0 + n)."""
    bit = next(d for d in built_room(key).doors if d.to_room == to).lock_bit
    return f"expectbit {0x7ED8B0 + bit // 8:06X} {1 << (bit % 8):02X}"


def east_down(m: dict, room: dict, tag: str) -> list[str]:
    """Shortcut (as elevador_chozo_east_e_south): from the landing to the Tallon's Chozo East transport by door_teleport
    (through Tunnel C: behind the ice door, round 4), onto its platform, DOWN: the Chozo's East transport."""
    return (poke16(0x7E0911, 0) + ["wait 2"] + door_teleport(m, "tallon_tunnel_c", "tallon_transport_chozo_east")
            + [f"expect {ROOM_PTR} {room['tallon_transport_chozo_east']}"] + onto_platform("tallon_transport_chozo_east")
            + ride_elevator(room, "tallon_transport_chozo_east", f"{IMG_12L}_{tag}_descendo.png"))


def east_to_save_3(room: dict, tag: str) -> list[str]:
    """From the Chozo East transport's platform, walking east: its R0 (Prime's link, a wall until now), the blue door
    shot, into Save Station 3."""
    return ["hold RIGHT 60", "hold RIGHT+X 2", "hold RIGHT 100", "wait 200", f"expect {ROOM_PTR} {room['chozo_save_station_3']}",
            f"expect {GAME_STATE} 0008", f"shot {IMG_12L}_{tag}_save3.png"]


def e_power_bomb_hut(n: int, start: int, block: tuple[int, int], tag: str) -> list[str]:
    """Chozo item n inside a hut whose west wall is power bomb blocks (the Crossway's, as the Main Plaza's tree): Samus put
    by RAM `start` blocks from the item, she walks east and stops against the wall, the Power Beam leaves it, ball, power
    bombs selected, X: the wall's blocks are air in the level in WRAM; she rolls in to the item (c_power_bomb_tunnel's
    steps)."""
    at = level_block(chozo_item(n).room, *block)
    pb = f"{0xC000 | 0x057:04X}"
    return (chozo_near(n, start) + ["hold RIGHT 60", "wait 30", f"expect {at:06X} {pb}", f"shot {IMG_12L}_itens_{tag}_bloco.png",
                                    "hold RIGHT+X 2", "wait 40", f"expect {at:06X} {pb}",
                                    "hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_POSE}",
                                    "hold SELECT 2", "wait 10", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0003",
                                    "hold X 2", "wait 80", f"shot {IMG_12L}_itens_{tag}_power_bomb.png", "wait 220",
                                    f"expect {at:06X} 00FF"]
            + b_take_and_close(n, f"{IMG_12L}_itens_{tag}_mensagem.png", "RIGHT", 120))


def chozo_items_e_test(m: dict, room: dict) -> list[str]:
    """specs/12l, chozo_regiao_e_itens: Prime's way into region E and its three items, each picked up by walking or rolling
    into it, A closing its box. Shortcuts, each noted: the rooms by door_teleport, the Tallon's items by RAM (the Morph Ball
    and the Bombs, round 1; the Wave Beam, round 1; the Space Jump's ledge: Samus put on the Furnace's east balcony; the
    Power Bomb, round 5), the Furnace's enemies deleted by RAM, Samus put by RAM near each item. The Furnace's R0: ball,
    through the Morph Ball tunnel (Prime's Morph Ball door) into its chamber, the blue door, the Crossway Access West; its
    wave door (the Power Beam leaves it, the Wave Beam opens it) into the Crossway; the missile in the hut of power bomb
    blocks (bit $D1); the Crossway's red floor door (missiles shot down: bit $BD) down into the Elder Hall Access, west into
    the Hall of the Elders (no ice: Prime's way); the E-tank in the "Down Launch" alcove (a bomb block, bit $D0). Then Save
    Station 3 (door_teleport; chozo_save_station_3 walks in from the East elevator), up its ceiling door into the flooded Reflecting Pool's west
    part (without the Gravity Suit), its red door to the Antechamber (bit $BF), the missile on the pedestal (Prime's Ice
    Beam, bit $D2); the Antechamber's ice door: the Power Beam, missiles and the Wave Beam leave it shut, the Ice Beam
    opens it, back into the Reflecting Pool."""
    from chozo import layouts as L
    etank, crossway, ante = (chozo_item_index(k) for k in ("chozo_hall_of_the_elders", "chozo_crossway", "chozo_antechamber"))
    eq = MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT
    return (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
            + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12L}_itens_descendo.png")
            + poke16(0x7E09A2, eq) + poke16(0x7E09A4, eq) + poke16(0x7E09C6, 5) + poke16(0x7E09C8, 5)
            + chain_teleports(m, room, TO_FURNACE) + clear_room_enemies("chozo_furnace")
            # the Furnace's Morph Ball door
            + put_samus(53, 10, 768, 0) + ["hold RIGHT 20", "wait 10", f"expect 7E0AFA {BALCONY_Y:04X}",
                                           f"shot {IMG_12L}_itens_furnace_tunel.png",
                                           "hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_POSE}",
                                           "hold RIGHT 60", "wait 10", "hold UP 2", "wait 30", "hold UP 2", "wait 30",
                                           f"expect {POSE} {STAND_POSE}", "hold RIGHT+X 2", "hold RIGHT 120", "wait 200",
                                           f"expect {ROOM_PTR} {room['chozo_crossway_access_west']}", f"expect {GAME_STATE} 0008"]
            # the Crossway Access West's wave door
            + ["hold RIGHT 150", "hold A+RIGHT 30", "hold RIGHT 150", "wait 30"]   # over the half-pipe's bowl
            + chozo_door_shut("chozo_crossway_access_west", "chozo_crossway")
            + ["hold RIGHT+X 2", "wait 30"] + chozo_door_shut("chozo_crossway_access_west", "chozo_crossway")
            + give_beams(WAVE_BEAM) + ["hold RIGHT+X 2", "wait 6", f"shot {IMG_12L}_itens_onda_abrindo.png", "wait 120",
                                       "hold RIGHT 90", "wait 200", f"expect {ROOM_PTR} {room['chozo_crossway']}",
                                       f"expect {GAME_STATE} 0008", f"shot {IMG_12L}_itens_crossway.png"]
            # the Crossway's missile (Prime's Missile Launcher)
            + poke16(0x7E09A2, eq) + poke16(0x7E09A4, eq) + poke16(0x7E09CE, 5) + poke16(0x7E09D0, 5)
            + e_power_bomb_hut(crossway, -10, (L.CROSSWAY_HUT[0], L.CROSSWAY_HUT[2]), "crossway")
            # down the red floor door into the Elder Hall Access, west into the Hall
            + ["hold LEFT 60", "wait 30", "hold UP 2", "wait 30", "hold UP 2", "wait 30", "poke 7E09D2 00", "wait 10"]
            + put_samus(23, 29, 256, 256) + ["hold RIGHT 1", "wait 20", f"expect 7E0AFA {29 * 16 - 21:04X}",
                                             f"shot {IMG_12L}_itens_b1_fechada.png", "hold SELECT 2", "wait 10",
                                             f"expect {HUD_ITEM} 0001"]
            + poke16(0x7E09C6, 5) + SHOOT_DOWN * 6   # one missile a jump: 5 open it (measured)
            + ["wait 300", f"expect {MISSILES} 0000", f"expect {ROOM_PTR} {room['chozo_elder_hall_access']}", f"expect {GAME_STATE} 0008",
                                chozo_red_bit("chozo_crossway", "chozo_elder_hall_access"), "poke 7E09D2 00", "wait 10",
                                f"shot {IMG_12L}_itens_eha.png", "hold LEFT 100", "hold LEFT+X 2", "hold LEFT 100", "wait 200",
                                f"expect {ROOM_PTR} {room['chozo_hall_of_the_elders']}", f"expect {GAME_STATE} 0008"]
            # the E-tank in the "Down Launch" alcove
            + b_bomb_tunnel(etank, 6, "LEFT", L.HALL_ETANK_BOMB, "hall", img=IMG_12L) + ["expect 7E09C4 00C7"]
            # Save Station 3 (door_teleport; walking in from the East elevator is chozo_save_station_3's), up its ceiling
            # door into the Reflecting Pool's west part, the Antechamber
            + chain_teleports(m, room, ["chozo_hall_of_the_elders", "chozo_reflecting_pool_access", "chozo_reflecting_pool",
                                        "chozo_save_station_3"])
            + chozo_climb(room, "chozo_save_station_3", "chozo_reflecting_pool", 40, "LEFT")
            + [f"expect 7E0AFA {BALCONY_Y:04X}", f"shot {IMG_12L}_itens_pool_oeste.png", "hold LEFT 120", "wait 30"]   # on the L0 ledge
            + red_door(room, "chozo_reflecting_pool", "LEFT", "chozo_antechamber", True)
            + chozo_pick_up(ante, f"{IMG_12L}_itens_antechamber_mensagem.png", start=1)
            + ["hold RIGHT 100", "wait 30"] + chozo_ice_door_holds(room, "chozo_antechamber", "chozo_reflecting_pool", "antechamber")
            + [chozo_item_bit(n) for n in (etank, crossway, ante)])


def chozo_save_3_test(m: dict, room: dict) -> list[str]:
    """specs/12l, chozo_save_station_3: as chozo_save_station_2, at Save Station 3, reached down the Tallon's East elevator
    (east_down: shortcut to the Tallon side) and walking east. Samus on the pedestal, a marker in the saved data (game hours
    9), YES: load station 3 of area 1, its used-station bit ($7ED8FA bit 3). Game over: the area-select screen picks area 1,
    station 3; continue: back on Save Station 3's pedestal, area 1, the marker loaded."""
    out = east_down(m, room, "save3") + east_to_save_3(room, "save3") + [f"poke {HEALTH} 63"] + poke16(0x7E09E0, 9)
    sx, sy = CHOZO_SAVE_3.x, CHOZO_SAVE_3.y
    for addr, v in ((0x7E0AF6, sx), (0x7E0B10, sx), (0x7E0AFA, sy), (0x7E0B14, sy)):
        out += poke16(addr, v)
    return (out + ["hold LEFT 1", "wait 180", f"shot {IMG_12L}_save3_pergunta.png", "hold A 2", "wait 300", "hold A 2", "wait 200",
                   f"expect {LOAD_STATION} 0003", f"expect {AREA} 0001", f"expectbit {USED_STATIONS_AREA1} 08",
                   f"expect {GAME_STATE} 0008", f"shot {IMG_12L}_save3_salvo.png",
                   "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
                   "hold A 2", "wait 300"]
            + area_select_shows_after(CHOZO.number, CHOZO_SAVE_3.index, (TALLON.number,), f"{IMG_12L}_save3_tela_de_area.png")
            + ["hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
            + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0001", f"expect {ROOM_PTR} {room[CHOZO_SAVE_3.room]}",
               f"expect {LOAD_STATION} 0003", f"expect {GAME_HOURS} 0009", f"expect 7E0AF6 {sx:04X}",
               f"shot {IMG_12L}_save3_continue.png"])


PLAZA_FEET = 26 * 16 - 21     # y of Samus standing on the Main Plaza's floor (row 26)
BALL_LEFT_POSE = "0041"       # the ball facing left (BALL_POSE, $1D, faces right)
PISTON_JUMP = ["hold UP 2", "wait 30", "hold UP 2", "wait 30", "hold RIGHT 14", "wait 20", "hold A 30", "hold RIGHT 300", "wait 60"]
CHAMBER_FEET = 29 * 16 - 21   # standing in the chamber under the plaza's dais, on the floor door's east ledge (row 29)


def tree_dead_slot() -> list[str]:
    """specs/12g2 (12f's ordering dropped: the Main Plaza's PLMs in list order, slot 39 the red door, 38 the one-way grey cap,
    37/36 the Space Jump ledges' missiles, 35 the tree's, 34 the E-tank): after the power bomb, with the other three taken,
    the dead PLM the blast left on the tree's block (header 0, its block index) sits in slot 37, above the live missile in
    slot 35 (measured, scratchpad s12h). Then a slot above the dead one frees without a PLM spawned first: shortcut, the red
    door's PLM ended by RAM (slot 39, as power_bomb_nao_apaga_item). Walking in, the touch's PLM takes slot 39; vanilla's
    lookup took the dead slot 37 and the missile stayed (emulator, the ROM without specs/13's fix and 12f's ordering); with
    specs/13's lookup she takes it. 12f's test alone did not show it: the touch's PLM took the dead slot itself."""
    it = chozo_item(2)
    index = 2 * (it.spot[1] * built_room(it.room).width * 16 + it.spot[0])
    return ([f"expect {plm_slot(PLM_HEADERS, 37)} 0000", f"expect {plm_slot(PLM_BLOCKS, 37)} {index:04X}",
             f"expect {plm_slot(PLM_HEADERS, 35)} {it.kind:04X}", f"expect {plm_slot(PLM_BLOCKS, 35)} {index:04X}"]
            + poke16(PLM_HEADERS + 2 * 39, 0))


def clear_room_enemies(key: str) -> list[str]:
    """specs/12h, shortcut: the enemies of room `key` (tools/chozo/enemies.py, in their slots: $7E0F78 + $40 n) deleted by RAM
    as the engine deletes one (properties bit $0200, DetermineWhichEnemiesToProcess $A0:8EB6: the slot's species becomes 0).
    For the tests of items and locks, not of fights (chozo_regiao_a_rota walks through them alive, chozo_inimigos checks them)."""
    spawns = CHOZO.enemies.get(key, [])
    # specs/12i: a spawn may fill two slots (the morph ball eye's socket): one per population entry
    props = [e[4] for s in spawns for e in s.entries()]
    out = [f"poke {0x7E0F78 + 0x40 * n + 0x0F:06X} {(p >> 8) | 0x02:02X}" for n, p in enumerate(props)]
    return out + ["wait 2"] + [f"expect {0x7E0F78 + 0x40 * n:06X} 0000" for n in range(len(props))]


# specs/12h, chozo_inimigos_vivos: each region-A room with enemies, entered through the door of the room before it, and where
# the photo looks (Samus standing on (x, floor), the camera at (cam_x, cam_y) px: tallon_look)
CHOZO_ENEMY_ROOMS = [
    ("chozo_ruins_entrance", NORTH, (5, 10, 0, 0)),
    ("chozo_main_plaza", "chozo_ruins_entrance", (40, 26, 1024, 256)),
    ("chozo_ruined_fountain_access", "chozo_main_plaza", (5, 10, 256, 0)),
    ("chozo_ruined_shrine_access", "chozo_main_plaza", (40, 10, 0, 0)),
    ("chozo_nursery_access", "chozo_main_plaza", (4, 10, 0, 0)),
    ("chozo_plaza_access", "chozo_main_plaza", (16, 13, 256, 0)),
    ("chozo_ruined_shrine", "chozo_ruined_shrine_access", (34, 13, 256, 0)),
    ("chozo_tower_of_light", "chozo_tower_of_light_access", (44, 10, 512, 0)),
    # specs/12i, region B (the Ruined Nursery through its side door from the North Atrium: no climb)
    ("chozo_eyon_tunnel", "chozo_nursery_access", (28, 10, 256, 0)),
    ("chozo_ruined_nursery", "chozo_north_atrium", (3, 10, 0, 0)),
    ("chozo_north_atrium", "chozo_ruined_nursery", (28, 10, 256, 0)),
    ("chozo_totem_access", "chozo_ruined_gallery", (3, 10, 0, 0)),
    ("chozo_hive_totem", "chozo_totem_access", (3, 10, 0, 0)),
    # specs/12j, region C (the Sun Tower through the Magmoor transport's door: its pocket under the shaft, no enemy there)
    ("chozo_ruined_fountain", "chozo_ruined_fountain_access", (5, 10, 0, 0)),
    ("chozo_arboretum_access", "chozo_ruined_fountain", (44, 10, 256, 0)),
    ("chozo_sun_tower", "chozo_transport_magmoor_north", (28, 42, 0, 256)),
    ("chozo_gathering_hall", "chozo_gathering_hall_access", (3, 10, 256, 0)),
    # specs/12k, region D (the Watery Hall through its L1 from the Watery Hall Access: the eye high over that door)
    ("chozo_watery_hall_access", "chozo_gathering_hall", (5, 10, 0, 0)),
    ("chozo_watery_hall", "chozo_watery_hall_access", (5, 26, 0, 256)),
    ("chozo_east_atrium", "chozo_gathering_hall", (5, 10, 0, 0)),
    ("chozo_energy_core_access", "chozo_east_atrium", (5, 10, 0, 0)),
    ("chozo_energy_core", "chozo_energy_core_access", (5, 13, 0, 0)),
    ("chozo_dynamo", "chozo_dynamo_access", (5, 10, 0, 0)),
    ("chozo_burn_dome", "chozo_burn_dome_access", (5, 13, 0, 0)),
    ("chozo_furnace", "chozo_west_furnace_access", (40, 28, 512, 256)),
]


def chozo_bosses_mod():
    from chozo import bosses
    return bosses


def enemies_alive(area, key: str) -> list[str]:
    """tallon_enemies_alive for any area: every enemy of the room in its slot ($7E0F78 + $40 n, in the table's order) with
    the species' full health, and no more."""
    rom = Rom.load(ROM)
    out = []
    spawns = area.enemies[key]
    arena = chozo_bosses_mod().arena_of(key)
    if arena is not None and arena.condition == chozo_bosses_mod().ITEM:   # specs/14d: its boss kinds come with the fight
        spawns = [e for e in spawns if not e.species.boss]
    species = slots(spawns)   # specs/12i: the morph ball eye fills two slots (its socket, then the eye)
    for n, ptr in enumerate(species):
        at = ENEMY_TABLE + ENEMY_SLOT * n
        out += [f"expect {at:06X} {ptr:04X}", f"expect {at + ENEMY_HEALTH:06X} {rom.u16(0xA00000 | ptr + 4):04X}"]
    return out + [f"expect {ENEMY_TABLE + ENEMY_SLOT * len(species):06X} 0000"]


def enter_through(m: dict, room: dict, frm: str, key: str) -> list[str]:
    """Shortcut: the door transition into `key` through `frm`'s door to it, started by RAM wherever Samus is (as door_teleport,
    without putting her at the door first: the door entry alone picks the room and where she arrives)."""
    i = next(i for i, d in enumerate(built_room(frm).doors) if d.to_room == key)
    return (poke16(0x7E099C, DOOR_HIT_TRANSITION) + poke16(0x7E078D, m[frm]["doors"][i] & 0xFFFF) + poke16(0x7E0998, 9)
            + ["wait 300", f"expect {ROOM_PTR} {room[key]}", f"expect {GAME_STATE} 0008"])


def chozo_enemies_test(m: dict, room: dict) -> list[str]:
    """specs/12h, chozo_inimigos_vivos: from the landing to the Chozo North (door_teleport through the Tallon's round-0 rooms,
    the elevator: shortcuts, as chozo_regiao_a_itens); then into each region-A room with enemies (enter_through, a
    shortcut): every enemy of tools/chozo/enemies.py in its slot of the WRAM table with the species' full health (the
    Sidehoppers, the frigate's crawler, Viola and Mella), standing still at the door 300 frames (the transition and 2 s more) she loses no energy; a photo
    of each room's enemies (tallon_look). (spec 15: this entry is by RAM, Samus not at the door: the door audit with real
    entries, every door, is entradas_de_porta_tallon / entradas_de_porta_chozo.)"""
    out = (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
           + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12H}_descendo.png") + give_beams(WAVE_BEAM))
    for key, frm, (x, floor, cx, cy) in CHOZO_ENEMY_ROOMS:
        # specs/12j: the energy refilled again 10 frames into the door's transition (the room left behind is frozen then: a
        # Mella of the Hive Totem's photo hit her as the transition started, and the next room's check took the blame)
        enter = enter_through(m, room, frm, key)
        enter[-3:-3] = ["wait 10", f"poke {HEALTH} 63"]
        out += [f"poke {HEALTH} 63"] + enter + enemies_alive(CHOZO, key) + [f"expect {HEALTH} 0063"]
        out += tallon_look(x, floor, cx, cy, f"{IMG_12H}_{key.removeprefix('chozo_')}.png")
    # the tower's Oculi (Viola) and Puffers (Mella) on the east platforms, a screen down
    return out + tallon_look(38, 25, 512, 256, f"{IMG_12H}_tower_of_light_plataformas.png")


IMG_12H = "build/tests/12h"


# spec 15: the door-entry audit. Every door entry of every room with enemies (Tallon, Chozo: the neighbour in the same area),
# a real one: Samus is put in the neighbour room (door_teleport into it: a shortcut), standing ENTRY_BLOCKS blocks inside its
# door to the room, shoots the door twice (a beam cap opens: every beam given; red doors' bits set by RAM) and walks into it:
# the door block's collision starts the transition. A floor or ceiling door, or a side door without floor at that spot:
# door_teleport (she is put at the door and the transition starts as the collision starts it). The energy is refilled while
# the transition runs; then standing still she must not lose energy in the first ENTRY_GRACE frames after she arrives (the
# 12h promise, "the transition and 2 s more", now measured from a real entry): enemies that come to a still Samus reach her
# later (they are recorded in the spec, scratchpad s14b/a2_*.out, 600 frames, two entries, four timings). The Ruined Shrine
# (the case spec 15 fixed) is watched ENTRY_LONG frames. ENTRY_EXCEPTIONS: recorded, not checked.
ENTRY_BLOCKS, ENTRY_GRACE, ENTRY_LONG, ENTRY_STEP = 3, 120, 600, 10
ENTRY_WATCH_LONG = {"chozo_ruined_shrine"}
ENTRY_EXCEPTIONS = {
    ("tallon_elevator_beta", 0): "o pirata atira na Samus parada (épico 10: atirando logo ela o mata antes)",
    ("tallon_elevator_beta", 1): "o pirata atira na Samus parada (épico 10: atirando logo ela o mata antes)",
}


def entry_walk_in(area, n_key: str, t_key: str) -> list[str] | None:
    """spec 15: Samus standing ENTRY_BLOCKS blocks inside n_key's side door to t_key, two shots at it, a walk into it (None
    if the door is not a side door or there is no floor there)."""
    from smlib import reach as reach_model
    r = area.by_key()[n_key]
    d = next(d for d in r.doors if d.to_room == t_key)
    if d.side not in "LR":
        return None
    wb = r.width * 16
    x = 2 + ENTRY_BLOCKS if d.side == "L" else wb - 3 - ENTRY_BLOCKS
    feet = d.screen * 16 + 9
    l1, _ = r.level().build_blocks()
    if not reach_model.Grid([w >> 12 for w in l1], wb, r.height * 16).stands(x, feet):
        return None
    place = []
    for addr, v in ((0x7E0AF6, x * 16 + 8), (0x7E0B10, x * 16 + 8), (0x7E0AFA, (feet + 1) * 16 - 21), (0x7E0B14, (feet + 1) * 16 - 21)):
        place += poke16(addr, v)
    camera = poke16(0x7E0911, 0 if d.side == "L" else (r.width - 1) * 256) + poke16(0x7E0915, min(d.screen * 256, camera_bottom(r)))
    toward = "LEFT" if d.side == "L" else "RIGHT"
    return (place + ["wait 30"] + place + camera + ["wait 20", f"hold {toward}+X 2", "wait 20", f"hold {toward}+X 2", "wait 40",
            f"hold {toward} 50", f"poke {HEALTH} 63"])


def build_arena_door(key: str, d) -> bool:
    """specs/18k: door `d` of room `key` is a boss door whose cap changes with its arena's state (tools/build.py
    arena_door_alive_cap: shut from the room's load until the win)."""
    import build
    return build.arena_door_alive_cap(key, d) is not None


def entry_audit(m: dict, room: dict, area) -> list[str]:
    """spec 15, entradas_de_porta_<area>: from a state saved once in the area, each entry (entry_walk_in, else door_teleport),
    then the energy, the room and the game state every ENTRY_STEP frames (check_entries reads them)."""
    state = f"build/tests/entradas_{area.key}.state"
    out = [f"save {state}"]
    by = area.by_key()
    for key in area.enemies:
        for i, d in enumerate(by[key].doors):
            if d.to_room not in by or (key, i) in ENTRY_EXCEPTIONS:
                continue
            n = by[d.to_room]
            frm = next((e.to_room for e in n.doors if e.to_room in by and e.to_room != key), key)
            items = (VARIA_EQUIPMENT if (by[key].heat or n.heat) else 0) | (GRAVITY_SUIT if (by[key].water or n.water) else 0)
            # specs/18k: walking out of an arena whose boss door shuts until the win (the Thardus' cave into its tunnels): the
            # arena won by RAM first (its bit, a shortcut: its dead state's door is the one the walk opens)
            arena = chozo_bosses_mod().arena_of(n.key)
            won = ([f"poke {0x7ED828 + area.number:06X} {arena.bit:02X}"]
                   if arena is not None and any(e.to_room == key and e.lock == "boss" and build_arena_door(n.key, e) for e in n.doors)
                   else [])
            out += ([f"load {state}"] + poke16(0x7E09A2, items) + poke16(0x7E09A4, items) + give_beams(WAVE_BEAM | ICE_BEAM | PLASMA_BEAM)
                    + [f"poke {0x7ED8B0 + k:06X} FF" for k in range(0x20)] + won
                    + door_teleport(m, frm, d.to_room) + [f"expect {ROOM_PTR} {room[d.to_room]}", f"poke {HEALTH} 63"])
            walk = entry_walk_in(area, d.to_room, key)
            out += walk if walk else door_teleport(m, d.to_room, key)[:-1] + [f"poke {HEALTH} 63"]
            watch = 250 + (ENTRY_LONG if key in ENTRY_WATCH_LONG else ENTRY_GRACE)
            out += ["peekw 7E0000"]   # check_entries splits the output here, one block per entry
            out += [f"wait {ENTRY_STEP}", f"peekw {HEALTH}", f"peekw {ROOM_PTR}", f"peekw {GAME_STATE}"] * (watch // ENTRY_STEP)
    return out


def check_entries(area):
    """spec 15: for each entry entry_audit made (in its order), the frame Samus arrives (the room is the entry's, game state
    8) and, from there, the first energy lost: before ENTRY_GRACE frames (ENTRY_LONG in ENTRY_WATCH_LONG) = a failure; also
    a failure: the entry does not end in its room."""
    def check(stdout: str) -> list[str]:
        by = area.by_key()
        entries = [(key, i) for key in area.enemies for i, d in enumerate(by[key].doors)
                   if d.to_room in by and (key, i) not in ENTRY_EXCEPTIONS]
        manifest = json.loads((ROOT / "build/manifest.json").read_text())
        blocks = stdout.split("7E0000 = ")[1:]
        if len(blocks) != len(entries):
            return [f"FAIL entradas: {len(blocks)} medidas, {len(entries)} esperadas"]
        out = []
        for (key, i), blk in zip(entries, blocks):
            vals = [int(v, 16) for v in re.findall(r"7E(?:09C2|079B|0998) = ([0-9A-F]{4})", blk)]
            rows = [vals[k:k + 3] for k in range(0, len(vals) - 2, 3)]
            want = manifest[key]["header"] & 0xFFFF
            arrive = next((k for k, (_, rm, gs) in enumerate(rows) if rm == want and gs == 8), None)
            tag = f"{key} porta {i} ({by[key].doors[i].side}{by[key].doors[i].screen})"
            if arrive is None:
                out.append(f"FAIL entrada {tag}: não chegou à sala")
                continue
            limit = (ENTRY_LONG if key in ENTRY_WATCH_LONG else ENTRY_GRACE) // ENTRY_STEP
            hit = next((k - arrive for k in range(arrive, min(len(rows), arrive + limit)) if rows[k][0] < rows[arrive][0]), None)
            if hit is not None:
                out.append(f"FAIL entrada {tag}: perdeu energia {hit * ENTRY_STEP} quadros depois de chegar "
                           f"(o limite é {limit * ENTRY_STEP})")
        return out
    return check


# specs/14a, chozo_plated_beetle: the Plated Beetle's fight (the big Sidehopper's copy, $A0:F83F: 320 health, 40 a touch) with the
# 3 small Sidehoppers, Power Beam only, no energy refilled, no RAM. The moves (~24 frames each) were found by a beam search in
# the emulator (scratchpad s14a/scripts/beam.py: from the shrine's entry, the best few sequences kept by energy, the boss'
# health and how far west she got); measured: from the door_teleport into the shrine it wins the same with 0-17 frames waited
# in the access before it (and loses from 18 on: the entry differs, s14a/robust.py), so the start is fixed as below.
BEETLE_MOVES = {
    "s": ["hold X 2", "wait 10", "hold X 2", "wait 10"],                  # two shots, standing
    "c": ["hold DOWN+X 2", "wait 10", "hold DOWN+X 2", "wait 10"],        # two shots, crouching
    "u": ["hold A+X 2", "hold A 12", "hold X 2", "wait 8"],               # a jump straight up, two shots
    "L": ["hold LEFT 12", "hold LEFT+X 2", "wait 10"],                    # a step west and a shot
    "J": ["hold LEFT+A 20", "hold LEFT+X 2", "wait 2"],                   # a jump west and a shot
    "H": ["hold LEFT+A+X 2", "hold LEFT+A 16", "hold X 2", "wait 4"],     # a jump west shooting
}
# spec 15 / specs/14b: searched again (s14b/scripts/beetle_beam.py, the same search) after the small ones moved to the bowl's
# middle screen and the shrine got the mini-boss song (14a's was "LLLLLLLuHLsLsusLLJcJHLsL", 39 left, 2 kills)
BEETLE_FIGHT = "LLLLssLLLJsHuHJcLuLussH"
BEETLE_ENERGY_LEFT = 44   # measured: the energy she ends with (99: the small Sidehoppers' and the beetle's touches)
BEETLE_KILLS = 4          # measured: the beetle and the 3 small ones
IMG_14A = "build/tests/14a"


# specs/14b, chozo_hive_mecha: the Hive Mecha (2 bug hives, Kago $A0:E7FF, under the Hive Totem's combs, and its 3 wasps,
# Mella) fought from the L0 entry (the round-0 way) with the Power Beam only, nothing refilled, no RAM. Moves of ~24 frames
# found by a beam search in the emulator (scratchpad s14b/scripts/hive_beam.py: kills, the hives' hits left, energy and the
# distance to the nearest enemy; then hive_beam2.py to the totem's missile); they hold for this exact entry (as 14a's).
HIVE_MOVES = {
    "R": ["hold RIGHT 12", "hold RIGHT+X 2", "wait 10"],                  # a step east and a shot
    "L": ["hold LEFT 12", "hold LEFT+X 2", "wait 10"],                    # a step west and a shot
    "U": ["hold UP 6", "hold UP+X 2", "hold UP 4", "wait 12"],            # a shot straight up (UP held first: else it fires ahead)
    "F": ["hold X 2", "wait 3"] * 5,                                      # 5 quick shots ahead
    "H": ["hold RIGHT 2"] + ["hold X 2", "wait 3"] * 5,                   # face east, 5 quick shots
    "G": ["hold LEFT 2"] + ["hold X 2", "wait 3"] * 5,                    # face west, 5 quick shots
    "c": ["hold DOWN 2"] + ["hold DOWN+X 2", "wait 3"] * 5,               # crouch, 5 quick shots
    "J": ["hold RIGHT+A 20", "hold RIGHT+X 2", "wait 2"],                 # a jump east and a shot
    "K": ["hold LEFT+A 20", "hold LEFT+X 2", "wait 2"],                   # a jump west and a shot
    "T": ["hold A+RIGHT 40", "hold RIGHT 20"],                            # a full jump east (onto the totem)
    "Y": ["hold A+LEFT 40", "hold LEFT 20"],                              # a full jump west
    "l": ["hold LEFT 24"],                                                # a walk west
    "a": ["hold A+LEFT 24"],                                              # a short jump west
}
HIVE_FIGHT = "JHJHTUHLcHGHGFFTUYcYTJRLRcGTRTFGKTTRUUUUU"   # 41 moves: the 5 dead (the east hive last), the missile spawned
HIVE_PICKUP = "laYYY"                                     # from under the east hive up the totem into the missile
HIVE_ENERGY_AT_WIN = 60      # measured: the wasps' and the bugs' hits, a drop picked up on the way; the same after the pickup
IMG_14B = "build/tests/14b"


def hive_mecha_test(m: dict, room: dict) -> list[str]:
    """specs/14b, chozo_hive_mecha: from the landing to the Chozo North (door_teleport through the Tallon's round-0 rooms, the
    North elevator: shortcuts, as chozo_plated_beetle), door_teleport round region B into the Hive Totem by its L0 (from the
    Totem Access: the round-0 way); Samus with the Power Beam only (round 0: no missile), 99 energy. The arena alive: the 3
    wasps and the 2 hives in their slots, the mini-boss music (song set $2A), the totem's missile NOT loaded (PLM slot 38,
    where the room's list puts it after the red door's cap in 39, empty), the boss bit $08 of area 1 off. HIVE_FIGHT, nothing refilled: all 5 die
    ($0E50 = 5), the arena routine sets the bit, stops the music and spawns the missile (PLM $EEDB in slot 38, block (23, 8));
    HIVE_PICKUP walks into it (bit $C2, 5 missiles). Out to the Totem Access and back (door_teleport): the dead state (the 3
    wasps, no hive, the area's music $1B/$05), the missile gone (taken), the bit on. Then to Save Station 1 (door_teleport
    round the loop), saved, game over, continue: the bit and the item still on; back into the Hive Totem: dead."""
    totem = chozo_item_index("chozo_hive_totem")
    spawns = CHOZO.enemies["chozo_hive_totem"]
    species = slots(spawns)
    hives = [n for n, sp in enumerate(species) if sp == SPECIES["hive"].ptr]
    wasps = [n for n, sp in enumerate(species) if sp != SPECIES["hive"].ptr]
    block = 2 * (8 * built_room("chozo_hive_totem").width * 16 + 23)
    music = lambda song, track: [f"expect 7E07F3 {song:04X}", f"expect 7E07F5 {track:04X}"]   # noqa: E731
    dead_room = ([f"expect {ENEMY_TABLE + ENEMY_SLOT * n:06X} {species[n]:04X}" for n in wasps]
                 + [f"expect {ENEMY_TABLE + ENEMY_SLOT * len(wasps):06X} 0000", "expectbit 7ED829 08"] + music(*CHOZO.music))
    out = (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
           + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_14B}_descendo.png")
           + chain_teleports(m, room, [NORTH, "chozo_ruins_entrance", "chozo_main_plaza", "chozo_plaza_access", "chozo_vault"])
           + rise_through(m, room, "chozo_vault", "chozo_vault_access", 0, "LEFT")
           + chain_teleports(m, room, ["chozo_vault_access", "chozo_transport_magmoor_north", "chozo_transport_access_north",
                                       "chozo_hive_totem", "chozo_totem_access", "chozo_hive_totem"])
           + [f"poke {HEALTH} 63", f"expect {MISSILES} 0000", f"expect {MAX_MISSILES} 0000", "expect 7ED829 0000"]
           + enemies_alive(CHOZO, "chozo_hive_totem") + music(0x2A, 0x05)
           + [f"expect {plm_slot(PLM_HEADERS, 38)} 0000", f"expect {plm_slot(PLM_HEADERS, 37)} 0000",   # no missile loaded
              f"shot {IMG_14B}_entrada.png"])
    for i, move in enumerate(HIVE_FIGHT):
        out += HIVE_MOVES[move]
        if i in (5, 20, 35):
            out += [f"shot {IMG_14B}_luta_{i:02d}.png"]
        if i == 35:   # 4 dead (measured), the east hive alive: no bit yet, no missile yet
            out += ["expect 7E0E50 0004", f"expect {ENEMY_TABLE + ENEMY_SLOT * hives[-1]:06X} {SPECIES['hive'].ptr:04X}",
                    "expect 7ED829 0000", f"expect {plm_slot(PLM_HEADERS, 38)} 0000"]
    out += ([f"expect {KILLS} 0005"] + [f"expect {ENEMY_TABLE + ENEMY_SLOT * n:06X} 0000" for n in range(len(species))]
            + ["expectbit 7ED829 08", f"expect {plm_slot(PLM_HEADERS, 38)} EEDB", f"expect {plm_slot(PLM_BLOCKS, 38)} {block:04X}",
               f"expect {HEALTH} {HIVE_ENERGY_AT_WIN:04X}", f"shot {IMG_14B}_missil_aparece.png"])
    for i, move in enumerate(HIVE_PICKUP):
        out += HIVE_MOVES[move] + ([f"shot {IMG_14B}_subindo.png"] if i == 2 else [])
    out += ["wait 120", f"shot {IMG_14B}_mensagem.png", "wait 300", "hold A 2", "wait 120", chozo_item_bit(totem),
            f"expect {MISSILES} 0005", f"expect {MAX_MISSILES} 0005", f"expect {GAME_STATE} 0008", "expect 7E07F5 0000",
            f"expect {HEALTH} {HIVE_ENERGY_AT_WIN:04X}"]
    out += (chain_teleports(m, room, ["chozo_hive_totem", "chozo_totem_access", "chozo_hive_totem"]) + ["wait 60"] + dead_room
            + [f"expect {plm_slot(PLM_HEADERS, 38)} 0000", f"expect {plm_slot(PLM_HEADERS, 37)} 0000", chozo_item_bit(totem),
               f"expect {MAX_MISSILES} 0005"]
            + tallon_look(23, 9, 256, 0, f"{IMG_14B}_morto.png"))
    # saved at Save Station 1 (as chozo_save_e_continue), game over, continue
    out += (chain_teleports(m, room, ["chozo_hive_totem", "chozo_totem_access", "chozo_ruined_gallery", "chozo_north_atrium",
                                      "chozo_ruined_nursery", "chozo_save_station_1"]) + [f"poke {HEALTH} 63"])
    for addr, v in ((0x7E0AF6, CHOZO_SAVE.x), (0x7E0B10, CHOZO_SAVE.x), (0x7E0AFA, CHOZO_SAVE.y), (0x7E0B14, CHOZO_SAVE.y)):
        out += poke16(addr, v)
    out += ["wait 180", "hold A 2", "wait 300", "hold A 2", "wait 200", f"expect {LOAD_STATION} 0001", f"expect {AREA} 0001",
            "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}", "hold A 2", "wait 300",
            "hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
    out += ([f"expect {GAME_STATE} 0008", f"expect {ROOM_PTR} {room[CHOZO_SAVE.room]}", "expectbit 7ED829 08", chozo_item_bit(totem)]
            + chain_teleports(m, room, ["chozo_save_station_1", "chozo_ruined_nursery", "chozo_north_atrium", "chozo_ruined_gallery",
                                        "chozo_totem_access", "chozo_hive_totem"]) + ["wait 60"] + dead_room
            + [f"expect {plm_slot(PLM_HEADERS, 38)} 0000", f"shot {IMG_14B}_depois_do_continue.png"])
    return out


# specs/14c, chozo_flaahgra: Flaahgra (the Spore Spawn, $A0:DF3F, in the Sunchamber's pit) fought with missiles from the
# R2 entry (door_teleport from the Sunchamber Access, round 2's way in), nothing refilled, no RAM in the fight. Its shot AI
# takes only missiles, bombs and charged shots, and only on its core: the core's hitbox ($A5:EF4F's, SporeSpawn_Shot) is
# exposed between the shells only while it stops and shakes (instruction lists $E719-$E741), ~180 frames a loop; a missile
# does 100 (10 to kill it). From the hall's floor at x 300 a missile shot west at the top of a jump with A held k frames
# flies at y 649 (k 1) ... 586 (k 16) ... 553 (k 28): the core's height (its y +-24). The jumps were found by a closed loop
# in the emulator (scratchpad s14c/scripts/policy2.py: fire when it stops, k for its y) and recorded: they hold for this
# exact entry (as 14a's and 14b's), (frames waited, k) each.
FLAAHGRA_HALL = ["hold LEFT 60", "hold LEFT+A 25", "hold LEFT 80", "hold LEFT+A 25", "hold LEFT 110", "wait 20", "hold LEFT 2",
                 "wait 10", "hold SELECT 2", "wait 4", "hold LEFT 30", "wait 20"]   # over the two bomb-slot pits to x 300
FLAAHGRA_FIGHT = [(712, 16), (0, 16), (716, 8), (0, 20), (712, 16), (0, 16), (716, 8), (0, 20), (712, 16), (0, 16), (716, 8),
                  (0, 8), (712, 1), (0, 8), (700, 8), (0, 8), (712, 1), (768, 8)]
FLAAHGRA_MISSILES = 40       # round 2's capacity (validate.round_missiles), by RAM: the test starts at the room
FLAAHGRA_MISSILES_LEFT = 22  # measured: 18 shot, 10 hits
FLAAHGRA_ENERGY_AT_WIN = 99  # measured: at x 300 nothing reaches her (the spores fall over x 32-224, its touch to x 235)
IMG_14C = "build/tests/14c"


def flaahgra_jump(k: int) -> list[str]:
    """A jump with A held k frames, a missile west at its top, the landing (70 frames)."""
    return [f"hold A {k}", "hold A+LEFT+X 1", f"wait {69 - k}"]


def sandstone_line(line: int) -> list[str]:
    """specs/14c: palette line `line` of the BG in WRAM ($7EC000) = the ruins' tileset palette as the build writes it (colours
    1-15): the Spore Spawn's death repaints lines 4 and 7 from its tables, now the ruins' own (bosses.spore_spawn_patches)."""
    import build as _build
    from smlib.rom import Rom as _Rom
    pal = _build.ruins_palette(_Rom.load(ROOT / "base/sm_fix.sfc"))
    return [f"expect {0x7EC000 + 2 * (16 * line + i):06X} {int.from_bytes(pal[32 * line + 2 * i:32 * line + 2 * i + 2], 'little'):04X}"
            for i in range(1, 16)]


def flaahgra_test(m: dict, room: dict) -> list[str]:
    """specs/14c, chozo_flaahgra: from the landing down the North elevator (chozo_down), door_teleport through region C (the
    Morph Ball and the Bombs by RAM) to the Sunchamber Lobby, up its ceiling door (rise_through), into the Sunchamber by its
    R2 (door_teleport from the Sunchamber Access); missiles FLAAHGRA_MISSILES by RAM (round 2's capacity), 99 energy, no
    Charge Beam. The arena alive: the Spore Spawn in slot 0 with 960, the mini-boss song, the bits $02/$40 of area 1 off,
    the grey door's PLM (type 1) on the L0 (PLM slot 39), the Varia Suit not loaded; the BG's lines 4 and 7 the ruins'.
    FLAAHGRA_HALL walks over the bomb-slot pits; FLAAHGRA_FIGHT (no RAM): two jumps in, one hit (860), no bit; at the end
    its health 0, the bits $02 (its own) and $40 (the arena routine's), the Varia Suit spawned at (8, 43), she has
    FLAAHGRA_ENERGY_AT_WIN and FLAAHGRA_MISSILES_LEFT; the music stopped; after the death's fade lines 4 and 7 still the
    ruins' (not brown). West into the pit against its wall, east into the Varia Suit (its bit, $09A2 bit 0); the arena's
    zigzag climbed (SUNCHAMBER_TO_STA), a shot at the grey door (opened by the bit $02) and through it into the Sun Tower
    Access. Back (door_teleport): the dead state (no boss, the area's song, no Varia: taken), the bits on, the colours. Saved
    at Save Station 2, game over, continue: the bits and the item on; back in the Sunchamber: dead."""
    varia = chozo_item_index("chozo_sunchamber")
    vit = chozo_item(varia)
    block = 2 * (vit.spot[1] * built_room("chozo_sunchamber").width * 16 + vit.spot[0])
    music = lambda song, track: [f"expect 7E07F3 {song:04X}", f"expect 7E07F5 {track:04X}"]   # noqa: E731
    colours = sandstone_line(4) + sandstone_line(7)
    eq = MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT
    dead_room = ([f"expect {ENEMY_TABLE:06X} 0000", "expectbit 7ED829 42", chozo_item_bit(varia)] + music(*CHOZO.music)
                 + [f"expect {plm_slot(PLM_HEADERS, 38)} 0000", f"expect {plm_slot(PLM_HEADERS, 37)} 0000"] + colours)
    out = (chozo_down(m, room, "flaahgra") + poke16(0x7E09A2, eq) + poke16(0x7E09A4, eq)
           + chain_teleports(m, room, [NORTH, "chozo_ruins_entrance", "chozo_main_plaza", FOUNTAIN, "chozo_ruined_fountain",
                                       "chozo_arboretum_access", "chozo_arboretum", "chozo_sunchamber_lobby"])
           + rise_through(m, room, "chozo_sunchamber_lobby", "chozo_sunchamber_access", 0, "LEFT")
           + chain_teleports(m, room, ["chozo_sunchamber_access", "chozo_sunchamber"])
           + poke16(0x7E09C8, FLAAHGRA_MISSILES) + poke16(0x7E09C6, FLAAHGRA_MISSILES) + [f"poke {HEALTH} 63", "wait 2"]
           + [f"expect {ENEMY_TABLE:06X} {SPECIES['flaahgra'].ptr:04X}", f"expect {ENEMY_TABLE + ENEMY_HEALTH:06X} 03C0",
              "expect 7ED829 0000"] + music(0x2A, 0x05)
           + [f"expect {plm_slot(PLM_HEADERS, 39)} C848", f"expect {plm_slot(PLM_HEADERS, 38)} 0000",
              f"expect {plm_slot(PLM_HEADERS, 37)} 0000"] + colours
           + FLAAHGRA_HALL + ["expect 7E0AF6 012C", f"expect 7E0AFA {42 * 16 - 21:04X}", f"shot {IMG_14C}_entrada.png"])
    for i, (wait, k) in enumerate(FLAAHGRA_FIGHT):
        out += [f"wait {wait}"] * bool(wait) + flaahgra_jump(k)
        if i == 0:
            out += [f"shot {IMG_14C}_luta.png"]
        if i == 1:   # one hit (measured), no bit yet, no Varia yet
            out += [f"expect {ENEMY_TABLE + ENEMY_HEALTH:06X} 035C", "expect 7ED829 0000", f"expect {plm_slot(PLM_HEADERS, 37)} 0000"]
        if i == 12:
            out += [f"shot {IMG_14C}_luta_2.png"]
    out += ([f"expect {ENEMY_TABLE + ENEMY_HEALTH:06X} 0000", "expectbit 7ED829 42", f"expect {plm_slot(PLM_HEADERS, 37)} EF07",
             f"expect {plm_slot(PLM_BLOCKS, 37)} {block:04X}", f"expect {HEALTH} {FLAAHGRA_ENERGY_AT_WIN:04X}",
             f"expect {MISSILES} {FLAAHGRA_MISSILES_LEFT:04X}", "wait 60", f"shot {IMG_14C}_morte.png", "expect 7E07F5 0000",
             "wait 900", f"shot {IMG_14C}_depois_da_morte.png"] + colours)
    out += (["hold SELECT 2", "wait 10", "hold LEFT 120", "wait 120", f"shot {IMG_14C}_varia_mensagem.png", "wait 300", "hold A 2", "wait 200", chozo_item_bit(varia),
               f"expectbit 7E09A2 {VARIA_EQUIPMENT:02X}", f"expectbit 7E09A4 {VARIA_EQUIPMENT:02X}", f"expect {GAME_STATE} 0008"]
            + SUNCHAMBER_TO_STA + [f"shot {IMG_14C}_alto.png", "hold LEFT+X 2", "hold LEFT 100", "wait 320",
                                   f"expect {ROOM_PTR} {room['chozo_sun_tower_access']}", f"expect {GAME_STATE} 0008"])
    out += (chain_teleports(m, room, ["chozo_sun_tower_access", "chozo_sunchamber"]) + ["wait 60"] + dead_room
            + [f"shot {IMG_14C}_morto.png"])
    # saved at Save Station 2 (as chozo_save_station_2), game over, continue
    out += (chain_teleports(m, room, ["chozo_sunchamber", "chozo_sunchamber_access", "chozo_sunchamber_lobby", "chozo_arboretum",
                                      "chozo_gathering_hall_access", "chozo_gathering_hall", "chozo_save_station_2"])
            + [f"poke {HEALTH} 63"])
    for addr, v in ((0x7E0AF6, CHOZO_SAVE_2.x), (0x7E0B10, CHOZO_SAVE_2.x), (0x7E0AFA, CHOZO_SAVE_2.y), (0x7E0B14, CHOZO_SAVE_2.y)):
        out += poke16(addr, v)
    out += ["hold LEFT 1", "wait 180", "hold A 2", "wait 300", "hold A 2", "wait 200", f"expect {LOAD_STATION} 0002",
            f"expect {AREA} 0001", "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
            "hold A 2", "wait 300", "hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
    out += ([f"expect {GAME_STATE} 0008", f"expect {ROOM_PTR} {room[CHOZO_SAVE_2.room]}", "expectbit 7ED829 42",
             chozo_item_bit(varia)]
            + chain_teleports(m, room, ["chozo_save_station_2", "chozo_gathering_hall", "chozo_gathering_hall_access",
                                        "chozo_arboretum", "chozo_sunchamber_lobby"])
            + rise_through(m, room, "chozo_sunchamber_lobby", "chozo_sunchamber_access", 0, "LEFT")
            + chain_teleports(m, room, ["chozo_sunchamber_access", "chozo_sunchamber"]) + ["wait 60"] + dead_room
            + [f"shot {IMG_14C}_depois_do_continue.png"])
    return out


# specs/14d, chozo_incinerator_drone: the Incinerator Drone's arena (the Burn Dome, an ITEM arena of tools/chozo/bosses.py):
# taking the stand's missile (bit $CC) shuts the L0 door (a grey cap of type 3, spawned), spawns 2 hives (the Kago copy) and 2
# wasps, starts the mini-boss song; all dead (with the Mella of before), the door opens. Moves of HIVE_MOVES found by a beam
# search in the emulator from the box closed on the stand (scratchpad s14d/scripts/drone_beam.py); they hold for this exact
# entry and this exact prefix (the death and the continue before it included), as 14a-14c's.
IMG_14D = "build/tests/14d"
DRONE_APPROACH = sum((["hold RIGHT+X 2", "hold RIGHT 10"] + (["hold RIGHT+A 20"] if i % 2 == 0 else []) for i in range(10)), [])
DRONE_MOVES = {**HIVE_MOVES, "w": ["wait 24"]}               # 14b's moves and a wait
DRONE_FIGHT = "YFJRUGaKLLaJJTTwJHJJaUUTFGKLU"   # 29 moves: the 5 dead (the east hive last)
DRONE_ENERGY_AT_WIN = 57     # measured: the wasps' and the bugs' hits, drops picked up on the way
DRONE_EXIT = ["hold LEFT+A 30", "hold LEFT+X 2", "hold LEFT 18"] * 10   # hops west over the pool and the stand onto the ledge
# from the stand: west off it along the floor to the L0 ledge's foot, a jump onto the ledge, against the grey cap
DRONE_TO_THE_DOOR = ["hold LEFT 260", "hold LEFT+A 25", "hold LEFT 40"]
GREY_CAP_SLOT = 37           # the PLM slot the routine's grey cap takes (the first free from the top: the stand's missile's)


def drone_box() -> list[str]:
    """After DRONE_APPROACH: the missile's box (MISSILE), closed with A; 40 frames on, the routine has started the fight."""
    return ["wait 120", "wait 300", "hold A 2", "wait 40"]


def incinerator_drone_test(m: dict, room: dict) -> list[str]:
    """specs/14d, chozo_incinerator_drone: from the landing down the North elevator (door_teleport through the Tallon's round-0
    rooms), the Morph Ball by RAM (the Tallon's, round 0: the Burn Dome Access' tunnel), door_teleport to Save Station 2 and a
    save there; door_teleport through region D to the Energy Core, up its ceiling door (rise_through) into the Burn Dome Access,
    into the Burn Dome by its L0 (round 1's way in); Samus with the Power Beam only, 99 energy. The arena alive before the
    fight: the Mella in slot 0 alone, the boss kinds not there, the quota $0E52 = 0, the song set $2A with track 3, the bit
    $10 off, no grey cap. DRONE_APPROACH (no refill) onto the stand into the missile: its bit $CC; the box closed: the quota
    5, track 5, the 2 hives and 2 wasps spawned in slots 1-4, the grey cap ($C848, type 3) on the L0 in PLM slot 37. To the
    door, a shot, pushing into it: still in the Burn Dome (shut). Energy 0 by RAM: game over, continue at Save Station 2 (the
    save before the fight): the item's bit and the boss bit off, no missile: the fight is reset. Back in the Burn Dome (the
    same way): alive again, the missile on its stand; DRONE_APPROACH and the box again, then DRONE_FIGHT (no RAM): all 5 dead,
    the bit $10, the song stopped, the cap opened by its own count; DRONE_EXIT through the door into the Burn Dome Access. Back
    (door_teleport): the dead state (the Mella only, the area's song, no cap, no missile). Saved at Save Station 2, game over,
    continue: the bits on; back in the Burn Dome: dead."""
    stand = chozo_item_index("chozo_burn_dome", 0xEEDB)
    music = lambda song, track: [f"expect 7E07F3 {song:04X}", f"expect 7E07F5 {track:04X}"]   # noqa: E731
    spawns = CHOZO.enemies["chozo_burn_dome"]
    before = slots([e for e in spawns if not e.species.boss])
    fighters = slots([e for e in spawns if e.species.boss])
    cap = next(d for d in built_room("chozo_burn_dome").doors if d.to_room == "chozo_burn_dome_access")
    to_dome = (chain_teleports(m, room, ["chozo_save_station_2", "chozo_gathering_hall", "chozo_east_atrium",
                                         "chozo_energy_core_access", "chozo_energy_core"])
               + rise_through(m, room, "chozo_energy_core", "chozo_burn_dome_access", 3, "RIGHT")
               + chain_teleports(m, room, ["chozo_burn_dome_access", "chozo_burn_dome"]) + [f"poke {HEALTH} 63", "wait 2"])
    alive = ([f"expect {ENEMY_TABLE + ENEMY_SLOT * n:06X} {ptr:04X}" for n, ptr in enumerate(before)]
             + [f"expect {ENEMY_TABLE + ENEMY_SLOT * len(before):06X} 0000", "expect 7E0E52 0000", "expect 7ED829 0000",
                f"expect {plm_slot(PLM_HEADERS, GREY_CAP_SLOT)} 0000"] + music(0x2A, 0x03))
    started = ([chozo_item_bit(stand), "expect 7E0E52 0005"] + music(0x2A, 0x05)
               + [f"expect {ENEMY_TABLE + ENEMY_SLOT * (len(before) + n):06X} {ptr:04X}" for n, ptr in enumerate(fighters)]
               + [f"expect {plm_slot(PLM_HEADERS, GREY_CAP_SLOT)} C848", "expect 7ED829 0000"])
    dead_room = ([f"expect {ENEMY_TABLE + ENEMY_SLOT * n:06X} {ptr:04X}" for n, ptr in enumerate(before)]
                 + [f"expect {ENEMY_TABLE + ENEMY_SLOT * len(before):06X} 0000", "expectbit 7ED829 10", chozo_item_bit(stand)]
                 + music(*CHOZO.music) + [f"expect {plm_slot(PLM_HEADERS, GREY_CAP_SLOT)} 0000",   # the tunnel's missile
                                          f"expect {plm_slot(PLM_HEADERS, 38)} EEDB",       # (38) stays, the stand's (39)
                                          f"expect {plm_slot(PLM_HEADERS, 39)} 0000"])      # is gone: taken

    def save_here() -> list[str]:   # at Save Station 2 (as chozo_flaahgra)
        out = [f"poke {HEALTH} 63"]
        for addr, v in ((0x7E0AF6, CHOZO_SAVE_2.x), (0x7E0B10, CHOZO_SAVE_2.x), (0x7E0AFA, CHOZO_SAVE_2.y),
                        (0x7E0B14, CHOZO_SAVE_2.y)):
            out += poke16(addr, v)
        return out + ["hold LEFT 1", "wait 180", "hold A 2", "wait 300", "hold A 2", "wait 200", f"expect {LOAD_STATION} 0002",
                      f"expect {AREA} 0001"]

    game_over = (["poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}", "hold A 2",
                  "wait 300", "hold A 2", "wait 200"] + GAME_OVER_CONTINUE[2:]
                 + [f"expect {GAME_STATE} 0008", f"expect {ROOM_PTR} {room[CHOZO_SAVE_2.room]}"])
    out = (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
           + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_14D}_descendo.png")
           + poke16(0x7E09A2, MORPH_BALL_EQUIPMENT) + poke16(0x7E09A4, MORPH_BALL_EQUIPMENT)
           + chain_teleports(m, room, TO_GATHERING + ["chozo_save_station_2"]) + save_here()
           + to_dome + alive + [f"expect {MISSILES} 0000", f"shot {IMG_14D}_entrada.png"]
           + DRONE_APPROACH + ["wait 120", f"shot {IMG_14D}_mensagem.png"] + drone_box()[1:] + started
           + [f"shot {IMG_14D}_comeco.png"]
           + DRONE_TO_THE_DOOR + ["hold LEFT+X 2", "wait 20", "hold LEFT 120", "wait 200", f"expect 7E0AFA {10 * 16 - 21:04X}",
                                  f"expect {ROOM_PTR} {room['chozo_burn_dome']}",
                                  f"expect {plm_slot(PLM_HEADERS, GREY_CAP_SLOT)} C848", f"shot {IMG_14D}_porta_cinza.png"]
           # the death mid-fight and the continue: the save before it, the fight reset
           + game_over + ["expect 7ED829 0000", f"expect {MAX_MISSILES} 0000"]
           + to_dome + alive + [f"expect {plm_slot(PLM_HEADERS, 38)} EEDB", f"expect {plm_slot(PLM_HEADERS, 39)} EEDB"]
           + DRONE_APPROACH + drone_box() + started + ["# the fight (DRONE_FIGHT) starts here"])
    for i, move in enumerate(DRONE_FIGHT):
        out += DRONE_MOVES[move]
        if i in (4, 12):
            out += [f"shot {IMG_14D}_luta_{i:02d}.png"]
    out += (["wait 2", f"expect {KILLS} 0005"] + [f"expect {ENEMY_TABLE + ENEMY_SLOT * n:06X} 0000" for n in range(5)]
            + ["expectbit 7ED829 10", "expect 7E07F5 0000", f"expect {HEALTH} {DRONE_ENERGY_AT_WIN:04X}", "wait 30",
               f"shot {IMG_14D}_vitoria.png"]
            + DRONE_EXIT + ["hold LEFT+X 2", "wait 20", "hold LEFT 100", "wait 300", f"expect {ROOM_PTR} {room['chozo_burn_dome_access']}",
                            f"expect {GAME_STATE} 0008"]
            + chain_teleports(m, room, ["chozo_burn_dome_access", "chozo_burn_dome"]) + ["wait 60"] + dead_room
            + [f"shot {IMG_14D}_morto.png"])
    out += (chain_teleports(m, room, ["chozo_burn_dome", "chozo_burn_dome_access", "chozo_energy_core", "chozo_energy_core_access",
                                      "chozo_east_atrium", "chozo_gathering_hall", "chozo_save_station_2"])
            + save_here() + game_over + ["expectbit 7ED829 10", chozo_item_bit(stand)] + to_dome + ["wait 60"] + dead_room
            + [f"shot {IMG_14D}_depois_do_continue.png"])
    return out


def plated_beetle_test(m: dict, room: dict) -> list[str]:
    """specs/14a, chozo_plated_beetle: from the landing to the Chozo North (door_teleport through the Tallon's round-0 rooms, the
    North elevator: shortcuts, as chozo_inimigos_vivos), door_teleport through region A into the Ruined Shrine by its R0 (the
    way Samus first comes in, round 1); there the Plated Beetle in its slot with 320 health and the small ones; Samus with the
    Power Beam only (no missile: less than the round's gear), 99 energy; BEETLE_FIGHT, nothing refilled: the beetle dies (its
    slot empty), she is alive with BEETLE_ENERGY_LEFT, and the room's kill count ($0E50) is BEETLE_KILLS. specs/14b: the
    shrine is an arena (tools/chozo/bosses.py): the mini-boss song while the beetle lives; its slot emptied, the arena routine
    sets the boss bit $20 of area 1 and stops the music."""
    boss = slots(CHOZO.enemies["chozo_ruined_shrine"]).index(SPECIES["plated_beetle"].ptr)
    at = ENEMY_TABLE + ENEMY_SLOT * boss
    out = (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
           + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_14A}_descendo.png")
           + chain_teleports(m, room, [NORTH, "chozo_ruins_entrance", "chozo_main_plaza", "chozo_ruined_shrine_access",
                                       "chozo_ruined_shrine"])
           + [f"expect {at:06X} {SPECIES['plated_beetle'].ptr:04X}", f"expect {at + ENEMY_HEALTH:06X} 0140",
              f"expect {HEALTH} 0063", f"expect {MISSILES} 0000", f"expect {MAX_MISSILES} 0000", "expect 7E0E50 0000",
              "expect 7ED829 0000", "expect 7E07F3 002A", "expect 7E07F5 0005"])
    for i, move in enumerate(BEETLE_FIGHT):
        out += BEETLE_MOVES[move]
        if i == 6:
            out += [f"shot {IMG_14A}_luta.png"]
        if i == 15:
            out += [f"shot {IMG_14A}_luta_2.png", f"expect {at:06X} {SPECIES['plated_beetle'].ptr:04X}"]
    return (out + [f"expect {at:06X} 0000", f"expect {HEALTH} {BEETLE_ENERGY_LEFT:04X}", f"expect {GAME_STATE} 0008",
                   f"expect 7E0E50 {BEETLE_KILLS:04X}", "expectbit 7ED829 20", f"shot {IMG_14A}_morto.png", "wait 30",
                   "expect 7E07F5 0000"]
            # specs/14b: out and back in: the dead state (the 3 small ones, no beetle, the area's music)
            + chain_teleports(m, room, ["chozo_ruined_shrine", "chozo_ruined_shrine_access", "chozo_ruined_shrine"])
            + [f"expect {ENEMY_TABLE + ENEMY_SLOT * n:06X} {SPECIES['beetle'].ptr:04X}" for n in range(boss)]
            + [f"expect {at:06X} 0000", "expect 7E07F3 001B", "expect 7E07F5 0005", "expectbit 7ED829 20"])


def chozo_items_test(m: dict, room: dict) -> list[str]:
    """specs/12f, chozo_regiao_a_itens: the region A items the route does not take, each picked up by walking (or
    rolling) into it, A closing its box (specs/12h: the rooms' enemies deleted by RAM on arrival, clear_room_enemies: a
    shortcut, this test is about the items). From the landing to the Chozo West (door_teleport), the Morph Ball picked up
    walking (pick_up), down the North elevator (onto_platform). Shortcuts, each noted: the Bombs, the Space Jump, 5 power
    bombs and 5 missiles by RAM (the Tallon's items of rounds 1, 2 and 5); the rooms by door_teleport; Samus put by RAM
    near each item (chozo_near). Main Plaza: the half-pipe's and the grapple ledge's missiles (Space Jump ledges: put on
    them); the tree's (after the other three: the order that showed the bombed-item lookup, layouts.main_plaza): standing
    she stops against the trunk's west wall, the Power Beam leaves it, ball, SELECT twice = power bombs, X: the 3 power
    bomb blocks turn to air (4 power bombs left), stand, the dead slot above the missile and a higher slot freed by RAM
    (tree_dead_slot, specs/12g2), walk in to the far end; the E-tank: through the
    Plaza Access (door_teleport up through the one-way door, which never opens from the plaza) and down its floor door
    she lands on the ledge under the one-way door's grey cap, walks into the E-tank (199 energy); a Space Jump up into
    the cap leaves her in the plaza. The Piston Tunnel: into the pit, ball, she rolls west through the tunnel into the
    chamber and drops through the floor door; standing on the Piston Tunnel's platform east of its middle, a jump and
    RIGHT held: up through the door into the chamber, onto the door's east ledge (row 29); ball, out through the tunnel
    to the pit, up on the floor. Ruined Shrine: the half-pipe ledge's missile (put on the ledge); the lower tunnel's:
    standing she stops against the bomb block, ball, a bomb breaks it (air in the level in WRAM), she rolls in to the
    missile and back out, stands. At the end the 6 bits (with the Morph Ball's), 30 missiles' capacity, 199 energy."""
    from chozo import items as chozo_items
    morph = item_index("tallon_transport_chozo_west")
    hut = [level_block("chozo_main_plaza", 60, y) for y in (23, 24, 25)]
    bomb = level_block("chozo_ruined_shrine", 9, 12)
    pb_block, bomb_block = f"{0xC000 | 0x057:04X}", f"{0xF000 | 0x058:04X}"
    plaza = room["chozo_main_plaza"]
    out = (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
           + pick_up(morph, f"{IMG_12F}_itens_morph.png", start=MORPH_START)
           + ["hold LEFT 2", "wait 30"]    # facing west, as the door teleport leaves her in elevador_chozo_ida_e_volta
           + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12F}_itens_descendo.png")
           + poke16(0x7E09A2, MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT | SPACE_JUMP_EQUIPMENT)
           + poke16(0x7E09A4, MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT | SPACE_JUMP_EQUIPMENT)
           + poke16(0x7E09C6, 5) + poke16(0x7E09C8, 5) + poke16(0x7E09CE, 5) + poke16(0x7E09D0, 5)
           + chain_teleports(m, room, [NORTH, "chozo_ruins_entrance", "chozo_main_plaza"]) + clear_room_enemies("chozo_main_plaza"))
    # the one-way door and the E-tank on its ledge
    out += (door_teleport(m, "chozo_main_plaza", "chozo_plaza_access") + [f"expect {ROOM_PTR} {room['chozo_plaza_access']}",
                                                                         f"shot {IMG_12F}_itens_plaza_access.png"]
            + door_teleport(m, "chozo_plaza_access", "chozo_main_plaza")
            # she lands facing the screen (pose 0, y 5 px higher), as after a station: a touch of LEFT and she stands
            + ["wait 60", f"expect {ROOM_PTR} {plaza}", f"expect {GAME_STATE} 0008"] + clear_room_enemies("chozo_main_plaza")
            + ["hold LEFT 2", "wait 30",
               f"expect 7E0AFA {6 * 16 - 21:04X}",
               f"shot {IMG_12F}_itens_mao_unica.png", "hold LEFT 30", "wait 120", f"shot {IMG_12F}_itens_etank_mensagem.png",
               "wait 180", "hold A 2", "wait 120", f"expect {HEALTH} 00C7", "expect 7E09C4 00C7", f"expect {GAME_STATE} 0008",
               "hold RIGHT 20", "hold A 40", "wait 100", f"expect {ROOM_PTR} {plaza}", f"expect {GAME_STATE} 0008"])
    # the Main Plaza's Space Jump ledges
    out += chozo_pick_up(0, f"{IMG_12F}_itens_meio_tubo.png") + chozo_pick_up(1, f"{IMG_12F}_itens_gancho.png")
    # the tree's stump: power bombs
    out += (chozo_near(2, -11) + ["hold RIGHT 60", "wait 30", f"expect {SAMUS_X} {60 * 16 - 5:04X}"]
            + [f"expect {a:06X} {pb_block}" for a in hut] + [f"shot {IMG_12F}_itens_arvore.png", "hold X 2", "wait 40",
                                                             f"expect {hut[1]:06X} {pb_block}"]
            + ["hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_POSE}",
               "hold SELECT 2", "wait 10", "hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0003",
               "hold X 2", "wait 80", f"shot {IMG_12F}_itens_power_bomb.png", "wait 220"]
            + [f"expect {a:06X} 00FF" for a in hut] + [f"expect {POWER_BOMBS} 0004",
                                                     "hold UP 2", "wait 30", "hold UP 2", "wait 30", f"expect {POSE} {STAND_POSE}"]
            + tree_dead_slot()
            + ["hold RIGHT 120", "wait 120", f"shot {IMG_12F}_itens_arvore_mensagem.png",
                                                     "wait 300", "hold A 2", "wait 120", f"expect {GAME_STATE} 0008"])
    # the Piston Tunnel's Morph Ball door, down and back up
    out += (tallon_look(22, 26, 0, 256, f"{IMG_12F}_itens_fosso.png") + ["hold LEFT 30", "wait 30",
            "hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_LEFT_POSE}", "hold LEFT 120", "wait 300",
            f"expect {ROOM_PTR} {room['chozo_piston_tunnel']}", f"shot {IMG_12F}_itens_piston.png"]
            + PISTON_JUMP + [f"expect {ROOM_PTR} {plaza}", f"expect 7E0AFA {CHAMBER_FEET:04X}"] + clear_room_enemies("chozo_main_plaza")
            + [f"shot {IMG_12F}_itens_camara.png",
                             "hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", "hold RIGHT 80", "wait 30",
                             "hold UP 2", "wait 30", "hold UP 2", "wait 30", f"expect {POSE} {STAND_POSE}",
                             "hold A+RIGHT 40", "hold RIGHT 60", "wait 30", f"expect {ROOM_PTR} {plaza}",
                             f"expect 7E0AFA {PLAZA_FEET:04X}"])
    # the Ruined Shrine: the half-pipe ledge, the lower tunnel's bomb block
    out += (chain_teleports(m, room, ["chozo_main_plaza", "chozo_ruined_shrine_access", "chozo_ruined_shrine"])
            + clear_room_enemies("chozo_ruined_shrine")
            + chozo_pick_up(5, f"{IMG_12F}_itens_shrine_meio_tubo.png")
            + chozo_near(6, 6) + ["hold LEFT 40", "wait 30", f"expect {SAMUS_X} {10 * 16 + 5:04X}", f"expect {bomb:06X} {bomb_block}",
                                  f"shot {IMG_12F}_itens_bloco_de_bomba.png",
                                  "hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", "hold X 2", "wait 100",
                                  f"expect {bomb:06X} 00FF", "hold LEFT 60", "wait 120", f"shot {IMG_12F}_itens_tunel_mensagem.png",
                                  "wait 300", "hold A 2", "wait 120", f"expect {GAME_STATE} 0008",
                                  "hold RIGHT 80", "wait 30", "hold UP 2", "wait 30", "hold UP 2", "wait 30",
                                  f"expect {POSE} {STAND_POSE}", f"shot {IMG_12F}_itens_tunel_volta.png"])
    taken = (0, 1, 2, 3, 5, 6)
    return out + [chozo_bits_word(taken, (morph,)), f"expect {MAX_MISSILES} {5 + 5 * sum(chozo_items.ITEMS[n].kind == 0xEEDB for n in taken):04X}",
                  "expect 7E09C4 00C7"]


# specs/12g: the new locks' tests run on the test build (tools/build.py --teste-12g -> build/teste-12g/, chozo/testrooms.py:
# the Ruined Fountain Access hot, its door to the Main Plaza a charge door on its side, the Charge Beam on its platform and
# the Varia Suit on its floor), built by main() before them; the game's ROM has none of this (the rooms of these items are
# regions C and D's)
TEST_12G_DIR = ROOT / "build/teste-12g"
TEST_12G = ("porta_de_charge", "sala_quente")
IMG_12G = "build/tests/12g"
SUB_HEALTH = "7E09C4"                # max energy (HEALTH, $09C2, is the energy)
CHARGE_EQUIPMENT, VARIA_EQUIPMENT = 0x1000, 0x0001   # $09A6 beams / $09A2 items
FOUNTAIN = "chozo_ruined_fountain_access"


def into_test_room(m: dict, room: dict) -> list[str]:
    """From the landing to the Chozo (door_teleport through the Tallon's round-0 rooms, onto the Chozo West's platform:
    shortcuts, as chozo_regiao_a_itens), down the North elevator, door_teleport to the test room through the Main Plaza's
    door into it (as walking in, she comes in through the charge door: its cap shuts behind her)."""
    return (chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
            + onto_platform(WEST) + ride_elevator(room, WEST, f"{IMG_12G}_descendo.png")
            + chain_teleports(m, room, [NORTH, "chozo_ruins_entrance", "chozo_main_plaza", FOUNTAIN]) + ["wait 30"])


def chozo_test_item(kind: int) -> int:
    from chozo import items as chozo_items
    return next(n for n, it in enumerate(chozo_items.ITEMS) if it.kind == kind)


def test_room_near(n: int, start: int) -> list[str]:
    """chozo_near for the test room's Charge Beam / Varia Suit (chozo/testrooms.py SPOTS: their rows have no spot)."""
    from chozo import items as chozo_items, testrooms
    it = chozo_items.ITEMS[n]
    x, y = (testrooms.SPOTS[it.kind][0] + start) * 16 + 8, (testrooms.SPOTS[it.kind][1] + 1) * 16 - 21
    place = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y)):
        place += poke16(addr, v)
    cam = poke16(0x7E0911, x // 256 * 256) + poke16(0x7E0915, 0)
    return place + ["wait 30"] + place + cam + ["wait 4", "hold START 10", "wait 200", "hold START 10", "wait 200"]


def test_room_pick_up(n: int, shot: str) -> list[str]:
    """Walk into the test room's item n from 2 blocks west, close its box with A, its bit on."""
    bit = __import__("chozo.items", fromlist=["BITS"]).BITS[n]
    return (test_room_near(n, -2) + ["hold RIGHT 40", "wait 120", f"shot {shot}", "wait 300", "hold A 2", "wait 120",
                                     f"expectbit {0x7ED870 + bit // 8:06X} {1 << (bit % 8):02X}", f"expect {GAME_STATE} 0008"])


CHARGE_DOOR_X = 2 * 16 + 5   # standing against the cap of a west door (beam_door_shut)


def charge_door_shut(room: dict) -> list[str]:
    """Walking west she stops against the charge door's cap, in the test room."""
    return ["hold LEFT 40", "wait 20", f"expect {SAMUS_X} {CHARGE_DOOR_X:04X}", f"expect {ROOM_PTR} {room[FOUNTAIN]}"]


def charge_door(m: dict, room: dict) -> list[str]:
    """specs/12g, porta_de_charge (test build): in the test room (hot: the Varia Suit by RAM, the heat is sala_quente's), the
    charge door to the Main Plaza is shut (she stops against its cap, white since specs/12g2: the cap's block and the palette
    line checked, charge_door_white; photo); an uncharged Power Beam shot, missiles
    (5 by RAM) leave it shut; the Charge Beam picked up by walking into it (its bit, $09A6/$09A8 with $1000); an uncharged
    shot still leaves it shut; X held 90 frames (the charge) and let go: the charged shot opens it, she walks into the Main
    Plaza; back by door_teleport, it is shut again (closed on every visit, as the beam doors)."""
    n = chozo_test_item(__import__("tallon.items", fromlist=["CHARGE_BEAM"]).CHARGE_BEAM)
    shut = charge_door_shut(room)
    out = into_test_room(m, room) + poke16(0x7E09A2, VARIA_EQUIPMENT) + poke16(0x7E09A4, VARIA_EQUIPMENT)
    out += [f"poke {HEALTH} 63"] + stand_before_chozo_door() + shut + charge_door_white() + [f"shot {IMG_12G}_porta_fechada.png"]
    out += ["hold LEFT+X 2", "wait 40"] * 3 + shut                                          # Power Beam, uncharged
    out += (poke16(0x7E09C6, 5) + poke16(0x7E09C8, 5) + ["hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0001"]
            + ["hold LEFT+X 2", "wait 40"] * 2 + [f"expect {MISSILES} 0003"] + shut
            + ["hold SELECT 2", "wait 10", f"expect {HUD_ITEM} 0000"])  # missiles
    out += test_room_pick_up(n, f"{IMG_12G}_charge_mensagem.png") + [
        f"expectbit 7E09A7 {CHARGE_EQUIPMENT >> 8:02X}", f"expectbit 7E09A9 {CHARGE_EQUIPMENT >> 8:02X}"]
    out += stand_before_chozo_door() + shut + ["hold LEFT+X 2", "wait 40"] * 3 + shut      # Charge Beam, uncharged
    out += ["hold LEFT 2", "hold X 90", "wait 6", f"shot {IMG_12G}_tiro_carregado.png", "wait 120",
            f"shot {IMG_12G}_porta_aberta.png", "hold LEFT 90", "wait 200",
            f"expect {ROOM_PTR} {room['chozo_main_plaza']}", f"expect {GAME_STATE} 0008"]
    return out + door_teleport(m, "chozo_main_plaza", FOUNTAIN) + ["wait 30"] + shut + [f"shot {IMG_12G}_porta_de_novo.png"]


def charge_door_white() -> list[str]:
    """specs/12g2: the shut charge door (the test room's L0 cap) is drawn with the white metatiles (the cap's top block in the
    level in WRAM, $7F0002 + 2 * block: beamdoors.CHARGE_METATILES) and palette line beamdoors.CHARGE_LINE holds the white
    (the palette in WRAM, $7EC000 + 2 * colour), as wave_door_purple."""
    from tallon import beamdoors
    r = built_room(FOUNTAIN)
    d = r.doors[0]
    cx, cy = (1 if d.side == "L" else r.width * 16 - 2), d.screen * 16 + 6     # build.door_cap_and_screen
    top = 0xC000 | (0x400 if d.side == "L" else 0) | beamdoors.CHARGE_METATILES[0x004]
    return ([f"expect {0x7F0002 + 2 * (cy * r.width * 16 + cx):06X} {top:04X}"]
            + [f"expect {0x7EC000 + 2 * (beamdoors.CHARGE_LINE * 16 + i):06X} {c:04X}" for i, c in enumerate(beamdoors.WHITE, 1)])


def stand_before_chozo_door() -> list[str]:
    """Shortcut: Samus put by RAM standing 4 blocks east of the test room's west door (its floor row 10), camera there."""
    x, y = (2 + 4) * 16 + 8, 10 * 16 - 21
    place = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y)):
        place += poke16(addr, v)
    return (place + ["wait 30"] + place + poke16(0x7E0911, 0) + poke16(0x7E0915, 0)
            + ["wait 4", "hold START 10", "wait 200", "hold START 10", "wait 200"])


def heat_room(m: dict, room: dict) -> list[str]:
    """specs/12g, sala_quente (test build): in the hot test room (measured, HEAT_* below): with the Power Suit the energy
    drops HEAT_DROP in HEAT_FRAMES frames (a quarter a frame, PalPreInstr_SamusInHeat $8D:E379: photo, Samus glowing);
    with the Gravity Suit only (by RAM) it drops too, HEAT_DROP_GRAVITY (specs/12g2, the user's decision: only the Varia
    protects, `AND #$0021` -> `#$0001` at $8D:E37D; vanilla SM let the Gravity Suit protect too; the drop is a quarter of
    the Power Suit's because Samus_HandlePeriodicDamage $90:E9CE divides any periodic damage by 4 with the Gravity Suit);
    without suits again it drops; the
    Varia Suit picked up by walking into it (its bit, $09A2/$09A4 with $0001; the cutscene leaves her where she took it: x
    checked, tallon/items.py varia_patch), then it does not drop."""
    n = chozo_test_item(__import__("tallon.items", fromlist=["VARIA_SUIT"]).VARIA_SUIT)
    from chozo import testrooms
    vx = testrooms.SPOTS[__import__("tallon.items", fromlist=["VARIA_SUIT"]).VARIA_SUIT][0]
    out = into_test_room(m, room) + [f"expect {ROOM_PTR} {room[FOUNTAIN]}"]
    drop = [f"poke {HEALTH} 63", f"wait {HEAT_FRAMES}", f"expect {HEALTH} {99 - HEAT_DROP:04X}"]
    stay = [f"poke {HEALTH} 63", f"wait {HEAT_FRAMES}", f"expect {HEALTH} 0063"]
    out += drop + [f"shot {IMG_12G}_calor_sem_varia.png"]
    gravity = [f"poke {HEALTH} 63", f"wait {HEAT_FRAMES}", f"expect {HEALTH} {99 - HEAT_DROP_GRAVITY:04X}"]
    out += poke16(0x7E09A2, 0x0020) + poke16(0x7E09A4, 0x0020) + gravity + [f"shot {IMG_12G}_calor_com_gravity.png"]
    out += poke16(0x7E09A2, 0) + poke16(0x7E09A4, 0) + drop
    out += [f"poke {HEALTH} 63"] + test_room_pick_up(n, f"{IMG_12G}_varia_mensagem.png")
    out += [f"expectbit 7E09A2 {VARIA_EQUIPMENT:02X}", f"expectbit 7E09A4 {VARIA_EQUIPMENT:02X}",
            f"expect {SAMUS_X} {VARIA_PICKED_X:04X}"]
    return out + stay + [f"shot {IMG_12G}_calor_com_varia.png"]


HEAT_FRAMES = 240
HEAT_DROP = 60          # a quarter of energy a frame for HEAT_FRAMES frames (measured in the test build, specs/12g)
HEAT_DROP_GRAVITY = 15  # specs/12g2: with the Gravity Suit only, the same heat divided by 4 ($90:E9CE; measured)
VARIA_PICKED_X = 0x02BD # measured: walking into the Varia Suit (44, 9) from the west she takes it at x 701; the vanilla
                        # cutscene would put her at the screen's middle, the camera's x 512 + 120 = 632 ($0278)


def tests_12g(m: dict) -> dict[str, list[str]]:
    """specs/12g: the tests of the test build (manifest `m`: its rooms' addresses)."""
    room = {k: f"{v['header'] & 0xFFFF:04X}" for k, v in m.items() if k != "banks"}
    start = NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"] + lands_on_landing_site(room[LANDING_SITE])
    return {"porta_de_charge": start + charge_door(m, room), "sala_quente": start + heat_room(m, room)}


# specs/17d: the lava test build (tools/build.py --teste-17d -> build/teste-17d/, magmoor/testrooms.py: two rooms of area 2,
# hung on a door the game doesn't have: specs/17e-17h the Magmoor's P16 east door, since specs/17i the P26's (the transport to
# the Mines West) R1, testrooms.HOST / HOST_DOOR), built by main() before these tests; the game's ROM has none of them
TEST_17D_DIR = ROOT / "build/teste-17d"
TEST_17D = ("lava_medida", "porta_de_onda_lava")
IMG_17D = "build/tests/17d"
LAVA_Y = "7E1962"                    # lava_acid_y_pos (FX type 2's surface)
LAVA_FRAMES = 120
LAVA_DROP = {0: 60, 0x0001: 30, 0x0020: 0}   # energy lost in LAVA_FRAMES frames in the lava, by suit (reach.LAVA_DAMAGE_PER_FRAME)
HOT_LAVA_DROP = 45                   # 60 frames in the hot room's lava without a suit: the heat's 1/4 + the lava's 1/2 a frame
LAVA_JUMPS = [(3, 0, "A"), (2, 0, "A"), (1, 0, "A"), (3, 0x0001, "A"), (3, 0x0020, "A")]   # (depth, suit, buttons): 200 frames
# the escapes (measured): from the deep floor at column 15 jumping east, from column 8 jumping west, she ends on the dry floor
# (feet row 9: y 10 * 16 - 21) at these x
LAVA_ESCAPES = [(15, "RIGHT", 0x0144), (8, "LEFT", 0x003C)]


def lava_place(x: int, y: int, items: int, face: str = "RIGHT") -> list[str]:
    """Samus put by RAM at pixel (x, y) with only `items` equipped, facing `face` (a toque first: put by RAM she faces the
    screen and A does not jump), placed twice to stop any run."""
    place = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y)):
        place += poke16(addr, v)
    return (poke16(0x7E09A2, items) + poke16(0x7E09A4, items) + [f"hold {face} 2", "wait 10"] + place + ["wait 30"]
            + place + ["wait 60"])


def lava_teleport(door: int, side: str, screen: int, width: int, height_px: int = 0) -> list[str]:
    """door_teleport through door entry `door` of a test room (not in tools/areas.py AREAS): Samus put before a door on wall
    `side` of screen `screen` of a room `width` screens wide (the room she is in), the camera on that screen."""
    x = 24 if side == "L" else (width * 16 - 2) * 16 + 8
    y = (screen * 16 + 10) * 16 - 21
    cam = (0 if side == "L" else (width - 1) * 256, screen * 256)
    place = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y)):
        place += poke16(addr, v)
    return (place + ["wait 30"] + place + poke16(0x7E0911, cam[0]) + poke16(0x7E0915, cam[1]) + ["wait 2"]
            + poke16(0x7E099C, DOOR_HIT_TRANSITION) + poke16(0x7E078D, door & 0xFFFF) + poke16(0x7E0998, 9) + ["wait 300"])


def host_door_to_cool() -> int:
    """specs/17h: the index of the host's door to the cool test room in the test build (specs/17i: the P26's R1; its L1 to the
    Workstation Tunnel comes first)."""
    import copy
    from magmoor import testrooms
    host = testrooms.apply(copy.deepcopy(MAGMOOR)).by_key()[testrooms.HOST]
    return next(i for i, d in enumerate(host.doors) if d.to_room == testrooms.COOL)


def into_lava_rooms(m: dict, room: dict) -> list[str]:
    """From the landing, through the test host's door (teleport; specs/17i: the Magmoor P26's R1) into the cool test room (in
    through its wave door, L0): lava FX type 2 with its surface at the row of magmoor/testrooms.py LAVA_ROW."""
    from magmoor import testrooms
    host = MAGMOOR.by_key()[testrooms.HOST]
    return (lava_teleport(m[testrooms.HOST]["doors"][host_door_to_cool()], *testrooms.HOST_DOOR, host.width)
            + [f"expect {ROOM_PTR} {room[testrooms.COOL]}", f"expect {WATER_FX_TYPE} 0002",
               f"expect {LAVA_Y} {testrooms.LAVA_ROW * 16:04X}", "wait 30"])


def lava_measured(m: dict, room: dict) -> list[str]:
    """specs/17d, lava_medida (test build): in the cool room's pit (magmoor/testrooms.py PIT_FLOORS, the surface on row
    LAVA_ROW), on the deep floor: the energy lost in LAVA_FRAMES frames with the Gravity Suit (0), the Varia (a quarter a frame)
    and no suit (half a frame: Samus_Animate_LavaFx $90:81C0); straight jumps from each depth, the Varia and the Gravity Suit
    (trajectories read by check_lava_jumps: reach.LAVA_RISE_PX; the Varia's = no suit's; the Gravity's = the dry 113); out of
    the deep pit to either side with a jump and the direction held (LAVA_ESCAPES: she stands on the dry floor); photos. Then
    in the hot room ($09, hot: the heat and the glows): out of the lava a quarter a frame (the heat), in it without a suit three
    quarters, with the Varia a quarter (the lava's)."""
    from magmoor import testrooms
    depth = {feet - testrooms.LAVA_ROW + 1: x0 for x0, _, feet in testrooms.PIT_FLOORS}
    deep_x = depth[3] * 16 + 8
    deep_y = (testrooms.PIT_FLOORS[0][2] + 1) * 16 - 21
    out = into_lava_rooms(m, room)
    full = ["poke 7E09C2 E7", "poke 7E09C3 03", "poke 7E09C4 E7", "poke 7E09C5 03"]   # 999 energy: no death mid-measure
    for suit in (0x0020, 0x0001, 0):
        out += full + lava_place(deep_x, deep_y, suit) + [f"poke {HEALTH} 63", "poke 7E09C3 00", f"wait {LAVA_FRAMES}",
                                                          f"expect {HEALTH} {99 - LAVA_DROP[suit]:04X}"]
        if suit == 0:
            out += [f"shot {IMG_17D}_lava_sem_roupa.png"]
    for d, suit, buttons in LAVA_JUMPS:
        out += full + lava_place(depth[d] * 16 + 8, (testrooms.LAVA_ROW + d) * 16 - 21, suit)
        out += ([f"hold {buttons} 1"] + [f"peekw {a}" for a in SAMUS_X_Y_RADIUS]) * 200
    for col, face, x in LAVA_ESCAPES:
        out += full + lava_place(col * 16 + 8, deep_y, 0, face) + [f"hold {face}+A 50", f"hold {face} 20", "wait 30",
                                                                    f"expect {SAMUS_X} {x:04X}", f"expect 7E0AFA {10 * 16 - 21:04X}"]
    out += (poke16(0x7E0911, 0) + ["hold START 10", "wait 200", "hold START 10", "wait 200",   # camera on her, redrawn
                                    f"shot {IMG_17D}_saiu_da_lava.png"]
            + poke16(0x7E09A2, 0) + poke16(0x7E09A4, 0))
    # into the hot room through the cool room's east door (R0)
    out += [f"poke {HEALTH} 63", "poke 7E09C3 00"] + lava_teleport(m[testrooms.COOL]["doors"][1], "R", 0, 2)
    out += [f"expect {ROOM_PTR} {room[testrooms.HOT]}", f"expect {WATER_FX_TYPE} 0002", f"poke {HEALTH} 63", "poke 7E09C3 00",
            f"wait {LAVA_FRAMES}", f"expect {HEALTH} {99 - HEAT_DROP // 2:04X}", f"shot {IMG_17D}_quente_seco.png"]
    hx, _, hfeet = testrooms.HOT_PIT
    out += full + lava_place(hx * 16 + 24, (hfeet + 1) * 16 - 21, 0) + [f"poke {HEALTH} 63", "poke 7E09C3 00", "wait 60",
                                                                 f"expect {HEALTH} {99 - HOT_LAVA_DROP:04X}",
                                                                 f"shot {IMG_17D}_quente_lava.png"]
    out += full + lava_place(hx * 16 + 24, (hfeet + 1) * 16 - 21, 0x0001) + [f"poke {HEALTH} 63", "poke 7E09C3 00",
                                                                       f"wait {LAVA_FRAMES}",
                                                                       f"expect {HEALTH} {99 - LAVA_DROP[1]:04X}",
                                                                       f"shot {IMG_17D}_quente_lava_varia.png"]
    return out


def check_lava_jumps(stdout: str) -> list[str]:
    """specs/17d: the jumps printed by lava_measured must give reach.LAVA_RISE_PX (no suit and the Varia) and the dry jump
    with the Gravity Suit."""
    vals = [int(v, 16) for v in re.findall(r"7E0(?:AF6|AFA|B00) = ([0-9A-F]{4})", stdout)]
    frames = [(x, y + r) for x, y, r in zip(vals[0::3], vals[1::3], vals[2::3])]
    if len(frames) < 200 * len(LAVA_JUMPS):
        return [f"FAIL pulo na lava: {len(frames)} quadros lidos"]
    fails = []
    for k, (d, suit, _) in enumerate(LAVA_JUMPS):
        try:
            rise = reach.arc_from_samples(frames[200 * k:200 * (k + 1)])[0]
        except ValueError as e:
            fails.append(f"FAIL pulo na lava a {d} linhas (roupa ${suit:04X}): {e}")
            continue
        want = reach.JUMP_RISE_PX if suit & 0x0020 else reach.LAVA_RISE_PX[d]
        if rise != want:
            fails.append(f"FAIL pulo na lava a {d} linhas (roupa ${suit:04X}): subiu {rise} px, reach.py diz {want}")
    return fails


def lava_wave_doors(m: dict, room: dict) -> list[str]:
    """specs/17d, porta_de_onda_lava (test build): in the cool room ($0A) the wave door she came in through (L0) is shut (she
    stops against its cap), drawn with the purple metatiles (the cap's top block in the level in WRAM) and palette line
    lava.PAINT_LINE purple (in WRAM); the Power Beam leaves it shut, the Wave Beam opens it and she walks into the test host
    (specs/17i: the Magmoor's P26); then in the hot room ($09), in through its wave door (L0): the same cap and colours."""
    from magmoor import testrooms
    from smlib import lava
    from tallon import beamdoors

    def purple(width: int) -> list[str]:   # the west door's cap (block 1, row 6), drawn h-flipped
        cx, cy = 1, 6
        return ([f"expect {0x7F0002 + 2 * (cy * width * 16 + cx):06X} {0xC400 | beamdoors.PAINT_METATILES[0x004]:04X}"]
                + [f"expect {0x7EC000 + 2 * (lava.PAINT_LINE * 16 + i):06X} {c:04X}" for i, c in enumerate(beamdoors.PURPLE, 1)])

    def shut() -> list[str]:   # against the west door's cap
        return [f"poke {HEALTH} 63", "hold LEFT 60", "wait 20", f"expect {SAMUS_X} {2 * 16 + 5:04X}"]

    out = into_lava_rooms(m, room) + lava_place((2 + 4) * 16 + 8, 10 * 16 - 21, 0, "LEFT")
    out += shut() + purple(2) + [f"shot {IMG_17D}_porta_de_onda_fria.png"]
    out += ["hold LEFT+X 2", "wait 30"] * 2 + shut()
    out += give_beams(WAVE_BEAM) + ["hold LEFT+X 2", "wait 6", f"shot {IMG_17D}_porta_de_onda_abrindo.png", "wait 120",
                                    "hold LEFT 90", "wait 200", f"expect {ROOM_PTR} {room[testrooms.HOST]}"]
    out += (lava_teleport(m[testrooms.HOST]["doors"][host_door_to_cool()], *testrooms.HOST_DOOR, MAGMOOR.by_key()[testrooms.HOST].width)
            + [f"expect {ROOM_PTR} {room[testrooms.COOL]}"])
    out += lava_teleport(m[testrooms.COOL]["doors"][1], "R", 0, 2) + [f"expect {ROOM_PTR} {room[testrooms.HOT]}"]
    out += lava_place((2 + 2) * 16 + 8, 10 * 16 - 21, 0x0001, "LEFT") + shut() + purple(1) + [   # west of its pit
        f"shot {IMG_17D}_porta_de_onda_quente.png"]
    return out


def tests_17d(m: dict) -> dict[str, list[str]]:
    """specs/17d: the tests of the lava test build (manifest `m`)."""
    room = {k: f"{v['header'] & 0xFFFF:04X}" for k, v in m.items() if k != "banks"}
    start = NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"] + lands_on_landing_site(room[LANDING_SITE])
    return {"lava_medida": start + lava_measured(m, room), "porta_de_onda_lava": start + lava_wave_doors(m, room)}


# specs/18d: the ice looks' test build (tools/build.py --teste-18d -> build/teste-18d/, phendrana/testrooms.py: an area 4 of its
# own, five rooms in a row: rain, snow, icy ruins, lab, water), built by main() before these tests; the game's ROM has none of
# them. The tests get in by loading its station 0 (the rain room) by RAM, as a continue would.
TEST_18D_DIR = ROOT / "build/teste-18d"
TEST_18D = ("neve_medida", "porta_de_onda_gelo", "agua_medida_area_4")
IMG_18D = "build/tests/18d"
BG3_Y = "7ECADE"                     # bg3_ypos: the snow layer's scroll
SNOW_FRAMES = 64                     # frames between the two readings of BG3_Y
SNOW_FALL = {0x08: 16, 0x0A: None}   # the spores move 64/256 px a frame (16 in SNOW_FRAMES); the rain: printed only


def ice_rooms():
    from phendrana import testrooms
    return testrooms, {r.key: r for r in testrooms.rooms()}


def ice_station() -> list[str]:
    """Load the test build's station of area 4 in the rain room (testrooms.TEST_STATION) by RAM; Samus takes input ~550 frames
    later."""
    from phendrana import testrooms
    return (["poke 7E079F 04", "poke 7E07A0 00"] + poke16(0x7E078B, testrooms.TEST_STATION) + poke16(0x7ED914, 5)
            + poke16(0x7E0998, 6) + ["wait 600"])


def ice_next(m: dict, key: str) -> list[str]:
    """door_teleport through the east door (R0) of test room `key` (its last door) into the next room."""
    _, by = ice_rooms()
    r = by[key]
    return lava_teleport(m[key]["doors"][len(r.doors) - 1], "R", 0, r.width)


def palette_expect(line: int, colours: dict) -> list[str]:
    from smlib import ice
    return [f"expect {0x7EC000 + 2 * (ln * 16 + i):06X} {ice._bgr555(c):04X}" for (ln, i), c in colours.items() if ln == line]


def snow_measured(m: dict, room: dict) -> list[str]:
    """specs/18d, neve_medida (test build): in each room the FX type in RAM ($196E) is the room's (rain $0A, spores $08 in the
    snow and the icy ruins, none in the lab); the snowflakes' colours (palette colours 25-26 = line 1 colours 9-10 in WRAM) are
    ice.SNOW_FLAKES and colour 27 is black (palette blend 0); BG3_Y read twice SNOW_FRAMES frames apart (the fall: printed,
    check_snow_fall); each look's own colours in the WRAM palette; photos of the four rooms."""
    from smlib import ice
    testrooms, by = ice_rooms()
    flakes = [f"expect {0x7EC000 + 2 * (16 + i):06X} {ice._bgr555(c):04X}" for (_, i), c in ice.SNOW_FLAKES.items()]
    out = ice_station() + [f"expect {AREA} 0004", f"expect {ROOM_PTR} {room[testrooms.RAIN]}"]

    def measure(key: str, fx: str, tag: str) -> list[str]:
        r = by[key]
        lines = [f"expect {ROOM_PTR} {room[key]}", f"expect {WATER_FX_TYPE} {fx}", "wait 60"]
        if r.snow:
            lines += flakes + ["expect 7EC036 0000", f"peekw {BG3_Y}", f"wait {SNOW_FRAMES - 1}", f"peekw {BG3_Y}"]
        return lines + ["hold RIGHT 30", "wait 30", f"shot {IMG_18D}_{tag}.png"]

    out += measure(testrooms.RAIN, "000A", "chuva")
    out += ice_next(m, testrooms.RAIN) + measure(testrooms.SNOW, "0008", "neve") + palette_expect(4, ice.SNOW_COLOURS)
    out += ice_next(m, testrooms.SNOW) + measure(testrooms.RUINS, "0008", "ruinas_de_gelo") + palette_expect(7, ice.RUINS_COLOURS)
    out += ice_next(m, testrooms.RUINS) + measure(testrooms.LAB, "0000", "laboratorio") + palette_expect(4, ice.LAB_COLOURS)
    return out


def check_snow_fall(stdout: str) -> list[str]:
    """specs/18d: the BG3 layer of the rain and of the spores moves as smlib/ice.py says (SNOW_FALL: the spores 16 px in 64
    frames; the rain only printed)."""
    vals = [int(v, 16) for v in re.findall(r"7ECADE = ([0-9A-F]{4})", stdout)]
    if len(vals) != 6:
        return [f"FAIL neve: {len(vals)} leituras do BG3"]
    falls = [(vals[k] - vals[k + 1]) & 0xFFFF for k in (0, 2, 4)]
    print(f"neve: BG3 y em {SNOW_FRAMES} quadros: chuva {falls[0]}, neve {falls[1]}, ruínas {falls[2]}")
    return [f"FAIL neve: o BG3 desceu {f} px em {SNOW_FRAMES} quadros, esperado {SNOW_FALL[0x08]}"
            for f in falls[1:] if f != SNOW_FALL[0x08]]


def ice_wave_doors(m: dict, room: dict) -> list[str]:
    """specs/18d, porta_de_onda_gelo (test build): in each look (snow $01, icy ruins $1C, lab $1B) the east wave door is shut
    (she stops against its cap), drawn with the purple metatile (the cap's top block in the level in WRAM) and the look's paint
    line purple in the WRAM palette; the Power Beam leaves it shut, the Wave Beam opens it and she walks into the next room. The
    green (ice) and orange (plasma) caps of the icy ruins' and the lab's west doors: photos."""
    from smlib import ice
    from tallon import beamdoors
    testrooms, by = ice_rooms()
    paint = {testrooms.SNOW: ice.SNOW_PAINT_LINE, testrooms.RUINS: beamdoors.RUINS_PAINT_LINE,
             testrooms.LAB: beamdoors.PAINT_LINE}
    out = ice_station() + ice_next(m, testrooms.RAIN)
    for key, nxt, tag in ((testrooms.SNOW, testrooms.RUINS, "neve"), (testrooms.RUINS, testrooms.LAB, "ruinas"),
                          (testrooms.LAB, testrooms.WATER, "laboratorio")):
        r = by[key]
        wb = r.width * 16
        cx, cy = wb - 2, 6
        out += [f"expect {ROOM_PTR} {room[key]}"] + give_beams(0) + lava_place((wb - 8) * 16 + 8, 10 * 16 - 21, 0, "RIGHT")
        out += [f"shot {IMG_18D}_porta_oeste_{tag}.png"]
        shut = [f"poke {HEALTH} 63", "hold RIGHT 90", "wait 20", f"expect {SAMUS_X} {(wb - 3) * 16 + 11:04X}"]
        back = ["hold LEFT 24", "wait 10", "hold RIGHT 1", "wait 10"]   # ~4 blocks off the cap: a point-blank shot misses it
        out += shut + [f"expect {0x7F0002 + 2 * (cy * wb + cx):06X} {0xC000 | beamdoors.PAINT_METATILES[0x004]:04X}"]
        out += [f"expect {0x7EC000 + 2 * (paint[key] * 16 + i):06X} {c:04X}" for i, c in enumerate(beamdoors.PURPLE, 1)]
        redraw = (poke16(0x7E0911, (r.width - 1) * 256)   # the camera on the door's screen, redrawn (pause and unpause)
                  + ["hold START 10", "wait 200", "hold START 10", "wait 200"])
        out += redraw + [f"shot {IMG_18D}_porta_de_onda_{tag}.png"] + back
        out += ["hold RIGHT+X 2", "wait 30"] * 2 + shut
        out += give_beams(WAVE_BEAM) + back + ["hold RIGHT+X 2", "wait 6",
                                        f"shot {IMG_18D}_porta_de_onda_{tag}_abrindo.png", "wait 120", "hold RIGHT 90",
                                        "wait 200", f"expect {ROOM_PTR} {room[nxt]}"]
    return out


# the water jump in the test build's flooded room (testrooms.WATER: floor row 13, open up to row 3 at column 7, east of the
# ledge under the west door, as the Savestation's column 2)
ICE_WATER_X = 7 * 16 + 8
# the sub-pixels Samus had at the start of each of the Savestation's measured jumps (read there: x $0AF8, y $0AFC = $FFFF); the
# horizontal reach of reach.py's WATER_* depends on them by 1-3 px, so the area 4 jumps start from the same ones
ICE_WATER_SUBPIXELS = (0xCC00, 0xDC00, 0xFFFF, 0xBFFF)


def ice_water(m: dict, room: dict) -> list[str]:
    """specs/18d, agua_medida_area_4 (test build): in area 4's flooded room the FX is water (type 6, surface WATER_SURFACE_Y) and
    no area palette FX runs (Maridia's list: specs/18b); the underwater jumps without and with the Gravity Suit (as
    pulo_na_agua_medido: check_water_jumps, reach.py WATER_*); a photo."""
    testrooms, by = ice_rooms()
    out = ice_station() + lava_teleport(m[testrooms.LAB]["doors"][1], "R", 0, 2)
    out += [f"expect {ROOM_PTR} {room[testrooms.WATER]}", f"expect {WATER_FX_TYPE} 0006", f"expect {WATER_SURFACE} 0010",
            "expect 7E1EF5 0000", f"shot {IMG_18D}_agua.png"]
    place = []
    for addr, v in ((0x7E0AF6, ICE_WATER_X), (0x7E0B10, ICE_WATER_X), (0x7E0AFA, WATER_JUMP_Y), (0x7E0B14, WATER_JUMP_Y),
                    (0x7E0AFC, 0xFFFF)):
        place += poke16(addr, v)
    for (_, items, buttons, frames), sub in zip(WATER_JUMPS, ICE_WATER_SUBPIXELS):
        out += (poke16(0x7E09A2, items) + ["hold RIGHT 2", "wait 20"] + place + ["wait 30"] + place + poke16(0x7E0AF8, sub)
                + ["wait 90"])
        out += ([f"hold {buttons} 1"] + [f"peekw {a}" for a in SAMUS_X_Y_RADIUS]) * frames
    return out


def tests_18d(m: dict) -> dict[str, list[str]]:
    """specs/18d: the tests of the ice looks' test build (manifest `m`)."""
    room = {k: f"{v['header'] & 0xFFFF:04X}" for k, v in m.items() if k != "banks"}
    return {"neve_medida": NEW_GAME + snow_measured(m, room), "porta_de_onda_gelo": NEW_GAME + ice_wave_doors(m, room),
            "agua_medida_area_4": NEW_GAME + ice_water(m, room)}


# specs/19d: the Mines looks' test build (tools/build.py --teste-19d -> build/teste-19d/, mines/testrooms.py: four rooms in a row,
# entry and pirate base ($0E), rock and fungus ($08) and an end room; specs/19e: on a copy of the Mines' area 5), built by main()
# before this test; the game's ROM has none of them. The test gets in by loading its station (testrooms.TEST_STATION, the entry
# room; specs/19e: 7, station 0 being the Mines' arrival) by RAM, as specs/18d's. specs/19e: in group D.
TEST_19D_DIR = ROOT / "build/teste-19d"
TEST_19D = ("porta_de_plasma_mina",)
IMG_19D = "build/tests/19d"


def mines_station() -> list[str]:
    """Load the test build's station of area 5 (mines/testrooms.py TEST_STATION, in ENTRY) by RAM; Samus takes input ~550 frames
    later."""
    from mines import testrooms
    return (["poke 7E079F 05", "poke 7E07A0 00"] + poke16(0x7E078B, testrooms.TEST_STATION) + poke16(0x7ED914, 5)
            + poke16(0x7E0998, 6) + ["wait 600"])


def mines_doors(m: dict, room: dict) -> list[str]:
    """specs/19d, porta_de_plasma_mina (test build): in each look (pirate base $0E, rock and fungus $08) the look's colours in the
    WRAM palette (the phazon blue of mines.BASE_COLOURS / ROCK_COLOURS) and the purple of the paint line; the east wave door is
    shut (she stops against its cap), drawn with the purple metatile (the cap's top block in the level in WRAM); the Power Beam
    leaves it shut, the Wave Beam opens it and she walks into the next room. In the rock room the west plasma door (orange, on its
    side): the Power Beam and the Wave Beam leave it shut, the Plasma Beam opens it and she walks back into the base room. Photos
    of both looks, their caps (the base's green ice cap too) and the plasma cap opening."""
    from mines import testrooms
    from smlib import mines
    from tallon import beamdoors
    by = {r.key: r for r in testrooms.rooms()}

    def colours(tileset: int) -> list[str]:
        return ([f"expect {0x7EC000 + 2 * (ln * 16 + i):06X} {mines._bgr555(c):04X}" for (ln, i), c in mines.COLOURS[tileset].items()]
                + [f"expect {0x7EC000 + 2 * (mines.PAINT_LINES[tileset] * 16 + i):06X} {c:04X}"
                   for i, c in enumerate(beamdoors.PURPLE, 1)])

    def redraw(screen_x: int) -> list[str]:   # the camera on a screen, redrawn (pause and unpause)
        return poke16(0x7E0911, screen_x * 256) + ["hold START 10", "wait 200", "hold START 10", "wait 200"]

    out = mines_station() + [f"expect {AREA} 0005", f"expect {ROOM_PTR} {room[testrooms.ENTRY]}", "expect 7E196E 0000",
                             f"shot {IMG_19D}_entrada.png"]
    out += lava_teleport(m[testrooms.ENTRY]["doors"][0], "R", 0, 1)
    for key, nxt, ts, tag in ((testrooms.BASE, testrooms.ROCK, mines.BASE_TILESET, "base"),
                              (testrooms.ROCK, testrooms.END, mines.ROCK_TILESET, "rocha")):
        r = by[key]
        wb = r.width * 16
        out += [f"expect {ROOM_PTR} {room[key]}", "expect 7E196E 0000"] + colours(ts) + give_beams(0)
        if key == testrooms.ROCK:   # the west plasma cap (on its side): Power and Wave leave it shut, the Plasma opens it
            shut_w = [f"poke {HEALTH} 63", "hold LEFT 60", "wait 20", f"expect {SAMUS_X} {2 * 16 + 5:04X}"]
            out += lava_place((2 + 4) * 16 + 8, 10 * 16 - 21, 0, "LEFT") + shut_w + redraw(0) + [
                f"shot {IMG_19D}_porta_de_plasma.png"]
            out += ["hold LEFT+X 2", "wait 30"] * 2 + shut_w
            out += give_beams(WAVE_BEAM) + ["hold LEFT+X 2", "wait 30"] * 2 + shut_w
            out += give_beams(PLASMA_BEAM) + ["hold LEFT+X 2", "wait 6", f"shot {IMG_19D}_porta_de_plasma_abrindo.png",
                                              "wait 120", "hold LEFT 90", "wait 200", f"expect {ROOM_PTR} {room[testrooms.BASE]}"]
            out += lava_teleport(m[testrooms.BASE]["doors"][1], "R", 0, 2) + [f"expect {ROOM_PTR} {room[key]}"] + give_beams(0)
        out += lava_place(8 * 16 + 8, 10 * 16 - 21, 0, "RIGHT") + redraw(0) + [f"shot {IMG_19D}_{tag}_oeste.png"]
        out += lava_place((wb - 8) * 16 + 8, 10 * 16 - 21, 0, "RIGHT")
        shut = [f"poke {HEALTH} 63", "hold RIGHT 90", "wait 20", f"expect {SAMUS_X} {(wb - 3) * 16 + 11:04X}"]
        back = ["hold LEFT 24", "wait 10", "hold RIGHT 1", "wait 10"]   # ~4 blocks off the cap: a point-blank shot misses it
        out += shut + [f"expect {0x7F0002 + 2 * (6 * wb + wb - 2):06X} {0xC000 | beamdoors.PAINT_METATILES[0x004]:04X}"]
        out += redraw(r.width - 1) + [f"shot {IMG_19D}_{tag}_leste.png"] + back
        out += ["hold RIGHT+X 2", "wait 30"] * 2 + shut
        out += give_beams(WAVE_BEAM) + back + ["hold RIGHT+X 2", "wait 6", f"shot {IMG_19D}_{tag}_onda_abrindo.png", "wait 120",
                                               "hold RIGHT 90", "wait 200", f"expect {ROOM_PTR} {room[nxt]}"]
    return out + [f"shot {IMG_19D}_fim.png"]


def tests_19d(m: dict) -> dict[str, list[str]]:
    """specs/19d: the test of the Mines looks' test build (manifest `m`)."""
    room = {k: f"{v['header'] & 0xFFFF:04X}" for k, v in m.items() if k != "banks"}
    return {"porta_de_plasma_mina": NEW_GAME + mines_doors(m, room)}


CROSSING_TEST = "nivel_cruza_banco_"


def crossing_rooms(m: dict) -> list[str]:
    return [k for k, v in m.items() if k != "banks" and (v["level"][0] & 0xFFFF) + v["level"][1] - 1 > 0xFFFF]


def room_def(key: str):
    return {**FRIGATE.by_key(), **TALLON.by_key(), **CHOZO.by_key(), **PHENDRANA.by_key(),
            **MINES.by_key()}[key]   # specs/12j: the Chozo's; 19f: the Mines'; 20f: Phendrana's


def level_layers(key: str) -> tuple[bytes, bytes]:
    """Layer-1 words and BTS of a room's level as tools/ builds it."""
    raw = decompress(room_def(key).level().compressed())[0]
    size = struct.unpack_from("<H", raw)[0]
    return raw[2:2 + size], raw[2 + size:2 + size + size // 2]


def tallon_door_path(start: str, goal: str) -> list[str]:
    by = TALLON.by_key()
    prev, queue = {start: None}, [start]
    while queue:
        k = queue.pop(0)
        for d in by[k].doors:
            if d.to_room not in prev:
                prev[d.to_room] = k
                queue.append(d.to_room)
    path = [goal]
    while prev[path[-1]]:
        path.append(prev[path[-1]])
    return list(reversed(path))


def chozo_door_path(goal: str) -> list[tuple[str, str]]:
    """specs/12j: the Chozo rooms from the North transport to `goal` (breadth first, in door order), each step (room, side of
    the door taken: 'T' = up through a ceiling door)."""
    by = CHOZO.by_key()
    prev, queue = {NORTH: None}, [NORTH]
    while queue:
        k = queue.pop(0)
        for d in by[k].doors:
            if d.to_room not in prev:
                prev[d.to_room] = (k, d.side)
                queue.append(d.to_room)
    path = [(goal, None)]
    while prev[path[-1][0]]:
        path.append(prev[path[-1][0]])
    return list(reversed(path))


def level_crossing_test(m: dict, room: dict, key: str) -> list[str]:
    if key in FRIGATE.by_key():
        out = NEW_GAME + traverse(route("hangar", key, False), room)
    elif key in CHOZO.by_key():
        # specs/12j: a Chozo room (the Sunchamber's level crosses $E0:FFFF): down the North elevator (as chozo_regiao_a_itens:
        # door_teleport to the Chozo West, onto_platform), then door_teleport room by room (up a ceiling door: rise_through
        # from the door's west column steering west, as measured for the Sunchamber Lobby's)
        out = (NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"] + lands_on_landing_site(room[LANDING_SITE])
               + chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
               + onto_platform(WEST) + ride_elevator(room, WEST, f"build/tests/{CROSSING_TEST}{key}_elevador.png"))
        path = chozo_door_path(key)
        for (a, side), (b, _) in zip(path, path[1:]):
            out += rise_through(m, room, a, b, 0, "LEFT") if side == "T" else door_teleport(m, a, b)
    elif key in MINES.by_key():
        # specs/19f: a Mines room (the Main Quarry's level crosses $E1:FFFF): down the Tallon's P43 elevator (mines_down), then
        # door_teleport room by room from the P0 (side doors: the Main Quarry is two doors away)
        by, prev, queue = MINES.by_key(), {MINES_EAST: None}, [MINES_EAST]
        while queue:
            k = queue.pop(0)
            for d in by[k].doors:
                if d.to_room not in prev and d.side in "LR":
                    prev[d.to_room] = k
                    queue.append(d.to_room)
        path = [key]
        while prev[path[-1]]:
            path.append(prev[path[-1]])
        out = (NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"] + lands_on_landing_site(room[LANDING_SITE])
               + mines_down(m, room, CROSSING_TEST + key) + chain_teleports(m, room, list(reversed(path))))
    elif key in PHENDRANA.by_key():
        # specs/20f: a Phendrana room (the Gravity Chamber's level crosses $E1:FFFF since the crater's region B moved the level
        # allocator): into the Frozen Pike (phendrana_pike: up to Phendrana's P0, a door_teleport), the Gravity Suit by RAM (the
        # Tallon's branch: a flooded room), then door_teleport room by room from the Pike (breadth first, every door: the
        # Tallon's branch; the Gravity Chamber is under the Chamber Access' floor door)
        by, prev, queue = PHENDRANA.by_key(), {FROZEN_PIKE: None}, [FROZEN_PIKE]
        while queue:
            k = queue.pop(0)
            for d in by[k].doors:
                if d.to_room not in prev and d.to_room in by:
                    prev[d.to_room] = k
                    queue.append(d.to_room)
        path = [key]
        while prev[path[-1]]:
            path.append(prev[path[-1]])
        out = (NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"] + lands_on_landing_site(room[LANDING_SITE])
               + phendrana_pike(m, room, CROSSING_TEST + key) + with_gravity_suit()
               + chain_teleports(m, room, list(reversed(path))))
    else:
        path = tallon_door_path(LANDING_SITE, key)
        out = (NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"] + lands_on_landing_site(room[LANDING_SITE])
               + with_gravity_suit())
        for a, b in zip(path, path[1:]):
            out += door_teleport(m, a, b)
    layer1, bts = level_layers(key)
    return out + [f"expect {ROOM_PTR} {room[key]}", "wait 120", f"expect {GAME_STATE} 0008", "peekw 7E0AFA", "wait 60",
                  "peekw 7E0AFA", f"peek {LEVEL_RAM:06X} {len(layer1)}", f"peek {BTS_RAM:06X} {len(bts)}",
                  f"shot build/tests/{CROSSING_TEST}{key}.png"]


def plm_cells(m: dict, key: str) -> set[tuple[int, int]]:
    """Blocks the room's PLMs may change (4 in a row or column from each PLM's block)."""
    rom = Rom.load(ROM)
    cells = set()
    for st in m[key]["states"]:
        if not rom.u16(st + 20):
            continue
        at = 0x8F0000 | rom.u16(st + 20)
        while rom.u16(at):
            x, y = rom.u8(at + 2), rom.u8(at + 3)
            cells |= {(x + k, y) for k in range(4)} | {(x, y + k) for k in range(4)}
            if rom.u16(at) == SAVE_PLM:
                # specs/20h: a save station draws its pedestal and the 2 columns of its tube over it (5 rows up: measured, Phendrana's
                # Save Station C, the first save room whose level crosses a bank, after the crater's Lair moved the level allocator)
                cells |= {(x + dx, y - dy) for dx in (0, 1) for dy in range(6)}
            at += 6
    return cells


def check_level_in_ram(stdout: str, m: dict, key: str) -> list[str]:
    layer1, bts = level_layers(key)
    rows = {a: bytes.fromhex(v) for a, v in re.findall(r"\] (7F0002|7F6402):((?: [0-9A-F]{2})+)", stdout)}
    ys = re.findall(r"7E0AFA = ([0-9A-F]{4})", stdout)[-2:]   # the test's two peeks (specs/12j: the elevator's expect too)
    fails = []
    if len(ys) != 2 or ys[0] != ys[1]:
        fails.append(f"FAIL {key}: a Samus não fica parada no chão (y {ys})")
    if rows.get("7F0002") is None or rows.get("7F6402") is None:
        return fails + [f"FAIL {key}: nível não lido da WRAM"]
    width = room_def(key).width * 16
    allowed = plm_cells(m, key)
    wrong = [(i % width, i // width) for i in range(len(bts))
             if rows["7F0002"][2 * i:2 * i + 2] != layer1[2 * i:2 * i + 2] or rows["7F6402"][i] != bts[i]]
    bad = [c for c in wrong if c not in allowed]
    if bad:
        fails.append(f"FAIL {key}: {len(bad)} blocos do nível na WRAM diferentes do da sala (ex.: {bad[:4]})")
    return fails


# specs/12m: the full chain of the two areas (was cadeia_completa_tallon_chozo). From the landing (as tallon_cadeia_completa), the
# 51 items of the Tallon and the Chozo Ruins in the order of the declared rounds (tallon/items.py and chozo/items.py
# Item.round; tools/validate.py walks the two areas together through the elevators), each walked or rolled into, its box
# closed with A, each lock on the way opened for real, the areas changed only by riding the three real elevators. The order
# is checked against the declarations when the script is built (FullChain.check_order). The shortcuts left are counted by
# FullChain.note and listed in full_chain's docstring and in specs/12m. specs/17j: the Magmoor's 7 items too (58), through its
# two elevators, and the chain split in three parts handed on by the emulator's savestates (CHAIN_PARTS, cadeia_completa_parte_*).
# specs/18n: Phendrana's 17 too (75), through its two elevators, with its two bosses fought for real (no boss bit by RAM), in
# four parts; at the end SM's ending screen draws the game's own count: 75%.
FULL_SHOT = "build/tests/12m"
MISSILE_KIND, ETANK_KIND, PB_KIND, SUPER_KIND = 0xEEDB, 0xEED7, 0xEEE3, 0xEEDF
GRAPPLE_KIND = 0xEF17        # specs/19m: the SM's Grapple Beam (tallon.items.GRAPPLE_BEAM)


def door_screen(key: str, d) -> tuple[str, int, int]:
    """The (room, screen x, screen y) of door `d` of room `key`."""
    r = built_room(key)
    return key, *{"L": (0, d.screen), "R": (r.width - 1, d.screen), "T": (d.screen, 0), "B": (d.screen, r.height - 1)}[d.side]


CHAIN_AREAS = ("tallon", "chozo", "magmoor", "phendrana", "mines")   # specs/17j: the areas of the full chain's items; specs/18n: Phendrana; specs/19m: the Mines


class FullChain:
    """The script of the full chain and what it has done so far: the item bits taken (to check that each item's bit is
    off before and on after, and the other bits of its 16-bit word as they should be), the rounds of the items taken, the
    ammo (missiles and power bombs: a red door takes 5 hits), the HUD selection, the photos and the shortcuts used."""

    def __init__(self, m: dict, room: dict):
        self.m, self.room = m, room
        self.out: list[str] = []
        self.bits: set[int] = set()
        self.taken: list[tuple[int, str, int]] = []      # (round, "tallon" | "chozo" | "magmoor" | "phendrana", index in its items.py)
        self.round = 0
        self.missiles = self.max_missiles = 0
        self.supers = self.max_supers = 0                # specs/18n: the Super Missile (Phendrana's Observatory)
        self.pbs = self.max_pbs = 0
        self.max_energy = 99
        self.xray = False
        self.grapple = False                             # specs/19m: the Grapple Beam (the Mines' Storage Depot B)
        self.hud = 0
        self.seq = 0
        self.shortcuts: dict[str, int] = {}
        self.screens: set[tuple[str, int, int]] = set()   # (room, screen x, screen y) of the doors door_teleport went through

    # --- bookkeeping -------------------------------------------------------------------------------------------------
    def note(self, what: str, n: int = 1) -> None:
        self.shortcuts[what] = self.shortcuts.get(what, 0) + n

    def shot(self, tag: str) -> str:
        self.seq += 1
        return f"shot {FULL_SHOT}_{self.seq:03d}_{tag}.png"

    def add(self, lines: list[str]) -> "FullChain":
        self.out += lines
        return self

    @staticmethod
    def items_of(area: str):
        """The items.py of `area` ("tallon", "chozo", specs/17j: "magmoor", specs/18n: "phendrana")."""
        from tallon import items as tallon_items
        from chozo import items as chozo_items
        from magmoor import items as magmoor_items
        from phendrana import items as phendrana_items
        from mines import items as mines_items
        return {"tallon": tallon_items, "chozo": chozo_items, "magmoor": magmoor_items, "phendrana": phendrana_items,
                "mines": mines_items}[area]

    @classmethod
    def item(cls, area: str, n: int):
        return cls.items_of(area).ITEMS[n]

    @classmethod
    def bit(cls, area: str, n: int) -> int:
        return cls.items_of(area).BITS[n]

    def word(self, bit: int) -> str:
        """`expect` of the 16 item bits from bit's byte on: exactly the bits taken so far."""
        byte = bit // 8
        v = sum(1 << (b - 8 * byte) for b in self.bits if 0 <= b - 8 * byte < 16)
        return f"expect {0x7ED870 + byte:06X} {v:04X}"

    def pre(self, area: str, n: int) -> list[str]:
        """Before walking into an item: its bit is off (and the bits around it as taken so far)."""
        b = self.bit(area, n)
        assert b not in self.bits, (area, n)
        return [self.word(b)]

    def post(self, area: str, n: int) -> list[str]:
        """After its box closed: its bit on, the round recorded, what it gives checked (ammo capacity, energy, equipment)."""
        it = self.item(area, n)
        b = self.bit(area, n)
        self.bits.add(b)
        self.taken.append((self.round, area, n))
        out = [f"expectbit {0x7ED870 + b // 8:06X} {1 << (b % 8):02X}", self.word(b), f"expect {GAME_STATE} 0008"]
        if it.kind == MISSILE_KIND:
            self.missiles += 5
            self.max_missiles += 5
            out += [f"expect {MISSILES} {self.missiles:04X}", f"expect {MAX_MISSILES} {self.max_missiles:04X}"]
        elif it.kind == PB_KIND:
            self.pbs += 5
            self.max_pbs += 5
            out += [f"expect {POWER_BOMBS} {self.pbs:04X}", f"expect {MAX_POWER_BOMBS} {self.max_pbs:04X}"]
        elif it.kind == ETANK_KIND:
            self.max_energy += 100
            out += [f"expect {MAX_ENERGY} {self.max_energy:04X}"]
        elif it.kind == SUPER_KIND:   # specs/18n
            self.supers += 5
            self.max_supers += 5
            out += [f"expect {SUPERS} {self.supers:04X}", f"expect {MAX_SUPERS} {self.max_supers:04X}"]
        elif it.kind == 0xEF0F:
            self.xray = True
        elif it.kind == GRAPPLE_KIND:   # specs/19m: the equipment bit, collected and on
            self.grapple = True
            out += [f"expectbit 7E09A3 {GRAPPLE_EQUIPMENT >> 8:02X}", f"expectbit 7E09A5 {GRAPPLE_EQUIPMENT >> 8:02X}"]
        return out

    def check_order(self) -> None:
        """The chain took every placed item of the three areas (specs/17j: the Magmoor's too; specs/18n: the four, Phendrana's
        too), each in its declared round (Item.round), rounds in order."""
        rounds = [r for r, _, _ in self.taken]
        if rounds != sorted(rounds):
            raise ValueError(f"cadeia 17j: itens fora da ordem das rodadas: {self.taken}")
        got = {(a, n): r for r, a, n in self.taken}
        want = {(a, n): it.round for a in CHAIN_AREAS for n, it in enumerate(self.items_of(a).ITEMS) if it.spot is not None}
        if got != want:
            diff = sorted(set(got.items()) ^ set(want.items()))
            raise ValueError(f"cadeia 17j: itens/rodadas diferentes das declaradas: {diff}")

    # --- moves ---------------------------------------------------------------------------------------------------------
    def tp(self, path: list[str]) -> "FullChain":
        """Shortcut: door_teleport through the consecutive rooms of `path` (only through doors with no lock or already
        opened in this run, as tallon_cadeia_completa)."""
        self.note("door_teleport", len(path) - 1)
        for a, b in zip(path, path[1:]):
            d = next(d for d in built_room(a).doors if d.to_room == b)
            self.screens.add(door_screen(a, d))
            self.screens.add(door_screen(b, built_room(b).doors[d.to_door]))
        return self.add(chain_teleports(self.m, self.room, path))

    def select(self, target: int) -> list[str]:
        """SELECT until the HUD item is `target` (0 = the beam): missiles (1), specs/18n: super missiles (2), power bombs (3),
        X-Ray (5), what she has."""
        order = ([0] + [1] * (self.max_missiles > 0) + [2] * (self.max_supers > 0) + [3] * (self.max_pbs > 0) + [4] * self.grapple
                 + [5] * self.xray)   # specs/19m: the grapple (4) between the power bombs and the X-Ray, SM's order
        out = []
        while self.hud != target:
            self.hud = order[(order.index(self.hud) + 1) % len(order)]
            out += ["hold SELECT 2", "wait 10", f"expect {HUD_ITEM} {self.hud:04X}"]
        return out

    def red_door(self, key: str, to: str, toward: str, tag: str) -> "FullChain":
        """Samus against key's red door to `to` (walking `toward`): a beam shot, then 5 missiles fired at it (refilled by RAM to 5 first if she
        has fewer: shortcut, counted), its bit on; back to the beam; she walks through into `to`."""
        d = next(d for d in built_room(key).doors if d.to_room == to)
        out = []
        if self.missiles < 5:
            out += poke16(0x7E09C6, 5)
            self.note("mísseis repostos por RAM")
            self.missiles = 5
        # a beam shot first: the first X after walking into the cap only turns her to aim (measured: no missile leaves)
        out += [f"expect {MISSILES} {self.missiles:04X}", self.shot(f"{tag}_fechada"), f"hold {toward}+X 2", "wait 20"]
        out += self.select(1)
        out += [f"poke {HEALTH} 63", f"hold {toward}+X 2", "wait 30"] * 5
        self.missiles -= 5
        out += ["wait 60", f"expectbit {0x7ED8B0 + d.lock_bit // 8:06X} {1 << (d.lock_bit % 8):02X}",
                f"expect {MISSILES} {self.missiles:04X}", self.shot(f"{tag}_aberta")]
        # back to the beam in the next room (an enemy's touch may push her through the open door meanwhile: measured)
        out += [f"hold {toward} 90", "wait 200", f"expect {ROOM_PTR} {self.room[to]}", f"expect {GAME_STATE} 0008"]
        out += self.select(0)
        return self.add(out)

    def red_floor_door(self, key: str, to: str, tag: str) -> "FullChain":
        """Samus standing on key's red floor door cap to `to`: a touch of direction (put there she would face the screen),
        missiles selected, 5 short jumps shooting down (one missile each: 5 hits open it, measured in specs/12l), its bit
        on, she drops into `to`; back to the beam there."""
        d = next(d for d in built_room(key).doors if d.to_room == to)
        out = []
        if self.missiles < 5:
            out += poke16(0x7E09C6, 5)
            self.note("mísseis repostos por RAM")
            self.missiles = 5
        out += [f"expect {MISSILES} {self.missiles:04X}", "hold RIGHT 1", "wait 20"] + self.select(1) + SHOOT_DOWN * 5
        self.missiles -= 5
        out += ["wait 300", f"expectbit {0x7ED8B0 + d.lock_bit // 8:06X} {1 << (d.lock_bit % 8):02X}",
                f"expect {MISSILES} {self.missiles:04X}", f"expect {ROOM_PTR} {self.room[to]}", f"expect {GAME_STATE} 0008",
                self.shot(tag)] + self.select(0)
        return self.add(out)

    def take_tallon(self, n: int, tag: str, start: int = -3, frames: int = 40, floor: int | None = None) -> "FullChain":
        """Tallon item n: Samus put by RAM `start` blocks from it (near_item: shortcut), she walks into it, A closes its box."""
        self.note("Samus posta perto do item")
        return self.add(self.pre("tallon", n) + near_item(n, start, floor) + [
            "wait 30", f"hold {'RIGHT' if start < 0 else 'LEFT'} {frames}", "wait 120", self.shot(tag), "wait 300",
            "hold A 2", "wait 120"] + self.post("tallon", n))

    def take_chozo(self, n: int, tag: str, start: int = -2, frames: int = 40) -> "FullChain":
        """Chozo item n: Samus put by RAM `start` blocks from it (chozo_near: shortcut), she walks into it, A closes its box."""
        self.note("Samus posta perto do item")
        return self.add(self.pre("chozo", n) + chozo_near(n, start) + [
            f"hold {'RIGHT' if start < 0 else 'LEFT'} {frames}", "wait 120", self.shot(tag), "wait 300", "hold A 2",
            "wait 120"] + self.post("chozo", n))

    def walked_into(self, area: str, n: int, tag: str, lines: list[str], wait: int = 120) -> "FullChain":
        """An item reached by real input (`lines` end walking or rolling into it): the box closed with A ~420 frames after
        (specs/18n: `wait` + 300 frames: Phendrana's region tests wait less before the photo, and a box not ready yet for the A
        takes the next held button instead, which the walk after it was measured with)."""
        return self.add(self.pre(area, n) + lines + [f"wait {wait}", self.shot(tag), "wait 300", "hold A 2", "wait 120"]
                        + self.post(area, n))

    def ride(self, key: str, tag: str) -> "FullChain":
        """The elevator of room `key`: Samus put on its platform (onto_platform: shortcut), DOWN / UP, the other area."""
        self.note("Samus posta na plataforma do elevador")
        return self.add(onto_platform(key) + ride_elevator(self.room, key, f"{FULL_SHOT}_{self.seq:03d}_{tag}.png"))


# the walks and jumps of the full chain, measured in the emulator (scratchpad s12m): frames of a held direction, or lists of
# inputs; the expected spot after each is checked where it is written
CHAIN_WEST_PAD = 30          # from the Morph Ball (Chozo West, walking east into it) back west onto the middle of the platform
CHAIN_ENTRANCE_WALK = 16     # chozo_walk cycles: the Ruins Entrance's pit and on through the door onto the Main Plaza's balcony
# the Main Plaza's balcony onto the platform under the T0 ceiling door, then up into the Nursery Access (a real climb,
# chozo_climb's jump: rise_through is not needed), a step east off the hole's edge before route B's walk (measured)
PLAZA_UP_TO_NURSERY = (["hold RIGHT 60", "wait 20", "hold A+LEFT 30", "hold LEFT 10", "wait 40", f"expect 7E0AFA {6 * 16 - 21:04X}",
                        "hold LEFT 20", "wait 20"] + climb_jump("RIGHT"))
# the Ruined Gallery from the Totem Access door: over the B1 hole onto the block, down to the basin's floor before the tunnel
# specs/14b: a run-up of 8 frames before the jump and "hold LEFT 50, wait 20" -> 80 / 40: since the Hive Totem's arena (won by
# RAM, arena_won_by_ram) she comes into the gallery standing at its R0 door, not jumping in as before, and the standing jump
# fell short into the floor door's hole (measured from the chain's own state there, scratchpad s14b)
# specs/14c (spec 15's leftover): the North Atrium's T0 platform from a fixed spot. The chain walked onto it from where the
# Nursery's and the atrium's blind walks left her (B_ATRIUM_TO_PLATFORM, B_PLATFORM_TO_DOOR): when the Nursery's wasp moved
# from 10 to 11 (spec 15's entry audit) she came into the atrium later, a crawler knocked her off the jump and the climb into
# the gallery landed 30 px east, into its floor door's hole. Now: west under the platform against the wall (x $15), up its
# west end, east to under the door's west half (x $7A, facing west): the climb starts from one spot (measured, scratchpad
# s14c/scripts/try_seq.py, from the chain's own state)
CHAIN_ATRIUM_TO_DOOR = ["hold LEFT 150", "wait 30", "expect 7E0AF6 0015", "hold RIGHT 8", "wait 10", "hold A 20", "hold A+RIGHT 30",
                        "wait 40", f"expect 7E0AFA {6 * 16 - 21:04X}", "hold RIGHT 24", "wait 20", "hold LEFT 2", "wait 20",
                        "expect 7E0AF6 007A"]
GALLERY_TO_TUNNEL = ["hold LEFT 8", "hold LEFT+A 30", "hold LEFT 60", "wait 30", "hold LEFT 80", "wait 40",
                     f"expect 7E0AFA {15 * 16 - 21:04X}"]
GALLERY_BACK_EAST = ["hold RIGHT 4", "hold RIGHT+A 20", "hold RIGHT 10", "wait 30", f"expect 7E0AFA {13 * 16 - 21:04X}",
                     "hold RIGHT 19", "hold RIGHT+A 30", "hold RIGHT 30", "wait 20", f"expect 7E0AFA {10 * 16 - 21:04X}"]
# the Hive Totem: from the totem's top (route B's climb) down into the east pool, out onto the step and the ledge, against
# the red door without a jump next to it (a jump there lands on its cap)
TOTEM_TO_RED_DOOR = ["hold RIGHT 80", "wait 20", "hold RIGHT+A 30", "hold RIGHT 150", "wait 30", "hold A+RIGHT 16", "hold RIGHT 80",
                     "wait 90", "expect 7E0AF6 02DB", f"expect 7E0AFA {10 * 16 - 21:04X}"]
BALL_RIGHT = ["hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_POSE}"]
BALL_LEFT = ["hold DOWN 2", "wait 10", "hold DOWN 2", "wait 30", f"expect {POSE} {BALL_LEFT_POSE}"]
STAND_UP = ["hold UP 2", "wait 30", "hold UP 2", "wait 30"]


def zig_jump(toward: str, walk: int, up: int, rest: int, shoot: int = 0) -> list[str]:
    """One step of a zigzag climb (measured): `shoot` shots straight up first (the Oculus crawling on the platform above
    knock her down otherwise), a walk of `walk` frames toward the edge, A held `up` frames straight up, then `rest` frames
    of A and the direction (she clears the platform's edge before drifting over it), the direction 10 more frames."""
    return ((["hold UP+X 2", "wait 20"] * shoot) + ([f"hold {toward} {walk}", "wait 20"] if walk else [])
            + [f"hold A {up}", f"hold A+{toward} {rest}", f"hold {toward} 10", "wait 50"])


# the Transport Access North: over the bump into the pit before the E-tank's tunnel
TAN_TO_PIT = ["hold RIGHT 200", "wait 30", "hold RIGHT+A 30", "hold RIGHT 100", "wait 30", f"expect 7E0AFA {12 * 16 - 21:04X}"]
# the Main Plaza from the one-way ledge's E-tank: west under the balcony's edge, back east off the block onto the stair's
# block, west off it onto the dais and down to the Ruined Shrine Access' red door
PLAZA_LEDGE_TO_SHRINE_DOOR = ["hold LEFT 200", "wait 30", "hold RIGHT 40", "wait 40", "hold LEFT 300", "wait 60",
                              "expect 7E0AF6 0025", f"expect 7E0AFA {26 * 16 - 21:04X}"]
# specs/12m: the Gathering Hall's east gallery climbed for real (was a RAM placement in chozo_regiao_d_rota): off the west
# ledge down the platforms to the stair's foot (row 22), then up the east zigzag (rows 18, 14, 10), over the cage's top
# (row 6) and down onto the R0 ledge
GH_EAST_GALLERY = (["hold RIGHT 195", "hold RIGHT+A 30", "hold RIGHT 4", "wait 60", f"expect 7E0AFA {18 * 16 - 21:04X}"]
                   + zig_jump("RIGHT", 12, 16, 24) + [f"expect 7E0AFA {14 * 16 - 21:04X}"]
                   + zig_jump("RIGHT", 3, 10, 30) + [f"expect 7E0AFA {10 * 16 - 21:04X}", "hold RIGHT 20", "wait 10",
                                                     "expect 7E0AF6 024B"])
GH_CAGE_TOP = ["hold A 8", "hold RIGHT+A 30", "hold RIGHT 10", "wait 60", f"expect 7E0AFA {6 * 16 - 21:04X}",
               "hold RIGHT 60", "wait 20", f"expect 7E0AFA {10 * 16 - 21:04X}"]
# specs/12m: the Watery Hall's stair climbed for real (was a RAM placement): from the L1 ledge onto the platforms (rows 22,
# 18, 14) and the upper gallery (row 10)
WATERY_STAIR = ["hold RIGHT 98", "hold RIGHT+A 60", "hold RIGHT 20", "wait 40", f"expect 7E0AFA {22 * 16 - 21:04X}",
                "hold RIGHT+A 60", "wait 40", f"expect 7E0AFA {18 * 16 - 21:04X}",
                "hold RIGHT+A 60", "wait 40", f"expect 7E0AFA {14 * 16 - 21:04X}",
                "hold RIGHT+A 60", "wait 40", f"expect 7E0AFA {10 * 16 - 21:04X}"]
WATERY_TO_CHARGE = ["hold RIGHT 30", "hold RIGHT+A 25", "hold RIGHT 10"]   # onto the pedestal into the Charge Beam
# off the gallery's west end onto the row-14 platform, east under the gallery down to the floor against the pool's wall
WATERY_TO_POOL = ["hold LEFT 100", "wait 40", f"expect 7E0AFA {14 * 16 - 21:04X}", "hold RIGHT 300", "wait 30",
                  f"expect 7E0AFA {29 * 16 - 21:04X}"]
# the Energy Core: from the L0 door over the two dry pools onto the step (row 10); from the step east under the T3 platform
# against the bomb slots' wall (a fixed spot), back west, onto the platform, under the door's west half, then
# chozo_climb's jump steered east up into the Burn Dome Access (a real climb)
EC_DOOR_TO_STEP = ["hold RIGHT 300", "hold RIGHT+A 30", "hold RIGHT 250", "wait 20", "hold RIGHT+A 30", "hold RIGHT 200", "wait 20",
                   "hold RIGHT+A 30", "hold RIGHT 20", "wait 30", f"expect 7E0AFA {10 * 16 - 21:04X}"]
ENERGY_CORE_TO_PLATFORM = ["hold RIGHT 120", "wait 20", "expect 7E0AF6 037B", "hold LEFT 36", "wait 20", "hold A 16", "hold A+RIGHT 24",
                           "hold RIGHT 10", "wait 50", f"expect 7E0AFA {6 * 16 - 21:04X}", "hold RIGHT 14", "wait 20"]


def fc_round_0(fc: FullChain) -> None:
    """Round 0, the Power Beam only. Tallon: the Landing Site's missile (tallon_first_missile), WALKING west (tallon_walk,
    as tallon_rota_mvp) to the Chozo West, the Morph Ball walked into, back west onto the platform (walking: no RAM), DOWN.
    Chozo: walking the Ruins Entrance onto the Main Plaza's balcony, onto the platform and up the T0 ceiling door (a real
    climb), route B's walk (chozo_regiao_b_rota) round the Nursery loop and up the totem: the Hive Totem missile."""
    m, room = fc.m, fc.room
    fc.add(fc.pre("tallon", 0) + tallon_first_missile("12m_missil") + ["wait 322"])
    fc.add(fc.post("tallon", 0))
    fc.add(tallon_walk("LEFT", "12m_ida", 50) + [f"expect {ROOM_PTR} {room[WEST]}", f"expect 7E0AF6 {0x15:04X}"])
    fc.walked_into("tallon", 17, "0_morph", ["hold RIGHT 80"])
    fc.add([f"expect {COLLECTED_ITEMS} {MORPH_BALL_EQUIPMENT:04X}", f"hold LEFT {CHAIN_WEST_PAD}", "wait 30",
            f"expect {ELEVATOR_FLAGS} 0001"])
    fc.add(ride_elevator(room, WEST, f"{FULL_SHOT}_0_descendo.png") + CHOZO_NORTH_TO_ENTRANCE
           + [f"expect {ROOM_PTR} {room['chozo_ruins_entrance']}"])
    fc.add(chozo_walk("RIGHT", CHAIN_ENTRANCE_WALK, "chozo_main_plaza", room)[:-3] + ["wait 200", f"expect {ROOM_PTR} {room['chozo_main_plaza']}",
                                                                                     f"expect 7E0AFA {10 * 16 - 21:04X}"])
    fc.add(PLAZA_UP_TO_NURSERY + [f"expect {ROOM_PTR} {room['chozo_nursery_access']}", "hold RIGHT 14", "wait 10"]
           + B_ACCESS_TO_EYON + [f"expect {ROOM_PTR} {room['chozo_eyon_tunnel']}", f"poke {HEALTH} 63"]
           + B_EYON_TO_PLATFORM + [f"expect 7E0AFA {6 * 16 - 21:04X}"] + B_PLATFORM_TO_DOOR + climb_jump("LEFT")
           + [f"expect {ROOM_PTR} {room['chozo_ruined_nursery']}", f"expect 7E0AFA {13 * 16 - 21:04X}"]
           + chozo_walk("LEFT", B_NURSERY_TO_ATRIUM, "chozo_north_atrium", room)
           + chozo_walk("LEFT", B_ATRIUM_WALK, "chozo_north_atrium", room)[:-3] + CHAIN_ATRIUM_TO_DOOR + climb_jump("LEFT")
           + [f"expect {ROOM_PTR} {room['chozo_ruined_gallery']}", f"expect 7E0AFA {13 * 16 - 21:04X}", fc.shot("0_galeria")]
           + B_GALLERY_OVER_THE_HOLE + [f"expect {ROOM_PTR} {room['chozo_totem_access']}"]
           + chozo_walk("RIGHT", B_TOTEM_ACCESS, "chozo_hive_totem", room)
           # specs/14b: the Hive Mecha's arena blocks the totem's missile: won by RAM as she comes in (its kill count, the
           # hives deleted; the real fight is chozo_hive_mecha), as epic 14 decision 9 says
           + arena_won_by_ram("chozo_hive_totem")
           + chozo_walk("RIGHT", B_TO_THE_TOTEM, "chozo_hive_totem", room)[:-3] + ["wait 30"])
    fc.note("energia por RAM nas caminhadas (chozo_walk, tallon_walk)")
    fc.note("arena vencida por RAM (cota de mortes): Hive Mecha")
    fc.walked_into("chozo", 14, "0_missil_totem", B_TOTEM_CLIMB)


def fc_round_1_chozo(fc: FullChain) -> None:
    """Round 1 in the Chozo (+ missiles and the Morph Ball), every room WALKED but one door_teleport stretch: back to the
    Ruined Gallery (its tunnel: the ball), the totem, its red door, the Transport Access North (the pit's tunnel: the
    E-tank), route B's way down the Magmoor well, the Vault and the Plaza Access onto the one-way ledge (the E-tank); down
    the plaza to the Ruined Shrine Access' red door, the shrine's floor missile (route A's walk and fight); by door_teleport
    to the Ruined Fountain Access, then route C's walk: the fountain, the Arboretum Access' U and red door, down the
    Arboretum to its R2 red door, the Gathering Hall Access, the Gathering Hall's east gallery CLIMBED (GH_EAST_GALLERY), the
    Watery Hall Access and its red door, the Watery Hall's stair CLIMBED (WATERY_STAIR): the Charge Beam, the pool's missile
    (the ball); door_teleport to the East Atrium, route D's walk to the Energy Core's step, onto the platform and up the T3
    ceiling door (a real climb), the Burn Dome Access' tunnel, the Burn Dome's stand: its missile (Prime's Bombs); specs/14d:
    it starts the Incinerator Drone's fight, won by RAM (noted)."""
    m, room = fc.m, fc.room
    fc.round = 1
    # specs/14c: the walk can end against the Totem Access' closed L0 cap (it did once the Nursery's wasp moved, spec 15's
    # leftover): one more shot and a step through it (from the gallery's side, as the walk did before, she arrives standing at
    # its R0 door, GALLERY_TO_TUNNEL's start)
    fc.add(chozo_walk("LEFT", 44, "chozo_ruined_gallery", room)[:-3] + ["hold LEFT+X 2", "hold LEFT 30", "wait 200",
                                                                         f"expect {ROOM_PTR} {room['chozo_ruined_gallery']}"])
    fc.walked_into("chozo", 11, "1_galeria_tunel", GALLERY_TO_TUNNEL + BALL_LEFT + ["hold LEFT 120"])
    fc.add(["hold RIGHT 80", "wait 30"] + STAND_UP + GALLERY_BACK_EAST
           + chozo_walk("RIGHT", 6, "chozo_totem_access", room)[:-3] + ["wait 200", f"expect {ROOM_PTR} {room['chozo_totem_access']}"]
           + chozo_walk("RIGHT", B_TOTEM_ACCESS, "chozo_hive_totem", room)
           + chozo_walk("RIGHT", B_TO_THE_TOTEM, "chozo_hive_totem", room)[:-3] + ["wait 30"] + B_TOTEM_CLIMB + ["wait 60"]
           + TOTEM_TO_RED_DOOR)
    fc.red_door("chozo_hive_totem", "chozo_transport_access_north", "RIGHT", "1_porta_totem")
    fc.walked_into("chozo", 13, "1_tan_etank", TAN_TO_PIT + BALL_RIGHT + ["hold RIGHT 120"])
    fc.add(["hold LEFT 80", "wait 30"] + STAND_UP + chozo_walk("RIGHT", 16, "chozo_transport_magmoor_north", room)[:-3]
           + ["wait 200", f"expect {ROOM_PTR} {room['chozo_transport_magmoor_north']}"]
           + B_DOWN_THE_WELL + [f"expect 7E0AFA {26 * 16 - 21:04X}"]
           + chozo_walk_paused("LEFT", B_WELL_TO_VAULT, B_WELL_SPLIT, B_WELL_PAUSE, "chozo_vault", room)
           + [f"expect 7E0AFA {6 * 16 - 21:04X}"]
           + B_VAULT_TO_PLAZA_ACCESS + [f"expect {ROOM_PTR} {room['chozo_plaza_access']}"]
           + chozo_walk("LEFT", B_PLAZA_ACCESS_DOWN, "chozo_main_plaza", room) + [f"expect 7E0AFA {6 * 16 - 21:04X}"])
    fc.walked_into("chozo", 3, "1_praca_etank", ["hold LEFT 30"])
    fc.add(PLAZA_LEDGE_TO_SHRINE_DOOR)
    fc.red_door("chozo_main_plaza", "chozo_ruined_shrine_access", "LEFT", "1_porta_shrine")
    fc.walked_into("chozo", 4, "1_shrine_chao", chozo_walk("LEFT", CHOZO_ACCESS_TO_SHRINE, "chozo_ruined_shrine", room) + SHRINE_FIGHT)
    fc.tp(["chozo_ruined_shrine", "chozo_ruined_shrine_access", "chozo_main_plaza", FOUNTAIN])
    fc.add(chozo_walk("RIGHT", C_RFA_WALK, "chozo_ruined_fountain", room)[:-3]
           + ["wait 150", f"expect {ROOM_PTR} {room['chozo_ruined_fountain']}", f"expect {GAME_STATE} 0008", f"poke {HEALTH} 63"]
           + C_OVER_THE_HOLE + [f"expect {ROOM_PTR} {room['chozo_ruined_fountain']}", f"expect 7E0AFA {13 * 16 - 21:04X}"]
           + chozo_walk("RIGHT", C_FOUNTAIN_WALK, "chozo_arboretum_access", room)
           + chozo_walk("RIGHT", C_AA_DOWN, "chozo_arboretum_access", room) + [f"expect 7E0AFA {28 * 16 - 21:04X}"]
           + C_AA_CLIMB + [f"expect 7E0AFA {10 * 16 - 21:04X}"])
    fc.red_door("chozo_arboretum_access", "chozo_arboretum", "RIGHT", "1_porta_arboretum")
    fc.add(C_ARB_DOWN + [f"expect {ROOM_PTR} {room['chozo_arboretum']}"])
    fc.red_door("chozo_arboretum", "chozo_gathering_hall_access", "RIGHT", "1_porta_gha")
    fc.add(chozo_walk("RIGHT", C_GHA_WALK, "chozo_gathering_hall", room) + GH_EAST_GALLERY + GH_CAGE_TOP + [fc.shot("1_galeria_leste")]
           + ["hold RIGHT+X 2", "hold RIGHT 100", "wait 200", f"expect {ROOM_PTR} {room['chozo_watery_hall_access']}"]
           + chozo_walk("RIGHT", D_WHA_WALK, "chozo_watery_hall_access", room)[:-3] + ["hold RIGHT 150", "wait 30"])
    fc.red_door("chozo_watery_hall_access", "chozo_watery_hall", "RIGHT", "1_porta_watery")
    fc.add(WATERY_STAIR + [fc.shot("1_watery_galeria")])
    fc.walked_into("chozo", 7, "1_charge", WATERY_TO_CHARGE)
    fc.add([f"expectbit 7E09A7 {CHARGE_EQUIPMENT >> 8:02X}", f"expectbit 7E09A9 {CHARGE_EQUIPMENT >> 8:02X}"])
    fc.walked_into("chozo", 21, "1_watery_poca", WATERY_TO_POOL + BALL_RIGHT + ["hold RIGHT 120"])
    fc.add(["hold LEFT 80", "wait 30"] + STAND_UP)
    fc.tp(["chozo_watery_hall", "chozo_watery_hall_access", "chozo_gathering_hall", "chozo_east_atrium"])
    fc.add(chozo_walk("RIGHT", D_EA_WALK, "chozo_east_atrium", room)[:-3] + to_the_door("RIGHT", "chozo_energy_core_access", room)
           + chozo_walk("RIGHT", D_ECA_WALK, "chozo_energy_core_access", room)[:-3] + to_the_door("RIGHT", "chozo_energy_core", room)
           + chozo_walk("RIGHT", D_EC_WALK, "chozo_energy_core", room) + ENERGY_CORE_TO_PLATFORM + climb_jump("RIGHT")
           + [f"expect {ROOM_PTR} {room['chozo_burn_dome_access']}", f"expect 7E0AFA {13 * 16 - 21:04X}"] + BALL_RIGHT
           + ["hold RIGHT 90", "wait 30"] + STAND_UP + [f"expect 7E0AFA {13 * 16 - 21:04X}", "hold A+RIGHT 30", "hold RIGHT 10", "wait 30"]
           + chozo_walk("RIGHT", D_BDA_WALK, "chozo_burn_dome", room))
    fc.walked_into("chozo", 24, "1_burn_dome_suporte", chozo_walk("RIGHT", D_TO_THE_STAND, "chozo_burn_dome", room)[:-3])
    # specs/14d: the missile started the Incinerator Drone's fight (the door shut): won by RAM (its kill count, every enemy
    # deleted; the real fight is chozo_incinerator_drone), as epic 14 decision 9 says
    fc.add(arena_won_by_ram("chozo_burn_dome") + ["expectbit 7ED829 10", "expect 7E07F5 0000"])
    fc.note("arena vencida por RAM (cota de mortes, depois do míssil do suporte): Incinerator Drone")
CHAIN_NORTH_PAD = 46         # from the North transport's west wall back east onto the middle of the platform


def chain_ride_up_north(fc: FullChain, frm: list[str], tag: str) -> None:
    """Shortcut: door_teleport along `frm` to the Chozo's North transport; WALKING west to its wall and back east onto the
    platform (no RAM), UP: the Tallon's Chozo West."""
    fc.tp(frm + [NORTH])
    fc.add(["hold LEFT 200", "wait 30", "expect 7E0AF6 0015", f"hold RIGHT {CHAIN_NORTH_PAD}", "wait 30", f"expect {ELEVATOR_FLAGS} 0001"]
           + ride_elevator(fc.room, NORTH, f"{FULL_SHOT}_{tag}_subindo.png"))


def chain_red_door_ahead(fc: FullChain, key: str, to: str, tag: str) -> None:
    """Shortcut: Samus put by RAM in front of key's red door to `to` (stand_before_door), then fc.red_door."""
    fc.note("Samus posta diante de porta")
    toward = "LEFT" if next(d for d in built_room(key).doors if d.to_room == to).side == "L" else "RIGHT"
    fc.add(stand_before_door(key, to) + beam_door_shut(key, to))
    fc.red_door(key, to, toward, tag)


def fc_round_1_up(fc: FullChain) -> None:
    chain_ride_up_north(fc, ["chozo_burn_dome", "chozo_burn_dome_access", "chozo_energy_core", "chozo_energy_core_access",
                             "chozo_east_atrium", "chozo_gathering_hall", "chozo_gathering_hall_access", "chozo_arboretum",
                             "chozo_arboretum_access", "chozo_ruined_fountain", FOUNTAIN, "chozo_main_plaza", "chozo_ruins_entrance"], "1")


def fc_round_1_tallon(fc: FullChain) -> None:
    """Round 1 in the Tallon (as tallon_cadeia_completa's): the three red doors opened with missiles (the Temple Security's,
    the Root Tunnel's, the Waterfall's: the missiles picked up so far, no refill), the Bombs (Artifact Temple), the Tunnel B
    missile, the Wave (Magmoor East), the Crash Site missile."""
    m, room = fc.m, fc.room
    fc.tp([WEST, "tallon_tunnel_a", "tallon_canyon", "tallon_canyon_cavern", "tallon_landing_site", "tallon_temple_hall",
           "tallon_temple_security"])
    chain_red_door_ahead(fc, "tallon_temple_security", "tallon_temple_lobby", "1_porta_vermelha_templo")
    fc.tp(["tallon_temple_lobby", "tallon_artifact_temple"])
    fc.add(tallon_look(15, 54, 0, 731, f"{FULL_SHOT}_1_bombas_sala.png"))
    fc.take_tallon(item_index("tallon_artifact_temple"), "1_bombas", start=2, frames=24)
    fc.add([f"expect {COLLECTED_ITEMS} {MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT:04X}"])
    # back to the gunship by RAM (load station 0, as tallon_cadeia_completa: door_teleport up through the temple's ceiling
    # door leaves her in the temple, measured again here)
    fc.note("volta à nave por RAM (estação 0)")
    fc.add(chain_home(room))
    fc.tp(["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_root_tunnel"])
    chain_red_door_ahead(fc, "tallon_root_tunnel", "tallon_root_cave", "1_porta_vermelha_raizes")
    fc.tp(["tallon_root_cave", "tallon_tunnel_b"])
    fc.take_tallon(item_index("tallon_tunnel_b"), "1_missil_tunnel_b")
    fc.tp(["tallon_tunnel_b", "tallon_transport_magmoor_east"])
    fc.take_tallon(lock_item("tallon_transport_magmoor_east"), "1_wave")
    fc.add(has_beams(WAVE_BEAM | CHARGE_EQUIPMENT))
    fc.tp(["tallon_transport_magmoor_east", "tallon_tunnel_b", "tallon_root_cave", "tallon_root_tunnel", "tallon_canyon",
           "tallon_canyon_cavern", "tallon_landing_site", "tallon_waterfall_cavern"])
    chain_red_door_ahead(fc, "tallon_waterfall_cavern", "tallon_crash_site", "1_porta_vermelha_cachoeira")
    fc.add([f"poke {HEALTH} 63"])
    fc.take_tallon(item_index("tallon_crash_site"), "1_missil_crash_site")


def fc_round_2_tallon(fc: FullChain) -> None:
    """Round 2 in the Tallon (+ the Bombs, the Wave, the Charge Beam), as tallon_cadeia_completa's: the Tallon Canyon's 2 bomb
    blocks bombed in the ball (Samus put on the platform's west end: shortcut), up into the Gully, through it to the
    Landing Site's ledge and into the Alcove: the Space Jump."""
    m, room = fc.m, fc.room
    fc.round = 2
    b1, b2 = level_block("tallon_canyon", 53, 5), level_block("tallon_canyon", 54, 5)
    block = f"{0xF000 | 0x058:04X}"
    fc.tp(["tallon_crash_site", "tallon_waterfall_cavern", "tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon"])
    fc.note("Samus posta na ponta da plataforma da Tallon Canyon")
    fc.add(poke16(0x7E091D, CANYON_BG1_OFFSETS[0]) + poke16(0x7E091F, CANYON_BG1_OFFSETS[1])
           + tallon_look(52, 6, 640, 0, f"{FULL_SHOT}_2_blocos_de_bomba.png")
           + ["hold RIGHT 30", "wait 20", f"expect {SAMUS_X} {TUNNEL_WEST_X:04X}", f"expect {b1:06X} {block}", f"expect {b2:06X} {block}"]
           + BALL_RIGHT + ["hold RIGHT 20", "hold X 2", "wait 90", f"expect {b1:06X} 00FF", "hold RIGHT 20", "wait 10",
                           "hold RIGHT 4", "hold X 2", "wait 90", f"expect {b2:06X} 00FF", fc.shot("2_tunel_aberto"),
                           "hold RIGHT 30", "wait 10"] + STAND_UP + [f"expect {POSE} {STAND_POSE}"]
           + ["hold LEFT 40", "wait 20", f"expect {SAMUS_X} {GULLY_TUNNEL_X:04X}"] + GULLY_UP
           + [f"expect {ROOM_PTR} {room['tallon_gully']}", fc.shot("2_gully")])
    fc.tp(["tallon_gully", "tallon_landing_site", "tallon_alcove"])
    fc.take_tallon(item_index("tallon_alcove"), "2_space_jump")
    fc.add([f"expectbit 7E09A5 {SPACE_JUMP_EQUIPMENT >> 8:02X}"])


CHAIN_WEST_PAD_FROM_WALL = 52
# the North Atrium from its R0 door: over the bump, onto the T0 platform, under the door's west half, up (chozo_climb's jump)
ATRIUM_TO_GALLERY = (["hold LEFT 60", "hold LEFT+A 30", "hold LEFT 60", "wait 30", f"expect 7E0AFA {8 * 16 - 21:04X}",
                      "hold LEFT 32", "wait 10", "hold A+LEFT 30", "hold LEFT 10", "wait 30", f"expect 7E0AFA {6 * 16 - 21:04X}",
                      "hold LEFT 16", "wait 20"] + climb_jump("LEFT"))   # from the Chozo West's west wall back east onto the middle of the platform


def chain_ride_down_west(fc: FullChain, frm: list[str], tag: str) -> None:
    """Shortcut: door_teleport along `frm` to the Tallon's Chozo West; WALKING down its steps to the west wall and back east
    onto the platform (no RAM), DOWN: the Chozo's North transport."""
    fc.tp(frm + [WEST])
    fc.add(["hold LEFT 400", "wait 30", f"hold RIGHT {CHAIN_WEST_PAD_FROM_WALL}", "wait 30", f"expect {ELEVATOR_FLAGS} 0001"]
           + ride_elevator(fc.room, WEST, f"{FULL_SHOT}_{tag}_descendo.png"))


def chain_bomb_tunnel(fc: FullChain, n: int, start: int, toward: str, block: tuple[int, int], tag: str, back: int = 80,
                      clear: bool = False) -> None:
    """Chozo item n behind a bomb block (b_bomb_tunnel: Samus put by RAM `start` blocks from it, she walks to the block, the
    Power Beam leaves it, ball, a bomb breaks it, she rolls in; back out and stands). `clear`: the room's enemies deleted by
    RAM first (shortcut: one sits where she stands and knocks her out of the ball)."""
    fc.note("Samus posta perto do item")
    if clear:
        fc.note("inimigos da sala apagados por RAM")
        fc.add(clear_room_enemies(fc.item("chozo", n).room))
    fc.add(fc.pre("chozo", n) + b_bomb_tunnel(n, start, toward, block, tag, back, img=FULL_SHOT))
    fc.add(fc.post("chozo", n))


def fc_round_2_chozo_a(fc: FullChain) -> None:
    """Round 2 in the Chozo, first part (+ the Bombs): down the North elevator (walking onto the platform), walking the Ruins
    Entrance and up the Main Plaza's T0 (a real climb) into region B's loop (route B's walk): the Ruined Nursery's bomb
    block (its missile), the Ruined Gallery's missile wall (a bomb block)."""
    from chozo import layouts as chozo_layouts
    m, room = fc.m, fc.room
    chain_ride_down_west(fc, ["tallon_alcove", "tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a"], "2")
    fc.add(CHOZO_NORTH_TO_ENTRANCE + [f"expect {ROOM_PTR} {room['chozo_ruins_entrance']}"]
           + chozo_walk("RIGHT", CHAIN_ENTRANCE_WALK, "chozo_main_plaza", room)[:-3]
           + ["wait 200", f"expect {ROOM_PTR} {room['chozo_main_plaza']}", f"expect 7E0AFA {10 * 16 - 21:04X}"]
           + PLAZA_UP_TO_NURSERY + [f"expect {ROOM_PTR} {room['chozo_nursery_access']}", "hold RIGHT 14", "wait 10"]
           + B_ACCESS_TO_EYON + [f"expect {ROOM_PTR} {room['chozo_eyon_tunnel']}", f"poke {HEALTH} 63"]
           + B_EYON_TO_PLATFORM + [f"expect 7E0AFA {6 * 16 - 21:04X}"] + B_PLATFORM_TO_DOOR + climb_jump("LEFT")
           + [f"expect {ROOM_PTR} {room['chozo_ruined_nursery']}"])
    chain_bomb_tunnel(fc, chozo_item_index("chozo_ruined_nursery"), -7, "RIGHT", chozo_layouts.NURSERY_BOMB, "2_nursery", clear=True)
    fc.tp(["chozo_ruined_nursery", "chozo_north_atrium"])
    fc.add(ATRIUM_TO_GALLERY
           + [f"expect {ROOM_PTR} {room['chozo_ruined_gallery']}", f"expect 7E0AFA {13 * 16 - 21:04X}"])
    wall = [n for n, it in enumerate(__import__("chozo.items", fromlist=["ITEMS"]).ITEMS) if it.room == "chozo_ruined_gallery"][1]
    chain_bomb_tunnel(fc, wall, -3, "RIGHT", chozo_layouts.GALLERY_BOMB, "2_galeria_parede", 30)


def fc_round_2_chozo_b(fc: FullChain) -> None:
    """Round 2 in the Chozo, second part: the Vault's cage (a bomb block: its missile), the Ruined Shrine's lower tunnel (a
    bomb block: its missile), by door_teleport round region B's loop and down to the plaza; walking from the one-way ledge
    to the Ruined Shrine Access' door (opened in round 1)."""
    from chozo import layouts as chozo_layouts
    m, room = fc.m, fc.room
    fc.tp(["chozo_ruined_gallery", "chozo_totem_access", "chozo_hive_totem", "chozo_transport_access_north",
           "chozo_transport_magmoor_north", "chozo_vault_access", "chozo_vault"])
    chain_bomb_tunnel(fc, chozo_item_index("chozo_vault"), -8, "RIGHT", chozo_layouts.VAULT_BOMB, "2_vault")
    fc.tp(["chozo_vault", "chozo_plaza_access", "chozo_main_plaza"])
    fc.add(PLAZA_LEDGE_TO_SHRINE_DOOR + ["hold LEFT+X 2", "wait 20", "hold LEFT 90", "wait 200",
                                         f"expect {ROOM_PTR} {room['chozo_ruined_shrine_access']}"])
    fc.tp(["chozo_ruined_shrine_access", "chozo_ruined_shrine"])
    chain_bomb_tunnel(fc, 6, 6, "LEFT", chozo_layouts.SHRINE_BOMB, "2_shrine_tunel", clear=True)


# specs/12m: the Arboretum's crown climbed for real (was a RAM placement in chozo_regiao_c_rota): from the L0 ledge east down
# onto the row-17 branch, up onto the row-12 step and the crown (row 10), east against the chamber's wall
ARBORETUM_CROWN = ["hold RIGHT 150", "hold RIGHT+A 40", "hold RIGHT 4", "wait 50", f"expect 7E0AFA {12 * 16 - 21:04X}",
                   "hold RIGHT+A 25", "hold RIGHT 4", "wait 40", f"expect 7E0AFA {10 * 16 - 21:04X}",
                   "hold RIGHT 150", "wait 20", "expect 7E0AF6 023B"]


def fc_round_2_chozo_c(fc: FullChain) -> None:
    """Round 2 in the Chozo, third part: by door_teleport to the Arboretum; its crown CLIMBED (ARBORETUM_CROWN), ball, a bomb
    breaks the block of the tunnel (the copa), the R0 chamber, its red door, the Sunchamber Lobby onto the T0 platform and up
    (a real climb), the Sunchamber Access and the arena walked (route C's); specs/14c: Flaahgra won by RAM (noted), the
    Varia Suit on the pit's floor."""
    m, room = fc.m, fc.room
    fc.tp(["chozo_ruined_shrine", "chozo_ruined_shrine_access", "chozo_main_plaza", FOUNTAIN, "chozo_ruined_fountain",
           "chozo_arboretum_access", "chozo_arboretum"])
    fc.add(ARBORETUM_CROWN + [fc.shot("2_copa")] + BALL_RIGHT
           + ["hold RIGHT 30", "wait 10", "hold X 2", "wait 100", f"expect {level_block('chozo_arboretum', 37, 9):06X} 00FF",
              "hold RIGHT 80", "wait 30"] + STAND_UP + [fc.shot("2_camara")])
    fc.red_door("chozo_arboretum", "chozo_sunchamber_lobby", "RIGHT", "2_porta_lobby")
    fc.add(C_LOBBY_TO_PLATFORM + [f"expect 7E0AFA {6 * 16 - 21:04X}"] + climb_jump("LEFT")
           + [f"expect {ROOM_PTR} {room['chozo_sunchamber_access']}", f"expect 7E0AFA {13 * 16 - 21:04X}"]
           + out_of_arena(chozo_walk("LEFT", C_ACCESS_WALK, "chozo_sunchamber", room))
           # specs/14c: Flaahgra (the Spore Spawn) blocks the Varia Suit and the door to the Sun Tower Access: won by RAM as
           # she comes in (its health 0; it dies at its first touch, by its own code), as epic 14 decision 9 says
           + flaahgra_won_by_ram() + C_TO_THE_PIT + ["expectbit 7ED829 42"])
    fc.note("arena vencida por RAM (vida 0, morre no primeiro toque): Flaahgra")
    fc.walked_into("chozo", 8, "2_varia", C_PIT_TO_VARIA)
    fc.add(["wait 80", f"expectbit 7E09A2 {VARIA_EQUIPMENT:02X}", f"expectbit 7E09A4 {VARIA_EQUIPMENT:02X}"])


# specs/12m: the Sun Tower's east zigzag climbed for real (was a RAM placement on its top passage in chozo_regiao_c_rota):
# from the R2 door's floor (row 42: against its cap first, a fixed spot) up the platforms of rows 37, 32, 27, 22, 17, 12 onto the column's top (row 8), shooting
# the Oculus above before the upper jumps; then west off the column down the shaft to the L1 door (Prime's free way down)
SUN_TOWER_CLIMB = (["hold RIGHT 30", "wait 20", "expect 7E0AF6 01DB", "hold LEFT 52", "wait 10", "hold RIGHT+A 60", "hold RIGHT 4", "wait 50", f"expect 7E0AFA {37 * 16 - 21:04X}"]
                   + zig_jump("LEFT", 20, 22, 18) + [f"expect 7E0AFA {32 * 16 - 21:04X}"]
                   + zig_jump("RIGHT", 21, 16, 24) + [f"expect 7E0AFA {27 * 16 - 21:04X}"]
                   + zig_jump("LEFT", 9, 16, 24, 6) + [f"expect 7E0AFA {22 * 16 - 21:04X}"]
                   + zig_jump("RIGHT", 9, 16, 24, 6) + [f"expect 7E0AFA {17 * 16 - 21:04X}"]
                   + zig_jump("LEFT", 9, 16, 24, 6) + [f"expect 7E0AFA {12 * 16 - 21:04X}"]
                   + zig_jump("LEFT", 21, 22, 18, 6) + [f"expect 7E0AFA {8 * 16 - 21:04X}"])


CHAIN_STA_WALK = 46          # the Sun Tower Access walked from the Sunchamber's door (C_STA_WALK, 40, was from a door_teleport)
# specs/12m: the Sunchamber's arena climbed for real (chozo_regiao_c_rota went to the Sun Tower Access by door_teleport: "the
# arena's zigzag up to the L0 is the validator's"); specs/14c, the new arena (measured again, s14c/scripts/try_seq.py): from
# the pit's west wall (a fixed spot: the Varia Suit leaves her where she takes it, from either side) east up out of the pit
# along the hall, up onto the row-37 platform from its east side, the zigzag's platforms of rows 32, 27, 22, 17, 12 and onto
# the L0 gallery (row 10)
SUNCHAMBER_TO_STA = (["hold LEFT 120", "wait 20", "expect 7E0AF6 0015", "hold RIGHT 78", "hold RIGHT+A 20", "hold RIGHT 128",
                      "wait 20", f"expect 7E0AFA {42 * 16 - 21:04X}",
                      "hold A 4", "hold A+LEFT 60", "hold LEFT 6", "wait 50", f"expect 7E0AFA {37 * 16 - 21:04X}"]
                     + zig_jump("LEFT", 24, 16, 18) + [f"expect 7E0AFA {32 * 16 - 21:04X}"]
                     + zig_jump("RIGHT", 4, 10, 30) + [f"expect 7E0AFA {27 * 16 - 21:04X}"]
                     + zig_jump("LEFT", 8, 16, 18) + [f"expect 7E0AFA {22 * 16 - 21:04X}"]
                     + zig_jump("RIGHT", 4, 10, 30) + [f"expect 7E0AFA {17 * 16 - 21:04X}"]
                     + zig_jump("LEFT", 8, 16, 18) + [f"expect 7E0AFA {12 * 16 - 21:04X}"]
                     + ["hold LEFT 20", "hold LEFT+A 25", "hold LEFT 10", "wait 40", f"expect 7E0AFA {10 * 16 - 21:04X}"])


def fc_round_2_chozo_d(fc: FullChain) -> None:
    """Round 2 in the Chozo, fourth part: the Sunchamber's arena CLIMBED (SUNCHAMBER_TO_STA) to its L0 door, the Sun Tower
    Access walked west into the Sun Tower (route C's), its east zigzag CLIMBED (SUN_TOWER_CLIMB), down the shaft and through the L1 door into the Magmoor
    transport (no item: the tower is on the way of the climb the validator says she can make on foot)."""
    m, room = fc.m, fc.room
    # specs/14c: a shot at the grey door (open: the boss is dead) and through; out of the arena's song set the transition
    # takes longer (out_of_arena's 150 more frames)
    fc.add(SUNCHAMBER_TO_STA + [fc.shot("2_arena_alto"), "hold LEFT+X 2", "hold LEFT 100", "wait 350",
                                f"expect {ROOM_PTR} {room['chozo_sun_tower_access']}", f"expect {GAME_STATE} 0008"])
    fc.add(chozo_walk("LEFT", CHAIN_STA_WALK, "chozo_sun_tower", room) + [f"expect 7E0AFA {42 * 16 - 21:04X}", fc.shot("2_torre_baixo")]
           + SUN_TOWER_CLIMB + [fc.shot("2_torre_alto"), "hold LEFT 200", "wait 60", f"expect 7E0AFA {26 * 16 - 21:04X}",
                                "hold LEFT+X 2", "wait 30", "hold LEFT 90", "wait 200",
                                f"expect {ROOM_PTR} {room['chozo_transport_magmoor_north']}", f"expect {GAME_STATE} 0008"])


def fc_round_2_chozo_e(fc: FullChain) -> None:
    """Round 2 in the Chozo, fifth part: by door_teleport to the Gathering Hall; its east gallery CLIMBED again, the cage's
    bomb block from the gallery (its missile), over the cage into the Watery Hall Access: the missile wall's bomb block
    (Samus put near it: shortcut); the Watery Hall's stair CLIMBED again, the gallery's bomb block (Prime's breakable block)
    into the R0 chamber, its red door, the Dynamo Access and its red door, the Dynamo's bomb block (its missile)."""
    from chozo import layouts as chozo_layouts
    m, room = fc.m, fc.room
    gh = chozo_item_index("chozo_gathering_hall")
    fc.tp(["chozo_transport_magmoor_north", "chozo_vault_access", "chozo_vault", "chozo_plaza_access", "chozo_main_plaza", FOUNTAIN,
           "chozo_ruined_fountain", "chozo_arboretum_access", "chozo_arboretum", "chozo_gathering_hall_access", "chozo_gathering_hall"])
    fc.add(GH_EAST_GALLERY)
    fc.walked_into("chozo", gh, "2_gathering_gaiola", BALL_RIGHT + ["hold RIGHT 30", "wait 10", "hold X 2", "wait 100",
                                                                   f"expect {level_block('chozo_gathering_hall', *chozo_layouts.GATHERING_BOMB):06X} 00FF",
                                                                   "hold RIGHT 120"])
    fc.add(["hold LEFT 20", "wait 30"] + STAND_UP + ["hold RIGHT 20", "wait 10", "expect 7E0AF6 024B"] + GH_CAGE_TOP
           + ["hold RIGHT+X 2", "hold RIGHT 100", "wait 200", f"expect {ROOM_PTR} {room['chozo_watery_hall_access']}"])
    wha = [n for n, it in enumerate(__import__("chozo.items", fromlist=["ITEMS"]).ITEMS) if it.room == "chozo_watery_hall_access"][0]
    chain_bomb_tunnel(fc, wha, -5, "RIGHT", chozo_layouts.WHA_BOMB, "2_wha", clear=True)
    fc.tp(["chozo_watery_hall_access", "chozo_watery_hall"])
    fc.add(WATERY_STAIR + ["hold RIGHT 30", "hold RIGHT+A 25", "hold RIGHT 150", "wait 20", "expect 7E0AF6 033B"] + BALL_RIGHT
           + ["hold RIGHT 30", "wait 10", "hold X 2", "wait 100",
              f"expect {level_block('chozo_watery_hall', *chozo_layouts.WATERY_BOMB):06X} 00FF", "hold RIGHT 80", "wait 30"]
           + STAND_UP + ["hold RIGHT 60", "wait 30"])
    fc.red_door("chozo_watery_hall", "chozo_dynamo_access", "RIGHT", "2_porta_dynamo_access")
    fc.add(chozo_walk("RIGHT", 6, "chozo_dynamo_access", room)[:-3] + ["hold RIGHT 60", "wait 30"])
    fc.red_door("chozo_dynamo_access", "chozo_dynamo", "RIGHT", "2_porta_dynamo")
    dyn_wall = [n for n, it in enumerate(__import__("chozo.items", fromlist=["ITEMS"]).ITEMS) if it.room == "chozo_dynamo"][0]
    chain_bomb_tunnel(fc, dyn_wall, -5, "RIGHT", chozo_layouts.DYNAMO_BOMB, "2_dynamo", clear=True)


def fc_round_2_chozo_f(fc: FullChain) -> None:
    """Round 2 in the Chozo, sixth part: by door_teleport to the Energy Core, route D's walk to its step, onto the platform and
    up the T3 ceiling door (a real climb), the Burn Dome Access' tunnel, the Burn Dome's tunnel (a bomb block: its missile);
    back down into the Energy Core (door_teleport), off the platform and under it, the bomb slots' block (a bomb), the West
    Furnace Access, the Furnace's corridor and down off its balcony (route D's walk), the E-tank under the floor (a bomb block)."""
    from chozo import layouts as chozo_layouts
    from chozo import items as chozo_items
    m, room = fc.m, fc.room
    fc.tp(["chozo_dynamo", "chozo_dynamo_access", "chozo_watery_hall", "chozo_watery_hall_access", "chozo_gathering_hall",
           "chozo_east_atrium", "chozo_energy_core_access", "chozo_energy_core"])
    fc.add(EC_DOOR_TO_STEP + ENERGY_CORE_TO_PLATFORM + climb_jump("RIGHT")
           + [f"expect {ROOM_PTR} {room['chozo_burn_dome_access']}", f"expect 7E0AFA {13 * 16 - 21:04X}"] + BALL_RIGHT
           + ["hold RIGHT 90", "wait 30"] + STAND_UP + [f"expect 7E0AFA {13 * 16 - 21:04X}", "hold A+RIGHT 30", "hold RIGHT 10", "wait 30"]
           + chozo_walk("RIGHT", D_BDA_WALK, "chozo_burn_dome", room))
    bd_tunnel = [n for n, it in enumerate(chozo_items.ITEMS) if it.room == "chozo_burn_dome"][1]
    chain_bomb_tunnel(fc, bd_tunnel, -9, "RIGHT", chozo_layouts.BURN_DOME_BOMB, "2_burn_dome_tunel", clear=True)
    fc.tp(["chozo_burn_dome", "chozo_burn_dome_access", "chozo_energy_core"])
    fc.add(["hold LEFT 60", "wait 30", f"expect 7E0AFA {10 * 16 - 21:04X}", "hold RIGHT 120", "wait 20", "expect 7E0AF6 037B"]
           + BALL_RIGHT + ["hold RIGHT 30", "wait 10", "hold X 2", "wait 100",
                           f"expect {level_block('chozo_energy_core', *chozo_layouts.ENERGY_CORE_BOMB):06X} 00FF", "hold RIGHT 80",
                           "wait 30"] + STAND_UP + [fc.shot("2_bomb_slots"), f"poke {HEALTH} 63", "hold RIGHT+X 2", "wait 30",
                                                    "hold RIGHT 90", "wait 200", f"expect {ROOM_PTR} {room['chozo_west_furnace_access']}"]
           + chozo_walk("RIGHT", 8, "chozo_furnace", room) + D_FURNACE_WALK
           + [f"expect {ROOM_PTR} {room['chozo_furnace']}", f"expect 7E0AFA {28 * 16 - 21:04X}"])
    fur_etank = chozo_item_index("chozo_furnace", 0xEED7)
    chain_bomb_tunnel(fc, fur_etank, 7, "LEFT", chozo_layouts.FURNACE_BOMB, "2_furnace_etank", clear=True)


# the Magma Pool from the Meditation Fountain's door: down into the dry pool against its west wall, up onto the west ledge
MAGMA_TO_WEST_LEDGE = ["hold LEFT 300", "wait 20", "hold A 24", "hold A+LEFT 16", "hold LEFT 10", "wait 40",
                       f"expect 7E0AFA {10 * 16 - 21:04X}"]


def chain_wave_door(fc: FullChain, key: str, to: str, toward: str, tag: str) -> None:
    """Samus walks against key's wave door to `to` (purple: the cap stops her), one shot of her beams (Wave in them) opens it,
    she walks through."""
    fc.add(chozo_door_shut(key, to) + [fc.shot(f"{tag}_fechada"), f"hold {toward}+X 2", "wait 6", fc.shot(f"{tag}_abrindo"), "wait 120",
                                       f"hold {toward} 90", "wait 200", f"expect {ROOM_PTR} {fc.room[to]}", f"expect {GAME_STATE} 0008"])


def fc_round_2_chozo_g(fc: FullChain) -> None:
    """Round 2 in the Chozo, last part: by door_teleport to the Magma Pool (hot: the Varia Suit protects her, specs/12g2),
    across it onto the west ledge, its wave door shot open, the Training Chamber Access: walking west she drops into the
    hole, ball, she rolls into the missile (Prime's Morph Ball path)."""
    m, room = fc.m, fc.room
    fc.tp(["chozo_furnace", "chozo_west_furnace_access", "chozo_energy_core", "chozo_energy_core_access", "chozo_east_atrium",
           "chozo_gathering_hall", "chozo_gathering_hall_access", "chozo_arboretum", "chozo_arboretum_access", "chozo_ruined_fountain",
           "chozo_meditation_fountain", MAGMA])
    fc.add(poke16(0x7E09C2, 99) + ["wait 120", f"expect {HEALTH} 0063"] + MAGMA_TO_WEST_LEDGE)   # no heat damage with the Varia
    chain_wave_door(fc, MAGMA, "chozo_training_chamber_access", "LEFT", "2_onda_tca")
    fc.walked_into("chozo", chozo_item_index("chozo_training_chamber_access"), "2_tca",
                   ["hold LEFT 300", "wait 30", f"expect 7E0AFA {12 * 16 - 21:04X}"] + BALL_LEFT + ["hold RIGHT 120"])
    fc.add(["hold LEFT 80", "wait 30"] + STAND_UP)


# the Meditation Fountain from its L0 door: over the step, onto the T1 platform, under the door's west half, up into the Ruined
# Fountain (chozo_climb's jump steered east; chozo_varia_e_calor used rise_through, a RAM transition)
MEDITATION_UP = (["hold RIGHT 60", "hold RIGHT+A 20", "hold RIGHT 40", "wait 20", "hold RIGHT 40", "wait 20"]
                 + zig_jump("RIGHT", 15, 16, 24) + [f"expect 7E0AFA {6 * 16 - 21:04X}", "hold RIGHT 15", "wait 20"] + climb_jump("RIGHT"))


def fc_round_3_chozo_a(fc: FullChain) -> None:
    """Round 3 in the Chozo (+ the Space Jump, the Varia Suit and round 2's missiles), the Space Jump ledges' items, each
    with Samus put on its ledge by RAM (shortcut: the flights up to them are the validator's flood fill; the chain flies for
    real to the Furnace's balcony): the Training Chamber's E-tank (through its wave door from the access), the Ruined
    Fountain's track missile, the Main Plaza's half-pipe and grapple ledges, the Ruined Shrine's half-pipe ledge, the
    Dynamo's track."""
    from chozo import items as chozo_items
    m, room = fc.m, fc.room
    fc.round = 3
    fc.add(["hold LEFT 20", "hold LEFT+A 30", "hold LEFT 150", "wait 20"])
    chain_wave_door(fc, "chozo_training_chamber_access", "chozo_training_chamber", "LEFT", "3_onda_tc")
    fc.take_chozo(chozo_item_index("chozo_training_chamber"), "3_training_etank", start=2)
    fc.tp(["chozo_training_chamber", "chozo_training_chamber_access", MAGMA, "chozo_meditation_fountain"])
    fc.add(MEDITATION_UP + [f"expect {ROOM_PTR} {room['chozo_ruined_fountain']}", f"expect 7E0AFA {13 * 16 - 21:04X}"])
    fc.add(clear_room_enemies("chozo_ruined_fountain"))
    fc.note("inimigos da sala apagados por RAM")
    fc.take_chozo(chozo_item_index("chozo_ruined_fountain"), "3_fonte_trilho")
    fc.tp(["chozo_ruined_fountain", FOUNTAIN, "chozo_main_plaza"])
    fc.take_chozo(0, "3_praca_meio_tubo")
    fc.take_chozo(1, "3_praca_gancho")
    fc.tp(["chozo_main_plaza", "chozo_ruined_shrine_access", "chozo_ruined_shrine"])
    fc.add(clear_room_enemies("chozo_ruined_shrine"))
    fc.note("inimigos da sala apagados por RAM")
    fc.take_chozo(5, "3_shrine_meio_tubo")
    fc.tp(["chozo_ruined_shrine", "chozo_ruined_shrine_access", "chozo_main_plaza", FOUNTAIN, "chozo_ruined_fountain",
           "chozo_arboretum_access", "chozo_arboretum", "chozo_gathering_hall_access", "chozo_gathering_hall",
           "chozo_watery_hall_access", "chozo_watery_hall", "chozo_dynamo_access", "chozo_dynamo"])
    fc.add(clear_room_enemies("chozo_dynamo"))
    fc.note("inimigos da sala apagados por RAM")
    dyn_track = [n for n, it in enumerate(chozo_items.ITEMS) if it.room == "chozo_dynamo"][1]
    fc.take_chozo(dyn_track, "3_dynamo_trilho", start=2)


# specs/12m: the Furnace with the Space Jump, for real (chozo_regiao_e_itens put her on the east balcony by RAM): from the L0
# door a running spin jump and four Space Jump presses up onto the track's ledge (into its missile), then a jump east down
# onto the balcony
FURNACE_TO_TRACK = ["hold RIGHT 170", "hold RIGHT+A 30"] + ["hold RIGHT 12", "hold RIGHT+A 30"] * 4 + ["hold RIGHT 30"]
FURNACE_TRACK_TO_BALCONY = ["hold RIGHT+A 10", "hold RIGHT 40", "wait 60", f"expect 7E0AFA {10 * 16 - 21:04X}"]
CAW_OVER_THE_BOWL = ["hold RIGHT 150", "hold A+RIGHT 30", "hold RIGHT 150", "wait 30"]


def fc_round_3_chozo_b(fc: FullChain) -> None:
    """Round 3 in the Chozo, second part: by door_teleport to the Furnace (the Energy Core's bomb slots were opened in round 2),
    the Space Jump for real up to the track's missile and down onto the east balcony, the Morph Ball door (its tunnel), the
    Crossway Access West's wave door, the Crossway: down its zigzag into the dip over the red floor door, 5 missiles shot down
    at it (its bit), down into the Elder Hall Access, west into the Hall of the Elders (Prime's way, no ice): the E-tank of
    the "Down Launch" alcove (a bomb block)."""
    from chozo import layouts as chozo_layouts
    m, room = fc.m, fc.room
    fc.tp(["chozo_dynamo", "chozo_dynamo_access", "chozo_watery_hall", "chozo_watery_hall_access", "chozo_gathering_hall",
           "chozo_east_atrium", "chozo_energy_core_access", "chozo_energy_core", "chozo_west_furnace_access", "chozo_furnace"])
    fc.note("inimigos da sala apagados por RAM")
    fc.add(clear_room_enemies("chozo_furnace"))
    fc.walked_into("chozo", chozo_item_index("chozo_furnace", 0xEEDB), "3_furnace_trilho", FURNACE_TO_TRACK)
    fc.add(FURNACE_TRACK_TO_BALCONY + [fc.shot("3_sacada"), "hold RIGHT 20", "wait 10"] + BALL_RIGHT
           + ["hold RIGHT 60", "wait 10"] + STAND_UP + [f"expect {POSE} {STAND_POSE}", "hold RIGHT+X 2", "hold RIGHT 120", "wait 200",
                                                     f"expect {ROOM_PTR} {room['chozo_crossway_access_west']}"]
           + CAW_OVER_THE_BOWL)
    chain_wave_door(fc, "chozo_crossway_access_west", "chozo_crossway", "RIGHT", "3_onda_crossway")
    fc.add(["hold RIGHT 400", "wait 60", "hold LEFT 120", "wait 30", f"expect 7E0AFA {29 * 16 - 21:04X}", fc.shot("3_crossway_b1")])
    fc.red_floor_door("chozo_crossway", "chozo_elder_hall_access", "3_porta_vermelha_b1")
    fc.add(["hold LEFT 100", "hold LEFT+X 2", "hold LEFT 100", "wait 200", f"expect {ROOM_PTR} {room['chozo_hall_of_the_elders']}",
            f"expect {GAME_STATE} 0008"])
    chain_bomb_tunnel(fc, chozo_item_index("chozo_hall_of_the_elders"), 6, "LEFT", chozo_layouts.HALL_ETANK_BOMB, "3_hall_etank")


# specs/17j: the Magmoor in the full chain. Its regions are walked with the measured moves of the region tests (magmoor_a_*,
# magmoor_b_*, magmoor_c_* pieces: magmoor_regiao_a_rota, magmoor_regiao_b_rota, magmoor_regiao_c_rota), every energy check
# at all she has (no heat with the Varia, no lava, no enemy touch, no damage in a door's first frames)
CHAIN_P24_PAD = 42           # from the Chozo's Magmoor North transport's west wall (walked down from the Sun Tower's door) east onto the platform
CHAIN_P16_PAD = 41           # from the P16's L0 door cap (walked west to it: a fixed spot) east onto the platform's middle
CHAIN_P23_PAD = 28           # from the Tallon's Magmoor East transport's west wall (a fixed spot) east onto the platform's middle
CHAIN_MAGMOOR_ROUND_3_SCREENS = MAGMOOR_A_SCREENS + MAGMOOR_B_SCREENS + M17I_SCREENS[:13]


def magmoor_shots(fc: FullChain, tag: str):
    """The region pieces' photos in the chain: the region test's photo name after the chain's sequence number and `tag`."""
    return lambda path: fc.shot(f"{tag}_{path.rsplit('/', 1)[1].split('_rota_')[-1]}")


def chain_magmoor_energy(fc: FullChain) -> int:
    """All her energy when she comes into the Magmoor, refilled by RAM (shortcut, counted: the walks before may have cost some;
    the Magmoor's are checked at all of it: the walks of the region tests hurt nothing); her missiles
    and power bombs refilled by RAM to what she can carry (shortcut, counted: the enemies she shoots there drop ammo, which the
    chain's count does not foresee; full, the drops add none)."""
    if fc.missiles < fc.max_missiles:
        fc.note("mísseis repostos por RAM")
        fc.missiles = fc.max_missiles
    if fc.pbs < fc.max_pbs:
        fc.note("power bombs repostas por RAM")
        fc.pbs = fc.max_pbs
    fc.note("energia reposta por RAM")
    fc.add(poke16(0x7E09C6, fc.missiles) + poke16(0x7E09CE, fc.pbs) + poke16(0x7E09C2, fc.max_energy)
           + ["wait 2", f"expect {HEALTH} {fc.max_energy:04X}"])
    return fc.max_energy


def fc_round_3_magmoor(fc: FullChain) -> None:
    """specs/17j, round 3 in the Magmoor (+ the Space Jump and the Varia Suit: the hot rooms, the ledges): from the Hall of the
    Elders by door_teleport to the Chozo's Magmoor North transport (the Sunchamber Lobby's ceiling door by rise_through: a door
    teleport up there stays in the lobby), WALKING down to its west wall and onto the platform, DOWN: the Magmoor's P0. Region A
    walked (magmoor_regiao_a_rota's moves): the Storage Cavern's missile, the Triclops Pit's column missile with the Space Jump;
    region B (magmoor_regiao_b_rota's): the Transport Tunnel A's energy tank (its bomb block), on to the P16; region C
    (magmoor_regiao_c_rota's): the Twin Fires Tunnel's cliff with the Space Jump, the Geothermal Core, the Workstation's energy
    tank on its raised platform. Back to the P16 by door_teleport (the wave doors opened on the way), WALKING onto its platform,
    UP: the Tallon's Magmoor East transport."""
    m, room = fc.m, fc.room
    fc.round = 3
    fc.tp(["chozo_hall_of_the_elders", "chozo_elder_hall_access", "chozo_crossway", "chozo_crossway_access_west", "chozo_furnace",
           "chozo_west_furnace_access", "chozo_energy_core", "chozo_energy_core_access", "chozo_east_atrium", "chozo_gathering_hall",
           "chozo_gathering_hall_access", "chozo_arboretum", "chozo_sunchamber_lobby"])
    fc.note("transição de porta de teto por RAM (rise_through)")
    fc.add(rise_through(m, room, "chozo_sunchamber_lobby", "chozo_sunchamber_access", 0, "LEFT"))
    fc.tp(["chozo_sunchamber_access", "chozo_sunchamber", "chozo_sun_tower_access", "chozo_sun_tower", CHOZO_TO_MAGMOOR])
    fc.add(["hold LEFT 300", "wait 60", "expect 7E0AF6 0025", f"hold RIGHT {CHAIN_P24_PAD}", "wait 30",
            f"expect {ELEVATOR_FLAGS} 0001"] + ride_elevator(room, CHOZO_TO_MAGMOOR, f"{FULL_SHOT}_{fc.seq:03d}_3_descendo_magmoor.png"))
    energy = chain_magmoor_energy(fc)
    sh = magmoor_shots(fc, "3m")
    fc.walked_into("magmoor", magmoor_item("magmoor_storage_cavern"), "3m_storage_missil", magmoor_a_to_storage(room, energy, sh))
    fc.walked_into("magmoor", magmoor_item("magmoor_triclops_pit"), "3m_triclops_missil", magmoor_a_to_column(room, energy, sh))
    fc.add(magmoor_a_to_station(room, energy, sh))
    fc.walked_into("magmoor", magmoor_item("magmoor_transport_tunnel_a"), "3m_tta_tanque", magmoor_b_to_tank(room, energy, sh))
    energy = fc.max_energy
    fc.add(magmoor_b_to_p16(room, energy, sh) + [f"hold RIGHT {M17H_P16_PAD}", "wait 30"])
    fc.walked_into("magmoor", magmoor_item("magmoor_workstation"), "3m_workstation_tanque", magmoor_c_to_tank(room, energy, sh, "D"))
    fc.screens |= set(CHAIN_MAGMOOR_ROUND_3_SCREENS)
    # specs/18n: round 3 goes on up into Phendrana (fc_round_3_phendrana_up) and comes back by its south elevator
    # (fc_round_3_phendrana_down: up the P16 from there)


# specs/18n: Phendrana in the full chain. Its regions are walked with the measured moves of the region tests (the pieces
# phendrana_a_*, phendrana_b_*, ...: phendrana_regiao_a_rota, _templo, _b_rota, _c_rota, _d_rota, _e_rota, _e_agua), every energy
# check at all she has; the two bosses fought for real with moves searched from the chain's own entry (CHAIN_SHEEGOTH_FIGHT,
# CHAIN_THARDUS_FIGHT); the two lifts ridden walking onto their platforms
CHAIN_P13_PAD = 46           # from the Magmoor's P13's west wall (x $15) east onto the middle of its platform (ride up to Phendrana's P0)
MAGMOOR_ROUND_3_TO_P13 = ["magmoor_workstation", "magmoor_south_core_tunnel", "magmoor_geothermal_core", "magmoor_north_core_tunnel",
                          "magmoor_twin_fires", "magmoor_twin_fires_tunnel", MAGMOOR_FROM_TALLON, "magmoor_transport_tunnel_b",
                          "magmoor_fiery_shores"]


def chain_ride_up_p13(fc: FullChain, tag: str) -> None:
    """From the Shore Tunnel by door_teleport to the Magmoor's P13 (in by its R0 door from the Transport Tunnel A); WALKING west
    against its wall and back east onto the platform, UP: Phendrana's P0 (area 4)."""
    room = fc.room
    fc.tp(["magmoor_shore_tunnel", "magmoor_monitor_station", "magmoor_transport_tunnel_a", MAGMOOR_TO_NORTH])
    fc.add(["hold LEFT 300", "wait 30", "expect 7E0AF6 0015", f"hold RIGHT {CHAIN_P13_PAD}", "wait 30",
            f"expect {ELEVATOR_FLAGS} 0001"]
           + ride_elevator(room, MAGMOOR_TO_NORTH, f"{FULL_SHOT}_{fc.seq:03d}_{tag}_subindo_phendrana.png"))


def fc_round_3_phendrana_up(fc: FullChain) -> None:
    """specs/18n, round 3 into Phendrana: from the Workstation (fc_round_3_magmoor) by door_teleport back through the Magmoor
    to the Fiery Shores, up its ceiling door into the Shore Tunnel (rise_through, as round 6), to the P13 (chain_ride_up_p13),
    UP: Phendrana's P0."""
    fc.round = 3
    fc.tp(MAGMOOR_ROUND_3_TO_P13)
    fc.note("transição de porta de teto por RAM (rise_through)")   # up the Fiery Shores' ceiling door, as round 6
    fc.add(rise_through(fc.m, fc.room, "magmoor_fiery_shores", "magmoor_shore_tunnel", 0, "LEFT"))
    chain_ride_up_p13(fc, "3")


def chain_phendrana_refill(fc: FullChain) -> int:
    """specs/18n: as chain_magmoor_energy (the same shortcuts, counted): all her energy, her missiles, super missiles and power
    bombs refilled by RAM to what she can carry (ammo, never capacity), where Phendrana's walks start (the region tests' walks
    check the energy at each arrival) and after what spends ammo or energy (a fight, a red door)."""
    if fc.supers < fc.max_supers:
        fc.note("super mísseis repostos por RAM")
        fc.supers = fc.max_supers
        fc.add(poke16(0x7E09CA, fc.supers))
    return chain_magmoor_energy(fc)


def fc_round_3_phendrana_a(fc: FullChain) -> None:
    """specs/18n, round 3 in Phendrana, region A's temple: from the P0's platform phendrana_regiao_a_templo's walk (the
    Shorelines' west zigzag, the Temple Entryway, the Chozo Ice Temple's bomb block and tunnel) into the Chapel Tunnel, east
    into the Chapel of the Elders: the Sheegoth's arena alive."""
    room = fc.room
    energy = chain_phendrana_refill(fc)
    fc.add(phendrana_a_to_chapel_tunnel(room, energy, magmoor_shots(fc, "3p"))
           + moves("RRRRRRRRRRRRRR") + CHAIN_SHEEGOTH_IN + phendrana_full(room, SHEEGOTH, 9, energy)
           + enemies_alive(PHENDRANA, SHEEGOTH) + ["expect 7ED82C 0000", fc.shot("3p_capela")] + fc.select(1))


CHAIN_SHEEGOTH_IN = ["hold RIGHT+X 2", "hold RIGHT 60", "wait 200"]   # through the Chapel Tunnel's R0 into the Chapel, stopping


# specs/18n: the Sheegoth fought for real from the chain's own entry (searched in the emulator, scratchpad s18n/scripts/boss.py:
# MAGMOOR_MOVES letters, missiles selected, no RAM): the moves, what it leaves her, the walk up onto the altar into the missile
CHAIN_SHEEGOTH_FIGHT = "GXcgGcRXXssccRscsc"
CHAIN_SHEEGOTH_ENERGY_LOST = 40      # measured: its and the small ones' touches (with the Varia Suit)
CHAIN_SHEEGOTH_MISSILES_FIRED = 10   # measured: 10 missiles (the Dessgeega's shell takes no uncharged beam)
CHAIN_SHEEGOTH_TO_ALTAR = "RRRXR"


def fc_round_3_phendrana_sheegoth(fc: FullChain) -> None:
    """specs/18n: the Sheegoth's arena fought (CHAIN_SHEEGOTH_FIGHT): the 3 dead (kill count 3), the bit $08 of area 4, the
    missile on the altar (Prime's Wave Beam's place) walked into; back to the beam, west out through the L0 (a blue door now:
    the grey cap opened by the count) into the Chapel Tunnel."""
    room = fc.room
    energy = fc.max_energy - CHAIN_SHEEGOTH_ENERGY_LOST
    fc.missiles -= CHAIN_SHEEGOTH_MISSILES_FIRED
    fc.add(moves(CHAIN_SHEEGOTH_FIGHT) + ["wait 2", f"expect {KILLS} 0003"]
           + [f"expect {ENEMY_TABLE + ENEMY_SLOT * n:06X} 0000" for n in range(3)]
           + ["expectbit 7ED82C 08", f"expect {HEALTH} {energy:04X}", f"expect {MISSILES} {fc.missiles:04X}",
              f"expect {plm_slot(PLM_HEADERS, SHEEGOTH_PRIZE_SLOT)} EEDB", "wait 30", fc.shot("3p_sheegoth_vitoria")])
    fc.walked_into("phendrana", phendrana_item("phendrana_chapel_of_the_elders"), "3p_capela_missil",
                   moves(CHAIN_SHEEGOTH_TO_ALTAR))
    fc.add(fc.select(0) + ["hold LEFT 560", f"expect {plm_slot(PLM_HEADERS, SHEEGOTH_GREY_SLOT)} C848"] + moves("E")
           + phendrana_full(fc.room, "phendrana_chapel_tunnel", 9, energy))


def fc_round_3_phendrana_shore(fc: FullChain) -> None:
    """specs/18n, round 3 in Phendrana, region A: from the Chapel Tunnel by door_teleport back to the P0 (in by its R1 door);
    phendrana_regiao_a_rota's walk from there: the Shorelines' lake missile, the ruined tower's missile (the Space Jump), the
    Ice Ruins Access, the Ice Ruins East's niche and tower missiles, the Plaza Walkway, the Shorelines' overhang, the Ruins
    Entryway, into the Ice Ruins West (region B)."""
    room = fc.room
    fc.tp(["phendrana_chapel_tunnel", "phendrana_chozo_ice_temple", "phendrana_temple_entryway", "phendrana_shorelines",
           "phendrana_shoreline_entrance", PHENDRANA_NORTH])
    energy = chain_phendrana_refill(fc)
    sh = magmoor_shots(fc, "3p")
    fc.walked_into("phendrana", phendrana_item("phendrana_shorelines", 1), "3p_lago_missil", phendrana_a_to_lake(room, energy, sh))
    fc.walked_into("phendrana", phendrana_item("phendrana_shorelines", 0), "3p_torre_missil", phendrana_a_to_tower(room, energy, sh))
    fc.walked_into("phendrana", phendrana_item("phendrana_ice_ruins_east", 1), "3p_nicho_missil",
                   phendrana_a_to_niche(room, energy, sh))
    fc.walked_into("phendrana", phendrana_item("phendrana_ice_ruins_east", 0), "3p_torre_leste_missil", phendrana_a_to_east_tower())
    fc.add(phendrana_a_to_irw(room, energy, sh))
    fc.screens |= set(PHENDRANA_A_SCREENS + PHENDRANA_TEMPLE_SCREENS + [("phendrana_ice_ruins_west", 0, 1)])


def chain_phendrana_red_door(fc: FullChain, key: str, toward: str, to: str, bit: int, tag: str, energy: int) -> None:
    """specs/18n: Samus against `key`'s red door (toward `toward`, a Phendrana missile shield): missiles selected, 6 shots (5 hits
    open it), its bit on, back to the beam, through into `to` (as phendrana_red_door, with the chain's HUD and count)."""
    out = ["wait 30"] + fc.select(1) + [f"hold {toward}+X 2", "wait 30"] * 6
    fc.missiles -= 6
    out += ["wait 60", red_door_bit(bit), f"expect {MISSILES} {fc.missiles:04X}"] + fc.select(0)
    fc.add(out + [f"hold {toward} 90", "wait 160", f"expect {ROOM_PTR} {fc.room[to]}", f"expect {GAME_STATE} 0008",
                  f"expect {HEALTH} {energy:04X}", fc.shot(tag)])


def fc_round_3_phendrana_ruins(fc: FullChain) -> None:
    """specs/18n, round 3 in Phendrana, region B (phendrana_regiao_b_rota's walk): the Ice Ruins West's plasma cap (the Wave
    Beam leaves it shut), its red door to the Canyon Entryway (6 missiles, bit $C2) and back, the Courtyard Entryway, the
    Ruined Courtyard's bomb block and its Energy Tank, the Specimen Storage, the Research Entrance's vertical wave door, the Hydra
    Lab Entryway, the Research Lab Hydra's missile."""
    room = fc.room
    energy = fc.max_energy
    sh = magmoor_shots(fc, "3p")
    # walked in, she is further in than the region test's door_teleport leaves her: in again the test's way
    fc.tp([IRW, "phendrana_ruins_entryway", IRW])
    fc.add(["wait 200"] + phendrana_full(room, IRW, 25, energy) + phendrana_b_to_red_door(room, energy, sh))
    chain_phendrana_red_door(fc, IRW, "LEFT", "phendrana_canyon_entryway", IRW_RED_BIT, "3p_canyon_entryway", energy)
    energy = chain_phendrana_refill(fc)
    fc.walked_into("phendrana", phendrana_item(COURT), "3p_courtyard_tanque", phendrana_b_to_tank(room, energy, sh), wait=30)
    energy = fc.max_energy
    fc.walked_into("phendrana", phendrana_item(HYDRA), "3p_hydra_missil", phendrana_b_to_hydra(room, energy, sh, beam_proof=False))
    fc.screens |= set(PHENDRANA_B_SCREENS)


def fc_round_3_phendrana_labs(fc: FullChain) -> None:
    """specs/18n, round 3 in Phendrana, region D (phendrana_regiao_d_rota's walk): back into the Research Lab Hydra by its L0
    (door_teleport), the Observatory: the SUPER MISSILE behind its bomb block; ONE super missile opens the red door of Save
    Station D (bit $C4) and back; the West Tower Entrance's red door (6 missiles, bit $C5), the towers, the Aether Lab Entryway,
    the Research Lab Aether's Metroid, its Energy Tank and missile, the Research Core's 3 Metroids (its L1, an ice door, waits
    for round 4)."""
    room = fc.room
    fc.tp([HYDRA, HLE, HYDRA])
    energy = fc.max_energy
    sh = magmoor_shots(fc, "3p")
    fc.add(["wait 200"] + phendrana_full(room, HYDRA, 9, energy))
    fc.walked_into("phendrana", phendrana_item(OBS), "3p_super_missil", phendrana_d_to_super(room, energy, sh))
    fc.add([fc.shot("3p_hud_super")] + phendrana_d_to_save_d_door(room, energy) + ["wait 30"] + fc.select(2)
           + ["hold RIGHT 2", "hold RIGHT+X 2", "wait 10", fc.shot("3p_super_disparo"), "wait 50"])
    fc.supers -= 1
    fc.add([f"expect {SUPERS} {fc.supers:04X}", f"expect {MISSILES} {fc.missiles:04X}", red_door_bit(SAVE_D_RED_BIT),
            fc.shot("3p_super_porta")] + fc.select(0) + ["hold RIGHT 90", "wait 160"] + phendrana_d_to_wte_door(room, energy))
    chain_phendrana_red_door(fc, WTE, "LEFT", WT, WT_RED_BIT, "3p_west_tower", energy)
    energy = chain_phendrana_refill(fc)
    fc.walked_into("phendrana", phendrana_item(AETHER, 0), "3p_aether_tanque", phendrana_d_to_aether_tank(room, energy, sh),
                   wait=60)
    energy = fc.max_energy
    fc.walked_into("phendrana", phendrana_item(AETHER, 1), "3p_aether_missil", ["hold LEFT 120"], wait=60)
    fc.add(phendrana_d_to_core(room, energy, sh))
    fc.screens |= set(PHENDRANA_D_SCREENS[:-1])   # not the Pike Access (round 4)


PHENDRANA_LABS_TO_QUARANTINE = [RC, RCA, AETHER, ALE, ET, CT, WT, WTE, OBS, "phendrana_observatory_access", HYDRA, HLE,
                                "phendrana_research_entrance", "phendrana_specimen_storage", COURT, QA]


def fc_round_3_phendrana_quarantine(fc: FullChain) -> None:
    """specs/18n, round 3 in Phendrana, region C (phendrana_regiao_c_rota's walk): from the Research Core by door_teleport back
    through the labs, the towers and the Ruined Courtyard into the Quarantine Access; down into the North Quarantine Tunnel, its
    vertical wave door, down the switchback, east through its R3 into the Quarantine Cave: the Thardus' arena alive."""
    room = fc.room
    fc.tp(PHENDRANA_LABS_TO_QUARANTINE)
    energy = fc.max_energy
    fc.add(["wait 200"] + phendrana_full(room, QA, 9, energy)
           + phendrana_c_to_nqt_foot(room, energy, magmoor_shots(fc, "3p"), beam_proof=False) + moves(P18J_NQT_OUT)
           + [f"expect {ROOM_PTR} {room[QC]}", f"expect {GAME_STATE} 0008"] + enemies_alive(PHENDRANA, QC)
           + ["expect 7ED82C 0008", fc.shot("3p_quarantine_cave")])   # the Sheegoth's bit only


# specs/18n: the Thardus fought for real from the chain's own entry (searched as the Sheegoth's: the beam only, no missile):
# its health 0 at the last shot, its death (THARDUS_DEATH frames), what it leaves her
CHAIN_THARDUS_FIGHT = "XgggxRccccccsccLRc"
CHAIN_THARDUS_ENERGY_LOST = 5        # measured: one touch of a rock (with the Varia Suit)


def fc_round_3_phendrana_thardus(fc: FullChain) -> None:
    """specs/18n: the Thardus' arena fought (CHAIN_THARDUS_FIGHT, the beam alone): its health 0, its death, the bits $04 (the
    Torizo's own) and $10 (the arena's) of area 4, the song stopped; west against the cliff at the Morph Ball tunnel's mouth;
    phendrana_regiao_c_rota's walk from there: the Quarantine Monitor's missile, back, up the cave's east zigzag, the South
    Quarantine Tunnel, the P29 (at its L1)."""
    room = fc.room
    sh = magmoor_shots(fc, "3p")
    energy = fc.max_energy - CHAIN_THARDUS_ENERGY_LOST
    fc.add(moves(CHAIN_THARDUS_FIGHT) + [f"expect {ENEMY_TABLE + ENEMY_HEALTH:06X} 0000", fc.shot("3p_thardus_morrendo"),
                                         f"wait {THARDUS_DEATH}", f"expect {ENEMY_TABLE:06X} 0000", "expectbit 7ED82C 14",
                                         "expect 7E07F5 0000", f"expect {HEALTH} {energy:04X}", fc.shot("3p_thardus_vitoria"),
                                         "hold LEFT 400", "wait 10"])
    energy = chain_phendrana_refill(fc)
    fc.add(phendrana_full(room, QC, 25, energy))
    fc.walked_into("phendrana", phendrana_item(QM), "3p_monitor_missil", phendrana_c_to_monitor_missile(room, energy, sh))
    fc.add(phendrana_c_to_p29(room, energy, sh))
    fc.screens |= set(PHENDRANA_C_SCREENS[:15])   # to the P29 (the Transport Access: round 4)


CHAIN_P29_PAD = 40           # from the P29's L1 door cap (walked west to it: x $25) east onto the middle of its platform
MAGMOOR_P27_TO_P16 = [MAGMOOR_TO_SOUTH, "magmoor_transport_tunnel_c", "magmoor_workstation", "magmoor_south_core_tunnel",
                      "magmoor_geothermal_core", "magmoor_north_core_tunnel", "magmoor_twin_fires", "magmoor_twin_fires_tunnel"]


def chain_ride_down_p29(fc: FullChain, tag: str) -> None:
    """In Phendrana's P29 (in by its L1): WALKING west against the L1's cap and back east onto the platform, DOWN: the Magmoor's
    P27; by door_teleport to the P16, WALKING onto its platform, UP: the Tallon's Magmoor East transport (chain_ride_up_p16)."""
    fc.add(["hold LEFT 60", "wait 30", "expect 7E0AF6 0025", f"hold RIGHT {CHAIN_P29_PAD}", "wait 30",
            f"expect {ELEVATOR_FLAGS} 0001"] + ride_elevator(fc.room, P29, f"{FULL_SHOT}_{fc.seq:03d}_{tag}_descendo_phendrana.png"))
    chain_ride_up_p16(fc, MAGMOOR_P27_TO_P16, tag)


def fc_round_3_phendrana_down(fc: FullChain) -> None:
    """specs/18n: round 3 leaves Phendrana by its south elevator (the P29, reached through the quarantine) and the Magmoor's
    P16 up to the Tallon (fc_round_3_tallon starts there)."""
    chain_ride_down_p29(fc, "3")


CHAIN_P27_PAD = 46           # from the Magmoor's P27's west wall east onto the middle of its platform (ride up to Phendrana's P29)


def chain_ride_up_p27(fc: FullChain, frm: list[str], tag: str) -> None:
    """Shortcut: door_teleport along `frm` to the Magmoor's P27 (in by its R1 door from the Transport Tunnel C); WALKING west
    against its wall and back east onto the platform, UP: Phendrana's P29 (area 4)."""
    fc.tp(frm + [MAGMOOR_TO_SOUTH])
    fc.add(["hold LEFT 300", "wait 30", "expect 7E0AF6 0015", f"hold RIGHT {CHAIN_P27_PAD}", "wait 30",
            f"expect {ELEVATOR_FLAGS} 0001"]
           + ride_elevator(fc.room, MAGMOOR_TO_SOUTH, f"{FULL_SHOT}_{fc.seq:03d}_{tag}_subindo_phendrana.png"))


def chain_phendrana_pike(fc: FullChain, frm: list[str], energy: int) -> None:
    """Shortcut: door_teleport along `frm` (ending in the Transport Access) into the Frozen Pike by its L0, as the region E tests
    get there (phendrana_pike), the snow falling."""
    fc.tp(frm + [FROZEN_PIKE])
    fc.add(["wait 200"] + phendrana_full(fc.room, FROZEN_PIKE, 9, energy) + [f"expect {WATER_FX_TYPE} 0008"])


def fc_round_4_phendrana(fc: FullChain) -> None:
    """specs/18n, round 4 in Phendrana (+ the Ice Beam): from the Plasma Processing (fc_round_4_magmoor) by door_teleport to the
    Magmoor's P27, UP its lift: Phendrana's P29; phendrana_regiao_c_rota's walk up to the R0, an ice door the Ice Beam's shot
    opens: the Transport Access; into the Frozen Pike (door_teleport, as the region E tests): phendrana_regiao_e_rota's walk to the
    Frost Cave's missile; in the Pike again, phendrana_regiao_e_agua's walk down to the flooded Gravity Chamber WITHOUT THE GRAVITY
    SUIT: its floor's missile (the Gravity Suit's place), back up the stair of 3-row steps, out by the L0, the Lake Tunnel, up into
    the Hunter Cave; by door_teleport back to the P29 (in by its L1), DOWN, and the Magmoor's P16 UP."""
    room = fc.room
    chain_ride_up_p27(fc, ["magmoor_plasma_processing", "magmoor_geothermal_core", "magmoor_south_core_tunnel",
                           "magmoor_workstation", "magmoor_transport_tunnel_c"], "4")
    energy = chain_phendrana_refill(fc)
    sh = magmoor_shots(fc, "4p")
    fc.add(phendrana_c_to_ta(room, energy, sh, beam_proof=False))
    chain_phendrana_pike(fc, [TA], energy)
    fc.walked_into("phendrana", phendrana_item(FROST), "4p_frost_missil", phendrana_e_to_frost_missile(room, energy, sh))
    chain_phendrana_pike(fc, [FROST, FCA, FROZEN_PIKE, TA], energy)
    fc.add(phendrana_e_to_chamber(room, energy, sh, beam_proof=False, mid=CHAIN_PIKE_MID) + [fc.shot("4p_gravity_chamber")])
    fc.walked_into("phendrana", phendrana_item(GRAV, 0), "4p_gravity_missil", phendrana_e_to_low_missile())
    fc.add(phendrana_e_up_the_stair(room, energy, sh) + CHAIN_GRAV_OUT_NO_SUIT
           + phendrana_e_lake_to_hunter(room, energy, CHAIN_LAKE))
    fc.screens |= set(PHENDRANA_E_WATER_SCREENS[:13]) | {(P29, 1, 0), (TA, 0, 0), (FROZEN_PIKE, 0, 0), (FCA, 0, 0), (FCA, 5, 0),
                                                         (FROST, 0, 2), (FROST, 1, 2)}
    fc.tp([HUNTER, HCA, FROZEN_PIKE, TA, P29, SQT])
    fc.tp([SQT, P29])
    chain_ride_down_p29(fc, "4")


# the Frozen Pike's L0 slab onto the slab of row 26 (P18M_PIKE_MID's "DD") when she comes in facing east (the region test's comes
# in facing the screen, from the lift: turning took frames): the second walk shorter, so the lower zigzag starts where it was
# measured (the window 143-145, measured)
CHAIN_PIKE_MID = MAGMOOR_MOVES["D"] + ["hold RIGHT+X 2", "hold RIGHT 145", "wait 200"]
# the Lake Tunnel from its R0 onto the ceiling door's platform past its orb (searched: s18n/scripts/seg.py, no damage), in round 4
# and in round 5 (the orb comes at her at another time)
CHAIN_LAKE, CHAIN_LAKE_5 = "LiIy", "lIIyl"
CHAIN_GRAV_OUT_NO_SUIT = P18M_STAIR_HOP + MAGMOOR_MOVES["E"]   # from the rock one more step west, out through the L0 (wave)


TALLON_CHOZO_EAST_TO_TUNNEL_B = ["tallon_transport_chozo_east", "tallon_tunnel_c", "tallon_overgrown_cavern", "tallon_crash_site",
                                 "tallon_waterfall_cavern", "tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon",
                                 "tallon_root_tunnel", "tallon_root_cave", "tallon_tunnel_b"]
MAGMOOR_P16_TO_TTC = [MAGMOOR_FROM_TALLON, "magmoor_twin_fires_tunnel", "magmoor_twin_fires", "magmoor_north_core_tunnel",
                      "magmoor_geothermal_core", "magmoor_south_core_tunnel", "magmoor_workstation", "magmoor_transport_tunnel_c"]


def fc_round_5_phendrana(fc: FullChain) -> None:
    """specs/18n, round 5 in Phendrana (+ the Gravity Suit), before the Tallon's: from the Chozo East transport (round 4's end)
    by door_teleport to the Magmoor East transport, DOWN to the P16, by door_teleport to the P27, UP: the P29; the R0 (ice), the
    Transport Access; by door_teleport into the flooded Gravity Chamber by its L0 (through the Pike, the Hunter Cave Access, the
    Hunter Cave and down into the Lake Tunnel); with the suit and the Space Jump under water onto the east ledge: its missile;
    phendrana_regiao_e_agua's way out (the stair, the L0, the Lake Tunnel, up into the Hunter Cave); by door_teleport back to the
    P29, DOWN, and the P16 UP."""
    room = fc.room
    fc.round = 5
    chain_ride_down_p23(fc, TALLON_CHOZO_EAST_TO_TUNNEL_B, "5")
    chain_ride_up_p27(fc, MAGMOOR_P16_TO_TTC, "5")
    energy = chain_phendrana_refill(fc)
    sh = magmoor_shots(fc, "5p")
    fc.add(phendrana_c_to_ta(room, energy, sh, beam_proof=False))
    fc.tp([TA, FROZEN_PIKE, HCA, HUNTER, LAKE, GRAV])
    fc.add(phendrana_full(room, GRAV, CHAIN_GRAV_L0_FEET, energy) + [f"expect {WATER_FX_TYPE} 0006", fc.shot("5p_gravity_chamber")])
    fc.walked_into("phendrana", phendrana_item(GRAV, 1), "5p_gravity_borda_missil", moves(CHAIN_GRAV_TO_LEDGE))
    fc.add(moves(P18M_GRAV_OUT) + phendrana_e_lake_to_hunter(room, energy, CHAIN_LAKE_5))
    fc.tp([HUNTER, HCA, FROZEN_PIKE, TA, P29, SQT])
    fc.tp([SQT, P29])
    chain_ride_down_p29(fc, "5")


CHAIN_GRAV_L0_FEET = 9      # in by the L0 from the Lake Tunnel (door_teleport): on the stair's top step
CHAIN_GRAV_TO_LEDGE = "GGgGGGR"   # from the L0 with the suit over the water onto the east ledge (searched: seg.py)


def chain_lay_power_bomb(fc: FullChain) -> list[str]:
    """In the ball: power bombs selected (the chain's HUD), one laid (as LAY_POWER_BOMB), back to the beam."""
    fc.pbs -= 1
    return fc.select(3) + ["hold X 2", "wait 300"] + fc.select(0)


# the Transport Access from its L0 past its orb (shot) east of the ice pillar, before the plasma cap (searched: s18n/scripts/seg.py,
# no damage: the region test's P18J_TA and hop leave the orb alive with the Plasma Beam's shots)
CHAIN_TA_6 = "gcaGXR"
CHAIN_FROST_UP_6 = "xxyxXD"   # the Frost Cave from its dry lake up the east zigzag through the R1 (searched: seg.py, no damage)
PHENDRANA_IRW_TO_SQT = [IRW, "phendrana_courtyard_entryway", COURT, QA, NQT, QC, SQT]


def fc_round_6_phendrana(fc: FullChain) -> None:
    """specs/18n, round 6 in Phendrana (+ the Power Bomb, the Plasma Beam): from the Shore Tunnel (fc_round_6_magmoor) to the P13,
    UP: the P0; by door_teleport into the Ice Ruins West (as phendrana_regiao_b_rota's end): the Plasma Beam opens the cap, the
    POWER BOMB EXPANSION in the niche; by door_teleport south through the quarantine to the P29 (in by its L1):
    phendrana_regiao_c_rota's walk to the Transport Access, the Plasma Beam opens its cap, the ENERGY TANK in the niche; into the
    Frozen Pike: phendrana_regiao_e_rota's walk (the Frost Cave, the Upper Edge Tunnel, Phendrana's Edge, the Storage Cave's
    plasma door), the power bomb blocks of the Morph Ball door: the Security Cave's POWER BOMB EXPANSION. Phendrana's explored
    screens and its pause map; by door_teleport back to the P29, DOWN, and the P16 UP."""
    room = fc.room
    fc.round = 6
    chain_ride_up_p13(fc, "6")
    energy = chain_phendrana_refill(fc)
    sh = magmoor_shots(fc, "6p")
    fc.tp([PHENDRANA_NORTH, "phendrana_shoreline_entrance", "phendrana_shorelines", "phendrana_ruins_entryway", IRW])
    fc.add(["wait 200"] + phendrana_full(room, IRW, 25, energy))
    fc.walked_into("phendrana", phendrana_item(IRW), "6p_irw_power_bomb", phendrana_b_to_pb(room, energy, sh), wait=60)
    fc.tp(PHENDRANA_IRW_TO_SQT + [P29])
    fc.add(phendrana_c_to_ta(room, energy, sh, beam_proof=False) + enemies_alive(PHENDRANA, TA) + moves(CHAIN_TA_6)
           + [f"expect {ENEMY_TABLE:06X} 0000"] + phendrana_full(room, TA, 12, energy) + ["hold LEFT 2", "wait 5"])
    fc.walked_into("phendrana", phendrana_item(TA), "6p_ta_tanque", phendrana_c_to_ta_tank(room, sh, beam_proof=False), wait=100)
    energy = fc.max_energy
    chain_phendrana_pike(fc, [TA], energy)
    lay = lambda: chain_lay_power_bomb(fc)   # noqa: E731
    # the missile taken in round 4: no message box stops her in the lake, and the walk up out of it is the chain's
    fc.add(phendrana_e_to_frost_missile(room, energy, sh) + phendrana_e_to_edge(room, energy, sh, CHAIN_FROST_UP_6)
           + phendrana_e_to_storage(room, energy, sh, beam_proof=False))
    fc.walked_into("phendrana", phendrana_item(SECURITY), "6p_security_power_bomb",
                   phendrana_e_to_security(room, energy, sh, power_bombs=fc.pbs, lay_bomb=lay))
    fc.screens |= set(PHENDRANA_C_SCREENS) | set(PHENDRANA_E_SCREENS)
    screens = sorted(sc for sc in fc.screens if sc[0].startswith("phendrana_"))
    fc.add([explored_at(*sc) for sc in screens] + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
           + pause_shows(PHENDRANA, screens, "18n_phendrana") + [fc.shot("6p_mapa_phendrana"), "hold START 10", "wait 200",
                                                                f"expect {GAME_STATE} 0008"])
    fc.tp([SECURITY, EDGE, UET, FROST, FCA, FROZEN_PIKE, TA, P29, SQT])
    fc.tp([SQT, P29])
    fc.add(UNMORPH + [f"expect {POSE} {STAND_POSE}"])   # still in the ball since the Security Cave's tunnel
    chain_ride_down_p29(fc, "6")


def chain_ride_up_p16(fc: FullChain, frm: list[str], tag: str) -> None:
    """Shortcut: door_teleport along `frm` to the Magmoor's P16 (in by its R0 door); WALKING west against the L0 door's cap and
    back east onto the platform (the spot she gets in at depends on which way she faced: measured), UP: the Tallon's Magmoor
    East transport."""
    fc.tp(frm + [MAGMOOR_FROM_TALLON])
    fc.add(["hold LEFT 400", "wait 30", "expect 7E0AF6 0025", f"hold RIGHT {CHAIN_P16_PAD}", "wait 30", f"expect {ELEVATOR_FLAGS} 0001"]
           + ride_elevator(fc.room, MAGMOOR_FROM_TALLON, f"{FULL_SHOT}_{fc.seq:03d}_{tag}_subindo_p16.png"))


CHAIN_EAST_PAD = 35
# Save Station 3 from its L0 door (walking in from the East transport): up onto the T0 platform, under the door's east half, up
# into the Reflecting Pool's west part (chozo_climb's jump, steered west; chozo_regiao_e_itens put her on the platform)
SS3_UP_TO_POOL = (["hold A 22", "hold A+RIGHT 18", "hold RIGHT 10", "wait 50", f"expect 7E0AFA {6 * 16 - 21:04X}", "hold RIGHT 16",
                   "wait 20"] + climb_jump("LEFT"))          # from where the Gravity Suit's cutscene leaves her, east onto the middle of the platform


def fc_round_3_tallon(fc: FullChain) -> None:
    """Round 3 in the Tallon (as tallon_cadeia_completa's): the Root Cave's ledge climbed with the Space Jump (ROOT_CAVE_CLIMB),
    on the shelf, walking west, the Root Cave missile and the Ice."""
    m, room = fc.m, fc.room
    # specs/17j: from the Magmoor East transport (round 3 came up from the Magmoor's P16), into the Root Cave by its Root
    # Tunnel door as before (where ROOT_CAVE_CLIMB starts)
    fc.tp([TALLON_TO_MAGMOOR, "tallon_tunnel_b", "tallon_root_cave", "tallon_root_tunnel", "tallon_root_cave"])
    fc.walked_into("tallon", item_index("tallon_root_cave"), "3_missil_root_cave", ROOT_CAVE_CLIMB)
    fc.walked_into("tallon", lock_item("tallon_root_cave"), "3_ice", ["hold LEFT 60"])
    fc.add([f"expect 7E0AFA {(ROOT_CAVE_SHELF_ROW + 1) * 16 - 21:04X}"] + has_beams(WAVE_BEAM | ICE_BEAM | CHARGE_EQUIPMENT))


def chain_ride_down_p23(fc: FullChain, frm: list[str], tag: str) -> None:
    """Shortcut: door_teleport along `frm` to the Tallon's Magmoor East transport (in by its R1 door from the Tunnel B); WALKING
    west to its wall and back east onto the platform (the spot she gets in at depends on which way she faced), DOWN: the
    Magmoor's P16."""
    fc.tp(frm + [TALLON_TO_MAGMOOR])
    fc.add(["hold LEFT 400", "wait 30", "expect 7E0AF6 0015", f"hold RIGHT {CHAIN_P23_PAD}", "wait 30", f"expect {ELEVATOR_FLAGS} 0001"]
           + ride_elevator(fc.room, TALLON_TO_MAGMOOR, f"{FULL_SHOT}_{fc.seq:03d}_{tag}_descendo_p23.png"))


def fc_round_4_magmoor(fc: FullChain) -> None:
    """specs/17j, round 4 in the Magmoor (+ the Ice Beam): from the Root Cave (the Ice) by door_teleport to the Tallon's Magmoor
    East transport, WALKING onto the platform, DOWN: the P16. Region C walked as magmoor_regiao_c_rota to the Geothermal Core's
    slab; against the puzzle's wall the bomb block, a bomb in the ball breaks it, the ball through the
    tunnel into the chamber; standing, the ice door shot open (magmoor_regiao_c_itens'): the Plasma Processing, west over its pit
    into the Missile Expansion where Prime has the Plasma Beam. Back to the P16 by door_teleport, WALKING onto the platform, UP."""
    from magmoor import layouts as magmoor_layouts
    m, room = fc.m, fc.room
    fc.round = 4
    chain_ride_down_p23(fc, ["tallon_root_cave", "tallon_tunnel_b"], "4")
    energy = chain_magmoor_energy(fc)
    sh = magmoor_shots(fc, "4m")
    block = level_block("magmoor_geothermal_core", *magmoor_layouts.GC_BOMB)
    fc.add(magmoor_c_to_slab(room, energy, sh)
           # no beam shot at the bomb block here (magmoor_regiao_c_itens' proof that the beam leaves it): the Wave Beam goes
           # through the wall and, with the Ice Beam on, opens the chamber's ice door (measured: the ball then rolls on into the
           # Plasma Processing)
           + ["hold LEFT 40", "wait 10", f"expect {block:06X} F058", fc.shot("4m_quebra_cabeca")]
           + MORPH + [f"expect {POSE} {BALL_POSE_LEFT}", "hold X 2", "wait 90", f"expect {block:06X} 00FF", "hold LEFT 100",
                      "wait 30"] + UNMORPH + [f"expect {POSE} 0002", f"expect {SAMUS_X} 0025", fc.shot("4m_porta_de_gelo"),
                                              "hold LEFT+X 2", "wait 120", "hold LEFT 90", "wait 200"]
           + magmoor_full(room, "magmoor_plasma_processing", 9, energy) + [fc.shot("4m_plasma_processing")])
    fc.walked_into("magmoor", magmoor_item("magmoor_plasma_processing"), "4m_plasma_processing_missil",
                   moves(M17I_PP) + ["hold LEFT 30"])
    fc.screens |= {("magmoor_plasma_processing", 0, 0), ("magmoor_plasma_processing", 2, 0)}
    # specs/18n: round 4 goes on up into Phendrana by its south elevator (fc_round_4_phendrana) and back up the P16 from there


def chain_beam_door_ahead(fc: FullChain, key: str, to: str, tag: str) -> None:
    """Shortcut: Samus put in front of key's beam door to `to` (stand_before_door); shut; one shot opens it; through it."""
    fc.note("Samus posta diante de porta")
    fc.add(stand_before_door(key, to) + beam_door_shut(key, to) + [fc.shot(f"{tag}_fechada")]
           + beam_door_open_and_through(fc.m, fc.room, key, to, None, f"12m_{tag}"))


def fc_round_4(fc: FullChain) -> None:
    """Round 4 (+ the Ice): in the Tallon (as tallon_cadeia_completa's) the ice doors shot open (Crash Site -> Overgrown, Samus
    put on the Crash Site's Space Jump ledge; Overgrown -> Tunnel C; Tunnel C -> Chozo East), the Overgrown missile, the
    Gravity Suit beside the platform; WALKING onto the platform, DOWN the East elevator: the Chozo's East transport, east into
    Save Station 3, up its ceiling door into the flooded Reflecting Pool's west part (a real climb), its red door (Samus on
    the L0 ledge), the Antechamber's missile (Prime's Ice Beam); back down into Save Station 3, west onto the platform, UP."""
    m, room = fc.m, fc.room
    fc.round = 4
    # specs/17j: from the Magmoor East transport (fc_round_4_magmoor came up from the Magmoor's P16)
    fc.tp([TALLON_TO_MAGMOOR, "tallon_tunnel_b", "tallon_root_cave", "tallon_root_tunnel", "tallon_canyon", "tallon_canyon_cavern",
           "tallon_landing_site", "tallon_waterfall_cavern", "tallon_crash_site"])
    chain_beam_door_ahead(fc, "tallon_crash_site", "tallon_overgrown_cavern", "4_porta_de_gelo_overgrown")
    fc.take_tallon(item_index("tallon_overgrown_cavern"), "4_missil_overgrown")
    chain_beam_door_ahead(fc, "tallon_overgrown_cavern", "tallon_tunnel_c", "4_porta_de_gelo_tunnel_c")
    chain_beam_door_ahead(fc, "tallon_tunnel_c", "tallon_transport_chozo_east", "4_porta_de_gelo_chozo_east")
    gravity = lock_item("tallon_transport_chozo_east")
    fc.note("Samus posta perto do item")
    fc.add(fc.pre("tallon", gravity) + ["wait 60"] + near_item(gravity, -1, floor=18) + ["wait 30"] + near_item(gravity, -1, floor=18)
           + ["wait 30", GRAVITY_STEP_OFF, "wait 120", fc.shot("4_gravity"), "wait 300", "hold A 2", "wait 200", "wait 1000"]
           + fc.post("tallon", gravity) + [f"expectbit 7E09A2 {GRAVITY_SUIT:02X}", f"expectbit 7E09A4 {GRAVITY_SUIT:02X}"])
    fc.add([f"hold RIGHT {CHAIN_EAST_PAD}", "wait 30", f"expect {ELEVATOR_FLAGS} 0001"]
           + ride_elevator(room, "tallon_transport_chozo_east", f"{FULL_SHOT}_4_descendo_east.png") + east_to_save_3(room, "12m_4")
           + SS3_UP_TO_POOL + [f"expect {ROOM_PTR} {room['chozo_reflecting_pool']}", f"expect 7E0AFA {BALCONY_Y:04X}",
                               fc.shot("4_piscina_oeste"), "hold LEFT 120", "wait 30"])
    fc.red_door("chozo_reflecting_pool", "chozo_antechamber", "LEFT", "4_porta_antechamber")
    fc.walked_into("chozo", chozo_item_index("chozo_antechamber"), "4_antechamber", ["hold LEFT 40", "hold LEFT+A 20", "hold LEFT 20"])
    # the Antechamber's ice door from inside (Prime's: ice on its side), back to the pool's west part, onto its red floor
    # door (missiles shot down, its bit), down into Save Station 3, west onto the East transport's platform, UP
    fc.add(["hold RIGHT 100", "wait 30"] + chozo_door_shut("chozo_antechamber", "chozo_reflecting_pool")
           + [fc.shot("4_gelo_antechamber_fechada"), "hold RIGHT+X 2", "wait 6", fc.shot("4_gelo_antechamber_abrindo"), "wait 120",
              "hold RIGHT 90", "wait 200", f"expect {ROOM_PTR} {room['chozo_reflecting_pool']}", f"expect {GAME_STATE} 0008",
              "hold RIGHT 30", "wait 40", f"expect 7E0AFA {13 * 16 - 21:04X}"])
    fc.red_floor_door("chozo_reflecting_pool", "chozo_save_station_3", "4_porta_vermelha_b0")
    fc.add(["hold LEFT 200", "wait 30", "hold LEFT+X 2", "hold LEFT 100", "wait 200", f"expect {ROOM_PTR} {room[EAST]}",
            "hold LEFT 25", "wait 30", f"expect {ELEVATOR_FLAGS} 0001"] + ride_elevator(room, EAST, f"{FULL_SHOT}_4_subindo_east.png"))


def fc_round_5(fc: FullChain) -> None:
    """Round 5 (+ the Gravity Suit), all in the Tallon (as tallon_cadeia_completa's): the Section C bulkhead climbed
    underwater with the suit, the Reactor Core's wave door, the Cargo Lift's and the Hydro Access' Energy Tanks, the
    Biohazard missile; region E: the Great Tree Chamber (its Space Jump ledge) and Life Grove Tunnel missiles, the Plasma
    (Chozo South), the Power Bomb (Mines East)."""
    m, room = fc.m, fc.room
    fc.round = 5
    # specs/18n: from the Magmoor East transport (round 5 went to Phendrana first: fc_round_5_phendrana)
    fc.tp([TALLON_TO_MAGMOOR, "tallon_tunnel_b", "tallon_root_cave", "tallon_root_tunnel", "tallon_canyon", "tallon_canyon_cavern",
           "tallon_landing_site", "tallon_waterfall_cavern", "tallon_crash_site", "tallon_frigate_access", "tallon_vent_c"])
    fc.add(["wait 30"] + BULKHEAD_TRY + [f"expect {ROOM_PTR} {room['tallon_vent_b']}", fc.shot("5_vent_b")])
    fc.tp(["tallon_vent_b", "tallon_vent_a", "tallon_reactor_core"])
    chain_beam_door_ahead(fc, "tallon_reactor_core", "tallon_reactor_access", "5_porta_de_onda")
    fc.tp(["tallon_reactor_access", "tallon_cargo_lift"])
    fc.add([f"poke {HEALTH} 63"])
    fc.take_tallon(item_index("tallon_cargo_lift"), "5_energy_tank_cargo_lift")
    fc.tp(["tallon_cargo_lift", "tallon_transit_hall", "tallon_biohazard"])
    fc.add([f"poke {HEALTH} 63"])
    fc.take_tallon(item_index("tallon_biohazard"), "5_missil_biohazard", start=-1)
    fc.tp(["tallon_biohazard", "tallon_security_hall", "tallon_biotech_1", "tallon_conduit_hall", "tallon_elevator_beta",
           "tallon_hydro_access"])
    fc.add([f"poke {HEALTH} 63"])
    fc.take_tallon(item_index("tallon_hydro_access"), "5_energy_tank_hydro")
    fc.tp(["tallon_hydro_access", "tallon_great_tree_hall", "tallon_great_tree_chamber"])
    fc.take_tallon(item_index("tallon_great_tree_chamber"), "5_missil_gtc")
    fc.tp(["tallon_great_tree_chamber", "tallon_great_tree_hall", "tallon_life_grove_tunnel"])
    fc.take_tallon(item_index("tallon_life_grove_tunnel"), "5_missil_lgt")
    fc.tp(["tallon_life_grove_tunnel", "tallon_great_tree_hall", "tallon_tunnel_d", "tallon_transport_chozo_south"])
    fc.take_tallon(lock_item("tallon_transport_chozo_south"), "5_plasma")
    fc.add(has_beams(WAVE_BEAM | ICE_BEAM | PLASMA_BEAM | CHARGE_EQUIPMENT))
    fc.tp(["tallon_transport_chozo_south", "tallon_tunnel_d", "tallon_great_tree_hall", "tallon_tunnel_e", "tallon_transport_mines_east"])
    fc.add(whole_screen_bg1(MINES_EAST_BG1_OFFSETS))
    fc.take_tallon(lock_item("tallon_transport_mines_east"), "5_power_bomb")


CHAIN_SOUTH_PAD = 50         # from the Tallon's Chozo South door (door_teleport from Tunnel D) east onto the middle of the platform


def fc_round_6_tallon(fc: FullChain) -> None:
    """Round 6 (+ the Power Bomb, the Plasma), the Tallon's first part (as tallon_cadeia_completa's): the Life Grove's hut broken
    by a power bomb laid in the ball, the X-Ray."""
    m, room = fc.m, fc.room
    fc.round = 6
    xray = item_index("tallon_life_grove")
    hut = [level_block("tallon_life_grove", x, y) for x, y in power_bomb_hut()]
    fc.tp(["tallon_transport_mines_east", "tallon_tunnel_e", "tallon_great_tree_hall", "tallon_life_grove_tunnel", "tallon_life_grove"])
    fc.add([f"poke {HEALTH} 63"] + whole_screen_bg1() + LIFE_GROVE_TO_HUT + [f"expect {SAMUS_X} {HUT_WEST_X:04X}"]
           + [f"expect {a:06X} {POWER_BOMB_BLOCK}" for a in hut] + [fc.shot("6_cabana")] + BALL_RIGHT + fc.select(3)
           + ["hold X 2", "wait 80", fc.shot("6_power_bomb_explodindo"), "wait 220"]
           + [f"expect {a:06X} 00FF" for a in hut])
    fc.pbs -= 1
    fc.add([f"expect {POWER_BOMBS} {fc.pbs:04X}", fc.shot("6_cabana_aberta")] + STAND_UP + [f"expect {POSE} {STAND_POSE}"] + fc.select(0))
    fc.walked_into("tallon", xray, "6_xray", ["hold RIGHT 40"])
    fc.add([f"expectbit 7E09A5 {XRAY_EQUIPMENT >> 8:02X}"])
    fc.tp(["tallon_life_grove", "tallon_life_grove_tunnel", "tallon_great_tree_hall", "tallon_tunnel_d", "tallon_transport_chozo_south"])
    fc.add([f"hold RIGHT {CHAIN_SOUTH_PAD}", "wait 30", f"expect {ELEVATOR_FLAGS} 0001"]
           + ride_elevator(room, "tallon_transport_chozo_south", f"{FULL_SHOT}_6_descendo_south.png")
           + ["hold LEFT 100", "hold LEFT+X 2", "hold LEFT 100", "wait 200", f"expect {ROOM_PTR} {room['chozo_transport_access_south']}",
              "hold LEFT 100", "wait 30"] + chozo_door_shut("chozo_transport_access_south", "chozo_reflecting_pool")
           + [fc.shot("6_gelo_tas_fechada"), "hold LEFT+X 2", "wait 6", fc.shot("6_gelo_tas_abrindo"), "wait 120", "hold LEFT 90",
              "wait 200", f"expect {ROOM_PTR} {room['chozo_reflecting_pool']}", f"expect {GAME_STATE} 0008"])


# specs/12m: the flooded Reflecting Pool for real with the Gravity Suit (chozo_regiao_e_rota put her on the pool's floor by
# RAM): from the R0 ledge west off the step down to the floor beside it, back up the step (POOL_CLIMB, as 12l), west off it
# onto the small platform, up onto the T2 door's platform, under the door, up into the Reflecting Pool Access (steered east)
POOL_R0_TO_FLOOR = ["hold LEFT 60", "wait 60", f"expect 7E0AFA {POOL_FLOOR_Y:04X}"]
POOL_STEP_TO_T2 = (["hold LEFT 50", "wait 60", f"expect 7E0AFA {11 * 16 - 21:04X}"] + zig_jump("RIGHT", 0, 16, 24)
                   + [f"expect 7E0AFA {POOL_PLATFORM_Y:04X}", "hold RIGHT 16", "wait 20"] + climb_jump("RIGHT"))
# the Reflecting Pool Access from its floor door: onto the step, up onto the T0 platform, under the door's east half, up into
# the Hall of the Elders' chamber under the statue (steered west)
RPA_UP_TO_HALL = (["hold RIGHT 20", "hold RIGHT+A 15", "hold RIGHT 10", "wait 40", f"expect 7E0AFA {10 * 16 - 21:04X}"]
                  + zig_jump("LEFT", 0, 16, 24) + [f"expect 7E0AFA {6 * 16 - 21:04X}", "hold LEFT 16", "wait 20"] + climb_jump("LEFT"))
# the Hall of the Elders from its chamber: west through the statue's bomb block into the pit, out onto the floor; then the
# Space Jump for real up to the east balcony (a running spin jump, three presses)
HALL_TO_EAST_BALCONY = ["hold RIGHT 20", "hold RIGHT+A 30"] + ["wait 12", "hold A+RIGHT 30"] * 3 + ["hold RIGHT 40", "wait 60",
                                                                                                f"expect 7E0AFA {10 * 16 - 21:04X}"]
# the Elder Hall Access from its L0 door: onto the T0 platform, up into the Crossway's dip over its floor door (steered east)
EHA_UP_TO_CROSSWAY = (["hold A 22", "hold A+RIGHT 18", "hold RIGHT 10", "wait 50", f"expect 7E0AFA {6 * 16 - 21:04X}", "hold RIGHT 12",
                       "wait 20"] + climb_jump("RIGHT"))


# the Main Plaza from its R1 door: west against the tree hut's east wall, a jump onto its roof, west off it and back east
# against its west wall of power bomb blocks
PLAZA_TO_TREE_HUT = ["hold LEFT 200", "wait 30", "hold RIGHT 20", "hold LEFT 10", "hold LEFT+A 30", "hold LEFT 60", "wait 40",
                     f"expect 7E0AFA {22 * 16 - 21:04X}", "hold LEFT 20", "wait 40", "hold RIGHT 40", "wait 20", "expect 7E0AF6 03BB",
                     f"expect 7E0AFA {26 * 16 - 21:04X}"]


def chain_power_bomb_wall(fc: FullChain, key: str, block: tuple[int, int], toward: str, tag: str) -> list[str]:
    """Samus standing against a wall of power bomb blocks (one of them `block` in room `key`): the beam leaves it, ball, power
    bombs selected, one laid: the block is air in the level in WRAM; back to the beam."""
    at = level_block(key, *block)
    pb = f"{0xC000 | 0x057:04X}"
    out = [f"expect {at:06X} {pb}", fc.shot(f"{tag}_parede"), f"hold {toward}+X 2", "wait 40", f"expect {at:06X} {pb}"]
    out += (BALL_RIGHT if toward == "RIGHT" else BALL_LEFT) + fc.select(3) + ["hold X 2", "wait 80", fc.shot(f"{tag}_power_bomb"),
                                                                              "wait 220", f"expect {at:06X} 00FF"]
    fc.pbs -= 1
    return out + [f"expect {POWER_BOMBS} {fc.pbs:04X}"] + fc.select(0)


def fc_round_6_chozo(fc: FullChain) -> None:
    """Round 6 in the Chozo (+ the Power Bomb, the Plasma, the X-Ray), from the South elevator (fc_round_6_tallon): through
    the flooded Reflecting Pool for real (POOL_R0_TO_FLOOR, POOL_CLIMB, POOL_STEP_TO_T2), up the Reflecting Pool Access into the
    Hall of the Elders' chamber, the statue's bomb block, the Space Jump up to the east balcony, the Elder Hall Access, up its
    ceiling door into the Crossway: its hut of power bomb blocks (Prime's Super Missile plate): the missile. By door_teleport to
    the Magma Pool: down into the pool against the west wall, a power bomb: the expansion in its tunnel. By door_teleport to the
    Main Plaza: from the R1 door west against the tree's hut, over its roof, a power bomb at its west wall: the tree's missile.
    Back to the North elevator by door_teleport, walking onto the platform, UP."""
    from chozo import layouts as chozo_layouts
    m, room = fc.m, fc.room
    fc.add(POOL_R0_TO_FLOOR + [fc.shot("6_piscina_fundo")] + POOL_CLIMB + [f"expect 7E0AFA {POOL_STEP_Y:04X}"] + POOL_STEP_TO_T2
           + [f"expect {ROOM_PTR} {room['chozo_reflecting_pool_access']}", f"expect 7E0AFA {13 * 16 - 21:04X}"] + RPA_UP_TO_HALL
           + [f"expect {ROOM_PTR} {room['chozo_hall_of_the_elders']}", f"expect 7E0AFA {29 * 16 - 21:04X}"] + BALL_LEFT
           + ["hold LEFT 30", "wait 10", "hold X 2", "wait 100",
              f"expect {level_block('chozo_hall_of_the_elders', *chozo_layouts.HALL_B2_BOMB):06X} 00FF", "hold LEFT 60", "wait 30"]
           + STAND_UP + ["hold A+LEFT 30", "hold LEFT 20", "wait 30", f"expect 7E0AFA {26 * 16 - 21:04X}"] + HALL_TO_EAST_BALCONY
           + ["hold RIGHT+X 2", "hold RIGHT 100", "wait 200", f"expect {ROOM_PTR} {room['chozo_elder_hall_access']}"]
           + EHA_UP_TO_CROSSWAY + [f"expect {ROOM_PTR} {room['chozo_crossway']}", f"expect 7E0AFA {29 * 16 - 21:04X}",
                                   "hold RIGHT+A 15", "hold RIGHT 120", "wait 30", "expect 7E0AF6 023B"])
    hut = chozo_layouts.CROSSWAY_HUT
    fc.add(chain_power_bomb_wall(fc, "chozo_crossway", (hut[0], hut[2]), "RIGHT", "6_crossway"))
    fc.walked_into("chozo", chozo_item_index("chozo_crossway"), "6_crossway_missil", ["hold RIGHT 120"])
    fc.add(["hold LEFT 100", "wait 30"] + STAND_UP)
    fc.tp(["chozo_crossway", "chozo_crossway_access_west", "chozo_furnace", "chozo_west_furnace_access", "chozo_energy_core",
           "chozo_energy_core_access", "chozo_east_atrium", "chozo_gathering_hall", "chozo_gathering_hall_access", "chozo_arboretum",
           "chozo_arboretum_access", "chozo_ruined_fountain", "chozo_meditation_fountain", MAGMA])
    fc.add(["hold LEFT 300", "wait 20", "expect 7E0AF6 00A5"]
           + chain_power_bomb_wall(fc, MAGMA, chozo_layouts.MAGMA_PB, "LEFT", "6_magma"))
    fc.walked_into("chozo", chozo_item_index(MAGMA), "6_magma_expansao", BALL_LEFT + ["hold LEFT 120"])
    fc.add(["hold RIGHT 80", "wait 30"] + STAND_UP)
    fc.tp([MAGMA, "chozo_meditation_fountain"])
    fc.add(MEDITATION_UP + [f"expect {ROOM_PTR} {room['chozo_ruined_fountain']}"])
    fc.tp(["chozo_ruined_fountain", FOUNTAIN, "chozo_main_plaza"])
    fc.add(PLAZA_TO_TREE_HUT + chain_power_bomb_wall(fc, "chozo_main_plaza", (chozo_layouts.PLAZA_TREE_HUT[0], chozo_layouts.PLAZA_TREE_HUT[2]),
                                                     "RIGHT", "6_arvore"))
    fc.walked_into("chozo", 2, "6_arvore_missil", ["hold RIGHT 120"])
    fc.add(["hold LEFT 80", "wait 30"] + STAND_UP)
    chain_ride_up_north(fc, ["chozo_main_plaza", "chozo_ruins_entrance"], "6")


def fc_round_6_arbor(fc: FullChain) -> None:
    """Round 6 in the Tallon, last part: the Root Cave climbed again with the Space Jump, its plasma door shot open, the Arbor
    Chamber's missile."""
    m, room = fc.m, fc.room
    fc.tp([WEST, "tallon_tunnel_a", "tallon_canyon", "tallon_root_tunnel", "tallon_root_cave"])
    fc.add(ROOT_CAVE_CLIMB + ["wait 60"] + beam_door_shut("tallon_root_cave", "tallon_arbor_chamber") + [fc.shot("6_porta_de_plasma_fechada")]
           + beam_door_open_and_through(m, room, "tallon_root_cave", "tallon_arbor_chamber", None, "12m_6_porta_de_plasma"))
    fc.take_tallon(item_index("tallon_arbor_chamber"), "6_missil_arbor")


def chain_magmoor_power_bomb(fc: FullChain, key: str, block: tuple[int, int], tag: str) -> list[str]:
    """In the ball against a power bomb block of the Magmoor (`block` of room `key`): power bombs selected, one laid, the block
    is air in the level in WRAM; back to the beam (as magmoor_regiao_b_itens' LAY_POWER_BOMB, with the chain's HUD)."""
    at = level_block(key, *block)
    out = [f"expect {at:06X} {POWER_BOMB_BLOCK}"] + fc.select(3) + ["hold X 2", "wait 80", fc.shot(f"{tag}_power_bomb"), "wait 220",
                                                                     f"expect {at:06X} 00FF"]
    fc.pbs -= 1
    return out + [f"expect {POWER_BOMBS} {fc.pbs:04X}"] + fc.select(0)


def fc_round_6_magmoor(fc: FullChain) -> None:
    """specs/17j, round 6 in the Magmoor (+ the Power Bomb): from the Arbor Chamber by door_teleport to the Tallon's Magmoor East
    transport, WALKING onto the platform, DOWN: the P16. By door_teleport into the Fiery Shores and up its ceiling door into the
    Shore Tunnel (rise_through: a door teleport up there stays in the Fiery Shores), by door_teleport into the Warrior Shrine;
    then magmoor_regiao_b_itens' walk: against its wall, the power bomb block stays after a bomb, a power bomb breaks it; the ball through the tunnel, the R0 door; the Fiery Shores' pocket: the Missile Expansion, in the ball east into
    the Power Bomb Expansion, a power bomb on the block at the tunnel's mouth, out onto the ledges, up onto the T0 platform and
    up through the ceiling door (a real climb) into the Shore Tunnel. Paused: the Magmoor's map (the screens the chain walked).
    Back to the P16 by door_teleport, WALKING onto the platform, UP."""
    m, room = fc.m, fc.room
    missile, expansion = (n for n, it in enumerate(fc.items_of("magmoor").ITEMS) if it.room == "magmoor_fiery_shores")
    chain_ride_down_p23(fc, ["tallon_arbor_chamber", "tallon_root_cave", "tallon_tunnel_b"], "6")
    energy = chain_magmoor_energy(fc)
    fc.tp(["magmoor_transport_tallon_west", "magmoor_transport_tunnel_b", "magmoor_fiery_shores"])
    fc.note("transição de porta de teto por RAM (rise_through)")
    fc.add(rise_through(m, room, "magmoor_fiery_shores", "magmoor_shore_tunnel", 0, "LEFT"))
    fc.tp(["magmoor_shore_tunnel", "magmoor_monitor_station", "magmoor_warrior_shrine"])
    wall = level_block("magmoor_warrior_shrine", 22, 9)
    fc.add(magmoor_full(room, "magmoor_warrior_shrine", 9, energy) + M17H_SHRINE_TO_WALL
           # no beam shot at the wall here (magmoor_regiao_b_itens' proof that the Power Beam leaves it): the Wave and Plasma
           # Beams go through it and open the R0 door behind (measured: the ball then rolls on into the Fiery Shores)
           + [f"expect {wall:06X} {POWER_BOMB_BLOCK}", fc.shot("6m_parede")]
           + MORPH + [f"expect {POSE} {BALL_POSE}", "hold X 2", "wait 120", f"expect {wall:06X} {POWER_BOMB_BLOCK}"]
           + chain_magmoor_power_bomb(fc, "magmoor_warrior_shrine", (22, 9), "6m_parede")
           + [fc.shot("6m_parede_aberta"), "hold RIGHT 60", "wait 10"] + UNMORPH + [f"expect {POSE} {STAND_POSE}"]
           + ["hold LEFT 30", "hold RIGHT 2", "wait 5", "hold X 2", "wait 30", "hold RIGHT 100", "wait 200"]
           + magmoor_full(room, "magmoor_fiery_shores", 9, energy) + enemies_alive(MAGMOOR, "magmoor_fiery_shores")
           + [fc.shot("6m_bolso")])
    fc.walked_into("magmoor", missile, "6m_fiery_shores_missil", ["hold RIGHT 30"])
    fc.add(["hold RIGHT 40", "wait 10"] + MORPH)
    fc.walked_into("magmoor", expansion, "6m_fiery_shores_expansao", ["hold RIGHT 40"])
    fc.add(chain_magmoor_power_bomb(fc, "magmoor_fiery_shores", (17, 9), "6m_boca")
           + ["hold RIGHT 60", "wait 30"] + UNMORPH + [f"expect 7E0AFA {16 * 16 - 21:04X}"] + M17H_SHORES_UP
           + [f"expect 7E0AFA {6 * 16 - 21:04X}", f"expect {HEALTH} {energy:04X}", fc.shot("6m_plataforma")]
           + M17H_RISE + magmoor_full(room, "magmoor_shore_tunnel", 12, energy))
    fc.screens |= {("magmoor_warrior_shrine", 0, 0), ("magmoor_warrior_shrine", 1, 0), ("magmoor_fiery_shores", 0, 0),
                   ("magmoor_shore_tunnel", 2, 0)}
    screens = sorted(s for s in fc.screens if s[0].startswith("magmoor_"))
    fc.add([explored_at(*sc) for sc in screens] + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
           + pause_shows(MAGMOOR, screens, "17j_magmoor") + [fc.shot("6m_mapa_magmoor"), "hold START 10", "wait 200",
                                                            f"expect {GAME_STATE} 0008"])
    # specs/18n: round 6 goes on up into Phendrana by its north elevator (fc_round_6_phendrana) and comes back by the south one


def chain_door_path(start: str, goal: str) -> list[str]:
    """specs/19m: the built rooms from `start` to `goal` through their doors (breadth first, in door order), for fc.tp."""
    prev, queue = {start: None}, [start]
    while queue:
        k = queue.pop(0)
        for d in built_room(k).doors:
            if d.to_room not in prev:
                prev[d.to_room] = k
                queue.append(d.to_room)
    path = [goal]
    while prev[path[-1]]:
        path.append(prev[path[-1]])
    return list(reversed(path))


# specs/19m: facing east before onto_platform (as the elevator tests, which come in through a west door): put by RAM facing west
# its 4 frames right and 4 left left her 1-2 px off the platform's middle (measured)
CHAIN_FACE_EAST = ["hold RIGHT 2", "wait 20"]


def chain_ride(fc: FullChain, key: str, tag: str, east: int = 2) -> None:
    """fc.ride with the chain's gear: onto_platform's 4 frames right and 4 left end 2 px east of the middle with all the chain's
    gear (measured at the Tallon's P43 and the Mines' P0 and P25; elevator_flags on all the same), so that spot is checked.
    specs/20j: `east` px (the Artifact Temple's teleporter: 1, measured)."""
    e = built_room(key).elevator
    x = (e.x + 1) * 16
    lines = onto_platform(key)
    assert lines[-1] == f"expect 7E0AF6 {x:04X}"
    fc.note("Samus posta na plataforma do elevador")
    fc.add(CHAIN_FACE_EAST + lines[:-1] + [f"expect 7E0AF6 {x + east:04X}"]
           + ride_elevator(fc.room, key, f"{FULL_SHOT}_{fc.seq:03d}_{tag}.png"))


def chain_mines_refill(fc: FullChain) -> int:
    """specs/19m: as chain_phendrana_refill (the same shortcuts, counted), where the Mines' walks start and after a fight."""
    return chain_phendrana_refill(fc)


def chain_mines_bomb_then_pb(fc: FullChain, key: str, block: tuple[int, int], tag: str) -> list[str]:
    """In the ball (already rolled up) against a power bomb block of the Mines (`block` of room `key`): a bomb leaves it, a power
    bomb (the chain's HUD) breaks it; back to the beam (as the region tests' bomb_then_pb)."""
    at = level_block(key, *block)
    out = ["hold X 2", "wait 150", f"expect {at:06X} C057", fc.shot(f"{tag}_bomba")] + fc.select(3) + ["hold X 2", "wait 300"]
    fc.pbs -= 1
    return out + [f"expect {at:06X} 00FF", f"expect {POWER_BOMBS} {fc.pbs:04X}"] + fc.select(0)


# specs/19m: the Phazon Elite fought for real in the chain (round 5: the Wave, Ice, Plasma and Charge Beams), from the chain's own
# entry (door_teleport from the Research Access, as mines_phazon_elite's): moves of MAGMOOR_MOVES (searched from that state)
CHAIN_ELITE_FIGHT = ELITE_FIGHT
# specs/19m: the Omega Pirate fought for real in the chain (round 6), from the chain's own entry (door_teleport from the Elite
# Quarters Access, as mines_omega_pirate's): missiles (searched from that state: scratchpad s19m)
CHAIN_OMEGA_FIGHT = OMEGA_FIGHT


def chain_fight(fc: FullChain, fight: str, tag: str, death: int) -> None:
    """A boss fight for real: the moves; its health 0, its death, the slot empty, the song stopped; no RAM. The fight's SELECTs
    ("S") move the chain's HUD item (fc.hud) as SM does."""
    order = ([0] + [1] * (fc.max_missiles > 0) + [2] * (fc.max_supers > 0) + [3] * (fc.max_pbs > 0) + [4] * fc.grapple
             + [5] * fc.xray)
    for _ in range(fight.count("S")):
        fc.hud = order[(order.index(fc.hud) + 1) % len(order)]
    fc.add([fc.shot(f"{tag}_entrada")] + moves(fight) + [f"expect {ENEMY_TABLE + ENEMY_HEALTH:06X} 0000", fc.shot(f"{tag}_morrendo"),
                                                         f"wait {death}", f"expect {ENEMY_TABLE:06X} 0000", "expect 7E07F5 0000",
                                                         fc.shot(f"{tag}_vitoria")])


def fc_round_5_mines(fc: FullChain) -> None:
    """specs/19m, round 5 in the Mines (+ the Gravity Suit, the Plasma Beam, the Power Bomb): from the Tallon's P43 (fc_round_5 took
    the Power Bomb there) DOWN the east elevator: the P0. Region A walked as mines_regiao_a_rota: the Quarry Access, the Main
    Quarry down to the basin, the Space Jump up the crane tower: its missile; off it onto the floor door's ice cap, the Waste
    Disposal, the Ore Processing, the Storage Depot B: the GRAPPLE BEAM. By door_teleport the Elite Research by its R0: the PHAZON
    ELITE fought for real (CHAIN_ELITE_FIGHT, the bit $08), its missile in the west corner. By door_teleport the Elevator A: down
    its zigzag, the Elite Control Access' missile; by door_teleport the Central Dynamo by its R0: down into the pit, the ball
    through the maze (a bomb on the bomb block), its missile (Prime's Power Bomb's place). By door_teleport back to the P0, UP."""
    m, room = fc.m, fc.room
    chain_ride(fc, TALLON_TO_MINES, "5_descendo_mines")
    energy = chain_mines_refill(fc)
    full = lambda key, feet: mines_full(room, key, feet, energy)   # noqa: E731
    fc.add(["hold RIGHT 4", "wait 10"] + moves("D") + full("mines_quarry_access", 25) + moves(M19F_QUARRY_ACCESS + "D")
           + full("mines_main_quarry", 9) + [fc.shot("5mi_main_quarry")] + moves(M19F_QUARRY_DOWN) + M19F_TOWER_UP
           + [f"expect 7E0AFA {14 * 16 - 21:04X}"])
    fc.walked_into("mines", 0, "5mi_torre_missil", ["hold LEFT 12"])
    fc.add(M19F_TOWER_OFF + SHOOT_DOWN + ["wait 200"] + full("mines_waste_disposal", 5) + M19F_WASTE
           + full("mines_ore_processing", 9) + M19F_ORE_DOWN + full("mines_ore_processing", 25) + moves(M19F_ORE_TO_DEPOT)
           + full("mines_storage_depot_b", 9))
    fc.walked_into("mines", 2, "5mi_grapple", ["hold RIGHT 30"])
    fc.tp(["mines_storage_depot_b", "mines_ore_processing", "mines_research_access", ELITE])
    fc.add(full(ELITE, 9))
    chain_fight(fc, CHAIN_ELITE_FIGHT, "5mi_phazon_elite", ELITE_DEATH)
    fc.add(["expectbit 7ED82D 08"])
    energy = chain_mines_refill(fc)
    fc.walked_into("mines", 3, "5mi_elite_research_missil", ["hold LEFT 600"])
    fc.tp(chain_door_path(ELITE, "mines_elevator_access_a") + ["mines_elevator_a"])
    fc.add(full("mines_elevator_a", 9) + M19I_EA_DOWN + full("mines_elevator_a", 41) + M19F_OUT["RIGHT"]
           + full("mines_elite_control_access", 9))
    fc.walked_into("mines", 4, "5mi_eca_missil", M19I_ECA_TO_MISSILE)
    cd = "mines_central_dynamo"
    fc.tp(chain_door_path("mines_elite_control_access", "mines_dynamo_access") + [cd])
    maze = level_block(cd, 31, 28)
    fc.add(full(cd, 9) + M19I_DOWN_WEST + full(cd, 28) + MORPH
           + ["hold LEFT 60", "wait 10", f"expect {maze:06X} F058", "hold X 2", "wait 120", f"expect {maze:06X} 00FF"])
    fc.walked_into("mines", 6, "5mi_dynamo_missil", ["hold LEFT 150"])
    fc.add(["hold RIGHT 200", "wait 10"] + UNMORPH + [f"expect {POSE} {STAND_POSE}"])
    fc.tp(chain_door_path(cd, MINES_EAST))
    chain_ride(fc, MINES_EAST, "5_subindo_mines")


def fc_round_6_mines(fc: FullChain) -> None:
    """specs/19m, round 6 in the Mines (+ the X-Ray): from the Tallon's Magmoor East transport (fc_round_6_phendrana came up the
    P16) DOWN to the Magmoor's P16, by door_teleport to its P26, DOWN the west elevator: the P25. Region C walked as
    mines_regiao_c_rota: the Transport Access, the Phazon Processing Center down to its floor, the pit's power bomb blocks (a bomb
    leaves them, a power bomb breaks them): its missile; up the zigzag, the plasma door: the Processing Center Access' ENERGY TANK.
    By door_teleport the Elite Quarters by its L1 (from the access, as mines_omega_pirate's): the OMEGA PIRATE fought for real
    (CHAIN_OMEGA_FIGHT, the bits $04 and $10), out by the L1. Region D walked as mines_regiao_d_rota: the floor door's plasma cap,
    the Metroid Quarantine B down to the floor, the Space Jump up the column: its missile; by door_teleport the Quarantine Access B
    (its orb killed by a missile), the Fungal Hall B's missile; by door_teleport the Fungal Hall Access' missile. By door_teleport
    the power bomb rooms of regions A and B (mines_regiao_a_rodada_6, mines_regiao_b_rodada_6): the Security Access A's niche
    missile, the Ventilation Shaft's duct ENERGY TANK, the Metroid Quarantine A's missile. By door_teleport to the P0, UP the east
    elevator; by door_teleport to the Magmoor East transport (fc_end starts there)."""
    m, room = fc.m, fc.room
    chain_ride_down_p23(fc, [], "6mi")
    fc.tp(chain_door_path(MAGMOOR_FROM_TALLON, MAGMOOR_TO_MINES))
    chain_ride(fc, MAGMOOR_TO_MINES, "6_descendo_mines_oeste")
    energy = chain_mines_refill(fc)
    full = lambda key, feet: mines_full(room, key, feet, energy)   # noqa: E731
    ppc = "mines_phazon_processing_center"
    fc.tp([MINES_WEST, "mines_transport_access"])
    fc.add(full("mines_transport_access", 9) + M19J_TA_EAST + M19F_OUT["RIGHT"] + full(ppc, 9) + M19I_DOWN_EAST + full(ppc, 41)
           + M19J_PPC_TO_NICHE + MORPH + chain_mines_bomb_then_pb(fc, ppc, (33, 42), "6mi_fosso") + UNMORPH)
    fc.walked_into("mines", 8, "6mi_ppc_missil", ["hold LEFT 90"])
    fc.add(M19I_PIT_OUT["LEFT"] + ["hold LEFT 900", "wait 30"] + M19I_OR_UP + full(ppc, 25) + M19F_OUT["LEFT"]
           + full("mines_processing_center_access", 9))
    fc.walked_into("mines", 9, "6mi_pca_tanque", ["hold LEFT 120"])
    energy = fc.max_energy
    fc.add([f"expect {HEALTH} {energy:04X}"])
    fc.tp(["mines_processing_center_access", OMEGA, "mines_elite_quarters_access", OMEGA])
    chain_fight(fc, CHAIN_OMEGA_FIGHT, "6mi_omega_pirate", OMEGA_DEATH)
    fc.add(["expectbit 7ED82D 14"] + fc.select(0) + ["hold LEFT 400", "wait 20"] + moves("E")
           + [f"expect {ROOM_PTR} {room['mines_elite_quarters_access']}"])
    eqa = "mines_elite_quarters_access"
    # walked in through the L1 she comes in running: back by door_teleport through the dead arena (omega_dead), in again as
    # mines_regiao_d_rota comes in (its walk to the floor door's cap was measured from there)
    fc.tp([eqa, OMEGA])
    fc.add(["wait 60"] + omega_dead(room))
    fc.tp([OMEGA, eqa])
    energy = chain_mines_refill(fc)
    fc.add(full(eqa, 9) + M19J_EQA_DOWN + M19L_EQA_TO_FLOOR_DOOR + full(eqa, 12) + SHOOT_DOWN + ["wait 300"]
           + full("mines_metroid_quarantine_b", 5) + M19L_MQB_DOWN + full("mines_metroid_quarantine_b", 44))
    fc.walked_into("mines", 10, "6mi_mqb_missil", M19L_MQB_UP)
    fc.tp(["mines_metroid_quarantine_b", "mines_quarantine_access_b"])
    fc.add(full("mines_quarantine_access_b", 9) + ["hold RIGHT 2", "wait 10"] + fc.select(1) + ["hold X 2", "wait 60",
                                                                                               f"expect {ENEMY_TABLE:06X} 0000"]
           + fc.select(0) + ["hold RIGHT 300", "wait 20"] + M19F_OUT["RIGHT"] + full("mines_fungal_hall_b", 25))
    # the missile at the orb comes back: it drops one (measured), so the count is as before
    fc.walked_into("mines", 11, "6mi_fhb_missil", M19L_FHB_TO_MISSILE)
    fc.tp(["mines_fungal_hall_b", "mines_phazon_mining_tunnel", "mines_fungal_hall_a", "mines_fungal_hall_access"])
    fc.add(full("mines_fungal_hall_access", 41))
    fc.walked_into("mines", 12, "6mi_fhac_missil", M19L_FHAC_TO_MISSILE)
    saa, vs, mqa = "mines_security_access_a", "mines_ventilation_shaft", "mines_metroid_quarantine_a"
    fc.tp(chain_door_path("mines_fungal_hall_access", "mines_main_quarry") + [saa])
    fc.add(full(saa, 9) + ["hold LEFT 130", "wait 20"] + MORPH + chain_mines_bomb_then_pb(fc, saa, (24, 10), "6mi_nicho") + UNMORPH)
    fc.walked_into("mines", 1, "6mi_saa_missil", ["hold LEFT 20"])
    fc.add(["hold LEFT+A 30", "hold LEFT 200", "wait 20"])
    fc.tp(chain_door_path(saa, "mines_elite_control") + [vs])
    duct = level_block(vs, 16, 10)
    out = full(vs, 9) + M19I_VS_MELLA + [f"expect {ENEMY_TABLE:06X} 0000"] + MORPH
    out += ["hold X 2", "wait 150", f"expect {duct:06X} C057", fc.shot("6mi_duto_bomba")] + fc.select(3)
    fc.add(out)
    fc.pbs -= 1
    fc.walked_into("mines", 5, "6mi_vs_tanque", ["hold X 2", "wait 300", "hold RIGHT 30"])
    energy = fc.max_energy
    fc.add([f"expect {duct:06X} 00FF", f"expect {POWER_BOMBS} {fc.pbs:04X}", f"expect {HEALTH} {energy:04X}"] + fc.select(0)
           + UNMORPH)
    fc.tp(chain_door_path(vs, "mines_quarantine_access_a") + [mqa])
    fc.add(["hold RIGHT 400", "wait 30"] + full(mqa, 25) + MORPH + chain_mines_bomb_then_pb(fc, mqa, (84, 24), "6mi_quarentena")
           + UNMORPH)
    fc.walked_into("mines", 7, "6mi_mqa_missil", ["hold RIGHT 200"])
    fc.tp(chain_door_path(mqa, MINES_EAST))
    chain_ride(fc, MINES_EAST, "6_subindo_mines")
    fc.tp(tallon_door_path(TALLON_TO_MINES, TALLON_TO_MAGMOOR))


def item_percentage(rom: bytes, max_energy: int, max_reserve: int, max_missiles: int, max_supers: int, max_pbs: int,
                    items: int, beams: int) -> int:
    """The item percentage of the game's ending (CalcItemPercentageCount, $8B:E627; its tables read from the ROM's bytes:
    the 5 ammo/energy words at $8B:E70D and their divisors at $8B:E717, the 11 item bits at $8B:E721, the 5 beam bits at
    $8B:E737)."""
    from smlib.rom import snes_to_pc

    def words(addr: int, n: int) -> list[int]:
        p = snes_to_pc(addr)
        return [rom[p + 2 * i] | rom[p + 2 * i + 1] << 8 for i in range(n)]

    value = {0x09C4: max_energy, 0x09D4: max_reserve, 0x09C8: max_missiles, 0x09CC: max_supers, 0x09D0: max_pbs}
    n = sum(value[a] // d for a, d in zip(words(0x8BE70D, 5), words(0x8BE717, 5)))
    n += sum(bool(b & items) for b in words(0x8BE721, 11)) + sum(bool(b & beams) for b in words(0x8BE737, 5))
    return n


FULL_CHAIN_ITEMS = (MORPH_BALL_EQUIPMENT | BOMB_ITEM_EQUIPMENT | GRAVITY_SUIT | SPACE_JUMP_EQUIPMENT | XRAY_EQUIPMENT | VARIA_EQUIPMENT
               | GRAPPLE_EQUIPMENT)   # specs/19m: the Mines' Grapple Beam
FULL_CHAIN_BEAMS = WAVE_BEAM | ICE_BEAM | PLASMA_BEAM | CHARGE_EQUIPMENT


def chain_percent(fc: FullChain) -> int:
    """The item percentage of the game's ending computed (item_percentage, the built ROM's tables) from what the chain took (its
    capacities, FULL_CHAIN_ITEMS, FULL_CHAIN_BEAMS): it must be one per item taken, every placed item of the five areas taken, and
    CHAIN_END_PERCENT, else the script is not made (specs/19m; specs/20j: fc_end and the crater's ending, fc_crater_ending)."""
    pct = item_percentage(ROM.read_bytes(), fc.max_energy, 0, fc.max_missiles, fc.max_supers, fc.max_pbs, FULL_CHAIN_ITEMS, FULL_CHAIN_BEAMS)
    n_items = len(fc.taken)
    placed = sum(len(fc.items_of(a).placed(set(area.by_key())))
                 for a, area in zip(CHAIN_AREAS, (TALLON, CHOZO, MAGMOOR, PHENDRANA, MINES)))
    if pct != n_items or n_items != placed or pct != CHAIN_END_PERCENT:
        raise ValueError(f"cadeia 19m: {n_items} itens de {placed}, porcentagem do fim {pct}% (o épico 19: {CHAIN_END_PERCENT}%)")
    return pct


def fc_end(fc: FullChain) -> None:
    """The 58 item bits ($7ED884-$7ED88B: $A0-$D9; specs/17j: the Magmoor's $D3-$D9 too; specs/18n: 75, Phendrana's $DA-$EA, to
    $7ED88D), the items and beams, the capacities (specs/18n: the super missiles' too); the item percentage of the game's ending
    computed from them (item_percentage) = 75, one per item; back to the gunship (door_teleport from the Magmoor East transport,
    then Samus put on it by RAM, as tallon_cadeia_completa), saved, game over, continue: all of it comes back, the explored
    screens of the four areas the chain went through too (the Chozo's in area 1's saved copy, the Magmoor's in area 2's,
    Phendrana's in area 4's); the pause map of the Tallon, the equipment screen; down the North elevator once more: the Chozo's
    pause map."""
    m, room = fc.m, fc.room
    fc.check_order()
    items, beams = FULL_CHAIN_ITEMS, FULL_CHAIN_BEAMS
    chain_percent(fc)
    bits =[0x7ED884, 0x7ED886, 0x7ED888, 0x7ED88A, 0x7ED88C, 0x7ED88E]   # specs/19m: the Mines' $EB-$F7 too
    have = [fc.word(8 * (a - 0x7ED870)) for a in bits] + [
        f"expect {COLLECTED_ITEMS} {items:04X}", f"expect 7E09A2 {items:04X}"] + has_beams(beams) + [
        f"expect {MAX_MISSILES} {fc.max_missiles:04X}", f"expect {MAX_POWER_BOMBS} {fc.max_pbs:04X}",
        f"expect {MAX_ENERGY} {fc.max_energy:04X}", "expect 7E09D4 0000", f"expect {MAX_SUPERS} {fc.max_supers:04X}"]
    tallon_screens = sorted(s for s in fc.screens if s[0].startswith("tallon_"))
    chozo_screens = sorted(s for s in fc.screens if s[0].startswith("chozo_"))
    magmoor_screens = sorted(s for s in fc.screens if s[0].startswith("magmoor_"))
    phendrana_screens = sorted(s for s in fc.screens if s[0].startswith("phendrana_"))
    explored = ([explored_at(*s) for s in tallon_screens]
                + [explored_at(*s, saved_area=CHOZO.number) for s in chozo_screens]
                + [explored_at(*s, saved_area=MAGMOOR.number) for s in magmoor_screens]
                + [explored_at(*s, saved_area=PHENDRANA.number) for s in phendrana_screens])
    fc.tp([TALLON_TO_MAGMOOR, "tallon_tunnel_b", "tallon_root_cave", "tallon_root_tunnel", "tallon_canyon", "tallon_canyon_cavern",
           "tallon_landing_site"])
    fc.note("Samus posta em cima da nave")
    fc.add(have + ["hold UP 2", "wait 60"] + stand_on_tallon_ship() + [line.replace("wait 600", "wait 1700") for line in   # specs/19m: up to 1499 energy: the refill takes up to ~1500 frames
                                                                        save_on_tallon_ship(f"{FULL_SHOT}_fim_save.png", fc.max_energy)]
           + ["poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}"]
           + GAME_OVER_CONTINUE + [f"expect {GAME_STATE} 0008", f"expect {ROOM_PTR} {room[LANDING_SITE]}"] + have + explored
           + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
           + pause_shows(TALLON, tallon_screens, "12m_tallon") + [f"shot {FULL_SHOT}_fim_mapa_tallon.png", "hold START 10", "wait 200"]
           + equipment_screen(f"{FULL_SHOT}_fim_equipamento.png"))
    # specs/20j: the gunship refills the ammo too (the game's own): what the save and the continue give back, the crater's part
    # (part 6) starts from it
    fc.missiles, fc.supers, fc.pbs = fc.max_missiles, fc.max_supers, fc.max_pbs
    fc.add([f"expect {MISSILES} {fc.missiles:04X}", f"expect {SUPERS} {fc.supers:04X}", f"expect {POWER_BOMBS} {fc.pbs:04X}"])
    chain_ride_down_west(fc, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a"], "fim")
    fc.add(["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
           + pause_shows(CHOZO, chozo_screens, "12m_chozo") + [f"shot {FULL_SHOT}_fim_mapa_chozo.png", "hold START 10", "wait 200"])


# specs/18n: the ending's screen: at the end of SM's ending and credits SM draws "YOUR RATE FOR COLLECTING ITEMS IS ...%":
# CalcItemPercentageCount ($8B:E627) writes its digits' tile words in the credits' tilemap in WRAM ($7E339C/$33DC hundreds,
# $339E/$33DE tens, $33A0/$33E0 ones, from the table at $8B:E741, and $33A2/$33E2 the % sign). specs/20j: the chain reaches the
# ending for real (the Impact Crater, the Metroid Prime beaten, the Lair's ceiling door: specs/20i), no longer by the event $0E by
# RAM on the gunship (18n-19m's shortcut, gone)
CHAIN_END_PERCENT = 88   # epic 19: Tallon 20 + Chozo 31 + Magmoor 7 + Phendrana 17 + Mines 13 items, one point each (epic 18: 75); epic 20: the crater has none (specs/20a)


def ending_digits(rom: bytes, pct: int) -> list[str]:
    """`expect` lines of the ending's item rate `pct` in the credits' tilemap (CalcItemPercentageCount's writes): the tens' and
    the ones' digit tiles (top and bottom halves, from $8B:E741), the hundreds' left as it was when 0 (written only when not 0)
    and the % sign."""
    from smlib.rom import snes_to_pc

    def word(addr: int) -> int:
        p = snes_to_pc(addr)
        return rom[p] | rom[p + 1] << 8
    hundreds, tens, ones = pct // 100, pct // 10 % 10, pct % 10
    out = []
    if hundreds:
        out += [f"expect 7E339C {word(0x8BE741 + 4 * hundreds):04X}", f"expect 7E33DC {word(0x8BE743 + 4 * hundreds):04X}"]
    if hundreds or tens:
        out += [f"expect 7E339E {word(0x8BE741 + 4 * tens):04X}", f"expect 7E33DE {word(0x8BE743 + 4 * tens):04X}"]
    return out + [f"expect 7E33A0 {word(0x8BE741 + 4 * ones):04X}", f"expect 7E33E0 {word(0x8BE743 + 4 * ones):04X}",
                  "expect 7E33A2 386A", "expect 7E33E2 387A"]


# specs/20j: Metroid Prime fought for real in the chain (round 6, all the chain's items), from the chain's own entry (door_teleport
# from the Subchamber Five, as prime_entry's). 20h's PRIME_FIGHT does not win from there (measured: 2100 of 3000 left, the fight
# goes otherwise from the chain's state): moves of MAGMOOR_MOVES searched from this entry as 20h's (scratchpad s20j/greedy.py,
# s20h's: each step every pair of candidate moves, the best by its health lost, Samus' energy)
CHAIN_PRIME_FIGHT = "xXXRsRsassaasaasahs"   # the beams (Plasma + Ice + Wave, 300 a hit): its health 0
CHAIN_PRIME_ENERGY_LOST = 2   # one touch (measured: 1499 -> 1497)
# the fight ends at x 640 (20h's at 830, where M20H_UP starts): east along the floor to 830 first (measured: 66-74 frames end at
# 819-841 and M20H_UP still lands on the ceiling door's platform)
CHAIN_PRIME_EAST = ["hold RIGHT 70", "wait 30", "expect 7E0AF6 033E"]


def fc_crater(fc: FullChain) -> None:
    """specs/20j, the Impact Crater (round 6, every item; no item there, specs/20a): from the Chozo's North transport (fc_end left
    her there) UP the North elevator; by door_teleport to the Artifact Temple: its platform there (the Omega Pirate beaten for
    real in fc_round_6_mines: the bit $10 of area 5, no RAM); DOWN the teleporter: the Entry Point, area 0. Regions A, B and C
    WALKED as impact_regiao_b_rota and impact_descida_rota (the plasma caps shot open): east through the Tunnel A, the Phazon Core
    along its floor, up its east zigzag onto the R1 shelf, the Tunnel B, the Infusion Chamber down its ledges into the hole (no
    door), the Subchamber One's platform, west down its zigzag to the L2: the Subchamber Two. By door_teleport (no lock: Prime's
    fall) the Subchambers Three, Four and Five and into the Lair through the Five's floor door (as prime_entry): the arena alive;
    METROID PRIME fought for real (CHAIN_PRIME_FIGHT, no RAM), the bits $04 and $10 of area 0; WALKING east along the floor to
    where 20h's fight ends (CHAIN_PRIME_EAST) and up the zigzag onto the ceiling door's platform (M20H_UP)."""
    m, room = fc.m, fc.room
    chain_ride_up_north(fc, [], "ic")
    fc.tp(chain_door_path(WEST, TEMPLE))
    fc.add([f"expect {ENEMY_TABLE:06X} D73F", "expectbit 7ED82D 10", fc.shot("ic_templo")])
    chain_ride(fc, TEMPLE, "ic_descendo_cratera", east=1)   # 1 px east here (measured)
    fc.add([f"expect {AREA} 0000"])
    energy = chain_mines_refill(fc)
    full = lambda key, feet: mines_full(room, key, feet, energy)   # noqa: E731
    fc.add(M19F_OUT["RIGHT"] + full(CRATER_TUNNEL_A, 9) + ["hold RIGHT 400", "wait 30"] + M19F_OUT["RIGHT"]
           + full(CRATER_CORE, 41) + [fc.shot("ic_phazon_core")] + ["hold RIGHT 900", "wait 30"] + M20F_EAST_UP
           + full(CRATER_CORE, 25) + M19F_OUT["RIGHT"] + full(CRATER_TUNNEL_B, 9) + ["hold RIGHT 400", "wait 30"]
           + M19F_OUT["RIGHT"] + full(CRATER_INFUSION, 9) + [fc.shot("ic_infusion")] + M20G_INTO_HOLE + full(CRATER_SUB1, 5)
           + M20G_TO_L2 + full(CRATER_SUB1, 41) + M19F_OUT["LEFT"] + full(CRATER_SUB2, 9) + [fc.shot("ic_subchamber_two")])
    fc.tp(chain_door_path(CRATER_SUB2, CRATER_LAIR))
    from chozo import bosses
    arena = bosses.arena_of(CRATER_LAIR)
    fc.add([f"expect {GAME_STATE} 0008"] + enemies_alive(TALLON, CRATER_LAIR)
           + ["expect 7E0F7A 0308", "expect 7E0F7E 0170", f"expect 7E07F3 {arena.music[0]:04X}",
              f"expect {plm_slot(PLM_HEADERS, PRIME_DOOR_SLOT)} C854", f"expect {HEALTH} {energy:04X}"])
    chain_fight(fc, CHAIN_PRIME_FIGHT, "ic_metroid_prime", PRIME_DEATH)
    fc.add(["expectbit 7ED828 14", f"expect {HEALTH} {energy - CHAIN_PRIME_ENERGY_LOST:04X}"] + fc.select(0) + CHAIN_PRIME_EAST
           + M20H_UP
           + [f"expect {ROOM_PTR} {room[CRATER_LAIR]}", f"expect 7E0AFA {6 * 16 - 21:04X}", f"expect {GAME_STATE} 0008",
              fc.shot("ic_plataforma")])


def fc_crater_ending(fc: FullChain) -> None:
    """specs/20j, the game's end (specs/20i) with the chain's real items: on the Lair's ceiling door platform, the 88 item bits,
    the items, beams and capacities the chain took (fc_end's checks; nothing by RAM); a shot opens the cap, the spin jump up into
    the door (M20I_EXIT): in the Lair still, game state $26, Samus held still (EXIT_LOCK_Y); $27 (SM's ending: no door
    transition); the credits; at their end the rate screen with the digits CalcItemPercentageCount wrote for the percentage
    COMPUTED from the chain's own gear (chain_percent: one per item, every placed item taken, CHAIN_END_PERCENT), the cinematic at
    its last function (ENDING_DONE) for good."""
    room = fc.room
    fc.check_order()
    pct = chain_percent(fc)
    rom = ROM.read_bytes()
    bits = [0x7ED884, 0x7ED886, 0x7ED888, 0x7ED88A, 0x7ED88C, 0x7ED88E]
    fc.add([fc.word(8 * (a - 0x7ED870)) for a in bits]
           + [f"expect {COLLECTED_ITEMS} {FULL_CHAIN_ITEMS:04X}", f"expect 7E09A2 {FULL_CHAIN_ITEMS:04X}"] + has_beams(FULL_CHAIN_BEAMS)
           + [f"expect {MAX_MISSILES} {fc.max_missiles:04X}", f"expect {MAX_POWER_BOMBS} {fc.max_pbs:04X}",
              f"expect {MAX_ENERGY} {fc.max_energy:04X}", "expect 7E09D4 0000", f"expect {MAX_SUPERS} {fc.max_supers:04X}"]
           + M20I_EXIT + [f"expect {ROOM_PTR} {room[CRATER_LAIR]}", f"expect {GAME_STATE} 0026",
                          f"expect 7E0AFA {EXIT_LOCK_Y:04X}", fc.shot("ic_saida"), "wait 30",
                          f"expect {GAME_STATE} 0027", f"expect {ROOM_PTR} {room[CRATER_LAIR]}",
                          f"wait {ENDING_CREDITS_AT - 30}", f"expect {GAME_STATE} 0027", fc.shot("ic_creditos"),
                          f"wait {ENDING_RATE_AT - ENDING_CREDITS_AT}", f"expect {GAME_STATE} 0027",
                          f"expect 7E1F51 {ENDING_DONE:04X}"]
           + ending_digits(rom, pct) + [f"shot {FULL_SHOT}_fim_porcentagem.png", "wait 2000", f"expect {GAME_STATE} 0027",
                                        f"expect 7E1F51 {ENDING_DONE:04X}"] + ending_digits(rom, pct))


def full_chain(m: dict, room: dict) -> list[list[str]]:
    """"""
    fc = FullChain(m, room)
    parts, handoff = [], []
    for k, (steps, end_room) in enumerate(CHAIN_PARTS):
        lines = [f"load {chain_state(k - 1)}"] + handoff if k else []
        n0 = len(fc.out)
        for step in steps:
            step(fc)
        lines += fc.out[n0:]
        if k < len(CHAIN_PARTS) - 1:
            handoff = chain_handoff(fc, end_room)
            lines += handoff + [f"save {chain_state(k)}"]
        parts.append(lines)
    return parts


# specs/17j: the full chain's parts (each a test, cadeia_completa_parte_<k+1>): its steps and the room where it ends. Split by
# rounds (one test was ~5.2 min alone before the Magmoor, near the tool's limit of one run): rounds 0-2 (group A), round 3 in
# the three areas and rounds 4-6 with the end (group B, run one after the other: run_chain_parts). specs/18n: four parts: rounds
# 0-2 (group A, as before), round 3 in the Chozo and the Magmoor (group B, to the Workstation), round 3 in Phendrana and the
# Tallon (group C), rounds 4-6 in the four areas, the end and the ending's screen (group C). specs/19m: five (see CHAIN_GROUP).
# specs/20j: six: part 5 = round 6 in the five areas and fc_end (to the Chozo's North transport), part 6 = the Impact Crater,
# Metroid Prime fought for real and the game's end through the Lair's ceiling door, with the ending's screen (both group D)
CHAIN_PARTS = (
    ((fc_round_0, fc_round_1_chozo, fc_round_1_up, fc_round_1_tallon, fc_round_2_tallon, fc_round_2_chozo_a, fc_round_2_chozo_b,
      fc_round_2_chozo_c, fc_round_2_chozo_d, fc_round_2_chozo_e, fc_round_2_chozo_f, fc_round_2_chozo_g),
     "chozo_training_chamber_access"),
    ((fc_round_3_chozo_a, fc_round_3_chozo_b, fc_round_3_magmoor), "magmoor_workstation"),
    ((fc_round_3_phendrana_up, fc_round_3_phendrana_a, fc_round_3_phendrana_sheegoth, fc_round_3_phendrana_shore,
      fc_round_3_phendrana_ruins, fc_round_3_phendrana_labs, fc_round_3_phendrana_quarantine,
      fc_round_3_phendrana_thardus, fc_round_3_phendrana_down, fc_round_3_tallon),
     "tallon_root_cave"),
    ((fc_round_4_magmoor, fc_round_4_phendrana, fc_round_4, fc_round_5_phendrana, fc_round_5, fc_round_5_mines),
     TALLON_TO_MINES),
    ((fc_round_6_tallon, fc_round_6_chozo, fc_round_6_arbor, fc_round_6_magmoor, fc_round_6_phendrana, fc_round_6_mines, fc_end),
     NORTH),
    ((fc_crater, fc_crater_ending), None),   # specs/20j: the Impact Crater, Metroid Prime and the game's end (group D, after part 5)
)
CHAIN_TESTS = tuple(f"cadeia_completa_parte_{k + 1}" for k in range(len(CHAIN_PARTS)))


def chain_state(k: int) -> str:
    """The emulator's state saved at the end of part k of the full chain (relative to the project: snesrun runs there)."""
    return f"build/tests/{CHAIN_TESTS[k]}.state"


def chain_handoff(fc: FullChain, end_room: str) -> list[str]:
    """The checks at the hand-off between two parts of the full chain, the same at the end of one (before `save`) and at the
    start of the next (after `load`): what the chain has done so far (FullChain: the item bits, ammo, capacities, the HUD) and
    where she is (the room, the game running)."""
    return ([fc.word(8 * (a - 0x7ED870)) for a in (0x7ED884, 0x7ED886, 0x7ED888, 0x7ED88A, 0x7ED88C, 0x7ED88E)]   # specs/19m
            + [f"expect {MISSILES} {fc.missiles:04X}", f"expect {MAX_MISSILES} {fc.max_missiles:04X}",
               f"expect {SUPERS} {fc.supers:04X}", f"expect {MAX_SUPERS} {fc.max_supers:04X}",   # specs/18n
               f"expect {POWER_BOMBS} {fc.pbs:04X}", f"expect {MAX_POWER_BOMBS} {fc.max_pbs:04X}",
               f"expect {MAX_ENERGY} {fc.max_energy:04X}", f"expect {HUD_ITEM} {fc.hud:04X}",
               f"expect {ROOM_PTR} {fc.room[end_room]}", f"expect {GAME_STATE} 0008"])


AREA5_SAVED = 0x7ECD52 + 0x500             # area 5's saved explored map (SAVED_MAPS + 0x100 * 5)
MINES_LIST = MINES.map_save_bytes()        # specs/19e: area 5's list (the Mines'), in $81


def tests(m: dict) -> dict[str, list[str]]:
    room = {k: f"{v['header'] & 0xFFFF:04X}" for k, v in m.items() if k != "banks"}
    ridley = f"{m['airlock']['meta_ridley'] & 0xFFFF:04X}"
    airlock_states = m["airlock"]["states"]
    vram = vram_refs()
    return {
        "novo_jogo_comeca_no_hangar": NEW_GAME + [
            f"expect {GAME_STATE} 0008", f"expect {AREA} 0003", f"expect {ROOM_PTR} {room['hangar']}",
            f"expect {HEALTH} 0063",
        ],
        # specs/16 (was specs/11's atracao_e_novo_jogo): the attract demos are off. Idle at the title well past the vanilla
        # demo start (~2900 frames; then 3 more demo cycles): still the title (state 1, waiting in $8B:9F29), no room
        # loaded, the item bits untouched (a demo fills them with $FF); the VRAM holds the new logo (METROID PRIME); from
        # the file select, B goes back to the title, which plays again and stays; a new game after all that starts clean
        # specs/16: the title's logo says METROID PRIME: its tiles in VRAM and the spritemap's pieces in the OAM buffer. Its
        # graphic loads in as many frames as vanilla's (title.pack): at frame 600 (when NEW_GAME presses START) the frame
        # counter and the random number are the ones of the ROM before specs/16 (the fights of chozo_hive_mecha,
        # chozo_incinerator_drone and chozo_save_station_3 depend on them)
        "titulo_metroid_prime": ["wait 600", f"expect {FRAME_COUNTER} 0100", f"expect {RANDOM} 8E82",
                                 "wait 1800", f"expect {GAME_STATE} 0001", f"expect {TITLE_FUNCTION} 9F29",
                                 title_logo_in_vram()] + title_logo_in_oam() + ["shot build/tests/16_titulo.png"],
        "titulo_sem_demo_e_novo_jogo": ["wait 3600", f"expect {GAME_STATE} 0001", f"expect {TITLE_FUNCTION} 9F29",
                                        f"expect {ROOM_PTR} 0000", "expect 7ED884 0000",
                                        "shot build/tests/16_titulo_parado.png", "wait 6000", f"expect {GAME_STATE} 0001",
                                        f"expect {TITLE_FUNCTION} 9F29", f"expect {ROOM_PTR} 0000",
                                        "hold START 2", "wait 120", f"expect {GAME_STATE} 0004", "hold B 2", "wait 3300",
                                        f"expect {GAME_STATE} 0001", f"expect {TITLE_FUNCTION} 9F29", title_logo_in_vram(),
                                        "shot build/tests/16_titulo_de_volta.png"]
        + NEW_GAME[1:] + [
            f"expect {GAME_STATE} 0008", f"expect {AREA} 0003", f"expect {ROOM_PTR} {room['hangar']}",
            "expect 7ED884 0000", "expect 7ED886 0000", "expect 7ED8C6 0000", f"expect {BOSS_BITS_AREA3} 0000",
        ],
        "ida_hangar_ate_evacuacao": NEW_GAME + walk("RIGHT", 220) + [
            f"expect {ROOM_PTR} {room['evac_area']}", f"expect {GAME_STATE} 0008",
            "shot build/tests/ida_fim.png",
        ],
        "rota_completa_ida_e_fuga": NEW_GAME + traverse(route("hangar", "reactor_core", False), room)
        + [f"expect {ROOM_PTR} {room['reactor_core']}"]
        # boss dead: leave and re-enter the core so its grey door spawns already open
        + poke16(0x7ED82B, 0x0001)[:1]
        + traverse(walk_rooms(["reactor_core", "reactor_entrance", "reactor_core"]), room)
        + traverse(walk_rooms(ESCAPE), room)
        + [f"expect {GAME_STATE} 0008", "shot build/tests/fuga_fim.png"],
        "porta_cinza_bloqueia_antes_do_chefe": NEW_GAME + traverse(walk_rooms(["hangar", "airlock"]), room)
        + go_through({r.key: r for r in ROOMS}["airlock"],
                     next(i for i, d in enumerate({r.key: r for r in ROOMS}["airlock"].doors) if d.locked))
        + [f"expect {ROOM_PTR} {room['airlock']}"],
        "inimigos_nascem_nas_salas": NEW_GAME + traverse(route("hangar", "access_hall", False), room)
        + [f"expect {ENEMY0_SPECIES} DC3F"]
        + traverse(walk_rooms(["access_hall", "evac_area", "umbilical_hall", "map_facility", "elevator_beta",
                               "conduit_hall", "biotech_1"]), room)
        + [f"expect {ENEMY0_SPECIES} F653"]
        + traverse(route("biotech_1", "reactor_core", False), room)
        + [f"expect {ENEMY0_SPECIES} {PHANTOON}", f"expect {TIMER_STATUS} 0000"],
        "parasite_queen_morre_e_fuga_com_timer": NEW_GAME + traverse(route("hangar", "reactor_core", False), room)
        + kill_parasite_queen()
        + [f"expect {BOSS_BITS_AREA3} 0001", f"expect {TIMER_STATUS} {TIMER_COUNTING}"]
        + traverse(walk_rooms(ESCAPE), room)
        + [f"expect {GAME_STATE} 0008", f"expect {TIMER_STATUS} 0000", f"peek {TIMER_TIME} 3",
           "shot build/tests/fuga_cronometrada_fim.png"],
        # spec 06: her own shape. After the entrance the body block has written its tilemap words
        # into WRAM $7E:2000 (head, leg, abdomen cells), the ones tools/frigate/queen_art.py encoded
        "parasite_queen_forma_nova": NEW_GAME + traverse(route("hangar", "reactor_core", False), room)
        + ["wait 600", f"expect {ENEMY0_SPECIES} {PHANTOON}"]
        + [f"expect {a} {w:04X}" for a, w in m["reactor_core"]["parasite_queen"]["tilemap_samples"].items()]
        + ["wait 240", "shot build/tests/parasite_queen.png"],   # she has faded in by now
        "timer_zerado_e_game_over": NEW_GAME + traverse(route("hangar", "reactor_core", False), room)
        + ["poke 7ED82B 01", "wait 240", f"expect {TIMER_STATUS} {TIMER_COUNTING}",
           "poke 7E0945 00", "poke 7E0946 02", "poke 7E0947 00", "wait 400",
           f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}", "shot build/tests/game_over.png",
           # "YES" must bring Samus back to the frigate, not to vanilla Crateria
           # YES, then keep tapping A until the area map screen takes it (its timing varies)
           ] + GAME_OVER_CONTINUE + [
           f"expect {GAME_STATE} 0008", f"expect {AREA} 0003", f"expect {ROOM_PTR} {room['hangar']}",
           f"expect {TIMER_STATUS} 0000"],
        # save at the Reactor Core Entrance, die, and "continue" must bring Samus back there
        "save_station_grava_e_continue_volta_nela": NEW_GAME + traverse(route("hangar", SAVE_ROOM, False), room)
        + step_on_save_station()
        + [f"expect {LOAD_STATION} 0001", f"expect {USED_STATIONS_AREA3} 02", f"expect {GAME_STATE} 0008",
           "shot build/tests/save_station.png",
           "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}"]
        + GAME_OVER_CONTINUE
        + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0003", f"expect {ROOM_PTR} {room[SAVE_ROOM]}",
           f"expect {LOAD_STATION} 0001", "shot build/tests/continue_na_save_station.png",
           # the explored map survives the save (SRAM keeps only listed bytes per area)
           explored_bit("hangar"), explored_bit("access_hall"), explored_bit("cargo_lift"), explored_bit(SAVE_ROOM)],
        # the area-select screen before the room map (continue after game over, or loading the save
        # from the title screen) says "TALLON IV" and "FRIGATE / ORPHEON", not "PLANET ZEBES / WRECKED SHIP"
        "continue_mostra_a_fragata": NEW_GAME + traverse(route("hangar", SAVE_ROOM, False), room)
        + step_on_save_station()
        + [f"expect {LOAD_STATION} 0001", "poke 7E09C2 00", "poke 7E09C3 00", "wait 400",
           f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}", "hold A 2", "wait 300"]
        + area_select_shows_frigate("build/tests/continue_tela_de_area.png")
        + GAME_OVER_CONTINUE[2:]
        + [f"expect {ROOM_PTR} {room[SAVE_ROOM]}", f"expect {GAME_STATE} 0008"],
        # NO at the game over goes to the title; START, then A on slot A, "start" and the map
        "carregar_save_mostra_a_fragata": NEW_GAME + traverse(route("hangar", SAVE_ROOM, False), room)
        + step_on_save_station()
        + [f"expect {LOAD_STATION} 0001", "poke 7E09C2 00", "poke 7E09C3 00", "wait 400",
           f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}", "hold DOWN 2", "wait 30", "hold A 2", "wait 600",
           "hold START 2", "wait 200"] + ["hold A 2", "wait 120"] * 3 + ["wait 200"]
        + area_select_shows_frigate("build/tests/carregar_tela_de_area.png"),
        # the frigate's map gets its own save block: Tourian (area 5) keeps all its 21 bytes.
        # $26 and $5A are the 1st and 21st bytes of its list, in the saved copy at $7ECD52+0x500.
        # specs/19e: area 5 is the Mines' now, its list its own (the whole table's 39 bytes, in $81: specs/19b): its 1st and
        # last bytes (MINES.map_save_bytes) in the saved copy
        "mapa_da_tourian_sobrevive_ao_save": NEW_GAME + traverse(route("hangar", SAVE_ROOM, False), room)
        + [f"poke {AREA5_SAVED + MINES_LIST[0]:06X} FF", f"poke {AREA5_SAVED + MINES_LIST[-1]:06X} FF"]
        + step_on_save_station()
        + [f"expect {LOAD_STATION} 0001", "poke 7E09C2 00", "poke 7E09C3 00", "wait 400",
           f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}"]
        + GAME_OVER_CONTINUE
        + [f"expect {GAME_STATE} 0008", f"expect {ROOM_PTR} {room[SAVE_ROOM]}",
           f"expect {AREA5_SAVED + MINES_LIST[0]:06X} 00FF", f"expect {AREA5_SAVED + MINES_LIST[-1]:06X} 00FF"],
        # like Prime ("Save Disabled"): once the Parasite Queen is dead the station does nothing,
        # or a save mid-escape would let a continue skip the timer
        "save_desligado_depois_do_chefe": NEW_GAME + traverse(route("hangar", "cargo_lift", False), room)
        + ["poke 7ED82B 01"] + traverse(walk_rooms(["cargo_lift", SAVE_ROOM]), room)
        + step_on_save_station()
        + [f"expect {LOAD_STATION} 0000", f"expect {USED_STATIONS_AREA3} 00", f"expect {GAME_STATE} 0008"],
        # map station: reveals the whole frigate; the pause map opens and closes without trouble,
        # and the explored bits land on the tiles pausemap.py drew for each room
        "map_station_e_mapa_de_pausa": NEW_GAME + traverse(route("hangar", MAP_ROOM, False), room)
        + [explored_bit("hangar"), explored_bit("access_hall"), explored_bit(MAP_ROOM),
           f"expect {MAP_STATION_AREA3} 00"]
        + use_map_station()
        + [f"expect {MAP_STATION_AREA3} FF", f"expect {GAME_STATE} {GAME_STATE_PAUSED}",
           "shot build/tests/mapa_de_pausa.png",
           # the pause menu ignores a 2-frame tap of START; 10 frames (a real press) works
           "hold START 10", "wait 200", f"expect {GAME_STATE} 0008", f"expect {ROOM_PTR} {room[MAP_ROOM]}",
           "hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}",   # pausing by hand works too
           "hold START 10", "wait 200", f"expect {GAME_STATE} 0008"],
        # end of the frigate: on the way out Meta Ridley shows up in the Air Lock, roars and flies
        # off through the ceiling (for good); in the hangar Samus boards her ship, it lifts off,
        # the Ceres escape plays (the frigate explodes, "TALLON IV") and she lands at the Landing Site
        "fuga_ridley_nave_e_final": NEW_GAME + traverse(route("hangar", "reactor_core", False), room)
        + kill_parasite_queen()
        + traverse(walk_rooms(ESCAPE[:-1]), room)
        + [f"expect {ROOM_PTR} {room['airlock']}", f"expect {ENEMY0_SPECIES} {ridley}", f"expect {TIMER_Y} {TIMER_HIDDEN}",
           "wait 20", f"expect {MINIMAP_OFF} 0000", "shot build/tests/minimapa_air_lock.png"]
        # leaving before he flies off: the timer comes back (digits copied again), and he is
        # still there when Samus returns
        + traverse(walk_rooms(["airlock", "access_hall"]), room)
        + [f"expect {TIMER_Y} {TIMER_IN_PLACE}", "shot build/tests/timer_fora_da_air_lock.png",
           forget_explored("airlock")]   # the minimap must mark the Air Lock again during the scene
        + traverse(walk_rooms(["access_hall", "airlock"]), room)
        + [f"expect {ENEMY0_SPECIES} {ridley}", "wait 90", explored_bit("airlock"), f"expect {MINIMAP_OFF} 0000", "shot build/tests/meta_ridley.png", "wait 600",
           f"expect {BOSS_BITS_AREA3} {BOSS_AND_RIDLEY_GONE}", f"expectbit {ENEMY0_PROPS_HI} 02",
           f"expect {TIMER_Y} {TIMER_IN_PLACE}", "shot build/tests/timer_depois_do_ridley.png"]
        + traverse(walk_rooms(["airlock", "access_hall", "airlock"]), room)
        + [f"expect {ROOM_STATE} {airlock_states[1] & 0xFFFF:04X}"]   # the state without him
        + traverse(walk_rooms(["airlock", "hangar"]), room)
        + [f"expect {TIMER_STATUS} 0000", f"expect {ENEMY0_SPECIES} {ending.GUNSHIP_TOP:04X}"]
        + [f"expect {EQUIPMENT} {START_ITEMS:04X}"]
        + board_ship() + ["wait 500", "shot build/tests/nave_decolando.png", "wait 100",
                          f"expect {GAME_STATE} {GAME_STATE_ESCAPE_CUTSCENE}",
                          f"expect {LOADING_GAME_STATE} 0022",
                          "wait 980", "shot build/tests/fuga_tallon_iv.png", "wait 2520"]
        + lands_on_landing_site(room[LANDING_SITE]) + ["shot build/tests/fuga_pouso_landing_site.png"],
        # the landing saved the game: a continue after game over brings Samus back to the Landing Site
        "final_continue_na_landing_site": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE])
        + ["poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}"]
        + GAME_OVER_CONTINUE
        + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0000", f"expect {ROOM_PTR} {room[LANDING_SITE]}",
           "shot build/tests/final_continue_landing_site.png"],
        # the black-out before the cutscene saves (area 3, loading state $22, as vanilla Ceres):
        # turning the console off mid-cutscene and loading the save plays the cutscene again and
        # lands at the Landing Site
        "final_reset_no_meio_da_cena": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 1000",
            f"expect {GAME_STATE} {GAME_STATE_ESCAPE_CUTSCENE}"]
        + load_slot_a_after_reset()
        + [f"expect {GAME_STATE} {GAME_STATE_ESCAPE_CUTSCENE}", f"expect {AREA} 0003",
           f"expect {EQUIPMENT} 0000",   # spec 07e: the mid-cutscene save is already without items
           "shot build/tests/final_reset_cena.png", "wait 4000"]
        + lands_on_landing_site(room[LANDING_SITE]),
        # before the boss the ship is scenery: boarding it would save as Crateria's ship does
        "nave_fechada_antes_do_chefe": NEW_GAME + board_ship() + ["wait 400",
            f"expect {ENEMY0_AI} {GUNSHIP_WAITING}", f"expect {GAME_STATE} 0008", "shot build/tests/nave_no_hangar.png"],
        # Prime's hangar is open to space: the starfield (star tiles + BG2 map) is in VRAM at the
        # start and is loaded again after the pause menu, the X-ray and a trip to the Air Lock;
        # the Air Lock keeps the Wrecked Ship background
        "hangar_ceu_estrelado": NEW_GAME + hangar_has_stars(vram) + ["shot build/tests/hangar_ceu.png"]
        # the pause redraws the screen after the camera jump; Samus is in front of the back wall
        + walk_under_ship()
        + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}",
           "hold START 10", "wait 200", f"expect {GAME_STATE} 0008"] + hangar_has_stars(vram)
        + ["shot build/tests/hangar_sob_a_nave.png"]
        + ["hold LEFT 4", "wait 20"] + ["hold SELECT 2", "wait 10"] * 3
        + [f"expect {XRAY_SELECTED} 0005", "hold B 60", f"expect {TIME_FROZEN} 0001", "wait 60",
           f"expect {TIME_FROZEN} 0000"] + hangar_has_stars(vram) + ["shot build/tests/hangar_depois_do_xray.png"]
        + traverse(walk_rooms(["hangar", "airlock"]), room)
        + [f"expectvram {space.BG2_TILEMAP_VRAM:04X} {vram['ws_map']}", "shot build/tests/air_lock_fundo.png"]
        + traverse(walk_rooms(["airlock", "hangar"]), room) + hangar_has_stars(vram),
        # spec 07g: the end of the frigate lands at the Tallon's Landing Site (the new room, next to
        # the ship); with the Power Beam only Samus walks the 5 MVP rooms door to door and back; the
        # pause screen works in area 0 (its own map since spec 07f: tallon_mapa_salvo)
        "tallon_rota_mvp": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + ["shot build/tests/tallon_chegada.png"]
        + tallon_walk("LEFT", "ida") + [f"expect {ROOM_PTR} {room[TALLON_PATH[-1]]}"]
        + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}", "shot build/tests/tallon_pausa.png",
           "hold START 10", "wait 200", f"expect {GAME_STATE} 0008"]
        + tallon_walk("RIGHT", "volta")
        + [f"expect {ROOM_PTR} {room[TALLON_PATH[0]]}", f"expect {GAME_STATE} 0008"]
        # specs/09d: the Morph Ball, picked up on the Chozo West pad (was: nothing at all); specs/12e: beside it
        + [f"expect {a:06X} {v:04X}" for a, v in MORPH_ONLY_RAM.items()] + [item_taken(item_index("tallon_transport_chozo_west"))],
        "tallon_rota_bc": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + tallon_route_bc()
        + [f"expect {ROOM_PTR} {room[LANDING_SITE]}", f"expect {GAME_STATE} 0008"]
        # specs/09d: the Morph Ball, picked up on the Chozo West pad (was: nothing at all)
        + [f"expect {a:06X} {v:04X}" for a, v in MORPH_ONLY_RAM.items()] + [item_taken(item_index("tallon_transport_chozo_west"))]
        # spec 07h: on the way west (bc_oeste) she walks through the Landing Site pond and picks up
        # its Missile Expansion; the beam stays selected, so the red doors above stayed shut
        + [f"expect 7E09C8 0005", item_taken(0)],
        # spec 07h: the first Missile Expansion (Landing Site pond) opens a red door
        "tallon_missil_abre_porta_vermelha": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE])
        + [l.replace("WATERFALL", room["tallon_waterfall_cavern"]).replace("CRASH", room["tallon_crash_site"])
           for l in tallon_missile_red_door()],
        # spec 07h: the item bit is saved: after saving on the ship and continuing, the missiles
        # (5/5) and the bit are back and the pond is empty (walking through it again gives nothing)
        "tallon_missil_salvo": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + tallon_first_missile()
        # the position poke keeps the walk's run (movement type 1, speed to the left: she slides off
        # the centre) and the ship only takes a standing Samus within 8 px of it ($A2:A9BD): tap UP
        # to stand, let her stop, and put her on the centre again
        + stand_on_tallon_ship() + ["hold UP 2", "wait 60"] + stand_on_tallon_ship()
        + save_on_tallon_ship("build/tests/tallon_missil_save.png")
        + ["poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}"]
        + GAME_OVER_CONTINUE
        + [f"expect {GAME_STATE} 0008", f"expect {ROOM_PTR} {room[LANDING_SITE]}", item_taken(0),
           f"expect {MAX_MISSILES} 0005", f"expect {MISSILES} 0005",
           "hold LEFT 70", "wait 60"] + tallon_walk("LEFT", "missil_de_novo", 1)
        + tallon_walk("LEFT", "missil_de_novo_lago", MISSILE_WALK, jump=False)
        + ["wait 60", f"expect {MAX_MISSILES} 0005", f"expect {GAME_STATE} 0008",
           "shot build/tests/tallon_lago_vazio.png"],
        # spec 07i: the enemies of the rooms on the arrival path are there, alive, with full health,
        # in the order of tools/tallon/enemies.py, and every species is seen on screen
        "tallon_inimigos_vivos": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE])
        + [f"expect {ENEMY_TABLE:06X} {ending.GUNSHIP_TOP:04X}"]   # the Landing Site: only the ship
        + tallon_traverse(["tallon_landing_site", "tallon_canyon_cavern"], room)
        + tallon_enemies_alive("tallon_canyon_cavern")
        + tallon_look(6, 10, 128, 0, "build/tests/tallon_inimigos_canyon_cavern.png")
        + tallon_traverse(["tallon_canyon_cavern", "tallon_canyon"], room)
        + tallon_enemies_alive("tallon_canyon")
        + tallon_look(27, 30, 256, 400, "build/tests/tallon_inimigos_canyon_fundo.png")
        + tallon_look(40, 18, 512, 160, "build/tests/tallon_inimigos_canyon_terracos.png")
        + tallon_traverse(["tallon_canyon", "tallon_tunnel_a"], room)
        + tallon_enemies_alive("tallon_tunnel_a")
        + tallon_look(5, 10, 64, 0, "build/tests/tallon_inimigos_tunnel_a.png")
        + tallon_traverse(["tallon_tunnel_a", "tallon_canyon", "tallon_root_tunnel"], room)
        + tallon_enemies_alive("tallon_root_tunnel")
        + tallon_look(14, 10, 192, 0, "build/tests/tallon_inimigos_root_tunnel.png"),
        # spec 07i: behind the Root Tunnel's red door (opened with the Landing Site missile): the
        # Root Cave (Cacatac, Geemers and Zeelas in one enemy set, palette slots 7, 1, 2) and the
        # Transport Tunnel B
        "tallon_inimigos_atras_da_porta_vermelha": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE])
        + tallon_first_missile()
        + tallon_traverse(["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_root_tunnel"], room)
        + go_through(TALLON.by_key()["tallon_root_tunnel"],
                     next(i for i, d in enumerate(TALLON.by_key()["tallon_root_tunnel"].doors) if d.lock == "missile"),
                     ["hold LEFT 8", "wait 10", "hold SELECT 2", "wait 10"] + ["hold LEFT+X 2", "wait 30"] * 6
                     + ["wait 60", red_door_open("tallon_root_tunnel", "tallon_root_cave"), "hold LEFT 90"])
        + [f"expect {ROOM_PTR} {room['tallon_root_cave']}"]
        + tallon_enemies_alive("tallon_root_cave")
        + tallon_look(14, 58, 128, 64 * 16 - 224, "build/tests/tallon_inimigos_root_cave.png")
        + tallon_traverse(["tallon_root_cave", "tallon_tunnel_b"], room)
        + tallon_enemies_alive("tallon_tunnel_b")
        + tallon_look(30, 10, 30 * 16 - 128, 0, "build/tests/tallon_inimigos_tunnel_b.png"),
        # spec 07i: the Power Beam kills a Tallon enemy: the Blood Flower (Cacatac, 60 HP) of the
        # Root Tunnel, shot crouching (it is 16 px tall: a standing shot passes over it) from 5
        # blocks away; each shot takes 20, the third kills it (its species word is cleared)
        "tallon_power_beam_mata_inimigo": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE])
        + tallon_traverse(["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_root_tunnel"], room)
        + tallon_enemies_alive("tallon_root_tunnel")
        + tallon_look(25, 10, 25 * 16 - 128, 0, "build/tests/tallon_power_beam_antes.png")
        + ["hold LEFT 2", "wait 20", "hold DOWN 4", "wait 20", "poke 7E09C2 63", "hold DOWN+X 2", "hold DOWN 20",
           f"expect {ENEMY_TABLE:06X} {SPECIES['blood_flower'].ptr:04X}", f"expect {ENEMY_TABLE + ENEMY_HEALTH:06X} 0028"]
        + ["poke 7E09C2 63", "hold DOWN+X 2", "hold DOWN 20"] * 5
        + ["wait 60", f"expect {ENEMY_TABLE:06X} 0000", f"expect {GAME_STATE} 0008",
           f"expect {POWER_BEAM_ONLY_RAM[0]:06X} 0000", "shot build/tests/tallon_power_beam_depois.png"],
        # spec 07e: Samus has the frigate's equipment until the lift-off and reaches the Tallon with
        # the Power Beam only (the lift-off clears it before the black-out saves)
        "tallon_chegada": NEW_GAME + ["poke 7ED82B 01", f"expect {EQUIPMENT} {START_ITEMS:04X}",
                                      f"expect 7E09C8 {START_MISSILES:04X}"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + ["wait 60", "shot build/tests/tallon_chegada_hud.png"],
        # spec 07e: the Tallon's ship is vanilla (the $A2 patches only touch area 3): crouching on it
        # refills and saves to load station 0 of area 0; a continue comes back to the Landing Site
        "tallon_nave_salva": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + save_on_tallon_ship()
        + ["poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}"]
        + GAME_OVER_CONTINUE
        + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0000", f"expect {ROOM_PTR} {room[LANDING_SITE]}",
           f"expect {LOAD_STATION} 0000", f"expect {GAME_HOURS} 0005"] + has_arrival_loadout()
        + ["shot build/tests/tallon_nave_continue.png"],
        # spec 07f: the Tallon's own pause map and save list. Explore the 5 MVP rooms (walk there and
        # back), save on the ship, die and continue: the explored screens come back from SRAM and
        # the pause map shows them with the Tallon's tiles
        "tallon_mapa_salvo": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE])
        + tallon_walk("LEFT", "mapa_ida", MAP_WALK_WEST) + [f"expect {ROOM_PTR} {room[TALLON_PATH[-1]]}"]
        + tallon_walk("RIGHT", "mapa_volta") + [f"expect {ROOM_PTR} {room[TALLON_PATH[0]]}"]
        + tallon_explored(tallon_door_screens())
        # specs/09d: the longer walk back ends with her running: stop her before boarding (as tallon_missil_salvo)
        + stand_on_tallon_ship() + ["hold UP 2", "wait 60"] + stand_on_tallon_ship()
        + save_on_tallon_ship("build/tests/tallon_mapa_save.png")
        + ["poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}"]
        + GAME_OVER_CONTINUE
        + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0000", f"expect {ROOM_PTR} {room[LANDING_SITE]}"]
        # specs/09d: the Morph Ball picked up on the way is saved too
        + [f"expect {COLLECTED_ITEMS} {MORPH_BALL_EQUIPMENT:04X}", item_taken(item_index("tallon_transport_chozo_west"))]
        + tallon_explored(tallon_door_screens()) + ["shot build/tests/tallon_minimapa.png"]
        + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"]
        + tallon_pause_shows(tallon_door_screens()) + ["shot build/tests/tallon_mapa_salvo.png",
           "hold START 10", "wait 200", f"expect {GAME_STATE} 0008"],
        # spec 07f: a save on the Tallon's ship shows "TALLON / OVERWORLD" on the area-select
        # screen (not "CRATERIA"), then the Tallon's room map, and continues at the Landing Site
        "continue_mostra_o_tallon": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + save_on_tallon_ship("build/tests/tallon_continue_save.png")
        + ["poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
           "hold A 2", "wait 300"]
        + area_select_shows(TALLON.number, 0, "build/tests/continue_tela_do_tallon.png")
        + ["hold A 2", "wait 200", "peekw 7E0727", "shot build/tests/continue_mapa_do_tallon.png"]
        + GAME_OVER_CONTINUE[2:]
        + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0000", f"expect {ROOM_PTR} {room[LANDING_SITE]}"],
        # spec 07l: the sunken frigate's save station = load station 1 of area 0. Load there; a station
        # just loaded doesn't save until Samus leaves the room (vanilla: save_station_lockout_flag,
        # cleared by a room transition, $82:E1B7), so walk down to the Reactor Access and back up
        # (tallon_rota_d), step on the pedestal, save (YES, close "save completed"), die and continue:
        # the area-select screen puts the save on the Tallon, station 1, and Samus is back on it
        "tallon_save_fragata": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + load_tallon_station(SAVESTATION.index)
        + [f"expect {ROOM_PTR} {room[SAVESTATION.room]}", f"expect {AREA} 0000", f"expect {WATER_FX_TYPE} 0006"]
        + with_gravity_suit() + tallon_route_d() + [f"expect {ROOM_PTR} {room[SAVESTATION.room]}"]
        + poke16(0x7E09E0, 7)
        + poke16(0x7E0AF6, SAVESTATION.x) + poke16(0x7E0B10, SAVESTATION.x) + poke16(0x7E0AFA, SAVESTATION.y)
        + poke16(0x7E0B14, SAVESTATION.y) + ["wait 180", "shot build/tests/tallon_save_fragata.png", "hold A 2",
                                             "wait 300", "hold A 2", "wait 200"]
        + [f"expect {LOAD_STATION} 0001", f"expectbit {USED_STATIONS_AREA0} 02", f"expect {GAME_STATE} 0008",
           "hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}",
           "shot build/tests/tallon_save_fragata_pausa.png", "hold START 10", "wait 200",
           "poke 7E09C2 00", "poke 7E09C3 00", "wait 400", f"expect {GAME_STATE} {GAME_STATE_GAME_OVER}",
           "hold A 2", "wait 300"]
        + area_select_shows(TALLON.number, SAVESTATION.index, "build/tests/tallon_save_fragata_area.png")
        + GAME_OVER_CONTINUE[2:]
        + [f"expect {GAME_STATE} 0008", f"expect {AREA} 0000", f"expect {ROOM_PTR} {room[SAVESTATION.room]}",
           f"expect {LOAD_STATION} 0001", f"expect {GAME_HOURS} 0007", f"expect 7E0AF6 {SAVESTATION.x:04X}",
           f"expect {WATER_FX_TYPE} 0006", "shot build/tests/tallon_save_fragata_continue.png"],
        # spec 07l: the underwater jump the validator assumes (reach.WATER_*), with and without the suit
        "pulo_na_agua_medido": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + load_tallon_station(SAVESTATION.index)
        + [f"expect {ROOM_PTR} {room[SAVESTATION.room]}", f"expect {WATER_FX_TYPE} 0006", f"expect {WATER_SURFACE} 0010"]
        + measure_water_jumps(),
        # spec 07l: walking from the save station: down into the Reactor Access, its two power-conduit
        # doors stay shut, back up into the Savestation (with the Gravity Suit, as the region assumes)
        "tallon_rota_d": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + load_tallon_station(SAVESTATION.index)
        + with_gravity_suit() + tallon_route_d()
        + [f"expect {ROOM_PTR} {room[SAVESTATION.room]}", f"expect {GAME_STATE} 0008"],
        # spec 07l: every room of region D, through the doors with door_teleport (the power-conduit
        # doors don't open yet): the room loads, the water (FX type 6) is there except in the Deck Beta
        # Transit Hall, the enemies are alive, and the Cargo Lift's Energy Tank is picked up
        "tallon_fragata_afundada": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + load_tallon_station(SAVESTATION.index) + with_gravity_suit()
        + tallon_sunken_tour(m, room),
        # spec 07m: region E through its doors (door_teleport: behind the sunken frigate and ice doors):
        # every room loads, dry, its Seedlings and Blood Flowers alive; the Great Tree Chamber's Missile
        # Expansion and the Life Grove's X-Ray Visor are picked up
        "tallon_grande_arvore": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + load_tallon_station(SAVESTATION.index) + with_gravity_suit()
        + tallon_great_tree_tour(m, room),
        # spec 09e: the Power Bomb picked up in the Mines East, laid in the ball by the Life Grove's hut: its 15
        # power bomb blocks broken for good, the X-Ray picked up
        "tallon_power_bomb": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + load_tallon_station(SAVESTATION.index) + with_gravity_suit()
        + tallon_power_bomb(m, room),
        # specs/13: a power bomb sweeps an item's block (a dead PLM slot with its block index), a slot above frees: the
        # item is still picked up (the touch's lookup, $84:EEAB, skips dead slots)
        "power_bomb_nao_apaga_item": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + bombed_item_touch(m, room),
        # spec 09f: from the landing, the 20 items in the order of the rounds, each round's lock opened for real
        # (tallon_full_chain: the shortcuts are noted there); at the end the 20 bits, saved, continued
        "tallon_cadeia_completa": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + tallon_full_chain(m, room),
        # specs/12m: from the landing, the 51 items of the Tallon and the Chozo in the order of the declared rounds, through
        # the three real elevators, each lock opened for real, the zigzag climbs climbed (full_chain: the shortcuts left are
        # listed there); at the end the 51 bits, 51%, saved, continued, both areas' pause maps
        # specs/17j: and the Magmoor's 7 (58, 58%), in three parts handed on by savestates (CHAIN_PARTS)
        **dict(zip(CHAIN_TESTS, [NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
                                 + lands_on_landing_site(room[LANDING_SITE]) + part if k == 0 else part
                                 for k, part in enumerate(full_chain(m, room))])),
        # specs/17e: the Chozo's elevator down to the Magmoor (area 2) and back, its map, save and continue (its name), and the
        # Tallon's down to the Magmoor's P16 and back
        "elevador_magmoor_ida_e_volta": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + magmoor_round_trip(m, room),
        "elevador_magmoor_tallon": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + magmoor_tallon_elevator(m, room),
        # specs/18e: the Magmoor's lifts up to Phendrana (area 4) and back, its map, save and continue (its name)
        "elevador_phendrana_norte": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_north_elevator(m, room),
        "elevador_phendrana_sul": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_south_elevator(m, room),
        # specs/19e: the Tallon's and the Magmoor's lifts down to the Mines (area 5) and back, its map, save and continue (the
        # five names)
        "elevador_mines_leste": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_east_elevator(m, room),
        "elevador_mines_oeste": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_west_elevator(m, room),
        # specs/19f: the Mines' region A walked from the Tallon's elevator (its 2 missiles of round 5 and the Grapple Beam, the
        # round-5 gear), its round-6 locks (the power bomb blocks, the plasma door; the niche's missile), Save Station A
        "mines_regiao_a_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_route_a(m, room),
        "mines_regiao_a_rodada_6": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_round6_a(m, room),
        "mines_save_station_a": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_save_a(m, room),
        # specs/19h: the Phazon Elite's arena fought with the gear of round 5: the ceiling door, the dead state on re-entry and
        # after a save and a continue
        "mines_phazon_elite": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_phazon_elite(m, room),
        # specs/19k: the Omega Pirate's arena fought with the gear of round 6 (missiles only): both doors, the dead state
        "mines_omega_pirate": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_omega_pirate(m, room),
        # specs/20e: the Impact Crater's way in: the Artifact Temple's teleporter off, then on once the Omega Pirate is dead; the
        # Entry Point, the Tunnel A and back up; the crater's Save Station
        "impact_entrada_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + crater_entrance_route(m, room),
        "impact_save_station": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + crater_save(m, room),
        # specs/20h: Metroid Prime's fight won for real (the beams), the door open, the way up and back to the temple, the dead
        # state; the door shut before the win, Samus' death in the fight and the continue at the last save station
        "impact_metroid_prime": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + impact_metroid_prime(m, room),
        "impact_prime_porta_e_morte": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + impact_prime_death(m, room),
        # specs/20i: the game's end: after the win, up through the ceiling door into the SM's ending, the credits and the rate
        # screen with the percentage of the chain's gear; without the win the exit's spot does nothing
        "impact_fim_do_jogo": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + impact_end(m, room),
        "impact_fim_sem_vitoria": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + impact_end_not_won(m, room),
        # specs/20f: the crater's region B walked both ways (the Phazon Core's climbs, the Tunnel B, the Missile Station's
        # refill); the Phazon Core's Metroids alive, no damage at its doors
        "impact_regiao_b_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + crater_route_b(m, room),
        "impact_inimigos_vivos": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + crater_enemies_test(m, room),
        # specs/20g: the descent (the Infusion Chamber's hole, the Subchamber One and back up to the Tunnel B), energy 99 all the way;
        # the phazon that hurts (SM's acid) in the Subchamber One's pool, nothing out of it
        "impact_descida_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + crater_route_c(m, room),
        "impact_phazon_dano": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + crater_phazon_test(m, room),
        # specs/19i: the Mines' region B walked from the Elevator A (its 2 missiles of round 5, the round-5 gear), its round-6
        # locks (the power bomb walls of the Maintenance Tunnel and of the Metroid Quarantine A, the duct's; the Energy Tank and
        # the missile behind them), Save Station B, the Map Station
        "mines_regiao_b_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_route_b(m, room),
        "mines_regiao_b_rodada_6": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_round6_b(m, room),
        "mines_save_station_b": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_save_b(m, room),
        "mines_map_station": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_map(m, room),
        # specs/19j: the Mines' region C walked with the gear of round 6 (the Maintenance Tunnel's wall from the west, the
        # missile in the Phazon Processing Center's pit, the Energy Tank behind the plasma doors, the Elite Quarters)
        "mines_regiao_c_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_route_c(m, room),
        # specs/19l: the Mines' region D walked with the gear of round 6 (the vertical plasma doors, the Metroid Quarantine B's Space
        # Jump column, the Phazon Mining Tunnel's bomb and power bomb blocks, the three missiles, the Missile Station), Save Station C
        "mines_regiao_d_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_route_d(m, room),
        "mines_save_station_c": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_save_c(m, room),
        # specs/18f: Phendrana's region A walked from the north elevator (its 4 missiles, the round-3 gear), the way up to the
        # Chozo Ice Temple and the Chapel of the Elders (the bomb slot's tunnel, the chapel's wave door), Save Station B
        "phendrana_regiao_a_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_route_a(m, room),
        "phendrana_regiao_a_templo": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_temple(m, room),
        "phendrana_save_station_b": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_save_b(m, room),
        # specs/18h: the Sheegoth's arena fought with missiles (the gear of round 3): the missile on the altar, the door, the
        # dead state on re-entry and after a save and a continue
        "phendrana_sheegoth": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_sheegoth(m, room),
        # specs/18i: region B walked (its 3 items: the Energy Tank behind the bomb block, the Hydra's missile, the power bomb
        # expansion behind the plasma cap with the gear of round 6), its red doors, the vertical wave doors
        "phendrana_regiao_b_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_route_b(m, room),
        "phendrana_save_station_a": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_save_a(m, room),
        "phendrana_map_station": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_map(m, room),
        # specs/18j: region C of Phendrana
        # specs/18k: the Thardus' arena fought for real (the Bomb Torizo's copy), the doors, the dead state
        "phendrana_thardus": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_thardus(m, room),
        "phendrana_regiao_c_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_route_c(m, room),
        # specs/18l: region D of Phendrana walked (the Super Missile picked up and fired, the Metroids), Save Station D
        "phendrana_regiao_d_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_route_d(m, room),
        "phendrana_save_station_d": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_save_d(m, room),
        # specs/18m: region E of Phendrana walked (the dry part and the flooded Gravity Chamber), Save Station C
        "phendrana_regiao_e_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_route_e(m, room),
        "phendrana_regiao_e_agua": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_water(m, room),
        "phendrana_save_station_c": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_save_c(m, room),
        # specs/17f: the Magmoor's region A walked from the Chozo's elevator (both missiles, the round-3 gear), the heat and the
        # lava in its rooms, Save Station A (save, game over, continue in the Magmoor)
        "magmoor_regiao_a_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + magmoor_route_a(m, room),
        "magmoor_calor": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + magmoor_heat_test(m, room),
        "magmoor_save_station_a": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + magmoor_save_test(m, room),
        # specs/17h: region B of the Magmoor walked from the Monitor Tunnel to the Tallon's elevator; its power bomb wall
        "magmoor_regiao_b_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + magmoor_route_b(m, room),
        "magmoor_regiao_b_itens": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + magmoor_items_b(m, room),
        # specs/17i: region C of the Magmoor walked from the Tallon's elevator; its items (the ice doors); Save Station B
        "magmoor_regiao_c_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + magmoor_route_c(m, room),
        "magmoor_regiao_c_itens": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + magmoor_items_c(m, room),
        "magmoor_save_station_b": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + magmoor_save_b(m, room),
        # specs/17g: spec 15's door-entry audit in the Magmoor (every door entry of every room with enemies, a real one)
        "entradas_de_porta_magmoor": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + magmoor_down(m, room, "15") + entry_audit(m, room, MAGMOOR),
        # specs/19g: the region-A enemies of the Mines alive in their rooms; spec 15's door-entry audit in the Mines
        "mines_inimigos_vivos": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_enemies_test(m, room),
        "entradas_de_porta_mines": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + mines_down(m, room, "15") + entry_audit(m, room, MINES),
        # specs/18g: spec 15's door-entry audit in Phendrana (every door entry of every room with enemies, a real one)
        "entradas_de_porta_phendrana": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + phendrana_up(m, room, "15") + entry_audit(m, room, PHENDRANA),
        # specs/12e: the Chozo West's elevator down to the Chozo Ruins (area 1) and back up, the map of each area, save
        # and continue with both areas' explored maps kept
        "elevador_chozo_ida_e_volta": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + elevator_round_trip(m, room),
        # specs/12f: region A of the Chozo Ruins, walked from the North elevator to the Tower Chamber; its other items
        "chozo_regiao_a_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_route(m, room),
        "chozo_regiao_a_itens": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_items_test(m, room),
        # specs/12i: a save in the Chozo (Save Station 1) and the continue there; the Chozo's map station
        "chozo_save_e_continue": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_save_test(m, room),
        "chozo_map_station": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_map_station_test(m, room),
        # specs/12i: the region B items the route does not take, each picked up walking or rolling in
        "chozo_regiao_b_itens": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_items_b_test(m, room),
        # specs/12i: region B walked round its loop from the Nursery Access back to the Main Plaza
        "chozo_regiao_b_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_route_b(m, room),
        # specs/12j: region C walked from the Ruined Fountain Access to Save Station 2, the Sunchamber and down the Sun Tower
        "chozo_regiao_c_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_route_c(m, room),
        # specs/12j: region C's items, the Varia Suit and the Magma Pool's heat, Save Station 2
        "chozo_regiao_c_itens": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_items_c_test(m, room),
        "chozo_varia_e_calor": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_varia_heat_test(m, room),
        "chozo_save_station_2": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_save_2_test(m, room),
        # specs/12k: region D walked (the Charge Beam, the Dynamo, the Burn Dome, the Furnace) and its items
        "chozo_regiao_d_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_route_d(m, room),
        "chozo_regiao_d_itens": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_items_d_test(m, room),
        # specs/12l: region E walked (the Furnace's floor ice door, the statue, the flooded Reflecting Pool, up the South
        # elevator) and its items (the Crossway's way in, the East elevator's way in, the Antechamber's ice door)
        "chozo_regiao_e_rota": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_route_e(m, room),
        "chozo_regiao_e_itens": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_items_e_test(m, room),
        "chozo_save_station_3": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_save_3_test(m, room),
        # specs/12h: the region-A enemies alive in their rooms, no damage standing at the door
        "chozo_inimigos_vivos": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + chozo_enemies_test(m, room),
        # spec 15: every door entry of every room with enemies, a real one: no energy lost standing still in the first 2 s
        "entradas_de_porta_tallon": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + entry_audit(m, room, TALLON),
        "entradas_de_porta_chozo": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE])
        + chain_teleports(m, room, ["tallon_landing_site", "tallon_canyon_cavern", "tallon_canyon", "tallon_tunnel_a", WEST])
        + onto_platform(WEST) + ride_elevator(room, WEST, "build/tests/15_descendo.png") + entry_audit(m, room, CHOZO),
        # specs/14a: the Plated Beetle (a copy of the big Sidehopper) fought with the Power Beam only, nothing refilled
        "chozo_plated_beetle": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + plated_beetle_test(m, room),
        # specs/14b: the Hive Mecha (the arena routine) fought with the Power Beam only: the missile appears, is taken, the
        # room stays dead on re-entry and after a save and a continue
        "chozo_hive_mecha": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + hive_mecha_test(m, room),
        # specs/14c: Flaahgra (the Spore Spawn) fought with missiles: the Varia Suit appears, is taken, the grey door opens,
        # the room stays dead on re-entry and after a save and a continue; the room's colours stay the ruins'
        "chozo_flaahgra": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + flaahgra_test(m, room),
        # specs/14d: the Incinerator Drone's arena: taking the stand's missile shuts the door and spawns the hives and wasps; a
        # death mid-fight resets it (the save before); won with the Power Beam, the door opens, the room stays dead
        "chozo_incinerator_drone": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + incinerator_drone_test(m, room),
        # specs/12e: the Chozo East's and Chozo South's elevators, down and back up
        "elevador_chozo_east_e_south": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + elevator_east_and_south(m, room),
        # spec 07m: Gully and Alcove from the landing (door_teleport: behind the bomb walls and the Space
        # Jump ledge); the Alcove's Space Jump picked up; the Gully door's grey cap stays shut
        # spec 09a: each beam door shut to the Power Beam, missiles and a wrong beam, opened by its beam
        # (given by RAM: the beams come in 09b), walked through, shut again on the way back
        **{name: NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
           + lands_on_landing_site(room[LANDING_SITE])
           + (with_gravity_suit() if TALLON.by_key()[BEAM_DOORS[name][0]].water else [])
           + beam_door(m, room, name) for name in BEAM_DOORS},
        # specs/10b: up the Tallon's two dry floor doors, steering across the hole to the ledge on the other side
        "sobe_porta_de_teto_pela_borda_longe": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE])
        + chain_teleports(m, room, ["tallon_landing_site", "tallon_gully", "tallon_canyon"])
        + climb_ceiling_door(room, *CLIMBS[0]) + ["shot build/tests/subida_gully.png"]
        + chain_teleports(m, room, ["tallon_gully", "tallon_landing_site", "tallon_temple_hall", "tallon_temple_security",
                                    "tallon_temple_lobby", "tallon_artifact_temple"])
        + climb_ceiling_door(room, *CLIMBS[1]) + ["shot build/tests/subida_temple_lobby.png"],
        # specs/10c: the map with the rooms' shapes (Tallon Canyon, Artifact Temple: walls toward their rock screens)
        "mapa_com_a_forma_da_sala": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + explore(map_shape_screens())
        + ["hold START 10", "wait 200", f"expect {GAME_STATE} {GAME_STATE_PAUSED}"] + map_shows_shapes()
        + ["shot build/tests/mapa_forma_das_salas.png"],
        # specs/10a: the test helper door_teleport through floor/ceiling doors: BG1 on whole screens, up changes room
        "teleporte_de_porta_alinhado": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + aligned_teleports(m, room),
        "tallon_gully_alcove": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + tallon_gully_alcove(m, room),
        # spec 09d: the Morph Ball and the Bombs picked up by walking into them, the Gully's bomb blocks
        # bombed, the tunnel rolled through (no unmorphing under its roof), up into the Gully
        "tallon_morph_e_bombas": NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
        + lands_on_landing_site(room[LANDING_SITE]) + tallon_morph_and_bombs(m, room),
        # spec 09b: each lock item picked up by walking into it and used on its gate (LOCK_ITEM_TESTS)
        **{name: NEW_GAME + ["poke 7ED82B 01"] + board_ship() + ["wait 4100"]
           + lands_on_landing_site(room[LANDING_SITE]) + f(m, room) for name, f in LOCK_ITEM_TESTS.items()},
        "pulo_sem_space_jump_medido": NEW_GAME + traverse(route("hangar", JUMP_ROOM, False), room)
        + [f"expect {ROOM_PTR} {room[JUMP_ROOM]}"] + measure_jumps(),
        # spec 08: on foot down the Map Facility's floor door; she lands on the ledge and walks off
        "fragata_desce_porta_de_chao_e_anda": NEW_GAME + traverse(route("hangar", "map_facility", False), room)
        + walk_down_floor_door() + [f"expect {ROOM_PTR} {room['elevator_beta']}", f"expect {GAME_STATE} 0008",
                                    "shot build/tests/fragata_porta_de_chao.png"],
        **{CROSSING_TEST + key: level_crossing_test(m, room, key) for key in crossing_rooms(m)},
        "volta_evacuacao_ate_hangar": NEW_GAME + walk("RIGHT", 220) + walk("LEFT", 260) + [
            f"expect {ROOM_PTR} {room['hangar']}", f"expect {GAME_STATE} 0008",
            "shot build/tests/volta_fim.png",
        ],
    }


# specs/10b: up a dry room's floor door to the ledge on the other side of the hole. Samus stands on the platform under the
# ceiling door (row 6), `dx` px into its 4 columns (64 px), facing `steer` (a tap, as a player standing there would),
# jumps (A), steers toward the far ledge and keeps steering through the transition: she lands on that ledge (row h-3 of
# the room above: standing y = its top - 21), beyond the hole. With the old push ($0240) both of these fell back
# (scan of this climb every 4 px: $0240 lands from x+16 / x+48 on, $02A0 from x+12 / x+56; the sweep of the 16 dry
# ceiling doors: 54 of 160 climbs fell back, 28 with $02A0, all from the door's outer quarter: specs/10b).
CLIMBS = [("tallon_canyon", "tallon_gully", 12, "RIGHT"), ("tallon_artifact_temple", "tallon_temple_lobby", 52, "LEFT")]


def climb_ceiling_door(room: dict, key: str, to: str, dx: int, steer: str) -> list[str]:
    r, up = TALLON.by_key()[key], TALLON.by_key()[to]
    d = next(d for d in r.doors if d.to_room == to)
    x, y = (d.screen * 16 + 6) * 16 + dx, 6 * 16 - 21          # door columns from screen*16 + 6 (Canvas.door_gap)
    place = []
    for addr, v in ((0x7E0AF6, x), (0x7E0B10, x), (0x7E0AFA, y), (0x7E0B14, y), (0x7E0911, d.screen * 256), (0x7E0915, 0)):
        place += poke16(addr, v)
    ledge_top = (up.height * 16 - 3) * 16
    return (place + ["wait 30"] + place + ["wait 30", f"poke {HEALTH} 63", f"hold {steer} 2", "wait 20", "hold A 4",
                                            f"hold A+{steer} 30", f"hold {steer} 180", "wait 60",
                                            f"expect {ROOM_PTR} {room[to]}", f"expect {GAME_STATE} 0008",
                                            f"expect 7E0AFA {ledge_top - 21:04X}", "peekw 7E0AF6", "peekw 7E0AFE"])


def check_far_ledges(stdout: str) -> list[str]:
    """Each climb ends standing on the far ledge: her body (x $0AF6 ± x radius $0AFE, read by peekw) reaches past the
    hole of the floor door she came up through, on the side she steered to."""
    xs = [int(v, 16) for v in re.findall(r"7E0AF6 = ([0-9A-F]{4})", stdout)]
    rs = [int(v, 16) for v in re.findall(r"7E0AFE = ([0-9A-F]{4})", stdout)]
    if len(xs) != len(CLIMBS) or len(rs) != len(CLIMBS):
        return [f"FAIL subidas: {len(xs)}/{len(rs)} posições lidas, esperado {len(CLIMBS)}"]
    out = []
    for xv, rad, (key, to, _, steer) in zip(xs, rs, CLIMBS):
        up = TALLON.by_key()[to]
        hole = (next(d for d in up.doors if d.to_room == key).screen * 16 + 6) * 16
        if (steer == "RIGHT" and xv + rad <= hole + 64) or (steer == "LEFT" and xv - rad >= hole):
            out.append(f"FAIL {key} → {to}: x {xv:#x} (raio {rad}) em cima do buraco da porta ({hole:#x}-{hole + 63:#x})")
    return out


# specs/10a: door_teleport through floor and ceiling doors keeps BG1's offsets on whole screens (PLMs on their blocks),
# and a teleport up through a ceiling door changes room. Down the Gully's floor door to the Chozo West (its Morph Ball
# drawn once), back up the Tallon Canyon's ceiling door into the Gully; down the Temple Lobby's floor door and back up.
BG1_OFFSETS = ("7E091D", "7E091F")


def aligned_teleports(m: dict, room: dict) -> list[str]:
    peek = [f"peekw {a}" for a in BG1_OFFSETS]
    out = []
    for path in (["tallon_landing_site", "tallon_gully", "tallon_canyon", "tallon_tunnel_a", "tallon_transport_chozo_west"],
                 ["tallon_transport_chozo_west", "tallon_tunnel_a", "tallon_canyon", "tallon_gully", "tallon_landing_site",
                  "tallon_temple_hall", "tallon_temple_security", "tallon_temple_lobby", "tallon_artifact_temple",
                  "tallon_temple_lobby"]):
        for a, b in zip(path, path[1:]):
            out += door_teleport(m, a, b) + [f"expect {ROOM_PTR} {room[b]}"] + peek
        if path[-1] == "tallon_transport_chozo_west":
            out += tallon_look(11, 26, 0, 288, "build/tests/teleporte_chozo_west_morph.png")
    return out + ["shot build/tests/teleporte_temple_lobby.png"]


def check_whole_screen_bg1(stdout: str) -> list[str]:
    """Every BG1 offset printed (peekw) is a whole screen (low byte 0); at least one per teleport was printed."""
    vals = re.findall(rf"(?:{'|'.join(BG1_OFFSETS)}) = ([0-9A-F]{{4}})", stdout)
    bad = [v for v in vals if not v.endswith("00")]
    if len(vals) < 2 * 13:
        return [f"FAIL deslocamentos do BG1: só {len(vals)} lidos"]
    return [f"FAIL deslocamento do BG1 fora de tela inteira: {bad}"] if bad else []


CHECKS = {"pulo_sem_space_jump_medido": check_jumps, "tallon_rota_mvp": check_tallon_route,
          "teleporte_de_porta_alinhado": check_whole_screen_bg1, "sobe_porta_de_teto_pela_borda_longe": check_far_ledges,
          "tallon_rota_bc": lambda out: check_walk(out, TALLON_BC_PATH, "rota B/C do Tallon"),
          "pulo_na_agua_medido": check_water_jumps,
          "lava_medida": check_lava_jumps,   # specs/17d
          "neve_medida": check_snow_fall, "agua_medida_area_4": check_ice_water_jumps,   # specs/18d
          "elevador_magmoor_ida_e_volta": check_magmoor_label,   # specs/17e
          "elevador_phendrana_norte": check_phendrana_label,     # specs/18e
          "elevador_mines_leste": check_five_labels,              # specs/19e
          "entradas_de_porta_tallon": check_entries(TALLON), "entradas_de_porta_chozo": check_entries(CHOZO),   # spec 15
          "entradas_de_porta_magmoor": check_entries(MAGMOOR),   # specs/17g
          "entradas_de_porta_phendrana": check_entries(PHENDRANA),   # specs/18g
          "entradas_de_porta_mines": check_entries(MINES),   # specs/19g
          "tallon_rota_d": lambda out: check_walk(out, TALLON_D_PATH, "rota D do Tallon")}   # tests that also read their printed values


def run_one(name: str, lines: list[str], rom: Path = ROM) -> tuple[str, bool, list[str], str]:
    script = WORK / f"{name}.txt"
    script.write_text("\n".join(lines) + "\n")
    res = subprocess.run([str(RUNNER), str(rom), str(script)], capture_output=True, text=True, cwd=ROOT)
    fails = [l for l in res.stdout.splitlines() if "FAIL" in l]
    if name in CHECKS and res.returncode in (0, 2):
        fails += CHECKS[name](res.stdout)
    if name.startswith(CROSSING_TEST) and res.returncode in (0, 2):
        fails += check_level_in_ram(res.stdout, json.loads((ROOT / "build/manifest.json").read_text()),
                                    name.removeprefix(CROSSING_TEST))
    err = res.stderr.strip()[-300:] if res.returncode not in (0, 2) else ""
    return name, res.returncode == 0 and not fails, fails, err


# specs/17i: the two groups of the suite (`--grupo A` / `--grupo B`), each well under the tool's time limit when run alone:
# B = the Tallon's, the Chozo's, the Magmoor's and the elevators' tests, the door-entry audits and the tests on the test builds
# (12g, 17d); A = everything else (the frigate, the title, the beam doors and the other single checks). By name, so a new
# test falls in one of them by its prefix; group_of is total (a test is in A unless its name starts with one of B's prefixes).
# specs/17j: the full chain's parts by CHAIN_GROUP: part 1 (rounds 0-2) in A, parts 2 and 3 in B (they start from the state
# part 1 saved: run group A first, run_chain_parts); specs/18n: part 2 in B, parts 3 and 4 in C (run A, then B, then C); specs/19f:
# part 4 in D (run A, B, C, then D)
TEST_GROUP_B = ("tallon_", "chozo_", "magmoor_", "elevador_", "entradas_de_porta_", "nivel_cruza_banco_", "lava_",
                "porta_de_onda_lava", "porta_de_charge", "sala_quente")
# specs/18e (epic 18, "Testes: tempo por comando"): group C = Phendrana's tests (prefix phendrana_, its elevators, the ice looks'
# test build of 18d), run after B; the full chain's new parts (18n: through Phendrana) go here too, after the parts of A and B
# (CHAIN_GROUP: each part loads the state the one before saved), and a group D by the same rule if C passes ~5 min alone
TEST_GROUP_C = ("phendrana_", "elevador_phendrana_", "neve_medida", "porta_de_onda_gelo", "agua_medida_area_4",
                "entradas_de_porta_phendrana")   # specs/18g
# specs/19e (epic 19, "Testes: tempo por comando", user decision 8): group D = the Mines' tests (prefix mines_, its elevators, the
# Mines looks' test build of 19d, its door-entry audit), run after C; the full chain's new parts through the Mines (19m) go here
# too, after C's (CHAIN_GROUP)
TEST_GROUP_D = ("mines_", "elevador_mines_", "porta_de_plasma_mina", "entradas_de_porta_mines",
                "impact_")   # specs/20e: the Impact Crater's (after the Mines': its way in waits for the Omega Pirate)
TEST_GROUPS = ("A", "B", "C", "D")
# specs/18n: the parts from Phendrana's on in group C; specs/19f: part 4 in group D (group C reached ~6 min with parts 3 and 4: the
# chain's content is the same, part 4 loads the state part 3 saved, so run C before D)
# specs/19m: five parts: part 4 (rounds 4-5, the Mines' round 5) in C after part 3, part 5 (round 6 with the Mines', the end) in D
# specs/20j: six parts: part 6 (the Impact Crater, Metroid Prime, the ending) in D after part 5
CHAIN_GROUP = dict(zip(CHAIN_TESTS, ("A", "B", "C", "C", "D", "D")))


def group_of(name: str) -> str:
    if name in CHAIN_GROUP:
        return CHAIN_GROUP[name]
    if name.startswith(TEST_GROUP_D):   # before B: elevador_mines_* would be B's elevador_
        return "D"
    if name.startswith(TEST_GROUP_C):   # before B: elevador_phendrana_* would be B's elevador_
        return "C"
    return "B" if name.startswith(TEST_GROUP_B) else "A"


def chain_stamp(lines: dict[str, list[str]], k: int) -> dict[str, str]:
    """What part k's saved state comes from: the ROM's sha1 and the sha1 of the scripts of parts 1..k."""
    scripts = "\n".join(line for name in CHAIN_TESTS[:k + 1] for line in lines[name])
    return {"rom": hashlib.sha1(ROM.read_bytes()).hexdigest(), "scripts": hashlib.sha1(scripts.encode()).hexdigest()}


def run_chain_parts(lines: dict[str, list[str]], wanted: list[str]) -> list[tuple[str, bool, list[str], str]]:
    """specs/17j: the parts `wanted` of the full chain, one after the other (part k starts by loading the state part k-1 saved).
    After a part passes its state's stamp (chain_stamp) is written next to it; a part whose previous state is missing, or
    stamped for another ROM or other scripts, first runs that part (a prerequisite, reported as such: running the groups in
    order, A then B, it never happens); after a failed part the next ones fail without running."""
    results, failed = [], set()

    def stamp_path(k: int) -> Path:
        return ROOT / (chain_state(k) + ".json")

    def valid(k: int) -> bool:
        try:
            return (ROOT / chain_state(k)).exists() and json.loads(stamp_path(k).read_text()) == chain_stamp(lines, k)
        except (OSError, ValueError):
            return False

    def run(k: int, prerequisite: bool) -> bool:
        name = CHAIN_TESTS[k]
        label = name + (f" (pré-requisito da {CHAIN_TESTS[k + 1]}: o estado salvo dela faltava ou era de outra ROM ou roteiro)"
                        if prerequisite else "")
        if k and (k - 1 in failed or (not valid(k - 1) and not run(k - 1, True))):
            failed.add(k)
            results.append((label, False, [f"FAIL a parte anterior ({CHAIN_TESTS[k - 1]}) falhou: sem o estado dela"], ""))
            return False
        stamp_path(k).unlink(missing_ok=True)
        _, ok, fails, err = run_one(name, lines[name])
        results.append((label, ok, fails, err))
        if ok and k < len(CHAIN_TESTS) - 1:   # the last part saves no state
            stamp_path(k).write_text(json.dumps(chain_stamp(lines, k)))
        else:
            failed.add(k)
        return ok

    for name in sorted(wanted, key=CHAIN_TESTS.index):
        k = CHAIN_TESTS.index(name)
        if not any(r[0].startswith(name) for r in results):
            run(k, False)
    return results


def main() -> int:
    """Usage: run_tests.py [--grupo A|B|C|D] [name-substring ...]  (no argument = every test, run in parallel; --grupo: only the
    tests of that group, specs/17i, 18e, 19e)"""
    manifest = json.loads((ROOT / "build/manifest.json").read_text())
    WORK.mkdir(parents=True, exist_ok=True)
    TALLON_SHOTS.mkdir(exist_ok=True)
    args = sys.argv[1:]
    group = None
    if "--grupo" in args:
        i = args.index("--grupo")
        if i + 1 >= len(args) or args[i + 1] not in TEST_GROUPS:
            raise SystemExit(f"uso: run_tests.py [--grupo {'|'.join(TEST_GROUPS)}] [parte-do-nome ...]")
        group = args[i + 1]
        del args[i:i + 2]
    wanted = args

    def selected(n: str) -> bool:
        return (not wanted or any(w in n for w in wanted)) and (group is None or group_of(n) == group)
    all_lines = tests(manifest)
    jobs = [(n, l, ROM) for n, l in all_lines.items() if selected(n)]
    if not crossing_rooms(manifest):
        print("(nenhum nível cruza banco neste build: sem teste nivel_cruza_banco_*; "
              "experimento: tools/build.py --cruzar-banco SALA)")
    variant = [n for n in TEST_12G if selected(n)]
    if variant:   # specs/12g: the test build of the new locks, in build/teste-12g/ (the game's ROM is not touched)
        subprocess.run([sys.executable, "-I", str(ROOT / "tools/build.py"), "--teste-12g"], check=True,
                       capture_output=True, cwd=ROOT)
        lines_12g = tests_12g(json.loads((TEST_12G_DIR / "manifest.json").read_text()))
        jobs += [(n, lines_12g[n], TEST_12G_DIR / ROM.name) for n in variant]
    variant = [n for n in TEST_17D if selected(n)]
    if variant:   # specs/17d: the lava test build, in build/teste-17d/ (the game's ROM is not touched)
        subprocess.run([sys.executable, "-I", str(ROOT / "tools/build.py"), "--teste-17d"], check=True,
                       capture_output=True, cwd=ROOT)
        lines_17d = tests_17d(json.loads((TEST_17D_DIR / "manifest.json").read_text()))
        jobs += [(n, lines_17d[n], TEST_17D_DIR / ROM.name) for n in variant]
    variant = [n for n in TEST_18D if selected(n)]
    if variant:   # specs/18d: the ice looks' test build, in build/teste-18d/ (the game's ROM is not touched)
        subprocess.run([sys.executable, "-I", str(ROOT / "tools/build.py"), "--teste-18d"], check=True,
                       capture_output=True, cwd=ROOT)
        lines_18d = tests_18d(json.loads((TEST_18D_DIR / "manifest.json").read_text()))
        jobs += [(n, lines_18d[n], TEST_18D_DIR / ROM.name) for n in variant]
    variant = [n for n in TEST_19D if selected(n)]
    if variant:   # specs/19d: the Mines looks' test build, in build/teste-19d/ (the game's ROM is not touched)
        subprocess.run([sys.executable, "-I", str(ROOT / "tools/build.py"), "--teste-19d"], check=True,
                       capture_output=True, cwd=ROOT)
        lines_19d = tests_19d(json.loads((TEST_19D_DIR / "manifest.json").read_text()))
        jobs += [(n, lines_19d[n], TEST_19D_DIR / ROM.name) for n in variant]
    # specs/12m: the longest scripts first (frames of their waits and holds), so the longest one (the full chain) is not
    # left running alone at the end; the results are printed in the usual order. specs/17j: the full chain's parts in one
    # job, one after the other (run_chain_parts), started first
    chain = [j[0] for j in jobs if j[0] in CHAIN_TESTS]
    order = sorted((j for j in jobs if j[0] not in CHAIN_TESTS),
                   key=lambda job: -sum(int(l.split()[-1]) for l in job[1] if l.startswith(("wait ", "hold "))))
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        chain_future = pool.submit(run_chain_parts, all_lines, chain) if chain else None
        futures = {j[0]: pool.submit(run_one, *j) for j in order}
        done = {j[0]: futures[j[0]].result() for j in order}
        chain_results = chain_future.result() if chain_future else []
    results = [done[j[0]] for j in jobs if j[0] not in CHAIN_TESTS]
    at = next((i for i, j in enumerate(jobs) if j[0] in CHAIN_TESTS), len(results))
    results[at:at] = chain_results
    failed = 0
    for name, ok, fails, err in results:
        failed += not ok
        print(f"{'PASSOU' if ok else 'FALHOU'}  {name}")
        for l in fails:
            print("        ", l)
        if err:
            print("        erro do emulador:", err)
    print(f"\n{len(results) - failed}/{len(results)} testes passaram" + (f" (grupo {group})" if group else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

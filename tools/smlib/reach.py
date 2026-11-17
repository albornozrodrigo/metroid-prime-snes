"""Where Samus can get to in a room, for a given equipment (specs/07b-alcance-sem-space-jump.md).
In a flooded room (water FX, specs/07l) the jump is the one measured underwater: with the Gravity
Suit the same blocks as on dry land (a pixel shorter here and there), without it a low, long jump,
and no Space Jump (pulo_na_agua_medido).

With Space Jump any connected open space is reachable (flood fill, what the frigate always used).
Without it, Samus is modelled on a block grid: she stands somewhere (feet on a floor block, 3 free
rows for her body), walks, falls, climbs a ledge beside her up to H blocks, and jumps over gaps up
to W(rise) columns. The numbers come from the emulator (tests/run_tests.py,
pulo_sem_space_jump_medido) and that test fails if the game ever disagrees with them.
Only the plain jump is assumed: no run-up, wall-jump or other technique for a required path.

Morph Ball (specs/09d): a ball state (x, y, BALL) takes one block; it rolls one column at a time
into a free block and falls until it rests on a floor; Samus morphs wherever she stands (the ball sits in
her feet's block) and unmorphs only where she can stand (3 free rows). No jump in the ball, no bomb jump.
Bomb blocks (block type F) are solid without the Bombs and air with them: whoever builds the grid swaps
them (tools/validate.py foot_grid); tools/validate.py check_breakables proves each one can be bombed.
Power Bomb blocks (specs/09e: shot block type C with BTS $08/$09, sm_84.c:2250, only a power bomb breaks them) are
solid without the Power Bomb and air with it and the Morph Ball (it is laid in the ball); never the body's air the
other type-C blocks (door caps) are. A power bomb also breaks bomb blocks in the game: the model does not count it.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace

BLOCK = 16
STANDING_ROWS = 3        # standing Samus is 42 px tall
SAMUS_HEIGHT = 42
HEAD_GAP = STANDING_ROWS * BLOCK - SAMUS_HEIGHT   # px between her head and the top of her 3 rows

# Measured in the emulator (specs/07b, table "Física do pulo medida no emulador"):
JUMP_RISE_PX = 113       # feet rise of a jump from standing still, no items
HIJUMP_RISE_PX = 169     # the same with Hi-Jump Boots
# horizontal px of the standing jump with a direction held (no run-up), at the last frame of the
# flight where the feet are still at least `rise` blocks above the take-off floor
JUMP_ARC_PX = {0: 115, 1: 109, 2: 105, 3: 100, 4: 94, 5: 87, 6: 79, 7: 62}
# underwater (water FX type 6, surface over the room; specs/07l, measured in the Savestation):
# with the Gravity Suit, and without it (no Space Jump there: it doesn't work underwater)
WATER_GRAVITY_RISE_PX = 113
WATER_GRAVITY_ARC_PX = {0: 112, 1: 108, 2: 105, 3: 100, 4: 93, 5: 87, 6: 78, 7: 62}
WATER_RISE_PX = 51
WATER_ARC_PX = {0: 144, 1: 131, 2: 116, 3: 91}

# specs/17d: in SM's lava (FX type 2), measured in the lava test build (tools/build.py --teste-17d, tests lava_medida):
# without the Gravity Suit the jump starts with the liquid speed and loses it in the lava; how high her feet rise depends on
# how deep they stand (rows under the surface: px). From 3 rows down the feet peak 21 px over the surface, from 2 rows 26, from
# 1 row 30; deeper was not measured (a deeper lava stand is an error: check_lava). The Varia changes the damage, not the
# jump; with the Gravity Suit the jump is the dry one (113 px). Space Jump: the model never counts it in the lava (SM turns it
# off while her head is under the surface, sm_90.c Samus_Movement_03_SpinJumping).
LAVA_RISE_PX = {1: 46, 2: 58, 3: 69}
LAVA_MAX_DEPTH = max(LAVA_RISE_PX)
LAVA_MAX_MOVES = 5        # an escape from the lava: at most this many moves (a block walked, a fall, a climb) before she stands out of it
# energy lost a frame in the lava (sub-units of $10000, measured over 120 frames): no suit 1/2, Varia 1/4, Gravity 0
LAVA_DAMAGE_PER_FRAME = {"nada": 0.5, "varia": 0.25, "gravity": 0.0}

AIR = 0x0
SOLID = 0x8
LAVA = 0x10              # specs/17d: an air block under a room's lava surface (not a block type of the game: with_lava)
BOMB_BLOCK = 0xF         # block type broken by a bomb or a power bomb (sm_94.c:1535)
SHOT_BLOCK = 0xC         # shot block type: door caps, and with these BTS the power bomb blocks (specs/09e)
POWER_BOMB_BTS = frozenset({0x08, 0x09})   # $94:9EA6 + 2 * BTS -> PLM $D084/$D088, setup $CF2E (read)
BALL = "bola"            # third field of a ball state (x, y, BALL)
# block types her body can be in: air, door, shootable door caps and their extensions
BODY_TYPES = frozenset({0x0, 0x5, 0x9, 0xC, 0xD})


@dataclass(frozen=True)
class Loadout:
    space_jump: bool = False
    hi_jump: bool = False
    morph: bool = False   # the ball (specs/09d); the Space Jump's flood fill needs it
    bombs: bool = False   # bomb blocks are air (the grid builder swaps them, specs/09d)
    power_bomb: bool = False   # with the Morph Ball, power bomb blocks are air (specs/09e)
    gravity: bool = False
    water: bool = False   # the room is flooded (the physics of this walk, not an item)
    lava_depth: int = 0   # specs/17d: rows her feet stand under a lava surface (0 = out of it): the measured lava jump
    plasma: bool = False   # specs/18i: a room's in-room plasma caps open (RoomDef.caps; the grid builder, validate.with_caps)

    def __post_init__(self):
        if self.water and self.hi_jump:
            raise ValueError("pulo com Hi-Jump debaixo d'água não foi medido")

    @property
    def rise_px(self) -> int:
        if self.lava_depth and not self.gravity:
            return LAVA_RISE_PX[self.lava_depth]
        if self.water:
            return WATER_GRAVITY_RISE_PX if self.gravity else WATER_RISE_PX
        return HIJUMP_RISE_PX if self.hi_jump else JUMP_RISE_PX

    @property
    def arc_px(self) -> dict[int, int]:
        if self.lava_depth and not self.gravity:
            return {0: 0}   # specs/17d: no gap jump counted out of the lava (only straight up beside a ledge)
        if self.water:
            return WATER_GRAVITY_ARC_PX if self.gravity else WATER_ARC_PX
        return JUMP_ARC_PX

    @property
    def flies(self) -> bool:
        """Space Jump works: on land, or underwater with the Gravity Suit."""
        return self.space_jump and (self.gravity or not self.water) and not self.lava_depth

    @property
    def max_rise(self) -> int:
        """Highest ledge (blocks above her floor) she can climb beside her."""
        return self.rise_px // BLOCK


SPACE_JUMP_MORPH = Loadout(space_jump=True, morph=True)   # the frigate (Prime's start loadout)
POWER_BEAM_ONLY = Loadout()                                # Tallon arrival (epic 07, decision 3)


def across(rise: int, arc: dict[int, int] = JUMP_ARC_PX) -> int:
    """Columns (centre to centre) of a gap jump that ends `rise` blocks higher (<= 0: same or lower)."""
    if rise <= 0:
        return arc[0] // BLOCK
    return arc[rise] // BLOCK if rise in arc else 0


def apex_row(y: int, rise_px: int) -> int:
    """Row of her head at the top of a full jump from a stand at row y (feet in row y)."""
    return y - 2 + (HEAD_GAP - rise_px) // BLOCK


def arc_from_samples(samples: list[tuple[int, int]]) -> tuple[int, dict[int, int]]:
    """(rise px, {rise blocks: horizontal px}) of one jump, from (x, feet y) per frame. The first
    sample is on the ground, before the jump; the flight goes from take-off to landing."""
    x0, b0 = samples[0]
    takeoff = next((i for i, (_, b) in enumerate(samples) if b < b0), None)
    if takeoff is None:
        raise ValueError("a Samus não saiu do chão")
    land = next((j for j in range(takeoff, len(samples)) if samples[j][1] >= b0), None)
    if land is None:
        raise ValueError("a Samus não voltou ao chão")
    flight = samples[takeoff:land + 1]
    rise = b0 - min(b for _, b in flight)
    arc = {r: max(abs(x - x0) for x, b in flight if b0 - b >= BLOCK * r) for r in range(rise // BLOCK + 1)}
    return rise, arc


class Grid:
    """Block types of a room (row-major, wb x hb)."""

    def __init__(self, types: list[int], wb: int, hb: int):
        self.types, self.wb, self.hb = types, wb, hb

    def type(self, x: int, y: int) -> int | None:
        return self.types[y * self.wb + x] if 0 <= x < self.wb and 0 <= y < self.hb else None

    def body(self, x: int, y: int) -> bool:
        return self.type(x, y) in BODY_TYPES

    def floor(self, x: int, y: int) -> bool:
        t = self.type(x, y)
        return t is not None and t not in (AIR, LAVA)

    def clear(self, x: int, y0: int, y1: int) -> bool:
        return all(self.body(x, y) for y in range(y0, y1 + 1))

    def stands(self, x: int, y: int) -> bool:
        return self.floor(x, y + 1) and self.clear(x, y - STANDING_ROWS + 1, y)

    def ball_land(self, x: int, y: int) -> tuple[int, int, str] | None:
        """The ball rolled into (x, y) falls to the floor; None if (x, y) is not free."""
        if not self.body(x, y):
            return None
        while not self.floor(x, y + 1):
            y += 1
            if not self.body(x, y):
                return None
        return x, y, BALL

    def land(self, x: int, y: int) -> tuple[int, int] | None:
        """Fall from (x, y) (her feet's row) to the floor; None if she can't stand where she lands."""
        if not self.body(x, y):
            return None
        while not self.floor(x, y + 1):
            y += 1
            if not self.body(x, y):
                return None
        return (x, y) if self.stands(x, y) else None


def flood(passable, start: tuple[int, int], loadout: Loadout) -> set[tuple[int, int]]:
    """Space Jump: every 4-connected open cell from `start`. A 1-block cell is only open to the
    Morph Ball, so the fill needs it (specs/09d)."""
    if not loadout.morph:
        raise ValueError("flood fill sem Morph Ball: a célula de 1 bloco pressupõe a bola")
    stack, seen = [start], {start}
    while stack:
        x, y = stack.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in seen and passable(nx, ny):
                seen.add((nx, ny))
                stack.append((nx, ny))
    return seen


def moves(g: Grid, state: tuple, loadout: Loadout):
    """States reachable in one move: from a stand (x, y), or a ball (x, y, BALL) (specs/09d)."""
    x, y = state[0], state[1]
    if len(state) == 3:
        for s in (-1, 1):          # roll, falling down any hole
            t = g.ball_land(x + s, y)
            if t:
                yield t
        if g.stands(x, y):         # unmorph: 3 free rows
            yield x, y
        return
    if loadout.morph:
        yield x, y, BALL
    top = apex_row(y, loadout.rise_px)
    for s in (-1, 1):
        # walk, or walk off the edge and fall
        if g.clear(x + s, y - 2, y):
            t = g.land(x + s, y)
            if t:
                yield t
        # jump straight up beside a ledge and step onto it (one block of headroom over her head)
        for r in range(1, loadout.max_rise + 1):
            if g.stands(x + s, y - r) and g.clear(x, y - r - 3, y):
                yield x + s, y - r
        # gap jump with the full arc: every column from the take-off one to the landing one must
        # be open from the top of the jump down to where she stands
        if not g.clear(x, top, y):
            continue
        arc = loadout.arc_px
        for d in range(2, across(0, arc) + 1):
            x2 = x + s * d
            t = g.land(x2, top)
            if t is None or not g.clear(x2, top, t[1]):
                continue
            y2 = t[1]
            if y - y2 > loadout.max_rise or d > across(y - y2, arc):
                continue
            if all(g.clear(x + s * k, top, max(y, y2)) for k in range(1, d)):
                yield t


def reach(g: Grid, starts: list[tuple[int, int]], loadout: Loadout) -> set[tuple]:
    """States (stands, and balls with the Morph Ball) reachable on foot from the stands in `starts`."""
    if loadout.flies:
        raise ValueError("com Space Jump o alcance é o flood fill (reach.flood)")
    seen, queue = set(starts), deque(starts)
    while queue:
        for t in moves(g, queue.popleft(), loadout):
            if t not in seen:
                seen.add(t)
                queue.append(t)
    return seen


def stuck(g: Grid, stands: set, doors: list[tuple[str, int]], loadout: Loadout,
          exits: frozenset = frozenset()) -> set[tuple[int, int]]:
    """Stands of `stands` (a set closed under moves, e.g. what reach returned) from which no door
    can be reached any more: a pit or fall with no way back is a softlock (specs/07j). `exits`: more
    stands that are a way out (specs/12e: standing on an elevator's platform)."""
    back: dict[tuple[int, int], list] = {s: [] for s in stands}
    for s in stands:
        for t in moves(g, s, loadout):
            if t in back:
                back[t].append(s)
    good = {s for s in stands
            if s in exits or any(door_reached(g, side, screen, {s}, loadout) for side, screen in doors)}
    queue = deque(good)
    while queue:
        for s in back[queue.popleft()]:
            if s not in good:
                good.add(s)
                queue.append(s)
    return set(stands) - good


def door_columns(screen: int) -> range:
    return range(screen * BLOCK + 6, screen * BLOCK + 10)


def door_entry(g: Grid, side: str, screen: int) -> tuple[int, int] | None:
    """Where Samus stands after coming in through a door (rows/columns as tools/smlib/level.py)."""
    if side in "LR":
        return g.land(2 if side == "L" else g.wb - 3, screen * BLOCK + 9)
    col = screen * BLOCK + 7
    return g.land(col, 3) if side == "T" else g.land(col, g.hb - 4)


def door_reached(g: Grid, side: str, screen: int, reached: set, loadout: Loadout) -> bool:
    """A side or floor door takes Samus standing or in the ball; a ceiling door only standing (a jump)."""
    if side in "LR":
        col = 2 if side == "L" else g.wb - 3
        rows = range(screen * BLOCK + 6, screen * BLOCK + 12)   # her body touches door rows 6-9
        return any(s[0] == col and s[1] in rows for s in reached)
    cols = door_columns(screen)
    if side == "B":
        return any(s[0] in cols and s[1] >= g.hb - 4 for s in reached)
    # top door: jump straight up into row 0
    return any(len(s) == 2 and s[0] in cols and g.clear(s[0], 0, s[1])
               and (s[1] - 2) * BLOCK + HEAD_GAP - loadout.rise_px < BLOCK for s in reached)


def body_cells(states) -> set[tuple[int, int]]:
    """Blocks Samus' body is in: the 3 rows of a stand, the block of a ball (an item there is picked up)."""
    return {(s[0], s[1] - k) for s in states for k in range(1 if len(s) == 3 else STANDING_ROWS)}


def with_lava(types: list[int], wb: int, lava_row: int | None) -> list[int]:
    """specs/17d: block types with every body block (air, door) from the lava's surface row down marked LAVA: neither a place
    for her body nor a floor. The model walks a room with lava without ever going into it (the user's rule: lava never on a
    mandatory path); check_lava proves every lava stand has a quick way out."""
    if lava_row is None:
        return list(types)
    return [LAVA if i // wb >= lava_row and t in BODY_TYPES else t for i, t in enumerate(types)]


def lava_escapes(g: Grid, lava_row: int, out: set, loadout: Loadout) -> dict[tuple[int, int], int | None]:
    """specs/17d: for every place she can stand in the lava of grid `g` (lava rows as air: the real room), the fewest moves to
    a stand of `out` (the places out of the lava from which she gets on; None: none in LAVA_MAX_MOVES), with the lava jump of
    the depth of each stand (LAVA_RISE_PX; Gravity Suit: the dry jump) and never the Space Jump. A stand deeper than
    LAVA_MAX_DEPTH gets None too (its jump was not measured)."""
    def lo(state) -> Loadout:
        depth = state[1] - lava_row + 1
        return replace(loadout, space_jump=False, lava_depth=max(0, min(depth, LAVA_MAX_DEPTH)) if depth > 0 else 0)

    result = {}
    for y in range(lava_row, g.hb):
        for x in range(g.wb):
            if not g.stands(x, y):
                continue
            if y - lava_row + 1 > LAVA_MAX_DEPTH:
                result[(x, y)] = None
                continue
            frontier, seen, found = [(x, y)], {(x, y)}, None
            for step in range(1, LAVA_MAX_MOVES + 1):
                nxt = []
                for s in frontier:
                    for t in moves(g, s, lo(s)):
                        if len(t) == 2 and t in out:
                            found = step
                            break
                        if t not in seen:
                            seen.add(t)
                            nxt.append(t)
                    if found:
                        break
                if found:
                    break
                frontier = nxt
            result[(x, y)] = found
    return result


def is_power_bomb_block(t: int, b: int) -> bool:
    return t == SHOT_BLOCK and b in POWER_BOMB_BTS


def with_breakables(types: list[int], bts, loadout: Loadout) -> list[int]:
    """Block types (bts: the room's BTS, same order) with the breakable blocks swapped for the loadout: bomb
    blocks air with the Bombs (specs/09d); power bomb blocks air with the Power Bomb and the Morph Ball, solid
    without them (specs/09e)."""
    pb = loadout.power_bomb and loadout.morph
    out = []
    for t, b in zip(types, bts, strict=True):
        if t == BOMB_BLOCK and loadout.bombs:
            t = AIR
        elif is_power_bomb_block(t, b):
            t = AIR if pb else SOLID
        out.append(t)
    return out


# --- model checks on synthetic rooms (run by tools/validate.py) ---------------------------------

def _room(w: int, h: int, solids=(), doors=()) -> Grid:
    """Closed box w x h; `solids` = (x0, y0, x1, y1) inclusive; `doors` = (x, y) door blocks."""
    t = [SOLID if x in (0, w - 1) or y in (0, h - 1) else AIR for y in range(h) for x in range(w)]
    for x0, y0, x1, y1 in solids:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                t[y * w + x] = SOLID
    for x, y in doors:
        t[y * w + x] = 0x9
    return Grid(t, w, h)


def _ledge(k: int, ceiling=()) -> Grid:
    """Samus on the floor (feet row 22) left of a ledge k blocks high (columns 6-10)."""
    return _room(12, 24, [(6, 23 - k, 10, 22), *ceiling])


def _gap(d: int, rise: int = 0, ceiling=()) -> Grid:
    """Left shelf (columns 1-5, top row 20) and right shelf from column 5+d, `rise` blocks higher,
    over a pit too deep to climb out of."""
    return _room(24, 40, [(1, 20, 5, 38), (5 + d, 20 - rise, 22, 38), *ceiling])


def self_test() -> list[str]:
    """Cases of specs/07b (criterion 4): each pair is a pass and the mutation that must fail."""
    walk, hj = POWER_BEAM_ONLY, Loadout(hi_jump=True)
    wet_g, wet = Loadout(water=True, gravity=True), Loadout(water=True)
    # the spec's numbers, written out: a change of the constants above must show up here too
    H, HJ, W, W_UP = 7, 10, 7, 3   # ledge, ledge with Hi-Jump, gap, gap rising H (blocks)
    WH, WW = 3, 9                  # underwater without the Gravity Suit: ledge, gap (specs/07l)
    cases = [  # (name, grid, start, goal, loadout, expected)
        (f"degrau de {H}", _ledge(H), (2, 22), (8, 22 - H), walk, True),
        (f"degrau de {H + 1}", _ledge(H + 1), (2, 22), (8, 21 - H), walk, False),
        (f"Hi-Jump degrau de {HJ}", _ledge(HJ), (2, 22), (8, 22 - HJ), hj, True),
        (f"Hi-Jump degrau de {HJ + 1}", _ledge(HJ + 1), (2, 22), (8, 21 - HJ), hj, False),
        (f"vão de {W} colunas", _gap(W), (2, 19), (5 + W, 19), walk, True),
        (f"vão de {W + 1} colunas", _gap(W + 1), (2, 19), (6 + W, 19), walk, False),
        (f"vão subindo {H}: {W_UP} colunas", _gap(W_UP, H), (2, 19), (5 + W_UP, 19 - H), walk, True),
        (f"vão subindo {H}: {W_UP + 1} colunas", _gap(W_UP + 1, H), (2, 19), (6 + W_UP, 19 - H), walk, False),
        (f"degrau de {H} com teto baixo", _ledge(H, [(1, 1, 5, 13)]), (2, 22), (8, 22 - H), walk, False),
        (f"vão de {W} com teto baixo no meio", _gap(W, 0, [(8, 1, 8, 13)]), (2, 19),
         (5 + W, 19), walk, False),
        ("queda de um buraco fundo", _room(16, 32, [(1, 12, 6, 12)]), (2, 11), (10, 30), walk, True),
        # underwater (specs/07l): with the Gravity Suit the same blocks as on land; without it a
        # 3-block ledge, gaps of 9 columns (the long, slow jump)
        (f"água com Gravity: degrau de {H}", _ledge(H), (2, 22), (8, 22 - H), wet_g, True),
        (f"água com Gravity: degrau de {H + 1}", _ledge(H + 1), (2, 22), (8, 21 - H), wet_g, False),
        (f"água com Gravity: vão de {W} colunas", _gap(W), (2, 19), (5 + W, 19), wet_g, True),
        (f"água com Gravity: vão de {W + 1} colunas", _gap(W + 1), (2, 19), (6 + W, 19), wet_g, False),
        (f"água sem Gravity: degrau de {WH}", _ledge(WH), (2, 22), (8, 22 - WH), wet, True),
        (f"água sem Gravity: degrau de {WH + 1}", _ledge(WH + 1), (2, 22), (8, 21 - WH), wet, False),
        (f"água sem Gravity: vão de {WW} colunas", _gap(WW), (2, 19), (5 + WW, 19), wet, True),
        (f"água sem Gravity: vão de {WW + 1} colunas", _gap(WW + 1), (2, 19), (6 + WW, 19), wet, False),
        ("volta da queda", _room(16, 32, [(1, 12, 6, 12)]), (10, 30), (2, 11), walk, False),
    ]
    problems = []
    for name, g, start, goal, loadout, want in cases:
        if not g.stands(*start) or not g.stands(*goal):
            problems.append(f"{name}: caso mal montado (início ou alvo sem lugar de pé)")
            continue
        got = goal in reach(g, [start], loadout)
        if got != want:
            problems.append(f"{name}: esperado {'alcança' if want else 'não alcança'}, deu o contrário")
    # no Space Jump underwater without the Gravity Suit (specs/07l)
    if Loadout(space_jump=True, water=True).flies or not Loadout(space_jump=True, water=True, gravity=True).flies:
        problems.append("Space Jump debaixo d'água: só com a Gravity Suit")
    # Space Jump: connected air is enough, even for a ledge too high to jump
    g = _ledge(H + 1)
    seen = flood(lambda x, y: g.type(x, y) not in (None, SOLID), (2, 22), SPACE_JUMP_MORPH)
    if (8, 21 - H) not in seen:
        problems.append(f"Space Jump degrau de {H + 1}: esperado alcança, deu o contrário")
    try:   # specs/09d: a 1-block cell is the ball's, the fill can't go without it
        flood(lambda x, y: g.type(x, y) not in (None, SOLID), (2, 22), Loadout(space_jump=True))
        problems.append("flood fill sem Morph Ball: esperado erro, deu certo")
    except ValueError:
        pass
    problems += _ball_cases()
    problems += _lava_cases()
    # a fall with no way back to the door is a trap; a flat floor is not (specs/07j)
    for name, g, start, trapped in (("buraco sem volta", _room(16, 32, [(1, 12, 6, 12)]), (2, 11), True),
                                    ("chão plano", _room(16, 13), (2, 11), False)):
        got = bool(stuck(g, reach(g, [start], walk), [("L", 0)], walk))
        if got != trapped:
            problems.append(f"{name}: esperado {'preso' if trapped else 'sem lugar preso'}, deu o contrário")
    # top door (columns 6-9 of row 0): feet in row 9 reach it with a jump, row 10 doesn't
    for feet, want in ((9, True), (10, False)):
        g = _room(16, 24, [(1, feet + 1, 14, 22)], [(x, 0) for x in door_columns(0)])
        got = door_reached(g, "T", 0, reach(g, [(7, feet)], walk), walk)
        if got != want:
            problems.append(f"porta de teto, pé na linha {feet}: esperado {'alcança' if want else 'não alcança'}")
    return problems


def _tunnel(extra=(), bomb=None, power_bomb=None) -> Grid:
    """Samus on the floor (feet row 10) left of a wall (columns 6-8) with a 1-row tunnel at the floor;
    3 free rows past it. `bomb` = a bomb block in the tunnel; `power_bomb` = a power bomb block (BTS $09)."""
    g = _room(16, 12, [(6, 1, 8, 9), *extra])
    g.bts = bytearray(len(g.types))
    if bomb:
        g.types[bomb[1] * g.wb + bomb[0]] = BOMB_BLOCK
    if power_bomb:
        g.types[power_bomb[1] * g.wb + power_bomb[0]] = SHOT_BLOCK
        g.bts[power_bomb[1] * g.wb + power_bomb[0]] = 0x09
    return g


def _lava_pit(depth: int, wall: int = 0) -> Grid:
    """specs/17d: a floor (top row 10) with a pit at columns 6-9 `depth` rows deep, the lava's surface at row 10 (so its stands
    are `depth` rows under it); `wall`: the floor west of the pit raised that many rows (and the east side walled up)."""
    return _room(16, 24, [(1, 10, 5, 22), (10, 10, 14, 22), (6, 10 + depth, 9, 22), (1, 10 - wall, 5, 9),
                          (10, 1, 14, 9) if wall else (0, 0, 0, 0)])


def _lava_cases() -> list[str]:
    """specs/17d: the lava model. Each pair: what must pass and the mutation that must fail."""
    walk = POWER_BEAM_ONLY
    out = []
    for depth, wall, want in ((1, 0, True), (3, 0, True), (3, 1, True), (3, 2, False), (4, 0, False)):
        g = _lava_pit(depth, wall)
        dry = Grid(with_lava(g.types, g.wb, 10), g.wb, g.hb)
        outside = reach(dry, [(2, 9 - wall)] + ([] if wall else [(12, 9)]), walk)
        got = lava_escapes(g, 10, outside, walk)
        ok = bool(got) and all(v is not None for v in got.values())
        if ok != want:
            out.append(f"lava a {depth} linhas, borda {wall} acima: esperado {'sai' if want else 'não sai'}, deu o contrário")
        if any(len(st) == 2 and st[1] >= 10 for st in outside):
            out.append(f"lava a {depth} linhas: o modelo pôs a Samus de pé dentro da lava")
    if Loadout(lava_depth=1, space_jump=True).flies:
        out.append("Space Jump contado dentro da lava")
    return out


def _ball_cases() -> list[str]:
    """specs/09d: the Morph Ball on foot. Each pair: what must pass and the mutation that must fail."""
    walk, ball, bombs = POWER_BEAM_ONLY, Loadout(morph=True), Loadout(morph=True, bombs=True)
    pb = Loadout(morph=True, power_bomb=True)

    def stands_past(g: Grid, loadout: Loadout, col: int = 9) -> bool:
        return any(len(s) == 2 and s[0] >= col for s in reach(g, [(2, 10)], loadout))

    def bombed(g: Grid, loadout: Loadout) -> Grid:
        return Grid(with_breakables(g.types, getattr(g, "bts", bytes(len(g.types))), loadout), g.wb, g.hb)

    cases = [  # (name, got, expected)
        ("túnel de 1 linha a pé", stands_past(_tunnel(), walk), False),
        ("túnel de 1 linha com a Morph", stands_past(_tunnel(), ball), True),
        # a 2-row tunnel (rows 9-10) whose floor rises by one block at columns 7-8: the ball does not
        # climb it (and the same tunnel without the step lets it through)
        ("bola num degrau de 1", stands_past(_room(16, 12, [(6, 1, 8, 8), (7, 10, 8, 10)]), ball), False),
        ("bola sem o degrau", stands_past(_room(16, 12, [(6, 1, 8, 8)]), ball), True),
        # past the tunnel only 2 free rows (rows 9-10): she rolls there but can't unmorph
        ("desfazer a bola num vão de 2 linhas", stands_past(_tunnel([(9, 1, 14, 8)]), ball), False),
        ("desfazer a bola num vão de 3 linhas", stands_past(_tunnel([(9, 1, 14, 7)]), ball), True),
        ("bloco de bomba sem as Bombas", stands_past(bombed(_tunnel(bomb=(7, 10)), ball), ball), False),
        ("bloco de bomba com as Bombas", stands_past(bombed(_tunnel(bomb=(7, 10)), bombs), bombs), True),
        # specs/09e: a power bomb block holds against the ball and the Bombs, breaks with the Power Bomb
        ("bloco de PB só com a Morph", stands_past(bombed(_tunnel(power_bomb=(7, 10)), ball), ball), False),
        ("bloco de PB com as Bombas", stands_past(bombed(_tunnel(power_bomb=(7, 10)), bombs), bombs), False),
        ("bloco de PB com a Power Bomb", stands_past(bombed(_tunnel(power_bomb=(7, 10)), pb), pb), True),
    ]
    return [f"{name}: esperado {'alcança' if want else 'não alcança'}, deu o contrário"
            for name, got, want in cases if got != want]

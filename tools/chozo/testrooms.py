"""specs/12g: the test build's room for the Chozo's new locks (tools/build.py --teste-12g), never the game's ROM.

The Charge Beam (Watery Hall, region D) and the Varia Suit (Sunchamber, region C) have no room yet (12j, 12k place them and
their locks). The mechanisms are proven in a separate ROM (build/teste-12g/, tests/run_tests.py porta_de_charge and
sala_quente) where one built region-A room carries all of them: the Ruined Fountain Access (off the Main Plaza; specs/12j
opened its door to the Ruined Fountain, region C: in the test build that door leads into the hot room, Varia gated). There it is hot (RoomDef.heat, chozo/heat.py), its door to the
Main Plaza is a charge door on its side (tallon/beamdoors.py, gate CHARGE both ways, as chozo/rooms.py GATES would make it),
the Charge Beam lies on the block platform and the Varia Suit on the floor east of it, with their real bits
(chozo/items.py rows 7 and 8). The game's build (build.py with no option) never calls this.
"""
from __future__ import annotations

import dataclasses

from tallon.rooms import CHARGE, LOCK_OF

from . import items as chozo_items
from .rooms import heat_gates

ROOM = "chozo_ruined_fountain_access"
PLAZA = "chozo_main_plaza"
# on the platform; on the floor east of it, far enough from the middle of the screen (the vanilla cutscene's spot: x = the
# camera's + 120, the camera at the room's east end) for the test to tell the varia_patch's "where she took it" from it
SPOTS = {chozo_items.CHARGE_BEAM: (24, 7), chozo_items.VARIA_SUIT: (44, 9)}


def apply(area) -> list[tuple[int, chozo_items.Item]]:
    """Turn ROOM of `area` (the Chozo's RoomDefs, changed in place) into the test room; returns the (bit, item) pairs to
    place in it."""
    rooms = area.by_key()
    r = rooms[ROOM]
    # specs/12j: the room's door to the Ruined Fountain (region C) is open now; the test room's charge door is still the one
    # to the Main Plaza, its first door (tests/run_tests.py charge_door_white reads doors[0])
    if not r.doors or r.doors[0].to_room != PLAZA or r.doors[0].lock is not None or r.doors[0].gate:
        raise RuntimeError(f"{ROOM}: esperado a 1ª porta sem trava para a {PLAZA}, achado {r.doors}")
    d = r.doors[0]
    back = rooms[d.to_room].doors[d.to_door]
    d.lock, d.gate = LOCK_OF[CHARGE], frozenset({CHARGE})
    back.gate = back.gate | {CHARGE}
    r.heat = True
    heat_gates(rooms)
    # specs/12h: no enemies in the test room (its Wall Crawlers would touch Samus while sala_quente measures the heat and
    # porta_de_charge stands at the door); the game's ROM keeps them
    area.enemies.pop(ROOM, None)
    out = []
    for n, it in enumerate(chozo_items.ITEMS):
        if it.kind in SPOTS:
            out.append((chozo_items.BITS[n], dataclasses.replace(it, room=ROOM, spot=SPOTS[it.kind])))
    return out

"""Where the grass grows (the patches from maya/make_grass.py): on every bit of bare ground (the
forest floor and the same ground round the motel and office), as one even carpet with no holes:
- big 4 m patches wherever they fit, then small 1.5 m patches filling every gap they leave
  (along the trail, the lot, the road shoulder, round the buildings)
- right up to the walls of the hunter's shack, the cabins, the boathouse and under the lookout
  tower (only their floors / the tower's stairs are kept clear, or blades would poke through)
- down the bank to the lake it thins out slowly, the last tufts at the water, each patch sat on
  the sloping ground (z from maya/make_lake.py's ground_z)
Never on the road, its gravel shoulders and ditch, the lot, the motel, the office, the trail itself.

Run with normal Python:  python tools/make_grass_layout.py
Writes export/grass.json: [{"mesh", "x", "y", "z", "yaw"}]. unreal/grass.py places them.
"""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_fill import LAYOUT, EDGE, SOUTH, near_trail          # same map edges and trail

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCK_X = 1500.0
CLEAR = {c["name"]: c for c in LAYOUT["clearings"]}
CABINS = [(-6500, 13150, 5), (5000, 13000, -8), (7500, 12400, 15)]      # x, y, yaw (maya/lake_buildings.py)
BIG, SMALL = 200.0, 75.0                                                # half sizes of the patches


def shore_y(x):                                               # maya/make_lake.py's water edge
    return (14550 + 260 * math.sin(x / 1700.0) + 140 * math.sin(x / 630.0 + 1.0)
            + 150 * math.sin(x / 420.0 + 2.0) + 60 * math.sin(x / 190.0 + 0.5)
            + 260 * math.exp(-((x - DOCK_X) / 700.0) ** 2))


def ground_z(x, y):                                           # maya/make_lake.py's shore slope
    d = y - shore_y(x)
    if d < -320:
        return 0.0
    z = 1.0 - (d + 320) * 0.24 - 0.0006 * (d + 320) ** 2
    return max(-260.0, z + 6 * math.sin(x / 230.0) * math.sin(y / 170.0)) - 1.0


def local(x, y, cx, cy, yaw):
    a = math.radians(-yaw)
    dx, dy = x - cx, y - cy
    return dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)


def bare(x, y):
    """Is this point bare ground grass can grow on?"""
    if abs(x) > EDGE - 100 or y < -SOUTH + 100:
        return False
    if -5300 < y < -3890:                                     # road, shoulders, ditch, guardrail
        return False
    if -2540 < x < 4170 and -4060 < y < -1690:                # the lot and its end curbs
        return False
    if -2530 < x < 690 and -1710 < y < -680:                  # the motel (rooms, walkway, ICE machine)
        return False
    if 3030 < x < 3770 and -1770 < y < -830:                  # the office
        return False
    if near_trail(x, y, 140):                                 # the trail's dirt path
        return False
    if y - shore_y(x) > -190:                                 # the water (and the wet mud at its edge)
        return False
    s = CLEAR["shack"]                                        # the shack's floor and step
    lx, ly = local(x, y, s["x"], s["y"], 12)
    if abs(lx) < 235 and -205 < ly < 245:
        return False
    t = CLEAR["tower"]                                        # the tower's stairs
    if abs(x - t["x"]) < 170 and abs(y - t["y"]) < 245:
        return False
    for cx, cy, yaw in CABINS:                                # a cabin's floor, porch and steps
        lx, ly = local(x, y, cx, cy, yaw)
        if abs(lx) < 325 and -270 < ly < 515:
            return False
    if -3910 < x < -3090 and 13930 < y:                       # the boathouse (over the water)
        return False
    c = CLEAR["car"]                                          # inside the abandoned car
    if math.hypot(x - c["x"], y - c["y"]) < 250:
        return False
    return True


def fits(x, y, half):
    for dx, dy in ((0, 0), (half, half), (-half, half), (half, -half), (-half, -half),
                   (half, 0), (-half, 0), (0, half), (0, -half)):
        if not bare(x + dx, y + dy):
            return False
    return True


def shore_keep(x, y, rng):
    """Down the bank the grass thins out: all of it 7 m from the water, none at the water."""
    d = y - shore_y(x)
    if d < -700:
        return True
    f = (d + 190) / (-700 + 190.0)                            # 1 at -700 .. 0 at -190
    return rng.random() < f ** 1.5


def layout(seed=8):
    rng = random.Random(seed)
    out, big = [], []
    # 1. big patches on a 3.6 m grid (they overlap a little: no seams), on the flat only
    step = 360
    y = -SOUTH
    while y < 17000:
        x = -EDGE
        while x < EDGE:
            px, py = x + rng.uniform(-40, 40), y + rng.uniform(-40, 40)
            if py - shore_y(px) < -540 and fits(px, py, BIG):
                out.append({"mesh": rng.choice(("grass_dense_A", "grass_dense_B")), "x": round(px), "y": round(py),
                            "z": 0, "yaw": round(rng.uniform(0, 360), 1)})
                big.append((px, py))
            x += step
        y += step
    # 2. small patches in every gap: a 1.3 m grid, wherever a point isn't already under a big patch
    cell = 900
    grid = {}
    for px, py in big:
        grid.setdefault((int(px // cell), int(py // cell)), []).append((px, py))

    def covered(x, y):
        gx, gy = int(x // cell), int(y // cell)
        for i in (gx - 1, gx, gx + 1):
            for j in (gy - 1, gy, gy + 1):
                for px, py in grid.get((i, j), ()):
                    if (x - px) ** 2 + (y - py) ** 2 < 215 ** 2:   # inside a 4 m patch, whatever its turn
                        return True
        return False

    step = 130
    y = -SOUTH
    while y < 17000:
        x = -EDGE
        while x < EDGE:
            px, py = x + rng.uniform(-20, 20), y + rng.uniform(-20, 20)
            if not covered(px, py) and fits(px, py, SMALL) and shore_keep(px, py, rng):
                out.append({"mesh": rng.choice(("grass_small_A", "grass_small_B")), "x": round(px), "y": round(py),
                            "z": round(ground_z(px, py), 1), "yaw": round(rng.uniform(0, 360), 1)})
            x += step
        y += step
    return out


if __name__ == "__main__":
    items = layout()
    json.dump(items, open(os.path.join(ROOT, "export", "grass.json"), "w"))
    kinds = {}
    for it in items:
        kinds[it["mesh"]] = kinds.get(it["mesh"], 0) + 1
    print(len(items), "grass patches", kinds)

"""Where the grass grows (the patches from maya/make_grass.py): thick grass on the verges and the
road edges, in the yard behind the motel, along both sides of the trail and round the clearings,
and scattered tufts over the rest of the forest floor. Never on the road, the lot, the trail
itself, inside buildings, or below the lake shore.

Run with normal Python:  python tools/make_grass_layout.py
Writes export/grass.json: [{"mesh", "x", "y", "yaw"}]. unreal/grass.py places them.
"""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_fill import LAYOUT, EDGE, SOUTH, near_trail          # same map edges and trail as the forest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCK_X = 1500.0
CLEAR = {c["name"]: c for c in LAYOUT["clearings"]}
CABINS = [(-6500, 13150), (5000, 13000), (7500, 12400)]


def shore_y(x):                                               # maya/make_lake.py's water edge
    return (14550 + 260 * math.sin(x / 1700.0) + 140 * math.sin(x / 630.0 + 1.0)
            + 150 * math.sin(x / 420.0 + 2.0) + 60 * math.sin(x / 190.0 + 0.5)
            + 260 * math.exp(-((x - DOCK_X) / 700.0) ** 2))


def ground_ok(x, y, pad):
    """Bare ground a patch may cover (pad = the patch's half size, so its edges stay clear too)."""
    if abs(x) > EDGE - pad or y < -SOUTH + pad:
        return False
    if y > shore_y(x) - 340 - pad:                            # flat ground only, above the shore slope
        return False
    if -4955 - pad < y < -4045 + pad:                         # the road
        return False
    if -2920 - pad < x < 4170 + pad and -3520 - pad < y < -1690 + pad:      # the lot
        return False
    if -2520 - pad < x < 3770 + pad and -1760 - pad < y < -690 + pad:       # the motel and the office
        return False
    if near_trail(x, y, 150 + pad):                           # the trail's dirt path
        return False
    s = CLEAR["shack"]
    if math.hypot(x - s["x"], y - s["y"]) < 320 + pad:
        return False
    for cx, cy in CABINS:
        if math.hypot(x - cx, y - cy) < 420 + pad:
            return False
    if -4000 - pad < x < -3000 + pad and 13800 - pad < y:     # the boathouse
        return False
    return True


def dense_spot(x, y):
    """Where the grass grows thick."""
    if -4050 >= y >= -5300 or -4045 < y < -3520:              # road edges, the verge by the lot
        return True
    if -3700 < x < 4950 and -3520 <= y < 400:                 # verges beside the lot, the yard behind the motel
        return True
    if near_trail(x, y, 420):                                 # along the trail
        return True
    for c in LAYOUT["clearings"]:
        if math.hypot(x - c["x"], y - c["y"]) < c["r"] + 150:
            return True
    if shore_y(x) - 900 < y:                                  # the grassy bank above the lake
        return True
    return False


def layout(seed=8):
    rng = random.Random(seed)
    out = []
    # thick grass: a 3.5 m grid of 4 m patches (they overlap a little, no seams)
    step = 350
    y = -SOUTH
    while y < 17000:
        x = -EDGE
        while x < EDGE:
            px, py = x + rng.uniform(-40, 40), y + rng.uniform(-40, 40)
            if dense_spot(px, py) and ground_ok(px, py, 120):
                out.append({"mesh": rng.choice(("grass_dense_A", "grass_dense_B")), "x": round(px), "y": round(py),
                            "yaw": round(rng.uniform(0, 360), 1)})
            x += step
        y += step
    # the forest floor: 8 m patches of scattered tufts, every 7.5 m, where it isn't thick already
    step = 750
    y = -SOUTH
    while y < 17000:
        x = -EDGE
        while x < EDGE:
            px, py = x + rng.uniform(-80, 80), y + rng.uniform(-80, 80)
            if not dense_spot(px, py) and ground_ok(px, py, 200) and rng.random() < 0.85:
                out.append({"mesh": rng.choice(("grass_sparse_A", "grass_sparse_B")), "x": round(px), "y": round(py),
                            "yaw": round(rng.uniform(0, 360), 1)})
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

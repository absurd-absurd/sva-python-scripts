"""Where the grass grows (the patches from maya/make_grass.py): one even carpet over the forest
ground only. Never on the road, its shoulders or verges, the lot, the yard behind the motel, any
concrete, the trail itself, round the structures, or down the lake shore.

Run with normal Python:  python tools/make_grass_layout.py
Writes export/grass.json: [{"mesh", "x", "y", "yaw"}]. unreal/grass.py places them.
"""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_fill import LAYOUT, EDGE, SOUTH, near_trail, forest  # same map edges, trail and forest area

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCK_X = 1500.0
CLEAR = {c["name"]: c for c in LAYOUT["clearings"]}
CABINS = [(-6500, 13150), (5000, 13000), (7500, 12400)]


def shore_y(x):                                               # maya/make_lake.py's water edge
    return (14550 + 260 * math.sin(x / 1700.0) + 140 * math.sin(x / 630.0 + 1.0)
            + 150 * math.sin(x / 420.0 + 2.0) + 60 * math.sin(x / 190.0 + 0.5)
            + 260 * math.exp(-((x - DOCK_X) / 700.0) ** 2))


def ground_ok(x, y, pad):
    """Forest ground a patch may cover (pad = half the patch, so its edges stay clear too): only
    the forest (tools/make_fill.py forest()), never the road, lot, verges, yard or concrete, and
    not on the trail's path, round the structures or down the lake shore."""
    for dx, dy in ((0, 0), (pad, pad), (-pad, pad), (pad, -pad), (-pad, -pad)):
        if not forest(x + dx, y + dy):
            return False
    if y > shore_y(x) - 340 - pad:                            # flat ground only, above the shore slope
        return False
    if near_trail(x, y, 170 + pad):                           # the trail's dirt path
        return False
    s = CLEAR["shack"]
    if math.hypot(x - s["x"], y - s["y"]) < 330 + pad:
        return False
    t = CLEAR["tower"]
    if abs(x - t["x"]) < 280 + pad and abs(y - t["y"]) < 280 + pad:
        return False
    for cx, cy in CABINS:
        if math.hypot(x - cx, y - cy) < 430 + pad:
            return False
    if -4000 - pad < x < -3000 + pad and 13800 - pad < y:     # the boathouse
        return False
    return True


def layout(seed=8):
    """One even carpet over all the forest ground: 4 m patches on a 3.6 m grid (overlapping a
    little so there are no seams), alternating the two thick patch variants."""
    rng = random.Random(seed)
    out = []
    step = 360
    y = -SOUTH
    while y < 17000:
        x = -EDGE
        while x < EDGE:
            px, py = x + rng.uniform(-50, 50), y + rng.uniform(-50, 50)
            if ground_ok(px, py, 200):
                out.append({"mesh": rng.choice(("grass_dense_A", "grass_dense_B")), "x": round(px), "y": round(py),
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

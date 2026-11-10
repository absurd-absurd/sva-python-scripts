"""Fill the empty ground around the motel with forest, so wherever you run you're in the scene:
woods right up to the far side of the road, trees closing in on both sides of the motel and the
lot, and a band of forest down both outer edges of the map past the scattered woods.

Run with normal Python:  python tools/make_fill.py
Writes export/fill.json: [{"asset", "x", "y", "yaw", "scale"}, ...]. unreal/fill_forest.py places
them (and the invisible walls at the map's edges); tools/make_map.py draws the trees on the map.
Same seed = same forest. The scattered woods north of the motel (the Maya scatter tool, export/
scatter.json) are left alone: this only fills the ground outside them.
"""
import json
import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYOUT = json.load(open(os.path.join(ROOT, "layout.json")))
EDGE = 12000                     # the map's walls: x -EDGE..EDGE, y -SOUTH..
SOUTH = 9800
LAKE_Y = 13300                   # trees stop short of the lake shore

TREES = [("tree_pine_A", 5), ("tree_pine_B", 5), ("tree_leafy_A", 2), ("tree_leafy_B", 2),
         ("tree_dead_A", 1), ("tree_dead_B", 1), ("tree_dead_C", 1), ("tree_dead_pine", 1)]
UNDER = [("bush_A", 4), ("shrub_dead_A", 3), ("shrub_dead_B", 3), ("stump_A", 1), ("log_A", 1)]
ROCKS = [("rock_A", 1), ("rock_B", 1), ("rock_C", 1)]


def pick(rng, table):
    total = sum(w for _, w in table)
    r = rng.uniform(0, total)
    for name, w in table:
        r -= w
        if r <= 0:
            return name
    return table[-1][0]


def near_trail(x, y, clear):
    pts = LAYOUT["trail"]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / float(dx * dx + dy * dy)))
        if math.hypot(x - (ax + dx * t), y - (ay + dy * t)) < clear:
            return True
    return False


def forest(x, y):
    """Is this forest ground? Everything outside the road and its shoulders/ditch/guardrail, the
    lot and its verges, the motel, the office and the yard behind them, and the lake."""
    if abs(x) > EDGE - 150 or y < -SOUTH + 150 or y > LAKE_Y:
        return False
    if -5600 < y < -3800:                                   # road, shoulders, ditch, guardrail, power poles
        return False
    if -3700 < x < 5000 and -3800 <= y < 450:               # lot, verges, motel, office, back yard + fence
        return False
    return True


def allowed(x, y):
    """Where fill may go: forest ground, not on the trail, not inside the scattered woods
    (they're already full)."""
    if not forest(x, y):
        return False
    w = LAYOUT["woods"]
    if w["x_min"] <= x <= w["x_max"] and w["y_min"] <= y <= w["y_max"]:
        return False
    if near_trail(x, y, 320):
        return False
    return True


def fill(seed=19):
    rng = random.Random(seed)
    out = []
    cell = 300.0
    y = -SOUTH
    while y < LAKE_Y:
        x = -EDGE
        while x < EDGE:
            px, py = x + rng.uniform(30, cell - 30), y + rng.uniform(30, cell - 30)
            if allowed(px, py):
                r = rng.random()
                # thicker near the road and the motel (the edges you see), a bit thinner deep in
                near = min(abs(py + 5450), abs(abs(px) - 4800) if py > -3800 else 1e9)
                p_tree = 0.62 if near < 2500 else 0.5
                if r < p_tree:
                    out.append({"asset": pick(rng, TREES), "x": round(px), "y": round(py),
                                "yaw": round(rng.uniform(0, 360), 1), "scale": round(rng.uniform(0.75, 1.3), 2)})
                elif r < p_tree + 0.3:
                    out.append({"asset": pick(rng, UNDER), "x": round(px), "y": round(py),
                                "yaw": round(rng.uniform(0, 360), 1), "scale": round(rng.uniform(0.7, 1.4), 2)})
                elif r < p_tree + 0.36:
                    out.append({"asset": pick(rng, ROCKS), "x": round(px), "y": round(py),
                                "yaw": round(rng.uniform(0, 360), 1), "scale": round(rng.uniform(0.6, 1.6), 2)})
            x += cell
        y += cell
    return out


if __name__ == "__main__":
    items = fill()
    path = os.path.join(ROOT, "export", "fill.json")
    json.dump({"edge": EDGE, "south": SOUTH, "items": items}, open(path, "w"))
    kinds = {}
    for it in items:
        kinds[it["asset"]] = kinds.get(it["asset"], 0) + 1
    print(len(items), "pieces ->", path, kinds)

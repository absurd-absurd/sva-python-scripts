"""Where the forest floor pieces (maya/make_floor.py) lie:
- fallen-leaf and pine-needle patches all over the forest ground, thickest round the trees
  (needles under the pines, leaves under the others), each a little above the last so
  overlapping patches never flicker
- along both edges of the trail, patches half on the path and half off, so its edge is ragged
  and leaf-covered instead of a straight line, and the odd drift of leaves across the middle
- sticks, forked sticks, little bundles and the occasional big fallen branch (none on the trail)
- the lookout tower's view (tools/tower_view.py): every tree in it is cut, a sawn stump left in
  its place, brush piles and branches left lying about
Never inside the buildings, on the road, the lot, inside the fence or in the water (the same
bare-ground test as the grass).

Run with normal Python:  python tools/make_floor_layout.py
Writes export/floor.json: {"items": [{"mesh", "x", "y", "z", "yaw", "scale"}], "cut": [[x, y], ...]}
("cut" = the trees taken out for the view). unreal/forest_floor.py places it all.
"""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_fill import LAYOUT, EDGE, SOUTH, forest, near_trail
from make_grass_layout import bare, ground_z, shore_y
from tower_view import in_view

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIL = LAYOUT["trail"]
HALF = 130.0                                             # half the trail's width (unreal/blockout.py: 260)


def trees():
    """Every standing tree: (x, y, asset) from the scatter tool's woods and the forest fill."""
    out = []
    sc = json.load(open(os.path.join(ROOT, "export", "scatter.json")))
    for c in sc["copies"]:
        if c["asset"].startswith("tree_"):
            out.append((c["matrix"][12], c["matrix"][14], c["asset"]))
    for it in json.load(open(os.path.join(ROOT, "export", "fill.json")))["items"]:
        if it["asset"].startswith("tree_"):
            out.append((it["x"], it["y"], it["asset"]))
    return out


class Grid:
    """Nearest-tree lookups without checking all 2000 trees each time."""
    def __init__(self, pts, cell=800.0):
        self.cell, self.g = cell, {}
        for p in pts:
            self.g.setdefault((int(p[0] // cell), int(p[1] // cell)), []).append(p)

    def nearest(self, x, y):
        cx, cy = int(x // self.cell), int(y // self.cell)
        best, bd = None, 1e9
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for p in self.g.get((cx + i, cy + j), ()):
                    d = math.hypot(p[0] - x, p[1] - y)
                    if d < bd:
                        best, bd = p, d
        return best, bd


def floor_ok(x, y):
    """Forest ground a patch can lie on (not the trail itself, not the lake bank's bottom)."""
    return forest(x, y) and bare(x, y) and y < shore_y(x) - 260


class Layers:
    """Each patch gets its own height step, so two that overlap never sit at the same height."""
    def __init__(self):
        self.k = 0

    def z(self, x, y):
        self.k = (self.k + 1) % 7
        return round(ground_z(x, y) + 1.25 + 0.3 * self.k, 2)


def layout(seed=23):
    rng = random.Random(seed)
    standing = trees()
    cut = [(x, y) for x, y, a in standing if in_view(x, y)]
    grid = Grid([t for t in standing if not in_view(t[0], t[1])])
    lay = Layers()
    items = []

    def put(mesh, x, y, z=None, scale=1.0, yaw=None):
        items.append({"mesh": mesh, "x": round(x), "y": round(y),
                      "z": z if z is not None else round(ground_z(x, y), 2),
                      "yaw": round(rng.uniform(0, 360) if yaw is None else yaw, 1), "scale": round(scale, 2)})

    # 1. litter patches on a jittered 3.6 m grid, likelier near trees
    cell = 360.0
    y = -SOUTH
    while y < 15000:
        x = -EDGE
        while x < EDGE:
            px, py = x + rng.uniform(0, cell), y + rng.uniform(0, cell)
            if floor_ok(px, py):
                t, d = grid.nearest(px, py)
                chance = 0.9 if d < 500 else (0.7 if d < 900 else 0.45)
                if rng.random() < chance:
                    pine = t is not None and d < 700 and "pine" in t[2]
                    mesh = "litter_needles_A" if pine else rng.choice(("litter_leaves_A", "litter_leaves_B"))
                    put(mesh, px, py, lay.z(px, py), rng.uniform(0.8, 1.4))
            x += cell
        y += cell

    # 2. the trail's edges: patches straddling each edge every ~1 m, a few across the middle
    for (ax, ay), (bx, by) in zip(TRAIL, TRAIL[1:]):
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        nx, ny = -uy, ux
        s = 0.0
        while s < L:
            for side in (-1, 1):
                off = side * (HALF + rng.uniform(-35, 25))
                px, py = ax + ux * s + nx * off, ay + uy * s + ny * off
                if forest(px, py) and py < shore_y(px) - 260:
                    put("litter_leaves_B", px, py, lay.z(px, py) + 1.1, rng.uniform(0.5, 0.9))      # over the trail (top z 2)
            if rng.random() < 0.22:                       # leaves blown across the path
                off = rng.uniform(-60, 60)
                px, py = ax + ux * s + nx * off, ay + uy * s + ny * off
                if forest(px, py) and py < shore_y(px) - 260:
                    put("litter_leaves_B", px, py, lay.z(px, py) + 1.1, rng.uniform(0.3, 0.5))
            s += rng.uniform(70, 120)

    # 3. sticks and fallen branches (kept off the trail so you don't trip on the path)
    cell = 380.0
    y = -SOUTH
    while y < 15000:
        x = -EDGE
        while x < EDGE:
            px, py = x + rng.uniform(0, cell), y + rng.uniform(0, cell)
            if floor_ok(px, py) and not near_trail(px, py, 200) and rng.random() < 0.2:
                r = rng.random()
                mesh = "stick_A" if r < 0.4 else "stick_B" if r < 0.7 else "stick_C" if r < 0.9 else "branch_A"
                put(mesh, px, py, None, rng.uniform(0.8, 1.2))
            x += cell
        y += cell

    # 4. the tower's view: stumps where the trees stood, brush piles and branches left behind
    for x, y in cut:
        put("stump_cut", x, y, round(ground_z(x, y), 2), rng.uniform(0.85, 1.25))
    v = LAYOUT["tower_view"]
    for k in range(18):
        r = rng.uniform(700, 4200)
        a = math.radians(v["aim_deg"] + rng.uniform(-v["half_deg"], v["half_deg"]) * 0.9)
        px, py = v["x"] + math.cos(a) * r, v["y"] + math.sin(a) * r
        if not floor_ok(px, py) or near_trail(px, py, 380):
            continue
        mesh = "slash_pile" if k % 3 == 0 else "branch_A" if k % 3 == 1 else "stick_C"
        put(mesh, px, py, None, rng.uniform(0.8, 1.2))
    return items, cut


if __name__ == "__main__":
    items, cut = layout()
    path = os.path.join(ROOT, "export", "floor.json")
    json.dump({"items": items, "cut": [[round(x), round(y)] for x, y in cut]}, open(path, "w"))
    kinds = {}
    for it in items:
        kinds[it["mesh"]] = kinds.get(it["mesh"], 0) + 1
    print(len(items), "pieces,", len(cut), "trees cut for the tower view ->", path, kinds)

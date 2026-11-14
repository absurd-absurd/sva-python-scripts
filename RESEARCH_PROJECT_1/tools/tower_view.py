"""The lookout tower's view: a wedge of woods cut down between the tower and the lake (loggers
clear a lookout's sightline). layout.json "tower_view" says where it points and how wide it is.

in_view(x, y) -> True if a tree standing there would block the view. Used by
tools/make_floor_layout.py (stumps go where the trees were), tools/make_map.py (no tree marks
there) and unreal/forest_floor.py (takes those trees out of the level). Plain Python: also runs
inside Unreal.
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEW = json.load(open(os.path.join(ROOT, "layout.json")))["tower_view"]


def in_view(x, y, margin=None):
    m = VIEW["margin"] if margin is None else margin
    dx, dy = x - VIEW["x"], y - VIEW["y"]
    r = math.hypot(dx, dy)
    if r < 250:                                   # the tower itself
        return False
    a = math.atan2(dy, dx) - math.radians(VIEW["aim_deg"])
    a = (a + math.pi) % (2 * math.pi) - math.pi
    if abs(a) > math.pi / 2:                      # behind the tower
        return False
    # distance sideways from the wedge's edge line
    side = r * math.sin(abs(a) - math.radians(VIEW["half_deg"]))
    return abs(a) <= math.radians(VIEW["half_deg"]) or side < m

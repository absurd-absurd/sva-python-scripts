"""Build Black Hollow Lake in Maya and export it for Unreal: the shore sloping down into the
water, the water itself, low mist, the old dock (planks, pilings, bracing, a swim ladder, a red
lantern), the overlook railing where the trail comes out, the canoe tied up at the dock, rocks,
reeds and cattails, a fallen log.

Run with mayapy (or in Maya):
    exec(open(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/maya/make_lake.py").read())

Reuses the helpers of make_motel.py / room_props.py / exterior_props.py (box, tube, rsoft, frustum,
bevel_box, lathe, light, _shaped, ...). Positions are Unreal cm. Writes maya/lake_scene.ma,
export/set_lake.fbx and export/sets_lake.json (unreal/import_sets.py reads every sets*.json).
Materials: water_* = the lake water (M_PS2_Water), mist_* = drifting mist (M_PS2_Mist).
"""
import json
import math
import os
import random

import maya.cmds as cmds
import maya.mel as mel

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
_src = open(os.path.join(ROOT, "maya", "make_motel.py"), encoding="utf-8").read()
exec(_src[:_src.rindex("\nbuild()")])                   # helpers + MATS (and the furniture/exterior props)

WATER_Z = -45.0               # the lake surface
DOCK_X = 1500.0               # the trail ends here (layout.json)
DECK_Z = 16.0                 # low: you step straight onto it from the trail (ground is z 1)
LAKE_MATS = {
    "shore_mat": (0.3, 0.26, 0.2), "mud_wet_mat": (0.1, 0.085, 0.07), "lakebed_mat": (0.03, 0.03, 0.03),
    "water_lake_mat": (0.012, 0.016, 0.02), "mist_lake_mat": (0.32, 0.34, 0.37),
    "dock_wood_mat": (0.33, 0.3, 0.26), "dock_dark_mat": (0.12, 0.1, 0.08), "rope_mat": (0.38, 0.32, 0.22),
    "canoe_mat": (0.3, 0.05, 0.04), "canoe_inner_mat": (0.24, 0.18, 0.12), "reed_mat": (0.2, 0.22, 0.1),
    "cattail_mat": (0.2, 0.12, 0.06), "lantern_metal_mat": (0.08, 0.08, 0.08),
    "rock_mat": (0.3, 0.3, 0.28), "lantern_dim_mat": (0.16, 0.11, 0.06), "bark_mat": (0.2, 0.15, 0.1),        # same names as the woods props (textured alike)
}
rng_l = random.Random(77)


def shore_y(x):
    """Where the water's edge would be on flat ground: a wavy line, with a point of land jutting
    out at the dock so the trail ends on solid ground and steps straight onto the dock."""
    return (14550 + 260 * math.sin(x / 1700.0) + 140 * math.sin(x / 630.0 + 1.0)
            + 150 * math.sin(x / 420.0 + 2.0) + 60 * math.sin(x / 190.0 + 0.5)         # little coves and points
            + 260 * math.exp(-((x - DOCK_X) / 700.0) ** 2))


def ground_z(x, y):
    d = y - shore_y(x)
    if d < -320:
        return 1.0                                                   # 1 cm over the woods ground (no fighting)
    z = 1.0 - (d + 320) * 0.24 - 0.0006 * (d + 320) ** 2
    return max(-260.0, z + 6 * math.sin(x / 230.0) * math.sin(y / 170.0))


def shore():
    """The ground falling away into the lake: one subdivided sheet bent to ground_z, coloured by
    height (dry shore, wet mud near the waterline, dark lake bed below)."""
    x0, x1, y0, y1 = -13000, 13000, 13500, 17500
    nx, ny = 220, 80
    p = cmds.polyPlane(w=x1 - x0, h=y1 - y0, sx=nx, sy=ny, ch=False)[0]
    cmds.move((x0 + x1) / 2.0, 0, (y0 + y1) / 2.0, p)
    cmds.makeIdentity(p, apply=True, t=True)
    pts = [(x, ground_z(x, z), z) for x, y, z in _verts(p)]
    _set_verts(p, pts)
    cmds.polySoftEdge(p, angle=70, ch=False)
    material("shore_mat", LAKE_MATS["shore_mat"])
    keep(p, "shore_mat")
    wet, bed = [], []
    for f in range(cmds.polyEvaluate(p, face=True)):
        vs = cmds.polyInfo(f"{p}.f[{f}]", faceToVertex=True)[0].split()[2:]
        zs = [pts[int(v)][1] for v in vs]
        z = sum(zs) / len(zs)
        if z < WATER_Z - 40:
            bed.append(f"{p}.f[{f}]")
        elif z < WATER_Z + 22:
            wet.append(f"{p}.f[{f}]")
    if wet:
        cmds.sets(wet, edit=True, forceElement="mud_wet_matSG")
    if bed:
        cmds.sets(bed, edit=True, forceElement="lakebed_matSG")


def water_and_mist():
    """Returns its parts: they go in their own mesh with no collision (you walked on the mist)."""
    before = len(PARTS)
    p = cmds.polyPlane(w=40000, h=16000, sx=40, sy=16, ch=False)[0]
    cmds.move(0, WATER_Z, 14100 + 8000, p)
    keep(p, "water_lake_mat")
    for k, (z, cx, cy, w, h) in enumerate(((WATER_Z + 12, 1500, 16500, 9000, 4200), (WATER_Z + 45, -1500, 17500, 12000, 5000),
                                         (WATER_Z + 85, 3000, 18800, 14000, 6000), (WATER_Z + 25, -4500, 15800, 6000, 2600))):
        m = cmds.polyPlane(w=w, h=h, sx=1, sy=1, ch=False)[0]
        cmds.move(cx, z, cy, m)
        keep(m, "mist_lake_mat")
    fx = PARTS[before:]
    del PARTS[before:]
    return fx


def blockers(y0, y1):
    """Invisible walls (collision only): along the lake where the water gets knee deep, and around
    the dock, so you can walk onto the dock but not into the lake or off the dock's sides."""
    hw = 126
    out = []
    def wall(a, b, z0=-320, z1=320):
        (xa, ya), (xb, yb) = a, b
        L = math.hypot(xb - xa, yb - ya)
        c = cmds.polyCube(w=L + 20, h=z1 - z0, d=10, ch=False)[0]
        cmds.rotate(0, -math.degrees(math.atan2(yb - ya, xb - xa)), 0, c)
        cmds.move((xa + xb) / 2.0, (z0 + z1) / 2.0, (ya + yb) / 2.0, c)
        out.append(c)
    edge = lambda x: shore_y(x) - 112                                  # ground_z there = WATER_Z - 30
    xs = sorted(set(list(range(-13000, int(DOCK_X - hw), 200)) + [DOCK_X - hw, BH_X - BH_W - 4, BH_X + BH_W + 4]))
    pts = [(x, edge(x)) for x in xs]
    for a, b in zip(pts, pts[1:]):
        if a[0] >= BH_X - BH_W - 5 and b[0] <= BH_X + BH_W + 5:
            continue                                                  # the boathouse walls take over here
        wall(a, b)
    for s in (-1, 1):                                                 # keep you out of the boat slip
        wall((BH_X + s * (SLIP + 2), BH_Y - 150), (BH_X + s * (SLIP + 2), BH_Y + BH_N))
    wall((BH_X - SLIP, BH_Y - 152), (BH_X + SLIP, BH_Y - 152))
    xs = [DOCK_X + hw] + list(range(int(DOCK_X + hw) + 200, 13001, 200))
    pts = [(x, edge(x)) for x in xs]
    for a, b in zip(pts, pts[1:]):
        wall(a, b)
    for s in (-1, 1):                                                 # dock sides and end
        wall((DOCK_X + s * hw, edge(DOCK_X + s * hw)), (DOCK_X + s * hw, y1 + 30))
    wall((DOCK_X - hw, y1 + 30), (DOCK_X + hw, y1 + 30))
    return out


def plank(cx, cy, z, w, d, t, yaw=0, tilt=0, mat="dock_wood_mat"):
    rbevel(cx, cy, z, w, d, t, mat, r=0.6, yaw=yaw, tilt_x=tilt)


def dock():
    """The old dock: two stringers on pilings with cross bracing, planks across with gaps (a few
    missing, one broken and sagging), a swim ladder off the end, cleats, a coil of rope, and a red
    lantern on a post at the end."""
    y0 = shore_y(DOCK_X) - 330                                         # starts on dry ground, level with the trail
    y1 = y0 + 2200
    hw = 120
    # where the trail meets it: a timber sill and two worn boards bridging ground to deck
    bevel_box(DOCK_X - hw - 10, DOCK_X + hw + 10, y0 - 40, y0 + 4, -4, DECK_Z - 4, "dock_dark_mat", r=1.5)
    for k, yy in enumerate((y0 - 62, y0 - 44)):
        plank(DOCK_X + (k - 0.5) * 6, yy, 1.5 + k * 4, 2 * hw - 20, 17, 3.0, yaw=(k - 0.5) * 3, tilt=-6)
    for k in range(int((y1 - y0) / 300) + 1):                         # pilings
        py = y0 + 80 + k * 300
        for s in (-1, 1):
            frustum(DOCK_X + s * (hw - 6), py, ground_z(DOCK_X, py) - 30, DECK_Z + 8, 12, 11, "dock_dark_mat", sides=12)
        if k:
            for s in (-1, 1):                                         # cross bracing
                tube((DOCK_X + s * (hw - 6), py - 300, DECK_Z - 12), (DOCK_X + s * (hw - 6), py, WATER_Z + 5), 3.5,
                     "dock_dark_mat", sides=6)
            tube((DOCK_X - hw + 6, py, DECK_Z - 14), (DOCK_X + hw - 6, py, DECK_Z - 14), 4, "dock_dark_mat", sides=6)
    for s in (-1, 1):                                                 # stringers
        bevel_box(DOCK_X + s * (hw - 14) - 6, DOCK_X + s * (hw - 14) + 6, y0, y1, DECK_Z - 22, DECK_Z - 4, "dock_dark_mat", r=1.0)
    y = y0
    while y < y1 - 14:                                                # planks
        r = rng_l.random()
        w = 2 * hw + rng_l.uniform(-6, 6)
        if r < 0.035:
            pass                                                      # missing
        elif r < 0.05:
            plank(DOCK_X - 30, y + 7, DECK_Z - 6, w * 0.55, 15, 3.2, yaw=rng_l.uniform(-8, 8), tilt=-14)   # broken, sagging
        else:
            plank(DOCK_X + rng_l.uniform(-3, 3), y + 7, DECK_Z - 2 + rng_l.uniform(-0.6, 0.6), w, 15, 3.2,
                  yaw=rng_l.uniform(-1.2, 1.2), mat="dock_wood_mat" if rng_l.random() > 0.2 else "dock_dark_mat")
        y += 17
    for s in (-1, 1):                                                 # cleats
        for cy in (y0 + 700, y1 - 120):
            bevel_box(DOCK_X + s * (hw - 10) - 4, DOCK_X + s * (hw - 10) + 4, cy - 12, cy + 12, DECK_Z, DECK_Z + 5,
                      "lantern_metal_mat", r=1.2)
    for k in range(4):                                                # coiled rope
        ring(DOCK_X + 70, y1 - 260, DECK_Z + 1.6 + k * 1.5, 14 - k * 1.2, 1.2, "rope_mat", sides=20)
    # swim ladder off the end, into the water
    for s in (-1, 1):
        lx = DOCK_X + s * 22
        tube((lx, y1 + 4, DECK_Z + 70), (lx, y1 + 8, WATER_Z - 120), 2.2, "lantern_metal_mat", sides=10)
        tube((lx, y1 + 4, DECK_Z + 70), (lx, y1 - 18, DECK_Z + 74), 2.2, "lantern_metal_mat", sides=10)
    for k in range(6):
        zz = DECK_Z - 10 - k * 28
        tube((DOCK_X - 22, y1 + 5 + k * 0.6, zz), (DOCK_X + 22, y1 + 5 + k * 0.6, zz), 1.6, "lantern_metal_mat", sides=8)
    # the red lantern on a post at the end (red marks where something happened)
    lx, ly = DOCK_X - hw + 10, y1 - 25
    frustum(lx, ly, DECK_Z - 30, DECK_Z + 140, 6, 5, "dock_dark_mat", sides=10)
    tube((lx, ly, DECK_Z + 132), (lx + 30, ly, DECK_Z + 132), 2, "lantern_metal_mat", sides=8)
    lz = DECK_Z + 104
    frustum(lx + 30, ly, lz + 20, lz + 26, 7, 2, "lantern_metal_mat", sides=12)          # cap
    frustum(lx + 30, ly, lz - 2, lz + 20, 5.5, 5.5, "glow_lamp_red_mat", sides=12)      # glass
    for k in range(4):
        a = k * math.pi / 2
        tube((lx + 30 + math.cos(a) * 6, ly + math.sin(a) * 6, lz - 2), (lx + 30 + math.cos(a) * 6, ly + math.sin(a) * 6, lz + 20),
             0.5, "lantern_metal_mat", sides=4)
    frustum(lx + 30, ly, lz - 6, lz - 2, 7, 7, "lantern_metal_mat", sides=12)            # base
    tube((lx + 30, ly, lz + 26), (lx + 30, ly, DECK_Z + 132), 0.5, "lantern_metal_mat", sides=4)
    light("light_dock_lantern", lx + 30, ly, lz + 8, [1.0, 0.02, 0.0], 700, 1600)
    return y0, y1


def canoe(cx, cy, yaw_deg):
    """An old canvas canoe, faded red, floating by the dock: a shaped hull that sweeps up at both
    ends, a darker inside, gunwales, two thwarts and two cane seats, a paddle lying across."""
    L, W = 480.0, 86.0
    def hull(u):
        end = min(u, 1 - u)
        k = math.sin(math.pi * min(0.5, end) ) ** 0.7
        rise = 14 * max(0.0, (0.12 - end) / 0.12) ** 2
        return WATER_Z - 12, WATER_Z + 22 + rise, W / 2 * k * 0.55, W / 2 * k
    a = math.radians(yaw_deg)
    grp = []
    before = len(PARTS)
    open_hull(L, hull, "canoe_mat", "canoe_inner_mat", sx=10, sy=6, sz=40, thick=2.0)      # hollow
    def inner(u):
        b, t, w0, w1 = hull(u)
        return b + 4, t + 0.6, max(0.5, w0 - 3), max(0.5, w1 - 3)
    sole_plate(L, lambda u: (lambda b, t, w0, w1: (b + 2, t, max(0.5, w0 - 2), max(0.5, w1 - 2)))(*hull(u * 0.8 + 0.1)),
               WATER_Z + 1.5, "canoe_inner_mat", Ls=L * 0.8)
    for s in (-1, 1):
        pts = []
        for k in range(21):
            u = k / 20.0
            b, t, w0, w1 = hull(u)
            pts.append((s * w1, (u - 0.5) * L, t + 0.5))
        for p0, p1 in zip(pts, pts[1:]):
            tube(p0, p1, 1.6, "dock_wood_mat", sides=8)
    for u, h in ((0.32, 0), (0.5, 0), (0.68, 0), (0.2, -6), (0.82, -6)):
        b, t, w0, w1 = hull(u)
        tube((-w1 + 1, (u - 0.5) * L, t - 1 + h), (w1 - 1, (u - 0.5) * L, t - 1 + h), 1.4, "dock_wood_mat", sides=8)
    tube((-30, -60, WATER_Z + 12), (32, 90, WATER_Z + 13), 1.6, "dock_wood_mat", sides=8)       # paddle shaft
    rbevel(36, 104, WATER_Z + 13, 16, 40, 1.4, "dock_wood_mat", r=0.6, yaw=-22)
    new = PARTS[before:]
    g = cmds.group(new, name="canoe_grp")
    cmds.rotate(0, -yaw_deg, 0, g, pivot=(0, 0, 0))
    cmds.move(cx, 0, cy, g, relative=True)
    cmds.ungroup(g)
    # a mooring line from the bow to the dock cleat
    return


def reeds(cx, cy, n):
    for _ in range(n):
        x, y = cx + rng_l.uniform(-160, 160), cy + rng_l.uniform(-60, 60)
        z = ground_z(x, y)
        h = rng_l.uniform(80, 170)
        a = rng_l.uniform(0, 6.28)
        top = (x + math.cos(a) * h * 0.12, y + math.sin(a) * h * 0.12, z + h)
        tube((x, y, z - 5), top, 0.6, "reed_mat", sides=4)
        if rng_l.random() < 0.35:                                     # a cattail head
            frustum(top[0], top[1], top[2] - 22, top[2] - 6, 1.6, 1.6, "cattail_mat", sides=8)


def rocks():
    for _ in range(46):
        x = rng_l.uniform(-9000, 9000)
        y = shore_y(x) + rng_l.uniform(-350, 120)
        if abs(x - DOCK_X) < 200 or (abs(x - BH_X) < BH_W + 60 and BH_Y + BH_S - 60 < y < BH_Y + BH_N + 60):
            continue
        r = rng_l.uniform(18, 75)
        rsoft(x, y, ground_z(x, y) + r * 0.25, r * 2.2, r * 1.8, r * 1.1, "rock_mat", jitter=r * 0.12,
              smooth=2, seed=int(x), yaw=rng_l.uniform(0, 360))


def fallen_log(x, y):
    """A dead tree lying from the shore into the water, a few broken branches."""
    yaw = math.radians(70)
    a = (x, y, ground_z(x, y) + 18)
    b = (x + math.cos(yaw) * 900, y + math.sin(yaw) * 900, WATER_Z - 6)
    tube(a, b, 26, "bark_mat", sides=14)
    sphere(*a, 27, "bark_mat", sides=12, scale=(1, 1, 0.9))
    for k in range(5):
        t = 0.2 + k * 0.15
        p = tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
        q = (p[0] + rng_l.uniform(-120, 120), p[1] + rng_l.uniform(-60, 60), p[2] + rng_l.uniform(30, 110))
        tube(p, q, 5, "bark_mat", sides=6)


def overlook(x0, x1):
    """A wooden railing along the top of the shore where the trail comes out: posts following the
    water's edge, two split rails between them, a gap for the dock."""
    xs = [x for x in range(int(x0), int(x1) + 1, 220) if abs(x - DOCK_X) > 230] + [DOCK_X - 165, DOCK_X + 165]
    posts = [(x, shore_y(x) - 345, ground_z(x, shore_y(x) - 345)) for x in sorted(xs)]
    for (xa, ya, za), (xb, yb, zb) in zip(posts, posts[1:]):
        if xa < DOCK_X < xb:
            continue                                                  # the open way onto the dock
        for zz in (55, 100):
            tube((xa, ya, za + zz), (xb, yb, zb + zz), 3.5, "dock_wood_mat", sides=8)
    for (x, y, z) in posts:
        frustum(x, y, z - 10, z + 108, 6, 5, "dock_dark_mat", sides=8)


def rowboat(cx, cy, yaw_deg):
    """A small empty rowboat far out on the lake, drifting: wide plank hull, three seats, the oars
    still in their locks, one trailing in the water. Its lantern has all but gone out."""
    L, W = 340.0, 128.0
    def hull(u):
        end = min(u, 1 - u)
        k = math.sin(math.pi * min(0.5, end + (0.12 if u < 0.5 else 0.0))) ** 0.6   # squared-off stern
        rise = 10 * max(0.0, (0.15 - (1 - u)) / 0.15) ** 2
        return WATER_Z - 14, WATER_Z + 26 + rise, W / 2 * k * 0.5, W / 2 * k
    before = len(PARTS)
    open_hull(L, hull, "dock_dark_mat", "dock_wood_mat", sx=10, sy=6, sz=36, thick=2.5)    # hollow
    def inner(u):
        b, t, w0, w1 = hull(u)
        return b + 4, t + 0.6, max(0.5, w0 - 3), max(0.5, w1 - 3)
    sole_plate(L, lambda u: (lambda b, t, w0, w1: (b + 2.5, t, max(0.5, w0 - 2.5), max(0.5, w1 - 2.5)))(*hull(u * 0.96 + 0.02)),
               WATER_Z + 1.5, "dock_wood_mat", Ls=L * 0.96)
    for s_ in (-1, 1):
        pts = [(s_ * hull(k / 20.0)[3], (k / 20.0 - 0.5) * L, hull(k / 20.0)[1] + 0.5) for k in range(21)]
        for p0, p1 in zip(pts, pts[1:]):
            tube(p0, p1, 2.0, "dock_wood_mat", sides=8)
    for u in (0.22, 0.5, 0.78):                                       # seats
        b, t, w0, w1 = hull(u)
        rbevel(0, (u - 0.5) * L, t - 8, 2 * w1 - 6, 24, 3, "dock_wood_mat", r=0.6)
    b, t, w0, w1 = hull(0.55)
    for s_, (ex, ez) in ((-1, (-200, WATER_Z + 2)), (1, (150, t + 6))):     # oars: one trailing, one shipped
        tube((s_ * w1, 0.05 * L, t + 4), (s_ * w1 + s_ * abs(ex) * 0.9, 0.05 * L - 60 * s_, ez), 2.2, "dock_wood_mat", sides=8)
    lz = hull(0.78)[1] + 4                                            # lantern on the front seat
    frustum(0, 0.3 * L, lz, lz + 16, 4.5, 4.5, "lantern_dim_mat", sides=10)    # gone out (almost)
    frustum(0, 0.3 * L, lz + 16, lz + 21, 6, 1.5, "lantern_metal_mat", sides=10)
    new = PARTS[before:]
    g = cmds.group(new, name="rowboat_grp")
    cmds.rotate(0, -yaw_deg, 0, g, pivot=(0, 0, 0))
    cmds.move(cx, 0, cy, g, relative=True)
    cmds.ungroup(g)
    a = math.radians(yaw_deg)
    ly = 0.3 * L
    light("light_rowboat", cx - math.sin(a) * ly, cy + math.cos(a) * ly, lz + 10, [1.0, 0.72, 0.42], 0.3, 300)      # basically out: even 3 left a bright streak on the water


exec(open(os.path.join(ROOT, "maya", "lake_buildings.py"), encoding="utf-8").read())


def build():
    del PARTS[:]
    del ROOM_PARTS[:]
    cmds.file(new=True, force=True)
    for name, rgb in list(MATS.items()) + list(LAKE_MATS.items()):
        material(name, rgb)
    shore()
    fx = water_and_mist()
    y0, y1 = dock()
    canoe(DOCK_X + 190, y1 - 420, 8)
    rowboat(-900, 20200, 35)
    tube((DOCK_X + 120, y1 - 120, DECK_Z + 3), (DOCK_X + 175, y1 - 190, WATER_Z + 20), 0.9, "rope_mat", sides=6)   # mooring line
    lake_buildings()
    for cx in (-6000, -4700, -1200, 300, 2800, 4400, 6900):
        reeds(cx, shore_y(cx) - 60, 26)
    rocks()
    fallen_log(-2200, shore_y(-2200) - 280)
    overlook(DOCK_X - 900, DOCK_X + 900)
    lake = cmds.polyUnite(PARTS, name="set_lake", constructionHistory=False)[0]
    cmds.delete(lake, constructionHistory=True)
    cmds.xform(lake, pivots=(0, 0, 0), worldSpace=True)
    extra = {}
    for name, parts in (("set_lake_rooms", list(ROOM_PARTS)), ("set_lake_fx", fx), ("set_lake_block", blockers(y0, y1))):
        m = cmds.polyUnite(parts, name=name, constructionHistory=False)[0] if len(parts) > 1 else cmds.rename(parts[0], name)
        cmds.delete(m, constructionHistory=True)
        cmds.xform(m, pivots=(0, 0, 0), worldSpace=True)
        if name.endswith("_block"):
            material("lake_block_mat", (1, 0, 1))
            cmds.sets(m, edit=True, forceElement="lake_block_matSG")
        extra[name] = m
    lights = cmds.ls("light_*", type="transform")
    cmds.file(rename=os.path.join(ROOT, "maya", "lake_scene.ma"))
    cmds.file(save=True, type="mayaAscii")
    if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
        cmds.loadPlugin("fbxmaya")
    fbx = os.path.join(OUT, "set_lake.fbx").replace("\\", "/")
    sets = {}
    used = set()
    for name, m in [("set_lake", lake)] + list(extra.items()):
        f = os.path.join(OUT, name + ".fbx").replace("\\", "/")
        cmds.select(m)
        mel.eval("FBXResetExport")
        mel.eval('FBXExport -f "{}" -s'.format(f))
        sets[name] = f
        for sg in cmds.listConnections(cmds.listRelatives(m, shapes=True), type="shadingEngine") or []:
            used.update(cmds.listConnections(sg + ".surfaceShader") or [])
    props = export_building_doors()
    data = {"sets": sets, "room_sets": ["set_lake_rooms"], "props": props,
            "materials": {m: list(cmds.getAttr(m + ".color")[0]) for m in sorted(used)},
            "lights": [dict(json.loads(cmds.getAttr(l + ".ue_light")), name=l,
                            position=[cmds.xform(l, q=True, t=True, ws=True)[i] for i in (0, 2, 1)]) for l in lights],
            "dock": {"x": DOCK_X, "y0": y0, "y1": y1, "deck_z": DECK_Z}, "water_z": WATER_Z}
    for mt in list(BLD_MATS) + ["metal_mat", "brass_mat", "chrome_mat"]:
        data["materials"].setdefault(mt, list(cmds.getAttr(mt + ".color")[0]))
    data["doors"] = DOORS
    json.dump(data, open(os.path.join(OUT, "sets_lake.json"), "w"), indent=1)
    print(f"Lake built: {cmds.polyEvaluate(lake, triangle=True)} triangles, dock y {y0:.0f}..{y1:.0f}")


build()

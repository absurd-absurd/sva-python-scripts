"""MARROW Chapter 2: build the bottom of Black Hollow Lake in Maya and export it for Unreal.

Run with mayapy (or in Maya's Script Editor, Python tab):
    exec(open(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_2/maya/make_lakebed.py").read())

What it makes (positions are Unreal cm, Z up, like Chapter 1):
  - the lakebed: one sheet bent into a winding gully that starts in the shallows under the dock
    (about 3-4 m down) and sinks north to a drop-off and the deep basin (about 24 m down).
    Steep silt banks on both sides keep you in the gully.
  - the old dock's pilings coming down through the surface, a rope, the swim ladder
  - the underside of the lake surface (seen from below, only near the dock; the murk hides the rest)
  - sunken red lanterns along the gully, still glowing: the lure trail
  - scatter props (rocks, boulders, pondweed, sunken branches), scattered over the lakebed with
    the MIDTERM scatter tool (its own build_all, called with settings instead of the window)

Writes to RESEARCH_PROJECT_2/:
  maya/lakebed_scene.ma
  export/set_lakebed*.fbx + export/sets_lakebed.json   (the set, read by unreal/lakebed_level.py)
  export/<prop>.fbx + export/scatter.json             (the scatter, same format as Chapter 1)
"""
import json
import math
import os
import random

import maya.cmds as cmds
import maya.mel as mel

RP1 = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
RP2 = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_2"
SCATTER_TOOL = r"C:/Users/fayth/sva-python-scripts/MIDTERM/scatter_tool.py"

ROOT = RP1
_src = open(os.path.join(RP1, "maya", "make_motel.py"), encoding="utf-8").read()
exec(_src[:_src.rindex("\nbuild()")])          # Chapter 1 helpers: box, tube, rsoft, frustum, sphere, light, red_lantern...
OUT = os.path.join(RP2, "export")              # (make_motel set OUT to Chapter 1's folder)

SURFACE_Z = 0.0          # the lake surface, overhead at the start
START_Y = -1900          # where Cas lands, under the end of the dock
BED_MATS = {
    "lakebed_mat": (0.05, 0.05, 0.045), "mud_wet_mat": (0.09, 0.08, 0.065), "rock_mat": (0.22, 0.23, 0.21),
    "bark_mat": (0.13, 0.1, 0.07), "bark_dark_mat": (0.07, 0.06, 0.05), "weed_mat": (0.09, 0.12, 0.05),
    "weed_brown_mat": (0.12, 0.1, 0.05), "slime_mat": (0.06, 0.08, 0.04), "rope_mat": (0.3, 0.25, 0.17),
    "under_surface_mat": (0.02, 0.05, 0.05), "ladder_metal_mat": (0.14, 0.13, 0.12),
    "rusty_tool_mat": (0.2, 0.11, 0.07), "seeglass_red_mat": (0.6, 0.05, 0.03),      # red_lantern() (as in lake_buildings.py)
    # the ground (blended in Unreal: unreal/lakebed_level.py ground_material())
    "lb_ground_mat": (0.3, 0.28, 0.24),
    "fish_body_mat": (0.42, 0.42, 0.34), "fish_back_mat": (0.12, 0.14, 0.09), "fish_fin_mat": (0.3, 0.22, 0.12),
    "fish_eye_mat": (0.02, 0.02, 0.02), "bubble_mat": (0.95, 1.0, 1.0), "lb_litter_mat": (0.2, 0.15, 0.1),
}
rng = random.Random(2001)


# ---------- the shape of the lakebed ----------

def path_x(y):
    """The middle of the gully: it winds left and right as it goes north."""
    return 1400 * math.sin(y / 3200.0) + 600 * math.sin(y / 1100.0 + 1.0)


# depth along the gully: (y, z). Shallows by the dock, a long slope, the drop-off, the deep basin.
# (2026-11-24: 5 m deeper than the first pass, the user found it shallow: ~8.5 m at the start, ~30 m in the basin)
DEPTH = [(-2600, -500), (-1500, -830), (0, -900), (3000, -1100), (6000, -1350), (9000, -1500),
         (11000, -1650), (12500, -2550), (14000, -2850), (18000, -2950)]


def floor_z(y):
    for (ya, za), (yb, zb) in zip(DEPTH, DEPTH[1:]):
        if y <= yb:
            t = max(0.0, (y - ya) / (yb - ya))
            t = t * t * (3 - 2 * t)                       # smooth: no creases where the slope changes
            return za + (zb - za) * t
    return DEPTH[-1][1]


def half_width(y):
    """How wide the walkable gully floor is: 9-15 m, opening into a wide basin past the drop-off."""
    w = 900 + 600 * math.sin(y / 2300.0) ** 2
    if y > 12000:
        w += min(1.0, (y - 12000) / 1500.0) * 2200
    return w


TOE = 700.0        # how far the floor takes to curve up into a bank (no crease where they meet)
STEEP = 1.25       # how steep the bank gets past the toe (~51 degrees: too steep to climb)


def edge_w(y, side):
    """Distance from the middle of the gully to the foot of the bank on one side (+1 / -1).
    It wanders in and out on each side on its own, instead of running parallel to the path."""
    return half_width(y) + 220 * math.sin(y / 640.0 + side * 2.1) + 90 * math.sin(y / 230.0 + side)


def edge(x, y):
    """How far past the edge of the gully floor (x, y) is (0 or less = on the floor)."""
    side = 1.0 if x > path_x(y) else -1.0
    return abs(x - path_x(y)) - edge_w(y, side), side


def bank_rise(e):
    """The floor curves up into the bank: the slope grows smoothly from 0 over TOE cm, then the
    bank keeps rising (and steepens a little higher up)."""
    if e <= 0:
        return 0.0
    if e < TOE:
        return STEEP * e * e / (2 * TOE)
    return STEEP * TOE / 2 + STEEP * (e - TOE) + 0.0004 * (e - TOE) ** 2


def bed_z(x, y):
    e, side = edge(x, y)
    z = floor_z(y) + min(bank_rise(e), 2600.0)
    if e > 0:
        # the banks are worn into gullies and spurs running down the slope, softly at the toe
        g = min(1.0, e / 900.0)
        z += g * (70 * math.sin(y / 190.0 + side * 1.7) + 35 * math.sin(y / 83.0 + x / 400.0))
        # slumped silt at the foot of the bank: low humps
        if e < TOE * 1.3:
            z += 22 * math.sin(math.pi * e / (TOE * 1.3)) * (0.5 + 0.5 * math.sin(y / 170.0 + x / 260.0))
    z += 18 * math.sin(x / 260.0) * math.sin(y / 210.0) + 9 * math.sin(x / 377.0 + y / 313.0)   # sand ripples
    for mx, my, r, h in MOUNDS:                           # silt mounds on the floor
        d2 = ((x - mx) ** 2 + (y - my) ** 2) / (r * r)
        if d2 < 4:
            z += h * math.exp(-d2)
    return z


MOUNDS = []
for _ in range(40):
    _y = rng.uniform(-1000, 17000)
    MOUNDS.append((path_x(_y) + rng.uniform(-0.8, 0.8) * half_width(_y), _y, rng.uniform(150, 450), rng.uniform(15, 60)))


def lakebed():
    x0, x1, y0, y1 = -7500, 7500, -2600, 18000
    nx, ny = 150, 206                                     # ~1 m squares
    p = cmds.polyPlane(w=x1 - x0, h=y1 - y0, sx=nx, sy=ny, ch=False, name="lakebed_floor")[0]
    cmds.move((x0 + x1) / 2.0, 0, (y0 + y1) / 2.0, p)
    cmds.makeIdentity(p, apply=True, t=True)
    pts = [(x, bed_z(x, z), z) for x, _, z in _verts(p)]
    _set_verts(p, pts)
    cmds.polySoftEdge(p, angle=180, ch=False)             # smooth shading all over: no facets on the banks
    # one material: Unreal's M_Ch2_Ground blends sand (flat), silt (the toe) and clay (steep banks)
    # by slope in the shader, so there are no hard face edges between them
    keep(p, "lb_ground_mat")
    return p


def angular(cx, cy, cz, sx, sy, sz, mat, seed, yaw=0.0, tilt=0.0, chips=6):
    """A rock with flat broken faces and sharp edges (not a soft lump): a rough ball, chipped
    flat by a few random planes, then stretched to sx * sy * sz (Unreal cm, centred on cx, cy, cz).
    The bottom is flattened so it sits in the silt. Returns the mesh (already kept)."""
    r = random.Random(seed)
    m = cmds.polySphere(r=1, sx=10, sy=7, ch=False)[0]
    pts = []
    for x, y, z in _verts(m):
        k = 1.0 + r.uniform(-0.12, 0.12)
        pts.append([x * k, y * k, z * k])
    for _ in range(chips):                                # chip off flat faces
        a, b = r.uniform(0, 6.283), r.uniform(-0.6, 1.2)
        n = (math.cos(a) * math.cos(b), math.sin(b), math.sin(a) * math.cos(b))
        d = r.uniform(0.55, 0.85)
        for q in pts:
            t = q[0] * n[0] + q[1] * n[1] + q[2] * n[2]
            if t > d:
                for i in range(3):
                    q[i] -= (t - d) * n[i]
    for q in pts:
        q[1] = max(q[1], -0.45)                           # flat underside
    _set_verts(m, [tuple(q) for q in pts])
    cmds.scale(sx / 2.0, sz / 2.0, sy / 2.0, m)
    cmds.rotate(tilt, yaw, r.uniform(-tilt, tilt), m)
    cmds.move(cx, cz, cy, m)
    cmds.makeIdentity(m, apply=True, t=True, r=True, s=True)
    cmds.polySoftEdge(m, angle=35, ch=False)              # hard edges between the chipped faces
    return keep(m, mat)


def wall_ledges():
    """Slabs of harder rock sticking out of the banks (the water wore the clay away around them):
    long, flat and broken-edged, sunk half into the wall, tilted a little like the bedding.
    They use the ground material, so their tops collect silt and their faces show rock."""
    r = random.Random(51)
    n = 0
    for side in (-1.0, 1.0):
        y = -1800.0
        while y < 17600:
            y += r.uniform(300, 700)
            e = r.uniform(TOE + 100, TOE + 1900)
            x = path_x(y) + side * (edge_w(y, side) + e)
            z = bed_z(x, y)
            length, depth, height = r.uniform(240, 600), r.uniform(150, 260), r.uniform(35, 90)
            angular(x + side * depth * 0.15, y, z, depth, length, height, "lb_ground_mat",
                    seed=int(y) * 3 + int(side), yaw=r.uniform(-10, 10), tilt=r.uniform(-6, 6), chips=8)
            n += 1
            if r.random() < 0.35:                      # a thinner slab stepped above it
                x2 = x + side * 190
                angular(x2, y + 60, bed_z(x2, y + 60), depth * 0.7, length * 0.6, height * 0.7, "lb_ground_mat",
                        seed=int(y) + 99, yaw=r.uniform(-10, 10), tilt=r.uniform(-6, 6), chips=8)
                n += 1
    return n


def rubble():
    """Broken rock that fell off the walls and piled up at their foot (the toe), bigger pieces
    nearer the wall. Same ground material: silt settles on top."""
    r = random.Random(52)
    n = 0
    for side in (-1.0, 1.0):
        y = -2000.0
        while y < 17800:
            y += r.uniform(90, 260)
            e = TOE * r.uniform(0.15, 1.1)
            x = path_x(y) + side * (edge_w(y, side) + e)
            size = r.uniform(25, 90) * (0.5 + e / TOE)
            angular(x, y, bed_z(x, y) - size * 0.12, size * r.uniform(0.9, 1.4), size * r.uniform(0.8, 1.3),
                    size * r.uniform(0.45, 0.75), "lb_ground_mat", seed=n + 7000, yaw=r.uniform(0, 360),
                    tilt=r.uniform(0, 25), chips=r.randint(4, 7))
            n += 1
    return n


def sunken_trees():
    """Whole dead trees that fell in long ago and sank: thick waterlogged trunks lying on the bed,
    a root plate at one end, broken branch stubs, half buried in the silt."""
    r = random.Random(53)
    spots = [(-600, 1), (2300, -1), (5200, 1), (7900, -1), (10300, 1), (13300, -1), (15200, 1), (16800, -1)]
    for y, side in spots:
        x = path_x(y) + side * r.uniform(200, 700)
        length, rad = r.uniform(700, 1200), r.uniform(18, 30)
        yaw = math.radians(r.uniform(-50, 50) + (90 if r.random() < 0.5 else 0))
        dx, dy = math.cos(yaw) * length / 2, math.sin(yaw) * length / 2
        a = (x - dx, y - dy, bed_z(x - dx, y - dy) + rad * 0.5)
        b = (x + dx, y + dy, bed_z(x + dx, y + dy) + rad * 0.35)
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, max(a[2], b[2], bed_z(x, y) + rad * 0.4))
        tube(a, mid, rad, "bark_dark_mat", sides=12)
        tube(mid, b, rad * 0.75, "bark_dark_mat", sides=12)
        tube(b, (b[0] + dx * 0.12, b[1] + dy * 0.12, b[2] - 4), rad * 0.4, "bark_dark_mat", sides=8)   # snapped top
        ux, uy = -math.cos(yaw), -math.sin(yaw)               # root plate at the thick end
        for k in range(9):
            ang = k * 6.283 / 9 + r.uniform(-0.2, 0.2)
            px, py = -uy * math.cos(ang), ux * math.cos(ang)
            tip = (a[0] + px * rad * 3.2 + ux * 25, a[1] + py * rad * 3.2 + uy * 25, a[2] + math.sin(ang) * rad * 2.6)
            tube(a, (tip[0], tip[1], max(tip[2], bed_z(tip[0], tip[1]) - 5)), rad * 0.22, "bark_dark_mat", sides=5)
        for k in range(6):                                    # broken branch stubs
            t = r.uniform(0.2, 0.85)
            p0 = tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
            ang = r.uniform(0.3, 2.8) * (1 if r.random() < 0.5 else -1)
            L = r.uniform(40, 140)
            q = (p0[0] - uy * math.cos(ang) * L, p0[1] + ux * math.cos(ang) * L, p0[2] + abs(math.sin(ang)) * r.uniform(30, 120))
            tube(p0, q, rad * r.uniform(0.15, 0.3), "bark_dark_mat", sides=6)
    return len(spots)


# ---------- the dock from below ----------

def dock_from_below():
    """Pilings in two rows down through the surface, cross-bracing, the ladder and a rope."""
    dx = path_x(START_Y)
    for y in range(-2500, -1100, 300):
        for s in (-1, 1):
            x = dx + s * 120 + rng.uniform(-6, 6)
            z0 = bed_z(x, y) - 30
            tube((x, y, z0), (x + rng.uniform(-8, 8), y, SURFACE_Z + 60), 13, "bark_dark_mat", sides=10)
            tube((x, y, z0 + 10), (x, y, z0 + 70 + rng.uniform(0, 60)), 14.2, "slime_mat", sides=10)   # weed slime at the foot
        x = dx
        tube((x - 120, y, SURFACE_Z - 35), (x + 120, y, SURFACE_Z - 70), 5, "bark_dark_mat", sides=6)   # bracing, up by the surface (lower, it hit your head)
    lx, ly = dx + 60, -1250                                                                         # the swim ladder
    for s in (-1, 1):
        tube((lx + s * 25, ly, bed_z(lx, ly) + 40), (lx + s * 25, ly, SURFACE_Z + 40), 2, "ladder_metal_mat", sides=8)
    for k in range(int((SURFACE_Z - bed_z(lx, ly)) / 30) - 1):    # rungs all the way down
        z = SURFACE_Z - 20 - k * 30
        tube((lx - 25, ly, z), (lx + 25, ly, z), 1.6, "ladder_metal_mat", sides=8)
    a = (dx - 100, -1600, SURFACE_Z - 5)                                                           # a mooring rope hanging down
    b = (dx - 140, -1640, bed_z(dx - 140, -1640) + 10)
    mid = ((a[0] + b[0]) / 2 + 20, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
    tube(a, mid, 1.2, "rope_mat", sides=6)
    tube(mid, b, 1.2, "rope_mat", sides=6)


def surface_underside():
    """The lake surface seen from below, near the dock. Flipped so it faces down."""
    before = len(PARTS)
    p = cmds.polyPlane(w=9000, h=8000, sx=30, sy=26, ch=False)[0]
    cmds.move(path_x(START_Y), SURFACE_Z, 400, p)
    cmds.polyNormal(p, normalMode=0, ch=False)
    keep(p, "under_surface_mat")
    fx = PARTS[before:]
    del PARTS[before:]
    return fx


# ---------- the lure trail ----------

def sunken_lanterns():
    """Red lanterns sunk along the gully, still lit. They lead you down. Some stand in the silt,
    some lie on their side; each one a little further, a little brighter."""
    spots = []
    y = 900
    while y < 15500:
        side = rng.choice((-1, 1))
        x = path_x(y) + side * rng.uniform(200, half_width(y) * 0.6)
        spots.append((x, y))
        y += rng.uniform(1400, 2000)
    for k, (x, y) in enumerate(spots):
        z = bed_z(x, y) - 3                               # sunk a little into the silt
        red_lantern(x, y, z)
        frustum(x, y, z + 6, z + 20, 3.2, 3.2, "glow_lamp_red_mat", sides=10)    # the glow inside the red glass
        t = k / max(1, len(spots) - 1)
        light("light_sunken_lantern_%d" % k, x, y, z + 30, [1.0, 0.06, 0.02], 25 + 55 * t, 700 + 500 * t)
    return spots


def specks():
    """Silt hanging in the water: tiny flecks filling the gully from the floor to ~7 m up.
    (They can't follow the camera: Unreal's Python can't wire World Position Offset.)"""
    r = random.Random(54)
    parts = []
    while len(parts) < 12000:
        y = r.uniform(-2500, 17800)
        side = r.choice((-1.0, 1.0))
        x = path_x(y) + side * r.uniform(0, edge_w(y, side) + TOE)
        z0 = bed_z(x, y)
        z = r.uniform(z0 + 10, min(z0 + 700, SURFACE_Z - 40))
        if z <= z0 + 10:
            continue
        sz = r.uniform(1.5, 4.0) if r.random() < 0.8 else r.uniform(4.0, 7.0)    # flakes of silt, a few clumps
        c = cmds.polyCube(w=sz, h=sz * r.uniform(0.15, 0.35), d=sz * r.uniform(0.5, 1.0), ch=False)[0]
        cmds.rotate(r.uniform(0, 180), r.uniform(0, 180), r.uniform(0, 180), c)
        cmds.move(x, z, y, c)
        parts.append(c)
    m = cmds.polyUnite(parts, name="set_lakebed_specks", constructionHistory=False)[0]
    cmds.delete(m, constructionHistory=True)
    cmds.xform(m, pivots=(0, 0, 0), worldSpace=True)
    material("specks_mat", (0.2, 0.2, 0.17))      # muted grey-brown silt, close to the water
    cmds.sets(m, edit=True, forceElement="specks_matSG")
    return m


def light_shafts():
    """Shafts of light slanting down from the surface in the shallows (they fade out deeper):
    long open cones, wide at the top; M_Ch2_Shaft makes them a faint, soft, shifting glow."""
    r = random.Random(55)
    parts = []
    y = -2400.0
    while y < 7000:
        y += r.uniform(500, 1100)
        x = path_x(y) + r.uniform(-900, 900)
        top = SURFACE_Z - 5
        L = r.uniform(800, 1300)
        rad = r.uniform(60, 160)
        c = cmds.polyCone(r=rad, h=L, sx=14, sy=4, ch=False)[0]
        cmds.delete(c + ".f[%d]" % (cmds.polyEvaluate(c, face=True) - 1))   # open: no base cap
        cmds.move(0, -L / 2.0, 0, c)                    # tip at the origin, then flip: wide end up
        cmds.makeIdentity(c, apply=True, t=True)
        cmds.rotate(180 + r.uniform(-14, 14), 0, r.uniform(-14, 14), c)
        cmds.move(x, top - L, y, c)
        parts.append(c)
    m = cmds.polyUnite(parts, name="set_lakebed_shafts", constructionHistory=False)[0]
    cmds.delete(m, constructionHistory=True)
    cmds.xform(m, pivots=(0, 0, 0), worldSpace=True)
    material("shaft_mat", (0.5, 0.8, 0.7))
    cmds.sets(m, edit=True, forceElement="shaft_matSG")
    return m


def blockers():
    """Invisible walls round the edge of the map, and a lid just under the surface by the dock."""
    out = []
    def wall(x0, x1, y0, y1, z0, z1):
        c = cmds.polyCube(w=x1 - x0, h=z1 - z0, d=y1 - y0, ch=False)[0]
        cmds.move((x0 + x1) / 2.0, (z0 + z1) / 2.0, (y0 + y1) / 2.0, c)
        out.append(c)
    wall(-7600, 7600, -2700, -2600, -3000, 300)
    wall(-7600, 7600, 18000, 18100, -3000, 300)
    wall(-7600, -7500, -2600, 18000, -3000, 300)
    wall(7500, 7600, -2600, 18000, -3000, 300)
    wall(-7500, 7500, -2600, 18000, SURFACE_Z - 30, SURFACE_Z - 10)     # can't swim up and out (lower than this blocked the start)
    return out


# ---------- scatter props (sources for the scatter tool) ----------

def make_prop(name, build):
    """Run build() (which adds parts at the origin), combine its parts into one tagged mesh."""
    before = len(PARTS)
    build()
    parts = PARTS[before:]
    del PARTS[before:]
    m = cmds.polyUnite(parts, name=name, constructionHistory=False)[0] if len(parts) > 1 else cmds.rename(parts[0], name)
    cmds.delete(m, constructionHistory=True)
    cmds.xform(m, pivots=(0, 0, 0), worldSpace=True)
    cmds.addAttr(m, longName="ue_asset", dataType="string")
    cmds.setAttr(m + ".ue_asset", name, type="string")
    return m


def rock(seed, sx, sy, sz):
    def build():
        angular(0, 0, sz * 0.35, sx, sy, sz, "lb_ground_mat", seed=seed, chips=7)
    return build


def milfoil(seed, stems, h0, h1):
    """Water milfoil: thin stems with whorls of short feathery leaves all the way up."""
    def build():
        r = random.Random(seed)
        for _ in range(stems):
            x, y = r.uniform(-10, 10), r.uniform(-10, 10)
            h = r.uniform(h0, h1)
            lean = (r.uniform(-0.25, 0.25), r.uniform(-0.25, 0.25))
            top = (x + lean[0] * h, y + lean[1] * h, h)
            tube((x, y, -2), top, 0.7, "weed_mat", sides=3)
            k = 7.0
            while k < h:
                t = k / h
                c = (x + (top[0] - x) * t, y + (top[1] - y) * t, k)
                L = 7 * (1.1 - t * 0.6)
                for j in range(4):
                    a = j * 1.571 + k * 0.4
                    tube(c, (c[0] + math.cos(a) * L, c[1] + math.sin(a) * L, c[2] + L * 0.5), 0.45, "weed_mat", sides=3)
                k += r.uniform(6, 9)
    return build


def tuft(seed, blades, h0, h1):
    """A low tuft of stonewort/grass-like weed: the carpet in the shallows."""
    def build():
        r = random.Random(seed)
        for _ in range(blades):
            a = r.uniform(0, 6.283)
            d = r.uniform(0, 14)
            x, y = math.cos(a) * d, math.sin(a) * d
            h = r.uniform(h0, h1)
            tube((x, y, -2), (x + math.cos(a) * h * 0.35, y + math.sin(a) * h * 0.35, h), 0.6, "weed_brown_mat", sides=3)
    return build


def litter(seed, size):
    """A patch of sunken dead leaves: a thin, slightly domed mat with a ragged edge."""
    def build():
        r = random.Random(seed)
        m = cmds.polyCylinder(r=size / 2.0, h=1, sx=14, sy=1, sc=3, ch=False)[0]
        pts = []
        for x, y, z in _verts(m):
            d = math.hypot(x, z) / (size / 2.0)
            k = 1.0 + r.uniform(-0.3, 0.05) if d > 0.95 else 1.0
            top = y > 0
            pts.append((x * k, (2.5 + 2.0 * (1 - d * d) if top else -1.0) + r.uniform(-0.4, 0.4), z * k))
        _set_verts(m, pts)
        keep(m, "lb_litter_mat")
    return build


def pondweed(seed, blades, h0, h1, mat):
    """A clump of long ribbon weed: thin blades that rise and bend with the (still) water."""
    def build():
        r = random.Random(seed)
        for _ in range(blades):
            a = r.uniform(0, 6.283)
            x, y, z = math.cos(a) * r.uniform(0, 8), math.sin(a) * r.uniform(0, 8), -2.0
            h = r.uniform(h0, h1)
            lean = r.uniform(0, 6.283)
            bend = r.uniform(0.1, 0.35)
            segs = 5
            for s in range(segs):
                t = (s + 1) / segs
                nx = math.cos(a) * 8 * t + math.cos(lean) * h * bend * t * t
                ny = math.sin(a) * 8 * t + math.sin(lean) * h * bend * t * t
                nz = h * t
                tube((x, y, z), (nx, ny, nz), max(0.5, 1.6 * (1 - t * 0.7)), mat, sides=3)
                x, y, z = nx, ny, nz
    return build


def branch(seed, length):
    """A sunken branch lying on the bed, with a few broken twigs."""
    def build():
        r = random.Random(seed)
        a, b = (-length / 2, 0, 6), (length / 2, r.uniform(-30, 30), 4)
        tube(a, b, 6, "bark_mat", sides=8)
        for k in range(4):
            t = r.uniform(0.15, 0.85)
            p = tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
            q = (p[0] + r.uniform(-60, 60), p[1] + r.uniform(-70, 70), p[2] + r.uniform(5, 50))
            tube(p, q, 2, "bark_mat", sides=5)
    return build


BUBBLE_RISE = 600.0      # how high a stream's bubbles go before they start again at the bottom (Unreal: RiseHeight)


def bubble_stream(seed, count):
    """A stream of gas bubbles from a seep in the silt: small round bubbles spread up a column
    BUBBLE_RISE high. Unreal's M_Ch2_Sway (Rise) moves them all up and wraps them back to the
    bottom, so the stream never ends; bigger bubbles are rarer."""
    def build():
        r = random.Random(seed)
        for k in range(count):
            z = (k + r.uniform(0, 0.8)) * BUBBLE_RISE / count
            rad = r.uniform(1.0, 2.0) if r.random() < 0.8 else r.uniform(2.0, 3.2)
            spread = 2.0 + z * 0.012                     # the stream widens a little as it rises
            sphere(r.uniform(-spread, spread), r.uniform(-spread, spread), z, rad, "bubble_mat",
                   sides=6, scale=(1, 1, 0.8))
    return build


def fish_parts():
    """One small lake fish (perch-like), nose toward +x, centred on the origin, about 16 cm long:
    a slim body with a darker back, forked tail, dorsal and side fins, eyes. Returns its meshes."""
    before = len(PARTS)
    sphere(0, 0, 0, 1, "fish_body_mat", sides=10, scale=(8.0, 1.3, 2.5))               # body
    sphere(0.5, 0, 1.0, 1, "fish_back_mat", sides=10, scale=(6.8, 1.1, 1.6))           # dark back
    for s_ in (-1, 1):                                                                  # forked tail
        t = sphere(-9.2, 0, s_ * 1.3, 1, "fish_fin_mat", sides=6, scale=(2.2, 0.2, 0.9))
        cmds.rotate(0, 0, s_ * 28, t, relative=True, pivot=(-8, 0, 0))
    sphere(0.8, 0, 2.6, 1, "fish_fin_mat", sides=6, scale=(3.2, 0.15, 1.1))             # dorsal fin
    for s_ in (-1, 1):
        sphere(2.6, s_ * 1.3, -0.8, 1, "fish_fin_mat", sides=6, scale=(1.4, 0.15, 0.6))  # side fins
        sphere(5.6, s_ * 1.05, 0.5, 0.45, "fish_eye_mat", sides=6)                     # eyes
    parts = PARTS[before:]
    del PARTS[before:]
    return parts


def fish_school(seed, n):
    """A school milling in a slow ring (a 'bait ball'): n fish spread round a ring 2-4 m across,
    each heading along the ring, at a few heights. Unreal's M_Ch2_Sway (Orbit) turns the ring,
    ripples each body and bobs the school, so the fish swim round for ever."""
    def build():
        r = random.Random(seed)
        for _ in range(n):
            th = r.uniform(0, 6.283)
            R = r.uniform(170, 330)
            h = r.uniform(-60, 60) + 25 * math.sin(th * 3)
            parts = fish_parts()
            f = cmds.polyUnite(parts, constructionHistory=False)[0] if len(parts) > 1 else parts[0]
            k = r.uniform(0.8, 1.2)
            cmds.scale(k, k, k, f, pivot=(0, 0, 0))
            heading = math.degrees(th) + 90 + r.uniform(-8, 8)       # along the ring, anticlockwise
            cmds.rotate(r.uniform(-6, 6), -heading, 0, f, pivot=(0, 0, 0))   # (Maya Y turn = minus Unreal yaw)
            cmds.move(R * math.cos(th), h, R * math.sin(th), f, relative=True)
            cmds.makeIdentity(f, apply=True, t=True, r=True, s=True)
            PARTS.append(f)
    return build


def scatter_props():
    props = {
        "lb_bubbles_A": bubble_stream(18, 220), "lb_bubbles_B": bubble_stream(19, 130),
        "lb_milfoil_A": milfoil(11, 3, 50, 110), "lb_milfoil_B": milfoil(12, 5, 30, 70),
        "lb_tuft_A": tuft(13, 22, 8, 18), "lb_tuft_B": tuft(14, 30, 5, 12),
        "lb_litter_A": litter(15, 90), "lb_litter_B": litter(16, 140),
        "lb_rock_A": rock(1, 70, 55, 40), "lb_rock_B": rock(2, 45, 50, 28), "lb_rock_C": rock(3, 90, 60, 35),
        "lb_boulder_A": rock(4, 260, 200, 170), "lb_boulder_B": rock(5, 320, 240, 140),
        "lb_weed_A": pondweed(6, 7, 70, 150, "weed_mat"), "lb_weed_B": pondweed(7, 5, 110, 220, "weed_mat"),
        "lb_weed_C": pondweed(8, 9, 40, 90, "weed_brown_mat"),
        "lb_branch_A": branch(9, 260), "lb_branch_B": branch(10, 420),
    }
    made = {}
    for i, (name, fn) in enumerate(props.items()):
        made[name] = make_prop(name, fn)
        cmds.move(-20000 - i * 600, 0, -5000, made[name])   # out of the way (the scatter places copies by matrix)
    return made


def scatter(surface):
    """Scatter with the midterm scatter tool. Same settings the window would give; the bed's
    banks are too steep for anything but rocks (max slope)."""
    tool = {"__name__": "scatter_tool"}
    exec(open(SCATTER_TOOL, encoding="utf-8").read(), tool)
    base = dict(tool["DEFAULT_CONTROLS"])
    def net(name, objects, **c):
        s = dict(base, **c)
        s.update(name=name, objects=objects, surface=surface, near=c.get("near", ""))
        return s
    # plants need light: the carpet only in the shallows, milfoil and pondweed a little deeper,
    # nothing in the deep basin (min_height = the deepest a plant grows, in cm)
    nets = [
        net("Carpet", [("lb_tuft_A", 1), ("lb_tuft_B", 1)], count=12000, scale_min=0.7, scale_max=1.5,
            tilt=8, follow=90, spacing=True, min_distance=45, max_slope=20, min_height=-1150, seed=15),
        net("Milfoil", [("lb_milfoil_A", 1), ("lb_milfoil_B", 2)], count=3500, scale_min=0.7, scale_max=1.3,
            tilt=8, follow=40, spacing=True, min_distance=60, max_slope=25, min_height=-1450, near="Rocks",
            near_range=300, open_share=35, seed=16),
        # (sunken leaf patches, lb_litter_*, were tried 2026-11-24: they read as dark holes in the sand)
        net("Seeps", [("lb_bubbles_A", 1), ("lb_bubbles_B", 2)], count=40, scale_min=1.0, scale_max=1.0,
            spin=360, tilt=0, follow=0, spacing=True, min_distance=500, max_slope=15, seed=18),
        net("Boulders", [("lb_boulder_A", 1), ("lb_boulder_B", 1)], count=70, scale_min=0.7, scale_max=1.6,
            tilt=20, sink=35, spacing=True, min_distance=700, max_slope=50, seed=11),
        net("Rocks", [("lb_rock_A", 2), ("lb_rock_B", 3), ("lb_rock_C", 1)], count=900, scale_min=0.5, scale_max=1.7,
            tilt=25, sink=30, spacing=True, min_distance=160, max_slope=55, seed=12),
        net("Weeds", [("lb_weed_A", 3), ("lb_weed_B", 2), ("lb_weed_C", 3)], count=4500, scale_min=0.7, scale_max=1.4,
            tilt=12, follow=30, spacing=True, min_distance=70, max_slope=30, min_height=-1600, near="Rocks", near_range=250,
            open_share=20, near_size=120, seed=13),
        net("Branches", [("lb_branch_A", 2), ("lb_branch_B", 1)], count=80, scale_min=0.8, scale_max=1.3,
            tilt=6, follow=100, sink=5, spacing=True, min_distance=300, max_slope=25, seed=14),
    ]
    top, skipped, no_room, made = tool["build_all"](nets, "scatter_grp1", False)
    print("Scatter:", made, f"(skipped {skipped} on steep banks, {no_room} found no room)")
    return top


def export_scatter(sources):
    """Same as Chapter 1's export_to_unreal.py, into RESEARCH_PROJECT_2/export."""
    copies = []
    for net in cmds.listRelatives("scatter_grp1", children=True, fullPath=True, type="transform") or []:
        for c in cmds.listRelatives(net, children=True, fullPath=True, type="transform") or []:
            asset = cmds.getAttr(c + ".ue_asset") if cmds.attributeQuery("ue_asset", node=c, exists=True) else None
            if asset:
                copies.append({"asset": asset, "network": net.split("|")[-1],
                               "matrix": cmds.xform(c, q=True, matrix=True, worldSpace=True)})
    props, colors = {}, {}
    for asset in sorted({c["asset"] for c in copies}):
        node = sources[asset]
        dup = cmds.duplicate(node, name=asset + "_export")[0]
        cmds.xform(dup, translation=(0, 0, 0), worldSpace=True)
        path = os.path.join(OUT, asset + ".fbx").replace("\\", "/")
        cmds.select(dup)
        mel.eval("FBXResetExport")
        mel.eval("FBXExportSmoothingGroups -v true")
        mel.eval('FBXExport -f "{}" -s'.format(path))
        cmds.delete(dup)
        shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
        mats = set()
        for sg in set(cmds.listConnections(shapes, type="shadingEngine") or []):
            mats.update(cmds.listConnections(sg + ".surfaceShader") or [])
        props[asset] = {"fbx": path, "materials": sorted(mats)}
        colors.update({m: list(cmds.getAttr(m + ".color")[0]) for m in mats})
    json.dump({"props": props, "materials": colors, "copies": copies},
              open(os.path.join(OUT, "scatter.json"), "w"), indent=1)
    return len(copies)


exec(open(os.path.join(RP2, "maya", "ch2_props.py"), encoding="utf-8").read())
LANTERNS = []


def export_prop(name, mesh):
    """One prop mesh -> export/<name>.fbx (pivot where it was built). Returns (path, its materials)."""
    path = os.path.join(OUT, name + ".fbx").replace("\\", "/")
    cmds.select(mesh)
    mel.eval("FBXResetExport")
    mel.eval('FBXExport -f "{}" -s'.format(path))
    mats = set()
    for sg in cmds.listConnections(cmds.listRelatives(mesh, shapes=True), type="shadingEngine") or []:
        mats.update(cmds.listConnections(sg + ".surfaceShader") or [])
    return path, mats


HUNTER_R = 900.0       # the hunter swims round a ring this wide (cm) over the gully


def hunter_on_ring():
    """The hunter, built nose +x, moved out to HUNTER_R and turned to swim anticlockwise round the prop's
    pivot (Unreal turns the ring with M_Ch2_Sway Orbit, like the fish)."""
    before = len(PARTS)
    hunter_parts()
    parts = PARTS[before:]
    del PARTS[before:]
    m = cmds.polyUnite(parts, constructionHistory=False)[0]
    cmds.rotate(0, -90, 0, m, pivot=(0, 0, 0))          # heading +y (Maya Y turn = minus Unreal yaw)
    cmds.move(HUNTER_R, 0, 0, m, relative=True)
    cmds.makeIdentity(m, apply=True, t=True, r=True, s=True)
    PARTS.append(m)


def build():
    del PARTS[:]
    del ROOM_PARTS[:]
    cmds.file(new=True, force=True)
    os.makedirs(OUT, exist_ok=True)
    for name, rgb in list(MATS.items()) + list(BED_MATS.items()) + list(CH2_MATS.items()):
        material(name, rgb)
    sources = scatter_props()
    school = make_prop("lb_fish_school", fish_school(60, 70))
    cmds.move(-30000, 0, -5000, school)
    story_props = {"lb_figure": make_prop("lb_figure", figure_parts), "lb_hunter": make_prop("lb_hunter", hunter_on_ring),
                   "lb_breather": make_prop("lb_breather", breather_parts)}
    for k, m in enumerate(story_props.values()):
        cmds.move(-40000 - k * 5000, 0, -5000, m)
    floor = lakebed()
    n_ledges = wall_ledges()
    n_rubble = rubble()
    n_trees = sunken_trees()
    dock_from_below()
    lanterns = sunken_lanterns()
    LANTERNS[:] = lanterns
    story_set()
    fx = surface_underside()
    # scatter on the bare floor before it is combined with the rest of the set
    floor_copy = cmds.duplicate(floor, name="scatter_surface")[0]
    far = []                                              # drop the banks and the flats up top
    vp = _verts(floor_copy)
    for f in range(cmds.polyEvaluate(floor_copy, face=True)):
        vs = [int(v) for v in cmds.polyInfo(f"{floor_copy}.f[{f}]", faceToVertex=True)[0].split()[2:]]
        cx = sum(vp[v][0] for v in vs) / len(vs)
        cy = sum(vp[v][2] for v in vs) / len(vs)
        if edge(cx, cy)[0] > TOE + 250:
            far.append(f"{floor_copy}.f[{f}]")
    if far:
        cmds.delete(far)
    scatter(floor_copy)
    n_copies = export_scatter(sources)
    cmds.move(0, 0, 0, school)
    school_fbx = os.path.join(OUT, "lb_fish_school.fbx").replace("\\", "/")
    cmds.select(school)
    mel.eval("FBXResetExport")
    mel.eval('FBXExport -f "{}" -s'.format(school_fbx))
    school_mats = set()
    for sg in cmds.listConnections(cmds.listRelatives(school, shapes=True), type="shadingEngine") or []:
        school_mats.update(cmds.listConnections(sg + ".surfaceShader") or [])
    cmds.delete(school)
    prop_files = {"lb_fish_school": school_fbx}
    for name, m in story_props.items():
        cmds.move(0, 0, 0, m)
        prop_files[name], mts = export_prop(name, m)
        school_mats |= mts
        cmds.delete(m)
    cmds.delete(floor_copy)

    bed = cmds.polyUnite(PARTS, name="set_lakebed", constructionHistory=False)[0]
    cmds.delete(bed, constructionHistory=True)
    cmds.xform(bed, pivots=(0, 0, 0), worldSpace=True)
    extra = {}
    extra["set_lakebed_specks"] = specks()
    extra["set_lakebed_shafts"] = light_shafts()
    for name, parts in (("set_lakebed_fx", fx), ("set_lakebed_block", blockers())):
        m = cmds.polyUnite(parts, name=name, constructionHistory=False)[0] if len(parts) > 1 else cmds.rename(parts[0], name)
        cmds.delete(m, constructionHistory=True)
        cmds.xform(m, pivots=(0, 0, 0), worldSpace=True)
        if name.endswith("_block"):
            material("lake_block_mat", (1, 0, 1))
            cmds.sets(m, edit=True, forceElement="lake_block_matSG")
        extra[name] = m
    lights = cmds.ls("light_*", type="transform")
    cmds.file(rename=os.path.join(RP2, "maya", "lakebed_scene.ma"))
    cmds.file(save=True, type="mayaAscii")
    if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
        cmds.loadPlugin("fbxmaya")
    sets, used = {}, set()
    for name, m in [("set_lakebed", bed)] + list(extra.items()):
        f = os.path.join(OUT, name + ".fbx").replace("\\", "/")
        cmds.select(m)
        mel.eval("FBXResetExport")
        mel.eval('FBXExport -f "{}" -s'.format(f))
        sets[name] = f
        for sg in cmds.listConnections(cmds.listRelatives(m, shapes=True), type="shadingEngine") or []:
            used.update(cmds.listConnections(sg + ".surfaceShader") or [])
    sx = path_x(START_Y)
    data = {"sets": sets, "room_sets": [], "props": prop_files,
            "materials": {m: list(cmds.getAttr(m + ".color")[0]) for m in sorted(used | school_mats)},
            "lights": [dict(json.loads(cmds.getAttr(l + ".ue_light")), name=l,
                            position=[cmds.xform(l, q=True, t=True, ws=True)[i] for i in (0, 2, 1)]) for l in lights],
            "start": [sx, START_Y, bed_z(sx, START_Y) + 100], "surface_z": SURFACE_Z,
            "lanterns": [[x, y, bed_z(x, y)] for x, y in lanterns],
            # fish schools: one copy of lb_fish_school milling 2-3 m over the gully floor at each spot
            # the story (unreal/place_clues2.py, lakebed_level.py place_story)
            "clue_spots": CLUE_SPOTS,
            # the red-lit figure, standing further on each time (it fades out as you get near)
            "figures": [[path_x(y) + dx, y, bed_z(path_x(y) + dx, y), yaw] for y, dx, yaw in
                        ((8200, 350, 200), (11900, -200, 170), (14700, 250, 190), (16050, 60, 185))],
            "hunter": [path_x(10200), 10200, floor_z(10200) + 260],
            "breather": [path_x(17600), 17900, floor_z(17600) - 300],
            "schools": [[path_x(y) + dx, y, floor_z(y) + h] for y, dx, h in
                        ((1200, 150, 260), (5600, -250, 300), (9800, 200, 330), (15200, -300, 420))],
            "path": [[path_x(y), y, floor_z(y)] for y in range(-2000, 18000, 500)]}
    json.dump(data, open(os.path.join(OUT, "sets_lakebed.json"), "w"), indent=1)
    print(f"Lakebed built: {cmds.polyEvaluate(bed, triangle=True)} triangles, {len(lanterns)} sunken lanterns, "
          f"{n_copies} scatter copies, {n_ledges} wall ledges, {n_rubble} rubble rocks, {n_trees} sunken trees")


build()

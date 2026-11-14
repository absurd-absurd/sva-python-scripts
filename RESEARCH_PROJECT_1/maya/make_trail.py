"""Build the structures along the trail from the motel to the lake, and export them for Unreal.

Run with mayapy (or in Maya):
    exec(open(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/maya/make_trail.py").read())

- the BACK GATE: a rusty chain-link fence all round the motel and office (behind and down both
  sides to the road) with barbed wire on top, and a gate
  where the trail starts, shut with a chain and a new padlock, a NO TRESPASSING sign on it.
  The gate leaf is a door (export/prop_gate.fbx, clues.json "door_backgate", needs the back
  gate key)
- the HUNTER'S SHACK (clearing "shack"): board walls, tin shed roof, the door hanging off one
  hinge; inside a cot (someone slept here: a bedroll, a candle stub, cans), antlers over the
  door, an empty gun rack, traps on nails, a stretched pelt, a table; a red lantern burning on
  the porch post
- the ABANDONED CAR (clearing "car"): the car itself is the same Fab car as the one in the lot,
  repainted black and rusted, sunk and leaning (unreal/place_wreck.py); here: weeds and
  vines growing up it, a fallen branch against it, drifts of dead leaves, and a red glow at its
  tail lights in the fog
- the LOOKOUT TOWER (clearing "tower"): four braced legs, six flights of stairs with landings
  and handrails up to the cabin 11 m up, which has windows all round and a table by the window
  (a clue goes there later)
Reuses the motel / lake helpers. Positions are Unreal cm; the woods floor is z 0.
Writes export/set_trail.fbx (+ set_trail_rooms: inside the shack and the tower cabin, lighting
channel 1) and export/sets_trail.json (import_sets.py reads every sets*.json).
"""
import json
import math
import os
import random

import maya.cmds as cmds
import maya.mel as mel

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
_src = open(os.path.join(ROOT, "maya", "make_lake.py"), encoding="utf-8").read()
exec(_src[:_src.rindex("\nbuild()")])           # motel + lake helpers, BLD_MATS, Placed, board_wall, ...

LAYOUT = json.load(open(os.path.join(ROOT, "layout.json")))
CLEAR = {c["name"]: c for c in LAYOUT["clearings"]}
TRAIL_MATS = {
    "firewood_bark_mat": (0.2, 0.15, 0.1), "split_wood_mat": (0.62, 0.5, 0.34), "axe_handle_mat": (0.55, 0.42, 0.26),
    "steel_edge_mat": (0.55, 0.55, 0.53), "cot_frame_mat": (0.05, 0.06, 0.04), "canvas_mat": (0.3, 0.29, 0.2),
    "bone_mat": (0.62, 0.58, 0.48), "fur_mat": (0.26, 0.18, 0.11), "can_label_mat": (0.42, 0.18, 0.1),
    "matchbox_mat": (0.5, 0.12, 0.06), "enamel_mat": (0.2, 0.3, 0.4), "flame_mat": (1.0, 0.7, 0.3),
    "galv_mat": (0.3, 0.3, 0.29), "sign_mat": (0.55, 0.53, 0.47), "sign_red_mat": (0.38, 0.03, 0.02),
    "rust_body_mat": (0.24, 0.12, 0.06), "antler_mat": (0.5, 0.45, 0.36), "pelt_mat": (0.24, 0.16, 0.09),
    "vine_mat": (0.1, 0.13, 0.06), "leaf_litter_mat": (0.2, 0.13, 0.06), "gloss_tint_mat": (0.012, 0.014, 0.016),
    "pic_sign_no_trespassing": (1, 1, 1), "pic_sign_road_closed": (1, 1, 1), "glow_amber_mat": (1.0, 0.55, 0.08),
}
FENCE_Y = -100.0                                 # the old fence line behind the motel (blockout)
GATE_X0, GATE_X1 = -3105.0, -2895.0             # the gate opening (the trail runs north at x -3000)
rng_t = random.Random(4)
FONT["G"] = [(4, 5, 3, 6), (3, 6, 1, 6), (1, 6, 0, 5), (0, 5, 0, 1), (0, 1, 1, 0), (1, 0, 3, 0), (3, 0, 4, 1), (4, 1, 4, 3), (4, 3, 2, 3)]


# ---------- the back gate and fence ----------

def chain_link(x0, x1, y, z0, z1, gap=10.0, r=0.28):
    """A chain-link panel: two sets of diagonal wires (thin tubes), z0..z1 between x0 and x1."""
    h = z1 - z0
    for sgn in (1, -1):
        s = -h
        while s < (x1 - x0):
            # a line x = x0 + s + sgn-dependent slope * (z - z0), clipped to the panel
            pa, pb = None, None
            pts = []
            for z in (z0, z1):
                x = x0 + s + (z - z0) if sgn > 0 else x0 + s + (z1 - z)
                pts.append((x, z))
            (xa, za), (xb, zb) = pts
            # clip to x0..x1
            def clip(xa, za, xb, zb):
                if xa < x0:
                    za = za + (zb - za) * (x0 - xa) / (xb - xa); xa = x0
                if xb > x1:
                    zb = za + (zb - za) * (x1 - xa) / (xb - xa) if xb != xa else zb; xb = x1
                return xa, za, xb, zb
            if xa > xb:
                xa, za, xb, zb = xb, zb, xa, za
            if xb > x0 and xa < x1:
                xa, za, xb, zb = clip(xa, za, xb, zb)
                if xb - xa > 1:
                    tube((xa, y, za), (xb, y, zb), r, "galv_mat", sides=3)
            s += gap * 1.414


FENCE_X0, FENCE_X1 = -3700.0, 4900.0           # the fence's west and east sides (Nov 10: it encloses the motel)
FENCE_FRONT = -3880.0                          # the sides run down to the road's gravel shoulder
ROAD_FENCE_WEST = -12000.0                     # along the road: to the map's west wall (fill_forest Wall_West)
ROAD_FENCE_EAST = 7630.0                       # ... and to the ROAD CLOSED gate's invisible wall (x 7630..7690)


def fence_run(xs, y, gap=None):
    """One straight run of fence along x at y: posts at xs (heavy ones at the gate), top rail,
    chain link, tension wire, three strands of barbed wire on arms leaning toward -y, weeds."""
    for x in xs:
        heavy = gap is not None and x in gap
        lean = 0 if heavy else rng_t.uniform(-3, 3)
        tube((x, y, -10), (x + lean, y, 185), 5.5 if heavy else 3.5, "galv_mat", sides=10)
        sphere(x + lean, y, 186, 6 if heavy else 4.2, "galv_mat", sides=8, scale=(1, 1, 0.6))
        tube((x + lean, y, 182), (x + lean, y - 28, 210), 1.4, "galv_mat", sides=6)       # barbed wire arm
    for a, b in zip(xs, xs[1:]):
        if gap is not None and a == gap[0]:
            continue                                                       # the gate opening
        sag = rng_t.uniform(0, 8)
        tube((a, y, 180), (b, y, 180), 2.2, "galv_mat", sides=8)                          # top rail
        chain_link(a + 4, b - 4, y + 1.5, 6 - sag * 0.2, 178 - sag)
        tube((a, y + 1.5, 8), (b, y + 1.5, 8), 0.5, "galv_mat", sides=4)                  # tension wire
        for kk in range(3):
            dz, dy = 188 + kk * 9, -7 - kk * 9
            pts = [(a + (b - a) * t / 6.0, y + dy, dz - 4 * math.sin(math.pi * t / 6.0)) for t in range(7)]
            for p0, p1 in zip(pts, pts[1:]):
                tube(p0, p1, 0.3, "rusty_tool_mat", sides=3)
            for p in pts[1:-1]:
                tube((p[0] - 2, p[1], p[2] - 1.5), (p[0] + 2, p[1], p[2] + 1.5), 0.25, "rusty_tool_mat", sides=3)
        if rng_t.random() < 0.3:                                            # weeds grown up through it
            for w in range(10):
                wx = rng_t.uniform(a, b)
                hh = rng_t.uniform(30, 90)
                tube((wx, y + rng_t.uniform(-25, 25), 0), (wx + rng_t.uniform(-10, 10), y + rng_t.uniform(-15, 15), hh),
                     0.6, "weed_mat", sides=3)


def posts(a, b, step=300):
    n = max(1, int(round((b - a) / step)))
    return [round(a + (b - a) * k / n) for k in range(n + 1)]


def fence():
    """A complete chain-link fence round the motel and the office: behind them (with the gate
    where the trail goes into the woods) and down both sides to the road's shoulder. Posts every
    ~3 m, top rail, chain link, three strands of barbed wire on leaning arms, sagging, weeds."""
    xs = posts(FENCE_X0, GATE_X0) + posts(GATE_X1, FENCE_X1)
    fence_run(sorted(set(xs)), FENCE_Y, gap=(round(GATE_X0), round(GATE_X1)))
    L = FENCE_Y - FENCE_FRONT
    mid = (FENCE_Y + FENCE_FRONT) / 2.0
    for x, yaw in ((FENCE_X0, -90), (FENCE_X1, 90)):                     # barbed arms lean inward
        with Placed(x, mid, yaw):
            fence_run(posts(-L / 2.0, L / 2.0), 0.0)
    # Nov 13: from both front corners the fence turns and runs along the woods side of the road,
    # so the back gate is the only way into the woods: west into the map's west wall (in the fog),
    # east to the ROAD CLOSED gate (its invisible wall starts right there). Barbs lean to the road.
    fence_run(posts(ROAD_FENCE_WEST, FENCE_X0), FENCE_FRONT)
    fence_run(posts(FENCE_X1, ROAD_FENCE_EAST), FENCE_FRONT)
    # the sign on the fence beside the gate, facing the motel (south)
    no_trespassing(GATE_X0 - 150, FENCE_Y - 4)


def no_trespassing(cx, y):
    """A real NO TRESPASSING sign wired to the chain link, facing -y (the motel): an aluminium
    sheet, the painted face (tools/make_signs.py: faded, rust from the bolts, bullet holes, dirt),
    four bolts with washers, wire ties through the link, a touch crooked, one corner bent back."""
    W, Hs = 92.0, 57.5
    with Placed(cx, y, 90):                                   # built facing -x, turned to face -y
        sp = 3.0
        rbevel(-0.2, 0, 148, 0.6, W + 2, Hs + 2, "galv_mat", r=0.25, tilt_y=sp)        # the sheet
        picture(-0.6, 0, 148, W, Hs, "pic_sign_no_trespassing", spin=sp, facing=-1)
        rbevel(1.2, W / 2.0 - 6, 148 + Hs / 2.0 - 6, 1.2, 10, 10, "galv_mat", r=0.3, tilt_x=-14)   # bent corner
        for dy, dz in ((-W / 2 + 4.5, Hs / 2 - 4.5), (W / 2 - 4.5, Hs / 2 - 4.5),
                       (-W / 2 + 4.5, -Hs / 2 + 4.5), (W / 2 - 4.5, -Hs / 2 + 4.5)):
            zz = 148 + dz + dy * math.sin(math.radians(sp))
            tube((-0.7, dy, zz), (-1.6, dy, zz), 1.1, "galv_mat", sides=8)                 # washer
            sphere(-1.8, dy, zz, 0.7, "rusty_tool_mat", sides=6)                         # bolt head
            ring(0.6, dy, zz, 1.4, 0.18, "galv_mat", axis="y", sides=8)                  # wire tie through the link


ROADBLOCK_X = 7600.0                          # the road is closed here, east of the motel


def chain_between(x, p0, p1, links):
    for k in range(links):
        t = (k + 0.5) / links
        ring(x, p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t, 1.6, 0.4, "rusty_tool_mat",
             axis="y" if k % 2 else "x", sides=8)


def road_closed():
    """Where the road is closed east of the motel: a galvanized pipe swing gate across the road
    (two leaves from heavy posts on the shoulders, red-and-white striped boards, the leaves chained
    together with a padlock), a ROAD CLOSED sign hung from it by two chains, one chain snapped so
    the sign has swung down at an angle, an amber warning lamp flashing on each post, and a few
    traffic cones. Behind it, an invisible wall (road_closed_wall)."""
    X = ROADBLOCK_X
    Y_N, Y_S = -3985.0, -5015.0                              # post centres, on the shoulders
    mid = (Y_N + Y_S) / 2.0
    for y in (Y_N, Y_S):
        frustum(X, y, -20, 0, 22, 22, "concrete_mat", sides=12)                   # footing
        tube((X, y, -10), (X, y, 135), 7, "galv_mat", sides=12)                    # post
        frustum(X, y, 135, 140, 8, 3, "galv_mat", sides=12)                        # cap
        for z in (50, 112):                                                         # hinge collars
            ring(X, y + (-6 if y > mid else 6), z, 4.5, 1.4, "rusty_tool_mat", sides=10)
        tube((X, y, 132), (X - 6, y, 150), 1.6, "galv_mat", sides=6)               # lamp bracket
        frustum(X - 6, y, 150, 154, 9, 9, "tv_mat", sides=16)
        frustum(X - 6, y, 154, 166, 8.5, 7.5, "glow_amber_mat", sides=16)          # amber lens
        frustum(X - 6, y, 166, 168, 8, 4, "tv_mat", sides=16)
        light("light_roadblock_%s" % ("n" if y > mid else "s"), X - 40, y, 160, [1.0, 0.55, 0.08], 25, 700, flicker=True)
    for y0, y1 in ((Y_N - 9, mid + 3), (Y_S + 9, mid - 3)):                         # the two leaves
        for z in (45, 112):
            tube((X, y0, z), (X, y1, z), 3.0, "galv_mat", sides=10)
        tube((X, y1, 45), (X, y1, 112), 3.0, "galv_mat", sides=10)
        for k in range(1, 4):
            yy = y0 + (y1 - y0) * k / 4.0
            tube((X, yy, 45), (X, yy, 112), 1.8, "galv_mat", sides=8)
        tube((X, y0, 47), (X, y1, 110), 1.8, "galv_mat", sides=8)                   # brace
        n = 10
        for k in range(n):                                                          # striped board
            a, b = y0 + (y1 - y0) * k / n, y0 + (y1 - y0) * (k + 1) / n
            bevel_box(X - 4.5, X - 3, min(a, b), max(a, b), 92, 108, "sign_red_mat" if k % 2 else "sign_mat", r=0.3)
    for k in range(10):                                                             # chain + padlock
        a = k * 0.7
        ring(X + 4 * math.cos(a), mid + 5 * math.sin(a), 75 - k * 2.2, 2.1, 0.6, "rusty_tool_mat",
             axis="z" if k % 2 else "y", sides=8)
    bevel_box(X - 7, X - 1, mid - 4, mid + 4, 47, 58, "brass_mat", r=1.0)
    ring(X - 4, mid, 60, 2.6, 0.6, "chrome_mat", axis="x", sides=12)
    # the ROAD CLOSED sign, hanging from the top rail; one chain snapped, so it's tipped
    W, Hs = 100.0, 62.5
    tilt = 18.0
    # hung so even its low corner stays ~10 cm off the road (it went into the ground before)
    reach = Hs / 2.0 * math.cos(math.radians(tilt)) + W / 2.0 * math.sin(math.radians(tilt))
    cy, cz = mid + 14, 112 - 12 - reach
    rbevel(X - 9, cy, cz, 0.8, W + 2, Hs + 2, "galv_mat", r=0.3, tilt_y=tilt)          # the sheet
    picture(X - 9.6, cy, cz, W, Hs, "pic_sign_road_closed", spin=tilt, facing=-1)
    a = math.radians(tilt)
    c1 = (cy - W / 2 * math.cos(a) * 0.85, cz + Hs / 2 - W / 2 * math.sin(a) * 0.85 + 4)
    c2 = (cy + W / 2 * math.cos(a) * 0.85, cz + Hs / 2 + W / 2 * math.sin(a) * 0.85 - 4)
    hi, lo = (c1, c2) if c1[1] > c2[1] else (c2, c1)
    chain_between(X - 7, (hi[0], 112), hi, 6)                                         # the chain that held
    chain_between(X - 7, (lo[0], 112), (lo[0], 112 - 14), 3)                          # the snapped one, dangling
    ring(X - 7, lo[0], lo[1], 1.6, 0.4, "rusty_tool_mat", axis="y", sides=8)          # its last link, in the sign
    for k, (dy, fallen) in enumerate(((-260, False), (-80, False), (330, False))):   # cones (the knocked-over one sank into the road: removed)
        cx = X - 140 - k * 12
        if fallen:
            rbevel(cx, mid + dy, 14, 70, 28, 28, "sign_red_mat", r=8, tilt_x=86, yaw=30)
            continue
        frustum(cx, mid + dy, 0, 3, 22, 22, "tv_mat", sides=4)
        frustum(cx, mid + dy, 3, 70, 15, 3, "sign_red_mat", sides=16)
        frustum(cx, mid + dy, 34, 46, 10.5, 8.5, "sign_mat", sides=16)


def road_closed_wall():
    """An invisible wall just behind the gate, from the south edge of the map up into the woods
    (the trees hide where it ends)."""
    c = cmds.polyCube(w=60, h=800, d=10400, ch=False)[0]
    cmds.move(ROADBLOCK_X + 60, 400, (-9900 + 500) / 2.0, c)
    return c


def gate_leaf(name):
    """The gate leaf built at its hinge (x 0 .. 206, facing +y is the outside / woods side): a pipe
    frame with a middle brace, chain link, the chain wrapped round the latch post end and a new
    padlock (it opens toward the woods)."""
    keep_parts = PARTS[:]
    del PARTS[:]
    W, Hh = 206.0, 176.0
    for p0, p1 in (((0, 0, 6), (0, 0, Hh)), ((W, 0, 6), (W, 0, Hh)), ((0, 0, 6), (W, 0, 6)), ((0, 0, Hh), (W, 0, Hh)),
                   ((0, 0, 90), (W, 0, 90)), ((0, 0, 8), (W, 0, Hh - 2))):
        tube(p0, p1, 2.4, "galv_mat", sides=8)
    chain_link(4, W - 4, 1.0, 10, Hh - 4)
    for z in (30, Hh - 30):                                               # hinge collars
        ring(0, 0, z, 4, 1.4, "rusty_tool_mat", sides=10)
    # the chain: links wrapped round the free end, the padlock hanging off it
    for k in range(9):
        a = k * 0.8
        ring(W + 6 * math.cos(a), 6 * math.sin(a), 96 - k * 2.2, 2.0, 0.55, "rusty_tool_mat", axis="z" if k % 2 else "x", sides=8)
    bevel_box(W + 3, W + 11, 4, 9, 70, 82, "brass_mat", r=1.2)
    ring(W + 7, 6.5, 84, 2.6, 0.6, "chrome_mat", axis="y", sides=12)
    mesh = cmds.polyUnite(PARTS, name=name, ch=False)[0]
    cmds.delete(mesh, constructionHistory=True)
    cmds.xform(mesh, pivots=(0, 0, 0), worldSpace=True)
    del PARTS[:]
    PARTS.extend(keep_parts)
    return mesh


# ---------- the hunter's shack ----------

# ---------- shack props (realistic pass, Nov 14) ----------

def firewood(cx, cy, cz, length, r, span=180.0, roll=0.0, yaw=0.0, tilt_x=0.0, seed=0):
    """A piece of firewood along x (before yaw): a log of radius r, split so only span degrees
    of bark remain (360 = a round log). The bark side is bark, the split face and both ends are
    pale split wood."""
    rng = random.Random(seed)
    n = 14
    c = cmds.polyCylinder(r=1, h=1, sx=n, sy=1, sz=0, ch=False)[0]
    pts = []
    for vx, vy, vz in _verts(c):
        k = int(round((math.atan2(vz, vx) % (2 * math.pi)) / (2 * math.pi / n))) % n
        a = math.radians(roll) + (2 * math.pi * k / n) * span / 360.0
        rr = r * (1 + rng.uniform(-0.05, 0.05))
        pts.append((vy * length + rng.uniform(-0.6, 0.6), rr * math.sin(a), rr * math.cos(a)))
    _set_verts(c, pts)
    cmds.polySoftEdge(c, angle=40, ch=False)
    nf = cmds.polyEvaluate(c, face=True)
    ends = []
    for fi in range(nf):
        vs = [int(t) for t in cmds.polyInfo("%s.f[%d]" % (c, fi), faceToVertex=True)[0].split(":")[1].split()]
        ring = sorted(set(v % n for v in vs))
        if len(vs) > 4 or (span < 359 and ring == [0, n - 1]):
            ends.append("%s.f[%d]" % (c, fi))
    _place(c, cx, cy, cz, "firewood_bark_mat", yaw=yaw, tilt_x=tilt_x)
    if ends:
        cmds.sets(ends, e=True, forceElement="split_wood_matSG")
    return c


def tapered(points, r0, r1, mat, sides=12):
    """A tube along a polyline whose radius goes from r0 to r1, with round joints."""
    n = len(points) - 1
    for i, (a, b) in enumerate(zip(points, points[1:])):
        rr = r0 + (r1 - r0) * (i + 0.5) / n
        tube(a, b, rr, mat, sides=sides)
        if i < n - 1:
            sphere(*b, rr, mat, sides=sides)


def stuck_axe(x, y, z, yaw):
    """An axe driven into the top of a chopping block (z = the block's top): a forged head with a
    thin bright bit and a thick poll, a curved hickory handle with a swelled knob, rising away."""
    with Moved(x, y, yaw):
        h = cmds.polyCube(w=1, h=1, d=1, ch=False)[0]
        pts = []
        for vx, vy, vz in _verts(h):
            if vy < 0:                                    # the bit, buried in the wood
                pts.append((vx * 13.0, -4.0, vz * 0.6))
            else:                                         # the poll
                pts.append((vx * 5.5, 13.0, vz * 3.4))
        _set_verts(h, pts)
        _bevel(h, 0.3, 1)
        cmds.move(x, z, y, h, relative=True)
        keep(h, "rusty_tool_mat")
        rbevel(x, y, z - 2.6, 12.8, 0.9, 1.6, "steel_edge_mat", r=0.2)        # the honed edge, just showing
        tube((x - 3, y, z + 9.5), (x + 3, y, z + 9.5), 2.2, "rusty_tool_mat", sides=12)       # the eye boss, round the handle
        handle = [(x + 1, y, z + 9.5), (x + 14, y + 0.5, z + 17), (x + 30, y + 0.8, z + 26),
                  (x + 46, y + 0.4, z + 33), (x + 60, y - 0.6, z + 38), (x + 68, y - 1.0, z + 41)]
        tapered(handle, 1.7, 1.5, "axe_handle_mat", sides=12)
        sphere(x + 69.5, y - 1.1, z + 42, 2.1, "axe_handle_mat", sides=12, scale=(0.8, 1, 1))  # knob


def tin_can(x, y, z, opened=True, lying=False, seed=0):
    """A tin can: body with rolled rims and ribs, a faded paper label, the lid bent up when opened."""
    if lying:
        tube((x - 5.5, y, z + 3.9), (x + 5.5, y, z + 3.9), 3.9, "can_mat", sides=16)
        tube((x - 3.2, y, z + 3.9), (x + 3.2, y, z + 3.9), 4.0, "can_label_mat", sides=16)
        return
    frustum(x, y, z, z + 11, 3.9, 3.9, "can_mat", sides=18, open_ends=opened)
    frustum(x, y, z + 0.3, z + 10.8, 3.7, 3.7, "can_mat", sides=18, open_ends=True, inside=True)
    frustum(x, y, z + 2.5, z + 8.5, 4.0, 4.0, "can_label_mat", sides=18, open_ends=True)
    for zz in (0.4, 10.6):
        ring(x, y, z + zz, 3.9, 0.3, "can_mat", sides=18)
    if opened:
        rbevel(x + 2.5, y, z + 13.5, 0.25, 7.4, 7.4, "can_mat", r=0.1, tilt_x=-60)        # lid bent back
    else:
        frustum(x, y, z + 10.6, z + 10.8, 3.6, 3.6, "can_mat", sides=18)


def leghold_trap(x, y, z, seed=0):
    """A steel leghold trap hanging flat against an east-facing wall (in the y-z plane) from a
    nail by its chain: two semicircular jaws, the pan in the middle, a flat leaf spring out each
    side with an eye over the jaws, the chain."""
    tube((x + 1, y, z + 30), (x - 4, y, z + 31), 0.4, "rusty_tool_mat", sides=4)            # nail
    for k in range(6):                                                                        # chain
        ring(x - 3, y, z + 27 - k * 2.6, 1.3, 0.3, "rusty_tool_mat", axis="z" if k % 2 else "x", sides=8)
    cz = z
    for side in (-1, 1):                                                                      # jaws
        arc = [(x - 3 - (0.8 if side > 0 else 0), y + 9 * math.cos(t), cz - 9 * math.sin(t) if side < 0 else cz + 9 * math.sin(t))
               for t in [math.pi * k / 10.0 for k in range(11)]]
        for a, b in zip(arc, arc[1:]):
            tube(a, b, 0.55, "rusty_tool_mat", sides=6)
    rbevel(x - 3, y, cz, 0.5, 6, 6, "rusty_tool_mat", r=0.2)                                 # pan
    rbevel(x - 2.5, y, cz, 0.6, 20, 2.0, "rusty_tool_mat", r=0.2)                            # cross bar
    for side in (-1, 1):                                                                      # leaf springs
        rbevel(x - 3, y + side * 17, cz - 1.5, 0.5, 15, 1.8, "rusty_tool_mat", r=0.2, tilt_x=0)
        ring(x - 3, y + side * 9.5, cz, 2.0, 0.4, "rusty_tool_mat", axis="y", sides=10)



def shack():
    c = CLEAR["shack"]
    HX, HY, F = 220.0, 190.0, 12.0
    FRONT_H, BACK_H = 270.0, 225.0                     # shed roof sloping to the back
    top = lambda y: BACK_H + (FRONT_H - BACK_H) * (y + HY) / (2 * HY)
    with Placed(c["x"], c["y"], 12) as P:
        rng = random.Random(9)
        # floor on sills
        for y in range(int(-HY) + 8, int(HY) - 4, 15):
            bevel_box(-HX + 4, HX - 4, y, y + 14, F - 3, F, "plank_grey_mat" if rng.random() > 0.3 else "plank_dark_mat", r=0.5)
        for x in (-HX + 10, 0, HX - 10):
            bevel_box(x - 7, x + 7, -HY, HY, 0, F - 3, "plank_dark_mat", r=0.8)
        door = (-50, 50, F - 2, F + 205)
        win = (60, 150, F + 100, F + 170)
        board_wall("x", HY, -HX, HX, 0, lambda s: FRONT_H, 3.0, "plank_grey_mat", openings=[door, win], missing=0.04, seed=31)
        board_wall("x", -HY, -HX, HX, 0, lambda s: BACK_H, 3.0, "plank_grey_mat", missing=0.06, seed=32)
        board_wall("y", -HX, -HY, HY, 0, top, 3.0, "plank_grey_mat", openings=[(-40, 40, F + 100, F + 160)], missing=0.05, seed=33)
        board_wall("y", HX, -HY, HY, 0, top, 3.0, "plank_grey_mat", missing=0.07, seed=34)
        frame("x", HY, -50, 50, F, F + 205, 3.5)
        frame("x", HY, 60, 150, F + 100, F + 170, 3.5)
        plank_boards_over("x", HY, 60, 150, F + 100, F + 170, 5.5, seed=3)       # front window boarded
        frame("y", -HX, -40, 40, F + 100, F + 160, -3.5)
        plank_boards_over("y", -HX, -40, 40, F + 100, F + 160, -5.5, seed=4)     # side window (by the cot) boarded up
        for xx in (-HX, HX):
            for yy in (-HY, HY):
                bevel_box(xx - 6, xx + 6, yy - 6, yy + 6, 0, top(yy), "plank_dark_mat", r=1)
        # tin roof in strips, rusted, one sheet slipped
        ang = math.degrees(math.atan2(FRONT_H - BACK_H, 2 * HY))
        L = (2 * HY + 60) / math.cos(math.radians(ang))
        x = -HX - 30
        k = 0
        while x < HX + 30:
            slip = 14 if k == 3 else 0
            rbevel(x + 46, slip, (FRONT_H + BACK_H) / 2.0 + 4 - slip * 0.1, 90, L, 1.4, "roof_tin_mat", r=0.4, tilt_y=-ang)
            for cc in range(5):
                rbevel(x + 6 + cc * 18, slip, (FRONT_H + BACK_H) / 2.0 + 5.5 - slip * 0.1, 3, L, 1.4, "roof_tin_mat", r=0.4, tilt_y=-ang)
            x += 88
            k += 1
        # stovepipe through the roof
        tube((HX - 60, -HY + 60, F + 60), (HX - 60, -HY + 60, BACK_H + 90), 7, "stove_mat", sides=12)
        frustum(HX - 60, -HY + 60, BACK_H + 90, BACK_H + 100, 13, 3, "stove_mat", sides=12)
        # the door, hanging off its bottom hinge, leaning out
        with Moved(-50, HY + 3, -70):
            for kk in range(5):
                rbevel(-50 + 10 + kk * 20, HY + 3, F + 100, 19.4, 3.5, 200, "plank_grey_mat" if kk % 2 else "plank_dark_mat",
                       r=0.5, tilt_x=-9)
            rbevel(0, HY + 6, F + 40, 96, 2.5, 14, "plank_dark_mat", r=0.5, tilt_x=-9)
            rbevel(0, HY + 6, F + 160, 96, 2.5, 14, "plank_dark_mat", r=0.5, tilt_x=-9)
        # a step and a porch post with the red lantern burning on a nail
        bevel_box(-70, 70, HY + 4, HY + 44, 0, F - 2, "plank_dark_mat", r=0.8)
        bevel_box(-90, -80, HY + 30, HY + 40, 0, FRONT_H - 10, "plank_dark_mat", r=1)
        rbevel(-85, HY + 35, FRONT_H - 10, 14, 12, 4, "plank_dark_mat", r=0.8)
        tube((-80, HY + 35, 180), (-72, HY + 35, 181), 0.5, "rusty_tool_mat", sides=4)
        lx, ly = P.world(-66, HY + 35)
        red_lantern(-66, HY + 35, 150)
        light("light_shack_lantern", lx, ly, 168, [1.0, 0.04, 0.01], 3, 520)
        # a chopping block with an axe stuck in it, chips round it, a stacked woodpile along the side wall
        frustum(150, HY + 120, 0, 44, 25, 27, "firewood_bark_mat", sides=20)                 # the block, bark on
        frustum(150, HY + 120, 44, 44.6, 24.4, 24.4, "split_wood_mat", sides=20)            # its sawn top
        for k in range(5):                                                                    # cut marks
            a = rng.uniform(0, 3.14)
            rbevel(150 + rng.uniform(-10, 10), HY + 120 + rng.uniform(-10, 10), 44.65, 9, 0.5, 0.15,
                   "plank_dark_mat", r=0.05, yaw=math.degrees(a))
        stuck_axe(147, HY + 120, 44.6, 25)
        for k in range(9):                                                                    # chips
            ang, d_ = rng.uniform(0, 6.28), rng.uniform(32, 70)
            rbevel(150 + d_ * math.cos(ang), HY + 120 + d_ * math.sin(ang), 0.8, rng.uniform(4, 9), rng.uniform(2, 4), 0.8,
                   "split_wood_mat", r=0.2, yaw=rng.uniform(0, 180))
        firewood(105, HY + 150, 0, 46, 9.5, span=180, roll=0, yaw=70, seed=71)                # a split half by the block
        firewood(190, HY + 85, 8.5, 44, 8.5, span=360, roll=0, yaw=-20, seed=72)
        # the woodpile: rounds and half-split logs stacked neatly along the east wall, ends out,
        # each row resting on the one below (half logs lie flat side down)
        wseed = 100
        base = 0.0
        for row in range(5):
            y_ = -HY + 20 + (row % 2) * 8
            r_row = rng.uniform(9.0, 10.5)
            half_row = (row % 2 == 1)
            y_end = HY - 30 - row * 16
            while y_ + 2 * r_row < y_end:
                r_ = r_row * rng.uniform(0.92, 1.05)
                L_ = rng.uniform(46, 54)
                if half_row:                                   # flat side down: arc on top, chord at the base
                    firewood(HX + 40 + rng.uniform(-2, 2), y_ + r_, base, L_, r_, span=180, roll=0,
                             yaw=rng.uniform(-3, 3), seed=wseed)
                else:
                    firewood(HX + 40 + rng.uniform(-2, 2), y_ + r_, base + r_, L_, r_, span=360,
                             roll=rng.uniform(0, 360), yaw=rng.uniform(-3, 3), seed=wseed)
                wseed += 1
                y_ += 2 * r_ + rng.uniform(0.3, 1.5)
            base += (r_row if half_row else 2 * r_row) - 0.8

        # ---- inside (lighting channel 1)
        IN_ROOM[0] = True
        I = 3.0
        # an army folding cot along the back wall: two side rails, a canvas sling sagging between
        # them, X legs with pivot bolts at both ends and the middle, rubber feet
        X0, X1, Y0, Y1, CZ = -HX + 30, -HX + 210, -HY + 22, -HY + 93, F + 40
        for yy in (Y0, Y1):
            tube((X0 - 4, yy, CZ), (X1 + 4, yy, CZ), 1.7, "cot_frame_mat", sides=12)
        for xx in (X0 - 4, X1 + 4):
            tube((xx, Y0, CZ), (xx, Y1, CZ), 1.3, "cot_frame_mat", sides=10)
        for xx in (X0 + 6, (X0 + X1) / 2.0, X1 - 6):
            for ya, yb in ((Y0, Y1), (Y1, Y0)):
                tube((xx, ya, CZ - 1), (xx + (0.8 if ya < yb else -0.8), yb, F + 1), 1.2, "cot_frame_mat", sides=10)
            sphere(xx, (Y0 + Y1) / 2.0, (CZ + F) / 2.0, 1.6, "rusty_tool_mat", sides=8)
            for yy in (Y0, Y1):
                sphere(xx, yy, F + 1.2, 1.8, "tire_mat", sides=8, scale=(1, 1, 0.6))
        sling = []
        for r_ in range(13):
            u = r_ / 12.0
            row = []
            for c_ in range(9):
                v = c_ / 8.0
                sag = 5.5 * math.sin(math.pi * v) * (0.6 + 0.4 * math.sin(math.pi * u))
                row.append((0, Y0 + 1 + (Y1 - Y0 - 2) * v, CZ + 1.4 - sag))
            sling.append(row)
        for r_, row in enumerate(sling):                     # rows run along x
            sling[r_] = [(X0 + (X1 - X0) * r_ / 12.0 - (X0 + X1) / 2.0, yy, zz) for _, yy, zz in row]
        _cloth((X0 + X1) / 2.0, sling, "canvas_mat")
        quilted((X0 + X1) / 2.0, (Y0 + Y1) / 2.0, CZ - 2.5, 60, 150, 7, "sleeping_bag_mat", baffles=8, seed=3, yaw=90)
        pillow(X0 + 24, (Y0 + Y1) / 2.0, CZ + 3.5, 60, 40, 13, 31, yaw=90, tilt_y=-8, dent=2.0)   # a pillow like the motel's
        # a slatted crate for a table: corner posts, slats with gaps, a plank top; on it a candle
        # stub with wax run down its side, a matchbox and two spent matches
        cx0, cx1, cy0, cy1, ch = -HX + 230, -HX + 290, -HY + 20, -HY + 70, 45.0
        for xx in (cx0, cx1 - 4):
            for yy in (cy0, cy1 - 4):
                bevel_box(xx, xx + 4, yy, yy + 4, F, F + ch, "plank_dark_mat", r=0.5)
        for k in range(3):
            za = F + 3 + k * 14
            for a_, b_, c_, d_ in ((cx0, cx1, cy0 - 1.2, cy0), (cx0, cx1, cy1, cy1 + 1.2),
                                   (cx0 - 1.2, cx0, cy0, cy1), (cx1, cx1 + 1.2, cy0, cy1)):
                bevel_box(a_, b_, c_, d_, za, za + 10, "plank_grey_mat", r=0.3)
        for k in range(4):
            bevel_box(cx0 - 1.2, cx1 + 1.2, cy0 - 1.2 + k * 13.5, cy0 - 1.2 + k * 13.5 + 12.6, F + ch, F + ch + 1.6,
                      "plank_grey_mat", r=0.3)
        tz = F + ch + 1.6
        frustum(cx0 + 20, cy0 + 20, tz, tz + 0.6, 6, 6.5, "candle_mat", sides=18)            # wax puddle
        frustum(cx0 + 20, cy0 + 20, tz + 0.5, tz + 6, 2.3, 2.1, "candle_mat", sides=14)     # the stub
        for k in range(4):
            a = k * 1.7
            sphere(cx0 + 20 + 2.2 * math.cos(a), cy0 + 20 + 2.2 * math.sin(a), tz + 2 + k, 0.8, "candle_mat", sides=6,
                   scale=(0.7, 0.7, 2.2))
        tube((cx0 + 20, cy0 + 20, tz + 6), (cx0 + 20, cy0 + 20, tz + 7), 0.15, "char_mat", sides=4)   # wick
        rbevel(cx0 + 42, cy0 + 32, tz + 0.8, 5.2, 3.6, 1.6, "matchbox_mat", r=0.2, yaw=20)
        rbevel(cx0 + 42, cy0 + 32 - 1.85, tz + 0.8, 4.6, 0.1, 1.2, "char_mat", r=0.02, yaw=20)          # striker
        for k in range(2):
            tube((cx0 + 34 + k * 3, cy0 + 22, tz + 0.15), (cx0 + 38 + k * 3, cy0 + 26, tz + 0.15), 0.12, "split_wood_mat", sides=4)
            sphere(cx0 + 38 + k * 3, cy0 + 26, tz + 0.15, 0.22, "char_mat", sides=4)
        tin_can(cx0 + 28, cy1 + 22, F, opened=False)
        tin_can(cx0 + 52, cy1 + 34, F, lying=True)
        # antlers over the door: a shield plaque, the bleached skull cap, two curving beams with tines
        rbevel(0, HY - I - 1.2, F + 228, 24, 2.4, 20, "wood_mat", r=1.2)
        sphere(0, HY - I - 4, F + 222, 7, "wood_mat", sides=12, scale=(1.7, 0.35, 1))
        sphere(0, HY - I - 5.5, F + 230, 5.5, "bone_mat", sides=12, scale=(1.3, 0.8, 0.8))
        for s_ in (-1, 1):
            beam = [(s_ * 5, HY - I - 6, F + 232), (s_ * 14, HY - I - 9, F + 238), (s_ * 24, HY - I - 12, F + 247),
                    (s_ * 30, HY - I - 14, F + 259), (s_ * 31, HY - I - 13, F + 270)]
            tapered(beam, 1.9, 1.0, "antler_mat", sides=10)
            for t, ln, lean in ((1, 15, 3), (2, 17, 1), (3, 11, -2)):
                p0 = beam[t]
                tapered([p0, (p0[0] - s_ * lean, p0[1] - 2, p0[2] + ln * 0.6), (p0[0] - s_ * (lean + 1.5), p0[1] - 2.5, p0[2] + ln)],
                        1.2, 0.6, "antler_mat", sides=8)
        # the empty gun rack on the west wall: a shaped back board, two rails of upturned hooks, and the
        # paler outline on the wall where the guns hung
        gx = -HX + I
        bevel_box(gx, gx + 2, 15, 155, F + 55, F + 172, "plank_dark_mat", r=0.6)
        for zr in (F + 64, F + 158):
            bevel_box(gx + 2, gx + 5, 18, 152, zr - 4, zr + 4, "wood_mat", r=0.8)
            for k in range(3):
                yy = 40 + k * 45
                tapered([(gx + 5, yy, zr), (gx + 10, yy, zr + 0.5), (gx + 12, yy, zr + 5)], 1.3, 1.0, "wood_mat", sides=8)
        rbevel(gx + 2.1, 90, F + 112, 0.3, 112, 82, "mud_print_mat", r=0.1)
        # traps hanging on the east wall
        for k in range(3):
            leghold_trap(HX - I, -110 + k * 55, F + 160, seed=k)
        # a stretched pelt laced into a willow hoop by the stove
        PX, PY, PZ, RR = HX - 9, 60, F + 122, 30.0
        tapered([(PX, PY + RR * math.cos(t), PZ + RR * math.sin(t)) for t in [2 * math.pi * k / 24 for k in range(25)]],
                1.4, 1.4, "wood_mat", sides=8)
        hide = []
        for r_ in range(11):
            v = r_ / 10.0 - 0.5
            row = []
            for c_ in range(11):
                u = c_ / 10.0 - 0.5
                e = max(0.0, 1 - (u * u / 0.25 + v * v / 0.25))
                bulge = 3.5 * e
                row.append((-bulge, PY + u * 2 * (RR - 7) * (0.8 + 0.2 * math.cos(v * 3)), PZ + v * 2 * (RR - 5)))
            hide.append(row)
        _cloth(PX - 0.8, hide, "fur_mat")
        for k in range(12):                                                                  # lacing
            t = 2 * math.pi * k / 12
            tube((PX - 0.5, PY + RR * math.cos(t), PZ + RR * math.sin(t)),
                 (PX - 1.5, PY + (RR - 7) * math.cos(t) * 0.92, PZ + (RR - 5) * math.sin(t) * 0.92), 0.2, "string_mat", sides=4)
        # the little cast-iron box stove the pipe comes out of: curved legs, a body with a top plate
        # and a lid ring, a front door with a latch and a draft spinner, a flue collar; an enamel
        # coffee pot on top, split wood beside it
        SX0, SX1, SY0, SY1, SZ0, SZ1 = HX - 95, HX - 25, -HY + 25, -HY + 95, F + 14, F + 58
        bevel_box(SX0, SX1, SY0, SY1, SZ0, SZ1, "stove_mat", r=2.5, seg=3)
        bevel_box(SX0 - 2, SX1 + 2, SY0 - 2, SY1 + 2, SZ1, SZ1 + 2.5, "stove_mat", r=0.8)
        ring((SX0 + SX1) / 2.0 - 10, (SY0 + SY1) / 2.0, SZ1 + 2.7, 9, 0.6, "stove_mat", sides=18)
        frustum((SX0 + SX1) / 2.0 + 15, (SY0 + SY1) / 2.0 + 5, SZ1 + 2.5, SZ1 + 7, 9, 7.5, "stove_mat", sides=16)
        for xx in (SX0 + 6, SX1 - 6):
            for yy in (SY0 + 6, SY1 - 6):
                tapered([(xx, yy, SZ0), (xx + (2 if xx > SX0 + 30 else -2), yy + (2 if yy > SY0 + 30 else -2), SZ0 - 8),
                         (xx + (4 if xx > SX0 + 30 else -4), yy + (4 if yy > SY0 + 30 else -4), F + 1)], 2.2, 1.5, "stove_mat", sides=8)
        dx0, dz0 = SX0 + 12, SZ0 + 8
        bevel_box(dx0, SX1 - 12, SY1, SY1 + 1.8, dz0, SZ1 - 8, "stove_mat", r=0.8)          # door, facing the room
        frustum((SX0 + SX1) / 2.0, SY1 + 2.5, dz0 + 14, dz0 + 14.5, 4.5, 4.5, "stove_mat", sides=14)
        tube((SX1 - 18, SY1 + 1.8, SZ1 - 16), (SX1 - 18, SY1 + 6, SZ1 - 16), 0.5, "steel_edge_mat", sides=6)
        tube((SX1 - 18, SY1 + 6, SZ1 - 16), (SX1 - 24, SY1 + 6, SZ1 - 16), 0.6, "steel_edge_mat", sides=6)    # latch
        for zz in (dz0 + 4, SZ1 - 12):
            tube((dx0 - 1, SY1 + 1, zz), (dx0 - 1, SY1 + 1, zz + 5), 1.0, "stove_mat", sides=8)                # hinges
        PCX, PCY = HX - 60, -HY + 60
        frustum(PCX, PCY, SZ1 + 2.5, SZ1 + 6, 8.5, 7.5, "stove_mat", sides=14)                                 # flue collar
        frustum(SX0 + 20, SY0 + 22, SZ1 + 2.6, SZ1 + 16, 7.5, 5.5, "enamel_mat", sides=16)                    # coffee pot
        frustum(SX0 + 20, SY0 + 22, SZ1 + 16, SZ1 + 18, 5.5, 4, "enamel_mat", sides=16)
        sphere(SX0 + 20, SY0 + 22, SZ1 + 18.6, 1.1, "can_mat", sides=8)
        tube((SX0 + 26, SY0 + 22, SZ1 + 8), (SX0 + 32, SY0 + 22, SZ1 + 15), 1.0, "enamel_mat", sides=8)
        ring(SX0 + 13.5, SY0 + 22, SZ1 + 10, 4.5, 0.6, "enamel_mat", axis="y", sides=12)
        for k in range(3):
            firewood(SX0 - 30, SY0 + 15 + k * 17, F, 42, 7.5, span=180, roll=0, yaw=90 + rng.uniform(-6, 6), seed=300 + k)
        cobweb((-HX + I + 1, -HY + I + 1), 1, 1, 40, BACK_H - 6)
        cobweb((HX - I - 1, HY - I - 1), -1, -1, 36, FRONT_H - 6)
        IN_ROOM[0] = False


# ---------- the rusted car ----------

def rusted_car():
    c = CLEAR["car"]
    n0 = len(PARTS)
    with Placed(c["x"], c["y"], -25):
        # the car itself is the same Fab car as in the lot, repainted and sunk (unreal/place_wreck.py);
        # here: the weeds, vines and leaves growing over and around it
        # dead leaves drifted against the wheels (the leaning branch was taken out Nov 14)
        for (wx, wy) in ((-95, -150), (95, -150), (-95, 140), (95, 140)):
            for k in range(6):
                rsoft(wx + rng_t.uniform(-25, 25), wy + rng_t.uniform(-35, 35), 2, rng_t.uniform(14, 30), rng_t.uniform(10, 24),
                      rng_t.uniform(3, 8), "leaf_litter_mat", jitter=1.5, smooth=1, seed=int(wx * wy) % 97 + k, yaw=rng_t.uniform(0, 180))
        for k in range(46):
            a = rng_t.uniform(0, 6.28)
            rr = rng_t.uniform(90, 160)
            wx, wy = math.cos(a) * rr * 0.7, math.sin(a) * rr * 1.6
            hh = rng_t.uniform(30, 110)
            tube((wx, wy, -2), (wx + rng_t.uniform(-15, 15), wy + rng_t.uniform(-15, 15), hh), 0.8, "weed_mat", sides=3)
        for k in range(8):                                                   # vines up the sides
            y0 = rng_t.uniform(-200, 200)
            s = rng_t.choice((-1, 1))
            p = (s * 95, y0, 0)
            for st in range(5):
                q = (s * (92 - st * 2), p[1] + rng_t.uniform(-20, 20), p[2] + 18)
                tube(p, q, 1.0, "vine_mat", sides=4)
                p = q
    # a red glow at the tail lights
    a = math.radians(-25)
    bx, by = c["x"] - 235 * -math.sin(a), c["y"] - 235 * math.cos(a)
    light("light_car_wreck", bx, by, 70, [1.0, 0.03, 0.0], 40, 600)


# ---------- the lookout tower ----------

TOWER_FL = 1100.0
FLIGHTS, RISERS = 6, 9


def tower():
    c = CLEAR["tower"]
    rise = TOWER_FL / (FLIGHTS * RISERS)
    tread = 28.0
    run = RISERS * tread                                     # 252
    Y0, Y1 = -run / 2.0, run / 2.0
    with Placed(c["x"], c["y"], 0):
        # legs and bracing
        for sx in (-1, 1):
            for sy in (-1, 1):
                tube((sx * 230, sy * 230, -20), (sx * 205, sy * 205, TOWER_FL), 11, "plank_dark_mat", sides=8)
                rsoft(sx * 230, sy * 230, 10, 60, 60, 26, "stone_mat", jitter=3, smooth=1, seed=sx + 3 * sy)
        for k in range(5):                                       # braces start above head height: the
            z0, z1 = 240 + k * 172, 240 + (k + 1) * 172 - 6      # way in under the tower stays open
            t0, t1 = 230 - 25 * z0 / TOWER_FL, 230 - 25 * z1 / TOWER_FL
            for s in (-1, 1):
                tube((-t0, s * t0, z0), (t1, s * t1, z1), 4, "plank_grey_mat", sides=6)       # X braces, front/back
                tube((t0, s * t0, z0), (-t1, s * t1, z1), 4, "plank_grey_mat", sides=6)
                tube((s * t0, -t0, z0), (s * t1, t1, z1), 4, "plank_grey_mat", sides=6)       # sides
                tube((s * t0, t0, z0), (s * t1, -t1, z1), 4, "plank_grey_mat", sides=6)
            for s in (-1, 1):                                                                  # horizontal girts
                tube((-t1, s * t1, z1), (t1, s * t1, z1), 4.5, "plank_dark_mat", sides=6)
                tube((s * t1, -t1, z1), (s * t1, t1, z1), 4.5, "plank_dark_mat", sides=6)
        # the stairs: flights up the west side going north, back down the east side going south, ...
        def rails(x_out, ya, yb, za, zb):
            for h in (45, 92):
                tube((x_out, ya, za + h), (x_out, yb, zb + h), 2.2, "plank_grey_mat", sides=6)
            for f in (0.0, 0.5, 1.0):
                yy, zz = ya + (yb - ya) * f, za + (zb - za) * f
                bevel_box(x_out - 3, x_out + 3, yy - 3, yy + 3, zz - 10, zz + 94, "plank_dark_mat", r=0.6)
        z = 0.0
        for fl in range(FLIGHTS):
            north = fl % 2 == 0
            xa, xb = (-150, -50) if north else (50, 150)
            for k in range(RISERS):
                zt = z + (k + 1) * rise
                yy = (Y0 + k * tread) if north else (Y1 - (k + 1) * tread)
                bevel_box(xa, xb, yy, yy + tread + 2, zt - 4, zt, "plank_grey_mat", r=0.6)
            for xs_ in (xa - 4, xb):                                                           # stringers
                y_lo, y_hi = Y0, Y1
                tube((xs_ + 2, y_lo if north else y_hi, z - 12), (xs_ + 2, y_hi if north else y_lo, z + RISERS * rise - 12), 5, "plank_dark_mat", sides=6)
            ztop = z + RISERS * rise
            # the outer rail of the flight (open side) and the inner one (the gap between flights)
            rails(xa - 6 if north else xb + 6, Y0 if north else Y1, Y1 if north else Y0, z, ztop)
            rails(xb + 6 if north else xa - 6, Y0 if north else Y1, Y1 if north else Y0, z, ztop)
            z = ztop
            if fl < FLIGHTS - 1:                                                               # landing at the turn
                ly0, ly1 = (Y1, Y1 + 100) if north else (Y0 - 100, Y0)
                for xx in range(-150, 150, 15):
                    bevel_box(xx, xx + 14, ly0, ly1, z - 4, z, "plank_grey_mat", r=0.5)
                bevel_box(-150, 150, ly0, ly1, z - 16, z - 4, "plank_dark_mat", r=0.8)
                edge = ly1 + 4 if north else ly0 - 4
                for h in (45, 92):
                    tube((-156, edge, z + h), (156, edge, z + h), 2.2, "plank_grey_mat", sides=6)
                for xx in (-156, 0, 156):
                    bevel_box(xx - 3, xx + 3, edge - 3, edge + 3, z - 10, z + 94, "plank_dark_mat", r=0.6)
                # side rails of the landing
                for xx in (-156, 156):
                    for h in (45, 92):
                        tube((xx, ly0, z + h), (xx, ly1, z + h), 2.2, "plank_grey_mat", sides=6)
        # the cabin floor with the stairwell opening (x -156..156, y Y0-4..Y1+104), railing round it
        F = TOWER_FL
        WELL = (-158, 158, Y0 - 6, Y1 + 106)
        for xx in range(-250, 250, 16):
            for (ya, yb) in ((-250, WELL[2]), (WELL[3], 250)):
                bevel_box(xx, xx + 15, ya, yb, F - 4, F, "plank_grey_mat", r=0.5)
            if xx + 16 <= WELL[0] or xx >= WELL[1]:
                bevel_box(xx, xx + 15, WELL[2], WELL[3], F - 4, F, "plank_grey_mat", r=0.5)
        for xx in (-250, 234):                                                # joists (none across the well)
            bevel_box(xx, xx + 16, -250, 250, F - 22, F - 4, "plank_dark_mat", r=0.8)
        for ya, yb in ((-250, WELL[2]), (WELL[3], 250)):
            bevel_box(-250, 250, ya, ya + 16, F - 22, F - 4, "plank_dark_mat", r=0.8)
        for h in (45, 92):                                                    # railing round the well,
            tube((WELL[0], WELL[2], F + h), (WELL[0], WELL[3], F + h), 2.2, "plank_grey_mat", sides=6)
            tube((WELL[0], WELL[3], F + h), (WELL[1], WELL[3], F + h), 2.2, "plank_grey_mat", sides=6)
            tube((WELL[1], WELL[3], F + h), (WELL[1], 40, F + h), 2.2, "plank_grey_mat", sides=6)
            tube((WELL[0], WELL[2], F + h), (40, WELL[2], F + h), 2.2, "plank_grey_mat", sides=6)   # open where you arrive
        for (px, py) in ((WELL[0], WELL[2]), (WELL[0], WELL[3]), (WELL[1], WELL[3]), (WELL[1], 40), (40, WELL[2])):
            bevel_box(px - 3, px + 3, py - 3, py + 3, F, F + 94, "plank_dark_mat", r=0.6)
        # cabin: wainscot boards, a band of windows all round, posts, a pyramid roof
        IN_ROOM[0] = True
        EAVE = F + 240
        for (axis, fixed) in (("x", -250), ("x", 250), ("y", -250), ("y", 250)):
            board_wall(axis, fixed, -250, 250, F - 20, lambda s: F + 100, 3.0, "plank_grey_mat", seed=int(fixed) + (1 if axis == "x" else 2))
            board_wall(axis, fixed, -250, 250, F + 205, lambda s: EAVE, 3.0, "plank_grey_mat", seed=int(fixed) + 7, batten=False)
            for k in range(5):                                                # window mullions and sills
                s = -250 + k * 125
                if axis == "x":
                    bevel_box(s - 5, s + 5, fixed - 5, fixed + 5, F + 100, F + 205, "plank_dark_mat", r=0.8)
                else:
                    bevel_box(fixed - 5, fixed + 5, s - 5, s + 5, F + 100, F + 205, "plank_dark_mat", r=0.8)
            if axis == "x":
                bevel_box(-250, 250, fixed - 9, fixed + 9, F + 98, F + 103, "plank_dark_mat", r=0.8)
            else:
                bevel_box(fixed - 9, fixed + 9, -250, 250, F + 98, F + 103, "plank_dark_mat", r=0.8)
        # a few panes of old glass left, most broken
        for (cx_, cy_, ax) in ((-187, 250, "x"), (63, -250, "x"), (250, 187, "y")):
            if ax == "x":
                rbevel(cx_, cy_, F + 152, 112, 0.6, 96, "seeglass_cabin_mat", r=0.2)
            else:
                rbevel(cx_, cy_, F + 152, 0.6, 112, 96, "seeglass_cabin_mat", r=0.2)
        # the table by the north-west window with a logbook and binoculars (a clue goes here later)
        tx, ty = -205, 205
        bevel_box(tx - 30, tx + 30, ty - 30, ty + 30, F + 74, F + 78, "wood_mat", r=0.8)
        for dx in (-26, 26):
            for dy in (-26, 26):
                bevel_box(tx + dx - 2, tx + dx + 2, ty + dy - 2, ty + dy + 2, F, F + 74, "wood_mat", r=0.5)
        rbevel(tx - 8, ty - 6, F + 79, 22, 30, 2.5, "book_green_mat", r=0.4, yaw=12)
        for s in (-1, 1):
            tube((tx + 12 + s * 3.5, ty + 8, F + 81), (tx + 12 + s * 3.5, ty + 22, F + 81), 2.4, "trim_mat", sides=10)
        cobweb((-245, -245), 1, 1, 50, EAVE - 4)
        IN_ROOM[0] = False
        ang = math.degrees(math.atan2(120, 280))
        for s in (-1, 1):                                                     # pyramid roof as four sloped panels
            rbevel(0, s * 140, EAVE + 60, 560, 310, 3, "shingle_mat", r=0.6, tilt_y=s * ang)
            rbevel(s * 140, 0, EAVE + 61.5, 310, 560, 3, "shingle_mat", r=0.6, tilt_x=-s * ang)
        tube((0, 0, EAVE + 115), (0, 0, EAVE + 175), 1.2, "rusty_tool_mat", sides=6)        # lightning rod
        bevel_box(-252, 252, -252, 252, EAVE - 6, EAVE, "plank_dark_mat", r=1)


# ---------- build and export ----------

def build():
    del PARTS[:]
    del ROOM_PARTS[:]
    del DOORS[:]
    cmds.file(new=True, force=True)
    for name, rgb in list(MATS.items()) + list(LAKE_MATS.items()) + list(BLD_MATS.items()) + list(TRAIL_MATS.items()):
        material(name, rgb)
    fence()
    shack()
    rusted_car()
    tower()
    road_closed()
    meshes = {}
    for name, parts in (("set_trail", PARTS), ("set_trail_rooms", ROOM_PARTS)):
        m = cmds.polyUnite(parts, name=name, constructionHistory=False)[0]
        cmds.delete(m, constructionHistory=True)
        cmds.xform(m, pivots=(0, 0, 0), worldSpace=True)
        meshes[name] = m
    wall = road_closed_wall()
    material("trail_block_mat", (1, 0, 1))
    cmds.sets(wall, edit=True, forceElement="trail_block_matSG")
    meshes["set_trail_block"] = cmds.rename(wall, "set_trail_block")
    lights = cmds.ls("light_*", type="transform")
    cmds.file(rename=os.path.join(ROOT, "maya", "trail_scene.ma"))
    cmds.file(save=True, type="mayaAscii")
    sets, used = {}, set()
    for name, m in meshes.items():
        f = os.path.join(OUT, name + ".fbx").replace("\\", "/")
        cmds.select(m)
        mel.eval("FBXResetExport")
        mel.eval('FBXExport -f "{}" -s'.format(f))
        sets[name] = f
        for sg in cmds.listConnections(cmds.listRelatives(m, shapes=True), type="shadingEngine") or []:
            used.update(cmds.listConnections(sg + ".surfaceShader") or [])
    g = gate_leaf("prop_gate")
    gf = os.path.join(OUT, "prop_gate.fbx").replace("\\", "/")
    cmds.select(g)
    mel.eval("FBXResetExport")
    mel.eval('FBXExport -f "{}" -s'.format(gf))
    for sg in cmds.listConnections(cmds.listRelatives(g, shapes=True), type="shadingEngine") or []:
        used.update(cmds.listConnections(sg + ".surfaceShader") or [])
    data = {"sets": sets, "room_sets": ["set_trail_rooms"], "props": {"prop_gate": gf},
            "materials": {m: list(cmds.getAttr(m + ".color")[0]) for m in sorted(used)},
            "lights": [dict(json.loads(cmds.getAttr(l + ".ue_light")), name=l,
                            position=[cmds.xform(l, q=True, t=True, ws=True)[i] for i in (0, 2, 1)]) for l in lights]}
    json.dump(data, open(os.path.join(OUT, "sets_trail.json"), "w"), indent=1)
    tris = sum(cmds.polyEvaluate(m, triangle=True) for n, m in meshes.items() if not n.endswith("_block"))
    print(f"Trail built: {tris} triangles, {len(lights)} lights; gate hinge at ({GATE_X0}, {FENCE_Y}), tower floor {TOWER_FL}")


build()

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
    traffic cones (one knocked over). Behind it, an invisible wall (road_closed_wall)."""
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
    for k, (dy, fallen) in enumerate(((-260, False), (-80, False), (180, True), (330, False))):   # cones
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
        for k in range(2):                                                    # glass shards in the side window
            rbevel(-HX, -25 + k * 30, F + 110 + k * 12, 0.6, 18, 28, "seeglass_cabin_mat", r=0.2, tilt_y=10 * k - 5)
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
        # a chopping block with an axe, a woodpile against the side wall
        frustum(150, HY + 120, 0, 45, 24, 26, "log_end_mat", sides=14)
        tube((150, HY + 120, 45), (190, HY + 140, 75), 1.6, "wood_mat", sides=6)
        rbevel(145, HY + 118, 47, 4, 14, 10, "rusty_tool_mat", r=0.6, tilt_x=-30)
        for row in range(4):
            for k2 in range(6 - row):
                y_ = -HY + 30 + k2 * 26 + row * 13
                tube((HX + 12, y_, 12 + row * 22), (HX + 70, y_ + rng.uniform(-4, 4), 12 + row * 22), 11, "log_mat", sides=8)

        # ---- inside (lighting channel 1)
        IN_ROOM[0] = True
        I = 3.0
        # the cot along the back wall with a bedroll (someone slept here), a candle stub, cans
        for xx in (-HX + 30, -HX + 210):
            for yy in (-HY + 20, -HY + 95):
                tube((xx, yy, F), (xx, yy, F + 40), 1.2, "rusty_tool_mat", sides=6)
        for yy in (-HY + 20, -HY + 95):
            tube((-HX + 30, yy, F + 40), (-HX + 210, yy, F + 40), 1.4, "rusty_tool_mat", sides=6)
        rsoft(-HX + 120, -HY + 57, F + 43, 180, 74, 6, "tarp_mat", jitter=1.0, sag=2, smooth=2, seed=2)
        quilted(-HX + 120, -HY + 57, F + 46, 60, 150, 7, "sleeping_bag_mat", baffles=8, seed=3, yaw=90)
        rsoft(-HX + 45, -HY + 57, F + 56, 44, 30, 12, "wool_mat", jitter=1.5, smooth=2, seed=4)      # rolled jacket as a pillow
        # a crate as a table: candle stub, matches, empty cans, an open can with a spoon
        bevel_box(-HX + 230, -HX + 290, -HY + 20, -HY + 70, F, F + 45, "plank_grey_mat", r=1)
        frustum(-HX + 250, -HY + 40, F + 45, F + 50, 2.2, 2.2, "candle_mat", sides=10)
        rsoft(-HX + 250, -HY + 40, F + 45.5, 10, 10, 1, "candle_mat", jitter=1, smooth=1, seed=5)       # wax puddle
        rbevel(-HX + 270, -HY + 55, F + 45.8, 5, 3, 1.6, "toolbox_mat", r=0.3)
        for k in range(3):
            frustum(-HX + 235 + k * 30, -HY + 85 + k * 8, F, F + 11, 4, 4, "can_mat", sides=12, open_ends=(k != 1))
        tube((-HX + 265, -HY + 85, F + 1), (-HX + 280, -HY + 105, F + 4), 2.5, "can_mat", sides=10)    # one rolled away
        # antlers over the door (inside), the empty gun rack on the west wall, traps on nails
        rbevel(0, HY - I - 1.5, F + 225, 26, 3, 22, "wood_mat", r=1)
        for s in (-1, 1):
            base = (s * 5, HY - I - 5, F + 230)
            tip = (s * 34, HY - I - 14, F + 262)
            tube(base, tip, 1.6, "antler_mat", sides=6)
            for t, ln in ((0.35, 15), (0.6, 17), (0.85, 11)):
                p = tuple(base[i] + (tip[i] - base[i]) * t for i in range(3))
                tube(p, (p[0] - s * 2, p[1] - 3, p[2] + ln), 1.0, "antler_mat", sides=5)
        gx = -HX + I
        bevel_box(gx, gx + 4, 20, 150, F + 150, F + 160, "wood_mat", r=0.8)
        bevel_box(gx, gx + 4, 20, 150, F + 60, F + 68, "wood_mat", r=0.8)
        for k in range(3):
            yy = 40 + k * 45
            rbevel(gx + 7, yy, F + 166, 8, 3, 8, "wood_mat", r=0.8)                         # empty pegs
            rbevel(gx + 7, yy, F + 74, 8, 3, 8, "wood_mat", r=0.8)
        rbevel(gx + 1, 90, F + 110, 0.4, 120, 90, "mud_print_mat", r=0.1)                 # pale outline where guns hung
        for k in range(3):                                                                   # traps on the east wall
            x_ = HX - I
            y_ = -110 + k * 55
            tube((x_ + 1, y_, F + 195), (x_ - 4, y_, F + 196), 0.4, "rusty_tool_mat", sides=4)
            for kk in range(5):
                ring(x_ - 3, y_, F + 191 - kk * 3, 1.4, 0.35, "rusty_tool_mat", axis="z" if kk % 2 else "x", sides=8)
            ring(x_ - 3, y_, F + 165, 11, 0.8, "rusty_tool_mat", axis="x", sides=16)
            ring(x_ - 4, y_, F + 165, 11, 0.8, "rusty_tool_mat", axis="x", sides=16)
        # a stretched pelt on a hoop frame by the stove
        ring(HX - 9, 60, F + 120, 30, 1.0, "wood_mat", axis="x", sides=18)
        rbevel(HX - 9, 60, F + 120, 1.0, 46, 50, "pelt_mat", r=0.3)
        # the little wood stove the pipe comes out of
        bevel_box(HX - 95, HX - 25, -HY + 25, -HY + 95, F + 14, F + 60, "stove_mat", r=2)
        for xx in (HX - 90, HX - 30):
            for yy in (-HY + 30, -HY + 90):
                tube((xx, yy, F), (xx, yy, F + 14), 1.5, "stove_mat", sides=6)
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
        # a fallen branch leaning against the driver's side, dead leaves drifted against the wheels
        tube((-230, -30, 0), (-100, 40, 88), 5, "bark_mat", sides=8)
        tube((-160, 8, 47), (-170, 60, 95), 2.2, "bark_mat", sides=5)
        tube((-130, 24, 68), (-150, -20, 120), 1.8, "bark_mat", sides=5)
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

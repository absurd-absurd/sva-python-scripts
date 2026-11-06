"""The boathouse and the three cabins at Black Hollow Lake. exec'd by make_lake.py (uses its
helpers, shore_y / ground_z, rng_l and the motel's shape helpers). Positions are Unreal cm.

Boathouse: rotting, padlocked (needs the boathouse key), and inside someone has been here
recently: a lit lantern, a new coil of rope, an open toolbox, muddy footprints, a tarp pulled back.
Cabins: two boarded up (outside only), cabin 2 open, with its inside dressed (Cas slept here).
Everything inside a building is built with IN_ROOM on: it goes into set_lake_rooms, which is on
lighting channel 1 like the motel rooms, so the moon never lights the insides; only the
flashlight and the lights placed in there do.
"""

BLD_MATS = {
    "plank_grey_mat": (0.25, 0.23, 0.2), "plank_dark_mat": (0.1, 0.09, 0.08), "roof_tin_mat": (0.24, 0.14, 0.09),
    "shingle_mat": (0.11, 0.1, 0.09), "log_mat": (0.22, 0.16, 0.11), "log_end_mat": (0.34, 0.27, 0.18),
    "stone_mat": (0.27, 0.26, 0.24), "life_ring_mat": (0.58, 0.32, 0.18), "lifejacket_mat": (0.5, 0.22, 0.07),
    "toolbox_mat": (0.38, 0.06, 0.04), "rope_new_mat": (0.62, 0.54, 0.36), "tarp_mat": (0.12, 0.17, 0.23),
    "mattress_mat": (0.38, 0.34, 0.27), "sleeping_bag_mat": (0.1, 0.19, 0.13), "backpack_mat": (0.28, 0.09, 0.07),
    "stove_mat": (0.06, 0.06, 0.06), "can_mat": (0.36, 0.34, 0.31), "rug_mat": (0.3, 0.17, 0.11),
    "candle_mat": (0.7, 0.66, 0.55), "seeglass_cabin_mat": (0.12, 0.14, 0.13), "rusty_tool_mat": (0.2, 0.11, 0.07),
    "boat_old_mat": (0.16, 0.17, 0.15), "mud_print_mat": (0.06, 0.05, 0.04),
}

BH_X, BH_Y = -3500.0, 14450.0          # boathouse: land wall at BH_Y - 500, lake wall at BH_Y + 650
BH_FL = 16.0                           # floor, level with the dock
BH_W, BH_S, BH_N = 400.0, -500.0, 650.0
SLIP = 172.0                           # half width of the boat slip (open water)
CABINS = [(-6500, 13150, 5, False), (5000, 13000, -8, True), (7500, 12400, 15, False)]   # x, y, yaw, open
CAB_FL = 40.0
DOORS = []                             # (id, shape, world x, y, z, yaw) for clues.json


class Placed:
    """Build at the origin (local coords), then turn by yaw and move to (cx, cy): everything made
    inside the with-block, in both PARTS and ROOM_PARTS."""
    def __init__(self, cx, cy, yaw):
        self.cx, self.cy, self.yaw = cx, cy, yaw

    def __enter__(self):
        self.n, self.m = len(PARTS), len(ROOM_PARTS)
        return self

    def world(self, lx, ly):
        a = math.radians(self.yaw)
        return (self.cx + lx * math.cos(a) - ly * math.sin(a), self.cy + lx * math.sin(a) + ly * math.cos(a))

    def __exit__(self, *exc):
        new = PARTS[self.n:] + ROOM_PARTS[self.m:]
        if not new:
            return
        g = cmds.group(new, name="placed_grp")
        cmds.rotate(0, -self.yaw, 0, g, pivot=(0, 0, 0))
        cmds.move(self.cx, 0, self.cy, g, relative=True)
        kids = cmds.ungroup(g)


# ---------- building pieces ----------

def board_wall(axis, fixed, s0, s1, z0, ztop, t, mat, openings=(), missing=0.0, bw=21.0, batten=True, seed=0):
    """A wall of vertical boards (board and batten) along x (axis 'x', at y = fixed) or along y.
    ztop(s) gives the top at that point (a gable). openings: (s0, s1, zlo, zhi) holes.
    missing: the chance a board has rotted away."""
    r = random.Random(seed)
    s = s0
    while s < s1 - 0.5:
        e = min(s1, s + bw)
        if r.random() >= missing:
            top = ztop((s + e) / 2.0) + r.uniform(-1.5, 1.5)
            spans = [(z0 + r.uniform(-1, 1), top)]
            for a, b, zlo, zhi in openings:
                if e > a and s < b:
                    nxt = []
                    for p, q in spans:
                        if zlo > p:
                            nxt.append((p, min(q, zlo)))
                        if zhi < q:
                            nxt.append((max(p, zhi), q))
                    spans = nxt
            off = r.uniform(-0.3, 0.3)
            for p, q in spans:
                if q - p < 2:
                    continue
                m_ = mat if r.random() > 0.25 else "plank_dark_mat"
                if axis == "x":
                    bevel_box(s - 0.3, e + 0.3, fixed - t / 2 + off, fixed + t / 2 + off, p, q, m_, r=0.5)
                else:
                    bevel_box(fixed - t / 2 + off, fixed + t / 2 + off, s - 0.3, e + 0.3, p, q, m_, r=0.5)
                if batten and e < s1 - 1:                                  # a batten over the seam, both faces
                    for side in (-1, 1):
                        f0 = fixed + side * (t / 2 + 0.9)
                        f1 = fixed + side * (t / 2 + 2.4)
                        lo, hi = min(f0, f1), max(f0, f1)
                        if axis == "x":
                            bevel_box(e - 2.5, e + 2.5, lo, hi, p + 1, q - 1, "plank_dark_mat", r=0.4)
                        else:
                            bevel_box(lo, hi, e - 2.5, e + 2.5, p + 1, q - 1, "plank_dark_mat", r=0.4)
        s = e


def frame(axis, fixed, a, b, zlo, zhi, out, mat="plank_dark_mat", t=4.0, w=9.0):
    """Trim boards round an opening, standing out `out` cm from the wall line (sign = side)."""
    y0, y1 = (fixed + out, fixed + out + math.copysign(t, out)) if out else (fixed - t / 2, fixed + t / 2)
    y0, y1 = min(y0, y1), max(y0, y1)
    pieces = [(a - w, a, zlo, zhi + w), (b, b + w, zlo, zhi + w), (a - w, b + w, zhi, zhi + w)]
    if zlo > 20:
        pieces.append((a - w - 4, b + w + 4, zlo - w, zlo))
    for p0, p1, q0, q1 in pieces:
        if axis == "x":
            bevel_box(p0, p1, y0, y1, q0, q1, mat, r=0.6)
        else:
            bevel_box(y0, y1, p0, p1, q0, q1, mat, r=0.6)


def plank_boards_over(axis, fixed, a, b, zlo, zhi, out, seed):
    """Boards nailed across an opening (boarded up), slightly crooked, with a dark backing so
    you never see into an empty house."""
    r = random.Random(seed)
    if axis == "x":
        bevel_box(a, b, fixed - 1, fixed + 1, zlo, zhi, "plank_dark_mat", r=0.3)
    else:
        bevel_box(fixed - 1, fixed + 1, a, b, zlo, zhi, "plank_dark_mat", r=0.3)
    n = max(2, int((zhi - zlo) / 34))
    for k in range(n):
        z = zlo + (k + 0.5) * (zhi - zlo) / n + r.uniform(-4, 4)
        L = (b - a) + 26
        c = (a + b) / 2.0 + r.uniform(-5, 5)
        tilt = r.uniform(-9, 9)
        if axis == "x":
            rbevel(c, fixed + out, z, L, 2.5, 17, "plank_grey_mat", r=0.5, tilt_x=tilt)
        else:
            rbevel(fixed + out, c, z, 2.5, L, 17, "plank_grey_mat", r=0.5, tilt_y=tilt)


def plank_door(width, height, name, lock=False):
    """A plank door built at its hinge (x 0 .. width, outside facing +y): vertical boards, a Z
    brace on the inside, strap hinges, a latch; lock=True adds a hasp and a new padlock."""
    keep_parts = PARTS[:]
    del PARTS[:]
    r = random.Random(len(name))
    n = 5
    w = width / n
    for k in range(n):
        bevel_box(k * w + 0.3, (k + 1) * w - 0.3, -2.0, 2.0, r.uniform(0, 1.5), height - r.uniform(0, 2), "plank_grey_mat" if k % 2 else "plank_dark_mat", r=0.5)
    for z in (30, height - 30):                                          # ledges (inside)
        bevel_box(4, width - 4, -4.5, -2.0, z - 8, z + 8, "plank_dark_mat", r=0.6)
    L = math.hypot(width - 16, height - 76)
    rbevel(width / 2.0, -3.2, height / 2.0, L, 2.4, 14, "plank_dark_mat", r=0.6, tilt_x=math.degrees(math.atan2(height - 76, width - 16)))
    for z in (30, height - 30):                                          # strap hinges (outside)
        bevel_box(-1.0, 42, 2.0, 2.8, z - 3, z + 3, "rusty_tool_mat", r=0.3)
        for bx in (8, 22, 36):
            sphere(bx, 3.0, z, 0.8, "rusty_tool_mat", sides=6)
    kx = width - 12
    bevel_box(kx - 2, kx + 2, 2.0, 4.0, 95, 118, "rusty_tool_mat", r=0.5)  # pull handle
    tube((kx, 4.0, 98), (kx, 6.5, 100), 0.8, "rusty_tool_mat", sides=6)
    tube((kx, 6.5, 100), (kx, 6.5, 113), 0.8, "rusty_tool_mat", sides=6)
    tube((kx, 6.5, 113), (kx, 4.0, 115), 0.8, "rusty_tool_mat", sides=6)
    if lock:                                                             # hasp + padlock (new, bright)
        bevel_box(width - 22, width + 6, 2.0, 3.0, 128, 136, "metal_mat", r=0.3)
        ring(width - 6, 4.8, 124, 2.6, 0.5, "metal_mat", axis="y", sides=12)
        bevel_box(width - 10, width - 2, 3.5, 6.5, 111, 121, "brass_mat", r=1.0)
        ring(width - 6, 5.0, 122.5, 2.3, 0.55, "chrome_mat", axis="y", sides=12)
    mesh = cmds.polyUnite(PARTS, name=name, ch=False)[0]
    cmds.delete(mesh, constructionHistory=True)
    cmds.xform(mesh, pivots=(0, 0, 0), worldSpace=True)
    del PARTS[:]
    PARTS.extend(keep_parts)
    return mesh


def cobweb_at(x, y, ax, ay, size, z):
    cobweb((x, y), ax, ay, size, z)


# ---------- boathouse ----------

def boat_hull(L, W, out_mat, in_mat, seats=3):
    """An open wooden rowboat at the origin (keel at z 0, length along y), returns nothing:
    its pieces are in PARTS / ROOM_PARTS."""
    def hull(u):
        end = min(u, 1 - u)
        k = math.sin(math.pi * min(0.5, end + (0.12 if u < 0.5 else 0.0))) ** 0.6
        rise = 10 * max(0.0, (0.15 - (1 - u)) / 0.15) ** 2
        return 0.0, 40 + rise, W / 2 * k * 0.5, W / 2 * k
    _shaped(0, 0, L, W, hull, out_mat, sx=10, sy=6, sz=36, smooth=2)
    def inner(u):
        b, t, w0, w1 = hull(u)
        return b + 4, t + 0.6, max(0.5, w0 - 3), max(0.5, w1 - 3)
    _shaped(0, 0, L - 14, W, inner, in_mat, sx=10, sy=6, sz=36, smooth=2)
    for s_ in (-1, 1):
        pts = [(s_ * hull(k / 20.0)[3], (k / 20.0 - 0.5) * L, hull(k / 20.0)[1] + 0.5) for k in range(21)]
        for p0, p1 in zip(pts, pts[1:]):
            tube(p0, p1, 2.0, "plank_dark_mat", sides=8)
    for u in [0.22, 0.5, 0.78][:seats]:
        b, t, w0, w1 = hull(u)
        rbevel(0, (u - 0.5) * L, t - 8, 2 * w1 - 6, 24, 3, "plank_grey_mat", r=0.6)


def boathouse():
    X, Y, F = BH_X, BH_Y, BH_FL
    W, S, N = BH_W, BH_S, BH_N
    EAVE, RISE = F + 284, 170.0
    gable = lambda x: EAVE + RISE * (1 - abs(x - X) / W)
    # floor: the landward end full width, then a walkway down each side of the slip
    def deck(x0, x1, y0, y1, seed):
        r = random.Random(seed)
        y = y0
        while y < y1 - 6:
            if r.random() > 0.03:
                bevel_box(x0 + r.uniform(-1, 1), x1 + r.uniform(-1, 1), y + 0.5, y + 14.5, F - 3.2 + r.uniform(-0.4, 0.4), F - 0.2,
                          "dock_wood_mat" if r.random() > 0.3 else "dock_dark_mat", r=0.5)
            y += 15
        for xx in (x0 + 10, (x0 + x1) / 2.0, x1 - 10):                   # joists
            bevel_box(xx - 5, xx + 5, y0, y1, F - 20, F - 3.4, "dock_dark_mat", r=0.8)
        for k in range(int((y1 - y0) / 220) + 2):                         # posts down to the ground / lake bed
            yy = min(y1 - 10, y0 + 10 + k * 220)
            for xx in (x0 + 10, x1 - 10):
                gz = ground_z(xx, yy)
                if gz < F - 25:
                    frustum(xx, yy, gz - 30, F - 18, 11, 10, "dock_dark_mat", sides=10)
    deck(X - W + 4, X + W - 4, Y + S + 4, Y - 150, 1)
    deck(X - W + 4, X - SLIP, Y - 150, Y + N - 4, 2)
    deck(X + SLIP, X + W - 4, Y - 150, Y + N - 4, 3)
    for s in (-1, 1):                                                     # slip edge beams (wet, dark)
        bevel_box(X + s * SLIP - 7, X + s * SLIP + 7, Y - 150, Y + N, F - 22, F + 2, "dock_dark_mat", r=1.0)
    bevel_box(X - SLIP, X + SLIP, Y - 157, Y - 143, F - 22, F + 2, "dock_dark_mat", r=1.0)
    # walls: grey boards and battens, rotten boards missing on the lake side
    door = (X - 56, X + 56, F - 1, F + 233)
    board_wall("x", Y + S, X - W, X + W, F - 22, gable, 3.0, "plank_grey_mat",
               openings=[door, (X + 200, X + 290, F + 110, F + 190)], seed=11)
    board_wall("x", Y + N, X - W, X + W, F - 22, gable, 3.0, "plank_grey_mat",
               openings=[(X - SLIP, X + SLIP, F - 60, F + 250)], missing=0.05, seed=12)
    board_wall("y", X - W, Y + S, Y + N, F - 22, lambda s: EAVE, 3.0, "plank_grey_mat",
               openings=[(Y + 80, Y + 190, F + 110, F + 190)], missing=0.04, seed=13)
    board_wall("y", X + W, Y + S, Y + N, F - 22, lambda s: EAVE, 3.0, "plank_grey_mat",
               openings=[(Y + 330, Y + 390, F - 30, F + 150)], missing=0.08, seed=14)   # a rotted-out hole
    frame("x", Y + S, X - 56, X + 56, F, F + 233, -1.6)
    frame("x", Y + S, X + 200, X + 290, F + 110, F + 190, -1.6)
    plank_boards_over("x", Y + S, X + 200, X + 290, F + 110, F + 190, -3.5, seed=5)
    frame("y", X - W, Y + 80, Y + 190, F + 110, F + 190, -1.6)
    for k in range(3):                                                    # glass shards left in the west window
        rbevel(X - W, Y + 90 + k * 38, F + 115 + (k % 2) * 30, 0.6, 22, 30 - k * 6, "seeglass_cabin_mat", r=0.2, tilt_y=12 * k - 10)
    # corner posts and the eave plates
    for xx in (X - W, X + W):
        for yy in (Y + S, Y + N):
            bevel_box(xx - 7, xx + 7, yy - 7, yy + 7, F - 30, EAVE, "dock_dark_mat", r=1.0)
    for xx in (X - W, X + W):
        bevel_box(xx - 6, xx + 6, Y + S, Y + N, EAVE - 10, EAVE + 2, "dock_dark_mat", r=1.0)
    # the boat doors on the lake end: one hanging open on a broken hinge, one fallen in the water
    rbevel(X - SLIP - 70, Y + N + 85, F + 110, 6, 165, 230, "plank_grey_mat", r=0.8, yaw=8, tilt_x=4)
    rbevel(X + 90, Y + N + 70, WATER_Z + 6, 175, 220, 5, "plank_dark_mat", r=0.8, yaw=-14, tilt_y=-9, tilt_x=5)
    bevel_box(X - SLIP, X + SLIP, Y + N - 6, Y + N + 6, F + 250, F + 266, "dock_dark_mat", r=1.0)    # header over the slip
    # roof: rusted tin in strips down each slope, sagging in the middle, a hole near the lake end
    run = W + 22
    L = math.hypot(run, RISE * run / W)
    ang = math.degrees(math.atan2(RISE, W))
    y = Y + S - 25
    k = 0
    while y < Y + N + 25:
        t = (y - (Y + S)) / (N - S)
        sag = 14 * math.sin(math.pi * max(0.0, min(1.0, t)))
        for s in (-1, 1):
            if s > 0 and 0.72 < t < 0.86:
                continue                                                  # the hole
            loose = 8 if (s < 0 and k == 3) else 0
            rbevel(X + s * run / 2.0, y + 46, EAVE + RISE / 2.0 - (22 * RISE / W) / 2.0 - sag + 2.5 + loose,
                   L, 94, 1.4, "roof_tin_mat", r=0.4, tilt_x=-s * ang + (s * 3 if loose else 0))
            for c in range(6):                                            # corrugation ribs
                f = (c + 0.5) / 6
                rbevel(X + s * run / 2.0, y + 2 + f * 92, EAVE + RISE / 2.0 - (22 * RISE / W) / 2.0 - sag + 4.0 + loose,
                       L, 3, 1.4, "roof_tin_mat", r=0.4, tilt_x=-s * ang + (s * 3 if loose else 0))
        y += 92
        k += 1
    tube((X, Y + S - 25, EAVE + RISE + 3), (X, Y + N + 25, EAVE + RISE + 3), 5, "rusty_tool_mat", sides=8)   # ridge cap
    # a sign over the door, mostly flaked
    rbevel(X, Y + S - 3, F + 262, 150, 2.5, 28, "plank_dark_mat", r=0.6)

    IN_ROOM[0] = True
    for k in range(5):                                                    # tie beams under the roof
        yy = Y + S + 60 + k * (N - S - 120) / 4.0
        bevel_box(X - W + 6, X + W - 6, yy - 6, yy + 6, EAVE - 22, EAVE - 8, "dock_dark_mat", r=1.0)
    # workbench on the west wall, landward end
    bx0, bx1, by0, by1, bz = X - W + 5, X - W + 80, Y + S + 30, Y + S + 270, F + 90
    bevel_box(bx0, bx1, by0, by1, bz - 6, bz, "dock_wood_mat", r=0.8)
    bevel_box(bx0 + 4, bx1 - 4, by0 + 6, by1 - 6, F + 22, F + 26, "dock_dark_mat", r=0.6)
    for xx in (bx0 + 5, bx1 - 5):
        for yy in (by0 + 5, by1 - 5):
            bevel_box(xx - 4, xx + 4, yy - 4, yy + 4, F, bz - 6, "dock_dark_mat", r=0.6)
    bevel_box(bx1 - 14, bx1 + 2, by0 + 20, by0 + 34, bz, bz + 12, "rusty_tool_mat", r=1.0)   # vise
    bevel_box(bx1 - 4, bx1 + 6, by0 + 18, by0 + 36, bz + 12, bz + 22, "rusty_tool_mat", r=1.0)
    tube((bx1 + 6, by0 + 27, bz + 6), (bx1 + 16, by0 + 27, bz + 6), 1.0, "rusty_tool_mat", sides=6)
    tube((bx0 + 30, by0 + 70, bz + 1.6), (bx0 + 34, by0 + 100, bz + 1.6), 1.3, "plank_grey_mat", sides=8)   # hammer
    rbevel(bx0 + 29, by0 + 68, bz + 2.6, 12, 3.5, 3.5, "rusty_tool_mat", r=0.6, yaw=8)
    rbevel(bx0 + 50, by0 + 120, bz + 1.0, 4, 26, 1.0, "rusty_tool_mat", r=0.3, yaw=-20)        # wrench
    frustum(bx0 + 20, by0 + 150, bz, bz + 17, 7, 7, "can_mat", sides=14, open_ends=False)     # coffee can of nails
    rbevel(X - W + 2.5, by0 + 120, bz + 70, 1.2, 70, 18, "rusty_tool_mat", r=0.3, tilt_y=-4)  # saw on the wall
    rbevel(X - W + 3.5, by0 + 82, bz + 74, 4, 14, 9, "plank_dark_mat", r=1.5)
    # the open toolbox (red, newer than everything else)
    tx, ty = bx0 + 40, by1 - 50
    bevel_box(tx - 24, tx + 24, ty - 11, ty + 11, bz, bz + 20, "toolbox_mat", r=1.2)
    rbevel(tx, ty + 15, bz + 26, 48, 2, 22, "toolbox_mat", r=0.8, tilt_y=-62)
    bevel_box(tx - 20, tx + 20, ty - 9, ty + 9, bz + 14, bz + 17, "rusty_tool_mat", r=0.6)
    tube((tx - 8, ty - 3, bz + 18), (tx + 12, ty + 4, bz + 19), 0.9, "metal_mat", sides=6)
    # the kerosene lantern, still burning low
    lx, ly = bx0 + 35, by0 + 200
    frustum(lx, ly, bz, bz + 4, 7, 7.5, "rusty_tool_mat", sides=14)
    frustum(lx, ly, bz + 4, bz + 18, 5, 5.5, "glow_lamp_mat", sides=14)
    frustum(lx, ly, bz + 18, bz + 24, 7, 3, "rusty_tool_mat", sides=14)
    ring(lx, ly, bz + 30, 4.5, 0.4, "rusty_tool_mat", axis="x", sides=12)
    light("light_boathouse_lantern", lx, ly, bz + 14, [1.0, 0.62, 0.3], 5, 520, room=True)
    # life jackets on hooks, life rings, oars against the wall
    for k, yy in enumerate((Y + 40, Y + 120)):
        tube((X - W + 3, yy, F + 205), (X - W + 9, yy, F + 207), 0.8, "rusty_tool_mat", sides=6)
        rsoft(X - W + 13, yy, F + 175, 14, 44, 55, "lifejacket_mat", jitter=1.5, smooth=2, seed=k, tilt_y=3 * k)
    ring(X + W - 5, Y + 230, F + 170, 30, 7, "life_ring_mat", axis="x", sides=24)
    ring(X - 150, Y + S + 5, F + 190, 30, 7, "life_ring_mat", axis="y", sides=24)
    for k in range(2):
        a = (X + W - 30 - k * 20, Y + S + 40, F)
        b = (X + W - 10 - k * 18, Y + S + 25, F + 230)
        tube(a, b, 2.3, "plank_grey_mat", sides=8)
        rbevel(a[0] + 2, a[1] + 1, F + 30, 3, 15, 55, "plank_grey_mat", r=0.8, yaw=0)
    # a crate with the tarp pulled half off it, in the corner
    cx, cy = X + W - 70, Y + S + 120
    bevel_box(cx - 45, cx + 45, cy - 35, cy + 35, F, F + 62, "dock_wood_mat", r=1.5)
    rsoft(cx - 10, cy + 6, F + 63, 70, 74, 10, "tarp_mat", jitter=4, sag=-3, smooth=2, seed=4)
    rsoft(cx - 62, cy + 30, F + 3, 70, 90, 12, "tarp_mat", jitter=6, smooth=2, seed=5, yaw=24)
    # the new rope, coiled on the east walkway
    for k in range(5):
        ring(X + SLIP + 70, Y + 60, F + 1.6 + k * 1.6, 17 - k * 1.4, 1.4, "rope_new_mat", sides=22)
    tube((X + SLIP + 87, Y + 60, F + 2), (X + SLIP + 8, Y + 140, F + 2), 1.4, "rope_new_mat", sides=8)
    # muddy footprints: in at the door, to the slip, along the east walkway
    path = [(X + 10, Y + S + 20), (X + 40, Y - 240), (X + SLIP + 60, Y - 140), (X + SLIP + 70, Y + 40)]
    step = 0
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        yaw = math.degrees(math.atan2(y1 - y0, x1 - x0)) - 90
        n = int(d / 34)
        for i in range(n):
            t = i / float(n)
            side = 1 if step % 2 else -1
            nx, ny = -(y1 - y0) / d, (x1 - x0) / d
            px, py = x0 + (x1 - x0) * t + nx * side * 9, y0 + (y1 - y0) * t + ny * side * 9
            rsoft(px, py, F + 0.6, 10, 26, 0.6, "mud_print_mat", smooth=1, yaw=yaw + side * 4, div=(2, 1, 3))
            step += 1
    # the half-sunk boat in the slip: stern under, bow up on the mud
    n, m = len(PARTS), len(ROOM_PARTS)
    boat_hull(340, 128, "boat_old_mat", "plank_dark_mat")
    new = PARTS[n:] + ROOM_PARTS[m:]
    g = cmds.group(new, name="sunk_grp")
    cmds.rotate(-7, 6, 5, g, pivot=(0, 0, 0))
    cmds.move(X - 10, WATER_Z - 22, Y + 260, g, relative=True)
    cmds.ungroup(g)
    # cobwebs in two top corners
    cobweb((X - W + 2, Y + S + 2), 1, 1, 46, EAVE - 2)
    cobweb((X + W - 2, Y + N - 2), -1, -1, 60, EAVE - 2)
    IN_ROOM[0] = False
    DOORS.append(("door_boathouse", "boathouse_door", X + 52, Y + S, F, 180))


# ---------- cabins (built at the origin, front porch toward +y) ----------

def log_wall(axis, fixed, s0, s1, z0, z1, openings, seed, r_=12.5):
    r = random.Random(seed)
    z = z0 + r_
    while z < z1:
        segs = [(s0, s1)]
        for a, b, zlo, zhi in openings:
            if z + r_ > zlo and z - r_ < zhi:
                nxt = []
                for p, q in segs:
                    if a > p:
                        nxt.append((p, min(q, a)))
                    if b < q:
                        nxt.append((max(p, b), q))
                segs = nxt
        for p, q in segs:
            if q - p < 4:
                continue
            j = r.uniform(-0.8, 0.8)
            if axis == "x":
                tube((p, fixed + j, z), (q, fixed + j, z), r_ + r.uniform(-0.8, 0.8), "log_mat", sides=8)
            else:
                tube((fixed + j, p, z), (fixed + j, q, z), r_ + r.uniform(-0.8, 0.8), "log_mat", sides=8)
        z += 2 * r_ - 1.0


def cabin(index, open_):
    HX, HY = 300.0, 250.0
    F = CAB_FL
    EAVE, RIDGE = 300.0, 450.0
    rng = random.Random(index * 31)
    # stone piers and a skirt board
    for x in (-HX + 15, 0, HX - 15):
        for y in (-HY + 15, 0, HY - 15):
            rsoft(x, y, F / 2.0 - 4, 34, 34, F + 6, "stone_mat", jitter=2, smooth=1, seed=int(x + y + index))
    # walls of logs with openings
    door = (-56, 56, F - 2, F + 230)
    wf = [(-235, -145, F + 95, F + 195), (145, 235, F + 95, F + 195)]
    side_w = (-45, 45, F + 95, F + 195)
    back_w = (60, 150, F + 95, F + 195)
    log_wall("x", HY, -HX - 18, HX + 18, F - 6, EAVE, [door] + wf, seed=index)
    log_wall("x", -HY, -HX - 18, HX + 18, F - 6, EAVE, [back_w], seed=index + 1)
    log_wall("y", -HX, -HY - 18, HY + 18, F - 6 + 12, EAVE, [side_w], seed=index + 2)
    log_wall("y", HX, -HY - 18, HY + 18, F - 6 + 12, EAVE, [], seed=index + 3)
    # gables: boards above the eaves on the side walls
    gab = lambda s: EAVE + (RIDGE - EAVE) * (1 - abs(s) / HY)
    for x in (-HX, HX):
        board_wall("y", x, -HY - 10, HY + 10, EAVE - 6, gab, 3.0, "plank_grey_mat", seed=index * 7 + int(x))
    # window and door trim
    for a, b, zlo, zhi in wf:
        frame("x", HY, a, b, zlo, zhi, 13.5)
    frame("y", -HX, side_w[0], side_w[1], side_w[2], side_w[3], -13.5)
    frame("x", -HY, back_w[0], back_w[1], back_w[2], back_w[3], -13.5)
    frame("x", HY, -56, 56, F, F + 230, 13.5)
    # roof: shingle courses down both slopes
    ang = math.degrees(math.atan2(RIDGE - EAVE, HY))
    for s in (-1, 1):
        run = HY + (18 if s > 0 else 55)                                  # short over the porch roof
        L = run / math.cos(math.radians(ang))
        rows = int(L / 26) + 1
        for k in range(rows):
            f = (k + 0.5) / rows
            yy = s * f * run
            zz = RIDGE - (RIDGE - EAVE) * (f * run) / HY + 4
            if not open_ and s > 0 and k == rows - 3:
                continue                                                  # a missing course
            rbevel(rng.uniform(-3, 3), yy, zz + rng.uniform(-0.5, 0.5), 2 * HX + 70, 29, 2.2, "shingle_mat", r=0.5,
                   tilt_y=s * ang + rng.uniform(-1.2, 1.2))
    tube((-HX - 35, 0, RIDGE + 7), (HX + 35, 0, RIDGE + 7), 6, "plank_dark_mat", sides=8)
    for x in (-HX - 33, HX + 33):                                          # barge boards
        for s in (-1, 1):
            run = HY + (18 if s > 0 else 55)
            tube((x, 0, RIDGE + 4), (x, s * run, RIDGE - (RIDGE - EAVE) * run / HY + 2), 3.5, "plank_dark_mat", sides=6)
    # porch: deck, posts, shed roof, railing, two steps
    PY0, PY1 = HY + 14, HY + 190
    y = PY0
    while y < PY1 - 6:
        broken = not open_ and rng.random() < 0.06
        if not broken:
            bevel_box(-HX - 10 + rng.uniform(-2, 2), HX + 10 + rng.uniform(-2, 2), y + 0.5, y + 13.5, F - 3.5, F - 0.3,
                      "plank_grey_mat" if rng.random() > 0.3 else "plank_dark_mat", r=0.5)
        y += 14
    for x in (-HX, -HX / 3.0, HX / 3.0, HX):
        bevel_box(x - 6, x + 6, PY0, PY1, F - 20, F - 3.8, "plank_dark_mat", r=0.8)
        rsoft(x, PY1 - 10, F / 2.0 - 4, 28, 28, F + 6, "stone_mat", jitter=2, smooth=1, seed=int(x) + index)
    posts = [-HX + 5, -HX / 3.0 - 70, HX / 3.0 + 70, HX - 5]
    PR_TOP, PR_DROP = 286.0, 40.0                                         # porch roof: under the main eave
    pz = lambda yy: PR_TOP - PR_DROP * (yy - HY) / (PY1 - HY)
    beam = pz(PY1 - 4) - 3
    for x in posts:
        bevel_box(x - 7, x + 7, PY1 - 18, PY1 - 4, F, beam - 12, "log_mat", r=2.0)
    pr_ang = math.degrees(math.atan2(PR_DROP, PY1 - HY))
    for k in range(9):
        f = (k + 0.5) / 9
        yy = HY + 4 + f * (PY1 - HY + 26)
        rbevel(rng.uniform(-2, 2), yy, pz(yy) + 2, 2 * HX + 40, 25, 2, "shingle_mat", r=0.5,
               tilt_y=pr_ang + rng.uniform(-1, 1))
    bevel_box(-HX - 5, HX + 5, PY1 - 18, PY1 - 4, beam - 12, beam, "log_mat", r=2.0)
    for a, b in ((posts[0], posts[1]), (posts[2], posts[3])):
        for z in (F + 45, F + 88):
            tube((a, PY1 - 11, z), (b, PY1 - 11, z), 3.0, "log_mat", sides=8)
        for x in range(int(a) + 25, int(b) - 10, 30):
            tube((x, PY1 - 11, F), (x, PY1 - 11, F + 88), 1.8, "plank_dark_mat", sides=6)
    for k, (z, dy) in enumerate(((F - 14, 32), (F - 28, 64))):            # two solid steps
        bevel_box(-70, 70, PY1 + dy - 32, PY1 + dy, z - 4, z, "plank_grey_mat", r=0.6)
        bevel_box(-68, 68, PY1 + dy - 31, PY1 + dy - 1, -2, z - 4.8, "plank_dark_mat", r=0.6)
    if not open_:
        # boarded: the door shut and boarded across, every window boarded, a stone chimney
        bevel_box(-54, 54, HY - 3, HY + 3, F, F + 228, "plank_dark_mat", r=0.6)
        for z, t in ((F + 70, 14), (F + 160, -12)):
            rbevel(0, HY + 14, z, 150, 2.5, 18, "plank_grey_mat", r=0.5, tilt_x=t)
        for a, b, zlo, zhi in wf:
            plank_boards_over("x", HY, a, b, zlo, zhi, 15.5, seed=int(a) + index)
        plank_boards_over("y", -HX, side_w[0], side_w[1], side_w[2], side_w[3], -15.5, seed=index + 9)
        plank_boards_over("x", -HY, back_w[0], back_w[1], back_w[2], back_w[3], -15.5, seed=index + 8)
        for k in range(16):                                                # the chimney
            z = k * 32
            w = 64 if z < 420 else 46
            rsoft(HX + 40 + rng.uniform(-2, 2), rng.uniform(-3, 3), z + 16, w, w, 33, "stone_mat", jitter=3, smooth=1, seed=index * 50 + k)
        # an old chair on the porch, tipped over
        rbevel(-180, HY + 90, F + 22, 44, 44, 4, "plank_grey_mat", r=0.6, tilt_x=80)
        return
    # ---- the open cabin ----
    for a, b, zlo, zhi in wf[1:]:                                         # grimy glass
        bevel_box(a, b, HY - 1, HY + 1, zlo, zhi, "seeglass_cabin_mat", r=0.2)
    bevel_box(-HX - 1, -HX + 1, side_w[0], side_w[1], side_w[2], side_w[3], "seeglass_cabin_mat", r=0.2)
    bevel_box(back_w[0], back_w[1], -HY - 1, -HY + 1, back_w[2], back_w[3], "seeglass_cabin_mat", r=0.2)
    tube((0, -HY + 50, 322), (0, -HY + 50, 395), 7, "stove_mat", sides=10)          # stove pipe out of the roof
    frustum(0, -HY + 50, 395, 404, 13, 9, "stove_mat", sides=10)
    IN_ROOM[0] = True
    I = 14.5                                                              # lining: boards inside the logs
    lin = lambda s: EAVE - 2
    board_wall("x", HY - I, -HX + I, HX - I, F - 1, lin, 2.0, "plank_grey_mat", openings=[door] + wf, seed=index + 40)
    board_wall("x", -HY + I, -HX + I, HX - I, F - 1, lin, 2.0, "plank_grey_mat", openings=[back_w], seed=index + 41)
    gab_in = lambda s: gab(s) - 8
    board_wall("y", -HX + I, -HY + I, HY - I, F - 1, gab_in, 2.0, "plank_grey_mat", openings=[side_w], seed=index + 42)
    board_wall("y", HX - I, -HY + I, HY - I, F - 1, gab_in, 2.0, "plank_grey_mat", seed=index + 43)
    plank_boards_over("x", HY - I, wf[0][0], wf[0][1], wf[0][2], wf[0][3], -3.0, seed=index + 44)   # boarded from inside
    y = -HY + I                                                           # floor
    while y < HY - I - 4:
        bevel_box(-HX + I, HX - I, y + 0.4, y + 13.6, F - 3.5 + rng.uniform(-0.3, 0.3), F - 0.3,
                  "dock_wood_mat" if rng.random() > 0.3 else "dock_dark_mat", r=0.5)
        y += 14
    for x in (-150, 0, 150):                                              # tie beams
        bevel_box(x - 7, x + 7, -HY + I, HY - I, EAVE - 18, EAVE - 4, "plank_dark_mat", r=1.0)
    # bunk bed on the west wall: Cas's sleeping bag on the bottom bunk
    x0, x1, y0, y1 = -HX + I + 2, -HX + I + 95, -HY + I + 2, -HY + I + 205
    for x in (x0 + 4, x1 - 4):
        for yy in (y0 + 4, y1 - 4):
            bevel_box(x - 4, x + 4, yy - 4, yy + 4, F, F + 210, "plank_dark_mat", r=0.8)
    for z in (F + 38, F + 150):
        for x in (x0, x1 - 6):
            bevel_box(x, x + 6, y0, y1, z, z + 12, "plank_dark_mat", r=0.8)
        for k in range(7):
            yy = y0 + 12 + k * 29
            bevel_box(x0 + 6, x1 - 6, yy, yy + 9, z + 6, z + 9, "plank_grey_mat", r=0.5)
    rsoft((x0 + x1) / 2.0, (y0 + y1) / 2.0, F + 55, 84, 196, 12, "mattress_mat", jitter=1.0, sag=-2, smooth=2, seed=3)
    rsoft((x0 + x1) / 2.0 + 2, (y0 + y1) / 2.0 + 8, F + 66, 74, 170, 11, "sleeping_bag_mat", jitter=3.5, sag=2, smooth=2, seed=6)
    rsoft((x0 + x1) / 2.0, y0 + 26, F + 72, 50, 30, 15, "clothes_a_mat", jitter=2.5, smooth=2, seed=7)   # a rolled flannel for a pillow
    rsoft((x0 + x1) / 2.0, (y0 + y1) / 2.0, F + 167, 84, 196, 11, "mattress_mat", jitter=1.5, sag=4, smooth=2, seed=8)
    for k in range(4):                                                    # ladder
        tube((x1 + 2, y1 - 20, F + 30 + k * 40), (x1 + 2, y1 - 50, F + 30 + k * 40), 1.8, "plank_dark_mat", sides=6)
    # her backpack by the bunk, flap open
    bx, by = x1 + 40, y0 + 40
    rsoft(bx, by, F + 22, 34, 24, 44, "backpack_mat", jitter=1.5, smooth=2, seed=9, yaw=20)
    rsoft(bx + 3, by + 8, F + 44, 30, 14, 6, "backpack_mat", jitter=1.0, smooth=2, seed=10, yaw=20, tilt_y=30)
    for d in (-8, 8):
        tube((bx + d, by - 12, F + 40), (bx + d - 2, by - 14, F + 4), 1.3, "strap_mat", sides=6)
    # wood stove on the back wall, rug in front
    sx0, sy0 = -40, -HY + I + 20
    bevel_box(sx0, sx0 + 80, sy0, sy0 + 58, F + 16, F + 82, "stove_mat", r=2.5)
    for x in (sx0 + 6, sx0 + 74):
        for yy in (sy0 + 6, sy0 + 52):
            frustum(x, yy, F, F + 16, 2.5, 3, "stove_mat", sides=8)
    bevel_box(sx0 + 14, sx0 + 66, sy0 + 58, sy0 + 61, F + 28, F + 66, "stove_mat", r=1.0)       # door
    tube((sx0 + 56, sy0 + 61, F + 47), (sx0 + 56, sy0 + 65, F + 47), 1.2, "rusty_tool_mat", sides=6)
    tube((sx0 + 50, sy0 + 65, F + 47), (sx0 + 62, sy0 + 65, F + 47), 1.0, "rusty_tool_mat", sides=6)
    tube((0, -HY + 50, F + 82), (0, -HY + 50, 322), 7, "stove_mat", sides=10)
    rsoft(0, -10, F + 1.0, 150, 95, 1.2, "rug_mat", jitter=0.6, smooth=1, seed=11, div=(4, 1, 3))
    # table and two chairs; the map, a torn page and the candle on it (the key: clues.json)
    tx, ty, tz = 70, 60, F + 75
    bevel_box(tx - 60, tx + 60, ty - 40, ty + 40, tz - 4, tz, "dock_wood_mat", r=1.0)
    for x in (tx - 54, tx + 54):
        for yy in (ty - 34, ty + 34):
            bevel_box(x - 3.5, x + 3.5, yy - 3.5, yy + 3.5, F, tz - 4, "plank_dark_mat", r=0.6)
    for (cx, cy, yaw) in ((tx - 10, ty - 70, 0), (tx + 95, ty + 10, 100)):
        rbevel(cx, cy, F + 45, 40, 40, 4, "plank_grey_mat", r=0.6, yaw=yaw)
        a = math.radians(yaw)
        for lx_, ly_ in ((-17, -17), (17, -17), (-17, 17), (17, 17)):
            px, py = cx + lx_ * math.cos(a) - ly_ * math.sin(a), cy + lx_ * math.sin(a) + ly_ * math.cos(a)
            bevel_box(px - 2, px + 2, py - 2, py + 2, F, F + 43, "plank_dark_mat", r=0.5)
        bxp, byp = cx + 18 * math.sin(a), cy - 18 * math.cos(a)          # the back: two posts, three slats
        for d in (-16, 16):
            px, py = bxp + d * math.cos(a), byp + d * math.sin(a)
            bevel_box(px - 2, px + 2, py - 2, py + 2, F + 47, F + 98, "plank_dark_mat", r=0.5)
        for z in (F + 62, F + 76, F + 90):
            rbevel(bxp, byp, z, 34, 2.2, 7, "plank_grey_mat", r=0.5, yaw=yaw)
    flat_picture(tx - 20, ty + 5, tz + 0.6, 38, 28, "pic_lake_map", yaw=8)
    flat_picture(tx + 30, ty - 15, tz + 0.9, 18, 24, "pic_page_2", yaw=-20)
    frustum(tx + 40, ty + 25, tz, tz + 1.2, 5, 4.5, "candle_mat", sides=12)        # wax puddle
    frustum(tx + 40, ty + 25, tz + 1.2, tz + 8, 2.2, 2.1, "candle_mat", sides=12)
    tube((tx + 40, ty + 25, tz + 8), (tx + 40, ty + 25, tz + 9.4), 0.25, "stove_mat", sides=4)
    rbevel(tx - 45, ty + 28, tz + 0.8, 5, 3.5, 1.5, "toolbox_mat", r=0.3, yaw=30)  # matchbox
    frustum(tx + 10, ty + 30, tz, tz + 9, 4, 4.4, "can_mat", sides=12)          # tin cup
    ring(tx + 15, ty + 30, tz + 5, 2.5, 0.5, "can_mat", axis="y", sides=8)
    # shelf with cans on the east wall
    sx = HX - I - 1
    bevel_box(sx - 26, sx, 40, 190, F + 150, F + 153, "plank_grey_mat", r=0.6)
    for yy in (60, 170):
        rbevel(sx - 3, yy, F + 138, 3, 3, 24, "plank_dark_mat", r=0.5, tilt_y=45)
    for k, yy in enumerate((55, 75, 96, 128, 152)):
        frustum(sx - 12 + (k % 2) * 3, yy, F + 153, F + 166 - (k % 3) * 2, 4.5, 4.5, "can_mat", sides=12)
    # an unlit lamp hanging from a beam
    tube((0, 40, EAVE - 18), (0, 40, EAVE - 70), 0.4, "rusty_tool_mat", sides=4)
    frustum(0, 40, EAVE - 92, EAVE - 72, 6, 5, "glass_mat", sides=12)
    frustum(0, 40, EAVE - 72, EAVE - 66, 8, 2, "rusty_tool_mat", sides=12)
    frustum(0, 40, EAVE - 96, EAVE - 92, 7, 7, "rusty_tool_mat", sides=12)
    cobweb((-HX + I + 1.5, HY - I - 1.5), 1, -1, 50, EAVE - 20)
    cobweb((HX - I - 1.5, -HY + I + 1.5), -1, 1, 42, EAVE - 20)
    IN_ROOM[0] = False


def lake_buildings():
    for name, rgb in BLD_MATS.items():
        material(name, rgb)
    boathouse()
    for i, (cx, cy, yaw, open_) in enumerate(CABINS):
        with Placed(cx, cy, yaw) as P:
            cabin(i + 1, open_)
        if open_:
            hx, hy = P.world(-52, 250)
            DOORS.append(("door_cabin%d" % (i + 1), "plank_door", hx, hy, CAB_FL, yaw))
            kx, ky = P.world(40, 50)
            DOORS.append(("key_boathouse", "key", kx, ky, CAB_FL + 75.8, yaw + 40))
    for d in DOORS:
        print("PLACE", d)


def export_building_doors():
    made = {}
    for name, lock in (("prop_plank_door", False), ("prop_boathouse_door", True)):
        m = plank_door(104, 228, name, lock)
        f = os.path.join(OUT, name + ".fbx").replace(os.sep, "/")
        cmds.select(m)
        mel.eval("FBXResetExport")
        mel.eval('FBXExport -f "{}" -s'.format(f))
        made[name] = f
        cmds.delete(m)
    return made

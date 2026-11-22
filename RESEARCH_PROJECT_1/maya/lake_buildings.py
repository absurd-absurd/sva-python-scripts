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
    "sleeping_bag_lining_mat": (0.34, 0.12, 0.08), "zipper_mat": (0.05, 0.05, 0.05), "wool_mat": (0.2, 0.19, 0.17),
    "boot_mat": (0.24, 0.14, 0.07), "boot_sole_mat": (0.045, 0.04, 0.035), "seeglass_red_mat": (0.6, 0.05, 0.03),
    "padlock_mat": (0.62, 0.63, 0.66), "padlock_band_mat": (0.14, 0.14, 0.16), "chain_mat": (0.38, 0.37, 0.36),
    "dark_leather_mat": (0.09, 0.06, 0.04), "algae_mat": (0.06, 0.09, 0.05), "paint_can_mat": (0.3, 0.29, 0.26),
    "gas_can_mat": (0.34, 0.05, 0.03), "net_mat": (0.22, 0.2, 0.15), "float_mat": (0.45, 0.36, 0.2),
    "bottle_mat": (0.14, 0.08, 0.03), "can_label_mat": (0.42, 0.18, 0.1), "enamel_mat": (0.2, 0.3, 0.4),
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


def plank_boards_over(axis, fixed, a, b, zlo, zhi, out, seed, gaps=False):
    """Boards nailed across an opening (boarded up). Outside (toward out): crooked boards that
    overlap so no gap shows; inside: two or three more boards nailed from that side, so from
    inside it reads as boarded too (it used to be a flat dark panel), with nail heads."""
    r = random.Random(seed)
    sgn = 1 if out > 0 else -1
    def board(off, c, z, L, tilt, depth):
        if axis == "x":
            rbevel(c, fixed + off, z, L, depth, 17, "plank_grey_mat" if r.random() > 0.3 else "plank_dark_mat", r=0.5, tilt_x=tilt)
        else:
            rbevel(fixed + off, c, z, depth, L, 17, "plank_grey_mat" if r.random() > 0.3 else "plank_dark_mat", r=0.5, tilt_y=tilt)
    def nail(off, c, z):
        if axis == "x":
            sphere(c, fixed + off, z, 0.6, "rusty_tool_mat", sides=6, scale=(1, 0.4, 1))
        else:
            sphere(fixed + off, c, z, 0.6, "rusty_tool_mat", sides=6, scale=(0.4, 1, 1))
    n = int(math.ceil((zhi - zlo) / (21.0 if gaps else 14.0))) + 1        # gaps: thin slits between the boards
    for k in range(n):                                   # outside: overlapping, alternately proud
        z = zlo + 4 + k * (zhi - zlo - 8) / max(1, n - 1)
        L = (b - a) + 26
        c = (a + b) / 2.0 + r.uniform(-4, 4)
        off = out + sgn * (0.6 if k % 2 else 0.0)
        board(off, c, z, L, r.uniform(-6, 6), 2.4)
        for e in (-1, 1):
            nail(off + sgn * 1.3, c + e * (L / 2 - 5), z)
    inner = -sgn * 3.6
    for k in range(0 if gaps else (3 if zhi - zlo > 60 else 2)):   # inside: a few boards with gaps
        z = zlo + 12 + k * (zhi - zlo - 24) / 2.0
        L = (b - a) + 18
        c = (a + b) / 2.0 + r.uniform(-3, 3)
        board(inner, c, z, L, r.uniform(-8, 8), 2.4)
        for e in (-1, 1):
            nail(inner - sgn * 1.3, c + e * (L / 2 - 4), z)

def oval_link(cx, cy, cz, u, v, L=4.6, W=2.6, r=0.42, mat="chain_mat"):
    """One oval chain link centred at (cx, cy, cz): its long axis along unit vector u, its short axis along v
    (u, v are 3-tuples). Built from a closed polyline, so it reads as a real welded link."""
    pts = []
    for k in range(17):
        t = 2 * math.pi * k / 16
        a_, b_ = (L / 2 - W / 2) * (1 if math.cos(t) >= 0 else -1) + (W / 2) * math.cos(t), (W / 2) * math.sin(t)
        pts.append((cx + u[0] * a_ + v[0] * b_, cy + u[1] * a_ + v[1] * b_, cz + u[2] * a_ + v[2] * b_))
    polyline(pts, r, r, mat, sides=6)


def chain_loop(cx, cy, cz, rx, ry, n, mat="chain_mat"):
    """A chain wrapped once round something: n links on an ellipse (rx, ry) at height cz, each link turned
    along the loop and alternating flat / on edge, so neighbours interlock."""
    for k in range(n):
        t = 2 * math.pi * k / n
        x, y = cx + rx * math.cos(t), cy + ry * math.sin(t)
        tx, ty = -rx * math.sin(t), ry * math.cos(t)
        L = math.hypot(tx, ty)
        u = (tx / L, ty / L, 0.0)
        v = (0.0, 0.0, 1.0) if k % 2 else (math.cos(t), math.sin(t), 0.0)
        oval_link(x, y, cz + 0.6 * math.sin(3 * t), u, v, mat=mat)


def padlock(px, py, pz, facing=1, scale=1.0):
    """A new laminated-steel padlock, hanging: the body is a stack of pressed plates (the ridged sides real
    padlocks have), a brass keyway on the bottom, a polished U shackle out of the top. px, py: centre; pz: the
    bottom of the body; facing: +1 / -1, the side (y) its front plate faces."""
    s_ = scale
    w, d, h = 4.6 * s_, 2.5 * s_, 4.9 * s_
    for k in range(7):                                                     # the laminations
        z0 = pz + k * h / 7
        inset = 0.12 * s_ if k in (0, 6) else 0.0
        bevel_box(px - w / 2 + inset, px + w / 2 - inset, py - d / 2 + inset, py + d / 2 - inset, z0 + 0.04 * s_, z0 + h / 7 - 0.05 * s_,
                  "padlock_mat", r=0.12 * s_)
    bevel_box(px - w / 2 - 0.05, px + w / 2 + 0.05, py - d / 2 - 0.05, py + d / 2 + 0.05, pz + h * 0.42, pz + h * 0.58,
              "padlock_band_mat", r=0.1 * s_)                                # the maker's band round the middle
    frustum(px, py, pz - 0.18 * s_, pz + 0.02, 0.75 * s_, 0.8 * s_, "brass_mat", sides=14)      # keyway
    bevel_box(px - 0.12 * s_, px + 0.12 * s_, py - 0.45 * s_, py + 0.45 * s_, pz - 0.22 * s_, pz - 0.16 * s_, "char_mat", r=0.03)
    sx, top = 1.35 * s_, pz + h + 2.3 * s_                                  # the shackle
    leg = [(px - sx, py, pz + h - 0.2), (px - sx, py, top)]
    arc = [(px + sx * math.cos(math.pi - a), py, top + sx * math.sin(math.pi - a)) for a in [k * math.pi / 8 for k in range(9)]]
    polyline(leg + arc + [(px + sx, py, pz + h - 0.2)], 0.42 * s_, 0.42 * s_, "chrome_mat", sides=10)
    return top + sx                                                         # top of the shackle


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
    if lock:                                                             # hasp, staple, and a new padlock through it
        bevel_box(width - 24, width - 4, 2.0, 2.8, 127, 135, "rusty_tool_mat", r=0.3)      # hasp plate (the door's)
        for bx in (width - 20, width - 13):
            sphere(bx, 3.0, 131, 0.6, "rusty_tool_mat", sides=6)
        bevel_box(width - 6, width + 8, 2.0, 2.8, 124, 138, "rusty_tool_mat", r=0.3)       # staple plate (on the frame)
        polyline([(width - 4, 2.8, 128), (width - 4, 6.0, 128), (width - 4, 6.0, 134), (width - 4, 2.8, 134)], 0.5, 0.5,
                 "rusty_tool_mat", sides=6)                                               # the staple loop
        padlock(width - 4, 6.0, 119.5)
    mesh = cmds.polyUnite(PARTS, name=name, ch=False)[0]
    cmds.delete(mesh, constructionHistory=True)
    cmds.xform(mesh, pivots=(0, 0, 0), worldSpace=True)
    del PARTS[:]
    PARTS.extend(keep_parts)
    return mesh


def cobweb_at(x, y, ax, ay, size, z):
    cobweb((x, y), ax, ay, size, z)



# ---------- small shared props ----------

def open_hull(L, prof, out_mat, in_mat, sx=10, sy=6, sz=36, smooth=2, thick=2.5):
    """A real hollow boat hull: the outside shell with its top cut away, and a thinner inner
    shell facing inward, so you look down into the boat (prof(u) -> bottom z, top z, half width
    at the bottom, at the top; u 0 stern .. 1 bow, along y)."""
    def build(pr, mat, flip):
        c = cmds.polyCube(w=1, h=1, d=1, sx=sx, sy=sy, sz=sz, ch=False)[0]
        info = cmds.polyInfo(c, faceNormals=True)
        tops = []
        for k, line in enumerate(info):
            nx, ny, nz = (float(v) for v in line.split()[-3:])
            if ny > 0.9 * math.sqrt(nx * nx + ny * ny + nz * nz):    # (Maya gives them unnormalised)
                tops.append(k)
        pts = []
        for x, y, z in _verts(c):
            u = z + 0.5
            bz, tz, hwb, hwt = pr(u)
            h = y + 0.5
            hw = hwb + (hwt - hwb) * h
            pts.append((x * 2 * hw, bz + (tz - bz) * h, (u - 0.5) * L))
        _set_verts(c, pts)
        cmds.delete(["%s.f[%d]" % (c, k) for k in tops])
        if smooth:
            cmds.polySmooth(c, dv=smooth, ch=False)
        if flip:
            cmds.polyNormal(c, normalMode=0, userNormalMode=0, ch=False)
        cmds.polySoftEdge(c, angle=70, ch=False)
        return keep(c, mat)
    build(prof, out_mat, False)
    def inner(u):
        b, t, w0, w1 = prof(u)
        return b + thick, t, max(0.5, w0 - thick), max(0.5, w1 - thick)
    build(inner, in_mat, True)

def sole_plate(L, prof, z, mat, Ls=None):
    """A flat floor inside a hull at height z (absolute, same frame as prof): it follows the
    inside of the hull exactly, so the lake surface never shows inside a floating boat."""
    def p(u):
        b, t, w0, w1 = prof(u)
        f = lambda zz: w0 + (w1 - w0) * max(0.0, min(1.0, (zz - b) / max(1e-3, t - b)))
        return z, z + 1.4, max(0.5, f(z) - 0.4), max(0.5, f(z + 1.4) - 0.4)
    _shaped(0, 0, Ls or L, 1, p, mat, sx=4, sy=1, sz=30, smooth=0)


def quilted(cx, cy, z, w, L, h, mat, baffles=9, seed=0, lift_head=0.0, **turn):
    """A puffy quilted slab (sleeping bag body): sewn channels across it every L/baffles, the
    loft bulging between them, soft rounded edges, a few lazy wrinkles. z = what it lies on."""
    r = random.Random(seed)
    c = cmds.polyCube(w=1, h=1, d=1, sx=8, sy=2, sz=baffles * 4, ch=False)[0]
    pts = []
    for x, y, zz in _verts(c):
        u, v = x * 2, zz + 0.5                                         # u -1..1 across, v 0..1 along
        edge = max(0.0, 1 - abs(u) ** 3) ** 0.45
        chan = abs(math.sin(math.pi * v * baffles)) ** 0.55               # 0 on the seams
        loft = h * (0.62 + 0.38 * chan) * (0.3 + 0.7 * edge)
        top = y > 0
        yy = loft + r.uniform(-0.3, 0.3) + 0.6 * math.sin(v * 9 + u * 2 + seed) if top else 0.0
        yy += lift_head * max(0.0, (0.12 - v) / 0.12)
        xx = x * w * (1 - 0.06 * v)                                     # a touch narrower at the foot
        pts.append((xx + r.uniform(-0.2, 0.2), yy, (v - 0.5) * L))
    _set_verts(c, pts)
    cmds.polySmooth(c, dv=1, ch=False)
    return _place(c, cx, cy, z, mat, **turn)


def fitted_sheet(cx, cy, z_bot, w, L, h, seed):
    """A mattress in a fitted sheet: the sheet over the top and down the sides, the striped
    ticking showing along the bottom edge, a few creases."""
    rsoft(cx, cy, z_bot + h / 2.0, w, L, h, "mattress_mat", jitter=0.4, smooth=2, seed=seed)
    rsoft(cx, cy, z_bot + 2.2 + (h - 1.4) / 2.0, w + 2.4, L + 2.4, h - 1.4 + 1.0, "sheet_mat", jitter=0.7,
          sag=-0.6, smooth=2, seed=seed + 1, div=(4, 2, 8))


def polyline(points, r0, r1, mat, sides=10):
    """A tube along a polyline whose radius runs r0 -> r1, with round joints."""
    n = len(points) - 1
    for i, (a, b) in enumerate(zip(points, points[1:])):
        rr = r0 + (r1 - r0) * (i + 0.5) / n
        tube(a, b, rr, mat, sides=sides)
        if i < n - 1:
            sphere(*b, rr, mat, sides=sides)


def chain_link(px, py, pz, yaw, upright, mat="rusty_tool_mat"):
    """One oval chain link lying along yaw (degrees), flat or standing on edge."""
    t = cmds.polyTorus(r=1.7, sr=0.45, sx=14, sy=6, ch=False)[0]
    cmds.scale(1.55, 1, 1, t)
    if upright:
        cmds.rotate(90, 0, 0, t)
    cmds.rotate(0, -yaw, 0, t, relative=True, objectSpace=False)
    cmds.move(px, pz, py, t)
    return keep(t, mat)


def chain(points, mat="rusty_tool_mat", pitch=4.2):
    """A chain of alternating links along a polyline (points on the floor or hanging)."""
    k = 0
    for (x0, y0, z0), (x1, y1, z1) in zip(points, points[1:]):
        L = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2)
        yaw = math.degrees(math.atan2(y1 - y0, x1 - x0))
        n = max(1, int(L / pitch))
        for i in range(n):
            t = (i + 0.5) / n
            chain_link(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z0 + (z1 - z0) * t + (0.4 if k % 2 else 1.4), yaw, k % 2 == 0, mat)
            k += 1


def admiralty_anchor(x, y, z, yaw):
    """An old fisherman's (admiralty) anchor lying on the boards: a tapered shank, the crown,
    two curved arms ending in spade-shaped flukes with pointed bills, the stock through the top
    of the shank, the ring - with its chain running off in a loose heap."""
    with Moved(x, y, yaw):
        polyline([(x, y - 32, z + 2.4), (x, y, z + 2.6), (x, y + 30, z + 2.6)], 2.4, 1.7, "rusty_tool_mat", sides=12)   # shank
        sphere(x, y - 32, z + 2.4, 3.0, "rusty_tool_mat", sides=12)                                                    # crown
        for s_ in (-1, 1):
            arm = [(x, y - 32, z + 2.4), (x + s_ * 9, y - 33, z + 2.4), (x + s_ * 17, y - 28, z + 2.4), (x + s_ * 22, y - 19, z + 2.4)]
            polyline(arm, 2.2, 1.6, "rusty_tool_mat", sides=12)
            # the spade fluke: a flat blade on the arm's end, broad at the base, pointed at the bill
            rsoft(x + s_ * 21.5, y - 15, z + 2.4, 9.5, 14, 1.6, "rusty_tool_mat", jitter=0.1, smooth=2, seed=7 + s_,
                  yaw=-s_ * 28, div=(3, 1, 4))
            rsoft(x + s_ * 22.5, y - 10, z + 2.4, 5.5, 7, 1.4, "rusty_tool_mat", jitter=0.1, smooth=2, seed=9 + s_,
                  yaw=-s_ * 28, div=(2, 1, 3))
            sphere(x + s_ * 23, y - 9, z + 2.4, 1.4, "rusty_tool_mat", sides=8, scale=(1, 2.2, 0.7))   # bill
        polyline([(x - 24, y + 22, z + 4.4), (x + 24, y + 22, z + 4.4)], 1.6, 1.6, "rusty_tool_mat", sides=10)   # stock
        for s_ in (-1, 1):
            sphere(x + s_ * 24, y + 22, z + 4.4, 2.4, "rusty_tool_mat", sides=10)
        t = cmds.polyTorus(r=5, sr=1.0, sx=18, sy=8, ch=False)[0]                                  # ring, lying flat
        cmds.move(x, z + 1.0, y + 36, t)
        keep(t, "rusty_tool_mat")
        chain([(x, y + 41, z), (x + 6, y + 52, z), (x + 16, y + 56, z), (x + 22, y + 48, z), (x + 14, y + 42, z + 1.2),
               (x + 8, y + 50, z + 2.4), (x + 18, y + 60, z + 1.0)])


def rope_coil(x, y, z, r_out, turns, rope_r, mat, seed=0):
    """A rope coiled flat on the floor in loose loops: a spiral of tube segments, the loops
    stacking a little where they cross."""
    rng = random.Random(seed)
    pts = []
    n = int(turns * 24)
    for i in range(n + 1):
        t = i / 24.0
        a = t * 2 * math.pi
        rr = r_out - (r_out * 0.45) * (i / float(n)) + rng.uniform(-0.6, 0.6)
        zz = z + rope_r + (rope_r * 1.6) * (t % 1.0 > 0.92) + 0.15 * math.sin(a * 3)
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a), zz))
    polyline(pts, rope_r, rope_r, mat, sides=8)
    return pts[-1], pts[0]


def sag_rope(p0, p1, sag, rope_r, mat, n=12):
    """A rope hanging between two points with a catenary-like sag."""
    pts = []
    for i in range(n + 1):
        t = i / float(n)
        pts.append(tuple(p0[k] + (p1[k] - p0[k]) * t for k in range(3)))
        pts[-1] = (pts[-1][0], pts[-1][1], pts[-1][2] - sag * 4 * t * (1 - t))
    polyline(pts, rope_r, rope_r, mat, sides=8)


def life_ring(x, y, z, wall_dir=-1):
    """A cork life ring hanging on a nail, faced away from the wall: a round torus in orange
    with four white bands, its grab line looped round it and seized at four points."""
    R, rr = 29.0, 7.0
    n = 32
    def at(k, rad, off=0.0):
        a = 2 * math.pi * k / n
        return (x + wall_dir * off, y + rad * math.cos(a), z + rad * math.sin(a))
    for k in range(n):
        mat = "sheet_mat" if (k % 8) in (2, 3) else "life_ring_mat"
        tube(at(k, R), at(k + 1, R), rr, mat, sides=16)
        sphere(*at(k + 1, R), rr, mat, sides=16)
    for k in range(4):                                                           # grab line seizings
        q = at(k * 8 + 2.5, R)
        t = cmds.polyTorus(r=rr + 0.6, sr=0.55, sx=14, sy=6, ch=False)[0]
        a = 2 * math.pi * (k * 8 + 2.5) / n
        cmds.rotate(math.degrees(a), 0, 90, t)
        cmds.move(q[0], q[2], q[1], t)
        keep(t, "rope_mat")
    for k in range(4):                                                           # the line between them, sagging
        a0, a1 = (k * 8 + 2.5), ((k + 1) * 8 + 2.5)
        pts = []
        for i in range(7):
            kk = a0 + (a1 - a0) * i / 6.0
            pts.append(at(kk, R + rr + 2.5 + 3 * math.sin(math.pi * i / 6.0), wall_dir * -1.0))
        polyline(pts, 0.7, 0.7, "rope_mat", sides=6)
    tube((x - wall_dir * 2, y, z + R + rr + 2), (x + wall_dir * 5, y, z + R + rr + 3), 0.6, "rusty_tool_mat", sides=6)   # nail


def fishing_net(x_wall, nails, drop, wall_dir=-1, seed=0):
    """A fishing net hung from nails on a wall (along y): a headrope with cork floats sagging
    between the nails, a diamond mesh hanging in folds below it, a leaded footrope at the bottom."""
    rng = random.Random(seed)
    for (ya, za), (yb, zb) in zip(nails, nails[1:]):
        cols, rows = 14, 9
        grid = []
        for r_ in range(rows + 1):
            row = []
            for c_ in range(cols + 1):
                t = c_ / float(cols)
                zz = za + (zb - za) * t - 12 * math.sin(math.pi * t) - r_ * drop / rows * (1 + 0.25 * math.sin(math.pi * t))
                fold = 2.2 * math.sin(t * 9 + r_ * 0.5) * (r_ / rows)
                row.append((x_wall + wall_dir * (1.5 + abs(fold) + r_ * 0.25), ya + (yb - ya) * t + (r_ % 2) * (yb - ya) / cols / 2.0, zz))
            grid.append(row)
        polyline(grid[0], 0.55, 0.55, "rope_mat", sides=5)                          # headrope
        polyline(grid[-1], 0.6, 0.6, "rope_mat", sides=5)                           # footrope
        for r_ in range(rows):                                                      # the diamond mesh
            for c_ in range(cols):
                a_, b_ = grid[r_][c_], grid[r_ + 1][c_]
                c2 = grid[r_ + 1][c_ + 1] if r_ % 2 == 0 else grid[r_ + 1][max(0, c_ - 1)]
                tube(a_, b_, 0.22, "net_mat", sides=3)
                tube(a_, c2, 0.22, "net_mat", sides=3)
        for c_ in range(1, cols, 3):                                                # cork floats on the headrope
            p_ = grid[0][c_]
            frustum(p_[0] + wall_dir * 1.5, p_[1], p_[2] - 3.5, p_[2] + 3.5, 3.0, 3.0, "float_mat", sides=10)
        for c_ in range(0, cols + 1, 2):                                            # lead weights on the footrope
            p_ = grid[-1][c_]
            sphere(p_[0], p_[1], p_[2], 1.4, "stove_mat", sides=8, scale=(1, 1.6, 1))
    for yy, zz in nails:
        tube((x_wall - wall_dir * 1, yy, zz), (x_wall + wall_dir * 4, yy, zz), 0.5, "rusty_tool_mat", sides=4)


def cantilever_toolbox(tx, ty, z):
    """An open red cantilever toolbox: the box with a rolled lip, two tiers of trays swung out on
    their arms, the carry handle laid flat, a latch; screwdrivers, a wrench, pliers inside."""
    bevel_box(tx - 23, tx + 23, ty - 10, ty + 10, z, z + 16, "toolbox_mat", r=1.4, seg=3)
    bevel_box(tx - 21.5, tx + 21.5, ty - 8.5, ty + 8.5, z + 12, z + 16.3, "stove_mat", r=0.6)       # dark inside
    for s_ in (-1, 1):
        for tier, (dy, dz) in enumerate(((13, 17.5), (22, 23))):
            yy = ty + s_ * dy
            bevel_box(tx - 22, tx + 22, yy - 5, yy + 5, z + dz, z + dz + 5.5, "toolbox_mat", r=0.8, seg=2)
            bevel_box(tx - 20.8, tx + 20.8, yy - 3.8, yy + 3.8, z + dz + 3, z + dz + 5.6, "stove_mat", r=0.4)
            for dx in (-19, 19):                                                   # the arms
                tube((tx + dx, ty + s_ * (dy - 9), z + dz - 4), (tx + dx, yy - s_ * 3, z + dz + 1.5), 0.5, "metal_mat", sides=6)
                sphere(tx + dx, ty + s_ * (dy - 9), z + dz - 4, 0.8, "metal_mat", sides=6)
    tube((tx - 9, ty, z + 16.6), (tx + 9, ty, z + 16.6), 1.0, "dark_leather_mat", sides=8)          # handle, flat
    for dx in (-9, 9):
        bevel_box(tx + dx - 1, tx + dx + 1, ty - 1.5, ty + 1.5, z + 15.5, z + 17.2, "metal_mat", r=0.3)
    bevel_box(tx - 2.5, tx + 2.5, ty - 10.7, ty - 10, z + 11, z + 15.5, "metal_mat", r=0.3)        # latch
    yy = ty + 22                                                                    # in the top tier
    for k in range(3):                                                              # screwdrivers
        frustum(tx - 14 + k * 3.5, yy - 1, z + 28, z + 28.4, 1.2, 1.2, "toolbox_mat" if k != 1 else "enamel_mat", sides=8)
        tube((tx - 14 + k * 3.5, yy - 2, z + 28.5), (tx - 14 + k * 3.5, yy + 3, z + 28.5), 1.2, "toolbox_mat" if k != 1 else "enamel_mat", sides=8)
        tube((tx - 14 + k * 3.5, yy + 3, z + 28.5), (tx - 14 + k * 3.5, yy - 9, z + 28.4), 0.3, "metal_mat", sides=5)
    rbevel(tx + 6, ty - 22, z + 28.8, 15, 1.6, 0.6, "metal_mat", r=0.2, yaw=8)                      # wrench
    for e in (-1, 1):
        ring(tx + 6 + e * 8, ty - 22 + e * 1.1, z + 28.8, 1.6, 0.5, "metal_mat", sides=10)
    for e in (-1, 1):                                                               # pliers
        tube((tx - 8, ty - 13, z + 23.3), (tx - 2, ty - 13 + e * 2.5, z + 23.3), 0.6, "dark_leather_mat", sides=6)


def hand_drill(x, y, z, yaw):
    """An eggbeater hand drill lying on its side: the frame, the big gear wheel with spokes and
    a crank handle, the pinion, the side handle, the end knob, the chuck and a bit."""
    with Moved(x, y, yaw):
        tube((x - 12, y, z + 2.4), (x + 14, y, z + 2.4), 0.8, "metal_mat", sides=8)                   # frame shaft
        frustum(x - 16, y, z + 0.2, z + 4.6, 2.4, 2.4, "plank_grey_mat", sides=10)                   # end knob (on its side)
        t = cmds.polyTorus(r=4.5, sr=0.5, sx=20, sy=6, ch=False)[0]                                  # gear wheel
        cmds.rotate(90, 0, 0, t)
        cmds.move(x + 2, z + 2.4 + 0.2, y + 2.6, t)
        keep(t, "metal_mat")
        for k in range(4):
            a = k * math.pi / 2
            tube((x + 2, y + 2.6, z + 2.6), (x + 2 + 4.3 * math.cos(a), y + 2.6, z + 2.6 + 4.3 * math.sin(a)), 0.35, "metal_mat", sides=4)
        tube((x + 2 + 4.5, y + 2.6, z + 2.6), (x + 2 + 4.5, y + 7, z + 2.6), 0.4, "metal_mat", sides=6)   # crank
        frustum(x + 6.5, y + 7, z + 1.4, z + 3.8, 0.9, 0.9, "plank_grey_mat", sides=8)
        tube((x + 4, y - 0.8, z + 2.4), (x + 4, y - 8, z + 2.0), 1.0, "plank_grey_mat", sides=8)       # side handle
        frustum(x + 15, y, z + 1.0, z + 3.8, 1.4, 0.9, "metal_mat", sides=10)                         # chuck
        tube((x + 16, y, z + 2.4), (x + 22, y, z + 2.4), 0.25, "metal_mat", sides=5)                   # bit


def bench_vise(vx, vy, z):
    """A bench vise bolted to the corner of the bench: a swivel base with bolts, the body, a fixed
    and a sliding jaw with serrated jaw plates, the screw and a T-bar handle with ball ends, the
    little anvil on the back."""
    frustum(vx, vy, z, z + 2.2, 8.5, 8.5, "stove_mat", sides=16)
    for k in range(3):
        a = k * 2.09 + 0.5
        frustum(vx + 7 * math.cos(a), vy + 7 * math.sin(a), z + 2.2, z + 3.0, 1.2, 1.2, "metal_mat", sides=6)
    bevel_box(vx - 7, vx + 6, vy - 6, vy + 6, z + 2.2, z + 10, "stove_mat", r=1.2, seg=2)              # body
    bevel_box(vx - 12, vx - 6, vy - 5, vy + 5, z + 8, z + 11, "stove_mat", r=0.8)                      # anvil
    for xx, w_ in ((vx - 1, 3), (vx + 6, 3)):
        bevel_box(xx, xx + w_, vy - 11, vy + 11, z + 10, z + 20, "stove_mat", r=0.8, seg=2)            # jaws
    for xx in (vx + 1.9, vx + 6.0):
        bevel_box(xx, xx + 0.4, vy - 10, vy + 10, z + 14, z + 19.5, "metal_mat", r=0.1)                # jaw plates
        for k in range(10):
            bevel_box(xx - 0.05, xx + 0.45, vy - 9.5 + k * 2, vy - 9.1 + k * 2, z + 14, z + 19.5, "stove_mat", r=0.02)
    bevel_box(vx + 9, vx + 18, vy - 4, vy + 4, z + 10, z + 14, "stove_mat", r=0.8)                      # slide
    tube((vx + 9, vy, z + 15), (vx + 24, vy, z + 15), 1.0, "metal_mat", sides=10)                      # screw
    frustum(vx + 24, vy, z + 13.4, z + 16.6, 2.0, 2.0, "metal_mat", sides=10)
    tube((vx + 25, vy - 10, z + 15), (vx + 25, vy + 7, z + 15), 0.7, "metal_mat", sides=8)              # T bar
    for dy in (-10, 7):
        sphere(vx + 25, vy + dy, z + 15, 1.4, "metal_mat", sides=8)


def screw_jar(x, y, z):
    """A glass jar of screws with a ridged tin lid screwed on: screws heaped inside."""
    frustum(x, y, z, z + 13, 4.6, 4.6, "seeglass_cabin_mat", sides=18, open_ends=True)
    frustum(x, y, z, z + 0.6, 4.6, 4.6, "seeglass_cabin_mat", sides=18)
    frustum(x, y, z + 13, z + 14.2, 4.0, 4.0, "seeglass_cabin_mat", sides=18)
    frustum(x, y, z + 13.6, z + 16.0, 4.5, 4.5, "rusty_tool_mat", sides=24)
    r = random.Random(int(x + y))
    for k in range(26):
        a, rr = r.uniform(0, 6.28), r.uniform(0, 3.4)
        h_ = 1.0 + min(5.0, (3.6 - rr) * 1.6) * r.random()
        p0 = (x + rr * math.cos(a), y + rr * math.sin(a), z + 0.8 + h_)
        d = (r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-0.4, 0.4))
        tube(p0, (p0[0] + d[0] * 2, p0[1] + d[1] * 2, p0[2] + d[2] * 2), 0.25, "metal_mat", sides=4)
        sphere(*p0, 0.45, "metal_mat", sides=5, scale=(1, 1, 0.5))


def nail_can(x, y, z):
    """A coffee can of nails: tin can with rims, ribs and a faded label, nails standing in it."""
    frustum(x, y, z, z + 17, 7, 7, "can_mat", sides=20, open_ends=True)
    frustum(x, y, z + 0.4, z + 16.6, 6.7, 6.7, "can_mat", sides=20, open_ends=True, inside=True)
    frustum(x, y, z + 3.5, z + 13, 7.1, 7.1, "can_label_mat", sides=20, open_ends=True)
    for zz in (0.5, 16.6):
        ring(x, y, z + zz, 7.0, 0.35, "can_mat", sides=20)
    frustum(x, y, z + 1, z + 14.5, 6.6, 6.6, "rusty_tool_mat", sides=20)
    r = random.Random(int(x * 3 + y))
    for k in range(18):
        a, rr = r.uniform(0, 6.28), r.uniform(0, 5.5)
        p0 = (x + rr * math.cos(a), y + rr * math.sin(a), z + 13)
        p1 = (p0[0] + r.uniform(-1.5, 1.5), p0[1] + r.uniform(-1.5, 1.5), z + 17 + r.uniform(0, 3))
        tube(p0, p1, 0.22, "metal_mat", sides=4)
        frustum(p1[0], p1[1], p1[2], p1[2] + 0.25, 0.6, 0.6, "metal_mat", sides=6)


def paint_can(x, y, z, k, dent=0):
    """A gallon paint can: body with rolled rims, a drip-stained label, the lid rim and a wire bail
    with a wooden grip lying to one side."""
    frustum(x, y, z, z + 18, 8, 8, "paint_can_mat", sides=22)
    for zz in (0.5, 17.6):
        ring(x, y, z + zz, 8.0, 0.4, "paint_can_mat", sides=22)
    frustum(x, y, z + 18, z + 18.5, 6.8, 6.8, "rusty_tool_mat", sides=22)
    ring(x, y, z + 18.5, 6.9, 0.45, "rusty_tool_mat", sides=22)
    for e in (-1, 1):
        frustum(x + e * 8.1, y, z + 14.5, z + 15.5, 1.0, 1.0, "metal_mat", sides=6)
    pts = [(x + 8.2 * math.cos(t), y + 6 * math.sin(t) * 0.3 + 2, z + 15 + 6 * math.sin(t) * 0.25) for t in [math.pi * i / 10.0 for i in range(11)]]
    for p0, p1 in zip(pts, pts[1:]):
        tube(p0, p1, 0.2, "metal_mat", sides=4)
    tube((x - 2.5, y + 2.6, z + 16.6), (x + 2.5, y + 2.6, z + 16.6), 0.8, "plank_grey_mat", sides=8)
    for d in range(2):                                                               # drips down the side
        a = 0.6 + d * 1.9 + k
        rbevel(x + 8.05 * math.cos(a), y + 8.05 * math.sin(a), z + 13.5 - d * 2, 0.4, 1.6, 7 + d * 3,
               "algae_mat" if k % 2 else "toolbox_mat", r=0.2, yaw=math.degrees(a))


def mason_jar(x, y, z, fill_mat=None):
    """A mason jar: shouldered glass with its screw band and lid, something in it."""
    lathe(x, y, [(z, 4.2), (z + 0.5, 4.6), (z + 11, 4.6), (z + 13, 3.8), (z + 14.5, 3.6)], "seeglass_cabin_mat", sides=18)
    frustum(x, y, z + 13.5, z + 16, 3.9, 3.9, "rusty_tool_mat", sides=18)
    if fill_mat:
        frustum(x, y, z + 0.5, z + 6, 4.2, 4.2, fill_mat, sides=16)


def glass_bottle(x, y, z, h=24.0):
    """A glass bottle: body, rounded shoulder, a neck with a lip, a cork."""
    lathe(x, y, [(z, 3.6), (z + 0.6, 4.0), (z + h * 0.6, 4.0), (z + h * 0.72, 3.2), (z + h * 0.8, 1.6), (z + h * 0.97, 1.4),
                 (z + h, 1.7)], "bottle_mat", sides=16)
    frustum(x, y, z + h, z + h + 1.6, 1.2, 1.3, "split_wood_mat" if "split_wood_mat" in BLD_MATS else "plank_grey_mat", sides=8)


def jerry_can(x, y, z, yaw):
    """A steel jerry can on its base: pressed X panels on both faces, three handles across the top,
    the spout cap with its clamp."""
    with Moved(x, y, yaw):
        bevel_box(x - 8, x + 8, y - 17, y + 17, z, z + 33, "gas_can_mat", r=2.0, seg=2)
        for e in (-1, 1):                                                           # the X pressings
            for s_ in (-1, 1):
                rbevel(x + e * 8.2, y, z + 15, 0.6, 2.0, 34, "gas_can_mat", r=0.3, tilt_y=s_ * 40)
            bevel_box(x + e * 8.2 - 0.3, x + e * 8.2 + 0.3, y - 15, y + 15, z + 1.5, z + 2.5, "gas_can_mat", r=0.2)
        for k in range(3):                                                          # handles
            yy = y - 9 + k * 6
            polyline([(x - 6, yy, z + 33), (x - 5, yy, z + 37), (x + 5, yy, z + 37), (x + 6, yy, z + 33)], 0.8, 0.8, "gas_can_mat", sides=6)
        frustum(x, y + 13, z + 33, z + 36.5, 2.6, 2.4, "gas_can_mat", sides=12)    # spout
        bevel_box(x - 3, x + 3, y + 11, y + 15, z + 36.5, z + 38, "metal_mat", r=0.4)


def galv_bucket(x, y, z):
    """A galvanized bucket: tapered body with two rolled ribs, a rolled rim, the bail with ears."""
    frustum(x, y, z, z + 22, 11, 13, "can_mat", sides=24, open_ends=True)
    frustum(x, y, z + 0.4, z + 21.6, 10.6, 12.6, "can_mat", sides=24, open_ends=True, inside=True)
    frustum(x, y, z, z + 0.5, 11, 11, "can_mat", sides=24)
    for zz, rr in ((7, 11.7), (14, 12.3)):
        ring(x, y, z + zz, rr, 0.35, "can_mat", sides=24)
    ring(x, y, z + 22, 13.1, 0.6, "can_mat", sides=24)
    for e in (-1, 1):
        bevel_box(x + e * 13.2 - 0.4, x + e * 13.2 + 0.4, y - 1.5, y + 1.5, z + 17, z + 21, "metal_mat", r=0.2)
    pts = [(x + 13.3 * math.cos(t), y - 6 * math.sin(t), z + 19 + 4 * math.sin(t)) for t in [math.pi * i / 12.0 for i in range(13)]]
    polyline(pts, 0.3, 0.3, "metal_mat", sides=5)



def hurricane_lantern(x, y, z, lit, name=None):
    """A kerosene hurricane lantern: a round fuel tank with a filler cap, the burner with its wick
    knob, a pear-shaped glass globe with the flame, the two air tubes up the sides to the vented
    top cap, a wire guard round the globe and the bail handle."""
    lathe(x, y, [(z, 6.5), (z + 0.6, 7.6), (z + 3.5, 8.0), (z + 5.6, 7.2), (z + 6.6, 4.6), (z + 7.0, 3.4)], "rusty_tool_mat", sides=20)
    frustum(x + 5.0, y, z + 5.2, z + 6.8, 1.0, 1.0, "rusty_tool_mat", sides=8)                       # filler cap
    frustum(x, y, z + 7.0, z + 9.0, 3.6, 3.2, "rusty_tool_mat", sides=14)                            # burner
    tube((x, y - 3.2, z + 8), (x, y - 5.5, z + 8), 0.35, "rusty_tool_mat", sides=6)                   # wick knob
    frustum(x, y - 5.5, z + 7.2, z + 8.8, 1.1, 1.1, "rusty_tool_mat", sides=8)
    if lit:
        sphere(x, y, z + 11.8, 0.9, "glow_lamp_mat", sides=8, scale=(1, 1, 2.2))
    lathe(x, y, [(z + 9.0, 3.2), (z + 11, 5.0), (z + 14, 5.8), (z + 17, 5.0), (z + 19.5, 3.4), (z + 20.5, 3.0)],
          "seeglass_cabin_mat", sides=18)                                                             # globe
    for k in range(4):                                                                               # guard wires
        a = k * math.pi / 2 + math.pi / 4
        pts = [(x + rr * math.cos(a), y + rr * math.sin(a), zz) for rr, zz in ((4.0, z + 9), (6.4, z + 13), (6.4, z + 16), (4.0, z + 20.5))]
        for p0, p1 in zip(pts, pts[1:]):
            tube(p0, p1, 0.18, "rusty_tool_mat", sides=4)
    ring(x, y, z + 14.5, 6.4, 0.2, "rusty_tool_mat", sides=18)
    for s_ in (-1, 1):                                                                               # the air tubes
        tube((x + s_ * 7.4, y, z + 6.2), (x + s_ * 7.4, y, z + 22.5), 0.55, "rusty_tool_mat", sides=8)
        tube((x + s_ * 7.4, y, z + 22.5), (x + s_ * 4.5, y, z + 24.5), 0.55, "rusty_tool_mat", sides=8)
    lathe(x, y, [(z + 20.5, 3.2), (z + 22.5, 6.0), (z + 24.5, 4.8), (z + 26.5, 2.4), (z + 27.5, 1.2)], "rusty_tool_mat", sides=18)   # top
    pts = [(x + 6.0 * math.cos(t), y, z + 24 + 7 * math.sin(t)) for t in [math.pi * k / 10.0 for k in range(11)]]
    for p0, p1 in zip(pts, pts[1:]):                                                                 # bail
        tube(p0, p1, 0.25, "rusty_tool_mat", sides=4)
    if name:
        light(name, x, y, z + 12, [1.0, 0.6, 0.28], 5, 560, room=True)

def sleeping_bag(cx, y_head, z, seed=0):
    """Cas's sleeping bag on a bunk, head toward -y... laid along +y from y_head: a quilted
    green shell, the top corner unzipped and folded back over itself showing the flannel
    lining, a zipper down the side with its pull, the hood bunched with its drawcord, the stuff
    sack at the foot."""
    L, W = 150.0, 72.0
    yc = y_head + L / 2.0
    quilted(cx, yc + 4, z, W, L - 8, 10, "sleeping_bag_mat", baffles=9, seed=seed)          # zipped-up bag
    # the top corner unzipped and turned back: lining (flannel) side up, lying on the bag
    quilted(cx + 14, y_head + 40, z + 8.5, 40, 46, 3.5, "sleeping_bag_lining_mat", baffles=2, seed=seed + 2, yaw=-28)
    rsoft(cx + 30, y_head + 34, z + 10, 10, 40, 6, "sleeping_bag_mat", jitter=0.6, smooth=2, seed=seed + 4, yaw=-28)   # the fold
    # the zipper down the right side, open from the fold up, its pull hanging off
    zx = cx + W / 2.0 - 0.6
    tube((zx, y_head + 62, z + 5), (zx, y_head + L - 4, z + 4.5), 0.55, "zipper_mat", sides=4)
    bevel_box(zx - 0.5, zx + 1.5, y_head + 60, y_head + 64, z + 2.5, z + 7, "metal_mat", r=0.3)
    rbevel(zx + 2, y_head + 62, z + 0.5, 1.2, 1.8, 6, "metal_mat", r=0.3)
    # the hood at the head end, bunched up, cord and toggle
    rsoft(cx, y_head + 6, z + 6, W - 8, 18, 12, "sleeping_bag_mat", jitter=0.8, sag=3, smooth=2, seed=seed + 5)
    tube((cx - 10, y_head - 3, z + 9), (cx - 16, y_head - 10, z + 2), 0.4, "zipper_mat", sides=4)
    frustum(cx - 16, y_head - 10, z + 0.2, z + 3.5, 1.4, 1.4, "zipper_mat", sides=6)
    # stuff sack at the foot, empty and crumpled
    rsoft(cx - 20, y_head + L - 6, z + 17, 18, 28, 14, "sleeping_bag_mat", jitter=0.9, sag=2, smooth=2, seed=seed + 6, yaw=60)
    tube((cx - 26, y_head + L + 4, z + 20), (cx - 30, y_head + L + 10, z + 11), 0.4, "zipper_mat", sides=4)


def boot_print(x, y, z, yaw, left):
    """A muddy work-boot print: a thin flat mud film in a boot's outline (wide ball, narrow waist,
    separate heel), lug bars of the tread pressed in, a little mud spatter."""
    a = math.radians(yaw)
    fx, fy = -math.sin(a), math.cos(a)                                  # toward the toe
    sx_, sy_ = fy, -fx                                                  # across the boot
    def flat(cx_, cy_, rx, ry):
        c = cmds.polyCylinder(r=1, h=0.18, sx=16, sy=1, sz=0, ch=False)[0]
        cmds.scale(rx, 1, ry, c)
        cmds.rotate(0, -yaw, 0, c)
        cmds.move(cx_, z + 0.1, cy_, c)
        keep(c, "mud_print_mat")
    flat(x + fx * 7, y + fy * 7, 5.0, 8.0)                              # ball and toe
    flat(x + fx * 0, y + fy * 0, 3.6, 5.0)                              # waist
    flat(x - fx * 10, y - fy * 10, 4.2, 4.4)                            # heel
    for k in range(5):                                                  # lugs across the sole
        t = 12 - k * 3.2
        for e in (-1, 1):
            cx_, cy_ = x + fx * t + sx_ * e * 2.1, y + fy * t + sy_ * e * 2.1
            rbevel(cx_, cy_, z + 0.28, 2.6, 1.0, 0.14, "plank_dark_mat", r=0.05, yaw=yaw + e * 25)
    for k in range(2):
        rbevel(x - fx * (8 + k * 3.5), y - fy * (8 + k * 3.5), z + 0.28, 5.5, 1.0, 0.14, "plank_dark_mat", r=0.05, yaw=yaw + 90)
    r = random.Random(int(x * 7 + y))
    for k in range(3):
        sphere(x + r.uniform(-9, 9), y + r.uniform(-12, 14), z + 0.12, r.uniform(0.5, 1.2), "mud_print_mat", sides=6, scale=(1, 1, 0.15))

def oar(p0, p1, mat="plank_grey_mat"):
    """An oar from the grip p0 to the blade tip p1 (lying flat): round loom, flat blade."""
    d = [p1[i] - p0[i] for i in range(3)]
    L = math.sqrt(sum(c * c for c in d))
    u = [c / L for c in d]
    at = lambda t: tuple(p0[i] + d[i] * t for i in range(3))
    tube(p0, at(0.06), 1.6, mat, sides=8)
    tube(at(0.06), at(0.68), 2.4, mat, sides=10)
    ring(*at(0.4), 2.8, 0.6, "dark_leather_mat", axis="y" if abs(u[1]) > abs(u[0]) else "x", sides=10)
    yaw = math.degrees(math.atan2(u[1], u[0])) - 90
    c = at(0.84)
    rbevel(c[0], c[1], c[2], 15, L * 0.32, 1.6, mat, r=0.6, yaw=yaw)


def life_vest(x, y, z_hook, seed, wall_dir=1):
    """An old kapok life jacket hanging by its collar loop on a hook: two front panels, each
    three stitched kapok blocks, a back panel behind, a padded collar, a webbing strap with a
    metal buckle across the front, ties hanging. wall_dir: +1 = the wall is toward -x."""
    tube((x - wall_dir * 2, y, z_hook), (x + wall_dir * 5, y, z_hook + 2.5), 0.7, "rusty_tool_mat", sides=6)
    sphere(x + wall_dir * 5, y, z_hook + 2.5, 1.0, "rusty_tool_mat", sides=6)
    ring(x + wall_dir * 4, y, z_hook - 1, 2.6, 0.5, "strap_mat", axis="y", sides=10)        # collar loop
    rsoft(x + wall_dir * 4, y, z_hook - 32, 6, 46, 52, "lifejacket_mat", jitter=0.6, smooth=2, seed=seed, div=(2, 4, 5))   # back
    for s_ in (-1, 1):
        for k in range(3):
            rsoft(x + wall_dir * 10, y + s_ * 11.5, z_hook - 14 - k * 16, 8, 20, 15, "lifejacket_mat", jitter=0.5,
                  sag=0, smooth=2, seed=seed + s_ * 7 + k, div=(2, 3, 3))
        for k in range(2):                                                          # seams between blocks
            bevel_box(x + wall_dir * 14.2 - 0.3, x + wall_dir * 14.2 + 0.3, y + s_ * 11.5 - 9.5, y + s_ * 11.5 + 9.5,
                      z_hook - 22.5 - k * 16 - 0.4, z_hook - 22.5 - k * 16 + 0.4, "strap_mat", r=0.1)
    tube((x + wall_dir * 8, y - 13, z_hook - 3), (x + wall_dir * 8, y + 13, z_hook - 3), 4.0, "lifejacket_mat", sides=12)   # collar
    for s_ in (-1, 1):
        sphere(x + wall_dir * 8, y + s_ * 13, z_hook - 3, 4.0, "lifejacket_mat", sides=10)
    zz = z_hook - 36
    bevel_box(x + wall_dir * 14.6 - 0.5, x + wall_dir * 14.6 + 0.5, y - 22, y + 22, zz - 1.6, zz + 1.6, "strap_mat", r=0.3)
    bevel_box(x + wall_dir * 15.4 - 0.7, x + wall_dir * 15.4 + 0.7, y + 1, y + 6, zz - 2.6, zz + 2.6, "metal_mat", r=0.4)
    for s_ in (-1, 1):                                                              # ties hanging down
        tube((x + wall_dir * 14.6, y + s_ * 4, z_hook - 46), (x + wall_dir * 14.8, y + s_ * 6, z_hook - 70), 0.6, "strap_mat", sides=5)


# ---------- boathouse ----------

def boat_hull(L, W, out_mat, in_mat, seats=3, keel_z=0.0, water_z=None):
    """An open wooden rowboat at the origin (keel at keel_z, length along y): plank hull, ribs,
    floorboards (laid above water_z so the lake never shows inside it), seats, keel, stem,
    transom, oarlocks."""
    def hull(u):
        end = min(u, 1 - u)
        k = math.sin(math.pi * min(0.5, end)) ** 0.6                  # pointed at both ends (a flat squared
        rise = 10 * max(0.0, (0.15 - end) / 0.15) ** 2                 # stern read as a loose slab of wood)
        return keel_z, keel_z + 52 + rise, W / 2 * k * 0.5, W / 2 * k      # ~45 cm of freeboard above the water
    open_hull(L, hull, out_mat, in_mat, sx=10, sy=6, sz=36, thick=2.5)
    def inner(u):
        b, t, w0, w1 = hull(u)
        return b + 2.5, t, max(0.5, w0 - 2.5), max(0.5, w1 - 2.5)
    fz = max(keel_z + 12, (water_z if water_z is not None else -1e9) + 4)
    sole_plate(L, lambda u: inner(u * 0.96 + 0.02), fz, "plank_dark_mat", Ls=L * 0.96)
    for k in range(5):                                                   # floorboards on the sole
        x = (k - 2) * 9.0
        bevel_box(x - 4, x + 4, -L * 0.3, L * 0.3, fz + 1.4, fz + 2.6, "plank_grey_mat", r=0.4)
    for u in (0.2, 0.32, 0.44, 0.56, 0.68, 0.8):                         # ribs
        b, t, w0, w1 = inner(u)
        y = (u - 0.5) * (L - 14)
        for s_ in (-1, 1):
            tube((s_ * (w0 + 0.5), y, b + 2), (s_ * (w1 - 0.8), y, t - 3), 1.3, "plank_dark_mat", sides=6)
    for s_ in (-1, 1):                                                   # gunwales
        pts = [(s_ * hull(k / 20.0)[3], (k / 20.0 - 0.5) * L, hull(k / 20.0)[1] + 0.5) for k in range(21)]
        for p0, p1 in zip(pts, pts[1:]):
            tube(p0, p1, 2.0, "plank_dark_mat", sides=8)
        b, t, w0, w1 = hull(0.55)
        ring(s_ * w1, 0.05 * L, t + 3.2, 2.2, 0.45, "rusty_tool_mat", axis="y", sides=10)   # oarlocks
        tube((s_ * w1, 0.05 * L, t + 1), (s_ * w1, 0.05 * L, t + 2.2), 0.5, "rusty_tool_mat", sides=6)
    for u in [0.22, 0.5, 0.78][:seats]:
        b, t, w0, w1 = hull(u)
        rbevel(0, (u - 0.5) * L, t - 8, 2 * min(hull(u - 0.04)[3], hull(u + 0.04)[3]) - 8, 24, 3, "plank_grey_mat", r=0.6)   # fits the narrowing hull
    tube((0, -L * 0.48, keel_z - 1.5), (0, L * 0.48, keel_z - 1.5), 2.2, "plank_dark_mat", sides=6)   # keel
    b, t, w0, w1 = hull(0.0)
    tube((0, -L / 2 + 4, keel_z + 2), (0, -L / 2 - 1, keel_z + 52), 2.4, "plank_dark_mat", sides=8)   # stern post
    tube((0, L / 2 - 4, keel_z + 2), (0, L / 2 + 1, keel_z + 52), 2.4, "plank_dark_mat", sides=8)     # stem
    return hull


def boot(cx, cy, z, yaw, seed):
    """Cas's hiking boot (2026-11-17, the ending in the boathouse): the foot built like room_props'
    sneaker (side profile _sneaker_top over a foot-shaped outline, smoothed) in brown leather, a thick
    dark lug sole, an ankle shaft with a padded collar, and the laces tucked in (no loose ends).
    yaw 0 = toe toward +y. z = the floor it stands on."""
    L, W = 29.0, 11.0
    c = cmds.polyCube(w=W, h=1, d=L, sx=4, sy=3, sz=12, ch=False)[0]
    pts = []
    for x, y, zz in _verts(c):
        u, v, h = zz / (L / 2), x / (W / 2), y + 0.5
        width = 0.8 + 0.2 * math.exp(-((u - 0.4) / 0.6) ** 2)
        if u > 0.75:
            width *= math.sqrt(max(0.05, 1 - ((u - 0.75) / 0.3) ** 2))
        pts.append((v * (W / 2) * width * (1 - 0.25 * h * h), h * _sneaker_top(u) * 1.3, zz))
    _set_verts(c, pts)
    cmds.polySmooth(c, dv=2, ch=False)
    _place(c, cx, cy, z + 3.4, "boot_mat", yaw=yaw)
    a = math.radians(yaw)
    fx, fy = -math.sin(a), math.cos(a)
    at = lambda d: (cx + fx * d, cy + fy * d)
    rbevel(cx, cy, z + 1.8, W + 1.4, L + 1.2, 3.6, "boot_sole_mat", r=1.2, seg=2, yaw=yaw)          # thick lug sole
    rsoft(*at(12.6), z + 3.2, 7.8, 4.6, 3.2, "boot_sole_mat", seed=seed, yaw=yaw)                    # rubber toe bumper
    hx, hy = at(-6.2)                                                                               # the ankle shaft
    frustum(hx, hy, z + 9.5, z + 19.0, 5.4, 5.0, "boot_mat", sides=18)
    frustum(hx, hy, z + 18.6, z + 21.0, 5.7, 5.6, "dark_leather_mat", sides=18)                    # padded collar
    sphere(hx, hy, z + 20.9, 4.3, "shoe_inner_mat", sides=14, scale=(1, 1, 0.12))                   # the opening
    for k in range(5):                                                                              # laces, tucked in
        d = 2.5 - k * 1.9
        lx, ly = at(d)
        zz = z + 3.4 + _sneaker_top(d / (L / 2)) * 1.3 + 0.4 if d > -1 else z + 10 + k * 2.2
        rbox(lx, ly, zz, 6.0, 0.8, 0.7, "dark_leather_mat", yaw=yaw, tilt_y=-14)


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
    plank_boards_over("y", X - W, Y + 80, Y + 190, F + 110, F + 190, -3.5, seed=6)     # the west window, boarded up
    # corner posts and the eave plates
    for xx in (X - W, X + W):
        for yy in (Y + S, Y + N):
            bevel_box(xx - 7, xx + 7, yy - 7, yy + 7, F - 30, EAVE, "dock_dark_mat", r=1.0)
    for xx in (X - W, X + W):
        bevel_box(xx - 6, xx + 6, Y + S, Y + N, EAVE - 10, EAVE + 2, "dock_dark_mat", r=1.0)
    # posts either side of the slip opening, up to the header: the lake doors hang on these
    for xa, xb in ((X - SLIP - 14, X - SLIP), (X + SLIP, X + SLIP + 14)):
        bevel_box(xa, xb, Y + N - 6, Y + N + 6, F - 30, F + 252, "dock_dark_mat", r=1.0)
    # pintle plates on the posts' outer faces
    for z in (F + 20, F + 196):
        for xa, xb in ((X - SLIP - 13, X - SLIP - 1), (X + SLIP + 1, X + SLIP + 13)):
            bevel_box(xa, xb, Y + N + 6, Y + N + 7.2, z - 7, z + 7, "rusty_tool_mat", r=0.4)
            for zz in (z - 4, z + 4):
                sphere((xa + xb) / 2.0, Y + N + 7.4, zz, 0.7, "rusty_tool_mat", sides=6, scale=(1, 0.4, 1))
    # the lake doors: the west leaf hangs open on its hinges off the post, sagging; the east one is gone
    with Placed(X - SLIP - 7, Y + N + 9.5, 72):
        for k in range(8):
            x0 = k * 21.5
            sag = -0.05 * (x0 + 10)
            bevel_box(x0 + 0.3, x0 + 21.2, -2.0, 2.0, F - 6 + sag, F + 222 + sag, "plank_grey_mat" if k % 3 else "plank_dark_mat", r=0.5)
        for z in (F + 20, F + 196):
            bevel_box(4, 168, -4.6, -2.0, z - 8 - 0.05 * 86, z + 8 - 0.05 * 86, "plank_dark_mat", r=0.6)
            bevel_box(-3, 60, 2.0, 2.9, z - 3, z + 3, "rusty_tool_mat", r=0.3)          # strap hinges
            tube((0, -2.5, z - 7), (0, -2.5, z + 7), 1.3, "rusty_tool_mat", sides=10)       # the knuckle on its pin
        rbevel(86, -3.3, F + 108 - 0.05 * 86, 205, 2.4, 14, "plank_dark_mat", r=0.6, tilt_x=48)   # Z brace
    for z in (F + 20, F + 196):                                           # the empty hinge pins on the east post
        tube((X + SLIP + 7, Y + N + 9.5, z - 5), (X + SLIP + 7, Y + N + 9.5, z + 5), 0.8, "rusty_tool_mat", sides=8)
        bevel_box(X + SLIP + 5, X + SLIP + 9, Y + N + 7.2, Y + N + 9.5, z - 2, z + 2, "rusty_tool_mat", r=0.3)
    # green slime and rot along the bottom of the walls over the water
    for xx in (X - W, X + W):
        bevel_box(xx - 3.4 if xx < X else xx + 2.4, xx - 2.4 if xx < X else xx + 3.4, Y - 160, Y + N, F - 22, F + 4,
                  "algae_mat", r=0.4)
    bevel_box(X - W, X - SLIP, Y + N + 2.4, Y + N + 3.4, F - 22, F + 2, "algae_mat", r=0.4)
    bevel_box(X + SLIP, X + W, Y + N + 2.4, Y + N + 3.4, F - 22, F + 2, "algae_mat", r=0.4)
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
    WI = X - W + 4.6                                                      # in front of the west wall's battens
    EI = X + W - 4.6
    SI = Y + S + 4.6
    for k in range(5):                                                    # tie beams under the roof
        yy = Y + S + 60 + k * (N - S - 120) / 4.0
        bevel_box(X - W + 6, X + W - 6, yy - 6, yy + 6, EAVE - 22, EAVE - 8, "dock_dark_mat", r=1.0)
    for k, xx in enumerate((X + 90, X + 118)):                            # two spare oars stored across the beams
        oar((xx, Y + S + 70, EAVE - 6.5 + k * 0.3), (xx + 6, Y + S + 70 + 265, EAVE - 6 + k * 0.3))
    # ---- workbench on the west wall, pegboard over it
    bx0, bx1, by0, by1, bz = WI, WI + 75, Y + S + 30, Y + S + 270, F + 90
    bevel_box(bx0, bx1, by0, by1, bz - 6, bz, "dock_wood_mat", r=0.8)
    bevel_box(bx1 - 4, bx1, by0, by1, bz - 14, bz - 6, "dock_dark_mat", r=0.6)
    bevel_box(bx0 + 4, bx1 - 4, by0 + 6, by1 - 6, F + 22, F + 26, "dock_dark_mat", r=0.6)
    for xx in (bx0 + 5, bx1 - 5):
        for yy in (by0 + 5, by1 - 5):
            bevel_box(xx - 4, xx + 4, yy - 4, yy + 4, F, bz - 6, "dock_dark_mat", r=0.6)
    bevel_box(bx0, bx0 + 1.2, by0 + 10, by1 - 10, bz + 18, bz + 112, "plank_dark_mat", r=0.3)      # pegboard
    for gy in range(int(by0) + 22, int(by1) - 14, 12):
        for gz in range(int(bz) + 26, int(bz) + 108, 12):
            bevel_box(bx0 + 1.2, bx0 + 1.5, gy - 0.6, gy + 0.6, gz - 0.6, gz + 0.6, "stove_mat", r=0.1)
    P = bx0 + 2.6                                                         # tools hanging on it
    tube((P, by0 + 40, bz + 95), (P, by0 + 40, bz + 62), 1.3, "plank_grey_mat", sides=8)            # hammer
    rbevel(P, by0 + 40, bz + 96, 3.5, 12, 3.5, "rusty_tool_mat", r=0.6)
    for k, yy in enumerate((by0 + 62, by0 + 70, by0 + 78)):                # screwdrivers
        frustum(P + 1, yy, bz + 88, bz + 99, 1.4, 1.2, "toolbox_mat" if k != 1 else "dark_leather_mat", sides=8)
        tube((P + 1, yy, bz + 88), (P + 1, yy, bz + 70 + k * 3), 0.35, "metal_mat", sides=4)
    rbevel(P, by0 + 100, bz + 80, 0.8, 4, 28, "rusty_tool_mat", r=0.3)                               # wrench
    ring(P, by0 + 100, bz + 95, 2.6, 0.8, "rusty_tool_mat", axis="x", sides=10)
    ring(P, by0 + 100, bz + 65, 2.2, 0.8, "rusty_tool_mat", axis="x", sides=10)
    rbevel(P, by0 + 150, bz + 70, 0.5, 58, 14, "metal_mat", r=0.2, tilt_y=-6)                         # hand saw
    rbevel(P + 0.5, by0 + 117, bz + 74, 2.4, 13, 11, "plank_grey_mat", r=1.5)
    ring(P + 0.6, by0 + 117, bz + 74, 3.6, 0.6, "plank_dark_mat", axis="x", sides=8)
    for k in range(4):                                                    # a coil of wire on a nail
        ring(P + 1.5 + k * 0.6, by0 + 200, bz + 80, 9 - k * 0.4, 0.3, "rusty_tool_mat", axis="x", sides=16)
    for s in (-1, 1):                                                     # pliers
        tube((P + 1, by0 + 225, bz + 96), (P + 1, by0 + 225 + s * 3, bz + 76), 0.6, "dark_leather_mat", sides=6)
    # the vise on the front corner of the bench
    bench_vise(bx1 - 10, by0 + 26, bz)
    # on the bench: a jar of screws, a coffee can of nails, a hand drill, the open toolbox, the lantern
    screw_jar(bx0 + 22, by0 + 60, bz)
    nail_can(bx0 + 20, by0 + 125, bz)
    hand_drill(bx0 + 46, by0 + 96, bz, 12)
    cantilever_toolbox(bx0 + 40, by1 - 62, bz)
    hurricane_lantern(bx0 + 30, by1 - 16, bz, True, "light_boathouse_lantern")      # clear of the toolbox now
    # ---- life jackets on the west wall, a life ring with its grab line on the east wall
    life_ring(EI - 8, Y + 230, F + 160, wall_dir=-1)
    # a fishing net hung on three nails, with floats, over the east walkway
    fishing_net(EI, [(Y + 330, F + 215), (Y + 420, F + 225), (Y + 510, F + 212)], 80, wall_dir=-1, seed=4)
    # ---- shelves on the east wall, landward: paint cans, a gas can, jars, bottles
    sx1, sx0, sy0, sy1 = EI, EI - 36, Y + S + 190, Y + S + 320
    for yy in (sy0 + 3, sy1 - 3):
        for xx in (sx0 + 3, sx1 - 3):
            bevel_box(xx - 2.5, xx + 2.5, yy - 2.5, yy + 2.5, F, F + 175, "dock_dark_mat", r=0.5)
    for zz in (F + 8, F + 52, F + 96, F + 140):
        bevel_box(sx0, sx1, sy0, sy1, zz, zz + 2.5, "dock_wood_mat", r=0.5)
    rngs = random.Random(9)
    for k in range(4):                                                    # paint cans on the second shelf
        paint_can(sx0 + 18, sy0 + 18 + k * 30, F + 54.5, k)
    for k in range(5):                                                    # jars and bottles on the third
        cy_ = sy0 + 14 + k * 24
        if k % 2:
            glass_bottle(sx0 + 16, cy_, F + 98.5, 22 + k)
        else:
            mason_jar(sx0 + 16, cy_, F + 98.5, ("rusty_tool_mat", "mud_print_mat", None)[k // 2])
    for k in range(3):                                                    # folded rags on the top shelf
        folded(sx0 + 17, sy0 + 30 + k * 34, F + 142.5, 22, 26, "tarp_mat" if k != 1 else "sheet_mat", "plain", 40 + k)
    jerry_can(sx0 + 17, sy0 + 40, F + 10.5, 0)                            # the red gas can on the bottom shelf
    galv_bucket(sx0 + 18, sy0 + 98, F + 10.5)
    # ---- fishing rods and a landing net in the south-east corner
    for k in range(3):
        base = (EI - 12 - k * 6, SI + 10 + k * 5, F + 0.5)
        tip = (EI - 2, SI + 4 + k * 9, F + 245)
        tube(base, tip, 0.9 - k * 0.1, "dark_leather_mat", sides=6)
        rp = tuple(base[i] + (tip[i] - base[i]) * 0.12 for i in range(3))
        frustum(rp[0] - 4, rp[1], rp[2] - 3, rp[2] + 3, 3.5, 3.5, "metal_mat", sides=10)
        for t in (0.35, 0.6, 0.85):
            q = tuple(base[i] + (tip[i] - base[i]) * t for i in range(3))
            ring(q[0] - 1.5, q[1], q[2], 1.0, 0.2, "metal_mat", axis="z", sides=6)
    nb, nt = (EI - 40, SI + 8, F + 0.5), (EI - 28, SI + 4, F + 120)
    tube(nb, nt, 1.3, "plank_grey_mat", sides=8)
    ring(nt[0] + 4, nt[1] + 1, nt[2] + 18, 18, 0.9, "rusty_tool_mat", axis="y", sides=20)
    for k in range(8):
        a = k * math.pi / 4
        p0 = (nt[0] + 4 + 18 * math.cos(a), nt[1] + 1, nt[2] + 18 + 18 * math.sin(a))
        tube(p0, (nt[0] + 8, nt[1] - 8, nt[2] + 6), 0.25, "net_mat", sides=3)
    # ---- the slatted crate with a tarp dragged half off it
    cx, cy = X + W - 70, Y + S + 120
    for s in (-1, 1):
        for xx in (cx - 44, cx + 40):
            bevel_box(xx, xx + 4, cy + s * 35 - 2, cy + s * 35 + 2, F, F + 62, "dock_dark_mat", r=0.5)
        for zz in (F + 4, F + 25, F + 46):
            bevel_box(cx - 45, cx + 45, cy + s * 35 - 1.5, cy + s * 35 + 1.5, zz, zz + 14, "dock_wood_mat", r=0.5)
            bevel_box(cx + s * 45 - 1.5, cx + s * 45 + 1.5, cy - 34, cy + 34, zz, zz + 14, "dock_wood_mat", r=0.5)
    for k in range(5):
        bevel_box(cx - 45 + k * 18.4, cx - 45 + k * 18.4 + 15.6, cy - 36, cy + 36, F + 62, F + 64.5, "dock_wood_mat", r=0.5)
    bevel_box(cx - 43, cx + 43, cy - 33, cy + 33, F + 2, F + 3.5, "plank_dark_mat", r=0.4)             # dark inside
    # ---- the new rope, coiled on the east walkway, its end running to the slip edge and down
    end_in, end_out = rope_coil(X + SLIP + 70, Y + 60, F + 0.2, 18, 4.5, 1.3, "rope_new_mat", seed=5)
    polyline([end_out, (X + SLIP + 60, Y + 95, F + 1.5), (X + SLIP + 25, Y + 135, F + 1.5), (X + SLIP + 8, Y + 150, F + 2.5),
              (X + SLIP - 2, Y + 160, F - 4), (X + SLIP - 5, Y + 166, F - 20)], 1.3, 1.3, "rope_new_mat", sides=8)
    # ---- an anchor and its chain on the west walkway
    admiralty_anchor(X - SLIP - 60, Y + 200, F, 0)
    # ---- muddy boot prints: in at the door, to the slip, along the east walkway
    path = [(X + 10, Y + S + 20), (X + 40, Y - 240), (X + SLIP + 60, Y - 140), (X + SLIP + 70, Y + 40)]
    step = 0
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        yaw = math.degrees(math.atan2(y1 - y0, x1 - x0)) - 90
        n = int(d / 36)
        for i in range(n):
            t = i / float(n)
            side = 1 if step % 2 else -1
            nx, ny = -(y1 - y0) / d, (x1 - x0) / d
            px, py = x0 + (x1 - x0) * t + nx * side * 9, y0 + (y1 - y0) * t + ny * side * 9
            boot_print(px, py, F + 0.5, yaw + side * 5, side < 0)
            step += 1
    # ---- the old rowboat, floating in the slip, tied off at the bow
    n, m = len(PARTS), len(ROOM_PARTS)
    boat_hull(340, 128, "boat_old_mat", "plank_dark_mat", keel_z=WATER_Z - 8, water_z=WATER_Z)
    new = PARTS[n:] + ROOM_PARTS[m:]
    g = cmds.group(new, name="slip_boat_grp")
    cmds.rotate(0, 3, 2.5, g, pivot=(0, WATER_Z, 0))
    cmds.move(X - 6, 0, Y + 300, g, relative=True)
    cmds.ungroup(g)
    # the bow line: from the eye on the stem, sagging, to a cleat on the slip edge, turns round it
    sag_rope((X - 6, Y + 470, WATER_Z + 55), (X - SLIP + 4, Y + 518, F + 3.5), 9, 0.9, "rope_mat", n=14)
    ring(X - 6, Y + 471, WATER_Z + 55, 1.8, 0.45, "rusty_tool_mat", axis="y", sides=10)
    cx_, cy_ = X - SLIP - 4, Y + 520
    bevel_box(cx_ - 3, cx_ + 3, cy_ - 4, cy_ + 4, F, F + 3, "rusty_tool_mat", r=0.6)                # cleat base
    polyline([(cx_, cy_ - 11, F + 4.5), (cx_, cy_ - 4, F + 4.8), (cx_, cy_ + 4, F + 4.8), (cx_, cy_ + 11, F + 4.5)], 1.4, 1.4,
             "rusty_tool_mat", sides=10)                                                              # horns
    for k in range(3):                                                                               # figure-eight turns
        e = 1 if k % 2 else -1
        polyline([(cx_ + 2.4, cy_ - 8, F + 5.6 + k * 0.6), (cx_, cy_, F + 6.4 + k * 0.6), (cx_ - 2.4, cy_ + 8, F + 5.6 + k * 0.6)],
                 0.9, 0.9, "rope_mat", sides=6) if e > 0 else polyline([(cx_ - 2.4, cy_ - 8, F + 5.6 + k * 0.6), (cx_, cy_, F + 6.4 + k * 0.6),
                 (cx_ + 2.4, cy_ + 8, F + 5.6 + k * 0.6)], 0.9, 0.9, "rope_mat", sides=6)
    polyline([(cx_ + 2.4, cy_ + 8, F + 5.6), (cx_ + 6, cy_ + 14, F + 1.4), (cx_ + 12, cy_ + 10, F + 1.2), (cx_ + 10, cy_ + 2, F + 1.2)],
             0.9, 0.9, "rope_mat", sides=6)                                                           # the tail
    oar((X - 30, Y + 220, WATER_Z + 40), (X + 4, Y + 420, WATER_Z + 40))                  # an oar left in the boat
    frustum(X + 28, Y + 250, WATER_Z + 7, WATER_Z + 21, 8, 9, "can_mat", sides=12, open_ends=True)   # bailing can
    # cobwebs in two top corners
    cobweb((X - W + 5, Y + S + 5), 1, 1, 46, EAVE - 2)
    cobweb((X + W - 5, Y + N - 5), -1, -1, 60, EAVE - 2)
    # ---- the ending (STORY.md, 2026-11-16): by the water door at the end of the west walkway, Cas's
    # boots set neatly side by side, laces tucked in, toes to the water (her note beside them is a clue,
    # clues.json boathouse_note)
    # (2026-11-22: the boots themselves are now the user's Fab scan, placed by unreal/place_boots.py at
    # BX, BYB = X - SLIP - 80, Y + N - 75 = (-3752, 15025); boot() is kept but no longer called)
    # (the last page and its red lantern moved to the end of the dock, 2026-11-17)
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
            # boarded with slits, and a dim red glow inside showing through them: someone is in there
            plank_boards_over("x", HY, a, b, zlo, zhi, 15.5, seed=int(a) + index, gaps=True)
            box(a, b, HY - 9, HY - 8, zlo, zhi, "glow_window_red_mat")
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
    # bunk bed on the west wall, a little off the walls: sheets and pillows on both, a wool
    # blanket turned down on the top bunk, Cas's sleeping bag on the bottom one
    x0, x1, y0, y1 = -HX + I + 10, -HX + I + 103, -HY + I + 10, -HY + I + 213
    mx = (x0 + x1) / 2.0
    for x in (x0 + 4, x1 - 4):
        for yy in (y0 + 4, y1 - 4):
            bevel_box(x - 4, x + 4, yy - 4, yy + 4, F, F + 210, "plank_dark_mat", r=0.8)
    for z in (F + 38, F + 150):
        for x in (x0, x1 - 6):
            bevel_box(x, x + 6, y0, y1, z, z + 12, "plank_dark_mat", r=0.8)
        for yy in (y0, y1 - 6):
            bevel_box(x0 + 6, x1 - 6, yy, yy + 6, z, z + 12, "plank_dark_mat", r=0.8)
        for k in range(7):
            yy = y0 + 12 + k * 29
            bevel_box(x0 + 6, x1 - 6, yy, yy + 9, z + 6, z + 9, "plank_grey_mat", r=0.5)
    for yy in (y0 + 4, y1 - 4):                                           # head and foot boards
        bevel_box(x0 + 8, x1 - 8, yy - 1.5, yy + 1.5, F + 168, F + 196, "plank_grey_mat", r=0.6)
        bevel_box(x0 + 8, x1 - 8, yy - 1.5, yy + 1.5, F + 56, F + 84, "plank_grey_mat", r=0.6)
    # bottom bunk: fitted sheet, pillow, the sleeping bag
    fitted_sheet(mx, (y0 + y1) / 2.0, F + 47, 82, 194, 12, seed=3)
    top0 = F + 47 + 12 + 1.0
    pillow(mx + 3, y0 + 30, top0, 54, 34, 13, seed=61, yaw=4)
    sleeping_bag(mx + 1, y0 + 44, top0, seed=6)
    # top bunk: fitted sheet, pillow at the far end, wool blanket turned down
    fitted_sheet(mx, (y0 + y1) / 2.0, F + 159, 82, 194, 12, seed=8)
    top1 = F + 159 + 12 + 1.0
    pillow(mx - 2, y1 - 30, top1 + 0.2, 54, 34, 13, seed=62, yaw=-3)
    bedspread(x0 + 7, x1 - 7, y0 + 7, y1 - 70, top1 + 0.6, seed=7, mat="wool_mat", hang=14)
    for k in range(4):                                                    # ladder at the head end
        tube((x1 + 2, y1 - 20, F + 30 + k * 40), (x1 + 2, y1 - 50, F + 30 + k * 40), 1.8, "plank_dark_mat", sides=6)
    for yy in (y1 - 20, y1 - 50):
        tube((x1 + 2, yy, F), (x1 + 2, yy, F + 175), 2.0, "plank_dark_mat", sides=6)
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
    # table and two chairs; a torn page and the candle on it (her lake map + the boathouse key are at the shack now)
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
        if not open_:                                    # the red glow from the boarded windows spills onto the porch
            gx, gy = P.world(0, 250 + 70)
            light("light_cabin_glow_%d" % (i + 1), gx, gy, CAB_FL + 140, [1.0, 0.05, 0.02], 40, 600, flicker=True)
        if open_:
            hx, hy = P.world(-52, 250)
            DOORS.append(("door_cabin%d" % (i + 1), "plank_door", hx, hy, CAB_FL, yaw))
            # (the boathouse key used to lie here; it's on Cas's map at the shack now, see make_trail.py)
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

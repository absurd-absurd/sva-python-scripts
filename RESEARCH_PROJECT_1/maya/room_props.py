"""Detailed furniture for the motel rooms (loaded by make_motel.py, which defines box, tube,
keep, rbox and the room layout constants). Positions are Unreal cm, like the rest of the motel.

The first pass was all plain boxes. These are built from a few richer shapes:
  bevel_box  a box with rounded (bevelled) edges: wood, plastic, metal
  rsoft      a smoothed, slightly lumpy shape: pillows, bedding, clothes, a jacket
  frustum    a tapered cylinder (open or closed): lamp shades, mugs, pots, legs
  sphere     knobs, bulbs, finials
Every surface keeps at least ~5 mm away from any other surface it lies on (z-fighting).
"""


# ---------- shape helpers ----------

def _verts(obj):
    p = cmds.xform(obj + ".vtx[*]", q=True, t=True, os=True)
    return [p[i:i + 3] for i in range(0, len(p), 3)]


def _set_verts(obj, pts):
    for i, p in enumerate(pts):
        cmds.xform(f"{obj}.vtx[{i}]", t=p, os=True)


def _bevel(obj, r, seg=2):
    if r > 0:
        cmds.polyBevel3(obj + ".e[*]", offset=r, offsetAsFraction=False, segments=seg,
                        depth=1, autoFit=True, chamfer=True, ch=False)
    return obj


def bevel_box(x0, x1, y0, y1, z0, z1, mat, r=1.0, seg=2):
    """box() with rounded edges (r cm, never more than a third of the thinnest side)."""
    r = min(r, abs(x1 - x0) / 3.0, abs(y1 - y0) / 3.0, abs(z1 - z0) / 3.0)
    return _bevel(box(x0, x1, y0, y1, z0, z1, mat), r, seg)


def rbevel(cx, cy, cz, sx, sy, sz, mat, r=1.0, seg=2, **turn):
    """rbox() (centred and turned) with rounded edges."""
    b = cmds.polyCube(w=sx, h=sz, d=sy, ch=False)[0]
    _bevel(b, min(r, sx / 3.0, sy / 3.0, sz / 3.0), seg)
    return _place(b, cx, cy, cz, mat, **turn)


def _place(obj, cx, cy, cz, mat, yaw=0, tilt_x=0, tilt_y=0):
    cmds.xform(obj, rotation=(tilt_y, -yaw, tilt_x), rotateOrder="yxz")
    cmds.move(cx, cz, cy, obj)
    return keep(obj, mat)


def rsoft(cx, cy, cz, sx, sy, sz, mat, jitter=0.0, sag=0.0, smooth=2, seed=0, **turn):
    """A soft, rounded lump exactly sx * sy * sz: a subdivided box smoothed round, then
    sag pushes the middle of the top down (a dent, a slump) and jitter adds random
    wrinkles (cm). Pillows, bedding, clothes."""
    c = cmds.polyCube(w=1, h=1, d=1, sx=3, sy=2, sz=3, ch=False)[0]
    cmds.polySmooth(c, dv=smooth, ch=False)
    bb = cmds.exactWorldBoundingBox(c)
    cmds.scale(sx / (bb[3] - bb[0]), sz / (bb[4] - bb[1]), sy / (bb[5] - bb[2]), c)
    cmds.makeIdentity(c, apply=True, s=True)
    if jitter or sag:
        r = random.Random(seed)
        pts = []
        for x, y, z in _verts(c):
            u, v = x / (sx / 2.0), z / (sy / 2.0)                    # -1..1 across the top
            if y > 0:
                y -= sag * max(0.0, 1 - u * u) * max(0.0, 1 - v * v)
            pts.append((x + r.uniform(-jitter, jitter), y + r.uniform(-jitter, jitter) * 0.6,
                        z + r.uniform(-jitter, jitter)))
        _set_verts(c, pts)
    return _place(c, cx, cy, cz, mat, **turn)


def frustum(cx, cy, z0, z1, r0, r1, mat, sides=16, open_ends=False, inside=False, sx=1.0, sy=1.0):
    """A tapered cylinder standing from z0 (radius r0) to z1 (radius r1). open_ends removes
    the caps (a lamp shade); inside=True gives an inner copy facing in, so it has a lining."""
    c = cmds.polyCylinder(r=1, h=1, sx=sides, sy=1, sz=0, ch=False)[0]
    pts = [((x * (r1 if y > 0 else r0)) * sx, y * (z1 - z0), (z * (r1 if y > 0 else r0)) * sy) for x, y, z in _verts(c)]
    _set_verts(c, pts)
    if open_ends:
        cmds.delete(f"{c}.f[{sides}:{sides + 1}]")
    if inside:
        cmds.polyNormal(c, normalMode=0, userNormalMode=0, ch=False)
    cmds.move(cx, (z0 + z1) / 2.0, cy, c)
    return keep(c, mat)


def sphere(cx, cy, cz, r, mat, sides=10, scale=(1, 1, 1)):
    s = cmds.polySphere(r=r, sx=sides, sy=max(6, sides // 2 + 2), ch=False)[0]
    cmds.scale(scale[0], scale[2], scale[1], s)
    cmds.move(cx, cz, cy, s)
    return keep(s, mat)


def ring(cx, cy, cz, r, thick, mat, axis="z", sides=12):
    """A torus (mug handle, pot rim). axis = the direction its hole faces."""
    t = cmds.polyTorus(r=r, sr=thick, sx=sides, sy=6, ch=False)[0]
    if axis == "x":
        cmds.rotate(0, 0, 90, t)
    elif axis == "y":
        cmds.rotate(90, 0, 0, t)
    cmds.move(cx, cz, cy, t)
    return keep(t, mat)


# ---------- furniture (every room) ----------

def bed(x0, x1, made=True):
    """Wood frame on short legs, a panelled headboard, a thick rounded mattress. made=True:
    tucked bedspread, a fold under two plump pillows (Room 104 dresses its own, unmade)."""
    bx0, bx1 = x0 + 220, x1 - 40
    by0, by1 = BACK - 250, BACK - 20
    bevel_box(bx0, bx1, by0, by1 - 8, 12, 35, "wood_mat", r=1.5)                     # frame
    for lx in (bx0 + 3, bx1 - 9):
        for ly in (by0 + 3, by1 - 17):
            bevel_box(lx, lx + 6, ly, ly + 6, 0, 12.5, "wood_mat", r=1)               # legs
    # headboard: two posts, a top rail, a panel with two raised insets
    for px in (bx0, bx1 - 8):
        bevel_box(px, px + 8, by1 - 9, by1, 0, 120, "wood_mat", r=1.5)
    bevel_box(bx0 - 2, bx1 + 2, by1 - 10, by1 - 0.5, 106, 116, "wood_mat", r=2.5)
    bevel_box(bx0 + 8, bx1 - 8, by1 - 6, by1 - 2, 38, 106.5, "wood_mat", r=0.5)
    mid = (bx0 + bx1) / 2.0
    for a, b in ((bx0 + 18, mid - 6), (mid + 6, bx1 - 18)):
        bevel_box(a, b, by1 - 7, by1 - 5.5, 52, 98, "wood_mat", r=1)
    top = 56.5 if not made else 55.0
    bevel_box(bx0 + 4, bx1 - 4, by0 + 4, by1 - 11, 34, top, "bed_mat", r=5, seg=3)  # mattress
    if made:
        # bedspread: over the top and hanging down the sides, stopping short of the pillows
        bevel_box(bx0 + 1.5, bx1 - 1.5, by0 + 1.5, by1 - 55, 26, 58.5, "bedspread_mat", r=5, seg=3)
        rsoft(mid, by1 - 58, 60, bx1 - bx0 - 6, 24, 10, "bedspread_mat", jitter=0.6, seed=int(x0))   # fold
        for k, px in enumerate((bx0 + 60, bx1 - 60)):
            rsoft(px, by1 - 34, 63, 88, 40, 15, "pillow_mat", sag=3, jitter=0.5, seed=int(x0) + k,
                  yaw=(-3, 4)[k], tilt_y=-12)


def nightstand(x0):
    """Top slab with a small overhang, a drawer with a brass knob, an open shelf, short legs."""
    nx0, nx1, ny0, ny1 = x0 + 150, x0 + 210, BACK - 70, BACK - 25
    bevel_box(nx0 + 2, nx1 - 2, ny0 + 2, ny1 - 2, 6, 57.5, "wood_mat", r=1)
    bevel_box(nx0, nx1, ny0, ny1, 57, 60, "wood_mat", r=1)                            # top: 60 high
    for lx in (nx0 + 3, nx1 - 7):
        for ly in (ny0 + 3, ny1 - 7):
            bevel_box(lx, lx + 4, ly, ly + 4, 0, 6.5, "wood_mat", r=0.8)
    bevel_box(nx0 + 5, nx1 - 5, ny0 + 0.5, ny0 + 2.5, 36, 53, "wood_mat", r=0.8)      # drawer front
    sphere((nx0 + nx1) / 2.0, ny0 - 0.6, 44.5, 1.6, "brass_mat", sides=8)            # knob
    bevel_box(nx0 + 5, nx1 - 5, ny0 + 1.5, ny1 - 4, 10, 31, "trim_mat", r=0.5)        # shelf, dark inside


def lamp(lx, ly, shade="glow_lamp_mat", bulb="glow_lamp_mat"):
    """Brass base and stem, a bulb you can see under the shade, a tapered shade (with a
    lining so it isn't see-through from inside) and a little finial on top."""
    frustum(lx, ly, 60.4, 62.6, 8, 6.5, "brass_mat", sides=16)
    frustum(lx, ly, 62.6, 64.2, 6.5, 3, "brass_mat", sides=16)
    tube((lx, ly, 64.2), (lx, ly, 92), 1.0, "brass_mat", sides=8)
    sphere(lx, ly, 92.5, 1.8, "brass_mat", sides=8)
    sphere(lx, ly, 98.5, 3.6, bulb, sides=10, scale=(1, 1, 1.25))
    frustum(lx, ly, 94, 118, 17, 11, shade, sides=20, open_ends=True)
    frustum(lx, ly, 94.3, 117.7, 16.4, 10.4, shade, sides=20, open_ends=True, inside=True)
    tube((lx, ly, 103), (lx, ly, 120), 0.35, "brass_mat", sides=4)                   # harp
    sphere(lx, ly, 121, 1.2, "brass_mat", sides=8)                                   # finial


def dresser(x0):
    """Against the left wall, facing the bed: six drawers with bar handles, a top slab with
    an overhang (80 high, the office key sits on it), and a plinth."""
    t = 20
    dx0 = x0 + t
    y0, y1 = FRONT + 200, FRONT + 370
    bevel_box(dx0, dx0 + 53, y0 + 2, y1 - 2, 8, 77.5, "wood_mat", r=1)
    bevel_box(dx0, dx0 + 56, y0, y1, 77, 80, "wood_mat", r=1)
    bevel_box(dx0 + 3, dx0 + 50, y0 + 6, y1 - 6, 0, 8.5, "trim_mat", r=0.6)
    mid = (y0 + y1) / 2.0
    for za, zb in ((10, 30), (32, 52), (54, 75)):
        for ya, yb in ((y0 + 5, mid - 1), (mid + 1, y1 - 5)):
            bevel_box(dx0 + 52.5, dx0 + 55, ya + 1, yb - 1, za + 1, zb - 1, "wood_mat", r=0.8)
            yc, zc = (ya + yb) / 2.0, (za + zb) / 2.0
            for dy in (-6, 6):
                box(dx0 + 55, dx0 + 57, yc + dy - 0.6, yc + dy + 0.6, zc - 0.6, zc + 0.6, "brass_mat")
            tube((dx0 + 57.6, yc - 7, zc), (dx0 + 57.6, yc + 7, zc), 0.8, "brass_mat", sides=6)


def crt_tv(x0):
    """An old CRT: rounded front case, tapered back, a curved dark screen in a recessed bezel,
    two knobs and a speaker grille, rabbit-ear antenna. Screen faces the bed (+x)."""
    t = 20
    fx = x0 + t + 50                      # front face of the case
    y0, y1 = FRONT + 235, FRONT + 335
    bevel_box(fx - 22, fx, y0, y1, 80.5, 150, "tv_mat", r=3, seg=3)                  # front case
    # tapered back: a box whose back face is shrunk toward the middle
    b = cmds.polyCube(w=24, h=56, d=80, sx=1, sy=1, sz=1, ch=False)[0]
    _set_verts(b, [(x, y * (0.7 if x < 0 else 1.0), z * (0.65 if x < 0 else 1.0)) for x, y, z in _verts(b)])
    cmds.move(fx - 33.5, 80.5 + 32, (y0 + y1) / 2.0, b)
    keep(b, "tv_mat")
    # bezel and curved screen
    sy0, sy1, sz0, sz1 = y0 + 8, y1 - 24, 88, 142
    bevel_box(fx - 0.5, fx + 0.6, sy0 - 3, sy1 + 3, sz0 - 3, sz1 + 3, "trim_mat", r=0.4)
    p = cmds.polyPlane(w=sz1 - sz0, h=sy1 - sy0, sx=8, sy=8, ch=False)[0]           # in Maya XZ, normal +Y
    cmds.rotate(0, 0, -90, p)                                                        # normal +X (into the room)
    cmds.makeIdentity(p, apply=True, r=True)
    hw, hh = (sz1 - sz0) / 2.0, (sy1 - sy0) / 2.0
    _set_verts(p, [(x + 2.2 * max(0, 1 - (y / hw) ** 2) * max(0, 1 - (z / hh) ** 2), y, z) for x, y, z in _verts(p)])
    cmds.move(fx + 1.0, (sz0 + sz1) / 2.0, (sy0 + sy1) / 2.0, p)
    keep(p, "screen_mat")
    # controls: two knobs, a grille of slots
    for kz in (128, 114):
        tube((fx, y1 - 12, kz), (fx + 2.2, y1 - 12, kz), 3.2, "trim_mat", sides=12)
        box(fx + 2.2, fx + 2.8, y1 - 12.4, y1 - 11.6, kz - 2.2, kz + 2.2, "chair_mat")  # pointer
    for i in range(6):
        box(fx - 0.3, fx + 0.7, y1 - 17, y1 - 7, 90 + i * 2.6, 91.2 + i * 2.6, "glass_mat")
    # rabbit ears
    ax, ay = fx - 20, (y0 + y1) / 2.0
    sphere(ax, ay, 150.5, 4.5, "tv_mat", sides=10, scale=(1, 1, 0.6))
    for dy in (-1, 1):
        tip = (ax - 4, ay + dy * 32, 196)
        tube((ax, ay + dy * 1.5, 152), tip, 0.35, "metal_mat", sides=4)
        sphere(*tip, 0.9, "metal_mat", sides=6)


# ---------- Cas's things (Room 104) ----------

def diary(cx, cy, cz, yaw):
    """A small hardback: two covers, the page block (pages torn out: a ragged edge), a spine."""
    rbevel(cx, cy, cz + 0.3, 15, 20, 0.6, "diary_mat", r=0.25, yaw=yaw)
    rbox(cx + 0.4, cy, cz + 1.6, 14, 19, 2.0, "page_mat", yaw=yaw)
    rbevel(cx, cy, cz + 2.9, 15, 20, 0.6, "diary_mat", r=0.25, yaw=yaw)
    a = math.radians(yaw)
    rbevel(cx - 7.3 * math.cos(a), cy + 7.3 * math.sin(a), cz + 1.6, 1.2, 20, 3.2, "diary_mat", r=0.5, yaw=yaw)


def _sneaker_top(u):
    """Height (cm above the sole) of a sneaker's upper along its length, u = -1 heel .. 1 toe:
    collar at the heel, a dip at the ankle opening, the tongue, then a slope to a low toe."""
    keys = [(-1.0, 7.2), (-0.75, 8.0), (-0.45, 7.0), (-0.2, 8.4), (0.1, 7.2), (0.45, 5.2), (0.75, 3.8), (1.0, 2.2)]
    for (u0, h0), (u1, h1) in zip(keys, keys[1:]):
        if u <= u1:
            t = (u - u0) / (u1 - u0)
            return h0 + (h1 - h0) * (t * t * (3 - 2 * t))
    return keys[-1][1]


def sneaker(cx, cy, yaw, seed):
    """A canvas sneaker built from a side profile (_sneaker_top) and a foot-shaped outline
    (narrow heel, wide ball, rounded toe), smoothed; a white rubber sole and toe cap,
    a dark ankle opening, white laces lying on the tongue."""
    L, W = 28.0, 10.0
    c = cmds.polyCube(w=W, h=1, d=L, sx=4, sy=3, sz=12, ch=False)[0]
    pts = []
    for x, y, z in _verts(c):
        u, v, h = z / (L / 2), x / (W / 2), y + 0.5                    # h: 0 bottom, 1 top
        width = 0.78 + 0.22 * math.exp(-((u - 0.4) / 0.6) ** 2)
        if u > 0.75:
            width *= math.sqrt(max(0.05, 1 - ((u - 0.75) / 0.3) ** 2))   # round toe
        pts.append((v * (W / 2) * width * (1 - 0.3 * h * h), h * _sneaker_top(u) * 1.18, z))
    _set_verts(c, pts)
    cmds.polySmooth(c, dv=2, ch=False)
    _place(c, cx, cy, 2.6, "shoe_mat", yaw=yaw)
    a = math.radians(yaw)
    fx, fy = -math.sin(a), math.cos(a)                                  # shoe forward, Unreal x/y
    at = lambda d: (cx + fx * d, cy + fy * d)                           # a point d cm toward the toe
    rbevel(cx, cy, 1.9, W + 0.8, L + 0.6, 2.6, "sole_mat", r=1.1, seg=2, yaw=yaw)       # sole (white sides)
    rsoft(*at(11.8), 3.6, 7.6, 5.2, 3.4, "sole_mat", seed=seed, yaw=yaw)                # rubber toe cap
    sphere(*at(-8.4), 2.6 + _sneaker_top(-0.6) * 1.12, 3.0, "shoe_inner_mat", sides=12, scale=(1, 1.4, 0.3))  # opening
    for k in range(5):                                                  # laces on the tongue
        d = -1.5 + k * 2.4
        rbox(*at(d), 2.6 + _sneaker_top(d / (L / 2)) * 1.12 + 0.5, 6.4, 0.9, 0.8, "sole_mat", yaw=yaw, tilt_y=-12)


def mug(cx, cy, z):
    """Open-topped mug with a lining, a rim, a handle, and cold coffee a centimetre down."""
    frustum(cx, cy, z + 0.3, z + 9, 3.7, 4.1, "mug_mat", sides=18, open_ends=True)
    frustum(cx, cy, z + 1.0, z + 9, 3.25, 3.65, "mug_mat", sides=18, open_ends=True, inside=True)
    frustum(cx, cy, z + 0.3, z + 1.2, 3.7, 3.75, "mug_mat", sides=18)             # base
    ring(cx, cy, z + 9, 3.88, 0.24, "mug_mat", sides=18)                          # rim
    frustum(cx, cy, z + 7.0, z + 7.6, 3.5, 3.55, "coffee_mat", sides=18)          # the coffee
    ring(cx + 4.7, cy, z + 5, 2.3, 0.55, "mug_mat", axis="y", sides=12)          # handle


def plant_pot(cx, cy, z, rng):
    """Terracotta pot with a rolled rim and a saucer, lumpy dry soil, and a dead plant: long
    curving stems that droop over, with curled brown leaves along them."""
    frustum(cx, cy, z + 0.2, z + 1.4, 7.5, 7.8, "pot_mat", sides=24)                       # saucer
    frustum(cx, cy, z + 1.4, z + 11, 5.4, 7.0, "pot_mat", sides=24, open_ends=True)
    frustum(cx, cy, z + 1.4, z + 11, 4.9, 6.5, "pot_mat", sides=24, open_ends=True, inside=True)
    ring(cx, cy, z + 11, 7.1, 0.9, "pot_mat", sides=24)
    rsoft(cx, cy, z + 9.3, 12.6, 12.6, 1.6, "soil_mat", jitter=0.35, seed=60)
    for i in range(9):
        ang = i * 0.7 + rng.uniform(-0.2, 0.2)
        reach, rise = rng.uniform(7, 12), rng.uniform(18, 30)
        prev = (cx + math.cos(ang) * 1.0, cy + math.sin(ang) * 1.0, z + 9.8)
        n = 6
        for k in range(1, n + 1):                                    # a stem: up, out, then drooping
            t = k / n
            p = (cx + math.cos(ang) * reach * t ** 0.8, cy + math.sin(ang) * reach * t ** 0.8,
                 z + 9.8 + rise * math.sin(t * 2.4) / math.sin(2.4 * 0.62) * 0.62)
            tube(prev, p, 0.45 - 0.25 * t, "twig_mat", sides=5)
            if k in (3, 5, 6):                                       # curled dry leaves
                rsoft(p[0], p[1], p[2] - 0.6, 3.4, 1.6, 0.9, "leaf_dead_mat", jitter=0.25, sag=-0.4,
                      seed=i * 10 + k, yaw=math.degrees(ang) + rng.uniform(-40, 40), tilt_x=rng.uniform(-30, 30))
            prev = p


def side_table(tx, ty, tz):
    """Small wooden table: rounded top, apron, tapered legs (top surface at tz)."""
    rbevel(tx, ty, tz - 2, 80, 70, 4, "wood_mat", r=1.5)
    for (a, b, c_, d) in ((-36, 36, -31, -29), (-36, 36, 29, 31), (-36, -34, -31, 31), (34, 36, -31, 31)):
        box(tx + a, tx + b, ty + c_, ty + d, tz - 12, tz - 4.5, "wood_mat")
    for dx in (-33, 33):
        for dy in (-28, 28):
            frustum(tx + dx, ty + dy, 0, tz - 4.5, 1.6, 2.4, "wood_mat", sides=8)


def wood_chair(cx, cy, rng):
    """Seat, two back posts with three slats, tapered legs, and her jacket draped over it."""
    rbevel(cx, cy, 45, 42, 40, 4, "wood_mat", r=1.2)
    for dx in (-18, 18):
        frustum(cx + dx, cy - 16, 0, 43, 1.4, 2.0, "wood_mat", sides=8)
        frustum(cx + dx, cy + 17, 0, 92, 1.6, 2.0, "wood_mat", sides=8)                   # back posts
    for k, z in enumerate((62, 74, 86)):
        rbevel(cx, cy + 17, z, 34, 2, 6 if k < 2 else 9, "wood_mat", r=0.8)
    jacket(cx, cy + 17, 92)


def _drape(path, width, rows, cols, flare, folds, seed):
    """Cloth hanging along a path of (y, z) points: a grid, wider toward the hanging ends,
    with soft vertical folds. Returns the vertex grid (Unreal x offset, y, z)."""
    rng = random.Random(seed)
    lens = [0.0]
    for (y0, z0), (y1, z1) in zip(path, path[1:]):
        lens.append(lens[-1] + math.hypot(y1 - y0, z1 - z0))
    total = lens[-1]
    grid = []
    for r in range(rows + 1):
        s = total * r / rows
        k = max(i for i in range(len(lens)) if lens[i] <= s) if s < total else len(path) - 2
        k = min(k, len(path) - 2)
        t = (s - lens[k]) / max(1e-6, lens[k + 1] - lens[k])
        y = path[k][0] + (path[k + 1][0] - path[k][0]) * t
        z = path[k][1] + (path[k + 1][1] - path[k][1]) * t
        hang = min(1.0, abs(s - lens[3]) / 15.0)                      # 0 where it lies over the rail
        row = []
        for c in range(cols + 1):
            u = c / cols - 0.5
            x = u * width * (1 + flare * hang)
            dy = math.sin(u * folds * 6.283 + r * 0.35) * 1.3 * hang + rng.uniform(-0.25, 0.25)
            row.append((x, y + dy, z + rng.uniform(-0.3, 0.3)))
        grid.append(row)
    return grid


def _cloth(cx, grid, mat):
    """Build a two-sided mesh from a vertex grid (rows x cols), at Unreal x = cx."""
    rows, cols = len(grid) - 1, len(grid[0]) - 1
    for side in (0, 1):
        p = cmds.polyPlane(w=1, h=1, sx=cols, sy=rows, ch=False)[0]
        # polyPlane vertex order: row by row (Maya z), cols along Maya x
        pts = []
        for r in range(rows + 1):
            for c in range(cols + 1):
                x, y, z = grid[r][c]
                pts.append((x, z, y))                                   # Unreal (x, y, z) -> Maya (x, z, y)
        _set_verts(p, pts)
        if side:
            cmds.polyNormal(p, normalMode=0, userNormalMode=0, ch=False)
            cmds.move(0, 0, 0.35, p, relative=True)                     # the inside, a few mm behind
        cmds.polySoftEdge(p, angle=180, ch=False)
        cmds.move(cx, 0, 0, p, relative=True)
        keep(p, mat)


def jacket(cx, ty, tz):
    """Her jacket thrown over the chair back (top rail at ty, tz): the body hangs down the
    back and a shorter front flap, the collar bunched on top, both sleeves dangling."""
    path = [(ty - 4.5, tz - 30), (ty - 3.5, tz - 10), (ty - 2.2, tz + 1.5), (ty, tz + 3.2),
            (ty + 2.4, tz + 1.5), (ty + 4.2, tz - 12), (ty + 5.5, tz - 35), (ty + 6.5, tz - 48)]
    _cloth(cx, _drape(path, 44, 26, 12, 0.18, 2.5, 70), "jacket_mat")
    rsoft(cx, ty, tz + 3.6, 40, 8, 3.5, "jacket_mat", jitter=0.5, seed=71)                 # collar
    for side in (-1, 1):                                                                # sleeves
        top = (cx + side * 21, ty + 3.5, tz - 2)
        mid = (cx + side * 23.5, ty + 7.5, tz - 26)
        bot = (cx + side * 22.5, ty + 6.0, tz - 50)
        tube(top, mid, 3.6, "jacket_mat", sides=10)
        tube(mid, bot, 3.3, "jacket_mat", sides=10)
        sphere(*mid, 3.6, "jacket_mat", sides=10)                                       # elbow
        tube(bot, (bot[0], bot[1] - 0.5, bot[2] - 2.5), 3.5, "jacket_cuff_mat", sides=10)


def suitcase(sx, sy, rng):
    """Open hard-shell suitcase on a folding rack: rounded shell and lid, a handle, brass
    latches, straps, clothes folded inside."""
    for dx in (-40, 40):
        tube((sx + dx, sy - 25, 0), (sx + dx, sy + 25, 45), 1.2, "metal_mat", sides=6)
        tube((sx + dx, sy + 25, 0), (sx + dx, sy - 25, 45), 1.2, "metal_mat", sides=6)
    for dy in (-12, 12):
        rbox(sx, sy + dy, 45.5, 86, 6, 1, "strap_mat")
    bevel_box(sx - 40, sx + 40, sy - 25, sy + 25, 46.5, 64, "suitcase_mat", r=3, seg=3)
    bevel_box(sx - 37, sx + 37, sy - 22, sy + 22, 60, 64.6, "lining_mat", r=1)         # lining showing
    rbevel(sx, sy + 28, 89, 80, 5, 48, "suitcase_mat", r=2.5, seg=3, tilt_y=12)          # lid, open
    for dx in (-25, 25):
        box(sx + dx - 2, sx + dx + 2, sy - 26, sy - 25, 60, 63, "brass_mat")             # latches
    ring(sx, sy - 27, 58, 5, 1.0, "strap_mat", axis="y", sides=10)                       # handle
    for i, mat in enumerate(("clothes_a_mat", "clothes_b_mat", "clothes_c_mat")):
        rsoft(sx - 22 + i * 22, sy - 4, 67.5 + i * 0.6, 26, 36, 6, mat, jitter=0.7, sag=1, seed=20 + i,
              yaw=rng.uniform(-6, 6))


def camera(cx, cy, cz):
    """A film camera: rounded body, lens barrel with rings, viewfinder hump, film winder."""
    rbevel(cx, cy, cz + 4.5, 8, 14, 8.5, "camera_mat", r=1.2, yaw=20)
    rbevel(cx - 0.6, cy, cz + 9.6, 6, 5, 2.2, "camera_mat", r=0.8, yaw=20)
    a = math.radians(20)
    lx, ly = cx + 4 * math.cos(a), cy - 4 * math.sin(a)
    tube((lx, ly, cz + 4.5), (lx + 5 * math.cos(a), ly - 5 * math.sin(a), cz + 4.5), 3.0, "camera_mat", sides=14)
    tube((lx + 4.8 * math.cos(a), ly - 4.8 * math.sin(a), cz + 4.5),
         (lx + 5.6 * math.cos(a), ly - 5.6 * math.sin(a), cz + 4.5), 3.3, "metal_mat", sides=14)
    tube((lx + 5.6 * math.cos(a), ly - 5.6 * math.sin(a), cz + 4.5),
         (lx + 5.9 * math.cos(a), ly - 5.9 * math.sin(a), cz + 4.5), 2.2, "glass_mat", sides=14)
    tube((cx, cy + 5, cz + 8.8), (cx, cy + 5, cz + 10.2), 1.2, "metal_mat", sides=8)


def investigation_wall(wall_x, front):
    """Her investigation pinned up around the lake photos over the dresser: handwritten notes
    (tools/make_photos.py), a newspaper clipping, a hand-drawn lake map, a red pin in each,
    and red string between the ones she connected. wall_x = the wall face (+x into the room)."""
    items = {   # name: (y from FRONT, z centre, width, height, spin)
        "pic_note_names": (168, 192, 21, 28, -3),
        "pic_lake_map": (272, 248, 42, 30, 2),
        "pic_clipping": (392, 196, 24, 30, 4),
        "pic_note_night": (440, 238, 17, 21, -5),
        "pic_note_lights": (388, 246, 17, 21, 3),
        "pic_note_rattle": (160, 242, 17, 21, 6),
        "pic_note_scrawl": (446, 186, 17, 21, -2),
    }
    pins = {}
    for name, (dy, z, w, h, spin) in items.items():
        picture(wall_x + 2.0, front + dy, z, w, h, name, spin=spin)
        pin = (wall_x + 2.8, front + dy, z + h / 2.0 - 2.0)
        sphere(*pin, 0.8, "pin_mat", sides=8)
        pins[name] = pin
    pins["pic_lanterns"] = (wall_x + 2.8, front + 336, 214.5)           # the red-lights photo (taped)
    sphere(*pins["pic_lanterns"], 0.8, "pin_mat", sides=8)
    for a, b in (("pic_note_names", "pic_lake_map"), ("pic_lake_map", "pic_lanterns"),
                 ("pic_lanterns", "pic_note_lights"), ("pic_note_lights", "pic_note_night"),
                 ("pic_note_names", "pic_clipping"), ("pic_note_rattle", "pic_lake_map")):
        p, q = pins[a], pins[b]
        m = ((p[0] + q[0]) / 2.0 + 0.3, (p[1] + q[1]) / 2.0, (p[2] + q[2]) / 2.0 - 2.5)   # string sags a little
        tube((p[0] + 0.2, p[1], p[2]), m, 0.22, "red_string_mat", sides=4)
        tube(m, (q[0] + 0.2, q[1], q[2]), 0.22, "red_string_mat", sides=4)


def cobweb(corner, a_dir, b_dir, size, ceiling_z):
    """A web strung across a top corner, 1.5 cm off both walls and the ceiling: spokes fanning
    from the corner to the edges of a triangle (along both walls and down the corner), and
    rings of sagging cross threads. a_dir / b_dir: +-1 directions along x and y into the room."""
    cx, cy = corner
    o = 1.5
    c = (cx + a_dir * o, cy + b_dir * o, ceiling_z - o)
    A = (cx + a_dir * size, cy + b_dir * o, ceiling_z - o)
    B = (cx + a_dir * o, cy + b_dir * size * 0.85, ceiling_z - o)
    C = (cx + a_dir * o, cy + b_dir * o, ceiling_z - size * 0.9)
    lerp = lambda p, q, t: tuple(p[i] + (q[i] - p[i]) * t for i in range(3))
    ends = [lerp(A, B, t) for t in (0, 0.33, 0.66)] + [lerp(B, C, t) for t in (0, 0.33, 0.66)] + \
           [lerp(C, A, t) for t in (0, 0.33, 0.66)]
    for e in ends:
        tube(c, e, 0.32, "cobweb_mat", sides=4)
    for f in (0.22, 0.4, 0.58, 0.76, 0.95):
        ring_pts = [lerp(c, e, f) for e in ends] + [lerp(c, ends[0], f)]
        for p, q in zip(ring_pts, ring_pts[1:]):
            m = lerp(p, q, 0.5)
            m = (m[0], m[1], m[2] - 1.2 * f)                              # sag
            tube(p, m, 0.24, "cobweb_mat", sides=3)
            tube(m, q, 0.24, "cobweb_mat", sides=3)
    for e, droop in ((ends[1], 14), (ends[7], 9)):                        # loose strands hanging down
        tube(lerp(c, e, 0.8), (lerp(c, e, 0.8)[0], lerp(c, e, 0.8)[1], lerp(c, e, 0.8)[2] - droop), 0.2, "cobweb_mat", sides=3)

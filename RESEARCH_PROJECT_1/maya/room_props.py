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


def rsoft(cx, cy, cz, sx, sy, sz, mat, jitter=0.0, sag=0.0, smooth=2, seed=0, div=(3, 2, 3), **turn):
    """A soft, rounded lump exactly sx * sy * sz: a subdivided box smoothed round, then
    sag pushes the middle of the top down (a dent, a slump) and jitter adds random
    wrinkles (cm). Pillows, bedding, clothes."""
    c = cmds.polyCube(w=1, h=1, d=1, sx=div[0], sy=div[1], sz=div[2], ch=False)[0]
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
            pillow(px, by1 - 34, 57.5, 70, 44, 14, int(x0) + k, yaw=(-3, 4)[k], tilt_y=-10, dent=1.5)


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
    lathe(lx, ly, [(60.3, 7.8), (60.9, 8.1), (61.8, 7.9), (62.5, 6.8), (63.1, 4.6), (63.8, 2.6), (64.6, 1.4)],
          "brass_mat", sides=24)                                    # one turned piece: no clashing parts
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
    """Her diary lying shut on the nightstand: two hard covers, the page block (a few torn-out
    stubs sticking out at the spine), a rounded spine, an elastic strap and a red ribbon
    bookmark hanging out. Every part is placed in the book's own frame, then turned by yaw."""
    a = math.radians(yaw)
    def at(dx, dy):                                    # book frame (x across, y up the page) -> world
        return cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)
    W, D = 15.0, 20.0
    rbevel(*at(0, 0), cz + 0.3, W, D, 0.6, "diary_mat", r=0.25, yaw=yaw)                     # back cover
    rbox(*at(0.6, 0), cz + 1.65, W - 1.6, D - 1.2, 2.1, "page_mat", yaw=yaw)                  # pages
    rbevel(*at(0, 0), cz + 3.0, W, D, 0.6, "diary_mat", r=0.25, yaw=yaw)                     # front cover
    rsoft(*at(-W / 2 + 0.2, 0), cz + 1.65, 1.6, D, 3.3, "diary_mat", smooth=2, yaw=yaw)       # rounded spine
    for k, dy in enumerate((-4.5, 1.0, 5.5)):                                                 # torn stubs
        rbox(*at(-W / 2 + 1.9, dy), cz + 1.0 + k * 0.6, 1.4, 2.8, 0.15, "page_mat", yaw=yaw + 8 * (k - 1))
    rbox(*at(W / 2 - 3.0, 0), cz + 1.65, 0.8, D + 0.3, 3.6, "strap_mat", yaw=yaw)            # elastic strap
    rbox(*at(2.0, D / 2 + 2.5), cz + 0.85, 0.7, 5.5, 0.12, "pin_mat", yaw=yaw + 6)           # ribbon


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
    folded(sx - 22, sy - 3, 64.8, 22, 34, "clothes_a_mat", "shirt", 20)
    folded(sx, sy - 2, 64.8, 22, 36, "clothes_b_mat", "jeans", 21)
    folded(sx + 22, sy - 3, 64.8, 22, 34, "clothes_c_mat", "sweater", 22)


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
                 ("pic_note_rattle", "pic_lake_map")):
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


def flat_picture(cx, cy, z, w, h, mat, yaw=0):
    """A picture lying flat, face up (a torn page on a table or the floor)."""
    p = cmds.polyPlane(w=w, h=h, sx=1, sy=1, ch=False)[0]
    return _place(p, cx, cy, z, mat, yaw=yaw)


def pen(cx, cy, z, yaw):
    """A ballpoint lying on the table: barrel, cap with a clip, a little cone tip."""
    a = math.radians(yaw)
    fx, fy = math.cos(a), math.sin(a)
    p = lambda d, up=0.0: (cx + fx * d, cy + fy * d, z + 0.5 + up)
    tube(p(-6.5), p(4.5), 0.45, "chair_mat", sides=8)
    tube(p(4.5), p(6.0), 0.35, "chair_mat", sides=8)
    frustum(*p(6.0)[:2], z + 0.32, z + 0.68, 0.18, 0.18, "metal_mat", sides=6)
    tube(p(-7.0), p(-3.0), 0.52, "pen_mat", sides=8)                                   # cap
    rbox(*p(-4.8)[:2], z + 1.05, 3.4, 0.35, 0.25, "metal_mat", yaw=yaw)                # clip


def window_inside(wx0, wx1, lit=False, gap=0.0):
    """The inside of a room's window: a wooden sill and casing, a curtain rod, and curtains.
    lit=True: closed and glowing (a lamp on behind them, seen from the lot); otherwise pulled
    back to the sides so you can see out."""
    y = FRONT + 20 + 2                                    # face of the inside wall lining
    z0, z1 = WIN[2], WIN[3]
    bevel_box(wx0 - 7, wx1 + 7, FRONT + 20, y + 8, z0 - 4, z0 + 0.5, "wood_mat", r=0.8)         # sill
    for a, b, c_, d in ((wx0 - 6, wx0, z0, z1 + 6), (wx1, wx1 + 6, z0, z1 + 6), (wx0 - 6, wx1 + 6, z1, z1 + 6)):
        bevel_box(a, b, y, y + 1.5, c_, d, "wood_mat", r=0.4)                                 # casing
    # rod and curtains hang in front of the sill (y + 8), so they never cut through the frame
    tube((wx0 - 32, y + 12.5, z1 + 14), (wx1 + 32, y + 12.5, z1 + 14), 0.9, "brass_mat", sides=8)   # rod
    for ex in (wx0 - 32, wx1 + 32):
        tube((ex, y + 0.2, z1 + 14), (ex, y + 12.5, z1 + 14), 0.6, "brass_mat", sides=6)            # brackets
    # curtains drawn shut (lit ones glow: a lamp on behind them, seen from the lot). gap: how far
    # apart they are in the middle (Room 104: a crack to look out of). The right panel hangs
    # 3 cm in front of the left so where they overlap they never fight.
    mid = (wx0 + wx1) / 2.0
    mat = "glow_window_mat" if lit else "curtain_mat"
    for k, (a, b, dy) in enumerate(((wx0 - 26, mid + 2 - gap / 2.0, 0.0), (mid - 2 + gap / 2.0, wx1 + 8, 3.0))):
        curtain((a + b) / 2.0, y + 10 + dy, 2.5, z1 + 13, b - a, mat, seed=int(a) + k, pleats=5)


def ceiling_fan(cx, cy, ceiling_z, lit=False):
    """An old motel ceiling fan with a light kit: canopy, downrod, motor housing with a trim
    ring, five wooden blades on brass irons, a frosted glass bowl (glowing when lit=True)
    and a pull chain."""
    top = ceiling_z - 1.0
    frustum(cx, cy, top - 4, top, 4.5, 7.5, "brass_mat", sides=20)                  # canopy
    tube((cx, cy, top - 4), (cx, cy, top - 30), 1.1, "brass_mat", sides=10)          # downrod
    mz = top - 36
    frustum(cx, cy, mz + 3.7, mz + 7, 9.3, 5, "fan_mat", sides=24)                   # motor housing
    frustum(cx, cy, mz - 2, mz + 4, 10, 9.5, "fan_mat", sides=24)
    ring(cx, cy, mz + 1, 10.1, 0.6, "brass_mat", sides=24)
    frustum(cx, cy, mz - 5, mz - 1.7, 7, 9.8, "fan_mat", sides=24)   # (pieces overlap: no shared faces)
    for k in range(5):                                                               # blades
        a = math.radians(k * 72 + 12)
        ex, ey = math.cos(a), math.sin(a)
        tube((cx + ex * 7, cy + ey * 7, mz - 1), (cx + ex * 18, cy + ey * 18, mz - 2.5), 0.9, "brass_mat", sides=6)
        rbevel(cx + ex * 38, cy + ey * 38, mz - 2.8, 46, 13, 0.9, "wood_mat", r=0.35, yaw=math.degrees(a), tilt_x=6)
    bz = mz - 5
    frustum(cx, cy, bz - 3, bz + 0.3, 5.5, 6.8, "brass_mat", sides=20)               # light kit fitter
    sphere(cx, cy, bz - 9, 10, "glow_lamp_mat" if lit else "bowl_mat", sides=20, scale=(1, 1, 0.62))   # bowl
    sphere(cx, cy, bz - 15.4, 1.0, "brass_mat", sides=8)                             # finial
    tube((cx + 5, cy, bz - 3), (cx + 5, cy, bz - 26), 0.18, "brass_mat", sides=3)    # pull chain
    sphere(cx + 5, cy, bz - 26.8, 0.8, "brass_mat", sides=6)


def curtain(cx, y_face, z_bot, z_top, width, mat, seed, pleats=6, depth=2.6):
    """A floor-length curtain hanging from the rod: pleated folds across, sagging slightly
    and flaring out a little toward the hem, gathered at the top."""
    rng = random.Random(seed)
    rows, cols = 16, pleats * 4
    grid = []
    for r in range(rows + 1):
        t = r / rows                                       # 0 hem .. 1 top
        z = z_bot + (z_top - z_bot) * t
        row = []
        for c in range(cols + 1):
            u = c / cols - 0.5
            x = u * width * (1.08 - 0.12 * t)
            fold = math.sin(u * pleats * 6.283) * depth * (0.7 + 0.3 * (1 - t))
            row.append((x, y_face + 2.5 + fold + rng.uniform(-0.2, 0.2), z + rng.uniform(-0.3, 0.3) * (1 - t)))
        grid.append(row)
    _cloth(cx, grid, mat)


def bedspread(bx0, bx1, by0, fold_y, top_z, keep_flat=None, seed=0, mat="bedspread_mat", hang=30.0):
    """A real bedspread thrown back: one cloth that lies over the bed from the foot to fold_y,
    hangs down both sides and over the foot with soft folds, then is turned back on itself
    in a loose roll. keep_flat = (x, y, r): a calm patch with no wrinkles (the note lies there)."""
    rng = random.Random(seed)
    hw = (bx1 - bx0) / 2.0 + 1.5
    mid = (bx0 + bx1) / 2.0
    # hang: how far it drapes down the sides
    # path along the bed (y, z): hanging over the foot, across the top, the fold, turned back
    path = [(by0 - 3.0, top_z - hang), (by0 - 2.0, top_z - 12), (by0 + 2, top_z), (fold_y, top_z + 0.5),
            (fold_y + 4, top_z + 3.0), (fold_y + 2, top_z + 6.0), (fold_y - 6, top_z + 5.2), (fold_y - 34, top_z + 3.4)]
    lens = [0.0]
    for (y0, z0), (y1, z1) in zip(path, path[1:]):
        lens.append(lens[-1] + math.hypot(y1 - y0, z1 - z0))
    rows, cols = 42, 36
    grid = []
    for r in range(rows + 1):
        s = lens[-1] * r / rows
        k = min(max(i for i in range(len(lens)) if lens[i] <= s), len(path) - 2)
        t = (s - lens[k]) / max(1e-6, lens[k + 1] - lens[k])
        y = path[k][0] + (path[k + 1][0] - path[k][0]) * t
        z = path[k][1] + (path[k + 1][1] - path[k][1]) * t
        on_top = k >= 2
        turned = k >= 4                                    # the folded-back layer: narrower, no side drop
        row = []
        for c in range(cols + 1):
            u = c / cols * 2 - 1                           # -1 .. 1 across
            span = hw + (0 if turned else hang)
            x = u * span
            zz, yy = z, y
            if not turned and abs(x) > hw:                 # over the side: hangs down, flares a little
                d = abs(x) - hw
                x = math.copysign(hw + 1.5 + d * 0.12, x)
                zz = min(z, top_z) - d
                yy += math.sin(y * 0.06 + seed) * 2.2 * (d / hang)        # a few broad folds in the drop
            if turned:
                x = u * (hw - 3)
            w = 0.7 * math.sin(x * 0.045 + y * 0.035 + seed) + 0.35 * math.sin(x * 0.03 - y * 0.06)   # broad, gentle
            if keep_flat:
                fx, fy, fr = keep_flat
                w *= min(1.0, math.hypot(mid + x - fx, yy - fy) / fr)
            if on_top and abs(x) <= hw:
                zz += max(-0.3, w)
            row.append((x, yy, zz))
        grid.append(row)
    _cloth(mid, grid, mat)


def folded(cx, cy, z, w, d, mat, kind, seed):
    """A folded piece of clothing lying in the suitcase (z = what it lies on), textured fabric
    (tools/make_fabrics.py): a soft body with a rounded fold along the front, then what makes
    it that garment. shirt: flannel, a real collar (band + two points), placket, buttons and
    one sleeve hanging out over the front of the case. jeans: denim, waistband with belt
    loops, button and fly. sweater: knit, both sleeves folded across the front, ribbed hem."""
    rsoft(cx, cy, z + 1.7, w, d, 3.4, mat, jitter=0.15, sag=0.4, smooth=2, seed=seed, div=(4, 2, 5))
    tube((cx - w / 2 + 1.8, cy - d / 2 + 1.8, z + 2.0), (cx + w / 2 - 1.8, cy - d / 2 + 1.8, z + 2.0), 1.8, mat, sides=14)
    for ex in (cx - w / 2 + 1.8, cx + w / 2 - 1.8):
        sphere(ex, cy - d / 2 + 1.8, z + 2.0, 1.8, mat, sides=12)
    top = z + 3.4
    back = cy + d / 2
    if kind == "shirt":
        rsoft(cx, back - 4, top + 0.9, 11, 3.2, 1.8, mat, smooth=2, seed=seed + 1)                       # collar band
        for side in (-1, 1):                                                                            # collar points
            rsoft(cx + side * 3.2, back - 7.5, top + 0.7, 5, 5.5, 1.0, mat, smooth=2, seed=seed + 2,
                  yaw=side * 28)
        rbox(cx, cy - 1, top + 0.25, 2.4, d - 16, 0.5, mat)                                            # placket
        for k in range(4):
            frustum(cx, back - 12 - k * 6, top + 0.4, top + 0.75, 0.55, 0.5, "sole_mat", sides=10)      # buttons
        # one sleeve slid out over the front edge of the case, hanging down outside it
        p0 = (cx - w / 2 + 3, cy - d / 2 + 4, top - 0.5)
        pts = [p0, (p0[0] - 2, p0[1] - 8, top + 0.6), (p0[0] - 3, p0[1] - 13, top - 3),
               (p0[0] - 3.5, p0[1] - 15, top - 14), (p0[0] - 3, p0[1] - 15.5, top - 24)]
        for a, b in zip(pts, pts[1:]):
            tube(a, b, 3.0, mat, sides=12)
            sphere(*b, 3.0, mat, sides=12)
        tube(pts[-1], (pts[-1][0], pts[-1][1], pts[-1][2] - 4), 3.2, mat, sides=12)                    # cuff
    elif kind == "jeans":
        rsoft(cx, back - 2.5, top + 0.4, w - 1, 4.5, 1.6, mat, smooth=2, seed=seed + 1)                  # waistband
        for dx in (-w / 2 + 3, -3, 3, w / 2 - 3):
            rbox(cx + dx, back - 2.5, top + 1.25, 1.2, 4.8, 0.5, mat)                                   # belt loops
        sphere(cx, back - 2.5, top + 1.3, 0.8, "brass_mat", sides=10)                                  # button
        rbox(cx, back - 12, top + 0.2, 0.4, 15, 0.3, "brass_mat")                                       # fly stitch
        rbox(cx + 2.5, back - 12, top + 0.2, 0.3, 15, 0.3, "brass_mat")
        rbox(cx, cy - 4, top + 0.15, 0.4, d - 18, 0.25, "strap_mat")                                    # leg seam
    elif kind == "sweater":
        rsoft(cx, back - 3, top + 0.6, w - 3, 5, 2.0, mat, smooth=2, seed=seed + 1)                       # neck
        for side in (-1, 1):                                                                            # sleeves crossed
            rsoft(cx, cy + 1, top + 1.0 + (0.9 if side > 0 else 0), w * 1.05, 6.5, 2.2, mat, smooth=2,
                  seed=seed + 2 + side, yaw=side * 38)
        for k in range(8):                                                                              # ribbed hem
            rbox(cx - w / 2 + 2.5 + k * (w - 5) / 7, cy - d / 2 + 5, top - 0.2, 0.8, 6, 0.6, mat)


def pillow(cx, cy, z, w, d, h, seed, yaw=0, tilt_y=0, dent=2.5):
    """A real pillow: plump in the middle, pinched thin at the seam all round and at the four
    corners, a soft head dent, slightly uneven. z = what it lies on."""
    r = random.Random(seed)
    c = cmds.polyCube(w=1, h=1, d=1, sx=10, sy=2, sz=7, ch=False)[0]
    pts = []
    for x, y, zz in _verts(c):
        u, v = x * 2, zz * 2                                       # -1 .. 1 across / along
        puff = (max(0.0, 1 - abs(u) ** 2.4)) ** 0.55 * (max(0.0, 1 - abs(v) ** 2.4)) ** 0.55
        thick = 0.12 + 0.88 * puff                                 # seam stays ~12 % thick
        yy = y * h * thick
        if y > 0:
            yy -= dent * max(0.0, 1 - (u / 0.6) ** 2) * max(0.0, 1 - (v / 0.7) ** 2)
        cu = 1 + 0.06 * (abs(u) * abs(v)) ** 3                    # corners poke out a little
        pts.append((x * w * cu + r.uniform(-0.3, 0.3), yy + h / 2.0 * 0.12 + r.uniform(-0.15, 0.15), zz * d * cu))
    _set_verts(c, pts)
    cmds.polySmooth(c, dv=2, ch=False)
    bb = cmds.exactWorldBoundingBox(c)
    cmds.move(0, -bb[1], 0, c, relative=True)                      # bottom on z
    cmds.makeIdentity(c, apply=True, t=True)
    cmds.xform(c, pivots=(0, 0, 0))
    return _place(c, cx, cy, z, "pillow_mat", yaw=yaw, tilt_y=tilt_y)


def lathe(cx, cy, profile, mat, sides=24):
    """A turned (lathed) solid: profile = [(z, radius), ...] from the bottom up, closed at both
    ends, smooth shading around it. Lamp bases, knobs, anything round with a profile."""
    n = len(profile)
    c = cmds.polyCylinder(r=1, h=1, sx=sides, sy=n - 1, sz=0, ch=False)[0]
    pts = []
    for x, y, z in _verts(c):
        k = int(round((y + 0.5) * (n - 1)))
        k = max(0, min(n - 1, k))
        pz, pr = profile[k]
        d = math.hypot(x, z)
        f = pr / d if d > 1e-6 else 0.0
        pts.append((x * f, pz, z * f))
    _set_verts(c, pts)
    cmds.polySoftEdge(c, angle=50, ch=False)
    cmds.move(cx, 0, cy, c, relative=True)
    return keep(c, mat)

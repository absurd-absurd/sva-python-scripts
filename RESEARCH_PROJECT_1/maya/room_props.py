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


def sneaker(cx, cy, yaw, seed):
    """Sole, a soft upper, a rounded toe cap and laces."""
    a = math.radians(yaw)
    fx, fy = math.sin(a), math.cos(a)                 # along the shoe
    rbevel(cx, cy, 1.5, 10, 28, 3, "sole_mat", r=1.2, yaw=yaw)
    rsoft(cx - fx * 3, cy - fy * 3, 7, 9, 20, 8, "shoe_mat", jitter=0.3, seed=seed, yaw=yaw)
    rsoft(cx + fx * 9, cy + fy * 9, 5, 9, 9, 5.5, "shoe_mat", seed=seed + 1, yaw=yaw)
    for k in range(3):
        rbox(cx + fx * (2 - k * 3), cy + fy * (2 - k * 3), 10.6, 5, 0.8, 0.5, "sole_mat", yaw=yaw)


def mug(cx, cy, z):
    frustum(cx, cy, z + 0.3, z + 9, 3.7, 4.1, "mug_mat", sides=14)
    frustum(cx, cy, z + 7.8, z + 8.4, 3.6, 3.7, "coffee_mat", sides=14)
    ring(cx + 4.6, cy, z + 5, 2.4, 0.6, "mug_mat", axis="y", sides=10)


def plant_pot(cx, cy, z, rng):
    frustum(cx, cy, z + 0.3, z + 11, 5.5, 7.2, "pot_mat", sides=14)
    ring(cx, cy, z + 11, 7.2, 0.8, "pot_mat", sides=14)
    frustum(cx, cy, z + 9.2, z + 9.8, 6.5, 6.6, "soil_mat", sides=14)
    for i in range(7):                                                               # dead stems, drooping
        ang = i * 0.9
        top = (cx + math.cos(ang) * 8, cy + math.sin(ang) * 8, z + 27 + rng.uniform(-4, 6))
        tube((cx, cy, z + 9.5), top, 0.5, "twig_mat", sides=3)
        end = (top[0] + math.cos(ang) * 6, top[1] + math.sin(ang) * 6, top[2] - 8)
        tube(top, end, 0.4, "twig_mat", sides=3)
        rsoft(end[0], end[1], end[2] - 0.5, 3, 1.5, 0.8, "leaf_dead_mat", seed=i, yaw=rng.uniform(0, 180))


def side_table(tx, ty, tz):
    """Small wooden table: rounded top, apron, tapered legs (top surface at tz)."""
    rbevel(tx, ty, tz - 2, 80, 70, 4, "wood_mat", r=1.5)
    for (a, b, c_, d) in ((-36, 36, -31, -29), (-36, 36, 29, 31), (-36, -34, -31, 31), (34, 36, -31, 31)):
        box(tx + a, tx + b, ty + c_, ty + d, tz - 12, tz - 4.5, "wood_mat")
    for dx in (-33, 33):
        for dy in (-28, 28):
            frustum(tx + dx, ty + dy, 0, tz - 4.5, 1.6, 2.4, "wood_mat", sides=8)


def wood_chair(cx, cy, rng):
    """Seat, two back posts with three slats, tapered legs, and her jacket slumped over it."""
    rbevel(cx, cy, 45, 42, 40, 4, "wood_mat", r=1.2)
    for dx in (-18, 18):
        frustum(cx + dx, cy - 16, 0, 43, 1.4, 2.0, "wood_mat", sides=8)
        frustum(cx + dx, cy + 17, 0, 92, 1.6, 2.0, "wood_mat", sides=8)                   # back posts
    for k, z in enumerate((62, 74, 86)):
        rbevel(cx, cy + 17, z, 34, 2, 6 if k < 2 else 9, "wood_mat", r=0.8)
    # jacket: hanging behind the back, collar over the top, a sleeve dangling
    rsoft(cx, cy + 21.5, 72, 44, 5, 40, "jacket_mat", jitter=1.0, seed=7, tilt_y=4)
    rsoft(cx, cy + 17, 93.5, 46, 12, 5, "jacket_mat", jitter=0.6, seed=8)
    rsoft(cx, cy + 13.5, 84, 40, 4, 20, "jacket_mat", jitter=0.8, seed=9, tilt_y=-6)
    rsoft(cx - 24, cy + 19, 64, 8, 9, 46, "jacket_mat", jitter=0.8, seed=10, tilt_x=-6)


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

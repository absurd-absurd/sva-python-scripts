"""Detailed outside of the Marrow Falls Motel (loaded by make_motel.py after room_props.py, so it
can use box, tube, bevel_box, rbevel, rsoft, frustum, sphere, ring, lathe, light, ...).
Replaces the first-pass block versions of: the room fronts, the awning, the office trim, the ICE
machine, the chairs, the lamp posts (all one cool green-white now, like the streetlight), the
payphone, the dumpster, the parking lot details and the car; and builds the swinging room and
office doors as their own meshes (export/prop_*.fbx, used by unreal/place_clues.py).
The rooftop MOTEL sign and the neon cross are not touched.
Positions are Unreal cm. Nothing lies closer than ~8 mm to a surface it sits on (z-fighting).
"""

COOL = [0.45, 1.0, 0.7]          # the streetlight's colour: every lamp post uses it now


# ---------- the room fronts ----------

def facade(x0, x1, i, number):
    """The outside of one room: brick base with a concrete cap, stepped door casing, framed
    window with a sloped sill, a numbered plate with screws, a wall AC unit under some windows,
    a doormat, and a plastic chair by some doors."""
    door_x0, door_x1 = x0 + 140, x0 + 280
    wx0, wx1 = x0 + WIN[0], x0 + WIN[1]
    # brick base and its cap
    for a, b in ((x0, door_x0 - 10), (door_x1 + 10, x1)):
        bevel_box(a, b, FRONT - 3.5, FRONT, 0, 100, "brick_mat", r=0.6)
        bevel_box(a - 1, b + 1, FRONT - 6, FRONT, 100, 106, "concrete_mat", r=1.2)
    # door casing: an outer flat band and an inner stop, a header with a little cornice
    for (a, b) in ((door_x0 - 10, door_x0), (door_x1, door_x1 + 10)):
        bevel_box(a, b, FRONT - 4, FRONT, 0, 240, "trim_mat", r=0.8)
    bevel_box(door_x0 - 10, door_x1 + 10, FRONT - 4, FRONT, 230, 240, "trim_mat", r=0.8)
    bevel_box(door_x0 - 14, door_x1 + 14, FRONT - 7, FRONT, 240, 245, "trim_mat", r=1.0)
    for (a, b) in ((door_x0 - 1.5, door_x0 + 0.5), (door_x1 - 0.5, door_x1 + 1.5)):
        bevel_box(a, b, FRONT - 6, FRONT - 3.5, 0, 231, "trim_mat", r=0.4)
    # window: casing, inner stop, middle bar, sloped sill with a drip edge, glass
    for a, b, c_, d in ((wx0 - 9, wx0, 100, 222), (wx1, wx1 + 9, 100, 222),
                        (wx0 - 9, wx1 + 9, WIN[3], 222), (wx0 - 9, wx1 + 9, 100, WIN[2])):
        bevel_box(a, b, FRONT - 5, FRONT, c_, d, "trim_mat", r=0.8)
    for a, b, c_, d in ((wx0, wx0 + 2, WIN[2], WIN[3]), (wx1 - 2, wx1, WIN[2], WIN[3]),
                        (wx0, wx1, WIN[3] - 2, WIN[3]), (wx0, wx1, WIN[2], WIN[2] + 2)):
        box(a, b, FRONT - 4.6, FRONT - 1.0, c_, d, "trim_mat")
    bevel_box((wx0 + wx1) / 2.0 - 2.5, (wx0 + wx1) / 2.0 + 2.5, FRONT - 5, FRONT - 1, WIN[2], WIN[3], "trim_mat", r=0.6)
    box(wx0, wx1, FRONT - 3.6, FRONT - 3.0, WIN[2], WIN[3], "seeglass_window_mat")
    rbevel((wx0 + wx1) / 2.0, FRONT - 7, 101.5, wx1 - wx0 + 26, 14, 4, "concrete_mat", r=1.0, tilt_y=-6)
    box(wx0 - 12, wx1 + 12, FRONT - 14.5, FRONT - 13.5, 97, 99.5, "concrete_mat")
    # room number plate: dark plate, bevelled, four screws, brass digits
    px = (door_x0 + door_x1) / 2.0
    bevel_box(px - 32, px + 32, FRONT - 9, FRONT - 6, 248, 272, "trim_mat", r=0.8)
    for sx in (-28, 28):
        for sz in (251.5, 268.5):
            sphere(px + sx, FRONT - 9.4, sz, 0.7, "brass_mat", sides=6)
    sign_word(str(number), px, FRONT - 9, 253, 14, 1.5, "brass_mat", 2.5)
    # through-wall air conditioner under the window in some rooms
    if i in (0, 2, 4, 5):
        ax = (wx0 + wx1) / 2.0
        bevel_box(ax - 34, ax + 34, FRONT - 38, FRONT - 6, 48, 92, "ac_mat", r=2.0)
        for k in range(9):
            box(ax - 28, ax + 28, FRONT - 38.8, FRONT - 37.6, 54 + k * 4, 56 + k * 4, "trim_mat")   # louvres
        for k in range(5):
            box(ax - 30 + k * 15, ax - 28 + k * 15, FRONT - 26, FRONT - 7, 92.2, 92.9, "trim_mat")  # top vents
        for sx in (-30, 30):
            tube((ax + sx, FRONT - 36, 48), (ax + sx, FRONT - 8, 26), 1.2, "metal_mat", sides=6)    # brackets
        blot(ax + 10, FRONT - 34, 14, "stain_mat", z=12)                     # drip stain on the walkway
    # a worn doormat in front of some doors
    if i in (1, 3, 4):
        rsoft(px, FRONT - 40, 13.4, 90, 55, 1.2, "doormat_mat", jitter=0.15, seed=i)
    if i in (0, 2, 4):
        chair(x0 + 60, FRONT - 120)


def chair(x, y):
    """A white plastic stacking patio chair, facing the lot: a slatted seat with a rolled front,
    a curved slatted back, arms, splayed legs with feet."""
    m = "chair_mat"
    z = 12.6                                                              # sits on the walkway
    rsoft(x, y, z + 42, 48, 44, 3.2, m, sag=0.8, smooth=2, seed=int(x))  # seat
    for k in range(4):
        box(x - 20, x + 20, y - 14 + k * 9, y - 13 + k * 9, z + 43.6, z + 44.3, "trim_mat")   # seat slots
    rsoft(x, y + 22, z + 70, 46, 4, 40, m, sag=-1.5, smooth=2, seed=int(x) + 1, tilt_y=-10)  # back
    for k in range(5):
        box(x - 18 + k * 9, x - 17 + k * 9, y + 24.5, y + 25.5, z + 56, z + 84, "trim_mat")  # back slots
    for s in (-1, 1):
        tube((x + s * 24, y - 18, z + 62), (x + s * 24, y + 20, z + 64), 2.0, m, sides=8)   # arms
        tube((x + s * 24, y - 18, z + 62), (x + s * 24, y - 16, z + 44), 1.8, m, sides=8)
        for dy in (-18, 18):
            frustum(x + s * (22 + 3), y + dy * 1.1, z + 0.5, z + 42, 2.6, 2.0, m, sides=8)   # legs
            sphere(x + s * 25, y + dy * 1.1, z + 0.9, 2.4, m, sides=8, scale=(1, 1, 0.4))     # feet


# ---------- the awning ----------

def corrugated(x0, x1, y0, y1, z, mat, pitch=8.0, depth=2.2):
    """A corrugated metal sheet: one plane rippled in a sine wave across x."""
    n = int((x1 - x0) / (pitch / 4.0))
    p = cmds.polyPlane(w=x1 - x0, h=y1 - y0, sx=min(n, 2000), sy=1, ch=False)[0]
    pts = [(x, depth * 0.5 * math.sin((x + (x1 - x0) / 2.0) / pitch * 2 * math.pi), zz) for x, y, zz in _verts(p)]
    _set_verts(p, pts)
    cmds.polySoftEdge(p, angle=80, ch=False)
    cmds.move((x0 + x1) / 2.0, z, (y0 + y1) / 2.0, p)
    keep(p, mat)
    p2 = cmds.duplicate(p)[0]                                            # the underside, facing down
    cmds.polyNormal(p2, normalMode=0, ch=False)
    cmds.move(0, -0.4, 0, p2, relative=True)
    keep(p2, mat)


def awning():
    """Corrugated metal awning on steel posts: the rippled roof (and its underside), a fascia
    board with a gutter and downspouts at both ends, posts with base plates and bolts and knee
    braces, the red neon strip, and the walkway slab with its expansion joints."""
    xa, xb = X0 - 40, X0 + ROOMS * ROOM_W + 40
    y_front = FRONT - WALK
    bevel_box(xa, xb, y_front, BACK + 40, H, H + 5, "roof_metal_mat", r=1.0)       # deck under the sheet
    corrugated(xa, xb, y_front - 4, BACK + 44, H + 8, "roof_metal_mat")
    bevel_box(xa, xb, y_front - 8, y_front, H - 30, H + 12, "trim_mat", r=1.2)      # fascia
    tube((xa, y_front - 15, H + 6), (xb, y_front - 15, H + 6), 6.5, "metal_mat", sides=12)   # gutter
    for gx in (xa + 12, xb - 12):                                                   # downspouts
        tube((gx, y_front - 15, H + 6), (gx, y_front - 15, 22), 4.5, "metal_mat", sides=10)
        tube((gx, y_front - 15, 22), (gx, y_front - 40, 13.5), 4.5, "metal_mat", sides=10)
        for zz in (80, 200):
            box(gx - 5, gx + 5, y_front - 11, y_front - 9, zz, zz + 2, "metal_mat")
    tube((xa, y_front - 10, H - 26), (xb, y_front - 10, H - 26), 2.5, "glow_neon_red_mat")   # neon strip
    for i in range(ROOMS + 1):                                                    # posts
        x = X0 + i * ROOM_W
        bevel_box(x - 7, x + 7, y_front + 11, y_front + 25, 13, H, "post_mat", r=1.2)
        bevel_box(x - 13, x + 13, y_front + 5, y_front + 31, 12.4, 14.4, "metal_mat", r=0.5)   # base plate
        for bx in (-10, 10):
            for by in (8, 28):
                sphere(x + bx, y_front + by, 14.8, 0.9, "metal_mat", sides=6)
        for s in (-1, 1):                                                        # knee braces
            tube((x + s * 7, y_front + 18, H - 40), (x + s * 40, y_front + 18, H - 2), 2.0, "post_mat", sides=6)
    bevel_box(xa, xb, y_front, FRONT, 0, 12, "concrete_mat", r=2.0)               # walkway slab
    for k in range(1, int((xb - xa) / 250)):                                     # expansion joints
        x = xa + k * 250
        box(x - 0.8, x + 0.8, y_front + 3, FRONT - 1, 12.0, 12.6, "crack_mat")


# ---------- the office (outside) and the ICE machine ----------

def office_trim():
    """Extra detail on the office front (office() still builds the shell): brick cap, door and
    window casings with sills and mullions, a gutter along the roof."""
    x0, x1, y0, y1, h = OFFICE
    d0, d1 = x0 + 50, x0 + 160
    for a, b in ((x0, d0 - 10), (d1 + 10, x1)):
        bevel_box(a - 1, b + 1, y0 - 6, y0, 100, 106, "concrete_mat", r=1.2)
    bevel_box(d0 - 14, d1 + 14, y0 - 8, y0, 238, 244, "trim_mat", r=1.0)
    wx0, wx1 = x0 + 430, x1 - 30
    for k in range(1, 3):
        mx = wx0 + (wx1 - wx0) * k / 3.0
        bevel_box(mx - 2.5, mx + 2.5, y0 - 7.5, y0 - 1, 103, 242, "trim_mat", r=0.6)
    rbevel((wx0 + wx1) / 2.0, y0 - 9, 96.5, wx1 - wx0 + 30, 16, 4, "concrete_mat", r=1.0, tilt_y=-6)
    tube((x0 - 30, y0 - 166, h + 4), (x1 + 30, y0 - 166, h + 4), 6.5, "metal_mat", sides=12)
    tube((x0 - 18, y0 - 166, h + 4), (x0 - 18, y0 - 166, 18), 4.5, "metal_mat", sides=10)


def ice_machine(x, y):
    """A vending ICE chest: bevelled cabinet on legs, a lit sign panel with dark letters, a
    stainless door with a long handle and hinges, a vent grille, a coin plate, rust at the foot."""
    bevel_box(x - 50, x + 50, y - 40, y + 40, 8, 172, "ice_mat", r=3.0)
    for dx in (-44, 44):
        for dy in (-34, 34):
            frustum(x + dx, y + dy, 0, 8.5, 2.5, 2.2, "metal_mat", sides=8)
    bevel_box(x - 41, x + 41, y - 42, y - 40.5, 118, 162, "glow_ice_mat", r=1.0)
    neon_word("ICE", x + 33, y - 46, 128, 24, "glass_mat", r=1.5)
    bevel_box(x - 43, x + 43, y - 43, y - 40.2, 20, 112, "metal_mat", r=1.5)               # door
    tube((x - 36, y - 46, 30), (x - 36, y - 46, 102), 1.6, "brass_mat", sides=8)            # handle
    for zz in (30, 102):
        tube((x - 36, y - 43, zz), (x - 36, y - 46, zz), 1.3, "brass_mat", sides=6)
    for zz in (30, 100):
        bevel_box(x + 40, x + 46, y - 44, y - 41, zz, zz + 8, "metal_mat", r=0.5)            # hinges
    for k in range(8):
        box(x - 30, x + 30, y - 43.6, y - 42.6, 11 + k * 1.1, 11.5 + k * 1.1, "trim_mat")   # vent
    bevel_box(x + 20, x + 34, y - 44, y - 42.6, 70, 92, "brass_mat", r=0.6)                # coin plate
    blot(x, y - 45, 30, "stain_mat", z=12)


# ---------- the lamp posts (one cool light colour) ----------

def lamp_post(x, y, arm_dx, arm_dy, height, working, name):
    """A tall steel pole on a concrete footing with an anchor flange and bolts, a tapered pole, a
    curved arm and a cobra-head luminaire with a lens that glows in the cool colour."""
    frustum(x, y, 0, 55, 28, 25, "concrete_mat", sides=16)                           # footing
    frustum(x, y, 55, 58, 18, 18, "metal_mat", sides=16)                             # flange
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        frustum(x + math.cos(a) * 14, y + math.sin(a) * 14, 57.5, 61, 1.6, 1.3, "metal_mat", sides=6)
    frustum(x, y, 58, height, 10, 6, "metal_mat", sides=16)                          # pole
    ring(x, y, 62, 10.3, 1.0, "metal_mat", sides=16)
    # arm: up and out in a curve
    L = math.hypot(arm_dx, arm_dy)
    ux, uy = arm_dx / L, arm_dy / L
    prev = (x, y, height - 30)
    for k in range(1, 9):
        t = k / 8.0
        p = (x + ux * L * t, y + uy * L * t, height - 30 + 40 * math.sin(t * math.pi / 2))
        tube(prev, p, 4.2 - 1.2 * t, "metal_mat", sides=10)
        prev = p
    hx, hy, hz = prev
    yaw = math.degrees(math.atan2(-ux, uy))
    rsoft(hx + ux * 20, hy + uy * 20, hz - 2, 34, 62, 16, "metal_mat", smooth=2, sag=-2, yaw=yaw)      # head
    rsoft(hx + ux * 24, hy + uy * 24, hz - 10.5, 26, 44, 3.5, "glow_street_mat" if working else "glass_mat",
          smooth=2, yaw=yaw)                                                                          # lens
    if working:
        light(name, hx + ux * 24, hy + uy * 24, hz - 40, COOL, 3800, 1750)


def streetlight(x, y):
    """The streetlight over the lot entrance (the one with the cool light everybody likes)."""
    lamp_post(x, y, 140, 0, 650, True, "light_street")


def lot_lamp(x, y, working):
    lamp_post(x, y, -170, 30, 720, working, "light_lot")


# ---------- payphone, dumpster ----------

def payphone(x, y):
    """A payphone on a post: housing with a coin slot, a 3x4 keypad, a card holder, the handset on
    its hook with an armoured cord, a hood with a cold lit strip, a shelf, a sticker or two."""
    frustum(x, y, 0, 2.5, 16, 15, "metal_mat", sides=12)
    frustum(x, y, 2.5, 104, 5.5, 4.5, "metal_mat", sides=10)
    bevel_box(x - 30, x + 30, y - 20, y + 20, 100, 186, "payphone_mat", r=2.0)
    bevel_box(x - 36, x + 36, y - 30, y + 24, 186, 193, "payphone_mat", r=1.5)             # hood
    bevel_box(x - 33, x + 33, y - 30.5, y - 25, 193.5, 199, "glow_phone_mat", r=0.8)       # lit strip
    bevel_box(x - 17, x + 17, y - 22, y - 20, 132, 172, "metal_mat", r=1.0)                # faceplate
    for r_ in range(4):
        for c_ in range(3):
            bevel_box(x - 11 + c_ * 8, x - 5 + c_ * 8, y - 23.6, y - 21.6, 138 + r_ * 8, 144 + r_ * 8,
                      "chair_mat", r=0.6)                                                  # keys
    box(x + 6, x + 13, y - 23, y - 21.8, 175, 176, "trim_mat")                             # coin slot
    bevel_box(x - 12, x + 12, y - 23, y - 21.5, 108, 120, "metal_mat", r=0.8)              # return chute
    rsoft(x - 25, y - 26, 148, 7, 6, 42, "trim_mat", smooth=2)                             # handset
    for zz in (128, 168):
        rsoft(x - 25, y - 28, zz, 9, 8, 9, "trim_mat", smooth=2)
    prev = (x - 25, y - 26, 128)
    for k in range(1, 9):                                                                  # armoured cord
        p = (x - 25 + k * 1.2, y - 26 - 2 * math.sin(k / 8.0 * math.pi), 128 - k * 2.6)
        tube(prev, p, 0.9, "metal_mat", sides=6)
        prev = p
    bevel_box(x - 30, x + 30, y - 32, y - 20, 96, 100, "payphone_mat", r=1.0)              # shelf


def dumpster(x, y):
    """A steel dumpster: tapered body with ribs, side lifting pockets, two plastic lids (one
    propped open on a bag), castors, rust streaks, rubbish bags around it."""
    c = cmds.polyCube(w=200, h=110, d=150, sx=1, sy=1, sz=1, ch=False)[0]
    _set_verts(c, [(vx * (1.0 if vy > 0 else 0.92), vy, vz * (1.0 if vy > 0 else 0.9)) for vx, vy, vz in _verts(c)])
    _bevel(c, 3.5, 6)                                                       # well rounded edges
    cmds.move(x, 70, y, c)
    keep(c, "dumpster_mat")
    for dx in (-60, 0, 60):                                                 # ribs, front and back
        for y0_, y1_ in ((y - 77, y - 72), (y + 72, y + 77)):
            bevel_box(x + dx - 5, x + dx + 5, y0_, y1_, 25, 120, "dumpster_mat", r=1.8, seg=4)
    for s in (-1, 1):
        bevel_box(x + s * 101, x + s * 109, y - 50, y + 50, 70, 86, "metal_mat", r=1.8, seg=4)  # lifting pockets
        bevel_box(x + s * 100.5, x + s * 110, y - 55, y + 55, 86.5, 88.5, "metal_mat", r=0.8, seg=3)
    rbevel(x - 50, y, 127.5, 102, 156, 4, "lid_mat", r=1.8, seg=5)                          # lid (shut)
    rbevel(x + 50, y + 18, 150, 102, 156, 4, "lid_mat", r=1.8, seg=5, tilt_y=28)            # lid (propped up)
    for lx in (-50, 50):                                                                   # hinge rods at the back
        tube((x + lx - 45, y + 78, 128), (x + lx + 45, y + 78, 128), 1.4, "metal_mat", sides=16)
    rsoft(x + 60, y - 30, 132, 50, 40, 34, "bag_mat", jitter=1.2, smooth=3, seed=3, div=(5, 4, 5))
    for dx in (-80, 80):
        for dy in (-55, 55):
            frustum(x + dx, y + dy, 9, 15.5, 4, 4, "metal_mat", sides=20)
            lathe(x + dx, y + dy, [(0.4, 0.5), (0.8, 3.5), (1.6, 5.2), (3.0, 6.0), (6.5, 6.0), (8.0, 5.2), (9.0, 3.5),
                                   (9.6, 0.5)], "tire_mat", sides=24)
    for bx, by, r in ((x - 150, y - 60, 28), (x - 175, y + 10, 22), (x + 140, y - 90, 25), (x - 135, y + 55, 18)):
        rsoft(bx, by, r * 0.75 + 0.5, r * 2.1, r * 1.9, r * 1.5, "bag_mat", jitter=r * 0.05, sag=-r * 0.1,
              smooth=3, seed=int(bx), div=(5, 4, 5))
        frustum(bx, by, r * 1.45, r * 1.75, 2.5, 1.0, "bag_mat", sides=16)                 # knot


# ---------- the parking lot ----------

def parking_lot_detail():
    """On top of parking_lot()'s lines: the painted asphalt (ground_textures), proper wheel stops (bevelled, two rebar pins,
    chipped), a bevelled curb, a storm drain grate, a manhole cover, weeds in the cracks."""
    ground_textures()
    for k in range(12):
        cx = X0 + k * 250 + 125
        bevel_box(cx - 85, cx + 85, FRONT - WALK - 162, FRONT - WALK - 138, LOT_Z + 3.4, LOT_Z + 15, "stop_mat", r=3.0)
        for s in (-55, 55):
            frustum(cx + s, FRONT - WALK - 150, LOT_Z + 15, LOT_Z + 16.2, 1.6, 1.6, "metal_mat", sides=8)
    # (the curbs are in maya/grounds.py now: open at the driveways)
    # storm drain by the curb and a manhole in the lot
    gx, gy = 600, LOT[2] + 40
    bevel_box(gx - 45, gx + 45, gy - 25, gy + 25, LOT_Z + 3.4, LOT_Z + 4.6, "metal_mat", r=0.8)
    for k in range(9):
        box(gx - 38 + k * 9.5, gx - 34 + k * 9.5, gy - 20, gy + 20, LOT_Z + 4.6, LOT_Z + 5.0, "crack_mat")
    mx, my = -1800, -3000
    lathe(mx, my, [(LOT_Z + 3.4, 0.1), (LOT_Z + 4.4, 34), (LOT_Z + 4.4, 34.5)], "metal_mat", sides=24)
    for r_ in (10, 20, 30):
        ring(mx, my, LOT_Z + 4.6, r_, 0.6, "trim_mat", sides=24)
    # weeds pushing up through the cracks and along the curb
    for _ in range(70):
        wx, wy = rng.uniform(LOT[0] + 100, LOT[1] - 100), rng.choice((LOT[2] + rng.uniform(5, 30), rng.uniform(LOT[2], LOT[3])))
        for b in range(rng.randint(3, 6)):
            a = rng.uniform(0, 6.28)
            h = rng.uniform(6, 18)
            tube((wx, wy, LOT_Z + 3.4), (wx + math.cos(a) * h * 0.4, wy + math.sin(a) * h * 0.4, LOT_Z + 3.4 + h), 0.35,
                 "weed_mat", sides=3)


# ---------- the car ----------

def _shaped(cx, cy, L, W, prof, mat, sx=12, sy=6, sz=40, smooth=2):
    """A car-body shape: a subdivided block whose cross-section along its length follows
    prof(u) -> (bottom z, top z, half width at the bottom, half width at the top), u = 0 rear .. 1 front."""
    c = cmds.polyCube(w=1, h=1, d=1, sx=sx, sy=sy, sz=sz, ch=False)[0]
    pts = []
    for x, y, z in _verts(c):
        u = z + 0.5
        bz, tz, hwb, hwt = prof(u)
        hgt = y + 0.5
        hw = hwb + (hwt - hwb) * hgt
        pts.append((x * 2 * hw, bz + (tz - bz) * hgt, cy + (u - 0.5) * L))
    _set_verts(c, pts)
    cmds.move(cx, 0, 0, c, relative=True)
    if smooth:
        cmds.polySmooth(c, dv=smooth, ch=False)
    return keep(c, mat)


def car(cx, cy):
    """Your car: a tired early-90s sedan, dark red, nose toward the motel (+y). A shaped body
    (sloped nose and trunk), a greenhouse of glass with pillars and a roof panel, wheel arches,
    tyres with hubcaps, chrome bumpers, a grille, headlights and red tail lights, mirrors, door
    seams and handles, wipers, plates, an aerial, a dent."""
    L, W = 470.0, 178.0
    front, back = cy + L / 2, cy - L / 2

    def body(u):
        top = 80 + 12 * min(1.0, u / 0.08) - 6 * max(0.0, (u - 0.9) / 0.1)       # trunk lid .. hood .. nose drop
        if u > 0.62:
            top -= 4 * (u - 0.62) / 0.28                                         # hood slopes down
        bot = 30 + 6 * max(0.0, (0.05 - u) / 0.05) + 6 * max(0.0, (u - 0.95) / 0.05)
        for uw in (92.0 / L, 1 - 105.0 / L):                                       # wheel arches
            d = abs(u - uw) * L
            if d < 40:
                bot = max(bot, 34 + math.sqrt(40 * 40 - d * d))
        end = min(u, 1 - u)
        k = math.sqrt(max(0.15, min(1.0, end / 0.04)))
        return bot, top, W / 2 * k * 0.98, (W / 2 - 6) * k
    _shaped(cx, cy, L, W, body, "gloss_car_paint_mat", sz=48)
    # greenhouse: glass block narrowing to the roof, pillars, a roof panel
    gl0, gl1 = 0.26, 0.64                                                       # rear window .. windscreen
    def cabin(u):
        uu = gl0 + (gl1 - gl0) * u
        rake = min(1.0, u / 0.22) * min(1.0, (1 - u) / 0.28)                    # slope front and back
        return 91.5, 91.5 + 45 * rake ** 0.6 + 0.5, W / 2 - 9, W / 2 - 22
    _shaped(cx, back + L * gl0 + L * (gl1 - gl0) / 2, L * (gl1 - gl0), W, cabin, "seeglass_car_mat", sz=24)
    roof_y0, roof_y1 = back + L * (gl0 + 0.07), back + L * (gl1 - 0.09)
    rbevel(cx, (roof_y0 + roof_y1) / 2, 137.5, W - 42, roof_y1 - roof_y0, 3.0, "gloss_car_paint_mat", r=1.4, seg=4)
    for s in (-1, 1):
        xx = cx + s * (W / 2 - 16)
        tube((xx, back + L * gl0 + 6, 93), (cx + s * (W / 2 - 22), roof_y0, 137), 3.0, "gloss_car_paint_mat", sides=16)   # C pillar
        tube((cx + s * (W / 2 - 13), back + L * 0.46, 93), (cx + s * (W / 2 - 21), back + L * 0.46, 137), 2.4, "trim_mat", sides=12)  # B
        tube((xx, back + L * gl1 - 6, 93), (cx + s * (W / 2 - 22), roof_y1, 137), 2.6, "gloss_car_paint_mat", sides=16)   # A pillar
        # wheels: rounded tyres (sidewall + tread), dished hubcaps, lug nuts
        for wy in (back + 92, front - 105):
            prof = [(0, 0.5), (0.6, 22), (1.6, 27), (3.0, 31), (5.0, 33), (9, 34), (14, 34.3), (19, 34), (23, 33),
                    (25, 31), (26.4, 27), (27.4, 22), (28, 0.5)]
            t = lathe(0, 0, prof, "tire_mat", sides=48)                       # tyre, built standing up then turned
            cmds.rotate(0, 0, 90, t, pivot=(0, 0, 0))                          # axis along -x, 28 wide
            cmds.move((cx + W / 2 - 1) if s > 0 else (cx - W / 2 + 29), 34, wy, t, relative=True)
            hub = lathe(0, 0, [(0, 0.3), (0.5, 19), (1.2, 19.5), (2.2, 18.5), (2.8, 15), (3.2, 10), (3.9, 6), (4.4, 3),
                               (4.7, 1.5), (4.8, 0.3)], "gloss_chrome_mat", sides=40)
            cmds.rotate(0, 0, -90 * s, hub, pivot=(0, 0, 0))
            cmds.move(cx + s * (W / 2 + 0.8), 34, wy, hub, relative=True)
            for k in range(5):                                                 # lug nuts
                a = k * 2 * math.pi / 5
                sphere(cx + s * (W / 2 + 3.6), wy + math.cos(a) * 7, 34 + math.sin(a) * 7, 0.9, "gloss_chrome_mat", sides=8)
        # door seams, handles, mirror, side trim
        for sy_ in (back + L * 0.30, back + L * 0.47, back + L * 0.64):
            box(cx + s * (W / 2 - 0.2) - 0.6, cx + s * (W / 2 - 0.2) + 0.6, sy_ - 0.5, sy_ + 0.5, 42, 90, "tire_mat")
        for hy in (back + L * 0.40, back + L * 0.58):
            rbevel(cx + s * (W / 2 + 0.6), hy, 80, 2, 14, 3, "gloss_chrome_mat", r=0.5)
        rsoft(cx + s * (W / 2 + 7), back + L * gl1 - 14, 98, 12, 6, 9, "gloss_car_paint_mat", smooth=3)
        box(cx + s * (W / 2 - 1) - 1, cx + s * (W / 2 - 1) + 1.6, back + 60, front - 60, 56, 60, "gloss_chrome_mat")
    for wy in (back + 92, front - 105):                                            # wheel wells (dark)
        tube((cx - W / 2 + 4, wy, 34), (cx + W / 2 - 4, wy, 34), 39, "tire_mat", sides=24)
    bevel_box(cx - W / 2 + 12, cx + W / 2 - 12, back + 30, front - 30, 24, 31, "tire_mat", r=2.0)   # underside
    car_interior(cx, back, L, W, gl0, gl1)
    # front: bumper, grille, headlights, plate; back: bumper, tail lights, plate, exhaust
    rbevel(cx, front - 4, 42, W + 4, 14, 14, "gloss_chrome_mat", r=4.0, seg=5)
    bevel_box(cx - 48, cx + 48, front - 9, front - 6.5, 58, 78, "trim_mat", r=1.0)
    for k in range(6):
        box(cx - 44, cx + 44, front - 6.9, front - 6.0, 60 + k * 3, 61.3 + k * 3, "gloss_chrome_mat")
    for s in (-1, 1):
        bevel_box(cx + s * 56 - 20, cx + s * 56 + 20, front - 10, front - 6, 60, 76, "gloss_chrome_mat", r=1.0)
        bevel_box(cx + s * 56 - 17, cx + s * 56 + 17, front - 6.6, front - 5.6, 62, 74, "glass_mat", r=0.6)
        bevel_box(cx + s * 60 - 22, cx + s * 60 + 22, back + 5.6, back + 8, 62, 78, "glow_tail_mat", r=1.0)
    rbevel(cx, back + 4, 44, W + 4, 14, 14, "gloss_chrome_mat", r=4.0, seg=5)
    for py, facing in ((front - 12.0, 1), (back + 12.0, -1)):
        plate(cx, py - facing * 0.8, 45, facing)
    tube((cx + 50, back + 12, 28), (cx + 50, back - 2, 28), 2.8, "metal_mat", sides=10)
    # wipers, aerial, a dent in the door
    for s in (-1, 1):
        tube((cx + s * 30, back + L * gl1 + 4, 92.5), (cx + s * 30 - 40, back + L * gl1 - 2, 98), 0.7, "trim_mat", sides=4)
    tube((cx + 60, front - 120, 92), (cx + 62, front - 125, 150), 0.35, "gloss_chrome_mat", sides=4)
    light("light_car_tail", cx, back - 60, 60, [1.0, 0.03, 0.0], 160, 380)


def car_interior(cx, back, L, W, gl0, gl1):
    """What you see through the tinted windows: front bucket seats and a bench, headrests, a
    dashboard with a hood over the gauges, a steering wheel, the rear parcel shelf."""
    fy = back + L * 0.50                                                  # front seats
    for s_ in (-1, 1):
        rsoft(cx + s_ * 38, fy, 104, 48, 12, 30, "seat_mat", smooth=2, sag=-1, tilt_y=-12)      # back
        rsoft(cx + s_ * 38, fy - 4, 125, 24, 10, 13, "seat_mat", smooth=2)                       # headrest
    by = back + L * 0.32                                                  # rear bench
    rsoft(cx, by, 104, W - 44, 12, 28, "seat_mat", smooth=2, sag=-1, tilt_y=-14)
    rsoft(cx, back + L * gl0 + 6, 95, W - 40, 22, 3, "dash_mat", smooth=1)                     # parcel shelf
    dy = back + L * gl1 - 14                                              # dashboard
    rsoft(cx, dy, 95, W - 34, 30, 10, "dash_mat", smooth=2, sag=-2)
    rsoft(cx + 38, dy - 8, 101, 36, 12, 7, "dash_mat", smooth=2)                               # gauge hood
    ring(cx + 38, dy - 22, 104, 17, 1.4, "dash_mat", axis="y", sides=24)                      # steering wheel
    tube((cx + 38, dy - 22, 104), (cx + 38, dy - 4, 97), 2.0, "dash_mat", sides=10)


def plate(cx, y, z, facing):
    """The number plate, a picture on a thin backing, facing +y (front) or -y (back)."""
    bevel_box(cx - 16, cx + 16, y - 0.5, y + 0.5, z - 8, z + 8, "gloss_chrome_mat", r=0.4)
    p = cmds.polyPlane(w=30, h=15, sx=1, sy=1, ch=False)[0]
    cmds.rotate(90 * facing, 0, 0, p)
    if facing < 0:
        cmds.rotate(0, 180, 0, p, relative=True)
    cmds.move(cx, z, y + facing * 0.9, p)
    keep(p, "pic_car_plate")


def ground_textures():
    """The lot and the road as one large painted surface each (tools/make_asphalt.py), 8 mm above
    the grey blockout so they never fight it, below the paint lines and the wheel stops."""
    flat_picture((LOT[0] + LOT[1]) / 2.0, (LOT[2] + LOT[3]) / 2.0, LOT_Z + 0.8, LOT[1] - LOT[0], LOT[3] - LOT[2], "pic_lot_asphalt")
    flat_picture(0, -4500, 2.8, 16000, 900, "pic_road_asphalt")


# ---------- the swinging doors (their own meshes) ----------

def door_mesh(width, height, name, knob_side=1):
    """A panelled door built at its hinge (x 0 .. width, y -2.5 .. 2.5, z 0 .. height), the
    outside facing +y: six raised panels each side, a knob with a backplate both sides, a peephole,
    a kick plate, three hinges. Returns the mesh, kept out of the motel mesh."""
    keep_parts = PARTS[:]
    del PARTS[:]
    bevel_box(0, width, -2.5, 2.5, 0, height, "door_mat", r=0.8)
    cols, rows = 2, 3
    m = 12.0
    pw = (width - m * (cols + 1)) / cols
    ph = (height - 30 - m * (rows + 1)) / rows
    for side in (1, -1):
        for c_ in range(cols):
            for r_ in range(rows):
                ax = m + c_ * (pw + m)
                az = 30 + m + r_ * (ph + m)
                y0 = 2.5 if side > 0 else -3.5
                bevel_box(ax, ax + pw, y0, y0 + 1.0, az, az + ph, "door_mat", r=0.8)
        kx = width - 10 if knob_side > 0 else 10
        ys = 2.5 if side > 0 else -2.5
        bevel_box(kx - 3, kx + 3, ys, ys + side * 0.8, 88, 106, "brass_mat", r=0.5)
        tube((kx, ys, 97), (kx, ys + side * 5, 97), 1.0, "brass_mat", sides=8)
        sphere(kx, ys + side * 6.5, 97, 2.8, "brass_mat", sides=12)
    tube((width / 2.0, 2.5, 160), (width / 2.0, 3.6, 160), 1.3, "brass_mat", sides=10)   # peephole
    for hz in (25, height / 2.0, height - 25):
        bevel_box(-1.5, 2.0, -2.0, 2.0, hz - 6, hz + 6, "metal_mat", r=0.4)
    mesh = cmds.polyUnite(PARTS, name=name, ch=False)[0] if len(PARTS) > 1 else PARTS[0]
    cmds.delete(mesh, constructionHistory=True)
    cmds.xform(mesh, pivots=(0, 0, 0), worldSpace=True)
    del PARTS[:]
    PARTS.extend(keep_parts)
    return mesh


def export_doors():
    """export/prop_room_door.fbx and prop_office_door.fbx, listed in sets.json "props"."""
    made = {}
    for name, w in (("prop_room_door", 138), ("prop_office_door", 108)):
        m = door_mesh(w, 231, name)                  # tucks up into the frame (no light strip under it)
        fbx = os.path.join(OUT, name + ".fbx").replace("\\", "/")
        cmds.select(m)
        mel.eval("FBXResetExport")
        mel.eval('FBXExport -f "{}" -s'.format(fbx))
        made[name] = fbx
        cmds.delete(m)
    p = os.path.join(OUT, "sets.json")
    data = json.load(open(p))
    data["props"] = made
    for mt in ("door_mat", "brass_mat", "metal_mat"):
        data["materials"].setdefault(mt, list(MATS[mt]))
    json.dump(data, open(p, "w"), indent=1)
    print("doors exported", list(made))

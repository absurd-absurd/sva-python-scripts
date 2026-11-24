"""MARROW Chapter 2: the story props and creatures, first pass (2026-11-24).

exec'd by make_lakebed.py (uses its helpers: rsoft, rbevel, frustum, sphere, tube, light, keep,
bed_z, path_x, floor_z, make_prop ...). Positions are Unreal cm.

Set pieces (combined into set_lakebed):
  handbag()        Eileen's brown leather shoulder bag, half sunk in the silt (clue: bag)
  research_case()  the 1974 researchers' aluminium instrument case, lid open, a fallen tripod,
                   sample jars (clue: log_1974 lies in the case)
  watch()          Freedman's wristwatch on a flat rock (clue: watch)
  coat()           Eileen's long wool coat spread on the basin floor (clue: last_page lies on it)
Props (own meshes, placed by unreal/lakebed_level.py with their own materials):
  lb_figure        the red-lit figure in a long wool coat (Eileen's silhouette): the lure
  lb_hunter        the red-lure hunter: a long eel-like body, jaws, a stalk with a red bulb
  lb_breather      the huge thing asleep in the basin, mostly buried, ribbed, with a lure stalk
"""

CH2_MATS = {
    "bag_leather_mat": (0.16, 0.08, 0.04), "bag_strap_mat": (0.12, 0.06, 0.03), "brass_dull_mat": (0.3, 0.24, 0.1),
    "case_alu_mat": (0.32, 0.33, 0.32), "case_foam_mat": (0.04, 0.04, 0.04), "case_rust_mat": (0.22, 0.12, 0.06),
    "seeglass_jar_mat": (0.3, 0.38, 0.32), "watch_steel_mat": (0.35, 0.35, 0.33), "watch_face_mat": (0.6, 0.58, 0.5),
    "watch_strap_mat": (0.1, 0.07, 0.05), "coat_wool_mat": (0.2, 0.14, 0.09), "coat_lining_mat": (0.12, 0.05, 0.05),
    "figure_mat": (0.01, 0.01, 0.01), "hunter_skin_mat": (0.05, 0.06, 0.05), "hunter_belly_mat": (0.16, 0.15, 0.12),
    "hunter_teeth_mat": (0.5, 0.48, 0.4), "hunter_eye_mat": (0.02, 0.02, 0.02), "hunter_lure_mat": (1.0, 0.06, 0.02),
    "breather_lure_mat": (1.0, 0.06, 0.02),
    "breather_skin_mat": (0.06, 0.07, 0.06), "breather_rib_mat": (0.03, 0.035, 0.03),
}

CLUE_SPOTS = {}      # clue id -> (x, y, z, yaw): where unreal/place_clues2.py puts the page/object


def _lantern_side(i, dx, dy):
    """A spot next to sunken lantern i (from sunken_lanterns(): LANTERNS)."""
    x, y = LANTERNS[i]
    return x + dx, y + dy


# ---------- set pieces ----------

def handbag(x, y, yaw):
    z = bed_z(x, y) - 4
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    at = lambda u, v: (x + u * c - v * s, y + u * s + v * c)
    rsoft(x, y, z + 9, 32, 13, 22, "bag_leather_mat", sag=2.0, jitter=0.6, smooth=2, seed=31, yaw=yaw, tilt_y=12)   # the bag, tipped
    px, py = at(0, 6.8)
    rsoft(px, py, z + 14, 30, 2.2, 15, "bag_leather_mat", jitter=0.4, smooth=1, seed=32, yaw=yaw, tilt_y=12)          # the flap
    bx, by = at(0, 8.2)
    rbevel(bx, by, z + 9, 4, 0.8, 3, "brass_dull_mat", r=0.3, yaw=yaw)                                                   # clasp
    pts = [at(-14, 0), at(-30, 18), at(-12, 40), at(14, 36), at(26, 12)]                                                 # the strap, lying in a loop
    for (ax, ay), (bx2, by2) in zip(pts, pts[1:]):
        tube((ax, ay, bed_z(ax, ay) + 0.8), (bx2, by2, bed_z(bx2, by2) + 0.8), 1.0, "bag_strap_mat", sides=6)
    ex, ey = at(26, 12)
    tube((ex, ey, bed_z(ex, ey) + 0.8), (ex + 6, ey - 3, bed_z(ex, ey) + 0.6), 0.9, "bag_strap_mat", sides=6)        # torn end
    return z


def research_case(x, y, yaw):
    """A 1970s aluminium field case, lid flopped open, foam inside, rust at the corners."""
    z = bed_z(x, y) - 3
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    at = lambda u, v: (x + u * c - v * s, y + u * s + v * c)
    rbevel(x, y, z + 9, 52, 36, 18, "case_alu_mat", r=1.5, yaw=yaw)                       # the box
    rbevel(x, y, z + 17.6, 48, 32, 1.2, "case_foam_mat", r=0.4, yaw=yaw)                  # foam inside
    lx, ly = at(0, -24)
    rbevel(lx, ly, z + 20, 52, 4, 30, "case_alu_mat", r=1.2, yaw=yaw, tilt_x=-18)         # lid, open and leaning back
    for u in (-24, 24):
        for v in (-16, 16):
            cx_, cy_ = at(u, v)
            sphere(cx_, cy_, z + 2, 2.4, "case_rust_mat", sides=6, scale=(1, 1, 0.7))     # rusted corner caps
    hx, hy = at(0, 18.5)
    tube((hx - 7 * c, hy - 7 * s, z + 12), (hx + 7 * c, hy + 7 * s, z + 12), 0.9, "case_rust_mat", sides=6)   # handle
    # a fallen survey tripod beside it
    tx, ty = at(80, 10)
    for k in range(3):
        a = math.radians(yaw + 20 + k * 9)
        tube((tx, ty, bed_z(tx, ty) + 3), (tx + math.cos(a) * 150, ty + math.sin(a) * 150, bed_z(tx, ty) + 2 + k * 3),
             1.6, "case_rust_mat", sides=6)
    # sample jars, two upright, one on its side
    for k, (u, v, lying) in enumerate(((-45, 20, False), (-52, 6, False), (-40, -14, True))):
        jx, jy = at(u, v)
        jz = bed_z(jx, jy) - 1
        if lying:
            tube((jx - 6, jy, jz + 4), (jx + 6, jy, jz + 4), 4, "seeglass_jar_mat", sides=10)
        else:
            frustum(jx, jy, jz, jz + 13, 4, 4, "seeglass_jar_mat", sides=10)
            frustum(jx, jy, jz + 13, jz + 15, 3.2, 3.2, "case_rust_mat", sides=10)
    return z + 18.3                                                                       # the log lies on the foam


def watch(x, y):
    z = bed_z(x, y)
    rbevel(x, y, z + 6, 40, 30, 14, "rock_mat", r=4)                                     # a flat rock
    top = z + 13
    frustum(x, y, top, top + 0.9, 2.0, 1.9, "watch_steel_mat", sides=16)                  # case
    frustum(x, y, top + 0.9, top + 1.0, 1.7, 1.7, "watch_face_mat", sides=16)             # face
    for sgn in (-1, 1):
        rbevel(x + sgn * 4.6, y, top + 0.3, 7, 1.8, 0.5, "watch_strap_mat", r=0.2)        # strap halves
    return top + 1.0


def coat(x, y, yaw):
    """Her long wool coat lying spread out, arms out, the lining showing at the collar."""
    z = bed_z(x, y)
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    at = lambda u, v: (x + u * c - v * s, y + u * s + v * c)
    rsoft(x, y, z + 2.5, 58, 112, 6, "coat_wool_mat", jitter=1.2, sag=1.5, smooth=2, seed=41, yaw=yaw)              # body
    for sgn in (-1, 1):
        a0 = at(sgn * 26, 38)
        a1 = at(sgn * 70, 10)
        tube((a0[0], a0[1], z + 3), (a1[0], a1[1], bed_z(*a1) + 2.5), 6, "coat_wool_mat", sides=8)                   # sleeves
    cx_, cy_ = at(0, 52)
    rsoft(cx_, cy_, z + 5, 34, 12, 5, "coat_lining_mat", jitter=0.6, smooth=1, seed=42, yaw=yaw)                    # collar
    for k in range(3):
        bx, by = at(4, 20 - k * 22)
        sphere(bx, by, z + 6, 1.4, "brass_dull_mat", sides=6, scale=(1, 1, 0.5))                                     # buttons
    return z + 6.2


def story_set():
    """Build the clue set pieces and note where each clue's page/object goes."""
    bx, by = _lantern_side(1, -120, 70)
    CLUE_SPOTS["bag"] = (bx, by, handbag(bx, by, 30) + 20, 30)
    cx_, cy_ = _lantern_side(3, -160, 40)
    CLUE_SPOTS["log_1974"] = (cx_, cy_, research_case(cx_, cy_, -20), -20)
    wx, wy = _lantern_side(6, 140, 30)
    CLUE_SPOTS["watch"] = (wx, wy, watch(wx, wy), 0)
    ky = 16300
    kx = path_x(ky)
    CLUE_SPOTS["last_page"] = (kx, ky, coat(kx, ky, 10), 10)


# ---------- the figure (a prop) ----------

def figure_parts():
    """Eileen's silhouette (STORY.md): shoulder-length 90s hair, long wool coat with the collar up,
    a handbag strap over one shoulder. ~168 cm, feet at the origin, facing -y (toward you)."""
    lathe(0, 0, [(10, 16), (40, 21), (80, 20), (110, 17), (130, 16), (138, 13)], "figure_mat", sides=14)   # coat to the knees, shoulders
    for sgn in (-1, 1):
        tube((sgn * 7, 0, 0), (sgn * 7, 0, 14), 4.2, "figure_mat", sides=6)          # legs below the coat
        tube((sgn * 17, 0, 134), (sgn * 21, -3, 86), 5.0, "figure_mat", sides=6)     # arms hanging
    frustum(0, 0, 135, 146, 9, 6, "figure_mat", sides=10)                             # collar up
    sphere(0, 0, 156, 10.5, "figure_mat", sides=10, scale=(0.9, 1.0, 1.15))           # head
    rsoft(0, 2, 150, 24, 20, 26, "figure_mat", jitter=1.5, smooth=1, seed=7)           # shoulder-length hair
    tube((-14, -2, 136), (12, -9, 100), 1.0, "figure_mat", sides=4)                   # handbag strap across


# ---------- the hunter (a prop) ----------

def hunter_parts():
    """The red-lure hunter: ~4.5 m eel-like body tapering to a fin, a broad head with an open jaw
    full of needle teeth, a stalk over its head ending in a red glowing bulb (the light that
    lures). Nose toward +x, centred near the origin."""
    segs = 14
    for i in range(segs):
        t0, t1 = i / segs, (i + 1) / segs
        x0, x1 = 120 - t0 * 450, 120 - t1 * 450
        r0, r1 = 26 * (1 - t0 * 0.85), 26 * (1 - t1 * 0.85)
        z0, z1 = 8 * math.sin(t0 * 6), 8 * math.sin(t1 * 6)
        tube((x0, 0, z0), (x1, 0, z1), r0, "hunter_skin_mat", sides=10)
        sphere(x1, 0, z1, r1 * 1.02, "hunter_skin_mat", sides=8)
        tube((x0, 0, z0 - r0 * 0.55), (x1, 0, z1 - r1 * 0.55), r0 * 0.5, "hunter_belly_mat", sides=8)
    rsoft(-330, 0, 0, 40, 4, 60, "hunter_skin_mat", jitter=3, smooth=1, seed=3)              # tail fin
    sphere(150, 0, 6, 1, "hunter_skin_mat", sides=12, scale=(55, 30, 22))                    # head
    rsoft(178, 0, -16, 70, 46, 10, "hunter_skin_mat", jitter=1, smooth=1, seed=4, tilt_y=-18)  # lower jaw, dropped open
    for k in range(18):                                                                       # needle teeth round the mouth
        a = math.radians(-80 + k * 160 / 17)
        tx, ty = 175 + math.cos(a) * 30, math.sin(a) * 26
        tube((tx, ty, -6), (tx + 2, ty, -6 - 9 - (k % 3) * 3), 0.9, "hunter_teeth_mat", sides=4)
        tube((tx, ty, -12), (tx + 2, ty, -12 + 8 + (k % 2) * 3), 0.8, "hunter_teeth_mat", sides=4)
    for sgn in (-1, 1):
        sphere(170, sgn * 22, 18, 3.5, "hunter_eye_mat", sides=8)                              # small dead eyes
    pts = [(140, 0, 26), (160, 0, 70), (200, 0, 95), (240, 0, 90)]                             # the lure stalk
    for a, b in zip(pts, pts[1:]):
        tube(a, b, 2.2, "hunter_skin_mat", sides=6)
    sphere(246, 0, 86, 13, "hunter_lure_mat", sides=10)                                           # the red bulb


# ---------- the breather (a prop) ----------

def breather_parts():
    """The thing in the lake, asleep: a huge low back rising out of the silt (~30 x 18 m, 7 m high),
    ribbed like a buried ribcage, with a tall stalk ending in a red bulb, the light the lanterns copy."""
    rsoft(0, 0, 0, 3000, 1800, 1400, "breather_skin_mat", jitter=80, smooth=2, seed=9, div=(6, 4, 6))
    for k in range(9):                                                                         # ribs over its back
        x = -1100 + k * 275
        for sgn in (-1, 1):
            tube((x, 0, 640 - abs(x) * 0.12), (x + 60, sgn * 820, 80), 45 - abs(x) * 0.012, "breather_rib_mat", sides=8)
    pts = [(900, 0, 560), (1150, 150, 1300), (1250, 120, 1900), (1150, 60, 2250)]               # the stalk
    for a, b in zip(pts, pts[1:]):
        tube(a, b, 30, "breather_skin_mat", sides=8)
    sphere(1130, 50, 2300, 120, "breather_lure_mat", sides=12)                                      # its red bulb

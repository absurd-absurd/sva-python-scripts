"""The motel office inside and the small stories in rooms 101, 102, 103, 105 and 106.
exec'd by make_motel.py after room_props.py / exterior_props.py (uses their helpers; replaces
the old empty office()). Positions are Unreal cm.

OFFICE, "someone just left": the desk lamp is on, the radio is on, a cigarette still burns in the
ashtray, the coffee pot sits on the warmer, the chair is pushed back from the desk, the guest
book lies open with the pen beside it, and the TV in the back room is still playing.
- lobby: couch under the front window, coffee table + magazines, coffee station, brochure rack,
  the framed photo of red lanterns on the lake (a ritual hint), a calendar
- front counter: bell, guest book, RING FOR SERVICE card, counter flap up at the left end
- behind it: desk (lamp, radio, ashtray, mug, papers), swivel chair pushed back, the key board
  (104's hook empty), a bookcase of old guest books going back to 1974 with red lanterns on top
- back room through a doorway in the partition: the owner's cot, a small TV left on, hot plate,
  coat on a hook, boots, a wall calendar
Everything inside is on lighting channel 1 (IN_ROOM), like the rooms.

ROOMS (the room's own furniture is placed by room_inside(); a story can leave pieces out):
- 101 left in a hurry: suitcase spilled open, nightstand drawer on the floor, lamp knocked over,
  a teddy bear, the room key on the carpet
- 102 barricaded: the dresser dragged toward the door and shoved aside again, a chair tipped
  over by the door, the phone off the hook, the lamp still on
- 103 renovation that stopped: mattress stripped and leaning on the wall, dust sheets over the
  dresser and TV, a step ladder, paint cans, a roller tray, a drop cloth
- 105 water damage: a ceiling panel hanging down, debris on the carpet, a bucket under the drip,
  water stains on the carpet, walls and the mattress
- 106 the next guest: someone checked in recently: bed slept in, a duffel bag, a meal tray, and
  on the nightstand a red lantern with a card: "Complimentary. For the lake."
"""

MATS.update({
    "couch_mat": (0.2, 0.13, 0.09), "magazine_mat": (0.45, 0.4, 0.32), "book_red_mat": (0.3, 0.06, 0.05),
    "book_green_mat": (0.08, 0.16, 0.1), "book_brown_mat": (0.24, 0.15, 0.08), "paper_mat": (0.62, 0.6, 0.52),
    "seeglass_red_mat": (0.4, 0.02, 0.01), "bakelite_mat": (0.12, 0.06, 0.03), "ash_mat": (0.3, 0.3, 0.29),
    "panel_mat": (0.3, 0.2, 0.12), "linoleum_mat": (0.32, 0.3, 0.24), "blanket_mat": (0.22, 0.2, 0.14),
    "coat_mat": (0.16, 0.13, 0.1), "bear_mat": (0.35, 0.24, 0.14), "dustsheet_mat": (0.52, 0.5, 0.45),
    "drip_mat": (0.18, 0.14, 0.08), "debris_mat": (0.42, 0.4, 0.36), "duffel_mat": (0.14, 0.17, 0.12),
    "food_mat": (0.3, 0.16, 0.06), "phone_mat": (0.5, 0.45, 0.36),
    # shared with the lake buildings (same colours as BLD_MATS there)
    "rusty_tool_mat": (0.2, 0.11, 0.07), "dark_leather_mat": (0.09, 0.06, 0.04), "can_mat": (0.36, 0.34, 0.31),
    "paint_can_mat": (0.3, 0.29, 0.26), "mattress_mat": (0.38, 0.34, 0.27),
    "ceiling_mat": (0.62, 0.6, 0.55), "mirror_mat": (0.05, 0.055, 0.06), "rug_mat": (0.3, 0.17, 0.11),
    "glow_tv_mat": (0.06, 0.1, 0.22), "glow_dial_mat": (1.0, 0.45, 0.12), "glow_ember_mat": (1.0, 0.22, 0.03),
})


class Moved:
    """Everything made inside the with-block is turned by yaw around (px, py), then moved by (dx, dy)."""
    def __init__(self, px, py, yaw, dx=0.0, dy=0.0):
        self.a = (px, py, yaw, dx, dy)

    def __enter__(self):
        self.n, self.m = len(PARTS), len(ROOM_PARTS)
        return self

    def __exit__(self, *exc):
        px, py, yaw, dx, dy = self.a
        new = PARTS[self.n:] + ROOM_PARTS[self.m:]
        if new:
            g = cmds.group(new, name="moved_grp")
            cmds.rotate(0, -yaw, 0, g, pivot=(px, 0, py))
            cmds.move(dx, 0, dy, g, relative=True)
            cmds.ungroup(g)


# ---------- small props ----------

def book(x, y, z, w, d, h, mat, yaw=0, lie=False):
    """A hardback: board covers, a paler block of pages, standing (lie=False) or lying flat."""
    if lie:
        rbevel(x, y, z + h / 2.0, w, d, h, mat, r=0.4, yaw=yaw)
        rbevel(x + 0.6, y, z + h / 2.0, w - 1.6, d - 1.2, h - 0.8, "paper_mat", r=0.2, yaw=yaw)
    else:
        rbevel(x, y, z + h / 2.0, w, d, h, mat, r=0.4, yaw=yaw)


def red_lantern(x, y, z, name=None):
    """The town's red lantern: a tin base and cap, red glass chimney, a wire bail. Unlit unless
    name is given (then a dim red light)."""
    frustum(x, y, z, z + 4, 6.5, 6.5, "rusty_tool_mat", sides=14)
    frustum(x, y, z + 4, z + 22, 5.5, 5.5, "seeglass_red_mat", sides=14)
    for k in range(3):
        a = k * 2.094
        tube((x + 6 * math.cos(a), y + 6 * math.sin(a), z + 4), (x + 6 * math.cos(a), y + 6 * math.sin(a), z + 22), 0.3, "rusty_tool_mat", sides=4)
    frustum(x, y, z + 22, z + 27, 6.5, 2, "rusty_tool_mat", sides=14)
    ring(x, y, z + 27, 6, 0.3, "rusty_tool_mat", axis="x", sides=14)
    if name:
        light(name, x, y, z + 14, [1.0, 0.05, 0.02], 2, 260, room=True)


def ashtray(x, y, z, lit=True):
    frustum(x, y, z, z + 2.2, 6, 6.5, "glass_mat", sides=14)
    frustum(x, y, z + 1.2, z + 2.3, 4.8, 5.2, "ash_mat", sides=14)
    for k in range(3):                                                    # old butts
        tube((x - 3 + k * 2.5, y - 2 + k, z + 2.4), (x - 1 + k * 2.5, y + 1 + k, z + 2.6), 0.4, "paper_mat", sides=6)
    # the one still burning, resting on the rim
    tube((x + 5, y, z + 2.6), (x + 11, y + 1.5, z + 2.9), 0.42, "paper_mat", sides=6)
    if lit:
        tube((x + 11, y + 1.5, z + 2.9), (x + 11.6, y + 1.65, z + 2.95), 0.44, "glow_ember_mat", sides=6)


def mug_at(x, y, z, full=True):
    frustum(x, y, z, z + 9.5, 3.8, 4.1, "mug_mat", sides=14, open_ends=True)
    frustum(x, y, z + 0.3, z + 9.3, 3.4, 3.7, "mug_mat", sides=14, open_ends=True, inside=True)
    frustum(x, y, z, z + 0.4, 3.8, 3.8, "mug_mat", sides=14)
    if full:
        frustum(x, y, z + 7.6, z + 7.9, 3.6, 3.6, "coffee_mat", sides=14)
    ring(x + 4.6, y, z + 5, 2.4, 0.6, "mug_mat", axis="y", sides=10)


def papers(x, y, z, n, seed, spread=6):
    r = random.Random(seed)
    for k in range(n):
        rbevel(x + r.uniform(-spread, spread), y + r.uniform(-spread, spread), z + 0.15 + k * 0.25, 21, 28, 0.15,
               "paper_mat", r=0.05, yaw=r.uniform(-25, 25))


def radio(x, y, z, yaw=0):
    """A bakelite table radio, its dial lit (it's on)."""
    with Moved(x, y, yaw):
        rbevel(x, y, z + 10, 30, 14, 20, "bakelite_mat", r=3, seg=3)
        rbevel(x - 6, y - 7.2, z + 12, 14, 0.8, 9, "glow_dial_mat", r=0.3)
        for k in range(4):
            rbevel(x + 9, y - 7.2, z + 6 + k * 3, 8, 0.8, 1.2, "trim_mat", r=0.2)
        for dx in (-10, 4):
            tube((x + dx, y - 7, z + 4.5), (x + dx, y - 9.5, z + 4.5), 1.8, "trim_mat", sides=10)


def desk_lamp(x, y, z, name):
    """A green banker's style lamp, on."""
    frustum(x, y, z, z + 2, 9, 8, "brass_mat", sides=16)
    tube((x, y, z + 2), (x, y, z + 32), 0.9, "brass_mat", sides=8)
    rbevel(x, y - 3, z + 34, 30, 12, 6, "book_green_mat", r=2.5, seg=3)
    rbevel(x, y - 3, z + 31.2, 26, 9, 0.6, "glow_lamp_mat", r=0.2)
    light(name, x, y - 3, z + 26, [1.0, 0.78, 0.5], 10, 480, room=True)


def swivel_chair(x, y, yaw):
    """An office chair on a five-star base, pushed back and turned away from the desk."""
    for k in range(5):
        a = math.radians(yaw + k * 72)
        tube((x, y, 8), (x + 30 * math.cos(a), y + 30 * math.sin(a), 5), 1.8, "metal_mat", sides=6)
        sphere(x + 30 * math.cos(a), y + 30 * math.sin(a), 3, 3, "trim_mat", sides=8)
    tube((x, y, 8), (x, y, 44), 2.4, "metal_mat", sides=8)
    with Moved(x, y, yaw):
        rsoft(x, y, 48, 48, 46, 9, "couch_mat", jitter=0.4, smooth=2, seed=5)
        tube((x, y + 20, 48), (x, y + 24, 70), 1.6, "metal_mat", sides=6)
        rsoft(x, y + 25, 88, 44, 9, 42, "couch_mat", jitter=0.4, smooth=2, seed=6, tilt_y=-8)


def bell(x, y, z):
    frustum(x, y, z, z + 1.2, 5, 5, "trim_mat", sides=16)
    sphere(x, y, z + 2, 4.3, "brass_mat", sides=14, scale=(1, 1, 0.7))
    tube((x, y, z + 4.5), (x, y, z + 6.5), 0.5, "brass_mat", sides=6)
    sphere(x, y, z + 6.8, 0.9, "brass_mat", sides=8)


def guest_book(x, y, z, yaw=0):
    """The guest book lying open: two page blocks in a cloth cover, the pages lined (pic texture
    later; plain paper for now), a ribbon."""
    with Moved(x, y, yaw):
        rbevel(x, y, z + 0.4, 62, 40, 0.8, "book_red_mat", r=0.3)
        for s in (-1, 1):
            rsoft(x + s * 15, y, z + 1.8, 28, 37, 2.2, "paper_mat", sag=-0.6, smooth=1, seed=8 + s, div=(4, 1, 2))
        rbevel(x + 2, y + 22, z + 2.5, 1, 8, 0.2, "red_string_mat", r=0.05)


def couch(x0, x1, y0, y1):
    """A tired 70s couch, back against y1 (facing -y): a base on turned wooden feet, three seat
    cushions with piped edges (the middle one sagging), button-tufted back cushions, rolled arms."""
    cxm, w_all = (x0 + x1) / 2.0, x1 - x0
    rsoft(cxm, (y0 + y1) / 2.0 + 4, 24, w_all - 8, y1 - y0 - 10, 22, "couch_mat", jitter=0.4, smooth=2, seed=11, div=(6, 2, 3))
    bevel_box(x0 + 6, x1 - 6, y1 - 22, y1 - 4, 30, 62, "couch_mat", r=4, seg=3)            # back frame
    aw = 18.0
    n = 3
    w = (w_all - 2 * aw) / n
    for k in range(n):
        cx = x0 + aw + w * (k + 0.5)
        sy0, sy1 = y0 + 4, y1 - 24
        rsoft(cx, (sy0 + sy1) / 2.0, 41, w - 2, sy1 - sy0, 13, "couch_mat", jitter=0.6, sag=3.0 if k == 1 else 1.2,
              smooth=2, seed=20 + k, div=(5, 2, 5))
        tube((cx - w / 2 + 3, sy0 + 1, 44), (cx + w / 2 - 3, sy0 + 1, 44), 0.9, "trim_mat", sides=8)    # piping
        rsoft(cx, y1 - 15, 70, w - 3, 18, 40, "couch_mat", jitter=0.6, smooth=2, seed=30 + k, tilt_y=8, div=(5, 4, 2))
        for r_ in range(2):                                                   # tufting buttons
            for c_ in range(3):
                sphere(cx - w / 3.0 + c_ * w / 3.0, y1 - 25 + r_ * 2.5, 60 + r_ * 16, 1.1, "trim_mat", sides=8)
    for x in (x0 + aw / 2.0, x1 - aw / 2.0):                                   # rolled arms
        rsoft(x, (y0 + y1) / 2.0, 44, aw, y1 - y0 - 2, 34, "couch_mat", jitter=0.4, smooth=2, seed=int(x), div=(3, 4, 5))
        tube((x, y0 + 2, 60), (x, y1 - 4, 60), aw * 0.52, "couch_mat", sides=14)
    for x in (x0 + 10, x1 - 10):
        for y in (y0 + 10, y1 - 10):
            lathe(x, y, [(5, 1.6), (8, 2.2), (12, 2.8), (13, 3.4)], "wood_mat", sides=12)


def coffee_table(cx, cy):
    """Coffee table: a top with a moulded edge, an apron, turned legs, a magazine shelf."""
    rbevel(cx, cy, 40, 110, 55, 3, "wood_mat", r=1.2, seg=3)
    for yy in (cy - 27.5, cy + 27.5):
        tube((cx - 55, yy, 38.6), (cx + 55, yy, 38.6), 1.0, "wood_mat", sides=8)
    for (a, b, c_, d) in ((-50, 50, -24, -22.5), (-50, 50, 22.5, 24), (-50, -48.5, -24, 24), (48.5, 50, -24, 24)):
        bevel_box(cx + a, cx + b, cy + c_, cy + d, 31, 38.5, "wood_mat", r=0.4)
    for dx in (-47, 47):
        for dy in (-21, 21):
            lathe(cx + dx, cy + dy, [(5, 1.4), (7, 2.0), (14, 1.5), (19, 2.4), (23, 2.4), (29, 1.8), (31, 2.6), (38.5, 2.6)],
                  "wood_mat", sides=12)
    rbevel(cx, cy, 13, 96, 44, 1.5, "wood_mat", r=0.5)


def end_table(cx, cy, top=60):
    """A small end table like the rooms' nightstands: drawer with a brass knob, a shelf."""
    bevel_box(cx - 28, cx + 28, cy - 24, cy + 24, 11, top - 2.5, "wood_mat", r=1)
    bevel_box(cx - 30, cx + 30, cy - 26, cy + 26, top - 3, top, "wood_mat", r=1)
    for lx in (cx - 26, cx + 22):
        for ly in (cy - 22, cy + 18):
            bevel_box(lx, lx + 4, ly, ly + 4, 5, 11.5, "wood_mat", r=0.8)
    bevel_box(cx - 24, cx + 24, cy - 25.5, cy - 24, top - 22, top - 6, "wood_mat", r=0.8)
    sphere(cx, cy - 26.2, top - 14, 1.6, "brass_mat", sides=8)
    bevel_box(cx - 24, cx + 24, cy - 24.5, cy + 20, 15, top - 26, "trim_mat", r=0.5)


def wainscot(axis, fixed, a, b, d, top=96.0, base=14.0):
    """Wood panelling below a chair rail: a backing board, raised panels with a field, a rounded
    chair rail and a baseboard; on the wall face `fixed`, the room toward d (+1 / -1)."""
    def bx(p, q, o0, o1, z0, z1, r):
        lo, hi = min(fixed + d * o0, fixed + d * o1), max(fixed + d * o0, fixed + d * o1)
        if axis == "x":
            bevel_box(p, q, lo, hi, z0, z1, "wood_mat", r=r)
        else:
            bevel_box(lo, hi, p, q, z0, z1, "wood_mat", r=r)
    if b - a < 4:
        return
    bx(a, b, 0.6, 1.4, base, top, 0.2)
    n = max(1, int((b - a) / 58))
    w = (b - a) / n
    for k in range(n):
        p, q = a + k * w + 7, a + (k + 1) * w - 7
        if q - p < 14:
            continue
        bx(p, q, 1.4, 2.4, base + 9, top - 12, 1.2)                  # raised panel
        bx(p + 6, q - 6, 2.4, 2.9, base + 15, top - 18, 0.8)         # its field
    bx(a, b, 1.4, 4.2, top - 2, top + 4, 1.4)                        # chair rail
    bx(a, b, 0.6, 2.6, 5, base, 0.5)                                 # baseboard


def crown(axis, fixed, a, b, d, ceil_z):
    """Two-step crown moulding where the wall meets the ceiling."""
    def bx(o0, o1, z0, z1):
        lo, hi = min(fixed + d * o0, fixed + d * o1), max(fixed + d * o0, fixed + d * o1)
        if axis == "x":
            bevel_box(a, b, lo, hi, z0, z1, "wood_mat", r=0.6)
        else:
            bevel_box(lo, hi, a, b, z0, z1, "wood_mat", r=0.6)
    bx(0.6, 3.0, ceil_z - 12, ceil_z - 0.5)
    bx(3.0, 5.5, ceil_z - 6, ceil_z - 0.5)


def wall_calendar(x_wall, y, z, facing, page_mat="paper_mat"):
    """A calendar on a nail (on a wall facing +x, or -x with facing=-1)."""
    fx = x_wall + facing * 0.9
    rbevel(fx, y, z, 0.6, 30, 42, page_mat, r=0.1)
    rbevel(fx + facing * 0.4, y, z + 12, 0.5, 28, 16, "pic_lake_fog", r=0.05)
    for r_ in range(4):
        for c in range(7):
            rbevel(fx + facing * 0.4, y - 12 + c * 4, z - 4 - r_ * 4, 0.3, 3, 3, "trim_mat" if (r_ + c) % 5 else "red_string_mat", r=0.0)


def step_ladder(x, y, yaw):
    with Moved(x, y, yaw):
        for s in (-1, 1):
            tube((x + s * 22, y - 30, 0), (x + s * 18, y, 160), 2.2, "wood_mat", sides=6)
            tube((x + s * 22, y + 30, 0), (x + s * 18, y, 160), 1.8, "wood_mat", sides=6)
        for k in range(4):
            z = 35 + k * 35
            yy = y - 30 + 30 * z / 160.0
            rbevel(x, yy, z, 44 - z * 0.05, 9, 2.5, "wood_mat", r=0.5)
        rbevel(x, y, 162, 40, 16, 3, "wood_mat", r=0.6)


def bucket(x, y, z=0, mat="metal_mat"):
    frustum(x, y, z, z + 28, 12, 15, mat, sides=16, open_ends=True)
    frustum(x, y, z + 0.5, z + 27.5, 11.4, 14.4, mat, sides=16, open_ends=True, inside=True)
    frustum(x, y, z, z + 0.6, 12, 12, mat, sides=16)
    frustum(x, y, z + 14, z + 14.6, 12.6, 12.6, "drip_mat", sides=16)        # brown water in it
    ring(x, y, z + 30, 15, 0.35, "metal_mat", axis="x", sides=16)


def stain(x, y, z, r, seed, mat="drip_mat"):
    """A flat irregular stain lying on a surface (top z)."""
    rsoft(x, y, z + 0.4, r * 2, r * 1.6, 0.8, mat, jitter=r * 0.12, smooth=1, seed=seed, div=(4, 1, 4), yaw=seed * 37 % 180)


def teddy(x, y, z, yaw):
    with Moved(x, y, yaw):
        sphere(x, y, z + 11, 10, "bear_mat", sides=12, scale=(1, 0.85, 1.1))
        sphere(x, y - 1, z + 27, 8, "bear_mat", sides=12)
        for s in (-1, 1):
            sphere(x + s * 6, y - 1, z + 34, 3, "bear_mat", sides=8)
            sphere(x + s * 11, y - 2, z + 15, 4, "bear_mat", sides=8, scale=(1.4, 1, 1))
            sphere(x + s * 6, y - 7, z + 4, 4.5, "bear_mat", sides=8, scale=(1, 1.5, 1))
            sphere(x + s * 3, y - 7.5, z + 29, 0.9, "dash_mat", sides=6)
        sphere(x, y - 8, z + 25, 2.5, "drip_mat", sides=8)


def dust_sheet(cx, cy, w, d, h, seed, drop=4):
    """A sheet thrown over furniture (w x d, h tall): flat on top, falling to the floor in folds."""
    rng = random.Random(seed)
    grid = []
    rows, cols = 18, 18
    for r_ in range(rows + 1):
        v = r_ / rows
        row = []
        for c in range(cols + 1):
            u = c / cols
            ex = (u - 0.5) * (w + 2 * h * 0.28)
            ey = (v - 0.5) * (d + 2 * h * 0.28)
            out = max(abs(ex) - w / 2.0, abs(ey) - d / 2.0, 0.0)
            z = h + 1.5 - out / 0.28 if out > 0 else h + 1.5
            z = max(drop * 0.5, z)
            wob = 2.2 * math.sin(u * 19 + seed) * math.sin(v * 13) * (out > 0) + rng.uniform(-0.4, 0.4)
            row.append((ex + wob, cy + ey + wob * 0.5, z + (0 if out else rng.uniform(-0.3, 0.3))))
        grid.append(row)
    _cloth(cx, grid, "dustsheet_mat")


def tv_small(x, y, z, facing_y=-1, on=True):
    """A small portable TV facing -y (facing_y=-1) or +y, screen lit when on."""
    rbevel(x, y, z + 18, 44, 34, 36, "tv_mat", r=3, seg=3)
    rbevel(x, y - facing_y * 26, z + 18, 30, 18, 26, "tv_mat", r=4, seg=2)
    rbevel(x - 4, y + facing_y * 17.2, z + 19, 30, 0.8, 24, "glow_tv_mat" if on else "screen_mat", r=0.6)
    for k in range(2):
        tube((x + 16, y + facing_y * 17, z + 26 - k * 9), (x + 16, y + facing_y * 19, z + 26 - k * 9), 2, "trim_mat", sides=10)
    if on:
        light("light_office_tv", x - 4, y + facing_y * 60, z + 20, [0.5, 0.65, 1.0], 2.5, 360, room=True)


def armchair(cx, cy, yaw, mat="couch_mat"):
    """An upholstered motel armchair, facing -y before yaw: seat cushion, tufted back, rolled
    arms, turned wooden feet."""
    with Moved(cx, cy, yaw):
        rsoft(cx, cy + 2, 26, 74, 70, 24, mat, jitter=0.4, smooth=2, seed=int(cx) % 50, div=(4, 2, 4))
        rsoft(cx, cy - 4, 43, 50, 56, 12, mat, jitter=0.6, sag=1.5, smooth=2, seed=int(cy) % 50, div=(4, 2, 4))
        rsoft(cx, cy + 28, 72, 56, 16, 46, mat, jitter=0.6, smooth=2, seed=7, tilt_y=8, div=(4, 4, 2))
        for c_ in range(3):
            for r_ in range(2):
                sphere(cx - 16 + c_ * 16, cy + 18.5 + r_ * 2.5, 63 + r_ * 16, 1.0, "trim_mat", sides=8)
        for s_ in (-1, 1):
            rsoft(cx + s_ * 31, cy + 2, 46, 12, 68, 30, mat, jitter=0.4, smooth=2, seed=11 + s_, div=(2, 3, 4))
            tube((cx + s_ * 31, cy - 32, 60), (cx + s_ * 31, cy + 34, 60), 7, mat, sides=12)
        for x in (cx - 30, cx + 30):
            for y in (cy - 28, cy + 30):
                lathe(x, y, [(5, 1.5), (8, 2.1), (13, 2.7), (14, 3.2)], "wood_mat", sides=10)


def bathroom_door(x_wall, y0, y1):
    """A closed door in the left wall (facing +x) to the bathroom: panelled slab, casing, knob."""
    bevel_box(x_wall, x_wall + 3.5, y0, y1, 3, 206, "door_mat", r=0.8)
    for a, b in ((y0 + 9, (y0 + y1) / 2.0 - 4), ((y0 + y1) / 2.0 + 4, y1 - 9)):
        for za, zb in ((18, 92), (104, 194)):
            bevel_box(x_wall + 3.5, x_wall + 4.6, a, b, za, zb, "door_mat", r=0.8)
    for a, b, c_, d in ((y0 - 8, y0, 3, 214), (y1, y1 + 8, 3, 214), (y0 - 8, y1 + 8, 206, 214)):
        bevel_box(x_wall, x_wall + 2, a, b, c_, d, "wood_mat", r=0.5)
    kx = x_wall + 3.5
    bevel_box(kx, kx + 0.8, y1 - 16, y1 - 10, 88, 106, "brass_mat", r=0.4)
    tube((kx, y1 - 13, 97), (kx + 5, y1 - 13, 97), 1.0, "brass_mat", sides=8)
    sphere(kx + 6.4, y1 - 13, 97, 2.8, "brass_mat", sides=12)


def rotary_phone(x, y, z, yaw=0):
    with Moved(x, y, yaw):
        rbevel(x, y, z + 4, 20, 22, 8, "phone_mat", r=3, seg=2)
        frustum(x, y - 2, z + 8, z + 9.5, 7, 6.5, "phone_mat", sides=18)
        frustum(x, y - 2, z + 9.5, z + 10, 6, 6, "plate_mat", sides=18)
        for s_ in (-1, 1):
            rbevel(x + s_ * 8, y + 4, z + 10, 6, 8, 5, "phone_mat", r=2)
        rbevel(x, y + 4, z + 13, 24, 5, 4, "phone_mat", r=1.8)
        tube((x + 10, y + 10, z + 3), (x + 18, y + 14, z + 1), 0.4, "trim_mat", sides=4)


def ice_bucket(x, y, z):
    frustum(x, y, z, z + 15, 9, 10.5, "plate_mat", sides=18)
    ring(x, y, z + 15, 10.6, 0.6, "plate_mat", sides=18)
    frustum(x, y, z + 15, z + 17, 10, 7, "plate_mat", sides=18)
    ring(x, y, z + 18.5, 2.5, 0.5, "plate_mat", axis="x", sides=10)


def room_finish(i, x0, x1):
    """What every motel room gets beyond room_inside(): crown moulding round the ceiling, a
    smoke detector, a cased door frame inside, a closed bathroom door, and (not in Room 104,
    which is dressed with Cas's things) a painting over the bed, a mirror over the dresser, an
    armchair by the window, a phone and an ice bucket. Runs with IN_ROOM on."""
    t = 20
    L, R = x0 + t, x1 - t
    FI, BI = FRONT + t + 2, BACK - t
    # crown moulding on all four walls
    for axis, fixed, d, a, b in (("x", FI, 1, L, R), ("x", BI, -1, L, R), ("y", L, 1, FI, BI), ("y", R, -1, FI, BI)):
        crown(axis, fixed, a, b, d, H - 10)
    # smoke detector
    frustum(x0 + 330, BACK - 380, H - 13.5, H - 10.5, 6.5, 7, "plate_mat", sides=16)
    sphere(x0 + 334, BACK - 380, H - 13.8, 0.6, "glow_ember_mat", sides=6)
    # the door from inside: a casing like the office's
    for a_, b_, c_, e_ in ((x0 + 131, x0 + 140, 2, 239), (x0 + 280, x0 + 289, 2, 239), (x0 + 131, x0 + 289, 230, 239)):
        bevel_box(a_, b_, FI, FI + 2, c_, e_, "wood_mat", r=0.6)
    bathroom_door(L, BACK - 185, BACK - 100)
    if i == HER_ROOM:
        return
    # painting over the bed (the same frame and picture as Room 104's)
    py, pz, pw, ph = BACK - 135, 168, 84, 57
    bevel_box(R - 3.5, R, py - pw / 2 - 5, py + pw / 2 + 5, pz - ph / 2 - 5, pz + ph / 2 + 5, "frame_mat", r=1.2)
    picture(R - 4.3, py, pz, pw, ph, "pic_painting", facing=-1)
    if i not in (1, 2):
        rotary_phone(x0 + 165, BACK - 50, 60, yaw=-15)
    if i in (0, 4, 5):
        ice_bucket(x0 + 58, FRONT + 228, 80)
    # an armchair by the window, turned toward the TV, a little round table next to it
    if i != 2:
        armchair(x1 - 85, FRONT + 300, -110)
        lathe(x1 - 70, FRONT + 205, [(0, 18), (2, 18), (3, 3), (52, 2.5), (54, 3.5), (55, 26), (58, 26)], "wood_mat", sides=24)


# ---------- the office ----------

def office():
    x0, x1, y0, y1, h = OFFICE
    t = 20
    d0, d1, dh = x0 + 50, x0 + 160, 230                  # doorway (the door itself is BP_Examinable)
    # the shell (outside mesh): walls, roof, brick skirt, door frame
    box(x0, x1, y1 - t / 2, y1, 0, h, "plaster_mat")
    box(x0, x0 + t / 2, y0, y1, 0, h, "plaster_mat")
    box(x1 - t / 2, x1, y0, y1, 0, h, "plaster_mat")
    box(x0, d0, y0, y0 + t, 0, h, "plaster_mat")
    box(d1, x1, y0, y0 + t, 0, h, "plaster_mat")
    box(d0, d1, y0, y0 + t, dh, h, "plaster_mat")
    for a, b in ((x0, d0 - 10), (d1 + 10, x1)):
        box(a, b, y0 - 3, y0, 0, 100, "brick_mat")
    box(x0 - 30, x1 + 30, y0 - 150, y1 + 30, h, h + 15, "roof_metal_mat")
    box(x0 - 30, x1 + 30, y0 - 158, y0 - 150, h - 25, h + 15, "trim_mat")
    tube((x0 - 30, y0 - 160, h - 21), (x1 + 30, y0 - 160, h - 21), 2.5, "glow_neon_red_mat")
    box(d0 - 10, d0, y0 - 5, y0, 0, dh + 8, "trim_mat")
    box(d1, d1 + 10, y0 - 5, y0, 0, dh + 8, "trim_mat")
    box(d0 - 10, d1 + 10, y0 - 5, y0, dh, dh + 8, "trim_mat")
    # front window: the opening in the wall is real now, so you can see in (and out)
    wx0, wx1 = x0 + 430, x1 - 30
    box(wx0 - 8, wx1 + 8, y0 - 6, y0, 95, 103, "trim_mat")
    box(wx0 - 8, wx1 + 8, y0 - 6, y0, 242, 250, "trim_mat")
    neon_word("OPEN", wx1 - 30, y0 - 12, 150, 40, "glow_neon_red_mat", r=3.5)
    light("light_open", (wx0 + wx1) / 2.0, y0 - 25, 170, [1.0, 0.0, 0.0], 600, 600)
    ice_machine(X0 + ROOMS * ROOM_W + 120, FRONT - 70)

    # ---- inside (lighting channel 1)
    IN_ROOM[0] = True
    L, R, F, B = x0 + t / 2 + 1, x1 - t / 2 - 1, y0 + t + 1, y1 - t / 2 - 1       # inner faces
    P0, P1 = -1136.0, -1124.0                          # the partition between the office and the back room
    PD0, PD1 = x1 - 140, x1 - 50                       # its doorway
    # like the rooms: the motel wallpaper (room_wall_mat) above a wood wainscot, crown moulding,
    # the motel carpet; walls lined 1 cm in from the shell
    def lining(axis, fixed, a, b, d, holes=()):
        spans = [(a, b, 0, h - 12)]
        for ha, hb, hz0, hz1 in holes:
            nxt = []
            for p, q, z0_, z1_ in spans:
                if hb <= p or ha >= q:
                    nxt.append((p, q, z0_, z1_))
                    continue
                if ha > p:
                    nxt.append((p, ha, z0_, z1_))
                if hb < q:
                    nxt.append((hb, q, z0_, z1_))
                nxt.append((max(p, ha), min(q, hb), hz1, z1_))
                if hz0 > z0_:
                    nxt.append((max(p, ha), min(q, hb), z0_, hz0))
            spans = nxt
        for p, q, z0_, z1_ in spans:
            if q - p < 1 or z1_ - z0_ < 1:
                continue
            if axis == "x":
                box(p, q, fixed - 0.5, fixed + 0.5, z0_, z1_, "room_wall_mat")
            else:
                box(fixed - 0.5, fixed + 0.5, p, q, z0_, z1_, "room_wall_mat")
            if z0_ < 1 and z1_ > 100:
                wainscot(axis, fixed + d * 0.5, p, q, d)
        crown(axis, fixed + d * 0.5, a, b, d, h - 12)
    lining("x", F + 0.5, L, R, 1, [(d0 - 10, d1 + 10, 0, dh + 8), (wx0 - 8, wx1 + 8, 99, 250)])
    lining("x", B - 0.5, L, R, -1)
    lining("y", L + 0.5, F, B, 1)
    lining("y", R - 0.5, F, B, -1)
    box(L, R, F, B, h - 12, h - 11, "plaster_mat")                                  # ceiling
    box(L + 1, R - 1, F + 1, P0, 0, 5.0, "carpet_mat")                                # motel carpet (the lot is z 3 here)
    box(L + 1, R - 1, P1, B - 1, 0, 5.0, "linoleum_mat")                              # back room: old linoleum
    # the entrance from inside: a casing round the door like the rooms'
    for a_, b_, c_, e_ in ((d0 - 9, d0, 5, dh + 9), (d1, d1 + 9, 5, dh + 9), (d0 - 9, d1 + 9, dh, dh + 9)):
        bevel_box(a_, b_, F + 1, F + 3, c_, e_, "wood_mat", r=0.6)
    # the partition with its doorway: wallpapered, wainscot on both faces, a cased doorway
    box(L + 1, PD0, P0, P1, 0, h - 12, "room_wall_mat")
    box(PD1, R - 1, P0, P1, 0, h - 12, "room_wall_mat")
    box(PD0, PD1, P0, P1, 215, h - 12, "room_wall_mat")
    for d_, fx in ((-1, P0), (1, P1)):
        wainscot("x", fx, L + 1, PD0 - 8, d_)
        wainscot("x", fx, PD1 + 8, R - 1, d_)
        crown("x", fx, L + 1, R - 1, d_, h - 12)
    for x in (PD0 - 8, PD1):
        bevel_box(x, x + 8, P0 - 3, P1 + 3, 5, 223, "wood_mat", r=0.6)
    bevel_box(PD0 - 8, PD1 + 8, P0 - 3, P1 + 3, 215, 223, "wood_mat", r=0.6)
    # the back-room door, left ajar
    with Moved(PD0, P1, -62):
        bevel_box(PD0, PD1 - 2, P1, P1 + 4, 1, 213, "door_mat", r=0.8)
        sphere(PD1 - 10, P1 + 6, 100, 2.2, "brass_mat", sides=8)
    # window like the rooms': glass, casing, sill, a brass rod with the curtains pulled to the
    # sides, the old blinds half down between them
    box(wx0, wx1, y0 + 2, y0 + 3, 103, 242, "seeglass_window_mat")
    bevel_box(wx0 - 7, wx1 + 7, F, F + 9, 98, 103.5, "wood_mat", r=0.8)
    for a_, b_, c_, e_ in ((wx0 - 7, wx0, 103, 249), (wx1, wx1 + 7, 103, 249), (wx0 - 7, wx1 + 7, 242, 249)):
        bevel_box(a_, b_, F + 1, F + 3, c_, e_, "wood_mat", r=0.5)
    tube((wx0 - 30, F + 12.5, 258), (wx1 + 12, F + 12.5, 258), 0.9, "brass_mat", sides=8)
    for ex in (wx0 - 30, wx1 + 12):
        tube((ex, F + 1, 258), (ex, F + 12.5, 258), 0.6, "brass_mat", sides=6)
        sphere(ex, F + 12.5, 258, 1.8, "brass_mat", sides=8)
    curtain(wx0 - 8, F + 8, 6, 257, 46, "curtain_mat", seed=71, pleats=5)
    curtain(wx1 - 14, F + 8, 108, 257, 40, "curtain_mat", seed=72, pleats=5)          # right one stops at the sill (couch)
    for k in range(14):
        z = 236 - k * 5.2
        if z < 175:
            break
        rbevel((wx0 + wx1) / 2.0, F + 6, z, wx1 - wx0 - 6, 4.5, 0.4, "plate_mat", r=0.1, tilt_y=25)
    rbevel((wx0 + wx1) / 2.0, F + 6, 170, wx1 - wx0 - 4, 5, 2.5, "plate_mat", r=0.5)
    tube(((wx0 + wx1) / 2.0 + 60, F + 6.5, 242), ((wx0 + wx1) / 2.0 + 60, F + 6.5, 150), 0.2, "string_mat", sides=3)
    sphere((wx0 + wx1) / 2.0 + 60, F + 6.5, 148, 1.0, "wood_mat", sides=6)

    # ---- lobby
    with Moved(wx0 + 110, F + 71, 180):              # back to the window, facing the counter
        couch(wx0 + 10, wx0 + 210, F + 30, F + 112)
    cy_ = F + 190
    coffee_table(wx0 + 110, cy_)
    for k in range(5):
        rbevel(wx0 + 80 + k * 13, cy_ - 5 + (k % 2) * 8, 41.6 + k * 0.3, 21, 28, 0.25, "magazine_mat", r=0.05, yaw=k * 17 - 30)
    for k in range(3):
        rbevel(wx0 + 90 + k * 25, cy_ + 3, 14 + k * 0.3, 21, 28, 0.25, "magazine_mat", r=0.05, yaw=k * 9 - 8)
    ashtray(wx0 + 145, cy_ + 10, 41.5, lit=False)
    # an end table by the couch with one of the rooms' lamps on it, lit
    end_table(wx0 - 40, F + 70)
    lamp(wx0 - 40, F + 70)
    light("light_office_lamp", wx0 - 40, F + 70, 100, [1.0, 0.75, 0.45], 3, 360, room=True)
    # the rooms' painting over the couch on the right wall, a dead plant on the end table
    bevel_box(R - 4, R - 1, F + 30, F + 130, 140, 215, "frame_mat", r=0.8)
    picture(R - 4.6, F + 80, 177.5, 88, 63, "pic_painting", facing=-1)
    plant_pot(wx0 - 52, F + 84, 60, random.Random(7))
    ceiling_fan((L + R) / 2.0 + 60, F + 200, h - 12, lit=True)
    # coffee station on the right wall: cabinet, coffee maker (pot on the warmer), cups, sugar
    cx_, cyy = R - 34, F + 290
    bevel_box(cx_ - 28, cx_ + 28, cyy - 50, cyy + 50, 0, 88, "wood_mat", r=1)
    bevel_box(cx_ - 30, cx_ + 30, cyy - 52, cyy + 52, 88, 91, "trim_mat", r=0.6)
    bevel_box(cx_ - 14, cx_ + 14, cyy - 12, cyy + 12, 91, 128, "tv_mat", r=2)
    frustum(cx_ - 4, cyy, 92, 106, 8, 7, "seeglass_window_mat", sides=14)
    frustum(cx_ - 4, cyy, 92.5, 99, 7.5, 7, "coffee_mat", sides=14)
    sphere(cx_ - 15, cyy + 9, 120, 0.9, "glow_ember_mat", sides=6)                     # the 'on' light
    for k in range(5):                                                    # a nested stack of cups
        frustum(cx_ + 8, cyy - 38, 91 + k * 1.6, 100 + k * 1.6, 3.5, 4.2, "chair_mat", sides=12, open_ends=True)
    frustum(cx_ + 8, cyy - 38, 91, 91.6, 3.5, 3.5, "chair_mat", sides=12)
    frustum(cx_ + 8, cyy - 24, 91, 100, 3.5, 4.2, "chair_mat", sides=12, open_ends=True)       # one on its own
    frustum(cx_ + 2, cyy + 35, 91, 101, 4.5, 4.5, "seeglass_window_mat", sides=12)
    # brochure rack and the lantern photo on the left wall (lobby side)
    bx_ = L + 5                                                   # in front of the wainscot
    bevel_box(bx_, bx_ + 6, F + 140, F + 220, 90, 170, "wood_mat", r=0.6)
    for r_ in range(3):
        for c in range(3):
            zz = 100 + r_ * 24
            rbevel(bx_ + 7.5, F + 152 + c * 26, zz + 9, 2.5, 21, 18, ["pic_lake_dusk", "pic_dock", "pic_lake_fog"][(r_ + c) % 3], r=0.2)
            bevel_box(bx_ + 6, bx_ + 11, F + 142 + c * 26, F + 166 + c * 26, zz, zz + 3, "wood_mat", r=0.4)
    # the framed photo: red lanterns floating on the lake at night (a ritual hint)
    bevel_box(bx_, bx_ + 3, F + 240, F + 330, 145, 215, "frame_mat", r=0.8)
    picture(bx_ + 3.6, F + 285, 180, 80, 60, "pic_lanterns", facing=1)
    rbevel(bx_ + 3.2, F + 285, 140, 0.5, 40, 6, "brass_mat", r=0.2)                     # little plaque
    wall_calendar(L + 1, F + 380, 175, 1)

    # the old roadside cross, small now, hung on the wall behind the counter near the coffee
    # machine (built facing -y, then turned to face into the office, -x)
    cyc = -1290.0
    with Moved(R - 3.4, cyc, -90):
        cross(R - 3.4, cyc, 7, top=262, post=False, light_at=(R - 40, cyc, 205, 3, 260))

    # ---- the counter, across the office, its flap up at the left end
    CY0, CY1 = -1400.0, -1340.0
    CX0 = L + 170
    bevel_box(CX0, R - 1, CY0 + 4, CY1, 5, 14, "trim_mat", r=0.8)                       # recessed plinth
    bevel_box(CX0, R - 1, CY0, CY1, 14, 101, "wood_mat", r=1)
    n_ = int((R - 1 - CX0) / 62)
    pw = (R - 1 - CX0) / n_
    for k in range(n_):
        p_, q_ = CX0 + k * pw, CX0 + (k + 1) * pw
        bevel_box(p_ + 1, p_ + 7, CY0 - 1.8, CY0, 14, 101, "wood_mat", r=0.6)              # stiles
        bevel_box(p_ + 13, q_ - 7, CY0 - 1.6, CY0, 24, 90, "wood_mat", r=1.4)              # raised panel
        bevel_box(p_ + 19, q_ - 13, CY0 - 2.2, CY0 - 1.6, 30, 84, "wood_mat", r=0.8)       # its field
    bevel_box(CX0, R - 1, CY0 - 2.5, CY0, 92, 101, "wood_mat", r=0.8)                    # top rail moulding
    bevel_box(CX0 - 4, R, CY0 - 6, CY1 + 4, 101, 108, "wood_mat", r=2.2, seg=3)          # top, rounded
    tube((CX0 - 4, CY0 - 5.5, 104.5), (R, CY0 - 5.5, 104.5), 3.2, "wood_mat", sides=12)  # bullnose edge
    tube((CX0 + 8, CY0 - 16, 20), (R - 8, CY0 - 16, 20), 1.6, "brass_mat", sides=12)     # brass foot rail
    for x in range(int(CX0) + 30, int(R) - 10, 110):
        tube((x, CY0 - 16, 20), (x, CY0, 24), 1.0, "brass_mat", sides=8)
    rbevel(CX0 - 3, (CY0 + CY1) / 2.0, 108 + 32, 4, 70, 64, "wood_mat", r=1, tilt_x=-8)  # the flap, lifted
    bell(CX0 + 50, CY0 + 20, 108)
    guest_book(CX0 + 175, CY0 + 30, 108, yaw=-6)
    pen(CX0 + 215, CY0 + 34, 108.3, 70)
    rbevel(CX0 + 95, CY0 + 14, 108 + 6, 18, 1, 11, "plate_mat", r=0.2, tilt_y=-12)        # RING FOR SERVICE card
    rbevel(CX0 + 95, CY0 + 17, 108 + 5.5, 16, 1, 10, "plate_mat", r=0.2, tilt_y=12)
    # behind the counter: a shelf under the top with papers and a cash box
    bevel_box(CX0 + 10, R - 10, CY1, CY1 + 25, 60, 63, "wood_mat", r=0.6)
    papers(CX0 + 80, CY1 + 12, 63, 5, 3)
    bevel_box(CX0 + 200, CX0 + 240, CY1 + 3, CY1 + 22, 63, 73, "dumpster_mat", r=1)

    # ---- the desk behind the counter, against the partition
    DX0, DX1, DY0, DY1 = L + 330, L + 490, P0 - 76, P0 - 6
    bevel_box(DX0 - 3, DX1 + 3, DY0 - 3, DY1, 74, 77.5, "wood_mat", r=1.2, seg=3)
    bevel_box(DX0 + 46, DX1 - 46, DY1 - 6, DY1 - 3, 30, 74, "wood_mat", r=0.6)          # modesty panel
    bevel_box(DX0 + 46, DX1 - 46, DY0 + 2, DY0 + 4, 64, 73, "wood_mat", r=0.6)          # pencil drawer
    tube((DX0 + 72, DY0 + 1, 68.5), (DX1 - 72, DY0 + 1, 68.5), 0.7, "brass_mat", sides=6)
    for xx in (DX0, DX1 - 46):
        bevel_box(xx + 2, xx + 44, DY0 + 3, DY1 - 3, 8, 74, "wood_mat", r=0.8)
        bevel_box(xx + 4, xx + 42, DY0 + 5, DY1 - 5, 4, 8.5, "trim_mat", r=0.6)
        for za, zb in ((10, 30), (32, 52), (54, 72)):
            bevel_box(xx + 4, xx + 42, DY0 + 1.6, DY0 + 3.2, za + 1, zb - 1, "wood_mat", r=0.8)
            zc = (za + zb) / 2.0
            for dx in (-7, 7):
                box(xx + 23 + dx - 0.6, xx + 23 + dx + 0.6, DY0 + 0.4, DY0 + 1.6, zc - 0.6, zc + 0.6, "brass_mat")
            tube((xx + 15, DY0 + 0.2, zc), (xx + 31, DY0 + 0.2, zc), 0.8, "brass_mat", sides=6)
    desk_lamp(DX1 - 25, DY1 - 22, 77, "light_office")
    radio(DX0 + 30, DY1 - 18, 77, yaw=10)
    ashtray(DX0 + 80, DY0 + 22, 77)
    mug_at(DX0 + 104, DY0 + 18, 77)
    papers(DX0 + 120, DY0 + 35, 77, 6, 9, spread=10)
    pen(DX0 + 75, DY0 + 45, 77.3, -20)
    swivel_chair(DX0 + 70, DY0 - 75, 35)                                                   # pushed back, turned
    # the key board on the partition, left of the desk: hooks 101-106, 104's hook empty
    KX0, KX1 = L + 175, L + 315
    bevel_box(KX0, KX1, P0 - 3, P0, 140, 215, "wood_mat", r=0.8)
    for k in range(6):
        kx = KX0 + 14 + k * 22.5
        rbevel(kx, P0 - 3.4, 205, 14, 0.4, 5, "paper_mat", r=0.1)                       # number plate
        tube((kx, P0 - 3, 190), (kx, P0 - 8, 191), 0.5, "brass_mat", sides=6)
        if k != HER_ROOM:
            ring(kx, P0 - 7.5, 186, 1.6, 0.35, "brass_mat", axis="y", sides=10)
            rbevel(kx, P0 - 7.5, 178, 1.2, 1.4, 6, "brass_mat", r=0.2)                    # key
            rbevel(kx, P0 - 7.2, 167, 5, 0.8, 9, "book_red_mat", r=0.6, tilt_x=45)       # diamond tag
    # the bookcase of old guest books (1974 onward), red lanterns on top
    SX0, SX1 = L + 6, L + 160
    bevel_box(SX0, SX1, P0 - 34, P0 - 5, 5, 12, "trim_mat", r=0.6)                        # plinth
    bevel_box(SX0 + 3, SX1 - 3, P0 - 7, P0 - 5.5, 12, 196, "trim_mat", r=0.3)            # back
    bevel_box(SX0 - 2, SX1 + 2, P0 - 37, P0 - 5, 196, 202, "wood_mat", r=1.2)            # crown
    for x in (SX0, SX1 - 3):
        bevel_box(x, x + 3, P0 - 34, P0 - 5, 5, 200, "wood_mat", r=0.5)
    rng = random.Random(1974)
    for k, z in enumerate((12, 58, 104, 150, 196)):
        bevel_box(SX0, SX1, P0 - 34, P0 - 5, z, z + 3, "wood_mat", r=0.5)
        if z >= 196:
            break
        x = SX0 + 5
        while x < SX1 - 12:
            w_ = rng.uniform(4.5, 7.5)
            hh = rng.uniform(32, 40)
            mat = ("book_red_mat", "book_green_mat", "book_brown_mat")[rng.randrange(3)]
            if rng.random() < 0.08:
                book(x + 14, P0 - 20, z + 3, 28, 22, 6, mat, yaw=90, lie=True)            # one lying flat
                x += 30
                continue
            book(x + w_ / 2.0, P0 - 19, z + 3, w_ - 0.6, 26, hh, mat, yaw=rng.uniform(-2, 2))
            x += w_
    for k in range(3):
        red_lantern(SX0 + 30 + k * 48, P0 - 20, 202)

    # ---- the back room: where the owner lives. A made single bed against the back wall, a rug,
    # an armchair turned to the TV (still on), a little kitchenette with a hot plate and a kettle,
    # a coat rack by the door with the coat, boots under it, a floor lamp, a calendar
    BY0, BY1 = P1 + 1, B
    rsoft((L + R) / 2.0 - 60, (BY0 + BY1) / 2.0, 6, 260, 150, 1.2, "rug_mat", jitter=0.4, smooth=1, seed=9, div=(6, 1, 6))
    # the bed: frame, headboard on the left wall, mattress, sheet, blanket pulled up, pillow
    bx0, bx1, by0, by1 = L + 4, L + 204, BY1 - 104, BY1 - 6
    bevel_box(bx0, bx1, by0, by1, 18, 38, "wood_mat", r=1.5)
    for lx in (bx0 + 4, bx1 - 10):
        for ly in (by0 + 4, by1 - 10):
            bevel_box(lx, lx + 6, ly, ly + 6, 5, 18.5, "wood_mat", r=1)
    bevel_box(bx0, bx0 + 8, by0, by1, 5, 105, "wood_mat", r=1.5)
    bevel_box(bx0 - 1, bx0 + 9, by0 - 2, by1 + 2, 95, 105, "wood_mat", r=2.5)
    bevel_box(bx0 + 10, bx1 - 4, by0 + 4, by1 - 4, 37, 54, "mattress_mat", r=5, seg=3)
    bevel_box(bx0 + 11, bx1 - 5, by0 + 3, by1 - 3, 50, 55.3, "sheet_mat", r=2.5, seg=2)
    rsoft(bx0 + 120, (by0 + by1) / 2.0, 57.5, 158, by1 - by0 + 8, 5, "blanket_mat", jitter=1.6, sag=-1, smooth=2, seed=4, div=(6, 2, 4))
    for s_ in (-1, 1):                                                     # blanket hanging down the sides
        rbevel(bx0 + 120, by0 - 2 if s_ < 0 else by1 + 2, 44, 156, 2.5, 26, "blanket_mat", r=1.0)
    pillow(bx0 + 34, (by0 + by1) / 2.0, 55.5, 44, 62, 13, 7, yaw=90, dent=2.5)
    # the TV on a low cabinet against the partition, still on
    TVX = L + 400
    bevel_box(TVX - 48, TVX + 48, BY0 + 4, BY0 + 50, 5, 58, "wood_mat", r=1)
    for k, xx in enumerate((TVX - 45, TVX + 1)):
        bevel_box(xx, xx + 44, BY0 + 50, BY0 + 51.5, 12, 54, "wood_mat", r=0.8)
        sphere(xx + (38 if k == 0 else 6), BY0 + 52.5, 33, 1.4, "brass_mat", sides=8)
    tv_small(TVX, BY0 + 26, 58, facing_y=1)
    # the armchair turned to it, an ashtray and a mug on a stool beside it
    armchair(TVX - 10, BY1 - 70, 0)                                     # facing the TV
    frustum(TVX - 78, BY1 - 70, 5, 45, 13, 15, "wood_mat", sides=16)
    mug_at(TVX - 81, BY1 - 74, 45)
    ashtray(TVX - 73, BY1 - 62, 45, lit=False)
    # floor lamp by the chair, on low
    lathe(TVX + 60, BY1 - 40, [(5, 13), (8, 12), (9, 1.6), (150, 1.4), (151, 2.4)], "brass_mat", sides=16)
    frustum(TVX + 60, BY1 - 40, 140, 165, 20, 14, "glow_lamp_mat", sides=20, open_ends=True)
    frustum(TVX + 60, BY1 - 40, 140.3, 164.7, 19.4, 13.4, "glow_lamp_mat", sides=20, open_ends=True, inside=True)
    light("light_office_back_lamp", TVX + 60, BY1 - 40, 150, [1.0, 0.72, 0.45], 2.5, 380, room=True)
    # kitchenette on the right of the back wall: base cabinets, counter, hot plate with a pan,
    # a kettle, a shelf with cans and a box of crackers
    KX0, KX1 = R - 230, R - 120
    bevel_box(KX0, KX1, BY1 - 58, BY1, 5, 86, "wood_mat", r=1)
    for k in range(2):
        xx = KX0 + 3 + k * 54
        bevel_box(xx, xx + 50, BY1 - 59.5, BY1 - 58, 12, 82, "wood_mat", r=0.8)
        tube((xx + (44 if k == 0 else 6), BY1 - 60.5, 60), (xx + (44 if k == 0 else 6), BY1 - 60.5, 74), 0.7, "brass_mat", sides=6)
    bevel_box(KX0 - 2, KX1 + 2, BY1 - 62, BY1, 86, 90, "linoleum_mat", r=1)
    lathe(KX0 + 85, BY1 - 28, [(90, 7), (94, 9), (104, 8.5), (108, 5), (110, 1.5)], "metal_mat", sides=16)
    tube((KX0 + 92, BY1 - 28, 98), (KX0 + 99, BY1 - 26, 105), 1.2, "metal_mat", sides=6)
    bevel_box(KX0, KX1, BY1 - 26, BY1, 150, 153, "wood_mat", r=0.6)
    for k in range(4):
        frustum(KX0 + 12 + k * 16, BY1 - 13, 153, 165, 4, 4, "can_mat", sides=12)
    rbevel(KX1 - 18, BY1 - 13, 165, 14, 9, 24, "magazine_mat", r=0.6)
    # coat rack by the doorway with his coat and hat; boots under it
    rx, ry = R - 40, BY0 + 40
    lathe(rx, ry, [(5, 16), (8, 15), (9, 2), (175, 1.8), (180, 3)], "wood_mat", sides=14)
    for k in range(4):
        a_ = k * math.pi / 2 + 0.4
        tube((rx, ry, 168), (rx + 14 * math.cos(a_), ry + 14 * math.sin(a_), 176), 1.0, "wood_mat", sides=6)
    wall_calendar(L + 1, BY0 + 140, 170, 1)
    # a framed photo over the bed: lanterns on the lake again
    bevel_box(L + 1, L + 4, by0 + 20, by0 + 80, 130, 175, "frame_mat", r=0.8)
    picture(L + 4.6, by0 + 50, 152.5, 52, 37, "pic_lake_night", facing=1)
    # the ceiling fan's light over the lobby (the office was left lit)
    light("light_office_lobby", (L + R) / 2.0 + 60, F + 200, h - 90, [1.0, 0.8, 0.55], 5, 650, room=True)
    IN_ROOM[0] = False


# ---------- the other rooms' stories ----------

def room_story(i, x0, x1):
    """Extra dressing for each room but 104 (index 3). Runs with IN_ROOM on."""
    t = 20
    L, R = x0 + t + 1, x1 - t - 1
    FI, BI = FRONT + t + 2, BACK - t - 1
    rng = random.Random(i * 13)
    if i == 0:      # 101: left in a hurry
        # suitcase on the floor, open, clothes spilled out of it
        sx, sy = x0 + 120, BACK - 90
        bevel_box(sx - 38, sx + 38, sy - 24, sy + 24, 0, 16, "suitcase_mat", r=3, seg=3)
        bevel_box(sx - 35, sx + 35, sy - 21, sy + 21, 12, 16.6, "lining_mat", r=1)
        rbevel(sx, sy + 26, 38, 76, 5, 46, "suitcase_mat", r=2.5, tilt_y=-30)
        for k, m in enumerate(("clothes_a_mat", "clothes_b_mat", "clothes_c_mat", "clothes_a_mat")):
            rsoft(sx - 40 + k * 22, sy - 45 - k * 9, 3, 30, 22, 4, m, jitter=2, smooth=2, seed=k + 50, yaw=k * 40)
        # the nightstand drawer pulled out and dropped
        rbevel(x0 + 185, BACK - 120, 9, 48, 36, 17, "wood_mat", r=1, tilt_x=12, yaw=25)
        # the lamp knocked over on the floor, shade rolled away
        tube((x0 + 210, BACK - 150, 5), (x0 + 240, BACK - 165, 5), 1.0, "brass_mat", sides=8)
        frustum(x0 + 250, BACK - 190, 0, 16, 10, 10, "brass_mat", sides=16)
        rbevel(x0 + 255, BACK - 220, 14, 34, 24, 28, "curtain_mat", r=8, tilt_x=80)
        teddy(x0 + 300, FRONT + 230, 0, 160)
        # the room key on the carpet by the door
        ring(x0 + 230, FRONT + 120, 2.6, 1.6, 0.35, "brass_mat", sides=10)
        rbevel(x0 + 238, FRONT + 124, 2.6, 6, 1.4, 0.8, "brass_mat", r=0.2, yaw=20)
        rbevel(x0 + 222, FRONT + 112, 2.4, 5, 9, 0.8, "book_red_mat", r=0.6, yaw=40)
    elif i == 1:    # 102: barricaded, then broken in
        # the chair, tipped over just inside the door
        with Moved(x0 + 200, FRONT + 215, 0):
            rbevel(x0 + 200, FRONT + 215, 21, 42, 40, 4, "wood_mat", r=1.2, tilt_x=88)
            for dz in (-18, 18):
                tube((x0 + 200, FRONT + 200 + dz * 0.2, 0), (x0 + 240, FRONT + 200 + dz * 0.2, 5), 1.8, "wood_mat", sides=8)
            for k in range(3):
                rbevel(x0 + 160 - k * 2, FRONT + 230, 10 + k * 3, 4, 34, 6, "wood_mat", r=0.8)
        # the phone off the hook on the nightstand, the receiver hanging by its cord
        rbevel(x0 + 165, BACK - 47, 63.5, 20, 18, 7, "phone_mat", r=2)
        tube((x0 + 172, BACK - 52, 63), (x0 + 178, BACK - 78, 30), 0.5, "trim_mat", sides=4)
        tube((x0 + 178, BACK - 78, 30), (x0 + 175, BACK - 82, 18), 0.5, "trim_mat", sides=4)
        rbevel(x0 + 175, BACK - 84, 12, 6, 6, 21, "phone_mat", r=2.5, tilt_x=10)
        # a Bible face down on the bed
        book(x0 + 340, BACK - 140, 58.6, 15, 22, 4, "book_brown_mat", yaw=30, lie=True)
    elif i == 2:    # 103: renovation stopped
        # the mattress leaning on the right wall
        rbevel(R - 30, FRONT + 330, 116, 22, 190, 230, "bed_mat", r=5, seg=3, tilt_x=6)   # clear of the bed
        dust_sheet(x0 + t + 28, FRONT + 285, 58, 172, 80, seed=7)                          # the dresser under a sheet
        bevel_box(x0 + 52, x0 + 98, BACK - 175, BACK - 135, 0, 52, "tv_mat", r=3)              # the TV on the floor, sheeted
        dust_sheet(x0 + 75, BACK - 155, 46, 40, 52, seed=8)
        step_ladder(x0 + 330, FRONT + 240, 20)
        for k in range(3):
            frustum(x0 + 270 + k * 25, BACK - 60, 0, 19, 9, 9, "paint_can_mat" if "paint_can_mat" in MATS else "metal_mat", sides=16)
            frustum(x0 + 270 + k * 25, BACK - 60, 19, 20, 8.5, 8.5, "metal_mat", sides=16)
        rbevel(x0 + 220, BACK - 100, 2.5, 34, 26, 3, "metal_mat", r=0.8, yaw=10)            # roller tray
        tube((x0 + 210, BACK - 110, 6), (x0 + 175, BACK - 150, 4), 1.0, "metal_mat", sides=6)
        tube((x0 + 210, BACK - 110, 6), (x0 + 230, BACK - 110, 6), 3.2, "dustsheet_mat", sides=12)
        bevel_box(R - 2, R - 1.2, BACK - 200, BACK - 80, 130, 200, "plaster_mat", r=0.2)   # a fresh plaster patch
    elif i == 4:    # 105: water damage
        cx, cy = x0 + 380, BACK - 220
        # a ceiling panel hanging down from one edge, with a dark wet hole above
        box(cx - 60, cx + 60, cy - 45, cy + 45, H - 11.5, H - 11.3, "drip_mat")
        for k in range(14):
            rsoft(cx + rng.uniform(-60, 60), cy + rng.uniform(-50, 50), 4, rng.uniform(6, 22), rng.uniform(6, 18),
                  rng.uniform(2, 7), "debris_mat", jitter=1.2, smooth=1, seed=k + 60, yaw=rng.uniform(0, 180))
        bucket(cx + 50, cy - 80)
    elif i == 5:    # 106: the next guest
        # a duffel bag on the luggage spot, unzipped
        rsoft(x0 + 120, BACK - 85, 18, 70, 34, 36, "duffel_mat", jitter=1.5, smooth=2, seed=1)
        tube((x0 + 95, BACK - 85, 37), (x0 + 145, BACK - 85, 37), 1.2, "strap_mat", sides=6)
        rsoft(x0 + 135, BACK - 80, 37, 28, 18, 6, "clothes_b_mat", jitter=1.5, smooth=2, seed=2)
        # a room-service tray on the bed, half eaten
        rbevel(x0 + 300, BACK - 160, 59, 46, 34, 2, "metal_mat", r=0.6, yaw=-12)
        frustum(x0 + 295, BACK - 160, 60, 62, 12, 13, "bowl_mat", sides=18)
        rsoft(x0 + 295, BACK - 160, 62.5, 16, 12, 2.5, "food_mat", jitter=0.8, smooth=1, seed=4)
        mug_at(x0 + 315, BACK - 150, 60)
        # on the nightstand: the red lantern, a card propped on it
        red_lantern(x0 + 192, BACK - 40, 60)
        rbevel(x0 + 168, BACK - 52, 64, 10, 1, 7, "plate_mat", r=0.2, tilt_y=-15)


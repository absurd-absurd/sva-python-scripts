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
    "drip_mat": (0.18, 0.14, 0.08), "debris_mat": (0.42, 0.4, 0.36), "duffel_mat": (0.14, 0.17, 0.12), "case_lining_mat": (0.16, 0.14, 0.13), "shirt_mat": (0.4, 0.38, 0.35),
    "sweater_mat": (0.2, 0.24, 0.3), "sweater_red_mat": (0.3, 0.08, 0.07),
    "food_mat": (0.3, 0.16, 0.06), "phone_mat": (0.5, 0.45, 0.36), "phone_dark_mat": (0.03, 0.03, 0.03), "paint_white_mat": (0.78, 0.76, 0.7), "roller_mat": (0.72, 0.7, 0.64), "grip_mat": (0.45, 0.08, 0.05),
    # shared with the lake buildings (same colours as BLD_MATS there)
    "rusty_tool_mat": (0.2, 0.11, 0.07), "dark_leather_mat": (0.09, 0.06, 0.04), "can_mat": (0.36, 0.34, 0.31),
    "paint_can_mat": (0.3, 0.29, 0.26), "mattress_mat": (0.38, 0.34, 0.27),
    "ceiling_mat": (0.62, 0.6, 0.55), "mirror_mat": (0.05, 0.055, 0.06), "rug_mat": (0.3, 0.17, 0.11),
    "glow_tv_mat": (0.06, 0.1, 0.22), "glow_dial_mat": (1.0, 0.45, 0.12), "glow_ember_mat": (1.0, 0.22, 0.03),
})


FONT.update({
    "0": [(1, 0, 3, 0), (3, 0, 4, 1), (4, 1, 4, 5), (4, 5, 3, 6), (3, 6, 1, 6), (1, 6, 0, 5), (0, 5, 0, 1), (0, 1, 1, 0)],
    "1": [(2, 0, 2, 6), (1, 5, 2, 6), (1, 0, 3, 0)],
    "2": [(0, 5, 1, 6), (1, 6, 3, 6), (3, 6, 4, 5), (4, 5, 4, 4), (4, 4, 0, 0), (0, 0, 4, 0)],
    "3": [(0, 6, 4, 6), (4, 6, 2, 3), (2, 3, 3, 3), (3, 3, 4, 2), (4, 2, 4, 1), (4, 1, 3, 0), (3, 0, 1, 0), (1, 0, 0, 1)],
    "4": [(3, 0, 3, 6), (3, 6, 0, 2), (0, 2, 4, 2)],
    "5": [(4, 6, 0, 6), (0, 6, 0, 3), (0, 3, 3, 3), (3, 3, 4, 2), (4, 2, 4, 1), (4, 1, 3, 0), (3, 0, 0, 0)],
    "6": [(4, 6, 1, 6), (1, 6, 0, 5), (0, 5, 0, 1), (0, 1, 1, 0), (1, 0, 3, 0), (3, 0, 4, 1), (4, 1, 4, 2), (4, 2, 3, 3), (3, 3, 0, 3)],
})


def room_key(kx, y_face, z_hook, tag_mat, seed):
    """A motel room key hanging off a cup hook on a board (board face at y_face, facing -y): split
    ring, a brass key (round bow with a hole, shoulder, cut blade with teeth), and a plastic
    diamond fob on its own ring."""
    r = random.Random(seed)
    sw = r.uniform(-4, 4)                                                  # hangs a little crooked
    y = y_face - 4.2
    ring(kx, y, z_hook - 2.0, 1.5, 0.25, "brass_mat", axis="y", sides=12)           # split ring
    with Moved(kx, y, 0):
        bz = z_hook - 6.2
        ring(kx, y, bz, 1.5, 0.55, "brass_mat", axis="y", sides=12)                  # bow
        rbevel(kx, y, bz - 2.2, 1.6, 0.35, 1.0, "brass_mat", r=0.1)                    # shoulder
        rbevel(kx, y, bz - 5.4, 0.9, 0.3, 5.6, "brass_mat", r=0.1)                     # blade
        for k in range(4):
            rbevel(kx + 0.7, y, bz - 3.8 - k * 1.2, 0.6 + 0.3 * (k % 2), 0.3, 0.6, "brass_mat", r=0.05)   # teeth
    # the fob hangs on its own ring beside the key
    ring(kx + 1.2, y + 0.2, z_hook - 3.5, 1.0, 0.2, "brass_mat", axis="y", sides=10)
    rbevel(kx + 1.4 + sw * 0.1, y + 0.3, z_hook - 9.5, 4.6, 0.7, 4.6, tag_mat, r=0.6, tilt_x=45 + sw)
    sphere(kx + 1.4 + sw * 0.1, y - 0.1, z_hook - 7.0, 0.35, "brass_mat", sides=6)   # the fob's eyelet


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
    """A wooden A-frame step ladder standing open: flat front rails with four treads, rear legs
    with cross braces, a top cap, the fold-out paint shelf, metal spreader bars, rubber feet
    and a few old paint drips."""
    H_, lean = 160.0, math.degrees(math.atan(30 / 160.0))
    L = math.hypot(H_, 30)
    with Moved(x, y, yaw):
        for s_ in (-1, 1):
            rbevel(x + s_ * 21, y - 15, H_ / 2, 2.4, 7.5, L, "wood_mat", r=0.5, tilt_y=lean)     # front rails
            rbevel(x + s_ * 21, y + 15, H_ / 2, 2.4, 5.5, L, "wood_mat", r=0.5, tilt_y=-lean)    # rear legs
            for yy in (y - 30, y + 30):
                bevel_box(x + s_ * 21 - 1.6, x + s_ * 21 + 1.6, yy - 3.2, yy + 3.2, 0, 1.2, "tire_mat", r=0.3)   # feet
            # spreader bar: two flat metal arms hinged in the middle, slightly sagging
            fy, zz = 30 - 30 * 70 / H_, 70
            tube((x + s_ * 22.6, y - fy, zz), (x + s_ * 22.6, y, zz - 2.5), 0.5, "metal_mat", sides=6)
            tube((x + s_ * 22.6, y, zz - 2.5), (x + s_ * 22.6, y + fy, zz), 0.5, "metal_mat", sides=6)
            sphere(x + s_ * 22.6, y, zz - 2.5, 0.8, "metal_mat", sides=6)
        for z_ in (38, 76, 114, 150):                                                           # treads
            yy = y - 30 + 30 * z_ / H_
            rbevel(x, yy - 1.5, z_, 40.2, 10, 2.2, "wood_mat", r=0.4)
        for z_ in (40, 105):                                                                    # rear braces
            yy = y + 30 - 30 * z_ / H_
            rbevel(x, yy, z_, 40.2, 1.8, 6, "wood_mat", r=0.4)
        rbevel(x, y + 1, H_ + 2, 48, 24, 3.2, "wood_mat", r=0.6)                                 # top cap
        rbevel(x, y + 17, 118, 36, 16, 1.6, "wood_mat", r=0.4)                                   # paint shelf
        for s_ in (-1, 1):
            tube((x + s_ * 16, y + 9.5, 118), (x + s_ * 16, y + 13, 118), 0.5, "metal_mat", sides=6)
        for k, (dx, z_) in enumerate(((-8, 39.2), (11, 77.2), (-14, 115.2), (5, 151.2))):
            yy = y - 30 + 30 * z_ / H_ - 1.5
            sphere(x + dx, yy, z_ + 0.1, 1.6 + (k % 2), "paint_white_mat", sides=8, scale=(1, 1, 0.18))
        sphere(x + 2, y + 1, H_ + 3.7, 2.4, "paint_white_mat", sides=8, scale=(1, 1, 0.15))


def paint_tray(x, y, yaw):
    """A metal paint roller tray on the floor: a deep well at the front (-y) with white paint
    in it, a ribbed ramp rising to the back, a rolled rim, little feet; the roller resting on
    the ramp (a fluffy paint-covered cover on a bent wire frame, a plastic grip) handle out."""
    W, D, Hr = 33.0, 40.0, 7.0
    with Moved(x, y, yaw):
        hw, hd = W / 2, D / 2
        for s_ in (-1, 1):
            box(x + s_ * hw - 0.4, x + s_ * hw + 0.4, y - hd, y + hd, 0.6, Hr, "metal_mat")        # side walls
        box(x - hw, x + hw, y - hd - 0.4, y - hd + 0.4, 0.6, Hr, "metal_mat")                   # front wall
        box(x - hw, x + hw, y + hd - 0.4, y + hd + 0.4, Hr - 2.0, Hr, "metal_mat")              # back lip
        box(x - hw, x + hw, y - hd, y - hd + 12, 0.6, 1.0, "metal_mat")                         # well floor
        ramp = math.degrees(math.atan((Hr - 2.6) / (D - 12)))
        rlen = math.hypot(D - 12, Hr - 2.6)
        rbevel(x, y - hd + 12 + (D - 12) / 2, 0.8 + (Hr - 2.6) / 2, W - 1, rlen, 0.4, "metal_mat", r=0.1, tilt_y=ramp)
        for k in range(7):                                                                      # ribs on the ramp
            t_ = (k + 1) / 8.0
            rbevel(x, y - hd + 12 + (D - 12) * t_, 1.1 + (Hr - 2.6) * t_, W - 4, 1.0, 0.5, "metal_mat", r=0.1, tilt_y=ramp)
        for s_ in (-1, 1):                                                                      # rolled rim
            tube((x + s_ * (hw + 0.9), y - hd - 0.9, Hr), (x + s_ * (hw + 0.9), y + hd + 0.9, Hr), 0.6, "metal_mat", sides=6)
        for yy in (y - hd - 0.9, y + hd + 0.9):
            tube((x - hw - 0.9, yy, Hr), (x + hw + 0.9, yy, Hr), 0.6, "metal_mat", sides=6)
        for dx in (-hw + 3, hw - 3):
            box(x + dx - 1, x + dx + 1, y + hd - 3, y + hd - 1, 0, 0.6, "metal_mat")             # feet
        box(x - hw + 0.5, x + hw - 0.5, y - hd + 0.5, y - hd + 11.5, 1.0, 3.2, "paint_white_mat")   # paint in the well
        # the roller lying across the ramp
        ry = y + 4
        rz = 0.8 + (Hr - 2.6) * ((4 + hd - 12) / (D - 12)) + 4.0
        tube((x - 11.5, ry, rz), (x + 11.5, ry, rz), 3.6, "roller_mat", sides=16)
        for ex in (-11.5, 11.5):
            sphere(x + ex, ry, rz, 3.6, "roller_mat", sides=12, scale=(0.25, 1, 1))
        tube((x + 11.5, ry, rz), (x + 14.5, ry, rz), 0.35, "metal_mat", sides=6)               # axle
        frame = [(x + 14.5, ry, rz), (x + 14.5, ry + 6, rz + 2), (x + 8, ry + 14, rz + 4.5), (x + 6, ry + 22, rz + 6.5)]
        for a_, b_ in zip(frame, frame[1:]):
            tube(a_, b_, 0.35, "metal_mat", sides=6)
        tube(frame[-1], (x + 3.5, ry + 36, rz + 9), 1.6, "grip_mat", sides=12)                  # plastic grip
        sphere(x + 3.5, ry + 36, rz + 9, 1.6, "grip_mat", sides=10)


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
    """A sheet thrown over furniture (w x d, h tall): flat on top with a 1.5 cm margin, folding
    exactly at the edges and falling to the floor in folds that only ever move outward, so it
    never cuts into what it covers."""
    rng = random.Random(seed)
    W2, D2, top = w / 2.0 + 1.5, d / 2.0 + 1.5, h + 1.2
    side = top - drop * 0.5

    def axis(half, n_top, n_side):
        a_ = [-half - side + side * k / n_side for k in range(n_side)]
        t_ = [-half + 2 * half * k / n_top for k in range(n_top + 1)]
        return a_ + t_ + [-v for v in reversed(a_)]
    us, vs = axis(W2, 12, 9), axis(D2, 20, 9)
    grid = []
    for sv in vs:
        row = []
        for su in us:
            ou, ov = max(0.0, abs(su) - W2), max(0.0, abs(sv) - D2)
            out = max(ou, ov)
            fold = abs(2.4 * math.sin(su * 0.31 + seed) * math.sin(sv * 0.23 + seed * 0.7)) + rng.uniform(0, 0.4)
            x = math.copysign(min(abs(su), W2) + ou * 0.22 + (fold if ou > 0 else 0), su)
            y = math.copysign(min(abs(sv), D2) + ov * 0.22 + (fold if ov > 0 else 0), sv)
            z = top - out if out > 0 else top + rng.uniform(0, 0.25)
            row.append((x, cy + y, z))
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
    """An upholstered motel armchair, facing -y before yaw, built as one solid piece like a
    real one: a boxed base with a short skirt, rolled arms that are part of the body, a seat
    cushion sitting down inside the arms with piping along its front, a back frame with a
    rolled top and a tufted back cushion resting on the seat, on four tapered wooden legs."""
    W, B0, B1 = 39.0, -37.0, 39.0                   # half width, front and back of the body
    with Moved(cx, cy, yaw):
        for x in (cx - W + 5, cx + W - 5):                                               # legs
            for y in (cy + B0 + 5, cy + B1 - 5):
                lathe(x, y, [(0, 1.5), (7, 2.0), (10, 2.4), (11, 2.8)], "wood_mat", sides=12)
        bevel_box(cx - W, cx + W, cy + B0, cy + B1, 11, 36, mat, r=3, seg=3)             # base
        bevel_box(cx - W - 0.6, cx + W + 0.6, cy + B0 - 0.6, cy + B1 + 0.6, 9.5, 15, mat, r=1, seg=2)   # skirt
        for k in range(1, 4):                                                            # skirt pleats
            xx = cx - W + k * W / 2.0
            box(xx - 0.3, xx + 0.3, cy + B0 - 0.9, cy + B0 - 0.6, 9.6, 14.6, "trim_mat")
        bevel_box(cx - W, cx + W, cy + B1 - 12, cy + B1, 11, 88, mat, r=5, seg=3)        # back frame
        tube((cx - W + 4, cy + B1 - 6, 87), (cx + W - 4, cy + B1 - 6, 87), 6.5, mat, sides=16)   # rolled top
        for s_ in (-1, 1):
            sphere(cx + s_ * (W - 4), cy + B1 - 6, 87, 6.5, mat, sides=16)
        for s_ in (-1, 1):                                                               # arms
            ax = cx + s_ * (W - 6)
            bevel_box(ax - 6, ax + 6, cy + B0, cy + B1 - 4, 11, 58, mat, r=3, seg=3)
            tube((ax, cy + B0 - 1, 58), (ax, cy + B1 - 8, 58), 7, mat, sides=16)       # rolled arm top
            sphere(ax, cy + B1 - 8, 58, 7, mat, sides=16)
        seat_y0, seat_y1 = cy + B0 - 2, cy + B1 - 11
        bevel_box(cx - W + 12.5, cx + W - 12.5, seat_y0, seat_y1, 36, 48, mat, r=4.5, seg=3)   # seat cushion
        tube((cx - W + 15, seat_y0 + 0.2, 46.3), (cx + W - 15, seat_y0 + 0.2, 46.3), 0.8, mat, sides=8)  # piping
        tube((cx - W + 15, seat_y0 + 0.2, 37.7), (cx + W - 15, seat_y0 + 0.2, 37.7), 0.8, mat, sides=8)
        rbevel(cx, cy + B1 - 17, 68, 2 * W - 25, 11, 40, mat, r=4.5, seg=3, tilt_y=8)    # back cushion
        for zz in (61, 75):                                                              # tufting buttons
            for k in range(3):
                yy = cy + B1 - 17 - 5.6 + (zz - 68) * 0.14
                sphere(cx - 13 + k * 13, yy, zz, 0.9, "trim_mat", sides=8)


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


def _sloped_body(x, y, z, w, d, hf, hb, r, mat):
    """A rounded block w x d whose top slopes from hf high at the front (-y) to hb at the back."""
    c = cmds.polyCube(w=w, h=1, d=d, sx=1, sy=1, sz=1, ch=False)[0]
    pts = []
    for vx, vy, vz in _verts(c):
        t = (vz + d / 2.0) / d
        pts.append((vx, 0.0 if vy < 0 else hf + (hb - hf) * t, vz))
    _set_verts(c, pts)
    _bevel(c, r, 3)
    cmds.move(x, z, y, c, relative=True)
    return keep(c, mat)


def coil_cord(path, coil_r=0.8, wire_r=0.22, pitch=0.6, mat="phone_mat"):
    """A coiled phone cord following a list of points: a helix of short tubes around the path."""
    pts = []
    for p0, p1 in zip(path, path[1:]):
        d = [p1[i] - p0[i] for i in range(3)]
        L = math.sqrt(sum(v * v for v in d)) or 0.01
        t = [v / L for v in d]
        up = (0, 0, 1) if abs(t[2]) < 0.9 else (1, 0, 0)
        u = (t[1] * up[2] - t[2] * up[1], t[2] * up[0] - t[0] * up[2], t[0] * up[1] - t[1] * up[0])
        ul = math.sqrt(sum(v * v for v in u)) or 1
        u = [v / ul for v in u]
        v_ = (t[1] * u[2] - t[2] * u[1], t[2] * u[0] - t[0] * u[2], t[0] * u[1] - t[1] * u[0])
        n = max(2, int(L / pitch * 6))
        for k in range(n):
            s_ = k / float(n)
            a = s_ * L / pitch * 2 * math.pi
            pts.append(tuple(p0[i] + d[i] * s_ + coil_r * (math.cos(a) * u[i] + math.sin(a) * v_[i]) for i in range(3)))
    for q0, q1 in zip(pts, pts[1:]):
        tube(q0, q1, wire_r, mat, sides=5)


def rotary_phone(x, y, z, yaw=0, handset=True):
    """A 1960s desk rotary phone (like the Western Electric 500), facing -y before yaw: a
    rounded body whose top slopes down to the front, a tilted finger-wheel dial with ten holes,
    a number card and a finger stop, the handset lying across the cradle on two raised
    shoulders with the hook-switch buttons between, a coiled cord out of the left end of the
    handset down to the body, rubber feet and the line cord running off the back."""
    W, D, HF, HB = 21.5, 23.0, 7.0, 10.5
    with Moved(x, y, yaw):
        bevel_box(x - W / 2 + 2.5, x + W / 2 - 2.5, y - D / 2 + 2.5, y + D / 2 - 2.5, z + 0.5, z + 1.6, "phone_dark_mat", r=0.5)
        for dx in (-W / 2 + 2.5, W / 2 - 2.5):
            for dy in (-D / 2 + 2.5, D / 2 - 2.5):
                frustum(x + dx, y + dy, z, z + 0.6, 1.1, 1.1, "phone_dark_mat", sides=8)       # feet
        _sloped_body(x, y, z + 1.4, W, D, HF, HB, 3.2, "phone_mat")
        # the dial on the front slope
        slope = (HB - HF) / D
        nl = math.sqrt(1 + slope * slope)
        n = (0, -slope / nl, 1 / nl)
        dy = -4.0
        top = z + 1.4 + HF + (HB - HF) * (dy + D / 2) / D - 0.2
        c0 = (x, y + dy, top)
        def on(r_, ang, h):
            # a point on the dial face: radius r_, angle ang (0 = +x), lifted h along the normal
            ux, uy = math.cos(ang) * r_, math.sin(ang) * r_ / nl
            return (c0[0] + ux + n[0] * h, c0[1] + uy + n[1] * h, c0[2] + math.sin(ang) * r_ * slope / nl + n[2] * h)
        tube(c0, tuple(c0[i] + n[i] * 0.5 for i in range(3)), 6.6, "phone_mat", sides=28)       # dial bezel
        tube(tuple(c0[i] + n[i] * 0.5 for i in range(3)), tuple(c0[i] + n[i] * 0.9 for i in range(3)), 6.0, "phone_dark_mat", sides=28)
        tube(tuple(c0[i] + n[i] * 0.9 for i in range(3)), tuple(c0[i] + n[i] * 1.2 for i in range(3)), 5.8, "plate_mat", sides=28)   # finger wheel
        for k in range(10):                                                                       # finger holes
            ang = math.radians(-60 - k * 28)
            tube(on(4.3, ang, 1.15), on(4.3, ang, 1.3), 0.85, "phone_dark_mat", sides=10)
        tube(tuple(c0[i] + n[i] * 1.2 for i in range(3)), tuple(c0[i] + n[i] * 1.35 for i in range(3)), 2.3, "paper_mat", sides=20)  # number card
        tube(on(6.3, math.radians(-40), 1.2), on(6.3, math.radians(-40), 2.2), 0.35, "plate_mat", sides=6)    # finger stop
        # cradle: raised shoulders at both ends, hook-switch buttons between
        hy, hz = y + 5.0, z + 1.4 + HF + (HB - HF) * (5.0 + D / 2) / D
        for s_ in (-1, 1):
            rbevel(x + s_ * 7.5, hy, hz + 0.6, 4.6, 7, 2.6, "phone_mat", r=1.2, seg=2)
            rbevel(x + s_ * 2.6, hy, hz + 0.4, 1.4, 2.2, 1.6, "plate_mat", r=0.4)
        if not handset:                                  # knocked off: the cradle is empty
            return
        # handset across the cradle: receiver and mouthpiece cups joined by a bent handle
        cz = hz + 3.6
        for s_ in (-1, 1):
            tube((x + s_ * 8.4, hy, cz - 1.8), (x + s_ * 8.4, hy, cz + 1.4), 3.0, "phone_mat", sides=20)
            sphere(x + s_ * 8.4, hy, cz - 1.8, 3.0, "phone_mat", sides=16, scale=(1, 1, 0.45))
            tube((x + s_ * 8.4, hy, cz + 1.4), (x + s_ * 5.6, hy, cz + 2.6), 1.9, "phone_mat", sides=14)
            sphere(x + s_ * 5.6, hy, cz + 2.6, 1.9, "phone_mat", sides=12)
        tube((x - 5.6, hy, cz + 2.6), (x + 5.6, hy, cz + 2.6), 1.9, "phone_mat", sides=14)
        # coiled cord from the left end of the handset, looping down to the body's left side
        coil_cord([(x - 11.2, hy, cz - 1.0), (x - 13.0, hy - 2, z + 4.5), (x - 13.2, hy - 7, z + 1.2),
                   (x - 12.0, y - 6, z + 0.9), (x - W / 2 + 0.3, y - 8.5, z + 2.2)])
        # line cord off the back
        tube((x + 4, y + D / 2 - 1, z + 1.2), (x + 6, y + D / 2 + 6, z + 0.25), 0.3, "phone_dark_mat", sides=6)
        tube((x + 6, y + D / 2 + 6, z + 0.25), (x + 9, y + D / 2 + 11, z + 0.25), 0.3, "phone_dark_mat", sides=6)


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
        rotary_phone(x0 + 164, BACK - 50, 60, yaw=-15)
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
    wx0, wx1 = x0 + 430, x1 - 30                         # the OPEN window
    nx0, nx1 = x0 + 215, x0 + 375                        # the second window, between the door and OPEN
    WZ0, WZ1 = 103, 242
    xs_ = [d1, nx0, nx1, wx0, wx1, x1]
    for k, (a_, b_) in enumerate(zip(xs_, xs_[1:])):
        if k in (1, 3):                                   # under and over a window
            box(a_, b_, y0, y0 + t, 0, WZ0, "plaster_mat")
            box(a_, b_, y0, y0 + t, WZ1, h, "plaster_mat")
        else:
            box(a_, b_, y0, y0 + t, 0, h, "plaster_mat")
    box(d0, d1, y0, y0 + t, dh, h, "plaster_mat")
    # the second window, outside: casing, sill, a mullion, glass
    box(nx0 - 8, nx1 + 8, y0 - 6, y0, 95, 103, "trim_mat")
    box(nx0 - 8, nx1 + 8, y0 - 6, y0, 242, 250, "trim_mat")
    for xx in (nx0 - 8, nx1):
        box(xx, xx + 8, y0 - 6, y0, 103, 242, "trim_mat")
    bevel_box((nx0 + nx1) / 2.0 - 2.5, (nx0 + nx1) / 2.0 + 2.5, y0 - 4, y0 + 1, 103, 242, "trim_mat", r=0.6)
    rbevel((nx0 + nx1) / 2.0, y0 - 9, 96.5, nx1 - nx0 + 30, 16, 4, "concrete_mat", r=1.0, tilt_y=-6)
    box(nx0, nx1, y0 + 2, y0 + 3, WZ0, WZ1, "seeglass_window_mat")
    for a, b in ((x0, d0 - 10), (d1 + 10, x1)):
        box(a, b, y0 - 3, y0, 0, 100, "brick_mat")
    box(x0 - 30, x1 + 30, y0 - 150, y1 + 30, h, h + 15, "roof_metal_mat")
    box(x0 - 30, x1 + 30, y0 - 158, y0 - 150, h - 25, h + 15, "trim_mat")
    tube((x0 - 30, y0 - 160, h - 21), (x1 + 30, y0 - 160, h - 21), 2.5, "glow_neon_red_mat")
    box(d0 - 10, d0, y0 - 5, y0, 0, dh + 8, "trim_mat")
    box(d1, d1 + 10, y0 - 5, y0, 0, dh + 8, "trim_mat")
    box(d0 - 10, d1 + 10, y0 - 5, y0, dh, dh + 8, "trim_mat")
    # front window (OPEN sign): a real opening now, you can see in and out
    box(wx0 - 8, wx1 + 8, y0 - 6, y0, 95, 103, "trim_mat")
    box(wx0 - 8, wx1 + 8, y0 - 6, y0, 242, 250, "trim_mat")
    neon_word("OPEN", wx1 - 30, y0 - 12, 150, 40, "glow_neon_red_mat", r=3.5)
    # an OFFICE sign over the door: a dark board on two brackets, red neon letters
    oc = (d0 + d1) / 2.0
    ow = (6 * 5.5 - 1.5) * (20 / 6.0)
    bevel_box(oc - ow / 2.0 - 12, oc + ow / 2.0 + 12, y0 - 9, y0 - 4, 248, 286, "metal_mat", r=1.2)
    for bx_ in (oc - ow / 2.0, oc + ow / 2.0):
        bevel_box(bx_ - 1.5, bx_ + 1.5, y0 - 4, y0, 262, 272, "metal_mat", r=0.5)
    # spaced by what each letter actually covers, so the narrow I doesn't leave a gap
    # (plain spacing read as "OFF ICE")
    u_ = 20 / 6.0
    ext = {"O": (0, 4), "F": (0, 4), "I": (1, 3), "C": (0, 4), "E": (0, 4)}
    tw = sum(b - a for a, b in (ext[c] for c in "OFFICE")) * u_ + 5 * 1.5 * u_
    cur = oc + tw / 2.0
    for ch in "OFFICE":
        a, b = ext[ch]
        neon_word(ch, cur + a * u_, y0 - 11, 257, 20, "glow_neon_red_mat", r=1.6)
        cur -= (b - a) * u_ + 1.5 * u_
    light("light_office_sign", oc, y0 - 60, 265, [1.0, 0.0, 0.0], 150, 300)
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
    lining("x", F + 0.5, L, R, 1, [(d0 - 10, d1 + 10, 0, dh + 8), (nx0 - 8, nx1 + 8, 99, 250), (wx0 - 8, wx1 + 8, 99, 250)])
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
    # the second window from inside: casing, sill, old blinds half down
    bevel_box(nx0 - 7, nx1 + 7, F, F + 9, 98, 103.5, "wood_mat", r=0.8)
    for a_, b_, c_, e_ in ((nx0 - 7, nx0, 103, 249), (nx1, nx1 + 7, 103, 249), (nx0 - 7, nx1 + 7, 242, 249)):
        bevel_box(a_, b_, F + 1, F + 3, c_, e_, "wood_mat", r=0.5)
    for k in range(10):
        rbevel((nx0 + nx1) / 2.0, F + 6, 236 - k * 5.2, nx1 - nx0 - 6, 4.5, 0.4, "plate_mat", r=0.1, tilt_y=25)
    rbevel((nx0 + nx1) / 2.0, F + 6, 184, nx1 - nx0 - 4, 5, 2.5, "plate_mat", r=0.5)
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
    bevel_box(KX0, KX1, P0 - 2.2, P0, 140, 215, "wood_mat", r=0.6)                      # board
    for a_, b_, c_, e_ in ((KX0 - 3, KX1 + 3, 212, 218), (KX0 - 3, KX1 + 3, 137, 143),
                           (KX0 - 3, KX0 + 3, 137, 218), (KX1 - 3, KX1 + 3, 137, 218)):
        bevel_box(a_, b_, P0 - 3.4, P0, c_, e_, "trim_mat", r=0.8)                     # moulded frame
    for k in range(6):
        kx = KX0 + 14 + k * 22.5
        bevel_box(kx - 7.5, kx + 7.5, P0 - 2.8, P0 - 2.2, 199.5, 207.5, "brass_mat", r=0.3)   # number plate
        room_no = 106 - k                                                  # +x is to your left here: 101 on the left
        block_word(str(room_no), kx + 4.5, P0 - 3.15, 201.6, 3.6, "trim_mat", 0.55, depth=0.5)
        tube((kx, P0 - 2.2, 192), (kx, P0 - 6.0, 192), 0.45, "brass_mat", sides=6)    # cup hook
        tube((kx, P0 - 6.0, 192), (kx, P0 - 6.0, 194.2), 0.45, "brass_mat", sides=6)
        sphere(kx, P0 - 6.0, 194.3, 0.5, "brass_mat", sides=6)
        if room_no != 104:                                                  # 104's hook is empty
            room_key(kx, P0 - 2.2, 192, ("book_red_mat", "book_green_mat", "book_brown_mat")[k % 3], k)
    bevel_box(KX0 + 30, KX1 - 30, P0 - 2.8, P0 - 2.2, 147, 156, "plate_mat", r=0.3)   # little card: "office" spares
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
    # the blanket: one draped cloth (like the rooms' bedspreads) over the bed and down both sides
    # and over the foot to the floor, turned back near the pillow. bedspread() lays a bed along y,
    # so it's built along y round the bed's centre and turned so its foot points to +x
    bcx, bcy = (bx0 + bx1) / 2.0 + 4, (by0 + by1) / 2.0
    hl, hw_ = (bx1 - bx0 - 8) / 2.0, (by1 - by0) / 2.0
    with Moved(bcx, bcy, 90):
        bedspread(bcx - hw_, bcx + hw_, bcy - hl, bcy + hl - 52, 55.8, seed=12, mat="blanket_mat", hang=48)
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
    FLX, FLY = bx0 + 28, by0 - 75                        # by the bed, clear of the calendar on the wall
    frustum(FLX, FLY, 6.8, 9, 17, 17, "brass_mat", sides=24)            # weighted base (on the rug)
    frustum(FLX, FLY, 9, 14, 16, 5, "brass_mat", sides=24)
    frustum(FLX, FLY, 14, 18, 3.2, 2.2, "brass_mat", sides=16)
    lathe(FLX, FLY, [(17, 1.6), (150, 1.4), (151, 2.4)], "brass_mat", sides=16)
    frustum(FLX, FLY, 140, 165, 20, 14, "glow_lamp_mat", sides=20, open_ends=True)
    frustum(FLX, FLY, 140.3, 164.7, 19.4, 13.4, "glow_lamp_mat", sides=20, open_ends=True, inside=True)
    light("light_office_back_lamp", FLX, FLY, 150, [1.0, 0.72, 0.45], 2.5, 380, room=True)
    # kitchenette on the right of the back wall: base cabinets, counter, hot plate with a pan,
    # a kettle, a shelf with cans and a box of crackers
    KX0, KX1 = R - 230, R - 120
    bevel_box(KX0, KX1, BY1 - 58, BY1, 5, 86, "wood_mat", r=1)
    for k in range(2):
        xx = KX0 + 3 + k * 54
        bevel_box(xx, xx + 50, BY1 - 59.5, BY1 - 58, 12, 82, "wood_mat", r=0.8)
        tube((xx + (44 if k == 0 else 6), BY1 - 60.5, 60), (xx + (44 if k == 0 else 6), BY1 - 60.5, 74), 0.7, "brass_mat", sides=6)
    bevel_box(KX0 - 2, KX1 + 2, BY1 - 62, BY1, 86, 90, "linoleum_mat", r=1)
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

def floor_suitcase(sx, sy, yaw):
    """A hard-shell suitcase lying open on the floor: the case (rounded shell, lining, a rim
    seal, latches, a carry handle, little feet) and its lid opened right back flat on the
    carpet toward -y (lining, two elastic straps with buckles, hinges along the fold), the
    clothes still folded inside."""
    def shell(y0, y1, top, floor):
        """An open hard shell: a rounded bottom, four walls, a fabric lining inside."""
        bevel_box(sx - 36, sx + 36, y0, y1, 0.6, floor, "suitcase_mat", r=2.5, seg=3)
        for a_, b_, c_, d_ in ((sx - 36, sx + 36, y0, y0 + 2.4), (sx - 36, sx + 36, y1 - 2.4, y1),
                               (sx - 36, sx - 33.6, y0, y1), (sx + 33.6, sx + 36, y0, y1)):
            bevel_box(a_, b_, c_, d_, 0.6, top, "suitcase_mat", r=1.1, seg=2)
        box(sx - 33.6, sx + 33.6, y0 + 2.4, y1 - 2.4, floor, floor + 0.4, "case_lining_mat")
        for a_, b_, c_, d_ in ((sx - 33.6, sx + 33.6, y0 + 2.4, y0 + 2.8), (sx - 33.6, sx + 33.6, y1 - 2.8, y1 - 2.4),
                               (sx - 33.6, sx - 33.2, y0 + 2.4, y1 - 2.4), (sx + 33.2, sx + 33.6, y0 + 2.4, y1 - 2.4)):
            box(a_, b_, c_, d_, floor, top - 0.6, "case_lining_mat")
    with Moved(sx, sy, yaw):
        shell(sy - 22, sy + 22, 17, 3.5)                                                          # the case
        for a_, b_, c_, d_ in ((sx - 36, sx + 36, sy - 22, sy - 21), (sx - 36, sx + 36, sy + 21, sy + 22)):
            box(a_, b_, c_, d_, 17, 17.5, "strap_mat")                                            # rim seal
        for dx in (-22, 22):
            bevel_box(sx + dx - 3, sx + dx + 3, sy + 21.8, sy + 23, 11, 16.5, "brass_mat", r=0.4)   # latches
        for dx in (-9, 9):
            bevel_box(sx + dx - 2, sx + dx + 2, sy + 21.8, sy + 24, 6.5, 10.5, "strap_mat", r=0.5)  # handle mounts
        tube((sx - 9, sy + 25.5, 8.5), (sx + 9, sy + 25.5, 8.5), 1.6, "strap_mat", sides=10)        # handle
        for dx in (-30, 30):
            for dy in (-16, 16):
                frustum(sx + dx, sy + dy, 0, 0.7, 1.8, 1.8, "strap_mat", sides=8)                   # feet
        # the lid, opened right back flat on the carpet toward -y
        shell(sy - 68, sy - 24, 11, 2.8)
        for dx in (-14, 14):
            box(sx + dx - 1.8, sx + dx + 1.8, sy - 65, sy - 27, 3.2, 3.6, "strap_mat")               # elastic straps
            bevel_box(sx + dx - 2.6, sx + dx + 2.6, sy - 47.5, sy - 44.5, 3.4, 4.6, "brass_mat", r=0.3)
        for dx in (-22, 22):
            tube((sx + dx - 5, sy - 23, 5), (sx + dx + 5, sy - 23, 5), 1.3, "metal_mat", sides=8)   # hinges
            bevel_box(sx + dx - 3, sx + dx + 3, sy - 69.2, sy - 68, 2, 6, "brass_mat", r=0.3)       # catches
        # inside: neatly folded clothes, two stacks and one on its own
        folded(sx - 21, sy, 3.9, 22, 34, "shirt_mat", "plain", 41)
        folded(sx - 21, sy + 0.5, 7.3, 21, 32, "sweater_mat", "plain", 42)
        folded(sx + 1, sy, 3.9, 21, 34, "clothes_b_mat", "jeans", 43)
        folded(sx + 22, sy, 3.9, 21, 34, "clothes_c_mat", "plain", 44)
        folded(sx + 22, sy - 0.5, 7.3, 20, 32, "sweater_red_mat", "plain", 45)


def dropped_jeans(cx, cy, yaw, seed=0):
    """A pair of jeans dropped on the floor: waistband, two legs splayed and creased, cuffs."""
    with Moved(cx, cy, yaw):
        rsoft(cx, cy + 22, 1.6, 36, 18, 3.2, "clothes_b_mat", jitter=0.6, sag=0.6, smooth=2, seed=seed, div=(5, 2, 3))
        rsoft(cx, cy + 30.5, 1.8, 36, 4.5, 3.0, "clothes_b_mat", jitter=0.3, smooth=2, seed=seed + 1)   # waistband
        sphere(cx, cy + 32.5, 3.3, 0.8, "brass_mat", sides=8)
        for side, ang in ((-1, 3), (1, -9)):
            rsoft(cx + side * 8, cy - 12, 1.3 + (side > 0) * 0.6, 16, 56, 2.6, "clothes_b_mat", jitter=0.7, sag=0.3, smooth=2,
                  seed=seed + 2 + side, div=(3, 2, 6), yaw=ang)
            for k in range(3):                                                                   # creases
                rsoft(cx + side * 8 + side * k * 1.5, cy - 2 - k * 15, 2.7, 15, 3, 1.4, "clothes_b_mat",
                      smooth=1, seed=seed + 10 + k, yaw=ang + 75)


def dropped_shirt(cx, cy, yaw, mat, seed=0):
    """A knit sweater dropped in a heap: a cloth sheet over the floor with soft folds and a
    raised ruck, the sleeves lying out to the sides."""
    rng = random.Random(seed)
    rows, cols, w, d = 14, 14, 50, 44
    grid = []
    for r_ in range(rows + 1):
        row = []
        for c_ in range(cols + 1):
            u, v = c_ / cols - 0.5, r_ / rows - 0.5
            edge = 1 - max(abs(u), abs(v)) * 2
            ruck = 3.0 * math.exp(-((u + 0.12) ** 2 + (v - 0.08) ** 2) * 14)
            folds = 1.1 * abs(math.sin(u * 11 + v * 5 + seed)) * max(0, edge)
            row.append((u * w + rng.uniform(-1, 1), cy + v * d + rng.uniform(-1, 1),
                        0.5 + max(0.0, ruck + folds) * min(1.0, edge * 3) + rng.uniform(0, 0.3)))
        grid.append(row)
    with Moved(cx, cy, yaw):
        _cloth(cx, grid, mat)
        for side in (-1, 1):                                    # sleeves running out from the shoulders
            rsoft(cx + side * 33, cy + 12 - side * 4, 1.2, 30, 9, 2.2, mat, jitter=0.4, smooth=2,
                  seed=seed + side, yaw=side * 18)
        rsoft(cx, cy + 20, 1.4, 16, 5, 2.4, mat, jitter=0.3, smooth=2, seed=seed + 7)        # neckline


def dropped_drawer(cx, cy, yaw, w=50.0, d=40.0, h=17.0, spill=True):
    """A drawer pulled out and dropped flat on the floor (front toward -y before yaw): front
    with a brass knob (or a bar handle when it is wide), sides, back, a thin bottom; papers and
    a pen spilled when spill."""
    hw, hd = w / 2.0, d / 2.0
    with Moved(cx, cy, yaw):
        bevel_box(cx - hw, cx + hw, cy - hd - 1, cy - hd + 1, 0, h, "wood_mat", r=0.8)          # front
        if w > 60:
            for dx in (-6, 6):
                box(cx + dx - 0.6, cx + dx + 0.6, cy - hd - 3, cy - hd - 1, h / 2 - 0.6, h / 2 + 0.6, "brass_mat")
            tube((cx - 7, cy - hd - 3.6, h / 2), (cx + 7, cy - hd - 3.6, h / 2), 0.8, "brass_mat", sides=6)
        else:
            sphere(cx, cy - hd - 1.8, h / 2, 1.6, "brass_mat", sides=8)
        for a_ in (cx - hw + 3, cx + hw - 4.5):
            bevel_box(a_, a_ + 1.5, cy - hd + 1, cy + hd, 0, h - 4, "wood_mat", r=0.4)        # sides
        bevel_box(cx - hw + 3, cx + hw - 3, cy + hd - 1.5, cy + hd, 0, h - 4, "wood_mat", r=0.4)   # back
        box(cx - hw + 4.5, cx + hw - 4.5, cy - hd + 1, cy + hd - 1.5, 0, 0.8, "trim_mat")        # bottom
        if spill:
            papers(cx - 4, cy + 2, 0.8, 2, 61)
            papers(cx - 2, cy - hd - 18, 0, 3, 62, spread=8)
            pen(cx + 22, cy - hd - 10, 0.5, 35)


def hanging_handset(x, y, z_top):
    """A phone handset hanging by its cord, mouthpiece end up: handle, both cups turned to -y."""
    zb = z_top - 21
    tube((x, y, zb + 3.5), (x, y, z_top - 3.5), 1.9, "phone_mat", sides=14)
    for zc, sgn in ((z_top - 1.5, 1), (zb + 1.5, -1)):
        tube((x, y, zc - sgn * 2.0), (x, y - 1.2, zc), 1.9, "phone_mat", sides=12)
        tube((x, y - 1.0, zc), (x, y - 4.2, zc), 3.0, "phone_mat", sides=20)                   # cup
        sphere(x, y - 4.2, zc, 3.0, "phone_mat", sides=16, scale=(1, 0.45, 1))


def bible(x, y, z, yaw):
    """A Bible lying face down: black leather covers a little bigger than the pages, a rounded
    spine with raised bands, gilt page edges, a red ribbon marker trailing out."""
    W, D, T = 15.0, 22.0, 4.2
    with Moved(x, y, yaw):
        bevel_box(x - W / 2, x + W / 2, y - D / 2, y + D / 2, z, z + 0.35, "dark_leather_mat", r=0.15)
        bevel_box(x - W / 2, x + W / 2, y - D / 2, y + D / 2, z + T - 0.35, z + T, "dark_leather_mat", r=0.15)
        box(x - W / 2 + 0.6, x + W / 2 - 0.35, y - D / 2 + 0.35, y + D / 2 - 0.35, z + 0.35, z + T - 0.35, "brass_mat")
        tube((x - W / 2 + 0.6, y - D / 2, z + T / 2), (x - W / 2 + 0.6, y + D / 2, z + T / 2), T / 2, "dark_leather_mat", sides=14)
        for k in range(4):
            yy = y - D / 2 + 3.5 + k * (D - 7) / 3.0
            tube((x - W / 2 + 0.6, yy - 0.3, z + T / 2), (x - W / 2 + 0.6, yy + 0.3, z + T / 2), T / 2 + 0.15,
                 "dark_leather_mat", sides=14)
        box(x + 1.5, x + 2.3, y - D / 2 - 7, y - D / 2 + 1, z + 0.02, z + 0.12, "red_string_mat")   # ribbon


def room_story(i, x0, x1):
    """Extra dressing for each room but 104 (index 3). Runs with IN_ROOM on."""
    t = 20
    L, R = x0 + t + 1, x1 - t - 1
    FI, BI = FRONT + t + 2, BACK - t - 1
    rng = random.Random(i * 13)
    if i == 0:      # 101: left in a hurry
        # a hard suitcase open on the floor at the foot of the bed, the lid flat on the carpet,
        # clothes still folded inside
        floor_suitcase(x0 + 300, BACK - 305, 8)
        # the nightstand drawer pulled out and dropped beside it (the nightstand is left with
        # a dark empty slot: room_inside(i=0) builds it without its drawer)
        dropped_drawer(x0 + 100, BACK - 75, 18)
        teddy(x0 + 300, FRONT + 230, 0, 160)
        # the room key on the carpet by the door
        ring(x0 + 230, FRONT + 120, 2.6, 1.6, 0.35, "brass_mat", sides=10)
        rbevel(x0 + 238, FRONT + 124, 2.6, 6, 1.4, 0.8, "brass_mat", r=0.2, yaw=20)
        rbevel(x0 + 222, FRONT + 112, 2.4, 5, 9, 0.8, "book_red_mat", r=0.6, yaw=40)
    elif i == 1:    # 102: barricaded, then broken in
        # the dresser was dragged to the door; its top drawer came out and lies on the floor
        with Moved(x0 + 48, FRONT + 285, -28, 70, -40):
            dropped_drawer(x0 + 120, FRONT + 330, 104, w=78, d=48, h=19, spill=False)
        # the phone knocked off the hook: base on the nightstand, the receiver hanging by its cord
        px, py = x0 + 163, BACK - 50
        rotary_phone(px, py, 60, yaw=0, handset=False)
        hx, hy = px - 6, BACK - 78
        coil_cord([(px - 10.4, py - 8.5, 62.2), (px - 9, BACK - 68.5, 61.2), (px - 8, BACK - 72.5, 58.5),
                   (px - 7, BACK - 75, 48), (hx, hy + 1, 36.5)])
        hanging_handset(hx, hy, 36)
        # a Bible face down on the bed
        bible(x0 + 340, BACK - 140, 58.6, 30)
    elif i == 2:    # 103: renovation stopped
        # the mattress leaning on the right wall
        rbevel(R - 30, FRONT + 330, 116, 22, 190, 230, "bed_mat", r=5, seg=3, tilt_x=6)   # clear of the bed
        dust_sheet(x0 + t + 29.5, FRONT + 285, 59, 171, 80, seed=7)                        # the dresser under a sheet
        bevel_box(x0 + 52, x0 + 98, BACK - 175, BACK - 135, 0, 52, "tv_mat", r=3)              # the TV on the floor, sheeted
        dust_sheet(x0 + 75, BACK - 155, 46, 40, 52, seed=8)
        step_ladder(x0 + 330, FRONT + 240, 20)
        for k in range(3):
            frustum(x0 + 270 + k * 25, BACK - 60, 0, 19, 9, 9, "paint_can_mat" if "paint_can_mat" in MATS else "metal_mat", sides=16)
            frustum(x0 + 270 + k * 25, BACK - 60, 19, 20, 8.5, 8.5, "metal_mat", sides=16)
        paint_tray(x0 + 150, BACK - 125, 190)                                               # clear of the bed frame and nightstand
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


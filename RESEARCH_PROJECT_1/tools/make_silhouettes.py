"""The three people in MARROW, as silhouettes (STORY.md: no faces, no photos). Drawn by hand in code
(user, 2026-11-17: "try without reference photos"); third pass. Style the user liked: flat black on an aged
photo print, grain, a white border; Eileen on a plain warm wall, Cas and Bug in front of a photo-booth curtain.

What makes a silhouette read as a real person (and what the earlier passes lacked):
  - a real head: a wide skull, the temples, cheekbones, the jaw angle and a narrower chin, ears where hair
    doesn't cover them, the head slightly turned and tilted (nobody sits dead symmetric in a photo booth)
  - a real neck and shoulders: the neck's sides, the long trapezius slope out to the shoulder, the rounded
    deltoid, and the arm falling away from it; one shoulder a little higher
  - background showing BETWEEN the parts (hair ends and shoulders, jaw and collar): the gaps carry the shape
  - edges that aren't smooth where real things aren't: loose strands at hair ends, cloth that sticks out
User notes kept from the roughs (2026-11-15): Eileen's hair is one full shoulder-length mass (no "dog ears");
Cas's ponytail is a real tail falling behind her shoulder (not a bun + ribbon); Bug has a real popped collar,
small tilted headphone cups and a short neck.

    python make_silhouettes.py  -> export/sil_eileen.png, sil_cas.png, sil_bug.png (660 x 860, bordered)
                                   + process/2026-11-17_silhouettes_v9.png (side by side)
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "export")
PROCESS = os.path.join(ROOT, "process")
S, W, H = 4, 600, 800
INK, LITE = 16, 50


def spline(pts, closed=True, steps=12):
    """Smooth curve through the points (Catmull-Rom), in 4x canvas pixels."""
    n = len(pts)
    out = []
    for i in (range(n) if closed else range(n - 1)):
        p0 = pts[(i - 1) % n] if closed else pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed else pts[min(i + 2, n - 1)]
        for k in range(steps):
            t = k / steps
            t2, t3 = t * t, t * t * t
            out.append(tuple(S * 0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                        + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append((pts[-1][0] * S, pts[-1][1] * S))
    return out


def fill(d, pts, val=INK):
    d.polygon(spline(pts), fill=val)


def line(d, pts, width=3, val=LITE):
    d.line(spline(pts, closed=False), fill=val, width=int(width * S), joint="curve")


def turn(pts, cx, cy, deg):
    """Rotate points round (cx, cy): the head's tilt."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def strands(d, base, direction, count, length, rng, width=3.0, spread=0.35):
    """Loose hair strands: thin tapering curves growing from points along `base` (a list of points),
    roughly along `direction` (dx, dy), each a little different."""
    for k in range(count):
        t = rng.random()
        i = min(int(t * (len(base) - 1)), len(base) - 2)
        f = t * (len(base) - 1) - i
        x = base[i][0] + (base[i + 1][0] - base[i][0]) * f
        y = base[i][1] + (base[i + 1][1] - base[i][1]) * f
        ang = math.atan2(direction[1], direction[0]) + rng.uniform(-spread, spread)
        L = length * rng.uniform(0.4, 1.0)
        bend = rng.uniform(-0.5, 0.5)
        pts = []
        for j in range(7):
            u = j / 6
            a2 = ang + bend * u
            pts.append((x + math.cos(a2) * L * u, y + math.sin(a2) * L * u))
        for j in range(6):                                   # taper: thick at the root, a hair at the tip
            wd = width * (1 - j / 6) + 0.6
            d.line([(pts[j][0] * S, pts[j][1] * S), (pts[j + 1][0] * S, pts[j + 1][1] * S)], fill=INK, width=max(1, int(wd * S)))


def head_outline(cx, top, chin, hw, ears=True):
    """A head seen from the front: wide rounded skull, temples, cheekbones, the jaw angle, a narrower chin
    (left side down, then the right side up). hw = half the skull's width."""
    h = chin - top
    left = [(cx - hw * 0.32, top + h * 0.012), (cx - hw * 0.6, top + h * 0.05), (cx - hw * 0.8, top + h * 0.11),
            (cx - hw * 0.93, top + h * 0.2), (cx - hw, top + h * 0.34),                          # a round dome
            (cx - hw * 0.96, top + h * 0.5), (cx - hw * 0.93, top + h * 0.6),            # temple / cheekbone
            (cx - hw * 0.84, top + h * 0.74), (cx - hw * 0.66, top + h * 0.86),            # jaw angle
            (cx - hw * 0.36, top + h * 0.96)]
    right = [(2 * cx - x, y) for x, y in reversed(left)]
    return [(cx, top)] + left + [(cx, chin)] + right


def ear(d, cx, y, side, hw, h):
    x = cx + side * (hw * 0.95)
    fill(d, [(x, y), (x + side * h * 0.08, y + h * 0.02), (x + side * h * 0.1, y + h * 0.1),
             (x + side * h * 0.06, y + h * 0.2), (x, y + h * 0.22)])


def shoulders(d, cx, neck_y, neck_hw, sh_y, sh_hw, tilt=0.0, boxy=0.0, drop=0.0):
    """Neck base, the trapezius slope, the deltoid and the arm falling to the bottom of the frame.
    tilt: px the right shoulder sits higher; boxy: 0 natural .. 1 padded coat; drop: a dropped,
    oversized jacket shoulder (px lower and wider)."""
    pts = []
    for side in (-1, 1):
        dy = -tilt if side > 0 else 0
        sy, sw = sh_y + dy + drop, sh_hw + drop * 0.6
        half = [(cx + side * neck_hw, neck_y),                                  # the neck's side
                (cx + side * (neck_hw + 26), neck_y + 16 + dy * 0.3),           # into the trapezius
                (cx + side * (sw * 0.58), sy - 6 - boxy * 8 + dy * 0.6),        # the long slope out
                (cx + side * (sw * 0.86), sy + 8 - boxy * 10),                  # top of the shoulder
                (cx + side * (sw * 0.98), sy + 36 - boxy * 14),                 # round over the deltoid
                (cx + side * (sw + 4), sy + 110),                               # the arm falls away
                (cx + side * (sw + 8), H + 20)]
        pts.append(half)
    outline = pts[0] + [(cx, H + 40)] + list(reversed(pts[1]))
    fill(d, outline)


def backdrop(base, curtain):
    img = Image.new("L", (W * S, H * S), base)
    d = ImageDraw.Draw(img)
    if curtain:
        for x in range(0, W * S, S):
            v = base + 24 * math.sin(x / (S * 36.0)) + 9 * math.sin(x / (S * 10.5))
            d.line([(x, 0), (x, H * S)], fill=int(v), width=S)
    glow = Image.new("L", img.size, 0)
    ImageDraw.Draw(glow).ellipse([-30 * S, -30 * S, 630 * S, 690 * S], fill=60)
    return Image.composite(Image.new("L", img.size, base + 55), img, glow.filter(ImageFilter.GaussianBlur(110 * S)))


def finish(img, name, tint, seed):
    img = img.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.8))
    rng = random.Random(seed)
    px = img.load()
    for y in range(H):
        for x in range(W):
            px[x, y] = max(0, min(255, px[x, y] + rng.randint(-13, 13)))
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-120, -80, W + 120, H + 120], fill=255)
    img = Image.composite(img, Image.new("L", (W, H), 40), vig.filter(ImageFilter.GaussianBlur(90)))
    frame = Image.new("L", (W + 60, H + 60), 236)
    frame.paste(img, (30, 30))
    r, g, b = tint
    out = Image.merge("RGB", [frame.point(lambda v: min(255, int(v * r))), frame.point(lambda v: min(255, int(v * g))),
                              frame.point(lambda v: min(255, int(v * b)))])
    os.makedirs(EXPORT, exist_ok=True)
    out.save(os.path.join(EXPORT, name))
    return out


def face_line(d, cx, top, chin, hw, tilt=0.0, pivot=None):
    """The faint grey outline of the face, done like Bug's (tools/make_bug_rough.py, the one the user liked,
    2026-11-17): just the lower curve of an oval round the face (cheeks, jaw and chin), no line across the
    brow. Same arc on all three so they match."""
    pivot = pivot or (cx, chin)
    h = chin - top
    ecx, ecy, rx, ry = cx, top + h * 0.53, hw * 0.9, h * 0.46            # Bug's: E(300, 318, 70, 90) on a 78 x 98 head
    pts = [(ecx + rx * math.cos(math.radians(a)), ecy + ry * math.sin(math.radians(a))) for a in range(-12, 193, 6)]
    line(d, turn(pts, pivot[0], pivot[1], tilt), 2.5)


def eileen():
    """1997, 48: tall and upright, head held level. Shoulder-length 90s hair with body and volume, ends
    turned under, one full mass from crown to shoulders. A long wool coat with padded shoulders, the
    collar turned up round her neck."""
    rng = random.Random(11)
    img = backdrop(150, curtain=False)
    d = ImageDraw.Draw(img)
    cx, top, chin, hw = 300, 214, 418, 74
    shoulders(d, cx, 470, 34, 548, 188, tilt=4, boxy=0.6)
    fill(d, [(cx - 34, 470), (cx - 32, 410), (cx + 32, 410), (cx + 34, 470)])                      # neck
    # the coat collar turned up: stiff wool standing on both sides of the neck, its points out past the jaw
    for s in (-1, 1):
        fill(d, [(cx + s * 30, 478), (cx + s * 34, 440), (cx + s * 58, 418), (cx + s * 84, 448), (cx + s * 92, 482),
                 (cx + s * 70, 500)])
    fill(d, head_outline(cx, top, chin, hw, ears=False))
    # the hair: rises in a full crown, out past the cheeks, falls to just above the shoulders where the
    # ends turn under and flick out; seen from the front it frames the face and closes against the collar
    hair_l = [(cx, top - 26), (cx - 50, top - 22), (cx - 92, top + 10), (cx - 112, top + 64), (cx - 116, top + 130),
              (cx - 112, top + 190), (cx - 114, top + 226), (cx - 132, top + 244), (cx - 116, top + 256),
              (cx - 86, top + 252), (cx - 52, top + 262)]                        # in to the back of the neck
    hair = hair_l + [(2 * cx - x, y) for x, y in reversed(hair_l)]
    hair = turn(hair, cx, top + 120, -2)
    fill(d, hair)
    face_line(d, cx, top, chin, hw)
    # lapels and buttons (no handbag strap, no wispy hair ends: user 2026-11-17)
    for s in (-1, 1):
        line(d, [(cx + s * 60, 500), (cx + s * 40, 560), (cx + s * 18, 660), (cx + s * 10, 800)], 2.5)
    for y in (600, 670, 740):                       # one straight column down the middle, where the coat closes
        d.ellipse([(cx - 6) * S, (y - 6) * S, (cx + 6) * S, (y + 6) * S], fill=LITE)
    return finish(img, "sil_eileen.png", (1.08, 1.0, 0.86), 1)


def cas():
    """2001: leaning in a little, head tipped. Long hair worn down (user, 2026-11-17: the ponytail versions
    didn't work), parted in the middle, falling past her shoulders.
    A hoodie under an open flannel (no backpack straps)."""
    rng = random.Random(22)
    img = backdrop(176, curtain=True)
    d = ImageDraw.Draw(img)
    cx, top, chin, hw = 300, 232, 426, 72
    shoulders(d, cx, 466, 32, 550, 180, tilt=-6)
    # the hood: a soft heavy roll behind and round the neck, standing up nearly to the ears
    # (no hood bunched round the neck: background shows behind her hair, user 2026-11-17)
    fill(d, [(cx - 30, 470), (cx - 30, 410), (cx + 30, 410), (cx + 30, 470)])                      # neck
    tilt = 3
    # long hair worn down (user, 2026-11-17: no ponytail): parted in the middle, over the ears, falling
    # straight past the jaw and in front of the shoulders to the chest; background shows in the two
    # triangles between the hair and the neck under the jaw
    hair_l = [(cx, top - 14), (cx - 46, top - 10), (cx - 80, top + 18), (cx - 92, top + 74), (cx - 96, top + 140),
              (cx - 100, top + 200), (cx - 108, top + 252), (cx - 118, top + 300), (cx - 124, top + 360),
              (cx - 120, top + 420), (cx - 86, top + 430),                       # the ends, over the chest
              (cx - 78, top + 360), (cx - 70, top + 290), (cx - 64, top + 230),  # its inner edge, up past the neck
              (cx - 58, top + 180), (cx - 52, top + 130), (cx - 30, top + 60), (cx - 6, top + 34)]   # to the parting
    hair = hair_l + [(2 * cx - x, y - (4 if y > top + 250 else 0)) for x, y in reversed(hair_l)]
    hd = turn(head_outline(cx, top, chin, hw), cx, chin, tilt)
    fill(d, hd)
    fill(d, turn(hair, cx, chin, tilt))
    # the hair at the back fills in behind her neck, so no neck shows, just hair down to her shoulders
    # (user, 2026-11-17: "I don't want to see Cas's neck, I want that to be hair")
    fill(d, turn([(cx - 60, top + 130), (cx - 66, top + 210), (cx - 72, top + 300), (cx - 76, top + 380), (cx, top + 392),
                  (cx + 76, top + 376), (cx + 72, top + 296), (cx + 66, top + 206), (cx + 60, top + 126), (cx, top + 120)],
                 cx, chin, tilt))
    # faint grey lines so the shapes read (user, 2026-11-17): where her face meets her hair, the parting,
    # strands falling down the hair, and her shoulders under it
    face_line(d, cx, top, chin, hw, tilt)
    line(d, turn([(cx, top - 12), (cx + 1, top + 18)], cx, chin, tilt), 2)                     # the parting
    for s_ in (-1, 1):
        for k, off in enumerate((84, 102)):                                                     # strands falling
            line(d, turn([(cx + s_ * (off - 6), top + 120), (cx + s_ * (off - 2), top + 220),
                          (cx + s_ * (off + 6), top + 320), (cx + s_ * (off + 4), top + 400)], cx, chin, tilt), 1.8)
        line(d, [(cx + s_ * 60, top + 312), (cx + s_ * 130, top + 336), (cx + s_ * 172, top + 360)], 2.5)  # shoulder under the hair
    for s_ in (-1, 1):                                                     # loose strands at the ends and sides
        ends = turn([(cx + s_ * 122, top + 418), (cx + s_ * 88, top + 428)], cx, chin, tilt)
        strands(d, ends, (s_ * 0.1, 1), 12, 24, rng, width=2.2, spread=0.35)
        side = turn([(cx + s_ * 100, top + 200), (cx + s_ * 122, top + 340)], cx, chin, tilt)
        strands(d, side, (s_ * 1, 0.4), 5, 12, rng, width=1.2, spread=0.5)
    strands(d, turn([(cx - 40, top - 8), (cx + 40, top - 8)], cx, chin, tilt), (0, -1), 6, 7, rng, width=1.2, spread=1.1)
    # flannel collar points lying open, the flannel's open front (no backpack straps: user 2026-11-17)
    for s in (-1, 1):
        fill(d, [(cx + s * 40, 506), (cx + s * 74, 494), (cx + s * 92, 520), (cx + s * 60, 540)])
        line(d, [(cx + s * 46, 528), (cx + s * 58, 640), (cx + s * 66, 800)], 2.5)
    for s in (-1, 1):
        line(d, [(cx + s * 12, 524), (cx + s * 14, 588)], 2)                                        # hood strings
    return finish(img, "sil_cas.png", (1.02, 1.0, 0.95), 2)


def bug():
    """Bug: the ORIGINAL rough from 2026-11-15 (tools/make_bug_rough.py), unchanged. The user compared it
    with the redrawn versions on 2026-11-17 and liked the original more."""
    # ... minus the collar (2026-11-17): tools/make_bug_rough.py with COLLAR = False
    out = Image.open(os.path.join(PROCESS, "2026-11-17_bug_silhouette_no_collar.png")).convert("RGB")
    out.save(os.path.join(EXPORT, "sil_bug.png"))
    return out


if __name__ == "__main__":
    ims = [eileen(), cas(), bug()]
    sheet = Image.new("RGB", (sum(i.width for i in ims) + 40, ims[0].height + 20), (40, 36, 32))
    x = 10
    for i in ims:
        sheet.paste(i, (x, 10))
        x += i.width + 10
    sheet.save(os.path.join(PROCESS, "2026-11-17_silhouettes_v9.png"))
    print("silhouettes v9 written")

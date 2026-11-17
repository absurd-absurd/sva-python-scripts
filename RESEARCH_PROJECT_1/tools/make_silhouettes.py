"""The three people in MARROW, as silhouettes (STORY.md: no faces, no photos). Second pass, 2026-11-17,
replacing the straight-edged roughs (tools/make_silhouettes_rough.py, tools/make_bug_rough.py) with smooth
curves and realistic proportions, keeping the style the user liked: flat black on an aged photo print,
grain, a white border; Eileen on a plain warm wall, Cas and Bug in front of a photo-booth curtain.

User notes on the roughs (2026-11-15), fixed here:
  Eileen: the hair read as dog ears / pigtails  -> one full shoulder-length 90s mass, closed to the neck
  Cas:    head 'not working', ponytail looked like a bun + ribbon -> a real high ponytail falling behind
          the right shoulder, hood bunched at the neck, open flannel, backpack straps
  Bug:    grey triangles -> a real popped jacket collar; smaller, tilted headphone cups; a shorter neck

    python make_silhouettes.py  -> export/sil_eileen.png, sil_cas.png, sil_bug.png (660 x 860, bordered)
                                   + process/2026-11-17_silhouettes_v2.png (side by side)
Each figure is a closed Catmull-Rom spline through hand-placed points (a 600 x 800 frame), mirrored
where the body is symmetric, drawn 4x and shrunk for clean edges.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "export")
PROCESS = os.path.join(ROOT, "process")
S, W, H = 4, 600, 800
INK, LITE = 16, 52                       # the figure, and the faint lines that show folds and straps


def spline(pts, closed=True, steps=14):
    """Smooth closed curve through the points (Catmull-Rom), scaled to the 4x canvas."""
    n = len(pts)
    out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0, p1 = pts[(i - 1) % n], pts[i]
        p2, p3 = pts[(i + 1) % n], pts[(i + 2) % n]
        if not closed:
            p0 = pts[max(i - 1, 0)]
            p3 = pts[min(i + 2, n - 1)]
        for k in range(steps):
            t = k / steps
            t2, t3 = t * t, t * t * t
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x * S, y * S))
    if not closed:
        out.append((pts[-1][0] * S, pts[-1][1] * S))
    return out


def mirror(half, cx=300):
    """Points down one side (left, top to bottom) -> the whole closed outline, both sides."""
    right = [(2 * cx - x, y) for x, y in reversed(half)]
    return half + right


def backdrop(base, curtain):
    img = Image.new("L", (W * S, H * S), base)
    d = ImageDraw.Draw(img)
    if curtain:                                                   # the booth curtain's folds
        for x in range(0, W * S, S):
            v = base + 24 * math.sin(x / (S * 36.0)) + 9 * math.sin(x / (S * 10.5))
            d.line([(x, 0), (x, H * S)], fill=int(v), width=S)
    glow = Image.new("L", img.size, 0)
    ImageDraw.Draw(glow).ellipse([-30 * S, -30 * S, 630 * S, 690 * S], fill=60)
    return Image.composite(Image.new("L", img.size, base + 55), img, glow.filter(ImageFilter.GaussianBlur(110 * S)))


def finish(img, name, tint, seed):
    """Shrink, soften a touch, grain, vignette, white photo border, tint; save to export/."""
    img = img.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.9))
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


def line(d, pts, width=3, closed=False):
    d.line(spline(pts, closed=closed), fill=LITE, width=width * S, joint="curve")


# a realistic head (front view, slightly narrower jaw) centred on cx; crown at top, chin at chin
def head(cx, top, chin, half_w):
    h = chin - top
    half = [(cx, top), (cx - half_w * 0.62, top + h * 0.06), (cx - half_w * 0.95, top + h * 0.3),
            (cx - half_w, top + h * 0.52), (cx - half_w * 0.9, top + h * 0.72), (cx - half_w * 0.62, top + h * 0.9),
            (cx - half_w * 0.25, top + h * 0.99)]
    right = [(2 * cx - x, y) for x, y in reversed(half[1:])]     # back up the other side (no slit down the middle)
    return half + [(cx, chin)] + right


def eileen():
    """1997, 48: shoulder-length voluminous 90s hair (one mass, closed to the neck), a long wool coat
    with the collar turned up, a handbag strap over the left shoulder. Tall and upright."""
    img = backdrop(150, curtain=False)
    d = ImageDraw.Draw(img)
    # coat: square shoulders, collar up round the neck, arms down the sides
    coat = mirror([(266, 452), (240, 470), (190, 492), (130, 512), (100, 548), (88, 640), (82, 800)])
    d.polygon(spline(coat), fill=INK)
    d.polygon(spline([(300, 440), (262, 446), (258, 480), (300, 500), (342, 480), (338, 446)]), fill=INK)   # neck
    d.polygon(spline(head(300, 252, 440, 72)), fill=INK)
    # the hair: full and round over the crown, out past the cheeks, down to the shoulders with the
    # ends turned under; its inner edge runs down to the collar, so there's no gap at the neck
    hair = mirror([(300, 222), (232, 230), (192, 266), (178, 330), (180, 392), (188, 432), (180, 452),
                   (170, 466), (190, 474), (220, 462), (246, 448), (262, 436)])     # ends flip out above the shoulders
    d.polygon(spline(hair), fill=INK)
    # collar points standing up, lapels, buttons and the handbag strap in faint lines
    for s in (-1, 1):
        d.polygon(spline([(300 + s * 40, 448), (300 + s * 70, 420), (300 + s * 96, 470), (300 + s * 70, 520)]), fill=INK)
        line(d, [(300 + s * 70, 422), (300 + s * 92, 470), (300 + s * 60, 530), (300 + s * 22, 640)])
    for y in (600, 690):
        d.ellipse([(300 - 7) * S, (y - 7) * S, (300 + 7) * S, (y + 7) * S], fill=LITE)
    line(d, [(190, 500), (240, 600), (320, 720), (380, 800)], width=4)
    return finish(img, "sil_eileen.png", (1.08, 1.0, 0.86), 1)


def cas():
    """2001: a high ponytail falling behind her right shoulder (no beanie), a hoodie with the hood
    bunched round her neck under an open flannel, backpack straps, the head tipped a little forward."""
    img = backdrop(176, curtain=True)
    d = ImageDraw.Draw(img)
    body = mirror([(262, 470), (236, 488), (186, 506), (128, 526), (102, 566), (92, 660), (88, 800)])
    d.polygon(spline(body), fill=INK)
    hood = mirror([(300, 446), (250, 448), (214, 470), (208, 500), (232, 520), (300, 528)])
    d.polygon(spline(hood), fill=INK)
    d.polygon(spline([(300, 430), (266, 438), (264, 480), (300, 490), (336, 480), (334, 438)]), fill=INK)   # neck
    hd = [(x + (y - 250) * 0.05, y) for x, y in head(300, 256, 436, 70)]               # tipped forward a touch
    d.polygon(spline(hd), fill=INK)
    # hair pulled back tight: just a little fuller than the skull at the crown
    d.polygon(spline(mirror([(300, 248), (246, 256), (230, 290), (228, 330), (238, 330), (250, 290), (300, 270)])), fill=INK)
    # the ponytail: tied high at the back of the crown, arcing out to her right, falling behind the
    # shoulder and narrowing to the tips
    tail = [(318, 250), (350, 236), (392, 246), (418, 284), (426, 350), (422, 420), (412, 480), (402, 530),
            (394, 558), (388, 522), (394, 450), (398, 380), (396, 322), (384, 292), (356, 274), (330, 268)]
    d.polygon(spline(tail), fill=INK)
    d.polygon(spline([(316, 248), (338, 238), (350, 252), (330, 264)]), fill=INK)     # the hair tie bump
    for sx in (-1, 1):                                                               # ears: her hair's pulled back
        ex = 300 + sx * 71 + (346 - 250) * 0.05
        d.ellipse([(ex - 9) * S, 328 * S, (ex + 9) * S, 366 * S], fill=INK)
    # open flannel edges, hood strings, backpack straps over the shoulders, in faint lines
    for s in (-1, 1):
        line(d, [(300 + s * 40, 528), (300 + s * 56, 620), (300 + s * 64, 800)])
        line(d, [(300 + s * 14, 520), (300 + s * 16, 580)], width=2)
        line(d, [(300 + s * 112, 524), (300 + s * 122, 640), (300 + s * 124, 800)], width=4)
        line(d, [(300 + s * 146, 528), (300 + s * 154, 640), (300 + s * 156, 800)], width=4)
    return finish(img, "sil_cas.png", (1.02, 1.0, 0.95), 2)


def bug():
    """2002: a short bob with bangs, an oversized jacket with a real popped collar, headphones round
    her neck (small cups, tilted), a short neck."""
    img = backdrop(170, curtain=True)
    d = ImageDraw.Draw(img)
    jacket = mirror([(262, 456), (230, 472), (172, 496), (112, 520), (82, 566), (70, 660), (62, 800)])
    d.polygon(spline(jacket), fill=INK)
    d.polygon(spline([(300, 424), (268, 430), (266, 462), (300, 474), (334, 462), (332, 430)]), fill=INK)  # short neck
    d.polygon(spline(head(300, 262, 432, 70)), fill=INK)
    # the bob: full over the crown, straight bangs across the brow, the sides falling to the jaw
    # and turning in under it
    bob = mirror([(300, 236), (236, 244), (206, 284), (196, 340), (198, 392), (210, 420), (236, 428),
                  (254, 412)])
    d.polygon(spline(bob), fill=INK)
    line(d, [(244, 318), (300, 322), (356, 318)], width=2)                             # where the bangs end
    # the popped collar: two stiff points standing up and out on each side of the neck
    for s in (-1, 1):
        d.polygon(spline([(300 + s * 34, 470), (300 + s * 42, 430), (300 + s * 74, 412), (300 + s * 96, 452),
                          (300 + s * 84, 486)]), fill=INK)
        line(d, [(300 + s * 44, 432), (300 + s * 74, 414), (300 + s * 94, 452)], width=2)
    # headphones round her neck: the band behind, two small cups tipped toward each other
    for s, tilt in ((-1, 18), (1, -18)):
        cx, cy = 300 + s * 60, 478
        cup = Image.new("L", (90 * S, 70 * S), 0)
        cd = ImageDraw.Draw(cup)
        cd.ellipse([8 * S, 6 * S, 82 * S, 64 * S], fill=255)
        cup = cup.rotate(tilt, resample=Image.BICUBIC, expand=False)
        img.paste(INK, (int((cx - 45) * S), int((cy - 35) * S)), cup)
        ring = Image.new("L", cup.size, 0)
        ImageDraw.Draw(ring).ellipse([14 * S, 12 * S, 76 * S, 58 * S], outline=255, width=3 * S)
        ring = ring.rotate(tilt, resample=Image.BICUBIC, expand=False)
        img.paste(LITE, (int((cx - 45) * S), int((cy - 35) * S)), ring)
    line(d, [(244, 470), (270, 494), (300, 500), (330, 494), (356, 470)], width=3)     # the band
    line(d, [(300, 520), (300, 800)], width=2)                                          # the zip
    return finish(img, "sil_bug.png", (1.04, 1.0, 0.92), 3)


if __name__ == "__main__":
    ims = [eileen(), cas(), bug()]
    sheet = Image.new("RGB", (sum(i.width for i in ims) + 40, ims[0].height + 20), (40, 36, 32))
    x = 10
    for i in ims:
        sheet.paste(i, (x, 10))
        x += i.width + 10
    sheet.save(os.path.join(PROCESS, "2026-11-17_silhouettes_v2.png"))
    print("silhouettes v2 written")

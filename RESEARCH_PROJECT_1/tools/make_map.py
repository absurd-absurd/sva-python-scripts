"""Draw the in-game map of Marrow Falls: the map Cas drew for Bug, by hand on a sketchbook page.

    python make_map.py            -> export/map.png (2048 x 2048) + export/map_marker.png,
                                     + export/map_full.png (torn paper, for the M screen);
                                     then unreal/import_map.py brings them into Unreal

Everything on it comes from the same data the level is built from:
  layout.json     trail, woods area, clearings (tower, cabins) and the map's world bounds
  export/scatter.json   every tree/rock the Maya scatter tool placed (small ink marks)
  export/fill.json      the forest filling the ground round the motel (tools/make_fill.py)
  the motel/office/road numbers below match blockout.py and maya/make_motel.py
Drawn like the hand-drawn hiking maps the user gave as reference: black felt-tip on a cream
sketchbook page, the trail as one wobbly line, landmarks boxed or ringed with their names, notes
in her handwriting with arrows, a title box, a north arrow and a note box; folded in four, torn out.

North (the lake, +Y) is up. Seen facing north, Unreal's +X is to the LEFT (west), so the
map flips X: u = (x_max - x) / size. The HUD uses the same bounds to put you on it.
Needs Pillow (python -m pip install pillow) and the Ink Free font that comes with Windows.
"""
import json
import math
import os
import random

import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tower_view import in_view                     # trees cut for the lookout's view aren't drawn

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LAYOUT = json.load(open(os.path.join(ROOT, "layout.json")))
SCATTER = os.path.join(ROOT, "export", "scatter.json")
OUT = os.path.join(ROOT, "export", "map.png")
MARKER = os.path.join(ROOT, "export", "map_marker.png")
FULL = os.path.join(ROOT, "export", "map_full.png")      # the torn-paper version for the M screen
FRAME = os.path.join(ROOT, "export", "map_frame.png")    # torn paper edge laid round the corner map
FRAME_HOLE = 0.08                                        # the hole (where the map shows) starts this far in, each side
B = LAYOUT["map"]                                   # world bounds of the picture (square)
PX = B["px"]
FONT = r"C:/Windows/Fonts/Inkfree.ttf"

PAPER = (238, 230, 205)
INK = (24, 22, 26)            # black felt-tip
HAND = r"C:/Windows/Fonts/Inkfree.ttf"

rng = random.Random(7)


def to_px(x, y):
    size = B["x_max"] - B["x_min"]
    return ((B["x_max"] - x) / size * PX, (B["y_max"] - y) / size * PX)


def cm(d):
    return d / (B["x_max"] - B["x_min"]) * PX


def font(size, f=HAND):
    return ImageFont.truetype(f, int(size))


def wobble(pts, amp=2.2, step=12):
    out = []
    for (a, b), (c, e) in zip(pts, pts[1:]):
        n = max(1, int(math.dist((a, b), (c, e)) / step))
        for k in range(n):
            t = k / n
            out.append((a + (c - a) * t + rng.uniform(-amp, amp), b + (e - b) * t + rng.uniform(-amp, amp)))
    out.append(pts[-1])
    return out


def pen(d, pts, width=5, amp=2.2):
    d.line(wobble(pts, amp), fill=INK, width=width, joint="curve")


def write_px(text, px_, py_, size=44, anchor="mm", tilt=0.0, lines=None):
    """Handwriting (several lines when text has '\n'), optionally tilted."""
    fnt = font(size)
    dd = ImageDraw.Draw(IMG)
    l, t, r, b = dd.multiline_textbbox((0, 0), text, font=fnt, spacing=size * 0.15, align="left")
    w, h = int(r - l + 24), int(b - t + 24)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(layer).multiline_text((12 - l, 12 - t), text, font=fnt, fill=INK + (255,), spacing=size * 0.15, align="left")
    if tilt:
        layer = layer.rotate(tilt, expand=True, resample=Image.BICUBIC)
    ox = {"m": layer.width / 2, "l": 0, "r": layer.width}[anchor[0]]
    oy = {"m": layer.height / 2, "t": 0, "b": layer.height}[anchor[1]]
    IMG.paste(layer, (int(px_ - ox), int(py_ - oy)), layer)
    return (px_ - ox, py_ - oy, px_ - ox + layer.width, py_ - oy + layer.height)


def write(d, text, x, y, size=44, anchor="mm", tilt=0.0):
    px_, py_ = to_px(x, y)
    return write_px(text, px_, py_, size, anchor, tilt)


def boxed(d, text, x, y, size=40, tilt=0.0):
    """A label with a hand-drawn box round it (like 'Big Rock' on her reference maps)."""
    l, t, r, b = write(d, text, x, y, size, tilt=tilt)
    pen(d, [(l + 2, t + 4), (r - 2, t + 1), (r + 1, b - 3), (l - 1, b), (l + 6, t + 2)], width=4)


def ringed(d, text, x, y, size=36, rx=None):
    """A label inside a wobbly oval: a building or landmark."""
    l, t, r, b = write(d, text, x, y, size)
    cx, cy = (l + r) / 2, (t + b) / 2
    rx = rx or (r - l) / 2 + 14
    ry = (b - t) / 2 + 14
    a0 = rng.uniform(0, 6.28)
    pts = [(cx + rx * math.cos(a0 + 2 * math.pi * 1.06 * k / 36) + rng.uniform(-2, 2),
            cy + ry * math.sin(a0 + 2 * math.pi * 1.06 * k / 36) + rng.uniform(-2, 2)) for k in range(37)]
    d.line(pts, fill=INK, width=4, joint="curve")


def note(d, text, at_px, to_world, size=36, tilt=0.0):
    """A note in her handwriting with a curvy arrow to what it's about."""
    l, t, r, b = write_px(text, at_px[0], at_px[1], size, tilt=tilt)
    tx, ty = to_px(*to_world)
    sx = r + 6 if tx > r else (l - 6 if tx < l else (l + r) / 2)
    sy = (t + b) / 2 if (tx > r or tx < l) else (b + 6 if ty > b else t - 6)
    mx, my = (sx + tx) / 2 + (ty - sy) * 0.2, (sy + ty) / 2 - (tx - sx) * 0.2
    pts = [((1 - u) ** 2 * sx + 2 * (1 - u) * u * mx + u * u * tx, (1 - u) ** 2 * sy + 2 * (1 - u) * u * my + u * u * ty)
           for u in [k / 14 for k in range(15)]]
    pen(d, pts, width=4, amp=1.2)
    ang = math.atan2(ty - pts[-3][1], tx - pts[-3][0])
    for s in (-1, 1):
        d.line([(tx, ty), (tx - 24 * math.cos(ang + s * 0.45), ty - 24 * math.sin(ang + s * 0.45))], fill=INK, width=4)


def paper():
    """A sketchbook page: cream, faint tooth, folded in four, a little grubby."""
    img = Image.new("RGB", (PX, PX), PAPER)
    d = ImageDraw.Draw(img)
    for _ in range(9000):
        x, y = rng.randrange(PX), rng.randrange(PX)
        v = rng.randint(-14, 8)
        d.point((x, y), fill=tuple(max(0, min(255, c + v)) for c in PAPER))
    stains = Image.new("L", (PX, PX), 0)
    sd = ImageDraw.Draw(stains)
    for _ in range(4):
        cx, cy, r = rng.randrange(PX), rng.randrange(PX), rng.randint(120, 320)
        sd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rng.randint(8, 18))
    stains = stains.filter(ImageFilter.GaussianBlur(60))
    img = Image.composite(Image.new("RGB", (PX, PX), (200, 184, 150)), img, stains)
    d = ImageDraw.Draw(img)
    for vertical in (True, False):
        o = PX * 0.5 + rng.uniform(-6, 6)
        a, b = ((o, 0), (o, PX)) if vertical else ((0, o), (PX, o))
        d.line([a, b], fill=(214, 204, 178), width=4)
        d.line([(a[0] + (3 if vertical else 0), a[1] + (0 if vertical else 3)), (b[0] + (3 if vertical else 0), b[1] + (0 if vertical else 3))],
               fill=(246, 241, 224), width=2)
    return img


def lake(d):
    pts = []
    for i in range(41):
        x = B["x_min"] + 250 + (B["x_max"] - B["x_min"] - 500) * i / 40
        pts.append(to_px(x, 14500 + 250 * math.sin(x / 1700.0) + rng.uniform(-60, 60)))
    pen(d, pts, width=6)
    for k in range(9):                                       # a few little wave squiggles
        x0, y0 = rng.uniform(120, PX - 300), rng.uniform(to_px(0, 19500)[1], to_px(0, 15300)[1])
        if (150 < x0 < 950 and 150 < y0 < 340) or (560 < x0 < 1420 and y0 < 210) or (PX - 470 < x0 < PX - 160 and y0 < 420):   # clear of the lake's name, the title and the north arrow
            continue
        d.line([(x0 + j * 16, y0 + 7 * math.sin(j * 1.6)) for j in range(8)], fill=INK, width=3)
    write(d, "BLACK HOLLOW\n     LAKE", 6300, 16900, 62, tilt=-2)


def tree(d, px_, py_, s):
    d.line([(px_, py_ + s * 1.2), (px_, py_ - s)], fill=INK, width=3)
    for k in range(3):
        y = py_ - s + k * s * 0.6
        w = s * (0.35 + k * 0.25)
        d.line([(px_ - w, y + s * 0.5), (px_, y), (px_ + w, y + s * 0.5)], fill=INK, width=3)


def trees(d):
    """Only a few doodled pines, in little groups by the trail - like her saguaros."""
    for x, y in ((-5200, 1800),(2200, 6600), (-2200, 9600), (2600, 12200), (-1500, 4300), (5200, 9000), (-6800, 7000)):
        for k in range(rng.choice((2, 3))):
            px_, py_ = to_px(x + rng.uniform(-400, 400), y + rng.uniform(-300, 300))
            tree(d, px_, py_, rng.uniform(20, 28))


def near_trail(x, y, clear):
    return False


def trail(d):
    pts = [to_px(x, y) for x, y in LAYOUT["trail"]]
    pen(d, wobble(pts, 3.0, 20), width=6)
    note(d, "trail starts\nbehind the motel", (to_px(3200, 1500)[0], to_px(3200, 1500)[1]), (-2900, 250), 38, tilt=3)
    note(d, "follow the red\nlanterns all the\nway down", (to_px(-6600, 3700)[0], to_px(-6600, 3700)[1]), (-1150, 1650), 36, tilt=-3)
    write(d, "steep", 1500, 7600, 34, tilt=60)


def town(d):
    for y in (-4060, -4940):                                 # the road
        pen(d, [to_px(B["x_max"] - 150, y), to_px(B["x_min"] + 150, y)], width=5)
    write(d, "old lake road", -7600, -4500, 42)
    write(d, "<- road closed", 6200, -4500, 34)
    # the motel: one long box of rooms with 104 marked, the office as its own box
    (a, b), (c, e) = to_px(500, -1400), to_px(-2500, -700)
    pen(d, [(a, b), (c, b), (c, e), (a, e), (a, b)], width=5)
    for i in range(1, 6):
        x = -2500 + i * 500
        pen(d, [to_px(x, -1400), to_px(x, -700)], width=3)
    px_, py_ = to_px(-750, -1050)
    d.text((px_, py_), "X", font=font(46), fill=INK, anchor="mm")
    boxed(d, "MOTEL", -1000, -2300, 50)
    (a, b), (c, e) = to_px(3750, -1750), to_px(3050, -850)
    pen(d, [(a, b), (c, b), (c, e), (a, e), (a, b)], width=5)
    write(d, "office", 3400, -2300, 38)
    note(d, "room 104\n(mine)", (to_px(1600, -3400)[0], to_px(1600, -3400)[1]), (-750, -1250), 38, tilt=-4)
    # the fence behind, and the gate
    for seg in ([(-3700, -100), (-3200, -100)], [(-2800, -100), (4900, -100)]):
        pts = wobble([to_px(*p) for p in seg], 1.0, 22)
        for k in range(len(pts) - 1):
            mx, my = (pts[k][0] + pts[k + 1][0]) / 2, (pts[k][1] + pts[k + 1][1]) / 2
            d.line([(mx - 7, my - 7), (mx + 7, my + 7)], fill=INK, width=3)
            d.line([(mx - 7, my + 7), (mx + 7, my - 7)], fill=INK, width=3)
    write(d, "gate", -3000, 650, 36)


def landmarks(d):
    clear = {c["name"]: c for c in LAYOUT["clearings"]}
    t = clear["tower"]
    px_, py_ = to_px(t["x"], t["y"])
    pen(d, [(px_ - 26, py_ + 36), (px_, py_ - 40), (px_ + 26, py_ + 36)], width=5)
    pen(d, [(px_ - 18, py_ + 12), (px_ + 18, py_ + 12)], width=3)
    pen(d, [(px_ - 12, py_ - 8), (px_ + 12, py_ - 8)], width=3)
    note(d, "old lookout tower -\nnice view of the\nlake from up here", (to_px(7600, 9500)[0], to_px(7600, 9500)[1]),
         (t["x"] - 200, t["y"]), 36, tilt=2)
    for n in ("cabin1", "cabin2", "cabin3"):
        ringed(d, "cabin", clear[n]["x"], clear[n]["y"], 32)
    s = clear["shack"]
    ringed(d, "shack", s["x"], s["y"], 32)
    c = clear["car"]
    note(d, "old car - weird", (to_px(-5600, 8100)[0], to_px(-5600, 8100)[1]), (c["x"] + 100, c["y"]), 34, tilt=-2)
    px_, py_ = to_px(c["x"], c["y"])
    pen(d, [(px_ - 20, py_ + 6), (px_ - 12, py_ - 8), (px_ + 12, py_ - 8), (px_ + 20, py_ + 6), (px_ - 20, py_ + 6)], width=3)
    boxed(d, "boathouse", -3500, 14200, 36)
    pen(d, [to_px(1440, 14450), to_px(1440, 16800), to_px(1560, 16800), to_px(1560, 14450)], width=4)   # dock
    write(d, "dock", 2400, 16200, 36)


def frame(d):
    """Title box, a north arrow with a question mark, and a note box - like her reference maps."""
    l, t, r, b = write_px("Black Hollow Lake HIKE", PX * 0.5, 120, 54)
    pen(d, [(l - 4, t + 2), (r + 4, t), (r + 2, b + 2), (l - 2, b + 4), (l - 4, t + 2)], width=4)
    ax, ay = PX - 300, 300
    pen(d, [(ax, ay + 80), (ax + 2, ay - 70)], width=5)                  # north is straight up the page
    d.line([(ax + 2, ay - 70), (ax - 22, ay - 36)], fill=INK, width=5)
    d.line([(ax + 2, ay - 70), (ax + 26, ay - 36)], fill=INK, width=5)
    write_px("north", ax + 2, ay - 115, 58)
    l, t, r, b = write_px("Note:\nstay on the trail.\ndon't go out on\nthe water at night.\n        - C.", PX - 330, PX - 470, 40, anchor="mm")
    pen(d, [(l - 6, t), (r + 4, t - 2), (r + 6, b + 4), (l - 4, b + 2), (l - 6, t)], width=4)


def torn(img):
    """The page as you hold it on the M screen: torn out of the sketchbook along the left (the
    ragged perforation), the other edges rough, one corner ripped away, edges darkened."""
    w = h = PX
    edge = []
    steps = 520
    for side in range(4):
        walk = 0.0
        for i in range(steps):
            t = i / steps
            walk = walk * 0.92 + rng.uniform(-3.0, 3.0)          # a slow random walk: a torn edge wanders
            if side == 3:                                    # left: torn out of the spiral binding
                inset = 44 + walk + (10 if (i % 26) < 3 else 0)
            else:
                inset = 28 + walk + 10 * math.sin(t * 7 + side * 2.1)
            if side == 0:
                edge.append((t * w, inset))
            elif side == 1:
                edge.append((w - inset, t * h))
            elif side == 2:
                edge.append((w - t * w, h - inset))
            else:
                edge.append((inset, h - t * h))
    cut = [(x, y) for x, y in edge if not (x > w * 0.8 and y > h * 0.86 and (x - w * 0.8) + (y - h * 0.86) > w * 0.1)]
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(cut, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    burn = mask.filter(ImageFilter.GaussianBlur(22))
    dark = Image.new("RGB", (w, h), (170, 140, 100))     # just a little grubby at the edges
    shade = Image.eval(burn, lambda v: 255 - v if v < 255 else 0)
    out = Image.composite(dark, img, shade.point(lambda v: min(255, v * 2))).convert("RGBA")
    out.putalpha(mask)
    out.save(FULL)
    return out


def frame_edge():
    """The corner map's torn edge: a margin of the same paper round a square hole, whose outer
    edge is ragged and darkened like the full sheet's. The HUD draws the moving map window in
    the hole and this on top, with the same tint, so map and margin read as one torn scrap."""
    n = 512
    hole = int(n * FRAME_HOLE)
    img = Image.new("RGB", (n, n), PAPER)
    d = ImageDraw.Draw(img)
    for _ in range(2500):
        x, y = rng.randrange(n), rng.randrange(n)
        v = rng.randint(-14, 8)
        d.point((x, y), fill=tuple(max(0, min(255, c + v)) for c in PAPER))
    edge = []
    steps = 160
    for side in range(4):
        walk = 0.0
        for i in range(steps):
            t = i / steps
            walk = walk * 0.85 + rng.uniform(-2.2, 2.2)
            inset = 9 + walk + 4 * math.sin(t * 9 + side * 1.7)
            inset = max(1.0, min(hole - 6.0, inset))
            if side == 0:
                edge.append((t * n, inset))
            elif side == 1:
                edge.append((n - inset, t * n))
            elif side == 2:
                edge.append((n - t * n, n - inset))
            else:
                edge.append((inset, n - t * n))
    mask = Image.new("L", (n, n), 0)
    ImageDraw.Draw(mask).polygon(edge, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))
    burn = mask.filter(ImageFilter.GaussianBlur(7))
    shade = Image.eval(burn, lambda v: 255 - v if v < 255 else 0)
    img = Image.composite(Image.new("RGB", (n, n), (150, 118, 80)), img, shade.point(lambda v: min(255, v * 2)))
    # the hole the map shows through: a few px smaller than the map window and feathered, so the
    # margin fades over the map's edge instead of leaving a hairline seam between them
    holem = Image.new("L", (n, n), 0)
    ImageDraw.Draw(holem).rectangle([hole + 7, hole + 7, n - 1 - hole - 7, n - 1 - hole - 7], fill=255)
    holem = holem.filter(ImageFilter.GaussianBlur(3.5))
    mask = Image.composite(Image.new("L", (n, n), 0), mask, holem)
    out = img.convert("RGBA")
    out.putalpha(mask)
    out.save(FRAME)


def marker():
    """The 'you are here' arrow: red ink, pointing up (the HUD turns it with your view)."""
    m = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(m)
    d.polygon([(64, 8), (110, 116), (64, 88), (18, 116)], fill=(170, 25, 20, 255), outline=(40, 10, 8, 255))
    m.save(MARKER)




IMG = None


def main():
    global IMG
    img = paper()
    IMG = img
    d = ImageDraw.Draw(img)
    lake(d)
    trees(d)
    town(d)
    trail(d)
    landmarks(d)
    frame(d)
    img = img.filter(ImageFilter.GaussianBlur(0.5))  # ink soaked into the paper a little
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    torn(img)
    frame_edge()
    marker()
    print("map ->", OUT, "+", MARKER)


if __name__ == "__main__":
    main()

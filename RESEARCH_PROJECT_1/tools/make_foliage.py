"""Draw the foliage cards for the trees (maya/make_trees.py): pictures with a see-through
background that the trees hang on their twigs, so a tree reads as hundreds of leaves without
hundreds of thousands of triangles.

Run with normal Python (needs Pillow):  python tools/make_foliage.py
Writes (512 x 512, RGBA: alpha = where there's a leaf):
  export/leaves_broad.png  a cluster of oval leaves on forked twigs (oak / maple / birch mix)
  export/leaves_pine.png   a pine spray: a stem with needles bristling both sides
  export/fern.png          one fern frond (the ferns on the forest floor)
The colour is mostly in the picture; Unreal tints it (green, thinner, dying brown).
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "export")
S = 512


def leaf(d, x, y, length, width, ang, col, vein):
    """One leaf: a pointed oval, a darker midrib."""
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for k in range(17):
        t = k / 16.0
        w = width * math.sin(math.pi * t) ** 0.8 * (1.0 - 0.25 * t)
        pts.append((t * length, w))
    pts += [(t, -w) for t, w in reversed(pts[1:-1])]
    poly = [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]
    d.polygon(poly, fill=col)
    d.line([(x, y), (x + length * 0.9 * ca, y + length * 0.9 * sa)], fill=vein, width=1)


def twig(d, p0, p1, w, col):
    d.line([p0, p1], fill=col, width=w)


def broad(rng):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bark = (58, 44, 30, 255)
    # a forked twig from the bottom middle, splitting twice
    tips = []
    def grow(x, y, ang, length, w, depth):
        x1, y1 = x + math.cos(ang) * length, y + math.sin(ang) * length
        twig(d, (x, y), (x1, y1), w, bark)
        if depth == 0:
            tips.append((x1, y1, ang))
            return
        for k in range(rng.randint(2, 3)):
            t = rng.uniform(0.45, 1.0)
            grow(x + (x1 - x) * t, y + (y1 - y) * t, ang + rng.uniform(-0.75, 0.75), length * rng.uniform(0.5, 0.75),
                 max(1, w - 2), depth - 1)
            tips.append((x + (x1 - x) * t, y + (y1 - y) * t, ang))
    grow(S / 2, S - 4, -math.pi / 2 + rng.uniform(-0.15, 0.15), S * 0.45, 7, 3)
    # leaves at every tip and along the twigs, varied greens with a few yellowing
    for (x, y, ang) in tips:
        for _ in range(rng.randint(4, 7)):
            g = rng.uniform(0.75, 1.15)
            base = (int(70 * g), int(105 * g), int(38 * g)) if rng.random() > 0.12 else (int(125 * g), int(118 * g), int(45 * g))
            col = base + (255,)
            vein = tuple(int(c * 0.7) for c in base) + (255,)
            a = ang + rng.uniform(-1.6, 1.6)
            leaf(d, x + rng.uniform(-6, 6), y + rng.uniform(-6, 6), rng.uniform(34, 58), rng.uniform(11, 18), a, col, vein)
    # soft shading: darker toward the middle (inner leaves are in shade)
    shade = Image.new("L", (S, S), 0)
    ds = ImageDraw.Draw(shade)
    ds.ellipse([S * 0.2, S * 0.25, S * 0.8, S * 0.95], fill=70)
    shade = shade.filter(ImageFilter.GaussianBlur(60))
    r, g_, b, a = im.split()
    dark = Image.new("RGB", (S, S), (0, 0, 0))
    rgb = Image.composite(dark, Image.merge("RGB", (r, g_, b)), shade)
    return Image.merge("RGBA", (*rgb.split(), a))


def pine(rng):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    stem = (66, 50, 34, 255)
    # a main stem bottom to top, two side shoots; needles bristling off every stem
    stems = [((S / 2, S - 2), (S / 2 + rng.uniform(-20, 20), 12), 6)]
    for side in (-1, 1):
        y0 = rng.uniform(S * 0.45, S * 0.7)
        stems.append(((S / 2, y0), (S / 2 + side * S * 0.36, y0 - S * 0.32), 4))
    for (x0, y0), (x1, y1), w in stems:
        d.line([(x0, y0), (x1, y1)], fill=stem, width=w)
        L = math.hypot(x1 - x0, y1 - y0)
        ang = math.atan2(y1 - y0, x1 - x0)
        n = int(L / 2.6)
        for k in range(n):
            t = k / float(n)
            px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for side in (-1, 1):
                a = ang + side * rng.uniform(0.55, 1.0)
                ln = rng.uniform(26, 40) * (1 - 0.35 * t)
                g = rng.uniform(0.7, 1.1)
                col = (int(34 * g), int(66 * g), int(42 * g), 255)
                d.line([(px, py), (px + math.cos(a) * ln, py + math.sin(a) * ln)], fill=col, width=2)
    return im


def fern(rng):
    """One fern frond: a curving stem up the middle, pairs of narrow leaflets getting shorter
    toward the tip, each leaflet itself notched."""
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    for k in range(41):
        t = k / 40.0
        pts.append((S / 2 + 30 * math.sin(t * 2.2) * t, S - 4 - t * (S - 20)))
    d.line(pts, fill=(60, 75, 30, 255), width=4)
    for k in range(3, 40):
        t = k / 40.0
        x, y = pts[k]
        ln = (S * 0.36) * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.7 * (1 - t * 0.55)
        for side in (-1, 1):
            a = -math.pi / 2 + side * (1.15 - 0.35 * t)
            g = rng.uniform(0.8, 1.1)
            col = (int(62 * g), int(98 * g), int(34 * g), 255)
            ex, ey = x + math.cos(a) * ln, y + math.sin(a) * ln
            # a leaflet: a narrow wedge with notches along it
            w = 6 + 4 * (1 - t)
            nx, ny = -math.sin(a), math.cos(a)
            poly = [(x + nx * w * 0.5, y + ny * w * 0.5)]
            for q in range(1, 7):
                f = q / 7.0
                ww = w * (1 - f) * (0.75 if q % 2 else 1.0)
                poly.append((x + (ex - x) * f + nx * ww, y + (ey - y) * f + ny * ww))
            poly.append((ex, ey))
            for q in range(6, 0, -1):
                f = q / 7.0
                ww = w * (1 - f) * (0.75 if q % 2 else 1.0)
                poly.append((x + (ex - x) * f - nx * ww, y + (ey - y) * f - ny * ww))
            poly.append((x - nx * w * 0.5, y - ny * w * 0.5))
            d.polygon(poly, fill=col)
    return im


if __name__ == "__main__":
    rng = random.Random(3)
    broad(rng).save(os.path.join(OUT, "leaves_broad.png"))
    pine(rng).save(os.path.join(OUT, "leaves_pine.png"))
    fern(rng).save(os.path.join(OUT, "fern.png"))
    print("foliage cards -> export/leaves_broad.png, leaves_pine.png, fern.png")

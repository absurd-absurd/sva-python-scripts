"""Draw the pictures for the forest floor: fallen leaves, pine needles, and the trail's dirt.

Run with normal Python (needs Pillow):  python tools/make_litter.py
Writes:
  export/litter_leaves.png   a ragged patch of fallen leaves (oval, lobed and maple-ish; browns,
                             ochre, a few rusty reds, some rotting dark), see-through between
                             the leaves and thinning out to the edge, so patches blend into the
                             ground instead of showing a shape (512 x 512 RGBA)
  export/litter_needles.png  a patch of dead brown pine needles with a few cones and twigs
  textures/forest_litter.jpg the forest ground everywhere: soil nearly covered in leaves and
                             needles (MI_Ground in textures.json; tiles seamlessly)
  textures/trail_leaves.jpg  the trail: packed dirt with leaves pressed into it, darker where
                             feet have worn it (tiles seamlessly; apply_textures.py imports it)
maya/make_floor.py lays the patches on flat cards; unreal/forest_floor.py tints and places them.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "export")
S = 512

# dull autumn colours: the PS2 screen effect and the night tint darken them further
BROWNS = [(92, 62, 36), (110, 76, 42), (74, 52, 32), (128, 96, 48), (100, 70, 30),
          (60, 44, 30), (118, 58, 34), (84, 72, 40), (140, 108, 56)]


def shade(col, g):
    return tuple(max(0, min(255, int(c * g))) for c in col)


def leaf_shape(rng, x, y, size, ang):
    """Outline of one fallen leaf: an oval, a lobed (oak) leaf or a pointed 5-lobed (maple) leaf."""
    kind = rng.random()
    pts = []
    n = 28
    for k in range(n):
        t = 2 * math.pi * k / n
        if kind < 0.5:                                    # oval, pointed at the tip
            r = size * (0.55 + 0.45 * abs(math.cos(t))) * (0.5 if abs(math.sin(t)) > 0.5 else 0.6)
            px, py = math.cos(t) * size, math.sin(t) * size * 0.42
        elif kind < 0.9:                                  # oak: wavy edge
            r = size * (0.62 + 0.14 * math.sin(7 * t))
            px, py = math.cos(t) * r * 1.1, math.sin(t) * r * 0.6
        else:                                             # maple: five points
            r = size * (0.5 + 0.38 * max(0.0, math.cos(5 * (t + 0.31)))) * 0.8
            px, py = math.cos(t) * r, math.sin(t) * r
        ca, sa = math.cos(ang), math.sin(ang)
        pts.append((x + px * ca - py * sa, y + px * sa + py * ca))
    return pts


def draw_leaf(d, rng, x, y, size, ang, col, wrap=None):
    pts = leaf_shape(rng, x, y, size, ang)
    vein = shade(col, 0.72)
    offsets = [(0, 0)] if wrap is None else [(ox, oy) for ox in (-wrap, 0, wrap) for oy in (-wrap, 0, wrap)]
    for ox, oy in offsets:
        d.polygon([(px + ox, py + oy) for px, py in pts], fill=col + (255,))
        ca, sa = math.cos(ang), math.sin(ang)
        d.line([(x - ca * size * 0.8 + ox, y - sa * size * 0.8 + oy), (x + ca * size * 0.9 + ox, y + sa * size * 0.9 + oy)],
               fill=vein + (255,), width=2)


def ragged_falloff(rng):
    """0..1 per pixel: 1 in the middle of the patch, a lumpy edge, 0 outside."""
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    for _ in range(14):                                   # a cluster of soft blobs = an uneven patch
        r = rng.uniform(70, 150)
        cx, cy = S / 2 + rng.uniform(-110, 110), S / 2 + rng.uniform(-110, 110)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(45))
    # keep it inside the card with a margin
    edge = Image.new("L", (S, S), 0)
    ImageDraw.Draw(edge).ellipse([20, 20, S - 20, S - 20], fill=255)
    edge = edge.filter(ImageFilter.GaussianBlur(30))
    return Image.composite(m, Image.new("L", (S, S), 0), edge)


def litter_leaves(rng):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fall = ragged_falloff(rng).load()
    placed = 0
    tries = 0
    while placed < 900 and tries < 20000:
        tries += 1
        x, y = rng.uniform(30, S - 30), rng.uniform(30, S - 30)     # whole leaves only, none cut by the card's edge
        if rng.random() * 255 > fall[int(x) % S, int(y) % S]:
            continue                                      # fewer leaves toward the edge
        col = shade(rng.choice(BROWNS), rng.uniform(0.7, 1.15))
        if rng.random() < 0.15:
            col = shade(col, 0.55)                        # rotting, nearly black
        draw_leaf(d, rng, x, y, rng.uniform(9, 19), rng.uniform(0, math.pi * 2), col)
        placed += 1
    # a couple of thin twigs lying in it
    for _ in range(5):
        x, y = rng.uniform(120, S - 120), rng.uniform(120, S - 120)
        a, ln = rng.uniform(0, math.pi), rng.uniform(60, 150)
        d.line([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln)], fill=(52, 40, 28, 255), width=3)
    return im


def litter_needles(rng):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fall = ragged_falloff(rng).load()
    for _ in range(7000):
        x, y = rng.uniform(30, S - 30), rng.uniform(30, S - 30)
        if rng.random() * 255 > fall[int(x) % S, int(y) % S]:
            continue
        a, ln = rng.uniform(0, math.pi * 2), rng.uniform(10, 22)
        g = rng.uniform(0.6, 1.1)
        col = shade((112, 74, 40), g) if rng.random() > 0.2 else shade((80, 66, 40), g)
        d.line([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln)], fill=col + (255,), width=3)
    for _ in range(6):                                    # cones: little scaled ovals
        x, y = rng.uniform(140, S - 140), rng.uniform(140, S - 140)
        a = rng.uniform(0, math.pi)
        for k in range(7):
            t = k / 6.0 - 0.5
            cx, cy = x + math.cos(a) * t * 34, y + math.sin(a) * t * 34
            r = 9 * (1 - abs(t) * 0.9)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=shade((70, 46, 28), 1 - 0.2 * (k % 2)) + (255,))
    for _ in range(3):
        x, y = rng.uniform(100, S - 100), rng.uniform(100, S - 100)
        a, ln = rng.uniform(0, math.pi), rng.uniform(80, 170)
        d.line([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln)], fill=(50, 38, 26, 255), width=4)
    return im


def trail_dirt(rng):
    """Packed dirt (the dirt photo, darker, less red) + leaves trodden flat into it. Every leaf is
    drawn 9 times (shifted a whole tile each way) so the picture tiles with no seam."""
    src = os.path.join(ROOT, "textures", "dirt.jpg")
    base = Image.open(src).convert("RGB").resize((S, S)) if os.path.exists(src) else Image.new("RGB", (S, S), (70, 55, 40))
    r, g, b = base.split()
    base = Image.merge("RGB", (r.point(lambda v: int(v * 0.7)), g.point(lambda v: int(v * 0.6)), b.point(lambda v: int(v * 0.48))))
    d = ImageDraw.Draw(base)
    for _ in range(420):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        col = shade(rng.choice(BROWNS), rng.uniform(0.45, 0.8))   # trodden: darker, muddier
        draw_leaf(d, rng, x, y, rng.uniform(7, 15), rng.uniform(0, math.pi * 2), col, wrap=S)
    for _ in range(60):                                   # broken leaf bits
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        r = rng.uniform(2, 5)
        col = shade(rng.choice(BROWNS), rng.uniform(0.5, 0.8))
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                d.ellipse([x + ox - r, y + oy - r, x + ox + r, y + oy + r], fill=col)
    return base.filter(ImageFilter.GaussianBlur(0.6))


def ground_litter(rng):
    """The forest ground everywhere: the forest-floor photo, darker, almost covered in fallen
    leaves and needles (soil showing between them). Tiles seamlessly like trail_dirt."""
    src = os.path.join(ROOT, "textures", "forest_floor.jpg")
    base = Image.open(src).convert("RGB").resize((S, S)) if os.path.exists(src) else Image.new("RGB", (S, S), (60, 50, 38))
    r, g, b = base.split()
    base = Image.merge("RGB", (r.point(lambda v: int(v * 0.55)), g.point(lambda v: int(v * 0.5)), b.point(lambda v: int(v * 0.42))))
    d = ImageDraw.Draw(base)
    wrap = [(ox, oy) for ox in (-S, 0, S) for oy in (-S, 0, S)]
    for _ in range(2600):                                 # needles first, leaves on top of them
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        a, ln = rng.uniform(0, math.pi * 2), rng.uniform(8, 16)
        col = shade((96, 66, 38), rng.uniform(0.5, 0.95))
        for ox, oy in wrap:
            d.line([(x + ox, y + oy), (x + ox + math.cos(a) * ln, y + oy + math.sin(a) * ln)], fill=col, width=2)
    for _ in range(1100):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        col = shade(rng.choice(BROWNS), rng.uniform(0.5, 0.95))
        if rng.random() < 0.2:
            col = shade(col, 0.55)
        draw_leaf(d, rng, x, y, rng.uniform(7, 14), rng.uniform(0, math.pi * 2), col, wrap=S)
    return base.filter(ImageFilter.GaussianBlur(0.5))


if __name__ == "__main__":
    rng = random.Random(41)
    os.makedirs(OUT, exist_ok=True)
    litter_leaves(rng).save(os.path.join(OUT, "litter_leaves.png"))
    litter_needles(rng).save(os.path.join(OUT, "litter_needles.png"))
    trail_dirt(rng).save(os.path.join(ROOT, "textures", "trail_leaves.jpg"), quality=92)
    ground_litter(rng).save(os.path.join(ROOT, "textures", "forest_litter.jpg"), quality=92)
    print("litter -> export/litter_leaves.png, export/litter_needles.png, textures/trail_leaves.jpg, textures/forest_litter.jpg")

"""Draw the motel room carpet: an old 70s motel pattern (faded mustard and rust diamond lattice
with dots on a dark olive-brown ground), worn and stained, woven into the photo carpet
texture so it still looks like pile. Tiles seamlessly.

Run with normal Python (needs Pillow; textures/carpet.jpg from tools/fetch_textures.py):
    python tools/make_carpet.py
Writes textures/carpet_pattern.jpg (256 x 256); textures.json gives it to MI_PS2_carpet_mat,
unreal/apply_textures.py imports it.
"""
import os
import random
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 256
GROUND = (50, 45, 36)
LATTICE = (104, 88, 58)         # faded mustard
INNER = (86, 56, 42)            # faded rust
DOT = (122, 110, 86)


def pattern():
    im = Image.new("RGB", (N, N), GROUND)
    d = ImageDraw.Draw(im)
    cell = N // 4                                    # 4 x 4 diamonds per tile
    for gy in range(-1, 5):
        for gx in range(-1, 5):
            cx, cy = gx * cell + cell / 2, gy * cell + cell / 2
            r = cell / 2
            d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], outline=LATTICE, width=3)
            r2 = r * 0.45
            d.polygon([(cx, cy - r2), (cx + r2, cy), (cx, cy + r2), (cx - r2, cy)], fill=INNER)
            d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=DOT)
            for ox, oy in ((cell / 2, 0), (0, cell / 2)):                # dots where diamonds meet
                d.ellipse([cx + ox - 2, cy + oy - 2, cx + ox + 2, cy + oy + 2], fill=DOT)
    return im


def wear(im, rng):
    """Faded traffic paths and dark stains (wrapped around, so the tile still repeats)."""
    mask = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(mask)
    for _ in range(14):
        x, y, r = rng.uniform(0, N), rng.uniform(0, N), rng.uniform(10, 40)
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                d.ellipse([x + ox - r, y + oy - r, x + ox + r, y + oy + r], fill=rng.randint(25, 70))
    mask = mask.filter(ImageFilter.GaussianBlur(9))
    faded = Image.blend(im, Image.new("RGB", (N, N), (78, 70, 56)), 0.65)
    im = Image.composite(faded, im, mask)
    stains = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(stains)
    for _ in range(5):
        x, y, r = rng.uniform(0, N), rng.uniform(0, N), rng.uniform(6, 16)
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                d.ellipse([x + ox - r, y + oy - r * 0.7, x + ox + r, y + oy + r * 0.7], fill=110)
    stains = stains.filter(ImageFilter.GaussianBlur(3))
    return Image.composite(Image.new("RGB", (N, N), (24, 20, 14)), im, stains)


def main():
    rng = random.Random(7)
    im = wear(pattern(), rng)
    pile = Image.open(os.path.join(ROOT, "textures", "carpet.jpg")).convert("L").resize((N, N))
    pile = pile.point(lambda v: int(150 + (v - 128) * 0.9))        # fibres around mid-grey
    im = ImageChops.multiply(im, Image.merge("RGB", (pile, pile, pile)))
    im = im.point(lambda v: min(255, int(v * 1.55)))                 # multiply darkens: bring it back
    im.save(os.path.join(ROOT, "textures", "carpet_pattern.jpg"), quality=92)
    print("carpet pattern -> textures/carpet_pattern.jpg")


if __name__ == "__main__":
    main()

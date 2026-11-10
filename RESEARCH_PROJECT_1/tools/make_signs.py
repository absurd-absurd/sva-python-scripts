"""Paint the two road signs as worn real-world signs (pictures for maya/make_trail.py):
  export/pic_sign_no_trespassing.png  white aluminium sheet: NO TRESPASSING in red, PRIVATE
                                      PROPERTY / VIOLATORS WILL BE PROSECUTED in black, a red
                                      border; faded, rust bleeding from the bolt holes, dents,
                                      a couple of bullet holes, dirt along the bottom
  export/pic_sign_road_closed.png     the standard ROAD CLOSED sign: black on white with a black
                                      border, reflective sheeting cracked and grimy
Run with normal Python (needs Pillow):  python tools/make_signs.py
"""
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "export")
BOLD = r"C:/Windows/Fonts/arialbd.ttf"
REG = r"C:/Windows/Fonts/arial.ttf"
BLACK = r"C:/Windows/Fonts/ariblk.ttf"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype(BOLD, size)


def wear(im, rng, bolts, rust=True, holes=0):
    """Fading, grime, scratches, rust runs from the bolt holes, dents, bullet holes."""
    w, h = im.size
    # uneven fading and grime: soft blotches
    blot = Image.new("L", (w // 16, h // 16))
    blot.putdata([rng.randint(0, 255) for _ in range(blot.width * blot.height)])
    blot = blot.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(20))
    dirt = Image.new("RGB", (w, h), (120, 108, 86))
    im = Image.composite(dirt, im, blot.point(lambda v: int(max(0, v - 120) * 0.55)))
    d = ImageDraw.Draw(im)
    # dirt splashed up along the bottom edge
    grime = Image.new("L", (w, h), 0)
    dg = ImageDraw.Draw(grime)
    for _ in range(600):
        x, y = rng.uniform(0, w), h - abs(rng.gauss(0, h * 0.05))
        r = rng.uniform(2, 6)
        dg.ellipse([x - r, y - r, x + r, y + r], fill=rng.randint(60, 140))
    im = Image.composite(Image.new("RGB", (w, h), (96, 82, 60)), im, grime.filter(ImageFilter.GaussianBlur(2.5)))
    d = ImageDraw.Draw(im)
    # scratches
    for _ in range(40):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        d.line([(x, y), (x + rng.uniform(-40, 40), y + rng.uniform(-6, 6))], fill=(205, 205, 198), width=1)
    # rust from the bolts: a dark ring and a streak running down
    for bx, by in bolts:
        if rust:
            streak = Image.new("L", (w, h), 0)
            ds = ImageDraw.Draw(streak)
            L = rng.uniform(60, 140)
            ds.polygon([(bx - 7, by), (bx + 7, by), (bx + 2 + rng.uniform(-3, 3), by + L), (bx - 2, by + L)], fill=150)
            im = Image.composite(Image.new("RGB", (w, h), (120, 62, 28)), im, streak.filter(ImageFilter.GaussianBlur(3)))
            d = ImageDraw.Draw(im)
        d.ellipse([bx - 9, by - 9, bx + 9, by + 9], fill=(70, 48, 32))
        d.ellipse([bx - 5, by - 5, bx + 5, by + 5], fill=(150, 150, 146))
        d.ellipse([bx - 2, by - 2, bx + 2, by + 2], fill=(40, 40, 40))
    # bullet holes: punched dark hole, bright torn rim, rust starting round it
    for _ in range(holes):
        x, y = rng.uniform(w * 0.15, w * 0.85), rng.uniform(h * 0.2, h * 0.8)
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(130, 80, 44))
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(214, 214, 208))
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(16, 14, 12))
    # dents: soft light/dark pairs
    for _ in range(4):
        x, y, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(25, 60)
        shade = Image.new("L", (w, h), 0)
        ImageDraw.Draw(shade).ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=60)
        im = Image.composite(Image.new("RGB", (w, h), (40, 40, 40)), im, shade.filter(ImageFilter.GaussianBlur(r * 0.5)))
    return im


def centered(d, text, y, f, fill, w):
    tw = d.textlength(text, font=f)
    d.text(((w - tw) / 2, y), text, font=f, fill=fill)


def no_trespassing(rng):
    w, h = 1024, 640
    im = Image.new("RGB", (w, h), (226, 224, 214))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([14, 14, w - 14, h - 14], radius=26, outline=(168, 26, 22), width=16)
    centered(d, "NO", 54, font(BLACK, 180), (168, 26, 22), w)
    centered(d, "TRESPASSING", 250, font(BLACK, 116), (168, 26, 22), w)
    centered(d, "PRIVATE PROPERTY", 410, font(BOLD, 64), (24, 22, 20), w)
    centered(d, "VIOLATORS WILL BE PROSECUTED", 500, font(BOLD, 44), (24, 22, 20), w)
    im = wear(im, rng, [(46, 46), (w - 46, 46), (46, h - 46), (w - 46, h - 46)], holes=3)
    im.save(os.path.join(OUT, "pic_sign_no_trespassing.png"))


def road_closed(rng):
    w, h = 1024, 640
    im = Image.new("RGB", (w, h), (232, 232, 226))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([18, 18, w - 18, h - 18], radius=30, outline=(18, 18, 18), width=18)
    centered(d, "ROAD", 80, font(BLACK, 200), (18, 18, 18), w)
    centered(d, "CLOSED", 330, font(BLACK, 170), (18, 18, 18), w)
    # reflective sheeting cracked in a fine web
    for _ in range(70):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        pts = [(x, y)]
        for k in range(rng.randint(3, 7)):
            x, y = x + rng.uniform(-30, 30), y + rng.uniform(-30, 30)
            pts.append((x, y))
        d.line(pts, fill=(150, 148, 140), width=1)
    im = wear(im, rng, [(60, 40), (w - 60, 40)], holes=1)
    im.save(os.path.join(OUT, "pic_sign_road_closed.png"))


if __name__ == "__main__":
    rng = random.Random(12)
    no_trespassing(rng)
    road_closed(rng)
    print("signs -> export/pic_sign_no_trespassing.png, pic_sign_road_closed.png")

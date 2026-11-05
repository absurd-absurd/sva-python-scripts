"""Draw Cas's lake photos (the prints taped up in Room 104) as small PS2-sized pictures.

Run with normal Python (needs Pillow):  python tools/make_photos.py
Writes export/pic_*.png (128 x 96). maya/make_motel.py puts them on the wall as pic_* materials,
unreal/import_sets.py imports each png and gives it the M_PS2_Picture material.

Each photo is painted from simple layers: sky, a jagged tree line, still water with the
trees reflected, a band of mist, then film grain and a dark vignette, like cheap prints
from a disposable camera. pic_lanterns is the odd one out: red lights out on the water.
"""
import os
import random
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "export")
W, H = 128, 96


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def lake(rng, sky_top, sky_low, water, trees, shore_y, mist=0.0, dock=False, lanterns=0):
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(shore_y):                                         # sky
        d.line([(0, y), (W, y)], fill=mix(sky_top, sky_low, y / shore_y))
    for y in range(shore_y, H):                                      # water, darker toward you
        d.line([(0, y), (W, y)], fill=mix(sky_low, water, min(1, (y - shore_y) / (H - shore_y) * 1.6)))
    # tree line: a row of jagged pines, and its reflection upside down in the water
    x = -4
    while x < W + 4:
        h = rng.randint(8, 22)
        w = rng.randint(4, 8)
        d.polygon([(x - w, shore_y), (x, shore_y - h), (x + w, shore_y)], fill=trees)
        d.polygon([(x - w, shore_y), (x, shore_y + h * 0.6), (x + w, shore_y)], fill=mix(trees, water, 0.45))
        x += rng.randint(3, 7)
    d.rectangle([0, shore_y - 3, W, shore_y], fill=trees)
    if dock:                                                         # old dock running out into the lake
        d.polygon([(52, H), (78, H), (68, shore_y + 10), (63, shore_y + 10)], fill=(38, 30, 24))
        for px in (54, 75, 59, 71):
            d.line([(px, H - 2), (px, H + 6)], fill=(20, 16, 12), width=2)
    for _ in range(lanterns):                                        # red lights floating on the water
        lx, ly = rng.randint(20, 108), rng.randint(shore_y + 4, shore_y + 20)
        d.ellipse([lx - 1, ly - 1, lx + 1, ly + 1], fill=(255, 40, 20))
        d.line([(lx, ly + 2), (lx, ly + 5)], fill=(120, 20, 10))     # its reflection
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    if mist:                                                         # mist hanging over the shore
        fog = Image.new("RGB", (W, H), mix(sky_low, (200, 200, 200), 0.3))
        mask = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(mask)
        for y in range(H):
            md.line([(0, y), (W, y)], fill=int(255 * mist * max(0, 1 - abs(y - shore_y) / 14)))
        im = Image.composite(fog, im, mask)
    px = im.load()                                                   # grain + vignette
    for y in range(H):
        for x in range(W):
            dx, dy = (x - W / 2) / (W / 2), (y - H / 2) / (H / 2)
            v = 1 - 0.45 * min(1, (dx * dx + dy * dy) * 0.6)
            g = rng.uniform(-9, 9)
            px[x, y] = tuple(max(0, min(255, int(c * v + g))) for c in px[x, y])
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    photos = {
        "pic_lake_dusk": dict(sky_top=(70, 78, 92), sky_low=(150, 150, 150), water=(28, 34, 40), trees=(22, 28, 26), shore_y=44, mist=0.5),
        "pic_lake_fog": dict(sky_top=(150, 154, 156), sky_low=(175, 176, 174), water=(80, 86, 88), trees=(95, 100, 98), shore_y=50, mist=0.9),
        "pic_dock": dict(sky_top=(55, 62, 74), sky_low=(120, 122, 126), water=(22, 28, 34), trees=(18, 22, 20), shore_y=38, mist=0.35, dock=True),
        "pic_lake_night": dict(sky_top=(12, 14, 20), sky_low=(40, 44, 52), water=(8, 10, 14), trees=(5, 6, 6), shore_y=46, mist=0.25),
        "pic_lanterns": dict(sky_top=(10, 11, 16), sky_low=(34, 36, 44), water=(6, 8, 12), trees=(4, 5, 5), shore_y=40, mist=0.2, lanterns=9),
    }
    for i, (name, spec) in enumerate(photos.items()):
        lake(random.Random(i + 7), **spec).save(os.path.join(OUT, name + ".png"))
    print("photos:", ", ".join(photos))


if __name__ == "__main__":
    main()

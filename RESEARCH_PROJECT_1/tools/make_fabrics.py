"""Draw fabric textures for the clothes in Cas's suitcase (tiling, 256 x 256):
flannel (red and black plaid), denim (blue twill with lighter weft), knit (oatmeal rib).

Run with normal Python (needs Pillow):  python tools/make_fabrics.py
Writes textures/flannel.jpg, denim.jpg, knit.jpg; textures.json gives them to the clothes.
"""
import os
import random
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 256


def flannel(rng):
    im = Image.new("RGB", (N, N), (120, 26, 24))
    d = ImageDraw.Draw(im)
    for k in range(4):                                   # dark bands both ways, 4 repeats per tile
        o = k * 64
        d.rectangle([o + 10, 0, o + 22, N], fill=(30, 22, 22))
        d.rectangle([0, o + 10, N, o + 22], fill=(30, 22, 22))
        d.rectangle([o + 44, 0, o + 47, N], fill=(36, 26, 24))
        d.rectangle([0, o + 44, N, o + 47], fill=(36, 26, 24))
    px = im.load()
    for y in range(N):                                   # where dark crosses red: in between; weave
        for x in range(N):
            r, g, b = px[x, y]
            v = ((x + y) % 4 < 2) * 10 - 5 + rng.uniform(-6, 6)
            px[x, y] = (max(0, min(255, int(r + v))), max(0, min(255, int(g + v * 0.5))), max(0, min(255, int(b + v * 0.5))))
    return im.filter(ImageFilter.GaussianBlur(0.6))


def denim(rng):
    im = Image.new("RGB", (N, N), (46, 62, 92))
    px = im.load()
    for y in range(N):
        for x in range(N):
            twill = 1 if ((x + y) % 4) < 2 else 0          # diagonal twill lines
            v = 18 * twill + rng.uniform(-10, 10)
            px[x, y] = tuple(max(0, min(255, int(c + v * f))) for c, f in zip(px[x, y], (0.8, 0.9, 1.0)))
    fade = Image.new("L", (N, N), 0)                       # worn lighter patches
    d = ImageDraw.Draw(fade)
    for _ in range(6):
        x, y, r = rng.uniform(0, N), rng.uniform(0, N), rng.uniform(20, 50)
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                d.ellipse([x + ox - r, y + oy - r, x + ox + r, y + oy + r], fill=60)
    fade = fade.filter(ImageFilter.GaussianBlur(14))
    return Image.composite(Image.new("RGB", (N, N), (98, 116, 146)), im, fade)


def knit(rng):
    im = Image.new("RGB", (N, N), (170, 156, 130))
    d = ImageDraw.Draw(im)
    for x in range(0, N, 8):                               # vertical ribs made of little Vs
        d.line([(x, 0), (x, N)], fill=(132, 120, 98), width=2)
        for y in range(0, N, 6):
            d.line([(x + 1, y), (x + 4, y + 4)], fill=(190, 176, 150), width=1)
            d.line([(x + 7, y), (x + 4, y + 4)], fill=(190, 176, 150), width=1)
    px = im.load()
    for y in range(N):
        for x in range(N):
            v = rng.uniform(-8, 8)
            px[x, y] = tuple(max(0, min(255, int(c + v))) for c in px[x, y])
    return im


def main():
    rng = random.Random(5)
    for name, f in (("flannel", flannel), ("denim", denim), ("knit", knit)):
        f(rng).save(os.path.join(ROOT, "textures", name + ".jpg"), quality=92)
    print("fabrics -> textures/flannel.jpg, denim.jpg, knit.jpg")


if __name__ == "__main__":
    main()

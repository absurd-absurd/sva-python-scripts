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


# ---------- her investigation notes (the wall over the dresser in Room 104) ----------

INK_FONT = r"C:/Windows/Fonts/Inkfree.ttf"
PAPER = (214, 204, 172)
INK = (28, 26, 34)
RED = (170, 22, 18)


def _paper(w, h, rng, tint=PAPER):
    im = Image.new("RGB", (w, h), tint)
    px = im.load()
    for y in range(h):                                                   # uneven, yellowed paper
        for x in range(w):
            g = rng.uniform(-10, 6) - 18 * ((x / w - 0.5) ** 2 + (y / h - 0.5) ** 2)
            px[x, y] = tuple(max(0, min(255, int(c + g))) for c in px[x, y])
    return im


def _scrawl(d, x, y, w, rng, ink=INK, height=4):
    """A line of handwriting too small to read: a wobbly pen line with loops."""
    pts, cx = [], x
    while cx < x + w:
        pts.append((cx, y + rng.uniform(-height, height) * (0.5 if rng.random() < 0.6 else 1)))
        cx += rng.uniform(1.5, 3.2)
    d.line(pts, fill=ink, width=1)


def note(name, w, h, lines, seed, extra=None):
    """Handwritten note: real words (lines) where she pressed hard, scrawl everywhere else."""
    from PIL import ImageFont
    rng = random.Random(seed)
    im = _paper(w, h, rng)
    d = ImageDraw.Draw(im)
    y = 8
    for text, size, color, circle in lines:
        if text == "~":
            _scrawl(d, 8, y + 4, w - 16 - rng.randint(0, 30), rng)
            y += 11
            continue
        f = ImageFont.truetype(INK_FONT, size)
        d.text((8 + rng.randint(-2, 4), y), text, font=f, fill=color)
        tw = d.textlength(text, font=f)
        if circle:
            d.ellipse([4, y - 2, 12 + tw + 6, y + size + 4], outline=RED, width=2)
        y += size + 5
    if extra:
        extra(d, im, rng)
    im.save(os.path.join(OUT, name + ".png"))


def clipping(name, seed):
    """A newspaper clipping: masthead, headline, a dark photo, columns of grey type."""
    from PIL import ImageFont
    rng = random.Random(seed)
    w, h = 160, 200
    im = _paper(w, h, rng, tint=(196, 190, 170))
    d = ImageDraw.Draw(im)
    bold = ImageFont.truetype(r"C:/Windows/Fonts/timesbd.ttf", 19)
    small = ImageFont.truetype(r"C:/Windows/Fonts/times.ttf", 10)
    d.text((8, 6), "MARROW FALLS COURIER", font=small, fill=(40, 38, 36))
    d.line([(8, 19), (w - 8, 19)], fill=(40, 38, 36), width=1)
    d.text((8, 22), "GUEST MISSING", font=bold, fill=(20, 20, 20))
    d.text((8, 44), "AT BLACK HOLLOW LAKE", font=ImageFont.truetype(r"C:/Windows/Fonts/timesbd.ttf", 10), fill=(20, 20, 20))
    d.rectangle([8, 64, 70, 112], fill=(46, 48, 50))                      # the photo
    d.rectangle([12, 90, 66, 108], fill=(24, 26, 28))
    for col, (x0, x1, y0) in enumerate(((76, w - 8, 64), (8, 76, 118), (82, w - 8, 118))):
        for yy in range(y0, h - 8, 5):
            d.line([(x0, yy), (x1 - rng.randint(0, 8), yy)], fill=(110, 106, 100), width=1)
    d.ellipse([80, 120, 150, 140], outline=RED, width=2)                 # she circled something
    d.text((96, 142), "1997!", font=ImageFont.truetype(INK_FONT, 15), fill=RED)
    im.save(os.path.join(OUT, name + ".png"))


def lake_map(name, seed):
    """Her hand-drawn map of the lake: shoreline, the dock, the boathouse, X marks."""
    from PIL import ImageFont
    rng = random.Random(seed)
    w, h = 220, 160
    im = _paper(w, h, rng)
    d = ImageDraw.Draw(im)
    pts = []
    for i in range(40):                                                  # wobbly lake outline
        a = i / 40 * 6.283
        r = 1 + 0.12 * math.sin(a * 3 + 1) + rng.uniform(-0.04, 0.04)
        pts.append((110 + math.cos(a) * 80 * r, 78 + math.sin(a) * 50 * r))
    d.line(pts + [pts[0]], fill=INK, width=2)
    f = ImageFont.truetype(INK_FONT, 13)
    d.text((70, 66), "BLACK HOLLOW", font=f, fill=INK)
    d.line([(110, 128), (110, 146)], fill=INK, width=3)                  # the dock
    d.text((116, 136), "dock", font=f, fill=INK)
    d.rectangle([178, 104, 192, 116], outline=INK, width=1)              # boathouse
    d.text((150, 118), "boathouse", font=ImageFont.truetype(INK_FONT, 11), fill=INK)
    for (x, y) in ((92, 50), (128, 46), (150, 70), (96, 96)):            # red X marks on the water
        d.line([(x - 5, y - 5), (x + 5, y + 5)], fill=RED, width=2)
        d.line([(x - 5, y + 5), (x + 5, y - 5)], fill=RED, width=2)
    d.text((8, 8), "where the lights were", font=f, fill=RED)
    d.text((176, 20), "?", font=ImageFont.truetype(INK_FONT, 26), fill=INK)
    im.save(os.path.join(OUT, name + ".png"))


def diary_page(name, words, seed):
    """A page torn out of her diary: ruled lines, a red margin, a ragged torn edge on the
    left, and her handwriting (mostly unreadable scrawl, a few words pressed hard)."""
    from PIL import ImageFont
    rng = random.Random(seed)
    w, h = 120, 160
    im = _paper(w, h, rng, tint=(222, 216, 196))
    d = ImageDraw.Draw(im)
    for y in range(18, h - 6, 11):
        d.line([(0, y), (w, y)], fill=(150, 160, 185), width=1)
    d.line([(20, 0), (20, h)], fill=(190, 90, 90), width=1)
    f = ImageFont.truetype(INK_FONT, 13)
    y = 8
    for word in words:
        if word == "~":
            _scrawl(d, 24, y + 6, w - 30 - rng.randint(0, 28), rng, height=3)
        else:
            d.text((24 + rng.randint(0, 6), y - 1), word, font=f, fill=INK)
        y += 11
    for y in range(0, h, 3):                                             # torn edge: ragged dark bite
        d.line([(0, y), (rng.randint(1, 6), y)], fill=(120, 110, 90), width=3)
    im.save(os.path.join(OUT, name + ".png"))


def notes():
    def arrow(d, im, rng):
        d.line([(20, im.height - 30), (im.width - 30, im.height - 50)], fill=RED, width=2)
        d.line([(im.width - 30, im.height - 50), (im.width - 42, im.height - 44)], fill=RED, width=2)
    note("pic_note_names", 150, 200, [
        ("every year?", 18, INK, False), ("1974  R. Dale", 14, INK, True), ("1981  M. Ostrowski", 14, INK, True),
        ("1988  J. Peake", 14, INK, True), ("1997  T. Hale", 14, INK, True), ("~", 0, 0, 0), ("2009  L. Brandt", 14, INK, True),
        ("2018  D. Moss", 14, INK, True), ("and now me?", 16, RED, False)], seed=1)
    note("pic_note_night", 120, 150, [
        ("SAME", 22, INK, False), ("NIGHT", 22, INK, False), ("every year", 15, RED, True), ("~", 0, 0, 0), ("~", 0, 0, 0),
        ("guest book", 14, INK, False), ("ask office", 14, INK, False)], seed=2)
    note("pic_note_lights", 120, 150, [
        ("red lights", 17, RED, False), ("on the water", 15, INK, False), ("~", 0, 0, 0), ("who carries", 14, INK, False),
        ("them?", 14, INK, False), ("~", 0, 0, 0)], seed=3, extra=arrow)
    note("pic_note_rattle", 120, 150, [
        ("the rattle", 16, INK, False), ("stops when", 14, INK, False), ("I stop", 16, RED, True), ("~", 0, 0, 0), ("~", 0, 0, 0),
        ("~", 0, 0, 0)], seed=4)
    note("pic_note_scrawl", 120, 150, [("~", 0, 0, 0)] * 6 + [("don't stay", 15, INK, False), ("past dark", 15, RED, False)], seed=5)
    for k, words in enumerate((["Oct", "~", "~", "they knew", "~", "~", "~"], ["~", "~", "the lake", "~", "~", "don't", "~", "~"],
                               ["Bug -", "~", "~", "~", "I'm sorry", "~", "~"])):
        diary_page(f"pic_page_{k + 1}", words, seed=10 + k)
    clipping("pic_clipping", seed=6)
    lake_map("pic_lake_map", seed=7)
    print("notes: names, night, lights, rattle, scrawl, clipping, lake map")


if __name__ == "__main__":
    import math
    notes()

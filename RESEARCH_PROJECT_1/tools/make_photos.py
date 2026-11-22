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

INK_FONT = os.path.join(ROOT, "fonts", "RockSalt-Regular.ttf")   # Cas's hand (was Ink Free until 2026-11-17)
CAS_SCALE = 0.72                                                   # Rock Salt draws ~1.4x bigger than Ink Free


def cas_font(size, k=1):
    from PIL import ImageFont
    return ImageFont.truetype(INK_FONT, max(6, int(size * CAS_SCALE * k)))
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
    d.line(pts, fill=ink, width=max(1, int(height) // 4))


def note(name, w, h, lines, seed, extra=None, k=1):
    """Handwritten note: real words (lines) where she pressed hard, scrawl everywhere else.
    k > 1 draws the same note k times bigger (export/hires_<name>.png) for the wall close-up."""
    rng = random.Random(seed)
    im = _paper(w * k, h * k, rng)
    d = ImageDraw.Draw(im)
    y = 8 * k
    for text, size, color, circle in lines:
        if text == "~":
            _scrawl(d, 8 * k, y + 4 * k, (w - 16 - rng.randint(0, 30)) * k, rng, height=4 * k)
            y += 11 * k
            continue
        f = cas_font(size, k)
        x = 8 * k + rng.randint(-2, 4) * k
        l, t, r, bt = d.textbbox((x, y), text, font=f)          # where the ink actually lands
        d.text((x, y - (t - y) + 2 * k), text, font=f, fill=color)   # top of the ink at y + 2
        h_ink = bt - t
        if circle:                                              # round the word, not through it
            d.ellipse([l - 6 * k, y - 3 * k, r + 6 * k, y + h_ink + 7 * k], outline=RED, width=2 * k)
        y += h_ink + (9 if circle else 6) * k
    if extra:
        extra(d, im, rng)
    im.save(os.path.join(OUT, (name if k == 1 else "hires_" + name) + ".png"))


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
    d.text((96, 142), "1997!", font=cas_font(15), fill=RED)
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
    f = cas_font(13)
    d.text((70, 66), "BLACK HOLLOW", font=f, fill=INK)
    d.line([(110, 128), (110, 146)], fill=INK, width=3)                  # the dock
    d.text((116, 136), "dock", font=f, fill=INK)
    d.rectangle([178, 104, 192, 116], outline=INK, width=1)              # boathouse
    d.text((150, 118), "boathouse", font=cas_font(11), fill=INK)
    for (x, y) in ((92, 50), (128, 46), (150, 70), (96, 96)):            # red X marks on the water
        d.line([(x - 5, y - 5), (x + 5, y + 5)], fill=RED, width=2)
        d.line([(x - 5, y + 5), (x + 5, y - 5)], fill=RED, width=2)
    d.text((8, 8), "where the lights were", font=f, fill=RED)
    d.text((176, 20), "?", font=cas_font(26), fill=INK)
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
    f = cas_font(13)
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


def painting(name, seed):
    """The motel's cheap framed landscape over the bed: a lake at sunset under mountains, dark
    pines, a little rowboat. Soft, brushy, faded, like a mass-produced oil print."""
    rng = random.Random(seed)
    w, h = 220, 150
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):                                                   # sunset sky / lake
        t = y / h
        if t < 0.55:
            c = mix((92, 96, 128), (214, 150, 96), (t / 0.55) ** 1.6)
        else:
            c = mix((150, 110, 84), (40, 52, 62), (t - 0.55) / 0.45)
        d.line([(0, y), (w, y)], fill=c)
    for k, (base, col) in enumerate(((70, (98, 92, 118)), (80, (70, 70, 88)))):   # two mountain ranges
        pts = [(0, h)]
        for x in range(0, w + 10, 10):
            pts.append((x, base - 10 * k - rng.uniform(0, 26) * (1 - abs(x - w / 2) / w)))
        pts.append((w, h))
        d.polygon(pts, fill=col)
    d.rectangle([0, 82, w, h], fill=None)
    for y in range(83, h):                                               # lake again over the mountain feet
        t = (y - 83) / (h - 83)
        d.line([(0, y), (w, y)], fill=mix((170, 120, 90), (34, 44, 54), t ** 0.7))
    d.ellipse([150, 50, 172, 72], fill=(240, 196, 120))                  # sun
    d.line([(161, 84), (161, 120)], fill=(220, 170, 110), width=4)       # its reflection
    for x in list(range(0, 70, 7)) + list(range(186, 224, 8)):           # dark pines on the shores
        ht = rng.uniform(26, 50)
        d.polygon([(x - 6, 92), (x, 92 - ht), (x + 6, 92)], fill=(26, 36, 30))
    d.polygon([(98, 112), (120, 112), (116, 116), (102, 116)], fill=(60, 40, 30))   # rowboat
    im = im.filter(ImageFilter.GaussianBlur(0.9))
    px = im.load()
    for y in range(h):                                                   # canvas weave + fading
        for x in range(w):
            g = rng.uniform(-8, 8) + (6 if (x + y) % 3 == 0 else 0)
            px[x, y] = tuple(max(0, min(255, int(c * 0.86 + 22 + g))) for c in px[x, y])
    im.save(os.path.join(OUT, name + ".png"))


def _photo(path, w, h):
    """A silhouette print (export/sil_*.png from tools/make_silhouettes.py), its white border cut off,
    fitted to w x h."""
    im = Image.open(os.path.join(OUT, path)).convert("RGB")
    im = im.crop((30, 30, im.width - 30, im.height - 30))
    return im.resize((w, h), Image.LANCZOS)


def missing_eileen(k=1):
    """Eileen's MISSING poster: a cheap printed flyer, her silhouette, the facts in type.
    150 x 200 on the wall; k = 4 for the close-up."""
    from PIL import ImageFont
    rng = random.Random(21)
    w, h = 150 * k, 200 * k
    im = _paper(w, h, rng, tint=(226, 222, 206))
    d = ImageDraw.Draw(im)
    big = ImageFont.truetype(r"C:/Windows/Fonts/arialbd.ttf", 30 * k)
    t = "MISSING"
    d.text(((w - d.textlength(t, font=big)) / 2, 6 * k), t, font=big, fill=(20, 18, 18))
    ph = _photo("sil_eileen.png", 84 * k, 104 * k)
    x0, y0 = (w - ph.width) // 2, 42 * k
    im.paste(ph, (x0, y0))
    d.rectangle([x0 - k, y0 - k, x0 + ph.width + k, y0 + ph.height + k], outline=(30, 28, 26), width=k)
    bold = ImageFont.truetype(r"C:/Windows/Fonts/arialbd.ttf", 11 * k)
    reg = ImageFont.truetype(r"C:/Windows/Fonts/arial.ttf", 7 * k)
    y = 150 * k
    lines = [("EILEEN BYRNE", bold), ("Missing since October 17, 1997", reg),
             ("Female, age 48, brown hair, brown eyes, 5'6" + chr(34), reg), ("Last seen at the Marrow Falls Motel", reg)]
    for text, f in lines:
        d.text(((w - d.textlength(text, font=f)) / 2, y), text, font=f, fill=(24, 22, 22))
        y += (14 if f is bold else 10) * k
    im = im.filter(ImageFilter.GaussianBlur(0.3 * k))
    im.save(os.path.join(OUT, ("pic_missing_eileen" if k == 1 else "hires_pic_missing_eileen") + ".png"))


def missing_bug(k=1, payphone=False):
    """Bug's MISSING poster for the final shot (a year later, on the payphone; clues.json missing_poster_bug):
    her photo-booth frame, the facts, the fake number. 150 x 200; k = 4 for a sharp copy.
    2026-11-22 (user: "blurry and hard to read" at the end): the small print was 7 px on a 150 px sheet, so it
    is now bigger and wrapped onto more lines (same words), the photo a little smaller; payphone=True writes
    the copy for the final shot (k = 8, turned for the plane in unreal/final_shot.py)."""
    from PIL import ImageFont
    rng = random.Random(31)
    w, h = 150 * k, 200 * k
    im = _paper(w, h, rng, tint=(230, 228, 216))
    d = ImageDraw.Draw(im)
    big = ImageFont.truetype(r"C:/Windows/Fonts/arialbd.ttf", 30 * k)
    t = "MISSING"
    d.text(((w - d.textlength(t, font=big)) / 2, 5 * k), t, font=big, fill=(20, 18, 18))
    ph = _photo("sil_bug.png", 66 * k, 80 * k)
    x0, y0 = (w - ph.width) // 2, 40 * k
    im.paste(ph, (x0, y0))
    d.rectangle([x0 - k, y0 - k, x0 + ph.width + k, y0 + ph.height + k], outline=(30, 28, 26), width=k)
    bold = ImageFont.truetype(r"C:/Windows/Fonts/arialbd.ttf", int(11 * k))
    reg = ImageFont.truetype(r"C:/Windows/Fonts/arial.ttf", int(9 * k))
    y = 126 * k
    lines = [("Last seen: Marrow Falls Motel,", reg), ("October 2002", reg),
             ("Brunette, 5'4" + chr(34) + ", blue eyes,", reg), ("21 years old", reg),
             ("If you have any information", reg), ("please call 555-0117", bold)]
    for text, f in lines:
        d.text(((w - d.textlength(text, font=f)) / 2, y), text, font=f, fill=(24, 22, 22))
        y += (13 if f is bold else 11) * k
    im = im.filter(ImageFilter.GaussianBlur(0.25 * k))
    if payphone:
        im.rotate(90, expand=True).save(os.path.join(OUT, "pic_missing_bug_payphone.png"))
        return
    im.save(os.path.join(OUT, ("pic_missing_bug" if k == 1 else "hires_pic_missing_bug") + ".png"))


def photo_strip(k=1):
    """The photo-booth strip of Cas and Bug (STORY.md: the only picture of the two of them): four frames
    down a white strip: Bug, Cas, then both of them twice. 60 x 220 on the wall; k = 4 for the close-up."""
    w, h = 60 * k, 220 * k
    im = Image.new("RGB", (w, h), (238, 236, 228))
    fw, fh, gap = 52 * k, 50 * k, 4 * k
    bug = _photo("sil_bug.png", fw, fh)
    cas = _photo("sil_cas.png", fw, fh)
    both = Image.new("RGB", (fw, fh))
    both.paste(_photo("sil_cas.png", fw, fh).crop((fw // 4, 0, fw // 4 + fw // 2, fh)), (0, 0))
    both.paste(_photo("sil_bug.png", fw, fh).crop((fw // 4, 0, fw // 4 + fw // 2, fh)), (fw // 2, 0))
    for i, fr in enumerate((bug, cas, both, both)):
        im.paste(fr, ((w - fw) // 2, gap + i * (fh + gap)))
    im = im.filter(ImageFilter.GaussianBlur(0.25 * k))
    im.save(os.path.join(OUT, ("pic_photo_strip" if k == 1 else "hires_pic_photo_strip") + ".png"))


def notes():
    def arrow(d, im, rng):
        d.line([(20, im.height - 30), (im.width - 30, im.height - 50)], fill=RED, width=2)
        d.line([(im.width - 30, im.height - 50), (im.width - 42, im.height - 44)], fill=RED, width=2)
    # (2026-11-17: the old "names" note went - it listed 2009 and 2018, after the game's 2002 - and
    # Eileen's MISSING poster took its place; "red lights on the water" became the lantern note)
    for k in (1, 4):                       # k = 4: the sharp copies for the wall close-up (tools/make_wall.py)
        note("pic_note_night", 120, 150, [
            ("SAME", 22, INK, False), ("NIGHT", 22, INK, False), ("every year", 15, RED, True), ("~", 0, 0, 0),
            ("guest book", 14, INK, False), ("ask office", 14, INK, False)], seed=2, k=k)
        note("pic_note_lights", 120, 150, [
            ("why does", 16, INK, False), ("everyone lie", 16, INK, False), ("about the", 16, INK, False),
            ("red lanterns?", 17, RED, True), ("~", 0, 0, 0)], seed=3, k=k)
        note("pic_note_rattle", 120, 150, [
            ("the rattle", 16, INK, False), ("stops when", 14, INK, False), ("I stop", 16, RED, True), ("~", 0, 0, 0),
            ("~", 0, 0, 0)], seed=4, k=k)
        note("pic_note_scrawl", 120, 150, [("~", 0, 0, 0)] * 5 + [("don't stay", 15, INK, False), ("past dark", 15, RED, False)],
             seed=5, k=k)
        missing_eileen(k)
        photo_strip(k)
        missing_bug(k)
    missing_bug(8, payphone=True)
    for k, words in enumerate((["Oct", "~", "~", "they knew", "~", "~", "~"], ["~", "~", "the lake", "~", "~", "don't", "~", "~"],
                               ["Bug -", "~", "~", "~", "I'm sorry", "~", "~"])):
        diary_page(f"pic_page_{k + 1}", words, seed=10 + k)
    clipping("pic_clipping", seed=6)
    painting("pic_painting", seed=8)
    lake_map("pic_lake_map", seed=7)
    print("notes: night, lantern note, rattle, scrawl, Eileen poster, photo strip, clipping, lake map")


if __name__ == "__main__":
    import math
    notes()

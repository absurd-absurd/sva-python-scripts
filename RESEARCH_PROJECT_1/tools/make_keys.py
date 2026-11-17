"""Draw the keys as the reading screen shows them (user, 2026-11-17: "make the keys look real too").

    python make_keys.py   -> export/paper_key_office.png, paper_key_gate.png, paper_key_boathouse.png
    then unreal/import_papers.py brings them in with the paper sheets (T_Paper_Key_office, ...)

Same 768 x 1024 frame as the sheets (tools/make_papers.py), see-through round the object. Unlike a
paper, the words are drawn INTO the picture (on the tag), and the clue uses hand "none" so the HUD
writes nothing on top. The tag words match clues.json (key_office / key_backgate / key_boathouse).
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "export")
W, H = 768, 1024
FONTS = os.path.join(ROOT, "fonts")


def lerp(a, b, t):
    n = min(len(a), len(b))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(n)) + tuple(a[n:])


def key_image(length, brass=(196, 160, 72), worn=0.0, seed=0):
    """A pin-tumbler key lying flat, bow on the left, pointing right; see-through background.
    Returns (image, bow centre). Brass with a lit top edge, a darker underside, scratches."""
    rng = random.Random(seed)
    w, h = length + 40, 200
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    bx, by, br = 80, 100, 70                                     # the bow: rounded, with a hole
    d.ellipse((bx - br, by - br, bx + br, by + br), fill=255)
    d.rectangle((bx + 40, by - 22, bx + 90, by + 22), fill=255)  # neck
    d.polygon([(bx + 86, by - 30), (bx + 100, by - 30), (bx + 100, by + 30), (bx + 86, by + 30)], fill=255)  # shoulder
    x0, x1 = bx + 100, length
    d.rectangle((x0, by - 22, x1 - 20, by + 8), fill=255)        # blade (spine on top)
    d.polygon([(x1 - 20, by - 22), (x1, by - 10), (x1, by + 2), (x1 - 20, by + 8)], fill=255)   # tip
    pts = [(x0, by + 8)]                                         # the bitting: cuts along the bottom
    cuts = [rng.choice((10, 18, 26, 34)) for _ in range(6)]
    step = (x1 - 30 - x0) / 6
    for k, c in enumerate(cuts):
        xa = x0 + k * step
        pts += [(xa + 4, by + 8 + c), (xa + step - 6, by + 8 + c), (xa + step - 2, by + 8)]
    pts += [(x1 - 24, by + 8)]
    d.polygon(pts + [(x1 - 24, by + 8), (x0, by + 8)], fill=255)
    d.ellipse((bx - 22, by - 22, bx + 22, by + 22), fill=0)      # the hole
    groove = Image.new("L", (w, h), 0)                           # milled groove along the blade
    ImageDraw.Draw(groove).rectangle((x0 + 6, by - 8, x1 - 30, by - 3), fill=255)
    # colour: lit top, dark bottom
    col = Image.new("RGB", (w, h))
    cd = ImageDraw.Draw(col)
    for y in range(h):
        t = abs(y - (by - 25)) / 110
        cd.line((0, y, w, y), fill=lerp(lerp(brass, (255, 236, 170), 0.35), lerp(brass, (70, 50, 20), 0.6), min(1, t)))
    dark = Image.new("RGB", (w, h), lerp(brass, (40, 28, 10), 0.6))
    col.paste(dark, (0, 0), groove)
    cd = ImageDraw.Draw(col)
    for _ in range(40):                                          # scratches and wear
        x, y = rng.randrange(10, w - 10), rng.randrange(30, h - 30)
        cd.line((x, y, x + rng.randint(4, 20), y + rng.randint(-2, 2)), fill=lerp(brass, (255, 245, 210), 0.5), width=1)
    for _ in range(int(worn * 60)):
        x, y = rng.randrange(10, w - 10), rng.randrange(30, h - 30)
        cd.point((x, y), fill=lerp(brass, (60, 70, 40), 0.5))
    img = col.convert("RGBA")
    edge = mask.filter(ImageFilter.FIND_EDGES)
    img.paste((60, 44, 14, 255), (0, 0), edge)
    img.putalpha(mask)
    return img, (bx, by)


def ring(d, cx, cy, r, color=(170, 170, 176)):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(60, 60, 64), width=9)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=6)
    d.arc((cx - r, cy - r, cx + r, cy + r), 200, 300, fill=(235, 235, 240), width=2)


def shadow(img, off=(14, 18), blur=12, alpha=150):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.putalpha(img.getchannel("A").point(lambda a: alpha if a > 0 else 0))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(sh, off)
    out.alpha_composite(img)
    return out


def tag_shape(w, h, color, rng, crack=False):
    """A motel key tag: a long rounded diamond-ish plastic tag with a hole for the ring."""
    t = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    pts = [(0, h / 2), (h / 2, 0), (w - h / 2, 0), (w, h / 2), (w - h / 2, h), (h / 2, h)]
    d.polygon(pts, fill=color)
    d.polygon(pts, outline=lerp(color, (0, 0, 0), 0.45), width=4)
    light = lerp(color, (255, 255, 255), 0.35)
    d.line((h / 2 + 6, 8, w - h / 2 - 6, 8), fill=light, width=3)
    d.ellipse((22, h / 2 - 14, 50, h / 2 + 14), fill=(0, 0, 0, 0))
    if crack:
        x, y = w * 0.62, 0
        pts = [(x, y)]
        while y < h * 0.7:
            x += rng.uniform(-14, 10)
            y += rng.uniform(10, 20)
            pts.append((x, y))
        d.line(pts, fill=lerp(color, (0, 0, 0), 0.6), width=3)
        d.line([(p[0] + 2, p[1]) for p in pts], fill=lerp(color, (255, 255, 255), 0.4), width=1)
    return t


def compose(parts, name, angle):
    """Lay parts on a 1100 canvas, turn it, fit it into the 768 x 1024 frame, add a drop shadow."""
    can = Image.new("RGBA", (1100, 1100), (0, 0, 0, 0))
    for img, pos in parts:
        can.alpha_composite(img, pos)
    can = can.rotate(angle, resample=Image.BICUBIC)
    bb = can.getbbox()
    can = can.crop(bb)
    s = min((W - 120) / can.width, (H - 200) / can.height, 1.0)
    can = can.resize((int(can.width * s), int(can.height * s)), Image.LANCZOS)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(can, ((W - can.width) // 2, (H - can.height) // 2))
    out = shadow(out)
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, f"paper_{name}.png"))
    print("key", name)


def hang(tag):
    """Turn a horizontal tag so it hangs straight down from its hole; returns (tag, hole x, hole y)."""
    w, h = tag.size
    return tag.rotate(-90, expand=True), h / 2, 36


def on_ring(key, tag, kx, ky, r, angle, name):
    """Key bow and tag hole both on one split ring: the key lies flat to the right of the ring, the
    tag hangs below it. kx, ky: where the key image goes (its hole is at +80, +100)."""
    hx, hy = kx + 80, ky + 100                       # the key's hole
    cx, cy = hx, hy + r                              # ring centre: the hole is at its top
    tag, tx, ty = hang(tag)
    # threaded like a real split ring: the whole ring BEHIND the key and the tag (it shows through both
    # holes), then a stretch near each hole drawn again IN FRONT, so it passes through, not over
    back = Image.new("RGBA", (1100, 1100), (0, 0, 0, 0))
    ring(ImageDraw.Draw(back), cx, cy, r)
    front = Image.new("RGBA", (1100, 1100), (0, 0, 0, 0))
    fd = ImageDraw.Draw(front)
    box = (cx - r, cy - r, cx + r, cy + r)
    for a0, a1 in ((272, 345),):                   # over the key's head on the right only (over the tag it
                                                   # looked like it cut through the plastic: user, 2026-11-17)
        fd.arc(box, a0, a1, fill=(60, 60, 64), width=9)
        fd.arc(box, a0, a1, fill=(170, 170, 176), width=6)
        fd.arc(box, a0 + 8, a1 - 25, fill=(235, 235, 240), width=2)
    # the ring goes behind the tag too, showing through the tag's hole
    compose([(back, (0, 0)), (tag, (int(cx - tx), int(cy + r - ty))), (key, (kx, ky)), (front, (0, 0))], name, angle)


def office():
    rng = random.Random(11)
    key, _ = key_image(520, worn=0.6, seed=3)
    tag = tag_shape(640, 150, (150, 34, 30, 255), rng, crack=True)          # old red motel tag, cracked
    td = ImageDraw.Draw(tag)
    f1 = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 23)
    f2 = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 20)
    white = (238, 230, 214, 255)
    for text, fnt, y in (("PROPERTY OF MARROW FALLS MOTEL", f1, 34), ("OFFICE - DO NOT REMOVE", f2, 70),
                         ("FROM PREMISES", f2, 96)):
        td.text((350 - td.textlength(text, font=fnt) / 2, y), text, font=fnt, fill=white)
    on_ring(key, tag, 300, 250, 52, 24, "key_office")


def gate():
    rng = random.Random(12)
    key, _ = key_image(470, brass=(206, 178, 96), worn=0.0, seed=7)        # new: bright, unworn
    tag = tag_shape(540, 140, (176, 30, 26, 255), rng)                        # new red tag, plain
    td = ImageDraw.Draw(tag)
    ink = (20, 18, 20, 255)                                                   # someone wrote on it in marker
    marker = ImageFont.truetype(os.path.join(FONTS, "RockSalt-Regular.ttf"), 19)
    big = ImageFont.truetype(os.path.join(FONTS, "RockSalt-Regular.ttf"), 26)
    for text, fnt, y in (("PROPERTY OF", marker, 10), ("MARROW FALLS MOTEL", marker, 40), ("- GATE.", big, 70)):
        td.text((290 - td.textlength(text, font=fnt) / 2, y), text, font=fnt, fill=ink)
    on_ring(key, tag, 300, 250, 48, -20, "key_gate")


def boathouse():
    rng = random.Random(13)
    # a torn piece of Cas's lake map (export/map_full.png from tools/make_map.py) round the boathouse
    src = Image.open(os.path.join(OUT, "map_full.png")).convert("RGBA")
    sw, shh = src.size
    piece = src.crop((int(sw * 0.43), int(shh * 0.09), int(sw * 0.86), int(shh * 0.40))).resize((620, 450))
    mask = Image.new("L", piece.size, 0)
    pts = []
    for k in range(40):
        pts.append((10 + k * 600 / 39, 10 + rng.uniform(-8, 8)))
    for k in range(30):
        pts.append((610 + rng.uniform(-8, 8), 10 + k * 430 / 29))
    for k in range(40):
        pts.append((610 - k * 600 / 39, 440 + rng.uniform(-8, 8)))
    for k in range(30):
        pts.append((10 + rng.uniform(-8, 8), 440 - k * 430 / 29))
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    piece.putalpha(mask)
    pd = ImageDraw.Draw(piece)
    # the circle round the boathouse, in the wrong hand's thin wobbly pen
    cx, cy = 300, 205
    circ = [(cx + 118 * math.cos(a) + rng.uniform(-3, 3), cy + 46 * math.sin(a) + rng.uniform(-3, 3))
            for a in [k * 2 * math.pi / 40 * 1.08 for k in range(41)]]
    pd.line(circ, fill=(60, 14, 12, 255), width=4)
    key, _ = key_image(300, brass=(200, 186, 150), seed=9)                 # small, nickel-ish, new
    key = key.resize((int(key.width * 0.8), int(key.height * 0.8)))
    line = Image.new("RGBA", (1100, 1100), (0, 0, 0, 0))                   # the loop of fishing line
    ld = ImageDraw.Draw(line)
    KX, KY = 360, 580                                                         # the key, below the circle
    hx, hy = KX + 64, KY + 80                                                 # its hole (scaled 0.8)
    loop = [(hx - 40 + 52 * math.cos(t) + 6 * math.sin(3 * t), hy + 40 + 46 * math.sin(t)) for t in
            [k * 2 * math.pi / 60 for k in range(61)]]
    for wdt, col in ((5, (40, 50, 50, 120)), (3, (225, 235, 232, 235))):     # a dark edge so it reads on the paper
        ld.line(loop, fill=col, width=wdt)
    ld.line([(hx - 40 + 52, hy + 40), (hx + 30, hy + 120), (hx + 70, hy + 200)], fill=(225, 235, 232, 235), width=3)  # loose end
    compose([(piece, (180, 300)), (key, (KX, KY)), (line, (0, 0))], "key_boathouse", 6)


if __name__ == "__main__":
    office()
    gate()
    boathouse()

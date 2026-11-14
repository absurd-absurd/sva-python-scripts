"""Draws the open guest register on the office counter: a two-page spread of an old motel ledger,
yellowed paper, printed column headings (DATE / NAME / ADDRESS / ROOM / CAR LIC.), ruled lines,
and guests' entries in different hands, the last one written tonight.

Writes export/pic_guest_book.png (512 x 330: the left page is the left half). maya/motel_interiors.py
guest_book() lays it over the curved pages as the pic_guest_book material.
"""
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "export", "pic_guest_book.png")
W, H = 512, 330
PAPER = (214, 200, 168)
RULE = (150, 160, 175)
PRINT = (70, 60, 52)
INKS = [(30, 38, 80), (25, 25, 30), (40, 50, 95), (55, 30, 30)]
FONTS = r"C:\Windows\Fonts"


def font(names, size):
    for n in names:
        try:
            return ImageFont.truetype(os.path.join(FONTS, n), size)
        except OSError:
            pass
    return ImageFont.load_default()


ENTRIES = [  # date, name, address, room, car
    ("10/2", "R. Delaney", "Akron, OH", "103", "OH 4471"),
    ("10/3", "Mr & Mrs Hale", "Erie, PA", "101", "PA 2Z90"),
    ("10/7", "T. Oyelaran", "Buffalo, NY", "105", ""),
    ("10/9", "J. Pruitt", "Toledo", "102", "OH 8812"),
    ("10/14", "Marjorie Kell", "Black Hollow", "106", ""),
    ("10/18", "D. Szabo", "Cleveland", "101", "OH 0157"),
    ("10/22", "Paul Ferris", "Pittsburgh", "103", "PA 7K14"),
    ("10/25", "L. Whitcomb", "Ashtabula", "105", ""),
    ("10/29", "K. Ruiz", "Detroit, MI", "102", "MI 3390"),
    ("11/1", "A. Brandt", "Youngstown", "106", "OH 6620"),
    ("11/5", "G. Novak", "Erie, PA", "101", ""),
    ("11/14", "", "", "106", ""),
]


def page(d, x0, entries, rng, heads, hands):
    cols = [x0 + 10, x0 + 46, x0 + 140, x0 + 218]
    d.text((x0 + 12, 10), "GUEST REGISTER", font=heads, fill=PRINT)
    for name, cx in zip(("DATE", "NAME", "ADDRESS", "ROOM"), cols):
        d.text((cx, 30), name, font=font(["arial.ttf"], 9), fill=PRINT)
    for k in range(13):
        y = 44 + k * 21
        d.line((x0 + 8, y, x0 + 248, y), fill=RULE, width=1)
    for cx in cols[1:]:
        d.line((cx - 4, 28, cx - 4, 44 + 12 * 21), fill=(170, 120, 120), width=1)
    for k, e in enumerate(entries):
        hand = hands[k % len(hands)]
        ink = INKS[k % len(INKS)]
        y = 44 + k * 21 + 3
        for txt, cx in zip(e[:4], cols):
            if txt:
                d.text((cx + rng.uniform(-1, 1.5), y + rng.uniform(-1.5, 1)), txt, font=hand, fill=ink)


def main():
    rng = random.Random(4)
    img = Image.new("RGB", (W, H), PAPER)
    px = img.load()
    for y in range(H):                                   # paper grain + age toward the edges
        for x in range(W):
            edge = min(x, W - 1 - x, y, H - 1 - y)
            age = max(0, 18 - edge) * 1.6
            g = rng.randint(-5, 5)
            px[x, y] = tuple(max(0, int(c + g - age)) for c in PAPER)
    d = ImageDraw.Draw(img)
    heads = font(["timesbd.ttf", "georgiab.ttf"], 13)
    hands = [font(["segoepr.ttf"], 10), font(["Inkfree.ttf"], 11), font(["comic.ttf", "segoepr.ttf"], 9), font(["segoeprb.ttf"], 10)]
    page(d, 0, ENTRIES[:6], rng, heads, hands)
    page(d, W // 2, ENTRIES[6:], rng, heads, hands)
    for x in range(W // 2 - 10, W // 2 + 10):            # the gutter's shadow
        a = 1 - abs(x - W // 2) / 10.0
        for y in range(H):
            r, g, b = px[x, y]
            px[x, y] = (int(r * (1 - 0.45 * a)), int(g * (1 - 0.45 * a)), int(b * (1 - 0.45 * a)))
    img.filter(ImageFilter.GaussianBlur(0.3)).save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()

"""Draws the Bible's front cover for Room 102: black pebbled leather, a gold tooled border, a
gold cross, and HOLY BIBLE stamped in gold serif capitals.

Writes export/pic_bible_cover.png (256 x 384, portrait: the top of the cover is the top of the
picture). maya/motel_interiors.py bible() lays it on the cover as the pic_bible_cover material.
"""
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "export", "pic_bible_cover.png")
W, H = 256, 384
GOLD = (176, 138, 64)
GOLD_DARK = (120, 90, 38)


def font(size):
    for name in ("timesbd.ttf", "georgiab.ttf", "times.ttf"):
        try:
            return ImageFont.truetype(os.path.join(r"C:\Windows\Fonts", name), size)
        except OSError:
            pass
    return ImageFont.load_default()


def main():
    rng = random.Random(7)
    img = Image.new("RGB", (W, H), (16, 14, 13))
    px = img.load()
    for y in range(H):                                   # pebbled leather: fine random grain
        for x in range(W):
            v = 14 + rng.randint(-4, 5)
            px[x, y] = (v + 2, v, v - 1)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    d = ImageDraw.Draw(img)
    # tooled border: a double gold line inset from the edge
    for inset, wdt in ((12, 2), (18, 1)):
        d.rectangle((inset, inset, W - 1 - inset, H - 1 - inset), outline=GOLD_DARK if wdt == 1 else GOLD, width=wdt)
    # the cross
    cx, top = W // 2, 70
    d.rectangle((cx - 7, top, cx + 7, top + 140), fill=GOLD)
    d.rectangle((cx - 42, top + 36, cx + 42, top + 50), fill=GOLD)
    d.line((cx - 7, top, cx - 7, top + 140), fill=GOLD_DARK, width=1)
    d.line((cx - 42, top + 50, cx + 42, top + 50), fill=GOLD_DARK, width=1)
    # HOLY BIBLE
    f = font(34)
    for text, y in (("HOLY", 250), ("BIBLE", 290)):
        tw = d.textlength(text, font=f)
        d.text(((W - tw) / 2 + 1, y + 1), text, font=f, fill=GOLD_DARK)
        d.text(((W - tw) / 2, y), text, font=f, fill=GOLD)
    img.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()

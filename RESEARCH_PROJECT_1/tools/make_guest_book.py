"""The motel's guest register, open at October 1997 (clues.json guest_book; STORY.md).

    python make_guest_book.py
      -> export/paper_register.png   768 x 1024: the page as the reading screen shows it (2026-11-17, user:
                                      "pages are pages": the real page, not text describing it)
      -> export/pic_guest_book.png   512 x 330: the open book on the office counter (maya/motel_interiors.py
                                      guest_book() lays it over the curved pages as the pic_guest_book material)

Both come from the same ENTRIES, so the book on the desk and the page you read always match:
a printed ledger page (MARROW FALLS MOTEL - GUEST REGISTER, DATE / NAME / ROOM / NIGHTS), three entries,
each in its guest's own hand, then the next days left blank, and under Eileen's name, in pencil, in a
different hand: "104 - kept." None of these hands is Cas's (Rock Salt), the thing's (Zeyada) or Bug's (Ink Free).
"""
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "export")
WIN = r"C:\Windows\Fonts"
PAPER = (222, 210, 178)
RULE = (150, 162, 178)
RED_RULE = (176, 112, 108)
PRINT = (70, 58, 50)
PENCIL = (96, 96, 100)

# date, name, room, nights, the guest's hand (font file, size at the 768 px page), ink
ENTRIES = [
    ("Oct 14 1997", "D. Hollis", "102", "2", (os.path.join(WIN, "LHANDW.TTF"), 24), (28, 30, 70)),
    ("Oct 15 1997", "The Carvers (2)", "106", "1", (os.path.join(WIN, "BRADHITC.TTF"), 30), (24, 24, 28)),
    ("Oct 17 1997", "Eileen Byrne", "104", "1", (os.path.join(WIN, "segoesc.ttf"), 27), (30, 40, 96)),
    ("Oct 18 1997", "", "", "", None, None),
    ("Oct 19 1997", "", "", "", None, None),
    ("Oct 20 1997", "", "", "", None, None),
]
KEPT = "104 - kept."                     # in pencil, under Eileen's name
PENCIL_HAND = (os.path.join(ROOT, "fonts", "ReenieBeanie.ttf"), 44)   # OFL, fonts/ReenieBeanie_OFL.txt
DATE_HAND = (os.path.join(WIN, "segoepr.ttf"), 20)                     # the desk clerk wrote the dates


def page(w, h, seed, empty=False):
    """One ledger page, w x h, see-through outside its slightly rounded edge."""
    rng = random.Random(seed)
    s = w / 768.0
    f = lambda path_size: ImageFont.truetype(path_size[0], max(6, int(path_size[1] * s)))
    img = Image.new("RGBA", (w, h), PAPER + (255,))
    px = img.load()
    for y in range(h):                                   # grain, and age toward the edges
        for x in range(w):
            edge = min(x, w - 1 - x, y, h - 1 - y) / s
            age = max(0, 40 - edge) * 0.9
            g = rng.randint(-6, 6)
            px[x, y] = tuple(max(0, int(c + g - age * k)) for c, k in zip(PAPER, (1.0, 1.1, 1.5))) + (255,)
    d = ImageDraw.Draw(img)
    head = ImageFont.truetype(os.path.join(WIN, "timesbd.ttf"), int(30 * s))
    small = ImageFont.truetype(os.path.join(WIN, "arial.ttf"), int(17 * s))
    t = "MARROW FALLS MOTEL - GUEST REGISTER"
    if not empty:
        d.text(((w - d.textlength(t, font=head)) / 2, 40 * s), t, font=head, fill=PRINT)
    cols = [60 * s, 230 * s, 560 * s, 650 * s]          # DATE | NAME | ROOM | NIGHTS
    for name, cx in zip(("DATE", "NAME", "ROOM", "NIGHTS"), cols):
        d.text((cx + 6 * s, 104 * s), name, font=small, fill=PRINT)
    top, row = 130 * s, 64 * s
    for k in range(14):
        y = top + k * row
        d.line((30 * s, y, w - 30 * s, y), fill=RULE, width=max(1, int(2 * s)))
    for cx in cols[1:]:
        d.line((cx, 96 * s, cx, top + 13 * row), fill=RED_RULE, width=max(1, int(2 * s)))
    for k, (date, name, room, nights, hand, ink) in enumerate([] if empty else ENTRIES):
        base = top + (k + 1) * row - 14 * s                # writing sits on the next rule down
        dh = f(DATE_HAND)
        d.text((cols[0] + 6 * s + rng.uniform(-2, 2) * s, base - dh.size * 1.1), date, font=dh, fill=(40, 40, 46))
        if not name:
            continue
        fh = f(hand)
        for txt, cx in ((name, cols[1]), (room, cols[2]), (nights, cols[3])):
            d.text((cx + 12 * s + rng.uniform(-3, 3) * s, base - fh.size * 1.15 + rng.uniform(-2, 2) * s), txt, font=fh, fill=ink)
        if name.startswith("Eileen"):
            ph = f(PENCIL_HAND)                            # squeezed in under her name, slanting a little
            layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(layer).text((cols[1] + 60 * s, base + 4 * s), KEPT, font=ph, fill=PENCIL + (210,))
            layer = layer.rotate(-3, center=(cols[1] + 60 * s, base), resample=Image.BICUBIC)
            img.alpha_composite(layer)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((2, 2, w - 3, h - 3), radius=int(8 * s), fill=255)
    img.putalpha(mask)
    return img.filter(ImageFilter.GaussianBlur(0.4 * s))


def main():
    os.makedirs(EXPORT, exist_ok=True)
    page(768, 1024, 4).save(os.path.join(EXPORT, "paper_register.png"))
    # the open book on the counter: this page on the left, the facing page ruled and empty
    W, H = 512, 330
    spread = Image.new("RGB", (W, H), PAPER)
    left = page(256 * 3, 330 * 3, 4).resize((256, 330), Image.LANCZOS)   # drawn big, then shrunk: crisp
    right = page(256 * 3, 330 * 3, 9, empty=True)                         # nobody checked in after her
    right = right.resize((256, 330), Image.LANCZOS)
    spread.paste(left, (0, 0), left)
    spread.paste(right, (256, 0), right)
    px = spread.load()
    for x in range(W // 2 - 10, W // 2 + 10):                             # the gutter's shadow
        a = 1 - abs(x - W // 2) / 10.0
        for y in range(H):
            r, g, b = px[x, y]
            px[x, y] = (int(r * (1 - 0.45 * a)), int(g * (1 - 0.45 * a)), int(b * (1 - 0.45 * a)))
    spread.save(os.path.join(EXPORT, "pic_guest_book.png"))
    print("register page + counter book written")


if __name__ == "__main__":
    main()

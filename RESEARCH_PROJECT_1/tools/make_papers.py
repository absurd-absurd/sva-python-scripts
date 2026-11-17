"""Draw the sheets the reading screen shows a paper on (user, 2026-11-17: "the items you pick up should
actually look like those items ... the letter should be on a piece of paper").

    python make_papers.py   -> export/paper_<kind>.png (768 x 1024, see-through torn/rounded edges)
    then unreal/import_papers.py brings them in as /Game/Horror/UI/T_Paper_<Kind>

The words are NOT drawn here: the HUD writes the clue's text on top, in the paper's hand (clues.json
"hand"), so a text change never needs a new picture. Each clue picks its sheet with clues.json "paper":
  stationery  Marrow Falls Motel letter paper (Cas's letter on the bed)
  notebook    a spiral-notebook page, faint blue rules (Cas's notebook, the later pages)
  typed       an old typed file sheet, punched, a coffee ring (the researchers' log)
  ledger      a guest-register page with ruled columns (the register)
  scrap       a torn-off scrap (the note by her boots, the last page)
The text area is the same on every sheet (the HUD's PAPER_* numbers in tools/make_interact_nodes.py):
keep the top 13% and the side margins free of heavy marks.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "export")
W, H = 768, 1024


def grain(img, rng, amount=10, tint=(0, 0, 0)):
    px = img.load()
    for _ in range(W * H // 6):
        x, y = rng.randrange(W), rng.randrange(H)
        r, g, b, a = px[x, y]
        if a:
            v = rng.randint(-amount, amount)
            px[x, y] = (max(0, min(255, r + v)), max(0, min(255, g + v)), max(0, min(255, b + v)), a)


def age(img, rng, strength=40):
    """Darker, yellower towards the edges, and a few soft stains."""
    shade = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(shade)
    for k in range(40):
        d.rectangle((k * 3, k * 3, W - k * 3, H - k * 3), outline=int(strength * (1 - k / 40)))
    shade = shade.filter(ImageFilter.GaussianBlur(14))
    brown = Image.new("RGBA", (W, H), (120, 90, 40, 255))
    img.paste(brown, (0, 0), shade)


def sheet(color, rng, torn_top=False, torn_all=False, corners=6):
    """A sheet with a see-through edge: straight with soft corners, or torn."""
    img = Image.new("RGBA", (W, H), color + (255,))
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    if torn_all:
        pts = []
        for k in range(60):
            pts.append((14 + k * (W - 28) / 59, 14 + rng.uniform(-10, 10)))
        for k in range(80):
            pts.append((W - 14 + rng.uniform(-10, 10), 14 + k * (H - 28) / 79))
        for k in range(60):
            pts.append((W - 14 - k * (W - 28) / 59, H - 14 + rng.uniform(-10, 10)))
        for k in range(80):
            pts.append((14 + rng.uniform(-10, 10), H - 14 - k * (H - 28) / 79))
        d.polygon(pts, fill=255)
    else:
        d.rounded_rectangle((10, 10, W - 10, H - 10), radius=corners, fill=255)
        if torn_top:                                      # torn out of a spiral notebook
            for x in range(10, W - 10, 3):
                d.line((x, 10, x, 10 + rng.randint(2, 12)), fill=0)
    img.putalpha(mask)
    return img


def save(img, name):
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, f"paper_{name}.png"))
    print("paper", name)


def stationery():
    rng = random.Random(1)
    img = sheet((236, 228, 206), rng)
    grain(img, rng)
    age(img, rng, 35)
    d = ImageDraw.Draw(img)
    serif = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 30)
    small = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 16)
    red = (130, 40, 36, 255)
    t = "MARROW FALLS MOTEL"
    d.text(((W - d.textlength(t, font=serif)) / 2, 40), t, font=serif, fill=red)
    t = "Black Hollow Lake  -  Rooms by the night or week"
    d.text(((W - d.textlength(t, font=small)) / 2, 80), t, font=small, fill=red)
    d.line((90, 112, W - 90, 112), fill=red, width=2)
    d.line((90, 117, W - 90, 117), fill=red, width=1)
    # folded in three to fit an envelope: two soft creases
    for y in (H // 3, 2 * H // 3):
        d.line((10, y, W - 10, y), fill=(200, 190, 165, 255), width=2)
        d.line((10, y + 2, W - 10, y + 2), fill=(250, 245, 230, 255), width=1)
    save(img, "stationery")


def notebook():
    rng = random.Random(2)
    img = sheet((238, 236, 226), rng, torn_top=True)
    grain(img, rng, 8)
    age(img, rng, 25)
    d = ImageDraw.Draw(img)
    for y in range(150, H - 30, 42):                     # faint blue rules
        d.line((14, y, W - 14, y), fill=(160, 180, 210, 255), width=1)
    d.line((96, 14, 96, H - 14), fill=(214, 120, 120, 255), width=2)      # red margin
    for x in range(40, W - 30, 38):                      # the torn spiral perforation
        d.ellipse((x, 22, x + 9, 31), fill=(0, 0, 0, 0))
    save(img, "notebook")


def typed():
    rng = random.Random(3)
    img = sheet((226, 218, 196), rng, corners=2)
    grain(img, rng, 12)
    age(img, rng, 55)
    d = ImageDraw.Draw(img)
    for y in (200, H // 2, H - 200):                     # three punched holes on the left
        d.ellipse((26, y - 13, 52, y + 13), fill=(0, 0, 0, 0))
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))       # a coffee ring, bottom right
    rd = ImageDraw.Draw(ring)
    cx, cy, r = W - 190, H - 210, 92
    rd.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(120, 80, 40, 70), width=7)
    rd.arc((cx - r + 6, cy - r + 4, cx + r - 2, cy + r + 3), 20, 200, fill=(110, 70, 30, 50), width=4)
    img.alpha_composite(ring.filter(ImageFilter.GaussianBlur(1.2)))
    stamp = ImageFont.truetype("C:/Windows/Fonts/courbd.ttf", 34)                # file stamp, top right
    st = Image.new("RGBA", (360, 70), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rectangle((2, 2, 357, 67), outline=(150, 40, 36, 150), width=4)
    sd.text((18, 14), "FILE COPY - 1974", font=stamp, fill=(150, 40, 36, 150))
    st = st.rotate(4, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(st, (W - st.width - 40, 26))
    save(img, "typed")


def ledger():
    rng = random.Random(4)
    img = sheet((232, 226, 204), rng, corners=3)
    grain(img, rng, 9)
    age(img, rng, 40)
    d = ImageDraw.Draw(img)
    green = (110, 140, 120, 255)
    for y in range(150, H - 40, 36):
        d.line((14, y, W - 14, y), fill=(170, 186, 200, 255), width=1)
    d.line((90, 120, 90, H - 30), fill=green, width=2)    # one ruled margin (the HUD's text can't follow columns)
    d.line((14, 120, W - 14, 120), fill=green, width=3)
    save(img, "ledger")


def scrap():
    rng = random.Random(5)
    img = sheet((230, 224, 206), rng, torn_all=True)
    grain(img, rng, 12)
    age(img, rng, 60)
    d = ImageDraw.Draw(img)
    for _ in range(3):                                   # damp, smudged
        x, y = rng.randrange(80, W - 160), rng.randrange(200, H - 200)
        blot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(blot).ellipse((x, y, x + rng.randint(90, 180), y + rng.randint(60, 140)), fill=(90, 80, 60, 28))
        img.alpha_composite(blot.filter(ImageFilter.GaussianBlur(18)))
    save(img, "scrap")


if __name__ == "__main__":
    stationery()
    notebook()
    typed()
    ledger()
    scrap()

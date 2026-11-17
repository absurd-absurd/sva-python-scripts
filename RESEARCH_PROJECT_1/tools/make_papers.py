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
    red = (130, 40, 36, 255)
    t = "MARROW FALLS MOTEL"
    d.text(((W - d.textlength(t, font=serif)) / 2, 40), t, font=serif, fill=red)
    # just the name (user, 2026-11-17: no sub-line under it)
    d.line((90, 88, W - 90, 88), fill=red, width=2)
    d.line((90, 93, W - 90, 93), fill=red, width=1)
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


def coffee_stain(img, cx, cy, r, rng):
    """A dried coffee ring like a real one (user, 2026-11-17: make it look more realistic): a pale
    brown wash inside, the edge darker and uneven where the coffee dried (thick in places, thin and
    broken in others, a slightly wobbly circle), a second fainter ring a little offset from setting the
    mug down again, and a drip and a couple of splash dots."""
    def ring_layer(cx, cy, r, strength, gaps):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.ellipse((cx - r * 0.97, cy - r * 0.97, cx + r * 0.97, cy + r * 0.97), fill=(150, 100, 45, int(26 * strength)))  # the wash
        steps = 260
        ph1, ph2 = rng.uniform(0, 6.28), rng.uniform(0, 6.28)
        for k in range(steps):
            t = k / steps * 2 * math.pi
            if any(a0 <= t <= a1 for a0, a1 in gaps):
                continue
            rr = r * (1 + 0.025 * math.sin(3 * t + ph1) + 0.012 * math.sin(7 * t + ph2))      # not a perfect circle
            wdt = 2.5 + 3.5 * (0.5 + 0.5 * math.sin(2 * t + ph2)) + rng.uniform(-0.8, 0.8)    # thick and thin
            x, y = cx + rr * math.cos(t), cy + rr * math.sin(t)
            alpha = int(strength * (95 + 50 * (0.5 + 0.5 * math.sin(2 * t + ph2))))
            d.ellipse((x - wdt, y - wdt, x + wdt, y + wdt), fill=(96, 58, 22, alpha))
            if rng.random() < 0.35:                                          # a darker crust just inside the edge
                xi, yi = cx + (rr - wdt) * math.cos(t), cy + (rr - wdt) * math.sin(t)
                d.ellipse((xi - 1.2, yi - 1.2, xi + 1.2, yi + 1.2), fill=(80, 46, 16, int(alpha * 0.8)))
        return lay.filter(ImageFilter.GaussianBlur(1.4))
    img.alpha_composite(ring_layer(cx, cy, r, 1.0, [(2.2, 2.55)]))
    img.alpha_composite(ring_layer(cx + 26, cy - 18, r * 0.98, 0.45, [(0.3, 1.4), (3.6, 4.4)]))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))                         # a drip running off the edge, splash dots
    d = ImageDraw.Draw(lay)
    for k in range(18):
        t = k / 17
        x, y = cx - r * 0.72 - t * 26, cy + r * 0.72 + t * 34
        d.ellipse((x - 4 + t * 2, y - 4 + t * 2, x + 4 - t * 2, y + 4 - t * 2), fill=(110, 68, 28, int(70 - 30 * t)))
    for _ in range(4):
        a_, dist = rng.uniform(0, 6.28), r * rng.uniform(1.15, 1.45)
        x, y = cx + dist * math.cos(a_), cy + dist * math.sin(a_)
        rad = rng.uniform(1.5, 3.5)
        d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=(100, 60, 24, 90))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.8)))


def typed():
    rng = random.Random(3)
    img = sheet((226, 218, 196), rng, corners=2)
    grain(img, rng, 12)
    age(img, rng, 55)
    d = ImageDraw.Draw(img)
    for y in (200, H // 2, H - 200):                     # three punched holes on the left
        d.ellipse((26, y - 13, 52, y + 13), fill=(0, 0, 0, 0))
    coffee_stain(img, W - 200, H - 220, 88, rng)                 # a mug set down on it, twice
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


def torn():
    """The last page (user, 2026-11-17): not a full page but a small scrap torn out of a notebook page, ruled
    lines and a red margin, torn ragged on every side. It sits in the middle of the frame, see-through all
    round, just big enough for the HUD's text (which starts 0.11 screen-heights in and 15% down the frame)."""
    rng = random.Random(6)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paper = Image.new("RGBA", (W, H), (236, 233, 220, 255))
    d = ImageDraw.Draw(paper)
    for y in range(118, 520, 42):                         # the notebook's faint rules (same as notebook())
        d.line((0, y), fill=None) if False else d.line((0, y, W, y), fill=(160, 180, 210, 255), width=1)
    d.line((96, 0, 96, H), fill=(214, 120, 120, 255), width=2)          # a bit of the red margin, torn through
    grain(paper, rng, 9)
    x0, x1, y0, y1 = 70, 640, 92, 500                       # the scrap's rough box
    pts = []
    def edge(a, b, n, jag):
        for k in range(n):
            t = k / n
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            nx, ny = b[1] - a[1], -(b[0] - a[0])
            L = (nx * nx + ny * ny) ** 0.5
            j = rng.uniform(-jag, jag) + (jag * 0.8 if k % 3 == 0 else 0)
            pts.append((x + nx / L * j, y + ny / L * j))
    corners = [(x0, y0 + 18), (x1 - 30, y0), (x1, y1 - 40), (x0 + 40, y1)]   # not square: torn at angles
    for i in range(4):
        edge(corners[i], corners[(i + 1) % 4], 46, 7)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    fibre = mask.filter(ImageFilter.GaussianBlur(1.2))     # torn paper shows a lighter fibrous edge
    img.paste(paper, (0, 0), mask)
    rim = Image.new("RGBA", (W, H), (250, 248, 240, 255))
    ring = Image.eval(fibre, lambda v: 255 if 40 < v < 200 else 0)
    img.paste(rim, (0, 0), ring)
    age(img, rng, 30)
    img.putalpha(Image.eval(fibre, lambda v: 255 if v > 40 else 0))
    save(img, "torn")
    # the same scrap with her two lines on it, cropped tight: lying under the lantern in the boathouse it's
    # this cut-out (unreal/key_cards.py), about 10 cm across
    import json
    w = img.copy()
    d = ImageDraw.Draw(w)
    f = ImageFont.truetype(os.path.join(ROOT, "fonts", "Zeyada.ttf"), 44)
    d.text((124, 140), "you came, bug", font=f, fill=(20, 8, 8, 240))
    d.text((124, 300), "now we can be together", font=f, fill=(20, 8, 8, 240))
    w = w.crop(w.getbbox())
    w.save(os.path.join(OUT, "keycard_torn.png"))
    cards_path = os.path.join(OUT, "keycards.json")
    cards = json.load(open(cards_path)) if os.path.exists(cards_path) else {}
    cards["torn"] = [10.0, round(10.0 * w.height / w.width, 2)]
    json.dump(cards, open(cards_path, "w"), indent=1)


def world_card(paper, lines, name, width_cm, size=40, x=124, y=150, gap=1.6):
    """A sheet with its words written on, cropped tight: the object as it lies in the world (cut-out,
    unreal/key_cards.py; place_clues.py lays it flat), width_cm wide. Adds it to export/keycards.json."""
    import json
    img = Image.open(os.path.join(OUT, f"paper_{paper}.png")).convert("RGBA")
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(os.path.join(ROOT, "fonts", "Zeyada.ttf"), size)
    for k, line in enumerate(lines):
        d.text((x, y + k * size * gap), line, font=f, fill=(20, 8, 8, 240))
    img = img.crop(img.getbbox())
    img.save(os.path.join(OUT, f"keycard_{name}.png"))
    cards_path = os.path.join(OUT, "keycards.json")
    cards = json.load(open(cards_path)) if os.path.exists(cards_path) else {}
    cards[name] = [width_cm, round(width_cm * img.height / img.width, 2)]
    json.dump(cards, open(cards_path, "w"), indent=1)


if __name__ == "__main__":
    torn()
    stationery()
    notebook()
    typed()
    ledger()
    scrap()
    # the note by her boots, as it lies by the water door (the reading screen shows paper_scrap + the HUD text)
    world_card("scrap", ["the lanterns are lit for", "you, bug", "", "don't worry, it won't be", "much longer now"], "scrap", 15.0, size=52)

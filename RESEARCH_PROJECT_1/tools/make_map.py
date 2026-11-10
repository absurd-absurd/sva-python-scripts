"""Draw the in-game map of Marrow Falls: an old paper map in ink, made from the level layout.

    python make_map.py            -> export/map.png (2048 x 2048) + export/map_marker.png,
                                     + export/map_full.png (torn paper, for the M screen);
                                     then unreal/import_map.py brings them into Unreal

Everything on it comes from the same data the level is built from:
  layout.json     trail, woods area, clearings (tower, cabins) and the map's world bounds
  export/scatter.json   every tree/rock the Maya scatter tool placed (small ink marks)
  export/fill.json      the forest filling the ground round the motel (tools/make_fill.py)
  the motel/office/road numbers below match blockout.py and maya/make_motel.py
The hunting shack and the rusted car are left off on purpose: they're not on a tourist map.

North (the lake, +Y) is up. Seen facing north, Unreal's +X is to the LEFT (west), so the
map flips X: u = (x_max - x) / size. The HUD uses the same bounds to put you on it.
Needs Pillow (python -m pip install pillow) and the Ink Free font that comes with Windows.
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LAYOUT = json.load(open(os.path.join(ROOT, "layout.json")))
SCATTER = os.path.join(ROOT, "export", "scatter.json")
OUT = os.path.join(ROOT, "export", "map.png")
MARKER = os.path.join(ROOT, "export", "map_marker.png")
FULL = os.path.join(ROOT, "export", "map_full.png")      # the torn-paper version for the M screen
B = LAYOUT["map"]                                   # world bounds of the picture (square)
PX = B["px"]
FONT = r"C:/Windows/Fonts/Inkfree.ttf"

PAPER = (214, 196, 158)
INK = (52, 40, 30)
FADED = (120, 100, 78)
WATER = (120, 132, 132)
RED = (150, 30, 25)

rng = random.Random(7)


def to_px(x, y):
    size = B["x_max"] - B["x_min"]
    return ((B["x_max"] - x) / size * PX, (B["y_max"] - y) / size * PX)


def cm(d):
    return d / (B["x_max"] - B["x_min"]) * PX


def font(size):
    return ImageFont.truetype(FONT, int(size))


def label(d, text, x, y, size=46, fill=INK, anchor="mm"):
    d.text(to_px(x, y), text, font=font(size), fill=fill, anchor=anchor)


def rect(d, x0, x1, y0, y1, fill=None, outline=INK, width=4):
    (a, b), (c, e) = to_px(x0, y0), to_px(x1, y1)
    d.rectangle([min(a, c), min(b, e), max(a, c), max(b, e)], fill=fill, outline=outline, width=width)


def paper():
    img = Image.new("RGB", (PX, PX), PAPER)
    d = ImageDraw.Draw(img)
    for _ in range(9000):                            # fibres and specks
        x, y = rng.randrange(PX), rng.randrange(PX)
        v = rng.randint(-22, 14)
        d.point((x, y), fill=tuple(max(0, min(255, c + v)) for c in PAPER))
    stains = Image.new("L", (PX, PX), 0)
    sd = ImageDraw.Draw(stains)
    for _ in range(14):                              # old water stains
        cx, cy, r = rng.randrange(PX), rng.randrange(PX), rng.randint(60, 260)
        sd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rng.randint(18, 40))
    stains = stains.filter(ImageFilter.GaussianBlur(40))
    img = Image.composite(Image.new("RGB", (PX, PX), (160, 132, 92)), img, stains)
    d = ImageDraw.Draw(img)
    for frac in (0.33, 0.66):                        # fold creases
        d.line([(PX * frac, 0), (PX * frac, PX)], fill=(196, 176, 138), width=3)
        d.line([(0, PX * frac), (PX, PX * frac)], fill=(196, 176, 138), width=3)
    return img


def lake(d):
    # wobbly south shore at about y = 14500, water to the top of the map
    pts = []
    for i in range(61):
        x = B["x_min"] + (B["x_max"] - B["x_min"]) * i / 60
        y = 14500 + 250 * math.sin(x / 1700.0) + rng.uniform(-120, 120)
        pts.append(to_px(x, y))
    poly = pts + [to_px(B["x_max"], B["y_max"]), to_px(B["x_min"], B["y_max"])]   # back along the top edge
    d.polygon(poly, fill=WATER)
    d.line(pts, fill=INK, width=5)
    for k in range(1, 5):                            # hatched ripple lines along the shore
        d.line([(x, y - k * 22) for x, y in pts], fill=(98, 110, 112), width=2)
    label(d, "BLACK HOLLOW LAKE", 0, 17600, 90)


def trees(d):
    if not os.path.exists(SCATTER):
        return
    data = json.load(open(SCATTER))
    for c in data["copies"]:
        m, prop = c["matrix"], c.get("asset", "")
        x, y = m[12], m[14]                          # Maya (x, y, z) -> Unreal (x, z, y)
        px, py = to_px(x, y)
        if "tree" in prop:
            r = 7 if "dead" in prop else 9
            d.line([(px, py - r), (px - r, py + r), (px + r, py + r), (px, py - r)], fill=FADED, width=2)
        elif "rock" in prop:
            d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=FADED)
    fill_path = os.path.join(ROOT, "export", "fill.json")             # the forest round the motel (tools/make_fill.py)
    if os.path.exists(fill_path):
        for it in json.load(open(fill_path))["items"]:
            if "tree" in it["asset"]:
                px, py = to_px(it["x"], it["y"])
                r = 7 if "dead" in it["asset"] else 9
                d.line([(px, py - r), (px - r, py + r), (px + r, py + r), (px, py - r)], fill=FADED, width=2)


def trail(d):
    pts = [to_px(x, y) for x, y in LAYOUT["trail"]]
    for (a, b), (c, e) in zip(pts, pts[1:]):         # dashed ink path
        n = max(1, int(math.dist((a, b), (c, e)) / 26))
        for k in range(0, n, 2):
            t0, t1 = k / n, min(1, (k + 1) / n)
            d.line([(a + (c - a) * t0, b + (e - b) * t0), (a + (c - a) * t1, b + (e - b) * t1)], fill=INK, width=6)
    label(d, "trail", -2300, 2300, 44, FADED)


def town(d):
    # the road and the motel
    rect(d, B["x_min"], B["x_max"], -4950, -4050, fill=(150, 140, 122))
    label(d, "OLD LAKE ROAD", -6000, -4500, 48)
    rect(d, -2900, 4150, -3500, -1450, outline=FADED, width=3)               # parking lot
    rect(d, -2500, 500, -1400, -700, fill=(120, 96, 76))                     # room row
    for i in range(1, 6):
        x = -2500 + i * 500
        d.line([to_px(x, -1400), to_px(x, -700)], fill=INK, width=3)
    for i in range(6):
        label(d, str(101 + i), -2250 + i * 500, -1050, 19, (230, 215, 190))
    rect(d, 3050, 3750, -1750, -850, fill=(120, 96, 76))                     # office
    label(d, "OFFICE", 3400, -550, 40)
    label(d, "MARROW FALLS MOTEL", -1000, -2500, 64)
    d.line([to_px(-2800, -100), to_px(3500, -100)], fill=FADED, width=4)     # fence behind the motel
    # (the neon cross in front of the office was removed Nov 9: a small one hangs inside now)


def landmarks(d):
    for c in LAYOUT["clearings"]:
        n, x, y = c["name"], c["x"], c["y"]
        if n == "tower":
            rect(d, x - 250, x + 250, y - 250, y + 250, fill=(150, 120, 90))
            d.line([to_px(x - 250, y - 250), to_px(x + 250, y + 250)], fill=INK, width=3)
            d.line([to_px(x + 250, y - 250), to_px(x - 250, y + 250)], fill=INK, width=3)
            label(d, "LOOKOUT", x, y - 600, 42)
        elif n.startswith("cabin"):
            rect(d, x - 350, x + 350, y - 300, y + 300, fill=(120, 96, 76))
    label(d, "cabins", -6500, 12500, 40, FADED)
    label(d, "cabins", 6300, 11600, 40, FADED)
    rect(d, -3900, -3100, 14200, 15200, fill=(120, 96, 76))                 # boathouse
    label(d, "boathouse", -3500, 13800, 40, FADED)
    rect(d, 1375, 1625, 14500, 16700, fill=(150, 120, 90), width=3)         # dock
    label(d, "dock", 2400, 15800, 40, INK)


def frame(d):
    d.rectangle([6, 6, PX - 7, PX - 7], outline=INK, width=10)
    d.rectangle([24, 24, PX - 25, PX - 25], outline=FADED, width=3)
    # compass in the top-left corner
    cx, cy = 150, 170
    d.polygon([(cx, cy - 80), (cx - 22, cy), (cx + 22, cy)], fill=INK)
    d.polygon([(cx, cy + 80), (cx - 22, cy), (cx + 22, cy)], outline=INK, width=3)
    d.text((cx, cy - 115), "N", font=font(56), fill=INK, anchor="mm")
    d.text((PX - 190, 330), "MARROW FALLS  - visitors' map -", font=font(40), fill=(200, 205, 200), anchor="rs")


def marker():
    """The 'you are here' arrow: red ink, pointing up (the HUD turns it with your view)."""
    m = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(m)
    d.polygon([(64, 8), (110, 116), (64, 88), (18, 116)], fill=(170, 25, 20, 255), outline=(40, 10, 8, 255))
    m.save(MARKER)


def torn(img):
    """The full-screen map: the same map on a sheet torn out of something, ragged edges with
    see-through bits (alpha), the paper scorched darker near the tears, one corner ripped off."""
    w = h = PX
    edge = []                                        # walk around the sheet with a jagged inset
    steps = 220
    for side in range(4):
        for i in range(steps):
            t = i / steps
            inset = 40 + rng.uniform(0, 34) + 26 * math.sin(t * 19 + side * 2.1)
            if rng.random() < 0.04:
                inset += rng.uniform(25, 70)         # a deeper rip now and then
            if side == 0:
                edge.append((t * w, inset))
            elif side == 1:
                edge.append((w - inset, t * h))
            elif side == 2:
                edge.append((w - t * w, h - inset))
            else:
                edge.append((inset, h - t * h))
    # rip off the top-right corner
    cut = [(x, y) for x, y in edge if not (x > w * 0.83 and y < h * 0.15 and x - w * 0.83 > y * 1.1)]
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(cut, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    burn = mask.filter(ImageFilter.GaussianBlur(28))  # darker paper near the torn edge
    dark = Image.new("RGB", (w, h), (92, 66, 40))
    shade = Image.eval(burn, lambda v: 255 - v if v < 255 else 0)
    paper_img = Image.composite(dark, img, shade.point(lambda v: min(255, v * 2)))
    out = paper_img.convert("RGBA")
    out.putalpha(mask)
    out.save(FULL)


def main():
    img = paper()
    d = ImageDraw.Draw(img)
    lake(d)
    trees(d)
    town(d)
    trail(d)
    landmarks(d)
    frame(d)
    img = img.filter(ImageFilter.GaussianBlur(0.6))  # soft, printed look
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    torn(img)
    marker()
    print("map ->", OUT, "+", MARKER)


if __name__ == "__main__":
    main()

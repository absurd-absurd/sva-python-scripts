"""Paint the parking lot and road surfaces as single large textures (not tiled), so the old lot
reads as one real worn surface: aggregate grain and tone variation, worn tyre tracks into the
stalls, an oil stain under every stall, branching cracks and crumbling alligator cracking,
repair patches with crisp edges, a wet puddle, dirt and grit along the curb. Plus the car's plate.

Run with normal Python (needs Pillow):  python tools/make_asphalt.py
Writes export/pic_lot_asphalt.png (2048 wide: the lot, LOT below, the same as maya/make_motel.py),
export/pic_road_asphalt.png ( the road by the motel, x -8000..8000, 900 wide, 4096 x 232) and
export/pic_car_plate.png. maya/exterior_props.py lays them on the ground as pic_* planes.
"""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "export")
LOT = (-2520, 4150, -4050, -1700)              # must match maya/make_motel.py
DRIVES = ((-2300, -1700), (2700, 3300))
X0, ROOM_W, FRONT, WALK = -2500, 500, -1400, 300


def noise(w, h, scale, rng, blur):
    """Smooth value noise: random greys at a coarse grid, scaled up and blurred."""
    small = Image.new("L", (max(2, w // scale), max(2, h // scale)))
    small.putdata([rng.randint(0, 255) for _ in range(small.width * small.height)])
    return small.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))


def base_asphalt(w, h, rng, tone=58):
    """Grey asphalt with aggregate: fine grain, light stones, dark pits, big soft tone blotches."""
    big = noise(w, h, 48, rng, 20)
    mid = noise(w, h, 8, rng, 2)
    im = Image.new("RGB", (w, h))
    px = im.load()
    bp, mp = big.load(), mid.load()
    for y in range(h):
        for x in range(w):
            v = tone + (bp[x, y] - 128) * 0.16 + (mp[x, y] - 128) * 0.08 + rng.uniform(-9, 9)
            r = rng.random()
            if r < 0.012:
                v += rng.uniform(25, 55)            # light aggregate stone
            elif r < 0.02:
                v -= rng.uniform(15, 30)            # pit
            v = max(5, min(230, v))
            px[x, y] = (int(v), int(v * 0.99), int(v * 0.97))
    return im


def stamp(im, mask, color, strength=1.0):
    layer = Image.new("RGB", im.size, color)
    if strength != 1.0:
        mask = mask.point(lambda v: int(v * strength))
    return Image.composite(layer, im, mask)


def crack_path(d, x, y, length, rng, width, branch=0.25, depth=0):
    ang = rng.uniform(0, math.pi * 2)
    pts = [(x, y)]
    for _ in range(int(length)):
        ang += rng.uniform(-0.5, 0.5)
        x += math.cos(ang) * 4
        y += math.sin(ang) * 4
        pts.append((x, y))
        if depth < 2 and rng.random() < branch * 0.06:
            crack_path(d, x, y, length * 0.4, rng, max(1, width - 1), branch, depth + 1)
    d.line(pts, fill=255, width=width)


def alligator(d, cx, cy, r, rng):
    """Crumbling 'alligator' cracking: a net of small polygons."""
    for _ in range(int(r * 0.9)):
        a = rng.uniform(0, math.pi * 2)
        rr = rng.uniform(0, r)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.7
        pts = [(x, y)]
        for k in range(rng.randint(3, 6)):
            a2 = rng.uniform(0, math.pi * 2)
            x, y = x + math.cos(a2) * rng.uniform(3, 8), y + math.sin(a2) * rng.uniform(3, 8)
            pts.append((x, y))
        d.line(pts, fill=255, width=1)


def lot():
    rng = random.Random(23)
    W = 2048
    H = int(round(W * (LOT[3] - LOT[2]) / float(LOT[1] - LOT[0])))
    sx = W / (LOT[1] - LOT[0])
    sy = H / (LOT[3] - LOT[2])
    to_px = lambda X, Y: ((X - LOT[0]) * sx, (LOT[3] - Y) * sy)       # image top = walkway edge
    im = base_asphalt(W, H, rng, tone=52)                             # the same asphalt as the road (one surface)
    # tyre wear: smooth darker, slightly polished lanes (the drive lane and into each stall)
    wear = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(wear)
    lane_y = to_px(0, -2640)[1]                                      # the drive aisle between the rows
    d.rectangle([0, lane_y - 40, W, lane_y + 40], fill=110)
    for k in range(12):
        cx = X0 + k * ROOM_W / 2 + 125
        for side in (-55, 55):
            a = to_px(cx + side, -1900)
            b = to_px(cx + side, -3400)
            d.line([a, b], fill=120, width=14)
    for a_, b_ in DRIVES:                                            # in and out at the driveways
        p, q = to_px(a_ + 60, LOT[2]), to_px(b_ - 60, LOT[2])
        d.polygon([(p[0], H), (q[0], H), (q[0] - 20, lane_y), (p[0] + 20, lane_y)], fill=120)
    wear = wear.filter(ImageFilter.GaussianBlur(10))
    im = stamp(im, wear, (30, 30, 31), 0.85)
    # oil stains under every stall, plus a few strays
    oil = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(oil)
    for k in range(24):                                              # both rows of stalls
        cx, cy = to_px(X0 + (k % 12) * ROOM_W / 2 + 125 + rng.uniform(-25, 25), (-2120 if k < 12 else -3200) + rng.uniform(-40, 40))
        for _ in range(rng.randint(2, 5)):
            r = rng.uniform(4, 14)
            ox, oy = rng.uniform(-10, 10), rng.uniform(-8, 8)
            d.ellipse([cx + ox - r, cy + oy - r * 0.8, cx + ox + r, cy + oy + r * 0.8], fill=rng.randint(120, 220))
    for _ in range(14):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(3, 9)
        d.ellipse([x - r, y - r, x + r, y + r], fill=rng.randint(80, 160))
    oil = oil.filter(ImageFilter.GaussianBlur(3))
    im = stamp(im, oil, (10, 9, 8), 0.9)
    # repair patches: darker, smoother, crisp edges, a thin sealed seam
    newer = base_asphalt(W, H, rng, tone=47).filter(ImageFilter.GaussianBlur(0.5))     # fresher, smoother asphalt
    pm = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(pm)
    seams = Image.new("L", (W, H), 0)
    ds = ImageDraw.Draw(seams)
    for _ in range(9):
        x, y = rng.uniform(80, W - 200), rng.uniform(40, H - 120)
        w, h = rng.uniform(30, 110), rng.uniform(20, 70)
        pts = [(x + rng.uniform(-4, 4), y + rng.uniform(-3, 3)), (x + w + rng.uniform(-4, 4), y + rng.uniform(-3, 3)),
               (x + w + rng.uniform(-6, 6), y + h * 0.5), (x + w + rng.uniform(-4, 4), y + h + rng.uniform(-3, 3)),
               (x + rng.uniform(-4, 4), y + h + rng.uniform(-3, 3)), (x + rng.uniform(-6, 6), y + h * 0.5)]
        d.polygon(pts, fill=255)
        ds.line(pts + [pts[0]], fill=200, width=1)                               # sealed seam
    im = Image.composite(newer, im, pm.filter(ImageFilter.GaussianBlur(0.8)))
    im = stamp(im, seams, (24, 24, 24), 0.7)
    # cracks and alligator cracking
    cr = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(cr)
    for _ in range(40):
        crack_path(d, rng.uniform(0, W), rng.uniform(0, H), rng.uniform(15, 60), rng, rng.choice((1, 1, 2)))
    for _ in range(7):
        alligator(d, rng.uniform(100, W - 100), rng.uniform(60, H - 60), rng.uniform(25, 60), rng)
    cr = cr.filter(ImageFilter.GaussianBlur(0.4))
    im = stamp(im, cr, (12, 12, 12), 0.95)
    # a shallow puddle: darker, smoother, a lighter rim of dried grit
    pud = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(pud)
    px_, py_ = to_px(-1300, -3200)
    d.ellipse([px_ - 70, py_ - 22, px_ + 70, py_ + 22], fill=255)
    d.ellipse([px_ - 30, py_ + 5, px_ + 40, py_ + 30], fill=255)
    pud = pud.filter(ImageFilter.GaussianBlur(4))
    rim = ImageChops.subtract(pud.filter(ImageFilter.MaxFilter(9)), pud)
    im = stamp(im, pud, (20, 22, 26), 0.85)
    im = stamp(im, rim, (92, 88, 80), 0.5)
    # grit, dirt and leaves along the road curb and the walkway edge
    edge = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(edge)
    for y0, y1 in ((0, 14),):                                       # (no curb on the road side: it runs on into the road)
        for _ in range(2500):
            x, y = rng.uniform(0, W), rng.uniform(y0, y1)
            d.point((x, y), fill=rng.randint(100, 255))
    edge = edge.filter(ImageFilter.GaussianBlur(1.2))
    im = stamp(im, edge, (70, 58, 42), 0.6)
    for _ in range(140):                                            # dead leaves
        x, y = rng.uniform(0, W), rng.choice((rng.uniform(0, 20), rng.uniform(0, H)))
        c = rng.choice(((70, 48, 22), (52, 38, 20), (88, 60, 28)))
        ImageDraw.Draw(im).ellipse([x, y, x + rng.uniform(2, 4), y + rng.uniform(1, 3)], fill=c)
    im.save(os.path.join(OUT, "pic_lot_asphalt.png"))
    print("lot asphalt", im.size)


def road():
    rng = random.Random(31)
    W, H = 4912, 276                     # 3.26 cm a pixel, exactly like the lot: where they meet reads as one surface
    im = base_asphalt(W, H, rng, tone=52)
    wear = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(wear)
    for yy in (H * 0.27, H * 0.38, H * 0.62, H * 0.73):                 # tyre lanes, both directions
        d.line([(0, yy), (W, yy)], fill=150, width=6)
    wear = wear.filter(ImageFilter.GaussianBlur(4))
    im = stamp(im, wear, (30, 30, 30), 0.6)
    cr = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(cr)
    for _ in range(120):
        crack_path(d, rng.uniform(0, W), rng.uniform(0, H), rng.uniform(16, 60), rng, 1)
    for _ in range(12):
        x = rng.uniform(0, W - 240)
        patch = base_asphalt(int(rng.uniform(80, 240)), int(rng.uniform(40, 100)), rng, tone=38)
        im.paste(patch, (int(x), int(rng.uniform(10, H - 110))))
    im = stamp(im, cr.filter(ImageFilter.GaussianBlur(0.4)), (12, 12, 12), 0.9)
    edge = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(edge)
    for y0, y1 in ():                                            # (no grit at the edges: the lot runs straight on)
        for _ in range(1500):
            d.point((rng.uniform(0, W), rng.uniform(y0, y1)), fill=rng.randint(100, 255))
    im = stamp(im, edge.filter(ImageFilter.GaussianBlur(1)), (66, 56, 40), 0.6)
    im.save(os.path.join(OUT, "pic_road_asphalt.png"))
    print("road asphalt", im.size)


def plate():
    from PIL import ImageFont
    im = Image.new("RGB", (256, 128), (214, 206, 176))
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, 252, 124], outline=(40, 40, 60), width=4)
    d.text((128, 22), "MAINE", font=ImageFont.truetype(r"C:/Windows/Fonts/arialbd.ttf", 18), fill=(150, 30, 30), anchor="mm")
    d.text((128, 72), "4KJ 219", font=ImageFont.truetype(r"C:/Windows/Fonts/arialbd.ttf", 54), fill=(30, 34, 70), anchor="mm")
    d.text((128, 112), "VACATIONLAND", font=ImageFont.truetype(r"C:/Windows/Fonts/arial.ttf", 13), fill=(30, 34, 70), anchor="mm")
    rng = random.Random(5)
    px = im.load()
    for y in range(128):                                           # grime
        for x in range(256):
            g = rng.uniform(-12, 6) - 30 * (y / 128.0) ** 3
            px[x, y] = tuple(max(0, min(255, int(c + g))) for c in px[x, y])
    im.save(os.path.join(OUT, "pic_car_plate.png"))


if __name__ == "__main__":
    lot()
    road()
    plate()

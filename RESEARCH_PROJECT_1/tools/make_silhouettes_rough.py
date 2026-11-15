"""First-pass silhouettes of Eileen (1997) and Cas (2001), same photo style as Bug's rough."""
from PIL import Image, ImageDraw, ImageFilter
import random, math

S, W, H = 4, 600, 800
INK, LITE, GAP = 18, 44, 120
OUT = "C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/process/"
P = lambda pts: [(x * S, y * S) for x, y in pts]
E = lambda cx, cy, rx, ry: [(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S]


def backdrop(base, folds=True):
    img = Image.new("L", (W * S, H * S), base)
    d = ImageDraw.Draw(img)
    if folds:
        for x in range(0, W * S, S):
            v = base + 25 * math.sin(x / (S * 38.0)) + 10 * math.sin(x / (S * 11.0))
            d.line([(x, 0), (x, H * S)], fill=int(v), width=S)
    glow = Image.new("L", img.size, 0)
    ImageDraw.Draw(glow).ellipse(E(300, 330, 330, 360), fill=60)
    return Image.composite(Image.new("L", img.size, base + 60), img, glow.filter(ImageFilter.GaussianBlur(120 * S)))


def age(img, name, tint, seed):
    img = img.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.1))
    random.seed(seed)
    px = img.load()
    for y in range(H):
        for x in range(W):
            px[x, y] = max(0, min(255, px[x, y] + random.randint(-14, 14)))
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-120, -80, W + 120, H + 120], fill=255)
    img = Image.composite(img, Image.new("L", (W, H), 40), vig.filter(ImageFilter.GaussianBlur(90)))
    frame = Image.new("L", (W + 60, H + 60), 236)
    frame.paste(img, (30, 30))
    r, g, b = tint
    Image.merge("RGB", [frame.point(lambda v: min(255, int(v * r))), frame.point(lambda v: min(255, int(v * g))),
                        frame.point(lambda v: min(255, int(v * b)))]).save(OUT + name)


def eileen():
    """1997: shoulder-length full 90s hair, long wool coat with the collar turned up, handbag strap, upright."""
    img = backdrop(150, folds=False)                     # plain wall, like a snapshot, not a booth
    d = ImageDraw.Draw(img)
    coat = [(262, 486), (212, 500), (168, 520), (140, 560), (126, 640), (118, 800),
            (482, 800), (474, 640), (460, 560), (432, 520), (388, 500), (338, 486)]     # narrower, square, upright
    d.polygon(P(coat), fill=INK)
    d.polygon(P([(272, 380), (328, 380), (334, 490), (266, 490)]), fill=INK)          # neck
    for sx in (-1, 1):                                   # tall turned-up wool collar hugging the neck
        c = [(300 + sx * 34, 500), (300 + sx * 46, 430), (300 + sx * 78, 446), (300 + sx * 92, 530), (300 + sx * 40, 556)]
        d.polygon(P(c), fill=INK)
        d.line(P([c[1], c[2], c[3], c[4]]), fill=GAP, width=2 * S)
    d.line(P([(300, 556), (300, 800)]), fill=GAP - 60, width=2 * S)                  # coat opening
    for y in (610, 700):                                 # big coat buttons
        d.ellipse(E(318, y, 8, 8), fill=LITE)
    d.line(P([(214, 504), (268, 620), (372, 800)]), fill=GAP - 20, width=3 * S)       # handbag strap across the body
    d.line(P([(214, 504), (268, 620), (372, 800)]), fill=LITE, width=2 * S)
    d.ellipse(E(300, 316, 72, 94), fill=INK)                                          # head
    hair = []                                            # full, layered 90s hair to the shoulders, with volume
    for a in range(180, 361, 3):
        r = math.radians(a)
        wob = 6 * math.sin(a / 9.0)
        hair.append((300 + (122 + wob) * math.cos(r), 312 + (124 + wob) * math.sin(r)))
    hair += [(424, 330), (438, 380), (446, 430), (452, 470), (436, 476), (420, 466), (408, 480), (390, 470),
             (370, 420), (360, 360), (240, 360), (230, 420), (210, 470), (192, 480), (180, 466), (164, 476),
             (148, 470), (154, 430), (162, 380), (176, 330)]
    d.polygon(P(hair), fill=INK)
    d.polygon(P([(272, 360), (328, 360), (334, 470), (266, 470)]), fill=INK)
    age(img, "2026-11-15_eileen_silhouette_rough.png", (1.04, 0.97, 0.84), 11)       # warmer, older print


def cas():
    """2001: high ponytail, hoodie under an open flannel, backpack straps, leaning in a little."""
    img = backdrop(170)
    d = ImageDraw.Draw(img)
    tilt = 10                                            # head and shoulders lean slightly to one side
    body = [(262, 474), (210, 490), (156, 512), (112, 548), (88, 620), (70, 720), (60, 800),
            (540, 800), (530, 720), (512, 620), (488, 548), (444, 512), (390, 490), (338, 474)]
    d.polygon(P(body), fill=INK)
    d.ellipse(E(300, 480, 92, 44), fill=INK)                                          # hood bunched behind the neck
    d.arc(E(300, 482, 92, 44), 200, 340, fill=GAP - 30, width=2 * S)
    d.polygon(P([(272, 384), (328, 384), (336, 486), (264, 486)]), fill=INK)          # neck
    for sx in (-1, 1):                                   # open flannel: lapels and the hoodie between them
        d.line(P([(300 + sx * 40, 520), (300 + sx * 62, 640), (300 + sx * 70, 800)]), fill=GAP - 40, width=2 * S)
        d.line(P([(300 + sx * 120, 520), (300 + sx * 112, 640), (300 + sx * 116, 800)]), fill=LITE + 20, width=6 * S)  # backpack strap
        d.line(P([(300 + sx * 130, 640), (300 + sx * 100, 640)]), fill=LITE + 20, width=3 * S)  # strap buckle
    for sx in (-1, 1):                                   # hoodie drawstrings
        d.line(P([(300 + sx * 14, 520), (300 + sx * 16, 600)]), fill=LITE + 30, width=2 * S)
    hx, hy = 300 + tilt, 320
    d.ellipse(E(hx, hy, 74, 96), fill=INK)                                            # head (hair pulled back: close to the skull)
    d.ellipse(E(hx, hy - 8, 82, 100), fill=INK)
    d.ellipse(E(hx + 30, 206, 30, 24), fill=INK)                                      # high ponytail knot
    tail = [(hx + 40, 200), (hx + 92, 214), (hx + 118, 262), (hx + 124, 330), (hx + 112, 392),
            (hx + 100, 360), (hx + 96, 300), (hx + 80, 250), (hx + 52, 228)]          # tail swinging out to one side
    d.polygon(P(tail), fill=INK)
    d.line(P([(hx + 30, 196), (hx + 52, 212)]), fill=LITE, width=4 * S)               # hair tie
    for sx in (-1, 1):                                   # a few loose strands at the temples
        d.line(P([(hx + sx * 72, 300), (hx + sx * 80, 360), (hx + sx * 74, 400)]), fill=INK, width=3 * S)
    age(img, "2026-11-15_cas_silhouette_rough.png", (1.02, 1.0, 0.93), 23)


eileen()
cas()
# side-by-side sheet with Bug's rough for comparison
names = ["2026-11-15_eileen_silhouette_rough.png", "2026-11-15_cas_silhouette_rough.png", "2026-11-15_bug_silhouette_rough.png"]
ims = [Image.open(OUT + n) for n in names]
sheet = Image.new("RGB", (sum(i.width for i in ims) + 40, ims[0].height + 20), (40, 36, 32))
x = 10
for i in ims:
    sheet.paste(i, (x, 10)); x += i.width + 10
sheet.save(OUT + "2026-11-15_silhouettes_three.png")
print("done")

"""Rough silhouette of Bug as one photo-booth frame (2002): short bob, oversized jacket with a popped collar,
headphones round her neck. Drawn at 4x and shrunk for smooth edges, then aged like a booth print."""
from PIL import Image, ImageDraw, ImageFilter
import random, math

S = 4
W, H = 600, 800
img = Image.new("L", (W * S, H * S), 0)
d = ImageDraw.Draw(img)
P = lambda pts: [(x * S, y * S) for x, y in pts]
E = lambda cx, cy, rx, ry: [(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S]

# booth curtain: soft light-grey gradient with faint folds
for y in range(H * S):
    for_x = 0
for x in range(0, W * S, S):
    v = 170 + 25 * math.sin(x / (S * 38.0)) + 10 * math.sin(x / (S * 11.0))
    d.line([(x, 0), (x, H * S)], fill=int(v), width=S)
glow = Image.new("L", img.size, 0)
ImageDraw.Draw(glow).ellipse(E(300, 330, 330, 360), fill=60)
img = Image.composite(Image.new("L", img.size, 235), img, glow.filter(ImageFilter.GaussianBlur(120 * S)))
d = ImageDraw.Draw(img)

INK = 18      # the figure
CUP = 46      # headphones, a touch lighter so they read against the jacket
GAP = 120     # thin light seams that separate shapes

# oversized jacket: dropped, slouched shoulders, wide body running off the frame
jacket = [(258, 470), (205, 492), (150, 520), (108, 560), (82, 630), (64, 720), (52, 800),
          (548, 800), (536, 720), (518, 630), (492, 560), (450, 520), (395, 492), (342, 470)]
d.polygon(P(jacket), fill=INK)
# neck
d.polygon(P([(270, 390), (330, 390), (338, 482), (262, 482)]), fill=INK)
COLLAR = False   # 2026-11-17, user: "remove the collar from Bug" (the popped collar and the grey triangles by the neck)
# popped collar points either side of the neck, split from the jacket by light seams
for sx in ((-1, 1) if COLLAR else ()):
    c = [(300 + sx * 30, 452), (300 + sx * 62, 432), (300 + sx * 96, 520), (300 + sx * 52, 548)]
    d.polygon(P(c), fill=INK)
    d.line(P([c[1], c[2], c[3]]), fill=GAP, width=2 * S)
# zip line down the front
d.line(P([(300, 560), (302, 800)]), fill=GAP - 50, width=2 * S)
# more detail on the jacket (2026-11-17, user: "add a bit more detail to Bug's clothes"), faint like the zip:
SEAM = GAP - 66
d.line(P([(254, 486), (276, 500), (300, 504), (324, 500), (346, 486)]), fill=SEAM, width=2 * S)       # the neckline
d.rectangle(P([(295, 556), (306, 574)]), outline=SEAM, width=2 * S)                                  # zip pull
for sx in (-1, 1):
    d.line(P([(300 + sx * 128, 514), (300 + sx * 160, 540), (300 + sx * 186, 600), (300 + sx * 200, 690)]),
           fill=SEAM, width=2 * S)                                                                    # dropped shoulder seam
    px0, px1 = (300 + sx * 46, 300 + sx * 116) if sx > 0 else (300 + sx * 116, 300 + sx * 46)
    d.rectangle(P([(px0, 610), (px1, 690)]), outline=SEAM, width=2 * S)                              # chest pocket
    d.line(P([(px0 - 3, 618), (px1 + 3, 618)]), fill=SEAM, width=2 * S)                               # its flap
    d.ellipse(E((px0 + px1) / 2, 628, 3, 3), fill=SEAM)                                               # snap
    for k in range(3):                                                                                # folds at the arm
        y0 = 720 + k * 24
        d.line(P([(300 + sx * (206 - k * 4), y0), (300 + sx * (184 - k * 6), y0 + 14)]), fill=SEAM, width=2 * S)

# headphones round the neck: band behind the neck, two cups resting on the collarbones
d.arc(E(300, 470, 74, 40), 180, 360, fill=CUP, width=9 * S)
for cx in (226, 374):
    d.ellipse(E(cx, 486, 34, 40), fill=GAP)            # light rim so the cup separates
    d.ellipse(E(cx, 486, 30, 36), fill=CUP)
    d.ellipse(E(cx, 486, 14, 18), fill=INK + 8)          # the speaker face

# head
d.ellipse(E(300, 318, 78, 98), fill=INK)
# short bob (2026-11-17, user: "make Bug's hair better and smoother with no background behind it like the
# other two"): one smooth closed curve (Catmull-Rom), round over the crown, straight down past the cheeks to
# blunt ends at the jaw with a slight flick out, and SOLID across behind her neck (no gaps showing through)
def smooth(pts, steps=14):
    out, n = [], len(pts)
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for k in range(steps):
            t = k / steps
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in (0, 1)))
    return out
bob_l = [(300, 194), (250, 200), (208, 226), (188, 268), (184, 320), (186, 368), (182, 398), (170, 414),
         (196, 418), (240, 416), (276, 420)]
bob = bob_l + [(600 - x, y) for x, y in reversed(bob_l)]
d.polygon(P(smooth(bob)), fill=INK)
# the faint grey face outline, matching Cas and Eileen (2026-11-17): cheeks, jaw and chin below the bangs
FACE_LINE = 50
d.arc(E(300, 318, 70, 90), -12, 192, fill=FACE_LINE, width=int(2.5 * S))
# redraw the neck over the seams
d.polygon(P([(270, 380), (330, 380), (336, 470), (264, 470)]), fill=INK)

img = img.resize((W, H), Image.LANCZOS)

# booth print: slight blur, film grain, uneven exposure, white border
img = img.filter(ImageFilter.GaussianBlur(1.1))
random.seed(7)
px = img.load()
for y in range(H):
    for x in range(W):
        px[x, y] = max(0, min(255, px[x, y] + random.randint(-14, 14)))
vig = Image.new("L", (W, H), 0)
ImageDraw.Draw(vig).ellipse([-120, -80, W + 120, H + 120], fill=255)
img = Image.composite(img, Image.new("L", (W, H), 40), vig.filter(ImageFilter.GaussianBlur(90)))
frame = Image.new("L", (W + 60, H + 60), 236)
frame.paste(img, (30, 30))
out = Image.merge("RGB", [frame.point(lambda v: min(255, int(v * 1.02 + 6))), frame, frame.point(lambda v: int(v * 0.93))])
out.save(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/process/2026-11-15_bug_silhouette_rough.png" if COLLAR else
         r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/process/archive/2026-11-17_bug_silhouette_no_collar.png")
print("saved")

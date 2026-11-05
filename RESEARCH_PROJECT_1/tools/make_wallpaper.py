"""Draw the motel room wallpaper: faded cream paper with pairs of thin olive stripes and a
small brown motif between them, yellowed toward the top, with a few water marks. Tiles
seamlessly; the room insides use it instead of the outside plaster (which read as concrete).

Run with normal Python (needs Pillow):  python tools/make_wallpaper.py
Writes textures/wallpaper_motel.jpg (256 x 256) for MI_PS2_room_wall_mat (textures.json).
"""
import os
import random
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 256
PAPER = (196, 184, 152)
STRIPE = (128, 124, 92)
MOTIF = (140, 112, 80)


def main():
    rng = random.Random(3)
    im = Image.new("RGB", (N, N), PAPER)
    d = ImageDraw.Draw(im)
    step = N // 4                                       # 4 stripe pairs across a tile
    for k in range(4):
        x = k * step
        d.line([(x + 2, 0), (x + 2, N)], fill=STRIPE, width=2)
        d.line([(x + 7, 0), (x + 7, N)], fill=STRIPE, width=1)
        cx = x + step / 2 + 2
        for j in range(4):                              # little lozenge motif between stripes
            cy = j * step + step / 2 + (step / 2 if k % 2 else 0)
            cy %= N
            d.polygon([(cx, cy - 6), (cx + 4, cy), (cx, cy + 6), (cx - 4, cy)], outline=MOTIF, width=1)
            d.point((cx, cy), fill=MOTIF)
    px = im.load()
    for y in range(N):                                  # paper grain
        for x in range(N):
            g = rng.uniform(-7, 5)
            px[x, y] = tuple(max(0, min(255, int(c + g))) for c in px[x, y])
    marks = Image.new("L", (N, N), 0)                   # faint water marks (wrapped)
    md = ImageDraw.Draw(marks)
    for _ in range(4):
        x, y, r = rng.uniform(0, N), rng.uniform(0, N), rng.uniform(14, 34)
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                md.ellipse([x + ox - r, y + oy - r * 1.4, x + ox + r, y + oy + r * 1.4], outline=70, width=3)
                md.ellipse([x + ox - r * 0.9, y + oy - r * 1.3, x + ox + r * 0.9, y + oy + r * 1.3], fill=25)
    marks = marks.filter(ImageFilter.GaussianBlur(2))
    im = Image.composite(Image.new("RGB", (N, N), (150, 128, 90)), im, marks)
    im.save(os.path.join(ROOT, "textures", "wallpaper_motel.jpg"), quality=92)
    print("wallpaper -> textures/wallpaper_motel.jpg")


if __name__ == "__main__":
    main()

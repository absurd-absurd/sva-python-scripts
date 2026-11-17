"""The close-up of Cas's wall in Room 104, for the reading screen (clues.json cas_wall; user, 2026-11-17:
every readable is a picture of the real thing). Her pieces from tools/make_photos.py (the sharp hires_ copies),
pinned on the motel wallpaper with red string between them: Eileen's MISSING poster, the lantern note, the
"same night" note, the rattle note, the photo-booth strip of Cas and Bug, the newspaper
clipping, her lake map and a few of her lake photos.

    python make_wall.py   -> export/paper_wall.png (768 x 1024, the reading-screen frame)
Run tools/make_silhouettes.py and tools/make_photos.py first.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "export")
W, H = 768, 1024


def wallpaper(rng):
    """Faded motel wallpaper: a dull green-brown with a faint vertical stripe and grime."""
    im = Image.new("RGB", (W, H), (88, 82, 64))
    d = ImageDraw.Draw(im)
    for x in range(0, W, 24):
        d.rectangle((x, 0, x + 10, H), fill=(94, 88, 70))
    px = im.load()
    for _ in range(W * H // 3):
        x, y = rng.randrange(W), rng.randrange(H)
        r, g, b = px[x, y]
        v = rng.randint(-8, 8)
        px[x, y] = (r + v, g + v, b + v)
    shade = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shade).ellipse((-200, -150, W + 200, H + 150), fill=255)
    return Image.composite(im, Image.new("RGB", (W, H), (40, 36, 28)), shade.filter(ImageFilter.GaussianBlur(160)))


def piece(name, width, spin, rng):
    """One item, scaled to width, turned a little, with a soft shadow; returns (image, its pin point)."""
    path = os.path.join(EXPORT, name + ".png")
    im = Image.open(path).convert("RGBA")
    im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    im = im.rotate(spin, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (im.width + 20, im.height + 20), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 110), (10, 14), im.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(5))
    sh.alpha_composite(im, (6, 4))
    return sh


def main():
    rng = random.Random(17)
    wall = wallpaper(rng).convert("RGBA")
    layout = [  # name, width px, spin deg, x, y (top-left), pinned?
        ("pic_lake_dusk", 170, 4, 30, 40, False), ("pic_lake_fog", 170, -3, 220, 26, False),
        ("pic_dock", 170, 2, 420, 46, False), ("pic_lake_night", 160, -5, 590, 70, False),
        ("hires_pic_missing_eileen", 250, -2, 40, 230, True),
        ("hires_pic_note_lights", 190, 3, 320, 250, True),
        ("pic_lanterns", 170, -4, 540, 250, False),
        ("hires_pic_photo_strip", 86, 3, 560, 470, False),
        ("hires_pic_note_night", 170, -5, 330, 520, True),
        ("pic_clipping", 200, 4, 40, 640, True),
        ("hires_pic_note_rattle", 160, 6, 290, 760, True),
        ("pic_lake_map", 230, 2, 480, 760, True),
    ]
    pins = {}
    for name, width, spin, x, y, pinned in layout:
        im = piece(name, width, spin, rng)
        wall.alpha_composite(im, (x, y))
        cx = x + im.width // 2
        if pinned:
            pins[name] = (cx, y + 18)
        else:                                           # taped: a strip of yellowed tape across the top
            tape = Image.new("RGBA", (70, 22), (214, 200, 150, 170))
            tape = tape.rotate(rng.uniform(-8, 8), expand=True, resample=Image.BICUBIC)
            wall.alpha_composite(tape, (cx - tape.width // 2, y + 2))
            if name in ("pic_lanterns", "hires_pic_photo_strip"):
                pins[name] = (cx, y + 14)
    d = ImageDraw.Draw(wall)
    for a, b in (("hires_pic_missing_eileen", "hires_pic_note_lights"), ("hires_pic_note_lights", "pic_lanterns"),
                 ("hires_pic_note_lights", "hires_pic_note_night"),
                 ("hires_pic_note_night", "pic_lake_map"), ("hires_pic_note_rattle", "pic_lake_map")):
        (x0, y0), (x1, y1) = pins[a], pins[b]
        sag = [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + 22 * math.sin(math.pi * t)) for t in [k / 20 for k in range(21)]]
        d.line(sag, fill=(150, 20, 18, 255), width=3)
    for name, (x, y) in pins.items():                  # red pin heads
        d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(170, 24, 20, 255))
        d.ellipse((x - 3, y - 5, x + 1, y - 1), fill=(240, 150, 140, 255))
    mask = Image.new("L", (W, H), 0)                    # the close-up's edge: a slightly rounded frame
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, W - 1, H - 1), radius=10, fill=255)
    wall.putalpha(mask)
    wall.save(os.path.join(EXPORT, "paper_wall.png"))
    print("wall close-up written")


if __name__ == "__main__":
    main()

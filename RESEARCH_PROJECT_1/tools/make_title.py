"""The title, MARROW, as a picture the HUD draws over the title screen's camera (see-through round the letters).

    python make_title.py [style]   -> export/title.png (2400 x 600)
    python make_title.py --sheet   -> process/2026-11-17_title_options.png (each style over each background)

Styles: serif (Baskerville, wide-spaced), condensed (Bodoni condensed, tall), thin (Century Gothic, wide).
Letters are off-white with a faint red bleed and grain, like a title on a worn PS2 disc's boot screen.
"""
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "export")
WF = "C:/Windows/Fonts/"
STYLES = {"serif": ("BASKVILL.TTF", 300, 70), "condensed": ("BOD_CR.TTF", 360, 40), "thin": ("GOTHIC.TTF", 260, 80)}
W, H = 2400, 600


def title(style):
    font_file, size, spacing = STYLES[style]
    f = ImageFont.truetype(WF + font_file, size)
    text = "MARROW"
    widths = [f.getlength(c) for c in text]
    total = sum(widths) + spacing * (len(text) - 1)
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    x = (W - total) / 2
    for c, w in zip(text, widths):
        d.text((x, H / 2), c, font=f, fill=255, anchor="lm")
        x += w + spacing
    rng = random.Random(4)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bleed = mask.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.55))       # a red glow bleeding out
    img.paste((150, 18, 14, 255), (6, 3), bleed)
    letters = Image.new("RGBA", (W, H), (226, 220, 206, 255))
    px = letters.load()
    for _ in range(W * H // 5):                                                              # grain in the letters
        xx, yy = rng.randrange(W), rng.randrange(H)
        v = rng.randint(-40, 10)
        r, g, b, a = px[xx, yy]
        px[xx, yy] = (r + v, g + v, b + v, a)
    img.paste(letters, (0, 0), mask)
    return img


def vignette():
    """export/title_vignette.png: black, see-through in the middle, dark at the edges, and a darker band over the
    lower part of the screen behind the menu (the user's approved mockup)."""
    w, h = 1920, 1080
    v = Image.new("L", (w, h), 0)
    ImageDraw.Draw(v).ellipse((-w * 0.15, -h * 0.25, w * 1.15, h * 1.2), fill=255)
    v = v.filter(ImageFilter.GaussianBlur(160))
    alpha = v.point(lambda x: int((255 - x) * 0.85))
    band = Image.new("L", (w, h), 0)
    bd = ImageDraw.Draw(band)
    for y in range(int(h * 0.55), h):
        bd.line((0, y, w, y), fill=int(150 * (y - h * 0.55) / (h * 0.45)))
    from PIL import ImageChops
    alpha = ImageChops.lighter(alpha, band)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    out.putalpha(alpha)
    out.save(os.path.join(EXPORT, "title_vignette.png"))


def sheet():
    D = r"C:/Users/fayth/Documents/Unreal Projects/RP1_Horror/Saved/Screenshots/WindowsEditor/"
    bgs = [("motel", Image.open(D + "tv_motel.png")), ("lake", Image.open(D + "tv_lake.png")), ("trail", Image.open(D + "tv_trail.png"))]
    tw, th = 640, 360
    out = Image.new("RGB", (len(STYLES) * (tw + 10) + 10, len(bgs) * (th + 10) + 10), (20, 20, 22))
    for j, (bname, bg) in enumerate(bgs):
        for i, style in enumerate(STYLES):
            tile = bg.convert("RGBA").resize((tw, th))
            t = title(style).resize((int(tw * 0.8), int(tw * 0.8 * H / W)), Image.LANCZOS)
            tile.alpha_composite(t, ((tw - t.width) // 2, int(th * 0.32 - t.height / 2)))
            ImageDraw.Draw(tile).text((14, th - 26), f"{i + 1}{'ABC'[j]}: {style} / {bname}", fill=(200, 200, 200, 255))
            out.paste(tile.convert("RGB"), (10 + i * (tw + 10), 10 + j * (th + 10)))
    path = os.path.join(ROOT, "process", "2026-11-17_title_options.png")
    out.save(path)
    print("options ->", path)


if __name__ == "__main__":
    if "--sheet" in sys.argv:
        sheet()
    else:
        style = sys.argv[1] if len(sys.argv) > 1 else "serif"
        title(style).save(os.path.join(EXPORT, "title.png"))
        vignette()
        print("title ->", style)

"""The back of the postcard that brings Bug to Marrow Falls (opening text; STORY.md).

    python make_postcard.py  -> export/postcard_back.png (900 x 600)

"i miss you bug - cas" in the wrong hand (Zeyada: the thing wrote it), postmarked Marrow Falls Oct 9 2002,
a 37-cent flag stamp. The motel's printed side is just its name (user, 2026-11-17: no sub-line).
Made from the font-comparison sample (process/2026-11-16_postcard_back_fonts.png)."""
import math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FD = os.path.join(ROOT, "fonts") + os.sep
WF = "C:/Windows/Fonts/"
FONTS = [("Zeyada", "Zeyada.ttf", 80), ("Reenie Beanie", "ReenieBeanie.ttf", 88),
         ("Nothing You Could Do", "NothingYouCouldDo.ttf", 62), ("Rock Salt", "RockSalt-Regular.ttf", 50),
         ("Just Me Again Down Here", "JustMeAgainDownHere.ttf", 86)]
W, H = 900, 600
INK = (38, 34, 40)
PRINT = (95, 80, 62)


def card(font_file, size, seed):
    rng = random.Random(seed)
    im = Image.new("RGB", (W, H), (226, 214, 186))
    px = im.load()
    for y in range(H):                                   # paper grain + yellowed edges
        for x in range(W):
            e = min(x, y, W - 1 - x, H - 1 - y)
            age = max(0, 30 - e) * 0.9
            n = rng.randint(-7, 7)
            r, g, b = px[x, y]
            px[x, y] = (int(r + n - age), int(g + n - age * 1.1), int(b + n - age * 1.5))
    d = ImageDraw.Draw(im)
    serif = ImageFont.truetype(WF + "georgia.ttf", 15)
    small = ImageFont.truetype(WF + "arial.ttf", 11)
    bold = ImageFont.truetype(WF + "arialbd.ttf", 22)
    # printed parts (the motel's own card)
    d.text((30, 26), "MARROW FALLS MOTEL", font=serif, fill=PRINT)
    d.text((W // 2 - 50, 22), "POST CARD", font=bold, fill=PRINT)
    d.line((W * 0.56, 90, W * 0.56, H - 40), fill=PRINT, width=2)                 # divided back
    for k in range(4):                                                              # address lines
        y = 300 + k * 58
        d.line((W * 0.56 + 30, y, W - 40, y), fill=PRINT, width=1)
    d.text((30, H - 30), "Photo: Black Hollow Lake at dusk  -  Printed in U.S.A.", font=small, fill=PRINT)
    # stamp: 37c flag (US rate from June 30 2002)
    sx, sy = W - 135, 80
    d.rectangle((sx, sy, sx + 95, sy + 115), fill=(236, 230, 214))
    for k in range(0, 96, 7):                                                       # perforation
        for yy in (sy, sy + 115):
            d.ellipse((sx + k - 3, yy - 3, sx + k + 3, yy + 3), fill=(226, 214, 186))
    d.rectangle((sx + 9, sy + 9, sx + 86, sy + 86), fill=(150, 40, 40))
    for k in range(4):
        d.rectangle((sx + 9, sy + 15 + k * 18, sx + 86, sy + 23 + k * 18), fill=(232, 226, 214))
    d.rectangle((sx + 9, sy + 9, sx + 44, sy + 45), fill=(40, 50, 100))
    d.text((sx + 10, sy + 92), "USA 37", font=ImageFont.truetype(WF + "arialbd.ttf", 13), fill=(40, 40, 40))
    # postmark over the stamp
    pm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pm)
    cx, cy = sx - 80, sy + 60
    pd.ellipse((cx - 58, cy - 58, cx + 58, cy + 58), outline=(30, 30, 50, 150), width=3)
    pmf = ImageFont.truetype(WF + "arialbd.ttf", 13)
    pd.text((cx - 44, cy - 32), "MARROW FALLS", font=pmf, fill=(30, 30, 50, 150))
    pd.text((cx - 32, cy - 8), "OCT 09", font=pmf, fill=(30, 30, 50, 150))
    pd.text((cx - 19, cy + 14), "2002", font=pmf, fill=(30, 30, 50, 150))
    for k in range(5):  # cancel waves
        y = cy - 30 + k * 14
        pts = [(cx + 62 + t, y + 5 * math.sin(t / 9.0)) for t in range(0, 170, 4)]
        pd.line(pts, fill=(30, 30, 50, 140), width=3)
    im.paste(pm, (0, 0), pm)
    # the handwriting: one line on the message side; the address in the same hand
    hf = ImageFont.truetype(FD + font_file, size)
    af = ImageFont.truetype(FD + font_file, int(size * 0.55))
    msg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(msg)
    md.text((60, 230), "i miss you bug", font=hf, fill=INK + (235,))
    md.text((230, 230 + int(size * 1.25)), "- cas", font=hf, fill=INK + (235,))
    msg = msg.rotate(-3, resample=Image.BICUBIC, center=(200, 280))
    for k, line in enumerate(["bug", "(your street)", "(your town)"]):
        md2 = ImageDraw.Draw(msg)
        bb = md2.textbbox((0, 0), line, font=af)
        md2.text((W * 0.56 + 40, 300 + k * 58 - bb[3] - 6), line, font=af,
                 fill=INK + (235,) if k == 0 else (120, 110, 100, 150))
    im.paste(msg, (0, 0), msg)
    return im.filter(ImageFilter.GaussianBlur(0.5))



if __name__ == "__main__":
    out = os.path.join(ROOT, "export", "postcard_back.png")
    im = card("Zeyada.ttf", 80, 3)
    im.save(out)
    im.save(os.path.join(ROOT, "export", "paper_postcard.png"))      # the opening shows this (unreal/import_papers.py)
    print("postcard ->", out)

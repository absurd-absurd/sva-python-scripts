"""The card the Chapter 2 opening shows after its text: Mom's MISSING poster (Chapter 1's
export/hires_pic_missing_eileen.png), laid a little crooked on a dark table, in the opening's
landscape card shape (3:2). Writes export/ch2_card.png (unreal/ch2_ui.py imports it as T_Ch2_Card)."""
import os
from PIL import Image

RP1 = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "export", "ch2_card.png")
poster = Image.open(os.path.join(RP1, "export", "hires_pic_missing_eileen.png")).convert("RGBA")
poster = poster.resize((int(600 * 0.7), int(800 * 0.7)), Image.LANCZOS).rotate(-3, expand=True, resample=Image.BICUBIC)
card = Image.new("RGBA", (900, 600), (14, 12, 11, 255))
card.alpha_composite(poster, ((900 - poster.width) // 2, (600 - poster.height) // 2))
card.convert("RGB").save(OUT)
print("wrote", OUT)

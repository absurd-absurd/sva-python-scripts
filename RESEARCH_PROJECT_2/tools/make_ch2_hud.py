"""Write Chapter 2's HUD logic (BP_Ch2HUD's Event Graph) as paste-able node text.

    python make_ch2_hud.py > hud_ch2.txt

It is Chapter 1's generator (RESEARCH_PROJECT_1/tools/make_interact_nodes.py, the whole interaction
system: E to read, the reading screen in the right hand, objective lines, the flashlight, the title
screen, the opening, pause, the ending) with Chapter 2's numbers and words swapped in:
  - the opening text from RESEARCH_PROJECT_2/clues.json, and the card after it = Eileen's MISSING
    poster (T_Ch2_Card, unreal/ch2_ui.py) instead of the postcard
  - the title camera pushes north up the lakebed from under the dock
  - the ending: "That's not her handwriting." -> "Eleven months later." -> the final shot (BP_FinalShot
    placed in the Lakebed showing the i miss you bug postcard) -> back to the Lakebed title screen
"""
import io
import json
import os
import sys
from contextlib import redirect_stdout

RP1_TOOLS = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/tools"
RP2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(RP1_TOOLS, "make_interact_nodes.py")
TEXT = json.load(open(os.path.join(RP2, "clues.json"), encoding="utf-8"))["game_text"]
START = json.load(open(os.path.join(RP2, "export", "sets_lakebed.json")))["start"]

src = open(GEN, encoding="utf-8").read()
SWAPS = [
    ('os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "clues.json")', repr(os.path.join(RP2, "clues.json"))),
    ('"/Game/Horror/Interact/BP_HorrorHUD.BP_HorrorHUD:EventGraph"', '"/Game/Chapter2/Blueprints/BP_Ch2HUD.BP_Ch2HUD:EventGraph"'),
    ('POSTCARD_TEX = "/Game/Horror/UI/T_Paper_Postcard.T_Paper_Postcard"', 'POSTCARD_TEX = "/Game/Chapter2/UI/T_Ch2_Card.T_Ch2_Card"'),
    ('END_LINE = "this isn\'t Cas."', "END_LINE = " + repr(TEXT["ending_last_line"])),
    ('draw("One year later.",', "draw(" + repr(TEXT["ending_card"]) + ","),
    ('LEVEL_NAME = "MotelLake"', 'LEVEL_NAME = "Lakebed"'),
    ("PUSH_FROM, PUSH_SPEED, PUSH_MAX = (1500.0, 14150.0, 260.0), 6.5, 800.0",
     "PUSH_FROM, PUSH_SPEED, PUSH_MAX = ({:.1f}, {:.1f}, {:.1f}), 5.0, 700.0".format(START[0], START[1] - 500, START[2] + 60)),
]
for a, b in SWAPS:
    if a not in src:
        sys.exit("Chapter 1's generator changed, can't find: " + a)
    src = src.replace(a, b)

ns = {"__name__": "ch2_hud", "__file__": GEN}
exec(compile(src, GEN, "exec"), ns)
out = ns["hud_graph"]().text()
import re
multi = [m.group(1) for m in re.finditer(r'Direction="EGPD_Output",PinType\.PinCategory="exec"[^\n]*?LinkedTo=\(([^)]*)\)', out)
         if len([x for x in m.group(1).split(",") if x.strip()]) > 1]
if multi:
    sys.exit(f"exec output wired to more than one node: {multi[:3]}")
sys.stdout.reconfigure(encoding="utf-8")
print(out)

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

# ---- the hunter (Chapter 2): it swims round its ring (M_Ch2_Sway Orbit, so its head is worked out here
# the same way: the ring centre + its head's spot turned by time x Orbit). Come within CATCH_DIST of its
# head and it has you: the growl, the picture warps, and you're back at the checkpoint before its ring.
SETS = json.load(open(os.path.join(RP2, "export", "sets_lakebed.json")))
HUNT_C = SETS["hunter"]
HUNTER_R, HEAD_FWD, ORBIT = 900.0, 220.0, 0.07          # make_lakebed HUNTER_R; its head is ~2.2 m ahead of the ring point
CATCH_DIST = 380.0
CHECKPOINT = SETS["checkpoint"]
CAUGHT_LINE = "It had me... Its light. I can't let that light find me."


def hunter_logic(g):
    MATH, STATICS, ACTOR, HUD = ns["MATH"], ns["STATICS"], ns["ACTOR"], ns["HUD"]
    add = lambda x, y: g.pure(MATH, "Add_DoubleDouble", [("A", "real", x), ("B", "real", y)])
    sub = lambda x, y: g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", x), ("B", "real", y)])
    mulr = lambda x, y: g.pure(MATH, "Multiply_DoubleDouble", [("A", "real", x), ("B", "real", y)])
    g.row(-12000, 9000)
    tick = g.event(ACTOR, "ReceiveTick", [("DeltaSeconds", "float")])
    ang = g.mul(g.now(), ORBIT)
    c = g.pure(MATH, "Cos", [("A", "real", ang)])
    s_ = g.pure(MATH, "Sin", [("A", "real", ang)])
    hx = add(HUNT_C[0], sub(g.mul(c, HUNTER_R), g.mul(s_, HEAD_FWD)))
    hy = add(HUNT_C[1], add(g.mul(s_, HUNTER_R), g.mul(c, HEAD_FWD)))
    head = g.pure(MATH, "MakeVector", [("X", "real", hx), ("Y", "real", hy), ("Z", "real", HUNT_C[2])], ty="vector")
    pawn = g.pure(HUD, "GetOwningPawn", ty="actor")
    ploc = g.pure(ACTOR, "K2_GetActorLocation", ty="vector", target=(pawn, "actor"))
    dist = g.pure(MATH, "VSize", [("A", "vector", g.pure(MATH, "Subtract_VectorVector", [("A", "vector", head), ("B", "vector", ploc)], ty="vector"))])
    near = g.pure(MATH, "Less_DoubleDouble", [("A", "real", dist), ("B", "real", CATCH_DIST)], ty="bool")
    rested = g.pure(MATH, "Greater_DoubleDouble", [("A", "real", g.now()), ("B", "real", add(g.get("CatchT", "real"), 4.0))], ty="bool")
    playing = g.not_(g.pure(MATH, "BooleanOR", [("A", "bool", g.get("Title", "bool")), ("B", "bool", g.pure(MATH, "BooleanOR", [
        ("A", "bool", g.get("Opening", "bool")), ("B", "bool", g.get("Ending", "bool"))], ty="bool"))], ty="bool"))
    go = g.pure(MATH, "BooleanAND", [("A", "bool", near), ("B", "bool", g.pure(MATH, "BooleanAND", [("A", "bool", rested), ("B", "bool", playing)], ty="bool"))], ty="bool")
    yes, _ = g.branch(go, tick.then)
    a = g.set("CatchT", "real", g.now(), yes).then
    a = g.call(STATICS, "SpawnSound2D", a, [("Sound", "sound", ns["SND"]("growl")), ("VolumeMultiplier", "float", ns["VOL"]["growl"])]).then
    a = g.set("WarpUntil", "real", add(g.now(), 1.5), a).then
    cp = g.pure(MATH, "MakeVector", [("X", "real", CHECKPOINT[0]), ("Y", "real", CHECKPOINT[1]), ("Z", "real", CHECKPOINT[2])], ty="vector")
    a = g.call(ACTOR, "K2_SetActorLocation", a, [("NewLocation", "vector", cp), ("bSweep", "bool", False), ("bTeleport", "bool", True)],
               target=(g.pure(HUD, "GetOwningPawn", ty="actor"), "actor")).then
    a = g.set("Toast", "string", CAUGHT_LINE, a).then
    g.set("ToastTime", "real", g.now(), a)


graph = ns["hud_graph"]()
hunter_logic(graph)
out = graph.text()
import re
multi = [m.group(1) for m in re.finditer(r'Direction="EGPD_Output",PinType\.PinCategory="exec"[^\n]*?LinkedTo=\(([^)]*)\)', out)
         if len([x for x in m.group(1).split(",") if x.strip()]) > 1]
if multi:
    sys.exit(f"exec output wired to more than one node: {multi[:3]}")
sys.stdout.reconfigure(encoding="utf-8")
print(out)

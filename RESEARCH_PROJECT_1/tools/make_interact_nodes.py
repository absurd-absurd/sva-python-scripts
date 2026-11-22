"""Write the Blueprint logic for the interaction system as paste-able node text.

    python make_interact_nodes.py hud   > hud.txt    (paste into BP_HorrorHUD's Event Graph)
    python make_interact_nodes.py door  > door.txt   (paste into BP_Examinable's Event Graph)

Same idea as make_bob_run_nodes.py: Unreal's Python can't add Blueprint nodes, but the graph
editor accepts nodes pasted as text. The assets and variables come from unreal/interact_setup.py.

BP_HorrorHUD
  Event Draw HUD (every frame):
    aim line 2.6 m from the camera -> Focus (clues have a slightly bigger invisible HitBox) = the BP_Examinable you look at (or nothing)
    (a clue you spotted keeps the prompt when you look away, until you use it or walk 3 m off)
    draw the objective (top left), the corner map (top right) and the latest message for 3 s (lower left)
    Reading?      -> dark screen with the page's title and text, "[E] Close"
    Journal open? -> dark screen with every journal line, "[Tab] Close"
    otherwise     -> "[E] Examine" (or the object's own Prompt) on a dark box when looking at something
  E:   close the page / journal, or use Focus:
         locked (NeedsKey not in Keys) -> show LockedText
         else -> open its page (Body), and the first time: journal line, key, objective;
                 doors swing open, pickups disappear
  Tab: nothing (the journal was switched off 2026-11-22; its screen code stays but never opens)
  M:   open / close the full torn-paper map; pauses the game while it's open
  flashlight flicker (every frame, top of Draw HUD): flutters, short cut-outs, sometimes a hit to
  bring it back (CS_FlashHit camera jolt); Fear in MPC_Horror makes it worse
  Movement and mouse look are frozen while a page or the journal is open.
BP_Examinable
  Event Tick: once Opened, Hinge turns smoothly to OpenAngle (the door swings).
"""
import json
import os
import sys
import uuid

K2 = "/Script/BlueprintGraph."
MATH, SYS, STR, STATICS = ("/Script/Engine.KismetMathLibrary", "/Script/Engine.KismetSystemLibrary",
                           "/Script/Engine.KismetStringLibrary", "/Script/Engine.GameplayStatics")
ACTOR, HUD, PC, CAM, CTRL, SCENE = ("/Script/Engine.Actor", "/Script/Engine.HUD", "/Script/Engine.PlayerController",
                                    "/Script/Engine.PlayerCameraManager", "/Script/Engine.Controller",
                                    "/Script/Engine.SceneComponent")
EX_CLASS = "/Script/Engine.BlueprintGeneratedClass'/Game/Horror/Interact/BP_Examinable.BP_Examinable_C'"
FONT = "/Game/Horror/UI/F_HUD_Italic.F_HUD_Italic"            # Bug's voice: Ink Free (made by interact_setup.py)
# the hand a paper is written in (clues.json "hand" -> BP_Examinable.Hand -> HUD.ReadHand), and how big
# its body text is drawn on the reading screen (each font sits at a different size at the same scale)
HANDS = [("cas", "/Game/Horror/UI/F_Hand_Cas.F_Hand_Cas", 0.5, "(R=0.020,G=0.030,B=0.090,A=0.950000)"),    # Rock Salt, blue-black pen
         ("wrong", "/Game/Horror/UI/F_Hand_Wrong.F_Hand_Wrong", 1.15, "(R=0.035,G=0.012,B=0.010,A=0.950000)"),  # Zeyada, near-black
         ("print", "/Game/Horror/UI/F_Hand_Print.F_Hand_Print", 0.48, "(R=0.030,G=0.028,B=0.030,A=0.900000)"),  # Courier, typewriter
         ("none", FONT, 1.0, "(R=0.0,G=0.0,B=0.0,A=0.000000)")]   # a picture with its words in it (the keys): write nothing
INK = "(R=0.030,G=0.028,B=0.035,A=0.950000)"     # writing with no hand, on paper
# the sheet a paper is shown on (clues.json "paper" -> BP_Examinable.Paper -> HUD.ReadPaper; tools/make_papers.py)
PAPERS = [(k, f"/Game/Horror/UI/T_Paper_{k.capitalize()}.T_Paper_{k.capitalize()}")
          for k in ("stationery", "notebook", "typed", "ledger", "scrap", "key_office", "key_gate", "key_boathouse", "register", "wall", "torn")]
PAPER_H, PAPER_ASPECT, PAPER_TOP = 0.92, 0.75, 0.04       # sheet height / width:height / top, x screen height
PAIR_H, PAIR_TOP = 0.86, 0.025                          # two sheets: height / top (x screen height); [E] Close under them
PAIR_GAP = 0.03                                           # gap between two sheets side by side, x screen height
PAPER_TEXT_X, PAPER_TEXT_Y = 0.11, 0.15                   # where the writing starts: x screen height in, x sheet height down
TEXT = "(R=0.78,G=0.75,B=0.68,A=1.000000)"                   # warm off-white
DIM = "(R=0.55,G=0.53,B=0.5,A=1.000000)"
DARK = "(R=0.004,G=0.004,B=0.006,A=0.930000)"
SHADOW = "(R=0.0,G=0.0,B=0.0,A=0.850000)"
PROMPT_BOX = "(R=0.0,G=0.0,B=0.0,A=0.550000)"     # dark box behind "[E] Examine"
SCRAP_TEX = "/Game/Horror/UI/T_PromptScrap.T_PromptScrap"   # torn paper scrap behind the prompt (tools/make_map.py)
INK = "(R=0.03,G=0.025,B=0.035,A=0.95)"                  # dark pen, for text on paper
MAP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "layout.json")))["map"]
MAP_SIZE = MAP["x_max"] - MAP["x_min"]   # cm the whole map picture covers (it's square)
MAP_VIEW = 4500.0              # cm of the world shown in the corner window
MAP_SCREEN = 0.18              # corner window size, as a fraction of screen height (small, out of the way)
MAP_TEX = "/Game/Horror/UI/T_Map.T_Map"
MARKER_TEX = "/Game/Horror/UI/T_MapMarker.T_MapMarker"
MAP_FRAME_TEX = "/Game/Horror/UI/T_MapFrame.T_MapFrame"   # torn edge round the corner map
FRAME_HOLE = 0.08                                          # = FRAME_HOLE in tools/make_map.py
WHITE = "(R=1.0,G=1.0,B=1.0,A=1.0)"
# the opening (2026-11-17, STORY.md): black screen, the opening text typing itself out in Bug's hand, then the
# postcard; [E] fades into the parking lot. Text = clues.json game_text.opening minus its last line (the
# postcard shows that, in the thing's hand); interact_setup.py puts it in the HUD's OpeningText.
OPEN_CPS, OPEN_DELAY = 15.0, 1.5        # slower (user, 2026-11-17)                    # typing speed (characters a second), black before it starts
_OPEN = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "clues.json"),
                       encoding="utf-8"))["game_text"]["opening"].rsplit("\n\n", 1)[0]
OPEN_T_TEXT = OPEN_DELAY + len(_OPEN) / OPEN_CPS     # typing done
OPEN_T_CARD = OPEN_T_TEXT + 0.7                      # the postcard appears
OPEN_T_CARD_IN = 1.8                                # the postcard fades in over this long
OPEN_T_GO = OPEN_T_CARD + OPEN_T_CARD_IN + 1.0                        # "[E] Continue"
OPEN_FADE = 1.6                                      # seconds to fade from black into the game after E
POSTCARD_TEX = "/Game/Horror/UI/T_Paper_Postcard.T_Paper_Postcard"   # tools/make_postcard.py
BLACK = "(R=0.0,G=0.0,B=0.0,A=1.0)"
# the ending (STORY.md): close the last page (a clue with "ends": true) -> Bug's line -> cut to black ->
# "One year later." -> the final shot (BP_FinalShot's camera on the payphone, Bug's MISSING poster now on it,
# unreal/final_shot.py) -> black -> the game quits. Times in seconds from closing the page.
END_LINE = "this isn't Cas."
END_T_LINE, END_T_BLACK = 0.6, 3.4                  # her line shows, then cut to black
END_T_YEAR, END_T_YEAR_OUT = 4.4, 7.6               # "One year later." fades in / is gone
END_T_SHOT, END_SHOT_FADE = 8.2, 2.0                 # the final shot, fading up from black
END_T_OUT, END_T_QUIT = 17.0, 20.0                   # cut to black, then quit
LEVEL_NAME = "MotelLake"                             # the ending reloads it -> the title screen
END_WARP = 1.0                                       # the warp: this long, right before the cut (user 2026-11-22)
FINAL_CLASS = "/Game/Horror/Interact/BP_FinalShot.BP_FinalShot_C"
# the title screen (2026-11-17): BP_TitleShot's camera on the foggy lake, the MARROW lettering (T_Title,
# tools/make_title.py "thin"), [E] Start / [C] Controls / [Q] Quit; Controls shows the key list
TITLE_CLASS = "/Game/Horror/Interact/BP_TitleShot.BP_TitleShot_C"
TITLE_TEX = "/Game/Horror/UI/T_Title.T_Title"
TITLE_FADE = 2.5                                     # the title fades up from black when the game starts
MENU_FONT = "/Game/Horror/UI/F_Menu.F_Menu"          # Century Gothic, like the title (interact_setup.py)
VIGNETTE_TEX = "/Game/Horror/UI/T_TitleVignette.T_TitleVignette"   # dark edges + a darker band low down (make_title.py)
TITLE_RED = "(R=0.55,G=0.06,B=0.05,A=0.85)"
PUSH_FROM, PUSH_SPEED, PUSH_MAX = (1500.0, 14150.0, 260.0), 6.5, 800.0   # the slow push down the dock (cm/s, cm)


def _menu_width(text, scale):
    """Screen width of text in the menu font, as a fraction of the screen height (the HUD draws the size-40
    font at TEXT_SCALE * height * scale; Unreal's 40 pt is 40 * 96/72 px)."""
    from PIL import ImageFont
    return ImageFont.truetype("C:/Windows/Fonts/GOTHIC.TTF", int(40 * 96 / 72)).getlength(text) * TEXT_SCALE * scale


MENU = [("E", "S T A R T"), ("C", "C O N T R O L S"), ("Q", "Q U I T")]
MENU_SCALE = 1.05
# the controls page (2026-11-17 second pass): two groups, each key drawn as a keycap
CONTROLS_MOVE = [(["W", "A", "S", "D"], "Walk"), (["Mouse"], "Look"), (["Shift"], "Run"), (["Space"], "Jump")]
CONTROLS_USE = [(["E"], "Examine, read, use"), (["F"], "Flashlight"), (["M"], "Map"), (["Esc", "P"], "Pause")]   # no Journal (user 2026-11-22)
# the pause menu (Esc; P too, since Esc stops play in the editor): key label, item, hit-box name
PAUSE_MENU = [("ESC", "R E S U M E", "P_RESUME"), ("C", "C O N T R O L S", "C"), ("Q", "Q U I T", "Q")]
CONTROLS = [(" ".join(k), w) for k, w in CONTROLS_MOVE + CONTROLS_USE]
MENU_HOVER = "(R=0.85,G=0.22,B=0.18,A=1.0)"         # a menu item under the mouse
CAP_FILL, CAP_EDGE = "(R=0.06,G=0.06,B=0.07,A=0.85)", "(R=0.55,G=0.5,B=0.45,A=0.9)"
MAP_TINT = "(R=0.8,G=0.78,B=0.75,A=1.0)"      # solid paper (it was half see-through; with the torn edge the overlap showed)
MARKER_TINT = "(R=1.0,G=1.0,B=1.0,A=0.8)"
MAP_FULL_TEX = "/Game/Horror/UI/T_MapFull.T_MapFull"
MAP_BIG = 0.96                 # the M screen: torn-paper map this tall (fraction of screen height), centred
MAP_FULL = 0.76                # ... and this tall, near the top, while her first-time line shows under it
import re as _re
_FL = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "unreal", "flashlight.py"), encoding="utf-8").read()
FLASH_INTENSITY = float(_re.search(r"^INTENSITY = ([0-9.]+)", _FL, _re.M).group(1))   # same as flashlight.py
MPC_PATH = "/Game/Horror/Materials/MPC_Horror.MPC_Horror"
HIT_SHAKE = "/Game/Horror/Player/CS_FlashHit.CS_FlashHit_C"
# flashlight flicker, calm -> afraid (Fear 0 -> 1 in MPC_Horror)
FLICK_GAP = ((2.5, 6.0), (0.2, 0.8))    # seconds between flickers (random in range)
FLICK_OFF = (0.25, 0.55)                # share of flickers that are a full cut-out
FLUTTER = (0.1, 0.4)                    # how long a flutter lasts (s)
CUTOUT = (0.3, 0.8)                     # how long a cut-out lasts (s); under a second
HIT_CHANCE = 0.75                       # share of cut-outs that end with a hit (camera jolt)
TEXT_SCALE = 0.0008            # text size = screen height * this; the font is rendered at size 40 (interact_setup.py),
                               # so this is 0.8 at 1000 px tall - same size as before (size 10 x 3.2) but sharp
LATE_AFTER, LATE_FLASH = "boathouse_note", 0.5   # after reading this clue, warp flashes keep coming (MPC WarpFlash level)
DOCK_X, DOCK_HW, DOCK_Y0 = 1500.0, 140.0, 14560.0   # the dock (maya/make_lake.py dock(); traced 2026-11-22): on it after LATE_AFTER = all warped
WARP_AFTER = 4.5               # seconds of warp flashes after you put down a page in the wrong hand
REACH, NEAR = 330.0, 40.0      # aim line from 40 cm in front of the eyes (outside the capsule) to 2.6 m
STICKY = 300.0                 # a spotted clue keeps its prompt until used, within 3 m


def gid():
    return uuid.uuid4().hex.upper()


def C(path):
    return f"/Script/CoreUObject.Class'{path}'"


def _t(cat, sub="", obj="None"):
    obj = obj if obj == "None" else f'"{obj}"'
    return (f'PinType.PinCategory="{cat}",PinType.PinSubCategory="{sub}",PinType.PinSubCategoryObject={obj},'
            'PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,'
            'PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False')


def _s(path):
    return _t("struct", obj=f"/Script/CoreUObject.ScriptStruct'{path}'")


TY = {
    "exec": _t("exec"), "bool": _t("bool"), "int": _t("int"), "real": _t("real", "double"),
    "float": _t("real", "float"), "string": _t("string"),
    "vector": _s("/Script/CoreUObject.Vector"), "rotator": _s("/Script/CoreUObject.Rotator"),
    "color": _s("/Script/CoreUObject.LinearColor"), "hit": _s("/Script/Engine.HitResult"),
    "object": _t("object", obj=C("/Script/CoreUObject.Object")), "actor": _t("object", obj=C(ACTOR)),
    "pc": _t("object", obj=C(PC)), "ctrl": _t("object", obj=C(CTRL)), "cam": _t("object", obj=C(CAM)),
    "font": _t("object", obj=C("/Script/Engine.Font")), "texture": _t("object", obj=C("/Script/Engine.Texture")),
    "vector2d": _s("/Script/CoreUObject.Vector2D"), "name": _t("name"),
    "mpc": _t("object", obj=C("/Script/Engine.MaterialParameterCollection")),
    "compclass": _t("class", obj=C("/Script/Engine.ActorComponent")),
    "comp": _t("object", obj=C("/Script/Engine.ActorComponent")),
    "spot": _t("object", obj=C("/Script/Engine.SpotLightComponent")),
    "light": _t("object", obj=C("/Script/Engine.LightComponent")),
    "shakeclass": _t("class", obj=C("/Script/Engine.CameraShakeBase")), "scene": _t("object", obj=C(SCENE)),
    "ex": _t("object", obj=EX_CLASS),
    "actorclass": _t("class", obj=C(ACTOR)),
    "smc": _t("object", obj=C("/Script/Engine.StaticMeshComponent")),
}


class Pin:
    def __init__(self, node, name, out, ty, default=None):
        self.node, self.name, self.out, self.ty, self.default = node, name, out, ty, default
        self.id, self.links = gid(), []


def fmt_default(ty, v):
    if ty == "int":
        return f'DefaultValue="{int(v)}"'
    if ty == "bool":
        return f'DefaultValue="{"true" if v else "false"}"'
    if ty in ("font", "texture", "mpc", "compclass", "shakeclass", "actorclass"):
        return f'DefaultObject="{v}"'
    if isinstance(v, float) or isinstance(v, int):
        return f'DefaultValue="{float(v)}"'
    return f'DefaultValue="{v}"'


class Node:
    def __init__(self, g, cls, x, y, props=""):
        g.count += 1
        self.cls, self.x, self.y, self.props = cls, int(x), int(y), props
        self.name = f"{cls.rsplit('.', 1)[1]}_I{g.count}"
        self.pins = []

    def out(self, name, ty):
        p = Pin(self, name, True, ty)
        self.pins.append(p)
        return p

    def inp(self, name, ty, src=None):
        """An input pin; src is another node's output pin (a wire) or a plain value (a default)."""
        p = Pin(self, name, False, ty)
        self.pins.append(p)
        if isinstance(src, Pin):
            wire(src, p)
        elif src is not None:
            p.default = fmt_default(ty, src)
        return p

    def text(self, graph):
        lines = [f'Begin Object Class={self.cls} Name="{self.name}" ExportPath="{self.cls}\'{graph}.{self.name}\'"']
        if self.props:
            lines.append("   " + self.props.replace("\n", "\n   "))
        lines += [f"   NodePosX={self.x}", f"   NodePosY={self.y}", f"   NodeGuid={gid()}"]
        for p in self.pins:
            parts = [f"PinId={p.id}", f'PinName="{p.name}"']
            if p.out:
                parts.append('Direction="EGPD_Output"')
            parts.append(TY[p.ty])
            if p.default:
                parts.append(p.default)
            if p.links:
                parts.append("LinkedTo=(" + ",".join(f"{q.node.name} {q.id}" for q in p.links) + ",)")
            lines.append("   CustomProperties Pin (" + ",".join(parts) + ")")
        lines.append("End Object")
        return "\n".join(lines)


def wire(a, b):
    a.links.append(b)
    b.links.append(a)


class Graph:
    """Builds nodes. Exec nodes go left to right along a row; the pure nodes that feed them
    stack up underneath, so the result is readable when pasted."""

    def __init__(self, path):
        self.path, self.nodes, self.count = path, [], 0
        self.x, self.y, self.under = 0, 0, 0

    def row(self, x, y):
        self.x, self.y, self.under = x, y, 0

    def _node(self, cls, props="", exec_node=False):
        if exec_node:
            self.x += 340
            self.under = 0
            n = Node(self, cls, self.x, self.y, props)
        else:
            self.under += 1
            n = Node(self, cls, self.x + 40, self.y + 60 + self.under * 110, props)
        self.nodes.append(n)
        return n

    # --- exec nodes: take the exec pin to come from, give back the node ---
    def _exec(self, n, after):
        ex = n.inp("execute", "exec")
        if after is not None:
            for a in (after if isinstance(after, (list, tuple)) else [after]):
                wire(a, ex)
        n.then = n.out("then", "exec")
        return n

    def call(self, owner, fn, after, args=(), outs=(), target=None):
        n = self._node(K2 + "K2Node_CallFunction", f'FunctionReference=(MemberParent="{C(owner)}",MemberName="{fn}")', True)
        self._exec(n, after)
        if target is not None:
            n.inp("self", target[1], target[0])
        for name, ty, src in args:
            n.inp(name, ty, src)
        n.o = {name: n.out(name, ty) for name, ty in outs}
        return n

    def set(self, var, ty, src, after, target=None):
        """Set a variable: on self, or on another object (target = (pin, type, class path))."""
        if target is None:
            ref = f'VariableReference=(MemberName="{var}",bSelfContext=True)'
        else:
            ref = f'VariableReference=(MemberParent="{target[2]}",MemberName="{var}")'
        n = self._node(K2 + "K2Node_VariableSet", ref, True)
        self._exec(n, after)
        if target is not None:
            n.inp("self", target[1], target[0])
        n.inp(var, ty, src)
        return n

    def branch(self, cond, after):
        n = self._node(K2 + "K2Node_IfThenElse", "", True)
        ex = n.inp("execute", "exec")
        for a in (after if isinstance(after, (list, tuple)) else [after]):
            wire(a, ex)
        n.inp("Condition", "bool", cond)
        return n.out("then", "exec"), n.out("else", "exec")

    def sequence(self, after, count):
        n = self._node(K2 + "K2Node_ExecutionSequence", "", True)
        wire(after, n.inp("execute", "exec"))
        return [n.out(f"then_{i}", "exec") for i in range(count)]

    # --- pure nodes: give back the output pin ---
    def pure(self, owner, fn, args=(), out="ReturnValue", ty="real", target=None, extra_outs=()):
        n = self._node(K2 + "K2Node_CallFunction", f'FunctionReference=(MemberParent="{C(owner)}",MemberName="{fn}")')
        if target is not None:
            n.inp("self", target[1], target[0])
        for name, pty, src in args:
            n.inp(name, pty, src)
        return n.out(out, ty)

    def get(self, var, ty, target=None):
        if target is None:
            ref = f'VariableReference=(MemberName="{var}",bSelfContext=True)'
        else:
            ref = f'VariableReference=(MemberParent="{target[2]}",MemberName="{var}")'
        n = self._node(K2 + "K2Node_VariableGet", ref)
        if target is not None:
            n.inp("self", target[1], target[0])
        return n.out(var, ty)

    def event(self, owner, member, outs):
        n = self._node(K2 + "K2Node_Event",
                       f'EventReference=(MemberParent="{C(owner)}",MemberName="{member}")\nbOverrideFunction=True', True)
        n.then = n.out("then", "exec")
        n.o = {name: n.out(name, ty) for name, ty in outs}
        return n

    def input_event(self, action):
        n = self._node("/Script/InputBlueprintNodes.K2Node_EnhancedInputAction",
                       f"InputAction=\"/Script/EnhancedInput.InputAction'/Game/FirstPerson/Input/Actions/{action}.{action}'\"", True)
        return n.out("Started", "exec")

    def text(self):
        return "\n".join(n.text(self.path) for n in self.nodes)

    # --- small helpers ---
    def mul(self, a, k):
        return self.pure(MATH, "Multiply_DoubleDouble", [("A", "real", a), ("B", "real", k)])

    def not_(self, a):
        return self.pure(MATH, "Not_PreBool", [("A", "bool", a)], ty="bool")

    def empty(self, s):
        return self.pure(STR, "IsEmpty", [("InString", "string", s)], ty="bool")

    def concat(self, a, b):
        return self.pure(STR, "Concat_StrStr", [("A", "string", a), ("B", "string", b)], ty="string")

    def now(self):
        return self.pure(STATICS, "GetTimeSeconds", ty="real")


# ======================= BP_HorrorHUD =======================

def hud_graph():
    g = Graph("/Game/Horror/Interact/BP_HorrorHUD.BP_HorrorHUD:EventGraph")
    focus = lambda: (g.get("Focus", "ex"), "ex", EX_CLASS)            # target tuple for Focus.<var>
    fget = lambda var, ty="string": g.get(var, ty, focus())
    pc = lambda: (g.pure(HUD, "GetOwningPlayerController", out="ReturnValue", ty="pc"), "ctrl")

    def freeze0(after):
        a = g.call(CTRL, "SetIgnoreMoveInput", after, [("bNewMoveInput", "bool", True)], target=pc()).then
        return g.call(CTRL, "SetIgnoreLookInput", a, [("bNewLookInput", "bool", True)], target=pc()).then

    # ---- Begin Play: let this HUD receive E and Tab; start the opening (frozen on black) ----
    g.row(0, 0)
    bp = g.event(ACTOR, "ReceiveBeginPlay", [])
    a = g.call(ACTOR, "EnableInput", bp.then, [("PlayerController", "pc",
               g.pure(HUD, "GetOwningPlayerController", ty="pc"))]).then
    found = g.call(STATICS, "GetActorOfClass", a, [("ActorClass", "actorclass", TITLE_CLASS)], outs=[("ReturnValue", "actor")])
    a = g.call(PC, "SetViewTargetWithBlend", found.then, [("NewViewTarget", "actor", found.o["ReturnValue"]), ("BlendTime", "float", 0.0)],
               target=(g.pure(HUD, "GetOwningPlayerController", ty="pc"), "pc")).then
    a = freeze0(a)
    pcpin = lambda: (g.pure(HUD, "GetOwningPlayerController", ty="pc"), "pc", C(PC))
    a = g.set("bShowMouseCursor", "bool", True, a, target=pcpin()).then
    a = g.set("bEnableClickEvents", "bool", True, a, target=pcpin()).then
    a = g.set("bEnableMouseOverEvents", "bool", True, a, target=pcpin()).then
    g.call("/Script/UMG.WidgetBlueprintLibrary", "SetInputMode_GameAndUIEx", a,
           [("PlayerController", "pc", g.pure(HUD, "GetOwningPlayerController", ty="pc")), ("bHideCursorDuringCapture", "bool", False)])
    open_t = lambda: g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.now()), ("B", "real", g.get("OpenStart", "real"))])

    # ---- Draw HUD ----
    g.row(0, 600)
    ev = g.event(HUD, "ReceiveDrawHUD", [("SizeX", "int"), ("SizeY", "int")])
    W = g.pure(MATH, "Conv_IntToDouble", [("InInt", "int", ev.o["SizeX"])])
    H = g.pure(MATH, "Conv_IntToDouble", [("InInt", "int", ev.o["SizeY"])])
    TS = g.mul(H, TEXT_SCALE)

    def draw(text, after, x, y, scale=1.0, color=TEXT, shadow=False, font=FONT, at=None):
        """DrawText at a fraction of the screen (or at=(x pin, y pin) in pixels). shadow: a black copy
        just behind it first, so the words stay readable on a bright wall."""
        if shadow:
            after = draw(text, after, x + 0.0012, y + 0.0018, scale, SHADOW, font=font)
        sx, sy = at if at else (g.mul(W, x), g.mul(H, y))
        return g.call(HUD, "DrawText", after, [
            ("Text", "string", text), ("TextColor", "color", color),
            ("ScreenX", "float", sx), ("ScreenY", "float", sy),
            ("Font", "font", font), ("Scale", "float", g.mul(TS, scale) if scale != 1.0 else TS)]).then

    def dark(after):
        return g.call(HUD, "DrawRect", after, [
            ("RectColor", "color", DARK), ("ScreenX", "float", 0.0), ("ScreenY", "float", 0.0),
            ("ScreenW", "float", W), ("ScreenH", "float", H)]).then

    # what are we looking at?
    cam = g.get("PlayerCameraManager", "cam", (g.pure(HUD, "GetOwningPlayerController", ty="pc"), "pc", C(PC)))
    loc = g.pure(CAM, "GetCameraLocation", ty="vector", target=(cam, "cam"))
    fwd = g.pure(MATH, "GetForwardVector", [("InRot", "rotator",
                 g.pure(CAM, "GetCameraRotation", ty="rotator", target=(cam, "cam")))], ty="vector")
    start = g.pure(MATH, "Add_VectorVector", [("A", "vector", loc), ("B", "vector",
                   g.pure(MATH, "Multiply_VectorFloat", [("A", "vector", fwd), ("B", "real", NEAR)], ty="vector"))], ty="vector")
    end = g.pure(MATH, "Add_VectorVector", [("A", "vector", loc), ("B", "vector",
                 g.pure(MATH, "Multiply_VectorFloat", [("A", "vector", fwd), ("B", "real", REACH)], ty="vector"))], ty="vector")
    # tell the materials where you are (MPC_Horror.PlayerPos): crows fly off, the owl turns its head
    ploc = g.pure(ACTOR, "K2_GetActorLocation", ty="vector", target=(g.pure(HUD, "GetOwningPawn", ty="actor"), "actor"))
    pcol = g.pure(MATH, "Conv_VectorToLinearColor", [("InVec", "vector", ploc)], ty="color")
    # the warp (unreal/breakdown.py, user 2026-11-17): flashes for a few seconds after you put down a page in the
    # wrong hand (WarpUntil); MPC_Horror.WarpFlash tells M_Breakdown, every frame, in every mode (the ending too)
    warp_on = g.pure(MATH, "Less_DoubleDouble", [("A", "real", g.now()), ("B", "real", g.get("WarpUntil", "real"))], ty="bool")
    # user 2026-11-22: the second half builds up - after the boathouse note flashes keep coming (LATE_FLASH), and
    # once she steps onto the dock after it, the whole picture is warped (WarpWhole; the ending keeps it on her line)
    late = g.pure(STR, "Contains", [("SearchIn", "string", g.get("Keys", "string")),
                                    ("Substring", "string", "#" + LATE_AFTER + ",")], ty="bool")
    flash = g.pure(MATH, "SelectFloat", [("A", "real", 1.0),
                                         ("B", "real", g.pure(MATH, "SelectFloat", [("A", "real", LATE_FLASH), ("B", "real", 0.0), ("bPickA", "bool", late)])),
                                         ("bPickA", "bool", warp_on)])
    warp = g.call("/Script/Engine.KismetMaterialLibrary", "SetScalarParameterValue", ev.then,
                  [("Collection", "mpc", MPC_PATH), ("ParameterName", "name", "WarpFlash"), ("ParameterValue", "float", flash)])
    bv = g._node(K2 + "K2Node_CallFunction", f'FunctionReference=(MemberParent="{C(MATH)}",MemberName="BreakVector")')
    bv.inp("InVec", "vector", ploc)
    wx, wy = bv.out("X", "real"), bv.out("Y", "real")
    on_dock = g.pure(MATH, "BooleanAND", [
        ("A", "bool", g.pure(MATH, "Greater_DoubleDouble", [("A", "real", wy), ("B", "real", DOCK_Y0)], ty="bool")),
        ("B", "bool", g.pure(MATH, "Less_DoubleDouble", [("A", "real", g.pure(MATH, "Abs", [("A", "real", g.pure(MATH, "Subtract_DoubleDouble", [
            ("A", "real", wx), ("B", "real", DOCK_X)]))])), ("B", "real", DOCK_HW)], ty="bool"))], ty="bool")
    whole = g.pure(MATH, "BooleanAND", [("A", "bool", on_dock), ("B", "bool", late)], ty="bool")
    warp = g.call("/Script/Engine.KismetMaterialLibrary", "SetScalarParameterValue", warp.then,
                  [("Collection", "mpc", MPC_PATH), ("ParameterName", "name", "WarpWhole"),
                   ("ParameterValue", "float", g.pure(MATH, "SelectFloat", [("A", "real", 1.0), ("B", "real", 0.0), ("bPickA", "bool", whole)]))])
    title_yes, title_no = g.branch(g.get("Title", "bool"), warp.then)
    end_yes, end_no = g.branch(g.get("Ending", "bool"), title_no)
    op_yes, op_no = g.branch(g.get("Opening", "bool"), end_no)
    hud_then, fade_then, pause_then = g.sequence(op_no, 3)
    tell = g.call("/Script/Engine.KismetMaterialLibrary", "SetVectorParameterValue", hud_then,
                  [("Collection", "mpc", MPC_PATH), ("ParameterName", "name", "PlayerPos"), ("ParameterValue", "color", pcol)])
    trace = g.call(SYS, "LineTraceSingle", tell.then, [("Start", "vector", start), ("End", "vector", end),
                   ("bIgnoreSelf", "bool", True)], outs=[("OutHit", "hit")])
    hit_actor = g.pure(STATICS, "BreakHitResult", [("Hit", "hit", trace.o["OutHit"])], out="HitActor", ty="actor")
    cast = g._node(K2 + "K2Node_DynamicCast", f'TargetType="{EX_CLASS}"', True)
    wire(trace.then, cast.inp("execute", "exec"))
    cast_ok, cast_fail = cast.out("then", "exec"), cast.out("CastFailed", "exec")
    cast.inp("Object", "object", hit_actor)
    as_ex = cast.out("AsBP Examinable", "ex")
    s_hit = g.set("Focus", "ex", as_ex, cast_ok)
    # looking away: a clue you already spotted stays picked (sticky) until you've used it,
    # unless it's a door or you walk more than STICKY cm away from it
    g.row(340 * 4, 300)
    f_yes, f_no = g.branch(g.pure(SYS, "IsValid", [("Object", "object", g.get("Focus", "ex"))], ty="bool"), cast_fail)
    near = g.pure(MATH, "Less_DoubleDouble", [
        ("A", "real", g.pure(ACTOR, "GetDistanceTo", [("OtherActor", "actor", g.pure(HUD, "GetOwningPawn", ty="actor"))],
                             ty="float", target=(g.get("Focus", "ex"), "actor"))),
        ("B", "real", STICKY)], ty="bool")
    fresh_clue = g.pure(MATH, "BooleanAND", [("A", "bool", g.not_(fget("Done", "bool"))),
                                             ("B", "bool", g.not_(fget("IsDoor", "bool")))], ty="bool")
    k_yes, k_no = g.branch(g.pure(MATH, "BooleanAND", [("A", "bool", fresh_clue), ("B", "bool", near)], ty="bool"), f_yes)
    s_none = g.set("Focus", "ex", None, [f_no, k_no])        # nothing examinable any more
    g.row(340 * 7, 600)

    # flashlight flicker: a small timer. Mode 0 = on, 1 = flutter, 2 = cut out. When an event
    # ends, the next one is FLICK_GAP away; a cut-out sometimes ends with a hit (camera jolt).
    # Fear (MPC_Horror) shortens the gaps and makes cut-outs more common.
    g.row(340 * 7, -2400)
    LIB = "/Script/Engine.KismetMaterialLibrary"
    read_fear = g.call(LIB, "GetScalarParameterValue", [s_hit.then, k_yes, s_none.then],
                       [("Collection", "mpc", MPC_PATH), ("ParameterName", "name", "Fear")], outs=[("ReturnValue", "float")])
    fear = lambda: read_fear.o["ReturnValue"]          # read once per frame (it's an action node)
    by_fear = lambda calm, afraid: g.pure(MATH, "Lerp", [("A", "real", calm), ("B", "real", afraid), ("Alpha", "real", fear())])
    rnd = lambda lo, hi: g.pure(MATH, "RandomFloatInRange", [("Min", "real", lo), ("Max", "real", hi)])
    mode_is = lambda k: g.pure(MATH, "EqualEqual_IntInt", [("A", "int", g.get("FlMode", "int")), ("B", "int", k)], ty="bool")
    past = lambda var: g.pure(MATH, "GreaterEqual_DoubleDouble", [("A", "real", g.now()), ("B", "real", g.get(var, "real"))], ty="bool")
    both = lambda a, b: g.pure(MATH, "BooleanAND", [("A", "bool", a), ("B", "bool", b)], ty="bool")
    later = lambda dt: g.pure(MATH, "Add_DoubleDouble", [("A", "real", g.now()), ("B", "real", dt)])
    chance = lambda p: g.pure(MATH, "Less_DoubleDouble", [("A", "real", g.pure(MATH, "RandomFloat")), ("B", "real", p)], ty="bool")

    ended, running = g.branch(both(g.not_(mode_is(0)), past("FlEnd")), read_fear.then)
    hit, no_hit = g.branch(both(mode_is(2), g.get("FlHit", "bool")), ended)
    cam_mgr = g.get("PlayerCameraManager", "cam", (g.pure(HUD, "GetOwningPlayerController", ty="pc"), "pc", C(PC)))
    knock = g.call(CAM, "StartCameraShake", hit, [("ShakeClass", "shakeclass", HIT_SHAKE), ("Scale", "float", 1.0)],
                   target=(cam_mgr, "cam"))
    a = g.set("FlMode", "int", 0, [knock.then, no_hit]).then
    a = g.set("FlNext", "real", later(rnd(by_fear(FLICK_GAP[0][0], FLICK_GAP[1][0]), by_fear(FLICK_GAP[0][1], FLICK_GAP[1][1]))), a).then
    g.row(340 * 7, -1700)
    start, idle = g.branch(both(mode_is(0), past("FlNext")), [a, running])
    cut, flutter = g.branch(chance(by_fear(FLICK_OFF[0], FLICK_OFF[1])), start)
    a = g.set("FlMode", "int", 2, cut).then
    a = g.set("FlEnd", "real", later(rnd(*CUTOUT)), a).then
    cut_done = g.set("FlHit", "bool", chance(HIT_CHANCE), a).then
    g.row(340 * 9, -1300)
    a = g.set("FlMode", "int", 1, flutter).then
    flutter_done = g.set("FlEnd", "real", later(rnd(*FLUTTER)), a).then
    g.row(340 * 12, -1700)
    light = g._node(K2 + "K2Node_CallFunction", f'FunctionReference=(MemberParent="{C(ACTOR)}",MemberName="GetComponentByClass")')
    light.inp("self", "actor", g.pure(HUD, "GetOwningPawn", ty="actor"))
    light.inp("ComponentClass", "compclass", "/Script/Engine.SpotLightComponent")
    light_out = light.out("ReturnValue", "comp")
    as_spot = g._node(K2 + "K2Node_DynamicCast", f'TargetType="{C("/Script/Engine.SpotLightComponent")}"', True)
    ex = as_spot.inp("execute", "exec")
    for w_ in (cut_done, flutter_done, idle):
        wire(w_, ex)
    spot_ok, spot_fail = as_spot.out("then", "exec"), as_spot.out("CastFailed", "exec")
    as_spot.inp("Object", "object", light_out)
    spot = as_spot.out("AsSpot Light Component", "spot")
    sel = lambda a_, b_, pick: g.pure(MATH, "SelectFloat", [("A", "real", a_), ("B", "real", b_), ("bPickA", "bool", pick)])
    level = sel(0.0, sel(rnd(0.1, 0.8), 1.0, mode_is(1)), mode_is(2))     # off / flutter / on
    # auto-dim: when the beam lands on something close (a wall, a bed), the light dims like
    # your eyes adjusting, so small rooms don't burn out white. FlDimNear/FlDimFar/FlDimMin live
    # in MPC_Horror (unreal/flashlight.py) so they can be tuned while playing.
    g.row(340 * 14, -2400)
    prm = []
    after_ = spot_ok
    for name_ in ("FlDimNear", "FlDimFar", "FlDimMin", "FlIndoor", "FlCeiling"):
        n_ = g.call(LIB, "GetScalarParameterValue", after_, [("Collection", "mpc", MPC_PATH), ("ParameterName", "name", name_)],
                    outs=[("ReturnValue", "float")])
        prm.append(n_.o["ReturnValue"])
        after_ = n_.then
    dim_near, dim_far, dim_min, indoor_level, ceiling = prm
    far_end = g.pure(MATH, "Add_VectorVector", [("A", "vector", loc), ("B", "vector",
                     g.pure(MATH, "Multiply_VectorFloat", [("A", "vector", fwd), ("B", "real", dim_far)], ty="vector"))], ty="vector")
    beam_start = g.pure(MATH, "Add_VectorVector", [("A", "vector", loc), ("B", "vector",
                        g.pure(MATH, "Multiply_VectorFloat", [("A", "vector", fwd), ("B", "real", NEAR)], ty="vector"))], ty="vector")
    beam = g.call(SYS, "LineTraceSingle", after_, [("Start", "vector", beam_start), ("End", "vector", far_end),
                  ("bIgnoreSelf", "bool", True)], outs=[("OutHit", "hit"), ("ReturnValue", "bool")])
    dist = g.pure(STATICS, "BreakHitResult", [("Hit", "hit", beam.o["OutHit"])], out="Distance", ty="float")
    dist = sel(g.pure(MATH, "Add_DoubleDouble", [("A", "real", dist), ("B", "real", NEAR)]), dim_far, beam.o["ReturnValue"])
    t_ = g.pure(MATH, "FClamp", [("Value", "real", g.pure(MATH, "Divide_DoubleDouble", [
        ("A", "real", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", dist), ("B", "real", dim_near)])),
        ("B", "real", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", dim_far), ("B", "real", dim_near)]))])),
        ("Min", "real", 0.0), ("Max", "real", 1.0)])
    want = g.pure(MATH, "Lerp", [("A", "real", dim_min), ("B", "real", 1.0), ("Alpha", "real", t_)])
    # indoors (a ceiling within FlCeiling cm above your eyes) the whole beam drops to FlIndoor
    up = g.call(SYS, "LineTraceSingle", beam.then, [("Start", "vector", loc), ("End", "vector",
                g.pure(MATH, "Add_VectorVector", [("A", "vector", loc), ("B", "vector",
                       g.pure(MATH, "MakeVector", [("X", "real", 0.0), ("Y", "real", 0.0), ("Z", "real", ceiling)], ty="vector"))],
                       ty="vector")), ("bIgnoreSelf", "bool", True)], outs=[("OutHit", "hit"), ("ReturnValue", "bool")])
    want = g.pure(MATH, "FMin", [("A", "real", want), ("B", "real", sel(indoor_level, 1.0, up.o["ReturnValue"]))])
    smooth = g.pure(MATH, "FInterpTo", [("Current", "real", g.get("FlDim", "real")), ("Target", "real", want),
                                       ("DeltaTime", "real", g.pure(STATICS, "GetWorldDeltaSeconds")),
                                       ("InterpSpeed", "real", 5.0)])
    s_dim = g.set("FlDim", "real", smooth, up.then)
    power = g.pure(MATH, "Multiply_DoubleDouble", [("A", "real", g.mul(level, FLASH_INTENSITY)), ("B", "real", g.get("FlDim", "real"))])
    lit = g.call("/Script/Engine.LightComponent", "SetIntensity", s_dim.then, [("NewIntensity", "float", power)],
                 target=(spot, "light"))

    # objective + message
    g.row(340 * 9, 0)
    after = draw(g.get("Objective", "string"), [lit.then, spot_fail], 0.04, 0.05, 0.8, DIM, True)

    # corner map: a MAP_VIEW-wide window of the paper map centred on you, top right,
    # with the red arrow in the middle turned the way you face (north is always up)
    g.row(340 * 9, 600)
    S = g.mul(H, MAP_SCREEN)
    MX = g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.pure(MATH, "Subtract_DoubleDouble", [
        ("A", "real", W), ("B", "real", S)])), ("B", "real", g.mul(W, 0.025))])
    MY = g.mul(H, 0.04)
    pawn_loc = g.pure(ACTOR, "K2_GetActorLocation", ty="vector",
                      target=(g.pure(HUD, "GetOwningPawn", ty="actor"), "actor"))
    px = g._node(K2 + "K2Node_CallFunction", f'FunctionReference=(MemberParent="{C(MATH)}",MemberName="BreakVector")')
    px.inp("InVec", "vector", pawn_loc)
    pX, pY = px.out("X", "real"), px.out("Y", "real")
    half = MAP_VIEW / MAP_SIZE / 2
    # +X is west (left on the map), so U grows as X shrinks
    U = g.pure(MATH, "Add_DoubleDouble", [("A", "real", g.mul(pX, -1.0 / MAP_SIZE)), ("B", "real", MAP["x_max"] / MAP_SIZE - half)])
    V = g.pure(MATH, "Add_DoubleDouble", [("A", "real", g.mul(pY, -1.0 / MAP_SIZE)), ("B", "real", MAP["y_max"] / MAP_SIZE - half)])
    # only once you've picked up Cas's map (clue map_cas gives the key "map")
    has_map, no_map = g.branch(g.pure(STR, "Contains", [("SearchIn", "string", g.get("Keys", "string")),
                                                        ("Substring", "string", "map")], ty="bool"), after)
    paper = g.call(HUD, "DrawTexture", has_map, [
        ("Texture", "texture", MAP_TEX), ("ScreenX", "float", MX), ("ScreenY", "float", MY),
        ("ScreenW", "float", S), ("ScreenH", "float", S),
        ("TextureU", "float", U), ("TextureV", "float", V),
        ("TextureUWidth", "float", 2 * half), ("TextureVHeight", "float", 2 * half),
        ("TintColor", "color", MAP_TINT)]).then
    # the torn paper edge round it (tools/make_map.py frame_edge): its hole is exactly the map window
    FRS = g.mul(S, 1.0 / (1 - 2 * FRAME_HOLE))
    paper = g.call(HUD, "DrawTexture", paper, [
        ("Texture", "texture", MAP_FRAME_TEX),
        ("ScreenX", "float", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", MX), ("B", "real", g.mul(FRS, FRAME_HOLE))])),
        ("ScreenY", "float", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", MY), ("B", "real", g.mul(FRS, FRAME_HOLE))])),
        ("ScreenW", "float", FRS), ("ScreenH", "float", FRS),
        ("TextureU", "float", 0.0), ("TextureV", "float", 0.0), ("TextureUWidth", "float", 1.0), ("TextureVHeight", "float", 1.0),
        ("TintColor", "color", MAP_TINT)]).then
    M = g.mul(S, 0.16)
    centre = lambda base: g.pure(MATH, "Subtract_DoubleDouble", [
        ("A", "real", g.pure(MATH, "Add_DoubleDouble", [("A", "real", base), ("B", "real", g.mul(S, 0.5))])),
        ("B", "real", g.mul(M, 0.5))])
    yaw = g._node(K2 + "K2Node_CallFunction", f'FunctionReference=(MemberParent="{C(MATH)}",MemberName="BreakRotator")')
    yaw.inp("InRot", "rotator", g.pure(CTRL, "GetControlRotation", ty="rotator",
                                       target=(g.pure(HUD, "GetOwningPlayerController", ty="pc"), "ctrl")))
    yaw_out = yaw.out("Yaw", "float")
    # facing +Y (yaw 90) is map-up, facing +X (yaw 0) is map-left: screen turn = yaw - 90
    after = g.call(HUD, "DrawTexture", paper, [
        ("Texture", "texture", MARKER_TEX), ("ScreenX", "float", centre(MX)), ("ScreenY", "float", centre(MY)),
        ("ScreenW", "float", M), ("ScreenH", "float", M),
        ("TextureU", "float", 0.0), ("TextureV", "float", 0.0), ("TextureUWidth", "float", 1.0), ("TextureVHeight", "float", 1.0),
        ("TintColor", "color", MARKER_TINT),
        ("Rotation", "float", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", yaw_out), ("B", "real", 90.0)])),
        ("RotPivot", "vector2d", "(X=0.500000,Y=0.500000)")]).then
    # how to open it, inside the corner map at the bottom left: "[M] Map" (black copy first)
    under = g.pure(MATH, "Add_DoubleDouble", [("A", "real", MY), ("B", "real", g.pure(MATH, "Subtract_DoubleDouble", [
        ("A", "real", S), ("B", "real", g.mul(H, 0.03))]))])
    inside = g.pure(MATH, "Add_DoubleDouble", [("A", "real", MX), ("B", "real", g.mul(H, 0.008))])
    for dx, dy, col in ((0.0, 0.0, "(R=0.03,G=0.025,B=0.03,A=0.85)"),):     # dark ink, on the solid paper
        after = g.call(HUD, "DrawText", after, [
            ("Text", "string", "[M]  Map"), ("TextColor", "color", col),
            ("ScreenX", "float", g.pure(MATH, "Add_DoubleDouble", [("A", "real", inside), ("B", "real", dx)])),
            ("ScreenY", "float", g.pure(MATH, "Add_DoubleDouble", [("A", "real", under), ("B", "real", dy)])),
            ("Font", "font", FONT), ("Scale", "float", g.mul(TS, 0.5))]).then
    fresh = g.pure(MATH, "Less_DoubleDouble", [("A", "real", g.pure(MATH, "Subtract_DoubleDouble", [
        ("A", "real", g.now()), ("B", "real", g.get("ToastTime", "real"))])), ("B", "real", 3.0)], ty="bool")
    t_yes, t_no = g.branch(fresh, [after, no_map])
    toast_done = draw(g.get("Toast", "string"), t_yes, 0.04, 0.8, 0.9, TEXT, True)

    # reading screen
    r_yes, r_no = g.branch(g.get("Reading", "bool"), [toast_done, t_no])
    a = dark(r_yes)
    on_paper, no_paper = g.branch(g.not_(g.empty(g.get("ReadPaper", "string"))), a)

    def body(after, x, y, on_sheet, sfx=""):
        """The body in the paper's own hand (ink on a sheet); Bug's font when it has none.
        sfx "2": the second sheet (ReadBody2 in ReadHand2)."""
        nxt = after
        for hand, font, scale, ink in HANDS:
            is_hand = g.pure(STR, "EqualEqual_StrStr", [("A", "string", g.get("ReadHand" + sfx, "string")),
                                                        ("B", "string", hand)], ty="bool")
            h_yes, nxt = g.branch(is_hand, nxt)
            draw(g.get("ReadBody" + sfx, "string"), h_yes, 0, 0, scale, ink if on_sheet else TEXT, font=font, at=(x, y))
        draw(g.get("ReadBody" + sfx, "string"), nxt, 0, 0, 1.0, INK if on_sheet else TEXT, at=(x, y))

    # no sheet: words on the dark screen, as before
    # no title over the page (user 2026-11-17: no labels like "A letter on the bed" / "Cas's wall")
    body_then, close_then = g.sequence(no_paper, 2)
    body(body_then, g.mul(W, 0.2), g.mul(H, 0.24), False)
    draw("[E]  Close", close_then, 0.2, 0.88, 0.75, DIM)

    # on a sheet: the paper in the middle, the words written on it; Bug's title and [E] beside it
    two = g.not_(g.empty(g.get("ReadPaper2", "string")))
    # two sheets (user 2026-11-22: "[E] Close" was faint on top of the left sheet): a little smaller and higher,
    # with [E] Close bright and centred under them
    PH = g.pure(MATH, "SelectFloat", [("A", "real", g.mul(H, PAIR_H)), ("B", "real", g.mul(H, PAPER_H)), ("bPickA", "bool", two)], ty="real")
    PW = g.mul(PH, PAPER_ASPECT)
    # two sheets (ReadPaper2 set, user 2026-11-22: the shack's notes side by side): first on the left, second
    # on the right, a small gap between; one sheet: centred as before
    left = g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.mul(W, 0.5)), ("B", "real", g.pure(MATH, "Add_DoubleDouble", [
        ("A", "real", PW), ("B", "real", g.mul(H, PAIR_GAP / 2))]))])
    PX = g.pure(MATH, "SelectFloat", [("A", "real", left),
                                      ("B", "real", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.mul(W, 0.5)), ("B", "real", g.mul(PW, 0.5))])),
                                      ("bPickA", "bool", two)], ty="real")
    PX2 = g.pure(MATH, "Add_DoubleDouble", [("A", "real", g.mul(W, 0.5)), ("B", "real", g.mul(H, PAIR_GAP / 2))])
    PY = g.pure(MATH, "SelectFloat", [("A", "real", g.mul(H, PAIR_TOP)), ("B", "real", g.mul(H, PAPER_TOP)), ("bPickA", "bool", two)], ty="real")

    def sheet_tex(after, var, x):
        nxt = after
        for kind, tex in PAPERS:
            is_kind = g.pure(STR, "EqualEqual_StrStr", [("A", "string", g.get(var, "string")),
                                                        ("B", "string", kind)], ty="bool")
            k_yes, nxt = g.branch(is_kind, nxt)
            g.call(HUD, "DrawTexture", k_yes, [
                ("Texture", "texture", tex), ("ScreenX", "float", x), ("ScreenY", "float", PY),
                ("ScreenW", "float", PW), ("ScreenH", "float", PH),
                ("TextureU", "float", 0.0), ("TextureV", "float", 0.0), ("TextureUWidth", "float", 1.0),
                ("TextureVHeight", "float", 1.0), ("TintColor", "color", "(R=1.0,G=1.0,B=1.0,A=1.000000)")])

    sheet = g.sequence(on_paper, 5)
    sheet_tex(sheet[0], "ReadPaper", PX)
    c_two, c_one = g.branch(two, sheet[4])
    draw("[E]  Close", c_two, 0.465, PAIR_TOP + PAIR_H + 0.012, 0.8, TEXT, True)
    draw("[E]  Close", c_one, 0.03, 0.9, 0.75, DIM)
    words = sheet[1]
    body(words, g.pure(MATH, "Add_DoubleDouble", [("A", "real", PX), ("B", "real", g.mul(H, PAPER_TEXT_X))]),
         g.pure(MATH, "Add_DoubleDouble", [("A", "real", PY), ("B", "real", g.mul(PH, PAPER_TEXT_Y))]), True)
    two_a, _ = g.branch(two, sheet[2])
    sheet_tex(two_a, "ReadPaper2", PX2)
    two_b, _ = g.branch(two, sheet[3])
    body(two_b, g.pure(MATH, "Add_DoubleDouble", [("A", "real", PX2), ("B", "real", g.mul(H, PAPER_TEXT_X))]),
         g.pure(MATH, "Add_DoubleDouble", [("A", "real", PY), ("B", "real", g.mul(PH, PAPER_TEXT_Y))]), True, "2")

    # journal
    g.row(340 * 9, 1300)
    j_yes, j_no = g.branch(g.get("JournalOpen", "bool"), r_no)
    a = dark(j_yes)
    a = draw("JOURNAL", a, 0.2, 0.14, 1.25)
    a = draw(g.get("Journal", "string"), a, 0.2, 0.24)
    draw("[Tab]  Close", a, 0.2, 0.88, 0.75, DIM)

    # the full map (M): the whole torn-paper map, opaque, with you on it; the game is paused
    g.row(340 * 9, 1700)
    m_yes, m_no = g.branch(g.get("MapOpen", "bool"), j_no)
    # full size; a little smaller and higher only while her first-time line is showing under it
    # (M clears the message, so any map opened with M is full size)
    with_text = g.not_(g.empty(g.get("Toast", "string")))
    FS = g.pure(MATH, "SelectFloat", [("A", "real", g.mul(H, MAP_FULL)), ("B", "real", g.mul(H, MAP_BIG)),
                                      ("bPickA", "bool", with_text)], ty="real")
    FX = g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.mul(W, 0.5)), ("B", "real", g.mul(FS, 0.5))])
    FY = g.pure(MATH, "SelectFloat", [("A", "real", g.mul(H, 0.02)), ("B", "real", g.mul(H, (1 - MAP_BIG) / 2)),
                                      ("bPickA", "bool", with_text)], ty="real")
    a = dark(m_yes)
    a = g.call(HUD, "DrawTexture", a, [
        ("Texture", "texture", MAP_FULL_TEX), ("ScreenX", "float", FX), ("ScreenY", "float", FY),
        ("ScreenW", "float", FS), ("ScreenH", "float", FS),
        ("TextureU", "float", 0.0), ("TextureV", "float", 0.0), ("TextureUWidth", "float", 1.0), ("TextureVHeight", "float", 1.0),
        ("TintColor", "color", WHITE)]).then
    FM = g.mul(FS, 0.035)
    # where you are on the sheet: same flip as the corner map (+X is west = left)
    on_sheet = lambda base, coord, top: g.pure(MATH, "Subtract_DoubleDouble", [
        ("A", "real", g.pure(MATH, "Add_DoubleDouble", [("A", "real", base), ("B", "real", g.pure(MATH, "Multiply_DoubleDouble", [
            ("A", "real", FS), ("B", "real", g.pure(MATH, "Add_DoubleDouble", [
                ("A", "real", g.mul(coord, -1.0 / MAP_SIZE)), ("B", "real", top / MAP_SIZE)]))]))])),
        ("B", "real", g.mul(FM, 0.5))])
    a = g.call(HUD, "DrawTexture", a, [
        ("Texture", "texture", MARKER_TEX), ("ScreenX", "float", on_sheet(FX, pX, MAP["x_max"])),
        ("ScreenY", "float", on_sheet(FY, pY, MAP["y_max"])), ("ScreenW", "float", FM), ("ScreenH", "float", FM),
        ("TextureU", "float", 0.0), ("TextureV", "float", 0.0), ("TextureUWidth", "float", 1.0), ("TextureVHeight", "float", 1.0),
        ("TintColor", "color", WHITE),
        ("Rotation", "float", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", yaw_out), ("B", "real", 90.0)])),
        ("RotPivot", "vector2d", "(X=0.500000,Y=0.500000)")]).then
    # a fresh message (her line when you've just picked the map up) along the bottom
    f_yes, f_no = g.branch(fresh, a)
    a = draw(g.get("Toast", "string"), f_yes, 0.04, 0.8, 0.9, TEXT, True)      # same spot as the normal message
    draw("[M]  Close", [a, f_no], 0.04, 0.92, 0.75, DIM, True)

    # prompt
    g.row(340 * 9, 2400)
    v_yes, _ = g.branch(g.pure(SYS, "IsValid", [("Object", "object", g.get("Focus", "ex"))], ty="bool"), m_no)
    o_yes, _ = g.branch(g.not_(fget("Opened", "bool")), v_yes)
    # a torn scrap of Cas's paper behind the prompt, written on in dark ink (was a grey box)
    box = g.call(HUD, "DrawTexture", o_yes, [
        ("Texture", "texture", SCRAP_TEX), ("ScreenX", "float", g.mul(W, 0.425)), ("ScreenY", "float", g.mul(H, 0.54)),
        ("ScreenW", "float", g.mul(W, 0.16)), ("ScreenH", "float", g.mul(H, 0.075)),
        ("TextureU", "float", 0.0), ("TextureV", "float", 0.0), ("TextureUWidth", "float", 1.0), ("TextureVHeight", "float", 1.0),
        ("TintColor", "color", "(R=0.85,G=0.83,B=0.8,A=0.95)")]).then
    draw(g.concat("[E]  ", fget("Prompt")), box, 0.45, 0.556, 0.8, INK)

    # ---- the opening: drawn instead of the HUD while Opening is on ----
    g.row(340 * 9, -3200)
    t = open_t()
    a = g.call(HUD, "DrawRect", op_yes, [("RectColor", "color", BLACK), ("ScreenX", "float", 0.0), ("ScreenY", "float", 0.0),
                                         ("ScreenW", "float", W), ("ScreenH", "float", H)]).then
    shown = g.pure(MATH, "FTrunc", [("A", "real", g.mul(g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", t), ("B", "real", OPEN_DELAY)]),
                                                       OPEN_CPS))], ty="int")
    shown = g.pure(MATH, "Clamp", [("Value", "int", shown), ("Min", "int", 0), ("Max", "int", 9999)], ty="int")
    typed = g.pure(STR, "Left", [("SourceString", "string", g.get("OpeningText", "string")), ("Count", "int", shown)], ty="string")
    tx = g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.mul(W, 0.5)), ("B", "real", g.mul(H, 0.3))])
    a = draw(typed, a, 0, 0, 1.0, TEXT, at=(tx, g.mul(H, 0.04)))
    card, _ = g.branch(g.pure(MATH, "Greater_DoubleDouble", [("A", "real", t), ("B", "real", OPEN_T_CARD)], ty="bool"), a)
    CH = g.mul(H, 0.33)
    a = g.call(HUD, "DrawTexture", card, [
        ("Texture", "texture", POSTCARD_TEX),
        ("ScreenX", "float", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.mul(W, 0.5)), ("B", "real", g.mul(H, 0.2475))])),
        ("ScreenY", "float", g.mul(H, 0.6)), ("ScreenW", "float", g.mul(H, 0.495)), ("ScreenH", "float", CH),
        ("TextureU", "float", 0.0), ("TextureV", "float", 0.0), ("TextureUWidth", "float", 1.0), ("TextureVHeight", "float", 1.0),
        ("TintColor", "color", g.pure(MATH, "MakeColor", [("R", "float", 1.0), ("G", "float", 1.0), ("B", "float", 1.0),
            ("A", "float", g.pure(MATH, "FMin", [("A", "real", 1.0), ("B", "real", g.mul(g.pure(MATH, "Subtract_DoubleDouble", [
                ("A", "real", t), ("B", "real", OPEN_T_CARD)]), 1.0 / OPEN_T_CARD_IN))], ty="real"))], ty="color"))]).then
    go, _ = g.branch(g.pure(MATH, "Greater_DoubleDouble", [("A", "real", t), ("B", "real", OPEN_T_GO)], ty="bool"), a)
    draw("[E]  Continue", go, 0.04, 0.92, 0.75, DIM)
    # after it: black fading out over the game
    g.row(340 * 9, -2800)
    since = g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.now()), ("B", "real", g.get("OpenEnd", "real"))])
    fading, _ = g.branch(g.pure(MATH, "Less_DoubleDouble", [("A", "real", since), ("B", "real", OPEN_FADE)], ty="bool"), fade_then)
    alpha = g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", 1.0), ("B", "real", g.mul(since, 1.0 / OPEN_FADE))])
    col = g.pure(MATH, "MakeColor", [("R", "float", 0.0), ("G", "float", 0.0), ("B", "float", 0.0), ("A", "float", alpha)], ty="color")
    g.call(HUD, "DrawRect", fading, [("RectColor", "color", col), ("ScreenX", "float", 0.0), ("ScreenY", "float", 0.0),
                                     ("ScreenW", "float", W), ("ScreenH", "float", H)])

    # ---- the title screen (2026-11-17, second pass: the user's approved mockup) ----
    g.row(340 * 9, -5200)
    ctl_yes, ctl_no = g.branch(g.get("ControlsOpen", "bool"), title_yes)
    T = g.now()
    # the slow push-in down the dock: move the title camera a little every frame
    found = g.call(STATICS, "GetActorOfClass", ctl_no, [("ActorClass", "actorclass", TITLE_CLASS)], outs=[("ReturnValue", "actor")])
    push = g.pure(MATH, "FMin", [("A", "real", g.mul(T, PUSH_SPEED)), ("B", "real", PUSH_MAX)], ty="real")
    bob = g.mul(g.pure(MATH, "Sin", [("A", "real", g.mul(T, 0.35))], ty="real"), 2.5)
    loc = g.pure(MATH, "MakeVector", [("X", "real", PUSH_FROM[0]),
                                      ("Y", "real", g.pure(MATH, "Add_DoubleDouble", [("A", "real", PUSH_FROM[1]), ("B", "real", push)])),
                                      ("Z", "real", g.pure(MATH, "Add_DoubleDouble", [("A", "real", PUSH_FROM[2]), ("B", "real", bob)]))], ty="vector")
    a = g.call(ACTOR, "K2_SetActorLocation", found.then, [("NewLocation", "vector", loc), ("bSweep", "bool", False),
                                                          ("bTeleport", "bool", True)], target=(found.o["ReturnValue"], "actor")).then
    # vignette, then the title breathing in and out of the fog, a thin red rule under it
    a = g.call(HUD, "DrawTexture", a, [
        ("Texture", "texture", VIGNETTE_TEX), ("ScreenX", "float", 0.0), ("ScreenY", "float", 0.0), ("ScreenW", "float", W), ("ScreenH", "float", H),
        ("TextureU", "float", 0.0), ("TextureV", "float", 0.0), ("TextureUWidth", "float", 1.0), ("TextureVHeight", "float", 1.0),
        ("TintColor", "color", WHITE)]).then
    breath = g.pure(MATH, "Add_DoubleDouble", [("A", "real", 0.8), ("B", "real", g.mul(g.pure(MATH, "Sin", [("A", "real", g.mul(T, 0.7))], ty="real"), 0.2))])
    TW = g.mul(W, 0.56)
    TH = g.mul(TW, 0.25)
    TY = g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.mul(H, 0.25)), ("B", "real", g.mul(TH, 0.5))])
    a = g.call(HUD, "DrawTexture", a, [
        ("Texture", "texture", TITLE_TEX), ("ScreenX", "float", g.mul(W, 0.22)), ("ScreenY", "float", TY),
        ("ScreenW", "float", TW), ("ScreenH", "float", TH),
        ("TextureU", "float", 0.0), ("TextureV", "float", 0.0), ("TextureUWidth", "float", 1.0), ("TextureVHeight", "float", 1.0),
        ("TintColor", "color", g.pure(MATH, "MakeColor", [("R", "float", 1.0), ("G", "float", 1.0), ("B", "float", 1.0), ("A", "float", breath)], ty="color"))]).then
    a = g.call(HUD, "DrawRect", a, [("RectColor", "color", TITLE_RED), ("ScreenX", "float", g.mul(W, 0.4)),
                                    ("ScreenY", "float", g.pure(MATH, "Add_DoubleDouble", [("A", "real", TY), ("B", "real", g.mul(TH, 0.78))])),
                                    ("ScreenW", "float", g.mul(W, 0.2)), ("ScreenH", "float", g.mul(H, 0.0022))]).then
    # the menu, centred: START / CONTROLS / QUIT in the title's lettering, each key small in dark red beside it
    for k, (key, item) in enumerate(MENU):
        half = _menu_width(item, MENU_SCALE) / 2
        mx = g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.mul(W, 0.5)), ("B", "real", g.mul(H, half))])
        my = g.mul(H, 0.69 + k * 0.07)
        hov = g.pure(STR, "EqualEqual_StrStr", [("A", "string", g.get("MenuHover", "string")), ("B", "string", key)], ty="bool")
        col = g.pure(MATH, "SelectColor", [("A", "color", MENU_HOVER), ("B", "color", TEXT), ("bPickA", "bool", hov)], ty="color")
        a = draw(item, a, 0, 0, MENU_SCALE, col, font=MENU_FONT, at=(mx, my))
        a = g.call(HUD, "AddHitBox", a, [
            ("Position", "vector2d", g.pure(MATH, "MakeVector2D", [("X", "real", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", mx), ("B", "real", g.mul(H, 0.06))])),
                                                                  ("Y", "real", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", my), ("B", "real", g.mul(H, 0.01))]))], ty="vector2d")),
            ("Size", "vector2d", g.pure(MATH, "MakeVector2D", [("X", "real", g.mul(H, 2 * half + 0.09)), ("Y", "real", g.mul(H, 0.06))], ty="vector2d")),
            ("InName", "name", key), ("bConsumesInput", "bool", True), ("Priority", "int", 0)]).then
        a = draw(key, a, 0, 0, 0.75, "(R=0.5,G=0.1,B=0.08,A=1.0)", font=MENU_FONT,
                 at=(g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", mx), ("B", "real", g.mul(H, 0.075))]),
                     g.pure(MATH, "Add_DoubleDouble", [("A", "real", my), ("B", "real", g.mul(H, 0.008))])))
    ta = g.pure(MATH, "FMax", [("A", "real", 0.0), ("B", "real", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", 1.0),
               ("B", "real", g.mul(g.now(), 1.0 / TITLE_FADE))]))], ty="real")
    g.call(HUD, "DrawRect", a, [("RectColor", "color", g.pure(MATH, "MakeColor", [("R", "float", 0.0), ("G", "float", 0.0),
                                ("B", "float", 0.0), ("A", "float", ta)], ty="color")),
                                ("ScreenX", "float", 0.0), ("ScreenY", "float", 0.0), ("ScreenW", "float", W), ("ScreenH", "float", H)])
    def controls_page(after):
        # the controls page (second pass): over the dock scene, a dark panel, CONTROLS with a red rule, two groups
        # (MOVE / INTERACT) with each key as a keycap, BACK clickable
        cx = lambda fx: g.pure(MATH, "Add_DoubleDouble", [("A", "real", g.mul(W, 0.5)), ("B", "real", g.mul(H, fx))])
        a = g.call(HUD, "DrawTexture", after, [
            ("Texture", "texture", VIGNETTE_TEX), ("ScreenX", "float", 0.0), ("ScreenY", "float", 0.0), ("ScreenW", "float", W), ("ScreenH", "float", H),
            ("TextureU", "float", 0.0), ("TextureV", "float", 0.0), ("TextureUWidth", "float", 1.0), ("TextureVHeight", "float", 1.0),
            ("TintColor", "color", WHITE)]).then
        a = g.call(HUD, "DrawRect", a, [("RectColor", "color", "(R=0.01,G=0.01,B=0.015,A=0.82)"), ("ScreenX", "float", cx(-0.66)),
                                        ("ScreenY", "float", g.mul(H, 0.1)), ("ScreenW", "float", g.mul(H, 1.32)), ("ScreenH", "float", g.mul(H, 0.8))]).then
        tw = _menu_width("C O N T R O L S", 1.15) / 2
        a = draw("C O N T R O L S", a, 0, 0, 1.15, TEXT, font=MENU_FONT, at=(cx(-tw), g.mul(H, 0.15)))
        a = g.call(HUD, "DrawRect", a, [("RectColor", "color", TITLE_RED), ("ScreenX", "float", cx(-0.09)), ("ScreenY", "float", g.mul(H, 0.225)),
                                        ("ScreenW", "float", g.mul(H, 0.18)), ("ScreenH", "float", g.mul(H, 0.0022))]).then

        def keycap(after, label, fx, fy):
            """A key drawn as a keycap at (fx screen-heights from the centre, fy down); returns (after, its width)."""
            w = _menu_width(label, 0.75) + 0.03
            x0, y0, h = cx(fx), g.mul(H, fy), 0.052
            after = g.call(HUD, "DrawRect", after, [("RectColor", "color", CAP_FILL), ("ScreenX", "float", x0), ("ScreenY", "float", y0),
                                                    ("ScreenW", "float", g.mul(H, w)), ("ScreenH", "float", g.mul(H, h))]).then
            corners = [(fx, fy), (fx + w, fy), (fx + w, fy + h), (fx, fy + h)]
            for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
                after = g.call(HUD, "DrawLine", after, [("StartScreenX", "float", cx(ax)), ("StartScreenY", "float", g.mul(H, ay)),
                                                        ("EndScreenX", "float", cx(bx)), ("EndScreenY", "float", g.mul(H, by)),
                                                        ("LineColor", "color", CAP_EDGE), ("LineThickness", "float", 1.5)]).then
            after = draw(label, after, 0, 0, 0.75, TEXT, font=MENU_FONT, at=(cx(fx + 0.015), g.mul(H, fy + 0.008)))
            return after, w

        for col, (heading, rows, label_at) in enumerate((("M O V E", CONTROLS_MOVE, 0.27), ("I N T E R A C T", CONTROLS_USE, 0.16))):
            x0 = -0.56 if col == 0 else 0.06
            a = draw(heading, a, 0, 0, 0.8, "(R=0.6,G=0.12,B=0.1,A=1.0)", font=MENU_FONT, at=(cx(x0), g.mul(H, 0.3)))
            for k, (keys, what) in enumerate(rows):
                fy = 0.38 + k * 0.085
                fx = x0
                for key in keys:
                    a, w = keycap(a, key, fx, fy)
                    fx += w + 0.012
                a = draw(what, a, 0, 0, 0.82, TEXT, font=MENU_FONT, at=(cx(x0 + label_at), g.mul(H, fy + 0.008)))
        # BACK, clickable like the menu
        bw = _menu_width("B A C K", 0.9) / 2
        hov = g.pure(STR, "EqualEqual_StrStr", [("A", "string", g.get("MenuHover", "string")), ("B", "string", "C")], ty="bool")
        a = draw("B A C K", a, 0, 0, 0.9, g.pure(MATH, "SelectColor", [("A", "color", MENU_HOVER), ("B", "color", TEXT), ("bPickA", "bool", hov)], ty="color"),
                 font=MENU_FONT, at=(cx(-bw), g.mul(H, 0.8)))
        a = draw("C", a, 0, 0, 0.7, "(R=0.5,G=0.1,B=0.08,A=1.0)", font=MENU_FONT, at=(cx(-bw - 0.045), g.mul(H, 0.808)))
        g.call(HUD, "AddHitBox", a, [
            ("Position", "vector2d", g.pure(MATH, "MakeVector2D", [("X", "real", cx(-bw - 0.06)), ("Y", "real", g.mul(H, 0.79))], ty="vector2d")),
            ("Size", "vector2d", g.pure(MATH, "MakeVector2D", [("X", "real", g.mul(H, 2 * bw + 0.09)), ("Y", "real", g.mul(H, 0.06))], ty="vector2d")),
            ("InName", "name", "C"), ("bConsumesInput", "bool", True), ("Priority", "int", 0)])

    controls_page(ctl_yes)

    # ---- the pause menu (2026-11-17): same style as the title menu ----
    g.row(340 * 9, -6200)
    p_on, p_off = g.branch(g.get("Paused", "bool"), pause_then)
    # how to pause, in the top-right corner during play (user, 2026-11-17); P works in the editor and the game
    busy = g.pure(MATH, "BooleanOR", [("A", "bool", g.pure(MATH, "BooleanOR", [("A", "bool", g.get("Reading", "bool")),
                                                                               ("B", "bool", g.get("JournalOpen", "bool"))], ty="bool")),
                                      ("B", "bool", g.get("MapOpen", "bool"))], ty="bool")
    hint, _ = g.branch(g.not_(busy), p_off)
    # a button in the bottom-right corner (the corner map is top right): a keycap with P, PAUSE beside it
    rx = lambda fx: g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", W), ("B", "real", g.mul(H, fx))])   # fx heights in from the right
    bx, by, bw, bh = 0.27, 0.905, 0.052, 0.05
    a = g.call(HUD, "DrawRect", hint, [("RectColor", "color", CAP_FILL), ("ScreenX", "float", rx(bx)), ("ScreenY", "float", g.mul(H, by)),
                                       ("ScreenW", "float", g.mul(H, bw)), ("ScreenH", "float", g.mul(H, bh))]).then
    corners = [(bx, by), (bx - bw, by), (bx - bw, by + bh), (bx, by + bh)]
    for (ax, ay), (cx2, cy2) in zip(corners, corners[1:] + corners[:1]):
        a = g.call(HUD, "DrawLine", a, [("StartScreenX", "float", rx(ax)), ("StartScreenY", "float", g.mul(H, ay)),
                                        ("EndScreenX", "float", rx(cx2)), ("EndScreenY", "float", g.mul(H, cy2)),
                                        ("LineColor", "color", CAP_EDGE), ("LineThickness", "float", 1.5)]).then
    a = draw("P", a, 0, 0, 0.75, TEXT, font=MENU_FONT, at=(rx(bx - 0.016), g.mul(H, by + 0.007)))
    draw("P A U S E", a, 0, 0, 0.8, TEXT, font=MENU_FONT, at=(rx(bx - bw - 0.025), g.mul(H, by + 0.006)))
    p_ctl, p_menu = g.branch(g.get("ControlsOpen", "bool"), p_on)
    controls_page(p_ctl)
    a = g.call(HUD, "DrawRect", p_menu, [("RectColor", "color", "(R=0.0,G=0.0,B=0.0,A=0.6)"), ("ScreenX", "float", 0.0), ("ScreenY", "float", 0.0),
                                         ("ScreenW", "float", W), ("ScreenH", "float", H)]).then
    a = g.call(HUD, "DrawTexture", a, [
        ("Texture", "texture", VIGNETTE_TEX), ("ScreenX", "float", 0.0), ("ScreenY", "float", 0.0), ("ScreenW", "float", W), ("ScreenH", "float", H),
        ("TextureU", "float", 0.0), ("TextureV", "float", 0.0), ("TextureUWidth", "float", 1.0), ("TextureVHeight", "float", 1.0),
        ("TintColor", "color", WHITE)]).then
    ph = _menu_width("P A U S E D", 1.4) / 2
    a = draw("P A U S E D", a, 0, 0, 1.4, TEXT, font=MENU_FONT,
             at=(g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.mul(W, 0.5)), ("B", "real", g.mul(H, ph))]), g.mul(H, 0.28)))
    a = g.call(HUD, "DrawRect", a, [("RectColor", "color", TITLE_RED),
                                    ("ScreenX", "float", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.mul(W, 0.5)), ("B", "real", g.mul(H, 0.1))])),
                                    ("ScreenY", "float", g.mul(H, 0.37)), ("ScreenW", "float", g.mul(H, 0.2)), ("ScreenH", "float", g.mul(H, 0.0022))]).then
    for k, (keylab, item, hit) in enumerate(PAUSE_MENU):
        half = _menu_width(item, MENU_SCALE) / 2
        mx = g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.mul(W, 0.5)), ("B", "real", g.mul(H, half))])
        my = g.mul(H, 0.47 + k * 0.08)
        hov = g.pure(STR, "EqualEqual_StrStr", [("A", "string", g.get("MenuHover", "string")), ("B", "string", hit)], ty="bool")
        col = g.pure(MATH, "SelectColor", [("A", "color", MENU_HOVER), ("B", "color", TEXT), ("bPickA", "bool", hov)], ty="color")
        a = draw(item, a, 0, 0, MENU_SCALE, col, font=MENU_FONT, at=(mx, my))
        kw = _menu_width(keylab, 0.75) + 0.035
        a = draw(keylab, a, 0, 0, 0.75, "(R=0.5,G=0.1,B=0.08,A=1.0)", font=MENU_FONT,
                 at=(g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", mx), ("B", "real", g.mul(H, kw))]),
                     g.pure(MATH, "Add_DoubleDouble", [("A", "real", my), ("B", "real", g.mul(H, 0.008))])))
        a = g.call(HUD, "AddHitBox", a, [
            ("Position", "vector2d", g.pure(MATH, "MakeVector2D", [("X", "real", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", mx), ("B", "real", g.mul(H, kw + 0.02))])),
                                                                  ("Y", "real", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", my), ("B", "real", g.mul(H, 0.01))]))], ty="vector2d")),
            ("Size", "vector2d", g.pure(MATH, "MakeVector2D", [("X", "real", g.mul(H, 2 * half + kw + 0.05)), ("Y", "real", g.mul(H, 0.065))], ty="vector2d")),
            ("InName", "name", hit), ("bConsumesInput", "bool", True), ("Priority", "int", 0)]).then

    # ---- the ending ----
    g.row(340 * 9, -4200)
    et = g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", g.now()), ("B", "real", g.get("EndStart", "real"))])
    after = lambda k: g.pure(MATH, "Greater_DoubleDouble", [("A", "real", et), ("B", "real", k)], ty="bool")
    steps = g.sequence(end_yes, 5)
    # 1: her line, until the cut
    l_on = g.pure(MATH, "BooleanAND", [("A", "bool", after(END_T_LINE)), ("B", "bool", g.not_(after(END_T_BLACK)))], ty="bool")
    l_yes, _ = g.branch(l_on, steps[0])
    draw(END_LINE, l_yes, 0.42, 0.8, 1.3, TEXT, True)
    # 2: black from the cut until the final shot, with "One year later." fading in
    b_on = g.pure(MATH, "BooleanAND", [("A", "bool", after(END_T_BLACK)), ("B", "bool", g.not_(after(END_T_SHOT)))], ty="bool")
    b_yes, _ = g.branch(b_on, steps[1])
    a = g.call(HUD, "DrawRect", b_yes, [("RectColor", "color", BLACK), ("ScreenX", "float", 0.0), ("ScreenY", "float", 0.0),
                                        ("ScreenW", "float", W), ("ScreenH", "float", H)]).then
    y_on = g.pure(MATH, "BooleanAND", [("A", "bool", after(END_T_YEAR)), ("B", "bool", g.not_(after(END_T_YEAR_OUT)))], ty="bool")
    y_yes, _ = g.branch(y_on, a)
    ya = g.pure(MATH, "FMin", [("A", "real", 1.0), ("B", "real", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", et), ("B", "real", END_T_YEAR)]))], ty="real")
    ycol = g.pure(MATH, "MakeColor", [("R", "float", 0.78), ("G", "float", 0.75), ("B", "float", 0.68), ("A", "float", ya)], ty="color")
    draw("One year later.", y_yes, 0.43, 0.47, 1.2, ycol)
    # 3: once, at the final shot: show BP_FinalShot (the poster) and look through its camera
    s_yes, _ = g.branch(g.pure(MATH, "BooleanAND", [("A", "bool", after(END_T_SHOT)), ("B", "bool", g.not_(g.get("EndShot", "bool")))], ty="bool"), steps[2])
    a = g.set("EndShot", "bool", True, s_yes).then
    found = g.call(STATICS, "GetActorOfClass", a, [("ActorClass", "actorclass", FINAL_CLASS)], outs=[("ReturnValue", "actor")])
    shot = found.o["ReturnValue"]
    a = g.call(ACTOR, "SetActorHiddenInGame", found.then, [("bNewHidden", "bool", False)], target=(shot, "actor")).then
    g.call(PC, "SetViewTargetWithBlend", a, [("NewViewTarget", "actor", shot), ("BlendTime", "float", 0.0)],
           target=(g.pure(HUD, "GetOwningPlayerController", ty="pc"), "pc"))
    # 4: the shot fades up from black, then cuts to black at the end
    f_on = g.pure(MATH, "BooleanAND", [("A", "bool", after(END_T_SHOT)), ("B", "bool", g.not_(after(END_T_OUT)))], ty="bool")
    # warped on the dock until the cut to black, then one second just before the final shot cuts to black (user 2026-11-22)
    w_on = g.pure(MATH, "BooleanOR", [("A", "bool", g.not_(after(END_T_BLACK))), ("B", "bool", g.pure(MATH, "BooleanAND", [
        ("A", "bool", after(END_T_OUT - END_WARP)), ("B", "bool", g.not_(after(END_T_OUT)))], ty="bool"))], ty="bool")
    # no flashes once the ending starts (user 2026-11-22: "one small warp before it i dont like")
    a = g.call("/Script/Engine.KismetMaterialLibrary", "SetScalarParameterValue", steps[3],
               [("Collection", "mpc", MPC_PATH), ("ParameterName", "name", "WarpFlash"), ("ParameterValue", "float", 0.0)]).then
    a = g.call("/Script/Engine.KismetMaterialLibrary", "SetScalarParameterValue", a,
               [("Collection", "mpc", MPC_PATH), ("ParameterName", "name", "WarpWhole"),
                ("ParameterValue", "float", g.pure(MATH, "SelectFloat", [("A", "real", 1.0), ("B", "real", 0.0), ("bPickA", "bool", w_on)]))]).then
    f_yes, f_no = g.branch(f_on, a)
    fa = g.pure(MATH, "FMax", [("A", "real", 0.0), ("B", "real", g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", 1.0),
               ("B", "real", g.mul(g.pure(MATH, "Subtract_DoubleDouble", [("A", "real", et), ("B", "real", END_T_SHOT)]), 1.0 / END_SHOT_FADE))]))], ty="real")
    fcol = g.pure(MATH, "MakeColor", [("R", "float", 0.0), ("G", "float", 0.0), ("B", "float", 0.0), ("A", "float", fa)], ty="color")
    g.call(HUD, "DrawRect", f_yes, [("RectColor", "color", fcol), ("ScreenX", "float", 0.0), ("ScreenY", "float", 0.0),
                                    ("ScreenW", "float", W), ("ScreenH", "float", H)])
    o_yes, _ = g.branch(after(END_T_OUT), f_no)
    g.call(HUD, "DrawRect", o_yes, [("RectColor", "color", BLACK), ("ScreenX", "float", 0.0), ("ScreenY", "float", 0.0),
                                    ("ScreenW", "float", W), ("ScreenH", "float", H)])
    # 5: back to the title screen (user 2026-11-22; it used to quit): reload the level, which starts on the title
    q_yes, _ = g.branch(after(END_T_QUIT), steps[4])
    g.call(STATICS, "OpenLevel", q_yes, [("LevelName", "name", LEVEL_NAME), ("bAbsolute", "bool", True), ("Options", "string", "")])

    def freeze(after):
        a = g.call(CTRL, "SetIgnoreMoveInput", after, [("bNewMoveInput", "bool", True)], target=pc()).then
        return g.call(CTRL, "SetIgnoreLookInput", a, [("bNewLookInput", "bool", True)], target=pc()).then

    def unfreeze(after):
        return g.call(CTRL, "ResetIgnoreInputFlags", after, target=pc()).then

    def toast(text, after):
        a = g.set("Toast", "string", text, after).then
        return g.set("ToastTime", "real", g.now(), a).then

    # ---- E ----
    g.row(0, 2800)
    e = g.input_event("IA_Interact")
    def resume(after):
        a = g.set("Paused", "bool", False, after).then
        a = g.set("ControlsOpen", "bool", False, a).then
        a = g.set("MenuHover", "string", "", a).then
        a = g.set("bShowMouseCursor", "bool", False, a, target=(g.pure(HUD, "GetOwningPlayerController", ty="pc"), "pc", C(PC))).then
        a = g.call("/Script/UMG.WidgetBlueprintLibrary", "SetInputMode_GameOnly", a,
                   [("PlayerController", "pc", g.pure(HUD, "GetOwningPlayerController", ty="pc"))]).then
        g.call(STATICS, "SetGamePaused", a, [("bPaused", "bool", False)])

    def pause(after):
        a = g.set("Paused", "bool", True, after).then
        a = g.set("bShowMouseCursor", "bool", True, a, target=(g.pure(HUD, "GetOwningPlayerController", ty="pc"), "pc", C(PC))).then
        a = g.call("/Script/UMG.WidgetBlueprintLibrary", "SetInputMode_GameAndUIEx", a,
                   [("PlayerController", "pc", g.pure(HUD, "GetOwningPlayerController", ty="pc")), ("bHideCursorDuringCapture", "bool", False)]).then
        g.call(STATICS, "SetGamePaused", a, [("bPaused", "bool", True)])

    def start_game(after):
        a = g.set("Title", "bool", False, after).then
        a = g.set("OpenStart", "real", g.now(), a).then
        a = g.set("MenuHover", "string", "", a).then
        a = g.set("bShowMouseCursor", "bool", False, a, target=(g.pure(HUD, "GetOwningPlayerController", ty="pc"), "pc", C(PC))).then
        a = g.call("/Script/UMG.WidgetBlueprintLibrary", "SetInputMode_GameOnly", a,
                   [("PlayerController", "pc", g.pure(HUD, "GetOwningPlayerController", ty="pc"))]).then
        g.call(PC, "SetViewTargetWithBlend", a, [("NewViewTarget", "actor", g.pure(HUD, "GetOwningPawn", ty="actor")), ("BlendTime", "float", 0.0)],
               target=(g.pure(HUD, "GetOwningPlayerController", ty="pc"), "pc"))

    on_title, e_game = g.branch(g.get("Title", "bool"), e)
    start, _ = g.branch(g.not_(g.get("ControlsOpen", "bool")), on_title)
    start_game(start)
    _, e_live = g.branch(g.get("Ending", "bool"), e_game)
    in_open, e_play = g.branch(g.get("Opening", "bool"), e_live)
    ready, _ = g.branch(g.pure(MATH, "Greater_DoubleDouble", [("A", "real", open_t()), ("B", "real", OPEN_T_GO)], ty="bool"), in_open)
    a = g.set("Opening", "bool", False, ready).then
    unfreeze(g.set("OpenEnd", "real", g.now(), a).then)
    b_read, b_not_read = g.branch(g.get("Reading", "bool"), e_play)
    a = g.set("Reading", "bool", False, b_read).then
    # either sheet in the wrong hand (the shack's second page is, user 2026-11-22: "didn't see a small warp")
    is_wrong = g.pure(MATH, "BooleanOR", [
        ("A", "bool", g.pure(STR, "EqualEqual_StrStr", [("A", "string", g.get("ReadHand", "string")), ("B", "string", "wrong")], ty="bool")),
        ("B", "bool", g.pure(STR, "EqualEqual_StrStr", [("A", "string", g.get("ReadHand2", "string")), ("B", "string", "wrong")], ty="bool"))], ty="bool")
    w_yes, w_no = g.branch(is_wrong, a)
    a = g.set("WarpUntil", "real", g.pure(MATH, "Add_DoubleDouble", [("A", "real", g.now()), ("B", "real", WARP_AFTER)]), w_yes).then
    ends, plain = g.branch(g.get("ReadEnds", "bool"), [a, w_no])
    unfreeze(plain)
    g.set("EndStart", "real", g.now(), g.set("Ending", "bool", True, ends).then)
    g.row(340, 3300)
    b_jour, b_not_jour = g.branch(g.get("JournalOpen", "bool"), b_not_read)
    unfreeze(g.set("JournalOpen", "bool", False, b_jour).then)
    g.row(680, 3800)
    v_yes, _ = g.branch(g.pure(SYS, "IsValid", [("Object", "object", g.get("Focus", "ex"))], ty="bool"), b_not_jour)
    _, not_open = g.branch(fget("Opened", "bool"), v_yes)
    unlocked = g.pure(MATH, "BooleanOR", [
        ("A", "bool", g.empty(fget("NeedsKey"))),
        ("B", "bool", g.pure(STR, "Contains", [("SearchIn", "string", g.get("Keys", "string")),
                                              ("Substring", "string", fget("NeedsKey"))], ty="bool"))], ty="bool")
    ok, locked = g.branch(unlocked, not_open)
    steps = g.sequence(ok, 4)
    g.row(340 * 5, 4500)
    toast(fget("LockedText"), locked)

    # 0: open its page
    g.row(340 * 5, 5000)
    p_yes, _ = g.branch(g.not_(g.empty(fget("Body"))), steps[0])
    a = g.set("ReadTitle", "string", fget("Title"), p_yes).then
    a = g.set("ReadBody", "string", fget("Body"), a).then
    a = g.set("ReadHand", "string", fget("Hand"), a).then
    a = g.set("ReadPaper", "string", fget("Paper"), a).then
    a = g.set("ReadBody2", "string", fget("Body2"), a).then      # a second sheet beside it (2026-11-22)
    a = g.set("ReadHand2", "string", fget("Hand2"), a).then
    a = g.set("ReadPaper2", "string", fget("Paper2"), a).then
    a = g.set("ReadEnds", "bool", fget("EndsGame", "bool"), a).then
    freeze(g.set("Reading", "bool", True, a).then)
    # 1: first time only - journal, key, objective
    g.row(340 * 5, 5700)
    _, first = g.branch(fget("Done", "bool"), steps[1])
    glint = g.get("Glint", "smc", focus())
    first = g.call(SCENE, "SetVisibility", first, [("bNewVisibility", "bool", False)], target=(glint, "scene")).then
    # remember that this clue has been read: "#<id>," in Keys (the area check below looks for these)
    first = g.set("Keys", "string", g.concat(g.concat(g.concat(g.get("Keys", "string"), "#"), fget("ClueId")), ","), first).then
    sub = g.sequence(first, 4)
    g.row(340 * 7, 6200)
    y, _ = g.branch(g.not_(g.empty(fget("Journal"))), sub[0])
    g.set("Journal", "string", g.concat(g.concat(g.get("Journal", "string"), fget("Journal")), g.get("Gap", "string")), y)
    g.row(340 * 7, 6900)
    y, _ = g.branch(g.not_(g.empty(fget("GivesKey"))), sub[1])
    a = g.set("Keys", "string", g.concat(g.concat(g.get("Keys", "string"), fget("GivesKey")), ","), y).then
    # Cas's map: open it straight away (paused, like M) with her line under it, instead of a page
    is_map, _ = g.branch(g.pure(STR, "Contains", [("SearchIn", "string", fget("GivesKey")),
                                                        ("Substring", "string", "map")], ty="bool"), a)
    # (no "Picked up: <title>" message any more: user 2026-11-17)
    g.row(340 * 9, 6900)
    a = toast(fget("Journal"), is_map)
    g.call(STATICS, "SetGamePaused", g.set("MapOpen", "bool", True, a).then, [("bPaused", "bool", True)])
    g.row(340 * 7, 7600)
    y, _ = g.branch(g.not_(g.empty(fget("Objective"))), sub[2])
    # the last clue read in an area (AreaNeed1 + AreaNeed2 = the other two already read) points on: AreaNext
    has = lambda k: g.pure(STR, "Contains", [("SearchIn", "string", g.get("Keys", "string")), ("Substring", "string", fget(k))], ty="bool")
    area_done = g.pure(MATH, "BooleanAND", [("A", "bool", g.not_(g.empty(fget("AreaNext")))),
                                            ("B", "bool", g.pure(MATH, "BooleanAND", [("A", "bool", has("AreaNeed1")), ("B", "bool", has("AreaNeed2"))], ty="bool"))], ty="bool")
    g.row(340 * 9, 7600)
    nxt, own = g.branch(area_done, y)
    g.set("Objective", "string", fget("AreaNext"), nxt)
    g.set("Objective", "string", fget("Objective"), own)
    g.row(340 * 7, 8200)
    g.set("Done", "bool", True, sub[3], target=focus())
    # 2: doors swing open
    g.row(340 * 5, 8800)
    y, _ = g.branch(fget("IsDoor", "bool"), steps[2])
    g.set("Opened", "bool", True, y, target=focus())
    # 3: pickups disappear
    g.row(340 * 5, 9400)
    y, _ = g.branch(fget("PickUp", "bool"), steps[3])
    g.call(ACTOR, "K2_DestroyActor", y, target=(g.get("Focus", "ex"), "actor"))

    # ---- mouse on the title menu: hover lights an item red, a click does what its key does ----
    g.row(0, 13800)
    over = g.event(HUD, "ReceiveHitBoxBeginCursorOver", [("BoxName", "name")])
    g.set("MenuHover", "string", g.pure(STR, "Conv_NameToString", [("InName", "name", over.o["BoxName"])], ty="string"), over.then)
    g.row(0, 14200)
    out = g.event(HUD, "ReceiveHitBoxEndCursorOver", [("BoxName", "name")])
    g.set("MenuHover", "string", "", out.then)
    g.row(0, 14600)
    click = g.event(HUD, "ReceiveHitBoxClick", [("BoxName", "name")])
    c_title, _ = g.branch(g.pure(MATH, "BooleanOR", [("A", "bool", g.get("Title", "bool")), ("B", "bool", g.get("Paused", "bool"))], ty="bool"), click.then)
    which = lambda key: g.pure(MATH, "EqualEqual_NameName", [("A", "name", click.o["BoxName"]), ("B", "name", key)], ty="bool")
    is_e, not_e = g.branch(which("E"), c_title)
    start_game(is_e)
    g.row(340 * 2, 15000)
    is_c, not_c = g.branch(which("C"), not_e)
    a = g.set("MenuHover", "string", "", is_c).then
    g.set("ControlsOpen", "bool", g.not_(g.get("ControlsOpen", "bool")), a)
    is_q, not_q = g.branch(which("Q"), not_c)
    is_r, _ = g.branch(which("P_RESUME"), not_q)
    resume(is_r)
    g.call(SYS, "QuitGame", is_q, [("SpecificPlayer", "pc", g.pure(HUD, "GetOwningPlayerController", ty="pc"))])

    # ---- C: the controls page (title screen) ----
    g.row(0, 12600)
    ckey = g.input_event("IA_Controls")
    t_yes, _ = g.branch(g.pure(MATH, "BooleanOR", [("A", "bool", g.get("Title", "bool")), ("B", "bool", g.get("Paused", "bool"))], ty="bool"), ckey)
    g.set("ControlsOpen", "bool", g.not_(g.get("ControlsOpen", "bool")), t_yes)
    # ---- Q: quit (title screen) ----
    g.row(0, 13200)
    qkey = g.input_event("IA_Quit")
    q_yes, _ = g.branch(g.pure(MATH, "BooleanAND", [("A", "bool", g.pure(MATH, "BooleanOR", [("A", "bool", g.get("Title", "bool")),
                                                                                              ("B", "bool", g.get("Paused", "bool"))], ty="bool")),
                                                    ("B", "bool", g.not_(g.get("ControlsOpen", "bool")))], ty="bool"), qkey)
    g.call(SYS, "QuitGame", q_yes, [("SpecificPlayer", "pc", g.pure(HUD, "GetOwningPlayerController", ty="pc"))])

    # ---- Esc / P: pause ----
    g.row(0, 15600)
    pkey = g.input_event("IA_Pause")
    is_p, not_p = g.branch(g.get("Paused", "bool"), pkey)
    in_ctl, not_ctl = g.branch(g.get("ControlsOpen", "bool"), is_p)
    g.set("ControlsOpen", "bool", False, in_ctl)                    # Esc on the controls page: back to the pause menu
    resume(not_ctl)
    blocked = g.pure(MATH, "BooleanOR", [("A", "bool", g.pure(MATH, "BooleanOR", [("A", "bool", g.get("Title", "bool")),
                                                                                   ("B", "bool", g.get("Opening", "bool"))], ty="bool")),
                                          ("B", "bool", g.pure(MATH, "BooleanOR", [("A", "bool", g.get("Ending", "bool")),
                                                                                   ("B", "bool", g.get("MapOpen", "bool"))], ty="bool"))], ty="bool")
    ok, _ = g.branch(g.not_(blocked), not_p)
    pause(ok)

    # ---- Tab: the journal is switched off (user 2026-11-22: "turn journal off"); IA_Journal does nothing now ----

    # ---- M: the full map, pauses the game (IA_Map works while paused) ----
    g.row(0, 11400)
    mkey = g.input_event("IA_Map")
    _, free = g.branch(g.pure(MATH, "BooleanOR", [("A", "bool", g.get("Reading", "bool")),
                                                 ("B", "bool", g.pure(MATH, "BooleanOR", [("A", "bool", g.get("JournalOpen", "bool")),
                                                 ("B", "bool", g.get("Ending", "bool"))], ty="bool"))], ty="bool"), mkey)
    got_map, _ = g.branch(g.pure(STR, "Contains", [("SearchIn", "string", g.get("Keys", "string")),
                                                   ("Substring", "string", "map")], ty="bool"), free)   # only once you have the map
    shut, opn = g.branch(g.get("MapOpen", "bool"), got_map)
    # opening or closing the map with M clears the message, so her line only ever shows the
    # first time (when picking it up opens the map) and no other message lands on the map screen
    shut = g.set("Toast", "string", "", shut).then
    opn = g.set("Toast", "string", "", opn).then
    g.call(STATICS, "SetGamePaused", g.set("MapOpen", "bool", False, shut).then, [("bPaused", "bool", False)])
    g.row(340 * 2, 11900)
    g.call(STATICS, "SetGamePaused", g.set("MapOpen", "bool", True, opn).then, [("bPaused", "bool", True)])
    return g


# ======================= BP_Examinable =======================

def door_graph():
    g = Graph("/Game/Horror/Interact/BP_Examinable.BP_Examinable:EventGraph")
    g.row(0, 0)
    tick = g.event(ACTOR, "ReceiveTick", [("DeltaSeconds", "float")])
    yes, _ = g.branch(g.get("Opened", "bool"), tick.then)
    yaw = g.pure(MATH, "FInterpTo", [("Current", "real", g.get("Yaw", "real")), ("Target", "real", g.get("OpenAngle", "real")),
                                    ("DeltaTime", "real", tick.o["DeltaSeconds"]), ("InterpSpeed", "real", 2.5)])
    s = g.set("Yaw", "real", yaw, yes)
    rot = g.pure(MATH, "MakeRotator", [("Roll", "float", 0.0), ("Pitch", "float", 0.0),
                                      ("Yaw", "float", g.get("Yaw", "real"))], ty="rotator")
    g.call(SCENE, "K2_SetRelativeRotation", s.then, [("NewRotation", "rotator", rot)],
           target=(g.get("Hinge", "scene"), "scene"))
    return g


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "hud"
    print({"hud": hud_graph, "door": door_graph}[which]().text())

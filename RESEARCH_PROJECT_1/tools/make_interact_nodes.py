"""Write the Blueprint logic for the interaction system as paste-able node text.

    python make_interact_nodes.py hud   > hud.txt    (paste into BP_HorrorHUD's Event Graph)
    python make_interact_nodes.py door  > door.txt   (paste into BP_Examinable's Event Graph)

Same idea as make_bob_run_nodes.py: Unreal's Python can't add Blueprint nodes, but the graph
editor accepts nodes pasted as text. The assets and variables come from unreal/interact_setup.py.

BP_HorrorHUD
  Event Draw HUD (every frame):
    aim line 2.6 m from the camera -> Focus (clues have a slightly bigger invisible HitBox) = the BP_Examinable you look at (or nothing)
    (a clue you spotted keeps the prompt when you look away, until you use it or walk 3 m off)
    draw the objective (top left) and the latest message for 3 s (lower left)
    Reading?      -> dark screen with the page's title and text, "[E] Close"
    Journal open? -> dark screen with every journal line, "[Tab] Close"
    otherwise     -> "[E] Examine" (or the object's own Prompt) on a dark box when looking at something
  E:   close the page / journal, or use Focus:
         locked (NeedsKey not in Keys) -> show LockedText
         else -> open its page (Body), and the first time: journal line, key, objective;
                 doors swing open, pickups disappear
  Tab: open / close the journal (not while reading)
  Movement and mouse look are frozen while a page or the journal is open.
BP_Examinable
  Event Tick: once Opened, Hinge turns smoothly to OpenAngle (the door swings).
"""
import sys
import uuid

K2 = "/Script/BlueprintGraph."
MATH, SYS, STR, STATICS = ("/Script/Engine.KismetMathLibrary", "/Script/Engine.KismetSystemLibrary",
                           "/Script/Engine.KismetStringLibrary", "/Script/Engine.GameplayStatics")
ACTOR, HUD, PC, CAM, CTRL, SCENE = ("/Script/Engine.Actor", "/Script/Engine.HUD", "/Script/Engine.PlayerController",
                                    "/Script/Engine.PlayerCameraManager", "/Script/Engine.Controller",
                                    "/Script/Engine.SceneComponent")
EX_CLASS = "/Script/Engine.BlueprintGeneratedClass'/Game/Horror/Interact/BP_Examinable.BP_Examinable_C'"
FONT = "/Game/Horror/UI/F_HUD_Italic.F_HUD_Italic"            # Roboto Italic (made by interact_setup.py)
TEXT = "(R=0.78,G=0.75,B=0.68,A=1.000000)"                   # warm off-white
DIM = "(R=0.55,G=0.53,B=0.5,A=1.000000)"
DARK = "(R=0.004,G=0.004,B=0.006,A=0.930000)"
SHADOW = "(R=0.0,G=0.0,B=0.0,A=0.850000)"
PROMPT_BOX = "(R=0.0,G=0.0,B=0.0,A=0.550000)"     # dark box behind "[E] Examine"
TEXT_SCALE = 0.0032            # text size = screen height * this (3.2 at 1000 px tall)
REACH, NEAR = 260.0, 40.0      # aim line from 40 cm in front of the eyes (outside the capsule) to 2.6 m
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
    "font": _t("object", obj=C("/Script/Engine.Font")), "scene": _t("object", obj=C(SCENE)),
    "ex": _t("object", obj=EX_CLASS),
}


class Pin:
    def __init__(self, node, name, out, ty, default=None):
        self.node, self.name, self.out, self.ty, self.default = node, name, out, ty, default
        self.id, self.links = gid(), []


def fmt_default(ty, v):
    if ty == "bool":
        return f'DefaultValue="{"true" if v else "false"}"'
    if ty in ("font",):
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

    # ---- Begin Play: let this HUD receive E and Tab ----
    g.row(0, 0)
    bp = g.event(ACTOR, "ReceiveBeginPlay", [])
    g.call(ACTOR, "EnableInput", bp.then, [("PlayerController", "pc",
           g.pure(HUD, "GetOwningPlayerController", ty="pc"))])

    # ---- Draw HUD ----
    g.row(0, 600)
    ev = g.event(HUD, "ReceiveDrawHUD", [("SizeX", "int"), ("SizeY", "int")])
    W = g.pure(MATH, "Conv_IntToDouble", [("InInt", "int", ev.o["SizeX"])])
    H = g.pure(MATH, "Conv_IntToDouble", [("InInt", "int", ev.o["SizeY"])])
    TS = g.mul(H, TEXT_SCALE)

    def draw(text, after, x, y, scale=1.0, color=TEXT, shadow=False):
        """DrawText at a fraction of the screen. shadow: a black copy just behind it first,
        so the words stay readable on a bright wall."""
        if shadow:
            after = draw(text, after, x + 0.0012, y + 0.0018, scale, SHADOW)
        return g.call(HUD, "DrawText", after, [
            ("Text", "string", text), ("TextColor", "color", color),
            ("ScreenX", "float", g.mul(W, x)), ("ScreenY", "float", g.mul(H, y)),
            ("Font", "font", FONT), ("Scale", "float", g.mul(TS, scale) if scale != 1.0 else TS)]).then

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
    trace = g.call(SYS, "LineTraceSingle", ev.then, [("Start", "vector", start), ("End", "vector", end),
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

    # objective + message
    after = draw(g.get("Objective", "string"), [s_hit.then, k_yes, s_none.then], 0.04, 0.05, 0.8, DIM, True)
    fresh = g.pure(MATH, "Less_DoubleDouble", [("A", "real", g.pure(MATH, "Subtract_DoubleDouble", [
        ("A", "real", g.now()), ("B", "real", g.get("ToastTime", "real"))])), ("B", "real", 3.0)], ty="bool")
    t_yes, t_no = g.branch(fresh, after)
    toast_done = draw(g.get("Toast", "string"), t_yes, 0.04, 0.8, 0.9, TEXT, True)

    # reading screen
    r_yes, r_no = g.branch(g.get("Reading", "bool"), [toast_done, t_no])
    a = dark(r_yes)
    a = draw(g.get("ReadTitle", "string"), a, 0.2, 0.14, 1.25)
    a = draw(g.get("ReadBody", "string"), a, 0.2, 0.24)
    draw("[E]  Close", a, 0.2, 0.88, 0.75, DIM)

    # journal
    g.row(340 * 9, 1300)
    j_yes, j_no = g.branch(g.get("JournalOpen", "bool"), r_no)
    a = dark(j_yes)
    a = draw("JOURNAL", a, 0.2, 0.14, 1.25)
    a = draw(g.get("Journal", "string"), a, 0.2, 0.24)
    draw("[Tab]  Close", a, 0.2, 0.88, 0.75, DIM)

    # prompt
    g.row(340 * 9, 2000)
    v_yes, _ = g.branch(g.pure(SYS, "IsValid", [("Object", "object", g.get("Focus", "ex"))], ty="bool"), j_no)
    o_yes, _ = g.branch(g.not_(fget("Opened", "bool")), v_yes)
    box = g.call(HUD, "DrawRect", o_yes, [
        ("RectColor", "color", PROMPT_BOX), ("ScreenX", "float", g.mul(W, 0.43)), ("ScreenY", "float", g.mul(H, 0.548)),
        ("ScreenW", "float", g.mul(W, 0.15)), ("ScreenH", "float", g.mul(H, 0.06))]).then
    draw(g.concat("[E]  ", fget("Prompt")), box, 0.45, 0.556, 0.8, TEXT, True)

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
    b_read, b_not_read = g.branch(g.get("Reading", "bool"), e)
    unfreeze(g.set("Reading", "bool", False, b_read).then)
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
    freeze(g.set("Reading", "bool", True, a).then)
    # 1: first time only - journal, key, objective
    g.row(340 * 5, 5700)
    _, first = g.branch(fget("Done", "bool"), steps[1])
    sub = g.sequence(first, 4)
    g.row(340 * 7, 6200)
    y, _ = g.branch(g.not_(g.empty(fget("Journal"))), sub[0])
    g.set("Journal", "string", g.concat(g.concat(g.get("Journal", "string"), fget("Journal")), g.get("Gap", "string")), y)
    g.row(340 * 7, 6900)
    y, _ = g.branch(g.not_(g.empty(fget("GivesKey"))), sub[1])
    a = g.set("Keys", "string", g.concat(g.concat(g.get("Keys", "string"), fget("GivesKey")), ","), y).then
    toast(g.concat("Picked up: ", fget("Title")), a)
    g.row(340 * 7, 7600)
    y, _ = g.branch(g.not_(g.empty(fget("Objective"))), sub[2])
    g.set("Objective", "string", fget("Objective"), y)
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

    # ---- Tab ----
    g.row(0, 10200)
    tab = g.input_event("IA_Journal")
    _, free = g.branch(g.get("Reading", "bool"), tab)
    shut, opn = g.branch(g.get("JournalOpen", "bool"), free)
    unfreeze(g.set("JournalOpen", "bool", False, shut).then)
    g.row(340 * 2, 10700)
    freeze(g.set("JournalOpen", "bool", True, opn).then)
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

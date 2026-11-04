"""Write the Blueprint nodes for head bob + running as paste-able text.

    python make_bob_run_nodes.py > nodes.txt     (then paste into BP_FirstPersonCharacter's Event Graph)

Unreal's Python can't add Blueprint nodes, but the graph editor accepts nodes pasted as text
(the same text you get from Ctrl+C on nodes). This builds that text, pins and wires included:

  Event Tick -> Branch(IsValid(BobShake))
      false: GetPlayerCameraManager -> StartCameraShake(CS_WalkBob, scale 0) -> set BobShake
      true:  BobShake.ShakeScale = clamp(VSizeXY(GetVelocity) / WALK, 0, MAX_BOB)
  IA_Run Started   -> CharacterMovement.MaxWalkSpeed = RUN
  IA_Run Completed -> CharacterMovement.MaxWalkSpeed = WALK
"""
import uuid

WALK, RUN, MAX_BOB = 300.0, 550.0, 1.6
X0, Y0 = 3400, -2400                       # where the nodes land, right of the template's nodes
BP = "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter.BP_FirstPersonCharacter:EventGraph"


def gid():
    return uuid.uuid4().hex.upper()


class Node:
    def __init__(self, cls, name, x, y, props=""):
        self.cls, self.name, self.x, self.y, self.props = cls, name, X0 + x, Y0 + y, props
        self.pins = []                       # [name, direction, category, default, pin id, links]

    def pin(self, name, out=False, cat="", default=None):
        p = [name, out, cat, default, gid(), []]
        self.pins.append(p)
        return p

    def text(self):
        short = self.cls.rsplit(".", 1)[1]
        lines = [f'Begin Object Class={self.cls} Name="{self.name}" ExportPath="{self.cls}\'{BP}.{self.name}\'"']
        if self.props:
            lines.append("   " + self.props)
        lines += [f"   NodePosX={self.x}", f"   NodePosY={self.y}", f"   NodeGuid={gid()}"]
        for name, out, cat, default, pid, links in self.pins:
            parts = [f"PinId={pid}", f'PinName="{name}"']
            if out:
                parts.append('Direction="EGPD_Output"')
            if cat:
                parts.append(TYPES.get(cat, f'PinType.PinCategory="{cat}"'))
            if default is not None:
                parts.append(default)
            if links:
                parts.append("LinkedTo=(" + ",".join(f"{n} {i}" for n, i in links) + ",)")
            lines.append("   CustomProperties Pin (" + ",".join(parts) + ")")
        lines.append("End Object")
        return "\n".join(lines)


def wire(node_a, pin_a, node_b, pin_b):
    pin_a[5].append((node_b.name, pin_b[4]))
    pin_b[5].append((node_a.name, pin_a[4]))


K2 = "/Script/BlueprintGraph."

# Full pin types: Unreal matches pasted pins by name AND type; a bare category ("object")
# doesn't match the real pin, so the wire gets orphaned (that's what happened the first time).
def _t(cat, sub="", obj="None"):
    obj = obj if obj == "None" else f'"{obj}"'
    return (f'PinType.PinCategory="{cat}",PinType.PinSubCategory="{sub}",PinType.PinSubCategoryObject={obj},'
            'PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,'
            'PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False')
_C = lambda path: f"/Script/CoreUObject.Class'{path}'"
TYPES = {
    "exec": _t("exec"), "bool": _t("bool"), "int": _t("int"),
    "real": _t("real", "double"), "float": _t("real", "float"),
    "vector": _t("struct", obj="/Script/CoreUObject.ScriptStruct'/Script/CoreUObject.Vector'"),
    "object": _t("object", obj=_C("/Script/CoreUObject.Object")),
    "shake": _t("object", obj=_C("/Script/Engine.CameraShakeBase")),
    "shakeclass": _t("class", obj=_C("/Script/Engine.CameraShakeBase")),
    "camman": _t("object", obj=_C("/Script/Engine.PlayerCameraManager")),
    "move": _t("object", obj=_C("/Script/Engine.CharacterMovementComponent")),
}
CLS = lambda path: f"/Script/CoreUObject.Class'{path}'"
FN = lambda owner, name: f'FunctionReference=(MemberParent="{CLS(owner)}",MemberName="{name}")'
MEMBER = lambda owner, name: f'VariableReference=(MemberParent="{CLS(owner)}",MemberName="{name}")'
SELFVAR = lambda name: f'VariableReference=(MemberName="{name}",bSelfContext=True)'
MATH, SYS, STATICS = "/Script/Engine.KismetMathLibrary", "/Script/Engine.KismetSystemLibrary", "/Script/Engine.GameplayStatics"

nodes = []
def N(*a, **k):
    n = Node(*a, **k)
    nodes.append(n)
    return n

# --- head bob ---
tick = N(K2 + "K2Node_Event", "K2Node_Event_BobTick", 0, 0,
         f'EventReference=(MemberParent="{CLS("/Script/Engine.Actor")}",MemberName="ReceiveTick")\n   bOverrideFunction=True')
tick_then = tick.pin("then", True, "exec")
tick.pin("DeltaSeconds", True, "float")

get_a = N(K2 + "K2Node_VariableGet", "K2Node_VariableGet_BobA", 0, 160, SELFVAR("BobShake"))
get_a_out = get_a.pin("BobShake", True, "shake")
valid = N(K2 + "K2Node_CallFunction", "K2Node_CallFunction_BobValid", 220, 160, FN(SYS, "IsValid"))
valid_in = valid.pin("Object", cat="object")
valid_out = valid.pin("ReturnValue", True, "bool")
wire(get_a, get_a_out, valid, valid_in)

branch = N(K2 + "K2Node_IfThenElse", "K2Node_IfThenElse_Bob", 480, 0)
br_exec, br_cond = branch.pin("execute", cat="exec"), branch.pin("Condition", cat="bool")
br_true, br_false = branch.pin("then", True, "exec"), branch.pin("else", True, "exec")
wire(tick, tick_then, branch, br_exec)
wire(valid, valid_out, branch, br_cond)

# false: start the shake once and keep it
cam = N(K2 + "K2Node_CallFunction", "K2Node_CallFunction_BobCam", 480, 300, FN(STATICS, "GetPlayerCameraManager"))
cam.pin("PlayerIndex", cat="int", default='DefaultValue="0"')
cam_out = cam.pin("ReturnValue", True, "camman")
start = N(K2 + "K2Node_CallFunction", "K2Node_CallFunction_BobStart", 760, 200,
          FN("/Script/Engine.PlayerCameraManager", "StartCameraShake"))
st_exec, st_then = start.pin("execute", cat="exec"), start.pin("then", True, "exec")
st_self = start.pin("self", cat="camman")
start.pin("ShakeClass", cat="shakeclass", default='DefaultObject="/Game/Horror/Player/CS_WalkBob.CS_WalkBob_C"')
start.pin("Scale", cat="float", default='DefaultValue="0.0"')
st_out = start.pin("ReturnValue", True, "shake")
wire(branch, br_false, start, st_exec)
wire(cam, cam_out, start, st_self)
keep = N(K2 + "K2Node_VariableSet", "K2Node_VariableSet_BobKeep", 1100, 200, SELFVAR("BobShake"))
kp_exec = keep.pin("execute", cat="exec")
keep.pin("then", True, "exec")
kp_val = keep.pin("BobShake", cat="shake")
wire(start, st_then, keep, kp_exec)
wire(start, st_out, keep, kp_val)

# true: shake strength follows walking speed
get_b = N(K2 + "K2Node_VariableGet", "K2Node_VariableGet_BobB", 760, -120, SELFVAR("BobShake"))
get_b_out = get_b.pin("BobShake", True, "shake")
vel = N(K2 + "K2Node_CallFunction", "K2Node_CallFunction_BobVel", 0, -300,
        FN("/Script/Engine.Actor", "GetVelocity"))
vel_out = vel.pin("ReturnValue", True, "vector")
size = N(K2 + "K2Node_CallFunction", "K2Node_CallFunction_BobSize", 240, -300, FN(MATH, "VSizeXY"))
size_in, size_out = size.pin("A", cat="vector"), size.pin("ReturnValue", True, "real")
div = N(K2 + "K2Node_CallFunction", "K2Node_CallFunction_BobDiv", 480, -300, FN(MATH, "Divide_DoubleDouble"))
div_a = div.pin("A", cat="real")
div.pin("B", cat="real", default=f'DefaultValue="{WALK}"')
div_out = div.pin("ReturnValue", True, "real")
clamp = N(K2 + "K2Node_CallFunction", "K2Node_CallFunction_BobClamp", 720, -300, FN(MATH, "FClamp"))
cl_v = clamp.pin("Value", cat="real")
clamp.pin("Min", cat="real", default='DefaultValue="0.0"')
clamp.pin("Max", cat="real", default=f'DefaultValue="{MAX_BOB}"')
cl_out = clamp.pin("ReturnValue", True, "real")
wire(vel, vel_out, size, size_in)
wire(size, size_out, div, div_a)
wire(div, div_out, clamp, cl_v)
scale = N(K2 + "K2Node_VariableSet", "K2Node_VariableSet_BobScale", 1100, -120,
          MEMBER("/Script/Engine.CameraShakeBase", "ShakeScale"))
sc_exec = scale.pin("execute", cat="exec")
scale.pin("then", True, "exec")
sc_self = scale.pin("self", cat="shake")
sc_val = scale.pin("ShakeScale", cat="float")
wire(branch, br_true, scale, sc_exec)
wire(get_b, get_b_out, scale, sc_self)
wire(clamp, cl_out, scale, sc_val)

# --- running ---
run = N("/Script/InputBlueprintNodes.K2Node_EnhancedInputAction", "K2Node_EnhancedInputAction_Run", 0, 600,
        "InputAction=\"/Script/EnhancedInput.InputAction'/Game/FirstPerson/Input/Actions/IA_Run.IA_Run'\"")
run_start, run_done = run.pin("Started", True, "exec"), run.pin("Completed", True, "exec")
move = N(K2 + "K2Node_VariableGet", "K2Node_VariableGet_RunMove", 240, 820,
         f'VariableReference=(MemberParent="{CLS("/Script/Engine.Character")}",MemberName="CharacterMovement",bSelfContext=True)')
move_out = move.pin("CharacterMovement", True, "move")
for label, speed, y, src in (("Fast", RUN, 600, run_start), ("Slow", WALK, 760, run_done)):
    s = N(K2 + "K2Node_VariableSet", f"K2Node_VariableSet_Run{label}", 520, y,
          MEMBER("/Script/Engine.CharacterMovementComponent", "MaxWalkSpeed"))
    e = s.pin("execute", cat="exec")
    s.pin("then", True, "exec")
    sp = s.pin("self", cat="move")
    s.pin("MaxWalkSpeed", cat="float", default=f'DefaultValue="{speed}"')
    wire(run, src, s, e)
    wire(move, move_out, s, sp)

print("\n".join(n.text() for n in nodes))

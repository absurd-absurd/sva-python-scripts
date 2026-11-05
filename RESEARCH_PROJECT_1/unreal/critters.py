"""Put the small living things into the level: moths at the lights, fireflies in the woods and
along the lake, clouds of gnats, bats at the lot lamp and over the lake, a flock circling high
over the dock.

Run in the Unreal editor after maya/make_critters.py has exported export/critter_*.fbx.
Safe to run again (old critters, tag "critter", are removed first).

How they move: no Blueprints. Every critter is a plain static mesh with M_PS2_Critter, a copy of
the PS2 surface material whose vertex shader (World Position Offset) moves the whole critter
along a looping path, turns it to face where it's going and flaps its wings. Each one gets its
own phase from its position, so no two move alike. Fireflies blink through Emissive.
Paths (Mode): 0 orbit a point (moths around a lamp, bats), 1 drift around a point (fireflies,
gnats), 2 flock (one big slow circle shared by the whole flock).
"""
import json
import math
import random

import unreal

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
DIR = "/Game/Horror/Critters"
SURFACE = "/Game/Horror/Materials/PS2/M_PS2_Surface"
CRITTER = "/Game/Horror/Materials/PS2/M_PS2_Critter"
TAG = "critter"
lib = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

MOVE_HLSL = """
// Whole-critter motion + facing + wing flap, as a world offset for every vertex.
float3 L = WPos - OPos;                                    // vertex relative to the critter's middle
float R = frac(sin(dot(OPos.xy, float2(12.9898, 78.233)) + OPos.z * 0.123) * 43758.5453);
float3 o = 0;
float2 vel = float2(0, 1);
if (Mode < 0.5) {                                          // orbit
    float t = T * Speed * (0.7 + 0.6 * R) + R * 6.2831;
    float r = Radius * (0.6 + 0.4 * R);
    o = float3(cos(t) * r, sin(t) * r, sin(t * 1.7 + R * 20.0) * Height);
    vel = float2(-sin(t), cos(t));
} else if (Mode < 1.5) {                                   // drift
    float a = T * Speed;
    o = float3(sin(a * 0.31 + R * 17.0) + 0.5 * sin(a * 0.83 + R * 5.0),
               sin(a * 0.27 + R * 29.0) + 0.5 * sin(a * 0.71 + R * 3.0), 0) * Radius;
    o.z = sin(a * 0.19 + R * 41.0) * Height;
    vel = float2(cos(a * 0.31 + R * 17.0), cos(a * 0.27 + R * 29.0));
} else {                                                   // flock
    float a = T * Speed + R * 0.9;
    o = float3(cos(a) * Radius, sin(a) * Radius, sin(T * 0.3 + R * 7.0) * Height);
    vel = float2(-sin(a), cos(a));
}
vel = normalize(vel + 1e-4);
float ang = atan2(-vel.x, vel.y);                          // turn so the head (+y) leads
float2 Lr = float2(L.x * cos(ang) - L.y * sin(ang), L.x * sin(ang) + L.y * cos(ang));
float side = abs(L.x);
float flap = max(0.0, side - Body) * sin(T * Flap + R * 30.0) * 0.9;
return o + float3(Lr - L.xy, flap);
"""

BLINK_HLSL = """
float R = frac(sin(dot(OPos.xy, float2(12.9898, 78.233)) + OPos.z * 0.123) * 43758.5453);
return pow(saturate(sin(T * Speed * 1.3 + R * 40.0) * 0.5 + 0.5), 6.0);
"""

# kind: color comes from Maya; motion and look per kind
KIND = {
    "moth":    dict(Mode=0, Speed=2.4, Radius=45, Height=18, Flap=45, Body=0.7, Glow=0, Bounds=60),
    "firefly": dict(Mode=1, Speed=0.6, Radius=70, Height=35, Flap=0, Body=9, Glow=90, Bounds=60),
    "gnat":    dict(Mode=1, Speed=1.6, Radius=28, Height=22, Flap=0, Body=9, Glow=0, Bounds=40),
    "bat":     dict(Mode=0, Speed=0.9, Radius=420, Height=60, Flap=26, Body=2.5, Glow=0, Bounds=300),
    "flock":   dict(Mode=2, Speed=0.07, Radius=1300, Height=120, Flap=5, Body=3, Glow=0, Bounds=900),
}


def _custom_nodes(m):
    return [e for e in unreal.ObjectIterator(unreal.MaterialExpressionCustom) if e.get_outer() == m]


def _expr(m, cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e


def critter_material():
    """M_PS2_Critter: a duplicate of M_PS2_Surface (which keeps its hand-connected World
    Position Offset wire on the custom node), with that node's code swapped for MOVE_HLSL and
    new inputs wired in, plus a blinking Emissive. Rebuilt from M_PS2_Surface every run."""
    if lib.does_asset_exist(CRITTER):
        unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(unreal.load_asset(CRITTER))
        lib.delete_asset(CRITTER)
    m = lib.duplicate_asset(SURFACE, CRITTER)
    wob = [c for c in _custom_nodes(m) if "Amount" in [str(i.get_editor_property("input_name")) for i in c.get_editor_property("inputs")]][0]
    pins = list(wob.get_editor_property("inputs"))
    for n in ("T", "OPos", "WPos", "Mode", "Speed", "Radius", "Height", "Flap", "Body"):
        p = unreal.CustomInput()
        p.set_editor_property("input_name", n)
        pins.append(p)
    wob.set_editor_property("inputs", pins)
    wob.set_editor_property("code", MOVE_HLSL)
    t = _expr(m, unreal.MaterialExpressionTime, -1100, 200)
    opos = _expr(m, unreal.MaterialExpressionObjectPositionWS, -1100, 300)
    wpos = _expr(m, unreal.MaterialExpressionWorldPosition, -1100, 400,
                 world_position_shader_offset=unreal.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    MEL.connect_material_expressions(t, "", wob, "T")
    MEL.connect_material_expressions(opos, "", wob, "OPos")
    MEL.connect_material_expressions(wpos, "", wob, "WPos")
    params = {}
    for i, n in enumerate(("Mode", "Speed", "Radius", "Height", "Flap", "Body", "Glow")):
        params[n] = _expr(m, unreal.MaterialExpressionScalarParameter, -1100, 520 + i * 80, parameter_name=n, default_value=0.0)
        if n != "Glow":
            MEL.connect_material_expressions(params[n], "", wob, n)
    # fireflies: Color * Glow * blink -> Emissive
    blink = _expr(m, unreal.MaterialExpressionCustom, -700, -500, code=BLINK_HLSL,
                  output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    bp = []
    for n in ("T", "OPos", "Speed"):
        p = unreal.CustomInput()
        p.set_editor_property("input_name", n)
        bp.append(p)
    blink.set_editor_property("inputs", bp)
    MEL.connect_material_expressions(t, "", blink, "T")
    MEL.connect_material_expressions(opos, "", blink, "OPos")
    MEL.connect_material_expressions(params["Speed"], "", blink, "Speed")
    color = [e for e in unreal.ObjectIterator(unreal.MaterialExpressionVectorParameter)
             if e.get_outer() == m and str(e.get_editor_property("parameter_name")) == "Color"][0]
    a = _expr(m, unreal.MaterialExpressionMultiply, -450, -450)
    MEL.connect_material_expressions(color, "", a, "A")
    MEL.connect_material_expressions(params["Glow"], "", a, "B")
    b = _expr(m, unreal.MaterialExpressionMultiply, -300, -450)
    MEL.connect_material_expressions(a, "", b, "A")
    MEL.connect_material_expressions(blink, "", b, "B")
    MEL.connect_material_property(b, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    m.set_editor_property("two_sided", True)                      # thin wings seen from both sides
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


def import_mesh(kind, fbx):
    t = unreal.AssetImportTask()
    t.filename, t.destination_path, t.destination_name = fbx, DIR, f"SM_Critter_{kind}"
    t.automated, t.replace_existing, t.save = True, True, True
    tools.import_asset_tasks([t])
    mesh = unreal.load_asset(f"{DIR}/SM_Critter_{kind}")
    nanite = mesh.get_editor_property("nanite_settings")
    nanite.set_editor_property("enabled", False)
    mesh.set_editor_property("nanite_settings", nanite)
    lib.save_loaded_asset(mesh, False)
    return mesh


def instance(kind, mat, rgb):
    path = f"{DIR}/MI_Critter_{kind}"
    mi = unreal.load_asset(path) if lib.does_asset_exist(path) else \
        tools.create_asset(f"MI_Critter_{kind}", DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", mat)
    MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*rgb, 1))
    for k, v in KIND[kind].items():
        if k != "Bounds":
            MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
    lib.save_loaded_asset(mi, False)
    return mi


def place(kind, mesh, mi, at, yaw=0.0):
    a = actors.spawn_actor_from_object(mesh, unreal.Vector(*at), unreal.Rotator(0, 0, yaw))
    a.set_actor_label(f"{kind}_{len(PLACED.setdefault(kind, []))}")
    a.set_folder_path(f"Critters/{kind}")
    a.tags = [TAG]
    c = a.static_mesh_component
    c.set_material(0, mi)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property("cast_shadow", False)
    c.set_editor_property("bounds_scale", float(KIND[kind]["Bounds"]))   # it wanders far from where it stands
    PLACED[kind].append(a)


PLACED = {}


def main():
    data = json.load(open(f"{ROOT}/export/critters.json"))
    layout = json.load(open(f"{ROOT}/layout.json"))
    lights = {l["name"]: l["position"] for l in json.load(open(f"{ROOT}/export/sets.json"))["lights"]}
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG):
            actors.destroy_actor(a)
    lib.make_directory(DIR)
    mat = critter_material()
    assets = {}
    for kind, spec in data["critters"].items():
        assets[kind] = (import_mesh(kind, spec["fbx"]), instance(kind, mat, data["materials"][spec["material"]]))
    rng = random.Random(13)
    # moths around the outside lights
    for name in ("light_lot", "light_street", "light_open", "light_ice", "light_cross", "light_car_tail"):
        if name in lights:
            x, y, z = lights[name]
            for _ in range(7 if name in ("light_lot", "light_street") else 4):
                place("moth", *assets["moth"], (x + rng.uniform(-25, 25), y + rng.uniform(-25, 25), z + rng.uniform(-30, 10)))
    # fireflies along the trail and the lake shore
    trail = layout["trail"]
    for _ in range(140):
        i = rng.randrange(len(trail) - 1)
        t = rng.random()
        px = trail[i][0] + (trail[i + 1][0] - trail[i][0]) * t + rng.uniform(-700, 700)
        py = trail[i][1] + (trail[i + 1][1] - trail[i][1]) * t + rng.uniform(-700, 700)
        if py > -900:                                             # not in the motel lot
            place("firefly", *assets["firefly"], (px, py, rng.uniform(40, 170)))
    for _ in range(60):
        place("firefly", *assets["firefly"], (rng.uniform(-7000, 8000), rng.uniform(14000, 14600), rng.uniform(30, 140)))
    # gnat clouds: along the trail, at the motel walkway, at the dock
    clouds = [(-3000, -1200), (-2950, 300), (-1600, 1500), (800, 3400), (1800, 8600), (1500, 14200), (-1200, -1550), (300, -1600)]
    for cx, cy in clouds:
        for _ in range(22):
            place("gnat", *assets["gnat"], (cx + rng.uniform(-90, 90), cy + rng.uniform(-90, 90), rng.uniform(90, 190)))
    # bats: around the lot lamp and the streetlight, and over the lake by the dock
    for (cx, cy, cz, n) in ((*lights.get("light_lot", (-3685, -2470, 690))[:2], 640, 3),
                            (*lights.get("light_street", (1630, -3500, 600))[:2], 560, 2), (1500, 14900, 650, 5)):
        for _ in range(n):
            place("bat", *assets["bat"], (cx + rng.uniform(-60, 60), cy + rng.uniform(-60, 60), cz + rng.uniform(-40, 40)))
    # the flock: one circle over the dock end of the lake
    for _ in range(12):
        place("flock", *assets["flock"], (1500 + rng.uniform(-250, 250), 15600 + rng.uniform(-250, 250), 1300 + rng.uniform(-80, 80)))
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print("critters placed:", {k: len(v) for k, v in PLACED.items()})


main()

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
if (Mode > 8.5) return float3(0, 0, 0);                    // still (the owl's dead tree)
if (Mode > 6.5 && Mode < 7.5) {                            // bugs around you: a field that wraps round the player
    float a = T * Speed;
    float3 drift = float3(sin(a * 0.31 + R * 17.0) + 0.5 * sin(a * 0.83 + R * 5.0),
                          sin(a * 0.27 + R * 29.0) + 0.5 * sin(a * 0.71 + R * 3.0),
                          sin(a * 0.19 + R * 41.0)) * 45.0;
    float3 rel = OPos + drift - PPos;
    rel.xy = (frac(rel.xy / (2.0 * Radius) + 0.5) - 0.5) * 2.0 * Radius;
    rel.z = (frac((rel.z - 40.0) / (2.0 * Height) + 0.5) - 0.5) * 2.0 * Height + 40.0;
    float flapn = max(0.0, abs(L.x) - Body) * sin(T * Flap + R * 30.0) * 0.9;
    float3 W = PPos + rel;                                 // where this bug is in the world
    float inRooms = step(-2500.0, W.x) * step(W.x, 500.0) * step(-1400.0, W.y) * step(W.y, -700.0);
    float inOffice = step(3050.0, W.x) * step(W.x, 3750.0) * step(-1750.0, W.y) * step(W.y, -850.0);
    float gone = saturate(inRooms + inOffice) * step(W.z, 340.0);   // none inside the motel rooms / office
    return PPos + rel - OPos + float3(0, 0, flapn) - L * gone;
}
if (Mode > 5.5) {                                          // a cat sitting far off, watching you
    float2 toP = PPos.xy - OPos.xy;
    float d = length(toP);
    float seen = step(Radius, d) * step(d, Height) * step(frac(T / 70.0 + R), 0.55);   // only now and then, only far off
    float a = atan2(-toP.x, toP.y);                        // always faces you
    float2 Lr = float2(L.x * cos(a) - L.y * sin(a), L.x * sin(a) + L.y * cos(a));
    return float3(Lr - L.xy, 0) - L * (1.0 - seen);       // not there: shrunk to nothing
}
if (Mode > 4.5) {                                          // the black cat walking round the motel
    // slow, elegant and a little uncanny: long unhurried strides in a cat's walking order,
    // feet planted (steps follow the distance walked, so the paws never slide), the body
    // gently bobbing and swaying, the tail waving slowly from base to tip, and the head
    // turning to keep watching you as it goes. Every 22 s it stops for 10 s to sit and stare.
    float cyc = 32.0, walk = 22.0;
    float k = floor(T / cyc), f = T - k * cyc;
    float sitting = step(walk, f);
    float ease = smoothstep(walk - 1.5, walk, f) * (1 - smoothstep(cyc - 1.5, cyc, f));   // settles / rises
    float dist = (k * walk + min(f, walk)) * Speed;
    float hx = Radius, hy = Height, per = 4.0 * (hx + hy);
    float s = fmod(dist, per);
    float2 p, dir;                                         // a rectangle round the building
    if (s < 2 * hx)               { p = float2(-hx + s, -hy); dir = float2(1, 0); }
    else if (s < 2 * hx + 2 * hy) { p = float2(hx, -hy + (s - 2 * hx)); dir = float2(0, 1); }
    else if (s < 4 * hx + 2 * hy) { p = float2(hx - (s - 2 * hx - 2 * hy), hy); dir = float2(-1, 0); }
    else                          { p = float2(-hx, hy - (s - 4 * hx - 2 * hy)); dir = float2(0, -1); }
    float2 toCat = OPos.xy + p - PPos.xy;
    float d = length(toCat);
    float2 away = toCat / max(d, 1.0);
    float push = saturate((400.0 - d) / 250.0);            // you come close: it slinks away
    p += away * push * 260.0;
    float2 face = lerp(dir, -away, ease * (1 - push));     // sitting: turned to stare at you
    face = normalize(lerp(face, away, push) + 1e-4);
    float a = atan2(-face.x, face.y);
    float moving = saturate((1 - ease) + push);
    // shape thresholds below are in the model's own size (Fab cat); Body = how much it's scaled
    float3 l = L / max(Body, 0.01);
    float3 U = l;
    // legs: everything below 20 cm swings from the hip and lifts on the way forward
    float leg = saturate((20.0 - U.z) / 20.0);
    float ph = dist * 6.2832 / 34.0 + push * T * 9.0;      // one full stride per 34 cm
    float off = (U.y > 0 ? 1.5708 : 0.0) + (U.x > 0 ? 3.1416 : 0.0);   // left hind, left fore, right hind, right fore
    l.y += sin(ph + off) * leg * 6.5 * moving;
    l.z += max(0.0, cos(ph + off)) * leg * 2.2 * moving;
    // body: a soft bob twice per stride and a slight sway
    l.z += sin(ph * 2.0) * 0.45 * moving * (1 - leg);
    l.x += sin(ph) * 0.6 * moving * (1 - leg);
    // tail: a slow wave travelling out to the tip
    if (U.y < -31.0) {
        float t = saturate((-U.y - 31.0) / 22.0);
        l.x += sin(T * 1.1 - t * 2.6) * t * 7.0;
        l.z += sin(T * 0.7 - t * 2.0) * t * 2.5;
    }
    // sitting: hips down, front stays up
    l.z -= ease * (1 - push) * saturate(-U.y / 25.0) * 10.0;
    // head: turns (smoothly, up to ~70 degrees) to watch you while you're within 20 m
    if (U.y > 20.0 && U.z > 40.0) {
        float2 toP = PPos.xy - (OPos.xy + p);
        float rel = atan2(-toP.x, toP.y) - a;
        rel = atan2(sin(rel), cos(rel));
        float h = clamp(rel, -1.2, 1.2) * saturate((2000.0 - length(toP)) / 500.0);
        float2 q = l.xy - float2(13.0, 20.0);
        l.xy = float2(13.0, 20.0) + float2(q.x * cos(h) - q.y * sin(h), q.x * sin(h) + q.y * cos(h));
    }
    float2 lr = float2(l.x * cos(a) - l.y * sin(a), l.x * sin(a) + l.y * cos(a));
    float gone = saturate((d - 150.0) / 100.0);            // right next to you: it's gone
    return float3(p, 0) + float3(lr, l.z) * Body * gone - L;
}
if (Mode > 3.5) {                                          // owl: the head turns to watch you
    float2 toP = PPos.xy - OPos.xy;
    float a = clamp(atan2(-toP.x, toP.y), -2.9, 2.9);
    a = round(a / 0.35) * 0.35;                            // in little jerks, like an owl
    if (L.z < Height) return float3(0, 0, 0);
    float2 hr = float2(L.x * cos(a) - L.y * sin(a), L.x * sin(a) + L.y * cos(a));
    return float3(hr - L.xy, 0);
}
if (Mode > 2.5) {                                          // perched crow: flies off as you come near
    float2 away = OPos.xy - PPos.xy;
    float d = length(away);
    float scare = saturate((Radius - d) / (Radius * 0.6));
    float s2 = scare * scare;
    float2 dir = away / max(d, 1.0);
    float3 off = float3(dir * s2 * Height * 2.0, s2 * Height + sin(T * 3.0 + R * 20.0) * 0.25 * (1 - scare));
    float flapw = max(0.0, abs(L.x) - Body) * sin(T * Flap + R * 30.0) * 2.2 * saturate(scare * 6.0);
    float keep = 1.0 - saturate((scare - 0.85) / 0.15);   // gone once it's high up
    return off + float3(0, 0, flapw) + L * (keep - 1.0);
}
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
    float dp = length(OPos.xy + o.xy - PPos.xy);            // you walk under it: it climbs away
    o.z += pow(saturate((1100.0 - dp) / 600.0), 1.5) * 900.0;
}
vel = normalize(vel + 1e-4);
float ang = atan2(-vel.x, vel.y);                          // turn so the head (+y) leads
float2 Lr = float2(L.x * cos(ang) - L.y * sin(ang), L.x * sin(ang) + L.y * cos(ang));
float side = abs(L.x);
float flap = max(0.0, side - Body) * sin(T * Flap + R * 30.0) * 0.9;
return o + float3(Lr - L.xy, flap);
"""

BLINK_HLSL = """
// Steady 2 = eyeshine: lights up only when you look (and shine the flashlight) straight at it
if (S > 1.5) return pow(saturate(dot(-Parameters.CameraVector, ResolvedView.ViewForward)), 80.0);
float R = frac(sin(dot(OPos.xy, float2(12.9898, 78.233)) + OPos.z * 0.123) * 43758.5453);
return pow(saturate(sin(T * Speed * 1.3 + R * 40.0) * 0.5 + 0.5), 6.0);
"""

# kind: color comes from Maya; motion and look per kind
KIND = {
    "moth":    dict(Mode=0, Speed=2.4, Radius=45, Height=18, Flap=45, Body=0.35, Glow=0, Bounds=120, Size=0.5),
    "firefly": dict(Mode=1, Speed=0.6, Radius=70, Height=35, Flap=0, Body=9, Glow=0, Bounds=120, Size=0.5),
    "firefly_lit": dict(Mode=1, Speed=0.6, Radius=70, Height=35, Flap=0, Body=9, Glow=4, Bounds=120, Size=0.5),   # 1 in 8, a faint glow
    "gnat":    dict(Mode=1, Speed=1.6, Radius=28, Height=22, Flap=0, Body=9, Glow=0, Bounds=80, Size=0.6),
    "bat":     dict(Mode=0, Speed=0.9, Radius=420, Height=60, Flap=26, Body=2.5, Glow=0, Bounds=300),
    "flock":   dict(Mode=2, Speed=0.07, Radius=1300, Height=120, Flap=5, Body=3, Glow=0, Bounds=900),
    "crow":    dict(Mode=3, Speed=1, Radius=1200, Height=700, Flap=24, Body=3.4, Glow=0, Bounds=400),
    # more birds: flocks of different sizes and heights, and single crows gliding low
    "flock2":  dict(Mode=2, Speed=0.11, Radius=800, Height=90, Flap=6, Body=3, Glow=0, Bounds=600),
    "glider":  dict(Mode=2, Speed=0.16, Radius=1500, Height=150, Flap=4, Body=3, Glow=0, Bounds=1000),
    # bugs around the screen: specks and a few moths in a field that always surrounds you
    "speck":   dict(Mode=7, Speed=0.5, Radius=350, Height=120, Flap=0, Body=9, Glow=0, Bounds=900000, Size=1.0),
    "nearmoth": dict(Mode=7, Speed=0.9, Radius=450, Height=110, Flap=45, Body=0.35, Glow=0, Bounds=24000, Size=0.5),
    "owl":     dict(Mode=4, Speed=1, Radius=0, Height=25, Flap=0, Body=0, Glow=0, Bounds=3),
    "snag":    dict(Mode=9, Speed=0, Radius=0, Height=0, Flap=0, Body=0, Glow=0, Bounds=1),
    # cat: Speed cm/s, Radius / Height = half size of the rectangle it walks round the motel
    "cat":     dict(Mode=5, Speed=30, Radius=1700, Height=625, Flap=0, Body=0.75, Glow=0, Bounds=120),
    # watching cat: seen only between Radius and Height cm away (and only some of the time)
    "catsit":  dict(Mode=6, Speed=0, Radius=1100, Height=4500, Flap=0, Body=0, Glow=0, Bounds=3),
    "cateyes": dict(Mode=9, Speed=0, Radius=0, Height=0, Flap=0, Body=0, Glow=0, Bounds=1),
}
SLOT = {    # per-part changes on top of the kind's settings
    "critter_owl_eye_mat": dict(Glow=5, Steady=1),
    "critter_cat_eye_mat": dict(Glow=150, Steady=2),        # eyeshine when you look right at it
    "critter_catsit_eye_mat": dict(Glow=150, Steady=2),
    "critter_cateyes_mat": dict(Glow=150, Steady=2),
}
TEXTURE = {"critter_snag_mat": ("T_bark", 150)}


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
    # Unreal won't delete a material its instances still use, so it's built fresh under whichever
    # of two names is free; finish_material() moves every critter instance onto it and removes the other
    for name in (CRITTER, CRITTER + "_b"):
        if lib.does_asset_exist(name):
            unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(unreal.load_asset(name))
            lib.delete_asset(name)
    free = next(n for n in (CRITTER, CRITTER + "_b") if not lib.does_asset_exist(n))
    m = lib.duplicate_asset(SURFACE, free)
    wob = [c for c in _custom_nodes(m) if "Amount" in [str(i.get_editor_property("input_name")) for i in c.get_editor_property("inputs")]][0]
    pins = list(wob.get_editor_property("inputs"))
    for n in ("T", "OPos", "WPos", "Mode", "Speed", "Radius", "Height", "Flap", "Body", "PPos"):
        p = unreal.CustomInput()
        p.set_editor_property("input_name", n)
        pins.append(p)
    wob.set_editor_property("inputs", pins)
    wob.set_editor_property("code", MOVE_HLSL)
    t = _expr(m, unreal.MaterialExpressionTime, -1100, 200)
    # the critter's pivot in the world (local 0,0,0 -> world). Not ObjectPositionWS: that's the centre
    # of the mesh's bounds, different for every mesh (the Fab cat's eyes drifted off its head)
    zero = _expr(m, unreal.MaterialExpressionConstant3Vector, -1300, 300, constant=unreal.LinearColor(0, 0, 0, 0))
    opos = _expr(m, unreal.MaterialExpressionTransformPosition, -1100, 300,
                 transform_source_type=unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL,
                 transform_type=unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD)
    MEL.connect_material_expressions(zero, "", opos, "")
    wpos = _expr(m, unreal.MaterialExpressionWorldPosition, -1100, 400,
                 world_position_shader_offset=unreal.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    MEL.connect_material_expressions(t, "", wob, "T")
    MEL.connect_material_expressions(opos, "", wob, "OPos")
    MEL.connect_material_expressions(wpos, "", wob, "WPos")
    ppos = _expr(m, unreal.MaterialExpressionCollectionParameter, -1100, 470,
                 collection=unreal.load_asset("/Game/Horror/Materials/MPC_Horror"), parameter_name="PlayerPos")
    MEL.connect_material_expressions(ppos, "", wob, "PPos")
    params = {}
    for i, n in enumerate(("Mode", "Speed", "Radius", "Height", "Flap", "Body", "Glow", "Steady")):
        params[n] = _expr(m, unreal.MaterialExpressionScalarParameter, -1100, 520 + i * 80, parameter_name=n, default_value=0.0)
        if n not in ("Glow", "Steady"):
            MEL.connect_material_expressions(params[n], "", wob, n)
    # fireflies: Color * Glow * blink -> Emissive
    blink = _expr(m, unreal.MaterialExpressionCustom, -700, -500, code=BLINK_HLSL,
                  output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    bp = []
    for n in ("T", "OPos", "Speed", "S"):
        p = unreal.CustomInput()
        p.set_editor_property("input_name", n)
        bp.append(p)
    blink.set_editor_property("inputs", bp)
    MEL.connect_material_expressions(t, "", blink, "T")
    MEL.connect_material_expressions(opos, "", blink, "OPos")
    MEL.connect_material_expressions(params["Speed"], "", blink, "Speed")
    MEL.connect_material_expressions(params["Steady"], "", blink, "S")
    color = [e for e in unreal.ObjectIterator(unreal.MaterialExpressionVectorParameter)
             if e.get_outer() == m and str(e.get_editor_property("parameter_name")) == "Color"][0]
    a = _expr(m, unreal.MaterialExpressionMultiply, -450, -450)
    MEL.connect_material_expressions(color, "", a, "A")
    MEL.connect_material_expressions(params["Glow"], "", a, "B")
    steady = _expr(m, unreal.MaterialExpressionLinearInterpolate, -450, -350)    # Steady 1 = no blinking
    MEL.connect_material_expressions(blink, "", steady, "A")
    one = _expr(m, unreal.MaterialExpressionConstant, -600, -330, r=1.0)
    MEL.connect_material_expressions(one, "", steady, "B")
    sub = _expr(m, unreal.MaterialExpressionCustom, -750, -280, code="return saturate(1.0 - abs(S - 1.0));",   # Steady 2 -> 0
                output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    sp = unreal.CustomInput()
    sp.set_editor_property("input_name", "S")
    sub.set_editor_property("inputs", [sp])
    MEL.connect_material_expressions(params["Steady"], "", sub, "S")
    MEL.connect_material_expressions(sub, "", steady, "Alpha")
    b = _expr(m, unreal.MaterialExpressionMultiply, -300, -450)
    MEL.connect_material_expressions(a, "", b, "A")
    MEL.connect_material_expressions(steady, "", b, "B")
    MEL.connect_material_property(b, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    # UVMode 1: use the mesh's own UVs for Tex (and a normal map), for bought models like the
    # Fab cat; 0 (default): the world projection every PS2 surface uses
    tex = [e for e in unreal.ObjectIterator(unreal.MaterialExpressionTextureObjectParameter)
           if e.get_outer() == m and str(e.get_editor_property("parameter_name")) == "Tex"][0]
    proj = [e for e in unreal.ObjectIterator(unreal.MaterialExpressionMaterialFunctionCall) if e.get_outer() == m][0]
    basemul = MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_BASE_COLOR)
    uvs = _expr(m, unreal.MaterialExpressionTextureSample, -800, -650)
    assert MEL.connect_material_expressions(tex, "", uvs, "Tex"), "texture sample: Tex pin"
    uvmode = _expr(m, unreal.MaterialExpressionScalarParameter, -800, -750, parameter_name="UVMode", default_value=0.0)
    pick = _expr(m, unreal.MaterialExpressionLinearInterpolate, -550, -600)
    MEL.connect_material_expressions(proj, "XYZ Texture", pick, "A")
    MEL.connect_material_expressions(uvs, "RGB", pick, "B")
    MEL.connect_material_expressions(uvmode, "", pick, "Alpha")
    MEL.connect_material_expressions(pick, "", basemul, "A")
    nrm = _expr(m, unreal.MaterialExpressionTextureSampleParameter2D, -800, -900, parameter_name="NormalTex",
                texture=unreal.load_asset("/Engine/EngineMaterials/FlatNormal"),
                sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    MEL.connect_material_property(nrm, "RGB", unreal.MaterialProperty.MP_NORMAL)
    m.set_editor_property("two_sided", True)                      # thin wings seen from both sides
    m.set_editor_property("used_with_skeletal_mesh", True)        # the rigged cat uses it too
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return finish_material(m)


def finish_material(m):
    mine = m.get_path_name().split(".")[0]
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in reg.get_assets_by_path(DIR, recursive=False):
        o = a.get_asset()
        if isinstance(o, unreal.MaterialInstanceConstant):
            o.set_editor_property("parent", m)
            lib.save_loaded_asset(o, False)
    for name in (CRITTER, CRITTER + "_b", CRITTER + "_build"):
        if name != mine and lib.does_asset_exist(name):
            lib.delete_asset(name)                       # nothing uses it now
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


def instance(kind, slot, mat, rgb):
    """MI_Critter_<kind>_<slot>: the kind's motion settings, the slot's color (and SLOT extras)."""
    name = "MI_Critter_%s_%s" % (kind, slot.replace("critter_", "").replace("_mat", ""))
    path = f"{DIR}/{name}"
    mi = unreal.load_asset(path) if lib.does_asset_exist(path) else \
        tools.create_asset(name, DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", mat)
    MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*rgb, 1))
    for k, v in dict(KIND[kind], **SLOT.get(slot, {})).items():
        if k not in ("Bounds", "Size"):
            MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
    if slot in TEXTURE and lib.does_asset_exist(f"/Game/Horror/Textures/{TEXTURE[slot][0]}"):
        MEL.set_material_instance_texture_parameter_value(mi, "Tex", unreal.load_asset(f"/Game/Horror/Textures/{TEXTURE[slot][0]}"))
        MEL.set_material_instance_scalar_parameter_value(mi, "TexSize", float(TEXTURE[slot][1]))
    lib.save_loaded_asset(mi, False)
    return mi


CAT_SCALE = 0.75          # the Fab cat is modelled bigger than a real cat


def fab_cat(mat):
    """The black cat the user added from Fab (Content/Fab/Black_Cat...): its mesh, and two
    M_PS2_Critter instances (walking / watching) that use its own textures through its UVs."""
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    found = [a for a in reg.get_assets_by_path("/Game/Fab", recursive=True)]
    mesh = next((a.get_asset() for a in found if str(a.asset_class_path.asset_name) == "StaticMesh" and "cat" in str(a.asset_name).lower()), None)
    if not mesh:
        print("no Fab cat found")
        return None
    tex = {str(a.asset_name): a.get_asset() for a in found if str(a.asset_class_path.asset_name) == "Texture2D"}
    nanite = mesh.get_editor_property("nanite_settings")
    nanite.set_editor_property("enabled", False)
    mesh.set_editor_property("nanite_settings", nanite)
    lib.save_loaded_asset(mesh, False)
    mis = {}
    for kind in ("cat", "catsit"):
        mi = instance(kind, "critter_fabcat_mat", mat, (1.0, 1.0, 1.0))
        base = next((t for n, t in tex.items() if "base" in n.lower()), None)
        normal = next((t for n, t in tex.items() if "normal" in n.lower()), None)
        if base:
            MEL.set_material_instance_texture_parameter_value(mi, "Tex", base)
        if normal:
            MEL.set_material_instance_texture_parameter_value(mi, "NormalTex", normal)
        MEL.set_material_instance_scalar_parameter_value(mi, "UVMode", 1.0)
        lib.save_loaded_asset(mi, False)
        mis[kind] = mi
    return mesh, mis


def place(kind, mesh, mis, at, yaw=0.0, scale=None):
    a = actors.spawn_actor_from_object(mesh, unreal.Vector(*at), unreal.Rotator(0, 0, yaw))
    scale = KIND[kind].get("Size", 1.0) if scale is None else scale     # bugs are drawn smaller
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.set_actor_label(f"{kind}_{len(PLACED.setdefault(kind, []))}")
    a.set_folder_path(f"Critters/{kind}")
    a.tags = [TAG]
    c = a.static_mesh_component
    for i, mi in enumerate(mis):
        c.set_material(i, mi)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property("cast_shadow", False)
    c.set_editor_property("bounds_scale", float(KIND[kind]["Bounds"]))   # it wanders far from where it stands
    if kind in BUGS:                     # lighting channel 2 only: the flashlight (channels 0 and 1)
        c.set_editor_property("lighting_channels", BUG_LIGHT)   # doesn't light them, so they never shine in the beam
    PLACED[kind].append(a)


PLACED = {}
BUGS = ("moth", "firefly", "firefly_lit", "gnat", "speck", "nearmoth")
BUG_LIGHT = unreal.LightingChannels()
BUG_LIGHT.set_editor_property("channel0", False)
BUG_LIGHT.set_editor_property("channel2", True)


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
        mesh = import_mesh(kind, spec["fbx"])
        mis = [instance(kind, str(sl.material_slot_name), mat,
                        data["materials"].get(str(sl.material_slot_name), (0.2, 0.2, 0.2))) for sl in mesh.static_materials]
        assets[kind] = (mesh, mis)
    rng = random.Random(13)

    def mis_for_kind(kind, base, rgb):
        return [instance(kind, str(sl.material_slot_name), mat, rgb) for sl in assets[base][0].static_materials]
    # moths around the outside lights
    for name in ("light_lot", "light_street", "light_open", "light_ice", "light_cross", "light_car_tail"):
        if name in lights:
            x, y, z = lights[name]
            for _ in range(rng.choice((2, 2, 3))):                # just two or three at each light
                place("moth", *assets["moth"], (x + rng.uniform(-25, 25), y + rng.uniform(-25, 25), z + rng.uniform(-30, 10)))
    # fireflies along the trail and the lake shore: only about one in eight glows, and faintly
    lit = mis_for_kind("firefly_lit", "firefly", (0.75, 0.85, 0.3))
    firefly = lambda: (("firefly_lit", assets["firefly"][0], lit) if rng.random() < 0.125 else ("firefly", *assets["firefly"]))
    trail = layout["trail"]
    for _ in range(140):
        i = rng.randrange(len(trail) - 1)
        t = rng.random()
        px = trail[i][0] + (trail[i + 1][0] - trail[i][0]) * t + rng.uniform(-700, 700)
        py = trail[i][1] + (trail[i + 1][1] - trail[i][1]) * t + rng.uniform(-700, 700)
        if py > -900:                                             # not in the motel lot
            place(*firefly(), (px, py, rng.uniform(40, 170)))
    for _ in range(60):
        place(*firefly(), (rng.uniform(-7000, 8000), rng.uniform(14000, 14600), rng.uniform(30, 140)))
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
    # flocks circling in the sky: over the lake, the woods, the motel and the road
    def mis_for(kind, base):
        return [instance(kind, str(sl.material_slot_name), mat, data["materials"].get(str(sl.material_slot_name), (0.2, 0.2, 0.2)))
                for sl in assets[base][0].static_materials]
    flock2, glider = mis_for("flock2", "flock"), mis_for("glider", "flock")
    for kind, mis, (cx, cy, cz, n) in (("flock", assets["flock"][1], (1500, 15600, 1300, 14)),
                                       ("flock", assets["flock"][1], (-4000, 9000, 1600, 12)),
                                       ("flock2", flock2, (3500, 5500, 1100, 10)),
                                       ("flock2", flock2, (-1000, -1200, 1500, 9)),
                                       ("flock2", flock2, (-6000, -4300, 1200, 8)),
                                       ("flock", assets["flock"][1], (6000, 12500, 1900, 16))):
        for _ in range(n):
            place(kind, assets["flock"][0], mis, (cx + rng.uniform(-260, 260), cy + rng.uniform(-260, 260), cz + rng.uniform(-90, 90)))
    for (cx, cy, cz) in ((-1500, -2600, 700), (1500, 2500, 800), (-500, 8000, 750), (2000, 13000, 650)):
        for _ in range(2):                                        # single crows gliding low, wide circles
            place("glider", assets["flock"][0], glider, (cx + rng.uniform(-400, 400), cy + rng.uniform(-400, 400), cz + rng.uniform(-60, 60)))
    # bugs around the screen: they float around you wherever you go (mostly seen in the flashlight)
    speck = mis_for("speck", "gnat")
    nearmoth = mis_for("nearmoth", "moth")
    for _ in range(45):
        place("speck", assets["gnat"][0], speck, (rng.uniform(-350, 350), rng.uniform(-350, 350), rng.uniform(0, 240)))
    for _ in range(4):
        place("nearmoth", assets["moth"][0], nearmoth, (rng.uniform(-450, 450), rng.uniform(-450, 450), rng.uniform(20, 240)))
    # crows: on the lot lamps, the streetlight, the payphone, the dumpster, the motel roof, the fence.
    # They lift off and fly away as you come within ~9 m, and drift back once you've gone.
    perches = [(-3685, -2470, 740.5), (-3500, -2500, 721), (-335, -3620, 740.5), (-150, -3650, 721), (1600, -3500, 655.5),
               (2930, -1830, 192), (3925, -1150, 130.5), (3995, -1120, 130.5), (-2300, -1692, 337.5), (-1880, -1692, 337.5),
               (-420, -1692, 337.5), (180, -1692, 337.5), (-1500, -100, 160.5), (1200, -100, 160.5), (1260, -100, 160.5)]
    # and on the ground along the trail and at the clearings, pecking about
    trail = layout["trail"]
    for i in range(len(trail) - 1):
        for _ in range(2):
            t = rng.random()
            perches.append((trail[i][0] + (trail[i + 1][0] - trail[i][0]) * t + rng.uniform(-300, 300),
                            trail[i][1] + (trail[i + 1][1] - trail[i][1]) * t + rng.uniform(-300, 300), 1.0))
    for c in layout["clearings"][:4]:
        perches.append((c["x"] + rng.uniform(-150, 150), c["y"] + rng.uniform(-150, 150), 1.0))
    for (x, y, z) in perches:
        place("crow", *assets["crow"], (x, y, z), yaw=rng.uniform(0, 360))
    # the owl on a dead tree just off the trail (yaw 0: the head-turn assumes it faces +y)
    place("snag", *assets["snag"], (450, 4500, 0))
    place("owl", *assets["owl"], (450, 4500, 301))
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print("critters placed:", {k: len(v) for k, v in PLACED.items()})


main()

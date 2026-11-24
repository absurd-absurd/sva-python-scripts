"""MARROW Chapter 2: make the Lakebed map in the same Unreal project as Chapter 1.

Run in the Unreal editor after maya/make_lakebed.py (send it with RESEARCH_PROJECT_1/tools/ue_send.py).
Safe to run again: everything it placed before (tag "ch2") is removed first.

  1. Copies Chapter 1's PS2 post-process (MotelLake's PostProcess_Look) so both chapters look alike,
     then opens (or makes) /Game/Chapter2/Maps/Lakebed.
  2. Imports the set (lakebed, dock pilings, sunken lanterns, the surface from below, invisible
     walls) and its lights, with Chapter 1's material rules (unreal/import_sets.py), but into
     /Game/Chapter2 so Chapter 1's materials keep their colours.
  3. Places the scatter (rocks, boulders, weed, branches); you walk through the weed.
  4. The underwater look (see underwater_look() for the numbers).
Then run heavy_walk.py (the slow underwater movement, Lakebed map only).
"""
import json

import unreal

RP1 = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
RP2 = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_2"
MAP = "/Game/Chapter2/Maps/Lakebed"
CH2 = "/Game/Chapter2"
TAG2 = "ch2"

# Chapter 1's set importer: its functions (materials, import_set...), without running it
_src = open(f"{RP1}/unreal/import_sets.py", encoding="utf-8").read()
exec(_src[:_src.rindex("\nmain()")])
SETS_DIR = f"{CH2}/Sets"
MAT_DIR = f"{CH2}/Materials"
level_subsys = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


# ---------- 1. the map ----------

LOOK_JSON = f"{RP2}/export/ch1_look.json"


def _plain(v):
    """A post-process value as JSON, or None for anything holding object references."""
    if isinstance(v, (bool, int, float)):
        return v
    if isinstance(v, unreal.EnumBase):
        return {"enum": type(v).__name__, "value": v.name}
    if isinstance(v, unreal.LinearColor):
        return {"LinearColor": [v.r, v.g, v.b, v.a]}
    if isinstance(v, unreal.Vector4):
        return {"Vector4": [v.x, v.y, v.z, v.w]}
    return None


def _unplain(v):
    if isinstance(v, dict):
        if "enum" in v:
            return getattr(getattr(unreal, v["enum"]), v["value"])
        if "LinearColor" in v:
            return unreal.LinearColor(*v["LinearColor"])
        return unreal.Vector4(*v["Vector4"])
    return v


def chapter1_look():
    """MotelLake's PostProcess_Look (the PS2 screen effect, exposure) as plain values, saved to
    export/ch1_look.json the first time. Copying the settings struct itself from MotelLake into
    the Lakebed crashed Unreal when the map was saved (it holds references into the other world)."""
    import os
    if not os.path.exists(LOOK_JSON):
        level_subsys.load_level("/Game/Horror/Maps/MotelLake")
        ppv = [a for a in actors.get_all_level_actors() if a.get_actor_label() == "PostProcess_Look"][0]
        s = ppv.get_editor_property("settings")
        values = {}
        for name in dir(s):
            if name.startswith("override_") and s.get_editor_property(name):
                v = _plain(s.get_editor_property(name[len("override_"):]))
                if v is not None:
                    values[name[len("override_"):]] = v
        blend = [[w.weight, w.object.get_path_name()] for w in s.weighted_blendables.array if w.object]
        json.dump({"values": values, "blendables": blend}, open(LOOK_JSON, "w"), indent=1)
    return json.load(open(LOOK_JSON))


def look_settings(look):
    s = unreal.PostProcessSettings()
    for name, v in look["values"].items():
        s.set_editor_property("override_" + name, True)
        s.set_editor_property(name, _unplain(v))
    arr = []
    for weight, path in look["blendables"]:
        w = unreal.WeightedBlendable()
        w.weight = weight
        w.object = unreal.load_asset(path)
        arr.append(w)
    s.weighted_blendables = unreal.WeightedBlendables(arr)
    return s


def open_map():
    if lib.does_asset_exist(MAP):
        level_subsys.load_level(MAP)
    else:
        level_subsys.new_level(MAP)
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG2) or a.actor_has_tag(TAG):
            actors.destroy_actor(a)


def no_collision(comp):
    """Walk-through, in Play too: set_collision_enabled alone only lasted in the editor (in Play the
    silt specks and a milfoil plant blocked the start, so Cas never spawned). The profile is saved."""
    comp.set_collision_profile_name("NoCollision")
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)


def tagged(a, label, folder):
    a.set_actor_label(label)
    a.set_folder_path(folder)
    a.tags = [TAG2]
    return a


# ---------- 2. the set ----------

def import_ch2_textures():
    """RESEARCH_PROJECT_2/textures/*.jpg -> /Game/Horror/Textures/T_<name> (where materials() looks),
    shrunk to PS2 size like Chapter 1's (apply_textures.py)."""
    import glob, os
    tasks = []
    for f in sorted(glob.glob(f"{RP2}/textures/*.jpg")):
        t = unreal.AssetImportTask()
        t.filename = f
        t.destination_path = "/Game/Horror/Textures"
        t.destination_name = "T_" + os.path.basename(f)[:-4]
        t.automated = True
        t.replace_existing = True
        tasks.append(t)
    tools.import_asset_tasks(tasks)
    for t in tasks:
        tex = unreal.load_asset(f"/Game/Horror/Textures/{t.destination_name}")
        tex.set_editor_property("max_texture_size", 256)
        lib.save_loaded_asset(tex, False)


DARKER = {"rock_mat": 0.4, "bubble_mat": 0.45, "fish_body_mat": 0.6, "fish_fin_mat": 0.7}   # fish glowed white too     # bubbles: glowing orbs at full white with Chapter 1's bloom     # Chapter 1's rock texture tint read as pale foam under the green light


def darker(mats):
    for name, k in DARKER.items():
        mi = mats.get(name)
        if mi:
            c = MEL.get_material_instance_vector_parameter_value(mi, "Color")
            MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(c.r * k, c.g * k, c.b * k, 1))
            lib.save_loaded_asset(mi, False)


def place_set(data, mats):
    for name, fbx in data["sets"].items():
        mesh = import_set(name, fbx, mats)
        a = tagged(actors.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0)), name, "Sets")
        comp = a.static_mesh_component
        if name.endswith(("_specks", "_shafts")):     # silt flecks and light shafts: seen, never felt
            no_collision(comp)
            comp.set_cast_shadow(False)
        elif name.endswith("_fx"):
            no_collision(comp)
            comp.set_cast_shadow(False)
        elif name.endswith("_block"):
            a.set_actor_hidden_in_game(True)
            comp.set_editor_property("visible", False)
            comp.set_cast_shadow(False)
    for l in data["lights"]:
        p = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*l["position"]))
        c = p.point_light_component
        c.set_intensity(l["intensity"])
        c.set_light_color(unreal.LinearColor(*l["color"], 1))
        c.set_attenuation_radius(l["radius"])
        c.set_cast_shadows(False)
        tagged(p, l["name"], "Sets/Lights")


GROUND_HLSL = """
// The lakebed ground: sand on the flat, silt where it starts to rise, clay up the banks, layered
// rock on the steepest walls. Blended by slope (sine of the angle) with world noise, so the lines
// wander and are soft. Walls use triplanar mapping (no stretching) and get sediment bands.
float3 n = normalize(N);
float s = sqrt(saturate(1.0 - n.z * n.z));
float wob = 0.07 * sin(WP.x / 170.0 + WP.y / 230.0) + 0.04 * sin(WP.x / 61.0 - WP.y / 47.0);
float3 w = pow(abs(n), 4.0);
w /= (w.x + w.y + w.z);
float3 sand = Sand.Sample(SandSampler, WP.xy / SandSize).rgb * SandTint;
float3 silt = Silt.Sample(SiltSampler, WP.xy / SiltSize).rgb * SiltTint;
float3 clay = (Clay.Sample(ClaySampler, WP.yz / ClaySize).rgb * w.x
             + Clay.Sample(ClaySampler, WP.xz / ClaySize).rgb * w.y
             + Clay.Sample(ClaySampler, WP.xy / ClaySize).rgb * w.z) * ClayTint;
float3 rock = (Rock.Sample(RockSampler, WP.yz / RockSize).rgb * w.x
             + Rock.Sample(RockSampler, WP.xz / RockSize).rgb * w.y
             + Rock.Sample(RockSampler, WP.xy / RockSize).rgb * w.z) * RockTint;
// rock shows in patches through the clay, more of it the steeper the wall
float patches = 0.12 * sin(WP.x / 330.0 + WP.z / 140.0) + 0.08 * sin(WP.y / 210.0 - WP.z / 90.0);
float a = smoothstep(SiltSlope.x, SiltSlope.y, s + wob);
float b = smoothstep(ClaySlope.x, ClaySlope.y, s + wob);
float c = smoothstep(RockSlope.x, RockSlope.y, s + wob + patches);
float3 col = lerp(lerp(lerp(sand, silt, a), clay, b), rock, c);
// sediment bands: layers of uneven thickness and strength stacked up the wall, gently warped,
// fading in only where the wall is steep (not on the silt at its foot)
float z = WP.z / Strata.x + 1.5 * sin(WP.x / 900.0 + WP.y / 700.0) + 0.4 * sin(WP.y / 260.0 + WP.x / 410.0);
float layer = floor(z);
float h = frac(sin(layer * 12.9898) * 43758.5453);          // each layer its own shade
float h2 = frac(sin(layer * 78.233) * 12345.678);
float edge = smoothstep(0.0, 0.08, frac(z)) * smoothstep(1.0, 0.9, frac(z));   // thin dark seams between layers
float band = (h - 0.5) * 0.9 + (edge - 1.0) * 0.6 * h2;
col *= 1.0 + Strata.y * band * smoothstep(0.45, 0.7, s + wob);
return col;
"""


def ground_material(spec):
    """M_Ch2_Ground: one material for the whole lakebed (see GROUND_HLSL). Numbers in textures.json."""
    m = _fresh(f"{CH2}/Materials/M_Ch2_Ground", "M_Ch2_Ground")
    pins = ["N", "WP"]
    node_in = {}
    y = -400
    for layer in ("sand", "silt", "clay", "rock"):
        L = spec[layer]
        name = layer.capitalize()
        tex = MEL.create_material_expression(m, unreal.MaterialExpressionTextureObjectParameter, -900, y)
        tex.set_editor_property("parameter_name", name)
        tex.set_editor_property("texture", unreal.load_asset(f"/Game/Horror/Textures/T_{L['texture']}"))
        size = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -900, y + 120)
        size.set_editor_property("parameter_name", name + "Size")
        size.set_editor_property("default_value", float(L["size"]))
        tint = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -900, y + 200)
        tint.set_editor_property("parameter_name", name + "Tint")
        tint.set_editor_property("default_value", unreal.LinearColor(*L["tint"], 1))
        node_in.update({name: tex, name + "Size": size, name + "Tint": tint})
        if "slope" in L:
            sl = MEL.create_material_expression(m, unreal.MaterialExpressionConstant2Vector, -900, y + 300)
            sl.set_editor_property("r", float(L["slope"][0]))
            sl.set_editor_property("g", float(L["slope"][1]))
            node_in[name + "Slope"] = sl
        y += 420
    st = MEL.create_material_expression(m, unreal.MaterialExpressionConstant2Vector, -900, y)
    st.set_editor_property("r", float(spec["strata"]["spacing"]))
    st.set_editor_property("g", float(spec["strata"]["strength"]))
    node_in["Strata"] = st
    pins += list(node_in)
    node = _custom(m, GROUND_HLSL, pins, unreal.CustomMaterialOutputType.CMOT_FLOAT3, -400, 0)
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -900, -600), "", node, "N")
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -900, -700), "", node, "WP")
    for name, expr in node_in.items():
        MEL.connect_material_expressions(expr, "", node, name)
    MEL.connect_material_property(node, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for prop, v in ((unreal.MaterialProperty.MP_ROUGHNESS, 1.0), (unreal.MaterialProperty.MP_SPECULAR, 0.0)):
        c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -200, 300)
        c.set_editor_property("r", v)
        MEL.connect_material_property(c, "", prop)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


SHAFT_HLSL = """
// A shaft of light from the surface: bright near the top, gone by the bottom, soft at its sides
// (seen edge-on it fades), slowly shimmering.
float top = saturate(1.0 - (Top - WP.z) / Len);
float side = pow(saturate(abs(dot(normalize(N), normalize(V)))), 1.5);
float shimmer = 0.75 + 0.25 * sin(T * 0.8 + WP.x / 90.0 + WP.y / 120.0);
return Color * Strength * top * top * side * shimmer;
"""

SURFACE_HLSL = """
// The underside of the lake surface: faint light moving through ripples overhead.
float2 p = WP.xy / 220.0;
float r = sin(p.x * 3.1 + T * 0.5) * sin(p.y * 2.7 - T * 0.4) + 0.5 * sin((p.x + p.y) * 5.3 + T * 0.9);
return Color * (0.6 + 0.4 * r);
"""


def _params(m, specs, x=-900, y=0):
    out = {}
    for name, value in specs:
        if isinstance(value, tuple):
            e = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, x, y)
            e.set_editor_property("default_value", unreal.LinearColor(*value, 1))
        else:
            e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
            e.set_editor_property("default_value", float(value))
        e.set_editor_property("parameter_name", name)
        out[name] = e
        y += 110
    return out


def _wire(m, node, inputs):
    for pin, expr in inputs.items():
        MEL.connect_material_expressions(expr, "", node, pin)


def specks_material():
    """M_Ch2_Specks: unlit pale flecks of silt."""
    m = _fresh(f"{CH2}/Materials/M_Ch2_Specks", "M_Ch2_Specks")
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    prm = _params(m, [("Color", (0.3, 0.42, 0.36))])
    MEL.connect_material_property(prm["Color"], "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


def shaft_material():
    """M_Ch2_Shaft: additive, unlit, two-sided glow for the light shafts."""
    m = _fresh(f"{CH2}/Materials/M_Ch2_Shaft", "M_Ch2_Shaft")
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    prm = _params(m, [("Color", (0.35, 0.75, 0.6)), ("Strength", 0.8), ("Top", 0.0), ("Len", 900.0)])
    node = _custom(m, SHAFT_HLSL, ["WP", "N", "V", "T", "Color", "Strength", "Top", "Len"],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, -400, 0)
    _wire(m, node, {"WP": MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -900, -300),
                    "N": MEL.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -900, -200),
                    "V": MEL.create_material_expression(m, unreal.MaterialExpressionCameraVectorWS, -900, -100),
                    "T": MEL.create_material_expression(m, unreal.MaterialExpressionTime, -900, -400),
                    **prm})
    MEL.connect_material_property(node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


def surface_material():
    """M_Ch2_Surface: the lake surface from below, a faint moving glow (it was plain black)."""
    m = _fresh(f"{CH2}/Materials/M_Ch2_Surface", "M_Ch2_Surface")
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    prm = _params(m, [("Color", (0.05, 0.16, 0.14))])
    node = _custom(m, SURFACE_HLSL, ["WP", "T", "Color"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -400, 0)
    _wire(m, node, {"WP": MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -900, -300),
                    "T": MEL.create_material_expression(m, unreal.MaterialExpressionTime, -900, -200), **prm})
    MEL.connect_material_property(node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


SWAY_HLSL = """
// Things moving in the water. Sway: plants bend back and forth, more the higher up they are
// (Obj = the actor's base). Drift: a slow float, the same over metres, so a whole fleck or rope
// moves as one.
float h = max(0.0, WP.z - Obj.z);
float k = pow(saturate(h / SwayHeight), 1.5) * SwayAmp;
float ph = T * SwaySpeed + Obj.x * 0.011 + Obj.y * 0.017;
float3 sway = float3(sin(ph + h * 0.015), cos(ph * 0.83 + h * 0.012), 0.0) * k;
sway += Drift * float3(sin(T * 0.21 + WP.y / 310.0), cos(T * 0.17 + WP.x / 290.0), 0.6 * sin(T * 0.13 + (WP.x + WP.y) / 330.0));
// Rise: bubbles climb Rise cm/s up their column and start again at the bottom after RiseHeight,
// wobbling side to side as they go
if (Rise > 0.0) {
    float hz = WP.z - Obj.z;
    float nz = frac((hz + T * Rise) / RiseHeight) * RiseHeight;
    sway += float3(sin(T * 4.0 + hz * 0.11) * 1.5, cos(T * 3.3 + hz * 0.13) * 1.5, nz - hz);
}
// Orbit: a fish school milling round its centre (Obj) at Orbit rad/s. Every fish turns with the
// ring, a ripple runs down each body (its wavelength about a fish long), and the school bobs.
if (Orbit != 0.0) {
    float3 r = WP - Obj;
    float a = T * Orbit;
    float ca = cos(a), sa = sin(a);
    float2 q = float2(r.x * ca - r.y * sa, r.x * sa + r.y * ca);
    float th = atan2(q.y, q.x);
    float rad = max(length(q), 1.0);
    q += (q / rad) * sin(th * rad / 2.4 - T * 9.0) * 0.9;
    sway += float3(q - r.xy, sin(T * 0.4 + th * 2.0) * 25.0);
}
"""

SWAY = {   # Maya material -> (SwayAmp cm, SwayHeight cm, SwaySpeed, Drift cm)
    "weed_mat": (16.0, 160.0, 0.9, 0.0),
    "weed_brown_mat": (10.0, 120.0, 1.1, 0.0),
    "rope_mat": (0.0, 1.0, 0.0, 6.0),
    "specks_mat": (0.0, 1.0, 0.0, 18.0),
    "bubble_mat": (0.0, 1.0, 0.0, 0.0, 38.0, 600.0),    # + Rise cm/s, RiseHeight (= make_lakebed BUBBLE_RISE)
    # fish: every part of a fish must move the same way (+ Orbit rad/s: ~0.13 = a fish 3 m out swims 40 cm/s)
    "fish_body_mat": (0, 1, 0, 0, 0, 600, 0.13), "fish_back_mat": (0, 1, 0, 0, 0, 600, 0.13),
    "fish_fin_mat": (0, 1, 0, 0, 0, 600, 0.13), "fish_eye_mat": (0, 1, 0, 0, 0, 600, 0.13),
}


def sway_material():
    """M_Ch2_Sway: a copy of Chapter 1's M_PS2_Surface (texture, colour, PS2 wobble) whose
    World Position Offset node also sways and drifts. Unreal's Python can't connect anything to
    World Position Offset, but the copy keeps Chapter 1's hand-made wire, so its node is edited
    in place and fed new inputs."""
    path = f"{CH2}/Materials/M_Ch2_Sway"
    if lib.does_asset_exist(path):
        lib.delete_asset(path)
    m = lib.duplicate_asset(SURFACE, path)
    node = [e for e in unreal.ObjectIterator(unreal.MaterialExpressionCustom) if e.get_outer() == m][0]
    code = node.get_editor_property("code")
    code = code.replace("return float3(0, 0, 0);", "return sway;")
    code = code.replace("return floor(Rel / g + 0.5) * g - Rel;", "return sway + floor(Rel / g + 0.5) * g - Rel;")
    node.set_editor_property("code", SWAY_HLSL + code)
    ins = list(node.get_editor_property("inputs"))
    new = {}
    for name, default in (("WP", None), ("Obj", None), ("T", None), ("SwayAmp", 0.0), ("SwayHeight", 100.0),
                          ("SwaySpeed", 1.0), ("Drift", 0.0), ("Rise", 0.0), ("RiseHeight", 900.0), ("Orbit", 0.0)):
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", name)
        ins.append(ci)
        if default is not None:
            new[name] = _params(m, [(name, default)], -1400, 600 + len(new) * 110)[name]
    node.set_editor_property("inputs", ins)
    new["WP"] = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1400, 300)
    new["Obj"] = MEL.create_material_expression(m, unreal.MaterialExpressionObjectPositionWS, -1400, 400)
    new["T"] = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -1400, 500)
    _wire(m, node, new)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


def make_sway(mats, sway):
    """Re-parent the moving things' material instances onto M_Ch2_Sway with their numbers."""
    for name, nums in SWAY.items():
        amp, height, speed, drift, rise, rise_h, orbit = (tuple(nums) + (0.0, 900.0, 0.0)[len(nums) - 4:])[:7]
        mi = mats.get(name)
        if not mi or not isinstance(mi, unreal.MaterialInstanceConstant):
            continue
        mi.set_editor_property("parent", sway)
        for p, v in (("SwayAmp", amp), ("SwayHeight", height), ("SwaySpeed", speed), ("Drift", drift),
                     ("Rise", rise), ("RiseHeight", rise_h), ("Orbit", orbit)):
            MEL.set_material_instance_scalar_parameter_value(mi, p, v)
        lib.save_loaded_asset(mi, False)


# ---------- 3. the scatter ----------

def maya_to_unreal(m):
    """Maya world matrix -> unreal.Transform (Maya's Y and Z swap; as in import_scatter.py)."""
    swap = lambda v: unreal.Vector(v[0], v[2], v[1])
    x_axis, y_axis, z_axis = swap(m[0:3]), swap(m[8:11]), swap(m[4:7])
    rotation = unreal.MathLibrary.make_rot_from_xz(x_axis, z_axis)
    return unreal.Transform(swap(m[12:15]), rotation, unreal.Vector(x_axis.length(), y_axis.length(), z_axis.length()))


def place_schools(data):
    """A copy of the fish school (data["props"]) at each spot in data["schools"]; they swim by material."""
    mesh = unreal.load_asset(f"{SETS_DIR}/lb_fish_school")
    for i, pos in enumerate(data.get("schools", [])):
        a = tagged(actors.spawn_actor_from_object(mesh, unreal.Vector(*pos)), f"FishSchool_{i}", "Fish")
        no_collision(a.static_mesh_component)
        a.static_mesh_component.set_cast_shadow(False)
    return len(data.get("schools", []))


def place_scatter(table):
    data = json.load(open(f"{RP2}/export/scatter.json"))
    mats = materials(data["materials"], table)
    darker(mats)
    mats["lb_ground_mat"] = unreal.load_asset(f"{CH2}/Materials/M_Ch2_Ground")   # rocks: silt on top, rock on the sides
    make_sway(mats, unreal.load_asset(f"{CH2}/Materials/M_Ch2_Sway"))              # the plants sway
    global SETS_DIR
    SETS_DIR = f"{CH2}/Props"
    meshes = {asset: import_set(asset, info["fbx"], mats) for asset, info in data["props"].items()}
    SETS_DIR = f"{CH2}/Sets"
    copies = data["copies"]
    with unreal.ScopedSlowTask(len(copies), "Placing the lakebed scatter") as task:
        task.make_dialog(True)
        for i, c in enumerate(copies):
            task.enter_progress_frame(1)
            xf = maya_to_unreal(c["matrix"])
            a = actors.spawn_actor_from_object(meshes[c["asset"]], xf.translation, xf.rotation.rotator())
            a.set_actor_transform(xf, False, False)
            tagged(a, f"{c['asset']}_{i}", f"Scatter/{c['network']}")
            comp = a.static_mesh_component
            if any(k in c["asset"] for k in ("weed", "milfoil", "tuft", "litter", "bubbles")):
                no_collision(comp)    # walk through the weed
                comp.set_cast_shadow(False)
    return len(copies)


# ---------- 4. the underwater look ----------

CAUSTICS_HLSL = """
// Wobbling light from the surface ripples, thrown down on the lakebed (a light function).
float2 p = WP.xy / Scale;
float t = T * Speed;
float c = 0;
float2 q = p;
for (int i = 0; i < 3; i++) {
    q += float2(sin(q.y * 1.7 + t * 0.9), cos(q.x * 1.3 - t * 0.7)) * 0.6;
    c += abs(sin(q.x + q.y + t));
}
c = pow(saturate(1.0 - c / 3.0), 3.0) * Strength;
return 0.45 + c;
"""


def caustics_material():
    path = f"{CH2}/Materials/M_Caustics"
    m = _fresh(path, "M_Caustics")
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_LIGHT_FUNCTION)
    params = []
    for i, (name, value) in enumerate((("Scale", 180.0), ("Speed", 0.6), ("Strength", 3.0))):
        p = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, i * 100)
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", value)
        params.append((name, p))
    wp = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -700, -150)
    tm = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -700, 320)
    node = _custom(m, CAUSTICS_HLSL, ["WP", "T", "Scale", "Speed", "Strength"],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT1, -350, 50)
    MEL.connect_material_expressions(wp, "", node, "WP")
    MEL.connect_material_expressions(tm, "", node, "T")
    for name, p in params:
        MEL.connect_material_expressions(p, "", node, name)
    MEL.connect_material_property(node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


WATER = unreal.LinearColor(0.1, 0.28, 0.25, 1)         # the colour of the murk (tuned from screenshots 2026-11-24)


def underwater_look(ps2_settings, data):
    # light from the surface: dim, green-blue, rippling
    sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(0, -75, 20))
    c = sun.light_component
    c.set_intensity(40.0)         # bright enough under Chapter 1's night exposure
    c.set_light_color(unreal.LinearColor(0.45, 0.85, 0.75, 1))
    c.set_editor_property("light_function_material", caustics_material())
    c.set_editor_property("cast_shadows", False)
    tagged(sun, "Surface_Light", "Look")
    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 300))
    sc = sky.light_component
    sc.set_intensity(8.0)
    sc.set_light_color(unreal.LinearColor(0.3, 0.6, 0.55, 1))
    sc.set_editor_property("lower_hemisphere_color", unreal.LinearColor(0.01, 0.02, 0.02, 1))
    tagged(sky, "SkyLight", "Look")
    # the murk: thick everywhere, thicker the deeper you go (height falloff from the surface down)
    fog = actors.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, data["surface_z"]))
    f = fog.component
    f.set_editor_property("fog_density", 1.0)         # ~10 m before things fade out
    f.set_editor_property("fog_height_falloff", 0.2)
    f.set_editor_property("fog_inscattering_luminance", WATER)
    f.set_editor_property("fog_max_opacity", 1.0)
    f.set_editor_property("start_distance", 0.0)
    tagged(fog, "Murk", "Look")
    # Chapter 1's PS2 screen and exposure, tinted toward the water
    ppv = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
    ppv.set_editor_property("unbound", True)
    s = look_settings(ps2_settings)
    s.set_editor_property("override_color_gain", True)
    s.set_editor_property("color_gain", unreal.Vector4(0.75, 1.0, 0.95, 1.0))
    s.set_editor_property("override_color_saturation", True)
    s.set_editor_property("color_saturation", unreal.Vector4(0.7, 0.7, 0.7, 1.0))
    s.set_editor_property("override_bloom_intensity", True)
    s.set_editor_property("bloom_intensity", 1.2)           # Chapter 1's bloom 9 blew fish and bubbles out into glowing blobs
    s.set_editor_property("override_motion_blur_amount", True)
    s.set_editor_property("motion_blur_amount", 0.0)        # rising bubbles smeared into lines (and the PS2 had none)
    s.set_editor_property("override_scene_fringe_intensity", True)
    s.set_editor_property("scene_fringe_intensity", 0.0)     # Chapter 1's colour fringe turned the silt into rainbow sparkles
    s.set_editor_property("override_vignette_intensity", True)
    s.set_editor_property("vignette_intensity", 0.8)
    ppv.set_editor_property("settings", s)
    tagged(ppv, "PostProcess_Underwater", "Look")
    x, y, z = data["start"]
    start = actors.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(x, y, z), unreal.Rotator(0, 0, 90))
    tagged(start, "PlayerStart", "Look")


def main():
    data = json.load(open(f"{RP2}/export/sets_lakebed.json"))
    table = json.load(open(f"{RP1}/textures.json"))
    table.update(json.load(open(f"{RP2}/textures.json")).get("surfaces", {}))   # Chapter 2 extras (leaf litter)
    ps2 = chapter1_look()
    open_map()
    import_ch2_textures()
    mats = materials(data["materials"], table)
    darker(mats)
    mats["lb_ground_mat"] = ground_material(json.load(open(f"{RP2}/textures.json"))["ground"])
    sway = sway_material()
    make_sway(mats, sway)              # specks_mat, rope_mat (and the plants, in place_scatter)
    mats["shaft_mat"] = shaft_material()
    mats["under_surface_mat"] = surface_material()
    place_set(data, mats)
    for name, fbx in data.get("props", {}).items():      # the fish school
        import_set(name, fbx, mats)
    place_schools(data)
    n = place_scatter(table)
    underwater_look(ps2, data)
    level_subsys.save_current_level()
    # the heavy walk is its own script (heavy_walk.py): making Blueprints in this same run crashed Unreal
    level_subsys.save_current_level()
    print(f"Lakebed map made: {list(data['sets'])}, {len(data['lights'])} lights, {n} scatter copies")


main()

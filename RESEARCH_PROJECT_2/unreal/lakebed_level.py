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


DARKER = {"rock_mat": 0.4}     # Chapter 1's rock texture tint read as pale foam under the green light


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
        if name.endswith("_fx"):
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
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


# ---------- 3. the scatter ----------

def maya_to_unreal(m):
    """Maya world matrix -> unreal.Transform (Maya's Y and Z swap; as in import_scatter.py)."""
    swap = lambda v: unreal.Vector(v[0], v[2], v[1])
    x_axis, y_axis, z_axis = swap(m[0:3]), swap(m[8:11]), swap(m[4:7])
    rotation = unreal.MathLibrary.make_rot_from_xz(x_axis, z_axis)
    return unreal.Transform(swap(m[12:15]), rotation, unreal.Vector(x_axis.length(), y_axis.length(), z_axis.length()))


def place_scatter(table):
    data = json.load(open(f"{RP2}/export/scatter.json"))
    mats = materials(data["materials"], table)
    darker(mats)
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
            if "weed" in c["asset"]:
                comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)    # walk through the weed
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
    ps2 = chapter1_look()
    open_map()
    import_ch2_textures()
    mats = materials(data["materials"], table)
    darker(mats)
    mats["lb_ground_mat"] = ground_material(json.load(open(f"{RP2}/textures.json"))["ground"])
    place_set(data, mats)
    n = place_scatter(table)
    underwater_look(ps2, data)
    level_subsys.save_current_level()
    # the heavy walk is its own script (heavy_walk.py): making Blueprints in this same run crashed Unreal
    level_subsys.save_current_level()
    print(f"Lakebed map made: {list(data['sets'])}, {len(data['lights'])} lights, {n} scatter copies")


main()

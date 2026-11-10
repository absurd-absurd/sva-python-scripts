"""Place the hand-built sets from Maya (the motel) and their lights.

Run in the Unreal editor after maya/make_motel.py has exported export/set_motel.fbx and
export/sets.json (build_level.py runs it in the right order).

- Builds M_PS2_Neon once: a glowing material with an optional flicker, for every Maya
  material named glow_*. Strength and flicker per material come from textures.json "glow".
- Materials named pic_* are pictures (Cas's photos): export/<name>.png from
  tools/make_photos.py on M_PS2_Picture, mapped once across the plane.
- Every other Maya material becomes an instance of M_PS2_Surface (texture, tint and size
  from textures.json, like the props).
- The set is placed exactly where Maya built it, and each light locator becomes a point light.
- set_motel_rooms (the room insides) and lights marked "room" go on lighting channel 1, so the
  sign and lot lights (channel 0) don't shine through the walls into the rooms.
Safe to run again: the old set and its lights are removed first.
"""
import json

import unreal

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
SETS_DIR = "/Game/Horror/Sets"
MAT_DIR = "/Game/Horror/Materials/PS2/Props"
NEON = "/Game/Horror/Materials/PS2/M_PS2_Neon"
SURFACE = "/Game/Horror/Materials/PS2/M_PS2_Surface"
TAG = "set"
MEL = unreal.MaterialEditingLibrary
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

FLICKER_HLSL = """
// Dying neon. Flicker 0 = steady, 1 = full effect. Time is cut into ~0.8 s chunks; each
// chunk is randomly dead (fully dark), sputtering (hard on/off blinks), or steadily on.
float slow = frac(sin(floor(T * 1.3 + Seed) * 12.98) * 4375.85);
float fast = frac(sin(floor(T * 18.0 + Seed * 7.0) * 91.17) * 43758.55);
float on = slow < 0.35 ? 0.0 : (slow < 0.75 ? step(0.45, fast) : 1.0);
return lerp(1.0, on, Flicker);
"""


def neon_material():
    """Rebuilt on every run (it has no hand-made wires), so changes to the flicker take effect."""
    if lib.does_asset_exist(NEON):
        m = unreal.load_asset(NEON)
        # a material open in an editor window can't be edited by script (nodes come back None)
        unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(m)
        MEL.delete_all_material_expressions(m)
    else:
        m = tools.create_asset("M_PS2_Neon", NEON.rsplit("/", 1)[0], unreal.Material, unreal.MaterialFactoryNew())
    color = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -900, -100)
    color.set_editor_property("parameter_name", "Color")
    glass = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -500, -300)
    glass.set_editor_property("parameter_name", "Glass")                 # what an unlit tube looks like
    glass.set_editor_property("default_value", unreal.LinearColor(0.08, 0.06, 0.06, 1))   # dark when off
    MEL.connect_material_property(glass, "", unreal.MaterialProperty.MP_BASE_COLOR)
    params = {}
    for i, (name, value) in enumerate((("Strength", 4.0), ("Flicker", 0.0), ("Seed", 0.0))):
        p = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -900, 50 + i * 90)
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", value)
        params[name] = p
    time = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -900, 330)
    flick = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, -600, 200)
    flick.set_editor_property("code", FLICKER_HLSL)
    flick.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    pins = []
    for n in ("T", "Flicker", "Seed"):
        pin = unreal.CustomInput()
        pin.set_editor_property("input_name", n)
        pins.append(pin)
    flick.set_editor_property("inputs", pins)
    MEL.connect_material_expressions(time, "", flick, "T")
    MEL.connect_material_expressions(params["Flicker"], "", flick, "Flicker")
    MEL.connect_material_expressions(params["Seed"], "", flick, "Seed")
    a = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, -50)
    MEL.connect_material_expressions(color, "", a, "A")
    MEL.connect_material_expressions(params["Strength"], "", a, "B")
    b = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 0)
    MEL.connect_material_expressions(a, "", b, "A")
    MEL.connect_material_expressions(flick, "", b, "B")
    MEL.connect_material_property(b, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


PICTURE = "/Game/Horror/Materials/PS2/M_PS2_Picture"
PIC_DIR = "/Game/Horror/Textures/Pictures"


def picture_material():
    """M_PS2_Picture: a photo or print mapped once across its plane (UVs, not world projection),
    matte like the other PS2 surfaces. Rebuilt on every run like the neon."""
    if lib.does_asset_exist(PICTURE):
        m = unreal.load_asset(PICTURE)
        unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(m)
        MEL.delete_all_material_expressions(m)
    else:
        m = tools.create_asset("M_PS2_Picture", PICTURE.rsplit("/", 1)[0], unreal.Material, unreal.MaterialFactoryNew())
    tex = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -600, 0)
    tex.set_editor_property("parameter_name", "Tex")
    color = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -600, 250)
    color.set_editor_property("parameter_name", "Color")
    color.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, 100)
    MEL.connect_material_expressions(tex, "RGB", mul, "A")
    MEL.connect_material_expressions(color, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for prop, v, y in ((unreal.MaterialProperty.MP_ROUGHNESS, 1.0, 400), (unreal.MaterialProperty.MP_SPECULAR, 0.0, 480)):
        c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, y)
        c.set_editor_property("r", v)
        MEL.connect_material_property(c, "", prop)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


def picture_texture(name):
    """export/<name>.png -> /Game/Horror/Textures/Pictures/T_<name>, kept crisp (PS2: no smoothing)."""
    t = unreal.AssetImportTask()
    t.filename = f"{ROOT}/export/{name}.png"
    t.destination_path = PIC_DIR
    t.destination_name = f"T_{name}"
    t.automated, t.save, t.replace_existing = True, True, True
    tools.import_asset_tasks([t])
    tex = unreal.load_asset(f"{PIC_DIR}/T_{name}")
    tex.set_editor_property("filter", unreal.TextureFilter.TF_NEAREST)
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    if "asphalt" in name:              # the lot and road pictures: no mipmaps, so both stay equally sharp
        tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tex.set_editor_property("never_stream", True)
    lib.save_loaded_asset(tex, False)
    return tex


WATER = "/Game/Horror/Materials/PS2/M_PS2_Water"
MIST = "/Game/Horror/Materials/PS2/M_PS2_Mist"

WATER_HLSL = """
// still lake water: a slow, faint ripple in the surface normal (no texture needed)
float2 p = W.xy;
float2 g = float2(sin(p.x * 0.011 + T * 0.6) + 0.6 * sin(p.y * 0.017 + T * 0.45) + 0.3 * sin((p.x + p.y) * 0.031 + T * 1.1),
                  cos(p.y * 0.013 + T * 0.5) + 0.5 * cos(p.x * 0.021 - T * 0.4) + 0.3 * cos((p.x - p.y) * 0.027 + T * 0.9));
return normalize(float3(g * Amp, 1.0));
"""
MIST_HLSL = """
// low mist: soft drifting banks (layered waves), slowly moving across the lake
float2 p = W.xy * 0.0006 + float2(T * 0.012, T * 0.007);
float n = sin(p.x * 6.1) * sin(p.y * 5.3) + 0.5 * sin(p.x * 13.7 + p.y * 9.1 + T * 0.05) + 0.25 * sin(p.x * 27.0 - p.y * 23.0);
return saturate(n * 0.35 + 0.45) * Op;
"""


def _custom(m, code, pins, out, x, y):
    c = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    c.set_editor_property("code", code)
    c.set_editor_property("output_type", out)
    ins = []
    for n in pins:
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", n)
        ins.append(ci)
    c.set_editor_property("inputs", ins)
    return c


def _fresh(path, name):
    if lib.does_asset_exist(path):
        m = unreal.load_asset(path)
        unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(m)
        MEL.delete_all_material_expressions(m)
        return m
    return tools.create_asset(name, path.rsplit("/", 1)[0], unreal.Material, unreal.MaterialFactoryNew())


def water_material():
    """M_PS2_Water: dark, glossy, a slow ripple, so the dock lantern and the lamps lay streaks
    of light on it. Rebuilt every run."""
    m = _fresh(WATER, "M_PS2_Water")
    color = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -500, -200)
    color.set_editor_property("parameter_name", "Color")
    MEL.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for prop, v, y in ((unreal.MaterialProperty.MP_ROUGHNESS, 0.16, 0), (unreal.MaterialProperty.MP_SPECULAR, 0.12, 80)):
        c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, y)
        c.set_editor_property("r", v)
        MEL.connect_material_property(c, "", prop)
    rip = _custom(m, WATER_HLSL, ("W", "T", "Amp"), unreal.CustomMaterialOutputType.CMOT_FLOAT3, -300, 200)
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -600, 200), "", rip, "W")
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionTime, -600, 280), "", rip, "T")
    amp = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, 360)
    amp.set_editor_property("parameter_name", "Ripple")
    amp.set_editor_property("default_value", 0.012)
    MEL.connect_material_expressions(amp, "", rip, "Amp")
    MEL.connect_material_property(rip, "", unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


def mist_material():
    """M_PS2_Mist: translucent drifting mist, fading out where it meets the ground (depth fade)."""
    m = _fresh(MIST, "M_PS2_Mist")
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("two_sided", True)
    color = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -500, -200)
    color.set_editor_property("parameter_name", "Color")
    MEL.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    n = _custom(m, MIST_HLSL, ("W", "T", "Op"), unreal.CustomMaterialOutputType.CMOT_FLOAT1, -500, 100)
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -800, 100), "", n, "W")
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionTime, -800, 180), "", n, "T")
    op = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -800, 260)
    op.set_editor_property("parameter_name", "Opacity")
    op.set_editor_property("default_value", 0.2)
    MEL.connect_material_expressions(op, "", n, "Op")
    fade = MEL.create_material_expression(m, unreal.MaterialExpressionDepthFade, -250, 100)
    fade.set_editor_property("fade_distance_default", 220.0)
    MEL.connect_material_expressions(n, "", fade, "Opacity")
    MEL.connect_material_property(fade, "", unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


GLASS = "/Game/Horror/Materials/PS2/M_PS2_Glass"
GLOSS = "/Game/Horror/Materials/PS2/M_PS2_Gloss"


def gloss_material():
    """M_PS2_Gloss: the PS2 surface (keeps its wobble wire) with a little shine, for car paint and
    chrome (Maya materials named gloss_*). Made once from M_PS2_Surface."""
    if lib.does_asset_exist(GLOSS):
        return unreal.load_asset(GLOSS)
    m = lib.duplicate_asset(SURFACE, GLOSS)
    for prop, v in ((unreal.MaterialProperty.MP_ROUGHNESS, 0.32), (unreal.MaterialProperty.MP_SPECULAR, 0.6)):
        node = MEL.get_material_property_input_node(m, prop)
        if node:
            node.set_editor_property("r", v)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


def glass_material():
    """M_PS2_Glass: see-through window glass (translucent, a dark tint, a bit glossy).
    For Maya materials named seeglass_*. Rebuilt on every run."""
    if lib.does_asset_exist(GLASS):
        m = unreal.load_asset(GLASS)
        unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(m)
        MEL.delete_all_material_expressions(m)
    else:
        m = tools.create_asset("M_PS2_Glass", GLASS.rsplit("/", 1)[0], unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("two_sided", True)
    color = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -500, 0)
    color.set_editor_property("parameter_name", "Color")
    MEL.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for prop, v, y, name in ((unreal.MaterialProperty.MP_OPACITY, 0.28, 200, "Opacity"),
                             (unreal.MaterialProperty.MP_ROUGHNESS, 0.15, 300, None),
                             (unreal.MaterialProperty.MP_SPECULAR, 0.6, 400, None)):
        if name:
            c = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -500, y)
            c.set_editor_property("parameter_name", name)
            c.set_editor_property("default_value", v)
        else:
            c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -500, y)
            c.set_editor_property("r", v)
        MEL.connect_material_property(c, "", prop)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


LIGHT_FLICKER = "/Game/Horror/Materials/PS2/M_PS2_LightFlicker"
DEAD_SEED = 3.0        # the dead M's neon and its light share this, so they die and sputter together


def light_flicker_material():
    """A light function: dims a light with the same flicker code as the dead neon."""
    if lib.does_asset_exist(LIGHT_FLICKER):
        m = unreal.load_asset(LIGHT_FLICKER)
        # a material open in an editor window can't be edited by script (nodes come back None)
        unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(m)
        MEL.delete_all_material_expressions(m)
    else:
        m = tools.create_asset("M_PS2_LightFlicker", LIGHT_FLICKER.rsplit("/", 1)[0], unreal.Material,
                               unreal.MaterialFactoryNew())
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_LIGHT_FUNCTION)
    time = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -700, 0)
    flick = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, -400, 0)
    flick.set_editor_property("code", FLICKER_HLSL)
    flick.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    pins = []
    for n in ("T", "Flicker", "Seed"):
        pin = unreal.CustomInput()
        pin.set_editor_property("input_name", n)
        pins.append(pin)
    flick.set_editor_property("inputs", pins)
    MEL.connect_material_expressions(time, "", flick, "T")
    for n, v, y in (("Flicker", 1.0, 120), ("Seed", DEAD_SEED, 200)):
        c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -700, y)
        c.set_editor_property("r", v)
        MEL.connect_material_expressions(c, "", flick, n)
    MEL.connect_material_property(flick, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


def instance(name, parent):
    path = f"{MAT_DIR}/{name}"
    mi = unreal.load_asset(path) if lib.does_asset_exist(path) else \
        tools.create_asset(name, MAT_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    return mi


def materials(colors, table):
    neon, surface, pic = neon_material(), unreal.load_asset(SURFACE), None
    glow = table.get("glow", {})
    made = {}
    for i, (name, rgb) in enumerate(colors.items()):
        if name.startswith("glow_"):
            mi = instance(f"MI_PS2_{name}", neon)
            spec = glow.get(name, {})
            MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*rgb, 1))
            MEL.set_material_instance_scalar_parameter_value(mi, "Strength", float(spec.get("strength", 4.0)))
            MEL.set_material_instance_scalar_parameter_value(mi, "Flicker", float(spec.get("flicker", 0.0)))
            if "glass" in spec:          # what it looks like unlit / in the flashlight (default: dark glass)
                MEL.set_material_instance_vector_parameter_value(mi, "Glass", unreal.LinearColor(*spec["glass"], 1))
            seed = DEAD_SEED if spec.get("flicker", 0) >= 1 else float(i)
            MEL.set_material_instance_scalar_parameter_value(mi, "Seed", seed)
        elif name.startswith("water_"):
            mi = instance(f"MI_PS2_{name}", water_material())
            MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*rgb, 1))
        elif name.startswith("mist_"):
            mi = instance(f"MI_PS2_{name}", mist_material())
            MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*rgb, 1))
        elif name.startswith("gloss_"):
            mi = instance(f"MI_PS2_{name}", gloss_material())
            MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*rgb, 1))
        elif name.startswith("seeglass_"):
            mi = instance(f"MI_PS2_{name}", glass_material())
            MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*rgb, 1))
            if "car" in name:              # tinted car glass: you see shapes inside, not a convertible
                MEL.set_material_instance_scalar_parameter_value(mi, "Opacity", 0.72)
        elif name.startswith("pic_"):
            pic = pic or picture_material()
            mi = instance(f"MI_PS2_{name}", pic)
            MEL.set_material_instance_texture_parameter_value(mi, "Tex", picture_texture(name))
            MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*rgb, 1))
        else:
            mi = instance(f"MI_PS2_{name}", surface)
            MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*rgb, 1))
            # texture, tint and size from textures.json (same as apply_textures.py does)
            spec = table.get(f"MI_PS2_{name}")
            tex = spec and unreal.load_asset(f"/Game/Horror/Textures/T_{spec['texture']}")
            if tex:
                MEL.set_material_instance_texture_parameter_value(mi, "Tex", tex)
                MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*spec["tint"], 1))
                MEL.set_material_instance_scalar_parameter_value(mi, "TexSize", float(spec["size"]))
        lib.save_loaded_asset(mi, False)
        made[name] = mi
    return made


def channels(outside, rooms):
    lc = unreal.LightingChannels()
    lc.set_editor_property("channel0", outside)
    lc.set_editor_property("channel1", rooms)
    return lc


# Lighting channels keep outside light out of the rooms without shadows: the room insides
# (set_motel_rooms) and the room lamps are on channel 1 only; everything else is on channel 0.
# The flashlight and the moonlight are on both (flashlight.py, blockout.py).
ROOM_ONLY = channels(False, True)


def import_set(name, fbx, mats):
    t = unreal.AssetImportTask()
    t.filename = fbx
    t.destination_path = SETS_DIR
    t.destination_name = name
    t.automated = True
    t.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    mesh = unreal.load_asset(f"{SETS_DIR}/{name}")
    body = mesh.get_editor_property("body_setup")
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    mesh.set_editor_property("body_setup", body)
    # no Nanite: Unreal switches it on for big meshes, and its simplification crushed the thin
    # sign letters, window frames and the flat lot details (and fights the PS2 vertex wobble)
    nanite = mesh.get_editor_property("nanite_settings")
    nanite.set_editor_property("enabled", False)
    mesh.set_editor_property("nanite_settings", nanite)
    for i, slot in enumerate(mesh.static_materials):
        mi = mats.get(str(slot.material_slot_name))
        if mi:
            mesh.set_material(i, mi)
    lib.save_loaded_asset(mesh, False)
    return mesh


def main():
    # every set file: sets.json (the motel), sets_lake.json (the lake), ... merged
    import glob
    data = {"sets": {}, "materials": {}, "lights": [], "props": {}, "room_sets": []}
    for path in sorted(glob.glob(f"{ROOT}/export/sets*.json")):
        d = json.load(open(path))
        for k in ("sets", "materials", "props"):
            data[k].update(d.get(k, {}))
        for k in ("lights", "room_sets"):        # lists: room_sets (lighting channel 1) was being dropped
            data[k] += d.get(k, [])
    table = json.load(open(f"{ROOT}/textures.json"))
    gray_motel = ("Room", "Motel_Roof", "Walkway_Post", "Office",       # blockout.py's stand-ins
                  "Fence_Behind", "Shack", "RustedCar", "Tower_")             # (the trail structures: maya/make_trail.py)
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG) or (a.actor_has_tag("blockout") and a.get_actor_label().startswith(gray_motel)):
            actors.destroy_actor(a)
    mats = materials(data["materials"], table)
    for name, fbx in data["sets"].items():
        mesh = import_set(name, fbx, mats)
        a = actors.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0))
        comp = a.static_mesh_component
        if name.endswith("_fx"):                     # water, mist: seen, never stood on
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        elif name.endswith("_block"):                # invisible walls: felt, never seen
            a.set_actor_hidden_in_game(True)
            comp.set_editor_property("visible", False)
            comp.set_cast_shadow(False)
        a.set_actor_label(name)
        a.set_folder_path("Sets")
        a.tags = [TAG]
        if name in data.get("room_sets", []):
            a.static_mesh_component.set_editor_property("lighting_channels", ROOM_ONLY)
    for name, fbx in data.get("props", {}).items():       # pieces placed by other scripts (the doors)
        import_set(name, fbx, mats)
    flicker = light_flicker_material()
    for l in data["lights"]:
        p = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*l["position"]))
        c = p.point_light_component
        c.set_intensity(l["intensity"])
        c.set_light_color(unreal.LinearColor(*l["color"], 1))
        c.set_attenuation_radius(l["radius"])
        c.set_cast_shadows(bool(l.get("shadows")))   # off: cheap, soft, PS2-like (only the room fan lights cast them)
        if l.get("room"):
            c.set_editor_property("lighting_channels", ROOM_ONLY)
        if l.get("flicker"):
            c.set_light_function_material(flicker)   # dies and sputters with the dead neon
        p.set_actor_label(l["name"])
        p.set_folder_path("Sets/Lights")
        p.tags = [TAG]
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print(f"Sets placed: {list(data['sets'])}, {len(data['lights'])} lights, {len(mats)} materials")


main()

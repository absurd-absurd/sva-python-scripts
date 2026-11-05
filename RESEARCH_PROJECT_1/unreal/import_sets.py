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
    lib.save_loaded_asset(tex, False)
    return tex


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
    for i, slot in enumerate(mesh.static_materials):
        mi = mats.get(str(slot.material_slot_name))
        if mi:
            mesh.set_material(i, mi)
    lib.save_loaded_asset(mesh, False)
    return mesh


def main():
    data = json.load(open(f"{ROOT}/export/sets.json"))
    table = json.load(open(f"{ROOT}/textures.json"))
    gray_motel = ("Room", "Motel_Roof", "Walkway_Post", "Office")       # blockout.py's stand-in motel
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG) or (a.actor_has_tag("blockout") and a.get_actor_label().startswith(gray_motel)):
            actors.destroy_actor(a)
    mats = materials(data["materials"], table)
    for name, fbx in data["sets"].items():
        mesh = import_set(name, fbx, mats)
        a = actors.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0))
        a.set_actor_label(name)
        a.set_folder_path("Sets")
        a.tags = [TAG]
        if name in data.get("room_sets", []):
            a.static_mesh_component.set_editor_property("lighting_channels", ROOM_ONLY)
    flicker = light_flicker_material()
    for l in data["lights"]:
        p = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*l["position"]))
        c = p.point_light_component
        c.set_intensity(l["intensity"])
        c.set_light_color(unreal.LinearColor(*l["color"], 1))
        c.set_attenuation_radius(l["radius"])
        c.set_cast_shadows(False)                # cheap, soft, PS2-like (and no shadow flicker)
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

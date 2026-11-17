"""The keys in the world as their drawings (user, 2026-11-17: "the keys are still blocks, they should look
exactly like the key image"). Run in the Unreal editor after tools/make_keys.py, then unreal/place_clues.py.

  M_PS2_Cutout                a picture with see-through parts: base colour from the texture, the texture's
                              alpha as the opacity mask (masked, two-sided), matte like the PS2 surfaces
  T_KeyCard_<key> + MI_KeyCard_<key>   one per key: export/keycard_<key>.png (the drawing, cropped tight)
place_clues.py lays each key clue down as a flat plane with its MI_KeyCard, sized from export/keycards.json.
"""
import unreal

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/"
lib = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
CUTOUT = "/Game/Horror/Materials/PS2/M_PS2_Cutout"
PROPS = "/Game/Horror/Materials/PS2/Props"
TEX_DIR = "/Game/Horror/Textures/Pictures"


def cutout_material():
    if lib.does_asset_exist(CUTOUT):
        m = unreal.load_asset(CUTOUT)
        unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(m)
        MEL.delete_all_material_expressions(m)
    else:
        m = tools.create_asset("M_PS2_Cutout", CUTOUT.rsplit("/", 1)[0], unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    m.set_editor_property("two_sided", True)
    m.set_editor_property("opacity_mask_clip_value", 0.5)
    tex = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -600, 0)
    tex.set_editor_property("parameter_name", "Tex")
    MEL.connect_material_property(tex, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(tex, "A", unreal.MaterialProperty.MP_OPACITY_MASK)
    for prop, v, y in ((unreal.MaterialProperty.MP_ROUGHNESS, 0.6, 300), (unreal.MaterialProperty.MP_SPECULAR, 0.3, 380)):
        c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, y)
        c.set_editor_property("r", v)
        MEL.connect_material_property(c, "", prop)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


def card(name, parent):
    t = unreal.AssetImportTask()
    t.filename = ROOT + f"export/keycard_{name}.png"
    t.destination_path, t.destination_name = TEX_DIR, f"T_KeyCard_{name}"
    t.automated, t.save, t.replace_existing = True, True, True
    tools.import_asset_tasks([t])
    tex = unreal.load_asset(f"{TEX_DIR}/T_KeyCard_{name}")
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    lib.save_loaded_asset(tex, False)
    path = f"{PROPS}/MI_KeyCard_{name}"
    mi = unreal.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(
        f"MI_KeyCard_{name}", PROPS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    MEL.set_material_instance_texture_parameter_value(mi, "Tex", tex)
    lib.save_loaded_asset(mi, False)


m = cutout_material()
for k in ("key_office", "key_gate", "key_boathouse"):
    card(k, m)
print("key cut-outs ready")

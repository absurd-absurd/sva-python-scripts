"""Put the CC0 photo textures on everything, PS2-sized.

Run in the Unreal editor after blockout.py and import_scatter.py (or use build_level.py,
which runs them all in order). Needs textures/ filled by tools/fetch_textures.py.

1. Imports textures/*.jpg into /Game/Horror/Textures, capped at 256 px (PS2-size).
2. Adds world-aligned texture projection to M_PS2_Surface (once): a texture is projected
   from the sides and from above in world space, so boxes and props need no UVs. The
   new nodes are added next to the old ones, so the hand-made World Position Offset
   wire is kept.
3. Sets each material instance's texture, tint and size from textures.json.
"""
import json
import os

import unreal

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
TEX_DIR = "/Game/Horror/Textures"
SURFACE = "/Game/Horror/Materials/PS2/M_PS2_Surface"
PS2_SIZE = 256
MEL = unreal.MaterialEditingLibrary
lib = unreal.EditorAssetLibrary


def import_textures():
    folder = os.path.join(ROOT, "textures")
    tasks = []
    for f in sorted(os.listdir(folder)):
        if f.endswith(".jpg"):
            t = unreal.AssetImportTask()
            t.filename = os.path.join(folder, f)
            t.destination_path = TEX_DIR
            t.destination_name = "T_" + f[:-4]
            t.automated = True
            t.replace_existing = True
            tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    made = {}
    for t in tasks:
        name = os.path.basename(t.filename)[:-4]
        tex = unreal.load_asset(f"{TEX_DIR}/T_{name}")
        tex.set_editor_property("max_texture_size", PS2_SIZE)   # shrink to PS2 size
        lib.save_loaded_asset(tex)
        made[name] = tex
    return made


def add_projection():
    m = unreal.load_asset(SURFACE)
    if "Tex" in [str(n) for n in MEL.get_texture_parameter_names(m)]:
        return m                                   # already added
    tex = MEL.create_material_expression(m, unreal.MaterialExpressionTextureObjectParameter, -1100, -450)
    tex.set_editor_property("parameter_name", "Tex")
    tex.set_editor_property("texture", unreal.load_asset("/Engine/EngineResources/WhiteSquareTexture"))
    size = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -1100, -300)
    size.set_editor_property("parameter_name", "TexSize")
    size.set_editor_property("default_value", 200.0)
    size3 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -950, -300)
    size2 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -1000, -340)
    MEL.connect_material_expressions(size, "", size2, "A")
    MEL.connect_material_expressions(size, "", size2, "B")
    MEL.connect_material_expressions(size2, "", size3, "A")
    MEL.connect_material_expressions(size, "", size3, "B")
    proj = MEL.create_material_expression(m, unreal.MaterialExpressionMaterialFunctionCall, -800, -400)
    proj.set_material_function(unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture"))
    MEL.connect_material_expressions(tex, "", proj, "TextureObject")
    MEL.connect_material_expressions(size3, "", proj, "TextureSize")
    # find the Color parameter that already exists and multiply the texture by it
    color = MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_BASE_COLOR)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -350, -350)
    MEL.connect_material_expressions(proj, "XYZ Texture", mul, "A")
    MEL.connect_material_expressions(color, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m)
    return m


def find_instances():
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    found = {}
    for path in ("/Game/Horror/Materials/Blockout", "/Game/Horror/Materials/PS2/Props"):
        for a in reg.get_assets_by_path(path):
            found[str(a.asset_name)] = a.get_asset()
    return found


def main():
    textures = import_textures()
    add_projection()
    table = json.load(open(os.path.join(ROOT, "textures.json")))
    instances = find_instances()
    done, missing = 0, []
    for name, spec in table.items():
        if name.startswith("_") or "texture" not in spec:     # notes and the "glow" section
            continue
        mi, tex = instances.get(name), textures.get(spec["texture"])
        if not mi or not tex:
            missing.append(name)
            continue
        MEL.set_material_instance_texture_parameter_value(mi, "Tex", tex)
        MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*spec["tint"], 1))
        MEL.set_material_instance_scalar_parameter_value(mi, "TexSize", float(spec["size"]))
        lib.save_loaded_asset(mi)
        done += 1
    print(f"Textures: {len(textures)} imported, {done} materials textured" +
          (f", not found: {missing}" if missing else ""))


main()

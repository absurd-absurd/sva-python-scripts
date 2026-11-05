"""Bring the rigged black cat (maya/make_cat_rig.py) into Unreal.

Run in the Unreal editor after make_cat_rig.py. Imports export/fabcat/cat_rig.fbx as a skeletal
mesh (SK_Cat) and cat_walk.fbx / cat_idle.fbx as animations on its skeleton (A_Cat_Walk,
A_Cat_Idle), and gives it the Fab cat's own material. unreal/cat_walk.py then makes it walk.
"""
import unreal

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/export/fabcat/"
DIR = "/Game/Horror/Critters/Cat"
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def task(fbx, name, options):
    t = unreal.AssetImportTask()
    t.filename, t.destination_path, t.destination_name = ROOT + fbx, DIR, name
    t.automated, t.replace_existing, t.save = True, True, True
    t.options = options
    tools.import_asset_tasks([t])
    return list(t.imported_object_paths)


def main():
    lib.make_directory(DIR)
    ui = unreal.FbxImportUI()
    ui.import_mesh, ui.import_as_skeletal, ui.import_animations = True, True, False
    ui.import_materials, ui.import_textures = False, False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    ui.skeletal_mesh_import_data.set_editor_property("import_morph_targets", False)
    print("mesh", task("cat_rig.fbx", "SK_Cat", ui))
    mesh = unreal.load_asset(f"{DIR}/SK_Cat")
    skel = mesh.get_editor_property("skeleton")
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    catmat = next(a.get_asset() for a in reg.get_assets_by_path("/Game/Fab", recursive=True)
                  if str(a.asset_class_path.asset_name) == "MaterialInstanceConstant")
    mats = mesh.get_editor_property("materials")
    for m in mats:
        m.set_editor_property("material_interface", catmat)
    mesh.set_editor_property("materials", mats)
    lib.save_loaded_asset(mesh, False)
    for fbx, name in (("cat_walk.fbx", "A_Cat_Walk"), ("cat_idle.fbx", "A_Cat_Idle")):
        a = unreal.FbxImportUI()
        a.import_mesh, a.import_animations, a.import_as_skeletal = False, True, True
        a.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
        a.skeleton = skel
        a.import_materials, a.import_textures = False, False
        print(name, task(fbx, name, a))
    print("cat imported; skeleton", skel.get_name())


main()

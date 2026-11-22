"""Trees collide with their trunk only (user 2026-11-22: couldn't walk between trees that were far apart - each
tree collided with a shell round its whole crown, ~2-3 m out).

Run in the Unreal editor after unreal/trees.py and `mayapy maya/make_trunk_collision.py`. Safe to run again.
For each tree kind: imports export/trees/trunkcol_<name>.fbx (a plain trunk-sized cylinder) as
/Game/Horror/Trees/Collision/SM_trunkcol_<name>, removes the tree mesh's own simple collision, sets the cylinder as
its complex-collision mesh and makes it use complex collision as simple: you bump into the trunk and nothing else.
"""
import unreal

ROOT = "C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/"
PROPS = "/Game/Horror/Props"
DIR = "/Game/Horror/Trees/Collision"
TREES = ("tree_pine_A", "tree_pine_B", "tree_leafy_A", "tree_leafy_B", "tree_dead_C", "tree_dead_A", "tree_dead_B",
         "tree_dead_pine")

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
sme = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

for name in TREES:
    t = unreal.AssetImportTask()
    t.filename = ROOT + f"export/trees/trunkcol_{name}.fbx"
    t.destination_path, t.destination_name = DIR, f"SM_trunkcol_{name}"
    t.automated, t.save, t.replace_existing = True, True, True
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    ui.static_mesh_import_data.set_editor_property("auto_generate_collision", False)
    t.options = ui
    tools.import_asset_tasks([t])
    col = unreal.load_asset(f"{DIR}/SM_trunkcol_{name}")
    tree = unreal.load_asset(f"{PROPS}/{name}")
    before = sme.get_simple_collision_count(tree)
    sme.remove_collisions(tree)
    tree.set_editor_property("complex_collision_mesh", col)
    body = tree.get_editor_property("body_setup")
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    tree.set_editor_property("body_setup", body)
    lib.save_loaded_asset(tree, False)
    print(name, "simple shapes removed:", before, "-> trunk", col.get_bounding_box().max.x)

"""The forest floor: fallen leaves, pine needles, sticks and branches (maya/make_floor.py, placed
where tools/make_floor_layout.py says in export/floor.json), and the lookout tower's view: the
trees in it (tools/tower_view.py) are taken out and sawn stumps and brush piles left instead.

- leaf / needle patches: flat cards with the pictures from tools/make_litter.py on M_PS2_Leaves
  (the trees' leaf material: see-through between the leaves, both sides), no shadow, no collision
- sticks and branches share the trees' bark; you walk over them (no collision)
- stumps and brush piles you bump into
- patches aren't drawn past 35 m, sticks past 30 m (fog), stumps / piles / branches past 80 m

Run after trees.py (build_level.py). Safe to run again: the old floor is cleared first, and the
trees in the view are found by where they stand, so re-running import_scatter / fill_forest
(which put them back) and then this takes them out again.
"""
import json
import os
import sys

import unreal

ROOT = "C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
sys.path.insert(0, ROOT + "/tools")
from tower_view import in_view                                          # noqa: E402

DIR = "/Game/Horror/Floor"
TREES = "/Game/Horror/Trees"
SURFACE = "/Game/Horror/Materials/PS2/M_PS2_Surface"
TAG = "floor"
MESHES = ("litter_leaves_A", "litter_leaves_B", "litter_needles_A", "stick_A", "stick_B", "stick_C",
          "branch_A", "stump_cut", "slash_pile")
SOLID = ("stump_cut", "slash_pile")
DRAW = {"litter": 3500.0, "stick": 3000.0}                              # anything else: 8000

lib = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def import_texture(name):
    t = unreal.AssetImportTask()
    t.filename = f"{ROOT}/export/{name}.png"
    t.destination_path, t.destination_name = DIR, "T_" + name
    t.automated, t.replace_existing, t.save = True, True, True
    tools.import_asset_tasks([t])
    tex = unreal.load_asset(f"{DIR}/T_{name}")
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)   # exact cut-out
    tex.set_editor_property("compression_no_alpha", False)
    lib.save_loaded_asset(tex, False)
    return tex


def mi(name, parent, color, tex=None, tex_param="CardTex", size=None):
    path = f"{DIR}/{name}"
    m = unreal.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(
        name, DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(m, parent)
    MEL.set_material_instance_vector_parameter_value(m, "Color", unreal.LinearColor(*color, 1))
    if tex:
        MEL.set_material_instance_texture_parameter_value(m, tex_param, tex)
    if size:
        MEL.set_material_instance_scalar_parameter_value(m, "TexSize", size)
    lib.save_loaded_asset(m, False)
    return m


def materials():
    leaves = unreal.load_asset(TREES + "/M_PS2_Leaves")
    return {
        "litter_leaves_mat": mi("MI_litter_leaves_mat", leaves, (1.05, 1.0, 0.9), import_texture("litter_leaves")),
        "litter_needles_mat": mi("MI_litter_needles_mat", leaves, (1.0, 0.95, 0.85), import_texture("litter_needles")),
        "stump_top_mat": mi("MI_stump_top_mat", unreal.load_asset(SURFACE), (0.5, 0.4, 0.3),
                            unreal.load_asset("/Game/Horror/Textures/T_planks"), "Tex", 45.0),
        "tree_bark_mat": unreal.load_asset(TREES + "/MI_tree_bark_mat"),
        "tree_dead_needles_mat": unreal.load_asset(TREES + "/MI_tree_dead_needles_mat"),
    }


def import_mesh(name, mats):
    t = unreal.AssetImportTask()
    t.filename = f"{ROOT}/export/floor/{name}.fbx"
    t.destination_path, t.destination_name = DIR, "SM_" + name
    t.automated, t.replace_existing, t.save = True, True, True
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_materials", False)
    opts.set_editor_property("import_textures", False)
    opts.get_editor_property("static_mesh_import_data").set_editor_property("combine_meshes", True)
    t.options = opts
    tools.import_asset_tasks([t])
    mesh = unreal.load_asset(f"{DIR}/SM_{name}")
    nan = mesh.get_editor_property("nanite_settings")
    nan.set_editor_property("enabled", False)                          # Nanite crushed thin parts before
    mesh.set_editor_property("nanite_settings", nan)
    for i, s in enumerate(mesh.get_editor_property("static_materials")):
        slot = str(s.material_slot_name)
        for key, m in mats.items():
            if key in slot and m:
                mesh.set_material(i, m)
    unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).remove_lods(mesh)   # reduced LODs broke cut-outs
    lib.save_loaded_asset(mesh, False)
    return mesh


def cut_trees():
    """Take the trees standing in the tower's view out of the level."""
    gone = 0
    for a in actors.get_all_level_actors():
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if not (c and c.static_mesh and c.static_mesh.get_name().startswith("tree_")):
            continue
        p = a.get_actor_location()
        if in_view(p.x, p.y):
            actors.destroy_actor(a)
            gone += 1
    return gone


def main():
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG):
            actors.destroy_actor(a)
    gone = cut_trees()
    mats = materials()
    meshes = {n: import_mesh(n, mats) for n in MESHES}
    items = json.load(open(ROOT + "/export/floor.json"))["items"]
    with unreal.ScopedSlowTask(len(items), "Laying the forest floor") as task:
        task.make_dialog(True)
        for it in items:
            task.enter_progress_frame(1)
            name = it["mesh"]
            a = actors.spawn_actor_from_object(meshes[name], unreal.Vector(it["x"], it["y"], it["z"]),
                                               unreal.Rotator(0, 0, it["yaw"]))
            a.set_actor_scale3d(unreal.Vector(it["scale"], it["scale"], it["scale"]))
            a.tags = [TAG]
            a.set_folder_path("Floor/" + name.rsplit("_", 1)[0])
            c = a.static_mesh_component
            if name not in SOLID:
                c.set_collision_profile_name("NoCollision")
            c.set_cast_shadow(name in SOLID)
            c.set_editor_property("ld_max_draw_distance", next((v for k, v in DRAW.items() if name.startswith(k)), 8000.0))
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print(f"forest floor: {len(items)} pieces, {gone} trees cut for the tower view")


main()

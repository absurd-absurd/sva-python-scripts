"""Rebuild the Maya scatter in Unreal.

Run in the Unreal editor (Tools > Execute Python Script) after export_to_unreal.py in Maya.
Reads RESEARCH_PROJECT_1/export/scatter.json, imports each prop FBX into /Game/Horror/Props
(replacing older versions), then places one actor per scatter copy. Safe to run again:
it removes the previous scatter and the gray placeholder trunks first.

Maya is Y-up and Unreal is Z-up. Tested: a Maya point (x, y, z) lands at Unreal (x, z, y),
so Maya's Y and Z swap. A copy's whole matrix is converted the same way, which keeps
its rotation and scale (checked against a baked copy: same bounds to 0.001 cm).
"""
import json
import os

import unreal

EXPORT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/export/scatter.json"
PROPS_DIR = "/Game/Horror/Props"
TAG = "scatter"
NO_COLLISION = ("shrub",)          # props you can walk through

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def maya_to_unreal(m):
    """Maya world matrix (16 numbers, rows = X axis, Y axis, Z axis, position) -> unreal.Transform."""
    swap = lambda v: unreal.Vector(v[0], v[2], v[1])
    x_axis = swap(m[0:3])
    y_axis = swap(m[8:11])         # Maya's Z axis is Unreal's Y axis
    z_axis = swap(m[4:7])          # Maya's Y axis (up) is Unreal's Z axis
    position = swap(m[12:15])
    rotation = unreal.MathLibrary.make_rot_from_xz(x_axis, z_axis)
    scale = unreal.Vector(x_axis.length(), y_axis.length(), z_axis.length())
    return unreal.Transform(position, rotation, scale)


PS2_SURFACE = "/Game/Horror/Materials/PS2/M_PS2_Surface"
PS2_PROPS_DIR = "/Game/Horror/Materials/PS2/Props"


def ps2_materials(colors):
    """One instance of the PS2 surface material per Maya material, with the same color.
    Returns {} if ps2_look.py hasn't been run yet (the props keep their FBX materials)."""
    if not unreal.EditorAssetLibrary.does_asset_exist(PS2_SURFACE):
        return {}
    parent = unreal.load_asset(PS2_SURFACE)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    made = {}
    for name, rgb in colors.items():
        path = f"{PS2_PROPS_DIR}/MI_PS2_{name}"
        mi = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else             tools.create_asset(f"MI_PS2_{name}", PS2_PROPS_DIR, unreal.MaterialInstanceConstant,
                               unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property("parent", parent)
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
            mi, "Color", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1))
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        made[name] = mi
    return made


def import_props(props, colors):
    tasks = []
    for asset, info in props.items():
        t = unreal.AssetImportTask()
        t.filename = info["fbx"]
        t.destination_path = PROPS_DIR
        t.destination_name = asset
        t.automated = True
        t.replace_existing = True
        t.save = True
        tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    mats = ps2_materials(colors)
    meshes = {}
    for asset in props:
        mesh = unreal.load_asset(f"{PROPS_DIR}/{asset}")
        if not isinstance(mesh, unreal.StaticMesh):
            unreal.log_error(f"{asset}: import failed")
            continue
        # low-poly meshes: collide with the real triangles, so you can stand by a trunk
        # without bumping into an invisible box around the branches
        body = mesh.get_editor_property("body_setup")
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        mesh.set_editor_property("body_setup", body)
        mi = mats.get(props[asset]["material"])
        if mi:
            mesh.set_material(0, mi)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        meshes[asset] = mesh
    return meshes


def clear_old():
    removed = 0
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG) or a.get_actor_label().startswith("TempTree"):
            actors.destroy_actor(a)
            removed += 1
    return removed


def main():
    data = json.load(open(EXPORT))
    copies = data["copies"]
    with unreal.ScopedSlowTask(len(copies) + 2, "Importing the woods") as task:
        task.make_dialog(True)
        task.enter_progress_frame(1, "Importing props")
        meshes = import_props(data["props"], data.get("materials", {}))
        task.enter_progress_frame(1, "Removing the old scatter")
        removed = clear_old()
        made = 0
        for i, c in enumerate(copies):
            task.enter_progress_frame(1)
            mesh = meshes.get(c["asset"])
            if not mesh:
                continue
            xf = maya_to_unreal(c["matrix"])
            a = actors.spawn_actor_from_object(mesh, xf.translation, xf.rotation.rotator())
            a.set_actor_transform(xf, False, False)
            a.set_actor_label(f"{c['asset']}_{i}")
            a.set_folder_path(f"Scatter/{c['network']}")
            a.tags = [TAG]
            if c["asset"].startswith(NO_COLLISION):
                a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            made += 1
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    unreal.log(f"Woods imported: {made} copies of {len(meshes)} props (removed {removed} old actors)")
    print(f"Woods imported: {made} copies of {len(meshes)} props (removed {removed} old actors)")


main()

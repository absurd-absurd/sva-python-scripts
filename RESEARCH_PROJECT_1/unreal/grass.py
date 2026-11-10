"""Grass you can walk through: the blade patches from maya/make_grass.py, placed where
tools/make_grass_layout.py says (export/grass.json), with a material that moves every blade:
- wind: the whole field sways in slow gusts that roll across it, plus a quicker flutter
- you: blades lean away from you and press down as you walk through them, then spring back
  (MPC_Horror.PlayerPos, which the HUD updates every frame, is where you are)
The roots stay put: the movement grows with how high up the blade the vertex is.
Grass beyond 45 m isn't drawn (the fog hides it), so it stays cheap.

Run after import_sets.py (build_level.py). Safe to run again.
"""
import json
import unreal

ROOT = "C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
DIR = "/Game/Horror/Grass"
SURFACE = "/Game/Horror/Materials/PS2/M_PS2_Surface"
GRASS = DIR + "/M_PS2_Grass"
TAG = "grass"
MESHES = ("grass_dense_A", "grass_dense_B", "grass_sparse_A", "grass_sparse_B", "grass_small_A", "grass_small_B")
LOOK = {"grass_green_mat": ((0.1, 0.14, 0.05), "T_grass", 35.0),
        "grass_dry_mat": ((0.17, 0.15, 0.08), "T_grass", 35.0)}
DRAW = 4500.0                    # cm

GRASS_HLSL = """
// Every blade vertex: wind sway + the player pushing through. WPos.z = height above the ground
// (the ground is at z 0..2), so roots (z 0) never move and tips move most.
float h = saturate(WPos.z / 55.0);
h *= h;
float2 dir = normalize(float2(0.8, 0.5));
float ph = dot(WPos.xy, float2(0.0021, 0.0013));
float gust = 0.55 + 0.45 * sin(T * 0.37 + ph * 0.8);                 // slow gusts rolling across
float sway = sin(T * 1.9 + ph * 6.0) * 0.6 + sin(T * 3.7 + WPos.x * 0.05 + WPos.y * 0.03) * 0.25;
float3 o = float3(dir * (sway + 0.6) * gust * Wind * h, 0);
float2 d = WPos.xy - PPos.xy;
float dist = length(d);
float near = saturate(1.0 - dist / Radius);
near = near * near * (3.0 - 2.0 * near);
if (PPos.z - WPos.z < 400.0) {                                       // only when you're down on the ground
    o.xy += (d / max(dist, 1.0)) * near * Push * h;
    o.z -= near * h * Push * 0.45;
}
return o;
"""

lib = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()


def _custom_nodes(m):
    return [e for e in unreal.ObjectIterator(unreal.MaterialExpressionCustom) if e.get_outer() == m]


def _expr(m, cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e


def grass_material():
    """M_PS2_Grass: a copy of M_PS2_Surface (its World Position Offset wire to the custom node is
    already connected; Python can't make that wire), the node's code swapped for GRASS_HLSL."""
    if lib.does_asset_exist(GRASS):
        m = unreal.load_asset(GRASS)
        node = [c for c in _custom_nodes(m) if "PPos" in [str(i.get_editor_property("input_name")) for i in c.get_editor_property("inputs")]][0]
        node.set_editor_property("code", GRASS_HLSL)                    # just refresh the code
        MEL.recompile_material(m)
        lib.save_loaded_asset(m, False)
        return m
    m = lib.duplicate_asset(SURFACE, GRASS)
    node = [c for c in _custom_nodes(m) if "Amount" in [str(i.get_editor_property("input_name")) for i in c.get_editor_property("inputs")]][0]
    pins = list(node.get_editor_property("inputs"))
    for n in ("WPos", "T", "PPos", "Wind", "Push", "Radius"):
        p = unreal.CustomInput()
        p.set_editor_property("input_name", n)
        pins.append(p)
    node.set_editor_property("inputs", pins)
    node.set_editor_property("code", GRASS_HLSL)
    wpos = _expr(m, unreal.MaterialExpressionWorldPosition, -1100, 300,
                 world_position_shader_offset=unreal.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    t = _expr(m, unreal.MaterialExpressionTime, -1100, 380)
    ppos = _expr(m, unreal.MaterialExpressionCollectionParameter, -1100, 450,
                 collection=unreal.load_asset("/Game/Horror/Materials/MPC_Horror"), parameter_name="PlayerPos")
    MEL.connect_material_expressions(wpos, "", node, "WPos")
    MEL.connect_material_expressions(t, "", node, "T")
    MEL.connect_material_expressions(ppos, "", node, "PPos")
    for i, (n, v) in enumerate((("Wind", 7.0), ("Push", 38.0), ("Radius", 95.0))):
        sp = _expr(m, unreal.MaterialExpressionScalarParameter, -1100, 520 + i * 80, parameter_name=n, default_value=v)
        MEL.connect_material_expressions(sp, "", node, n)
    m.set_editor_property("two_sided", True)                           # a blade is one sheet, seen from both sides
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


def instances(parent):
    out = {}
    for slot, (rgb, tex, size) in LOOK.items():
        path = f"{DIR}/MI_{slot}"
        mi = unreal.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(
            f"MI_{slot}", DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, parent)
        MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*rgb, 1))
        t = unreal.load_asset("/Game/Horror/Textures/" + tex)
        if t:
            MEL.set_material_instance_texture_parameter_value(mi, "Tex", t)
            MEL.set_material_instance_scalar_parameter_value(mi, "TexSize", size)
        lib.save_loaded_asset(mi, False)
        out[slot] = mi
    return out


def import_mesh(name, mis):
    t = unreal.AssetImportTask()
    t.filename = f"{ROOT}/export/{name}.fbx"
    t.destination_path, t.destination_name = DIR, f"SM_{name}"
    t.automated, t.replace_existing, t.save = True, True, True
    tools.import_asset_tasks([t])
    mesh = unreal.load_asset(f"{DIR}/SM_{name}")
    nanite = mesh.get_editor_property("nanite_settings")
    nanite.set_editor_property("enabled", False)
    mesh.set_editor_property("nanite_settings", nanite)
    for i, sm in enumerate(mesh.get_editor_property("static_materials")):
        slot = str(sm.material_slot_name)
        for key, mi in mis.items():
            if key in slot:
                mesh.set_material(i, mi)
    lib.save_loaded_asset(mesh, False)
    return mesh


def main():
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG):
            actors.destroy_actor(a)
    mis = instances(grass_material())
    meshes = {n: import_mesh(n, mis) for n in MESHES}
    items = json.load(open(ROOT + "/export/grass.json"))
    with unreal.ScopedSlowTask(len(items), "Growing grass") as task:
        task.make_dialog(True)
        for it in items:
            task.enter_progress_frame(1)
            a = actors.spawn_actor_from_object(meshes[it["mesh"]], unreal.Vector(it["x"], it["y"], it.get("z", 0)), unreal.Rotator(0, 0, it["yaw"]))
            c = a.static_mesh_component
            c.set_collision_profile_name("NoCollision")                # you walk straight through it
            c.set_cast_shadow(False)
            c.set_editor_property("ld_max_draw_distance", DRAW)
            a.set_folder_path("Grass")
            a.tags = [TAG]
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print("grass:", len(items), "patches")


main()

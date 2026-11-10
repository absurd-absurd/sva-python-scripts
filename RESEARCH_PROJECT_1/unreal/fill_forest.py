"""Place the forest fill (export/fill.json from tools/make_fill.py) and the invisible walls at the
edges of the map. Uses the same prop meshes the Maya scatter brought in (/Game/Horror/Props).

Run after import_scatter.py (build_level.py). Safe to run again: it clears its own actors first.
"""
import json
import unreal

ROOT = "C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
PROPS = "/Game/Horror/Props/"
TAG = "fill"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def main():
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG):
            actors.destroy_actor(a)
    data = json.load(open(ROOT + "/export/fill.json"))
    meshes = {}
    placed = 0
    with unreal.ScopedSlowTask(len(data["items"]), "Planting the forest") as task:
        task.make_dialog(True)
        for it in data["items"]:
            task.enter_progress_frame(1)
            name = it["asset"]
            if name not in meshes:
                meshes[name] = unreal.load_asset(PROPS + name)
            mesh = meshes[name]
            if not mesh:
                continue
            a = actors.spawn_actor_from_object(mesh, unreal.Vector(it["x"], it["y"], 0), unreal.Rotator(0, 0, it["yaw"]))
            a.set_actor_scale3d(unreal.Vector(it["scale"], it["scale"], it["scale"]))
            if name.startswith(("bush", "shrub")):                      # you push through small plants
                a.static_mesh_component.set_collision_profile_name("NoCollision")
            a.set_folder_path("Fill/" + ("Trees" if name.startswith("tree") else "Ground"))
            a.tags = [TAG]
            placed += 1
    # the woods from the Maya scatter tool too: no ferns (bush_A; you didn't like their shape),
    # and you push through their dead shrubs
    for a in actors.get_all_level_actors():
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if c and c.static_mesh and c.static_mesh.get_name() == "bush_A":
            actors.destroy_actor(a)
        elif c and c.static_mesh and c.static_mesh.get_name().startswith("shrub"):
            c.set_collision_profile_name("NoCollision")
    # invisible walls just behind the outermost trees (the lake has its own, from make_lake.py)
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    E, S = data["edge"], data["south"]
    for name, cx, cy, sx, sy in (("Wall_West", -E - 100, 2100, 200, 2 * (S + 14000) / 2.0 + 400),
                                 ("Wall_East", E + 100, 2100, 200, 2 * (S + 14000) / 2.0 + 400),
                                 ("Wall_South", 0, -S - 100, 2 * E + 400, 200)):
        w = actors.spawn_actor_from_object(cube, unreal.Vector(cx, cy, 500))
        w.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, 12))
        w.set_actor_hidden_in_game(True)
        w.static_mesh_component.set_editor_property("visible", False)
        w.static_mesh_component.set_cast_shadow(False)
        w.set_actor_label(name)
        w.set_folder_path("Fill/Walls")
        w.tags = [TAG]
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print("forest fill:", placed, "pieces + 3 walls")


main()

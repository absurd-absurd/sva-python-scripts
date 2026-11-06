"""Put your car (the Fab "Low-Poly Classic Car (Free)" you added) in the stall in front of Room 104,
nose toward the motel, wheels on the asphalt, with collision so you can't walk through it.

Run in the Unreal editor after import_sets.py (build_level.py step). Safe to run again.
The model itself lives in Content/Fab (your download); it isn't part of this repo.
"""
import unreal

SPOT = (-725, -2120)          # stall centre (where the old Maya car stood)
LIFT = 106                    # its pivot is mid-body: 103 cm above the wheels' bottom, + the lot (3)
YAW = -90                     # its front is at local -x: this turns the nose to +y (the motel)
TAG = "fabcar"

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
reg = unreal.AssetRegistryHelpers.get_asset_registry()


def main():
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG) or a.get_actor_label() == "CARTEST":
            actors.destroy_actor(a)
    meshes = [a.get_asset() for a in reg.get_assets_by_path("/Game/Fab", recursive=True)
              if str(a.asset_class_path.asset_name) == "StaticMesh" and "car" in str(a.package_name).lower()]
    if not meshes:
        print("no Fab car found under /Game/Fab")
        return
    mesh = meshes[0]
    body = mesh.get_editor_property("body_setup")
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    mesh.set_editor_property("body_setup", body)
    nan = mesh.get_editor_property("nanite_settings")
    nan.set_editor_property("enabled", False)
    mesh.set_editor_property("nanite_settings", nan)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    b = mesh.get_bounding_box()
    cx, cy = (b.min.x + b.max.x) / 2.0, (b.min.y + b.max.y) / 2.0      # centre the car on the stall
    # yaw -90 takes local (x, y) to world (y, -x)
    at = unreal.Vector(SPOT[0] - cy, SPOT[1] + cx, LIFT)
    car = actors.spawn_actor_from_object(mesh, at, unreal.Rotator(0, 0, YAW))
    car.set_actor_label("PlayerCar")
    car.set_folder_path("Sets")
    car.tags = [TAG]
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print("car placed:", mesh.get_name(), at)


main()

"""The abandoned car in the woods: the same Fab "Low-Poly Classic Car" as your car in the lot,
but black and rusted through, its chrome rusted, sunk into the ground nose-down and
leaning, at the "car" clearing of layout.json (the weeds, vines, branch and leaves around it come
from maya/make_trail.py). Its windows stay the model's dark glass (you can't see in).

Run after import_sets.py and place_car.py (build_level.py). Safe to run again.
"""
import json
import math
import unreal

ROOT = "C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
TAG = "fabwreck"
YAW = -115                  # nose toward the old car's heading (the Fab car's front is local -x)
SINK = 14                   # sunk into the soft ground
LIFT = 103 - SINK           # pivot is 103 cm above the bottom of the wheels
PAINT = "/Game/Horror/Materials/PS2/Props/MI_PS2_wreck_paint"
SRC = "/Game/Horror/Materials/PS2/Props/MI_PS2_rust_body_mat"
RUST = "/Game/Horror/Materials/PS2/Props/MI_PS2_rusty_tool_mat"
GRIME = "/Game/Horror/Materials/PS2/Props/MI_PS2_mud_print_mat"
TINT = "/Game/Horror/Materials/PS2/Props/MI_PS2_wreck_glass"          # dark tinted glass
SURFACE = "/Game/Horror/Materials/PS2/M_PS2_Surface"   # matte: the gloss one flared white in the flashlight
# which of the Fab car's material slots get what (found by colour-testing them): 0 the blue
# paint, 2/3/4 the windows (dark tint, can't see in), 9/13 the rims (rusted), 11/12 the tyres
# (dark matte: the model's own flared white), 1/5/6/10 the trim (dark grey, barely there: white was
# too bright, rust read gold); the lights (7/8) keep the model's own
TRIM = "/Game/Horror/Materials/PS2/Props/MI_PS2_wreck_trim"
OVERRIDE = {0: PAINT, 2: TINT, 3: TINT, 4: TINT, 11: TINT, 12: TINT, 9: RUST, 13: RUST,
            1: TRIM, 5: TRIM, 6: TRIM, 10: TRIM}

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary


def paint():
    if not lib.does_asset_exist(PAINT):
        lib.duplicate_asset(SRC, PAINT)
    mi = unreal.load_asset(PAINT)
    mel.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(0.014, 0.014, 0.016, 1))   # black, rust showing through
    lib.save_loaded_asset(mi, False)
    return mi


def matte(path, rgb):
    """A plain matte material instance of M_PS2_Surface in one colour (made once, recoloured each run)."""
    if not lib.does_asset_exist(path):
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        folder, name = path.rsplit("/", 1)
        tools.create_asset(name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi = unreal.load_asset(path)
    mel.set_material_instance_parent(mi, unreal.load_asset(SURFACE))
    mel.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*rgb, 1))
    lib.save_loaded_asset(mi, False)


def glass():
    matte(TINT, (0.006, 0.007, 0.008))
    matte(TRIM, (0.011, 0.011, 0.012))           # just off black: barely shows on the black paint


def main():
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG):
            actors.destroy_actor(a)
    car = [a for a in actors.get_all_level_actors() if a.actor_has_tag("fabcar")]
    if not car:
        print("place_car.py first")
        return
    mesh = car[0].static_mesh_component.static_mesh
    clear = {c["name"]: c for c in json.load(open(ROOT + "/layout.json"))["clearings"]}["car"]
    b = mesh.get_bounding_box()
    cx, cy = (b.min.x + b.max.x) / 2.0, (b.min.y + b.max.y) / 2.0
    a_ = math.radians(YAW)
    ox, oy = cx * math.cos(a_) - cy * math.sin(a_), cx * math.sin(a_) + cy * math.cos(a_)
    at = unreal.Vector(clear["x"] - ox, clear["y"] - oy, LIFT)
    wreck = actors.spawn_actor_from_object(mesh, at, unreal.Rotator(2.0, -2.5, YAW))     # roll, pitch, yaw
    wreck.set_actor_label("WreckCar")
    wreck.set_folder_path("Sets")
    wreck.tags = [TAG]
    paint()
    glass()
    comp = wreck.static_mesh_component
    for slot, path in OVERRIDE.items():
        comp.set_material(slot, unreal.load_asset(path))
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print("wreck placed at", at)


main()

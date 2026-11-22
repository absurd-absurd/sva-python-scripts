"""The final shot (STORY.md): a year later, Bug's MISSING poster on the payphone in the motel lot.

Run in the Unreal editor after tools/make_photos.py (export/pic_missing_bug.png). Makes:
  T_pic_missing_bug + MI_PS2_pic_missing_bug   the poster picture on M_PS2_Picture
  /Game/Horror/Interact/BP_FinalShot           an actor with a Camera and the Poster (a plane on the
                                                payphone's side panel); placed once in the level, HIDDEN
The HUD's ending (tools/make_interact_nodes.py) shows it and looks through its camera.
"""
import math

import unreal

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/"
lib = unreal.EditorAssetLibrary
BPL = unreal.BlueprintEditorLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

PHONE = (2930.0, -1830.0)                    # maya/make_motel.py payphone(2930, -1830): body x +-30, y +-20, z 100..186
POSTER_AT = (PHONE[0] + 31.2, PHONE[1], 146.0)   # on the +x side panel, facing +x
POSTER_SIZE = (46.0, 34.5)                   # height, width (cm): the 150 x 200 picture
CAM_AT = (POSTER_AT[0] + 78.0, PHONE[1] - 24.0, 150.0)   # close in front of the poster, a little to the side
# (2026-11-22, user: the poster was "blurry and hard to read" from 2 m away at a slant; was (3125, -1905, 156))


def texture():
    t = unreal.AssetImportTask()
    t.filename = ROOT + "export/pic_missing_bug_payphone.png"      # sharp, turned to stand upright on the plane
    t.destination_path, t.destination_name = "/Game/Horror/Textures/Pictures", "T_pic_missing_bug"
    t.automated, t.save, t.replace_existing = True, True, True
    tools.import_asset_tasks([t])
    tex = unreal.load_asset("/Game/Horror/Textures/Pictures/T_pic_missing_bug")
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    lib.save_loaded_asset(tex, False)
    path = "/Game/Horror/Materials/PS2/Props/MI_PS2_pic_missing_bug"
    mi = unreal.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(
        "MI_PS2_pic_missing_bug", path.rsplit("/", 1)[0], unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", unreal.load_asset("/Game/Horror/Materials/PS2/M_PS2_Picture"))
    MEL.set_material_instance_texture_parameter_value(mi, "Tex", tex)
    MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(1, 1, 1, 1))
    lib.save_loaded_asset(mi, False)
    return mi


def blueprint(mi):
    path = "/Game/Horror/Interact/BP_FinalShot"
    if lib.does_asset_exist(path):
        bp = unreal.load_asset(path)
    else:
        bp = BPL.create_blueprint_asset_with_parent(path, unreal.Actor)
        BPL.remove_unused_nodes(bp)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    L = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    names = {str(L.get_variable_name(L.get_data(h))): h for h in handles}

    def add(cls, name):
        if name in names:
            return L.get_object(L.get_data(names[name]))
        h, _ = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=cls, blueprint_context=bp))
        sub.rename_subobject(h, name)
        return L.get_object(L.get_data(h))

    # the actor sits at the poster; the camera is offset to where you stand in the lot
    poster = add(unreal.StaticMeshComponent, "Poster")
    poster.set_editor_property("static_mesh", unreal.load_asset("/Engine/BasicShapes/Plane"))
    poster.set_material(0, mi)
    poster.set_editor_property("relative_rotation", unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0))   # stand up, face +x
    poster.set_editor_property("relative_scale3d", unreal.Vector(POSTER_SIZE[0] / 100, POSTER_SIZE[1] / 100, 1))
    poster.set_collision_profile_name("NoCollision")
    cam = add(unreal.CameraComponent, "Camera")
    off = unreal.Vector(CAM_AT[0] - POSTER_AT[0], CAM_AT[1] - POSTER_AT[1], CAM_AT[2] - POSTER_AT[2])
    cam.set_editor_property("relative_location", off)
    yaw = math.degrees(math.atan2(-off.y, -off.x))
    pitch = math.degrees(math.atan2(-off.z, math.hypot(off.x, off.y)))
    cam.set_editor_property("relative_rotation", unreal.Rotator(roll=0.0, pitch=pitch, yaw=yaw))
    cam.set_editor_property("field_of_view", 60.0)
    BPL.compile_blueprint(bp)
    lib.save_loaded_asset(bp, False)
    return bp


def place(bp):
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if a.actor_has_tag("final_shot"):
            actors.destroy_actor(a)
    a = actors.spawn_actor_from_class(BPL.generated_class(bp), unreal.Vector(*POSTER_AT), unreal.Rotator(0, 0, 0))
    a.set_actor_label("FinalShot")
    a.tags = ["final_shot"]
    a.set_actor_hidden_in_game(True)          # the poster isn't there until a year later
    return a


mi = texture()
bp = blueprint(mi)
a = place(bp)
print("final shot placed", a.get_actor_location())

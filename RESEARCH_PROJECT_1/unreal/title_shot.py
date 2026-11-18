"""The title screen's view and picture (user, 2026-11-17: lake background, lettering 3B "thin").

Run in the Unreal editor after tools/make_title.py thin (export/title.png). Makes:
  T_Title                         the MARROW lettering (see-through round the letters), a UI texture
  /Game/Horror/Interact/BP_TitleShot   an actor with just a Camera, placed at the end of the dock looking
                                  out over Black Hollow Lake into the fog; the HUD looks through it on the title
                                  screen (tools/make_interact_nodes.py) and goes back to the player on Start
Also adds the menu's input actions: IA_Controls (C), IA_Quit (Q).
"""
import unreal

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/"
lib = unreal.EditorAssetLibrary
BPL = unreal.BlueprintEditorLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
CAM_AT, CAM_ROT = (1500.0, 14150.0, 260.0), (-4.0, 90.0)          # pitch, yaw: down the dock into the fog
INPUT_DIR = "/Game/FirstPerson/Input/Actions"


def texture():
    t = unreal.AssetImportTask()
    t.filename = ROOT + "export/title.png"
    t.destination_path, t.destination_name = "/Game/Horror/UI", "T_Title"
    t.automated, t.save, t.replace_existing = True, True, True
    tools.import_asset_tasks([t])
    tex = unreal.load_asset("/Game/Horror/UI/T_Title")
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property("never_stream", True)
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    lib.save_loaded_asset(tex, False)


def vignette():
    t = unreal.AssetImportTask()
    t.filename = ROOT + "export/title_vignette.png"
    t.destination_path, t.destination_name = "/Game/Horror/UI", "T_TitleVignette"
    t.automated, t.save, t.replace_existing = True, True, True
    tools.import_asset_tasks([t])
    tex = unreal.load_asset("/Game/Horror/UI/T_TitleVignette")
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property("never_stream", True)
    lib.save_loaded_asset(tex, False)


def camera_actor():
    path = "/Game/Horror/Interact/BP_TitleShot"
    if lib.does_asset_exist(path):
        bp = unreal.load_asset(path)
    else:
        bp = BPL.create_blueprint_asset_with_parent(path, unreal.Actor)
        BPL.remove_unused_nodes(bp)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    L = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    names = {str(L.get_variable_name(L.get_data(h))) for h in handles}
    if "Camera" not in names:
        h, _ = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=unreal.CameraComponent,
                                                                  blueprint_context=bp))
        sub.rename_subobject(h, "Camera")
    BPL.compile_blueprint(bp)
    lib.save_loaded_asset(bp, False)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if a.actor_has_tag("title_shot"):
            actors.destroy_actor(a)
    a = actors.spawn_actor_from_class(BPL.generated_class(bp), unreal.Vector(*CAM_AT),
                                      unreal.Rotator(roll=0.0, pitch=CAM_ROT[0], yaw=CAM_ROT[1]))
    a.set_actor_label("TitleShot")
    a.tags = ["title_shot"]
    cam = a.get_components_by_class(unreal.CameraComponent)[0]
    cam.set_editor_property("field_of_view", 70.0)
    return a


def input_action(name, keys):
    path = f"{INPUT_DIR}/{name}"
    ia = unreal.load_asset(path) if lib.does_asset_exist(path) else \
        tools.create_asset(name, INPUT_DIR, unreal.InputAction, unreal.InputAction_Factory())
    ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
    ia.set_editor_property("trigger_when_paused", True)
    lib.save_loaded_asset(ia, False)
    imc = unreal.load_asset("/Game/FirstPerson/Input/IMC_Default")
    have = {(m.action.get_name() if m.action else "", str(m.key.get_editor_property("key_name"))) for m in imc.get_editor_property("mappings")}
    for key in keys:
        if (name, key) not in have:
            k = unreal.Key()
            k.set_editor_property("key_name", key)
            imc.map_key(ia, k)
    lib.save_loaded_asset(imc, False)


texture()
vignette()
camera_actor()
input_action("IA_Controls", ["C"])
input_action("IA_Quit", ["Q"])
input_action("IA_Pause", ["Escape", "P"])          # P too: in the editor Esc stops play before the game sees it
print("title screen pieces ready")

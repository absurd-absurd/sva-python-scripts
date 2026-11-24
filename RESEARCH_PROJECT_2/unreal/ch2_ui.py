"""MARROW Chapter 2: what BP_Ch2HUD's logic (tools/make_ch2_hud.py) needs in the Lakebed map.

Run in the Unreal editor with the Lakebed map open, after lakebed_level.py and place_clues2.py.
Safe to run again.
  - T_Ch2_Card: the card after the opening text (export/ch2_card.png, Mom's MISSING poster)
  - BP_Ch2HUD defaults: the opening text (clues.json, minus its last line: the card), title screen on
  - BP_TitleShot placed under the dock looking north (the HUD pushes it up the gully on the title screen)
  - BP_FinalShot placed high above the lake, hidden, showing the "i miss you bug" postcard close up
    (Chapter 1's export/postcard_back.png): the ending's last shot
  - the Lakebed's game mode uses BP_Ch2HUD
"""
import json
import math
import textwrap

import unreal

RP1 = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
RP2 = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_2"
lib = unreal.EditorAssetLibrary
BPL = unreal.BlueprintEditorLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
TAG = "ch2ui"
FINAL_AT = None


def texture(png, name, ui=True):
    t = unreal.AssetImportTask()
    t.filename, t.destination_path, t.destination_name = png, "/Game/Chapter2/UI", name
    t.automated, t.save, t.replace_existing = True, True, True
    tools.import_asset_tasks([t])
    tex = unreal.load_asset(f"/Game/Chapter2/UI/{name}")
    if ui:                                   # drawn by the HUD: sharp, no mipmaps (like Chapter 1's T_Paper_*)
        tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    lib.save_loaded_asset(tex, False)
    return tex


def hud_defaults():
    txt = json.load(open(f"{RP2}/clues.json", encoding="utf-8"))["game_text"]["opening"].rsplit("\n\n", 1)[0]
    opening = "\n".join(textwrap.fill(p, 44) if p else "" for p in txt.split("\n"))
    hud = unreal.load_asset("/Game/Chapter2/Blueprints/BP_Ch2HUD")
    cdo = unreal.get_default_object(BPL.generated_class(hud))
    cdo.set_editor_property("OpeningText", opening)
    cdo.set_editor_property("Title", True)
    cdo.set_editor_property("Opening", True)
    BPL.compile_blueprint(hud)
    lib.save_loaded_asset(hud, False)
    gm = unreal.load_asset("/Game/Chapter2/Blueprints/BP_Ch2GameMode")
    unreal.get_default_object(BPL.generated_class(gm)).set_editor_property("hud_class", BPL.generated_class(hud))
    BPL.compile_blueprint(gm)
    lib.save_loaded_asset(gm, False)


def place_shots(start):
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG):
            actors.destroy_actor(a)
    title_cls = BPL.generated_class(unreal.load_asset("/Game/Horror/Interact/BP_TitleShot"))
    t = actors.spawn_actor_from_class(title_cls, unreal.Vector(start[0], start[1] - 500, start[2] + 60),
                                      unreal.Rotator(roll=0.0, pitch=4.0, yaw=90.0))
    t.set_actor_label("TitleShot")
    t.tags = [TAG]
    # the final shot: the postcard, close up, far above the water (no murk up there)
    tex = texture(f"{RP1}/export/postcard_back.png", "T_Ch2_Postcard", ui=False)
    path = "/Game/Chapter2/Materials/MI_Ch2_Postcard"
    mi = unreal.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(
        "MI_Ch2_Postcard", "/Game/Chapter2/Materials", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", unreal.load_asset("/Game/Horror/Materials/PS2/M_PS2_Picture"))
    MEL.set_material_instance_texture_parameter_value(mi, "Tex", tex)
    MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(1, 1, 1, 1))
    lib.save_loaded_asset(mi, False)
    final_cls = BPL.generated_class(unreal.load_asset("/Game/Horror/Interact/BP_FinalShot"))
    f = actors.spawn_actor_from_class(final_cls, unreal.Vector(start[0], 0, 30000), unreal.Rotator(0, 0, 0))
    f.set_actor_label("FinalShot_Postcard")
    f.tags = [TAG]
    f.set_actor_hidden_in_game(True)
    poster = [c for c in f.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith("Poster")][0]
    poster.set_material(0, mi)
    poster.set_relative_scale3d(unreal.Vector(0.40, 0.60, 1))          # landscape, 3:2 like the card
    cam = f.get_components_by_class(unreal.CameraComponent)[0]
    off = unreal.Vector(70.0, -8.0, 4.0)                               # close in front, a touch to the side
    cam.set_relative_location(off, False, True)
    cam.set_relative_rotation(unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(-off.z, math.hypot(off.x, off.y))),
                                             yaw=math.degrees(math.atan2(-off.y, -off.x))), False, True)


def main():
    start = json.load(open(f"{RP2}/export/sets_lakebed.json"))["start"]
    texture(f"{RP2}/export/ch2_card.png", "T_Ch2_Card")
    hud_defaults()
    place_shots(start)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print("Chapter 2 UI ready")


main()

"""MARROW Chapter 2: the heavy walk on the lakebed. Run in the Unreal editor with the Lakebed map
open, after lakebed_level.py. Safe to run again.

BP_Ch2Character is a CHILD of Chapter 1's BP_FirstPersonCharacter, so the flashlight, HUD,
reading and journal all still work; only its movement numbers differ (slow to start, slow to
stop, a slow floaty hop). BP_Ch2GameMode (child of Chapter 1's game mode) spawns it, and only
the Lakebed map uses that game mode (World Settings > GameMode Override), so Chapter 1 is untouched.
"""
import unreal

CH2 = "/Game/Chapter2"
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
BPL = unreal.BlueprintEditorLibrary

MOVE = {
    "max_walk_speed": 170.0,                 # water drags at you (Chapter 1 walks much faster)
    "max_acceleration": 260.0,               # slow to get going
    "braking_deceleration_walking": 220.0,   # and slow to stop
    "ground_friction": 2.0,
    "jump_z_velocity": 260.0,                # a slow, floaty hop
    "gravity_scale": 0.35,
    "air_control": 0.15,
}


def child_blueprint(name, parent_path):
    path = f"{CH2}/Blueprints/{name}"
    if lib.does_asset_exist(path):
        return unreal.load_asset(path)
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.load_asset(parent_path).generated_class())
    bp = tools.create_asset(name, f"{CH2}/Blueprints", unreal.Blueprint, factory)
    BPL.compile_blueprint(bp)            # compile once before touching its defaults
    lib.save_loaded_asset(bp, False)
    return bp


def main():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if "Lakebed" not in world.get_path_name():
        raise RuntimeError("Open the Lakebed map first")
    char = child_blueprint("BP_Ch2Character", "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter")
    move = unreal.get_default_object(BPL.generated_class(char)).get_editor_property("character_movement")
    for k, v in MOVE.items():
        move.set_editor_property(k, v)
    BPL.compile_blueprint(char)
    lib.save_loaded_asset(char, False)
    gm = child_blueprint("BP_Ch2GameMode", "/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode")
    gm_cdo = unreal.get_default_object(BPL.generated_class(gm))
    gm_cdo.set_editor_property("default_pawn_class", BPL.generated_class(char))
    # plain HUD for now: Chapter 1's BP_HorrorHUD runs the title screen and looks for Chapter 1
    # actors every frame ("Accessed None" errors, dark screen); Chapter 2 needs its own
    gm_cdo.set_editor_property("hud_class", unreal.HUD.static_class())
    BPL.compile_blueprint(gm)
    lib.save_loaded_asset(gm, False)
    world.get_world_settings().set_editor_property("default_game_mode", BPL.generated_class(gm))
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print("Heavy walk set:", MOVE)


main()

"""The dock goes quiet (user 2026-11-22: "when we get on the dock all the sound should go quiet minus the rattle").

Run in the Unreal editor after place_sounds.py. Safe to run again.
  /Game/Horror/Audio/SC_Ambience   a sound class for everything that should fall silent on the dock: the music, the
                                   wind, the insects, the lake and the footsteps
  /Game/Horror/Audio/MIX_Dock      a sound mix that turns SC_Ambience down to nothing over 2 s
BP_HorrorHUD pushes MIX_Dock the first time you step onto the dock after the boathouse note, pops it for the
one-year-later shot, and clears it when the level starts. The rattle (the growl), paper and keys stay out of it.
"""
import unreal

DIR = "/Game/Horror/Audio"
QUIET = ["S_rec_music_loop", "S_wind_loop", "S_rec_bugs_loop", "S_rec_lake_rec_loop"] + \
        [f"S_rec_step_{s}_{k}" for s in ("grass", "wood") for k in range(1, 5)]
FADE = 2.0

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary


def make(name, cls, factory):
    path = f"{DIR}/{name}"
    return unreal.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(name, DIR, cls, factory)


sc = make("SC_Ambience", unreal.SoundClass, unreal.SoundClassFactory())
lib.save_loaded_asset(sc, False)
for n in QUIET:
    s = unreal.load_asset(f"{DIR}/{n}")
    s.set_editor_property("sound_class_object", sc)
    lib.save_loaded_asset(s, False)
mix = make("MIX_Dock", unreal.SoundMix, unreal.SoundMixFactory())
adj = unreal.SoundClassAdjuster()
adj.set_editor_property("sound_class_object", sc)
adj.set_editor_property("volume_adjuster", 0.0)
adj.set_editor_property("apply_to_children", True)
mix.set_editor_property("sound_class_effects", [adj])
mix.set_editor_property("fade_in_time", FADE)
mix.set_editor_property("fade_out_time", 1.0)
lib.save_loaded_asset(mix, False)
print("SC_Ambience on", len(QUIET), "sounds; MIX_Dock ready")

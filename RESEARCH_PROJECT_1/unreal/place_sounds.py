"""Sound in the level (2026-11-22, first pass): import the sounds from tools/make_sounds.py and place the ambience.

Run in the Unreal editor after `python tools/make_sounds.py` (export/sounds/*.wav). Safe to run again.
  /Game/Horror/Audio/S_<name>     every export/sounds/*.wav as a SoundWave (the *_loop ones set to loop)
  snd_wind                        the wind, everywhere, not placed in space (2D), quiet under everything
  snd_lake_<k>                    the waves, placed along the shore, heard only near the water (attenuation)
After this, run unreal/sound_mix.py (the dock's quiet: it tags the ambience sounds with SC_Ambience).
The flashlight click is played by BP_HorrorHUD when the light is switched (tools/make_interact_nodes.py).
The drone, the rattle and the warp sting are imported but not placed yet (the user said they "don't work").
"""
import glob
import os
import unreal

ROOT = "C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/"
DIR = "/Game/Horror/Audio"
TAG = "sound"
WIND_VOLUME = 0.2          # 0.35 was "a little loud" (user 2026-11-22)
LAKE_VOLUME = 0.9
BUGS_VOLUME = 0.25         # night insects, 2D, under everything
# the music, the car, the growl, the warp bass, paper, keys, door and footsteps are played by BP_HorrorHUD
# (tools/make_interact_nodes.py SND / VOL); its TitleMusic / GameMusic vars are AudioComponent references
LAKE_AT = [(-4500, 14700), (-3000, 14700), (-1500, 14650), (0, 14700), (1500, 14700), (3000, 14700), (4500, 14700),
           (1500, 16000)]          # along the shore every 15 m (dock starts at y 14601), and out on the dock
LAKE_INNER, LAKE_FALLOFF = 500.0, 1500.0     # full within 5 m of a shore point, gone by 20 m (user 2026-11-22: "only
                                              # hear the lake from the lake"; was 12 m / 47 m)

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def import_sounds():
    tasks = []
    for f in sorted(glob.glob(ROOT + "export/sounds/*.wav")):
        t = unreal.AssetImportTask()
        t.filename = f
        t.destination_path = DIR
        t.destination_name = "S_" + os.path.splitext(os.path.basename(f))[0]
        t.automated, t.save, t.replace_existing = True, True, True
        tasks.append(t)
    tools.import_asset_tasks(tasks)
    out = {}
    for t in tasks:
        s = unreal.load_asset(f"{DIR}/{t.destination_name}")
        s.set_editor_property("looping", t.destination_name.endswith("_loop"))
        if not t.destination_name.endswith("_loop"):     # short sounds fully in memory: no streaming delay on first play
            s.set_editor_property("loading_behavior", unreal.SoundWaveLoadingBehavior.FORCE_INLINE)
        lib.save_loaded_asset(s, False)
        out[t.destination_name[2:]] = s
    print("imported", sorted(out))
    return out


def attenuation():
    path = f"{DIR}/ATT_Lake"
    att = unreal.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(
        "ATT_Lake", DIR, unreal.SoundAttenuation, unreal.SoundAttenuationFactory())
    st = att.get_editor_property("attenuation")
    st.set_editor_property("attenuate", True)
    st.set_editor_property("spatialize", True)
    st.set_editor_property("attenuation_shape", unreal.AttenuationShape.SPHERE)
    st.set_editor_property("attenuation_shape_extents", unreal.Vector(LAKE_INNER, 0, 0))
    st.set_editor_property("falloff_distance", LAKE_FALLOFF)
    att.set_editor_property("attenuation", st)
    lib.save_loaded_asset(att, False)
    return att


def ambient(label, sound, at, volume, att=None):
    a = actors.spawn_actor_from_class(unreal.AmbientSound, unreal.Vector(*at))
    a.set_actor_label(label)
    a.set_folder_path("Sound")
    a.tags = [TAG]
    c = a.get_editor_property("audio_component")
    c.set_editor_property("sound", sound)
    c.set_editor_property("volume_multiplier", volume)
    c.set_editor_property("auto_activate", True)
    if att:
        c.set_editor_property("attenuation_settings", att)
        c.set_editor_property("allow_spatialization", True)
    else:
        c.set_editor_property("allow_spatialization", False)      # 2D: the same in both ears wherever you are
    return a


for a in actors.get_all_level_actors():
    if a.actor_has_tag(TAG):
        actors.destroy_actor(a)
snd = import_sounds()
# the user's recordings (tools/prep_sounds.py, 2026-11-22) instead of the synthesised wind and lake; bugs are new
# the wind (synth: the recording whistled) and the insects are played by BP_HorrorHUD now, so it can turn them down
# indoors (user 2026-11-22: "shouldn't be able to hear the outside noise when I'm indoors")
att = attenuation()
for k, (x, y) in enumerate(LAKE_AT):
    ambient(f"snd_lake_{k}", snd["rec_lake_rec_loop"], (x, y, 40), LAKE_VOLUME, att)
print("placed: lake x", len(LAKE_AT))

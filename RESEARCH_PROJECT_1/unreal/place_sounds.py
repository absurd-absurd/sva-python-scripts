"""Sound in the level (2026-11-22, first pass): import the sounds from tools/make_sounds.py and place the ambience.

Run in the Unreal editor after `python tools/make_sounds.py` (export/sounds/*.wav). Safe to run again.
  /Game/Horror/Audio/S_<name>     every export/sounds/*.wav as a SoundWave (the *_loop ones set to loop)
  snd_wind                        the wind, everywhere, not placed in space (2D), quiet under everything
  snd_lake_<k>                    the waves, placed along the shore, heard only near the water (attenuation)
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
LAKE_AT = [(-4500, 14700), (-1500, 14650), (1500, 14700), (4500, 14700)]   # along the shore (dock starts at y 14601)
LAKE_INNER, LAKE_FALLOFF = 1200.0, 3500.0                                   # full volume within 12 m, gone by 47 m

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
ambient("snd_wind", snd["wind_loop"], (0, 0, 300), WIND_VOLUME)
att = attenuation()
for k, (x, y) in enumerate(LAKE_AT):
    ambient(f"snd_lake_{k}", snd["lake_loop"], (x, y, 40), LAKE_VOLUME, att)
print("placed: wind + lake x", len(LAKE_AT))

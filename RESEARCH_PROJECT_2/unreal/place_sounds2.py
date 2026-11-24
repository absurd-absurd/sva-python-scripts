"""MARROW Chapter 2: the underwater sound (tools/make_ch2_sounds.py -> export/sounds/*.wav).

Run in the Unreal editor with the Lakebed map open. Safe to run again. Uses Chapter 1's
unreal/place_sounds.py helpers (import, attenuation, ambient), pointed at Chapter 2's files:
  ch2_underwater   everywhere (2D), the pressure and rumble of deep water
  ch2_breath       at the thing in the basin: heard from ~60 m away, loud close up
  ch2_hunter       at the centre of the hunter's ring: its clicking, within ~25 m
"""
import json

import unreal

RP1 = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/"
RP2 = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_2/"
src = open(RP1 + "unreal/place_sounds.py", encoding="utf-8").read()
src = src[:src.index("\nfor a in actors.get_all_level_actors():")]
ns = {"__name__": "ch1_sounds"}
exec(src, ns)
ns.update(ROOT=RP2, DIR="/Game/Chapter2/Audio", TAG="ch2sound")


def attenuation(name, inner, falloff):
    ns.update(LAKE_INNER=inner, LAKE_FALLOFF=falloff)
    att = ns["attenuation"]()                        # makes /Game/Chapter2/Audio/ATT_Lake ...
    path = f"/Game/Chapter2/Audio/{name}"
    lib = unreal.EditorAssetLibrary
    if lib.does_asset_exist(path):
        lib.delete_asset(path)
    lib.rename_asset("/Game/Chapter2/Audio/ATT_Lake", path)   # ... renamed, one per sound
    return unreal.load_asset(path)


data = json.load(open(RP2 + "export/sets_lakebed.json"))
actors = ns["actors"]
for a in actors.get_all_level_actors():
    if a.actor_has_tag("ch2sound"):
        actors.destroy_actor(a)
snd = ns["import_sounds"]()
amb = ns["ambient"]
amb("snd_underwater", snd["ch2_underwater_loop"], data["start"], 0.7)
x, y, z = data["breather"]
amb("snd_breath", snd["ch2_breath_loop"], (x, y, z + 600), 2.5, attenuation("ATT_Breath", 2500.0, 6000.0))
amb("snd_hunter", snd["ch2_hunter_loop"], data["hunter"], 1.5, attenuation("ATT_Hunter", 1100.0, 1500.0))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("Chapter 2 sound placed")

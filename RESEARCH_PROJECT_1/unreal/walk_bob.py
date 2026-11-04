"""Walking head bob: a camera shake that makes the first-person camera move like a head.

Run in the Unreal editor. Makes /Game/Horror/Player/CS_WalkBob, a looping camera shake:
  - up and down twice per stride (once per footstep)
  - a slight roll and side sway once per stride (left foot, right foot)
  - a small dip in pitch with each step
The character Blueprint starts it once and sets its ShakeScale from the walking speed
every frame, so standing still = no bob, walking = full bob (see the README).

UE oscillators advance by Frequency * time in radians, so 2 footsteps a second = 4*pi rad/s.
"""
import math
import unreal

PATH, NAME = "/Game/Horror/Player", "CS_WalkBob"
STEPS_PER_SECOND = 2.0
STEP = 2 * math.pi * STEPS_PER_SECOND          # one cycle per footstep
STRIDE = STEP / 2                              # one cycle per left+right pair

lib = unreal.EditorAssetLibrary
if lib.does_asset_exist(f"{PATH}/{NAME}"):
    bp = unreal.load_asset(f"{PATH}/{NAME}")
else:
    f = unreal.BlueprintFactory()
    f.set_editor_property("parent_class", unreal.LegacyCameraShake)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, PATH, unreal.Blueprint, f)


def wave(amplitude, frequency):
    o = unreal.FOscillator()
    o.set_editor_property("amplitude", amplitude)
    o.set_editor_property("frequency", frequency)
    return o


shake = unreal.get_default_object(bp.generated_class())
shake.set_editor_property("oscillation_duration", -1.0)      # loop forever; the Blueprint scales it
shake.set_editor_property("oscillation_blend_in_time", 0.25)
shake.set_editor_property("oscillation_blend_out_time", 0.25)
rot = unreal.ROscillator()
rot.set_editor_property("pitch", wave(0.1, STEP))           # degrees: a small nod each step
rot.set_editor_property("roll", wave(0.13, STRIDE))           # sway, left foot / right foot
rot.set_editor_property("yaw", wave(0.04, STRIDE))
shake.set_editor_property("rot_oscillation", rot)
loc = unreal.VOscillator()
loc.set_editor_property("z", wave(0.5, STEP))                # cm: head rises and falls each step
loc.set_editor_property("y", wave(0.25, STRIDE))              # cm: weight shifts side to side
shake.set_editor_property("loc_oscillation", loc)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
lib.save_loaded_asset(bp)
print("CS_WalkBob ready:", shake.get_editor_property("rot_oscillation"))

"""Flashlight light settings (the Flashlight spot light in BP_FirstPersonCharacter).

Run in the Unreal editor. The flashlight itself (the light on the camera, F to toggle) was
built by hand in the Blueprint; this script only sets how its light behaves.

Why not real (inverse-square) falloff: the light sits 30 cm in front of the eyes, so with
real falloff anything within about a metre is tens of times brighter than the woods a few
metres away, and walls, doors and beds burned out to pure white up close. Old console
games lit flashlights with a simple, even falloff instead, which is also the PS2 look we
want: the beam fades smoothly out to RADIUS and never gets hotter than INTENSITY.

Tested (Nov 4): same brightness as before in the woods (screen mean 78 vs 77), bed close-up
55% -> 23% pure white, door at half a metre no longer burns out.
"""
import unreal

INTENSITY = 400.0      # unitless (this falloff mode has no physical units)
FALLOFF = 3.0          # how quickly it fades toward RADIUS (higher = more of the light near you)
RADIUS = 1200.0        # cm: the beam reaches 12 m
POSITION = (30, 20, -15)   # cm from the camera: a little forward, right and down, like a held light

bp = unreal.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter")
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
for h in sub.k2_gather_subobject_data_for_blueprint(bp):
    light = lib.get_object(lib.get_data(h))
    if isinstance(light, unreal.SpotLightComponent):
        light.set_editor_property("use_inverse_squared_falloff", False)
        light.set_editor_property("intensity_units", unreal.LightUnits.UNITLESS)
        light.set_editor_property("intensity", INTENSITY)
        light.set_editor_property("light_falloff_exponent", FALLOFF)
        light.set_editor_property("attenuation_radius", RADIUS)
        light.set_editor_property("relative_location", unreal.Vector(*POSITION))
        break
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
print("flashlight: even falloff, intensity", INTENSITY, "radius", RADIUS)

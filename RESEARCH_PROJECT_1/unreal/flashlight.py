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

Flicker (done in BP_HorrorHUD every frame, tools/make_interact_nodes.py, so the light and
the camera stay in step): now and then the beam flutters for a fraction of a second, sometimes
it cuts out completely for under a second, and about half the times it comes back you "hit"
the flashlight: a short camera jolt (CS_FlashHit, made here). How often comes from ONE global
value, Fear (0..1) in MPC_Horror: 0 = calm, 1 = the thing is right there. Later the
creature/rattle only sets that value (Set Scalar Parameter Value on MPC_Horror, "Fear").
"""
import unreal

INTENSITY = 560.0      # unitless (this falloff mode has no physical units); 400 felt a bit dim
FALLOFF = 3.0          # how quickly it fades toward RADIUS (higher = more of the light near you)
RADIUS = 1200.0        # cm: the beam reaches 12 m
POSITION = (30, 20, -15)   # cm from the camera: a little forward, right and down, like a held light
MPC = "/Game/Horror/Materials/MPC_Horror"
# Auto-dim (BP_HorrorHUD), so small rooms don't burn out white while the woods look the same:
# indoors (a ceiling within FlCeiling cm above your eyes) the beam drops to FlIndoor of its power;
# anywhere, it also dims when what it lands on is close: full from FlDimFar cm, FlDimMin at FlDimNear.
AUTO_DIM = (("FlDimNear", 60.0), ("FlDimFar", 250.0), ("FlDimMin", 0.4), ("FlIndoor", 0.15), ("FlCeiling", 250.0))
OLD_FLICKER = "/Game/Horror/Materials/M_FlashlightFlicker"   # first try (light function), removed
HIT = "/Game/Horror/Player/CS_FlashHit"

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary


def fear_collection():
    """MPC_Horror: global values every material and Blueprint can read; Fear starts at 0."""
    if lib.does_asset_exist(MPC):
        mpc = unreal.load_asset(MPC)
    else:
        mpc = tools.create_asset("MPC_Horror", MPC.rsplit("/", 1)[0], unreal.MaterialParameterCollection,
                                 unreal.MaterialParameterCollectionFactoryNew())
    params = []
    for name, value in (("Fear", 0.0),) + AUTO_DIM:
        p = unreal.CollectionScalarParameter()
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", value)
        params.append(p)
    mpc.set_editor_property("scalar_parameters", params)
    lib.save_loaded_asset(mpc, False)
    return mpc


def osc(amplitude, frequency):
    o = unreal.FOscillator()
    o.set_editor_property("amplitude", amplitude)
    o.set_editor_property("frequency", frequency)
    return o


def hit_shake():
    """CS_FlashHit: a knock, like smacking a dying flashlight against your hand (0.5 s).
    First try (1 degree, 0.3 s) was too small to notice."""
    if lib.does_asset_exist(HIT):
        bp = unreal.load_asset(HIT)
    else:
        f = unreal.BlueprintFactory()
        f.set_editor_property("parent_class", unreal.LegacyCameraShake)
        bp = tools.create_asset(HIT.rsplit("/", 1)[1], HIT.rsplit("/", 1)[0], unreal.Blueprint, f)
    shake = unreal.get_default_object(bp.generated_class())
    shake.set_editor_property("oscillation_duration", 0.5)
    shake.set_editor_property("oscillation_blend_in_time", 0.02)
    shake.set_editor_property("oscillation_blend_out_time", 0.3)
    rot = unreal.ROscillator()
    rot.set_editor_property("pitch", osc(3.2, 24.0))     # degrees: a sharp nod down and back
    rot.set_editor_property("roll", osc(2.0, 20.0))
    rot.set_editor_property("yaw", osc(1.0, 17.0))
    shake.set_editor_property("rot_oscillation", rot)
    loc = unreal.VOscillator()
    loc.set_editor_property("z", osc(2.0, 24.0))         # cm
    shake.set_editor_property("loc_oscillation", loc)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    lib.save_loaded_asset(bp, False)


fear_collection()
hit_shake()
if lib.does_asset_exist(OLD_FLICKER):
    lib.delete_asset(OLD_FLICKER)
bp = unreal.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter")
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
parts = unreal.SubobjectDataBlueprintFunctionLibrary
for h in sub.k2_gather_subobject_data_for_blueprint(bp):
    light = parts.get_object(parts.get_data(h))
    if isinstance(light, unreal.SpotLightComponent):
        light.set_editor_property("use_inverse_squared_falloff", False)
        light.set_editor_property("intensity_units", unreal.LightUnits.UNITLESS)
        light.set_editor_property("intensity", INTENSITY)
        light.set_editor_property("light_falloff_exponent", FALLOFF)
        light.set_editor_property("attenuation_radius", RADIUS)
        light.set_editor_property("relative_location", unreal.Vector(*POSITION))
        light.set_editor_property("light_function_material", None)
        # no shadows: the light is held off to the right and bobs with every step, so its shadow
        # edges (TV, dresser, posts, door frames) jittered and crawled in blocks all the time
        light.set_editor_property("cast_shadows", False)
        both = unreal.LightingChannels()           # lights the outside AND the room insides
        both.set_editor_property("channel0", True)
        both.set_editor_property("channel1", True)
        light.set_editor_property("lighting_channels", both)
        break
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
lib.save_loaded_asset(bp, False)
print("auto-dim", AUTO_DIM)
print("flashlight: even falloff, intensity", INTENSITY, "radius", RADIUS, "| CS_FlashHit + MPC_Horror.Fear ready")

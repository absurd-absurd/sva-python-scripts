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

Flicker: a light function (M_FlashlightFlicker) dims the beam a little, all the time: a faint
shimmer and, every 7 s or so, a quick stuttering dip like a tired battery. How bad it gets
comes from ONE global value, Fear (0..1) in MPC_Horror: 0 = calm (now), 1 = the thing is
right there (frequent, deep, stuttering dips, sometimes out for a second).
Measured Nov 4 (beam brightness on a wall over 12 s): Fear 0.5 = a dip every ~1-2 s,
Fear 1 = dimmed nearly all the time with a 1.3 s blackout. Later the creature/rattle only has
to set that one value (Set Scalar Parameter Value on MPC_Horror, "Fear").
"""
import unreal

INTENSITY = 400.0      # unitless (this falloff mode has no physical units)
FALLOFF = 3.0          # how quickly it fades toward RADIUS (higher = more of the light near you)
RADIUS = 1200.0        # cm: the beam reaches 12 m
POSITION = (30, 20, -15)   # cm from the camera: a little forward, right and down, like a held light
MPC = "/Game/Horror/Materials/MPC_Horror"
FLICKER = "/Game/Horror/Materials/M_FlashlightFlicker"

# T = seconds, Fear = 0..1. Returns how much of the beam gets through (0..1).
FLICKER_HLSL = """
float shimmer = 0.95 + 0.05 * sin(T * 23.0 + sin(T * 7.3) * 2.0);
float slot = lerp(0.9, 0.12, Fear);                 // time is cut into slots; shorter when afraid
float k = floor(T / slot);
float chance = lerp(0.12, 0.55, Fear);              // share of slots that dip
float pick = frac(sin(k * 127.1) * 43758.5453);
float depth = lerp(0.5, 0.95, Fear) * (0.5 + 0.5 * frac(sin((k + 17.0) * 311.7) * 43758.5453));
float dipLen = lerp(0.25, 0.6, Fear);               // part of the slot the dip lasts
float dip = (pick < chance && frac(T / slot) < dipLen) ? depth : 0.0;
float stutter = step(0.5, frac(sin(floor(T * 30.0) * 91.3) * 43758.5453));
return saturate(shimmer * (1.0 - dip * lerp(1.0, stutter, 0.6)));
"""

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
    p = unreal.CollectionScalarParameter()
    p.set_editor_property("parameter_name", "Fear")
    p.set_editor_property("default_value", 0.0)
    mpc.set_editor_property("scalar_parameters", [p])
    lib.save_loaded_asset(mpc, False)
    return mpc


def flicker_material(mpc):
    if lib.does_asset_exist(FLICKER):
        m = unreal.load_asset(FLICKER)
        unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(m)
        MEL.delete_all_material_expressions(m)
    else:
        m = tools.create_asset("M_FlashlightFlicker", FLICKER.rsplit("/", 1)[0], unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_LIGHT_FUNCTION)
    time = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -700, 0)
    fear = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, -700, 150)
    fear.set_editor_property("collection", mpc)
    fear.set_editor_property("parameter_name", "Fear")
    code = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, -400, 0)
    code.set_editor_property("code", FLICKER_HLSL)
    code.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    pins = []
    for n in ("T", "Fear"):
        pin = unreal.CustomInput()
        pin.set_editor_property("input_name", n)
        pins.append(pin)
    code.set_editor_property("inputs", pins)
    MEL.connect_material_expressions(time, "", code, "T")
    MEL.connect_material_expressions(fear, "", code, "Fear")
    MEL.connect_material_property(code, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


flicker = flicker_material(fear_collection())
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
        light.set_editor_property("light_function_material", flicker)
        break
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
lib.save_loaded_asset(bp, False)
print("flashlight: even falloff, intensity", INTENSITY, "radius", RADIUS, "+ flicker (Fear in MPC_Horror)")

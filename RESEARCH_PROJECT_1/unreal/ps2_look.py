"""The PS2 look: low resolution, color banding with dither, and wobbly vertices.

Run in the Unreal editor (Tools > Execute Python Script). Safe to run again.

Makes two materials in /Game/Horror/Materials/PS2:
  M_PS2_Screen  - a post-process effect: the picture is cut down to about 448 rows (PS2 resolution)
                  of chunky pixels and a limited number of color levels, with a 4x4
                  ordered dither (the checker pattern the PS2 used to hide banding).
  M_PS2_Surface - the material every object uses: a flat color, fully matte, and a
                  World Position Offset that snaps each vertex to a grid around the
                  camera, so edges jitter as you move. The grid gets coarser with
                  distance, like the PS2's low-precision vertex math.
One wire is connected by hand, once: in M_PS2_Surface, drag the wobble node's
output to World Position Offset (Unreal's Python can't reach that pin).

Then it switches the blockout materials over to M_PS2_Surface, adds the screen
effect to the post-process volume, and turns anti-aliasing off (PS2 edges were jagged).

Tweak without code: open MI_PS2_Screen (Height, Levels, Dither) or any material
instance using M_PS2_Surface (Wobble).
"""
import unreal

DIR = "/Game/Horror/Materials/PS2"
MEL = unreal.MaterialEditingLibrary
assets = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary

SCREEN_HLSL = """
float2 vpUV = GetViewportUV(Parameters);
float2 size = View.ViewSizeAndInvSize.xy;
float2 res = float2(floor(Height * size.x / size.y), Height);
float2 cell = floor(vpUV * res);
float3 c = SceneTextureLookup(ViewportUVToBufferUV((cell + 0.5) / res), 14, false).rgb;

const float bayer[16] = {0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5};
int2 p = int2(fmod(cell, 4.0));
float t = (bayer[p.y * 4 + p.x] + 0.5) / 16.0 - 0.5;
c = floor(c * Levels + 0.5 + t * Dither) / Levels;
return saturate(c) + Unused * 0;
"""

WOBBLE_HLSL = """
// PS2 vertex snapping, only toward the edges and corners of the screen.
// edge = 0 for anything within ~15 degrees of where the camera looks, 1 in the corners
// (the field of view is 65 degrees, so a corner is ~38 degrees off-center).
float d = length(Rel);
float off = 1.0 - dot(Rel / max(d, 1.0), ResolvedView.ViewForward);
float edge = saturate((off - 0.035) / 0.17);
edge *= edge;
if (edge < 0.01) return float3(0, 0, 0);
float g = max(d * Amount * edge, 0.01);
return floor(Rel / g + 0.5) * g - Rel;
"""


def material(name):
    path = f"{DIR}/{name}"
    if lib.does_asset_exist(path):
        m = unreal.load_asset(path)
        MEL.delete_all_material_expressions(m)
        return m
    return assets.create_asset(name, DIR, unreal.Material, unreal.MaterialFactoryNew())


def instance(name, parent):
    path = f"{DIR}/{name}"
    mi = unreal.load_asset(path) if lib.does_asset_exist(path) else \
        assets.create_asset(name, DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    lib.save_loaded_asset(mi)
    return mi


def scalar(m, name, value, x, y):
    p = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
    p.set_editor_property("parameter_name", name)
    p.set_editor_property("default_value", value)
    return p


def custom(m, code, inputs, output_type, x, y):
    c = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    c.set_editor_property("code", code)
    c.set_editor_property("output_type", output_type)
    pins = []
    for n in inputs:
        pin = unreal.CustomInput()
        pin.set_editor_property("input_name", n)
        pins.append(pin)
    c.set_editor_property("inputs", pins)
    return c


def build_screen():
    m = material("M_PS2_Screen")
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    m.set_editor_property("blendable_location", unreal.BlendableLocation.BL_SCENE_COLOR_AFTER_TONEMAPPING)
    c = custom(m, SCREEN_HLSL, ["Height", "Levels", "Dither", "Unused"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -300, 0)
    MEL.connect_material_expressions(scalar(m, "Height", 448.0, -700, -150), "", c, "Height")
    MEL.connect_material_expressions(scalar(m, "Levels", 48.0, -700, -50), "", c, "Levels")
    MEL.connect_material_expressions(scalar(m, "Dither", 0.25, -700, 50), "", c, "Dither")
    # the scene texture node makes Unreal bind the picture so the code can read it
    st = MEL.create_material_expression(m, unreal.MaterialExpressionSceneTexture, -700, 150)
    st.set_editor_property("scene_texture_id", unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
    MEL.connect_material_expressions(st, "Color", c, "Unused")
    MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m)
    return instance("MI_PS2_Screen", m)


def build_surface():
    path = f"{DIR}/M_PS2_Surface"
    if lib.does_asset_exist(path):
        # Built already. Not rebuilt, because the World Position Offset wire is
        # connected by hand (Unreal's Python can't connect that pin) and would be lost.
        return unreal.load_asset(path)
    m = material("M_PS2_Surface")
    color = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -500, -200)
    color.set_editor_property("parameter_name", "Color")
    color.set_editor_property("default_value", unreal.LinearColor(0.2, 0.2, 0.2, 1))
    MEL.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, -50)
    rough.set_editor_property("r", 1.0)
    MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    spec = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 30)
    spec.set_editor_property("r", 0.0)
    MEL.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)

    wp = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -700, 200)
    wp.set_editor_property("world_position_shader_offset", unreal.WorldPositionIncludedOffsets.WPT_CAMERA_RELATIVE_NO_OFFSETS)
    c = custom(m, WOBBLE_HLSL, ["Rel", "Amount"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -300, 200)
    MEL.connect_material_expressions(wp, "", c, "Rel")
    MEL.connect_material_expressions(scalar(m, "Wobble", 0.0025, -700, 320), "", c, "Amount")
    # Unreal's Python has no name for the World Position Offset pin, so this one wire
    # is connected by hand: drag from this node's output to World Position Offset.
    note = MEL.create_material_expression(m, unreal.MaterialExpressionComment, -340, 150)
    note.set_editor_property("text", "WOBBLE: drag this node's output to World Position Offset")
    MEL.recompile_material(m)
    lib.save_loaded_asset(m)
    return m


def update_wobble(surface):
    """Put the current WOBBLE_HLSL into the existing wobble node, without rebuilding the
    material (its World Position Offset wire was connected by hand)."""
    for e in unreal.ObjectIterator(unreal.MaterialExpressionCustom):
        if e.get_outer() == surface and "Amount" in [str(i.get_editor_property("input_name")) for i in e.get_editor_property("inputs")]:
            e.set_editor_property("code", WOBBLE_HLSL)
            for p in unreal.ObjectIterator(unreal.MaterialExpressionScalarParameter):
                if p.get_outer() == surface and str(p.get_editor_property("parameter_name")) == "Wobble":
                    p.set_editor_property("default_value", 0.0025)
            MEL.recompile_material(surface)
            lib.save_loaded_asset(surface)
            return True
    return False


def switch_blockout(surface):
    """The blockout's flat colors already use a 'Color' parameter, so just change their parent."""
    n = 0
    for a in unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path("/Game/Horror/Materials/Blockout"):
        mi = a.get_asset()
        if isinstance(mi, unreal.MaterialInstanceConstant):
            mi.set_editor_property("parent", surface)
            lib.save_loaded_asset(mi)
            n += 1
    return n


def hook_screen(mi):
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    pp = next(a for a in acts if a.get_actor_label() == "PostProcess_Look")
    s = pp.settings
    s.set_editor_property("weighted_blendables",
                          unreal.WeightedBlendables(array=[unreal.WeightedBlendable(weight=1.0, object=mi)]))
    pp.set_editor_property("settings", s)


def no_antialiasing():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, "r.AntiAliasingMethod 0")
    unreal.SystemLibrary.execute_console_command(world, "r.DefaultFeature.MotionBlur 0")
    # saved for good in Config/DefaultEngine.ini under [/Script/Engine.RendererSettings]


def main():
    unreal.EditorAssetLibrary.make_directory(DIR)
    screen = build_screen()
    surface = build_surface()
    update_wobble(surface)
    n = switch_blockout(surface)
    hook_screen(screen)
    no_antialiasing()
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print(f"PS2 look on: screen effect hooked up, {n} blockout materials switched")


main()

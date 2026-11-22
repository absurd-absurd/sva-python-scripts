"""The world breaks down near the lake (STORY.md): the closer you get, the more the PS2 picture falls apart.

Run in the Unreal editor. Safe to run again. Makes /Game/Horror/Materials/PS2/M_Breakdown, a post-process
effect added to PostProcess_Look before the PS2 screen effect (so the result still gets chunky pixels):
  - when (user 2026-11-22): flashes for a few seconds after each page in the wrong hand (MPC_Horror.WarpFlash = 1),
    keeps flashing every few seconds once the boathouse note is read (WarpFlash = LATE_FLASH), fully warped on the
    dock after that note and through Bug's last line (WarpWhole = 1), and one second at the very end of the
    "one year later" shot. All set by the HUD (tools/make_interact_nodes.py).
  - a slow wavy warp of the whole picture, like looking through water
  - shapes stretching: the picture pulled a little toward the centre line, more at the edges
  - red and blue fringes pulling apart (a chromatic split)
  - the fog turns red: distant parts of the picture (scene depth) tinted toward deep red
  - now and then a glitch tear: bands of the picture jump sideways for a frame or two
Tune live: MI_Breakdown (Start, Full, Strength).
"""
import unreal

DIR = "/Game/Horror/Materials/PS2"
MEL = unreal.MaterialEditingLibrary
assets = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary

HLSL = """
// user 2026-11-22: the HUD drives it all. Flash (MPC_Horror.WarpFlash) = how often it flashes: 1 for a few
// seconds after a wrong-hand page, LATE_FLASH for the rest of the game once the boathouse note is read.
// Whole (WarpWhole) = fully warped: on the dock after the boathouse note, and the last second of the final shot.
// (Pos and Full are still wired in but unused.)
float t = Time;
float act = Flash + 0 * (Pos.y + Full);
// time is cut into short slots; some of them flare up for a moment and fade
float slot = floor(t / 0.7);
float roll = frac(sin(slot * 91.7 + 3.1) * 43758.5453);
float within = frac(t / 0.7);
float glimpse = (roll > 1.0 - 0.5 * act) ? sin(within * 3.14159) : 0.0;
float F = max(Whole, glimpse * (0.45 + 0.55 * act)) * Strength;
float2 uv = GetViewportUV(Parameters);
if (F < 0.002) { return SceneTextureLookup(ViewportUVToBufferUV(uv), 14, false).rgb + Unused * 0; }
// slow wavy warp (water / heat), and a pull toward the centre (stretch)
float2 w = float2(sin(uv.y * 23.0 + t * 1.7) + 0.6 * sin(uv.y * 61.0 - t * 2.9),
                  sin(uv.x * 17.0 + t * 1.3) + 0.5 * sin(uv.x * 47.0 + t * 2.1)) * 0.0035 * F;
float2 c = uv - 0.5;
uv = 0.5 + c * float2(1.0 - 0.05 * F * abs(c.y) * 2.0, 1.0 - 0.07 * F * abs(c.x) * 2.0) + w;
// glitch tear: a few bands jump sideways, now and then
float tick = floor(t * 9.0);
float rnd = frac(sin(tick * 12.9898) * 43758.5453);
float band = frac(sin(floor(uv.y * 14.0 + tick) * 78.233) * 9374.13);
if (rnd > 1.0 - 0.18 * F && band > 0.55) { uv.x += (band - 0.75) * 0.06 * F; }
// chromatic split
float2 off = c * 0.012 * F + w * 2.0;
float r = SceneTextureLookup(ViewportUVToBufferUV(uv + off), 14, false).r;
float g = SceneTextureLookup(ViewportUVToBufferUV(uv), 14, false).g;
float b = SceneTextureLookup(ViewportUVToBufferUV(uv - off), 14, false).b;
float3 col = float3(r, g, b);
// the fog turns red: far away (and the fog itself) pulled toward deep red
float depth = SceneTextureLookup(ViewportUVToBufferUV(uv), 1, false).r;
float far = saturate((depth - 800.0) / 6000.0);
float lum = dot(col, float3(0.3, 0.59, 0.11));
float3 red = float3(lum * 1.45 + 0.01, lum * 0.5, lum * 0.45);
col = lerp(col, red, F * (0.12 + 0.5 * far));
// a dark red edge closing in
float vig = saturate(length(c) * 1.6 - 0.35);
col = lerp(col, col * float3(0.75, 0.35, 0.32), vig * F * 0.5);
return col + Unused * 0;
"""


def material():
    path = f"{DIR}/M_Breakdown"
    if lib.does_asset_exist(path):
        m = unreal.load_asset(path)
        MEL.delete_all_material_expressions(m)
    else:
        m = assets.create_asset("M_Breakdown", DIR, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    # same stage as the PS2 look (after tonemapping, display colours) and just before it, so with the effect
    # off the picture is untouched (before-DOF darkened everything: 2026-11-17)
    m.set_editor_property("blendable_location", unreal.BlendableLocation.BL_SCENE_COLOR_AFTER_TONEMAPPING)
    m.set_editor_property("blendable_priority", -1)
    c = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, -200, 0)
    c.set_editor_property("code", HLSL)
    c.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    pins = []
    for n in ("Pos", "Start", "Full", "Strength", "Time", "Unused", "Flash", "Whole"):
        pin = unreal.CustomInput()
        pin.set_editor_property("input_name", n)
        pins.append(pin)
    c.set_editor_property("inputs", pins)
    pos = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, -700, -250)
    pos.set_editor_property("collection", unreal.load_asset("/Game/Horror/Materials/MPC_Horror"))
    pos.set_editor_property("parameter_name", "PlayerPos")
    MEL.connect_material_expressions(pos, "", c, "Pos")
    for k, name in enumerate(("WarpFlash", "WarpWhole")):
        q = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, -700, -400 - k * 90)
        q.set_editor_property("collection", unreal.load_asset("/Game/Horror/Materials/MPC_Horror"))
        q.set_editor_property("parameter_name", name)
        MEL.connect_material_expressions(q, "", c, ("Flash", "Whole")[k])
    for k, (name, v) in enumerate((("Start", 3000.0), ("Full", 13900.0), ("Strength", 1.0))):
        p = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, -120 + k * 90)
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", v)
        MEL.connect_material_expressions(p, "", c, name)
    t = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -700, 170)
    MEL.connect_material_expressions(t, "", c, "Time")
    st = MEL.create_material_expression(m, unreal.MaterialExpressionSceneTexture, -700, 260)
    st.set_editor_property("scene_texture_id", unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
    MEL.connect_material_expressions(st, "Color", c, "Unused")
    MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    path = f"{DIR}/MI_Breakdown"
    mi = unreal.load_asset(path) if lib.does_asset_exist(path) else assets.create_asset(
        "MI_Breakdown", DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", m)
    lib.save_loaded_asset(mi, False)
    return mi


def attach(mi):
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label() == "PostProcess_Look":
            s = a.settings
            blends = [b for b in s.weighted_blendables.array if not (b.object and b.object.get_name() == "MI_Breakdown")]
            blends.insert(0, unreal.WeightedBlendable(weight=1.0, object=mi))
            s.set_editor_property("weighted_blendables", unreal.WeightedBlendables(array=blends))
            a.set_editor_property("settings", s)
            print("breakdown added to", a.get_actor_label(), [b.object.get_name() for b in blends if b.object])


def mpc_params():
    """WarpFlash / WarpWhole in MPC_Horror (kept if there: rebuilding params gives them new ids and breaks
    materials that use them, see flashlight.py)."""
    mpc = unreal.load_asset("/Game/Horror/Materials/MPC_Horror")
    params = list(mpc.get_editor_property("scalar_parameters"))
    have = [str(p.get_editor_property("parameter_name")) for p in params]
    for name in ("WarpFlash", "WarpWhole"):
        if name not in have:
            p = unreal.CollectionScalarParameter()
            p.set_editor_property("parameter_name", name)
            p.set_editor_property("default_value", 0.0)
            params.append(p)
    mpc.set_editor_property("scalar_parameters", params)
    lib.save_loaded_asset(mpc, False)


mpc_params()
attach(material())

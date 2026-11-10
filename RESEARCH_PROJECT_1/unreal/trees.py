"""Bring the realistic trees (maya/make_trees.py -> export/trees/*.fbx) into Unreal, replacing
the old low-poly trees in /Game/Horror/Props under the same names, so every tree already placed
(the scatter tool's woods, the forest fill) turns into a new one.

- M_PS2_TreeBark: the PS2 surface (world-projected bark texture); its wind code is there but
  set to 0 (Sway), because the leaves can't move with it
- M_PS2_Leaves: the leaf / needle cards: the card's picture (tools/make_foliage.py), its
  see-through background cut away (masked), seen from both sides
- collision: just the UCX_ cylinder round the bottom of the trunk
- trees past 120 m aren't drawn (the fog has long swallowed them), ferns and shrubs past 50 m

Run after import_scatter.py and fill_forest.py (build_level.py). Safe to run again.
"""
import unreal

ROOT = "C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
PROPS = "/Game/Horror/Props"
DIR = "/Game/Horror/Trees"
SURFACE = "/Game/Horror/Materials/PS2/M_PS2_Surface"
TREES = ("tree_pine_A", "tree_pine_B", "tree_leafy_A", "tree_leafy_B", "tree_dead_C", "tree_dead_A", "tree_dead_B",
         "tree_dead_pine", "bush_A", "shrub_dead_A", "shrub_dead_B")
PLANTS = ("bush_A", "shrub_dead_A", "shrub_dead_B")            # ferns and twiggy shrubs: walk-through
DRAW = 12000.0
# material slot -> (parent, colour tint, card picture or bark texture)
LOOK = {
    "tree_bark_mat":         ("bark", (0.32, 0.29, 0.26), None),
    "tree_leaves_mat":       ("foliage", (0.8, 0.9, 0.7), "T_leaves_broad"),
    "tree_dead_leaves_mat":  ("foliage", (0.85, 0.55, 0.32), "T_leaves_broad"),
    "tree_needles_mat":      ("foliage", (0.85, 1.0, 0.85), "T_leaves_pine"),
    "tree_dead_needles_mat": ("foliage", (1.0, 0.55, 0.3), "T_leaves_pine"),
    "fern_mat":              ("foliage", (0.9, 1.0, 0.8), "T_fern"),
}

WIND_HLSL = """
// The whole tree leans with the wind, more the higher up (roots stay put), in slow gusts that
// roll across the woods; leaf cards also flutter quickly.
float3 L = WPos - OPos;
float s = saturate(L.z / 2400.0);
s *= s;
float ph = dot(OPos.xy, float2(0.0017, 0.0011));
float gust = 0.6 + 0.4 * sin(T * 0.31 + ph);
float2 dir = normalize(float2(0.8, 0.5));
float3 o = float3(dir * (sin(T * 0.8 + ph * 5.0) * 0.7 + 0.45) * gust * Sway * s, 0);
o += Flutter * s * float3(sin(T * 5.3 + dot(WPos, float3(0.031, 0.047, 0.023))),
                          cos(T * 4.7 + dot(WPos, float3(0.043, 0.029, 0.037))),
                          sin(T * 6.1 + dot(WPos, float3(0.027, 0.039, 0.051))) * 0.6);
return o;
"""

lib = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def _expr(m, cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e


def _wobble_node(m):
    return [e for e in unreal.ObjectIterator(unreal.MaterialExpressionCustom) if e.get_outer() == m
            and "Amount" in [str(i.get_editor_property("input_name")) for i in e.get_editor_property("inputs")]][0]


def windy_copy(path, sway, flutter):
    """A copy of M_PS2_Surface whose World Position Offset node (already wired to WPO by hand
    once; Python can't make that wire) runs WIND_HLSL. Made once, its code refreshed each run."""
    if lib.does_asset_exist(path):                         # already made: just refresh the wind code
        m = unreal.load_asset(path)
        _wobble_node(m).set_editor_property("code", WIND_HLSL)
        MEL.recompile_material(m)
        lib.save_loaded_asset(m, False)
        return m, False
    m = lib.duplicate_asset(SURFACE, path)
    node = _wobble_node(m)
    pins = list(node.get_editor_property("inputs"))
    for n in ("WPos", "OPos", "T", "Sway", "Flutter"):
        p = unreal.CustomInput()
        p.set_editor_property("input_name", n)
        pins.append(p)
    node.set_editor_property("inputs", pins)
    node.set_editor_property("code", WIND_HLSL)
    wpos = _expr(m, unreal.MaterialExpressionWorldPosition, -1200, 300,
                 world_position_shader_offset=unreal.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    zero = _expr(m, unreal.MaterialExpressionConstant3Vector, -1400, 380, constant=unreal.LinearColor(0, 0, 0, 0))
    opos = _expr(m, unreal.MaterialExpressionTransformPosition, -1200, 380,
                 transform_source_type=unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL,
                 transform_type=unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD)
    MEL.connect_material_expressions(zero, "", opos, "")
    t = _expr(m, unreal.MaterialExpressionTime, -1200, 460)
    MEL.connect_material_expressions(wpos, "", node, "WPos")
    MEL.connect_material_expressions(opos, "", node, "OPos")
    MEL.connect_material_expressions(t, "", node, "T")
    for i, (n, v) in enumerate((("Sway", sway), ("Flutter", flutter))):
        sp = _expr(m, unreal.MaterialExpressionScalarParameter, -1200, 540 + i * 80, parameter_name=n, default_value=v)
        MEL.connect_material_expressions(sp, "", node, n)
    return m, True


def foliage_material():
    """M_PS2_Leaves: the leaf / needle cards. Built fresh (not a copy of M_PS2_Surface like the
    rest): in the copy the cut-out never worked and every card drew as a solid square, so the
    leaves don't sway (Python can't wire World Position Offset on a new material). Flat PS2
    shading: rough, no shine; the card's picture by its UVs x Color; its alpha is the cut-out."""
    path = DIR + "/M_PS2_Leaves"
    if lib.does_asset_exist(path):
        return unreal.load_asset(path)
    m = tools.create_asset("M_PS2_Leaves", DIR, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    m.set_editor_property("two_sided", True)
    m.set_editor_property("opacity_mask_clip_value", 0.4)
    tex = _expr(m, unreal.MaterialExpressionTextureSampleParameter2D, -700, -100, parameter_name="CardTex",
                texture=unreal.load_asset(DIR + "/T_leaves_broad"))
    color = _expr(m, unreal.MaterialExpressionVectorParameter, -700, 150, parameter_name="Color",
                  default_value=unreal.LinearColor(1, 1, 1, 1))
    mulx = _expr(m, unreal.MaterialExpressionMultiply, -400, -50)
    MEL.connect_material_expressions(tex, "RGB", mulx, "A")
    MEL.connect_material_expressions(color, "", mulx, "B")
    MEL.connect_material_property(mulx, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(tex, "A", unreal.MaterialProperty.MP_OPACITY_MASK)
    rough = _expr(m, unreal.MaterialExpressionConstant, -400, 150, r=1.0)
    spec = _expr(m, unreal.MaterialExpressionConstant, -400, 220, r=0.0)
    MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


def bark_material():
    m, new = windy_copy(DIR + "/M_PS2_TreeBark", 0.0, 0.0)   # still: the leaves can't sway with it
    MEL.recompile_material(m)
    lib.save_loaded_asset(m, False)
    return m


def import_texture(name):
    t = unreal.AssetImportTask()
    t.filename = f"{ROOT}/export/{name}.png"
    t.destination_path, t.destination_name = DIR, "T_" + name
    t.automated, t.replace_existing, t.save = True, True, True
    tools.import_asset_tasks([t])
    tex = unreal.load_asset(f"{DIR}/T_{name}")
    # keep the see-through background exact: the default compression smeared the alpha, so the
    # cut-out left whole squares around the leaves
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("compression_no_alpha", False)
    lib.save_loaded_asset(tex, False)


def instances():
    parents = {"foliage": foliage_material(), "bark": bark_material()}
    bark = unreal.load_asset("/Game/Horror/Textures/T_bark")
    out = {}
    for slot, (kind, rgb, pic) in LOOK.items():
        path = f"{DIR}/MI_{slot}"
        mi = unreal.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(
            "MI_" + slot, DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, parents[kind])
        MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*rgb, 1))
        if pic:
            MEL.set_material_instance_texture_parameter_value(mi, "CardTex", unreal.load_asset(f"{DIR}/{pic}"))
        elif bark:
            MEL.set_material_instance_texture_parameter_value(mi, "Tex", bark)
            MEL.set_material_instance_scalar_parameter_value(mi, "TexSize", 160.0)
        lib.save_loaded_asset(mi, False)
        out[slot] = mi
    return out


def import_tree(name, mis):
    t = unreal.AssetImportTask()
    t.filename = f"{ROOT}/export/trees/{name}.fbx"
    t.destination_path, t.destination_name = PROPS, name
    t.automated, t.replace_existing, t.save = True, True, True
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_materials", False)
    opts.set_editor_property("import_textures", False)
    sm = opts.get_editor_property("static_mesh_import_data")
    sm.set_editor_property("auto_generate_collision", False)       # the UCX_ cylinder is the collision
    sm.set_editor_property("combine_meshes", True)
    t.options = opts
    tools.import_asset_tasks([t])
    mesh = unreal.load_asset(f"{PROPS}/{name}")
    body = mesh.get_editor_property("body_setup")
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    mesh.set_editor_property("body_setup", body)
    nan = mesh.get_editor_property("nanite_settings")
    nan.set_editor_property("enabled", False)
    mesh.set_editor_property("nanite_settings", nan)
    for i, s in enumerate(mesh.get_editor_property("static_materials")):
        slot = str(s.material_slot_name)
        for key, mi in mis.items():
            if key in slot:
                mesh.set_material(i, mi)
    # no generated LODs: Unreal's reduction broke the leaf cards' cut-out on the reduced versions
    # (whole squares showed); the fog and the draw distance keep the cost down instead
    unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).remove_lods(mesh)
    lib.save_loaded_asset(mesh, False)
    return mesh


def main():
    for n in ("leaves_broad", "leaves_pine", "fern"):
        import_texture(n)
    mis = instances()
    meshes = {n: import_tree(n, mis) for n in TREES}
    # every placed tree: drawn out to DRAW only, and the shadow-free PS2 look
    count = 0
    for a in actors.get_all_level_actors():
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if c and c.static_mesh and c.static_mesh.get_name() in meshes:
            c.set_editor_property("ld_max_draw_distance", DRAW)
            # drop the old trees' per-actor material overrides: they'd paint the new leaf cards
            # with the old world-projected leaf texture (squares) instead of the cut-out pictures
            c.set_editor_property("override_materials", [])
            if c.static_mesh.get_name() in PLANTS:
                c.set_collision_profile_name("NoCollision")
                c.set_editor_property("ld_max_draw_distance", 5000.0)
            count += 1
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print("trees:", len(meshes), "kinds,", count, "placed trees updated")


main()

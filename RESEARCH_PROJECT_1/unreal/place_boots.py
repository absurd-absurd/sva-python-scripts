"""Cas's boots by the boathouse water door (user 2026-11-22): the Fab "Leather Boots" pair (Top_Boots; the user
swapped it in for the "Hiking Boots LOWPOLY" scan the same day), in place of the boots maya/lake_buildings.py
used to build there.

The pack is one mesh with both boots, so tools/split_boots.py (mayapy) cut it into export/boots/boot_left.fbx and
boot_right.fbx; this imports them as SM_Cas_Boot_Left/Right and places the left one standing, toes to the water,
and the right one lying on its side beside it (user: "put one laying down like the last boots that we had").
The pack came without a material: MI_Cas_Boots is made from its textures on Unreal's glTF material, darkened to
black leather (user: "lets make them black"). Run in the Unreal editor after import_sets.py. Safe to run again.
"""
import unreal

ROOT = "C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/"
DIR = "/Game/Fab/Leather_Boots"
TEX = DIR + "/Boots_"
MI_PATH = DIR + "/MI_Cas_Boots"
FLOOR = 16.0                       # boathouse floor (lake_buildings BH_FL)
STAND = (-3747.0, 15022.0)         # the standing boot (centre); the note lies just east of it, at x -3703
LIE = (-3782.0, 15030.0)           # the fallen one, its shaft pointing west, away from the note
LIE_YAW = 8.0                      # a little askew
SCALE = 0.36                       # the model is ~119 cm tall; tall leather boots ~43 cm (foot ~23 cm)
BLACK = unreal.LinearColor(0.05, 0.048, 0.046, 1.0)   # multiplies the leather texture: near-black, the grain still shows
LABELS = ("prop_cas_boots", "prop_cas_boot_standing", "prop_cas_boot_fallen")

lib = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def material():
    mi = unreal.load_asset(MI_PATH) if lib.does_asset_exist(MI_PATH) else tools.create_asset(
        MI_PATH.rsplit("/", 1)[1], DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", unreal.load_asset("/InterchangeAssets/gltf/MaterialInstances/MI_Default_Opaque"))
    nrm = unreal.load_asset(TEX + "normal")
    nrm.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    nrm.set_editor_property("srgb", False)
    orm = unreal.load_asset(TEX + "OcclusionRoughnessMetallic")
    orm.set_editor_property("srgb", False)
    for t in (nrm, orm):
        lib.save_loaded_asset(t, False)
    for param, tex in (("BaseColorTexture", "BaseColor"), ("NormalTexture", "normal"),
                       ("MetallicRoughnessTexture", "OcclusionRoughnessMetallic"), ("OcclusionTexture", "OcclusionRoughnessMetallic")):
        MEL.set_material_instance_texture_parameter_value(mi, param, unreal.load_asset(TEX + tex))
    MEL.set_material_instance_vector_parameter_value(mi, "BaseColorFactor", BLACK)
    # no shine: matte leather (the fallen boot caught the flashlight like metal)
    MEL.set_material_instance_scalar_parameter_value(mi, "MetallicFactor", 0.0)
    MEL.set_material_instance_scalar_parameter_value(mi, "RoughnessFactor", 1.0)
    lib.save_loaded_asset(mi, False)
    return mi


def import_boot(name):
    t = unreal.AssetImportTask()
    t.filename = ROOT + f"export/boots/{name}.fbx"
    t.destination_path = DIR
    t.destination_name = "SM_Cas_" + name.replace("boot_", "Boot_").title().replace("_", "_")
    t.automated, t.save, t.replace_existing = True, True, True
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    ui.static_mesh_import_data.set_editor_property("combine_meshes", True)
    t.options = ui
    tools.import_asset_tasks([t])
    return unreal.load_asset(f"{DIR}/{t.destination_name}")


def spawn(mesh, label, rot, mi, at):
    a = actors.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), rot)
    a.set_actor_label(label)
    a.set_folder_path("Props")
    a.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
    c = a.static_mesh_component
    c.set_material(0, mi)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    lc = unreal.LightingChannels()                   # inside the boathouse = light channel 1, like the room sets
    lc.set_editor_property("channel0", False)
    lc.set_editor_property("channel1", True)
    c.set_editor_property("lighting_channels", lc)
    # move it so its bounds sit centred on `at`, resting on the floor
    o, e = a.get_actor_bounds(False)
    a.set_actor_location(unreal.Vector(at[0] - o.x, at[1] - o.y, FLOOR - (o.z - e.z)), False, True)
    o, e = a.get_actor_bounds(False)
    print(label, "centre", round(o.x), round(o.y), "size", round(2 * e.x), round(2 * e.y), round(2 * e.z))
    return a


for a in actors.get_all_level_actors():
    if a.get_actor_label() in LABELS:
        actors.destroy_actor(a)
mi = material()
left, right = import_boot("boot_left"), import_boot("boot_right")
spawn(left, "prop_cas_boot_standing", unreal.Rotator(0, 0, 0), mi, STAND)       # toes to the water (+y)
# on its side: rolled 90 degrees about its length, so the tall shaft lies along the floor
spawn(right, "prop_cas_boot_fallen", unreal.Rotator(roll=0.0, pitch=90.0, yaw=LIE_YAW), mi, LIE)

"""Cas's boots by the boathouse water door (user 2026-11-22): the Fab "Leather Boots" pair (Top_Boots; the user
swapped it in for the "Hiking Boots LOWPOLY" scan the same day), in place of the boots maya/lake_buildings.py
used to build there. The pack came without a material, so MI_Cas_Boots is made from its textures on
Unreal's glTF material. Run in the Unreal editor after import_sets.py. Safe to run
again (deletes the old one first)."""
import unreal

MESH = "/Game/Fab/Leather_Boots/Top_Boots"
TEX = "/Game/Fab/Leather_Boots/Boots_"
MI_PATH = "/Game/Fab/Leather_Boots/MI_Cas_Boots"
AT = (-3752.0, 15025.0, 16.0)     # = lake_buildings boathouse(): BX, BYB, F (west walkway by the water door)
SCALE = 0.36                       # the model is ~119 cm tall; tall leather boots ~43 cm (foot ~23 cm)
YAW = 0.0                          # toes to the water (+y): the mesh's toes point +y (checked from its vertices)
LABEL = "prop_cas_boots"

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actors.get_all_level_actors():
    if a.get_actor_label() == LABEL:
        actors.destroy_actor(a)
mesh = unreal.load_asset(MESH)
lib = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
mi = unreal.load_asset(MI_PATH) if lib.does_asset_exist(MI_PATH) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    MI_PATH.rsplit("/", 1)[1], MI_PATH.rsplit("/", 1)[0], unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
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
lib.save_loaded_asset(mi, False)
lo = mesh.get_bounding_box().min
a = actors.spawn_actor_from_object(mesh, unreal.Vector(AT[0], AT[1], AT[2] - lo.z * SCALE), unreal.Rotator(0, 0, YAW))
a.set_actor_label(LABEL)
a.set_folder_path("Props")
a.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
c = a.static_mesh_component
c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
c.set_material(0, mi)
lc = unreal.LightingChannels()                       # inside the boathouse = light channel 1, like the room sets
lc.set_editor_property("channel0", False)
lc.set_editor_property("channel1", True)
c.set_editor_property("lighting_channels", lc)
print("boots at", a.get_actor_location(), "bounds", a.get_actor_bounds(False))

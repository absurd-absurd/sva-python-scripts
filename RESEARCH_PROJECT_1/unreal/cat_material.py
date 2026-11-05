"""MI_Cat: the rigged black cat's material: M_PS2_Critter (matte PS2 look, Mode 9 = no shader motion)
with the Fab cat's own colour and normal textures through its UVs, darkened so it stays black.
Run after critters.py and cat_rig_import.py; cat_walk.py puts it on the cat."""
import unreal
MEL = unreal.MaterialEditingLibrary; lib = unreal.EditorAssetLibrary
reg = unreal.AssetRegistryHelpers.get_asset_registry()
found = list(reg.get_assets_by_path("/Game/Fab", recursive=True))
tex = {str(a.asset_name): a.get_asset() for a in found if str(a.asset_class_path.asset_name) == "Texture2D"}
crit = [unreal.load_asset(p) for p in ("/Game/Horror/Materials/PS2/M_PS2_Critter", "/Game/Horror/Materials/PS2/M_PS2_Critter_b") if lib.does_asset_exist(p)]
parent = unreal.load_asset("/Game/Horror/Critters/MI_Critter_moth_moth").get_editor_property("parent")
path = "/Game/Horror/Critters/Cat/MI_Cat"
mi = unreal.load_asset(path) if lib.does_asset_exist(path) else unreal.AssetToolsHelpers.get_asset_tools().create_asset("MI_Cat", "/Game/Horror/Critters/Cat", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
mi.set_editor_property("parent", parent)
MEL.set_material_instance_texture_parameter_value(mi, "Tex", next(t for n, t in tex.items() if "base" in n.lower()))
MEL.set_material_instance_texture_parameter_value(mi, "NormalTex", next(t for n, t in tex.items() if "normal" in n.lower()))
for k, v in (("UVMode", 1.0), ("Mode", 9.0)):
    MEL.set_material_instance_scalar_parameter_value(mi, k, v)
MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(0.4, 0.4, 0.42, 1))   # keeps him black under the PS2 light
lib.save_loaded_asset(mi, False)
print("MI_Cat parent", parent.get_name())

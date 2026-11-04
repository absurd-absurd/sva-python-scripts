"""Bring the paper map into Unreal for the HUD's corner map.

Run in the Unreal editor after tools/make_map.py. Imports export/map.png and
export/map_marker.png as /Game/Horror/UI/T_Map and T_MapMarker, set up as UI textures
(no mipmaps, no streaming, clamped edges) so the map stays sharp and never smears at the border.
"""
import unreal

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/export/"
DEST = "/Game/Horror/UI"


def bring(png, name):
    t = unreal.AssetImportTask()
    t.filename = ROOT + png
    t.destination_path = DEST
    t.destination_name = name
    t.automated, t.save, t.replace_existing = True, True, True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = unreal.load_asset(f"{DEST}/{name}")
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)   # "UserInterface2D"
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("never_stream", True)
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
    return tex


bring("map.png", "T_Map")
bring("map_marker.png", "T_MapMarker")
print("map textures imported")

"""Bring the paper map into Unreal for the HUD's corner map.

Run in the Unreal editor after tools/make_map.py. Imports export/map.png and
export/map_marker.png / export/map_full.png as /Game/Horror/UI/T_Map, T_MapMarker
and T_MapFull, set up as UI textures
(sharpened mipmaps, no streaming, clamped edges) so the map stays sharp and never smears at the border.
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
    # smaller, sharpened copies (mipmaps): on a smaller screen the 2048 px map is shrunk a lot, and
    # without them the pen lines and handwriting come out jagged/pixelated in the game
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_SHARPEN4)
    tex.set_editor_property("filter", unreal.TextureFilter.TF_TRILINEAR)
    tex.set_editor_property("never_stream", True)
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
    return tex


bring("map.png", "T_Map")
bring("map_marker.png", "T_MapMarker")
bring("map_full.png", "T_MapFull")          # torn paper, with see-through edges
bring("map_frame.png", "T_MapFrame")        # torn edge laid round the corner map
bring("prompt_scrap.png", "T_PromptScrap")  # torn paper scrap behind the [E] prompt
print("map textures imported")

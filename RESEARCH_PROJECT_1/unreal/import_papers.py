"""Bring the reading-screen sheets (and the key pictures) into Unreal: export/paper_<kind>.png (tools/make_papers.py) ->
/Game/Horror/UI/T_Paper_<Kind>, set up as sharp UI textures like the map (unreal/import_map.py)."""
import unreal

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/export/"
DEST = "/Game/Horror/UI"

for kind in ("stationery", "notebook", "typed", "ledger", "scrap",
             "key_office", "key_gate", "key_boathouse",      # the keys: tools/make_keys.py
             "register",                                     # the guest register page: tools/make_guest_book.py
             "wall", "postcard", "torn"):                            # + the postcard for the opening: tools/make_postcard.py                                        # Cas's wall close-up: tools/make_wall.py
    name = "T_Paper_" + kind.capitalize()
    t = unreal.AssetImportTask()
    t.filename = ROOT + f"paper_{kind}.png"
    t.destination_path, t.destination_name = DEST, name
    t.automated, t.save, t.replace_existing = True, True, True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = unreal.load_asset(f"{DEST}/{name}")
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_SHARPEN4)
    tex.set_editor_property("never_stream", True)
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
print("paper textures imported")

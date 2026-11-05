"""Rebuild the whole level in the right order, in one go.

Run in the Unreal editor (Tools > Execute Python Script):
  1. blockout.py       - gray-box places, lighting, fog, post-process
  2. import_scatter.py - the Maya woods (needs export/ from maya/export_to_unreal.py)
  3. ps2_look.py       - PS2 screen effect and surface material
  4. apply_textures.py - CC0 photo textures (needs textures/ from tools/fetch_textures.py)
  5. import_sets.py    - the detailed Maya motel and its lights (needs export/ from maya/make_motel.py
                         and tools/make_photos.py for the photos in Room 104)
  6. interact_setup.py - E / Tab input, BP_Examinable, BP_HorrorHUD (their graphs: tools/make_interact_nodes.py)
  7. place_clues.py    - clues, keys and locked doors from clues.json
  8. import_map.py     - the paper map for the corner of the screen (needs export/ from tools/make_map.py)
Each step can also be run on its own.
"""
import os

HERE = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/unreal"
for step in ("blockout.py", "import_scatter.py", "ps2_look.py", "apply_textures.py", "import_sets.py",
             "interact_setup.py", "place_clues.py", "import_map.py"):
    print("---", step)
    path = os.path.join(HERE, step)
    exec(compile(open(path, encoding="utf-8").read(), path, "exec"), {"__name__": "__main__", "__file__": path})

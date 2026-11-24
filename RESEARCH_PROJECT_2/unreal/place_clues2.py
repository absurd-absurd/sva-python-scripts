"""MARROW Chapter 2: put the clues from RESEARCH_PROJECT_2/clues.json into the Lakebed map.

Run in the Unreal editor with the Lakebed map open, after lakebed_level.py. Safe to run again.
Uses Chapter 1's unreal/place_clues.py (BP_Examinable, the paper cards, the aim boxes), with:
  - Chapter 2's clues.json, each clue's 'at' + yaw from export/sets_lakebed.json clue_spots
    (where make_lakebed.py / ch2_props.py built its prop)
  - 'zone_small' shapes: an invisible aim box over a built prop (the bag, the watch): the prop is the clue
  - the start objective going to BP_Ch2HUD (not Chapter 1's HUD)
"""
import json

import unreal

RP1 = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
RP2 = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_2"
data = json.load(open(f"{RP2}/clues.json", encoding="utf-8"))
spots = json.load(open(f"{RP2}/export/sets_lakebed.json"))["clue_spots"]
for c in data["clues"]:
    x, y, z, yaw = spots[c["id"]]
    c["at"] = [x, y, z]
    c.setdefault("yaw", yaw)
    c["room"] = False

src = open(f"{RP1}/unreal/place_clues.py", encoding="utf-8").read()
src = src.replace('DATA = json.load(open(ROOT + "/clues.json", encoding="utf-8"))', "DATA = CH2_DATA")
src = src.replace('"/Game/Horror/Interact/BP_HorrorHUD"', '"/Game/Chapter2/Blueprints/BP_Ch2HUD"')
src = src.replace('    "gate": ((206, 6, 176),', '    "zone_small": ((44, 40, 22), "MI_PS2_curtain_mat", (0, 0, 11)),\n    "gate": ((206, 6, 176),')
src = src.replace('if c["shape"] == "wall_zone":', 'if c["shape"] in ("wall_zone", "zone_small"):')
assert "CH2_DATA" in src and "BP_Ch2HUD" in src and "zone_small" in src
exec(compile(src, f"{RP1}/unreal/place_clues.py", "exec"), {"__name__": "__main__", "CH2_DATA": data})
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

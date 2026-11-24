# MARROW Chapter 2: Under the Lake

Research Project 2. A prequel to MARROW (Research Project 1): you play Cas, on October 17, 2001,
walking the bottom of Black Hollow Lake to find her mother. Same Unreal project as Chapter 1
(`Documents/Unreal Projects/RP1_Horror`), its own map: `/Game/Chapter2/Maps/Lakebed`.

**Status: first pass of everything (2026-11-24).** All of it works roughly; refining comes next.
The story texts are a draft (see `../RESEARCH_PROJECT_1/STORY.md`, "Chapter 2").

## What's in it
- **The lakebed** (Maya, `maya/make_lakebed.py`): a winding gully from under the old dock (8.5 m down)
  to a drop-off and a deep basin (30 m). Sand floor curving up into clay and layered-rock walls, rock
  slabs and rubble, sunken trees, rocks, boulders and plants placed with the **MIDTERM scatter tool**
  (called from the script), plants only as deep as light reaches.
- **Underwater look** (`unreal/lakebed_level.py`): Chapter 1's PS2 screen, green murk that thickens
  with depth, rippling light from the surface, light shafts, silt specks, slow heavy walking
  (`unreal/heavy_walk.py`).
- **Things that move** (one material, `M_Ch2_Sway`): plants sway, silt drifts, bubbles rise from
  seeps, fish schools mill in rings, the hunter circles, the thing in the basin breathes.
- **The story** (`maya/ch2_props.py`, `clues.json`, `unreal/place_clues2.py`): Mom's handbag, the
  1974 researchers' case and log page, Freedman's watch, Mom's coat and the last page; the red-lit
  figure that fades as you get near; the hunter (too close and it catches you: back to the checkpoint).
- **Chapter 2's HUD** (`tools/make_ch2_hud.py`, pasted into `BP_Ch2HUD`): Chapter 1's interaction
  system (E to read, papers in the right handwriting, the flashlight, title screen, opening, pause,
  ending) with Chapter 2's words, plus the hunter's catch.
- **Sound** (`tools/make_ch2_sounds.py`, `unreal/place_sounds2.py`): the deep-water rumble, the
  breathing in the basin, the hunter's clicking.

## How to rebuild it
1. `mayapy maya/make_lakebed.py` (via `maya.standalone`; about 1.5 minutes)
2. In Unreal, with `RESEARCH_PROJECT_1/tools/ue_send.py <file>`, in order:
   `unreal/lakebed_level.py`, `unreal/heavy_walk.py`, `unreal/place_start.py`,
   `unreal/place_clues2.py`, `unreal/ch2_ui.py`, `unreal/place_sounds2.py`
3. HUD logic: `python tools/make_ch2_hud.py > hud_ch2.txt`, open `BP_Ch2HUD`'s Event Graph,
   select all, delete, paste, compile.

## Recording
(to come)

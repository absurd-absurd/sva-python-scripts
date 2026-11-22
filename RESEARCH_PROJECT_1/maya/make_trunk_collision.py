"""Trunk-only collision shapes for the trees (user 2026-11-22: "trees in the forest so far apart but I still
can't walk in between them": the trees collided with a shell round the whole tree, lowest branches included -
a big pine blocked about 2 m out at ankle height, 3 m at chest height).

One plain cylinder per tree kind, the size of the bottom of the trunk (0.75 of maya/make_trees.py's trunk
radius, 260 cm tall, base at 0), written to export/trees/trunkcol_<name>.fbx. unreal/tree_collision.py sets each
as its tree's complex-collision mesh and makes the tree collide with that alone.

    mayapy maya/make_trunk_collision.py      (maya.standalone, see scratchpad run_*.py)
"""
import os
import maya.cmds as cmds
import maya.mel as mel

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "export", "trees")
TRUNKS = {"tree_pine_A": (2300, 0.016), "tree_pine_B": (2800, 0.016), "tree_leafy_A": (2200, 0.026),
          "tree_leafy_B": (2500, 0.026), "tree_dead_C": (2100, 0.026), "tree_dead_A": (1900, 0.026),
          "tree_dead_B": (1600, 0.026), "tree_dead_pine": (2400, 0.016)}      # = make_trees.TREES (height, trunk ratio)
SHRINK, HEIGHT = 0.75, 260.0

cmds.loadPlugin("fbxmaya", quiet=True)
os.makedirs(OUT, exist_ok=True)
for name, (h, rf) in TRUNKS.items():
    cmds.file(new=True, force=True)
    c = cmds.polyCylinder(r=h * rf * SHRINK, h=HEIGHT, sx=12, sy=1, sz=1, ch=False)[0]
    cmds.move(0, HEIGHT / 2.0, 0, c)                          # base at 0 (Maya y up = Unreal z up)
    cmds.makeIdentity(c, apply=True, t=True)
    c = cmds.rename(c, "trunkcol_" + name)
    cmds.select(c)
    mel.eval("FBXResetExport")
    f = os.path.join(OUT, f"trunkcol_{name}.fbx").replace("\\", "/")
    cmds.file(f, force=True, options="v=0;", type="FBX export", exportSelected=True)
    print("wrote", f, "radius", round(h * rf * SHRINK, 1))

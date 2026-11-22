"""Split the Fab "Leather Boots" pair (one mesh) into two meshes, so one boot can stand and the other lie on its
side (user 2026-11-22: "put one laying down like the last boots that we had").

    mayapy tools/split_boots.py   (reads export/boots/top_boots.fbx, exported from Unreal by unreal/place_boots.py's notes)
    -> export/boots/boot_left.fbx, export/boots/boot_right.fbx  (same coordinates as the pair; Unreal imports them)
"""
import os
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds
import maya.mel as mel

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "export", "boots").replace("\\", "/")
cmds.loadPlugin("fbxmaya", quiet=True)
cmds.file(new=True, force=True)
cmds.file(D + "/top_boots.fbx", i=True, type="FBX", ignoreVersion=True)
mesh = [t for t in cmds.ls(type="transform") if cmds.listRelatives(t, shapes=True, type="mesh")][0]
parts = cmds.polySeparate(mesh, ch=False)
parts = [p for p in parts if cmds.listRelatives(p, shapes=True, type="mesh")]
# the two biggest shells are the boots; any small loose shells join the boot they sit closest to
def cx(p):
    b = cmds.exactWorldBoundingBox(p)
    return (b[0] + b[3]) / 2.0
left = [p for p in parts if cx(p) < 0]
right = [p for p in parts if cx(p) >= 0]
print("shells", len(parts), "left", len(left), "right", len(right))
for name, group in (("boot_left", left), ("boot_right", right)):
    obj = cmds.polyUnite(group, ch=False, name=name)[0] if len(group) > 1 else cmds.rename(group[0], name)
    cmds.select(obj)
    mel.eval("FBXResetExport")
    mel.eval("FBXExportSmoothingGroups -v true")
    cmds.file(D + "/" + name + ".fbx", force=True, options="v=0;", type="FBX export", exportSelected=True)
    print("wrote", name, cmds.exactWorldBoundingBox(obj))

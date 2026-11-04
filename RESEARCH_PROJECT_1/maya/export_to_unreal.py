"""Export the scattered woods from Maya for Unreal.

Run in Maya after Apply in the scatter tool (Python tab):
    exec(open(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/maya/export_to_unreal.py").read())

Writes to RESEARCH_PROJECT_1/export/:
  - one FBX per prop that was used (moved to the origin first, so Unreal gets the bare mesh)
  - scatter.json: for every copy, which prop it is, its network, and its world matrix

The Unreal side (unreal/import_scatter.py) reads these and rebuilds the woods.
Only scatter_grp# groups (made by Apply) are exported, not a Preview.
"""
import json
import os
import re

import maya.cmds as cmds
import maya.mel as mel

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
OUT = os.path.join(ROOT, "export")


def prop_sources():
    """{asset name: prop node} for every prop that make_woods.py tagged."""
    found = {}
    for node in cmds.ls("*.ue_asset", objectsOnly=True, long=True, recursive=True) or []:
        if "scatter_grp" not in node:          # copies live under scatter_grp#; the originals don't
            found[cmds.getAttr(node + ".ue_asset")] = node
    return found


def asset_of(copy, sources):
    """Which prop a scatter copy came from."""
    if cmds.attributeQuery("ue_asset", node=copy, exists=True):      # a duplicate keeps the tag
        return cmds.getAttr(copy + ".ue_asset")
    short = copy.split("|")[-1]
    base = re.sub(r"_inst\d*$", "", short)                            # an instance: tree_dead_A_inst12
    return base if base in sources else None


def export_prop(asset, node, path):
    dup = cmds.duplicate(node, name=asset + "_export")[0]
    if cmds.listRelatives(dup, parent=True):
        dup = cmds.parent(dup, world=True)[0]
    cmds.xform(dup, translation=(0, 0, 0), worldSpace=True)
    cmds.select(dup)
    mel.eval("FBXResetExport")
    mel.eval("FBXExportSmoothingGroups -v true")
    mel.eval('FBXExport -f "{}" -s'.format(path.replace("\\", "/")))
    cmds.delete(dup)


def export():
    if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
        cmds.loadPlugin("fbxmaya")
    groups = [g for g in cmds.ls("scatter_grp*", long=True, type="transform") if g.count("|") == 1]
    if not groups:
        cmds.warning("No scatter_grp found. Press Apply in the scatter tool first.")
        return
    sources = prop_sources()
    copies, unknown = [], 0
    for g in groups:
        for net in cmds.listRelatives(g, children=True, fullPath=True, type="transform") or []:
            network = net.split("|")[-1]
            for c in cmds.listRelatives(net, children=True, fullPath=True, type="transform") or []:
                asset = asset_of(c, sources)
                if asset is None:
                    unknown += 1
                    continue
                copies.append({"asset": asset, "network": network,
                               "matrix": cmds.xform(c, q=True, matrix=True, worldSpace=True)})

    os.makedirs(OUT, exist_ok=True)
    used = sorted({c["asset"] for c in copies})
    props = {}
    for asset in used:
        path = os.path.join(OUT, asset + ".fbx")
        export_prop(asset, sources[asset], path)
        props[asset] = path.replace("\\", "/")
    with open(os.path.join(OUT, "scatter.json"), "w") as f:
        json.dump({"props": props, "copies": copies}, f, indent=1)
    msg = "Exported {} copies of {} props to {}".format(len(copies), len(used), OUT)
    if unknown:
        msg += " ({} copies skipped: not made from a tagged prop)".format(unknown)
    print(msg)
    cmds.inViewMessage(amg=msg, pos="topCenter", fade=True)


export()

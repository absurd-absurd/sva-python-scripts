"""Grass made of real blades, as patches for Unreal to scatter (unreal/grass.py), which sways in
the wind and parts around you as you walk through it (the material bends every blade by how high
up the blade the vertex is: the bottom stays planted, the tip moves most).

Run with mayapy (or in Maya):
    exec(open(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/maya/make_grass.py").read())

Each blade: a tapered, curving strip of 3 triangles (wide base, narrower middle, a point),
leaning and bowed a little in its own direction. Blades grow in tufts (clumps); tufts make patches:
- grass_dense_A/B: 4 x 4 m of thick grass (verges, road edges, the yard, along the trail)
- grass_sparse_A/B: 8 x 8 m of looser tufts and single blades (the forest floor)
Two materials so the grass isn't one flat colour: grass_green_mat, grass_dry_mat (straw).
Built with Maya's API in one go (fast). Writes export/grass_*.fbx; pivots at the patch centre on
the ground. Unreal (x, y, z) = Maya (x, z, y).
"""
import math
import os
import random

import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
OUT = os.path.join(ROOT, "export")
MATS = {"grass_green_mat": (0.16, 0.2, 0.08), "grass_dry_mat": (0.3, 0.26, 0.14)}


def material(name, rgb):
    if not cmds.objExists(name):
        cmds.shadingNode("lambert", asShader=True, name=name)
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name + "SG")
        cmds.connectAttr(name + ".outColor", sg + ".surfaceShader")
    cmds.setAttr(name + ".color", *rgb, type="double3")


def blade(pts, faces, x, y, rng, h_rng, w_rng):
    """Append one blade's 5 vertices and its 2 faces (a quad and the tip triangle)."""
    h = rng.uniform(*h_rng)
    w = rng.uniform(*w_rng)
    a = rng.uniform(0, 2 * math.pi)                         # which way it faces
    lean = rng.uniform(0.05, 0.35) * h                      # how far the tip leans out
    la = a + rng.uniform(-0.6, 0.6) + math.pi / 2
    cx, cy = math.cos(a), math.sin(a)                       # across the blade
    lx, ly = math.cos(la), math.sin(la)                     # the lean direction
    def at(t, half):
        bend = lean * t * t                                 # bows more toward the tip
        return (x + cx * half + lx * bend, y + cy * half + ly * bend, h * t * (1 - 0.15 * t * t))
    i = len(pts)
    for t, half in ((0.0, w / 2.0), (0.0, -w / 2.0), (0.55, w * 0.32), (0.55, -w * 0.32)):
        pts.append(at(t, half))
    pts.append(at(1.0, 0.0))
    faces.append((i, i + 1, i + 3, i + 2))
    faces.append((i + 2, i + 3, i + 4))


def mesh_from(name, pts, faces, mat):
    verts = om.MFloatPointArray([om.MFloatPoint(p[0], p[2], p[1]) for p in pts])   # Unreal -> Maya
    counts = om.MIntArray([len(f) for f in faces])
    conn = om.MIntArray([v for f in faces for v in f])
    obj = om.MFnMesh().create(verts, counts, conn)         # returns the new transform
    tr = cmds.rename(om.MFnDagNode(obj).fullPathName(), name)
    cmds.sets(tr, edit=True, forceElement=mat + "SG")
    cmds.polySoftEdge(tr, angle=180, ch=False)               # smooth shading across each blade
    return tr


def patch(name, size, tufts, singles, seed, tall=1.0):
    rng = random.Random(seed)
    parts = {m: ([], []) for m in MATS}
    half = size / 2.0
    for _ in range(tufts):
        tx, ty = rng.uniform(-half, half), rng.uniform(-half, half)
        dry = rng.random() < 0.35
        m = "grass_dry_mat" if dry else "grass_green_mat"
        n = rng.randint(9, 16)
        r = rng.uniform(5, 14)
        hh = (rng.uniform(22, 40) * tall, rng.uniform(40, 62) * tall)
        for _ in range(n):
            ang, rr = rng.uniform(0, 6.283), r * math.sqrt(rng.random())
            pts, faces = parts[m]
            blade(pts, faces, tx + math.cos(ang) * rr, ty + math.sin(ang) * rr, rng, hh, (1.4, 2.6))
    for _ in range(singles):
        m = "grass_dry_mat" if rng.random() < 0.4 else "grass_green_mat"
        pts, faces = parts[m]
        blade(pts, faces, rng.uniform(-half, half), rng.uniform(-half, half), rng, (14 * tall, 34 * tall), (1.2, 2.2))
    meshes = [mesh_from(name + "_" + m.split("_")[1], pts, faces, m) for m, (pts, faces) in parts.items() if pts]
    out = cmds.polyUnite(meshes, name=name, ch=False)[0] if len(meshes) > 1 else cmds.rename(meshes[0], name)
    cmds.delete(out, constructionHistory=True)
    cmds.xform(out, pivots=(0, 0, 0), worldSpace=True)
    return out


def build():
    cmds.file(new=True, force=True)
    for n, rgb in MATS.items():
        material(n, rgb)
    if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
        cmds.loadPlugin("fbxmaya")
    made = []
    for name, size, tufts, singles, seed, tall in (("grass_dense_A", 400, 70, 160, 1, 1.0),
                                                   ("grass_dense_B", 400, 64, 200, 2, 1.15),
                                                   ("grass_sparse_A", 800, 75, 300, 3, 0.9),
                                                   ("grass_sparse_B", 800, 65, 340, 4, 0.8)):
        m = patch(name, size, tufts, singles, seed, tall)
        f = os.path.join(OUT, name + ".fbx").replace("\\", "/")
        cmds.select(m)
        mel.eval("FBXResetExport")
        mel.eval('FBXExport -f "{}" -s'.format(f))
        made.append((name, cmds.polyEvaluate(m, triangle=True)))
        cmds.delete(m)
    print("grass patches:", made)


build()

"""Realistic trees for the woods, after the reference photos (process/refs/): tall straight dark
trunks, the crown high overhead, bare trunks below it. Eight kinds, replacing the old low-poly
blocks under the same names, so the scatter tool's woods and the forest fill both use them:

  tree_pine_A      spruce, full: straight to the tip, drooping whorls of needle sprays up top,
                   dead stubs lower down
  tree_pine_B      a taller, thinner spruce
  tree_leafy_A     beech, full: the trunk forks high into big limbs, a dense leafy crown
  tree_leafy_B     beech, thinner crown (light shows through)
  tree_dead_C      dying: the same branching, a few brown leaves left
  tree_dead_A      dead, bare: gnarled limbs, no leaves
  tree_dead_B      dead, bare, the top snapped off
  tree_dead_pine   dead spruce: bare whorls, a few rust-brown needle sprays

Trunks and branches are real tapered tubes that split into limbs, branches and twigs. The
leaves and needles are cards: flat panels with a leaf-cluster picture (tools/make_foliage.py),
two crossed at each spot, the usual way games make trees. Materials: tree_bark_mat,
tree_leaves_mat (green), tree_dead_leaves_mat (brown), tree_needles_mat, tree_dead_needles_mat.
Each tree also gets a UCX_ collision cylinder round the bottom of its trunk (you bump into the
trunk, never into the crown). unreal/trees.py imports them.

Run with mayapy (or in Maya):
    exec(open(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/maya/make_trees.py").read())
Writes export/trees/<name>.fbx. Built at the origin, base at z 0, Unreal (x, y, z) = Maya (x, z, y).
"""
import math
import os
import random

import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
OUT = os.path.join(ROOT, "export", "trees")
MATS = {"tree_bark_mat": (0.12, 0.1, 0.08), "tree_leaves_mat": (0.3, 0.4, 0.18),
        "tree_dead_leaves_mat": (0.4, 0.28, 0.14), "tree_needles_mat": (0.18, 0.3, 0.2),
        "tree_dead_needles_mat": (0.38, 0.25, 0.14), "fern_mat": (0.25, 0.4, 0.15)}


# ---------- small vector maths ----------

def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    l = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


def perp(d):
    """Two unit vectors at right angles to d."""
    u = norm(cross(d, (0, 0, 1) if abs(d[2]) < 0.95 else (1, 0, 0)))
    return u, norm(cross(d, u))


def turn(d, rng, amount, up=0.0):
    """d nudged in a random direction by about `amount`, plus `up` (negative = droop)."""
    u, v = perp(d)
    a = rng.uniform(0, 2 * math.pi)
    return norm(add(add(d, mul(add(mul(u, math.cos(a)), mul(v, math.sin(a))), amount)), (0, 0, up)))


# ---------- geometry, per material ----------

class Geo:
    def __init__(self, centre=(0, 0, 0)):
        self.parts = {}                                    # mat -> (verts, uvs, faces)
        self.centre = centre                               # foliage normals point away from here

    def _p(self, mat):
        return self.parts.setdefault(mat, ([], [], []))

    def tube(self, pts, radii, sides, mat="tree_bark_mat"):
        """A tapered tube through pts (closed at the tip only if its radius is ~0)."""
        verts, uvs, faces = self._p(mat)
        base = len(verts)
        length = 0.0
        prev_u = None
        for i, (p, r) in enumerate(zip(pts, radii)):
            d = norm(sub(pts[min(i + 1, len(pts) - 1)], pts[max(i - 1, 0)]))
            u, v = perp(d) if prev_u is None else (norm(sub(prev_u, mul(d, dot(prev_u, d)))), None)
            if v is None:
                v = norm(cross(d, u))
            prev_u = u
            if i:
                length += math.dist(pts[i], pts[i - 1])
            for k in range(sides + 1):                     # one extra column so the UV seam wraps
                a = 2 * math.pi * k / sides
                off = add(mul(u, math.cos(a) * r), mul(v, math.sin(a) * r))
                verts.append(add(p, off))
                uvs.append((k / float(sides), length / 120.0))
        n = sides + 1
        for i in range(len(pts) - 1):
            for k in range(sides):
                a = base + i * n + k
                faces.append((a, a + 1, a + n + 1, a + n))

    def card(self, c, right, up, w, h, mat):
        """A flat foliage panel centred at c, the picture's bottom at c - up * h/2."""
        verts, uvs, faces = self._p(mat)
        i = len(verts)
        for sx, sy, uv in ((-1, -1, (0, 0)), (1, -1, (1, 0)), (1, 1, (1, 1)), (-1, 1, (0, 1))):
            verts.append(add(c, add(mul(right, sx * w / 2.0), mul(up, sy * h / 2.0))))
            uvs.append(uv)
        faces.append((i, i + 1, i + 2, i + 3))

    def spray(self, base, direction, size, mat, rng, flat=False):
        """Two crossed cards growing from base along direction (a cluster of leaves / needles)."""
        d = norm(direction)
        u, v = perp(d)
        a = rng.uniform(0, math.pi)
        r1 = add(mul(u, math.cos(a)), mul(v, math.sin(a)))
        r2 = norm(cross(d, r1))
        c = add(base, mul(d, size * 0.45))
        if flat:                                           # pine sprays lie mostly flat, facing up
            r1 = norm((r1[0], r1[1], r1[2] * 0.2))
        self.card(c, r1, d, size * 0.85, size, mat)
        self.card(c, r2, d, size * 0.85, size, mat)

    def build(self, name):
        made = []
        for mat, (verts, uvs, faces) in self.parts.items():
            if not faces:
                continue
            pts = om.MFloatPointArray([om.MFloatPoint(p[0], p[2], p[1]) for p in verts])   # Unreal -> Maya
            counts = om.MIntArray([len(f) for f in faces])
            conn = om.MIntArray([i for f in faces for i in f])
            fn = om.MFnMesh()
            obj = fn.create(pts, counts, conn, om.MFloatArray([u for u, v in uvs]), om.MFloatArray([v for u, v in uvs]))
            fn.assignUVs(counts, conn)
            tr = cmds.rename(om.MFnDagNode(obj).fullPathName(), name + "_" + mat)
            cmds.polyNormal(tr, normalMode=0, userNormalMode=0, ch=False)   # Maya builds these inside-out
            cmds.polySoftEdge(tr, angle=80 if "bark" in mat else 180, ch=False)
            if "bark" not in mat:
                # leaves light like one leafy mass: every card's normal points out from the middle
                # of the crown (flat cards facing sideways were black on their shady side)
                c = self.centre
                ns = om.MVectorArray()
                ids = om.MIntArray()
                for i, p in enumerate(verts):
                    d = norm(sub(p, c))
                    ns.append(om.MVector(d[0], d[2], d[1]))
                    ids.append(i)
                sel = om.MSelectionList()
                sel.add(tr)
                om.MFnMesh(sel.getDagPath(0)).setVertexNormals(ns, ids)
            cmds.sets(tr, edit=True, forceElement=mat + "SG")
            made.append(tr)
        mesh = cmds.polyUnite(made, name=name, ch=False)[0] if len(made) > 1 else cmds.rename(made[0], name)
        cmds.delete(mesh, constructionHistory=True)
        cmds.xform(mesh, pivots=(0, 0, 0), worldSpace=True)
        return mesh


# ---------- growing ----------

def limb(g, rng, p, d, length, r0, r1, segs, sides, bend=0.12, up=0.0):
    """One curving tapered limb from p along d; returns its points (for children)."""
    pts, radii = [p], [r0]
    for k in range(1, segs + 1):
        d = turn(d, rng, bend, up)
        p = add(p, mul(d, length / segs))
        pts.append(p)
        radii.append(r0 + (r1 - r0) * k / segs)
    g.tube(pts, radii, sides)
    return pts, d


def broadleaf(g, rng, height, leaves, mat, broken=False):
    """A beech: a straight trunk to ~55-60 %, forking into 3-5 big limbs that climb and spread,
    each splitting into branches and twigs; leaf sprays on the twigs. leaves = sprays per twig
    (0 = bare). broken: the top half of the crown snapped off."""
    fork = height * rng.uniform(0.52, 0.6)
    r = height * 0.026
    # trunk with a root flare
    pts, radii = [], []
    for k in range(9):
        t = k / 8.0
        z = fork * t
        pts.append((rng.uniform(-3, 3) * t, rng.uniform(-3, 3) * t, z))
        radii.append(r * (1.0 - 0.3 * t) * (1.0 + 0.6 * max(0.0, 0.12 - t) / 0.12))
    g.tube(pts, radii, 10)
    for _ in range(4):                                     # root flares
        a = rng.uniform(0, 2 * math.pi)
        o = (math.cos(a), math.sin(a), 0)
        g.tube([add(mul(o, r * 0.4), (0, 0, 40)), add(mul(o, r * 1.4), (0, 0, 2)), add(mul(o, r * 2.1), (0, 0, -6))],
               [r * 0.45, r * 0.3, r * 0.12], 6)
    top = pts[-1]
    tips = []
    n_limbs = rng.randint(3, 5)
    for i in range(n_limbs):
        a = 2 * math.pi * i / n_limbs + rng.uniform(-0.4, 0.4)
        d = norm((math.cos(a) * 0.55, math.sin(a) * 0.55, 1.0))
        L = (height - fork) * rng.uniform(0.75, 1.0)
        if broken and i % 2 == 0:
            L *= 0.35                                      # snapped
        lp, ld = limb(g, rng, top, d, L, r * 0.6, r * 0.18, 5, 7, bend=0.18)
        if broken and i % 2 == 0:
            continue
        # branches off each limb, and twigs off each branch
        for j in range(rng.randint(4, 6)):
            t = rng.uniform(0.3, 1.0)
            bp = lp[min(len(lp) - 1, int(t * (len(lp) - 1)))]
            bd = turn(ld, rng, 0.9, up=-0.05)
            bl = L * rng.uniform(0.35, 0.55)
            bpts, bdir = limb(g, rng, bp, bd, bl, r * 0.16, r * 0.05, 3, 5, bend=0.25)
            for q in range(3):
                tp = bpts[rng.randint(1, len(bpts) - 1)]
                td = turn(bdir, rng, 0.8, up=0.1)
                tpts, tdir = limb(g, rng, tp, td, bl * 0.4, r * 0.05, r * 0.015, 2, 4, bend=0.3)
                tips.append((tpts[-1], tdir))
                tips.append((tpts[1], tdir))
    for p, d in tips:
        for _ in range(leaves):
            if leaves < 1:
                break
            g.spray(add(p, (rng.uniform(-40, 40), rng.uniform(-40, 40), rng.uniform(-30, 30))),
                    turn(d, rng, 0.9, up=0.2), rng.uniform(150, 230), mat, rng)


def spruce(g, rng, height, density, mat, dead=False):
    """A spruce: a straight trunk to the tip; whorls of branches only in the top 45 % that droop
    and turn up at the ends, shorter toward the top; dead stubs lower down. Needle sprays along
    every branch (density 0..1); dead = bare whorls, a few brown sprays."""
    r = height * 0.016
    pts = [(0, 0, height * t / 10.0) for t in range(11)]
    g.tube(pts, [r * (1 - 0.95 * t / 10.0) * (1.25 if t == 0 else 1.0) for t in range(11)], 8)
    for z in range(int(height * 0.12), int(height * 0.55), 55):        # dead stubs on the bare trunk
        for _ in range(rng.randint(1, 3)):
            a = rng.uniform(0, 2 * math.pi)
            d = norm((math.cos(a), math.sin(a), rng.uniform(-0.3, 0.1)))
            p = (0, 0, z + rng.uniform(-20, 20))
            g.tube([add(p, mul(d, r * 0.6)), add(p, mul(d, r + rng.uniform(25, 70)))], [r * 0.12, r * 0.04], 4)
    z = height * 0.55
    while z < height * 0.97:
        t = (z - height * 0.55) / (height * 0.45)
        reach = height * 0.2 * (1 - t) ** 0.9 + 40
        for i in range(rng.randint(5, 7)):
            a = 2 * math.pi * i / 6.0 + rng.uniform(-0.3, 0.3)
            d = norm((math.cos(a), math.sin(a), -0.15))
            p = (0, 0, z)
            L = reach * rng.uniform(0.8, 1.1) * (0.55 if dead else 1.0)
            bpts, bdir = limb(g, rng, p, d, L, r * 0.16 * (1 - t * 0.6), r * 0.03, 3, 4, bend=0.12, up=-0.08)
            if dead:
                if rng.random() < 0.15:
                    g.spray(bpts[-1], add(bdir, (0, 0, 0.3)), rng.uniform(90, 140), mat, rng, flat=True)
                continue
            n = int(L / 70) + 1
            for k in range(n):
                if rng.random() > density:
                    continue
                q = bpts[min(len(bpts) - 1, 1 + k * (len(bpts) - 1) // n)]
                g.spray(q, add(bdir, (0, 0, 0.35)), rng.uniform(110, 170) * (1 - 0.35 * t), mat, rng, flat=True)
        z += rng.uniform(60, 90) * (1 - 0.4 * t)
    if not dead:                                            # the leader at the very top
        g.spray((0, 0, height * 0.94), (0, 0, 1), 140, mat, rng)


def fern_clump(g, rng, fronds):
    """A fern: fronds arching up and out from one root, each a card of tools/make_foliage.py's
    frond picture, two crossed per frond so it has body from every side."""
    for i in range(fronds):
        a = 2 * math.pi * i / fronds + rng.uniform(-0.3, 0.3)
        out = (math.cos(a), math.sin(a), 0)
        rise = rng.uniform(0.6, 1.4)
        d = norm((out[0], out[1], rise))
        L = rng.uniform(80, 130)
        c = add(mul(d, L * 0.5), (0, 0, 2))
        right = norm(cross(d, (0, 0, 1)))
        flat = norm(cross(right, d))
        g.card(c, right, d, L * 0.55, L, "fern_mat")
        g.card(c, norm(add(mul(right, 0.4), mul(flat, 0.9))), d, L * 0.45, L, "fern_mat")


def twiggy_shrub(g, rng, size, leaves):
    """A dead / winter shrub: thin stems from one root splitting into twigs, a few brown leaves."""
    for i in range(rng.randint(6, 9)):
        a = rng.uniform(0, 2 * math.pi)
        d = norm((math.cos(a) * 0.5, math.sin(a) * 0.5, 1.0))
        pts, dd = limb(g, rng, (0, 0, 0), d, size * rng.uniform(0.6, 1.0), 2.2, 0.6, 3, 4, bend=0.25)
        for k in range(rng.randint(2, 4)):
            p = pts[rng.randint(1, len(pts) - 1)]
            tp, td = limb(g, rng, p, turn(dd, rng, 0.9), size * 0.35, 0.8, 0.25, 2, 3, bend=0.35)
            if rng.random() < leaves:
                g.spray(tp[-1], td, rng.uniform(35, 55), "tree_dead_leaves_mat", rng)


def collision(name, height, radius):
    c = cmds.polyCylinder(r=radius * 1.1, h=260, sx=8, sy=1, sz=0, ch=False)[0]
    cmds.move(0, 130, 0, c)
    cmds.makeIdentity(c, apply=True, t=True)
    return cmds.rename(c, "UCX_" + name + "_00")


TREES = [
    ("tree_pine_A",    lambda g, r: spruce(g, r, 2300, 0.9, "tree_needles_mat"), 2300, 0.016),
    ("tree_pine_B",    lambda g, r: spruce(g, r, 2800, 0.6, "tree_needles_mat"), 2800, 0.016),
    ("tree_leafy_A",   lambda g, r: broadleaf(g, r, 2200, 3, "tree_leaves_mat"), 2200, 0.026),
    ("tree_leafy_B",   lambda g, r: broadleaf(g, r, 2500, 1, "tree_leaves_mat"), 2500, 0.026),
    ("tree_dead_C",    lambda g, r: broadleaf(g, r, 2100, 1 if r.random() < 2 else 0, "tree_dead_leaves_mat"), 2100, 0.026),
    ("tree_dead_A",    lambda g, r: broadleaf(g, r, 1900, 0, "tree_leaves_mat"), 1900, 0.026),
    ("tree_dead_B",    lambda g, r: broadleaf(g, r, 1600, 0, "tree_leaves_mat", broken=True), 1600, 0.026),
    ("tree_dead_pine", lambda g, r: spruce(g, r, 2400, 0.0, "tree_dead_needles_mat", dead=True), 2400, 0.016),
    # the forest floor (no collision: you walk through them)
    ("bush_A",         lambda g, r: fern_clump(g, r, 11), 0, 0),
    ("shrub_dead_A",   lambda g, r: twiggy_shrub(g, r, 120, 0.35), 0, 0),
    ("shrub_dead_B",   lambda g, r: twiggy_shrub(g, r, 85, 0.0), 0, 0),
]


def material(name, rgb):
    if not cmds.objExists(name):
        cmds.shadingNode("lambert", asShader=True, name=name)
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name + "SG")
        cmds.connectAttr(name + ".outColor", sg + ".surfaceShader")
    cmds.setAttr(name + ".color", *rgb, type="double3")


def build():
    cmds.file(new=True, force=True)
    for n, rgb in MATS.items():
        material(n, rgb)
    if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
        cmds.loadPlugin("fbxmaya")
    os.makedirs(OUT, exist_ok=True)
    report = []
    for i, (name, grow, height, rf) in enumerate(TREES):
        g = Geo(centre=(0, 0, height * 0.72) if height else (0, 0, -60))
        grow(g, random.Random(100 + i))
        mesh = g.build(name)
        col = collision(name, height, height * rf) if height else None
        f = os.path.join(OUT, name + ".fbx").replace("\\", "/")
        cmds.select([mesh, col] if col else [mesh])
        mel.eval("FBXResetExport")
        mel.eval("FBXExportSmoothingGroups -v true")
        mel.eval('FBXExport -f "{}" -s'.format(f))
        report.append((name, cmds.polyEvaluate(mesh, triangle=True)))
        cmds.delete([mesh, col] if col else [mesh])
    print("trees:", report)


build()

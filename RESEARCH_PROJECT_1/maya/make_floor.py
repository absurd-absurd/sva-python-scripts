"""The forest floor: what lies on the ground between the trees.

  litter_leaves_A / _B   a ragged patch of fallen leaves (3 m / 2.2 m), a flat card with the
                         picture from tools/make_litter.py (see-through between the leaves)
  litter_needles_A       a patch of dead pine needles and cones (2.6 m)
  stick_A                one fallen stick, slightly bent
  stick_B                a forked stick with a couple of side twigs
  stick_C                three sticks lying across each other
  branch_A               a big fallen branch (3.4 m) with its side branches, one end propped up
  stump_cut              a sawn-off stump: flat pale top, roots flaring into the ground
                         (where trees were cut for the lookout tower's view)
  slash_pile             a heap of cut branches and dead needle sprays left by the loggers

Same Geo / limb helpers as maya/make_trees.py (its code is run here without its build step), so
the sticks share the trees' bark material (tree_bark_mat). The litter cards use
litter_leaves_mat / litter_needles_mat; the stump top stump_top_mat.

Run with mayapy (or in Maya):
    exec(open(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/maya/make_floor.py").read())
Writes export/floor/<name>.fbx (built at the origin, ground at z 0). unreal/forest_floor.py imports
and places them.
"""
import math
import os
import random

import maya.cmds as cmds
import maya.mel as mel

_TREES = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/maya/make_trees.py"
_src = open(_TREES).read()
exec(_src[:_src.rindex("\nbuild()")])            # Geo, limb, spray, material(), MATS ... (not the tree build)

OUT = os.path.join(ROOT, "export", "floor")
FLOOR_MATS = {"tree_bark_mat": (0.12, 0.1, 0.08), "tree_dead_needles_mat": (0.38, 0.25, 0.14),
              "litter_leaves_mat": (0.3, 0.2, 0.1), "litter_needles_mat": (0.3, 0.2, 0.1),
              "stump_top_mat": (0.45, 0.36, 0.25)}
DOWN = (0, 0, -100000)                            # card normals point straight up (away from far below)


def litter(g, rng, size, mat):
    """A flat card lying on the ground, the picture's middle at the origin."""
    g.card((0, 0, 0), (1, 0, 0), (0, 1, 0), size, size, mat)


def lying(g, rng, p, ang, length, r0, r1, rise=0.0, bend=0.1):
    """A stick lying along the ground from p (its underside touching the ground)."""
    d = norm((math.cos(ang), math.sin(ang), rise))
    pts, radii = [], []
    segs = max(3, int(length / 25))
    q = (p[0], p[1], r0 * 0.8)
    for k in range(segs + 1):
        t = k / float(segs)
        r = r0 + (r1 - r0) * t
        pts.append((q[0], q[1], max(r * 0.8, q[2])))
        radii.append(r)
        side = rng.uniform(-bend, bend)
        d = norm((d[0] - d[1] * side, d[1] + d[0] * side, d[2]))
        q = add(q, mul(d, length / segs))
    g.tube(pts, radii, 6)
    return pts


def stick_one(g, rng):
    lying(g, rng, (-45, 0, 0), rng.uniform(-0.2, 0.2), 95, 2.4, 1.0)


def stick_forked(g, rng):
    pts = lying(g, rng, (-70, 0, 0), 0.0, 140, 3.0, 1.0)
    for k in (2, 4):
        p = pts[k]
        a = rng.choice((-1, 1)) * rng.uniform(0.4, 0.8)
        lying(g, rng, (p[0], p[1], 0), a, rng.uniform(35, 60), 1.4, 0.5, bend=0.2)


def stick_bundle(g, rng):
    for i in range(3):
        a = rng.uniform(0, math.pi)
        L = rng.uniform(70, 110)
        lying(g, rng, (-math.cos(a) * L / 2, -math.sin(a) * L / 2, 0), a, L, rng.uniform(1.6, 2.6), 0.8,
              rise=0.03 * i)


def fallen_branch(g, rng):
    """A big branch lying on the ground, its thick end propped up on its own side branches."""
    L = 340.0
    pts, radii = [], []
    for k in range(9):
        t = k / 8.0
        pts.append((-L / 2 + L * t + rng.uniform(-4, 4), rng.uniform(-10, 10) + 15 * math.sin(t * 3), 22 * (1 - t) + 4))
        radii.append(7.5 - 5.5 * t)
    g.tube(pts, radii, 7)
    for k in range(1, 8):
        p = pts[k]
        side = 1 if k % 2 else -1
        d = norm((rng.uniform(0.2, 0.8), side * rng.uniform(0.6, 1.0), rng.uniform(-0.25, 0.35)))
        bp, bd = limb(g, rng, p, d, rng.uniform(60, 130) * (1 - k / 10.0), radii[k] * 0.45, 0.6, 3, 5, bend=0.25)
        for j in range(2):
            limb(g, rng, bp[-1], turn(bd, rng, 0.8), rng.uniform(20, 40), 0.9, 0.3, 2, 3, bend=0.4)


def stump(g, rng, radius=27.0, height=48.0):
    """Sawn stump: a short trunk flaring at the bottom, a flat pale cut on top, roots."""
    pts = [(0, 0, -12), (0, 0, 4), (0, 0, 14), (0, 0, height)]
    g.tube(pts, [radius * 1.55, radius * 1.3, radius * 1.08, radius], 12)
    # the flat cut: a fan of triangles (slightly tilted, as a saw leaves it)
    verts, uvs, faces = g._p("stump_top_mat")
    i0 = len(verts)
    tilt = rng.uniform(-0.08, 0.08)
    verts.append((0, 0, height))
    uvs.append((0.5, 0.5))
    n = 12
    for k in range(n):
        a = 2 * math.pi * k / n
        x, y = math.cos(a) * radius * 1.01, math.sin(a) * radius * 1.01
        verts.append((x, y, height + x * tilt))
        uvs.append((0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)))
    for k in range(n):
        faces.append((i0, i0 + 1 + (k + 1) % n, i0 + 1 + k))
    # roots: thick at the trunk, diving into the ground
    for k in range(5):
        a = 2 * math.pi * (k + rng.uniform(-0.2, 0.2)) / 5
        c, s = math.cos(a), math.sin(a)
        rp = [(c * radius * 0.9, s * radius * 0.9, 12), (c * radius * 1.7, s * radius * 1.7, 4),
              (c * radius * 2.5, s * radius * 2.5, -2), (c * radius * 3.1, s * radius * 3.1, -10)]
        g.tube(rp, [radius * 0.38, radius * 0.26, radius * 0.16, radius * 0.06], 6)


def slash_pile(g, rng):
    """Cut branches heaped up, some still holding brown needle sprays."""
    for i in range(14):
        a = rng.uniform(0, math.pi * 2)
        h = rng.uniform(0, 55) * (1 - i / 20.0)
        L = rng.uniform(130, 260)
        p = (rng.uniform(-60, 60) - math.cos(a) * L / 2, rng.uniform(-50, 50) - math.sin(a) * L / 2, h + 4)
        d = norm((math.cos(a), math.sin(a), rng.uniform(-0.25, 0.25) if h > 20 else rng.uniform(0, 0.2)))
        bp, bd = limb(g, rng, p, d, L, rng.uniform(3, 6), 1.0, 4, 5, bend=0.15)
        for q in bp[1:]:
            if rng.random() < 0.6:
                tp, td = limb(g, rng, q, turn(bd, rng, 1.0), rng.uniform(30, 60), 1.2, 0.4, 2, 3, bend=0.35)
                if rng.random() < 0.55:
                    g.spray(tp[-1], td, rng.uniform(40, 70), "tree_dead_needles_mat", rng, flat=True)


PIECES = [
    ("litter_leaves_A",  lambda g, r: litter(g, r, 300, "litter_leaves_mat")),
    ("litter_leaves_B",  lambda g, r: litter(g, r, 220, "litter_leaves_mat")),
    ("litter_needles_A", lambda g, r: litter(g, r, 260, "litter_needles_mat")),
    ("stick_A",          stick_one),
    ("stick_B",          stick_forked),
    ("stick_C",          stick_bundle),
    ("branch_A",         fallen_branch),
    ("stump_cut",        stump),
    ("slash_pile",       slash_pile),
]


def build_floor():
    cmds.file(new=True, force=True)
    for n, rgb in FLOOR_MATS.items():
        material(n, rgb)
    if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
        cmds.loadPlugin("fbxmaya")
    os.makedirs(OUT, exist_ok=True)
    report = []
    for i, (name, grow) in enumerate(PIECES):
        # litter cards light as if facing straight up; branch / pile foliage as a mass round its middle
        g = Geo(centre=DOWN if name.startswith("litter") else (0, 0, -60))
        grow(g, random.Random(200 + i))
        mesh = g.build(name)
        f = os.path.join(OUT, name + ".fbx").replace("\\", "/")
        cmds.select(mesh)
        mel.eval("FBXResetExport")
        mel.eval("FBXExportSmoothingGroups -v true")
        mel.eval('FBXExport -f "{}" -s'.format(f))
        report.append((name, cmds.polyEvaluate(mesh, triangle=True)))
        cmds.delete(mesh)
    print("floor:", report)


build_floor()

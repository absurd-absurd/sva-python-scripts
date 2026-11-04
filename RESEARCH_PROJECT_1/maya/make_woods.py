"""Build the Maya side of the woods: low-poly PS2-style props and the ground to scatter on.

Run in Maya's Script Editor (Python tab):
    exec(open(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/maya/make_woods.py").read())

Makes a new scene with:
  - props: dead trees, a dead pine, dead shrubs, rocks, a stump and a log,
    each a single low-poly mesh with its pivot at the base (off to the side at x = -12000)
  - woods_ground: a flat ground matching the Unreal woods, with the trail and the
    structure spots cut out, so the scatter tool can't put anything there

Maya is Y-up and Unreal is Z-up: Unreal (x, y) is Maya (x, 0, y). Units are cm in both.
"""
import json
import math
import os
import random

import maya.cmds as cmds

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else \
    r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/maya"
LAYOUT = json.load(open(os.path.join(HERE, "..", "layout.json")))
SCENE = os.path.join(HERE, "woods_scene.ma")


# ---------- small helpers ----------

def material(name, rgb):
    if not cmds.objExists(name):
        cmds.shadingNode("lambert", asShader=True, name=name)
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name + "SG")
        cmds.connectAttr(name + ".outColor", sg + ".surfaceShader")
    cmds.setAttr(name + ".color", *rgb, type="double3")
    return name


def assign(obj, mat):
    cmds.sets(obj, edit=True, forceElement=mat + "SG")


def ring(obj, index, sides):
    return f"{obj}.vtx[{index * sides}:{index * sides + sides - 1}]"


def finish(parts, name, mat=None):
    """Combine parts into one mesh named name, pivot at the origin, no history.
    mat=None keeps the materials already on the parts (e.g. bark trunk + green leaves)."""
    mesh = cmds.polyUnite(parts, name=name, constructionHistory=False)[0] if len(parts) > 1 else cmds.rename(parts[0], name)
    cmds.delete(mesh, constructionHistory=True)
    cmds.makeIdentity(mesh, apply=True, t=True, r=True, s=True)
    cmds.xform(mesh, pivots=(0, 0, 0), worldSpace=True)
    if mat:
        assign(mesh, mat)
    cmds.addAttr(mesh, longName="ue_asset", dataType="string")
    cmds.setAttr(mesh + ".ue_asset", name, type="string")
    return mesh


def limb(rng, base, direction, length, radius, sides=4, segments=2, taper=0.2, droop=0.0):
    """A tapered cylinder from base along direction (a branch or a trunk piece)."""
    c = cmds.polyCylinder(r=radius, h=length, sx=sides, sy=segments, sz=0, ch=False)[0]
    cmds.move(0, length / 2.0, 0, c, absolute=True)
    cmds.makeIdentity(c, apply=True, t=True)
    cmds.xform(c, pivots=(0, 0, 0), worldSpace=True)   # freezing leaves the pivot mid-cylinder; put it at the base
    for i in range(segments + 1):
        f = 1.0 - (1.0 - taper) * i / segments
        y = length * i / segments
        cmds.scale(f, 1, f, ring(c, i, sides), pivot=(0, y, 0), relative=True)
        # droop: bend the far end down a little, like a dead branch sagging
        if droop and i:
            cmds.move(0, -droop * (i / segments) ** 2 * length, 0, ring(c, i, sides), relative=True)
    # point the cylinder (which grows along +Y) along direction
    dx, dy, dz = direction
    yaw = math.degrees(math.atan2(dx, dz))
    pitch = math.degrees(math.acos(max(-1, min(1, dy / math.sqrt(dx * dx + dy * dy + dz * dz)))))
    cmds.xform(c, rotation=(pitch, yaw, 0), rotateOrder="xyz")
    cmds.move(*base, c, absolute=True)
    return c


def trunk(rng, height, radius, sides=6, segments=5, lean=0.06, taper=0.25):
    """Trunk with a slight random wobble. Returns the mesh and its center line (for branches)."""
    t = cmds.polyCylinder(r=radius, h=height, sx=sides, sy=segments, sz=0, ch=False)[0]
    cmds.move(0, height / 2.0, 0, t, absolute=True)
    cmds.makeIdentity(t, apply=True, t=True)
    cmds.xform(t, pivots=(0, 0, 0), worldSpace=True)
    line, x, z = [], 0.0, 0.0
    for i in range(segments + 1):
        y = height * i / segments
        f = 1.0 - (1.0 - taper) * i / segments
        if i == 0:
            f *= 1.25                                            # flared base
        if i:
            x += rng.uniform(-lean, lean) * height / segments
            z += rng.uniform(-lean, lean) * height / segments
        cmds.scale(f, 1, f, ring(t, i, sides), pivot=(0, y, 0), relative=True)
        cmds.move(x, 0, z, ring(t, i, sides), relative=True)
        line.append((x, y, z, radius * f))
    return t, line


def point_on(line, frac):
    """A point on the trunk center line, frac 0 = base, 1 = top."""
    k = frac * (len(line) - 1)
    i = min(int(k), len(line) - 2)
    a, b, u = line[i], line[i + 1], k - i
    return tuple(a[j] + (b[j] - a[j]) * u for j in range(4))


# ---------- the props ----------

def dead_tree(name, seed, height, radius, branches):
    rng = random.Random(seed)
    t, line = trunk(rng, height, radius)
    parts = [t]
    for _ in range(branches):
        x, y, z, r = point_on(line, rng.uniform(0.35, 0.9))
        a = rng.uniform(0, math.tau)
        up = rng.uniform(0.3, 1.2)
        length = rng.uniform(0.18, 0.35) * height
        parts.append(limb(rng, (x, y, z), (math.sin(a), up, math.cos(a)), length, r * 0.45, droop=0.08))
        # a twig off the branch
        if rng.random() < 0.6:
            tip = (x + math.sin(a) * length * 0.6, y + up * length * 0.45, z + math.cos(a) * length * 0.6)
            b = a + rng.uniform(-1.0, 1.0)
            parts.append(limb(rng, tip, (math.sin(b), rng.uniform(0.4, 1.3), math.cos(b)), length * 0.45, r * 0.22, segments=1))
    return finish(parts, name, MATS["bark"])


def dead_pine(name, seed, height):
    rng = random.Random(seed)
    t, line = trunk(rng, height, 28, segments=6, lean=0.03, taper=0.08)
    parts = [t]
    for i in range(14):
        frac = 0.3 + 0.68 * i / 13
        x, y, z, r = point_on(line, frac)
        a = rng.uniform(0, math.tau)
        length = (1.0 - frac) * 0.3 * height + 60
        parts.append(limb(rng, (x, y, z), (math.sin(a), rng.uniform(-0.25, 0.1), math.cos(a)), length, 7, segments=1, taper=0.1))
    return finish(parts, name, MATS["bark_dark"])


def dead_shrub(name, seed):
    rng = random.Random(seed)
    parts = []
    for _ in range(9):
        a = rng.uniform(0, math.tau)
        out = rng.uniform(0.3, 0.9)
        parts.append(limb(rng, (0, 0, 0), (math.sin(a) * out, 1.0, math.cos(a) * out), rng.uniform(60, 130), 3.5, segments=2, taper=0.1, droop=0.05))
    return finish(parts, name, MATS["bark"])


def rock(name, seed, size):
    rng = random.Random(seed)
    r = cmds.polySphere(r=size, sx=8, sy=6, ch=False)[0]
    count = cmds.polyEvaluate(r, vertex=True)
    for i in range(count):
        p = cmds.pointPosition(f"{r}.vtx[{i}]", local=True)
        k = rng.uniform(0.8, 1.15)
        cmds.move(p[0] * k, p[1] * k * 0.6, p[2] * k, f"{r}.vtx[{i}]", absolute=True, objectSpace=True)
    cmds.move(0, size * 0.6 * 0.75, 0, r, absolute=True)      # mostly above ground, a bit sunk
    cmds.makeIdentity(r, apply=True, t=True)
    return finish([r], name, MATS["rock"])


def stump(name, seed):
    rng = random.Random(seed)
    s = cmds.polyCylinder(r=42, h=70, sx=7, sy=1, sz=0, ch=False)[0]
    cmds.move(0, 35, 0, s, absolute=True)
    cmds.makeIdentity(s, apply=True, t=True)
    cmds.scale(1.3, 1, 1.3, ring(s, 0, 7), pivot=(0, 0, 0), relative=True)
    for i in range(7):                                         # jagged broken top
        cmds.move(0, rng.uniform(-25, 15), 0, f"{s}.vtx[{7 + i}]", relative=True)
    return finish([s], name, MATS["bark"])


def log(name, seed):
    rng = random.Random(seed)
    l = limb(rng, (-260, 28, 0), (1, rng.uniform(-0.03, 0.03), 0), 520, 30, sides=6, segments=3, taper=0.75)
    return finish([l], name, MATS["bark_dark"])


def blob(rng, center, radius, squash=0.8, sides=6, rows=4):
    """A lumpy low-poly ball: a clump of leaves or a bush."""
    b = cmds.polySphere(r=radius, sx=sides, sy=rows, ch=False)[0]
    for i in range(cmds.polyEvaluate(b, vertex=True)):
        p = cmds.pointPosition(f"{b}.vtx[{i}]", local=True)
        k = rng.uniform(0.8, 1.2)
        cmds.move(p[0] * k, p[1] * k * squash, p[2] * k, f"{b}.vtx[{i}]", absolute=True, objectSpace=True)
    cmds.move(*center, b, absolute=True)
    return b


def pine(name, seed, height, tiers):
    """A living pine: a thin trunk and stacked low-poly cones of needles."""
    rng = random.Random(seed)
    t, line = trunk(rng, height * 0.95, 22, segments=3, lean=0.02, taper=0.3)
    assign(t, MATS["bark"])
    parts = [t]
    for i in range(tiers):
        frac = i / tiers
        base_y = height * (0.22 + 0.68 * frac)
        r = (1.0 - frac * 0.75) * height * 0.24
        h = height * (0.42 - 0.12 * frac)
        c = cmds.polyCone(r=r, h=h, sx=7, sy=1, ch=False)[0]
        for v in range(7):                       # ragged bottom edge
            cmds.move(0, rng.uniform(-0.12, 0.05) * h, 0, f"{c}.vtx[{v}]", relative=True)
        x, _, z, _ = point_on(line, base_y / height)
        cmds.move(x, base_y + h / 2, z, c, absolute=True)
        cmds.rotate(0, rng.uniform(0, 360), 0, c)
        assign(c, MATS["needles"])
        parts.append(c)
    return finish(parts, name)


def leafy_tree(name, seed, height, clumps):
    """A living broadleaf tree: trunk, a few branches, and lumpy clumps of leaves on top."""
    rng = random.Random(seed)
    t, line = trunk(rng, height * 0.7, 30, segments=4)
    assign(t, MATS["bark"])
    parts = [t]
    top = line[-1]
    for k in range(clumps):
        a = math.tau * k / clumps + rng.uniform(-0.4, 0.4)
        out = rng.uniform(0.08, 0.18) * height
        start = point_on(line, rng.uniform(0.6, 0.9))
        tip = (start[0] + math.sin(a) * out, start[1] + height * rng.uniform(0.12, 0.22), start[2] + math.cos(a) * out)
        br = limb(rng, start[:3], (tip[0] - start[0], tip[1] - start[1], tip[2] - start[2]),
                  math.dist(start[:3], tip), start[3] * 0.5, segments=1)
        assign(br, MATS["bark"])
        parts.append(br)
        leaves = blob(rng, tip, height * rng.uniform(0.14, 0.2))
        assign(leaves, MATS["leaves"])
        parts.append(leaves)
    crown = blob(rng, (top[0], top[1] + height * 0.12, top[2]), height * 0.22)
    assign(crown, MATS["leaves"])
    parts.append(crown)
    return finish(parts, name)


def bush(name, seed, size):
    rng = random.Random(seed)
    parts = []
    for _ in range(3):
        a, d = rng.uniform(0, math.tau), rng.uniform(0, size * 0.5)
        parts.append(blob(rng, (math.sin(a) * d, size * 0.45, math.cos(a) * d), size * rng.uniform(0.5, 0.7), squash=0.7, sides=5))
    return finish(parts, name, MATS["leaves"])


# ---------- the ground ----------

def seg_dist(px, py, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def blocked(x, y):
    trail = LAYOUT["trail"]
    if min(seg_dist(x, y, trail[i], trail[i + 1]) for i in range(len(trail) - 1)) < LAYOUT["trail_clear"]:
        return True
    return any(math.hypot(x - c["x"], y - c["y"]) < c["r"] for c in LAYOUT["clearings"])


def woods_ground(cell=200):
    w = LAYOUT["woods"]
    width, depth = w["x_max"] - w["x_min"], w["y_max"] - w["y_min"]
    sx, sz = int(width / cell), int(depth / cell)
    g = cmds.polyPlane(w=width, h=depth, sx=sx, sy=sz, ch=False, name="woods_ground")[0]
    cmds.move((w["x_min"] + w["x_max"]) / 2.0, 0, (w["y_min"] + w["y_max"]) / 2.0, g)
    cmds.makeIdentity(g, apply=True, t=True)
    cut = []
    for f in range(sx * sz):
        verts = cmds.xform(f"{g}.f[{f}]", q=True, translation=True, worldSpace=True)
        x = sum(verts[0::3]) / (len(verts) / 3)
        z = sum(verts[2::3]) / (len(verts) / 3)
        if blocked(x, z):              # Maya z is Unreal y
            cut.append(f"{g}.f[{f}]")
    cmds.delete(cut)
    assign(g, MATS["ground"])
    return g, len(cut), sx * sz


# ---------- build it ----------

def build():
    global MATS
    cmds.file(new=True, force=True)
    MATS = {
        "bark": material("bark_mat", (0.20, 0.16, 0.12)),
        "bark_dark": material("bark_dark_mat", (0.12, 0.10, 0.08)),
        "rock": material("rock_mat", (0.30, 0.30, 0.28)),
        "ground": material("ground_mat", (0.10, 0.11, 0.07)),
        "needles": material("needles_mat", (0.035, 0.08, 0.045)),
        "leaves": material("leaves_mat", (0.06, 0.11, 0.04)),
    }
    props = [
        dead_tree("tree_dead_A", 1, 1200, 34, 6),
        dead_tree("tree_dead_B", 2, 950, 28, 4),
        dead_tree("tree_dead_C", 3, 1500, 40, 7),
        dead_pine("tree_dead_pine", 4, 1700),
        dead_shrub("shrub_dead_A", 5),
        dead_shrub("shrub_dead_B", 6),
        rock("rock_A", 7, 70),
        rock("rock_B", 8, 130),
        rock("rock_C", 9, 40),
        stump("stump_A", 10),
        log("log_A", 11),
        pine("tree_pine_A", 12, 1400, 4),
        pine("tree_pine_B", 13, 1900, 5),
        leafy_tree("tree_leafy_A", 14, 1100, 3),
        leafy_tree("tree_leafy_B", 15, 1400, 4),
        bush("bush_A", 16, 120),
    ]
    # line the props up off to the side, like the midterm test scene
    for i, p in enumerate(props):
        cmds.move(-12000, 0, 1000 + i * 1000, p, absolute=True)
    cmds.group(props, name="props")
    ground, cut, total = woods_ground()

    # the woods are ~180 m across: push the camera's far clip out so it all shows
    cmds.setAttr("perspShape.farClipPlane", 200000)
    cmds.setAttr("perspShape.nearClipPlane", 5)
    cmds.viewSet("persp", home=True)
    cmds.select(clear=True)
    cmds.file(rename=SCENE)
    cmds.file(save=True, type="mayaAscii")
    print(f"woods scene saved: {len(props)} props, ground cut {cut} of {total} cells -> {SCENE}")


build()

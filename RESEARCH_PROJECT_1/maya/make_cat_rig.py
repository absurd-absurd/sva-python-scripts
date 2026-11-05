"""Rig and animate the Fab black cat in Maya, and export it for Unreal as an animated
skeletal mesh.

Run with mayapy (or in Maya):
    exec(open(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/maya/make_cat_rig.py").read())

Input:  export/fabcat/black_cat.fbx (the Fab cat, exported from Unreal by unreal/cat_rig_import.py)
Output: export/fabcat/cat_rig.fbx       the skinned mesh + skeleton (bind pose)
        export/fabcat/cat_walk.fbx      walk cycle, 1 s, in place (Unreal moves the actor)
        export/fabcat/cat_idle.fbx      standing still: breathing, slow tail sway, looking around
        maya/cat_rig.ma                 the rig scene

Steps:
 1. Import the cat, turn it so its body faces +Z (it was standing 35 degrees off), feet on y = 0.
 2. Find landmarks in the mesh itself (feet, leg centres at several heights, the spine line,
    the head, the tail) and build a skeleton there: root > pelvis > spine x3 > chest > neck x2 >
    head; four legs (back legs bend backwards at the hock, like a real cat); a tail chain.
 3. Skin it (heat-map bind, falls back to closest-distance), plus two glowing eyes on the head joint.
 4. Animate with IK on the legs so the paws plant on the ground and never slide: a lateral
    walk (back-left, front-left, back-right, front-right, like the reference video), shoulders and
    hips rolling, a small bob, the head held level, the tail raised with a curl and a slow wave.
    Bake to the joints, remove the IK, export.
Maya axes: y up, z forward. Unreal gets them as z up, y forward (same as all MARROW exports).
"""
import json
import math
import os

import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
SRC = os.path.join(ROOT, "export", "fabcat", "black_cat.fbx")
OUT = os.path.join(ROOT, "export", "fabcat")
FPS = 30
WALK_FRAMES = 30                  # one full stride cycle = 1 s (reference video: ~1.1 s)
STRIDE = 26.0                     # cm the body travels per cycle (model scale; Unreal scales it 0.75)
IDLE_FRAMES = 240


def vec(a, b):
    return om.MVector(b[0] - a[0], b[1] - a[1], b[2] - a[2])


# ---------- 1. the mesh ----------

def load_cat():
    cmds.file(new=True, force=True)
    cmds.currentUnit(time="ntsc")                         # 30 fps
    if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
        cmds.loadPlugin("fbxmaya")
    cmds.file(SRC, i=True, type="FBX", ignoreVersion=True)
    for t in cmds.ls("UCX_*", type="transform"):
        cmds.delete(t)                                    # Unreal's collision box
    mesh = [cmds.listRelatives(m, parent=True)[0] for m in cmds.ls(type="mesh")][0]
    mesh = cmds.rename(mesh, "cat_mesh")
    cmds.makeIdentity(mesh, apply=True, t=True, r=True, s=True)
    # the body runs from the rump (x -17, z -30) to the chest (x 14, z 15): turn it onto +Z
    ang = math.degrees(math.atan2(14 - -17, 15 - -30))
    cmds.rotate(0, -ang, 0, mesh, pivot=(0, 0, 0))
    cmds.makeIdentity(mesh, apply=True, r=True)
    pts = points(mesh)
    feet = [p for p in pts if p[1] < 2.5]
    cx = sum(p[0] for p in feet) / len(feet)
    cz = sum(p[2] for p in feet) / len(feet)
    cmds.move(-cx, -min(p[1] for p in pts), -cz, mesh, relative=True)
    cmds.makeIdentity(mesh, apply=True, t=True)
    cmds.delete(mesh, constructionHistory=True)
    return mesh


def points(mesh):
    p = cmds.xform(mesh + ".vtx[*]", q=True, t=True, ws=True)
    return [(p[i], p[i + 1], p[i + 2]) for i in range(0, len(p), 3)]


def centre(pts):
    n = float(len(pts))
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n, sum(p[2] for p in pts) / n)


# ---------- 2. landmarks and skeleton ----------

def landmarks(mesh):
    P = points(mesh)
    L = {}
    # feet: four clusters on the ground, sorted into front/back (z) and left/right (x)
    low = [p for p in P if p[1] < 3.0]
    front = [p for p in low if p[2] > 0]
    back = [p for p in low if p[2] <= 0]
    for name, grp in (("f", front), ("b", back)):
        mx = sum(p[0] for p in grp) / len(grp)
        L[name + "L"] = centre([p for p in grp if p[0] > mx])     # +x = the cat's left (facing +z)
        L[name + "R"] = centre([p for p in grp if p[0] <= mx])
    # leg centres at a few heights, near each foot
    for k in ("fL", "fR", "bL", "bR"):
        fx, _, fz = L[k]
        for h in (6, 11, 16):
            near = [p for p in P if abs(p[1] - h) < 1.2 and math.hypot(p[0] - fx, p[2] - fz) < 9]
            L[f"{k}{h}"] = centre(near) if len(near) > 10 else (fx, h, fz)
    # spine line: centre of the body cross-section every few cm along z, above the legs
    zs = [p[2] for p in P]
    body = []
    z0, z1 = min(zs), max(zs)
    for z in range(int(z0) + 4, int(z1) - 2, 3):
        sl = [p for p in P if abs(p[2] - z) < 1.5 and p[1] > 20]
        if len(sl) > 30:
            ys = sorted(p[1] for p in sl)
            body.append((z, sum(p[0] for p in sl) / len(sl), ys[len(ys) // 2], ys[-1]))
    L["body"] = body
    # tail: the points behind the rump, walked from the base out to the tip
    rump_z = body[0][0]
    tail = [p for p in P if p[2] < rump_z - 2]
    L["tail"] = tail
    L["all"] = P
    return L


def chain_through(pts, n):
    """n evenly spaced points along a cloud of points that forms a tube (the tail): start at the
    end nearest the body, step to the nearest unvisited neighbourhood each time."""
    pts = sorted(pts, key=lambda p: -p[2])                # nearest the body first
    path = [centre(pts[:40])]
    left = pts[:]
    for _ in range(60):
        cur = path[-1]
        ahead = [p for p in left if 2.0 < math.dist(p, cur) < 5.0]
        if len(ahead) < 6:
            break
        nxt = centre(ahead)
        path.append(nxt)
        left = [p for p in left if math.dist(p, cur) > 2.0]
    # resample to n points by length
    lens = [0.0]
    for a, b in zip(path, path[1:]):
        lens.append(lens[-1] + math.dist(a, b))
    out = []
    for i in range(n):
        s = lens[-1] * i / (n - 1)
        k = max(j for j in range(len(lens)) if lens[j] <= s + 1e-6)
        k = min(k, len(path) - 2)
        t = (s - lens[k]) / max(1e-6, lens[k + 1] - lens[k])
        out.append(tuple(path[k][d] + (path[k + 1][d] - path[k][d]) * t for d in range(3)))
    return out


def joint(name, p, parent=None):
    cmds.select(clear=True)
    j = cmds.joint(name=name, position=p)
    if parent:
        cmds.parent(j, parent)
    cmds.setAttr(j + ".jointOrient", 0, 0, 0)
    return j


def build_skeleton(L):
    """Joints placed from the mesh: the torso is the part above 20 cm between the legs (its
    middle height is the spine line), the head is everything above 48 cm, the tail is the part
    behind the back legs. Legs go from the body down through the leg centres to the paws."""
    P = L["all"]
    torso = [p for p in P if 20 < p[1] < 47 and L["bL"][2] + 3 < p[2] < L["fL"][2] - 3]
    spine_y = (min(p[1] for p in torso) + max(p[1] for p in torso)) / 2.0
    head_pts = [p for p in P if p[1] > 48]
    head = centre(head_pts)
    back_z = min(L["bL"][2], L["bR"][2])
    front_z = max(L["fL"][2], L["fR"][2])
    rump_z = min(p[2] for p in P if abs(p[1] - spine_y) < 6)        # back end of the body
    J = {}
    J["root"] = joint("root", (0, 0, 0))
    J["pelvis"] = joint("pelvis", (0, spine_y, back_z + 2), J["root"])
    prev = J["pelvis"]
    chest_z = front_z - 6
    for i, t in enumerate((0.25, 0.5, 0.75)):
        prev = J[f"spine{i + 1}"] = joint(f"spine{i + 1}", (0, spine_y + 1.0, back_z + 2 + (chest_z - back_z - 2) * t), prev)
    J["chest"] = joint("chest", (0, spine_y, chest_z), prev)
    neck_base = (head[0] * 0.3, spine_y + 8, front_z + 1)
    J["neck1"] = joint("neck1", neck_base, J["chest"])
    J["neck2"] = joint("neck2", tuple(neck_base[d] + (head[d] - neck_base[d]) * 0.5 for d in range(3)), J["neck1"])
    J["head"] = joint("head", (head[0], head[1] - 2, head[2] - 3), J["neck2"])
    J["head_end"] = joint("head_end", (head[0], head[1] - 2, head[2] + 7), J["head"])
    for side in ("L", "R"):
        f, b = L["f" + side], L["b" + side]
        J["shoulder" + side] = joint("shoulder" + side, (f[0] * 0.7, spine_y - 4, f[2] - 3), J["chest"])
        J["elbow" + side] = joint("elbow" + side, (L[f"f{side}16"][0], 15.0, L[f"f{side}16"][2] - 3.0), J["shoulder" + side])
        J["wrist" + side] = joint("wrist" + side, (L[f"f{side}6"][0], 4.5, L[f"f{side}6"][2]), J["elbow" + side])
        J["fpaw" + side] = joint("fpaw" + side, (f[0], 0.8, f[2] + 3.0), J["wrist" + side])
        J["hip" + side] = joint("hip" + side, (b[0] * 0.7, spine_y - 3, b[2] + 1), J["pelvis"])
        J["knee" + side] = joint("knee" + side, (L[f"b{side}16"][0], 16.0, L[f"b{side}16"][2] + 5.0), J["hip" + side])
        J["hock" + side] = joint("hock" + side, (L[f"b{side}6"][0], 6.5, L[f"b{side}6"][2] - 3.0), J["knee" + side])
        J["bpaw" + side] = joint("bpaw" + side, (b[0], 0.8, b[2] + 3.0), J["hock" + side])
    # tail: from the top of the rump, down the hanging tail in height bands to the tip
    tail = [p for p in P if p[2] < back_z - 6]
    pts = [(0.0, spine_y + 3, rump_z + 2)]
    top = max(p[1] for p in tail)
    bottom = min(p[1] for p in tail)
    for k in range(1, 8):
        y = top - (top - bottom) * k / 7.0
        band = [p for p in tail if abs(p[1] - y) < 2.0]
        if band:
            pts.append(centre(band))
    prev = J["pelvis"]
    for i, p in enumerate(pts):
        prev = J[f"tail{i + 1}"] = joint(f"tail{i + 1}", p, prev)
    return J


# ---------- 3. skin and eyes ----------

def skin(mesh, J):
    bones = [j for k, j in J.items() if k not in ("head_end", "root") and not k.startswith("fpaw") and not k.startswith("bpaw")]
    bones += [J[k] for k in J if k.startswith("fpaw") or k.startswith("bpaw")]
    for method in (1, 0):            # closest along the bone hierarchy (heat map needs a GPU)
        try:
            sc = cmds.skinCluster(bones, mesh, toSelectedBones=True, bindMethod=method, maximumInfluences=3,
                                  normalizeWeights=1, obeyMaxInfluences=True, name="cat_skin")[0]
            print("skinned, bind method", method)
            fix_tail(mesh, sc, J)
            return sc
        except RuntimeError as e:
            print("bind method", method, "failed:", e)
            cmds.delete(mesh, constructionHistory=True)
    raise RuntimeError("could not skin the cat")


def fix_tail(mesh, sc, J):
    """Closest-distance binding gives the bottom of the hanging tail to the back legs (it hangs
    near them), so lifting the tail stretched it into a long streak. Every vertex behind the back
    legs now belongs only to its nearest tail bone (blended with the next one along)."""
    import maya.api.OpenMayaAnim as oma
    tails = sorted([k for k in J if k.startswith("tail")], key=lambda k: int(k[4:]))
    tp = [om.MVector(*cmds.xform(J[k], q=True, ws=True, t=True)) for k in tails]
    back_z = min(cmds.xform(J["bpawL"], q=True, ws=True, t=True)[2], cmds.xform(J["bpawR"], q=True, ws=True, t=True)[2])
    sel = om.MSelectionList(); sel.add(sc); sel.add(mesh)
    fn = oma.MFnSkinCluster(sel.getDependNode(0))
    dag = sel.getDagPath(1)
    infl = [p.partialPathName() for p in fn.influenceObjects()]
    idx = {name: infl.index(J[name]) for name in tails}
    pts = om.MFnMesh(dag).getPoints(om.MSpace.kWorld)
    comp = om.MFnSingleIndexedComponent()
    cobj = comp.create(om.MFn.kMeshVertComponent)
    # back-leg bones: a vertex only goes to the tail if it's closer to the tail than to a back leg
    legs = []
    for side in ("L", "R"):
        ch = [om.MVector(*cmds.xform(J[k + side], q=True, ws=True, t=True)) for k in ("hip", "knee", "hock", "bpaw")]
        legs += list(zip(ch, ch[1:]))
    def seg_d(p, a_, b_):
        ab = b_ - a_
        t = max(0.0, min(1.0, ((p - a_) * ab) / max(1e-6, ab * ab)))
        return (a_ + ab * t - p).length()
    tsegs = list(zip(tp, tp[1:]))
    verts = []
    for i, p in enumerate(pts):
        if p.z >= back_z - 5:
            continue
        v = om.MVector(p)
        if min(seg_d(v, a_, b_) for a_, b_ in tsegs) < min(seg_d(v, a_, b_) for a_, b_ in legs):
            verts.append(i)
    comp.addElements(verts)
    n = len(infl)
    w = om.MDoubleArray(len(verts) * n, 0.0)
    for row, i in enumerate(verts):
        p = om.MVector(pts[i])
        best, bt, bk = 1e9, 0.0, 0
        for k in range(len(tp) - 1):
            a_, b_ = tp[k], tp[k + 1]
            ab = b_ - a_
            t = max(0.0, min(1.0, ((p - a_) * ab) / max(1e-6, ab * ab)))
            d = (a_ + ab * t - p).length()
            if d < best:
                best, bt, bk = d, t, k
        w[row * n + idx[tails[bk]]] = 1.0 - bt
        w[row * n + idx[tails[bk + 1]]] = bt
    fn.setWeights(dag, cobj, om.MIntArray(list(range(n))), w, normalize=True)
    print("tail weights fixed on", len(verts), "vertices")


def eyes(J):
    """Two glowing eyes on the face (the model's eyes are only painted), bound to the head."""
    head = cmds.xform(J["head"], q=True, ws=True, t=True)
    made = []
    mat = "cat_eye_glow"
    if not cmds.objExists(mat):
        cmds.shadingNode("lambert", asShader=True, name=mat)
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=mat + "SG")
        cmds.connectAttr(mat + ".outColor", sg + ".surfaceShader")
    cmds.setAttr(mat + ".color", 0.55, 0.9, 0.25, type="double3")
    return mat, head


# ---------- 4. animation ----------

def ik_legs(J):
    """IK on each leg (shoulder->wrist, hip->hock) with a pole so elbows point back and knees
    forward; the paw goal is a locator that the walk keys move."""
    goals = {}
    for side in ("L", "R"):
        for top, mid, end, pole_dz, key in (("shoulder", "elbow", "wrist", -30, "f"), ("hip", "knee", "hock", 30, "b")):
            h = cmds.ikHandle(startJoint=J[top + side], endEffector=J[end + side], solver="ikRPsolver",
                              name=f"ik_{key}{side}")[0]
            p = cmds.xform(J[mid + side], q=True, ws=True, t=True)
            pole = cmds.spaceLocator(name=f"pole_{key}{side}")[0]
            cmds.move(p[0], p[1], p[2] + pole_dz, pole)
            cmds.parent(pole, J["root"])
            cmds.poleVectorConstraint(pole, h)
            g = cmds.spaceLocator(name=f"goal_{key}{side}")[0]
            e = cmds.xform(J[end + side], q=True, ws=True, t=True)
            cmds.move(*e, g)
            cmds.parent(h, g)
            # and a second, single-bone IK from the wrist/hock to the paw: keeps the paw flat on the ground
            paw = J[("fpaw" if key == "f" else "bpaw") + side]
            h2 = cmds.ikHandle(startJoint=J[end + side], endEffector=paw, solver="ikSCsolver", name=f"ikpaw_{key}{side}")[0]
            cmds.parent(h2, g)
            goals[key + side] = (g, e)
    return goals


def key(obj, attr, frame, value):
    cmds.setKeyframe(obj, attribute=attr, time=frame, value=value, inTangentType="spline", outTangentType="spline")


def walk(J, goals):
    """Lateral-sequence walk: back-left 0, front-left .25, back-right .5, front-right .75.
    Each foot is planted for 62% of the cycle (sliding back at the body's speed, so it stays put
    once Unreal moves the cat forward) and swings forward in an arc for the rest."""
    phase = {"bL": 0.0, "fL": 0.25, "bR": 0.5, "fR": 0.75}
    stance = 0.62
    n = WALK_FRAMES
    for k, (g, rest) in goals.items():
        lift = 3.2 if k[0] == "f" else 2.6
        reach = STRIDE if k[0] == "f" else STRIDE * 0.8     # back legs: shorter reach, never fully straight
        for f in range(n + 1):
            u = (f / n + phase[k]) % 1.0
            if u < stance:                                   # planted: moves back under the body
                s = u / stance
                dz = reach * (0.5 - s)
                dy = 0.0
            else:                                            # swinging forward
                s = (u - stance) / (1 - stance)
                e = 0.5 - 0.5 * math.cos(s * math.pi)
                dz = reach * (-0.5 + e)
                dy = lift * math.sin(s * math.pi)
            key(g, "translateZ", f, rest[2] + dz)
            key(g, "translateY", f, rest[1] + dy)
            key(g, "translateX", f, rest[0])
    # body: a small bob twice a cycle, hips and shoulders rolling with the legs, head level
    rest_y = cmds.getAttr(J["pelvis"] + ".translateY")
    for f in range(n + 1):
        t = f / n * 2 * math.pi
        key(J["pelvis"], "translateY", f, rest_y + 0.6 * math.cos(2 * t))
        key(J["pelvis"], "rotateZ", f, 3.0 * math.sin(t))                  # hips roll
        key(J["pelvis"], "rotateY", f, 2.5 * math.sin(t))                  # and swing
        key(J["chest"], "rotateZ", f, -3.0 * math.sin(t + math.pi / 2))    # shoulders roll the other way
        key(J["chest"], "rotateY", f, -2.0 * math.sin(t + math.pi / 2))
        key(J["neck1"], "rotateZ", f, 2.0 * math.sin(t + math.pi / 2))     # head stays steady
        key(J["head"], "rotateX", f, 1.0 * math.sin(2 * t))
    tail_pose(J, n, wave=3.0, speed=1)       # the model's tail hangs: a gentle sway (raising it tore the mesh)


def tail_pose(J, n, wave, speed, t0=0, raise_tail=False):
    """Raise the tail upright with a soft curl at the tip (the reference), then wave it slowly."""
    tails = sorted([k for k in J if k.startswith("tail")], key=lambda k: int(k[4:]))
    # target shape: from the base, curve up to vertical, the last joints curling forward
    base = om.MVector(*cmds.xform(J[tails[0]], q=True, ws=True, t=True))
    seg = [om.MVector(*cmds.xform(J[b], q=True, ws=True, t=True)) - om.MVector(*cmds.xform(J[a], q=True, ws=True, t=True))
           for a, b in zip(tails, tails[1:])]
    length = sum(s.length() for s in seg) / max(1, len(seg))
    cmds.currentTime(t0)
    for i, (a, b) in enumerate(zip(tails, tails[1:]) if raise_tail else []):
        t = i / max(1, len(tails) - 2)
        ang = math.radians(-35 + 125 * t ** 0.8)              # back and up ... vertical ... over forward
        want = om.MVector(0, math.sin(ang), -math.cos(ang))
        pa = om.MVector(*cmds.xform(J[a], q=True, ws=True, t=True))
        pb = om.MVector(*cmds.xform(J[b], q=True, ws=True, t=True))
        q = om.MQuaternion(pb - pa, want)
        e = q.asEulerRotation()
        cmds.rotate(math.degrees(e.x), math.degrees(e.y), math.degrees(e.z), J[a], relative=True, worldSpace=True)
    rest = {k: cmds.getAttr(J[k] + ".rotate")[0] for k in tails}
    for f in range(t0, t0 + n + 1):
        t = (f - t0) / n * 2 * math.pi * speed
        for i, k in enumerate(tails):
            r = rest[k]
            key(J[k], "rotateX", f, r[0])
            key(J[k], "rotateY", f, r[1] + wave * 0.5 * math.sin(t - i * 0.5))
            key(J[k], "rotateZ", f, r[2] + wave * math.sin(t - i * 0.45))


def idle(J, goals):
    """Standing: feet planted, slow breathing, the tail swaying, the head slowly looking around."""
    n = IDLE_FRAMES
    for g, rest in goals.values():
        for f in (0, n):
            for a, v in zip("XYZ", rest):
                key(g, "translate" + a, f, v)
    for f in range(0, n + 1, 4):
        t = f / n * 2 * math.pi
        key(J["spine2"], "scaleY", f, 1.0 + 0.012 * math.sin(t * 6))         # breathing
        key(J["neck1"], "rotateY", f, 18 * math.sin(t) + 6 * math.sin(t * 3))   # looking round
        key(J["head"], "rotateX", f, 4 * math.sin(t * 2))
    tail_pose(J, n, wave=5.0, speed=2)


def bake_and_export(J, name, frames, mesh):
    joints = list(J.values())
    cmds.bakeResults(joints, time=(0, frames), simulation=True, sampleBy=1, preserveOutsideKeys=False,
                     attribute=["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ",
                                "scaleX", "scaleY", "scaleZ"])
    for h in cmds.ls(type="ikHandle"):
        cmds.delete(h)
    for loc in cmds.ls("goal_*", "pole_*", type="transform"):
        cmds.delete(loc)
    path = os.path.join(OUT, name + ".fbx").replace("\\", "/")
    cmds.currentUnit(time="ntsc")
    cmds.playbackOptions(minTime=0, maxTime=frames, animationStartTime=0, animationEndTime=frames)
    cmds.select(J["root"], mesh)
    mel.eval("FBXResetExport")
    mel.eval("FBXExportBakeComplexAnimation -v true")
    mel.eval(f"FBXExportBakeComplexStart -v 0")
    mel.eval(f"FBXExportBakeComplexEnd -v {frames}")
    mel.eval("FBXExportSkins -v true")
    mel.eval("FBXExportShapes -v false")
    mel.eval(f'FBXExport -f "{path}" -s')
    print("exported", path)


def build(anim):
    mesh = load_cat()
    L = landmarks(mesh)
    J = build_skeleton(L)
    skin(mesh, J)
    if anim is None:
        path = os.path.join(OUT, "cat_rig.fbx").replace("\\", "/")
        cmds.select(J["root"], mesh)
        mel.eval("FBXResetExport")
        mel.eval("FBXExportSkins -v true")
        mel.eval(f'FBXExport -f "{path}" -s')
        cmds.file(rename=os.path.join(ROOT, "maya", "cat_rig.ma"))
        cmds.file(save=True, type="mayaAscii")
        json.dump({k: [round(v, 2) for v in cmds.xform(j, q=True, ws=True, t=True)] for k, j in J.items()},
                  open(os.path.join(OUT, "cat_joints.json"), "w"), indent=1)
        print("rig exported", path, len(J), "joints")
        return
    goals = ik_legs(J)
    if anim == "walk":
        walk(J, goals)
        for f in (0, 8, 15, 23):
            cmds.currentTime(f)
            print("WALK", f, {k: [round(v, 1) for v in cmds.xform(J[k], q=True, ws=True, t=True)] for k in ("pelvis", "chest", "head", "fpawL", "fpawR", "bpawL", "bpawR", "tail8")})
        bake_and_export(J, "cat_walk", WALK_FRAMES, mesh)
    else:
        idle(J, goals)
        bake_and_export(J, "cat_idle", IDLE_FRAMES, mesh)


for _anim in (None, "walk", "idle"):
    build(_anim)

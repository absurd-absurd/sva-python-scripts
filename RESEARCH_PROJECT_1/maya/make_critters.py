"""Build the small living things in MARROW and export one FBX each for Unreal.

Run with mayapy (or in Maya):
    exec(open(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/maya/make_critters.py").read())

Each critter is built at the origin, in Unreal coordinates (the helpers from make_motel.py and
room_props.py are reused), facing +y, wings along x. It has ONE material named critter_<kind>_mat;
unreal/critters.py gives that the M_PS2_Critter material, which moves the whole critter along its
path and flaps its wings in the vertex shader (no Blueprint logic, so hundreds cost nothing).
Wings must lie away from the body centre: the shader flaps everything further than the body
radius from the critter's middle.

Writes export/critter_<kind>.fbx and export/critters.json (the colors of their materials).
"""
import json
import math
import os

import maya.cmds as cmds
import maya.mel as mel

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
_src = open(os.path.join(ROOT, "maya", "make_motel.py"), encoding="utf-8").read()
exec(_src[:_src.rindex("\nbuild()")])              # the helpers (box, tube, rsoft, sphere, ...)

COLORS = {
    "critter_moth_mat": (0.55, 0.48, 0.36), "critter_firefly_mat": (0.75, 0.85, 0.3),
    "critter_gnat_mat": (0.5, 0.5, 0.48), "critter_bat_mat": (0.06, 0.05, 0.05),
    "critter_flock_mat": (0.03, 0.03, 0.035),
    "critter_crow_mat": (0.028, 0.028, 0.034), "critter_crow_beak_mat": (0.06, 0.055, 0.05),
    "critter_owl_mat": (0.26, 0.2, 0.14), "critter_owl_face_mat": (0.5, 0.44, 0.34),
    "critter_owl_eye_mat": (1.0, 0.72, 0.1), "critter_snag_mat": (0.2, 0.17, 0.14),
    "critter_cat_mat": (0.022, 0.021, 0.024), "critter_cat_eye_mat": (0.55, 0.9, 0.25),
    "critter_catsit_mat": (0.022, 0.021, 0.024), "critter_catsit_eye_mat": (0.55, 0.9, 0.25),
}


def wing(x0, x1, y0, y1, z, mat, droop=0.0):
    """A thin flat wing (a flattened soft shape), its tip drooping a little."""
    return rsoft((x0 + x1) / 2.0, (y0 + y1) / 2.0, z - droop, abs(x1 - x0), abs(y1 - y0), 0.15 + 0.02 * abs(x1 - x0),
                 mat, smooth=1, tilt_x=(8 if x0 > 0 else -8) * (1 if droop else 0))


def moth():
    """~8 cm across: a big moth, so it still reads at the PS2 resolution."""
    m = "critter_moth_mat"
    rsoft(0, 0, 0, 1.1, 4.0, 1.1, m, smooth=1)                                  # body
    for s in (-1, 1):
        wing(s * 0.6, s * 4.2, -0.3, 2.0, 0.2, m)                              # fore wings
        wing(s * 0.5, s * 3.0, -1.9, -0.2, 0.1, m)                             # hind wings
    tube((0, 1.8, 0.4), (0.9, 3.6, 0.9), 0.08, m, sides=3)                      # antennae
    tube((0, 1.8, 0.4), (-0.9, 3.6, 0.9), 0.08, m, sides=3)


def firefly():
    m = "critter_firefly_mat"
    sphere(0, 0, 0, 1.1, m, sides=6, scale=(1, 1.5, 1))          # bigger than life: it's a glow, not a bug


def gnat():
    m = "critter_gnat_mat"
    sphere(0, 0, 0, 0.18, m, sides=4)


def bat():
    """Body, ears, and two membrane wings with finger ribs (span ~32 cm)."""
    m = "critter_bat_mat"
    rsoft(0, 0, 0, 4, 8, 3.5, m, smooth=1)
    sphere(0, 4.5, 0.6, 2.2, m, sides=8)
    for s in (-1, 1):
        tube((s * 0.8, 5.0, 2.0), (s * 1.4, 5.6, 3.6), 0.5, m, sides=4)          # ears
        for k, (tx, ty) in enumerate(((7, 3), (12, 1), (16, -3))):              # wing: three panels
            x0 = s * (3 + k * 4.5)
            wing(x0, s * (3 + (k + 1) * 4.5), -4 + k * 0.5, ty + 1.5, 0.3, m)
            tube((s * 2, 1.5, 0.5), (s * tx, ty, 0.5 + k * 0.3), 0.18, m, sides=3)   # finger ribs


def flock_bird():
    """A crow-sized black silhouette with long swept wings, for the flock high over the lake."""
    m = "critter_flock_mat"
    rsoft(0, 0, 0, 5, 18, 4, m, smooth=1)
    sphere(0, 9, 0.8, 2.6, m, sides=8)
    rbox(0, -11, 0, 6, 6, 0.6, m)                                               # tail
    for s in (-1, 1):
        wing(s * 2, s * 18, -3, 4, 0.4, m)
        wing(s * 17, s * 30, -4, 2, 0.6, m, droop=0.5)


def crow():
    """A crow sitting on a perch (feet at the origin, facing +y): body leaning forward, folded
    wings along the sides, tail, head with a heavy beak, legs and toes. ~40 cm long."""
    m, b = "critter_crow_mat", "critter_crow_beak_mat"
    rsoft(0, 0, 11, 9, 19, 10, m, smooth=2, tilt_y=-12)                         # body
    sphere(0, 9.5, 18, 4.6, m, sides=10, scale=(1, 1.15, 1))                   # head
    tube((0, 13, 18), (0, 19.5, 16.8), 1.5, b, sides=6)                         # beak
    sphere(0, 19.3, 16.9, 0.7, b, sides=6)
    rbevel(0, -13, 8.5, 6, 12, 0.9, m, r=0.3, tilt_y=14)                        # tail
    for s_ in (-1, 1):
        rsoft(s_ * 4.6, -1.5, 12.5, 2.2, 19, 7, m, smooth=1, tilt_x=s_ * 6)       # folded wings
        tube((s_ * 1.8, 1, 6.5), (s_ * 1.8, 1.8, 0.4), 0.45, b, sides=4)         # legs
        for dx, dy in ((-1.5, 2.5), (0, 3.2), (1.5, 2.5), (0, -2)):
            tube((s_ * 1.8, 1.8, 0.4), (s_ * 1.8 + dx, 1.8 + dy, 0.2), 0.3, b, sides=3)   # toes


def owl():
    """A barred owl on a perch (feet at the origin, facing +y): an egg-shaped body, a round head
    (everything above 25 cm turns to watch you), pale facial disc, glowing yellow eyes, beak,
    ear tufts, wings folded, talons."""
    m, f, e = "critter_owl_mat", "critter_owl_face_mat", "critter_owl_eye_mat"
    rsoft(0, 0, 13, 18, 16, 24, m, smooth=2)                                    # body
    rsoft(0, 5.5, 13, 12, 6, 18, f, smooth=2)                                   # pale chest
    sphere(0, 0, 32, 9.5, m, sides=14, scale=(1, 0.95, 0.9))                    # head
    rsoft(0, 7.6, 32, 15, 2.5, 12, f, smooth=2)                                 # facial disc
    for s_ in (-1, 1):
        sphere(s_ * 3.4, 9.0, 33, 2.1, e, sides=10)                             # eyes
        sphere(s_ * 3.4, 10.6, 33, 0.9, "critter_crow_mat", sides=8)             # pupils
        tube((s_ * 5, 1, 39), (s_ * 7, 1.5, 43.5), 1.2, m, sides=5)             # ear tufts
        rsoft(s_ * 8, -1, 15, 3, 15, 20, m, smooth=1)                           # folded wings
        for dx in (-1.2, 0, 1.2):
            tube((s_ * 3 + dx, 3, 1.5), (s_ * 3 + dx * 1.4, 5.5, 0.2), 0.45, "critter_crow_beak_mat", sides=3)  # talons
    tube((0, 9.5, 30.5), (0, 11.5, 28.5), 0.9, "critter_crow_beak_mat", sides=5)  # beak


def snag():
    """A dead, broken-off tree for the owl to sit on: tapered trunk, jagged top, one stub branch."""
    m = "critter_snag_mat"
    frustum(0, 0, 0, 290, 17, 10, m, sides=10)
    for k in range(5):                                                          # jagged break
        a = k * 1.25
        tube((math.cos(a) * 6, math.sin(a) * 6, 288), (math.cos(a) * 4, math.sin(a) * 4, 300 + (k % 3) * 9), 2.5, m, sides=4)
    tube((0, 0, 230), (45, 10, 262), 4, m, sides=6)                             # stub branch
    tube((-2, 0, 40), (-30, 5, 0), 6, m, sides=6)                               # a root


def _limb(points, radii, m, sides=10):
    """A smooth limb or tail through points, radius tapering along radii, with round joints."""
    for (a, b), (ra, rb) in zip(zip(points, points[1:]), zip(radii, radii[1:])):
        tube(a, b, (ra + rb) / 2.0, m, sides=sides)
    for p, r in zip(points, radii):
        sphere(*p, r, m, sides=sides)


def _torso(m, y0, y1, profile, seed=0):
    """A cat's body as one smooth shape along y (y0 rump .. y1 chest). profile(u) gives
    (half width, half height, centre height) at u = 0..1 along the body."""
    c = cmds.polyCube(w=1, h=1, d=1, sx=6, sy=6, sz=14, ch=False)[0]
    pts = []
    for x, y, z in _verts(c):
        u = z + 0.5
        hw, hh, cz = profile(u)
        v, q = x * 2, y * 2                                   # -1..1 square cross-section
        r = max(abs(v), abs(q))
        n = math.hypot(v, q) or 1.0
        v, q = v / n * r, q / n * r                            # square -> round
        pts.append((v * hw, cz + q * hh, y0 + (y1 - y0) * u))
    _set_verts(c, pts)
    cmds.polySmooth(c, dv=2, ch=False)
    return keep(c, m)


def _cat_head(m, e, y, z, look=0.0):
    """Head centred at (0, y, z) facing +y: round skull, cheeks, muzzle, nose, pointed ears,
    almond eyes standing just out of the face."""
    sphere(0, y, z, 5.4, m, sides=20, scale=(1.08, 1.0, 0.92))
    for s_ in (-1, 1):
        sphere(s_ * 2.6, y + 1.8, z - 1.6, 2.9, m, sides=14)                       # cheeks
        frustum(s_ * 3.0, y - 0.6, z + 3.2, z + 9.4, 2.4, 0.2, m, sides=10)       # ears
        sphere(s_ * 2.15, y + 4.75, z + 0.9, 1.25, e, sides=12, scale=(1.25, 0.55, 0.75))   # eyes
    rsoft(0, y + 4.6, z - 2.0, 4.4, 3.4, 3.0, m, smooth=2)                         # muzzle
    sphere(0, y + 6.1, z - 0.9, 0.8, m, sides=8, scale=(1.2, 0.8, 0.7))             # nose


def _cat_body(u):
    """half width, half height, centre z along the body (0 rump .. 1 chest)."""
    hw = 4.2 + 0.9 * math.exp(-((u - 0.18) / 0.2) ** 2) - 0.9 * math.exp(-((u - 0.5) / 0.18) ** 2) \
        + 0.5 * math.exp(-((u - 0.82) / 0.15) ** 2)
    hh = 5.0 + 0.9 * math.exp(-((u - 0.2) / 0.2) ** 2) - 0.8 * math.exp(-((u - 0.5) / 0.2) ** 2) \
        + 0.9 * math.exp(-((u - 0.82) / 0.16) ** 2)
    end = min(u, 1 - u)
    k = math.sqrt(max(0.02, min(1.0, end / 0.12)))            # rounded ends
    return hw * k, hh * k, 21.0 + 0.8 * math.sin(u * math.pi) - 1.2 * math.exp(-((u - 0.5) / 0.2) ** 2) * 0.5


def cat():
    """A slender black cat walking (feet at the origin, facing +y). The shader moves it:
    legs = everything below 16 cm, tail = behind y -18, head = in front of y 17 and above 23 cm."""
    m, e = "critter_cat_mat", "critter_cat_eye_mat"
    _torso(m, -18, 15, _cat_body)
    _limb([(0, 12, 24), (0, 16, 27.5), (0, 19.5, 29.5)], [3.6, 3.0, 2.7], m)                   # neck
    _cat_head(m, e, 21.5, 31)
    for s_ in (-1, 1):
        _limb([(s_ * 2.9, 11, 18), (s_ * 2.8, 12, 9.5), (s_ * 2.7, 11.6, 2.6)], [1.9, 1.35, 1.1], m)      # front legs
        sphere(s_ * 2.7, 12.6, 1.2, 1.35, m, sides=10, scale=(1, 1.4, 0.7))
        _limb([(s_ * 3.4, -12, 19.5), (s_ * 3.4, -7.5, 11), (s_ * 3.2, -13.5, 5), (s_ * 3.1, -12.2, 1.8)],
              [2.8, 1.8, 1.2, 1.05], m)                                                                     # back legs
        sphere(s_ * 3.1, -11.2, 1.2, 1.35, m, sides=10, scale=(1, 1.4, 0.7))
    pts, rad = [], []
    for i in range(14):                                         # long tail, rising, tip curling
        t = i / 13.0
        pts.append((0, -18 - 22 * t + 4 * max(0, t - 0.75) ** 2 * 10, 22 + 6 * t + 22 * t * t))
        rad.append(1.7 - 0.8 * t)
    _limb(pts, rad, m, sides=8)


def catsit():
    """The same cat sitting upright (feet at the origin, facing +y), tail curled round its feet."""
    m, e = "critter_catsit_mat", "critter_catsit_eye_mat"
    _torso(m, -9, 7, lambda u: (lambda hw, hh: (hw * 1.15, hh * 1.35, 10 + 11 * u))(*_cat_body(u)[:2]))
    _limb([(0, 3, 22), (0, 4.5, 27), (0, 5, 30)], [4.0, 3.2, 2.8], m)                           # neck
    _cat_head(m, e, 6, 33)
    for s_ in (-1, 1):
        _limb([(s_ * 2.4, 4.5, 17), (s_ * 2.3, 6.5, 8), (s_ * 2.2, 7, 2.4)], [1.8, 1.3, 1.1], m)  # front legs
        sphere(s_ * 2.2, 8.0, 1.2, 1.35, m, sides=10, scale=(1, 1.4, 0.7))
        sphere(s_ * 5.2, -2, 5, 4.5, m, sides=14, scale=(0.6, 1.3, 0.9))                       # haunches
        sphere(s_ * 3.6, 4.5, 1.2, 1.4, m, sides=10, scale=(1, 1.6, 0.6))                      # back feet
    pts = [(0, -9, 2), (5, -8, 1.8), (9, -2, 1.6), (9.5, 4, 1.5), (7, 9, 1.5), (3, 11, 1.6), (0.5, 11.5, 1.8)]
    _limb(pts, [1.7, 1.6, 1.5, 1.4, 1.2, 1.05, 0.95], m, sides=8)                          # tail round the front


KINDS = {"cat": cat, "catsit": catsit, "crow": crow, "owl": owl, "snag": snag, "moth": moth, "firefly": firefly, "gnat": gnat, "bat": bat, "flock": flock_bird}


def export_one(kind):
    del PARTS[:]
    del ROOM_PARTS[:]
    IN_ROOM[0] = False
    KINDS[kind]()
    mesh = cmds.polyUnite(PARTS, name="critter_" + kind, ch=False)[0] if len(PARTS) > 1 else cmds.rename(PARTS[0], "critter_" + kind)
    cmds.delete(mesh, constructionHistory=True)
    cmds.xform(mesh, pivots=(0, 0, 0), worldSpace=True)
    fbx = os.path.join(ROOT, "export", f"critter_{kind}.fbx").replace("\\", "/")
    cmds.select(mesh)
    mel.eval("FBXResetExport")
    mel.eval('FBXExport -f "{}" -s'.format(fbx))
    tris = cmds.polyEvaluate(mesh, triangle=True)
    cmds.delete(mesh)
    return fbx, tris


def main():
    cmds.file(new=True, force=True)
    for name, rgb in list(MATS.items()) + list(COLORS.items()):
        material(name, rgb)
    out = {"critters": {}, "materials": {k: list(v) for k, v in COLORS.items()}}
    for kind in KINDS:
        fbx, tris = export_one(kind)
        mats = sorted(m for m in COLORS if m.startswith(f"critter_{kind}_"))
        out["critters"][kind] = {"fbx": fbx, "materials": mats, "tris": tris}
    with open(os.path.join(ROOT, "export", "critters.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("critters:", {k: v["tris"] for k, v in out["critters"].items()})


main()

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


KINDS = {"moth": moth, "firefly": firefly, "gnat": gnat, "bat": bat, "flock": flock_bird}


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
        out["critters"][kind] = {"fbx": fbx, "material": f"critter_{kind}_mat", "tris": tris}
    with open(os.path.join(ROOT, "export", "critters.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("critters:", {k: v["tris"] for k, v in out["critters"].items()})


main()

"""
Scatter Tool for Maya
Fayth Elisa Navarro - SVA Python midterm

Pick one object and one surface, and the tool scatters copies of the
object across the surface with random size, spin and tilt.

Run it from Maya's Script Editor (Python tab): File > Open Script,
pick this file, then Execute All (Ctrl+Enter).
"""

import bisect
import math
import random

import maya.cmds as cmds


WINDOW = "scatterToolWindow"
PREVIEW_GROUP = "scatter_preview"

# Names of the UI controls, filled in by show()
ui = {}

# Name of the last group made with Apply, so Clear can remove it
last_scatter = {"group": None}


# ---------------------------------------------------------------
# Small vector helpers (plain Python, no extra modules)
# ---------------------------------------------------------------

def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def length(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def normalize(a):
    size = length(a)
    if size < 1e-9:
        return (0.0, 1.0, 0.0)
    return (a[0] / size, a[1] / size, a[2] / size)


def axes_from_up(up):
    """Return x, y, z axes where y points along 'up'."""
    helper = (1.0, 0.0, 0.0) if abs(up[0]) < 0.9 else (0.0, 0.0, 1.0)
    z = normalize(cross(helper, up))
    x = cross(up, z)
    return x, up, z


# ---------------------------------------------------------------
# Reading the surface
# ---------------------------------------------------------------

def surface_triangles(surface):
    """
    Split the surface mesh into triangles in world space.
    Returns a list of triangles and a running total of their areas,
    used to pick big triangles more often than small ones so copies
    spread evenly. Each triangle is (corners, corner_normals).
    """
    flat = cmds.xform(surface + ".vtx[*]", query=True, worldSpace=True,
                      translation=True)
    points = [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)]

    # Each corner's normal is the average of the faces around it, so
    # copies lean smoothly across a hill instead of jumping face to face.
    corner_normals = [(0.0, 0.0, 0.0)] * len(points)
    corner_ids = []
    areas = []
    for line in cmds.polyInfo(surface + ".f[*]", faceToVertex=True):
        ids = [int(n) for n in line.split(":")[1].split()]
        # Fan each face into triangles: (0,1,2), (0,2,3) ...
        for i in range(1, len(ids) - 1):
            tri = (ids[0], ids[i], ids[i + 1])
            a, b, c = [points[n] for n in tri]
            normal_long = cross(sub(b, a), sub(c, a))
            area = length(normal_long) / 2.0
            if area <= 0:
                continue
            for n in tri:
                corner_normals[n] = add(corner_normals[n], normal_long)
            corner_ids.append(tri)
            areas.append(area)

    triangles = []
    running_area = []
    total = 0.0
    for tri, area in zip(corner_ids, areas):
        total += area
        triangles.append(([points[n] for n in tri],
                          [normalize(corner_normals[n]) for n in tri]))
        running_area.append(total)
    return triangles, running_area


def random_spot(triangles, running_area, rng):
    """Pick a random point on the surface and the surface normal there."""
    pick = rng.random() * running_area[-1]
    index = min(bisect.bisect_right(running_area, pick), len(triangles) - 1)
    (a, b, c), (na, nb, nc) = triangles[index]
    r1, r2 = rng.random(), rng.random()
    if r1 + r2 > 1.0:
        r1, r2 = 1.0 - r1, 1.0 - r2
    point = add(a, add(mul(sub(b, a), r1), mul(sub(c, a), r2)))
    normal = normalize(add(mul(na, 1.0 - r1 - r2), add(mul(nb, r1), mul(nc, r2))))
    return point, normal


# ---------------------------------------------------------------
# Building the scatter
# ---------------------------------------------------------------

def placement_matrix(position, up, spin, scale):
    """A Maya world matrix that stands a copy on 'position', leaning to 'up'."""
    x, y, z = axes_from_up(up)
    angle = math.radians(spin)
    x = add(mul(x, math.cos(angle)), mul(z, math.sin(angle)))
    z = cross(x, y)
    x, y, z = mul(x, scale[0]), mul(y, scale[1]), mul(z, scale[2])
    return [x[0], x[1], x[2], 0,
            y[0], y[1], y[2], 0,
            z[0], z[1], z[2], 0,
            position[0], position[1], position[2], 1]


def tilt(up, angle, direction):
    """Lean the 'up' direction by 'angle' degrees toward 'direction' degrees."""
    x, _, z = axes_from_up(up)
    d, a = math.radians(direction), math.radians(angle)
    side = add(mul(x, math.cos(d)), mul(z, math.sin(d)))
    return normalize(add(mul(up, math.cos(a)), mul(side, math.sin(a))))


def make_instance(obj, group):
    """
    Make an instance of obj inside group. Maya's own cmds.instance gets
    slower with every instance (500 took 12 seconds), so this makes an
    empty transform and hangs obj's shapes and children under it instead.
    """
    holder = cmds.createNode("transform", parent=group,
                             name=obj.split("|")[-1] + "_inst#")
    for child in cmds.listRelatives(obj, children=True, fullPath=True) or []:
        is_shape = bool(cmds.ls(child, shapes=True))
        if is_shape and cmds.getAttr(child + ".intermediateObject"):
            continue
        cmds.parent(child, holder, add=True, shape=is_shape)
    return holder


def build_scatter(settings, group_name, use_instances):
    """
    Make the copies and put them in one new group. Returns the group
    and how many spots were skipped by the slope and height rules.
    The same settings and seed always give the same layout.
    """
    obj = settings["object"]
    triangles, running_area = surface_triangles(settings["surface"])
    rng = random.Random(settings["seed"])
    base_scale = cmds.getAttr(obj + ".scale")[0]
    world_up = (0.0, 1.0, 0.0)

    group = cmds.group(empty=True, name=group_name)
    skipped = 0
    for _ in range(settings["count"]):
        # Always draw every random number, in the same order, so changing
        # one control doesn't reshuffle the whole layout.
        position, normal = random_spot(triangles, running_area, rng)
        tilt_angle = rng.uniform(0, settings["tilt"])
        tilt_direction = rng.uniform(0, 360)
        spin = rng.uniform(0, settings["spin"])
        size = rng.uniform(settings["scale_min"], settings["scale_max"])

        # Landing rules
        slope = math.degrees(math.acos(max(-1.0, min(1.0, normal[1]))))
        if slope > settings["max_slope"] or position[1] < settings["min_height"]:
            skipped += 1
            continue

        up = normal if settings["align"] else world_up
        up = tilt(up, tilt_angle, tilt_direction)
        scale = (base_scale[0] * size, base_scale[1] * size, base_scale[2] * size)

        if use_instances:
            copy = make_instance(obj, group)
        else:
            copy = cmds.duplicate(obj, returnRootsOnly=True)[0]
            copy = cmds.parent(copy, group)[0]
        cmds.xform(copy, worldSpace=True,
                   matrix=placement_matrix(position, up, spin, scale))
    return group, skipped


# ---------------------------------------------------------------
# Reading and checking the window's controls
# ---------------------------------------------------------------

def set_status(message):
    if cmds.text(ui.get("status", ""), exists=True):
        cmds.text(ui["status"], edit=True, label=message)
    print("Scatter: " + message)


def read_settings():
    """Read the window. Returns the settings, or None and shows why not."""
    obj = cmds.textFieldButtonGrp(ui["object"], query=True, text=True).strip()
    surface = cmds.textFieldButtonGrp(ui["surface"], query=True, text=True).strip()

    if not obj:
        set_status("Pick an object to scatter first (select it, then 'Use selected').")
        return None
    if not cmds.objExists(obj):
        set_status("Can't find an object called '%s'." % obj)
        return None
    if not surface:
        set_status("Pick a surface first (select it, then 'Use selected').")
        return None
    if not cmds.objExists(surface):
        set_status("Can't find a surface called '%s'." % surface)
        return None
    if not cmds.listRelatives(surface, shapes=True, type="mesh", noIntermediate=True):
        set_status("'%s' isn't a polygon mesh, so it can't be a surface." % surface)
        return None
    if obj == surface:
        set_status("The object and the surface are the same thing. Pick two different ones.")
        return None

    scale_a = cmds.floatSliderGrp(ui["scale_min"], query=True, value=True)
    scale_b = cmds.floatSliderGrp(ui["scale_max"], query=True, value=True)
    return {
        "object": obj,
        "surface": surface,
        "count": cmds.intSliderGrp(ui["count"], query=True, value=True),
        "scale_min": min(scale_a, scale_b),
        "scale_max": max(scale_a, scale_b),
        "spin": cmds.floatSliderGrp(ui["spin"], query=True, value=True),
        "tilt": cmds.floatSliderGrp(ui["tilt"], query=True, value=True),
        "align": cmds.checkBox(ui["align"], query=True, value=True),
        "instances": cmds.checkBox(ui["instances"], query=True, value=True),
        "max_slope": cmds.floatSliderGrp(ui["max_slope"], query=True, value=True),
        "min_height": cmds.floatFieldGrp(ui["min_height"], query=True, value1=True),
        "seed": cmds.intFieldGrp(ui["seed"], query=True, value1=True),
    }


def skipped_note(skipped):
    if skipped:
        return " (%d spots skipped by the slope/height rules)" % skipped
    return ""


# ---------------------------------------------------------------
# Button actions
# ---------------------------------------------------------------

def delete_preview():
    """Remove the preview without adding anything to the undo list."""
    if cmds.objExists(PREVIEW_GROUP):
        cmds.undoInfo(stateWithoutFlush=False)
        try:
            cmds.delete(PREVIEW_GROUP)
        finally:
            cmds.undoInfo(stateWithoutFlush=True)


def restore_selection(selection):
    if selection:
        cmds.select(selection, replace=True)
    else:
        cmds.select(clear=True)


def on_preview(*_):
    settings = read_settings()
    if not settings:
        return
    selection = cmds.ls(selection=True)
    # The preview is temporary, so keep it out of the undo list.
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        if cmds.objExists(PREVIEW_GROUP):
            cmds.delete(PREVIEW_GROUP)
        group, skipped = build_scatter(settings, PREVIEW_GROUP, use_instances=True)
        restore_selection(selection)
    finally:
        cmds.undoInfo(stateWithoutFlush=True)
    set_status("Preview: %d copies%s. Press Apply to keep it."
               % (len(cmds.listRelatives(group, children=True) or []),
                  skipped_note(skipped)))


def refresh_preview(*_):
    """Called when a control changes; only redraws if a preview is showing."""
    if cmds.objExists(PREVIEW_GROUP):
        on_preview()


def on_apply(*_):
    settings = read_settings()
    if not settings:
        return
    delete_preview()
    selection = cmds.ls(selection=True)
    # One undo chunk, so one Ctrl+Z removes the whole scatter.
    cmds.undoInfo(openChunk=True, chunkName="Scatter")
    try:
        group, skipped = build_scatter(settings, "scatter_grp#",
                                       use_instances=settings["instances"])
        restore_selection(selection)
    finally:
        cmds.undoInfo(closeChunk=True)
    last_scatter["group"] = group
    count = len(cmds.listRelatives(group, children=True) or [])
    set_status("Made %d copies in '%s'%s. Ctrl+Z removes them all."
               % (count, group, skipped_note(skipped)))


def on_clear(*_):
    if cmds.objExists(PREVIEW_GROUP):
        delete_preview()
        set_status("Preview cleared.")
    elif last_scatter["group"] and cmds.objExists(last_scatter["group"]):
        cmds.delete(last_scatter["group"])
        set_status("Removed '%s'." % last_scatter["group"])
        last_scatter["group"] = None
    else:
        set_status("Nothing to clear.")


def use_selected(field, need_mesh):
    selection = cmds.ls(selection=True, transforms=True)
    if not selection:
        set_status("Nothing is selected. Click an object in the viewport first.")
        return
    name = selection[0]
    if need_mesh and not cmds.listRelatives(name, shapes=True, type="mesh",
                                            noIntermediate=True):
        set_status("'%s' isn't a polygon mesh, so it can't be a surface." % name)
        return
    cmds.textFieldButtonGrp(ui[field], edit=True, text=name)
    set_status("%s set to '%s'." % (field.capitalize(), name))
    refresh_preview()


def on_new_seed(*_):
    cmds.intFieldGrp(ui["seed"], edit=True, value1=random.randint(1, 99999))
    refresh_preview()


# ---------------------------------------------------------------
# The window
# ---------------------------------------------------------------

def show():
    if cmds.window(WINDOW, exists=True):
        cmds.deleteUI(WINDOW)
    cmds.window(WINDOW, title="Scatter Tool", widthHeight=(440, 520))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnAttach=("both", 8))

    cmds.separator(height=6, style="none")
    ui["object"] = cmds.textFieldButtonGrp(
        label="Object to scatter", buttonLabel="Use selected",
        columnWidth3=(110, 210, 90), changeCommand=refresh_preview,
        buttonCommand=lambda *_: use_selected("object", need_mesh=False))
    ui["surface"] = cmds.textFieldButtonGrp(
        label="Surface", buttonLabel="Use selected",
        columnWidth3=(110, 210, 90), changeCommand=refresh_preview,
        buttonCommand=lambda *_: use_selected("surface", need_mesh=True))

    cmds.separator(height=10)
    ui["count"] = cmds.intSliderGrp(
        label="Count", field=True, minValue=1, maxValue=500, value=50,
        columnWidth3=(110, 60, 240), changeCommand=refresh_preview)
    ui["scale_min"] = cmds.floatSliderGrp(
        label="Scale min", field=True, minValue=0.1, maxValue=5, value=0.8,
        precision=2, columnWidth3=(110, 60, 240), changeCommand=refresh_preview)
    ui["scale_max"] = cmds.floatSliderGrp(
        label="Scale max", field=True, minValue=0.1, maxValue=5, value=1.2,
        precision=2, columnWidth3=(110, 60, 240), changeCommand=refresh_preview)
    ui["spin"] = cmds.floatSliderGrp(
        label="Random spin", field=True, minValue=0, maxValue=360, value=360,
        precision=0, columnWidth3=(110, 60, 240), changeCommand=refresh_preview)
    ui["tilt"] = cmds.floatSliderGrp(
        label="Random tilt", field=True, minValue=0, maxValue=45, value=0,
        precision=0, columnWidth3=(110, 60, 240), changeCommand=refresh_preview)

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(250, 150),
                   columnAttach=(1, "left", 114))
    ui["align"] = cmds.checkBox(label="Align to surface", value=True,
                                changeCommand=refresh_preview)
    ui["instances"] = cmds.checkBox(label="Use instances", value=False)
    cmds.setParent("..")

    cmds.separator(height=10)
    cmds.text(label="Landing rules", align="left", font="boldLabelFont")
    ui["max_slope"] = cmds.floatSliderGrp(
        label="Max slope", field=True, minValue=0, maxValue=90, value=90,
        precision=0, columnWidth3=(110, 60, 240), changeCommand=refresh_preview)
    ui["min_height"] = cmds.floatFieldGrp(
        label="Min height", value1=-10000, precision=2,
        columnWidth2=(110, 80), changeCommand=refresh_preview)

    cmds.separator(height=10)
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(220, 100))
    ui["seed"] = cmds.intFieldGrp(label="Seed", value1=1, columnWidth2=(110, 80),
                                  changeCommand=refresh_preview)
    cmds.button(label="New seed", width=90, command=on_new_seed)
    cmds.setParent("..")

    cmds.separator(height=10)
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(140, 140, 140))
    cmds.button(label="Preview", width=134, command=on_preview)
    cmds.button(label="Apply", width=134, command=on_apply,
                backgroundColor=(0.35, 0.5, 0.35))
    cmds.button(label="Clear", width=134, command=on_clear)
    cmds.setParent("..")

    cmds.separator(height=10)
    ui["status"] = cmds.text(label="Select an object and a surface to start.",
                             align="left", wordWrap=True)
    cmds.showWindow(WINDOW)


if __name__ == "__main__":
    show()

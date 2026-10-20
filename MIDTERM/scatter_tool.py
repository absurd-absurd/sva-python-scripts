"""
Scatter Tool for Maya
Fayth Elisa Navarro - SVA Python midterm

Pick one or more objects and a surface, and the tool scatters copies
of the objects across the surface with random size, spin and tilt.
Objects with a bigger weight show up more often. Presets and your last
settings are saved to scatter_tool.json in Maya's user folder.

Run it from Maya's Script Editor (Python tab): File > Open Script,
pick this file, then Execute All (Ctrl+Enter).
"""

import bisect
import json
import math
import os
import random

import maya.cmds as cmds


WINDOW = "scatterToolWindow"
PREVIEW_GROUP = "scatter_preview"
WINDOW_HEIGHT = 650
NO_PRESET = "Pick a preset..."

# Presets and the last settings live here, e.g. Documents/maya/scatter_tool.json
SETTINGS_FILE = os.path.join(cmds.internalVar(userAppDir=True), "scatter_tool.json")

# Presets you get the first time, before you've saved any of your own
STARTER_PRESETS = {
    "Sparse rocks": {"count": 30, "scale_min": 0.6, "scale_max": 1.6,
                     "spin": 360.0, "tilt": 15.0, "align": True, "instances": False,
                     "max_slope": 35.0, "min_height": -10000.0, "seed": 1},
    "Dense grass": {"count": 400, "scale_min": 0.7, "scale_max": 1.1,
                    "spin": 360.0, "tilt": 10.0, "align": True, "instances": True,
                    "max_slope": 50.0, "min_height": -10000.0, "seed": 1},
}

# Names of the UI controls, filled in by show()
ui = {}

# The objects to scatter, as [name, weight] pairs, in list order
objects = []

# Name of the last group made with Apply, so Clear can remove it
last_scatter = {"group": None}

# The controls a preset saves: name -> (Maya command, flag holding the value)
CONTROLS = {
    "count": (cmds.intSliderGrp, "value"),
    "scale_min": (cmds.floatSliderGrp, "value"),
    "scale_max": (cmds.floatSliderGrp, "value"),
    "spin": (cmds.floatSliderGrp, "value"),
    "tilt": (cmds.floatSliderGrp, "value"),
    "align": (cmds.checkBox, "value"),
    "instances": (cmds.checkBox, "value"),
    "max_slope": (cmds.floatSliderGrp, "value"),
    "min_height": (cmds.floatFieldGrp, "value1"),
    "seed": (cmds.intFieldGrp, "value1"),
}


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
    Make the copies and put them in one new group. Returns the group,
    how many spots were skipped by the slope and height rules, and how
    many copies of each object were made.
    The same settings and seed always give the same layout.
    """
    names = [name for name, _ in settings["objects"]]
    running_weight = []
    total = 0.0
    for _, weight in settings["objects"]:
        total += weight
        running_weight.append(total)
    base_scales = dict((name, cmds.getAttr(name + ".scale")[0]) for name in names)

    triangles, running_area = surface_triangles(settings["surface"])
    rng = random.Random(settings["seed"])
    # A second random stream picks which object goes on each spot, so
    # changing the weights swaps objects but doesn't move any spots.
    object_rng = random.Random("objects %d" % settings["seed"])
    world_up = (0.0, 1.0, 0.0)

    group = cmds.group(empty=True, name=group_name)
    skipped = 0
    counts = dict((name, 0) for name in names)
    for _ in range(settings["count"]):
        # Always draw every random number, in the same order, so changing
        # one control doesn't reshuffle the whole layout.
        position, normal = random_spot(triangles, running_area, rng)
        tilt_angle = rng.uniform(0, settings["tilt"])
        tilt_direction = rng.uniform(0, 360)
        spin = rng.uniform(0, settings["spin"])
        size = rng.uniform(settings["scale_min"], settings["scale_max"])
        pick = object_rng.random() * total
        obj = names[min(bisect.bisect_right(running_weight, pick), len(names) - 1)]

        # Landing rules
        slope = math.degrees(math.acos(max(-1.0, min(1.0, normal[1]))))
        if slope > settings["max_slope"] or position[1] < settings["min_height"]:
            skipped += 1
            continue

        up = normal if settings["align"] else world_up
        up = tilt(up, tilt_angle, tilt_direction)
        base_scale = base_scales[obj]
        scale = (base_scale[0] * size, base_scale[1] * size, base_scale[2] * size)

        if use_instances:
            copy = make_instance(obj, group)
        else:
            copy = cmds.duplicate(obj, returnRootsOnly=True)[0]
            copy = cmds.parent(copy, group)[0]
        cmds.xform(copy, worldSpace=True,
                   matrix=placement_matrix(position, up, spin, scale))
        counts[obj] += 1
    return group, skipped, counts


# ---------------------------------------------------------------
# Reading and checking the window's controls
# ---------------------------------------------------------------

def set_status(message):
    if cmds.text(ui.get("status", ""), exists=True):
        cmds.text(ui["status"], edit=True, label=message)
    print("Scatter: " + message)


def read_controls():
    """The values of the sliders and boxes, which is what a preset saves."""
    return dict((key, command(ui[key], query=True, **{flag: True}))
                for key, (command, flag) in CONTROLS.items())


def set_controls(values):
    """Put saved values back into the window. Missing or bad ones are skipped."""
    for key, (command, flag) in CONTROLS.items():
        if key in values:
            try:
                command(ui[key], edit=True, **{flag: values[key]})
            except (RuntimeError, TypeError):
                print("Scatter: couldn't set %s to %r" % (key, values[key]))


def read_settings():
    """Read the window. Returns the settings, or None and shows why not."""
    surface = cmds.textFieldButtonGrp(ui["surface"], query=True, text=True).strip()

    if not objects:
        set_status("Add an object to scatter first (select it, then 'Add selected').")
        return None
    for name, _ in objects:
        if not cmds.objExists(name):
            set_status("Can't find an object called '%s'. Remove it from the list." % name)
            return None
    if sum(weight for _, weight in objects) <= 0:
        set_status("Every weight is 0. Give at least one object a weight above 0.")
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
    if surface in [name for name, _ in objects]:
        set_status("'%s' is the surface and also in the object list. Remove it from the list."
                   % surface)
        return None

    settings = read_controls()
    scale_a, scale_b = settings["scale_min"], settings["scale_max"]
    settings["scale_min"] = min(scale_a, scale_b)
    settings["scale_max"] = max(scale_a, scale_b)
    settings["objects"] = [(name, weight) for name, weight in objects if weight > 0]
    settings["surface"] = surface
    return settings


def skipped_note(skipped):
    if skipped:
        return " (%d spots skipped by the slope/height rules)" % skipped
    return ""


def counts_note(counts):
    """'50 copies' for one object, '50 copies (rock 31, bush 19)' for more."""
    note = "%d copies" % sum(counts.values())
    if len(counts) > 1:
        note += " (%s)" % ", ".join("%s %d" % (name, n) for name, n in counts.items())
    return note


# ---------------------------------------------------------------
# The settings file: presets and the last settings used
# ---------------------------------------------------------------

def load_saved():
    """Read the settings file. Always returns {"presets": ..., "last": ...}."""
    data = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
        except (IOError, OSError, ValueError):
            print("Scatter: couldn't read %s, starting fresh." % SETTINGS_FILE)
    if not isinstance(data, dict):
        data = {}
    # Only the very first time: once you delete the starters they stay gone.
    data.setdefault("presets", dict(STARTER_PRESETS))
    data.setdefault("last", {})
    return data


def save_saved(data):
    try:
        folder = os.path.dirname(SETTINGS_FILE)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        return True
    except (IOError, OSError) as error:
        set_status("Couldn't save to %s: %s" % (SETTINGS_FILE, error))
        return False


def remember_settings(*_):
    """Save everything in the window, so it comes back next time."""
    data = load_saved()
    data["last"] = read_controls()
    data["last"]["objects"] = objects
    data["last"]["surface"] = cmds.textFieldButtonGrp(ui["surface"], query=True,
                                                      text=True).strip()
    save_saved(data)


def restore_settings():
    """Fill the window with the last settings. Returns True if there were any."""
    last = load_saved()["last"]
    set_controls(last)
    surface = last.get("surface", "")
    if surface and cmds.objExists(surface):
        cmds.textFieldButtonGrp(ui["surface"], edit=True, text=surface)
    # Only bring back objects that are in this scene.
    del objects[:]
    try:
        for name, weight in last.get("objects", []):
            if cmds.objExists(name):
                objects.append([name, float(weight)])
    except (TypeError, ValueError):
        pass
    return bool(last)


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
        group, skipped, counts = build_scatter(settings, PREVIEW_GROUP,
                                               use_instances=True)
        restore_selection(selection)
    finally:
        cmds.undoInfo(stateWithoutFlush=True)
    set_status("Preview: %s%s. Press Apply to keep it."
               % (counts_note(counts), skipped_note(skipped)))


def refresh_preview(*_):
    """Only redraws if a preview is showing."""
    if cmds.objExists(PREVIEW_GROUP):
        on_preview()


def on_change(*_):
    """Called when any control changes."""
    remember_settings()
    refresh_preview()


def on_apply(*_):
    settings = read_settings()
    if not settings:
        return
    delete_preview()
    selection = cmds.ls(selection=True)
    # One undo chunk, so one Ctrl+Z removes the whole scatter.
    cmds.undoInfo(openChunk=True, chunkName="Scatter")
    try:
        group, skipped, counts = build_scatter(settings, "scatter_grp#",
                                               use_instances=settings["instances"])
        restore_selection(selection)
    finally:
        cmds.undoInfo(closeChunk=True)
    last_scatter["group"] = group
    set_status("Made %s in '%s'%s. Ctrl+Z removes them all."
               % (counts_note(counts), group, skipped_note(skipped)))


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


def use_selected_surface(*_):
    selection = cmds.ls(selection=True, transforms=True)
    if not selection:
        set_status("Nothing is selected. Click an object in the viewport first.")
        return
    name = selection[0]
    if not cmds.listRelatives(name, shapes=True, type="mesh", noIntermediate=True):
        set_status("'%s' isn't a polygon mesh, so it can't be a surface." % name)
        return
    cmds.textFieldButtonGrp(ui["surface"], edit=True, text=name)
    set_status("Surface set to '%s'." % name)
    on_change()


def on_new_seed(*_):
    cmds.intFieldGrp(ui["seed"], edit=True, value1=random.randint(1, 99999))
    on_change()


# ---------------------------------------------------------------
# The object list and weights
# ---------------------------------------------------------------

def selected_row():
    """Index of the highlighted row in the object list, or None."""
    rows = cmds.textScrollList(ui["objects"], query=True, selectIndexedItem=True)
    return rows[0] - 1 if rows else None


def redraw_object_list(select=None):
    """Show each object with its weight and its share of the copies."""
    total = sum(weight for _, weight in objects)
    cmds.textScrollList(ui["objects"], edit=True, removeAll=True)
    for name, weight in objects:
        share = 100.0 * weight / total if total > 0 else 0.0
        cmds.textScrollList(ui["objects"], edit=True,
                            append="%s    weight %g    (%d%%)" % (name, weight, round(share)))
    if select is not None and 0 <= select < len(objects):
        cmds.textScrollList(ui["objects"], edit=True, selectIndexedItem=select + 1)
    show_row_weight()


def show_row_weight(*_):
    """Put the highlighted object's weight in the Weight box."""
    row = selected_row()
    if row is None:
        cmds.floatFieldGrp(ui["weight"], edit=True, enable=False, value1=1)
    else:
        cmds.floatFieldGrp(ui["weight"], edit=True, enable=True, value1=objects[row][1])


def on_add_objects(*_):
    selection = cmds.ls(selection=True, transforms=True)
    if not selection:
        set_status("Nothing is selected. Click one or more objects in the viewport first.")
        return
    surface = cmds.textFieldButtonGrp(ui["surface"], query=True, text=True).strip()
    in_list = [name for name, _ in objects]
    added = []
    for name in selection:
        if name != surface and name not in in_list:
            objects.append([name, 1.0])
            added.append(name)
    if not added:
        set_status("Those are already in the list (or are the surface).")
        return
    redraw_object_list(select=len(objects) - 1)
    set_status("Added %s. Click a row to change its weight." % ", ".join(added))
    on_change()


def on_remove_object(*_):
    row = selected_row()
    if row is None:
        set_status("Click an object in the list first, then Remove.")
        return
    name = objects.pop(row)[0]
    redraw_object_list(select=min(row, len(objects) - 1))
    set_status("Removed '%s' from the list." % name)
    on_change()


def on_weight_change(*_):
    row = selected_row()
    if row is None:
        return
    weight = max(0.0, cmds.floatFieldGrp(ui["weight"], query=True, value1=True))
    objects[row][1] = weight
    redraw_object_list(select=row)
    on_change()


# ---------------------------------------------------------------
# Presets
# ---------------------------------------------------------------

def redraw_preset_menu(select=None):
    for item in cmds.optionMenu(ui["preset"], query=True, itemListLong=True) or []:
        cmds.deleteUI(item)
    names = sorted(load_saved()["presets"], key=str.lower)
    for name in [NO_PRESET] + names:
        cmds.menuItem(label=name, parent=ui["preset"])
    if select in names:
        cmds.optionMenu(ui["preset"], edit=True, value=select)


def on_pick_preset(name):
    if name == NO_PRESET:
        return
    preset = load_saved()["presets"].get(name)
    if preset is None:
        set_status("The preset '%s' is gone from the file." % name)
        redraw_preset_menu()
        return
    set_controls(preset)
    set_status("Loaded the preset '%s'." % name)
    on_change()


def on_save_preset(*_):
    current = cmds.optionMenu(ui["preset"], query=True, value=True)
    answer = cmds.promptDialog(
        title="Save preset", message="Name for this preset:",
        text="" if current == NO_PRESET else current,
        button=["Save", "Cancel"], defaultButton="Save",
        cancelButton="Cancel", dismissString="Cancel")
    if answer != "Save":
        return
    name = cmds.promptDialog(query=True, text=True).strip()
    if not name or name == NO_PRESET:
        set_status("The preset needs a name. Nothing was saved.")
        return
    data = load_saved()
    if name in data["presets"]:
        replace = cmds.confirmDialog(
            title="Save preset", message="Replace the preset '%s'?" % name,
            button=["Replace", "Cancel"], defaultButton="Replace",
            cancelButton="Cancel", dismissString="Cancel")
        if replace != "Replace":
            return
    data["presets"][name] = read_controls()
    if save_saved(data):
        redraw_preset_menu(select=name)
        set_status("Saved the preset '%s'." % name)


def on_delete_preset(*_):
    name = cmds.optionMenu(ui["preset"], query=True, value=True)
    if name == NO_PRESET:
        set_status("Pick a preset in the menu first, then Delete preset.")
        return
    answer = cmds.confirmDialog(
        title="Delete preset", message="Delete the preset '%s'?" % name,
        button=["Delete", "Cancel"], defaultButton="Cancel",
        cancelButton="Cancel", dismissString="Cancel")
    if answer != "Delete":
        return
    data = load_saved()
    data["presets"].pop(name, None)
    if save_saved(data):
        redraw_preset_menu()
        set_status("Deleted the preset '%s'." % name)


# ---------------------------------------------------------------
# The window
# ---------------------------------------------------------------

def show():
    if cmds.window(WINDOW, exists=True):
        cmds.deleteUI(WINDOW)
    # Maya reopens a window at its last size, which may be from before the
    # object list was added. If that's too short, forget it. The saved size
    # is in screen pixels, so it's doubled on a screen scaled to 200%.
    ui_scale = cmds.mayaDpiSetting(query=True, realScaleValue=True)
    if (cmds.windowPref(WINDOW, exists=True)
            and cmds.windowPref(WINDOW, query=True, height=True) < WINDOW_HEIGHT * ui_scale):
        cmds.windowPref(WINDOW, remove=True)
    cmds.window(WINDOW, title="Scatter Tool", widthHeight=(440, WINDOW_HEIGHT))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnAttach=("both", 8))

    cmds.separator(height=6, style="none")
    cmds.text(label="Objects to scatter", align="left", font="boldLabelFont")
    ui["objects"] = cmds.textScrollList(numberOfRows=4, allowMultiSelection=False,
                                        selectCommand=show_row_weight)
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(110, 110, 200))
    cmds.button(label="Add selected", width=104, command=on_add_objects)
    cmds.button(label="Remove", width=104, command=on_remove_object)
    ui["weight"] = cmds.floatFieldGrp(label="Weight", value1=1, precision=1,
                                      columnWidth2=(50, 70), enable=False,
                                      changeCommand=on_weight_change)
    cmds.setParent("..")
    ui["surface"] = cmds.textFieldButtonGrp(
        label="Surface", buttonLabel="Use selected",
        columnWidth3=(110, 210, 90), changeCommand=on_change,
        buttonCommand=use_selected_surface)

    cmds.separator(height=10)
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(220, 100, 100))
    ui["preset"] = cmds.optionMenu(label="Preset", width=210,
                                   changeCommand=on_pick_preset)
    cmds.button(label="Save preset", width=94, command=on_save_preset)
    cmds.button(label="Delete preset", width=94, command=on_delete_preset)
    cmds.setParent("..")

    ui["count"] = cmds.intSliderGrp(
        label="Count", field=True, minValue=1, maxValue=500, value=50,
        columnWidth3=(110, 60, 240), changeCommand=on_change)
    ui["scale_min"] = cmds.floatSliderGrp(
        label="Scale min", field=True, minValue=0.1, maxValue=5, value=0.8,
        precision=2, columnWidth3=(110, 60, 240), changeCommand=on_change)
    ui["scale_max"] = cmds.floatSliderGrp(
        label="Scale max", field=True, minValue=0.1, maxValue=5, value=1.2,
        precision=2, columnWidth3=(110, 60, 240), changeCommand=on_change)
    ui["spin"] = cmds.floatSliderGrp(
        label="Random spin", field=True, minValue=0, maxValue=360, value=360,
        precision=0, columnWidth3=(110, 60, 240), changeCommand=on_change)
    ui["tilt"] = cmds.floatSliderGrp(
        label="Random tilt", field=True, minValue=0, maxValue=45, value=0,
        precision=0, columnWidth3=(110, 60, 240), changeCommand=on_change)

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(250, 150),
                   columnAttach=(1, "left", 114))
    ui["align"] = cmds.checkBox(label="Align to surface", value=True,
                                changeCommand=on_change)
    ui["instances"] = cmds.checkBox(label="Use instances", value=False,
                                    changeCommand=remember_settings)
    cmds.setParent("..")

    cmds.separator(height=10)
    cmds.text(label="Landing rules", align="left", font="boldLabelFont")
    ui["max_slope"] = cmds.floatSliderGrp(
        label="Max slope", field=True, minValue=0, maxValue=90, value=90,
        precision=0, columnWidth3=(110, 60, 240), changeCommand=on_change)
    ui["min_height"] = cmds.floatFieldGrp(
        label="Min height", value1=-10000, precision=2,
        columnWidth2=(110, 80), changeCommand=on_change)

    cmds.separator(height=10)
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(220, 100))
    ui["seed"] = cmds.intFieldGrp(label="Seed", value1=1, columnWidth2=(110, 80),
                                  changeCommand=on_change)
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
    ui["status"] = cmds.text(label="", align="left", wordWrap=True)
    cmds.showWindow(WINDOW)

    had_settings = restore_settings()
    redraw_object_list()
    redraw_preset_menu()
    if had_settings:
        set_status("Your settings from last time are back.")
    else:
        set_status("Add objects to scatter and pick a surface to start.")


if __name__ == "__main__":
    show()

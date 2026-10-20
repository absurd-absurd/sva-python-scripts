"""
Scatter Tool for Maya
Fayth Elisa Navarro - SVA Python midterm

Pick a surface and set up one or more networks: a network is a set of
objects (say five rocks) that share the same settings. The tool scatters
copies of every network across the surface with random size, spin and
tilt. Inside a network, objects with a bigger weight show up more often.
Presets and your last settings are saved to scatter_tool.json in Maya's
user folder.

Run it from Maya's Script Editor (Python tab): File > Open Script,
pick this file, then Execute All (Ctrl+Enter).
"""

import bisect
import json
import math
import os
import random
import re

import maya.cmds as cmds


WINDOW = "scatterToolWindow"
PREVIEW_GROUP = "scatter_preview"
WINDOW_HEIGHT = 740
NO_PRESET = "Pick a preset..."

# How many other spots to try when a copy lands too close to another one
SPACING_TRIES = 30

# Presets and the last settings live here, e.g. Documents/maya/scatter_tool.json
SETTINGS_FILE = os.path.join(cmds.internalVar(userAppDir=True), "scatter_tool.json")

# The settings a new network starts with
DEFAULT_CONTROLS = {"count": 50, "scale_min": 0.8, "scale_max": 1.2,
                    "spin": 360.0, "tilt": 0.0, "align": True, "instances": False,
                    "max_slope": 90.0, "min_height": -10000.0,
                    "spacing": False, "min_distance": 1.0, "seed": 1}

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

# The networks, in menu order. Each one is a dict:
#   name     - shown in the Network menu
#   use      - False leaves it out of Preview and Apply
#   objects  - [name, weight] pairs
#   controls - its slider and checkbox values (same keys as DEFAULT_CONTROLS)
networks = []

# Which network the window is showing
current = {"index": 0}

# Name of the last group made with Apply, so Clear can remove it
last_scatter = {"group": None}

# The controls a network or preset saves: name -> (Maya command, flag holding the value)
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
    "spacing": (cmds.checkBox, "value"),
    "min_distance": (cmds.floatSliderGrp, "value"),
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


# ---------------------------------------------------------------
# Keeping copies apart
# ---------------------------------------------------------------
# Every copy placed so far goes in a grid of square cells on the ground
# (x and z), so checking a new spot only looks at the 9 cells around it
# instead of every copy. Each copy keeps a circle of ground clear around it:
# half its network's min distance. Two copies are too close when their
# circles overlap.

def spacing_grid(cell_size):
    # A cell must be at least as wide as the biggest gap, so a too-close
    # copy is always in one of the 9 cells around the new spot.
    return {"cell": max(cell_size, 0.001), "cells": {}}


def grid_cell(grid, point):
    return (int(math.floor(point[0] / grid["cell"])),
            int(math.floor(point[2] / grid["cell"])))


def too_close(grid, point, radius):
    """True if a circle of 'radius' at point overlaps a copy already placed."""
    cx, cz = grid_cell(grid, point)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for x, z, other in grid["cells"].get((cx + dx, cz + dz), ()):
                gap = radius + other
                if (point[0] - x) ** 2 + (point[2] - z) ** 2 < gap * gap:
                    return True
    return False


def mark_placed(grid, point, radius):
    grid["cells"].setdefault(grid_cell(grid, point), []).append(
        (point[0], point[2], radius))


def lands(position, normal, settings):
    """True if the landing rules (max slope, min height) allow this spot."""
    slope = math.degrees(math.acos(max(-1.0, min(1.0, normal[1]))))
    return slope <= settings["max_slope"] and position[1] >= settings["min_height"]


def build_scatter(settings, group, use_instances, grid):
    """
    Make one network's copies inside 'group'. 'grid' holds every copy
    placed so far, from any network. Returns how many spots were skipped
    by the slope and height rules, how many copies didn't fit because of
    the min distance, and how many copies of each object were made.
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
    # A third stream gives the extra spots tried when a copy is too close,
    # so with Keep copies apart off, the layout is the same as without it.
    retry_rng = random.Random("spacing %d" % settings["seed"])
    world_up = (0.0, 1.0, 0.0)
    radius = settings["min_distance"] / 2.0 if settings["spacing"] else 0.0

    skipped = 0
    crowded = 0
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

        if not lands(position, normal, settings):
            skipped += 1
            continue
        if settings["spacing"] and too_close(grid, position, radius):
            for _ in range(SPACING_TRIES):
                position, normal = random_spot(triangles, running_area, retry_rng)
                if lands(position, normal, settings) and not too_close(grid, position, radius):
                    break
            else:
                crowded += 1
                continue
        mark_placed(grid, position, radius)

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
    return skipped, crowded, counts


def group_name_for(network_name):
    """'Small rocks' -> 'Small_rocks', since Maya names can't have spaces."""
    name = re.sub(r"[^A-Za-z0-9_]", "_", network_name)
    return name if re.match(r"[A-Za-z_]", name) else "n_" + name


def build_all(all_settings, group_name, preview):
    """
    Scatter every network into one new group, each network in its own
    group inside it. Returns the group, the total spots skipped by the
    landing rules, the total copies that didn't fit, and
    (network name, counts) for each network.
    """
    def gap(settings):
        return settings["min_distance"] if settings["spacing"] else 0.0

    top = cmds.group(empty=True, name=group_name)
    groups = [cmds.group(empty=True, parent=top, name=group_name_for(settings["name"]))
              for settings in all_settings]
    grid = spacing_grid(max(gap(settings) for settings in all_settings))
    skipped = 0
    crowded = 0
    counts_by_network = {}
    # The networks with the most space around their copies go first, so
    # big things like trees get their room before small rocks fill in.
    order = sorted(range(len(all_settings)), key=lambda i: -gap(all_settings[i]))
    for i in order:
        settings = all_settings[i]
        net_skipped, net_crowded, counts = build_scatter(
            settings, groups[i], use_instances=preview or settings["instances"], grid=grid)
        skipped += net_skipped
        crowded += net_crowded
        counts_by_network[i] = counts
    made = [(settings["name"], counts_by_network[i]) for i, settings in enumerate(all_settings)]
    return top, skipped, crowded, made


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
    sync_spacing()


def sync_spacing(*_):
    """Min distance can only be changed while Keep copies apart is ticked."""
    on = cmds.checkBox(ui["spacing"], query=True, value=True)
    cmds.floatSliderGrp(ui["min_distance"], edit=True, enable=on)
    cmds.button(ui["fit_distance"], edit=True, enable=on)


def read_settings():
    """
    Read the window. Returns a list with the settings of each network
    that's switched on, or None and shows why not.
    """
    surface = cmds.textFieldButtonGrp(ui["surface"], query=True, text=True).strip()
    if not surface:
        set_status("Pick a surface first (select it, then 'Use selected').")
        return None
    if not cmds.objExists(surface):
        set_status("Can't find a surface called '%s'." % surface)
        return None
    if not cmds.listRelatives(surface, shapes=True, type="mesh", noIntermediate=True):
        set_status("'%s' isn't a polygon mesh, so it can't be a surface." % surface)
        return None

    store_controls()
    used = [net for net in networks if net["use"]]
    if not used:
        set_status("Every network is switched off. Tick 'Include in scatter' on at least one.")
        return None

    all_settings = []
    for net in used:
        # Say which network the problem is in, once there's more than one
        where = "In '%s': " % net["name"] if len(networks) > 1 else ""
        objects = net["objects"]
        if not objects:
            set_status(where + "Add an object to scatter first (select it, then 'Add selected').")
            return None
        for name, _ in objects:
            if not cmds.objExists(name):
                set_status(where + "Can't find an object called '%s'. Remove it from the list."
                           % name)
                return None
        if sum(weight for _, weight in objects) <= 0:
            set_status(where + "Every weight is 0. Give at least one object a weight above 0.")
            return None
        if surface in [name for name, _ in objects]:
            set_status(where + "'%s' is the surface and also in the object list. "
                       "Remove it from the list." % surface)
            return None

        settings = dict(DEFAULT_CONTROLS, **net["controls"])
        scale_a, scale_b = settings["scale_min"], settings["scale_max"]
        settings["scale_min"] = min(scale_a, scale_b)
        settings["scale_max"] = max(scale_a, scale_b)
        settings["objects"] = [(name, weight) for name, weight in objects if weight > 0]
        settings["surface"] = surface
        settings["name"] = net["name"]
        all_settings.append(settings)
    return all_settings


def skipped_note(skipped, crowded):
    notes = []
    if skipped:
        notes.append("%d spots skipped by the slope/height rules" % skipped)
    if crowded:
        notes.append("%d copies didn't fit with the min distance" % crowded)
    return " (%s)" % "; ".join(notes) if notes else ""


def counts_note(counts):
    """'50 copies' for one object, '50 copies (rock 31, bush 19)' for more."""
    note = "%d copies" % sum(counts.values())
    if len(counts) > 1:
        note += " (%s)" % ", ".join("%s %d" % (name, n) for name, n in counts.items())
    return note


def made_note(made):
    """counts_note for one network, '80 copies (Small rocks 60, Large trees 20)' for more."""
    if len(made) == 1:
        return counts_note(made[0][1])
    total = sum(sum(counts.values()) for _, counts in made)
    return "%d copies (%s)" % (total, ", ".join("%s %d" % (name, sum(counts.values()))
                                                 for name, counts in made))


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
    store_controls()
    data = load_saved()
    data["last"] = {
        "surface": cmds.textFieldButtonGrp(ui["surface"], query=True, text=True).strip(),
        "networks": networks,
        "current": current["index"],
    }
    save_saved(data)


def saved_objects(saved):
    """The [name, weight] pairs from the file that are in this scene."""
    return [[name, float(weight)] for name, weight in saved.get("objects", [])
            if cmds.objExists(name)]


def restore_settings():
    """Load the last networks and surface. Returns True if there were any."""
    last = load_saved()["last"]
    surface = last.get("surface", "")
    if surface and cmds.objExists(surface):
        cmds.textFieldButtonGrp(ui["surface"], edit=True, text=surface)

    del networks[:]
    current["index"] = 0
    try:
        if "networks" in last:
            for saved in last["networks"]:
                net = make_network(str(saved["name"]))
                net["use"] = bool(saved.get("use", True))
                net["controls"].update(saved.get("controls", {}))
                net["objects"] = saved_objects(saved)
                networks.append(net)
            current["index"] = min(max(int(last.get("current", 0)), 0), len(networks) - 1)
        elif last:
            # Saved before networks existed: those settings become the first network
            net = make_network("Network 1")
            net["controls"].update((key, last[key]) for key in DEFAULT_CONTROLS if key in last)
            net["objects"] = saved_objects(last)
            networks.append(net)
    except (TypeError, ValueError, KeyError, AttributeError):
        print("Scatter: the saved networks didn't make sense, starting fresh.")
        del networks[:]
        current["index"] = 0
    if not networks:
        networks.append(make_network("Network 1"))
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
    all_settings = read_settings()
    if not all_settings:
        return
    selection = cmds.ls(selection=True)
    # The preview is temporary, so keep it out of the undo list.
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        if cmds.objExists(PREVIEW_GROUP):
            cmds.delete(PREVIEW_GROUP)
        group, skipped, crowded, made = build_all(all_settings, PREVIEW_GROUP, preview=True)
        restore_selection(selection)
    finally:
        cmds.undoInfo(stateWithoutFlush=True)
    set_status("Preview: %s%s. Press Apply to keep it."
               % (made_note(made), skipped_note(skipped, crowded)))


def refresh_preview(*_):
    """Only redraws if a preview is showing."""
    if cmds.objExists(PREVIEW_GROUP):
        on_preview()


def on_change(*_):
    """Called when any control changes."""
    remember_settings()
    refresh_preview()


def on_apply(*_):
    all_settings = read_settings()
    if not all_settings:
        return
    delete_preview()
    selection = cmds.ls(selection=True)
    # One undo chunk, so one Ctrl+Z removes the whole scatter.
    cmds.undoInfo(openChunk=True, chunkName="Scatter")
    try:
        group, skipped, crowded, made = build_all(all_settings, "scatter_grp#", preview=False)
        restore_selection(selection)
    finally:
        cmds.undoInfo(closeChunk=True)
    last_scatter["group"] = group
    set_status("Made %s in '%s'%s. Ctrl+Z removes them all."
               % (made_note(made), group, skipped_note(skipped, crowded)))


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


def on_spacing(*_):
    sync_spacing()
    on_change()


def on_fit_distance(*_):
    """Set Min distance to the widest object at Scale max, so copies don't touch."""
    names = [name for name, _ in network()["objects"] if cmds.objExists(name)]
    if not names:
        set_status("Add objects to this network first, then Fit to size.")
        return
    widest, widest_name = 0.0, names[0]
    for name in names:
        box = cmds.exactWorldBoundingBox(name)  # xmin ymin zmin xmax ymax zmax
        width = max(box[3] - box[0], box[5] - box[2])
        if width > widest:
            widest, widest_name = width, name
    scale_max = max(cmds.floatSliderGrp(ui["scale_min"], query=True, value=True),
                    cmds.floatSliderGrp(ui["scale_max"], query=True, value=True))
    distance = round(widest * scale_max, 2)
    cmds.floatSliderGrp(ui["min_distance"], edit=True, value=distance)
    set_status("Min distance set to %g: '%s' is %.2f wide, times Scale max %g."
               % (distance, widest_name, widest, scale_max))
    on_change()


# ---------------------------------------------------------------
# Networks
# ---------------------------------------------------------------

def make_network(name, seed=1):
    controls = dict(DEFAULT_CONTROLS)
    controls["seed"] = seed
    return {"name": name, "use": True, "objects": [], "controls": controls}


def network():
    """The network the window is showing."""
    return networks[current["index"]]


def network_names():
    return [net["name"] for net in networks]


def store_controls():
    """Copy the sliders into the network the window is showing."""
    if networks and cmds.intSliderGrp(ui.get("count", ""), exists=True):
        network()["controls"] = read_controls()


def show_network():
    """Fill the window with the current network's settings and objects."""
    net = network()
    set_controls(dict(DEFAULT_CONTROLS, **net["controls"]))
    cmds.checkBox(ui["use"], edit=True, value=net["use"])
    redraw_object_list()


def redraw_network_menu():
    for item in cmds.optionMenu(ui["network"], query=True, itemListLong=True) or []:
        cmds.deleteUI(item)
    for name in network_names():
        cmds.menuItem(label=name, parent=ui["network"])
    cmds.optionMenu(ui["network"], edit=True, select=current["index"] + 1)


def ask_network_name(title, text):
    """Ask for a network name. Returns it, or None if cancelled or taken."""
    answer = cmds.promptDialog(
        title=title, message="Network name:", text=text,
        button=["OK", "Cancel"], defaultButton="OK",
        cancelButton="Cancel", dismissString="Cancel")
    if answer != "OK":
        return None
    name = cmds.promptDialog(query=True, text=True).strip()
    if not name:
        set_status("The network needs a name.")
        return None
    if name in network_names() and name != network()["name"]:
        set_status("There's already a network called '%s'." % name)
        return None
    return name


def on_pick_network(name):
    store_controls()
    current["index"] = network_names().index(name)
    show_network()
    set_status("Showing the network '%s'." % name)
    remember_settings()


def on_new_network(*_):
    store_controls()
    number = len(networks) + 1
    while "Network %d" % number in network_names():
        number += 1
    name = ask_network_name("New network", "Network %d" % number)
    if name is None or name in network_names():
        if name is not None:
            set_status("There's already a network called '%s'." % name)
        return
    # A new seed, so this network doesn't land on the same spots as the others
    networks.append(make_network(name, seed=random.randint(1, 99999)))
    current["index"] = len(networks) - 1
    redraw_network_menu()
    show_network()
    set_status("Made the network '%s'. Add its objects, then set its sliders." % name)
    on_change()


def on_rename_network(*_):
    old = network()["name"]
    name = ask_network_name("Rename network", old)
    if name is None or name == old:
        return
    network()["name"] = name
    redraw_network_menu()
    set_status("Renamed '%s' to '%s'." % (old, name))
    on_change()


def on_delete_network(*_):
    if len(networks) == 1:
        set_status("You need at least one network. Rename this one instead.")
        return
    name = network()["name"]
    answer = cmds.confirmDialog(
        title="Delete network", message="Delete the network '%s'?" % name,
        button=["Delete", "Cancel"], defaultButton="Cancel",
        cancelButton="Cancel", dismissString="Cancel")
    if answer != "Delete":
        return
    networks.pop(current["index"])
    current["index"] = min(current["index"], len(networks) - 1)
    redraw_network_menu()
    show_network()
    set_status("Deleted the network '%s'." % name)
    on_change()


def on_use_network(value):
    network()["use"] = bool(value)
    on_change()


# ---------------------------------------------------------------
# The object list and weights (for the network the window is showing)
# ---------------------------------------------------------------

def selected_row():
    """Index of the highlighted row in the object list, or None."""
    rows = cmds.textScrollList(ui["objects"], query=True, selectIndexedItem=True)
    return rows[0] - 1 if rows else None


def redraw_object_list(select=None):
    """Show each object with its weight and its share of the copies."""
    objects = network()["objects"]
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
        cmds.floatFieldGrp(ui["weight"], edit=True, enable=True,
                           value1=network()["objects"][row][1])


def on_add_objects(*_):
    selection = cmds.ls(selection=True, transforms=True)
    if not selection:
        set_status("Nothing is selected. Click one or more objects in the viewport first.")
        return
    surface = cmds.textFieldButtonGrp(ui["surface"], query=True, text=True).strip()
    objects = network()["objects"]
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
    set_status("Added %s to '%s'. Click a row to change its weight."
               % (", ".join(added), network()["name"]))
    on_change()


def on_remove_object(*_):
    row = selected_row()
    if row is None:
        set_status("Click an object in the list first, then Remove.")
        return
    objects = network()["objects"]
    name = objects.pop(row)[0]
    redraw_object_list(select=min(row, len(objects) - 1))
    set_status("Removed '%s' from the list." % name)
    on_change()


def on_weight_change(*_):
    row = selected_row()
    if row is None:
        return
    weight = max(0.0, cmds.floatFieldGrp(ui["weight"], query=True, value1=True))
    network()["objects"][row][1] = weight
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
    set_status("Loaded the preset '%s' into '%s'." % (name, network()["name"]))
    on_change()


def on_save_preset(*_):
    current_preset = cmds.optionMenu(ui["preset"], query=True, value=True)
    answer = cmds.promptDialog(
        title="Save preset", message="Name for this preset:",
        text="" if current_preset == NO_PRESET else current_preset,
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
    # Maya reopens a window at its last size, which may be from an older,
    # shorter version of this window. If that's too short, forget it. The
    # saved size is in screen pixels, so it's doubled on a screen scaled to 200%.
    ui_scale = cmds.mayaDpiSetting(query=True, realScaleValue=True)
    if (cmds.windowPref(WINDOW, exists=True)
            and cmds.windowPref(WINDOW, query=True, height=True) < WINDOW_HEIGHT * ui_scale):
        cmds.windowPref(WINDOW, remove=True)
    cmds.window(WINDOW, title="Scatter Tool", widthHeight=(440, WINDOW_HEIGHT))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnAttach=("both", 8))

    cmds.separator(height=6, style="none")
    ui["surface"] = cmds.textFieldButtonGrp(
        label="Surface", buttonLabel="Use selected",
        columnWidth3=(60, 260, 90), changeCommand=on_change,
        buttonCommand=use_selected_surface)

    cmds.separator(height=10)
    cmds.rowLayout(numberOfColumns=4, columnWidth4=(200, 70, 70, 70))
    ui["network"] = cmds.optionMenu(label="Network", width=192,
                                    changeCommand=on_pick_network)
    cmds.button(label="New", width=64, command=on_new_network)
    cmds.button(label="Rename", width=64, command=on_rename_network)
    cmds.button(label="Delete", width=64, command=on_delete_network)
    cmds.setParent("..")
    ui["use"] = cmds.checkBox(label="Include in scatter (Preview and Apply)", value=True,
                              changeCommand=on_use_network)

    cmds.text(label="Objects in this network", align="left", font="boldLabelFont")
    ui["objects"] = cmds.textScrollList(numberOfRows=4, allowMultiSelection=False,
                                        selectCommand=show_row_weight)
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(110, 110, 200))
    cmds.button(label="Add selected", width=104, command=on_add_objects)
    cmds.button(label="Remove", width=104, command=on_remove_object)
    ui["weight"] = cmds.floatFieldGrp(label="Weight", value1=1, precision=1,
                                      columnWidth2=(50, 70), enable=False,
                                      changeCommand=on_weight_change)
    cmds.setParent("..")

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

    cmds.text(label="Landing rules", align="left", font="boldLabelFont")
    ui["max_slope"] = cmds.floatSliderGrp(
        label="Max slope", field=True, minValue=0, maxValue=90, value=90,
        precision=0, columnWidth3=(110, 60, 240), changeCommand=on_change)
    ui["min_height"] = cmds.floatFieldGrp(
        label="Min height", value1=-10000, precision=2,
        columnWidth2=(110, 80), changeCommand=on_change)
    ui["spacing"] = cmds.checkBox(label="Keep copies apart (no overlapping)", value=False,
                                  changeCommand=on_spacing)
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(330, 90))
    ui["min_distance"] = cmds.floatSliderGrp(
        label="Min distance", field=True, minValue=0, maxValue=10, fieldMaxValue=1000,
        value=1, precision=2, columnWidth3=(110, 60, 150), changeCommand=on_change)
    ui["fit_distance"] = cmds.button(label="Fit to size", width=86, command=on_fit_distance)
    cmds.setParent("..")

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
    redraw_network_menu()
    show_network()
    redraw_preset_menu()
    if had_settings:
        set_status("Your settings from last time are back.")
    else:
        set_status("Pick a surface, then add objects to the network to start.")


if __name__ == "__main__":
    show()

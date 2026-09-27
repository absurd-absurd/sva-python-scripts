"""
circular_labyrinth_gui.py

Maya tool (maya.cmds UI, no PySide needed) that procedurally builds a
classical, UNICURSAL circular labyrinth: one single winding path with
no branches and no dead ends, spiraling from an outer entrance to a
center chamber -- built as real extruded 3D wall geometry.

HOW IT WORKS
------------
The labyrinth is made of N concentric circular walls at decreasing
radii. Each wall has exactly one gap (opening) in it. Gaps alternate
roughly opposite each other (offset by ~180 degrees, plus a small twist
per ring for a nicer spiral look), so getting from one gap to the next
means walking most of the way around that ring -- exactly like a real
garden/meditation labyrinth. Because every wall has only one opening,
there is only ever one possible route: in through the entrance gap,
around ring 1 to its gap, into ring 2, around to its gap, and so on
until you reach the open center chamber. No branches, no forks, no
dead ends -- just one long winding path.

HOW TO USE IN MAYA
-------------------
1. Open Maya's Script Editor (Windows > General Editors > Script Editor),
   on a Python tab.
2. Paste this whole file in and run it (Ctrl+Enter / Execute All), or:
       exec(open("/path/to/circular_labyrinth_gui.py").read())
3. A "Circular Labyrinth Generator" window opens. Set your options and
   hit "Generate". Hit "Delete Generated Labyrinth" to clear it.

You can also skip the UI and call generate_labyrinth(...) directly with
your own keyword args from another script.
"""

# math import (building points around circles) and random for colors
import math
import random
# Maya's Python command import line
import maya.cmds as cmds


# name of the group node the tool creates 
_DEFAULT_GROUP_NAME = "circularLabyrinth_grp"


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
def _arc_points(radius, angle_start_deg, angle_end_deg, segments):
    """Points sampled along a circular arc, in the XZ plane (Y is up)."""

    pts = []
    for s in range(segments + 1):
        t = float(s) / float(segments)
        ang = math.radians(angle_start_deg + t * (angle_end_deg - angle_start_deg))
        pts.append((radius * math.cos(ang), radius * math.sin(ang)))
    return pts


def _quad(p0, p1, p2, p3):
    # creates one flat 4-sided polygon face from 4 corner points -- the basic building block for every wall
    return cmds.polyCreateFacet(point=[p0, p1, p2, p3], constructionHistory=False)[0]


def _build_wall_arc(radius, angle_start_deg, angle_end_deg, thickness, height, segments, name):
    """Build one curved wall segment (a box swept along an arc) as a single mesh."""
    # creating two wall faces
    outer_r = radius + thickness / 2.0
    inner_r = radius - thickness / 2.0
    outer_pts = _arc_points(outer_r, angle_start_deg, angle_end_deg, segments)
    inner_pts = _arc_points(inner_r, angle_start_deg, angle_end_deg, segments)

    # building the outer face, inner face, and top cap
    faces = []
    for i in range(segments):
        ox0, oz0 = outer_pts[i]
        ox1, oz1 = outer_pts[i + 1]
        ix0, iz0 = inner_pts[i]
        ix1, iz1 = inner_pts[i + 1]

        # outer face
        faces.append(_quad((ox0, 0, oz0), (ox1, 0, oz1), (ox1, height, oz1), (ox0, height, oz0)))
        # inner face (reversed winding so its normal faces inward)
        faces.append(_quad((ix1, 0, iz1), (ix0, 0, iz0), (ix0, height, iz0), (ix1, height, iz1)))
        # top cap
        faces.append(_quad((ix0, height, iz0), (ix1, height, iz1), (ox1, height, oz1), (ox0, height, oz0)))

    # end caps so the two open ends of the arc (either side of the gap) are closed off, not hollow
    ox0, oz0 = outer_pts[0]
    ix0, iz0 = inner_pts[0]
    faces.append(_quad((ix0, 0, iz0), (ox0, 0, oz0), (ox0, height, oz0), (ix0, height, iz0)))

    ox1, oz1 = outer_pts[-1]
    ix1, iz1 = inner_pts[-1]
    faces.append(_quad((ox1, 0, oz1), (ix1, 0, iz1), (ix1, height, iz1), (ox1, height, oz1)))

    # stitch all the separate quad faces into one mesh, then weld their touching edges together
    merged = cmds.polyUnite(faces, constructionHistory=False, name=name)[0]
    cmds.polyMergeVertex(merged, distance=0.001, constructionHistory=False)
    return merged


def _make_color_shader(color, name):
    # a shader that holds the RGB color
    shader = cmds.shadingNode("lambert", asShader=True, name=name)
    cmds.setAttr(shader + ".color", color[0], color[1], color[2], type="double3")
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name + "SG")
    cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader", force=True)
    return sg


def _assign_color(transform, color, name):
    # make a fresh shader for this object and assign it, so each piece can have its own independent color
    sg = _make_color_shader(color, name)
    cmds.sets(transform, edit=True, forceElement=sg)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def generate_labyrinth(
    num_rings=8,
    outer_radius=15.0,
    ring_width=1.5,
    wall_thickness=0.25,
    wall_height=2.0,
    gap_width_deg=8.0,
    twist_deg=15.0,
    entrance_angle=0.0,
    circle_resolution=90,
    random_colors=True,
    wall_color=(0.6, 0.6, 0.65),
    add_floor=True,
    add_center_marker=True,
    group_name=_DEFAULT_GROUP_NAME,
    clear_existing=True,
    seed=None,
):
    """Build a unicursal circular labyrinth out of concentric, single-gapped walls.

    Returns the name of the top-level group node.
    """
    # a fixed seed makes the random colors reproducible between runs
    if seed is not None:
        random.seed(seed)

    # wipe out any previous labyrinth from this tool before building a new one, if asked to
    if clear_existing and cmds.objExists(group_name):
        cmds.delete(group_name)

    thickness = max(0.01, wall_thickness)
    all_nodes = []

    # sanity check: warn if the rings would be crammed so tight the center chamber nearly disappears
    innermost_radius = outer_radius - (num_rings - 1) * ring_width
    if innermost_radius < ring_width * 0.25:
        cmds.warning(
            "Rings are packed very tight for this outer radius/ring width -- "
            "consider fewer rings, a smaller ring width, or a larger outer radius."
        )

   
    for i in range(num_rings):
        radius = outer_radius - i * ring_width
     
        gap_angle = (entrance_angle + i * (180.0 + twist_deg)) % 360.0

       
        angle_start = gap_angle + gap_width_deg / 2.0
        angle_end = angle_start + (360.0 - gap_width_deg)

        
        arc_fraction = (360.0 - gap_width_deg) / 360.0
        segments = max(3, int(round(circle_resolution * arc_fraction)))

        wall_name = "labyrinthWall_{0:02d}".format(i)
        wall = _build_wall_arc(radius, angle_start, angle_end, thickness, wall_height, segments, wall_name)

        # give this ring either a random hue or the single fixed color, purely cosmetic
        if random_colors:
            hue = random.random()
            color = _hsv_to_rgb(hue, 0.6, 0.9)
        else:
            color = wall_color
        _assign_color(wall, color, wall_name + "_shd")

        all_nodes.append(wall)

    # optional flat disc under everything so the labyrinth reads as standing on ground, not floating
    if add_floor:
        floor_radius = outer_radius + ring_width * 0.5
        floor_name = "labyrinthFloor"
        floor_transform, _ = cmds.polyCylinder(
            radius=floor_radius, height=0.02, subdivisionsAxis=max(24, circle_resolution),
            name=floor_name
        )
        cmds.move(0, -0.01, 0, floor_transform, absolute=True)
        _assign_color(floor_transform, (0.35, 0.32, 0.28), floor_name + "_shd")
        all_nodes.append(floor_transform)

    # optional small marker (a cone) at the very center so the "goal" of the labyrinth is visible
    if add_center_marker:
        marker_name = "labyrinthCenterMarker"
        marker_radius = max(0.1, min(ring_width * 0.3, innermost_radius * 0.5))
        marker_transform, _ = cmds.polyCone(
            radius=marker_radius, height=wall_height * 0.75, subdivisionsAxis=16, name=marker_name
        )
        cmds.move(0, wall_height * 0.375, 0, marker_transform, absolute=True)
        _assign_color(marker_transform, (0.9, 0.75, 0.2), marker_name + "_shd")
        all_nodes.append(marker_transform)

    # bundle every wall/floor/marker under one group node so it's a single selectable/deletable object
    group = cmds.group(all_nodes, name=group_name)
    print("Built a {0}-ring circular labyrinth inside '{1}'.".format(num_rings, group))
    return group


def _hsv_to_rgb(h, s, v):
    # standard hue/saturation/value to red/green/blue conversion, used to spread random colors evenly around the color wheel
    if s <= 0.0:
        return (v, v, v)
    i = int(h * 6.0)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    return [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i]


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

_WINDOW_NAME = "circularLabyrinthWindow"

_ui = {}


def _build_ui():
    
    if cmds.window(_WINDOW_NAME, exists=True):
        cmds.deleteUI(_WINDOW_NAME)

    window = cmds.window(
        _WINDOW_NAME, title="Circular Labyrinth Generator", widthHeight=(360, 560), sizeable=False
    )
    # single vertical column that all the controls below stack into
    main = cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnAttach=("both", 12))

    cmds.text(label=" ")
    cmds.text(label="Circular Labyrinth Generator", font="boldLabelFont")
    cmds.text(label="One winding path, no branches -- classic spiral labyrinth.", font="smallPlainLabelFont")
    cmds.separator(height=10, style="in")

    # each of these sliders exposes one keyword argument of generate_labyrinth to the user
    _ui["num_rings"] = cmds.intSliderGrp(
        label="Number of rings", field=True, minValue=2, maxValue=30,
        fieldMinValue=2, fieldMaxValue=60, value=8, columnWidth3=(110, 50, 100),
    )
    _ui["outer_radius"] = cmds.floatSliderGrp(
        label="Outer radius", field=True, minValue=2.0, maxValue=60.0,
        fieldMinValue=0.5, fieldMaxValue=500.0, value=15.0, columnWidth3=(110, 50, 100),
    )
    _ui["ring_width"] = cmds.floatSliderGrp(
        label="Ring width (lane)", field=True, minValue=0.3, maxValue=6.0,
        fieldMinValue=0.05, fieldMaxValue=50.0, value=1.5, columnWidth3=(110, 50, 100),
    )
    _ui["wall_thickness"] = cmds.floatSliderGrp(
        label="Wall thickness", field=True, minValue=0.02, maxValue=1.5,
        fieldMinValue=0.01, fieldMaxValue=10.0, value=0.25, columnWidth3=(110, 50, 100),
    )
    _ui["wall_height"] = cmds.floatSliderGrp(
        label="Wall height", field=True, minValue=0.2, maxValue=10.0,
        fieldMinValue=0.05, fieldMaxValue=100.0, value=2.0, columnWidth3=(110, 50, 100),
    )
    _ui["gap_width"] = cmds.floatSliderGrp(
        label="Gap width (deg)", field=True, minValue=2.0, maxValue=45.0,
        fieldMinValue=1.0, fieldMaxValue=90.0, value=8.0, columnWidth3=(110, 50, 100),
    )
    _ui["twist"] = cmds.floatSliderGrp(
        label="Spiral twist (deg)", field=True, minValue=-90.0, maxValue=90.0,
        fieldMinValue=-360.0, fieldMaxValue=360.0, value=15.0, columnWidth3=(110, 50, 100),
    )
    _ui["entrance_angle"] = cmds.floatSliderGrp(
        label="Entrance angle (deg)", field=True, minValue=0.0, maxValue=360.0,
        fieldMinValue=0.0, fieldMaxValue=360.0, value=0.0, columnWidth3=(110, 50, 100),
    )
    _ui["resolution"] = cmds.intSliderGrp(
        label="Circle resolution", field=True, minValue=16, maxValue=240,
        fieldMinValue=8, fieldMaxValue=720, value=90, columnWidth3=(110, 50, 100),
    )

    cmds.separator(height=10, style="in")

    # simple on/off toggles for the optional extras
    _ui["random_colors"] = cmds.checkBox(label="Random color per ring", value=True)
    _ui["add_floor"] = cmds.checkBox(label="Add floor disc", value=True)
    _ui["add_center_marker"] = cmds.checkBox(label="Add center goal marker", value=True)

  
    seed_row = cmds.rowLayout(numberOfColumns=2, columnWidth2=(150, 150), adjustableColumn=2)
    _ui["use_seed"] = cmds.checkBox(label="Use fixed seed", value=False)
    _ui["seed_value"] = cmds.intField(value=42, enable=False)
    cmds.checkBox(
        _ui["use_seed"], edit=True,
        changeCommand=lambda val: cmds.intField(_ui["seed_value"], edit=True, enable=val),
    )
    cmds.setParent(main)

    _ui["clear_existing"] = cmds.checkBox(label="Delete previous labyrinth before generating", value=True)

    cmds.separator(height=10, style="in")

    # the three action buttons, each wired to one of the callback functions below
    cmds.button(label="Generate", height=36, backgroundColor=(0.35, 0.55, 0.35), command=_on_generate)
    cmds.button(label="Delete Generated Labyrinth", height=28, command=_on_delete)
    cmds.button(label="Close", height=24, command=lambda *_: cmds.deleteUI(_WINDOW_NAME))

    cmds.showWindow(window)


def _on_generate(*_args):
    use_seed = cmds.checkBox(_ui["use_seed"], query=True, value=True)
    seed = cmds.intField(_ui["seed_value"], query=True, value=True) if use_seed else None

    # pull the current value out of every control and forward it straight into generate_labyrinth()
    generate_labyrinth(
        num_rings=cmds.intSliderGrp(_ui["num_rings"], query=True, value=True),
        outer_radius=cmds.floatSliderGrp(_ui["outer_radius"], query=True, value=True),
        ring_width=cmds.floatSliderGrp(_ui["ring_width"], query=True, value=True),
        wall_thickness=cmds.floatSliderGrp(_ui["wall_thickness"], query=True, value=True),
        wall_height=cmds.floatSliderGrp(_ui["wall_height"], query=True, value=True),
        gap_width_deg=cmds.floatSliderGrp(_ui["gap_width"], query=True, value=True),
        twist_deg=cmds.floatSliderGrp(_ui["twist"], query=True, value=True),
        entrance_angle=cmds.floatSliderGrp(_ui["entrance_angle"], query=True, value=True),
        circle_resolution=cmds.intSliderGrp(_ui["resolution"], query=True, value=True),
        random_colors=cmds.checkBox(_ui["random_colors"], query=True, value=True),
        add_floor=cmds.checkBox(_ui["add_floor"], query=True, value=True),
        add_center_marker=cmds.checkBox(_ui["add_center_marker"], query=True, value=True),
        clear_existing=cmds.checkBox(_ui["clear_existing"], query=True, value=True),
        seed=seed,
    )


def _on_delete(*_args):
    
    if cmds.objExists(_DEFAULT_GROUP_NAME):
        cmds.delete(_DEFAULT_GROUP_NAME)
        print("Deleted '{0}'.".format(_DEFAULT_GROUP_NAME))
    else:
        cmds.warning("No generated labyrinth found ('{0}' does not exist).".format(_DEFAULT_GROUP_NAME))



if __name__ == "__main__":
    _build_ui()

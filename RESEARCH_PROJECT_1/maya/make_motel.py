"""Build the Marrow Falls Motel in Maya and export it for Unreal.

Run in Maya (Python tab):
    exec(open(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/maya/make_motel.py").read())

Look taken from the motel reference board: a single-story row of rooms with brick
below and plaster above, a curtained window beside every numbered door, a corrugated
awning with a red neon strip, a big red neon MOTEL on the roof with a dead,
flickering M, an office with an OPEN sign and the neon cross "SIN WILL FIND YOU OUT",
an ICE machine, plastic chairs, and a green streetlight.

Everything is built where it sits in the game, in Unreal coordinates (cm): Unreal (x, y, z)
is Maya (x, z, y), so the helpers below take Unreal numbers and do the swap.
Saves maya/motel_scene.ma and exports export/set_motel.fbx plus export/sets.json
(materials and the lights, which are locators here). unreal/import_sets.py places it.

Materials whose name starts with glow_ become neon (emissive) in Unreal.
"""
import json
import math
import os

import maya.cmds as cmds
import maya.mel as mel

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
SCENE = os.path.join(ROOT, "maya", "motel_scene.ma")
OUT = os.path.join(ROOT, "export")

# The layout the rest of the game expects (same as blockout.py)
X0, ROOM_W, ROOMS, HER_ROOM = -2500, 500, 6, 3        # rooms 101-106 run x -2500..500; 104 is hers
FRONT, BACK, H = -1400, -700, 320                     # front wall y, back wall y, wall height
WALK = 300                                            # covered walkway depth
OFFICE = (3050, 3750, -1750, -850, 340)               # x0, x1, y0 (front), y1, height
LOT_Z = 3                                             # parking lot surface height

MATS = {
    "brick_mat": (0.45, 0.25, 0.2), "plaster_mat": (0.75, 0.7, 0.6), "trim_mat": (0.25, 0.22, 0.2),
    "door_mat": (0.35, 0.15, 0.12), "brass_mat": (0.6, 0.5, 0.25), "glass_mat": (0.03, 0.04, 0.05),
    "curtain_mat": (0.55, 0.45, 0.3), "roof_metal_mat": (0.35, 0.33, 0.3), "concrete_mat": (0.5, 0.5, 0.48),
    "carpet_mat": (0.45, 0.2, 0.2), "bed_mat": (0.7, 0.68, 0.6), "wood_mat": (0.35, 0.22, 0.12),
    "chair_mat": (0.85, 0.85, 0.8), "metal_mat": (0.3, 0.3, 0.3), "ice_mat": (0.8, 0.82, 0.85),
    # glowing materials (emissive in Unreal; strength and flicker are set in textures.json)
    "glow_neon_red_mat": (1.0, 0.0, 0.0), "glow_neon_dead_mat": (1.0, 0.0, 0.0),
    "glow_window_mat": (1.0, 0.7, 0.4), "glow_ice_mat": (0.5, 0.8, 1.0),
    "glow_street_mat": (0.45, 1.0, 0.7), "glow_lamp_mat": (1.0, 0.75, 0.45),
}

# A tiny stroke font for neon: each letter is line segments on a 4 wide x 6 tall grid
FONT = {
    "M": [(0, 0, 0, 6), (0, 6, 2, 3), (2, 3, 4, 6), (4, 6, 4, 0)],
    "O": [(1, 0, 3, 0), (3, 0, 4, 1), (4, 1, 4, 5), (4, 5, 3, 6), (3, 6, 1, 6), (1, 6, 0, 5), (0, 5, 0, 1), (0, 1, 1, 0)],
    "T": [(0, 6, 4, 6), (2, 6, 2, 0)],
    "E": [(4, 6, 0, 6), (0, 6, 0, 0), (0, 0, 4, 0), (0, 3, 3, 3)],
    "L": [(0, 6, 0, 0), (0, 0, 4, 0)],
    "P": [(0, 0, 0, 6), (0, 6, 3, 6), (3, 6, 4, 5), (4, 5, 4, 4), (4, 4, 3, 3), (3, 3, 0, 3)],
    "N": [(0, 0, 0, 6), (0, 6, 4, 0), (4, 0, 4, 6)],
    "S": [(4, 6, 1, 6), (1, 6, 0, 5), (0, 5, 0, 4), (0, 4, 1, 3), (1, 3, 3, 3), (3, 3, 4, 2), (4, 2, 4, 1), (4, 1, 3, 0), (3, 0, 0, 0)],
    "I": [(2, 0, 2, 6), (1, 6, 3, 6), (1, 0, 3, 0)],
    "W": [(0, 6, 1, 0), (1, 0, 2, 3), (2, 3, 3, 0), (3, 0, 4, 6)],
    "F": [(0, 0, 0, 6), (0, 6, 4, 6), (0, 3, 3, 3)],
    "D": [(0, 0, 0, 6), (0, 6, 2, 6), (2, 6, 4, 4), (4, 4, 4, 2), (4, 2, 2, 0), (2, 0, 0, 0)],
    "Y": [(0, 6, 2, 3), (4, 6, 2, 3), (2, 3, 2, 0)],
    "U": [(0, 6, 0, 1), (0, 1, 1, 0), (1, 0, 3, 0), (3, 0, 4, 1), (4, 1, 4, 6)],
    "C": [(4, 6, 1, 6), (1, 6, 0, 5), (0, 5, 0, 1), (0, 1, 1, 0), (1, 0, 4, 0)],
    "A": [(0, 0, 0, 4), (0, 4, 2, 6), (2, 6, 4, 4), (4, 4, 4, 0), (0, 3, 4, 3)],
    "R": [(0, 0, 0, 6), (0, 6, 3, 6), (3, 6, 4, 5), (4, 5, 4, 4), (4, 4, 3, 3), (3, 3, 0, 3), (2, 3, 4, 0)],
}

PARTS = []      # every mesh made, combined at the end


# ---------- helpers (all positions in Unreal coordinates) ----------

def material(name, rgb):
    if not cmds.objExists(name):
        cmds.shadingNode("lambert", asShader=True, name=name)
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name + "SG")
        cmds.connectAttr(name + ".outColor", sg + ".surfaceShader")
    cmds.setAttr(name + ".color", *rgb, type="double3")
    return name


def keep(obj, mat):
    cmds.sets(obj, edit=True, forceElement=mat + "SG")
    PARTS.append(obj)
    return obj


def box(x0, x1, y0, y1, z0, z1, mat):
    """An axis-aligned box from Unreal bounds."""
    b = cmds.polyCube(w=abs(x1 - x0), h=abs(z1 - z0), d=abs(y1 - y0), ch=False)[0]
    cmds.move((x0 + x1) / 2.0, (z0 + z1) / 2.0, (y0 + y1) / 2.0, b)
    return keep(b, mat)


def tube(p0, p1, r, mat, sides=6):
    """A cylinder between two Unreal points (a neon tube, a pipe, a leg)."""
    a = (p0[0], p0[2], p0[1])
    b = (p1[0], p1[2], p1[1])
    d = [b[i] - a[i] for i in range(3)]
    length = math.sqrt(sum(v * v for v in d)) or 0.01
    c = cmds.polyCylinder(r=r, h=length, sx=sides, sy=1, sz=0, ch=False)[0]
    cmds.move(0, length / 2.0, 0, c)
    cmds.makeIdentity(c, apply=True, t=True)
    cmds.xform(c, pivots=(0, 0, 0), worldSpace=True)
    yaw = math.degrees(math.atan2(d[0], d[2]))
    pitch = math.degrees(math.acos(max(-1, min(1, d[1] / length))))
    cmds.xform(c, rotation=(pitch, yaw, 0))
    cmds.move(*a, c)
    return keep(c, mat)


def neon_word(text, left, y, z, height, mat, r=None, mats=None, vertical=False):
    """Neon letters read from the road (looking toward +y), bottom at z.
    Seen from the road, Unreal's +x runs to the LEFT, so 'left' is the largest x and
    the text runs toward -x (tested: laid out toward +x it read mirrored, LETOM).
    mats can give one letter its own material (the dead M). vertical stacks letters top-down."""
    u = height / 6.0
    r = r or u * 0.18
    for i, ch in enumerate(text):
        if ch == " ":
            continue
        if vertical:
            ox, oz = left, z - i * u * 8
        else:
            ox, oz = left - i * u * 5.5, z
        m = (mats or {}).get(i, mat)
        pts = [(ox - ax * u, oz + ay * u, ox - bx * u, oz + by * u) for (ax, ay, bx, by) in FONT[ch]]
        for (ax, az, bx, bz) in pts:
            tube((ax, y, az), (bx, y, bz), r, m)
        for (ax, az, bx, bz) in pts:        # little balls hide the gaps where tubes meet
            s = cmds.polySphere(r=r * 1.05, sx=6, sy=4, ch=False)[0]
            cmds.move(ax, az, y, s)
            keep(s, m)
    return (len(text) * 5.5 - 1.5) * u        # width


def block_word(text, left, y, z, height, mat, thick, depth=14):
    """Thick, solid letters (like lit box letters on a sign), read from the road like neon_word."""
    u = height / 6.0
    for i, ch in enumerate(text):
        if ch == " ":
            continue
        ox = left - i * u * 5.5
        for (ax, ay, bx, by) in FONT[ch]:
            x0, z0, x1, z1 = ox - ax * u, z + ay * u, ox - bx * u, z + by * u
            length = math.hypot(x1 - x0, z1 - z0)
            b = cmds.polyCube(w=length + thick, h=thick, d=depth, ch=False)[0]
            cmds.rotate(0, 0, math.degrees(math.atan2(z1 - z0, x1 - x0)), b)   # Maya x-y plane = Unreal x-z
            cmds.move((x0 + x1) / 2.0, (z0 + z1) / 2.0, y, b)
            keep(b, mat)


def light(name, x, y, z, color, intensity, radius, flicker=False):
    """A locator that becomes a point light in Unreal (flicker: dims in step with the dead neon)."""
    loc = cmds.spaceLocator(name=name)[0]
    cmds.move(x, z, y, loc)
    cmds.addAttr(loc, longName="ue_light", dataType="string")
    cmds.setAttr(loc + ".ue_light", json.dumps({"color": color, "intensity": intensity, "radius": radius, "flicker": flicker}), type="string")
    return loc


# ---------- the building ----------

def room_row():
    """Six rooms, 101-106, all hollow with a doorway you can walk through. The doors
    themselves are BP_Examinable actors in Unreal (clues.json), so they swing open on E."""
    for i in range(ROOMS):
        x0 = X0 + i * ROOM_W
        x1 = x0 + ROOM_W
        number = 101 + i
        room_inside(x0, x1)
        # brick lower wall, sticking out 3 cm
        door_x0, door_x1 = x0 + 140, x0 + 280                       # doorway, 140 wide x 230 tall
        for a, b in ((x0, door_x0 - 8), (door_x1 + 8, x1)):
            box(a, b, FRONT - 3, FRONT, 0, 100, "brick_mat")
        # window: frame, dark glass, curtains (some lit)
        wx0, wx1 = x0 + 320, x0 + 470
        box(wx0 - 8, wx1 + 8, FRONT - 6, FRONT, 100, 222, "trim_mat")
        box(wx0, wx1, FRONT - 7, FRONT - 2, 108, 214, "glass_mat")
        curtain = "glow_window_mat" if i in (1, 5) else "curtain_mat"
        box(wx0 + 4, wx0 + 70, FRONT - 9, FRONT - 7, 110, 212, curtain)
        box(wx1 - 70, wx1 - 4, FRONT - 9, FRONT - 7, 110, 212, curtain)
        box(wx0 - 12, wx1 + 12, FRONT - 14, FRONT, 96, 104, "trim_mat")     # sill
        # door frame: two jambs and a header, so the doorway stays open
        box(door_x0 - 8, door_x0, FRONT - 5, FRONT, 0, 238, "trim_mat")
        box(door_x1, door_x1 + 8, FRONT - 5, FRONT, 0, 238, "trim_mat")
        box(door_x0 - 8, door_x1 + 8, FRONT - 5, FRONT, 230, 238, "trim_mat")
        # room number: brass digits on a dark plate above the door
        plate_x = (door_x0 + door_x1) / 2.0
        box(plate_x - 32, plate_x + 32, FRONT - 8, FRONT - 5, 244, 270, "trim_mat")
        sign_word(str(number), plate_x, FRONT - 8, 250, 14, 1.5, "brass_mat", 2.5)
        # plastic chair by some doors
        if i in (0, 2, 4):
            chair(x0 + 60, FRONT - 120)


def room_inside(x0, x1):
    """One motel room: walls, ceiling, carpet, bed, nightstand + lamp, dresser + TV.
    Every room has the same layout; Room 104 (Cas's) gets its clues from clues.json."""
    t = 20
    mid = (FRONT + BACK) / 2.0
    box(x0, x1, BACK - t, BACK, 0, H, "plaster_mat")                         # back
    box(x0, x0 + t, FRONT, BACK, 0, H, "plaster_mat")                        # left
    box(x1 - t, x1, FRONT, BACK, 0, H, "plaster_mat")                        # right
    box(x0, x0 + 140, FRONT, FRONT + t, 0, H, "plaster_mat")                 # front, left of door
    box(x0 + 280, x1, FRONT, FRONT + t, 0, H, "plaster_mat")                 # front, right of door
    box(x0 + 140, x0 + 280, FRONT, FRONT + t, 230, H, "plaster_mat")         # above door
    box(x0, x1, FRONT, BACK, H - 10, H, "plaster_mat")                       # ceiling
    box(x0 + t, x1 - t, FRONT + t, BACK - t, 0, 2, "carpet_mat")             # carpet
    # bed: frame, mattress, pillow, headboard
    bx0, bx1 = x0 + 220, x1 - 40
    box(bx0, bx1, BACK - 250, BACK - 20, 0, 35, "wood_mat")
    box(bx0 + 5, bx1 - 5, BACK - 245, BACK - 25, 35, 58, "bed_mat")
    box(bx0 + 30, bx1 - 30, BACK - 70, BACK - 30, 58, 70, "bed_mat")
    box(bx0, bx1, BACK - 28, BACK - 20, 0, 110, "wood_mat")
    # nightstand with a lamp
    box(x0 + 150, x0 + 210, BACK - 70, BACK - 25, 0, 60, "wood_mat")
    tube((x0 + 180, BACK - 47, 60), (x0 + 180, BACK - 47, 95), 3, "brass_mat")
    tube((x0 + 180, BACK - 47, 95), (x0 + 180, BACK - 47, 120), 16, "glow_lamp_mat", sides=8)
    # dresser with an old TV across from the bed
    box(x0 + 30, x0 + 200, FRONT + 25, FRONT + 80, 0, 80, "wood_mat")
    box(x0 + 60, x0 + 160, FRONT + 30, FRONT + 75, 80, 150, "metal_mat")
    box(x0 + 70, x0 + 150, FRONT + 76, FRONT + 78, 90, 140, "glass_mat")


def chair(x, y):
    """A white plastic patio chair facing the lot."""
    box(x - 25, x + 25, y - 22, y + 22, 42, 47, "chair_mat")
    box(x - 25, x + 25, y + 18, y + 24, 47, 90, "chair_mat")
    for dx in (-21, 21):
        for dy in (-18, 18):
            tube((x + dx, y + dy, 0), (x + dx, y + dy, 43), 2.5, "chair_mat", sides=4)


def awning():
    """Corrugated metal awning over the walkway, posts, and the red neon strip."""
    xa, xb = X0 - 40, X0 + ROOMS * ROOM_W + 40
    y_front = FRONT - WALK
    box(xa, xb, y_front, BACK + 40, H, H + 12, "roof_metal_mat")                 # roof deck
    for k in range(int((xb - xa) / 30)):                                         # corrugation ribs
        x = xa + 15 + k * 30
        box(x - 5, x + 5, y_front, BACK + 40, H + 12, H + 17, "roof_metal_mat")
    box(xa, xb, y_front - 8, y_front, H - 30, H + 17, "trim_mat")                 # fascia
    tube((xa, y_front - 10, H - 26), (xb, y_front - 10, H - 26), 2.5, "glow_neon_red_mat")   # neon strip
    for i in range(ROOMS + 1):                                                   # posts
        x = X0 + i * ROOM_W
        box(x - 8, x + 8, y_front + 10, y_front + 26, 0, H, "trim_mat")
    box(xa, xb, y_front, FRONT, 0, 12, "concrete_mat")                           # walkway slab


# ---------- the rooftop sign: real font letters ----------

SIGN_FONT = "Century Gothic|wt:75"     # round, clean sans-serif like the reference photo
_font_scale = {}


def _curves_of(group):
    shapes = cmds.listRelatives(group, allDescendents=True, type="nurbsCurve", fullPath=True) or []
    return [cmds.listRelatives(sh, parent=True, fullPath=True)[0] for sh in shapes]


def _font_curves(ch, cap):
    """Outline curves of one character, scaled so a capital letter is `cap` cm tall, baseline at 0."""
    if cap not in _font_scale:
        t = cmds.textCurves(font=SIGN_FONT, text="T", ch=False)[0]
        bb = cmds.exactWorldBoundingBox(t)
        _font_scale[cap] = cap / (bb[4] - bb[1])
        cmds.delete(t)
    g = cmds.textCurves(font=SIGN_FONT, text=ch, ch=False)[0]
    cmds.scale(_font_scale[cap], _font_scale[cap], _font_scale[cap], g, pivot=(0, 0, 0))
    cmds.makeIdentity(g, apply=True, t=True, r=True, s=True)
    return g, _curves_of(g)


def _outline_points(curve):
    """Points around one outline: exact corners for straight (degree 1) curves,
    dense samples for round ones, so an O is round and an E keeps sharp corners."""
    if cmds.getAttr(curve + ".degree") == 1:
        pts = cmds.xform(curve + ".cv[*]", q=True, translation=True, worldSpace=True)
        pts = [(pts[i], pts[i + 1]) for i in range(0, len(pts), 3)]
    else:
        a, b = cmds.getAttr(curve + ".minValue"), cmds.getAttr(curve + ".maxValue")
        n = cmds.getAttr(curve + ".spans") * 10
        pts = [tuple(cmds.pointOnCurve(curve, pr=a + (b - a) * k / n, p=True)[:2]) for k in range(n)]
    if len(pts) > 2 and math.dist(pts[0], pts[-1]) < 0.01:
        pts = pts[:-1]
    return pts


def _area(pts):
    return 0.5 * sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))


def solid_letter(ch, cap, depth, mat):
    """A solid letter with real depth (like a lit box letter), facing +z in its own space,
    left edge at x=0. Returns (mesh, width)."""
    g, curves = _font_curves(ch, cap)
    loops = sorted((_outline_points(c) for c in curves), key=lambda p: -abs(_area(p)))
    x_min = min(x for loop in loops for x, _ in loop)
    x_max = max(x for loop in loops for x, _ in loop)
    pts = []
    for k, loop in enumerate(loops):           # first loop is the outside, the rest are holes
        if k:
            pts.append(())
        pts += [(x - x_min, y, 0) for x, y in loop]
    face = cmds.polyCreateFacet(p=pts, ch=False)[0]
    n = cmds.polyInfo(face + ".f[0]", faceNormals=True)[0].split()
    if float(n[-1]) < 0:
        cmds.polyNormal(face, normalMode=0, ch=False)
    cmds.polyExtrudeFacet(face + ".f[0]", localTranslateZ=depth)
    cmds.delete(face, constructionHistory=True)
    cmds.delete(g)
    return face, x_max - x_min


def tube_letter(ch, cap, r, inset):
    """A letter drawn as neon tube along its outline, twice: the outline and a second line
    `inset` cm inside it (the double-line dead M in the reference). Facing +z, left edge at 0."""
    g, curves = _font_curves(ch, cap)
    bb = cmds.exactWorldBoundingBox(g)
    parts = []
    for c in curves:
        offs = cmds.offsetCurve(c, distance=inset, normal=(0, 0, 1), ch=False) + \
            cmds.offsetCurve(c, distance=-inset, normal=(0, 0, 1), ch=False)
        # keep the offset that lies inside the letter (the one with the smaller box)
        def box_area(o):
            b = cmds.exactWorldBoundingBox(o)
            return (b[3] - b[0]) * (b[4] - b[1])
        offs.sort(key=box_area)
        cmds.delete(offs[1:])
        for path in (c, offs[0]):
            prof = cmds.circle(r=r, nr=(0, 0, 1), sections=8, ch=False)[0]
            srf = cmds.extrude(prof, path, extrudeType=2, fixedPath=True, useComponentPivot=1, polygon=0, ch=False)[0]
            mesh = cmds.nurbsToPoly(srf, f=2, pt=1, ut=1, un=1, vt=1, vn=1, ch=False)[0]
            cmds.delete(prof, srf)
            parts.append(mesh)
    m = cmds.polyUnite(parts, ch=False)[0]
    cmds.move(-bb[0], 0, r, m, relative=True)
    cmds.makeIdentity(m, apply=True, t=True)
    cmds.xform(m, pivots=(0, 0, 0), worldSpace=True)
    cmds.delete(g)
    return m, bb[3] - bb[0]


def place_letter(mesh, left, y_wall, z_base, mat):
    """Turn a letter (built facing +z) to face the road and put its left edge, as seen
    from the road, at Unreal x = left (seen from the road, +x is to the left)."""
    cmds.rotate(0, 180, 0, mesh, pivot=(0, 0, 0))
    cmds.move(left, z_base, y_wall, mesh, relative=True)
    return keep(mesh, mat)


def sign_word(text, center_x, y_wall, z_base, cap, depth, mat, tracking, special=None):
    """Lay out a word centred on center_x. special maps a letter index to a function that
    builds that letter differently (the neon-tube M). Returns the centre x of each letter."""
    built = []
    for i, ch in enumerate(text):
        if ch == " ":
            built.append((None, cap * 0.45))
            continue
        built.append(special[i](ch) if special and i in special else solid_letter(ch, cap, depth, mat))
    total = sum(w for _, w in built) + tracking * (len(built) - 1)
    left = center_x + total / 2.0
    centers = []
    for k, (mesh, w) in enumerate(built):
        if mesh:
            place_letter(mesh, left, y_wall, z_base, "glow_neon_dead_mat" if special and k in special else mat)
            centers.append(left - w / 2.0)
        left -= w + tracking
    return centers


def rooftop_sign():
    """Big solid MOTEL letters in a round sans-serif standing on a thin steel frame on the
    roof (the user preferred this to a sign wall), the M a dead double neon tube that
    flickers. The town name (from story.json) sits smaller on top. The red light comes
    FROM the letters: one light at each letter (the M's light flickers with it)."""
    story = json.load(open(os.path.join(ROOT, "story.json")))
    top_line = story["places"]["motel"].upper().rsplit(" ", 1)[0]      # MARROW FALLS
    y_wall = FRONT - 10                      # letters' back face, just above the front wall
    cx = X0 + ROOMS * ROOM_W / 2.0
    big, small = 165, 62
    z_big, z_small = H + 75, H + 300
    centers = sign_word("MOTEL", cx, y_wall, z_big, big, 22, "glow_neon_red_mat", tracking=big * 0.42,
                        special={0: lambda ch: tube_letter(ch, big * 1.05, 2.6, inset=big * 0.07)})
    sign_word(top_line, cx, y_wall, z_small, small, 12, "glow_neon_red_mat", tracking=small * 0.28)
    # thin steel frame behind the letters, standing on the roof
    half = (centers[0] - centers[-1]) / 2.0 + big * 0.7
    for px in (cx - half + 40, cx - half / 3.0, cx + half / 3.0, cx + half - 40):
        tube((px, y_wall + 25, H + 12), (px, y_wall + 25, z_small + small + 15), 5, "metal_mat")
    for bz in (z_big + 25, z_big + big - 20, z_small + 10, z_small + small - 5):
        tube((cx - half, y_wall + 25, bz), (cx + half, y_wall + 25, bz), 4, "metal_mat")
    # a light just in front of and below each letter: the spill on the wall, awning and lot
    # comes from the letters (closer than ~1 m it burns a hot spot into the wall)
    for k, x in enumerate(centers):
        light(f"light_sign_{'MOTEL'[k]}", x, y_wall - 150, z_big + big * 0.2, [1.0, 0.0, 0.0],
              1400, 2600, flicker=(k == 0))


def office():
    x0, x1, y0, y1, h = OFFICE
    t = 20
    d0, d1, dh = x0 + 50, x0 + 160, 230                  # doorway (the door itself is BP_Examinable)
    # hollow shell you can walk into
    box(x0, x1, y1 - t, y1, 0, h, "plaster_mat")                               # back
    box(x0, x0 + t, y0, y1, 0, h, "plaster_mat")                               # left
    box(x1 - t, x1, y0, y1, 0, h, "plaster_mat")                               # right
    box(x0, d0, y0, y0 + t, 0, h, "plaster_mat")                               # front, left of door
    box(d1, x1, y0, y0 + t, 0, h, "plaster_mat")                               # front, right of door
    box(d0, d1, y0, y0 + t, dh, h, "plaster_mat")                              # above door
    box(x0, x1, y0, y1, h - 10, h, "plaster_mat")                              # ceiling
    box(x0 + t, x1 - t, y0 + t, y1 - t, 0, 2, "carpet_mat")                    # carpet
    for a, b in ((x0, d0 - 10), (d1 + 10, x1)):
        box(a, b, y0 - 3, y0, 0, 100, "brick_mat")
    box(x0 - 30, x1 + 30, y0 - 150, y1 + 30, h, h + 15, "roof_metal_mat")         # flat roof with overhang
    box(x0 - 30, x1 + 30, y0 - 158, y0 - 150, h - 25, h + 15, "trim_mat")
    tube((x0 - 30, y0 - 160, h - 21), (x1 + 30, y0 - 160, h - 21), 2.5, "glow_neon_red_mat")
    # door frame (jambs + header, so the doorway stays open)
    box(d0 - 10, d0, y0 - 5, y0, 0, dh + 8, "trim_mat")
    box(d1, d1 + 10, y0 - 5, y0, 0, dh + 8, "trim_mat")
    box(d0 - 10, d1 + 10, y0 - 5, y0, dh, dh + 8, "trim_mat")
    # inside: front counter facing the door, a key board on the back wall, a desk lamp
    box(x0 + 220, x1 - 80, y0 + 380, y0 + 440, 0, 105, "wood_mat")
    box(x0 + 215, x1 - 75, y0 + 375, y0 + 445, 105, 109, "trim_mat")
    box(x0 + 300, x0 + 420, y1 - t - 3, y1 - t, 140, 210, "wood_mat")
    for k in range(6):                                                          # empty hooks
        box(x0 + 312 + k * 19, x0 + 316 + k * 19, y1 - t - 7, y1 - t - 3, 190, 194, "brass_mat")
    tube((x1 - 130, y0 + 410, 109), (x1 - 130, y0 + 410, 140), 2, "brass_mat")
    tube((x1 - 130, y0 + 410, 140), (x1 - 130, y0 + 410, 158), 12, "glow_lamp_mat", sides=8)
    light("light_office", x1 - 130, y0 + 380, 200, [1.0, 0.75, 0.45], 300, 700)
    # big front window with a neon OPEN sign
    wx0, wx1 = x0 + 430, x1 - 30
    box(wx0 - 8, wx1 + 8, y0 - 6, y0, 95, 250, "trim_mat")
    box(wx0, wx1, y0 - 7, y0 - 2, 103, 242, "glass_mat")
    neon_word("OPEN", wx1 - 30, y0 - 12, 150, 40, "glow_neon_red_mat", r=3.5)
    light("light_open", (wx0 + wx1) / 2.0, y0 - 25, 170, [1.0, 0.0, 0.0], 600, 600)
    # the neon cross: SIN above the bar, WILL / FIND on the bar, YOU OUT below. It stands in
    # front of the office on a post, rising above the roof, bottom high enough to walk under.
    cross(x0 + 300, y0 - 190, 38)
    # ICE machine at the end of the room row
    ice_machine(X0 + ROOMS * ROOM_W + 120, FRONT - 70)


def cross(cx, y, letter_h):
    u = letter_h / 6.0
    step = u * 8                     # one stacked letter
    col_w = u * 4
    top = 780                        # top of the cross, well above the office roof
    bar_z = top - 3 * step - u * 2   # crossbar letters' bottom
    # backing board (dark metal), vertical and horizontal
    v_bottom = bar_z - 6 * step - u * 4
    box(cx - col_w, cx + col_w, y + 4, y + 10, v_bottom, top + u * 2, "metal_mat")
    tube((cx, y + 20, 0), (cx, y + 20, v_bottom + 20), 8, "metal_mat")          # the post it stands on
    bar_half = col_w + 4 * 5.5 * u + u * 2
    box(cx - bar_half, cx + bar_half, y + 4, y + 10, bar_z - u * 2, bar_z + u * 8, "metal_mat")
    # red outline tubes around both boards
    for (ax, az, bx, bz) in ((cx - col_w, v_bottom, cx - col_w, bar_z - u * 2), (cx + col_w, v_bottom, cx + col_w, bar_z - u * 2),
                             (cx - col_w, v_bottom, cx + col_w, v_bottom),
                             (cx - col_w, bar_z + u * 8, cx - col_w, top + u * 2), (cx + col_w, bar_z + u * 8, cx + col_w, top + u * 2),
                             (cx - col_w, top + u * 2, cx + col_w, top + u * 2),
                             (cx - bar_half, bar_z - u * 2, cx - col_w, bar_z - u * 2), (cx + col_w, bar_z - u * 2, cx + bar_half, bar_z - u * 2),
                             (cx - bar_half, bar_z + u * 8, cx - col_w, bar_z + u * 8), (cx + col_w, bar_z + u * 8, cx + bar_half, bar_z + u * 8),
                             (cx - bar_half, bar_z - u * 2, cx - bar_half, bar_z + u * 8), (cx + bar_half, bar_z - u * 2, cx + bar_half, bar_z + u * 8)):
        tube((ax, y, az), (bx, y, bz), 4, "glow_neon_red_mat")
    word_w = (4 * 5.5 - 1.5) * u
    neon_word("SIN", cx + u * 2, y, top - u * 6, letter_h, "glow_neon_red_mat", r=3.5, vertical=True)
    neon_word("YOUOUT", cx + u * 2, y, bar_z - step, letter_h, "glow_neon_red_mat", r=3.5, vertical=True)
    neon_word("WILL", cx + col_w + u + word_w, y, bar_z, letter_h, "glow_neon_red_mat", r=3.5)   # left of the column, seen from the road
    neon_word("FIND", cx - col_w - u, y, bar_z, letter_h, "glow_neon_red_mat", r=3.5)
    light("light_cross", cx, y - 30, bar_z, [1.0, 0.0, 0.0], 2500, 1100)
    print(f"cross bottom at {v_bottom:.0f} cm, top at {top:.0f} cm")


def ice_machine(x, y):
    box(x - 50, x + 50, y - 40, y + 40, 0, 170, "ice_mat")
    box(x - 40, x + 40, y - 42, y - 40, 120, 160, "glow_ice_mat")       # lit panel
    neon_word("ICE", x + 33, y - 46, 128, 24, "glass_mat", r=1.5)          # dark letters on the panel
    light("light_ice", x, y - 120, 140, [0.5, 0.8, 1.0], 200, 400)


def streetlight(x, y):
    """Tall pole with a sickly green-teal lamp over the parking lot."""
    tube((x, y, 0), (x, y, 650), 9, "metal_mat")
    tube((x, y, 640), (x + 120, y, 650), 5, "metal_mat")
    box(x + 100, x + 160, y - 20, y + 20, 630, 648, "metal_mat")
    box(x + 105, x + 155, y - 15, y + 15, 626, 630, "glow_street_mat")
    light("light_street", x + 130, y, 600, [0.45, 1.0, 0.7], 4000, 1800)


# ---------- build and export ----------

def build():
    del PARTS[:]
    cmds.file(new=True, force=True)
    for name, rgb in MATS.items():
        material(name, rgb)
    room_row()
    awning()
    rooftop_sign()
    office()
    streetlight(1500, -3500)
    motel = cmds.polyUnite(PARTS, name="set_motel", constructionHistory=False)[0]
    cmds.delete(motel, constructionHistory=True)
    cmds.xform(motel, pivots=(0, 0, 0), worldSpace=True)
    lights = cmds.ls("light_*", type="transform")
    cmds.group(lights, name="motel_lights")
    cmds.setAttr("perspShape.farClipPlane", 200000)
    cmds.file(rename=SCENE)
    cmds.file(save=True, type="mayaAscii")
    tris = cmds.polyEvaluate(motel, triangle=True)
    export(motel, lights)
    print(f"Motel built: {tris} triangles, {len(lights)} lights -> {SCENE}")


def export(motel, lights):
    if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
        cmds.loadPlugin("fbxmaya")
    os.makedirs(OUT, exist_ok=True)
    fbx = os.path.join(OUT, "set_motel.fbx").replace("\\", "/")
    cmds.select(motel)
    mel.eval("FBXResetExport")
    mel.eval('FBXExport -f "{}" -s'.format(fbx))
    used = set()
    for sg in cmds.listConnections(cmds.listRelatives(motel, shapes=True), type="shadingEngine") or []:
        used.update(cmds.listConnections(sg + ".surfaceShader") or [])
    data = {
        "sets": {"set_motel": fbx},
        "materials": {m: list(cmds.getAttr(m + ".color")[0]) for m in sorted(used)},
        "lights": [dict(json.loads(cmds.getAttr(l + ".ue_light")), name=l,
                        position=[cmds.xform(l, q=True, t=True, ws=True)[i] for i in (0, 2, 1)]) for l in lights],
    }
    with open(os.path.join(OUT, "sets.json"), "w") as f:
        json.dump(data, f, indent=1)


build()

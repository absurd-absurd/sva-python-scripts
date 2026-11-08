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
import random
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
# Flat things lying on the lot/road each get their own height (tops 8 mm apart). Closer than
# that, two overlapping surfaces "z-fight": the GPU can't tell which is in front and they
# flash in and out as you move.
DECAL_H = {"stain": 0.8, "patch": 1.6, "crack": 2.4, "paint": 3.2}

MATS = {
    "brick_mat": (0.45, 0.25, 0.2), "plaster_mat": (0.75, 0.7, 0.6), "trim_mat": (0.25, 0.22, 0.2),
    "door_mat": (0.35, 0.15, 0.12), "brass_mat": (0.6, 0.5, 0.25), "glass_mat": (0.03, 0.04, 0.05),
    "curtain_mat": (0.55, 0.45, 0.3), "roof_metal_mat": (0.35, 0.33, 0.3), "concrete_mat": (0.5, 0.5, 0.48),
    "carpet_mat": (0.3, 0.28, 0.2), "bed_mat": (0.5, 0.46, 0.38), "wood_mat": (0.35, 0.22, 0.12),   # bed: old, yellowed
    # Room 104 (Cas's room)
    "sheet_mat": (0.42, 0.38, 0.3), "bedspread_mat": (0.33, 0.2, 0.14), "pillow_mat": (0.46, 0.42, 0.34), "stain_sheet_mat": (0.16, 0.12, 0.07),
    "shoe_mat": (0.07, 0.075, 0.11), "diary_mat": (0.18, 0.08, 0.06), "page_mat": (0.6, 0.56, 0.45),
    "mug_mat": (0.55, 0.52, 0.46), "coffee_mat": (0.04, 0.02, 0.01), "pot_mat": (0.35, 0.17, 0.1),
    "soil_mat": (0.05, 0.04, 0.03), "twig_mat": (0.16, 0.11, 0.07), "leaf_dead_mat": (0.25, 0.17, 0.07),
    "jacket_mat": (0.12, 0.16, 0.12), "suitcase_mat": (0.2, 0.06, 0.05), "strap_mat": (0.1, 0.08, 0.06),
    "clothes_a_mat": (0.4, 0.38, 0.35), "clothes_b_mat": (0.12, 0.14, 0.22), "clothes_c_mat": (0.35, 0.3, 0.2),
    "photo_border_mat": (0.62, 0.6, 0.55), "tape_mat": (0.6, 0.57, 0.45),
    # her photos (pictures drawn by tools/make_photos.py; the color here only tints them)
    "pic_lake_dusk": (1, 1, 1), "pic_lake_fog": (1, 1, 1), "pic_dock": (1, 1, 1), "pic_lake_night": (1, 1, 1),
    "pic_lanterns": (1, 1, 1),
    "camera_mat": (0.04, 0.04, 0.04), "string_mat": (0.4, 0.33, 0.22), "wallpaper_mat": (0.7, 0.64, 0.5),
    "stain_wall_mat": (0.38, 0.3, 0.18), "stain_dark_mat": (0.22, 0.16, 0.09), "cobweb_mat": (0.62, 0.61, 0.58),
    "glow_lamp_red_mat": (1.0, 0.05, 0.02),
    "room_wall_mat": (1, 1, 1), "seeglass_window_mat": (0.12, 0.14, 0.15), "frame_mat": (0.3, 0.22, 0.1),
    "pic_painting": (1, 1, 1),
    "fan_mat": (0.32, 0.26, 0.17), "bowl_mat": (0.62, 0.6, 0.55),
    "ac_mat": (0.55, 0.53, 0.48), "doormat_mat": (0.14, 0.11, 0.08), "post_mat": (0.18, 0.17, 0.16),
    "lid_mat": (0.06, 0.07, 0.06), "chrome_mat": (0.5, 0.5, 0.52), "plate_mat": (0.75, 0.72, 0.6),
    "weed_mat": (0.16, 0.2, 0.09),
    "gloss_car_paint_mat": (0.22, 0.035, 0.03), "gloss_chrome_mat": (0.55, 0.55, 0.57),
    "seeglass_car_mat": (0.05, 0.06, 0.07), "seat_mat": (0.16, 0.12, 0.09), "dash_mat": (0.05, 0.05, 0.05),
    "pic_lot_asphalt": (1, 1, 1), "pic_road_asphalt": (1, 1, 1), "pic_car_plate": (1, 1, 1),
    "tv_mat": (0.09, 0.075, 0.06), "screen_mat": (0.035, 0.045, 0.045), "sole_mat": (0.62, 0.6, 0.55),
    "lining_mat": (0.3, 0.1, 0.09), "pin_mat": (0.6, 0.03, 0.02), "red_string_mat": (0.45, 0.03, 0.03),
    "shoe_inner_mat": (0.05, 0.05, 0.05), "jacket_cuff_mat": (0.08, 0.1, 0.08),
    "pic_note_names": (1, 1, 1), "pic_note_night": (1, 1, 1), "pic_note_lights": (1, 1, 1), "pic_note_rattle": (1, 1, 1),
    "pic_note_scrawl": (1, 1, 1), "pic_clipping": (1, 1, 1), "pic_lake_map": (1, 1, 1),
    "pic_page_1": (1, 1, 1), "pic_page_2": (1, 1, 1), "pic_page_3": (1, 1, 1), "pen_mat": (0.05, 0.07, 0.2),
    "chair_mat": (0.85, 0.85, 0.8), "metal_mat": (0.3, 0.3, 0.3), "ice_mat": (0.8, 0.82, 0.85),
    # the lot and the car
    "paint_mat": (0.55, 0.54, 0.48), "paint_yellow_mat": (0.55, 0.45, 0.12), "crack_mat": (0.015, 0.015, 0.015),
    "patch_mat": (0.05, 0.05, 0.05), "stain_mat": (0.008, 0.008, 0.01), "car_paint_mat": (0.22, 0.035, 0.03),
    "tire_mat": (0.025, 0.025, 0.025), "payphone_mat": (0.11, 0.13, 0.15), "dumpster_mat": (0.08, 0.16, 0.1),
    "bag_mat": (0.02, 0.02, 0.022), "stop_mat": (0.18, 0.17, 0.15),
    # glowing materials (emissive in Unreal; strength and flicker are set in textures.json)
    "glow_neon_red_mat": (1.0, 0.0, 0.0), "glow_neon_dead_mat": (1.0, 0.0, 0.0),
    "glow_window_mat": (1.0, 0.7, 0.4), "glow_ice_mat": (0.5, 0.8, 1.0),
    "glow_street_mat": (0.45, 1.0, 0.7), "glow_lamp_mat": (1.0, 0.75, 0.45),
    "glow_sodium_mat": (1.0, 0.55, 0.2), "glow_tail_mat": (1.0, 0.02, 0.0), "glow_phone_mat": (0.75, 0.85, 1.0),
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

LAMP_104 = (9, 450)        # Room 104's red bulb: brightness, reach in cm
WIN = (320, 470, 108, 214)  # window opening: x from the room's left edge, bottom and top height
PHOTOS = ["pic_lake_dusk", "pic_lake_fog", "pic_dock", "pic_lake_night"]
PARTS = []      # every mesh made, combined at the end
ROOM_PARTS = []  # the insides of the rooms: exported as their own mesh on lighting channel 1
IN_ROOM = [False]


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
    (ROOM_PARTS if IN_ROOM[0] else PARTS).append(obj)
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


def light(name, x, y, z, color, intensity, radius, flicker=False, room=False, shadows=False):
    """A locator that becomes a point light in Unreal (flicker: dims in step with the dead neon).
    No light casts shadows (cheap, soft, PS2-like, and no shadow flicker). So outside light
    can't shine through the walls into the rooms, the room insides are on their own lighting
    channel: room=True lights reach only them, the other lights never do."""
    loc = cmds.spaceLocator(name=name)[0]
    cmds.move(x, z, y, loc)
    cmds.addAttr(loc, longName="ue_light", dataType="string")
    cmds.setAttr(loc + ".ue_light", json.dumps({"color": color, "intensity": intensity, "radius": radius, "flicker": flicker,
                                                        "room": room, "shadows": shadows}), type="string")
    return loc


# ---------- the building ----------

def room_row():
    """Six rooms, 101-106, all hollow with a doorway you can walk through. The doors
    themselves are BP_Examinable actors in Unreal (clues.json), so they swing open on E."""
    for i in range(ROOMS):
        x0 = X0 + i * ROOM_W
        x1 = x0 + ROOM_W
        number = 101 + i
        IN_ROOM[0] = True
        room_inside(x0, x1, her=(i == HER_ROOM), i=i)
        room_finish(i, x0, x1)             # maya/motel_interiors.py: ceiling, trim, bathroom door, ...
        if i == HER_ROOM:
            room_104(x0, x1)
        else:
            room_story(i, x0, x1)          # maya/motel_interiors.py
        IN_ROOM[0] = False
        wx0, wx1 = x0 + WIN[0], x0 + WIN[1]
        IN_ROOM[0] = True
        window_inside(wx0, wx1, lit=i in (1, 5), gap=16 if i == HER_ROOM else 0)
        IN_ROOM[0] = False
        facade(x0, x1, i, number)        # the outside (maya/exterior_props.py)


def room_inside(x0, x1, her=False, i=-1):
    """One motel room: walls, ceiling, carpet, bed, nightstand + lamp, dresser + TV.
    Every room has the same layout; Room 104 (Cas's) gets its clues from clues.json."""
    t = 20
    mid = (FRONT + BACK) / 2.0
    # side walls stop 1 cm short of the front wall's outer face: flush, they flashed through it
    # each wall: an outside half (plaster, in the outside mesh) and an inside half with the
    # motel wallpaper (the outside plaster inside read as concrete)
    h2 = t / 2.0
    IN_ROOM[0] = False
    box(x0, x1, BACK - h2, BACK, 0, H, "plaster_mat")                        # back
    box(x0, x0 + h2, FRONT + 1, BACK, 0, H, "plaster_mat")                   # left
    box(x1 - h2, x1, FRONT + 1, BACK, 0, H, "plaster_mat")                   # right
    IN_ROOM[0] = True
    box(x0, x1, BACK - t, BACK - h2, 0, H, "room_wall_mat")
    box(x0 + h2, x0 + t, FRONT + 1, BACK - h2, 0, H, "room_wall_mat")
    box(x1 - t, x1 - h2, FRONT + 1, BACK - h2, 0, H, "room_wall_mat")
    # the front wall is the motel's face, lit by the sign: it stays in the outside mesh, and a
    # thin lining on its inside face belongs to the room
    IN_ROOM[0] = False
    box(x0, x0 + 140, FRONT, FRONT + t, 0, H, "plaster_mat")                 # front, left of door
    wx0, wx1, wz0, wz1 = x0 + WIN[0], x0 + WIN[1], WIN[2], WIN[3]
    box(x0 + 280, wx0, FRONT, FRONT + t, 0, H, "plaster_mat")                # front, right of door,
    box(wx1, x1, FRONT, FRONT + t, 0, H, "plaster_mat")                      # around the window
    box(wx0, wx1, FRONT, FRONT + t, 0, wz0, "plaster_mat")
    box(wx0, wx1, FRONT, FRONT + t, wz1, H, "plaster_mat")
    box(x0 + 140, x0 + 280, FRONT, FRONT + t, 230, H, "plaster_mat")         # above door
    IN_ROOM[0] = True
    box(x0 + t, x0 + 140, FRONT + t + 1, FRONT + t + 2, 0, H - 10, "room_wall_mat")
    box(x0 + 280, wx0, FRONT + t + 1, FRONT + t + 2, 0, H - 10, "room_wall_mat")
    box(wx1, x1 - t, FRONT + t + 1, FRONT + t + 2, 0, H - 10, "room_wall_mat")
    box(wx0, wx1, FRONT + t + 1, FRONT + t + 2, 0, wz0, "room_wall_mat")
    box(wx0, wx1, FRONT + t + 1, FRONT + t + 2, wz1, H - 10, "room_wall_mat")
    box(x0 + 140, x0 + 280, FRONT + t + 1, FRONT + t + 2, 230, H - 10, "room_wall_mat")
    # baseboards, 1.5 cm proud of the wall
    for a, b in ((x0 + t, x0 + 140), (x0 + 280, x1 - t)):
        bevel_box(a, b, FRONT + t + 2, FRONT + t + 3.5, 1, 12, "wood_mat", r=0.4)
    bevel_box(x0 + t, x1 - t, BACK - t - 1.5, BACK - t, 1, 12, "wood_mat", r=0.4)
    bevel_box(x0 + t, x0 + t + 1.5, FRONT + t + 2, BACK - t, 1, 12, "wood_mat", r=0.4)
    bevel_box(x1 - t - 1.5, x1 - t, FRONT + t + 2, BACK - t, 1, 12, "wood_mat", r=0.4)
    box(x0 + 1, x1 - 1, FRONT + 1, BACK - 1, H - 10, H - 1, "ceiling_mat")   # ceiling (clear of the awning and front wall)
    box(x0 + t, x1 - t, FRONT + t, BACK - t, 0, 2, "carpet_mat")             # carpet
    # furniture (maya/room_props.py): bed, nightstand + lamp, dresser with an old TV against the
    # left wall facing the bed (kept clear of the doorway). Room 104 dresses its own bed.
    # some rooms' stories (maya/motel_interiors.py) change these: 101's lamp was knocked over,
    # 102's dresser was dragged to the door, 103 is stripped for a renovation
    bed(x0, x1, made=not her and i != 2, mattress=(i != 2))
    nightstand(x0)
    if i != 0:
        lamp(x0 + 180, BACK - 47, *(("glow_lamp_red_mat", "glow_lamp_red_mat") if her else ()))
    if i == 1:
        with Moved(x0 + 48, FRONT + 285, -28, 70, -40):
            dresser(x0)
            crt_tv(x0)
    else:
        dresser(x0)
        if i != 2:
            crt_tv(x0)
    # Room 104's fan light is on (Lamp_HerRoom, blockout.py); 102 and 106 look occupied (lit
    # curtains), so theirs are on too, the same light: warm, and the one kind of light that casts
    # shadows, so the fan blades throw shadows on the ceiling like in 104
    lit_fan = her or i in (1, 5)
    ceiling_fan(x0 + 250, (FRONT + BACK) / 2.0, H - 10, lit=lit_fan)
    if lit_fan and not her:
        light("light_fan_%d" % (101 + i), x0 + 250, (FRONT + BACK) / 2.0, 240, [1.0, 0.8, 0.55], 60, 1000, room=True, shadows=True)


def rbox(cx, cy, cz, sx, sy, sz, mat, yaw=0, tilt_x=0, tilt_y=0):
    """A box centred at an Unreal point, sizes along Unreal x/y/z, then turned:
    yaw spins it flat on the floor; tilt_x leans its top toward x, tilt_y toward y (degrees)."""
    b = cmds.polyCube(w=sx, h=sz, d=sy, ch=False)[0]
    cmds.xform(b, rotation=(tilt_y, -yaw, tilt_x), rotateOrder="yxz")
    cmds.move(cx, cz, cy, b)
    return keep(b, mat)


def tri(p0, p1, p2, mat):
    """One flat triangle between three Unreal points."""
    f = cmds.polyCreateFacet(p=[(p[0], p[2], p[1]) for p in (p0, p1, p2)], ch=False)[0]
    return keep(f, mat)


def picture(x_wall, y, z, w, h, mat, spin=0, facing=1):
    """A flat photo on a wall facing +x (facing=-1: -x) into the room, its texture filling it
    once. pic_* materials are pictures in Unreal (tools/make_photos.py draws them)."""
    p = cmds.polyPlane(w=h, h=w, sx=1, sy=1, ch=False)[0]        # turned on its side below
    cmds.xform(p, rotation=(spin, 0, -90 * facing), rotateOrder="zyx")
    cmds.polyEditUV(p + ".map[*]", pivotU=0.5, pivotV=0.5, angle=-90 * facing)  # upright (+90 left them upside down)
    cmds.move(x_wall, z, y, p)
    return keep(p, mat)


def room_104(x0, x1):
    """Cas's room, frozen in time: everything where she left it a year ago, as if she
    meant to be back that night, under a year of damp and dust. Her lake photos are taped
    over the dresser, her camera sits by the TV, a cold coffee and a dead plant are on the
    table, the bed is unmade, and one of the twig figures from her door hangs over the bed.
    The bedside lamp has a red bulb (the red light theme: red marks where something happened).
    Keep clear of the clues in clues.json: the note on the bed (-660, -850), the office key
    on the dresser (-952, -1182) and the door swing (x -860..-720, y -1380..-1240)."""
    t = 20
    inner_l, inner_r = x0 + t, x1 - t            # wall faces: -980 (dresser side), -520 (bed side)
    rng = random.Random(104)

    # --- the bed, slept in and left: blanket thrown back, pillows dented and askew
    bx0, bx1 = x0 + 220, x1 - 40
    # fitted sheet over the mattress (top 57.3: the note clue lies at 58)
    bevel_box(bx0 + 3, bx1 - 3, BACK - 247, BACK - 30, 44, 57.3, "sheet_mat", r=5.5, seg=3)
    # the bedspread, thrown back toward the foot; the note (clues.json) lies on it at (-708, -914)
    bedspread(bx0, bx1, BACK - 250, BACK - 150, 58.3, keep_flat=(-708, -914, 26), seed=3)
    pillow(bx0 + 66, BACK - 52, 57.5, 72, 44, 15, 46, yaw=-8, tilt_y=-8, dent=3.5)     # slept on
    pillow(bx1 - 62, BACK - 58, 57.5, 70, 42, 13, 47, yaw=14, dent=1.0)

    # --- nightstand: red bulb in the lamp, her diary with pages torn out
    lx, ly = x0 + 180, BACK - 47
    # the bulb: real (inverse-square) falloff, so it's hot right at the lamp and fades across the room.
    # It sits just under the shade: inside it, it burnt a white spot into the shade. Kept dim on
    # purpose: bright red light on the cream walls reads as pink.
    light("light_104_lamp", lx, ly - 22, 90, [1.0, 0.0, 0.0], LAMP_104[0], LAMP_104[1], room=True)
    diary(lx - 17, ly - 9, 60.2, -12)

    # --- the table under the window: cold coffee, dead plant, torn pages
    tx, ty, tz = x1 - 110, FRONT + 240, 70
    side_table(tx, ty, tz)
    mug(tx - 18, ty - 10, tz)
    plant_pot(tx + 18, ty + 14, tz, rng)
    for _ in range(4):                                                                    # dead leaves
        rbox(tx + rng.uniform(-5, 38), ty + rng.uniform(-10, 30), tz + 2.2, 4, 2.5, 0.3, "leaf_dead_mat", yaw=rng.uniform(0, 180))
    for k, (px, py, pz, yw) in enumerate(((tx - 20, ty + 18, tz + 0.6, 18), (tx - 5, ty + 26, tz + 1.4, -25),
                                          (tx - 40, ty + 60, 3.0, 40))):                  # torn diary pages, written on
        flat_picture(px, py, pz, 15, 20, f"pic_page_{k + 1}", yaw=yw)
    pen(tx + 5, ty - 22, tz, 32)
    # chair at the table with her jacket over the back
    cx_, cy_ = tx, ty + 70
    wood_chair(cx_, cy_, rng)

    # --- open suitcase on a luggage rack in the corner, clothes folded inside
    sx, sy = x1 - 95, FRONT + 400
    suitcase(sx, sy, rng)

    # --- her lake photos taped over the dresser, camera next to the TV
    for i in range(7):
        col, row = i % 4, i // 4
        py = FRONT + 210 + col * 42 + rng.uniform(-4, 4)
        pz = 172 + row * 34 + rng.uniform(-3, 3)
        spin = rng.uniform(-6, 6)
        rbox(inner_l + 0.6, py, pz, 1, 30, 23, "photo_border_mat", tilt_y=spin)
        picture(inner_l + 2.0, py, pz + 1, 26, 19.5, PHOTOS[i % len(PHOTOS)], spin=spin)
        rbox(inner_l + 3.0, py, pz + 11, 1, 8, 3, "tape_mat")
    # the empty 4th spot of the top row (at FRONT + 296 it sat right on top of another photo)
    rbox(inner_l + 0.6, FRONT + 336, 206, 1, 30, 23, "photo_border_mat", tilt_y=4)
    picture(inner_l + 2.0, FRONT + 336, 207, 26, 19.5, "pic_lanterns", spin=4)    # red lights out on the water
    rbox(inner_l + 3.0, FRONT + 336, 218, 1, 8, 3, "tape_mat")
    cam_x, cam_y = inner_l + 25, FRONT + 352
    camera(cam_x, cam_y, 80)
    investigation_wall(inner_l, FRONT)          # her notes, clipping, map and red string around the photos
    # the motel's framed landscape over the bed, on the left wall as you walk in
    py, pz, pw, ph = BACK - 135, 168, 84, 57
    bevel_box(inner_r - 3.5, inner_r, py - pw / 2 - 5, py + pw / 2 + 5, pz - ph / 2 - 5, pz + ph / 2 + 5, "frame_mat", r=1.2)
    picture(inner_r - 4.3, py, pz, pw, ph, "pic_painting", facing=-1)

    # --- twig figure on a string over the bed, turning slowly in the draft (still, here)
    fx, fy = x1 - 120, BACK - 160
    tube((fx, fy, H - 10), (fx, fy, 215), 0.3, "string_mat", sides=3)
    tube((fx, fy, 217), (fx + 1, fy, 168), 1.0, "twig_mat", sides=4)                      # body
    tube((fx - 17, fy, 202), (fx + 16, fy + 2, 199), 0.8, "twig_mat", sides=4)            # arms
    tube((fx, fy, 172), (fx - 11, fy, 142), 0.8, "twig_mat", sides=4)                     # legs
    tube((fx, fy, 172), (fx + 12, fy - 1, 143), 0.8, "twig_mat", sides=4)
    rbox(fx, fy, 200, 3.5, 3.5, 4, "string_mat")                                          # twine knots
    rbox(fx + 0.5, fy, 172, 3, 3, 4, "string_mat")

    # --- a year of damp: cobwebs
    # cobwebs: one big web in the back corner above the bed (you see it walking in), a small
    # one over the door
    cobweb((inner_r, BACK - t), -1, -1, 62, H - 10)
    cobweb((inner_l, FRONT + t + 2), 1, 1, 30, H - 10)


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


# ---------- the lot outside ----------

LOT = (-4000, 4000, -3800, -1700)        # x0, x1, y0 (road side), y1 (walkway edge)
rng = random.Random(41)                  # same cracks and stains every build


def flat(x0, x1, y0, y1, mat, h=DECAL_H["paint"], z=LOT_Z):
    """A thin flat piece lying on the lot (paint, patches)."""
    return box(x0, x1, y0, y1, z, z + h, mat)


def seg(p0, p1, width, mat, z=LOT_Z, h=DECAL_H["paint"]):
    """A thin strip from p0 to p1 on the ground, any angle (cracks, road lines)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy)
    b = cmds.polyCube(w=length, h=h, d=width, ch=False)[0]
    cmds.rotate(0, -math.degrees(math.atan2(dy, dx)), 0, b)      # Unreal x-y = Maya x-z
    cmds.move((p0[0] + p1[0]) / 2.0, z + h / 2.0, (p0[1] + p1[1]) / 2.0, b)
    return keep(b, mat)


def blot(x, y, r, mat, z=LOT_Z, h=DECAL_H["stain"]):
    """A round flat stain."""
    c = cmds.polyCylinder(r=r, h=h, sx=10, sy=1, sz=0, ch=False)[0]
    cmds.scale(1, 1, rng.uniform(0.6, 1.0), c)
    cmds.rotate(0, rng.uniform(0, 180), 0, c)
    cmds.move(x, z + h / 2.0, y, c)
    return keep(c, mat)


def crack(x, y, steps, length):
    """A wandering crack: a few short kinked strips."""
    ang = rng.uniform(0, math.pi)
    for _ in range(steps):
        ang += rng.uniform(-0.7, 0.7)
        nx, ny = x + math.cos(ang) * length, y + math.sin(ang) * length
        seg((x, y), (nx, ny), rng.uniform(2.5, 5), "crack_mat", h=DECAL_H["crack"])
        if rng.random() < 0.3:                               # a branch off the side
            bx, by = x + math.cos(ang + 1.2) * length * 0.6, y + math.sin(ang + 1.2) * length * 0.6
            seg((x, y), (bx, by), 2.5, "crack_mat", h=DECAL_H["crack"])
        x, y = nx, ny


def parking_lot():
    # stalls in front of the rooms: faded white lines (some worn away), a concrete stop in each
    for k in range(13):
        x = X0 + k * 250
        y_top, y_end = FRONT - WALK - 60, FRONT - WALK - 620
        if rng.random() < 0.25:                              # worn: only part of the line left
            y_end = y_top - rng.uniform(150, 400)
        flat(x - 6, x + 6, y_end, y_top, "paint_mat")
    # a few stalls by the office, and a painted arrow toward the exit
    for k in range(4):
        x = 2800 + k * 260
        flat(x - 6, x + 6, -2700, -2150, "paint_mat")
    seg((1200, -3050), (1200, -3350), 14, "paint_mat")
    seg((1200, -3350), (1150, -3270), 14, "paint_mat")
    seg((1200, -3350), (1250, -3270), 14, "paint_mat")
    # cracks, patches and oil stains are painted into the asphalt texture (tools/make_asphalt.py)


def road_lines():
    """Old Lake Road: dashed yellow centre line, faded white edge lines."""
    y, z = -4500, 3.6                       # above the road texture plane (2.8)
    for x in range(-19800, 19800, 900):
        seg((x, y), (x + 420, y), 12, "paint_yellow_mat", z=z, h=1.0)
    for edge in (-4060, -4940):
        for x in range(-19800, 19800, 1200):
            if rng.random() < 0.8:
                seg((x, edge), (x + rng.uniform(600, 1150), edge), 10, "paint_mat", z=z, h=1.0)


def lot_lamp(x, y, working):
    """A tall sodium lamp. The working one throws an orange pool; the dead one is just dark."""
    tube((x, y, 0), (x, y, 720), 10, "metal_mat", sides=8)
    tube((x, y, 700), (x - 170, y + 30, 735), 5, "metal_mat")
    box(x - 230, x - 140, y + 5, y + 55, 715, 740, "metal_mat")
    box(x - 225, x - 145, y + 10, y + 50, 711, 715, "glow_sodium_mat" if working else "glass_mat")
    box(x - 25, x + 25, y - 25, y + 25, 0, 60, "concrete_mat")             # base
    if working:
        light("light_lot", x - 185, y + 30, 690, [1.0, 0.55, 0.22], 3500, 1700)


def payphone(x, y):
    """A payphone on a post by the office, with a cold lit strip under its hood."""
    tube((x, y, 0), (x, y, 110), 5, "metal_mat")
    box(x - 32, x + 32, y - 22, y + 22, 100, 185, "payphone_mat")           # housing
    box(x - 38, x + 38, y - 30, y + 26, 185, 192, "payphone_mat")           # hood
    box(x - 34, x + 34, y - 30, y - 24, 192, 200, "glow_phone_mat")         # lit strip
    box(x - 14, x + 14, y - 25, y - 22, 140, 172, "metal_mat")              # keypad
    box(x - 28, x - 18, y - 30, y - 22, 120, 175, "trim_mat")               # handset
    tube((x - 23, y - 28, 120), (x - 5, y - 26, 104), 1, "trim_mat", sides=4)   # cord
    # no real light here: with the night exposure this high, even 1.5 cd this close lit the
    # phone brighter than the whole office wall. The glowing strip is enough.


def dumpster(x, y):
    box(x - 100, x + 100, y - 75, y + 75, 15, 125, "dumpster_mat")
    box(x - 104, x + 104, y - 79, y + 79, 125, 130, "dumpster_mat")         # lid (shut)
    for dx in (-80, 80):
        for dy in (-55, 55):
            tube((x + dx, y + dy, 0), (x + dx, y + dy, 15), 6, "tire_mat")  # castors
    for bx, by, r in ((x - 150, y - 60, 28), (x - 175, y + 10, 22), (x + 140, y - 90, 25)):
        b = cmds.polySphere(r=r, sx=8, sy=6, ch=False)[0]
        cmds.scale(1, 0.75, 1, b)
        cmds.move(bx, r * 0.7, by, b)
        keep(b, "bag_mat")


def trapezoid(x0, x1, y0, y1, z0, z1, inset_x, inset_front, inset_back, mat):
    """A box whose top face is pulled in: a car's cabin (windscreen and rear window slope)."""
    b = box(x0, x1, y0, y1, z0, z1, mat)
    cx = (x0 + x1) / 2.0
    for v in cmds.ls(b + ".vtx[*]", flatten=True):
        px, py, pz = cmds.pointPosition(v, world=True)                       # Maya: y is up, z is Unreal y
        if py > (z0 + z1) / 2.0:
            nx = cx + (px - cx) * (1 - 2.0 * inset_x / (x1 - x0))
            nz = pz - inset_front if pz > (y0 + y1) / 2.0 else pz + inset_back
            cmds.move(nx, py, nz, v, absolute=True, worldSpace=True)
    return b


def car(cx, cy):
    """Your car: a tired early-90s sedan, dark red, nose toward the motel (+y)."""
    w, front, back = 180, cy + 235, cy - 235
    x0, x1 = cx - w / 2, cx + w / 2
    box(x0, x1, back + 15, front - 15, 30, 82, "car_paint_mat")                     # body
    trapezoid(x0, x1, front - 135, front - 10, 82, 92, 6, 25, 0, "car_paint_mat")   # hood
    trapezoid(x0, x1, back + 10, back + 105, 82, 95, 6, 0, 15, "car_paint_mat")     # trunk
    trapezoid(x0 + 8, x1 - 8, back + 105, front - 135, 82, 138, 12, 45, 40, "glass_mat")   # cabin glass
    trapezoid(x0 + 20, x1 - 20, back + 150, front - 180, 136, 141, 2, 0, 0, "car_paint_mat")  # roof
    box(x0 - 2, x1 + 2, front - 18, front, 32, 50, "metal_mat")                     # bumpers
    box(x0 - 2, x1 + 2, back, back + 18, 32, 50, "metal_mat")
    for sx in (x0 + 18, x1 - 48):
        box(sx, sx + 30, front - 4, front + 1, 58, 72, "glass_mat")                 # headlights (off)
        box(sx, sx + 30, back - 1, back + 4, 60, 74, "glow_tail_mat")               # tail lights: red
    for wx in (x0 - 4, x1 - 18):
        for wy in (front - 75, back + 75):
            tube((wx, wy, 33), (wx + 22, wy, 33), 33, "tire_mat", sides=10)
    light("light_car_tail", cx, back - 60, 60, [1.0, 0.03, 0.0], 160, 380)         # red glow on the asphalt


def lot_dressing():
    parking_lot()
    parking_lot_detail()
    road_lines()
    lot_lamp(-3500, -2500, True)
    lot_lamp(-150, -3650, False)
    payphone(2930, -1830)
    dumpster(3960, -1150)
    # your car is the Fab "Low-Poly Classic Car" (unreal/place_car.py puts it in front of Room 104);
    # its red tail-light glow on the asphalt stays part of the red-light theme
    light("light_car_tail", -725, FRONT - WALK - 420 - 290, 60, [1.0, 0.03, 0.0], 160, 380)


# detailed furniture and Cas's things (bed, nightstand, lamp, dresser, TV, ...)
exec(open(os.path.join(ROOT, "maya", "room_props.py"), encoding="utf-8").read())
# detailed outside: room fronts, awning, lamps, payphone, dumpster, lot, car, doors
exec(open(os.path.join(ROOT, "maya", "exterior_props.py"), encoding="utf-8").read())
# the office inside (replaces office() above) and the other rooms' stories
exec(open(os.path.join(ROOT, "maya", "motel_interiors.py"), encoding="utf-8").read())


# ---------- build and export ----------

def build():
    del PARTS[:]
    del ROOM_PARTS[:]
    cmds.file(new=True, force=True)
    for name, rgb in MATS.items():
        material(name, rgb)
    room_row()
    awning()
    rooftop_sign()
    office()
    office_trim()
    streetlight(1500, -3500)
    lot_dressing()
    meshes = []
    for name, parts in (("set_motel", PARTS), ("set_motel_rooms", ROOM_PARTS)):
        m = cmds.polyUnite(parts, name=name, constructionHistory=False)[0]
        cmds.delete(m, constructionHistory=True)
        cmds.xform(m, pivots=(0, 0, 0), worldSpace=True)
        meshes.append(m)
    lights = cmds.ls("light_*", type="transform")
    cmds.group(lights, name="motel_lights")
    cmds.setAttr("perspShape.farClipPlane", 200000)
    cmds.file(rename=SCENE)
    cmds.file(save=True, type="mayaAscii")
    tris = sum(cmds.polyEvaluate(m, triangle=True) for m in meshes)
    export(meshes, lights)
    export_doors()
    print(f"Motel built: {tris} triangles, {len(lights)} lights -> {SCENE}")


def export(meshes, lights):
    """One FBX per mesh: set_motel (outside) and set_motel_rooms (room insides, own light channel)."""
    if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
        cmds.loadPlugin("fbxmaya")
    os.makedirs(OUT, exist_ok=True)
    sets, used = {}, set()
    for m in meshes:
        fbx = os.path.join(OUT, m + ".fbx").replace("\\", "/")
        cmds.select(m)
        mel.eval("FBXResetExport")
        mel.eval('FBXExport -f "{}" -s'.format(fbx))
        sets[m] = fbx
        for sg in cmds.listConnections(cmds.listRelatives(m, shapes=True), type="shadingEngine") or []:
            used.update(cmds.listConnections(sg + ".surfaceShader") or [])
    data = {
        "sets": sets,
        "room_sets": ["set_motel_rooms"],
        "materials": {m: list(cmds.getAttr(m + ".color")[0]) for m in sorted(used)},
        "lights": [dict(json.loads(cmds.getAttr(l + ".ue_light")), name=l,
                        position=[cmds.xform(l, q=True, t=True, ws=True)[i] for i in (0, 2, 1)]) for l in lights],
    }
    with open(os.path.join(OUT, "sets.json"), "w") as f:
        json.dump(data, f, indent=1)


build()

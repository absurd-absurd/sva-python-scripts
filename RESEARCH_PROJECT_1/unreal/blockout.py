"""Blockout for the motel -> woods -> lake level.

Run inside the Unreal editor (Tools > Execute Python Script, or remote execution).
Builds gray boxes for every place in the game so the layout can be walked
before anything is modeled. Safe to run again: it deletes the old blockout first.

Unreal units are centimeters, Z is up. The road is south (negative Y),
the lake is north (positive Y).
"""
import json
import math
import unreal

LAYOUT = json.load(open(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/layout.json"))

MAP_PATH = "/Game/Horror/Maps/MotelLake"
MAT_DIR = "/Game/Horror/Materials/Blockout"
TAG = "blockout"

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")        # 100 x 100 x 100, pivot in the center
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder")
PLANE = unreal.load_asset("/Engine/BasicShapes/Plane")      # 100 x 100, flat

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assets = unreal.AssetToolsHelpers.get_asset_tools()


# ---------- level ----------

def open_or_make_level():
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        levels.load_level(MAP_PATH)
    else:
        levels.new_level(MAP_PATH)


def clear_old_blockout():
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG):
            actors.destroy_actor(a)


# ---------- colors ----------

_mats = {}

def color(name, rgb):
    """A flat-color material instance, made once and reused."""
    if name in _mats:
        return _mats[name]
    path = f"{MAT_DIR}/MI_{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mi = unreal.load_asset(path)
    else:
        mi = assets.create_asset(f"MI_{name}", MAT_DIR, unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property("parent", unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial"))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        mi, "Color", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1))
    unreal.EditorAssetLibrary.save_loaded_asset(mi, False)
    _mats[name] = mi
    return mi


# ---------- placing shapes ----------

def place(label, folder, mesh, center, size, mat, yaw=0.0):
    """Put a shape whose size is given in centimeters (x, y, z)."""
    a = actors.spawn_actor_from_object(mesh, unreal.Vector(*center), unreal.Rotator(0, 0, yaw))
    a.set_actor_scale3d(unreal.Vector(size[0] / 100, size[1] / 100, size[2] / 100))
    a.static_mesh_component.set_material(0, mat)
    a.set_actor_label(label)
    a.set_folder_path(f"Blockout/{folder}")
    a.tags = [TAG]
    return a


def box(label, folder, x, y, z0, sx, sy, sz, mat, yaw=0.0):
    """A box standing on height z0 (its bottom), centered on x, y."""
    return place(label, folder, CUBE, (x, y, z0 + sz / 2), (sx, sy, sz), mat, yaw)


def strip(label, folder, p0, p1, width, mat, z=1.0):
    """A flat strip from point p0 to p1 (used for the road and the trail)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy)
    yaw = math.degrees(math.atan2(dy, dx))
    mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    return box(label, folder, mid[0], mid[1], z - 1, length + width * 0.5, width, 2, mat, yaw)


# ---------- the places ----------

def ground():
    m = color("Ground", (0.05, 0.06, 0.04))
    # the flat ground stops at the lake: the shore, the water and the lake bed come from maya/make_lake.py
    place("Ground", "Ground", PLANE, (0, -650, 0), (40000, 28700, 1), m)


STORY = json.load(open(r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/story.json"))


def sign_text(x, y, z):
    """The motel's name on both faces of the roadside sign, with a dim red glow."""
    name = STORY["places"]["motel"].upper()               # MARROW FALLS MOTEL
    top, _, bottom = name.rpartition(" ")                 # "MARROW FALLS" / "MOTEL"
    for side, yaw in ((1, 0), (-1, 180)):
        t = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(x + side * 22, y, z), unreal.Rotator(0, 0, yaw))
        c = t.text_render
        c.set_text(f"{top}\n{bottom}")
        c.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
        c.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
        c.set_world_size(55)
        c.set_text_render_color(unreal.Color(r=255, g=225, b=190, a=255))
        t.set_actor_label(f"MotelSign_Text{'' if side > 0 else '_Back'}")
        t.set_folder_path("Blockout/Motel")
        t.tags = [TAG]
    glow = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x + 120, y, z))
    glow.point_light_component.set_intensity(40)
    glow.point_light_component.set_light_color(unreal.LinearColor(1.0, 0.25, 0.2, 1))
    glow.point_light_component.set_attenuation_radius(600)
    glow.set_actor_label("MotelSign_Glow")
    glow.set_folder_path("Blockout/Lighting")
    glow.tags = [TAG]


def road_and_lot():
    asphalt = color("Asphalt", (0.03, 0.03, 0.03))
    strip("Road", "Motel", (-20000, -4500), (20000, -4500), 900, asphalt)
    # (the parking lot's slab, curbs and driveways are built in maya/grounds.py now)
    # (the fence behind the motel and its gate are built in maya/make_trail.py now)
    if not unreal.EditorAssetLibrary.does_asset_exist(MOTEL_SET):      # the Maya motel has the real car
        box("Car_Player", "Motel", -1800, -2600, 0, 450, 190, 140, color("Car", (0.1, 0.12, 0.15)))


MOTEL_SET = "/Game/Horror/Sets/set_motel"


def motel():
    """Gray-box motel. Skipped once the detailed Maya motel (make_motel.py) has been imported."""
    if unreal.EditorAssetLibrary.does_asset_exist(MOTEL_SET):
        return
    wall = color("MotelWall", (0.35, 0.3, 0.22))
    roof = color("Roof", (0.12, 0.08, 0.06))
    door = color("Door", (0.2, 0.1, 0.05))
    room_w, depth, h = 500, 700, 320
    front_y, back_y = -1400, -1400 + depth
    mid_y = (front_y + back_y) / 2
    xs = [-2500 + i * room_w for i in range(6)]   # left edge of each room
    her_room = 3                                  # Room 4 (counting from 1)

    for i, x0 in enumerate(xs):
        cx = x0 + room_w / 2
        name = f"Room{i + 1}"
        if i != her_room:
            box(name, "Motel", cx, mid_y, 0, room_w, depth, h, wall)
            box(name + "_Door", "Motel", cx - 120, front_y - 3, 0, 100, 6, 220, door)
            continue
        # Her room: hollow, with a doorway you can walk through.
        t = 20
        box(name + "_Back", "Motel/HerRoom", cx, back_y - t / 2, 0, room_w, t, h, wall)
        box(name + "_Left", "Motel/HerRoom", x0 + t / 2, mid_y, 0, t, depth, h, wall)
        box(name + "_Right", "Motel/HerRoom", x0 + room_w - t / 2, mid_y, 0, t, depth, h, wall)
        # front wall split around a doorway (140 wide x 230 tall; the player is 70 wide)
        d0, dw, dh = 140, 140, 230
        box(name + "_FrontL", "Motel/HerRoom", x0 + d0 / 2, front_y + t / 2, 0, d0, t, h, wall)
        box(name + "_FrontR", "Motel/HerRoom", (x0 + d0 + dw + x0 + room_w) / 2, front_y + t / 2, 0, room_w - d0 - dw, t, h, wall)
        box(name + "_FrontTop", "Motel/HerRoom", x0 + d0 + dw / 2, front_y + t / 2, dh, dw, t, h - dh, wall)
        box(name + "_Floor", "Motel/HerRoom", cx, mid_y, 0, room_w, depth, 2, color("Carpet", (0.12, 0.06, 0.06)))
        box(name + "_Bed", "Motel/HerRoom", cx + 60, back_y - 160, 0, 200, 220, 55, color("Bed", (0.4, 0.38, 0.34)))
        box(name + "_Nightstand", "Motel/HerRoom", cx - 110, back_y - 60, 0, 60, 50, 60, door)

    box("Motel_Roof", "Motel", xs[0] + room_w * 3, mid_y - 100, h, room_w * 6 + 100, depth + 300, 30, roof)
    # covered walkway posts in front
    for i in range(7):
        box(f"Walkway_Post{i}", "Motel", -2500 + i * room_w, front_y - 230, 0, 20, 20, h, roof)
    box("Office", "Motel", 3400, -1300, 0, 700, 900, 340, wall)
    box("Office_Door", "Motel", 3400, -1300 - 453, 0, 110, 6, 220, door)


TRAIL = [tuple(p) for p in LAYOUT["trail"]]   # shared with Maya


def trail():
    dirt = color("Dirt", (0.09, 0.07, 0.05))
    # a gap in the fence where the trail starts
    for i in range(len(TRAIL) - 1):
        strip(f"Trail{i}", "Woods/Trail", TRAIL[i], TRAIL[i + 1], 260, dirt, z=1.0)   # top 1 cm under the parking lot (flush, they flickered)


def structures():
    # (the hunting shack, the rusted car and the lookout tower are built in maya/make_trail.py now;
    #  the boathouse in maya/lake_buildings.py)
    pass


def lake():
    # (the dock is built in maya/make_lake.py now)
    # (the three cabins are built in maya/lake_buildings.py now)


def placeholder_trees():
    """Stand-in trunks so the woods read as woods. Skipped once the Maya scatter is imported."""
    import random
    if any(a.actor_has_tag("scatter") for a in actors.get_all_level_actors()):
        return
    rng = random.Random(7)
    bark = color("Bark", (0.07, 0.05, 0.04))
    w, clear = LAYOUT["woods"], LAYOUT["clearings"]
    n = 0
    while n < 260:
        x, y = rng.uniform(w["x_min"], w["x_max"]), rng.uniform(w["y_min"], w["y_max"])
        if min(math.hypot(x - px, y - py) for px, py in TRAIL) < 450:
            continue    # keep the trail clear (rough check against trail points)
        if any(math.hypot(x - c["x"], y - c["y"]) < c["r"] for c in clear):
            continue
        h = rng.uniform(800, 1600)
        place(f"TempTree{n}", "Woods/TempTrees", CYL, (x, y, h / 2), (rng.uniform(25, 50),) * 2 + (h,), bark)
        n += 1


def weather():
    """Almost night under heavy overcast: flat grey-blue light, no hard shadows, a dim
    blue-grey fog wall, washed-out low-contrast colors with grain. (Picked from test
    shots: brighter versions read as daytime.)"""
    def spawn(cls, label, loc=(0, 0, 0), rot=(0, 0, 0)):
        a = actors.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(*rot))
        a.set_actor_label(label)
        a.set_folder_path("Blockout/Lighting")
        a.tags = [TAG]
        return a

    sun = spawn(unreal.DirectionalLight, "Sun_Overcast", (0, 0, 2000), (0, -55, 60))
    lc = sun.light_component
    lc.set_intensity(3.0)
    lc.set_light_color(unreal.LinearColor(0.9, 0.92, 1.0, 1))
    lc.set_cast_shadows(False)                       # overcast: no hard shadows
    both = unreal.LightingChannels()
    both.set_editor_property("channel0", True)
    both.set_editor_property("channel1", True)
    lc.set_editor_property("lighting_channels", both)   # moonlight reaches the room insides too

    sky = spawn(unreal.SkyLight, "SkyLight", (0, 0, 1500))
    sc = sky.light_component
    sc.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sc.set_cubemap(unreal.load_asset("/Engine/EngineResources/GrayLightTextureCube"))   # plain grey sky
    sc.set_intensity(1.0)

    fog = spawn(unreal.ExponentialHeightFog, "Fog", (0, 0, 0))
    fc = fog.component
    fc.set_fog_density(0.18)
    fc.set_fog_height_falloff(0.25)
    fc.set_fog_inscattering_color(unreal.LinearColor(0.22, 0.24, 0.3, 1))    # blue-grey
    fc.set_editor_property("start_distance", 200)

    pp = spawn(unreal.PostProcessVolume, "PostProcess_Look", (0, 0, 0))
    pp.set_editor_property("unbound", True)
    s = pp.settings
    for name, value in (
        ("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL),
        ("auto_exposure_bias", 7.3),                 # raise to brighten, lower to darken
        ("color_saturation", unreal.Vector4(0.85, 0.85, 0.85, 1)),   # washed-out colors
        ("color_contrast", unreal.Vector4(0.9, 0.9, 0.9, 1)),    # milky, low contrast
        ("vignette_intensity", 0.35),
        ("film_grain_intensity", 0.5),
        ("bloom_intensity", 6.0),                   # big halo around the neon (picked from test shots)
    ):
        s.set_editor_property("override_" + name, True)
        s.set_editor_property(name, value)
    # keep the PS2 screen effect if ps2_look.py has made it
    screen = "/Game/Horror/Materials/PS2/MI_PS2_Screen"
    if unreal.EditorAssetLibrary.does_asset_exist(screen):
        s.set_editor_property("weighted_blendables", unreal.WeightedBlendables(
            array=[unreal.WeightedBlendable(weight=1.0, object=unreal.load_asset(screen))]))
    pp.set_editor_property("settings", s)

    # a dim lamp inside her room (the streetlight comes with the Maya motel)
    lamp = spawn(unreal.PointLight, "Lamp_HerRoom", (-750, -1050, 240))   # just under the ceiling fan's bowl
    lamp.point_light_component.set_intensity(60)
    lamp.point_light_component.set_light_color(unreal.LinearColor(1.0, 0.8, 0.55, 1))
    lamp.point_light_component.set_attenuation_radius(450)
    rooms = unreal.LightingChannels()
    rooms.set_editor_property("channel0", False)
    rooms.set_editor_property("channel1", True)
    lamp.point_light_component.set_editor_property("lighting_channels", rooms)   # room insides only

    spawn(unreal.PlayerStart, "PlayerStart", (-1000, -3300, 120), (0, 0, 90))


def main():
    open_or_make_level()
    clear_old_blockout()
    with unreal.ScopedSlowTask(8, "Building blockout") as task:
        for step in (ground, road_and_lot, motel, trail, structures, lake, placeholder_trees, weather):
            task.enter_progress_frame(1, step.__name__)
            step()
    levels.save_current_level()
    unreal.log("Blockout done")


main()

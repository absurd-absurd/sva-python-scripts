"""Walls of very thick fog round every edge of the map that isn't built, so you never see the
level just stop: right behind the ROAD CLOSED gate (maya/make_trail.py ROADBLOCK_X), all along
the east and west edges (the road runs into them both ways), along the south edge past the woods
across the road, and out on the lake past the drifting rowboat. Each wall is Local Fog Volumes
(UE 5.5) in rows: a soft one in front so the fog thickens gradually, then a solid one. They are
tall, so the treetops vanish too. Pale grey like the rest of the night fog.
Safe to run again (tag "edgefog").
"""
import unreal

TAG = "edgefog"
GATE_X = 7600.0
EDGE_X, SOUTH_Y, NORTH_Y = 12000.0, -9800.0, 25000.0        # the map's walls; the lake's far fog line
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
COUNT = [0]


def fog(x, y, scale, density):
    f = actors.spawn_actor_from_class(unreal.LocalFogVolume, unreal.Vector(x, y, 400), unreal.Rotator(0, 0, 0))
    f.set_actor_scale3d(unreal.Vector(scale, scale, 3.5))
    c = f.get_component_by_class(unreal.LocalFogVolumeComponent)
    c.set_radial_fog_extinction(density)
    c.set_height_fog_extinction(density)
    c.set_height_fog_falloff(1200.0)
    c.set_fog_albedo(unreal.LinearColor(0.32, 0.34, 0.38, 1))
    c.set_fog_emissive(unreal.LinearColor(0.004, 0.0045, 0.005, 1))
    f.set_actor_label("EdgeFog_%d" % COUNT[0])
    f.set_folder_path("Weather/EdgeFog")
    f.tags = [TAG]
    COUNT[0] += 1


def wall(axis, at, a, b, inward):
    """Fog along a line (axis "x": along x at y=at; "y": along y at x=at), rows stepping outward
    from the playable side (inward = the sign pointing back into the map)."""
    for off, scale, density in ((300.0, 2.0, 0.35), (1500.0, 3.0, 0.8), (3500.0, 5.0, 2.0)):
        step = scale * 1000 * 0.6
        t = a
        while t <= b + 1:
            pos = at - inward * off
            if axis == "x":
                fog(t, pos, scale, density)
            else:
                fog(pos, t, scale, density)
            t += step


def main():
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG):
            actors.destroy_actor(a)
    wall("y", GATE_X + 100, SOUTH_Y, 800.0, -1)           # right behind the ROAD CLOSED gate (east)
    wall("y", EDGE_X - 1500, 800.0, NORTH_Y, -1)          # the east edge, north of that, out over the lake
    wall("y", -EDGE_X + 1500, SOUTH_Y, NORTH_Y, 1)        # the west edge (the road runs into it)
    wall("x", SOUTH_Y + 1500, -EDGE_X, GATE_X, 1)         # the south edge, past the woods across the road
    wall("x", NORTH_Y, -EDGE_X, EDGE_X, -1)               # far out on the lake, past the rowboat
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print("edge fog:", COUNT[0], "volumes")


main()

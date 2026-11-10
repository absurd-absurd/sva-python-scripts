"""A wall of very thick fog east of the motel, just past the ROAD CLOSED gate (maya/make_trail.py
ROADBLOCK_X), so you can't see on down the road into the parts of the map that aren't built.
Local Fog Volumes (UE 5.5): overlapping fog spheres along a line from the south edge of the map
up into the woods, thin at the front edge and solid a few metres in. Pale grey like the rest of
the night fog. Safe to run again (tag "edgefog").
"""
import unreal

TAG = "edgefog"
X = 7700.0                         # just behind the gate
Y0, Y1 = -9800.0, 600.0
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def main():
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG):
            actors.destroy_actor(a)
    n = 0
    # two rows: a softer one right at the gate, a solid one behind it
    for row, (dx, scale, density) in enumerate(((900.0, 3.0, 0.6), (2600.0, 5.0, 2.0))):
        y = Y0
        step = scale * 1000 * 0.6
        while y <= Y1:
            f = actors.spawn_actor_from_class(unreal.LocalFogVolume, unreal.Vector(X + dx, y, 200), unreal.Rotator(0, 0, 0))
            f.set_actor_scale3d(unreal.Vector(scale, scale, 1.6))
            c = f.get_component_by_class(unreal.LocalFogVolumeComponent)
            c.set_radial_fog_extinction(density)
            c.set_height_fog_extinction(density)
            c.set_height_fog_falloff(200.0)
            c.set_fog_albedo(unreal.LinearColor(0.32, 0.34, 0.38, 1))
            c.set_fog_emissive(unreal.LinearColor(0.004, 0.0045, 0.005, 1))
            f.set_actor_label("EdgeFog_%d_%d" % (row, n))
            f.set_folder_path("Weather/EdgeFog")
            f.tags = [TAG]
            n += 1
            y += step
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print("edge fog:", n, "volumes")


main()

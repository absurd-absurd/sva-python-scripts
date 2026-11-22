"""Cas's boots by the boathouse water door (user 2026-11-22): the Fab "Hiking Boots LOWPOLY" pair, in place of
the boots maya/lake_buildings.py used to build there. Run in the Unreal editor after import_sets.py. Safe to run
again (deletes the old one first)."""
import unreal

MESH = "/Game/Fab/Hiking_Boots_LOWPOLY/hiking_boots_lowpoly"
AT = (-3752.0, 15025.0, 16.0)     # = lake_buildings boathouse(): BX, BYB, F (west walkway by the water door)
SCALE = 0.38                       # the scan is ~61 cm tall; a hiking boot is ~23 cm
YAW = 0.0                          # toes to the water (+y)
LABEL = "prop_cas_boots"

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actors.get_all_level_actors():
    if a.get_actor_label() == LABEL:
        actors.destroy_actor(a)
mesh = unreal.load_asset(MESH)
lo = mesh.get_bounding_box().min
a = actors.spawn_actor_from_object(mesh, unreal.Vector(AT[0], AT[1], AT[2] - lo.z * SCALE), unreal.Rotator(0, 0, YAW))
a.set_actor_label(LABEL)
a.set_folder_path("Props")
a.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
c = a.static_mesh_component
c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
lc = unreal.LightingChannels()                       # inside the boathouse = light channel 1, like the room sets
lc.set_editor_property("channel0", False)
lc.set_editor_property("channel1", True)
c.set_editor_property("lighting_channels", lc)
print("boots at", a.get_actor_location(), "bounds", a.get_actor_bounds(False))

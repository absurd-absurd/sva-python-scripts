"""Put the PlayerStart on the lakebed under the dock (traced, lifted until the capsule is clear).
Run after lakebed_level.py: the floor there slopes, so a fixed height can touch it."""
import unreal, json
s = json.load(open(r'C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_2/export/sets_lakebed.json'))['start']
A = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
OT = [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2]
hit = unreal.SystemLibrary.line_trace_single_for_objects(w, unreal.Vector(s[0], s[1], -60), unreal.Vector(s[0], s[1], -1000), OT, True, [], unreal.DrawDebugTrace.NONE, True)
t = hit.to_tuple()
print('floor hit', t[9].get_actor_label() if t[9] else None, t[4])
p = unreal.Vector(s[0], s[1], t[4].z + 100)
while unreal.SystemLibrary.capsule_overlap_actors(w, p, 42, 96, OT, None, []):
    p = unreal.Vector(p.x, p.y, p.z + 10)
for a in A.get_all_level_actors():
    if isinstance(a, unreal.PlayerStart):
        a.set_actor_location(p, False, False)
r = unreal.SystemLibrary.capsule_overlap_actors(w, p, 42, 96, OT, None, [])
print('start', p, 'overlap', [a.get_actor_label() for a in (r or [])])
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

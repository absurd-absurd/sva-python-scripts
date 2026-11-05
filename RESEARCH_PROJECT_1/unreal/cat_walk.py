"""Make the rigged black cat (unreal/cat_rig_import.py) walk its loop around the motel.

Run in the Unreal editor. Places a SkeletalMeshActor "BlackCat" and a looping Level Sequence
(LS_CatWalk) that starts by itself when the game starts: the cat walks slowly along the front of
the rooms, turns the corners, stops at two corners to stand and look around (A_Cat_Idle), and
keeps going round behind the rooms. The walk animation moves the paws exactly as far per step as
the sequence moves the cat, so the paws stay planted (no sliding).
Safe to run again: the old cat and sequence are replaced.
"""
import math

import unreal

DIR = "/Game/Horror/Critters/Cat"
SEQ = f"{DIR}/LS_CatWalk"
FPS = 30
SCALE = 0.75
STRIDE = 26.0 * SCALE          # cm per walk cycle (maya/make_cat_rig.py STRIDE), at this scale
CYCLE = 1.0                    # s per walk cycle (A_Cat_Walk)
SPEED = STRIDE / CYCLE         # ~20 cm/s: slow and unhurried
IDLE = 8.0                     # s, A_Cat_Idle
TURN = 1.5                     # s to turn a corner
# the loop (Unreal x, y): along the front edge of the walkway, round the east end, behind the
# rooms by the fence, round the west end. (pause) = stand and look around there.
PATH = [(-2700, -1780, True), (700, -1780, True), (700, -520, False), (-2700, -520, False)]

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def yaw_for(dx, dy):
    """The cat model faces +Y at yaw 0."""
    return math.degrees(math.atan2(dy, dx)) - 90.0


def plan():
    """Keyframes (time s, x, y, yaw) and animation spans [(start, end, 'Walk'|'Idle')]."""
    keys, spans, t = [], [], 0.0
    n = len(PATH)
    yaw = yaw_for(PATH[1][0] - PATH[0][0], PATH[1][1] - PATH[0][1])
    for i in range(n):
        x0, y0, pause = PATH[i]
        x1, y1, _ = PATH[(i + 1) % n]
        if pause:
            keys.append((t, x0, y0, yaw))
            spans.append((t, t + IDLE, "Idle"))
            t += IDLE
        new_yaw = yaw_for(x1 - x0, y1 - y0)
        while new_yaw - yaw > 180:
            new_yaw -= 360
        while new_yaw - yaw < -180:
            new_yaw += 360
        start = t
        keys.append((t, x0, y0, yaw))
        t += TURN
        keys.append((t, x0, y0, new_yaw))                 # turns on the spot, stepping
        yaw = new_yaw
        t += math.hypot(x1 - x0, y1 - y0) / SPEED
        keys.append((t, x1, y1, yaw))
        spans.append((start, t, "Walk"))
    return keys, spans, t


def main():
    for a in actors.get_all_level_actors():
        if a.get_actor_label() in ("BlackCat", "BlackCat_Sequence", "CATTEST"):
            actors.destroy_actor(a)
    if lib.does_asset_exist(SEQ):
        lib.delete_asset(SEQ)
    cat = actors.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(PATH[0][0], PATH[0][1], 3))
    cat.set_actor_label("BlackCat")
    cat.set_folder_path("Critters")
    c = cat.skeletal_mesh_component
    c.set_skinned_asset_and_update(unreal.load_asset(f"{DIR}/SK_Cat"))
    c.set_material(0, unreal.load_asset(f"{DIR}/MI_Cat"))
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    cat.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))

    keys, spans, total = plan()
    seq = tools.create_asset("LS_CatWalk", DIR, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    seq.set_display_rate(unreal.FrameRate(FPS, 1))
    seq.set_tick_resolution(unreal.FrameRate(FPS, 1))
    end = int(math.ceil(total * FPS))
    seq.set_playback_start(0)
    seq.set_playback_end(end)
    b = seq.add_possessable(cat)
    tr = b.add_track(unreal.MovieScene3DTransformTrack)
    sec = tr.add_section()
    sec.set_range(0, end)
    ch = sec.get_all_channels()                          # loc x y z, rot x y z, scale x y z
    lin = unreal.MovieSceneKeyInterpolation.LINEAR
    for t, x, y, yaw in keys:
        f = unreal.FrameNumber(int(round(t * FPS)))
        ch[0].add_key(f, x, interpolation=lin)
        ch[1].add_key(f, y, interpolation=lin)
        ch[2].add_key(f, 3.0, interpolation=lin)
        ch[5].add_key(f, yaw, interpolation=unreal.MovieSceneKeyInterpolation.AUTO)
        for k in (6, 7, 8):
            ch[k].add_key(f, SCALE, interpolation=lin)
    at = b.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    anims = {n: unreal.load_asset(f"{DIR}/A_Cat_{n}") for n in ("Walk", "Idle")}
    for s0, s1, name in spans:
        s = at.add_section()
        s.set_range(int(round(s0 * FPS)), int(round(s1 * FPS)))
        p = s.get_editor_property("params")
        p.set_editor_property("animation", anims[name])
        s.set_editor_property("params", p)
    lib.save_loaded_asset(seq, False)

    lsa = actors.spawn_actor_from_class(unreal.LevelSequenceActor, unreal.Vector(PATH[0][0], PATH[0][1], 50))
    lsa.set_actor_label("BlackCat_Sequence")
    lsa.set_folder_path("Critters")
    lsa.set_sequence(seq)
    ps = lsa.get_editor_property("playback_settings")
    lc = unreal.MovieSceneSequenceLoopCount()
    lc.set_editor_property("value", -1)                  # loop forever
    ps.set_editor_property("loop_count", lc)
    lsa.set_editor_property("playback_settings", ps)
    for prop in ("auto_play", "b_auto_play"):
        for obj in (lsa, ps):
            try:
                obj.set_editor_property(prop, True)
            except Exception:
                pass
    lsa.set_editor_property("playback_settings", ps)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print("cat walks: loop %.0f s (%d walk/idle sections), %.0f cm/s" % (total, len(spans), SPEED))


main()

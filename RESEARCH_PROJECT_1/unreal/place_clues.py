"""Put every clue, key and locked door from clues.json into the level.

Run in the Unreal editor after interact_setup.py (build_level.py runs it as the last step).
Safe to run again: it deletes the old clue actors (tag "clue") first. Each entry becomes a
BP_Examinable with its variables filled in; the HUD's starting objective comes from here too.
"""
import json
import os
import textwrap
import unreal

ROOT = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1"
DATA = json.load(open(ROOT + "/clues.json", encoding="utf-8"))
TAG = "clue"
HIT_MARGIN, HIT_UP = 10, 10   # cm the aim box sticks out around / above small clues
WRAP = 44                     # characters per line on the reading screen
# on a sheet (clues.json "paper") lines are shorter, and each hand is a different width (measured with
# PIL at the HUD's sizes in tools/make_interact_nodes.py HANDS, 2026-11-17)
SHEET_WRAP = {"cas": 39, "wrong": 28, "print": 44, "": 38}
MATS = "/Game/Horror/Materials/PS2/Props/"

# shape: size in cm (x, y, z), material, and where the mesh sits from the actor's origin.
# A door's origin is its hinge edge, so the Hinge component swings it like a real door.
SHAPES = {
    "paper": ((21, 28, 0.4), "MI_PS2_curtain_mat", (0, 0, 0.2)),   # yellowed, shows up on a white bed
    "map_ground": ((20, 26, 0.6), "MI_PS2_curtain_mat", (0, 0, 0.3)),   # Cas's map, folded, lying on the ground
    "folder": ((31, 23, 1.4), "MI_PS2_page_mat", (0, 0, 0.7)),          # a manila file folder (the 1974 log)
    "notebook": ((15, 21, 1.6), "MI_PS2_diary_mat", (0, 0, 0.8)),       # Cas's spiral notebook
    "wall_page": ((0.4, 21, 28), "MI_PS2_curtain_mat", (0, 0, 14)),     # a page nailed to a wall (faces +-x after yaw)
    "wall_zone": ((4, 340, 130), "MI_PS2_curtain_mat", (0, 0, 65)),
    "scrap_small": ((10, 7, 0.3), "MI_PS2_curtain_mat", (0, 0, 0.15)),  # a little torn scrap (the last page)     # invisible: the aim area over Cas's wall
    "key":   ((10, 4, 1.2), "MI_PS2_brass_mat", (0, 0, 0.6)),
    "book":  ((30, 22, 4), "MI_PS2_door_mat", (0, 0, 2)),
    "door":  ((108, 5, 228), "MI_PS2_door_mat", (54, 0, 114)),
    "room_door": ((138, 5, 228), "MI_PS2_door_mat", (69, 0, 114)),
    "plank_door": ((104, 5, 228), "MI_PS2_door_mat", (52, 0, 114)),        # the lake cabin
    "boathouse_door": ((104, 5, 228), "MI_PS2_door_mat", (52, 0, 114)),    # padlocked plank door
    "gate": ((206, 6, 176), "MI_PS2_galv_mat", (103, 0, 88)),             # the chain-link back gate
}
DOOR_MESH = {"room_door": "/Game/Horror/Sets/prop_room_door", "door": "/Game/Horror/Sets/prop_office_door",
             "plank_door": "/Game/Horror/Sets/prop_plank_door", "boathouse_door": "/Game/Horror/Sets/prop_boathouse_door",
             "gate": "/Game/Horror/Sets/prop_gate"}
FIELDS = {"prompt": "Prompt", "title": "Title", "body": "Body", "journal": "Journal",
          "gives_key": "GivesKey", "needs_key": "NeedsKey", "locked_text": "LockedText",
          "objective": "Objective", "pickup": "PickUp", "hand": "Hand", "paper": "Paper", "ends": "EndsGame",
          "open_angle": "OpenAngle"}

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
BPL = unreal.BlueprintEditorLibrary
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
PLANE = unreal.load_asset("/Engine/BasicShapes/Plane")
_kc = ROOT + "/export/keycards.json"
KEYCARDS = json.load(open(_kc)) if os.path.exists(_kc) else {}


def wrap(text, width=WRAP):
    """Break long lines so they fit the reading screen; keeps the blank lines between paragraphs."""
    return "\n".join(textwrap.fill(p, width) if p else "" for p in text.split("\n"))


ROOM_LIGHT = unreal.LightingChannels()
ROOM_LIGHT.set_editor_property("channel0", False)
ROOM_LIGHT.set_editor_property("channel1", True)


def in_room(at):
    """Inside one of the six motel rooms (import_sets.py puts their insides on light channel 1)."""
    return -2500 < at[0] < 500 and -1400 < at[1] < -700


def main():
    for a in actors.get_all_level_actors():
        if a.actor_has_tag(TAG):
            actors.destroy_actor(a)

    cls = BPL.generated_class(unreal.load_asset("/Game/Horror/Interact/BP_Examinable"))
    for c in DATA["clues"]:
        a = actors.spawn_actor_from_class(cls, unreal.Vector(*c["at"]), unreal.Rotator(0, 0, c.get("yaw", 0)))
        a.set_actor_label(c["id"])
        a.set_folder_path("Clues")
        a.tags = [TAG]
        for key, var in FIELDS.items():
            if key in c:
                if key == "body" and c.get("paper"):
                    value = wrap(c[key], SHEET_WRAP.get(c.get("hand", ""), SHEET_WRAP[""]))
                else:
                    value = wrap(c[key]) if key in ("body", "journal") else c[key]
                a.set_editor_property(var, value)
        a.set_editor_property("IsDoor", "door" in c["shape"])
        size, mat, offset = SHAPES[c["shape"]]
        # a key is its drawing, cut out and laid flat (unreal/key_cards.py; user 2026-11-17: "the keys are still
        # blocks, they should look exactly like the key image")
        card = KEYCARDS.get(c.get("paper", "")) if c["shape"] in ("key", "scrap_small", "paper") else None
        card_mi = card and unreal.load_asset(f"{MATS}MI_KeyCard_{c['paper']}")
        if card_mi:
            size, offset = (card[0], card[1], 0.6), (0, 0, 0.15)
        mesh = a.get_components_by_class(unreal.StaticMeshComponent)[0]
        door = DOOR_MESH.get(c["shape"])
        if door and unreal.EditorAssetLibrary.does_asset_exist(door):
            # the detailed panelled door from maya/exterior_props.py, built at its hinge
            mesh.set_static_mesh(unreal.load_asset(door))
            mesh.set_relative_location(unreal.Vector(0, 0, 0), False, True)
            mesh.set_relative_scale3d(unreal.Vector(1, 1, 1))
        elif card_mi:
            mesh.set_static_mesh(PLANE)
            mesh.set_relative_location(unreal.Vector(*offset), False, True)
            mesh.set_relative_scale3d(unreal.Vector(card[0] / 100, card[1] / 100, 1))
            mesh.set_material(0, card_mi)
        else:
            mesh.set_static_mesh(CUBE)
            mesh.set_relative_location(unreal.Vector(*offset), False, True)
            mesh.set_relative_scale3d(unreal.Vector(size[0] / 100, size[1] / 100, size[2] / 100))
            mesh.set_material(0, unreal.load_asset(MATS + mat))
        if c["shape"] == "wall_zone":                  # only the aim box counts; the wall itself is the prop
            mesh.set_visibility(False)
        if (c.get("room") or in_room(c["at"])) and "door" not in c["shape"]:
            mesh.set_editor_property("lighting_channels", ROOM_LIGHT)   # like the room around it
        # the invisible aim box: the object plus HIT_MARGIN all round (doors: just the door)
        # it sits on the same surface and rises HIT_UP cm above the object, so the aim line
        # meets it before the bed or table around it
        margin, up = (0, 0) if "door" in c["shape"] else (HIT_MARGIN, HIT_UP)
        hit = a.get_components_by_class(unreal.BoxComponent)[0]
        hit.set_relative_location(unreal.Vector(offset[0], offset[1], (size[2] + up) / 2), False, True)
        hit.set_box_extent(unreal.Vector(size[0] / 2 + margin, size[1] / 2 + margin, (size[2] + up) / 2), False)
        hit.set_collision_profile_name("UI")

    hud = unreal.load_asset("/Game/Horror/Interact/BP_HorrorHUD")
    unreal.get_default_object(BPL.generated_class(hud)).set_editor_property("Objective", DATA["start_objective"])
    unreal.EditorAssetLibrary.save_loaded_asset(hud, False)
    print(f"placed {len(DATA['clues'])} clues")


main()

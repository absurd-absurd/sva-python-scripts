"""Interaction system assets: E to examine, clue pickups, keys and locked doors, journal on Tab.

Run in the Unreal editor. Safe to run again (it only adds what is missing).

Makes, in /Game/Horror/Interact:
  BP_Examinable  - one actor class for every clue, key and door. What it does comes from
                   its variables, which place_clues.py fills in from clues.json:
                     Title, Body      -> the reading screen (no Body = no reading screen)
                     Journal          -> line added to the Tab journal the first time
                     GivesKey         -> key name you get the first time
                     NeedsKey         -> locked until you have that key (LockedText shown)
                     Objective        -> the objective line changes to this
                     PickUp           -> the object disappears after you take it
                     IsDoor           -> swings open (Hinge turns to OpenAngle) once unlocked
                   Components: DefaultSceneRoot > Hinge > Mesh, so a door turns on its edge.
  BP_HorrorHUD   - draws everything on screen (prompt, reading screen, journal, objective,
                   short messages) and handles E / Tab. Set as the game mode's HUD.
Input actions IA_Interact (E), IA_Journal (Tab) and IA_Map (M, works while paused) are added to IMC_Default.

The Blueprint graphs (the logic) can't be made from Python; tools/make_interact_nodes.py
writes them as text that gets pasted into the two graphs.
"""
import os

import unreal

DIR = "/Game/Horror/Interact"
INPUT_DIR = "/Game/FirstPerson/Input/Actions"
lib = unreal.EditorAssetLibrary
BPL = unreal.BlueprintEditorLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
T = BPL.get_basic_type_by_name


# ---------- input ----------

def input_action(name, keys, when_paused=False):
    path = f"{INPUT_DIR}/{name}"
    ia = unreal.load_asset(path) if lib.does_asset_exist(path) else \
        tools.create_asset(name, INPUT_DIR, unreal.InputAction, unreal.InputAction_Factory())
    ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
    ia.set_editor_property("trigger_when_paused", when_paused)
    lib.save_loaded_asset(ia, False)   # save even if Unreal did not mark it changed
    imc = unreal.load_asset("/Game/FirstPerson/Input/IMC_Default")
    have = {(m.action.get_name() if m.action else "", str(m.key.get_editor_property("key_name")))
            for m in imc.get_editor_property("mappings")}
    for key in keys:
        if (name, key) not in have:
            k = unreal.Key()
            k.set_editor_property("key_name", key)
            imc.map_key(ia, k)
    lib.save_loaded_asset(imc, False)   # save even if Unreal did not mark it changed


# ---------- Blueprints ----------

def blueprint(name, parent):
    path = f"{DIR}/{name}"
    if lib.does_asset_exist(path):
        return unreal.load_asset(path), False
    bp = BPL.create_blueprint_asset_with_parent(path, parent)
    BPL.remove_unused_nodes(bp)          # the gray placeholder events, so pasted events don't clash
    return bp, True


def add_vars(bp, spec, editable):
    """Add member variables that aren't there yet (add_member_variable would add a second
    copy named Var_0, so check the compiled class first)."""
    BPL.compile_blueprint(bp)
    cdo = unreal.get_default_object(BPL.generated_class(bp))
    for name, kind in spec:
        try:
            cdo.get_editor_property(name)
            continue                                  # already there
        except Exception:
            pass
        BPL.add_member_variable(bp, name, kind)
        if editable:
            BPL.set_blueprint_variable_instance_editable(bp, name, True)


def defaults(bp, values):
    cdo = unreal.get_default_object(BPL.generated_class(bp))
    for k, v in values.items():
        cdo.set_editor_property(k, v)


def components(bp):
    """DefaultSceneRoot > Hinge (scene) > Mesh (static mesh) + HitBox (box).
    HitBox is an invisible box a little bigger than the object that only the aim line hits
    (collision preset "UI"), so a thin note or a small key is easy to look at."""
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib_s = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    names = {str(lib_s.get_variable_name(lib_s.get_data(h))): h for h in handles}
    root = handles[0]

    def add(parent, cls, name):
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(
            parent_handle=parent, new_class=cls, blueprint_context=bp))
        sub.rename_subobject(h, name)
        return h

    if "Hinge" not in names:
        names["Hinge"] = add(root, unreal.SceneComponent, "Hinge")
        mesh = add(names["Hinge"], unreal.StaticMeshComponent, "Mesh")
        comp = lib_s.get_object(lib_s.get_data(mesh))
        comp.set_editor_property("static_mesh", unreal.load_asset("/Engine/BasicShapes/Cube"))
    if "HitBox" not in names:
        box = lib_s.get_object(lib_s.get_data(add(names["Hinge"], unreal.BoxComponent, "HitBox")))
        box.set_collision_profile_name("UI")


def make_font(path, ff_name, ttf):
    """A composite font at `path` (a copy of the engine's Roboto) whose regular style is the FontFace
    `ff_name` imported from `ttf`. The HUD canvas always draws with the first style."""
    if not lib.does_asset_exist(path):
        lib.duplicate_asset("/Engine/EngineFonts/Roboto", path)
    font = unreal.load_asset(path)
    ff = "/Game/Horror/UI/" + ff_name
    if not lib.does_asset_exist(ff):
        t = unreal.AssetImportTask()
        t.filename = ttf
        t.destination_path, t.destination_name = "/Game/Horror/UI", ff_name
        t.automated, t.save, t.replace_existing = True, True, True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        ffa = unreal.load_asset(ff)
        ffa.set_editor_property("loading_policy", unreal.FontLoadingPolicy.INLINE)   # all loaded up front
        lib.save_loaded_asset(ffa, False)
    # load the face first: import_text only links an asset that is already in memory; after an editor
    # restart it isn't, and the font silently gets an empty face (crash on the first DrawText, 2026-11-17)
    if lib.does_asset_exist(ff):
        unreal.load_asset(ff)
        face = f"/Script/Engine.FontFace'{ff}.{ff_name}'"
    else:
        unreal.load_asset("/Engine/EngineFonts/Faces/RobotoItalic")
        face = "/Script/Engine.FontFace'/Engine/EngineFonts/Faces/RobotoItalic.RobotoItalic'"
    cf = font.get_editor_property("composite_font")
    text = cf.export_text()
    fallback = text[text.index("FallbackTypeface="):]
    cf.import_text(f'(DefaultTypeface=(Fonts=((Name="Regular",Font=(FontFaceAsset="{face}")))),{fallback}')
    font.set_editor_property("composite_font", cf)
    font.set_editor_property("legacy_font_size", 40)   # rendered big and scaled down by the HUD (TEXT_SCALE): sharp, not pixelated
    lib.save_loaded_asset(font, False)   # save even if Unreal did not mark it changed


FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")


def italic_font():
    """/Game/Horror/UI/F_HUD_Italic: Bug's voice (corner lines, journal, titles). Nov 14: the user wanted
    the on-screen text in Ink Free; the asset keeps its old name so the HUD needs no change."""
    make_font("/Game/Horror/UI/F_HUD_Italic", "FF_InkFree", r"C:/Windows/Fonts/Inkfree.ttf")


def hand_fonts():
    """The three hands a paper can be in (clues.json "hand"), for the reading screen's body text
    (Nov 16-17): Cas = Rock Salt, the thing wearing her = Zeyada, the researchers' typed log = Courier New."""
    # Rock Salt's own line height is ~2.4 em (lots of empty space over the capitals), so the game uses
    # fonts/RockSalt-Tight.ttf: the same letters with ~0.6x the line spacing (made with fontTools, 2026-11-17).
    # (Unreal's FontFace ascend/descend override made the text vanish, so it isn't used.)
    make_font("/Game/Horror/UI/F_Hand_Cas", "FF_RockSalt", os.path.join(FONTS_DIR, "RockSalt-Tight.ttf"))
    make_font("/Game/Horror/UI/F_Hand_Wrong", "FF_Zeyada", os.path.join(FONTS_DIR, "Zeyada.ttf"))
    make_font("/Game/Horror/UI/F_Hand_Print", "FF_CourierNew", r"C:/Windows/Fonts/cour.ttf")
    # the title screen's menu, in the title's lettering (Century Gothic, 2026-11-17)
    make_font("/Game/Horror/UI/F_Menu", "FF_CenturyGothic", r"C:/Windows/Fonts/GOTHIC.TTF")


def opening_text():
    """clues.json game_text.opening without its last line (the postcard shows that), wrapped like the
    reading screen (44 characters a line)."""
    import json, textwrap
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    txt = json.load(open(os.path.join(root, "clues.json"), encoding="utf-8"))["game_text"]["opening"].rsplit("\n\n", 1)[0]
    return "\n".join(textwrap.fill(p, 44) if p else "" for p in txt.split("\n"))


def main():
    italic_font()
    hand_fonts()
    input_action("IA_Interact", ["E", "Gamepad_FaceButton_Bottom"])
    input_action("IA_Journal", ["Tab", "Gamepad_Special_Right"])
    input_action("IA_Map", ["M", "Gamepad_Special_Left"], when_paused=True)    # must work while the map pauses the game

    ex, _ = blueprint("BP_Examinable", unreal.Actor)
    components(ex)
    s, b, r = T("string"), T("bool"), T("real")
    add_vars(ex, [("Prompt", s), ("Title", s), ("Body", s), ("Journal", s), ("GivesKey", s),
                  ("NeedsKey", s), ("LockedText", s), ("Objective", s), ("Hand", s), ("Paper", s), ("EndsGame", b), ("PickUp", b),
                  ("IsDoor", b), ("OpenAngle", r)], editable=True)
    add_vars(ex, [("Done", b), ("Opened", b), ("Yaw", r)], editable=False)
    BPL.compile_blueprint(ex)
    defaults(ex, {"Prompt": "Examine", "LockedText": "It's locked.", "OpenAngle": 95.0})
    BPL.compile_blueprint(ex)
    lib.save_loaded_asset(ex, False)   # save even if Unreal did not mark it changed

    hud, _ = blueprint("BP_HorrorHUD", unreal.HUD)
    add_vars(hud, [("Focus", BPL.get_object_reference_type(BPL.generated_class(ex))),
                   ("Reading", b), ("JournalOpen", b), ("ReadTitle", s), ("ReadBody", s), ("ReadHand", s), ("ReadPaper", s),
                   ("Journal", s), ("Keys", s), ("Objective", s), ("Toast", s), ("ToastTime", r),
                   ("Gap", s), ("MapOpen", b),
                   ("Opening", b), ("OpenStart", r), ("OpenEnd", r), ("OpeningText", s),   # the opening (2026-11-17)
                   ("ReadEnds", b), ("Ending", b), ("EndStart", r), ("EndShot", b),          # the ending (2026-11-17)
                   ("Title", b), ("ControlsOpen", b), ("MenuHover", s),                                       # the title screen (2026-11-17)
                   # flashlight flicker timer: mode 0 on / 1 flutter / 2 off, next start, end, hit on return
                   ("FlMode", T("int")), ("FlNext", r), ("FlEnd", r), ("FlHit", b),
                   ("FlDim", r)], editable=False)   # flashlight auto-dim near walls (0..1)
    BPL.compile_blueprint(hud)
    defaults(hud, {"Gap": "\n\n", "ToastTime": -100.0, "Objective": "", "FlNext": 4.0, "FlDim": 1.0,
                   "Opening": True, "OpenEnd": -100.0, "Title": True, "OpeningText": opening_text()})
    BPL.compile_blueprint(hud)
    lib.save_loaded_asset(hud, False)   # save even if Unreal did not mark it changed

    gm = unreal.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode")
    unreal.get_default_object(BPL.generated_class(gm)).set_editor_property("hud_class", BPL.generated_class(hud))
    BPL.compile_blueprint(gm)
    lib.save_loaded_asset(gm, False)   # save even if Unreal did not mark it changed
    print("interaction assets ready")


main()

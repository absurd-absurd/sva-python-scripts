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
Input actions IA_Interact (E) and IA_Journal (Tab) are added to IMC_Default.

The Blueprint graphs (the logic) can't be made from Python; tools/make_interact_nodes.py
writes them as text that gets pasted into the two graphs.
"""
import unreal

DIR = "/Game/Horror/Interact"
INPUT_DIR = "/Game/FirstPerson/Input/Actions"
lib = unreal.EditorAssetLibrary
BPL = unreal.BlueprintEditorLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
T = BPL.get_basic_type_by_name


# ---------- input ----------

def input_action(name, keys):
    path = f"{INPUT_DIR}/{name}"
    ia = unreal.load_asset(path) if lib.does_asset_exist(path) else \
        tools.create_asset(name, INPUT_DIR, unreal.InputAction, unreal.InputAction_Factory())
    ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
    lib.save_loaded_asset(ia)
    imc = unreal.load_asset("/Game/FirstPerson/Input/IMC_Default")
    have = {(m.action.get_name() if m.action else "", str(m.key.get_editor_property("key_name")))
            for m in imc.get_editor_property("mappings")}
    for key in keys:
        if (name, key) not in have:
            k = unreal.Key()
            k.set_editor_property("key_name", key)
            imc.map_key(ia, k)
    lib.save_loaded_asset(imc)


# ---------- Blueprints ----------

def blueprint(name, parent):
    path = f"{DIR}/{name}"
    if lib.does_asset_exist(path):
        return unreal.load_asset(path), False
    bp = BPL.create_blueprint_asset_with_parent(path, parent)
    BPL.remove_unused_nodes(bp)          # the gray placeholder events, so pasted events don't clash
    return bp, True


def add_vars(bp, spec, editable):
    for name, kind in spec:
        BPL.add_member_variable(bp, name, kind)       # does nothing if it already exists
        if editable:
            BPL.set_blueprint_variable_instance_editable(bp, name, True)


def defaults(bp, values):
    cdo = unreal.get_default_object(BPL.generated_class(bp))
    for k, v in values.items():
        cdo.set_editor_property(k, v)


def components(bp):
    """DefaultSceneRoot > Hinge (scene) > Mesh (static mesh)."""
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib_s = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    names = {str(lib_s.get_variable_name(lib_s.get_data(h))): h for h in handles}
    if "Hinge" in names:
        return
    root = handles[0]

    def add(parent, cls, name):
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(
            parent_handle=parent, new_class=cls, blueprint_context=bp))
        sub.rename_subobject(h, name)
        return h

    hinge = add(root, unreal.SceneComponent, "Hinge")
    mesh = add(hinge, unreal.StaticMeshComponent, "Mesh")
    comp = lib_s.get_object(lib_s.get_data(mesh))
    comp.set_editor_property("static_mesh", unreal.load_asset("/Engine/BasicShapes/Cube"))


def italic_font():
    """/Game/Horror/UI/F_HUD_Italic: a copy of the engine's Roboto whose regular style is the
    italic face. The HUD draws all its text with it (the canvas always uses the first style)."""
    path = "/Game/Horror/UI/F_HUD_Italic"
    if not lib.does_asset_exist(path):
        lib.duplicate_asset("/Engine/EngineFonts/Roboto", path)
    font = unreal.load_asset(path)
    face = "/Script/Engine.FontFace'/Engine/EngineFonts/Faces/RobotoItalic.RobotoItalic'"
    cf = font.get_editor_property("composite_font")
    text = cf.export_text()
    fallback = text[text.index("FallbackTypeface="):]
    cf.import_text(f'(DefaultTypeface=(Fonts=((Name="Regular",Font=(FontFaceAsset="{face}")))),{fallback}')
    font.set_editor_property("composite_font", cf)
    lib.save_loaded_asset(font)


def main():
    italic_font()
    input_action("IA_Interact", ["E", "Gamepad_FaceButton_Bottom"])
    input_action("IA_Journal", ["Tab", "Gamepad_Special_Right"])

    ex, _ = blueprint("BP_Examinable", unreal.Actor)
    components(ex)
    s, b, r = T("string"), T("bool"), T("real")
    add_vars(ex, [("Prompt", s), ("Title", s), ("Body", s), ("Journal", s), ("GivesKey", s),
                  ("NeedsKey", s), ("LockedText", s), ("Objective", s), ("PickUp", b),
                  ("IsDoor", b), ("OpenAngle", r)], editable=True)
    add_vars(ex, [("Done", b), ("Opened", b), ("Yaw", r)], editable=False)
    BPL.compile_blueprint(ex)
    defaults(ex, {"Prompt": "Examine", "LockedText": "It's locked.", "OpenAngle": 95.0})
    BPL.compile_blueprint(ex)
    lib.save_loaded_asset(ex)

    hud, _ = blueprint("BP_HorrorHUD", unreal.HUD)
    add_vars(hud, [("Focus", BPL.get_object_reference_type(BPL.generated_class(ex))),
                   ("Reading", b), ("JournalOpen", b), ("ReadTitle", s), ("ReadBody", s),
                   ("Journal", s), ("Keys", s), ("Objective", s), ("Toast", s), ("ToastTime", r),
                   ("Gap", s)], editable=False)
    BPL.compile_blueprint(hud)
    defaults(hud, {"Gap": "\n\n", "ToastTime": -100.0, "Objective": "Find Room 4."})
    BPL.compile_blueprint(hud)
    lib.save_loaded_asset(hud)

    gm = unreal.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode")
    unreal.get_default_object(BPL.generated_class(gm)).set_editor_property("hud_class", BPL.generated_class(hud))
    BPL.compile_blueprint(gm)
    lib.save_loaded_asset(gm)
    print("interaction assets ready")


main()

"""Run input: hold Left Shift (or click the left stick) to run.

Run in the Unreal editor. Makes /Game/FirstPerson/Input/Actions/IA_Run (a button) and maps
it in IMC_Default, the template's input mapping. The character Blueprint uses IA_Run:
pressed -> MaxWalkSpeed 550, released -> 300 (the careful walk).
"""
import unreal

ACTION = "/Game/FirstPerson/Input/Actions/IA_Run"
lib = unreal.EditorAssetLibrary

if lib.does_asset_exist(ACTION):
    ia = unreal.load_asset(ACTION)
else:
    ia = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "IA_Run", ACTION.rsplit("/", 1)[0], unreal.InputAction, unreal.InputAction_Factory())
ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
lib.save_loaded_asset(ia)

imc = unreal.load_asset("/Game/FirstPerson/Input/IMC_Default")
have = {(m.action.get_name() if m.action else "", str(m.key.get_editor_property("key_name"))) for m in imc.get_editor_property("mappings")}
for key in ("LeftShift", "Gamepad_LeftThumbstick"):
    if ("IA_Run", key) not in have:
        k = unreal.Key()
        k.set_editor_property("key_name", key)
        imc.map_key(ia, k)
lib.save_loaded_asset(imc)
print("IA_Run keys:", [str(m.key.get_editor_property("key_name")) for m in imc.get_editor_property("mappings") if m.action == ia])

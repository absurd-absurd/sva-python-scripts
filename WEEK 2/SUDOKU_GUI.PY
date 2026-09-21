"""
sudoku_gui.py

Maya tool (maya.cmds UI, no PySide needed) that pops up a small, easy,
playable 4x4 mini-sudoku (numbers 1-4, 2x2 boxes) as a real interactive
grid of text fields -- type the numbers in, check your answer, and a
correct solve builds a 3D gold star in the viewport as a reward.

THE POPUP WINDOW *IS* THE GAME -- there's no separate board drawn in
the 3D scene. You solve the puzzle in the tool's own window; the only
thing that appears in the Maya viewport is the reward star once you
solve it.

DESIGN PROBLEM
---------------
A "make a sudoku" tool is trivial if you don't care whether the result
is an actual sudoku: you could scatter random digits on a grid and call
it done. A real sudoku has to satisfy two much harder constraints:
every row/column/box contains each digit exactly once, AND the puzzle
(with cells blanked out) has to have exactly ONE solution -- checked by
actually re-solving it after every cell removed, not assumed.

Earlier versions of this tool tried to DRAW the puzzle onto 3D geometry
in the scene -- first as raised "7-segment" digits, then as a hand-
rendered image texture. Both turned out to be fighting the wrong
problem: getting Maya to reliably display custom digit shapes (fonts
differ per machine, texture display depends on viewport settings that
differ per machine) was more fragile than the sudoku logic itself ever
was. The actual fix was realizing Maya's own UI widgets already render
numbers correctly on every machine, because that's the operating
system's native UI font -- so this version doesn't draw a single digit
itself. The "board" is real Maya text fields you type into, and the
only 3D geometry built is the reward star, which never needs to show
text at all.

WHY 4x4 AND NOT 9x9
---------------------
A regular 9x9 sudoku takes real solving effort. Making this a small,
fast, genuinely-easy puzzle (4 numbers, 2x2 boxes, most cells already
filled in) means someone can open the tool and solve it in well under
a minute -- the point here is demonstrating the interactive loop and
the reward, not testing anyone's sudoku skills.

WHAT IT HAS TO GET RIGHT
--------------------------
1. The generated puzzle must be a fully valid mini-sudoku with exactly
   one solution.
2. Checking a solve compares against that real, unique answer.
3. Wrong entries get highlighted, not just rejected, so solving it
   inside the tool is actually possible.
4. It survives running on a machine with no Maya at all -- the puzzle
   logic is plain Python with zero Maya dependency, and the bottom of
   this file prints a puzzle to the terminal instead of crashing if
   maya.cmds can't be imported.

HOW TO USE IN MAYA
-------------------
1. Open Maya's Script Editor (Windows > General Editors > Script Editor),
   on a Python tab.
2. Paste this whole file in and run it (Ctrl+Enter / Execute All).
3. A small "Sudoku" window opens. Given digits are shaded and locked;
   click an empty box and type 1-4.
4. Hit "Check Solution". Wrong cells turn red -- fix and check again.
   A correct solve builds a gold star in the viewport.
5. "New Puzzle" starts over with a freshly generated one.
"""

import math
import random

try:
    import maya.cmds as cmds
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False


_REWARD_GROUP_NAME = "sudokuRewardStar_grp"

# grid is BOX_SIZE x BOX_SIZE boxes of BOX_SIZE x BOX_SIZE cells each --
# 2x2 boxes of 2x2 cells = a 4x4 grid using digits 1-4. Every solver
# function below works off these two numbers instead of hardcoded 9s/3s,
# so this is the one place puzzle size is decided.
BOX_SIZE = 2
GRID_SIZE = BOX_SIZE * BOX_SIZE

# how many of the GRID_SIZE*GRID_SIZE cells each difficulty leaves filled in --
# carving stops early if removing more would break uniqueness, so a puzzle may
# end up with a couple more clues than the target if it has to
DIFFICULTY_CLUE_TARGETS = {
    "Easy": 12,
    "Medium": 9,
    "Hard": 7,
    "Expert": 6,
}


# ---------------------------------------------------------------------------
# Sudoku solver / generator -- pure Python, no Maya dependency at all
# ---------------------------------------------------------------------------
def _is_valid(grid, row, col, value):
    # a placement is legal only if that value doesn't already appear in the row, column, or box
    for i in range(GRID_SIZE):
        if grid[row][i] == value or grid[i][col] == value:
            return False
    box_row, box_col = (row // BOX_SIZE) * BOX_SIZE, (col // BOX_SIZE) * BOX_SIZE
    for r in range(box_row, box_row + BOX_SIZE):
        for c in range(box_col, box_col + BOX_SIZE):
            if grid[r][c] == value:
                return False
    return True


def _find_best_empty_cell(grid):
    # picking the empty cell with the FEWEST legal candidates (instead of just the first blank)
    # makes backtracking dramatically faster, since we fail fast on the most constrained cells
    best_cell = None
    best_candidates = None
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if grid[r][c] == 0:
                candidates = [v for v in range(1, GRID_SIZE + 1) if _is_valid(grid, r, c, v)]
                if best_candidates is None or len(candidates) < len(best_candidates):
                    best_cell, best_candidates = (r, c), candidates
                    if len(candidates) == 0:
                        return best_cell, best_candidates  # dead end, bail out early
    return best_cell, best_candidates


def _fill_full_grid(grid):
    """Recursively fill an empty grid into one complete, valid, randomized solution."""
    cell, candidates = _find_best_empty_cell(grid)
    if cell is None:
        return True  # no empty cells left -- solved
    row, col = cell
    random.shuffle(candidates)
    for value in candidates:
        grid[row][col] = value
        if _fill_full_grid(grid):
            return True
        grid[row][col] = 0
    return False


def _count_solutions(grid, limit=2):
    """Counts solutions up to `limit`, stopping early -- we only need to know if it's exactly 1."""
    cell, candidates = _find_best_empty_cell(grid)
    if cell is None:
        return 1  # reached a complete, valid grid -- that's one solution
    row, col = cell
    total = 0
    for value in candidates:
        grid[row][col] = value
        total += _count_solutions(grid, limit - total)
        grid[row][col] = 0
        if total >= limit:
            break  # found enough solutions to know it's not unique -- no need to keep searching
    return total


def _carve_puzzle(solved_grid, target_clues, seed=None):
    """Remove cells from a solved grid one at a time, only keeping a removal if the
    puzzle still has exactly one solution afterward -- this is what makes it a real
    sudoku instead of just a grid with holes in it."""
    if seed is not None:
        random.seed(seed)

    puzzle = [row[:] for row in solved_grid]
    cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
    random.shuffle(cells)

    clues_remaining = GRID_SIZE * GRID_SIZE
    for row, col in cells:
        if clues_remaining <= target_clues:
            break
        removed_value = puzzle[row][col]
        puzzle[row][col] = 0

        # test uniqueness on a scratch copy so we don't disturb the puzzle we're building
        test_grid = [r[:] for r in puzzle]
        if _count_solutions(test_grid, limit=2) != 1:
            puzzle[row][col] = removed_value  # removing this cell broke uniqueness -- put it back
        else:
            clues_remaining -= 1

    return puzzle


def generate_puzzle(difficulty="Easy", seed=None):
    """Returns (puzzle, solved) -- both GRID_SIZE x GRID_SIZE lists of lists, 0 = blank."""
    if seed is not None:
        random.seed(seed)

    solved = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    _fill_full_grid(solved)

    target_clues = DIFFICULTY_CLUE_TARGETS.get(difficulty, DIFFICULTY_CLUE_TARGETS["Easy"])
    puzzle = _carve_puzzle(solved, target_clues, seed=seed)
    return puzzle, solved


def _grid_to_text(grid):
    lines = []
    for r in range(GRID_SIZE):
        if r % BOX_SIZE == 0 and r != 0:
            lines.append("-" * (GRID_SIZE * 2 + BOX_SIZE - 1))
        row_cells = []
        for c in range(GRID_SIZE):
            if c % BOX_SIZE == 0 and c != 0:
                row_cells.append("|")
            row_cells.append(str(grid[r][c]) if grid[r][c] != 0 else ".")
        lines.append(" ".join(row_cells))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reward: a puffy, rounded-edge 3D star -- like a star-shaped plush toy/balloon,
# not a faceted low-poly star. Built the same reliable way as the labyrinth
# walls were (individual quads via polyCreateFacet, unite, merge), just with
# many horizontal rings instead of two, then rounded off with polySmooth.
# No text, no fonts, nothing that can vary by machine.
# ---------------------------------------------------------------------------
def _make_color_shader(color, name):
    shader = cmds.shadingNode("lambert", asShader=True, name=name)
    cmds.setAttr(shader + ".color", color[0], color[1], color[2], type="double3")
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name + "SG")
    cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader", force=True)
    return sg


def _assign_color(transform, color, name):
    sg = _make_color_shader(color, name)
    cmds.sets(transform, edit=True, forceElement=sg)


def _dome_profile(rings_per_hemisphere):
    """Latitude angles (radians, 0 = equator, +-pi/2 = pole) for the rings between the
    equator and each pole, evenly spaced in ANGLE rather than in height. That's what makes
    the silhouette bulge like a rounded dome instead of tapering off in straight lines --
    the same trick as building a sphere from latitude bands."""
    return [(i / float(rings_per_hemisphere + 1)) * (math.pi / 2.0)
            for i in range(1, rings_per_hemisphere + 1)]


def build_reward_star(num_points=5, outer_radius=2.6, inner_radius=1.15, puff_height=2.6,
                       rings_per_hemisphere=5, smooth_divisions=2,
                       center=(0.0, 3.0, 0.0), color=(1.0, 0.88, 0.45),
                       group_name=_REWARD_GROUP_NAME):
    """Builds a puffy, rounded 5-pointed star -- a star-shaped balloon -- as a single mesh.

    Rather than a flat prism with hard edges, this stacks horizontal star-outline rings
    from a bottom point up through the equator to a top point, each ring scaled down by
    how close it is to a pole (following a quarter-circle profile, see _dome_profile), so
    the whole shape is already rounded before any smoothing happens. cmds.polySmooth then
    softens every remaining facet -- including the star's point tips -- into the soft,
    inflated look of a plush toy instead of a faceted low-poly star.
    """
    n = num_points * 2
    directions = []
    for i in range(n):
        angle = math.radians(90.0 - i * (360.0 / n))
        base_radius = outer_radius if i % 2 == 0 else inner_radius
        directions.append((math.cos(angle) * base_radius, math.sin(angle) * base_radius))

    latitudes = _dome_profile(rings_per_hemisphere)
    # ring stack from bottom pole to top pole: bottom-hemisphere latitudes (most-negative
    # first, so the list already runs bottom-to-top), the equator, then the top hemisphere
    ring_latitudes = [-lat for lat in reversed(latitudes)] + [0.0] + latitudes

    rings = []
    for lat in ring_latitudes:
        radial_scale = math.cos(lat)
        y = center[1] + math.sin(lat) * (puff_height / 2.0)
        rings.append([(center[0] + dx * radial_scale, y, center[2] + dz * radial_scale)
                      for dx, dz in directions])

    bottom_pole = (center[0], center[1] - puff_height / 2.0, center[2])
    top_pole = (center[0], center[1] + puff_height / 2.0, center[2])

    faces = []

    # bottom pole cap -- a fan of triangles closing off the lowest ring to a single point.
    # order is (pole, j, i) -- the reverse of the "increasing" order used everywhere else --
    # so this cap's normal faces down and out, matching the bottom-cap winding the original
    # flat star used (see the "reversed winding" note that used to live here).
    lowest_ring = rings[0]
    for i in range(n):
        j = (i + 1) % n
        faces.append(cmds.polyCreateFacet(
            point=[bottom_pole, lowest_ring[j], lowest_ring[i]], constructionHistory=False)[0])

    # side bands between every pair of consecutive rings, climbing from bottom to top --
    # same (lower[i], lower[j], upper[j], upper[i]) winding proven on the original star's
    # single band and on the labyrinth walls, just repeated once per ring pair now
    for ring_index in range(len(rings) - 1):
        lower, upper = rings[ring_index], rings[ring_index + 1]
        for i in range(n):
            j = (i + 1) % n
            faces.append(cmds.polyCreateFacet(
                point=[lower[i], lower[j], upper[j], upper[i]], constructionHistory=False)[0])

    # top pole cap -- increasing order, so its normal faces up and out
    highest_ring = rings[-1]
    for i in range(n):
        j = (i + 1) % n
        faces.append(cmds.polyCreateFacet(
            point=[top_pole, highest_ring[i], highest_ring[j]], constructionHistory=False)[0])

    merged = cmds.polyUnite(faces, constructionHistory=False, name="rewardStar")[0]
    cmds.polyMergeVertex(merged, distance=0.001, constructionHistory=False)
    # belt-and-suspenders: make sure every face's normal agrees with its neighbors before
    # rounding it off, so polySmooth never rounds off a normal that's pointing the wrong way
    cmds.polyNormal(merged, normalMode=2, constructionHistory=False)

    if smooth_divisions > 0:
        merged = cmds.polySmooth(merged, divisions=smooth_divisions, constructionHistory=False)[0]
    cmds.polySoftEdge(merged, angle=180, constructionHistory=False)

    _assign_color(merged, color, "rewardStar_shd")

    group = cmds.group(merged, name=group_name)
    return group


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
_WINDOW_NAME = "sudokuWindow"
_ui = {"cells": {}}
_current_puzzle = {"puzzle": None, "solved": None}
_settings = {"difficulty": "Easy", "use_seed": False, "seed": 1}


def _block_shade(row, col):
    """True for cells in a box that should get the alternate (light gray) shading,
    giving a checkerboard-of-boxes look without needing any spacer/border geometry."""
    return ((row // BOX_SIZE) + (col // BOX_SIZE)) % 2 == 1


def _normal_bg(row, col, given):
    if given:
        return (0.80, 0.82, 0.88)
    return (0.90, 0.90, 0.90) if _block_shade(row, col) else (1.0, 1.0, 1.0)


_rebuild_state = {"in_progress": False}


def _build_ui():
    # guards against the window vanishing with nothing to replace it: a rapid double
    # click firing this twice before the first rebuild finishes could otherwise tear
    # the window down partway through a second, overlapping rebuild
    if _rebuild_state["in_progress"]:
        return
    _rebuild_state["in_progress"] = True

    try:
        # generate the puzzle FIRST, before touching any existing window. If puzzle
        # generation ever raised here, doing it after deleteUI would leave the old
        # window destroyed with nothing built to replace it -- exactly the "GUI just
        # disappears" symptom. Doing the fallible work first means a failure here
        # leaves whatever window was already open untouched.
        puzzle, solved = generate_puzzle(difficulty=_settings["difficulty"],
                                          seed=(_settings["seed"] if _settings["use_seed"] else None))

        if cmds.window(_WINDOW_NAME, exists=True):
            cmds.deleteUI(_WINDOW_NAME)

        # starting the window fresh always means starting a fresh puzzle, and clearing
        # any star left over from a previous game -- habit 2: delete only our exact-named group
        if cmds.objExists(_REWARD_GROUP_NAME):
            cmds.delete(_REWARD_GROUP_NAME)

        _current_puzzle["puzzle"], _current_puzzle["solved"] = puzzle, solved
        _ui["cells"] = {}

        cell_px = 50
        window_w = max(260, GRID_SIZE * cell_px + 40)
        window = cmds.window(_WINDOW_NAME, title="Sudoku", widthHeight=(window_w, 320), sizeable=False)
        main = cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnAttach=("both", 12))

        cmds.text(label=" ")
        cmds.text(label="Sudoku", font="boldLabelFont")
        cmds.text(label="Quick 4x4 puzzle -- fill in 1 to 4, then Check Solution.",
                  font="smallPlainLabelFont", wordWrap=True, align="left")
        cmds.separator(height=8, style="in")

        _ui["difficulty"] = cmds.optionMenu(label="Difficulty", changeCommand=_on_difficulty_changed)
        for level in ["Easy", "Medium", "Hard", "Expert"]:
            cmds.menuItem(label=level, parent=_ui["difficulty"])
        cmds.optionMenu(_ui["difficulty"], edit=True, value=_settings["difficulty"])

        cmds.separator(height=8, style="in")

        cmds.rowColumnLayout(numberOfColumns=GRID_SIZE, columnWidth=[(i + 1, cell_px) for i in range(GRID_SIZE)])
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                given_value = puzzle[row][col]
                is_given = given_value != 0
                field = cmds.textField(
                    text=(str(given_value) if is_given else ""),
                    editable=(not is_given),
                    font="boldLabelFont",
                    backgroundColor=_normal_bg(row, col, is_given),
                    width=cell_px, height=cell_px,
                    changeCommand=lambda val, r=row, c=col: _on_cell_edited(r, c),
                )
                _ui["cells"][(row, col)] = field
        cmds.setParent(main)

        cmds.separator(height=10, style="in")

        cmds.button(label="Check Solution", height=36, backgroundColor=(0.35, 0.55, 0.35), command=_on_check)
        cmds.button(label="New Puzzle", height=28, command=_on_new_puzzle)
        cmds.button(label="Close", height=24, command=lambda *_: cmds.deleteUI(_WINDOW_NAME))

        cmds.showWindow(window)
    except Exception:
        # if something still goes wrong after the old window is already gone, at least
        # make it loud and specific instead of silently vanishing -- paste this traceback
        # back if it happens again and it pinpoints the exact line
        import traceback
        traceback.print_exc()
        cmds.warning("Sudoku window failed to rebuild -- see the error above in the Script "
                     "Editor history, then run the script again to reopen it.")
        raise
    finally:
        _rebuild_state["in_progress"] = False


def _on_difficulty_changed(value):
    _settings["difficulty"] = value


def _on_cell_edited(row, col):
    # handling "an input I didn't plan for": someone can type anything into a text
    # field, not just a valid digit. Anything that isn't a single valid digit gets
    # reduced to its last valid digit, or cleared -- rather than crashing or accepting
    # garbage that would make the checker misbehave.
    field = _ui["cells"][(row, col)]
    value = cmds.textField(field, query=True, text=True)
    if value == "":
        return
    valid_digits = "".join(str(d) for d in range(1, GRID_SIZE + 1))
    cleaned = "".join(ch for ch in value if ch in valid_digits)
    fixed = cleaned[-1] if cleaned else ""
    if fixed != value:
        cmds.textField(field, edit=True, text=fixed)


def _on_check(*_args):
    puzzle = _current_puzzle["puzzle"]
    solved = _current_puzzle["solved"]
    incomplete = False
    all_correct = True

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if puzzle[row][col] != 0:
                continue  # given cells are never wrong -- nothing to check
            field = _ui["cells"][(row, col)]
            text = cmds.textField(field, query=True, text=True)
            if text == "":
                incomplete = True
                cmds.textField(field, edit=True, backgroundColor=_normal_bg(row, col, False))
                continue
            if int(text) == solved[row][col]:
                cmds.textField(field, edit=True, backgroundColor=_normal_bg(row, col, False))
            else:
                all_correct = False
                cmds.textField(field, edit=True, backgroundColor=(0.95, 0.55, 0.55))

    if incomplete:
        cmds.warning("Not finished yet -- fill in every box, then check again.")
    elif all_correct:
        _on_solved()
    else:
        cmds.warning("Not quite -- the boxes highlighted in red are wrong. Keep trying!")


def _on_solved():
    # habit 1: wrap everything the tool builds in a single undo chunk, so one Ctrl+Z
    # undoes the whole star instead of removing it piece by piece
    cmds.undoInfo(openChunk=True)
    try:
        # habit 2: delete only the exact group this tool made before building a new one
        if cmds.objExists(_REWARD_GROUP_NAME):
            cmds.delete(_REWARD_GROUP_NAME)
        build_reward_star()
    finally:
        cmds.undoInfo(closeChunk=True)
    cmds.confirmDialog(title="Solved!", message="Nice work -- you solved it.\nEnjoy your star.",
                        button=["Nice"])


def _on_new_puzzle(*_args):
    # THE likely real cause of the "sometimes the whole GUI disappears" bug: this callback
    # is running *because* a button inside the window called it, so calling _build_ui()
    # directly here asks Maya to delete the very window this callback is still executing
    # inside of, then immediately recreate a new window with the same name in the same
    # breath. That races Maya's own internal teardown of the old window -- sometimes it's
    # finished in time and the rebuild works, sometimes it isn't and the rebuild silently
    # fails, which is exactly the intermittent symptom reported. evalDeferred pushes the
    # rebuild to run after this callback fully returns and Maya is back at its event loop,
    # so the delete-then-recreate happens in a clean state instead of mid-teardown.
    cmds.evalDeferred(_build_ui)


# ---------------------------------------------------------------------------
# Entry point -- graceful fallback when Maya isn't available at all
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if MAYA_AVAILABLE:
        _build_ui()
    else:
        # the "handled an input I didn't plan for" habit: instead of crashing with an
        # ImportError when there's no Maya, prove the puzzle logic works on its own
        print("maya.cmds not available -- the interactive board needs Maya, but here's "
              "a puzzle generated by the same logic, printed to the terminal:\n")
        demo_puzzle, demo_solved = generate_puzzle(difficulty="Easy", seed=1)
        print(_grid_to_text(demo_puzzle))
        print("\nSolution:\n")
        print(_grid_to_text(demo_solved))

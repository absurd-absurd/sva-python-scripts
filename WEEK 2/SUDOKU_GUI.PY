"""
sudoku_gui.py

Maya tool (maya.cmds UI, no PySide needed) that pops up a small, playable
mini-sudoku -- size chosen from a dropdown, 4x4 up to 9x9 -- as a real
interactive grid of text fields -- type the numbers in, check your answer,
and a correct solve builds a puffy, randomly-colored 3D star in the
viewport as a reward.

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

VARIABLE GRID SIZE (4-9) AND WHY 5 AND 7 ARE DIFFERENT
----------------------------------------------------------
A classic sudoku's "box" regions only work cleanly when the grid size
factors into two roughly-equal numbers -- 4 = 2x2 boxes, 6 = 2x3 boxes,
8 = 2x4 boxes, 9 = 3x3 boxes. 5 and 7 are prime: there's no way to split
them into a grid of smaller boxes at all (the only factors are 1 and the
number itself, which just means "the whole row" -- not a real region).
Rather than fake a box constraint that doesn't actually mean anything at
those two sizes, a 5x5 or 7x7 puzzle here is a genuine Latin square
instead: every row and every column still has to contain each number
exactly once, and the puzzle is still carved down to a single unique
solution the same way as any other size -- it just doesn't have the
extra box rule on top. That's an honest tradeoff, documented here rather
than hidden: BOX_SHAPES below is the one place that decision gets made,
and every solver function takes the box shape as a parameter (None
meaning "no boxes") instead of assuming boxes always exist.

WHAT IT HAS TO GET RIGHT
--------------------------
1. The generated puzzle must be a fully valid sudoku (or, at 5x5/7x7, a
   fully valid Latin square) with exactly one solution, at whatever grid
   size is currently selected.
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
3. A small "Sudoku" window opens. Pick a grid size (4-9) and a difficulty
   from the two dropdowns. Given digits are shaded and locked; click an
   empty box and type a number in range.
4. Hit "Check Solution". Wrong cells turn red -- fix and check again.
   A correct solve builds a puffy, randomly-colored 3D star in the
   viewport.
5. "New Puzzle" starts over with a freshly generated one at whatever
   size and difficulty are currently selected.
"""

import math
import random

try:
    import maya.cmds as cmds
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False


_REWARD_GROUP_NAME = "sudokuRewardStar_grp"

GRID_SIZE_OPTIONS = [4, 5, 6, 7, 8, 9]

# box (region) shape -- (box_rows, box_cols) -- for each selectable grid size, chosen to be
# as square as possible for sizes that factor evenly. 5 and 7 are prime and have no such
# factorization, so they're None -- see the module docstring's "VARIABLE GRID SIZE" section.
BOX_SHAPES = {
    4: (2, 2),
    5: None,
    6: (2, 3),
    7: None,
    8: (2, 4),
    9: (3, 3),
}

# fraction of the grid's cells each difficulty leaves filled in -- scales to any grid size
# instead of a fixed clue count. Carving stops early if removing more would break
# uniqueness, so a puzzle may end up with a couple more clues than the target if it has to.
DIFFICULTY_FILL_FRACTION = {
    "Easy": 0.75,
    "Medium": 0.5625,
    "Hard": 0.4375,
    "Expert": 0.375,
}


# ---------------------------------------------------------------------------
# Sudoku solver / generator -- pure Python, no Maya dependency at all.
# Every function here takes grid_size and box_shape explicitly instead of reading a fixed
# module-level constant, so the exact same logic generates anything from a 4x4 up to a 9x9
# puzzle (or a 5x5/7x7 Latin square, where box_shape is None).
# ---------------------------------------------------------------------------
def _is_valid(grid, row, col, value, grid_size, box_shape):
    # a placement is legal only if that value doesn't already appear in the row or column...
    for i in range(grid_size):
        if grid[row][i] == value or grid[i][col] == value:
            return False
    # ...or, at grid sizes that actually have box regions, the box
    if box_shape is not None:
        box_rows, box_cols = box_shape
        box_row, box_col = (row // box_rows) * box_rows, (col // box_cols) * box_cols
        for r in range(box_row, box_row + box_rows):
            for c in range(box_col, box_col + box_cols):
                if grid[r][c] == value:
                    return False
    return True


def _find_best_empty_cell(grid, grid_size, box_shape):
    # picking the empty cell with the FEWEST legal candidates (instead of just the first blank)
    # makes backtracking dramatically faster, since we fail fast on the most constrained cells
    best_cell = None
    best_candidates = None
    for r in range(grid_size):
        for c in range(grid_size):
            if grid[r][c] == 0:
                candidates = [v for v in range(1, grid_size + 1)
                              if _is_valid(grid, r, c, v, grid_size, box_shape)]
                if best_candidates is None or len(candidates) < len(best_candidates):
                    best_cell, best_candidates = (r, c), candidates
                    if len(candidates) == 0:
                        return best_cell, best_candidates  # dead end, bail out early
    return best_cell, best_candidates


def _fill_full_grid(grid, grid_size, box_shape):
    """Recursively fill an empty grid into one complete, valid, randomized solution."""
    cell, candidates = _find_best_empty_cell(grid, grid_size, box_shape)
    if cell is None:
        return True  # no empty cells left -- solved
    row, col = cell
    random.shuffle(candidates)
    for value in candidates:
        grid[row][col] = value
        if _fill_full_grid(grid, grid_size, box_shape):
            return True
        grid[row][col] = 0
    return False


def _count_solutions(grid, grid_size, box_shape, limit=2):
    """Counts solutions up to `limit`, stopping early -- we only need to know if it's exactly 1."""
    cell, candidates = _find_best_empty_cell(grid, grid_size, box_shape)
    if cell is None:
        return 1  # reached a complete, valid grid -- that's one solution
    row, col = cell
    total = 0
    for value in candidates:
        grid[row][col] = value
        total += _count_solutions(grid, grid_size, box_shape, limit - total)
        grid[row][col] = 0
        if total >= limit:
            break  # found enough solutions to know it's not unique -- no need to keep searching
    return total


def _carve_puzzle(solved_grid, grid_size, box_shape, target_clues, seed=None):
    """Remove cells from a solved grid one at a time, only keeping a removal if the
    puzzle still has exactly one solution afterward -- this is what makes it a real
    sudoku instead of just a grid with holes in it."""
    if seed is not None:
        random.seed(seed)

    puzzle = [row[:] for row in solved_grid]
    cells = [(r, c) for r in range(grid_size) for c in range(grid_size)]
    random.shuffle(cells)

    clues_remaining = grid_size * grid_size
    for row, col in cells:
        if clues_remaining <= target_clues:
            break
        removed_value = puzzle[row][col]
        puzzle[row][col] = 0

        # test uniqueness on a scratch copy so we don't disturb the puzzle we're building
        test_grid = [r[:] for r in puzzle]
        if _count_solutions(test_grid, grid_size, box_shape, limit=2) != 1:
            puzzle[row][col] = removed_value  # removing this cell broke uniqueness -- put it back
        else:
            clues_remaining -= 1

    return puzzle


def generate_puzzle(grid_size=4, difficulty="Easy", seed=None):
    """Returns (puzzle, solved) -- both grid_size x grid_size lists of lists, 0 = blank."""
    if grid_size not in BOX_SHAPES:
        raise ValueError("grid_size must be one of %s" % (GRID_SIZE_OPTIONS,))
    box_shape = BOX_SHAPES[grid_size]

    if seed is not None:
        random.seed(seed)

    solved = [[0] * grid_size for _ in range(grid_size)]
    _fill_full_grid(solved, grid_size, box_shape)

    fraction = DIFFICULTY_FILL_FRACTION.get(difficulty, DIFFICULTY_FILL_FRACTION["Easy"])
    target_clues = max(grid_size, round(fraction * grid_size * grid_size))
    puzzle = _carve_puzzle(solved, grid_size, box_shape, target_clues, seed=seed)
    return puzzle, solved


def _grid_to_text(grid, grid_size, box_shape):
    box_rows, box_cols = box_shape if box_shape else (grid_size, grid_size)
    lines = []
    for r in range(grid_size):
        if box_shape and r % box_rows == 0 and r != 0:
            lines.append("-" * (grid_size * 2 + (grid_size // box_cols)))
        row_cells = []
        for c in range(grid_size):
            if box_shape and c % box_cols == 0 and c != 0:
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


_STAR_COLOR_PALETTE = {
    "red":    (0.90, 0.16, 0.16),
    "orange": (1.00, 0.55, 0.10),
    "yellow": (1.00, 0.85, 0.15),
    "green":  (0.25, 0.75, 0.30),
    "blue":   (0.20, 0.45, 0.95),
    "purple": (0.55, 0.25, 0.85),
    "pink":   (0.95, 0.45, 0.70),
}


def _random_star_color():
    """Picks one of exactly the 7 allowed star colors at random -- never anything outside
    that list, and (per the winding fix below) never unlit black regardless of which one."""
    return random.choice(list(_STAR_COLOR_PALETTE.values()))


def _dome_profile(rings_per_hemisphere):
    """Latitude angles (radians, 0 = equator, +-pi/2 = pole) for the rings between the
    equator and each pole, evenly spaced in ANGLE rather than in height. That's what makes
    the silhouette bulge like a rounded dome instead of tapering off in straight lines --
    the same trick as building a sphere from latitude bands."""
    return [(i / float(rings_per_hemisphere + 1)) * (math.pi / 2.0)
            for i in range(1, rings_per_hemisphere + 1)]


def build_reward_star(num_points=5, outer_radius=2.6, inner_radius=1.15, puff_depth=1.8,
                       rings_per_hemisphere=5, smooth_divisions=2,
                       center=(0.0, 3.0, 0.0), color=(1.0, 0.88, 0.45),
                       group_name=_REWARD_GROUP_NAME):
    """Builds a puffy, rounded 5-pointed star -- a star-shaped balloon -- as a single mesh,
    standing upright (its points laid out in the X/Y plane, facing the camera) rather than
    lying flat on the ground.

    This stacks star-outline "slices" from the back of the star through the middle to the
    front, each slice scaled down the closer it is to the front/back tip (following a
    quarter-circle profile, see _dome_profile), so the whole shape is already rounded before
    any smoothing happens. cmds.polySmooth then softens every remaining facet -- including
    the star's point tips -- into the soft, inflated look of a plush toy instead of a
    faceted low-poly star.
    """
    n = num_points * 2
    directions = []
    for i in range(n):
        angle = math.radians(90.0 - i * (360.0 / n))
        base_radius = outer_radius if i % 2 == 0 else inner_radius
        # (dx, dy) instead of (dx, dz): the star's outline lives in the vertical X/Y plane
        # now, so it reads as an upright star from the front instead of a flat shape you'd
        # only recognize looking straight down at it
        directions.append((math.cos(angle) * base_radius, math.sin(angle) * base_radius))

    latitudes = _dome_profile(rings_per_hemisphere)
    # slice stack from the back tip to the front tip: back-half latitudes (most-negative
    # first, so the list already runs back-to-front), the middle, then the front half
    slice_latitudes = [-lat for lat in reversed(latitudes)] + [0.0] + latitudes

    slices = []
    for lat in slice_latitudes:
        radial_scale = math.cos(lat)
        # puffiness now bulges along Z (front-to-back depth) instead of Y (up/down height),
        # so the star's height/width still come from outer_radius/inner_radius as before
        z = center[2] + math.sin(lat) * (puff_depth / 2.0)
        slices.append([(center[0] + dx * radial_scale, center[1] + dy * radial_scale, z)
                       for dx, dy in directions])

    back_tip = (center[0], center[1], center[2] - puff_depth / 2.0)
    front_tip = (center[0], center[1], center[2] + puff_depth / 2.0)

    faces = []

    # back-tip cap -- a fan of triangles closing off the back-most slice to a single point.
    #
    # NOTE on winding: swapping the star's outline from the X/Z plane to the X/Y plane (to
    # make it stand upright) flips handedness for this axis pair, so the winding order that
    # was correct for the old flat-lying star is backwards here -- verified by computing
    # actual face normals (via edge cross products) against the star's own center: every
    # face came out facing inward, which is exactly what renders as flat black under normal
    # lighting no matter what color the material is. Every point list below is reversed
    # from the flat-star version to correct that.
    back_slice = slices[0]
    for i in range(n):
        j = (i + 1) % n
        faces.append(cmds.polyCreateFacet(
            point=[back_tip, back_slice[i], back_slice[j]], constructionHistory=False)[0])

    # side bands between every pair of consecutive slices, moving from back to front
    for slice_index in range(len(slices) - 1):
        lower, upper = slices[slice_index], slices[slice_index + 1]
        for i in range(n):
            j = (i + 1) % n
            faces.append(cmds.polyCreateFacet(
                point=[lower[j], lower[i], upper[i], upper[j]], constructionHistory=False)[0])

    # front-tip cap
    front_slice = slices[-1]
    for i in range(n):
        j = (i + 1) % n
        faces.append(cmds.polyCreateFacet(
            point=[front_tip, front_slice[j], front_slice[i]], constructionHistory=False)[0])

    merged = cmds.polyUnite(faces, constructionHistory=False, name="rewardStar")[0]
    cmds.polyMergeVertex(merged, distance=0.001, constructionHistory=False)
    # belt-and-suspenders: make sure every face's normal agrees with its neighbors before
    # rounding it off, so polySmooth never rounds off a normal that's pointing the wrong way
    cmds.polyNormal(merged, normalMode=2, constructionHistory=False)

    # IMPORTANT: unlike polyUnite/polyCreateFacet, polySmooth does not create a new
    # transform -- it smooths the existing mesh in place and returns its (temporary)
    # history-node name, not the transform. Capturing that into `merged` was the actual
    # bug behind the star showing up uncolored/ungrouped: every step after it -- soft-edging,
    # coloring, grouping -- was silently running on the wrong object, so the real mesh never
    # got its color (looked black/default-gray) and never landed inside the exact-named
    # group the "delete old star" check looks for, so it just piled up uncleaned. `merged`
    # stays the polyUnite transform name the whole way through now.
    if smooth_divisions > 0:
        cmds.polySmooth(merged, divisions=smooth_divisions, constructionHistory=False)
    cmds.polySoftEdge(merged, angle=180, constructionHistory=False)

    _assign_color(merged, color, "rewardStar_shd")

    group = cmds.group(merged, name=group_name)
    return group


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
_WINDOW_NAME = "sudokuWindow"
_ui = {"cells": {}}
_current_puzzle = {"puzzle": None, "solved": None, "grid_size": None, "box_shape": None}
_settings = {"difficulty": "Easy", "grid_size": 4, "use_seed": False, "seed": 1}


def _block_shade(row, col, box_shape):
    """True for cells in a box that should get the alternate (light gray) shading,
    giving a checkerboard-of-boxes look without needing any spacer/border geometry.
    With no box shape (5x5/7x7 Latin squares), there's no box to shade by, so every
    cell just gets the same plain background."""
    if box_shape is None:
        return False
    box_rows, box_cols = box_shape
    return ((row // box_rows) + (col // box_cols)) % 2 == 1


def _normal_bg(row, col, given, box_shape):
    if given:
        return (0.80, 0.82, 0.88)
    return (0.90, 0.90, 0.90) if _block_shade(row, col, box_shape) else (1.0, 1.0, 1.0)


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
        grid_size = _settings["grid_size"]
        puzzle, solved = generate_puzzle(grid_size=grid_size, difficulty=_settings["difficulty"],
                                          seed=(_settings["seed"] if _settings["use_seed"] else None))
        box_shape = BOX_SHAPES[grid_size]

        if cmds.window(_WINDOW_NAME, exists=True):
            cmds.deleteUI(_WINDOW_NAME)

        # starting the window fresh always means starting a fresh puzzle, and clearing
        # any star left over from a previous game -- habit 2: delete only our exact-named group
        if cmds.objExists(_REWARD_GROUP_NAME):
            cmds.delete(_REWARD_GROUP_NAME)

        _current_puzzle["puzzle"], _current_puzzle["solved"] = puzzle, solved
        _current_puzzle["grid_size"], _current_puzzle["box_shape"] = grid_size, box_shape
        _ui["cells"] = {}

        # slightly smaller cells for the bigger grids so a 9x9 window doesn't sprawl
        cell_px = 50 if grid_size <= 6 else 40
        window_w = max(260, grid_size * cell_px + 40)
        window_h = 320 + (grid_size - 4) * (cell_px - 8)
        window = cmds.window(_WINDOW_NAME, title="Sudoku", widthHeight=(window_w, window_h), sizeable=False)
        main = cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnAttach=("both", 12))

        cmds.text(label=" ")
        cmds.text(label="Sudoku", font="boldLabelFont")
        cmds.text(label="%dx%d puzzle -- fill in 1 to %d, then Check Solution." % (grid_size, grid_size, grid_size),
                  font="smallPlainLabelFont", wordWrap=True, align="left")
        cmds.separator(height=8, style="in")

        _ui["difficulty"] = cmds.optionMenu(label="Difficulty", changeCommand=_on_difficulty_changed)
        for level in ["Easy", "Medium", "Hard", "Expert"]:
            cmds.menuItem(label=level, parent=_ui["difficulty"])
        cmds.optionMenu(_ui["difficulty"], edit=True, value=_settings["difficulty"])

        _ui["grid_size"] = cmds.optionMenu(label="Numbers", changeCommand=_on_grid_size_changed)
        for size in GRID_SIZE_OPTIONS:
            cmds.menuItem(label=str(size), parent=_ui["grid_size"])
        cmds.optionMenu(_ui["grid_size"], edit=True, value=str(_settings["grid_size"]))

        cmds.separator(height=8, style="in")

        cmds.rowColumnLayout(numberOfColumns=grid_size, columnWidth=[(i + 1, cell_px) for i in range(grid_size)])
        for row in range(grid_size):
            for col in range(grid_size):
                given_value = puzzle[row][col]
                is_given = given_value != 0
                field = cmds.textField(
                    text=(str(given_value) if is_given else ""),
                    editable=(not is_given),
                    font="boldLabelFont",
                    backgroundColor=_normal_bg(row, col, is_given, box_shape),
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


def _on_grid_size_changed(value):
    _settings["grid_size"] = int(value)


def _on_cell_edited(row, col):
    # handling "an input I didn't plan for": someone can type anything into a text
    # field, not just a valid digit. Anything that isn't a single valid digit gets
    # reduced to its last valid digit, or cleared -- rather than crashing or accepting
    # garbage that would make the checker misbehave. Valid digits depend on the grid size
    # of the puzzle actually on screen right now, not whatever the dropdown currently shows.
    field = _ui["cells"][(row, col)]
    value = cmds.textField(field, query=True, text=True)
    if value == "":
        return
    grid_size = _current_puzzle["grid_size"]
    valid_digits = "".join(str(d) for d in range(1, grid_size + 1))
    cleaned = "".join(ch for ch in value if ch in valid_digits)
    fixed = cleaned[-1] if cleaned else ""
    if fixed != value:
        cmds.textField(field, edit=True, text=fixed)


def _on_check(*_args):
    puzzle = _current_puzzle["puzzle"]
    solved = _current_puzzle["solved"]
    grid_size = _current_puzzle["grid_size"]
    box_shape = _current_puzzle["box_shape"]
    incomplete = False
    all_correct = True

    for row in range(grid_size):
        for col in range(grid_size):
            if puzzle[row][col] != 0:
                continue  # given cells are never wrong -- nothing to check
            field = _ui["cells"][(row, col)]
            text = cmds.textField(field, query=True, text=True)
            if text == "":
                incomplete = True
                cmds.textField(field, edit=True, backgroundColor=_normal_bg(row, col, False, box_shape))
                continue
            if int(text) == solved[row][col]:
                cmds.textField(field, edit=True, backgroundColor=_normal_bg(row, col, False, box_shape))
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
        build_reward_star(color=_random_star_color())
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
        demo_grid_size = 4
        demo_puzzle, demo_solved = generate_puzzle(grid_size=demo_grid_size, difficulty="Easy", seed=1)
        print(_grid_to_text(demo_puzzle, demo_grid_size, BOX_SHAPES[demo_grid_size]))
        print("\nSolution:\n")
        print(_grid_to_text(demo_solved, demo_grid_size, BOX_SHAPES[demo_grid_size]))

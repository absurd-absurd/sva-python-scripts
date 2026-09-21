# Sudoku GUI (Maya Python Tool)

`sudoku_gui.py` is an interactive mini-sudoku you actually play inside Maya. The popup window it opens *is* the game — there's no separate board drawn in the 3D scene. Pick a grid size (4x4 up to 9x9) and a difficulty from the two dropdowns, type numbers into the empty boxes, and hit Check Solution. Wrong entries turn red so you can fix them; a correct solve builds a puffy, randomly-colored 3D star in the viewport as a reward.

## How to run it

1. Open Maya's Script Editor (Windows > General Editors > Script Editor), on a Python tab.
2. Paste the whole `sudoku_gui.py` file in and run it (Ctrl+Enter / Execute All).
3. A "Sudoku" window opens with a puzzle already generated. Given digits are shaded and locked; click an empty box and type a number in range.
4. Hit **Check Solution**. Wrong cells highlight red — fix them and check again. A correct solve pops up a "Solved!" dialog and builds the reward star.
5. **New Puzzle** starts over at whatever grid size and difficulty the dropdowns are currently set to.

## Design problem

A "make a sudoku" tool is trivial if you don't check that the result is an actual sudoku — you could just scatter random digits on a grid. A real one has to satisfy two much harder constraints: every row, column, and box contains each number exactly once, *and* the puzzle (with cells blanked out) has exactly ONE solution, which the tool verifies by actually re-solving it after every cell it removes rather than assuming.

The grid-size dropdown (4–9) adds a wrinkle: a classic sudoku's box regions only work cleanly when the grid size factors into two roughly-equal numbers — 4 as 2x2 boxes, 6 as 2x3, 8 as 2x4, 9 as 3x3. 5 and 7 are prime, so there's no way to split them into real box regions at all. Rather than fake a box rule that wouldn't mean anything at those two sizes, a 5x5 or 7x7 puzzle here is a genuine Latin square instead — every row and column still has exactly one of each number, still carved down to a single unique solution the same rigorous way, just without the extra box constraint. That's a deliberate, documented tradeoff, not a bug.

The tool also went through an earlier design that tried to draw the puzzle directly onto 3D geometry in the scene (first raised "7-segment" digits, then a hand-rendered image texture). Both were fighting the wrong problem — getting Maya to reliably display custom digit shapes turned out far more fragile across machines than the sudoku logic itself ever was. The fix was realizing Maya's own UI widgets already render numbers correctly everywhere, since that's the OS's native font — so the current version doesn't draw a single digit itself. The board is real Maya `textField` cells you type into; the only 3D geometry built is the reward star, which never needs to show text at all.

## How this tool is helpful

- **It's a genuinely playable game, not a demo.** You can hand this to someone with zero context and they can just play it — pick a size, fill in numbers, get a reward. That's a higher bar than most one-off Maya scripts, which usually just print something or move an object once.
- **It teaches the underlying technique, not just the output.** The puzzle-generation approach here — build a full valid solution, then carve cells out one at a time while checking uniqueness by re-solving — is the standard real-world method for generating *any* constraint puzzle with a guaranteed single answer, not just sudoku. The grid-size/box-shape logic is reusable for other Latin-square-style puzzles too.
- **It's a reusable pattern for "solve something, get a 3D reward" tools.** The reward-star logic is decoupled from the puzzle logic on purpose — `build_reward_star()` doesn't know or care that a sudoku triggered it. Swap in a different win condition (a quiz, a matching game, a timed challenge) and the same reward pipeline, undo-safety, and cleanup-by-exact-name habits carry over directly.
- **It shows a low-risk way to build interactive UI in Maya.** Using Maya's own `textField`/`optionMenu` widgets instead of hand-drawn geometry or textures means the interface renders identically on every machine with no font or texture-display dependency — a pattern worth reusing anytime a tool needs to collect structured input from inside Maya rather than the Script Editor's command line.

## What it has to get right

- The generated puzzle must be a fully valid sudoku (or, at 5x5/7x7, a fully valid Latin square) with exactly one solution, at whatever size is currently selected.
- Checking a solve compares against that real, unique answer — not just "looks plausible."
- Wrong entries get highlighted, not just silently rejected, so solving it inside the tool is actually possible.
- It survives running on a machine with no Maya at all: the puzzle logic is plain Python with zero Maya dependency, and the bottom of the file prints a demo puzzle to the terminal instead of crashing if `maya.cmds` can't be imported.

## Habits followed

- **Undo in one step** — building the reward star is wrapped in `cmds.undoInfo(openChunk=True)` / `closeChunk(True)` (with a `try/finally` so the chunk always closes even if something goes wrong mid-build), so one Ctrl+Z undoes the whole star instead of removing it piece by piece.
- **Delete only what the tool made** — the star always lives under one fixed, exact group name (`sudokuRewardStar_grp`). Every cleanup checks `cmds.objExists()` on that exact name before deleting it; nothing is ever deleted by a wildcard pattern that could catch someone else's objects.

## Honest caveat

Like the rest of this project's tools, this depends on `import maya.cmds`, so it doesn't run as a plain `python3 sudoku_gui.py` outside Maya — it has to be pasted into Maya's Script Editor. It does still run *something* useful standalone, though: with no Maya available, it falls back to printing a demo puzzle and its solution straight to the terminal, which is what "handling an input you didn't plan for" meant here — a missing `maya.cmds` is itself treated as an input to handle gracefully, not a crash.

Recording: **[ADD YOUR RECORDING LINK HERE]**

See `env-report.md` for setup details, and `conversation.md` for the working conversation with the agent that built this tool.

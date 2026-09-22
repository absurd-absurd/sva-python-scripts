# Sudoku GUI (Maya Python Tool)

A playable mini-sudoku you actually use inside Maya. This game will run when pasted into the python script editor in Maya. A "Sudoku" window opens with a puzzle already generated. The popup window it opens is the game and there's no separate board drawn in the 3D scene. Pick a grid size (4x4 up to 9x9) and a difficulty level from the two dropdown menus, type numbers into the empty boxes, and hit Check Solution. Wrong entries turn red so you can fix them. When solving the puzzle you we receive a star 3D model as a reward.  


## Design problem

A "make a sudoku" tool is trivial if you don't check that the result is an actual a working sudoku puzzle. A real sudoku puzzle has to satisfy two difficult constraints: each row, column, and box contain a singular correct number, and the empty cells have exactly one solution, which the tool verifies by actually re-solving it after you solved it yourself. This alone requires testing each option of the gui to make it works the way it should.

The grid-size dropdown (4–9) added a problem. When I decided to expand the amount of numbers that could be played in game from only 4 to 4-9 I came across an issue where the screen was not big enough to show the grid and would have to be manually resized each time a new puzzle was generated. After trial and error it was changed to a fixed sized pop up for every size grid and new puzzle generation.

The tool also went through an earlier design that tried to draw the puzzle directly onto 3D geometry in the scene, but in practice that build didn't work and would have not been a clickable, typable, or playable game. 

## How this tool is helpful

-It helps create a fun environment where solving puzzles can and using your brain can give you 3D modeling rewards. It makes the Maya experience more unique. You can hand this to someone with zero context and they can just play it, pick a size, fill in numbers, get a reward. 
-It shows a low-risk way to build interactive UI in Maya.


## Habits followed

- **Undo in one step**: the reward star is wrapped in `cmds.undoInfo(openChunk=True)` / `closeChunk(True)` (with a `try/finally` so the chunk always closes even if something goes wrong mid-build), so one Ctrl+Z undoes the whole star instead of removing it piece by piece.
- **Delete only what the tool made**: the star always lives under one fixed, exact group name (`sudokuRewardStar_grp`). Every cleanup checks `cmds.objExists()` on that exact name before deleting it. Nothing is ever deleted by a wildcard pattern that could catch someone else's objects.


Recording: https://youtu.be/Wuwr2IC6-Wk

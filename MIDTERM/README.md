# Scatter Tool for Maya

A Maya window that takes one or more objects (rocks, trees, props) and
scatters many copies of them across a surface you pick, with random size, spin
and tilt, so you can fill a scene in seconds instead of placing props by hand.
Give each object a weight to say how often it shows up.

![The Scatter Tool window](window.png)

## Which app

- **App:** Autodesk Maya 
- No extra installs. It only uses Maya's own Python 

## How to run it

1. Get the code from the repo.

2. Open Maya.

3. Open the Script Editor (**Windows > General Editors > Script Editor**) and
   click the **Python** tab at the bottom.

4. Paste these lines. Change the `folder` line to wherever your `MIDTERM`
   folder is (use forward slashes):

   ```python
   import maya.cmds as cmds
   folder = "C:/Users/you/sva-python-scripts/MIDTERM"
   cmds.file(folder + "/scatter_test_scene.ma", open=True, force=True)
   exec(open(folder + "/scatter_tool.py").read())
   ```

   The third line opens the test scene, with a hilly `ground` and a small
   `rock` off to the left. `force=True` throws away unsaved changes in the
   scene you had open, so save first if you need to. Leave that line out to
   use your own scene instead. The last line runs the tool. There's no
   separate import step.

5. Run it: press **Ctrl+Enter**, or click the **Execute All** button (the
   double play arrow) at the top of the Script Editor. The **Scatter Tool**
   window opens.

Don't press Ctrl+S in the test scene, or you'll overwrite the repo's copy.

## How to use it

1. Click the `rock` in the viewport, then click **Add selected** under
   **Objects to scatter**. You can select several objects and add them at
   once.
2. Click the `ground`, then click **Use selected** next to **Surface**.
3. Click **Preview**. Copies appear on the ground in a group called
   `scatter_preview`.
4. Move any slider or change any box. When you let go, the preview redraws.
5. Click **New seed** for a different layout with the same settings. The same
   seed number always gives the same layout.
6. Click **Apply** to keep it. The copies go into one group (`scatter_grp1`,
   `scatter_grp2`, ...). One **Ctrl+Z** removes the whole scatter.
7. **Clear** removes the preview. If there's no preview, it removes the last
   scatter you applied.

The line at the bottom of the window says what happened or what's wrong.

### Several objects with weights

Add more than one object to mix them. Each one starts with a weight of 1. To
change it, click its row in the list and type a new **Weight**. The list shows
each object's share, e.g. `rock  weight 3  (75%)` and `bush  weight 1  (25%)`
means about three rocks for every bush. A weight of 0 leaves an object out
without removing it. **Remove** takes the clicked row out of the list.

Changing weights only swaps which object sits on each spot. The spots
themselves stay where they were.

### Presets

The **Preset** menu loads saved slider settings. It starts with two:
"Sparse rocks" and "Dense grass".

- **Save preset** asks for a name and saves the sliders, checkboxes and seed
  under it. Use an existing name to replace that preset.
- **Delete preset** removes the one showing in the menu.

Presets don't save the objects or the surface, since those change from scene
to scene.

### Remembered settings

The window saves your settings every time you change something. Next time you
open it, even after restarting Maya, everything comes back. The objects and
surface come back too, if they're in the scene you have open.

Presets and remembered settings are saved in `scatter_tool.json` in your Maya
user folder (on Windows, `Documents/maya/scatter_tool.json`). Delete that file
to start fresh.

### The controls

| Control | What it does |
| --- | --- |
| Objects to scatter | The objects to copy, each with a weight for how often it shows up |
| Surface | The mesh the copies land on |
| Preset | Load, save or delete saved settings |
| Count | How many copies (1 to 500) |
| Scale min / Scale max | Each copy gets a random size between these |
| Random spin | Random turn around the copy's up direction, 0 to 360 degrees |
| Random tilt | Random lean, 0 to 45 degrees, so copies don't all stand perfectly straight |
| Align to surface | On: copies lean with the slope of the ground. Off: copies stand straight up |
| Use instances | Copies share one mesh, which keeps heavy scenes light (only used by Apply; the preview always uses instances) |
| Max slope | Nothing lands on ground steeper than this angle. 90 means no limit |
| Min height | Nothing lands below this height, e.g. to keep a water's edge clear |
| Seed | Picks the layout. Same seed + same settings = same layout |

### Using your own objects

- The surface must be a polygon mesh.
- Delete the original objects afterwards, or move them away, if you don't want
  them in the scene.

## What works now

- The window, with every control from the pitch.
- Several objects with weights (from the pitch feedback). The status line
  says how many of each were made, e.g. `60 copies (rock 47, bush 13)`.
- Presets saved to a file, with two starters.
- The window remembers your last settings, even after restarting Maya.
- Copies land on the real surface, including hills, and lean with the slope.
  The lean blends between faces, so it stays smooth on low-poly ground.
- Random scale, spin and tilt, repeatable with the seed, and a New seed button.
- Preview, which redraws when you change a control, and isn't added to the
  undo list.
- Apply puts everything in one group, and one Ctrl+Z removes it.
- Clear.
- Use instances.
- Landing rules: max slope and min height (from the pitch feedback).
- Messages instead of errors when nothing is picked, an object can't be
  found, the surface isn't a mesh, the surface is also in the object list, or
  every weight is 0.

Checked in Maya 2026: copies sit within 0.06 units of a smooth hill and lean
within 3 degrees of its slope, and Apply, Ctrl+Z, Preview, New seed, Clear and
the error messages were each run in a real Maya session with the window open.
With weights rock 3 and bush 1, 400 copies came out as 287 rocks and 113
bushes. With one object, the layout is the same as before weights were added,
so old seeds still give the same result.

## What doesn't work yet

- **Copies can overlap.** There's no minimum distance between them yet.
- Preview at 500 copies on a very dense mesh takes a few seconds, so it only
  redraws when you let go of a slider, not while you drag.
- Copies land on whichever side of the mesh they're on. Skip a surface
  with overhangs or caves for now.

## Plan for the rest of the midterm

From the pitch, with the teacher's feedback:

- **By Oct 20:** copies on the real surface, tilt, scale, spin, seed, Preview
  and Clear. Done, plus the slope and height landing rules.
- **By Oct 26:** presets saved to a file, remembered settings, and scattering
  several objects with weights. Done.
- **Stretch goals:** minimum distance between copies, and a painted density
  mask.

## Peer run

_Classmate's name:_ Alfredo (ALF-Mii)

_Their three sentences (what they did, what happened, what confused them or
broke):_

1. "I cloned the repo, opened scatter_test_scene.ma in Maya 2027, imported
   and ran scatter_tool.py from the Script Editor, then set Object to rock and
   Surface to ground with 'Use selected', hit Preview, raised Count to 200,
   and hit New seed, Apply and Clear."
2. "Everything your README promises worked — the window opened, the preview
   drew 50 copies and redrew to 200 when I changed the count, the same seed
   reproduced the same layout and a different seed didn't, one Ctrl+Z removed
   all 200 copies in a single step, 'Use instances' shared one mesh across all
   of them, and the copies sat at most 0.0403 units off the hill and leaned
   0.000° off its slope, both inside the 0.06 / 3° numbers you claimed."
3. "Nothing broke, but the two install steps were my only stumbling block: the
   README asks me to 'paste python import command' and to 'open the test
   scene by pasting the script' without ever showing the actual commands, so I
   had to work out the sys.path.append + import scatter_tool lines and the
   cmds.file(..., open=True) call myself, and it isn't clear whether step 3 is
   still needed once step 5 has me paste the whole script anyway."

_What I'll fix:_ Write the actual commands into the "How to run it" steps (the
line that opens the test scene and the line that runs the tool), and drop the
separate import step, since pasting or opening the whole script already runs
it.

## Recording

(https://youtu.be/2UrF8U327YE)

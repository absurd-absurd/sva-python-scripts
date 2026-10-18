# Scatter Tool for Maya

A Maya window that takes one object (a rock, tree or prop) and scatters many
copies of it across a surface you pick, with random size, spin and tilt, so you
can fill a scene in seconds instead of placing props by hand.

![The Scatter Tool window](window.png)

## Which app

- **App:** Autodesk Maya (built and tested on Maya 2026, Windows 11)
- No extra installs. It only uses Maya's own Python (`maya.cmds`).

## How to run it

1. Get the code. Either:
   - on the GitHub page click **Code > Download ZIP** and unzip it, or
   - `git clone https://github.com/absurd-absurd/sva-python-scripts`

2. Open Maya.

3. Open the test scene: **File > Open Scene**, go into the `MIDTERM` folder and
   pick `scatter_test_scene.ma`. It has a hilly `ground` and a small `rock`
   off to the left. (You can also use your own scene. See "Using your own
   objects" below.)

4. Open the Script Editor: **Windows > General Editors > Script Editor**.

5. In the Script Editor click the **Python** tab at the bottom, then
   **File > Open Script** and pick `MIDTERM/scatter_tool.py`.

6. Run it: press **Ctrl+Enter**, or click the **Execute All** button (the
   double play arrow) at the top of the Script Editor. The **Scatter Tool**
   window opens.

## How to use it

1. Click the `rock` in the viewport, then click **Use selected** next to
   **Object to scatter**.
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

### The controls

| Control | What it does |
| --- | --- |
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
- The point of the object that lands on the ground is its **origin** (where it
  sits when its translate is 0, 0, 0). Model the prop with its base at the
  grid's center, or it will float or sink.
- Delete the original object afterwards, or move it away, if you don't want it
  in the scene.

## What works now

- The window, with every control from the pitch except presets.
- Copies land on the real surface, including hills, and lean with the slope.
  The lean blends between faces, so it stays smooth on low-poly ground.
- Random scale, spin and tilt, repeatable with the seed, and a New seed button.
- Preview, which redraws when you change a control, and isn't added to the
  undo list.
- Apply puts everything in one group, and one Ctrl+Z removes it.
- Clear.
- Use instances.
- Landing rules: max slope and min height (from the pitch feedback).
- Messages instead of errors when nothing is picked, the object can't be
  found, or the surface isn't a mesh.

Checked in Maya 2026: copies sit within 0.06 units of a smooth hill and lean
within 3 degrees of its slope, and Apply, Ctrl+Z, Preview, New seed, Clear and
the error messages were each run in a real Maya session with the window open.

## What doesn't work yet

- **Presets** (save and load "sparse rocks", "dense grass") aren't built.
- The window doesn't **remember your last settings** yet.
- **Only one object** at a time. Scattering several props with weights (60%
  rocks, 30% bushes, 10% logs) is planned next.
- **Copies can overlap.** There's no minimum distance between them yet.
- Preview at 500 copies on a very dense mesh takes a few seconds, so it only
  redraws when you let go of a slider, not while you drag.
- Copies land on whichever side of the mesh they're on. Skip a surface
  with overhangs or caves for now.

## Plan for the rest of the midterm

From the pitch, with the teacher's feedback:

- **By Oct 20 (this step):** copies on the real surface, tilt, scale, spin,
  seed, Preview and Clear. Done, plus the slope and height landing rules.
- **By Oct 26:** presets saved to a file, remembered settings, and scattering
  several objects with weights.
- **Stretch goals:** minimum distance between copies, and a painted density
  mask.

## Peer run

_Classmate's name:_

_Their three sentences (what they did, what happened, what confused them or
broke):_

_What I'll fix:_

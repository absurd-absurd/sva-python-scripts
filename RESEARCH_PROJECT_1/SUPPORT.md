# MARROW — Player support

Help for playing MARROW: how to install it, the controls, what to do if you're stuck, and fixes for common
problems. **MARROW runs on Windows only** (64-bit Windows 10 or 11). There is no Mac or Linux version.

## Contents

- [Install and start](#install-and-start)
- [Controls](#controls)
- [How the game works](#how-the-game-works)
- [Stuck? Hints by area](#stuck-hints-by-area)
- [Problems and fixes](#problems-and-fixes)
- [Report a problem](#report-a-problem)

## Install and start

1. Download **[MARROW_Final_2026-11-22.zip](https://github.com/absurd-absurd/sva-python-scripts/releases/download/marrow-v1.0/MARROW_Final_2026-11-22.zip)** (about 540 MB), also on the
   [Releases page](https://github.com/absurd-absurd/sva-python-scripts/releases/tag/marrow-v1.0).
2. Right-click the zip and choose **Extract All...**, then pick a folder (for example your Desktop). Don't run
   the game from inside the zip: Windows can open a zip like a folder, but the game won't start from there.
3. Open the extracted **`MARROW`** folder and double-click **`RP1_Horror.exe`**.
4. The game opens in a window on the title screen. Press **E** (or click **START**).

**What you need:** 64-bit Windows 10 or 11, a graphics card that supports DirectX 12, about 1 GB of free space
after unzipping, and 8 GB of memory or more. Headphones are recommended; sound is a big part of the game.

## Controls

| Key | What it does |
| --- | --- |
| **W A S D** | Walk |
| **Mouse** | Look around |
| **Shift** (hold) | Run |
| **Space** | Jump |
| **E** | Examine, read, pick up, open doors; close a page you're reading |
| **F** | Flashlight on / off |
| **M** | Open / close the map (once you've found it) |
| **Esc** or **P** | Pause menu (Resume, Controls, Quit) |

On the title screen: **E** Start, **C** Controls, **Q** Quit. You can also click the menu with the mouse.

The game runs in a normal window: drag its edges to resize it, or use the window's minimize, maximize and close
buttons.

## How the game works

- Look at something you can use and a **[E]** prompt appears. Papers open full screen to read; press **E** again
  to put them down.
- The line in the **top-left corner** is what Bug is thinking. It always points you to what to look at next.
- Some doors are **locked** until you find the right key. If a door won't open, the corner line tells you so;
  look around the area you're in for the key.
- Once you have the map, a small map sits in the corner and **M** opens the whole thing. The red arrow is you.
- There is **no save**. A playthrough is short enough for one sitting; quitting starts the game over.
- When the game ends it returns to the title screen.

## Stuck? Hints by area

Open a hint only if you need it. They go in the order you'll reach each place.

<details>
<summary>The parking lot: I don't know where to start</summary>

Look at the ground next to your car. Pick up what's there, then read the corner line.
</details>

<details>
<summary>Room 104: what am I looking for?</summary>

There are three things in the room: something on the bed, the wall over the dresser, and a key. Once you've
looked at all three, the corner line sends you on.
</details>

<details>
<summary>The office: the door is locked</summary>

The key is in Room 104, on the dresser next to the TV.
</details>

<details>
<summary>The office: what now?</summary>

Look at the book on the front desk, then go into the back room: there's a folder on the bed, and a key beside it.
</details>

<details>
<summary>The back gate is locked</summary>

The gate key is in the office's back room, on the bed next to the folder.
</details>

<details>
<summary>The trail: where am I going?</summary>

Follow the red lanterns. Open your map (M): the shack is marked on it, about a third of the way along.
</details>

<details>
<summary>The hunter's shack</summary>

Read the pages on the cot, then look for a key on the crate.
</details>

<details>
<summary>The boathouse is padlocked</summary>

The boathouse key is in the hunter's shack, on the crate.
</details>

<details>
<summary>The boathouse: then what?</summary>

Look by the water door, near the boots. After that, the corner line tells you where to go.
</details>

<details>
<summary>The page at the end of the dock says "Not yet"</summary>

Read the note in the boathouse first (by the boots, near the water door).
</details>

Optional places you can explore off the trail: a rusted car, a lookout tower you can climb, and the cabins by the
lake.

## Problems and fixes

**Windows says "Windows protected your PC" when I open the game.**
The game isn't signed by a publisher, so Windows warns you. Click **More info**, then **Run anyway**.

**Nothing happens, or an error says a file like `VCRUNTIME140.dll` or `MSVCP140.dll` is missing.**
Install Microsoft's **Visual C++ Redistributable (x64)** from Microsoft's website, then start the game again.

**An error mentions DirectX 12 or D3D12.**
Update your graphics card driver (NVIDIA, AMD or Intel). The game needs a DirectX 12 graphics card.

**The game won't start from the zip.**
Extract it first (right-click the zip, **Extract All...**), then run `RP1_Horror.exe` from the extracted folder.

**The window is small.**
Maximize it with the window's maximize button, or drag its edges.

**Keys don't do anything on the title screen.**
Click once inside the game window so it has focus, then press the key again.

**It's too dark to see.**
That's partly on purpose. Turn the flashlight on with **F**, play somewhere dark, or turn up your monitor's
brightness. The game has no brightness setting.

**I can't hear anything.**
Check that MARROW isn't muted in Windows' volume mixer. The opening only has a typing sound; music and ambience
start when you press **E** after the postcard.

**The screen warps and goes strange.**
That's part of the game, not a problem with your computer.

**I'm stuck on the scenery.**
Step back and walk around the object. If you're truly stuck, pause (**Esc** or **P**), quit and start again.

**How do I quit?**
Pause with **Esc** or **P** and choose **QUIT**, press **Q** on the title screen, or close the window.

**Is there a Mac version?**
No. MARROW is Windows only.

## Report a problem

Open an issue on the [GitHub repository](https://github.com/absurd-absurd/sva-python-scripts/issues). Say what
happened, what you were doing, and your Windows version and graphics card.

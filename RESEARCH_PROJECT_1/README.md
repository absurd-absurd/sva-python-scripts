# Research Project 1: A low-poly horror game in Unreal

## The project in one sentence

A short horror game in Unreal Engine 5.5 that looks and feels like a PS2 game, where you play as someone whose best friend went missing a year ago, and you go to the last place she was seen: a run-down roadside motel at the edge of dark woods along a still, black lake.

## The game

You arrive at the motel at night. Her room is still there. You search it and the motel for clues (a room key, torn diary pages, old newspaper clippings, photos), and each one points you farther out: past the motel, down a trail into the woods, to the lakeshore with its rotting dock and boarded-up cabins. You're hoping to find her at the end.

Along the way the woods aren't empty. You keep coming across structures that seem abandoned: a hunting shack with the door hanging open, a rusted car off the trail, a ranger's lookout tower, a boathouse on the water. Someone was here not that long ago. Some of them hold the next clue.

You never see what's out there. You only hear it: a noise in the trees, a dry rattle somewhere in the distance, closer when you stay too long in one place. It's enough to make the hair on your neck stand up and tell you you're not safe.

The look is PS2-era: low-poly models, blurry low-res textures, thick fog, a flashlight that only lights a few feet ahead. The woods are placed with my Maya scatter tool and brought into Unreal by a Python script.

## Why this one

After this project I'll be able to:

- take things I made in Maya into a game engine and script the Unreal editor with Python
- make basic gameplay in Blueprints (picking up clues, reading them, doors that need keys, an ending)
- get a specific art style on purpose: low-poly modeling, and a post-process effect that makes Unreal look like an old console instead of a modern one
- build fear with sound and lighting instead of a monster you can see

## What I'll show

The **game**: a packaged build you can play from the motel to the ending. The **tool**: a Maya export plus an Unreal Python script that rebuilds the scatter in Unreal (same objects, positions, rotations and scale), so I can change the woods in Maya and update them in Unreal.

## The three weeks

- **By Nov 10:** The motel blocked out (parking lot, a row of rooms, her room) and the trail and lakeshore blocked out behind it. Fog, darkness and a flashlight on the player. Low-poly dead trees and rocks modeled in Maya, and the script places them in Unreal in the right spots. I can walk from the motel to the lake.
- **By Nov 17:** Clues work: pick up a key, page, newspaper or photo, read it on screen, and a key opens the next locked door. The woods filled in with the scatter tool, with the trail kept clear. A first version of the PS2 look (low resolution, color banding, wobbly vertices). The dock and cabins at the lake, and the abandoned structures in the woods, each a simple low-poly model with a clue inside.
- **By Nov 23:** The sound that makes it scary: wind, footsteps, the lake lapping, and the noise and rattle in the distance that get closer when you linger. Lighting and fog tuned, a title screen, an ending at the lake, a packaged .exe, this README with how to play, and a recording.

## The smallest version that still counts

The motel and the lakeside woods, dark and foggy, with a flashlight; one abandoned structure on the way; three clues that lead you from her room to the lake; and the rattle in the distance. If the PS2 effect doesn't work, the fog, darkness and sound still carry the mood. If the import script doesn't work, I place the woods by hand and show what went wrong.

## The riskiest part

The PS2 look. Unreal is built to look modern and realistic, so getting the low-res, wobbly, dithered style means writing a post-process material I've never made. Second: the motel, the woods, the structures and the lake are a lot to build in three weeks. I'll keep the motel small (a few rooms you can enter), start with two or three structures in the woods, and add more only if there's time.

## The Maya scenes aren't in the repo

The Maya scene files (`maya/motel_scene.ma`, `maya/lake_scene.ma`, `maya/trail_scene.ma`) are built entirely by the scripts and are too big for GitHub (over 50 MB each), so they aren't committed. To rebuild them, run each script in Maya (or with `mayapy`):

- `maya/make_motel.py` builds the motel, the rooms, the office, the lot and the roadside, and saves `motel_scene.ma`.
- `maya/make_lake.py` builds the lake, the dock, the boathouse and the cabins, and saves `lake_scene.ma`.
- `maya/make_trail.py` builds the gate and fence, the shack, the tower and the overgrowth around the car, and saves `trail_scene.ma`.

Each one also writes the FBX files and the JSON that the Unreal scripts in `unreal/` import.

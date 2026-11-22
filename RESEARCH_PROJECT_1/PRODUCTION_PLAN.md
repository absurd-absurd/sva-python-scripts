# MARROW — Production Plan (snapshot, Nov 22, 2026)

The live, full plan (daily grid, Phase 1 visuals, story drafts, pipeline diagram, bug log) is the Claude Doc
"MARROW — Production Plan": https://claude.ai/artifact/Wytdpd8zj95xS8246fCHSg. This file is its state at the
end of production, for the submission.

## Due dates

| Date | What's due |
| --- | --- |
| Nov 10 | Walkable level, fog, flashlight, Maya woods in Unreal (done early) |
| Nov 17 | Clues and keys work, structures built, PS2 look |
| Nov 23, 11:59 pm | RP1 due: playable .exe, README, recording; RP2 proposal |
| Nov 24 | In-class presentation |

**Must** = needed for Nov 23, **Should** = planned, **Stretch** = only if there's time. A row is Done once it works
in the game.

## Phase 1: Visuals (Nov 3–14)

Done: the Unreal project and first-person player, flashlight (F) with flicker and auto-dim, the Maya → Unreal
pipeline, the PS2 look (dither, grain, fog), the motel (neon sign, six rooms each with its own story, Room 104,
the office), the lot and road, the fence and back gate, the forest (spruces, beeches, dead trees, ferns, leaf
litter), the hunter's shack, the rusted car, the climbable lookout tower, the lake, dock, boathouse, three cabins,
canoe and rowboat, birds and bugs, and the lighting pass (red lanterns, haze). Not done: twig figures along the
trail, a covered bridge (Stretch).

## Phase 2: Gameplay and story (Nov 15–23)

| Day | Task | Area | Priority | Status |
| --- | --- | --- | --- | --- |
| Sun Nov 15 | Write the clue trail: what Cas left, where, what each unlocks | Story | Must | Done |
| Sun Nov 15 | Voice-over in or not (decided: no voice, everything is read on paper) | Story | Must | Done |
| Sun Nov 15 | clues.json: every clue's real text, type, place, what it unlocks | Story | Must | Done |
| Mon Nov 16 | Real clues placed in the motel and every structure | Gameplay | Must | Done |
| Tue Nov 17 | The rattle (the creature growl, made stranger): through the forest, after wrong-hand pages, a growing loop on the dock, the last warp | Audio | Must | Done |
| Tue Nov 17 | Ambience: wind, insects, lake, music (quiet indoors and on the dock) | Audio | Must | Done |
| Tue Nov 17 | Flashlight flickers harder when the creature is close | Gameplay | Must | Not started |
| Wed Nov 18 | Checkpoint: full playthrough motel to lake, every clue works | Testing | Must | Done |
| Wed Nov 18 | Title screen and opening text | UI | Must | Done |
| Wed Nov 18 | Pause menu and controls screen | UI | Must | Done |
| Thu Nov 19 | Opening (typed backstory + postcard, typing sound) | Cutscenes | Must | Done |
| Thu Nov 19 | Sounds: footsteps, pickup, page, door, key, gate | Audio | Must | Done |
| Fri Nov 20 | Ending at the lake: the dock, the last page by the red lantern, "this isn't Cas.", one year later, back to the title (play-tested Nov 22) | Cutscenes | Must | Done |
| Fri Nov 20 | Ending screen (no credits screen, by choice) | UI | Must | Done |
| Sat Nov 21 | Settings: brightness, mouse sensitivity, volume | UI | Should | Not started |
| Sat Nov 21 | Clear the bug log | Testing | Must | In progress |
| Sun Nov 22 | Package the .exe, test it (RP1_Horror_Builds/Final_2026-11-22, a normal resizable window, opens on the title) | Build | Must | Done |
| Sun Nov 22 | README | Build | Must | Not started |
| Mon Nov 23 | Gameplay recording; this plan in the repo; RP2 proposal | Build | Must | In progress |
| Tue Nov 24 | Presentation: one script line by line, the flashlight Blueprint, the axis-swap math | Admin | Must | Not started |
| If time | Footsteps that change per surface (hard ground / forest floor) | Audio | Should | Done |
| If time | Title music | Audio | Should | Done |
| If time | Neon buzz synced to the dead M | Audio | Should | Not started |
| If time | Red lights pulse when the thing is near | Gameplay | Stretch | Not started |

## What changed in the last play-tests (Nov 22)

- The warp builds through the second half: flashes after each wrong-hand page, flashes on and off after the
  boathouse note, fully warped on the dock, two seconds on the last shot.
- The shack's two pages open side by side; the last page lies by the lantern at the end of the dock.
- Cas's boots (Fab leather boots, black, one fallen) by the water door, footprints leading to them.
- Sound: title music, typing in the opening, ambient music, wind, insects, lake, footsteps by surface, paper,
  keys, doors, the metal gate, and the rattle; the dock goes quiet but for the rattle.
- Collision: bugs and birds no longer block you; trees collide with their trunks only.
- Controls: F Flashlight instead of the journal (switched off); title menu keys and clicks fixed.

## Still open in the bug log

- Test games sometimes close themselves a few seconds after Play starts (cause unknown)
- Grey-box car near the office is still a placeholder
- The flashlight "hit" jolt after a cut-out isn't visible in play
- Unreal shows "Unable to check out from revision control" when saving (files still save)

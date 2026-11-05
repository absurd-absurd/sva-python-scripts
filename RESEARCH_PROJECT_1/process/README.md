# Process images

Pictures from along the way, kept for the final presentation.

## 2026-11-05: lighting balance test

![Lighting options](2026-11-05_lighting_options.png)

Four views (payphone, motel front, woods, Room 104), one row per lighting option:

- **Now**: the current lighting (exposure bias 7.3, flashlight 560). Bright flashlight pool, but whatever the beam hits head-on (tree trunk, payphone) goes nearly white.
- **A**: flashlight at about a third, everything else 2.5x brighter.
- **B**: flashlight at about half, everything else 2.5x brighter.
- **C**: like A, everything else 3.5x brighter, lamps a little dimmer.

A, B and C stopped the white burn-out, but the flashlight lost its pool of light on the ground.
**Decision: keep "Now".** The strong beam is part of the look.

Made with a test script that changed every light at once, played the game, jumped the player to each view and took a screenshot.

## 2026-11-05: Room 104 (Cas's room), "frozen in time"

Chosen direction: her things are where she left them a year ago, as if she meant to come back
that night, under a year of damp. Extras: her lake photos taped over the dresser and her camera by
the TV, a twig figure hanging over the bed, a red bulb in the bedside lamp (the red-light theme),
grime (ceiling water stain with a drip streak, peeling wallpaper, cobwebs, yellowed sheets).
Every shot: entering from the door · the photo wall over the dresser · the table by the window · the bed.

### Her photos

![Cas's photos](2026-11-05_cas_photos.png)

Drawn by `tools/make_photos.py` (128 x 96, like cheap disposable-camera prints): lake at dusk,
lake in fog, the dock, the lake at night, and the odd one out, red lights out on the water
(a hint at the lantern ritual).

### First pass

![Room 104 v1](2026-11-05_room104_v1.png)

Layout works, but: the new colors came out near-white (the texture tint replaced the Maya color),
the blanket roll read as pipes, the red lamp light tinted the whole room pink, and the photos were
blank grey cards.

### Second pass

![Room 104 v2](2026-11-05_room104_v2.png)

Photos now have pictures but were mapped sideways (stripes); the suitcase lid and jacket were tilted
on the wrong axis. The flashlight state differed from v1, which showed the real problem: inside a
small room the beam burns everything white (screen mean 200-220 of 255).

### Third pass: flashlight off vs on

![Room 104 v3](2026-11-05_room104_v3_flashlight_off_on.png)

Photos upright, bedspread bunched at the foot, jacket over the chair, suitcase lid leaning back.
Left (flashlight off) shows the dressing itself (mean ~100); right (on) is still burnt out.
**Decision:** the flashlight auto-dims when what it points at is close (like your eyes adjusting),
and stays exactly the same outdoors.

### Flashlight indoors: how strong?

![Indoor flashlight levels](2026-11-05_room104_indoor_flashlight_levels.png)

First try dimmed the beam by distance to what it hits, but the room is 5 m deep, so most walls
were "far" and nothing changed. Now the HUD also checks for a ceiling within 2.5 m above your
eyes: indoors, the beam drops to a set share of its power; outside nothing changes (woods and
motel front measured the same as before). Rows: flashlight off, 35%, 15%, 8% (the 35% bed shot
caught a flicker cut-out). **Picked: 15%**: a soft pool on the wall, photos and table readable.

### Red lamp, new carpet, red kept outside

![Red lamp and carpet](2026-11-05_room104_red_lamp_carpet.png)

Your notes: "change the carpet color", "I don't want the whole room red, just the lamp", and the lamp
looked pink, not like a real light. Causes and fixes:
- **Whole room red:** the big outside lights (sign letters, cross, OPEN, lot lamps, streetlight) cast no
  shadows, so their light went straight through the walls. They now cast shadows, so walls block them.
  That also took the red glow off the motel's front wall (the awning blocked the sign), so six red
  wash lights under the awning (one per room, also shadowed) put it back. The front looks close to before.
- **Pink lamp:** the shade's glow was so strong it bloomed to pinky white. Turned down (3 to 0.6) so
  it reads as red, and the bulb is now a real point light with inverse-square falloff right at the
  lamp: hot at the bulb, fading across the wall and nightstand.
- **Carpet:** from red to a worn khaki brown (all rooms).

### The lamp, still pink → deep red

![Lamp options](2026-11-05_room104_lamp_red_options.png)

Your note: "the lamp color is still pink". Very bright red bleaches toward pink and white on screen,
and it was too bright in two places: the shade's glow, and the bulb light sitting inside the shade
(it burnt a white spot into it and turned the cream wall pink). Tried three dimmer, pure-red versions
(A, B, C, with the bulb moved under the shade). B was the reddest but its shade went dark grey.

![Lamp final](2026-11-05_room104_lamp_deep_red.png)

Final: bulb under the shade, pure red, dim (9); the shade is now red fabric itself (it showed grey in
the flashlight before) with a soft glow (0.5).

## 2026-11-05: "really bad artifacting everywhere"

![Artifacts found](2026-11-05_artifacts_found.png)

Two frames from recording your screen while you played: saw-tooth shadow edges along the awning and
posts, thin bright lines leaking along the window and door frames, and shadow bands that crawled as
you moved. Cause: the shadows turned on for the outside lights earlier today (to stop the sign's red
shining through the walls into the rooms). Point-light shadows at this resolution, with no
anti-aliasing, look like this. (A first guess, turning off motion blur and ambient occlusion, didn't
help and changed the look, so it was undone.)

![Lighting channels fix](2026-11-05_lighting_channels_fix.png)

Fix without any shadows: **lighting channels**. The motel is now two meshes: the outside
(`set_motel`) and the room insides (`set_motel_rooms`, with a thin lining on the inside of the front
wall). The room insides and the room lamps are on channel 1; the sign, cross, lot and street lights
are on channel 0, so they can't reach inside. The flashlight and the moonlight light both. All lights
are back to no shadows, the six extra awning lights are gone, and the motel front looks like it did
originally (top row: the shadowed version; middle/bottom: now, flashlight off/on).

### The real culprit: the flashlight's own shadow

![Flashlight shadows](2026-11-05_flashlight_shadows.png)

Your note: "it did not fix it at all" (worst on the walkway). The lighting-channel change was still
worth keeping, but the artifacts came from the one light that still cast shadows: the flashlight.
It's held off to the right and bobs with every step, so its hard, low-resolution shadow (the dark
band beside the TV and dresser, the patch by the chair, the post and frame edges on the walkway)
jittered and crawled all the time. Rows: now · shadows off · softer, sharper shadows (only blurs it).
**Fix: flashlight casts no shadows.**

### What you actually meant: textures flashing in and out (z-fighting)

![Z-fighting test](2026-11-05_zfighting_test.png)

Your note: "I'm talking about all the textures that keep flashing in and out of the screen."
That's **z-fighting**: two surfaces in (almost) the same place, so the GPU can't tell which is
in front and they flash between each other as you move. Found and fixed:
- **Parking lot:** paint lines, cracks, patches and oil stains were 3-6 mm apart and overlapping.
  Now each kind has its own layer, 8 mm apart (stains 0.8 cm, patches 1.6, cracks 2.4, paint 3.2).
- **Road lines** 4 mm above the road: now 1 cm. **Trail** top 5 mm under the lot: now 1 cm.
- **Motel front:** the room side walls and ceilings were flush with the outside wall. Once the
  room insides got their own lighting this morning, they flashed through as dark/red strips.
  They now stop 1 cm short.
- **Room 104:** photos 1 mm off their borders (now 8 mm), bed stains under the sheet, papers/leaves
  on the table, ceiling stains on the ceiling.
- Also off: occlusion culling (objects popping in late at the screen edge when you turn).

Test: two screenshots 2 cm apart. White = pixels that changed a lot: only outlines moving by a
pixel and the dead "M" (it flickers on purpose). Nothing flashes on the lot or the walls.

### Last flashing: the ground under Room 104 and the lot

![Wobble ground fix](2026-11-05_wobble_ground_fix.png)

Your note: "it worked except in Room 104 I still see flashing of the ground underneath, and sometimes
the parking lot too." Cause: the PS2 vertex wobble snaps vertices to a grid that gets coarser with
distance. The ground is one giant flat piece whose corners are up to 200 m away, and vertices behind
the camera counted as "corner", so they were snapped by up to ~12 cm. That tilted the whole ground a
little, enough to poke up through the carpet (2 cm above it) and the lot (3 cm) now and then.
Fix: the wobble only moves vertices in front of you, by at most half a centimetre. Test: turning in
Room 104 and on the lot, no ground shows through.

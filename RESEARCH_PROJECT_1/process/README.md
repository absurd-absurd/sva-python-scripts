# Process

How MARROW was built and changed along the way, area by area. Each part says what I asked
for, what changed, and what was decided. Every image in this folder is from the work; only
the key ones are shown here (the full day-by-day log is in this file's git history).

**How the work went:** everything is built by scripts (Maya for the models, Python in Unreal
for placing and setting up), so a change means editing a script and rebuilding. After each
round of changes I watched an in-game tour of just the new edits and gave notes.

---

## 1. The look

![Haze options](2026-11-14_haze_options.png)

- **Lighting balance (Nov 5):** tested three brighter/dimmer setups against the original.
  The others stopped the flashlight burning surfaces white, but lost its pool of light.
  **Kept the original**: the strong beam is part of the look.
- **Haze and bloom (Nov 14):** four post-process looks at the same four spots, then the two
  I liked with more contrast. **Picked option B at contrast 1.1**: a wide soft glow round
  every light, light fog, deep blacks.

![More contrast](2026-11-14_haze_contrast.png)

- **Red lights as a theme (Nov 14):** in the story the red lanterns are the town's lake
  ritual. Added red lanterns on posts along the trail (some flicker), a red glow through the
  slits of the boarded cabins, and a flickering lantern at the end of the dock. Floating
  lanterns on the lake were tried and removed.

## 2. Room 104 (Cas's room)

![Room 104](2026-11-05_room104_diary_pillows_curtains.png)

Direction: "frozen in time": her things are where she left them a year ago, under a year of
damp. Built over many rounds of notes:
- An investigation wall: her lake photos, notes ("same night every year", "the rattle stops
  when I stop"), a 1997 newspaper clipping, a map with red pins and string.
- Detailed props (bed, nightstand, dresser, CRT TV, fan), real fabric for the clothes and
  bedding, motel wallpaper and a worn 70s carpet, a window with curtains, her diary.
- A deep-red bedside lamp (bright red kept reading as pink; fixed by dimming it).
- The flashlight burnt the small room white, so it **auto-dims indoors** (picked 15%).

![Her notes](2026-11-05_cas_notes.png)

## 3. Getting rid of flicker

![Z-fighting test](2026-11-05_zfighting_test.png)

"Textures flashing in and out" was **z-fighting**: two surfaces in the same place taking turns
being drawn. Fixed by spacing layers apart (lot markings, road lines, walls, photos), stopping
the PS2 vertex wobble from tilting the ground, and later lining every doorway so the wall's
edge doesn't show. Other causes found on the way: the flashlight's own shadow crawling
(flashlight now casts no shadows) and Unreal's Nanite crushing the motel's thin details
(turned off). The last flicker was found by **recording my screen while I played** and
going through it frame by frame.

![Back-room doorway](2026-11-14_backroom_doorway_books.png)

## 4. Life around the motel

![Crows, owl](2026-11-05_critters_crows_owl_cat.png)

Moths at the lights, fireflies, gnats, bats, flocks and crows that fly off as you get close,
and an owl that watches you. All of it moves in the material (no Blueprints). Bugs were made
smaller and darker, ignore the flashlight, and don't follow you indoors. A black cat went
through four versions (shader walk, Fab model, a full Maya rig) and was **removed**: it never
looked right.

## 5. The motel outside, the lot and the road

![Motel exterior](2026-11-05_exterior_detail.png)

- Detail pass on everything except the sign (which I loved as it was): brick, panelled
  doors, awning, AC units, payphone, dumpster, lamp posts. My Fab classic car replaced the
  Maya one.
- The lot was refitted to the motel and painted as one asphalt surface that runs straight
  into the road; verges, a guardrail and power lines along the road.
- Forest fills every empty space, with hidden walls and **fog** at every unbuilt edge.
- A **ROAD CLOSED** gate and a weathered NO TRESPASSING sign; the fence runs along the road
  so the back gate is the only way into the woods.

![Road closed](2026-11-10_road_closed_and_sign.png)

## 6. The woods

![Forest before](2026-11-09_forest_before.png)
![Forest after](2026-11-09_forest_after.png)

From my reference photos: tall dark trunks with the crowns high up, a mix of living, dying
and dead trees. Real grass blades that sway in the wind and part as you walk through them.
A forest floor of leaves, needles and sticks, and the trail as packed dirt with leaves. A
sightline was logged clear from the lookout tower so you can see the lake.

![Tower view](2026-11-13_tower_view_before_after.png)

## 7. The lake, boathouse and cabins

![The lake](2026-11-05_lake.png)

A real shore, dark water with mist, a low dock you can walk onto, a far rowboat. The
boathouse (padlocked, signs someone was here recently) and three log cabins (two boarded,
one open where Cas slept). Final pass on Nov 14: realistic anchor and chain, bench, toolbox,
lantern, shelves, rope, life ring and net; windows boarded on both sides.

![Boathouse](2026-11-14_boathouse.png)

## 8. The other rooms and the office

![Room 101 before](2026-11-14_room101_before.png)
![Room 101 after](2026-11-14_room101_after.png)

Each room tells a small story: 101 left in a hurry, 102 barricaded then broken into, 103 a
renovation that stopped, 105 water damage, 106 the next guest. The office: "someone just
left" (cigarette still burning, guest register open, 104's key missing from the board).
Reviewed room by room on Nov 14, with two rules for everything:
- **Props must look like the real thing** (armchair, rotary phone, Bible, ladder, duffel...).
- **Nothing may cut into anything else** (checked up close from several angles).

![The office](2026-11-14_office.png)

## 9. On the trail

![Shack](2026-11-14_shack.png)

The hunter's shack (Cas camped here: cot, stove, traps, antlers, woodpile and axe outside),
the rusted car with its tail lights still glowing, and the climbable lookout tower.

## 10. Playing it: the map and the on-screen text

![Cas's map](2026-11-14_cas_map.png)

- **Cas's map:** redrawn to look hand-drawn, following my references (hand-drawn hiking
  maps): black pen on a torn sketchbook page, her notes and arrows. You don't start with it.
  It lies on the ground by your car: the first message is *"There's something on the ground
  by the car. I should see what that is."* Picking it up opens it with *"This is Cas's
  handwriting. It looks like she made a map of this place."* After that, M opens it full
  screen and a torn scrap of it sits in the corner.
- **Messages** are first person, the character talking, in the map's handwriting font.
  Prompts sit on a torn paper scrap instead of a grey box.
- **Movement:** faster running, and the flashlight flickers without jolting the camera.

![Map full and corner](2026-11-14_map_full_and_corner.png)
![Prompt](2026-11-14_prompt_scrap.png)

## 11. Silhouettes (Nov 15)

![Bug, rough](2026-11-15_bug_silhouette_rough.png)

Every person in the game is a silhouette, no faces: Eileen (1997), Cas (2001) and Bug (2002)
each get their own outline. First rough of Bug as a photo-booth frame: short bob, oversized
jacket, headphones round her neck. Then Eileen and Cas to match; I liked the style (flat black on an
aged photo), shapes to refine.

![All three](2026-11-15_silhouettes_three.png)

## 2026-11-16_postcard_back_fonts.png
The back of the postcard that brings Bug to Marrow Falls ("i miss you bug - cas", postmarked
Marrow Falls, Oct 9 2002, 37-cent flag stamp). It is written by the thing wearing Cas, so it uses
the second "wrong" handwriting. Shown in five free erratic handwriting fonts (Google Fonts:
Zeyada, Reenie Beanie, Nothing You Could Do, Rock Salt, Just Me Again Down Here) next to Cas's real
handwriting (Ink Free), to pick the wrong-hand font. Address lines are placeholders.

## 2026-11-17_map_rock_salt_compare.png
Cas's map, before (left, Ink Free) and after (right) switching her handwriting to Rock Salt, so it
contrasts with the thin "wrong" hand (Zeyada). Rock Salt draws much bigger, so make_map.py scales it
to 0.78x and pulls its lines closer; the gate label and lookout note were moved to stop overlaps.

## 2026-11-17_reading_letter_on_paper.png
The reading screen now shows a paper as the real thing (user: "when you pick up the letter to read it,
it should be on a piece of paper"): Cas's letter on Marrow Falls Motel letter paper, in her own
handwriting (Rock Salt, blue-black pen), with Bug's title beside it. Sheets come from tools/make_papers.py
(stationery, notebook, typed, ledger, scrap); each clue picks one with "paper" and its hand with "hand".
Rock Salt's huge built-in line spacing was tightened in a copy of the font (fonts/RockSalt-Tight.ttf).

## 2026-11-17_reading_keys.png
The keys on the reading screen as the real objects (user: "make the keys look real too"): the office key
on a cracked red motel tag, the new gate key on a red tag someone wrote on in marker, and the small
boathouse key on a loop of fishing line lying on a torn piece of Cas's map with the boathouse circled.
Drawn by tools/make_keys.py with the tag words drawn in; those clues use hand "none" so nothing is
written over the picture.

## 2026-11-17_postcard_back.png
The postcard that brings Bug to Marrow Falls, for the opening (tools/make_postcard.py): the motel's
printed side is now just its name (user removed the "Black Hollow Lake - Rooms by the night or week" line).

## 2026-11-17_key_rings_threaded.png
Key rings fixed (user: the keychain didn't look attached): the split ring now goes behind the key's head
and shows through its hole, then through the tag's hole, with a short stretch drawn in front at each
hole so it reads as threaded, not lying on top.

## 2026-11-17_key_rings_v2.png
Second ring fix (user: at the tag's corner the ring looked like it went through the flat plastic): the
ring is now only behind the tag, seen outside it and through its hole; it still passes over the front
of the key's head on one side.

## 2026-11-17_keys_full_v2.png
All three key pictures at full size after the ring fixes (office, gate, boathouse).

## 2026-11-17_keys_full_v3.png
The gate tag is now in a motel worker's felt-tip marker (Permanent Marker), not Cas's handwriting
(user: "the second key should not be the same font as Cas's handwriting").

## 2026-11-17_reading_register.png / 2026-11-17_register_on_counter.png
The guest register as a real page (user: "pages are pages", no text describing it): October 1997,
D. Hollis, the Carvers and Eileen Byrne each in their own handwriting, the next days blank, and
"104 - kept." in pencil in another hand under her name. The book on the office counter now shows the
same page (the old texture still had guests from the first story draft); the facing page is empty.
Both come from tools/make_guest_book.py.

## 2026-11-17_silhouettes_v2.png
Second pass at the three silhouettes (tools/make_silhouettes.py), smooth curves instead of the straight-
edged roughs, same aged-print style. Fixes from the user's notes on the roughs: Eileen's hair is one
shoulder-length mass with the ends flipped out (no "dog ears"); Cas has a real high ponytail falling clear
of her head behind the right shoulder, ears showing, the hood bunched at her neck, open flannel and
backpack straps; Bug has the bob with bangs, a shorter neck, the popped collar and smaller tilted
headphone cups. Waiting for the user's OK before they go on the wall, the photo strip and the posters.

## 2026-11-17_new_clues_reading_preview.png
Preview (drawn outside the game with the same fonts, sizes and line breaks) of the five new clues'
reading screens: the researchers' typed 1974 log, Cas's notebook, the wrong-hand pages nailed in the shack,
the note by her boots and the last page. It caught the typed log and the wrong hand being far too big
(running off the sheet), so their sizes were cut (typed 0.85 -> 0.48, wrong hand 1.35 -> 1.15).

## 2026-11-17_trials_log_preview.png
The researchers' log after the user's edits: Aug 3 now reads "... and failed again", "We don't know why."
is gone from Aug 21, and the coffee stain is a realistic dried ring (uneven darker edge, pale wash inside,
a fainter second ring from setting the mug down again, a drip and splash dots; make_papers.coffee_stain).

## 2026-11-17_silhouettes_v3.png
Third pass, still drawn by hand in code (user: "try without reference photos"): real skull/jaw shapes,
ears for Cas, a sloping neck-to-shoulder line, gaps of background between hair/jaw and collars, loose
strands at hair ends, slight head tilts. Shown to the user for notes.

## 2026-11-17_cas_silhouette_v3.png
Cas redrawn from the user's ponytail reference photo: from the front a high ponytail barely shows on top;
the crown is smooth and lifted, the ears show, and the tail comes into view behind her right side below
the ear and hangs past the jaw to the collarbone, with loose ends. The head now has a round skull dome
(shared by all three silhouettes).

## 2026-11-17_cas_silhouette_hair_down.png
Cas with long hair worn down, parted in the middle, falling past her shoulders (user: the ponytail
versions still looked bad). Bug's silhouette goes back to the original 2026-11-15 rough, which the user
liked more than the redraws.

## 2026-11-17_silhouettes_v4.png
Cas without the hood bunched at her neck, so background shows behind her hair (user); Bug's original
rough with its collar taken off (the popped collar points and the grey triangles by the neck,
tools/make_bug_rough.py COLLAR = False -> process/2026-11-17_bug_silhouette_no_collar.png).

## 2026-11-17_silhouettes_v5.png
Cas's long hair now fills the space behind her neck (user: "I don't want to see Cas's neck, I want that to
be hair"): one mass of hair from her head down past her shoulders.

## 2026-11-17_silhouettes_v6.png
Cas with faint grey lines so her shapes read (user): her face's edge against her hair, the parting, strands
falling down her hair, and her shoulders under it.

## 2026-11-17_silhouettes_v7.png
All three now share the same faint grey face outline so they match (user). Cas's backpack straps and
Eileen's handbag strap and the wispy ends of her hair are gone.

## 2026-11-17_silhouettes_v8.png
Eileen and Cas now use Bug's face outline (just the lower curve of the oval: cheeks, jaw, chin), which the
user liked best; Eileen's coat buttons line up in one column down the middle where the coat closes.

## 2026-11-17_silhouettes_v9.png
Bug's bob redrawn as one smooth closed curve, solid behind her neck with no background showing through
(user: "make Bug's hair better and smoother with no background behind it like the other two").

## 2026-11-17_silhouettes_v10.png
More detail on Bug's jacket in faint seams like the zip (user): the neckline, a zip pull, dropped shoulder
seams, two chest pockets with flaps and snaps, folds near the arms.

## 2026-11-17_silhouettes_v11.png
Cas without the little strands of hair sticking out (user); her hair edge is clean now.

## 2026-11-17_cas_wall_closeup.png
Cas's wall as the reading screen shows it (tools/make_wall.py), and on the Room 104 wall itself: her
notes now in her Rock Salt hand, the lantern note ("why does everyone lie about the red lanterns?"),
Eileen's MISSING poster with her silhouette (replacing the old names list, which had dates after 2002),
and the photo-booth strip of Cas and Bug, pinned and strung on the wallpaper with her lake photos,
the clipping and her lake map.

## 2026-11-17_new_readables_in_game.png
In-game test of the six new readables (each moved onto the Room 104 bed and opened with E): the 1974 log
on its typed file sheet, Cas's notebook, the wrong-hand pages, the note by her boots, the last page, and
Cas's wall close-up. All fit their sheets.

## 2026-11-17_opening.png
The opening in play: black, Bug's opening text typed out in her hand, the postcard ("i miss you bug - cas"
in the wrong hand) under it, [E] Continue; after E the screen fades from black into the parking lot with
her first line at the top.

## 2026-11-17_opening_v2.png
The opening slowed down (user): text types at 15 characters a second, the postcard fades in over 1.8 s,
and the line now ends "On the back, one line..." (no "signed Cas:").

## 2026-11-17_postcard_oregon.png
The postcard now has a made-up Oregon address in the wrong hand (user): bug / 1418 SE Hollins Ave. /
Portland, OR 97214.

## 2026-11-17_final_shot.png
The final shot's camera (unreal/final_shot.py, BP_FinalShot): a year later, the payphone in the motel lot
with Bug's MISSING poster taped to its side (tools/make_photos.py missing_bug: her silhouette, last seen
October 2002, 555-0117). The poster is hidden during the game and only appears in the ending.

## 2026-11-17_ending.png
The ending in play: the last page; on closing it, "this isn't Cas."; cut to black, "One year later.";
the final shot of the payphone with Bug's MISSING poster; cut to black; the game then quits by itself.

## 2026-11-17_keys_in_world.png
The three keys in the world are now their drawings, cut out and laid flat (user: "the keys are still
blocks, they should look exactly like the key image"): the office key on the Room 104 dresser, the gate
key on the office desk, the boathouse key on Cas's lake map in the shack (tools/make_keys.py card(),
unreal/key_cards.py M_PS2_Cutout, place_clues.py).

## 2026-11-17_opening_text_and_torn_page.png / 2026-11-17_boathouse_notes_in_world.png
Opening line now "Marrow Falls Motel on the front" (user). The last page is a small scrap torn from a
notebook page (tools/make_papers.py torn()), on the reading screen and as a ~10 cm cut-out under the lantern;
the note by her boots is also now its torn sheet with the writing on it, not a white block.

## 2026-11-17_papers_in_world.png
The last four papers in the world are now the real things too (cut-outs, tools/make_papers.py world_card,
folder_cover, notebook_cover): Cas's letter on motel stationery on the bed, the researchers' manila folder on
the back-room bed, Cas's red spiral notebook ("C.B.") on the cot, and the wrong-hand page nailed to the shack
wall. The reading "The last page" title is gone (user).

# MARROW: the story (locked 2026-11-15, updated 2026-11-16 from the story workbook)

All clue texts live in `clues.json` (built props in `clues`, not-yet-built props in `new_prop_texts`).

## The thing in the lake
Something huge sleeps under Black Hollow Lake. The rattle is its breathing. It **only takes**:
one person goes in, and *something* comes back out wearing them, for the lake's own gain. It
gives nothing back. The thing that comes back is bait: it brings the next person in.

## The motel
The Marrow Falls Motel was built in the 1970s by researchers who came to study it ("The Trials
of Black Hollow Lake"). Their records are in the office. In 1974 one of them, Freedman, walked
into the water on **October 17**; a boy missing since 1952 came out of the woods, not a day older.
The red lanterns were their way of keeping it quiet; the town still lights them every year and
won't say why. The road is closed.

## Cas
Cassidy "Cas" Byrne. Her mother, **Eileen Byrne** (48, brown hair, brown eyes, 5'6"), vanished
here on **October 17, 1997** (room 104). Cas researched it for years without telling her best
friend (you, "Bug"), found her mom's last-seen location, and came here in **2001**. She read the
researchers' log wrong: she believed "one goes in, one comes back" and that she could get her
mom back. She went missing too.

## Timeline
- **Oct 17, 1974:** Freedman walks into the lake. The 1952 boy comes back out.
- **Oct 17, 1997:** Eileen Byrne checks into room 104 and is never seen again ("104 - kept").
- **Oct 2001:** Cas comes to the motel to find her mother and disappears.
- **Early Oct 2002:** Bug gets a postcard of the Marrow Falls Motel, signed Cas: "i miss you bug" (addressed to "bug, 1418 SE Hollins Ave., Portland, OR 97214": Bug lives in Portland, Oregon; the street is made up)
  It's in the WRONG handwriting (the thing wrote it), but Bug doesn't know that yet.
- **Oct 17, 2002 (the game, the anniversary):** a year later, you (Bug, 21) come looking for Cas.

## The clue trail
1. **Cas's map**, on the ground by your car, in her handwriting.
2. **Room 104**: her unsent letter to her mom on the bed; her wall (readable): a note about the
   red lanterns, Eileen's MISSING poster, the photo-booth strip of Cas and Bug; the office key.
3. **The office**: the guest register (Eileen Byrne, Room 104, "104 - kept"); the researchers'
   field log ("One goes in. Something comes back out.") on the bed in the back room, with the gate
   key beside it (moved off the desk 2026-11-17 so you read the log first).
   The corner prompts: whichever clue you read last in Room 104, the office or the shack points
   you on to the next place (clues.json "areas"); until then they say there's more to find there.
4. **The shack**: Cas's notebook (she misquotes the log: "one comes back"), then later pages in
   **the wrong handwriting** (second font), signed "- cas"; the boathouse key.
5. **The boathouse**: her boots set side by side by the water; a note in the wrong hand:
   "the lanterns are lit for you, bug / don't worry, it won't be much longer now". Bug: "Not much
   longer? The rattling... it's getting louder." This is where the game ends (below).

## The world breaks down
The closer you get to the lake, the more the PS2 look falls apart: textures warp, geometry
stretches, the fog turns red (driven by the Fear value in MPC_Horror).

## Ending
The boathouse, on the lake (decided 2026-11-16: the lake is the big story piece, so the game
ends there, not in a cabin). Past her boots, at the edge of the water door, a lit red lantern
holds down one last page in the wrong handwriting: *"you came, bug / now we can be together."* Bug: *"this isn't Cas."* The
map was bait: Cas drew it for herself in 2001; the thing left it by your car. The lake took her mother, took Cas, and now it has you too. The rattle is right
behind you. Cut to black.

**Final shot:** a year later, a car (driver unseen) pulls into the motel lot at night. On the
payphone, a MISSING poster: yours (Bug's photo-booth silhouette; brunette, 5'4", blue eyes, 21).

## Decided
- Townspeople are never seen, only felt (lanterns, closed road, things just left).
- No recorded voice: everything is read on paper.
- Messages stay first person (Bug talking).
- All people-images are silhouettes.
  Their looks (tools/make_silhouettes.py): Eileen = shoulder-length 90s hair, long wool coat collar up, handbag strap;
  Cas = long hair worn down, parted in the middle (no ponytail, user 2026-11-17), hoodie + open flannel, backpack straps;
  Bug = short bob with bangs, oversized jacket, headphones round her neck (the original 2026-11-15 rough).
- No tagline.
- Cabin 2 stays as is (2026-11-16): an optional side room, Cas's camp (bunk, backpack, stove,
  table with a torn page). Not part of the ending.
- Wrong-hand font = **Zeyada** (fonts/Zeyada.ttf, SIL Open Font License). Cas's own hand = **Rock Salt** (fonts/RockSalt-Regular.ttf, Apache license): bold all-caps scrawl, the opposite of the thin wrong hand. (Was Ink Free until 2026-11-16; map/wall/letter textures and the HUD still use Ink Free until regenerated.)
- Other people's writing is never Cas's or the thing's font: the motel's marker on the gate key tag = Permanent Marker (fonts/, Apache license). The register: D. Hollis = Lucida Handwriting, the Carvers = Bradley Hand, Eileen = Segoe Script, the desk clerk's dates = Segoe Print, "104 - kept." in pencil = Reenie Beanie (fonts/, OFL).
- Ending cuts straight to black. No credits screen.
- Phone numbers are fake 555 numbers (Bug's poster: 555-0117, a nod to Oct 17).

## Continuity checklist (check EVERY new clue piece against this before it goes in)
- **The rule:** the lake only takes. "Something" comes back, never "someone". Only Cas (misreading)
  says "one comes back".
- **Dates:** everything happens on October 17 (1974, 1997, 2002). Cas came in October 2001.
  Nothing in the game is newer than 2002: no cell phones, no internet; payphones, film, tapes.
- **Ages:** Eileen 48 in 1997. Bug 21 in 2002; Cas about the same age.
- **Cas's map** is in HER hand (Rock Salt): she drew it for herself in 2001. The thing only left it
  by Bug's car ("i left bug a map"), it didn't draw it.
- **The postcard** (opening text) is in the wrong handwriting: it's what brought Bug here.
- **Handwriting:** Cas's own notes = normal font, normal capitals. Anything from the thing
  wearing her = second font, all lowercase, cold, calls you "bug", signs "- cas".
- **Names:** Freedman (researcher, 1974), D. Hollis + the Carvers (1997 guests), Eileen Byrne,
  Cassidy "Cas" Byrne, Bug. No other named people unless added here first.
- **Voice:** corner lines are Bug, first person, short, no commands.
- **Props match text:** the visible prop (register pages, tags, wall notes, poster) must show
  the same words as its reading screen.

## Still open

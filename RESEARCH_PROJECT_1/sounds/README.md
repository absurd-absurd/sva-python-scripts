# MARROW sounds

Two kinds of sound go into the game:

- **Made in Python** with `tools/make_sounds.py`, written to `export/sounds/`: wind, lake, drone, rattle, flashlight click and warp sting.
- **Downloaded recordings**, kept in this folder: the sounds that need real recordings.

## Where to download

Use freesound.org. You need a free account to download.
On the search results page, open **Filters** and set **License** to **Creative Commons 0**. CC0 needs no credit, but list the files below anyway.
Download the **.wav** if there is one. Keep each file under about 30 s.

| File name to save as | Search for | What to pick |
|---|---|---|
| `step_asphalt_1..4.wav` | `footsteps asphalt sneakers` | single, slow steps; cut 4 of them out of one clip if needed |
| `step_grass_1..4.wav` | `footsteps grass leaves` or `footsteps forest floor` | soft crunchy steps |
| `step_wood_1..4.wav` | `footsteps wooden floor` or `footsteps dock` | hollow wooden steps (dock, boathouse, motel rooms) |
| `paper_pickup.wav` | `paper pick up` or `paper rustle` | short, about 1 s, one handling of a sheet |
| `paper_putdown.wav` | `paper put down` | short |
| `key_pickup.wav` | `keys pick up jingle` | a small jingle |
| `door_creak.wav` | `door creak old wooden` | slow creak, 1–3 s |
| `door_locked.wav` | `door handle locked rattle` | handle tried, won't open |
| `gate_chain.wav` | `chain gate open` or `padlock chain` | for the back gate |
| `car_arrive.wav` | `car pull up gravel engine off` or `car arrive park engine stop` | for the start: engine, tyres, engine off, door shuts |
| `night_crickets.wav` | `night crickets ambience loop` | quiet, no traffic or voices (optional, for the motel lot) |
| `neon_buzz.wav` | `neon sign buzz hum` | loopable hum for the motel sign (optional) |

You don't need every one. Footsteps, paper, door and car matter most.
Drop the files in this folder and tell me. I'll trim and level them and bring them into Unreal.

## Credits

| Sound | Freesound link | Author | Used for | License |
|---|---|---|---|---|
| hualdk | https://freesound.org/s/879900/ | timkahn | ambient music, whole game | (check on the page) |
| yemxid | https://freesound.org/s/874213/ | timkahn | title screen music | (check on the page) |
| bass synth 98 | https://freesound.org/s/797286/ | cvltiv8r | with the warp | (check on the page) |
| creature deep growl | https://freesound.org/s/435150/ | vykroft | the ending | (check on the page) |
| 2023-10-03 lake shore ambience | https://freesound.org/s/705034/ | mick | the lake shore | (check on the page) |
| strong wind through door crack | https://freesound.org/s/687450/ | zumbidos | wind | (check on the page) |
| chicharras and bugs on the road to Minca | https://freesound.org/s/397824/ | adrienpola | night insects | (check on the page) |
| car turning on and off (interior) | https://freesound.org/s/370897/ | sjturia | the opening | (check on the page) |
| footsteps on grass | https://freesound.org/s/807862/ | designerschoice | footsteps outside | (check on the page) |
| footsteps on wooden floor and carpet | https://freesound.org/s/119913/ | ftpalad | footsteps inside / dock | (check on the page) |
| picking up one paper | https://freesound.org/s/463689/ | usamah | reading a note | (check on the page) |
| door creak | https://freesound.org/s/460542/ | coosemek | doors | (check on the page) |
| jingling keys | https://freesound.org/s/444267/ | karinalarasart | keys | (check on the page) |

The originals are in `sounds/downloads/` (not in git: too big). `python tools/prep_sounds.py` cuts, loops and levels
them into `export/sounds/rec_*.wav`; `unreal/place_sounds.py` imports them into Unreal.

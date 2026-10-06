# Falling Star Catch

A simple pygame game built up from a bare bones WASD-moves-a-ball starter into a full color-matching
catch game. With the sun you dodge the wrong colored stars, catch the right ones, and don't let too many slip past.

## How to run it

From a terminal, inside the project folder:

```
python -m venv .venv
.venv\Scripts\python -m pip install pygame-ce      # Windows
# .venv/bin/python -m pip install pygame-ce         # Mac/Linux

.venv\Scripts\python ball_game.py                   # Windows
# .venv/bin/python ball_game.py                      # Mac/Linux
```

A window opens on a Start screen. Click **Start** to play. Move with **W A S D**. Click the
**?** button in the corner any time during play to pause and bring the instructions back up.

## What I made better

From starting with just a ball that moves around an empty window with WASD, I added:

- Falling stars that spawn at the top and fall toward the bottom
- A goal, your sun has its own color and only creates matches when touched with that same color falling star
- A scoring system, catching a matching star adds points; touching the wrong color subtracts points
- A miss counter and a real lose condition, 5 matching stars reaching the bottom of the screen ends the game
- A Game Over screen showing your final score
- A Start screen with a title, how-to-play instructions, and a Start button
- An in-game help button that re-opens the instructions and pauses the game
- Replaced the plain circles with shaded sun and star shapes that read as glowing 3D objects instead of flat shapes
- A glow around each object that follows its own silhouette, star-shaped glow behind the stars,
  sun-shaped glow behind the sun
- A fixed starry night-sky background

## How it works

Three of the game's functions, in my own words:

**`resolve_candy_touches(x, y, ball_color, candies)`** — checks every falling star against the
sun's current position. If a star is close enough to count as touching and its color matches the
sun's current color, that's a catch (adds to score, and the sun gets a new random color). If it's
touching but the wrong color, that's a penalty hit (subtracts from score). Either way the star
disappears, since it was hit — only a *matching* hit counts as an actual "catch." It hands back
how many of each happened that frame so `main()` can update the score.

**`update_falling_candies(candies, ball_color)`** — moves every star down a little each frame,
then checks which ones fell past the bottom of the window. Only a star that matched the sun's
*current* color counts as a miss, since you were never supposed to catch the wrong-colored ones
anyway — letting those fall through is fine. It returns how many real misses happened so
`main()` can add them to the running miss count and check for game over.

**`draw_star(screen, color, center_x, center_y, radius)`** — draws one falling star, but instead
of a single flat-colored shape, it layers three things: a darkened full-size star underneath, a
mid-tone star shifted slightly toward one corner on top of that, and a small bright highlight
circle further in that same direction. That "light coming from one side" trick is what makes the
star read as a lit, rounded 3D gem instead of a flat cutout.

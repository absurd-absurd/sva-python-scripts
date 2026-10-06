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

**`resolve_candy_touches(x, y, ball_color, candies)`** This means that every star that touches the sun and matches it color will be removed from the screen and a points will be added and wrong color matches will remove points from your score.

**`update_falling_candies(candies, ball_color)`** A line that makes sure the stars continue to fall down the screen throughout the game if not matched to the proper color or if matched with the wrong color.

**`draw_star(screen, color, center_x, center_y, radius)`** This line draws the shape of the falling stars and adds shading and tones so that the stars look 3D eveb though they are not. 

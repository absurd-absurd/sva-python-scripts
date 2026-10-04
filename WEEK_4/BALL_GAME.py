"""
ball_game.py -- a pygame-ce game: move a ball with WASD and catch falling
candies before they reach the bottom.

Run it (inside the venv where pygame-ce is installed):
    python ball_game.py
"""

import math
import random

import pygame

# ---- settings -----------------------------------------------------------
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
BALL_RADIUS = 20
BALL_SPEED = 5          # pixels moved per frame while a key is held
BACKGROUND_COLOR = (30, 30, 30)
TEXT_COLOR = (230, 230, 230)
FPS = 60

FALL_RADIUS = 14
FALL_SPEED = 3                  # pixels per frame a candy falls
FALL_SPAWN_EVERY_MS = 900       # how often a new candy appears
SCORE_PER_CATCH = 10
SCORE_PENALTY_PER_WRONG_HIT = 5
MAX_MISSES = 5          # misses are candies that reach the bottom uncaught

CANDY_COLORS = [
    (255, 80, 80),    # red
    (255, 200, 60),   # yellow
    (80, 220, 120),   # green
    (120, 160, 255),  # blue
    (220, 100, 230),  # purple
]
COLOR_NAMES = {
    (255, 80, 80): "red",
    (255, 200, 60): "yellow",
    (80, 220, 120): "green",
    (120, 160, 255): "blue",
    (220, 100, 230): "purple",
}

SPAWN_EVENT = pygame.USEREVENT + 1


def handle_input(keys, x, y):
    """Read which keys are currently held and return the ball's new (x, y)."""
    if keys[pygame.K_w]:
        y -= BALL_SPEED
    if keys[pygame.K_s]:
        y += BALL_SPEED
    if keys[pygame.K_a]:
        x -= BALL_SPEED
    if keys[pygame.K_d]:
        x += BALL_SPEED
    return x, y


def clamp_to_window(x, y):
    """Keep the ball fully inside the window instead of letting it wander off."""
    x = max(BALL_RADIUS, min(WINDOW_WIDTH - BALL_RADIUS, x))
    y = max(BALL_RADIUS, min(WINDOW_HEIGHT - BALL_RADIUS, y))
    return x, y


def spawn_falling_candy(candies):
    """Add one new candy at a random x position just above the top edge."""
    x = random.randint(FALL_RADIUS, WINDOW_WIDTH - FALL_RADIUS)
    color = random.choice(CANDY_COLORS)
    candies.append({"x": x, "y": -FALL_RADIUS, "color": color})


def update_falling_candies(candies, ball_color):
    """Move every candy down one step, and drop any that passed the bottom.

    Only a candy that MATCHES the ball's current color counts as a miss --
    you were never supposed to catch the wrong-colored ones anyway, so
    letting those fall off the bottom doesn't count against you. Misses
    are the only thing that end the game.
    """
    for candy in candies:
        candy["y"] += FALL_SPEED
    passed_bottom = [c for c in candies if c["y"] - FALL_RADIUS > WINDOW_HEIGHT]
    candies[:] = [c for c in candies if c["y"] - FALL_RADIUS <= WINDOW_HEIGHT]
    return sum(1 for c in passed_bottom if c["color"] == ball_color)


def pick_new_ball_color(current_color):
    """Pick a random candy color that's different from the current one."""
    choices = [c for c in CANDY_COLORS if c != current_color]
    return random.choice(choices)


def resolve_candy_touches(x, y, ball_color, candies):
    """Remove any candy touching the ball, and score the touch.

    A matching-color touch is a catch (+score). A wrong-color touch is a
    penalty (-score) -- but note it does NOT count as a miss, since the
    candy never reached the bottom; only misses can end the game.
    Returns (caught, wrong_hits) for this frame.
    """
    catch_radius = BALL_RADIUS + FALL_RADIUS
    still_falling = []
    caught = 0
    wrong_hits = 0
    for candy in candies:
        distance = math.hypot(candy["x"] - x, candy["y"] - y)
        if distance <= catch_radius:
            if candy["color"] == ball_color:
                caught += 1
            else:
                wrong_hits += 1
        else:
            still_falling.append(candy)
    candies[:] = still_falling
    return caught, wrong_hits


def draw(screen, font, x, y, ball_color, candies, score, misses):
    """Draw one frame: clear the screen, the candies, the ball, then the HUD text."""
    screen.fill(BACKGROUND_COLOR)
    for candy in candies:
        pygame.draw.circle(screen, candy["color"], (candy["x"], int(candy["y"])), FALL_RADIUS)
    pygame.draw.circle(screen, ball_color, (int(x), int(y)), BALL_RADIUS)

    color_label = font.render(f"Your color: {COLOR_NAMES[ball_color]}", True, TEXT_COLOR)
    screen.blit(color_label, (10, 10))

    score_label = font.render(f"Score: {score}", True, TEXT_COLOR)
    screen.blit(score_label, (WINDOW_WIDTH - score_label.get_width() - 10, 10))

    misses_label = font.render(f"Missed: {misses}/{MAX_MISSES}", True, TEXT_COLOR)
    screen.blit(misses_label, (10, 40))

    pygame.display.flip()


def draw_game_over(screen, font, score):
    """Draw the end-of-game screen with the final score."""
    screen.fill(BACKGROUND_COLOR)

    title = font.render("Game Over", True, TEXT_COLOR)
    screen.blit(title, (WINDOW_WIDTH / 2 - title.get_width() / 2, WINDOW_HEIGHT / 2 - 40))

    final_score = font.render(f"Final score: {score}", True, TEXT_COLOR)
    screen.blit(final_score, (WINDOW_WIDTH / 2 - final_score.get_width() / 2, WINDOW_HEIGHT / 2))

    hint = font.render("Close the window to quit", True, TEXT_COLOR)
    screen.blit(hint, (WINDOW_WIDTH / 2 - hint.get_width() / 2, WINDOW_HEIGHT / 2 + 40))

    pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("WASD Candy Catch")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)

    x, y = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
    ball_color = random.choice(CANDY_COLORS)
    candies = []
    score = 0
    misses = 0
    game_over = False

    pygame.time.set_timer(SPAWN_EVENT, FALL_SPAWN_EVERY_MS)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == SPAWN_EVENT and not game_over:
                spawn_falling_candy(candies)

        if game_over:
            draw_game_over(screen, font, score)
            clock.tick(FPS)
            continue

        keys = pygame.key.get_pressed()
        x, y = handle_input(keys, x, y)
        x, y = clamp_to_window(x, y)

        misses += update_falling_candies(candies, ball_color)
        caught, wrong_hits = resolve_candy_touches(x, y, ball_color, candies)
        score += caught * SCORE_PER_CATCH
        score -= wrong_hits * SCORE_PENALTY_PER_WRONG_HIT
        if caught:
            ball_color = pick_new_ball_color(ball_color)

        if misses >= MAX_MISSES:
            game_over = True

        draw(screen, font, x, y, ball_color, candies, score, misses)
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()

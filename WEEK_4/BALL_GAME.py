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

BUTTON_WIDTH = 160
BUTTON_HEIGHT = 50
BUTTON_COLOR = (80, 220, 120)
BUTTON_TEXT_COLOR = (20, 20, 20)

HELP_BUTTON_SIZE = 36
HELP_BUTTON_COLOR = (90, 90, 90)

INSTRUCTIONS = [
    "Move your sun with W A S D.",
    "Catch falling stars that match your sun's color to score.",
    "The ball changes to a new color each time you catch one.",
    "Touching the WRONG color costs you points so try to dodge those.",
    f"If {MAX_MISSES} matching falling stars hit the bottom it's game over.",
]

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


def draw_help_button(screen, font, help_button):
    """Draw the small '?' button in the corner that reopens the instructions."""
    pygame.draw.circle(screen, HELP_BUTTON_COLOR, help_button.center, HELP_BUTTON_SIZE // 2)
    label = font.render("?", True, TEXT_COLOR)
    screen.blit(label, (help_button.centerx - label.get_width() / 2,
                         help_button.centery - label.get_height() / 2))


def draw(screen, font, x, y, ball_color, candies, score, misses, help_button):
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

    draw_help_button(screen, font, help_button)


def draw_help_overlay(screen, font, title_font):
    """Draw a semi-transparent overlay repeating the how-to-play instructions."""
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    title = title_font.render("How to Play", True, TEXT_COLOR)
    screen.blit(title, (WINDOW_WIDTH / 2 - title.get_width() / 2, 60))

    line_y = 130
    for line in INSTRUCTIONS:
        text = font.render(line, True, TEXT_COLOR)
        screen.blit(text, (WINDOW_WIDTH / 2 - text.get_width() / 2, line_y))
        line_y += 28

    hint = font.render("Click the ? button again to close", True, TEXT_COLOR)
    screen.blit(hint, (WINDOW_WIDTH / 2 - hint.get_width() / 2, line_y + 20))


def draw_start_screen(screen, title_font, font, start_button):
    """Draw the title, how-to-play instructions, and the Start button."""
    screen.fill(BACKGROUND_COLOR)

    title = title_font.render("WASD Candy Catch", True, TEXT_COLOR)
    screen.blit(title, (WINDOW_WIDTH / 2 - title.get_width() / 2, 40))

    line_y = 110
    for line in INSTRUCTIONS:
        text = font.render(line, True, TEXT_COLOR)
        screen.blit(text, (WINDOW_WIDTH / 2 - text.get_width() / 2, line_y))
        line_y += 28

    pygame.draw.rect(screen, BUTTON_COLOR, start_button, border_radius=8)
    label = font.render("Start", True, BUTTON_TEXT_COLOR)
    screen.blit(label, (start_button.centerx - label.get_width() / 2,
                         start_button.centery - label.get_height() / 2))


def draw_game_over(screen, font, score):
    """Draw the end-of-game screen with the final score."""
    screen.fill(BACKGROUND_COLOR)

    title = font.render("Game Over", True, TEXT_COLOR)
    screen.blit(title, (WINDOW_WIDTH / 2 - title.get_width() / 2, WINDOW_HEIGHT / 2 - 40))

    final_score = font.render(f"Final score: {score}", True, TEXT_COLOR)
    screen.blit(final_score, (WINDOW_WIDTH / 2 - final_score.get_width() / 2, WINDOW_HEIGHT / 2))

    hint = font.render("Close the window to quit", True, TEXT_COLOR)
    screen.blit(hint, (WINDOW_WIDTH / 2 - hint.get_width() / 2, WINDOW_HEIGHT / 2 + 40))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("WASD Candy Catch")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)
    title_font = pygame.font.SysFont(None, 44)

    start_button = pygame.Rect(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT)
    start_button.center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT - 70)

    help_button = pygame.Rect(0, 0, HELP_BUTTON_SIZE, HELP_BUTTON_SIZE)
    help_button.center = (WINDOW_WIDTH - 30, WINDOW_HEIGHT - 30)

    x, y = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
    ball_color = random.choice(CANDY_COLORS)
    candies = []
    score = 0
    misses = 0
    state = "start"   # one of: "start", "playing", "game_over"
    show_help = False  # when True, gameplay is paused and instructions show again

    pygame.time.set_timer(SPAWN_EVENT, FALL_SPAWN_EVERY_MS)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == SPAWN_EVENT and state == "playing" and not show_help:
                spawn_falling_candy(candies)
            elif event.type == pygame.MOUSEBUTTONDOWN and state == "start":
                if start_button.collidepoint(event.pos):
                    state = "playing"
            elif event.type == pygame.MOUSEBUTTONDOWN and state == "playing":
                if help_button.collidepoint(event.pos):
                    show_help = not show_help

        if state == "start":
            draw_start_screen(screen, title_font, font, start_button)
            pygame.display.flip()
            clock.tick(FPS)
            continue

        if state == "game_over":
            draw_game_over(screen, font, score)
            pygame.display.flip()
            clock.tick(FPS)
            continue

        # state == "playing" from here on
        if not show_help:
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
                state = "game_over"

        draw(screen, font, x, y, ball_color, candies, score, misses, help_button)
        if show_help:
            draw_help_overlay(screen, font, title_font)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()

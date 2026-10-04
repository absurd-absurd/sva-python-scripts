"""
ball_game.py -- a pygame-ce game: move a ball with WASD and catch falling
candies before they reach the bottom.

Run it (inside the venv where pygame-ce is installed):
    python ball_game.py
"""

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
BALL_COLOR_CHANGE_EVERY_MS = 4000  # how often the ball's own color changes

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
COLOR_CHANGE_EVENT = pygame.USEREVENT + 2


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


def update_falling_candies(candies):
    """Move every candy down one step, and drop any that passed the bottom."""
    for candy in candies:
        candy["y"] += FALL_SPEED
    candies[:] = [c for c in candies if c["y"] - FALL_RADIUS <= WINDOW_HEIGHT]


def draw(screen, font, x, y, ball_color, candies):
    """Draw one frame: clear the screen, the candies, the ball, then the HUD text."""
    screen.fill(BACKGROUND_COLOR)
    for candy in candies:
        pygame.draw.circle(screen, candy["color"], (candy["x"], int(candy["y"])), FALL_RADIUS)
    pygame.draw.circle(screen, ball_color, (int(x), int(y)), BALL_RADIUS)

    label = font.render(f"Your color: {COLOR_NAMES[ball_color]}", True, TEXT_COLOR)
    screen.blit(label, (10, 10))

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

    pygame.time.set_timer(SPAWN_EVENT, FALL_SPAWN_EVERY_MS)
    pygame.time.set_timer(COLOR_CHANGE_EVENT, BALL_COLOR_CHANGE_EVERY_MS)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == SPAWN_EVENT:
                spawn_falling_candy(candies)
            elif event.type == COLOR_CHANGE_EVENT:
                ball_color = random.choice(CANDY_COLORS)

        keys = pygame.key.get_pressed()
        x, y = handle_input(keys, x, y)
        x, y = clamp_to_window(x, y)

        update_falling_candies(candies)

        draw(screen, font, x, y, ball_color, candies)
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()

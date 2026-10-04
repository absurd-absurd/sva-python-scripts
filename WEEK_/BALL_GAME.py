"""
ball_game.py -- a minimal pygame-ce game: a ball you move with WASD.

Run it (inside the venv where pygame-ce is installed):
    python ball_game.py
"""

import pygame

# ---- settings -----------------------------------------------------------
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
BALL_RADIUS = 20
BALL_SPEED = 5          # pixels moved per frame while a key is held
BACKGROUND_COLOR = (30, 30, 30)
BALL_COLOR = (70, 160, 255)
FPS = 60


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


def draw(screen, x, y):
    """Draw one frame: clear the screen, then draw the ball."""
    screen.fill(BACKGROUND_COLOR)
    pygame.draw.circle(screen, BALL_COLOR, (int(x), int(y)), BALL_RADIUS)
    pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("WASD Ball")
    clock = pygame.time.Clock()

    x, y = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        x, y = handle_input(keys, x, y)
        x, y = clamp_to_window(x, y)

        draw(screen, x, y)
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()

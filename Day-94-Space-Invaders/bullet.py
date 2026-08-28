import pygame


class Bullet:
    def __init__(
        self,
        x,
        y,
        speed=-8,
        color=(255, 230, 80)
    ):
        self.width = 5
        self.height = 14

        self.x = x
        self.y = y

        self.speed = speed

        self.color = color

        self.rect = pygame.Rect(
            x,
            y,
            self.width,
            self.height
        )

    def update(self):
        self.y += self.speed
        self.rect.y = self.y

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            self.color,
            self.rect,
            border_radius=2
        )

    def is_off_screen(self, screen_height):
        return (
            self.rect.bottom < 0
            or self.rect.top > screen_height
        )
import pygame


class Player:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.width = 55
        self.height = 35

        self.x = (
            screen_width - self.width
        ) // 2

        self.y = (
            screen_height - 75
        )

        self.speed = 6

        self.color = (80, 220, 120)

        self.rect = pygame.Rect(
            self.x,
            self.y,
            self.width,
            self.height
        )

        self.lives = 3

    def move(self, direction):
        self.x += direction * self.speed

        if self.x < 0:
            self.x = 0

        if self.x + self.width > self.screen_width:
            self.x = (
                self.screen_width - self.width
            )

        self.rect.x = self.x

    def draw(self, screen):
        # Main ship
        pygame.draw.polygon(
            screen,
            self.color,
            [
                (self.x + self.width // 2, self.y),
                (self.x, self.y + self.height),
                (
                    self.x + self.width,
                    self.y + self.height
                )
            ]
        )

        # Ship center
        pygame.draw.rect(
            screen,
            (180, 255, 200),
            (
                self.x + 20,
                self.y + 15,
                15,
                15
            )
        )

    def reset_position(self):
        self.x = (
            self.screen_width - self.width
        ) // 2

        self.y = (
            self.screen_height - 75
        )

        self.rect.x = self.x
        self.rect.y = self.y
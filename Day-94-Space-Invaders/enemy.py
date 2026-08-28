import pygame


class Enemy:
    def __init__(
        self,
        x,
        y,
        width=45,
        height=30
    ):
        self.x = x
        self.y = y

        self.width = width
        self.height = height

        self.rect = pygame.Rect(
            x,
            y,
            width,
            height
        )

        self.color = (230, 80, 100)

        self.speed = 1

    def move(self, direction):
        self.x += direction * self.speed

        self.rect.x = self.x

    def move_down(self, amount=20):
        self.y += amount
        self.rect.y = self.y

    def draw(self, screen):
        # Body
        pygame.draw.rect(
            screen,
            self.color,
            self.rect,
            border_radius=5
        )

        # Eyes
        eye_size = 6

        pygame.draw.rect(
            screen,
            (255, 255, 255),
            (
                self.x + 9,
                self.y + 8,
                eye_size,
                eye_size
            )
        )

        pygame.draw.rect(
            screen,
            (255, 255, 255),
            (
                self.x + 30,
                self.y + 8,
                eye_size,
                eye_size
            )
        )

        # Feet
        pygame.draw.rect(
            screen,
            self.color,
            (
                self.x + 5,
                self.y + self.height - 2,
                10,
                7
            )
        )

        pygame.draw.rect(
            screen,
            self.color,
            (
                self.x + 30,
                self.y + self.height - 2,
                10,
                7
            )
        )
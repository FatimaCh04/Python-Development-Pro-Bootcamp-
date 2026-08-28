import pygame
import random

from player import Player
from enemy import Enemy
from bullet import Bullet


class Game:

    WIDTH = 900
    HEIGHT = 650

    FPS = 60

    def __init__(self):
        pygame.init()

        pygame.display.set_caption(
            "Space Invaders — Day 94"
        )

        self.screen = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT)
        )

        self.clock = pygame.time.Clock()

        self.running = True

        self.game_over = False

        self.paused = False

        self.score = 0

        self.level = 1

        self.enemy_direction = 1

        self.enemy_move_timer = 0

        self.enemy_move_delay = 30

        self.player = Player(
            self.WIDTH,
            self.HEIGHT
        )

        self.bullets = []

        self.enemy_bullets = []

        self.enemies = []

        self.create_enemies()

        self.font = pygame.font.Font(
            None,
            32
        )

        self.large_font = pygame.font.Font(
            None,
            65
        )

        self.small_font = pygame.font.Font(
            None,
            24
        )

    # --------------------------------------------------
    # ENEMY CREATION
    # --------------------------------------------------

    def create_enemies(self):

        self.enemies.clear()

        rows = min(
            3 + self.level // 2,
            6
        )

        columns = 10

        enemy_width = 45
        enemy_height = 30

        horizontal_gap = 28
        vertical_gap = 25

        total_width = (
            columns * enemy_width
            + (columns - 1) * horizontal_gap
        )

        start_x = (
            self.WIDTH - total_width
        ) // 2

        start_y = 80

        for row in range(rows):

            for column in range(columns):

                x = (
                    start_x
                    + column
                    * (
                        enemy_width
                        + horizontal_gap
                    )
                )

                y = (
                    start_y
                    + row
                    * (
                        enemy_height
                        + vertical_gap
                    )
                )

                enemy = Enemy(
                    x,
                    y,
                    enemy_width,
                    enemy_height
                )

                enemy.speed = (
                    1 + self.level * 0.15
                )

                self.enemies.append(enemy)

    # --------------------------------------------------
    # EVENT HANDLING
    # --------------------------------------------------

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_p:
                    self.paused = not self.paused

                if (
                    event.key == pygame.K_r
                    and self.game_over
                ):
                    self.restart()

                if (
                    event.key == pygame.K_SPACE
                    and not self.game_over
                    and not self.paused
                ):
                    self.shoot()

    # --------------------------------------------------
    # PLAYER SHOOTING
    # --------------------------------------------------

    def shoot(self):

        # Prevent too many bullets
        if len(self.bullets) >= 4:
            return

        bullet_x = (
            self.player.x
            + self.player.width // 2
            - 2
        )

        bullet_y = self.player.y - 12

        bullet = Bullet(
            bullet_x,
            bullet_y
        )

        self.bullets.append(bullet)

    # --------------------------------------------------
    # ENEMY SHOOTING
    # --------------------------------------------------

    def enemy_shoot(self):

        if not self.enemies:
            return

        if random.random() > 0.015:
            return

        # Select enemies from bottom row
        shooters = []

        for enemy in self.enemies:

            blocked = False

            for other in self.enemies:

                if (
                    other.y > enemy.y
                    and abs(
                        other.x - enemy.x
                    ) < 25
                ):
                    blocked = True
                    break

            if not blocked:
                shooters.append(enemy)

        if not shooters:
            return

        enemy = random.choice(
            shooters
        )

        bullet_x = (
            enemy.x
            + enemy.width // 2
            - 2
        )

        bullet_y = (
            enemy.y
            + enemy.height
        )

        bullet = Bullet(
            bullet_x,
            bullet_y,
            speed=5,
            color=(255, 100, 120)
        )

        self.enemy_bullets.append(
            bullet
        )

    # --------------------------------------------------
    # UPDATE PLAYER
    # --------------------------------------------------

    def update_player(self):

        keys = pygame.key.get_pressed()

        direction = 0

        if keys[pygame.K_LEFT]:
            direction -= 1

        if keys[pygame.K_RIGHT]:
            direction += 1

        self.player.move(direction)

    # --------------------------------------------------
    # UPDATE BULLETS
    # --------------------------------------------------

    def update_bullets(self):

        for bullet in self.bullets[:]:

            bullet.update()

            if bullet.is_off_screen(
                self.HEIGHT
            ):
                self.bullets.remove(
                    bullet
                )

    def update_enemy_bullets(self):

        for bullet in self.enemy_bullets[:]:

            bullet.update()

            if bullet.is_off_screen(
                self.HEIGHT
            ):
                self.enemy_bullets.remove(
                    bullet
                )

    # --------------------------------------------------
    # UPDATE ENEMIES
    # --------------------------------------------------

    def update_enemies(self):

        if not self.enemies:
            return

        self.enemy_move_timer += 1

        if (
            self.enemy_move_timer
            < self.enemy_move_delay
        ):
            return

        self.enemy_move_timer = 0

        hit_edge = False

        for enemy in self.enemies:

            next_x = (
                enemy.x
                + self.enemy_direction
                * enemy.speed
                * 10
            )

            if (
                next_x <= 10
                or
                next_x + enemy.width
                >= self.WIDTH - 10
            ):
                hit_edge = True
                break

        if hit_edge:

            self.enemy_direction *= -1

            for enemy in self.enemies:
                enemy.move_down(20)

        else:

            for enemy in self.enemies:
                enemy.move(
                    self.enemy_direction
                )

    # --------------------------------------------------
    # COLLISIONS
    # --------------------------------------------------

    def check_bullet_collisions(self):

        for bullet in self.bullets[:]:

            for enemy in self.enemies[:]:

                if bullet.rect.colliderect(
                    enemy.rect
                ):

                    if bullet in self.bullets:
                        self.bullets.remove(
                            bullet
                        )

                    if enemy in self.enemies:
                        self.enemies.remove(
                            enemy
                        )

                    self.score += 10

                    break

    def check_enemy_bullet_collisions(self):

        for bullet in self.enemy_bullets[:]:

            if bullet.rect.colliderect(
                self.player.rect
            ):

                self.enemy_bullets.remove(
                    bullet
                )

                self.player.lives -= 1

                self.player.reset_position()

                if self.player.lives <= 0:
                    self.game_over = True

    # --------------------------------------------------
    # CHECK ENEMY POSITION
    # --------------------------------------------------

    def check_enemy_reached_player(self):

        for enemy in self.enemies:

            if enemy.rect.bottom >= (
                self.player.y
            ):

                self.game_over = True

                return

    # --------------------------------------------------
    # NEXT LEVEL
    # --------------------------------------------------

    def check_level_complete(self):

        if self.enemies:
            return

        self.level += 1

        self.bullets.clear()

        self.enemy_bullets.clear()

        self.enemy_direction = 1

        self.create_enemies()

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def update(self):

        if self.game_over or self.paused:
            return

        self.update_player()

        self.update_bullets()

        self.update_enemy_bullets()

        self.update_enemies()

        self.enemy_shoot()

        self.check_bullet_collisions()

        self.check_enemy_bullet_collisions()

        self.check_enemy_reached_player()

        self.check_level_complete()

    # --------------------------------------------------
    # DRAW BACKGROUND
    # --------------------------------------------------

    def draw_background(self):

        self.screen.fill(
            (8, 12, 28)
        )

        # Stars
        random.seed(10)

        for _ in range(90):

            x = random.randint(
                0,
                self.WIDTH
            )

            y = random.randint(
                0,
                self.HEIGHT
            )

            size = random.choice(
                [1, 1, 1, 2]
            )

            pygame.draw.circle(
                self.screen,
                (150, 160, 190),
                (x, y),
                size
            )

        random.seed()

    # --------------------------------------------------
    # DRAW HUD
    # --------------------------------------------------

    def draw_hud(self):

        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            (255, 255, 255)
        )

        level_text = self.font.render(
            f"Level: {self.level}",
            True,
            (255, 255, 255)
        )

        lives_text = self.font.render(
            f"Lives: {self.player.lives}",
            True,
            (255, 255, 255)
        )

        self.screen.blit(
            score_text,
            (25, 20)
        )

        self.screen.blit(
            level_text,
            (
                self.WIDTH // 2 - 55,
                20
            )
        )

        self.screen.blit(
            lives_text,
            (
                self.WIDTH - 140,
                20
            )
        )

    # --------------------------------------------------
    # DRAW GAME
    # --------------------------------------------------

    def draw(self):

        self.draw_background()

        self.draw_hud()

        self.player.draw(
            self.screen
        )

        for enemy in self.enemies:
            enemy.draw(
                self.screen
            )

        for bullet in self.bullets:
            bullet.draw(
                self.screen
            )

        for bullet in self.enemy_bullets:
            bullet.draw(
                self.screen
            )

        if self.paused:
            self.draw_pause_screen()

        if self.game_over:
            self.draw_game_over()

        pygame.display.flip()

    # --------------------------------------------------
    # PAUSE SCREEN
    # --------------------------------------------------

    def draw_pause_screen(self):

        overlay = pygame.Surface(
            (self.WIDTH, self.HEIGHT)
        )

        overlay.set_alpha(150)

        overlay.fill(
            (0, 0, 0)
        )

        self.screen.blit(
            overlay,
            (0, 0)
        )

        text = self.large_font.render(
            "PAUSED",
            True,
            (255, 255, 255)
        )

        text_rect = text.get_rect(
            center=(
                self.WIDTH // 2,
                self.HEIGHT // 2
            )
        )

        self.screen.blit(
            text,
            text_rect
        )

        instruction = self.small_font.render(
            "Press P to continue",
            True,
            (200, 200, 200)
        )

        instruction_rect = (
            instruction.get_rect(
                center=(
                    self.WIDTH // 2,
                    self.HEIGHT // 2 + 60
                )
            )
        )

        self.screen.blit(
            instruction,
            instruction_rect
        )

    # --------------------------------------------------
    # GAME OVER SCREEN
    # --------------------------------------------------

    def draw_game_over(self):

        overlay = pygame.Surface(
            (self.WIDTH, self.HEIGHT)
        )

        overlay.set_alpha(180)

        overlay.fill(
            (0, 0, 0)
        )

        self.screen.blit(
            overlay,
            (0, 0)
        )

        title = self.large_font.render(
            "GAME OVER",
            True,
            (255, 90, 100)
        )

        title_rect = title.get_rect(
            center=(
                self.WIDTH // 2,
                self.HEIGHT // 2 - 60
            )
        )

        self.screen.blit(
            title,
            title_rect
        )

        score = self.font.render(
            f"Final Score: {self.score}",
            True,
            (255, 255, 255)
        )

        score_rect = score.get_rect(
            center=(
                self.WIDTH // 2,
                self.HEIGHT // 2 + 10
            )
        )

        self.screen.blit(
            score,
            score_rect
        )

        restart = self.small_font.render(
            "Press R to play again  |  ESC to quit",
            True,
            (200, 200, 200)
        )

        restart_rect = restart.get_rect(
            center=(
                self.WIDTH // 2,
                self.HEIGHT // 2 + 65
            )
        )

        self.screen.blit(
            restart,
            restart_rect
        )

    # --------------------------------------------------
    # RESTART
    # --------------------------------------------------

    def restart(self):

        self.score = 0

        self.level = 1

        self.game_over = False

        self.paused = False

        self.enemy_direction = 1

        self.enemy_move_timer = 0

        self.bullets.clear()

        self.enemy_bullets.clear()

        self.player.lives = 3

        self.player.reset_position()

        self.create_enemies()

    # --------------------------------------------------
    # MAIN GAME LOOP
    # --------------------------------------------------

    def run(self):

        while self.running:

            self.handle_events()

            self.update()

            self.draw()

            self.clock.tick(
                self.FPS
            )

        pygame.quit()
import time
import turtle

from player import Player
from obstacle import ObstacleManager
from scoreboard import Scoreboard

screen = turtle.Screen()
screen.setup(width=600, height=600)
screen.title("Frog Crossing Game")
screen.tracer(0)

player = Player()
obstacles = ObstacleManager()
scoreboard = Scoreboard()

screen.listen()
screen.onkey(player.move, "Up")

game_on = True

while game_on:

    time.sleep(0.1)
    screen.update()

    obstacles.create_obstacle()
    obstacles.move_obstacles()

    for obstacle in obstacles.obstacles:
        if obstacle.distance(player) < 20:
            scoreboard.game_over()
            game_on = False

    if player.reached_finish():
        player.reset_position()
        obstacles.increase_speed()
        scoreboard.next_level()

screen.exitonclick()
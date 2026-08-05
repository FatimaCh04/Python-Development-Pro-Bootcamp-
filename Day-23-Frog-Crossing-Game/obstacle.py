import turtle
import random

MOVE_DISTANCE = 5


class ObstacleManager:

    def __init__(self):
        self.obstacles = []

    def create_obstacle(self):

        if random.randint(1, 6) == 1:
            obstacle = turtle.Turtle("square")
            obstacle.penup()
            obstacle.shapesize(stretch_wid=1, stretch_len=2)
            obstacle.color(random.choice([
                "red", "blue", "orange",
                "yellow", "purple", "cyan"
            ]))
            obstacle.goto(300, random.randint(-240, 240))
            self.obstacles.append(obstacle)

    def move_obstacles(self):
        for obstacle in self.obstacles:
            obstacle.backward(MOVE_DISTANCE)

    def increase_speed(self):
        global MOVE_DISTANCE
        MOVE_DISTANCE += 2
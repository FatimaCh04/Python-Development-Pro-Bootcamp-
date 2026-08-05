import turtle

START_POSITION = (0, -270)
FINISH_LINE = 260


class Player(turtle.Turtle):

    def __init__(self):
        super().__init__()

        self.shape("turtle")
        self.color("green")
        self.penup()
        self.goto(START_POSITION)
        self.setheading(90)

    def move(self):
        self.forward(20)

    def reset_position(self):
        self.goto(START_POSITION)

    def reached_finish(self):
        return self.ycor() >= FINISH_LINE
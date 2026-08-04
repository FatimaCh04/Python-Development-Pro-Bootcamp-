from turtle import Turtle

STARTING_POSITIONS = [(0, 0), (-20, 0), (-40, 0)]
MOVE_DISTANCE = 20


class Snake:

    def __init__(self):
        self.body = []

        for position in STARTING_POSITIONS:
            self.create_segment(position)

        self.head = self.body[0]

    def create_segment(self, position):
        segment = Turtle("square")
        segment.color("white")
        segment.penup()
        segment.goto(position)
        self.body.append(segment)

    def grow(self):
        self.create_segment(self.body[-1].position())

    def move(self):
        for seg_num in range(len(self.body) - 1, 0, -1):
            x = self.body[seg_num - 1].xcor()
            y = self.body[seg_num - 1].ycor()
            self.body[seg_num].goto(x, y)

        self.head.forward(MOVE_DISTANCE)

    def up(self):
        if self.head.heading() != 270:
            self.head.setheading(90)

    def down(self):
        if self.head.heading() != 90:
            self.head.setheading(270)

    def left(self):
        if self.head.heading() != 0:
            self.head.setheading(180)

    def right(self):
        if self.head.heading() != 180:
            self.head.setheading(0)
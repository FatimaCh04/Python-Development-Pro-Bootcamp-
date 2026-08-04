import turtle
import random

screen = turtle.Screen()
screen.title("Day 18 - Colorful Shapes")
screen.bgcolor("white")

pen = turtle.Turtle()
pen.speed(0)
pen.width(2)

colors = [
    "red",
    "blue",
    "green",
    "orange",
    "purple",
    "cyan",
    "magenta",
    "yellow",
    "pink",
    "brown"
]


def draw_shape(sides, length):
    angle = 360 / sides
    pen.color(random.choice(colors))

    for _ in range(sides):
        pen.forward(length)
        pen.right(angle)


# Draw shapes from triangle to decagon
for sides in range(3, 11):
    draw_shape(sides, 80)
    pen.penup()
    pen.forward(120)
    pen.pendown()

# Move to center for spiral
pen.penup()
pen.goto(0, -100)
pen.pendown()

# Draw colorful spiral
for i in range(80):
    pen.color(random.choice(colors))
    pen.forward(i * 3)
    pen.right(91)

pen.hideturtle()
screen.exitonclick()
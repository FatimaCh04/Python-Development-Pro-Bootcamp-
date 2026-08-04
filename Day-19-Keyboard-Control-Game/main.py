import turtle

# Screen setup
screen = turtle.Screen()
screen.title("Day 19 - Keyboard Control Game")
screen.bgcolor("lightblue")
screen.setup(width=700, height=600)

# Create player turtle
player = turtle.Turtle()
player.shape("turtle")
player.color("green")
player.penup()
player.speed(0)


# Movement functions
def move_forward():
    player.forward(20)


def move_backward():
    player.backward(20)


def turn_left():
    player.left(20)


def turn_right():
    player.right(20)


def reset_position():
    player.penup()
    player.home()
    player.setheading(0)


def pen_up():
    player.penup()
    print("Pen Up")


def pen_down():
    player.pendown()
    print("Pen Down")


# Keyboard Controls
screen.listen()

screen.onkeypress(move_forward, "Up")
screen.onkeypress(move_backward, "Down")
screen.onkeypress(turn_left, "Left")
screen.onkeypress(turn_right, "Right")

screen.onkeypress(reset_position, "r")
screen.onkeypress(pen_up, "u")
screen.onkeypress(pen_down, "d")

screen.exitonclick()
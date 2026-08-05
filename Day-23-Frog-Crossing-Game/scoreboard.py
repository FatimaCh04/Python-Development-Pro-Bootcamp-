import turtle


class Scoreboard(turtle.Turtle):

    def __init__(self):
        super().__init__()

        self.level = 1

        self.penup()
        self.hideturtle()
        self.color("black")

        self.goto(-260, 260)

        self.update()

    def update(self):
        self.clear()
        self.write(
            f"Level: {self.level}",
            font=("Arial", 18, "bold")
        )

    def next_level(self):
        self.level += 1
        self.update()

    def game_over(self):
        self.goto(0, 0)
        self.write(
            "GAME OVER",
            align="center",
            font=("Arial", 26, "bold")
        )
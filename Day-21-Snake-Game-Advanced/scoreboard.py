from turtle import Turtle


class Scoreboard(Turtle):

    def __init__(self):

        super().__init__()

        self.score = 0

        self.color("white")
        self.penup()
        self.goto(0,260)

        self.hideturtle()

        self.update_score()



    def update_score(self):

        self.clear()

        self.write(
            f"Score: {self.score}",
            align="center",
            font=("Arial",24,"bold")
        )


    def increase_score(self):

        self.score += 1
        self.update_score()



    def game_over(self):

        self.goto(0,0)

        self.write(
            "GAME OVER",
            align="center",
            font=("Arial",35,"bold")
        )


    def reset(self):

        self.score = 0
        self.update_score()
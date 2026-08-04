from turtle import Turtle


ALIGNMENT = "center"
FONT = ("Arial", 20, "bold")


class Scoreboard(Turtle):

    def __init__(self):

        super().__init__()

        self.score = 0

        self.high_score = self.read_high_score()

        self.color("white")

        self.penup()

        self.goto(0,260)

        self.hideturtle()

        self.update_score()



    def update_score(self):

        self.clear()

        self.write(
            f"Score: {self.score}  High Score: {self.high_score}",
            align=ALIGNMENT,
            font=FONT
        )



    def increase_score(self):

        self.score += 1

        self.update_score()



    def reset(self):

        if self.score > self.high_score:

            self.high_score = self.score

            self.save_high_score()



        self.score = 0

        self.update_score()



    def game_over(self):

        self.goto(0,0)

        self.write(
            "GAME OVER",
            align="center",
            font=("Arial",35,"bold")
        )



    def read_high_score(self):

        try:

            with open("data.txt") as file:

                return int(file.read())

        except:

            return 0



    def save_high_score(self):

        with open("data.txt","w") as file:

            file.write(str(self.high_score))
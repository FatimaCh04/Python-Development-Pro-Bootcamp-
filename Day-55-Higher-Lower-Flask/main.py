from flask import Flask, render_template
import random


# ==========================================
# CREATE FLASK APP
# ==========================================

app = Flask(__name__)


# ==========================================
# GENERATE RANDOM NUMBER
# ==========================================

correct_number = random.randint(0, 9)


# ==========================================
# HOME ROUTE
# ==========================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        message="Guess a number between 0 and 9"
    )


# ==========================================
# GUESS ROUTE
# ==========================================

@app.route("/<int:guess>")
def check_guess(guess):

    if guess < correct_number:

        message = "Too low! Try a higher number. 🔼"

        result = "low"

    elif guess > correct_number:

        message = "Too high! Try a lower number. 🔽"

        result = "high"

    else:

        message = "You got it! 🎉"

        result = "correct"

    return render_template(
        "index.html",
        message=message,
        result=result,
        guess=guess
    )


# ==========================================
# RUN APP
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
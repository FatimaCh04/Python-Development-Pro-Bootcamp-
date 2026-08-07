import pandas as pd
import random
from tkinter import *

BACKGROUND_COLOR = "#B1DDC6"

# -------------------- Load Data -------------------- #
try:
    data = pd.read_csv("words_to_learn.csv")
except FileNotFoundError:
    data = pd.read_csv("words.csv")

to_learn = data.to_dict(orient="records")

current_card = {}
flip_timer = None


# -------------------- Functions -------------------- #
def next_card():
    global current_card, flip_timer

    if flip_timer:
        window.after_cancel(flip_timer)

    current_card = random.choice(to_learn)

    card_title.config(text="English", fg="black")
    card_word.config(text=current_card["English"], fg="black")

    flip_timer = window.after(3000, flip_card)


def flip_card():
    card_title.config(text="Urdu", fg="blue")
    card_word.config(text=current_card["Urdu"], fg="blue")


def known_word():
    global current_card

    if current_card in to_learn:
        to_learn.remove(current_card)

        pd.DataFrame(to_learn).to_csv(
            "words_to_learn.csv",
            index=False
        )

    if len(to_learn) > 0:
        next_card()
    else:
        card_title.config(text="Congratulations!")
        card_word.config(text="You learned all words!")


# -------------------- UI -------------------- #
window = Tk()
window.title("Flash Card App")
window.config(bg=BACKGROUND_COLOR, padx=40, pady=40)

card_title = Label(
    text="English",
    font=("Arial", 20, "italic"),
    bg=BACKGROUND_COLOR
)
card_title.pack()

card_word = Label(
    text="Press Next",
    font=("Arial", 32, "bold"),
    bg=BACKGROUND_COLOR
)
card_word.pack(pady=30)

Button(
    text="Known",
    width=12,
    command=known_word
).pack(pady=5)

Button(
    text="Next",
    width=12,
    command=next_card
).pack(pady=5)

next_card()

window.mainloop()
import random
from art import logo

EASY_LEVEL_TURNS = 10
HARD_LEVEL_TURNS = 5


def check_answer(user_guess, answer, turns):
    if user_guess > answer:
        print("📉 Too high.")
        return turns - 1
    elif user_guess < answer:
        print("📈 Too low.")
        return turns - 1
    else:
        print(f"🎉 Correct! The answer was {answer}.")


def set_difficulty():
    level = input("Choose a difficulty. Type 'easy' or 'hard': ").lower()

    if level == "easy":
        return EASY_LEVEL_TURNS
    else:
        return HARD_LEVEL_TURNS


def game():
    print(logo)
    print("Welcome to the Number Guessing Game!")
    print("I'm thinking of a number between 1 and 100.")

    answer = random.randint(1, 100)

    turns = set_difficulty()

    guess = 0

    while guess != answer:

        print(f"\nYou have {turns} attempts remaining.")

        guess = int(input("Make a guess: "))

        turns = check_answer(guess, answer, turns)

        if guess == answer:
            print("🏆 You Win!")
        elif turns == 0:
            print("❌ You've run out of guesses.")
            print(f"The number was {answer}.")
            return
        else:
            print("Guess again.")


game()
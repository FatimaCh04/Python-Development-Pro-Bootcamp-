import random
from art import logo, vs
from game_data import data


def format_data(account):
    return f"{account['name']}, {account['description']}, from {account['country']}"


def check_answer(guess, a_followers, b_followers):
    if a_followers > b_followers:
        return guess == "a"
    else:
        return guess == "b"


def game():
    print(logo)

    score = 0
    game_should_continue = True

    account_b = random.choice(data)

    while game_should_continue:

        account_a = account_b
        account_b = random.choice(data)

        while account_a == account_b:
            account_b = random.choice(data)

        print(f"\nCompare A: {format_data(account_a)}")
        print(vs)
        print(f"Against B: {format_data(account_b)}")

        guess = input("\nWho has more followers? Type 'A' or 'B': ").lower()

        a_followers = account_a["follower_count"]
        b_followers = account_b["follower_count"]

        is_correct = check_answer(guess, a_followers, b_followers)

        if is_correct:
            score += 1
            print(f"\n✅ Correct! Current score: {score}")
        else:
            print(f"\n❌ Wrong!")
            print(f"Final Score: {score}")
            game_should_continue = False


game()
import random
from art import logo

cards = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]


def deal_card():
    return random.choice(cards)


def calculate_score(cards_list):
    if sum(cards_list) == 21 and len(cards_list) == 2:
        return 0

    if 11 in cards_list and sum(cards_list) > 21:
        cards_list.remove(11)
        cards_list.append(1)

    return sum(cards_list)


def compare(user_score, computer_score):
    if user_score == computer_score:
        return "🤝 Draw"

    elif computer_score == 0:
        return "😢 You lose. Computer has Blackjack."

    elif user_score == 0:
        return "🎉 You win with a Blackjack!"

    elif user_score > 21:
        return "💥 You went over. You lose."

    elif computer_score > 21:
        return "🎉 Computer went over. You win!"

    elif user_score > computer_score:
        return "🏆 You win!"

    else:
        return "😢 You lose."


def play_game():
    print(logo)

    user_cards = []
    computer_cards = []
    is_game_over = False

    for _ in range(2):
        user_cards.append(deal_card())
        computer_cards.append(deal_card())

    while not is_game_over:

        user_score = calculate_score(user_cards)
        computer_score = calculate_score(computer_cards)

        print(f"\nYour cards: {user_cards}, Current score: {user_score}")
        print(f"Computer's first card: {computer_cards[0]}")

        if user_score == 0 or computer_score == 0 or user_score > 21:
            is_game_over = True
        else:
            choice = input("Type 'y' to get another card, type 'n' to pass: ").lower()

            if choice == "y":
                user_cards.append(deal_card())
            else:
                is_game_over = True

    while computer_score != 0 and computer_score < 17:
        computer_cards.append(deal_card())
        computer_score = calculate_score(computer_cards)

    print("\n========== Final Result ==========")
    print(f"Your cards: {user_cards}, Final score: {user_score}")
    print(f"Computer's cards: {computer_cards}, Final score: {computer_score}")

    print(compare(user_score, computer_score))


while input("\nDo you want to play Blackjack? Type 'y' or 'n': ").lower() == "y":
    play_game()
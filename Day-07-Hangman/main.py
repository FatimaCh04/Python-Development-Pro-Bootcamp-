import random

word_list = [
    "apple",
    "banana",
    "orange",
    "python",
    "computer",
    "keyboard",
    "monitor",
    "programming",
    "developer",
    "internet",
    "github",
    "variable",
    "function",
    "loop",
    "condition"
]

hangman_stages = [
    """
     +---+
     |   |
     O   |
    /|\\  |
    / \\  |
        ===
    """,
    """
     +---+
     |   |
     O   |
    /|\\  |
    /    |
        ===
    """,
    """
     +---+
     |   |
     O   |
    /|\\  |
         |
        ===
    """,
    """
     +---+
     |   |
     O   |
    /|   |
         |
        ===
    """,
    """
     +---+
     |   |
     O   |
     |   |
         |
        ===
    """,
    """
     +---+
     |   |
     O   |
         |
         |
        ===
    """,
    """
     +---+
     |   |
         |
         |
         |
        ===
    """
]

chosen_word = random.choice(word_list)
word_length = len(chosen_word)

display = []

for _ in range(word_length):
    display.append("_")

lives = 6
guessed_letters = []

print("🎮 Welcome to Hangman!")
print("Guess the word one letter at a time.\n")

game_over = False

while not game_over:

    print(hangman_stages[lives])
    print("Word:", " ".join(display))
    print(f"Lives Left: {lives}")

    guess = input("\nGuess a letter: ").lower()

    if len(guess) != 1 or not guess.isalpha():
        print("❌ Please enter only one alphabet.\n")
        continue

    if guess in guessed_letters:
        print("⚠️ You already guessed that letter.\n")
        continue

    guessed_letters.append(guess)

    if guess in chosen_word:

        for position in range(word_length):
            if chosen_word[position] == guess:
                display[position] = guess

        print("✅ Correct Guess!\n")

    else:
        lives -= 1
        print("❌ Wrong Guess!\n")

    if "_" not in display:
        game_over = True
        print("🎉 Congratulations! You Won!")
        print(f"The word was: {chosen_word}")

    if lives == 0:
        game_over = True
        print(hangman_stages[0])
        print("💀 Game Over!")
        print(f"The word was: {chosen_word}")
import os

FILE_NAME = "scores.txt"


def load_high_score():
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, "w") as file:
            file.write("0")

    with open(FILE_NAME, "r") as file:
        return int(file.read())


def save_high_score(score):
    with open(FILE_NAME, "w") as file:
        file.write(str(score))


def main():
    print("=" * 35)
    print("📘 Student Score Manager")
    print("=" * 35)

    high_score = load_high_score()

    print(f"\nCurrent High Score: {high_score}")

    score = int(input("Enter your new score: "))

    if score > high_score:
        print("\n🎉 Congratulations! New High Score!")
        save_high_score(score)
    else:
        print("\nNo new high score this time.")

    print(f"\nHighest Score: {load_high_score()}")


if __name__ == "__main__":
    main()
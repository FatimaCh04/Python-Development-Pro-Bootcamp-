import pandas as pd

# Read the NATO phonetic alphabet CSV file
data = pd.read_csv("nato_phonetic_alphabet.csv")

# Create a dictionary:
# {"A": "Alfa", "B": "Bravo", ...}
phonetic_dict = {
    row.letter: row.code
    for (index, row) in data.iterrows()
}

# Get user input
word = input("Enter a word: ").upper()

# Convert each letter into its NATO code word
try:
    result = [
        phonetic_dict[letter]
        for letter in word
    ]

    print(result)

except KeyError:
    print("Sorry, only letters of the alphabet are allowed.")